#!/usr/bin/env python3
"""v50.57 · Revisión general (15/10/2026), en el navegador, sobre la demo.

Bloque 1.1 · zona horaria. El servidor arranca como en un Windows limpio (sin las zonas horarias del sistema y sin
tzdata): el panel del centro, sus reservas y su planning, y las reservas, el planning y «Mi agenda» del freelance se abren
sin error. Además, si una parte del panel falla, solo esa parte lo dice (con «Reintentar») y el resto funciona.

Bloque 1.2 · el QR de la reserva se ve en la ficha del buceador, del centro y de la administración, y al leerlo (OpenCV,
como un móvil) lleva a esa reserva.

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

            c, pg = ctx(); login(pg, 'admin.prueba')
            pg.route('**/api/admin/audit', lambda route: route.fulfill(status=500, content_type='application/json', body='{"error":"Error interno"}'))
            pg.goto(f'{srv.base}/#/admin'); pg.wait_for_selector('.provider-tabs', timeout=15000); pg.wait_for_timeout(1500)
            t = pg.inner_text('body')
            check('1.1 · administración: si falla una parte, el Centro de control se abre igual y lo dice', 'Centro de control' in t and 'No se ha podido abrir' not in t
                  and 'Actividad' in pg.inner_text('.wd-block-error'), t[:400])
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
