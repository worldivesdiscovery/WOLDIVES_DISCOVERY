"""v50.51 · Correcciones de la revisión OWASP ASVS 5.0, nivel 2 (docs/auditoria/v50.51/asvs-5.0-nivel2.md).
Cada prueba nombra el requisito que comprueba."""
import concurrent.futures as cf
import datetime as dt
import os
import re
import subprocess
import sys
import tempfile
import textwrap
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from helpers import Client, ServerTestCase  # noqa: E402
from wod import totp as wtotp  # noqa: E402


def totp_now(secret):
    return wtotp.code_at(secret, int(time.time()) // 30)


class CorreoCifrado(unittest.TestCase):
    """V12.3.2: el servidor de correo tiene que demostrar quién es; uno falso no recibe la contraseña SMTP."""

    def test_fake_mail_server_gets_nothing(self):
        script = textwrap.dedent('''
            import base64, datetime, socket, ssl, sys, threading
            from cryptography import x509
            from cryptography.hazmat.primitives import hashes, serialization
            from cryptography.hazmat.primitives.asymmetric import ec
            from cryptography.x509.oid import NameOID
            key = ec.generate_private_key(ec.SECP256R1()); name = x509.Name([x509.NameAttribute(NameOID.COMMON_NAME, 'atacante.example')])
            now = datetime.datetime.now(datetime.timezone.utc)
            cert = x509.CertificateBuilder().subject_name(name).issuer_name(name).public_key(key.public_key()).serial_number(1) \\
                .not_valid_before(now).not_valid_after(now + datetime.timedelta(days=1)).sign(key, hashes.SHA256())
            open('c.pem', 'wb').write(cert.public_bytes(serialization.Encoding.PEM))
            open('k.pem', 'wb').write(key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()))
            got = []
            def serve(sock):
                ctx = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER); ctx.load_cert_chain('c.pem', 'k.pem')
                conn, _ = sock.accept(); f = conn.makefile('rb'); w = lambda s: conn.sendall(s.encode() + b'\\r\\n'); w('220 falso')
                try:
                    while True:
                        line = f.readline().decode().strip()
                        if not line: break
                        cmd = line.split(' ')[0].upper()
                        if cmd in ('EHLO', 'HELO'): w('250-falso'); w('250-AUTH PLAIN'); w('250 STARTTLS')
                        elif cmd == 'STARTTLS':
                            w('220 listo'); conn = ctx.wrap_socket(conn, server_side=True); f = conn.makefile('rb')
                            w = (lambda c: lambda s: c.sendall(s.encode() + b'\\r\\n'))(conn)
                        elif cmd == 'AUTH': got.append(line); w('235 ok')
                        else: w('250 ok')
                except Exception: pass
            s = socket.socket(); s.bind(('127.0.0.1', 0)); s.listen(1)
            threading.Thread(target=serve, args=(s,), daemon=True).start()
            sys.path.insert(0, sys.argv[1]); import server
            try:
                server._smtp_open({'host': '127.0.0.1', 'port': s.getsockname()[1], 'security': 'starttls', 'user': 'u', 'password': 'clave-smtp'})
                print('CONECTADO', got)
            except ssl.SSLError as e:
                print('RECHAZADO', got)
        ''')
        with tempfile.TemporaryDirectory() as tmp:
            env = dict(os.environ, WOD_DB_PATH=str(Path(tmp) / 'x.sqlite3'), WOD_DATA_DIR=tmp, WOD_NO_ENV_FILE='1', WOD_LOG_DIR=tmp)
            r = subprocess.run([sys.executable, '-c', script, str(ROOT / 'app')], cwd=tmp, env=env, capture_output=True, text=True, timeout=60)
        self.assertIn('RECHAZADO []', r.stdout, r.stdout + r.stderr)


class Sesiones(ServerTestCase):
    """V7: volver a entrar, inactividad, ver y cerrar sesiones, cierre por la administración, 2FA en cambios sensibles."""

    def cookie(self, c):
        return next(x.value for x in c.jar if x.name.endswith('wd_session'))

    def with_cookie(self, value):
        c = self.client(); c.opener.addheaders = [('Cookie', f'wd_session={value}')]; return c

    def test_v7_2_4_signing_in_again_ends_the_old_session(self):
        d = self.make_diver('ses1'); old = self.cookie(d)
        self.assertEqual(d.login('diver_ses1').status, 200)
        self.assertNotEqual(self.cookie(d), old)
        self.assertFalse(self.with_cookie(old).me()['authenticated'])

    def test_v7_3_1_idle_sessions_end(self):
        d = self.make_diver('ses2')
        self.server.sql("UPDATE sessions SET last_seen=last_seen-5*3600 WHERE user_id=?", (d.user['id'],))   # 5 h without use
        self.assertFalse(d.me()['authenticated'])

    def test_v7_5_2_see_and_close_the_other_sessions(self):
        a = self.make_diver('ses3'); b = self.client(); self.assertEqual(b.login('diver_ses3').status, 200)
        items = a.get('/api/account/sessions').json['items']
        self.assertEqual(len(items), 2); self.assertTrue(items[0]['current']); self.assertNotIn('token_hash', items[0])
        self.assertEqual(a.post('/api/account/sessions/close', {'password': 'mala-clave-1'}).status, 400)
        r = a.post('/api/account/sessions/close', {'password': 'buceo-seguro-2026'}); self.assertEqual(r.json['closed'], 1)
        self.assertFalse(b.me()['authenticated']); self.assertTrue(a.me()['authenticated'])

    def test_v7_4_5_the_administration_closes_someones_sessions(self):
        admin = self.make_admin('adm-ses@worldives.test', 'admses'); d = self.make_diver('ses4')
        self.assertEqual(admin.post('/api/admin/sessions/close', {'user_id': d.user['id']}).status, 400)        # a reason is needed
        self.assertEqual(admin.post('/api/admin/sessions/close', {'user_id': d.user['id'], 'reason': 'Cuenta comprometida'}).json['closed'], 1)
        self.assertFalse(d.me()['authenticated'])
        self.assertIn(d.post('/api/admin/sessions/close', {'all': True, 'reason': 'intento'}).status, (401, 403))
        self.assertTrue(self.server.sql("SELECT 1 FROM audit_log WHERE action='admin_sessions_closed'"))

    def enable_totp(self, c):
        secret = c.post('/api/account/totp/setup', {'password': 'buceo-seguro-2026'}).json['secret']
        self.assertEqual(c.post('/api/account/totp/enable', {'code': totp_now(secret)}).status, 200)
        self.server.sql('UPDATE users SET totp_last_step=NULL WHERE id=?', (c.user['id'],))   # the next code of this step is usable
        return secret

    def test_v7_5_1_password_change_asks_for_the_code(self):
        d = self.make_diver('ses5'); secret = self.enable_totp(d)
        body = {'current_password': 'buceo-seguro-2026', 'new_password': 'otra-clave-segura-5'}
        self.assertEqual(d.post('/api/account/password', body).status, 400)
        self.assertEqual(d.post('/api/account/password', {**body, 'totp_code': totp_now(secret)}).status, 200)

    def test_v6_5_1_one_code_one_login_even_at_the_same_time(self):
        d = self.make_diver('ses6'); secret = self.enable_totp(d); code = totp_now(secret)
        def login(_):
            c = self.client(); return c.post('/api/auth/login', {'login': 'diver_ses6', 'password': 'buceo-seguro-2026', 'totp_code': code}).status
        with cf.ThreadPoolExecutor(6) as ex: statuses = list(ex.map(login, range(6)))
        self.assertEqual(statuses.count(200), 1, statuses)

    def test_v7_4_3_turning_2fa_off_ends_the_other_sessions(self):
        d = self.make_diver('ses7'); secret = self.enable_totp(d)
        other = self.client()
        self.assertEqual(other.post('/api/auth/login', {'login': 'diver_ses7', 'password': 'buceo-seguro-2026', 'totp_code': totp_now(secret)}).status, 200)
        self.server.sql('UPDATE users SET totp_last_step=NULL WHERE id=?', (d.user['id'],))
        self.assertEqual(d.post('/api/account/totp/disable', {'password': 'buceo-seguro-2026', 'code': totp_now(secret)}).status, 200)
        self.assertFalse(other.me()['authenticated']); self.assertTrue(d.me()['authenticated'])

    def test_v6_5_2_recovery_codes_have_120_bits(self):
        codes = wtotp.recovery_codes()
        self.assertEqual(len(codes), 8); self.assertEqual(len(set(codes)), 8)
        self.assertTrue(all(len(c.replace('-', '')) == 24 and set(c.replace('-', '')) <= set(wtotp.RECOVERY_ALPHABET) for c in codes))


class AdministradorSin2FA(ServerTestCase):
    """V6.3.3: con la verificación en dos pasos obligatoria, un administrador sin ella no ve datos de nadie."""
    extra_env = {'WOD_ADMIN_TOTP_REQUIRED': '1'}

    def test_only_my_account_until_2fa_is_on(self):
        res = self.server.run_cli('--create-admin', '--email', 'a2fa@worldives.test', '--username', 'a2fa', '--name', 'Admin', env={'WOD_ADMIN_PASSWORD': 'admin-seguro-2026'})
        self.assertEqual(res.returncode, 0, res.stdout + res.stderr)
        d = self.make_diver('a2fa1')
        uid = d.user['id']
        t = dt.datetime.now().isoformat()
        self.server.sql("INSERT INTO centers(name,country,city,active,created_at,updated_at) VALUES('Centro 2FA','España','Xàbia',1,?,?)", (t, t))
        cid = self.server.sql("SELECT id FROM centers WHERE name='Centro 2FA'")[0]['id']
        self.server.sql("INSERT INTO bookings(user_id,center_id,booking_date,participants,status,created_at,updated_at) VALUES(?,?,?,1,'requested',?,?)",
                        (uid, cid, '2031-01-10', t, t))
        a = self.client(); self.assertEqual(a.login('a2fa', 'admin-seguro-2026').status, 200)
        self.assertEqual(a.me()['user']['role'], 'admin')                                            # «Mi cuenta» works
        self.assertEqual(a.get('/api/bookings').json['items'], [])                                   # before: every booking
        r = a.get('/api/admin/users'); self.assertEqual(r.status, 403); self.assertIn('verificación en dos pasos', r.json['error'])
        self.assertEqual(a.post('/api/account/totp/setup', {'password': 'admin-seguro-2026'}).status, 200)   # and can turn it on


class ContrasenasYBloqueo(ServerTestCase):
    """V6.2 y V6.3: contraseñas filtradas o del contexto, contraseñas largas, bloqueo malicioso de cuentas, IPv6 y
    enlaces firmados de los avisos (V9)."""
    extra_env = {'WOD_TRUSTED_PROXIES': '127.0.0.1'}

    def ip(self, value):
        return {'X-Forwarded-For': value}

    def test_v6_2_4_v6_2_11_leaked_and_context_passwords_are_refused(self):
        weak = ['password123', 'password1234', 'qwerty1234', '1q2w3e4r5t', '12345678910', 'iloveyou12', 'aaaaaaaaaa',
                'worldives2026', 'worldivesdiscovery', 'Worldives-Demo-2026', 'buceo123456', 'scubadiving', 'qwertyuiop!!']
        for i, pw in enumerate(weak):
            r = self.client().request('POST', '/api/auth/register', {'fullname': 'Prueba Débil', 'email': f'debil{i}@diver.example.org', 'username': f'debil{i}',
                                                                      'password': pw, 'account_type': 'recreational', 'accept_terms': True, 'accept_privacy': True},
                                       headers=self.ip(f'203.0.113.{i + 1}'))
            self.assertEqual(r.status, 400, (pw, r)); self.assertIn('fácil de adivinar', r.json['error'])
        d = self.make_diver('fuerte1')   # 'buceo-seguro-2026': the name of the sport plus other words is fine
        self.assertEqual(d.post('/api/account/password', {'current_password': 'buceo-seguro-2026', 'new_password': 'password1234'}).status, 400)

    def test_v6_2_8_a_longer_password_is_not_cut(self):
        pw = ('Mar-de-fondo-' * 20)[:256]
        c = self.client()
        r = c.register('Buceador Largo', 'largo@diver.example.org', 'diver_largo', password=pw)
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.client().request('POST', '/api/auth/login', {'login': 'diver_largo', 'password': pw + 'EXTRA'}, headers=self.ip('203.0.113.50')).status, 401)
        self.assertEqual(self.client().request('POST', '/api/auth/login', {'login': 'diver_largo', 'password': pw}, headers=self.ip('203.0.113.50')).status, 200)

    def test_v6_3_1_nobody_can_lock_the_owner_out(self):
        self.make_diver('cerrojo')
        login = lambda who, pw, ip: self.client().request('POST', '/api/auth/login', {'login': who, 'password': pw}, headers=self.ip(ip))
        self.assertEqual(login('diver_cerrojo', 'buceo-seguro-2026', '198.51.100.70').status, 200)       # the owner, at home
        # 24 wrong passwords from three addresses, with the username and with the email (one account, one counter)
        for n in range(3):
            for k in range(8):
                who = 'diver_cerrojo' if k % 2 else 'cerrojo@diver.example.org'
                self.assertEqual(login(who, f'no-es-la-clave-{k}', f'192.0.2.{n + 1}').status, 401)
        self.assertEqual(login('diver_cerrojo', 'buceo-seguro-2026', '192.0.2.200').status, 429)          # an unknown place: locked
        self.assertEqual(login('cerrojo@diver.example.org', 'buceo-seguro-2026', '192.0.2.201').status, 429)
        self.assertEqual(login('diver_cerrojo', 'buceo-seguro-2026', '198.51.100.70').status, 200)        # the owner still gets in
        # ... and the owner can always ask for the link from home, and resetting the password unlocks the account
        anon = self.client()
        for _ in range(6):
            r = anon.request('POST', '/api/auth/forgot', {'email': 'cerrojo@diver.example.org'}, headers=self.ip('192.0.2.77'))
        self.assertEqual(r.status, 429)
        r = anon.request('POST', '/api/auth/forgot', {'email': 'cerrojo@diver.example.org'}, headers=self.ip('198.51.100.70'))
        self.assertEqual(r.status, 200, r)
        mail = self.server.sql("SELECT text FROM email_outbox WHERE template='password_reset' AND to_email='cerrojo@diver.example.org' ORDER BY id DESC")[0]['text']
        token = re.search(r'restablecer\?token=([A-Za-z0-9_\-]+)', mail).group(1)
        self.assertEqual(anon.request('POST', '/api/auth/reset', {'token': token, 'password': 'nueva-clave-segura-8'}, headers=self.ip('198.51.100.71')).status, 200)
        self.assertEqual(login('diver_cerrojo', 'nueva-clave-segura-8', '192.0.2.202').status, 200)

    def test_v6_3_1_an_ipv6_network_counts_as_one_address(self):
        self.make_diver('seisv')
        for k in range(8):
            r = self.client().request('POST', '/api/auth/login', {'login': 'diver_seisv', 'password': 'no-es-la-clave'}, headers=self.ip(f'2001:db8:77:1::{k + 1:x}'))
            self.assertEqual(r.status, 401)
        r = self.client().request('POST', '/api/auth/login', {'login': 'diver_seisv', 'password': 'no-es-la-clave'}, headers=self.ip('2001:db8:77:1:ffff::9'))
        self.assertEqual(r.status, 429)      # before: every address of the /64 had its own 8 attempts

    def test_v9_2_2_a_reminder_link_cannot_choose_a_refund(self):
        from wod import avisos
        d = self.make_diver('enlace1')
        t = dt.datetime.now().isoformat()
        self.server.sql("INSERT INTO centers(name,country,city,active,created_at,updated_at) VALUES('Centro Enlace','España','Xàbia',1,?,?)", (t, t))
        cid = self.server.sql("SELECT id FROM centers WHERE name='Centro Enlace'")[0]['id']
        self.server.sql("INSERT INTO bookings(user_id,center_id,booking_date,participants,status,created_at,updated_at) VALUES(?,?,?,1,'confirmed',?,?)",
                        (d.user['id'], cid, '2031-01-10', t, t))
        bid = self.server.sql('SELECT id FROM bookings WHERE center_id=?', (cid,))[0]['id']
        token = avisos.sign_link('x' * 40, bid, 'reminder', int(time.time()) + 3600)
        self.assertEqual(self.client().get('/api/r/' + token).status, 200)                  # it opens the booking
        r = self.client().post('/api/r/' + token, {'choice': 'refund'})
        self.assertEqual(r.status, 403, r); self.assertIn('no sirve', r.json['error'])


