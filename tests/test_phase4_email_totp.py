"""Fase 4 (v50.35): email (file spool in development, 48 h / 24 h reminders, document expiry, booking change,
commercial emails with one-click unsubscribe) and two-step verification (optional for all, mandatory for admins)."""
import os
import subprocess
import sys
import time
import unittest
from pathlib import Path

from helpers import ServerTestCase, Server, Client, ROOT

sys.path.insert(0, str(ROOT / 'app'))
from wod import totp  # noqa: E402


def code_for(secret, offset=0):
    return totp.code_at(secret, totp.current_step() + offset)


class TwoStep(ServerTestCase):
    def test_optional_totp_for_a_diver(self):
        d = self.make_diver('totp1')
        self.assertEqual(d.post('/api/account/totp/setup', {'password': 'mala'}).status, 403)
        r = d.post('/api/account/totp/setup', {'password': 'buceo-seguro-2026'})
        self.assertEqual(r.status, 200, r)
        secret = r.json['secret']
        self.assertTrue(r.json['uri'].startswith('otpauth://totp/'))
        self.assertIn('<svg', r.json['qr_svg'])
        self.assertEqual(d.post('/api/account/totp/enable', {'code': '000000' if code_for(secret) != '000000' else '111111'}).status, 400)
        r = d.post('/api/account/totp/enable', {'code': code_for(secret)})
        self.assertEqual(r.status, 200, r)
        rec = r.json['recovery_codes']
        self.assertEqual(len(rec), 8)
        self.assertTrue(d.me()['security']['totp_enabled'])
        row = self.server.sql("SELECT totp_recovery FROM users WHERE username='diver_totp1'")[0]
        self.assertNotIn(rec[0], row['totp_recovery'])  # only hashes are stored
        c = self.client()
        r = c.login('diver_totp1')
        self.assertEqual((r.status, r.json.get('totp_required')), (200, True))
        self.assertFalse(c.me().get('authenticated'))
        self.assertEqual(c.post('/api/auth/login', {'login': 'diver_totp1', 'password': 'buceo-seguro-2026', 'totp_code': '12345'}).status, 401)
        # The code of the current step was already used when enabling: wait for the next one.
        nxt = totp.current_step() + 1
        time.sleep(max(0, nxt * totp.STEP - time.time()) + 0.2)
        good = totp.code_at(secret, nxt)
        self.assertEqual(c.post('/api/auth/login', {'login': 'diver_totp1', 'password': 'buceo-seguro-2026', 'totp_code': good}).status, 200)
        self.assertTrue(c.me()['authenticated'])
        c2 = self.client()
        self.assertEqual(c2.post('/api/auth/login', {'login': 'diver_totp1', 'password': 'buceo-seguro-2026', 'totp_code': good}).status, 401)  # replay refused
        self.assertEqual(c2.post('/api/auth/login', {'login': 'diver_totp1', 'password': 'buceo-seguro-2026', 'totp_code': rec[0]}).status, 200)
        c3 = self.client()
        self.assertEqual(c3.post('/api/auth/login', {'login': 'diver_totp1', 'password': 'buceo-seguro-2026', 'totp_code': rec[0]}).status, 401)  # recovery codes work once
        self.assertEqual(c2.me()['security']['recovery_left'], 7)
        self.assertEqual(c2.post('/api/account/totp/disable', {'password': 'buceo-seguro-2026', 'code': rec[1]}).status, 200)
        self.assertFalse(c2.me()['security']['totp_enabled'])


