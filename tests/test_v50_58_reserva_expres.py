"""v50.58 · Reserva exprés desde la web del centro (encargo unificado del 16/10/2026, bloque 2): el servidor.

Comprueba:
  - la franja del centro (portada, valoración, WhatsApp, cómo llegar) y lo que necesita la pantalla «¿Qué y cuándo?»
    (política propia de cada servicio, confirmación al momento o plazo de respuesta, titulación, extras);
  - la tira de 14 días con las horas y las plazas, y las horas o días más cercanos con plazas cuando no quedan;
  - el pago de Stripe dentro de la reserva (Embedded Checkout): sin success_url ni cancel_url, cobro directo en la cuenta
    del centro, comprobado con Stripe al terminar (nunca se fía del navegador), y la página de Stripe de siempre cuando
    el servidor no tiene la clave pública o es de otro modo (test/live);
  - el pago que se empezó dentro de la reserva sigue en la página de la reserva (nunca un segundo cobro);
  - el QR (solo cuando el centro cuenta con la persona), el archivo de calendario y los datos de los acompañantes (que
    pasan a la lista del barco), con sus límites;
  - la titulación solo cuando el servicio la pide; los enlaces con todo elegido; las cabeceras (Stripe solo en las
    páginas de reserva y solo con la clave); y que los datos de los acompañantes se borran con la cuenta.
"""
import re
import sys
import unittest
from datetime import datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

from helpers import ServerTestCase, Client
from stripe_mock import StripeMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from wod import reserva_expres as wrx  # noqa: E402

FAR = '2099-12-31'
day = lambda n: (datetime.now(ZoneInfo('Europe/Madrid')).date() + timedelta(days=n)).isoformat()   # the centre's «today» (Xàbia)


class Puras(unittest.TestCase):
    def test_tira_de_dias(self):
        strip = wrx.day_strip('2031-05-01', [{'id': 1, 'date': '2031-05-03', 'time': '09:00', 'free': 3}, {'id': 2, 'date': '2031-05-03', 'time': '07:30', 'free': 0},
                                             {'id': 3, 'date': '2031-05-20', 'time': '09:00', 'free': 5}])
        self.assertEqual(len(strip), 14)
        self.assertEqual(strip[0]['date'], '2031-05-01'); self.assertEqual(strip[-1]['date'], '2031-05-14')
        d3 = strip[2]
        self.assertEqual([x['time'] for x in d3['slots']], ['07:30', '09:00']); self.assertTrue(d3['free'])
        self.assertFalse(strip[0]['free']); self.assertEqual(strip[0]['slots'], [])

    def test_alternativas(self):
        slots = [{'id': 1, 'date': '2031-05-03', 'time': '09:00', 'free': 0}, {'id': 2, 'date': '2031-05-03', 'time': '15:00', 'free': 4},
                 {'id': 3, 'date': '2031-05-03', 'time': '11:00', 'free': 1}, {'id': 4, 'date': '2031-05-02', 'time': '09:00', 'free': 6},
                 {'id': 5, 'date': '2031-05-06', 'time': '09:00', 'free': 8}]
        alt = wrx.alternatives(slots, '2031-05-03', '09:00', 2, exclude=1)
        self.assertEqual([a['id'] for a in alt], [2, 4, 5])          # same day first (11:00 has 1 spot: not enough for 2)
        self.assertTrue(alt[0]['same_day']); self.assertFalse(alt[1]['same_day'])
        self.assertEqual(wrx.alternatives(slots, 'no-es-fecha', '', 1), [])

    def test_enlaces_y_calendario(self):
        self.assertEqual(wrx.whatsapp_link('+34 600 111 222', 'Hola'), 'https://wa.me/34600111222?text=Hola')
        self.assertEqual(wrx.whatsapp_link('600 111 222'), '')        # no international prefix: nothing (never guessed)
        self.assertEqual(wrx.whatsapp_link(None), '')
        self.assertIn('destination=38.791000,0.170000', wrx.maps_link(38.791, 0.17))
        self.assertIn('destination=Calle%20Mar%201', wrx.maps_link(None, None, 'Calle Mar 1'))
        self.assertEqual(wrx.maps_link(None, None, ''), '')
        ics = wrx.booking_ics('wod-1@x', 'Doble inmersión · Centro; Ñ, largo ' + 'x' * 80, '2031-05-03T07:00:00Z', '2031-05-03T11:00:00Z', 'Puerto, 1', 'línea 1\nlínea 2',
                              '2031-05-01T10:00:00Z')
        text = ics.decode()
        self.assertTrue(text.startswith('BEGIN:VCALENDAR\r\n')); self.assertIn('DTSTART:20310503T070000Z\r\n', text)
        self.assertIn('LOCATION:Puerto\\, 1', text); self.assertIn('DESCRIPTION:línea 1\\nlínea 2', text)
        self.assertTrue(all(len(line.encode()) <= 75 for line in text.split('\r\n')))   # RFC 5545 folding
        self.assertEqual(wrx.phone_prefix('fr'), '+33'); self.assertEqual(wrx.phone_prefix('xx', 'México'), '+52'); self.assertEqual(wrx.phone_prefix('', ''), '+34')

    def test_acompanantes_limpios(self):
        out = wrx.clean_companions([{'name': '  Ana   Ruiz ', 'level': 'ow', 'size': 'm', 'shoe': '41'}, {'name': 'Leo', 'level': 'jefe', 'shoe': '99'}, {'name': 'Sobra'}], 3)
        # 3 people: seats 2 and 3 only; an unknown level or an impossible shoe size is left empty
        self.assertEqual(out, [{'seat': 2, 'name': 'Ana Ruiz', 'level': 'ow', 'size': 'M', 'shoe': '41'}, {'seat': 3, 'name': 'Leo', 'level': None, 'size': None, 'shoe': None}])
        self.assertEqual([p['seat'] for p in wrx.clean_companions([{'name': ''}, {'name': 'B'}], 3)], [3])   # an empty one keeps its seat
        self.assertEqual(len(wrx.clean_companions([{'name': 'A'}, {'name': 'B'}], 3)), 2)
        with self.assertRaises(ValueError): wrx.clean_companions('no', 3)

    def test_csp_de_stripe(self):
        csp = wrx.with_stripe("default-src 'self'; script-src 'self'; connect-src 'self'; frame-src 'self'; frame-ancestors 'none'")
        self.assertIn("script-src 'self' https://js.stripe.com", csp); self.assertIn('frame-src', csp); self.assertIn('https://hooks.stripe.com', csp)
        self.assertIn("frame-ancestors 'none'", csp); self.assertNotIn('default-src https', csp)


