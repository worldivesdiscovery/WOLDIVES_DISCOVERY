#!/usr/bin/env python3
"""v50.57 · Revisión general 2.2: el mapa del buceo (#/explorar), elemento a elemento, en un navegador real (Chromium).

El recorrido automático de botones (tests/navegador/inventario_botones.py) dejó 16 elementos de esta pantalla como
«No probado»: grupos de puntos («2», «3»), algún punto suelto y el enlace «Seguridad en el buceo» de la nota de
«Relieve». Con tres navegadores a la vez, la animación del mapa pasó de 10 s o el mapa ya se había movido por una
prueba anterior; los mismos elementos sí se probaron bien con otras cuentas. Aquí se prueban uno a uno, cada uno con
la pantalla recién abierta:
- cada grupo de puntos a la vista: al pulsarlo, el mapa se acerca y el grupo se abre en puntos o grupos más pequeños;
- cada punto suelto a la vista: abre su ficha lateral con su nombre y «×» la cierra; «Ver ficha del punto» lleva a la
  ficha de ese punto;
- «Relieve»: sale la nota «No sirve para navegar…» y su enlace «Seguridad en el buceo» abre esa página.
El mapa es el mismo para todos (visitante, buceador, centro, freelance y administración): se prueba sin sesión. Las
imágenes del relieve (GEBCO, fuera de la web) se sustituyen por una imagen vacía: aquí se prueba la web, no GEBCO.

    python3 tests/navegador/e2e_v50_57_explorar.py
"""
from __future__ import annotations

import base64
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PNG = base64.b64decode('iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==')
# What is on the map and can be pressed: clusters and single dive sites inside the map, not covered by anything.
VISIBLE = """sel => { const box = document.querySelector('#explore-map').getBoundingClientRect();
  return [...document.querySelectorAll(sel)].map((el, i) => { const r = el.getBoundingClientRect(), x = r.left + r.width / 2, y = r.top + r.height / 2;
    const top = document.elementFromPoint(x, y);
    return {i, x, y, text: el.textContent.trim(), name: (el.querySelector('[aria-label]') || el).getAttribute('aria-label') || '',
            ok: r.width > 0 && x > box.left + 4 && x < box.right - 4 && y > box.top + 4 && y < box.bottom - 4 && !!top && el.contains(top)}; }).filter(m => m.ok); }"""
COUNT = "() => document.querySelectorAll('#explore-map .leaflet-marker-icon').length"


