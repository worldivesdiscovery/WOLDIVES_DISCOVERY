#!/usr/bin/env python3
"""v50.56 · README-PRUEBAS «Probar el motor multicanal», paso a paso sobre la demo y en un navegador real:

 1. En la web de ejemplo del centro (http://localhost:8101, la que sirve «iniciar --pruebas»), «Snorkel en la
    Granadella» (salidas de 2 plazas): una solicitud de 1 persona desde el calendario.
 2. centro.prueba la ve al momento en el panel, con la etiqueta «Tu web», y la acepta: en WORLDIVES (la ficha del
    centro) esa salida pasa de 2 plazas a 1.
 3. buzo.prueba reserva la última plaza en WORLDIVES y el centro la acepta: la ficha dice «Completa» y la web de
    ejemplo, «Completo».
 4. El centro cancela la reserva que entró por la web: la plaza vuelve a estar libre en WORLDIVES y en la web de
    ejemplo.

    python3 tests/navegador/e2e_v50_56_demo_multicanal.py [carpeta-de-capturas]

Usa las cuentas de la demo y la web de ejemplo: no va en el zip de producción (scripts/generar_zips.py)."""
from __future__ import annotations

import subprocess
import sys
import tempfile
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app'),
                str(Path(__file__).resolve().parents[2] / 'scripts')]
from helpers import Client, Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402
from crear_demo import PASSWORD  # noqa: E402
from iniciar import example_site  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DESK = {'viewport': {'width': 1366, 'height': 900}, 'locale': 'es-ES'}


