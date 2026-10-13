"""v50.48 · App móvil en 3 módulos, Tanda 1 (Capacitor): what the server does for the app.

- wod.movil (pure): the two app schemes, the page that sends the phone back into the app after paying, the date window
  of «Salidas con plazas cerca de ti» and the bug reports of WORLDIVES Pruebas.
- /api/salidas-cercanas: next departures with free places of public centres, closest first with a position; full,
  past and hidden (centre not verified) departures are left out; the windows hoy / mañana / finde.
- Paying from the app: Stripe gets /app/vuelta?esquema=… as success and cancel addresses (only our two schemes).
- Test environment only: quick entry with a test account and «Reportar fallo». Outside it both addresses are 404.
"""
from __future__ import annotations

import base64
import datetime as dt
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from wod import movil as wmovil  # noqa: E402

from helpers import Client, ServerTestCase  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402

JPEG = base64.b64encode(b'\xff\xd8\xff\xe0' + b'\x00' * 64).decode()


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


class MovilUnits(unittest.TestCase):
    def test_schemes_and_return_page(self):
        self.assertEqual(wmovil.app_scheme('com.worldives.app.pruebas'), 'com.worldives.app.pruebas')
        for bad in ('javascript', 'com.otra.app', 'https', '', None):
            self.assertIsNone(wmovil.app_scheme(bad))
        ok, ko = wmovil.return_urls('https://worldives.com', 'com.worldives.app', 41)
        self.assertEqual(ok, 'https://worldives.com/app/vuelta?esquema=com.worldives.app&session_id={CHECKOUT_SESSION_ID}')
        self.assertIn('pago=cancelado', ko); self.assertIn('reserva=41', ko)
        page = wmovil.return_page('com.worldives.app', {'session_id': 'cs_test_1', 'evil': '"><script>', 'pago': '<x>'})
        self.assertIn('com.worldives.app://pago?session_id=cs_test_1', page)
        self.assertIn('package=com.worldives.app;end', page)
        self.assertNotIn('<script', page); self.assertNotIn('evil', page); self.assertNotIn('<x>', page)

    def test_departures_window(self):
        tue = dt.date(2026, 10, 13)
        self.assertEqual(wmovil.departures_window('hoy', tue), (tue, tue))
        self.assertEqual(wmovil.departures_window('manana', tue), (dt.date(2026, 10, 14),) * 2)
        self.assertEqual(wmovil.departures_window('finde', tue), (dt.date(2026, 10, 17), dt.date(2026, 10, 18)))
        self.assertEqual(wmovil.departures_window('finde', dt.date(2026, 10, 17)), (dt.date(2026, 10, 17), dt.date(2026, 10, 18)))
        self.assertEqual(wmovil.departures_window('finde', dt.date(2026, 10, 18)), (dt.date(2026, 10, 18), dt.date(2026, 10, 18)))
        self.assertEqual(wmovil.departures_window('', tue), (tue, dt.date(2026, 10, 27)))

    def test_bug_report_fields(self):
        report, image = wmovil.clean_report({'texto': 'x' * 5000, 'pantalla': 'Inicio', 'captura': 'data:image/jpeg;base64,' + JPEG})
        self.assertEqual(len(report['texto']), 3000); self.assertEqual(image[1], 'jpg')
        _, image = wmovil.clean_report({'texto': 'sin captura válida', 'captura': 'data:image/jpeg;base64,' + base64.b64encode(b'GIF89a').decode()})
        self.assertIsNone(image)   # not a real JPEG: ignored
        with self.assertRaises(ValueError): wmovil.clean_report({'texto': '  '})


