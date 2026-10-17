#!/usr/bin/env python3
"""v50.58 · Equipo del centro enlazado por QR (encargo unificado del 16/10/2026, bloque 1), en el navegador, sobre la demo.

Las comprobaciones del encargo que se ven en pantalla (las demás están en tests/test_v50_58_equipo_qr.py, en el servidor,
porque dependen del reloj o de muchos casos: QR de hace 2 minutos, enlace «Por días» que termina solo, 16.ª persona…):

  1  enlazar con el QR (abierto con la cámara del móvil: /p/…) y con el código corto, en ordenador y en móvil; la persona
     acepta y aparece en el equipo con su perfil; «Enlazar persona» también dentro de cada perfil (parte 2.1);
  2  un QR ya usado no vuelve a servir;
  3  invitación por correo a alguien sin cuenta: crea la cuenta y queda enlazado;
  4  enlace «Por días»: sale «Empieza el …» hasta su primer día;
  5  dos centros: el selector de perfil y «Mi agenda» con un color por centro; al cambiar de centro no se ve nada del otro;
  6  «Ocupado» en el manifiesto, sin decir por qué;
  7  permisos: un instructor no ve «Cobros» y la dirección le responde que no existe;
  8  desenlazar: el acceso se quita al momento, con la sesión abierta;
  9  registro de actividad con el nombre y el perfil de cada persona;
  10 planes: con Ficha gratuita «Enlazar persona» sale bloqueado; con Motor de reservas solo Recepción;
  12 «Compartir para enlazar»: el enlace sirve una vez;
  13 la demo trae a freelance.prueba enlazado a los dos centros.
  Además: «Mantener la sesión iniciada» y «Cerrar sesión» siempre a la vista.

    python3 tests/navegador/e2e_v50_58_equipo_qr.py [carpeta-de-capturas]

Usa las cuentas de la demo: no va en el zip de producción (scripts/generar_zips.py)."""
from __future__ import annotations

import re
import shutil
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
DESK = {'viewport': {'width': 1366, 'height': 900}, 'locale': 'es-ES'}
PHONE = {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2, 'locale': 'es-ES'}


