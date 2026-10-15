"""v50.55 · Encargo del 15/10/2026: «Pago en persona» para freelance.

The freelance professional chooses how he is paid: «Pago online» (his own Stripe) or «Pago en persona» (the client pays
him directly; WORLDIVES is only the search, the showcase and the agenda). The tests of the brief:
  · no publishing without a price;
  · «Pago en persona» with «Pago al reservar» fails;
  · no request without ticking the box of the notice;
  · the WhatsApp never appears before the acceptance nor in any public answer;
  · the price is the same in the search, the page, the booking, the e-mail and the PDF;
  · the agenda is taken when the professional accepts and freed when the booking is cancelled.
Plus: the professional's private marks, the e-mails, the migration of the old services, experiences, plans and DAC7."""
import datetime as dt
import json
import re
import shutil
import subprocess
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ROOT, Server, ServerTestCase, IN_PERSON  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402

sys.path.insert(0, str(ROOT / 'app'))
from wod import presencial as wpres  # noqa: E402

WA = '+34 611 000 000'
WA_DIGITS = '34611000000'


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


class Rules(unittest.TestCase):
    """The pure rules of wod/presencial.py."""

    def test_methods_policy_and_link(self):
        self.assertEqual(wpres.clean_methods(['bizum', 'cash'], ''), (['cash', 'bizum'], ''))
        self.assertEqual(wpres.clean_methods('transfer, other', ' Tarjeta  en mano '), (['transfer', 'other'], 'Tarjeta en mano'))
        for bad in ([], ['nada'], None):
            with self.assertRaises(ValueError): wpres.clean_methods(bad, '')
        with self.assertRaises(ValueError): wpres.clean_methods(['other'], '')
        with self.assertRaises(ValueError): wpres.clean_methods(['other'], 'x' * 41)
        with self.assertRaises(ValueError): wpres.clean_policy('x' * 1001)
        link = wpres.wa_link('+34 611 000 000', wpres.wa_message('es', 'WOD-000007', 'Bautizo', 'sábado, 1 de noviembre de 2031'))
        self.assertTrue(link.startswith('https://wa.me/34611000000?text='))
        self.assertIn('WOD-000007', link)
        self.assertEqual(wpres.wa_link('600', 'x'), '')
        self.assertEqual(set(wpres.WA_MESSAGE), {'es', 'en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh'})
        self.assertIn('WORLDIVES no gestiona pagos, devoluciones, cancelaciones ni incidencias', wpres.NOTICE)


