"""v50.48 · App móvil (Capacitor), Tanda 1, in a real phone-sized browser (390 × 844 and 360 × 800).
The app shows the web in «modo app»: the same pages are opened here with the user agent of WORLDIVES Pruebas
(«WorldivesApp/1.0 pruebas») or with «?app=1». Checks:
- visitor: tabs Inicio · Explorar · Entrar, no site header, «Salidas con plazas cerca de ti», the quick booking sheet
  asks for the session at the end and opens again after signing in;
- diver: five tabs, next dive with Cómo llegar · Ver reserva · WhatsApp, booking in the sheet (paid: Stripe comes back to
  /app/vuelta with the scheme of the test app; on request: «Solicitud enviada»), Reservas, Buddies (pending), Mi área;
- Explorar: full-screen map, sheet of three heights, «Salidas con plazas», the card synced with the marker;
- Buscar, the centre's ficha with Llamar · WhatsApp · Cómo llegar · Compartir and the fixed «Desde … · Reservar» bar;
- Ajustes: Noche, Enorme and the three languages (every text of the app screens translated in en and fr);
- WORLDIVES Pruebas: the band, the quick entry with a test account and «Reportar fallo» (test environment only);
- nothing goes out of the screen at 360 px, no JavaScript errors.
Usage: python tests/navegador/e2e_app.py [--shots DIR]
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]   # tests/navegador and tests (helpers)
from helpers import ServerTestCase, Server  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
UA = 'Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36 WorldivesApp/1.0 pruebas'
FAKE_CAPACITOR = """
window.__cap = {listeners: {}, opened: [], closed: 0, min: false, shared: null,
  fire(plugin, ev, data) { (this.listeners[plugin + ':' + ev] || []).forEach(fn => fn(data || {})); }};
