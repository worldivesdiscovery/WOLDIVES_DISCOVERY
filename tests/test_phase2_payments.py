"""Fase 2 (v50.34): direct charges without commission, Connect webhook, refunds by the provider, deposits,
cancellation policy per provider and per service, freelance professionals with their own Stripe account,
booking voucher, sponsorship register and the v50.34 migration. Stripe is a local simulator."""
import shutil
import sqlite3
import subprocess
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

from helpers import ServerTestCase, Server, Client
from stripe_mock import StripeMock

PLATFORM_SECRET = 'whsec_plat_local'
CONNECT_SECRET = 'whsec_connect_local'
# 1×1 transparent PNG
PNG = bytes.fromhex('89504e470d0a1a0a0000000d49484452000000010000000108060000001f15c4890000000d49444154789c6360000002000154a24f5d0000000049454e44ae426082')


class Payments(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base, 'STRIPE_WEBHOOK_SECRET': PLATFORM_SECRET,
                         'STRIPE_CONNECT_WEBHOOK_SECRET': CONNECT_SECRET, 'WOD_MAINTENANCE_SECONDS': '2'}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'directo', phone='+34 600 000 011')
        cls.other = t.make_center(cls.admin, 'vecino', phone='+34 600 000 012')
        cls.cid = cls.center.user['center_id']
        cls.server.sql("UPDATE centers SET stripe_account_id='acct_center_a',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.cid,))
        cls.server.sql("UPDATE centers SET stripe_account_id='acct_center_b',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.other.user['center_id'],))
        cls.pro = t.make_freelance(cls.admin, 'libre')
        cls.server.sql("UPDATE users SET stripe_account_id='acct_freelance',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.pro.user['id'],))
        cls.diver = t.make_diver('pagos1')
        cls.diver2 = t.make_diver('pagos2')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.stripe.stop()

    # ------------------------------------------------------------------ helpers
    def service(self, provider, price, mode='payment', date='2031-05-10', **extra):
        data = {'title': f'svc-{time.time_ns()}', 'price': price, 'booking_mode': mode}
        data.update(extra)
        r = provider.post('/api/provider-services', data)
        self.assertEqual(r.status, 200, r)
        sid = r.json['id']
        r = provider.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': date, 'slot_time': '10:00', 'spots_total': 8})
        self.assertEqual(r.status, 200, r)
        return sid, r.json['slot_id']

    def book(self, diver, sid, slot, center_id=None, pax=2):
        return diver.post('/api/bookings', {'center_id': center_id, 'service_id': sid, 'slot_id': slot, 'participants': pax})

    def bk(self, bid):
        return self.server.sql('SELECT * FROM bookings WHERE id=?', (bid,))[0]

    def connect_webhook(self, event, secret=CONNECT_SECRET, path='/api/payments/webhook/connect'):
        payload, sig = StripeMock.signed(event, secret)
        return Client(self.server, origin=None).request('POST', path, raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})

    def paid_booking(self, diver=None, price=50, pax=2, **svc_extra):
        sid, slot = self.service(self.center, price, **svc_extra)
        r = self.book(diver or self.diver, sid, slot, self.cid, pax)
        self.assertEqual(r.status, 200, r)
        bid = r.json['id']
        sess = self.stripe.last_session()
        self.stripe.pay(sess['id'])
        ev = {'id': f'evt_{time.time_ns()}', 'type': 'checkout.session.completed', 'account': 'acct_center_a',
              'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
        r = self.connect_webhook(ev)
        self.assertEqual(r.status, 200, r)
        return bid, sess

    # ------------------------------------------------------------------ 2.1 / 2.2 direct charges, no commission
    def test_direct_charge_without_commission(self):
        sid, slot = self.service(self.center, 60)
        r = self.book(self.diver, sid, slot, self.cid)
        self.assertEqual(r.status, 200, r)
        call = [c for c in self.stripe.calls if c['path'] == '/v1/checkout/sessions' and c['method'] == 'POST'][-1]
        self.assertEqual(call['account'], 'acct_center_a')  # created ON the centre's account
        pid = call['params'].get('payment_intent_data', {})
        self.assertNotIn('application_fee_amount', pid)
        self.assertNotIn('transfer_data', pid)
        order = self.server.sql('SELECT * FROM payment_orders WHERE booking_id=?', (r.json['id'],))[0]
        self.assertEqual((order['charge_type'], order['platform_fee'], order['connected_account_id']), ('direct', 0, 'acct_center_a'))

    def test_every_stripe_call_carries_the_account(self):
        sid, slot = self.service(self.center, 30)
        bid = self.book(self.diver2, sid, slot, self.cid, 1).json['id']
        sess = self.stripe.last_session()
        self.diver2.post('/api/payments/cancel', {'booking_id': bid})  # retrieve + expire
        calls = [c for c in self.stripe.calls if c['path'].startswith('/v1/checkout/sessions/' + sess['id'])]
        self.assertTrue(calls)
        self.assertTrue(all(c['account'] == 'acct_center_a' for c in calls), calls)

    # ------------------------------------------------------------------ 2.3 Connect webhook
    def test_connect_webhook_confirms_and_is_idempotent(self):
        sid, slot = self.service(self.center, 45)
        bid = self.book(self.diver, sid, slot, self.cid, 1).json['id']
        sess = self.stripe.last_session(); self.stripe.pay(sess['id'])
        ev = {'id': 'evt_connect_once', 'type': 'checkout.session.completed', 'account': 'acct_center_a',
              'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
        self.assertEqual(self.connect_webhook(ev).status, 200)
        b = self.bk(bid)
        self.assertEqual((b['status'], b['payment_status']), ('confirmed', 'paid'))
        self.assertTrue(self.connect_webhook(ev).json['duplicate'])

    def test_connect_event_of_another_account_is_ignored(self):
        sid, slot = self.service(self.center, 45)
        bid = self.book(self.diver2, sid, slot, self.cid, 1).json['id']
        sess = self.stripe.last_session(); self.stripe.pay(sess['id'])
        ev = {'id': 'evt_other_acct', 'type': 'checkout.session.completed', 'account': 'acct_center_b',
              'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
        self.assertEqual(self.connect_webhook(ev).status, 200)
        self.assertEqual(self.bk(bid)['status'], 'payment_in_progress')

    def test_webhook_secrets_are_separate(self):
        ev = {'id': 'evt_wrong_secret', 'type': 'account.updated', 'data': {'object': {'id': 'acct_x'}}}
        self.assertEqual(self.connect_webhook(ev, secret=PLATFORM_SECRET).status, 400)
        self.assertEqual(self.connect_webhook(ev, secret=CONNECT_SECRET, path='/api/payments/webhook').status, 400)

    def test_onboarding_uses_controller_properties(self):
        c = self.make_center(self.admin, 'nuevoalta', phone='+34 600 000 019')
        r = c.post('/api/payments/connect/onboard', {})
        self.assertEqual(r.status, 200, r)
        call = [x for x in self.stripe.calls if x['path'] == '/v1/accounts' and x['method'] == 'POST'][-1]['params']
        self.assertNotIn('type', call)
        self.assertEqual(call['controller']['stripe_dashboard']['type'], 'full')
        self.assertEqual(call['controller']['fees']['payer'], 'account')
        self.assertEqual(call['controller']['losses']['payments'], 'stripe')
        self.assertEqual(set(call['capabilities']), {'card_payments'})
        r = self.center.post('/api/payments/connect/login', {})
        self.assertEqual(r.json['url'], 'https://dashboard.stripe.com/')

    # ------------------------------------------------------------------ 2.4 refunds
    def test_partial_then_total_refund_by_centre(self):
        bid, _ = self.paid_booking(price=50, pax=2)  # 100 €
        r = self.center.post(f'/api/bookings/{bid}/refund', {'amount': 30, 'note': 'sin traje'})
        self.assertEqual(r.status, 200, r)
        ref = self.stripe.refunds[-1]
        self.assertEqual((ref['amount'], ref['account']), (3000, 'acct_center_a'))
        self.assertNotIn('reverse_transfer', ref['params'])
        b = self.bk(bid)
        self.assertEqual((b['status'], b['payment_status'], b['refunded_total']), ('confirmed', 'partially_refunded', 30))  # partial: still booked
        self.assertEqual(self.center.post(f'/api/bookings/{bid}/refund', {'amount': 80}).status, 400)  # more than what is left
        self.assertEqual(self.center.post(f'/api/bookings/{bid}/refund', {'amount': 70}).status, 200)
        self.assertEqual(self.bk(bid)['payment_status'], 'refunded')
        rows = self.server.sql('SELECT amount,source FROM payment_refunds WHERE booking_id=? ORDER BY id', (bid,))
        self.assertEqual([r['amount'] for r in rows], [30, 70])
        mail = self.server.sql("SELECT 1 FROM email_outbox WHERE template='refund_issued' AND related_id=?", (bid,))
        self.assertTrue(mail)

    def test_only_the_provider_refunds(self):
        bid, _ = self.paid_booking(diver=self.diver2, price=20, pax=1)
        for who in (self.other, self.diver2, self.admin, self.pro):
            r = who.post(f'/api/bookings/{bid}/refund', {'amount': 5})
            # v50.47 (B.3): another provider gets 404 (the booking does not exist for it); other roles 403
            self.assertEqual(r.status, 404 if who in (self.other, self.pro) else 403, (who.user if hasattr(who, 'user') else 'admin', r))
        self.assertEqual(self.bk(bid)['refunded_total'], 0)

    def test_diver_cancel_proposes_refund_by_policy(self):
        bid, _ = self.paid_booking(price=40, pax=1, cancel_free_hours=48, cancel_refund_pct=50)
        n_refunds = len(self.stripe.refunds)
        r = self.diver.post(f'/api/bookings/{bid}/cancel', {})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['refund'], 'proposed')
        self.assertEqual(len(self.stripe.refunds), n_refunds)  # the platform does not move the money
        b = self.bk(bid)
        self.assertEqual((b['status'], b['refund_status'], b['refund_proposed']), ('cancelled', 'proposed', 40))
        pending = self.center.get('/api/provider/payments').json['pending_refunds']
        self.assertIn(bid, [p['id'] for p in pending])
        # Reminder after 72 h (maintenance job).
        old = (datetime.now(timezone.utc) - timedelta(hours=73)).isoformat(timespec='seconds')
        self.server.sql('UPDATE bookings SET refund_proposed_at=? WHERE id=?', (old, bid))
        end = time.time() + 12
        while time.time() < end and not self.bk(bid)['refund_reminded_at']: time.sleep(0.5)
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='center_refund_reminder' AND related_id=?", (bid,)))
        self.assertEqual(self.center.post(f'/api/bookings/{bid}/refund', {'amount': 40}).status, 200)
        self.assertEqual(self.bk(bid)['refund_status'], 'done')

    def test_late_cancel_uses_percentage(self):
        soon = (datetime.now() + timedelta(days=1)).date().isoformat()
        sid, slot = self.service(self.center, 80, date=soon, cancel_free_hours=72, cancel_refund_pct=25)
        bid = self.book(self.diver2, sid, slot, self.cid, 1).json['id']
        sess = self.stripe.last_session(); self.stripe.pay(sess['id'])
        self.connect_webhook({'id': f'evt_late_{bid}', 'type': 'checkout.session.completed', 'account': 'acct_center_a',
                              'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}})
        terms = self.diver2.post(f'/api/bookings/{bid}/cancel', {'preview': True}).json['terms']
        self.assertEqual((terms['free'], terms['refund_amount'], terms['refund_pct']), (False, 20.0, 25))

    def test_policy_is_copied_into_the_booking(self):
        self.center.post('/api/provider/cancellation-policy', {'cancel_free_hours': 24, 'cancel_refund_pct': 0})
        sid, slot = self.service(self.center, 0, mode='request')
        bid = self.book(self.diver, sid, slot, self.cid, 1).json['id']
        self.assertEqual((self.bk(bid)['cancel_free_hours'], self.bk(bid)['cancel_refund_pct']), (24, 0))
        self.center.post('/api/provider/cancellation-policy', {'cancel_free_hours': 168, 'cancel_refund_pct': 10})
        d = self.diver.get(f'/api/bookings/{bid}').json['booking']
        self.assertEqual((d['cancel_free_hours'], d['cancel_refund_pct']), (24, 0))
        self.assertIn('24 horas', d['cancellation_text'])
        self.assertEqual(self.center.post('/api/provider/cancellation-policy', {'cancel_free_hours': 'x', 'cancel_refund_pct': 5}).status, 400)

    def test_centre_cancel_refunds_everything(self):
        bid, _ = self.paid_booking(diver=self.diver2, price=35, pax=2)
        r = self.center.post(f'/api/bookings/{bid}/status', {'status': 'cancelled', 'reason': 'mal tiempo'})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['refund'], 'refunded')
        b = self.bk(bid)
        self.assertEqual((b['status'], b['refunded_total']), ('cancelled', 70))

    # ------------------------------------------------------------------ 2.5 deposit
    def test_deposit_then_rest_at_the_desk(self):
        sid, slot = self.service(self.center, 100, deposit_type='percent', deposit_value=20)
        r = self.book(self.diver, sid, slot, self.cid, 2)  # 200 €, deposit 40 €
        self.assertEqual((r.status, r.json['deposit']), (200, 40.0))
        sess = self.stripe.last_session()
        self.assertEqual(sess['amount_total'], 4000)
        self.stripe.pay(sess['id'])
        self.connect_webhook({'id': f'evt_dep_{sess["id"]}', 'type': 'checkout.session.completed', 'account': 'acct_center_a',
                              'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}})
        b = self.bk(r.json['id'])
        self.assertEqual((b['status'], b['payment_status'], b['amount_paid'], b['amount_due']), ('confirmed', 'deposit_paid', 40, 160))
        r2 = self.center.post(f"/api/bookings/{b['id']}/payment", {'payment_status': 'paid', 'payment_method': 'Efectivo'})
        self.assertEqual(r2.status, 200, r2)
        b = self.bk(b['id'])
        self.assertEqual((b['payment_status'], b['amount_paid'], b['amount_due']), ('paid', 200, 0))
        self.assertEqual(self.center.post('/api/provider-services', {'title': 'x', 'price': 50, 'booking_mode': 'payment', 'deposit_type': 'percent', 'deposit_value': 150}).status, 400)

    # ------------------------------------------------------------------ 2.7 freelance without a centre
    def test_freelance_takes_bookings_and_payments(self):
        sid, slot = self.service(self.pro, 70)
        r = self.book(self.diver, sid, slot, None, 1)
        self.assertEqual(r.status, 200, r)
        bid = r.json['id']
        call = [c for c in self.stripe.calls if c['path'] == '/v1/checkout/sessions' and c['method'] == 'POST'][-1]
        self.assertEqual(call['account'], 'acct_freelance')
        sess = self.stripe.last_session(); self.stripe.pay(sess['id'])
        self.connect_webhook({'id': f'evt_fl_{bid}', 'type': 'checkout.session.completed', 'account': 'acct_freelance',
                              'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}})
        b = self.bk(bid)
        self.assertEqual((b['center_id'], b['provider_user_id'], b['status']), (None, self.pro.user['id'], 'confirmed'))
        self.assertIn(bid, [x['id'] for x in self.pro.get('/api/bookings').json['items']])
        self.assertNotIn(bid, [x['id'] for x in self.center.get('/api/bookings').json['items']])
        self.assertEqual(self.center.get(f'/api/bookings/{bid}').status, 403)
        self.assertEqual(self.pro.get(f'/api/bookings/{bid}').status, 200)
        self.assertEqual(self.pro.post(f'/api/bookings/{bid}/refund', {'amount': 10}).status, 200)
        self.assertEqual(self.stripe.refunds[-1]['account'], 'acct_freelance')
        st = self.pro.get('/api/payments/connect-status').json
        self.assertEqual((st['payee_type'], st['ready']), ('freelance', True))
        pdf = self.diver.get(f'/api/bookings/{bid}/receipt.pdf')
        self.assertEqual(pdf.status, 200)

    # ------------------------------------------------------------------ refunds and disputes from Stripe
    def test_refund_made_in_stripe_dashboard_is_recorded(self):
        bid, sess = self.paid_booking(price=25, pax=1)
        pi = self.stripe.sessions[sess['id']]['pi']
        ev = {'id': f'evt_ref_{bid}', 'type': 'charge.refunded', 'account': 'acct_center_a',
              'data': {'object': {'id': 'ch_x', 'object': 'charge', 'payment_intent': pi, 'amount_refunded': 1000,
                                  'refunds': {'data': [{'id': f're_dash_{bid}', 'amount': 1000, 'status': 'succeeded'}]}}}}
        self.assertEqual(self.connect_webhook(ev).status, 200)
        b = self.bk(bid)
        self.assertEqual((b['refunded_total'], b['payment_status'], b['status']), (10, 'partially_refunded', 'confirmed'))
        self.assertEqual(self.server.sql('SELECT source FROM payment_refunds WHERE stripe_refund_id=?', (f're_dash_{bid}',))[0]['source'], 'stripe')

    def test_dispute_marks_an_incident(self):
        bid, sess = self.paid_booking(price=25, pax=1)
        pi = self.stripe.sessions[sess['id']]['pi']
        ev = {'id': f'evt_disp_{bid}', 'type': 'charge.dispute.created', 'account': 'acct_center_a',
              'data': {'object': {'id': 'dp_1', 'object': 'dispute', 'payment_intent': pi, 'status': 'needs_response', 'reason': 'fraudulent'}}}
        self.assertEqual(self.connect_webhook(ev).status, 200)
        self.assertEqual(self.server.sql('SELECT incident FROM payment_orders WHERE booking_id=?', (bid,))[0]['incident'], 'dispute')
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='center_dispute' AND related_id=?", (bid,)))

    # ------------------------------------------------------------------ admin, KPIs, legal texts
    def test_admin_sees_income_by_currency_and_marks_incidents(self):
        self.paid_booking(price=10, pax=1)
        d = self.admin.get('/api/admin/payments').json
        self.assertNotIn('platform_fees', d)
        self.assertTrue(any(x['currency'] == 'EUR' and x['net'] > 0 for x in d['income']))
        oid = d['items'][0]['id']
        self.assertEqual(self.admin.post('/api/admin/payments/incident', {'order_id': oid, 'incident': 'customer_complaint', 'note': 'llamó el cliente'}).status, 200)
        self.assertEqual(self.center.post('/api/admin/payments/incident', {'order_id': oid, 'incident': 'resolved'}).status, 403)
        self.assertEqual(self.center.get('/api/admin/payments').status, 403)

    def test_no_commission_in_legal_texts_and_settings(self):
        for slug in ('centros', 'reservas'):
            txt = self.client().get(f'/api/legal/doc?slug={slug}').json['markdown'].lower()
            self.assertNotIn('comisión de intermediación', txt)
            self.assertNotIn('fee_percent', txt)
        self.assertNotIn('fee_percent', self.admin.get('/api/admin/legal').json['fields'])

    def test_centre_kpis_are_income_by_currency(self):
        self.paid_booking(price=15, pax=1)
        k = self.center.get('/api/center/analytics').json['metrics']
        self.assertTrue(any(x['currency'] == 'EUR' and x['amount'] > 0 for x in k['income']))

    # ------------------------------------------------------------------ 2.8 voucher
    def test_voucher_names_the_provider_and_is_not_an_invoice(self):
        self.server.sql("UPDATE centers SET legal_name='Buceo Directo S.L.',tax_id='B11111111' WHERE id=?", (self.cid,))
        bid, _ = self.paid_booking(price=12, pax=1)
        raw = self.diver.get(f'/api/bookings/{bid}/receipt.pdf').body
        self.assertTrue(raw.startswith(b'%PDF'))
        self.assertIn(b'/FontFile2', raw)
        self.assertIn(b'/ToUnicode', raw)
        if shutil.which('pdftotext'):
            out = Path(self.server.tmp) / f'v{bid}.pdf'; out.write_bytes(raw)
            text = subprocess.run(['pdftotext', str(out), '-'], capture_output=True, text=True).stdout
            text = text.lower()
            for needle in ('Justificante de reserva', 'Prestador del servicio', 'Buceo Directo S.L.', 'B11111111', 'WORLDIVES DISCOVERY: plataforma de reservas', 'Este documento no es una factura', 'impuestos incluidos'):
                self.assertIn(needle.lower(), text)

    # ------------------------------------------------------------------ 2.10 sponsorship
    def test_sponsored_label_is_fixed_and_sponsor_registered(self):
        fields = {'id': '0', 'kind': 'partner', 'title': 'Marca de aletas', 'url': 'https://aletas.example.org', 'label': 'Gratis!', 'active': '1'}
        r = self.admin.upload('/api/admin/site-promos', dict(fields, sponsor_name=''), 'logo.png', PNG)
        self.assertEqual(r.status, 200, r)  # a partner defaults to its own name as sponsor
        pid = r.json['id']
        self.assertEqual(self.server.sql('SELECT label FROM site_promos WHERE id=?', (pid,))[0]['label'], 'Patrocinado')
        reg = self.server.sql("SELECT * FROM sponsorships WHERE placement='band' AND ref_id=?", (pid,))
        self.assertEqual(reg[0]['sponsor_name'], 'Marca de aletas')
        self.assertEqual(self.admin.post('/api/admin/site-promos/delete', {'id': pid}).status, 200)
        self.assertTrue(self.server.sql("SELECT ended_at FROM sponsorships WHERE ref_id=? AND placement='band'", (pid,))[0]['ended_at'])
        r = self.admin.upload('/api/admin/site-promos', {'id': '0', 'kind': 'offer', 'title': 'Viaje', 'active': '1'}, 'x.png', PNG)
        self.assertEqual(r.status, 400)  # an offer needs to say who sponsors it


class MigrationV5034(unittest.TestCase):
    """Old databases: bookings.center_id becomes optional with a copy of the database made first; nothing is lost."""

    def test_rebuild_keeps_data_and_makes_a_backup(self):
        s = Server()
        try:
            s.start(); s.stop(cleanup=False)
            db = sqlite3.connect(s.db)
            sql = db.execute("SELECT sql FROM sqlite_master WHERE name='bookings'").fetchone()[0]
            # Simulate a v50.33 database: center_id NOT NULL again, one booking, migration not yet applied.
            db.execute('PRAGMA foreign_keys=OFF')
            db.execute('PRAGMA legacy_alter_table=ON')   # like the 12-step rebuild: the triggers of other tables keep naming «bookings»
            db.execute("INSERT INTO users(id,fullname,email,username,password_hash,role,created_at) VALUES(9501,'U','u9501@x.org','u9501','!','recreational','x')")
            cid = db.execute('SELECT id FROM centers LIMIT 1').fetchone()[0]
            db.execute('ALTER TABLE bookings RENAME TO bookings_tmp')
            db.execute(sql.replace('center_id INTEGER,', 'center_id INTEGER NOT NULL,', 1).replace('CREATE TABLE bookings', 'CREATE TABLE bookings', 1))
            cols = ','.join(r[1] for r in db.execute('PRAGMA table_info(bookings_tmp)'))
            db.execute(f'INSERT INTO bookings({cols}) SELECT {cols} FROM bookings_tmp')
            db.execute('DROP TABLE bookings_tmp')
            db.execute("INSERT INTO bookings(user_id,center_id,booking_date,status,created_at,updated_at) VALUES(9501,?,'2031-01-01','confirmed','x','x')", (cid,))
            db.execute("DELETE FROM schema_migrations WHERE version='50.34'")
            db.commit()
            self.assertEqual(db.execute("SELECT \"notnull\" FROM pragma_table_info('bookings') WHERE name='center_id'").fetchone()[0], 1)
            db.close()
            s.start()
            self.assertEqual(s.sql("SELECT \"notnull\" AS n FROM pragma_table_info('bookings') WHERE name='center_id'")[0]['n'], 0)
            self.assertEqual(len(s.sql('SELECT 1 FROM bookings WHERE user_id=9501')), 1)
            row = s.sql("SELECT backup_path FROM schema_migrations WHERE version='50.34'")[0]
            self.assertTrue(row['backup_path'] and Path(row['backup_path']).exists())
            bk = sqlite3.connect(row['backup_path'])
            try: self.assertEqual(bk.execute('SELECT COUNT(*) FROM bookings WHERE user_id=9501').fetchone()[0], 1)
            finally: bk.close()
            self.assertTrue(s.sql("SELECT 1 FROM sqlite_master WHERE name='trg_bookings_public_token'"))
        finally:
            s.stop()


if __name__ == '__main__':
    unittest.main(verbosity=2)
