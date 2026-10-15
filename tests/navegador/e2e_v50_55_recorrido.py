#!/usr/bin/env python3
"""v50.55 · Encargo 1 «Pago en persona» para freelance: el recorrido completo sobre la demo, en el ordenador, en el móvil
y en el modo app, con capturas (y, de paso, «Ver salidas aquí» y «Dispositivos conectados»).

 1. Ficha pública de Sara Molina (freelance que cobra en persona): precio publicado, etiqueta y sin su WhatsApp.
 2. Bea reserva medio día: el aviso con casilla; sin la casilla no se envía; con ella, «Solicitud enviada».
 3. Antes de aceptar, Bea no ve el WhatsApp; Sara acepta y Bea ve «Confirmada · pago en persona» y «Hablar por
    WhatsApp» con el mensaje ya escrito (servicio, fecha y número de reserva).
 4. Sara marca «Cobrado» (solo para ella; Bea no lo ve).
 5. El mismo precio en la ficha, la reserva, el correo y el justificante PDF.
 6. Modo app: la hoja de reserva rápida con el aviso y la casilla; Mis reservas con «Pago en persona» y WhatsApp.

    python3 tests/navegador/e2e_v50_55_recorrido.py [carpeta-de-capturas]     (por defecto docs/capturas/v50-55)
Usa las cuentas de la demo: no va en el zip de producción (scripts/generar_zips.py, NOT_IN_PRODUCTION)."""
from __future__ import annotations

import datetime as dt
import re
import shutil
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
import e2e_v50_55_seguridad_app as SEG  # noqa: E402   (the app's user agent and the test double of the native plugin)

ROOT = Path(__file__).resolve().parents[2]
DESK = {'viewport': {'width': 1366, 'height': 900}, 'locale': 'es-ES'}
MOB = {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'locale': 'es-ES'}
NOTICE = 'Este profesional cobra directamente, no a través de WORLDIVES.'


def until(pg, expr, timeout=15000):
    end = time.time() + timeout / 1000
    while time.time() < end:
        try:
            if pg.evaluate(expr): return True
        except Exception:
            pass
        pg.wait_for_timeout(200)
    return False