class AdminNeedsTotp(unittest.TestCase):
    def test_admin_works_only_with_totp(self):
        s = Server({'WOD_ADMIN_TOTP_REQUIRED': '1'}).start()
        try:
            res = s.run_cli('--create-admin', '--email', 'a@worldives.test', '--username', 'admin', '--name', 'Admin', env={'WOD_ADMIN_PASSWORD': 'admin-seguro-2026'})
            self.assertEqual(res.returncode, 0, res.stderr)
            a = Client(s)
            r = a.login('admin', 'admin-seguro-2026')
            self.assertEqual((r.status, r.json.get('totp_setup_required')), (200, True))
            self.assertTrue(a.me()['security']['totp_setup_required'])
            blocked = a.get('/api/admin/payments')
            self.assertEqual(blocked.status, 403)
            self.assertIn('verificación en dos pasos', blocked.json['error'])
            secret = a.post('/api/account/totp/setup', {'password': 'admin-seguro-2026'}).json['secret']
            rec = a.post('/api/account/totp/enable', {'code': code_for(secret)}).json['recovery_codes']
            self.assertEqual(a.get('/api/admin/payments').status, 200)
            self.assertEqual(a.post('/api/account/totp/disable', {'password': 'admin-seguro-2026', 'code': rec[0]}).status, 403)
        finally:
            s.stop()

    def test_production_refuses_admins_without_totp(self):
        env = dict(os.environ, WOD_ENV='production', WOD_PUBLIC_URL='https://worldives.example.org', WOD_SECRET_KEY='y' * 40, WOD_ADMIN_TOTP_REQUIRED='0',
                   WOD_DB_PATH=str(Path(Server().tmp) / 'x.sqlite3'))
        r = subprocess.run([sys.executable, str(ROOT / 'app' / 'server.py')], env=env, capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 2)
        self.assertIn('WOD_ADMIN_TOTP_REQUIRED', r.stdout)


