"""v50.57 · Revisión general, Bloque 4.4: códigos QR con destinos predefinidos.

El destino se elige de una lista (nunca una dirección escrita a mano) y el QR lleva una dirección corta y estable
(/q/abc234) que solo puede ir a páginas de WORLDIVES; se decide al escanearlo, así que un QR impreso sigue funcionando
si cambia la ruta interna. Nombre interno, contador de escaneos (solo un número), «Probar enlace» (no cuenta), PNG en
alta resolución, SVG y PDF con el logo y un texto opcional. Los centros, desde su panel, con sus propios destinos."""
import io
import re
import unittest
from urllib.parse import quote

from helpers import ServerTestCase

PHONE = {'User-Agent': 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1'}
OTHER = {'User-Agent': 'Mozilla/5.0 (Linux; Android 14) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Mobile Safari/537.36'}


def outbox(server, template, to):
    return server.sql('SELECT * FROM email_outbox WHERE template=? AND to_email=? ORDER BY id DESC', (template, to))


class CodigosQR(ServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'qr1')
        cls.other = t.make_center(cls.admin, 'qr2')
        cls.diver = t.make_diver('qr3')
        cls.cid = cls.center.user['center_id']
        cls.point = cls.server.sql('SELECT id, name FROM dive_points WHERE active=1 LIMIT 1')[0]
        cls.offer = cls.server.sql('SELECT id, title FROM travel_offers WHERE active=1 LIMIT 1')[0]

    def make(self, client, path='/api/admin/short-links/save', **data):
        r = client.post(path, {'name': 'QR de prueba', **data})
        self.assertEqual(r.status, 200, r.json)
        return r.json['id']

    def item(self, client, sid, path='/api/admin/short-links'):
        return next(x for x in client.get(path).json['items'] if x['id'] == sid)

    def go(self, code, headers=PHONE, extra=''):
        r = self.client().get(f'/q/{code}{extra}', headers=dict(headers))
        self.assertEqual(r.status, 302, r.status)
        return r.headers['Location']

    # ------------------------------------------------------------------------------------------- administration
    def test_1_cada_destino_de_la_lista_lleva_a_su_pagina(self):
        want = {'portada': '/#/', 'registro_centro': '/#/registro?tipo=center', 'registro_buceador': '/#/registro?tipo=recreational',
                'registro_freelance': '/#/registro?tipo=freelance', 'puntos': '/#/puntos', 'centros': '/#/centros', 'experiencias': '/#/experiencias',
                'punto': f"/#/punto?id={self.point['id']}", 'centro': f'/#/centro?id={self.cid}', 'experiencia': f"/#/experiencia?id={self.offer['id']}"}
        refs = {'punto': self.point['id'], 'centro': self.cid, 'experiencia': self.offer['id']}
        dests = {d['key']: d for d in self.admin.get('/api/admin/short-links').json['dests']}
        self.assertEqual(set(dests), set(want) | {'app'})
        self.assertTrue(dests['app']['not_yet'])                                             # «cuando exista»
        for dest, path in want.items():
            sid = self.make(self.admin, dest=dest, ref_id=refs.get(dest), name=f'Feria · {dest}')
            it = self.item(self.admin, sid)
            self.assertRegex(it['code'], r'^[abcdefghjkmnpqrstuvwxyz23456789]{6}$')
            self.assertTrue(it['short_url'].endswith('/q/' + it['code']))
            self.assertEqual(self.go(it['code']), path, dest)
            self.assertTrue(it['target'].endswith(path)); self.assertFalse(it['broken'])
            if dest in refs: self.assertTrue(it['ref_name'])
        self.assertEqual(self.go(it['code'].upper()), path)                                  # also in capitals

    def test_2_nunca_una_direccion_escrita_a_mano(self):
        for bad in ({'dest': 'https://phishing.example/login'}, {'dest': 'url', 'url': 'https://otra.example'}, {'dest': ''}, {'dest': 'c_reservas'},
                    {'dest': 'punto'}, {'dest': 'punto', 'ref_id': 999999}, {'dest': 'centro', 'ref_id': 'x'}):
            r = self.admin.post('/api/admin/short-links/save', {'name': 'Mal', **bad})
            self.assertEqual(r.status, 400, (bad, r.json))
        r = self.admin.post('/api/admin/short-links/save', {'name': 'App', 'dest': 'app'})
        self.assertEqual(r.status, 400); self.assertIn('app', r.json['error'])
        r = self.admin.post('/api/admin/short-links/save', {'name': '  ', 'dest': 'portada'})
        self.assertEqual(r.status, 400); self.assertIn('nombre interno', r.json['error'])
        sid = self.make(self.admin, dest='portada', caption='x' * 300)
        self.assertEqual(len(self.item(self.admin, sid)['caption']), 80)
        # a code that does not exist (or no longer exists): the home page, never an error page or another site
        for code in ('zzzzzz', 'abc', 'ABCDEFGHIJ', 'a1l0oi'):
            self.assertEqual(self.client().get(f'/q/{code}').headers.get('Location'), '/#/', code)

    def test_3_escaneos_solo_un_numero(self):
        sid = self.make(self.admin, dest='registro_centro', name='Recepción feria Madrid', caption='Regístrate como centro')
        code = self.item(self.admin, sid)['code']
        self.go(code); self.go(code)                                                         # scanned twice: 2
        self.go(code, OTHER)                                                                 # another phone (the same Wi-Fi): 3
        self.go(code, extra='?prueba=1')                                                     # «Probar enlace»: not counted
        for ua in ('WhatsApp/2.23.20.0', 'facebookexternalhit/1.1', 'Mozilla/5.0 (compatible; Googlebot/2.1)', ''):
            self.go(code, {'User-Agent': ua})                                                # link previews and robots: not counted
        it = self.item(self.admin, sid)
        self.assertEqual(it['scans'], 3); self.assertTrue(it['last_scan_at'])
        cols = {r['name'] for r in self.server.sql('PRAGMA table_info(short_links)')}
        self.assertFalse(cols & {'ip', 'user_agent', 'user_id'}, cols)                       # nothing about who scanned

    def test_3b_nadie_lo_infla(self):
        code = self.item(self.admin, self.make(self.admin, dest='portada', name='Tope'))['code']
        for _ in range(65): self.go(code)
        self.assertEqual(next(x for x in self.admin.get('/api/admin/short-links').json['items'] if x['code'] == code)['scans'], 60)   # 60 per connection / 10 min

    def test_4_si_el_destino_desaparece_lleva_a_su_lista_y_se_avisa(self):
        sid = self.make(self.admin, dest='punto', ref_id=self.point['id'])
        self.server.sql('UPDATE dive_points SET active=0 WHERE id=?', (self.point['id'],))
        try:
            it = self.item(self.admin, sid)
            self.assertTrue(it['broken']); self.assertIsNone(it['ref_name'])
            self.assertEqual(self.go(it['code']), '/#/puntos')
        finally:
            self.server.sql('UPDATE dive_points SET active=1 WHERE id=?', (self.point['id'],))
        # changed later to another destination: the printed QR follows it
        self.assertEqual(self.admin.post('/api/admin/short-links/save', {'id': sid, 'name': 'Ahora centros', 'dest': 'centros'}).status, 200)
        self.assertEqual(self.go(self.item(self.admin, sid)['code']), '/#/centros')
        # deleted: the home page
        code = self.item(self.admin, sid)['code']
        self.assertEqual(self.admin.post('/api/admin/short-links/delete', {'id': sid}).status, 200)
        self.assertEqual(self.go(code), '/#/')
        self.assertEqual(self.admin.post('/api/admin/short-links/delete', {'id': sid}).status, 404)

    def test_5_buscador_de_puntos_centros_y_experiencias(self):
        r = self.admin.get('/api/admin/short-links/search?tipo=punto&q=' + quote(self.point['name'][:4])).json['items']
        self.assertIn(self.point['id'], [x['id'] for x in r])
        r = self.admin.get('/api/admin/short-links/search?tipo=centro&q=qr1').json['items']
        self.assertEqual([x['id'] for x in r], [self.cid])
        r = self.admin.get('/api/admin/short-links/search?tipo=experiencia&q=' + quote(self.offer['title'][:4])).json['items']
        self.assertIn(self.offer['id'], [x['id'] for x in r])
        self.assertEqual(self.admin.get('/api/admin/short-links/search?tipo=usuarios&q=a').status, 400)
        self.assertEqual(self.center.get('/api/admin/short-links/search?tipo=centro&q=a').status, 403)

    def test_6_png_svg_y_pdf(self):
        sid = self.make(self.admin, dest='registro_centro', caption='Regístrate como centro')
        it = self.item(self.admin, sid)
        svg = self.admin.get(f'/api/short-links/{sid}/qr.svg')
        self.assertEqual(svg.status, 200); self.assertIn('image/svg+xml', svg.headers['Content-Type']); self.assertIn(b'<svg', svg.body)
        png = self.admin.get(f'/api/short-links/{sid}/qr.png?descargar=1')
        self.assertEqual(png.status, 200); self.assertTrue(png.body.startswith(b'\x89PNG'))
        self.assertIn(f'qr-', png.headers['Content-Disposition']); self.assertIn(it['code'], png.headers['Content-Disposition'])
        from PIL import Image
        img = Image.open(io.BytesIO(png.body)); self.assertGreaterEqual(img.size[0], 2048)    # high resolution
        try:
            import cv2, numpy as np
        except ImportError:
            cv2 = None
        if cv2:
            data, _pts, _ = cv2.QRCodeDetector().detectAndDecode(np.array(img.convert('RGB').resize((600, 600))))
            self.assertEqual(data, it['short_url'])                                         # read as a phone reads it
        pdf = self.admin.get(f'/api/short-links/{sid}/qr.pdf?descargar=1&lang=en')
        self.assertEqual(pdf.status, 200); self.assertTrue(pdf.body.startswith(b'%PDF')); self.assertIn('application/pdf', pdf.headers['Content-Type'])
        self.assertGreater(len(pdf.body), 5000)

    # ------------------------------------------------------------------------------------------------- centres
    def test_7_los_qr_del_centro_van_a_sus_paginas(self):
        sid_svc = self.center.post('/api/provider-services', {'title': 'Bautizo QR', 'price': 60}).json['id']
        d = self.center.get('/api/center/short-links').json
        self.assertEqual([x['key'] for x in d['dests']], ['c_reservas', 'c_servicio', 'c_resena', 'c_ficha'])
        self.assertIn(sid_svc, [s['id'] for s in d['services']])
        P = '/api/center/short-links/save'
        a = self.make(self.center, P, dest='c_reservas'); b = self.make(self.center, P, dest='c_servicio', ref_id=sid_svc)
        c = self.make(self.center, P, dest='c_resena'); f = self.make(self.center, P, dest='c_ficha')
        mine = {x['id']: x for x in self.center.get('/api/center/short-links').json['items']}
        slug = re.search(r'/c/([a-z0-9-]+)', mine[a]['target']).group(1)
        self.assertEqual(self.go(mine[a]['code']), f'/c/{slug}')
        self.assertEqual(self.go(mine[b]['code']), f'/c/{slug}?servicio={sid_svc}')
        self.assertEqual(self.go(mine[c]['code']), f'/#/centro?id={self.cid}&resena=1')
        self.assertEqual(self.go(mine[f]['code']), f'/#/centro?id={self.cid}')
        # the centre changes the address of its page: the QR already printed follows it
        self.assertEqual(self.server.sql('UPDATE sales_settings SET slug=? WHERE provider_kind=? AND provider_id=?', ('bahia-nueva-qr', 'center', self.cid)), [])
        self.assertEqual(self.go(mine[a]['code']), '/c/bahia-nueva-qr')
        # the service is switched off: its page, and the panel says so
        self.server.sql('UPDATE provider_services SET active=0 WHERE id=?', (sid_svc,))
        self.assertEqual(self.go(mine[b]['code']), '/c/bahia-nueva-qr')
        self.assertTrue(self.item(self.center, b, '/api/center/short-links')['broken'])
        # only its own destinations and its own services
        other_svc = self.other.post('/api/provider-services', {'title': 'Ajeno', 'price': 10}).json['id']
        for bad in ({'dest': 'portada'}, {'dest': 'registro_centro'}, {'dest': 'c_servicio', 'ref_id': other_svc}):
            self.assertEqual(self.center.post(P, {'name': 'Mal', **bad}).status, 400, bad)
        dl = self.center.get(f'/api/short-links/{a}/qr.pdf')
        self.assertEqual(dl.status, 200); self.assertTrue(dl.body.startswith(b'%PDF'))

    def test_8_cada_uno_solo_ve_y_cambia_los_suyos(self):
        mine = self.make(self.center, '/api/center/short-links/save', dest='c_ficha', name='Solo mío')
        site = self.make(self.admin, dest='portada', name='De la web')
        self.assertNotIn(mine, [x['id'] for x in self.other.get('/api/center/short-links').json['items']])
        self.assertNotIn(site, [x['id'] for x in self.center.get('/api/center/short-links').json['items']])
        self.assertNotIn(mine, [x['id'] for x in self.admin.get('/api/admin/short-links').json['items']])
        self.assertEqual(self.other.post('/api/center/short-links/save', {'id': mine, 'name': 'Robado', 'dest': 'c_ficha'}).status, 404)
        self.assertEqual(self.other.post('/api/center/short-links/delete', {'id': mine}).status, 404)
        for c, sid in ((self.other, mine), (self.center, site), (self.diver, mine), (self.diver, site), (self.admin, mine)):
            self.assertIn(c.get(f'/api/short-links/{sid}/qr.svg').status, (403, 404), (c.user, sid))
        self.assertIn(self.client().get(f'/api/short-links/{mine}/qr.svg').status, (401, 403))
        for c in (self.center, self.diver, self.client()):
            self.assertIn(c.get('/api/admin/short-links').status, (401, 403))
            self.assertIn(c.post('/api/admin/short-links/save', {'name': 'x', 'dest': 'portada'}).status, (401, 403))
        self.assertIn(self.diver.get('/api/center/short-links').status, (401, 403, 404))   # 17/10 (1.7): a diver gets «no existe» on a professional route
        self.assertIn(self.admin.post('/api/center/short-links/save', {'name': 'x', 'dest': 'c_ficha'}).status, (400, 403))

    def test_9_el_equipo_sin_mi_centro_los_ve_pero_no_los_cambia(self):
        r = self.center.post('/api/center/team/invite', {'email': 'qr-rec@example.org', 'member_role': 'reception'})
        self.assertEqual(r.status, 200, r.json)
        tok = re.search(r'equipo\?token=([A-Za-z0-9_\-]+)', outbox(self.server, 'team_invite', 'qr-rec@example.org')[0]['text']).group(1)
        m = self.client()
        self.assertEqual(m.post('/api/team/join', {'token': tok, 'fullname': 'Persona Recepción', 'username': 'qr_rec', 'password': 'buceo-seguro-2026',
                                                   'accept_terms': True}).status, 200)
        self.assertEqual(m.get('/api/center/short-links').status, 200)
        self.assertEqual(m.post('/api/center/short-links/save', {'name': 'x', 'dest': 'c_ficha'}).status, 403)


if __name__ == '__main__':
    unittest.main()
