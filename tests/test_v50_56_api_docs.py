"""v50.56 · docs/api: the examples of the documentation work against the real server.

- The three examples to check a webhook's signature (Python, Node.js and PHP) accept a notice signed by the server
  (wod.canales.sign) and reject a changed body, a wrong secret and an old notice.
- The services and the booking the API gives have every field the documentation shows (and the documented
  «insurance» field), and the documented error format and codes are the ones the API answers.
"""
from __future__ import annotations

import importlib.util
import json
import re
import shutil
import subprocess
import sys
import time
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app')); sys.path.insert(0, str(ROOT / 'tests'))
from helpers import Client, ServerTestCase  # noqa: E402
from wod import canales as wch  # noqa: E402

DOCS = ROOT / 'docs' / 'api'
EX = DOCS / 'ejemplos'
FAR = '2099-12-31'
SECRET = 'whsk_' + 'x' * 43
BODY = json.dumps({'id': 'evt_1', 'type': 'booking.confirmed', 'created': 1, 'data': {'booking': {'id': 7, 'ref': 'WOD-000007'}}}, separators=(',', ':')).encode()


def doc_json_keys(md: str, start: str) -> set[str]:
    """The keys of the first JSON object in the documentation that starts with `start`."""
    i = md.index(start)
    block = md[i:md.index('```', i)]
    return set(re.findall(r'"([a-z_]+)":', block))


class Firma(unittest.TestCase):
    def cases(self):
        now = int(time.time())
        good = wch.sign(SECRET, BODY, now)
        return [('buena', SECRET, good, BODY, now, True),
                ('cuerpo cambiado', SECRET, good, BODY.replace(b'7', b'8'), now, False),
                ('otro secreto', 'whsk_otro', good, BODY, now, False),
                ('aviso viejo', SECRET, wch.sign(SECRET, BODY, now - 301), BODY, now, False),
                ('sin cabecera', SECRET, '', BODY, now, False)]

    def test_python(self):
        spec = importlib.util.spec_from_file_location('verificar_firma', EX / 'verificar_firma.py')
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        for name, secret, header, body, now, want in self.cases():
            with self.subTest(name):
                self.assertIs(mod.verificar(secret, header, body, now), want)
                self.assertIs(wch.verify(secret, header, body, now), want)   # the same as the server

    @unittest.skipUnless(shutil.which('node'), 'Node.js no está instalado')
    def test_node(self):
        for name, secret, header, body, now, want in self.cases():
            with self.subTest(name):
                code = (f"const {{verificar}}=require({json.dumps(str(EX / 'verificar-firma.js'))});"
                        f"process.stdout.write(String(verificar({json.dumps(secret)},{json.dumps(header)},Buffer.from({json.dumps(body.decode())}),{now})))")
                r = subprocess.run(['node', '-e', code], capture_output=True, text=True, timeout=30)
                self.assertEqual(r.returncode, 0, r.stderr); self.assertEqual(r.stdout, 'true' if want else 'false')

    @unittest.skipUnless(shutil.which('php'), 'PHP no está instalado')
    def test_php(self):
        for name, secret, header, body, now, want in self.cases():
            with self.subTest(name):
                code = (f"require {json.dumps(str(EX / 'verificar-firma.php'))};"
                        f"echo worldives_verificar({json.dumps(secret)},{json.dumps(header)},{json.dumps(body.decode())},{now})?'true':'false';")
                r = subprocess.run(['php', '-r', code], capture_output=True, text=True, timeout=30)
                self.assertEqual(r.returncode, 0, r.stderr); self.assertEqual(r.stdout.strip(), 'true' if want else 'false')

    def test_documentacion_de_los_avisos(self):
        md = (DOCS / 'webhooks.md').read_text(encoding='utf-8')
        for ev in wch.WEBHOOK_EVENTS: self.assertIn(f'`{ev}`', md)
        for h in ('X-WORLDIVES-Signature', 'X-WORLDIVES-Event', 'X-WORLDIVES-Delivery'): self.assertIn(h, md)
        self.assertIn('5 minutos', md); self.assertEqual(wch.WEBHOOK_TOLERANCE, 300)
        self.assertIn('1 min, 5 min, 30 min, 2 h, 6 h y 24 h', md); self.assertEqual(wch.WEBHOOK_RETRIES, (60, 300, 1800, 7200, 21600, 86400))


