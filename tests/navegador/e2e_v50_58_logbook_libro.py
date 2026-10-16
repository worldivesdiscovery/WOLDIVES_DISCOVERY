#!/usr/bin/env python3
"""v50.58 · El pasaporte del Log Book como un libro de verdad, en el navegador, sobre una copia de la demo.

Comprueba lo que pide el encargo del 16/10/2026 (docs/encargos/encargo-logbook-libro-16-10-2026.md):
1. Se sigue abriendo con los 5 toques.
2. Nada cortado en 360, 390, 414, 768, 1024, 1366, 1440 y 1920 px: el libro entero en la pantalla, bajo la cabecera y
   sin desplazarse; las dos ilustraciones enteras (proporción propia, sin recortar), sin triángulos ni bordes de foto.
3. Parece un libro: tapa que asoma, lomo, grosor de las hojas y sombra; centrado, como mucho 90 % del ancho y 85 % del alto.
4. Una sola página en el móvil en vertical; las dos en horizontal y en tableta.
5. Pasar páginas con las flechas, el teclado, arrastrando la esquina con el ratón, tocando el borde y deslizando el dedo,
   hacia delante y hacia atrás; indicador «n / total»; con «reducir movimiento», fundido sin giro.
6. Las páginas de inmersión: casillas impresas con los datos como texto real (campos) y el sello si está validada.
7. Consola sin errores.

    python3 tests/navegador/e2e_v50_58_logbook_libro.py [--capturas carpeta] [--solo-capturas carpeta]

--solo-capturas hace solo las capturas (sirve también con el código de antes, para las capturas «antes»).
Usa las cuentas de la demo: no va en el zip de producción (scripts/generar_zips.py)."""
from __future__ import annotations

import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app'),
                str(Path(__file__).resolve().parents[2] / 'scripts')]
from helpers import Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402
from crear_demo import PASSWORD  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
LB = 'DiveLogbook.instances.filter(i=>i.root.isConnected).at(-1)'
PP = LB + '.pp'
SIZES = [('360', 360, 780, True), ('390', 390, 844, True), ('414', 414, 896, True), ('768', 768, 1024, True), ('1024', 1024, 768, True),
         ('1366', 1366, 768, False), ('1440', 1440, 900, False), ('1920', 1920, 1080, False)]
SHOTS = [('ordenador-1440', 1440, 900, False), ('ordenador-1920', 1920, 1080, False), ('movil-390', 390, 844, True)]