def run(out: Path | None):
    rows = []

    def check(name, ok, detail=''):
        rows.append((name, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + name + ('' if ok else f'  → {str(detail)[:400]}'), flush=True)

    tmp = Path(tempfile.mkdtemp(prefix='wod-equipo-qr-'))
    db = tmp / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(db)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=db).start()
    errors = []
    try:
        with sync_playwright() as pw:
            browser = chromium(pw)

            def ctx(opts=DESK):
                c = browser.new_context(**opts)
                c.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg = c.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
                return c, pg

            def login(pg, user, keep=False):
                pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login-form')
                pg.fill('#login', user); pg.fill('#password', PASSWORD)
                if keep: pg.check('#remember')
                pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1500)

            def shot(pg, name, full=False):
                if out: out.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(out / f'{name}.png'), full_page=full)

            def get(pg, url):
                """A request of the signed-in page (its cookie); the body is read so the page does not stay «busy»."""
                return pg.evaluate("u => fetch(u).then(r => r.text().then(t => ({status: r.status, body: t})))", url)

            visits = iter(range(1, 999))

            def team(pg):
                """The team page drawn again (a new address each time: the same one would not draw it again)."""
                pg.evaluate("document.querySelectorAll('.wd-modal').forEach(m => m.remove())")
                pg.goto(f'{srv.base}/#/admin?tab=team&v={next(visits)}'); pg.wait_for_selector('#tq-links-mount .svc-head', timeout=15000); pg.wait_for_timeout(600)

            def wait_text(pg, sel, text, timeout=8000):
                for _ in range(timeout // 100):
                    if pg.locator(sel).count() and text in pg.inner_text(sel): return True
                    pg.wait_for_timeout(100)
                return False

            # 13 · the demo: freelance.prueba linked to both centres, with its own profile in the selector
            fl_c, fl = ctx(); login(fl, 'freelance.prueba')
            fl.click('#account-toggle'); fl.wait_for_timeout(300)
            profs = [fl.inner_text(f'.acc-prof >> nth={i}') for i in range(fl.locator('.acc-prof').count())]
            check('13 · la demo trae a freelance.prueba enlazado a los dos centros (su perfil y los dos centros en el selector)',
                  len(profs) == 3 and any('Bahía Coralina' in p and 'Instructor' in p for p in profs) and any('Escafandra' in p and 'Instructor' in p for p in profs), profs)
            shot(fl, 'selector-de-perfil')
            # 5 · «Mi agenda»: both centres, each with its colour, and her own work
            fl.goto(srv.base + '/#/mi-agenda'); fl.wait_for_selector('.tq-ag-nav'); fl.wait_for_timeout(500)
            colours = set(fl.eval_on_selector_all('.tq-ag-item', 'xs => xs.map(x => getComputedStyle(x).borderLeftColor)'))
            legend = fl.inner_text('.tq-legend')
            check('5 · «Mi agenda» junta los dos centros, cada uno con su color', 'Bahía Coralina' in legend and 'Escafandra' in legend and len(colours) >= 2, (legend, colours))
            shot(fl, 'mi-agenda-dos-centros', True)
            # 5 · working in the second centre: nothing of the first one on screen
            fl.goto(srv.base + '/#/area'); fl.wait_for_timeout(800)
            fl.click('#account-toggle'); fl.locator('.acc-prof', has_text='Escafandra').click(); fl.wait_for_timeout(2500)
            fl.goto(srv.base + '/#/admin?tab=bookings'); fl.wait_for_selector('#cb-bookings *', timeout=15000); fl.wait_for_timeout(1500)
            body = fl.inner_text('main') if fl.locator('main').count() else fl.inner_text('body')
            check('5 · al trabajar en el segundo centro no se ve nada del primero (sus reservas, su nombre)',
                  'Escafandra' in fl.inner_text('body') and 'Bahía Coralina' not in body and fl.locator('.tq-ctx').count() == 1, body[:300])
            shot(fl, 'trabajando-en-el-segundo-centro')
            # 6 · «Ocupado» in the manifest of the second centre at the time she works for the first one
            # (a departure of the second centre with divers, at a time she works for the first one: the demo assigns her two)
            busy = srv.sql("""SELECT x.id FROM service_slots x JOIN provider_services ps ON ps.id=x.service_id JOIN centers c ON c.id=ps.center_id
                               WHERE c.name LIKE 'Escafandra%' AND x.spots_available<x.spots_total AND x.slot_time BETWEEN '09:00' AND '11:30'
                                 AND x.slot_date IN (SELECT y.slot_date FROM service_slots y JOIN provider_services q ON q.id=y.service_id JOIN centers d ON d.id=q.center_id
                                                     WHERE d.name LIKE 'Bahía%' AND y.slot_time BETWEEN '08:30' AND '09:00'
                                                       AND y.instructor_user_id=(SELECT id FROM users WHERE username='freelance.prueba'))
                               ORDER BY x.slot_date LIMIT 1""")
            ce2_c, ce2 = ctx(); login(ce2, 'centro2.prueba')
            if busy:
                ce2.goto(f'{srv.base}/#/manifiesto?slot={busy[0]["id"]}'); ce2.wait_for_selector('#mf-add-group', timeout=15000); ce2.click('#mf-add-group')
                ce2.wait_for_selector('#mfg-guide'); ce2.wait_for_timeout(1200)
                opts = ce2.eval_on_selector_all('#mfg-guide option', 'os => os.map(o => [o.textContent, o.disabled])')
                check('6 · en el manifiesto, la persona ocupada con el otro centro sale «Ocupado» y no se puede elegir (sin decir dónde ni por qué)',
                      any('Diego Arenas' in t and 'Ocupado' in t and d for t, d in opts) and not any('Bahía' in t for t, _ in opts), opts)
                shot(ce2, 'manifiesto-ocupado')
            else:
                check('6 · hay una salida del segundo centro a la hora en que trabaja para el primero', False, 'sin salida')

            # 1 · linking with the QR opened by the phone's camera (/p/…): the centre's phone goes to «Enlazar persona»
            f2_c, f2 = ctx(); login(f2, 'freelance2.prueba')
            f2.goto(srv.base + '/#/mi-qr'); f2.wait_for_selector('#tq-code'); f2.wait_for_timeout(500)
            shot(f2, 'mi-qr', True)
            qr_url = srv.base + '/p/' + f2.evaluate("fetch('/api/my/qr').then(r => r.json()).then(d => d.token)")   # what the phone's camera opens
            ce_c, ce = ctx(PHONE); login(ce, 'centro.prueba')
            ce.goto(qr_url)
            ok1 = wait_text(ce, '#tq-step2', 'Sara Molina', 12000)
            check('1 · el QR abierto con la cámara del móvil del centro lleva a «Enlazar persona» con la tarjeta de la persona', ok1, ce.evaluate('location.href'))
            shot(ce, 'movil-enlazar-tarjeta')
            ce.select_option('#tq-role', 'manager'); ce.click('#tq-req button[type=submit]')
            check('1 · la petición sale: «En cuanto acepte, aparecerá en tu equipo»', wait_text(ce, '#tq-step2', 'En cuanto acepte'))
            ce.goto(qr_url); wait_text(ce, '#tq-err', 'ya se ha usado', 8000)
            check('2 · el mismo QR no vuelve a servir («ya se ha usado»)', 'ya se ha usado' in ce.inner_text('#tq-err'), ce.inner_text('#tq-link') if ce.locator('#tq-link').count() else '')
            ce_c.close()
            f2.goto(srv.base + '/#/mi-equipo'); f2.wait_for_selector('[data-accept]', timeout=10000)
            shot(f2, 'mi-equipo-peticion', True)
            f2.click('[data-accept]'); f2.wait_for_timeout(1500)
            ce_c, ce = ctx(); login(ce, 'centro.prueba'); team(ce)
            row = ce.locator('.tq-table tr', has_text='Sara Molina')
            check('1 · la persona acepta y aparece en el equipo como Encargado, activa',
                  row.count() == 1 and 'Activo' in row.inner_text() and row.locator('select').input_value() == 'manager', row.inner_text() if row.count() else '')
            # 1 · with the short code, from the computer, and the camera that this browser does not have
            f3_c, f3 = ctx(); login(f3, 'buzo2.prueba')
            f3.goto(srv.base + '/#/mi-qr'); f3.wait_for_selector('#tq-code'); code = f3.inner_text('#tq-code').replace(' ', '')
            ce.click('#tq-open'); ce.wait_for_selector('#tq-link'); ce.click('#tq-cam'); ce.wait_for_timeout(800)
            wait_text(ce, '#tq-err', 'escribe el código', 6000)
            check('1 · sin cámara en este navegador, lo dice y pasa a «Escribir el código»', 'escribe el código' in ce.inner_text('#tq-err') and ce.locator('#tq-code-form').is_visible(), ce.inner_text('#tq-err'))
            ce.fill('#tq-code-i', code); ce.click('#tq-code-form button[type=submit]'); ce.wait_for_selector('#tq-req', timeout=8000)
            ce.select_option('#tq-role', 'reception')
            # 4 · «Por días», starting the day after tomorrow
            ce.check('input[name="tq-r-kind"][value="days"]')
            d2 = srv.sql("SELECT date('now','+2 day') AS d")[0]['d']; d4 = srv.sql("SELECT date('now','+4 day') AS d")[0]['d']
            ce.fill('#tq-r-from', d2); ce.fill('#tq-r-to', d4)
            shot(ce, 'ordenador-enlazar-por-dias')
            ce.click('#tq-req button[type=submit]'); wait_text(ce, '#tq-step2', 'En cuanto acepte')
            ce.click('#tq-link [data-modal-close]'); ce.wait_for_timeout(300)
            f3.goto(srv.base + '/#/mi-equipo'); f3.wait_for_selector('[data-accept]', timeout=10000); f3.click('[data-accept]'); f3.wait_for_timeout(1500)
            team(ce)
            row = ce.locator('.tq-table tr', has_text='Lukas Becker')
            check('4 · un enlace «Por días» que aún no ha empezado dice «Empieza el …» y la persona todavía no entra', row.count() == 1 and 'Empieza el' in row.inner_text()
                  and f3.evaluate("fetch('/api/me').then(r => r.json()).then(d => (d.profiles||[]).length)") <= 1, row.inner_text() if row.count() else '')
            shot(ce, 'equipo-del-centro', True)
            f3_c.close()

            # 12 · «Compartir para enlazar»: the link works once
            f2.goto(srv.base + '/#/mi-qr'); f2.wait_for_selector('#tq-share'); f2.click('#tq-share'); f2.wait_for_selector('#tq-share-url')
            share = srv.base + '/e/' + f2.input_value('#tq-share-url').rsplit('/e/', 1)[1]
            shot(f2, 'compartir-para-enlazar', True)
            bahia = srv.sql("SELECT id FROM centers WHERE name LIKE 'Bahía%'")[0]['id']
            f2.evaluate("c => fetch('/api/team/switch', {method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({center: c})}).then(r => r.text())", bahia)
            working = f2.evaluate("fetch('/api/me').then(r => r.json()).then(d => d.user.role)")
            row = ce.locator('.tq-table tr', has_text='Sara Molina'); row.locator('[data-tl="end"]').click()
            ce.click('#wd-confirm-ok'); ce.wait_for_timeout(1500)
            # 8 · removed: Sara loses access at once (her session was open)
            f2.goto(srv.base + '/#/area'); f2.wait_for_timeout(1000)
            me = f2.evaluate("fetch('/api/me').then(r => r.json())")
            check('8 · al quitarla del equipo pierde el acceso al momento, con su sesión abierta dentro del centro',
                  working == 'center' and len(me.get('profiles') or []) <= 1 and me['user']['role'] == 'freelance', (working, me.get('profiles')))
            ce.goto(share)
            ok12 = wait_text(ce, '#tq-step2', 'Sara Molina', 12000)
            ce.goto(share); wait_text(ce, '#tq-err', 'ya se ha usado', 8000)
            check('12 · «Compartir para enlazar»: el enlace abre la tarjeta de la persona una vez; la segunda vez «ya se ha usado»',
                  ok12 and 'ya se ha usado' in ce.inner_text('#tq-err'), ce.inner_text('#tq-link') if ce.locator('#tq-link').count() else '')

            # 3 · invitation by e-mail to somebody without an account
            team(ce); ce.click('#tq-open'); ce.wait_for_selector('#tq-link'); ce.click('[data-tqt="email"]')
            ce.fill('#tq-mail', 'nueva.recepcion@example.com'); ce.select_option('#tq-mail-role', 'reception'); ce.click('#tq-mail-form button[type=submit]')
            wait_text(ce, '#tq-mail-form', 'Invitación enviada')
            mail = srv.sql("SELECT html FROM email_outbox WHERE to_email='nueva.recepcion@example.com' ORDER BY id DESC LIMIT 1")
            tok = re.search(r'#/equipo\?token=([A-Za-z0-9_\-]+)', mail[0]['html']).group(1) if mail else ''
            nw_c, nw = ctx(PHONE)
            nw.goto(f'{srv.base}/#/equipo?token={tok}'); nw.wait_for_selector('#tj-form', timeout=10000)
            shot(nw, 'invitacion-correo-movil', True)
            nw.fill('#tj-name', 'Nuria Recepción'); nw.fill('#tj-user', 'nuria.recepcion'); nw.fill('#tj-pass', 'buceo-seguro-2026-x'); nw.check('#tj-terms')
            nw.click('#tj-form button[type=submit]'); nw.wait_for_timeout(2500)
            team(ce); row = ce.locator('.tq-table tr', has_text='Nuria Recepción')
            check('3 · la invitación por correo a alguien sin cuenta crea la cuenta y queda enlazada (Recepción, cuenta normal)',
                  row.count() == 1 and 'Activo' in row.inner_text() and nw.evaluate('location.hash').startswith('#/mi-equipo'), row.inner_text() if row.count() else nw.evaluate('location.hash'))
            nw_c.close()

            # 2.1 · «Enlazar persona» also inside each profile, with that profile already chosen
            team(ce); ce.locator('.tr-role[data-key="reception"] summary').click(); ce.locator('.tr-role[data-key="reception"] .tq-link-role').click()
            ce.wait_for_selector('#tq-link'); ce.click('[data-tqt="email"]')
            check('2.1 · «Enlazar persona» dentro de cada perfil abre con ese perfil ya elegido', ce.eval_on_selector('#tq-mail-role', 's => s.value') == 'reception')
            ce.click('#tq-link [data-modal-close]'); ce.wait_for_timeout(300)

            # 9 · the activity log names the person and the profile
            ce.goto(srv.base + '/#/admin?tab=activity'); ce.wait_for_selector('#cb-activity table', timeout=15000)
            act = ce.inner_text('#cb-activity')
            check('9 · el registro de actividad dice quién y con qué perfil (por ejemplo, «Diego Arenas (Instructor)»)', re.search(r'\((Propietario|Instructor|Encargado|Recepción)\)', act) is not None, act[:400])
            shot(ce, 'registro-de-actividad')

            # 7 · an instructor does not see «Cobros», and the address answers that it does not exist
            fl.click('#account-toggle'); fl.locator('.acc-prof', has_text='Bahía').click(); fl.wait_for_timeout(2500)
            fl.goto(srv.base + '/#/admin'); fl.wait_for_selector('.cb-nav', timeout=15000)
            pay = get(fl, '/api/provider/payments')
            check('7 · como Instructor no ve «Cobros» en el menú y la dirección de los cobros responde 404 «No existe»',
                  fl.locator('.cb-nav[data-cbtab="payments"]').count() == 0 and pay['status'] == 404, pay)
            shot(fl, 'instructor-sin-cobros')

            # 10 · plans: Ficha gratuita, locked; Motor de reservas, only Recepción
            srv.sql("UPDATE centers SET plan_code='free',plan_status='free' WHERE name LIKE 'Escafandra%'")
            team(ce2)
            check('10 · con Ficha gratuita «Enlazar persona» sale bloqueado, con «Disponible en el plan Motor de reservas» y «Ver planes»',
                  ce2.locator('#tq-open[disabled]').count() == 1 and 'Disponible en el plan Motor de reservas' in ce2.inner_text('#tq-links-mount') and 'Ver planes' in ce2.inner_text('#tq-links-mount'))
            shot(ce2, 'plan-gratuito-bloqueado')
            srv.sql("UPDATE centers SET plan_code='booking',plan_status='active',plan_expires_at=date('now','+30 day') WHERE name LIKE 'Escafandra%'")
            team(ce2)
            dis = ce2.eval_on_selector_all('#tq-links-mount select.tl-role >> nth=0 >> option', 'os => os.map(o => [o.value, o.disabled])') if ce2.locator('select.tl-role').count() else []
            ce2.click('#tq-open'); ce2.wait_for_selector('#tq-link'); ce2.click('[data-tqt="email"]')
            mail_opts = ce2.eval_on_selector_all('#tq-mail-role option', 'os => os.map(o => [o.value, o.disabled])')
            check('10 · con Motor de reservas solo se puede elegir Recepción; los demás perfiles salen con «Disponible en el plan Pro»',
                  [v for v, d in mail_opts if not d] == ['reception'] and 'Disponible en el plan Pro' in ce2.inner_text('#tq-mail-role'), (mail_opts, dis))
            shot(ce2, 'plan-motor-solo-recepcion')
            ce2_c.close()

            # «Mantener la sesión iniciada en este ordenador» and «Cerrar sesión» always in view
            k_c, k = ctx(); login(k, 'recepcion.prueba', keep=True)
            ck = [x for x in k_c.cookies() if x['name'].endswith('wd_session') or x['name'] == 'wd_session']
            n_c, n = ctx(PHONE); login(n, 'recepcion.prueba')
            ck2 = [x for x in n_c.cookies() if x['name'].endswith('wd_session') or x['name'] == 'wd_session']
            check('«Mantener la sesión iniciada»: con la casilla la sesión sigue al cerrar el navegador (como mucho 8 horas); sin ella, no',
                  ck and 0 < ck[0]['expires'] - __import__('time').time() <= 8 * 3600 + 60 and ck2 and ck2[0]['expires'] == -1, (ck, ck2))
            # encargo del 17/10 (1.1): «Cerrar sesión» es la última opción del menú del perfil (ya no va suelto en la cabecera)
            n.click('#account-toggle'); n.wait_for_timeout(300)
            check('«Cerrar sesión», la última opción del menú del perfil, también en el móvil',
                  n.locator('#account-dropdown > :last-child#account-logout').is_visible() and not n.locator('#account-out').count())
            n.click('#account-logout'); n.wait_for_timeout(1500)
            check('«Cerrar sesión» cierra la sesión', n.evaluate("fetch('/api/me').then(r => r.json()).then(d => d.authenticated)") is False)
            for c_ in (k_c, n_c, ce_c, f2_c, fl_c): c_.close()
            browser.close()
    finally:
        srv.stop(); shutil.rmtree(tmp, ignore_errors=True)
    check('sin errores de JavaScript', not errors, errors[:3])
    good = sum(1 for _, ok in rows if ok)
    print(f'{good}/{len(rows)} comprobaciones')
    return good == len(rows)


if __name__ == '__main__':
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(0 if run(target) else 1)
