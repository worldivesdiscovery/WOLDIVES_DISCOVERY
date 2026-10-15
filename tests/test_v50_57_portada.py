"""v50.57 · Revisión general 5.4: la cabecera de la portada viene dibujada en la propia página.

Antes, la foto de la cabecera (lo más grande de la portada, el LCP) esperaba al programa principal de la web (1,2 MB):
5,9 s en un móvil con 4G lento. Ahora index.html trae la cabecera dibujada, con la misma foto (en sus tamaños), los
mismos textos en el idioma con el que empieza la página y la cinta del tema del momento; public/js/wd-arranque.js la
enseña solo en la portada de la web (no en la app ni en otras direcciones) y la web dibuja después la misma cabecera
encima. Lo que se ve en el navegador (que no se mueve nada y que no sale en otras pantallas) lo prueba
tests/navegador/e2e_v50_57_portada.py."""
import io
import re
import unittest
from pathlib import Path

from helpers import ServerTestCase

ROOT = Path(__file__).resolve().parents[1]


def js():
    return (ROOT / 'public' / 'js' / 'world-dives-v8.js').read_text(encoding='utf-8')


def pre(body: bytes) -> str:
    html = body.decode('utf-8')
    m = re.search(r'<main id="app" tabindex="-1">(<section class="wd-pre".*?</section>)</main>', html, re.S)
    return m.group(1) if m else ''


