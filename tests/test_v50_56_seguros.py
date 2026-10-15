"""v50.56 · Bloque 2: seguros de buceo. Las pruebas obligatorias del encargo, contra el servidor real.

Estados: un seguro vigente da 🟢; uno que caduca en 10 días da 🟠 y se envía el aviso; uno caducado da 🔴; sin seguro, ⚪.
Reserva: con «obligatorio» y el seguro caducado no se confirma hasta subir uno válido y no se pierden las plazas; con «se
comprueba en el centro» se deja reservar y se avisa.
Contratar: el botón abre la web correcta de la aseguradora, con el código de colaborador; no se envía ningún dato
personal; una dirección fuera de los dominios autorizados no se puede guardar.
Centro: ve el estado del seguro solo de sus buceadores y solo en el plazo permitido; no ve el documento si el buceador
no lo comparte; la póliza que sube el centro no llega al perfil sin el «sí» del buceador; cada vista queda registrada.
Archivos: un archivo falso con extensión .pdf se rechaza; uno de 20 MB se rechaza; el documento no se abre sin sesión con
permiso; las fotos se guardan sin EXIF. Canales: lo mismo por WORLDIVES, el widget y la API. Retención: 12 meses salvo
reserva en disputa.
"""
import datetime as dt
import io
import json
import subprocess
import sys
import zlib
from pathlib import Path

from helpers import ServerTestCase, Client
from stripe_mock import StripeMock

ROOT = Path(__file__).resolve().parents[1]
FAR = '2099-12-31'


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


def pdf(*lines):
    """A small real PDF with text (standard font), like the one an insurer sends."""
    content = b'BT /F1 11 Tf 72 760 Td ' + b' '.join(b'(' + l.encode('latin-1') + b') Tj 0 -16 Td' for l in lines) + b' ET'
    comp = zlib.compress(content)
    return (b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'
            b'3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]/Contents 4 0 R>>endobj\n4 0 obj<</Length ' + str(len(comp)).encode()
            + b'/Filter/FlateDecode>>stream\n' + comp + b'\nendstream\nendobj\ntrailer<</Root 1 0 R>>\n%%EOF\n')


def jpeg_with_exif():
    from PIL import Image
    im = Image.new('RGB', (64, 48), (10, 120, 200)); ex = Image.Exif(); ex[0x010F] = 'CamaraSecreta'; ex[0x0131] = 'GPS-Tracker'
    b = io.BytesIO(); im.save(b, 'JPEG', exif=ex); return b.getvalue()


