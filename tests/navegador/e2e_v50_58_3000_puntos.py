#!/usr/bin/env python3
"""v50.58 · Encargo de puntos del 16/10/2026, B.6: el mapa con más de 3.000 puntos sigue fluido.

Sobre una COPIA de prueba del catálogo de ejemplo (nunca la base real) se añaden 2.800 puntos inventados, cada uno a
pocos kilómetros de un punto del catálogo, hasta pasar de 3.000. Solo existen en esa copia, que se borra al terminar.
Se mide:
1. el servidor: lo que tarda y lo que pesa la lista del mapa (/api/dive-points/map y la vista «Mapa» de Puntos);
2. «Explorar» y la vista «Mapa» de «Puntos de buceo»: lo que tarda en salir el mapa con sus grupos, cuántas marcas
   hay en la página (los grupos evitan pintar 3.000 marcas) y si al acercarse y moverse va fluido en un móvil con la
   CPU cuatro veces más lenta (fotogramas medidos en el navegador);
3. la lista de «Puntos de buceo»: dice el total y pinta una página, no 3.000 fichas.

    python3 tests/navegador/e2e_v50_58_3000_puntos.py [carpeta-de-capturas]
"""
from __future__ import annotations

import gzip
import random
import sqlite3
import statistics
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

EXTRA = 2800
NO_COOKIES = "try{localStorage.setItem('wd_cookie_notice',String(Date.now()));localStorage.removeItem('wd-map-layer')}catch(e){}"
MOBILE = dict(viewport={'width': 412, 'height': 823}, device_scale_factor=1.75, is_mobile=True, has_touch=True, locale='es-ES')
DESK = dict(viewport={'width': 1440, 'height': 900}, locale='es-ES')
FRAMES = """ms => new Promise(done => { const ts = []; let last = performance.now(); const end = last + ms;
  const tick = now => { ts.push(now - last); last = now; if (now < end) requestAnimationFrame(tick); else done(ts.slice(2)); };
  requestAnimationFrame(tick); })"""


def add_points(db: Path):
    """2.800 puntos inventados junto a los del catálogo de ejemplo (en la copia de prueba)."""
    c = sqlite3.connect(db); c.row_factory = sqlite3.Row
    base = [dict(r) for r in c.execute('SELECT * FROM dive_points WHERE active=1 AND latitude IS NOT NULL')]
    cols = [k for k in base[0] if k != 'id']
    rnd = random.Random(5058)
    rows = []
    for i in range(EXTRA):
        b = dict(rnd.choice(base))
        b['name'] = f'Punto de prueba {i + 1:04d}'
        b['latitude'] = round(b['latitude'] + rnd.uniform(-0.06, 0.06), 6)
        b['longitude'] = round(b['longitude'] + rnd.uniform(-0.06, 0.06), 6)
        b['center_id'] = None
        rows.append([b[k] for k in cols])
    c.executemany(f'INSERT INTO dive_points ({",".join(cols)}) VALUES ({",".join("?" * len(cols))})', rows)
    c.commit()
    total = c.execute('SELECT COUNT(*) FROM dive_points WHERE active=1').fetchone()[0]
    c.close()
    return total