class Referencia(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.extra_env = dict(cls.extra_env, WOD_API_MAX_PER_MINUTE='400')
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.c = t.make_center(cls.admin, 'apidoc')
        cid = cls.c.user['center_id']
        cls.server.sql(f"UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}' WHERE id=?", (cid,))
        cls.sid = cls.c.post('/api/provider-services', {'title': 'Inmersión guiada', 'price': 45, 'booking_mode': 'request', 'max_participants': 6,
                                                         'insurance_required': 'online'}).json['id']
        cls.slot = cls.c.post('/api/provider-services/slot', {'service_id': cls.sid, 'slot_date': '2031-09-14', 'slot_time': '10:00', 'spots_total': 6}).json['slot_id']
        cls.key = cls.c.post('/api/provider/api-keys', {'action': 'create', 'name': 'Doc', 'scope': 'write'}).json['key']
        cls.md = (DOCS / 'README.md').read_text(encoding='utf-8')

    def api(self, method, path, body=None, headers=None):
        h = {'Authorization': f'Bearer {self.key}', **(headers or {})}
        c = Client(self.server, origin=None)
        return c.request(method, path, data=body, headers=h) if method == 'POST' else c.get(path, headers=h)

    def test_campos_documentados(self):
        svc = self.api('GET', '/api/v1/services').json['data'][0]
        self.assertLessEqual(doc_json_keys(self.md, '{"data": [{'), set(svc) | {'data'})
        self.assertEqual(svc['insurance_required'], 'online')
        av = self.api('GET', f'/api/v1/availability?service_id={self.sid}&from=2031-09-01&to=2031-09-30').json
        self.assertLessEqual(doc_json_keys(self.md, '{"service_id": 41, "unit": "slot"'), set(av) | set(av['departures'][0]))
        body = {'service_id': self.sid, 'departure_id': self.slot, 'participants': 2, 'external_ref': 'PEDIDO-7781',
                'customer': {'name': 'Marta Pérez', 'email': 'marta@example.org', 'phone': '+34600000000', 'language': 'es'},
                'insurance': {'insurer': 'Aseguradora Demo A', 'valid_to': '2032-12-31'}}
        r = self.api('POST', '/api/v1/bookings', body, headers={'Idempotency-Key': 'pedido-7781'})
        self.assertEqual(r.status, 201, r)
        b = r.json['booking']
        documented = doc_json_keys(self.md, '{\n  "id": 1323')
        self.assertLessEqual(documented - {'id', 'title', 'name', 'email', 'phone', 'required', 'status', 'valid_to', 'insurer'}, set(b))
        self.assertEqual(set(b['customer']), {'name', 'email', 'phone'})
        self.assertEqual((b['insurance']['required'], b['insurance']['status']), ('online', 'declared'))   # the centre's system vouches for it
        self.assertIn('booking_url', r.json)
        again = self.api('POST', '/api/v1/bookings', body, headers={'Idempotency-Key': 'pedido-7781'})
        self.assertEqual((again.status, again.json.get('duplicate'), again.json['booking']['id']), (200, True, b['id']))

    def test_seguro_obligatorio_sin_seguro_espera(self):
        body = {'service_id': self.sid, 'departure_id': self.slot, 'participants': 1, 'customer': {'name': 'Sin Seguro', 'email': 'sin@example.org'}}
        r = self.api('POST', '/api/v1/bookings', body, headers={'Idempotency-Key': 'sin-seguro-1'})
        self.assertEqual(r.status, 201, r)
        self.assertTrue(r.json.get('insurance_required'))
        self.assertEqual(r.json['booking']['status'], 'insurance_pending')
        self.assertTrue(r.json['booking']['insurance'].get('deadline'))

    def test_errores_documentados(self):
        r = Client(self.server, origin=None).get('/api/v1/services')
        self.assertEqual(r.status, 401); self.assertEqual(set(r.json), {'error'}); self.assertEqual(r.json['error']['code'], 'invalid_key')
        self.assertIn('`invalid_key`', self.md)
        r = self.api('GET', '/api/v1/availability?service_id=999999')
        self.assertEqual((r.status, r.json['error']['code']), (404, 'not_found'))
        r = self.api('GET', f'/api/v1/availability?service_id={self.sid}&from=2031-01-01&to=2031-12-31')
        self.assertEqual((r.status, r.json['error']['code']), (400, 'invalid_range'))
        for code in ('invalid_json', 'missing_service_id', 'invalid_date', 'read_only_key', 'plan_required', 'no_spots', 'not_cancellable',
                     'unsupported_media_type', 'rate_limited', 'busy'):
            self.assertIn(f'`{code}`', self.md)


if __name__ == '__main__':
    unittest.main()
