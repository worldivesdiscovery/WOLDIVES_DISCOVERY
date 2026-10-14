#!/usr/bin/env python3
"""v50.53 · recorrido en un navegador real (Chromium) sobre la base de la VERSIÓN DE DEMOSTRACIÓN, con capturas:

1. Top 10 y «Puntos de buceo» con la ubicación permitida (Madrid, Valencia, Canarias simuladas), denegada, sin
   respuesta (se rinde a los 8 s) y denegada antes (no vuelve a preguntar); lista y mapa con los mismos puntos y en el
   mismo orden; búsqueda «Hawaii» en Puntos y en Explorar.
2. El buscador: sin el «circulito» del navegador, con nuestra «×» solo cuando hay texto.
3. Ficha del centro a 360 px y en ordenador: títulos de 1–2 líneas a todo el ancho; precio y «Reservar» debajo en el
   móvil; «Puntos de buceo del centro»; reseñas 3 + «Ver más reseñas» (5 más sin recargar).
4. Tarjetas con foto: contraste AA medido en píxeles en claro (web) y oscuro (modo app «Noche»); la foto de una
   plantilla cambia al momento en la web y en el modo app, la foto propia no; flujo de foto como centro (casilla de
   derechos, vista previa clara y oscura, «Volver a la foto de la plantilla») y como administración (intensidad de la
   capa, retirar una foto propia).
5. Sin «Profundidad habitual»; cada rol solo ve lo suyo; consola sin errores en todas las páginas tocadas.

    python3 tests/navegador/e2e_v50_53.py [carpeta-de-capturas]

Solo hay Chromium en este entorno: Firefox y Safari de iPhone se comprueban a mano en dispositivos reales.
"""
from __future__ import annotations

import io
import re
import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Client, Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from PIL import Image  # noqa: E402
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'scripts'))
from crear_demo import ACCOUNTS, DATA, PASSWORD  # noqa: E402

PLACES = {'madrid': (40.4168, -3.7038), 'valencia': (39.4699, -0.3763), 'canarias': (28.4636, -16.2518)}
# A browser that never answers (neither allows nor denies): the page must give up after 8 s.
NEVER = "Object.defineProperty(navigator,'geolocation',{value:{getCurrentPosition(){window.__geoAsked=(window.__geoAsked||0)+1},watchPosition(){return 1},clearWatch(){}}});" \
        "const q=navigator.permissions.query.bind(navigator.permissions);navigator.permissions.query=d=>d&&d.name==='geolocation'?Promise.resolve({state:'prompt',onchange:null}):q(d);"
COUNT_ASKS = "const g=navigator.geolocation.getCurrentPosition.bind(navigator.geolocation);navigator.geolocation.getCurrentPosition=(...a)=>{window.__geoAsked=(window.__geoAsked||0)+1;return g(...a)};"
LONG_TITLES = ['Curso Open Water Diver 3 días', 'Curso Advanced Open Water 2 días', 'Doble inmersión con barco', 'Especialidad Nitrox (EANx)']
TEXT_SEL = '.svc2-title, .svc2-kicker, .svc2-desc, .svc2-price strong'


def lum(c):
    def ch(v):
        v /= 255
        return v / 12.92 if v <= 0.03928 else ((v + 0.055) / 1.055) ** 2.4
    return 0.2126 * ch(c[0]) + 0.7152 * ch(c[1]) + 0.0722 * ch(c[2])


def ratio(a, b):
    la, lb = sorted((lum(a), lum(b)), reverse=True)
    return (la + 0.05) / (lb + 0.05)


