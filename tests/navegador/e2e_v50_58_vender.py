#!/usr/bin/env python3
"""v50.58 · Parte 5 «Reservas desde tu web e Instagram», en el navegador
(docs/encargos/encargo-revision-usabilidad-15-16-10-2026.md, Parte 5). En su orden:

1. El menú se llama «Reservas desde tu web e Instagram».
2. Arriba, lo más fácil: «Tu enlace de reservas» con Copiar, Compartir en WhatsApp y Descargar QR, y la frase.
   El contador «Este mes te han reservado N personas desde tu web».
3. Paso 1 «¿Qué quieres que reserven?»: todo, un servicio o un tipo (el código cambia).
4. Paso 2 «¿Cómo quieres que se vea?»: botón, calendario o lista, con dibujo y vista previa en vivo.
5. Paso 3 «Ponlo en tu web»: «Copiar código», la frase, las guías de WordPress, Wix y Squarespace en 3 pasos con
   dibujos, y «Enviar las instrucciones a mi informático» (el correo sale con el código).
6. Paso 4: «Comprobar» → «Aún no lo encontramos» y «✔ Tu botón está funcionando», que autoriza el dominio.
7. Lo técnico plegado al final en «Para programadores».
8. Móvil a 390 px sin desplazamiento lateral; en inglés; sin errores en la consola.

    python3 tests/navegador/e2e_v50_58_vender.py [carpeta-de-capturas]

No usa la demo: un servidor nuevo y una web del centro simulada en local (nada sale de la máquina)."""
from __future__ import annotations

import sys
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Server, ServerTestCase  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
DESK = {'viewport': {'width': 1440, 'height': 900}, 'locale': 'es-ES'}
PHONE = {'viewport': {'width': 390, 'height': 844}, 'locale': 'es-ES', 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}
PAGES = {}


class Web:
    """The centre's website on the internet, played locally: /fetch?url=<address> answers PAGES[host] or 404."""
    def __init__(self):
        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                url = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('url', [''])[0]
                body = PAGES.get(urllib.parse.urlparse(url).hostname or '')
                self.send_response(200 if body is not None else 404); self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers()
                self.wfile.write((body or 'No existe').encode())
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.base = f'http://127.0.0.1:{self.httpd.server_address[1]}'
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()


