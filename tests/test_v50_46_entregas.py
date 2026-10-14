"""v50.45/v50.46 · Two delivery zips and the test environment (encargo 2b bloque 1 and cambios del 12/10/2026).

- demo_guard: the server refuses to start with WOD_DEMO_MODE=1 on the production address, in production, or with a
  real Stripe key; in the test environment no e-mail goes out by SMTP.
- The automatic check of build_release refuses a production zip with test accounts, the test password, real keys,
  a database other than the seed, a .env, WOD_DEMO_MODE=1 or caches; and accepts a clean one.
- «Restaurar demo» only exists in the test environment, recreates the fixed test accounts and keeps the
  administrator the owner created.
- v50.46: the test database has no administrator; the «create the administrator» screen exists only in the test
  environment while there is none; old /assets/… addresses redirect to the new folders; «Contacto» form; Russian → English.
"""
from __future__ import annotations

import http.client
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import Client, Server

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'scripts'))
import generar_zips as br  # noqa: E402
from crear_demo import ACCOUNTS, PASSWORD  # noqa: E402


def start_code(env):
    e = dict(os.environ); e.update({'WOD_NO_ENV_FILE': '1', 'WOD_PORT': '1'}); e.pop('WOD_DEMO_MODE', None); e.update(env)
    with tempfile.TemporaryDirectory() as d:
        e['WOD_DB_PATH'] = str(Path(d) / 'x.sqlite3'); e['WOD_LOG_DIR'] = d; e['WOD_STORAGE_DIR'] = d
        r = subprocess.run([sys.executable, str(ROOT / 'app' / 'server.py')], env=e, capture_output=True, text=True, timeout=30)
    return r.returncode, r.stdout + r.stderr


class DemoGuard(unittest.TestCase):
    def test_refuses_production_address(self):
        # v50.52: the real domain and every subdomain of it, the test site pruebas.* included
        for url in ('https://worldivesdiscovery.com', 'https://www.worldivesdiscovery.com', 'https://pruebas.worldivesdiscovery.com'):
            code, out = start_code({'WOD_DEMO_MODE': '1', 'WOD_PUBLIC_URL': url})
            self.assertEqual(code, 2, (url, out)); self.assertIn('WOD_DEMO_MODE=1 no se permite', out)

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
        files = {p: ROOT / p for p in ('app/server.py', '.env.example', 'README.md', 'requirements.txt', 'iniciar.bat', 'iniciar.sh', 'public/index.html')}
        problems = br.check_files(files, 'produccion')
        self.assertEqual(problems, [f'falta {br.SEED}'])         # only the seed is missing in this small sample

    def test_dirty_production_is_refused(self):
        user = ACCOUNTS['diver'][0]
        files = {
            'docs/notas.md': self.f('notas.md', f'Entra con {user} y la clave {PASSWORD}'),
            'app/keys.py': self.f('keys.py', "KEY='sk_live_" + 'A1b2C3d4E5f6G7h8' + "'"),
            '.env': self.f('.env', 'WOD_SECRET_KEY='),
            '.env.example': self.f('.env.example', 'STRIPE_SECRET_KEY=sk_test_abc   # filled by mistake\nWOD_SMTP_USER=\nWOD_SMTP_PASSWORD=\n'),
            'docs/despliegue/start.sh': self.f('start.sh', 'export WOD_DEMO_MODE=1\n'),
            'data/worldives.sqlite3': self.f('db.sqlite3', ''),
            'app/__pycache__/server.cpython-311.pyc': self.f('x.pyc', ''),
            'docs/pruebas/README-PRUEBAS.md': self.f('c.md', 'x'),
        }
        text = '\n'.join(br.check_files(files, 'produccion'))
        for what in ('docs/notas.md: menciona', 'sk_live_', '.env: no puede ir', '.env.example: STRIPE_SECRET_KEY tiene un valor',
                     'docs/despliegue/start.sh: activa WOD_DEMO_MODE=1', 'data/worldives.sqlite3: base de datos', '__pycache__', 'solo puede ir en el zip de pruebas'):
            self.assertIn(what, text)
        self.assertNotIn('WOD_SMTP_USER', text)                       # an empty variable followed by another is not a value

    def test_seed_with_people_is_refused(self):
        import sqlite3
        db = self.tmp / 'seed.sqlite3'
        c = sqlite3.connect(db); c.execute('CREATE TABLE users(id INTEGER)'); c.execute('INSERT INTO users VALUES(1)'); c.commit(); c.close()
        self.assertTrue(any('la semilla tiene datos' in p for p in br.check_files({br.SEED: db}, 'produccion')))