def card_contrast(page, card):
    """Lowest contrast between each text of a card and the photo + veil right behind it (99.5 % of the pixels), measured
    on a screenshot of the card's area with its texts made transparent. The card is brought into view first (in the
    app's horizontal carousel it may be half outside the screen)."""
    card.evaluate("c=>c.scrollIntoView({block:'center',inline:'start',behavior:'instant'})"); page.wait_for_timeout(500)
    info = card.evaluate(f"""c=>{{const cr=c.getBoundingClientRect();return {{card:{{x:cr.left,y:cr.top,width:cr.width,height:cr.height}},
        boxes:[...c.querySelectorAll('{TEXT_SEL}')].filter(e=>e.offsetParent&&e.textContent.trim()).map(e=>{{const r=e.getBoundingClientRect();
        return {{color:getComputedStyle(e).color,x:r.left-cr.left,y:r.top-cr.top,w:r.width,h:r.height}}}})}}}}""")
    dpr = page.evaluate('devicePixelRatio')
    card.evaluate("c=>{c.dataset.e2eColor='1';const s=document.createElement('style');s.id='e2e-hide';s.textContent='[data-e2e-color] *{color:transparent!important;text-shadow:none!important}';document.head.append(s)}")
    shot = Image.open(io.BytesIO(page.screenshot(clip=info['card']))).convert('RGB')
    card.evaluate("c=>{delete c.dataset.e2eColor;document.getElementById('e2e-hide')?.remove()}")
    worst = 99.0
    for b in info['boxes']:
        rgb = tuple(int(float(x)) for x in re.findall(r'[\d.]+', b['color'])[:3])
        crop = shot.crop((int(b['x'] * dpr), int(b['y'] * dpr), int((b['x'] + b['w']) * dpr), int((b['y'] + b['h']) * dpr)))
        px = list(crop.get_flattened_data() if hasattr(crop, 'get_flattened_data') else crop.getdata())[::3]
        if not px: continue
        rs = sorted(ratio(rgb, q) for q in px)
        worst = min(worst, rs[int(len(rs) * 0.005)])
    return round(worst, 2)


def photo_file(name):
    return (ROOT / 'public' / 'img' / name).read_bytes()


