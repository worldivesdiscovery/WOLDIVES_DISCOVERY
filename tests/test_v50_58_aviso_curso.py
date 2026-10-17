"""v50.58 (3.5): «Tu sesión del curso pasa a otro día» también por WhatsApp.

El titular dejó a elección el texto de la plantilla («profesional, claro, sin textazos, conciso y agradable»). Meta y
Stripe son simuladores locales: nada sale de la máquina. Comprueba:
- la plantilla nueva en los 9 idiomas cumple las reglas de Meta (variables en orden y nunca al principio, al final ni
  juntas; sin saltos de línea; categoría UTILIDAD; botón con el enlace firmado) y se crea al conectar WhatsApp;
- al pasar una sesión a otro día sale por WhatsApp desde el número del centro, con el centro, el curso, la sesión, la
  nueva fecha con su instructor y si tiene coste; nunca con precios (un suplemento solo se menciona);
- en el idioma del buceador; sin su permiso no sale nada por WhatsApp (el correo y la app sí);
- con la plantilla aún sin aprobar por Meta no se envía y el centro ve por qué;
- «Comprobar plantillas» crea en la cuenta del centro las que le faltan (los centros conectados antes de esta versión);
- el enlace del botón abre solo esa reserva, con la sesión y su nueva fecha, y no sirve para cambiar nada;
- otro centro no ve el aviso;
- la migración de una base anterior conserva los avisos (con copia previa) y admite el tipo nuevo.
"""
import datetime as dt
import http.client
import json
import re
import subprocess
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from helpers import ServerTestCase, Client, Server, ROOT  # noqa: E402
from meta_mock import MetaMock  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from wod import avisos as wav  # noqa: E402
from wod import whatsapp as wwa  # noqa: E402

SECRET = 'whsec_connect_local'
NAME = 'worldives_curso_nueva_fecha'
FAR = '2099-12-31'


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


def wait_for(fn, seconds=25):
    end = time.time() + seconds
    while time.time() < end:
        v = fn()
        if v: return v
        time.sleep(0.3)
    return fn()


class Template(unittest.TestCase):
    def test_the_template_follows_metas_rules_in_the_9_languages(self):
        payloads = [p for p in wwa.template_payloads(wav.data(), 'https://worlddivesdiscovery.com') if p['name'] == NAME]
        self.assertEqual(sorted(p['language'] for p in payloads), sorted(wwa.META_LANG.values()))
        for p in payloads:
            self.assertEqual(p['category'], 'UTILITY')
            body = p['components'][0]['text']
            self.assertEqual(re.findall(r'\{\{(\d+)\}\}', body), ['1', '2', '3', '4', '5'], p['language'])   # in order
            self.assertFalse(body.lstrip().startswith('{{') or body.rstrip().endswith('}}'), p['language'])
            self.assertNotRegex(body, r'\}\}\s*\{\{', p['language'])                                        # never side by side
            self.assertNotIn('\n', body); self.assertLess(len(body), 1024)
            self.assertEqual(len(p['components'][0]['example']['body_text'][0]), 5)
            self.assertTrue(p['components'][1]['buttons'][0]['url'].endswith('/r/{{1}}'))
            self.assertNotRegex(body, r'€|\d+[.,]\d\d', 'no prices in the template')
        es = wav.body('course_moved', 'es', wav.params('course_moved', 'es', center='Bahía', date='sábado, 14 de noviembre de 2026 a las 09:00 con Marta',
                                                        time_='', course='Open Water', session='inmersión 4'))
        self.assertEqual(es, 'Hola. Bahía ha cambiado la fecha de una sesión de tu curso Open Water (inmersión 4). Nueva fecha: sábado, 14 de noviembre de 2026 a '
                             'las 09:00 con Marta. Sigue dentro de tu curso, sin coste añadido. Confírmala o pide otro día desde tu reserva.')


