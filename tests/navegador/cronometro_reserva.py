#!/usr/bin/env python3
"""v50.58 · Bloque 2 (reserva exprés): cronómetro de la reserva desde la web de un centro, a ritmo humano.

Desde el toque en «Reservar» de la web del centro (scripts/demo/web-de-centro-ejemplo.html, servida desde otro origen)
hasta que la persona ve la reserva confirmada (o la solicitud enviada), para una reserva normal: un servicio, la fecha
más cercana con plazas y 2 personas. Mide:

  - segundos de reloj, con las respuestas reales del servidor y las esperas de una persona;
  - toques: cada botón, casilla o campo que se toca (escribir en un campo cuenta como el toque de entrar en él);
  - pantallas hasta la confirmación: cada vez que la reserva cambia de paso (la página o el formulario de pago de Stripe
    cuenta como una); la confirmación final no se cuenta;
  - scroll: los píxeles que hay que desplazar para llegar al botón principal de cada pantalla.

Ritmo humano (el mismo antes y después): 1,5 s de lectura al aparecer cada pantalla, 0,5 s entre toques, 0,3 s por letra
en el móvil (unas 40 palabras por minuto, la media escribiendo en el móvil según Palin et al., MobileHCI 2019) y 0,2 s
en el ordenador (unas 52 palabras por minuto, Dhakal et al., CHI 2018), y 0,6 s por cada pantalla de scroll.

Datos de quien reserva: «a mano» (letra a letra) o «con autocompletar» (tocar el nombre y la sugerencia del navegador,
que rellena nombre, correo y teléfono: 2 toques y medio segundo para mirarla). Los dos formularios, antes y después,
tienen los campos marcados para el autocompletar del navegador.

El pago no se puede hacer aquí de verdad (Stripe solo existe en internet): su parte se espera con el mismo ritmo,
contando lo que pide Stripe (tarjeta, caducidad, CVC, nombre en la tarjeta y «Pagar»; el correo ya va escrito porque
WORLDIVES se lo pasa), y la de Apple Pay o Google Pay como un toque y 2 s para la confirmación en el teléfono. Después
el simulador de Stripe da el pago por hecho y se espera a que la reserva lo diga. Va marcado como «modelo».

    python3 tests/navegador/cronometro_reserva.py antes [carpeta]
    python3 tests/navegador/cronometro_reserva.py despues [carpeta]

Escribe el resultado en <carpeta>/cronometro.json y las capturas de cada pantalla. «antes» recorre la reserva de
v50.56/57: la copia guardada en tests/navegador/reserva_v50_57/ se sirve en lugar de los archivos de ahora. «despues»
recorre la reserva exprés, con el formulario de Stripe dentro (Stripe.js se sustituye por tests/navegador/stripe_js_stub.js).

Cada recorrido empieza con los límites del widget a cero (las reservas seguidas desde el mismo ordenador harían saltar la
comprobación «no soy un robot», que una persona real no ve) y es otra persona (otro correo).
"""
from __future__ import annotations

