"""Fase 1B (v50.32): the two booking modes and their state machine, for every combination of
mode × online payments yes/no × price > 0 / 0. Stripe is a local simulator (tests/stripe_mock.py)."""
import time
import unittest

from helpers import ServerTestCase, Server, Client
from stripe_mock import StripeMock

WEBHOOK_SECRET = 'whsec_test_local'


class BookingModes(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base, 'STRIPE_WEBHOOK_SECRET': WEBHOOK_SECRET,
                         'WOD_MAINTENANCE_SECONDS': '2'}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.pay_center = t.make_center(cls.admin, 'cobra', phone='+34 600 000 001')
        cls.desk_center = t.make_center(cls.admin, 'mostrador', phone='+34 600 000 002')
        cid = cls.pay_center.user['center_id']
        cls.server.sql("UPDATE centers SET stripe_account_id='acct_test_ready',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cid,))
        cls.diver = t.make_diver('modos1')
        cls.diver2 = t.make_diver('modos2')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.stripe.stop()

    # ------------------------------------------------------------------ helpers
    def service(self, center, mode, price, spots=6, **extra):
        data = {'title': f'{mode}-{price}-{time.time_ns()}', 'price': price, 'booking_mode': mode}
        data.update(extra)
        r = center.post('/api/provider-services', data)
        self.assertEqual(r.status, 200, r)
        sid = r.json['id']
        r = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-05-10', 'slot_time': '10:00', 'spots_total': spots})
        self.assertEqual(r.status, 200, r)
        return sid, r.json['slot_id']

    def book(self, diver, center, sid, slot, pax=2):
        return diver.post('/api/bookings', {'center_id': center.user['center_id'], 'service_id': sid, 'slot_id': slot, 'participants': pax})

    def spots(self, slot):
        return self.server.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot,))[0]['spots_available']

    def bk(self, bid):
        return self.server.sql('SELECT * FROM bookings WHERE id=?', (bid,))[0]

    def center_sees(self, center, bid):
        ids = [b['id'] for b in center.get('/api/bookings').json['items']]
        return bid in ids

    def webhook(self, event):
        payload, sig = StripeMock.signed(event, WEBHOOK_SECRET)
        return Client(self.server, origin=None).request('POST', '/api/payments/webhook', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})

    def wait_for(self, fn, timeout=12):
        end = time.time() + timeout
        while time.time() < end:
            if fn():
                return True
            time.sleep(0.5)
        return False

    # ------------------------------------------------------------------ «Pago al reservar»
    def test_payment_mode_needs_online_payments(self):
        r = self.desk_center.post('/api/provider-services', {'title': 'x', 'price': 30, 'booking_mode': 'payment'})
        self.assertEqual(r.status, 400)
        self.assertIn('Activa los cobros online', r.json['error'])

    def test_payment_mode_paid(self):
        sid, slot = self.service(self.pay_center, 'payment', 60)
        r = self.book(self.diver, self.pay_center, sid, slot)
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['status'], 'payment_in_progress')
        self.assertTrue(r.json['checkout_url'].startswith('https://checkout.stripe.test/'))
        bid = r.json['id']
        self.assertEqual(self.spots(slot), 4)  # held while paying
        self.assertFalse(self.center_sees(self.pay_center, bid))  # not a booking for the centre yet
        planning = self.pay_center.get('/api/center/planning?month=2031-05').json
        placeholders = [b for s in planning['slots'] for b in s['bookings'] if b.get('placeholder')]
        self.assertTrue(placeholders and all(b['id'] is None and 'fullname' not in b for b in placeholders))
        sess = self.stripe.last_session()
        self.assertEqual(sess['amount_total'], 12000)
        self.stripe.pay(sess['id'])
        r = self.webhook({'id': 'evt_paid_1', 'type': 'checkout.session.completed', 'data': {'object': {'id': sess['id'], 'metadata': sess['metadata']}}})
        self.assertEqual(r.status, 200, r)
        b = self.bk(bid)
        self.assertEqual((b['status'], b['payment_status']), ('confirmed', 'paid'))
        self.assertTrue(self.center_sees(self.pay_center, bid))
        self.assertEqual(self.spots(slot), 4)
        # Duplicate webhook: idempotent.
        self.assertEqual(self.webhook({'id': 'evt_paid_1', 'type': 'checkout.session.completed', 'data': {'object': {'id': sess['id'], 'metadata': sess['metadata']}}}).json.get('duplicate'), True)

    def test_payment_mode_return_page_confirms(self):
        sid, slot = self.service(self.pay_center, 'payment', 25)
        bid = self.book(self.diver2, self.pay_center, sid, slot, 1).json['id']
        sess = self.stripe.last_session()
        self.stripe.pay(sess['id'])
        r = self.diver2.get('/api/payments/session/' + sess['id'])
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.bk(bid)['status'], 'confirmed')

    def test_payment_mode_abandoned(self):
        sid, slot = self.service(self.pay_center, 'payment', 40)
        bid = self.book(self.diver, self.pay_center, sid, slot).json['id']
        self.assertEqual(self.spots(slot), 4)
        r = self.diver.post('/api/payments/cancel', {'booking_id': bid})
        self.assertEqual(r.status, 200, r)
        b = self.bk(bid)
        self.assertEqual(b['status'], 'expired')
        self.assertEqual(self.spots(slot), 6)
        self.assertFalse(self.center_sees(self.pay_center, bid))
        self.assertEqual(self.stripe.sessions[self.stripe.last_session()['id']]['status'], 'expired')

    def test_payment_mode_hold_expires(self):
        sid, slot = self.service(self.pay_center, 'payment', 40)
        bid = self.book(self.diver, self.pay_center, sid, slot).json['id']
        self.server.sql("UPDATE bookings SET hold_expires_at='2000-01-01T00:00' WHERE id=?", (bid,))
        self.assertTrue(self.wait_for(lambda: self.bk(bid)['status'] == 'expired'))
        self.assertEqual(self.bk(bid)['expired_reason'], 'hold_expired')
        self.assertEqual(self.spots(slot), 6)

    def test_payment_mode_cannot_be_confirmed_without_stripe(self):
        sid, slot = self.service(self.pay_center, 'payment', 50)
        bid = self.book(self.diver, self.pay_center, sid, slot).json['id']
        for path, body in ((f'/api/bookings/{bid}/status', {'status': 'confirmed'}), (f'/api/bookings/{bid}/payment', {'payment_status': 'paid'})):
            r = self.pay_center.post(path, body)
            self.assertEqual(r.status, 400, (path, r))
        self.assertEqual(self.bk(bid)['status'], 'payment_in_progress')
        # A webhook for an UNPAID session changes nothing.
        sess = self.stripe.last_session()
        self.webhook({'id': 'evt_unpaid', 'type': 'checkout.session.completed', 'data': {'object': {'id': sess['id'], 'metadata': sess['metadata']}}})
        self.assertEqual(self.bk(bid)['status'], 'payment_in_progress')
        # A forged webhook without a valid signature is refused.
        r = Client(self.server, origin=None).request('POST', '/api/payments/webhook', raw=b'{}', content_type='application/json', headers={'Stripe-Signature': 't=1,v1=bad'})
        self.assertEqual(r.status, 400)

    def test_payment_mode_free(self):
        sid, slot = self.service(self.pay_center, 'payment', 0)
        r = self.book(self.diver, self.pay_center, sid, slot)
        self.assertEqual(r.json['status'], 'confirmed')
        self.assertEqual(self.spots(slot), 4)

    def test_payment_mode_checkout_failure_releases(self):
        sid, slot = self.service(self.pay_center, 'payment', 30)
        self.stripe.fail_next = True
        r = self.book(self.diver, self.pay_center, sid, slot)
        self.assertEqual(r.status, 400)
        self.assertEqual(self.spots(slot), 6)

    def test_centre_disables_payments(self):
        t = self.client()
        c = self.make_center(self.admin, 'apagado', phone='+34 600 000 003')
        cid = c.user['center_id']
        self.server.sql("UPDATE centers SET stripe_account_id='acct_test_off',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cid,))
        sid, slot = self.service(c, 'payment', 45)
        r = self.webhook({'id': 'evt_acct_off', 'type': 'account.updated', 'data': {'object': {'id': 'acct_test_off', 'charges_enabled': False, 'payouts_enabled': True, 'details_submitted': True}}})
        self.assertEqual(r.status, 200)
        r = self.book(self.diver, c, sid, slot)
        self.assertEqual(r.status, 400)  # never silently «pay at the centre»
        svc = [s for s in self.client().get(f'/api/provider-services?center_id={cid}').json['items'] if s['id'] == sid][0]
        self.assertFalse(svc['bookable'])
        mails = self.server.sql("SELECT * FROM email_outbox WHERE template='center_payments_disabled'")
        self.assertTrue(mails)
        # Editing another field of the service is still possible.
        self.assertEqual(c.post('/api/provider-services/update', {'id': sid, 'title': 'Renombrado'}).status, 200)

    # ------------------------------------------------------------------ «Bajo petición»
    def test_request_accept_and_pay(self):
        sid, slot = self.service(self.pay_center, 'request', 70, response_hours=12, payment_hours=6)
        r = self.book(self.diver, self.pay_center, sid, slot)
        self.assertEqual(r.json['status'], 'requested')
        bid = r.json['id']
        self.assertEqual(self.spots(slot), 6)  # a request takes no spots
        self.assertIsNotNone(self.bk(bid)['response_deadline'])
        req = self.pay_center.get('/api/center/requests').json
        self.assertTrue(any(x['id'] == bid and x['minutes_left'] is not None for x in req['items']))
        # Paying before acceptance is impossible.
        self.assertEqual(self.diver.post('/api/payments/checkout', {'booking_id': bid}).status, 400)
        r = self.pay_center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})
        self.assertEqual(r.json['status'], 'accepted_pending_payment', r)
        b = self.bk(bid)
        self.assertIsNotNone(b['payment_deadline'])
        self.assertEqual(self.spots(slot), 4)
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='payment_required' AND related_id=?", (bid,)))
        r = self.diver.post('/api/payments/checkout', {'booking_id': bid})
        self.assertEqual(r.status, 200, r)
        sess = self.stripe.last_session()
        self.stripe.pay(sess['id'])
        self.webhook({'id': f'evt_req_{bid}', 'type': 'checkout.session.completed', 'data': {'object': {'id': sess['id'], 'metadata': sess['metadata']}}})
        self.assertEqual(self.bk(bid)['status'], 'confirmed')

    def test_request_accept_without_online_payments(self):
        sid, slot = self.service(self.desk_center, 'request', 55)
        bid = self.book(self.diver, self.desk_center, sid, slot).json['id']
        self.assertEqual(self.bk(bid)['payment_status'], 'at_center')
        r = self.desk_center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})
        self.assertEqual(r.json['status'], 'confirmed')
        b = self.bk(bid)
        self.assertEqual((b['status'], b['payment_status']), ('confirmed', 'at_center'))
        self.assertEqual(self.spots(slot), 4)

    def test_request_free(self):
        sid, slot = self.service(self.pay_center, 'request', 0)
        bid = self.book(self.diver, self.pay_center, sid, slot).json['id']
        self.assertEqual(self.pay_center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'}).json['status'], 'confirmed')
        self.assertEqual(self.bk(bid)['payment_status'], 'not_required')

    def test_request_reject_with_reason(self):
        sid, slot = self.service(self.pay_center, 'request', 30)
        bid = self.book(self.diver, self.pay_center, sid, slot).json['id']
        r = self.pay_center.post(f'/api/bookings/{bid}/status', {'status': 'rejected', 'reason': 'Mar de fondo previsto'})
        self.assertEqual(r.status, 200, r)
        b = self.bk(bid)
        self.assertEqual((b['status'], b['reject_reason']), ('rejected', 'Mar de fondo previsto'))
        self.assertEqual(self.spots(slot), 6)
        mail = self.server.sql("SELECT text FROM email_outbox WHERE template='booking_rejected' AND related_id=?", (bid,))[0]['text']
        self.assertIn('Mar de fondo previsto', mail)

    def test_request_no_answer_expires(self):
        sid, slot = self.service(self.pay_center, 'request', 30)
        bid = self.book(self.diver, self.pay_center, sid, slot).json['id']
        self.server.sql("UPDATE bookings SET response_deadline='2000-01-01T00:00' WHERE id=?", (bid,))
        self.assertTrue(self.wait_for(lambda: self.bk(bid)['status'] == 'expired'))
        self.assertEqual(self.bk(bid)['expired_reason'], 'no_response')
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='booking_expired' AND related_id=?", (bid,)))
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='center_booking_expired' AND related_id=?", (bid,)))
        # Too late to accept.
        self.assertEqual(self.pay_center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'}).status, 400)

    def test_request_accept_without_spots(self):
        sid, slot = self.service(self.pay_center, 'request', 30, spots=2)
        bid = self.book(self.diver, self.pay_center, sid, slot, 2).json['id']
        self.server.sql('UPDATE service_slots SET spots_available=1 WHERE id=?', (slot,))
        r = self.pay_center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})
        self.assertEqual(r.status, 400)
        self.assertIn('plazas', r.json['error'])
        self.assertEqual(self.bk(bid)['status'], 'requested')

    def test_request_accept_not_paid_in_time(self):
        sid, slot = self.service(self.pay_center, 'request', 80)
        bid = self.book(self.diver, self.pay_center, sid, slot).json['id']
        self.pay_center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})
        self.assertEqual(self.spots(slot), 4)
        self.server.sql("UPDATE bookings SET payment_deadline='2000-01-01T00:00' WHERE id=?", (bid,))
        self.assertTrue(self.wait_for(lambda: self.bk(bid)['status'] == 'expired'))
        self.assertEqual(self.bk(bid)['expired_reason'], 'not_paid')
        self.assertEqual(self.spots(slot), 6)
        self.assertEqual(self.diver.post('/api/payments/checkout', {'booking_id': bid}).status, 400)

    def test_mode_change_keeps_existing_bookings(self):
        sid, slot = self.service(self.pay_center, 'request', 35)
        bid = self.book(self.diver, self.pay_center, sid, slot).json['id']
        self.assertEqual(self.pay_center.post('/api/provider-services/update', {'id': sid, 'title': 'x', 'booking_mode': 'payment'}).status, 200)
        self.assertEqual(self.bk(bid)['booking_mode'], 'request')
        self.assertEqual(self.pay_center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'}).json['status'], 'accepted_pending_payment')

    def test_labels_and_filter(self):
        sid, slot = self.service(self.pay_center, 'payment', 20)
        cid = self.pay_center.user['center_id']
        items = self.client().get(f'/api/provider-services?center_id={cid}').json['items']
        s = [x for x in items if x['id'] == sid][0]
        self.assertEqual(s['mode_label'], 'Pago al reservar · confirmación inmediata')
        self.assertTrue(s['instant'])
        sid2, _ = self.service(self.pay_center, 'request', 20, response_hours=6)
        s2 = [x for x in self.client().get(f'/api/provider-services?center_id={cid}').json['items'] if x['id'] == sid2][0]
        self.assertEqual(s2['mode_label'], 'Bajo petición · el centro responde en 6 h')
        time.sleep(0.1)
        self.server.sql('SELECT 1')
        d = self.client().get('/api/center-directory?only=instant').json
        # The directory snapshot refreshes in the background; the flag exists either way.
        self.assertIn('items', d)


class InstantMigration(unittest.TestCase):
    """«Reserva inmediata» services and templates move to one of the two modes when the server starts."""

    def test_migration(self):
        s = Server({'STRIPE_SECRET_KEY': 'sk_test_mock'})
        try:
            s.start(); s.stop(cleanup=False)  # creates the tables of the current version
            s.sql("UPDATE provider_services SET booking_mode='request'")
            s.sql("INSERT INTO users(id,fullname,email,username,password_hash,role,created_at) VALUES(9001,'C','c@x.org','c9001','!','center','x')")
            s.sql("INSERT INTO centers(id,name,country,active,created_at,updated_at,stripe_account_id,stripe_charges_enabled,stripe_payouts_enabled) VALUES(9001,'Cobra','España',1,'x','x','acct_1',1,1)")
            s.sql("INSERT INTO centers(id,name,country,active,created_at,updated_at) VALUES(9002,'Sin cobros','España',1,'x','x')")
            s.sql("INSERT INTO provider_services(id,provider_user_id,center_id,title,price,booking_mode,created_at,updated_at) VALUES(9001,9001,9001,'Con precio y cobros',50,'instant','x','x')")
            s.sql("INSERT INTO provider_services(id,provider_user_id,center_id,title,price,booking_mode,created_at,updated_at) VALUES(9002,9001,9002,'Con precio sin cobros',50,'instant','x','x')")
            s.sql("INSERT INTO provider_services(id,provider_user_id,center_id,title,price,booking_mode,created_at,updated_at) VALUES(9003,9001,9001,'Gratis',0,'instant','x','x')")
            s.sql("INSERT INTO service_templates(provider_user_id,name,booking_mode,price,created_at,updated_at) VALUES(9001,'Plantilla','instant',40,'x','x')")
            s.start()
            modes = {r['id']: r['booking_mode'] for r in s.sql('SELECT id,booking_mode FROM provider_services WHERE id IN (9001,9002,9003)')}
            self.assertEqual(modes, {9001: 'payment', 9002: 'request', 9003: 'request'})
            report = s.sql('SELECT * FROM booking_mode_migration')
            self.assertGreaterEqual(len(report), 4)
            self.assertFalse(s.sql("SELECT 1 FROM service_templates WHERE booking_mode='instant'"))
        finally:
            s.stop()


if __name__ == '__main__':
    unittest.main(verbosity=2)
