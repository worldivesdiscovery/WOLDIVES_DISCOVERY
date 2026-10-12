"""Encargo 2, puntos 2, 3 y 4 in a real browser (computer and phone): the centre cancels a departure for the weather
with the list of affected people before confirming; a diver picks another date from the email link without signing
in; another asks for the cancellation from «Mi reserva»; a diver asks to change the date and the centre approves it;
the options of the service form; and the waiting list on a full departure («Avisarme si queda plaza», kept spot,
booking it). Usage: python tests/e2e_departures.py [--shots DIR]
"""
from __future__ import annotations

import datetime
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from helpers import ServerTestCase, Server  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
DAY = lambda n: (datetime.date.today() + datetime.timedelta(days=n)).isoformat()


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
        center = t.make_center(admin, 'salidas', phone='+34 600 460 001')
        cid = center.user['center_id']
        sid = center.post('/api/provider-services', {'title': 'Inmersión desde barco', 'price': 45, 'booking_mode': 'request'}).json['id']
        mk = lambda d, n=8: center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': d, 'slot_time': '09:00', 'spots_total': n}).json['slot_id']
        A, B, C, D = mk(DAY(5)), mk(DAY(6)), mk(DAY(7), 1), mk(DAY(8))
        divers = {k: t.make_diver(k) for k in ('viento1', 'viento2', 'cambio3', 'lleno4', 'espera5')}

        def book(tag, slot, pax):
            r = divers[tag].post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': pax})
            center.post(f"/api/bookings/{r.json['id']}/status", {'status': 'confirmed'})
            return r.json['id']
        b1, b2 = book('viento1', A, 2), book('viento2', A, 1)
        b3 = book('cambio3', B, 1)
        book('lleno4', C, 1)
        base = srv.base
        with sync_playwright() as p:
            browser = chromium(p)

            def session(login=None, width=1366):
                ctx = browser.new_context(viewport={'width': width, 'height': 900 if width > 500 else 844}, locale='es-ES')
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                page = ctx.new_page(); errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                if login:
                    page.goto(base + '/#/login'); page.wait_for_selector('#login'); page.fill('#login', login); page.fill('#password', PW)
                    page.click('#login-form button[type=submit]'); page.wait_for_timeout(900)
                return ctx, page, errors

            def go(page, route, wait=1200):
                page.goto(base + '/' + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)

            def shot(page, name, full=True):
                if shots:
                    shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'), full_page=full)

            # ---- 2. The centre cancels departure A (computer)
            ctx, page, errors = session('center_salidas')
            go(page, f'#/manifiesto?slot={A}')
            page.click('#mf-cancel'); page.wait_for_timeout(800)
            txt = page.inner_text('#slot-cancel')
            check('cancelar: resumen «Se avisará a 2 reservas (3 buceadores)»', 'Se avisará a 2 reservas (3 buceadores)' in txt, txt[:160])
            check('cancelar: qué recibe cada uno', txt.count('Cambio de fecha o anulación sin coste') == 2)
            shot(page, 'cancelar-salida-ordenador', False)
            page.check('input[name="sc-reason"][value="sea"]'); page.fill('#sc-note', 'Mar de fondo de 2 metros')
            page.click('#sc-ok'); page.wait_for_timeout(1400)
            check('salida cancelada y aviso en el manifiesto', 'Salida cancelada' in page.inner_text('.mf-page') and srv.sql('SELECT cancelled_at FROM service_slots WHERE id=?', (A,))[0]['cancelled_at'])
            check('historial de la salida', 'Salida cancelada' in (page.locator('.mf-hist').text_content() or ''))
            check('correos a los dos buceadores', len(srv.sql("SELECT 1 FROM email_outbox WHERE template='slot_cancelled'")) == 2)
            if DAY(5)[:7] == datetime.date.today().isoformat()[:7]:
                go(page, '#/admin?tab=planning', 1500)
                cell = page.locator(f'.pl-cell[data-day="{DAY(5)}"]')
                if cell.count():
                    cell.first.click(); page.wait_for_timeout(700)
                    check('planning: etiqueta «Cancelada»', 'Cancelada' in page.inner_text('#pl-pop'))
                    shot(page, 'planning-cancelada-ordenador', False)
            check('centro sin errores JS', not errors, errors)
            ctx.close()

            # ---- 2. Diver 1 chooses another date from the email link, on a phone, without signing in
            mail = srv.sql("SELECT text FROM email_outbox WHERE template='slot_cancelled' AND to_email='viento1@diver.example.org'")[0]['text']
            link = re.search(r'#/salida-cancelada\?b=\d+&t=[A-Za-z0-9_\-]+', mail).group(0)
            ctx, page, errors = session(width=390)
            go(page, link)
            check('elección: otras fechas con plazas', page.locator('input[name="sc-alt"]').count() >= 2)
            shot(page, 'eleccion-salida-cancelada-movil')
            page.check(f'input[name="sc-alt"][value="{B}"]'); page.click('#sc-move'); page.wait_for_timeout(500)
            check('elección: confirmación con resumen', 'pasará al' in page.inner_text('#wd-confirm'))
            page.click('#wd-confirm-ok'); page.wait_for_timeout(1300)
            check('elección: reserva movida a la nueva fecha', srv.sql('SELECT slot_id FROM bookings WHERE id=?', (b1,))[0]['slot_id'] == B)
            check('móvil sin desbordamiento (elección)', page.evaluate('document.documentElement.scrollWidth') <= 392)
            check('elección sin errores JS', not errors, errors)
            ctx.close()

            # ---- 2. Diver 2 cancels from «Mi reserva» (signed in, phone)
            ctx, page, errors = session('diver_viento2', 390)
            go(page, f'#/reserva?id={b2}', 1500)
            check('mi reserva: aviso de salida cancelada', page.locator('.sc-card').count() == 1)
            page.click('.sc-card a.btn'); page.wait_for_timeout(1200)
            page.click('#sc-refund'); page.wait_for_timeout(500); page.click('#wd-confirm-ok'); page.wait_for_timeout(1300)
            check('anulación sin coste elegida', srv.sql('SELECT status FROM bookings WHERE id=?', (b2,))[0]['status'] == 'cancelled')
            check('diver 2 sin errores JS', not errors, errors)
            ctx.close()

            # ---- 3. Change of date with the centre's approval
            ctx, page, errors = session('diver_cambio3', 390)
            go(page, f'#/reserva?id={b3}', 1500)
            check('mi reserva: «Cambiar fecha»', page.locator('#bk-change-open').count() == 1)
            page.click('#bk-change-open'); page.wait_for_timeout(600)
            check('cambiar fecha: solo salidas con plazas (la completa no sale)', page.locator(f'input[name="bk-alt"][value="{C}"]').count() == 0 and page.locator(f'input[name="bk-alt"][value="{D}"]').count() == 1)
            shot(page, 'cambiar-fecha-movil', False)
            page.check(f'input[name="bk-alt"][value="{D}"]'); page.click('#bk-change-go'); page.wait_for_timeout(500)
            check('cambiar fecha: confirmación (con aprobación del centro)', 'Pediremos al centro' in page.inner_text('#wd-confirm'))
            page.click('#wd-confirm-ok'); page.wait_for_timeout(1400)
            check('solicitud pendiente visible', 'Pendiente' in page.inner_text('#bk-change'))
            check('diver 3 sin errores JS', not errors, errors)
            ctx.close()
            ctx, page, errors = session('center_salidas')
            go(page, f'#/reserva?id={b3}', 1500)
            check('centro: solicitud de cambio en la reserva', page.locator('#rq-ok').count() == 1)
            shot(page, 'centro-solicitud-cambio-ordenador')
            page.click('#rq-ok'); page.wait_for_timeout(500); page.click('#wd-confirm-ok'); page.wait_for_timeout(1300)
            check('cambio aprobado y plazas movidas', srv.sql('SELECT slot_id FROM bookings WHERE id=?', (b3,))[0]['slot_id'] == D)
            # Service form: the options of change of date and waiting list
            go(page, '#/admin?tab=services', 1600)
            page.locator('.service-edit').first.click(); page.wait_for_timeout(800)
            check('formulario del servicio: cambio de fecha y lista de espera', page.locator('#svc-resched').count() == 1 and page.locator('#svc-waitlist').count() == 1)
            page.select_option('#svc-resched', 'direct'); page.locator('#svc-waitlist').scroll_into_view_if_needed()
            shot(page, 'servicio-opciones-ordenador', False)
            page.locator('.wd-modal button[type=submit]').last.click(); page.wait_for_timeout(1300)
            check('opciones guardadas', srv.sql('SELECT reschedule_mode FROM provider_services WHERE id=?', (sid,))[0]['reschedule_mode'] == 'direct')
            check('centro (2) sin errores JS', not errors, errors)
            ctx.close()

            # ---- 4. Waiting list on the full departure C (phone)
            ctx, page, errors = session('diver_espera5', 390)
            go(page, f'#/reservar?center={cid}&service={sid}&slot={C}', 1600)
            dates = page.locator(f'.bk-date[data-date="{DAY(7)}"]')
            if dates.count(): dates.first.click(); page.wait_for_timeout(600)
            check('reserva: «Avisarme si queda plaza» en la salida completa', page.locator(f'[data-wl-join="{C}"]').count() == 1)
            page.click(f'[data-wl-join="{C}"]'); page.wait_for_timeout(1500)
            if dates.count(): page.locator(f'.bk-date[data-date="{DAY(7)}"]').first.click(); page.wait_for_timeout(600)
            check('en la lista de espera (puesto 1)', 'puesto 1' in page.inner_text('.bk-wl'))
            shot(page, 'lista-espera-movil')
            # A spot frees up: the person gets it kept and can book it
            b4 = srv.sql("SELECT id FROM bookings WHERE slot_id=? AND status='confirmed'", (C,))[0]['id']
            center.post(f'/api/bookings/{b4}/status', {'status': 'cancelled', 'reason': 'El cliente no puede venir'})
            check('aviso por email de plaza libre', srv.sql("SELECT 1 FROM email_outbox WHERE template='waitlist_spot' AND to_email='espera5@diver.example.org'"))
            page.reload(); page.wait_for_load_state('networkidle'); page.wait_for_timeout(1600)
            if dates.count(): page.locator(f'.bk-date[data-date="{DAY(7)}"]').first.click(); page.wait_for_timeout(600)
            check('reserva: «Te guardamos 1 plaza»', 'Te guardamos 1 plaza' in page.inner_text('#bk-times') if page.locator('#bk-times').count() else 'Te guardamos 1 plaza' in page.inner_text('body'))
            shot(page, 'plaza-guardada-movil')
            check('espera sin errores JS', not errors, errors)
            check('móvil sin desbordamiento (reserva)', page.evaluate('document.documentElement.scrollWidth') <= 392)
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