import functools
import http.server
import json
import socket
import sqlite3
import sys
import tempfile
import threading
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
from helpers import ServerTestCase, Server  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
TEMPLATE = ROOT / 'scripts' / 'demo' / 'web-de-centro-ejemplo.html'
READ, TAP, FLICK, WALLET, GLANCE = 1.5, 0.5, 0.6, 2.0, 0.5
CHAR = {'movil': 0.3, 'ordenador': 0.2}   # seconds per letter
PHONE = {'viewport': {'width': 390, 'height': 844}, 'device_scale_factor': 2, 'is_mobile': True, 'has_touch': True, 'locale': 'es-ES'}
DESK = {'viewport': {'width': 1366, 'height': 900}, 'locale': 'es-ES'}
PERSON = {'name': 'Lucía Martín', 'email': 'lucia.mart00@example.org', 'phone': '611 222 333'}
# Each walk is another person (same length of e-mail): a person may only have 3 payments open at the same time.
person = lambda n: {**PERSON, 'email': f'lucia.mart{n:02d}@example.org'}
# What Stripe asks (Checkout, hosted or embedded): card number, expiry, CVC, name on the card and «Pagar». The e-mail
# is already written: WORLDIVES sends it as customer_email.
STRIPE_CARD = {'taps': 5, 'chars': 16 + 4 + 3 + len(PERSON['name'])}
OLD = Path(__file__).resolve().parent / 'reserva_v50_57'   # the booking of v50.56/57, served instead of today's files
STUB = (Path(__file__).resolve().parent / 'stripe_js_stub.js').read_text(encoding='utf-8')
# The walks: kind of service, how the details are given, how it is paid, and which button of the centre's website
WALKS = {
    'peticion': ('peticion', 'mano', None, '#boton-reservar'),
    'tarjeta': ('pago', 'mano', 'tarjeta', '#boton-reservar'),
    'monedero': ('pago', 'mano', 'monedero', '#boton-reservar'),
    'peticion-autocompletar': ('peticion', 'auto', None, '#boton-reservar'),
    'monedero-autocompletar': ('pago', 'auto', 'monedero', '#boton-reservar'),
    'monedero-autocompletar-boton-servicio': ('pago', 'auto', 'monedero', '#boton-servicio'),
}


def free_port():
    with socket.socket() as s:
        s.bind(('127.0.0.1', 0)); return s.getsockname()[1]


def host_site(folder: Path, port: int):
    handler = functools.partial(http.server.SimpleHTTPRequestHandler, directory=str(folder))
    handler.log_message = lambda *a, **k: None
    httpd = http.server.ThreadingHTTPServer(('127.0.0.1', port), handler)
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return httpd


class Human:
    """A person going through the booking: counts taps, screens and scroll, and waits as a person would."""

    def __init__(self, page, frame, shots: Path | None, prefix: str):
        self.page, self.f, self.shots, self.prefix = page, frame, shots, prefix
        self.char = CHAR['movil' if prefix.startswith('movil') else 'ordenador']
        self.taps = 0; self.screens = 0; self.scroll = 0; self.t0 = time.time(); self.modelled = 0.0; self.notes = []; self.names = []

    def wait(self, s): self.page.wait_for_timeout(int(s * 1000))

    def shot(self, name):
        if self.shots:
            self.shots.mkdir(parents=True, exist_ok=True)
            self.page.screenshot(path=str(self.shots / f'{self.prefix}-{len(self.names) + 1}-{name}.png'))
        self.names.append(name)

    def screen(self, ready: str, name: str, button: str | None = None, final=False):
        """A new screen: wait for it, read it, measure how far its main button is, and take its picture."""
        self.f.locator(ready).first.wait_for(timeout=20000)
        if final: self.done_at = time.time()
        else: self.screens += 1
        if not final: self.wait(READ)
        if button:
            over = self.f.locator(button).first.evaluate('(b) => { const r = b.getBoundingClientRect(); return Math.max(0, Math.ceil(r.bottom - window.innerHeight)); }')
            if over > 0:
                self.scroll += over; self.wait(FLICK * max(1, round(over / 700)))
        self.shot(name)

    def tap(self, sel, nth=0):
        self.wait(TAP); loc = self.f.locator(sel).nth(nth); loc.scroll_into_view_if_needed(); loc.click(); self.taps += 1

    def type(self, sel, text):
        self.wait(TAP); loc = self.f.locator(sel).first; loc.scroll_into_view_if_needed(); loc.click(); self.taps += 1
        loc.press_sequentially(text, delay=int(self.char * 1000))

    def autofill(self, fields):
        """The browser's suggestion: tap the first field, look at the suggestion, tap it; it fills every field."""
        self.wait(TAP); first = self.f.locator(fields[0][0]).first; first.scroll_into_view_if_needed(); first.click(); self.taps += 1
        self.wait(GLANCE + TAP); self.taps += 1
        for sel, val in fields: self.f.locator(sel).first.fill(val)

    def model(self, taps, chars=0, extra=0.0, note='', screen=True):
        """A part that can not run here (Stripe): waited with the same pace, and counted."""
        s = (READ if screen else 0) + taps * TAP + chars * self.char + extra
        self.wait(s); self.taps += taps; self.modelled += s
        if screen: self.screens += 1
        self.notes.append(note)

    def result(self):
        end = getattr(self, 'done_at', time.time())
        return {'segundos': round(end - self.t0, 1), 'segundos_modelo': round(self.modelled, 1), 'toques': self.taps, 'pantallas': self.screens,
                'scroll_px': self.scroll, 'pantallas_vistas': self.names, 'notas': self.notes}


