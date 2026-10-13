"""v50.49 · App Centro PRO y Freelance PRO (Tandas 2, 3 y 4) in a phone-sized browser, with the user agent of
WORLDIVES Pruebas. Checks:
- owner of a centre: tabs Hoy · Agenda · Escanear · Solicitudes · Más; «Hoy» with its numbers, what is urgent and
  today's departure drawn as seats; the boat list (56 px check-in, without coverage: kept on the phone and sent when the
  connection comes back), counting on board, the summary for the boat (shared text and the signed PDF link);
- Escanear: a typed booking code marks the arrival, twice says «ya estaba», a booking of another centre says so;
- Solicitudes: reject with a reason chip, accept; «Pendientes de pago»: take the payment at the centre;
- Agenda: month (42 days, today marked), week (7 days), create a departure repeated one week;
- Reservas and «Nueva reserva» (less than 45 s), Más (Disponible en la web, «Borrar mi cuenta para siempre»);
- an instructor (permission «checkin» only): no Solicitudes, no Cobros, no Equipo;
- a freelance: today's job with Llamar · WhatsApp · Cómo llegar, block a day with one tap;
- closing an account in the app and reopening it; en and fr: every text translated; 360 px: nothing goes out of the
  screen (Normal and Enorme); no JavaScript errors.
Usage: python tests/navegador/e2e_app_pro.py [--shots DIR]
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
from helpers import ServerTestCase, Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
UA = 'Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36 WorldivesApp/1.0 pruebas'
PRO = ['#/', '#/agenda', '#/escanear', '#/solicitudes', '#/mas', '#/reservas', '#/nueva-reserva', '#/estadisticas', '#/cobros-app']


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


def run(shots: Path | None):
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))

    ServerTestCase.server = Server().start(); srv = ServerTestCase.server
    try:
        t = ServerTestCase('run')
        admin = t.make_admin()
        c = t.make_center(admin, 'pro1', phone='+34 600 300 001'); other = t.make_center(admin, 'otro1', phone='+34 600 300 002')
        cid, oid = c.user['center_id'], other.user['center_id']
        srv.sql("UPDATE centers SET name='Centro de Buceo Xàbia', plan_code='pro', plan_status='active', latitude=38.79, longitude=0.18 WHERE id=?", (cid,))
        srv.sql("UPDATE centers SET plan_code='pro', plan_status='active' WHERE id=?", (oid,))
        s1 = c.post('/api/provider-services', {'title': 'Doble inmersión en barco', 'price': 45, 'booking_mode': 'request'}).json['id']
        hoy_t = '23:30' if dt.datetime.now().hour < 23 else '23:59'
        sl_hoy = c.post('/api/provider-services/slot', {'service_id': s1, 'slot_date': day(0), 'slot_time': hoy_t, 'spots_total': 12}).json['slot_id']
        sl_man = c.post('/api/provider-services/slot', {'service_id': s1, 'slot_date': day(1), 'slot_time': '09:00', 'spots_total': 10}).json['slot_id']
        so = other.post('/api/provider-services', {'title': 'Islas Medes', 'price': 60}).json['id']
        sl_o = other.post('/api/provider-services/slot', {'service_id': so, 'slot_date': day(0), 'slot_time': hoy_t, 'spots_total': 8}).json['slot_id']

        def booking(diver, center, service, slot, status, n=1, **extra):
            r = diver.post('/api/bookings', {'center_id': center, 'service_id': service, 'slot_id': slot, 'participants': n})
            assert r.status == 200, r
            sets = ', '.join(['status=?'] + [f'{k}=?' for k in extra])
            srv.sql(f'UPDATE bookings SET {sets} WHERE id=?', (status, *extra.values(), r.json['id']))
            if status == 'confirmed':
                srv.sql('UPDATE service_slots SET spots_available=spots_available-? WHERE id=?', (n, slot))
            return r.json['id']
        divers = [t.make_diver(f'pro{i}') for i in range(6)]
        for i, d in enumerate(divers): d.post('/api/account/profile', {'phone': f'+34 611 300 0{i:02d}', 'preferred_language': 'es'})
        b1 = booking(divers[0], cid, s1, sl_hoy, 'confirmed', 2, payment_status='at_center')
        b2 = booking(divers[1], cid, s1, sl_hoy, 'confirmed', payment_status='at_center')
        b3 = booking(divers[2], cid, s1, sl_hoy, 'confirmed', payment_status='at_center')
        req1 = booking(divers[3], cid, s1, sl_man, 'requested', response_deadline=(dt.datetime.now() + dt.timedelta(minutes=40)).isoformat(timespec='minutes'))
        req2 = booking(divers[4], cid, s1, sl_man, 'requested', response_deadline=(dt.datetime.now() + dt.timedelta(hours=20)).isoformat(timespec='minutes'))
        pay1 = booking(divers[5], cid, s1, sl_man, 'accepted_pending_payment', payment_status='required', payment_deadline=(dt.datetime.now() + dt.timedelta(hours=2)).isoformat(timespec='minutes'))
        b_other = booking(t.make_diver('ajeno1'), oid, so, sl_o, 'confirmed', payment_status='at_center')
        tok = lambda bid: srv.sql('SELECT public_token FROM bookings WHERE id=?', (bid,))[0]['public_token']
        code = lambda bid: f'{bid}-{tok(bid)[:6].upper()}'
        # an instructor of the centre
        ins = t.make_diver('instr1')
        srv.sql("UPDATE users SET role='center', center_id=? WHERE id=?", (cid, ins.user['id']))
        srv.sql("INSERT INTO center_members(center_id,user_id,member_role,created_at) VALUES(?,?,'instructor',?)", (cid, ins.user['id'], day(0)))
        # a freelance with a job by days today
        fr = t.make_freelance(admin, 'libre1')
        rules = {'min_days': 1, 'max_days': 10, 'lead_hours': 0, 'am': ['08:00', '13:00'], 'pm': ['14:00', '19:00'], 'full': ['08:00', '16:00']}
        sf = fr.post('/api/provider-services', {'title': 'Guía privado', 'price': 120, 'booking_mode': 'request', 'booking_unit': 'day', 'unit_rules': rules, 'pricing': {'day': 120}}).json['id']
        base = srv.base

        with sync_playwright() as p:
            browser = chromium(p)

            def phone(width=390, height=844, lang='es-ES'):
                ctx = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=True, has_touch=True, device_scale_factor=2, locale=lang, user_agent=UA)
                page = ctx.new_page(); errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                return ctx, page, errors

            def go(page, route, wait=1000):
                page.goto(base + '/' + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)

            def shot(page, name):
                if shots:
                    shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'))

            def login(page, user):
                go(page, '#/login', 600); page.fill('#login', user); page.fill('#password', PW); page.click('#login-form button[type=submit]'); page.wait_for_timeout(1500)

            tabs = lambda page: page.eval_on_selector_all('.wda-tab > span:nth-child(2)', 'els => els.map(e => e.textContent.trim())')
            toast = lambda page: page.evaluate("[...document.querySelectorAll('.toast, #toast, .wd-toast')].map(e => e.textContent).join(' ')")

            # ---------------------------------------------------------------- owner: Hoy
            ctx, page, errors = phone()
            login(page, 'center_pro1'); go(page, '#/', 1800)
            check('centro · pestañas Hoy, Agenda, Escanear, Solicitudes, Más', tabs(page) == ['Hoy', 'Agenda', 'Escanear', 'Solicitudes', 'Más'], tabs(page))
            check('centro · Escanear es la pestaña central', page.locator('.wda-tab.central').count() == 1)
            txt = page.inner_text('#app')
            check('hoy · «Tu día» con las cifras', 'Tu día' in txt and page.locator('.cifras .cifra').count() == 4, page.locator('.cifras .cifra').count())
            check('hoy · 4 buceadores hoy, 0 llegados', '0/4' in txt, txt[:300])
            check('hoy · urgente: la solicitud que caduca en 40 min', 'Urgente' in txt and page.locator('section .anillo.urg').count() >= 1)
            card = page.locator(f'a[href="#/salida?id={sl_hoy}"]').first
            check('hoy · la salida de hoy dibujada con sus plazas', card.locator('.asiento').count() == 12 and card.locator('.asiento.ok').count() == 4, (card.locator('.asiento').count(), card.locator('.asiento.ok').count()))
            check('hoy · «Mañana» plegado', page.locator('details summary', has_text='Mañana').count() == 1)
            check('hoy · contador de solicitudes en la pestaña', page.locator('.wda-tab[href="#/solicitudes"] .cont').inner_text() == '2' if page.locator('.wda-tab[href="#/solicitudes"] .cont').count() else False)
            t_hoy = page.evaluate('window.WDAMedidas && window.WDAMedidas.hoy')
            check('hoy · se ve en menos de 5 s', t_hoy is not None and t_hoy < 5000, t_hoy)
            print(f'   medida · «Hoy» en {t_hoy} ms', flush=True)
            shot(page, '01-hoy')

            # ---------------------------------------------------------------- the boat list
            page.locator('a[href="#/salida?id=%d"]' % sl_hoy).first.click(); page.wait_for_timeout(1500)
            check('salida · lista con los 4 buceadores (uno con acompañante)', page.locator('.buceador-fila').count() == 4, page.locator('.buceador-fila').count())
            sizes = page.eval_on_selector_all('.marca-check', 'els => els.map(e => [e.offsetWidth, e.offsetHeight])')
            check('salida · botones de llegada de 56 px', all(w >= 56 and h >= 56 for w, h in sizes), sizes)
            page.locator('.marca-check').first.click(); page.wait_for_timeout(900)
            row = srv.sql('SELECT checked_in_at FROM manifest_entries WHERE booking_id=? AND seat=1', (b1,))
            check('salida · tocar marca la llegada en el servidor', row and row[0]['checked_in_at'])
            shot(page, '02-salida')
            ctx.set_offline(True)
            page.locator('.marca-check:not(.si)').first.click(); page.wait_for_timeout(700)
            queued = page.evaluate("JSON.parse(localStorage.getItem('wda-pro-cola') || '[]').length")
            check('sin conexión · la marca se guarda en el móvil', queued == 1, queued)
            ctx.set_offline(False); page.evaluate("window.dispatchEvent(new Event('online'))"); page.wait_for_timeout(1500)
            present = srv.sql('SELECT COUNT(*) n FROM manifest_entries WHERE slot_id=? AND checked_in_at IS NOT NULL', (sl_hoy,))[0]['n']
            check('sin conexión · al volver la red se envía', present == 2 and page.evaluate("JSON.parse(localStorage.getItem('wda-pro-cola') || '[]').length") == 0, present)
            go(page, f'#/salida?id={sl_hoy}', 1200)
            ctx.set_offline(True); go_ok = True
            try:
                page.evaluate("location.hash = '#/contar?id=%d'" % sl_hoy); page.wait_for_timeout(300); page.evaluate("location.hash = '#/salida?id=%d'" % sl_hoy); page.wait_for_timeout(1200)
            except Exception:
                go_ok = False
            check('sin conexión · la lista del barco se abre desde el móvil', go_ok and page.locator('.buceador-fila').count() == 4 and 'Sin conexión' in page.inner_text('#app'))
            ctx.set_offline(False)
            # count on board
            go(page, f'#/contar?id={sl_hoy}', 1200)
            page.click('#ct-mas'); page.click('#ct-mas'); page.click('#ct-ok'); page.wait_for_timeout(800)
            check('contar a bordo · 2 de 2: están todos', 'Están todos' in page.inner_text('#ct-res'), page.inner_text('#ct-res'))
            page.click('#ct-mas'); page.click('#ct-ok'); page.wait_for_timeout(800)
            check('contar a bordo · 3 de 2: sobra 1', 'Sobran' in page.inner_text('#ct-res'), page.inner_text('#ct-res'))
            check('contar a bordo · queda en el historial', len(srv.sql("SELECT 1 FROM slot_events WHERE slot_id=? AND kind='headcount'", (sl_hoy,))) == 2)
            shot(page, '03-contar')
            go(page, f'#/resumen-barco?id={sl_hoy}', 1200)
            check('resumen barco · buceadores y botones', 'buceadores' in page.inner_text('#app') and page.locator('#rb-comp').count() == 1)
            shot(page, '04-resumen-barco')
            with page.expect_request(lambda r: '/resumen.pdf?t=' in r.url) as pdf_req:
                page.click('#rb-pdf')
            url = pdf_req.value.url
            pdf = c.get(url.replace(base, '')) if False else None
            import urllib.request
            raw = urllib.request.urlopen(url).read()
            check('resumen barco · enlace firmado al PDF (sin sesión, 10 min)', raw.startswith(b'%PDF'), url)

            # ---------------------------------------------------------------- Escanear
            go(page, '#/escanear', 1000)
            page.fill('#wda-cod-i', code(b2)); page.click('#wda-cod button[type=submit]'); page.wait_for_timeout(1000)
            check('escanear · código escrito: llegada marcada', 'Llegada marcada' in page.inner_text('#wda-res'), page.inner_text('#wda-res'))
            shot(page, '05-escanear-ok')
            page.fill('#wda-cod-i', code(b2)); page.click('#wda-cod button[type=submit]'); page.wait_for_timeout(900)
            check('escanear · otra vez: ya estaba marcada', 'ya estaba' in page.inner_text('#wda-res'))
            page.fill('#wda-cod-i', code(b_other)); page.click('#wda-cod button[type=submit]'); page.wait_for_timeout(900)
            check('escanear · reserva de otro centro: «no es de tu centro»', 'no es de tu centro' in page.inner_text('#wda-res') and 'Islas' not in page.inner_text('#wda-res'))
            page.fill('#wda-cod-i', f'{req1}-{tok(req1)[:6]}'); page.click('#wda-cod button[type=submit]'); page.wait_for_timeout(900)
            check('escanear · solicitud sin aceptar', 'no has aceptado' in page.inner_text('#wda-res'))
            shot(page, '06-escanear-aviso')

            # ---------------------------------------------------------------- Solicitudes
            go(page, '#/solicitudes', 1300)
            check('solicitudes · las dos por contestar, la urgente primero', page.locator('.solicitud').count() == 2 and page.locator('.solicitud').first.locator('.anillo.urg').count() == 1)
            shot(page, '07-solicitudes')
            page.locator(f'[data-no="{req2}"]').click(); page.wait_for_timeout(600)
            page.locator('[data-m="1"]').click(); page.click('#rj-ok'); page.wait_for_timeout(1200)
            st = srv.sql('SELECT status,reject_reason FROM bookings WHERE id=?', (req2,))[0]
            check('solicitudes · rechazar con el motivo elegido', st['status'] == 'rejected' and 'Mal tiempo' in (st['reject_reason'] or ''), dict(st))
            page.locator(f'[data-ok="{req1}"]').click(); page.wait_for_timeout(1300)
            check('solicitudes · aceptar', srv.sql('SELECT status FROM bookings WHERE id=?', (req1,))[0]['status'] in ('confirmed', 'accepted_pending_payment'))
            go(page, '#/solicitudes?ver=pago', 1200)
            check('pendientes de pago · listadas con su cuenta atrás', page.locator(f'[data-cob="{pay1}"]').count() == 1)
            page.locator(f'[data-cob="{pay1}"]').click(); page.wait_for_timeout(500); page.click('[data-pm="efectivo"]'); page.wait_for_timeout(1200)
            st = srv.sql('SELECT status,payment_status FROM bookings WHERE id=?', (pay1,))[0]
            check('pendientes de pago · cobrar en el centro confirma la plaza', st['status'] == 'confirmed' and st['payment_status'] == 'paid', dict(st))

            # ---------------------------------------------------------------- Agenda
            go(page, '#/agenda?vista=mes', 1500)
            check('agenda · mes con 42 días y hoy marcado', page.locator('.mes .dia').count() == 42 and page.locator('.mes .dia.hoy').count() == 1)
            check('agenda · el color de la ocupación', page.locator(f'.dia[data-dia="{day(0)}"]').get_attribute('data-p') not in ('0', None))
            shot(page, '08-agenda-mes')
            page.locator(f'.dia[data-dia="{day(1)}"]').click(); page.wait_for_timeout(500)
            check('agenda · tocar un día muestra sus salidas', page.locator(f'#wda-ag-dia a[href="#/salida?id={sl_man}"]').count() == 1)
            page.click('[data-vista="semana"]'); page.wait_for_timeout(1200)
            check('agenda · semana con 7 días', page.locator('.semana-dia').count() == 7)
            shot(page, '09-agenda-semana')
            page.click('#wda-crear'); page.wait_for_timeout(900)
            page.fill('#cs-d', day(5)); page.fill('#cs-h', '10:30'); page.select_option('#cs-r', '1'); page.click('#cs-ok'); page.wait_for_timeout(1800)
            made = srv.sql("SELECT slot_date FROM service_slots WHERE service_id=? AND slot_time='10:30' ORDER BY slot_date", (s1,))
            check('agenda · crear salida repetida una semana', [r['slot_date'] for r in made] == [day(5), day(12)], made)

            # ---------------------------------------------------------------- Reservas and Nueva reserva
            go(page, '#/reservas', 1300)
            check('reservas · lista con filtros', page.locator('[data-chip]').count() == 4 and page.locator('#rs-l .lista-fila').count() >= 3)
            go(page, '#/nueva-reserva', 1200)
            t0 = time.time()
            page.fill('#nr-n', 'Marta Cliente Teléfono'); page.fill('#nr-t', '+34 622 000 111'); page.select_option('#nr-sl', str(sl_man)); page.click('#nr-mas'); page.click('#nr [type=submit]'); page.wait_for_timeout(1500)
            secs = time.time() - t0
            nb = srv.sql("SELECT b.participants,b.slot_id FROM bookings b JOIN users u ON u.id=b.user_id WHERE u.fullname='Marta Cliente Teléfono' ORDER BY b.id DESC LIMIT 1")
            check('nueva reserva · guardada en la salida (2 personas)', nb and nb[0]['participants'] == 2 and nb[0]['slot_id'] == sl_man, (nb, page.inner_text('#toast')))
            check('nueva reserva · menos de 45 s', secs < 45, round(secs, 1))
            print(f'   medida · nueva reserva en {secs:.1f} s (recorrido automático)', flush=True)
            check('nueva reserva · abre la lista del barco', page.evaluate('location.hash') == f'#/salida?id={sl_man}')

            # ---------------------------------------------------------------- Más
            go(page, '#/mas', 1300)
            m = page.inner_text('#app')
            check('más · «Disponible en la web», equipo y borrar la cuenta', all(x.lower() in m.lower() for x in ('Disponible en la web', 'Equipo y perfiles', 'Borrar mi cuenta para siempre', 'Cobros', 'Estadísticas')), m[:400])
            shot(page, '10-mas')
            go(page, '#/estadisticas', 1200)
            check('estadísticas · cifras', page.locator('.cifra').count() == 3)
            go(page, '#/cobros-app', 1200)
            check('cobros · se abren', 'Últimos cobros' in page.inner_text('#app'))
            check('sin errores de JavaScript (centro)', not errors, errors[:3])
            ctx.close()

            # ---------------------------------------------------------------- instructor
            ctx, page, errors = phone()
            login(page, 'diver_instr1'); go(page, '#/', 1500)
            check('instructor · sin Solicitudes', tabs(page) == ['Hoy', 'Agenda', 'Escanear', 'Más'], tabs(page))
            check('instructor · «Hoy» sin cifras de solicitudes', page.locator('.cifras .cifra').count() == 2)
            go(page, '#/solicitudes', 1000)
            check('instructor · #/solicitudes vuelve a Hoy', page.evaluate('location.hash') in ('#/', ''))
            go(page, '#/mas', 1100); m = page.inner_text('#app')
            check('instructor · sin Cobros, Equipo ni borrar la cuenta', not any(x in m for x in ('Cobros', 'Equipo y perfiles', 'Borrar mi cuenta para siempre')), m[:300])
            go(page, f'#/salida?id={sl_hoy}', 1300)
            check('instructor · pasa lista', page.locator('.marca-check').count() == 4 and 'Cancelar la salida' not in page.inner_text('#app'))
            check('sin errores de JavaScript (instructor)', not errors, errors[:3])
            ctx.close()

            # ---------------------------------------------------------------- freelance
            ctx, page, errors = phone()
            login(page, 'pro_libre1'); go(page, '#/agenda?vista=mes', 1500)
            check('freelance · pestañas', tabs(page) == ['Hoy', 'Agenda', 'Escanear', 'Solicitudes', 'Más'], tabs(page))
            page.locator(f'.dia[data-dia="{day(3)}"]').click(); page.wait_for_timeout(500)
            page.click('[data-bloquear]'); page.wait_for_timeout(600); page.click('[data-part="full"]'); page.wait_for_timeout(1500)
            check('freelance · bloquear un día con un toque', page.locator(f'.dia.bloqueado[data-dia="{day(3)}"]').count() == 1)
            shot(page, '11-freelance-agenda')
            d = t.make_diver('cliente1'); d.post('/api/account/profile', {'phone': '+34 633 000 001'})
            r = d.post('/api/bookings', {'service_id': sf, 'days': [day(1)], 'part': 'full', 'participants': 1})
            if r.status == 200:
                srv.sql("UPDATE bookings SET status='confirmed', booking_date=? WHERE id=?", (day(0), r.json['id']))
                srv.sql('UPDATE booking_days SET local_date=? WHERE booking_id=?', (day(0), r.json['id']))
            go(page, '#/', 1500)
            check('freelance · el trabajo de hoy con Llamar, WhatsApp y Cómo llegar', r.status == 200 and page.locator('[data-trabajo="wa"]').count() == 1, (r.status, r.json if r.status != 200 else ''))
            shot(page, '12-freelance-hoy')
            check('sin errores de JavaScript (freelance)', not errors, errors[:3])
            ctx.close()

            # ---------------------------------------------------------------- languages
            for lang in ('en', 'fr'):
                ctx, page, errors = phone(lang={'en': 'en-GB', 'fr': 'fr-FR'}[lang])
                page.add_init_script(f"localStorage.setItem('wod-language','{lang}'); localStorage.setItem('wd-i18n-debug','1');")
                login(page, 'center_pro1')
                misses = set()
                for r_ in PRO + [f'#/salida?id={sl_hoy}', f'#/contar?id={sl_hoy}', f'#/resumen-barco?id={sl_hoy}', '#/cerrar-cuenta']:
                    go(page, r_, 1300)
                    misses |= set(page.evaluate('window.__wdI18nMisses ? [...window.__wdI18nMisses] : []'))
                go(page, '#/agenda?vista=semana', 1200); misses |= set(page.evaluate('window.__wdI18nMisses ? [...window.__wdI18nMisses] : []'))
                go(page, '#/agenda?vista=dia', 1200); misses |= set(page.evaluate('window.__wdI18nMisses ? [...window.__wdI18nMisses] : []'))
                shot(page, f'13-hoy-{lang}') if lang == 'en' else None
                pack = json.loads((Path(__file__).resolve().parents[2] / 'public' / 'idiomas' / f'{lang}.json').read_text(encoding='utf-8'))['exact']
                want = [pack.get(x) for x in ('Hoy', 'Agenda', 'Escanear', 'Solicitudes', 'Más')]
                check(f'idioma {lang} · las cinco pestañas traducidas', None not in want and tabs(page) == want, (tabs(page), want))
                check(f'idioma {lang} · todo traducido en las pantallas PRO', not misses, json.dumps(sorted(misses), ensure_ascii=False))
                ctx.close()

            # ---------------------------------------------------------------- 360 px
            ctx, page, errors = phone(360, 800)
            login(page, 'center_pro1')
            wide = []
            for size in ('normal', 'enorme'):
                page.evaluate(f"localStorage.setItem('wda-tamano','{size}')")
                for r_ in PRO + [f'#/salida?id={sl_hoy}', f'#/contar?id={sl_hoy}', f'#/resumen-barco?id={sl_hoy}']:
                    go(page, r_, 1100)
                    w = page.evaluate('[document.scrollingElement.scrollWidth, innerWidth]')
                    if w[0] > w[1]: wide.append((size, r_, w))
            check('360 px · nada se sale de la pantalla (Normal y Enorme)', not wide, wide)
            page.evaluate("localStorage.setItem('wda-tamano','normal')")
            check('sin errores de JavaScript (360 px)', not errors, errors[:3])
            ctx.close()

            # ---------------------------------------------------------------- close the account in the app and reopen it
            ctx, page, errors = phone()
            login(page, 'center_otro1')
            srv.sql("UPDATE bookings SET status='cancelled' WHERE id=?", (b_other,))
            go(page, '#/cerrar-cuenta', 1300)
            check('cerrar cuenta · explica los 6 meses', 'Guardamos todo durante 6 meses' in page.inner_text('#app'))
            shot(page, '14-cerrar-cuenta')
            page.fill('#cc-pw', PW); page.click('#cc-ok'); page.wait_for_timeout(1800)
            check('cerrar cuenta · cerrada y fuera de la sesión', srv.sql('SELECT active FROM centers WHERE id=?', (oid,))[0]['active'] == 0)
            login(page, 'center_otro1'); go(page, '#/', 1400)
            check('cerrar cuenta · al entrar: «Reabrir mi cuenta»', page.locator('#wda-reabrir').count() == 1, page.inner_text('#app')[:200])
            shot(page, '15-cuenta-cerrada')
            page.click('#wda-reabrir'); page.wait_for_timeout(1800)
            check('cerrar cuenta · reabierta con todo', srv.sql('SELECT active FROM centers WHERE id=?', (oid,))[0]['active'] == 1 and 'Tu día' in page.inner_text('#app'))
            check('sin errores de JavaScript (cerrar cuenta)', not errors, errors[:3])
            ctx.close()
            browser.close()
    finally:
        srv.stop()

    width = max(len(n) for n, _, _ in checks)
    for name, ok, detail in checks:
        print(f"{'OK ' if ok else 'MAL'} {name.ljust(width)} {'' if ok else detail}")
    bad = [c_ for c_ in checks if not c_[1]]
    print(f'\n{len(checks) - len(bad)}/{len(checks)} comprobaciones correctas')
    return 1 if bad else 0


if __name__ == '__main__':
    out = None
    if '--shots' in sys.argv:
        out = Path(sys.argv[sys.argv.index('--shots') + 1])
    sys.exit(run(out))
