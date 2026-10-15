"""v50.55 · Encargo 2: seguridad de la app WORLDIVES PRO (servidor).

  · The app gets a refresh token for its device (never the web); its access session lasts 15 minutes and is renewed
    with that token; a device session lasts 30 days at most.
  · «Dispositivos conectados»: web sessions and app devices; «Cerrar sesión» in one, and «Cerrar todas menos esta».
  · Closing a device from the web: the phone's next renewal answers «revoked» (the app deletes its data).
  · Changing the password closes every other session and device.
  · A sign-in from a new device sends an e-mail.
  · The owner of a centre closes the sessions of his team.
The phone side (fingerprint / PIN, lock after 5 minutes, 5 failures, encrypted offline data, recents) is tested in
the emulator: movil/scripts/emulador.py."""
import re
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import Client, ServerTestCase  # noqa: E402

APP_UA = 'Mozilla/5.0 (Linux; Android 14; Pixel 7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Mobile Safari/537.36 WorldivesApp/1.0'
WEB_UA = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/129.0 Safari/537.36'
PW = 'buceo-seguro-2026'


class UAClient(Client):
    def __init__(self, server, ua):
        super().__init__(server); self.ua = ua

    def request(self, method, path, data=None, headers=None, **kw):
        h = dict(headers or {}); h.setdefault('User-Agent', self.ua)
        return super().request(method, path, data, headers=h, **kw)


def device(key='instalacion-0001-abcdef'):
    return {'platform': 'android', 'model': 'Pixel 7', 'os': '14', 'app_version': '1.0.0', 'device_key': key}


