"""v50.47 · parte G.12 y G.13 (navegador real, Playwright): avisos masivos y recorrido completo con el entorno de pruebas.

Arranca el servidor en modo pruebas con la base del zip «-pruebas» (dos centros con buceadores en común, WhatsApp de
prueba) y Stripe simulado. Recorre la web como visitante, buceador (incluido el pago con la tarjeta 4242 simulada y
la reserva bajo petición), centro (cancelar una salida con avisos y devolución, cambio de hora, estado, informes y
exportaciones), freelance y administración (con el motivo obligatorio), en escritorio y en móvil. Falla con errores
de JavaScript, violaciones de la política de contenido o errores 500 del servidor. Guarda las capturas en
docs/capturas/v50.47/ y la lista OK / fallo en docs/pruebas/recorrido-v50.47.md.

    python tests/navegador/e2e_avisos.py
"""
from __future__ import annotations

import datetime as dt
import email
import json
import re
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(Path(__file__).resolve().parent), str(ROOT / 'tests')]
from helpers import Server, Client  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
sys.path.insert(0, str(ROOT / 'app'))
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402

CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
SHOTS = ROOT / 'docs' / 'capturas' / 'v50.47'
REPORT = ROOT / 'docs' / 'pruebas' / 'recorrido-v50.47.md'
PASSWORD = 'Worldives-Prueba-2026'
CONNECT_SECRET = 'whsec_connect_local'
VIEWS = {'escritorio': {'width': 1366, 'height': 900}, 'movil': {'width': 390, 'height': 844}}
results = []


def check(name, ok, detail=''):
    results.append((name, bool(ok), '' if ok else str(detail)[:300]))
    print(('OK   ' if ok else 'FALLA') + ' ' + name + ('' if ok else f'  → {detail}'))


def shot(page, name):
    SHOTS.mkdir(parents=True, exist_ok=True)
    page.screenshot(path=str(SHOTS / f'{name}.jpg'), type='jpeg', quality=62, full_page=False)


def eml_part(path, ctype):
    msg = email.message_from_bytes(Path(path).read_bytes())
    part = next((x for x in msg.walk() if x.get_content_type() == ctype), None)
    return part.get_payload(decode=True).decode(part.get_content_charset() or 'utf-8') if part else ''


