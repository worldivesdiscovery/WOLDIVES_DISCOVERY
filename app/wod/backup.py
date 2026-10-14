"""Backups (Fase 7.4).

- Database: every hour (WOD_BACKUP_DB_MINUTES, 60) with SQLite's online backup API, which copies a consistent
  snapshot while the server keeps working. Files: <WOD_BACKUP_DIR>/db/worldives-YYYYmmdd-HHMM.sqlite3 (gzip).
- Uploads (photos of the catalogue and private documents): once a day, a .tar.gz of the uploads and storage folders.
- Rotation: the last 48 hourly copies, 30 daily and 12 monthly (WOD_BACKUP_KEEP_HOURLY / _DAILY / _MONTHLY).
- External destination: WOD_BACKUP_COMMAND, run after each copy with the file path as its only argument
  (for example a script that calls «rclone copy» or «aws s3 cp»). Its failure is reported, never hidden.
- Integrity: «PRAGMA quick_check» once a day; every copy is opened and checked before it is kept.
Restore and the restore test are documented in docs/despliegue/README.md.
"""
from __future__ import annotations

import gzip
import os
import shutil
import sqlite3
import subprocess
import tarfile
import time
from datetime import datetime, timezone
from pathlib import Path

from . import config


MAGIC = b'WODBK1\n'
CHUNK = 4 * 1024 * 1024


def _backup_key(name='WOD_BACKUP_KEY'):
    """32-byte key from WOD_BACKUP_KEY (never the data key): None when not configured (development only)."""
    import hashlib
    raw = config.env(name)
    return hashlib.sha256(raw.encode('utf-8')).digest() if raw else None


def encrypt_file(path: Path) -> None:
    """Encrypts a finished copy in place with AES-256-GCM, chunk by chunk (each chunk authenticates its number and
    whether it is the last one, so a copy cannot be cut or reordered)."""
    key = _backup_key()
    if not key: return
    import secrets, struct
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aes = AESGCM(key); tmp = path.with_name(path.name + '.enc-tmp')
    with open(path, 'rb') as fi, open(tmp, 'wb') as fo:
        fo.write(MAGIC); n = 0; block = fi.read(CHUNK)
        while True:
            nxt = fi.read(CHUNK); last = not nxt; nonce = secrets.token_bytes(12)
            ct = aes.encrypt(nonce, block, struct.pack('>Q?', n, last))
            fo.write(struct.pack('>I', len(ct)) + nonce + ct); n += 1
            if last: break
            block = nxt
    os.replace(tmp, path); os.chmod(path, 0o600)


def _plain_copy(path: Path, out: Path) -> None:
    """Writes the decrypted (and still gzip-compressed if it was) content of a copy to out."""
    import struct
    with open(path, 'rb') as fi:
        head = fi.read(len(MAGIC))
        if head != MAGIC:
            fi.seek(0)
            with open(out, 'wb') as fo: shutil.copyfileobj(fi, fo)
            return
        # After changing the key, WOD_BACKUP_KEY_OLD still opens the copies made before (ASVS 5.0 V11.2.2).
        keys = [k for k in (_backup_key(), _backup_key('WOD_BACKUP_KEY_OLD')) if k]
        if not keys: raise RuntimeError('Esta copia está cifrada: falta WOD_BACKUP_KEY.')
        from cryptography.exceptions import InvalidTag
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        start = fi.tell()
        for i, key in enumerate(keys):
            fi.seek(start); aes = AESGCM(key); n = 0
            try:
                with open(out, 'wb') as fo:
                    while True:
                        size = fi.read(4)
                        if not size: raise RuntimeError('Copia cifrada incompleta.')
                        ln = struct.unpack('>I', size)[0]; nonce = fi.read(12); ct = fi.read(ln)
                        peek = fi.read(1); last = not peek
                        if peek: fi.seek(-1, 1)
                        fo.write(aes.decrypt(nonce, ct, struct.pack('>Q?', n, last))); n += 1
                        if last: break
                return
            except InvalidTag:
                if n or i == len(keys) - 1: raise RuntimeError('La clave de las copias no abre esta copia (o la copia está dañada).')


def backup_dir(db_path: Path) -> Path:
    return Path(config.env('WOD_BACKUP_DIR') or (db_path.parent / 'backups'))


def _stamp() -> str:
    return datetime.now(timezone.utc).strftime('%Y%m%d-%H%M')


def backup_db(db_path: Path) -> Path:
    """Consistent copy with the SQLite backup API, checked and compressed. Returns the .sqlite3.gz path."""
    folder = backup_dir(db_path) / 'db'
    folder.mkdir(parents=True, exist_ok=True)
    tmp = folder / f'.tmp-{os.getpid()}-{time.time_ns()}.sqlite3'
    src = sqlite3.connect(db_path, timeout=30)
    dst = sqlite3.connect(tmp)
    try:
        src.backup(dst, pages=2000, sleep=0.01)
        ok = dst.execute('PRAGMA quick_check').fetchone()[0]
    finally:
        dst.close(); src.close()
    if ok != 'ok':
        tmp.unlink(missing_ok=True)
        raise RuntimeError(f'La copia de la base no supera quick_check: {ok}')
    out = folder / f'worldives-{_stamp()}.sqlite3.gz'
    with open(tmp, 'rb') as fi, gzip.open(out, 'wb', compresslevel=6) as fo:
        shutil.copyfileobj(fi, fo, 1024 * 1024)
    tmp.unlink(missing_ok=True)
    os.chmod(out, 0o600)
    encrypt_file(out)
    return out


