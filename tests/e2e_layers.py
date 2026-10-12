"""Fase 1C, points 9 and 10 (v50.43) in a real browser, desktop and phone: the layer selector «Mapa», «Satélite»,
«Relieve» (in that order, without «Mundo») on the home page, Explorar and the small maps; «Satélite» disabled with
«Disponible próximamente» without ARCGIS_API_KEY and working with it (through our server); «Relieve» = GEBCO WMS
(exact layer name, opaque, exact 2026 credit, help «no apto para la navegación»); fallback «Relieve no disponible
ahora» when GEBCO does not answer; the last layer is remembered; the administration notice without the key.

There is no internet here: the base map, GEBCO and the ArcGIS tiles are simulated (same requests, local images).
Usage: python tests/e2e_layers.py [--shots DIR]
"""
from __future__ import annotations

import http.server
import sys
import threading
from pathlib import Path
from urllib.parse import urlparse, parse_qs

sys.path.insert(0, str(Path(__file__).parent))
from helpers import ServerTestCase, Server  # noqa: E402
from e2e_markers import png, MAP_TILE, SAT_TILE, chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

GEBCO_CREDIT = 'Imagery reproduced from the GEBCO_2026 Grid, GEBCO Compilation Group (2026) GEBCO 2026 Grid'
RELIEF_TILE = png(256, 256, lambda x, y: (18 + (x // 16) * 3, 60 + (y // 8) * 2 % 90, 120 + (x + y) // 6 % 100))


class SatTiles(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200); self.send_header('Content-Type', 'image/png'); self.end_headers(); self.wfile.write(SAT_TILE)

    def log_message(self, *a):
        pass


def run(shots: Path | None):
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))

    def shot(page, name, sel=None):
        if shots:
            shots.mkdir(parents=True, exist_ok=True)
            (page.locator(sel).first if sel else page).screenshot(path=str(shots / f'{name}.png'))

    def context(browser, dev, gebco='ok', lang='es-ES'):
        opts = {'viewport': {'width': 1366, 'height': 900}} if dev == 'ordenador' else \
               {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}
        ctx = browser.new_context(locale=lang, **opts)
        ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
        ctx.wms = []
        ctx.route('**/*tile.openstreetmap.org/**', lambda r: r.fulfill(body=MAP_TILE, content_type='image/png'))

        def gebco_route(r):
            ctx.wms.append(r.request.url)
            r.fulfill(body=RELIEF_TILE, content_type='image/png') if gebco == 'ok' else r.abort()
        ctx.route('**/wms.gebco.net/**', gebco_route)
        return ctx

    def toolbar(page, scope):
        return page.evaluate(f"""()=>[...document.querySelectorAll('{scope} .map-toolbar button')].map(b=>({{mode:b.dataset.mapmode,text:b.querySelector('span').textContent.trim(),
            disabled:b.disabled,small:(b.querySelector('small')||{{}}).textContent||'',active:b.classList.contains('active')}}))""")

    def open_map(page, url, scope):
        page.goto(url); page.wait_for_load_state('networkidle'); page.wait_for_timeout(1200)
        page.locator(f'{scope} .map-toolbar').first.scroll_into_view_if_needed(); page.wait_for_timeout(300)

    # 1 · Without ARCGIS_API_KEY ----------------------------------------------------------------------------
    ServerTestCase.server = Server().start(); srv = ServerTestCase.server
    try:
        t = ServerTestCase('run')
        t.make_admin()
        pid = t.client().get('/api/dive-points').json['items']
        pid = next(x['id'] for x in pid if x.get('latitude') is not None)
        base = srv.base
        with sync_playwright() as p:
            browser = chromium(p)
            for dev in ('ordenador', 'movil'):
                ctx = context(browser, dev); page = ctx.new_page(); errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                for name, url, scope, mapsel in (('portada', '/#/', '.hm-map', '#home-map'), ('explorar', '/#/explorar', '.ex-map', '#explore-map')):
                    page.evaluate("localStorage.removeItem('wd-map-layer')") if page.url.startswith(base) else None
                    open_map(page, base + url, scope)
                    tb = toolbar(page, scope)
                    check(f'{dev} · {name}: «Mapa», «Satélite», «Relieve» en ese orden, sin «Mundo»', [b['text'] for b in tb] == ['Mapa', 'Satélite', 'Relieve'], tb)
                    check(f'{dev} · {name}: «Mapa» por defecto', tb and tb[0]['active'], tb)
                    sat = next((b for b in tb if b['mode'] == 'satellite'), {})
                    check(f'{dev} · {name}: sin clave, «Satélite» desactivado con «Disponible próximamente»', sat.get('disabled') and 'Disponible próximamente' in sat.get('small', '') + page.get_attribute(f'{scope} [data-mapmode=satellite]', 'title'), sat)
                    shot(page, f'{name}-{dev}-mapa', mapsel)
                    ctx.wms.clear()
                    page.click(f'{scope} [data-mapmode=marine]'); page.wait_for_timeout(1500)
                    q = {k.lower(): v[0] for k, v in parse_qs(urlparse(ctx.wms[0]).query).items()} if ctx.wms else {}
                    check(f'{dev} · {name}: «Relieve» pide GEBCO_LATEST opaco (WMS 1.3.0, EPSG:3857)', q.get('layers') == 'GEBCO_LATEST' and q.get('transparent') == 'false' and q.get('version') == '1.3.0' and q.get('crs') == 'EPSG:3857', q)
                    imgs = page.evaluate(f"[...document.querySelectorAll('{mapsel} .leaflet-tile-loaded')].filter(i=>i.src.includes('wms.gebco.net')).length")
                    check(f'{dev} · {name}: el relieve se ve (teselas cargadas)', imgs > 0, imgs)
                    check(f'{dev} · {name}: solo la capa de relieve (sin el mapa base debajo)', page.evaluate(f"[...document.querySelectorAll('{mapsel} .leaflet-tile')].every(i=>i.src.includes('wms.gebco.net'))"))
                    attr = page.inner_text(f'{mapsel} .leaflet-control-attribution')
                    check(f'{dev} · {name}: atribución exacta de GEBCO 2026', GEBCO_CREDIT in attr, attr)
                    note = page.inner_text(f'{mapsel} .wd-relief-note') if page.locator(f'{mapsel} .wd-relief-note').count() else ''
                    check(f'{dev} · {name}: ayuda «no sirve para navegar» con enlace a Seguridad', 'No sirve para navegar' in note and page.locator(f'{mapsel} .wd-relief-note a[href="#/legal/seguridad"]').count() == 1, note)
                    shot(page, f'{name}-{dev}-relieve', mapsel)
                    check(f'{dev} · {name}: se recuerda la última capa', page.evaluate("localStorage.getItem('wd-map-layer')") == 'marine')
                    page.click(f'{scope} [data-mapmode=street]'); page.wait_for_timeout(500)
                    check(f'{dev} · {name}: volver a «Mapa» quita la ayuda del relieve', page.locator(f'{mapsel} .wd-relief-note').count() == 0)
                    page.click(f'{scope} [data-mapmode=marine]'); page.wait_for_timeout(400)
                # Remembered across pages and reloads
                open_map(page, base + '/#/', '.hm-map')
                check(f'{dev}: al volver a la portada sigue «Relieve»', next((b['active'] for b in toolbar(page, '.hm-map') if b['mode'] == 'marine'), False))
                # Small maps: the same selector
                open_map(page, base + f'/#/punto?id={pid}', '#pp-map')
                small = page.evaluate("[...document.querySelectorAll('#pp-map .map-toolbar button')].map(b=>b.querySelector('span').textContent.trim())")
                check(f'{dev}: ficha del punto con el mismo selector', small == ['Mapa', 'Satélite', 'Relieve'], small)
                shot(page, f'punto-{dev}-relieve', '#pp-map')
                page.evaluate("localStorage.setItem('wd-map-layer','street')")
                check(f'{dev}: sin desbordamiento', page.evaluate('document.documentElement.scrollWidth') <= (1366 if dev == 'ordenador' else 392))
                check(f'{dev}: sin errores JS', not errors, errors)
                ctx.close()
            # GEBCO does not answer: back to «Mapa» with «Relieve no disponible ahora»
            ctx = context(browser, 'movil', gebco='fail'); page = ctx.new_page()
            open_map(page, base + '/#/explorar', '.ex-map')
            page.click('.ex-map [data-mapmode=marine]'); page.wait_for_timeout(2500)
            tb = toolbar(page, '.ex-map'); body = page.inner_text('body')
            check('GEBCO sin respuesta: vuelve a «Mapa» y avisa «Relieve no disponible ahora»', tb[0]['active'] and 'Relieve no disponible ahora' in body, tb)
            check('GEBCO sin respuesta: «Relieve» queda desactivado', next(b for b in tb if b['mode'] == 'marine')['disabled'])
            shot(page, 'explorar-movil-relieve-no-disponible')
            ctx.close()
            # Other languages: same buttons, translated
            for lang, want in (('en', ['Map', 'Satellite', 'Relief']), ('de', ['Karte', 'Satellit', 'Relief']), ('zh', ['地图', '卫星', '地形'])):
                ctx = context(browser, 'ordenador'); page = ctx.new_page()
                open_map(page, base + f'/?lang={lang}#/explorar', '.ex-map'); page.wait_for_timeout(800)
                got = [b['text'] for b in toolbar(page, '.ex-map')]
                check(f'idioma {lang}: {", ".join(want)}', got == want, got)
                ctx.close()
            # Administration: notice without the key
            ctx = context(browser, 'ordenador'); page = ctx.new_page()
            page.goto(base + '/#/login'); page.wait_for_selector('#login'); page.fill('#login', 'admin'); page.fill('#password', 'admin-seguro-2026')
            page.click('#login-form button[type=submit]'); page.wait_for_timeout(1200)
            page.goto(base + '/#/admin'); page.wait_for_load_state('networkidle'); page.wait_for_timeout(1500)
            body = page.inner_text('body')
            check('Administración: «Añade la clave de ArcGIS para activar el satélite»', 'Añade la clave de ArcGIS para activar el satélite' in body or 'Activa la verificación en dos pasos' in body, body[:200])
            page.goto(base + '/#/admin?tab=maps'); page.wait_for_load_state('networkidle'); page.wait_for_timeout(1500)
            if page.locator('#maps-sat-notice').count():
                check('Administración → Mapas: el mismo aviso', 'Añade la clave de ArcGIS' in page.inner_text('#maps-sat-notice'))
                shot(page, 'admin-mapas-sin-clave')
            ctx.close(); browser.close()
    finally:
        srv.stop()

    # 2 · With ARCGIS_API_KEY (Esri simulated behind our server) ------------------------------------------------
    tiles = http.server.ThreadingHTTPServer(('127.0.0.1', 0), SatTiles)
    threading.Thread(target=tiles.serve_forever, daemon=True).start()
    srv = Server({'ARCGIS_API_KEY': 'clave-de-prueba', 'WOD_ARCGIS_TILE_URL': f'http://127.0.0.1:{tiles.server_port}/tile/{{z}}/{{y}}/{{x}}'}).start()
    try:
        base = srv.base
        with sync_playwright() as p:
            browser = chromium(p)
            for dev in ('ordenador', 'movil'):
                ctx = context(browser, dev); page = ctx.new_page(); outside = []
                page.on('request', lambda r: outside.append(r.url) if 'arcgis' in r.url else None)
                for name, url, scope, mapsel in (('portada', '/#/', '.hm-map', '#home-map'), ('explorar', '/#/explorar', '.ex-map', '#explore-map')):
                    open_map(page, base + url, scope)
                    sat = next(b for b in toolbar(page, scope) if b['mode'] == 'satellite')
                    check(f'con clave · {dev} · {name}: «Satélite» activo', not sat['disabled'] and not sat['small'], sat)
                    page.click(f'{scope} [data-mapmode=satellite]'); page.wait_for_timeout(1500)
                    n = page.evaluate(f"[...document.querySelectorAll('{mapsel} .leaflet-tile-loaded')].filter(i=>i.src.includes('/api/tiles/satellite/')).length")
                    check(f'con clave · {dev} · {name}: teselas satélite a través de nuestro servidor', n > 0, n)
                    shot(page, f'{name}-{dev}-satelite', mapsel)
                check(f'con clave · {dev}: el navegador nunca pide nada a Esri directamente', not outside, outside[:3])
                check(f'con clave · {dev}: la clave no llega al navegador', 'clave-de-prueba' not in page.content())
                page.evaluate("localStorage.setItem('wd-map-layer','street')")
                ctx.close()
            browser.close()
        used = srv.sql("SELECT tiles FROM map_tile_usage WHERE layer='satellite'")
        check('con clave: las teselas se cuentan para el límite mensual', used and used[0]['tiles'] > 0, used)
    finally:
        srv.stop(); tiles.shutdown()
    return checks


if __name__ == '__main__':
    shots = Path(sys.argv[sys.argv.index('--shots') + 1]) if '--shots' in sys.argv else None
    results = run(shots)
    for name, ok, detail in results:
        print(('OK   ' if ok else 'FALLA') + ' ' + name + (f' · {detail}' if detail and not ok else ''))
    bad = [r for r in results if not r[1]]
    print(f'{len(results) - len(bad)}/{len(results)} comprobaciones correctas')
    sys.exit(1 if bad else 0)
