"""v50.56 · Bloque 1, Parte E: API REST v1 de cada centro y avisos automáticos (webhooks).

Comprueba:
  - la clave se enseña una vez y se guarda solo su huella SHA-256; revocada deja de servir;
  - una clave de solo lectura no crea ni cancela; la clave de un centro no ve nada de otro;
  - servicios, disponibilidad en tiempo real (menos de 300 ms), reservas con filtros y páginas;
  - crear una reserva por la API pasa por la función única: precio del servidor, «Sin plazas» con 409, la misma
    petición 5 veces da 1 reserva y 1 cobro, cancelar libera la plaza;
  - errores claros (400, 401, 403, 404, 409, 415, 422, 429 con Retry-After);
  - los webhooks llegan firmados (HMAC-SHA256), se reintentan cuando fallan, quedan en el registro del panel y una
    firma falsa o antigua no se acepta.
"""
import hashlib
import http.server
import json
import sys
import threading
import time
from pathlib import Path

from helpers import ServerTestCase, Client
from stripe_mock import StripeMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from wod import canales as wch  # noqa: E402

FAR = '2099-12-31'


class Receiver:
    """The centre's server: keeps what arrives; answers 500 to the first n notices (to see the retries)."""
    def __init__(self, fail_first=1):
        self.got = []; self.fail = fail_first; me = self

        class H(http.server.BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get('Content-Length') or 0))
                me.got.append({'body': body, 'sig': self.headers.get('X-WORLDIVES-Signature'), 'event': self.headers.get('X-WORLDIVES-Event')})
                code = 500 if me.fail > 0 else 200
                me.fail -= 1
                self.send_response(code); self.send_header('Content-Length', '2'); self.end_headers(); self.wfile.write(b'ok')

            def log_message(self, *a):
                pass
        self.httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.url = f'http://127.0.0.1:{self.httpd.server_address[1]}/avisos'
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def stop(self):
        self.httpd.shutdown()


