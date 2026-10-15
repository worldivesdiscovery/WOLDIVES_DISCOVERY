#!/usr/bin/env python3
"""v50.57 · Revisión general 5.1: los cuatro modos completos, pantalla a pantalla, en un navegador real (Chromium) sobre
una copia de la demo: administración, centro, freelance y buceador, en el ordenador (1366 px) y en el móvil (390 px).

En cada pantalla (cada pestaña de cada panel, y las páginas del buceador):
- sin errores de JavaScript ni respuestas de error del servidor (500) ni peticiones rechazadas que la web no esperaba;
- sin textos rotos («undefined», «NaN», «[object Object]», «No se ha podido abrir», «Error interno»);
- en el móvil, nada se sale por el lado.
Con especial atención (el titular encontró fallos ahí):
- centro: reservas, planning y agenda con sus datos;
- freelance: reservas, planning y «Mi agenda» con sus datos;
- administración: destinos, puntos y plantillas: abrir uno, guardarlo sin cambios y volver a la lista con «Guardado».

    python3 tests/navegador/e2e_v50_57_modos.py [carpeta-de-capturas]

Usa las cuentas de la demo: no va en el zip de producción (scripts/generar_zips.py)."""
from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app'),
                str(Path(__file__).resolve().parents[2] / 'scripts')]
