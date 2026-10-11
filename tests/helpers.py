"""Test harness: starts the real server on a COPY of the database in a temporary folder.

The bundled database is never modified by the tests. Every test module gets its own server process,
storage folder and log folder, removed at the end.
"""
from __future__ import annotations

import http.cookiejar
import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import unittest
import urllib.error
import urllib.request
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SEED_DB = ROOT / 'data' / 'worldivesdiscovery.sqlite3'


def free_port() -> int:
    s = socket.socket()
    s.bind(('127.0.0.1', 0))
    port = s.getsockname()[1]
    s.close()
    return port


class Server:
    def __init__(self, extra_env: dict | None = None, seed: Path | None = SEED_DB):
        self.tmp = Path(tempfile.mkdtemp(prefix='wod-test-'))
        self.db = self.tmp / 'test.sqlite3'
        if seed and Path(seed).exists():
            shutil.copy(seed, self.db)
        self.port = free_port()
        self.base = f'http://127.0.0.1:{self.port}'
        self.env = dict(os.environ)
        self.env.update({
            'WOD_DB_PATH': str(self.db), 'WOD_STORAGE_DIR': str(self.tmp / 'storage'), 'WOD_LOG_DIR': str(self.tmp / 'logs'),
            'WOD_DATA_DIR': str(self.tmp), 'WOD_UPLOADS_DIR': str(self.tmp / 'uploads'), 'WOD_PORT': str(self.port), 'WOD_HOST': '127.0.0.1', 'WOD_ENV': 'development',
            'WOD_PUBLIC_URL': self.base, 'WOD_SECRET_KEY': 'x' * 40, 'WOD_MAIL_FILE_DIR': str(self.tmp / 'mail'),
            'WOD_ADMIN_TOTP_REQUIRED': '0', 'WOD_PBKDF2_ITERATIONS': '100000', 'WOD_MAINTENANCE_SECONDS': '30',
            'PYTHONDONTWRITEBYTECODE': '1', 'WOD_REGISTER_MAX_PER_HOUR': '1000',
        })
        for k in ('STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'STRIPE_CONNECT_WEBHOOK_SECRET', 'WOD_SMTP_HOST', 'ARCGIS_API_KEY', 'WOD_DEMO_MODE'):
            self.env.pop(k, None)
        self.env.update(extra_env or {})
        self.proc = None

    def start(self):
        self._out = open(self.tmp / 'stdout.log', 'w'); self._err = open(self.tmp / 'stderr.log', 'w')
        self.proc = subprocess.Popen([sys.executable, str(ROOT / 'app' / 'server.py')], env=self.env, cwd=str(self.tmp), stdout=self._out, stderr=self._err)
        for _ in range(200):
            try:
                urllib.request.urlopen(self.base + '/api/health', timeout=1).read()
                return self
            except Exception:
                if self.proc.poll() is not None:
                    raise RuntimeError('El servidor no arranca:\n' + (self.tmp / 'stderr.log').read_text())
                time.sleep(0.1)
        raise RuntimeError('El servidor no responde')

    def run_cli(self, *args, env=None):
        e = dict(self.env)
        e.update(env or {})
        return subprocess.run([sys.executable, str(ROOT / 'app' / 'server.py'), *args], env=e, cwd=str(self.tmp), capture_output=True, text=True, timeout=120)

    def stop(self):
        if self.proc and self.proc.poll() is None:
            self.proc.terminate()
            try:
                self.proc.wait(10)
            except subprocess.TimeoutExpired:
                self.proc.kill()
        for f in (getattr(self, '_out', None), getattr(self, '_err', None)):
            if f: f.close()
        self.stderr = (self.tmp / 'stderr.log').read_text() if (self.tmp / 'stderr.log').exists() else ''
        shutil.rmtree(self.tmp, ignore_errors=True)

    def sql(self, query, args=()):
        import sqlite3
        c = sqlite3.connect(self.db)
        c.row_factory = sqlite3.Row
        try:
            rows = [dict(r) for r in c.execute(query, args).fetchall()]
            c.commit()
            return rows
        finally:
            c.close()


class Response:
    def __init__(self, status, headers, body):
        self.status = status
        self.headers = headers
        self.body = body

    @property
    def json(self):
        try:
            return json.loads(self.body.decode('utf-8'))
        except Exception:
            return None

    def __repr__(self):
        return f'<{self.status} {self.body[:200]!r}>'


class Client:
    """A browser-like client: keeps cookies and sends Origin on writes (like a real browser)."""

    def __init__(self, server: Server, origin: str | None = 'self'):
        self.server = server
        self.jar = http.cookiejar.CookieJar()
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(self.jar), NoRedirect())
        self.origin = server.base if origin == 'self' else origin
        self.user = None

    def request(self, method, path, data=None, headers=None, raw=None, content_type=None):
        url = self.server.base + path
        h = dict(headers or {})
        body = None
        if raw is not None:
            body = raw
            if content_type:
                h['Content-Type'] = content_type
        elif data is not None:
            body = json.dumps(data).encode()
            h['Content-Type'] = 'application/json'
        if method in ('POST', 'DELETE', 'PUT') and self.origin and 'Origin' not in h:
            h['Origin'] = self.origin
        req = urllib.request.Request(url, data=body, method=method, headers=h)
        try:
            with self.opener.open(req, timeout=60) as r:
                return Response(r.status, dict(r.headers), r.read())
        except urllib.error.HTTPError as e:
            return Response(e.code, dict(e.headers), e.read())

    def get(self, path, **kw):
        return self.request('GET', path, **kw)

    def post(self, path, data=None, **kw):
        return self.request('POST', path, data if data is not None else {}, **kw)

    def upload(self, path, fields: dict, filename: str, content: bytes, field='file'):
        boundary = uuid.uuid4().hex
        parts = []
        for k, v in fields.items():
            parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{k}"\r\n\r\n{v}\r\n'.encode())
        parts.append(f'--{boundary}\r\nContent-Disposition: form-data; name="{field}"; filename="{filename}"\r\nContent-Type: application/octet-stream\r\n\r\n'.encode() + content + b'\r\n')
        parts.append(f'--{boundary}--\r\n'.encode())
        return self.request('POST', path, raw=b''.join(parts), content_type=f'multipart/form-data; boundary={boundary}')

    # convenience
    def register(self, name, email, username, password='buceo-seguro-2026', account_type='recreational', **extra):
        data = {'fullname': name, 'email': email, 'username': username, 'password': password, 'account_type': account_type,
                'accept_terms': True, 'accept_pro_terms': account_type != 'recreational', 'lang': 'es'}
        data.update(extra)
        r = self.post('/api/auth/register', data)
        return r

    def login(self, login, password='buceo-seguro-2026'):
        return self.post('/api/auth/login', {'login': login, 'password': password})

    def me(self):
        return self.get('/api/me').json


class NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, *a, **k):
        return None


PDF_BYTES = b'%PDF-1.4\n1 0 obj<<>>endobj\ntrailer<<>>\n%%EOF\n'
PNG_BYTES = b'\x89PNG\r\n\x1a\n' + b'\x00' * 64


class ServerTestCase(unittest.TestCase):
    """One server for the whole test class."""
    extra_env: dict = {}
    server: Server

    @classmethod
    def setUpClass(cls):
        cls.server = Server(cls.extra_env).start()

    @classmethod
    def tearDownClass(cls):
        cls.server.stop()
        errors = [l for l in cls.server.stderr.splitlines() if ' -> ' in l and l.startswith('[')]
        if errors:
            print('\nERRORES INTERNOS DEL SERVIDOR (500):\n' + '\n'.join(errors))
        cls.server_errors = errors

    def client(self, origin='self'):
        return Client(self.server, origin)

    # Roles used across the suites -------------------------------------------------
    def make_admin(self, email='admin@worldives.test', username='admin'):
        res = self.server.run_cli('--create-admin', '--email', email, '--username', username, '--name', 'Admin Test', env={'WOD_ADMIN_PASSWORD': 'admin-seguro-2026'})
        assert res.returncode == 0, res.stdout + res.stderr
        c = self.client()
        r = c.login(username, 'admin-seguro-2026')
        assert r.status == 200, r
        return c

    def make_diver(self, tag):
        c = self.client()
        r = c.register(f'Buceador {tag} Pérez', f'{tag}@diver.example.org', f'diver_{tag}')
        assert r.status == 200, r
        c.user = c.me()['user']
        return c

    def make_center(self, admin, tag, phone='+34 600 111 222'):
        c = self.client()
        r = c.register(f'Gerente {tag}', f'{tag}@centro-{tag}.example.org', f'center_{tag}', account_type='center',
                       center_name=f'Centro {tag}', phone=phone, city='Xàbia', website=f'https://centro-{tag}.example.org')
        assert r.status == 200, r
        claim = [x for x in admin.get('/api/admin/center-claims').json['items'] if x['email'] == f'{tag}@centro-{tag}.example.org'][0]
        r = admin.post('/api/admin/center-claims/review', {'id': claim['id'], 'decision': 'approve', 'verification_method': 'email_domain', 'verification_note': 'email del dominio comprobado'})
        assert r.status == 200, r
        assert c.login(f'center_{tag}').status == 200
        c.user = c.me()['user']
        return c

    def make_freelance(self, admin, tag):
        c = self.client()
        r = c.register(f'Instructor {tag}', f'{tag}@pro.example.org', f'pro_{tag}', account_type='freelance', phone='+34 611 000 000')
        assert r.status == 200, r
        claim = [x for x in admin.get('/api/admin/center-claims').json['items'] if x['email'] == f'{tag}@pro.example.org'][0]
        r = admin.post('/api/admin/center-claims/review', {'id': claim['id'], 'decision': 'approve', 'verification_method': 'document', 'verification_note': 'licencia de instructor revisada'})
        assert r.status == 200, r
        assert c.login(f'pro_{tag}').status == 200
        c.user = c.me()['user']
        return c
