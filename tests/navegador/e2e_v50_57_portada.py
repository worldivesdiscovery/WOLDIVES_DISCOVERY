#!/usr/bin/env python3
"""v50.57 · Revisión general 5.4: la cabecera de la portada dibujada en la propia página, en un navegador real.

- Sin el programa principal (bloqueado a propósito), la portada ya enseña su cabecera: la foto cargada y los textos en
  castellano (o en inglés para quien lee en inglés).
- En cualquier otra dirección (#/puntos) y en la app (?app=1) no se enseña, y el pie no sube hasta que la web dibuja.
- Al dibujar la web su cabecera encima, nada se mueve (la misma caja, el mismo título en el mismo sitio).
- Con 4G lento y el procesador 4 veces más lento (como el móvil de Lighthouse): la foto de la cabecera aparece en
  menos de 2,5 s (LCP) y la página no salta (CLS < 0,1).
- En la portada, el programa principal y el paquete de idioma empiezan a bajar cuando la foto ya está pintada (no le
  quitan ancho de banda); en cualquier otra página empiezan al momento, como antes.
- El mapa de la portada no se prepara mientras no se ve (en un móvil queda debajo de la cabecera): sí al bajar, y
  «Buscar» lo prepara y enseña el punto.

    python3 tests/navegador/e2e_v50_57_portada.py [carpeta-de-capturas]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

MAIN_JS = '**/js/world-dives-v8.js*'
STATE = """() => { const p = document.querySelector('#app > .wd-pre'), h = document.querySelector('#app .tp-hero'), img = h && h.querySelector('img.tp-hero-img');
  const foot = document.querySelector('.site-footer').getBoundingClientRect();
  return {pre_shown: !!p && getComputedStyle(p).display !== 'none', web: !!document.querySelector('#home-search'),
          img_loaded: !!img && img.complete && img.naturalWidth > 0, img_src: img ? img.currentSrc.split('/').pop() : '',
          text_visible: !!h && getComputedStyle(h.querySelector('.tp-hero-in')).visibility === 'visible', h1: h ? h.querySelector('h1').textContent : '',
          hero: h ? [h.getBoundingClientRect().top, h.getBoundingClientRect().height].map(Math.round) : null,
          h1_box: h ? [h.querySelector('h1').getBoundingClientRect().top, h.querySelector('h1').getBoundingClientRect().left].map(Math.round) : null,
          footer_below: foot.top >= innerHeight - 1}; }"""
VITALS = """() => new Promise(done => { let lcp = 0, cls = 0, el = '';
  new PerformanceObserver(l => { for (const e of l.getEntries()) { lcp = e.startTime; el = e.url || (e.element && e.element.tagName) || ''; } }).observe({type: 'largest-contentful-paint', buffered: true});
  new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) cls += e.value; }).observe({type: 'layout-shift', buffered: true});
  setTimeout(() => done({lcp: Math.round(lcp), cls: Math.round(cls * 1000) / 1000, el: String(el)}), 300); })"""


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if out: out.mkdir(parents=True, exist_ok=True)
    srv = Server({'WOD_DEMO_MODE': '0'}).start()
    rows, errors = [], []

    def check(what, ok, detail=''):
        rows.append((what, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + what + ('' if ok else f'  → {str(detail)[:400]}'), flush=True)

    try:
        with sync_playwright() as pw:
            browser = chromium(pw)

            def page(w=390, h=844, locale='es-ES'):
                ctx = browser.new_context(viewport={'width': w, 'height': h}, locale=locale, device_scale_factor=1.75 if w < 500 else 1)
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg = ctx.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
                return ctx, pg

            # ---------------------------------------------------------------- what the page alone draws
            for w, h in ((390, 844), (1440, 900)):
                ctx, pg = page(w, h)
                pg.route(MAIN_JS, lambda r: r.abort())
                pg.goto(srv.base + '/'); pg.wait_for_timeout(900)
                s = pg.evaluate(STATE)
                check(f'{w}px · sin el programa principal, la portada ya tiene su cabecera con la foto y los textos',
                      s['pre_shown'] and s['img_loaded'] and s['text_visible'] and s['h1'] == 'Encuentra tu próxima inmersión' and s['footer_below'], s)
                if out: pg.screenshot(path=str(out / f'{w}-solo-la-pagina.png'))
                pre = s
                pg.goto(srv.base + '/#/puntos'); pg.reload(); pg.wait_for_timeout(700)
                s = pg.evaluate(STATE)
                check(f'{w}px · en otra dirección no sale y el pie no sube', not s['pre_shown'] and s['footer_below'], s)
                pg.goto(srv.base + '/?app=1#/'); pg.wait_for_timeout(700)
                s = pg.evaluate(STATE)
                check(f'{w}px · en la app no sale', not s['pre_shown'], s)
                pg.unroute(MAIN_JS)
                pg.evaluate("sessionStorage.removeItem('wd-app')")
                pg.goto(srv.base + '/?app=0#/'); pg.wait_for_selector('#home-search'); pg.wait_for_timeout(1500)
                s = pg.evaluate(STATE)
                check(f'{w}px · la web dibuja su cabecera en la misma caja (nada se mueve)', s['web'] and s['hero'] == pre['hero'] and s['h1_box'] == pre['h1_box'] and s['img_src'] == pre['img_src'],
                      {'página': pre, 'web': s})
                ctx.close()

            # ---------------------------------------------------------------- a visitor who reads English
            ctx, pg = page(locale='en-GB')
            pg.route(MAIN_JS, lambda r: r.abort())
            pg.goto(srv.base + '/'); pg.wait_for_timeout(900)
            s = pg.evaluate(STATE)
            check('Inglés · la cabecera de la página viene en inglés', s['pre_shown'] and s['text_visible'] and s['h1'] == 'Find your next dive', s)
            ctx.close()
            ctx, pg = page(locale='en-GB')
            pg.add_init_script("try{localStorage.setItem('wod-language','fr')}catch(e){}")
            pg.route(MAIN_JS, lambda r: r.abort())
            pg.goto(srv.base + '/'); pg.wait_for_timeout(900)
            s = pg.evaluate(STATE)
            check('Quien eligió francés y su navegador dice inglés: la foto sí, los textos esperan a su idioma', s['pre_shown'] and s['img_loaded'] and not s['text_visible'], s)
            ctx.close()

            # ---------------------------------------------------------------- order of the downloads (5.4)
            ORDER = """() => new Promise(done => { let lcp = null;
              new PerformanceObserver(l => { const e = l.getEntries().pop(); if (e) lcp = e.startTime; }).observe({type: 'largest-contentful-paint', buffered: true});
              setTimeout(() => { const r = n => { const e = performance.getEntriesByType('resource').find(x => x.name.includes(n)); return e ? Math.round(e.startTime) : null; };
                done({lcp: lcp == null ? null : Math.round(lcp), main: r('/js/world-dives-v8.js'), pack: r('/idiomas/en.json'), web: !!document.querySelector('#home-search, #pt-search, .pt57')}); }, 2500); })"""
            ctx, pg = page(412, 823, locale='en-GB')
            pg.goto(srv.base + '/'); pg.wait_for_selector('#home-search'); o = pg.evaluate(ORDER)
            check('Portada · el programa principal y el paquete de idioma empiezan después de pintarse la foto',
                  o['web'] and o['lcp'] is not None and o['main'] is not None and o['pack'] is not None and o['main'] >= o['lcp'] and o['pack'] >= o['lcp'], o)
            pg.goto(srv.base + '/?otra=1#/puntos'); pg.wait_for_selector('.pt57, #pt-search', timeout=30000); o = pg.evaluate(ORDER)
            check('Otra página · empiezan al momento (sin esperar a nada)', o['web'] and o['main'] is not None and o['pack'] is not None and o['main'] < 300 and o['pack'] < 300, o)
            ctx.close()
            ctx, pg = page(412, 823)
            pg.goto(srv.base + '/'); pg.wait_for_selector('#home-search'); pg.wait_for_timeout(2500)
            m0 = pg.evaluate("({L: !!window.L, map: !!document.querySelector('#home-map.leaflet-container'), top: Math.round(document.querySelector('#home-map').getBoundingClientRect().top)})")
            pg.mouse.wheel(0, 300); pg.wait_for_timeout(2500)
            m1 = pg.evaluate("({L: !!window.L, markers: document.querySelectorAll('#home-map .leaflet-marker-icon').length})")
            check('Móvil · el mapa de la portada no se prepara mientras no se ve, y sí al bajar',
                  m0['top'] > 823 and not m0['L'] and not m0['map'] and m1['L'] and m1['markers'] > 0, {'al abrir': m0, 'al bajar': m1})
            pg.goto(srv.base + '/?b=2#/'); pg.wait_for_selector('#home-search'); pg.wait_for_timeout(2000)
            pg.fill('#home-search', 'Carall Bernat'); pg.wait_for_timeout(600); pg.click('#home-search-btn'); pg.wait_for_timeout(4000)
            s2 = pg.evaluate("({markers: document.querySelectorAll('#home-map .leaflet-marker-icon').length, drawer: document.querySelector('#home-drawer.open h3')?.textContent || ''})")
            check('Móvil · «Buscar» prepara el mapa y abre la ficha del punto', s2['drawer'] == 'Medes – Carall Bernat' and s2['markers'] >= 1, s2)
            ctx.close()

            # ---------------------------------------------------------------- 4G lento y procesador 4× más lento
            for run in range(2):
                ctx, pg = page()
                cdp = ctx.new_cdp_session(pg)
                cdp.send('Network.enable')
                cdp.send('Network.emulateNetworkConditions', {'offline': False, 'latency': 150, 'downloadThroughput': 1.6 * 1024 * 1024 / 8, 'uploadThroughput': 750 * 1024 / 8})
                cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
                pg.goto(srv.base + '/', wait_until='load', timeout=60000); pg.wait_for_selector('#home-search', timeout=60000); pg.wait_for_timeout(2500)
                v = pg.evaluate(VITALS)
                check(f'4G lento (pasada {run + 1}) · la foto de la cabecera en menos de 2,5 s y sin saltos', v['lcp'] < 2500 and v['cls'] < 0.1 and '/img/titular/buceador-rayos' in v['el'], v)
                if out and run == 0: pg.screenshot(path=str(out / '390-4g-lento.png'))
                ctx.close()
            browser.close()
    finally:
        srv.stop()
    check('sin errores de JavaScript', not errors, errors[:3])
    bad = [n for n, ok in rows if not ok]
    print(f'\n{len(rows) - len(bad)}/{len(rows)} comprobaciones correctas')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
