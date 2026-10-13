"""Fase 5 in a real browser: legal pages (version, history, prevails note), re-acceptance window, announced change
for centres, admin legal editor, retention card, data rights, «Denunciar» on reviews/centres/points with the single
reply of the centre, own point descriptions in two languages, maps without third-party tiles, admin maps/images,
demo ribbon, labels tied to their fields, and phone width.
Usage: python tests/e2e_legal_catalog.py [--shots DIR]
"""
from __future__ import annotations

import datetime as dt
import sys
import tempfile
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]   # tests/navegador and tests (helpers)
from helpers import ServerTestCase, Server  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
TODAY = dt.date.today()
LABELS_JS = """() => [...document.querySelectorAll('label')].filter(l => !l.htmlFor && !l.querySelector('input,select,textarea')
                 && l.offsetParent !== null).map(l => l.textContent.trim().slice(0, 40))"""


from e2e_markers import chromium  # noqa: E402  (answers the administrator's reason, v50.47 B.9)


def run(shots: Path | None):
    tiles = Path(tempfile.mkdtemp(prefix='wod-e2e-tiles-'))
    ServerTestCase.server = Server({'WOD_TILES_DIR': str(tiles)}).start()
    srv = ServerTestCase.server
    t = ServerTestCase('run')
    checks = []

    def check(name, ok, detail=''):
        checks.append((name, bool(ok), detail))

    try:
        admin = t.make_admin()
        center = t.make_center(admin, 'legale2e')
        cid = center.user['center_id']
        diver = t.make_diver('legale2e')
        srv.sql('''INSERT INTO bookings(user_id,center_id,booking_date,participants,status,payment_status,created_at,updated_at)
                   VALUES(?,?,?,1,'confirmed','paid',datetime('now'),datetime('now'))''', (diver.user['id'], cid, '2026-01-10'))
        rid = diver.post(f'/api/centers/{cid}/reviews', {'rating': 5, 'title': 'Genial', 'body': 'Todo perfecto en la inmersión.'}).json['id']
        pid = srv.sql("SELECT id FROM dive_points WHERE name='Cap Dor'")[0]['id']
        base = srv.base
        with sync_playwright() as p:
            browser = chromium(p)
            external = []

            def session(login=None, pw=PW, width=1366):
                ctx = browser.new_context(viewport={'width': width, 'height': 900}, locale='es-ES')
                page = ctx.new_page(); errors = []
                page.on('pageerror', lambda e: errors.append(str(e)))
                page.on('request', lambda r: external.append(r.url) if ('tile.openstreetmap' in r.url or 'arcgisonline' in r.url) else None)
                if login:
                    page.goto(base + '/#/login'); page.wait_for_selector('#login'); page.fill('#login', login); page.fill('#password', pw)
                    page.click('#login-form button[type=submit]'); page.wait_for_timeout(900)
                return ctx, page, errors

            def go(page, route, wait=1000):
                page.goto(base + '/' + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)

            def shot(page, name, full=True):
                if shots:
                    shots.mkdir(parents=True, exist_ok=True); page.screenshot(path=str(shots / f'{name}.png'), full_page=full)

            # ---------------------------------------------------------------- visitor: legal pages, point, centre
            ctx, page, errors = session()
            go(page, '#/legal/condiciones-buceadores', 1200)
            body = page.inner_text('body')
            check('legal: versión vigente e historial', 'Versión vigente' in body and 'Versiones de este documento' in body and page.locator('.lg-hist-list li').count() >= 1)
            check('legal: enlace del pie con la ruta nueva', page.locator('footer a[href="#/legal/condiciones-centros"]').count() >= 1 and page.locator('footer a[href="#/legal/centros"]').count() == 0)
            page.locator('.lg-hist-list [data-ver]').first.click(); page.wait_for_timeout(600)
            check('legal: leer una versión anterior', page.locator('#legal-version .lg-doc').count() == 1)
            shot(page, 'legal-condiciones')
            go(page, f'#/punto?id={pid}', 1500)
            about = page.inner_text('.tp-block')
            check('punto: descripción propia en castellano', 'Torre de Cap d' in about and 'Profundidad de 10 a 28 m' in about)
            check('punto: botón Denunciar contenido', page.locator('.wd-report[data-report="point"]').count() == 1)
            page.locator('.wd-report[data-report="point"]').click(); page.wait_for_timeout(500)
            check('denuncia: ventana con motivo y buena fe', page.locator('#report-modal #rpm-reason').count() == 1 and page.locator('#rpm-faith').count() == 1)
            page.select_option('#rpm-reason', 'false'); page.fill('#rpm-details', 'La profundidad indicada no coincide con la real.')
            page.fill('#rpm-name', 'Visitante'); page.fill('#rpm-email', 'visitante@example.org'); page.check('#rpm-faith')
            page.click('#rpm-send'); page.wait_for_timeout(900)
            check('denuncia de un punto registrada', srv.sql("SELECT 1 FROM content_reports WHERE target_type='point' AND target_id=?", (pid,)))
            go(page, f'#/centro?id={cid}', 1500)
            check('centro: Denunciar en la reseña y en la ficha', page.locator(f'#review-{rid} .wd-report').count() == 1 and page.locator('.wd-report[data-report="center"]').count() == 1)
            check('visitante sin errores JS', not errors, errors)
            ctx.close()
            # English visitor: the point text in English
            ctx = browser.new_context(viewport={'width': 1280, 'height': 900}, locale='en-GB'); page = ctx.new_page()
            go(page, f'#/punto?id={pid}', 1800)
            check('punto: descripción en inglés', 'Depth from 10 to 28 m' in page.inner_text('.tp-block'))
            ctx.close()

            # ---------------------------------------------------------------- centre replies to the review; sees announced change
            md = '# Condiciones para centros y profesionales\n\nVersión de prueba con un cambio anunciado con quince días.'
            admin.post('/api/admin/legal/publish', {'slug': 'centros', 'lang': 'es', 'markdown': md, 'summary': 'Cambio de prueba', 'effective_at': (TODAY + dt.timedelta(days=16)).isoformat()})
            ctx, page, errors = session('center_legale2e')
            go(page, '#/admin', 1600)
            check('centro: aviso de cambio en el panel', page.locator('#pro-terms-bar').count() == 1 and 'entra en vigor' in page.inner_text('#pro-terms-bar'))
            shot(page, 'centro-aviso-condiciones', False)
            go(page, f'#/centro?id={cid}', 1500)
            page.locator(f'#review-{rid} .rv-reply').click(); page.wait_for_timeout(500)
            page.fill('#rr-body', 'Gracias por venir, os esperamos pronto.'); page.click('#rr-save'); page.wait_for_timeout(1300)
            check('centro: respuesta pública publicada', 'Respuesta del centro' in page.inner_text(f'#review-{rid}'))
            shot(page, 'resena-respuesta')
            check('centro sin errores JS', not errors, errors)
            ctx.close()

            # ---------------------------------------------------------------- diver: new terms must be accepted again
            admin.post('/api/admin/legal/publish', {'slug': 'privacidad', 'lang': 'es', 'markdown': '# Política de privacidad\n\nNueva versión de prueba de la política de privacidad.',
                                                    'summary': 'Cambio de prueba', 'effective_at': TODAY.isoformat()})
            ctx, page, errors = session('diver_legale2e', width=390)
            go(page, '#/cuenta', 1500)
            check('buceador: ventana para aceptar la nueva versión', page.locator('#legal-accept').count() == 1)
            shot(page, 'reaceptar-movil', False)
            check('aceptar desactivado sin la casilla', page.locator('#la-accept').is_disabled())
            page.check('#la-ok'); page.click('#la-accept'); page.wait_for_timeout(900)
            check('buceador: versión aceptada', not diver.me()['legal']['pending'])
            check('Mi cuenta: descarga ZIP', page.locator('a[href="/api/account/export?format=zip"]').count() >= 1)
            page.click('#acc-delete'); page.wait_for_timeout(400); page.fill('#del-pw', PW); page.click('#del-ok'); page.wait_for_timeout(900)
            check('eliminar cuenta pide confirmación por email', srv.sql("SELECT 1 FROM email_outbox WHERE template='account_delete_confirm' AND to_email='legale2e@diver.example.org'"))
            sw = page.evaluate('document.documentElement.scrollWidth')
            check('móvil sin desbordamiento horizontal', sw <= 392, sw)
            check('buceador sin errores JS', not errors, errors)
            ctx.close()

            # ---------------------------------------------------------------- admin: legal editor, retention, maps, images, point texts
            admin.post('/api/legal/accept', {})   # the administrator also accepts the new privacy version
            ctx, page, errors = session('admin', 'admin-seguro-2026')
            go(page, '#/admin?tab=legal', 1600)
            check('admin: conservación de datos', page.locator('#ret-form').count() == 1)
            check('admin: tabla de documentos', page.locator('.adl-doctable tbody tr').count() >= 10)
            page.locator('.adl-edit[data-slug="cookies"]').click(); page.wait_for_timeout(900)
            check('admin: editor con fecha de entrada en vigor', page.locator('#legal-editor #le-eff').count() == 1 and page.locator('#le-md').input_value().startswith('# '))
            shot(page, 'admin-editor-legal', False)
            page.fill('#le-sum', 'Aclaramos los servicios de terceros.'); page.click('#le-pub'); page.wait_for_timeout(1200)
            check('admin: versión publicada', srv.sql("SELECT 1 FROM legal_documents WHERE slug='cookies' AND summary='Aclaramos los servicios de terceros.'"))
            unl = page.evaluate(LABELS_JS)
            check('admin legal: todas las etiquetas enlazadas', not unl, unl)
            go(page, '#/admin?tab=maps', 1300)
            check('admin: mapas (límite satélite)', page.locator('#maps-limit').input_value() == '1900000')
            go(page, '#/admin?tab=pointtexts', 1600)
            check('admin: descripciones por revisar', page.locator('.apt-item').count() > 50)
            go(page, '#/admin?tab=media', 1800)
            check('admin: origen de las imágenes', page.locator('#image-origins .data-table tbody tr').count() >= 20)
            check('admin sin errores JS', not errors, errors)
            ctx.close()

            # ---------------------------------------------------------------- registration labels and maps
            ctx, page, errors = session()
            go(page, '#/registro', 1000)
            unl = page.evaluate(LABELS_JS)
            check('registro: todas las etiquetas enlazadas', not unl, unl)
            go(page, '#/', 2500)
            # Without a PMTiles file and outside production the map uses OSM only for development (docs/mapas.md);
            # the public Esri server is never used.
            cfg = page.evaluate("fetch('/api/map/config').then(r=>r.json())")
            check('mapas: sin el servidor público de Esri', not [u for u in external if 'arcgisonline' in u], external[:3])
            check('mapas: OSM público solo en desarrollo sin archivo PMTiles', cfg['basemap']['type'] == 'osm-dev' or not [u for u in external if 'openstreetmap' in u])
            ctx.close()
            browser.close()
    finally:
        srv.stop()

    # Demo mode: ribbon
    ServerTestCase.server = Server({'WOD_DEMO_MODE': '1'}).start()
    srv = ServerTestCase.server
    try:
        with sync_playwright() as p:
            browser = chromium(p)
            ctx = browser.new_context(viewport={'width': 1280, 'height': 900}, locale='es-ES'); page = ctx.new_page()
            page.goto(srv.base + '/#/'); page.wait_for_load_state('networkidle'); page.wait_for_timeout(1500)
            check('demo: banda «Entorno de pruebas»', 'Entorno de pruebas' in page.inner_text('#demo-ribbon'))
            if shots: page.screenshot(path=str(shots / 'demo-cinta.png'))
            browser.close()
    finally:
        srv.stop()
    return checks


if __name__ == '__main__':
    shots = Path(sys.argv[sys.argv.index('--shots') + 1]) if '--shots' in sys.argv else None
    results = run(shots)
    for name, ok, detail in results:
        print(('OK   ' if ok else 'FALLA') + ' ' + name + (f' · {detail}' if detail and not ok else ''))
    bad = [r for r in results if not r[1]]
    print(f'{len(results) - len(bad)}/{len(results)} comprobaciones correctas')
    sys.exit(1 if bad else 0)
