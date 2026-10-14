#!/usr/bin/env python3
"""v50.54 · punto 1 (velocidad) en un navegador real (Chromium) sobre la demo:

1. Una página sin mapa (Tipos) no descarga las librerías del mapa; cada mapa sigue funcionando cuando se abre
   (Inicio, Explorar, ficha del punto, vista «Mapa» de Puntos, Top 10 «Elegir en el mapa», editores de punto y centro).
2. En un móvil la portada baja la copia ligera de la foto (640 o 960 px), no el original.
3. CLS medido en el navegador (móvil, con la conexión 4G lenta que simula Lighthouse) por debajo de 0,1 en Inicio, Puntos, ficha del punto, Tipos, Top 10 y Centros.

    python3 tests/navegador/e2e_v50_54_velocidad.py [carpeta-de-capturas]
"""
from __future__ import annotations

import re
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
NO_COOKIES = "try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}"
# Layout shifts not caused by the visitor, added up from the first paint (the same rule as CLS, without session windows).
CLS = "window.__cls=0;try{new PerformanceObserver(l=>{for(const e of l.getEntries()) if(!e.hadRecentInput) window.__cls+=e.value}).observe({type:'layout-shift',buffered:true})}catch(e){}"
# Slow 4G as Lighthouse simulates it (150 ms, 1.6 Mbit/s): on a fast local connection everything arrives at once and
# no jump would show.
SLOW_4G = {'offline': False, 'latency': 150, 'downloadThroughput': 1_600_000 / 8, 'uploadThroughput': 750_000 / 8}
MOBILE = dict(viewport={'width': 412, 'height': 823}, device_scale_factor=1.75, is_mobile=True, has_touch=True, locale='es-ES')


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='wod-e2e-vel-'))
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
        pid = srv.sql("SELECT id FROM dive_points WHERE name LIKE 'Cabo San Antonio%' ORDER BY id LIMIT 1")[0]['id']
        cid = srv.sql("SELECT id FROM centers WHERE name LIKE 'Bahía Coralina%'")[0]['id']
        with sync_playwright() as pw:
            browser = chromium(pw)
            errors = []

            def page(ctx_opts=None, cls=False):
                ctx = browser.new_context(**(ctx_opts or dict(viewport={'width': 1366, 'height': 900}, locale='es-ES')))
                pg = ctx.new_page()
                pg.on('pageerror', lambda e: errors.append(str(e)))
                pg.on('dialog', lambda d: d.accept('Prueba de los mapas del editor'))
                pg.add_init_script(NO_COOKIES)
                if cls:
                    pg.add_init_script(CLS)
                    cdp = ctx.new_cdp_session(pg); cdp.send('Network.enable'); cdp.send('Network.emulateNetworkConditions', SLOW_4G)
                return ctx, pg

            # 1. map libraries only where there is a map
            ctx, pg = page()
            pg.goto(srv.base + '/#/tipos'); pg.wait_for_selector('.tp54'); pg.wait_for_timeout(800)
            check('Tipos no descarga las librerías del mapa', pg.evaluate("!window.L && !document.querySelector('script[src*=leaflet],link[href*=leaflet]')"))
            pg.goto(srv.base + '/#/'); pg.wait_for_selector('#home-map .leaflet-marker-icon', timeout=20000)
            check('Inicio: mapa con marcadores', pg.locator('#home-map .leaflet-marker-icon').count() > 0)
            pg.goto(srv.base + '/#/explorar'); pg.wait_for_selector('#explore-map .leaflet-marker-icon', timeout=20000)
            check('Explorar: mapa con marcadores', pg.locator('#explore-map .leaflet-marker-icon').count() > 0)
            pg.goto(srv.base + f'/#/punto?id={pid}'); pg.wait_for_selector('#pp-map'); pg.locator('#pp-map').scroll_into_view_if_needed()
            pg.wait_for_selector('#pp-map.leaflet-container', timeout=15000)
            check('Ficha del punto: mapa con su marcador', pg.locator('#pp-map .leaflet-marker-icon').count() == 1)
            pg.goto(srv.base + '/#/puntos?vista=mapa'); pg.wait_for_selector('.pt54'); pg.click('.pt-view [data-view="map"]')
            pg.wait_for_selector('#pt-map .leaflet-marker-icon', timeout=20000)
            check('Puntos, vista «Mapa»: marcadores', pg.locator('#pt-map .leaflet-marker-icon').count() > 0)
            pg.goto(srv.base + '/#/top10'); pg.wait_for_timeout(1500)
            pick = pg.locator('button', has_text='mapa').first
            if pick.count():
                pick.click(); pg.wait_for_selector('#tt-pick-map.leaflet-container', timeout=15000)
                pg.locator('#tt-pick-map').click(position={'x': 300, 'y': 200}); pg.wait_for_timeout(300)
                check('Top 10: elegir la posición en el mapa', not pg.locator('#tt-pick-ok').is_disabled())
            else:
                check('Top 10: botón «Elegir en el mapa»', False, 'no aparece')
            ctx.close()
            ctx, pg = page()
            pg.goto(srv.base + '/#/login'); pg.wait_for_selector('.demo-quick [data-demo-login]')
            pg.click('[data-demo-login="admin.prueba"]'); pg.wait_for_timeout(1800)
            pg.goto(srv.base + '/#/admin?tab=points'); pg.wait_for_timeout(1800)
            pg.locator('.edit-point').first.click(); pg.wait_for_selector('#point-editor-map.leaflet-container', timeout=15000)
            check('Editor de punto: marcador que se puede mover', pg.locator('#point-editor-map .leaflet-marker-draggable').count() == 1)
            pg.goto(srv.base + '/#/admin?tab=centers'); pg.wait_for_timeout(1500)
            pg.locator('button,a', has_text='Nuevo centro').first.click(); pg.wait_for_selector('#center-editor-map.leaflet-container', timeout=15000)
            check('Editor de centro: mapa', pg.locator('#center-editor-map .leaflet-marker-icon').count() == 1)
            ctx.close()

            # 2 and 3. on a phone: the light copy of the photo and no jumps
            for name, path, ready in (('inicio', '/#/', '.tp-hero-img'), ('puntos', '/#/puntos', '#pt-grid .pt-card:not(.is-skeleton)'),
                                      ('punto', f'/#/punto?id={pid}', '.pp-keys'), ('tipos', '/#/tipos', '.tp54'),
                                      ('top10', '/#/top10', '.tp-hero-img'), ('centros', '/#/centros', '.cd-card'),
                                      ('centro', f'/#/centro?id={cid}', '.cp-hero')):
                ctx, pg = page(MOBILE, cls=True)
                pg.goto(srv.base + path); pg.wait_for_selector(ready, timeout=60000); pg.wait_for_timeout(2500)
                if name == 'inicio':
                    src = pg.evaluate("document.querySelector('.tp-hero-img').currentSrc")
                    check('Móvil: la portada baja la copia ligera', re.search(r'-(640|960)\.webp$', src or ''), src)
                    check('Cabecera: idioma y cuenta visibles', pg.evaluate("getComputedStyle(document.querySelector('.header-tools')).visibility") == 'visible')
                cls = pg.evaluate('window.__cls')
                check(f'CLS en móvil por debajo de 0,1 ({name}: {cls:.3f})', cls < 0.1, cls)
                pg.screenshot(path=str(out / f'movil-{name}.png'))
                ctx.close()
            browser.close()
            check('Sin errores en la página', not errors, errors[:4])
    finally:
        srv.stop()
    for what, ok in rows: print(f"{'OK ' if ok else 'MAL'} {what}")
    print(f'Capturas en {out}')
    if problems:
        print('PROBLEMAS:\n - ' + '\n - '.join(problems)); sys.exit(1)
    print('OK: mapas solo donde hacen falta, fotos ligeras en el móvil y sin saltos.')


if __name__ == '__main__':
    main()
