"""Fase 7 (v50.38): complete schema (a clean installation equals a migrated one), clean production database without
any personal data, backups (copy, verification, rotation, restore), health of the server for the administration,
maintenance / incident banner. All on temporary copies."""
import gzip
import os
import sqlite3
import subprocess
import sys
import tempfile
import time
import unittest
from pathlib import Path

from helpers import ServerTestCase, Server, ROOT, SEED_DB


def schema(path):
    db = sqlite3.connect(path)
    try:
        return {t: sorted(r[1] for r in db.execute(f'PRAGMA table_info("{t}")'))
                for (t,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")}
    finally:
        db.close()


def bootstrap(db_path, extra=None):
    env = {**os.environ, 'WOD_DB_PATH': str(db_path), 'WOD_BACKUP_DIR': str(Path(db_path).parent / 'bk'), **(extra or {})}
    r = subprocess.run([sys.executable, '-c', 'import sys; sys.path.insert(0, "app"); import server; server.bootstrap()'], cwd=ROOT, env=env, capture_output=True, text=True)
    assert r.returncode == 0, r.stderr


class Schema(unittest.TestCase):
    def test_clean_install_equals_migrated_database(self):
        tmp = Path(tempfile.mkdtemp(prefix='wod-schema-'))
        clean = tmp / 'clean.sqlite3'; old = tmp / 'old.sqlite3'
        bootstrap(clean)
        import shutil; shutil.copy(SEED_DB, old); bootstrap(old)
        a, b = schema(clean), schema(old)
        self.assertEqual(sorted(a), sorted(b), 'mismas tablas')
        diff = {t: (set(a[t]) ^ set(b[t])) for t in a if set(a[t]) != set(b[t])}
        self.assertEqual(diff, {}, 'mismas columnas')
        bootstrap(clean); bootstrap(old)   # idempotent
        db = sqlite3.connect(clean)
        self.assertEqual(db.execute('SELECT COUNT(*) FROM users').fetchone()[0], 0)
        self.assertEqual(db.execute('PRAGMA integrity_check').fetchone()[0], 'ok')
        db.close()

    def test_server_starts_without_bundled_database(self):
        s = Server({'WOD_EMPTY_DB': '1'}, seed=None).start()
        try:
            import urllib.request, json
            self.assertEqual(json.loads(urllib.request.urlopen(s.base + '/api/health').read())['ok'], True)
            self.assertEqual(s.sql('SELECT COUNT(*) n FROM centers')[0]['n'], 0)
        finally:
            s.stop()

    def test_production_database_has_no_personal_data(self):
        tmp = Path(tempfile.mkdtemp(prefix='wod-prod-'))
        src = tmp / 'src.sqlite3'
        import shutil; shutil.copy(SEED_DB, src); bootstrap(src)
        db = sqlite3.connect(src)
        db.execute("INSERT INTO users(fullname,email,username,password_hash,role,created_at) VALUES('Test','t@example.org','t','x','recreational','2026-01-01')")
        db.execute("INSERT INTO site_settings(key,value,updated_at) VALUES('legal_owner_name','Titular SL','2026-01-01')")
        db.commit(); db.close()
        out = tmp / 'prod' / 'wd.sqlite3'
        r = subprocess.run([sys.executable, 'scripts/crear_semilla.py', '--source', str(src), '--out', str(out)], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        p = sqlite3.connect(out)
        for t in ('users', 'centers', 'bookings', 'sessions', 'audit_log', 'email_outbox', 'payment_orders', 'reward_offers'):
            self.assertEqual(p.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0], 0, t)
        self.assertGreater(p.execute('SELECT COUNT(*) FROM dive_points').fetchone()[0], 250)
        self.assertEqual(p.execute('SELECT COUNT(*) FROM dive_points WHERE center_id IS NOT NULL').fetchone()[0], 0)
        n = p.execute('SELECT COUNT(*) FROM dive_points').fetchone()[0]
        self.assertEqual(p.execute('SELECT COUNT(*) FROM dive_point_texts').fetchone()[0], n * 9)   # 9 languages (v50.46)
        self.assertEqual(p.execute("SELECT value FROM site_settings WHERE key='legal_owner_name'").fetchone()[0], 'Titular SL')
        p.close()
        self.assertEqual(oct(out.stat().st_mode & 0o777), '0o600')
        r = subprocess.run([sys.executable, 'scripts/crear_semilla.py', '--source', str(src), '--out', str(out)], cwd=ROOT, capture_output=True, text=True)
        self.assertNotEqual(r.returncode, 0)   # never overwrites


class EnvFile(unittest.TestCase):
    def test_env_file_with_inline_comments(self):
        sys.path.insert(0, str(ROOT / 'app'))
        from wod import config
        tmp = Path(tempfile.mkdtemp(prefix='wod-env-')) / '.env'
        tmp.write_text('# comentario\nWOD_T_A=on   # off desactiva\nWOD_T_B="valor # con almohadilla"\nexport WOD_T_C=Nombre con espacios\nWOD_T_D=ya\n\n', encoding='utf-8')
        os.environ['WOD_T_D'] = 'del entorno'
        try:
            self.assertEqual(config.load_env_file(tmp), 3)
            self.assertEqual((os.environ['WOD_T_A'], os.environ['WOD_T_B'], os.environ['WOD_T_C'], os.environ['WOD_T_D']),
                             ('on', 'valor # con almohadilla', 'Nombre con espacios', 'del entorno'))
        finally:
            for k in ('WOD_T_A', 'WOD_T_B', 'WOD_T_C', 'WOD_T_D'): os.environ.pop(k, None)


class Backups(ServerTestCase):
    extra_env = {'WOD_MAINTENANCE_SECONDS': '2', 'WOD_BACKUP_KEEP_HOURLY': '2', 'WOD_BACKUP_KEEP_DAILY': '1', 'WOD_BACKUP_KEEP_MONTHLY': '1'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = cls('run').make_admin()

    def test_automatic_backup_verify_and_restore(self):
        folder = self.server.tmp / 'backups' / 'db'
        end = time.time() + 15
        while time.time() < end and not list(folder.glob('worldives-*.sqlite3.gz')): time.sleep(0.5)
        files = list(folder.glob('worldives-*.sqlite3.gz'))
        self.assertTrue(files, 'copia horaria creada al arrancar')
        with gzip.open(files[0]) as f: self.assertEqual(f.read(16), b'SQLite format 3\x00')
        h = self.admin.get('/api/admin/health').json
        self.assertTrue(h['backup_db']); self.assertEqual(h['quick_check']['result'], 'ok')
        self.assertTrue((self.server.tmp / 'backups' / 'files').exists() or h['backup_files'] is None)
        env = {**self.server.env}
        r = subprocess.run([sys.executable, 'app/server.py', '--verify-backup', str(files[0])], cwd=ROOT, env=env, capture_output=True, text=True)
        self.assertIn('ok', r.stdout)
        # Rotation keeps 2 hourly copies
        for i in range(4):
            (folder / f'worldives-2020010{i + 1}-0000.sqlite3.gz').write_bytes(files[0].read_bytes())
        sys.path.insert(0, str(ROOT / 'app'))
        from wod import backup
        os.environ['WOD_BACKUP_KEEP_HOURLY'] = '2'; os.environ['WOD_BACKUP_KEEP_DAILY'] = '1'; os.environ['WOD_BACKUP_KEEP_MONTHLY'] = '1'
        try:
            backup.rotate(self.server.db)
        finally:
            for k in ('WOD_BACKUP_KEEP_HOURLY', 'WOD_BACKUP_KEEP_DAILY', 'WOD_BACKUP_KEEP_MONTHLY'): os.environ.pop(k, None)
        self.assertLessEqual(len(list(folder.glob('worldives-*.sqlite3.gz'))), 3)
        # Restore on a separate copy (never on the live database)
        target = self.server.tmp / 'restaurada.sqlite3'
        target.write_bytes(b'antigua')
        r = subprocess.run([sys.executable, 'app/server.py', '--restore', str(files[0]), '--yes'], cwd=ROOT, env={**env, 'WOD_DB_PATH': str(target)}, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        t = sqlite3.connect(target); self.assertEqual(t.execute('PRAGMA integrity_check').fetchone()[0], 'ok'); t.close()
        self.assertTrue(list(self.server.tmp.glob('restaurada.sqlite3.antes-de-restaurar-*')))

    def test_backup_now_with_external_command(self):
        marker = self.server.tmp / 'enviado.txt'
        script = self.server.tmp / 'externo.sh'
        script.write_text(f'#!/bin/sh\necho "$1" > {marker}\n'); script.chmod(0o755)
        r = subprocess.run([sys.executable, 'app/server.py', '--backup-now'], cwd=ROOT, env={**self.server.env, 'WOD_BACKUP_COMMAND': str(script)}, capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertTrue(marker.read_text().strip().endswith('.sqlite3.gz'))

    def test_health_and_banner(self):
        self.assertEqual(self.client().get('/api/admin/health').status, 403)
        h = self.admin.get('/api/admin/health').json
        self.assertIn('email_queue', h); self.assertIn('disk', h); self.assertFalse(h['production'])
        diver = self.make_diver('banner7')
        self.assertEqual(diver.post('/api/admin/banner', {'text': 'x'}).status, 403)
        r = self.admin.post('/api/admin/banner', {'text': 'Mantenimiento el domingo de 7 a 8', 'level': 'maintenance', 'hours': 2, 'notify_centers': True})
        self.assertEqual(r.status, 200, r)
        b = self.client().get('/api/meta').json['banner']
        self.assertEqual(b['level'], 'maintenance'); self.assertIn('domingo', b['text'])
        self.assertEqual(self.admin.post('/api/admin/banner', {'text': ''}).status, 200)
        self.assertIsNone(self.client().get('/api/meta').json['banner'])


if __name__ == '__main__':
    unittest.main()
