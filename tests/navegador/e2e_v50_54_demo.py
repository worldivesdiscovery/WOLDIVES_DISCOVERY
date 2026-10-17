#!/usr/bin/env python3
"""v50.54 · punto 6: entrar en la demo con cada cuenta, por el formulario y por «Acceso rápido a la demostración».

Se reproduce el fallo tal como lo veía el titular: el paquete de pruebas tiene como dirección pública
http://127.0.0.1:PUERTO pero abre el navegador en http://localhost:PUERTO. Hasta v50.53 el servidor rechazaba cada
envío del formulario por venir de «otro origen» y nadie podía entrar.

    python3 tests/navegador/e2e_v50_54_demo.py [carpeta-de-capturas]
    python3 tests/navegador/e2e_v50_54_demo.py --base http://localhost:8100 [carpeta]   # un paquete DEMO ya arrancado

Comprueba también que sin WOD_DEMO_MODE el bloque no aparece y su dirección no existe.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from crear_demo import ACCOUNTS, PASSWORD  # noqa: E402

# The five buttons the owner asked for, in this order, and the role each one must open.
QUICK = [('Administrador', 'admin', 'admin'), ('Centro de buceo 1', 'center', 'center'), ('Centro de buceo 2', 'center2', 'center'),
         ('Freelance', 'freelance', 'freelance'), ('Buceador', 'diver', 'recreational')]
SIZES = {'escritorio': {'width': 1366, 'height': 900}, 'movil': {'width': 390, 'height': 844}}


def main():
    args = [a for a in sys.argv[1:]]
    base = None
    if '--base' in args:
        i = args.index('--base'); base = args[i + 1].rstrip('/'); del args[i:i + 2]
    out = Path(args[0]) if args else Path(tempfile.mkdtemp(prefix='wod-e2e-v5054-'))
    out.mkdir(parents=True, exist_ok=True)
    servers, results, problems = [], [], []
    try:
        if base is None:
            tmp = Path(tempfile.mkdtemp(prefix='wod-demo-')) / 'demo.sqlite3'
            r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(tmp)], capture_output=True, text=True)
            assert r.returncode == 0, r.stdout + r.stderr
            # The public address stays http://127.0.0.1:P (like iniciar.py --pruebas); the browser opens localhost.
            srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=tmp).start()
            servers.append(srv)
            assert srv.env['WOD_PUBLIC_URL'].startswith('http://127.0.0.1:')
            base = f'http://localhost:{srv.port}'
        prod = Server().start(); servers.append(prod)   # the same code without WOD_DEMO_MODE
        with sync_playwright() as pw:
            browser = chromium(pw)
            errors = []

            def page_for(size='escritorio'):
                ctx = browser.new_context(viewport=SIZES[size], locale='es-ES')
                pg = ctx.new_page()
                pg.on('console', lambda m: errors.append(f'{m.type}: {m.text}') if m.type == 'error' else None)
                pg.on('pageerror', lambda e: errors.append(f'pageerror: {e}'))
                return ctx, pg

            def me(pg):
                return pg.evaluate("fetch('/api/me',{credentials:'same-origin'}).then(r=>r.json())")

            def wait_signed_in(pg):
                for _ in range(100):
                    m = me(pg)
                    if m.get('authenticated'): return m
                    pg.wait_for_timeout(100)
                return me(pg)

            # 1) The form, with every account of the brief (username and, for the first, the email).
            for key, expected in [('admin', 'admin'), ('center', 'center'), ('center2', 'center'), ('freelance', 'freelance'), ('diver', 'recreational')]:
                user, email, _ = ACCOUNTS[key]
                for login in ((user, email) if key == 'admin' else (user,)):
                    ctx, pg = page_for()
                    pg.goto(base + '/#/login'); pg.wait_for_selector('#login-form')
                    pg.fill('#login', login); pg.fill('#password', PASSWORD); pg.click('#login-form button[type=submit]')
                    m = wait_signed_in(pg)
                    ok = m.get('authenticated') and m['user']['role'] == expected
                    results.append(('formulario', login, 'entra' if ok else f"NO entra ({m})"))
                    if not ok: problems.append(f'formulario {login}: {m}')
                    ctx.close()

            # 2) The quick access block: five buttons, each one opens its panel.
            ctx, pg = page_for()
            pg.goto(base + '/#/login'); pg.wait_for_selector('.demo-quick [data-demo-login]')
            labels = [t.strip().split('\n')[0] for t in pg.locator('.demo-quick-btn strong').all_inner_texts()]
            if labels != [q[0] for q in QUICK]: problems.append(f'botones del acceso rápido: {labels}')
            pg.screenshot(path=str(out / 'login-acceso-rapido-escritorio.png'), full_page=True)
            ctx.close()
            ctx, pg = page_for('movil')
            pg.goto(base + '/#/login'); pg.wait_for_selector('.demo-quick [data-demo-login]'); pg.wait_for_timeout(300)
            pg.screenshot(path=str(out / 'login-acceso-rapido-movil.png'), full_page=True)
            ctx.close()
            for label, key, expected in QUICK:
                ctx, pg = page_for()
                pg.goto(base + '/#/login'); pg.wait_for_selector('.demo-quick [data-demo-login]')
                pg.locator('.demo-quick-btn', has_text=label).first.click()
                m = wait_signed_in(pg)
                for _ in range(100):   # the page's CSP does not allow wait_for_function (eval)
                    if pg.evaluate('location.hash').startswith(('#/admin', '#/area', '#/cuenta')): break
                    pg.wait_for_timeout(100)
                ok = m.get('authenticated') and m['user']['role'] == expected and m['user']['username'] == ACCOUNTS[key][0]
                results.append(('acceso rápido', label, ('entra como ' + m['user']['username'] + ' → ' + pg.evaluate('location.hash')) if ok else f'NO entra ({m})'))
                if not ok: problems.append(f'acceso rápido {label}: {m}')
                pg.wait_for_timeout(600)
                if key in ('admin', 'diver'): pg.screenshot(path=str(out / f'acceso-rapido-{key}.png'))
                ctx.close()

            # 3) Without WOD_DEMO_MODE: no block, no address.
            ctx, pg = page_for()
            pg.goto(prod.base + '/#/login'); pg.wait_for_selector('#login-form'); pg.wait_for_timeout(800)
            if pg.locator('.demo-quick').count(): problems.append('el bloque de acceso rápido aparece sin WOD_DEMO_MODE')
            status = pg.evaluate("fetch('/api/pruebas/cuentas').then(r=>r.status)")
            if status != 404: problems.append(f'/api/pruebas/cuentas sin demo devuelve {status}')
            results.append(('producción', 'sin bloque ni /api/pruebas/cuentas', 'correcto' if status == 404 and not pg.locator('.demo-quick').count() else 'FALLO'))
            pg.screenshot(path=str(out / 'login-produccion-escritorio.png'))
            ctx.close()
            browser.close()
            real_errors = [e for e in errors if 'status of 401' not in e and 'status of 404' not in e]
            if real_errors: problems.append('errores en la consola: ' + ' | '.join(real_errors[:5]))
    finally:
        for s in servers: s.stop()
    for kind, who, what in results: print(f'{kind:14} {who:34} {what}')
    print(f'Capturas en {out}')
    if problems:
        print('PROBLEMAS:\n - ' + '\n - '.join(problems)); sys.exit(1)
    print('OK: las 5 cuentas entran por el formulario y por el acceso rápido; sin demo no hay acceso rápido.')


if __name__ == '__main__':
    main()