class InPerson(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.pro = t.make_freelance(cls.admin, 'presencial')
        cls.other = t.make_freelance(cls.admin, 'otrofl')
        cls.online = t.make_freelance(cls.admin, 'conpagos')
        cls.server.sql("UPDATE users SET stripe_account_id='acct_ok',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.online.user['id'],))
        cls.center = t.make_center(cls.admin, 'centropres', phone='+34 600 555 001')
        cls.diver = t.make_diver('ipbuzo')
        cls.diver2 = t.make_diver('ipbuzo2')
        r = cls.pro.post('/api/provider-services', {'title': 'Bautizo en la cala', 'price': 45, 'max_participants': 4, 'booking_mode': 'request',
                                                    'pay_way': 'in_person', 'pay_methods': ['cash', 'bizum', 'other'], 'pay_other': 'Tarjeta en mano',
                                                    'pay_whatsapp': WA, 'pay_policy': 'Gratis hasta 24 horas antes. Después, la mitad.', 'accept_in_person_terms': True})
        assert r.status == 200, r
        cls.sid = r.json['id']

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def slot(self, n=20, spots=4, sid=None):
        r = self.pro.post('/api/provider-services/slot', {'service_id': sid or self.sid, 'slot_date': day(n), 'slot_time': '10:00', 'spots_total': spots})
        self.assertEqual(r.status, 200, r); return r.json['slot_id']

    def book(self, diver, slot, pax=2, ack=True, sid=None):
        return diver.post('/api/bookings', {'service_id': sid or self.sid, 'slot_id': slot, 'participants': pax, **({'in_person_ack': True} if ack else {})})

    def spots(self, slot):
        return self.server.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot,))[0]['spots_available']

    # ------------------------------------------------------------------ 1. Configuración
    def test_online_only_with_stripe(self):
        r = self.other.post('/api/provider-services', {'title': 'Online sin Stripe', 'price': 30, 'booking_mode': 'request', 'pay_way': 'online'})
        self.assertEqual(r.status, 400, r); self.assertIn('Cobros y pagos', r.json['error'])
        r = self.other.post('/api/provider-services', {'title': 'Sin forma de cobro', 'price': 30, 'booking_mode': 'request'})
        self.assertEqual(r.status, 400, r); self.assertIn('forma de cobro', r.json['error'])
        r = self.online.post('/api/provider-services', {'title': 'Online con Stripe', 'price': 30, 'booking_mode': 'payment', 'pay_way': 'online'})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.server.sql('SELECT pay_way FROM provider_services WHERE id=?', (r.json['id'],))[0]['pay_way'], 'online')

    def test_in_person_with_pay_when_booking_fails(self):
        for mode in ('payment', 'instant'):
            r = self.online.post('/api/provider-services', {'title': 'Mezcla imposible', 'price': 30, 'booking_mode': mode, **IN_PERSON})
            self.assertEqual(r.status, 400, (mode, r)); self.assertIn('Bajo petición', r.json['error'])
        r = self.pro.post('/api/provider-services/update', {'id': self.sid, 'title': 'Bautizo en la cala', 'booking_mode': 'payment'})
        self.assertEqual(r.status, 400, r)
        self.assertEqual(self.server.sql('SELECT booking_mode,pay_way FROM provider_services WHERE id=?', (self.sid,))[0]['pay_way'], 'in_person')

    def test_in_person_needs_methods_whatsapp_and_terms(self):
        base = {'title': 'Prueba de campos', 'price': 30, 'booking_mode': 'request', 'pay_way': 'in_person'}
        f = self.make_freelance(self.admin, 'campos')
        r = f.post('/api/provider-services', {**base, 'pay_whatsapp': WA, 'accept_in_person_terms': True})
        self.assertEqual(r.status, 400, r); self.assertIn('forma de pago', r.json['error'])
        r = f.post('/api/provider-services', {**base, 'pay_methods': ['other'], 'pay_whatsapp': WA, 'accept_in_person_terms': True})
        self.assertEqual(r.status, 400, r)
        for phone in ('', '611 000 000', 'llámame'):
            r = f.post('/api/provider-services', {**base, 'pay_methods': ['cash'], 'pay_whatsapp': phone, 'accept_in_person_terms': True})
            self.assertEqual(r.status, 400, (phone, r)); self.assertIn('prefijo', r.json['error'])
        r = f.post('/api/provider-services', {**base, 'pay_methods': ['cash'], 'pay_whatsapp': WA})
        self.assertEqual((r.status, r.json.get('terms_required')), (400, 'pago-en-persona'), r)
        self.assertFalse(self.server.sql("SELECT 1 FROM legal_acceptances WHERE user_id=? AND document='pago-en-persona'", (f.user['id'],)))
        r = f.post('/api/provider-services', {**base, 'pay_methods': ['cash'], 'pay_whatsapp': '0034 611 000 000', 'accept_in_person_terms': True})
        self.assertEqual(r.status, 200, r)
        self.assertTrue(self.server.sql("SELECT 1 FROM legal_acceptances WHERE user_id=? AND document='pago-en-persona'", (f.user['id'],)))
        # accepted once: the next service does not ask again
        self.assertEqual(f.post('/api/provider-services', {**base, 'title': 'Segundo', 'pay_methods': ['cash'], 'pay_whatsapp': WA}).status, 200)
        # without the plan feature (the owner decides in which plan it goes)
        self.server.sql("UPDATE users SET plan_code='free',plan_expires_at=NULL WHERE id=?", (f.user['id'],))
        r = f.post('/api/provider-services', {**base, 'title': 'Sin plan', 'pay_methods': ['cash'], 'pay_whatsapp': WA})
        self.assertEqual((r.status, r.json.get('plan_required')), (403, 'in_person_payments'), r)

    def test_whatsapp_stored_encrypted_and_apart(self):
        row = self.server.sql("SELECT substr(phone,1,5)='wdx1:' AS enc,instr(phone,'611')>0 AS clear,phone_hash FROM pay_contacts WHERE kind='service' AND ref_id=?", (self.sid,))[0]
        self.assertEqual((row['enc'], row['clear']), (1, 0)); self.assertTrue(row['phone_hash'])
        self.assertNotIn(WA_DIGITS, json.dumps(self.server.sql('SELECT * FROM provider_services WHERE id=?', (self.sid,))))
        # the owner sees it in his own list (to edit it); nobody else does
        mine = [x for x in self.pro.get(f"/api/provider-services?provider_id={self.pro.user['id']}&include_inactive=1").json['items'] if x['id'] == self.sid][0]
        self.assertEqual(mine['pay_whatsapp'], '+34611000000')

    def test_no_whatsapp_no_requests(self):
        # A service the 50.55 migration moved to «Pago en persona» when the profile phone had no country code: the
        # client could not reach the professional once accepted, so it takes no requests until he adds his WhatsApp.
        pid = self.pro.user['id']
        sid = self.pro.post('/api/provider-services', {'title': 'Migrado sin WhatsApp', 'price': 30, 'booking_mode': 'request', **IN_PERSON}).json['id']
        slot = self.slot(28, sid=sid)
        self.server.sql("DELETE FROM pay_contacts WHERE kind='service' AND ref_id=?", (sid,))
        card = lambda: [x for x in self.client().get(f'/api/provider-services?provider_id={pid}').json['items'] if x['id'] == sid][0]
        self.assertFalse(card()['bookable']); self.assertIn('no admite reservas', card()['unavailable_reason'])
        r = self.book(self.diver2, slot, pax=1, sid=sid)
        self.assertEqual(r.status, 400, r); self.assertFalse(self.server.sql('SELECT 1 FROM bookings WHERE slot_id=?', (slot,)))
        r = self.pro.post('/api/provider-services/update', {'id': sid, 'title': 'Migrado sin WhatsApp', 'price': 30, 'booking_mode': 'request', **IN_PERSON})
        self.assertEqual(r.status, 200, r)
        self.assertTrue(card()['bookable'])
        self.assertEqual(self.book(self.diver2, slot, pax=1, sid=sid).status, 200)

    # ------------------------------------------------------------------ 2. Precio obligatorio
    def test_no_publishing_without_price(self):
        for who in (self.pro, self.center):
            for price in (0, '', None, '0,00'):
                data = {'title': 'Sin precio', 'price': price, 'booking_mode': 'request', **(IN_PERSON if who is self.pro else {})}
                r = who.post('/api/provider-services', data)
                self.assertEqual(r.status, 400, (price, r)); self.assertIn('precio', r.json['error'])
        r = self.pro.post('/api/provider-services', {'title': 'Días sin precio', 'booking_mode': 'request', 'booking_unit': 'day', 'pricing': {'day': 0}, **IN_PERSON})
        self.assertEqual(r.status, 400, r)
        r = self.pro.post('/api/provider-services/update', {'id': self.sid, 'title': 'Bautizo en la cala', 'price': 0})
        self.assertEqual(r.status, 400, r)
        sid = self.center.post('/api/provider-services', {'title': 'Con precio', 'price': 20, 'booking_mode': 'request'}).json['id']
        self.assertEqual(self.center.post('/api/center/tariffs/save', {'service_id': sid, 'price': 0}).status, 400)
        r = self.center.post('/api/travel-experiences', {'new_destination': 'Medes', 'title': 'Viaje sin precio', 'spots_total': 4})
        self.assertEqual(r.status, 400, r); self.assertIn('precio', r.json['error'])
        # a service left at 0 € before this version stays in the panel but is not bookable
        self.server.sql('UPDATE provider_services SET price=0 WHERE id=?', (sid,)); self.server.sql('UPDATE center_tariffs SET price=0 WHERE service_id=?', (sid,))
        pub = [x for x in self.client().get(f"/api/provider-services?provider_id=0&center_id={self.center.user['center_id']}").json['items'] if x['id'] == sid][0]
        self.assertFalse(pub['bookable']); self.assertIn('precio', pub['unavailable_reason'])

    def test_freelance_changes_his_price(self):
        sid = self.pro.post('/api/provider-services', {'title': 'Cambio de precio', 'price': 30, 'booking_mode': 'request', **IN_PERSON}).json['id']
        self.assertEqual(self.pro.post('/api/provider-services/update', {'id': sid, 'title': 'Cambio de precio', 'price': 35}).status, 200)
        self.assertEqual(self.client().get(f'/api/provider-services/{sid}').json['service']['price'], 35)

    def test_price_identical_everywhere(self):
        slot = self.slot(25)
        pid = self.pro.user['id']
        search = [x for x in self.client().get(f'/api/provider-services?provider_id={pid}').json['items'] if x['id'] == self.sid][0]
        page = self.client().get(f'/api/provider-services/{self.sid}').json['service']
        near = [x for x in self.client().get('/api/salidas-cercanas?limite=50').json.get('items', []) if x['service_id'] == self.sid]
        quote = self.client().get(f'/api/booking-quote?center_id=0&service_id={self.sid}&slot_id={slot}&participants=2').json
        self.assertEqual((search['price'], page['price']), (45, 45))
        for x in near: self.assertEqual(x['price'], 45)
        self.assertEqual(quote['total'], 90)
        bid = self.book(self.diver, slot).json['id']
        b = self.server.sql('SELECT price,price_breakdown,pay_way,in_person_ack_at FROM bookings WHERE id=?', (bid,))[0]
        self.assertEqual(b['price'], 90); self.assertEqual(json.loads(b['price_breakdown'])[0]['unit'], 45)
        self.assertEqual(b['pay_way'], 'in_person'); self.assertTrue(b['in_person_ack_at'])
        self.assertEqual(self.pro.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'}).json['status'], 'confirmed')
        mail = self.server.sql("SELECT text FROM email_outbox WHERE template='booking_confirmed' AND related_id=?", (bid,))[0]['text']
        self.assertIn('Pago en persona al profesional: 90 € (precio publicado).', mail)
        self.assertIn(wpres.NOTICE, mail)
        self.assertIn('Política del profesional: Gratis hasta 24 horas antes. Después, la mitad.', mail)
        self.assertIn('Hablar por WhatsApp: https://wa.me/34611000000?text=', mail)
        raw = self.diver.get(f'/api/bookings/{bid}/receipt.pdf').body
        self.assertTrue(raw.startswith(b'%PDF'))
        if shutil.which('pdftotext'):
            out = Path(self.server.tmp) / f'p{bid}.pdf'; out.write_bytes(raw)
            text = ' '.join(subprocess.run(['pdftotext', str(out), '-'], capture_output=True, text=True).stdout.split()).lower()
            for needle in ('Precio publicado', '90 €', 'Pago en persona al profesional', 'Confirmada · pago en persona', 'Política del profesional',
                           'WORLDIVES no gestiona pagos', 'WhatsApp +34611000000'):
                self.assertIn(needle.lower(), text)

    # ------------------------------------------------------------------ 3. Lo que ve el cliente
    def test_label_on_cards(self):
        pid = self.pro.user['id']
        card = [x for x in self.client().get(f'/api/provider-services?provider_id={pid}').json['items'] if x['id'] == self.sid][0]
        self.assertEqual((card['pay_way'], card['pay_label']), ('in_person', 'Pago en persona al profesional'))
        self.assertEqual(card['pay_methods'], ['cash', 'bizum', 'other']); self.assertEqual(card['pay_other'], 'Tarjeta en mano')
        self.assertEqual(card['pay_notice'], wpres.NOTICE)
        self.assertEqual(self.client().get(f'/api/provider-services/{self.sid}').json['service']['pay_label'], 'Pago en persona al profesional')

    def test_request_needs_the_box(self):
        slot = self.slot(26)
        r = self.book(self.diver, slot, ack=False)
        self.assertEqual(r.status, 400, r); self.assertTrue(r.json.get('in_person_ack_required')); self.assertIn('casilla', r.json['error'])
        self.assertEqual(self.diver.post('/api/bookings', {'service_id': self.sid, 'slot_id': slot, 'participants': 1, 'in_person_ack': False}).status, 400)
        self.assertFalse(self.server.sql('SELECT 1 FROM bookings WHERE slot_id=?', (slot,)))
        r = self.book(self.diver, slot)
        self.assertEqual((r.status, r.json['status'], r.json['pay_way']), (200, 'requested', 'in_person'), r)
        b = self.server.sql('SELECT payment_status,deposit_amount,cancel_free_hours,cancel_refund_pct,booking_mode FROM bookings WHERE id=?', (r.json['id'],))[0]
        self.assertEqual(dict(b), {'payment_status': 'at_center', 'deposit_amount': None, 'cancel_free_hours': None, 'cancel_refund_pct': None, 'booking_mode': 'request'})
        self.assertTrue(self.server.sql("SELECT 1 FROM audit_log WHERE action='in_person_notice_accepted' AND entity_id=?", (r.json['id'],)))

    def test_whatsapp_only_after_acceptance(self):
        slot = self.slot(27)
        d3 = self.make_diver('ipbuzo3')
        bid = self.book(d3, slot).json['id']
        before = json.dumps(d3.get(f'/api/bookings/{bid}').json) + json.dumps(d3.get('/api/me/area').json)
        self.assertNotIn(WA_DIGITS, before.replace(' ', ''))
        self.assertNotIn('pro_whatsapp', before); self.assertNotIn('wa.me', before)
        req_mail = self.server.sql("SELECT text FROM email_outbox WHERE template='booking_request' AND related_id=?", (bid,))[0]['text']
        self.assertNotIn('wa.me', req_mail); self.assertIn('No se cobra nada a través de WORLDIVES', req_mail); self.assertIn(wpres.NOTICE, req_mail)
        self.assertEqual(self.pro.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'}).json['status'], 'confirmed')
        d = d3.get(f'/api/bookings/{bid}').json['booking']
        self.assertEqual(d['cancellation_policy'], 'in_person'); self.assertEqual(d['cancellation_text'], 'Gratis hasta 24 horas antes. Después, la mitad.')
        self.assertEqual(d['status_label'], 'Confirmada · pago en persona')
        self.assertTrue(d['pro_whatsapp'].startswith('https://wa.me/34611000000?text='))
        text = __import__('urllib.parse').parse.unquote(d['pro_whatsapp'].split('text=', 1)[1])
        self.assertIn(f'WOD-{bid:06d}', text); self.assertIn('Bautizo en la cala', text)
        area = [x for x in d3.get('/api/me/area').json['bookings'] if x['id'] == bid][0]
        self.assertEqual(area['pro_whatsapp'], d['pro_whatsapp']); self.assertEqual(area['status_label'], 'Confirmada · pago en persona')
        self.assertEqual(self.diver2.get(f'/api/bookings/{bid}').status, 404)
        # in-person bookings never open an online payment
        self.assertEqual(d3.post('/api/payments/checkout', {'booking_id': bid}).status, 400)

    def test_whatsapp_never_in_public_answers(self):
        pid = self.pro.user['id']
        pub = [self.client().get(u) for u in (f'/api/provider-services?provider_id={pid}', f'/api/provider-services/{self.sid}', f'/api/providers/{pid}',
                                              '/api/salidas-cercanas?limite=50', f'/api/agenda/public?service={self.sid}', '/api/travel-experiences')]
        # a logged-in diver who has not booked does not see it either
        pub.append(self.diver2.get(f'/api/provider-services/{self.sid}'))
        for r in pub:
            body = r.body.decode('utf-8', 'replace')
            self.assertNotIn(WA_DIGITS, body.replace(' ', '')); self.assertNotIn('pay_whatsapp', body); self.assertNotIn('wa.me', body)

    # ------------------------------------------------------------------ 4. Lo que no hace la plataforma / 5. Agenda
    def test_agenda_taken_on_acceptance_and_freed_on_cancel(self):
        slot = self.slot(28, spots=4)
        bid = self.book(self.diver, slot).json['id']
        self.assertEqual(self.spots(slot), 4)                       # a request holds nothing
        self.pro.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})
        self.assertEqual(self.spots(slot), 2)                       # accepted: the agenda is taken
        terms = self.diver.post(f'/api/bookings/{bid}/cancel', {'preview': True}).json['terms']
        self.assertTrue(terms['in_person']); self.assertEqual(terms['refund_amount'], 0); self.assertFalse(terms['paid_online'])
        self.assertEqual(terms['policy_text'], 'Gratis hasta 24 horas antes. Después, la mitad.')
        r = self.diver.post(f'/api/bookings/{bid}/cancel', {})
        self.assertEqual(r.status, 200, r); self.assertEqual(r.json.get('refund'), 'none_paid')
        self.assertEqual(self.spots(slot), 4)                       # cancelled: freed
        self.assertFalse(self.server.sql('SELECT 1 FROM payment_orders WHERE booking_id=?', (bid,)))   # no money moves
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='center_booking_cancelled' AND related_id=?", (bid,)))
        # the professional cancels: the other side is told, no money
        slot2 = self.slot(29, spots=4)
        bid2 = self.book(self.diver, slot2).json['id']
        self.pro.post(f'/api/bookings/{bid2}/status', {'status': 'confirmed'})
        r = self.pro.post(f'/api/bookings/{bid2}/status', {'status': 'cancelled', 'reason': 'Mal tiempo'})
        self.assertEqual((r.status, r.json.get('refund')), (200, 'none_paid'), r)
        self.assertEqual(self.spots(slot2), 4)

    def test_days_agenda_taken_and_freed(self):
        sid = self.pro.post('/api/provider-services', {'title': 'Guía por días', 'price': 150, 'max_participants': 2, 'booking_mode': 'request', 'booking_unit': 'day',
                                                       'unit_rules': {'min_days': 1, 'max_days': 5, 'lead_hours': 24}, 'pricing': {'day': 150}, **IN_PERSON}).json['id']
        self.pro.post('/api/agenda/hours', {'weekdays': [0, 1, 2, 3, 4, 5, 6], 'closures': []})
        d = day(40)
        r = self.diver.post('/api/bookings', {'service_id': sid, 'days': [d], 'part': 'full', 'participants': 1})
        self.assertEqual(r.status, 400, r)
        bid = self.diver.post('/api/bookings', {'service_id': sid, 'days': [d], 'part': 'full', 'participants': 1, 'in_person_ack': True}).json['id']
        cal = lambda: self.client().get(f'/api/agenda/public?service={sid}&month={d[:7]}').json
        self.assertEqual(cal()['days'][d], 'free'); self.assertEqual(cal()['pay_way'], 'in_person')
        self.pro.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})
        self.assertEqual(cal()['days'][d], 'busy')
        self.assertEqual(self.diver.post(f'/api/bookings/{bid}/cancel', {}).status, 200)
        self.assertEqual(cal()['days'][d], 'free')

    def test_private_marks(self):
        slot = self.slot(30)
        bid = self.book(self.diver, slot).json['id']
        self.assertEqual(self.pro.post('/api/pro-mark', {'id': bid, 'mark': 'paid'}).status, 400)          # still a request
        self.pro.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})
        self.assertEqual(self.pro.post('/api/pro-mark', {'id': bid, 'mark': 'cobrado'}).status, 400)
        self.assertEqual(self.other.post('/api/pro-mark', {'id': bid, 'mark': 'paid'}).status, 404)        # not his booking
        self.assertEqual(self.diver.post('/api/pro-mark', {'id': bid, 'mark': 'paid'}).status, 403)
        r = self.pro.post('/api/pro-mark', {'id': bid, 'mark': 'paid'})
        self.assertEqual((r.status, r.json['label']), (200, 'Cobrado'))
        self.assertEqual(self.pro.get(f'/api/bookings/{bid}').json['booking']['pro_mark'], 'paid')
        self.assertNotIn('pro_mark', self.diver.get(f'/api/bookings/{bid}').json['booking'])
        self.assertNotIn('pro_mark', [x for x in self.diver.get('/api/me/area').json['bookings'] if x['id'] == bid][0])
        self.assertEqual(self.pro.post('/api/pro-mark', {'id': bid, 'mark': 'no_show'}).json['label'], 'No se presentó')
        self.assertEqual(self.pro.post('/api/pro-mark', {'id': bid, 'mark': ''}).json['mark'], None)
        self.assertFalse(self.server.sql('SELECT 1 FROM payment_orders WHERE booking_id=?', (bid,)))
        # an online booking is never marked by hand
        osid = self.online.post('/api/provider-services', {'title': 'Online', 'price': 30, 'booking_mode': 'request', 'pay_way': 'online'}).json['id']
        oslot = self.online.post('/api/provider-services/slot', {'service_id': osid, 'slot_date': day(31), 'slot_time': '10:00', 'spots_total': 4}).json['slot_id']
        obid = self.diver.post('/api/bookings', {'service_id': osid, 'slot_id': oslot, 'participants': 1}).json['id']
        self.assertEqual(self.online.post('/api/pro-mark', {'id': obid, 'mark': 'paid'}).status, 400)

    # ------------------------------------------------------------------ experiences
    def test_experiences(self):
        offer = self.admin.post('/api/admin/travel-offers', {'title': 'Cabo de Palos', 'region': 'España', 'kind': 'Viaje'}).json['id']
        r = self.pro.post('/api/travel-experiences', {'travel_offer_id': offer, 'title': 'Fin de semana en Cabo de Palos', 'price': 200, 'spots_total': 6, 'spots_available': 6,
                                                      'pay_way': 'in_person', 'pay_methods': ['transfer'], 'pay_whatsapp': WA})
        self.assertEqual(r.status, 200, r); eid = r.json['id']
        self.admin.post('/api/admin/travel-experiences/status', {'id': eid, 'status': 'published'})
        item = self.client().get(f'/api/travel-experiences/{eid}').json['item']
        self.assertEqual((item['pay_way'], item['pay_label']), ('in_person', 'Pago en persona al profesional'))
        self.assertNotIn(WA_DIGITS, json.dumps(item))
        self.assertEqual(self.diver.post('/api/experience-bookings', {'travel_experience_id': eid, 'participants': 2}).status, 400)
        r = self.diver.post('/api/experience-bookings', {'travel_experience_id': eid, 'participants': 2, 'in_person_ack': True})
        self.assertEqual((r.status, r.json['payment_required'], r.json['total'], r.json['pay_way']), (200, False, 400, 'in_person'), r)
        ebid = r.json['id']
        self.assertEqual(self.server.sql('SELECT price,currency FROM experience_bookings WHERE id=?', (ebid,))[0]['price'], 400)
        x = [e for e in self.diver.get('/api/me/area').json['experience_bookings'] if e['id'] == ebid][0]
        self.assertNotIn('pro_whatsapp', x)
        self.assertEqual(self.diver.post('/api/payments/checkout', {'experience_booking_id': ebid}).status, 400)
        self.pro.post('/api/provider/experience-bookings/status', {'id': ebid, 'status': 'confirmed'})
        x = [e for e in self.diver.get('/api/me/area').json['experience_bookings'] if e['id'] == ebid][0]
        self.assertTrue(x['pro_whatsapp'].startswith('https://wa.me/34611000000')); self.assertEqual(x['status_label'], 'Confirmada · pago en persona')
        self.assertEqual(self.pro.post('/api/pro-mark', {'kind': 'experience', 'id': ebid, 'mark': 'paid'}).status, 200)
        self.assertNotIn('pro_mark', [e for e in self.diver.get('/api/me/area').json['experience_bookings'] if e['id'] == ebid][0])

    # ------------------------------------------------------------------ 6. Planes · 7. Legal · DAC7
    def test_plans_and_legal(self):
        d = self.admin.get('/api/admin/plans').json
        self.assertIn('in_person_payments', d['features']); self.assertIn('online_payments', d['features'])
        plans = {p['code']: p for p in d['plans']}
        self.assertTrue(plans['booking']['features'].get('in_person_payments')); self.assertTrue(plans['pro']['features'].get('in_person_payments'))
        self.assertFalse(plans['free']['features'].get('in_person_payments'))
        for lang in ('es', 'en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh'):
            r = self.client().get(f'/api/legal/doc?slug=pago-en-persona&lang={lang}')
            self.assertEqual(r.status, 200, (lang, r)); self.assertNotIn('{{', r.json['markdown'])
        self.assertIn('único responsable de tus cobros', self.client().get('/api/legal/doc?slug=pago-en-persona&lang=es').json['markdown'])
        self.assertIn('pago-en-persona', self.client().get('/api/legal/doc?slug=condiciones-centros&lang=es').json['markdown'])
        self.assertIn('pago-en-persona', self.client().get('/api/legal/doc?slug=condiciones-reserva&lang=es').json['markdown'])

    def test_dac7_keeps_in_person_apart(self):
        slot = self.slot(33)
        bid = self.book(self.diver2, slot, pax=1).json['id']
        self.pro.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})
        year = day(33)[:4]
        d = self.admin.get(f'/api/admin/dac7?year={year}&part=in_person').json
        self.assertEqual(d['pending'], 'gestoria')
        mine = [r for r in d['items'] if r['id'] == self.pro.user['id']][0]
        self.assertEqual(mine['forma_de_cobro'], 'pago en persona'); self.assertIn('PENDIENTE GESTORÍA', mine['nota'])
        self.assertGreaterEqual(sum(mine[f'precio_publicado_t{i}'] for i in range(1, 5)), 45)
        self.assertNotIn(self.pro.user['id'], [r['id'] for r in self.admin.get(f'/api/admin/dac7?year={year}').json['items']])   # nothing went through the platform
        csv = self.admin.get(f'/api/admin/dac7?year={year}&part=in_person&format=csv')
        self.assertEqual(csv.status, 200); self.assertIn(b'precio_publicado_t1', csv.body)


