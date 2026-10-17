"""Encargo 2b (v50.45): screenshots of the brand on the main screens, desktop and phone, plus an e-mail, a booking
receipt (PDF → PNG) and a poster. Run it from a checkout of any version to compare before and after:
    python tests/shots_brand.py OUT_DIR
"""
from __future__ import annotations

import subprocess
import sys
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]   # tests/navegador and tests (helpers)
from helpers import ServerTestCase, Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'


def run(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    ServerTestCase.server = Server().start(); srv = ServerTestCase.server
    try:
        t = ServerTestCase('run')
        admin = t.make_admin()
        center = t.make_center(admin, 'marca')
        cid = center.user['center_id']
        sid = center.post('/api/provider-services', {'title': 'Doble inmersión en barco', 'price': 75, 'booking_mode': 'request'}).json['id']
        center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': time.strftime('%Y') + '-12-20', 'slot_time': '09:00', 'spots_total': 8})
        pro = t.make_freelance(admin, 'marcapro')
        diver = t.make_diver('marcabuzo')
        bid = diver.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': None, 'booking_date': time.strftime('%Y') + '-12-20', 'participants': 2}).json.get('id')
        if bid:
            pdf = diver.get(f'/api/bookings/{bid}/receipt.pdf').body
            (out / 'justificante.pdf').write_bytes(pdf)
            subprocess.run(['pdftoppm', '-png', '-r', '70', '-singlefile', str(out / 'justificante.pdf'), str(out / 'justificante')], check=False)
            (out / 'justificante.pdf').unlink(missing_ok=True)
        mail = srv.sql("SELECT html FROM email_outbox WHERE html IS NOT NULL AND template LIKE 'booking%' ORDER BY id DESC LIMIT 1") or srv.sql("SELECT html FROM email_outbox WHERE html IS NOT NULL ORDER BY id DESC LIMIT 1")
        routes = [('portada', None, '#/'), ('explorar', None, '#/explorar'), ('ficha-centro', None, f'#/centro?id={cid}'), ('reserva', 'diver_marcabuzo', f'#/reservar?center={cid}'),
                  ('mis-reservas', 'diver_marcabuzo', '#/mis-reservas'), ('inicio-sesion', None, '#/login'), ('panel-centro', 'center_marca', '#/admin'),
                  ('panel-freelance', 'pro_marcapro', '#/admin'), ('administracion', 'admin', '#/admin')]
        with sync_playwright() as p:
            b = chromium(p)
            for dev, opts in (('ordenador', {'viewport': {'width': 1366, 'height': 900}}), ('movil', {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2})):
                ctxs = {}
                for name, who, route in routes:
                    if who not in ctxs:
                        ctx = b.new_context(locale='es-ES', **opts); ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                        pg = ctx.new_page()
                        if who:
                            pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login'); pg.fill('#login', who); pg.fill('#password', 'admin-seguro-2026' if who == 'admin' else PW)
                            pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1200)
                        ctxs[who] = pg
                    pg = ctxs[who]
                    pg.goto(srv.base + '/' + route); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(1300)
                    pg.screenshot(path=str(out / f'{name}-{dev}.png'), full_page=False)
                if mail and dev == 'ordenador':
                    pg = b.new_page(viewport={'width': 700, 'height': 900}); pg.set_content(mail[0]['html'].replace('http://127.0.0.1', srv.base.rsplit(':', 1)[0]).replace(srv.base.rsplit(':', 1)[0] + ':' + srv.base.rsplit(':', 1)[1], srv.base))
                    pg.wait_for_timeout(800); pg.screenshot(path=str(out / 'correo.png'), full_page=True)
            b.close()
    finally:
        srv.stop()


if __name__ == '__main__':
    run(Path(sys.argv[1]))
    print('capturas hechas')
