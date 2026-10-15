"""v50.57 · Revisión general (15/10/2026), Bloque 4.1: la contraseña solo para ver datos sensibles.

- Entrar en el Centro de control y gestionar la web (puntos, destinos, plantillas, centros, experiencias, estadísticas,
  QR…) no pide nada más: ni contraseña ni motivo.
- Ver datos personales o sensibles (reservas con datos de clientes, documentos, pagos con datos personales, correos
  enviados, exportaciones con datos personales, el informe DAC7, correos y teléfonos completos) pide confirmar la
  contraseña, o el código de verificación si la cuenta lo tiene, y un motivo.
- Una confirmación vale 15 minutos (configurable) para todo lo sensible; pasado ese tiempo se vuelve a pedir.
- Cada acceso sensible queda registrado con el motivo.
- Por defecto, las reservas de los centros se ven solo en cifras, sin datos de clientes.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ServerTestCase, Client  # noqa: E402

DAY = (dt.date.today() + dt.timedelta(days=6)).isoformat()
ADMIN_PW = 'admin-seguro-2026'


class DatosSensibles(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'sens')
        cls.diver = t.make_diver('sens')
        cid = cls.center.user['center_id']; cls.cid = cid
        sid = cls.center.post('/api/provider-services', {'title': 'Inmersión en las Medas', 'price': 55, 'booking_mode': 'request', 'max_participants': 8}).json['id']
        slot = cls.center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': DAY, 'slot_time': '09:30', 'spots_total': 8}).json['slot_id']
        r = cls.diver.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': 2})
        assert r.status == 200, r.json
        cls.bid = r.json['id']
        assert cls.center.post(f'/api/bookings/{cls.bid}/status', {'status': 'confirmed'}).status == 200

    def fresh_admin(self):
        """An administrator who has just logged in: no confirmation, no reason header."""
        a = Client(self.server); a.admin_reason = None
        assert a.login('admin', ADMIN_PW).status == 200
        return a

    def confirm(self, a, reason='Soporte: llamada del centro sens', password=ADMIN_PW):
        return a.post('/api/admin/confirm', {'password': password, 'reason': reason})

    # 1 · managing the web asks for nothing
    def test_entrar_y_gestionar_la_web_no_pide_nada(self):
        a = self.fresh_admin()
        for path in ('/api/me', '/api/dive-points', '/api/centers', '/api/admin/suggestions', '/api/admin/center-claims', '/api/admin/travel-experiences',
                     '/api/admin/audit', '/api/provider/reward-offers', '/api/admin/service-catalog', '/api/admin/qr', '/api/admin/bookings/summary',
                     '/api/admin/users', '/api/admin/settings'):
            r = a.get(path)
            self.assertEqual(r.status, 200, (path, r.json))
        r = a.post('/api/admin/travel-offers', {'title': 'Islas Medas', 'region': 'Girona', 'kind': 'Viaje', 'summary': 'Reserva marina'})
        self.assertEqual(r.status, 200, r.json)
        self.assertFalse(self.server.sql("SELECT 1 FROM audit_log WHERE action='admin_center_access' AND details LIKE '%travel-offers%'"))

    # 2 · personal data asks for the password (or the code) and a reason
    def test_datos_personales_piden_confirmar(self):
        a = self.fresh_admin()
        for path in ('/api/bookings', f'/api/bookings/{self.bid}', '/api/admin/payments', '/api/admin/emails', '/api/admin/dac7?year=2025',
                     '/api/exportar/pagos?periodo=todo', '/api/exportar/dac7?anio=2025', '/api/exportar/actividad?periodo=todo'):
            r = a.get(path)
            self.assertEqual(r.status, 403, path)
            self.assertTrue(r.json.get('admin_confirm_required'), (path, r.json))
        self.assertEqual(a.get('/api/exportar/cuotas?periodo=todo').status, 200)            # no personal data: no confirmation
        self.assertEqual(a.get('/api/exportar/reservas_centros?periodo=todo').status, 200)

    def test_confirmar_con_la_contrasena_y_motivo(self):
        a = self.fresh_admin()
        self.assertEqual(self.confirm(a, password='no-es-esta').status, 403)
        r = self.confirm(a, reason='abc'); self.assertEqual(r.status, 400, r.json)            # a reason is needed
        r = self.confirm(a); self.assertEqual(r.status, 200, r.json)
        self.assertEqual(r.json['minutes'], 15)
        self.assertAlmostEqual(r.json['until_ts'], time.time() + 15 * 60, delta=30)
        b = a.get(f'/api/bookings/{self.bid}'); self.assertEqual(b.status, 200, b.json)
        self.assertEqual(a.get('/api/admin/payments').status, 200)
        st = a.get('/api/admin/confirm').json; self.assertTrue(st['active']); self.assertIn('llamada', st['reason'])
        # each access is logged with the reason given when confirming
        rows = self.server.sql("SELECT details FROM audit_log WHERE action='admin_center_access' ORDER BY id DESC LIMIT 5")
        self.assertTrue(any('Soporte: llamada del centro sens' in (r['details'] or '') and f'/api/bookings/{self.bid}' in (r['details'] or '') for r in rows), rows)
        conf = self.server.sql("SELECT details FROM audit_log WHERE action='admin_sensitive_confirmed' ORDER BY id DESC LIMIT 1")
        self.assertIn('Soporte', conf[0]['details'])
        # «Cerrar ahora»
        self.assertEqual(a.post('/api/admin/confirm/end').status, 200)
        self.assertEqual(a.get(f'/api/bookings/{self.bid}').status, 403)

    def test_la_confirmacion_caduca(self):
        a = self.fresh_admin(); self.assertEqual(self.confirm(a).status, 200)
        self.server.sql('UPDATE sessions SET admin_confirmed_until=? WHERE admin_confirmed_until IS NOT NULL', (time.time() - 1,))
        r = a.get('/api/bookings'); self.assertEqual(r.status, 403); self.assertTrue(r.json.get('admin_confirm_required'))

    def test_minutos_configurables(self):
        a = self.fresh_admin()
        r = a.post('/api/admin/settings', {'admin_confirm_minutes': 30}); self.assertEqual(r.status, 200, r.json)
        try:
            self.assertEqual(a.get('/api/admin/settings').json['admin_confirm_minutes'], 30)
            r = self.confirm(a); self.assertEqual(r.json['minutes'], 30)
            self.assertAlmostEqual(r.json['until_ts'], time.time() + 30 * 60, delta=30)
            self.assertEqual(a.post('/api/admin/settings', {'admin_confirm_minutes': 1}).status, 400)       # 5 to 120 minutes
        finally:
            a.post('/api/admin/settings', {'admin_confirm_minutes': 15})

    def test_con_doble_factor_pide_el_codigo(self):
        a = self.fresh_admin()
        self.server.sql("UPDATE users SET totp_enabled=1,totp_secret='JBSWY3DPEHPK3PXP' WHERE username='admin'")
        try:
            r = self.confirm(a); self.assertEqual(r.status, 403, r.json)                         # the password alone is not enough
            self.assertIn('código', r.json['error'])
            st = a.get('/api/admin/confirm').json; self.assertEqual(st['method'], 'code')
        finally:
            self.server.sql("UPDATE users SET totp_enabled=0,totp_secret=NULL WHERE username='admin'")

    # 3 · bookings of the centres: in figures by default
    def test_reservas_en_cifras_sin_datos_de_clientes(self):
        a = self.fresh_admin()
        r = a.get('/api/admin/bookings/summary?periodo=todo'); self.assertEqual(r.status, 200, r.json)
        raw = json.dumps(r.json, ensure_ascii=False)
        for personal in ('Pérez', 'sens@diver', 'diver_sens', '@'):
            self.assertNotIn(personal, raw)
        row = [c for c in r.json['providers'] if c['name'] == 'Centro sens'][0]
        self.assertEqual(row['bookings'], 1); self.assertEqual(row['confirmed'], 1); self.assertEqual(row['divers'], 2)
        self.assertGreaterEqual(r.json['totals']['bookings'], 1)
        self.assertTrue(r.json['totals']['by_mode']); self.assertTrue(r.json['totals']['by_channel'])

    # 4 · emails and phones in full only with the confirmation
    def test_correos_completos_solo_con_confirmacion(self):
        a = self.fresh_admin()
        items = a.get('/api/admin/users').json
        self.assertTrue(items['masked'])
        mine = [u for u in items['items'] if u['username'] == 'diver_sens'][0]
        self.assertNotEqual(mine['email'], 'sens@diver.example.org'); self.assertTrue(mine['email'].endswith('@diver.example.org'))
        self.confirm(a)
        items = a.get('/api/admin/users').json
        self.assertFalse(items['masked'])
        self.assertIn('sens@diver.example.org', [u['email'] for u in items['items']])

    # 5 · the centre itself never needs any of this
    def test_el_centro_ve_lo_suyo_sin_confirmar(self):
        self.assertEqual(self.center.get(f'/api/bookings/{self.bid}').status, 200)
        self.assertEqual(self.center.get('/api/exportar/reservas?periodo=todo').status, 200)


if __name__ == '__main__':
    unittest.main()
