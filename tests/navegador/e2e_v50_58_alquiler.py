#!/usr/bin/env python3
"""v50.58 · Alquiler de equipo como extra dentro de la inmersión, en el navegador (encargo del 16/10/2026,
docs/encargos/encargo-alquiler-equipo-16-10-2026.md). Las comprobaciones del encargo, en su orden:

1. Como centro: activar unas piezas, poner precios y un «Equipo completo»; crear «Inmersión simple» a 50 € con «Pago al
   reservar» en el asistente; el alquiler sale activado y bien en la vista previa.
2. Reservas como buceador: solo máscara y aletas (60 €); dos buceadores, uno con traje, máscara, aletas y escarpines y
   otro solo con boya; una con «Equipo completo» (también desde el modo app y desde el widget de la web del centro).
3. Botella y plomos nunca como piezas; sí «Incluido: botella y plomos».
4. Lo que ve el centro: la reserva, la lista del barco y «Equipo para preparar», con las tallas.
5. Stock: con 2 jackets M, una tercera reserva no puede pedir jacket M.
6. Cambios: el buceador añade una linterna desde Mis reservas y paga la diferencia; el centro añade una pieza en el
   mostrador como «Pagado en el centro».
7. «Bajo petición»: el equipo llega en la solicitud y se cobra solo al pagar tras aceptar.
8. Una reserva antigua (formato «código:cantidad») se sigue viendo y cobrando.
9. Pantallas en ordenador y en móvil a 360 px, web y modo app «Noche», sin errores en la consola.

    python3 tests/navegador/e2e_v50_58_alquiler.py [carpeta-de-capturas]

No usa la demo: un servidor nuevo con el simulador de Stripe (tests/stripe_mock.py)."""
from __future__ import annotations

import datetime as dt
import json
import re
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Server, ServerTestCase  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
DESK = {'viewport': {'width': 1440, 'height': 900}, 'locale': 'es-ES'}
PHONE = {'viewport': {'width': 360, 'height': 780}, 'locale': 'es-ES', 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}
# The first free size of the first marked piece still without one (the picker draws again after each choice): 1 if it chose one.
SIZES_JS = """(root) => { const host = document.querySelector(root + ' .eq-pick'); if (!host) return 0;
  for (const sel of host.querySelectorAll('select[data-size-sel]')) if (!sel.value) { const o = [...sel.options].find(x => x.value && !x.disabled);
    sel.value = o.value; sel.dispatchEvent(new Event('change', {bubbles: true})); return 1; }
  for (const row of host.querySelectorAll('.eq-size-row')) { const chips = [...row.querySelectorAll('[data-size]')];
    if (chips.length && !chips.some(c => c.getAttribute('aria-checked') === 'true')) { chips.find(c => !c.disabled).click(); return 1; } }
  return 0; }"""


def day(n):
    from zoneinfo import ZoneInfo
    return (dt.datetime.now(ZoneInfo('Europe/Madrid')).date() + dt.timedelta(days=n)).isoformat()


