"""v50.57 · Revisión general (15/10/2026), Bloque 1.2: el QR de la reserva.

- Un único generador (app/wod/qr.py) para toda la web: el SVG, el PNG, el PDF y la matriz del cartel son el mismo QR
  y se leen (se descodifican con OpenCV, como un móvil).
- La ficha de la reserva trae su QR dentro (sin una segunda petición de imagen): el buceador, el centro y la
  administración lo ven; lleva a la reserva correcta. Otro centro, sin permiso, no la ve; sin el código del QR tampoco.
- El justificante PDF lleva el QR y se lee (la página se dibuja con pdftoppm).
- El correo de la reserva confirmada lleva el QR como imagen del propio mensaje (no un enlace) y el código para dictar.
"""
from __future__ import annotations

import datetime as dt
import email
import io
import shutil
import subprocess
import sys
import tempfile
import time
import unittest
from email import policy
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ROOT, ServerTestCase  # noqa: E402
sys.path.insert(0, str(ROOT / 'app'))
from wod import qr as wqr  # noqa: E402

try:
    import cv2
    import numpy as np
    from PIL import Image
except ImportError:   # the decoding checks need OpenCV (not a dependency of the server)
    cv2 = None

DAY = (dt.date.today() + dt.timedelta(days=9)).isoformat()


def decode_png(raw: bytes) -> str:
    img = np.array(Image.open(io.BytesIO(raw)).convert('RGB'))
    return cv2.QRCodeDetector().detectAndDecode(img)[0]


def decode_svg(svg: bytes | str) -> str:
    """Draws the SVG in Chromium (as a browser does) and reads it."""
    from playwright.sync_api import sync_playwright
    sys.path.insert(0, str(ROOT / 'tests' / 'navegador'))
    from e2e_markers import chromium
    svg = svg.decode() if isinstance(svg, bytes) else svg
    with sync_playwright() as pw:
        br = chromium(pw); pg = br.new_page(viewport={'width': 420, 'height': 420})
        pg.set_content(f'<body style="margin:0;background:#fff"><div style="width:400px;height:400px">{svg}</div></body>')
        pg.eval_on_selector('svg', 'e=>{e.setAttribute("width","400");e.setAttribute("height","400")}')
        shot = pg.screenshot(); br.close()
    return decode_png(shot)


def rows_png(rows: list[str]) -> bytes:
    """The matrix of the poster drawn as the browser does (dark modules, quiet zone)."""
    n = len(rows); q = 4; img = Image.new('RGB', (n + 2 * q, n + 2 * q), 'white'); px = img.load()
    for y, r in enumerate(rows):
        for x, v in enumerate(r):
            if v == '1': px[x + q, y + q] = (0, 0, 0)
    img = img.resize(((n + 2 * q) * 8, (n + 2 * q) * 8), Image.NEAREST); buf = io.BytesIO(); img.save(buf, 'PNG'); return buf.getvalue()


@unittest.skipIf(cv2 is None, 'OpenCV no está instalado: no se pueden leer los QR')
class Generador(unittest.TestCase):
    URL = 'https://worlddivesdiscovery.com/#/verificarreserva?id=1319&t=Zx9-abc_DEF0123456789abcdefghijklmnop'

    def test_svg_png_pdf_y_matriz_son_el_mismo_qr_y_se_leen(self):
        self.assertEqual(decode_png(wqr.png(self.URL, scale=6)), self.URL)
        self.assertEqual(decode_svg(wqr.svg(self.URL)), self.URL)
        self.assertEqual(decode_png(rows_png(wqr.rows(self.URL))), self.URL)
        self.assertEqual(len(wqr.rows(self.URL)), len(wqr.matrix(self.URL)))

    def test_svg_ligero_una_sola_ruta(self):
        s = wqr.svg(self.URL).decode()
        self.assertEqual(s.count('<path'), 1); self.assertLess(len(s), 9000)   # before: one <rect> per module (~25 KB)

    def test_el_servidor_solo_usa_este_generador(self):
        src = (ROOT / 'app' / 'server.py').read_text(encoding='utf-8')
        self.assertNotIn('import qrcode', src); self.assertNotIn('SvgPathImage', src)


