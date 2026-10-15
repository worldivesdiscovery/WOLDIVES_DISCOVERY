#!/usr/bin/env python3
"""v50.57 · Revisión general (15/10/2026), en el navegador, sobre la demo.

Bloque 1.1 · zona horaria. El servidor arranca como en un Windows limpio (sin las zonas horarias del sistema y sin
tzdata): el panel del centro, sus reservas y su planning, y las reservas, el planning y «Mi agenda» del freelance se abren
sin error. Además, si una parte del panel falla, solo esa parte lo dice (con «Reintentar») y el resto funciona.

Bloque 1.2 · el QR de la reserva se ve en la ficha del buceador, del centro y de la administración, y al leerlo (OpenCV,
como un móvil) lleva a esa reserva.

Bloque 1.3 · las exportaciones descargan en Excel y en CSV desde Herramientas (centro) y desde Pagos y DAC7
(administración); sin datos en el periodo, el archivo sale igual con el aviso.

    python3 tests/navegador/e2e_v50_57_revision.py [carpeta-de-capturas]

Usa las cuentas de la demo: no va en el zip de producción (scripts/generar_zips.py)."""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app'),
                str(Path(__file__).resolve().parents[2] / 'scripts')]
from helpers import Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402
from crear_demo import PASSWORD  # noqa: E402
import io  # noqa: E402
try:
    import cv2  # noqa: E402
    import numpy as np  # noqa: E402
    from PIL import Image  # noqa: E402
except ImportError:   # without OpenCV the QR is checked on screen but not read
    cv2 = None

ROOT = Path(__file__).resolve().parents[2]
DESK = {'viewport': {'width': 1366, 'height': 900}, 'locale': 'es-ES'}
BROKEN = ('No se ha podido abrir', 'No time zone', 'Falta un dato obligatorio')
QUICK = os.environ.get('WOD_E2E_RAPIDO') == '1'


def no_time_zones(tmp: Path) -> dict:
    """A Python that finds no time zone at all, as on Windows without tzdata."""
    (tmp / 'vacio').mkdir(exist_ok=True); (tmp / 'falso' / 'tzdata').mkdir(parents=True, exist_ok=True)
    (tmp / 'falso' / 'tzdata' / '__init__.py').write_text('', encoding='utf-8')
    return {'PYTHONTZPATH': str(tmp / 'vacio'), 'PYTHONPATH': str(tmp / 'falso')}