def reset_limits(srv):
    """The widget counts booking attempts per address (5 in 10 minutes before the «not a robot» check)."""
    db = sqlite3.connect(str(srv.db.with_name(srv.db.stem + '-limites.sqlite3')))
    try: db.execute("DELETE FROM hits WHERE name LIKE 'widget%'"); db.commit()
    except sqlite3.Error: pass
    finally: db.close()


def serve_old(ctx, base):
    """«antes»: the three files of v50.56/57 instead of today's."""
    for path, kind in (('/js/wd-reservar.js', 'application/javascript'), ('/widget.js', 'application/javascript'), ('/css/wd-reservar.css', 'text/css')):
        body = (OLD / path.rsplit('/', 1)[1]).read_text(encoding='utf-8')
        def answer(b, k):
            return lambda route: route.fulfill(status=200, content_type=k + '; charset=utf-8', body=b)
        ctx.route(base + path + '*', answer(body, kind))


def setup(color='#0b7a75', pk=False):
    """pk: the server has STRIPE_PUBLISHABLE_KEY (Stripe's form inside the booking); without it, Stripe's page."""
    stripe = StripeMock()
    env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': stripe.base}
    if pk: env['STRIPE_PUBLISHABLE_KEY'] = 'pk_test_cronometro01'
    srv = ServerTestCase.server = Server(env).start()
    t = ServerTestCase('run')
    admin = t.make_admin(); center = t.make_center(admin, 'bahia'); cid = center.user['center_id']
    srv.sql("UPDATE centers SET name='Bahía Coralina',plan_code='pro',plan_status='active',plan_expires_at='2099-12-31',stripe_account_id='acct_bahia',"
            "stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cid,))
    req = center.post('/api/provider-services', {'title': 'Bautizo de buceo', 'price': 75, 'booking_mode': 'request', 'max_participants': 4, 'duration_minutes': 150}).json['id']
    pay = center.post('/api/provider-services', {'title': 'Doble inmersión en barco', 'price': 50, 'booking_mode': 'payment', 'max_participants': 8, 'duration_minutes': 240}).json['id']
    day = lambda n: time.strftime('%Y-%m-%d', time.localtime(time.time() + n * 86400))
    for n in (2, 3, 5, 9):
        center.post('/api/provider-services/slot', {'service_id': req, 'slot_date': day(n), 'slot_time': '10:00', 'spots_total': 40})
        center.post('/api/provider-services/slot', {'service_id': pay, 'slot_date': day(n), 'slot_time': '09:00', 'spots_total': 40})
    slug = center.get('/api/provider/vender').json['slug']
    port = free_port()
    center.post('/api/provider/vender', {'domains': [f'localhost:{port}'], 'color': color})
    folder = Path(tempfile.mkdtemp(prefix='web-centro-'))
    html = TEMPLATE.read_text(encoding='utf-8').replace('__WORLDIVES__', srv.base).replace('__CENTRO__', slug).replace('__SERVICIO__', str(pay))
    (folder / 'index.html').write_text(html, encoding='utf-8')
    site = host_site(folder, port)
    return {'srv': srv, 'stripe': stripe, 'site': site, 'host': f'http://localhost:{port}', 'slug': slug, 'req': req, 'pay': pay, 'center': center}


def details(h, fields, how):
    if how == 'auto': h.autofill(fields)
    else:
        for sel, val in fields: h.type(sel, val)


def stripe_part(h, pay):
    if pay == 'tarjeta': h.model(STRIPE_CARD['taps'], STRIPE_CARD['chars'], note='Stripe con la tarjeta escrita a mano (modelo)', screen=h.stripe_screen)
    else: h.model(1, 0, WALLET, note='Apple Pay o Google Pay (modelo)', screen=h.stripe_screen)


# ------------------------------------------------------------------------------------------------ the booking of v50.56/57
def antes(page, env, walk, shots, prefix, who=PERSON):
    """«Reservar ahora» → list of services → «Ver fechas» → calendar → time → form (people, details, conditions) → send;
    paying: Stripe's page in a new window, back to the widget, which asks the server until it says «confirmada»."""
    kind, how, pay, button = WALKS[walk]
    if button != '#boton-reservar': return None   # v50.56/57 had no button for one service on the example page
    page.click(button); page.wait_for_selector('div[role=dialog] iframe', timeout=8000)
    h = Human(page, page.frame_locator('div[role=dialog] iframe'), shots, prefix); h.taps = 1; h.stripe_screen = True
    title = 'Bautizo' if kind == 'peticion' else 'Doble inmersión'
    h.screen('.wr-card', 'servicios', '.wr-card >> nth=-1')
    h.tap(f'.wr-card:has-text("{title}") button.wr-btn')
    h.screen('.wr-cal', 'calendario')
    h.tap('.wr-day.on')
    h.screen('[data-pick]', 'horas', '[data-pick]')
    h.tap('[data-pick]')
    h.screen('[data-form]', 'datos', '[data-go]')
    h.tap('[data-pax="1"]')
    details(h, [('input[name=fullname]', who['name']), ('input[name=email]', who['email']), ('input[name=phone]', who['phone'])], how)
    h.tap('input[name=accept_policy]')
    if kind == 'peticion':
        h.tap('[data-go]'); h.screen('.wr-done h2', 'enviada', final=True)
        return h
    with page.expect_popup() as pop:
        h.tap('[data-go]')
    popup = pop.value; popup.wait_for_load_state()
    stripe_part(h, pay)
    sess = env['stripe'].last_session(); env['stripe'].pay(sess['id'])
    bid = int(sess['metadata']['booking_id']); tok = env['srv'].sql('SELECT public_token FROM bookings WHERE id=?', (bid,))[0]['public_token']
    popup.goto(f"{env['srv'].base}/w/pago/{bid}.{tok}?r=ok")   # Stripe sends the person back
    h.screen('.wr-done h2:has-text("confirmada")', 'confirmada', final=True)
    return h


# ------------------------------------------------------------------------------------------------ the express booking (v50.58)
def despues(page, env, walk, shots, prefix, who=PERSON):
    """«Reservar» → «¿Qué y cuándo?» (service, the nearest day and its time already chosen, people) → «Tus datos» (details,
    one box) → «Pagar 100 €» with Stripe's form inside the same booking, or «Enviar solicitud» → «¡Reservado!»."""
    kind, how, pay, button = WALKS[walk]
    page.click(button); page.wait_for_selector('div[role=dialog] iframe', timeout=8000)
    h = Human(page, page.frame_locator('div[role=dialog] iframe'), shots, prefix); h.taps = 1; h.stripe_screen = False
    title = 'Bautizo' if kind == 'peticion' else 'Doble inmersión'
    if button == '#boton-reservar':
        h.screen('.wr-svc', 'que-te-apetece', '.wr-svc >> nth=-1')
        h.tap('.wr-cat:has-text("Bautizos")' if kind == 'peticion' else '.wr-cat:has-text("Inmersiones")')   # 17/10 (1.5): first the category
        h.tap(f'.wr-svc:has-text("{title}")')
        h.f.locator('.wr-time[aria-checked="true"]').wait_for(timeout=15000)
        h.wait(READ)   # the same screen goes on: the person reads the day and the time already chosen
        h.shot('que-y-cuando')
    else:
        h.screen('.wr-time[aria-checked="true"]', 'que-y-cuando', '[data-primary]')
    h.tap('[data-pax="1"]')
    h.f.locator('[data-primary]:not([disabled])').wait_for(timeout=10000)
    h.tap('[data-primary]')
    h.screen('[data-form]', 'tus-datos', '[data-primary]')
    details(h, [('input[name=fullname]', who['name']), ('input[name=email]', who['email']), ('input[name=phone]', who['phone'])], how)
    h.tap('input[name=accept_policy]')
    h.tap('[data-primary]')
    if kind == 'peticion':
        h.screen('.wr-done h2', 'enviada', final=True)
        return h
    h.screen('[data-stripe-stub]', 'pago')
    stripe_part(h, pay)
    fr = next(x for x in page.frames if 'f=boton' in x.url)
    secret = fr.evaluate('() => window.__stripeStub.secret')
    env['stripe'].pay(env['stripe'].session_by_secret(secret)['id'])
    fr.evaluate('() => window.__stripeStub.complete()')   # Stripe says the payment is done (onComplete)
    h.screen('.wr-done h2:has-text("Reservado")', 'reservado', final=True)
    return h


FLOWS = {'antes': antes, 'despues': despues}
OLD_FILES = {'antes'}


def run(which: str, out: Path | None, walks=None):
    flow = FLOWS[which]
    result = {'version': which, 'ritmo': {'lectura_s': READ, 'toque_s': TAP, 'letra_s': CHAR, 'scroll_s_por_pantalla': FLICK, 'monedero_s': WALLET, 'mirar_sugerencia_s': GLANCE},
              'recorridos': {}}
    n = 0
    for color in ('#0b7a75', '#c2410c'):
        env = setup(color, pk=which != 'antes')
        try:
            with sync_playwright() as p:
                browser = chromium(p)
                for dev, opts in (('movil', PHONE), ('ordenador', DESK)):
                    for walk in (walks or WALKS):
                        if color != '#0b7a75' and walk not in ('peticion', 'tarjeta'): continue   # the second colour: the pictures of two walks
                        ctx = browser.new_context(**opts); reset_limits(env['srv'])
                        if which in OLD_FILES: serve_old(ctx, env['srv'].base)
                        ctx.route('https://js.stripe.com/**', lambda r: r.fulfill(status=200, content_type='application/javascript', body=STUB))
                        ctx.route('https://checkout.stripe.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body='<!doctype html><title>Stripe</title><p>Pago</p>'))
                        page = ctx.new_page(); page.goto(env['host'] + '/index.html'); page.wait_for_load_state('networkidle')
                        tag = f"{dev}-{walk}{'-color2' if color != '#0b7a75' else ''}"
                        n += 1
                        keep = out if walk in ('peticion', 'tarjeta') else None
                        h = flow(page, env, walk, keep, tag, person(n))
                        if h is not None:
                            if color == '#0b7a75': result['recorridos'][f'{dev}-{walk}'] = h.result()
                            print(tag, json.dumps(h.result(), ensure_ascii=False), flush=True)
                        ctx.close()
                browser.close()
        finally:
            env['site'].shutdown(); env['srv'].stop(); env['stripe'].stop()
    if out:
        out.mkdir(parents=True, exist_ok=True); (out / 'cronometro.json').write_text(json.dumps(result, ensure_ascii=False, indent=1), encoding='utf-8')
    return result


if __name__ == '__main__':
    run(sys.argv[1] if len(sys.argv) > 1 else 'antes', Path(sys.argv[2]) if len(sys.argv) > 2 else None)
