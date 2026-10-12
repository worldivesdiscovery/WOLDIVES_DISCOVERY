#!/usr/bin/env python3
"""Builds the two delivery zips of a version (encargo 2b · bloque 1; v50.46: final production package for the VPS):

    python scripts/generar_zips.py              → dist/WORLDIVES-v<APP_VERSION>-produccion.zip
                                                   dist/WORLDIVES-v<APP_VERSION>-pruebas.zip

-produccion  ready to upload as it is to the VPS: clean code, no data (no users, not even an administrator, no
             bookings, no test accounts or test database, no uploads, logs, caches, temporary files or .env) and no
             files that are not used. The database is created on the first start from data/seed/catalogo.sqlite3
             (countries, types, zones, certifications, points, destinations and legal texts). The administrator is
             created when installing: python app/server.py --create-admin (README.md).
-pruebas     the same code + the demonstration database, README-PRUEBAS.md and iniciar-pruebas (port 8100). It has
             no administrator: the owner creates it the first time. It is NEVER uploaded to the real server.

Before writing each zip it runs an automatic check (check_production / check_pruebas). If anything is wrong the zip
is not created and the script ends with an error listing every problem.
"""
from __future__ import annotations

import argparse
import fnmatch
import re
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED = 'data/seed/catalogo.sqlite3'
DEMO_LIVE = 'data/pruebas/worldives.sqlite3'

# Only in the test zip (or in none): demo data, test accounts, screenshots with demo data, the old brand archive.
NOT_IN_PRODUCTION = ['docs/pruebas/*', 'data/demo/*', 'data/pruebas/*', 'scripts/crear_demo.py', 'scripts/reset_demo.*', 'iniciar-pruebas.*',
                     'scripts/herramientas/demo_centros_ficticios.py', 'README-PRUEBAS.md']
# In no zip: the archive of retired files, screenshots, repository files, runtime data, caches and temporary files.
NOT_IN_ANY = ['_archivo/*', 'docs/capturas/*', '.github/*', '.gitignore', '.env', '.env.*', '*.pyc', '*/__pycache__/*', '*.log', 'logs/*',
              'storage/*', 'public/assets/*', 'data/subidas/*', 'data/backups/*', 'data/mail-outbox/*', 'data/tiles/*', 'dist/*',
              '*.sqlite3-wal', '*.sqlite3-shm', '.git/*', '*.tmp', '*.swp', '*~', '.DS_Store', 'Thumbs.db', '*.lock', '*/capturas/*']
ALLOWED_ENV = {'.env.example'}

# What must never be inside the production zip
TEST_ACCOUNT = re.compile(r'\b(?:admin|centro|freelance|instructor|pendiente|buzo\d?)\.prueba\b|Worldives-Prueba-2026', re.I)
SECRETS = [(re.compile(r'sk_live_[A-Za-z0-9]{8,}'), 'clave real de Stripe (sk_live_)'),
           (re.compile(r'rk_live_[A-Za-z0-9]{8,}'), 'clave restringida real de Stripe (rk_live_)'),
           (re.compile(r'sk_test_[A-Za-z0-9]{20,}'), 'clave de Stripe en modo test (sk_test_ de verdad)'),
           (re.compile(r'whsec_[A-Za-z0-9]{24,}'), 'secreto de webhook de Stripe'),
           (re.compile(r'-----BEGIN (?:RSA |EC |OPENSSH |)PRIVATE KEY-----'), 'clave privada'),
           (re.compile(r'\bAKIA[0-9A-Z]{16}\b'), 'clave de AWS'),
           (re.compile(r'\bAAP[KT][A-Za-z0-9_\-]{30,}'), 'clave de ArcGIS'),
           (re.compile(r'\bxkeysib-[a-f0-9]{30,}'), 'clave de Brevo')]
SECRET_VARS = ('WOD_SECRET_KEY', 'STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'STRIPE_CONNECT_WEBHOOK_SECRET', 'WOD_SMTP_PASSWORD',
               'WOD_SMTP_USER', 'ARCGIS_API_KEY', 'WOD_ADMIN_PASSWORD', 'VAPID_PRIVATE_KEY')
