#!/usr/bin/env python3
"""v50.58 (3.5) · El aviso por WhatsApp de una sesión del curso pasada a otro día, en el navegador.

Con Meta y Stripe simulados en local (nada sale de la máquina):
1. el centro pasa la «inmersión 4» de una alumna a la salida del sábado;
2. sale el WhatsApp desde el número del centro, con la plantilla del curso y en el idioma de la alumna;
3. el botón del mensaje (/r/…) abre en la web solo esa reserva: la sesión, su nueva fecha, con quién y «Abrir mi
   reserva»; en el ordenador, en el móvil a 360 px sin desplazamiento lateral y en inglés;
4. el centro lo ve en «Avisos y WhatsApp» como «Nueva fecha de una sesión de curso», enviado;
5. sin errores en la consola.

    python3 tests/navegador/e2e_v50_58_aviso_curso.py [carpeta-de-capturas]

No usa la demo: un servidor nuevo, con un centro, su WhatsApp de prueba y dos alumnas."""
from __future__ import annotations

import datetime as dt
import sys
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Client, Server, ServerTestCase  # noqa: E402
from meta_mock import MetaMock  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
SECRET = 'whsec_connect_local'
NAME = 'worldives_curso_nueva_fecha'
DESK = {'viewport': {'width': 1440, 'height': 900}, 'locale': 'es-ES'}
PHONE = {'viewport': {'width': 360, 'height': 780}, 'locale': 'es-ES', 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}


def day(n):
    from zoneinfo import ZoneInfo
    return (dt.datetime.now(ZoneInfo('Europe/Madrid')).date() + dt.timedelta(days=n)).isoformat()


def saturday(after):
    d = dt.date.fromisoformat(day(after))
    while d.weekday() != 5: d += dt.timedelta(days=1)
    return d.isoformat()


def wait_for(fn, seconds=25):
    end = time.time() + seconds
    while time.time() < end:
        v = fn()
        if v: return v
        time.sleep(0.3)
    return fn()


