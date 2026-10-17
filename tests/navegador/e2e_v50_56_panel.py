"""v50.56 · Bloque 1, Partes F y H en un navegador real: el panel del centro con el motor multicanal.

Comprueba, con Chromium:
  - «Vender en tu web»: el código de 2 líneas en los 3 formatos, la vista previa en vivo, los dominios, la clave de API
    (se enseña una vez), los webhooks y el iCal; sin desplazamiento lateral en el móvil;
  - el planning único: las reservas de los 5 canales en la misma salida, cada una con su etiqueta, y el filtro por canal;
  - el aviso al momento en el panel cuando entra una reserva nueva desde otro canal;
  - «Ventas por canal»: reservas e importe por canal y mes;
  - «Nueva reserva» manual con «Online con enlace»: el enlace de pago para mandar al cliente;
  - «Bloquear plazas» sin cliente: las plazas salen del inventario de todos los canales.
Uso: python tests/navegador/e2e_v50_56_panel.py [--shots DIR]
"""
from __future__ import annotations

import datetime
import sys
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
from helpers import ServerTestCase, Server, Client  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
TOASTS = """window.__toasts=[];document.addEventListener('DOMContentLoaded',()=>{const t=document.getElementById('toast');
  if(t) new MutationObserver(()=>{ if(t.textContent) window.__toasts.push(t.textContent); }).observe(t,{childList:true,characterData:true,subtree:true});});"""

# Elements that end beyond the right edge of the screen (what scrolls or is clipped inside a box that fits does not count)
OVERFLOW = """[...document.querySelectorAll('ROOT *')].filter(e => { const r = e.getBoundingClientRect(); if (!r.width || r.right <= window.innerWidth + 1) return false;
  for (let p = e.parentElement; p && p !== document.body; p = p.parentElement) { const o = getComputedStyle(p).overflowX;
    if (o !== 'visible' && p.getBoundingClientRect().right <= window.innerWidth + 1) return false; }
  return true; }).slice(0, 12).map(e => e.tagName.toLowerCase() + (e.id ? '#' + e.id : '') + (e.className && typeof e.className === 'string' ? '.' + e.className.trim().split(/ +/).join('.') : '') + ' → ' + Math.round(e.getBoundingClientRect().right))"""


def chromium(p):
    exe = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    return p.chromium.launch(executable_path=exe) if Path(exe).exists() else p.chromium.launch()