class RestoreDemo(unittest.TestCase):
    def test_owner_creates_the_admin_and_reset_keeps_it(self):
        srv = Server({'WOD_DEMO_MODE': '1'}).start()
        try:
            st = Client(srv).get('/api/setup/status').json
            self.assertTrue(st['demo']); self.assertTrue(st['setup_allowed'])          # no administrator yet: the screen exists
            a = Client(srv)
            r = a.post('/api/setup', {'fullname': 'Titular', 'email': 'titular@example.com', 'username': 'titular', 'password': 'Clave-Titular-2026!'})
            self.assertEqual(r.status, 200, r)
            self.assertFalse(Client(srv).get('/api/setup/status').json['setup_allowed'])   # only while there is none
            self.assertEqual(Client(srv).post('/api/setup', {'fullname': 'X', 'email': 'x@example.com', 'username': 'x2', 'password': 'Clave-Titular-2026!'}).status, 400)
            self.assertTrue(a.get('/api/admin/health').json['demo'])
            self.assertEqual(a.post('/api/admin/demo/reset', {}).status, 200)
            for role in ('center', 'freelance', 'diver', 'instructor'):
                self.assertEqual(Client(srv).login(ACCOUNTS[role][0], PASSWORD).status, 200, role)
            self.assertEqual(Client(srv).login('titular', 'Clave-Titular-2026!').status, 200)   # the owner's administrator is kept
            # v50.51: the demo brings its own administrator (CUENTAS-DEMO.txt); the owner's one is kept too
            self.assertEqual(sorted(r['username'] for r in srv.sql("SELECT username FROM users WHERE role='admin'")), [ACCOUNTS['admin'][0], 'titular'])
            self.assertEqual(Client(srv).login(ACCOUNTS['admin'][0], PASSWORD).status, 200)
            states = {x['status'] for x in srv.sql('SELECT status FROM bookings')}
            self.assertTrue({'requested', 'confirmed', 'accepted_pending_payment', 'cancelled', 'rejected', 'expired', 'completed'} <= states, states)
            self.assertGreaterEqual(srv.sql('SELECT COUNT(*) n FROM provider_services WHERE center_id IS NOT NULL')[0]['n'], 5)
        finally:
            srv.stop()

    def test_demo_database_has_only_the_demo_administrator(self):
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'demo.sqlite3'
            r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(out)], capture_output=True, text=True, timeout=300)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertEqual(br.db_counts(out)['admins'], 1)                             # v50.51: the demo administrator (CUENTAS-DEMO.txt)

    def test_no_setup_screen_and_no_reset_outside_demo(self):
        srv = Server({'WOD_ADMIN_PASSWORD': 'Admin-Local-2026!'}).start()
        try:
            self.assertFalse(Client(srv).get('/api/setup/status').json['setup_allowed'])
            self.assertEqual(Client(srv).post('/api/setup', {'fullname': 'X', 'email': 'x@example.com', 'username': 'x', 'password': 'Clave-Titular-2026!'}).status, 403)
            srv.run_cli('--create-admin', '--email', 'root@example.com', '--username', 'root', '--name', 'Root')
            a = Client(srv); a.login('root', 'Admin-Local-2026!')
            self.assertEqual(a.post('/api/admin/demo/reset', {}).status, 404)
            self.assertFalse(a.get('/api/admin/health').json['demo'])
        finally:
            srv.stop()