def run(out: Path):
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
        sara = srv.sql("SELECT id FROM users WHERE username='freelance2.prueba'")[0]['id']
        bea = srv.sql("SELECT id FROM users WHERE username='buzo.prueba'")[0]['id']
        guia = srv.sql("SELECT id,price,pricing FROM provider_services WHERE provider_user_id=? AND title LIKE 'Guía privada%'", (sara,))[0]
        per_day = f"{float(__import__('json').loads(guia['pricing'])['day']):.0f}"     # the card shows the price per day
        busy = {r['d'] for r in srv.sql("SELECT booking_date AS d FROM bookings WHERE provider_user_id=?", (sara,))}
        day = next(d for d in (dt.date.today() + dt.timedelta(days=k) for k in range(9, 30)) if d.weekday() <= 5 and d.isoformat() not in busy).isoformat()
        cli_sara = Client(srv); assert cli_sara.login('freelance2.prueba', PASSWORD).status == 200
        cli_bea = Client(srv); assert cli_bea.login('buzo.prueba', PASSWORD).status == 200

        with sync_playwright() as pw:
            browser = chromium(pw)

            def ctx(kind, app=False):
                c = browser.new_context(**(MOB if kind == 'movil' else DESK), **({'user_agent': SEG.UA} if app else {}))
                c.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                if app: c.add_init_script(SEG.FAKE)
                pg = c.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
                return c, pg

            def login(pg, who):
                pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login-form')
                pg.fill('#login', who); pg.fill('#password', PASSWORD); pg.click('#login-form button[type=submit]')
                until(pg, "!!(window.WD ? WD.state.me : document.querySelector('.account-trigger, [data-account]'))", 8000); pg.wait_for_timeout(1200)

            def shot(pg, name, full=True):
                pg.wait_for_timeout(500); pg.screenshot(path=str(out / f'{name}.png'), full_page=full)

            # 1 · the public page of the professional ------------------------------------------------------
            for kind in ('escritorio', 'movil'):
                c, pg = ctx(kind)
                pg.goto(srv.base + f'/#/profesional?id={sara}'); until(pg, "document.body.innerText.includes('Guía privada')", 15000)
                html, text = pg.content(), pg.inner_text('body')
                check(f'{kind} · ficha del profesional con «Pago en persona» y el precio publicado', 'Pago en persona' in text and re.search(rf'{per_day}\s*€', text), text[:300])   # \s: the currency format uses a no-break space
                check(f'{kind} · su WhatsApp no está en la ficha pública', '611222333' not in re.sub(r'\D', '', html) and 'wa.me' not in html)
                shot(pg, f'{kind}-01-ficha-profesional'); c.close()

            # 2 · the booking with the notice --------------------------------------------------------------------
            c, pg = ctx('escritorio'); login(pg, 'buzo.prueba')
            pg.goto(srv.base + f'/#/reservar-dias?service={guia["id"]}&part=am&from={day}&to={day}')
            until(pg, "/€/.test((document.getElementById('dbk-total')||{}).innerText||'')", 15000)
            bar = pg.inner_text('#dbk-total')
            check('reserva · aviso del pago en persona y su casilla antes de enviar', NOTICE in pg.inner_text('body') and pg.locator('#dbk-ip-ack').count() == 1, bar)
            shot(pg, 'escritorio-02-reserva-aviso')
            n0 = srv.sql('SELECT COUNT(*) AS n FROM bookings WHERE user_id=?', (bea,))[0]['n']
            pg.click('#dbk-go'); pg.wait_for_timeout(800)
            check('reserva · sin la casilla no se envía', srv.sql('SELECT COUNT(*) AS n FROM bookings WHERE user_id=?', (bea,))[0]['n'] == n0
                  and 'Marca la casilla' in pg.inner_text('#toast'), pg.inner_text('#toast'))
            pg.check('#dbk-ip-ack'); pg.click('#dbk-go')
            until(pg, f"location.hash.includes('reserva')", 10000); pg.wait_for_timeout(1500)
            bk = srv.sql('SELECT * FROM bookings WHERE user_id=? ORDER BY id DESC LIMIT 1', (bea,))[0]
            check('reserva · con la casilla se envía como solicitud de pago en persona', bk['pay_way'] == 'in_person' and bk['status'] in ('requested', 'pending') and bk['in_person_ack_at'], dict(bk))
            shot(pg, 'escritorio-03-solicitud-enviada')
            price = float(bk['price']); money = f"{price:.0f}"
            check('precio · el de la barra es el de la reserva', money in bar.replace('.', ''), (bar, price))
            pg.goto(srv.base + f'/#/reserva?id={bk["id"]}'); pg.wait_for_timeout(2500)
            html = pg.content()
            check('antes de aceptar · sin WhatsApp del profesional', 'wa.me' not in html and '611222333' not in re.sub(r'\D', '', html))
            shot(pg, 'escritorio-04-reserva-pendiente')
            # 3 · the professional accepts -------------------------------------------------------------------------
            check('el profesional acepta', cli_sara.post(f'/api/bookings/{bk["id"]}/status', {'status': 'confirmed'}).status == 200)
            pg.reload(); pg.wait_for_timeout(2500)
            wa = pg.eval_on_selector_all('a.btn-wa', 'as=>as.map(a=>a.href)')
            text = pg.inner_text('body')
            check('aceptada · «Confirmada · pago en persona»', 'Confirmada · pago en persona' in text, text[:400])
            check('aceptada · nada dice «pagas en el centro» ni «centro de buceo» en la reserva de un profesional',
                  not any(x in text for x in ('Pagas en el centro', 'Pago en el centro', 'CENTRO DE BUCEO', 'con el centro')) and 'PROFESIONAL' in text, text[:600])
            check('aceptada · «Hablar por WhatsApp» con el mensaje ya escrito (servicio, fecha y número)', wa and wa[0].startswith('https://wa.me/34611222333')
                  and str(bk['id']) in wa[0] and 'Gu%C3%ADa' in wa[0], wa)
            shot(pg, 'escritorio-05-confirmada-whatsapp'); c.close()
            c, pg = ctx('movil'); login(pg, 'buzo.prueba'); pg.goto(srv.base + f'/#/reserva?id={bk["id"]}'); pg.wait_for_timeout(2500)
            check('móvil · la misma reserva con WhatsApp', pg.locator('a.btn-wa').count() >= 1)
            shot(pg, 'movil-02-confirmada-whatsapp'); c.close()
            # 4 · «Cobrado», only for the professional ---------------------------------------------------------------
            c, pg = ctx('escritorio'); login(pg, 'freelance2.prueba'); pg.goto(srv.base + f'/#/reserva?id={bk["id"]}')
            until(pg, "!!document.querySelector('[data-pro-mark=\"paid\"]')", 15000)
            pg.click('[data-pro-mark="paid"]'); pg.wait_for_timeout(1200)
            check('profesional · marca «Cobrado»', srv.sql('SELECT pro_mark FROM bookings WHERE id=?', (bk['id'],))[0]['pro_mark'] == 'paid')
            shot(pg, 'escritorio-06-profesional-cobrado'); c.close()
            seen = cli_bea.get(f'/api/bookings/{bk["id"]}').json
            check('el cliente no ve la marca', 'pro_mark' not in str(seen), str(seen)[:200])
            # 5 · the same price everywhere -------------------------------------------------------------------------
            mails = srv.sql("SELECT template,html FROM email_outbox WHERE to_email='bea.navarro@example.com' ORDER BY id DESC LIMIT 6")
            mail = next((m for m in mails if 'pago en persona' in (m['html'] or '').lower()), None)
            check('correo · aviso de pago en persona con el mismo precio', mail and money in (mail['html'] or ''), [m['template'] for m in mails])
            raw = cli_bea.get(f'/api/bookings/{bk["id"]}/receipt.pdf').body
            if shutil.which('pdftotext'):
                f = out / 'justificante.pdf'; f.write_bytes(raw)
                pdf = ' '.join(subprocess.run(['pdftotext', str(f), '-'], capture_output=True, text=True).stdout.split()); f.unlink()
                check('PDF · «Pago en persona», «Precio publicado» y el mismo importe', 'pago en persona' in pdf.lower() and 'Precio publicado' in pdf and money in pdf, pdf[:300])
            # 6 · app mode ----------------------------------------------------------------------------------------------
            c, pg = ctx('movil', app=True); login(pg, 'buzo.prueba')
            pg.goto(srv.base + '/#/'); until(pg, "document.querySelectorAll('#wda-salidas [data-reservar]').length > 0", 20000)
            # Diego's photo session (slots, «Pago en persona»): the same quick sheet as a card of «Salidas con plazas»
            foto = pg.evaluate("""(async () => { const d = await WD.api('/api/salidas-cercanas?limite=50'); const s = (d.items || []).find(x => /Sesión de fotos/.test(x.title));
                if (!s) return false; WDA.mem.salidas.set(String(s.slot_id), s);
                const b = document.createElement('button'); b.type = 'button'; b.dataset.reservar = String(s.slot_id); b.hidden = true; document.body.appendChild(b); b.click(); return true; })()""")
            check('app · hay una salida de pago en persona en «Salidas con plazas»', foto)
            until(pg, "!!document.getElementById('wda-aviso')", 10000)
            check('app · la hoja de reserva rápida trae el aviso y la casilla', pg.locator('#wda-aviso').count() == 1 and NOTICE in pg.inner_text('.wda-capa'))
            pg.click('#wda-confirmar'); pg.wait_for_timeout(700)
            check('app · sin la casilla no se envía', 'Marca la casilla' in pg.inner_text('#toast'), pg.inner_text('#toast'))
            shot(pg, 'app-01-reserva-rapida-aviso', full=False)
            pg.keyboard.press('Escape'); pg.goto(srv.base + '/#/reservas'); pg.wait_for_timeout(2500)
            text = pg.inner_text('body')
            check('app · Mis reservas: la reserva con «Pago en persona» y WhatsApp', 'Pago en persona' in text and 'Guía privada' in text, text[:300])
            shot(pg, 'app-02-mis-reservas', full=False)
            pg.goto(srv.base + f'/#/reserva?id={bk["id"]}'); pg.wait_for_timeout(2500)
            shot(pg, 'app-03-reserva-confirmada', full=False)
            # the point page: «Ver salidas aquí» (brief de la app)
            pid = srv.sql("SELECT sp.dive_point_id AS id FROM service_slot_points sp JOIN service_slots ss ON ss.id=sp.slot_id WHERE ss.slot_date>=date('now') AND ss.status='open' AND ss.spots_available>0 LIMIT 1")[0]['id']
            pg.goto(srv.base + f'/#/punto?id={pid}'); until(pg, "!!document.querySelector('.pp-dep-bar')", 15000)
            check('app · ficha del punto con «Ver salidas aquí»', pg.locator('.pp-dep-bar').count() == 1)
            shot(pg, 'app-04-punto-ver-salidas', full=False)
            pg.click('.pp-dep-bar button'); pg.wait_for_timeout(1200)
            shot(pg, 'app-05-punto-proximas-salidas', full=False); c.close()
            check('sin errores de JavaScript', not errors, errors[:5])
    finally:
        srv.stop()
    bad = [r for r in rows if not r[1]]
    print(f'\n{len(rows) - len(bad)}/{len(rows)} comprobaciones correctas · capturas en {out}')
    return 1 if bad else 0


if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else ROOT / 'docs' / 'capturas' / 'v50-55'
    out.mkdir(parents=True, exist_ok=True)
    sys.exit(run(out))