class Migration(unittest.TestCase):
    """The freelance «Bajo petición» services of a professional without online payments were already paid to him
    directly («Pagas en el centro»): they become «Pago en persona», with his profile phone as WhatsApp when it has an
    international prefix. Nothing is deleted."""

    def test_old_freelance_services_become_in_person(self):
        s = Server({'STRIPE_SECRET_KEY': 'sk_test_mock'})
        try:
            s.start(); s.stop(cleanup=False)
            s.sql("DELETE FROM schema_migrations WHERE version='50.55'")
            for uid, extra in ((9101, ''), (9102, ''), (9103, 'acct_h')):
                s.sql("INSERT INTO users(id,fullname,email,username,password_hash,role,created_at,stripe_account_id,stripe_charges_enabled,stripe_payouts_enabled) VALUES(?,?,?,?,'!','freelance','x',?,?,?)",
                      (uid, f'F{uid}', f'f{uid}@x.org', f'f{uid}', extra or None, 1 if extra else 0, 1 if extra else 0))
            s.sql("INSERT INTO user_profiles(user_id,phone,updated_at) VALUES(9101,wod_cifrar('+34 622 000 111'),'x')")
            s.sql("INSERT INTO user_profiles(user_id,phone,updated_at) VALUES(9102,wod_cifrar('622000222'),'x')")
            for sid, uid, title in ((9101, 9101, 'Viejo'), (9102, 9102, 'Sin prefijo'), (9103, 9103, 'Con Stripe')):
                s.sql("INSERT INTO provider_services(id,provider_user_id,center_id,title,price,booking_mode,created_at,updated_at) VALUES(?,?,NULL,?,40,'request','x','x')", (sid, uid, title))
            s.start()
            ways = {r['id']: r['pay_way'] for r in s.sql('SELECT id,pay_way FROM provider_services WHERE id IN (9101,9102,9103)')}
            self.assertEqual(ways, {9101: 'in_person', 9102: 'in_person', 9103: 'online'})
            contacts = {r['ref_id']: r['phone'] for r in s.sql("SELECT ref_id,phone FROM pay_contacts WHERE kind='service' AND ref_id IN (9101,9102)")}
            self.assertEqual(contacts, {9101: '+34622000111'})          # only a number with its prefix becomes the WhatsApp
            self.assertTrue(s.sql("SELECT 1 FROM schema_migrations WHERE version='50.55'"))
            feats = {r['code']: json.loads(r['features']) for r in s.sql('SELECT code,features FROM plans')}
            self.assertTrue(feats['booking'].get('in_person_payments')); self.assertFalse(feats['free'].get('in_person_payments'))
            self.assertEqual(s.sql('SELECT COUNT(*) n FROM provider_services WHERE id IN (9101,9102,9103)')[0]['n'], 3)   # nothing deleted
        finally:
            s.stop()


if __name__ == '__main__':
    unittest.main(verbosity=2)