CONFIG_FILES = ('*.sh', '*.bat', '*.service', '*.env.example', '.env.example', 'docs/despliegue/*', '*.conf', 'Caddyfile', '*.toml', '*.ini')
TEXT_EXT = {'.py', '.js', '.css', '.html', '.md', '.txt', '.json', '.webmanifest', '.sh', '.bat', '.example', '.conf', '.service',
            '.svg', '.csv', '.ini', '.toml', '.yml', '.yaml', '.xml', ''}


def match(path: str, patterns) -> bool:
    return any(fnmatch.fnmatch(path, p) or fnmatch.fnmatch(Path(path).name, p) for p in patterns)


def repo_files() -> list[str]:
    out = subprocess.run(['git', 'ls-files', '--cached', '--others', '--exclude-standard'], cwd=ROOT, capture_output=True, text=True, check=True).stdout
    return sorted(p for p in out.splitlines() if p and (ROOT / p).is_file())


def app_version() -> str:
    m = re.search(r"^APP_VERSION\s*=\s*'([^']+)'", (ROOT / 'app' / 'server.py').read_text(encoding='utf-8'), re.M)
    return m.group(1) if m else '0'


def db_counts(path: Path) -> dict:
    c = sqlite3.connect(f'file:{path}?mode=ro', uri=True)
    try:
        tables = {r[0] for r in c.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        out = {t: c.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0] for t in ('users', 'centers', 'bookings', 'sessions', 'payment_orders',
                                                                                  'logbook_entries', 'email_outbox', 'audit_log', 'contact_messages') if t in tables}
        if 'users' in tables and 'role' in {r[1] for r in c.execute('PRAGMA table_info(users)')}:
            out['admins'] = c.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
        return out
    finally:
        c.close()


def check_files(files: dict[str, Path], kind: str) -> list[str]:
    """files: {path inside the zip: file on disk}. Returns the list of problems (empty = OK)."""
    problems = []
    for rel, src in files.items():
        if match(rel, NOT_IN_ANY) and rel not in ALLOWED_ENV:
            problems.append(f'{rel}: no puede ir en ningún zip (caché, registro, subidas, .env o archivo antiguo)')
        if rel.endswith(('.sqlite3', '.sqlite', '.db')):
            if kind == 'produccion' and rel != SEED:
                problems.append(f'{rel}: base de datos en el zip de producción (solo se permite {SEED})')
            elif rel == SEED:
                n = db_counts(src)
                busy = {k: v for k, v in n.items() if v}
                if busy: problems.append(f'{SEED}: la semilla tiene datos de personas o actividad {busy}')
            continue
        if kind == 'produccion' and match(rel, NOT_IN_PRODUCTION):
            problems.append(f'{rel}: solo puede ir en el zip de pruebas')
        if src.suffix.lower() not in TEXT_EXT or src.stat().st_size > 8_000_000: continue
        text = src.read_text(encoding='utf-8', errors='ignore')
        for rx, what in SECRETS:
            if rx.search(text): problems.append(f'{rel}: contiene una {what}')
        if kind == 'produccion' and TEST_ACCOUNT.search(text) and rel != 'scripts/generar_zips.py' and not rel.startswith('tests/test_v50_45'):
            problems.append(f'{rel}: menciona una cuenta o la contraseña de prueba')
        if rel in ALLOWED_ENV or rel.endswith('.env.example'):
            for var in SECRET_VARS:
                m = re.search(rf'^[ \t]*{var}[ \t]*=[ \t]*([^#\s][^#\n]*)', text, re.M)
                if m and m.group(1).strip(): problems.append(f'{rel}: {var} tiene un valor (debe ir vacía)')
        if kind == 'produccion' and match(rel, CONFIG_FILES) and re.search(r'^\s*(?:export\s+|set\s+")?WOD_DEMO_MODE=1', text, re.M | re.I):
            problems.append(f'{rel}: activa WOD_DEMO_MODE=1')
    if kind == 'produccion' and SEED not in files: problems.append(f'falta {SEED}')
    if kind == 'produccion':
        for need in ('README.md', '.env.example', 'requirements.txt', 'iniciar.bat', 'iniciar.sh', 'app/server.py', 'public/index.html'):
            if need not in files: problems.append(f'falta {need}')
        if 'README.md' in files and '--create-admin' not in files['README.md'].read_text(encoding='utf-8'):
            problems.append('README.md: no explica cómo crear el administrador (--create-admin)')
    if kind == 'pruebas' and DEMO_LIVE in files and db_counts(files[DEMO_LIVE]).get('admins'):
        problems.append(f'{DEMO_LIVE}: la base de pruebas no debe traer cuentas de administración (las crea el titular)')
    if kind == 'pruebas':
        for need in ('README-PRUEBAS.md', 'iniciar-pruebas.sh', 'iniciar-pruebas.bat', DEMO_LIVE):
            if need not in files: problems.append(f'falta {need}')
    return problems


