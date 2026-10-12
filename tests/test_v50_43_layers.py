"""v50.43 · Fase 1C, points 9 and 10: map layers «Mapa», «Satélite», «Relieve».

- /api/map/config gives GEBCO with the exact layer name (GEBCO_LATEST, or GEBCO_LATEST_2 with WOD_GEBCO_LAYER) and
  the exact 2026 credit; anything else in WOD_GEBCO_LAYER is ignored.
- Without ARCGIS_API_KEY the satellite is disabled and our tile route never reaches Esri.
- The content security policy lets the browser load the GEBCO images.
- «Seguridad en el buceo» warns, in the 10 languages, that the GEBCO relief is not for navigation or safety at sea.
- The web keeps no «Mundo» button and uses the same selector on every map.
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from helpers import ServerTestCase

ROOT = Path(__file__).resolve().parents[1]
CREDIT = 'Imagery reproduced from the GEBCO_2026 Grid, GEBCO Compilation Group (2026) GEBCO 2026 Grid'
LANGS = ['es', 'en', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'ru', 'zh']


class LayersWithoutKey(ServerTestCase):
    def test_config_gebco_exact_and_satellite_off(self):
        c = self.client()
        cfg = c.get('/api/map/config').json
        self.assertEqual(cfg['bathymetry']['layers'], 'GEBCO_LATEST')
        self.assertEqual(cfg['bathymetry']['attribution'], CREDIT)
        self.assertTrue(cfg['bathymetry']['url'].startswith('https://wms.gebco.net/'))
        self.assertFalse(cfg['satellite']['enabled'])
        self.assertNotIn('arcgis', str(cfg).lower())   # never the public Esri server, never the key
        r = c.get('/api/tiles/satellite/3/2/4')
        self.assertEqual(r.status, 404)

    def test_csp_allows_gebco_images(self):
        r = self.client().get('/')
        csp = r.headers.get('Content-Security-Policy', '')
        img = re.search(r"img-src([^;]*)", csp).group(1)
        self.assertTrue(' https:' in img or 'wms.gebco.net' in img, csp)

    def test_safety_document_warns_in_10_languages(self):
        c = self.client()
        for lang in LANGS:
            md = (ROOT / 'app' / 'legal' / lang / 'seguridad.md').read_text(encoding='utf-8')
            self.assertIn('GEBCO', md, lang)
            self.assertIn(CREDIT, md, lang)
            doc = c.get(f'/api/legal/doc?slug=seguridad&lang={lang}').json
            self.assertIn(CREDIT, str(doc), lang)

    def test_same_selector_everywhere_without_mundo(self):
        js = (ROOT / 'public' / 'assets' / 'js' / 'world-dives-v8.js').read_text(encoding='utf-8')
        self.assertNotIn('data-mapmode="world"', js)
        self.assertNotIn('Relieve marino', js)
        self.assertEqual(js.count('${wdLayerToolbar()}'), 2)          # portada and Explorar
        self.assertEqual(js.count('wdLayerControl('), 5)              # definition + point page, 2 editors, «elegir en el mapa»
        self.assertNotIn('wdBaseLayer().addTo', js)                   # no map without the selector
        self.assertIn("transparent:false", js)


class LayersColourVariant(ServerTestCase):
    extra_env = {'WOD_GEBCO_LAYER': 'GEBCO_LATEST_2', 'ARCGIS_API_KEY': ''}

    def test_colour_variant(self):
        self.assertEqual(self.client().get('/api/map/config').json['bathymetry']['layers'], 'GEBCO_LATEST_2')


class LayersBadVariant(ServerTestCase):
    extra_env = {'WOD_GEBCO_LAYER': 'GEBCO<script>'}

    def test_unknown_layer_is_ignored(self):
        self.assertEqual(self.client().get('/api/map/config').json['bathymetry']['layers'], 'GEBCO_LATEST')


if __name__ == '__main__':
    unittest.main()
