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
            c, pg = ctx(); login(pg, 'admin.prueba')
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
