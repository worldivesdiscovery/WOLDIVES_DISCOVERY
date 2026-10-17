"""A tiny local imitation of the Stripe API, enough for the payment flows of WORLDIVES.

The server talks to it when WOD_STRIPE_API_BASE points here. Nothing leaves the machine.
It records every call (method, path, params and the Stripe-Account header) so tests can check, for example,
that direct charges are created on the connected account and carry no application fee.
"""
from __future__ import annotations

import hashlib
import hmac
import itertools
import json
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qsl, urlparse


def _nest(pairs):
    """Stripe form encoding (a[b][0][c]=1) -> nested dicts/lists."""
    root = {}
    for key, value in pairs:
        parts = key.replace(']', '').split('[')
        cur = root
        for i, p in enumerate(parts):
            last = i == len(parts) - 1
            nxt = None if last else parts[i + 1]
            if last:
                cur[p] = value
            else:
                cur = cur.setdefault(p, {} if not nxt.isdigit() else {})
    def fix(x):
        if isinstance(x, dict):
            if x and all(k.isdigit() for k in x):
                return [fix(x[k]) for k in sorted(x, key=int)]
            return {k: fix(v) for k, v in x.items()}
        return x
    return fix(root)


class StripeMock:
    def __init__(self):
        self.sessions = {}
        self.accounts = {}
        self.refunds = []
        self.domains = []   # v50.58: payment method domains (Apple Pay / Google Pay inside the booking)
        self.calls = []
        self.ids = itertools.count(1)
        self.fail_next = False
        mock = self

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def _send(self, status, obj):
                raw = json.dumps(obj).encode()
                self.send_response(status)
                self.send_header('Content-Type', 'application/json')
                self.send_header('Content-Length', str(len(raw)))
                self.end_headers()
                self.wfile.write(raw)

            def _params(self):
                n = int(self.headers.get('Content-Length') or 0)
                body = self.rfile.read(n).decode() if n else ''
                q = urlparse(self.path).query
                return _nest(parse_qsl(body, keep_blank_values=True) + parse_qsl(q, keep_blank_values=True))

            def handle_any(self, method):
                path = urlparse(self.path).path
                params = self._params()
                acct = self.headers.get('Stripe-Account')
                mock.calls.append({'method': method, 'path': path, 'params': params, 'account': acct})
                if mock.fail_next and method == 'POST' and path == '/v1/checkout/sessions':
                    mock.fail_next = False
                    return self._send(402, {'error': {'type': 'card_error', 'message': 'simulated failure'}})
                parts = path.strip('/').split('/')
                if path == '/v1/checkout/sessions' and method == 'POST':
                    sid = f'cs_test_{next(mock.ids)}'
                    li = (params.get('line_items') or [{}])[0]
                    pd = li.get('price_data', {})
                    embedded = params.get('ui_mode') == 'embedded'
                    # Stripe's own rules for the form inside the page (ui_mode=embedded): no success_url / cancel_url, and a
                    # return_url unless redirect_on_completion=never
                    if embedded and (params.get('success_url') or params.get('cancel_url')):
                        return self._send(400, {'error': {'type': 'invalid_request_error', 'message': 'success_url and cancel_url are not allowed with ui_mode=embedded'}})
                    if embedded and params.get('redirect_on_completion') != 'never' and not params.get('return_url'):
                        return self._send(400, {'error': {'type': 'invalid_request_error', 'message': 'return_url is required'}})
                    s = {'id': sid, 'object': 'checkout.session', 'url': None if embedded else f'https://checkout.stripe.test/{sid}', 'status': 'open', 'payment_status': 'unpaid',
                         'ui_mode': 'embedded' if embedded else 'hosted', 'client_secret': f'{sid}_secret_mock' if embedded else None,
                         'customer_email': params.get('customer_email'),
                         'amount_total': int(pd.get('unit_amount', 0)) * int(li.get('quantity', 1)), 'currency': pd.get('currency', 'eur'),
                         'metadata': params.get('metadata', {}), 'payment_intent': None, 'payment_intent_data': params.get('payment_intent_data', {}),
                         'account': acct, 'expires_at': int(params.get('expires_at', 0) or 0)}
                    mock.sessions[sid] = s
                    return self._send(200, s)
                if len(parts) >= 4 and parts[:3] == ['v1', 'checkout', 'sessions']:
                    s = mock.sessions.get(parts[3])
                    if not s:
                        return self._send(404, {'error': {'message': 'No such session'}})
                    if len(parts) == 5 and parts[4] == 'expire':
                        if s['status'] == 'open':
                            s['status'] = 'expired'
                        return self._send(200, s)
                    out = dict(s)
                    if s['payment_status'] == 'paid':
                        out['payment_intent'] = {'id': s['pi'], 'object': 'payment_intent', 'latest_charge': {'id': 'ch_' + s['pi'][3:], 'receipt_url': 'https://pay.stripe.test/receipt',
                                                 'payment_method_details': {'card': {'brand': 'visa', 'last4': '4242'}}}}
                    return self._send(200, out)
                if path == '/v1/refunds' and method == 'GET':
                    pi = params.get('payment_intent')
                    return self._send(200, {'object': 'list', 'data': [r for r in mock.refunds if not pi or r['payment_intent'] == pi]})
                if path == '/v1/refunds' and method == 'POST':
                    r = {'id': f're_{next(mock.ids)}', 'object': 'refund', 'status': 'succeeded', 'amount': int(params.get('amount', 0) or 0),
                         'payment_intent': params.get('payment_intent'), 'account': acct, 'params': params}
                    mock.refunds.append(r)
                    return self._send(200, r)
                if path == '/v1/accounts' and method == 'POST':
                    aid = f'acct_test_{next(mock.ids)}'
                    a = {'id': aid, 'object': 'account', 'charges_enabled': False, 'payouts_enabled': False, 'details_submitted': False, 'params': params}
                    mock.accounts[aid] = a
                    return self._send(200, a)
                if len(parts) >= 3 and parts[:2] == ['v1', 'accounts']:
                    a = mock.accounts.get(parts[2]) or {'id': parts[2], 'object': 'account', 'charges_enabled': True, 'payouts_enabled': True, 'details_submitted': True}
                    if len(parts) == 4 and parts[3] == 'login_links':
                        return self._send(200, {'object': 'login_link', 'url': 'https://connect.stripe.test/express'})
                    return self._send(200, a)
                if path == '/v1/payment_method_domains' and method == 'POST':
                    d = {'id': f'pmd_test_{next(mock.ids)}', 'object': 'payment_method_domain', 'domain_name': params.get('domain_name'), 'enabled': True, 'account': acct}
                    mock.domains.append(d)
                    return self._send(200, d)
                if path == '/v1/account_links' and method == 'POST':
                    return self._send(200, {'object': 'account_link', 'url': 'https://connect.stripe.test/onboarding'})
                if path.startswith('/v2/core/accounts'):
                    aid = parts[3] if len(parts) > 3 else f'acct_test_{next(mock.ids)}'
                    a = mock.accounts.setdefault(aid, {'id': aid, 'object': 'v2.core.account', 'params': params})
                    return self._send(200, a)
                return self._send(404, {'error': {'message': f'mock: {method} {path} not implemented'}})

            def do_GET(self):
                self.handle_any('GET')

            def do_POST(self):
                self.handle_any('POST')

            def do_DELETE(self):
                self.handle_any('DELETE')

        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.port = self.httpd.server_address[1]
        self.base = f'http://127.0.0.1:{self.port}'
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def stop(self):
        self.httpd.shutdown()

    # --- test helpers ---------------------------------------------------------
    def pay(self, sid, amount=None):
        s = self.sessions[sid]
        s['payment_status'] = 'paid'
        s['status'] = 'complete'
        s['pi'] = f'pi_test_{next(self.ids)}'
        if amount is not None:
            s['amount_total'] = amount
        return s

    def last_session(self):
        return list(self.sessions.values())[-1]

    def session_by_secret(self, secret):
        """The session of an embedded form (what Stripe.js gets in the browser)."""
        return next((x for x in self.sessions.values() if x.get('client_secret') == secret), None)

    @staticmethod
    def signed(event: dict, secret: str):
        payload = json.dumps(event)
        t = int(time.time())
        sig = hmac.new(secret.encode(), f'{t}.{payload}'.encode(), hashlib.sha256).hexdigest()
        return payload.encode(), f't={t},v1={sig}'
