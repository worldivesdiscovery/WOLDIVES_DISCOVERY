"""Encargo 2, puntos 2, 3 y 4 (v50.41): cancelling a departure (choice of another date or the full refund, automatic
refund after the deadline, history of the departure), change of date by the diver (direct or with approval, deadline,
price difference shown, spots moved atomically) and the waiting list (spots kept for the first person who fits,
2 h never after the start, then the next one; booking mode respected). Permissions between roles. Stripe is a local
simulator; every test runs on a temporary copy of the database."""
import datetime as dt
import re
import time
import unittest

from helpers import ServerTestCase, Client
from stripe_mock import StripeMock

CONNECT_SECRET = 'whsec_connect_local'
DAY = lambda n: (dt.date.today() + dt.timedelta(days=n)).isoformat()


def wait_for(fn, seconds=12):
    end = time.time() + seconds
    while time.time() < end:
        if fn(): return True
        time.sleep(0.4)
    return False


class SlotCancel(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base, 'STRIPE_CONNECT_WEBHOOK_SECRET': CONNECT_SECRET, 'WOD_MAINTENANCE_SECONDS': '2'}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'mal', phone='+34 600 410 001')
        cls.other = t.make_center(cls.admin, 'otromal', phone='+34 600 410 002')
        cls.cid = cls.center.user['center_id']
        cls.server.sql("UPDATE centers SET stripe_account_id='acct_mal',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.cid,))
        cls.sid = cls.center.post('/api/provider-services', {'title': 'Doble inmersión', 'price': 40, 'booking_mode': 'payment'}).json['id']
        mk = lambda d, n=10: cls.center.post('/api/provider-services/slot', {'service_id': cls.sid, 'slot_date': d, 'slot_time': '09:00', 'spots_total': n}).json['slot_id']
        cls.A, cls.B, cls.D = mk(DAY(5)), mk(DAY(6)), mk(DAY(7))
        cls.d1, cls.d2, cls.d3, cls.d4 = (t.make_diver(x) for x in ('lluvia1', 'lluvia2', 'lluvia3', 'lluvia4'))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def paid(self, diver, slot, pax):
        r = diver.post('/api/bookings', {'center_id': self.cid, 'service_id': self.sid, 'slot_id': slot, 'participants': pax})
        self.assertEqual(r.status, 200, r)
        sess = self.stripe.last_session(); self.stripe.pay(sess['id'])
        ev = {'id': f'evt_{time.time_ns()}', 'type': 'checkout.session.completed', 'account': 'acct_mal', 'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
        payload, sig = StripeMock.signed(ev, CONNECT_SECRET)
        Client(self.server, origin=None).request('POST', '/api/payments/webhook/connect', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
        self.assertEqual(self.server.sql('SELECT status FROM bookings WHERE id=?', (r.json['id'],))[0]['status'], 'confirmed')
        return r.json['id']

    def spots(self, slot):
        return self.server.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot,))[0]['spots_available']

    def test_cancel_choose_and_automatic_refund(self):
        b1 = self.paid(self.d1, self.A, 2); b2 = self.paid(self.d2, self.A, 1)
        b3 = self.d3.post('/api/bookings', {'center_id': self.cid, 'service_id': self.sid, 'slot_id': self.A, 'participants': 1}).json['id']   # paying right now
        c = self.center
        # Preview: who is affected and what they receive
        p = c.post('/api/provider-services/slot-cancel', {'slot_id': self.A, 'preview': True}).json
        rec = {a['booking_id']: a['receives'] for a in p['affected']}
        self.assertEqual(rec, {b1: 'refund', b2: 'refund', b3: 'released'}); self.assertEqual(p['choice_hours'], 48)
        self.assertEqual([a['paid'] for a in p['affected'] if a['booking_id'] == b1], [80.0])
        # Permissions and bad data
        self.assertEqual(self.other.post('/api/provider-services/slot-cancel', {'slot_id': self.A, 'reason': 'weather'}).status, 404)  # v50.47 (B.3): what belongs to another centre does not exist (404)
        self.assertEqual(self.d1.post('/api/provider-services/slot-cancel', {'slot_id': self.A, 'reason': 'weather'}).status, 404)  # v50.47 (B.3)
        self.assertEqual(c.post('/api/provider-services/slot-cancel', {'slot_id': self.A}).status, 400)
        self.assertEqual(c.post('/api/provider-services/slot-cancel', {'slot_id': self.A, 'reason': 'other', 'note': ''}).status, 400)
        self.assertEqual(c.post('/api/provider-services/slot-cancel', {'slot_id': self.A, 'reason': 'weather', 'choice_hours': 0}).status, 400)
        # Cancel
        r = c.post('/api/provider-services/slot-cancel', {'slot_id': self.A, 'reason': 'weather', 'note': 'Levante fuerte'})
        self.assertEqual((r.status, r.json.get('affected')), (200, 3), r)
        self.assertEqual(self.server.sql('SELECT status FROM bookings WHERE id=?', (b3,))[0]['status'], 'expired')
        mails = self.server.sql("SELECT to_email,text FROM email_outbox WHERE template='slot_cancelled' ORDER BY id")
        self.assertEqual([m['to_email'] for m in mails], ['lluvia1@diver.example.org', 'lluvia2@diver.example.org'])
        self.assertIn('Levante fuerte', mails[0]['text']); self.assertIn('80 €', mails[0]['text'])
        tok = re.search(r'salida-cancelada\?b=(\d+)&t=([A-Za-z0-9_\-]+)', mails[0]['text'])
        self.assertEqual(int(tok.group(1)), b1)
        self.assertEqual(c.post('/api/provider-services/slot-cancel', {'slot_id': self.A, 'reason': 'weather'}).status, 400)   # already cancelled
        # Diver 1 chooses another date from the email link, without signing in
        anon = self.client()
        self.assertEqual(anon.get(f'/api/slot-cancel/{b1}?t=falso').status, 404)  # v50.47 (B.3)
        o = anon.get(f'/api/slot-cancel/{b1}?t={tok.group(2)}').json
        self.assertEqual(o['paid'], 80.0); self.assertIn(self.B, [a['slot_id'] for a in o['alternatives']])
        before = self.spots(self.B)
        self.assertEqual(anon.post(f'/api/slot-cancel/{b1}', {'t': tok.group(2), 'choice': 'reschedule', 'slot_id': self.A}).status, 400)
        r = anon.post(f'/api/slot-cancel/{b1}', {'t': tok.group(2), 'choice': 'reschedule', 'slot_id': self.B})
        self.assertEqual((r.status, r.json.get('result')), (200, 'rescheduled'), r)
        bk = self.server.sql('SELECT slot_id,status,booking_date FROM bookings WHERE id=?', (b1,))[0]
        self.assertEqual((bk['slot_id'], bk['status'], bk['booking_date']), (self.B, 'confirmed', DAY(6)))
        self.assertEqual(self.spots(self.B), before - 2)
        self.assertEqual(anon.post(f'/api/slot-cancel/{b1}', {'t': tok.group(2), 'choice': 'refund'}).status, 400)   # only once
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='booking_date_changed' AND to_email='lluvia1@diver.example.org'"))
        # Diver 2 asks for the refund (signed in)
        r = self.d2.post(f'/api/slot-cancel/{b2}', {'choice': 'refund'})
        self.assertEqual((r.status, r.json.get('result')), (200, 'refunded'), r)
        self.assertEqual(self.server.sql('SELECT status,refunded_total FROM bookings WHERE id=?', (b2,))[0]['status'], 'cancelled')
        self.assertTrue(self.server.sql("SELECT 1 FROM payment_refunds WHERE booking_id=?", (b2,)))
        self.assertEqual(self.d1.post(f'/api/slot-cancel/{b2}', {'choice': 'refund'}).status, 403)   # not hers
        # History of the departure and planning
        hist = [e['kind'] for e in c.get(f'/api/manifest/{self.A}').json['events']]
        self.assertTrue({'cancelled', 'choice_reschedule', 'choice_refund'} <= set(hist))
        pl = c.get(f'/api/center/planning?month={DAY(5)[:7]}').json
        self.assertTrue(any(s['id'] == self.A and s['cancelled_at'] for s in pl['slots']))
        # Automatic refund when nobody answers
        b4 = self.paid(self.d4, self.D, 1)
        c.post('/api/provider-services/slot-cancel', {'slot_id': self.D, 'reason': 'sea', 'choice_hours': 1})
        self.server.sql("UPDATE slot_cancel_offers SET deadline='2000-01-01T00:00' WHERE booking_id=?", (b4,))
        self.assertTrue(wait_for(lambda: self.server.sql('SELECT status FROM bookings WHERE id=?', (b4,))[0]['status'] == 'cancelled'))
        off = self.server.sql('SELECT choice,refund_result FROM slot_cancel_offers WHERE booking_id=?', (b4,))[0]
        self.assertEqual((off['choice'], off['refund_result']), ('auto_refund', 'refunded'))
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='center_slot_choice'"))


class Reschedule(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'cambio', phone='+34 600 420 001')
        cls.other = t.make_center(cls.admin, 'otrocambio', phone='+34 600 420 002')
        cls.cid = cls.center.user['center_id']
        cls.sid = cls.center.post('/api/provider-services', {'title': 'Bautizo', 'price': 30, 'booking_mode': 'request'}).json['id']
        mk = lambda d: cls.center.post('/api/provider-services/slot', {'service_id': cls.sid, 'slot_date': d, 'slot_time': '10:00', 'spots_total': 6}).json['slot_id']
        cls.X, cls.Y, cls.Y2, cls.Z = mk(DAY(10)), mk(DAY(11)), mk(DAY(12)), mk(DAY(1))
        cls.diver = t.make_diver('cambia3'); cls.stranger = t.make_diver('ajeno3')

    def book(self, slot, pax=2, diver=None):
        r = (diver or self.diver).post('/api/bookings', {'center_id': self.cid, 'service_id': self.sid, 'slot_id': slot, 'participants': pax})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.center.post(f"/api/bookings/{r.json['id']}/status", {'status': 'confirmed'}).status, 200)
        return r.json['id']

    def spots(self, slot):
        return self.server.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot,))[0]['spots_available']

    def test_direct_approval_deadline_and_permissions(self):
        c = self.center
        self.assertEqual(self.other.post('/api/provider-services/options', {'id': self.sid, 'reschedule_mode': 'direct'}).status, 404)  # v50.47 (B.3): what belongs to another centre does not exist (404)
        self.assertEqual(c.post('/api/provider-services/options', {'id': self.sid, 'reschedule_mode': 'loquesea'}).status, 400)
        self.assertEqual(c.post('/api/provider-services/options', {'id': self.sid, 'reschedule_mode': 'direct', 'reschedule_hours': 48}).status, 200)
        # A different price on the new date: the difference is shown, the booking keeps its price
        self.server.sql('INSERT INTO center_tariffs(center_id,service_id,price,currency,effective_from,active,created_at,updated_at) VALUES(?,?,45,"EUR",?,1,?,?)', (self.cid, self.sid, DAY(11), DAY(0), DAY(0)))
        bid = self.book(self.X)
        o = self.diver.get(f'/api/bookings/{bid}/reschedule-options').json
        self.assertTrue(o['allowed']); self.assertEqual(o['mode'], 'direct')
        ids = {x['slot_id']: x for x in o['options']}
        self.assertNotIn(self.X, ids); self.assertIn(self.Y, ids)
        self.assertEqual(ids[self.Y]['price_diff'], 30.0)              # (45 − 30) × 2
        self.assertEqual(self.stranger.post(f'/api/bookings/{bid}/change-date', {'slot_id': self.Y}).status, 403)
        self.assertEqual(c.post(f'/api/bookings/{bid}/change-date', {'slot_id': self.Y}).status, 403)
        x0, y0 = self.spots(self.X), self.spots(self.Y)
        r = self.diver.post(f'/api/bookings/{bid}/change-date', {'slot_id': self.Y})
        self.assertEqual((r.status, r.json.get('status')), (200, 'changed'), r)
        b = self.server.sql('SELECT slot_id,price FROM bookings WHERE id=?', (bid,))[0]
        self.assertEqual((b['slot_id'], b['price']), (self.Y, 60.0))
        self.assertEqual((self.spots(self.X), self.spots(self.Y)), (x0 + 2, y0 - 2))   # spots moved together
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='booking_date_changed'"))
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='center_booking_date_changed'"))
        # With approval
        c.post('/api/provider-services/options', {'id': self.sid, 'reschedule_mode': 'approval', 'reschedule_hours': 48})
        r = self.diver.post(f'/api/bookings/{bid}/change-date', {'slot_id': self.Y2})
        self.assertEqual(r.json.get('status'), 'requested', r)
        self.assertEqual(self.server.sql('SELECT slot_id FROM bookings WHERE id=?', (bid,))[0]['slot_id'], self.Y)   # nothing moves yet
        self.assertEqual(self.diver.post(f'/api/bookings/{bid}/change-date', {'slot_id': self.X}).status, 400)    # one request at a time
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='center_reschedule_request'"))
        self.assertEqual(self.other.post(f'/api/bookings/{bid}/change-date/decide', {'approve': True}).status, 404)  # v50.47 (B.3)
        self.assertEqual(self.diver.post(f'/api/bookings/{bid}/change-date/decide', {'approve': True}).status, 404)  # v50.47 (B.3)
        self.assertEqual(c.get(f'/api/bookings/{bid}/change-date').json['request']['to_slot_id'], self.Y2)
        self.assertEqual(c.post(f'/api/bookings/{bid}/change-date/decide', {'approve': True}).status, 200)
        self.assertEqual(self.server.sql('SELECT slot_id FROM bookings WHERE id=?', (bid,))[0]['slot_id'], self.Y2)
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='reschedule_approved'"))
        self.diver.post(f'/api/bookings/{bid}/change-date', {'slot_id': self.X})
        self.assertEqual(c.post(f'/api/bookings/{bid}/change-date/decide', {'approve': False, 'note': 'Ese día no tenemos barco'}).status, 200)
        self.assertEqual(self.server.sql('SELECT slot_id FROM bookings WHERE id=?', (bid,))[0]['slot_id'], self.Y2)
        self.assertIn('no tenemos barco', self.server.sql("SELECT text FROM email_outbox WHERE template='reschedule_rejected'")[0]['text'])
        # Deadline (48 h) and «no» mode
        near = self.book(self.Z, 1)
        o = self.diver.get(f'/api/bookings/{near}/reschedule-options').json
        self.assertFalse(o['allowed']); self.assertIn('plazo', o['reason'])
        self.assertEqual(self.diver.post(f'/api/bookings/{near}/change-date', {'slot_id': self.X}).status, 400)
        c.post('/api/provider-services/options', {'id': self.sid, 'reschedule_mode': 'none'})
        self.assertFalse(self.diver.get(f'/api/bookings/{bid}/reschedule-options').json['allowed'])