def main():
    stripe = StripeMock()
    tmpdb = Path('/tmp') / f'wod-e2e47-{int(time.time())}.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(tmpdb)], capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stdout + r.stderr)
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'WOD_ALLOW_SETUP': '1', 'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': stripe.base, 'STRIPE_CONNECT_WEBHOOK_SECRET': CONNECT_SECRET,
                  'WOD_AVISOS_DESHACER_SEGUNDOS': '10', 'WOD_AVISOS_SEGUNDOS': '1', 'WOD_MAINTENANCE_SECONDS': '3'}, seed=tmpdb).start()
    errors_500 = []
    try:
        base = srv.base
        # --- the owner creates the administrator (only in the test environment) --------------------------------
        adm = Client(srv)
        check('Entrar con la cuenta de administración de la demo (CUENTAS-DEMO.txt)', adm.login('admin.prueba', PASSWORD).status == 200)
        center, center2, buzo, buzo2, buzo3 = (Client(srv) for _ in range(5))
        for c, u in ((center, 'centro.prueba'), (center2, 'centro2.prueba'), (buzo, 'buzo.prueba'), (buzo2, 'buzo2.prueba'), (buzo3, 'buzo3.prueba')):
            assert c.login(u, PASSWORD).status == 200, u
        cid = center.me()['user']['center_id']
        # A departure with a paid booking (simulated 4242 card) and two more divers: the one cancelled with refunds
        svc = [s for s in center.get(f'/api/provider-services?center_id={cid}').json['items'] if s['title'] == 'Inmersión simple en barco'][0]
        slot = svc['slots'][3]
        rb = buzo3.post('/api/bookings', {'center_id': cid, 'service_id': svc['id'], 'slot_id': slot['id'], 'participants': 1, 'wa_consent': True})
        if not stripe.sessions: raise SystemExit(f'Sin sesión de Stripe: {rb} {svc["booking_mode"]} {slot}')
        sess = stripe.last_session(); stripe.pay(sess['id'])
        ev = {'id': f'evt_{time.time_ns()}', 'type': 'checkout.session.completed', 'account': 'acct_test_pruebas', 'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
        payload, sig = StripeMock.signed(ev, CONNECT_SECRET)
        Client(srv, origin=None).request('POST', '/api/payments/webhook/connect', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
        paid = srv.sql('SELECT status,payment_status FROM bookings WHERE id=?', (rb.json['id'],))[0]
        check('Buceador: pago con la tarjeta 4242 (Stripe simulado) → reserva confirmada y pagada', paid == {'status': 'confirmed', 'payment_status': 'paid'}, paid)
        for d in (buzo, buzo2):
            x = d.post('/api/bookings', {'center_id': cid, 'service_id': svc['id'], 'slot_id': slot['id'], 'participants': 1}).json['id']
            srv.sql("UPDATE bookings SET status='confirmed',payment_status='at_center' WHERE id=?", (x,))
        # Request mode
        doble = [s for s in center.get(f'/api/provider-services?center_id={cid}').json['items'] if s['title'] == 'Doble inmersión en barco'][0]
        rq = buzo2.post('/api/bookings', {'center_id': cid, 'service_id': doble['id'], 'slot_id': doble['slots'][5]['id'], 'participants': 1})
        check('Buceador: reserva bajo petición → «solicitada»', rq.status == 200 and srv.sql('SELECT status FROM bookings WHERE id=?', (rq.json['id'],))[0]['status'] == 'requested', rq)
        check('Centro: aceptar la solicitud', center.post(f"/api/bookings/{rq.json['id']}/status", {'status': 'confirmed'}).status == 200)

        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=CHROME)

            def new(view, login=None, lang='es'):
                ctx = b.new_context(viewport=VIEWS[view], locale='es-ES', device_scale_factor=1)
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")   # cookie notice already read
                pg = ctx.new_page(); pg.errs = []
                pg.on('console', lambda m, pg=pg: pg.errs.append(m.text) if m.type == 'error' and 'favicon' not in m.text else None)
                pg.on('pageerror', lambda e, pg=pg: pg.errs.append('pageerror: ' + str(e)))
                pg.on('response', lambda resp: errors_500.append(resp.url) if resp.status >= 500 else None)
                pg.on('dialog', lambda d: d.accept('Revisión del recorrido de pruebas v50.47') if d.type == 'prompt' else d.accept())
                pg.goto(base + '/#/' + (f'?lang={lang}' if lang != 'es' else ''))
                if login:
                    pg.goto(base + '/#/login'); pg.wait_for_selector('#login-form, form', timeout=15000)
                    st = pg.evaluate("""async ([u,pw])=>{ const r=await fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({login:u,password:pw})}); return r.status; }""", list(login))
                    assert st == 200, (login[0], st)
                    pg.goto(base + '/#/'); pg.reload(); pg.wait_for_timeout(600)
                return ctx, pg

            def visit(pg, route, wait='main, .page, section', name=None, settle=900):
                pg.goto(base + '/' + route); pg.wait_for_timeout(settle)
                try: pg.wait_for_selector(wait, timeout=8000)
                except Exception: pass
                # Phone: no page may be wider than the screen (no horizontal scroll of the whole page).
                over = pg.evaluate("()=>document.documentElement.scrollWidth-window.innerWidth")
                if over > 1: pg.errs.append(f'overflow: {route} es {over}px más ancha que la pantalla')
                if name: shot(pg, name)

            def no_errors(pg, label):
                bad = [e for e in pg.errs if 'Content Security Policy' in e or 'pageerror' in e or 'TypeError' in e or 'ReferenceError' in e]
                check(f'{label}: sin errores de JavaScript ni de política de contenido', not bad, bad[:3])
                wide = [e for e in pg.errs if e.startswith('overflow:')]
                check(f'{label}: ninguna página más ancha que la pantalla', not wide, wide[:3]); pg.errs.clear()

            for view in VIEWS:
                # --- visitor -------------------------------------------------------------------------------------
                ctx, pg = new(view)
                for route, nm in (('#/', 'portada'), ('#/explorar', 'explorar'), ('#/centros', 'centros'), (f'#/centro?id={cid}', 'ficha-centro'), ('#/experiencias', 'experiencias')):
                    visit(pg, route, name=f'{view}-visitante-{nm}' if nm in ('portada', 'ficha-centro') else None)
                no_errors(pg, f'Visitante ({view})'); ctx.close()
                # --- diver ---------------------------------------------------------------------------------------
                ctx, pg = new(view, ('buzo2.prueba', PASSWORD))
                visit(pg, '#/cuenta', '#p-phone-num', name=f'{view}-buceador-telefono-y-permiso')
                ok_prefix = pg.locator('#p-phone-cc').count() == 1 and pg.locator('#p-wa').count() == 1
                check(f'Buceador ({view}): móvil con selector de prefijo y casilla de permiso de WhatsApp', ok_prefix)
                pg.fill('#p-phone-num', '6112'); pg.wait_for_timeout(200); SHOTS.mkdir(parents=True, exist_ok=True); pg.locator('.ph-field').screenshot(path=str(SHOTS / f'{view}-buceador-aviso-telefono.jpg'), type='jpeg', quality=70)
                warn = pg.locator('#p-phone-warn').inner_text()
                pg.select_option('#p-phone-cc', 'ES'); pg.fill('#p-phone-num', '611 000 101'); pg.wait_for_timeout(200)
                check(f'Buceador ({view}): aviso «Revisa el número…» con un número corto y sin aviso con el correcto', 'prefijo' in warn and not pg.locator('#p-phone-warn').inner_text(), warn)
                visit(pg, '#/area', name=f'{view}-buceador-mi-area')
                no_errors(pg, f'Buceador ({view})'); ctx.close()
                # --- freelance -----------------------------------------------------------------------------------
                ctx, pg = new(view, ('freelance.prueba', PASSWORD))
                visit(pg, '#/admin?tab=agenda', '.cb-main', name=f'{view}-freelance-agenda' if view == 'escritorio' else None)
                visit(pg, '#/admin?tab=avisos', '.nt-panel')
                no_errors(pg, f'Freelance ({view})'); ctx.close()

            # --- centre: cancel the departure with notices and refunds (desktop) and the change of time (mobile) --
            ctx, pg = new('escritorio', ('centro.prueba', PASSWORD))
            visit(pg, '#/admin?tab=avisos', '.nt-panel', name='escritorio-centro-avisos-y-whatsapp')
            visit(pg, f'#/manifiesto?slot={slot["id"]}', '#mf-cancel', name='escritorio-centro-boton-cancelar-y-avisar')
            pg.click('#mf-cancel'); pg.wait_for_selector('#nt-confirm', timeout=15000)
            pg.check('input[name="nt-reason"][value="sea"]'); pg.fill('#nt-note', 'Mar de fondo de 2 metros')
            pg.check('input[name="nt-policy"][value="refund"]'); pg.wait_for_timeout(1200)
            shot(pg, 'escritorio-centro-confirmacion-cancelar')
            txt = pg.locator('#nt-preview').inner_text()
            check('Confirmación: salida, recuento por canal, nombres con inicial, dinero y mensaje por idioma',
                  all(s in txt for s in ('WhatsApp', 'Correo', 'App', 'Bea N.', 'Devolución de', 'Mensaje que recibe')), txt[:300])
            check('El botón queda desactivado hasta escribir la fecha', pg.locator('#nt-ok').is_disabled())
            hint = pg.locator('#nt-preview .nt-confirm b').inner_text()
            pg.fill('#nt-confirm', hint); pg.wait_for_timeout(200)
            check('Escribiendo la fecha se activa el botón', not pg.locator('#nt-ok').is_disabled())
            pg.locator('.nt-msg').scroll_into_view_if_needed(); pg.wait_for_timeout(200)
            shot(pg, 'escritorio-centro-confirmacion-mensaje-y-fecha')
            pg.click('#nt-ok'); pg.wait_for_selector('#ns-undo', timeout=10000)
            shot(pg, 'escritorio-centro-deshacer-10-segundos')
            check('Tras confirmar: «Deshacer» y cuenta atrás antes de enviar', pg.locator('#ns-left').count() == 1)
            pg.wait_for_function("()=>!document.querySelector('#ns-undo') && document.querySelector('.ns-table')", timeout=40000)
            pg.wait_for_function("()=>!document.querySelector('.ns-queued,.ns-sending')", timeout=40000)
            shot(pg, 'escritorio-centro-panel-de-estado')
            st = pg.locator('#ns-body').inner_text()
            check('Panel de estado: cada buceador y canal', st.count('Enviado') >= 6 or st.count('Entregado') >= 6, st[:300])
            pg.click('[data-modal-close]'); pg.wait_for_timeout(300)
            visit(pg, '#/admin?tab=planning', '.cb-main', name='escritorio-centro-planning')
            visit(pg, '#/admin?tab=analytics', '.cb-main', name='escritorio-centro-informes')
            no_errors(pg, 'Centro (escritorio)'); ctx.close()

            ctx, pg = new('movil', ('centro.prueba', PASSWORD))
            visit(pg, '#/admin?tab=avisos', '.nt-panel', name='movil-centro-avisos-y-whatsapp')
            slot2 = [s for s in doble['slots'] if s['id'] != doble['slots'][5]['id']][4]
            for d in (buzo, buzo3):
                x = d.post('/api/bookings', {'center_id': cid, 'service_id': doble['id'], 'slot_id': slot2['id'], 'participants': 1}).json['id']
                srv.sql("UPDATE bookings SET status='confirmed' WHERE id=?", (x,))
            visit(pg, f'#/manifiesto?slot={slot2["id"]}', '#mf-change', name='movil-centro-botones-avisos')
            pg.click('#mf-change'); pg.wait_for_selector('#nt-time', timeout=15000)
            pg.fill('#nt-time', '10:30'); pg.fill('#nt-point', 'Puerto de Xàbia, pantalán 3'); pg.wait_for_timeout(1500)
            shot(pg, 'movil-centro-confirmacion-cambio-de-hora')
            pg.fill('#nt-confirm', pg.locator('#nt-preview .nt-confirm b').inner_text()); pg.click('#nt-ok')
            pg.wait_for_selector('#ns-undo', timeout=10000); shot(pg, 'movil-centro-deshacer')
            pg.wait_for_function("()=>!document.querySelector('#ns-undo') && document.querySelector('.ns-table')", timeout=40000)
            pg.wait_for_function("()=>!document.querySelector('.ns-queued,.ns-sending')", timeout=40000)
            shot(pg, 'movil-centro-panel-de-estado')
            check('Cambio de hora: la salida y las reservas pasan a las 10:30', srv.sql('SELECT slot_time FROM service_slots WHERE id=?', (slot2['id'],))[0]['slot_time'] == '10:30')
            no_errors(pg, 'Centro (móvil)'); ctx.close()

            # --- results of the cancellation: refunds, isolation, examples of WhatsApp, email and app notice ------
            time.sleep(3)
            check('Devolución en la cuenta Stripe del centro (una sola vez)', [x.get('account') for x in stripe.refunds] == ['acct_test_pruebas'], stripe.refunds)
            other = srv.sql("SELECT COUNT(*) n FROM notice_outbox WHERE provider_id<>?", (f'c:{cid}',))[0]['n']
            check('Ningún aviso a reservas del segundo centro', other == 0, other)
            avisos = srv.tmp / 'avisos'
            wa = sorted((avisos / f'c-{cid}' / 'whatsapp').glob('*.json')) if (avisos / f'c-{cid}').exists() else []
            wa.sort(key=lambda f: ('salida_cancelada' not in f.read_text(encoding='utf-8'), '"idioma": "es"' not in f.read_text(encoding='utf-8')))
            check('WhatsApp de prueba guardado en local, en la carpeta del centro', bool(wa) and not (avisos / f"c-{srv.sql('SELECT center_id FROM users WHERE username=?', ('centro2.prueba',))[0]['center_id']}").exists())
            if wa:
                m = json.loads(wa[0].read_text(encoding='utf-8'))
                html = f"""<!doctype html><meta charset="utf-8"><body style="margin:0;font:15px system-ui;background:#efeae2"><div style="background:#075e54;color:#fff;padding:14px 16px"><b>{m['desde']}</b><br><small>WhatsApp Business · plantilla {m['plantilla']} ({m['idioma']})</small></div>
                <div style="max-width:420px;margin:18px;background:#fff;border-radius:10px 10px 10px 2px;padding:10px 12px;box-shadow:0 1px 1px rgba(0,0,0,.15)">{m['texto']}<div style="border-top:1px solid #eee;margin-top:8px;padding-top:8px;text-align:center;color:#0a7cff;font-weight:600">{m.get('boton_texto', '')}</div></div>
                <p style="margin:0 18px;color:#54656f;font-size:12px">Enlace del botón: {m.get('boton', '')}<br>Para: {m.get('para', '')}</p></body>"""
                for view in VIEWS:
                    ctx = b.new_context(viewport=VIEWS[view]); pg = ctx.new_page(); pg.set_content(html); shot(pg, f'{view}-ejemplo-whatsapp'); ctx.close()
            emls = sorted((srv.tmp / 'mail').glob('*.eml'))
            texts = {f: eml_part(f, 'text/plain') for f in emls}
            pick = [f for f in emls if 'Mar de fondo' in texts[f] and 'Hola' in texts[f]] or [f for f in emls if 'Mar de fondo' in texts[f]]
            check('Correo de la cancelación con el motivo y la nota del centro', bool(pick), [texts[f][:200] for f in emls[-3:]])
            if emls:
                html = eml_part((pick or emls)[-1], 'text/html')
                for view in VIEWS:
                    ctx = b.new_context(viewport=VIEWS[view]); pg = ctx.new_page(); pg.set_content(html); shot(pg, f'{view}-ejemplo-correo'); ctx.close()
            check('Correo del aviso guardado en local (entorno de pruebas: nunca se envía)', bool(emls))
            for view in VIEWS:
                ctx, pg = new(view, ('buzo3.prueba', PASSWORD))
                visit(pg, '#/area', '#acc-messages')
                pg.wait_for_timeout(600); pg.locator('#acc-messages').screenshot(path=str(SHOTS / f'{view}-ejemplo-aviso-en-la-app.jpg'), type='jpeg', quality=70)
                body = [m_['body'] for m_ in buzo3.get('/api/me/area').json['messages'] if '/r/' in (m_['body'] or '')]
                if body:
                    link = re.search(r'/r/([0-9a-z]+\.[cmr]\.[0-9a-z]+\.[A-Za-z0-9_\-]+)', body[0]).group(1)
                    visit(pg, f'#/r/{link}', '.auth-card, .page, main', name=f'{view}-enlace-del-aviso')
                    check(f'Enlace del aviso ({view}): abre solo esa reserva', 'WOD-' in pg.locator('body').inner_text() or 'Salida cancelada' in pg.locator('body').inner_text())
                no_errors(pg, f'Buceador con aviso ({view})'); ctx.close()

            # --- second centre: sees only its own -----------------------------------------------------------------
            ctx, pg = new('escritorio', ('centro2.prueba', PASSWORD))
            visit(pg, '#/admin?tab=bookings', '.cb-main', name='escritorio-centro2-solo-sus-reservas')
            check('Segundo centro: la reserva del primero da 404', center2.get(f"/api/bookings/{rb.json['id']}").status == 404)
            no_errors(pg, 'Segundo centro'); ctx.close()

            # --- reports and exports --------------------------------------------------------------------------------
            for kind in ('bookings', 'clients', 'payments'):
                r_ = center.get(f'/api/center/export?kind={kind}')
                check(f'Exportación «{kind}» del centro', r_.status == 200 and len(r_.body) > 20, r_.status)
            r_ = center.get(f"/api/bookings/{rb.json['id']}/receipt.pdf")
            check('Justificante PDF de una reserva del centro', r_.status == 200 and r_.body[:4] == b'%PDF', r_.status)
            check('Justificante PDF de otro centro: 404', center2.get(f"/api/bookings/{rb.json['id']}/receipt.pdf").status == 404)

            # --- administration (with the mandatory reason) ---------------------------------------------------------
            # v50.57 (4.1): the bookings of the centres are shown in figures without asking anything; their detail (data
            # of clients) asks for the password and a reason, in the web's own window, and the reason is logged.
            ctx, pg = new('escritorio', ('admin.prueba', PASSWORD))
            visit(pg, '#/admin?tab=claims', '.page, main', name='escritorio-admin-verificaciones')
            visit(pg, '#/admin?tab=bookings', '.page, main', name='escritorio-admin-reservas-con-motivo', settle=2000)
            pg.click('#ab-detail-open'); pg.wait_for_selector('#wag-form', timeout=10000)
            pg.fill('#wag-note', 'Revisión del recorrido de pruebas v50.47'); pg.fill('#wag-pass', PASSWORD)
            pg.click('button[type=submit][form=wag-form]'); pg.wait_for_selector('#ab-detail-list .bk-row, #ab-detail-list tr, #ab-detail-list .empty', timeout=15000); pg.wait_for_timeout(800)
            logged = srv.sql("SELECT details FROM audit_log WHERE action='admin_center_access' ORDER BY id DESC LIMIT 1")
            check('Administración: el detalle de las reservas pide contraseña y motivo, y el motivo queda en el registro', bool(logged) and 'Revisión del recorrido' in logged[0]['details'], logged)
            no_errors(pg, 'Administración'); ctx.close()
            b.close()
        check('Sin errores 500 del servidor en todo el recorrido', not errors_500, errors_500[:5])
    finally:
        srv.stop(); stripe.stop(); tmpdb.unlink(missing_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    lines = ['# Recorrido completo v50.47 (navegador real)', '', f'Fecha: {dt.date.today().isoformat()}. Entorno de pruebas (base del zip «-pruebas», dos centros, WhatsApp de prueba, Stripe simulado). '
             'Escritorio 1366×900 y móvil 390×844. Capturas en `docs/capturas/v50.47/`.', '', '| Resultado | Comprobación |', '|---|---|']
    lines += [f"| {'OK' if ok else 'FALLO'} | {name}{(' — ' + det) if det else ''} |" for name, ok, det in results]
    lines += ['', f"**Total: {sum(1 for _, ok, _ in results if ok)} OK, {sum(1 for _, ok, _ in results if not ok)} fallos.**"]
    REPORT.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    print(f"\n{sum(1 for _, ok, _ in results if ok)} OK · {sum(1 for _, ok, _ in results if not ok)} fallos → {REPORT.relative_to(ROOT)}")
    return 0 if all(ok for _, ok, _ in results) else 1


if __name__ == '__main__':
    sys.exit(main())