def run(out: Path | None):
    rows = []

    def check(name, ok, detail=''):
        rows.append((name, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + name + (f'  · {str(detail)[:300]}' if detail != '' else ''), flush=True)

    stripe, meta = StripeMock(), MetaMock()
    meta.add_business('codeC', 'wabaC', [('pnidC', '+34 600 000 555')])
    ServerTestCase.server = Server({**meta.env(), 'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': stripe.base, 'STRIPE_CONNECT_WEBHOOK_SECRET': SECRET,
                                    'WOD_PAYMENTS_TOTP_REQUIRED': '0', 'WOD_AVISOS_SEGUNDOS': '1', 'WOD_DATA_KEY': 'clave-de-datos-de-las-pruebas-0123456789'}).start()
    srv = ServerTestCase.server
    errors = []
    try:
        t = ServerTestCase('run')
        admin = t.make_admin()
        center = t.make_center(admin, 'cwac', phone='+34 600 590 101')
        cid = center.user['center_id']
        srv.sql("""UPDATE centers SET name='Centro de Buceo Las Islas',plan_code='pro',plan_status='active',plan_expires_at='2099-12-31',stripe_account_id='acct_cwac',
                   stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?""", (cid,))
        assert center.post('/api/whatsapp/connect', {'code': 'codeC', 'waba_id': 'wabaC', 'phone_number_id': 'pnidC'}).status == 200
        srv.sql("INSERT INTO users(fullname,email,username,password_hash,role,center_id,created_at) VALUES('Marta Instructora','marta@cwac.example.org','cwac_marta','!','center',?,datetime('now'))", (cid,))
        marta = srv.sql("SELECT id FROM users WHERE username='cwac_marta'")[0]['id']
        dive = center.post('/api/provider-services', {'title': 'Doble inmersión', 'price': 40, 'booking_mode': 'payment'}).json['id']
        sat = saturday(9)
        dep = center.post('/api/provider-services/slot', {'service_id': dive, 'slot_date': sat, 'slot_time': '09:00', 'spots_total': 10}).json['slot_id']
        r = center.post('/api/provider-services/wizard', {'publish': True, 'kind': 'course', 'title': 'Open Water', 'plan': {'days': ['full', 'full'], 'dives': [1, 2, 3, 4]},
                                                          'price': 450, 'max_participants': 6, 'booking_mode': 'payment', 'instructor_user_id': marta,
                                                          'schedule': {'mode': 'dates', 'dates': [day(40)]}})
        assert r.status == 200, r
        course = r.json['id']; ed = srv.sql('SELECT id FROM service_slots WHERE service_id=?', (course,))[0]['id']

        def student(tag, name, lang, phone):
            d = t.make_diver(tag)
            srv.sql('UPDATE users SET fullname=? WHERE id=?', (name, d.user['id']))
            assert d.post('/api/account/profile', {'preferred_language': lang, 'wa_consent': True, 'phone': phone}).status == 200
            b = d.post('/api/bookings', {'center_id': cid, 'service_id': course, 'slot_id': ed, 'participants': 1})
            assert b.status == 200, b
            sess = stripe.last_session(); stripe.pay(sess['id'])
            ev = {'id': f'evt_{time.time_ns()}', 'type': 'checkout.session.completed', 'account': 'acct_cwac',
                  'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
            payload, sig = StripeMock.signed(ev, SECRET)
            Client(srv, origin=None).request('POST', '/api/payments/webhook/connect', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
            return b.json['id']

        lucia = student('cwaclucia', 'Lucía Alumna', 'es', '+34 611 300 300')
        emma = student('cwacemma', 'Emma Student', 'en', '+44 7700 900300')
        check('0 · las dos reservas del curso están pagadas', all(srv.sql('SELECT status FROM bookings WHERE id=?', (b,))[0]['status'] == 'confirmed' for b in (lucia, emma)))
        for bid in (lucia, emma):
            mv = center.post(f'/api/center/bookings/{bid}/course/move', {'seq': 4, 'mode': 'join', 'slot_id': dep})
            assert mv.status == 200, mv
        sent = wait_for(lambda: (lambda m: m if len(m) == 2 else None)([x for x in meta.sent if x['template'] == NAME]))
        check('1 · sale un WhatsApp con la plantilla del curso a cada alumna, desde el número del centro',
              sent and {x['to'] for x in sent} == {'34611300300', '447700900300'} and {x['phone_number_id'] for x in sent} == {'pnidC'}, sent)
        by_to = {x['to']: x for x in sent or []}
        params = lambda m: [p['text'] for p in next(c for c in m['components'] if c['type'] == 'body')['parameters']]
        link = lambda m: next(c for c in m['components'] if c['type'] == 'button')['parameters'][0]['text']
        es, en_ = by_to.get('34611300300'), by_to.get('447700900300')
        check('2 · en el idioma de cada alumna, con el curso, la sesión y la nueva fecha con su instructora',
              es and en_ and es['lang'] == 'es' and en_['lang'] == 'en' and params(es)[1:3] == ['Open Water', 'inmersión 4'] and 'con Marta Instructora' in params(es)[3]
              and params(en_)[2] == 'dive 4' and 'with Marta Instructora' in params(en_)[3], (es and params(es), en_ and params(en_)))
        base = srv.base

        with sync_playwright() as p:
            browser = chromium(p)

            def page_for(opts, lang=None):
                ctx = browser.new_context(**opts)
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg = ctx.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
                pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' and 'tile.openstreetmap' not in m.text and 'ERR_' not in m.text else None)
                return pg

            def shot(pg, name, full=False):
                if out: out.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(out / f'{name}.png'), full_page=full)

            def open_link(pg, token, lang=None):
                # exactly what WhatsApp opens: /r/<token>, which takes the web to that booking
                pg.goto(base + f'/r/{token}' + (f'?lang={lang}' if lang else '')); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(1200)
                if lang: pg.goto(base + f'/?lang={lang}#/r/{token}'); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(1200)
                return pg.inner_text('main')

            # ============================================================ 3 · the link of the button, desktop
            dk = page_for(DESK)
            txt = open_link(dk, link(es))
            from_date = dt.date.fromisoformat(sat)
            check('3 · el botón abre la reserva: «Nueva fecha para tu sesión del curso», la sesión, la fecha, la hora y la instructora',
                  'Nueva fecha para tu sesión del curso' in txt and 'Inmersión 4' in txt and str(from_date.day) in txt and '09:00' in txt and 'Con Marta Instructora' in txt, txt[:400])
            href = dk.get_attribute('a.btn-primary', 'href')
            check('3 · «Abrir mi reserva» lleva a esa reserva', href == f'#/reserva?id={lucia}', href)
            check('3 · no enseña el correo ni el teléfono de la alumna', 'cwaclucia' not in txt and '611 300 300' not in txt)
            shot(dk, 'aviso-whatsapp-enlace-ordenador')
            # ============================================================ 3 · phone at 360 px
            ph = page_for(PHONE)
            open_link(ph, link(es))
            wide = ph.evaluate('document.documentElement.scrollWidth - window.innerWidth')
            check('3 · móvil 360 px: sin desplazamiento lateral', wide <= 1, wide)
            shot(ph, 'aviso-whatsapp-enlace-movil-360', full=True)
            # ============================================================ 3 · English
            en = page_for(DESK)
            etxt = open_link(en, link(en_), lang='en')
            check('3 · en inglés: la página traducida', 'New date for your course session' in etxt and 'Dive 4' in etxt and 'With Marta Instructora' in etxt
                  and 'Open my booking' in etxt and 'Nueva fecha' not in etxt, etxt[:400])
            shot(en, 'aviso-whatsapp-enlace-ingles')
            # ============================================================ 4 · the centre's history
            ce = page_for(DESK)
            ce.goto(base + '/#/login'); ce.wait_for_selector('#login-form'); ce.fill('#login', 'center_cwac'); ce.fill('#password', PW)
            ce.click('#login-form button[type=submit]'); ce.wait_for_timeout(1300)
            ce.goto(base + '/#/admin?tab=avisos'); ce.wait_for_load_state('networkidle'); ce.wait_for_timeout(1500)
            hist = ce.inner_text('#nt-history') if ce.locator('#nt-history').count() else ce.inner_text('main')
            check('4 · «Avisos y WhatsApp»: el aviso del curso en el historial, enviado', hist.count('Nueva fecha de una sesión de curso') == 2 and 'Enviado' in hist, hist[:400])
            ce.locator('text=Nueva fecha de una sesión de curso').first.scroll_into_view_if_needed(); ce.wait_for_timeout(300)
            shot(ce, 'aviso-whatsapp-historial-centro')
            ce.locator('button.btn-link', has_text='Nueva fecha de una sesión de curso').first.click()
            ce.wait_for_selector('#ns-body .nt-slot', timeout=8000); ce.wait_for_timeout(600)
            st = ce.inner_text('#notice-status')
            check('4 · su estado: la sesión con su nueva fecha (no el primer día del curso) y la alumna, enviado por WhatsApp (solo esa columna: el correo y la app salen con la reserva)',
                  'nueva fecha de una sesión de curso' in st.lower() and 'inmersión 4' in st and f'{from_date.day} de ' in st and '09:00' in st
                  and ('Lucía' in st or 'Emma' in st) and 'Enviado' in st and 'Correo' not in st, repr(st[:400]))
            shot(ce, 'aviso-whatsapp-estado')
            bad = [e for e in errors if 'favicon' not in e]
            check('5 · sin errores en la consola', not bad, bad[:5])
            browser.close()
    finally:
        srv.stop(); stripe.stop(); meta.stop()
    ok = sum(1 for _, x in rows if x)
    print(f'\n{ok}/{len(rows)} comprobaciones correctas')
    return ok == len(rows)


if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(0 if run(out) else 1)