class Api(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = dict(cls.extra_env, STRIPE_SECRET_KEY='sk_test_mock', WOD_STRIPE_API_BASE=cls.stripe.base, WOD_WEBHOOK_ALLOW_LOCAL='1',
                             WOD_WEBHOOK_SECONDS='1', WOD_API_MAX_PER_MINUTE='400')
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.a = t.make_center(cls.admin, 'apia'); cls.b = t.make_center(cls.admin, 'apib', phone='+34 600 000 458')
        cls.cid = cls.a.user['center_id']; cls.cidb = cls.b.user['center_id']
        for c in (cls.cid, cls.cidb):
            cls.server.sql(f"UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_api{c}',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (c,))
        cls.req_sid = cls.a.post('/api/provider-services', {'title': 'Bautizo', 'price': 75, 'booking_mode': 'request', 'max_participants': 6}).json['id']
        cls.pay_sid = cls.a.post('/api/provider-services', {'title': 'Doble inmersión', 'price': 60, 'booking_mode': 'payment'}).json['id']
        cls.slots = [cls.a.post('/api/provider-services/slot', {'service_id': cls.req_sid, 'slot_date': f'2031-08-{d:02d}', 'slot_time': '10:00', 'spots_total': 4}).json['slot_id'] for d in range(1, 21)]
        cls.pay_slot = cls.a.post('/api/provider-services/slot', {'service_id': cls.pay_sid, 'slot_date': '2031-08-25', 'slot_time': '09:00', 'spots_total': 8}).json['slot_id']
        cls.b_sid = cls.b.post('/api/provider-services', {'title': 'Servicio del centro B', 'price': 40, 'booking_mode': 'request'}).json['id']
        r = cls.a.post('/api/provider/api-keys', {'action': 'create', 'name': 'Web', 'scope': 'write'}); cls.key_w = r.json['key']
        cls.key_r = cls.a.post('/api/provider/api-keys', {'action': 'create', 'name': 'Informes', 'scope': 'read'}).json['key']
        cls.key_b = cls.b.post('/api/provider/api-keys', {'action': 'create', 'name': 'B', 'scope': 'write'}).json['key']
        cls.n = 0

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def api(self, method, path, body=None, key=None, headers=None):
        h = {'Authorization': f'Bearer {key or self.key_w}', **(headers or {})}
        c = Client(self.server, origin=None)
        return c.request(method, path, data=body, headers=h) if method == 'POST' else c.get(path, headers=h)

    def booking(self, **kw):
        type(self).n += 1
        body = {'service_id': self.req_sid, 'departure_id': self.slots[self.n % 20], 'participants': 1, 'customer': {'name': f'Cliente API {self.n}', 'email': f'api{self.n}@example.org'}}
        body.update(kw)
        return self.api('POST', '/api/v1/bookings', body, headers={'Idempotency-Key': f'api-test-{self.n:06d}'})

    def test_clave_una_vez_y_hash(self):
        rows = self.server.sql('SELECT key_hash, prefix FROM api_keys')
        self.assertTrue(all(len(r['key_hash']) == 64 for r in rows))
        self.assertEqual(hashlib.sha256(self.key_w.encode()).hexdigest() in {r['key_hash'] for r in rows}, True)
        dump = json.dumps(self.server.sql('SELECT * FROM api_keys'))
        self.assertNotIn(self.key_w, dump)
        listing = self.a.get('/api/provider/api-keys').json['items']
        self.assertNotIn(self.key_w, json.dumps(listing)); self.assertTrue(all('key' not in x for x in listing))
        self.assertEqual(self.a.post('/api/provider/api-keys', {'action': 'revoke', 'id': self.server.sql("SELECT id FROM api_keys WHERE key_hash=?", (hashlib.sha256(self.key_b.encode()).hexdigest(),))[0]['id']}).status, 404)  # not his

    def test_errores_claros_y_autenticacion(self):
        r = Client(self.server, origin=None).get('/api/v1/services')
        self.assertEqual((r.status, r.json['error']['code']), (401, 'invalid_key'))
        self.assertEqual(self.api('GET', '/api/v1/services', key='wdk_' + 'x' * 43).status, 401)
        self.assertEqual(self.api('GET', '/api/v1/nada').json['error']['code'], 'not_found')
        r = Client(self.server, origin=None).request('POST', '/api/v1/bookings', raw=b'{no es json', content_type='application/json', headers={'Authorization': f'Bearer {self.key_w}'})
        self.assertEqual((r.status, r.json['error']['code']), (400, 'invalid_json'))
        r = Client(self.server, origin=None).request('POST', '/api/v1/bookings', raw=b'service_id=1', content_type='application/x-www-form-urlencoded', headers={'Authorization': f'Bearer {self.key_w}'})
        self.assertEqual(r.status, 415)
        r = self.api('POST', '/api/v1/bookings', {'service_id': self.req_sid, 'departure_id': self.slots[0], 'customer': {}})
        self.assertEqual((r.status, r.json['error']['code']), (422, 'invalid_request')); self.assertIn('nombre', r.json['error']['message'])
        r = self.api('POST', '/api/v1/bookings', {'departure_id': self.slots[0]})
        self.assertEqual(r.json['error']['code'], 'missing_service_id')
        # Never a cookie, never CSRF: the API answers without Origin, and a cookie session alone gives nothing
        self.assertEqual(self.a.get('/api/v1/services').status, 401)

    def test_solo_lectura_y_aislamiento(self):
        r = self.api('POST', '/api/v1/bookings', {'service_id': self.req_sid}, key=self.key_r)
        self.assertEqual((r.status, r.json['error']['code']), (403, 'read_only_key'))
        self.assertEqual(self.api('GET', '/api/v1/services', key=self.key_r).status, 200)
        bid = self.booking().json['booking']['id']
        self.assertEqual(self.api('GET', f'/api/v1/bookings/{bid}', key=self.key_b).status, 404)
        self.assertEqual(self.api('POST', f'/api/v1/bookings/{bid}/cancel', {}, key=self.key_b).status, 404)
        self.assertEqual(self.api('GET', f'/api/v1/services/{self.req_sid}', key=self.key_b).status, 404)
        self.assertEqual(self.api('GET', f'/api/v1/availability?service_id={self.req_sid}', key=self.key_b).status, 404)
        r = self.api('POST', '/api/v1/bookings', {'service_id': self.b_sid, 'date': '2031-08-05', 'customer': {'name': 'X'}})
        self.assertEqual(r.status, 422)
        ids = [x['id'] for x in self.api('GET', '/api/v1/bookings?limit=100', key=self.key_b).json['data']]
        self.assertNotIn(bid, ids)

    def test_servicios_disponibilidad_y_rapidez(self):
        s = self.api('GET', '/api/v1/services').json['data']
        self.assertEqual({x['title'] for x in s}, {'Bautizo', 'Doble inmersión'})
        self.assertEqual({x['timezone'] for x in s}, {'Europe/Madrid'})
        times = []
        for _ in range(5):
            t0 = time.perf_counter(); r = self.api('GET', f'/api/v1/availability?service_id={self.req_sid}&from=2031-08-01&to=2031-08-31'); times.append(time.perf_counter() - t0)
            self.assertEqual(r.status, 200)
        dep = r.json['departures']
        self.assertEqual(len(dep), 20); self.assertTrue(all(d['starts_at_utc'].endswith('Z') for d in dep))
        self.assertEqual(dep[0]['starts_at_utc'], '2031-08-01T08:00:00Z')            # 10:00 in Madrid (summer) = 08:00 UTC
        self.assertLess(sorted(times)[2], 0.300, times)
        self.assertEqual(self.api('GET', f'/api/v1/availability?service_id={self.req_sid}&from=2031-08-10&to=2031-08-01').status, 400)

    def test_reserva_precio_canal_y_sin_plazas(self):
        r = self.booking(participants=2, price=1, paid=True, status='confirmed')
        self.assertEqual(r.status, 201, r)
        b = r.json['booking']
        self.assertEqual((b['channel'], b['price'], b['status'], b['participants']), ('api', 150.0, 'requested', 2))
        row = self.server.sql('SELECT api_key_id, payment_status, source FROM bookings WHERE id=?', (b['id'],))[0]
        self.assertTrue(row['api_key_id']); self.assertNotEqual(row['payment_status'], 'paid'); self.assertEqual(row['source'], 'api')
        self.assertTrue(r.json['booking_url'].endswith(f"/mi-reserva/{b['id']}." + self.server.sql('SELECT public_token FROM bookings WHERE id=?', (b['id'],))[0]['public_token']))
        # «Pago al reservar»: the centre gets the payment link for its customer; spots held
        slot = self.a.post('/api/provider-services/slot', {'service_id': self.pay_sid, 'slot_date': '2031-08-26', 'slot_time': '09:00', 'spots_total': 8}).json['slot_id']
        full = self.api('POST', '/api/v1/bookings', {'service_id': self.pay_sid, 'departure_id': slot, 'participants': 8, 'customer': {'name': 'Grupo'}},
                        headers={'Idempotency-Key': 'api-pay-grupo-1'})
        self.assertEqual(full.status, 201, full); self.assertTrue(full.json['checkout_url'].startswith('https://')); self.assertTrue(full.json['payment_required'])
        r = self.api('POST', '/api/v1/bookings', {'service_id': self.pay_sid, 'departure_id': slot, 'participants': 1, 'customer': {'name': 'Tarde'}},
                     headers={'Idempotency-Key': 'api-pay-tarde-1'})
        self.assertEqual((r.status, r.json['error']['code']), (409, 'no_spots'))
        # Cancel from the API: the spots are free again for every channel
        r = self.api('POST', f"/api/v1/bookings/{full.json['booking']['id']}/cancel", {'reason': 'El grupo no viene'})
        self.assertEqual(r.status, 200, r); self.assertEqual(r.json['booking']['status'], 'expired')
        self.assertEqual(self.server.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot,))[0]['spots_available'], 8)

    def test_idempotencia_5_veces(self):
        body = {'service_id': self.pay_sid, 'departure_id': self.pay_slot, 'participants': 1, 'customer': {'name': 'Repetida', 'email': 'rep@example.org'}}
        res = [self.api('POST', '/api/v1/bookings', body, headers={'Idempotency-Key': 'api-idem-12345'}) for _ in range(5)]
        self.assertEqual([r.status for r in res], [201, 200, 200, 200, 200])
        ids = {r.json['booking']['id'] for r in res}
        self.assertEqual(len(ids), 1)
        self.assertEqual(self.server.sql('SELECT COUNT(*) n FROM payment_orders WHERE booking_id=?', (ids.pop(),))[0]['n'], 1)
        self.assertEqual(len({r.json['checkout_url'] for r in res}), 1)

    def test_listado_filtros_y_paginas(self):
        for _ in range(3): self.booking()
        r = self.api('GET', '/api/v1/bookings?limit=2&channel=api')
        self.assertEqual(len(r.json['data']), 2); self.assertTrue(r.json['has_more'])
        nxt = self.api('GET', f"/api/v1/bookings?limit=2&channel=api&starting_after={r.json['data'][-1]['id']}").json['data']
        self.assertTrue(all(x['id'] < r.json['data'][-1]['id'] for x in nxt))
        self.assertEqual(self.api('GET', '/api/v1/bookings?channel=fax').status, 400)
        self.assertEqual(self.api('GET', '/api/v1/bookings?from=ayer').status, 400)

    def test_webhooks_firmados_reintentos_y_registro(self):
        rec = Receiver(fail_first=1)
        try:
            r = self.a.post('/api/provider/webhooks', {'action': 'create', 'url': rec.url, 'events': ['booking.created', 'booking.cancelled']})
            self.assertEqual(r.status, 200, r); secret = r.json['secret']; wid = r.json['id']
            self.assertNotIn(secret, json.dumps(self.server.sql('SELECT * FROM webhook_endpoints')))      # stored encrypted
            self.assertEqual(self.a.post('/api/provider/webhooks', {'action': 'create', 'url': 'http://example.org/x'}).status, 400)
            bid = self.booking().json['booking']['id']
            for _ in range(80):
                if rec.got: break
                time.sleep(0.1)
            self.assertTrue(rec.got, 'el aviso no llegó')
            first = rec.got[0]
            self.assertEqual(first['event'], 'booking.created')
            self.assertTrue(wch.verify(secret, first['sig'], first['body']))
            self.assertFalse(wch.verify('whsk_falso', first['sig'], first['body']))
            self.assertFalse(wch.verify(secret, first['sig'], first['body'].replace(b'"requested"', b'"confirmed"')))
            ts = int(first['sig'].split(',')[0][2:]); self.assertFalse(wch.verify(secret, first['sig'], first['body'], now=ts + 600))
            payload = json.loads(first['body']); self.assertEqual(payload['data']['booking']['id'], bid); self.assertEqual(payload['type'], 'booking.created')
            d = self.server.sql('SELECT * FROM webhook_deliveries WHERE endpoint_id=? ORDER BY id', (wid,))[0]
            self.assertEqual((d['status'], d['attempts'], d['last_status']), ('pending', 1, 500))                  # the centre's server failed: retry later
            self.server.sql('UPDATE webhook_deliveries SET next_attempt_at=? WHERE id=?', (time.time() - 1, d['id']))   # «a minute later»
            for _ in range(80):
                if self.server.sql('SELECT status FROM webhook_deliveries WHERE id=?', (d['id'],))[0]['status'] == 'delivered': break
                time.sleep(0.1)
            d = self.server.sql('SELECT * FROM webhook_deliveries WHERE id=?', (d['id'],))[0]
            self.assertEqual((d['status'], d['attempts'], d['last_status']), ('delivered', 2, 200))
            # The same notice again and the same signature check
            self.assertTrue(wch.verify(secret, rec.got[1]['sig'], rec.got[1]['body']))
            # Not subscribed to «booking.confirmed»; subscribed to «booking.cancelled»
            self.api('POST', f'/api/v1/bookings/{bid}/cancel', {'reason': 'prueba'})
            for _ in range(80):
                if any(g['event'] == 'booking.cancelled' for g in rec.got): break
                time.sleep(0.1)
            self.assertTrue(any(g['event'] == 'booking.cancelled' for g in rec.got))
            log = self.a.get('/api/provider/webhooks').json
            self.assertTrue(any(x['event'] == 'booking.created' and x['status'] == 'delivered' for x in log['deliveries']))
            self.assertEqual(self.b.get('/api/provider/webhooks').json['deliveries'], [])                       # centre B sees nothing of A
            self.assertEqual(self.b.post('/api/provider/webhooks', {'action': 'delete', 'id': wid}).status, 404)
        finally:
            rec.stop()

    def test_limite_por_clave(self):
        key = self.a.post('/api/provider/api-keys', {'action': 'create', 'name': 'Prisa', 'scope': 'read'}).json['key']
        codes = [self.api('GET', '/api/v1/services', key=key).status for _ in range(401)]
        self.assertEqual(codes.count(429), 1)
        r = self.api('GET', '/api/v1/services', key=key)
        self.assertEqual((r.status, r.headers.get('Retry-After')), (429, '60'))
        self.assertEqual(self.api('GET', '/api/v1/services').status, 200)                      # another key is not affected

    def test_revocada(self):
        r = self.a.post('/api/provider/api-keys', {'action': 'create', 'name': 'Vieja', 'scope': 'read'})
        self.assertEqual(self.api('GET', '/api/v1/services', key=r.json['key']).status, 200)
        self.a.post('/api/provider/api-keys', {'action': 'revoke', 'id': r.json['id']})
        self.assertEqual(self.api('GET', '/api/v1/services', key=r.json['key']).status, 401)


if __name__ == '__main__':
    import unittest
    unittest.main()