def timed_get(url, gz=False):
    req = urllib.request.Request(url, headers={'Accept-Encoding': 'gzip'} if gz else {})
    t = time.perf_counter()
    with urllib.request.urlopen(req, timeout=30) as r:
        body = r.read(); enc = r.headers.get('Content-Encoding', '')
    return (time.perf_counter() - t) * 1000, len(body), enc


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='wod-e2e-3000-'))
    out.mkdir(parents=True, exist_ok=True)
    srv = Server({'WOD_DEMO_MODE': '0'})
    add_points(srv.db)
    srv.start()
    total = srv.sql('SELECT COUNT(*) AS n FROM dive_points WHERE active=1')[0]['n']   # after the start-up migrations
    rows, errors = [], []

    def check(what, ok, detail=''):
        rows.append((what, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + what + ('' if ok else f'  → {str(detail)[:400]}'), flush=True)

    def note(text):
        print('   medida · ' + text, flush=True)

    try:
        check(f'la copia de prueba tiene más de 3.000 puntos ({total})', total > 3000, total)

        # ---------------------------------------------------------------- 1. servidor
        timed_get(srv.base + '/api/dive-points/map')                       # the first one builds the cached answer
        times = [timed_get(srv.base + '/api/dive-points/map', gz=True) for _ in range(5)]
        ms, size_gz, enc = statistics.median(t[0] for t in times), times[0][1], times[0][2]
        raw = timed_get(srv.base + '/api/dive-points/map')[1]
        note(f'/api/dive-points/map con {total} puntos: {ms:.0f} ms (mediana de 5), {raw / 1024:.0f} KB, {size_gz / 1024:.0f} KB comprimido ({enc or "sin comprimir"})')
        check('servidor · la lista del mapa sale en menos de 300 ms', ms < 300, ms)
        check('servidor · la lista del mapa viaja comprimida y pesa menos de 250 KB', enc == 'gzip' and size_gz < 250 * 1024, (enc, size_gz))
        times = [timed_get(srv.base + '/api/point-directory?view=map', gz=True) for _ in range(5)]
        ms = statistics.median(t[0] for t in times)
        note(f'/api/point-directory?view=map: {ms:.0f} ms (mediana de 5), {times[0][1] / 1024:.0f} KB ({times[0][2] or "sin comprimir"})')
        check('servidor · la vista «Mapa» de Puntos sale en menos de 500 ms', ms < 500, ms)

        with sync_playwright() as pw:
            browser = chromium(pw)

            def page_for(opts, slow=False):
                ctx = browser.new_context(**opts); ctx.add_init_script(NO_COOKIES)
                ctx.route('https://wms.gebco.net/**', lambda r: r.abort())
                pg = ctx.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)[:200]))
                if slow:
                    ctx.new_cdp_session(pg).send('Emulation.setCPUThrottlingRate', {'rate': 4})
                return pg

            def wait_marks(pg, sel, limit=30):
                t = time.perf_counter()
                while time.perf_counter() - t < limit:
                    if pg.evaluate(f"document.querySelectorAll('{sel} .leaflet-marker-icon').length"): break
                    pg.wait_for_timeout(100)
                return (time.perf_counter() - t) * 1000

            def marks(pg, sel):
                return pg.evaluate(f"""(() => ({{all: document.querySelectorAll('{sel} .leaflet-marker-icon').length,
                    groups: document.querySelectorAll('{sel} .wd-cluster-wrap').length,
                    inGroups: [...document.querySelectorAll('{sel} .wd-cluster')].reduce((n, e) => n + (parseInt(e.textContent) || 0), 0)}}))()""")

            def move_around(pg, sel):
                """Zoom in twice and drag the map, measuring frames while it animates."""
                box = pg.locator(sel).bounding_box(); cx, cy = box['x'] + box['width'] / 2, box['y'] + box['height'] / 2
                frames = []
                for _ in range(2):
                    pg.evaluate(f"document.querySelector('{sel} .leaflet-control-zoom-in').click()")
                    frames += pg.evaluate(FRAMES, 900)
                pg.mouse.move(cx, cy); pg.mouse.down()
                for k in range(12):
                    pg.mouse.move(cx - 18 * k, cy - 8 * k)
                pg.mouse.up()
                frames += pg.evaluate(FRAMES, 900)
                for _ in range(2):
                    pg.evaluate(f"document.querySelector('{sel} .leaflet-control-zoom-out').click()")
                    frames += pg.evaluate(FRAMES, 900)
                return frames

            for label, opts, slow, url, sel in (
                    ('Explorar · ordenador', DESK, False, '#/explorar', '#explore-map'),
                    ('Explorar · móvil con la CPU 4× más lenta', MOBILE, True, '#/explorar', '#explore-map'),
                    ('Puntos, vista «Mapa» · ordenador', DESK, False, '#/puntos?view=map', '#pt-map'),
                    ('Puntos, vista «Mapa» · móvil con la CPU 4× más lenta', MOBILE, True, '#/puntos?view=map', '#pt-map')):
                pg = page_for(opts, slow)
                t0 = time.perf_counter(); pg.goto(srv.base + '/' + url)
                waited = wait_marks(pg, sel); first = (time.perf_counter() - t0) * 1000
                pg.wait_for_timeout(1500)
                m = marks(pg, sel)
                note(f'{label}: mapa con sus grupos a los {first / 1000:.1f} s; {m["all"]} marcas en la página ({m["groups"]} grupos con {m["inGroups"]} puntos)')
                limit = 8000 if slow else 4000
                check(f'{label}: el mapa sale con sus marcas en menos de {limit // 1000} s', waited < 30000 and first < limit, first)
                check(f'{label}: los puntos van en grupos (menos de 400 marcas en la página)', 0 < m['all'] < 400 and m['groups'] > 0, m)
                frames = move_around(pg, sel)
                med, p95 = statistics.median(frames), sorted(frames)[int(len(frames) * .95)]
                long_ = sum(1 for f in frames if f > 100)
                note(f'{label}: al acercarse, moverse y alejarse, fotograma mediano {med:.1f} ms, p95 {p95:.1f} ms, {long_} de {len(frames)} por encima de 100 ms')
                check(f'{label}: fluido al moverse (fotograma mediano < 34 ms, como mínimo 30 por segundo)', med < 34, (med, p95))
                check(f'{label}: sin tirones largos (p95 < 100 ms)', p95 < 100, (med, p95, long_))
                pg.screenshot(path=str(out / (label.split(' ·')[0].replace('«', '').replace('»', '').replace(',', '').replace(' ', '-').lower()
                                               + ('-movil' if opts is MOBILE else '-ordenador') + '.png')))
                pg.context.close()

            # ---------------------------------------------------------------- 3. the list
            pg = page_for(DESK)
            pg.goto(srv.base + '/#/puntos'); pg.wait_for_selector('#pt-grid .pt-card:not(.is-skeleton)', timeout=20000); pg.wait_for_timeout(800)
            info = pg.evaluate("({cards: document.querySelectorAll('#pt-grid .pt-card').length, count: document.querySelector('#pt-count')?.textContent || document.querySelector('.pt-count')?.textContent || ''})")
            digits = ''.join(ch for ch in info['count'] if ch.isdigit())
            note(f'lista de Puntos: {info["cards"]} fichas pintadas; el contador dice «{info["count"].strip()}»')
            check('lista · pinta una página de fichas, no 3.000', 0 < info['cards'] <= 60, info)
            check('lista · el contador dice el total de puntos', digits == str(total), info)
            pg.context.close()
            check('sin errores de JavaScript', not errors, errors)
    finally:
        srv.stop()
    ok = sum(1 for _, good in rows if good)
    print(f'\n{ok}/{len(rows)} comprobaciones correctas · capturas en {out}')
    return 0 if ok == len(rows) else 1


if __name__ == '__main__':
    sys.exit(main())
