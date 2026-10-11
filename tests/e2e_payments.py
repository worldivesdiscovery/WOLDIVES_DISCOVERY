"""Fase 2 in a real browser: «Cobros y pagos» of a centre and of a freelance, the service form with deposit and
cancellation policy, the booking page with a deposit, the booking with «Devolver», the freelance panel, the
administrator's payments and the sponsorship form. Stripe is the local simulator.
Usage: python tests/e2e_payments.py [--shots DIR]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from helpers import ServerTestCase, Server, Client  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
CONNECT = 'whsec_connect_e2e'


def chromium(p):
    exe = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    return p.chromium.launch(executable_path=exe) if Path(exe).exists() else p.chromium.launch()


def run(shots: Path | None):
    stripe = StripeMock()
    ServerTestCase.server = Server({'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': stripe.base, 'STRIPE_CONNECT_WEBHOOK_SECRET': CONNECT, 'STRIPE_WEBHOOK_SECRET': 'whsec_p'}).start()
    srv = ServerTestCase.server
    t = ServerTestCase('run')
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))

    try:
        admin = t.make_admin()
        center = t.make_center(admin, 'cobros')
        cid = center.user['center_id']
        srv.sql("UPDATE centers SET stripe_account_id='acct_e2e',stripe_charges_enabled=1,stripe_payouts_enabled=1,legal_name='Cobros Buceo S.L.',tax_id='B22222222' WHERE id=?", (cid,))
        pro = t.make_freelance(admin, 'guia')
        srv.sql("UPDATE users SET stripe_account_id='acct_pro',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (pro.user['id'],))
        sid = center.post('/api/provider-services', {'title': 'Buceo doble', 'price': 60, 'booking_mode': 'payment', 'deposit_type': 'percent', 'deposit_value': 25,
                                                     'cancel_free_hours': 48, 'cancel_refund_pct': 50}).json['id']
        center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-06-15', 'slot_time': '09:30', 'spots_total': 8})
        psid = pro.post('/api/provider-services', {'title': 'Guía privado', 'price': 90, 'booking_mode': 'payment'}).json['id']
        pro.post('/api/provider-services/slot', {'service_id': psid, 'slot_date': '2031-06-16', 'slot_time': '10:00', 'spots_total': 4})
        diver = t.make_diver('e2epay')
        # A paid booking (deposit) to see «Devolver»
        slot = srv.sql('SELECT id FROM service_slots WHERE service_id=?', (sid,))[0]['id']
        bid = diver.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': 2}).json['id']
        sess = stripe.last_session(); stripe.pay(sess['id'])
        payload, sig = StripeMock.signed({'id': 'evt_e2e', 'type': 'checkout.session.completed', 'account': 'acct_e2e',
                                          'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}, CONNECT)
        Client(srv, origin=None).request('POST', '/api/payments/webhook/connect', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
        base = srv.base
        with sync_playwright() as p:
            browser = chromium(p)

            def session(login, width=1366):
                ctx = browser.new_context(viewport={'width': width, 'height': 900}, locale='es-ES')
                page = ctx.new_page(); errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.route('https://checkout.stripe.test/**', lambda route: route.fulfill(status=200, body='<h1>Stripe Checkout (simulado)</h1>', content_type='text/html'))
                page.goto(base + '/#/login'); page.wait_for_selector('#login'); page.fill('#login', login)
                page.fill('#password', 'admin-seguro-2026' if login == 'admin' else PW); page.click('#login-form button[type=submit]'); page.wait_for_timeout(900)
                return ctx, page, errors

            def go(page, route, wait=1000):
                page.goto(base + '/' + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)

            def shot(page, name, full=True):
                if shots:
                    shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'), full_page=full)

            # Centre: «Cobros y pagos»
            ctx, page, errors = session('center_cobros')
            go(page, '#/admin?tab=payments', 1400)
            txt = page.inner_text('body')
            check('centro · cobros: sin comisión y cargo directo', 'no cobra comisión' in txt and 'directamente a tu cuenta de Stripe' in txt)
            check('centro · cobros: ingresos por moneda', 'Ingresos (EUR)' in txt)
            check('centro · cobros: datos del prestador', page.locator('#pp-legal').input_value() == 'Cobros Buceo S.L.')
            check('centro · cobros: política con horas y %', page.locator('#cxp-h').count() == 1 and page.locator('#cxp-p').count() == 1)
            shot(page, 'centro-cobros')
            page.fill('#cxp-h', '24'); page.fill('#cxp-p', '30'); page.click('#cxp-save'); page.wait_for_timeout(700)
            check('centro · política guardada', srv.sql('SELECT cancel_free_hours,cancel_refund_pct FROM centers WHERE id=?', (cid,))[0] == {'cancel_free_hours': 24, 'cancel_refund_pct': 30})
            # Service form
            go(page, '#/admin?tab=services', 1200)
            page.click('#new-center-service'); page.wait_for_timeout(700)
            check('formulario: señal y política', page.locator('#svc-dep-type').count() == 1 and page.locator('#svc-pol-own').count() == 1)
            page.select_option('#svc-dep-type', 'percent'); page.click('label:has(#svc-pol-own)'); page.wait_for_timeout(200)
            check('formulario: texto de la política', 'Cancelación gratuita' in page.inner_text('#svc-pol-text'))
            shot(page, 'formulario-servicio', False)
            page.keyboard.press('Escape'); page.wait_for_timeout(300)
            # Booking detail with «Devolver»
            go(page, f'#/reserva?id={bid}', 1200)
            check('ficha · señal pagada visible', 'Señal pagada' in page.inner_text('body'))
            check('ficha · botón Devolver', page.locator('#center-refund').count() == 1)
            page.click('#center-refund'); page.wait_for_timeout(700)
            shot(page, 'devolver', False)
            page.fill('#rf-amount', '10'); page.click('#rf-ok'); page.wait_for_timeout(1200)
            b = srv.sql('SELECT refunded_total,payment_status,status FROM bookings WHERE id=?', (bid,))[0]
            check('devolución parcial desde la ficha', b == {'refunded_total': 10, 'payment_status': 'partially_refunded', 'status': 'confirmed'}, b)
            check('centro sin errores JS', not errors, errors)
            ctx.close()
            # Diver: booking page with deposit, and booking detail
            ctx, page, errors = session('diver_e2epay', 390)
            go(page, f'#/reservar?center={cid}&service={sid}', 1100)
            page.locator('.bk-time').first.click(); page.wait_for_timeout(800)
            txt = page.inner_text('#bk-summary')
            check('reserva · CTA de señal', 'pagar la señal' in page.inner_text('#bk-summary .bk-go'))
            check('reserva · resto en el centro', 'Resto a pagar en el centro' in txt)
            check('reserva · política del servicio', '48 horas' in txt or '2 días' in txt)
            check('reserva · impuestos incluidos', 'impuestos incluidos' in txt)
            shot(page, 'reserva-senal')
            go(page, f'#/reserva?id={bid}', 1000)
            txt = page.inner_text('body')
            check('buceador · ficha con señal y devolución', 'Señal pagada' in txt and 'Devuelto' in txt)
            shot(page, 'buceador-reserva')
            # Freelance services on the professional page
            go(page, f'#/profesional?id={pro.user["id"]}', 1000)
            check('ficha del profesional · servicios reservables', page.locator('a.cp-book').count() == 1)
            page.click('a.cp-book'); page.wait_for_timeout(1200)
            page.locator('.bk-time').first.click(); page.wait_for_timeout(700)
            page.click('#bk-summary .bk-go'); page.wait_for_timeout(1500)
            check('reserva a freelance → Stripe en su cuenta', 'checkout.stripe.test' in page.url and [c for c in stripe.calls if c['path'] == '/v1/checkout/sessions'][-1]['account'] == 'acct_pro', page.url)
            check('buceador sin errores JS', not errors, errors)
            ctx.close()
            # Freelance panel
            ctx, page, errors = session('pro_guia')
            go(page, '#/admin?tab=payments', 1300)
            check('freelance · cobros y pagos', 'Tus cobros' in page.inner_text('body'))
            shot(page, 'freelance-cobros')
            go(page, '#/admin?tab=bookings', 1300)
            check('freelance · pestaña de reservas', page.locator('.bk-module').count() == 1)
            check('freelance sin errores JS', not errors, errors)
            ctx.close()
            # Administrator
            ctx, page, errors = session('admin')
            go(page, '#/admin?tab=adminpay', 1400)
            txt = page.inner_text('body')
            check('admin · sin KPI de comisión', 'comisión WORLDIVES' not in txt and 'Ingresos de los prestadores' in txt)
            check('admin · webhook de Connect', 'Webhook de Connect' in txt)
            shot(page, 'admin-pagos')
            go(page, '#/admin?tab=promos', 1200)
            if page.locator('.pr-new[data-kind="offer"]').count():
                page.click('.pr-new[data-kind="offer"]'); page.wait_for_timeout(600)
                check('patrocinio · etiqueta fija y registro', page.locator('#pr-label').count() == 0 and page.locator('#pr-sponsor').count() == 1)
                shot(page, 'patrocinio', False)
            check('admin sin errores JS', not errors, errors)
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
