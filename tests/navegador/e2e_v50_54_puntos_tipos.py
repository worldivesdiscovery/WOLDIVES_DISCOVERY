#!/usr/bin/env python3
"""v50.54 · puntos 2, 3 y 4 del encargo del 14/10/2026, en un navegador real (Chromium) sobre la demo:

Puntos de buceo
- cabecera compacta y barra fija al bajar (v50.57, revisión general 3.3: buscador, «Filtros», orden y Lista/Mapa en una
  sola línea; tipo, nivel y profundidad en el panel de «Filtros»);
- regiones con su número (ninguna vacía), tipo, nivel y profundidad con su número; la dirección guarda los filtros;
- rejilla de 3–4 columnas en el ordenador y lista de 1 en el móvil; tarjeta sin «Por confirmar» ni «Por asociar»;
- «Ver más» y carga al bajar; Lista/Mapa en la misma página (el mapa enseña todos los puntos filtrados);
- al volver de una ficha: mismos filtros, mismas páginas y la misma posición.
Ficha del punto
- datos clave en el orden fijo y solo los que existen; secciones en el orden: descripción, vida marina, recorrido
  virtual, centros, mapa; la misma estructura en todos los puntos.
Tipos de buceo
- elegir un tipo no recarga ni sube arriba (desplazamiento suave a los resultados) y cambia la dirección;
  «Atrás» vuelve al estado anterior; tipos sin puntos desactivados; un tipo vacío da sugerencias.

    python3 tests/navegador/e2e_v50_54_puntos_tipos.py [carpeta-de-capturas]
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
KEY_ORDER = ['Profundidad', 'Nivel', 'Titulación recomendada', 'Tipo', 'Mejor época', 'Temperatura del agua', 'Visibilidad']


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='wod-e2e-5054-'))
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='wod-demo-')) / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(tmp)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=tmp).start()
    rows, problems = [], []

    def check(what, ok, detail=''):
        rows.append((what, bool(ok), detail))
        if not ok: problems.append(f'{what}: {detail}')

    try:
        with sync_playwright() as pw:
            browser = chromium(pw)
            errors = []

            def page(w=1366, h=900):
                ctx = browser.new_context(viewport={'width': w, 'height': h}, locale='es-ES')
                pg = ctx.new_page()
                pg.on('pageerror', lambda e: errors.append(str(e)))
                pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' and 'ERR_TUNNEL' not in m.text and 'ERR_PROXY' not in m.text else None)
                pg.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                return ctx, pg

            def cards(pg):
                return pg.evaluate("document.querySelectorAll('#pt-grid .pt-card:not(.is-skeleton)').length")

            # ---------------------------------------------------------------- Puntos de buceo (ordenador)
            ctx, pg = page()
            pg.goto(srv.base + '/#/puntos'); pg.wait_for_selector('#pt-grid .pt-card:not(.is-skeleton)')
            pg.evaluate('window.__same=1')
            band = pg.evaluate("(()=>{const b=document.querySelector('.pt-bar').getBoundingClientRect();return {h:b.height,q:!!document.querySelector('.pt-bar #pt-q'),f:!!document.querySelector('.pt-bar #pt-filters-btn'),s:!!document.querySelector('.pt-bar #pt-sort'),v:document.querySelectorAll('.pt-bar .pt-view button').length}})()")
            check('Puntos: buscador, «Filtros», orden y Lista/Mapa en una línea', band['q'] and band['f'] and band['s'] and band['v'] == 2 and band['h'] < 70, band)
            cols = pg.evaluate("new Set([...document.querySelectorAll('#pt-grid .pt-card')].slice(0,8).map(c=>Math.round(c.getBoundingClientRect().left))).size")
            check('Puntos: 3–4 columnas en el ordenador', cols in (3, 4), cols)
            text = pg.inner_text('#pt-grid')
            check('Puntos: sin «Por confirmar» ni «Por asociar»', 'Por confirmar' not in text and 'Por asociar' not in text)
            pills = pg.evaluate("[...document.querySelectorAll('#pt-regions [data-area]')].map(b=>({a:b.dataset.area,n:+(b.querySelector('.pt-n')?.textContent||'0').replace(/\\D/g,'')}))")
            check('Puntos: regiones con su número y ninguna vacía', pills and all(p['n'] > 0 for p in pills), pills[:5])
            pg.screenshot(path=str(out / 'puntos-ordenador.png'))
            # sticky filters
            pg.mouse.wheel(0, 1800); pg.wait_for_timeout(500)
            top = pg.evaluate("[document.querySelector('#pt-filters').getBoundingClientRect().top, document.querySelector('.site-header').getBoundingClientRect().height]")
            check('Puntos: la barra de filtros se queda fija al bajar', abs(top[0] - top[1]) <= 2, top)
            pg.evaluate('window.scrollTo(0,0)')
            # a region
            reg = next(p for p in pills if p['a'] and p['n'] >= 13)
            pg.click(f"#pt-regions [data-area=\"{reg['a']}\"]"); pg.wait_for_timeout(900)
            total = pg.evaluate("+(document.querySelector('#pt-count strong')?.textContent||'0').replace(/\\D/g,'')")
            check(f"Puntos: la región «{reg['a']}» da sus {reg['n']} puntos", total == reg['n'] and 'area=' in pg.evaluate('location.hash'), (total, pg.evaluate('location.hash')))
            # depth and type selects carry counts; a choice goes to the address
            opts = pg.evaluate("[...document.querySelectorAll('#pt-depth option')].map(o=>[o.value,o.textContent,o.disabled])")
            check('Puntos: profundidad con su número', all('(' in o[1] for o in opts if o[0]), opts)
            first = next((o[0] for o in opts if o[0] and not o[2]), '')
            if first:
                pg.click('#pt-filters-btn'); pg.select_option('#pt-depth', first); pg.wait_for_timeout(900); pg.keyboard.press('Escape')
                check('Puntos: el filtro de profundidad va a la dirección', f'depth={first}' in pg.evaluate('location.hash'), pg.evaluate('location.hash'))
            pg.click('#pt-clear'); pg.wait_for_timeout(900)
            # Ver más and loading by itself
            n0 = cards(pg); pg.click('#pt-more'); pg.wait_for_timeout(900); n1 = cards(pg)
            check('Puntos: «Ver más» añade 12', n1 == n0 + 12, (n0, n1))
            pg.evaluate("document.querySelector('#pt-more').scrollIntoView()"); pg.wait_for_timeout(1500); n2 = cards(pg)
            check('Puntos: carga sola al bajar', n2 > n1, (n1, n2))
            # back from a dive site: same filters, pages and position
            pg.click('#pt-regions [data-area=""]'); pg.wait_for_timeout(300)
            pg.click('#pt-filters-btn'); pg.select_option('#pt-level', 'mid'); pg.wait_for_timeout(900); pg.keyboard.press('Escape')
            pg.click('#pt-more'); pg.wait_for_timeout(900)
            target = pg.locator('#pt-grid .pt-card').nth(17)
            target.scroll_into_view_if_needed(); pg.wait_for_timeout(300)
            y = pg.evaluate('window.scrollY'); url = pg.evaluate('location.hash'); before = cards(pg)
            target.locator('a').click(); pg.wait_for_selector('.pp-keys, .pp54'); pg.wait_for_timeout(500)
            pg.go_back(); pg.wait_for_selector('#pt-grid .pt-card:not(.is-skeleton)'); pg.wait_for_timeout(900)
            after = (pg.evaluate('location.hash'), cards(pg), pg.evaluate('window.scrollY'), pg.evaluate("document.querySelector('#pt-level').value"))
            check('Puntos: al volver de la ficha, mismos filtros, páginas y posición', after[0] == url and after[1] >= before and abs(after[2] - y) < 60 and after[3] == 'mid', {'antes': (url, before, y), 'después': after})
            # Lista / Mapa
            pg.click('.pt-view [data-view="map"]'); pg.wait_for_timeout(1500)
            m = pg.evaluate("({map:!document.querySelector('#pt-mapview').hidden,grid:document.querySelector('#pt-grid').hidden,pins:document.querySelectorAll('#pt-map .pt-pin-wrap').length,total:+(document.querySelector('#pt-count strong')?.textContent||'0').replace(/\\D/g,''),url:location.hash})")
            check('Puntos: Mapa en la misma página con todos los puntos filtrados', m['map'] and m['grid'] and m['pins'] == m['total'] and 'view=map' in m['url'], m)
            pg.screenshot(path=str(out / 'puntos-mapa-ordenador.png'))
            pg.click('.pt-view [data-view="list"]'); pg.wait_for_timeout(900)
            check('Puntos: vuelta a la lista', cards(pg) > 0 and pg.evaluate("document.querySelector('#pt-mapview').hidden"))
            check('Puntos: sin recargar la página', pg.evaluate('window.__same') == 1)
            ctx.close()

            # ---------------------------------------------------------------- Puntos (móvil)
            ctx, pg = page(390, 844)
            pg.goto(srv.base + '/#/puntos'); pg.wait_for_selector('#pt-grid .pt-card:not(.is-skeleton)'); pg.wait_for_timeout(400)
            cols = pg.evaluate("new Set([...document.querySelectorAll('#pt-grid .pt-card')].slice(0,4).map(c=>Math.round(c.getBoundingClientRect().left))).size")
            first_card = pg.evaluate("document.querySelector('#pt-grid .pt-card').getBoundingClientRect().top")
            check('Puntos móvil: una columna y la primera tarjeta en la primera pantalla', cols == 1 and first_card < 844, (cols, first_card))
            check('Puntos móvil: sin desplazamiento horizontal', pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
            pg.screenshot(path=str(out / 'puntos-movil.png'))
            ctx.close()

            # ---------------------------------------------------------------- Ficha del punto: orden fijo
            ctx, pg = page()
            pg.goto(srv.base + '/#/puntos?q=Cabo'); pg.wait_for_selector('#pt-grid .pt-card:not(.is-skeleton)')
            ids = pg.evaluate("[...document.querySelectorAll('#pt-grid .pt-card')].slice(0,4).map(c=>c.id.replace('pt-card-',''))")
            structures = []
            for i, pid in enumerate(ids):
                pg.goto(f'{srv.base}/#/punto?id={pid}'); pg.wait_for_selector('.pp54'); pg.wait_for_timeout(500)
                info = pg.evaluate("""(()=>{const keys=[...document.querySelectorAll('.pp-keys dt')].map(x=>x.textContent.trim());
                  const order=['#pp-about','.pm-block','.pp-virtual-block','#pp-centers','#pp-where'].map(s=>{const e=document.querySelector(s);return e?[s,[...document.querySelectorAll('.pp-body > *')].indexOf(e)]:null}).filter(Boolean);
                  return {keys,order,text:document.querySelector('.pp54').innerText}})()""")
                idx = [KEY_ORDER.index(k) for k in info['keys'] if k in KEY_ORDER]
                check(f'Ficha {pid}: datos clave en el orden fijo', idx == sorted(idx) and len(idx) == len(info['keys']) and len(idx) >= 2, info['keys'])
                check(f'Ficha {pid}: nunca «Por confirmar»', 'Por confirmar' not in info['text'])
                pos = [p[1] for p in info['order']]
                check(f'Ficha {pid}: descripción, vida marina, recorrido, centros y mapa en ese orden', pos == sorted(pos) and info['order'][0][0] == '#pp-about' and info['order'][-1][0] == '#pp-where', info['order'])
                structures.append(tuple(p[0] for p in info['order']))
                if i == 0:
                    pg.screenshot(path=str(out / 'ficha-ordenador.png'))
            ctx.close()

            # ---------------------------------------------------------------- Tipos de buceo
            ctx, pg = page()
            pg.goto(srv.base + '/#/tipos'); pg.wait_for_selector('#tp-grid .tp-card')
            pg.evaluate('window.__same=1')
            empty = pg.evaluate("[...document.querySelectorAll('#tp-grid .tp-card.is-empty')].map(c=>[c.tagName,c.getAttribute('aria-disabled')])")
            check('Tipos: los tipos sin puntos están desactivados (no son enlaces)', all(e == ['SPAN', 'true'] for e in empty), empty)
            counts = pg.evaluate("[...document.querySelectorAll('#tp-grid a.tp-card .tp-card-meta')].every(m=>/\\d+ punto/.test(m.textContent))")
            check('Tipos: cada tipo dice cuántos puntos tiene', counts)
            pg.locator('#tp-grid').scroll_into_view_if_needed(); pg.mouse.wheel(0, 300); pg.wait_for_timeout(300)
            y0 = pg.evaluate('window.scrollY')
            pg.click('#tp-grid a.tp-card[data-key="pecios-y-naufragios"]'); pg.wait_for_selector('#tp-results .pt-card:not(.is-skeleton)'); pg.wait_for_timeout(1200)
            st = pg.evaluate("({hash:location.hash,y:scrollY,same:window.__same,top:document.querySelector('#tp-results').getBoundingClientRect().top,cards:document.querySelectorAll('#tp-results .pt-card').length})")
            check('Tipos: elegir no recarga ni sube arriba; baja hasta los resultados', st['same'] == 1 and st['y'] > y0 and 0 <= st['top'] < 200 and st['cards'] > 0, st)
            check('Tipos: la dirección cambia (#/tipos?t=…)', st['hash'] == '#/tipos?t=pecios-y-naufragios', st['hash'])
            pg.screenshot(path=str(out / 'tipos-resultados-ordenador.png'))
            pg.click('#tp-grid a.tp-card[data-key="paredes"]'); pg.wait_for_timeout(1500)
            pg.go_back(); pg.wait_for_timeout(1500)
            back = pg.evaluate("({hash:location.hash,same:window.__same,h:document.querySelector('#tp-results h2')?.textContent})")
            check('Tipos: «Atrás» vuelve al tipo anterior sin recargar', back['hash'] == '#/tipos?t=pecios-y-naufragios' and back['same'] == 1 and 'Pecios' in (back['h'] or ''), back)
            pg.go_back(); pg.wait_for_timeout(1000)
            check('Tipos: «Atrás» hasta la lista sin resultados', pg.evaluate("location.hash==='#/tipos'&&document.querySelector('#tp-results').hidden"))
            ctx.close()
            ctx, pg = page()
            pg.goto(srv.base + '/#/tipos?t=nocturnas'); pg.wait_for_selector('#tp-results .tp-res-empty'); pg.wait_for_timeout(500)
            sug = pg.evaluate("[...document.querySelectorAll('#tp-results .tp-res-empty a.cd-chip')].map(a=>a.textContent.trim())")
            check('Tipos: un tipo sin puntos explica y sugiere otros', len(sug) >= 1 and 'Todavía no hay puntos' in pg.inner_text('#tp-results'), sug)
            pg.screenshot(path=str(out / 'tipos-vacio-ordenador.png'))
            ctx.close()
            browser.close()
            check('Sin errores en la consola', not errors, errors[:4])
    finally:
        srv.stop()
    for what, ok, detail in rows: print(f"{'OK ' if ok else 'MAL'} {what}" + ('' if ok else f'  → {detail}'))
    print(f'Capturas en {out}')
    if problems:
        print(f'PROBLEMAS: {len(problems)}'); sys.exit(1)
    print('OK: listado de puntos, ficha y tipos de buceo como pide el encargo.')


if __name__ == '__main__':
    main()
