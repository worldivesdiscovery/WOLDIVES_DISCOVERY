"""Real browser walk (Chromium + Playwright) through every screen with the 5 roles.

Fails on JavaScript errors, Content-Security-Policy violations and server errors (HTTP 500).
Usage: python tests/e2e_walk.py [--shots DIR]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from helpers import ServerTestCase, Server, Client  # noqa: E402

from playwright.sync_api import sync_playwright  # noqa: E402

PUBLIC_ROUTES = ['#/', '#/explorar', '#/puntos', '#/centros', '#/tipos', '#/experiencias', '#/top10', '#/login', '#/registro',
                 '#/legal/aviso-legal', '#/legal/privacidad', '#/legal/cookies', '#/legal/condiciones-buceadores', '#/legal/condiciones-centros',
                 '#/legal/denuncias', '#/setup', '#/recuperar']
DIVER_ROUTES = ['#/area', '#/cuenta', '#/logbook', '#/recompensas', '#/reservar']
PRO_ROUTES = ['#/admin', '#/cuenta']
ADMIN_ROUTES = ['#/admin', '#/admin?tab=claims', '#/admin?tab=users', '#/admin?tab=centers', '#/admin?tab=points', '#/admin?tab=bookings',
                '#/admin?tab=emails', '#/admin?tab=legal', '#/admin?tab=adminpay', '#/admin?tab=audit']


def walk(shots: Path | None = None, extra_routes=None):
    t = ServerTestCase('run')
    ServerTestCase.server = Server().start()
    problems = []
    try:
        admin = t.make_admin()
        center = t.make_center(admin, 'walk')
        pro = t.make_freelance(admin, 'walkpro')
        diver = t.make_diver('walker')
        accounts = {'anon': None, 'diver': ('diver_walker', 'buceo-seguro-2026'), 'center': ('center_walk', 'buceo-seguro-2026'),
                    'freelance': ('pro_walkpro', 'buceo-seguro-2026'), 'admin': ('admin', 'admin-seguro-2026')}
        plan = {'anon': PUBLIC_ROUTES, 'diver': DIVER_ROUTES + ['#/centros'], 'center': PRO_ROUTES, 'freelance': PRO_ROUTES, 'admin': ADMIN_ROUTES}
        for k, v in (extra_routes or {}).items():
            plan[k] = plan.get(k, []) + v
        base = ServerTestCase.server.base
        with sync_playwright() as p:
            exe = next((str(x) for x in (Path('/opt/pw-browsers/chromium-1194/chrome-linux/chrome'), Path('/opt/pw-browsers/chromium')) if x.exists() and x.is_file()), None)
            browser = p.chromium.launch(executable_path=exe) if exe else p.chromium.launch()
            for role, creds in accounts.items():
                for viewport in ({'width': 1366, 'height': 900}, {'width': 390, 'height': 844}):
                    ctx = browser.new_context(viewport=viewport, locale='es-ES')
                    page = ctx.new_page()
                    errs = []
                    page.on('console', lambda m, errs=errs: errs.append(m.text) if m.type == 'error' else None)
                    page.on('pageerror', lambda e, errs=errs: errs.append('pageerror: ' + str(e)))
                    page.on('response', lambda r, errs=errs: errs.append(f'HTTP {r.status} {r.url}') if r.status >= 500 else None)
                    page.goto(base + '/#/')
                    page.wait_for_load_state('networkidle')
                    if creds:
                        page.goto(base + '/#/login')
                        page.wait_for_selector('#login')
                        page.fill('#login', creds[0]); page.fill('#password', creds[1])
                        page.click('#login-form button[type=submit]')
                        page.wait_for_timeout(800)
                    for route in plan[role]:
                        errs.clear()
                        page.goto(base + '/' + route)
                        page.wait_for_load_state('networkidle')
                        page.wait_for_timeout(250)
                        bad = [e for e in errs if 'favicon' not in e and 'tile.openstreetmap' not in e and 'ERR_' not in e and 'arcgis' not in e and 'gebco' not in e]
                        if bad:
                            problems.append((role, viewport['width'], route, bad))
                        if shots:
                            shots.mkdir(parents=True, exist_ok=True)
                            name = f"{role}-{viewport['width']}-{route.replace('#/', '').replace('/', '_').replace('?', '_').replace('=', '-') or 'home'}.png"
                            page.screenshot(path=str(shots / name), full_page=False)
                    ctx.close()
            browser.close()
    finally:
        ServerTestCase.server.stop()
        errors = [l for l in ServerTestCase.server.stderr.splitlines() if ' -> ' in l]
        if errors:
            problems.append(('server', 0, '', errors))
    return problems


if __name__ == '__main__':
    shots = Path(sys.argv[sys.argv.index('--shots') + 1]) if '--shots' in sys.argv else None
    probs = walk(shots)
    for p in probs:
        print('PROBLEMA', p)
    print('OK: ningún error' if not probs else f'{len(probs)} pantallas con errores')
    sys.exit(1 if probs else 0)
