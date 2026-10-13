"""v50.51 · Recorrido en un navegador real: la ficha del punto como en v50.49, el carrusel sutil «Vida marina en esta
inmersión» con su bocadillo, el «Recorrido virtual» con los vídeos enlazados, el editor de la administración, las
propuestas de un centro y los 9 idiomas, en ordenador y en móvil.

Las plataformas de vídeo y Wikimedia Commons están simuladas (tests/media_mock.py): nada sale del ordenador, y el
navegador corta cualquier petición a otra web para comprobar que nada externo se carga antes de «Cargar vídeo».

    python tests/navegador/e2e_vida_marina.py [CARPETA_DE_CAPTURAS]
"""
from __future__ import annotations

import datetime as dt
import io
import statistics
import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
from helpers import Server, ServerTestCase  # noqa: E402
from media_mock import MediaMock, picture  # noqa: E402
from e2e_markers import ADMIN_REASON, chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
PW = 'buceo-seguro-2026'
LANG_CHECK = {   # title of the strip, «8 species», the octopus and «Habitual» (in the bubble) in each language
    'es': ('Vida marina en esta inmersión', '8 especies', 'Pulpo común', 'Habitual'), 'en': ('Marine life on this dive', '8 species', 'Common octopus', 'Common'),
    'fr': ('Vie marine de cette plongée', '8 espèces', 'Poulpe commun', 'Fréquente'), 'de': ('Meeresleben bei diesem Tauchgang', '8 Arten', 'Gemeiner Krake', 'Häufig'),
    'it': ('Vita marina in questa immersione', '8 specie', 'Polpo comune', 'Frequente'), 'pt': ('Vida marinha neste mergulho', '8 espécies', 'Polvo-comum', 'Habitual'),
    'nl': ('Zeeleven tijdens deze duik', '8 soorten', 'Gewone octopus', 'Vaak'), 'pl': ('Życie morskie podczas tego nurkowania', '8 gatunków', 'Ośmiornica zwyczajna', 'Częsty'),
    'zh': ('本次潜水可见的海洋生物', '8 个物种', '真蛸', '常见'),
}


def photo(i):
    from PIL import Image, ImageDraw
    im = Image.new('RGB', (1280, 960), (10 + i * 7 % 60, 70 + i * 13 % 90, 120 + i * 5 % 100))
    d = ImageDraw.Draw(im); d.ellipse((300, 280, 980, 680), fill=(230, 140 + i * 3 % 100, 60)); d.polygon([(980, 480), (1180, 330), (1180, 630)], fill=(200, 110, 50))
    out = io.BytesIO(); im.save(out, 'JPEG', quality=80); return out.getvalue()


