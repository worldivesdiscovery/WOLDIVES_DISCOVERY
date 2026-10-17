#!/usr/bin/env python3
"""v50.58 · 6.4 «Foto por tipo de buceo», en el navegador
(docs/encargos/encargo-revision-usabilidad-15-16-10-2026.md, 6.4). En su orden:

1. Un punto sin foto propia muestra la foto de su tipo principal (un pecio, la del pecio; una pared, la de la pared),
   en la lista de puntos y en su ficha, con su texto alternativo. Nunca una foto al azar.
2. Un punto de un tipo sin foto adecuada (un canal, una cueva) muestra el color del mar, no otra foto.
3. Administración → Tipos de buceo: «Poner foto» abre el encuadre (marco 16:10, arrastrar, zoom, flechas) con la vista
   previa de la tarjeta, la cabecera y un punto sin foto; «Guardar» la deja en WebP con sus copias (srcset).
4. La foto nueva sale al momento en la tarjeta del tipo y en los puntos de ese tipo sin foto propia.
5. Una foto pequeña no abre el encuadre: un aviso. «Restaurar original» vuelve al color del mar.
6. En inglés (el texto alternativo y la ventana traducidos) y en el móvil a 390 px sin desplazamiento lateral; sin
   errores en la consola.

    python3 tests/navegador/e2e_v50_58_fototipo.py [carpeta-de-capturas]

No usa la demo: un servidor nuevo con el catálogo de ejemplo de puntos."""
from __future__ import annotations

import io
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Server, ServerTestCase  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

APW = 'admin-seguro-2026'
DESK = {'viewport': {'width': 1440, 'height': 900}, 'locale': 'es-ES'}
PHONE = {'viewport': {'width': 390, 'height': 844}, 'locale': 'es-ES', 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}
NO_COOKIES = "try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}"


def photo(path: Path, w, h):
    """A real photo for the upload: a sea gradient with a «wreck» (a dark shape) on the right."""
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (w, h))
    d = ImageDraw.Draw(im)
    for y in range(h):
        t = y / h; d.line([(0, y), (w, y)], fill=(int(10 + 20 * t), int(120 - 70 * t), int(170 - 90 * t)))
    d.polygon([(w * .55, h * .72), (w * .9, h * .62), (w * .95, h * .78), (w * .6, h * .86)], fill=(40, 34, 30))
    buf = io.BytesIO(); im.save(buf, 'JPEG', quality=90); path.write_bytes(buf.getvalue()); return path


