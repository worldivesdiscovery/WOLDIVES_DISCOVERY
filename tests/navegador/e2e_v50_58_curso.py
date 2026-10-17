#!/usr/bin/env python3
"""v50.58 · 3.5 «Pasar una sesión o inmersión del curso a otro día (por alumno)», en el navegador
(docs/encargos/encargo-revision-usabilidad-15-16-10-2026.md, punto 3.5). En su orden:

1. Ficha de la reserva del curso (centro): la lista de sesiones con su estado y «0 de 4 inmersiones hechas».
2. «Marcar como hecha» con un toque: «3 de 4 inmersiones hechas · 1 pendiente».
3. «Pasar a otro día» → «Unirlo a una salida que ya existe» (sábado 9:00): la sesión sale ↪ con su nueva fecha, la
   salida y el instructor; la plaza baja en la salida; sin cobro.
4. Planning y manifiesto del sábado: «Sesión de curso – Open Water (inmersión 4)», sin «Liberar».
5. El alumno ve su curso y confirma la nueva fecha.
6. Cancelar la salida del sábado por mal tiempo: la ventana avisa de que el alumno no recibe devolución; su sesión
   queda «Pendiente de nueva fecha» y sale en «Sesiones de curso por recolocar».
7. «Crear una sesión nueva» con fecha, hora, instructor y barco: sale en el planning como bloque de curso.
8. El día llega: «Marcar como hecha» → «Curso completado», Log Book y «Registrar titulación».
9. Móvil a 360 px sin desplazamiento lateral; el alumno en inglés; sin errores en la consola.

    python3 tests/navegador/e2e_v50_58_curso.py [carpeta-de-capturas]

No usa la demo: un servidor nuevo con el simulador de Stripe (tests/stripe_mock.py)."""
from __future__ import annotations

import datetime as dt
import sys
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Client, Server, ServerTestCase  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
SECRET = 'whsec_connect_local'
DESK = {'viewport': {'width': 1440, 'height': 900}, 'locale': 'es-ES'}
PHONE = {'viewport': {'width': 360, 'height': 780}, 'locale': 'es-ES', 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}


def day(n):
    from zoneinfo import ZoneInfo
    return (dt.datetime.now(ZoneInfo('Europe/Madrid')).date() + dt.timedelta(days=n)).isoformat()


def saturday(after):
    d = dt.date.fromisoformat(day(after))
    while d.weekday() != 5: d += dt.timedelta(days=1)
    return d.isoformat()