class Seguros(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = dict(cls.extra_env, STRIPE_SECRET_KEY='sk_test_mock', WOD_STRIPE_API_BASE=cls.stripe.base, WOD_WIDGET_MAX_PER_HOUR='60',
                             WOD_TRUSTED_PROXIES='127.0.0.1', WOD_API_MAX_PER_MINUTE='400')
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'seguro', phone='+34 600 570 001')
        cls.other = t.make_center(cls.admin, 'seguro2', phone='+34 600 570 002')
        cls.cid = cls.center.user['center_id']
        for c in (cls.center, cls.other):
            cls.server.sql(f"UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_seg{c.user['center_id']}',"
                           "stripe_charges_enabled=1,stripe_payouts_enabled=1,country='España' WHERE id=?", (c.user['center_id'],))
        # Two invented insurers, configured in Administración (none is in the code)
        a = cls.admin.post('/api/admin/insurance/providers', {'name': 'Aseguradora Demo A', 'allowed_domains': 'demo-a.example.com', 'partner_code': 'WD123',
                                                               'collaborator': True, 'website': 'https://www.demo-a.example.com/'})
        assert a.status == 200, a
        cls.prov_a = a.json['id']
        cls.prod_a = cls.admin.post('/api/admin/insurance/products', {'provider_id': cls.prov_a, 'kind': 'dia', 'name': 'Seguro de un día', 'price_from': 4.5,
                                                                      'zones': ['europa'], 'countries': 'ES, PT',
                                                                      'diver_url': 'https://www.demo-a.example.com/contratar?socio={codigo}&tipo=dia',
                                                                      'center_url': 'https://centros.demo-a.example.com/alta?socio={codigo}'}).json['id']
        cls.prov_b = cls.admin.post('/api/admin/insurance/providers', {'name': 'Aseguradora Demo B', 'allowed_domains': 'demo-b.example.org', 'partner_code': 'B77',
                                                                       'featured': True}).json['id']
        cls.prod_b = cls.admin.post('/api/admin/insurance/products', {'provider_id': cls.prov_b, 'kind': 'dia', 'name': 'Día de buceo',
                                                                      'diver_url': 'https://demo-b.example.org/seguro-dia?ref={codigo}'}).json['id']
        # Services: «obligatorio» (request and payment), «se comprueba en el centro» (the default) and «no»
        mk = lambda title, mode, ins, price=50: cls.center.post('/api/provider-services', {'title': title, 'price': price, 'booking_mode': mode, 'max_participants': 6,
                                                                                         **({'insurance_required': ins} if ins else {})}).json['id']
        cls.s_req = mk('Inmersión obligatoria', 'request', 'online')
        cls.s_pay = mk('Bautizo obligatorio', 'payment', 'online', 70)
        cls.s_center = mk('Inmersión normal', 'request', None)
        cls.s_no = mk('Snorkel', 'request', 'no', 20)
        cls.slug = cls.center.get('/api/provider/vender').json['slug']
        cls.center.post('/api/provider/vender', {'domains': 'buceo-seguro.example.com'})
        cls.key = cls.center.post('/api/provider/api-keys', {'action': 'create', 'name': 'Web', 'scope': 'write'}).json['key']
        cls.n = 0

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def run_py(self, code):
        """Runs server code (the daily and hourly jobs) on the test copy of the database."""
        full = 'import sys; sys.path.insert(0, %r); import server, datetime; db=server.connect(); ' % str(ROOT / 'app') + code + '; db.close()'
        r = subprocess.run([sys.executable, '-c', full], env=self.server.env, cwd=str(self.server.tmp), capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)
        return r.stdout

    def diver(self):
        type(self).n += 1
        return self.make_diver(f'segbuzo{self.n}')

    def upload(self, client, valid_to, valid_from=None, content=None, name='poliza.pdf', **extra):
        fields = {'insurer': 'Aseguradora Demo A', 'provider_id': self.prov_a, 'policy_number': 'DA-2026-001', 'kind': 'anio', 'valid_to': valid_to,
                  'valid_from': valid_from or day(-30), 'zone': 'europa', 'max_depth': '40', **extra}
        return client.upload('/api/insurance/policies', fields, name, content or pdf('Aseguradora Demo A', f'Valido hasta: {valid_to}'))

    def slot(self, sid, n=4, d=None):
        """A new departure (its own day: the same service, day and time would be the same departure)."""
        type(self).n += 1
        r = self.center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': day(d if d is not None else 20 + self.n), 'slot_time': '10:00', 'spots_total': n})
        return r.json['slot_id']

    def slot_date(self, slot):
        return self.server.sql('SELECT slot_date FROM service_slots WHERE id=?', (slot,))[0]['slot_date']

    def free(self, slot):
        return self.server.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot,))[0]['spots_available']

    # ------------------------------------------------------------------------------------------------ states
    def test_cuatro_estados_y_aviso_a_10_dias(self):
        d = self.diver()
        st = d.get('/api/insurance').json['state']
        self.assertEqual((st['state'], st['icon']), ('sin_seguro', '⚪'))
        self.assertEqual(self.upload(d, day(200)).status, 200)
        self.assertEqual(d.get('/api/insurance').json['state']['icon'], '🟢')
        d2 = self.diver(); self.upload(d2, day(10))
        st = d2.get('/api/insurance').json['state']
        self.assertEqual((st['state'], st['icon'], st['days_left']), ('caduca_pronto', '🟠', 10))
        self.run_py('print(server.queue_insurance_notices(db))')
        mails = self.server.sql("SELECT subject FROM email_outbox WHERE template='insurance_diver_expiring' AND to_email=?", (d2.user['email'],))
        self.assertEqual(len(mails), 1, mails); self.assertIn('10 días', mails[0]['subject'])
        self.run_py('server.queue_insurance_notices(db)')   # once per mark, never twice
        self.assertEqual(len(self.server.sql("SELECT 1 FROM email_outbox WHERE template='insurance_diver_expiring' AND to_email=?", (d2.user['email'],))), 1)
        d3 = self.diver(); self.upload(d3, day(-5), day(-60))
        self.assertEqual(d3.get('/api/insurance').json['state']['icon'], '🔴')
        self.assertFalse(self.server.sql("SELECT 1 FROM email_outbox WHERE template='insurance_diver_expiring' AND to_email=?", (d.user['email'],)))   # 200 days left: nothing

    # ------------------------------------------------------------------------------------------------ files
    def test_archivos_seguros(self):
        d = self.diver(); stranger = self.diver()
        r = self.upload(d, day(100), content=b'Esto no es un PDF, solo texto con extension .pdf', name='falso.pdf')
        self.assertEqual(r.status, 400, r); self.assertIn('Formato', r.json['error'])
        try:   # 20 MB: refused (the server may even close the connection before reading it all)
            r = self.upload(d, day(100), content=b'%PDF-1.4\n' + b'0' * (20 * 1024 * 1024) + b'\n%%EOF\n'); status = r.status
        except OSError:
            status = 'cerrada'
        self.assertIn(status, (400, 413, 'cerrada'))
        self.assertFalse(self.server.sql('SELECT 1 FROM insurance_policies WHERE user_id=?', (d.user['id'],)))
        r = self.upload(d, day(100), content=jpeg_with_exif(), name='foto.jpg')
        self.assertEqual(r.status, 200, r)
        p = self.server.sql('SELECT file_path FROM insurance_policies WHERE id=?', (r.json['id'],))[0]
        stored = (Path(self.server.env.get('WOD_STORAGE_DIR') or (self.server.tmp / 'storage')) / p['file_path']).read_bytes()
        self.assertNotIn(b'CamaraSecreta', stored); self.assertNotIn(b'GPS-Tracker', stored)
        url = f"/api/insurance/policies/{r.json['id']}/file"
        self.assertEqual(d.get(url).status, 200)
        self.assertIn(Client(self.server).get(url).status, (401, 403))
        self.assertEqual(stranger.get(url).status, 404)
        self.assertTrue(self.server.sql("SELECT 1 FROM audit_log WHERE action='insurance_policy_denied' AND entity_id=?", (r.json['id'],)))
        self.assertEqual(d.post(f"/api/insurance/policies/{r.json['id']}/delete", {}).status, 200)
        self.assertFalse(self.server.sql('SELECT 1 FROM insurance_policies WHERE id=?', (r.json['id'],)))

    def test_lectura_del_pdf_solo_propone(self):
        d = self.diver()
        before = self.server.sql('SELECT COUNT(*) n FROM insurance_policies')[0]['n']
        r = d.upload('/api/insurance/leer', {}, 'poliza.pdf', pdf('Aseguradora Demo A', 'Poliza n: DA-2027-555', 'Fecha de efecto: 01/06/2027', 'Valido hasta: 31/05/2028'))
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['proposal'], {'valid_to': '2028-05-31', 'valid_from': '2027-06-01', 'policy_number': 'DA-2027-555'})
        self.assertEqual(self.server.sql('SELECT COUNT(*) n FROM insurance_policies')[0]['n'], before)   # nothing saved without confirmation

    # ------------------------------------------------------------------------------------------------ booking
    def test_obligatorio_no_confirma_y_guarda_las_plazas(self):
        d = self.diver(); self.upload(d, day(5), day(-100))   # expired by the day of the dive
        slot = self.slot(self.s_req)
        r = d.post('/api/bookings', {'center_id': self.cid, 'service_id': self.s_req, 'slot_id': slot, 'participants': 2})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['status'], 'insurance_pending'); self.assertEqual(r.json['insurance']['status'], 'expired')
        self.assertEqual(self.free(slot), 2)   # the spots are held while he uploads it
        bid = r.json['id']
        self.assertNotIn(bid, [b['id'] for b in self.center.get('/api/bookings').json['items']])   # not a booking for the centre yet
        self.assertFalse(self.server.sql("SELECT 1 FROM provider_feed WHERE booking_id=?", (bid,)))
        self.assertEqual(self.center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'}).status, 400)
        # He contracts it and uploads it: the booking goes on (request → the centre gets it)
        up = self.upload(d, day(400), day(-1), booking_id=bid)
        self.assertEqual(up.status, 200, up); self.assertEqual(up.json['booking']['status'], 'requested')
        b = self.server.sql('SELECT status, insurance_status, insurance_policy_id FROM bookings WHERE id=?', (bid,))[0]
        self.assertEqual((b['status'], b['insurance_status']), ('requested', 'ok'))
        self.assertTrue(self.server.sql("SELECT 1 FROM provider_feed WHERE booking_id=? AND event='booking.created'", (bid,)))
        # «Pago al reservar»: held while he uploads, then the payment, with the spots still his
        slot2 = self.slot(self.s_pay, 3)
        d2 = self.diver()
        r = d2.post('/api/bookings', {'center_id': self.cid, 'service_id': self.s_pay, 'slot_id': slot2, 'participants': 1})
        self.assertEqual((r.json['status'], self.free(slot2)), ('insurance_pending', 2))
        up = self.upload(d2, day(400), day(-1), booking_id=r.json['id'])
        self.assertEqual(up.json['booking']['status'], 'payment_in_progress'); self.assertTrue(up.json['booking']['checkout_url'].startswith('https://'))
        self.assertEqual(self.free(slot2), 2)
        # Nobody uploads anything in time: the spots are free again
        d3 = self.diver(); slot3 = self.slot(self.s_req, 2)
        r = d3.post('/api/bookings', {'center_id': self.cid, 'service_id': self.s_req, 'slot_id': slot3, 'participants': 2})
        self.assertEqual(self.free(slot3), 0)
        self.server.sql("UPDATE bookings SET hold_expires_at='2000-01-01T00:00:00' WHERE id=?", (r.json['id'],))
        self.run_py('server.run_booking_deadlines(db)')
        self.assertEqual(self.server.sql('SELECT status, expired_reason FROM bookings WHERE id=?', (r.json['id'],))[0], {'status': 'expired', 'expired_reason': 'insurance_missing'})
        self.assertEqual(self.free(slot3), 2)

    def test_se_comprueba_en_el_centro_deja_reservar_y_avisa(self):
        d = self.diver(); slot = self.slot(self.s_center)
        r = d.post('/api/bookings', {'center_id': self.cid, 'service_id': self.s_center, 'slot_id': slot, 'participants': 1})
        self.assertEqual((r.status, r.json['status'], r.json['insurance']), (200, 'requested', {'required': 'center', 'status': 'missing'}))
        mail = self.server.sql("SELECT text FROM email_outbox WHERE template='booking_request' AND to_email=? ORDER BY id DESC LIMIT 1", (d.user['email'],))[0]['text']
        self.assertIn('Recuerda llevar tu seguro de buceo vigente', mail); self.assertIn('/#/seguro?contratar=dia', mail)
        # A service that does not ask for it: nothing is said
        r = d.post('/api/bookings', {'center_id': self.cid, 'service_id': self.s_no, 'slot_id': self.slot(self.s_no), 'participants': 1})
        self.assertNotIn('insurance', r.json)

    # ------------------------------------------------------------------------------------------------ contract
    def test_contratar_enlace_codigo_y_sin_datos(self):
        d = self.diver()
        off = d.get('/api/insurance/offers?tipo=dia&pais=ES').json
        self.assertEqual([o['insurer'] for o in off['offers']], ['Aseguradora Demo B', 'Aseguradora Demo A'])   # «Destacado» first, and it says so
        b_, a_ = off['offers']
        self.assertTrue(b_['featured'] and b_['featured_text']); self.assertTrue(a_['collaborator'] and 'Colaborador' in a_['collaborator_text'])
        self.assertEqual(a_['notice'], 'La contratación se realiza en la web de Aseguradora Demo A. WORLDIVES no es aseguradora ni mediador de seguros.')
        self.assertEqual(off['not_insurer'], 'WORLDIVES no es aseguradora ni mediador de seguros.')
        self.assertEqual(d.get('/api/insurance/offers?tipo=dia&pais=FR').json['offers'][0]['insurer'], 'Aseguradora Demo B')   # A only sells in ES and PT
        r = Client(self.server, origin=None).get(a_['url'])   # the test client never follows redirects
        loc = r.headers.get('Location') or ''
        self.assertEqual((r.status, loc), (302, 'https://www.demo-a.example.com/contratar?socio=WD123&tipo=dia'))
        self.assertEqual(r.headers.get('Referrer-Policy'), 'no-referrer')
        for personal in (d.user['email'], d.user['email'].split('@')[0], 'segbuzo'):
            self.assertNotIn(personal, loc)
        self.assertEqual(sorted(loc.split('?')[1].split('&')), ['socio=WD123', 'tipo=dia'])   # only the insurer's own address and the partner code
        clicks = self.server.sql('SELECT * FROM insurance_clicks WHERE product_id=?', (self.prod_a,))
        self.assertEqual(sum(c['clicks'] for c in clicks), 1); self.assertEqual(set(clicks[0].keys()), {'month', 'provider_id', 'product_id', 'country', 'audience', 'clicks', 'policies'})
        r = Client(self.server, origin=None).get(f'/seguros/ir/{self.prod_a}?para=centro')
        self.assertEqual(r.headers.get('Location'), 'https://centros.demo-a.example.com/alta?socio=WD123')
        # A policy uploaded after the click is counted (without saying whose)
        self.upload(d, day(1), day(0), kind='dia', after_click=self.prod_a)
        self.assertEqual(sum(c['policies'] for c in self.server.sql('SELECT policies FROM insurance_clicks WHERE product_id=?', (self.prod_a,))), 1)
        # An address outside the authorised domains, or without https, cannot be saved
        for bad in ('https://evil.example.com/demo-a.example.com', 'http://www.demo-a.example.com/x', 'https://demo-a.example.com.evil.net/', 'javascript:alert(1)'):
            r = self.admin.post('/api/admin/insurance/products', {'provider_id': self.prov_a, 'kind': 'semana', 'name': 'Semana', 'diver_url': bad})
            self.assertEqual(r.status, 400, bad)
        self.assertEqual(Client(self.server, origin=None).get('/seguros/ir/999999').status, 404)

    # ------------------------------------------------------------------------------------------------ centre
    def test_centro_ve_solo_lo_suyo_en_su_plazo_y_queda_registrado(self):
        d = self.diver(); pol = self.upload(d, day(90), day(-5)).json['id']
        slot = self.slot(self.s_center, d=3)
        bid = d.post('/api/bookings', {'center_id': self.cid, 'service_id': self.s_center, 'slot_id': slot, 'participants': 1}).json['id']
        url = f'/api/center/bookings/{bid}/insurance'
        self.assertFalse(self.center.get(url).json['visible'])   # a request: not yet (from the confirmation)
        self.assertEqual(self.center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'}).status, 200)
        v = self.center.get(url).json
        main = v['participants'][0]
        self.assertEqual((v['visible'], main['state'], main['icon'], main['insurer'], main['valid_to']), (True, 'ok', '🟢', 'Aseguradora Demo A', day(90)))
        self.assertFalse(main['can_view_file']); self.assertNotIn('policy_number', json.dumps(v))
        self.assertEqual(self.center.get(f'/api/insurance/policies/{pol}/file').status, 404)   # he does not share it
        self.assertEqual(self.other.get(url).status, 404)   # another centre: nothing
        self.assertEqual(d.post('/api/insurance/share', {'share': True}).status, 200)
        self.assertTrue(self.center.get(url).json['participants'][0]['can_view_file'])
        self.assertEqual(self.center.get(f'/api/insurance/policies/{pol}/file').status, 200)
        self.assertEqual(self.other.get(f'/api/insurance/policies/{pol}/file').status, 404)
        log = self.server.sql("SELECT details FROM audit_log WHERE action='insurance_policy_viewed' AND entity_id=? ORDER BY id DESC LIMIT 1", (pol,))
        self.assertTrue(log and json.loads(log[0]['details'])['center_id'] == self.cid, log)
        # 7 days after the dive the centre no longer sees it
        self.server.sql("UPDATE bookings SET booking_date=?, status='completed' WHERE id=?", (day(-8), bid))
        self.assertFalse(self.center.get(url).json['visible'])
        self.assertEqual(self.center.get(f'/api/insurance/policies/{pol}/file').status, 404)
        # The planning shows the mark only in the window
        self.server.sql("UPDATE bookings SET booking_date=?, status='confirmed' WHERE id=?", (day(3), bid))
        items = {b['id']: b for b in self.center.get('/api/bookings').json['items']}
        self.assertEqual(items[bid]['insurance'], {'status': 'ok', 'icon': '🟢'})

    def test_poliza_del_centro_necesita_el_si_del_buceador(self):
        d = self.diver(); slot = self.slot(self.s_center, d=2)
        bid = d.post('/api/bookings', {'center_id': self.cid, 'service_id': self.s_center, 'slot_id': slot, 'participants': 1}).json['id']
        self.center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})
        self.assertEqual(self.center.get(f'/api/center/bookings/{bid}/insurance').json['participants'][0]['icon'], '⚪')
        r = self.center.upload(f'/api/center/bookings/{bid}/insurance', {'insurer': 'Aseguradora Demo A', 'kind': 'dia', 'valid_from': day(2), 'valid_to': day(2)}, 'dia.pdf',
                               pdf('Seguro de dia'))
        self.assertEqual((r.status, r.json['pending_acceptance'], r.json['covers']), (200, True, True), r)
        self.assertEqual(d.get('/api/insurance').json['state']['state'], 'sin_seguro')   # not in his profile without his «sí»
        self.assertEqual(len(d.get('/api/insurance').json['pending']), 1)
        mail = self.server.sql("SELECT subject FROM email_outbox WHERE template='insurance_policy_added' AND to_email=?", (d.user['email'],))
        self.assertTrue(mail and 'Centro seguro' in mail[0]['subject'], mail)
        self.assertEqual(self.center.get(f'/api/center/bookings/{bid}/insurance').json['participants'][0]['icon'], '🟢')   # valid for that booking
        self.assertEqual(d.post(f"/api/insurance/policies/{r.json['id']}/accept", {}).status, 200)
        self.assertEqual(len(d.get('/api/insurance').json['policies']), 1)
        # Another one he does not keep: it stays only in that booking
        r2 = self.center.upload(f'/api/center/bookings/{bid}/insurance', {'insurer': 'Aseguradora Demo B', 'kind': 'dia', 'valid_to': day(2)}, 'b.pdf', pdf('B'))
        d.post(f"/api/insurance/policies/{r2.json['id']}/decline", {})
        self.assertEqual(self.server.sql('SELECT status FROM insurance_policies WHERE id=?', (r2.json['id'],))[0]['status'], 'booking')
        self.assertEqual(len(d.get('/api/insurance').json['policies']), 1)
        self.assertEqual(self.other.upload(f'/api/center/bookings/{bid}/insurance', {'insurer': 'X', 'valid_to': day(2)}, 'x.pdf', pdf('X')).status, 404)

    # ------------------------------------------------------------------------------------------------ channels
    def test_canales_widget_y_api(self):
        slot = self.slot(self.s_req, 4)
        r = Client(self.server).post(f'/api/w/{self.slug}/reservar', {'service_id': self.s_req, 'slot_id': slot, 'participants': 1, 'fullname': 'Cliente Web',
                                                                       'email': 'web.seguro@example.org', 'accept_policy': True, 'canal': 'widget',
                                                                       'host_url': 'https://buceo-seguro.example.com/'},
                                     headers={'Idempotency-Key': 'seg-widget-1', 'X-Forwarded-For': '198.51.100.77'})
        self.assertEqual((r.status, r.json['status'], r.json['insurance']['status']), (200, 'insurance_pending', 'missing'), r)
        self.assertEqual(self.free(slot), 3)
        tok = r.json['token']
        view = Client(self.server).get(f'/api/mi-reserva/{tok}').json['booking']
        self.assertEqual((view['status'], view['insurance']['required']), ('insurance_pending', 'online'))
        bad = Client(self.server).upload(f'/api/mi-reserva/{tok}/seguro', {'insurer': 'Aseguradora Demo A', 'valid_to': day(5)}, 'p.pdf', pdf('corto'))
        self.assertEqual(bad.status, 400)   # does not cover the day of the dive
        sd = self.slot_date(slot)
        ok = Client(self.server).upload(f'/api/mi-reserva/{tok}/seguro', {'insurer': 'Aseguradora Demo A', 'valid_from': sd, 'valid_to': sd}, 'p.pdf', pdf('ok'))
        self.assertEqual((ok.status, ok.json['booking']['status']), (200, 'requested'), ok)
        self.assertEqual(Client(self.server).get(f'/api/mi-reserva/{tok}').json['booking']['insurance']['status'], 'ok')
        # The widget's catalogue and offers
        cat = Client(self.server).get(f'/api/w/{self.slug}?canal=widget').json
        self.assertEqual({s['title']: s['insurance'] for s in cat['services']}['Inmersión obligatoria'], 'online')
        self.assertEqual([o['insurer'] for o in Client(self.server).get(f'/api/w/{self.slug}/seguros?tipo=dia').json['offers']], ['Aseguradora Demo B', 'Aseguradora Demo A'])
        # The API: the field in services and bookings; without insurance it waits; with the one the centre checked, it goes on
        api = lambda m, p, body=None: (Client(self.server, origin=None).request(m, p, data=body, headers={'Authorization': f'Bearer {self.key}'}) if m == 'POST'
                                       else Client(self.server, origin=None).get(p, headers={'Authorization': f'Bearer {self.key}'}))
        svc = {s['id']: s for s in api('GET', '/api/v1/services').json['data']}
        self.assertEqual((svc[self.s_req]['insurance_required'], svc[self.s_center]['insurance_required'], svc[self.s_no]['insurance_required']), ('online', 'center', 'no'))
        r = api('POST', '/api/v1/bookings', {'service_id': self.s_req, 'departure_id': slot, 'participants': 1, 'customer': {'name': 'Cliente API', 'email': 'api.seg@example.org'}})
        self.assertEqual((r.status, r.json['booking']['status'], r.json['booking']['insurance']['status'], r.json.get('insurance_required')), (201, 'insurance_pending', 'missing', True))
        r = api('POST', '/api/v1/bookings', {'service_id': self.s_req, 'departure_id': slot, 'participants': 1, 'customer': {'name': 'Cliente API 2', 'email': 'api2.seg@example.org'},
                                            'insurance': {'insurer': 'Aseguradora Demo A', 'valid_to': day(400)}})
        self.assertEqual((r.status, r.json['booking']['status'], r.json['booking']['insurance']['status']), (201, 'requested', 'declared'))

    # ------------------------------------------------------------------------------------------------ retention and admin
    def test_retencion_12_meses_salvo_disputa(self):
        d = self.diver()
        old = self.upload(d, day(-400), day(-765)).json['id']
        kept = self.upload(d, day(-390), day(-760)).json['id']
        # a booking covered by the second one is in dispute
        self.server.sql("INSERT INTO bookings(user_id,center_id,booking_date,participants,status,price,created_at,updated_at) VALUES(?,?,?,1,'completed',50,?,?)",
                        (d.user['id'], self.cid, day(-395), day(-400), day(-400)))
        bk = self.server.sql('SELECT MAX(id) AS id FROM bookings')[0]['id']
        self.server.sql("INSERT INTO payment_orders(user_id,booking_id,amount,currency,status,provider,created_at,updated_at,incident,payee_type,payee_id) VALUES(?,?,50,'EUR','paid','stripe',?,?,'dispute','center',?)",
                        (d.user['id'], bk, day(-400), day(-400), self.cid))
        self.run_py('print(server.run_insurance_retention(db))')
        left = {r['id'] for r in self.server.sql('SELECT id FROM insurance_policies WHERE user_id=?', (d.user['id'],))}
        self.assertNotIn(old, left); self.assertIn(kept, left)

    def test_administracion_textos_y_estadisticas(self):
        texts = {'en': {'notice': 'Bought on the {insurer} website. WORLDIVES is not an insurer.'}}
        self.assertEqual(self.admin.post('/api/admin/insurance/texts', {'texts': texts, 'order': 'alpha'}).status, 200)
        adm = self.admin.get('/api/admin/insurance').json
        self.assertEqual(len(adm['texts']), 9); self.assertEqual(adm['texts']['en']['notice'], texts['en']['notice'])
        self.assertEqual(adm['texts']['de']['notice'], adm['defaults']['de']['notice'])
        self.assertTrue(any(p['name'] == 'Aseguradora Demo A' for p in adm['providers']))
        d = self.diver()
        self.assertEqual(d.get('/api/admin/insurance').status, 403)
        self.assertEqual(d.post('/api/admin/insurance/providers', {'name': 'X', 'allowed_domains': 'x.com'}).status, 403)
        off = Client(self.server).get('/api/insurance/offers?tipo=dia&pais=ES&lang=en').json
        self.assertEqual(off['offers'][1]['notice'], 'Bought on the Aseguradora Demo A website. WORLDIVES is not an insurer.')
        self.assertEqual(Client(self.server).get('/api/insurance/offers?tipo=dia&pais=ES&lang=pl').json['offers'][1]['notice'],
                         'Ubezpieczenie zawiera się na stronie Aseguradora Demo A. WORLDIVES nie jest ubezpieczycielem ani pośrednikiem ubezpieczeniowym.')
        self.assertEqual(Client(self.server, origin=None).request('POST', f'/api/insurance/webhook/{self.prov_a}', data={'x': 1}).status, 404)   # direct connection: off

    # ------------------------------------------------------------------------------------------------ languages
    def test_avisos_y_ventana_en_9_idiomas(self):
        """The notices (e-mail and app) and the texts of the window, in the 9 languages of the web."""
        code = ("import json; out={}\n"
                "for l in ('es','en','fr','de','it','pt','pl','nl','zh'):\n"
                "    ctx={'expiry_title': server.mail_t(l,'Tu seguro de buceo caduca en {days} días',days=30),'first_name':'Bea','insurer':'Aseguradora Demo A',"
                "'valid_to_text':'14/11','insurance_url':'https://x','center':'Mar Azul','kind_text':server.mail_t(l,'Día').lower(),'valid_text':'14/11'}\n"
                "    a=server.render_email(db,'insurance_diver_expiring',l,ctx); b=server.render_email(db,'insurance_policy_added',l,ctx)\n"
                "    out[l]=[a[0],a[2],b[0],b[2],server.mail_t(l,'Tu seguro de buceo caduca hoy')]\n"
                "print(json.dumps(out))")
        out = json.loads(self.run_py(code).strip().splitlines()[-1])
        es = out['es']
        self.assertIn('30 días', es[0]); self.assertIn('Renovar o contratar seguro', es[1]); self.assertIn('Mar Azul ha añadido tu seguro de buceo', es[2])
        for l in ('en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh'):
            with self.subTest(lang=l):
                self.assertNotEqual(out[l][0], es[0]); self.assertIn('30', out[l][0])
                self.assertNotIn('Renovar o contratar seguro', out[l][1]); self.assertNotIn('Hola Bea', out[l][1])
                self.assertNotEqual(out[l][2], es[2]); self.assertIn('Mar Azul', out[l][2])
                self.assertNotEqual(out[l][4], es[4])
        # The web: every text of «Mi seguro de buceo» and of the window has its translation in the 8 language packs
        keys = ['Mi seguro de buceo', 'Contrata tu seguro de buceo', 'Contratar en', '¿Ya lo tienes? Sube tu póliza', 'Destacado', 'Colaborador', 'Vigente',
                'Caduca pronto', 'Caducado', 'Sin seguro', 'Recuerda llevar tu seguro de buceo vigente.', 'Contratar seguro del día', 'Dar de alta seguro',
                'Seguro caducado ese día', 'Contratar o renovar seguro de RC del centro', 'Exige seguro de buceo']
        for l in ('en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh'):
            pack = json.loads((ROOT / 'public' / 'idiomas' / f'{l}.json').read_text(encoding='utf-8'))
            with self.subTest(web=l):
                self.assertEqual([k for k in keys if not pack['exact'].get(k)], [])
        # The legal notice of the window comes in the language asked for (texts of Administración → Seguros)
        notices = {l: Client(self.server).get(f'/api/insurance/offers?tipo=dia&pais=ES&lang={l}').json['not_insurer'] for l in ('es', 'en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh')}
        self.assertEqual(len(set(notices.values())), 9, notices)