class CabeceraEnLaPagina(ServerTestCase):

    def test_1_la_portada_trae_su_cabecera_con_la_foto_en_sus_tamanos(self):
        r = self.client().get('/')
        self.assertEqual(r.status, 200)
        p = pre(r.body)
        self.assertIn('lang="es"', p)
        self.assertIn('aria-hidden="true"', p)                                 # a picture of the header, not a second page
        self.assertIn('srcset="/img/titular/buceador-rayos-640.webp 640w, /img/titular/buceador-rayos-960.webp 960w, '
                      '/img/titular/buceador-rayos-1440.webp 1440w, /img/titular/buceador-rayos.webp 1916w"', p)
        self.assertIn('<img src="/img/titular/buceador-rayos.jpg" class="tp-hero-img" alt="" fetchpriority="high" style="object-position:78% 66%">', p)
        self.assertNotRegex(p, r'<(?:a|button)[^>]*\bhref=|<button')               # nothing to press before the web is ready
        self.assertIn('disabled tabindex="-1"', p)
        self.assertEqual(self.client().get('/index.html').body.count(b'class="wd-pre"'), 1)

    def test_2_los_mismos_textos_que_la_web(self):
        src = js()
        tpl = src[src.index('function homeTemplate(){'):src.index('<section class="hm-section hm-mapband"')]
        p = pre(self.client().get('/').body)
        for text in ('WORLDIVES DISCOVERY', 'Encuentra tu próxima inmersión',
                     'Puntos de buceo de todo el mundo, centros que reservan al momento y viajes organizados. Busca un lugar o empieza por el mapa.',
                     'Punto, centro, isla o ciudad', 'Buscar', 'Cerca de mí', 'Pecios', 'Cuevas', 'Arrecifes', 'Centros con reserva online'):
            self.assertIn(text, tpl, text)
            self.assertIn(text, p, text)
        for cls in ('tp-hero hm-hero', 'tp-hero-in', 'eyebrow', 'lead', 'hm-search', 'searchbar', 'search-input-wrap', 'btn btn-primary', 'hm-quick', 'tp-hero-stats'):
            self.assertIn(f'class="{cls}"', tpl, cls)
            self.assertIn(f'class="{cls}"', p, cls)
        # the focus point of each owner's photo, the same in the web and in the page
        web = dict(re.findall(r"'([a-z-]+)':\{alt:'[^']+',focus:'([^']+)'\}", src))
        py = (ROOT / 'app' / 'server.py').read_text(encoding='utf-8')
        page = dict(re.findall(r"'([a-z-]+)': '(\d+% \d+%)'", re.search(r'TITULAR_FOCUS = \{(.*?)\}', py, re.S).group(1)))
        self.assertEqual(page, web)
        self.assertEqual(len(web), 5)

    def test_3_en_el_idioma_con_el_que_empieza_la_pagina(self):
        p = pre(self.client().get('/', headers={'Accept-Language': 'en-GB,en;q=0.9'}).body)
        self.assertIn('lang="en"', p)
        self.assertIn('Find your next dive', p)
        self.assertNotIn('Encuentra tu próxima inmersión', p)
        p = pre(self.client().get('/?lang=de').body)
        self.assertIn('lang="de"', p)
        self.assertNotIn('Encuentra tu próxima inmersión', p)

    def test_4_la_foto_y_la_cinta_que_elige_la_administracion(self):
        admin = self.make_admin()
        from PIL import Image
        buf = io.BytesIO(); Image.new('RGB', (1600, 900), (10, 60, 90)).save(buf, 'JPEG')
        r = admin.upload('/api/admin/site-media', {'key': 'hero:home', 'credit': 'Foto: Ana'}, 'portada.jpg', buf.getvalue())
        self.assertEqual(r.status, 200, r.body[:300])
        url = r.json['url']
        r = admin.post('/api/admin/site-themes', {'name': 'Verano', 'mode': 'always', 'ribbon': 'Temporada de verano abierta'})
        self.assertEqual(r.status, 200, r.body[:300])
        p = pre(self.client().get('/').body)
        self.assertIn(f'<img src="{url}" class="tp-hero-img"', p)
        self.assertIn('<span class="hero-credit">Foto: Ana</span>', p)
        self.assertIn('class="hm-ribbon"', p)
        self.assertIn('Temporada de verano abierta', p)

    def test_5_el_aviso_de_arranque_y_la_politica_de_seguridad(self):
        html = self.client().get('/').body.decode('utf-8')
        head = html[:html.index('</head>')]
        # the boot script goes first (it runs without waiting for the CSS) and names the main script: there is no other tag
        # for it, so its download no longer competes with the photo of the header on the home page
        self.assertRegex(head, r'<script src="/js/wd-arranque\.js\?v=([0-9.]+)" data-main="/js/world-dives-v8\.js\?v=\1"></script>')
        self.assertLess(head.index('wd-arranque.js'), head.index('world-dives-v8.css'))
        self.assertNotIn('<script src="/js/world-dives-v8.js', html)
        self.assertIsNone(re.search(r'<script(?![^>]*\bsrc=)', html))                    # no script written in the page
        r = self.client().get('/js/wd-arranque.js')
        self.assertEqual(r.status, 200)
        self.assertIn('javascript', r.headers.get('Content-Type', ''))
        self.assertLess(len(r.body), 4000)
        csp = r.headers.get('Content-Security-Policy') or self.client().get('/').headers.get('Content-Security-Policy', '')
        self.assertIn("script-src 'self'", csp)
        self.assertNotIn('unsafe-inline', csp.split('script-src', 1)[1].split(';', 1)[0])
        src = r.body.decode('utf-8')
        for rule in ('WorldivesApp', "'wd-app'", "'wod-language'", 'navigator.languages', "route==='home'"):
            self.assertIn(rule, src)                                                    # only on the home page of the web

    def test_6_el_programa_principal_despues_de_la_cabecera(self):
        """5.4 · On the home page the main script (355 KB) and the language pack start once the browser says the photo of
        the header is painted (largest-contentful-paint), at «load» without that notice, at the latest after 3 s; on any
        other page they start right away and the main script runs when the page is ready, as before. The browser test
        (e2e_v50_57_portada.py) measures the order of the downloads."""
        boot = (ROOT / 'public' / 'js' / 'wd-arranque.js').read_text(encoding='utf-8')
        for rule in ("getAttribute('data-main')", "observe({type:'largest-contentful-paint',buffered:true})", 'catch(e){ go(); }',
                     'setTimeout(go,3000)', "pack(); preload(main,'script'); ready(run);", 's.async=false', 'window.__wdMain=new Promise'):
            self.assertIn(rule, boot)
        src = js()
        self.assertIn("if(document.readyState==='loading') window.addEventListener('DOMContentLoaded',wdBoot); else wdBoot();", src)
        sw = (ROOT / 'public' / 'js' / 'sw-register.js').read_text(encoding='utf-8')
        self.assertIn('Promise.resolve(window.__wdMain).then(', sw)                  # the worker copies the web afterwards
        # the map of the home page: when it is on the screen, when the visitor scrolls or when a search shows it
        home = src[src.index('async function renderHome(){'):src.index('// ---------------------------------------------------------------- Explorar')]
        for rule in ('new IntersectionObserver(', "addEventListener('scroll',go,{passive:true})", 'state.homeMap=startMap', 'const layerP=loadMapLayer();'):
            self.assertIn(rule, home)
        self.assertIn('Promise.resolve(state.homeMap?.()).then(()=>setTimeout(()=>{', src)


if __name__ == '__main__':
    unittest.main()