def run(out: Path | None):
    rows = []

    def check(name, ok, detail=''):
        rows.append((name, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + name + (f'  · {str(detail)[:300]}' if detail != '' else ''), flush=True)

    web = Web()
    ServerTestCase.server = Server({'WOD_MEDIA_FETCH_BASE': web.base, 'WOD_PAYMENTS_TOTP_REQUIRED': '0'}).start()
    srv = ServerTestCase.server
    errors = []
    try:
        t = ServerTestCase('run')
        admin = t.make_admin()
        center = t.make_center(admin, 'vtw', phone='+34 600 590 101')
        cid = center.user['center_id']
        srv.sql("UPDATE centers SET name='Buceo Mar Azul',plan_code='pro',plan_status='active',plan_expires_at='2099-12-31',email='hola@buceomarazul.es' WHERE id=?", (cid,))
        s1 = center.post('/api/provider-services', {'title': 'Bautizo de buceo', 'price': 60, 'booking_mode': 'request', 'service_type': 'bautizo'}).json['id']
        s2 = center.post('/api/provider-services', {'title': 'Curso Open Water', 'price': 420, 'booking_mode': 'request', 'service_type': 'curso'}).json['id']
        diver = t.make_diver('vtwcliente')
        for pax in (3, 2):
            srv.sql("""INSERT INTO bookings(user_id,center_id,booking_date,participants,status,channel,created_at,updated_at)
                       VALUES(?,?,date('now','+9 day'),?,'confirmed','widget',strftime('%Y-%m-%dT%H:%M:%S','now'),strftime('%Y-%m-%dT%H:%M:%S','now'))""", (diver.user['id'], cid, pax))
        slug = center.get('/api/provider/vender').json['slug']
        PAGES['buceomarazul.com'] = f'<html><body><h1>Buceo Mar Azul</h1><script src="https://worlddivesdiscovery.com/widget.js" async></script><a data-worldives="boton" data-centro="{slug}">Reservar</a></body></html>'
        PAGES['buceo-sin-boton.com'] = '<html><body><h1>Otra web</h1><p>Llámanos.</p></body></html>'
        base = srv.base

        with sync_playwright() as p:
            browser = chromium(p)

            def page_for(opts, lang=None):
                ctx = browser.new_context(**opts)
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                ctx.grant_permissions(['clipboard-read', 'clipboard-write'], origin=base)
                pg = ctx.new_page(); pg.lang = lang
                pg.on('pageerror', lambda e: errors.append(str(e)))
                pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' and 'ERR_' not in m.text and 'tile.openstreetmap' not in m.text else None)
                return pg

            def go(pg, route, wait=1200):
                pg.goto(base + (f'/?lang={pg.lang}' if pg.lang else '/') + route); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(wait)

            def login(pg, user):
                go(pg, '#/login', 500); pg.fill('#login', user); pg.fill('#password', PW); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1300)

            def shot(pg, name, full=False):
                if out: out.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(out / f'{name}.png'), full_page=full)

            def code(pg):
                return pg.inner_text('#vt-code')

            ce = page_for(DESK); login(ce, 'center_vtw'); go(ce, '#/admin?tab=vender', 1800)
            ce.wait_for_selector('#cb-vender .vt-wrap', timeout=15000)
            # ============================================================ 1 · the menu
            check('1 · el menú se llama «Reservas desde tu web e Instagram»', ce.locator('.cb-nav[data-cbtab="vender"]', has_text='Reservas desde tu web e Instagram').count() >= 1)
            # ============================================================ 2 · the easiest first
            order = ce.evaluate("[...document.querySelectorAll('#cb-vender .vt-card')].map(x=>x.id||x.className)")
            check('2 · arriba de todo, «Tu enlace de reservas» (antes de los pasos)', 'vt-easy' in order[0] and order.index('vt-step1') > 0, order)
            easy = ce.inner_text('.vt-easy')
            check('2 · con Copiar, Compartir en WhatsApp y Descargar QR', all(x in easy for x in ('Copiar', 'Compartir en WhatsApp', 'Descargar QR')), easy)
            check('2 · y la frase «Ponlo en tu Instagram, en Google Maps o mándalo por WhatsApp»', 'Ponlo en tu Instagram, en Google Maps o mándalo por WhatsApp' in easy)
            wa = ce.get_attribute('#vt-wa', 'href')
            check('2 · WhatsApp lleva el enlace de reservas', wa.startswith('https://wa.me/?text=') and f'/c/{slug}' in urllib.parse.unquote(wa), wa)
            check('2 · el QR se descarga en PNG', ce.get_attribute('#vt-qr-dl', 'href').endswith('/qr.png?descargar=1'))
            ce.click('#vt-link-copy'); ce.wait_for_timeout(300)
            clip = ce.evaluate('navigator.clipboard.readText()')
            check('2 · «Copiar» copia el enlace', clip.endswith(f'/c/{slug}'), clip)
            cnt = ce.inner_text('.vt-count')
            check('2 · contador «Este mes te han reservado 5 personas desde tu web»', 'Este mes te han reservado 5 personas desde tu web' in cnt, cnt)
            shot(ce, 'vender-1-arriba-enlace-y-contador')
            # ============================================================ 3 · step 1
            s1t = ce.inner_text('#vt-step1')
            check('3 · paso 1 «¿Qué quieres que reserven?»: todo, un servicio o un tipo', all(x in s1t for x in ('¿Qué quieres que reserven?', 'Todo tu catálogo', 'Un servicio concreto', 'Un tipo')), s1t)
            base_code = code(ce)
            check('3 · todo el catálogo: el código sin servicio', f'data-centro="{slug}"' in base_code and 'data-servicio' not in base_code and 'data-tipo' not in base_code, base_code)
            ce.check('input[name="vt-what"][value="service"]'); ce.wait_for_selector('#vt-svc'); ce.wait_for_timeout(500)
            ce.select_option('#vt-svc', str(s2)); ce.wait_for_timeout(700)
            check('3 · un servicio concreto: data-servicio en el código', f'data-servicio="{s2}"' in code(ce), code(ce))
            ce.check('input[name="vt-what"][value="type"]'); ce.wait_for_timeout(700)
            ce.select_option('#vt-type', 'curso'); ce.wait_for_timeout(700)
            check('3 · un tipo (cursos): data-tipo en el código', 'data-tipo="curso"' in code(ce), code(ce))
            ce.check('input[name="vt-what"][value="all"]'); ce.wait_for_timeout(700)
            # ============================================================ 4 · step 2
            s2t = ce.inner_text('#vt-step2')
            check('4 · paso 2: botón «Reservar», calendario y lista de próximas salidas', all(x in s2t for x in ('Un botón «Reservar»', 'Un calendario', 'Una lista de próximas salidas')), s2t)
            check('4 · cada opción con su dibujo', ce.locator('#vt-step2 .vt-look svg').count() == 3)
            check('4 · «El color y el logo salen solos de tu perfil»', 'El color y el logo salen solos de tu perfil' in s2t)
            ce.click('.vt-look[data-fmt="calendario"]'); ce.wait_for_timeout(800)
            check('4 · el calendario cambia el código', 'data-worldives="calendario"' in code(ce), code(ce))
            src = ce.get_attribute('#vt-frame', 'src')
            check('4 · la vista previa en vivo sigue la elección (modo de prueba)', 'f=calendario' in src and 'prueba=1' in src, src)
            frame = ce.frame_locator('#vt-frame')
            try: prev = frame.locator('body').inner_text(timeout=10000)
            except Exception as exc: prev = f'ERROR {exc}'
            check('4 · la vista previa enseña los servicios', 'Bautizo de buceo' in prev or 'Curso Open Water' in prev, prev[:200])
            ce.locator('#vt-step2').scroll_into_view_if_needed(); ce.wait_for_timeout(1200); shot(ce, 'vender-2-como-se-ve')
            ce.click('.vt-look[data-fmt="boton"]'); ce.wait_for_timeout(800)
            # ============================================================ 5 · step 3
            s3t = ce.inner_text('#vt-step3')
            check('5 · paso 3: «Copiar código» y la frase del encargo', 'Copiar código' in s3t and 'Pega este código en tu web donde quieras que aparezca el botón' in s3t, s3t[:300])
            ce.click('#vt-copy'); ce.wait_for_timeout(300)
            check('5 · «Copiar código» copia el código del botón', 'data-worldives="boton"' in ce.evaluate('navigator.clipboard.readText()'))
            guides = {}
            for k in ('wordpress', 'wix', 'squarespace'):
                ce.click(f'.vt-tab[data-guide="{k}"]'); ce.wait_for_timeout(200)
                pane = ce.locator(f'[data-guide-pane="{k}"]')
                guides[k] = (pane.locator('li').count(), pane.locator('svg').count(), pane.is_visible())
            check('5 · guías de WordPress, Wix y Squarespace: 3 pasos con dibujo cada una', all(g == (3, 3, True) for g in guides.values()), guides)
            ce.click('.vt-tab[data-guide="wordpress"]')
            ce.locator('#vt-step3').scroll_into_view_if_needed(); ce.wait_for_timeout(300); shot(ce, 'vender-3-ponlo-en-tu-web')
            ce.click('#vt-mail'); ce.wait_for_selector('#vt-mail-to'); ce.wait_for_timeout(300)
            ce.fill('#vt-mail-to', 'jordi@informatica-ejemplo.es'); ce.fill('#vt-mail-name', 'Jordi'); ce.fill('#vt-mail-note', 'Ponlo debajo de las fotos.')
            shot(ce, 'vender-4-enviar-al-informatico')
            ce.click('#vt-mail-send'); ce.wait_for_timeout(1000)
            mail = srv.sql("SELECT to_email, reply_to FROM email_outbox WHERE template='web_instructions' ORDER BY id DESC LIMIT 1")
            check('5 · «Enviar las instrucciones a mi informático» manda el correo (y la respuesta va al centro)',
                  mail and mail[0]['to_email'] == 'jordi@informatica-ejemplo.es' and mail[0]['reply_to'] == 'hola@buceomarazul.es', mail)
            check('5 · y lo dice en pantalla', ce.locator('.toast, #toast, [role=status]', has_text='Enviado a jordi@informatica-ejemplo.es').count() >= 1)
            # ============================================================ 6 · step 4
            ce.fill('#vt-check-url', 'buceo-sin-boton.com'); ce.click('#vt-check'); ce.wait_for_selector('#vt-check-out .notice', timeout=10000)
            out1 = ce.inner_text('#vt-check-out')
            check('6 · «Comprobar» en una web sin el código: «Aún no lo encontramos» y qué hacer', 'Aún no lo encontramos' in out1 and 'publica los cambios' in out1, out1)
            ce.fill('#vt-check-url', 'buceomarazul.com'); ce.click('#vt-check'); ce.wait_for_selector('#vt-check-out .vt-check-ok', timeout=10000)
            out2 = ce.inner_text('#vt-check-out')
            check('6 · con el código: «✔ Tu botón está funcionando»', '✔ Tu botón está funcionando' in out2, out2)
            check('6 · y su web queda autorizada sola', 'Hemos autorizado buceomarazul.com' in out2 and 'buceomarazul.com' in center.get('/api/provider/vender').json['domains'], out2)
            ce.locator('#vt-step4').scroll_into_view_if_needed(); ce.wait_for_timeout(300); shot(ce, 'vender-5-comprobado')
            # ============================================================ 7 · for programmers, folded at the end
            order = ce.evaluate("[...document.querySelectorAll('#cb-vender .vt-card')].map(x=>x.id)")
            check('7 · «Para programadores» al final y plegado', order[-1] == 'vt-dev' and not ce.evaluate("document.querySelector('#vt-dev').open"), order)
            dev = ce.inner_text('#vt-dev summary')
            check('7 · dentro: API, claves, webhooks y dominios autorizados', all(x in dev for x in ('API', 'webhooks', 'dominios autorizados')), dev)
            ce.click('#vt-dev summary'); ce.wait_for_timeout(300)
            check('7 · al abrirlo, el dominio autorizado en su lista', 'buceomarazul.com' in ce.input_value('#vt-domains'))
            check('7 · y las claves de la API y el calendario', ce.locator('#vt-key-new').is_visible() and ce.locator('#vt-ical').count() == 1)
            # ============================================================ 8 · phone, English, console
            ph = page_for(PHONE); login(ph, 'center_vtw'); go(ph, '#/admin?tab=vender', 2000)
            ph.wait_for_selector('#cb-vender .vt-wrap', timeout=15000)
            sw = ph.evaluate('[document.documentElement.scrollWidth, window.innerWidth]')
            check('8 · móvil 390 px: sin desplazamiento lateral', sw[0] <= sw[1] + 1, sw)
            shot(ph, 'vender-6-movil-arriba')
            ph.locator('#vt-step3').scroll_into_view_if_needed(); ph.wait_for_timeout(300); shot(ph, 'vender-7-movil-paso-3')
            en = page_for(DESK, lang='en'); login(en, 'center_vtw'); go(en, '#/admin?tab=vender', 2000)
            en.wait_for_selector('#cb-vender .vt-wrap', timeout=15000)
            etxt = en.inner_text('#cb-vender')
            check('8 · en inglés', all(x in etxt for x in ('Your booking link', 'What do you want them to book?', 'Put it on your website', 'Check that it works', 'For developers'))
                  and '¿Qué quieres que reserven?' not in etxt, etxt[:400])
            shot(en, 'vender-8-ingles')
            bad = [e for e in errors if 'favicon' not in e]
            check('8 · sin errores en la consola', not bad, bad[:5])
            browser.close()
    finally:
        srv.stop(); web.httpd.shutdown()
    ok = sum(1 for _, x in rows if x)
    print(f'\n{ok}/{len(rows)} comprobaciones correctas')
    return ok == len(rows)


if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(0 if run(out) else 1)
