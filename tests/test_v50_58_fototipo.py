"""v50.58 (revisión y usabilidad 15-16/10/2026, 6.4): la foto de cada tipo de buceo, en el servidor.

- Administración → Tipos de buceo sube la foto con la parte encuadrada en la vista previa (x, y, ancho y alto, en
  fracciones de la foto): el servidor corta esa parte, la deja en 1600 × 1000 y la guarda en WebP con sus copias de
  640, 960 y 1440 px (las mismas reglas que las fotos del titular, 6.1).
- Sin encuadre: el centro de la foto. Un encuadre roto o tan pequeño que se vería borroso, y una foto pequeña: un aviso.
- Al cambiarla o al «Restaurar original», se borran la foto anterior y sus copias. Solo la administración.
- Las demás imágenes de la web (las portadas) siguen como antes: un solo archivo.
"""
import io
import unittest

from helpers import ServerTestCase


def photo(w, h, left=(200, 30, 30), right=(20, 60, 200), fmt='JPEG'):
    """A real photo: the left half one colour and the right half another (to see which part was cut)."""
    from PIL import Image
    im = Image.new('RGB', (w, h), left)
    im.paste(Image.new('RGB', (w - w // 2, h), right), (w // 2, 0))
    buf = io.BytesIO(); im.save(buf, fmt, quality=92); return buf.getvalue()


class FotoPorTipo(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.admin = cls('run').make_admin()

    def files(self, url):
        base = url.rsplit('/', 1)[1][:-len('.webp')]
        up = self.server.tmp / 'uploads'
        return [up / f'{base}{s}.webp' for s in ('', '-640', '-960', '-1440')]

    def upload(self, key, content, client=None, **crop):
        fields = {'key': key, 'credit': 'Foto: WORLDIVES DISCOVERY', **{f'crop_{k}': str(v) for k, v in crop.items()}}
        return (client or self.admin).upload('/api/admin/site-media', fields, 'tipo.jpg', content)

    def test_1_recorte_en_webp_y_tres_tamanos(self):
        from PIL import Image
        # the right half of a 2000 × 1250 photo, top: x 0.5, w 0.5, h 0.5 (16:10)
        r = self.upload('type:canales', photo(2000, 1250), x=0.5, y=0, w=0.5, h=0.5)
        self.assertEqual(r.status, 200, r)
        url = r.json['url']
        self.assertRegex(url, r'^/assets/uploads/divetype_canales_[0-9a-f]{12}\.webp$')
        main, *copies = self.files(url)
        with Image.open(main) as im:
            self.assertEqual((im.format, im.size), ('WEBP', (1600, 1000)))
            px = im.convert('RGB').getpixel((800, 500))
            self.assertLess(px[0], 80, px); self.assertGreater(px[2], 150, px)   # only the blue half was kept
        for f, wdt in zip(copies, (640, 960, 1440)):
            with Image.open(f) as im: self.assertEqual((im.format, im.size), ('WEBP', (wdt, wdt * 10 // 16)), f.name)
        # served to the browser, the copies too
        for f in (main, *copies):
            g = self.client().get('/assets/uploads/' + f.name)
            self.assertEqual((g.status, g.headers.get('Content-Type')), (200, 'image/webp'), f.name)
        self.assertEqual(self.client().get('/api/site-media').json['items']['type:canales']['url'], url)
        # replaced: the photo before and its copies are deleted
        r2 = self.upload('type:canales', photo(1800, 1200))
        self.assertEqual(r2.status, 200, r2)
        self.assertFalse(any(f.exists() for f in self.files(url)), 'the old photo and its copies are deleted')
        self.assertTrue(all(f.exists() for f in self.files(r2.json['url'])))
        # «Restaurar original»: the type goes back to «no suitable photo» and its files are deleted
        self.assertEqual(self.admin.upload('/api/admin/site-media', {'key': 'type:canales', 'reset': '1'}, 'x.jpg', b'').status, 200)
        self.assertFalse(any(f.exists() for f in self.files(r2.json['url'])))
        it = self.client().get('/api/site-media').json['items']['type:canales']
        self.assertEqual((it['custom'], it['url']), (False, ''), 'canales has no suitable photo of its own: the sea colour')

    def test_2_sin_encuadre_el_centro_y_avisos(self):
        from PIL import Image
        # a panoramic photo, no frame: the centre, 16:10 (the half line in the middle: both colours)
        r = self.upload('type:lagos', photo(3000, 1000))
        self.assertEqual(r.status, 200, r)
        with Image.open(self.files(r.json['url'])[0]) as im:
            self.assertEqual(im.size, (1600, 1000)); rgb = im.convert('RGB')
            self.assertGreater(rgb.getpixel((100, 500))[0], 150); self.assertGreater(rgb.getpixel((1500, 500))[2], 150)
        for bad, text in (({'x': 'abc', 'y': 0, 'w': 1, 'h': 1}, 'no es válido'), ({'x': 0.2, 'y': 0, 'w': 1.5, 'h': 1}, 'no es válido'),
                          ({'x': 0, 'y': 0, 'w': 0.1, 'h': 0.1}, 'demasiado'), ({'x': 'nan', 'y': 0, 'w': 1, 'h': 1}, 'no es válido')):
            r = self.upload('type:lagos', photo(2000, 1250), **bad)
            self.assertEqual(r.status, 400, (bad, r)); self.assertIn(text, r.json['error'])
        r = self.upload('type:lagos', photo(600, 380))
        self.assertEqual(r.status, 400, r); self.assertIn('muy pequeña', r.json['error'])
        r = self.upload('type:lagos', b'<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        self.assertEqual(r.status, 400, r); self.assertIn('Formato no admitido', r.json['error'])

    def test_3_solo_la_administracion_y_las_portadas_como_antes(self):
        diver = self.make_diver('fototipo')
        self.assertEqual(self.upload('type:pilares', photo(1600, 1000), client=diver).status, 403)
        self.assertEqual(self.upload('type:no-existe', photo(1600, 1000)).status, 400)
        r = self.admin.upload('/api/admin/site-media', {'key': 'hero:home', 'credit': ''}, 'portada.jpg', photo(2400, 900))
        self.assertEqual(r.status, 200, r)
        self.assertRegex(r.json['url'], r'^/assets/uploads/site_hero_home_[0-9a-f]{16}\.jpg$')   # one file, as before


if __name__ == '__main__':
    unittest.main()