class CourseWhatsApp(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.meta = MetaMock()
        cls.meta.add_business('codeA', 'wabaA', [('pnidA', '+34 600 000 333')])
        cls.meta.add_business('codeB', 'wabaB', [('pnidB', '+34 600 000 444')])
        cls.extra_env = {**cls.meta.env(), 'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base, 'STRIPE_CONNECT_WEBHOOK_SECRET': SECRET,
                         'WOD_AVISOS_SEGUNDOS': '1', 'WOD_MAINTENANCE_SECONDS': '2', 'WOD_PAYMENTS_TOTP_REQUIRED': '0',
                         'WOD_DATA_KEY': 'clave-de-datos-de-las-pruebas-0123456789'}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.A = t.make_center(cls.admin, 'cursowa', phone='+34 600 590 001')
        cls.B = t.make_center(cls.admin, 'cursowb', phone='+34 600 590 002')
        cls.cid = cls.A.user['center_id']
        cls.server.sql(f"""UPDATE centers SET name='Bahía Curso',plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_cursowa',
                           stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?""", (cls.cid,))
        assert cls.A.post('/api/whatsapp/connect', {'code': 'codeA', 'waba_id': 'wabaA', 'phone_number_id': 'pnidA'}).status == 200
        assert cls.B.post('/api/whatsapp/connect', {'code': 'codeB', 'waba_id': 'wabaB', 'phone_number_id': 'pnidB'}).status == 200
        cls.server.sql("INSERT INTO users(fullname,email,username,password_hash,role,center_id,created_at) VALUES('Marta Instructora','marta@cursowa.example.org','cwa_marta','!','center',?,datetime('now'))", (cls.cid,))
        cls.marta = cls.server.sql("SELECT id FROM users WHERE username='cwa_marta'")[0]['id']
        dive = cls.A.post('/api/provider-services', {'title': 'Doble inmersión', 'price': 40, 'booking_mode': 'payment'}).json['id']
        cls.dep = cls.A.post('/api/provider-services/slot', {'service_id': dive, 'slot_date': day(12), 'slot_time': '09:00', 'spots_total': 20}).json['slot_id']
        r = cls.A.post('/api/provider-services/wizard', {'publish': True, 'kind': 'course', 'title': 'Open Water', 'plan': {'days': ['full', 'full'], 'dives': [1, 2, 3, 4]},
                                                         'price': 450, 'max_participants': 8, 'booking_mode': 'payment', 'instructor_user_id': cls.marta,
                                                         'schedule': {'mode': 'dates', 'dates': [day(30)]}})
        assert r.status == 200, r
        cls.course = r.json['id']
        cls.edition = cls.server.sql('SELECT id FROM service_slots WHERE service_id=?', (cls.course,))[0]['id']
        cls.divers = {}

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop(); cls.meta.stop()

    # ------------------------------------------------------------------------------------------------- helpers
    def diver(self, tag, lang='es', consent=True):
        d = self.make_diver(tag)
        n = 200 + len(self.divers)
        body = {'preferred_language': lang, 'wa_consent': consent, 'phone': f'+34 611 {n:03d} {n:03d}'}
        self.assertEqual(d.post('/api/account/profile', body).status, 200)
        self.divers[tag] = (d, f'34611{n:03d}{n:03d}')
        return self.divers[tag]

    def booked(self, d):
        r = d.post('/api/bookings', {'center_id': self.cid, 'service_id': self.course, 'slot_id': self.edition, 'participants': 1})
        self.assertEqual(r.status, 200, r)
        sess = self.stripe.last_session(); self.stripe.pay(sess['id'])
        ev = {'id': f'evt_{time.time_ns()}', 'type': 'checkout.session.completed', 'account': 'acct_cursowa',
              'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
        payload, sig = StripeMock.signed(ev, SECRET)
        Client(self.server, origin=None).request('POST', '/api/payments/webhook/connect', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
        self.assertEqual(self.server.sql('SELECT status FROM bookings WHERE id=?', (r.json['id'],))[0]['status'], 'confirmed')
        return r.json['id']

    def move(self, bid, **kw):
        r = self.A.post(f'/api/center/bookings/{bid}/course/move', {'seq': 4, 'mode': 'join', 'slot_id': self.dep, **kw})
        self.assertEqual(r.status, 200, r)

    def sent_to(self, phone):
        return [m for m in self.meta.sent if m['template'] == NAME and m['to'] == phone]

    @staticmethod
    def params(msg):
        body = next(c for c in msg['components'] if c['type'] == 'body')
        return [p['text'] for p in body['parameters']]

    @staticmethod
    def button(msg):
        return next(c for c in msg['components'] if c['type'] == 'button')['parameters'][0]['text']

    # ------------------------------------------------------------------------------------------------- tests
    def test_1_created_when_connecting(self):
        tpl = self.meta.templates['wabaA']
        self.assertEqual(sorted(k.split(':')[1] for k in tpl if k.startswith(NAME + ':')), sorted(wwa.META_LANG.values()))
        st = self.A.get('/api/avisos/ajustes').json['whatsapp']['templates']
        self.assertEqual((st['approved'], st['total']), (36, 36))

    def test_2_sent_from_the_centres_number_in_spanish(self):
        d, phone = self.diver('cwa_es')
        bid = self.booked(d)
        self.move(bid)
        msg = wait_for(lambda: self.sent_to(phone))
        self.assertTrue(msg, 'the WhatsApp of the course notice was not sent')
        msg = msg[0]
        self.assertEqual((msg['phone_number_id'], msg['lang']), ('pnidA', 'es'))
        p = self.params(msg)
        self.assertEqual(p[:3], ['Bahía Curso', 'Open Water', 'inmersión 4'])
        self.assertIn('a las 09:00 con Marta Instructora', p[3])
        self.assertEqual(p[4], 'Sigue dentro de tu curso, sin coste añadido.')
        row = wait_for(lambda: (lambda r: r if r and r[0]['status'] == 'sent' else None)(
            self.server.sql("SELECT * FROM notice_outbox WHERE booking_id=? AND event LIKE 'course_moved:%'", (bid,))))
        self.assertEqual((row[0]['channel'], row[0]['template']), ('whatsapp', NAME))
        batch = self.server.sql('SELECT * FROM notice_batches WHERE id=?', (row[0]['batch_id'],))[0]
        self.assertEqual((batch['kind'], batch['provider_id'], batch['course_seq'], batch['new_date']), ('course_moved', f'c:{self.cid}', 4, day(12)))
        self.assertEqual(wait_for(lambda: self.server.sql('SELECT status FROM notice_batches WHERE id=?', (batch['id'],))[0]['status'] == 'done'), True)
        # the email and the app are still sent as before (one each), never twice
        self.assertEqual(len(self.server.sql("SELECT 1 FROM email_outbox WHERE template='course_session_moved' AND related_id=?", (bid,))), 1)
        # the button opens only that booking, with the session and its new date, and cannot change anything
        link = self.button(msg)
        self.assertRegex(link, r'^[0-9a-z]+\.k\.[0-9a-z]+\.[A-Za-z0-9_\-]+$')
        # what the diver taps in WhatsApp: /r/<link> opens the web on that booking
        host, port = self.server.base.split('//')[1].split(':')
        c = http.client.HTTPConnection(host, int(port), timeout=10); c.request('GET', f'/r/{link}'); rr = c.getresponse()
        self.assertIn(rr.status, (301, 302, 303)); self.assertEqual(rr.getheader('Location'), f'/#/r/{link}'); c.close()
        anon = Client(self.server)
        v = anon.get(f'/api/r/{link}')
        self.assertEqual(v.status, 200, v)
        self.assertEqual(v.json['kind'], 'course_moved')
        self.assertEqual(v.json['session'], {'label': 'Inmersión 4', 'date': day(12), 'time': '09:00', 'who': 'Marta Instructora'})
        self.assertEqual(v.json['booking']['id'], bid)
        self.assertNotIn('email', json.dumps(v.json).lower().replace('center_email', ''))
        self.assertEqual(anon.post(f'/api/r/{link}', {'choice': 'refund'}).status, 403)
        # the centre sees it in its history; another centre does not
        uid = batch['uid']
        self.assertIn(uid, [x['uid'] for x in self.A.get('/api/avisos').json['items']])
        self.assertEqual(self.B.get(f'/api/avisos/{uid}').status, 404)
        self.assertNotIn(uid, [x['uid'] for x in self.B.get('/api/avisos').json['items']])

    def test_3_in_english_and_a_supplement_without_its_price(self):
        d, phone = self.diver('cwa_en', lang='en')
        bid = self.booked(d)
        self.move(bid, surcharge=35, surcharge_label='Barco extra')
        msg = wait_for(lambda: self.sent_to(phone))
        self.assertTrue(msg)
        p = self.params(msg[0])
        self.assertEqual(msg[0]['lang'], 'en')
        self.assertEqual(p[2], 'dive 4')
        self.assertIn('at 09:00 with Marta Instructora', p[3])
        self.assertEqual(p[4], 'The centre has added a supplement: you will see it in your booking.')
        self.assertFalse(any('35' in x or '€' in x for x in p), p)

    def test_4_without_permission_nothing_by_whatsapp(self):
        d, phone = self.diver('cwa_no', consent=False)
        bid = self.booked(d)
        self.move(bid)
        self.assertTrue(wait_for(lambda: self.server.sql("SELECT 1 FROM email_outbox WHERE template='course_session_moved' AND related_id=?", (bid,))))
        time.sleep(3)
        self.assertEqual(self.sent_to(phone), [])
        self.assertEqual(self.server.sql("SELECT COUNT(*) AS n FROM notice_outbox WHERE booking_id=?", (bid,))[0]['n'], 0)

    def test_5_template_not_approved_yet(self):
        d, phone = self.diver('cwa_pend')
        bid = self.booked(d)
        acc = self.server.sql("SELECT templates FROM whatsapp_accounts WHERE provider_id=?", (f'c:{self.cid}',))[0]
        tpl = json.loads(acc['templates']); tpl[f'{NAME}:es'] = 'PENDING'
        self.server.sql('UPDATE whatsapp_accounts SET templates=? WHERE provider_id=?', (json.dumps(tpl), f'c:{self.cid}'))
        try:
            self.move(bid)
            row = self.server.sql("SELECT status, skip_reason FROM notice_outbox WHERE booking_id=?", (bid,))
            self.assertEqual(row[0]['status'], 'skipped')
            self.assertIn('todavía no está aprobada por Meta', row[0]['skip_reason'])
            time.sleep(3)
            self.assertEqual(self.sent_to(phone), [])
        finally:
            tpl[f'{NAME}:es'] = 'APPROVED'
            self.server.sql('UPDATE whatsapp_accounts SET templates=? WHERE provider_id=?', (json.dumps(tpl), f'c:{self.cid}'))

    def test_6_check_templates_creates_the_missing_ones(self):
        # a centre connected before this version: neither Meta nor WORLDIVES have the course template
        for k in [k for k in self.meta.templates['wabaB'] if k.startswith(NAME + ':')]: del self.meta.templates['wabaB'][k]
        acc = self.server.sql("SELECT templates FROM whatsapp_accounts WHERE provider_id=?", (f'c:{self.B.user["center_id"]}',))[0]
        old = {k: v for k, v in json.loads(acc['templates']).items() if not k.startswith(NAME + ':')}
        self.server.sql('UPDATE whatsapp_accounts SET templates=? WHERE provider_id=?', (json.dumps(old), f'c:{self.B.user["center_id"]}'))
        st = self.B.get('/api/avisos/ajustes').json['whatsapp']['templates']
        self.assertEqual((st['approved'], st['total']), (27, 36), 'the missing template shows as missing')
        r = self.B.post('/api/whatsapp/templates/refresh', {})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(sorted(k.split(':')[1] for k in self.meta.templates['wabaB'] if k.startswith(NAME + ':')), sorted(wwa.META_LANG.values()))
        st = r.json['templates']
        self.assertEqual((st['approved'], st['total']), (36, 36))

    def test_7_the_daily_job_creates_them_without_the_centre_doing_anything(self):
        bkey = f'c:{self.B.user["center_id"]}'
        for k in [k for k in self.meta.templates['wabaB'] if k.startswith(NAME + ':')]: del self.meta.templates['wabaB'][k]
        acc = self.server.sql("SELECT templates FROM whatsapp_accounts WHERE provider_id=?", (bkey,))[0]
        self.server.sql('UPDATE whatsapp_accounts SET templates=? WHERE provider_id=?',
                        (json.dumps({k: v for k, v in json.loads(acc['templates']).items() if not k.startswith(NAME + ':')}), bkey))
        code = 'import sys; sys.path.insert(0, %r)\nimport server\ndb = server.connect()\nserver.run_whatsapp_template_jobs(db)\ndb.commit()\n' % str(ROOT / 'app')
        r = subprocess.run([sys.executable, '-c', code], env=self.server.env, cwd=str(self.server.tmp), capture_output=True, text=True, timeout=120)
        self.assertEqual(r.returncode, 0, r.stderr)
        self.assertEqual(sorted(k.split(':')[1] for k in self.meta.templates['wabaB'] if k.startswith(NAME + ':')), sorted(wwa.META_LANG.values()))
        st = json.loads(self.server.sql("SELECT templates FROM whatsapp_accounts WHERE provider_id=?", (bkey,))[0]['templates'])
        self.assertEqual(sum(1 for k, v in st.items() if k.startswith(NAME + ':') and v == 'APPROVED'), 9)


class Migration(unittest.TestCase):
    def test_an_older_database_keeps_its_notices_and_accepts_the_new_kind(self):
        srv = Server().start()
        try:
            t = ServerTestCase('run'); ServerTestCase.server = srv
            center = t.make_center(t.make_admin(), 'migra', phone='+34 600 591 001')
            sid = center.post('/api/provider-services', {'title': 'Salida', 'price': 30, 'booking_mode': 'request'}).json['id']
            slot = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': day(5), 'slot_time': '09:00', 'spots_total': 8}).json['slot_id']
            key = f"c:{center.user['center_id']}"
        finally:
            srv.stop(cleanup=False)
        code = '''
import json, sys
sys.path.insert(0, %r)
import server
db = server.connect()
db.execute('PRAGMA foreign_keys=OFF')
sql = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='notice_batches'").fetchone()[0]
old = sql.replace(",'course_moved'", '').replace(' course_seq INTEGER,', '')
assert old != sql
db.execute('DROP TABLE notice_batches'); db.execute(old)        # the table as it was in v50.57
db.execute("INSERT INTO notice_batches(uid,provider_id,slot_id,kind,status,run_after,created_at) VALUES('antiguo',?,?,'reminder','done',datetime('now'),datetime('now'))", (%r, %d))
db.commit(); db.execute('PRAGMA foreign_keys=ON')
server.migrate_notices_v50_58(db); db.commit()
sql = db.execute("SELECT sql FROM sqlite_master WHERE type='table' AND name='notice_batches'").fetchone()[0]
cols = [r['name'] for r in db.execute('PRAGMA table_info(notice_batches)').fetchall()]
kept = [r['uid'] for r in db.execute('SELECT uid FROM notice_batches').fetchall()]
db.execute("INSERT INTO notice_batches(uid,provider_id,slot_id,kind,status,run_after,created_at,course_seq) VALUES('nuevo',?,?,'course_moved','running',datetime('now'),datetime('now'),4)", (%r, %d))
backups = [p.name for p in (server.DB_PATH.parent / 'backups').glob('*v50_58_avisos*')]
print(json.dumps({'check': 'course_moved' in sql, 'cols': 'course_seq' in cols, 'kept': kept, 'backups': backups}))
''' % (str(ROOT / 'app'), key, slot, key, slot)
        try:
            r = subprocess.run([sys.executable, '-c', code], env=srv.env, cwd=str(srv.tmp), capture_output=True, text=True, timeout=120)
            self.assertEqual(r.returncode, 0, r.stderr)
            out = json.loads(r.stdout.strip().splitlines()[-1])
            self.assertTrue(out['check'] and out['cols'], out)
            self.assertEqual(out['kept'], ['antiguo'], 'the notices of before are kept')
            self.assertTrue(out['backups'], 'a full copy of the database before rebuilding the table')
        finally:
            srv.stop()


if __name__ == '__main__':
    unittest.main()