class CleanFoldersAndContact(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.srv = Server().start()

    @classmethod
    def tearDownClass(cls):
        cls.srv.stop()

    def test_old_addresses_redirect_and_new_ones_serve(self):
        c = Client(self.srv)
        for old, new in (('/assets/js/world-dives-v8.js', '/js/world-dives-v8.js'), ('/assets/brand/favicon.ico', '/img/marca/favicon.ico'),
                         ('/assets/images/BUCEADORES.webp', '/img/portada/buceadores.webp'), ('/assets/images/maldivas.webp', '/img/destinos/maldivas.webp'),
                         ('/assets/i18n/en.json', '/idiomas/en.json'), ('/assets/vendor/leaflet/leaflet.js', '/lib/leaflet/leaflet.js')):
            conn = http.client.HTTPConnection('127.0.0.1', self.srv.port, timeout=10); conn.request('GET', old); r = conn.getresponse(); r.read(); conn.close()
            self.assertEqual((r.status, r.getheader('Location')), (301, new), old)
            self.assertEqual(c.get(new).status, 200, new)
        self.assertEqual(c.get('/assets/images/no-existe.webp').status, 404)
        self.assertFalse((ROOT / 'public' / 'assets').exists())
        self.assertFalse((ROOT / 'public' / 'idiomas' / 'ru.json').exists())
        html = c.get('/').body.decode()
        self.assertNotIn('/assets/', html); self.assertNotIn('hreflang="ru"', html)
        self.assertNotIn('value="ru"', html)

    def test_saved_paths_are_migrated(self):
        rows = self.srv.sql("SELECT image_path FROM dive_point_photos WHERE image_path LIKE '/assets/images/%'")
        self.assertEqual(rows, [])
        self.assertTrue(self.srv.sql("SELECT 1 FROM dive_point_photos WHERE image_path LIKE '/img/destinos/%'"))

    def test_russian_falls_back_to_english(self):
        self.assertIn('<html lang="en">', Client(self.srv).get('/?lang=ru').body.decode())

    def test_contact_form(self):
        c = Client(self.srv)
        bad = c.post('/api/contact', {'topic': 'web', 'name': 'Ana', 'email': 'ana@example.com', 'message': 'Hola', 'privacy': True})
        self.assertEqual(bad.status, 400)
        self.assertEqual(c.post('/api/contact', {'topic': 'nope', 'name': 'Ana', 'email': 'ana@example.com', 'message': 'Una duda sobre mi cuenta', 'privacy': True}).status, 400)
        self.assertEqual(c.post('/api/contact', {'topic': 'web', 'name': 'Ana', 'email': 'ana@example.com', 'message': 'Una duda sobre mi cuenta'}).status, 400)
        r = c.post('/api/contact', {'topic': 'booking', 'booking_ref': 'WOD-123', 'name': 'Ana Pérez', 'email': 'ana@buceo-ana.es',
                                    'message': 'Una duda sobre mi reserva del sábado', 'privacy': True, 'lang': 'fr'})
        self.assertEqual(r.status, 200, r); self.assertTrue(r.json['ref'].startswith('CON-'))
        row = self.srv.sql('SELECT topic,booking_ref,lang,status FROM contact_messages WHERE id=?', (r.json['id'],))[0]
        self.assertEqual(row, {'topic': 'booking', 'booking_ref': 'WOD-123', 'lang': 'fr', 'status': 'open'})
        mail = self.srv.sql("SELECT subject,lang FROM email_outbox WHERE template='contact_received' ORDER BY id DESC LIMIT 1")[0]
        self.assertEqual(mail['lang'], 'fr'); self.assertIn(r.json['ref'], mail['subject'])


if __name__ == '__main__':
    unittest.main()
