"""Fase 1 (v50.31): security fixes G1-G12 and points 13-16, with cross-role permission checks."""
import re
import time
import unittest

from helpers import ServerTestCase, Client, PDF_BYTES, PNG_BYTES


class Phase1Security(ServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center_a = t.make_center(cls.admin, 'alfa')
        cls.center_b = t.make_center(cls.admin, 'beta', phone='+34 600 333 444')
        cls.pro = t.make_freelance(cls.admin, 'gamma')
        cls.diver = t.make_diver('ana')
        cls.diver2 = t.make_diver('luis')

    # ------------------------------------------------------------------ G2
    def test_g2_register_never_grants_center_role(self):
        c = self.client()
        # Same phone as an existing centre: only a suggestion for the administrator.
        phone = self.server.sql('SELECT phone FROM centers WHERE active=1 AND phone IS NOT NULL LIMIT 1')[0]['phone']
        r = c.register('Intruso', 'intruso@evil.example.org', 'intruso', account_type='center', center_name='Centro Robado', phone=phone)
        self.assertEqual(r.status, 200, r)
        me = c.me()['user']
        self.assertEqual(me['role'], 'recreational')
        self.assertIsNone(me['center_id'])
        self.assertEqual(c.get('/api/center/analytics').status, 403)
        claim = self.server.sql("SELECT * FROM center_claims WHERE email='intruso@evil.example.org'")[0]
        self.assertIsNotNone(claim['suggested_center_id'])
        self.assertNotEqual(claim['center_id'], claim['suggested_center_id'])
        draft = self.server.sql('SELECT active,verification_status FROM centers WHERE id=?', (claim['center_id'],))[0]
        self.assertEqual(draft['active'], 0)
        # Approval needs a verification method and a note.
        r = self.admin.post('/api/admin/center-claims/review', {'id': claim['id'], 'decision': 'approve'})
        self.assertEqual(r.status, 400)
        r = self.admin.post('/api/admin/center-claims/review', {'id': claim['id'], 'decision': 'reject', 'verification_method': 'phone_call', 'verification_note': 'el centro no conoce a esta persona'})
        self.assertEqual(r.status, 200)

    def test_g2_admin_role_cannot_be_requested(self):
        r = self.client().register('X', 'x-admin@example.org', 'xadmin', account_type='admin')
        self.assertEqual(r.status, 403)

    def test_g2_freelance_needs_approval(self):
        c = self.client()
        c.register('Libre', 'libre@pro.example.org', 'libre1', account_type='freelance', phone='+34 699 000 111')
        self.assertEqual(c.me()['user']['role'], 'recreational')
        self.assertEqual(c.get('/api/provider/experiences').status, 403)

    # ------------------------------------------------------------------ G1 / G8
    def test_g1_documents_access(self):
        d = self.make_diver('docs1')
        r = d.upload('/api/account/documents', {'document_type': 'Seguro', 'title': 'Seguro 2026'}, 'seguro.pdf', PDF_BYTES)
        self.assertEqual(r.status, 200, r)
        did = r.json['id']
        own = d.get(f'/api/documents/file/{did}')
        self.assertEqual(own.status, 200)
        self.assertIn('no-store', own.headers.get('Cache-Control'))
        self.assertIn('private', own.headers.get('Cache-Control'))
        self.assertIn('filename', own.headers.get('Content-Disposition', ''))
        # A centre without a booking from this diver: denied (G1).
        self.assertEqual(self.center_a.get(f'/api/documents/file/{did}').status, 403)
        # Another diver: denied.
        self.assertEqual(self.diver2.get(f'/api/documents/file/{did}').status, 403)
        # The administrator: allowed and logged.
        self.assertEqual(self.admin.get(f'/api/documents/file/{did}').status, 200)
        logged = self.server.sql("SELECT * FROM audit_log WHERE action='document_downloaded' AND entity_id=?", (did,))
        self.assertGreaterEqual(len(logged), 2)
        # The diver books with centre A himself -> centre A can see it; centre B still cannot.
        cid = self.center_a.user['center_id']
        r = d.post('/api/bookings', {'center_id': cid, 'booking_date': '2030-06-01', 'participants': 1})
        self.assertEqual(r.status, 200, r)
        bid = r.json['id']
        self.assertEqual(self.center_a.get(f'/api/documents/file/{did}').status, 200)
        self.assertEqual(self.center_b.get(f'/api/documents/file/{did}').status, 403)
        # Cancelled booking -> access gone.
        self.server.sql("UPDATE bookings SET status='cancelled' WHERE id=?", (bid,))
        self.assertEqual(self.center_a.get(f'/api/documents/file/{did}').status, 403)
        # Delete removes the file from disk.
        path = self.server.sql('SELECT file_path FROM user_documents WHERE id=?', (did,))[0]['file_path']
        full = self.server.tmp / 'storage' / path
        self.assertTrue(full.exists())
        self.assertEqual(d.post('/api/account/documents/delete', {'id': did}).status, 200)
        self.assertFalse(full.exists())

    def test_g1_real_file_type_and_size(self):
        d = self.diver
        r = d.upload('/api/account/documents', {'document_type': 'Seguro', 'title': 'falso'}, 'virus.pdf', b'MZ\x90\x00 not a pdf')
        self.assertEqual(r.status, 400)
        r = d.upload('/api/account/documents', {'document_type': 'Seguro', 'title': 'grande'}, 'g.pdf', b'%PDF-' + b'0' * (10 * 1024 * 1024 + 10))
        self.assertEqual(r.status, 400)
        r = d.upload('/api/account/documents', {'document_type': 'Titulación', 'title': 'png'}, 'x.png', PNG_BYTES)
        self.assertEqual(r.status, 200)

    # ------------------------------------------------------------------ G6
    def test_g6_no_medical_certificates(self):
        r = self.diver.upload('/api/account/documents', {'document_type': 'Certificado médico', 'title': 'apto'}, 'm.pdf', PDF_BYTES)
        self.assertEqual(r.status, 400)
        self.assertIn('médicos', r.json['error'])

    # ------------------------------------------------------------------ G3
    def test_g3_virtual_urls(self):
        pid = self.server.sql('SELECT id FROM dive_points WHERE active=1 LIMIT 1')[0]['id']
        for bad in ('javascript:alert(1)', 'http://www.youtube-nocookie.com/embed/x', 'https://evil.example.com/x', 'https://youtube-nocookie.com.evil.org/embed/x', 'data:text/html,hi'):
            r = self.admin.post(f'/api/dive-points/{pid}/virtual', {'title': 't', 'experience_type': 'video360', 'url': bad})
            self.assertEqual(r.status, 400, bad)
        r = self.admin.post(f'/api/dive-points/{pid}/virtual', {'title': 'ok', 'experience_type': 'video360', 'url': 'https://www.youtube-nocookie.com/embed/abc'})
        self.assertEqual(r.status, 200, r)
        # Old rows with a bad URL are never handed out.
        self.server.sql("INSERT INTO virtual_experiences(dive_point_id,title,experience_type,url,active,created_at,updated_at) VALUES(?,?,?,?,1,'x','x')", (pid, 'viejo', 'video360', 'javascript:alert(1)'))
        items = self.client().get(f'/api/dive-points/{pid}/virtual').json['items']
        self.assertFalse(any(i.get('url') and i['url'].startswith('javascript') for i in items))
        # Upload limit for virtual tours.
        try:
            r = self.admin.upload(f'/api/dive-points/{pid}/virtual/upload', {'title': 'big', 'experience_type': 'panorama'}, 'p.png', PNG_BYTES + b'0' * (16 * 1024 * 1024))
            self.assertIn(r.status, (400, 413))
        except OSError:
            pass  # the server refused the body before reading it (413 + connection closed)
        r = self.admin.upload(f'/api/dive-points/{pid}/virtual/upload', {'title': 'fake', 'experience_type': 'panorama'}, 'p.png', b'<svg onload=alert(1)>')
        self.assertEqual(r.status, 400)
        r = self.admin.upload(f'/api/dive-points/{pid}/virtual/upload', {'title': 'pano', 'experience_type': 'panorama'}, 'p.png', PNG_BYTES)
        self.assertEqual(r.status, 200, r)


    # ------------------------------------------------------------------ CSP / headers
    def test_csp_and_headers_everywhere(self):
        c = self.client()
        for path in ('/', '/api/health', '/assets/js/world-dives-v8.js'):
            r = c.get(path)
            self.assertIn("script-src 'self'", r.headers.get('Content-Security-Policy', ''), path)
            self.assertEqual(r.headers.get('X-Content-Type-Options'), 'nosniff')
        etag = c.get('/assets/css/world-dives-v8.css').headers.get('ETag')
        r = c.get('/assets/css/world-dives-v8.css', headers={'If-None-Match': etag})
        self.assertEqual(r.status, 304)
        self.assertIn('Content-Security-Policy', r.headers)
        index = c.get('/').body.decode()
        self.assertNotIn('unpkg.com', index)
        self.assertIsNone(re.search(r'<script>(?!</script>)', index))

    # ------------------------------------------------------------------ G4
    def test_g4_public_booking_needs_token(self):
        cid = self.center_a.user['center_id']
        bid = self.diver.post('/api/bookings', {'center_id': cid, 'booking_date': '2030-07-01'}).json['id']
        anon = self.client()
        self.assertEqual(anon.get(f'/api/public/bookings/{bid}').status, 404)
        self.assertEqual(anon.get(f'/api/public/bookings/{bid}?t=wrong').status, 404)
        token = self.server.sql('SELECT public_token FROM bookings WHERE id=?', (bid,))[0]['public_token']
        self.assertGreaterEqual(len(token), 30)
        r = anon.get(f'/api/public/bookings/{bid}?t={token}')
        self.assertEqual(r.status, 200)
        b = r.json['booking']
        self.assertNotIn('user_id', b)
        self.assertEqual(b['customer'], 'Buceador A.')
        self.assertEqual(self.diver.get(f'/api/public/bookings/{bid}').status, 200)
        self.assertEqual(self.center_b.get(f'/api/public/bookings/{bid}').status, 404)

    # ------------------------------------------------------------------ G5
    def test_g5_manual_booking_never_links_registered_account(self):
        svc = self.center_a.post('/api/provider-services', {'title': 'Inmersión guiada', 'price': 50, 'booking_mode': 'request'})
        self.assertEqual(svc.status, 200, svc)
        r = self.center_a.post('/api/center/bookings/manual', {'fullname': 'Ana', 'email': 'ana@diver.example.org', 'service_id': svc.json['id'], 'booking_date': '2030-08-01'})
        self.assertEqual(r.status, 200, r)
        b = self.server.sql('SELECT user_id,contact_email FROM bookings WHERE id=?', (r.json['id'],))[0]
        self.assertNotEqual(b['user_id'], self.diver.user['id'])
        self.assertEqual(b['contact_email'], 'ana@diver.example.org')
        det = self.center_a.get(f"/api/bookings/{r.json['id']}").json
        self.assertEqual(det['documents'], [])
        # API integration: same rule.
        key = self.center_a.post('/api/center/integration/regenerate').json['api_key']
        r2 = Client(self.server, origin=None).post('/api/integrations/bookings', {'email': 'ana@diver.example.org', 'booking_date': '2030-08-02', 'fullname': 'Ana'}, headers={'X-WORLDIVES-API-Key': key})
        self.assertEqual(r2.status, 200, r2)
        b2 = self.server.sql('SELECT user_id FROM bookings WHERE id=?', (r2.json['booking_id'],))[0]
        self.assertNotEqual(b2['user_id'], self.diver.user['id'])

    def test_g5_checkin_requires_consent(self):
        code = self.center_b.post('/api/qr/create', {'label': 'Recepción'}).json['code']
        d = self.make_diver('qr1')
        r = d.post(f'/api/checkin/{code}', {})
        self.assertEqual(r.status, 409)
        self.assertTrue(r.json['needs_consent'])
        self.assertEqual(d.post(f'/api/checkin/{code}', {'share_consent': True}).status, 200)
        self.assertEqual(len(d.get('/api/account/shares').json['items']), 1)
        cid = self.center_b.user['center_id']
        self.assertEqual(d.post('/api/account/shares/revoke', {'center_id': cid}).status, 200)
        self.assertEqual(len(d.get('/api/account/shares').json['items']), 0)

    # ------------------------------------------------------------------ G7
    def test_g7_body_limits(self):
        import http.client
        # The server answers 413 from the headers alone, without reading the body.
        for length in (2 * 1024 * 1024, 99999999999):
            conn = http.client.HTTPConnection('127.0.0.1', self.server.port, timeout=10)
            conn.putrequest('POST', '/api/auth/login')
            conn.putheader('Content-Type', 'application/json'); conn.putheader('Content-Length', str(length)); conn.putheader('Origin', self.server.base)
            conn.endheaders()
            self.assertEqual(conn.getresponse().status, 413)
            conn.close()
        c = self.client()
        r = c.request('POST', '/api/auth/login', raw=b'not json', content_type='application/json')
        self.assertEqual(r.status, 400)

    # ------------------------------------------------------------------ G9
    def test_g9_setup_disabled(self):
        r = self.client().post('/api/setup', {'fullname': 'x', 'email': 'x@x.org', 'username': 'x', 'password': 'abcdefghijk'})
        self.assertEqual(r.status, 403)
        self.assertFalse(self.client().get('/api/setup/status').json['setup_allowed'])

    # ------------------------------------------------------------------ G10
    def test_g10_csrf(self):
        noorigin = Client(self.server, origin=None)
        self.assertEqual(noorigin.post('/api/auth/login', {'login': 'a', 'password': 'b'}).status, 403)
        evil = Client(self.server, origin='https://evil.example')
        self.assertEqual(evil.post('/api/auth/login', {'login': 'a', 'password': 'b'}).status, 403)
        # Webhook stays reachable without Origin (answers 503 because it is not configured in tests).
        self.assertEqual(noorigin.post('/api/payments/webhook', {}).status, 503)
        # DELETE also checked.
        self.assertEqual(noorigin.request('DELETE', '/api/dive-points/1').status, 403)

    # ------------------------------------------------------------------ G11
    def test_g11_no_free_messaging(self):
        r = self.center_a.post('/api/messages', {'recipient_user_id': self.diver2.user['id'], 'subject': 'hola', 'body': 'spam spam'})
        self.assertEqual(r.status, 400)
        self.assertEqual(self.diver.post('/api/messages', {'booking_id': 1, 'body': 'hola hola'}).status, 403)
        cid = self.center_a.user['center_id']
        bid = self.diver2.post('/api/bookings', {'center_id': cid, 'booking_date': '2030-09-01'}).json['id']
        # Centre B cannot send a notice about centre A's booking.
        self.assertEqual(self.center_b.post('/api/messages', {'booking_id': bid, 'body': 'cambio de hora'}).status, 403)
        r = self.center_a.post('/api/messages', {'booking_id': bid, 'subject': 'Cambio de hora', 'body': 'La salida pasa a las 10:00.'})
        self.assertEqual(r.status, 200, r)
        msgs = self.diver2.get('/api/me/area').json['messages']
        self.assertTrue(any(m['subject'] == 'Cambio de hora' and m['kind'] == 'notice' for m in msgs))

    # ------------------------------------------------------------------ G12
    def test_g12_payments_fields(self):
        self.server.sql("INSERT INTO payment_orders(user_id,amount,currency,status,provider,platform_fee,connected_account_id,checkout_url,created_at,updated_at) VALUES(?,?,?,?,?,?,?,?,?,?)",
                        (self.diver.user['id'], 10, 'EUR', 'pending', 'stripe', 1, 'acct_x', 'https://checkout', 'x', 'x'))
        items = self.diver.post('/api/payments').json['items']
        self.assertTrue(items)
        for it in items:
            for k in ('platform_fee', 'connected_account_id', 'checkout_url', 'provider_payment_id'):
                self.assertNotIn(k, it)

    # ------------------------------------------------------------------ 13
    def test_13_password_hash_and_rehash(self):
        h = self.server.sql("SELECT password_hash FROM users WHERE username='diver_ana'")[0]['password_hash']
        self.assertTrue(h.startswith('pbkdf2_sha256$'))
        # A legacy hash (240 000 iterations) is upgraded at login.
        import base64, hashlib, os
        salt = os.urandom(16)
        legacy = base64.urlsafe_b64encode(salt + hashlib.pbkdf2_hmac('sha256', b'clave-antigua-123', salt, 240000)).decode()
        self.server.sql("UPDATE users SET password_hash=? WHERE username='diver_luis'", (legacy,))
        c = self.client()
        self.assertEqual(c.login('diver_luis', 'clave-antigua-123').status, 200)
        self.assertTrue(self.server.sql("SELECT password_hash FROM users WHERE username='diver_luis'")[0]['password_hash'].startswith('pbkdf2_sha256$'))

    def test_13_role_change_closes_sessions(self):
        d = self.make_diver('roles1')
        self.assertTrue(d.me()['authenticated'])
        r = self.admin.post('/api/admin/users/role', {'user_id': d.user['id'], 'role': 'recreational'})
        self.assertEqual(r.status, 200)
        self.assertFalse(d.me()['authenticated'])

    def test_13_login_rate_limit(self):
        c = self.client()
        codes = [c.login('nadie-existe', 'mala-clave-xx').status for _ in range(10)]
        self.assertIn(429, codes)

    # ------------------------------------------------------------------ 15
    def test_15_health_minimal(self):
        self.assertEqual(set(self.client().get('/api/health').json), {'ok', 'version'})

    def test_15_logs_without_query(self):
        self.client().get('/api/top-dives?lat=38.7&lon=0.1')
        time.sleep(0.3)
        log = (self.server.tmp / 'logs' / 'access.log').read_text()
        self.assertIn('/api/top-dives', log)
        self.assertNotIn('lat=38.7', log)
        self.assertNotIn('127.0.0.1 ', log)

    # ------------------------------------------------------------------ 16
    def test_16_promo_qr_svg(self):
        r = self.client().get('/api/promo/NOEXISTE/qr.svg')
        self.assertEqual(r.status, 404)

    # ------------------------------------------------------------------ permissions matrix
    def test_cross_role_permissions(self):
        cid_a = self.center_a.user['center_id']
        bid = self.diver.post('/api/bookings', {'center_id': cid_a, 'booking_date': '2030-10-01'}).json['id']
        # Another diver cannot see or cancel it.
        self.assertEqual(self.diver2.get(f'/api/bookings/{bid}').status, 403)
        self.assertIn(self.diver2.post(f'/api/bookings/{bid}/cancel', {}).status, (403, 404))
        self.assertEqual(self.diver2.get(f'/api/bookings/{bid}/receipt.pdf').status, 403)
        # Centre B cannot see or change it.
        self.assertEqual(self.center_b.get(f'/api/bookings/{bid}').status, 403)
        self.assertEqual(self.center_b.post(f'/api/bookings/{bid}/status', {'status': 'cancelled'}).status, 403)
        self.assertEqual(self.center_b.post(f'/api/bookings/{bid}/payment', {'payment_status': 'paid'}).status, 403)
        self.assertEqual(self.center_b.get(f'/api/bookings/{bid}/diver-sheet.pdf').status, 403)
        # Freelance and divers cannot reach admin or centre endpoints.
        for c in (self.pro, self.diver):
            self.assertEqual(c.get('/api/admin/users').status, 403)
            self.assertEqual(c.get('/api/admin/audit').status, 403)
            self.assertEqual(c.get('/api/center/clients').status, 403)
        # A centre cannot manage another centre's services.
        svc = self.center_a.post('/api/provider-services', {'title': 'Bautizo', 'price': 40, 'booking_mode': 'request'}).json['id']
        self.assertEqual(self.center_b.post('/api/provider-services/update', {'id': svc, 'title': 'Hackeado'}).status, 403)
        self.assertEqual(self.center_b.post('/api/provider-services/delete', {'id': svc}).status, 403)
        self.assertEqual(self.center_b.post('/api/provider-services/slot', {'service_id': svc, 'slot_date': '2030-01-01', 'slot_time': '10:00'}).status, 403)
        # Anonymous: no private data.
        anon = self.client()
        for path in ('/api/bookings', '/api/me/area', '/api/account/documents', '/api/logbook', f'/api/bookings/{bid}'):
            self.assertEqual(anon.get(path).status, 403, path)

    def test_bad_data_everywhere(self):
        """Malformed input must give 4xx, never 500."""
        c = self.diver
        paths = ['/api/bookings', '/api/account/profile', '/api/logbook', '/api/experience-bookings', '/api/rewards/redeem', '/api/reports',
                 '/api/auth/register', '/api/auth/reset', '/api/account/password', '/api/payments/checkout', '/api/messages']
        for p in paths:
            for body in ({'center_id': 'abc', 'participants': 'x', 'id': None}, {'center_id': -1}, {}):
                r = c.post(p, body)
                self.assertLess(r.status, 500, (p, body, r))
        for p in ('/api/dive-points/abc', '/api/centers/xyz', '/api/bookings/zz', '/api/providers/qq', '/api/top-dives?lat=a&lon=b'):
            self.assertLess(anon_status := self.client().get(p).status, 500, p)


if __name__ == '__main__':
    unittest.main(verbosity=2)