class Emails(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'correo', phone='+34 600 000 041')
        cls.cid = cls.center.user['center_id']

    def run_jobs(self, at_iso):
        """Runs the hourly email jobs at a given moment, on the test copy of the database."""
        code = ('import sys; sys.path.insert(0, %r); import server, datetime; db=server.connect(); '
                'server.run_email_jobs(db, datetime.datetime.fromisoformat(%r)); db.close()') % (str(ROOT / 'app'), at_iso)
        r = subprocess.run([sys.executable, '-c', code], env=self.server.env, cwd=str(self.server.tmp), capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stderr)

    def test_development_writes_emails_to_files(self):
        self.make_diver('archivo')
        folder = Path(self.server.env['WOD_MAIL_FILE_DIR'])
        end = time.time() + 15
        while time.time() < end and not list(folder.glob('*verify_email*archivo*.eml')): time.sleep(0.5)
        files = list(folder.glob('*verify_email*archivo*.eml'))
        self.assertTrue(files)
        self.assertIn(b'Subject:', files[0].read_bytes())
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE delivery='file' AND to_email='archivo@diver.example.org'"))

    def test_reminders_48h_and_24h(self):
        r = self.center.post('/api/provider-services', {'title': 'Salida', 'price': 30, 'booking_mode': 'request'})
        sid = r.json['id']
        slot = self.center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-03-12', 'slot_time': '09:00', 'spots_total': 6}).json['slot_id']
        # v50.47: with the centre's day-before notice on, the reminder of a departure goes through the notice queue
        # (WhatsApp, email and app, at the centre's hour: tests/test_v50_47_avisos.py). Here the classic email is tested.
        self.assertEqual(self.center.post('/api/avisos/ajustes', {'reminder_enabled': False}).status, 200)
        d = self.make_diver('recordatorio')
        bid = d.post('/api/bookings', {'center_id': self.cid, 'service_id': sid, 'slot_id': slot, 'participants': 1}).json['id']
        self.center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})
        self.server.sql("UPDATE bookings SET created_at='2031-03-01T10:00:00+00:00' WHERE id=?", (bid,))
        self.run_jobs('2031-03-10T10:00:00')
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='reminder_48h' AND related_id=?", (bid,)))
        self.assertFalse(self.server.sql("SELECT 1 FROM email_outbox WHERE template='reminder' AND related_id=?", (bid,)))
        self.run_jobs('2031-03-11T10:00:00')
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='reminder' AND related_id=?", (bid,)))
        self.run_jobs('2031-03-11T11:00:00')
        self.assertEqual(len(self.server.sql("SELECT 1 FROM email_outbox WHERE template IN ('reminder','reminder_48h') AND related_id=?", (bid,))), 2)  # once each

    def test_document_expiry_alerts(self):
        d = self.make_diver('caduca')
        r = d.upload('/api/account/documents', {'document_type': 'Seguro', 'title': 'Seguro DAN', 'expires_at': '2031-04-30'}, 'seguro.pdf', b'%PDF-1.4\n%test\n%%EOF\n')
        self.assertEqual(r.status, 200, r)
        self.run_jobs('2031-04-05T10:00:00')  # 25 days before → 30-day alert
        self.run_jobs('2031-04-06T10:00:00')  # nothing new
        self.run_jobs('2031-04-25T10:00:00')  # 5 days before → 7-day alert
        self.run_jobs('2031-05-01T10:00:00')  # expired
        rows = self.server.sql("SELECT template FROM email_outbox WHERE to_email='caduca@diver.example.org' AND template LIKE 'document_%' ORDER BY id")
        self.assertEqual([r['template'] for r in rows], ['document_expiring', 'document_expiring', 'document_expired'])

    def test_booking_change_by_the_provider(self):
        sid = self.center.post('/api/provider-services', {'title': 'Doble', 'price': 30, 'booking_mode': 'request'}).json['id']
        s1 = self.center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-07-01', 'slot_time': '09:00', 'spots_total': 4}).json['slot_id']
        s2 = self.center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-07-02', 'slot_time': '11:00', 'spots_total': 4}).json['slot_id']
        d = self.make_diver('cambio')
        bid = d.post('/api/bookings', {'center_id': self.cid, 'service_id': sid, 'slot_id': s1, 'participants': 2}).json['id']
        self.center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})
        self.assertEqual(d.post(f'/api/bookings/{bid}/reschedule', {'slot_id': s2}).status, 403)
        other = self.make_center(self.admin, 'ajeno', phone='+34 600 000 042')
        self.assertEqual(other.post(f'/api/bookings/{bid}/reschedule', {'slot_id': s2}).status, 404)  # v50.47 (B.3): what belongs to another centre does not exist (404)
        r = self.center.post(f'/api/bookings/{bid}/reschedule', {'slot_id': s2, 'reason': 'mar de fondo'})
        self.assertEqual(r.status, 200, r)
        b = self.server.sql('SELECT booking_date,booking_time,slot_id FROM bookings WHERE id=?', (bid,))[0]
        self.assertEqual((b['booking_date'], b['booking_time'], b['slot_id']), ('2031-07-02', '11:00', s2))
        spots = {r['id']: r['spots_available'] for r in self.server.sql('SELECT id,spots_available FROM service_slots WHERE id IN (?,?)', (s1, s2))}
        self.assertEqual(spots, {s1: 4, s2: 2})
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='booking_changed' AND related_id=?", (bid,)))

    def test_commercial_emails_only_with_consent_and_one_click_unsubscribe(self):
        yes = self.make_diver('mktsi')
        no = self.make_diver('mktno')
        yes.post('/api/account/marketing', {'consent': True})
        self.server.sql("UPDATE users SET email_verified_at='2026-01-01' WHERE username IN ('diver_mktsi','diver_mktno')")
        self.assertEqual(yes.post('/api/admin/marketing/send', {'subject': 'x', 'body': 'y'}).status, 403)
        r = self.admin.post('/api/admin/marketing/send', {'subject': 'Ofertas de otoño', 'body': 'Nuevas salidas.', 'url': '#/experiencias'})
        self.assertEqual(r.status, 200, r)
        rows = self.server.sql("SELECT to_email,unsubscribe_url,html FROM email_outbox WHERE template='marketing'")
        emails = {x['to_email'] for x in rows}
        self.assertIn('mktsi@diver.example.org', emails)
        self.assertNotIn('mktno@diver.example.org', emails)
        row = [x for x in rows if x['to_email'] == 'mktsi@diver.example.org'][0]
        self.assertIn('#/baja?t=', row['html'])
        path = row['unsubscribe_url'].split(self.server.base, 1)[1]
        # The mail client posts «List-Unsubscribe=One-Click» without session nor Origin (RFC 8058).
        r = Client(self.server, origin=None).request('POST', path, raw=b'List-Unsubscribe=One-Click', content_type='application/x-www-form-urlencoded')
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.server.sql("SELECT marketing_consent FROM users WHERE username='diver_mktsi'")[0]['marketing_consent'], 0)
        self.assertEqual(Client(self.server, origin=None).request('POST', '/api/marketing/unsubscribe?t=nonvalidtoken123456', raw=b'').status, 404)
        self.assertTrue(self.server.sql("SELECT 1 FROM consent_log WHERE kind='marketing' AND granted=0"))


if __name__ == '__main__':
    unittest.main(verbosity=2)
