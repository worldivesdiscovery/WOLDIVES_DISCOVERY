"""Encargo 2, punto 7 in a real browser (computer and phone): sign-in with only email and password, the forgotten
password and the second step on separate screens, sign-up with the three account cards, changing the type halfway,
the email notice in the account, and both screens in the 9 languages with every text translated.
Usage: python tests/e2e_auth.py [--shots DIR]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]   # tests/navegador and tests (helpers)
from helpers import ServerTestCase, Server, ROOT  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

sys.path.insert(0, str(ROOT / 'app'))
from wod import totp  # noqa: E402

PW = 'buceo-seguro-2026'
LANGS = ['es', 'en', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'zh']


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
        dos = t.make_diver('dospasosweb')
        secret = dos.post('/api/account/totp/setup', {'password': PW}).json['secret']     # (in the database it is encrypted)
        dos.post('/api/account/totp/enable', {'code': totp.code_at(secret, totp.current_step())})
        cid = srv.sql('SELECT id FROM certifications WHERE active=1 ORDER BY id LIMIT 1')[0]['id']
        with sync_playwright() as p:
            browser = chromium(p)

            def session(width, lang='es'):
                ctx = browser.new_context(viewport={'width': width, 'height': 900 if width > 500 else 844}, locale='es-ES')
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                page = ctx.new_page(); errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                return ctx, page, errors

            def go(page, route, wait=900, lang=None):
                page.goto(srv.base + ('/?lang=' + lang if lang else '/') + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)

            def shot(page, name):
                if shots:
                    shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'), full_page=True)

            for dev, width in (('ordenador', 1366), ('movil', 390)):
                ctx, page, errors = session(width)
                # Sign-in: only email, password, «Mantener la sesión iniciada» (v50.58) and «Entrar»; the link to the forgotten password below
                go(page, '#/login')
                inputs = page.evaluate("[...document.querySelectorAll('#login-form input')].filter(i=>i.offsetParent!==null).map(i=>i.id)")
                check(f'{dev}: inicio de sesión solo con email y contraseña', inputs == ['login', 'password', 'remember'], inputs)
                below = page.evaluate("(()=>{const b=document.querySelector('#login-form button[type=submit]').getBoundingClientRect(), a=document.querySelector('#login-form a[href=\"#/recuperar\"]').getBoundingClientRect(); return a.top>b.bottom})()")
                check(f'{dev}: enlace «¿Has olvidado tu contraseña?» debajo de Entrar', below)
                visual = page.locator('.auth-visual').is_visible()
                check(f'{dev}: foto a la izquierda en ordenador y solo el formulario en el móvil', visual if dev == 'ordenador' else not visual)
                check(f'{dev}: sin desbordamiento horizontal', page.evaluate('document.documentElement.scrollWidth') <= width + 2)
                shot(page, f'despues-login-{dev}')
                page.click('#login-form a[href="#/recuperar"]'); page.wait_for_timeout(700)
                check(f'{dev}: contraseña olvidada en otra pantalla', page.evaluate('location.hash') == '#/recuperar' and page.locator('#login-form').count() == 0)
                # Second step on its own screen
                go(page, '#/login')
                page.fill('#login', 'dospasosweb@diver.example.org'); page.fill('#password', PW); page.click('#login-form button[type=submit]'); page.wait_for_timeout(900)
                check(f'{dev}: verificación en dos pasos en pantalla aparte', page.evaluate('location.hash') == '#/verificacion' and page.locator('#totp').is_visible())
                shot(page, f'despues-verificacion-{dev}')
                srv.sql("UPDATE users SET totp_last_step=NULL WHERE username='diver_dospasosweb'")
                page.fill('#totp', totp.code_at(secret, totp.current_step())); page.click('#totp-form button[type=submit]'); page.wait_for_timeout(1200)
                me = page.evaluate("fetch('/api/me').then(r=>r.json())")
                check(f'{dev}: sesión iniciada tras el código', me.get('authenticated') and me['user']['username'] == 'diver_dospasosweb')
                page.evaluate("fetch('/api/auth/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})"); page.wait_for_timeout(400)
                ctx.close()

                # Sign-up: three cards, change of type halfway, only the fields of each type
                ctx, page, errors = session(width)
                go(page, '#/registro')
                check(f'{dev}: registro con tres tarjetas de tipo de cuenta', page.locator('.reg-type').count() == 3)
                shot(page, f'despues-registro-{dev}')
                page.click('.reg-type[data-type="center"]'); page.wait_for_timeout(700)
                ids = page.evaluate("[...document.querySelectorAll('#register-form input,#register-form select')].filter(i=>i.offsetParent!==null&&i.type!=='checkbox').map(i=>i.id)")
                check(f'{dev}: campos del centro', ids == ['r-center-name', 'r-name', 'r-email', 'r-phone', 'r-country', 'r-city', 'r-pass'], ids)
                check(f'{dev}: mensaje «Revisaremos tu centro»', 'Revisaremos tu centro y te avisaremos por email' in page.inner_text('#register-form'))
                shot(page, f'despues-registro-centro-{dev}')
                page.fill('#r-name', 'Persona a medias')
                page.click('#r-change'); page.wait_for_timeout(600)
                check(f'{dev}: «Cambiar» vuelve a las tarjetas', page.locator('.reg-type').count() == 3)
                page.click('.reg-type[data-type="recreational"]'); page.wait_for_timeout(600)
                ids = page.evaluate("[...document.querySelectorAll('#register-form input,#register-form select')].filter(i=>i.offsetParent!==null&&i.type!=='checkbox').map(i=>i.id)")
                check(f'{dev}: buceador: nombre, email y contraseña', ids == ['r-name', 'r-email', 'r-pass'], ids)
                page.fill('#r-name', f'Nadia {dev}'); page.fill('#r-email', f'nadia.{dev}@example.org'); page.fill('#r-pass', PW); page.check('#r-terms')
                page.click('#register-form button[type=submit]'); page.wait_for_timeout(1400)
                u = srv.sql('SELECT role, username FROM users WHERE email=?', (f'nadia.{dev}@example.org',))
                check(f'{dev}: alta de buceador', u and u[0]['role'] == 'recreational')
                go(page, '#/cuenta', 1200)
                check(f'{dev}: aviso discreto de email sin verificar', page.locator('.acc-verify').is_visible())
                shot(page, f'despues-cuenta-sin-verificar-{dev}')
                page.locator('[data-verify-resend]').click(); page.wait_for_timeout(700)
                check(f'{dev}: reenviar el enlace', len(srv.sql("SELECT 1 FROM email_outbox WHERE template='verify_email' AND to_email=?", (f'nadia.{dev}@example.org',))) == 2)
                page.evaluate("fetch('/api/auth/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})")
                ctx.close()

                ctx, page, errors2 = session(width)
                go(page, '#/registro?tipo=center')
                page.fill('#r-center-name', f'Centro {dev}'); page.fill('#r-name', 'Gema Gerente'); page.fill('#r-email', f'gema.{dev}@centro.example.org'); page.fill('#r-phone', '+34 600 222 333')
                page.fill('#r-country', 'España'); page.fill('#r-city', 'Altea'); page.fill('#r-pass', PW); page.check('#r-terms')
                page.click('#register-form button[type=submit]'); page.wait_for_timeout(1400)
                cl = srv.sql('SELECT status, requested_center_name FROM center_claims WHERE email=?', (f'gema.{dev}@centro.example.org',))
                check(f'{dev}: alta de centro pendiente de aprobación', cl and cl[0]['status'] == 'pending' and cl[0]['requested_center_name'] == f'Centro {dev}')
                page.evaluate("fetch('/api/auth/logout',{method:'POST',headers:{'Content-Type':'application/json'},body:'{}'})")
                ctx.close()

                ctx, page, errors3 = session(width)
                go(page, '#/registro?tipo=freelance')
                ids = page.evaluate("[...document.querySelectorAll('#register-form input,#register-form select')].filter(i=>i.offsetParent!==null&&i.type!=='checkbox').map(i=>i.id)")
                check(f'{dev}: campos del profesional', ids == ['r-name', 'r-email', 'r-phone', 'r-cert', 'r-pass'], ids)
                page.fill('#r-name', 'Pablo Guía'); page.fill('#r-email', f'pablo.{dev}@pro.example.org'); page.fill('#r-phone', '+34 611 333 444')
                page.select_option('#r-cert', str(cid)); page.fill('#r-pass', PW); page.check('#r-terms')
                shot(page, f'despues-registro-profesional-{dev}')
                page.click('#register-form button[type=submit]'); page.wait_for_timeout(1400)
                cl = srv.sql('SELECT status FROM center_claims WHERE email=?', (f'pablo.{dev}@pro.example.org',))
                check(f'{dev}: alta de profesional pendiente de aprobación', cl and cl[0]['status'] == 'pending')
                check(f'{dev}: sin errores JS', not (errors + errors2 + errors3), errors + errors2 + errors3)
                ctx.close()

            # The 9 languages: every text of both screens translated, no overflow on the phone
            ctx = browser.new_context(viewport={'width': 390, 'height': 844})
            ctx.add_init_script("try{localStorage.setItem('wd-i18n-debug','1');localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
            page = ctx.new_page()
            for lang in LANGS:
                misses = set(); over = False
                for route in ('#/login', '#/registro', '#/registro?tipo=recreational', '#/registro?tipo=center', '#/registro?tipo=freelance', '#/recuperar'):
                    go(page, route, 700, lang)
                    misses |= set(page.evaluate('window.__wdI18nMisses?[...window.__wdI18nMisses]:[]'))
                    over = over or page.evaluate('document.documentElement.scrollWidth') > 392
                    if lang in ('de', 'pl', 'zh') and route == '#/registro?tipo=center': shot(page, f'idioma-{lang}-registro-centro-movil')
                check(f'idioma {lang}: todo traducido', lang == 'es' or not misses, sorted(misses)[:5])
                check(f'idioma {lang}: sin desbordamiento en el móvil', not over)
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
