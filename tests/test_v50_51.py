"""v50.51 · La ficha del punto como en v50.49: vida marina, vídeos de la ruta y recorridos 360° antiguos en una sola
petición; las fotos de las especies en dos tamaños; la demo se regenera cuando cambia la versión."""
import datetime as dt
import importlib.util
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from helpers import ServerTestCase  # noqa: E402
from media_mock import MediaMock  # noqa: E402


class Ficha(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock = MediaMock()
        cls.extra_env = {'WOD_MEDIA_FETCH_BASE': cls.mock.base}
        super().setUpClass()
        cls.admin = cls('run').make_admin()
        cls.pid = cls.admin.get('/api/dive-points').json['items'][0]['id']

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.mock.stop()

    def test_01_one_request_for_everything(self):
        srv = self.server
        srv.sql("INSERT INTO virtual_experiences(dive_point_id,title,experience_type,url,active,created_at,updated_at) VALUES(?,?,?,?,1,datetime(),datetime())",
                (self.pid, 'Panorámica de la entrada', 'panorama', None))
        srv.sql("INSERT INTO virtual_experiences(dive_point_id,title,experience_type,url,active,created_at,updated_at) VALUES(?,?,?,?,1,datetime(),datetime())",
                (self.pid, 'Vídeo copiado a la ruta', 'video360', 'https://www.youtube-nocookie.com/embed/Ab3dEf6hI9k'))
        copied = srv.sql("SELECT id FROM virtual_experiences WHERE title='Vídeo copiado a la ruta'")[0]['id']
        r = self.admin.post('/api/marina/video', {'point_id': self.pid, 'url': 'https://www.youtube.com/watch?v=Ab3dEf6hI9k', 'kind': '360', 'title': ''})
        self.assertEqual(r.status, 200, r.json)
        srv.sql('UPDATE route_videos SET legacy_virtual_id=? WHERE dive_point_id=?', (copied, self.pid))
        self.admin.post('/api/admin/marina/ejemplos')
        sp = {x['scientific']: x['id'] for x in self.admin.get('/api/admin/marina/especies').json['items']}
        self.admin.post('/api/marina/especie-punto', {'point_id': self.pid, 'species_id': sp['Octopus vulgaris'], 'frequency': 'common', 'months': []})

        d = self.client().get(f'/api/dive-points/{self.pid}?lang=de').json
        self.assertEqual([v['title'] for v in d['virtual']], ['Panorámica de la entrada'])   # the copied one is a route video now
        self.assertEqual(len(d['videos']), 1)
        self.assertEqual(d['videos'][0]['kind'], '360')
        self.assertTrue(d['videos'][0]['insertable'])
        self.assertEqual(d['species'][0]['name'], 'Gemeiner Krake')

    def test_02_example_photos_in_two_sizes(self):
        self.admin.post('/api/admin/marina/ejemplos')
        item = [x for x in self.admin.get('/api/admin/marina/especies').json['items'] if x['scientific'] == 'Mola mola'][0]
        srcset = item['photo']['srcset']
        self.assertEqual(srcset, '/img/especies/pez-luna-128.webp 128w, /img/especies/pez-luna-640.webp 640w')
        for w in (128, 640):
            r = self.client().get(f'/img/especies/pez-luna-{w}.webp')
            self.assertEqual(r.status, 200)
            self.assertEqual(r.headers.get('Content-Type'), 'image/webp')
        old = self.server.sql("SELECT COUNT(*) AS n FROM species WHERE photo_base LIKE '/img/especies/%' AND photo_widths<>'128,640'")[0]['n']
        self.assertEqual(old, 0)
        self.assertTrue(self.server.sql("SELECT 1 FROM schema_migrations WHERE version='50.51'"))


class CentroIdiomas(ServerTestCase):
    """The centre writes its presentation in other languages; each visitor sees the one of their language."""

    def test_texts_by_language(self):
        admin = self.make_admin()
        center = self.make_center(admin, 'idiomas1'); other = self.make_center(admin, 'idiomas2')
        cid = center.user['center_id']
        base = {'tagline': 'Buceo en la reserva marina', 'languages': 'Español, inglés', 'opening_hours': '9-19'}
        texts = {'en': {'tagline': 'Diving in the marine reserve', 'description': 'A small family centre.\n\nBoat dives every day.'},
                 'de': {'tagline': 'Tauchen im Meeresschutzgebiet', 'description': ''}, 'fr': {'tagline': '', 'description': ''}, 'xx': {'tagline': 'ignored'}}
        r = center.post('/api/provider/center-showcase', {**base, 'texts': texts}); self.assertEqual(r.status, 200, r.json)
        en = self.client().get(f'/api/centers/{cid}?lang=en').json['item']
        self.assertEqual((en['tagline'], en['text_lang']), ('Diving in the marine reserve', 'en'))
        self.assertIn('Boat dives every day.', en['description'])
        de = self.client().get(f'/api/centers/{cid}?lang=de').json['item']
        self.assertEqual(de['tagline'], 'Tauchen im Meeresschutzgebiet')
        it = self.client().get(f'/api/centers/{cid}?lang=it').json['item']
        self.assertEqual(it['tagline'], 'Buceo en la reserva marina'); self.assertNotIn('text_lang', it)
        self.assertEqual(sorted(it['texts']), ['de', 'en'])                     # empty languages are not stored
        r = center.post('/api/provider/center-showcase', {**base})                   # saving without «texts» keeps them
        self.assertEqual(sorted(self.client().get(f'/api/centers/{cid}').json['item']['texts']), ['de', 'en'])
        r = other.post('/api/provider/center-showcase', {**base, 'texts': {'en': {'tagline': 'Hacked'}}})
        self.assertEqual(self.client().get(f'/api/centers/{cid}?lang=en').json['item']['tagline'], 'Diving in the marine reserve')
        self.assertIn(self.client().post('/api/provider/center-showcase', {**base, 'texts': {}}).status, (401, 403))
        r = center.post('/api/provider/center-showcase', {**base, 'texts': 'no'}); self.assertEqual(r.status, 400)


class SeguridadExtra(ServerTestCase):
    """Security review v50.51: findings without an automated test in the review (now with one)."""

    def test_current_password_attempts_are_limited(self):
        d = self.make_diver('pwlimit1')
        for _ in range(10):
            self.assertEqual(d.post('/api/account/password', {'current_password': 'no-es-esta-1', 'new_password': 'otra-clave-segura-1'}).status, 400)
        r = d.post('/api/account/password', {'current_password': 'buceo-seguro-2026', 'new_password': 'otra-clave-segura-1'})
        self.assertEqual(r.status, 403, r.json)                                   # blocked for a while, even with the right one

    def test_report_limit_is_bounded(self):
        import importlib
        sys.path.insert(0, str(ROOT / 'app'))
        from wod import security as wsec
        lim = wsec.RateLimiter(10, 3600, max_keys=50)
        for i in range(500): lim.hit(f'10.0.{i // 250}.{i % 250}')
        self.assertLessEqual(len(lim._hits), 60)

    def test_team_join_uses_the_password_rules(self):
        admin = self.make_admin('adm-pw@worldives.test', 'admpw')
        center = self.make_center(admin, 'pwteam1')
        self.assertEqual(center.post('/api/center/team/invite', {'email': 'nuevo@pwteam1.example.org', 'member_role': 'instructor'}).status, 200)
        mail = self.server.sql("SELECT html FROM email_outbox WHERE template='team_invite' ORDER BY id DESC LIMIT 1")[0]['html']
        token = __import__('re').search(r'#/equipo\?token=([A-Za-z0-9_-]+)', mail).group(1)
        r = self.client().post('/api/team/join', {'token': token, 'fullname': 'Nuevo Instructor', 'username': 'nuevo.pw', 'password': 'qwertyuiop', 'accept_terms': True})
        self.assertEqual(r.status, 400); self.assertIn('fácil', r.json['error'])


class EstadoDelSistema(unittest.TestCase):
    """Administración → Operación → «Estado del sistema»: each service with its state and the .env variable."""

    def status(self, env):
        from helpers import Client, Server
        srv = Server(env).start()
        try:
            res = srv.run_cli('--create-admin', '--email', 'est@example.com', '--username', 'est', '--name', 'Estado', env={'WOD_ADMIN_PASSWORD': 'Estado-Seguro-2026'})
            self.assertEqual(res.returncode, 0, res.stderr)
            a = Client(srv); self.assertEqual(a.login('est', 'Estado-Seguro-2026').status, 200)
            self.assertEqual(Client(srv).get('/api/admin/health').status in (401, 403), True)
            return {x['key']: x for x in a.get('/api/admin/health').json['services']}
        finally:
            srv.stop()

    def test_missing_keys_are_pending_and_present_ones_ok(self):
        st = self.status({'WOD_SMTP_HOST': '', 'STRIPE_SECRET_KEY': '', 'ARCGIS_API_KEY': '', 'WOD_BACKUP_KEY': ''})
        for k in ('domain', 'session_key', 'data_key', 'mail', 'payments', 'basemap', 'satellite', 'whatsapp', 'push', 'backup', 'backup_key', 'backup_offsite', 'disk', 'admin_2fa'):
            self.assertIn(k, st)
        self.assertEqual((st['mail']['state'], st['payments']['state'], st['satellite']['state'], st['backup_key']['state']), ('pending',) * 4)
        self.assertIn('STRIPE_SECRET_KEY', st['payments']['env'])
        st = self.status({'WOD_SMTP_HOST': 'smtp.example.com', 'STRIPE_SECRET_KEY': 'sk_test_x', 'STRIPE_CONNECT_WEBHOOK_SECRET': 'whsec_x', 'ARCGIS_API_KEY': 'AAPKx', 'WOD_BACKUP_KEY': 'k' * 40})
        self.assertEqual((st['mail']['state'], st['payments']['state'], st['satellite']['state'], st['backup_key']['state']), ('ok',) * 4)
        self.assertIn('prueba', st['payments']['detail'])


class DemoVersion(unittest.TestCase):
    """reset_demo --si-hace-falta keeps the demonstration data only when it is recent AND from this version."""

    def test_rebuilt_when_the_version_changes(self):
        spec = importlib.util.spec_from_file_location('reset_demo', ROOT / 'scripts' / 'reset_demo.py')
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        self.assertRegex(mod.app_version(), r'^\d+\.\d+$')
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'demo.sqlite3'
            c = sqlite3.connect(db); c.execute('CREATE TABLE site_settings(key TEXT PRIMARY KEY, value TEXT)')
            c.execute("INSERT INTO site_settings VALUES('demo_generated_on',?)", (dt.date.today().isoformat(),)); c.commit()
            self.assertEqual(mod.generated(db), (dt.date.today(), None))          # made before v50.51: no version → rebuilt
            c.execute("INSERT INTO site_settings VALUES('demo_generated_version','50.49')"); c.commit(); c.close()
            made, version = mod.generated(db)
            self.assertNotEqual(version, mod.app_version())
        self.assertEqual(mod.generated(Path('/no/existe.sqlite3')), (None, None))


if __name__ == '__main__':
    unittest.main()