def run(shots: Path | None):
    stripe = StripeMock()
    srv = ServerTestCase.server = Server({'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': stripe.base}).start()
    t = ServerTestCase('run')
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))

    def shot(page, name, full=True):
        if shots:
            shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'), full_page=full)

    try:
        admin = t.make_admin()
        center = t.make_center(admin, 'multicanal', phone='+34 600 560 001')
        cid = center.user['center_id']
        srv.sql("UPDATE centers SET name='Bahía Coralina',plan_code='pro',plan_status='active',plan_expires_at='2099-12-31',stripe_account_id='acct_bahia',"
                "stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cid,))
        sid = center.post('/api/provider-services', {'title': 'Doble inmersión en barco', 'price': 60, 'booking_mode': 'request', 'max_participants': 12}).json['id']
        pay_sid = center.post('/api/provider-services', {'title': 'Bautizo de buceo', 'price': 75, 'booking_mode': 'payment', 'max_participants': 6}).json['id']
        today = datetime.date.today()
        day = today + datetime.timedelta(days=3)
        slot = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': day.isoformat(), 'slot_time': '09:00', 'spots_total': 12}).json['slot_id']
        pay_slot = center.post('/api/provider-services/slot', {'service_id': pay_sid, 'slot_date': day.isoformat(), 'slot_time': '16:00', 'spots_total': 6}).json['slot_id']
        cfg = center.get('/api/provider/vender').json; slug = cfg['slug']
        center.post('/api/provider/vender', {'domains': 'buceobahia.example.com', 'color': '#0b7a75'})
        key = center.post('/api/provider/api-keys', {'action': 'create', 'name': 'Programa de reservas', 'scope': 'write'}).json['key']

        # One booking from each channel, all in the same departure
        n = [0]

        def widget(name, canal='widget'):
            n[0] += 1
            body = {'service_id': sid, 'slot_id': slot, 'participants': 1, 'fullname': name, 'email': f'cliente{n[0]}@example.org', 'accept_policy': True, 'canal': canal, 'lang': 'es'}
            if canal == 'widget': body['host_url'] = 'https://www.buceobahia.example.com/reservas'
            return Client(srv).post(f'/api/w/{slug}/reservar', body, headers={'Idempotency-Key': f'e2e-panel-{n[0]:04d}'})
        diver = t.make_diver('canales')
        r1 = diver.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': 2})
        r2 = widget('Lucía Web')
        r3 = widget('Pablo Enlace', canal='link')
        r4 = Client(srv, origin=None).request('POST', '/api/v1/bookings', data={'service_id': sid, 'departure_id': slot, 'participants': 1, 'customer': {'name': 'Marta API', 'email': 'marta.api@example.org'}},
                                                headers={'Authorization': f'Bearer {key}', 'Idempotency-Key': 'e2e-panel-api-1'})
        r5 = center.post('/api/center/bookings/manual', {'fullname': 'Hotel Sol (teléfono)', 'phone': '+34 611 222 333', 'service_id': sid, 'slot_id': slot, 'participants': 3, 'status': 'confirmed', 'notify_client': False})
        check('5 reservas por 5 canales en la misma salida', all(r.status in (200, 201) for r in (r1, r2, r3, r4, r5)), [r.status for r in (r1, r2, r3, r4, r5)])
        chans = {r['channel'] for r in srv.sql('SELECT channel FROM bookings WHERE slot_id=?', (slot,))}
        check('canales guardados', chans == {'worldives', 'widget', 'link', 'api', 'manual'}, chans)
        base = srv.base
        with sync_playwright() as p:
            browser = chromium(p)

            def session(width=1366):
                ctx = browser.new_context(viewport={'width': width, 'height': 900 if width > 500 else 844}, locale='es-ES')
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                ctx.add_init_script(TOASTS)
                page = ctx.new_page(); errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.goto(base + '/#/login'); page.wait_for_selector('#login'); page.fill('#login', 'center_multicanal'); page.fill('#password', PW)
                page.click('#login-form button[type=submit]'); page.wait_for_timeout(900)
                return ctx, page, errors

            def go(page, route, wait=1200):
                page.goto(base + '/' + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)

            ctx, page, errors = session()
            # ---- «Vender en tu web»
            go(page, '#/admin?tab=vender', 1800)
            page.wait_for_selector('#cb-vender .vt-wrap', timeout=15000)
            code = page.inner_text('#vt-code')
            check('vender: código de 2 líneas con el centro', 'data-worldives' in code and f'data-centro="{slug}"' in code and code.strip().count('\n') <= 1, code)
            formats = {}
            for f in ('boton', 'calendario', 'lista'):
                page.click(f'.vt-look[data-fmt="{f}"]'); page.wait_for_timeout(600)   # v50.58 (Parte 5): «¿Cómo quieres que se vea?»
                formats[f] = page.inner_text('#vt-code')
            check('vender: los 3 formatos', all(f'data-formato="{f}"' in formats[f] or f in formats[f] for f in formats) and len(set(formats.values())) == 3, formats)
            page.check('input[name="vt-what"][value="service"]'); page.wait_for_selector('#vt-svc'); page.wait_for_timeout(500)   # v50.58: paso 1
            page.select_option('#vt-svc', str(pay_sid)); page.wait_for_timeout(500)
            check('vender: filtro por servicio en el código', f'data-servicio="{pay_sid}"' in page.inner_text('#vt-code'))
            page.check('input[name="vt-what"][value="all"]'); page.wait_for_timeout(500)
            frame = page.frame_locator('#vt-frame')
            try:
                frame.locator('body').wait_for(timeout=10000)
                prev = frame.locator('body').inner_text(timeout=10000)
            except Exception as exc:
                prev = f'ERROR {exc}'
            check('vender: vista previa en vivo', 'Doble inmersión' in prev or 'Bautizo' in prev, prev[:200])
            page.click('#vt-dev summary'); page.wait_for_timeout(300)   # v50.58: lo técnico, plegado en «Para programadores»
            check('vender: dominio autorizado en pantalla', 'buceobahia.example.com' in page.input_value('#vt-domains'))
            page.fill('#vt-key-name', 'Mi web'); page.select_option('#vt-key-scope', 'read'); page.click('#vt-key-new')
            page.wait_for_selector('#vt-key-out code, #vt-key-out .vt-code', timeout=10000)
            shown = page.inner_text('#vt-key-out')
            check('vender: la clave nueva se enseña una vez', 'wdk_' in shown, shown[:120])
            shot(page, 'vender-en-tu-web-ordenador')
            page.click('#vt-key-done') if page.locator('#vt-key-done').count() else None
            page.wait_for_timeout(800)
            check('vender: la clave ya no se vuelve a ver', 'wdk_' not in (page.inner_text('#vt-api') if page.locator('#vt-api').count() else '') or page.locator('#vt-key-out code').count() == 0)
            guide = page.inner_text('#cb-vender')
            check('vender: guía para WordPress, Wix y Squarespace', all(x in guide for x in ('WordPress', 'Wix', 'Squarespace')))
            check('vender: iCal en la misma pantalla', page.locator('#vt-ical').count() == 1)

            # ---- Planning: one inventory, every channel with its label, filter by channel
            go(page, '#/admin?tab=planning', 1500)
            if day.strftime('%Y-%m') != today.strftime('%Y-%m'):
                page.select_option('#pl-month', day.strftime('%Y-%m')); page.wait_for_timeout(1200)
            page.locator(f'.pl-cell[data-day="{day.isoformat()}"]').first.click(); page.wait_for_timeout(800)
            pop = page.inner_text('#pl-pop')
            labels = ['WORLDIVES', 'Tu web', 'Enlace directo', 'API', 'Manual']
            check('planning: las 5 etiquetas de canal en la misma salida', all(l in pop for l in labels), pop[:500])
            check('planning: plazas comunes (12 − 8 = 4 libres)', '4' in pop and page.locator('#pl-pop .pl-ch').count() >= 5, pop[:300])
            shot(page, 'planning-multicanal-ordenador', False)
            page.keyboard.press('Escape'); page.wait_for_timeout(300)
            page.select_option('#pl-channel', 'widget'); page.wait_for_timeout(1300)
            page.locator(f'.pl-cell[data-day="{day.isoformat()}"]').first.click(); page.wait_for_timeout(800)
            pop_w = page.inner_text('#pl-pop')
            check('planning: filtro por canal («Tu web»)', 'Lucía' in pop_w and 'Marta' not in pop_w and 'Hotel Sol' not in pop_w, pop_w[:300])
            shot(page, 'planning-filtro-canal-ordenador', False)
            page.keyboard.press('Escape'); page.select_option('#pl-channel', ''); page.wait_for_timeout(1200)

            # ---- Spots kept for a group without a customer
            page.locator(f'.pl-cell[data-day="{day.isoformat()}"]').first.click(); page.wait_for_timeout(800)
            free_before = srv.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot,))[0]['spots_available']
            page.locator(f'#pl-pop .pl-blockspots[data-slot="{slot}"]').click(); page.wait_for_selector('#sb-qty')
            page.fill('#sb-qty', '2'); page.fill('#sb-label', 'Agencia Azul · grupo'); page.click('#sb-form ~ * button[type=submit], button[form="sb-form"]')
            page.wait_for_timeout(1500)
            free_after = srv.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot,))[0]['spots_available']
            check('bloquear plazas: salen del inventario común', free_after == free_before - 2, (free_before, free_after))
            page.locator(f'.pl-cell[data-day="{day.isoformat()}"]').first.click(); page.wait_for_timeout(800)
            check('bloquear plazas: se ven en el planning', 'Agencia Azul' in page.inner_text('#pl-pop'))
            shot(page, 'planning-bloqueo-plazas-ordenador', False)
            avail = Client(srv, origin=None).get(f'/api/v1/availability?service_id={sid}&from={day.isoformat()}&to={day.isoformat()}', headers={'Authorization': f'Bearer {key}'}).json
            api_free = [d_['spots_free'] for d_ in avail.get('departures', avail.get('items', [])) if d_.get('id') == slot]
            check('bloquear plazas: la API ve las mismas plazas', api_free == [free_after], (api_free, free_after, str(avail)[:200]))
            page.keyboard.press('Escape'); page.wait_for_timeout(300)

            # ---- Manual booking with an online payment link
            page.locator(f'.pl-cell[data-day="{day.isoformat()}"]').first.click(); page.wait_for_timeout(800)
            page.locator(f'#pl-pop .pl-add[data-slot="{pay_slot}"]').click(); page.wait_for_selector('#mb-name')
            page.fill('#mb-name', 'Andrés Teléfono'); page.fill('#mb-phone', '+34 622 333 444'); page.fill('#mb-email', 'andres@example.org')
            page.check('input[name="mb-pay"][value="link"]', force=True)
            page.click('#mb-form ~ * button[type=submit], button[form="mb-form"], #mb-form button[type=submit]')
            page.wait_for_selector('text=Enlace de pago', timeout=15000); page.wait_for_timeout(900)   # the first window fades out
            check('reserva manual: la ventana de la reserva se cierra', page.locator('#mb-form').count() == 0)
            link = page.locator('.vt-link').last.inner_text()
            check('reserva manual: enlace de pago online', '/mi-reserva/' in link and 'pagar=1' in link, link)
            check('reserva manual: botón de WhatsApp', page.locator('a[href^="https://wa.me/?text="]').count() >= 1)
            shot(page, 'reserva-manual-enlace-de-pago', False)
            mb = srv.sql("SELECT channel, payment_status, status, slot_reserved FROM bookings WHERE slot_id=? ORDER BY id DESC LIMIT 1", (pay_slot,))[0]
            check('reserva manual: canal «manual», plaza guardada hasta el pago', mb['channel'] == 'manual' and mb['slot_reserved'] == 1, mb)
            pm = srv.sql("SELECT text FROM email_outbox WHERE template='payment_required' AND to_email='andres@example.org'")
            check('reserva manual: el cliente recibe el enlace por email', pm and '/mi-reserva/' in pm[0]['text'], pm[0]['text'][:300] if pm else None)
            page.keyboard.press('Escape'); page.wait_for_timeout(400)

            # ---- The instant notice: a new booking from the centre's web while the panel is open
            go(page, '#/admin?tab=bookings', 2500)
            widget('Sergio Nuevo')
            for _ in range(60):   # the panel looks every 20 s (a function in the page can't be used: the CSP has no 'unsafe-eval')
                if any('Sergio' in x for x in page.evaluate('window.__toasts')): break
                page.wait_for_timeout(500)
            toast = [x for x in page.evaluate('window.__toasts') if 'Nueva reserva' in x]
            check('aviso al momento en el panel con el canal', toast and 'Tu web' in toast[-1] and 'Sergio' in toast[-1], toast)
            check('sin aviso por las reservas manuales del propio equipo', not any('Manual' in x for x in toast), toast)
            mails = srv.sql("SELECT text FROM email_outbox WHERE template='center_new_booking' ORDER BY id DESC LIMIT 1")
            check('aviso por email al centro con el canal', mails and 'Canal: Tu web · www.buceobahia.example.com' in mails[0]['text'], mails[0]['text'][:300] if mails else None)
            go(page, '#/admin?tab=bookings', 1500)
            check('lista de reservas con su canal', all(x in page.inner_text('main') for x in ('Tu web', 'API', 'Manual')))

            # ---- «Ventas por canal»
            go(page, '#/admin?tab=analytics', 2000)
            page.wait_for_selector('#cb-vcanal .vt-table', timeout=15000)
            rep = page.inner_text('#cb-vcanal')
            check('ventas por canal: los canales y el mes', all(x in rep for x in ('Tu web', 'API', 'Manual', 'Enlace directo', 'WORLDIVES')), rep[:400])
            # v50.57 (1.3): one way to export everywhere, Excel (by default) and CSV; the CSV is downloaded for real
            check('ventas por canal: exportar en Excel y en CSV', page.locator('#cb-vcanal [data-vc-ex="xlsx"]').count() == 1 and page.locator('#cb-vcanal [data-vc-ex="csv"]').count() == 1)
            with page.expect_download(timeout=15000) as dl:
                page.click('#cb-vcanal [data-vc-ex="csv"]')
            csv_body = Path(dl.value.path()).read_bytes()
            check('ventas por canal: el CSV se descarga (UTF-8 con BOM y «;»)', csv_body.startswith(b'\xef\xbb\xbf') and b';' in csv_body[:400], csv_body[:120])
            page.locator('#cb-vcanal').scroll_into_view_if_needed(); shot(page, 'ventas-por-canal-ordenador', False)
            check('panel sin errores JS', not errors, errors)
            ctx.close()

            # ---- Phone
            ctx, page, errors = session(390)
            go(page, '#/admin?tab=vender', 2000)
            page.wait_for_selector('#cb-vender .vt-wrap', timeout=15000)
            sw = page.evaluate('[document.documentElement.scrollWidth, window.innerWidth]')
            check('vender en el móvil: sin desplazamiento lateral', sw[0] <= sw[1] + 1, sw)
            # The page hides what overflows: also check that nothing of the screen is cut off on the right
            cut = page.evaluate(OVERFLOW.replace('ROOT', '#cb-vender'))
            check('vender en el móvil: nada cortado a la derecha', not cut, cut)
            full_h = page.evaluate('document.scrollingElement.scrollHeight')
            page.set_viewport_size({'width': 390, 'height': full_h}); page.wait_for_timeout(800)
            shot(page, 'vender-en-tu-web-movil', False)
            page.set_viewport_size({'width': 390, 'height': 844})
            go(page, '#/admin?tab=analytics', 2000)
            page.wait_for_selector('#cb-vcanal .vt-table', timeout=15000)
            sw = page.evaluate('[document.documentElement.scrollWidth, window.innerWidth]')
            check('ventas por canal en el móvil: sin desplazamiento lateral', sw[0] <= sw[1] + 1, sw)
            cut = page.evaluate(OVERFLOW.replace('ROOT', '#cb-vcanal'))
            check('ventas por canal en el móvil: nada cortado a la derecha', not cut, cut)
            shot(page, 'ventas-por-canal-movil')
            check('móvil sin errores JS', not errors, errors)
            ctx.close()
            browser.close()
    finally:
        srv.stop(); stripe.stop()
    ok = sum(1 for c in checks if c[1])
    for name, good, detail in checks:
        print(('OK  ' if good else 'MAL ') + name + ('' if good else f'  → {detail}'))
    print(f'{ok}/{len(checks)} comprobaciones')
    return ok == len(checks)


if __name__ == '__main__':
    out = Path(sys.argv[sys.argv.index('--shots') + 1]) if '--shots' in sys.argv else None
    sys.exit(0 if run(out) else 1)