@unittest.skipIf(cv2 is None, 'OpenCV no está instalado: no se pueden leer los QR')
class QRDeLaReserva(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.extra_env = dict(cls.extra_env, WOD_MAINTENANCE_SECONDS='2')
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'qrres'); cls.other = t.make_center(cls.admin, 'qrotro')
        cls.diver = t.make_diver('qrres')
        cid = cls.center.user['center_id']
        cls.sid = cls.center.post('/api/provider-services', {'title': 'Inmersión con QR', 'price': 40, 'booking_mode': 'request', 'max_participants': 6}).json['id']
        cls.slot = cls.center.post('/api/provider-services/slot', {'service_id': cls.sid, 'slot_date': DAY, 'slot_time': '10:00', 'spots_total': 6}).json['slot_id']
        r = cls.diver.post('/api/bookings', {'center_id': cid, 'service_id': cls.sid, 'slot_id': cls.slot, 'participants': 1})
        assert r.status == 200, r.json
        cls.bid = r.json['id']
        assert cls.center.post(f'/api/bookings/{cls.bid}/status', {'status': 'confirmed'}).status == 200

    def check_url(self, url):
        q = parse_qs(urlparse(url).fragment.split('?', 1)[1]); self.assertEqual(q['id'], [str(self.bid)]); return q['t'][0]

    def test_ficha_con_el_qr_dentro_para_los_tres(self):
        for who in (self.diver, self.center, self.admin):
            r = who.get(f'/api/bookings/{self.bid}')
            self.assertEqual(r.status, 200, r.json)
            b = r.json['booking']
            self.assertTrue(b['qr_svg'].startswith('<svg'))
            self.assertEqual(decode_svg(b['qr_svg']), b['check_url'])
            self.check_url(b['check_url'])
            self.assertTrue(b['check_code'])

    def test_sin_permiso_no_se_ve(self):
        self.assertEqual(self.other.get(f'/api/bookings/{self.bid}').status, 404)
        self.assertEqual(self.other.get(f'/api/bookings/{self.bid}/qr.svg').status, 404)
        self.assertIn(self.client().get(f'/api/bookings/{self.bid}/qr.svg').status, (401, 403))

    def test_al_escanearlo_abre_la_reserva_correcta_solo_con_su_codigo(self):
        raw = self.diver.get(f'/api/bookings/{self.bid}/qr.svg').body
        url = decode_svg(raw); token = self.check_url(url)
        anon = self.client()
        r = anon.get(f'/api/public/bookings/{self.bid}?t={token}')
        self.assertEqual(r.status, 200); self.assertEqual(r.json['booking']['ref'], f'WOD-{self.bid:06d}')
        self.assertNotIn('email', r.json['booking']); self.assertNotIn('Pérez', r.json['booking']['customer'])   # never the surname
        self.assertEqual(anon.get(f'/api/public/bookings/{self.bid}').status, 404)
        self.assertEqual(anon.get(f'/api/public/bookings/{self.bid}?t={token[:-2]}xx').status, 404)
        self.assertEqual(anon.get(f'/api/public/bookings/{self.bid + 1}?t={token}').status, 404)

    @unittest.skipUnless(shutil.which('pdftoppm'), 'pdftoppm no está instalado')
    def test_el_justificante_pdf_lleva_el_qr(self):
        r = self.diver.get(f'/api/bookings/{self.bid}/receipt.pdf')
        self.assertEqual(r.status, 200)
        tmp = Path(tempfile.mkdtemp())
        (tmp / 'j.pdf').write_bytes(r.body)
        subprocess.run(['pdftoppm', '-r', '200', '-png', '-f', '1', '-l', '1', str(tmp / 'j.pdf'), str(tmp / 'p')], check=True)
        page = next(tmp.glob('p*.png')).read_bytes(); shutil.rmtree(tmp)
        self.check_url(decode_png(page))

    def test_el_correo_de_la_reserva_confirmada_lleva_el_qr(self):
        folder = Path(self.server.env['WOD_MAIL_FILE_DIR'])
        end = time.time() + 40; files = []
        while time.time() < end and not files:
            files = list(folder.glob('*booking_confirmed*.eml')); time.sleep(0.5)
        self.assertTrue(files, 'no ha salido el correo de la reserva confirmada')
        msg = email.message_from_bytes(files[0].read_bytes(), policy=policy.default)
        html = msg.get_body(('html',)).get_content()
        self.assertIn('cid:qr-reserva@worldives', html)
        pngs = [p for p in msg.walk() if p.get_content_type() == 'image/png']
        self.assertEqual(len(pngs), 1); self.assertEqual(pngs[0]['Content-ID'], '<qr-reserva@worldives>')
        self.check_url(decode_png(pngs[0].get_content()))
        txt = msg.get_body(('plain',)).get_content()
        code = self.diver.get(f'/api/bookings/{self.bid}').json['booking']['check_code']
        self.assertIn(code, txt)
        # the administration sees the email with a drawn example in place of the QR (the real one carries the token)
        eid = self.server.sql("SELECT id FROM email_outbox WHERE template='booking_confirmed' AND related_id=?", (self.bid,))[0]['id']
        r = self.admin.get(f'/api/admin/emails/{eid}'); self.assertEqual(r.status, 200, r.json)
        it = r.json['item']
        self.assertNotIn('inline_qr', it); self.assertNotIn('cid:', it['html']); self.assertIn('data:image/svg+xml', it['html'])


if __name__ == '__main__':
    unittest.main()