def main():
    srv = Server({'WOD_DEMO_MODE': '0'}).start()
    rows, errors = [], []

    def check(what, ok, detail=''):
        rows.append((what, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + what + ('' if ok else f'  → {str(detail)[:400]}'), flush=True)

    try:
        with sync_playwright() as pw:
            browser = chromium(pw)
            ctx = browser.new_context(viewport={'width': 1366, 'height': 900}, locale='es-ES')
            ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()));localStorage.removeItem('wd-map-layer')}catch(e){}")
            ctx.route('https://wms.gebco.net/**', lambda r: r.fulfill(status=200, content_type='image/png', body=PNG))
            pg = ctx.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)[:200]))

            loads = [0]

            def fresh():                                   # a new page load each time (only the # changing is not a new load)
                loads[0] += 1
                pg.goto(f'{srv.base}/?carga={loads[0]}#/explorar')
                for _ in range(120):                       # (wait_for_function evaluates text: the CSP of the web forbids it)
                    if pg.evaluate(COUNT): break
                    pg.wait_for_timeout(250)
                pg.wait_for_timeout(1500)

            # ---------------------------------------------------------------- the clusters
            fresh()
            clusters = pg.evaluate(VISIBLE, '#explore-map .wd-cluster-wrap')
            check('hay grupos de puntos a la vista al abrir el mapa', len(clusters) >= 2, clusters)
            for c in sorted(clusters, key=lambda m: int(m['text'] or 0))[:4]:
                fresh()
                now = [m for m in pg.evaluate(VISIBLE, '#explore-map .wd-cluster-wrap') if m['text'] == c['text'] and abs(m['x'] - c['x']) < 3 and abs(m['y'] - c['y']) < 3]
                if not now:
                    check(f'grupo «{c["text"]}»: vuelve a estar al abrir el mapa', False, c); continue
                before = pg.evaluate(COUNT)
                handle = pg.evaluate_handle("i => document.querySelectorAll('#explore-map .wd-cluster-wrap')[i]", now[0]['i'])
                pg.mouse.click(now[0]['x'], now[0]['y']); pg.wait_for_timeout(2000)
                gone = not pg.evaluate('el => el.isConnected', handle)
                pins = pg.evaluate(VISIBLE, '#explore-map .wd-pin-wrap')
                check(f'grupo «{c["text"]}»: al pulsarlo el mapa se acerca y el grupo se abre', gone and pg.evaluate(COUNT) != before and len(pins) >= 1,
                      {'grupo_quitado': gone, 'marcas_antes': before, 'marcas_después': pg.evaluate(COUNT), 'puntos_a_la_vista': len(pins)})

            # ---------------------------------------------------------------- single dive sites
            fresh()
            sites = pg.evaluate(VISIBLE, '#explore-map .wd-pin-wrap')
            check('hay puntos sueltos a la vista al abrir el mapa', len(sites) >= 2, sites)
            for s in sites[:4]:
                fresh()
                now = [m for m in pg.evaluate(VISIBLE, '#explore-map .wd-pin-wrap') if m['name'] == s['name']]
                if not now:
                    check(f'«{s["name"]}»: vuelve a estar al abrir el mapa', False, s); continue
                pg.mouse.click(now[0]['x'], now[0]['y']); pg.wait_for_timeout(1200)
                drawer = pg.evaluate("(() => { const d = document.querySelector('#explore-drawer'); return {open: d.classList.contains('open'), h3: d.querySelector('h3')?.textContent || ''}; })()")
                check(f'«{s["name"]}»: abre su ficha lateral con su nombre', drawer['open'] and drawer['h3'] == s['name'], drawer)
                pg.click('#explore-drawer .close'); pg.wait_for_timeout(500)
                check(f'«{s["name"]}»: «×» cierra la ficha lateral', not pg.evaluate("document.querySelector('#explore-drawer').classList.contains('open')"))
            if sites:
                fresh()
                m = [x for x in pg.evaluate(VISIBLE, '#explore-map .wd-pin-wrap') if x['name'] == sites[0]['name']][0]
                pg.mouse.click(m['x'], m['y']); pg.wait_for_timeout(1200)
                pg.click('#explore-drawer a.btn-primary'); pg.wait_for_selector('h1', timeout=15000); pg.wait_for_timeout(800)
                h1 = pg.inner_text('h1')
                check(f'«Ver ficha del punto» abre la ficha de «{sites[0]["name"]}»', pg.evaluate('location.hash').startswith('#/punto?id=') and sites[0]['name'] in h1,
                      {'dirección': pg.evaluate('location.hash'), 'h1': h1})

            # ---------------------------------------------------------------- «Relieve» and its safety link
            fresh()
            pg.click('.ex-map [data-mapmode="marine"]'); pg.wait_for_timeout(1200)
            note = pg.locator('.wd-relief-note')
            check('«Relieve»: sale la nota «No sirve para navegar ni para la seguridad en el mar»',
                  note.count() == 1 and note.is_visible() and 'No sirve para navegar' in note.inner_text(), note.count())
            link = pg.locator('.wd-relief-note a[href="#/legal/seguridad"]')
            if link.count(): link.scroll_into_view_if_needed(); pg.wait_for_timeout(300)   # at the foot of the map, below the first screen
            box = link.bounding_box() if link.count() else None
            covered = pg.evaluate("([x, y]) => { const t = document.elementFromPoint(x, y); return !t || !t.closest('.wd-relief-note a'); }",
                                  [box['x'] + box['width'] / 2, box['y'] + box['height'] / 2]) if box else True
            check('«Seguridad en el buceo» se ve al bajar y se puede pulsar (nada lo tapa)', bool(box) and not covered, box)
            if box:
                link.click(); pg.wait_for_selector('.lg-page', timeout=15000); pg.wait_for_timeout(600)
                check('«Seguridad en el buceo» abre esa página', pg.evaluate('location.hash') == '#/legal/seguridad' and 'seguridad' in pg.inner_text('main').lower(),
                      pg.evaluate('location.hash'))
            browser.close()
    finally:
        srv.stop()
    check('sin errores de JavaScript', not errors, errors[:3])
    bad = [n for n, ok in rows if not ok]
    print(f'\n{len(rows) - len(bad)}/{len(rows)} comprobaciones correctas')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