def run(shots: Path | None):
    results = []

    def check(name, ok, detail=''):
        results.append((name, bool(ok), detail)); print(('OK    ' if ok else 'FALLO ') + name + ('' if ok else f'  → {detail}'), flush=True)

    tmp = Path(tempfile.mkdtemp(prefix='wod-v5053-')) / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(tmp)], capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stdout + r.stderr)
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=tmp).start()
    base = srv.base
    try:
        admin = Client(srv); admin.login(ACCOUNTS['admin'][0], PASSWORD)
        center = Client(srv); center.login(ACCOUNTS['center'][0], PASSWORD)
        tpl = {t['slug']: t['id'] for t in admin.get('/api/admin/service-catalog').json['items']}
        cid = srv.sql('SELECT id FROM centers WHERE name=?', (DATA['bahia']['name'],))[0]['id']

        def wait_ready(table, oid):
            for _ in range(200):
                st = srv.sql(f'SELECT photo_status,photo_base FROM {table} WHERE id=?', (oid,))[0]
                if not str(st['photo_status'] or '').startswith('processing'): return st
                time.sleep(0.1)
            return st

        # Demo services linked to their templates (crear_demo) and the four titles of the review on Bahía Coralina.
        linked = srv.sql('SELECT COUNT(*) AS n FROM provider_services WHERE template_id IS NOT NULL')[0]['n']
        total = srv.sql('SELECT COUNT(*) AS n FROM provider_services')[0]['n']
        check(f'demo: servicios vinculados a su plantilla ({linked}/{total})', linked >= total - 1, (linked, total))
        svc = srv.sql('SELECT id,title FROM provider_services WHERE center_id=? AND active=1 ORDER BY id LIMIT 4', (cid,))
        for row, title in zip(svc, LONG_TITLES):
            srv.sql('UPDATE provider_services SET title=? WHERE id=?', (title, row['id']))
        # Template photos (as the administration would upload them) and one own photo of the centre.
        for slug, img in (('inmersion-doble', 'portada/fondo1.webp'), ('open-water', 'destinos/maldivas.webp'), ('bautizo', 'portada/portada-arrecife.webp'),
                          ('advanced', 'portada/logbook1.webp'), ('nitrox', 'portada/fondosuperior.webp')):
            admin.upload('/api/admin/service-catalog/photo', {'id': tpl[slug]}, img.rsplit('/', 1)[1], photo_file(img)); wait_ready('service_catalog', tpl[slug])
        own_sid = svc[3]['id']
        center.upload('/api/provider-services/photo', {'id': own_sid, 'rights': '1', 'focal': '50,50'}, 'propia.webp', photo_file('destinos/egipto.webp'))
        own_base = wait_ready('provider_services', own_sid)['photo_base']

        with sync_playwright() as p:
            browser = chromium(p)
            all_errors = {}

            def session(width=1366, mobile=False, geo=None, grant=False, init=None, lang='es-ES', scheme='light'):
                kw = {'viewport': {'width': width, 'height': 900 if width > 500 else 780}, 'locale': lang, 'color_scheme': scheme}
                if mobile: kw.update(is_mobile=True, has_touch=True, device_scale_factor=2)
                if geo: kw['geolocation'] = {'latitude': geo[0], 'longitude': geo[1], 'accuracy': 20}   # v50.54: km only when precise
                kw['permissions'] = ['geolocation'] if grant else []
                ctx = browser.new_context(**kw)
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                if init: ctx.add_init_script(init)
                pg = ctx.new_page(); pg.errs = []
                # Map tiles come from an external server the test environment cannot reach: not an error of the page.
                pg.on('console', lambda m: pg.errs.append(m.text) if m.type in ('error', 'warning') and 'ERR_TUNNEL' not in m.text and 'ERR_PROXY' not in m.text else None)
                pg.on('pageerror', lambda e: pg.errs.append(str(e)))
                return ctx, pg

            def go(pg, route, wait=1800):
                pg.goto(base + '/' + route); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(wait)

            def done(pg, label):
                all_errors[label] = list(pg.errs)

            def shot(pg, name, el=None, full=False):
                if not shots: return
                shots.mkdir(parents=True, exist_ok=True)
                (pg.locator(el).first if el else pg).screenshot(path=str(shots / f'{name}.jpg'), type='jpeg', quality=80, **({'full_page': True} if full and not el else {}))

            def login(pg, user):
                go(pg, '#/login', 600); pg.fill('#login', user); pg.fill('#password', PASSWORD); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1500)

            def top10(pg):
                return pg.evaluate("""()=>({title:document.querySelector('#tt-title')?.textContent||'',sub:document.querySelector('#tt-sub')?.textContent||'',
                    status:document.querySelector('#tt-status')?.innerText||'',n:document.querySelectorAll('#tt-list .tt-card:not(.is-skeleton)').length,
                    dist:[...document.querySelectorAll('#tt-list .tt-dist')].map(x=>x.textContent),locate:!!document.querySelector('#tt-locate, #tt-note-locate'),
                    asked:window.__geoAsked||0})""")

            def puntos(pg):
                return pg.evaluate("""()=>({sort:document.querySelector('#pt-sort')?.value,loc:document.querySelector('#pt-locbar')?.innerText||'',
                    groups:[...document.querySelectorAll('#pt-regions [data-area]')].map(x=>x.dataset.area).filter(Boolean),
                    cards:[...document.querySelectorAll('#pt-grid .pt-card')].map(c=>({id:c.id,km:c.querySelector('.pt-dist')?.textContent||''}))})""")

            # ---- 1. Top 10 and «Puntos de buceo» with the location allowed in three places --------------------------
            radii = {}
            for name, pos in PLACES.items():
                ctx, pg = session(geo=pos, grant=True)
                go(pg, '#/top10', 3500); t = top10(pg)
                km = [float(re.sub(r'[^\d,.]', '', d).replace(',', '.') or 0) for d in t['dist']]
                check(f'top10 {name}: 10 buceos cerca, con distancia', t['n'] == 10 and len(km) == 10 and 'cerca' in t['title'].lower(), t)
                radii[name] = max(km) if km else 0
                shot(pg, f'top10-{name}')
                go(pg, '#/puntos', 3000); d = puntos(pg)
                kms = [float(re.sub(r'[^\d,.]', '', c['km']).replace(',', '.') or 0) for c in d['cards']]
                check(f'puntos {name}: del más cercano al más lejano, km en cada tarjeta', d['sort'] == 'distance' and kms and all(b >= a - 1 for a, b in zip(kms, kms[1:])) and all(c['km'] for c in d['cards']), d['cards'][:4])
                # v50.54: the list and the map are two views of the same page (checked in e2e_v50_54_puntos_tipos.py).
                shot(pg, f'puntos-{name}')
                done(pg, f'top10/puntos {name}'); ctx.close()
            check('top10: desde Valencia el radio es menor que desde Madrid (costa)', radii['valencia'] < radii['madrid'], radii)

            # ---- 1b. Denied, no answer, denied before ---------------------------------------------------------------
            ctx, pg = session(init=COUNT_ASKS)
            go(pg, '#/top10', 3500); t = top10(pg)
            check('top10 denegada: Top 10 de España y aviso para activar la ubicación', t['n'] == 10 and 'España' in t['title'] and 'Activa la ubicación' in (t['status'] + t['sub']), t)
            shot(pg, 'top10-denegada')
            go(pg, '#/puntos', 3000); d = puntos(pg)
            order = ['Costa Brava', 'Comunidad Valenciana', 'Murcia', 'Andalucía', 'Baleares', 'Canarias', 'Cantábrico', 'Galicia']
            seen = [g for g in d['groups'] if g in order]
            check('puntos denegada: las zonas de España primero y en orden (v50.54: en la barra de regiones)', d['sort'] == 'area' and seen and seen == sorted(seen, key=order.index), d['groups'])
            check('puntos denegada: aviso «Activa la ubicación para ver primero los más cercanos»', 'Activa la ubicación' in d['loc'], d['loc'])
            shot(pg, 'puntos-denegada')
            done(pg, 'denegada'); ctx.close()

            ctx, pg = session(init=NEVER)
            go(pg, '#/top10', 1000)
            loading = top10(pg)
            check('top10 sin respuesta: estado de carga breve', 'Buscando' in loading['status'] or loading['n'] == 0, loading)
            pg.wait_for_timeout(9500); t = top10(pg)
            check('top10 sin respuesta: a los 8 s Top 10 de España y mensaje claro', t['n'] == 10 and 'España' in t['title'] and 'tardando' in (t['status'] + t['sub']), t)
            shot(pg, 'top10-sin-respuesta')
            done(pg, 'sin respuesta'); ctx.close()

            ctx, pg = session(init=COUNT_ASKS + "try{localStorage.setItem('wd_loc','denied')}catch(e){}")
            go(pg, '#/top10', 3000); t = top10(pg)
            check('top10 denegada antes: no vuelve a preguntar, España y botón «Usar mi ubicación»', t['asked'] == 0 and t['n'] == 10 and 'Usar mi ubicación' in pg.inner_text('#app'), t)
            done(pg, 'denegada antes'); ctx.close()

            # ---- 1c. Hawaii ---------------------------------------------------------------------------------------
            ctx, pg = session()
            go(pg, '#/puntos', 2000); pg.fill('#pt-q', 'Hawaii'); pg.press('#pt-q', 'Enter'); pg.wait_for_timeout(3500)
            h = pg.evaluate("()=>({h:document.querySelector('.pt-none h3')?.textContent||'',cards:document.querySelectorAll('#pt-grid .pt-card').length,m:document.querySelectorAll('#pt-map .pt-num').length})")
            check('puntos «Hawaii»: «Todavía no hay puntos de buceo en «Hawaii»» y los más cercanos debajo', 'Todavía no hay puntos de buceo en' in h['h'] and h['cards'] > 0, h)   # v50.54: no side map in the list view
            shot(pg, 'puntos-hawaii', full=True)
            go(pg, '#/explorar', 2500); pg.fill('#ex-q', 'Hawaii'); pg.wait_for_timeout(3500)
            ex = pg.inner_text('#ex-none') if pg.locator('#ex-none:visible').count() else ''
            check('explorar «Hawaii»: mensaje y sugerencias', 'Todavía no hay puntos de buceo en' in ex and pg.locator('#ex-none li').count() > 0, ex[:200])
            shot(pg, 'explorar-hawaii')
            # ---- 2. The search box: our «×» only with text, never the browser's circle
            q = pg.locator('#ex-q')
            x = pg.locator('#ex-q + .cd-x')
            check('buscador: «×» propia visible con texto', x.count() == 1 and x.is_visible())
            x.click(); pg.wait_for_timeout(300)
            check('buscador: «×» borra y desaparece', q.input_value() == '' and not x.is_visible())
            # The browser does not report the style of its inner «×»: the page's own rule that hides it is what is checked.
            native = pg.evaluate("""()=>[...document.styleSheets].flatMap(s=>{try{return [...s.cssRules]}catch(e){return []}})
                .filter(r=>r.selectorText&&r.selectorText.includes('::-webkit-search-cancel-button')).map(r=>r.style.display+'/'+(r.style.appearance||r.style.webkitAppearance))""")
            check('buscador: sin el botón nativo del navegador («circulito»)', native and all(x.startswith('none/none') for x in native), native)
            done(pg, 'hawaii'); ctx.close()

            # ---- 3. The centre's page at 360 px and on a computer ------------------------------------------------------
            for label, width, mobile in (('360', 360, True), ('ordenador', 1366, False)):
                ctx, pg = session(width, mobile)
                go(pg, f'#/centro?id={cid}', 2500)
                info = pg.evaluate("""()=>[...document.querySelectorAll('#cp-services .svc2, .cp-services .svc2')].map(c=>{const t=c.querySelector('.svc2-title');const r=t.getBoundingClientRect();
                    const lh=parseFloat(getComputedStyle(t).lineHeight)||20;const f=c.querySelector('.svc2-foot');const inr=c.querySelector('.svc2-in').getBoundingClientRect();
                    return {t:t.textContent.trim(),lines:Math.round(r.height/lh),w:r.width/inr.width,below:f?f.getBoundingClientRect().top>=r.bottom-1:true,
                            full:t.getAttribute('title'),h:c.getBoundingClientRect().height}})""")
                mine = [i for i in info if i['t'] in LONG_TITLES]
                check(f'centro {label}: los 4 títulos de prueba en 1–2 líneas', len(mine) == 4 and all(1 <= i['lines'] <= 2 for i in mine), mine)
                check(f'centro {label}: el título ocupa el ancho de la tarjeta', all(i['w'] > 0.6 for i in mine), [round(i['w'], 2) for i in mine])
                check(f'centro {label}: precio y «Reservar» debajo del título', all(i['below'] for i in info), info[:3])
                check(f'centro {label}: título completo disponible (title)', all(i['full'] == i['t'] for i in mine))
                if label == 'ordenador':
                    rows = pg.evaluate("""()=>{const m={};document.querySelectorAll('.cp-services .svc2').forEach(c=>{const r=c.getBoundingClientRect();
                        (m[Math.round(r.top+scrollY)]=m[Math.round(r.top+scrollY)]||[]).push(Math.round(r.height))});return Object.values(m)}""")
                    check('centro ordenador: tarjetas del mismo tamaño en cada fila', all(max(r) - min(r) <= 1 for r in rows), rows)
                shot(pg, f'centro-actividades-{label}', el='.cp-services')
                pts = pg.locator('#cp-points')
                check(f'centro {label}: «Puntos de buceo del centro» con subtítulo y «Ver punto»',
                      pts.count() == 1 and 'Puntos de buceo del centro' in pts.inner_text() and 'Puntos donde este centro organiza inmersiones' in pts.inner_text()
                      and pg.locator('#cp-points .cp-point').count() > 0 and pg.locator('#cp-points .cp-point a:has-text("Ver punto")').count() > 0)
                check(f'centro {label}: sin «Dónde se bucea»', 'Dónde se bucea' not in pg.inner_text('#app') and 'Dónde bucea' not in pg.inner_text('#app'))
                shot(pg, f'centro-puntos-{label}', el='#cp-points')
                n0 = pg.locator('#cp-reviews .review-card').count()
                url0 = pg.url
                if pg.locator('#cp-reviews-more').count(): pg.click('#cp-reviews-more'); pg.wait_for_timeout(1500)
                n1 = pg.locator('#cp-reviews .review-card').count()
                check(f'centro {label}: 3 reseñas al entrar y 5 más sin recargar', n0 == 3 and n0 < n1 <= 8 and pg.url == url0, (n0, n1))
                check(f'centro {label}: media encima de las reseñas', pg.locator('#cp-reviews .reviews-head .review-summary-box').count() == 1 and bool(pg.inner_text('#cp-reviews .review-summary-box').strip()))
                shot(pg, f'centro-resenas-{label}', el='#cp-reviews')
                if label == 'ordenador':
                    cards = pg.locator('.cp-services .svc2')
                    worst = min(card_contrast(pg, cards.nth(i)) for i in range(min(4, cards.count())))
                    check(f'tarjetas claras: contraste AA medido sobre la foto (≥ 4,5:1, peor {worst})', worst >= 4.5, worst)
                    src = pg.evaluate(f"()=>[...document.querySelectorAll('.cp-services .svc2')].map(c=>c.querySelector('img')?.currentSrc||'')")
                    check('foto propia en su tarjeta', any(own_base in s for s in src), src[:4])
                    lazy = pg.evaluate("()=>[...document.querySelectorAll('.cp-services .svc2 img')].every(i=>i.loading==='lazy'&&i.width&&i.height)")
                    check('fotos de las tarjetas con carga diferida y tamaño fijo', lazy)
                done(pg, f'centro {label}'); ctx.close()

            # ---- 4. Template photo changes at once (web and app), own photo does not; dark cards in the app ----------
            ctx, pg = session()
            go(pg, f'#/centro?id={cid}', 2500)
            before = pg.evaluate("()=>[...document.querySelectorAll('.cp-services .svc2')].map(c=>c.querySelector('img')?.getAttribute('src')||'')")
            admin.upload('/api/admin/service-catalog/photo', {'id': tpl['inmersion-doble']}, 'nueva.webp', photo_file('portada/portada-arrecife.webp'))
            new_base = wait_ready('service_catalog', tpl['inmersion-doble'])['photo_base']
            pg.reload(); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(2500)
            after = pg.evaluate("()=>[...document.querySelectorAll('.cp-services .svc2')].map(c=>c.querySelector('img')?.getAttribute('src')||'')")
            check('plantilla: la foto nueva sale al momento en los servicios que la usan', any(new_base in s for s in after) and not any(new_base in s for s in before), after[:4])
            check('plantilla: la foto propia no cambia', any(own_base in s for s in after))
            done(pg, 'plantilla web'); ctx.close()

            ctx, pg = session(390, True, init="try{localStorage.setItem('wda-tema','noche')}catch(e){}")
            go(pg, '?app=1#/', 3500)
            cards = pg.locator('.tarjeta-salida.svc2')
            check('modo app: tarjetas de salidas con la tarjeta común', cards.count() > 0, cards.count())
            check('modo app: sin desbordamiento horizontal', pg.evaluate('document.documentElement.scrollWidth') <= 391)
            if cards.count():
                srcs = pg.evaluate("()=>[...document.querySelectorAll('.tarjeta-salida img')].map(i=>i.getAttribute('src')||'')")
                check('modo app: con las fotos de plantilla', any('/assets/uploads/plantillas/' in s for s in srcs), srcs[:3])
                worst = min(card_contrast(pg, cards.nth(i)) for i in range(min(3, cards.count())))
                check(f'tarjetas oscuras (app «Noche»): contraste AA medido (≥ 4,5:1, peor {worst})', worst >= 4.5, worst)
                shot(pg, 'app-noche-salidas')
            done(pg, 'app noche'); ctx.close()

            # ---- 4b. Photo flow as the centre -------------------------------------------------------------------------
            ctx, pg = session()
            login(pg, ACCOUNTS['center'][0]); go(pg, '#/admin?tab=services', 2000)
            pg.click('#new-center-service'); pg.wait_for_timeout(1200)
            pg.select_option('#svc-template', str(tpl['bautizo'])); pg.wait_for_timeout(500)
            prev = pg.evaluate("()=>({l:document.querySelector('#svc-prev-light img')?.getAttribute('src')||'',d:document.querySelector('#svc-prev-dark img')?.getAttribute('src')||'',dark:document.querySelector('#svc-prev-dark .svc2')?.classList.contains('is-dark')})")
            check('centro: al elegir plantilla, vista previa clara y oscura con su foto', '/plantillas/' in prev['l'] and prev['l'] == prev['d'] and prev['dark'], prev)
            worst = card_contrast(pg, pg.locator('#svc-prev-dark .svc2'))
            check(f'vista previa oscura: contraste AA (peor {worst})', worst >= 4.5, worst)
            pg.locator('label.svc-check:has(input[name=svc-photo-mode][value=own])').click(); pg.wait_for_timeout(300)
            pg.set_input_files('#svc-photo-file', files=[{'name': 'mia.webp', 'mimeType': 'image/webp', 'buffer': photo_file('destinos/maldivas.webp')}]); pg.wait_for_timeout(800)
            pg.focus('.svc-preview'); pg.keyboard.press('ArrowRight'); pg.keyboard.press('ArrowRight'); pg.keyboard.press('ArrowUp'); pg.wait_for_timeout(300)
            pos = pg.evaluate("()=>getComputedStyle(document.querySelector('#svc-prev-light img')).objectPosition")
            check('centro: punto focal también con el teclado (flechas)', pos == '60% 45%', pos)
            rights = pg.locator('#svc-photo-rights')
            check('centro: casilla de derechos de la imagen visible', rights.count() == 1 and rights.is_visible())
            shot(pg, 'centro-foto-propia', el='#svc-photo')
            pg.fill('#svc-title', 'Bautizo con foto propia'); pg.fill('#svc-price', '55')
            pg.locator('button[type=submit][form=svc-form]').first.click(); pg.wait_for_timeout(1200)
            body = pg.inner_text('body')
            check('centro: sin la casilla no se guarda la foto (mensaje claro)', 'derechos' in body, body[-300:])
            pg.locator('label.svc-check:has(#svc-photo-rights)').click(); pg.locator('button[type=submit][form=svc-form]').first.click(); pg.wait_for_timeout(2500)
            sid = srv.sql("SELECT id FROM provider_services WHERE title='Bautizo con foto propia'")
            st = wait_ready('provider_services', sid[0]['id']) if sid else {}
            check('centro: foto propia guardada (derechos, quién y cuándo)', sid and st.get('photo_base') and srv.sql('SELECT photo_rights_at,photo_by FROM provider_services WHERE id=?', (sid[0]['id'],))[0]['photo_by'], st)
            done(pg, 'centro foto'); ctx.close()

            # ---- 4c. Administration: veil and withdrawing an own photo ------------------------------------------------
            ctx, pg = session()
            login(pg, ACCOUNTS['admin'][0]); go(pg, '#/admin', 2000)
            pg.click('button[data-tab="svctemplates"]'); pg.wait_for_timeout(2500)
            check('admin: «Plantillas de servicios» con sus plantillas', pg.locator('.st-card').count() >= 16, pg.locator('.st-card').count())
            pg.evaluate("()=>{const r=document.querySelector('#st-veil');r.value='90';r.dispatchEvent(new Event('input',{bubbles:true}))}")   # the slider is in % (50–95)
            pg.click('#st-veil-save'); pg.wait_for_timeout(1000)
            check('admin: intensidad de la capa guardada', abs(float(Client(srv).get('/api/site-media').json['card_veil']) - 0.9) < 0.01)
            shot(pg, 'admin-plantillas')
            item = pg.locator('.st-own-card .st-withdraw').first
            check('admin: lista de fotos propias con «Retirar foto»', item.count() == 1)
            if item.count():
                item.click(); pg.wait_for_timeout(600)
                pg.fill('#stw-why', 'Aparecen personas sin consentimiento'); pg.click('#stw-ok'); pg.wait_for_timeout(1500)
            left = srv.sql("SELECT COUNT(*) AS n FROM provider_services WHERE photo_mode='own'")[0]['n']
            check('admin: retirar una foto propia (vuelve a la plantilla, el centro ve el motivo)', srv.sql("SELECT COUNT(*) AS n FROM provider_services WHERE photo_note LIKE 'La administración ha retirado la foto:%'")[0]['n'] >= 1, left)
            admin.post('/api/admin/service-card-veil', {'value': 0.8})
            done(pg, 'admin'); ctx.close()

            # ---- 5. No «Profundidad habitual»; each role only its own --------------------------------------------------
            ctx, pg = session()
            go(pg, '#/tipos', 2000); txt = pg.inner_text('#app')
            first = pg.locator('#app a[href*="#/tipos/"], #app a[href*="tipo="]').first
            if first.count(): first.click(); pg.wait_for_timeout(1800); txt += pg.inner_text('#app')
            check('tipos de buceo: sin «Profundidad habitual»', 'Profundidad habitual' not in txt)
            done(pg, 'tipos'); ctx.close()
            for role in ('diver', 'freelance', 'center'):
                ctx, pg = session(); login(pg, ACCOUNTS[role][0]); go(pg, '#/admin?tab=svctemplates', 2000)
                check(f'rol {role}: no ve «Plantillas de servicios»', pg.locator('button[data-tab="svctemplates"]').count() == 0 and pg.locator('#st-veil').count() == 0)
                done(pg, f'rol {role}'); ctx.close()
            browser.close()
            dirty = {k: v for k, v in all_errors.items() if v}
            check('consola limpia en todas las páginas tocadas', not dirty, dirty)
    finally:
        srv.stop()
    return results


if __name__ == '__main__':
    out = run(Path(sys.argv[1]) if len(sys.argv) > 1 else None)
    bad = [r for r in out if not r[1]]
    print(f'{len(out) - len(bad)}/{len(out)} comprobaciones correctas')
    sys.exit(1 if bad else 0)