class Expres(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = dict(cls.extra_env, STRIPE_SECRET_KEY='sk_test_mock', STRIPE_PUBLISHABLE_KEY='pk_test_publicamock01', WOD_STRIPE_API_BASE=cls.stripe.base,
                             WOD_WIDGET_MAX_PER_HOUR='200', WOD_TRUSTED_PROXIES='127.0.0.1')
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'rexp', phone='+34 600 111 222')
        cls.cid = cls.center.user['center_id']
        cls.server.sql(f"UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_rexp',stripe_charges_enabled=1,"
                       "stripe_payouts_enabled=1,latitude=38.791,longitude=0.17,address='Puerto 1',cover_url='https://img.example.org/portada.jpg' WHERE id=?", (cls.cid,))
        c = cls.center
        assert c.post('/api/center/extras/save', {'name': 'Linterna', 'price': 5}).status == 200
        cls.extra = cls.server.sql('SELECT id FROM center_extras WHERE center_id=?', (cls.cid,))[0]['id']
        cls.req = c.post('/api/provider-services', {'title': 'Bautizo', 'price': 75, 'booking_mode': 'request', 'max_participants': 4, 'response_hours': 12}).json['id']
        cls.pay = c.post('/api/provider-services', {'title': 'Doble inmersión', 'price': 50, 'booking_mode': 'payment', 'max_participants': 8, 'duration_minutes': 240}).json['id']
        cls.server.sql("UPDATE provider_services SET level_required='Open Water', meeting_point='Puerto deportivo, pantalán 3', cancel_free_hours=24, cancel_refund_pct=50 WHERE id=?", (cls.pay,))
        cls.slots = {}
        for n, t_, sp in ((2, '09:00', 8), (2, '15:00', 2), (3, '09:00', 8), (20, '09:00', 8)):
            cls.slots[(n, t_)] = c.post('/api/provider-services/slot', {'service_id': cls.pay, 'slot_date': day(n), 'slot_time': t_, 'spots_total': sp}).json['slot_id']
        cls.req_slot = c.post('/api/provider-services/slot', {'service_id': cls.req, 'slot_date': day(4), 'slot_time': '10:00', 'spots_total': 6}).json['slot_id']
        cls.slug = c.get('/api/provider/vender').json['slug']
        assert c.post('/api/provider/vender', {'domains': 'buceorexp.com', 'color': '#0b7a75'}).status == 200
        cls.n = 0

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def book(self, **kw):
        type(self).n += 1
        body = {'service_id': self.req, 'slot_id': self.req_slot, 'participants': 1, 'fullname': f'Cliente {self.n}', 'email': f'rexp{self.n}@example.org',
                'phone': '+34 611 222 333', 'accept_policy': True, 'canal': 'widget', 'host_url': 'https://buceorexp.com/', 'lang': 'es', 'reserva_expres': True}
        body.update(kw)
        return Client(self.server).post(f'/api/w/{self.slug}/reservar', body, headers={'Idempotency-Key': f'rexp-{self.n:06d}', 'X-Forwarded-For': f'203.0.113.{self.n % 250}'})

    def test_catalogo_franja_y_servicios(self):
        cat = Client(self.server).get(f'/api/w/{self.slug}?lang=fr&canal=widget').json
        p = cat['provider']
        self.assertEqual(p['cover'], 'https://img.example.org/portada.jpg')
        self.assertIsNone(p['rating'])                                     # no reviews: no stars (never made up)
        self.assertEqual(p['whatsapp'], 'https://wa.me/34600111222')
        self.assertIn('destination=38.791000,0.170000', p['maps'])
        self.assertEqual(p['phone_prefix'], '+33')                         # the language of the page
        self.assertEqual(cat['stripe'], {'key': 'pk_test_publicamock01', 'account': 'acct_rexp'})
        svc = {s['id']: s for s in cat['services']}
        pay, req = svc[self.pay], svc[self.req]
        self.assertEqual((pay['level'], pay['meeting_point'], pay['free_hours'], pay['refund_pct'], pay['instant']), ('Open Water', 'Puerto deportivo, pantalán 3', 24, 50, True))
        self.assertIn('24', pay['policy'])
        self.assertEqual((req['level'], req['instant'], req['response_hours']), ('', False, 12))
        self.assertEqual([x['name'] for x in pay['extras']], ['Linterna'])
        # A service that offers only some extras: only those
        self.server.sql("UPDATE provider_services SET extra_ids='[]' WHERE id=?", (self.req,))
        req2 = [s for s in Client(self.server).get(f'/api/w/{self.slug}').json['services'] if s['id'] == self.req][0]
        self.assertEqual(req2['extras'], [])
        # A centre with reviews shows its average and how many
        uid = self.admin.user['id'] if hasattr(self.admin, 'user') and self.admin.user else 1
        self.server.sql("INSERT INTO center_reviews(center_id,user_id,rating,title,body,active,verified,created_at,updated_at) VALUES(?,?,5,'t','b',1,1,'2031-01-01','2031-01-01')", (self.cid, uid))
        self.server.sql("INSERT INTO center_reviews(center_id,user_id,rating,title,body,active,verified,created_at,updated_at) VALUES(?,?,4,'t','b',1,1,'2031-01-01','2031-01-01')", (self.cid, uid + 1))
        self.assertEqual(Client(self.server).get(f'/api/w/{self.slug}').json['provider']['rating'], {'avg': 4.5, 'count': 2})
        self.server.sql('DELETE FROM center_reviews WHERE center_id=?', (self.cid,))

    def test_tira_y_alternativas(self):
        anon = Client(self.server)
        r = anon.get(f'/api/w/{self.slug}/dias?servicio={self.pay}').json
        self.assertEqual((r['unit'], len(r['days']), r['from'], r['days'][0]['date']), ('slot', 14, r['today'], r['today']))
        d2 = [d for d in r['days'] if d['date'] == day(2)][0]
        self.assertEqual([(x['time'], x['free']) for x in d2['slots']], [('09:00', 8), ('15:00', 2)]); self.assertTrue(d2['free'])
        self.assertEqual(r['next'], day(20))                                # «Más fechas»: the first day with spots after the strip
        later = anon.get(f'/api/w/{self.slug}/dias?servicio={self.pay}&desde={day(15)}').json
        self.assertEqual(later['from'], day(15)); self.assertTrue([d for d in later['days'] if d['date'] == day(20)][0]['free'])
        self.assertEqual(anon.get(f'/api/w/{self.slug}/dias?servicio=999999').status, 404)
        # 4 people at 15:00 (2 spots): the nearest times with 4 free spots, the same day first
        alt = anon.get(f'/api/w/{self.slug}/alternativas?servicio={self.pay}&salida={self.slots[(2, "15:00")]}&personas=4').json['alternatives']
        self.assertEqual([(a['date'], a['time']) for a in alt][:2], [(day(2), '09:00'), (day(3), '09:00')])
        self.assertTrue(alt[0]['same_day'])
        # Booking it anyway: «sin plazas» (400 in the widget, 409 in the API) with the alternatives in the answer
        r = self.book(service_id=self.pay, slot_id=self.slots[(2, '15:00')], participants=4, level='ow')
        self.assertEqual(r.status, 400, r); self.assertEqual(r.json.get('code'), 'no_spots')
        self.assertEqual(r.json['alternatives'][0]['id'], self.slots[(2, '09:00')])

    def test_pago_integrado(self):
        r = self.book(service_id=self.pay, slot_id=self.slots[(3, '09:00')], participants=2, level='aow', pago_integrado=True)
        self.assertEqual(r.status, 200, r)
        body = r.json
        self.assertTrue(body['client_secret'].endswith('_secret_mock')); self.assertIsNone(body['checkout_url'])
        self.assertEqual(body['stripe'], {'key': 'pk_test_publicamock01', 'account': 'acct_rexp'})
        self.assertTrue(0 < body['hold_seconds'] <= 10 * 60 + 5, body['hold_seconds'])
        call = [c for c in self.stripe.calls if c['path'] == '/v1/checkout/sessions' and c['method'] == 'POST'][-1]
        p = call['params']
        self.assertEqual((p.get('ui_mode'), p.get('redirect_on_completion'), call['account']), ('embedded', 'never', 'acct_rexp'))
        self.assertNotIn('success_url', p); self.assertNotIn('cancel_url', p)
        self.assertEqual(p['customer_email'], f'rexp{self.n}@example.org')   # Stripe does not ask for it again
        order = self.server.sql('SELECT ui_mode, client_secret, checkout_url, status FROM payment_orders WHERE booking_id=?', (body['id'],))[0]
        self.assertEqual((order['ui_mode'], order['checkout_url'], order['status']), ('embedded', None, 'pending'))
        # The level of who booked is kept with the booking (seat 1)
        self.assertEqual(self.server.sql('SELECT seat, level FROM booking_people WHERE booking_id=?', (body['id'],))[0]['level'], 'aow')
        anon = Client(self.server); tok = body['token']
        # The browser says «paid» before Stripe does: nothing changes
        v = anon.post(f'/api/mi-reserva/{tok}/comprobar-pago', {}).json['booking']
        self.assertEqual(v['status'], 'payment_in_progress')
        # Asking for a page for the same booking: the page of the booking (the same form), never a second payment
        r2 = anon.post(f'/api/mi-reserva/{tok}/pagar', {})
        self.assertEqual(r2.status, 200, r2); self.assertTrue(r2.json['checkout_url'].endswith(f'/mi-reserva/{tok}?pagar=1'))
        r3 = anon.post(f'/api/mi-reserva/{tok}/pagar', {'pago_integrado': True}).json
        self.assertEqual(r3['client_secret'], body['client_secret'])
        self.assertEqual(self.server.sql('SELECT COUNT(*) AS n FROM payment_orders WHERE booking_id=?', (body['id'],))[0]['n'], 1)
        # Stripe says paid: confirmed, and the QR exists
        self.stripe.pay(self.stripe.session_by_secret(body['client_secret'])['id'])
        v = anon.post(f'/api/mi-reserva/{tok}/comprobar-pago', {}).json['booking']
        self.assertEqual((v['status'], v['has_qr']), ('confirmed', True))
        qr = anon.get(f'/api/mi-reserva/{tok}/qr.svg')
        self.assertEqual(qr.status, 200); self.assertIn(b'<svg', qr.body)

    def test_sin_clave_publica_la_pagina_de_siempre(self):
        # «pago_integrado» from a service without online payments ready: nothing embedded is promised
        self.server.sql("UPDATE centers SET stripe_charges_enabled=0 WHERE id=?", (self.cid,))
        try:
            cat = Client(self.server).get(f'/api/w/{self.slug}').json
            self.assertIsNone(cat['stripe'])
        finally:
            self.server.sql("UPDATE centers SET stripe_charges_enabled=1 WHERE id=?", (self.cid,))

    def test_titulacion_solo_si_el_servicio_la_pide(self):
        r = self.book(service_id=self.pay, slot_id=self.slots[(2, '09:00')], participants=1)
        self.assertEqual(r.status, 400, r); self.assertIn('titulación', r.json['error'])
        r = self.book(service_id=self.pay, slot_id=self.slots[(2, '09:00')], participants=1, level='nivel-inventado')
        self.assertEqual(r.status, 400, r)
        r = self.book()                                                    # the request service asks for none
        self.assertEqual(r.status, 200, r)
        # The old widget (without reserva_expres) keeps booking as before
        r = self.book(service_id=self.pay, slot_id=self.slots[(2, '09:00')], participants=1, reserva_expres=False)
        self.assertEqual(r.status, 200, r)

    def test_calendario_qr_y_acompanantes(self):
        r = self.book(participants=3)
        self.assertEqual(r.status, 200, r)
        tok, bid = r.json['token'], r.json['id']
        anon = Client(self.server)
        self.assertEqual(anon.get(f'/api/mi-reserva/{tok}/qr.svg').status, 404)   # a request: the centre has not said yes
        ics = anon.get(f'/mi-reserva/{tok}.ics')
        self.assertEqual(ics.status, 200); self.assertTrue(ics.headers['Content-Type'].startswith('text/calendar'))
        text = ics.body.decode()
        self.assertRegex(text, r'DTSTART:\d{8}T\d{6}Z'); self.assertIn('SUMMARY:Bautizo', text); self.assertIn('BEGIN:VEVENT', text)
        self.assertEqual(anon.get(f'/mi-reserva/{tok[:-2]}xx.ics').status, 404)       # never without its token
        # The companions: seats 2 and 3, into the boat list
        out = anon.post(f'/api/mi-reserva/{tok}/acompanantes', {'people': [{'name': 'Ana Ruiz', 'level': 'ow', 'size': 'M', 'shoe': '40'},
                                                                              {'name': 'Leo Gil', 'level': 'none'}, {'name': 'De más'}]})
        self.assertEqual(out.status, 200, out)
        self.assertEqual([(p['seat'], p['name']) for p in out.json['people'] if p['seat'] > 1], [(2, 'Ana Ruiz'), (3, 'Leo Gil')])
        names = {r_['seat']: r_['name'] for r_ in self.server.sql('SELECT seat, name FROM manifest_entries WHERE booking_id=?', (bid,))}
        self.assertEqual((names.get(2), names.get(3)), ('Ana Ruiz', 'Leo Gil'))
        got = anon.get(f'/api/mi-reserva/{tok}/acompanantes').json
        self.assertEqual(got['participants'], 3)
        view = anon.get(f'/api/mi-reserva/{tok}').json['booking']
        self.assertTrue(view['can_people']); self.assertEqual(len([p for p in view['people'] if p['seat'] > 1]), 2)
        # Changing them: a removed companion leaves the boat list
        anon.post(f'/api/mi-reserva/{tok}/acompanantes', {'people': [{'name': 'Ana Ruiz'}]})
        names = {r_['seat']: r_['name'] for r_ in self.server.sql('SELECT seat, name FROM manifest_entries WHERE booking_id=?', (bid,))}
        self.assertIsNone(names.get(3))
        self.assertEqual(anon.post(f'/api/mi-reserva/{tok}/acompanantes', {'people': 'x'}).status, 400)
        # A cancelled booking: no more changes, no calendar
        self.assertEqual(anon.post(f'/api/mi-reserva/{tok}/cancelar', {}).status, 200)
        self.assertEqual(anon.post(f'/api/mi-reserva/{tok}/acompanantes', {'people': [{'name': 'Otra'}]}).status, 400)
        self.assertEqual(anon.get(f'/mi-reserva/{tok}.ics').status, 404)

    def test_cabeceras_y_enlaces_con_todo_elegido(self):
        anon = Client(self.server)
        r = anon.get(f'/c/{self.slug}?servicio={self.pay}&fecha={day(3)}&hora=09:00&personas=2')
        self.assertEqual(r.status, 200)
        csp, pp = r.headers.get('Content-Security-Policy', ''), r.headers.get('Permissions-Policy', '')
        self.assertIn('https://js.stripe.com', csp); self.assertIn('frame-src', csp); self.assertIn("frame-ancestors 'none'", csp)
        self.assertIn('payment=(self "https://js.stripe.com"', pp)
        boot = re.search(r'<script type="application/json" id="wd-boot">(.*?)</script>', r.body.decode()).group(1)
        self.assertIn('"time": "09:00"', boot); self.assertIn('"people": 2', boot); self.assertIn(f'"date": "{day(3)}"', boot)
        r = anon.get(f'/c/{self.slug}?servicio={self.pay}&hora=25h&personas=999')
        boot = re.search(r'id="wd-boot">(.*?)</script>', r.body.decode()).group(1)
        self.assertIn('"time": null', boot); self.assertIn('"people": null', boot)
        # The rest of the web keeps its policy: no Stripe outside the booking pages
        home = anon.get('/')
        self.assertNotIn('js.stripe.com', home.headers.get('Content-Security-Policy', ''))
        w = anon.get(f'/w/{self.slug}')
        self.assertIn('frame-ancestors https://buceorexp.com', w.headers.get('Content-Security-Policy', ''))
        self.assertIn('https://js.stripe.com', w.headers.get('Content-Security-Policy', ''))

    def test_los_acompanantes_se_borran_con_los_datos(self):
        r = self.book(participants=2)
        tok, bid = r.json['token'], r.json['id']
        Client(self.server).post(f'/api/mi-reserva/{tok}/acompanantes', {'people': [{'name': 'Marta Sanz'}]})
        self.assertTrue(self.server.sql('SELECT 1 FROM booking_people WHERE booking_id=?', (bid,)))
        uid = self.server.sql('SELECT user_id FROM bookings WHERE id=?', (bid,))[0]['user_id']
        src = (ROOT / 'app' / 'server.py').read_text(encoding='utf-8')
        # the three places where personal data of bookings is erased also erase the companions
        self.assertIn("'DELETE FROM booking_people WHERE booking_id IN (SELECT id FROM bookings WHERE user_id=?)'", src)
        self.assertIn("step('people'", src); self.assertIn('DELETE FROM booking_people WHERE booking_id IN (SELECT id FROM bookings WHERE booking_date < ?)', src)
        self.assertTrue(uid)


