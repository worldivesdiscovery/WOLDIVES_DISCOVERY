"""Fase 6 in a real browser: plans page, the new tabs of the centre panel (plan, fiscal data, information requests,
statistics, tools, team, activity), a centre on the free listing with «Solicitar información», the team invitation
page, a reception member without owner tabs, and Administración → Planes / Funciones.
Usage: python tests/e2e_centers.py [--shots DIR]
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]   # tests/navegador and tests (helpers)
from helpers import ServerTestCase, Server  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
LABELS_JS = """() => [...document.querySelectorAll('label')].filter(l => !l.htmlFor && !l.querySelector('input,select,textarea')
                 && l.offsetParent !== null).map(l => l.textContent.trim().slice(0, 40))"""


from e2e_markers import chromium  # noqa: E402  (answers the administrator's reason, v50.47 B.9)


def run(shots: Path | None):
    ServerTestCase.server = Server().start()
    srv = ServerTestCase.server
    t = ServerTestCase('run')
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))

    try:
        admin = t.make_admin()
        center = t.make_center(admin, 'panel6')
        free = t.make_center(admin, 'gratis6', phone='+34 600 777 001')
        srv.sql("UPDATE centers SET plan_expires_at='2020-01-01' WHERE id=?", (free.user['center_id'],))
        sid = free.post('/api/provider-services', {'title': 'Bautizo de mar', 'price': 60}).json['id']
        center.post('/api/center/team/invite', {'email': 'recep6@example.org', 'member_role': 'reception'})
        mail = srv.sql("SELECT text FROM email_outbox WHERE template='team_invite' AND to_email='recep6@example.org'")[0]['text']
        token = re.search(r'equipo\?token=([A-Za-z0-9_\-]+)', mail).group(1)
        base = srv.base
        with sync_playwright() as p:
            browser = chromium(p)

            def session(login=None, pw=PW, width=1366):
                ctx = browser.new_context(viewport={'width': width, 'height': 900}, locale='es-ES')
                page = ctx.new_page(); errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                if login:
                    page.goto(base + '/#/login'); page.wait_for_selector('#login'); page.fill('#login', login); page.fill('#password', pw)
                    page.click('#login-form button[type=submit]'); page.wait_for_timeout(900)
                return ctx, page, errors

            def go(page, route, wait=1000):
                page.goto(base + '/' + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)

            def shot(page, name, full=True):
                if shots:
                    shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'), full_page=full)

            # Visitor on a phone: plans and a centre on the free listing
            ctx, page, errors = session(width=390)
            go(page, '#/planes', 1000)
            check('planes: tres planes', page.locator('.pl-card').count() == 3)
            check('planes: sin desbordamiento en móvil', page.evaluate('document.documentElement.scrollWidth') <= 392)
            shot(page, 'planes-movil')
            go(page, f"#/centro?id={free.user['center_id']}", 1500)
            body = page.inner_text('body')
            check('ficha gratuita: aviso sin reserva online', 'no tiene reserva online' in body and 'sin plazas' not in body.lower())
            check('ficha gratuita: sin enlaces de reserva', page.locator('a[href^="#/reservar"]').count() == 0)
            page.locator('button.cp-book').first.click(); page.wait_for_timeout(500)
            page.fill('#ir-name', 'Laura Visitante'); page.fill('#ir-email', 'laura@example.org'); page.fill('#ir-msg', 'Queremos hacer un bautizo dos personas en agosto.'); page.check('#ir-ok')
            shot(page, 'solicitar-informacion', False)
            page.click('#ir-send'); page.wait_for_timeout(900)
            check('solicitud de información enviada', srv.sql("SELECT 1 FROM info_requests WHERE email='laura@example.org'"))
            go(page, f"#/reservar?center={free.user['center_id']}&service={sid}", 1500)
            check('reserva directa: ofrece solicitar información', page.locator('#bk-info').count() == 1)
            check('visitante sin errores JS', not errors, errors)
            ctx.close()

            # Owner: new tabs
            ctx, page, errors = session('center_panel6')
            for tab, sel, name in (('plan', '.pl-card', 'mi plan'), ('fiscal', '#fi-form', 'datos fiscales'), ('requests', '.mm-module', 'solicitudes'),
                                   ('stats', '.acc-kpis', 'estadísticas'), ('tools', '.tl-row', 'herramientas'), ('team', '#tq-links-mount', 'equipo'), ('activity', '.mm-module', 'registro de actividad')):
                go(page, f'#/admin?tab={tab}', 1400)
                check(f'centro: pestaña {name}', page.locator(sel).count() >= 1)
                unl = page.evaluate(LABELS_JS)
                check(f'centro: etiquetas enlazadas en {name}', not unl, unl)
                if tab in ('plan', 'tools', 'fiscal'): shot(page, f'centro-{tab}')
            go(page, '#/admin?tab=fiscal', 1300)
            page.select_option('#fi-type', 'individual'); page.fill('#fi-legal', 'Ana Pérez'); page.fill('#fi-tax', '12345678Z'); page.fill('#fi-country', 'es')
            page.fill('#fi-birth', '1985-04-02'); page.fill('#fi-addr', 'Calle Mar 1'); page.fill('#fi-exp', '2031-01-01'); page.click('#fi-form button[type=submit]'); page.wait_for_timeout(900)
            check('centro: datos fiscales guardados', srv.sql("SELECT tax_id_country FROM centers WHERE id=?", (center.user['center_id'],))[0]['tax_id_country'] == 'ES')
            go(page, '#/admin?tab=tools', 1300)
            page.click('#tl-ical-new'); page.wait_for_timeout(900)
            check('centro: dirección iCal generada', '/ical/' in page.locator('#tl-ical').input_value())
            check('centro sin errores JS', not errors, errors)
            ctx.close()

            # Team invitation and reception panel
            ctx, page, errors = session()
            go(page, f'#/equipo?token={token}', 1000)
            page.fill('#tj-name', 'Rosa Recepción'); page.fill('#tj-user', 'recep6'); page.fill('#tj-pass', PW); page.check('#tj-terms')
            page.click('#tj-form button[type=submit]'); page.wait_for_timeout(1800)
            go(page, '#/admin', 1600)
            check('recepción: panel del centro sin pestañas de propietario', page.locator('.cb-nav[data-cbtab="bookings"]').count() == 1 and page.locator('.cb-nav[data-cbtab="plan"]').count() == 0)
            check('recepción sin errores JS', not errors, errors)
            ctx.close()

            # Admin
            ctx, page, errors = session('admin', 'admin-seguro-2026')
            go(page, '#/admin?tab=plans', 1600)
            check('admin: planes editables', page.locator('.ap-plan').count() == 3 and page.locator('.ap-manage').count() >= 2)
            shot(page, 'admin-planes')
            go(page, '#/admin?tab=features', 1200)
            check('admin: funciones y modo piloto', page.locator('#af-form [data-k]').count() == 6 and page.locator('#af-pilot').count() == 1)
            unl = page.evaluate(LABELS_JS)
            check('admin funciones: etiquetas enlazadas', not unl, unl)
            go(page, '#/admin?tab=ops', 1500)
            check('admin: operación (salud, copias, aviso)', page.locator('#ops-banner').count() == 1 and page.locator('.acc-kpi').count() >= 5)
            page.fill('#ops-text', 'Mantenimiento programado el domingo de 7:00 a 8:00'); page.click('#ops-banner button[type=submit]'); page.wait_for_timeout(900)
            go(page, '#/', 1500)
            check('aviso de mantenimiento visible en la web', 'Mantenimiento programado' in page.inner_text('#site-banner'))
            shot(page, 'aviso-mantenimiento', False)
            check('admin sin errores JS', not errors, errors)
            ctx.close()
            browser.close()
    finally:
        srv.stop()
    return checks


if __name__ == '__main__':
    shots = Path(sys.argv[sys.argv.index('--shots') + 1]) if '--shots' in sys.argv else None
    results = run(shots)
    for name, ok, detail in results:
        print(('OK   ' if ok else 'FALLA') + ' ' + name + (f' · {detail}' if detail and not ok else ''))
    bad = [r for r in results if not r[1]]
    print(f'{len(results) - len(bad)}/{len(results)} comprobaciones correctas')
    sys.exit(1 if bad else 0)