def run(out: Path | None):
    rows = []

    def check(name, ok, detail=''):
        rows.append((name, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + name + ('' if ok else f'  → {str(detail)[:400]}'), flush=True)

    tmp = Path(tempfile.mkdtemp(prefix='wod-revision-'))
    db = tmp / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(db)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': '', 'PYTHONUNBUFFERED': '1', **no_time_zones(tmp)}, seed=db).start()
    errors = []
    try:
        out_txt = (srv.tmp / 'stdout.log').read_text(encoding='utf-8')
        check('1.1 · el servidor arranca sin zonas horarias y lo dice en la consola, con la solución',
              'faltan las zonas horarias' in out_txt.lower() and 'requirements.txt' in out_txt, out_txt[:300])
        with sync_playwright() as pw:
            browser = chromium(pw)

            def ctx():
                c = browser.new_context(**DESK)
                c.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg = c.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
                return c, pg

            def login(pg, user):
                pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login-form')
                pg.fill('#login', user); pg.fill('#password', PASSWORD); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1500)

            def confirm_admin(pg):
                """4.1: personal data opens with the password and a reason (as the window does), for the sections that test other things."""
                st = pg.evaluate("""() => fetch('/api/admin/confirm', {method: 'POST', headers: {'Content-Type': 'application/json'},
                                   body: JSON.stringify({password: '%s', reason: 'Soporte: recorrido de la revisión'})}).then(r => r.text().then(() => r.status))""" % PASSWORD)
                # (the body is read: a response left unread counts as a request in progress and «networkidle» never comes)
                assert st == 200, st

            def tab(pg, name, ready, wait=900):
                pg.goto(f'{srv.base}/#/admin?tab={name}'); pg.wait_for_selector('.cb-nav', timeout=15000)
                pg.wait_for_selector(ready, timeout=15000); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(wait)
                return pg.inner_text('main') if pg.locator('main').count() else pg.inner_text('body')

            def wait_hash(pg, test, timeout=15000):
                """The page's CSP does not allow wait_for_function with text: the address is read until it matches."""
                h = ''
                for _ in range(timeout // 100):
                    h = pg.evaluate('location.hash')
                    if test(h): return h
                    pg.wait_for_timeout(100)
                raise AssertionError('dirección: ' + h)

            def shot(pg, name, full=False):
                if out: out.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(out / f'{name}.png'), full_page=full)

            def clean(txt): return not any(b in txt for b in BROKEN)

            # 1.1 · the centre: panel, bookings and planning, with no time zones on the server
            c, pg = ctx(); login(pg, 'centro.prueba')
            t = tab(pg, 'dashboard', '#cb-content .cb-module, #cb-content section, #cb-content article')
            check('1.1 · centro: el panel se abre sin el error de zona horaria', clean(t) and 'Bahía Coralina' in t, t[:300])
            shot(pg, 'b1-1-centro-panel-sin-tzdata')
            t = tab(pg, 'bookings', '#cb-bookings *')
            check('1.1 · centro: Reservas se abre', clean(t) and pg.locator('#cb-bookings *').count() > 3, t[:300])
            t = tab(pg, 'planning', '#cb-planning *')
            check('1.1 · centro: Planning se abre', clean(t) and pg.locator('#cb-planning *').count() > 3, t[:300])
            c.close()

            # 1.1 · the freelance: bookings, planning and «Mi agenda»
            c, pg = ctx(); login(pg, 'freelance.prueba')
            for name, ready, label in (('bookings', '#fl-bookings *', 'Reservas'), ('planning', '#fl-planning *', 'Planning'), ('agenda', '#fl-agenda *', 'Mi agenda')):
                t = tab(pg, name, ready)
                check(f'1.1 · freelance: {label} se abre sin el error de zona horaria', clean(t) and pg.locator(ready).count() > 3, t[:300])
                if name == 'agenda': shot(pg, 'b1-1-freelance-agenda-sin-tzdata')
            c.close()

            # 1.1 · a part that fails says so on its own; the rest of the panel works
            c, pg = ctx(); login(pg, 'centro.prueba')
            pg.route('**/api/bookings', lambda route: route.fulfill(status=500, content_type='application/json', body='{"error":"Error interno"}'))
            pg.goto(f'{srv.base}/#/admin'); pg.wait_for_selector('.cb-nav', timeout=15000); pg.wait_for_timeout(1500)
            t = pg.inner_text('body')
            check('1.1 · si fallan las reservas, el panel se abre y solo esa parte lo dice', 'No se ha podido abrir' not in t and pg.locator('.wd-block-error').count() >= 1
                  and 'Reservas' in pg.inner_text('.wd-block-error') and pg.locator('.cb-nav').count() > 5, t[:400])
            shot(pg, 'b1-1-parte-que-falla')
            pg.unroute('**/api/bookings'); pg.locator('.wd-block-error [data-block-retry]').first.click(); pg.wait_for_timeout(2000)
            check('1.1 · «Reintentar» lo carga cuando vuelve a funcionar', pg.locator('.wd-block-error').count() == 0 and 'Bahía Coralina' in pg.inner_text('body'))
            pg.route('**/api/center/planning*', lambda route: route.fulfill(status=500, content_type='application/json', body='{"error":"Error interno"}'))
            pg.locator('.cb-nav[data-cbtab="planning"]').click(); pg.wait_for_timeout(1500)
            ct = pg.inner_text('#cb-content')
            check('1.1 · una pestaña que falla lo dice en su sitio, con «Reintentar», y el menú sigue',
                  ('no se ha podido cargar' in ct.lower()) and 'Reintentar' in ct and pg.locator('.cb-nav').count() > 5, ct[:200])
            pg.locator('.cb-nav[data-cbtab="services"]').click(); pg.wait_for_timeout(1800)
            check('1.1 · y las demás pestañas funcionan', pg.locator('#center-services-manager *').count() > 3 and pg.locator('#cb-content .wd-block-error').count() == 0)
            c.close()

            # 1.2 · the QR of the booking, inside the page, for the diver, the centre and the administration
            uid = lambda u: srv.sql('SELECT id,center_id FROM users WHERE username=?', (u,))[0]
            bk = srv.sql("SELECT id FROM bookings WHERE user_id=? AND center_id=? AND status IN ('confirmed','requested') ORDER BY id DESC LIMIT 1",
                         (uid('buzo.prueba')['id'], uid('centro.prueba')['center_id']))[0]['id']
            for user, sel, label in (('buzo.prueba', '.reservation-qr .bk-qr svg', 'buceador'), ('centro.prueba', '.bk-qr-center .bk-qr svg', 'centro'),
                                     ('admin.prueba', '.reservation-qr .bk-qr svg', 'administración')):
                c, pg = ctx(); login(pg, user)
                if user == 'admin.prueba': confirm_admin(pg)
                pg.goto(f'{srv.base}/#/reserva?id={bk}'); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(1200)
                ok = pg.locator(sel).count() == 1
                read = ''
                if ok and cv2 is not None:
                    raw = pg.locator(sel).screenshot()
                    read = cv2.QRCodeDetector().detectAndDecode(np.array(Image.open(io.BytesIO(raw)).convert('RGB')))[0]
                check(f'1.2 · {label}: el QR se ve en la ficha de la reserva y lleva a esa reserva',
                      ok and (cv2 is None or f'verificarreserva?id={bk}&t=' in read), read or pg.inner_text('main')[:200])
                shot(pg, f'b1-2-qr-ficha-{label.replace("ó", "o")}')
                c.close()

            # 1.3 · exports: Excel and CSV download from Herramientas (centre) and from Pagos and DAC7 (administration)
            c, pg = ctx(); login(pg, 'centro.prueba')
            pg.goto(f'{srv.base}/#/admin?tab=tools'); pg.wait_for_selector('#cb-tools [data-export]', timeout=15000); pg.wait_for_timeout(800)
            box = pg.locator('#cb-tools [data-export]').first
            with pg.expect_download() as dl: box.locator('[data-ex-kind="reservas"]').click()
            f = dl.value; path = f.path(); data = Path(path).read_bytes()
            check('1.3 · centro: «Reservas» descarga un Excel (.xlsx)', f.suggested_filename.endswith('.xlsx') and data[:2] == b'PK', f.suggested_filename)
            box.locator('input[value="csv"]').check(); box.locator('[data-ex-period]').select_option('todo')
            with pg.expect_download() as dl: box.locator('[data-ex-kind="clientes"]').click()
            f = dl.value; data = Path(f.path()).read_bytes()
            check('1.3 · centro: «Clientes» en CSV para Excel en español (BOM y «;»)', f.suggested_filename.endswith('.csv') and data.startswith(b'\xef\xbb\xbf') and b';' in data.split(b'\r\n')[0], data[:80])
            box.locator('[data-ex-period]').select_option('personalizado')
            box.locator('[data-ex-kind="servicios"]').click(); pg.wait_for_timeout(500)
            check('1.3 · sin fechas en «Personalizado» lo dice en su sitio', 'dos fechas' in box.locator('[data-ex-msg]').inner_text())
            box.locator('[data-ex-from]').fill('2001-01-01'); box.locator('[data-ex-to]').fill('2001-01-31')
            with pg.expect_download() as dl: box.locator('[data-ex-kind="reservas"]').click()
            data = Path(dl.value.path()).read_bytes().decode('utf-8-sig')
            check('1.3 · un periodo sin datos descarga igual, con «Sin datos en este periodo»', 'Sin datos en este periodo' in data, data[:120])
            shot(pg, 'b1-3-exportar-herramientas')
            c.close()
            c, pg = ctx(); login(pg, 'admin.prueba'); confirm_admin(pg)
            pg.goto(f'{srv.base}/#/admin?tab=adminpay'); pg.wait_for_selector('#admin-payments .wd-export-wrap', timeout=15000)
            pg.locator('#admin-payments .wd-export-wrap summary').click()
            with pg.expect_download() as dl: pg.locator('#admin-payments [data-ex-kind="pagos"]').click()
            check('1.3 · administración: «Pagos» descarga', dl.value.suggested_filename.endswith('.xlsx'), dl.value.suggested_filename)
            pg.goto(f'{srv.base}/#/admin?tab=plans'); pg.wait_for_selector('#admin-plans [data-ex-kind="dac7"]', timeout=15000)
            with pg.expect_download() as dl: pg.locator('#admin-plans [data-ex-kind="dac7"]').click()
            check('1.3 · administración: el informe DAC7 descarga (Excel)', dl.value.suggested_filename.startswith('worldives-informe-dac7') and dl.value.suggested_filename.endswith('.xlsx'), dl.value.suggested_filename)
            shot(pg, 'b1-3-exportar-dac7')
            c.close()

            c, pg = ctx(); login(pg, 'admin.prueba')
            pg.route('**/api/admin/audit', lambda route: route.fulfill(status=500, content_type='application/json', body='{"error":"Error interno"}'))
            pg.goto(f'{srv.base}/#/admin'); pg.wait_for_selector('.provider-tabs', timeout=15000); pg.wait_for_timeout(1500)
            t = pg.inner_text('body')
            check('1.1 · administración: si falla una parte, el Centro de control se abre igual y lo dice', 'Centro de control' in t and 'No se ha podido abrir' not in t
                  and 'Actividad' in pg.inner_text('.wd-block-error'), t[:400])
            c.close()

            # 2.1 · always back to where you were
            c, pg = ctx(); login(pg, 'admin.prueba')
            pg.goto(f'{srv.base}/#/admin?tab=points'); pg.wait_for_selector('.edit-point', timeout=15000)
            pid = pg.locator('.edit-point').first.get_attribute('data-id')
            pg.locator('.edit-point').first.click(); pg.wait_for_selector('#point-form', timeout=15000)
            crumbs = pg.inner_text('.wd-crumbs')
            check('2.1 · editar un punto tiene su dirección propia', pg.evaluate('location.hash') == f'#/admin?tab=points&edit={pid}', pg.evaluate('location.hash'))
            check('2.1 · migas «Centro de control › Puntos de buceo › Editar …» y «← Volver»',
                  crumbs.startswith('Centro de control') and 'Puntos de buceo' in crumbs and 'Editar ' in crumbs and pg.locator('.wd-back').is_visible(), crumbs)
            shot(pg, 'b2-1-editar-punto-migas')
            pg.go_back(); pg.wait_for_selector('.edit-point', timeout=15000)
            check('2.1 · el botón «atrás» del navegador vuelve a la lista de puntos', pg.evaluate('location.hash') == '#/admin?tab=points', pg.evaluate('location.hash'))
            pg.go_forward(); pg.wait_for_selector('#point-form', timeout=15000)
            pg.locator('.wd-back').click(); pg.wait_for_selector('.edit-point', timeout=15000)
            check('2.1 · «← Volver» lleva a la lista de puntos', pg.evaluate('location.hash') == '#/admin?tab=points', pg.evaluate('location.hash'))
            pg.goto(f'{srv.base}/#/admin?tab=points&edit={pid}'); pg.wait_for_selector('#point-form', timeout=15000)
            name = pg.input_value('#p-name')
            pg.locator('#point-form button.btn-primary').last.click()
            wait_hash(pg, lambda h: h == '#/admin?tab=points'); pg.wait_for_selector('.edit-point', timeout=15000)
            check('2.1 · «Guardar» un punto vuelve a Administración › Puntos con «Guardado»',
                  'Guardado' in pg.inner_text('body') and 'Explorar' not in pg.inner_text('#app')[:200], pg.inner_text('body')[:300])
            shot(pg, 'b2-1-guardado-vuelve-a-puntos')
            check('2.1 · el punto se ha guardado sin cambios no pedidos', name in pg.inner_text('#app'), name)
            # the menu of the section you are in always works (before: from «Editar punto», «Administración» did nothing)
            pg.goto(f'{srv.base}/#/admin'); pg.wait_for_selector('.provider-tabs', timeout=15000); pg.wait_for_load_state('networkidle')
            pg.evaluate("document.querySelector('#app').insertAdjacentHTML('afterbegin','<p id=wd-mark>marca</p>')")
            pg.locator('#account-toggle').click(); pg.locator('#account-dropdown a[href="#/admin"]').click()
            pg.wait_for_selector('#wd-mark', state='detached', timeout=8000); pg.wait_for_selector('.provider-tabs', timeout=15000)
            check('2.1 · pulsar «Administración» estando ya en Administración la vuelve a cargar', pg.locator('#wd-mark').count() == 0)
            for tabname, sel, form, label in (('centers', '#new-center', '#center-form', 'Nuevo centro'), ('centers', '.edit-center', '#center-form', 'Editar centro'),
                                              ('destinations', '.edit-destination', '#destination-form', 'Editar destino')):
                pg.goto(f'{srv.base}/#/admin?tab={tabname}'); pg.wait_for_selector(sel, timeout=15000)
                pg.locator(sel).first.click()
                try: pg.wait_for_selector(form, timeout=10000); ok = True
                except Exception: ok = False
                check(f'2.1 · Administración › {label} se abre, con su dirección y «← Volver»', ok and pg.locator('.wd-back').is_visible(), pg.evaluate('location.hash'))
            pg.locator('#destination-form button.btn-primary').click()
            wait_hash(pg, lambda h: h == '#/admin?tab=destinations')
            check('2.1 · «Guardar destino» vuelve a Administración › Destinos con «Guardado»', 'Guardado' in pg.inner_text('body'))
            # changing mode at the first try: Administración → public page of a centre → Administración
            pg.locator('#main-nav a[href="#/centros"]').first.click(); wait_hash(pg, lambda h: h == '#/centros')
            pg.wait_for_selector('a[href^="#/centro?id="]', timeout=15000); pg.locator('a[href^="#/centro?id="]').first.click()
            wait_hash(pg, lambda h: h.startswith('#/centro?id=')); pg.wait_for_load_state('networkidle')
            pg.locator('#account-toggle').click(); pg.locator('#account-dropdown a[href="#/admin"]').click()
            pg.wait_for_selector('.provider-tabs', timeout=15000)
            check('2.1 · de la ficha de un centro a Administración, a la primera', 'Centro de control' in pg.inner_text('#app'))
            # a slow screen that finishes after the next one does not cover it
            pg.goto(f'{srv.base}/#/centros'); pg.wait_for_selector('a[href^="#/centro?id="]', timeout=15000)
            pg.evaluate("""() => { const f = window.fetch; window.fetch = (u, o) => String(u).includes('/api/admin/audit') ? new Promise(r => setTimeout(r, 2500)).then(() => f(u, o)) : f(u, o);
                                   location.hash = '#/admin'; setTimeout(() => { location.hash = '#/centros'; }, 300); }""")
            pg.wait_for_timeout(8000)   # in v50.56 Administración covered «Centros» after about 5.6 s
            t = pg.inner_text('#app')
            check('2.1 · una pantalla lenta (Administración) no tapa la siguiente', pg.evaluate('location.hash') == '#/centros' and 'Centro de control' not in t, t[:200])
            shot(pg, 'b2-1-pantalla-lenta-no-tapa')
            c.close()
            # «Volver» never takes you out of the web (you arrived from another site)
            c, pg = ctx()
            pg.goto('data:text/html,<p>otra web</p>'); pg.goto(f'{srv.base}/#/centros'); pg.wait_for_selector('a[href^="#/centro?id="]', timeout=15000)
            href = pg.locator('a[href^="#/centro?id="]').first.get_attribute('href')
            pg.goto(f'{srv.base}/{href}'); pg.wait_for_selector('#global-back', timeout=15000)
            pg.locator('#global-back').click(); pg.wait_for_timeout(1500)
            check('2.1 · «Volver» vuelve a la pantalla anterior de la web', pg.url.startswith(srv.base) and pg.evaluate('location.hash') == '#/centros', pg.url)
            c.close()
            c, pg = ctx()
            pg.goto('data:text/html,<p>otra web</p>'); pg.goto(f'{srv.base}/{href}'); pg.wait_for_selector('#global-back', timeout=15000)
            pg.locator('#global-back').click(); pg.wait_for_timeout(1500)
            check('2.1 · «Volver» en la primera pantalla no saca de la web (va al inicio)', pg.url.startswith(srv.base), pg.url)
            c.close()

            # 2.2 · Administración → Puntos, Destinos y Plantillas, botón a botón (where the owner saw failures)
            c, pg = ctx(); login(pg, 'admin.prueba')

            def toast_has(text, timeout=8000):
                for _ in range(timeout // 100):
                    if text in (pg.inner_text('#toast') or ''): return True
                    pg.wait_for_timeout(100)
                return False

            def every_edit(tab, button, form, field, label):
                pg.goto(f'{srv.base}/#/admin?tab={tab}'); pg.wait_for_selector(button, timeout=15000)
                found = pg.eval_on_selector_all(button, "bs => bs.map(b => [b.dataset.id, b.closest('tr').cells[0].innerText.trim()])")
                bad = []
                for rid, rname in (found[:12] if QUICK else found):   # WOD_E2E_RAPIDO=1: the first 12 (while developing)
                    pg.locator(f'{button}[data-id="{rid}"]').click()
                    try:
                        pg.wait_for_selector(form, timeout=10000)
                        if pg.input_value(field) != rname: bad.append((rname, 'abre otro: ' + pg.input_value(field)))
                        if not pg.locator('.wd-back').is_visible(): bad.append((rname, 'sin «← Volver»'))
                    except Exception as e:
                        bad.append((rname, type(e).__name__))
                    pg.go_back(); pg.wait_for_selector(button, timeout=15000)
                check(f'2.2 · {label}: los {len(found)} botones «Editar» abren cada uno el suyo, con «← Volver»' + (' (rápido: 12)' if QUICK else ''), found and not bad, bad[:5])
                return found

            def jpeg(w=1600, h=1000):
                buf = io.BytesIO(); Image.new('RGB', (w, h), (20, 90, 130)).save(buf, 'JPEG', quality=80); return buf.getvalue()

            # Puntos
            listed = every_edit('points', '.edit-point', '#point-form', '#p-name', 'Puntos')
            pid = listed[0][0]
            pg.goto(f'{srv.base}/#/admin?tab=points&edit={pid}'); pg.wait_for_selector('#point-photo-form', timeout=15000)
            count = lambda: pg.evaluate(f"fetch('/api/dive-points/{pid}/photos').then(r => r.json()).then(d => d.photos.length)")
            n0 = count()
            pg.set_input_files('#point-photo-form input[name=file]', {'name': 'foto.jpg', 'mimeType': 'image/jpeg', 'buffer': jpeg(1200, 800)})
            pg.locator('#point-photo-form button[type=submit]').click()
            check('2.2 · Puntos › «Subir fotografía» sube la foto una vez (antes, dos)', toast_has('Fotografía subida') and (pg.wait_for_timeout(2500) or count() == n0 + 1), (n0, count()))
            pg.locator('#point-form a.btn', has_text='Cancelar').click(); wait_hash(pg, lambda h: h == '#/admin?tab=points')
            pg.wait_for_selector('.edit-point', timeout=15000)
            check('2.2 · Puntos › «Cancelar» vuelve a la lista de puntos (antes, a Inicio)', pg.locator('.edit-point').first.is_visible())
            pg.locator('#new-point').click(); pg.wait_for_selector('#point-form', timeout=15000)
            ok = pg.input_value('#p-name') == '' and pg.evaluate('location.hash') == '#/admin?tab=points&edit=nuevo'
            pg.fill('#p-name', 'Punto de prueba de la revisión'); pg.locator('#point-form button.btn-primary').last.click()
            wait_hash(pg, lambda h: h == '#/admin?tab=points'); pg.wait_for_selector('.edit-point', timeout=15000)
            check('2.2 · Puntos › «Nuevo punto» se crea y vuelve a la lista', ok and 'Punto de prueba de la revisión' in pg.inner_text('#app'))
            # Destinos
            every_edit('destinations', '.edit-destination', '#destination-form', '#td-title', 'Destinos')
            pg.locator('#new-destination').click(); pg.wait_for_selector('#destination-form', timeout=15000)
            pg.fill('#td-title', 'Destino de prueba'); pg.fill('#td-region', 'Islas Medas'); pg.fill('#td-kind', 'Viaje')
            pg.set_input_files('#td-file', {'name': 'd.jpg', 'mimeType': 'image/jpeg', 'buffer': jpeg()})
            pg.locator('#destination-form button.btn-primary').click()
            wait_hash(pg, lambda h: h == '#/admin?tab=destinations'); pg.wait_for_selector('.edit-destination', timeout=15000)
            row = pg.locator('tr', has_text='Destino de prueba')
            check('2.2 · Destinos › «Nuevo destino» con foto se crea y vuelve a la lista', row.count() == 1 and row.locator('img').count() == 1)
            pg.locator('.edit-destination').first.click(); pg.wait_for_selector('#destination-form', timeout=15000)
            pg.locator('#destination-form a.btn', has_text='Cancelar').click(); wait_hash(pg, lambda h: h == '#/admin?tab=destinations')
            pg.wait_for_selector('.edit-destination', timeout=15000)
            check('2.2 · Destinos › «Cancelar» vuelve a la lista', pg.locator('.edit-destination').first.is_visible())
            shot(pg, 'b2-2-destinos')
            # Plantillas
            pg.goto(f'{srv.base}/#/admin?tab=svctemplates'); pg.wait_for_selector('.st-card', timeout=15000)
            check('2.2 · Plantillas se abre por su dirección (antes, «Inicio»)', pg.evaluate("document.querySelector('.provider-tabs .active')?.dataset.tab") == 'svctemplates')
            cards = pg.eval_on_selector_all('.st-card', "cs => cs.map(c => [c.dataset.id, c.querySelector('.st-body strong').innerText.trim()])")
            bad = []
            for tid, tname in cards:
                pg.locator(f'.st-card[data-id="{tid}"] .st-edit').click()
                try:
                    pg.wait_for_selector('#st-form #stf-n-es', timeout=8000)
                    if pg.input_value('#stf-n-es') != tname: bad.append((tname, 'abre otra: ' + pg.input_value('#stf-n-es')))
                    pg.locator('#st-form footer [data-modal-close]').click(); pg.wait_for_selector('#st-form', state='detached', timeout=5000)
                except Exception as e:
                    bad.append((tname, type(e).__name__))
            check(f'2.2 · Plantillas: las {len(cards)} «Editar» abren cada una la suya y «Cancelar» cierra', cards and not bad, bad[:5])
            pg.locator(f'.st-card[data-id="{cards[0][0]}"] .st-edit').click(); pg.wait_for_selector('#st-form #stf-n-es', timeout=8000)
            pg.locator('#st-form footer button[type=submit]').click()
            check('2.2 · Plantillas › «Guardar plantilla» guarda', toast_has('Plantilla guardada'))
            pg.wait_for_selector('.st-card', timeout=15000)
            pg.locator('#st-new').click(); pg.wait_for_selector('#st-form #stf-n-es', timeout=8000)
            pg.locator('#st-form footer button[type=submit]').click()
            ok = toast_has('Escribe al menos el nombre en castellano')
            pg.fill('#stf-n-es', 'Plantilla de prueba'); pg.locator('#st-form footer button[type=submit]').click()
            ok = ok and toast_has('Plantilla guardada'); pg.wait_for_timeout(1500)
            check('2.2 · Plantillas › «Nueva plantilla» pide el nombre y se crea', ok and pg.locator('.st-card', has_text='Plantilla de prueba').count() == 1)
            pg.locator('#st-veil-save').click()
            check('2.2 · Plantillas › «Guardar intensidad» guarda', toast_has('Intensidad guardada'))
            pg.set_input_files(f'.st-card[data-id="{cards[0][0]}"] .st-file input', {'name': 'p.jpg', 'mimeType': 'image/jpeg', 'buffer': jpeg()})
            check('2.2 · Plantillas › «Poner foto / Cambiar foto» la recibe', toast_has('Foto recibida'))
            shot(pg, 'b2-2-plantillas')
            c.close()

            # 4.1 · the password only for personal data
            c, pg = ctx(); dialogs = []; pg.on('dialog', lambda d: (dialogs.append(d.message), d.dismiss()))
            login(pg, 'admin.prueba')
            pg.goto(f'{srv.base}/#/admin'); pg.wait_for_selector('.provider-tabs', timeout=15000); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(800)
            check('4.1 · entrar en el Centro de control no pide nada (antes, dos ventanas de motivo)', not dialogs and pg.locator('#wd-admin-gate').count() == 0, dialogs)
            for tabname in ('points', 'destinations', 'svctemplates', 'centers', 'experiences', 'qr', 'audit'):
                pg.goto(f'{srv.base}/#/admin?tab={tabname}'); pg.wait_for_selector('#admin-content *', timeout=15000); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(300)
            check('4.1 · gestionar la web (puntos, destinos, plantillas, centros, experiencias, QR, actividad) no pide nada',
                  not dialogs and pg.locator('#wd-admin-gate').count() == 0, dialogs)
            pg.goto(f'{srv.base}/#/admin?tab=bookings'); pg.wait_for_selector('.ab-sum', timeout=15000)
            t = pg.inner_text('#admin-content')
            check('4.1 · Reservas: en cifras y sin datos de clientes', 'En cifras' in t and 'Bahía Coralina' in t and '@' not in t and pg.locator('#wd-admin-gate').count() == 0, t[:300])
            shot(pg, 'b4-1-reservas-en-cifras')
            pg.locator('#ab-detail-open').click(); pg.wait_for_selector('#wd-admin-gate #wag-pass', timeout=8000)
            shot(pg, 'b4-1-confirmar-contrasena')
            pg.select_option('#wag-why', 'Disputa o reclamación'); pg.fill('#wag-note', 'reserva de prueba'); pg.fill('#wag-pass', 'no-es-esta')
            pg.locator('#wd-admin-gate button[type=submit]').click(); pg.wait_for_selector('.wd-gate-msg:not([hidden])', timeout=8000)
            check('4.1 · una contraseña mal lo dice en la ventana', 'no es correcta' in pg.inner_text('.wd-gate-msg'))
            pg.fill('#wag-pass', PASSWORD); pg.locator('#wd-admin-gate button[type=submit]').click()
            pg.wait_for_selector('#ab-detail-list table', timeout=15000)
            check('4.1 · con la contraseña y el motivo se abre el detalle y se ve hasta cuándo', pg.locator('#ab-detail-list tbody tr').count() > 1
                  and 'Datos personales abiertos hasta las' in pg.inner_text('#wd-conf-strip') and 'Disputa o reclamación: reserva de prueba' in pg.inner_text('#wd-conf-strip'))
            shot(pg, 'b4-1-detalle-con-motivo')
            pg.goto(f'{srv.base}/#/admin?tab=adminpay'); pg.wait_for_selector('#admin-payments', timeout=15000); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(500)
            check('4.1 · durante esos minutos, Pagos no lo vuelve a pedir', pg.locator('#wd-admin-gate').count() == 0)
            pg.locator('#wd-conf-end').click(); pg.wait_for_timeout(800)
            check('4.1 · «Cerrar ahora» cierra los datos personales', pg.locator('.wd-conf-strip').count() == 0)
            pg.goto(f'{srv.base}/#/admin?tab=users'); pg.wait_for_selector('#users-full', timeout=15000)
            masked = pg.inner_text('#admin-content')
            pg.locator('#users-full').click(); pg.wait_for_selector('#wd-admin-gate #wag-pass', timeout=8000)
            pg.fill('#wag-pass', PASSWORD); pg.locator('#wd-admin-gate button[type=submit]').click()
            pg.wait_for_selector('#users-full', state='detached', timeout=15000)
            check('4.1 · Usuarios: correos en parte y completos tras confirmar', '•••@' in masked and '•••@' not in pg.inner_text('#admin-content'))
            pg.goto(f'{srv.base}/#/admin?tab=ops'); pg.wait_for_selector('#as-form', timeout=15000)
            pg.fill('#as-min', '20'); pg.locator('#as-form button.btn-primary').click()
            check('4.1 · Operación › los minutos de la confirmación se cambian', toast_has('Guardado') and pg.evaluate("fetch('/api/admin/settings').then(r => r.json()).then(d => d.admin_confirm_minutes)") == 20)
            shot(pg, 'b4-1-ajustes')
            check('4.1 · ninguna ventana del navegador (prompt) en todo el recorrido', not dialogs, dialogs)
            c.close()

            # 4.2 · visits and bookings, without cookies. A visitor with a normal browser (the test browser says
            # «HeadlessChrome», which counts as a robot), the administration and the centre's own team.
            def figures(pg, url):
                return pg.evaluate("u => fetch(u).then(r => r.json()).then(d => Object.fromEntries(d.periods.map(p => [p.key, p])))", url)

            c, pg = ctx(); login(pg, 'admin.prueba')
            before = figures(pg, '/api/admin/contador')['todo']
            cid = pg.evaluate("fetch('/api/centers').then(r => r.json()).then(d => (d.items || []).find(x => x.name.includes('Bahía Coralina'))?.id)")
            for h in ('#/', '#/centros'):   # the administration browsing: not counted
                pg.goto(srv.base + '/' + h); pg.wait_for_load_state('networkidle')
            vis = browser.new_context(**DESK, user_agent='Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36')
            vis.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
            vp = vis.new_page(); vp.on('pageerror', lambda e: errors.append(str(e)))
            for h in ('#/', '#/centros', f'#/centro?id={cid}', '#/puntos'):
                vp.goto(srv.base + '/' + h); vp.wait_for_load_state('networkidle'); vp.wait_for_timeout(300)
            kept = vp.evaluate("[...Object.keys(localStorage), ...Object.keys(sessionStorage)].filter(k => /visit|visita|track|count/i.test(k))")
            check('4.2 · la web no deja ninguna cookie ni nada guardado para contar', not vis.cookies() and not kept, (vis.cookies(), kept))
            vis.close()
            after = figures(pg, '/api/admin/contador')['todo']
            check('4.2 · 4 pantallas de un visitante: 4 páginas vistas y 1 visitante; las de la administración no cuentan',
                  (after['views'] - before['views'], after['uniques'] - before['uniques']) == (4, 1), (before, after))
            pg.goto(f'{srv.base}/#/admin?tab=audit'); pg.wait_for_selector('#wd-counter-admin .vc-table', timeout=15000)
            t = pg.inner_text('#wd-counter-admin').lower()
            check('4.2 · Actividad: visitas y reservas de la temporada, el mes y desde el inicio',
                  all(x.lower() in t for x in ('Visitas y reservas', 'Temporada', 'Este mes', 'Desde el inicio', 'Páginas vistas', 'Visitantes únicos', 'Reservas', 'Importe reservado')), t[:400])
            shot(pg, 'b4-2-actividad-contador')
            c.close()
            c, pg = ctx(); login(pg, 'centro.prueba')
            mine = figures(pg, '/api/provider/contador')['todo']
            pg.goto(f'{srv.base}/#/centro?id={cid}'); pg.wait_for_load_state('networkidle')   # its own team: not counted for it
            t = tab(pg, 'stats', '#cb-stats-vc .vc-table')
            check('4.2 · el centro ve el mismo contador en Estadísticas: la visita a su ficha, no las de su equipo',
                  mine['views'] >= 1 and figures(pg, '/api/provider/contador')['todo']['views'] == mine['views'] and 'Visitas y reservas' in t, mine)
            shot(pg, 'b4-2-centro-estadisticas')
            c.close()

            # 4.3 · templates: icon with a preview, delete or archive, order by dragging
            c, pg = ctx(); login(pg, 'admin.prueba')
            pg.goto(f'{srv.base}/#/admin?tab=svctemplates'); pg.wait_for_selector('.st-card', timeout=15000)
            pg.locator('#st-new').click(); pg.wait_for_selector('#st-form .st-icon', timeout=8000)
            names = pg.eval_on_selector_all('#st-form .st-icon small', 'ns => ns.map(n => n.innerText.trim())')
            check('4.3 · el selector tiene todos los iconos (inmersión, bautizo, curso, salida privada, viaje, alquiler, fotografía, nocturna, snorkel…)',
                  all(n in names for n in ('Inmersión', 'Bautizo', 'Curso', 'Salida privada', 'Viaje de buceo', 'Alquiler de equipo', 'Fotografía', 'Nocturna', 'Snorkel')), names)
            pg.fill('#stf-n-es', 'Nocturna de prueba'); pg.locator('#st-form .st-icon[data-icon="nocturna"]').click()
            prev = pg.inner_html('#stf-prev')
            check('4.3 · al elegirlo se ve la tarjeta con ese icono y el nombre', 'Nocturna de prueba' in pg.inner_text('#stf-prev')
                  and pg.locator('#st-form .st-icon[data-icon="nocturna"][aria-checked="true"]').count() == 1 and 'M19.5 13.4' in prev)
            shot(pg, 'b4-3-icono-vista-previa')
            pg.locator('#st-form footer button[type=submit]').click()
            check('4.3 · se guarda con su icono', toast_has('Plantilla guardada'))
            pg.wait_for_timeout(1200)
            # delete the one nobody uses (with confirmation)
            card = pg.locator('.st-card', has_text='Nocturna de prueba')
            card.locator('.st-del').click(); pg.wait_for_selector('#wd-confirm', timeout=8000)
            check('4.3 · «Borrar» pide confirmación y dice que nadie la usa', 'Ningún centro la usa' in pg.inner_text('#wd-confirm'))
            shot(pg, 'b4-3-borrar-confirmar')
            pg.locator('#wd-confirm-ok').click()
            check('4.3 · se borra', toast_has('Plantilla borrada') and pg.wait_for_selector('.st-card', timeout=8000)
                  and pg.locator('.st-card', has_text='Nocturna de prueba').count() == 0)
            # archive one a centre uses: it says how many
            used = pg.locator('.st-card', has=pg.locator('.st-del', has_text='Archivar')).first
            uid = used.get_attribute('data-id')
            used.locator('.st-del').click(); pg.wait_for_selector('#wd-confirm', timeout=8000)
            txt = pg.inner_text('#wd-confirm')
            check('4.3 · «Archivar» si la usa algún centro, y dice cuántos', ('La usan ' in txt or 'La usa 1 ' in txt) and 'No se borra' in txt, txt)
            pg.locator('#wd-confirm-ok').click()
            ok = toast_has('Plantilla archivada'); pg.wait_for_selector(f'.st-card[data-id="{uid}"]', timeout=8000)
            arch = pg.locator(f'.st-card[data-id="{uid}"]')
            public = pg.evaluate("fetch('/api/service-catalog').then(r => r.json()).then(d => d.items.map(x => String(x.id)))")
            check('4.3 · archivada: sigue en la lista, deja de salir para servicios nuevos', ok and 'Archivada' in arch.inner_text() and uid not in public)
            shot(pg, 'b4-3-archivada')
            arch.locator('.st-restore').click()
            check('4.3 · «Recuperar» la vuelve a ofrecer', toast_has('Plantilla recuperada'))
            # order: the arrows, and dragging
            pg.wait_for_selector('.st-card', timeout=8000); pg.wait_for_timeout(800)
            first = pg.eval_on_selector_all('.st-card', 'cs => cs.map(c => c.dataset.id)')
            pg.locator('.st-card').first.locator('.st-down').click()
            ok = toast_has('Orden guardado')
            pg.reload(); pg.wait_for_selector('.st-card', timeout=15000)
            now_ = pg.eval_on_selector_all('.st-card', 'cs => cs.map(c => c.dataset.id)')
            check('4.3 · ↓ baja una plantilla y el orden se queda al volver a entrar', ok and now_[:2] == [first[1], first[0]], (first[:3], now_[:3]))
            # (the first two cards in view, below the fixed header of the web: a drop under the header lands on the header)
            pg.locator('.st-card').first.scroll_into_view_if_needed(); pg.evaluate('window.scrollBy(0, -160)'); pg.wait_for_timeout(300)
            pg.locator('.st-card').nth(1).locator('.st-grip').drag_to(pg.locator('.st-card').first, target_position={'x': 30, 'y': 120})
            ok = toast_has('Orden guardado'); pg.reload(); pg.wait_for_selector('.st-card', timeout=15000)
            dragged = pg.eval_on_selector_all('.st-card', 'cs => cs.map(c => c.dataset.id)')
            check('4.3 · arrastrar una plantilla la cambia de sitio y se guarda', ok and dragged[:2] == [now_[1], now_[0]], (now_[:3], dragged[:3]))
            shot(pg, 'b4-3-plantillas-orden')
            c.close()

            # 4.4 · QR codes with destinations chosen from a list and a short, stable address
            def phone_scan(url):
                ph = browser.new_context(**DESK, user_agent='Mozilla/5.0 (iPhone; CPU iPhone OS 17_5 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.5 Mobile/15E148 Safari/604.1')
                pp = ph.new_page(); pp.goto(url); pp.wait_for_load_state('networkidle'); final = pp.url; ph.close(); return final

            def qr_items(pg, url):
                return pg.evaluate("u => fetch(u).then(r => r.json()).then(d => d.items)", url)

            c, pg = ctx(); login(pg, 'admin.prueba')
            pg.goto(f'{srv.base}/#/admin?tab=qr'); pg.wait_for_selector('#wd-short-links .sl-module', timeout=15000)
            pg.locator('#sl-new').click(); pg.wait_for_selector('#sl-form #slf-dest', timeout=8000)
            opts = pg.eval_on_selector_all('#slf-dest option', 'os => os.map(o => [o.value, o.disabled])')
            keys = [k for k, _ in opts if k]
            check('4.4 · el destino se elige de la lista (registros, puntos, centros, experiencias, app, portada) y no hay campo de dirección',
                  keys == ['portada', 'registro_centro', 'registro_buceador', 'registro_freelance', 'puntos', 'punto', 'centros', 'centro', 'experiencias', 'experiencia', 'app']
                  and dict(opts)['app'] and pg.locator('#sl-form input[type=url]').count() == 0, opts)
            pg.fill('#slf-name', 'Recepción feria Madrid'); pg.select_option('#slf-dest', 'registro_centro'); pg.fill('#slf-cap', 'Regístrate como centro')
            pg.locator('#sl-form footer button[type=submit]').click()
            ok = toast_has('QR guardado'); pg.wait_for_selector('.sl-card', timeout=8000)
            item = next(x for x in qr_items(pg, '/api/admin/short-links') if x['name'] == 'Recepción feria Madrid')
            check('4.4 · se crea con su nombre interno y su dirección corta /q/…', ok and pg.locator('.sl-card', has_text='Recepción feria Madrid').count() == 1
                  and '/q/' in pg.inner_text('.sl-card') and item['scans'] == 0)
            card = pg.locator('.sl-card', has_text='Recepción feria Madrid')
            with pg.context.expect_page() as newp:
                card.locator('.sl-try').click()
            tp = newp.value; tp.wait_for_load_state('networkidle')
            tried = tp.url; tp.close()
            check('4.4 · «Probar enlace» abre el destino real (el registro de centros) y no cuenta como escaneo',
                  tried.endswith('#/registro?tipo=center') and next(x for x in qr_items(pg, '/api/admin/short-links') if x['id'] == item['id'])['scans'] == 0, tried)
            final = phone_scan(item['short_url'].replace(item['short_url'].split('/q/')[0], srv.base))
            check('4.4 · escanearlo con un móvil lleva al mismo sitio y suma 1 escaneo', final.endswith('#/registro?tipo=center')
                  and next(x for x in qr_items(pg, '/api/admin/short-links') if x['id'] == item['id'])['scans'] == 1, final)
            files = pg.evaluate("""id => Promise.all(['png', 'svg', 'pdf'].map(f => fetch(`/api/short-links/${id}/qr.${f}?descargar=1`)
                                     .then(r => r.arrayBuffer().then(b => [r.status, r.headers.get('content-type'), r.headers.get('content-disposition'), b.byteLength]))))""", item['id'])
            check('4.4 · descargas en PNG (alta resolución), SVG y PDF listo para imprimir', all(s_ == 200 and 'attachment' in (cd or '') for s_, _t, cd, _n in files)
                  and [t_.split(';')[0] for _s, t_, _c, _n in files] == ['image/png', 'image/svg+xml', 'application/pdf'] and files[2][3] > 5000, files)
            if cv2:
                raw = pg.evaluate("id => fetch(`/api/short-links/${id}/qr.png`).then(r => r.arrayBuffer()).then(b => Array.from(new Uint8Array(b)))", item['id'])
                full = Image.open(io.BytesIO(bytes(raw))); img = full.convert('RGB').resize((600, 600))
                text, _p, _ = cv2.QRCodeDetector().detectAndDecode(np.array(img))
                check('4.4 · el PNG (de al menos 2048 px, para imprimir grande) se lee como lo lee un móvil y lleva la dirección corta',
                      text == item['short_url'] and full.size[0] >= 2048, (text, full.size))
            # a dive site chosen with the search
            pg.locator('#sl-new').click(); pg.wait_for_selector('#sl-form #slf-dest', timeout=8000)
            pg.fill('#slf-name', 'Cartel del Cabo'); pg.select_option('#slf-dest', 'punto')
            name = pg.evaluate("fetch('/api/admin/short-links/search?tipo=punto&q=a').then(r => r.json()).then(d => d.items[0].name)")
            pg.fill('#slf-q', name[:5]); pg.wait_for_selector('#slf-results .sl-hit', timeout=8000)
            shot(pg, 'b4-4-qr-buscar-punto')
            pg.locator('#slf-results .sl-hit').first.click()
            chosen = pg.inner_text('#slf-chosen')
            pg.locator('#sl-form footer button[type=submit]').click(); ok = toast_has('QR guardado'); pg.wait_for_timeout(800)
            it2 = next(x for x in qr_items(pg, '/api/admin/short-links') if x['name'] == 'Cartel del Cabo')
            final = phone_scan(srv.base + '/q/' + it2['code'])
            check('4.4 · un punto concreto, elegido con el buscador', ok and it2['ref_name'] and it2['ref_name'] in chosen and f"#/punto?id={it2['ref_id']}" in final, (chosen, final))
            pg.reload(); pg.wait_for_selector('.sl-card', timeout=15000)
            shot(pg, 'b4-4-qr-administracion')
            c.close()
            # the centre: its own destinations, from its panel
            c, pg = ctx(); login(pg, 'centro.prueba')
            pg.goto(f'{srv.base}/#/admin?tab=qr&pt=print'); pg.wait_for_selector('#pr-pane .sl-module', timeout=15000)
            pg.locator('#sl-new').click(); pg.wait_for_selector('#sl-form #slf-dest', timeout=8000)
            keys = [k for k in pg.eval_on_selector_all('#slf-dest option', 'os => os.map(o => o.value)') if k]
            pg.fill('#slf-name', 'Mostrador · bautizo'); pg.select_option('#slf-dest', 'c_servicio')
            svc = pg.eval_on_selector('#slf-svc', 's => s.value')
            pg.locator('#sl-form footer button[type=submit]').click(); ok = toast_has('QR guardado'); pg.wait_for_selector('.sl-card', timeout=8000)
            it3 = next(x for x in qr_items(pg, '/api/center/short-links') if x['name'] == 'Mostrador · bautizo')
            final = phone_scan(srv.base + '/q/' + it3['code'])
            check('4.4 · el centro hace QR de su página de reservas, un servicio, dejar una reseña y su ficha (el del servicio abre su página de reservas en ese servicio)',
                  keys == ['c_reservas', 'c_servicio', 'c_resena', 'c_ficha'] and ok and '/c/' in final and f'servicio={svc}' in final, (keys, final))
            shot(pg, 'b4-4-qr-centro')
            c.close()
            browser.close()
    finally:
        srv.stop(); shutil.rmtree(tmp, ignore_errors=True)
    check('sin errores de JavaScript', not errors, errors[:3])
    good = sum(1 for _, ok in rows if ok)
    print(f'{good}/{len(rows)} comprobaciones')
    return good == len(rows)


if __name__ == '__main__':
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(0 if run(target) else 1)
