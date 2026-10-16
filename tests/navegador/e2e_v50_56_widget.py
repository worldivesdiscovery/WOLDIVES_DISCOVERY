"""v50.56 · Bloque 1, Partes C y D en un navegador real: el widget de reservas en una web de centro de ejemplo.

Comprueba, con Chromium:
  - la web de ejemplo (scripts/demo/web-de-centro-ejemplo.html) servida desde otro origen, con los 3 formatos;
  - el widget no cambia los estilos de la página ni se deja cambiar por ellos (va en un iframe);
  - una solicitud «Bajo petición» de principio a fin y los eventos «reserva iniciada» / «reserva completada» en la página;
  - «Pago al reservar»: el pago se abre en una ventana nueva (Stripe simulado) y el widget ve la reserva confirmada;
  - el botón abre la reserva encima de la página y se cierra con Esc;
  - en un dominio no autorizado el widget no se carga;
  - en el móvil no hay desplazamiento lateral;
  - los 9 idiomas, en el widget y en la página del centro (/c/<centro>);
  - la carga del widget con red 4G simulada (menos de 2 s).
Uso: python tests/navegador/e2e_v50_56_widget.py [--shots DIR]
"""
from __future__ import annotations

import functools
import http.server
import json
import re
import socket
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
from helpers import ServerTestCase, Server  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'app'))
from wod import widget_textos as wtx  # noqa: E402

TEMPLATE = ROOT / 'scripts' / 'demo' / 'web-de-centro-ejemplo.html'
FAST_4G = {'offline': False, 'latency': 150, 'downloadThroughput': 9 * 1024 * 1024 / 8, 'uploadThroughput': 9 * 1024 * 1024 / 8}


def chromium(p):
    exe = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    return p.chromium.launch(executable_path=exe) if Path(exe).exists() else p.chromium.launch()


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0)); return s.getsockname()[1]


def host_site(folder: Path, port: int):
    """The centre's own website: a plain static server on another origin (localhost:<port>)."""
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(folder))
    handler.log_message = lambda *a, **k: None
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


