"""v50.51 · Auditoría OWASP Top 10 (2021): comprobaciones empíricas contra el servidor real.

Informe con el detalle de cada punto (qué se revisó, archivo:línea, gravedad y corrección propuesta):
seguridad_hallazgos.md, entregado junto a esta prueba.

Convención de nombres:
- test_a0X_…            protección que ya funciona (debe pasar siempre: si falla, algo se ha roto).
- test_hallazgo_a0X_…   hallazgo real de la auditoría. FALLA mientras el fallo siga abierto y pasará cuando se aplique la
                        corrección propuesta en el informe (el docstring de cada una dice cuál).

Todo se ejecuta con una copia temporal de la base de pruebas (tests/helpers.py). Sin carga: cada comprobación hace
unas pocas peticiones; el barrido de rutas hace una petición por ruta.
"""
import ast
import base64
import datetime as dt
import gzip
import hashlib
import http.client
import importlib.util
import io
import json
import os
import re
import shutil
import sqlite3
import statistics
import subprocess
import sys
import tempfile
import time
import unittest
import uuid
from pathlib import Path

from helpers import ROOT, ServerTestCase, Client, PDF_BYTES

APP = ROOT / 'app'
if str(APP) not in sys.path:
    sys.path.insert(0, str(APP))

DAY = lambda n: (dt.date.today() + dt.timedelta(days=n)).isoformat()
PASSWORD = 'buceo-seguro-2026'


# --------------------------------------------------------------------------------------------- rutas de app/server.py
def _sample(rx):
    """A concrete path that matches one of the route regular expressions of the server (or None)."""
    s = rx
    for a, b in ((r'(?:/(\d+))?', '/1'), (r'(/borrar|/commons)?', ''), (r'(/retirar)?', ''), (r'(video|especie-punto)', 'video'),
                 (r'[0-9a-f]{32}', '0' * 32), (r'\d+', '1'), (r'[0-9a-z]+', 'a1'), (r'[cmr]', 'c'), (r'[A-Za-z0-9_\-]+', 'x'), (r'\.', '.')):
        s = s.replace(a, b)
    return s if re.fullmatch(rx, s) else None


def server_routes():
    """[(method, sample path)] of every route compared in do_GET / do_POST / do_DELETE of app/server.py:
    «path == '…'», «path in (…)», «path.startswith('…')[ and path.endswith('…')]» and «re.fullmatch(r'…', path)»."""
    lines = (APP / 'server.py').read_text(encoding='utf-8').split('\n')

    def find(name):
        for i, l in enumerate(lines):
            if l.startswith(f'    def {name}('): return i
        raise AssertionError(f'No encuentro Handler.{name} en app/server.py')
    blocks = {'GET': (find('do_GET'), find('serve_spa')), 'POST': (find('do_POST'), find('do_DELETE')), 'DELETE': (find('do_DELETE'), find('session_hash'))}
    out, seen = [], set()
    for method, (a, b) in blocks.items():
        for l in lines[a:b]:
            m = re.match(r'^\s+(?:el)?if (.*?):', l)
            if not m or 'path' not in m.group(1): continue
            cond, paths = m.group(1), []
            paths += re.findall(r"path\s*==\s*'([^']+)'", cond)
            mi = re.search(r'path in \(([^)]*)\)', cond)
            if mi: paths += re.findall(r"'([^']+)'", mi.group(1))
            for rx in re.findall(r"re\.fullmatch\(r'([^']+)',\s*path\)", cond):
                s = _sample(rx)
                if s: paths.append(s)
            ms = re.search(r"path\.startswith\('([^']+)'\)", cond)
            if ms and not paths:
                pre, me = ms.group(1), re.search(r"path\.endswith\('([^']+)'\)", cond)
                if me: paths.append(pre.rstrip('/') + '/1' + (me.group(1) if me.group(1).startswith('/') else '/' + me.group(1)))
                elif pre.endswith('/'): paths.append(pre + '1')
                else: paths.append(pre)
            for p in paths:
                if p.startswith('/api/') and p not in ('/api/', '/api/1') and (method, p) not in seen:
                    seen.add((method, p)); out.append((method, p))
    return out


# Public on purpose (catalogue, legal texts, sign-up and sign-in, links protected by their own token or signature,
# webhooks). Everything else must refuse a visitor without a session.
PUBLIC_GET = re.compile(r'^/api/(health|setup/status|legal/(doc|info|history|version)|plans|center/import/template|map/config|tiles/satellite/.*'
                        r'|site-media|site-promos|agenda/public|point-directory|dive-points/map|travel-directory|travel-offers/.*|travel-experiences/\d+'
                        r'|meta|geocode|me|providers/.*|provider-services(/\d+)?|center-extras|booking-quote|center-equipment|dive-points(/\d+)?'
                        r'|dive-points/\d+/(virtual|centers)|salidas-cercanas|top-dives|center-directory|dive-types(/.*)?|centers(/\d+)?|qr/.*'
                        r'|app/push|promo/.*|team/invite|whatsapp/webhook|r/.*|public/bookings/\d+|slot-cancel/\d+'
                        r'|service-catalog|dive-areas|centers/\d+/reviews)$')   # v50.53: templates, areas of Spain, more reviews
PUBLIC_POST = re.compile(r'^/api/(setup|auth/(register|login|logout|forgot|reset|verify-email)|marketing/unsubscribe|pruebas/(entrar|fallo)'
                         r'|integrations/bookings|payments/webhook(/connect)?|whatsapp/webhook|info-requests|stats/track|agenda/quote|reports|contact'
                         r'|team/join|account/delete/confirm|r/.*|slot-cancel/\d+|provider/wallet-grant)$')
# Professional and administration areas: a diver gets 403/404 there.
PRO_PATH = re.compile(r'^/api/(admin/|center/|provider/|manifest|avisos|whatsapp|pro/|team/|payments/connect|payments/center|agenda/(mine|block|unblock|hours)'
                      r'|service-templates|center-points/(assign|unassign)|qr/create|dive-points/\d+/photos|dive-points(/update)?$|provider-services|travel-experiences'
                      r'|center-equipment$|centers$'
                      r'|bookings/\d+/(status|payment|refund|reschedule|change-date/decide|whatsapp|diver-sheet\.pdf|qr\.svg)|promo/.*/redeem|reviews/\d+/reply'
                      r'|centers/update|marina/)')
# Diver exceptions: public pages of the panel area, the request to become a centre, retired routes and routes checked one by
# one below with real ids (their sample path is not a real request: they validate the body before the role).
DIVER_ALLOWED = {('GET', '/api/center/import/template'), ('POST', '/api/provider/center-create'), ('POST', '/api/provider/wallet-grant'),
                 ('GET', '/api/team/invite'), ('POST', '/api/team/join'), ('GET', '/api/whatsapp/webhook'), ('POST', '/api/whatsapp/webhook'),
                 ('POST', '/api/pro/escanear'), ('POST', '/api/manifest/sync'), ('POST', '/api/manifest/1'),
                 ('POST', '/api/marina/video'), ('POST', '/api/marina/especie-punto'), ('POST', '/api/reviews/1/reply')}


def tiny_png():
    """A real 2x2 PNG (stdlib only): an image that any decoder opens."""
    import struct, zlib
    chunk = lambda t, d: struct.pack('>I', len(d)) + t + d + struct.pack('>I', zlib.crc32(t + d) & 0xffffffff)
    raw = b''.join(b'\x00' + b'\x1c\xa5\xc7' * 2 for _ in range(2))
    return b'\x89PNG\r\n\x1a\n' + chunk(b'IHDR', struct.pack('>IIBBBBB', 2, 2, 8, 2, 0, 0, 0)) + chunk(b'IDAT', zlib.compress(raw)) + chunk(b'IEND', b'')


def _code_at(secret):
    from wod import totp
    return totp.code_at(secret, totp.current_step())


