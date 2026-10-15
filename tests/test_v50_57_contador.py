"""v50.57 · Revisión general, Bloque 4.2: el contador de visitas y reservas de «Actividad» (administración) y de
«Estadísticas» (cada centro y cada profesional).

Sin cookies ni datos de nadie: el servidor solo suma páginas vistas y visitantes de cada día; para contar a cada
visitante una vez al día guarda una huella (sal del día + IP + navegador) solo ese día, y la sal cambia cada día. No
cuentan los robots conocidos, la administración ni el equipo del centro en su propia ficha. Temporada configurable."""
import datetime as dt
import re
import unittest

from helpers import ServerTestCase

BROWSER = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'}
OTHER = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'}
TODAY = dt.date.today()


def outbox(server, template, to):
    return server.sql('SELECT * FROM email_outbox WHERE template=? AND to_email=? ORDER BY id DESC', (template, to))


class ContadorDeVisitas(ServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'vc1')
        cls.other_center = t.make_center(cls.admin, 'vc2')
        cls.pro = t.make_freelance(cls.admin, 'vc3')
        cls.diver = t.make_diver('vc4')
        cls.cid = cls.center.user['center_id']
        cls.cid2 = cls.other_center.user['center_id']

    def counts(self, scope):
        r = self.server.sql('SELECT COALESCE(SUM(views),0) AS v, COALESCE(SUM(uniques),0) AS u FROM visit_counts WHERE scope=? AND day=?', (scope, TODAY.isoformat()))[0]
        return r['v'], r['u']

    def visit(self, client, page, pid=None, headers=BROWSER):
        r = client.post('/api/visita', {'p': page, **({'id': pid} if pid else {})}, headers=dict(headers))
        self.assertEqual(r.status, 200, r.json)
        self.assertEqual(r.json, {'ok': True})
        return r

    # ------------------------------------------------------------------------------------------------ counting
    def test_1_una_visita_sin_cookies(self):
        anon = self.client()
        before = self.counts('site')
        r = self.visit(anon, 'home')
        self.assertFalse(any(k.lower() == 'set-cookie' for k in r.headers), r.headers)    # no cookie at all
        self.visit(anon, 'puntos'); self.visit(anon, 'centros')
        v, u = self.counts('site')
        self.assertEqual((v - before[0], u - before[1]), (3, 1))                            # 3 pages, 1 visitor of the day
        self.visit(self.client(), 'home', headers=OTHER)                                    # another browser: another visitor
        self.assertEqual(self.counts('site')[1] - before[1], 2)

    def test_2_robots_y_programas_no_cuentan(self):
        before = self.counts('site')
        for ua in ('Mozilla/5.0 (compatible; Googlebot/2.1; +http://www.google.com/bot.html)', 'facebookexternalhit/1.1',
                   'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) HeadlessChrome/126.0 Safari/537.36',
                   'WhatsApp/2.23.20.0', 'curl/8.5.0', 'python-requests/2.32', 'Chrome-Lighthouse', ''):
            self.visit(self.client(), 'home', headers={'User-Agent': ua})
        self.visit(self.client(), 'home', headers={})                                      # urllib's own agent
        self.assertEqual(self.counts('site'), before)

    def test_3_la_administracion_no_cuenta(self):
        before_site, before_c = self.counts('site'), self.counts(f'center:{self.cid}')
        self.visit(self.admin, 'home'); self.visit(self.admin, 'centro', self.cid)
        self.assertEqual((self.counts('site'), self.counts(f'center:{self.cid}')), (before_site, before_c))

    def test_4_solo_paginas_publicas(self):
        before = self.counts('site')
        for page in ('admin', 'cuenta', 'logbook', 'reserva', 'mis-puntos', 'inventada', '', None):
            self.visit(self.client(), page)
        self.assertEqual(self.counts('site'), before)

    def test_5_la_ficha_del_centro_y_su_equipo(self):
        scope = f'center:{self.cid}'
        before = self.counts(scope)
        st_before = self.server.sql("SELECT COALESCE(SUM(views),0) AS v FROM provider_stats_daily WHERE provider_type='center' AND provider_id=?", (self.cid,))[0]['v']
        anon = self.client()
        self.visit(anon, 'centro', self.cid); self.visit(anon, 'centro', self.cid)
        self.assertEqual((self.counts(scope)[0] - before[0], self.counts(scope)[1] - before[1]), (2, 1))
        # «visitas a tu ficha» of Estadísticas: the same visitors of each day (the API of the ficha no longer counts)
        self.client().get(f'/api/centers/{self.cid}', headers=dict(OTHER))
        st = self.server.sql("SELECT COALESCE(SUM(views),0) AS v FROM provider_stats_daily WHERE provider_type='center' AND provider_id=?", (self.cid,))[0]['v']
        self.assertEqual(st - st_before, 1)
        # the centre's own team on its ficha: only the web counts it, not the centre
        site = self.counts('site')
        self.visit(self.center, 'centro', self.cid, headers=OTHER)
        self.assertEqual(self.counts(scope)[0] - before[0], 2)
        self.assertEqual(self.counts('site')[0], site[0] + 1)
        # another centre's team member is a visitor like any other
        self.visit(self.other_center, 'centro', self.cid, headers=OTHER)
        self.assertEqual(self.counts(scope)[0] - before[0], 3)
        # a centre that is not public, or an id that does not exist: only the web
        self.server.sql('UPDATE centers SET active=0 WHERE id=?', (self.cid2,))
        try:
            self.visit(self.client(), 'centro', self.cid2); self.visit(self.client(), 'centro', 999999)
            self.assertEqual(self.counts(f'center:{self.cid2}'), (0, 0)); self.assertEqual(self.counts('center:999999'), (0, 0))
        finally:
            self.server.sql('UPDATE centers SET active=1 WHERE id=?', (self.cid2,))

    def test_6_el_perfil_del_profesional(self):
        pid = self.pro.user['id']
        self.visit(self.client(), 'profesional', pid)
        self.assertEqual(self.counts(f'freelance:{pid}')[0], 1)
        self.visit(self.pro, 'profesional', pid)                                            # himself: not counted for him
        self.assertEqual(self.counts(f'freelance:{pid}')[0], 1)
        self.visit(self.client(), 'profesional', self.center.user['id'])                    # a centre account is not a professional
        self.assertEqual(self.counts(f'freelance:{self.center.user["id"]}'), (0, 0))

    def test_7_no_se_guarda_ninguna_ip_y_la_sal_cambia_cada_dia(self):
        self.visit(self.client(), 'home')
        rows = self.server.sql('SELECT * FROM visit_seen')
        self.assertTrue(rows)
        for r in rows:
            self.assertNotIn('127.0.0.1', ' '.join(str(v) for v in r.values()))
            self.assertRegex(r['h'], r'^[0-9a-f]{24}$')
            self.assertEqual(r['day'], TODAY.isoformat())
        cols = {r['name'] for t in ('visit_counts', 'visit_seen') for r in self.server.sql(f'PRAGMA table_info({t})')}
        self.assertFalse(cols & {'ip', 'user_agent', 'user_id', 'session'}, cols)
        # a new day: a new salt, and the salts and the hashes of the days before are deleted
        self.server.sql("INSERT INTO site_settings(key,value,updated_at) VALUES('visitas_sal:2000-01-01','vieja','2000-01-01')")
        self.server.sql("INSERT INTO visit_seen(day,scope,h) VALUES('2000-01-01','site','aaaaaaaaaaaaaaaaaaaaaaaa')")
        self.server.sql("DELETE FROM site_settings WHERE key=?", (f'visitas_sal:{TODAY.isoformat()}',))
        self.visit(self.client(), 'home')
        salts = [r['key'] for r in self.server.sql("SELECT key FROM site_settings WHERE key LIKE 'visitas%'")]
        self.assertEqual(salts, [f'visitas_sal:{TODAY.isoformat()}'])
        self.assertEqual(self.server.sql("SELECT COUNT(*) AS n FROM visit_seen WHERE day<>?", (TODAY.isoformat(),))[0]['n'], 0)

    # ------------------------------------------------------------------------------------------------ the figures
    def add_booking(self, center_id, day, status, price, mode, pay_way=None, currency='EUR'):
        self.server.sql("""INSERT INTO bookings(user_id,center_id,booking_date,participants,status,price,currency,booking_mode,pay_way,created_at,updated_at)
                           VALUES(?,?,?,1,?,?,?,?,?,?,?)""", (self.diver.user['id'], center_id, day, status, price, currency, mode, pay_way, day, day))

    def test_8_reservas_por_modo_e_importe(self):
        today = TODAY.isoformat(); old = (TODAY.replace(day=1) - dt.timedelta(days=400)).isoformat()
        self.add_booking(self.cid, today, 'confirmed', 60, 'payment')
        self.add_booking(self.cid, today, 'requested', 45, 'request')
        self.add_booking(self.cid, today, 'completed', 30, 'request', 'in_person')
        self.add_booking(self.cid, today, 'cancelled', 999, 'payment')                    # cancelled: not counted
        self.add_booking(self.cid, old, 'completed', 80, 'payment')                       # only «desde el inicio»
        self.add_booking(self.cid2, today, 'confirmed', 500, 'payment')                   # another centre
        d = self.center.get('/api/provider/contador').json
        by = {p['key']: p for p in d['periods']}
        self.assertEqual(list(by), ['temporada', 'mes', 'todo'])
        mes, todo = by['mes'], by['todo']
        self.assertEqual(mes['bookings'], 3)
        self.assertEqual({m['mode']: m['bookings'] for m in mes['by_mode']}, {'payment': 1, 'request': 1, 'in_person': 1})
        self.assertEqual(mes['amounts'], [{'currency': 'EUR', 'amount': 90}])               # confirmed and completed only
        self.assertEqual(todo['bookings'], 4); self.assertEqual(todo['amounts'], [{'currency': 'EUR', 'amount': 170}])
        self.assertIsNone(todo['from'])
        self.assertGreaterEqual(todo['views'], 2)                                           # its ficha (test 5)
        # the administration: the whole web and every centre
        a = {p['key']: p for p in self.admin.get('/api/admin/contador').json['periods']}
        self.assertGreaterEqual(a['mes']['bookings'], 4)
        self.assertGreaterEqual(a['todo']['views'], self.counts('site')[0])

    def test_9_temporada_configurable(self):
        r = self.admin.post('/api/admin/settings', {'temporada_inicio': '11-01', 'temporada_fin': '04-30'})
        self.assertEqual(r.status, 200, r.json)
        try:
            p = self.admin.get('/api/admin/contador').json['periods'][0]
            self.assertEqual(p['key'], 'temporada')
            a, b = dt.date.fromisoformat(p['from']), dt.date.fromisoformat(p['to'])
            self.assertEqual(((a.month, a.day), (b.month, b.day)), ((11, 1), (4, 30)))
            self.assertEqual(b.year, a.year + 1)                                            # over new year
            self.assertTrue(re.match(r'temporada \d\d/\d\d/\d{4}–\d\d/\d\d/\d{4}', p['label']))
        finally:
            self.admin.post('/api/admin/settings', {'temporada_inicio': '04-01', 'temporada_fin': '10-31'})

    def test_10_quien_lo_ve(self):
        self.assertEqual(self.client().get('/api/admin/contador').status, 403)
        self.assertEqual(self.diver.get('/api/admin/contador').status, 403)
        self.assertEqual(self.center.get('/api/admin/contador').status, 403)
        self.assertEqual(self.diver.get('/api/provider/contador').status, 403)
        self.assertEqual(self.admin.get('/api/provider/contador').status, 403)
        self.assertEqual(self.pro.get('/api/provider/contador').status, 200)
        # a team member without «Estadísticas» does not see it; with it, the centre's figures (not the person's)
        r = self.center.post('/api/center/team/invite', {'email': 'vc-inst@example.org', 'member_role': 'instructor'})
        self.assertEqual(r.status, 200, r.json)
        tok = re.search(r'equipo\?token=([A-Za-z0-9_\-]+)', outbox(self.server, 'team_invite', 'vc-inst@example.org')[0]['text']).group(1)
        m = self.client()
        self.assertEqual(m.post('/api/team/join', {'token': tok, 'fullname': 'Persona Instructora', 'username': 'vc_inst', 'password': 'buceo-seguro-2026',
                                                   'accept_terms': True}).status, 200)
        self.assertEqual(m.get('/api/provider/contador').status, 403)
        self.assertEqual(self.center.post('/api/center/team/roles/save', {'key': 'instructor', 'name': 'Instructor', 'permissions': ['checkin', 'estadisticas']}).status, 200)
        mine = self.center.get('/api/provider/contador').json
        self.assertEqual(m.get('/api/provider/contador').json, mine)


class MismasPantallas(unittest.TestCase):
    def test_la_web_avisa_de_las_mismas_pantallas_que_cuenta_el_servidor(self):
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        js = (root / 'public' / 'js' / 'world-dives-v8.js').read_text(encoding='utf-8')
        py = (root / 'app' / 'server.py').read_text(encoding='utf-8')
        web = set(re.findall(r"'([a-z0-9-]+)'", re.search(r'WD_VISIT_PAGES=new Set\(\[(.*?)\]\)', js, re.S).group(1)))
        server = set(re.findall(r"'([a-z0-9-]+)'", re.search(r'VISIT_PAGES = \{(.*?)\}', py, re.S).group(1)))
        self.assertEqual(web, server)
        self.assertFalse(web & {'admin', 'cuenta', 'logbook', 'reserva', 'area', 'mis-puntos'})   # never a private screen


if __name__ == '__main__':
    unittest.main()
