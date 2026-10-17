#!/usr/bin/env python3
"""v50.58 · Vídeos de los puntos (encargo del 16/10/2026) en un navegador real (Chromium), sobre una copia de la demo.

Las plataformas están simuladas (tests/media_mock.py) y el navegador corta cualquier petición a otra web; las imágenes
de YouTube, TikTok e Instagram se sirven desde el simulador para ver las tarjetas como serán. Se comprueba:
- el bloque «Vídeos del punto» justo debajo de «Sobre el punto», con 1, 3 y 8 vídeos, horizontales y verticales;
- antes de pulsar, ninguna petición a las plataformas salvo la imagen; el reproductor (youtube-nocookie, TikTok,
  Instagram) solo al pulsar, en una ventana con ✕, Esc, fuera y flechas ‹ ›; a pantalla completa en el móvil;
- un buceador sin el perfil completo ve qué le falta; con él, envía un vídeo, se rechaza otra web y un repetido;
- un vídeo borrado en YouTube dice «Este vídeo ya no está disponible» y sale marcado en Administración;
- denunciar un vídeo lo lleva a «Denunciados» y «Retirar» lo quita de la ficha;
- consola sin errores de JavaScript.
Capturas en docs/capturas/v50.58/videos/despues (ordenador 1440 y móvil 390; web y modo app «Noche»).

    python3 tests/navegador/e2e_v50_58_videos.py [CARPETA_DE_CAPTURAS]

Crea sus propias cuentas en una copia temporal del catálogo (como e2e_vida_marina.py): no usa las cuentas de la demo."""
from __future__ import annotations

import sys
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Server, ServerTestCase  # noqa: E402
from media_mock import MediaMock  # noqa: E402
from e2e_markers import ADMIN_REASON, chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from wod import costa  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
YT = 'https://www.youtube.com/watch?v='
PLATFORMS = ('youtube.com', 'youtube-nocookie.com', 'youtu.be', 'tiktok.com', 'instagram.com', 'ytimg.com', 'tiktokcdn', 'cdninstagram')
IMAGES = ('i.ytimg.com', 'tiktokcdn', 'cdninstagram')