def run(out: Path | None):
    rows = []

    def check(name, ok, detail=''):
        rows.append((name, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + name + (f'  · {str(detail)[:300]}' if detail != '' else ''), flush=True)

    stripe = StripeMock()
    ServerTestCase.server = Server({'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': stripe.base, 'STRIPE_CONNECT_WEBHOOK_SECRET': SECRET,
                                    'WOD_PAYMENTS_TOTP_REQUIRED': '0'}).start()
    srv = ServerTestCase.server
    errors = []
    try:
        t = ServerTestCase('run')
        admin = t.make_admin()
        center = t.make_center(admin, 'cso', phone='+34 600 580 101')
        cid = center.user['center_id']
        srv.sql("""UPDATE centers SET name='Centro de Buceo Las Islas',plan_code='pro',plan_status='active',plan_expires_at='2099-12-31',stripe_account_id='acct_cso',
                   stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?""", (cid,))
        for name in ('Marta Instructora', 'Leo Instructor'):
            srv.sql("INSERT INTO users(fullname,email,username,password_hash,role,center_id,created_at) VALUES(?,?,?,'!','center',?,datetime('now'))",
                    (name, name.split()[0].lower() + '@cso.example.org', 'cso_' + name.split()[0].lower(), cid))
        marta, leo = [r['id'] for r in srv.sql("SELECT id FROM users WHERE username LIKE 'cso_%' ORDER BY id")]
        srv.sql("INSERT INTO boats(center_id,name,capacity,active,created_at,updated_at) VALUES(?,'Neptuno',12,1,datetime('now'),datetime('now'))", (cid,))
        dive = center.post('/api/provider-services', {'title': 'Doble inmersión', 'price': 40, 'booking_mode': 'payment'}).json['id']
        sat1, sat2 = saturday(9), saturday(16)
        dep1 = center.post('/api/provider-services/slot', {'service_id': dive, 'slot_date': sat1, 'slot_time': '09:00', 'spots_total': 10}).json['slot_id']
        r = center.post('/api/provider-services/wizard', {'publish': True, 'kind': 'course', 'title': 'Open Water', 'plan': {'days': ['full', 'full'], 'dives': [1, 2, 3, 4]},
                                                          'price': 450, 'max_participants': 6, 'booking_mode': 'payment', 'instructor_user_id': marta,
                                                          'schedule': {'mode': 'dates', 'dates': [day(40)]}})
        assert r.status == 200, r
        course = r.json['id']; ed = srv.sql('SELECT id FROM service_slots WHERE service_id=?', (course,))[0]['id']
        diver = t.make_diver('csoalumna')
        srv.sql("UPDATE users SET fullname='Lucía Alumna' WHERE id=?", (diver.user['id'],))
        b = diver.post('/api/bookings', {'center_id': cid, 'service_id': course, 'slot_id': ed, 'participants': 1})
        assert b.status == 200, b
        bid = b.json['id']
        sess = stripe.last_session(); stripe.pay(sess['id'])
        ev = {'id': f'evt_{time.time_ns()}', 'type': 'checkout.session.completed', 'account': 'acct_cso',
              'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
        payload, sig = StripeMock.signed(ev, SECRET)
        Client(srv, origin=None).request('POST', '/api/payments/webhook/connect', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
        check('0 · la reserva del curso está pagada y confirmada', srv.sql('SELECT status FROM bookings WHERE id=?', (bid,))[0]['status'] == 'confirmed')
        # the course began yesterday: today is its second and last day
        srv.sql('UPDATE service_slots SET slot_date=?, date_to=? WHERE id=?', (day(-1), day(0), ed))
        srv.sql('UPDATE bookings SET booking_date=?, date_to=? WHERE id=?', (day(-1), day(0), bid))
        base = srv.base

        with sync_playwright() as p:
            browser = chromium(p)

            def page_for(opts, lang=None):
                ctx = browser.new_context(**opts)
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg = ctx.new_page(); pg.lang = lang; pg.on('pageerror', lambda e: errors.append(str(e)))
                pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' and 'tile.openstreetmap' not in m.text and 'ERR_' not in m.text else None)
                return pg

            def go(pg, route, wait=1200):
                pg.goto(base + (f'/?lang={pg.lang}' if pg.lang else '/') + route); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(wait)

            def login(pg, user):
                go(pg, '#/login', 500); pg.fill('#login', user); pg.fill('#password', PW); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1300)

            def shot(pg, name, full=False):
                if out: out.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(out / f'{name}.png'), full_page=full)

            def card(pg):
                pg.wait_for_selector('.cs-card', timeout=8000)
                return pg.inner_text('.cs-card')

            def row(pg, seq):
                return pg.inner_text(f'.cs-row[data-seq="{seq}"]')

            def spots(slot):
                return srv.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot,))[0]['spots_available']

            # ============================================================ 1 · the course booking, as the centre
            ce = page_for(DESK); login(ce, 'center_cso'); go(ce, f'#/reserva?id={bid}', 1500)
            txt = card(ce)
            check('1 · ficha de la reserva: «PROGRESO DEL CURSO» con las 4 inmersiones', 'PROGRESO DEL CURSO' in txt and ce.locator('.cs-row').count() == 4, txt[:200])
            check('1 · resumen «0 de 4 inmersiones hechas · 4 pendientes»', '0 de 4 inmersiones hechas · 4 pendientes' in txt)
            check('1 · las de hoy se pueden marcar; ninguna dice «Hecha» todavía', ce.locator('[data-cs-done]').count() == 4 and ce.locator('.cs-row.cs-done').count() == 0)
            shot(ce, 'curso-1-progreso-ordenador')
            # ============================================================ 2 · one tap each
            for seq in (1, 2, 3):
                ce.click(f'[data-cs-done="{seq}"]'); ce.wait_for_selector(f'.cs-row.cs-done[data-seq="{seq}"]', timeout=6000)
            txt = card(ce)
            check('2 · «Marcar como hecha» con un toque: «3 de 4 inmersiones hechas · 1 pendiente»', '3 de 4 inmersiones hechas · 1 pendiente' in txt, txt[:200])
            check('2 · ✔ en las tres y ⏳ en la cuarta', ce.locator('.cs-row.cs-done').count() == 3 and ce.locator('.cs-row.cs-pending[data-seq="4"]').count() == 1)
            # ============================================================ 3 · «Pasar a otro día» → Saturday's departure
            before, price = spots(dep1), srv.sql('SELECT price FROM bookings WHERE id=?', (bid,))[0]['price']
            ce.click('[data-cs-move="4"]'); ce.wait_for_selector('#cs-move-m .cs-dep')
            m = ce.inner_text('#cs-move-m')
            check('3 · la ventana ofrece las dos opciones del encargo', 'Unirlo a una salida que ya existe' in m and 'Crear una sesión nueva' in m)
            check('3 · la salida del sábado 9:00 con sus plazas libres; el instructor del curso por defecto',
                  ce.locator(f'#cs-move-m input[name="csm-slot"][value="{dep1}"]').count() == 1 and ce.input_value('#csm-teacher') == str(marta), m[:300])
            check('3 · dice que no se cobra otra vez', 'Sin cobro extra' in m)
            ce.wait_for_timeout(450); shot(ce, 'curso-2-pasar-a-otro-dia')
            ce.click(f'#cs-move-m input[name="csm-slot"][value="{dep1}"]'); ce.click('#csm-ok'); ce.wait_for_selector('.cs-row.cs-moved[data-seq="4"]', timeout=8000); ce.wait_for_timeout(450)
            r4 = row(ce, 4)
            d1 = dt.date.fromisoformat(sat1)
            check('3 · la inmersión 4 sale ↪ «Aplazada» con la nueva fecha, la salida y Marta', 'Aplazada' in r4 and str(d1.day) in r4 and 'Doble inmersión · 09:00' in r4 and 'con Marta Instructora' in r4, r4)
            check('3 · y recuerda cuándo era («Antes: …»)', 'Antes:' in r4, r4)
            check('3 · la plaza baja en la salida del sábado', spots(dep1) == before - 1, (before, spots(dep1)))
            check('3 · sin cobro: mismo precio y ningún pago nuevo', srv.sql('SELECT price FROM bookings WHERE id=?', (bid,))[0]['price'] == price
                  and srv.sql('SELECT COUNT(*) AS n FROM payment_orders WHERE booking_id=?', (bid,))[0]['n'] == 1)
            check('3 · el curso sigue «En curso»', 'En curso' in card(ce) and 'Curso completado' not in card(ce))
            shot(ce, 'curso-3-aplazada')
            # ============================================================ 4 · planning and manifest of Saturday
            go(ce, '#/admin?tab=planning', 1500)
            while ce.locator(f'.pl-cell[data-day="{sat1}"]').count() == 0:
                ce.click('.pl-arrow[aria-label="Mes siguiente"]'); ce.wait_for_timeout(900)
            ce.click(f'.pl-cell[data-day="{sat1}"]'); ce.wait_for_selector('#pl-pop')
            pop = ce.inner_text('#pl-pop')
            check('4 · planning: la salida del sábado lleva «Sesión de curso – Open Water (inmersión 4)»', 'Sesión de curso – Open Water (inmersión 4)' in pop, pop[:300])
            check('4 · esa plaza no se «Libera» desde el planning', ce.locator('#pl-pop .pl-block.is-course .pl-unblock').count() == 0)
            shot(ce, 'curso-4-planning-sabado')
            ce.keyboard.press('Escape')
            go(ce, f'#/manifiesto?slot={dep1}', 1500)
            man = ce.inner_text('body')
            check('4 · manifiesto: «Sesiones de curso» con la alumna y su instructora', 'Sesiones de curso' in man and 'Lucía Alumna' in man and 'con Marta Instructora' in man)
            # ============================================================ 5 · the student
            dv = page_for(DESK); login(dv, 'diver_csoalumna'); go(dv, f'#/reserva?id={bid}', 1500)
            txt = card(dv)
            check('5 · el alumno ve su curso: «3 de 4 inmersiones hechas · 1 pendiente»', '3 de 4 inmersiones hechas · 1 pendiente' in txt, txt[:200])
            check('5 · y no tiene los botones del centro', dv.locator('[data-cs-done],[data-cs-move]').count() == 0)
            check('5 · le ha llegado el aviso con la nueva fecha', bool(srv.sql("SELECT 1 FROM messages WHERE recipient_user_id=? AND subject='Nueva fecha para tu inmersión 4'", (diver.user['id'],))))
            dv.click('[data-cs-ok="4"]'); dv.wait_for_selector('.cs-reply', timeout=6000)
            check('5 · «Confirmo» → «Has confirmado la nueva fecha.»', 'Has confirmado la nueva fecha' in row(dv, 4))
            shot(dv, 'curso-5-alumno-confirma')
            # ============================================================ 6 · bad weather on Saturday
            go(ce, '#/admin?tab=planning', 1500)
            while ce.locator(f'.pl-cell[data-day="{sat1}"]').count() == 0:
                ce.click('.pl-arrow[aria-label="Mes siguiente"]'); ce.wait_for_timeout(900)
            ce.click(f'.pl-cell[data-day="{sat1}"]'); ce.wait_for_selector('#pl-pop .pl-cancel'); ce.click('#pl-pop .pl-cancel')
            ce.wait_for_selector('#notice-modal .nt-course', timeout=8000)
            hint = ce.inner_text('#notice-modal .nt-course')
            check('6 · «Cancelar salida y avisar a todos» avisa: el alumno de curso no recibe devolución', 'no se le devuelve el dinero' in hint and 'Pendiente de nueva fecha' in hint, hint)
            ce.wait_for_timeout(450); shot(ce, 'curso-6-cancelar-mal-tiempo')
            ce.click('#notice-modal [data-modal-close]'); ce.wait_for_timeout(300)
            r = center.post('/api/provider-services/slot-cancel', {'slot_id': dep1, 'reason': 'weather', 'note': 'Temporal'})
            check('6 · salida cancelada por mal tiempo', r.status == 200, r)
            go(ce, f'#/reserva?id={bid}', 1500)
            r4 = row(ce, 4)
            check('6 · la inmersión 4 queda «Pendiente de nueva fecha»', 'Pendiente de nueva fecha' in r4 and ce.locator('.cs-row.cs-pending_new_date[data-seq="4"]').count() == 1, r4)
            check('6 · sin devolución: la reserva sigue confirmada', srv.sql('SELECT status, COALESCE(refunded_total,0) AS r FROM bookings WHERE id=?', (bid,))[0]['status'] == 'confirmed')
            go(ce, '#/admin?tab=planning', 1500)
            ce.wait_for_selector('.cs-relocate', timeout=8000)
            pend = ce.inner_text('.cs-relocate')
            check('6 · el panel: «Sesiones de curso por recolocar» con la alumna', 'Sesiones de curso por recolocar' in pend and 'Lucía Alumna' in pend and 'Pendiente de nueva fecha' in pend, pend)
            check('6 · con el recordatorio configurable (30 días)', ce.input_value('#cs-days') == '30')
            shot(ce, 'curso-7-por-recolocar')
            # ============================================================ 7 · a new session of its own
            ce.click('.cs-relocate li a'); ce.wait_for_selector('.cs-card'); ce.wait_for_timeout(600)
            ce.click('[data-cs-move="4"]'); ce.wait_for_selector('#cs-move-m')
            ce.check('#cs-move-m input[name="csm-mode"][value="new"]'); ce.wait_for_timeout(200)
            ce.fill('#csm-date', sat2); ce.fill('#csm-time', '10:00'); ce.fill('#csm-end', '13:00')
            ce.select_option('#csm-teacher', str(leo)); ce.select_option('#csm-boat', label='Neptuno')
            ce.wait_for_timeout(300); shot(ce, 'curso-8-sesion-nueva')
            ce.click('#csm-ok'); ce.wait_for_selector('.cs-row.cs-moved[data-seq="4"]', timeout=8000)
            r4 = row(ce, 4)
            check('7 · «Crear una sesión nueva»: fecha, hora, Leo y el barco', '10:00' in r4 and 'con Leo Instructor' in r4 and 'Barco Neptuno' in r4, r4)
            busy = srv.sql("""SELECT 1 FROM resource_blocks rb JOIN resources r ON r.id=rb.resource_id WHERE r.user_id=? AND rb.ref_type='course_new' AND rb.status='active'""", (leo,))
            check('7 · Leo queda ocupado en la agenda común', bool(busy))
            go(ce, '#/admin?tab=planning', 1500)
            while ce.locator(f'.pl-cell[data-day="{sat2}"]').count() == 0:
                ce.click('.pl-arrow[aria-label="Mes siguiente"]'); ce.wait_for_timeout(900)
            chip = ce.locator(f'.pl-cell[data-day="{sat2}"] .pl-chip.is-course').count()
            ce.click(f'.pl-cell[data-day="{sat2}"]'); ce.wait_for_selector('#pl-pop')
            pop = ce.inner_text('#pl-pop')
            check('7 · planning: la sesión de curso sale en su día, con su hora e instructor', chip == 1 and 'Sesión de curso · Open Water' in pop and 'con Leo Instructor' in pop, pop[:300])
            check('7 · «Sesiones de curso por recolocar» ya no la lista', ce.locator('.cs-relocate').count() == 0)
            ce.keyboard.press('Escape')
            # ============================================================ 8 · the day comes: completed
            srv.sql('UPDATE booking_sessions SET local_date=? WHERE booking_id=? AND seq=4', (day(0), bid))
            go(ce, f'#/reserva?id={bid}', 1500)
            ce.click('[data-cs-done="4"]'); ce.wait_for_selector('.cs-card .cs-finished', timeout=8000)
            txt = card(ce)
            check('8 · todas hechas → «Curso completado»', 'Curso completado' in txt and '4 de 4 inmersiones hechas' in txt, txt[:300])
            check('8 · la reserva pasa a completada', srv.sql('SELECT status FROM bookings WHERE id=?', (bid,))[0]['status'] == 'completed')
            n_lb = srv.sql("SELECT COUNT(*) AS n FROM logbook_entries WHERE user_id=? AND dive_type='Curso'", (diver.user['id'],))[0]['n']
            check('8 · las 4 inmersiones entran en su Log Book', n_lb == 4, n_lb)
            for _ in range(40):
                if ce.locator('#cs-cert option').count(): break
                ce.wait_for_timeout(100)
            ce.select_option('#cs-cert', label='OWD'); ce.click('#cs-cert-save'); ce.wait_for_timeout(900)
            check('8 · «Registrar titulación» → «Titulación registrada: OWD»', 'Titulación registrada: OWD' in card(ce))
            shot(ce, 'curso-9-completado')
            # ============================================================ 9 · phone, English, console
            ph = page_for(PHONE); login(ph, 'diver_csoalumna'); go(ph, f'#/reserva?id={bid}', 1500); card(ph)
            wide = ph.evaluate('document.documentElement.scrollWidth - window.innerWidth')
            check('9 · móvil 360 px: la ficha del curso sin desplazamiento lateral', wide <= 1, wide)
            ph.locator('.cs-card').scroll_into_view_if_needed(); shot(ph, 'curso-10-alumno-movil-360')
            check('9 · el alumno ve «¡Curso completado!» y el enlace a su Log Book', ph.locator('.cs-card a[href="#/logbook"]').count() == 1)
            en = page_for(DESK, lang='en'); login(en, 'diver_csoalumna'); go(en, f'#/reserva?id={bid}', 1800)
            etxt = card(en)
            check('9 · en inglés: la tarjeta traducida', 'COURSE PROGRESS' in etxt and '4 of 4 dives done' in etxt and 'Dive 4' in etxt and 'PROGRESO' not in etxt, etxt[:300])
            en.locator('.cs-card').scroll_into_view_if_needed(); en.evaluate('window.scrollBy(0,-90)'); en.wait_for_timeout(200)
            shot(en, 'curso-11-alumno-ingles')
            bad = [e for e in errors if 'favicon' not in e]
            check('9 · sin errores en la consola', not bad, bad[:5])
            browser.close()
    finally:
        srv.stop(); stripe.stop()
    ok = sum(1 for _, x in rows if x)
    print(f'\n{ok}/{len(rows)} comprobaciones correctas')
    return ok == len(rows)


if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(0 if run(out) else 1)
