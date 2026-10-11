"""Fases 3 y 4 in a real browser: «Mis puntos», the old #/monedero link, «Cómo funcionan los puntos», advantages
of a centre with code validation, two-step verification in «Mi cuenta», the unsubscribe page and the commercial
email composer. Usage: python tests/e2e_points_email.py [--shots DIR]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from helpers import ServerTestCase, Server  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from wod import totp  # noqa: E402

PW = 'buceo-seguro-2026'


def chromium(p):
    exe = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    return p.chromium.launch(executable_path=exe) if Path(exe).exists() else p.chromium.launch()


def run(shots: Path | None):
    ServerTestCase.server = Server().start()
    srv = ServerTestCase.server
    t = ServerTestCase('run')
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))

    try:
        admin = t.make_admin()
        center = t.make_center(admin, 'ventajas')
        cid = center.user['center_id']
        oid = center.post('/api/provider/reward-offers', {'title': 'Botella de nitrox gratis', 'reward_type': 'gift', 'cost_points': 50, 'value_text': '1 botella de nitrox'}).json['id']
        diver = t.make_diver('e2epts')
        srv.sql("INSERT INTO points_ledger(user_id,points,kind,description,created_at) VALUES(?,120,'granted','Bienvenida',datetime('now'))", (diver.user['id'],))
        srv.sql("INSERT INTO wallet_transactions(user_id,amount,description,created_at) VALUES(?,5,'Saldo antiguo',datetime('now'))", (diver.user['id'],))
        base = srv.base
        with sync_playwright() as p:
            browser = chromium(p)

            def session(login, pw=PW, width=1366):
                ctx = browser.new_context(viewport={'width': width, 'height': 900}, locale='es-ES')
                page = ctx.new_page(); errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(base + '/#/login'); page.wait_for_selector('#login'); page.fill('#login', login); page.fill('#password', pw)
                page.click('#login-form button[type=submit]'); page.wait_for_timeout(900)
                return ctx, page, errors

            def go(page, route, wait=1000):
                page.goto(base + '/' + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)

            def shot(page, name, full=True):
                if shots:
                    shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'), full_page=full)

            # Diver (phone)
            ctx, page, errors = session('diver_e2epts', width=390)
            go(page, '#/monedero', 1200)
            check('#/monedero lleva a #/mis-puntos', '#/mis-puntos' in page.url, page.url)
            txt = page.inner_text('body')
            check('mis puntos: saldo en puntos', '120 puntos' in txt and 'no son dinero' in txt)
            check('mis puntos: historial del antiguo monedero', 'Historial del antiguo monedero' in txt)
            check('sin «Monedero» en el menú', 'Monedero' not in page.inner_text('header'))
            shot(page, 'mis-puntos')
            go(page, '#/recompensas', 1200)
            check('recompensas: ventaja del centro en puntos', 'Botella de nitrox gratis' in page.inner_text('body') and '50 puntos' in page.inner_text('body'))
            page.once('dialog', lambda d: d.accept())
            page.locator(f'.redeem-reward[data-id="{oid}"]').click(); page.wait_for_timeout(1200)
            code = srv.sql('SELECT code FROM reward_redemptions WHERE user_id=?', (diver.user['id'],))[0]['code']
            go(page, '#/mis-puntos', 1000)
            check('mis puntos: código para usar', code in page.inner_text('body'))
            page.locator('[data-qr]').first.click(); page.wait_for_timeout(600)
            check('mis puntos: QR del código', page.locator('.code-qr img').count() == 1)
            shot(page, 'codigo-qr', False)
            go(page, '#/como-funcionan-los-puntos', 800)
            check('página «Cómo funcionan los puntos»', 'Lo que no se puede hacer' in page.inner_text('body'))
            go(page, '#/cuenta', 1200)
            check('cuenta: verificación en dos pasos', page.locator('#acc-totp').count() == 1)
            check('cuenta: novedades y ofertas', page.locator('#acc-mkt').count() == 1)
            page.fill('#totp-pw', PW); page.click('#totp-start button'); page.wait_for_timeout(900)
            secret = srv.sql("SELECT totp_pending_secret FROM users WHERE username='diver_e2epts'")[0]['totp_pending_secret']
            check('cuenta: QR de activación', page.locator('.totp-qr svg').count() == 1)
            page.fill('#totp-code', totp.code_at(secret, totp.current_step())); page.click('#totp-confirm button'); page.wait_for_timeout(1000)
            check('cuenta: códigos de recuperación', page.locator('.totp-codes').count() == 1)
            shot(page, 'totp-activada')
            check('buceador sin errores JS', not errors, errors)
            ctx.close()
            # Centre validates the code
            ctx, page, errors = session('center_ventajas')
            go(page, '#/admin?tab=rewards', 1300)
            check('centro: ventajas y puntos', 'Validar un código' in page.inner_text('body') and 'Conceder puntos' in page.inner_text('body'))
            page.fill('#rw-code', code); page.click('#rw-validate button.btn-primary'); page.wait_for_timeout(800)
            check('centro: comprobar código', 'Botella de nitrox gratis' in page.inner_text('#rw-result'))
            shot(page, 'centro-validar')
            page.click('#rw-ok'); page.wait_for_timeout(1000)
            check('centro: código validado', srv.sql('SELECT status FROM reward_redemptions WHERE code=?', (code,))[0]['status'] == 'redeemed')
            check('centro sin errores JS', not errors, errors)
            ctx.close()
            # Unsubscribe page
            srv.sql("UPDATE users SET marketing_consent=1,marketing_token='tokenprueba1234567890' WHERE id=?", (diver.user['id'],))
            ctx = browser.new_context(viewport={'width': 390, 'height': 800}, locale='es-ES'); page = ctx.new_page(); errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            go(page, '#/baja?t=tokenprueba1234567890', 1200)
            check('baja en un clic', 'ya no recibirás' in page.inner_text('body') and srv.sql('SELECT marketing_consent FROM users WHERE id=?', (diver.user['id'],))[0]['marketing_consent'] == 0)
            shot(page, 'baja')
            ctx.close()
            # Admin: commercial email composer
            ctx, page, errors = session('admin', 'admin-seguro-2026')
            go(page, '#/admin?tab=emails', 1400)
            check('admin: comunicación comercial', page.locator('#mkt-form').count() == 1)
            shot(page, 'admin-correos')
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