def run(out: Path | None):
    rows = []

    def check(name, ok, detail=''):
        rows.append((name, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + name + (f'  · {str(detail)[:300]}' if detail != '' else ''), flush=True)

    stripe = StripeMock()
    # The two-step verification of accounts with payments (V6.3.3) has its own tests; here the centre signs in with its password.
    ServerTestCase.server = Server({'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': stripe.base, 'WOD_PAYMENTS_TOTP_REQUIRED': '0'}).start()
    srv = ServerTestCase.server
    errors = []
    try:
        t = ServerTestCase('run')
        admin = t.make_admin()
        near = t.make_center(admin, 'eq', phone='+34 600 000 021')
        cid = near.user['center_id']
        srv.sql("UPDATE centers SET name='Centro de Buceo La Restinga', latitude=27.64, longitude=-17.98, stripe_account_id='acct_eq', stripe_charges_enabled=1, stripe_payouts_enabled=1 WHERE id=?", (cid,))
        divers = {k: t.make_diver(k) for k in ('eqa', 'eqb', 'eqc', 'eqd', 'eqe')}
        base = srv.base

        with sync_playwright() as p:
            browser = chromium(p)

            def page_for(opts, app=False, theme=None):
                ctx = browser.new_context(**opts)
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                if theme: ctx.add_init_script(f"try{{localStorage.setItem('wda-tema','{theme}')}}catch(e){{}}")
                pg = ctx.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
                pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' else None)
                pg.app = app
                return pg

            def go(pg, route, wait=1200):
                pg.goto(base + ('/?app=1' if pg.app else '/') + route); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(wait)

            def login(pg, user):
                go(pg, '#/login', 500); pg.fill('#login', user); pg.fill('#password', PW); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1300)

            def shot(pg, name, full=False):
                if out: out.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(out / f'{name}.png'), full_page=full)

            def sizes(pg, root):
                for _ in range(25):
                    if not pg.evaluate(SIZES_JS, root): break
                    pg.wait_for_timeout(120)

            def saved(pg):
                for _ in range(40):
                    if 'Guardado' == (pg.text_content('#eq-saved') or '').strip(): return True
                    pg.wait_for_timeout(100)
                return False

            # ============================================================ 1 · the centre, once: its rental list
            ce = page_for(DESK); login(ce, 'center_eq'); go(ce, '#/admin?tab=equipment', 1500)
            ce.wait_for_selector('.eq-cfg[data-code]')
            names = ce.eval_on_selector_all('.eq-cfg[data-code] h3', 'els => els.map(e => e.textContent.trim())')
            check('1 · Equipo de alquiler: las 11 piezas de la lista, con su icono e interruptor', len(names) == 11 and ce.locator('.eq-cfg[data-code] .eq-switch').count() == 11, names)
            check('3 · botella y plomos no salen como piezas; sí «Incluido: botella y plomos»', not any(re.search(r'botella|plomo|lastre', n, re.I) for n in names)
                  and 'Incluido: botella y plomos' in ce.inner_text('.eq-incl'), names)
            check('1 · aviso «Activa las piezas que alquilas…» mientras no hay nada', ce.locator('.notice.warning', has_text='Activa las piezas').count() == 1)
            shot(ce, 'alquiler-config-ordenador-vacio')
            # the switch without a price asks for it first
            ce.click('.eq-cfg[data-code="mask"] .eq-switch span'); ce.wait_for_timeout(300)
            check('1 · activar sin precio: pide el precio (0 € si va gratis)', not ce.is_checked('.eq-cfg[data-code="mask"] [data-f="active"]'))
            for code, price in (('mask', 5), ('fins', 5), ('boots', 3), ('wetsuit', 10), ('bcd', 8), ('regulator', 8), ('torch', 5), ('smb', 2)):
                ce.fill(f'#eq-p-{code}', str(price)); ce.press(f'#eq-p-{code}', 'Tab')
            check('1 · los precios se guardan solos', saved(ce))
            ce.click('.eq-cfg[data-code="bcd"] .eq-stock summary'); ce.fill('.eq-cfg[data-code="bcd"] [data-stock="M"]', '2'); ce.press('.eq-cfg[data-code="bcd"] [data-stock="M"]', 'Tab')
            saved(ce)
            ce.fill('#eq-kit-p', '30'); ce.press('#eq-kit-p', 'Tab'); saved(ce)
            ce.click('.eq-cfg-kit .eq-switch span'); ce.wait_for_timeout(200); saved(ce)
            cfg = near.get('/api/provider/equipment').json
            act = {i['code']: i['price'] for i in cfg['items'] if i['active']}
            check('1 · piezas activas con su precio', act == {'mask': 5, 'fins': 5, 'boots': 3, 'wetsuit': 10, 'bcd': 8, 'regulator': 8, 'torch': 5, 'smb': 2}, act)
            check('1 · «Equipo completo» a 30 € por inmersión', (cfg.get('kit') or {}).get('active') and float(cfg['kit']['price']) == 30 and cfg['kit']['price_per'] == 'dive', cfg.get('kit'))
            check('1 · stock: 2 jackets M', (cfg.get('stock') or {}).get('bcd', {}).get('M') == 2, cfg.get('stock'))
            go(ce, '#/admin?tab=equipment', 1500); shot(ce, 'alquiler-config-ordenador')

            # ---------- «Inmersión simple» a 50 € with «Pago al reservar», in the wizard
            go(ce, '#/admin?tab=services', 1500); ce.click('.new-center-service >> nth=0'); ce.wait_for_selector('.wz-kind')
            ce.click('.wz-kind[data-kind="dive"]'); ce.wait_for_timeout(200); ce.click('#wz-next'); ce.wait_for_selector('#wz-title')
            ce.fill('#wz-title', 'Inmersión simple'); ce.fill('#wz-desc', 'Una inmersión guiada desde la orilla.'); ce.click('#wz-next'); ce.wait_for_selector('#wz-time')
            ce.fill('#wz-time', '09:00')
            ce.check('input[name="wz-sm"][value="dates"]'); ce.wait_for_timeout(200)
            for n in (3, 4, 5):
                ce.fill('#wz-newdate', day(n)); ce.click('#wz-adddate'); ce.wait_for_timeout(150)
            ce.click('#wz-next'); ce.wait_for_selector('#wz-price')
            ce.fill('#wz-price', '50'); ce.fill('#wz-seats', '10'); ce.wait_for_timeout(200)
            on = ce.is_checked('[data-rental-on]')
            chips = ce.inner_text('.wz-rental') if ce.locator('.wz-rental').count() else ''
            check('1 · paso 4: «Ofrecer alquiler de equipo» activado por defecto en una inmersión, con las piezas y sus precios', on and 'Máscara' in chips and 'Equipo completo' in chips, chips[:200])
            shot(ce, 'alquiler-asistente-paso4')
            ce.click('#wz-next'); ce.wait_for_selector('.wz-mode[data-mode="payment"]'); ce.click('.wz-mode[data-mode="payment"]'); ce.wait_for_timeout(200)
            ce.click('#wz-next'); ce.wait_for_selector('#wz-publish')
            ficha = ce.inner_text('.wz-ficha')
            check('1 · vista previa: el alquiler con sus piezas y precios, y «Reservar y pagar»', 'Alquiler de equipo' in ficha and 'Máscara' in ficha and 'Reservar y pagar' in ce.inner_text('.wz-review'), ficha[:200])
            shot(ce, 'alquiler-asistente-vista-previa')
            ce.click('#wz-publish'); ce.wait_for_timeout(1500)
            svc = srv.sql("SELECT id, price, booking_mode, rental_mode FROM provider_services WHERE title='Inmersión simple'")
            check('1 · publicada: 50 €, pago al reservar y alquiler ofrecido', len(svc) == 1 and float(svc[0]['price']) == 50 and svc[0]['booking_mode'] == 'payment' and svc[0]['rental_mode'] == 'offer', svc)
            sid = svc[0]['id'] if svc else 0
            slots = [r['id'] for r in srv.sql('SELECT id FROM service_slots WHERE service_id=? ORDER BY slot_date', (sid,))]
            check('1 · sus 3 salidas', len(slots) == 3, slots)
            # A service «Bajo petición» for check 7 (via the API: the wizard is checked above)
            rq = near.post('/api/provider-services', {'title': 'Salida en barco a la Reserva', 'price': 60, 'booking_mode': 'request'}).json['id']
            near.post('/api/provider-services/slot', {'service_id': rq, 'slot_date': day(6), 'slot_time': '10:00', 'spots_total': 8})
            rq_slot = srv.sql('SELECT id FROM service_slots WHERE service_id=?', (rq,))[0]['id']

            # ============================================================ 2 · bookings as a diver, on the web
            def web_booking(user, slot, pax, pick, name):
                """Opens the booking of the service and the slot, chooses the people, the equipment (pick(pg)) and books."""
                pg = page_for(DESK); login(pg, user)
                go(pg, f'#/reservar?center={cid}&service={sid}&slot={slot}', 1800)
                pg.wait_for_selector('#bk-eq .eq-pick')
                for _ in range(pax - 1):
                    pg.click('.bk-pax-btn[data-d="1"]'); pg.wait_for_timeout(250)
                pick(pg); pg.wait_for_timeout(900)
                shot(pg, name)
                return pg

            def piece(pg, root, code):
                pg.click(f'{root} .eq-piece[data-code="{code}"]'); pg.wait_for_timeout(150)

            def total(pg):
                return pg.inner_text('#bk-summary')

            # a · only mask and fins: 50 + 5 + 5 = 60 €
            def a_pick(pg):
                default = pg.get_attribute('#bk-eq [data-rent="0"]', 'aria-checked')
                check('2 · paso «Equipo»: «Llevo mi equipo» marcado por defecto', default == 'true', default)
                pg.click('#bk-eq [data-rent="1"]'); pg.wait_for_timeout(200)
                grid = pg.inner_text('#bk-eq .eq-grid')
                check('3 · la cuadrícula no tiene botella ni plomos y debajo dice «Incluido: botella y plomos»',
                      not re.search(r'botella|plomo', grid, re.I) and 'Incluido: botella y plomos' in pg.inner_text('#bk-eq .eq-included'), grid[:160])
                piece(pg, '#bk-eq', 'mask'); piece(pg, '#bk-eq', 'fins'); sizes(pg, '#bk-eq')
            pa = web_booking('diver_eqa', slots[0], 1, a_pick, 'alquiler-reserva-mascara-aletas-ordenador')
            summ = total(pa)
            check('2 · solo máscara y aletas: «Inmersión 50 € + Máscara 5 € + Aletas 5 € = 60 €»', '60' in summ and 'Máscara' in summ and 'Aletas' in summ, summ[-220:])
            pa.locator('.bk-go:visible').first.click(); pa.wait_for_timeout(2000)
            b1 = srv.sql("SELECT id, price, status FROM bookings ORDER BY id DESC LIMIT 1")[0]
            check('2 · reserva de 60 € creada (pago al reservar: a Stripe)', float(b1['price']) == 60, b1)
            eqr = srv.sql('SELECT diver, code, size, unit_price, total FROM booking_equipment WHERE booking_id=? ORDER BY diver, code', (b1['id'],))
            check('2 · el equipo guardado por buceador, con su precio del momento', [(r['code'], float(r['total'])) for r in eqr] == [('fins', 5.0), ('mask', 5.0)], [dict(r) for r in eqr])
            pa.context.close()

            # b · two divers: suit, mask, fins and boots / only the buoy
            def b_pick(pg):
                pg.click('#bk-eq [data-rent="1"]'); pg.wait_for_timeout(200)
                for c in ('wetsuit', 'mask', 'fins', 'boots'): piece(pg, '#bk-eq', c)
                sizes(pg, '#bk-eq')
                tabs = pg.locator('#bk-eq .eq-tabs [data-tab]').count()
                check('2 · dos buceadores: una pestaña por buceador («Tú», «Buceador 2»)', tabs == 2, tabs)
                pg.click('#bk-eq [data-tab="1"]'); pg.wait_for_timeout(150); piece(pg, '#bk-eq', 'smb')
            pb = web_booking('diver_eqb', slots[0], 2, b_pick, 'alquiler-reserva-dos-buceadores-ordenador')
            summ = total(pb)
            check('2 · dos buceadores: 2 × 50 + traje 10 + máscara 5 + aletas 5 + escarpines 3 + boya 2 = 125 €', '125' in summ, summ[-260:])
            pb.locator('.bk-go:visible').first.click(); pb.wait_for_timeout(2000)
            b2 = srv.sql("SELECT id, price FROM bookings ORDER BY id DESC LIMIT 1")[0]
            per = {}
            for r in srv.sql('SELECT diver, code, size FROM booking_equipment WHERE booking_id=?', (b2['id'],)): per.setdefault(r['diver'], []).append(r['code'])
            check('2 · cada buceador con sus piezas', sorted(per.get(0, [])) == ['boots', 'fins', 'mask', 'wetsuit'] and per.get(1) == ['smb'] and float(b2['price']) == 125, (per, b2['price']))
            pb.context.close()

            # c · «Equipo completo» in one tap (and «Igual que el anterior» on the phone, in the app: see below)
            def c_pick(pg):
                pg.click('#bk-eq [data-rent="1"]'); pg.wait_for_timeout(200); pg.click('#bk-eq [data-kit]'); pg.wait_for_timeout(300)
                on = pg.locator('#bk-eq .eq-piece.is-on').count()
                check('2 · «Equipo completo» en un toque marca sus piezas', on >= 4, on)
                sizes(pg, '#bk-eq')
                # removing one piece goes back to the price per piece, with a notice and the new amount
                pg.click('#bk-eq .eq-piece.is-on >> nth=0'); pg.wait_for_timeout(1200)
                warn = pg.inner_text('#bk-eq .eq-warn') if pg.locator('#bk-eq .eq-warn').count() else ''
                check('2 · quitar una pieza del equipo completo avisa: se cobra por piezas, con el importe nuevo', 'por piezas' in warn and '€' in warn, warn)
                pg.click('#bk-eq [data-kit]'); pg.wait_for_timeout(300); sizes(pg, '#bk-eq')
            pc = web_booking('diver_eqc', slots[1], 1, c_pick, 'alquiler-reserva-equipo-completo-ordenador')
            summ = total(pc)
            check('2 · con «Equipo completo»: 50 + 30 = 80 €', '80' in summ, summ[-200:])
            pc.locator('.bk-go:visible').first.click(); pc.wait_for_timeout(2000)
            b3 = srv.sql("SELECT id, price FROM bookings ORDER BY id DESC LIMIT 1")[0]
            check('2 · reserva con «Equipo completo» a 80 €', float(b3['price']) == 80, b3)
            pc.context.close()

            # ============================================================ 5 · stock: 2 jackets M; a third can not have one
            for user in ('diver_eqd',):
                c2 = t.client(); c2.login(user)
                r = c2.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slots[2], 'participants': 2,
                                              'equipment': [{'items': [{'code': 'bcd', 'size': 'M'}]}, {'items': [{'code': 'bcd', 'size': 'M'}]}]})
                check('5 · dos jackets M reservados en la misma salida', r.status == 200, r.json)
            pd = page_for(PHONE); login(pd, 'diver_eqe'); go(pd, f'#/reservar?center={cid}&service={sid}&slot={slots[2]}', 1800)
            pd.wait_for_selector('#bk-eq .eq-pick'); pd.click('#bk-eq [data-rent="1"]'); pd.wait_for_timeout(200); piece(pd, '#bk-eq', 'bcd'); pd.wait_for_timeout(1200)
            m = pd.locator('#bk-eq [data-size="bcd"][data-val="M"]')
            msel = pd.locator('#bk-eq select[data-size-sel="bcd"] option[value="M"]')
            out_m = (m.count() and m.is_disabled() and 'No disponible' in m.inner_text()) or (msel.count() and msel.get_attribute('disabled') is not None)
            check('5 · la tercera persona ve el jacket M «No disponible» y no lo puede marcar', bool(out_m))
            c3 = t.client(); c3.login('diver_eqe')
            r = c3.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slots[2], 'participants': 1, 'equipment': [{'items': [{'code': 'bcd', 'size': 'M'}]}]})
            check('5 · y el servidor tampoco lo acepta', r.status in (400, 409), (r.status, r.json))
            shot(pd, 'alquiler-reserva-movil-360-sin-stock')
            pd.context.close()

            # ============================================================ 4 · what the centre sees
            srv.sql("UPDATE bookings SET status='confirmed', payment_status='paid', amount_paid=price WHERE id IN (?,?,?)", (b1['id'], b2['id'], b3['id']))
            go(ce, f'#/reserva?id={b2["id"]}', 1800); ce.wait_for_selector('#bk-equip-card .eq-card')
            card = ce.inner_text('#bk-equip-card')
            check('4 · ficha de la reserva: cada buceador con sus piezas y tallas', 'Traje' in card and 'Boya' in card and 'Aletas' in card and re.search(r'\b(XS|S|M|L|XL|XXL)\b', card), card[:240])
            shot(ce, 'alquiler-ficha-reserva-centro')
            man = near.get(f'/api/manifest/{slots[0]}').json
            rent = [x.get('rental') for x in (man.get('divers') or [])]
            check('4 · lista del barco: la fila de cada buceador con su alquiler', any(rent) and any('Boya' in ' '.join(r or []) for r in rent), rent)
            go(ce, '#/admin?tab=equipment', 1500); ce.click('.svc-tab[data-view="prep"]'); ce.wait_for_timeout(300)
            ce.fill('#eq-prep-day', day(3)); ce.dispatch_event('#eq-prep-day', 'change'); ce.wait_for_timeout(1500)
            prep = ce.inner_text('#eq-prep')
            check('4 · «Equipo para preparar» del día, por pieza y talla', 'Aletas' in prep and 'Máscara' in prep and '×' in prep, prep[:300])
            pdf = near.get(f'/api/provider/equipment/prep.pdf?date={day(3)}')
            check('4 · y en PDF para imprimir o compartir', pdf.status == 200 and pdf.body[:4] == b'%PDF', pdf.status)
            shot(ce, 'alquiler-equipo-para-preparar-ordenador')

            # ============================================================ 6 · changes: a torch from «Mis reservas»; a piece at the desk
            pa = page_for(DESK); login(pa, 'diver_eqa'); go(pa, f'#/reserva?id={b1["id"]}', 1800); pa.wait_for_selector('#eq-change')
            pa.click('#eq-change'); pa.wait_for_selector('#eq-change-pick .eq-pick'); piece(pa, '#eq-change-pick', 'torch'); pa.wait_for_timeout(1200)
            diff = pa.inner_text('#eq-diff')
            check('6 · el buceador añade una linterna: «Diferencia a pagar: 5 €»', 'Diferencia a pagar' in diff and '5' in diff, diff)
            n0 = len([c for c in stripe.calls if c['path'] == '/v1/checkout/sessions' and c['method'] == 'POST'])
            pa.click('#eq-change-save'); pa.wait_for_timeout(1800)
            n1 = len([c for c in stripe.calls if c['path'] == '/v1/checkout/sessions' and c['method'] == 'POST'])
            check('6 · y se le cobra la diferencia (un pago de Stripe por la diferencia)', n1 == n0 + 1, (n0, n1))
            pa.context.close()
            go(ce, f'#/reserva?id={b3["id"]}', 1800); ce.wait_for_selector('#eq-desk'); ce.click('#eq-desk'); ce.wait_for_selector('#eq-desk-f')
            ce.select_option('#eq-d-code', 'torch'); ce.check('input[name="eq-d-pay"][value="desk"]'); ce.click('button[form="eq-desk-f"]'); ce.wait_for_timeout(1500)
            desk = srv.sql("SELECT code, source FROM booking_equipment WHERE booking_id=? AND code='torch'", (b3['id'],))
            check('6 · el centro añade una linterna en el mostrador como «Pagado en el centro»', len(desk) == 1 and desk[0]['source'] == 'desk', [dict(r) for r in desk])
            check('6 · y se ve en la reserva como «añadido en el centro»', 'añadido en el centro' in ce.inner_text('#bk-equip-card'))

            # ============================================================ 7 · «Bajo petición»
            c7 = t.client(); c7.login('diver_eqd')
            r = c7.post('/api/bookings', {'center_id': cid, 'service_id': rq, 'slot_id': rq_slot, 'participants': 1, 'equipment': [{'items': [{'code': 'mask'}, {'code': 'fins', 'size': '40'}]}]})
            b7 = r.json.get('id')
            row = srv.sql('SELECT status, price, payment_status FROM bookings WHERE id=?', (b7,))[0] if b7 else {}
            check('7 · bajo petición: la solicitud lleva el equipo y no se cobra nada todavía', r.status == 200 and row['status'] in ('pending', 'requested') and float(row['price']) == 70
                  and not r.json.get('checkout_url'), (r.status, dict(row) if row else r.json))
            go(ce, '#/admin?tab=bookings', 1800)
            check('7 · el centro lo ve antes de aceptar', 'Máscara' in near.get(f'/api/bookings/{b7}/equipment').json and True or near.get(f'/api/bookings/{b7}/equipment').status == 200)
            acc = near.post(f'/api/bookings/{b7}/status', {'status': 'accepted'})
            pay = c7.post('/api/payments/checkout', {'booking_id': b7, 'service_id': rq, 'slot_id': rq_slot})
            sess = [c for c in stripe.calls if c['path'] == '/v1/checkout/sessions' and c['method'] == 'POST'][-1]['params']
            amounts = sum(int(li['price_data']['unit_amount']) * int(li.get('quantity', 1)) for li in sess.get('line_items') or [])
            check('7 · al aceptar, el pago incluye el equipo (70 €)', acc.status == 200 and pay.status == 200 and amounts == 7000, (acc.status, pay.status, amounts))

            # ============================================================ 8 · an old booking («código:cantidad»)
            c8 = t.client(); c8.login('diver_eqc')
            r = c8.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slots[1], 'participants': 2, 'equipment_codes': 'mask:2,fins:1'})
            b8 = r.json.get('id')
            old = srv.sql('SELECT price FROM bookings WHERE id=?', (b8,))[0] if b8 else {}
            check('8 · el formato antiguo «código:cantidad» se sigue cobrando bien (2 × 50 + 2 × 5 + 5 = 115 €)', r.status == 200 and float(old['price']) == 115, (r.status, dict(old) if old else r.json))
            st = c8.get(f'/api/bookings/{b8}/equipment').json
            check('8 · y se ve en la reserva', len(st.get('rows') or []) >= 2 or st.get('legacy_text'), st)

            # ============================================================ 2 (app) and 9 · phone 360, app «Noche», widget
            pm = page_for(PHONE, app=True, theme='noche'); login(pm, 'diver_eqd'); go(pm, '#/', 1500)
            card = pm.locator('#wda-salidas .tarjeta-salida', has_text='Inmersión simple').first
            if card.count():
                card.locator('[data-reservar]').click(); pm.wait_for_timeout(1200)
                pm.click('[data-cambiar="pers"]'); pm.wait_for_timeout(250); pm.click('[data-pax="1"]'); pm.wait_for_timeout(600)
                pm.click('[data-cambiar="equipo"]'); pm.wait_for_timeout(400); pm.click('.wda-capa [data-rent="1"]'); pm.wait_for_timeout(250)
                pm.click('.wda-capa [data-kit]'); pm.wait_for_timeout(300); sizes(pm, '.wda-capa')
                pm.click('.wda-capa [data-tab="1"]'); pm.wait_for_timeout(200); pm.click('.wda-capa [data-copy]'); pm.wait_for_timeout(1000)
                foot = pm.inner_text('.wda-capa .hoja-pie')
                check('2 · modo app: equipo completo para dos con «Igual que el anterior» (2 × 50 + 2 × 30 = 160 €)', '160' in foot, foot)
                shot(pm, 'alquiler-app-movil-360-noche')
            else:
                check('2 · modo app: la salida en la portada', False, pm.inner_text('#wda-salidas')[:200])
            pm.context.close()
            # the widget of the centre's website: the same equipment, inside the booking
            wpg = page_for(PHONE)
            slug = near.get('/api/provider/vender').json['slug']
            wpg.goto(f'{base}/c/{slug}'); wpg.wait_for_load_state('networkidle'); wpg.wait_for_timeout(1500)
            wpg.locator('.wr-svc', has_text='Inmersión simple').first.click(); wpg.wait_for_timeout(1200)
            wpg.evaluate("document.querySelector('[data-eqrent]')?.closest('details')?.setAttribute('open', '')"); wpg.wait_for_timeout(300)   # «Equipo», folded
            has = wpg.locator('[data-eqrent="1"]').count() > 0
            check('2 · widget de la web del centro: «Necesito equipo» dentro de la reserva', has)
            if has:
                wpg.click('[data-eqrent="1"]'); wpg.wait_for_timeout(300)
                txt = wpg.inner_text('body')
                check('3 · widget: sin botella ni plomos como piezas, con «Incluido: botella y plomos»', 'botella y plomos' in txt.lower() and not re.search(r'\bBotella\b \d', txt))
                shot(wpg, 'alquiler-widget-movil-360')
            wpg.context.close()
            # the screens of the brief at 360 px, in the web and in the app «Noche»
            for theme, app in (('web', False), ('noche', True)):
                pg = page_for(PHONE, app=app, theme='noche' if app else None); login(pg, 'center_eq')
                go(pg, '#/admin?tab=equipment', 1800)
                wide = pg.evaluate('document.scrollingElement.scrollWidth - innerWidth')
                check(f'9 · móvil 360 · {theme}: «Equipo de alquiler» sin salirse de la pantalla', pg.locator('.eq-cfg').count() >= 11 and wide <= 0, wide)
                shot(pg, f'alquiler-config-movil-360-{theme}')
                pg.click('.svc-tab[data-view="prep"]'); pg.wait_for_timeout(300); pg.fill('#eq-prep-day', day(3)); pg.dispatch_event('#eq-prep-day', 'change'); pg.wait_for_timeout(1300)
                shot(pg, f'alquiler-equipo-para-preparar-movil-360-{theme}')
                pg.context.close()
            ce.context.close()
            own = [e for e in errors if 'tile.openstreetmap.org' not in e and 'ERR_TUNNEL_CONNECTION_FAILED' not in e]
            check('9 · consola sin errores', not own, own[:5])
            browser.close()
    finally:
        srv.stop(); stripe.stop()
    return rows


if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    rows = run(out)
    bad = [r for r in rows if not r[1]]
    print(f'{len(rows) - len(bad)}/{len(rows)} comprobaciones correctas')
    sys.exit(1 if bad else 0)