const on = (plugin) => (ev, fn) => { (window.__cap.listeners[plugin + ':' + ev] ||= []).push(fn); return Promise.resolve({ remove() {} }); };
window.Capacitor = { isNativePlatform: () => true, Plugins: {
  App: { addListener: on('App'), getInfo: async () => ({ name: 'WORLDIVES Pruebas', version: '1.0.99', build: '99' }), minimizeApp: async () => { window.__cap.min = true; }, exitApp: async () => {} },
  Browser: { addListener: on('Browser'), open: async ({ url }) => { window.__cap.opened.push(url); }, close: async () => { window.__cap.closed++; } },
  Device: { getInfo: async () => ({ manufacturer: 'Google', model: 'Pixel 8', operatingSystem: 'android', osVersion: '15' }) },
  Share: { share: async (o) => { window.__cap.shared = o; } },
  SystemBars: { setStyle: async () => {} }, SplashScreen: { hide: async () => {} },
}};
"""
OWN = ['#/', '#/explorar', '#/buscar', '#/reservas', '#/buddies', '#/mi-area', '#/ajustes']


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


def run(shots: Path | None):
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))

    stripe = StripeMock()
    ServerTestCase.server = Server({'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': stripe.base}).start(); srv = ServerTestCase.server
    try:
        t = ServerTestCase('run')
        admin = t.make_admin()
        near = t.make_center(admin, 'cerca', phone='+34 600 000 011'); far = t.make_center(admin, 'lejos', phone='965 000 000')
        cn, cf = near.user['center_id'], far.user['center_id']
        srv.sql("UPDATE centers SET name='Centro de Buceo Xàbia', latitude=38.79, longitude=0.18, address='Puerto de Xàbia, pantalán 3', stripe_account_id='acct_c', stripe_charges_enabled=1, stripe_payouts_enabled=1 WHERE id=?", (cn,))
        srv.sql("UPDATE centers SET name='Estartit Diving', latitude=41.98, longitude=3.22 WHERE id=?", (cf,))
        near.post('/api/center-equipment', {'code': 'full_kit', 'price': 25}); near.post('/api/center-equipment', {'code': 'computer', 'price': 8})
        s1 = near.post('/api/provider-services', {'title': 'Doble inmersión en barco', 'price': 45, 'booking_mode': 'payment'}).json['id']
        for d, h in ((1, '09:00'), (2, '09:00'), (3, '09:00')):
            near.post('/api/provider-services/slot', {'service_id': s1, 'slot_date': day(d), 'slot_time': h, 'spots_total': 10})
        s2 = far.post('/api/provider-services', {'title': 'Islas Medes', 'price': 60, 'booking_mode': 'request'}).json['id']
        far.post('/api/provider-services/slot', {'service_id': s2, 'slot_date': day(1), 'slot_time': '10:00', 'spots_total': 6})
        diver = t.make_diver('app1')
        # A past dive (for «Repetir») and an upcoming one (for «Próxima inmersión»)
        slot3 = srv.sql('SELECT id FROM service_slots WHERE service_id=? ORDER BY slot_date DESC', (s1,))[0]['id']
        b_next = diver.post('/api/bookings', {'center_id': cn, 'service_id': s1, 'slot_id': slot3, 'participants': 1}).json['id']
        srv.sql("UPDATE bookings SET status='confirmed', payment_status='paid' WHERE id=?", (b_next,))
        b_old = diver.post('/api/bookings', {'center_id': cf, 'service_id': s2, 'participants': 1, 'booking_date': day(1), 'booking_time': '10:00'}).json.get('id')
        if b_old: srv.sql("UPDATE bookings SET status='completed', booking_date=? WHERE id=?", (day(-20), b_old))
        base = srv.base

        with sync_playwright() as p:
            browser = chromium(p)

            def phone(width=390, height=844, ua=UA, lang='es-ES'):
                ctx = browser.new_context(viewport={'width': width, 'height': height}, is_mobile=True, has_touch=True, device_scale_factor=2, locale=lang,
                                          **({'user_agent': ua} if ua else {}))
                page = ctx.new_page(); errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.route('https://checkout.stripe.test/**', lambda route: route.fulfill(status=200, body='<h1>Stripe Checkout (simulado)</h1>', content_type='text/html'))
                page.route('**/*tile.openstreetmap.org/**', lambda r: r.fulfill(status=204))
                return ctx, page, errors

            def go(page, route, wait=900):
                page.goto(base + '/' + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)

            def shot(page, name):
                if shots:
                    shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'))

            def login(page, user):
                go(page, '#/login', 600); page.fill('#login', user); page.fill('#password', PW); page.click('#login-form button[type=submit]'); page.wait_for_timeout(1200)

            tabs = lambda page: page.eval_on_selector_all('.wda-tab span:last-child', 'els => els.map(e => e.textContent.trim())')

            # ---------------------------------------------------------------- visitor in the browser preview (?app=1)
            ctx, page, errors = phone(ua=None)
            page.goto(base + '/?app=1#/'); page.wait_for_load_state('networkidle'); page.wait_for_timeout(1200)
            check('visitante · modo app activo con ?app=1', page.evaluate("document.documentElement.classList.contains('wd-app')"))
            check('visitante · sin cabecera ni pie de la web', not page.is_visible('.site-header') and not page.is_visible('.site-footer'))
            check('visitante · pestañas Inicio, Explorar, Entrar', tabs(page) == ['Inicio', 'Explorar', 'Entrar'], tabs(page))
            check('visitante · sin banda de pruebas en la vista previa', page.locator('.wda-banda').count() == 0)
            cards = page.locator('#wda-salidas .tarjeta-salida')
            check('visitante · salidas con plazas (las dos de mañana y más)', cards.count() >= 3, cards.count())
            shot(page, '01-visitante-inicio')
            page.click('[data-cuando="manana"]'); page.wait_for_timeout(700)
            titles = page.eval_on_selector_all('#wda-salidas h3', 'els => els.map(e => e.textContent)')
            check('visitante · «Mañana» filtra las salidas', sorted(titles) == ['Doble inmersión en barco', 'Islas Medes'], titles)
            page.locator('#wda-salidas [data-reservar]').first.click(); page.wait_for_timeout(900)
            check('visitante · la reserva rápida se abre en una hoja', page.is_visible('.wda-capa.abierta .hoja'))
            check('visitante · el botón pide la sesión al final', 'Entrar y reservar' in page.inner_text('#wda-confirmar'))
            shot(page, '02-visitante-hoja-reserva')
            page.click('#wda-confirmar'); page.wait_for_timeout(900)
            check('visitante · «Entrar y reservar» lleva a Entrar', '#/login' in page.url)
            page.fill('#login', 'diver_app1'); page.fill('#password', PW); page.click('#login-form button[type=submit]'); page.wait_for_timeout(1800)
            check('visitante → buceador · la hoja vuelve a abrirse tras entrar', page.is_visible('.wda-capa.abierta .hoja'))
            check('buceador · cinco pestañas', tabs(page) == ['Inicio', 'Explorar', 'Reservas', 'Buddies', 'Mi área'], tabs(page))
            check('sin errores de JavaScript (vista previa)', not errors, errors[:3])
            ctx.close()

            # ---------------------------------------------------------------- diver inside WORLDIVES Pruebas (user agent)
            ctx, page, errors = phone()
            login(page, 'diver_app1'); go(page, '#/', 1400)
            check('pruebas · banda fija «Pruebas» con «Reportar fallo»', page.is_visible('.wda-banda') and 'Reportar fallo' in page.inner_text('.wda-banda'))
            check('buceador · próxima inmersión con anillo y acciones', page.is_visible('#wda-proxima .anillo') and page.locator('#wda-proxima .accion').count() == 3)
            check('buceador · «Repetir» con el centro donde ya buceó', 'Estartit Diving' in page.inner_text('#wda-repetir') if b_old else True)
            shot(page, '03-buceador-inicio')
            page.click('#wda-proxima [data-wa]'); page.wait_for_timeout(600)
            msg = page.input_value('#wda-wa-txt')
            check('WhatsApp · mensaje ya escrito con la reserva', msg.startswith('Hola, soy Buceador app1') and 'Doble inmersión en barco' in msg, msg)
            check('WhatsApp · en Pruebas no se abre (solo se enseña)', 'no se abre WhatsApp' in page.inner_text('.wda-capa .hoja-pie'))
            shot(page, '04-whatsapp-centro')
            page.click('.wda-capa .hoja-cerrar'); page.wait_for_timeout(400)
            # booking with payment: the sheet, «Cambiar» on each line, the total and Stripe coming back to the app
            card = page.locator('#wda-salidas .tarjeta-salida', has_text='Doble inmersión en barco').first
            t0 = time.monotonic()
            card.locator('[data-reservar]').click(); page.wait_for_timeout(1000)
            check('reserva · total del presupuesto (45 €)', '45' in page.inner_text('.wda-capa .hoja-pie'), page.inner_text('.wda-capa .hoja-pie'))
            page.click('[data-cambiar="pers"]'); page.wait_for_timeout(300); page.click('[data-pax="1"]'); page.wait_for_timeout(700)
            check('reserva · «Cambiar» personas recalcula el total (90 €)', '90' in page.inner_text('.wda-capa .hoja-pie'), page.inner_text('.wda-capa .hoja-pie'))
            page.click('[data-cambiar="equipo"]'); page.wait_for_timeout(300)
            check('reserva · equipo del centro con su precio', page.locator('[data-equipo="full_kit"]').count() == 1)
            page.check('[data-equipo="full_kit"]'); page.wait_for_timeout(800)
            check('reserva · alquiler suma por persona (140 €)', '140' in page.inner_text('.wda-capa .hoja-pie'), page.inner_text('.wda-capa .hoja-pie'))
            page.click('[data-cambiar="fecha"]'); page.wait_for_timeout(300)
            check('reserva · «Cambiar» la salida enseña las otras fechas', page.locator('[data-slot]').count() >= 2)
            shot(page, '05-reserva-rapida')
            check('reserva · botón «Reservar y pagar»', 'Reservar y pagar' in page.inner_text('#wda-confirmar'))
            page.click('#wda-confirmar'); page.wait_for_timeout(1500)
            secs = time.monotonic() - t0
            sess = [c for c in stripe.calls if c['path'] == '/v1/checkout/sessions' and c['method'] == 'POST'][-1]['params']
            check('pago · Stripe vuelve a la app de pruebas (/app/vuelta)', sess['success_url'].startswith(base + '/app/vuelta?esquema=com.worldives.app.pruebas'), sess['success_url'])
            check('pago · abre la página de Stripe', 'checkout.stripe.test' in page.url, page.url)
            check(f'reserva en {secs:.1f} s (promesa ≤ 30 s)', secs <= 30)
            bk = srv.sql('SELECT participants, price, needs_equipment FROM bookings ORDER BY id DESC LIMIT 1')[0]
            check('reserva · 2 personas y equipo guardados (140 €)', bk['participants'] == 2 and bk['needs_equipment'] == 1 and float(bk['price']) == 140, bk)
            # on request
            go(page, '#/', 1200); page.click('[data-cuando="manana"]'); page.wait_for_timeout(700)
            page.locator('#wda-salidas .tarjeta-salida', has_text='Islas Medes').locator('[data-reservar]').click(); page.wait_for_timeout(900)
            check('solicitud · botón «Enviar solicitud» y «No pagas nada…»', 'Enviar solicitud' in page.inner_text('#wda-confirmar') and 'No pagas nada' in page.inner_text('.wda-capa .hoja-pie'))
            page.click('#wda-confirmar'); page.wait_for_timeout(1200)
            check('solicitud · confirmación en la hoja', 'Solicitud enviada' in page.inner_text('.wda-capa'))
            shot(page, '06-solicitud-enviada')
            page.click('.wda-capa .hoja-cerrar'); page.wait_for_timeout(300)
            # Reservas
            go(page, '#/reservas', 1200)
            txt = page.inner_text('#app')
            check('reservas · próximas con estado (color, icono y texto)', 'Islas Medes' in txt and page.locator('#wda-res .wtag').count() >= 2)
            check('reservas · contador de pagos pendientes en la pestaña', page.locator('.wda-tab .cont').count() == 1)
            shot(page, '07-reservas')
            page.click('[data-seg="hist"]'); page.wait_for_timeout(300)
            check('reservas · historial', 'Islas Medes' in page.inner_text('#wda-res') if b_old else True)
            go(page, '#/buddies'); check('buddies · pendiente (no existe en el servidor)', 'Pendiente' in page.inner_text('#app'))
            go(page, '#/mi-area', 1200); check('mi área · cifras y accesos', page.is_visible('#wda-c-puntos') and 'Log Book' in page.inner_text('#app'))
            shot(page, '08-mi-area')
            # Explorar
            go(page, '#/explorar', 2000)
            check('explorar · mapa a pantalla completa con hoja', page.is_visible('#wda-mapa.leaflet-container') and page.get_attribute('#wda-hoja', 'data-altura') == 'asomada')
            shot(page, '09-explorar')
            page.click('[data-ver="salidas"]'); page.wait_for_timeout(1500)
            check('explorar · salidas con plazas en el mapa', page.locator('#wda-mapa .marca-c').count() >= 2, page.locator('#wda-mapa .marca-c').count())
            check('explorar · «Buscar en esta zona» no sale si el mapa lo mueve la app', page.is_hidden('#wda-zona'))
            page.locator('#wda-mapa .marca-c').first.click(); page.wait_for_timeout(800)
            check('explorar · tarjeta sincronizada con el marcador', page.is_visible('#wda-carrusel') and page.locator('#wda-mapa .marca-c.is-sync').count() == 1)
            shot(page, '10-explorar-tarjeta')
            page.click('#wda-verlista'); page.wait_for_timeout(500)
            check('explorar · «Ver lista» sube la hoja', page.get_attribute('#wda-hoja', 'data-altura') == 'completa')
            shot(page, '11-explorar-lista')
            page.click('#wda-verlista'); page.wait_for_timeout(400)
            box = page.locator('#wda-mapa').bounding_box()
            page.mouse.move(box['x'] + 100, box['y'] + 400); page.mouse.down(); page.mouse.move(box['x'] + 220, box['y'] + 470, steps=8); page.mouse.up(); page.wait_for_timeout(700)
            check('explorar · «Buscar en esta zona» sale al mover el mapa', page.is_visible('#wda-zona'))
            page.click('#wda-capas'); page.wait_for_timeout(500)
            check('explorar · capas Mapa, Satélite y Relieve en una hoja', page.locator('.wda-capa [data-mapmode]').count() == 3)
            page.click('.wda-capa .hoja-cerrar'); page.wait_for_timeout(300)
            # Buscar and the centre's ficha
            go(page, '#/buscar', 600); page.fill('#wda-q', 'xabia'); page.wait_for_timeout(1200)
            check('buscar · encuentra el centro', 'Centro de Buceo Xàbia' in page.inner_text('#wda-res'))
            shot(page, '12-buscar')
            go(page, f'#/centro?id={cn}', 2200)
            check('ficha · Llamar, WhatsApp, Cómo llegar y Compartir', page.locator('.wda-ficha .accion').count() == 4)
            check('ficha · barra fija «Desde 45 € · Reservar»', page.is_visible('#wda-barra') and '45' in page.inner_text('#wda-barra'))
            shot(page, '13-ficha-centro')
            go(page, f'#/centro?id={cf}', 2000)
            check('ficha · sin móvil con prefijo: WhatsApp desactivado', page.get_attribute('.wda-ficha [data-wa]', 'aria-disabled') == 'true')
            # Ajustes: theme, size, languages
            go(page, '#/ajustes', 1000)
            check('ajustes · versión visible', 'web v50.48' in page.inner_text('#wda-version'), page.inner_text('#wda-version'))
            page.click('[data-tema="noche"]'); page.click('[data-tamano="enorme"]'); page.wait_for_timeout(300)
            check('ajustes · tema Noche y texto Enorme', page.evaluate("document.documentElement.dataset.wdaTema") == 'noche' and page.evaluate("document.documentElement.dataset.wdaTamano") == 'enorme')
            shot(page, '14-ajustes-noche-enorme')
            go(page, '#/', 1400); shot(page, '15-inicio-noche-enorme')
            go(page, '#/ajustes', 800); page.click('[data-tema="clasico"]'); page.click('[data-tamano="normal"]')
            check('ajustes · solo tres idiomas', page.locator('[data-lang]').count() == 3)
            check('sin errores de JavaScript (buceador)', not errors, errors[:3])
            ctx.close()

            # ---------------------------------------------------------------- languages: every text of the app screens translated
            for lang in ('en', 'fr'):
                ctx, page, errors = phone(lang={'en': 'en-GB', 'fr': 'fr-FR'}[lang])
                page.add_init_script(f"localStorage.setItem('wod-language','{lang}'); localStorage.setItem('wd-i18n-debug','1');")
                login(page, 'diver_app1')
                misses = set()
                for r in OWN:
                    go(page, r, 1300)
                    misses |= set(page.evaluate('window.__wdI18nMisses ? [...window.__wdI18nMisses] : []'))
                go(page, '#/', 1200); page.locator('#wda-salidas [data-reservar]').first.click(); page.wait_for_timeout(1000)
                for k in ('pers', 'equipo', 'tit', 'nota'):
                    if page.locator(f'[data-cambiar="{k}"]').count(): page.click(f'[data-cambiar="{k}"]'); page.wait_for_timeout(250)
                misses |= set(page.evaluate('window.__wdI18nMisses ? [...window.__wdI18nMisses] : []'))
                shot(page, f'16-reserva-{lang}')
                check(f'idioma {lang} · pestañas traducidas', tabs(page)[0] in ('Home', 'Accueil'), tabs(page))
                check(f'idioma {lang} · banda de pruebas traducida', page.inner_text('.wda-banda').startswith(('Testing', 'Tests')), page.inner_text('.wda-banda'))
                check(f'idioma {lang} · todo traducido en las pantallas de la app', not misses, json.dumps(sorted(misses), ensure_ascii=False))
                # the device in German: the app speaks English
                ctx.close()
            ctx, page, errors = phone(lang='de-DE')
            page.add_init_script("localStorage.setItem('wod-language','de');")
            go(page, '#/', 1200)
            check('idioma · un móvil en alemán ve la app en inglés', page.evaluate('document.documentElement.lang') == 'en' and tabs(page)[0] == 'Home', tabs(page))
            ctx.close()

            # ---------------------------------------------------------------- 360 × 800: nothing goes out of the screen
            ctx, page, errors = phone(360, 800)
            login(page, 'diver_app1')
            wide = []
            for size in ('normal', 'enorme'):
                page.evaluate(f"localStorage.setItem('wda-tamano','{size}')")
                for r in OWN:
                    go(page, r, 1100)
                    w = page.evaluate('[document.scrollingElement.scrollWidth, innerWidth]')
                    if w[0] > w[1]: wide.append((size, r, w))
            check('360 px · nada se sale de la pantalla (Normal y Enorme)', not wide, wide)
            page.evaluate("localStorage.setItem('wda-tamano','normal')")
            go(page, '#/', 1200); shot(page, '17-inicio-360')
            check('sin errores de JavaScript (360 px)', not errors, errors[:3])
            ctx.close()

            # ---------------------------------------------------------------- the native glue, with a simulated Capacitor
            ctx, page, errors = phone()
            page.add_init_script(FAKE_CAPACITOR)
            login(page, 'diver_app1'); go(page, '#/', 1400)
            card = page.locator('#wda-salidas .tarjeta-salida', has_text='Doble inmersión en barco').first
            card.locator('[data-reservar]').click(); page.wait_for_timeout(900)
            page.evaluate("window.__cap.fire('App', 'backButton')"); page.wait_for_timeout(500)
            check('nativo · el botón atrás de Android cierra la hoja', page.locator('.wda-capa').count() == 0)
            card.locator('[data-reservar]').click(); page.wait_for_timeout(900); page.click('#wda-confirmar'); page.wait_for_timeout(1500)
            opened = page.evaluate('window.__cap.opened')
            check('nativo · el pago se abre en la pestaña del navegador (Custom Tabs)', len(opened) == 1 and 'checkout.stripe.test' in opened[0], opened)
            check('nativo · la app sigue en la reserva mientras se paga', page.url.startswith(base), page.url)
            page.evaluate("window.__cap.fire('App', 'appUrlOpen', {url: 'com.worldives.app.pruebas://pago?session_id=cs_test_vuelta'})"); page.wait_for_timeout(900)
            check('nativo · al volver de Stripe abre «Confirmando tu pago»', '#/pago-ok?session_id=cs_test_vuelta' in page.url and page.evaluate('window.__cap.closed') == 1, page.url)
            page.evaluate("window.__cap.fire('App', 'appUrlOpen', {url: 'com.worldives.app.pruebas://pago?pago=cancelado&reserva=1'})"); page.wait_for_timeout(900)
            check('nativo · pago cancelado: vuelve a la reserva', '#/reserva?id=1' in page.url, page.url)
            page.evaluate("window.__cap.fire('App', 'appUrlOpen', {url: 'otra.app://pago?session_id=x'})"); page.wait_for_timeout(400)
            check('nativo · un enlace de otra app no hace nada', '#/reserva?id=1' in page.url, page.url)
            go(page, '#/ajustes', 1000)
            check('nativo · versión de la app y de la web en Ajustes', 'WORLDIVES Pruebas 1.0.99 (99)' in page.inner_text('#wda-version'), page.inner_text('#wda-version'))
            go(page, '#/', 900); page.evaluate("window.__cap.fire('App', 'backButton')"); page.wait_for_timeout(300)
            check('nativo · atrás en Inicio deja la app en segundo plano', page.evaluate('window.__cap.min') is True)
            go(page, f'#/centro?id={cn}', 2000); page.click('.wda-ficha [data-compartir]'); page.wait_for_timeout(400)
            shared = page.evaluate('window.__cap.shared') or {}
            check('nativo · Compartir usa la hoja del sistema', f'#/centro?id={cn}' in shared.get('url', ''), shared)
            check('sin errores de JavaScript (nativo simulado)', not errors, errors[:3])
            ctx.close()

            # ---------------------------------------------------------------- a centre in Tanda 1: its web panel inside the app
            ctx, page, errors = phone()
            login(page, 'center_cerca'); go(page, '#/', 1200)
            check('centro · aviso «Centro PRO llega a la app en la Tanda 2»', 'Tanda 2' in page.inner_text('#app'))
            check('centro · pestañas Inicio, Mi panel, Explorar, Mi área', tabs(page) == ['Inicio', 'Mi panel', 'Explorar', 'Mi área'], tabs(page))
            shot(page, '19-centro-inicio')
            go(page, '#/admin', 2200)
            check('centro · el panel de la web se abre dentro de la app', page.locator('.wda-tab[aria-current="page"]').inner_text().strip() == 'Mi panel' and len(page.inner_text('#app')) > 200)
            shot(page, '20-centro-panel-web')
            check('sin errores de JavaScript (centro)', not errors, errors[:3])
            ctx.close()
    finally:
        srv.stop(); stripe.stop()

    # ---------------------------------------------------------------- the test environment (WOD_DEMO_MODE=1)
    demo = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo'}).start()
    try:
        res = demo.run_cli('--create-admin', '--email', 'probador@example.org', '--username', 'probador', '--name', 'Bea Probadora', env={'WOD_ADMIN_PASSWORD': 'probador-seguro-2026'})
        assert res.returncode == 0, res.stdout + res.stderr
        demo.sql("UPDATE users SET username='probador.prueba', role='recreational' WHERE username='probador'")
        with sync_playwright() as p:
            browser = chromium(p)
            ctx = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, device_scale_factor=2, locale='es-ES', user_agent=UA)
            page = ctx.new_page(); errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(demo.base + '/#/pruebas-entrar?cuenta=probador.prueba'); page.wait_for_load_state('networkidle'); page.wait_for_timeout(1800)
            check('pruebas · entrada rápida con la cuenta de prueba', page.evaluate("location.hash") in ('#/', '') and page.locator('.wda-tab').count() == 5)
            check('pruebas · la cinta de demo de la web no se duplica', not page.is_visible('#demo-ribbon'))
            page.click('#wda-fallo'); page.wait_for_timeout(900)
            check('reportar fallo · pantalla, versión, móvil y hora', all(x in page.inner_text('.wda-capa') for x in ('Pantalla', 'Versión', 'Móvil', 'Hora')))
            if shots: page.screenshot(path=str(shots / '18-reportar-fallo.png'))
            page.fill('#wda-qp', 'El total no cambia al añadir el equipo'); page.click('#wda-enviar-fallo'); page.wait_for_timeout(900)
            folder = Path(demo.db).parent / 'fallos'
            saved = [json.loads(f.read_text(encoding='utf-8')) for f in folder.glob('*.json')] if folder.exists() else []
            check('reportar fallo · guardado en la carpeta «fallos»', len(saved) == 1 and saved[0]['cuenta'] == 'probador.prueba', saved)
            go2 = lambda r: (page.goto(demo.base + '/' + r), page.wait_for_timeout(900))
            go2('#/ajustes')
            check('pruebas · «Cambiar de servidor o de cuenta de prueba» en Ajustes', 'Cambiar de servidor' in page.inner_text('#app'))
            check('sin errores de JavaScript (pruebas)', not errors, errors[:3])
            ctx.close()
    finally:
        demo.stop()

    width = max(len(n) for n, _, _ in checks)
    for name, ok, detail in checks:
        print(f"{'OK ' if ok else 'MAL'} {name.ljust(width)} {'' if ok else detail}")
    bad = [c for c in checks if not c[1]]
    print(f'\n{len(checks) - len(bad)}/{len(checks)} comprobaciones correctas')
    return 1 if bad else 0


if __name__ == '__main__':
    out = None
    if '--shots' in sys.argv:
        out = Path(sys.argv[sys.argv.index('--shots') + 1])
    sys.exit(run(out))
