"""v50.58 · Reserva exprés desde la web del centro (encargo del 16/10/2026, bloque 2) en un navegador real.

Con Chromium, la web de ejemplo del centro servida desde otro origen y el simulador de Stripe (Stripe.js se sustituye
por tests/navegador/stripe_js_stub.js, que imita el formulario de Stripe dentro de la reserva):
  1. el botón abre una hoja desde abajo en el móvil y una ventana centrada de ~480 px en el ordenador;
  2. franja del centro (logo, nombre, valoración) y el color del centro en los botones (dos colores);
  3. «¿Qué y cuándo?»: la tira de 14 días con punto verde, la fecha más cercana y su única hora ya elegidas, personas;
  4. barra fija con total, desglose y «Continuar» / «Pagar 100 €» / «Enviar solicitud», y la línea de confianza;
  5. sin scroll en las dos pantallas a 390×844;
  6. «Tus datos»: errores junto a cada campo, una sola casilla, titulación solo si el servicio la pide;
  7. pago dentro de la reserva con las plazas apartadas y su contador; la reserva confirmada solo cuando Stripe lo dice;
  8. «¡Reservado!» con QR, calendario (.ics), cómo llegar, WhatsApp y los acompañantes (que llegan a la lista del barco);
  9. cerrar: sin nada elegido se cierra; con algo elegido pregunta; «Salir» cierra;
 10. horas alternativas cuando no quedan plazas a esa hora;
 11. «Recordar mis datos en este dispositivo» y borrarlos;
 12. un enlace con todo elegido abre directamente en «Tus datos»;
 13. «Probar como cliente» (modo de prueba) no guarda nada;
 14. los 9 idiomas sin textos sin traducir;
 15. sin errores de JavaScript; carga del widget con 4G simulada en menos de 2 s.
Uso: python tests/navegador/e2e_v50_58_reserva_expres.py [--shots DIR]
"""
from __future__ import annotations

import re
import sys
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
import cronometro_reserva as cr  # noqa: E402  (the same centre, website and Stripe simulator)
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'app'))
from wod import widget_textos as wtx  # noqa: E402

FAST_4G = {'offline': False, 'latency': 150, 'downloadThroughput': 9 * 1024 * 1024 / 8, 'uploadThroughput': 9 * 1024 * 1024 / 8}


