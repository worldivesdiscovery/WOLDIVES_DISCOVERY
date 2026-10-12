"""Fase 1B in a real browser: the mode label, the button and the state on every screen.

Screens: search results (centres and dive sites), centre page, dive-site page, booking page, «Mis reservas»,
booking detail, centre panel (services, planning, bookings / requests). Stripe is the local simulator.
Usage: python tests/e2e_booking_modes.py [--shots DIR]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]   # tests/navegador and tests (helpers)
from helpers import ServerTestCase, Server  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'


def chromium(p):
    exe = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    return p.chromium.launch(executable_path=exe) if Path(exe).exists() else p.chromium.launch()


def run(shots: Path | None):
    stripe = StripeMock()
    ServerTestCase.server = Server({'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': stripe.base, 'WOD_MAINTENANCE_SECONDS': '2'}).start()
    srv = ServerTestCase.server
    t = ServerTestCase('run')
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))

    try:
        admin = t.make_admin()
        center = t.make_center(admin, 'navegador')
        cid = center.user['center_id']
        srv.sql("UPDATE centers SET stripe_account_id='acct_e2e',stripe_charges_enabled=1,stripe_payouts_enabled=1,latitude=38.79,longitude=0.18 WHERE id=?", (cid,))
        pid = srv.sql('SELECT id FROM dive_points WHERE active=1 ORDER BY id LIMIT 1')[0]['id']
        center.post('/api/center-points/assign', {'dive_point_id': pid})
        pay = center.post('/api/provider-services', {'title': 'Buceo doble', 'price': 60, 'booking_mode': 'payment'}).json['id']
        req = center.post('/api/provider-services', {'title': 'Bautizo', 'price': 45, 'booking_mode': 'request', 'response_hours': 12}).json['id']
        for sid in (pay, req):
            center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-06-15', 'slot_time': '09:30', 'spots_total': 8, 'dive_point_ids': [pid]})
        t.make_diver('nav')
        base = srv.base
        with sync_playwright() as p:
            browser = chromium(p)
            for width in (1366, 390):
                ctx = browser.new_context(viewport={'width': width, 'height': 900}, locale='es-ES')
                page = ctx.new_page()
                errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.route('https://checkout.stripe.test/**', lambda route: route.fulfill(status=200, body='<h1>Stripe Checkout (simulado)</h1>', content_type='text/html'))

                def go(route, wait=500):
                    page.goto(base + '/' + route)
                    page.wait_for_load_state('networkidle')
                    page.wait_for_timeout(wait)

                def shot(name):
                    if shots:
                        shots.mkdir(parents=True, exist_ok=True)
                        page.screenshot(path=str(shots / f'{width}-{name}.png'), full_page=True)

                go('#/login'); page.fill('#login', 'diver_nav'); page.fill('#password', PW); page.click('#login-form button[type=submit]'); page.wait_for_timeout(800)
                # Search results: centres directory with the instant filter
                go('#/centros', 900)
                page.click('.cd-chip[data-flag="instant"]'); page.wait_for_timeout(900)
                txt = page.inner_text('body')
                check(f'{width} buscador centros: filtro y etiqueta', 'Confirmación inmediata' in txt and 'Centro navegador' in txt)
                shot('buscador-centros')
                go('#/puntos', 900)
                check(f'{width} buscador puntos: filtro', page.locator('.cd-chip[data-only="instant"]').count() == 1)
                # Centre page
                go(f'#/centro?id={cid}', 900)
                txt = page.inner_text('body')
                check(f'{width} ficha centro: etiquetas', 'Pago al reservar · confirmación inmediata' in txt and 'Bajo petición · el centro responde en 12 h' in txt)
                check(f'{width} ficha centro: botones', page.locator('a.cp-book', has_text='Reservar y pagar').count() == 1 and page.locator('a.cp-book', has_text='Enviar solicitud').count() == 1)
                shot('ficha-centro')
                # Dive site page
                go(f'#/punto?id={pid}', 900)
                check(f'{width} ficha punto: confirmación inmediata', 'Confirmación inmediata disponible' in page.inner_text('body'))
                shot('ficha-punto')
                # Booking page: request mode
                go(f'#/reservar?center={cid}&service={req}', 900)
                page.locator('.bk-time').first.click(); page.wait_for_timeout(600)
                txt = page.inner_text('#bk-summary')
                check(f'{width} reserva bajo petición: texto', 'No se cobra nada hasta que el centro acepte' in txt and 'Bajo petición' in txt)
                check(f'{width} reserva bajo petición: botón', 'Enviar solicitud' in page.inner_text('#bk-summary .bk-go'))
                shot('reserva-peticion')
                page.click('#bk-summary .bk-go'); page.wait_for_timeout(1200)
                check(f'{width} solicitud creada', '#/reserva?id=' in page.url)
                txt = page.inner_text('body')
                check(f'{width} mi reserva: estado y plazo', 'Solicitada' in txt and 'El centro responde como muy tarde' in txt)
                shot('mi-reserva-solicitada')
                # Booking page: payment mode
                go(f'#/reservar?center={cid}&service={pay}', 900)
                page.locator('.bk-time').first.click(); page.wait_for_timeout(600)
                btn = page.inner_text('#bk-summary .bk-go')
                check(f'{width} reserva pago: botón «Reservar y pagar»', btn.startswith('Reservar y pagar'), btn)
                check(f'{width} reserva pago: texto legal', 'Prestado por' in page.inner_text('#bk-summary') and 'impuestos incluidos' in page.inner_text('#bk-summary'))
                shot('reserva-pago')
                page.click('#bk-summary .bk-go'); page.wait_for_timeout(1500)
                check(f'{width} redirección a Stripe', 'checkout.stripe.test' in page.url, page.url)
                # Mis reservas
                go('#/area', 900)
                txt = page.inner_text('body')
                check(f'{width} mis reservas: estados', 'Solicitada' in txt and 'Pago en curso' in txt)
                shot('mis-reservas')
                check(f'{width} sin errores JS', not errors, errors)
                ctx.close()
            # Centre panel
            ctx = browser.new_context(viewport={'width': 1366, 'height': 900}, locale='es-ES')
            page = ctx.new_page()
            errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(base + '/#/login'); page.wait_for_selector('#login'); page.fill('#login', 'center_navegador'); page.fill('#password', PW); page.click('#login-form button[type=submit]'); page.wait_for_timeout(900)
            page.goto(base + '/#/admin?tab=services'); page.wait_for_load_state('networkidle'); page.wait_for_timeout(1200)
            txt = page.inner_text('body')
            check('panel servicios: etiquetas', 'Pago al reservar · confirmación inmediata' in txt and 'Bajo petición · el centro responde en 12 h' in txt)
            if shots: page.screenshot(path=str(shots / 'panel-servicios.png'), full_page=True)
            page.click('#new-center-service'); page.wait_for_timeout(700)
            check('formulario: dos modos', page.locator('input[name="svc-mode"]').count() == 2)
            check('formulario: ejemplo visible', 'El cliente verá' in page.inner_text('#center-service-modal'))
            if shots: page.screenshot(path=str(shots / 'panel-formulario.png'), full_page=False)
            page.keyboard.press('Escape'); page.wait_for_timeout(300)
            page.goto(base + '/#/admin?tab=bookings'); page.wait_for_load_state('networkidle'); page.wait_for_timeout(1000)
            page.click('.bk-view[data-view="pending"]'); page.wait_for_timeout(900)
            txt = page.inner_text('body')
            check('panel: solicitudes pendientes con plazo', 'Solicitudes pendientes' in txt and 'para responder' in txt)
            check('panel: la reserva en pago NO aparece como reserva', page.locator('.bk-row.bk-st-payment_in_progress').count() == 0)
            if shots: page.screenshot(path=str(shots / 'panel-solicitudes.png'), full_page=True)
            page.locator('.bk-act[data-act="confirmed"]').first.click(); page.wait_for_timeout(1200)
            st = [r['status'] for r in srv.sql("SELECT status FROM bookings WHERE service_id=? ORDER BY id", (req,))]
            check('panel: aceptar → aceptada pendiente de pago', 'accepted_pending_payment' in st, st)
            page.goto(base + '/#/admin?tab=services'); page.wait_for_timeout(300)
            page.goto(base + '/#/admin?tab=overview'); page.wait_for_load_state('networkidle'); page.wait_for_timeout(800)
            if shots: page.screenshot(path=str(shots / 'panel-resumen.png'), full_page=False)
            check('panel sin errores JS', not errors, errors)
            ctx.close()
            browser.close()
    finally:
        srv.stop()
        stripe.stop()
    return checks


if __name__ == '__main__':
    shots = Path(sys.argv[sys.argv.index('--shots') + 1]) if '--shots' in sys.argv else None
    results = run(shots)
    for name, ok, detail in results:
        print(('OK   ' if ok else 'FALLA') + ' ' + name + (f' · {detail}' if detail and not ok else ''))
    bad = [r for r in results if not r[1]]
    print(f'{len(results) - len(bad)}/{len(results)} comprobaciones correctas')
    sys.exit(1 if bad else 0)
