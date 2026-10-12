"""A tiny local imitation of Meta's Graph API (WhatsApp Cloud API), enough for the notices of WORLDIVES (v50.47).

The server talks to it when WHATSAPP_GRAPH_BASE points here. Nothing leaves the machine. Each «Embedded Signup» code
is mapped to a WhatsApp Business account (WABA) with its numbers, as Meta would after the centre logs in. Every sent
message is recorded (phone number id of origin, recipient, template, language, parameters) so tests can check that
each notice leaves from the number of its own centre.
"""
from __future__ import annotations

import hashlib
import hmac
import itertools
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

APP_ID = '1234567890'
APP_SECRET = 'secreto-de-la-app-de-pruebas'


class MetaMock:
    def __init__(self):
        self.codes = {}          # code → {'waba': id, 'numbers': [{'id':…, 'display_phone_number':…}]}
        self.tokens = {}         # token → waba
        self.sent = []           # every message sent
        self.templates = {}      # waba → {name:lang → status}
        self.subscribed = set()
        self.registered = set()
        self.fail_next = None    # (http status, meta code) for the next /messages call
        self.revoked = set()     # tokens that answer 190 (expired / revoked)
        self.ids = itertools.count(1)
        mock = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a): pass

            def _send(self, status, obj):
                raw = json.dumps(obj).encode()
                self.send_response(status); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(raw)))
                self.end_headers(); self.wfile.write(raw)

            def _err(self, status, msg, code):
                self._send(status, {'error': {'message': msg, 'code': code}})

            def _token(self):
                a = self.headers.get('Authorization', '')
                return a[7:] if a.startswith('Bearer ') else ''

            def do_GET(self):
                u = urlparse(self.path); q = {k: v[0] for k, v in parse_qs(u.query).items()}
                parts = u.path.strip('/').split('/')[1:]          # without the version
                if parts == ['oauth', 'access_token']:
                    if q.get('client_id') != APP_ID or q.get('client_secret') != APP_SECRET: return self._err(400, 'bad app', 101)
                    c = mock.codes.get(q.get('code'))
                    if not c: return self._err(400, 'Invalid verification code', 100)
                    tok = 'tok_' + hashlib.sha256(q['code'].encode()).hexdigest()[:16]
                    mock.tokens[tok] = c['waba']; return self._send(200, {'access_token': tok, 'token_type': 'bearer'})
                if parts == ['debug_token']:
                    waba = mock.tokens.get(q.get('input_token'))
                    return self._send(200, {'data': {'app_id': APP_ID, 'is_valid': bool(waba), 'granular_scopes': [
                        {'scope': 'whatsapp_business_management', 'target_ids': [waba] if waba else []},
                        {'scope': 'whatsapp_business_messaging', 'target_ids': [waba] if waba else []}]}})
                tok = self._token()
                if tok in mock.revoked: return self._err(401, 'Error validating access token', 190)
                if len(parts) == 2 and parts[1] == 'phone_numbers':
                    if mock.tokens.get(tok) != parts[0]: return self._err(403, 'no permission', 200)
                    nums = next((c['numbers'] for c in mock.codes.values() if c['waba'] == parts[0]), [])
                    return self._send(200, {'data': nums})
                if len(parts) == 2 and parts[1] == 'message_templates':
                    st = mock.templates.get(parts[0], {})
                    return self._send(200, {'data': [{'name': k.split(':')[0], 'language': k.split(':')[1], 'status': v} for k, v in st.items()]})
                self._err(404, 'unknown', 100)

            def do_POST(self):
                u = urlparse(self.path); parts = u.path.strip('/').split('/')[1:]
                body = json.loads(self.rfile.read(int(self.headers.get('Content-Length') or 0)) or b'{}')
                tok = self._token()
                if tok in mock.revoked: return self._err(401, 'Error validating access token', 190)
                waba_of_tok = mock.tokens.get(tok)
                if len(parts) == 2 and parts[1] == 'subscribed_apps':
                    if waba_of_tok != parts[0]: return self._err(403, 'no permission', 200)
                    mock.subscribed.add(parts[0]); return self._send(200, {'success': True})
                if len(parts) == 2 and parts[1] == 'message_templates':
                    if waba_of_tok != parts[0]: return self._err(403, 'no permission', 200)
                    key = f"{body.get('name')}:{body.get('language')}"
                    mock.templates.setdefault(parts[0], {})[key] = 'APPROVED'
                    return self._send(200, {'id': str(next(mock.ids)), 'status': 'APPROVED', 'category': body.get('category')})
                if len(parts) == 2 and parts[1] == 'register':
                    mock.registered.add(parts[0]); return self._send(200, {'success': True})
                if len(parts) == 2 and parts[1] == 'messages':
                    pnid = parts[0]
                    owner = next((c['waba'] for c in mock.codes.values() if any(n['id'] == pnid for n in c['numbers'])), None)
                    if not owner or owner != waba_of_tok: return self._err(403, 'The phone number does not belong to this token', 200)
                    if mock.fail_next:
                        st, code = mock.fail_next; mock.fail_next = None
                        return self._err(st, 'simulated failure', code)
                    wamid = f'wamid.{pnid}.{next(mock.ids)}'
                    mock.sent.append({'wamid': wamid, 'phone_number_id': pnid, 'to': body.get('to'), 'template': body['template']['name'],
                                      'lang': body['template']['language']['code'], 'components': body['template'].get('components')})
                    return self._send(200, {'messaging_product': 'whatsapp', 'contacts': [{'wa_id': body.get('to')}], 'messages': [{'id': wamid}]})
                self._err(404, 'unknown', 100)

        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.port = self.httpd.server_address[1]
        self.base = f'http://127.0.0.1:{self.port}'
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def add_business(self, code, waba, numbers):
        """numbers: [(phone_number_id, display number)]"""
        self.codes[code] = {'waba': waba, 'numbers': [{'id': i, 'display_phone_number': d, 'verified_name': f'Empresa {waba}'} for i, d in numbers]}

    def env(self):
        return {'WHATSAPP_ENABLED': '1', 'WHATSAPP_APP_ID': APP_ID, 'WHATSAPP_APP_SECRET': APP_SECRET, 'WHATSAPP_VERIFY_TOKEN': 'verificar-pruebas',
                'WHATSAPP_CONFIG_ID': '987654321', 'WHATSAPP_GRAPH_BASE': self.base}

    @staticmethod
    def signed(payload: dict, secret: str = APP_SECRET):
        raw = json.dumps(payload).encode()
        return raw, 'sha256=' + hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()

    @staticmethod
    def status_event(phone_number_id, wamid, status, ts='1700000000', error_code=None):
        st = {'id': wamid, 'status': status, 'timestamp': ts, 'recipient_id': '34600000000'}
        if error_code: st['errors'] = [{'code': error_code, 'title': 'failed'}]
        return {'object': 'whatsapp_business_account', 'entry': [{'id': 'waba', 'changes': [{'field': 'messages', 'value': {
            'messaging_product': 'whatsapp', 'metadata': {'phone_number_id': phone_number_id, 'display_phone_number': '34000'}, 'statuses': [st]}}]}]}

    def stop(self):
        self.httpd.shutdown()
