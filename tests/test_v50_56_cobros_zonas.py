"""v50.56 · Bloque 1, pruebas obligatorias de cobros y de zonas horarias.

Stripe:
  - una reserva del widget y otra de la API se cobran en la cuenta de Stripe del centro (cargo directo);
  - al cancelarlas desde el panel o por la API la devolución sale de esa misma cuenta, por el importe pagado, y las
    plazas vuelven a estar libres en todos los canales; si cancela el cliente con su enlace, se propone la devolución
    de la política del centro y el centro la hace desde su cuenta (como en WORLDIVES desde la Fase 2.4).

Zonas horarias (un centro en Cancún y otro en Madrid, las dos salidas a las 09:00 hora local):
  - el widget enseña las 09:00 de cada centro, se vea desde donde se vea;
  - la reserva guarda la zona del lugar del servicio;
  - el correo al cliente y el planning dicen 09:00;
  - el iCal lo pasa a UTC: 14:00Z en Cancún (UTC−5) y 07:00Z en Madrid (verano, UTC+2).
"""
import json

from helpers import ServerTestCase, Client
from stripe_mock import StripeMock

FAR = '2099-12-31'
DAY = '2031-07-15'


class Cobros(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = dict(cls.extra_env, STRIPE_SECRET_KEY='sk_test_mock', WOD_STRIPE_API_BASE=cls.stripe.base, WOD_WIDGET_MAX_PER_HOUR='60', WOD_TRUSTED_PROXIES='127.0.0.1')
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'cobroscz', phone='+34 600 560 101')
        cls.cid = cls.center.user['center_id']; cls.acct = f'acct_cz{cls.cid}'
        cls.server.sql(f"UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id=?,stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.acct, cls.cid))
        cls.sid = cls.center.post('/api/provider-services', {'title': 'Doble inmersión', 'price': 80, 'booking_mode': 'payment', 'max_participants': 6}).json['id']
        cls.slot = cls.center.post('/api/provider-services/slot', {'service_id': cls.sid, 'slot_date': DAY, 'slot_time': '09:00', 'spots_total': 10}).json['slot_id']
        cls.slug = cls.center.get('/api/provider/vender').json['slug']
        cls.center.post('/api/provider/vender', {'domains': 'buceocz.example.com'})
        cls.key = cls.center.post('/api/provider/api-keys', {'action': 'create', 'name': 'Web', 'scope': 'write'}).json['key']
        cls.n = 0

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def free(self):
        return self.server.sql('SELECT spots_available FROM service_slots WHERE id=?', (self.slot,))[0]['spots_available']

    def bk(self, bid):
        return self.server.sql('SELECT status, payment_status, amount_paid, refunded_total, channel, slot_reserved FROM bookings WHERE id=?', (bid,))[0]

    def pay_and_return(self, bid):
        """Pay the last Checkout and come back to the booking page, as the customer does."""
        sess = self.stripe.last_session()
        call = [c for c in self.stripe.calls if c['path'] == '/v1/checkout/sessions' and c['method'] == 'POST'][-1]
        self.assertEqual(call['account'], self.acct)                     # direct charge on the centre's own account
        self.assertNotIn('application_fee_amount', json.dumps(call['params']))
        self.stripe.pay(sess['id'])
        tok = self.server.sql('SELECT public_token FROM bookings WHERE id=?', (bid,))[0]['public_token']
        self.assertEqual(Client(self.server, origin=None).get(f'/w/pago/{bid}.{tok}?r=ok').status, 200)
        return tok

    def widget(self, pax=2):
        type(self).n += 1
        r = Client(self.server).post(f'/api/w/{self.slug}/reservar', {'service_id': self.sid, 'slot_id': self.slot, 'participants': pax, 'fullname': f'Cliente CZ {self.n}',
                                                                        'email': f'cz{self.n}@example.org', 'accept_policy': True, 'canal': 'widget',
                                                                        'host_url': 'https://www.buceocz.example.com/'},
                                     headers={'Idempotency-Key': f'cz-widget-{self.n:04d}', 'X-Forwarded-For': f'203.0.113.{self.n}'})
        self.assertEqual(r.status, 200, r)
        return r.json['id']

    def api(self, method, path, body=None, key=None):
        h = {'Authorization': f'Bearer {key or self.key}'}
        c = Client(self.server, origin=None)
        return c.request(method, path, data=body, headers=h) if method == 'POST' else c.get(path, headers=h)

    def test_widget_cobro_y_devolucion_desde_el_panel(self):
        before = self.free()
        bid = self.widget(2)
        self.pay_and_return(bid)
        b = self.bk(bid)
        self.assertEqual((b['status'], b['payment_status'], b['amount_paid'], b['channel']), ('confirmed', 'paid', 160.0, 'widget'))
        self.assertEqual(self.free(), before - 2)
        n = len(self.stripe.refunds)
        r = self.center.post(f'/api/bookings/{bid}/status', {'status': 'cancelled', 'reason': 'Mar de fondo'})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(len(self.stripe.refunds), n + 1)
        ref = self.stripe.refunds[-1]
        self.assertEqual((ref['account'], ref['amount']), (self.acct, 16000))   # back to the same card, from the centre's account
        b = self.bk(bid)
        self.assertEqual((b['status'], b['refunded_total'], b['slot_reserved']), ('cancelled', 160.0, 0))
        self.assertEqual(self.free(), before)
        # Free again in every channel at once
        av = self.api('GET', f'/api/v1/availability?service_id={self.sid}&from={DAY}&to={DAY}').json['departures'][0]
        self.assertEqual(av['spots_free'], before)
        self.assertEqual(next(s for s in Client(self.server).get(f'/api/w/{self.slug}/fechas?servicio={self.sid}&mes=2031-07').json['slots'] if s['id'] == self.slot)['free'], before)

    def test_api_cobro_y_devolucion_por_la_api(self):
        before = self.free()
        r = self.api('POST', '/api/v1/bookings', {'service_id': self.sid, 'departure_id': self.slot, 'participants': 1,
                                                  'customer': {'name': 'Cliente API CZ', 'email': 'api.cz@example.org'}})
        self.assertEqual(r.status, 201, r)
        self.assertTrue(r.json['checkout_url'].startswith('https://'))
        bid = r.json['booking']['id'] if 'booking' in r.json else r.json['id']
        self.pay_and_return(bid)
        self.assertEqual(self.bk(bid)[('payment_status')], 'paid')
        self.assertEqual(self.bk(bid)['channel'], 'api')
        n = len(self.stripe.refunds)
        r = self.api('POST', f'/api/v1/bookings/{bid}/cancel', {'reason': 'El cliente no puede venir'})
        self.assertEqual(r.status, 200, r)
        ref = self.stripe.refunds[-1]
        self.assertEqual((len(self.stripe.refunds), ref['account'], ref['amount']), (n + 1, self.acct, 8000))
        self.assertEqual(self.bk(bid)['status'], 'cancelled'); self.assertEqual(self.free(), before)

    def test_el_cliente_cancela_con_su_enlace(self):
        before = self.free()
        bid = self.widget(1)
        tok = self.pay_and_return(bid)
        n = len(self.stripe.refunds)
        r = Client(self.server).post(f'/api/mi-reserva/{bid}.{tok}/cancelar', {})
        self.assertEqual(r.status, 200, r)
        # As in every channel since Fase 2.4: the customer's cancellation proposes the refund of the centre's policy
        # (free cancellation in 2031: all of it) and the centre makes it from its own account.
        self.assertEqual((r.json['refund'], r.json['refund_amount']), ('proposed', 80.0))
        self.assertEqual(self.bk(bid)['status'], 'cancelled'); self.assertEqual(self.free(), before)
        self.assertEqual(len(self.stripe.refunds), n)
        r = self.center.post(f'/api/bookings/{bid}/refund', {'amount': 80})
        self.assertEqual(r.status, 200, r)
        ref = self.stripe.refunds[-1]
        self.assertEqual((len(self.stripe.refunds), ref['account'], ref['amount']), (n + 1, self.acct, 8000))
        self.assertEqual(self.bk(bid)['refunded_total'], 80.0)


class Zonas(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.es = t.make_center(cls.admin, 'zonaes', phone='+34 600 560 201')
        cls.mx = t.make_center(cls.admin, 'zonamx', phone='+52 998 560 2020')
        for c in (cls.es, cls.mx):
            cls.server.sql(f"UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}' WHERE id=?", (c.user['center_id'],))
        cls.server.sql("UPDATE centers SET country='México',city='Cancún' WHERE id=?", (cls.mx.user['center_id'],))
        cls.ids = {}
        for tag, c in (('es', cls.es), ('mx', cls.mx)):
            sid = c.post('/api/provider-services', {'title': f'Salida {tag}', 'price': 50, 'booking_mode': 'request', 'duration_minutes': 120}).json['id']
            slot = c.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': DAY, 'slot_time': '09:00', 'spots_total': 6}).json['slot_id']
            cls.ids[tag] = (sid, slot, c.get('/api/provider/vender').json['slug'])

    def test_misma_hora_local_en_widget_correo_planning_e_ical(self):
        expect = {'es': ('Europe/Madrid', '070000Z'), 'mx': ('America/Cancun', '140000Z')}
        for tag, c in (('es', self.es), ('mx', self.mx)):
            with self.subTest(centro=tag):
                sid, slot, slug = self.ids[tag]
                tz, utc = expect[tag]
                # Widget: the local time of the place, whatever the time zone of whoever looks
                for accept in ('es-ES', 'ja-JP'):
                    d = Client(self.server).get(f'/api/w/{slug}/fechas?servicio={sid}&mes=2031-07', headers={'Accept-Language': accept}).json
                    self.assertEqual(d['timezone'], tz)
                    self.assertEqual([(s['date'], s['time']) for s in d['slots'] if s['id'] == slot], [(DAY, '09:00')])
                r = Client(self.server).post(f'/api/w/{slug}/reservar', {'service_id': sid, 'slot_id': slot, 'participants': 1, 'fullname': f'Hora {tag}',
                                                                          'email': f'hora.{tag}@example.org', 'accept_policy': True, 'canal': 'link'})
                self.assertEqual(r.status, 200, r)
                bid = r.json['id']
                b = self.server.sql('SELECT timezone, booking_date, booking_time FROM bookings WHERE id=?', (bid,))[0]
                self.assertEqual((b['timezone'], b['booking_date'], b['booking_time']), (tz, DAY, '09:00'))
                mail = self.server.sql('SELECT text FROM email_outbox WHERE to_email=? ORDER BY id LIMIT 1', (f'hora.{tag}@example.org',))[0]['text']
                self.assertIn('Hora: 09:00', mail); self.assertIn('15 de julio de 2031', mail)
                center_mail = self.server.sql("SELECT text FROM email_outbox WHERE template='center_new_booking' AND related_id=?", (bid,))
                self.assertTrue(center_mail and all('Hora: 09:00' in m['text'] for m in center_mail))
                pl = c.get('/api/center/planning?month=2031-07').json
                self.assertIn('09:00', json.dumps([s for s in pl['slots'] if s['id'] == slot]))
                r = c.get('/api/provider/ical')
                if not r.json.get('url'): c.post('/api/provider/ical/regenerate', {}); r = c.get('/api/provider/ical')
                feed = Client(self.server, origin=None).get('/' + r.json['url'].split('/', 3)[3]).body.decode()
                self.assertIn(f'DTSTART:20310715T{utc}', feed)
                self.assertIn(f'X-WR-TIMEZONE:{tz}', feed)
