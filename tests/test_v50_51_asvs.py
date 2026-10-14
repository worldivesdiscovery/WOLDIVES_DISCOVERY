"""v50.51 · Correcciones de la revisión OWASP ASVS 5.0, nivel 2 (docs/auditoria/v50.51/asvs-5.0-nivel2.md).
Cada prueba nombra el requisito que comprueba."""
import concurrent.futures as cf
import datetime as dt
import os
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


if __name__ == '__main__':
    unittest.main()