class Seguridad(ServerTestCase):
    # 127.0.0.1 is a trusted proxy here, so each check can come «from» its own IP with X-Forwarded-For and the rate
    # limits of one test never affect another one.
    extra_env = {'WOD_TRUSTED_PROXIES': '127.0.0.1', 'STRIPE_WEBHOOK_SECRET': 'whsec_pruebas_no_es_real'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        s = cls.server
        cls.admin = t.make_admin()
        cls.A = t.make_center(cls.admin, 's51a', phone='+34 600 510 001')
        cls.B = t.make_center(cls.admin, 's51b', phone='+34 600 510 002')
        cls.cidA, cls.cidB = cls.A.user['center_id'], cls.B.user['center_id']
        cls.diver = t.make_diver('s51d')
        cls.diver2 = t.make_diver('s51e')
        cls.recA = cls.member(t, cls.cidA, 's51rec', 'reception')
        cls.insA = cls.member(t, cls.cidA, 's51ins', 'instructor')
        cls.memB = cls.member(t, cls.cidB, 's51memb', 'reception')
        B = cls.B
        # --- private data of centre B -------------------------------------------------------------------------------
        cls.sB = B.post('/api/provider-services', {'title': 'Salida B', 'price': 30, 'booking_mode': 'request'}).json['id']
        cls.slB = B.post('/api/provider-services/slot', {'service_id': cls.sB, 'slot_date': DAY(8), 'slot_time': '09:00', 'spots_total': 8}).json['slot_id']
        r = cls.diver2.post('/api/bookings', {'center_id': cls.cidB, 'service_id': cls.sB, 'slot_id': cls.slB, 'participants': 1})
        assert r.status == 200, r
        cls.bB = r.json['id']
        assert B.post(f'/api/bookings/{cls.bB}/status', {'status': 'confirmed'}).status == 200
        cls.sB_paused = B.post('/api/provider-services', {'title': 'Pausado B', 'price': 20, 'booking_mode': 'request'}).json['id']
        s.sql('UPDATE provider_services SET active=0 WHERE id=?', (cls.sB_paused,))
        assert B.post('/api/center/extras/save', {'name': 'Extra B', 'price': 5}).status == 200
        cls.extraB = s.sql('SELECT id FROM center_extras WHERE center_id=? ORDER BY id DESC', (cls.cidB,))[0]['id']
        cls.tplB = B.post('/api/service-templates/save', {'name': 'Plantilla B', 'price': 10}).json['id']
        cls.boatB = B.post('/api/manifest/boats/save', {'name': 'Barco B', 'capacity': 10}).json['id']
        assert B.post('/api/center/tariffs/save', {'service_id': cls.sB, 'price': 35, 'effective_from': DAY(30)}).status == 200
        cls.tariffB = s.sql('SELECT id FROM center_tariffs WHERE center_id=? ORDER BY id DESC', (cls.cidB,))[0]['id']
        B.post('/api/center/team/invite', {'email': 'invitado-b@diver.example.org', 'member_role': 'reception'})
        inv = s.sql('SELECT id FROM team_invites WHERE center_id=? ORDER BY id DESC', (cls.cidB,))
        cls.invB = inv[0]['id'] if inv else 0
        r = B.post('/api/center/promotions', {'title': 'Promo B', 'value_text': '10 %', 'valid_until': DAY(60)})
        cls.pB = r.json.get('id') if r.status == 200 else None
        # --- centre A ---------------------------------------------------------------------------------------------
        cls.sA = cls.A.post('/api/provider-services', {'title': 'Salida A', 'price': 30, 'booking_mode': 'request'}).json['id']

    @classmethod
    def member(cls, t, center_id, tag, role):
        """A team member of a centre (same way as tests/test_v50_47_aislamiento.py)."""
        c = t.make_diver(tag); uid = c.user['id']
        cls.server.sql("UPDATE users SET role='center',center_id=? WHERE id=?", (center_id, uid))
        cls.server.sql('INSERT OR REPLACE INTO center_members(center_id,user_id,member_role,created_at) VALUES(?,?,?,?)', (center_id, uid, role, '2026-01-01'))
        assert c.login(f'diver_{tag}').status == 200
        c.user = c.me()['user']
        return c

    # ------------------------------------------------------------------------------------------------ helpers
    def ip(self, n):
        return {'X-Forwarded-For': f'198.51.100.{n}'}

    def snapshot_b(self):
        """Hash of every row of centre B touched by the checks below (and of B's owner templates)."""
        db = sqlite3.connect(self.server.db)
        try:
            out = []
            for table, where, args in (('provider_services', 'center_id=?', (self.cidB,)), ('service_slots', 'service_id IN (SELECT id FROM provider_services WHERE center_id=?)', (self.cidB,)),
                                       ('bookings', 'center_id=?', (self.cidB,)), ('center_extras', 'center_id=?', (self.cidB,)),
                                       ('service_templates', 'provider_user_id=?', (self.B.user['id'],)), ('boats', 'center_id=?', (self.cidB,)),
                                       ('center_tariffs', 'center_id=?', (self.cidB,)), ('team_invites', 'center_id=?', (self.cidB,)),
                                       ('center_members', 'center_id=?', (self.cidB,)), ('promotions', 'center_id=?', (self.cidB,)), ('centers', 'id=?', (self.cidB,))):
                out.append((table, [tuple(r) for r in db.execute(f'SELECT * FROM {table} WHERE {where} ORDER BY rowid', args).fetchall()]))
            out.append(('users', [tuple(r) for r in db.execute('SELECT id,role,center_id FROM users WHERE id=?', (self.memB.user['id'],)).fetchall()]))
        finally:
            db.close()
        return hashlib.sha256(json.dumps(out, default=str).encode()).hexdigest()

    def new_diver(self, tag):
        c = self.make_diver(tag)
        return c

    # ======================================================================================== A01 · control de acceso
    def test_a01_rutas_privadas_sin_sesion_responden_401_403_404(self):
        routes = server_routes()
        self.assertGreater(len(routes), 250, 'El analizador de rutas de app/server.py no encuentra las rutas')
        anon = self.client()
        bad = []
        for method, path in routes:
            public = (PUBLIC_GET if method == 'GET' else PUBLIC_POST).match(path)
            if public: continue
            r = anon.request(method, path, None if method == 'GET' else {})
            if r.status not in (401, 403, 404):
                bad.append(f'{method} {path} → {r.status} {r.body[:100]!r}')
        self.assertEqual(bad, [], 'Rutas privadas que responden sin sesión:\n' + '\n'.join(bad))

    def test_a01_buceador_no_usa_rutas_de_profesional_ni_admin(self):
        d = self.diver
        bad = []
        for method, path in server_routes():
            if not PRO_PATH.match(path) or (method, path) in DIVER_ALLOWED: continue
            if method == 'GET' and (PUBLIC_GET.match(path)): continue
            r = d.request(method, path, None if method == 'GET' else {})
            if r.status not in (403, 404, 410):
                bad.append(f'{method} {path} → {r.status} {r.body[:100]!r}')
        self.assertEqual(bad, [], 'Rutas de profesional o administración que acepta un buceador:\n' + '\n'.join(bad))
        self.assertEqual(d.request('DELETE', '/api/dive-points/1').status, 403)

    def test_a01_buceador_con_ids_reales_de_otro_centro(self):
        """The routes skipped above (they validate the body first), now with real ids of centre B: never any data."""
        from wod import pro as wpro
        d, before = self.diver, self.snapshot_b()
        change = {'slot_id': self.slB, 'booking_id': self.bB, 'seat': 1, 'field': 'status', 'base': '', 'value': 'present', 'at': '2026-01-01T00:00:00'}
        self.assertIn(d.post('/api/manifest/sync', {'changes': [change]}).status, (403, 404))
        self.assertIn(d.post(f'/api/manifest/{self.slB}/settings', {'max_per_guide': 2}).status, (403, 404))
        self.assertIn(d.post('/api/pro/contar', {'slot_id': self.slB, 'count': 3}).status, (403, 404))
        tok = self.server.sql('SELECT public_token FROM bookings WHERE id=?', (self.bB,))[0]['public_token']
        r = d.post('/api/pro/escanear', {'code': wpro.booking_code(self.bB, tok)})
        self.assertIn(r.status, (200, 403, 404))
        if r.status == 200:
            self.assertNotIn('booking', r.json)           # «otro centro», never the card of the booking
        pid = self.server.sql('SELECT id FROM dive_points WHERE active=1 LIMIT 1')[0]['id']
        self.assertEqual(d.post('/api/marina/video', {'point_id': pid, 'url': 'https://www.youtube.com/watch?v=dQw4w9WgXcQ'}).status, 403)
        self.assertEqual(self.snapshot_b(), before)

    def test_a01_centro_no_lee_ni_cambia_datos_de_otro_centro_por_id(self):
        A, before = self.A, self.snapshot_b()
        calls = [('GET', f'/api/bookings/{self.bB}', None, (404,)), ('GET', f'/api/bookings/{self.bB}/receipt.pdf', None, (404,)),
                 ('GET', f'/api/manifest/{self.slB}', None, (404,)),
                 ('POST', f'/api/bookings/{self.bB}/status', {'status': 'cancelled'}, (404,)),
                 ('POST', f'/api/bookings/{self.bB}/payment', {'payment_status': 'paid'}, (404,)),
                 ('POST', '/api/provider-services/update', {'id': self.sB, 'title': 'Robado', 'price': 1}, (404,)),
                 ('POST', '/api/provider-services/delete', {'id': self.sB}, (404,)),
                 ('POST', '/api/provider-services/slot-close', {'slot_id': self.slB}, (404,)),
                 ('POST', '/api/center/extras/save', {'id': self.extraB, 'name': 'Robado', 'price': 0}, (403, 404)),
                 ('POST', '/api/center/extras/delete', {'id': self.extraB}, (200, 403, 404)),     # 200 = «nada que borrar»: checked by the snapshot
                 ('POST', '/api/service-templates/delete', {'id': self.tplB}, (403, 404)),
                 ('POST', '/api/service-templates/save', {'id': self.tplB, 'name': 'Robada'}, (403, 404)),
                 ('POST', '/api/manifest/boats/save', {'id': self.boatB, 'name': 'Robado', 'capacity': 2}, (404,)),
                 ('POST', '/api/center/tariffs/save', {'service_id': self.sB, 'price': 1, 'effective_from': DAY(2)}, (404,)),
                 ('POST', '/api/center/tariffs/history-delete', {'id': self.tariffB}, (400, 404)),
                 ('POST', '/api/center/team/role', {'user_id': self.memB.user['id'], 'member_role': 'owner'}, (404,)),
                 ('POST', '/api/center/team/remove', {'user_id': self.memB.user['id']}, (404,)),
                 ('POST', '/api/center/team/invite/revoke', {'id': self.invB}, (400, 404))]
        if self.pB:
            calls += [('GET', f'/api/center/promotions/{self.pB}/codes', None, (404,)), ('POST', f'/api/center/promotions/{self.pB}/status', {'status': 'archived'}, (404,)),
                      ('POST', f'/api/center/promotions/{self.pB}/assign', {'user_ids': [self.diver2.user['id']]}, (404,))]
        bad = []
        for method, path, body, ok in calls:
            r = A.get(path) if method == 'GET' else A.post(path, body)
            if r.status not in ok: bad.append(f'{method} {path} → {r.status} {r.body[:100]!r}')
        self.assertEqual(bad, [], '\n'.join(bad))
        # Lists: A never sees B's clients nor B's paused services.
        self.assertNotIn(self.diver2.user['id'], [c['id'] for c in A.get('/api/center/clients').json['items']])
        items = A.get(f"/api/provider-services?provider_id={self.B.user['id']}&include_inactive=1").json['items']
        self.assertNotIn(self.sB_paused, [s['id'] for s in items])
        self.assertEqual(self.snapshot_b(), before, 'Los datos del centro B han cambiado')

    def test_a01_buceador_no_toca_datos_de_otro_buceador(self):
        d, d2 = self.diver, self.diver2
        lid = d2.post('/api/logbook', {'dive_date': '2026-05-01', 'site': 'Portitxol', 'depth': 12, 'duration': 40}).json['id']
        doc = d2.upload('/api/account/documents', {'document_type': 'Seguro', 'title': 'Seguro'}, 's.pdf', PDF_BYTES).json['id']
        self.assertEqual(d.get(f'/api/bookings/{self.bB}').status, 404)
        self.assertIn(d.post(f'/api/bookings/{self.bB}/cancel', {}).status, (403, 404))
        self.assertIn(d.post(f'/api/bookings/{self.bB}/change-date', {'slot_id': self.slB}).status, (403, 404))
        self.assertEqual(d.get(f'/api/bookings/{self.bB}/reschedule-options').status, 404)
        self.assertIn(d.post('/api/payments/checkout', {'booking_id': self.bB}).status, (403, 404))
        self.assertEqual(d.post('/api/logbook/update', {'id': lid, 'dive_date': '2026-05-01', 'site': 'Robado'}).status, 404)
        self.assertEqual(d.post('/api/logbook/delete', {'id': lid}).status, 404)
        self.assertEqual(d.get(f'/api/documents/file/{doc}').status, 404)
        self.assertEqual(d.post('/api/account/documents/delete', {'id': doc}).status, 404)
        self.assertEqual(self.server.sql('SELECT site FROM logbook_entries WHERE id=?', (lid,))[0]['site'], 'Portitxol')

    def test_a01_csrf_post_de_otro_origen_rechazado_aunque_haya_sesion(self):
        d = self.make_diver('s51csrf')
        base = self.server.base
        for origin in ('https://evil.example', 'null', base + '.evil.example', 'http://127.0.0.1.evil.example'):
            r = d.request('POST', '/api/account/language', {'lang': 'en'}, headers={'Origin': origin})
            self.assertEqual(r.status, 403, origin)
        d.origin = None
        self.assertEqual(d.request('POST', '/api/account/language', {'lang': 'en'}).status, 403)                       # neither Origin nor Referer
        self.assertEqual(d.request('POST', '/api/account/language', {'lang': 'en'}, headers={'Referer': base + '/#/cuenta'}).status, 200)
        d.origin = base
        lang = self.server.sql('SELECT preferred_language FROM user_profiles WHERE user_id=?', (d.user['id'],))[0]['preferred_language']
        self.assertEqual(lang, 'en')                                                                                  # only the same-origin one
        self.assertEqual(self.admin.request('DELETE', '/api/dive-points/1', headers={'Origin': 'https://evil.example'}).status, 403)

    def test_a01_equipo_respeta_permisos_en_las_rutas_principales(self):
        """Control positivo: las rutas «oficiales» de la ficha y la política sí comprueban el permiso «centro»."""
        self.assertEqual(self.recA.post('/api/provider/center-update', {'name': 'X'}).status, 403)
        self.assertEqual(self.recA.post('/api/provider/cancellation-policy', {'cancel_free_hours': 1, 'cancel_refund_pct': 100}).status, 403)
        self.assertEqual(self.insA.get('/api/provider/stats').status, 403)
        self.assertEqual(self.insA.get('/api/provider/payments').status, 403)

    def test_hallazgo_a01_recepcion_cambia_la_ficha_publica_con_api_center_profile(self):
        """HALLAZGO A01-1 (media). /api/center/profile no está en wod/roles.py:REGLAS_POST «centro» y cae en «reservas»:
        recepción (o un perfil propio con «reservas») cambia nombre, email, teléfono y web públicos del centro.
        Corrección: añadir '/api/center/profile' a la regla 'centro' de REGLAS_POST."""
        cols = 'name,country,region,city,address,website,phone,email,description,specialties,latitude,longitude'
        before = self.server.sql(f'SELECT {cols} FROM centers WHERE id=?', (self.cidA,))[0]
        r = self.recA.post('/api/center/profile', {'name': before['name'], 'country': 'España', 'city': 'Xàbia', 'email': 'desvio@evil.example',
                                                    'phone': '+34 000 000', 'website': 'https://evil.example', 'latitude': 38.79, 'longitude': 0.18})
        after = self.server.sql('SELECT email FROM centers WHERE id=?', (self.cidA,))[0]['email']
        self.server.sql(f"UPDATE centers SET {','.join(c + '=?' for c in cols.split(','))} WHERE id=?", (*before.values(), self.cidA))
        self.assertEqual(r.status, 403, 'recepción no debería poder cambiar la ficha pública del centro')
        self.assertEqual(after, before['email'])

    def test_hallazgo_a01_recepcion_cambia_la_politica_de_cancelacion_con_el_alias(self):
        """HALLAZGO A01-1 (media). '/api/center/cancellation-policy' es un alias de '/api/provider/cancellation-policy'
        (app/server.py:12796) y solo el segundo está en la regla 'centro': recepción fija el reembolso al 100 % o al 0 %.
        Corrección: añadir '/api/center/cancellation-policy' a la regla 'centro' de wod/roles.py:REGLAS_POST."""
        before = self.server.sql('SELECT cancel_free_hours,cancel_refund_pct FROM centers WHERE id=?', (self.cidA,))[0]
        r = self.recA.post('/api/center/cancellation-policy', {'cancel_free_hours': 1, 'cancel_refund_pct': 100})
        self.server.sql('UPDATE centers SET cancel_free_hours=?,cancel_refund_pct=? WHERE id=?', (before['cancel_free_hours'], before['cancel_refund_pct'], self.cidA))
        self.assertEqual(r.status, 403)

    def test_hallazgo_a01_recepcion_cambia_logo_y_redes_del_centro(self):
        """HALLAZGO A01-1 (media). '/api/provider/avatar' (logo del centro) y '/api/provider/profile' (redes sociales del
        centro) no están en la regla 'centro'. Corrección: añadirlos a 'centro' en wod/roles.py:REGLAS_POST."""
        r1 = self.recA.upload('/api/provider/avatar', {}, 'logo.png', tiny_png())
        r2 = self.recA.post('/api/provider/profile', {'provider_bio': 'x', 'instagram_url': 'https://evil.example/'})
        self.assertEqual((r1.status, r2.status), (403, 403))

    def test_hallazgo_a01_instructor_ve_los_ingresos_en_center_analytics(self):
        """HALLAZGO A01-1 (media). GET /api/center/analytics devuelve ingresos y reservas del centro a cualquier miembro
        (app/server.py:10569) aunque /api/provider/stats exige «estadisticas» y los cobros «cobros». Un instructor (solo
        «checkin») ve los ingresos. Corrección: añadir '/api/center/analytics' a REGLAS_GET con 'estadisticas'."""
        r = self.insA.get('/api/center/analytics')
        self.assertIn(r.status, (403, 404), f'el instructor ve {list((r.json or {}).get("metrics", {}))}')

    # ======================================================================================== A02 · criptografía
    def test_a02_contrasenas_con_pbkdf2_sal_unica_y_nunca_en_claro(self):
        a, b = self.make_diver('s51pwa'), self.make_diver('s51pwb')       # same password for both
        rows = self.server.sql('SELECT password_hash FROM users WHERE id IN (?,?)', (a.user['id'], b.user['id']))
        salts = set()
        for r in rows:
            algo, it, salt, digest = r['password_hash'].split('$')
            self.assertEqual(algo, 'pbkdf2_sha256')
            self.assertGreaterEqual(int(it), int(self.server.env['WOD_PBKDF2_ITERATIONS']))
            raw = base64.urlsafe_b64decode(salt + '=' * (-len(salt) % 4))
            self.assertGreaterEqual(len(raw), 16)
            salts.add(salt)
        self.assertEqual(len(salts), 2, 'dos cuentas con la misma contraseña deben tener sal distinta')
        # Default cost in production (the tests lower it to 100 000 to go faster): 600 000, as OWASP recommends for PBKDF2-SHA256.
        self.assertRegex((APP / 'wod' / 'config.py').read_text(encoding='utf-8'), r"WOD_PBKDF2_ITERATIONS',\s*600_000")
        blob = b''.join(p.read_bytes() for p in self.server.tmp.glob('test.sqlite3*'))
        self.assertNotIn(PASSWORD.encode(), blob)

    def test_hallazgo_a02_secreto_totp_guardado_en_claro(self):
        """HALLAZGO A02-1 (baja). users.totp_secret / totp_pending_secret se guardan en claro (app/server.py:11596 y 11606):
        quien lea la base o una copia (sin cifrar, ver A02-2) genera los códigos del segundo factor.
        Corrección: guardarlos con wod.cifrado.encrypt_secret() y abrirlos con decrypt_secret() en check_totp_or_recovery."""
        d = self.make_diver('s51totp')
        sec = d.post('/api/account/totp/setup', {'password': PASSWORD}).json['secret']
        self.assertEqual(d.post('/api/account/totp/enable', {'code': _code_at(sec)}).status, 200)
        stored = self.server.sql('SELECT totp_secret FROM users WHERE id=?', (d.user['id'],))[0]['totp_secret']
        self.assertNotIn(sec, str(stored), 'el secreto TOTP está en claro en la base')

    def test_hallazgo_a02_fotos_publicas_conservan_exif_y_gps(self):
        """HALLAZGO A02-3 (baja, privacidad). save_public_image (app/server.py:2865) guarda la foto tal cual: el logo, la
        portada, la galería o las fotos de un punto conservan EXIF (GPS, cámara). Corrección: reescribir la imagen sin
        metadatos con wod.imagenes (Pillow) antes de guardarla."""
        try:
            from PIL import Image
        except ImportError:
            self.skipTest('Pillow no está instalado')
        im = Image.new('RGB', (200, 200), (10, 40, 80)); ex = Image.Exif()
        ex[0x010f] = 'CamaraSecretaWOD'; ex[0x8825] = {1: 'N', 2: (38.0, 47.0, 12.0), 3: 'E', 4: (0.0, 11.0, 5.0)}
        buf = io.BytesIO(); im.save(buf, 'JPEG', exif=ex.tobytes())
        r = self.A.upload('/api/provider/avatar', {}, 'logo.jpg', buf.getvalue())
        self.assertEqual(r.status, 200, r)
        served = self.client().get(r.json['url']).body
        self.assertNotIn(b'CamaraSecretaWOD', served)
        self.assertNotIn(b'Exif\x00\x00', served)

    # ======================================================================================== A03 · inyección y XSS
    def test_a03_inyeccion_sql_en_login_y_busquedas_no_tiene_efecto(self):
        c = self.client()
        r = c.request('POST', '/api/auth/login', {'login': "' OR '1'='1' --", 'password': "' OR '1'='1"}, headers=self.ip(30))
        self.assertEqual(r.status, 401)
        r = c.request('POST', '/api/auth/login', {'login': "diver_s51d'--", 'password': 'x'}, headers=self.ip(31))
        self.assertEqual(r.status, 401)
        payload = "x' UNION SELECT password_hash,email FROM users--"
        for path in ('/api/point-directory?q=', '/api/center-directory?q=', '/api/centers?q=', '/api/dive-points?q='):
            r = c.get(path + payload.replace(' ', '%20'))
            self.assertLess(r.status, 500, path)
            self.assertNotIn(b'pbkdf2_sha256', r.body, path)
        r = self.A.get('/api/bookings?q=' + payload.replace(' ', '%20') + '&order=id;DROP%20TABLE%20users&limit=1%20OR%201=1')
        self.assertLess(r.status, 500)
        self.assertNotIn(b'pbkdf2_sha256', r.body)
        self.assertTrue(self.server.sql('SELECT COUNT(*) n FROM users')[0]['n'] > 0)

    def test_a03_html_generado_por_el_servidor_escapado(self):
        name = self.server.sql('SELECT name FROM centers WHERE id=?', (self.cidB,))[0]['name']
        evil = '<img src=x onerror=alert(1)><script>alert(2)</script>'
        self.server.sql('UPDATE centers SET name=? WHERE id=?', (evil, self.cidB))
        try:
            r = self.client().get(f'/widget/center/{self.cidB}')
            self.assertEqual(r.status, 200)
            self.assertNotIn(b'<img src=x', r.body); self.assertNotIn(b'<script>', r.body)
            self.assertIn(b'&lt;img', r.body)
            self.assertIn("default-src 'none'", r.headers.get('Content-Security-Policy', ''))
        finally:
            self.server.sql('UPDATE centers SET name=? WHERE id=?', (name, self.cidB))
        r = self.client().get('/app/vuelta?esquema=com.worldives.app&session_id=%22%3E%3Cscript%3Ealert(1)%3C/script%3E&pago=x')
        self.assertEqual(r.status, 200)
        self.assertNotIn(b'<script', r.body)
        self.assertEqual(self.client().get('/app/vuelta?esquema=javascript:alert(1)').status, 404)

    # ======================================================================================== A04 · diseño
    def test_hallazgo_a04_denuncia_guarda_enlaces_javascript(self):
        """HALLAZGO A04-1 (baja). POST /api/reports (público, app/server.py:12870) guarda target_url sin comprobar el
        esquema y Administración → Legal lo pinta como <a href> (public/js/world-dives-v8.js:5335): un anónimo deja un
        enlace javascript:/data: para que lo pulse un administrador (lo frena la CSP, pero no debe guardarse).
        Corrección: target=wsec.clean_http_url(...) (o aceptar solo rutas #/… del propio sitio)."""
        reason = list(self.client().get('/api/legal/info').json['reasons'])[0]
        r = self.client().request('POST', '/api/reports', {'reason': reason, 'details': 'Contenido falso en la ficha del centro, revisadlo.', 'name': 'Ana Prueba',
                                                           'email': 'ana@example.org', 'good_faith': True, 'target_url': 'javascript:alert(document.cookie)'}, headers=self.ip(40))
        stored = self.server.sql("SELECT COUNT(*) n FROM content_reports WHERE target_url LIKE 'javascript:%'")[0]['n']
        self.assertEqual((r.status, stored), (400, 0))

    # ======================================================================================== A05 · configuración
    def test_a05_cabeceras_de_seguridad_en_html_api_estaticos_y_errores(self):
        c = self.client()
        for path in ('/', '/api/health', '/api/me', '/js/world-dives-v8.js', '/css/world-dives-v8.css', '/api/no-existe', '/no-existe/ruta'):
            r = c.get(path)
            h = {k.lower(): v for k, v in r.headers.items()}
            csp = h.get('content-security-policy', '')
            self.assertIn("script-src 'self'", csp, path)
            self.assertNotIn("'unsafe-inline'", csp.split('script-src', 1)[1].split(';')[0], path)
            self.assertIn("frame-ancestors 'none'", csp, path)
            self.assertIn("object-src 'none'", csp, path)
            self.assertEqual(h.get('x-frame-options'), 'DENY', path)
            self.assertEqual(h.get('x-content-type-options'), 'nosniff', path)
            self.assertEqual(h.get('referrer-policy'), 'strict-origin-when-cross-origin', path)
            self.assertIn('camera=()', h.get('permissions-policy', ''), path)
            self.assertNotIn('access-control-allow-origin', h, path)
            if path.startswith('/api/'): self.assertEqual(h.get('cache-control'), 'no-store', path)
        # Development server (http): no HSTS here; the https case is checked in ConHttps.
        self.assertNotIn('Strict-Transport-Security', c.get('/').headers)

    def test_a05_rutas_de_archivos_sin_salto_de_directorio(self):
        c = self.client()
        for path in ('/js/..%2f..%2fapp%2fserver.py', '/css/%2e%2e/%2e%2e/.env.example', '/assets/uploads/..%2f..%2f..%2fapp%2fserver.py',
                     '/img/../../app/server.py', '/storage/documents/x.pdf', '/tiles/..%2f..%2fapp%2fserver.py.pmtiles'):
            r = c.get(path)
            self.assertIn(r.status, (403, 404), path)
            self.assertNotIn(b'def do_GET', r.body, path)

    def test_hallazgo_a05_cabecera_server_revela_la_version_de_python(self):
        """HALLAZGO A05-1 (baja). Handler solo cambia server_version (app/server.py:9746); BaseHTTPRequestHandler añade
        sys_version: «Server: WORLDIVES Python/3.x.y». Corrección: sys_version = '' en la clase Handler."""
        self.assertNotIn('Python/', self.client().get('/api/health').headers.get('Server', ''))

    def test_hallazgo_a05_error_de_integridad_devuelve_el_detalle_interno(self):
        """HALLAZGO A05-2 (baja). do_POST responde a sqlite3.IntegrityError con 'detail': str(e) (app/server.py:13965):
        nombres de tablas, columnas y mensajes de los disparadores. Corrección: quitar 'detail' y registrar el error con
        log_exception()."""
        src = (APP / 'server.py').read_text(encoding='utf-8')
        self.assertIsNone(re.search(r"IntegrityError[^\n]*\n[^\n]*\n[^\n]*'detail'\s*:\s*str\(e\)", src))

    # ======================================================================================== A06 · componentes
    # (estático, ver la clase Estatico)

    # ======================================================================================== A07 · autenticación
    def test_a07_inicio_de_sesion_limitado_por_ip_y_cuenta(self):
        c = self.client()
        codes = [c.request('POST', '/api/auth/login', {'login': 'diver_s51e', 'password': f'mala-{i}-clave'}, headers=self.ip(50)).status for i in range(10)]
        self.assertIn(429, codes)
        codes = [c.request('POST', '/api/auth/login', {'login': f'nadie{i}@x.example', 'password': 'mala-clave-1'}, headers=self.ip(51)).status for i in range(45)]
        self.assertIn(429, codes, 'una sola IP no puede probar muchas cuentas')

    def test_hallazgo_a07_fuerza_bruta_distribuida_contra_una_cuenta(self):
        """HALLAZGO A07-1 (media). El límite de inicio de sesión es por «IP+cuenta» y por IP (app/server.py:1062-1063,
        11576-11580); no hay límite por cuenta: desde muchas IPs (botnet, o un /64 de IPv6) se prueban contraseñas sin fin
        contra la misma cuenta. Corrección: tercer RateLimiter por cuenta (24 fallos/15 min = LOGIN_MAX_ATTEMPTS*3, clave 'acct:'+login) que
        devuelva 429 sin revelar si la cuenta existe, y agrupar IPv6 por /64 en la clave de IP."""
        self.make_diver('s51bf')
        codes = []
        for i in range(30):
            r = self.client().request('POST', '/api/auth/login', {'login': 'diver_s51bf', 'password': f'intento-{i}-xx'}, headers={'X-Forwarded-For': f'203.0.113.{i + 1}'})
            codes.append(r.status)
        self.assertIn(429, codes, f'30 contraseñas falsas desde 30 IPs y ningún bloqueo: {codes}')

    def test_hallazgo_a07_enumeracion_de_cuentas_por_tiempo_de_respuesta(self):
        """HALLAZGO A07-2 (baja). Con un usuario inexistente el login responde sin calcular PBKDF2 (app/server.py:11579,
        «if not user or not verify_password»): ~10 veces más rápido, así se sabe qué emails tienen cuenta.
        Corrección: si no hay usuario, verificar contra un hash ficticio (wsec.verify_password(password, DUMMY_HASH))."""
        def timed(login, n):
            t0 = time.perf_counter()
            self.client().request('POST', '/api/auth/login', {'login': login, 'password': 'no-es-la-clave'}, headers={'X-Forwarded-For': f'192.0.2.{n}'})
            return time.perf_counter() - t0
        known, unknown = [], []
        for i in range(15):   # 15 of each, interleaved: one slow request (a disk write) does not move the median
            known.append(timed('diver_s51d', 10 + i)); unknown.append(timed(f'nadie-{uuid.uuid4().hex[:8]}@x.example', 40 + i))
        # Cost of one password check with the iterations of this test server, measured here.
        t0 = time.perf_counter(); hashlib.pbkdf2_hmac('sha256', b'x', b'0' * 16, int(self.server.env['WOD_PBKDF2_ITERATIONS'])); t_hash = time.perf_counter() - t0
        gap = statistics.median(known) - statistics.median(unknown)
        # Today the gap is one PBKDF2 (~60 ms with the 100 000 iterations of the tests); with a dummy check it is noise.
        self.assertLess(gap, 0.03, f'existe {statistics.median(known):.3f}s · no existe {statistics.median(unknown):.3f}s · un PBKDF2 {t_hash:.3f}s')

    def test_a07_recuperacion_y_restablecimiento_limitados(self):
        c = self.client()
        codes = [c.request('POST', '/api/auth/forgot', {'email': f'x{i}@nadie.example'}, headers=self.ip(60)).status for i in range(7)]
        self.assertIn(429, codes)
        codes = [c.request('POST', '/api/auth/reset', {'token': f'falso{i}', 'password': 'una-clave-larga-1'}, headers=self.ip(61)).status for i in range(7)]
        self.assertIn(429, codes)
        codes = [c.request('POST', '/api/auth/verify-email', {'token': f'falso{i}'}, headers=self.ip(62)).status for i in range(7)]
        self.assertIn(429, codes)

    def test_a07_segundo_factor_limitado(self):
        d = self.make_diver('s51tl')
        self.assertEqual(d.post('/api/account/totp/setup', {'password': PASSWORD}).status, 200)
        codes = [d.post('/api/account/totp/enable', {'code': '000000'}).status for _ in range(8)]
        self.assertIn(429, codes)

    def test_a07_cookie_de_sesion_httponly_samesite_y_caducidad(self):
        d = self.make_diver('s51ck')
        r = self.client().login('diver_s51ck')
        cookie = [v for k, v in r.headers.items() if k.lower() == 'set-cookie'][0]
        for flag in ('HttpOnly', 'SameSite=Lax', 'Path=/'):
            self.assertIn(flag, cookie)
        self.assertNotRegex(cookie, r'(?i)max-age|expires')          # session cookie: gone when the browser closes
        token_hash = self.server.sql('SELECT token_hash FROM sessions WHERE user_id=? ORDER BY created_at DESC', (d.user['id'],))[0]['token_hash']
        raw = cookie.split(';')[0].split('=', 1)[1]
        self.assertEqual(token_hash, hashlib.sha256(raw.encode()).hexdigest())   # only the hash is stored
        # 8 h after the start the session is over even if it was used a minute ago.
        self.assertTrue(d.me()['authenticated'])
        self.server.sql('UPDATE sessions SET created_at=created_at-?, last_seen=last_seen WHERE user_id=?', (9 * 3600, d.user['id']))
        self.assertFalse(d.me()['authenticated'])

    def test_a07_cambio_de_contrasena_restablecimiento_y_salida_cierran_sesiones(self):
        d = self.make_diver('s51ses')
        other = self.client(); self.assertEqual(other.login('diver_s51ses').status, 200)
        self.assertEqual(d.post('/api/account/password', {'current_password': PASSWORD, 'new_password': 'otra-clave-segura-1'}).status, 200)
        self.assertTrue(d.me()['authenticated']); self.assertFalse(other.me()['authenticated'])
        # Reset by email: every session is closed.
        r = self.client().request('POST', '/api/auth/forgot', {'email': 's51ses@diver.example.org'}, headers=self.ip(70))
        self.assertEqual(r.status, 200)
        text = self.server.sql("SELECT text FROM email_outbox WHERE template='password_reset' AND to_email='s51ses@diver.example.org' ORDER BY id DESC")[0]['text']
        tok = re.search(r'token=([A-Za-z0-9_\-]+)', text).group(1)
        self.assertEqual(self.client().request('POST', '/api/auth/reset', {'token': tok, 'password': 'tercera-clave-1'}, headers=self.ip(71)).status, 200)
        self.assertFalse(d.me()['authenticated'])
        self.assertEqual(self.client().request('POST', '/api/auth/reset', {'token': tok, 'password': 'cuarta-clave-1'}, headers=self.ip(72)).status, 400)  # one use
        # Logout deletes the session on the server: the old cookie is useless.
        e = self.client(); self.assertEqual(e.login('diver_s51ses', 'tercera-clave-1').status, 200)
        cookies = list(e.jar)
        self.assertEqual(e.post('/api/auth/logout').status, 200)
        f = self.client()
        for ck in cookies: f.jar.set_cookie(ck)
        self.assertFalse(f.me()['authenticated'])

    # ======================================================================================== A08 · integridad
    def test_a08_webhooks_e_integracion_exigen_firma_o_clave(self):
        raw = Client(self.server, origin=None)
        self.assertEqual(raw.post('/api/payments/webhook', {'type': 'checkout.session.completed'}, headers={'Stripe-Signature': 't=1,v1=00'}).status, 400)
        self.assertEqual(raw.post('/api/whatsapp/webhook', {'entry': []}, headers={'X-Hub-Signature-256': 'sha256=00'}).status, 403)
        self.assertEqual(raw.post('/api/integrations/bookings', {'booking_date': '2030-01-01'}).status, 403)
        self.assertEqual(raw.post('/api/integrations/bookings', {'booking_date': '2030-01-01'}, headers={'X-WORLDIVES-API-Key': 'wod_' + 'x' * 43}).status, 403)
        self.assertEqual(raw.get('/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=x&hub.challenge=hola').status, 403)

    def test_a08_subidas_comprueban_contenido_tamano_y_tipo_servido(self):
        A, d = self.A, self.make_diver('s51up')
        # Content checked by its first bytes, whatever the name or the type the browser says.
        self.assertEqual(d.upload('/api/account/documents', {'document_type': 'Seguro', 'title': 'x'}, 'seguro.pdf', b'MZ\x90\x00 ejecutable').status, 400)
        self.assertEqual(d.upload('/api/account/documents', {'document_type': 'Seguro', 'title': 'x'}, 'seguro.pdf', b'<html><script>alert(1)</script>').status, 400)
        self.assertEqual(A.upload('/api/provider/avatar', {}, 'logo.png', b'<html><script>alert(1)</script></html>').status, 400)
        self.assertEqual(A.upload('/api/provider/avatar', {}, 'logo.svg', b'<svg xmlns="http://www.w3.org/2000/svg" onload="alert(1)"/>').status, 400)
        self.assertEqual(A.upload('/api/provider/avatar', {}, 'logo.gif', b'GIF89a' + b'\x00' * 64).status, 400)
        self.assertEqual(A.upload('/api/provider/avatar', {}, 'logo.png', b'\x89PNG\r\n\x1a\n' + b'\x00' * (6 * 1024 * 1024 + 10)).status, 400)
        # A PNG with HTML appended is stored as .png and served as an image that the browser never sniffs as HTML.
        r = A.upload('/api/provider/avatar', {}, 'logo.html', tiny_png() + b'<html><script>alert(1)</script>')
        self.assertEqual(r.status, 200)
        self.assertTrue(r.json['url'].endswith('.png'))
        served = self.client().get(r.json['url'])
        self.assertEqual(served.headers.get('Content-Type'), 'image/png')
        self.assertEqual(served.headers.get('X-Content-Type-Options'), 'nosniff')
        # Bodies above the limit are refused from the headers, without reading them.
        conn = http.client.HTTPConnection('127.0.0.1', self.server.port, timeout=10)
        conn.putrequest('POST', '/api/account/documents')
        conn.putheader('Content-Type', 'multipart/form-data; boundary=x'); conn.putheader('Content-Length', str(200 * 1024 * 1024)); conn.putheader('Origin', self.server.base)
        conn.endheaders()
        self.assertEqual(conn.getresponse().status, 413)
        conn.close()

    # ======================================================================================== A09 · registro
    def test_a09_registro_de_accesos_sin_consulta_ni_ip_completa(self):
        self.client().request('GET', '/api/salidas-cercanas?lat=38.7123&lon=0.1777', headers={'X-Forwarded-For': '203.0.113.77'})
        time.sleep(0.3)
        log = (self.server.tmp / 'logs' / 'access.log').read_text()
        self.assertIn('/api/salidas-cercanas', log)
        self.assertNotIn('38.7123', log)
        self.assertNotIn('203.0.113.77', log)
        self.assertIn('203.0.113.0', log)

    def test_hallazgo_a09_tokens_de_la_ruta_quedan_en_el_registro(self):
        """HALLAZGO A09-1 (baja). log_message (app/server.py:9750) quita la consulta pero no los secretos que van en la
        ruta: /ical/<token>.ics (calendario privado de reservas, sin caducidad), /r/… y /api/r/… (enlaces firmados de los
        avisos). Quien lea logs/access.log abre el calendario del centro. Corrección: en log_message sustituir esos
        segmentos (re.sub(r'(/ical/)[^/ ]+(\\.ics)', r'\\1***\\2', …) y lo mismo para /r/ y /api/r/)."""
        tok = 'SECRETO' + uuid.uuid4().hex + 'XYZ'
        self.client().get(f'/ical/{tok}.ics')
        self.client().get(f'/api/r/a1.c.b2.{tok}')
        time.sleep(0.3)
        self.assertNotIn(tok, (self.server.tmp / 'logs' / 'access.log').read_text())

    def test_hallazgo_a09_intentos_fallidos_de_inicio_de_sesion_sin_auditoria(self):
        """HALLAZGO A09-2 (baja). Un inicio de sesión fallido o bloqueado (401/429) no deja rastro en audit_log ni avisa
        (app/server.py:11576-11580): solo una línea anónima en access.log. Corrección: audit(db, user['id'] or None,
        'login_failed', details={'ip': wsec.ip_hash(ip)}) y security_alert('login_bruteforce', …) al llegar al límite."""
        d = self.make_diver('s51aud')
        for i in range(3):
            self.client().request('POST', '/api/auth/login', {'login': 'diver_s51aud', 'password': f'mala-{i}-clave'}, headers={'X-Forwarded-For': f'192.0.2.{100 + i}'})
        rows = self.server.sql("SELECT COUNT(*) n FROM audit_log WHERE user_id=? AND action LIKE '%fail%'", (d.user['id'],))[0]['n']
        self.assertGreater(rows, 0)

    def test_hallazgo_a09_enlace_de_restablecimiento_legible_en_administracion(self):
        """HALLAZGO A09-3 (baja). email_outbox guarda el correo completo con el enlace de un solo uso y
        GET /api/admin/emails/<id> (app/server.py:10335) lo devuelve: un administrador (o quien tenga su sesión) usa el
        enlace de restablecimiento de cualquier cuenta. Lo mismo con verificación de email, invitación de equipo y borrado
        de cuenta. Corrección: guardar el texto con el token enmascarado (o borrar text/html al enviarlo) y no devolver
        los enlaces de esas plantillas en /api/admin/emails/<id>."""
        self.make_diver('s51adm')
        self.client().request('POST', '/api/auth/forgot', {'email': 's51adm@diver.example.org'}, headers=self.ip(80))
        items = self.admin.get('/api/admin/emails?template=password_reset&q=s51adm').json['items']
        self.assertTrue(items)
        body = self.admin.get(f"/api/admin/emails/{items[0]['id']}").body.decode('utf-8', 'replace')
        self.assertIsNone(re.search(r'token=[A-Za-z0-9_\-]{20,}', body), 'el administrador puede leer el enlace de restablecimiento')

    # ======================================================================================== A10 · SSRF
    def test_a10_ssrf_direcciones_internas_rechazadas(self):
        for url in ('https://127.0.0.1/x', 'https://localhost/x', 'https://169.254.169.254/latest/meta-data/', 'https://[::1]/x',
                    'http://example.com/v', 'https://example.com:8443/v', 'https://user:pw@example.com/v', 'file:///etc/passwd', 'gopher://x/'):
            r = self.admin.post('/api/marina/video/comprobar', {'url': url})
            self.assertEqual(r.status, 400, url)


class ConHttps(ServerTestCase):
    """A05: with a public https address the server adds HSTS, upgrade-insecure-requests and the Secure cookie."""
    extra_env = {'WOD_PUBLIC_URL': 'https://worldives.test'}

    def test_a05_hsts_y_cookie_secure_con_https(self):
        c = Client(self.server, origin='https://worldives.test')
        for path in ('/', '/api/health', '/js/world-dives-v8.js'):
            r = c.get(path)
            self.assertIn('max-age=31536000', r.headers.get('Strict-Transport-Security', ''), path)
            self.assertIn('upgrade-insecure-requests', r.headers.get('Content-Security-Policy', ''), path)
        r = c.register('Https Prueba', 'https-prueba@diver.example.org', 'https_prueba')
        self.assertEqual(r.status, 200, r)
        cookie = [v for k, v in r.headers.items() if k.lower() == 'set-cookie'][0]
        self.assertIn('; Secure', cookie)
        # The allowed origin is WOD_PUBLIC_URL: the plain-http one of the same host is another origin.
        self.assertEqual(Client(self.server, origin='http://worldives.test').post('/api/auth/login', {'login': 'a', 'password': 'b'}).status, 403)


class RegistroLimitado(ServerTestCase):
    extra_env = {'WOD_REGISTER_MAX_PER_HOUR': '3'}

    def test_a07_registro_limitado_por_ip(self):
        c = self.client()
        codes = [c.register(f'Alta {i}', f'alta{i}@diver.example.org', f'alta_{i}').status for i in range(5)]
        self.assertEqual(codes[:3], [200, 200, 200])
        self.assertIn(429, codes[3:])


# ============================================================================================ comprobaciones estáticas
class Estatico(unittest.TestCase):

    # ----------------------------------------------------------------------------------- A03 · SQL con f-strings
    def test_a03_sql_con_fstring_nunca_interpola_datos_de_la_peticion(self):
        """Every SQL f-string of app/ interpolates only constants, column/table names chosen by the code or '?' lists:
        never the body, the query string, the headers or the uploaded fields."""
        request_input = re.compile(r'\b(data|query|fields|files|body|params|qs)\s*(\.get\(|\[)|json_body|parse_qs|headers|self\.path|\.rfile')
        total, bad = 0, []
        for f in [APP / 'server.py', *sorted((APP / 'wod').glob('*.py'))]:
            tree = ast.parse(f.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if not isinstance(node, ast.JoinedStr): continue
                text = ''.join(v.value for v in node.values if isinstance(v, ast.Constant) and isinstance(v.value, str)).upper()
                if not re.search(r'\b(SELECT|UPDATE|INSERT INTO|DELETE FROM|WHERE)\b', text): continue
                total += 1
                for v in node.values:
                    if isinstance(v, ast.FormattedValue) and request_input.search(ast.unparse(v.value)):
                        bad.append(f'{f.relative_to(ROOT)}:{node.lineno}: {{{ast.unparse(v.value)}}}')
        self.assertGreater(total, 100, 'el analizador no encuentra las sentencias SQL')
        self.assertEqual(bad, [], 'SQL construido con datos de la petición:\n' + '\n'.join(bad))

    # ----------------------------------------------------------------------------------- A03 · XSS en la web
    def _wdmd(self, cases):
        node = shutil.which('node')
        if not node: self.skipTest('Node.js no está instalado')
        js = (ROOT / 'public' / 'js' / 'world-dives-v8.js').read_text(encoding='utf-8')
        esc = re.search(r'const escapeHtml = [^\n]+', js).group(0)
        start = js.index('function wdMd(md){'); i = js.index('{', start); depth = 0
        for j in range(i, len(js)):
            depth += js[j] == '{'; depth -= js[j] == '}'
            if depth == 0: break
        prog = f"{esc}\nconst wdFold=s=>String(s).toLowerCase();\n{js[start:j + 1]}\nconst c=JSON.parse(require('fs').readFileSync(0,'utf8'));process.stdout.write(JSON.stringify(c.map(wdMd)));"
        with tempfile.TemporaryDirectory() as tmp:
            p = Path(tmp) / 'md.js'; p.write_text(prog, encoding='utf-8')
            out = subprocess.run([node, str(p)], input=json.dumps(cases), capture_output=True, text=True, timeout=30)
        self.assertEqual(out.returncode, 0, out.stderr)
        return json.loads(out.stdout)

    def test_a03_markdown_de_los_textos_legales_escapa_html_y_enlaces(self):
        cases = ['<script>alert(1)</script>', '[pulsa](javascript:alert(1))', '[x](https://ok.example/" onmouseover="alert(1))',
                 '| <img src=x onerror=alert(1)> | b |\n|---|---|\n| c | <svg onload=alert(1)> |', '## <img src=x onerror=1>', '**<b>negrita</b>**',
                 '> <iframe src=https://evil.example></iframe>', '- [a](data:text/html,<script>alert(1)</script>)', 'www.example.org"><script>x</script>']
        from html.parser import HTMLParser

        class Tags(HTMLParser):
            def __init__(self):
                super().__init__(); self.found = []
            def handle_starttag(self, tag, attrs):
                self.found.append((tag, dict(attrs)))
        for src, out in zip(cases, self._wdmd(cases)):
            p = Tags(); p.feed(out); p.close()
            for tag, attrs in p.found:
                self.assertIn(tag, {'p', 'a', 'strong', 'h2', 'h3', 'ul', 'ol', 'li', 'blockquote', 'div', 'table', 'thead', 'tbody', 'tr', 'th', 'td', 'mark'}, (src, out))
                self.assertFalse([k for k in attrs if k.startswith('on')], (src, out))
                self.assertFalse(re.match(r'\s*(javascript|data|vbscript):', attrs.get('href') or '', re.I), (src, out))

    def test_hallazgo_a03_titulos_de_ventanas_sin_escapar(self):
        """HALLAZGO A03-1 (baja, la CSP impide ejecutar scripts). wdOpenModal() inserta title/subtitle como HTML
        (public/js/world-dives-v8.js:3310) y cuatro llamadas pasan texto de la base sin escapeHtml: título de la promoción
        (2237, 2249), nombre del tema (4071) y nombre del punto de buceo (4095; un punto lo crea cualquier centro).
        Inyección de HTML (enlaces o formularios falsos dentro del panel de otro usuario).
        Corrección: title:`Dar «${escapeHtml(p.title)}»`, etc."""
        js = (ROOT / 'public' / 'js' / 'world-dives-v8.js').read_text(encoding='utf-8')
        bad = []
        for m in re.finditer(r'wdOpenModal\(\{', js):
            chunk = js[m.end():m.end() + 600]
            for tm in re.finditer(r'\b(title|subtitle):`([^`]*)`', chunk):
                for expr in re.findall(r'\$\{([^{}]+)\}', tm.group(2)):
                    e = expr.strip()
                    if re.fullmatch(r'[\w$]+(\??\.[\w$]+)*\.(title|name|label|fullname|email|description|city|value_text)', e):
                        bad.append(f'línea {js.count(chr(10), 0, m.start()) + 1}: {tm.group(1)} con ${{{e}}}')
        self.assertEqual(bad, [], 'Títulos de ventana con texto sin escapar:\n' + '\n'.join(bad))

    # ----------------------------------------------------------------------------------- A06 · dependencias
    def test_hallazgo_a06_requirements_admite_versiones_vulnerables(self):
        """HALLAZGO A06-1 (baja). requirements.txt pide «Pillow>=10.0» y «cryptography>=42», y scripts/iniciar.py solo
        instala lo que falta: un servidor con Pillow 10.0.0 (libwebp CVE-2023-4863, corregido en 10.0.1; CVE-2024-28219 en
        10.3.0) lo conserva, y el servidor abre imágenes WebP subidas por los centros (wod/imagenes.py).
        Corrección: Pillow>=10.3.0, cryptography>=42.0.4 y fijar versiones con hashes (pip-compile --generate-hashes)."""
        req = (ROOT / 'requirements.txt').read_text(encoding='utf-8')
        # v50.51 (ASVS V15): every dependency with its exact tested version, never a range
        deps = [l.split('#')[0].strip() for l in req.splitlines() if l.split('#')[0].strip()]
        self.assertEqual([d for d in deps if not re.fullmatch(r'[A-Za-z0-9_.-]+==[\d.]+', d)], [], 'dependencias sin versión exacta')
        mins = {m.group(1).lower(): tuple(int(x) for x in m.group(2).split('.')) for m in re.finditer(r'^([A-Za-z0-9_.-]+)\s*(?:>=|==)\s*([\d.]+)', req, re.M)}
        need = {'pillow': (10, 3, 0), 'cryptography': (42, 0, 4)}
        low = {k: mins.get(k) for k, v in need.items() if mins.get(k, (0,)) + (0,) * (3 - len(mins.get(k, (0,)))) < v}
        self.assertEqual(low, {}, f'versiones mínimas por debajo de las corregidas: {low}')

    # ----------------------------------------------------------------------------------- secretos
    def test_secretos_fuera_del_codigo_y_env_example_vacio(self):
        self.assertIn('.env', (ROOT / '.gitignore').read_text(encoding='utf-8').split())
        env = (ROOT / '.env.example').read_text(encoding='utf-8')
        for var in ('WOD_SECRET_KEY', 'WOD_DATA_KEY', 'WOD_DATA_KEY_OLD', 'STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'STRIPE_CONNECT_WEBHOOK_SECRET',
                    'WOD_SMTP_PASSWORD', 'ARCGIS_API_KEY', 'WHATSAPP_APP_SECRET', 'WHATSAPP_VERIFY_TOKEN'):
            m = re.search(rf'^[ \t]*{var}[ \t]*=[ \t]*([^#\s][^#\n]*)', env, re.M)
            self.assertIsNone(m and m.group(1).strip() or None, f'.env.example trae un valor en {var}')
        pat = re.compile(r'sk_live_[A-Za-z0-9]{8,}|rk_live_[A-Za-z0-9]{8,}|whsec_[A-Za-z0-9]{24,}|-----BEGIN [A-Z ]*PRIVATE KEY-----|AKIA[0-9A-Z]{16}|AAP[KT][A-Za-z0-9_\-]{30,}')
        for f in [*APP.rglob('*.py'), *(ROOT / 'public' / 'js').glob('*.js'), ROOT / 'public' / 'index.html']:
            self.assertIsNone(pat.search(f.read_text(encoding='utf-8', errors='ignore')), str(f))

    def test_hallazgo_generar_zips_no_vigila_todas_las_claves(self):
        """HALLAZGO A05-3 (baja). scripts/generar_zips.py:57 SECRET_VARS no incluye WOD_DATA_KEY, WOD_DATA_KEY_OLD,
        WHATSAPP_APP_SECRET ni WHATSAPP_VERIFY_TOKEN: un .env.example con la clave de cifrado rellena saldría en el zip.
        Corrección: añadirlas a SECRET_VARS."""
        spec = importlib.util.spec_from_file_location('generar_zips_prueba', ROOT / 'scripts' / 'generar_zips.py')
        mod = importlib.util.module_from_spec(spec); spec.loader.exec_module(mod)
        missing = [v for v in ('WOD_DATA_KEY', 'WOD_DATA_KEY_OLD', 'WHATSAPP_APP_SECRET', 'WHATSAPP_VERIFY_TOKEN') if v not in mod.SECRET_VARS]
        self.assertEqual(missing, [])

    # ----------------------------------------------------------------------------------- A10 · SSRF (wod.remoto)
    def test_a10_guardia_ssrf_de_wod_remoto(self):
        from wod import remoto
        old = os.environ.pop('WOD_MEDIA_FETCH_BASE', None)
        try:
            for url in ('http://example.com/', 'https://127.0.0.1/', 'https://[::1]/', 'https://10.0.0.1/', 'https://user:pw@example.com/',
                        'https://example.com:8443/', 'ftp://example.com/', 'file:///etc/passwd'):
                with self.assertRaises(remoto.FetchError, msg=url):
                    remoto.check_url(url)
            self.assertFalse(remoto.public_host('localhost'))
            with self.assertRaises(remoto.FetchError):
                remoto.fetch('https://localhost/', kinds=('text/html',), max_bytes=1000)
        finally:
            if old is not None: os.environ['WOD_MEDIA_FETCH_BASE'] = old

    # ----------------------------------------------------------------------------------- copias de seguridad
    BACKUP_KEY = 'clave-de-las-copias-de-prueba-0123456789'

    def setUp(self):
        # The copies are encrypted with WOD_BACKUP_KEY (correction of A02-2): the checks below run with a test key.
        self._old_bk = os.environ.get('WOD_BACKUP_KEY'); os.environ['WOD_BACKUP_KEY'] = self.BACKUP_KEY

    def tearDown(self):
        if self._old_bk is None: os.environ.pop('WOD_BACKUP_KEY', None)
        else: os.environ['WOD_BACKUP_KEY'] = self._old_bk

    def _backup(self):
        from wod import backup
        tmp = Path(tempfile.mkdtemp(prefix='wod-backup-test-'))
        self.addCleanup(shutil.rmtree, tmp, True)
        db_path = tmp / 'worldives.sqlite3'
        c = sqlite3.connect(db_path); c.execute('CREATE TABLE users(id INTEGER PRIMARY KEY, email TEXT, totp_secret TEXT)')
        c.execute("INSERT INTO users(email,totp_secret) VALUES('cliente-secreto@example.org','JBSWY3DPEHPK3PXP')"); c.commit(); c.close()
        old = os.environ.get('WOD_BACKUP_DIR'); os.environ['WOD_BACKUP_DIR'] = str(tmp / 'copias')
        try:
            out = backup.backup_db(db_path)
        finally:
            if old is None: os.environ.pop('WOD_BACKUP_DIR', None)
            else: os.environ['WOD_BACKUP_DIR'] = old
        return backup, tmp, db_path, out

    def test_copias_de_seguridad_se_comprueban_y_se_restauran(self):
        backup, tmp, db_path, out = self._backup()
        self.assertTrue(out.exists())
        self.assertEqual(oct(out.stat().st_mode & 0o777), '0o600')
        self.assertTrue(backup.verify(out).startswith('ok'))
        target = tmp / 'restaurada.sqlite3'
        backup.restore(out, target)
        c = sqlite3.connect(target)
        try:
            self.assertEqual(c.execute('SELECT email FROM users').fetchone()[0], 'cliente-secreto@example.org')
        finally:
            c.close()

    def test_hallazgo_copias_de_seguridad_sin_cifrar(self):
        """HALLAZGO A02-2 (media). wod/backup.py:35 backup_db solo comprime con gzip y ship() (l. 92) las envía tal cual
        fuera del servidor (scripts/copia_externa.sh: rclone a un almacenamiento externo). Contienen emails, nombres,
        hashes, secretos TOTP en claro, correos con enlaces vivos y los documentos privados (backup_files). Quien acceda al
        almacenamiento externo los lee. Corrección: backup_db/backup_files cifran con AES-256-GCM y una WOD_BACKUP_KEY
        distinta de WOD_DATA_KEY (obligatoria en producción), y verify()/restore() descifran. Esta prueba la fija."""
        backup, tmp, db_path, out = self._backup()
        raw = out.read_bytes()
        try:
            raw = gzip.decompress(raw)
        except OSError:
            pass
        self.assertNotIn(b'SQLite format 3', raw[:100], 'la copia es una base SQLite legible')
        self.assertNotIn(b'cliente-secreto@example.org', raw)


if __name__ == '__main__':
    unittest.main(verbosity=2)
