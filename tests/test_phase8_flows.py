"""Flows the inventory (docs/legal/inventario.md § 6.8) found without an automated test: password recovery, change
of email, closing the other sessions when the password changes, and the price of a travel experience × participants."""
import re
import unittest

from helpers import ServerTestCase
from stripe_mock import StripeMock

PW = 'buceo-seguro-2026'


class AccountFlows(ServerTestCase):
    def mail(self, template, to):
        rows = self.server.sql('SELECT text FROM email_outbox WHERE template=? AND to_email=? ORDER BY id DESC', (template, to))
        self.assertTrue(rows, f'sin correo {template} a {to}')
        return rows[0]['text']

    def test_password_recovery(self):
        diver = self.make_diver('recupera8')
        anon = self.client()
        # Same answer whether the account exists or not
        self.assertEqual(anon.post('/api/auth/forgot', {'email': 'nadie@example.org'}).json, {'ok': True})
        self.assertEqual(anon.post('/api/auth/forgot', {'email': 'recupera8@diver.example.org'}).json, {'ok': True})
        token = re.search(r'restablecer\?token=([A-Za-z0-9_\-]+)', self.mail('password_reset', 'recupera8@diver.example.org')).group(1)
        self.assertEqual(anon.post('/api/auth/reset', {'token': token, 'password': '123'}).status, 400)       # weak password
        self.assertEqual(anon.post('/api/auth/reset', {'token': 'falso', 'password': 'nueva-clave-segura-8'}).status, 400)
        self.assertEqual(anon.post('/api/auth/reset', {'token': token, 'password': 'nueva-clave-segura-8'}).status, 200)
        self.assertEqual(anon.post('/api/auth/reset', {'token': token, 'password': 'otra-clave-segura-8'}).status, 400)  # single use
        self.assertEqual(diver.get('/api/me/area').status, 403)    # the sessions that were open are closed
        self.assertEqual(self.client().login('diver_recupera8', PW).status, 401)
        self.assertEqual(self.client().login('diver_recupera8', 'nueva-clave-segura-8').status, 200)
        self.mail('password_changed', 'recupera8@diver.example.org')

    def test_password_change_closes_other_sessions(self):
        a = self.make_diver('sesiones8')
        b = self.client(); self.assertEqual(b.login('diver_sesiones8').status, 200)
        self.assertEqual(a.post('/api/account/password', {'current_password': 'mal', 'new_password': 'nueva-clave-segura-8'}).status, 400)
        self.assertEqual(a.post('/api/account/password', {'current_password': PW, 'new_password': 'nueva-clave-segura-8'}).status, 200)
        self.assertEqual(a.get('/api/me/area').status, 200)        # the session that made the change stays open
        self.assertEqual(b.get('/api/me/area').status, 403)        # the others are closed

    def test_change_of_email_confirmed_from_the_new_address(self):
        diver = self.make_diver('cambia8')
        other = self.make_diver('ocupado8')
        self.assertEqual(diver.post('/api/account/email', {'email': 'nuevo8@example.org', 'password': 'mal'}).status, 400)
        self.assertEqual(diver.post('/api/account/email', {'email': 'ocupado8@diver.example.org', 'password': PW}).status, 400)
        self.assertEqual(diver.post('/api/account/email', {'email': 'nuevo8@example.org', 'password': PW}).status, 200)
        self.assertEqual(self.server.sql('SELECT email FROM users WHERE id=?', (diver.user['id'],))[0]['email'], 'cambia8@diver.example.org')    # nothing changes until it is confirmed
        token = re.search(r'verificar-email\?token=([A-Za-z0-9_\-]+)', self.mail('verify_email_change', 'nuevo8@example.org')).group(1)
        r = self.client().post('/api/auth/verify-email', {'token': token})
        self.assertEqual((r.status, r.json.get('changed')), (200, True))
        self.assertEqual(self.server.sql('SELECT email FROM users WHERE id=?', (diver.user['id'],))[0]['email'], 'nuevo8@example.org')
        self.assertEqual(self.client().post('/api/auth/verify-email', {'token': token}).status, 400)   # single use
        self.assertEqual(diver.get('/api/me/area').status, 403)    # sessions closed after the change
        self.assertEqual(other.get('/api/me/area').status, 200)


class ExperiencePrice(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'viajes8', phone='+34 600 800 001')
        cls.server.sql("UPDATE centers SET stripe_account_id='acct_viajes8',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.center.user['center_id'],))
        cls.diver = t.make_diver('viajero8')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.stripe.stop()

    def test_price_times_participants_and_spots(self):
        offer = self.server.sql('SELECT id FROM travel_offers LIMIT 1')[0]['id']
        r = self.center.post('/api/travel-experiences', {'travel_offer_id': offer, 'title': 'Vida a bordo 8', 'price': 450, 'spots_total': 6})
        self.assertEqual(r.status, 200, r)
        eid = r.json['id']
        self.server.sql("UPDATE travel_experiences SET status='published',active=1,spots_available=6 WHERE id=?", (eid,))
        self.assertEqual(self.diver.post('/api/experience-bookings', {'travel_experience_id': eid, 'participants': 7}).status, 400)   # more than the spots
        r = self.diver.post('/api/experience-bookings', {'travel_experience_id': eid, 'participants': 3})
        self.assertEqual(r.status, 200, r)
        ebid = r.json['id']
        self.assertEqual(self.server.sql('SELECT spots_available FROM travel_experiences WHERE id=?', (eid,))[0]['spots_available'], 3)
        # Not payable before the organiser accepts
        self.assertEqual(self.diver.post('/api/payments/checkout', {'experience_booking_id': ebid}).status, 400)
        self.assertEqual(self.center.post('/api/provider/experience-bookings/status', {'id': ebid, 'status': 'confirmed'}).status, 200)
        r = self.diver.post('/api/payments/checkout', {'experience_booking_id': ebid})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.stripe.last_session()['amount_total'], 450 * 3 * 100)
        # Another diver cannot pay it
        self.assertEqual(self.make_diver('intruso8').post('/api/payments/checkout', {'experience_booking_id': ebid}).status, 403)


if __name__ == '__main__':
    unittest.main()