def run(out: Path | None):
    rows = []

    def check(name, ok, detail=''):
        rows.append((name, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + name + (f'  · {str(detail)[:300]}' if detail != '' else ''), flush=True)

    ServerTestCase.server = Server({'WOD_PAYMENTS_TOTP_REQUIRED': '0'}).start()
    srv = ServerTestCase.server
    errors = []
    tmp = srv.tmp
    try:
        t = ServerTestCase('run')
        t.make_admin()
        pick = lambda kind: srv.sql("""SELECT p.id,p.name FROM dive_points p WHERE p.active=1 AND p.dive_type=?
                                       AND NOT EXISTS(SELECT 1 FROM dive_point_photos f WHERE f.dive_point_id=p.id) ORDER BY p.id LIMIT 1""", (kind,))[0]
        wreck, wall, canal = pick('Pecio'), pick('Pared'), pick('Canal')
        big, small = photo(tmp / 'canal.jpg', 2400, 1500), photo(tmp / 'pequena.jpg', 600, 380)
        with sync_playwright() as p:
            browser = chromium(p)

            def page_for(opts, lang=None):
                ctx = browser.new_context(**opts); ctx.add_init_script(NO_COOKIES)
                pg = ctx.new_page(); pg.lang = lang
                # without internet here, the map tiles of OpenStreetMap on the dive site page can not load: not the page's fault
                pg.on('console', lambda m: m.type == 'error' and 'favicon' not in m.text and 'tile.openstreetmap' not in m.text
                      and 'ERR_TUNNEL_CONNECTION_FAILED' not in m.text and errors.append(m.text))
                pg.on('pageerror', lambda e: errors.append(str(e)))
                return pg

            base = srv.base

            def go(pg, route, wait=1200):
                pg.goto(base + (f'/?lang={pg.lang}' if pg.lang else '/') + route); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(wait)

            def login(pg, user, pw):
                go(pg, '#/login', 500); pg.fill('#login', user); pg.fill('#password', pw); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1400)

            def shot(pg, name, full=False):
                if out: out.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(out / f'{name}.png'), full_page=full)

            def hero(pg, pid):
                go(pg, f'#/punto?id={pid}', 1500)
                return pg.eval_on_selector('.pp-hero .tp-hero-img', 'i=>({src:i.getAttribute("src"),alt:i.getAttribute("alt"),ok:i.complete&&i.naturalWidth>0})')

            # 1–2 · the dive sites without their own photo
            pub = page_for(DESK)
            h = hero(pub, wreck['id'])
            check('punto «Pecio» sin foto: la foto de los pecios', h['src'] == '/img/portada/logbook1.webp' and h['ok'], h)
            check('su texto alternativo dice qué es', h['alt'] == 'Foto representativa de Pecios y naufragios', h['alt'])
            h = hero(pub, wall['id'])
            check('punto «Pared» sin foto: la foto de las paredes', h['src'] == '/img/destinos/australia.webp' and h['ok'], h)
            h = hero(pub, canal['id'])
            check('punto «Canal» (tipo sin foto adecuada): el color del mar, no otra foto', h['src'] == '/img/punto-sin-foto.svg' and h['ok'] and h['alt'] == '', h)
            shot(pub, '01-punto-canal-sin-foto')
            go(pub, '#/puntos?q=' + wreck['name'].replace(' ', '%20'), 1800)
            src = pub.eval_on_selector_all('.pt-card .pt-media img', 'l=>l.map(i=>i.getAttribute("src"))')
            check('en la lista de puntos, el pecio con la foto de su tipo', '/img/portada/logbook1.webp' in src, src[:4])
            shot(pub, '02-lista-pecio')

            # 3 · Administración → Tipos de buceo: frame and preview
            ad = page_for(DESK); login(ad, 'admin', APW); go(ad, '#/admin?tab=divetypes', 2000)
            card = ad.locator('.mm-card[data-key="type:canales"]')
            check('Tipos de buceo: «Canales» sin foto y con «Poner foto»', card.count() == 1 and card.locator('.mm-empty').count() == 1 and 'Poner foto' in card.locator('.mm-file').inner_text(), card.inner_text()[:200] if card.count() else '')
            card.locator('.mm-file input').set_input_files(str(small)); ad.wait_for_timeout(800)
            check('una foto pequeña no abre el encuadre: aviso', ad.locator('#mmc-m').count() == 0 and 'muy pequeña' in ad.locator('body').inner_text(), '')
            ad.wait_for_timeout(2500)
            card.locator('.mm-file input').set_input_files(str(big)); ad.wait_for_selector('#mmc-m .mmc-frame img', timeout=8000); ad.wait_for_timeout(600)
            m = ad.locator('#mmc-m')
            check('se abre el encuadre con el nombre del tipo', 'Encuadra la foto de «Canales»' in m.inner_text(), m.inner_text()[:120])
            ratio = ad.eval_on_selector('#mmc-frame', 'f=>f.clientWidth/f.clientHeight')
            check('el marco es 16:10, como la foto que se guarda', abs(ratio - 1.6) < 0.02, ratio)
            check('vista previa: tarjeta, cabecera y punto sin foto', m.locator('.mmc-box').count() == 3 and all(x in m.inner_text() for x in ('Tarjeta del tipo', 'Cabecera de su página', 'Punto de este tipo sin foto propia')))
            check('aviso de calidad: buena', 'Buena calidad' in ad.inner_text('#mmc-q'), ad.inner_text('#mmc-q'))
            before = ad.eval_on_selector('#mmc-frame img', 'i=>i.style.left')
            fb = ad.locator('#mmc-frame').bounding_box()
            ad.mouse.move(fb['x'] + fb['width'] / 2, fb['y'] + fb['height'] / 2); ad.mouse.down()
            ad.mouse.move(fb['x'] + fb['width'] / 2 - 120, fb['y'] + fb['height'] / 2, steps=6); ad.mouse.up()
            # at zoom 1 a 16:10 photo in a 16:10 frame cannot move: zoom first, then drag
            ad.fill('#mmc-z', '160'); ad.dispatch_event('#mmc-z', 'input'); ad.wait_for_timeout(200)
            z_left = ad.eval_on_selector('#mmc-frame img', 'i=>i.style.left')
            ad.mouse.move(fb['x'] + fb['width'] / 2, fb['y'] + fb['height'] / 2); ad.mouse.down()
            ad.mouse.move(fb['x'] + fb['width'] / 2 - 160, fb['y'] + fb['height'] / 2 - 60, steps=8); ad.mouse.up(); ad.wait_for_timeout(200)
            after = ad.eval_on_selector('#mmc-frame img', 'i=>i.style.left')
            check('el zoom acerca y arrastrar mueve la foto', before != z_left and z_left != after, (before, z_left, after))
            prev = ad.eval_on_selector_all('.mmc-box img', 'l=>l.map(i=>i.style.left)')
            ad.focus('#mmc-frame'); ad.keyboard.press('ArrowLeft'); ad.keyboard.press('ArrowLeft'); ad.wait_for_timeout(150)
            check('las flechas también mueven la foto y la vista previa sigue', ad.eval_on_selector_all('.mmc-box img', 'l=>l.map(i=>i.style.left)') != prev)
            q = ad.inner_text('#mmc-q')
            check('con zoom avisa si se verá menos nítida', '1600' in q, q)
            shot(ad, '03-encuadre-y-vista-previa')
            ad.click('#mmc-ok'); ad.wait_for_selector('#mmc-m', state='detached', timeout=10000); ad.wait_for_timeout(1500)
            img = ad.locator('.mm-card[data-key="type:canales"] .mm-preview img')
            src, srcset = (img.get_attribute('src') or ''), (img.get_attribute('srcset') or '')
            check('guardada: WebP con sus copias de 640, 960 y 1440', src.startswith('/assets/uploads/divetype_canales_') and all(f'-{w}.webp {w}w' in srcset for w in (640, 960, 1440)), (src, srcset))
            check('la tarjeta dice «Personalizada»', 'Personalizada' in ad.locator('.mm-card[data-key="type:canales"] .mm-badge').inner_text())
            shot(ad, '04-tipos-de-buceo-guardada')
            files = sorted(f.name for f in (tmp / 'uploads').glob('divetype_canales_*'))
            check('en el servidor: la foto y sus 3 copias', len(files) == 4, files)

            # 4 · at once in the type card and in the dive sites of that type
            pub2 = page_for(DESK)
            h = hero(pub2, canal['id'])
            check('el punto «Canal» sin foto ya muestra la foto nueva del tipo', h['src'] == src and h['ok'], h)
            check('con su texto alternativo', h['alt'] == 'Foto representativa de Canales', h['alt'])
            go(pub2, '#/tipos', 1800)
            tc = pub2.eval_on_selector('.tp-card[data-key="canales"] .tp-card-media img', 'i=>({src:i.getAttribute("src"),alt:i.getAttribute("alt"),set:i.getAttribute("srcset")||"",ok:i.complete&&i.naturalWidth>0})')
            check('la tarjeta del tipo «Canales» con la foto y su srcset', tc['src'] == src and '-640.webp' in tc['set'], tc)
            shot(pub2, '05-tipos-tarjeta-canales')

            # 6 · English and the phone
            en = page_for(DESK, lang='en')
            h = hero(en, canal['id'])
            check('en inglés, el texto alternativo traducido', h['alt'] not in ('', 'Foto representativa de Canales') and 'Foto' not in h['alt'], h['alt'])
            h = hero(en, wreck['id'])
            check('en inglés, el del pecio también', 'Foto' not in h['alt'] and h['alt'] != '', h['alt'])
            ph = page_for(PHONE); login(ph, 'admin', APW); go(ph, '#/admin?tab=divetypes', 2200)
            ph.locator('.mm-card[data-key="type:lagos"] .mm-file input').set_input_files(str(big)); ph.wait_for_selector('#mmc-m .mmc-frame img', timeout=8000); ph.wait_for_timeout(700)
            sw = ph.evaluate('()=>[document.documentElement.scrollWidth,innerWidth]')
            check('móvil 390: el encuadre cabe sin desplazamiento lateral', sw[0] <= sw[1], sw)
            box = ph.locator('#mmc-frame').bounding_box()
            check('móvil: el marco ocupa el ancho', box['width'] >= 300, box)
            shot(ph, '06-movil-encuadre')
            ph.click('#mmc-m [data-modal-close]'); ph.wait_for_timeout(300)
            check('Cancelar no guarda nada', not list((tmp / 'uploads').glob('divetype_lagos_*')))
            enad = page_for(DESK, lang='en'); login(enad, 'admin', APW); go(enad, '#/admin?tab=divetypes', 2000)
            enad.locator('.mm-card[data-key="type:pilares"] .mm-file input').set_input_files(str(big)); enad.wait_for_selector('#mmc-m .mmc-frame img', timeout=8000); enad.wait_for_timeout(700)
            tx = enad.inner_text('#mmc-m')
            check('en inglés, la ventana del encuadre traducida', 'Encuadra' not in tx and 'Así se verá' not in tx and 'Guardar foto' not in tx, tx[:200])
            shot(enad, '07-encuadre-en-ingles')
            enad.click('#mmc-m [data-modal-close]')

            # 5 · «Restaurar original»
            ad.once('dialog', lambda d: d.accept())
            ad.click('.mm-card[data-key="type:canales"] .mm-reset'); ad.wait_for_timeout(1800)
            check('«Restaurar original»: Canales vuelve a «sin foto»', ad.locator('.mm-card[data-key="type:canales"] .mm-empty').count() == 1)
            check('y sus archivos se borran', not list((tmp / 'uploads').glob('divetype_canales_*')))
            check('sin errores en la consola', not errors, errors[:5])
            browser.close()
    finally:
        srv.stop()
    bad = [n for n, ok in rows if not ok]
    print(f'\n{len(rows) - len(bad)}/{len(rows)} comprobaciones correctas')
    return not bad


if __name__ == '__main__':
    sys.exit(0 if run(Path(sys.argv[1]) if len(sys.argv) > 1 else None) else 1)
