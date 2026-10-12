"""B1 (encargo unificado): screenshots of «Experiencias» as it is today (list, detail, booking, organizer panel and
admin), desktop and phone, on a temporary copy of the demo catalogue. No code is changed.
Usage: python tests/shots_b1_experiences.py [DIR]
"""
from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from helpers import ServerTestCase, Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402


def run(out: Path):
    out.mkdir(parents=True, exist_ok=True)
    ServerTestCase.server = Server().start(); srv = ServerTestCase.server
    try:
        t = ServerTestCase('run')
        admin = t.make_admin()
        center = t.make_center(admin, 'expb1')
        r = center.post('/api/travel-experiences', {'new_destination': 'Islas Medas', 'new_destination_region': 'España', 'title': 'Fin de semana en las Medas',
                                                    'start_date': '2026-11-14', 'end_date': '2026-11-15', 'price': 240, 'spots_total': 8, 'spots_available': 8,
                                                    'includes': '4 inmersiones, guía y botellas', 'summary': 'Dos días de buceo en la reserva marina.'})
        assert r.status == 200, r
        eid = r.json.get('id'); offer = srv.sql('SELECT travel_offer_id FROM travel_experiences WHERE id=?', (eid,))[0]['travel_offer_id']
        free = t.make_freelance(admin, 'expb1pro')
        free.post('/api/travel-experiences', {'travel_offer_id': offer, 'title': 'Medas con fotógrafo', 'start_date': '2026-11-21', 'end_date': '2026-11-22', 'price': 290, 'spots_total': 4, 'spots_available': 4})
        diver = t.make_diver('expb1buzo')
        with sync_playwright() as p:
            b = chromium(p)
            for dev, opts in (('ordenador', {'viewport': {'width': 1366, 'height': 900}}),
                              ('movil', {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2})):
                def page_for(login=None, pw='buceo-seguro-2026'):
                    ctx = b.new_context(locale='es-ES', **opts)
                    ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                    pg = ctx.new_page()
                    if login:
                        pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login'); pg.fill('#login', login); pg.fill('#password', pw)
                        pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1000)
                    return pg

                def shot(pg, route, name):
                    pg.goto(srv.base + '/' + route); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(1200)
                    pg.screenshot(path=str(out / f'{name}-{dev}.png'), full_page=True)
                pg = page_for()
                shot(pg, '#/experiencias', 'lista')
                shot(pg, f'#/experiencia?id={offer}', 'ficha')
                pg = page_for('diver_expb1buzo')
                shot(pg, f'#/experienciareserva?id={eid}', 'reserva')
                pg = page_for('center_expb1')
                shot(pg, '#/admin?tab=experiences', 'panel-centro')
                pg = page_for('pro_expb1pro')
                shot(pg, '#/admin?tab=experiences', 'panel-freelance')
                pg = page_for('admin', 'admin-seguro-2026')
                shot(pg, '#/admin?tab=experiences', 'admin')
            b.close()
    finally:
        srv.stop()


if __name__ == '__main__':
    run(Path(sys.argv[1] if len(sys.argv) > 1 else 'docs/capturas/experiencias-b1'))
    print('capturas hechas')