class PermisosDelEquipo(ServerTestCase):
    """V8.2: lo que un perfil del equipo sin «Reservas», «Cobros» o «Ver todas las salidas» puede leer."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.owner = t.make_center(cls.admin, 'v8a', phone='+34 600 580 001')
        cid = cls.cid = cls.owner.user['center_id']
        cls.ins = cls.member(t, cid, 'v8ins', 'instructor')       # only «Pasar lista»
        cls.ins2 = cls.member(t, cid, 'v8ins2', 'instructor')
        cls.rec = cls.member(t, cid, 'v8rec', 'reception')        # «Reservas» (charges at the desk), without «Cobros»
        day = cls.day = cls.owner.get('/api/pro/hoy').json['tomorrow']   # «tomorrow» where the centre is
        sid = cls.owner.post('/api/provider-services', {'title': 'Salida V8', 'price': 40, 'booking_mode': 'request'}).json['id']
        cls.slot_other = cls.owner.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': day, 'slot_time': '09:00', 'spots_total': 8}).json['slot_id']
        cls.slot_mine = cls.owner.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': day, 'slot_time': '15:00', 'spots_total': 8}).json['slot_id']
        diver = t.make_diver('v8d')
        bids = []
        for slot in (cls.slot_other, cls.slot_mine):
            r = diver.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': 1})
            assert r.status == 200, r
            bids.append(r.json['id'])
            assert cls.owner.post(f"/api/bookings/{r.json['id']}/status", {'status': 'confirmed'}).status == 200
        cls.bid = bids[0]
        s = cls.server
        s.sql("UPDATE bookings SET internal_notes='Nota solo del centro', amount_paid=40, payment_status='paid' WHERE id=?", (cls.bid,))
        ts = dt.datetime.now().isoformat()
        s.sql("INSERT INTO slot_groups(slot_id,guide_user_id,label,sort,created_at,updated_at) VALUES(?,?,?,?,?,?)", (cls.slot_other, cls.ins2.user['id'], 'Grupo 1', 0, ts, ts))
        s.sql("INSERT INTO slot_groups(slot_id,guide_user_id,label,sort,created_at,updated_at) VALUES(?,?,?,?,?,?)", (cls.slot_mine, cls.ins.user['id'], 'Grupo 1', 0, ts, ts))

    @classmethod
    def member(cls, t, center_id, tag, role):
        c = t.make_diver(tag); uid = c.user['id']
        cls.server.sql("UPDATE users SET role='center',center_id=? WHERE id=?", (center_id, uid))
        cls.server.sql('INSERT OR REPLACE INTO center_members(center_id,user_id,member_role,created_at) VALUES(?,?,?,?)', (center_id, uid, role, '2026-01-01'))
        assert c.login(f'diver_{tag}').status == 200
        c.user = c.me()['user']
        return c

    def test_v8_2_1_requests_clients_and_exports_need_reservas(self):
        for path in ('/api/center/requests', '/api/center/clients', '/api/center/info-requests', '/api/center/export?kind=clients', '/api/center/export?kind=bookings'):
            self.assertEqual(self.ins.get(path).status, 403, path)
            self.assertEqual(self.owner.get(path).status, 200, path)
        self.assertEqual(self.ins.get('/api/center/export?kind=payments').status, 403)
        self.assertEqual(self.ins.get('/api/center/export?kind=services').status, 200)

    def test_v8_2_1_rewards_check_a_code_but_not_validate_or_grant(self):
        # The web shows an instructor only what the server lets him do in «Recompensas» (inventory of 14/10)
        diver = self.server.sql("SELECT id FROM users WHERE username='diver_v8d'")[0]['id']
        self.assertEqual(self.ins.post('/api/provider/points-grant', {'user_id': diver, 'points': 5}).status, 403)
        self.assertEqual(self.ins.post('/api/center/redemptions/validate', {'code': 'WOD-NOEXISTE'}).status, 403)
        self.assertNotEqual(self.ins.get('/api/center/redemptions?code=WOD-NOEXISTE').status, 403)
        js = self.client().get('/js/world-dives-v8.js').body.decode('utf-8')
        self.assertIn("const write=isAdmin||wdCan('reservas');", js)
        self.assertIn("r.status==='issued'&&write?", js)

    def test_v8_2_2_a_departure_guided_by_someone_else_is_not_readable(self):
        self.assertEqual(self.ins.get(f'/api/manifest/{self.slot_other}').status, 404)        # before: 200 with phones
        self.assertEqual(self.ins.get(f'/api/manifest/{self.slot_mine}').status, 200)
        self.assertEqual(self.ins2.get(f'/api/manifest/{self.slot_other}').status, 200)
        self.assertEqual(self.owner.get(f'/api/manifest/{self.slot_other}').status, 200)
        day = self.ins.get(f'/api/manifest/day?date={self.day}')
        self.assertEqual(day.status, 200, day)
        self.assertEqual({x['slot']['id'] for x in day.json['slots']}, {self.slot_mine})
        self.assertEqual(self.ins.get(f'/api/manifest/{self.slot_other}/resumen.pdf').status, 404)

    def test_v8_2_3_amounts_and_internal_notes_need_their_permission(self):
        mine = [b for b in self.ins.get('/api/bookings').json['items'] if b['id'] == self.bid][0]
        for k in ('amount_paid', 'amount_due', 'refunded_total', 'price_breakdown', 'payment_method', 'internal_notes'):
            self.assertNotIn(k, mine)
        d = self.ins.get(f'/api/bookings/{self.bid}').json
        self.assertIsNone(d['payment']); self.assertNotIn('internal_notes', d['booking']); self.assertNotIn('paid_online', d['booking'])
        own = self.owner.get(f'/api/bookings/{self.bid}').json
        self.assertEqual(own['booking']['internal_notes'], 'Nota solo del centro'); self.assertIn('paid_online', own['booking'])
        self.assertEqual([b for b in self.owner.get('/api/bookings').json['items'] if b['id'] == self.bid][0]['amount_paid'], 40)
        self.assertEqual(self.ins.get(f'/api/bookings/{self.bid}/receipt.pdf').status, 403)                  # it shows what was paid
        # reception charges at the desk: it needs what was already paid
        self.assertEqual([b for b in self.rec.get('/api/bookings').json['items'] if b['id'] == self.bid][0]['amount_paid'], 40)
        self.assertIn('paid_online', self.rec.get(f'/api/bookings/{self.bid}').json['booking'])
        self.assertEqual(self.rec.get(f'/api/bookings/{self.bid}/receipt.pdf').status, 200)


class DocumentoDePermisos(unittest.TestCase):
    """V8.1.1: la matriz de docs/seguridad/permisos.md dice lo mismo que app/wod/roles.py."""

    def test_permissions_doc_matches_the_rules(self):
        from wod import roles
        doc = (ROOT / 'docs' / 'seguridad' / 'permisos.md').read_text(encoding='utf-8')
        for key, name, _ in roles.PERMISOS:
            self.assertIn(f'| `{key}` | {name} |', doc)
        for role, perms in roles.POR_DEFECTO.items():
            if role != 'manager':
                for p in perms: self.assertIn(f'`{p}`', doc)
        for rules in (roles.REGLAS_GET, roles.REGLAS_POST):
            for _perm, pats in rules:
                for pat in pats:
                    if isinstance(pat, str): self.assertIn(f'`{pat}`', doc, pat)
        flat = ' '.join(doc.split()).lower()
        for what in roles.SOLO_PROPIETARIO:
            self.assertIn(what[1:].lower(), flat, what)


class ValidacionYLimites(ServerTestCase):
    """V1.4.2, V2.2, V2.3 y V2.4: importes finitos, fechas y horas reales, personas, coordenadas, límites por persona y
    operaciones de puntos y plazas sin carreras."""
    extra_env = {'WOD_BOOKING_MAX_PER_HOUR': '4'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.owner = t.make_center(cls.admin, 'v2a', phone='+34 600 590 001')
        cls.cid = cls.owner.user['center_id']
        cls.sid = cls.owner.post('/api/provider-services', {'title': 'Salida V2', 'price': 30, 'booking_mode': 'request'}).json['id']
        day = (dt.date.today() + dt.timedelta(days=20)).isoformat()
        cls.slots = [cls.owner.post('/api/provider-services/slot', {'service_id': cls.sid, 'slot_date': day, 'slot_time': f'{9 + i:02d}:00', 'spots_total': 8}).json['slot_id'] for i in range(6)]

    def raw(self, c, path, body):
        return c.request('POST', path, raw=body.encode(), content_type='application/json')

    def test_v2_2_1_amounts_are_finite_and_not_negative(self):
        for price in ('inf', 'nan', '-5', 1e9, '1e400'):
            r = self.owner.post('/api/provider-services', {'title': 'Precio raro', 'price': price, 'booking_mode': 'request'})
            self.assertEqual(r.status, 400, (price, r)); self.assertIn('importe', r.json['error'])
        self.assertEqual(self.owner.post('/api/center/extras/save', {'name': 'Extra negativo', 'price': -80}).status, 400)
        self.assertEqual(self.raw(self.owner, '/api/center/extras/save', '{"name": "Extra", "price": NaN}').status, 400)
        self.assertEqual(self.raw(self.owner, '/api/center/extras/save', '{"name": "Extra", "price": Infinity}').status, 400)
        self.assertEqual(self.owner.post('/api/center/extras/save', {'name': 'Extra bueno', 'price': '12,50'}).status, 200)
        self.assertEqual(self.client().get('/api/center-directory').status, 200)

    def test_v2_2_1_dates_times_people_and_places(self):
        d = self.make_diver('v2fechas')
        base = {'center_id': self.cid, 'service_id': self.sid, 'participants': 1}
        r = d.post('/api/bookings', {**base, 'booking_date': '2031-02-31'}); self.assertEqual(r.status, 400, r); self.assertIn('fecha', r.json['error'])
        r = d.post('/api/bookings', {**base, 'booking_date': '2031-03-03', 'booking_time': '<b>99:99</b>'}); self.assertEqual(r.status, 400, r); self.assertIn('hora', r.json['error'])
        for n in (0, 5000, 10 ** 30, 'muchos', 2.5):
            r = d.post('/api/bookings', {**base, 'slot_id': self.slots[0], 'participants': n}); self.assertEqual(r.status, 400, (n, r))
        r = d.post('/api/logbook/update', {'id': 10 ** 30, 'dive_date': '2020-01-01', 'site': 'Cala'})   # V1.4.2: before, 500
        self.assertEqual(r.status, 400, r); self.assertIn('demasiado grande', r.json['error'])
        for day in ('2025-02-31', '1999-99-99', '0001-01-01', '1949-12-31'):
            self.assertEqual(d.post('/api/logbook', {'dive_date': day, 'site': 'Cala', 'country': 'España'}).status, 400, day)
        self.assertEqual(d.post('/api/logbook', {'dive_date': '1998-07-14', 'site': 'Cala', 'country': 'España'}).status, 200)
        self.assertEqual(d.post('/api/account/identity', {'fullname': {'x': 1}}).status, 400)
        r = self.owner.post('/api/center/profile', {'name': 'Centro v2a', 'country': 'España', 'city': 'Xàbia', 'latitude': 123, 'longitude': 5})
        self.assertEqual(r.status, 400, r); self.assertIn('coordenadas', r.json['error'])
        self.assertEqual(self.owner.post('/api/provider-services', {'title': 'Duración rara', 'price': 10, 'duration_minutes': -30, 'booking_mode': 'request'}).status, 400)

    def test_v2_4_1_bookings_per_person_and_hour(self):
        d = self.make_diver('v2limite')
        for i in range(4):
            r = d.post('/api/bookings', {'center_id': self.cid, 'service_id': self.sid, 'slot_id': self.slots[1 + i], 'participants': 1})
            self.assertEqual(r.status, 200, r)
        r = d.post('/api/bookings', {'center_id': self.cid, 'service_id': self.sid, 'slot_id': self.slots[5], 'participants': 1})
        self.assertEqual(r.status, 429, r); self.assertIn('muchas reservas', r.json['error'])

    def test_v2_3_2_logbook_points_stop_after_ten_entries_a_day(self):
        d = self.make_diver('v2granja')
        for i in range(14):
            self.assertEqual(d.post('/api/logbook', {'dive_date': (dt.date(2020, 1, 1) + dt.timedelta(days=i)).isoformat(), 'site': f'Punto {i}', 'country': 'España'}).status, 200)
        d.get('/api/points')
        n = self.server.sql("SELECT COUNT(*) n FROM reward_events WHERE user_id=? AND event_key LIKE 'logbook:dive:%'", (d.user['id'],))[0]['n']
        self.assertEqual(n, 10)      # before: 14 (one per date chosen by the diver)


@unittest.skipUnless(hasattr(os, 'fork') and os.path.isdir('/proc'), 'WOD_WORKERS necesita Linux')
class PuntosYPlazasVariosProcesos(ServerTestCase):
    """V2.3.4: con cuatro procesos a la vez, un saldo da un solo código y una plaza se vende una sola vez."""
    extra_env = {'WOD_WORKERS': '4'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.owner = t.make_center(cls.admin, 'v2p', phone='+34 600 590 101')

    def test_v2_3_4_one_point_balance_one_code(self):
        for rnd in range(3):
            d = self.make_diver(f'v2canje{rnd}')
            oid = self.owner.post('/api/provider/reward-offers', {'title': f'Botella gratis {rnd}', 'reward_type': 'discount', 'cost_points': 100, 'value_text': 'Una botella', 'stock': 1}).json['id']
            self.server.sql("INSERT INTO points_ledger(user_id,points,kind,description,created_at) VALUES(?,?,'adjust','test',datetime('now'))", (d.user['id'], 100 - d.get('/api/points').json['balance']))
            with cf.ThreadPoolExecutor(12) as ex:
                res = list(ex.map(lambda _: d.post('/api/rewards/redeem', {'offer_id': oid}).status, range(12)))
            self.assertEqual(res.count(200), 1, res)
            self.assertEqual(d.get('/api/points').json['balance'], 0)
            self.assertEqual(self.server.sql('SELECT stock FROM reward_offers WHERE id=?', (oid,))[0]['stock'], 0)

    def test_v2_3_4_the_last_spot_of_an_experience_is_sold_once(self):
        start = (dt.date.today() + dt.timedelta(days=40)).isoformat()
        for rnd in range(3):
            r = self.owner.post('/api/travel-experiences', {'title': f'Viaje a Medes {rnd}', 'summary': 'Dos días', 'start_date': start, 'end_date': start,
                                                            'price': 0, 'spots_total': 1, 'spots_available': 1, 'new_destination': 'Islas Medes'})
            self.assertEqual(r.status, 200, r); eid = r.json['id']
            divers = [self.make_diver(f'v2viaje{rnd}x{i}') for i in range(6)]
            with cf.ThreadPoolExecutor(6) as ex:
                res = list(ex.map(lambda c: c.post('/api/experience-bookings', {'travel_experience_id': eid, 'participants': 1}).status, divers))
            self.assertEqual(res.count(200), 1, res)
            self.assertEqual(self.server.sql('SELECT spots_available FROM travel_experiences WHERE id=?', (eid,))[0]['spots_available'], 0)


class ArchivosYCabeceras(ServerTestCase):
    """V3.2.1, V3.4.3, V4.1.1, V4.2.1, V5.2.2, V5.3.2, V5.4.1 y V5.4.3: lo que se sube se comprueba de verdad y lo que
    se sirve no puede ejecutar nada."""
    extra_env = {'WOD_AV_COMMAND': sys.executable + " -c \"import sys; sys.exit(1 if b'EICAR-PRUEBA' in sys.stdin.buffer.read() else 0)\""}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.A = t.make_center(cls.admin, 'v5a', phone='+34 600 595 001')
        cls.B = t.make_center(cls.admin, 'v5b', phone='+34 600 595 002')

    def test_v5_2_2_images_and_pdfs_must_really_be_what_they_say(self):
        from helpers import PDF_BYTES, PNG_BYTES
        fake = b'\x89PNG\r\n\x1a\n<html><script>alert(1)</script></html>'
        r = self.A.upload('/api/provider/avatar', {}, 'logo.png', fake); self.assertEqual(r.status, 400, r)   # before: stored as it came
        self.assertEqual(self.A.upload('/api/provider/avatar', {}, 'logo.png', PNG_BYTES).status, 200)
        d = self.make_diver('v5doc')
        self.assertEqual(d.upload('/api/account/documents', {'document_type': 'Seguro', 'title': 'roto'}, 'x.png', fake).status, 400)
        self.assertEqual(d.upload('/api/account/documents', {'document_type': 'Seguro', 'title': 'cortado'}, 'x.pdf', b'%PDF-1.4\n1 0 obj<<>>endobj\n').status, 400)
        self.assertEqual(d.upload('/api/account/documents', {'document_type': 'Seguro', 'title': 'bueno'}, 'x.pdf', PDF_BYTES).status, 200)

    def test_v5_4_3_the_antivirus_stops_an_infected_file(self):
        d = self.make_diver('v5virus')
        r = d.upload('/api/account/documents', {'document_type': 'Seguro', 'title': 'virus'}, 'x.pdf', b'%PDF-1.4\nEICAR-PRUEBA\n%%EOF\n')
        self.assertEqual(r.status, 400, r); self.assertIn('antivirus', r.json['error'])

    def test_v5_4_1_v3_2_1_documents_keep_their_real_type_and_run_nothing(self):
        from helpers import PDF_BYTES, PNG_BYTES
        d = self.make_diver('v5nombre')
        self.assertEqual(d.upload('/api/account/documents', {'document_type': 'Seguro', 'title': 'Seguro'}, 'seguro.html', PDF_BYTES).status, 200)
        self.assertEqual(d.upload('/api/account/documents', {'document_type': 'Titulación', 'title': 'Foto'}, 'foto.svg', PNG_BYTES).status, 200)
        docs = {x['title']: x['id'] for x in d.get('/api/account/documents').json['items']}
        r = d.get(f"/api/documents/file/{docs['Seguro']}")
        self.assertIn('seguro.pdf', r.headers['Content-Disposition']); self.assertNotIn('.html', r.headers['Content-Disposition'])
        r = d.get(f"/api/documents/file/{docs['Foto']}")
        self.assertTrue(r.headers['Content-Disposition'].endswith('foto.png') or 'foto.png' in r.headers['Content-Disposition'])
        self.assertIn('sandbox', r.headers['Content-Security-Policy'])

    def test_v5_3_2_a_centre_cannot_take_another_centres_file_as_logo(self):
        from helpers import PNG_BYTES
        self.assertEqual(self.B.upload('/api/provider/avatar', {}, 'b.png', PNG_BYTES).status, 200)
        logo_b = self.server.sql('SELECT logo_url FROM centers WHERE id=?', (self.B.user['center_id'],))[0]['logo_url']
        self.assertTrue(logo_b.startswith('/assets/uploads/'))
        r = self.A.post('/api/provider/center-update', {'name': 'Centro v5a', 'country': 'España', 'city': 'Xàbia', 'logo_url': logo_b}); self.assertEqual(r.status, 400, r); self.assertIn('logo', r.json['error'])
        r = self.A.post('/api/provider/center-update', {'name': 'Centro v5a', 'country': 'España', 'city': 'Xàbia', 'logo_url': 'https://centro-v5a.example.org/logo.png'}); self.assertEqual(r.status, 200, r)
        r = self.client().get(logo_b); self.assertEqual(r.status, 200); self.assertIn('sandbox', r.headers['Content-Security-Policy'])

    def test_v3_4_3_v4_1_1_v4_2_1_headers(self):
        page = self.client().get('/')
        self.assertIn("base-uri 'none'", page.headers['Content-Security-Policy'])
        self.assertIn('charset=utf-8', self.client().get('/js/world-dives-v8.js').headers['Content-Type'])
        import http.client
        conn = http.client.HTTPConnection('127.0.0.1', self.server.port, timeout=10)
        conn.putrequest('POST', '/api/contact'); conn.putheader('Origin', self.server.base); conn.putheader('Content-Type', 'application/json')
        conn.putheader('Transfer-Encoding', 'chunked'); conn.endheaders(); conn.send(b'2\r\n{}\r\n0\r\n\r\n')
        self.assertEqual(conn.getresponse().status, 400)


class RegistrosYSalidas(ServerTestCase):
    """V12–V16: sucesos de seguridad en la actividad, textos de Python que no llegan al visitante, registros sin
    caracteres de control y en UTC, sí/no estrictos, buscador de lugares que no bloquea, retención y copias."""
    extra_env = {'WOD_TRUSTED_PROXIES': '127.0.0.1', 'WOD_GEOCODER_URL': 'http://127.0.0.1:9/buscar', 'WOD_ACCESS_LOG': 'file'}

    def alerts(self, kind, wait=8):
        end = time.time() + wait
        while time.time() < end:
            rows = self.server.sql("SELECT user_id,details FROM audit_log WHERE action='security_alert' AND entity_type=?", (kind,))
            if rows: return rows
            time.sleep(0.3)
        return []

    def test_v16_3_security_events_are_recorded(self):
        d = self.make_diver('v16ev')
        self.assertEqual(d.get('/api/admin/users').status, 403)
        self.assertEqual(Client(self.server, origin='https://otra-web.example').post('/api/contact', {}).status, 403)
        self.assertEqual(self.client().request('POST', '/api/auth/login', {'login': 'nadie-existe', 'password': 'x' * 12}, headers={'X-Forwarded-For': '192.0.2.99'}).status, 401)
        self.assertEqual(self.client().request('POST', '/api/payments/webhook', raw=b'{}', content_type='application/json', headers={'Stripe-Signature': 't=1,v1=falsa'}).status in (400, 503), True)
        self.assertEqual(d.post('/api/auth/logout', {}).status, 200)
        self.assertTrue(self.alerts('access_denied')); self.assertEqual(self.alerts('access_denied')[0]['user_id'], d.user['id'])
        self.assertTrue(self.alerts('csrf_blocked')); self.assertTrue(self.alerts('login_unknown_account'))
        self.assertTrue(self.server.sql("SELECT 1 FROM audit_log WHERE action='logout' AND user_id=?", (d.user['id'],)))

    def test_v16_5_1_python_texts_never_reach_the_visitor(self):
        d = self.make_diver('v16texto')
        r = d.post('/api/bookings', {'center_id': 'abc'})
        self.assertEqual(r.status, 400); self.assertNotIn('invalid literal', r.body.decode()); self.assertIn('formato esperado', r.json['error'])

    def test_v15_3_5_false_means_no(self):
        d = self.make_diver('v15bool')
        self.assertEqual(d.post('/api/account/marketing', {'consent': 'false'}).status, 200)
        self.assertEqual(self.server.sql('SELECT marketing_consent FROM users WHERE id=?', (d.user['id'],))[0]['marketing_consent'], 0)   # before: 1
        self.assertEqual(d.post('/api/account/marketing', {'consent': 'quizá'}).status, 400)

    def test_v16_4_1_v16_2_2_log_lines_are_safe_and_in_utc(self):
        import socket
        s = socket.create_connection(('127.0.0.1', self.server.port), timeout=5)
        s.sendall(b'GET /nada\x1b[31mROJO HTTP/1.0\r\nHost: x\r\n\r\n'); s.recv(100); s.close()
        log = self.server.tmp / 'logs' / 'access.log'
        end = time.time() + 5
        while time.time() < end and (not log.exists() or 'ROJO' not in log.read_text(encoding='utf-8', errors='replace')): time.sleep(0.2)
        line = [x for x in log.read_text(encoding='utf-8', errors='replace').splitlines() if 'ROJO' in x][-1]
        self.assertNotIn('\x1b', line); self.assertIn('\\x1b', line)
        self.assertRegex(line, r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z ')

    def test_v15_2_2_v16_5_2_a_broken_geocoder_answers_at_once(self):
        statuses = []
        for i in range(5):
            t0 = time.time(); r = self.client().get(f'/api/geocode?q=lugar{i}'); statuses.append((r.status, (r.json or {}).get('unavailable'), round(time.time() - t0, 1)))
        # v50.53: the provider being down is said in the answer ({'unavailable': true}), not with a 503 that would leave
        # an error in the visitor's console; it still answers at once after three failures.
        self.assertEqual(statuses[-1][:2], (200, True), statuses)
        self.assertLess(statuses[-1][2], 0.5, statuses)

    def test_v14_2_4_old_bookings_lose_their_contact_details(self):
        admin = self.make_admin('ret@worldives.test', 'admin_ret')
        d = self.make_diver('v14viejo')
        t = dt.datetime.now().isoformat()
        self.server.sql("INSERT INTO centers(name,country,city,active,created_at,updated_at) VALUES('Centro Viejo','España','Xàbia',1,?,?)", (t, t))
        cid = self.server.sql("SELECT id FROM centers WHERE name='Centro Viejo'")[0]['id']
        old = (dt.date.today() - dt.timedelta(days=365 * 7)).isoformat(); new = (dt.date.today() - dt.timedelta(days=30)).isoformat()
        for day in (old, new):
            self.server.sql("INSERT INTO bookings(user_id,center_id,booking_date,participants,status,contact_name,contact_email,notes,created_at,updated_at) VALUES(?,?,?,1,'completed','Ana Vieja','ana@example.org','Alérgica',?,?)",
                            (d.user['id'], cid, day, t, t))
        r = admin.post('/api/admin/retention', {'run_now': True}); self.assertEqual(r.status, 200, r)
        rows = {x['booking_date']: x for x in self.server.sql('SELECT booking_date,contact_name,contact_email,notes FROM bookings WHERE center_id=?', (cid,))}
        self.assertEqual((rows[old]['contact_name'], rows[old]['contact_email'], rows[old]['notes']), (None, None, None))
        self.assertEqual(rows[new]['contact_name'], 'Ana Vieja')
        # a deleted account takes its information requests and the contact details of its bookings with it
        gone = self.make_diver('v14borrado')
        self.server.sql("INSERT INTO info_requests(center_id,user_id,name,email,message,created_at) VALUES(?,?,?,?,?,?)", (cid, gone.user['id'], 'Borrado', 'b@example.org', 'Hola', t))
        self.server.sql("INSERT INTO bookings(user_id,center_id,booking_date,participants,status,contact_name,contact_email,created_at,updated_at) VALUES(?,?,?,1,'completed','Borrado','b@example.org',?,?)",
                        (gone.user['id'], cid, new, t, t))
        long_ago = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=1200)).isoformat(timespec='seconds')
        self.server.sql('UPDATE users SET last_login=?, created_at=? WHERE id=?', (long_ago, long_ago, gone.user['id']))
        admin.post('/api/admin/retention', {'run_now': True})
        self.server.sql('UPDATE users SET inactive_warned_at=? WHERE id=?', ((dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=40)).isoformat(timespec='seconds'), gone.user['id']))
        admin.post('/api/admin/retention', {'run_now': True})
        self.assertEqual(self.server.sql('SELECT fullname FROM users WHERE id=?', (gone.user['id'],))[0]['fullname'], 'Usuario eliminado')
        self.assertFalse(self.server.sql('SELECT 1 FROM info_requests WHERE user_id=?', (gone.user['id'],)))
        self.assertEqual(self.server.sql('SELECT contact_name,contact_email FROM bookings WHERE user_id=?', (gone.user['id'],))[0]['contact_name'], None)


class CopiasYConexiones(unittest.TestCase):
    """V11.2.2, V13.3.2, V15.3.2 y V15.3.4 sin servidor."""

    def test_v11_2_2_the_old_backup_key_still_opens_old_copies(self):
        from wod import backup
        with tempfile.TemporaryDirectory() as d:
            f = Path(d) / 'copia.sqlite3'; f.write_bytes(b'SQLite format 3\x00' + b'datos' * 1000)
            old_env = {k: os.environ.get(k) for k in ('WOD_BACKUP_KEY', 'WOD_BACKUP_KEY_OLD')}
            try:
                os.environ['WOD_BACKUP_KEY'] = 'a' * 40; os.environ.pop('WOD_BACKUP_KEY_OLD', None)
                backup.encrypt_file(f)
                os.environ['WOD_BACKUP_KEY'] = 'b' * 40
                with self.assertRaises(RuntimeError): backup._plain_copy(f, Path(d) / 'x')
                os.environ['WOD_BACKUP_KEY_OLD'] = 'a' * 40
                backup._plain_copy(f, Path(d) / 'y'); self.assertTrue((Path(d) / 'y').read_bytes().startswith(b'SQLite format 3'))
            finally:
                for k, v in old_env.items():
                    if v is None: os.environ.pop(k, None)
                    else: os.environ[k] = v

    def test_v13_3_2_the_offsite_copy_gets_no_keys(self):
        from wod import backup
        with tempfile.TemporaryDirectory() as d:
            out = Path(d) / 'env.txt'; script = Path(d) / 'copia.py'
            script.write_text(f"import os,sys; open({str(out)!r},'w').write(' '.join(sorted(os.environ)))")
            old = {k: os.environ.get(k) for k in ('WOD_BACKUP_COMMAND', 'STRIPE_SECRET_KEY')}
            try:
                os.environ['WOD_BACKUP_COMMAND'] = f'{sys.executable} {script}'; os.environ['STRIPE_SECRET_KEY'] = 'sk_test_no_debe_salir'
                self.assertEqual(backup.ship(Path(d) / 'copia.sqlite3'), '')
                names = out.read_text().split()
                self.assertIn('PATH', names); self.assertNotIn('STRIPE_SECRET_KEY', names); self.assertNotIn('WOD_BACKUP_COMMAND', names)
            finally:
                for k, v in old.items():
                    if v is None: os.environ.pop(k, None)
                    else: os.environ[k] = v

    def test_v15_3_2_no_redirects_for_our_own_calls(self):
        import http.server, threading, urllib.error, urllib.request
        from wod import remoto

        class R(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                self.send_response(302); self.send_header('Location', 'http://127.0.0.1:9/robado'); self.end_headers()
            def log_message(self, *a): pass
        srv = http.server.HTTPServer(('127.0.0.1', 0), R); threading.Thread(target=srv.handle_request, daemon=True).start()
        with self.assertRaises(urllib.error.HTTPError) as e:
            remoto.open_once(urllib.request.Request(f'http://127.0.0.1:{srv.server_port}/x', headers={'Authorization': 'Bearer secreto'}), timeout=5)
        self.assertEqual(e.exception.code, 302); srv.server_close()

    def test_v15_3_4_x_real_ip_must_be_an_address(self):
        from wod import security as wsec
        os.environ['WOD_TRUSTED_PROXIES'] = '127.0.0.1'
        try:
            self.assertEqual(wsec.client_ip('127.0.0.1', {'X-Real-IP': 'no-soy-una-ip'}), '127.0.0.1')
            self.assertEqual(wsec.client_ip('127.0.0.1', {'X-Real-IP': '203.0.113.7'}), '203.0.113.7')
        finally:
            os.environ.pop('WOD_TRUSTED_PROXIES', None)


if __name__ == '__main__':
    unittest.main()
