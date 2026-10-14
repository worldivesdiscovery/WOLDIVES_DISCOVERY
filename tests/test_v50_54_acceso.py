"""v50.54 · acceso a la demo y cuenta de administración (puntos 6 y 7 del encargo del 14/10/2026).

Punto 6 · Nadie podía entrar en la demo: el paquete de pruebas se abre en http://localhost:8100 pero su dirección
pública es http://127.0.0.1:8100, y la comprobación de origen (CSRF) rechazaba cada envío del formulario. Ahora las
direcciones locales del mismo puerto son equivalentes, solo cuando la dirección pública es local. «Acceso rápido a la
demostración» (Administrador, Centro de buceo 1 y 2, Freelance, Buceador) solo existe con WOD_DEMO_MODE=1.

Punto 7 · «python app/server.py --create-admin» antes del primer arranque (el orden de la guía del VPS) creaba una base
vacía, sin el catálogo de puntos. Ahora usa el mismo .env y la misma base que el servidor, la crea con el catálogo si no
existe, explica cada fallo y «--reset-admin-password» recupera el acceso.
"""
from __future__ import annotations

import hashlib
import os
import shutil
import sqlite3
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from helpers import Client, Server, ServerTestCase  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
DEMO_CATALOGUE = ROOT / 'data' / 'demo' / 'catalogo-demo.sqlite3'
GOOD = 'Coral-Faro-Morena-2026'


