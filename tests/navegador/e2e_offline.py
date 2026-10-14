"""Encargo 2, punto 6 in a real browser (phone): the crew opens «Check-in en el barco» with connection, loses it,
reloads the app without network (service worker + data kept on the device), marks «Presente», «No se presentó» and
a note; the indicator shows the pending changes; meanwhile the desk changes the same diver; back online the changes
are sent and the conflict screen lets the crew choose. Data of past days is deleted; no documents are stored.
Usage: python tests/e2e_offline.py [--shots DIR]
"""
from __future__ import annotations

import datetime
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]   # tests/navegador and tests (helpers)
from helpers import ServerTestCase, Server, midday_clock  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
ZONE = midday_clock()   # «today at 23:58» ahead whatever the hour (tests/helpers.py)
TODAY = datetime.date.today().isoformat()


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
        center = t.make_center(admin, 'sincob', phone='+34 600 480 001')
        cid = center.user['center_id']
        sid = center.post('/api/provider-services', {'title': 'Salida a las Medas', 'price': 50, 'booking_mode': 'request'}).json['id']
        srv.sql('UPDATE provider_services SET timezone=? WHERE id=?', (ZONE, sid))
        slot = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': TODAY, 'slot_time': '23:58', 'spots_total': 8}).json['slot_id']
        diver = t.make_diver('marinero6')
        diver.post('/api/account/profile', {'certification_id': 2, 'emergency_contact_name': 'Juan Marinero', 'emergency_contact_phone': '+34 600 222 111', 'suit_size': 'L'})
        bid = diver.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': 2}).json['id']
        srv.sql("UPDATE bookings SET status='confirmed' WHERE id=?", (bid,))
        base = srv.base
        with sync_playwright() as p:
            browser = chromium(p)
            ctx = browser.new_context(viewport={'width': 390, 'height': 844}, locale='es-ES', has_touch=True, service_workers='allow', timezone_id=ZONE)
            ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
            page = ctx.new_page(); errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))

            def shot(name):
                if shots:
                    shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'), full_page=True)

            page.goto(base + '/#/login'); page.wait_for_selector('#login'); page.fill('#login', 'center_sincob'); page.fill('#password', PW)
            page.click('#login-form button[type=submit]'); page.wait_for_timeout(1000)
            # With connection: the day is kept on the device
            page.goto(base + '/#/barco'); page.wait_for_load_state('networkidle'); page.wait_for_timeout(1500)
            check('hoy en el barco: la salida del día', page.locator('.boat-slot').count() == 1)
            stored = page.evaluate(f"localStorage.getItem('wd-day-{TODAY}')") or ''
            check('manifiesto del día guardado en el dispositivo', 'Juan Marinero' in stored)
            check('sin documentos en el dispositivo', '/api/documents' not in stored and 'document_type' not in stored)
            page.evaluate("navigator.serviceWorker && navigator.serviceWorker.ready")
            page.wait_for_timeout(1500)
            shot('hoy-en-el-barco-movil')
            # Without connection, even after reloading the app
            ctx.set_offline(True)
            page.reload(); page.wait_for_timeout(2500)
            page.evaluate(f"location.hash='#/barco?slot={slot}&fecha={TODAY}'"); page.wait_for_timeout(1500)
            body = page.inner_text('body')
            check('sin conexión: la app abre con los datos guardados', 'Sin conexión: usando los datos guardados' in body and 'Juan Marinero' in body, body[:200])
            page.locator('[data-ck="present"][data-s="1"]').click(); page.wait_for_timeout(500)
            page.locator('[data-ck="no_show"][data-s="2"]').click(); page.wait_for_timeout(500)
            page.locator('[data-note]').first.click(); page.wait_for_timeout(400); page.fill('#bn-text', 'Trae su propio ordenador'); page.click('#bn-ok'); page.wait_for_timeout(500)
            ind = page.inner_text('#wd-offline') if page.locator('#wd-offline').count() else ''
            check('indicador «Sin conexión · 3 cambios pendientes»', 'Sin conexión' in ind and '3 cambios pendientes' in ind, ind)
            check('nada enviado todavía', not srv.sql('SELECT 1 FROM manifest_entries WHERE booking_id=? AND (checked_in_at IS NOT NULL OR no_show=1)', (bid,)))
            shot('check-in-sin-conexion-movil')
            # Meanwhile the desk marks the companion as present
            center.post('/api/manifest/sync', {'changes': [{'slot_id': slot, 'booking_id': bid, 'seat': 2, 'field': 'status', 'base': '', 'value': 'present'}]})
            # Back online: the changes are sent; one conflict
            ctx.set_offline(False); page.wait_for_timeout(3000)
            check('al volver la conexión: pantalla de conflictos', page.locator('#sync-conflicts').count() == 1)
            shot('conflictos-movil')
            if page.locator('#sync-conflicts').count():
                page.click('#cf-ok'); page.wait_for_timeout(2500)   # keeps the crew's value («No se presentó»)
            e = srv.sql('SELECT seat,checked_in_at,no_show,note,checkin_source FROM manifest_entries WHERE booking_id=? ORDER BY seat', (bid,))
            check('sincronizado: presente, no se presentó y nota', e[0]['checked_in_at'] and e[0]['note'] == 'Trae su propio ordenador' and e[1]['no_show'] == 1 and e[0]['checkin_source'] == 'offline', e)
            check('cola vacía e indicador oculto', page.evaluate("JSON.parse(localStorage.getItem('wd-sync-queue')||'[]').length") == 0 and page.locator('#wd-offline').count() == 0)
            # End of the day: the data of past days is deleted
            page.evaluate("localStorage.setItem('wd-day-2000-01-01','{\"slots\":[]}')")
            page.goto(base + '/#/barco'); page.wait_for_load_state('networkidle'); page.wait_for_timeout(1200)
            check('datos de días anteriores borrados', page.evaluate("localStorage.getItem('wd-day-2000-01-01')") is None)
            check('móvil sin desbordamiento', page.evaluate('document.documentElement.scrollWidth') <= 392)
            check('sin errores JS', not errors, errors)
            # Signing out deletes the day kept on the device
            page.goto(base + '/#/cuenta'); page.wait_for_timeout(1200)
            if page.locator('#logout').count():
                page.click('#logout'); page.wait_for_timeout(1000)
                check('cerrar sesión borra el día guardado', page.evaluate(f"localStorage.getItem('wd-day-{TODAY}')") is None)
            ctx.close(); browser.close()
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