def make_seed(tmp: Path) -> Path:
    out = tmp / 'catalogo.sqlite3'
    res = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_semilla.py'), '--source', str(ROOT / 'data' / 'demo' / 'catalogo-demo.sqlite3'),
                          '--out', str(out)], capture_output=True, text=True)
    if res.returncode != 0 or not out.exists(): raise SystemExit('No se ha podido crear la semilla del catálogo:\n' + res.stdout + res.stderr)
    for ext in ('-wal', '-shm'):
        p = Path(str(out) + ext)
        if p.exists(): p.unlink()
    return out


def make_demo(tmp: Path) -> Path:
    out = tmp / 'demo.sqlite3'
    res = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(out)], capture_output=True, text=True)
    if res.returncode != 0: raise SystemExit('No se ha podido crear la base de pruebas:\n' + res.stdout + res.stderr)
    return out


def write_zip(path: Path, top: str, files: dict[str, Path]):
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists(): path.unlink()
    with zipfile.ZipFile(path, 'w', zipfile.ZIP_DEFLATED, compresslevel=9) as z:
        for rel in sorted(files):
            z.write(files[rel], f'{top}/{rel}')


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=str(ROOT / 'dist'))
    ap.add_argument('--solo-comprobar', action='store_true', help='only run the checks, write nothing')
    a = ap.parse_args()
    ver = app_version(); out = Path(a.out)
    tracked = repo_files()
    tmp = Path(tempfile.mkdtemp(prefix='wod-release-'))
    try:
        seed = make_seed(tmp)
        prod = {p: ROOT / p for p in tracked if not match(p, NOT_IN_ANY + NOT_IN_PRODUCTION) or p in ALLOWED_ENV}
        prod[SEED] = seed
        demo = make_demo(tmp)
        pruebas = {p: ROOT / p for p in tracked if not match(p, NOT_IN_ANY) or p in ALLOWED_ENV}
        pruebas[SEED] = seed
        pruebas[DEMO_LIVE] = demo
        pruebas['README-PRUEBAS.md'] = ROOT / 'docs' / 'pruebas' / 'README-PRUEBAS.md'
        report = {}
        for kind, files in (('produccion', prod), ('pruebas', pruebas)):
            problems = check_files(files, kind)
            if problems:
                print(f'COMPROBACIÓN FALLIDA ({kind}): no se crea el zip.'); [print('  -', p) for p in problems]
                raise SystemExit(1)
            print(f'Comprobación {kind}: correcta ({len(files)} archivos).')
            if not a.solo_comprobar:
                z = out / f'WORLDIVES-v{ver}-{kind}.zip'
                write_zip(z, f'WORLDIVES-v{ver}-{kind}', files)
                report[kind] = (z, z.stat().st_size, len(files))
        for kind, (z, size, n) in report.items():
            print(f'{z}  ·  {size / 1048576:.1f} MB  ·  {n} archivos')
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


if __name__ == '__main__':
    main()