def run(shots: Path | None):
    results = []

    def check(name, ok, detail=''):
        results.append((name, bool(ok))); print(('OK  ' if ok else 'MAL ') + name + ('' if ok else f'  → {detail}'), flush=True)

    mock = MediaMock()
    ServerTestCase.server = srv = Server({'WOD_MEDIA_FETCH_BASE': mock.base}).start()
    try:
        t = ServerTestCase('run'); t.server = srv
        admin = t.make_admin(); center = t.make_center(admin, 'marinae2e'); diver = t.make_diver('marinae2e')
        admin.post('/api/admin/marina/ejemplos')
        sp = {x['scientific']: x['id'] for x in admin.get('/api/admin/marina/especies').json['items']}
        month = dt.date.today().month
        off = lambda m: [x for x in m if x != month] or [((month + 5) % 12) + 1]          # months that never include today's
        PID, EMPTY, BIG = 5, 84, 85                                                        # Islas Medes, Carall Bernat, Tascons
        links = [('Epinephelus marginatus', 'common', []), ('Octopus vulgaris', 'common', []), ('Muraena helena', 'common', []),
                 ('Sphyraena sphyraena', 'occasional', []), ('Sepia officinalis', 'occasional', off([3, 4, 5, 6])), ('Hippocampus guttulatus', 'rare', []),
                 ('Mola mola', 'rare', off([5, 6, 7, 8])), ('Caretta caretta', 'rare', off([6, 7, 8, 9]))]
        for sci, f, m in links: admin.post('/api/marina/especie-punto', {'point_id': PID, 'species_id': sp[sci], 'frequency': f, 'months': m})
        vids = [('https://www.youtube.com/watch?v=Ab360Ef6hI9', '360', ''), ('https://vimeo.com/76979871', 'normal', 'Bajada por la pared norte'),
                ('https://www.twitch.tv/videos/123456789', 'normal', ''), ('https://www.youtube.com/watch?v=NOTHUMB0001', 'vr', 'Recorrido en realidad virtual')]
        for u, k, ti in vids: admin.post('/api/marina/video', {'point_id': PID, 'url': u, 'kind': k, 'title': ti})
        for i in range(30):   # a site with 30 species (smoothness on a phone)
            r = admin.upload('/api/admin/marina/especie', {'scientific_name': f'Pruebaspecies {chr(97 + i % 26)}{chr(97 + i // 26)}lata', 'texts': '{"es":{"name":"Especie %02d"}}' % i,
                                                           'photo_author': 'Pruebas', 'photo_license': 'Propia'}, 'p.jpg', photo(i))
            admin.post('/api/marina/especie-punto', {'point_id': BIG, 'species_id': r.json['id'], 'frequency': ('common', 'occasional', 'rare')[i % 3], 'months': []})
        base = srv.base

        with sync_playwright() as p:
            browser = chromium(p)
            DESK = {'viewport': {'width': 1366, 'height': 900}}
            PHONE = {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}

            def page_for(opts, lang='es-ES', reduced=None):
                ctx = browser.new_context(**opts, locale=lang, **({'reduced_motion': reduced} if reduced else {}))
                page = ctx.new_page(); page.outside = []; page.errors = []
                page.on('pageerror', lambda e: page.errors.append(str(e)))
                def route(r):
                    host = r.request.url.split('/')[2]
                    if host.startswith('127.0.0.1') or host.startswith('localhost'):   # same reason header as e2e_markers.chromium()
                        return r.continue_(headers={**r.request.headers, 'x-admin-reason': ADMIN_REASON})
                    if host == 'upload.wikimedia.org':   # Commons previews in the administration: the stand-in's pictures
                        return r.fulfill(body=picture(480, 360, 13), content_type='image/jpeg')
                    page.outside.append(r.request.url); return r.abort()
                page.route('**/*', route)
                return page

            def go(page, route, wait=1200):
                page.goto(base + '/' + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)
                page.evaluate("document.getElementById('ck-ok')?.click()")

            def shot(page, name, full=False, el=None):
                if not shots: return
                shots.mkdir(parents=True, exist_ok=True)
                if full:   # lazy images: walk the page first so every picture is there
                    h = page.evaluate('document.body.scrollHeight')
                    for y in range(0, h, 500): page.evaluate(f'window.scrollTo(0,{y})'); page.wait_for_timeout(60)
                    page.evaluate('window.scrollTo(0,0)'); page.wait_for_timeout(400)
                (page.locator(el) if el else page).screenshot(path=str(shots / f'{name}.jpg'), type='jpeg', quality=82, **({'full_page': True} if full and not el else {}))

            def login(page, user, pw=PW):
                go(page, '#/login', 600); page.fill('#login', user); page.fill('#password', pw); page.click('#login-form button[type=submit]'); page.wait_for_timeout(1500)

            sv = '#pm-viewport'
            offset = lambda page: page.evaluate("(() => { const m = getComputedStyle(document.getElementById('pm-track')).transform; return m === 'none' ? 0 : -new DOMMatrix(m).m41; })()")
            items = '#pm-track > li:not([data-copy]) .pm-item'
            virtual_block = '.pp-virtual-block'
            route_cards = f'{virtual_block} .pp-virtual:has(.rv-logo)'
            platforms = lambda page: [u for u in page.outside if 'tile.openstreetmap.org' not in u]   # the map's tiles are not video platforms

            # ------------------------------------------------------------------------- ficha del punto (ordenador)
            page = page_for(DESK)
            go(page, f'#/punto?id={PID}', 1500)
            order = page.evaluate("""() => { const y = e => e ? e.getBoundingClientRect().top + scrollY : null;
                const h2 = t => [...document.querySelectorAll('.tp-main h2')].find(h => h.textContent.trim() === t)?.closest('section');
                return [y(h2('Sobre el punto')), y(document.querySelector('.pm-block')), y(h2('Recorrido virtual')), y(document.getElementById('pp-centers'))]; }""")
            check('ficha · orden de v50.49: datos, vida marina justo encima del recorrido virtual, centros', None not in order and order[0] < order[1] < order[2] < order[3], order)
            gap = page.evaluate("(() => { const a = document.querySelector('.pm-block').getBoundingClientRect(), b = document.querySelector('.pm-block').nextElementSibling; return [b.querySelector('h2')?.textContent.trim(), b.getBoundingClientRect().top - a.bottom]; })()")
            check('ficha · el carrusel va pegado al «Recorrido virtual»', gap[0] == 'Recorrido virtual' and 0 <= gap[1] <= 40, gap)
            check('ficha · sin las secciones de v50.50 (carrusel grande y «Vídeos de la ruta»)', page.locator('.mv-block, .rv-block, .rv-card').count() == 0 and 'Vídeos de la ruta' not in page.inner_text('#app'))
            check('carrusel · título pequeño y número de especies', page.inner_text('.pm-title').strip() == 'Vida marina en esta inmersión' and page.inner_text('.pm-count').strip() == '8 especies'
                  and page.evaluate("parseFloat(getComputedStyle(document.querySelector('.pm-title')).fontSize) <= 15"))
            check('carrusel · 8 especies', page.locator(items).count() == 8, page.locator(items).count())
            size = page.evaluate("document.querySelector('.pm-photo').getBoundingClientRect().width")
            check('carrusel · fotos pequeñas y redondas (56–64 px en ordenador)', 56 <= size <= 64 and page.evaluate("getComputedStyle(document.querySelector('.pm-photo')).borderRadius") == '50%', size)
            names = page.evaluate(f"[...document.querySelectorAll('{items} .pm-name')].map(e => e.textContent)")
            check('carrusel · nombre común debajo de cada foto, en pequeño', len(names) == 8 and 'Pulpo común' in names and page.evaluate("parseFloat(getComputedStyle(document.querySelector('.pm-name')).fontSize) <= 12"), names)
            check('carrusel · primero las de temporada y habituales', names[0] in ('Mero', 'Morena', 'Pulpo común') and names[-1] in ('Pez luna', 'Tortuga boba', 'Sepia común'), names)
            check('carrusel · fotos WebP en dos tamaños con carga diferida', page.evaluate(f"[...document.querySelectorAll('{items} img')].every(i => i.loading === 'lazy' && i.srcset.split(',').length === 2 && /-128\\.webp 128w/.test(i.srcset) && /-640\\.webp 640w/.test(i.srcset))"))
            check('carrusel · quieto en el ordenador porque caben todas', page.get_attribute(sv, 'data-state') == 'still' and offset(page) == 0, page.get_attribute(sv, 'data-state'))
            shot(page, 'ordenador-carrusel', el='.pm-block')
            # bubble
            first = page.locator(items).first
            first.click(); page.wait_for_timeout(400)
            pop = page.locator('#pm-pop')
            check('bocadillo · se abre sin salir de la página', pop.count() == 1 and '#/punto' in page.url)
            geo = page.evaluate("""() => { const p = document.getElementById('pm-pop').getBoundingClientRect(), t = document.querySelector('.pm-item[aria-expanded=true]').getBoundingClientRect();
                return {gap: Math.min(Math.abs(p.top - t.bottom), Math.abs(t.top - p.bottom)), overlap: p.left < t.right && p.right > t.left, w: p.width,
                        img: document.querySelector('#pm-pop .pm-pop-photo img')?.getBoundingClientRect().width || 0}; }""")
            check('bocadillo · junto a la foto, con la foto más grande', geo['gap'] <= 20 and geo['overlap'] and geo['img'] >= 200, geo)
            body = pop.inner_text()
            check('bocadillo · nombre común, científico en cursiva, frecuencia, mejor época, información y crédito',
                  pop.locator('h3').inner_text().strip() == names[0] and pop.locator('.pm-pop-sci em').count() == 1 and pop.locator('.pm-freq').inner_text().strip() == 'Habitual'
                  and 'Mejor época' in body and pop.locator('.pm-pop-info').count() == 1 and pop.locator('.pm-pop-credit').count() == 1, body)
            check('bocadillo · accesible (diálogo con título, el foco va a «Cerrar»)', page.evaluate("document.activeElement.id") == 'pm-pop-x'
                  and pop.get_attribute('role') == 'dialog' and pop.get_attribute('aria-labelledby') == 'pm-pop-title' and first.get_attribute('aria-expanded') == 'true')
            shot(page, 'ordenador-bocadillo')
            page.locator(items).nth(1).click(); page.wait_for_timeout(400)
            check('bocadillo · solo uno abierto a la vez', page.locator('#pm-pop').count() == 1 and page.locator('#pm-pop h3').inner_text().strip() == names[1])
            page.keyboard.press('Escape'); page.wait_for_timeout(250)
            check('bocadillo · Esc lo cierra y el foco vuelve a la foto', page.locator('#pm-pop').count() == 0 and page.evaluate("document.activeElement.classList.contains('pm-item')"))
            page.locator(items).nth(2).click(); page.wait_for_timeout(300); page.mouse.click(5, 300); page.wait_for_timeout(250)
            check('bocadillo · se cierra tocando fuera', page.locator('#pm-pop').count() == 0)
            page.locator(items).nth(2).click(); page.wait_for_timeout(300); page.click('#pm-pop-x'); page.wait_for_timeout(250)
            check('bocadillo · se cierra con la X', page.locator('#pm-pop').count() == 0)
            page.locator(items).nth(3).focus(); page.keyboard.press('Enter'); page.wait_for_timeout(300)
            check('bocadillo · con el teclado (Intro abre)', page.locator('#pm-pop').count() == 1)
            page.keyboard.press('Tab'); page.keyboard.press('Tab'); page.keyboard.press('Tab'); page.wait_for_timeout(100)
            check('bocadillo · el foco no se escapa con Tab', page.evaluate("!!document.activeElement.closest('#pm-pop')"))
            page.keyboard.press('Escape')
            # recorrido virtual
            check('recorrido virtual · el aspecto de v50.49 (tarjetas con el cuadro de 58 px)', page.locator(f'{virtual_block} .pp-virtuals').count() == 1
                  and page.evaluate(f"""(() => {{ const r = document.querySelector('{route_cards} .pp-virtual-mark').getBoundingClientRect(); return r.width === 58 && r.height === 58; }})()"""))
            check('recorrido virtual · los 4 vídeos aprobados', page.locator(route_cards).count() == 4, page.locator(route_cards).count())
            thumbs = page.evaluate(f"""[...document.querySelectorAll("{route_cards} .pp-virtual-thumb img")].map(i => i.currentSrc || i.src)""")
            check('recorrido virtual · miniatura guardada en el servidor (WebP) dentro del cuadro', len(thumbs) == 3 and all('/assets/uploads/videos/' in x and x.endswith('.webp') for x in thumbs), thumbs)
            check('recorrido virtual · etiqueta 360° y VR', page.locator(f'{route_cards} .pp-virtual-mark b', has_text='360°').count() == 1 and page.locator(f'{route_cards} .pp-virtual-mark', has_text='VR').count() == 1)
            tw = page.locator(route_cards, has_text='Twitch')
            check('recorrido virtual · plataforma no insertable: «Abrir en Twitch» en pestaña nueva con icono externo',
                  tw.locator('a.btn[target=_blank][rel*=noopener]', has_text='Abrir en Twitch').count() == 1 and tw.locator('.rv-ext').count() == 1)
            check('recorrido virtual · logotipo de la plataforma y quién lo aportó', page.locator(f'{route_cards} .rv-logo svg').count() == 4 and 'Aportado por' in page.locator(route_cards).first.inner_text())
            check('recorrido virtual · nada de las plataformas se carga en la ficha', platforms(page) == [], platforms(page))
            shot(page, 'ordenador-recorrido-virtual', el=virtual_block)
            check('ficha · sin errores de JavaScript', not page.errors, page.errors)
            page.locator(route_cards, has_text='YouTube').filter(has=page.locator('.pp-virtual-mark b', has_text='360°')).locator('a.btn', has_text='Entrar en el recorrido').click(); page.wait_for_timeout(1200)
            check('recorrido virtual · «Entrar en el recorrido» abre el visor con el aviso y la miniatura de fondo', '#/virtual?video=' in page.url and page.locator('#virtual-consent.has-thumb').count() == 1 and platforms(page) == [])
            shot(page, 'ordenador-recorrido-aviso')
            page.click('#virtual-load'); page.wait_for_timeout(800)
            src = page.evaluate("document.querySelector('.virtual-frame iframe')?.src || ''")
            check('recorrido virtual · «Cargar vídeo» trae el reproductor de YouTube sin cookies', src.startswith('https://www.youtube-nocookie.com/embed/Ab360Ef6hI9'), src)
            check('recorrido virtual · solo entonces se pide algo a la plataforma', platforms(page) and all('youtube-nocookie.com' in u for u in platforms(page)), platforms(page))
            page.context.close()
            page = page_for(DESK); go(page, f'#/punto?id={PID}', 1500); shot(page, 'ordenador-ficha-punto-completa', full=True)
            page.locator(items).first.scroll_into_view_if_needed(); page.locator(items).first.click(); page.wait_for_timeout(500)
            shot(page, 'ordenador-ficha-con-bocadillo'); page.context.close()

            # ------------------------------------------------------------------------- 30 especies: se mueve, se para
            page = page_for(DESK)
            go(page, f'#/punto?id={BIG}', 1800); page.locator(sv).scroll_into_view_if_needed(); page.mouse.move(5, 5); page.wait_for_timeout(400)
            check('30 especies · se mueve solo porque no caben', page.get_attribute(sv, 'data-state') == 'moving')
            a = offset(page); page.wait_for_timeout(2000); b = offset(page)
            check('30 especies · movimiento lento y continuo (≈ 20 px/s)', 25 <= b - a <= 70, (a, b))
            mask = page.evaluate("getComputedStyle(document.getElementById('pm-viewport')).maskImage || getComputedStyle(document.getElementById('pm-viewport')).webkitMaskImage")
            check('30 especies · bordes difuminados', 'linear-gradient' in mask, mask)
            page.locator(sv).hover(); page.wait_for_timeout(300); a = offset(page); page.wait_for_timeout(1500)
            check('30 especies · se para con el ratón encima', offset(page) == a, (a, offset(page)))
            page.mouse.move(5, 5); page.wait_for_timeout(1200)
            check('30 especies · sigue al quitar el ratón', offset(page) != a)
            vis = page.evaluate("""(() => { const v = document.getElementById('pm-viewport').getBoundingClientRect();
                return [...document.querySelectorAll('#pm-track .pm-item')].findIndex(b => { const r = b.getBoundingClientRect(); return r.left > v.left + 50 && r.right < v.right - 50; }); })()""")
            bb = page.locator('#pm-track .pm-item').nth(vis).bounding_box()
            page.mouse.move(bb['x'] + bb['width'] / 2, bb['y'] + 20); page.wait_for_timeout(150); page.mouse.down(); page.mouse.up()   # as a person: the pointer stops it, then the click
            page.wait_for_timeout(200); page.mouse.move(5, 5); page.wait_for_timeout(200); a = offset(page); page.wait_for_timeout(1500)
            check('30 especies · se para con una especie abierta', page.locator('#pm-pop').count() == 1 and offset(page) == a, (a, offset(page)))
            page.keyboard.press('Escape'); page.mouse.move(5, 5)
            check('30 especies · las copias del bucle no se leen ni se enfocan', page.evaluate("[...document.querySelectorAll('#pm-track > li[data-copy]')].every(li => li.getAttribute('aria-hidden') === 'true' && li.querySelector('button').tabIndex === -1)"))
            check('30 especies · sin errores de JavaScript', not page.errors, page.errors)
            shot(page, 'ordenador-carrusel-30', el='.pm-block')
            page.context.close()

            # ------------------------------------------------------------------------- reducir movimiento
            page = page_for(DESK, reduced='reduce')
            go(page, f'#/punto?id={BIG}', 1800); page.locator(sv).scroll_into_view_if_needed(); page.mouse.move(5, 5)
            a = offset(page); page.wait_for_timeout(1500)
            check('reducir movimiento · quieto (se puede desplazar a mano)', page.get_attribute(sv, 'data-state') == 'scroll' and offset(page) == a == 0
                  and page.evaluate("(() => { const v = document.getElementById('pm-viewport'); v.scrollLeft = 200; return v.scrollLeft > 0; })()"))
            page.context.close()

            # ------------------------------------------------------------------------- punto sin especies
            page = page_for(DESK)
            go(page, f'#/punto?id={EMPTY}', 1500)
            txt = page.inner_text('#app')
            check('punto sin especies · el carrusel no aparece', page.locator('.pm-block').count() == 0 and 'Vida marina' not in txt)
            check('punto sin vídeos · «Recorrido virtual» como en v50.49', 'Recorrido virtual' in txt and page.locator('.pp-empty .pp-virtual-mark').count() == 1)
            page.context.close()

            # ------------------------------------------------------------------------- móvil
            page = page_for(PHONE)
            go(page, f'#/punto?id={PID}', 1500)
            check('móvil · nada más ancho que la pantalla', page.evaluate('document.scrollingElement.scrollWidth <= innerWidth + 1'), page.evaluate('document.scrollingElement.scrollWidth'))
            size = page.evaluate("document.querySelector('.pm-photo').getBoundingClientRect().width")
            check('móvil · fotos de 48–56 px', 48 <= size <= 56, size)
            page.locator(sv).scroll_into_view_if_needed(); page.wait_for_timeout(500)
            check('móvil · se mueve porque no caben', page.get_attribute(sv, 'data-state') == 'moving')
            box = page.locator(sv).bounding_box(); cdp = page.context.new_cdp_session(page)
            y = box['y'] + box['height'] / 2; x0 = box['x'] + box['width'] - 40
            a = offset(page)
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchStart', 'touchPoints': [{'x': x0, 'y': y}]})
            for k in range(1, 11): cdp.send('Input.dispatchTouchEvent', {'type': 'touchMove', 'touchPoints': [{'x': x0 - k * 18, 'y': y}]}); page.wait_for_timeout(16)
            cdp.send('Input.dispatchTouchEvent', {'type': 'touchEnd', 'touchPoints': []}); page.wait_for_timeout(100)
            moved = offset(page) - a
            check('móvil · se desliza con el dedo', moved > 120, moved)
            check('móvil · deslizar no abre ninguna especie', page.locator('#pm-pop').count() == 0)
            a = offset(page); page.wait_for_timeout(1500)
            check('móvil · se para un rato después de tocarlo', offset(page) == a, (a, offset(page)))
            shot(page, 'movil-carrusel', el='.pm-block')
            vis = page.evaluate("""(() => { const v = document.getElementById('pm-viewport').getBoundingClientRect();
                return [...document.querySelectorAll('#pm-track .pm-item')].findIndex(b => { const r = b.getBoundingClientRect(); return r.left > v.left + 30 && r.right < v.right - 30; }); })()""")
            page.locator('#pm-track .pm-item').nth(vis).tap(); page.wait_for_timeout(500)
            sheet = page.evaluate("(() => { const p = document.getElementById('pm-pop'); if (!p) return null; const r = p.getBoundingClientRect(); return {sheet: p.classList.contains('is-sheet'), bottom: Math.round(r.bottom), h: innerHeight, w: r.width}; })()")
            check('móvil · el bocadillo es un panel pequeño desde abajo', sheet and sheet['sheet'] and abs(sheet['bottom'] - sheet['h']) <= 1 and sheet['w'] >= 389, sheet)
            shot(page, 'movil-bocadillo')
            page.locator('#pm-backdrop').tap(position={'x': 30, 'y': 40}); page.wait_for_timeout(300)
            check('móvil · se cierra tocando fuera', page.locator('#pm-pop').count() == 0)
            shot(page, 'movil-ficha-punto-completa', full=True)
            page.context.close()
            page = page_for(PHONE); go(page, f'#/punto?id={PID}', 1500)
            page.locator(sv).scroll_into_view_if_needed(); page.wait_for_timeout(300)
            page.evaluate("document.querySelector('#pm-track .pm-item').click()"); page.wait_for_timeout(500)
            shot(page, 'movil-ficha-con-bocadillo')
            vid = page.evaluate(f"""document.querySelector("{route_cards} a.btn[href*='video=']").getAttribute('href')""")
            go(page, vid, 1200)
            check('móvil · el visor del recorrido ofrece «Abrir en la app de YouTube»', page.locator('.rv-app', has_text='Abrir en la app de YouTube').count() == 1)
            check('móvil · sin errores de JavaScript', not page.errors, page.errors)
            page.context.close()

            # ------------------------------------------------------------------------- 30 especies en un móvil lento
            page = page_for(PHONE)
            cdp = page.context.new_cdp_session(page); cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
            go(page, f'#/punto?id={BIG}', 2500); page.locator(sv).scroll_into_view_if_needed(); page.wait_for_timeout(500)
            check('30 especies en el móvil · las 30', page.locator(items).count() == 30)
            frames = page.evaluate("""() => new Promise(done => { const ts = []; let last = performance.now();
                const tick = now => { ts.push(now - last); last = now; if (ts.length < 150) requestAnimationFrame(tick); else done(ts.slice(5)); };
                requestAnimationFrame(tick); })""")
            p95 = sorted(frames)[int(len(frames) * .95)]; med = statistics.median(frames); long_ = sum(1 for f in frames if f > 50)
            print(f'   medida · 30 especies en movimiento, CPU 4× más lenta: fotograma mediano {med:.1f} ms, p95 {p95:.1f} ms, {long_} de {len(frames)} por encima de 50 ms', flush=True)
            check('30 especies en el móvil · movimiento fluido con la CPU 4× más lenta (p95 < 50 ms)', p95 < 50 and long_ <= len(frames) * .05, (med, p95, long_))
            page.context.close()

            # ------------------------------------------------------------------------- 9 idiomas
            for lang, (head, count, octo, freq) in LANG_CHECK.items():
                page = page_for(DESK)
                page.add_init_script("try{localStorage.setItem('wd-i18n-debug','1')}catch(e){}")
                go(page, f'?lang={lang}#/punto?id={PID}', 1800)
                h = page.inner_text('.pm-title').strip(); c = page.inner_text('.pm-count').strip(); names = page.inner_text('.pm-block')
                page.locator(items, has_text=octo).click(); page.wait_for_timeout(400)
                f = page.inner_text('#pm-pop .pm-freq').strip() if page.locator('#pm-pop').count() else ''
                misses = page.evaluate("""() => { const t = [...document.querySelectorAll('.pm-block, #pm-pop, .pp-virtuals')].map(e => e.innerText).join('\\n');
                                          return [...(window.__wdI18nMisses || [])].filter(m => t.includes(m)); }""")
                check(f'idioma {lang} · título, número, nombres y bocadillo', h == head and c == count and octo in names and f == freq and not misses, (h, c, f, misses))
                if lang in ('en', 'zh'): shot(page, f'ordenador-bocadillo-{lang}')
                page.context.close()

            # ------------------------------------------------------------------------- centro: proponer, administración: aprobar
            page = page_for(DESK)
            login(page, 'center_marinae2e'); go(page, '#/admin?tab=marina', 1800)
            check('centro · pestaña «Vídeos y vida marina» en su panel', page.locator('.cb-nav[data-cbtab="marina"]').count() == 1 and page.locator('.mk-panel').count() == 1)
            page.fill('#mk-pq', 'Medes'); page.wait_for_timeout(900)
            page.locator('#mk-pres .mk-point', has_text='Islas Medes, Costa Brava').click(); page.wait_for_timeout(1500)
            page.fill('#mk-url', 'https://youtu.be/hB3dEf6hI9k'); page.click('#mk-check'); page.wait_for_timeout(1500)
            check('centro · «Comprobar» trae el título y la miniatura', page.locator('.mk-prev img').count() == 1 and 'Ruta del pecio' in page.inner_text('.mk-prev'))
            page.fill('#mk-url', 'https://bit.ly/abc'); page.click('#mk-check'); page.wait_for_timeout(900)
            check('centro · enlace no válido: mensaje claro', 'enlace acortado' in page.inner_text('#mk-preview'), page.inner_text('#mk-preview'))
            page.fill('#mk-url', 'https://youtu.be/hB3dEf6hI9k'); page.click('#mk-vform button[type=submit]'); page.wait_for_timeout(1800)
            check('centro · su vídeo queda «Pendiente de aprobación»', page.locator('.mk-row', has_text='Ruta del pecio').locator('.status.warn').count() >= 1)
            go(page, '#/admin?tab=marina', 1800)
            check('centro · «Tus propuestas» con el estado', 'Pendiente de aprobación' in page.inner_text('.mk-panel'))
            shot(page, 'ordenador-panel-centro')
            pub = page_for(DESK); go(pub, f'#/punto?id={PID}', 1500)
            check('pendiente · no se publica hasta que lo apruebe la administración', 'Ruta del pecio' not in pub.inner_text('.pp-virtuals')); pub.context.close()
            page.context.close()

            page = page_for(DESK)
            login(page, 'admin', 'admin-seguro-2026'); go(page, '#/admin?tab=marina', 2000)
            check('administración · la propuesta en «Pendientes»', page.locator('.mk-row', has_text='Ruta del pecio').count() == 1)
            shot(page, 'ordenador-admin-pendientes')
            page.locator('.mk-row', has_text='Ruta del pecio').locator('button', has_text='Aprobar').click(); page.wait_for_timeout(1500)
            go(page, '#/admin?tab=marina&sub=especies', 1800)
            check('administración · catálogo con buscador en cualquier idioma', page.locator('.mk-table tbody tr').count() >= 46)
            page.fill('#mk-cq', 'krake'); page.wait_for_timeout(900)
            check('administración · «krake» (alemán) encuentra el pulpo', page.locator('.mk-table tbody tr').count() == 1 and 'Pulpo común' in page.inner_text('.mk-table'))
            page.locator('.mk-table button', has_text='Editar').click(); page.wait_for_timeout(900)
            check('administración · ficha de la especie con los 9 idiomas', page.locator('.mk-name-row').count() == 9)
            page.click('#mk-commons'); page.wait_for_timeout(1500)
            check('administración · Wikimedia Commons: fotos con autor y licencia; las no libres, marcadas', page.locator('.mk-cimg').count() == 4 and page.locator('.mk-cimg.is-no').count() == 2)
            shot(page, 'ordenador-admin-especie')
            page.click('#mk-sp-close')
            go(page, f'#/admin?tab=points&edit={PID}', 2500)
            check('administración · el editor del punto tiene vídeos y especies', page.locator('#marina-point-editor .mk-row').count() >= 13)
            shot(page, 'ordenador-admin-editor-punto', el='.mk-notice')
            page.context.close()

            page = page_for(DESK); go(page, f'#/punto?id={PID}', 1500)
            card = page.locator('.pp-virtual', has_text='Ruta del pecio')
            check('aprobado · ya se ve en la ficha con quién lo aportó', card.count() == 1 and 'Centro marinae2e' in card.inner_text())
            page.context.close()

            page = page_for(DESK)
            login(page, 'diver_marinae2e'); go(page, f'#/punto?id={PID}', 1500)
            check('buceador · no ve nada para añadir vídeos o especies', page.locator('#mk-vform, .mk-add, [data-cbtab="marina"]').count() == 0)
            page.context.close()
            browser.close()
    finally:
        srv.stop(); mock.stop()
    bad = [n for n, ok in results if not ok]
    print(f'\n{len(results) - len(bad)}/{len(results)} comprobaciones correctas')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(run(Path(sys.argv[1]) if len(sys.argv) > 1 else None))
