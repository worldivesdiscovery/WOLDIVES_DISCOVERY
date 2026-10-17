"""v50.47 · parte C: cambiar la clave de los datos cifrados (scripts/seguridad/rotar_clave_datos.py).

Con la clave A se guardan el teléfono de un buceador y la conexión de WhatsApp de un centro. Con el servidor parado se
pone la clave B (y A como antigua) y se ejecuta el script: hace una copia previa, todo se vuelve a cifrar con B, las
huellas cambian y, ya solo con la clave B, el servidor lee el teléfono, lo encuentra por su huella y reconoce el número
de WhatsApp del centro. Sin la clave antigua, el script no cambia nada."""
import subprocess
import sys
import unittest

from helpers import ROOT, Server, Client, cifrado_for
from meta_mock import MetaMock

KEY_A = 'clave-de-datos-A-de-las-pruebas-0123456789'
KEY_B = 'clave-de-datos-B-de-las-pruebas-9876543210'
SCRIPT = ROOT / 'scripts' / 'seguridad' / 'rotar_clave_datos.py'


class DataKeyRotation(unittest.TestCase):
    def rotate(self, srv, *args, **env):
        e = dict(srv.env, **env)
        return subprocess.run([sys.executable, str(SCRIPT), *args], env=e, cwd=str(ROOT), capture_output=True, text=True, timeout=120)

    def test_rotation(self):
        meta = MetaMock(); meta.add_business('codeR', 'wabaR', [('pnidR', '+34 600 000 333')])
        srv = Server({**meta.env(), 'WOD_DATA_KEY': KEY_A, 'WOD_BACKUP_DIR': ''}).start()
        try:
            from helpers import ServerTestCase
            t = ServerTestCase('run'); t.server = srv
            admin = t.make_admin(); center = t.make_center(admin, 'rota')
            self.assertEqual(center.post('/api/whatsapp/connect', {'code': 'codeR', 'waba_id': 'wabaR', 'phone_number_id': 'pnidR'}).status, 200)
            d = t.make_diver('rota')
            self.assertEqual(d.post('/api/account/profile', {'phone': '+34 611 222 333', 'wa_consent': True}).status, 200)
            before = srv.sql('SELECT phone, phone_hash FROM user_profiles WHERE user_id=?', (d.user['id'],))[0]
            raw0 = self.raw(srv, "SELECT phone FROM user_profiles WHERE user_id=?", (d.user['id'],))
            wa0 = self.raw(srv, 'SELECT pnid_hash FROM whatsapp_accounts')
            srv.stop(cleanup=False)

            # Without the old key nothing changes.
            r = self.rotate(srv, '--aplicar', WOD_DATA_KEY=KEY_B, WOD_DATA_KEY_OLD='')
            self.assertEqual(r.returncode, 2, r.stdout + r.stderr)
            self.assertEqual(self.raw(srv, "SELECT phone FROM user_profiles WHERE user_id=?", (d.user['id'],)), raw0)
            # Check only, then apply.
            r = self.rotate(srv, WOD_DATA_KEY=KEY_B, WOD_DATA_KEY_OLD=KEY_A)
            self.assertEqual(r.returncode, 0, r.stderr); self.assertIn('sin cambios', r.stdout)
            r = self.rotate(srv, '--aplicar', WOD_DATA_KEY=KEY_B, WOD_DATA_KEY_OLD=KEY_A)
            self.assertEqual(r.returncode, 0, r.stdout + r.stderr)
            self.assertTrue(list((srv.tmp / 'backups').glob('*antes-rotar-clave*.sqlite3')), r.stdout)
            self.assertNotEqual(self.raw(srv, "SELECT phone FROM user_profiles WHERE user_id=?", (d.user['id'],)), raw0)
            self.assertNotEqual(self.raw(srv, 'SELECT pnid_hash FROM whatsapp_accounts'), wa0)

            # Only the new key from now on.
            srv.env.update({'WOD_DATA_KEY': KEY_B}); srv.env.pop('WOD_DATA_KEY_OLD', None)
            srv.start()
            after = srv.sql('SELECT phone, phone_hash FROM user_profiles WHERE user_id=?', (d.user['id'],))[0]
            self.assertEqual(after['phone'], before['phone'])
            self.assertNotEqual(after['phone_hash'], before['phone_hash'])
            self.assertEqual(after['phone_hash'], cifrado_for(srv.env).fingerprint('+34611222333'))
            c2 = Client(srv); self.assertEqual(c2.login('center_rota').status, 200)
            self.assertTrue(c2.get('/api/whatsapp').json.get('connected'), 'el centro sigue conectado y su número se reconoce')
            # The check before every send (notice_recheck) compares this fingerprint with the credentials: it must match.
            self.assertEqual(self.raw(srv, 'SELECT pnid_hash FROM whatsapp_accounts'), [(cifrado_for(srv.env).keyed_hash('pnid', 'pnidR'),)])
        finally:
            srv.stop(); meta.stop()

    @staticmethod
    def raw(srv, q, args=()):
        import sqlite3
        c = sqlite3.connect(srv.db)
        try: return [tuple(r) for r in c.execute(q, args).fetchall()]
        finally: c.close()


if __name__ == '__main__':
    unittest.main()
