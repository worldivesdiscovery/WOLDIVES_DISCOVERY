"""v50.51 · Recorrido en un navegador real sobre la base de la VERSIÓN DE DEMOSTRACIÓN (scripts/crear_demo.py), en
ordenador y en móvil, con capturas: la ficha de los puntos de los dos centros inventados con su vida marina y el
bocadillo abierto, la página de un centro en otros idiomas, el aviso discreto de demostración, las cuentas de
CUENTAS-DEMO.txt y Administración → Operación → «Estado del sistema».

    python tests/navegador/e2e_demo_v50_51.py [CARPETA_DE_CAPTURAS]
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Client, Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from crear_demo import ACCOUNTS, DATA, PASSWORD  # noqa: E402


def run(shots: Path | None):
    results = []

    def check(name, ok, detail=''):
        results.append((name, bool(ok))); print(('OK  ' if ok else 'MAL ') + name + ('' if ok else f'  → {detail}'), flush=True)

    tmp = Path(tempfile.mkdtemp(prefix='wod-demo51-')) / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(tmp)], capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stdout + r.stderr)
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=tmp).start()
    try:
        base = srv.base
        api = Client(srv)
        pts = {p['name']: p['id'] for p in api.get('/api/dive-points').json['items']}
        cid = srv.sql("SELECT id FROM centers WHERE name=?", (DATA['bahia']['name'],))[0]['id']
        for name in ('Cabo San Antonio', 'Islas Medes, Costa Brava', 'Medes – Tascons'):
            n = len(api.get(f'/api/dive-points/{pts[name]}?lang=es').json['species'])
            check(f'demo · {name}: entre 8 y 15 especies', 8 <= n <= 15, n)
        for role, (u, _e, _n) in ACCOUNTS.items():
            check(f'cuenta {role} ({u}) entra con la contraseña de CUENTAS-DEMO.txt', Client(srv).login(u, PASSWORD).status == 200)
        with sync_playwright() as p:
            browser = chromium(p)
            DESK = {'viewport': {'width': 1366, 'height': 900}}
            PHONE = {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}

            def page_for(opts, lang='es-ES'):
                ctx = browser.new_context(**opts, locale=lang)
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg = ctx.new_page(); pg.errors = []
                pg.on('pageerror', lambda e: pg.errors.append(str(e)))
                return pg

            def go(pg, route, wait=1500):
                pg.goto(base + '/' + route); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(wait)

            def shot(pg, name, full=False, el=None):
                if not shots: return
                shots.mkdir(parents=True, exist_ok=True)
                if full:
                    h = pg.evaluate('document.body.scrollHeight')
                    for y in range(0, h, 500): pg.evaluate(f'window.scrollTo(0,{y})'); pg.wait_for_timeout(50)
                    pg.evaluate('window.scrollTo(0,0)'); pg.wait_for_timeout(300)
                (pg.locator(el) if el else pg).screenshot(path=str(shots / f'{name}.jpg'), type='jpeg', quality=82, **({'full_page': True} if full and not el else {}))

            def open_first_species(pg):
                pg.locator('#pm-viewport').scroll_into_view_if_needed(); pg.wait_for_timeout(300)
                bb = pg.locator('#pm-track .pm-item').first.bounding_box()
                pg.mouse.move(bb['x'] + bb['width'] / 2, bb['y'] + 20); pg.wait_for_timeout(150); pg.mouse.down(); pg.mouse.up(); pg.wait_for_timeout(500)

            # ordenador · ficha de Cabo San Antonio (Bahía Coralina)
            pg = page_for(DESK)
            go(pg, f'#/punto?id={pts["Cabo San Antonio"]}')
            check('aviso discreto «Versión de demostración»', 'Versión de demostración' in pg.inner_text('#demo-ribbon')
                  and pg.evaluate("getComputedStyle(document.getElementById('demo-ribbon')).position") != 'sticky')
            check('ficha · «Vida marina en esta inmersión · 14 especies»', pg.inner_text('.pm-count').strip() == '14 especies')
            check('ficha · «Recorrido virtual» justo debajo', pg.evaluate("document.querySelector('.pm-block').nextElementSibling.querySelector('h2').textContent.trim()") == 'Recorrido virtual')
            shot(pg, 'ordenador-ficha-cabo-san-antonio', full=True)
            open_first_species(pg)
            check('ficha · bocadillo abierto', pg.locator('#pm-pop').count() == 1)
            pg.evaluate("window.scrollBy(0, document.getElementById('pm-pop').getBoundingClientRect().top - 260)"); pg.wait_for_timeout(300)
            shot(pg, 'ordenador-ficha-bocadillo')
            check('ficha · sin errores de JavaScript', not pg.errors, pg.errors)
            pg.context.close()
            # ordenador · Islas Medes en inglés (Escafandra Medes) con el bocadillo
            pg = page_for(DESK, 'en-GB')
            go(pg, f'?lang=en#/punto?id={pts["Islas Medes, Costa Brava"]}')
            check('inglés · «Marine life on this dive · 15 species»', pg.inner_text('.pm-title').strip() == 'Marine life on this dive' and pg.inner_text('.pm-count').strip() == '15 species')
            open_first_species(pg); shot(pg, 'ordenador-ficha-medes-en-bocadillo')
            pg.context.close()
            # ordenador · la página de un centro en alemán (su propio texto)
            pg = page_for(DESK, 'de-DE')
            go(pg, f'?lang=de#/centro?id={cid}')
            check('centro · su presentación en alemán', 'Bootstauchen am Kap San Antonio' in pg.inner_text('#app'))
            check('centro · reseñas con respuestas del centro', pg.locator('.review-card').count() >= 5 and pg.locator('.review-reply').count() >= 2)
            shot(pg, 'ordenador-centro-aleman', full=True)
            pg.context.close()
            # ordenador · administración: Estado del sistema
            pg = page_for(DESK)
            go(pg, '#/login', 800); pg.fill('#login', ACCOUNTS['admin'][0]); pg.fill('#password', PASSWORD); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1500)
            go(pg, '#/admin?tab=ops', 2000)
            rows = pg.locator('.ops-status tbody tr')
            check('administración · «Estado del sistema» con cada servicio', rows.count() >= 12, rows.count())
            check('administración · pagos «Pendiente» sin clave de Stripe', 'Pendiente' in pg.inner_text('.ops-status tr[data-service="payments"]'))
            check('administración · botón «Restaurar demo»', pg.locator('#ops-demo-reset').count() == 1)
            if rows.count(): pg.locator('#ops-status').scroll_into_view_if_needed(); pg.wait_for_timeout(300); shot(pg, 'ordenador-estado-del-sistema', el='.ops-status')
            check('administración · sin errores de JavaScript', not pg.errors, pg.errors)
            pg.context.close()

            # móvil
            pg = page_for(PHONE)
            go(pg, f'#/punto?id={pts["Cabo San Antonio"]}')
            check('móvil · nada más ancho que la pantalla', pg.evaluate('document.scrollingElement.scrollWidth <= innerWidth + 1'))
            shot(pg, 'movil-ficha-cabo-san-antonio', full=True)
            pg.locator('#pm-viewport').scroll_into_view_if_needed(); pg.wait_for_timeout(300)
            pg.evaluate("document.querySelector('#pm-track .pm-item').click()"); pg.wait_for_timeout(500)
            check('móvil · bocadillo como panel desde abajo', pg.locator('#pm-pop.is-sheet').count() == 1)
            shot(pg, 'movil-ficha-bocadillo')
            check('móvil · sin errores de JavaScript', not pg.errors, pg.errors)
            pg.context.close()
            pg = page_for(PHONE, 'fr-FR')
            go(pg, f'?lang=fr#/centro?id={cid}')
            check('móvil · centro en francés', 'Plongée en bateau au cap Saint-Antoine' in pg.inner_text('#app') and pg.evaluate('document.scrollingElement.scrollWidth <= innerWidth + 1'))
            shot(pg, 'movil-centro-frances')
            pg.context.close()
            browser.close()
    finally:
        srv.stop()
    bad = [n for n, ok in results if not ok]
    print(f'\n{len(results) - len(bad)}/{len(results)} comprobaciones correctas')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(run(Path(sys.argv[1]) if len(sys.argv) > 1 else None))
