"""Encargo 2, punto 7 (v50.39): simpler sign-up and sign-in. The sign-up asks only for what each type of account needs
(no user name: it is made from the email); a professional gives a qualification; a centre gives its country and city
and stays pending approval (Fase 1, G2); the email is verified with a link; the second step of the sign-in stays a
separate request."""
import re
import sys
import unittest

from helpers import ServerTestCase, ROOT
sys.path.insert(0, str(ROOT / 'app'))
from wod import totp  # noqa: E402

PW = 'buceo-seguro-2026'


class SignUp(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = cls('run').make_admin()

    def reg(self, **data):
        base = {'password': PW, 'accept_terms': True, 'lang': 'es'}
        base.update(data)
        return self.client().post('/api/auth/register', base)

    def user(self, email):
        return self.server.sql('SELECT u.*, p.country, p.city, p.phone, p.certification_id FROM users u LEFT JOIN user_profiles p ON p.user_id=u.id WHERE u.email=?', (email,))[0]

    def test_diver_needs_only_name_email_password(self):
        r = self.reg(fullname='Lucía Mar', email='lucia.mar@example.org', account_type='recreational')
        self.assertEqual(r.status, 200, r)
        u = self.user('lucia.mar@example.org')
        self.assertEqual((u['role'], u['username']), ('recreational', 'lucia.mar'))
        self.assertIsNone(u['email_verified_at'])
        mail = self.server.sql("SELECT text FROM email_outbox WHERE template='verify_email' AND to_email='lucia.mar@example.org'")
        self.assertEqual(len(mail), 1)
        self.assertIn('verificar-email?token=', mail[0]['text'])
        # Same local part, other domain: the user name is still unique
        self.assertEqual(self.reg(fullname='Lucía Otra', email='lucia.mar@example.net', account_type='recreational').status, 200)
        self.assertEqual(self.user('lucia.mar@example.net')['username'], 'lucia.mar2')
        # The sign-in works with the email
        self.assertEqual(self.client().login('lucia.mar@example.org').status, 200)
        # Bad data
        self.assertEqual(self.reg(fullname='X', email='no-es-email', account_type='recreational').status, 400)
        self.assertEqual(self.reg(fullname='X', email='x@example.org', account_type='recreational', password='corta').status, 400)
        self.assertEqual(self.reg(fullname='X', email='y@example.org', account_type='recreational', accept_terms=False).status, 400)
        self.assertEqual(self.reg(fullname='Repetida', email='lucia.mar@example.org', account_type='recreational').status, 400)

    def test_centre_pending_with_country_and_city(self):
        r = self.reg(fullname='Marta Gerente', email='marta@centro-azul.example.org', account_type='center', center_name='Centro Azul',
                     phone='+34 600 123 456', country='Portugal', city='Sagres', accept_pro_terms=True)
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['provider_verification'], 'pending')
        u = self.user('marta@centro-azul.example.org')
        self.assertEqual((u['role'], u['requested_role'], u['country'], u['city']), ('recreational', 'center', 'Portugal', 'Sagres'))
        draft = self.server.sql("SELECT c.active, c.country, c.city FROM center_claims cl JOIN centers c ON c.id=cl.center_id WHERE cl.user_id=?", (u['id'],))[0]
        self.assertEqual((draft['active'], draft['country'], draft['city']), (0, 'Portugal', 'Sagres'))
        # Without the conditions for centres, the name of the centre or the phone: refused
        for missing in ({'accept_pro_terms': False}, {'center_name': ''}, {'phone': ''}):
            data = dict(fullname='Otro', email=f'otro{len(missing)}{list(missing)[0]}@c.example.org', account_type='center', center_name='C', phone='+34 600 000 000',
                        country='España', city='Xàbia', accept_pro_terms=True)
            data.update(missing)
            self.assertEqual(self.reg(**data).status, 400, missing)

    def test_professional_gives_a_qualification(self):
        base = dict(fullname='Iván Guía', account_type='freelance', phone='+34 611 111 111', accept_pro_terms=True)
        self.assertEqual(self.reg(email='ivan1@pro.example.org', **base).status, 400)   # no qualification
        cid = self.server.sql('SELECT id FROM certifications WHERE active=1 LIMIT 1')[0]['id']
        self.assertEqual(self.reg(email='ivan2@pro.example.org', certification_id=cid, **base).status, 200)
        self.assertEqual(self.user('ivan2@pro.example.org')['certification_id'], cid)
        self.assertEqual(self.reg(email='ivan3@pro.example.org', certification_text='Instructor SSI Open Water', **base).status, 200)
        note = self.server.sql("SELECT note FROM center_claims WHERE email='ivan3@pro.example.org'")[0]['note']
        self.assertIn('Instructor SSI Open Water', note)   # the administration sees it when verifying
        self.assertEqual(self.reg(email='ivan4@pro.example.org', certification_id=999999, **base).status, 400)   # unknown id, no text

    def test_nobody_becomes_admin_or_centre_by_signing_up(self):
        self.assertEqual(self.reg(fullname='A', email='a@example.org', account_type='admin').status, 403)
        r = self.reg(fullname='B', email='b@centro.example.org', account_type='center', center_name='B', phone='+34 600 000 001', country='España', city='Dénia', accept_pro_terms=True)
        self.assertEqual(r.json['role'], 'recreational')


class SignIn(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = cls('run').make_admin()

    def test_second_step_is_a_separate_request(self):
        diver = self.make_diver('dospasos7')
        secret = diver.post('/api/account/totp/setup', {'password': PW}).json['secret']   # v50.51: stored encrypted
        r = diver.post('/api/account/totp/enable', {'code': totp.code_at(secret, totp.current_step())})
        self.assertEqual(r.status, 200, r)
        c = self.client()
        r = c.post('/api/auth/login', {'login': 'dospasos7@diver.example.org', 'password': PW})
        self.assertTrue(r.json.get('totp_required'))
        self.assertEqual(c.get('/api/me/area').status, 403)          # not signed in yet
        self.assertEqual(c.post('/api/auth/login', {'login': 'dospasos7@diver.example.org', 'password': PW, 'totp_code': '000000'}).status, 401)
        self.server.sql("UPDATE users SET totp_last_step=NULL WHERE username='diver_dospasos7'")
        r = c.post('/api/auth/login', {'login': 'dospasos7@diver.example.org', 'password': PW, 'totp_code': totp.code_at(secret, totp.current_step() + 1)})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(c.get('/api/me/area').status, 200)

    def test_forgotten_password_does_not_reveal_accounts(self):
        self.make_diver('olvido7')
        a = self.client().post('/api/auth/forgot', {'email': 'olvido7@diver.example.org'}).json
        b = self.client().post('/api/auth/forgot', {'email': 'no-existe7@diver.example.org'}).json
        self.assertEqual(a, b)
        self.assertTrue(re.search(r'restablecer\?token=', self.server.sql("SELECT text FROM email_outbox WHERE template='password_reset' AND to_email='olvido7@diver.example.org'")[0]['text']))


if __name__ == '__main__':
    unittest.main()
