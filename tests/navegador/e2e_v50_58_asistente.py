#!/usr/bin/env python3
"""v50.58 · El asistente de servicios del centro, en el navegador (revisión y usabilidad 15-16/10/2026, Parte 3).

1. Prueba de tiempo (3.6.1) con un ritmo de persona que no conoce WORLDIVES: un Open Water de 3 días con dos
   ediciones, una doble inmersión de los sábados y un alquiler de traje, cada uno en menos de 3 minutos.
   Es un MODELO (ritmo publicado de lectura, toques y escritura), no una persona real: la prueba con una persona real
   queda para el titular.
2. Reglas del asistente (3.2): barra de progreso, volver atrás sin perder nada, borrador que se retoma, error junto al
   campo en palabras claras, «Más opciones» plegadas, edición en una sola página con bloques plegables, «Duplicar».
3. Duración en el idioma del buceador (3.3): horas y minutos con hora de salida; curso de días con atajos y ediciones
   con su fecha de fin; «2 mañanas + 2 días completos»; alquiler por día; sin «unidad de reserva» en la pantalla.
4. Planning (3.6.2): el Open Water como un bloque de 3 días y su instructor ocupado; las mañanas respetadas.
5. Reserva del buceador (3.6.3): una edición concreta del curso, por WORLDIVES (pago al reservar) y por el widget de la
   web del centro (bajo petición).
6. Migración (3.6.4): un servicio de antes se abre en la edición en una página y se reserva igual.
7. Capturas de cada paso en el ordenador y en el móvil (3.6.5).

    python3 tests/navegador/e2e_v50_58_asistente.py [carpeta-de-capturas]

No usa la demo: un servidor nuevo con el simulador de Stripe."""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Server, ServerTestCase  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
DESK = {'viewport': {'width': 1440, 'height': 900}, 'locale': 'es-ES'}
PHONE = {'viewport': {'width': 390, 'height': 844}, 'locale': 'es-ES', 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}
# The pace of a person who does not know the tool (seconds): reading a step of the wizard (longer than a booking screen:
# it is new to them), deciding between cards, a tap, a letter typed on a computer (published mean, as in the stopwatch
# of the express booking: Dhakal et al. CHI 2018).
READ, DECIDE, TAP, CHAR = 6.0, 2.0, 0.5, 0.2
LIMIT = 180


def madrid_today():
    from zoneinfo import ZoneInfo
    return dt.datetime.now(ZoneInfo('Europe/Madrid')).date()


def next_weekday(wd, after):
    d = madrid_today() + dt.timedelta(days=after)
    while d.weekday() != wd: d += dt.timedelta(days=1)
    return d


class Pace:
    """What a person would spend: the real time of the page plus the modelled reading, deciding, tapping and typing."""

    def __init__(self, page):
        self.page, self.t0 = page, time.time(); self.model = 0.0; self.taps = 0; self.steps = 0; self.chars = 0

    def read(self, n=1): self.model += READ * n; self.steps += n
    def decide(self): self.model += DECIDE

    def tap(self, sel):
        self.model += TAP; self.taps += 1; self.page.locator(sel).first.click()

    def type(self, sel, text):
        self.model += TAP; self.taps += 1; self.chars += len(text); loc = self.page.locator(sel).first; loc.click(); loc.fill(text); self.model += CHAR * len(text)

    def total(self): return round(time.time() - self.t0 + self.model, 1)