class ClaveDeOtroModo(ServerTestCase):
    """A live publishable key with a test secret key (or no key): Stripe's page, as before."""
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = dict(cls.extra_env, STRIPE_SECRET_KEY='sk_test_mock', STRIPE_PUBLISHABLE_KEY='pk_live_publicamock01', WOD_STRIPE_API_BASE=cls.stripe.base,
                             WOD_TRUSTED_PROXIES='127.0.0.1')
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin(); cls.center = t.make_center(cls.admin, 'rexpb'); cls.cid = cls.center.user['center_id']
        cls.server.sql(f"UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_rexpb',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.cid,))
        cls.pay = cls.center.post('/api/provider-services', {'title': 'Doble', 'price': 50, 'booking_mode': 'payment'}).json['id']
        cls.slot = cls.center.post('/api/provider-services/slot', {'service_id': cls.pay, 'slot_date': day(5), 'slot_time': '09:00', 'spots_total': 8}).json['slot_id']
        cls.slug = cls.center.get('/api/provider/vender').json['slug']

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def test_pagina_de_stripe(self):
        anon = Client(self.server)
        self.assertIsNone(anon.get(f'/api/w/{self.slug}').json['stripe'])
        r = anon.post(f'/api/w/{self.slug}/reservar', {'service_id': self.pay, 'slot_id': self.slot, 'participants': 1, 'fullname': 'Pepa Ruiz', 'email': 'pepa@example.org',
                                                        'accept_policy': True, 'canal': 'link', 'pago_integrado': True, 'reserva_expres': True})
        self.assertEqual(r.status, 200, r)
        self.assertTrue(r.json['checkout_url'].startswith('https://checkout.stripe.test/')); self.assertNotIn('client_secret', r.json)
        page = anon.get(f'/c/{self.slug}')
        self.assertNotIn('js.stripe.com', page.headers.get('Content-Security-Policy', ''))
        self.assertIn('payment=()', page.headers.get('Permissions-Policy', ''))


if __name__ == '__main__':
    unittest.main()
