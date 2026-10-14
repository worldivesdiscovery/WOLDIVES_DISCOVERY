"""v50.52 · ASVS 5.0 V6.3.3 (decision of the owner, 14/10/2026): two-step verification is mandatory for whoever can move
money or see payment data. Centres and freelance with online payments (Stripe Connect connected or being set up) and
the team members of those centres with «Cobros»; without it, only «Mi cuenta». Centres without online payments go on
without it, and the bookings and payments of the clients of a blocked centre go on working (Stripe webhooks)."""
import os
import re
import subprocess
import sys
import time
import unittest
from datetime import datetime, timedelta, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from helpers import Client, ServerTestCase  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from wod import totp as wtotp  # noqa: E402

CONNECT_SECRET = 'whsec_connect_2fa'
PAST = '2026-01-01T00:00:00+00:00'
PW = 'buceo-seguro-2026'


def totp_now(secret):
    return wtotp.code_at(secret, int(time.time()) // 30)


def wait_for(fn, seconds=15):
    end = time.time() + seconds
    while time.time() < end:
        v = fn()
        if v: return v
        time.sleep(0.3)
    return fn()


def provider_get_routes():
    """Every fixed GET route of the panels in app/server.py: centre, provider, team app, manifest, payments, bookings,
    agenda, notices and exports (the sweep of «por ninguna ruta»)."""
    src = (ROOT / 'app' / 'server.py').read_text(encoding='utf-8')
    paths = set(re.findall(r"path\s*==\s*'(/api/(?:center|provider|pro|manifest|payments|bookings|agenda|avisos|whatsapp|team|admin/planning)[^']*)'", src))
    return sorted(p for p in paths if '{' not in p)


class CobrosDosPasos(ServerTestCase):
    """V6.3.3: verificación en dos pasos obligatoria con cobros online o con el permiso «Cobros»."""

    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base, 'STRIPE_WEBHOOK_SECRET': 'whsec_plat_2fa',
                         'STRIPE_CONNECT_WEBHOOK_SECRET': CONNECT_SECRET, 'WOD_PAYMENTS_TOTP_REQUIRED': '1', 'WOD_MAINTENANCE_SECONDS': '2'}
        super().setUpClass()
        t = cls('run'); s = cls.server
        cls.admin = t.make_admin()
        # Centre A: online payments, the owner past the grace period, a manager (all permissions, «Cobros» included)
        # and an instructor (only «Pasar lista»).
        cls.a = t.make_center(cls.admin, 'cobra2fa', phone='+34 600 520 001')
        cls.cid = cls.a.user['center_id']
        s.sql("UPDATE centers SET stripe_account_id='acct_cobra',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.cid,))
        cls.sid = cls.a.post('/api/provider-services', {'title': 'Doble con pago', 'price': 60, 'booking_mode': 'payment'}).json['id']
        cls.slot = cls.a.post('/api/provider-services/slot', {'service_id': cls.sid, 'slot_date': '2031-06-10', 'slot_time': '09:00', 'spots_total': 10}).json['slot_id']
        cls.diver = t.make_diver('cliente2fa')
        r = cls.diver.post('/api/bookings', {'center_id': cls.cid, 'service_id': cls.sid, 'slot_id': cls.slot, 'participants': 1})
        assert r.status == 200, r
        cls.bid = r.json['id']
        s.sql("UPDATE bookings SET status='confirmed', payment_status='paid', amount_paid=60 WHERE id=?", (cls.bid,))
        cls.manager = cls.member(t, cls.cid, 'gerente2fa', 'manager')
        cls.instructor = cls.member(t, cls.cid, 'instr2fa', 'instructor')
        s.sql('UPDATE users SET totp_deadline=? WHERE id=?', (PAST, cls.a.user['id']))     # the 14 days are over
        # Centre B: no online payments.
        cls.b = t.make_center(cls.admin, 'sinpagos2fa', phone='+34 600 520 002')
        cls.b_manager = cls.member(t, cls.b.user['center_id'], 'gerenteb2fa', 'manager')
        # Freelance with online payments, past the grace period.
        cls.pro = t.make_freelance(cls.admin, 'libre2fa')
        s.sql("UPDATE users SET stripe_account_id='acct_libre',stripe_charges_enabled=1,stripe_payouts_enabled=1,totp_deadline=? WHERE id=?", (PAST, cls.pro.user['id']))

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.stripe.stop()

    @classmethod
    def member(cls, t, center_id, tag, role):
        c = t.make_diver(tag); uid = c.user['id']
        cls.server.sql("UPDATE users SET role='center',center_id=? WHERE id=?", (center_id, uid))
        cls.server.sql('INSERT OR REPLACE INTO center_members(center_id,user_id,member_role,created_at) VALUES(?,?,?,?)', (center_id, uid, role, '2026-01-01'))
        assert c.login(f'diver_{tag}').status == 200
        c.user = c.me()['user']
        return c

    def enable_totp(self, c):
        r = c.post('/api/account/totp/setup', {'password': PW})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(c.post('/api/account/totp/enable', {'code': totp_now(r.json['secret'])}).status, 200)
        self.server.sql('UPDATE users SET totp_last_step=NULL WHERE id=?', (c.user['id'],))
        return r.json['secret']

    def assert_sees_nothing(self, c, who):
        """No booking, client, payment or export of the centre by any route (the client's email is the marker)."""
        marker = 'cliente2fa@diver.example.org'
        routes = provider_get_routes() + [f'/api/bookings/{self.bid}', f'/api/bookings/{self.bid}/receipt.pdf', f'/api/manifest/{self.slot}',
                                          f'/api/manifest/day?date=2031-06-10', '/api/center/export?kind=bookings', '/api/center/export?kind=clients',
                                          '/api/center/export?kind=payments', '/api/center/export?kind=services', '/api/bookings?scope=center']
        self.assertGreater(len(routes), 40, routes)
        opened = []
        for path in routes:
            r = c.get(path)
            body = r.body.decode('utf-8', 'replace') if isinstance(r.body, bytes) else str(r.body)
            self.assertNotIn(marker, body, f'{who}: {path} enseña datos del cliente')
            self.assertNotIn('Cliente2fa', body, f'{who}: {path}')
            if r.status == 200 and path.startswith(('/api/center/', '/api/provider/payments', '/api/payments/center', '/api/bookings', '/api/manifest')): opened.append(path)
        self.assertEqual(opened, [], f'{who}: rutas del panel abiertas sin la verificación en dos pasos')

    # --------------------------------------------------------------------------------------------- the four of the brief
    def test_v6_3_3_centre_with_stripe_and_without_2fa_sees_no_bookings_clients_payments_or_exports(self):
        self.assert_sees_nothing(self.a, 'propietario')
        me = self.a.me()
        self.assertTrue(me['security']['totp_setup_required']); self.assertTrue(me['security']['totp_blocked'])
        self.assertEqual(me['security']['totp_required'], 'pagos')
        # «Mi cuenta» still works: its sessions and turning the verification on
        self.assertEqual(self.a.get('/api/account/sessions').status, 200)
        r = self.a.post('/api/bookings/%d/status' % self.bid, {'status': 'cancelled'})
        self.assertIn(r.status, (401, 403), r)
        self.assertTrue(wait_for(lambda: self.server.sql("SELECT 1 FROM audit_log WHERE action='security_alert' AND entity_type='totp_required_block' AND user_id=?", (self.a.user['id'],))))
        # The same routes for a person of the same centre for whom it is not mandatory: the bookings are there
        bk = self.instructor.get('/api/bookings')
        self.assertEqual(bk.status, 200, bk); self.assertIn('cliente2fa', bk.body.decode('utf-8', 'replace').lower())

    def test_v6_3_3_member_with_cobros_without_2fa_the_same(self):
        self.assert_sees_nothing(self.manager, 'encargado con «Cobros»')
        me = self.manager.me()
        self.assertEqual(me['security']['totp_required'], 'cobros'); self.assertTrue(me['security']['totp_blocked'])
        self.assertIsNone(me['security']['totp_deadline'])                    # no grace period for a member
        self.assertIsNone(self.instructor.me()['security']['totp_required'])    # without «Cobros» it stays optional
        self.assertEqual(self.instructor.get('/api/pro/hoy').status, 200)

    def test_v6_3_3_centre_without_online_payments_enters_without_it(self):
        for c in (self.b, self.b_manager):
            me = c.me()
            self.assertIsNone(me['security']['totp_required']); self.assertFalse(me['security']['totp_setup_required'])
            self.assertEqual(c.get('/api/bookings').status, 200)
            self.assertEqual(c.get('/api/center/clients').status, 200)
            self.assertEqual(c.get('/api/provider/payments').status, 200)

    def test_v6_3_3_payments_of_a_blocked_centre_still_confirm(self):
        diver = self.make_diver('pagabloq')
        r = diver.post('/api/bookings', {'center_id': self.cid, 'service_id': self.sid, 'slot_id': self.slot, 'participants': 2})
        self.assertEqual(r.status, 200, r)
        bid = r.json['id']
        sess = self.stripe.last_session(); self.stripe.pay(sess['id'])
        ev = {'id': f'evt_{time.time_ns()}', 'type': 'checkout.session.completed', 'account': 'acct_cobra',
              'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
        payload, sig = StripeMock.signed(ev, CONNECT_SECRET)
        w = Client(self.server, origin=None).request('POST', '/api/payments/webhook/connect', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
        self.assertEqual(w.status, 200, w)
        row = self.server.sql('SELECT status, payment_status FROM bookings WHERE id=?', (bid,))[0]
        self.assertEqual((row['status'], row['payment_status']), ('confirmed', 'paid'))
        self.assertEqual(diver.get(f'/api/bookings/{bid}').status, 200)      # the client sees their booking
        self.assertTrue(self.a.me()['security']['totp_blocked'])             # and the centre is still blocked

    # --------------------------------------------------------------------------------------------- how it behaves
    def test_v6_3_3_grace_period_of_14_days_with_panel_notice_and_email(self):
        c = self.make_center(self.admin, 'plazo2fa', phone='+34 600 520 003')
        self.server.sql("UPDATE centers SET stripe_account_id='acct_plazo' WHERE id=?", (c.user['center_id'],))   # being set up counts
        me = c.me()['security']
        self.assertEqual(me['totp_required'], 'pagos'); self.assertFalse(me['totp_blocked']); self.assertFalse(me['totp_setup_required'])
        days = (datetime.fromisoformat(me['totp_deadline']) - datetime.now(timezone.utc)).days
        self.assertIn(days, (13, 14), me['totp_deadline'])
        self.assertEqual(c.get('/api/bookings').status, 200)                                     # it works during the 14 days
        mails = self.server.sql("SELECT subject FROM email_outbox WHERE template='totp_required_payments' AND to_email='plazo2fa@centro-plazo2fa.example.org'")
        self.assertEqual(len(mails), 1, mails); self.assertIn('verificación en dos pasos', mails[0]['subject'])
        self.assertTrue(self.server.sql("SELECT 1 FROM audit_log WHERE action='totp_deadline_set' AND user_id=?", (c.user['id'],)))
        c.me(); self.assertEqual(len(self.server.sql("SELECT 1 FROM email_outbox WHERE template='totp_required_payments' AND to_email='plazo2fa@centro-plazo2fa.example.org'")), 1)
        self.server.sql('UPDATE users SET totp_deadline=? WHERE id=?', (PAST, c.user['id']))      # the 14 days are over
        self.assertEqual(c.get('/api/bookings').status, 403)
        self.enable_totp(c)                                                                       # allowed while blocked
        self.assertEqual(c.get('/api/bookings').status, 200)
        self.assertFalse(c.me()['security']['totp_setup_required'])

    def test_v6_3_3_the_email_goes_out_without_signing_in(self):
        c = self.make_center(self.admin, 'sinentrar2fa', phone='+34 600 520 004')
        self.server.sql("UPDATE centers SET stripe_account_id='acct_sinentrar' WHERE id=?", (c.user['center_id'],))
        self.assertTrue(wait_for(lambda: self.server.sql("SELECT 1 FROM email_outbox WHERE template='totp_required_payments' AND to_email='sinentrar2fa@centro-sinentrar2fa.example.org'"), 20))
        self.assertTrue(self.server.sql('SELECT totp_deadline FROM users WHERE id=?', (c.user['id'],))[0]['totp_deadline'])

    def test_v6_3_3_stripe_is_not_connected_without_it(self):
        c = self.make_center(self.admin, 'conecta2fa', phone='+34 600 520 005')
        before = len([x for x in self.stripe.calls if x['path'] == '/v1/accounts' and x['method'] == 'POST'])
        r = c.post('/api/payments/connect/onboard', {})
        self.assertEqual(r.status, 403, r); self.assertTrue(r.json.get('totp_required'))
        self.assertEqual(len([x for x in self.stripe.calls if x['path'] == '/v1/accounts' and x['method'] == 'POST']), before)
        self.assertFalse(self.server.sql('SELECT stripe_account_id FROM centers WHERE id=?', (c.user['center_id'],))[0]['stripe_account_id'])
        self.enable_totp(c)
        r = c.post('/api/payments/connect/onboard', {})
        self.assertEqual(r.status, 200, r)

    def test_v6_3_3_cannot_be_turned_off_with_payments_or_cobros(self):
        c = self.make_center(self.admin, 'apagar2fa', phone='+34 600 520 006')
        secret = self.enable_totp(c)
        self.server.sql("UPDATE centers SET stripe_account_id='acct_apagar' WHERE id=?", (c.user['center_id'],))
        r = c.post('/api/account/totp/disable', {'password': PW, 'code': totp_now(secret)})
        self.assertEqual(r.status, 403, r); self.assertIn('cobros', r.json['error'])
        self.assertTrue(self.server.sql('SELECT totp_enabled FROM users WHERE id=?', (c.user['id'],))[0]['totp_enabled'])
        self.assertTrue(wait_for(lambda: self.server.sql("SELECT 1 FROM audit_log WHERE action='security_alert' AND entity_type='totp_disable_refused' AND user_id=?", (c.user['id'],))))
        # without online payments it can be turned off, as before
        d = self.make_center(self.admin, 'apagarb2fa', phone='+34 600 520 007')
        secret = self.enable_totp(d)
        self.server.sql('UPDATE users SET totp_last_step=NULL WHERE id=?', (d.user['id'],))
        self.assertEqual(d.post('/api/account/totp/disable', {'password': PW, 'code': totp_now(secret)}).status, 200)
        self.assertTrue(self.server.sql("SELECT 1 FROM audit_log WHERE action IN ('totp_enabled') AND user_id=?", (d.user['id'],)))
        self.assertTrue(self.server.sql("SELECT 1 FROM audit_log WHERE action='totp_disabled' AND user_id=?", (d.user['id'],)))

    def test_v6_3_3_giving_cobros_asks_for_it_at_the_next_sign_in(self):
        owner = self.make_center(self.admin, 'equipo2fa', phone='+34 600 520 008')
        self.enable_totp(owner)
        cid = owner.user['center_id']
        self.server.sql("UPDATE centers SET stripe_account_id='acct_equipo' WHERE id=?", (cid,))
        rec = self.member(self, cid, 'recep2fa', 'reception')                  # «Recepción»: without «Cobros» by default
        self.assertEqual(rec.get('/api/bookings').status, 200)
        perms = [p for p in owner.get('/api/center/team').json['role_list'] if p['key'] == 'reception'][0]['permissions']
        self.assertNotIn('cobros', perms)
        r = owner.post('/api/center/team/roles/save', {'key': 'reception', 'permissions': perms + ['cobros']})
        self.assertEqual(r.status, 200, r)
        login = self.client().post('/api/auth/login', {'login': 'diver_recep2fa', 'password': PW})
        self.assertEqual(login.status, 200, login); self.assertTrue(login.json['totp_setup_required'])
        self.assertEqual(rec.get('/api/bookings').status, 403)
        self.assertEqual(rec.get('/api/payments/center').status, 403)

    def test_v6_3_3_freelance_with_online_payments(self):
        self.assertEqual(self.pro.get('/api/provider/payments').status, 403)
        self.assertEqual(self.pro.get('/api/bookings').status, 403)
        me = self.pro.me()
        self.assertEqual(me['security']['totp_required'], 'pagos'); self.assertTrue(me['security']['totp_blocked'])

    def test_v6_3_3_status_row_and_production_refuses_turning_it_off(self):
        rows = {r['key']: r for r in self.admin.get('/api/admin/health').json['services']}
        self.assertEqual(rows['payments_2fa']['state'], 'ok')
        env = dict(os.environ, WOD_ENV='production', WOD_PUBLIC_URL='https://worlddivesdiscovery.example.org', WOD_SECRET_KEY='y' * 40,
                   WOD_DATA_KEY='z' * 40, WOD_PAYMENTS_TOTP_REQUIRED='0', WOD_NO_ENV_FILE='1', WOD_PORT='1',
                   WOD_DB_PATH=str(self.server.tmp / 'prod.sqlite3'), WOD_LOG_DIR=str(self.server.tmp), WOD_STORAGE_DIR=str(self.server.tmp))
        env.pop('WOD_DEMO_MODE', None)
        r = subprocess.run([sys.executable, str(ROOT / 'app' / 'server.py')], env=env, capture_output=True, text=True, timeout=60)
        self.assertNotEqual(r.returncode, 0); self.assertIn('WOD_PAYMENTS_TOTP_REQUIRED=0', r.stdout + r.stderr)


if __name__ == '__main__':
    unittest.main()