def run(shots: Path | None):
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))
        print(('OK   ' if ok else 'FALLA') + ' ' + name + (f' · {detail}' if detail else ''), flush=True)

    def shot(page, name):
        if shots:
            shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'))

    env = cr.setup('#0b7a75', pk=True)
    srv, stripe, host, slug = env['srv'], env['stripe'], env['host'], env['slug']
    srv.sql("UPDATE provider_services SET level_required='Open Water', meeting_point='Puerto deportivo, pantalán 3' WHERE id=?", (env['pay'],))
    cid = srv.sql('SELECT center_id FROM provider_services WHERE id=?', (env['pay'],))[0]['center_id']
    srv.sql("INSERT INTO center_reviews(center_id,user_id,rating,title,body,active,verified,created_at,updated_at) VALUES(?,1,5,'t','b',1,1,'2026-01-01','2026-01-01')", (cid,))
    try:
        with sync_playwright() as p:
            browser = chromium(p)

            def context(opts, **kw):
                ctx = browser.new_context(**{**opts, **kw})
                ctx.route('https://js.stripe.com/**', lambda r: r.fulfill(status=200, content_type='application/javascript', body=cr.STUB))
                cr.reset_limits(srv)
                return ctx

            def sheet(page):
                return page.frame_locator('div[role=dialog] iframe')

            def sheet_frame(page):
                return next(x for x in page.frames if 'f=boton' in x.url)

            # ---- 1-8 · mobile, payment service, from the general button
            ctx = context(cr.PHONE); page = ctx.new_page(); errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            page.goto(host + '/index.html'); page.wait_for_load_state('networkidle')
            page.click('#boton-reservar'); f = sheet(page)
            f.locator('.wr-svc').first.wait_for(timeout=10000); page.wait_for_timeout(400)
            box = page.evaluate("(() => { const b = document.querySelector('div[role=dialog] iframe').parentNode.getBoundingClientRect(); return [b.left, b.width, Math.round(b.bottom), innerHeight]; })()")
            check('1 · móvil: hoja desde abajo a todo el ancho', box[0] == 0 and box[1] == 390 and abs(box[2] - box[3]) <= 1, box)
            band = f.locator('.wr-band').inner_text()
            check('2 · franja del centro con nombre y valoración', 'Bahía Coralina' in band and '★' in band, band)
            f.locator('.wr-svc', has_text='Doble').click()
            f.locator('.wr-time[aria-checked="true"]').wait_for(timeout=10000)
            n_days = f.locator('.wr-dchip:not(.more)').count(); dots = f.locator('.wr-dchip:not(.none):not(.more)').count()
            check('3 · tira de 14 días con «Más fechas» y punto verde en los días con plazas', n_days == 14 and dots >= 3 and f.locator('.wr-dchip.more').count() == 1, (n_days, dots))
            check('3 · la fecha más cercana y su única hora ya elegidas', f.locator('.wr-dchip[aria-selected="true"]').count() == 1 and 'Quedan' in f.locator('.wr-time[aria-checked="true"]').inner_text())
            f.locator('[data-pax="1"]').click(); page.wait_for_timeout(700)
            bar = f.locator('[data-bar]').inner_text()
            check('4 · barra con total, desglose y «Continuar»', '100' in bar and 'Continuar' in bar and '2 personas' in bar, bar)
            check('4 · línea de confianza: pago seguro, cancelación y confirmación al momento', all(x in bar for x in ('Pago seguro', 'Cancelación gratis', 'Confirmación al momento')), bar)
            primary_bg = f.locator('[data-primary]').evaluate('e => getComputedStyle(e).backgroundColor')
            check('2 · el color del centro en el botón', primary_bg == 'rgb(11, 122, 117)', primary_bg)
            fr = sheet_frame(page)
            scroll1 = fr.evaluate("() => { const s = document.querySelector('.wr-screen'); return s.scrollHeight - s.clientHeight; }")
            check('5 · «¿Qué y cuándo?» sin scroll a 390×844', scroll1 <= 0, scroll1)
            shot(page, 'movil-1-que-y-cuando')
            f.locator('[data-primary]').click(); f.locator('[data-form]').wait_for(timeout=8000); page.wait_for_timeout(300)
            scroll2 = fr.evaluate("() => { const s = document.querySelector('.wr-screen'); return s.scrollHeight - s.clientHeight; }")
            check('5 · «Tus datos» sin scroll a 390×844', scroll2 <= 0, scroll2)
            check('6 · titulación (el servicio la pide) y una sola casilla de condiciones', f.locator('[data-level]').count() == 4 and f.locator('input[name=accept_policy]').count() == 1)
            check('6 · campos de 16 px o más', fr.evaluate("() => [...document.querySelectorAll('input[type=text],input[type=email],input[type=tel],select')].every(e => parseFloat(getComputedStyle(e).fontSize) >= 16)"))
            check('6 · autocompletar en nombre, correo y teléfono', fr.evaluate("() => ['fullname','email','phone'].map(n => document.querySelector('[name='+n+']').autocomplete).join(',')") == 'name,email,tel-national')
            check('6 · prefijo del teléfono según el idioma', f.locator('select[name=prefix]').input_value() == '+34')
            f.locator('[data-primary]').click(); page.wait_for_timeout(300)
            errs = [x.strip() for x in f.locator('.wr-ferr:not([hidden])').all_inner_texts()]
            check('6 · errores junto a cada campo', len(errs) == 4 and f.locator('.wr-field.bad').count() == 4, errs)
            shot(page, 'movil-2-errores')
            f.locator('input[name=fullname]').fill('Lucía Martín'); f.locator('input[name=email]').fill('lucia.e2e@example.org'); f.locator('input[name=phone]').fill('611 222 333')
            f.locator('[data-level="ow"]').click(); f.locator('input[name=accept_policy]').check()
            check('6 · el error se quita al corregir', f.locator('.wr-field.bad').count() == 0)
            check('4 · «Pagar 100 €»', f.locator('[data-primary]').inner_text().replace('\xa0', ' ').strip() == 'Pagar 100 €', f.locator('[data-primary]').inner_text())
            shot(page, 'movil-3-tus-datos')
            f.locator('[data-primary]').click()
            f.locator('[data-stripe-stub]').wait_for(timeout=10000)
            hold = f.locator('[data-hold]').inner_text()
            check('7 · plazas apartadas con su contador', re.search(r'(9|10):\d\d', hold) is not None, hold)
            b = srv.sql("SELECT id,status,slot_reserved,public_token FROM bookings ORDER BY id DESC LIMIT 1")[0]
            check('7 · reserva en pago con las plazas apartadas', b['status'] == 'payment_in_progress' and b['slot_reserved'] == 1, dict(b))
            stub = fr.evaluate('() => window.__stripeStub')
            check('7 · Stripe dentro de la reserva, en la cuenta del centro', stub['account'] == 'acct_bahia' and stub['secret'].endswith('_secret_mock'), stub['account'])
            shot(page, 'movil-4-pago')
            fr.evaluate('() => window.__stripeStub.complete()')   # the browser says «paid» before Stripe does
            page.wait_for_timeout(2500)
            check('7 · sin el pago en Stripe la reserva no se confirma', srv.sql('SELECT status FROM bookings WHERE id=?', (b['id'],))[0]['status'] == 'payment_in_progress')
            stripe.pay(stripe.session_by_secret(stub['secret'])['id'])
            f.locator('.wr-done h2', has_text='Reservado').wait_for(timeout=20000)
            check('7 · confirmada cuando Stripe lo dice', srv.sql('SELECT status FROM bookings WHERE id=?', (b['id'],))[0]['status'] == 'confirmed')
            done = f.locator('.wr-done').inner_text()
            check('8 · «¡Reservado!» con referencia y punto de encuentro', 'WOD-' in done and 'pantalán 3' in done, done[:200])
            check('8 · QR de la reserva', f.locator('.wr-qr img').count() == 1 and fr.evaluate("() => document.querySelector('.wr-qr img').naturalWidth > 0"))
            ics = f.locator('[data-ics]').get_attribute('href')
            r = page.request.get(ics)
            check('8 · «Añadir al calendario» (.ics)', r.status == 200 and 'BEGIN:VEVENT' in r.text(), r.status)
            hrefs = f.locator('.wr-act').evaluate_all('els => els.map(e => e.getAttribute("href"))')
            check('8 · «Cómo llegar» y WhatsApp del centro', any('google.com/maps' in h for h in hrefs) and any(h.startswith('https://wa.me/') for h in hrefs), hrefs)
            shot(page, 'movil-5-reservado')
            f.locator('[data-people]').click(); f.locator('[data-people-form]').wait_for()
            f.locator('[data-seat="2"] [name=name]').fill('Ana Ruiz'); f.locator('[data-seat="2"] [name=level]').select_option('aow'); f.locator('[data-seat="2"] [name=size]').select_option('M')
            f.locator('[data-people-form] button[type=submit]').click(); f.locator('.wr-msg.ok').wait_for(timeout=8000)
            name2 = srv.sql('SELECT name FROM manifest_entries WHERE booking_id=? AND seat=2', (b['id'],))
            check('8 · acompañantes guardados y en la lista del barco', name2 and name2[0]['name'] == 'Ana Ruiz', name2 and dict(name2[0]))
            shot(page, 'movil-6-acompanantes')
            ev = page.evaluate('window.__eventos || []')
            check('eventos «reserva iniciada» y «reserva completada» en la web del centro', [e['name'] for e in ev] == ['reserva iniciada', 'reserva completada'], [e['name'] for e in ev])
            # ---- 9 · closing
            fr.evaluate("() => document.querySelector('[data-back], .wr-x') && 0")
            page.keyboard.press('Escape'); page.wait_for_timeout(400)
            check('9 · ya reservado: se cierra sin preguntar', page.locator('div[role=dialog]').count() == 0)
            page.click('#boton-reservar'); f = sheet(page); f.locator('.wr-svc').first.wait_for(timeout=10000); page.wait_for_timeout(300)
            page.mouse.click(195, 30); page.wait_for_timeout(400)
            check('9 · sin nada elegido: tocar fuera cierra', page.locator('div[role=dialog]').count() == 0)
            page.click('#boton-reservar'); f = sheet(page); f.locator('.wr-svc').first.wait_for(timeout=10000)
            f.locator('.wr-svc', has_text='Bautizo').click(); f.locator('.wr-time').first.wait_for(timeout=10000); page.wait_for_timeout(300)
            page.mouse.click(195, 30); page.wait_for_timeout(500)
            check('9 · con algo elegido: pregunta antes de cerrar', page.locator('div[role=dialog]').count() == 1 and f.locator('.wr-ask').count() == 1)
            shot(page, 'movil-7-salir')
            f.locator('[data-stay]').click(); page.wait_for_timeout(200)
            check('9 · «Seguir reservando» mantiene la reserva', f.locator('.wr-ask').count() == 0 and page.locator('div[role=dialog]').count() == 1)
            f.locator('.wr-x').click(); page.wait_for_timeout(300); f.locator('[data-go-out]').click(); page.wait_for_timeout(500)
            check('9 · «Salir» cierra', page.locator('div[role=dialog]').count() == 0)
            check('15 · sin errores de JavaScript (móvil)', not errors, errors)
            ctx.close()

            # ---- 10 · alternatives: 9 people at a time with fewer spots
            ctx = context(cr.DESK); page = ctx.new_page(); errors = []
            page.on('pageerror', lambda e: errors.append(str(e)))
            day1 = time.strftime('%Y-%m-%d', time.localtime(time.time() + 2 * 86400))
            small = env['center'].post('/api/provider-services/slot', {'service_id': env['req'], 'slot_date': day1, 'slot_time': '16:00', 'spots_total': 2}).json['slot_id']
            page.goto(f"{srv.base}/c/{slug}?servicio={env['req']}&fecha={day1}"); f = page
            f.locator('.wr-time').first.wait_for(timeout=10000)
            for _ in range(2): f.locator('[data-pax="1"]').click(); page.wait_for_timeout(250)
            f.locator(f'[data-slot="{small}"]').click()
            f.locator('[data-alt-pick]').first.wait_for(timeout=8000)
            alt = f.locator('[data-alt]').inner_text()
            check('10 · sin plazas a esa hora: las horas o días más cercanos', f.locator('[data-alt-pick]').count() >= 1 and 'para 3' in alt, alt)
            f.locator('[data-alt-pick]').first.click(); page.wait_for_timeout(400)
            check('10 · elegir una alternativa la deja elegida', f.locator('.wr-time[aria-checked="true"]').count() == 1)
            box = page.evaluate("document.querySelector('.wr-shell').getBoundingClientRect().width")
            shot(page, 'ordenador-alternativas')
            check('15 · sin errores de JavaScript (ordenador)', not errors, errors)
            ctx.close()

            # ---- 1 · the window on the computer; 11 · remember my details; 12 · a link with everything chosen
            ctx = context(cr.DESK); page = ctx.new_page()
            page.goto(host + '/index.html'); page.wait_for_load_state('networkidle')
            page.click('#boton-servicio'); f = sheet(page); f.locator('.wr-time[aria-checked="true"]').wait_for(timeout=10000); page.wait_for_timeout(500)
            w = page.evaluate("document.querySelector('div[role=dialog] iframe').parentNode.getBoundingClientRect().width")
            check('1 · ordenador: ventana centrada de ~480 px', 470 <= w <= 490, w)
            check('12 · botón de un servicio: abre ya en ese servicio', 'Doble inmersión' in f.locator('.wr-svc-one').inner_text())
            shot(page, 'ordenador-1-ventana')
            f.locator('[data-primary]').click(); f.locator('[data-form]').wait_for()
            f.locator('input[name=fullname]').fill('Marc Recuerda'); f.locator('input[name=email]').fill('marc.recuerda@example.org')
            f.locator('[data-level="aow"]').click(); f.locator('input[name=accept_policy]').check(); f.locator('input[name=remember]').check()
            f.locator('[data-primary]').click(); f.locator('[data-stripe-stub]').wait_for(timeout=10000)
            fr = sheet_frame(page); stub = fr.evaluate('() => window.__stripeStub')
            stripe.pay(stripe.session_by_secret(stub['secret'])['id']); fr.evaluate('() => window.__stripeStub.complete()')
            f.locator('.wr-done h2', has_text='Reservado').wait_for(timeout=20000)
            page.keyboard.press('Escape'); page.wait_for_timeout(400)
            page.click('#boton-servicio'); f = sheet(page); f.locator('.wr-time[aria-checked="true"]').wait_for(timeout=10000)
            f.locator('[data-primary]').click(); f.locator('[data-form]').wait_for()
            check('11 · «Recordar mis datos»: nombre y correo ya escritos la próxima vez', f.locator('input[name=fullname]').input_value() == 'Marc Recuerda' and f.locator('input[name=email]').input_value() == 'marc.recuerda@example.org')
            f.locator('[data-forget]').click()
            stored = sheet_frame(page).evaluate("() => localStorage.getItem('wd-reserva-datos-v1')")
            check('11 · «Borrar mis datos de este dispositivo»', stored is None and f.locator('input[name=fullname]').input_value() == '', stored)
            ctx.close()
            ctx = context(cr.PHONE); page = ctx.new_page()
            day2 = time.strftime('%Y-%m-%d', time.localtime(time.time() + 3 * 86400))
            page.goto(f"{srv.base}/c/{slug}?servicio={env['pay']}&fecha={day2}&hora=09:00&personas=2")
            page.locator('[data-form]').wait_for(timeout=10000)
            summary = page.locator('.wr-sum1').inner_text()
            check('12 · enlace con todo elegido: abre directamente en «Tus datos»', 'Doble inmersión' in summary and '09:00' in summary and '2 personas' in summary, summary)
            shot(page, 'movil-enlace-directo')
            ctx.close()

            # ---- 13 · «Probar como cliente»: nothing is saved
            ctx = context(cr.PHONE); page = ctx.new_page()
            before = srv.sql('SELECT COUNT(*) AS n FROM bookings')[0]['n']
            page.goto(f"{srv.base}/c/{slug}?servicio={env['req']}&prueba=1")
            page.locator('.wr-test').wait_for(timeout=10000)
            page.locator('.wr-time').first.wait_for(timeout=10000)
            if not page.locator('.wr-time[aria-checked="true"]').count(): page.locator('.wr-time').first.click()   # that day has two times
            page.locator('[data-primary]').click(); page.locator('[data-form]').wait_for()
            page.locator('input[name=fullname]').fill('Cliente Prueba'); page.locator('input[name=email]').fill('prueba@example.org'); page.locator('input[name=accept_policy]').check()
            page.locator('[data-primary]').click(); page.locator('.wr-done').wait_for(timeout=8000)
            check('13 · modo de prueba: se ve el final y no se guarda nada', srv.sql('SELECT COUNT(*) AS n FROM bookings')[0]['n'] == before and 'prueba' in page.locator('.wr-done').inner_text().lower())
            ctx.close()

            # ---- 2 · the second colour (a light one: readable text on the buttons)
            env['center'].post('/api/provider/vender', {'color': '#f2c94c'})
            ctx = context(cr.PHONE); page = ctx.new_page()
            page.goto(f"{srv.base}/c/{slug}?servicio={env['pay']}"); page.locator('.wr-time[aria-checked="true"]').wait_for(timeout=10000)
            col = page.locator('[data-primary]').evaluate('e => [getComputedStyle(e).backgroundColor, getComputedStyle(e).color]')
            check('2 · color claro del centro con texto oscuro legible', col == ['rgb(242, 201, 76)', 'rgb(1, 28, 60)'], col)
            shot(page, 'movil-color-claro')
            ctx.close()
            env['center'].post('/api/provider/vender', {'color': '#0b7a75'})

            # ---- 14 · 9 languages: no Spanish left on the two screens
            ctx = context(cr.DESK); page = ctx.new_page(); bad = {}
            for lang in wtx.LANGS:
                tx = wtx.texts(lang)
                page.goto(f"{srv.base}/c/{slug}?servicio={env['pay']}&lang={lang}"); page.locator('.wr-time[aria-checked="true"]').wait_for(timeout=10000)
                s1 = page.locator('.wr-shell').inner_text()
                page.locator('[data-primary]').click(); page.locator('[data-form]').wait_for()
                s2 = page.locator('.wr-shell').inner_text()
                want = [tx['rx_when'], tx['rx_continue'], tx['powered']]
                miss = [x for x in want if x not in s1] + [x for x in (tx['rx_accept'], tx['rx_remember'], tx['your_details'] if False else tx['name']) if x not in s2]
                if lang != 'es':
                    same = set(tx.values())   # a word that is the same in both languages (Portuguese «Continuar») is not a leak
                    leaked = [x for x in ('¿Cuándo?', 'Continuar', 'Acepto las condiciones', 'Recordar mis datos', 'Nombre y apellidos', 'Pago seguro')
                              if x in s1 + s2 and not any(x in v for v in same)]
                    if leaked: miss += leaked
                if miss: bad[lang] = miss
                if lang in ('zh', 'de'): shot(page, f'idioma-{lang}')
            check('14 · los 9 idiomas, sin textos en español en otro idioma', not bad, bad)
            ctx.close()

            # ---- 15 · load with 4G (simulated): the sheet shows the centre's services in less than 2 s
            ctx = context(cr.PHONE); page = ctx.new_page(); cdp = ctx.new_cdp_session(page)
            page.goto(host + '/index.html'); page.wait_for_load_state('networkidle')
            cdp.send('Network.enable'); cdp.send('Network.emulateNetworkConditions', FAST_4G)
            t0 = time.time(); page.click('#boton-reservar'); sheet(page).locator('.wr-svc').first.wait_for(timeout=15000)
            secs = time.time() - t0
            check('15 · la reserva abierta en menos de 2 s con 4G', secs < 2.0, f'{secs:.2f} s')
            ctx.close()
            browser.close()
    finally:
        env['site'].shutdown(); srv.stop(); stripe.stop()
    return checks


if __name__ == '__main__':
    shots = Path(sys.argv[sys.argv.index('--shots') + 1]) if '--shots' in sys.argv else None
    results = run(shots)
    bad = [r for r in results if not r[1]]
    print(f'{len(results) - len(bad)}/{len(results)} comprobaciones correctas')
    sys.exit(1 if bad else 0)