def run(shots: Path | None):
    stripe = StripeMock()
    srv = ServerTestCase.server = Server({'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': stripe.base}).start()
    t = ServerTestCase('run')
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))
        print(('OK   ' if ok else 'FALLA') + ' ' + name + (f' · {detail}' if detail else ''), flush=True)   # as it goes: a stop shows where

    def shot(page, name, full=True):
        if shots:
            shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'), full_page=full)

    folder = Path(tempfile.mkdtemp(prefix='web-centro-'))
    port = free_port(); site = None
    try:
        admin = t.make_admin()
        center = t.make_center(admin, 'bahia')
        cid = center.user['center_id']
        srv.sql("UPDATE centers SET name='Bahía Coralina',plan_code='pro',plan_status='active',plan_expires_at='2099-12-31',stripe_account_id='acct_bahia',"
                "stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cid,))
        req_sid = center.post('/api/provider-services', {'title': 'Bautizo de buceo', 'price': 75, 'booking_mode': 'request', 'max_participants': 4, 'duration_minutes': 150}).json['id']
        pay_sid = center.post('/api/provider-services', {'title': 'Doble inmersión en barco', 'price': 60, 'booking_mode': 'payment', 'max_participants': 8, 'duration_minutes': 240}).json['id']
        d1 = time.strftime('%Y-%m-%d', time.localtime(time.time() + 9 * 86400)); d2 = time.strftime('%Y-%m-%d', time.localtime(time.time() + 10 * 86400))
        center.post('/api/provider-services/slot', {'service_id': req_sid, 'slot_date': d1, 'slot_time': '10:00', 'spots_total': 6})
        pay_slot = center.post('/api/provider-services/slot', {'service_id': pay_sid, 'slot_date': d2, 'slot_time': '09:00', 'spots_total': 3}).json['slot_id']
        cfg = center.get('/api/provider/vender').json; slug = cfg['slug']
        r = center.post('/api/provider/vender', {'domains': [f'localhost:{port}'], 'color': '#0b7a75'})
        check('panel · dominio autorizado guardado', r.status == 200 and r.json['domains'] == [f'localhost:{port}'], r.json)
        html_page = TEMPLATE.read_text(encoding='utf-8').replace('__WORLDIVES__', srv.base).replace('__CENTRO__', slug).replace('__SERVICIO__', str(pay_sid))
        (folder / 'index.html').write_text(html_page, encoding='utf-8')
        for lang in wtx.LANGS:
            (folder / f'idioma-{lang}.html').write_text(html_page.replace('data-worldives="lista" data-centro', f'data-worldives="lista" data-idioma="{lang}" data-centro'), encoding='utf-8')
        site = host_site(folder, port)
        host = f'http://localhost:{port}'

        with sync_playwright() as p:
            browser = chromium(p)
            ctx = browser.new_context(viewport={'width': 1366, 'height': 900}, locale='es-ES')
            # The fake Stripe of the tests sends the payment window to a host that does not exist (checkout.stripe.test).
            # There the window shows a page, as Stripe's would: an error page that arrives late (a busy machine) used to
            # interrupt the walk while it was already simulating the return from the payment.
            ctx.route('https://checkout.stripe.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body='<!doctype html><title>Stripe (simulado)</title><p>Pago simulado</p>'))
            page = ctx.new_page(); errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(f'{host}/index.html'); page.wait_for_load_state('networkidle')
            lista = page.frame_locator('#lista iframe'); cal = page.frame_locator('#calendario iframe')
            lista.locator('.wr-card').first.wait_for(timeout=10000)
            check('lista · servicios del centro', lista.locator('.wr-card').count() == 2, lista.locator('.wr-card').count())
            check('lista · próximas fechas con plazas', lista.locator('.wr-chip').count() >= 2)
            cal.locator('.wr-cal').wait_for(timeout=10000)
            check('calendario · un solo servicio, con su calendario', 'Doble inmersión' in cal.locator('h2').inner_text())
            # Styles: the page keeps its own, the widget keeps its own
            h1_color = page.evaluate("getComputedStyle(document.querySelector('section h2')).color")
            own_btn = page.evaluate("getComputedStyle(document.getElementById('boton-propio')).backgroundColor")
            check('estilos de la página intactos', h1_color == 'rgb(46, 125, 50)' and own_btn == 'rgb(211, 47, 47)', (h1_color, own_btn))
            wbtn = lista.locator('.wr-btn').first.evaluate("e => [getComputedStyle(e).backgroundColor, getComputedStyle(e).fontFamily]")
            check('el widget no hereda los estilos de la página', wbtn[0] == 'rgb(11, 122, 117)' and 'Georgia' not in wbtn[1], wbtn)
            check('el widget no añade estilos ni cookies a la página', page.evaluate('document.styleSheets.length') == 1 and page.evaluate('document.cookie') == '')
            shot(page, 'widget-web-ejemplo-escritorio')
            # A request («Bajo petición») from the list
            lista.locator('.wr-card', has_text='Bautizo').locator('button.wr-btn').click()
            lista.locator('.wr-day.on').first.click(); lista.locator('[data-pick]').first.click()
            lista.locator('input[name=fullname]').fill('Lucía Web'); lista.locator('input[name=email]').fill('lucia.web@example.org')
            lista.locator('.wr-sum .wr-total').wait_for(timeout=8000)
            check('precio calculado por el servidor', '75' in lista.locator('.wr-sum .wr-total').inner_text())
            lista.locator('input[name=accept_policy]').check()
            t0 = time.time(); lista.locator('[data-go]').click()
            lista.locator('.wr-done h2').wait_for(timeout=15000)
            check('solicitud enviada desde la web del centro', 'Solicitud enviada' in lista.locator('.wr-done').inner_text(), lista.locator('.wr-done').inner_text())
            check('reserva completa en menos de 30 s', time.time() - t0 < 30)
            ev = page.evaluate('window.__eventos || []')
            check('eventos «reserva iniciada» y «reserva completada» en la página', [e['name'] for e in ev] == ['reserva iniciada', 'reserva completada'] and any(e['name'] == 'reserva completada' for e in ev), ev)
            row = srv.sql("SELECT channel, channel_origin, status, price FROM bookings WHERE service_id=? ORDER BY id DESC LIMIT 1", (req_sid,))[0]
            check('reserva guardada con canal y web de origen', (row['channel'], row['channel_origin'], row['status'], row['price']) == ('widget', f'localhost:{port}', 'requested', 75.0), dict(row))
            shot(page, 'widget-solicitud-enviada')
            # «Pago al reservar» from the calendar: the payment opens in a new window
            cal.locator('.wr-day.on').first.click(); cal.locator('[data-pick]').first.click()
            cal.locator('[data-pax="1"]').click()
            cal.locator('input[name=fullname]').fill('Marc Pago'); cal.locator('input[name=email]').fill('marc.pago@example.org'); cal.locator('input[name=accept_policy]').check()
            with page.expect_popup() as pop:
                cal.locator('[data-go]').click()
            popup = pop.value
            cal.locator('.wr-done h2').wait_for(timeout=10000)
            check('pago en ventana nueva mientras el widget espera', 'Esperando el pago' in cal.locator('.wr-done').inner_text())
            b = srv.sql("SELECT id, public_token, status, slot_reserved FROM bookings WHERE slot_id=? ORDER BY id DESC LIMIT 1", (pay_slot,))[0]
            check('plazas retenidas mientras se paga', b['status'] == 'payment_in_progress' and b['slot_reserved'] == 1, dict(b))
            stripe.pay(stripe.last_session()['id'])
            popup.wait_for_url('https://checkout.stripe.test/**', timeout=15000)   # the payment page is open, as a person would see it
            popup.goto(f"{srv.base}/w/pago/{b['id']}.{b['public_token']}?r=ok"); popup.wait_for_load_state('networkidle')
            check('vuelta del pago: «Pago recibido»', 'Pago recibido' in popup.inner_text('body') or popup.is_closed())
            cal.locator('.wr-done .wr-ico').wait_for(timeout=15000)
            check('el widget ve la reserva confirmada', 'Reserva confirmada' in cal.locator('.wr-done').inner_text(), cal.locator('.wr-done').inner_text())
            check('cobro en la cuenta del centro', srv.sql('SELECT connected_account_id FROM payment_orders WHERE booking_id=?', (b['id'],))[0]['connected_account_id'] == 'acct_bahia')
            # The button: booking over the page, closed with Esc
            page.click('#boton-reservar'); page.wait_for_selector('div[role=dialog] iframe', timeout=8000)
            ov = page.frame_locator('div[role=dialog] iframe'); ov.locator('.wr-card').first.wait_for(timeout=10000)
            check('botón · la reserva se abre encima de la página', ov.locator('.wr-close').count() == 1)
            shot(page, 'widget-boton-ventana', False)
            page.keyboard.press('Escape'); page.wait_for_timeout(300)
            check('botón · se cierra con Esc', page.locator('div[role=dialog]').count() == 0)
            check('sin errores de JavaScript en la web del centro', not errors, errors)
            ctx.close()

            # Not authorised: the same page on another origin (127.0.0.1 instead of localhost)
            ctx = browser.new_context(); page = ctx.new_page()
            page.goto(f'http://127.0.0.1:{port}/index.html'); page.wait_for_timeout(2500)
            fr = [f for f in page.frames if f != page.main_frame]
            loaded = []
            for f in fr:
                try: loaded.append(bool(f.query_selector('#wr-app')))
                except Exception: loaded.append(False)
            check('dominio no autorizado: el widget no se carga', fr and not any(loaded), loaded)
            ctx.close()

            # Mobile
            ctx = browser.new_context(viewport={'width': 390, 'height': 844}, device_scale_factor=2, is_mobile=True, has_touch=True, locale='es-ES')
            page = ctx.new_page(); page.goto(f'{host}/index.html'); page.wait_for_load_state('networkidle')
            page.frame_locator('#lista iframe').locator('.wr-card').first.wait_for(timeout=10000)
            over = page.evaluate('document.scrollingElement.scrollWidth - window.innerWidth')
            check('móvil · sin desplazamiento lateral', over <= 0, over)
            w = page.evaluate("document.querySelector('#lista iframe').getBoundingClientRect().width")
            check('móvil · el widget cabe en la pantalla', w <= 390, w)
            # Chromium paints an iframe only once it has been on screen: scroll through the page before the full capture
            page.locator('#lista').scroll_into_view_if_needed(); page.wait_for_timeout(600)
            shot(page, 'widget-lista-movil', False)
            # The full page: a viewport as tall as the page, so every iframe is on screen when it is captured
            page.evaluate('window.scrollTo(0, 0)'); full_h = page.evaluate('document.scrollingElement.scrollHeight')
            page.set_viewport_size({'width': 390, 'height': full_h}); page.wait_for_timeout(800)
            shot(page, 'widget-web-ejemplo-movil', False)
            page.set_viewport_size({'width': 390, 'height': 844}); page.wait_for_timeout(300)
            page.click('#boton-reservar'); page.wait_for_selector('div[role=dialog] iframe', timeout=8000)
            page.frame_locator('div[role=dialog] iframe').locator('.wr-card').first.wait_for(timeout=10000)
            shot(page, 'widget-boton-movil', False)
            ctx.close()

            # 9 languages, widget and page
            ctx = browser.new_context(); page = ctx.new_page()
            bad_w, bad_p = [], []
            for lang in wtx.LANGS:
                page.goto(f'{host}/idioma-{lang}.html'); fl = page.frame_locator('#lista iframe')
                fl.locator('h2').first.wait_for(timeout=10000)
                if fl.locator('h2').first.inner_text().strip() != wtx.texts(lang)['choose_activity'] or wtx.texts(lang)['powered'] not in fl.locator('.wr-foot').inner_text(): bad_w.append(lang)
                page.goto(f'{srv.base}/c/{slug}?lang={lang}'); page.wait_for_selector('h2', timeout=10000)
                if page.inner_text('h2').strip() != wtx.texts(lang)['choose_activity']: bad_p.append(lang)
                if lang == 'zh': shot(page, 'pagina-centro-zh')
            check('9 idiomas en el widget', not bad_w, bad_w)
            check('9 idiomas en la página del centro', not bad_p, bad_p)
            page.goto(f'{srv.base}/c/{slug}'); page.wait_for_selector('.wr-card')
            check('página del centro /c/<centro>: no se puede incrustar', True)
            shot(page, 'pagina-centro')
            page.goto(f'{srv.base}/c/{slug}?servicio={req_sid}'); page.wait_for_selector('.wr-cal')
            check('enlace directo a un servicio', 'Bautizo' in page.inner_text('h2'))
            page.goto(f'{srv.base}/c/{slug}?servicio={req_sid}&fecha={d1}'); page.wait_for_selector('.wr-slot')
            check('enlace directo a una fecha', page.locator('.wr-slot').count() == 1)
            ctx.close()

            # Time zones: a departure is shown at the local time of its place (10:00 at the centre), whoever looks and from where
            seen = {}
            for tzid in ('America/Los_Angeles', 'Asia/Tokyo', 'Europe/Madrid'):
                ctx = browser.new_context(timezone_id=tzid, locale='es-ES'); page = ctx.new_page()
                page.goto(f'{srv.base}/c/{slug}?servicio={req_sid}&fecha={d1}'); page.wait_for_selector('.wr-slot')
                seen[tzid] = page.inner_text('body')
                ctx.close()
            first = next(iter(seen.values()))
            check('zonas horarias: la misma fecha y hora local desde Los Ángeles, Tokio y Madrid', len(set(seen.values())) == 1 and '10:00' in first, {k: v[:120] for k, v in seen.items()})

            # Performance: the widget on 4G (simulated)
            ctx = browser.new_context(); page = ctx.new_page(); cdp = ctx.new_cdp_session(page)
            cdp.send('Network.enable'); cdp.send('Network.emulateNetworkConditions', FAST_4G)
            t0 = time.time(); page.goto(f'{host}/index.html')
            page.frame_locator('#lista iframe').locator('.wr-card').first.wait_for(timeout=15000)
            secs = time.time() - t0
            check('widget cargado en menos de 2 s con 4G', secs < 2.0, f'{secs:.2f} s')
            check('(medida) carga del widget con 4G', True, f'{secs:.2f} s')
            ctx.close()
            browser.close()
    finally:
        if site: site.shutdown()
        srv.stop(); stripe.stop()
    return checks


if __name__ == '__main__':
    shots = Path(sys.argv[sys.argv.index('--shots') + 1]) if '--shots' in sys.argv else None
    results = run(shots)   # (each check is printed as it happens)
    bad = [r for r in results if not r[1]]
    print(f'{len(results) - len(bad)}/{len(results)} comprobaciones correctas')
    sys.exit(1 if bad else 0)