from helpers import Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402
from crear_demo import PASSWORD  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
BROKEN = re.compile(r'\bundefined\b|\bNaN\b|\[object Object\]|No se ha podido abrir|Error interno|Falta un dato obligatorio')
SIZES = {'ordenador': {'width': 1366, 'height': 900}, 'movil': {'width': 390, 'height': 844}}
DIVER_PAGES = ['#/area', '#/cuenta', '#/logbook', '#/recompensas', '#/mis-puntos', '#/seguro', '#/reserva?id={booking}']
# Answers the web asks for knowing they may say no (checked by the screens themselves, not errors).
EXPECTED_4XX = ('/api/admin/confirm/status', '/api/logbook', '/api/insurance', '/api/me/insurance')


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    db = Path(tempfile.mkdtemp(prefix='wod-modos-')) / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(db)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=db).start()
    rows, report = [], {}

    def check(what, ok, detail=''):
        rows.append((what, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + what + ('' if ok else f'  → {str(detail)[:500]}'), flush=True)

    try:
        booking = srv.sql("SELECT b.id FROM bookings b JOIN users u ON u.id=b.user_id WHERE u.username='buzo.prueba' ORDER BY b.id DESC LIMIT 1")[0]['id']
        with sync_playwright() as pw:
            browser = chromium(pw)
            for size, viewport in SIZES.items():
                for role, user in (('administración', 'admin.prueba'), ('centro', 'centro.prueba'), ('freelance', 'freelance.prueba'), ('buceador', 'buzo.prueba')):
                    ctx = browser.new_context(viewport=viewport, locale='es-ES')
                    ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                    pg = ctx.new_page(); errs = []; bad = []
                    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
                    pg.on('response', lambda rsp: bad.append(f'{rsp.status} {rsp.request.method} {rsp.url.split("?")[0].replace(srv.base, "")}')
                          if '/api/' in rsp.url and (rsp.status >= 500 or (rsp.status >= 400 and not rsp.url.split('?')[0].endswith(EXPECTED_4XX))) else None)
                    pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login-form')
                    pg.fill('#login', user); pg.fill('#password', PASSWORD); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1500)
                    if role == 'administración':   # 4.1: personal data with the password and a reason (as the window does)
                        pg.evaluate("""() => fetch('/api/admin/confirm', {method: 'POST', headers: {'Content-Type': 'application/json'},
                                       body: JSON.stringify({password: '%s', reason: 'Soporte: auditoría de los cuatro modos'})}).then(r => r.text())""" % PASSWORD)
                    if role == 'buceador':
                        screens = [p.format(booking=booking) for p in DIVER_PAGES]
                    else:
                        pg.goto(srv.base + '/#/admin'); pg.wait_for_selector('.cb-nav, .provider-tabs .tab', timeout=20000); pg.wait_for_timeout(800)
                        keys = pg.evaluate("[...document.querySelectorAll('.cb-nav[data-cbtab], .provider-tabs .tab[data-tab]')].map(b => b.dataset.cbtab || b.dataset.tab)")
                        screens = [f'#/admin?tab={k}' for k in dict.fromkeys(keys)]
                    seen = []
                    for route in screens:
                        errs.clear(); bad.clear()
                        pg.goto(srv.base + '/' + route); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(900)
                        txt = pg.inner_text('main') if pg.locator('main').count() else ''
                        broken = sorted(set(m.group(0) for m in BROKEN.finditer(txt)))
                        wide = pg.evaluate('document.documentElement.scrollWidth - innerWidth') if size == 'movil' else 0
                        ok = not errs and not bad and not broken and wide <= 1 and len(txt.strip()) > 40
                        seen.append({'pantalla': route, 'ok': ok, 'errores_js': errs[:3], 'peticiones_con_error': bad[:5], 'textos_rotos': broken, 'sale_por_el_lado_px': wide,
                                     'texto': len(txt.strip())})
                        check(f'{size} · {role} · {route}', ok, seen[-1])
                        if out and size == 'ordenador':
                            out.mkdir(parents=True, exist_ok=True)
                            pg.screenshot(path=str(out / f'{role}-{re.sub(r"[^a-z0-9]+", "-", route.lower()).strip("-")}.png'))
                    report[f'{size}/{role}'] = seen

                    # ------------------------------------------------------------ special attention
                    if size == 'ordenador' and role in ('centro', 'freelance'):
                        for tab, sel in (('bookings', '#cb-bookings .bk-row, #fl-bookings .bk-row'),
                                         ('planning', '#cb-planning .pl-cell.has-events, #fl-planning .pl-cell.has-events'),   # month view: days with dives
                                         ('agenda', '#fl-agenda .ag-item, #fl-agenda .dbk-card')):
                            if role == 'centro' and tab == 'agenda': continue          # the centre has «Planning / agenda» in one
                            pg.goto(f'{srv.base}/#/admin?tab={tab}'); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(900)
                            n = pg.locator(sel).count()
                            check(f'{role} · {tab}: se abre con sus datos', n > 0, n)
                    if role in ('centro', 'freelance'):
                        # 5.1: the time and number of each booking showed as «0…» (a style of the booking flow with the same
                        # name) and between 761 and 1180 px the state of the booking was hidden
                        pg.goto(f'{srv.base}/#/admin?tab=bookings'); pg.wait_for_selector('.bk-row'); pg.wait_for_timeout(700)
                        rows = pg.evaluate("""() => [...document.querySelectorAll('.bk-row')].slice(0, 5).map(r => { const t = r.querySelector('.bk-time strong'), n = r.querySelector('.bk-time span'), st = r.querySelector('.bk-state');
                            return [t.textContent, t.scrollWidth <= t.clientWidth + 1 && n.scrollWidth <= n.clientWidth + 1, !!st.offsetParent && st.getBoundingClientRect().width > 0]; })""")
                        check(f'{size} · {role} · reservas: la hora y el número se ven enteros y el estado se ve', rows and all(r[1] and r[2] for r in rows), rows)
                    if size == 'ordenador' and role == 'administración':
                        # 2.2 (button walk): «Subir» on the first template and «Bajar» on the last did nothing; now they are off
                        pg.goto(f'{srv.base}/#/admin?tab=svctemplates'); pg.wait_for_selector('.st-card .st-up'); pg.wait_for_timeout(500)
                        arrows = pg.evaluate("(()=>{const c=[...document.querySelectorAll('.st-grid .st-card')];return c.map((x,i)=>[x.querySelector('.st-up').disabled,x.querySelector('.st-down').disabled])})()")
                        check('administración · plantillas: ↑ apagada en la primera y ↓ en la última, las demás activas',
                              arrows and arrows[0][0] and arrows[-1][1] and not any(a[0] for a in arrows[1:]) and not any(a[1] for a in arrows[:-1]), arrows)
                        why = pg.evaluate("[document.querySelector('.st-grid .st-card .st-up').title, [...document.querySelectorAll('.st-grid .st-card .st-down')].pop().title]")
                        check('administración · plantillas: la flecha apagada dice por qué', why == ['Ya es la primera: no se puede subir más', 'Ya es la última: no se puede bajar más'], why)
                        pg.locator('.st-grid .st-card').nth(1).locator('.st-up').click(); pg.wait_for_timeout(800)
                        arrows = pg.evaluate("(()=>{const c=[...document.querySelectorAll('.st-grid .st-card')];return c.map((x,i)=>[x.querySelector('.st-up').disabled,x.querySelector('.st-down').disabled])})()")
                        check('administración · plantillas: después de subir una, siguen bien las flechas', arrows[0][0] and not arrows[1][0] and arrows[-1][1], arrows)
                        for tab, edit, save in (('destinations', '.edit-destination', '#destination-form button.btn-primary'),
                                                ('points', '.edit-point', '#point-form button.btn-primary'),
                                                ('svctemplates', '.st-edit', 'button[type=submit][form=stf]')):
                            errs.clear(); bad.clear()
                            pg.goto(f'{srv.base}/#/admin?tab={tab}'); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(900)
                            btn = pg.locator(edit).first
                            if not btn.count():
                                check(f'administración · {tab}: hay algo que editar', False, edit); continue
                            btn.click(); pg.wait_for_timeout(1200)
                            sub = pg.locator(save).first
                            if not sub.count():
                                check(f'administración · {tab}: el formulario tiene «Guardar»', False, save); continue
                            sub.click(); pg.wait_for_timeout(1500)
                            toast = pg.evaluate("document.querySelector('#toast')?.textContent||''")
                            h = pg.evaluate('location.hash')
                            check(f'administración · {tab}: abrir uno y guardarlo sin cambios vuelve a la lista con «Guardado»',
                                  ('Guardado' in toast or 'guardad' in toast.lower()) and h.startswith(f'#/admin?tab={tab}') and 'edit=' not in h and not errs and not bad,
                                  {'aviso': toast, 'dirección': h, 'errores': errs[:2], 'peticiones': bad[:3]})
                    ctx.close()
            browser.close()
    finally:
        srv.stop()
    if out: (out / 'modos.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    bad_rows = [n for n, ok in rows if not ok]
    print(f'\n{len(rows) - len(bad_rows)}/{len(rows)} comprobaciones correctas')
    return 1 if bad_rows else 0


if __name__ == '__main__':
    sys.exit(main())