def run(shots: Path | None):
    results = []

    def check(name, ok, detail=''):
        results.append((name, bool(ok))); print(('OK  ' if ok else 'MAL ') + name + ('' if ok else f'  → {detail}'), flush=True)

    mock = MediaMock()
    ServerTestCase.server = srv = Server({'WOD_MEDIA_FETCH_BASE': mock.base, 'WOD_VIDEO_CHECKS': '0'}).start()
    try:
        t = ServerTestCase('run'); t.server = srv
        admin = t.make_admin(); diver = t.make_diver('vide2e')
        sea = [r for r in srv.sql("SELECT id,latitude,longitude FROM dive_points WHERE country='España' AND active=1 ORDER BY id")
               if (c := costa.check(r['latitude'], r['longitude'])) and not c['land']]
        def point(name, i):
            r = admin.post('/api/dive-points', {'name': name, 'country': 'España', 'region': 'Prueba', 'dive_type': 'Arrecifes', 'force_new': True,
                                                'latitude': sea[i]['latitude'] + 0.02, 'longitude': sea[i]['longitude'] + 0.02, 'force_position': True,
                                                'description': 'Ficha de prueba para ver el bloque de vídeos.'})
            assert r.status == 200, r.json
            return r.json['id']
        P1, P3, P8 = point('El Rincón del Buzo (copia de prueba)', 0), point('Punto con tres vídeos (prueba)', 1), point('Punto con ocho vídeos (prueba)', 2)
        def video(pid, url, **kw):
            r = admin.post(f'/api/dive-points/{pid}/videos', {'url': url, **kw}); assert r.status == 200, (url, r.json); return r.json['id']
        video(P1, YT + 'Rb7xK2mQ9aZ', title='El Rincón del Buzo')
        video(P3, YT + 'Tr1dEf6hI9k', title='Bajada por la pared'); video(P3, 'https://www.youtube.com/shorts/SHo3tEf6hI9', title='Short del pecio')
        video(P3, 'https://www.tiktok.com/@buceo/video/7234567890123456789', title='Tortuga en la Restinga')
        eight = [YT + 'Ei1dEf6hI9k', YT + 'hE2dEf6hI9k', 'https://www.youtube.com/shorts/SHe3dEf6hI9', YT + 'Ei4dEf6hI9k', 'https://www.tiktok.com/@buceo/video/7234567890123456700',
                 'https://www.instagram.com/reel/Cxyz12345/', YT + 'Ei7360f6hI9', YT + 'Ei8dEf6hI9k']
        for n, u in enumerate(eight): video(P8, u, title=f'Vídeo {n + 1} del punto', **({'kind': '360'} if '360' in u else {}))
        base = srv.base

        with sync_playwright() as p:
            browser = chromium(p)
            DESK = {'viewport': {'width': 1440, 'height': 900}}
            PHONE = {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}

            def page_for(opts, theme=None):
                ctx = browser.new_context(**opts, locale='es-ES'); page = ctx.new_page(); page.outside = []; page.errors = []
                page.on('pageerror', lambda e: page.errors.append(str(e)))
                if theme: page.add_init_script(f"try{{localStorage.setItem('wda-tema','{theme}')}}catch(e){{}}")
                def route(r):
                    url = r.request.url; host = url.split('/')[2]
                    if host.startswith('127.0.0.1') or host.startswith('localhost'):
                        return r.continue_(headers={**r.request.headers, 'x-admin-reason': ADMIN_REASON})
                    page.outside.append(url)
                    if any(h in host for h in IMAGES):   # the platforms' images, from the stand-in
                        code, body, ctype, _ = mock.answer(url)
                        return r.fulfill(status=code, body=body, content_type=ctype)
                    return r.abort()
                page.route('**/*', route)
                return page

            def go(page, route, wait=1400, app=False):
                page.goto(base + '/' + ('?app=1' if app else '') + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)
                page.evaluate("document.getElementById('ck-ok')?.click()")

            def shot(page, name, el=None):
                if not shots: return
                shots.mkdir(parents=True, exist_ok=True)
                if el: page.locator(el).scroll_into_view_if_needed(); page.wait_for_timeout(300)
                (page.locator(el) if el else page).screenshot(path=str(shots / f'{name}.png'))

            players = lambda page: [u for u in page.outside if any(h in u for h in PLATFORMS) and not any(h in u for h in IMAGES)]

            # ------------------------------------------------------------------ the dive site with one video
            for dev, opts in (('ordenador-1440', DESK), ('movil-390', PHONE)):
                for theme, app in (('clasico', False), ('noche-app', True)):
                    page = page_for(opts, 'noche' if app else None)
                    go(page, f'#/punto?id={P1}', app=app)
                    if dev == 'ordenador-1440' and not app:
                        order = page.evaluate("""() => { const y = s => { const e = document.querySelector(s); return e ? e.getBoundingClientRect().top + scrollY : null; };
                            return [y('#pp-about'), y('#pp-videos'), y('#pp-where')]; }""")
                        check('ficha · «Vídeos del punto» justo debajo de «Sobre el punto»', None not in order and order == sorted(order)
                              and page.evaluate("document.querySelector('#pp-about').nextElementSibling?.id === 'pp-videos'"), order)
                        txt = page.inner_text('#pp-videos')
                        check('ficha · título «Vídeos del punto», sin «Aportado por», sin «Entrar en el recorrido» ni «RUTA NORMAL»',
                              'Vídeos del punto' in txt and 'Aportado por' not in txt and 'Entrar en el recorrido' not in txt and 'RUTA NORMAL' not in txt.upper().replace('VÍDEOS', ''), txt)
                        geo = page.evaluate("""() => { const b = document.querySelector('#pp-videos').getBoundingClientRect(), c = document.querySelector('.pv-card.is-big').getBoundingClientRect(),
                            pl = document.querySelector('.pv-card.is-big .pv-play').getBoundingClientRect();
                            return {w: c.width, bw: b.width, ratio: c.width / c.height, cx: Math.abs((pl.left + pl.width / 2) - (c.left + c.width / 2)), cy: Math.abs((pl.top + pl.height / 2) - (c.top + c.height / 2)),
                                    radius: getComputedStyle(document.querySelector('.pv-card.is-big')).borderTopLeftRadius, shadow: getComputedStyle(document.querySelector('.pv-card.is-big')).boxShadow}; }""")
                        check('un vídeo · imagen a todo el ancho, 16:9, esquinas redondeadas y sombra', abs(geo['w'] - geo['bw']) < 2 and abs(geo['ratio'] - 16 / 9) < .03
                              and geo['radius'] != '0px' and geo['shadow'] != 'none', geo)
                        check('un vídeo · botón de reproducir en el centro', geo['cx'] < 2 and geo['cy'] < 2, geo)
                        check('un vídeo · título en blanco abajo con el icono de la plataforma', page.inner_text('.pv-card.is-big .pv-title').strip() == 'El Rincón del Buzo'
                              and page.locator('.pv-card.is-big .pv-logo svg').count() == 1 and page.evaluate("getComputedStyle(document.querySelector('.pv-card.is-big .pv-title')).color") == 'rgb(255, 255, 255)')
                        img = page.evaluate("document.querySelector('.pv-card.is-big img').currentSrc")
                        check('un vídeo · imagen oficial de la plataforma en la mayor calidad (maxresdefault)', img == 'https://i.ytimg.com/vi/Rb7xK2mQ9aZ/maxresdefault.jpg', img)
                        check('antes de pulsar · ninguna petición a la plataforma salvo la imagen', not players(page), players(page))
                        page.hover('.pv-card.is-big'); page.wait_for_timeout(350)
                        grow = page.evaluate("getComputedStyle(document.querySelector('.pv-card.is-big .pv-play')).transform")
                        check('un vídeo · el botón crece un poco al pasar el ratón', 'matrix(1.1' in grow, grow)
                        page.mouse.move(5, 5)
                    shot(page, f'ficha-un-video-{dev}-{theme}', el='#pp-videos')
                    if dev == 'movil-390' and not app:
                        page.locator('.pv-card.is-big').click(); page.wait_for_timeout(600)
                        box = page.evaluate("(() => { const b = document.querySelector('.pv-m-box').getBoundingClientRect(); return [b.width, b.height, innerWidth, innerHeight]; })()")
                        check('móvil · la ventana del vídeo ocupa toda la pantalla', abs(box[0] - box[2]) < 2 and abs(box[1] - box[3]) < 2, box)
                        shot(page, 'reproductor-movil-390')
                        page.keyboard.press('Escape'); page.wait_for_timeout(300)
                    check(f'consola sin errores · {dev} {theme}', not page.errors, page.errors)
                    page.context.close()

            # ------------------------------------------------------------------ playing: window, Esc, outside, arrows
            page = page_for(DESK)
            go(page, f'#/punto?id={P3}')
            check('tres vídeos · el primero en grande y los demás en la fila', page.locator('.pv-feature .pv-card').count() == 1 and page.locator('.pv-row .pv-card').count() == 2)
            check('tres vídeos · los verticales (Short y TikTok) en tarjetas 9:16', page.evaluate("""[...document.querySelectorAll('.pv-row .pv-card.is-vertical .pv-img')].map(e => { const r = e.getBoundingClientRect(); return Math.abs(r.width / r.height - 9 / 16) < .03; })""") == [True, True])
            shot(page, 'ficha-tres-videos-ordenador-1440', el='#pp-videos')
            before = list(page.outside)
            page.locator('.pv-card.is-big').click(); page.wait_for_timeout(700)
            src = page.get_attribute('#pv-m-frame iframe', 'src') or ''
            check('reproducir · ventana grande con el reproductor oficial (youtube-nocookie)', page.locator('#pv-modal').count() == 1 and src.startswith('https://www.youtube-nocookie.com/embed/Tr1dEf6hI9k'), src)
            check('reproducir · el reproductor se carga solo al pulsar', not [u for u in before if 'nocookie' in u] and any('youtube-nocookie.com' in u for u in page.outside))
            check('reproducir · la primera vez, la línea de cookies de YouTube, Instagram o TikTok', page.is_visible('#pv-m-note') and 'pueden usar cookies' in page.inner_text('#pv-m-note'))
            shot(page, 'reproductor-ordenador-1440')
            page.click('.pv-m-next'); page.wait_for_timeout(400)
            check('reproducir · ‹ › pasan al siguiente sin cerrar', (page.get_attribute('#pv-m-frame iframe', 'src') or '').startswith('https://www.youtube-nocookie.com/embed/SHo3tEf6hI9') and page.locator('#pv-modal .pv-m-box.is-vertical').count() == 1)
            page.keyboard.press('ArrowRight'); page.wait_for_timeout(400)
            check('reproducir · TikTok con su reproductor oficial', (page.get_attribute('#pv-m-frame iframe', 'src') or '').startswith('https://www.tiktok.com/player/v1/'))
            page.keyboard.press('Escape'); page.wait_for_timeout(300)
            check('reproducir · se cierra con Esc', page.locator('#pv-modal').count() == 0)
            page.locator('.pv-row .pv-card').first.click(); page.wait_for_timeout(400)
            page.mouse.click(10, 450); page.wait_for_timeout(300)
            check('reproducir · una miniatura se reproduce y la ventana se cierra tocando fuera', page.locator('#pv-modal').count() == 0)
            page.locator('.pv-card.is-big').click(); page.wait_for_timeout(300); page.click('.pv-m-x'); page.wait_for_timeout(300)
            check('reproducir · se cierra con ✕', page.locator('#pv-modal').count() == 0)
            page.locator('.pv-card.is-big').click(); page.wait_for_timeout(300)
            check('reproducir · la línea de cookies solo la primera vez', not page.is_visible('#pv-m-note'))
            page.keyboard.press('Escape')
            check('consola sin errores · reproducir', not page.errors, page.errors)
            page.context.close()

            for dev, opts in (('ordenador-1440', DESK), ('movil-390', PHONE)):
                page = page_for(opts); go(page, f'#/punto?id={P8}', 2000)
                n = page.locator('#pp-videos .pv-card').count()
                check(f'ocho vídeos · {dev}: uno grande y siete en la fila deslizable', n == 8 and page.evaluate("getComputedStyle(document.querySelector('.pv-row')).overflowX") == 'auto', n)
                ig = page.locator('.pv-card:has(.pv-see)')
                check(f'ocho vídeos · Instagram sin clave de Meta: foto del punto con «Ver en Instagram»', ig.count() == 1 and 'Ver en Instagram' in ig.inner_text())
                hq = page.evaluate("[...document.querySelectorAll('.pv-card img')].find(i => i.currentSrc.includes('hE2dEf6hI9k'))?.currentSrc || ''")
                check(f'ocho vídeos · sin maxresdefault se usa hqdefault', hq.endswith('/hqdefault.jpg'), hq)
                check(f'ocho vídeos · la etiqueta 360° encima de su imagen', page.locator('.pv-card .pv-tag', has_text='360°').count() == 1)
                check(f'ocho vídeos · nada se sale de la pantalla', page.evaluate('document.documentElement.scrollWidth <= innerWidth + 1'))
                shot(page, f'ficha-ocho-videos-{dev}', el='#pp-videos')
                check(f'consola sin errores · ocho vídeos {dev}', not page.errors, page.errors)
                page.context.close()

            # ------------------------------------------------------------------ a diver sends a video
            page = page_for(DESK)
            go(page, '#/login', 600); page.fill('#login', 'diver_vide2e'); page.fill('#password', 'buceo-seguro-2026'); page.click('#login-form button[type=submit]'); page.wait_for_timeout(1500)
            go(page, f'#/punto?id={P1}')
            page.click('#pv-add-btn'); page.wait_for_selector('.pv-missing', timeout=8000)
            miss = page.inner_text('.pv-missing')
            check('buceador sin el perfil completo · ve qué le falta', 'Confirmar tu correo' in miss and 'Tu país' in miss and 'certificación' in miss, miss)
            shot(page, 'anadir-falta-perfil', el='#pp-videos')
            srv.sql("UPDATE users SET email_verified_at=datetime('now') WHERE id=?", (diver.user['id'],))
            cert = srv.sql('SELECT id FROM certifications ORDER BY id LIMIT 1')[0]['id']
            diver.post('/api/account/profile', {'country': 'España', 'city': 'Valencia', 'certification_id': cert, 'preferred_language': 'es'})
            page.reload(); page.wait_for_load_state('networkidle'); page.wait_for_timeout(1200)
            page.click('#pv-add-btn'); page.wait_for_selector('#pv-add-form', timeout=8000)
            shot(page, 'anadir-formulario', el='#pp-videos')
            page.fill('#pv-url', 'https://vimeo.com/76979871'); page.check('#pv-own'); page.click('#pv-add-form button[type=submit]'); page.wait_for_timeout(800)
            check('enviar · un enlace de otra web se rechaza', 'Solo se admiten' in page.inner_text('#pv-err'), page.inner_text('#pv-err'))
            page.fill('#pv-url', YT + 'Rb7xK2mQ9aZ'); page.click('#pv-add-form button[type=submit]'); page.wait_for_timeout(800)
            check('enviar · un vídeo repetido se avisa', 'ya está en este punto' in page.inner_text('#pv-err'), page.inner_text('#pv-err'))
            page.fill('#pv-url', YT + 'Nw1dEf6hI9k'); page.fill('#pv-vtitle', 'Mi primera inmersión aquí'); page.click('#pv-add-form button[type=submit]'); page.wait_for_timeout(1000)
            check('enviar · un enlace válido: «Gracias. Lo revisaremos antes de publicarlo»', 'Gracias. Lo revisaremos antes de publicarlo' in page.inner_text('#pp-videos'))
            shot(page, 'anadir-gracias', el='#pp-videos')
            # report a published video
            page.locator('.pv-card.is-big').click(); page.wait_for_timeout(400); page.click('#pv-m-report'); page.wait_for_selector('#rpm-reason', timeout=6000)
            opts_ = page.eval_on_selector_all('#rpm-reason option', 'o => o.map(x => x.textContent)')
            check('denunciar · los tres motivos de un vídeo', opts_[1:] == ['No es de este punto', 'Contenido inadecuado', 'Es mío y no di permiso'], opts_)
            page.select_option('#rpm-reason', 'not_mine'); page.check('#rpm-faith'); page.click('#rpm-send'); page.wait_for_timeout(900)
            check('consola sin errores · buceador', not page.errors, page.errors)
            page.context.close()

            # ------------------------------------------------------------------ the administration
            page = page_for(DESK)
            go(page, '#/login', 600); page.fill('#login', 'admin'); page.fill('#password', 'admin-seguro-2026'); page.click('#login-form button[type=submit]'); page.wait_for_timeout(1500)
            go(page, '#/admin?tab=pointvideos', 1800)
            badge = page.inner_text('.cb-sidebar .cb-nav[data-tab="pointvideos"]')
            check('admin · «Vídeos de puntos» en el menú con su contador', 'Vídeos de puntos' in badge and any(ch.isdigit() for ch in badge), badge)
            check('admin · el pendiente con su imagen, el punto, quién lo envió y la plataforma', page.locator('.av-item').count() == 1 and 'Buceador vide2e' in page.inner_text('.av-item')
                  and 'YouTube' in page.inner_text('.av-item') and page.locator('.av-item .av-thumb img').count() == 1)
            shot(page, 'admin-pendientes')
            page.click('.av-item .av-thumb'); page.wait_for_timeout(400)
            check('admin · se ve el vídeo sin salir del panel', page.locator('#pv-modal iframe').count() == 1); page.keyboard.press('Escape')
            page.click('.av-item .av-ok'); page.wait_for_timeout(900)
            page.click('.av-tab[data-tab="reported"]'); page.wait_for_timeout(900)
            check('admin · el vídeo denunciado está en «Denunciados» con su motivo', page.locator('.av-item').count() == 1 and 'Es mío y no di permiso' in page.inner_text('.av-item'))
            shot(page, 'admin-denunciados')
            page.click('.av-item .av-take'); page.wait_for_timeout(900)
            page.click('.av-tab[data-tab="published"]'); page.wait_for_timeout(900)
            shot(page, 'admin-publicados')
            check('admin · publicados por punto, con flechas y arrastrar', page.locator('.av-group').count() >= 3 and page.locator('.av-item[draggable="true"]').count() >= 10)
            check('consola sin errores · administración', not page.errors, page.errors)
            page.context.close()
            pub = admin.get(f'/api/dive-points/{P1}').json['videos']
            check('retirar · el vídeo denunciado ya no está en la ficha', [v['title'] for v in pub] == ['Mi primera inmersión aquí'], [v['title'] for v in pub])

            # ------------------------------------------------------------------ a video deleted on YouTube
            gone = video(P3, YT + 'Gx1dEf6hI9k', title='Vídeo que se borrará')
            srv.sql("UPDATE route_videos SET url=?, video_ref='GONEdEf6hI9' WHERE id=?", (YT + 'GONEdEf6hI9', gone))
            page = page_for(DESK)
            real_answer = mock.answer
            mock.answer = lambda url: (404, b'', 'text/plain', None) if 'GONE' in url and 'i.ytimg.com' in url else real_answer(url)
            go(page, f'#/punto?id={P3}', 2500); page.wait_for_timeout(1500)
            card = page.locator('.pv-card.is-gone')
            check('vídeo borrado · «Este vídeo ya no está disponible»', card.count() == 1 and 'Este vídeo ya no está disponible' in card.inner_text(), page.locator('.pv-card').count())
            shot(page, 'video-no-disponible', el='#pp-videos')
            mock.answer = real_answer
            page.context.close()
            item = [x for x in admin.get('/api/admin/videos?tab=published').json['items'] if x['id'] == gone]
            check('vídeo borrado · marcado en Administración', item and item[0]['unavailable'] and 'borrado' in item[0]['unavailable_reason'], item)
            browser.close()
    finally:
        srv.stop(); mock.stop()
    bad = [n for n, ok in results if not ok]
    print(f'\n{len(results) - len(bad)}/{len(results)} comprobaciones correctas')
    return not bad


if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'docs' / 'capturas' / 'v50.58' / 'videos' / 'despues'
    sys.exit(0 if run(out) else 1)