class Devices(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'segcentro', phone='+34 600 700 001')

    def account(self, tag):
        c = UAClient(self.server, WEB_UA)
        self.assertEqual(c.register(f'Persona {tag}', f'{tag}@seg.example.org', f'seg_{tag}').status, 200)
        c.user = c.me()['user']
        return c

    def app_login(self, tag, key='instalacion-0001-abcdef', password=PW):
        a = UAClient(self.server, APP_UA)
        r = a.post('/api/auth/login', {'login': f'seg_{tag}', 'password': password, 'app_device': device(key)})
        return a, r

    def emails(self, uid, template='new_device_login'):
        return self.server.sql('SELECT * FROM email_outbox WHERE template=? AND to_email=(SELECT email FROM users WHERE id=?)', (template, uid))

    # ------------------------------------------------------------------ tokens
    def test_only_the_app_gets_a_refresh_token(self):
        web = self.account('soloapp')
        r = web.post('/api/auth/login', {'login': 'seg_soloapp', 'password': PW, 'app_device': device()})
        self.assertEqual(r.status, 200); self.assertNotIn('refresh_token', r.json)
        a, r = self.app_login('soloapp')
        self.assertEqual(r.status, 200, r)
        self.assertGreaterEqual(len(r.json['refresh_token']), 40); self.assertEqual(r.json['access_ttl'], 900)
        row = self.server.sql('SELECT * FROM device_sessions WHERE id=?', (r.json['device_id'],))[0]
        self.assertNotEqual(row['refresh_hash'], r.json['refresh_token'])                       # only its SHA-256 is kept
        self.assertAlmostEqual(row['expires_at'] - row['created_at'], 30 * 86400, delta=5)      # 30 days at most
        s = self.server.sql('SELECT expires_at,created_at FROM sessions WHERE device_id=?', (r.json['device_id'],))[0]
        self.assertAlmostEqual(s['expires_at'] - s['created_at'], 900, delta=5)                 # access: 15 minutes
        # without an installation id, no device session
        b = UAClient(self.server, APP_UA)
        self.assertNotIn('refresh_token', b.post('/api/auth/login', {'login': 'seg_soloapp', 'password': PW, 'app_device': {'device_key': 'corto'}}).json)

    def test_access_expires_and_is_renewed(self):
        self.account('renueva')
        a, r = self.app_login('renueva')
        tok = r.json['refresh_token']
        self.assertTrue(a.me()['authenticated'])
        self.server.sql('UPDATE sessions SET expires_at=? WHERE device_id=?', (time.time() - 1, r.json['device_id']))
        self.assertFalse(a.me()['authenticated'])                                                # 15 minutes later
        r2 = a.post('/api/auth/refresh', {'refresh_token': tok})
        self.assertEqual((r2.status, r2.json['access_ttl']), (200, 900), r2)
        self.assertTrue(a.me()['authenticated'])
        self.assertEqual(len(self.server.sql('SELECT 1 FROM sessions WHERE device_id=?', (r.json['device_id'],))), 1)   # one access session per device
        # a wrong token is refused and counted
        self.assertEqual(UAClient(self.server, APP_UA).post('/api/auth/refresh', {'refresh_token': 'x' * 43}).json.get('revoked'), True)

    def test_thirty_days_at_most(self):
        self.account('caduca')
        a, r = self.app_login('caduca')
        self.server.sql('UPDATE device_sessions SET expires_at=? WHERE id=?', (time.time() - 1, r.json['device_id']))
        r2 = a.post('/api/auth/refresh', {'refresh_token': r.json['refresh_token']})
        self.assertEqual((r2.status, r2.json['revoked'], r2.json['reason']), (401, True, 'expired'))

    # ------------------------------------------------------------------ «Dispositivos conectados»
    def test_device_list_and_remote_close(self):
        web = self.account('lista')
        a, r = self.app_login('lista')
        items = web.get('/api/account/devices').json['items']
        kinds = {i['kind'] for i in items}
        self.assertEqual(kinds, {'web', 'app'})
        app = [i for i in items if i['kind'] == 'app'][0]
        self.assertEqual((app['device'], app['system'], app['current']), ('App WORLDIVES · Pixel 7', 'Android 14', False))
        self.assertTrue(app['last_seen']); self.assertIn('city', app)
        me = [i for i in items if i['current']][0]
        self.assertEqual(me['kind'], 'web'); self.assertIn('Chrome', me['device']); self.assertEqual(me['system'], 'Windows')
        self.assertEqual(web.post('/api/account/devices/close', {'id': me['id']}).status, 400)   # not the one in use
        # close the phone from the web: its access session ends now and its renewal says «revoked»
        self.assertEqual(web.post('/api/account/devices/close', {'id': app['id']}).status, 200)
        self.assertFalse(a.me()['authenticated'])
        r2 = a.post('/api/auth/refresh', {'refresh_token': r.json['refresh_token']})
        self.assertEqual((r2.status, r2.json['revoked'], r2.json['reason']), (401, True, 'closed_by_owner'))
        self.assertNotIn('app', {i['kind'] for i in web.get('/api/account/devices').json['items']})
        # somebody else's device is never closed
        other = self.account('ajeno')
        self.assertEqual(other.post('/api/account/devices/close', {'id': app['id']}).status, 404)

    def test_close_all_but_this(self):
        web = self.account('todas')
        a, r = self.app_login('todas')
        b, rb = self.app_login('todas', key='instalacion-0002-ghijkl')
        r_ = web.post('/api/account/sessions/close', {'password': PW})
        self.assertEqual((r_.status, r_.json['closed']), (200, 2), r_)
        for c, tok in ((a, r.json['refresh_token']), (b, rb.json['refresh_token'])):
            self.assertEqual(c.post('/api/auth/refresh', {'refresh_token': tok}).status, 401)
        self.assertTrue(web.me()['authenticated'])

    def test_password_change_closes_the_others(self):
        web = self.account('clave')
        other_web = UAClient(self.server, WEB_UA); other_web.login('seg_clave')
        a, r = self.app_login('clave')
        self.assertTrue(other_web.me()['authenticated'])
        r_ = web.post('/api/account/password', {'current_password': PW, 'new_password': 'otra-clave-segura-2026'})
        self.assertEqual(r_.status, 200, r_)
        self.assertTrue(web.me()['authenticated']); self.assertFalse(other_web.me()['authenticated'])
        self.assertEqual(a.post('/api/auth/refresh', {'refresh_token': r.json['refresh_token']}).status, 401)
        # changed from the phone: the phone stays, the rest go
        a2, r2 = self.app_login('clave', key='instalacion-0003-mnopqr', password='otra-clave-segura-2026')
        web2 = UAClient(self.server, WEB_UA); web2.login('seg_clave', 'otra-clave-segura-2026')
        self.assertEqual(a2.post('/api/account/password', {'current_password': 'otra-clave-segura-2026', 'new_password': 'tercera-clave-segura-2026'}).status, 200)
        self.assertTrue(a2.me()['authenticated']); self.assertFalse(web2.me()['authenticated'])
        self.assertEqual(a2.post('/api/auth/refresh', {'refresh_token': r2.json['refresh_token']}).status, 200)

    def test_logout_and_forget_end_the_device(self):
        self.account('salir')
        a, r = self.app_login('salir')
        self.assertEqual(a.post('/api/auth/logout').status, 200)
        self.assertEqual(a.post('/api/auth/refresh', {'refresh_token': r.json['refresh_token']}).json['reason'], 'logout')
        b, rb = self.app_login('salir', key='instalacion-0004-stuvwx')
        x = UAClient(self.server, APP_UA)
        self.assertEqual(x.post('/api/auth/device/forget', {'device_id': rb.json['device_id'], 'device_key': 'otra-clave-instalacion'}).status, 200)
        self.assertEqual(b.post('/api/auth/refresh', {'refresh_token': rb.json['refresh_token']}).status, 200)   # a wrong id changes nothing
        x.post('/api/auth/device/forget', {'device_id': rb.json['device_id'], 'device_key': 'instalacion-0004-stuvwx', 'reason': 'unlock_failures'})
        r3 = b.post('/api/auth/refresh', {'refresh_token': rb.json['refresh_token']})
        self.assertEqual((r3.status, r3.json['reason']), (401, 'unlock_failures'))

    # ------------------------------------------------------------------ new device e-mail
    def test_new_device_email(self):
        web = self.account('aviso')
        uid = web.user['id']
        self.assertEqual(self.emails(uid), [])                       # the first device is only remembered
        web.post('/api/auth/logout'); web.login('seg_aviso')         # the same browser (its wd_dev cookie)
        self.assertEqual(self.emails(uid), [])
        self.app_login('aviso')                                      # a phone it never used
        mails = self.emails(uid)
        self.assertEqual(len(mails), 1)
        self.assertIn('App WORLDIVES · Pixel 7', mails[0]['text']); self.assertIn('Dispositivos conectados', mails[0]['text'])
        self.app_login('aviso')                                      # the same phone again: no new e-mail
        UAClient(self.server, WEB_UA).login('seg_aviso')             # another browser: one more
        self.assertEqual(len(self.emails(uid)), 2)

    # ------------------------------------------------------------------ the owner and his team
    def test_owner_closes_team_sessions(self):
        inv = self.center.post('/api/center/team/invite', {'email': 'empleado@seg.example.org', 'member_role': 'reception'})
        self.assertEqual(inv.status, 200, inv)
        emp = UAClient(self.server, WEB_UA)
        self.assertEqual(emp.register('Empleado Seg', 'empleado@seg.example.org', 'seg_empleado', account_type='recreational').status, 200)
        mail = self.server.sql("SELECT text FROM email_outbox WHERE template='team_invite' AND to_email='empleado@seg.example.org' ORDER BY id DESC LIMIT 1")[0]['text']
        tok = re.search(r'token=([A-Za-z0-9_-]+)', mail).group(1)
        j = emp.post('/api/team/join', {'token': tok})
        self.assertEqual(j.status, 200, j)
        emp.login('seg_empleado')
        ea, er = self.app_login('empleado')
        emp_id = emp.me()['user']['id']
        lst = self.center.get('/api/center/team/sessions').json['items']
        mine = [x for x in lst if x['user_id'] == emp_id][0]
        self.assertTrue(any(d['kind'] == 'app' for d in mine['devices']))
        self.assertEqual(emp.get('/api/center/team/sessions').status, 403)                       # only the owner
        self.assertEqual(emp.post('/api/center/team/sessions/close', {'user_id': self.center.user['id']}).status, 403)
        r = self.center.post('/api/center/team/sessions/close', {'user_id': emp_id})
        self.assertEqual(r.status, 200, r); self.assertGreaterEqual(r.json['closed'], 2)
        self.assertFalse(emp.me()['authenticated'])
        self.assertEqual(ea.post('/api/auth/refresh', {'refresh_token': er.json['refresh_token']}).status, 401)
        self.assertEqual(self.center.post('/api/center/team/sessions/close', {'user_id': 999999}).status, 404)

    def test_login_says_the_role_and_a_lost_session_is_marked(self):
        # the app decides with the role whether the lock is mandatory (centres and freelance) or optional (divers)
        self.account('rol')
        a, r = self.app_login('rol')
        self.assertEqual(r.json['role'], 'recreational')
        # an expired access session: the app sees «login_required», renews with its token and asks again
        self.server.sql('UPDATE sessions SET expires_at=1 WHERE device_id=?', (r.json['device_id'],))
        g = a.get('/api/account/devices')
        self.assertEqual(g.status, 403); self.assertIs(g.json.get('login_required'), True)
        self.assertEqual(a.post('/api/auth/refresh', {'refresh_token': r.json['refresh_token']}).status, 200)
        self.assertEqual(a.get('/api/account/devices').status, 200)
        # a session that exists but has no permission is not «login_required»
        self.assertNotIn('login_required', a.get('/api/admin/users').json or {})


if __name__ == '__main__':
    unittest.main(verbosity=2)
