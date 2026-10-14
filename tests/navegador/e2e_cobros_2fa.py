#!/usr/bin/env python3
"""v50.52 · ASVS 5.0 V6.3.3 en un navegador real (Chromium): lo que ve un centro con cobros online sin verificación en
dos pasos, en el ordenador y en la app profesional del móvil.

- durante los 14 días: aviso arriba del panel con la fecha, y «Obligatoria» en «Mi cuenta»;
- pasado el plazo: el panel solo enseña «Activa la verificación en dos pasos»; se activa desde «Mi cuenta» (QR, código y
  códigos de recuperación) y el panel vuelve; ya no hay botón «Desactivar»;
- un centro sin cobros que pulsa «Activar los cobros online» sin verificación: se le pide antes y se le lleva a «Mi cuenta»;
- la app profesional del móvil: la misma pantalla en lugar de errores.

    python3 tests/navegador/e2e_cobros_2fa.py [carpeta-de-capturas]
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import ServerTestCase, Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from wod import totp as wtotp  # noqa: E402

PW = 'buceo-seguro-2026'
PAST = '2026-01-01T00:00:00+00:00'
UA = 'Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36 WorldivesApp/1.0 pruebas'


def run(shots: Path | None):
    ServerTestCase.server = Server({'WOD_PAYMENTS_TOTP_REQUIRED': '1'}).start(); srv = ServerTestCase.server
    t = ServerTestCase('run')
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))

    try:
        admin = t.make_admin()
        cobra = t.make_center(admin, 'cobraweb', phone='+34 600 530 001')
        srv.sql("UPDATE centers SET stripe_account_id='acct_web' WHERE id=?", (cobra.user['center_id'],))
        nuevo = t.make_center(admin, 'nuevoweb', phone='+34 600 530 002')
        movil = t.make_center(admin, 'movilweb', phone='+34 600 530 003')
        srv.sql("UPDATE centers SET stripe_account_id='acct_movil' WHERE id=?", (movil.user['center_id'],))
        srv.sql('UPDATE users SET totp_deadline=? WHERE id=?', (PAST, movil.user['id']))
        base = srv.base
        with sync_playwright() as p:
            browser = chromium(p)

            def session(width=1366, mobile=False):
                kw = {'viewport': {'width': width, 'height': 900 if width > 500 else 844}, 'locale': 'es-ES'}
                if mobile: kw.update(is_mobile=True, has_touch=True, user_agent=UA)
                ctx = browser.new_context(**kw)
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                page = ctx.new_page(); errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                return ctx, page, errors

            def go(page, route, wait=1400):
                page.goto(base + '/' + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)

            def login(page, user):
                go(page, '#/login', 600); page.fill('#login', user); page.fill('#password', PW)
                page.click('#login-form button[type=submit]'); page.wait_for_timeout(1500)

            def shot(page, name):
                if shots:
                    shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'))

            # ---- 1. Within the 14 days: notice on the panel and «Obligatoria» in «Mi cuenta»
            ctx, page, errors = session()
            login(page, 'center_cobraweb'); go(page, '#/admin', 2200)
            note = page.locator('#totp-grace')
            check('plazo: aviso arriba del panel', note.count() == 1, page.inner_text('#app')[:200])
            check('plazo: el aviso dice hasta cuándo (con el año)', note.count() == 1 and str(time.gmtime().tm_year) in note.inner_text())
            check('plazo: el panel funciona (sin pantalla de bloqueo)', 'Activa la verificación en dos pasos' not in page.inner_text('h2') if page.locator('h2').count() else True)
            shot(page, 'ordenador-plazo-aviso')
            go(page, '#/cuenta?seguridad=1', 1600)
            card = page.inner_text('#acc-totp')
            check('mi cuenta: «Obligatoria» y por qué', 'Obligatoria' in card and 'cobros online' in card, card[:300])
            check('mi cuenta: «Tienes hasta el …»', 'Tienes hasta el' in card, card[:300])

            # ---- 2. The 14 days are over: only «Mi cuenta»
            srv.sql('UPDATE users SET totp_deadline=? WHERE id=?', (PAST, cobra.user['id']))
            go(page, '#/admin', 1800)
            txt = page.inner_text('#app')
            check('bloqueado: «Activa la verificación en dos pasos»', 'Activa la verificación en dos pasos' in txt and 'cobros online activados' in txt, txt[:300])
            check('bloqueado: botón «Activarla ahora»', page.locator('a[href="#/cuenta?seguridad=1"]').count() >= 1)
            shot(page, 'ordenador-bloqueado')
            page.click('a[href="#/cuenta?seguridad=1"]'); page.wait_for_timeout(1500)
            page.fill('#totp-pw', PW); page.click('#totp-start button'); page.wait_for_timeout(1200)
            check('activar: código QR en pantalla', page.locator('.totp-qr svg').count() == 1)
            secret = page.inner_text('.totp-steps code').replace(' ', '')
            page.fill('#totp-code', wtotp.code_at(secret, int(time.time()) // 30)); page.click('#totp-confirm button'); page.wait_for_timeout(1500)
            check('activar: códigos de recuperación', page.locator('.totp-codes').count() == 1)
            page.click('#totp-done'); page.wait_for_timeout(1500)
            card = page.inner_text('#acc-totp')
            check('activada: sin botón «Desactivar» (tiene cobros)', page.locator('#totp-off').count() == 0 and 'Activada' in card, card[:200])
            go(page, '#/admin', 2200)
            check('activada: el panel vuelve', page.locator('#totp-grace').count() == 0 and 'Activa la verificación en dos pasos' not in page.inner_text('#app')[:400])
            check('centro sin errores JS', not errors, errors[:3])
            ctx.close()

            # ---- 3. A centre without payments wants to connect Stripe without the verification
            ctx, page, errors = session()
            login(page, 'center_nuevoweb'); go(page, '#/admin', 2000)
            check('sin cobros: sin aviso de plazo', page.locator('#totp-grace').count() == 0)
            go(page, '#/admin?tab=payments', 2000)
            btn = page.locator('#stripe-onboard')
            if btn.count():
                btn.click(); page.wait_for_timeout(700)
                modal = page.inner_text('#wd-confirm') if page.locator('#wd-confirm').count() else ''
                check('stripe: pide antes la verificación en dos pasos', 'verificación en dos pasos' in modal, modal[:200])
                shot(page, 'ordenador-stripe-pide-2fa')
                page.click('#wd-confirm-ok'); page.wait_for_timeout(1200)
                check('stripe: lleva a «Mi cuenta»', 'seguridad=1' in page.url, page.url)
            else:
                check('stripe: botón «Activar los cobros online»', False, page.inner_text('#app')[:300])
            check('sin errores JS (sin cobros)', not errors, errors[:3])
            ctx.close()

            # ---- 4. The professional app on the phone
            ctx, page, errors = session(390, mobile=True)
            login(page, 'center_movilweb'); go(page, '#/', 2000)
            txt = page.inner_text('#app')
            check('app pro: pantalla «Activa la verificación en dos pasos»', 'Activa la verificación en dos pasos' in txt, txt[:300])
            check('app pro: botón a «Mi cuenta»', page.locator('a[href="#/cuenta?seguridad=1"]').count() >= 1)
            check('app pro: sin desbordamiento', page.evaluate('document.documentElement.scrollWidth') <= 392)
            shot(page, 'movil-app-pro-bloqueado')
            check('app pro sin errores JS', not errors, errors[:3])
            ctx.close()
            browser.close()
    finally:
        srv.stop()
    return checks


if __name__ == '__main__':
    results = run(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    for name, ok, detail in results:
        print(('OK    ' if ok else 'FALLO ') + name + ('' if ok else f'  → {detail}'))
    bad = [r for r in results if not r[1]]
    print(f'{len(results) - len(bad)}/{len(results)} comprobaciones correctas')
    sys.exit(1 if bad else 0)
