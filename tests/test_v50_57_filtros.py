"""v50.57 · Revisión general 3.3: los filtros de «Puntos de buceo».

Lo que se ve y se usa se prueba en el navegador (tests/navegador/e2e_v50_57_filtros.py, a 360, 390, 768, 1024 y
1440 px). Aquí, lo que no necesita navegador: qué va en la línea fija y qué en el panel de «Filtros», que todos los
filtros van a la dirección y que los textos nuevos están en los 9 idiomas."""
import json
import re
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh')


def render_points():
    src = (ROOT / 'public' / 'js' / 'world-dives-v8.js').read_text(encoding='utf-8')
    start = src.index('async function renderPoints(')
    return src[start:src.index('// ---------------------------------------------------------------- Ficha de punto', start)]


class FiltrosDePuntos(unittest.TestCase):

    def test_1_una_linea_fija_y_un_panel(self):
        fn = render_points()
        bar = fn[fn.index('<div class="pt-filters pt-bar" id="pt-filters">'):fn.index('<div class="pt-panel"')]
        for what in ('id="pt-q"', 'id="pt-filters-btn"', 'id="pt-sort"', 'data-view="list"', 'data-view="map"'):
            self.assertIn(what, bar)                       # the one line: search, «Filtros (n)», sort and list/map
        panel = fn[fn.index('<div class="pt-panel"'):fn.index('<div class="pt-scrim"')]
        for what in ('id="pt-area"', 'id="pt-type"', 'id="pt-level"', 'id="pt-depth"', 'data-only="centers"', 'data-only="instant"', 'id="pt-panel-clear"'):
            self.assertIn(what, panel)                     # the rest, in the panel
            self.assertNotIn(what, bar)
        self.assertIn('role="dialog"', panel)
        self.assertNotIn('PT_REGIONS_SHOWN', fn)           # the regions: all of them in one row that scrolls sideways
        self.assertIn('id="pt-active"', fn)                # the active filters, as chips with a ✕

    def test_2_cada_filtro_va_a_la_direccion(self):
        fn = render_points()
        query = re.search(r'const query=\(extra=\{\}\)=>\{ const qs=new URLSearchParams\(\{(.*?)\}\)', fn).group(1)
        for key in ('q', 'area', 'zone', 'type', 'level', 'depth', 'only', 'sort'):
            self.assertRegex(query, rf'\b{key}:st\.{key}\b')
        self.assertIn("if(st.view==='map') url.set('view','map')", fn)
        for key in ('q', 'area', 'zone', 'type', 'level', 'depth', 'only', 'sort', 'view'):
            self.assertIn(f"params.get('{key}')", fn)      # and the address gives them back

    def test_3_los_textos_nuevos_en_9_idiomas(self):
        exact = ('Filtros', 'Borrar todo', 'Filtros activos', 'Ver zonas anteriores', 'Ver más zonas', 'Ver resultados',
                 'Región', 'Todas', 'Ordenar', 'Lista', 'Mapa', 'Cerrar', 'Ver el punto', 'No hay puntos con estos filtros')
        patterns = ('Quitar filtro: {x}', 'Ver los {n} puntos')
        for lang in LANGS:
            pack = json.loads((ROOT / 'public' / 'idiomas' / f'{lang}.json').read_text(encoding='utf-8'))
            have = {p[0] for p in pack['patterns']}
            for text in exact: self.assertTrue(pack['exact'].get(text), (lang, text))
            for text in patterns: self.assertIn(text, have, (lang, text))


if __name__ == '__main__':
    unittest.main()
