"""v50.50 · Recorrido en un navegador real: vida marina (carrusel) y vídeos de la ruta en la ficha del punto, el editor
de la administración, las propuestas de un centro y los 9 idiomas, en ordenador y en móvil.

Las plataformas de vídeo y Wikimedia Commons están simuladas (tests/media_mock.py): nada sale del ordenador, y el
navegador corta cualquier petición a otra web para comprobar que nada externo se carga antes de «Reproducir».

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
LANG_CHECK = {   # heading of the carousel, the octopus and «Habitual» in each language
    'es': ('Vida marina que puedes ver', 'Pulpo común', 'Habitual'), 'en': ('Marine life you can see', 'Common octopus', 'Common'),
    'fr': ('Vie marine à observer', 'Poulpe commun', 'Fréquente'), 'de': ('Meereslebewesen, die du sehen kannst', 'Gemeiner Krake', 'Häufig'),
    'it': ('Vita marina che puoi vedere', 'Polpo comune', 'Frequente'), 'pt': ('Vida marinha que pode ver', 'Polvo-comum', 'Habitual'),
    'nl': ('Zeeleven dat je kunt zien', 'Gewone octopus', 'Vaak'), 'pl': ('Życie morskie, które zobaczysz', 'Ośmiornica zwyczajna', 'Częsty'),
    'zh': ('可以看到的海洋生物', '真蛸', '常见'),
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

            sl = lambda page: page.evaluate("document.getElementById('mv-track').scrollLeft")

            # ------------------------------------------------------------------------- ficha del punto (ordenador)
            page = page_for(DESK)
            go(page, f'#/punto?id={PID}', 1500)
            order = page.evaluate("""() => { const y = s => { const e = document.querySelector(s); return e ? e.getBoundingClientRect().top + scrollY : null; };
                                      return [y('.mv-block'), y('.rv-block'), y('#pp-centers')]; }""")
            check('ficha · orden: datos, vida marina, vídeos, centros', None not in order and order[0] < order[1] < order[2], order)
            check('ficha · sin «Recorrido virtual» ni huecos de 360°', 'Recorrido virtual' not in page.inner_text('#app') and 'aún no tiene recorrido' not in page.inner_text('#app'))
            cards = page.locator('.mv-card')
            check('carrusel · 8 especies', cards.count() == 8, cards.count())
            first = page.evaluate("[...document.querySelectorAll('.mv-card')].map(c => [c.classList.contains('is-off'), c.querySelector('.mv-freq').textContent.trim()])")
            n_off = sum(1 for o, _ in first if o)
            check('carrusel · primero las habituales y de temporada; las de fuera de temporada al final', not first[0][0] and first[0][1] == 'Habitual'
                  and all(o for o, _ in first[-n_off:]) and n_off == 3, first)
            seasons = page.evaluate("[...document.querySelectorAll('.mv-card.is-off .mv-season')].map(e => e.textContent)")
            check('carrusel · «Mejor época: …» en las que no son de temporada', len(seasons) == 3 and all(s.startswith('Mejor época: ') and '–' in s for s in seasons), seasons)
            check('carrusel · nombres como texto (buscadores) y nombre científico', 'Pulpo común' in page.inner_text('.mv-block') and 'Octopus vulgaris' in page.inner_text('.mv-block'))
            check('carrusel · crédito de la foto sobre cada foto', page.locator('.mv-card .mv-credit').count() == 8)
            check('carrusel · fotos WebP con varios tamaños y carga diferida', page.evaluate("[...document.querySelectorAll('.mv-card img')].every(i => i.loading === 'lazy' && i.srcset.split(',').length === 3 && i.src.endsWith('.webp'))"))
            page.locator('#mv-track').scroll_into_view_if_needed(); page.mouse.move(5, 5); page.wait_for_timeout(300)
            a = sl(page); page.wait_for_timeout(6000); b = sl(page)
            check('carrusel · avanza solo, despacio', b > a, (a, b))
            page.locator('#mv-track').hover(); a = sl(page); page.wait_for_timeout(6000)
            check('carrusel · se para con el ratón encima', sl(page) == a, (a, sl(page)))
            page.mouse.move(5, 5)
            check('carrusel · flechas en el ordenador', page.locator('.mv-arrow').first.is_visible())
            page.evaluate("document.getElementById('mv-track').scrollTo({left:0,behavior:'auto'})"); page.wait_for_timeout(300)
            page.locator('.mv-arrow[data-dir="1"]').click(); page.wait_for_timeout(900)
            check('carrusel · la flecha avanza', sl(page) > 0, sl(page))
            shot(page, 'ordenador-carrusel', el='.mv-block')
            page.locator('.mv-card').first.click(); page.wait_for_timeout(500)
            modal = page.locator('#mv-modal')
            check('carrusel · al pulsar, ventana con la foto grande y la frase', modal.count() == 1 and modal.locator('.mv-blurb').count() == 1 and modal.locator('.mv-modal-photo img').count() == 1)
            shot(page, 'ordenador-especie')
            page.keyboard.press('Escape'); page.wait_for_timeout(300)
            check('carrusel · Escape cierra la ventana', page.locator('#mv-modal').count() == 0)
            # videos
            check('vídeos · 4 vídeos de la ruta', page.locator('.rv-card').count() == 4, page.locator('.rv-card').count())
            platforms = lambda: [u for u in page.outside if 'tile.openstreetmap.org' not in u]   # the map's tiles are not video platforms
            check('vídeos · nada de las plataformas se carga antes de «Reproducir»', platforms() == [], platforms())
            thumbs = page.evaluate("[...document.querySelectorAll('.rv-card img.rv-img:not(.rv-fallback)')].map(i => i.currentSrc || i.src)")
            check('vídeos · miniaturas guardadas en el servidor (WebP)', len(thumbs) == 3 and all('/assets/uploads/videos/' in x and x.endswith('.webp') for x in thumbs), thumbs)
            fb = page.locator('.rv-card', has=page.locator('.rv-fallback'))
            check('vídeos · sin miniatura: foto del punto, botón y nombre de la plataforma', fb.count() == 1 and fb.locator('.rv-play').count() == 1 and 'YouTube' in fb.locator('.rv-fb-name').inner_text())
            check('vídeos · etiqueta 360° y VR', page.locator('.rv-kind', has_text='360°').count() == 1 and page.locator('.rv-kind', has_text='VR').count() == 1)
            tw = page.locator('.rv-card', has_text='Twitch')
            check('vídeos · plataforma no insertable: pestaña nueva e icono de enlace externo',
                  tw.locator('a.rv-media[target=_blank][rel*=noopener]').count() == 1 and tw.locator('.rv-ext').count() == 1)
            check('vídeos · logotipo pequeño de la plataforma y quién lo aportó', page.locator('.rv-logo svg').count() == 4 and page.locator('.rv-by').first.inner_text().startswith('Aportado por'))
            shot(page, 'ordenador-videos', el='.rv-block')
            page.locator('.rv-media[data-play="0"]').click(); page.wait_for_timeout(800)
            src = page.evaluate("document.querySelector('.rv-frame')?.src || ''")
            check('vídeos · al pulsar se carga el reproductor de YouTube sin cookies', src.startswith('https://www.youtube-nocookie.com/embed/Ab360Ef6hI9'), src)
            check('vídeos · solo entonces se pide algo a la plataforma', platforms() and all('youtube-nocookie.com' in u for u in platforms()), platforms())
            check('ficha · sin errores de JavaScript', not page.errors, page.errors)
            page.context.close()
            page = page_for(DESK); go(page, f'#/punto?id={PID}', 1500); shot(page, 'ordenador-ficha-punto-completa', full=True)
            page.context.close()

            # ------------------------------------------------------------------------- reducir movimiento
            page = page_for(DESK, reduced='reduce')
            go(page, f'#/punto?id={PID}', 1500); page.locator('#mv-track').scroll_into_view_if_needed(); page.mouse.move(5, 5)
            a = sl(page); page.wait_for_timeout(6500)
            check('reducir movimiento · el carrusel no avanza solo', sl(page) == a and page.get_attribute('#mv-track', 'data-auto') == 'off', (a, sl(page)))
            page.context.close()

            # ------------------------------------------------------------------------- punto sin vídeos ni especies
            page = page_for(DESK)
            go(page, f'#/punto?id={EMPTY}', 1500)
            txt = page.inner_text('#app')
            check('punto vacío · no aparecen las secciones (ni «próximamente»)', page.locator('.mv-block, .rv-block').count() == 0 and 'próximamente' not in txt.lower()
                  and 'Vídeos de la ruta' not in txt and 'Vida marina' not in txt)
            page.context.close()

            # ------------------------------------------------------------------------- móvil
            page = page_for(PHONE)
            go(page, f'#/punto?id={PID}', 1500)
            check('móvil · nada más ancho que la pantalla', page.evaluate('document.scrollingElement.scrollWidth <= innerWidth + 1'), page.evaluate('document.scrollingElement.scrollWidth'))
            check('móvil · sin flechas (se desliza con el dedo)', not page.locator('.mv-arrow').first.is_visible())
            check('móvil · se ve que hay más tarjetas a la derecha', page.evaluate("(() => { const t = document.getElementById('mv-track'); return t.scrollWidth > t.clientWidth + 100; })()"))
            page.evaluate("document.getElementById('mv-track').scrollTo({left:300,behavior:'auto'})"); page.wait_for_timeout(300)
            check('móvil · el carrusel se desliza', sl(page) > 0)
            check('móvil · «Abrir en la app de YouTube»', page.locator('.rv-app', has_text='Abrir en la app de YouTube').count() == 2)
            shot(page, 'movil-carrusel', el='.mv-block'); shot(page, 'movil-videos', el='.rv-block')
            page.locator('.mv-card').nth(1).click(); page.wait_for_timeout(500); shot(page, 'movil-especie'); page.keyboard.press('Escape')
            shot(page, 'movil-ficha-punto-completa', full=True)
            page.context.close()

            # ------------------------------------------------------------------------- 30 especies en un móvil lento
            page = page_for(PHONE)
            cdp = page.context.new_cdp_session(page); cdp.send('Emulation.setCPUThrottlingRate', {'rate': 4})
            go(page, f'#/punto?id={BIG}', 2500)
            check('30 especies · las 30 tarjetas', page.locator('.mv-card').count() == 30)
            frames = page.evaluate("""() => new Promise(done => { const t = document.getElementById('mv-track'); const ts = []; let last = performance.now();
                const tick = now => { ts.push(now - last); last = now; if (ts.length < 150) requestAnimationFrame(tick); else done(ts.slice(5)); };
                requestAnimationFrame(tick); let x = 0; const step = () => { x += 9; t.scrollLeft = x; if (ts.length < 150) setTimeout(step, 16); }; step(); })""")
            p95 = sorted(frames)[int(len(frames) * .95)]; med = statistics.median(frames); long_ = sum(1 for f in frames if f > 50)
            print(f'   medida · 30 especies, CPU 4× más lenta: fotograma mediano {med:.1f} ms, p95 {p95:.1f} ms, {long_} de {len(frames)} por encima de 50 ms', flush=True)
            check('30 especies · desliza fluido en un móvil lento (p95 < 50 ms)', p95 < 50 and long_ <= len(frames) * .05, (med, p95, long_))
            shot(page, 'movil-30-especies', el='.mv-block')
            page.context.close()

            # ------------------------------------------------------------------------- 9 idiomas
            for lang, (head, octo, freq) in LANG_CHECK.items():
                page = page_for(DESK)
                page.add_init_script("try{localStorage.setItem('wd-i18n-debug','1')}catch(e){}")
                go(page, f'?lang={lang}#/punto?id={PID}', 1800)
                h = page.inner_text('#mv-title').strip(); names = page.inner_text('.mv-block')
                misses = page.evaluate("""() => { const t = [...document.querySelectorAll('.mv-block, .rv-block')].map(e => e.innerText).join('\\n');
                                          return [...(window.__wdI18nMisses || [])].filter(m => t.includes(m)); }""")
                check(f'idioma {lang} · título, nombres de las especies y etiquetas', h == head and octo in names and freq in names and not misses, (h, misses))
                if lang in ('en', 'zh'): shot(page, f'ordenador-carrusel-{lang}', el='.mv-block')
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
            check('pendiente · no se publica hasta que lo apruebe la administración', 'Ruta del pecio · hB3dEf6hI9k' not in pub.inner_text('.rv-block')); pub.context.close()
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
            card = page.locator('.rv-card', has_text='Ruta del pecio')
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