class AppServer(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.near = t.make_center(cls.admin, 'cerca', phone='+34 600 000 011')
        cls.far = t.make_center(cls.admin, 'lejos', phone='+34 600 000 012')
        for c, lat, lon in ((cls.near, 38.79, 0.18), (cls.far, 41.98, 3.22)):   # Xàbia and l'Estartit
            cls.server.sql('UPDATE centers SET latitude=?, longitude=?, stripe_account_id=?, stripe_charges_enabled=1, stripe_payouts_enabled=1 WHERE id=?',
                           (lat, lon, f"acct_{c.user['center_id']}", c.user['center_id']))
        cls.diver = t.make_diver('movil1')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def slot(self, center, when, time='10:00', spots=6, mode='payment', price=45):
        sid = center.post('/api/provider-services', {'title': f'Inmersión {when} {time} {mode}', 'price': price, 'booking_mode': mode}).json['id']
        r = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': day(when), 'slot_time': time, 'spots_total': spots})
        self.assertEqual(r.status, 200, r)
        return sid, r.json['slot_id']

    def test_salidas_cercanas(self):
        _, a = self.slot(self.near, 1, '09:00')
        _, b = self.slot(self.far, 1, '08:00', mode='request', price=60)
        _, full = self.slot(self.near, 1, '11:00', spots=2)
        self.server.sql('UPDATE service_slots SET spots_available=0 WHERE id=?', (full,))
        _, later = self.slot(self.near, 10)
        _, outside = self.slot(self.near, 20)
        anon = Client(self.server, origin=None)
        items = anon.get('/api/salidas-cercanas?cuando=manana').json['items']
        ids = [x['slot_id'] for x in items]
        self.assertEqual(ids[:2], [b, a])                        # no position: by date and hour
        self.assertNotIn(full, ids); self.assertNotIn(later, ids)
        x = [i for i in items if i['slot_id'] == a][0]
        self.assertEqual((x['price'], x['spots_left'], x['booking_mode'], x['instant']), (45, 6, 'payment', True))
        self.assertEqual(x['provider_name'], 'Centro cerca')
        items = anon.get('/api/salidas-cercanas?cuando=manana&lat=38.80&lon=0.17').json['items']
        self.assertEqual([i['slot_id'] for i in items][:2], [a, b])     # with a position: the closest first
        self.assertLess(items[0]['distance_km'], 5); self.assertGreater(items[1]['distance_km'], 300)
        default = [i['slot_id'] for i in anon.get('/api/salidas-cercanas').json['items']]
        self.assertIn(later, default); self.assertNotIn(outside, default)   # default: the next 14 days
        # a centre that is no longer public disappears from the list
        self.server.sql("UPDATE centers SET verification_status='pending' WHERE id=?", (self.far.user['center_id'],))
        try:
            self.assertNotIn(b, [i['slot_id'] for i in anon.get('/api/salidas-cercanas?cuando=manana').json['items']])
        finally:
            self.server.sql("UPDATE centers SET verification_status='verified' WHERE id=?", (self.far.user['center_id'],))
        self.assertEqual(anon.get('/api/salidas-cercanas?lat=999&lon=1').status, 200)   # a wrong position is ignored

    def test_paying_from_the_app_comes_back_to_the_app(self):
        sid, slot = self.slot(self.near, 3, '12:00')
        r = self.diver.post('/api/bookings', {'center_id': self.near.user['center_id'], 'service_id': sid, 'slot_id': slot, 'participants': 1, 'app': 'com.worldives.app.pruebas'})
        self.assertEqual(r.status, 200, r); self.assertTrue(r.json['checkout_url'])
        sess = [c for c in self.stripe.calls if c['path'] == '/v1/checkout/sessions' and c['method'] == 'POST'][-1]['params']
        self.assertTrue(sess['success_url'].startswith(f'{self.server.base}/app/vuelta?esquema=com.worldives.app.pruebas&session_id='), sess['success_url'])
        self.assertIn('pago=cancelado', sess['cancel_url'])
        # a scheme that is not ours is ignored: the web addresses as always
        sid2, slot2 = self.slot(self.near, 3, '13:00')
        self.diver.post('/api/bookings', {'center_id': self.near.user['center_id'], 'service_id': sid2, 'slot_id': slot2, 'participants': 1, 'app': 'intent://x'})
        sess = [c for c in self.stripe.calls if c['path'] == '/v1/checkout/sessions' and c['method'] == 'POST'][-1]['params']
        self.assertTrue(sess['success_url'].startswith(f'{self.server.base}/#/pago-ok'), sess['success_url'])
        page = Client(self.server, origin=None).get('/app/vuelta?esquema=com.worldives.app&session_id=cs_test_9')
        self.assertEqual(page.status, 200); self.assertIn(b'com.worldives.app://pago?session_id=cs_test_9', page.body)
        self.assertEqual(Client(self.server, origin=None).get('/app/vuelta?esquema=javascript&session_id=1').status, 404)

    def test_test_addresses_do_not_exist_outside_the_test_environment(self):
        self.assertEqual(self.client().post('/api/pruebas/entrar', {'cuenta': 'probador.prueba'}).status, 404)
        self.assertEqual(self.client().post('/api/pruebas/fallo', {'texto': 'hola'}).status, 404)


class AppTestEnvironment(ServerTestCase):
    extra_env = {'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        # Registration is closed in the test environment: the account is made with the command line, as the demo does.
        res = cls.server.run_cli('--create-admin', '--email', 'probador@example.org', '--username', 'probador', '--name', 'Probador', env={'WOD_ADMIN_PASSWORD': 'probador-seguro-2026'})
        assert res.returncode == 0, res.stdout + res.stderr
        cls.server.sql("UPDATE users SET username='probador.prueba', role='recreational' WHERE username='probador'")
        cls.tester = cls('run').client(); assert cls.tester.post('/api/pruebas/entrar', {'cuenta': 'probador.prueba'}).status == 200

    def test_quick_entry_with_a_test_account(self):
        c = self.client()
        r = c.post('/api/pruebas/entrar', {'cuenta': 'probador.prueba'})
        self.assertEqual(r.status, 200, r); self.assertEqual(c.me()['user']['username'], 'probador.prueba')
        self.assertEqual(self.client().post('/api/pruebas/entrar', {'cuenta': 'nadie.prueba'}).status, 404)
        self.assertEqual(self.client().post('/api/pruebas/entrar', {'cuenta': 'admin'}).status, 400)   # only *.prueba accounts
        self.assertEqual(Client(self.server, origin='https://otra-web.example').post('/api/pruebas/entrar', {'cuenta': 'probador.prueba'}).status, 403)

    def test_bug_report_is_saved_in_the_test_folder(self):
        r = self.tester.post('/api/pruebas/fallo', {'texto': 'El contador de Solicitudes no baja', 'pantalla': 'Centro · Hoy', 'version': '1.0.7 (7)',
                                                    'movil': 'Android 15', 'captura': 'data:image/jpeg;base64,' + JPEG})
        self.assertEqual(r.status, 200, r)
        folder = Path(self.server.db).parent / 'fallos'
        saved = json.loads((folder / f"{r.json['id']}.json").read_text(encoding='utf-8'))
        self.assertEqual((saved['pantalla'], saved['cuenta']), ('Centro · Hoy', 'probador.prueba'))
        self.assertTrue((folder / saved['captura']).exists())
        self.assertEqual(self.client().post('/api/pruebas/fallo', {'texto': ''}).status, 400)


if __name__ == '__main__':
    unittest.main()