def run(out: Path | None, only_shots: bool):
    rows = []

    def check(name, ok, detail=''):
        rows.append((name, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + name + (f'  · {str(detail)[:300]}' if detail != '' else ''), flush=True)

    tmp = Path(tempfile.mkdtemp(prefix='wod-libro-'))
    db = tmp / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(db)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': '', 'PYTHONUNBUFFERED': '1'}, seed=db).start()
    errors = []
    try:
        with sync_playwright() as pw:
            browser = chromium(pw)

            def ctx(w, h, touch, app=False, reduce=False):
                c = browser.new_context(viewport={'width': w, 'height': h}, locale='es-ES', is_mobile=touch and w < 1100, has_touch=touch,
                                        device_scale_factor=2 if touch else 1, reduced_motion='reduce' if reduce else 'no-preference')
                c.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                if app: c.add_init_script("try{localStorage.setItem('wda-tema','noche')}catch(e){}")
                pg = c.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
                pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
                pg.on('requestfailed', lambda r: errors.append(f'falló {r.url} ({r.failure})'))
                return c, pg

            def wait(pg, js, timeout=15000):
                """The page's CSP does not allow wait_for_function with text: the condition is read until it holds."""
                v = None
                for _ in range(timeout // 100):
                    v = pg.evaluate(js)
                    if v: return v
                    pg.wait_for_timeout(100)
                return v

            def login(pg):
                pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login-form')
                pg.fill('#login', 'buzo.prueba'); pg.fill('#password', PASSWORD); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1500)

            def open_book(pg, app=False, taps=True):
                """Log Book → the 5 taps (if still locked) → the passport, closed on its cover."""
                # a new visit (another address, not only another #): a reload would cut the first visit's requests half-way
                pg.goto(srv.base + ('/?app=1&libro=1' if app else '/?libro=1') + '#/logbook'); pg.wait_for_selector('#wd-logbook .dlc-head', timeout=20000)
                wait(pg, "() => (document.querySelector('#lb-sync')?.textContent||'').includes('Guardado')")
                tapped = False
                if pg.get_attribute('[data-c="toggle"]', 'data-state') != 'open' and taps:
                    for _ in range(5): pg.click('[data-c="toggle"]'); pg.wait_for_timeout(120)
                    pg.wait_for_timeout(500); tapped = True
                t0 = time.time(); pg.click('[data-c="toggle"]')
                # the passport opens by itself on its first spread (the two illustrations)
                wait(pg, f"() => {{ const pp = window.DiveLogbook && {PP}; return !!pp && pp.cur === 1 && !pp.anim && !pp.ts; }}", 6000)
                pg.t_open = time.time() - t0
                pg.wait_for_timeout(300)
                return tapped

            def turn(pg, n=1, how='next'):
                for _ in range(n): pg.click(f'[data-nav="{how}"]'); pg.wait_for_timeout(900)

            def shot(pg, folder, name):
                if folder: folder.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(folder / f'{name}.png'))

            # ------------------------------------------------------------------ captures (also with the old code: --solo-capturas)
            def captures():
                for name, w, h, touch in SHOTS:
                    for theme, app in (('clasico', False), ('noche', True)):
                        c, pg = ctx(w, h, touch, app); login(pg); open_book(pg, app)
                        pg.wait_for_timeout(1200)   # the old code had no «settled» state: the same pause for both
                        # the first spread: «DIVE LOGBOOK» and «EXPLORE · RECORD · PROTECT»
                        shot(pg, out, f'logbook-libro-{name}-{theme}-ilustraciones')
                        if touch and not only_shots:   # on the phone, one page: the right-hand one, the other illustration
                            turn(pg); shot(pg, out, f'logbook-libro-{name}-{theme}-ilustracion-derecha')
                        turn(pg, 2); shot(pg, out, f'logbook-libro-{name}-{theme}-inmersion')
                        pg.click('[data-nav="close"]'); pg.wait_for_timeout(1500); shot(pg, out, f'logbook-libro-{name}-{theme}-portada')
                        c.close()
            if only_shots:
                captures()
                return rows

            # ------------------------------------------------------------------ 1 · the 5 taps
            c, pg = ctx(1440, 900, False); login(pg)
            tapped = open_book(pg)
            check('1 · se abre con los 5 toques, como antes', tapped and pg.get_attribute('[data-c="toggle"]', 'data-state') == 'open'
                  and pg.evaluate("() => !document.querySelector('[data-c=\"passport\"]').hidden"))
            c.close()

            # ------------------------------------------------------------------ 2-4 · nothing cut, a real book, at every width
            for name, w, h, touch in SIZES:
                c, pg = ctx(w, h, touch); login(pg); open_book(pg)
                geo = pg.evaluate("""() => {
                    const lb = %s, pp = lb.pp, vp = (typeof lb.viewport === 'function' && lb.viewport()) || (() => {
                      // what covers the window (the same rule as the web's wdLbViewport): the sticky header, the app's band and tabs
                      const shown = e => !!e && e.getClientRects().length > 0; let top = 0;
                      const hd = document.querySelector('.site-header'); if (shown(hd) && /sticky|fixed/.test(getComputedStyle(hd).position)) top = Math.max(top, hd.offsetHeight);
                      const band = document.querySelector('.wda-banda'); if (shown(band)) top = Math.max(top, band.getBoundingClientRect().bottom);
                      const tabs = document.querySelector('.wda-tabs'); return {top, bottom: shown(tabs) ? tabs.getBoundingClientRect().height : 0}; })();
                    const R = e => { const b = e.getBoundingClientRect(); return {l: b.left, t: b.top, r: b.right, b: b.bottom, w: b.width, h: b.height}; };
                    const book = R(pp.scaleEl), root = R(pp.root);
                    const arts = [...pp.root.querySelectorAll('.dlb-art img')].filter(i => { const s = i.closest('.dlb-leaf'); return s && !s.inert && i.getClientRects().length; })
                      .map(i => { const b = R(i), sh = R(i.closest('.dlb-sheet')), cs = getComputedStyle(i);
                        return {b, sh, fit: cs.objectFit, ratio: b.w / b.h, nat: i.naturalWidth / i.naturalHeight, loaded: i.complete && i.naturalWidth > 0, src: i.currentSrc.split('/').pop()}; });
                    const vis = s => { const e = pp.root.querySelector(s); return !!e && !e.hidden && getComputedStyle(e).display !== 'none'; };
                    const shadow = s => { const e = pp.root.querySelector(s); return e ? getComputedStyle(e).boxShadow : 'none'; };
                    return {vw: innerWidth, vh: innerHeight, top: vp.top || 0, bottom: vp.bottom || 0, book, root, arts, single: pp.single, cur: pp.cur,
                      spine: vis('.dlb-spine'), stack: vis('.dlb-stack.r') && shadow('.dlb-stack.r') !== 'none',
                      ground: getComputedStyle(pp.root.querySelector('.dlb-ground')).boxShadow, board: vis('.dlb-board'),
                      hscroll: document.scrollingElement.scrollWidth - innerWidth,
                      count: pp.countEl.textContent, triangles: pp.root.querySelectorAll('.dlb-corner,.dlb-fold,[class*="triang"]').length};
                }""" % LB)
                b = geo['book']
                fits = b['l'] >= -0.5 and b['r'] <= geo['vw'] + 0.5 and b['t'] >= geo['top'] - 0.5 and b['b'] <= geo['vh'] - geo['bottom'] + 0.5
                check(f'2 · {name} px: el libro entero en la pantalla, bajo la cabecera y sin desplazarse', fits and geo['hscroll'] <= 0,
                      {k: round(v) for k, v in b.items()} | {'vw': geo['vw'], 'vh': geo['vh'], 'arriba': geo['top']})
                arts = geo['arts']
                whole = arts and all(a['loaded'] and a['fit'] == 'contain' and a['b']['l'] >= a['sh']['l'] - 0.5 and a['b']['r'] <= a['sh']['r'] + 0.5
                                     and a['b']['t'] >= a['sh']['t'] - 0.5 and a['b']['b'] <= a['sh']['b'] + 0.5
                                     and a['b']['l'] >= -0.5 and a['b']['r'] <= geo['vw'] + 0.5 for a in arts)
                check(f'2 · {name} px: las ilustraciones enteras, con su proporción y sin salirse de la página', whole,
                      [(a['src'], a['fit'], round(a['nat'], 3)) for a in arts])
                want_single = w < 600
                check(f'4 · {name} px: {"una sola página" if want_single else "las dos páginas abiertas"}', geo['single'] == want_single and len(arts) == (1 if want_single else 2),
                      (geo['single'], len(arts)))
                centred = abs((b['l'] + b['r']) / 2 - (geo['root']['l'] + geo['root']['r']) / 2) < 2
                big = b['w'] <= 0.9 * geo['root']['w'] + 1 and (b['w'] >= 0.9 * geo['root']['w'] - 2 or b['h'] >= 0.85 * (geo['vh'] - geo['top'] - geo['bottom'] - 56) - 2)
                check(f'3 · {name} px: centrado y del tamaño máximo que cabe (90 % del ancho u 85 % del alto)', centred and big,
                      (round(b['w']), round(b['h']), round(geo['root']['w'])))
                check(f'3 · {name} px: tapa, lomo, grosor de las hojas y sombra; sin triángulos', geo['spine'] and geo['stack'] and geo['ground'] != 'none'
                      and geo['board'] and not geo['triangles'], geo)
                c.close()

            # phone in landscape: the open book with the two pages
            c, pg = ctx(844, 390, True); login(pg); open_book(pg)
            st = pg.evaluate(f"() => ({{single: {PP}.single, n: [...{PP}.root.querySelectorAll('.dlb-art img')].filter(i => !i.closest('.dlb-leaf').inert).length}})")
            check('4 · móvil en horizontal: el libro abierto con las dos páginas', not st['single'] and st['n'] == 2, st)
            c.close()

            # ------------------------------------------------------------------ 5 · turning the pages
            c, pg = ctx(1440, 900, False); login(pg); open_book(pg)
            cur = lambda: pg.evaluate(f'() => {PP}.cur')
            count = lambda: pg.evaluate(f'() => {PP}.countEl.textContent')
            c0 = cur(); turn(pg); c1 = cur(); n1 = count(); turn(pg); c2 = cur(); turn(pg, 1, 'prev'); c3 = cur()
            check('5 · flechas ‹ ›: adelante y atrás', (c0, c1, c2, c3) == (1, 2, 3, 2), (c0, c1, c2, c3))
            check('5 · indicador «n–m / total» bajo el libro', bool(re.fullmatch(r'3–4 / \d+', n1)), n1)
            pg.keyboard.press('ArrowRight'); pg.wait_for_timeout(900); k1 = cur(); pg.keyboard.press('ArrowLeft'); pg.wait_for_timeout(900); k2 = cur()
            check('5 · teclas → y ←', (k1, k2) == (3, 2), (k1, k2))

            def corner(right=True):
                b = pg.evaluate(f"() => {{ const b = {PP}.book.getBoundingClientRect(), s = {PP}.scale; return {{l: b.left, t: b.top, s}}; }}")
                s, W, H, P = b['s'], 400, 617, 8
                y = b['t'] + (H - 14) * s
                x0 = b['l'] + ((2 * W - 14) if right else 14) * s
                x1 = b['l'] + (60 if right else 2 * W - 60) * s
                return x0, x1, y

            x0, x1, y = corner(True)
            pg.mouse.move(x0, y); pg.mouse.down()
            for i in range(1, 13): pg.mouse.move(x0 + (x1 - x0) * i / 12, y - 30 * i / 12); pg.wait_for_timeout(16)
            mid = pg.evaluate(f"() => !!{PP}.ts")   # the leaf is following the mouse
            pg.mouse.up(); pg.wait_for_timeout(1000); d1 = cur()
            x0, x1, y = corner(False)
            pg.mouse.move(x0, y); pg.mouse.down()
            for i in range(1, 13): pg.mouse.move(x0 + (x1 - x0) * i / 12, y - 30 * i / 12); pg.wait_for_timeout(16)
            pg.mouse.up(); pg.wait_for_timeout(1000); d2 = cur()
            check('5 · ratón: arrastrar la esquina dobla la hoja y la pasa (adelante y atrás)', mid and (d1, d2) == (3, 2), (mid, d1, d2))
            b = pg.evaluate(f"() => {{ const b = {PP}.book.getBoundingClientRect(); return {{l: b.left, t: b.top, s: {PP}.scale}}; }}")
            pg.mouse.click(b['l'] + (2 * 400 - 20) * b['s'], b['t'] + 300 * b['s']); pg.wait_for_timeout(1000); e1 = cur()
            pg.mouse.click(b['l'] + 20 * b['s'], b['t'] + 300 * b['s']); pg.wait_for_timeout(1000); e2 = cur()
            check('5 · clic en el borde de la página: adelante y atrás', (e1, e2) == (3, 2), (e1, e2))
            c.close()

            # the finger, on the phone (one page): swipe left and right
            c, pg = ctx(390, 844, True); login(pg); open_book(pg)
            cdp = c.new_cdp_session(pg)
            state = lambda: pg.evaluate(f'() => [{PP}.cur, {PP}.side]')

            def swipe(x0, x1, y):
                cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x0, 'y': y}]})
                for i in range(1, 11):
                    cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x0 + (x1 - x0) * i / 10, 'y': y}]}); pg.wait_for_timeout(16)
                cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []}); pg.wait_for_timeout(1100)

            box = pg.evaluate(f"() => {{ const b = {PP}.scaleEl.getBoundingClientRect(); return {{l: b.left, r: b.right, y: b.top + b.height * .55}}; }}")
            s0 = state(); swipe(box['r'] - 30, box['l'] + 30, box['y']); s1 = state(); swipe(box['r'] - 30, box['l'] + 30, box['y']); s2 = state()
            swipe(box['l'] + 30, box['r'] - 30, box['y']); s3 = state()
            check('5 · móvil: deslizar el dedo pasa de página (adelante y atrás)', s1 != s0 and s2 != s1 and s3 == s1, (s0, s1, s2, s3))
            n = pg.evaluate(f'() => {PP}.countEl.textContent')
            check('5 · móvil: indicador de una página «n / total»', bool(re.fullmatch(r'\d+ / \d+', n)), n)
            c.close()

            # a mid-range phone (the CPU 4 times slower): the turn runs smoothly
            c, pg = ctx(390, 844, True); login(pg)
            cdp = c.new_cdp_session(pg); cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
            open_book(pg)
            pg.evaluate(f"() => {{ const pp = {PP}; if (pp.side === 'left') pp.next(); }}"); pg.wait_for_timeout(400)   # on the right page: the next tap turns a leaf
            fr = pg.evaluate(f"""() => new Promise(done => {{ const ts = []; let t0 = 0;
                const tick = t => {{ ts.push(t); if (t - ts[0] < 800) requestAnimationFrame(tick); else {{
                  const gaps = ts.slice(1).map((x, i) => x - ts[i]); done({{fps: Math.round(1000 * gaps.length / (ts.at(-1) - ts[0])), worst: Math.round(Math.max(...gaps))}}); }} }};
                requestAnimationFrame(t => {{ {PP}.next(); tick(t); }}); }})""")
            check('5 · móvil de gama media (CPU 4 veces más lenta): la hoja pasa fluida', fr['fps'] >= 30 and fr['worst'] <= 100, f"{fr['fps']} imágenes/s, el peor salto {fr['worst']} ms")
            # from the tap: the cover (at once), a pause of 0.65 s and the cover opening (0.6 s), as a real book
            check('5 · y el pasaporte se abre sin retraso visible tras el toque', pg.t_open < 2.0, f'{pg.t_open:.2f} s del toque a la primera doble página quieta (0,65 s de pausa y 0,6 s de giro incluidos)')
            c.close()

            # reduce motion: a fade, no 3D turn
            c, pg = ctx(1440, 900, False, reduce=True); login(pg); open_book(pg)
            pg.click('[data-nav="next"]')
            seen = pg.evaluate(f"""() => new Promise(done => {{ const out = {{fade: false, turn: false}}, t0 = performance.now();
                const tick = () => {{ const pp = {PP};
                    if (pp.stage.classList.contains('is-fading')) out.fade = true;
                    if (pp.ts || pp.anim) out.turn = true;
                    if (performance.now() - t0 < 700) requestAnimationFrame(tick); else done(out); }}; tick(); }})""")
            pg.wait_for_timeout(400)
            check('5 · «reducir movimiento»: fundido sin giro', seen['fade'] and not seen['turn'] and pg.evaluate(f'() => {PP}.cur') == 2, seen)
            c.close()

            # ------------------------------------------------------------------ 6 · the dive pages
            c, pg = ctx(1440, 900, False); login(pg); open_book(pg); turn(pg, 3)
            dive = pg.evaluate(f"""() => {{ const pp = {PP}; const page = [...pp.root.querySelectorAll('.dlb-leaf')].filter(l => !l.inert)
                  .flatMap(l => [...l.querySelectorAll('.dlb-sheet')]).find(s => s.querySelector('[data-k$=":site"]'));
                if (!page) return null;
                const keys = [...page.querySelectorAll('[data-k]')].map(e => e.dataset.k.split(':').pop());
                return {{keys, inputs: page.querySelectorAll('input,textarea').length, stamp: !!page.querySelector('.dlb-stamp'), imgs: page.querySelectorAll('img').length}}; }}""")
            need = ['date', 'site', 'depth', 'time', 'temp', 'vis', 'buddy', 'center']
            check('6 · página de inmersión: fecha, punto, profundidad, tiempo, temperatura, visibilidad, compañero y centro, como texto (campos)',
                  dive and all(k in dive['keys'] for k in need) and dive['inputs'] >= len(need), dive)
            check('6 · y la casilla del sello del centro', dive and dive['stamp'], dive)
            c.close()

            # ------------------------------------------------------------------ 7 · console
            # without internet here, the map tiles of OpenStreetMap (the list's map, not the book) can not load: not the page's fault
            offline = [e for e in errors if 'tile.openstreetmap.org' in e or 'ERR_TUNNEL_CONNECTION_FAILED' in e]
            own = [e for e in errors if e not in offline]
            check('7 · consola sin errores', not own, own[:5] or f'(sin internet aquí: {len(offline)} avisos de las teselas del mapa de OpenStreetMap, fuera del libro)')
            if out: captures()   # last: the 5 taps of check 1 unlock the passport of the account
            browser.close()
    finally:
        srv.stop()
    return rows


if __name__ == '__main__':
    out = None
    only = '--solo-capturas' in sys.argv
    for flag in ('--capturas', '--solo-capturas'):
        if flag in sys.argv: out = Path(sys.argv[sys.argv.index(flag) + 1])
    rows = run(out, only)
    if not only:
        bad = [r for r in rows if not r[1]]
        print(f'{len(rows) - len(bad)}/{len(rows)} comprobaciones correctas')
        sys.exit(1 if bad else 0)
