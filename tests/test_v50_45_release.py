"""v50.45 · Encargo 2b, bloque 1: two delivery zips and the test environment.

- demo_guard: the server refuses to start with WOD_DEMO_MODE=1 on the production address, in production, or with a
  real Stripe key; in the test environment no e-mail goes out by SMTP.
- The automatic check of build_release refuses a production zip with test accounts, the test password, real keys,
  a database other than the seed, a .env, WOD_DEMO_MODE=1 or caches; and accepts a clean one.
- «Restaurar demo» only exists in the test environment and recreates the fixed test accounts.
"""
from __future__ import annotations

import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import Client, Server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import build_release as br  # noqa: E402
from crear_demo import ACCOUNTS, PASSWORD  # noqa: E402


def start_code(env):
    e = dict(os.environ); e.update({'WOD_NO_ENV_FILE': '1', 'WOD_PORT': '1'}); e.pop('WOD_DEMO_MODE', None); e.update(env)
    with tempfile.TemporaryDirectory() as d:
        e['WOD_DB_PATH'] = str(Path(d) / 'x.sqlite3'); e['WOD_LOG_DIR'] = d; e['WOD_STORAGE_DIR'] = d
        r = subprocess.run([sys.executable, str(ROOT / 'app' / 'server.py')], env=e, capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout + r.stderr


class DemoGuard(unittest.TestCase):
    def test_refuses_production_address(self):
        code, out = start_code({'WOD_DEMO_MODE': '1', 'WOD_PUBLIC_URL': 'https://www.worldives.com'})
        self.assertEqual(code, 2, out); self.assertIn('WOD_DEMO_MODE=1 no se permite', out)

    def test_refuses_extra_production_host_and_real_stripe_key(self):
        code, out = start_code({'WOD_DEMO_MODE': '1', 'WOD_PUBLIC_URL': 'https://reservas.example.org', 'WOD_PRODUCTION_HOSTS': 'reservas.example.org'})
        self.assertEqual(code, 2, out)
        code, out = start_code({'WOD_DEMO_MODE': '1', 'WOD_PUBLIC_URL': 'http://127.0.0.1:8100', 'STRIPE_SECRET_KEY': 'sk_live_' + 'x' * 20})
        self.assertEqual(code, 2, out); self.assertIn('modo test', out)


class EnvTemplate(unittest.TestCase):
    def test_env_example_copied_as_is_sets_nothing(self):
        sys.path.insert(0, str(ROOT / 'app'))
        from wod import config as wcfg
        keys = [l.split('=', 1)[0] for l in (ROOT / '.env.example').read_text(encoding='utf-8').splitlines() if l[:1].isalpha() and '=' in l]
        self.assertGreater(len(keys), 40)
        saved = {k: os.environ.pop(k) for k in keys if k in os.environ}
        try:
            self.assertEqual(wcfg.load_env_file(ROOT / '.env.example'), 0)     # every variable is empty: defaults apply
            self.assertFalse([k for k in keys if k in os.environ])
        finally:
            os.environ.update(saved)


class ReleaseCheck(unittest.TestCase):
    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def f(self, name, text):
        p = self.tmp / name.replace('/', '_'); p.write_text(text, encoding='utf-8'); return p

    def test_clean_production_passes(self):
        files = {'app/server.py': ROOT / 'app' / 'server.py', '.env.example': ROOT / '.env.example', 'README.md': ROOT / 'README.md'}
        problems = br.check_files(files, 'produccion')
        self.assertEqual(problems, [f'falta {br.SEED}'])         # only the seed is missing in this small sample

    def test_dirty_production_is_refused(self):
        user = ACCOUNTS['diver'][0]
        files = {
            'docs/notas.md': self.f('notas.md', f'Entra con {user} y la clave {PASSWORD}'),
            'app/keys.py': self.f('keys.py', "KEY='sk_live_" + 'A1b2C3d4E5f6G7h8' + "'"),
            '.env': self.f('.env', 'WOD_SECRET_KEY='),
            '.env.example': self.f('.env.example', 'STRIPE_SECRET_KEY=sk_test_abc   # filled by mistake\nWOD_SMTP_USER=\nWOD_SMTP_PASSWORD=\n'),
            'deploy/start.sh': self.f('start.sh', 'export WOD_DEMO_MODE=1\n'),
            'data/worldives.sqlite3': self.f('db.sqlite3', ''),
            'app/__pycache__/server.cpython-311.pyc': self.f('x.pyc', ''),
            'docs/pruebas/CUENTAS-DE-PRUEBA.md': self.f('c.md', 'x'),
        }
        text = '\n'.join(br.check_files(files, 'produccion'))
        for what in ('docs/notas.md: menciona', 'sk_live_', '.env: no puede ir', '.env.example: STRIPE_SECRET_KEY tiene un valor',
                     'deploy/start.sh: activa WOD_DEMO_MODE=1', 'data/worldives.sqlite3: base de datos', '__pycache__', 'solo puede ir en el zip de pruebas'):
            self.assertIn(what, text)
        self.assertNotIn('WOD_SMTP_USER', text)                       # an empty variable followed by another is not a value

    def test_seed_with_people_is_refused(self):
        import sqlite3
        db = self.tmp / 'seed.sqlite3'
        c = sqlite3.connect(db); c.execute('CREATE TABLE users(id INTEGER)'); c.execute('INSERT INTO users VALUES(1)'); c.commit(); c.close()
        self.assertTrue(any('la semilla tiene datos' in p for p in br.check_files({br.SEED: db}, 'produccion')))


class RestoreDemo(unittest.TestCase):
    def test_reset_only_in_demo_and_recreates_the_accounts(self):
        srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ADMIN_PASSWORD': 'Admin-Local-2026!'}).start()
        try:
            r = srv.run_cli('--create-admin', '--email', 'root@example.com', '--username', 'root', '--name', 'Root')
            self.assertEqual(r.returncode, 0, r.stderr)
            a = Client(srv); a.login('root', 'Admin-Local-2026!')
            self.assertTrue(a.get('/api/admin/health').json['demo'])
            r = a.post('/api/admin/demo/reset', {})
            self.assertEqual(r.status, 200, r)
            for role in ('admin', 'center', 'freelance', 'diver'):
                c = Client(srv); self.assertEqual(c.login(ACCOUNTS[role][0], PASSWORD).status, 200, role)
            states = {x['status'] for x in srv.sql('SELECT status FROM bookings')}
            self.assertTrue({'requested', 'confirmed', 'accepted_pending_payment', 'cancelled', 'rejected', 'expired', 'completed'} <= states, states)
            self.assertFalse(srv.sql("SELECT 1 FROM users WHERE username='root'"))         # replaced by the demo
        finally:
            srv.stop()

    def test_reset_does_not_exist_outside_demo(self):
        srv = Server({'WOD_ADMIN_PASSWORD': 'Admin-Local-2026!'}).start()
        try:
            srv.run_cli('--create-admin', '--email', 'root@example.com', '--username', 'root', '--name', 'Root')
            a = Client(srv); a.login('root', 'Admin-Local-2026!')
            self.assertEqual(a.post('/api/admin/demo/reset', {}).status, 404)
            self.assertFalse(a.get('/api/admin/health').json['demo'])
        finally:
            srv.stop()


if __name__ == '__main__':
    unittest.main()