def run(out: Path | None):
    rows = []

    def check(name, ok, detail=''):
        rows.append((name, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + name + ('' if ok else f'  → {str(detail)[:300]}'), flush=True)

    tmp = Path(tempfile.mkdtemp(prefix='wod-demo-')) / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(tmp)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=tmp).start()
    errors = []
    try:
        site = example_site(srv.base, str(srv.db), '127.0.0.1')
        assert site, 'el puerto 8101 está ocupado'
        cid = srv.sql("SELECT provider_id FROM sales_settings WHERE slug='bahia-coralina'")[0]['provider_id']
        sid = srv.sql("SELECT id FROM provider_services WHERE center_id=? AND title='Snorkel en la Granadella'", (cid,))[0]['id']
        html = (ROOT / 'data' / 'pruebas' / 'web-centro' / 'index.html').read_text(encoding='utf-8')
        check('la web de ejemplo lleva el widget de Bahía Coralina en sus 3 formatos',
              all(f'data-worldives="{f}"' in html for f in ('boton', 'calendario', 'lista')) and 'data-centro="bahia-coralina"' in html and f'data-servicio="{sid}"' in html)
        slot = srv.sql("SELECT id, slot_date, slot_time FROM service_slots WHERE service_id=? ORDER BY slot_date LIMIT 1", (sid,))[0]
        free = lambda: srv.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot['id'],))[0]['spots_available']
        center = Client(srv); assert center.login('centro.prueba', PASSWORD).status == 200
        bea = Client(srv); assert bea.login('buzo.prueba', PASSWORD).status == 200
        check('la salida empieza con 2 plazas', free() == 2, free())

        with sync_playwright() as pw:
            browser = chromium(pw)

            def ctx():
                c = browser.new_context(**DESK)
                c.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg = c.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
                return c, pg

            def shot(pg, name, full=False):
                if not out: return
                out.mkdir(parents=True, exist_ok=True); pg.wait_for_timeout(400)
                if full:
                    # Chromium only paints the iframes that are on screen: a viewport as tall as the page, then back
                    pg.set_viewport_size({'width': DESK['viewport']['width'], 'height': pg.evaluate('document.scrollingElement.scrollHeight')}); pg.wait_for_timeout(900)
                pg.screenshot(path=str(out / f'{name}.png'))
                if full: pg.set_viewport_size(DESK['viewport'])

            def widget_day(pg):
                """The calendar of the example website on the day of the departure: the text of its time (v50.58: the strip of
                14 days of the express booking; a later day through «Más fechas»)."""
                pg.goto(site); cal = pg.frame_locator('#calendario iframe')
                cal.locator('.wr-strip .wr-dchip').first.wait_for(timeout=15000)
                chip = cal.locator(f'.wr-dchip[data-day="{slot["slot_date"]}"]')
                if chip.count(): chip.click()
                else: cal.locator('[data-more]').click(); cal.locator(f'[data-cal="{slot["slot_date"]}"]').click()
                cal.locator('.wr-time').first.wait_for(timeout=8000)
                return cal, cal.locator('.wr-time').first.inner_text()

            def worldives_slot(pg):
                """The same departure on the page of the centre in WORLDIVES."""
                pg.goto(f'{srv.base}/#/centro?id={cid}'); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(1200)
                link = pg.locator(f'a.cp-slot[href*="slot={slot["id"]}"]')
                if link.count(): return link.first.inner_text()
                # A full departure is not a link: the card of the service shows it as «Completa»
                card = pg.locator('article, section, div').filter(has_text='Snorkel en la Granadella').locator('span.cp-slot.is-full')
                return ' | '.join(card.all_inner_texts())

            # 1. A request from the example website (calendar format)
            c, pg = ctx()
            cal, txt = widget_day(pg)
            check('1 · la web de ejemplo enseña la salida con 2 plazas', 'Quedan 2' in txt, txt)
            if not cal.locator('.wr-time[aria-checked="true"]').count(): cal.locator('.wr-time').first.click()
            cal.locator('[data-primary]:not([disabled])').click(); cal.locator('[data-form]').wait_for(timeout=8000)
            cal.locator('input[name=fullname]').fill('Paula Web'); cal.locator('input[name=email]').fill('paula.web@example.org')
            cal.locator('input[name=accept_policy]').check(); cal.locator('[data-primary]').click()
            cal.locator('.wr-done h2').wait_for(timeout=15000)
            check('1 · «Solicitud enviada» en la web del centro', 'Solicitud enviada' in cal.locator('.wr-done').inner_text())
            pg.wait_for_timeout(600)
            fh = pg.evaluate("document.querySelector('#calendario iframe').getBoundingClientRect().height")
            bh = cal.locator('body').evaluate('b => b.getBoundingClientRect().height')
            check('1 · el recuadro del widget se ajusta a lo que enseña (también al encoger)', abs(fh - bh) <= 4, (fh, bh))
            shot(pg, 'demo-1-web-ejemplo-solicitud', True)
            c.close()
            bid = srv.sql("SELECT id FROM bookings WHERE service_id=? AND channel='widget' ORDER BY id DESC LIMIT 1", (sid,))[0]['id']
            row = srv.sql('SELECT status, channel_origin, slot_reserved FROM bookings WHERE id=?', (bid,))[0]
            check('1 · solicitud con su canal y su web, sin tomar plaza todavía', (row['status'], row['channel_origin'], row['slot_reserved']) == ('requested', 'localhost:8101', 0) and free() == 2, row)

            # 2. The centre sees it in its panel (channel «Tu web») and accepts it
            c, pg = ctx()
            pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login-form')
            pg.fill('#login', 'centro.prueba'); pg.fill('#password', PASSWORD); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1500)
            pg.goto(srv.base + '/#/admin?tab=bookings'); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(1800)
            main = pg.inner_text('main')
            check('2 · el centro ve la solicitud en «Reservas» con la etiqueta «Tu web»', 'Paula' in main and 'Tu web' in main, main[:400])
            shot(pg, 'demo-2-panel-reservas-tu-web')
            c.close()
            r = center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})
            check('2 · el centro la acepta', r.status == 200, r)
            check('2 · en WORLDIVES queda 1 plaza', free() == 1, free())
            c, pg = ctx()
            txt = worldives_slot(pg)
            check('2 · la ficha del centro en WORLDIVES dice «1 plaza»', '1 plaza' in txt, txt)
            shot(pg, 'demo-2-worldives-1-plaza')
            c.close()

            # 3. Bea takes the last spot in WORLDIVES; the centre accepts it
            r = bea.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot['id'], 'participants': 1})
            check('3 · buzo.prueba reserva la última plaza en WORLDIVES', r.status == 200, r)
            r2 = center.post(f"/api/bookings/{r.json['id']}/status", {'status': 'confirmed'})
            check('3 · el centro la acepta y la salida queda completa', r2.status == 200 and free() == 0, (r2.status, free()))
            c, pg = ctx()
            txt = worldives_slot(pg)
            check('3 · la ficha del centro en WORLDIVES dice «Completa»', 'Completa' in txt, txt)
            cal, txt = widget_day(pg)
            check('3 · la web de ejemplo dice «Completo»', 'Completo' in txt, txt)
            cal.locator('.wr-time').first.click(); cal.locator('[data-alt]').wait_for(timeout=8000)
            check('3 · y no deja elegirla (propone otras horas o días)', cal.locator('.wr-time[aria-checked="true"]').count() == 0)
            shot(pg, 'demo-3-web-ejemplo-completo', True)
            c.close()

            # 4. The centre cancels the booking of the website: the spot is free again everywhere at once
            r = center.post(f'/api/bookings/{bid}/status', {'status': 'cancelled', 'reason': 'El cliente no puede venir'})
            check('4 · el centro cancela la reserva de la web', r.status == 200 and free() == 1, (r.status, free()))
            c, pg = ctx()
            cal, txt = widget_day(pg)
            check('4 · la web de ejemplo vuelve a ofrecer la plaza', 'Completo' not in txt and 'Queda 1' in txt, txt)
            shot(pg, 'demo-4-web-ejemplo-plaza-libre', True)
            txt = worldives_slot(pg)
            check('4 · y WORLDIVES también', '1 plaza' in txt, txt)
            c.close()
            browser.close()
        check('sin errores de JavaScript', not errors, errors)
    finally:
        srv.stop()
    print(f"{sum(1 for _, ok in rows if ok)}/{len(rows)} comprobaciones")
    return all(ok for _, ok in rows)


if __name__ == '__main__':
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(0 if run(target) else 1)
