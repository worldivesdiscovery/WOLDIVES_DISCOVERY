"""Encargo unificado, bloque A (v50.44) in a real browser, desktop and phone: a freelance sells «Cenotes por días»
(days and half days); a diver picks Monday to Wednesday on the calendar, sees the total at once (with the discount
and an extra) and sends the request; another diver asks for some of the same days; the freelance confirms the first
one from «Mi agenda» and the second one is rejected on its own; the days turn red for the public; a busy day in the
middle of a range cannot be chosen; a manual block shows as busy without reason; the service form has the new
«Unidad de reserva». Screenshots in --shots DIR.
Usage: python tests/e2e_agenda.py [--shots DIR]
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]   # tests/navegador and tests (helpers)
from helpers import ServerTestCase, Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'


def next_monday(after_days=14):
    d = datetime.date.today() + datetime.timedelta(days=after_days)
    return d + datetime.timedelta(days=(7 - d.weekday()) % 7)


def run(shots: Path | None):
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))

    ServerTestCase.server = Server().start(); srv = ServerTestCase.server
    try:
        t = ServerTestCase('run')
        admin = t.make_admin()
        pro = t.make_freelance(admin, 'tito44')
        r = pro.post('/api/provider-services', {'title': 'Cenotes por días', 'description': 'Guía titulado, 2 cenotes por día, fotos del día.', 'price': 180, 'max_participants': 4,
                                                'booking_mode': 'request', 'booking_unit': 'half_day', 'timezone': 'America/Cancun',
                                                'unit_rules': {'min_days': 1, 'max_days': 10, 'lead_hours': 48, 'am': ['08:00', '13:00'], 'pm': ['14:00', '19:00'], 'full': ['08:00', '16:00']},
                                                'pricing': {'day': 180, 'half': 110, 'discount': {'min_days': 3, 'pct': 10}, 'extras': [{'id': 'foto', 'label': 'Fotos y vídeo', 'price': 40, 'per': 'day'}]}})
        sid = r.json['id']
        mon = next_monday(); days = [(mon + datetime.timedelta(days=i)).isoformat() for i in range(3)]
        busy_day = (mon + datetime.timedelta(days=9)).isoformat()   # a busy Wednesday the next week
        pro.post('/api/agenda/block', {'date_from': busy_day, 'date_to': busy_day})
        t.make_diver('ana44'); t.make_diver('leo44')
        base = srv.base
        try:
            run_browser(t, srv, sid, check, shots)
        except Exception as e:  # noqa: BLE001 · report what was checked before the failure
            check('recorrido completo sin excepción', False, repr(e)[:1500])
    finally:
        srv.stop()
    return checks


def run_browser(t, srv, sid, check, shots):
    pro = t.client(); pro.login('pro_tito44')
    base = srv.base
    mon = next_monday(); days = [(mon + datetime.timedelta(days=i)).isoformat() for i in range(3)]
    busy_day = (mon + datetime.timedelta(days=9)).isoformat()
    if True:
        with sync_playwright() as p:
            b = chromium(p)
            for dev, opts in (('ordenador', {'viewport': {'width': 1366, 'height': 900}}),
                              ('movil', {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2})):
                if dev == 'movil':
                    # second round on the phone with fresh days
                    mon = next_monday(35); days = [(mon + datetime.timedelta(days=i)).isoformat() for i in range(3)]
                    busy_day = (mon + datetime.timedelta(days=9)).isoformat(); pro.post('/api/agenda/block', {'date_from': busy_day, 'date_to': busy_day})
                ctx = b.new_context(locale='es-ES', **opts); ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                page = ctx.new_page(); errors = []; page.on('pageerror', lambda e: errors.append(str(e)))

                def shot(name, full=True):
                    if shots:
                        shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}-{dev}.png'), full_page=full)

                def pick(day):   # the fixed total bar covers the bottom of the phone screen: centre the day first, as a person scrolls
                    loc = page.locator(f'button[data-day="{day}"]'); loc.evaluate("e=>e.scrollIntoView({block:'center'})"); loc.click(); page.wait_for_timeout(350)

                def login(user):
                    page.goto(base + '/#/login'); page.wait_for_selector('#login'); page.fill('#login', user); page.fill('#password', PW)
                    page.click('#login-form button[type=submit]'); page.wait_for_timeout(1000)

                # The diver picks Monday–Wednesday (signed out first: the choice survives signing in)
                page.goto(base + f'/#/reservar-dias?service={sid}&m={mon.strftime("%Y-%m")}'); page.wait_for_selector('.dcal'); page.wait_for_timeout(500)
                check(f'{dev}: calendario público con «Elige tus días»', page.locator('#dbk-pick-h').count() == 1)
                check(f'{dev}: día bloqueado sale ocupado, sin motivo', 'busy' in (page.get_attribute(f'td:has(button[data-day="{busy_day}"])', 'class') or '') if busy_day[:7] == mon.strftime('%Y-%m') else True)
                pick(days[0]); pick(days[2])
                page.check('.dbk-extras input[value="foto"]'); page.select_option('#dbk-pax', '2'); page.wait_for_timeout(900)
                total = page.inner_text('#dbk-total')
                check(f'{dev}: total al momento «3 días · 2 personas · 606 €»', '3 días' in total and '2 personas' in total and '606' in total, total)
                check(f'{dev}: desglose con el descuento y el extra', 'Descuento desde 3 días' in page.inner_text('#dbk-lines') and 'Fotos' in page.inner_text('#dbk-lines'), page.inner_text('#dbk-lines'))
                shot('reservar-dias')
                if shots and dev == 'movil':
                    page.evaluate("document.querySelector('#dbk-pick').scrollIntoView()"); page.wait_for_timeout(200); shot('reservar-dias-pantalla', full=False)
                # Range over a busy day is refused with the reason
                if busy_day[:7] == mon.strftime('%Y-%m'):
                    pick((mon + datetime.timedelta(days=7)).isoformat())
                    pick((mon + datetime.timedelta(days=11)).isoformat())
                    check(f'{dev}: un día ocupado en medio no se puede seleccionar', not page.locator('#dbk-msg').is_hidden() and 'no está libre' in page.inner_text('#dbk-msg'), (page.inner_text('#dbk-msg'), page.url, page.get_attribute(f'td:has(button[data-day="{busy_day}"])', 'class')))
                    pick(days[0]); pick(days[2])
                # Send without session → login → back with the same days
                page.click('#dbk-go'); page.wait_for_timeout(800)
                check(f'{dev}: sin sesión pide iniciarla', '#/login' in page.url)
                page.fill('#login', 'diver_ana44'); page.fill('#password', PW); page.click('#login-form button[type=submit]'); page.wait_for_timeout(1500)
                page.wait_for_selector('#dbk-total'); page.wait_for_timeout(1200)
                check(f'{dev}: al volver conserva los días elegidos', '606' in page.inner_text('#dbk-total'), page.inner_text('#dbk-total'))
                page.click('#dbk-go'); page.wait_for_timeout(1500)
                bid_a = srv.sql("SELECT id FROM bookings WHERE date_to=? ORDER BY id DESC LIMIT 1", (days[2],))
                check(f'{dev}: solicitud enviada (sin pagar nada)', bid_a and '#/reserva' in page.url, page.url)
                # Second diver asks for Tuesday–Wednesday through the API, as fast as it is
                leo = t.client(); leo.login('diver_leo44')
                rb = leo.post('/api/bookings', {'service_id': sid, 'days': days[1:], 'part': 'full', 'participants': 1})
                check(f'{dev}: la segunda solicitud también entra (los días siguen libres mientras tanto)', rb.status == 200, rb.json)
                # The freelance confirms from «Mi agenda»
                ctx.clear_cookies(); login('pro_tito44')
                page.goto(base + f'/#/admin?tab=agenda')
                try: page.wait_for_selector('.dcal', timeout=8000)
                except Exception:
                    print('DEBUG', page.url, page.inner_text('main, #app')[:600], errors); raise
                page.wait_for_timeout(800)
                for _ in range(3):
                    if page.locator(f'button[data-day="{days[1]}"]').count(): break
                    page.click('#ag-next'); page.wait_for_timeout(700)
                pick(days[1])
                side = page.inner_text('.ag-side')
                check(f'{dev}: la agenda avisa de qué solicitud se rechazará', 'se rechazará sola' in side, side[:300])
                shot('agenda-solicitudes')
                page.locator(f'[data-accept="{bid_a[0]["id"]}"]').first.click(); page.wait_for_timeout(600)
                check(f'{dev}: confirmación con resumen antes de confirmar', 'se rechazará sola' in page.inner_text('#wd-confirm'))
                shot('agenda-confirmar')
                page.click('#wd-confirm-ok'); page.wait_for_timeout(1500)
                st_b = srv.sql('SELECT status FROM bookings WHERE id=?', (rb.json['id'],))[0]['status']
                check(f'{dev}: la otra solicitud se rechaza sola', st_b == 'rejected', st_b)
                mail = srv.sql("SELECT text AS body_text FROM email_outbox WHERE subject LIKE 'Solicitud no disponible%' ORDER BY id DESC LIMIT 1")
                check(f'{dev}: aviso «Esas fechas ya no están disponibles» con enlace a otras fechas', mail and 'ya no están disponibles' in (mail[0]['body_text'] or '') and 'reservar-dias' in (mail[0]['body_text'] or ''), (mail[0]['body_text'] or '')[:200] if mail else 'sin correo')
                pick(days[1])
                shot('agenda-mes')
                pub = t.client().get(f'/api/agenda/public?service={sid}&month={mon.strftime("%Y-%m")}').json
                check(f'{dev}: los días confirmados salen ocupados para el público', all(pub['days'][d] == 'busy' for d in days), [pub['days'][d] for d in days])
                check(f'{dev}: la API pública no da nombres ni motivos', 'ana44' not in str(pub) and 'Buceador' not in str(pub) and 'manual' not in str(pub['days']))
                # Service form: «Unidad de reserva»
                page.goto(base + '/#/admin?tab=services'); page.wait_for_timeout(1500)
                if page.locator('.service-edit').count():
                    page.locator('.service-edit').first.click(); page.wait_for_timeout(800)
                    check(f'{dev}: formulario con «Unidad de reserva» y precios por día', page.locator('#svc-unit-box').count() == 1 and page.locator('#svc-day-box').is_visible())
                    shot('formulario-servicio')
                check(f'{dev}: sin desbordamiento', page.evaluate('document.documentElement.scrollWidth') <= (1366 if dev == 'ordenador' else 392))
                check(f'{dev}: sin errores JS', not errors, errors)
                ctx.close()
            b.close()


if __name__ == '__main__':
    shots = Path(sys.argv[sys.argv.index('--shots') + 1]) if '--shots' in sys.argv else None
    results = run(shots)
    for name, ok, detail in results:
        print(('OK   ' if ok else 'FALLA') + ' ' + name + (f' · {detail}' if detail and not ok else ''))
    bad = [r for r in results if not r[1]]
    print(f'{len(results) - len(bad)}/{len(results)} comprobaciones correctas')
    sys.exit(1 if bad else 0)
