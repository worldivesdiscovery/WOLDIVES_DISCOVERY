#!/usr/bin/env python3
"""v50.58 · Bloque 2 (reserva exprés): cronómetro de la reserva desde la web de un centro, a ritmo humano.

Desde el toque en «Reservar» de la web del centro (scripts/demo/web-de-centro-ejemplo.html, servida desde otro origen)
hasta la confirmación, para una reserva normal: un servicio, una fecha y 2 personas. Mide:

  - segundos de reloj, con las respuestas reales del servidor;
  - toques: cada botón, casilla o campo que se toca (escribir en un campo cuenta como el toque de entrar en él);
  - pantallas: cada vez que el contenido de la reserva cambia de paso;
  - scroll: los píxeles que hay que desplazar para llegar al botón principal de cada pantalla.

Ritmo humano (el mismo antes y después): 1,5 s de lectura al aparecer cada pantalla, 0,5 s entre toques, 0,3 s por letra
en el móvil (unas 40 palabras por minuto, la media escribiendo en el móvil según Palin et al., MobileHCI 2019) y 0,2 s
en el ordenador (unas 52 palabras por minuto, Dhakal et al., CHI 2018), y 0,6 s por cada pantalla de scroll. Los datos de
quien reserva se escriben a mano, letra a letra; con «autocompletar» (la sugerencia del navegador) serían un toque.

El pago con tarjeta de Stripe no se puede abrir aquí (Stripe solo existe en internet): su parte se suma con el mismo
ritmo, contando lo que pide Stripe (tarjeta, caducidad, CVC, nombre en la tarjeta y «Pagar»; el correo ya va escrito
porque WORLDIVES se lo pasa), y la de Apple Pay o Google Pay como un toque y la confirmación del teléfono (1,5 s). Va
marcada como «modelo» en el resultado.

Cada recorrido empieza con los límites del widget a cero (las 6 reservas seguidas desde el mismo ordenador harían
saltar la comprobación «no soy un robot», que una persona real no ve).

    python3 tests/navegador/cronometro_reserva.py antes [carpeta-de-capturas]

Escribe el resultado en <carpeta>/cronometro.json. «antes» recorre la reserva de v50.56/57: la copia guardada en
tests/navegador/reserva_v50_57/ se sirve en lugar de los archivos de ahora, así se puede repetir cuando se quiera.
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
READ, TAP, FLICK, WALLET = 1.5, 0.5, 0.6, 2.0
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
        self.taps = 0; self.screens = 0; self.scroll = 0; self.t0 = time.time(); self.modelled = 0.0; self.notes = []

    def wait(self, s): self.page.wait_for_timeout(int(s * 1000))

    def screen(self, ready: str, name: str, button: str | None = None):
        """A new screen: wait for it, read it, measure how far its main button is, and take its picture."""
        self.f.locator(ready).first.wait_for(timeout=15000)
        self.screens += 1
        self.wait(READ)
        if button:
            over = self.f.locator(button).first.evaluate('(b) => { const r = b.getBoundingClientRect(); return Math.max(0, Math.ceil(r.bottom - window.innerHeight)); }')
            if over > 0:
                self.scroll += over; self.wait(FLICK * max(1, round(over / 700)))
        if self.shots:
            self.shots.mkdir(parents=True, exist_ok=True)
            self.page.screenshot(path=str(self.shots / f'{self.prefix}-{self.screens}-{name}.png'))

    def tap(self, sel, nth=0):
        self.wait(TAP); loc = self.f.locator(sel).nth(nth); loc.scroll_into_view_if_needed(); loc.click(); self.taps += 1

    def type(self, sel, text):
        self.wait(TAP); loc = self.f.locator(sel).first; loc.scroll_into_view_if_needed(); loc.click(); self.taps += 1
        loc.press_sequentially(text, delay=int(self.char * 1000))

    def model(self, taps, chars=0, extra=0.0, note=''):
        """A part that can not run here (Stripe's own page): counted with the same pace."""
        self.taps += taps; self.screens += 1
        self.modelled += READ + taps * TAP + chars * self.char + extra
        self.notes.append(note)

    def result(self):
        wall = time.time() - self.t0
        return {'segundos': round(wall + self.modelled, 1), 'segundos_medidos': round(wall, 1), 'segundos_modelo': round(self.modelled, 1),
                'toques': self.taps, 'pantallas': self.screens, 'scroll_px': self.scroll, 'notas': self.notes}


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
        center.post('/api/provider-services/slot', {'service_id': req, 'slot_date': day(n), 'slot_time': '10:00', 'spots_total': 6})
        center.post('/api/provider-services/slot', {'service_id': pay, 'slot_date': day(n), 'slot_time': '09:00', 'spots_total': 8})
    slug = center.get('/api/provider/vender').json['slug']
    port = free_port()
    center.post('/api/provider/vender', {'domains': [f'localhost:{port}'], 'color': color})
    folder = Path(tempfile.mkdtemp(prefix='web-centro-'))
    html = TEMPLATE.read_text(encoding='utf-8').replace('__WORLDIVES__', srv.base).replace('__CENTRO__', slug).replace('__SERVICIO__', str(pay))
    (folder / 'index.html').write_text(html, encoding='utf-8')
    site = host_site(folder, port)
    return {'srv': srv, 'stripe': stripe, 'site': site, 'host': f'http://localhost:{port}', 'slug': slug, 'req': req, 'pay': pay, 'center': center}


# ------------------------------------------------------------------------------------------------ the booking of v50.56/57
def antes(page, kind, shots, prefix, who=PERSON):
    """«Reservar ahora» → list of services → «Ver fechas» → calendar → time → form (people, details, conditions) → send."""
    page.click('#boton-reservar'); page.wait_for_selector('div[role=dialog] iframe', timeout=8000)
    h = Human(page, page.frame_locator('div[role=dialog] iframe'), shots, prefix); h.taps = 1
    title = 'Bautizo' if kind == 'peticion' else 'Doble inmersión'
    h.screen('.wr-card', 'servicios', '.wr-card >> nth=-1')
    h.tap(f'.wr-card:has-text("{title}") button.wr-btn')
    h.screen('.wr-cal', 'calendario')
    h.tap('.wr-day.on')
    h.screen('[data-pick]', 'horas', '[data-pick]')
    h.tap('[data-pick]')
    h.screen('[data-form]', 'datos', '[data-go]')
    h.tap('[data-pax="1"]')
    h.type('input[name=fullname]', who['name']); h.type('input[name=email]', who['email']); h.type('input[name=phone]', who['phone'])
    h.tap('input[name=accept_policy]')
    if kind == 'peticion':
        h.tap('[data-go]'); h.screen('.wr-done h2', 'enviada')
        return h
    with page.expect_popup() as pop:
        h.tap('[data-go]')
    pop.value.wait_for_load_state()
    h.f.locator('.wr-done h2').wait_for(timeout=15000)
    return h


FLOWS = {'antes': antes}
OLD_FILES = {'antes'}


def run(which: str, out: Path | None):
    flow = FLOWS[which]; result = {'version': which, 'ritmo': {'lectura_s': READ, 'toque_s': TAP, 'letra_s': CHAR, 'scroll_s_por_pantalla': FLICK, 'monedero_s': WALLET}, 'recorridos': {}}
    n = 0
    for color in ('#0b7a75', '#c2410c'):
        env = setup(color)
        try:
            with sync_playwright() as p:
                browser = chromium(p)
                for dev, opts in (('movil', PHONE), ('ordenador', DESK)):
                    for kind in ('peticion', 'tarjeta', 'monedero'):
                        if color != '#0b7a75' and kind != 'peticion': continue   # the second colour: only the pictures of one walk
                        ctx = browser.new_context(**opts); reset_limits(env['srv'])
                        if which in OLD_FILES: serve_old(ctx, env['srv'].base)
                        ctx.route('https://checkout.stripe.test/**', lambda r: r.fulfill(status=200, content_type='text/html', body='<!doctype html><title>Stripe</title><p>Pago</p>'))
                        page = ctx.new_page(); page.goto(env['host'] + '/index.html'); page.wait_for_load_state('networkidle')
                        tag = f"{dev}-{kind}{'-color2' if color != '#0b7a75' else ''}"
                        n += 1
                        h = flow(page, 'peticion' if kind == 'peticion' else 'pago', out if (kind != 'monedero') else None, tag, person(n))
                        if kind == 'tarjeta': h.model(STRIPE_CARD['taps'], STRIPE_CARD['chars'], note='página de pago de Stripe con la tarjeta escrita a mano (modelo)')
                        if kind == 'monedero': h.model(1, 0, WALLET, note='Apple Pay o Google Pay en la página de Stripe (modelo)')
                        if color == '#0b7a75': result['recorridos'][f'{dev}-{kind}'] = h.result()
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