def backup_files(folders: list[Path], db_path: Path) -> Path | None:
    """Daily .tar.gz of the uploaded files (catalogue photos and private documents)."""
    existing = [f for f in folders if f and f.exists()]
    if not existing: return None
    folder = backup_dir(db_path) / 'files'
    folder.mkdir(parents=True, exist_ok=True)
    out = folder / f'archivos-{_stamp()}.tar.gz'
    with tarfile.open(out, 'w:gz') as tar:
        for f in existing:
            tar.add(f, arcname=f.name)
    os.chmod(out, 0o600)
    encrypt_file(out)
    return out


def rotate(db_path: Path) -> int:
    """Keeps the newest N hourly copies, one per day for D days and one per month for M months."""
    keep_h = config.env_int('WOD_BACKUP_KEEP_HOURLY', 48, 1, 10000)
    keep_d = config.env_int('WOD_BACKUP_KEEP_DAILY', 30, 1, 10000)
    keep_m = config.env_int('WOD_BACKUP_KEEP_MONTHLY', 12, 0, 1000)
    removed = 0
    for sub, pattern in (('db', 'worldives-*.sqlite3.gz'), ('files', 'archivos-*.tar.gz')):
        files = sorted((backup_dir(db_path) / sub).glob(pattern), reverse=True)
        keep, days, months = set(), [], []
        for i, f in enumerate(files):
            stamp = f.name.split('-', 1)[1][:13]   # YYYYmmdd-HHMM
            if sub == 'db' and i < keep_h: keep.add(f)
            if stamp[:8] not in days and len(days) < keep_d: days.append(stamp[:8]); keep.add(f)
            if stamp[:6] not in months and len(months) < keep_m: months.append(stamp[:6]); keep.add(f)
        for f in files:
            if f not in keep:
                f.unlink(missing_ok=True); removed += 1
    return removed


def ship(path: Path) -> str:
    """Runs WOD_BACKUP_COMMAND <file> to send a copy outside the server. Returns '' or the error."""
    cmd = config.env('WOD_BACKUP_COMMAND')
    if not cmd or not path: return ''
    try:
        # Only what rclone needs: never the keys of the .env (ASVS 5.0 V13.3.2).
        env = {k: v for k, v in os.environ.items() if k in ('PATH', 'HOME', 'LANG', 'LC_ALL', 'TZ', 'TMPDIR', 'USER', 'LOGNAME') or k.startswith('RCLONE_')}
        r = subprocess.run([*cmd.split(), str(path)], capture_output=True, text=True, timeout=1800, env=env)
        return '' if r.returncode == 0 else (r.stderr or r.stdout or f'código {r.returncode}')[-500:]
    except (OSError, subprocess.TimeoutExpired) as exc:
        return str(exc)[-500:]


def verify(path: Path) -> str:
    """Opens a backup (.sqlite3 or .sqlite3.gz) in a temporary file and runs integrity_check: the restore test."""
    tmp = Path(str(path) + f'.verify-{os.getpid()}.sqlite3'); plain = Path(str(path) + f'.plain-{os.getpid()}')
    try:
        _plain_copy(path, plain)
        if str(path).endswith('.gz'):
            with gzip.open(plain, 'rb') as fi, open(tmp, 'wb') as fo: shutil.copyfileobj(fi, fo)
        else:
            shutil.copy2(plain, tmp)
        plain.unlink(missing_ok=True)
        db = sqlite3.connect(tmp)
        try:
            res = db.execute('PRAGMA integrity_check').fetchone()[0]
            tables = db.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
        finally:
            db.close()
        return f'{res} · {tables} tablas'
    finally:
        tmp.unlink(missing_ok=True); plain.unlink(missing_ok=True)


def restore(path: Path, db_path: Path) -> Path:
    """Restores a copy over the database (server stopped). The current database is kept aside first."""
    if not path.exists(): raise FileNotFoundError(path)
    aside = None
    if db_path.exists():
        aside = db_path.with_name(db_path.name + f'.antes-de-restaurar-{_stamp()}')
        shutil.move(db_path, aside)
        for side in ('-wal', '-shm'):
            p = Path(str(db_path) + side)
            if p.exists(): p.unlink()
    plain = Path(str(db_path) + '.plain')
    _plain_copy(path, plain)
    if str(path).endswith('.gz'):
        with gzip.open(plain, 'rb') as fi, open(db_path, 'wb') as fo: shutil.copyfileobj(fi, fo)
    else:
        shutil.copy2(plain, db_path)
    plain.unlink(missing_ok=True)
    os.chmod(db_path, 0o600)
    return aside
