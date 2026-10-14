#!/usr/bin/env python3
"""v50.54 · punto 1 (revisión UX) en un navegador real (Chromium) sobre la demo, a 360 y 390 px de ancho:

1. Ninguna caja de texto o selector de las pantallas públicas queda más estrecha de 120 px (en Top 10 la caja de
   localidad medía 34 px desde v50.53) y ningún selector corta su texto.
2. El nivel de un punto se llama igual en el filtro, las tarjetas y la ficha («Para empezar», «Intermedio»,
   «Avanzado»), y la ficha no dice «Por confirmar».
3. La ruta «Centros / …» se lee sobre la foto del centro (texto blanco).

    python3 tests/navegador/e2e_v50_54_ux.py [carpeta-de-capturas]
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
LEVELS = {'Para empezar', 'Intermedio', 'Avanzado'}
# Too narrow (< 120 px), or a select whose chosen text does not fit: its width measured with the select's own font
# against the room left by its padding (a select never reports the overflow in scrollWidth).
NARROW = """(()=>{ const ctx=document.createElement('canvas').getContext('2d');
  const cut=e=>{ if(e.tagName!=='SELECT') return false; const c=getComputedStyle(e); ctx.font=`${c.fontWeight} ${c.fontSize} ${c.fontFamily}`;
    const txt=e.options[e.selectedIndex]?.text||''; return ctx.measureText(txt).width > e.clientWidth-parseFloat(c.paddingLeft)-parseFloat(c.paddingRight)+1; };
  return [...document.querySelectorAll('#app input:not([type=hidden]):not([type=checkbox]):not([type=radio]):not([type=range]), #app select, #app textarea')]
    .filter(e=>e.offsetParent).map(e=>[e.id||e.name||e.placeholder||e.tagName, Math.round(e.getBoundingClientRect().width), cut(e)])
    .filter(x=>x[1]<120||x[2]); })()"""


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='wod-e2e-ux-'))
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='wod-demo-')) / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(tmp)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=tmp).start()
    rows, problems = [], []

    def check(what, ok, detail=''):
        rows.append((what, bool(ok)))
        if not ok: problems.append(f'{what}: {detail}')

    try:
        pid = srv.sql("SELECT id FROM dive_points WHERE difficulty='Moderado' ORDER BY id LIMIT 1")[0]['id']   # a word not in the filter
        cid = srv.sql("SELECT id FROM centers WHERE name LIKE 'Bahía Coralina%'")[0]['id']
        routes = ['#/', '#/puntos', f'#/punto?id={pid}', '#/tipos', '#/tipos?t=arrecifes', '#/centros', f'#/centro?id={cid}',
                  '#/experiencias', '#/top10', '#/login', '#/registro']
        with sync_playwright() as pw:
            browser = chromium(pw)
            errors = []
            for width in (360, 390):
                ctx = browser.new_context(viewport={'width': width, 'height': 844}, is_mobile=True, has_touch=True, locale='es-ES')
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg = ctx.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
                bad = {}
                for route in routes:
                    pg.goto(srv.base + '/' + route); pg.wait_for_timeout(1500)
                    found = pg.evaluate(NARROW)
                    if found: bad[route] = found
                    if width == 390 and route in ('#/top10', '#/centros'): pg.screenshot(path=str(out / f'movil-{route[2:].split("?")[0] or "inicio"}.png'))
                check(f'{width} px: cajas y selectores con sitio y sin texto cortado', not bad, bad)
                ctx.close()
            ctx = browser.new_context(viewport={'width': 1366, 'height': 900}, locale='es-ES'); pg = ctx.new_page()
            pg.on('pageerror', lambda e: errors.append(str(e)))
            pg.goto(srv.base + f'/#/punto?id={pid}'); pg.wait_for_selector('.pp-keys')
            keys = pg.inner_text('.pp-keys'); page = pg.inner_text('#app')
            check('Ficha: el nivel con las palabras del filtro', 'Intermedio' in keys and 'Moderado' not in keys, keys)
            check('Ficha: nunca «Por confirmar»', 'Por confirmar' not in page)
            pg.goto(srv.base + '/#/puntos?level=mid'); pg.wait_for_selector('#pt-grid .pt-card:not(.is-skeleton)'); pg.wait_for_timeout(600)
            shown = set(pg.eval_on_selector_all('#pt-grid .pt-card', 'cs=>cs.map(c=>c.innerText)'))
            words = {w for t in shown for w in ('Moderado', 'Intermedia', 'Fácil', 'Principiante', 'Iniciación') if w in t}
            check('Tarjetas: ninguna palabra de nivel distinta de las del filtro', shown and not words, words or 'sin tarjetas')
            pg.goto(srv.base + f'/#/centro?id={cid}'); pg.wait_for_selector('.cp-crumb a')
            color = pg.eval_on_selector('.cp-crumb a', 'a=>getComputedStyle(a).color')
            check('Centro: la ruta se lee sobre la foto', color == 'rgb(255, 255, 255)', color)
            ctx.close(); browser.close()
            check('Sin errores en la página', not errors, errors[:4])
    finally:
        srv.stop()
    for what, ok in rows: print(f"{'OK ' if ok else 'MAL'} {what}")
    print(f'Capturas en {out}')
    if problems:
        print('PROBLEMAS:\n - ' + '\n - '.join(problems)); sys.exit(1)
    print('OK: revisión UX comprobada en el navegador.')


if __name__ == '__main__':
    main()
