"""v50.45 · Encargo 2b: new brand (logo, palette, icons, e-mails, PDF, cache) and currencies without decimals (yen).

- wod.money: smallest unit per currency (EUR, MXN, THB ×100; JPY ×1; KWD ×1000 ending in 0) and Stripe minimums.
- With the Stripe simulator: a booking in JPY is charged 10 000 (not 1 000 000), the amount check accepts it and a
  refund of 3 000 JPY is sent as 3 000; a price under the Stripe minimum (MXN) is refused with a clear message.
- Brand: the page, manifest and service worker only use /img/marca/; the old logo files are not served; e-mails
  and PDF carry the new icon; the brand colours are only written once (CSS variables).
"""
from __future__ import annotations

import re
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from wod import money as wmoney  # noqa: E402

from helpers import Client, ServerTestCase  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
CONNECT_SECRET = 'whsec_connect_money'


class MoneyUnits(unittest.TestCase):
    def test_smallest_unit(self):
        self.assertEqual(wmoney.to_minor(12.5, 'EUR'), 1250)
        self.assertEqual(wmoney.to_minor(250, 'MXN'), 25000)
        self.assertEqual(wmoney.to_minor(1500, 'THB'), 150000)
        self.assertEqual(wmoney.to_minor(5000, 'JPY'), 5000)            # never × 100
        self.assertEqual(wmoney.to_minor(5000.4, 'jpy'), 5000)
        self.assertEqual(wmoney.to_minor(1.234, 'KWD'), 1230)            # three decimals, last digit 0
        self.assertEqual(wmoney.from_minor(5000, 'JPY'), 5000); self.assertEqual(wmoney.from_minor(1250, 'EUR'), 12.5)
        self.assertEqual(wmoney.round_major(19.99, 'JPY'), 20)
        self.assertEqual(wmoney.code('xx'), 'EUR')
        self.assertTrue(wmoney.below_minimum(5, 'MXN')); self.assertFalse(wmoney.below_minimum(10, 'MXN'))
        self.assertTrue(wmoney.below_minimum(40, 'JPY')); self.assertFalse(wmoney.below_minimum(0.5, 'EUR'))


class YenEndToEnd(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base, 'STRIPE_CONNECT_WEBHOOK_SECRET': CONNECT_SECRET}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.pro = t.make_freelance(cls.admin, 'tokio')
        cls.server.sql("UPDATE users SET stripe_account_id='acct_tokio',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.pro.user['id'],))
        cls.diver = t.make_diver('yen')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def service(self, title, price, currency):
        sid = self.pro.post('/api/provider-services', {'title': title, 'price': price, 'currency': currency, 'booking_mode': 'payment', 'max_participants': 6}).json['id']
        slot = self.pro.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': (time.strftime('%Y') + '-12-20'), 'slot_time': '09:00', 'spots_total': 6}).json['slot_id']
        return sid, slot

    def test_jpy_charge_check_and_refund(self):
        sid, slot = self.service('Shore dive Izu', 5000, 'JPY')
        r = self.diver.post('/api/bookings', {'service_id': sid, 'slot_id': slot, 'participants': 2})
        self.assertEqual(r.status, 200, r)
        sess = self.stripe.last_session()
        self.assertEqual((sess['amount_total'], sess['currency']), (10000, 'jpy'))   # 10 000 yen, not 1 000 000
        self.stripe.pay(sess['id'])
        ev = {'id': f'evt_{time.time_ns()}', 'type': 'checkout.session.completed', 'account': 'acct_tokio', 'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
        payload, sig = StripeMock.signed(ev, CONNECT_SECRET)
        Client(self.server, origin=None).request('POST', '/api/payments/webhook/connect', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
        row = self.server.sql('SELECT b.status,o.amount_received,o.status AS os FROM bookings b JOIN payment_orders o ON o.booking_id=b.id WHERE b.id=?', (r.json['id'],))[0]
        self.assertEqual((row['status'], row['amount_received'], row['os']), ('confirmed', 10000, 'paid'))   # the amount check accepted it
        rr = self.pro.post(f"/api/bookings/{r.json['id']}/refund", {'amount': 3000, 'reason': 'requested_by_customer'})
        self.assertEqual(rr.status, 200, rr)
        self.assertEqual(self.stripe.refunds[-1]['amount'], 3000)

    def test_below_stripe_minimum_is_refused(self):
        sid, slot = self.service('Snorkel corto', 5, 'MXN')
        r = self.diver.post('/api/bookings', {'service_id': sid, 'slot_id': slot, 'participants': 1})
        self.assertEqual(r.status, 400, r)
        self.assertIn('mínimo', r.json['error'])


class Brand(ServerTestCase):
    def test_page_manifest_and_service_worker_use_the_new_brand(self):
        c = self.client()
        html = c.get('/').body.decode('utf-8')
        refs = set(re.findall(r'/img/marca/[\w./-]+', html))
        self.assertTrue({'/img/marca/favicon.ico', '/img/marca/apple-touch-icon-180.png', '/img/marca/og-image-1200x630.png'} <= refs, refs)
        for ref in refs | set(re.findall(r'/img/marca/[\w./-]+', (ROOT / 'public' / 'manifest.webmanifest').read_text()) + re.findall(r'/img/marca/[\w./-]+', (ROOT / 'public' / 'sw.js').read_text())):
            self.assertEqual(c.get(ref).status, 200, ref)
        self.assertIn('content="#011C3C"', html)
        for old in ('/assets/images/wod-icon.png', '/assets/images/wod-icon-512.png', '/assets/images/world-dives-discovery-logo.png'):
            self.assertEqual(c.get(old).status, 404, old)

    def test_palette_written_once(self):
        css = (ROOT / 'public' / 'css' / 'world-dives-v8.css').read_text()
        for hexv in ('#011C3C', '#043D6C', '#076898', '#1CA5C7', '#87E2EF'):
            self.assertEqual(css.upper().count(hexv), 1, hexv)            # only in the definition of its variable
        for old in ('#07364a', '#0b7a89', '#12a5b5'):
            self.assertNotIn(old, css.lower())

    def test_email_and_pdf_carry_the_new_icon(self):
        self.make_diver('marca')
        mails = self.server.sql("SELECT html FROM email_outbox WHERE html IS NOT NULL ORDER BY id DESC LIMIT 1")
        self.assertTrue(mails)
        self.assertIn('/img/marca/worldives-icono-correo-96.png', mails[0]['html'])
        self.assertIn('#011C3C', mails[0]['html']); self.assertNotIn('wod-icon', mails[0]['html'])
        sys.path.insert(0, str(ROOT / 'app'))
        from wod import pdf as wpdf
        d = wpdf.Document('Prueba', 'es')
        d.image_jpeg((ROOT / 'public' / 'img' / 'marca' / 'worldives-icono-pdf.jpg').read_bytes(), 40, 760, 58, 58)
        d.text(110, 800, 'WORLDIVES DISCOVERY', 17)
        out = d.pdf()
        self.assertIn(b'/Subtype /Image', out); self.assertIn(b'/DCTDecode', out); self.assertIn(b'/XObject', out)


if __name__ == '__main__':
    unittest.main()