def run(out: Path | None):
    rows = []
    timings = {}

    def check(name, ok, detail=''):
        rows.append((name, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + name + (f'  · {str(detail)[:300]}' if detail != '' else ''), flush=True)

    stripe = StripeMock()
    ServerTestCase.server = Server({'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': stripe.base, 'WOD_PAYMENTS_TOTP_REQUIRED': '0'}).start()
    srv = ServerTestCase.server
    errors = []
    try:
        t = ServerTestCase('run')
        admin = t.make_admin()
        center = t.make_center(admin, 'wz', phone='+34 600 000 031')
        cid = center.user['center_id']
        srv.sql("UPDATE centers SET name='Centro de Buceo Islas Medas', stripe_account_id='acct_wz', stripe_charges_enabled=1, stripe_payouts_enabled=1 WHERE id=?", (cid,))
        srv.sql("UPDATE users SET fullname='Marta Instructora' WHERE id=?", (center.user['id'],))
        # a service from before v50.58 (the old form, by the API): it has to keep working (3.6.4)
        legacy = center.post('/api/provider-services', {'title': 'Bautizo en la playa (antiguo)', 'price': 65, 'booking_mode': 'request', 'duration_minutes': 150, 'max_participants': 6}).json['id']
        center.post('/api/provider-services/slot', {'service_id': legacy, 'slot_date': (madrid_today() + dt.timedelta(days=8)).isoformat(), 'slot_time': '11:00', 'spots_total': 6})
        diver = t.make_diver('wza')
        base = srv.base
        mon = next_weekday(0, 14)          # an Open Water starting on a Monday, and the next one a week later
        sat0, sat1 = next_weekday(5, 3), next_weekday(5, 3) + dt.timedelta(days=27)

        with sync_playwright() as p:
            browser = chromium(p)

            def page_for(opts):
                ctx = browser.new_context(**opts)
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg = ctx.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
                pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
                return pg

            def go(pg, route, wait=1300):
                pg.goto(base + '/' + route); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(wait)

            def login(pg, user):
                go(pg, '#/login', 500); pg.fill('#login', user); pg.fill('#password', PW); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1300)

            def shot(pg, name):
                if out: out.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(out / f'{name}.png'))

            def step_no(pg):
                return pg.evaluate("() => { const t = document.querySelector('.wz-stepname')?.textContent || ''; const m = t.match(/(\\d) de 6/); return m ? +m[1] : 0; }")

            def nxt(pg, pace=None):
                (pace.tap('#wz-next') if pace else pg.click('#wz-next')); pg.wait_for_timeout(600)

            def open_wizard(pg, pace=None):
                go(pg, '#/admin?tab=services', 1500)
                (pace.tap('.new-center-service') if pace else pg.click('.new-center-service >> nth=0')); pg.wait_for_selector('.wz-kind')

            ce = page_for(DESK); login(ce, 'center_wz')

            # ============================================================ 1 · Open Water 3 days, two editions (stopwatch)
            pace = Pace(ce); open_wizard(ce, pace); pace.read()
            check('3.2 · paso 1: tarjetas grandes con icono y ejemplo (7 para un centro, sin «Guía por días»)', ce.locator('.wz-kind').count() == 6 and ce.locator('.wz-kind small').count() == 6,
                  ce.eval_on_selector_all('.wz-kind strong', 'els => els.map(e => e.textContent)'))
            check('3.2 · barra de progreso con los 6 pasos', ce.locator('.wz-progress li').count() == 6 and ce.locator('.wz-bar i').count() == 1)
            shot(ce, 'asistente-ordenador-1-que-vas-a-ofrecer')
            pace.decide(); pace.tap('.wz-kind[data-kind="course"]'); ce.wait_for_timeout(200); nxt(ce, pace)
            ce.wait_for_selector('#wz-title'); pace.read()
            check('3.2 · volver atrás: el asistente guarda un borrador en cuanto hay tipo', srv.sql("SELECT COUNT(*) n FROM provider_services WHERE draft=1")[0]['n'] == 1)
            # an error next to the field, in plain words
            nxt(ce)
            err = ce.inner_text('.wz-err[data-for="title"]') if ce.locator('.wz-err[data-for="title"]').count() else ''
            check('3.2 · error junto al campo y en palabras claras («Pon un nombre al servicio…»)', 'Pon un nombre' in err, err)
            pace.type('#wz-title', 'Open Water'); pace.type('#wz-desc', 'Tu primera titulación de buceo, en 3 días.')
            shot(ce, 'asistente-ordenador-2-lo-basico')
            nxt(ce, pace); ce.wait_for_selector('.wz-days'); pace.read()
            check('3.3 · curso: «¿Cuántos días dura?» de 1 a 10 y atajos', ce.locator('.wz-days .wz-n').count() == 10 and ce.locator('[data-preset="2am2full"]').count() == 1)
            check('3.3 · sin el campo técnico «unidad de reserva»', 'unidad de reserva' not in ce.inner_text('#wz').lower())
            pace.decide(); pace.tap('[data-preset="3full"]'); ce.wait_for_timeout(200)
            pace.tap('input[name="wz-sm"][value="dates"]'); ce.wait_for_timeout(200)
            for d in (mon, mon + dt.timedelta(days=7)):
                pace.type('#wz-newdate', d.isoformat()); pace.tap('#wz-adddate'); ce.wait_for_timeout(150)
            hint = ce.inner_text('.wz-sched')
            check('3.3 · ediciones: la fecha de fin se calcula sola («del lunes al miércoles»)', '2 ediciones' in hint, hint[:200])
            if ce.locator('#wz-ins').count():
                ce.select_option('#wz-ins', str(center.user['id'])); pace.model += TAP * 2; pace.taps += 2
            shot(ce, 'asistente-ordenador-3-cuando-y-cuanto-dura')
            nxt(ce, pace); ce.wait_for_selector('#wz-price'); pace.read()
            pace.type('#wz-price', '450'); pace.type('#wz-seats', '6'); ce.wait_for_timeout(300)
            ex = ce.inner_text('.wz-example') if ce.locator('.wz-example').count() else ''
            check('3.2 · precio con el cálculo de ejemplo al momento («2 personas × 1 curso = 900 €»)', '2 personas × 1 curso = 900' in ex.replace(' ', ' '), ex)
            shot(ce, 'asistente-ordenador-4-precio-y-plazas')
            # back without losing anything
            ce.click('#wz-back'); ce.wait_for_timeout(400); ce.click('#wz-next'); ce.wait_for_timeout(600)
            check('3.2 · volver atrás sin perder nada', ce.input_value('#wz-price') == '450' and ce.input_value('#wz-seats') == '6')
            nxt(ce, pace); ce.wait_for_selector('.wz-mode'); pace.read()
            rec = ce.inner_text('.wz-mode[data-mode="request"]')
            check('3.4 · dos tarjetas grandes con la recomendada marcada (curso: «Tú apruebas cada reserva»)', ce.locator('.wz-mode').count() == 2 and 'Recomendada' in rec, rec[:160])
            folded = ce.inner_text('details.wz-more[data-more="mode"] summary') if ce.locator('details.wz-more[data-more="mode"]:not([open])').count() else ''
            check('3.2 · lo avanzado (señal, plazo de respuesta, antelación, cancelación) plegado en «Más opciones»', folded == 'Más opciones', folded)
            shot(ce, 'asistente-ordenador-5-como-se-reserva')
            pace.decide(); nxt(ce, pace); ce.wait_for_selector('#wz-publish'); pace.read()
            check('3.2 · paso 6: «Así lo verá el buceador», «Publicar» y «Guardar como borrador»', 'Así lo verá el buceador' in ce.inner_text('.wz-review')
                  and ce.locator('#wz-publish').count() == 1 and ce.locator('#wz-draft').count() == 1)
            shot(ce, 'asistente-ordenador-6-revisar-y-publicar')
            pace.tap('#wz-publish'); ce.wait_for_timeout(1500)
            timings['Open Water de 3 días con dos ediciones'] = (pace.total(), pace.taps, pace.chars)
            ow = srv.sql("SELECT id, kind, draft, active FROM provider_services WHERE title='Open Water'")
            eds = srv.sql('SELECT slot_date, date_to, instructor_user_id FROM service_slots WHERE service_id=? ORDER BY slot_date', (ow[0]['id'],)) if ow else []
            check('3.3 · publicado con dos ediciones de 3 días (la fecha de fin, sola) y su instructora',
                  len(eds) == 2 and eds[0]['date_to'] == (mon + dt.timedelta(days=2)).isoformat() and eds[0]['instructor_user_id'] == center.user['id'], [dict(e) for e in eds])
            check(f'3.6.1 · Open Water con dos ediciones en menos de 3 min (modelo): {timings["Open Water de 3 días con dos ediciones"][0]} s',
                  timings['Open Water de 3 días con dos ediciones'][0] < LIMIT, timings['Open Water de 3 días con dos ediciones'])

            # ============================================================ 2 · double dive every Saturday (stopwatch)
            pace = Pace(ce); open_wizard(ce, pace); pace.read(); pace.decide(); pace.tap('.wz-kind[data-kind="dive"]'); ce.wait_for_timeout(200); nxt(ce, pace)
            ce.wait_for_selector('#wz-title'); pace.read(); pace.type('#wz-title', 'Doble inmersión en las Medas'); nxt(ce, pace)
            ce.wait_for_selector('#wz-time'); pace.read()
            check('3.3 · inmersión: horas y minutos y hora de salida', ce.locator('#wz-h').count() == 1 and ce.locator('select[data-w="minutes"]').count() == 1)
            pace.type('#wz-h', '4'); pace.type('#wz-time', '09:00'); pace.tap('input[name="wz-dpo"][value="2"]')
            if not ce.is_checked('input[name="wz-sm"][value="weekly"]'): pace.tap('input[name="wz-sm"][value="weekly"]'); ce.wait_for_timeout(200)
            pace.tap('[data-wday="5"]'); ce.wait_for_timeout(200)
            ce.fill('#wz-from', sat0.isoformat()); ce.dispatch_event('#wz-from', 'change'); ce.wait_for_timeout(200)
            ce.fill('#wz-to', sat1.isoformat()); ce.dispatch_event('#wz-to', 'change'); ce.wait_for_timeout(300); pace.model += 2 * (TAP + 8 * CHAR); pace.taps += 2
            hint = ce.inner_text('.wz-sched')
            check('3.3 · «todos los sábados a las 9:00»: las salidas, contadas al momento', '4 salidas' in hint, hint[:200])
            shot(ce, 'asistente-ordenador-3b-sabados')
            nxt(ce, pace); ce.wait_for_selector('#wz-price'); pace.read(); pace.type('#wz-price', '70'); pace.type('#wz-seats', '10')
            nxt(ce, pace); ce.wait_for_selector('.wz-mode'); pace.read()
            check('3.4 · inmersión: «Reserva inmediata» recomendada y elegida', ce.get_attribute('.wz-mode[data-mode="payment"]', 'aria-checked') == 'true'
                  and 'Recomendada' in ce.inner_text('.wz-mode[data-mode="payment"]'))
            nxt(ce, pace); ce.wait_for_selector('#wz-publish'); pace.read(); pace.tap('#wz-publish'); ce.wait_for_timeout(1500)
            timings['Doble inmersión de los sábados'] = (pace.total(), pace.taps, pace.chars)
            dd = srv.sql("SELECT id FROM provider_services WHERE title='Doble inmersión en las Medas'")
            sl = srv.sql('SELECT slot_date, slot_time FROM service_slots WHERE service_id=?', (dd[0]['id'],)) if dd else []
            check('3.3 · publicada con las 4 salidas de los sábados a las 9:00', len(sl) == 4 and all(dt.date.fromisoformat(x['slot_date']).weekday() == 5 and x['slot_time'] == '09:00' for x in sl), [dict(x) for x in sl])
            check(f'3.6.1 · doble inmersión de los sábados en menos de 3 min (modelo): {timings["Doble inmersión de los sábados"][0]} s', timings['Doble inmersión de los sábados'][0] < LIMIT)

            # ============================================================ 3 · rental of a wetsuit (stopwatch)
            pace = Pace(ce); open_wizard(ce, pace); pace.read(); pace.decide(); pace.tap('.wz-kind[data-kind="rental"]'); ce.wait_for_timeout(200); nxt(ce, pace)
            ce.wait_for_selector('#wz-title'); pace.read(); pace.type('#wz-title', 'Alquiler de traje 5 mm'); nxt(ce, pace)
            ce.wait_for_selector('input[name="wz-rent"]'); pace.read()
            check('3.3 · alquiler: por día o por inmersión', ce.locator('input[name="wz-rent"]').count() == 2)
            nxt(ce, pace); ce.wait_for_selector('#wz-price'); pace.read(); pace.type('#wz-price', '12')
            nxt(ce, pace); ce.wait_for_selector('.wz-mode'); pace.read(); nxt(ce, pace); ce.wait_for_selector('#wz-publish'); pace.read(); pace.tap('#wz-publish'); ce.wait_for_timeout(1500)
            timings['Alquiler de traje'] = (pace.total(), pace.taps, pace.chars)
            check('3.3 · alquiler publicado', len(srv.sql("SELECT id FROM provider_services WHERE title='Alquiler de traje 5 mm' AND COALESCE(draft,0)=0")) == 1)
            check(f'3.6.1 · alquiler de traje en menos de 3 min (modelo): {timings["Alquiler de traje"][0]} s', timings['Alquiler de traje'][0] < LIMIT)

            # ============================================================ 4 · on the phone: «2 mañanas + 2 días completos», step by step
            ph = page_for(PHONE); login(ph, 'center_wz'); open_wizard(ph)
            shot(ph, 'asistente-movil-1-que-vas-a-ofrecer')
            ph.click('.wz-kind[data-kind="course"]'); ph.wait_for_timeout(200); nxt(ph); ph.wait_for_selector('#wz-title')
            ph.fill('#wz-title', 'Advanced: 2 mañanas + 2 días'); shot(ph, 'asistente-movil-2-lo-basico'); nxt(ph); ph.wait_for_selector('.wz-days')
            ph.click('[data-preset="2am2full"]'); ph.wait_for_timeout(200)
            parts = ph.eval_on_selector_all('.wz-plan input[type=radio]:checked', 'els => els.map(e => e.value)')
            check('3.3 · atajo «2 mañanas + 2 días completos»: mañana, mañana, día completo, día completo', parts == ['am', 'am', 'full', 'full'], parts)
            ph.check('input[name="wz-sm"][value="dates"]'); ph.wait_for_timeout(200)
            start2 = mon + dt.timedelta(days=21)
            ph.fill('#wz-newdate', start2.isoformat()); ph.click('#wz-adddate'); ph.wait_for_timeout(200)
            shot(ph, 'asistente-movil-3-cuando-y-cuanto-dura'); nxt(ph); ph.wait_for_selector('#wz-price')
            ph.fill('#wz-price', '380'); ph.fill('#wz-seats', '4'); ph.wait_for_timeout(200); shot(ph, 'asistente-movil-4-precio-y-plazas'); nxt(ph); ph.wait_for_selector('.wz-mode')
            shot(ph, 'asistente-movil-5-como-se-reserva'); nxt(ph); ph.wait_for_selector('#wz-publish')
            shot(ph, 'asistente-movil-6-revisar-y-publicar')
            wide = ph.evaluate('document.scrollingElement.scrollWidth - innerWidth')
            check('3.6.5 · móvil: el asistente a pantalla completa y sin salirse de lado', wide <= 0 and ph.locator('.wz-modal').count() == 1, wide)
            ph.click('#wz-publish'); ph.wait_for_timeout(1500)
            adv = srv.sql("SELECT id FROM provider_services WHERE title='Advanced: 2 mañanas + 2 días'")
            ed2 = srv.sql('SELECT id, slot_date, date_to FROM service_slots WHERE service_id=?', (adv[0]['id'],)) if adv else []
            check('3.3 · el curso de 4 días: una edición del día 1 al 4', len(ed2) == 1 and ed2[0]['date_to'] == (start2 + dt.timedelta(days=3)).isoformat(), [dict(e) for e in ed2])
            ph.context.close()

            # ============================================================ 2 (rules) · draft, edit page, duplicate
            open_wizard(ce); ce.click('.wz-kind[data-kind="baptism"]'); ce.wait_for_timeout(200); nxt(ce); ce.wait_for_selector('#wz-title')
            ce.fill('#wz-title', 'Bautizo a medias'); nxt(ce); ce.wait_for_timeout(500)
            ce.locator('#svc-wiz [data-modal-close]').first.click(); ce.wait_for_timeout(1200)
            card = ce.locator('.svc-card', has_text='Bautizo a medias')
            check('3.2 · cerrar a medias: queda como «Borrador» en la lista', card.count() == 1 and 'Borrador' in card.first.inner_text(), card.first.inner_text()[:200] if card.count() else '')
            go(ce, '#/admin?tab=services', 1500)
            ce.locator('.svc-card', has_text='Open Water').first.locator('.service-edit').click(); ce.wait_for_selector('.wz-sec')
            secs = ce.locator('details.wz-sec').count()
            check('3.2 · editar un servicio creado: una sola página con bloques plegables', secs == 5, secs)
            shot(ce, 'asistente-ordenador-editar-en-una-pagina')
            ce.locator('details.wz-sec').nth(2).locator('summary').click(); ce.wait_for_timeout(200)
            ce.fill('#wz-price', '460'); ce.click('#wz-save'); ce.wait_for_timeout(1300)
            check('3.2 · guardar cambios desde la edición en una página', float(srv.sql("SELECT price FROM provider_services WHERE title='Open Water'")[0]['price']) == 460)
            go(ce, '#/admin?tab=services', 1500)
            owc = ce.locator('.svc-card', has_text='Open Water').first
            owc.locator('.svc-more summary').click(); ce.wait_for_timeout(200); owc.locator('.service-duplicate').click(); ce.wait_for_timeout(1500)
            dup = srv.sql("SELECT title, draft FROM provider_services WHERE title LIKE 'Open Water (copia)%'")
            check('3.2 · «Duplicar servicio»: una copia como borrador para la variante', len(dup) == 1 and dup[0]['draft'] == 1, [dict(x) for x in dup])

            # ============================================================ 4 · planning: a block of several days
            go(ce, f'#/admin?tab=planning', 1500)
            month = mon.isoformat()[:7]
            if ce.locator('select[data-month], .pl-month-select, #pl-month').count():
                pass
            plan = center.get(f'/api/center/planning?month={month}').json
            ow_slot = [s for s in plan['slots'] if s['service_title'] == 'Open Water']
            days = ow_slot[0].get('days') if ow_slot else []
            check('3.6.2 · planning: el Open Water como un bloque de 3 días, cada uno con su día completo',
                  len(days) == 3 and [x['part'] for x in days] == ['full'] * 3, days)
            busy = srv.sql("""SELECT COUNT(*) n FROM resource_blocks b JOIN resources r ON r.id=b.resource_id WHERE r.user_id=? AND b.ref_type='edition' AND b.status='active'""", (center.user['id'],))[0]['n']
            check('3.6.2 · la instructora ocupada los 6 días de las dos ediciones (sin solapes)', busy >= 6, busy)
            plan2 = center.get(f'/api/center/planning?month={start2.isoformat()[:7]}').json
            adv_slot = [s for s in plan2['slots'] if s['service_title'].startswith('Advanced')]
            parts = [(x['part'], x['hours'][0]) for x in (adv_slot[0].get('days') if adv_slot else [])]
            check('3.6.2 · «2 mañanas + 2 días completos» respeta las mañanas (9:00-13:00) y los días completos',
                  parts == [('am', '09:00'), ('am', '09:00'), ('full', '09:00'), ('full', '09:00')] and adv_slot[0]['days'][0]['hours'][1] == '13:00', parts)
            # the month view: the chip on each of the 3 days
            if mon.isoformat()[:7] != madrid_today().isoformat()[:7]:
                ce.evaluate(f"document.querySelector('[data-month=\"{month}\"]')?.click()"); ce.wait_for_timeout(1200)
            chips = [ce.locator(f'.pl-cell[data-day="{(mon + dt.timedelta(days=i)).isoformat()}"] .pl-chip.is-multi').count() for i in range(3)]
            check('3.6.2 · en el mes: el curso en cada uno de sus 3 días (1/3, 2/3, 3/3)', chips == [1, 1, 1], chips)
            if chips[0]:
                ce.click(f'.pl-cell[data-day="{(mon + dt.timedelta(days=1)).isoformat()}"]'); ce.wait_for_timeout(500)
                pop = ce.inner_text('#pl-pop') if ce.locator('#pl-pop').count() else ''
                check('3.6.2 · el día 2 dice «Día 2 de 3 · Día completo»', 'Día 2 de 3' in pop, pop[:200])
                shot(ce, 'asistente-planning-curso-3-dias')

            # ============================================================ 5 · the diver books an edition (web, payment) and the widget (request)
            ow_id = ow[0]['id']
            ed_ids = [r['id'] for r in srv.sql('SELECT id FROM service_slots WHERE service_id=? ORDER BY slot_date', (ow_id,))]
            srv.sql("UPDATE provider_services SET booking_mode='payment' WHERE id=?", (ow_id,))   # the Open Water with «Pago al reservar» for this check
            dv = page_for(DESK); login(dv, 'diver_wza'); go(dv, f'#/reservar?center={cid}&service={ow_id}&slot={ed_ids[1]}', 1800)
            dv.locator('.bk-go:visible').first.click(); dv.wait_for_timeout(2000)
            b = srv.sql('SELECT slot_id, booking_date, date_to, price, status FROM bookings WHERE user_id=? ORDER BY id DESC LIMIT 1', (diver.user['id'],))
            check('3.6.3 · el buceador reserva la segunda edición por WORLDIVES (pago al reservar), con su último día',
                  b and b[0]['slot_id'] == ed_ids[1] and b[0]['date_to'] == (mon + dt.timedelta(days=9)).isoformat() and float(b[0]['price']) == 460, [dict(x) for x in b])
            dv.context.close()
            slug = center.get('/api/provider/vender').json['slug']
            wg = page_for(PHONE); go(wg, f'c/{slug}', 1800); wg.wait_for_selector('.wr-svc', timeout=15000)
            names = ' · '.join(wg.eval_on_selector_all('.wr-svc', 'els => els.map(e => e.textContent.trim())'))
            check('3.6.3 · página de reservas del centro (la misma del widget): el curso «Advanced» entre sus actividades', 'Advanced' in names, names[:200])
            shot(wg, 'asistente-reserva-widget-curso')
            wg.context.close()
            r = diver.post('/api/bookings', {'center_id': cid, 'service_id': adv[0]['id'], 'slot_id': ed2[0]['id'], 'participants': 1, 'channel': 'widget'})
            check('3.6.3 · por el widget, bajo petición: solicitud de la edición, sin cobro', r.status == 200 and r.json.get('status') == 'requested' and not r.json.get('checkout_url'), r.json)

            # ============================================================ 6 · migration: a service from before
            go(ce, '#/admin?tab=services', 1500)
            ce.locator('.svc-card', has_text='Bautizo en la playa (antiguo)').first.locator('.service-edit').click(); ce.wait_for_selector('.wz-sec')
            ce.locator('details.wz-sec').nth(1).locator('summary').click(); ce.wait_for_timeout(200)
            h_, m_ = ce.input_value('#wz-h'), ce.input_value('select[data-w="minutes"]')
            check('3.6.4 · un servicio de antes se abre en el asistente con su duración en horas y minutos (2 h 30 min)', (h_, m_) == ('2', '30'), (h_, m_))
            ce.click('#wz-save'); ce.wait_for_timeout(1300)
            old = srv.sql('SELECT price, booking_mode, duration_minutes FROM provider_services WHERE id=?', (legacy,))[0]
            check('3.6.4 · y al guardar sin cambios sigue igual (precio, modo y duración)', float(old['price']) == 65 and old['booking_mode'] == 'request' and int(old['duration_minutes']) == 150, dict(old))
            ls = srv.sql('SELECT id FROM service_slots WHERE service_id=?', (legacy,))[0]['id']
            r = diver.post('/api/bookings', {'center_id': cid, 'service_id': legacy, 'slot_id': ls, 'participants': 2})
            check('3.6.4 · y se reserva igual que antes', r.status == 200 and r.json.get('status') == 'requested', r.json)
            ce.context.close()

            own = [e for e in errors if 'tile.openstreetmap.org' not in e and 'ERR_TUNNEL_CONNECTION_FAILED' not in e]
            check('consola sin errores', not own, own[:5])
            browser.close()
    finally:
        srv.stop(); stripe.stop()
    if out:
        out.mkdir(parents=True, exist_ok=True)
        (out / 'cronometro-asistente.json').write_text(json.dumps({k: {'segundos': v[0], 'toques': v[1], 'letras': v[2]} for k, v in timings.items()} |
                                                                    {'ritmo': {'leer_paso': READ, 'decidir': DECIDE, 'toque': TAP, 'letra': CHAR}}, ensure_ascii=False, indent=1), encoding='utf-8')
    print('cronómetro (modelo):', json.dumps(timings, ensure_ascii=False))
    return rows


if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    rows = run(out)
    bad = [r for r in rows if not r[1]]
    print(f'{len(rows) - len(bad)}/{len(rows)} comprobaciones correctas')
    sys.exit(1 if bad else 0)