class InstalacionNueva(unittest.TestCase):
    """Una copia del programa como la del VPS: app/, data/seed/catalogo.sqlite3 y un .env de producción. Se ejecuta el
    comando desde otra carpeta (como hace sudo -u worldives) y antes de arrancar el servidor."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp(prefix='wod-cli-'))
        self.root = self.tmp / 'worldives'
        shutil.copytree(ROOT / 'app', self.root / 'app', ignore=shutil.ignore_patterns('__pycache__'))
        os.symlink(ROOT / 'public', self.root / 'public')   # read only: the photos of the example species
        (self.root / 'data' / 'seed').mkdir(parents=True)
        shutil.copy(DEMO_CATALOGUE, self.root / 'data' / 'seed' / 'catalogo.sqlite3')   # stands in for the real catalogue
        self.db = self.tmp / 'datos' / 'base.sqlite3'   # WOD_DB_PATH comes from the .env, as on the server
        (self.root / '.env').write_text('\n'.join([
            'WOD_ENV=production', 'WOD_PUBLIC_URL=https://worldivesdiscovery.com', f'WOD_SECRET_KEY={"k" * 48}',
            f'WOD_DB_PATH={self.db}   # base de la web', f'WOD_DATA_DIR={self.tmp / "datos"}', 'WOD_PBKDF2_ITERATIONS=100000', '']), encoding='utf-8')
        self.env = {k: v for k, v in os.environ.items() if not k.startswith(('WOD_', 'STRIPE_', 'ARCGIS_'))}
        self.env['PYTHONDONTWRITEBYTECODE'] = '1'

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def cli(self, *args, password=None, stdin=''):
        env = dict(self.env)
        if password is not None: env['WOD_ADMIN_PASSWORD'] = password
        return subprocess.run([sys.executable, str(self.root / 'app' / 'server.py'), *args], env=env, cwd=str(self.tmp),
                              input=stdin, capture_output=True, text=True, timeout=120)

    def q(self, sql, *args):
        with sqlite3.connect(self.db) as d:
            return d.execute(sql, args).fetchall()

    def test_create_admin_before_the_first_start_makes_the_whole_database(self):
        r = self.cli('--create-admin', '--email', 'Jefa@WorldivesDiscovery.com', password=GOOD, stdin='\n\n')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn(f'Base de datos: {self.db}', r.stdout)                    # the same base as the server (from .env)
        self.assertIn('creada a partir de data/seed/catalogo.sqlite3', r.stdout)
        self.assertIn('Hecho. Administrador creado: usuario «jefa», email jefa@worldivesdiscovery.com.', r.stdout)
        self.assertIn('https://worldivesdiscovery.com/#/login', r.stdout)
        with sqlite3.connect(DEMO_CATALOGUE) as d: points = d.execute('SELECT COUNT(*) FROM dive_points').fetchone()[0]
        self.assertGreaterEqual(self.q('SELECT COUNT(*) FROM dive_points')[0][0], points)   # the catalogue, not the 10 points of bootstrap()
        self.assertGreater(self.q('SELECT COUNT(*) FROM countries')[0][0], 0)
        self.assertGreater(self.q('SELECT COUNT(*) FROM species')[0][0], 0)
        self.assertEqual(self.q("SELECT username,email,fullname FROM users WHERE role='admin'"), [('jefa', 'jefa@worldivesdiscovery.com', 'Administración')])
        self.assertNotIn(GOOD, r.stdout + r.stderr)

    def test_clear_failures_and_nothing_written(self):
        r = self.cli('--create-admin', '--email', 'no-es-un-email', password=GOOD)
        self.assertEqual(r.returncode, 1); self.assertIn('el email no es válido', r.stdout)
        r = self.cli('--create-admin', '--email', 'a@b.es', '--username', 'a b', '--name', 'A', password=GOOD)
        self.assertEqual(r.returncode, 1); self.assertIn('el usuario debe tener de 3 a 40', r.stdout)
        for weak, why in (('corta', 'al menos'), ('password123', 'fácil de adivinar')):
            r = self.cli('--create-admin', '--email', 'jefa@worldivesdiscovery.com', password=weak, stdin='\n\n')
            self.assertEqual(r.returncode, 1, r.stdout); self.assertIn('No se ha creado el administrador', r.stdout); self.assertIn(why, r.stdout)
        self.assertEqual(self.q("SELECT COUNT(*) FROM users WHERE role='admin'")[0][0], 0)
        self.assertEqual(self.cli('--create-admin', '--email', 'jefa@worldivesdiscovery.com', password=GOOD, stdin='\n\n').returncode, 0)
        r = self.cli('--create-admin', '--email', 'jefa@worldivesdiscovery.com', password=GOOD, stdin='\n\n')
        self.assertEqual(r.returncode, 1)
        self.assertIn('ya existe el administrador «jefa»', r.stdout); self.assertIn('--reset-admin-password --email jefa@worldivesdiscovery.com', r.stdout)
        r = self.cli('--create-admin', password=GOOD, stdin='')                 # no terminal and nothing typed
        self.assertEqual(r.returncode, 1); self.assertIn('Cancelado', r.stdout)

    def test_unreadable_folder_says_which_user_to_use(self):
        if os.geteuid() == 0: self.skipTest('root puede escribir en cualquier carpeta')
        (self.tmp / 'datos').mkdir(); os.chmod(self.tmp / 'datos', 0o500)
        try:
            r = self.cli('--create-admin', '--email', 'jefa@worldivesdiscovery.com', password=GOOD, stdin='\n\n')
        finally:
            os.chmod(self.tmp / 'datos', 0o700)
        self.assertEqual(r.returncode, 1); self.assertIn('sudo -u worldives', r.stdout)

    def test_old_database_without_catalogue_is_reported_never_deleted(self):
        # What --create-admin of v50.53 left when it ran before the first start: tables, an admin, no catalogue.
        self.db.parent.mkdir(parents=True)
        env = dict(self.env, WOD_EMPTY_DB='1', WOD_ADMIN_PASSWORD=GOOD)
        subprocess.run([sys.executable, str(self.root / 'app' / 'server.py'), '--create-admin', '--email', 'jefa@worldivesdiscovery.com', '--username', 'jefa', '--name', 'Jefa'],
                       env=env, cwd=str(self.tmp), capture_output=True, text=True, timeout=120, check=True)
        self.assertEqual(self.q('SELECT COUNT(*) FROM countries')[0][0], 0)
        r = self.cli('--create-admin', '--email', 'otra@worldivesdiscovery.com', password=GOOD, stdin='\n\n')
        self.assertIn('no tiene el catálogo de puntos de buceo', r.stdout); self.assertIn(f'mv {self.db} {self.db}.sin-catalogo', r.stdout)
        self.assertTrue(self.db.exists())

    def test_reset_admin_password(self):
        r = self.cli('--reset-admin-password', password=GOOD)
        self.assertEqual(r.returncode, 1); self.assertIn('no hay ninguna base de datos', r.stdout)
        self.assertEqual(self.cli('--create-admin', '--email', 'jefa@worldivesdiscovery.com', password=GOOD, stdin='\n\n').returncode, 0)
        uid = self.q("SELECT id FROM users WHERE username='jefa'")[0][0]
        with sqlite3.connect(self.db) as d:
            d.execute("INSERT INTO sessions(token_hash,user_id,created_at,last_seen) VALUES('x',?,0,0)", (uid,))
        # an account locked by attempts from many places (the counters live in a file next to the database)
        limits = self.db.with_name(self.db.stem + '-limites.sqlite3')
        with sqlite3.connect(limits) as d:
            d.execute('CREATE TABLE IF NOT EXISTS hits(name TEXT NOT NULL, key TEXT NOT NULL, start REAL NOT NULL, count INTEGER NOT NULL, PRIMARY KEY(name, key)) WITHOUT ROWID')
            key = hashlib.sha256(f'{"k" * 48}|login-cuenta|acct:{uid}'.encode()).hexdigest()[:32]
            d.execute("INSERT INTO hits VALUES('login-cuenta',?,9e12,999)", (key,))
        before = self.q("SELECT password_hash FROM users WHERE id=?", uid)[0][0]
        r = self.cli('--reset-admin-password', '--email', 'nadie@x.es', password='Otra-Frase-Larga-2026')
        self.assertEqual(r.returncode, 1); self.assertIn('Las que hay: jefa', r.stdout)
        r = self.cli('--reset-admin-password', password='password123')
        self.assertEqual(r.returncode, 1); self.assertIn('No se ha cambiado la contraseña', r.stdout)
        r = self.cli('--reset-admin-password', password='Otra-Frase-Larga-2026')
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
        self.assertIn('Nueva contraseña guardada para «jefa»; sesiones abiertas cerradas: 1.', r.stdout)
        self.assertNotEqual(self.q("SELECT password_hash FROM users WHERE id=?", uid)[0][0], before)
        self.assertEqual(self.q('SELECT COUNT(*) FROM sessions WHERE user_id=?', uid)[0][0], 0)
        self.assertEqual(self.q("SELECT COUNT(*) FROM audit_log WHERE action='admin_password_reset_cli' AND user_id=?", uid)[0][0], 1)
        with sqlite3.connect(limits) as d:
            self.assertEqual(d.execute("SELECT COUNT(*) FROM hits WHERE name='login-cuenta'").fetchone()[0], 0)


class ResetThenSignIn(ServerTestCase):
    """The new password works on the running server; the old one no longer does."""

    def test_reset_and_sign_in(self):
        self.make_admin(email='jefa@worldives.test', username='jefa')
        res = self.server.run_cli('--reset-admin-password', '--username', 'JEFA', env={'WOD_ADMIN_PASSWORD': 'Nueva-Frase-Buceo-2026'})
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        self.assertEqual(self.client().login('jefa', 'admin-seguro-2026').status, 401)
        self.assertEqual(self.client().login('jefa', 'Nueva-Frase-Buceo-2026').status, 200)


class LoopbackOrigins(unittest.TestCase):
    """http://localhost:P and http://127.0.0.1:P are the same computer: both are accepted when the public address is
    one of them. A public address on the internet never accepts them."""

    def post_login(self, srv, origin):
        return Client(srv, origin=origin).post('/api/auth/login', {'login': 'nadie', 'password': 'x'}).status

    def test_local_names_of_the_same_port(self):
        srv = Server().start()
        try:
            port = srv.port
            for origin in (f'http://localhost:{port}', f'http://127.0.0.1:{port}', f'http://[::1]:{port}'):
                self.assertEqual(self.post_login(srv, origin), 401, origin)   # wrong password, but not refused by origin
            for origin in (f'http://localhost:{port + 1}', 'http://localhost', f'https://localhost:{port}', 'http://evil.example'):
                self.assertEqual(self.post_login(srv, origin), 403, origin)
        finally:
            srv.stop()

    def test_public_address_on_the_internet(self):
        srv = Server({'WOD_PUBLIC_URL': 'https://pruebas.example.org'}).start()
        try:
            self.assertEqual(self.post_login(srv, 'https://pruebas.example.org'), 401)
            self.assertEqual(self.post_login(srv, f'http://localhost:{srv.port}'), 403)
            self.assertEqual(self.post_login(srv, f'http://127.0.0.1:{srv.port}'), 403)
        finally:
            srv.stop()


class QuickAccessOutsideTheDemo(ServerTestCase):
    def test_no_quick_access_list(self):
        self.assertEqual(self.client().get('/api/pruebas/cuentas').status, 404)
        self.assertEqual(self.client().post('/api/pruebas/entrar', {'cuenta': 'x.prueba'}).status, 404)

    def test_no_quick_access_with_demo_mode_on_the_real_domain(self):
        srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_PUBLIC_URL': 'https://worldivesdiscovery.com'})
        try:
            with self.assertRaises(RuntimeError): srv.start()   # it refuses to start at all
            self.assertIn('No se puede arrancar', (srv.tmp / 'stdout.log').read_text())
        finally:
            srv.stop()


class QuickAccessInTheDemo(ServerTestCase):
    extra_env = {'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        accounts = [('jefa', 'admin', None), ('dueno1', 'center', 'owner'), ('monitor1', 'center', 'instructor'), ('dueno2', 'center', 'owner'),
                    ('libre', 'freelance', None), ('libre2', 'freelance', None), ('bea', 'recreational', None)]
        for i, (u, role, member) in enumerate(accounts):
            res = cls.server.run_cli('--create-admin', '--email', f'{u}@example.org', '--username', u, '--name', u.title(), env={'WOD_ADMIN_PASSWORD': 'Demo-Frase-Larga-2026'})
            assert res.returncode == 0, res.stdout + res.stderr
            centre = None
            if role == 'center':
                centre = 1 if u.endswith('1') else 2
                cls.server.sql("INSERT OR IGNORE INTO centers(id,name,country,active,created_at,updated_at) VALUES(?,?,'España',1,'2026-01-01','2026-01-01')", (900 + centre, f'Centro {centre}'))
                centre = 900 + centre
                cls.server.sql('INSERT INTO center_members(center_id,user_id,member_role,created_at) SELECT ?,id,?,? FROM users WHERE username=?', (centre, member, '2026-01-01', u))
            cls.server.sql('UPDATE users SET username=?, role=?, center_id=? WHERE username=?', (f'{u}.prueba', role, centre, u))

    def test_list_has_the_five_buttons_with_the_owners(self):
        r = self.client().get('/api/pruebas/cuentas')
        self.assertEqual(r.status, 200)
        got = [(a['label'], a['cuenta']) for a in r.json['items']]
        self.assertEqual(got, [('Administrador', 'jefa.prueba'), ('Centro de buceo 1', 'dueno1.prueba'), ('Centro de buceo 2', 'dueno2.prueba'),
                               ('Freelance', 'libre.prueba'), ('Buceador', 'bea.prueba')])
        self.assertEqual(r.json['items'][1]['detail'], 'Centro 1')
        self.assertNotIn('password', r.body.decode())

    def test_each_button_signs_in_with_its_account(self):
        for cuenta, role in (('jefa.prueba', 'admin'), ('dueno1.prueba', 'center'), ('dueno2.prueba', 'center'), ('libre.prueba', 'freelance'), ('bea.prueba', 'recreational')):
            c = self.client(); r = c.post('/api/pruebas/entrar', {'cuenta': cuenta})
            self.assertEqual(r.status, 200, (cuenta, r)); self.assertEqual(c.me()['user']['role'], role)
            # and with the form, from http://localhost (the address the test package opens)
            f = Client(self.server, origin=f'http://localhost:{self.server.port}')
            self.assertEqual(f.login(cuenta, 'Demo-Frase-Larga-2026').status, 200, cuenta)


if __name__ == '__main__':
    unittest.main()
