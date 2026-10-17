#!/usr/bin/env python3
"""v50.57 · Revisión general 3.3: los filtros de «Puntos de buceo», en un navegador real (Chromium) sobre una copia de la
demo, a 360, 390, 768, 1024 y 1440 px.

- Al bajar, una sola línea fija arriba: buscador, «Filtros (n)», orden y Lista/Mapa (nunca más de una línea).
- Las regiones, en una fila que se desliza de lado (no en varias filas); la página no se desplaza de lado.
- «Filtros» abre un panel bajo la barra (en el móvil, una hoja que sube desde abajo); Esc lo cierra y el foco vuelve.
- Los filtros activos, como fichas con ✕ (cada una quita el suyo) y «Borrar todo»; «Filtros (n)» los cuenta.
- Más puntos a la vista: 4 columnas a 1440 px, 3 a 1024 y 768 px; en el móvil, al menos 2 puntos completos en la primera
  pantalla con los filtros puestos.
- Los filtros quedan en la dirección: abrirla en otra pestaña da la misma búsqueda (también la vista de mapa).

    python3 tests/navegador/e2e_v50_57_filtros.py [carpeta-de-capturas]
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
SIZES = ((360, 640), (390, 844), (768, 1024), (1024, 768), (1440, 900))
COLUMNS = {360: 1, 390: 1, 768: 3, 1024: 3, 1440: 4}
# The bar seen from the page: its height, whether its controls are on one line, what it holds and where it is.
BAR = """() => {
  const bar = document.querySelector('#pt-filters'), r = bar.getBoundingClientRect(), hdr = document.querySelector('.site-header').getBoundingClientRect();
  const kids = ['#pt-q', '#pt-filters-btn', '#pt-sort', '.pt-view button:not([hidden])'].flatMap(s => [...bar.querySelectorAll(s)])
    .filter(e => { const b = e.closest('.pt-sortbox') || e; return b.getBoundingClientRect().width > 0 && getComputedStyle(b).display !== 'none'; });
  const mids = kids.map(e => { const b = (e.closest('.pt-sortbox') || e).getBoundingClientRect(); return (b.top + b.bottom) / 2; });
  return {h: Math.round(r.height), top: Math.round(r.top), hdr_bottom: Math.round(hdr.bottom), hdr_sticky: getComputedStyle(document.querySelector('.site-header')).position === 'sticky',
          one_line: mids.length >= 4 && Math.max(...mids) - Math.min(...mids) <= 12, controls: mids.length,
          has: ['#pt-q', '#pt-filters-btn', '#pt-sort', '.pt-view [data-view="list"]', '.pt-view [data-view="map"]'].every(s => bar.querySelector(s))};
}"""
CARDS = """() => {
  const bar = document.querySelector('#pt-filters').getBoundingClientRect(), vh = innerHeight;
  const cards = [...document.querySelectorAll('#pt-grid .pt-card:not(.is-skeleton)')].map(c => c.getBoundingClientRect()).filter(r => r.height > 0);
  return {full: cards.filter(r => r.top >= bar.bottom - 1 && r.bottom <= vh + 1).length,
          cols: new Set(cards.slice(0, 8).map(r => Math.round(r.left))).size};
}"""


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    if out: out.mkdir(parents=True, exist_ok=True)
    db = Path(tempfile.mkdtemp(prefix='wod-demo-')) / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(db)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=db).start()
    rows, errors = [], []

    def check(what, ok, detail=''):
        rows.append((what, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + what + ('' if ok else f'  → {str(detail)[:400]}'), flush=True)

    try:
        with sync_playwright() as pw:
            browser = chromium(pw)

            def page(w, h):
                ctx = browser.new_context(viewport={'width': w, 'height': h}, locale='es-ES')
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg = ctx.new_page()
                pg.on('pageerror', lambda e: errors.append(f'{w}px: {e}'))
                return ctx, pg

            def ready(pg):
                pg.wait_for_selector('#pt-grid .pt-card:not(.is-skeleton)'); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(400)

            def shot(pg, name):
                if out: pg.screenshot(path=str(out / f'{name}.png'))

            for w, h in SIZES:
                phone = w <= 760
                ctx, pg = page(w, h)
                pg.goto(srv.base + '/#/puntos'); ready(pg)
                shot(pg, f'{w}-arriba')
                # ------------------------------------------------------------ one line, fixed at the top when scrolling
                pg.mouse.wheel(0, 1200); pg.wait_for_timeout(600)
                b = pg.evaluate(BAR)
                check(f'{w}px · al bajar, la barra es una sola línea con buscador, «Filtros», orden y Lista/Mapa', b['one_line'] and b['h'] <= 64 and b['has'], b)
                check(f'{w}px · la barra se queda fija arriba', abs(b['top'] - (b['hdr_bottom'] if b['hdr_sticky'] else 0)) <= 2, b)
                c = pg.evaluate(CARDS)
                check(f'{w}px · {COLUMNS[w]} columna(s) de puntos', c['cols'] == COLUMNS[w], c)
                check(f'{w}px · al bajar se ven puntos completos bajo la barra', c['full'] >= (3 if phone else 2), c)
                shot(pg, f'{w}-al-bajar')
                pg.evaluate('window.scrollTo(0,0)'); pg.wait_for_timeout(300)
                # ------------------------------------------------------------ regions in one row, sideways
                z = pg.evaluate("""() => { const row = document.querySelector('#pt-regions'), chips = [...row.querySelectorAll('[data-area]')];
                  return {chips: chips.length, tops: new Set(chips.map(c => Math.round(c.offsetTop))).size, scrolls: row.scrollWidth > row.clientWidth + 4,
                          page: document.documentElement.scrollWidth <= innerWidth + 1}; }""")
                check(f'{w}px · regiones en una sola fila que se desliza de lado, sin desplazar la página', z['chips'] > 10 and z['tops'] == 1 and z['scrolls'] and z['page'], z)
                if not phone:
                    arrows = pg.evaluate("[...document.querySelectorAll('.pt-zarrow')].map(b=>!b.hidden)")
                    pg.click('.pt-zarrow[data-dir="1"]'); pg.wait_for_timeout(700)
                    moved = pg.evaluate("document.querySelector('#pt-regions').scrollLeft")
                    check(f'{w}px · la flecha desliza las regiones', arrows == [False, True] and moved > 50, (arrows, moved))
                # ------------------------------------------------------------ the «Filtros» panel
                pg.click('#pt-filters-btn'); pg.wait_for_timeout(400)
                p = pg.evaluate("""() => { const p = document.querySelector('#pt-panel'), r = p.getBoundingClientRect(), bar = document.querySelector('#pt-filters').getBoundingClientRect();
                  return {open: !p.hidden, sheet: p.classList.contains('is-sheet'), bottom: Math.round(r.bottom), left: Math.round(r.left), right: Math.round(r.right),
                          below: r.top >= bar.bottom - 2, veil: !document.querySelector('#pt-scrim').hidden, focus: p.contains(document.activeElement),
                          expanded: document.querySelector('#pt-filters-btn').getAttribute('aria-expanded')}; }""")
                if phone:
                    check(f'{w}px · «Filtros» abre una hoja desde abajo, sobre un velo', p['open'] and p['sheet'] and abs(p['bottom'] - h) <= 1 and p['left'] == 0 and p['right'] == w and p['veil'] and p['focus'], p)
                else:
                    check(f'{w}px · «Filtros» abre un panel bajo la barra', p['open'] and not p['sheet'] and p['below'] and not p['veil'] and p['focus'] and p['expanded'] == 'true', p)
                shot(pg, f'{w}-panel-filtros')
                pg.select_option('#pt-level', 'start'); pg.wait_for_timeout(900)
                area = pg.evaluate("[...document.querySelectorAll('#pt-area option')].filter(o=>o.value&&!o.disabled).sort((a,b)=>+b.textContent.match(/\\((\\d+)\\)/)[1]-+a.textContent.match(/\\((\\d+)\\)/)[1])[0].value")
                pg.select_option('#pt-area', area); pg.wait_for_timeout(900)
                ok_text = pg.inner_text('#pt-panel-ok')
                pg.keyboard.press('Escape'); pg.wait_for_timeout(300)
                f = pg.evaluate("""() => ({hidden: document.querySelector('#pt-panel').hidden, focus: document.activeElement?.id, lock: document.documentElement.classList.contains('pt-lock'),
                  button: document.querySelector('#pt-filters-btn').innerText.replace(/\\s+/g, ' ').trim(), chips: [...document.querySelectorAll('#pt-active [data-remove]')].map(b => b.dataset.remove),
                  clear: !!document.querySelector('#pt-active #pt-clear'), hash: location.hash, params: Object.fromEntries(new URLSearchParams(location.hash.split('?')[1] || '')), total: +(document.querySelector('#pt-count strong')?.textContent || '0').replace(/\\D/g, '')})""")
                check(f'{w}px · Esc cierra el panel y el foco vuelve a «Filtros»', f['hidden'] and f['focus'] == 'pt-filters-btn' and not f['lock'], f)
                check(f'{w}px · «Filtros (2)», una ficha por filtro y «Borrar todo»', f['button'] == 'Filtros (2)' and sorted(f['chips']) == ['area', 'level'] and f['clear'], f)
                check(f'{w}px · los filtros van a la dirección', f['params'].get('area') == area and f['params'].get('level') == 'start', f['hash'])
                check(f'{w}px · el botón del panel dice cuántos puntos hay', str(f['total']) in ok_text.replace('.', ''), (ok_text, f['total']))
                shot(pg, f'{w}-filtros-activos')
                if phone:
                    c = pg.evaluate(CARDS)
                    check(f'{w}px · con los filtros puestos, al menos 2 puntos completos en la primera pantalla', c['full'] >= 2, c)
                # ------------------------------------------------------------ the same search in another tab
                url = pg.url
                ctx2, pg2 = page(w, h); pg2.goto(url); ready(pg2)
                same = pg2.evaluate("""() => ({chips: [...document.querySelectorAll('#pt-active [data-remove]')].map(b => b.dataset.remove).sort(),
                  total: +(document.querySelector('#pt-count strong')?.textContent || '0').replace(/\\D/g, ''), level: document.querySelector('#pt-level').value})""")
                check(f'{w}px · la dirección abre la misma búsqueda en otra pestaña', same['chips'] == ['area', 'level'] and same['total'] == f['total'] and same['level'] == 'start', same)
                ctx2.close()
                # ------------------------------------------------------------ ✕ on a chip and «Borrar todo»
                pg.click('#pt-active [data-remove="level"]'); pg.wait_for_timeout(900)
                g = pg.evaluate("({chips:[...document.querySelectorAll('#pt-active [data-remove]')].map(b=>b.dataset.remove),hash:location.hash,button:document.querySelector('#pt-filters-btn').innerText.replace(/\\s+/g,' ').trim()})")
                check(f'{w}px · la ✕ de una ficha quita solo ese filtro', g['chips'] == ['area'] and 'level=' not in g['hash'] and g['button'] == 'Filtros (1)', g)
                pg.click('#pt-clear'); pg.wait_for_timeout(900)
                g = pg.evaluate("({hidden:document.querySelector('#pt-active').hidden,hash:location.hash,button:document.querySelector('#pt-filters-btn').innerText.trim()})")
                check(f'{w}px · «Borrar todo» quita todos los filtros', g['hidden'] and g['hash'] == '#/puntos' and g['button'] == 'Filtros', g)
                check(f'{w}px · sin desplazamiento de lado', pg.evaluate('document.documentElement.scrollWidth<=innerWidth+1'))
                ctx.close()

            # ---------------------------------------------------------------- the map view from the address, with the keyboard
            ctx, pg = page(1440, 900)
            pg.goto(srv.base + '/#/puntos?level=mid&view=map'); pg.wait_for_selector('#pt-map .pt-pin-wrap, #pt-map .marker-cluster', timeout=20000); pg.wait_for_timeout(800)
            m = pg.evaluate("({map:!document.querySelector('#pt-mapview').hidden,pressed:document.querySelector('.pt-view [data-view=\"map\"]').getAttribute('aria-pressed'),chips:[...document.querySelectorAll('#pt-active [data-remove]')].map(b=>b.dataset.remove)})")
            check('1440px · la dirección con view=map abre el mapa con su filtro', m['map'] and m['pressed'] == 'true' and m['chips'] == ['level'], m)
            pg.focus('#pt-filters-btn'); pg.keyboard.press('Enter'); pg.wait_for_timeout(300)
            k = pg.evaluate("({open:!document.querySelector('#pt-panel').hidden,focus:document.activeElement?.id})")
            pg.keyboard.press('Escape'); pg.wait_for_timeout(200)
            check('1440px · con el teclado: Intro abre «Filtros» con el foco dentro y Esc lo cierra', k['open'] and k['focus'] == 'pt-area' and pg.evaluate("document.querySelector('#pt-panel').hidden"), k)
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
