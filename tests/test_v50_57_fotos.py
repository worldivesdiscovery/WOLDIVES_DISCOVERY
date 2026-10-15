"""v50.57 · Revisión general, Bloque 3.1: las fotos del titular.

Cada foto va donde encaja por su contenido (docs/fotos/README.md); los sitios sin foto adecuada se quedan sin foto (no se
rellenan al azar). Cada foto en WebP en 3 tamaños más el original y JPG de respaldo, con su licencia en los metadatos
(«Propiedad de WORLDIVES DISCOVERY») y en el registro de origen de las imágenes, su texto alternativo en los 9 idiomas
y su punto de enfoque. La foto que deja de usarse pasa a _archivo/ (no se borra) y su dirección antigua lleva a la que la
sustituye."""
import io
import json
import re
import unittest
from pathlib import Path

from helpers import ServerTestCase

ROOT = Path(__file__).resolve().parents[1]
PHOTOS = ('buceador-rayos', 'costa-barco', 'barco-cadena', 'nocturna-pulpo', 'caballito-posidonia')
LANGS = ('en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh')


def js():
    return (ROOT / 'public' / 'js' / 'world-dives-v8.js').read_text(encoding='utf-8')


def width(path):
    from PIL import Image
    with Image.open(path) as im: return im.width


class FotosDelTitular(ServerTestCase):

    def test_1_cada_foto_en_tres_tamanos_webp_y_jpg_con_su_licencia(self):
        from PIL import Image
        for name in PHOTOS:
            for suffix, ctype in (('.webp', 'image/webp'), ('-640.webp', 'image/webp'), ('-960.webp', 'image/webp'), ('-1440.webp', 'image/webp'), ('.jpg', 'image/jpeg')):
                r = self.client().get(f'/img/titular/{name}{suffix}')
                self.assertEqual((r.status, r.headers.get('Content-Type')), (200, ctype), name + suffix)
                with Image.open(io.BytesIO(r.body)) as im: exif = im.getexif()
                self.assertEqual(exif.get(0x8298), 'Propiedad de WORLDIVES DISCOVERY', name + suffix)   # EXIF Copyright
            self.assertEqual(width(ROOT / 'public' / 'img' / 'titular' / f'{name}-640.webp'), 640)

    def test_2_la_foto_retirada_va_al_archivo_y_su_direccion_lleva_a_la_nueva(self):
        self.assertFalse(list((ROOT / 'public' / 'img' / 'portada').glob('portada-arrecife*')))
        self.assertTrue((ROOT / '_archivo' / 'fotos' / 'portada' / 'portada-arrecife.webp').exists())   # archived, not deleted
        for old, new in (('/img/portada/portada-arrecife.webp', '/img/titular/buceador-rayos.webp'),
                         ('/img/portada/portada-arrecife-640.webp', '/img/titular/buceador-rayos-640.webp'),
                         ('/assets/images/portada-arrecife.webp', '/img/titular/buceador-rayos.webp')):   # the old /assets address: one jump
            r = self.client().get(old)
            self.assertEqual((r.status, r.headers.get('Location')), (301, new), old)
        self.assertEqual(self.client().get('/img/portada/fondo.webp').status, 200)   # the rest stay where they were

    def test_3_cada_foto_donde_encaja_y_los_sitios_sin_foto_adecuada_sin_foto(self):
        items = self.client().get('/api/site-media').json['items']
        url = lambda k: (items.get(k) or {}).get('url', '')
        self.assertEqual(url('hero:home'), '/img/titular/buceador-rayos.webp')          # wide sea with a diver: the home page
        self.assertEqual(url('hero:experiencias'), '/img/titular/barco-cadena.webp')    # boat: trips and liveaboards
        self.assertEqual(url('hero:explorar'), '/img/titular/costa-barco.webp')         # coast from the air: the map
        self.assertEqual(url('type:nocturnas'), '/img/titular/nocturna-pulpo.webp')
        self.assertEqual(url('type:muck'), '/img/titular/caballito-posidonia.webp')
        self.assertEqual(url('type:aguas-profundas'), '/img/titular/barco-cadena.webp')
        for k in ('cuevas-y-cavernas', 'canales', 'canones', 'pinaculos', 'corrientes-y-deriva', 'lagos', 'pilares'):
            self.assertEqual(url('type:' + k), '', k)                                   # no photo at random

    def test_4_el_registro_de_origen_dice_de_quien_son(self):
        admin = self.make_admin()
        items = {x['path']: x for x in admin.get('/api/admin/images').json['items']}
        for name in PHOTOS:
            it = items.get(f'/img/titular/{name}.webp')
            self.assertIsNotNone(it, name)
            self.assertEqual(it['origin'], 'Propiedad de WORLDIVES DISCOVERY')
            self.assertFalse(it['missing'])
        self.assertNotIn('/img/portada/portada-arrecife.webp', items)

    def test_5_la_web_y_el_servidor_dicen_lo_mismo(self):
        src = js(); py = (ROOT / 'app' / 'server.py').read_text(encoding='utf-8')
        web = dict(re.findall(r"'?([a-z-]+)'?:(null|'[a-z0-9-]+')", re.search(r'const TYPE_IMAGES=\{(.*?)\};', src).group(1)))
        web = {k: (None if v == 'null' else v.strip("'")) for k, v in web.items()}
        server = re.search(r'SITE_MEDIA_TYPE_DEFAULTS = \{(.*?)\}\n', py, re.S).group(1)
        server = {k: (None if v == 'None' else v.strip("'")) for k, v in re.findall(r"'([a-z-]+)':(None|'[a-z0-9-]+')", server)}
        self.assertEqual(web, server)
        defaults = dict(re.findall(r"'(hero:[a-z0-9]+)':'([^']+)'", re.search(r'const MEDIA_DEFAULTS=\{(.*?)\};', src).group(1)))
        for key, _l, _w, default, _s in re.findall(r"\('(hero:[a-z0-9]+)', '([^']*)', '([^']*)', '([^']*)', '([^']*)'\)", py):
            self.assertEqual(defaults.get(key), default, key)

    def test_6_texto_alternativo_en_9_idiomas_y_punto_de_enfoque(self):
        src = js()
        photos = dict(re.findall(r"'([a-z-]+)':\{alt:'([^']+)',focus:'(\d{1,3}% \d{1,3}%)'\}", src) and
                      [(n, (a, f)) for n, a, f in re.findall(r"'([a-z-]+)':\{alt:'([^']+)',focus:'(\d{1,3}% \d{1,3}%)'\}", src)])
        self.assertEqual(set(photos), set(PHOTOS))
        packs = {l: json.loads((ROOT / 'public' / 'idiomas' / f'{l}.json').read_text(encoding='utf-8'))['exact'] for l in LANGS}
        for name, (alt, focus) in photos.items():
            self.assertGreater(len(alt), 20, name)
            for l in LANGS: self.assertTrue(packs[l].get(alt), (name, l))
        widths = dict(re.findall(r"'titular/([a-z-]+)':(\d+)", re.search(r'const WD_IMG_W=\{(.*?)\};', src).group(1)))
        for name in PHOTOS:
            self.assertEqual(int(widths[name]), width(ROOT / 'public' / 'img' / 'titular' / f'{name}.webp'), name)


if __name__ == '__main__':
    unittest.main()