class Waitlist(ServerTestCase):
    extra_env = {'WOD_MAINTENANCE_SECONDS': '2'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'espera', phone='+34 600 430 001')
        cls.cid = cls.center.user['center_id']
        cls.sid = cls.center.post('/api/provider-services', {'title': 'Salida a la reserva marina', 'price': 35, 'booking_mode': 'request'}).json['id']
        cls.S = cls.center.post('/api/provider-services/slot', {'service_id': cls.sid, 'slot_date': DAY(4), 'slot_time': '09:30', 'spots_total': 2}).json['slot_id']
        cls.a, cls.b, cls.c = (t.make_diver(x) for x in ('esperaA', 'esperaB', 'esperaC'))

    def spots(self):
        return self.server.sql('SELECT spots_available FROM service_slots WHERE id=?', (self.S,))[0]['spots_available']

    def entry(self, diver):
        return self.server.sql('SELECT * FROM waitlist_entries WHERE slot_id=? AND user_id=? ORDER BY id DESC', (self.S, diver.user['id']))[0]

    def test_waiting_list_order_hold_and_expiry(self):
        self.assertEqual(self.b.post('/api/waitlist/join', {'slot_id': self.S}).status, 400)    # still spots: book instead
        ba = self.a.post('/api/bookings', {'center_id': self.cid, 'service_id': self.sid, 'slot_id': self.S, 'participants': 2}).json['id']
        self.center.post(f'/api/bookings/{ba}/status', {'status': 'confirmed'})
        self.assertEqual(self.spots(), 0)
        self.assertEqual(self.center.post('/api/waitlist/join', {'slot_id': self.S}).status, 403)   # staff accounts do not queue
        r = self.b.post('/api/waitlist/join', {'slot_id': self.S, 'participants': 1})
        self.assertEqual((r.status, r.json.get('position')), (200, 1), r)
        self.assertEqual(self.b.post('/api/waitlist/join', {'slot_id': self.S}).status, 400)    # once
        self.assertEqual(self.c.post('/api/waitlist/join', {'slot_id': self.S, 'participants': 2}).json.get('position'), 2)
        lst = self.b.get(f'/api/provider-services?provider_id=0&center_id={self.cid}').json['items'][0]['slots']
        self.assertEqual([s['waitlist']['status'] for s in lst if s['id'] == self.S], ['waiting'])
        # The centre sees the list in the departure
        self.assertEqual([w['fullname'] for w in self.center.get(f'/api/manifest/{self.S}').json['waitlist']], ['Buceador esperaB Pérez', 'Buceador esperaC Pérez'])
        # A cancels one booking of 2: 2 spots free → B (1) gets one kept for 2 h; C needs 2 and keeps waiting
        self.assertEqual(self.a.post(f'/api/bookings/{ba}/cancel', {}).status, 200)
        eb = self.entry(self.b)
        self.assertEqual((eb['status'], eb['held']), ('notified', 1))
        start = dt.datetime.fromisoformat(f'{DAY(4)}T09:30')
        self.assertLessEqual(dt.datetime.fromisoformat(eb['expires_at'][:16]), start)
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='waitlist_spot' AND to_email='esperab@diver.example.org'"))
        self.assertEqual(self.entry(self.c)['status'], 'waiting')
        self.assertEqual(self.spots(), 1)                                   # the kept spot is not free for others
        # B books (request mode): the kept spot goes with the request
        r = self.b.post('/api/bookings', {'center_id': self.cid, 'service_id': self.sid, 'slot_id': self.S, 'participants': 1})
        self.assertEqual(r.status, 200, r)
        bb = self.server.sql('SELECT status,slot_reserved FROM bookings WHERE id=?', (r.json['id'],))[0]
        self.assertEqual((bb['status'], bb['slot_reserved']), ('requested', 1))
        self.assertEqual(self.entry(self.b)['status'], 'booked')
        # The centre rejects B's request: 2 spots free → C is notified
        self.center.post(f"/api/bookings/{r.json['id']}/status", {'status': 'rejected', 'reason': 'Sin guía'})
        self.assertEqual((self.entry(self.c)['status'], self.entry(self.c)['held']), ('notified', 2))
        # C does not book in time: the spots are freed again
        self.server.sql("UPDATE waitlist_entries SET expires_at='2000-01-01T00:00' WHERE user_id=?", (self.c.user['id'],))
        self.assertTrue(wait_for(lambda: self.entry(self.c)['status'] == 'expired'))
        self.assertEqual(self.spots(), 2)
        hist = {e['kind'] for e in self.center.get(f'/api/manifest/{self.S}').json['events']}
        self.assertTrue({'waitlist_joined', 'waitlist_notified', 'waitlist_booked', 'waitlist_expired'} <= hist)
        # Turned off per service
        self.center.post('/api/provider-services/options', {'id': self.sid, 'waitlist_enabled': False})
        self.server.sql('UPDATE service_slots SET spots_available=0 WHERE id=?', (self.S,))
        self.assertEqual(self.a.post('/api/waitlist/join', {'slot_id': self.S}).status, 400)


if __name__ == '__main__':
    unittest.main()
