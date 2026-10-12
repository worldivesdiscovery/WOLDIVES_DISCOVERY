"""Encargo 2, puntos 1 y 5 in a real browser (computer and phone): the «Manifiesto» button of a departure in the
planning, boats, automatic split with confirmation, moving divers by dragging (computer) and with «Mover» (phone),
the view for the boat crew, the A4 print view, the waiver editor, a diver signing from «Mi reserva» with a drawn
signature, the companion signing at the check-in on the centre's device, and the manifest marking who signed.
Usage: python tests/e2e_manifest.py [--shots DIR]
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from helpers import ServerTestCase, Server  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
WAIVER = ('Declaro que conozco los riesgos propios del buceo, que he informado al centro de mi titulación real y que '
          'seguiré en todo momento las instrucciones del guía. Recibo el equipo de alquiler revisado y me comprometo a devolverlo.')


def chromium(p):
    exe = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    return p.chromium.launch(executable_path=exe) if Path(exe).exists() else p.chromium.launch()


def draw(page, sel):
    box = page.locator(sel).bounding_box()
    x0, y0, w, h = box['x'], box['y'], box['width'], box['height']
    page.mouse.move(x0 + w * 0.1, y0 + h * 0.6); page.mouse.down()
    for i in range(1, 16):
        page.mouse.move(x0 + w * (0.1 + i * 0.05), y0 + h * (0.6 - 0.25 * (i % 2)), steps=2)
    page.mouse.up()


DAY = (datetime.date.today() + datetime.timedelta(days=2)).isoformat()


def run(shots: Path | None):
    ServerTestCase.server = Server().start()
    srv = ServerTestCase.server
    t = ServerTestCase('run')
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))

    try:
        admin = t.make_admin()
        center = t.make_center(admin, 'mfweb', phone='+34 600 450 001')
        cid = center.user['center_id']
        sid = center.post('/api/provider-services', {'title': 'Salida en barco a Cabo de San Antonio', 'price': 55, 'booking_mode': 'request'}).json['id']
        slot = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': DAY, 'slot_time': '09:00', 'spots_total': 14}).json['slot_id']
        bookings = {}
        for tag, cert, pax, prof in (('lucia7', 2, 1, {'emergency_contact_name': 'Javier Lucía', 'emergency_contact_phone': '+34 600 111 222', 'suit_size': 'S', 'fin_size': '38-39', 'bcd_size': 'S'}),
                                     ('mario7', 1, 2, {'suit_size': 'L'}), ('nora7', 3, 1, {}), ('oscar7', 1, 1, {}), ('paula7', 2, 3, {})):
            d = t.make_diver(tag)
            d.post('/api/account/profile', {'certification_id': cert, 'phone': '+34 611 222 333', **prof})
            r = d.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': pax, 'nitrox': tag == 'nora7'})
            srv.sql("UPDATE bookings SET status='confirmed' WHERE id=?", (r.json['id'],))
            bookings[tag] = r.json['id']
        center.post('/api/manifest/boats/save', {'name': 'Neptuno', 'capacity': 8})
        center.post('/api/manifest/boats/save', {'name': 'Tritón', 'capacity': 12})
        base = srv.base
        with sync_playwright() as p:
            browser = chromium(p)

            def session(login=None, pw=PW, width=1366):
                ctx = browser.new_context(viewport={'width': width, 'height': 900 if width > 500 else 844}, locale='es-ES', has_touch=width < 500)
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                page = ctx.new_page(); errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                if login:
                    page.goto(base + '/#/login'); page.wait_for_selector('#login'); page.fill('#login', login); page.fill('#password', pw)
                    page.click('#login-form button[type=submit]'); page.wait_for_timeout(900)
                return ctx, page, errors

            def go(page, route, wait=1100):
                page.goto(base + '/' + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)

            def shot(page, name, full=True):
                if shots:
                    shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'), full_page=full)

            # ---- Centre on a computer: waiver, planning, manifest
            ctx, page, errors = session('center_mfweb')
            go(page, '#/admin?tab=tools', 1500)
            check('herramientas: editor del descargo', page.locator('#wv-form').count() == 1)
            check('descargo: aviso de que no se incluyen preguntas de salud', 'preguntas de salud' in page.inner_text('#wv-editor'))
            page.fill('#wv-body', WAIVER); page.click('#wv-form button[type=submit]'); page.wait_for_timeout(500)
            check('descargo: confirmación antes de publicar', page.locator('#wd-confirm').count() == 1)
            page.click('#wd-confirm-ok'); page.wait_for_timeout(900)
            check('descargo publicado (versión 1)', srv.sql('SELECT version FROM waiver_templates WHERE center_id=? AND active=1', (cid,))[0]['version'] == 1)
            shot(page, 'descargo-editor-ordenador')
            go(page, '#/admin?tab=planning', 1600)
            if DAY[:7] != datetime.date.today().isoformat()[:7]:
                page.locator('.pl-nav-next, [data-pl-move="1"], button[aria-label*="siguiente" i]').first.click(); page.wait_for_timeout(1200)
            day = page.locator(f'.pl-cell[data-day="{DAY}"]')
            if day.count():
                day.first.click(); page.wait_for_timeout(700)
                check('planning: botón «Manifiesto» en la salida', page.locator('.pl-manifest').count() >= 1)
                shot(page, 'planning-salida-ordenador', False)
            else:
                check('planning: botón «Manifiesto» en la salida', False, 'día no encontrado')
            go(page, f'#/manifiesto?slot={slot}', 1300)
            check('manifiesto: 8 buceadores', page.locator('.mf-diver').count() == 8)
            check('manifiesto: aviso de buceadores sin grupo y sin firma', 'sin grupo' in page.inner_text('.mf-warn') and 'sin firmar' in page.inner_text('.mf-warn'))
            shot(page, 'manifiesto-sin-repartir-ordenador')
            page.fill('#mf-max', '3'); page.dispatch_event('#mf-max', 'change'); page.wait_for_timeout(900)
            page.click('#mf-suggest'); page.wait_for_timeout(700)
            check('reparto: confirmación con resumen', page.locator('#wd-confirm').count() == 1 and 'Se repartirán 8 buceadores' in page.inner_text('#wd-confirm'))
            page.click('#wd-confirm-ok'); page.wait_for_timeout(1300)
            cols = page.locator('.mf-col[data-group]:not([data-group=""])').count()
            check('reparto hecho en grupos de 3 como máximo', cols >= 3 and srv.sql('SELECT COUNT(*) n FROM manifest_entries WHERE slot_id=? AND group_id IS NULL', (slot,))[0]['n'] == 0)
            shot(page, 'manifiesto-reparto-ordenador')
            # Drag one diver into the first group: over the maximum -> warning
            for _ in range(4):
                first = page.locator('.mf-col[data-group]:not([data-group=""])').first
                if first.locator('.mf-diver').count() > 3: break
                page.locator('.mf-col[data-group]:not([data-group=""])').nth(1).locator('.mf-diver').first.drag_to(first); page.wait_for_timeout(1300)
            check('arrastrar: el grupo supera el máximo y se avisa', page.locator('.mf-col.is-over').count() >= 1 and 'máximo 3' in page.inner_text('.mf-warn'))
            # Group: boat and guide
            page.locator('[data-edit]').first.click(); page.wait_for_timeout(500)
            page.select_option('#mfg-guide', 'other'); page.fill('#mfg-other', 'Iván Guía'); page.click('#mfg-save'); page.wait_for_timeout(1100)
            check('grupo con guía externo', 'Iván Guía' in page.inner_text('.mf-board'))
            # Boat view and print view
            go(page, f'#/manifiesto?slot={slot}&vista=barco', 1200)
            txt = page.inner_text('.mf-boat-view')
            check('vista para el barco: contacto de emergencia compartido', 'Javier Lucía' in txt and '+34 600 111 222' in txt)
            check('vista para el barco: tallas y nitrox', 'Aletas 38-39' in txt and 'Nitrox' in txt)
            page.emulate_media(media='print')
            check('impresión A4: tabla limpia sin menús', page.locator('.mf-print table').count() >= 3 and not page.locator('.site-header').is_visible())
            shot(page, 'manifiesto-impresion-a4')
            if shots: page.pdf(path=str(shots / 'manifiesto-impresion-a4.pdf'), format='A4')
            page.emulate_media(media='screen')
            check('centro sin errores JS', not errors, errors)
            ctx.close()

            # ---- The diver signs from «Mi reserva» on a phone
            ctx, page, errors = session('diver_lucia7', width=390)
            go(page, f"#/reserva?id={bookings['lucia7']}", 1400)
            check('mi reserva: tarjeta del descargo pendiente', page.locator('.wv-card').count() == 1 and 'Pendiente de firma' in page.inner_text('.wv-card'))
            shot(page, 'mi-reserva-descargo-movil')
            page.locator('[data-wv-seat="1"]').click(); page.wait_for_timeout(600)
            shot(page, 'firma-movil', False)
            page.click('#wvs-send'); page.wait_for_timeout(400)
            check('firma: no se envía sin casilla ni firma', not srv.sql('SELECT 1 FROM waiver_signatures WHERE booking_id=?', (bookings['lucia7'],)))
            page.check('#wvs-ok'); draw(page, '#wvs-pad'); page.click('#wvs-send'); page.wait_for_timeout(1100)
            sig = srv.sql('SELECT id,method,signer_name FROM waiver_signatures WHERE booking_id=?', (bookings['lucia7'],))
            check('firma desde «Mi reserva» guardada', sig and sig[0]['method'] == 'online')
            check('mi reserva: firmado con PDF', 'Firmado' in page.inner_text('.wv-card') and page.locator('.wv-card a[href$=".pdf"]').count() == 1)
            pdf = page.evaluate(f"fetch('/api/waivers/{sig[0]['id'] if sig else 0}.pdf').then(r=>r.headers.get('content-type'))")
            check('PDF del descargo firmado', pdf == 'application/pdf')
            check('móvil sin desbordamiento', page.evaluate('document.documentElement.scrollWidth') <= 392)
            check('buceador sin errores JS', not errors, errors)
            ctx.close()

            # ---- Check-in on the boat (phone): the centre takes the companion's signature; manifest marks it
            ctx, page, errors = session('center_mfweb', width=390)
            go(page, f"#/reserva?id={bookings['mario7']}", 1400)
            page.locator('[data-wv-seat="2"]').click(); page.wait_for_timeout(600)
            page.check('#wvs-ok'); page.fill('#wvs-name', 'Elena Acompañante Ruiz'); draw(page, '#wvs-pad'); page.click('#wvs-send'); page.wait_for_timeout(1100)
            check('firma en el check-in (dispositivo del centro)', srv.sql("SELECT method FROM waiver_signatures WHERE booking_id=? AND seat=2", (bookings['mario7'],))[0]['method'] == 'checkin')
            go(page, f'#/manifiesto?slot={slot}', 1300)
            check('manifiesto en móvil: «Firmado» marcado', page.locator('.mf-badge.good').count() == 2)
            check('manifiesto en móvil: sin desbordamiento', page.evaluate('document.documentElement.scrollWidth') <= 392)
            shot(page, 'manifiesto-movil')
            btn = page.locator('[data-move]').first
            btn.click(); page.wait_for_timeout(500)
            check('móvil: «Mover» abre los grupos', page.locator('#mf-move [data-to]').count() >= 2)
            shot(page, 'mover-movil', False)
            page.locator('#mf-move [data-to]:not([disabled])').first.click(); page.wait_for_timeout(1100)
            go(page, f'#/manifiesto?slot={slot}&vista=barco', 1200)
            shot(page, 'vista-barco-movil')
            check('centro (móvil) sin errores JS', not errors, errors)
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
