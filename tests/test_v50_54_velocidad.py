"""v50.54 · punto 1 del encargo del 14/10/2026 (velocidad, Core Web Vitals), lo que se puede comprobar sin navegador:

- Las librerías del mapa no van en la página: se descargan solo cuando una pantalla dibuja un mapa (wdMaps).
- Las fotos que trae la web tienen copias ligeras de 640, 960 y 1440 px, y la tabla de anchos de world-dives-v8.js
  coincide con los archivos (si se cambia una foto y no se rehacen las copias, esta prueba lo dice).
- El paquete de idioma del visitante se pide junto con la página (preload), con la misma dirección que usa
  loadLanguagePack(); en español, o dentro de la app, no se pide nada. La respuesta lleva «Vary: Accept-Language».
"""
from __future__ import annotations

import re
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from helpers import ServerTestCase  # noqa: E402
import server  # noqa: E402

JS = (ROOT / 'public' / 'js' / 'world-dives-v8.js').read_text(encoding='utf-8')
INDEX = (ROOT / 'public' / 'index.html').read_text(encoding='utf-8')


class Estatico(unittest.TestCase):
    def test_map_libraries_load_on_demand(self):
        self.assertNotIn('/lib/', INDEX)                                       # nothing of the map in the page itself
        for lib in ('/lib/leaflet/leaflet.js', '/lib/markercluster/leaflet.markercluster.js',
                    '/lib/protomaps-leaflet/protomaps-leaflet.js', '/lib/protomaps-leaflet/wd-flavor.js',
                    '/lib/leaflet/leaflet.css', '/lib/markercluster/MarkerCluster.css'):
            self.assertIn(f"'{lib}'", JS)                                       # …but wdMaps() knows them
            self.assertTrue((ROOT / 'public' / lib.lstrip('/')).is_file(), lib)
        # every map is created after wdMaps(): no L.map( before the loader in the code that runs at start
        self.assertLess(JS.index('function wdMaps('), JS.index('L.map('))
        for map_id in ("'pp-map'", "'point-editor-map'", "'center-editor-map'"):
            i = JS.index(f'L.map({map_id}')
            self.assertIn('wdMaps()', JS[max(0, i - 400):i], map_id)

    def test_light_copies_match_the_table(self):
        from PIL import Image
        def width_of(f):
            with Image.open(f) as im: return im.size[0]
        table = dict(re.findall(r"'((?:portada|destinos)/[a-z0-9-]+)':(\d+)", re.search(r'const WD_IMG_W=\{([^}]*)\}', JS).group(1)))
        on_disk = {f'{d}/{f.stem}' for d in ('portada', 'destinos') for f in (ROOT / 'public' / 'img' / d).glob('*.webp')
                   if not re.search(r'-\d+$', f.stem)}
        self.assertEqual(set(table), on_disk)
        for name, width in table.items():
            original = ROOT / 'public' / 'img' / f'{name}.webp'
            self.assertEqual(width_of(original), int(width), name)
            for copy in (640, 960, 1440):
                f = ROOT / 'public' / 'img' / f'{name}-{copy}.webp'
                if copy < int(width):
                    self.assertTrue(f.is_file(), f)
                    self.assertEqual(width_of(f), copy, f)
                    self.assertLess(f.stat().st_size, original.stat().st_size, f)

    def test_version_of_the_language_pack(self):
        self.assertIn(f"const WD_I18N_VERSION='{server.APP_VERSION}'", JS)    # same address as the preload
        self.assertIn(f'?v={server.APP_VERSION}', INDEX)

    def test_language_guess(self):
        g = server.page_language_guess
        self.assertEqual(g('', 'en-US,en;q=0.9'), 'en')
        self.assertEqual(g('', 'es-ES,es;q=0.9,en;q=0.8'), 'es')
        self.assertEqual(g('', 'sv-SE,de-DE;q=0.8'), 'de')                    # first language the site has
        self.assertEqual(g('', 'zh-TW'), 'zh')
        self.assertEqual(g('', 'ru-RU'), 'en')                                # retired language → English
        self.assertEqual(g('', 'sv,da'), 'es')
        self.assertEqual(g('', None), 'es')
        self.assertEqual(g('fr', 'en-US'), 'fr')                              # ?lang= wins
        self.assertEqual(g('', 'de-DE', 'Mozilla/5.0 WorldivesApp/1.4'), 'es')   # the app chooses its own


class Pagina(ServerTestCase):
    def page(self, path='/', lang=None):
        r = self.client().get(path, headers={'Accept-Language': lang} if lang else None)
        self.assertEqual(r.status, 200); return r, r.body.decode('utf-8')

    def test_preload_of_the_visitor_language(self):
        r, html = self.page(lang='de-DE,de;q=0.9')
        self.assertIn(f'<link rel="preload" href="/idiomas/de.json?v={server.APP_VERSION}" as="fetch" crossorigin="anonymous">', html)
        self.assertEqual(r.headers.get('Vary'), 'Accept-Language')
        self.assertEqual(self.client().get(f'/idiomas/de.json?v={server.APP_VERSION}').status, 200)
        _, html = self.page('/?lang=it', lang='de-DE')
        self.assertIn('/idiomas/it.json?v=', html); self.assertNotIn('/idiomas/de.json', html)
        _, html = self.page(lang='es-ES,es;q=0.9')
        self.assertNotIn('rel="preload"', html)                               # Spanish needs no pack

    def test_light_copy_is_served(self):
        r = self.client().get('/img/portada/fondo-640.webp')
        self.assertEqual(r.status, 200); self.assertEqual(r.headers.get('Content-Type'), 'image/webp')
        r = self.client().get('/img/titular/buceador-rayos-640.webp')   # v50.57: the owner's photos have their copies too
        self.assertEqual(r.status, 200); self.assertEqual(r.headers.get('Content-Type'), 'image/webp')


if __name__ == '__main__':
    unittest.main()
