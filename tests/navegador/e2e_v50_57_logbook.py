#!/usr/bin/env python3
"""v50.57 · Log Book con el componente «Dive Logbook», en el navegador, sobre una copia de la demo.

Los 7 criterios de aceptación del encargo:
1. La lista se ve integrada en escritorio y en móvil, con la letra de la web.
2. Un usuario nuevo ve el icono del pasaporte en gris; al pulsarlo sale la explicación y no se abre.
3. Escanear el QR de una inmersión la añade verificada y desbloquea el pasaporte; escanearlo otra vez no la duplica.
4. Registrarse con el enlace de un centro pone su logo en la portada y desbloquea.
5. Escanear el QR de otro buceador lo añade como amigo y aparece en «Compañero».
6. Los datos persisten entre dispositivos y son los mismos en las dos vistas.
7. Los campos bloqueados de una inmersión verificada no se pueden cambiar, ni manipulando la petición.

    python3 tests/navegador/e2e_v50_57_logbook.py [carpeta-de-capturas]

Usa las cuentas de la demo: no va en el zip de producción (scripts/generar_zips.py)."""
from __future__ import annotations

import json
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
try:
    import cv2  # noqa: E402
    import numpy as np  # noqa: E402
except ImportError:   # without OpenCV the QR is checked on screen but not read
    cv2 = None
from PIL import Image, ImageDraw  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DESK = {'viewport': {'width': 1366, 'height': 900}, 'locale': 'es-ES'}
PHONE = {'viewport': {'width': 390, 'height': 844}, 'locale': 'es-ES', 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}
LB = 'DiveLogbook.instances.filter(i=>i.root.isConnected).at(-1)'


def read_qr(png: bytes) -> str:
    if cv2 is None: return ''
    img = cv2.imdecode(np.frombuffer(png, np.uint8), cv2.IMREAD_COLOR)
    return cv2.QRCodeDetector().detectAndDecode(img)[0] or ''


def run(out: Path | None):
    rows = []

    def check(name, ok, detail=''):
        rows.append((name, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + name + ('' if ok else f'  → {str(detail)[:400]}'), flush=True)

    tmp = Path(tempfile.mkdtemp(prefix='wod-logbook-'))
    db = tmp / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(db)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    # Registration is closed in demo mode (WOD_DEMO_MODE=1): this copy runs as a normal site, with the demo's accounts.
    srv = Server({'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': '', 'PYTHONUNBUFFERED': '1'}, seed=db).start()
    cid = srv.sql("SELECT center_id FROM users WHERE username='centro.prueba'")[0]['center_id']
    srv.sql("UPDATE centers SET verification_status='verified' WHERE id=?", (cid,))   # public outside the demo mode
    errors, csp = [], []
    # a logo with a transparent background, as the brief asks the centres
    logo = tmp / 'logo-centro.png'
    im = Image.new('RGBA', (256, 256), (0, 0, 0, 0)); dr = ImageDraw.Draw(im)
    dr.ellipse((28, 28, 228, 228), outline=(10, 60, 120, 255), width=18); dr.polygon([(128, 60), (190, 180), (66, 180)], fill=(10, 60, 120, 255)); im.save(logo)
    try:
        with sync_playwright() as pw:
            browser = chromium(pw)

            def ctx(phone=False):
                c = browser.new_context(**(PHONE if phone else DESK))
                c.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg = c.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
                pg.on('console', lambda m: csp.append(m.text) if 'Content Security Policy' in m.text else None)
                return c, pg

            def login(pg, user):
                pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login-form')
                pg.fill('#login', user); pg.fill('#password', PASSWORD); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1500)

            def register(pg, name, email, url=None):
                pg.goto(url or srv.base + '/#/registro?tipo=recreational'); pg.wait_for_selector('#register-form', timeout=15000)
                pg.fill('#r-name', name); pg.fill('#r-email', email); pg.fill('#r-pass', 'Buceo-Seguro-2026!'); pg.check('#r-terms')
                pg.click('#register-form button[type=submit]'); pg.wait_for_timeout(1800)

            def wait(pg, js, timeout=15000):
                """The page's CSP does not allow wait_for_function with text: the condition is read until it holds."""
                v = None
                for _ in range(timeout // 100):
                    v = pg.evaluate(js)
                    if v: return v
                    pg.wait_for_timeout(100)
                return v

            def open_logbook(pg, path='/#/logbook'):
                # a page load (a new visit): going to the address the page already shows would not load it again
                pg.goto(srv.base + path); pg.reload(); pg.wait_for_selector('#wd-logbook .dlc-head', timeout=20000)
                wait(pg, "() => (document.querySelector('#lb-sync')?.textContent||'').includes('Guardado')")

            def saved(pg):
                return wait(pg, "() => (document.querySelector('#lb-sync')?.textContent||'').includes('Guardado en tu cuenta')", 12000)

            def book(pg):
                return pg.evaluate(f'() => {LB}.getData()')

            def dives(data):
                out = {}
                for k, v in data['v'].items():
                    if k.startswith('d:'):
                        n, f = k.split(':')[1:3]; out.setdefault(int(n), {})[f] = v
                return out

            def shot(pg, name, full=False):
                if out: out.mkdir(parents=True, exist_ok=True); pg.screenshot(path=str(out / f'{name}.png'), full_page=full)

            def hint(pg):
                return pg.evaluate("() => { const h=document.querySelector('.dlc-hint'); return h&&!h.hidden?h.textContent:''; }")

            # ---------------------------------------------------------------- 1 · integrated list, desktop and phone
            for phone in (False, True):
                c, pg = ctx(phone); login(pg, 'buzo.prueba'); open_logbook(pg)
                st = pg.evaluate("""() => { const row=document.querySelector('.dlc-row:not(.dlc-th)'), btn=document.querySelector('.dlc-btn.primary');
                    return {rows: document.querySelectorAll('.dlc-row:not(.dlc-th)').length, font: row&&getComputedStyle(row).fontFamily,
                            body: getComputedStyle(document.body).fontFamily, accent: btn&&getComputedStyle(btn).color,
                            wide: document.scrollingElement.scrollWidth-innerWidth, title: !!document.querySelector('.acc-head h1')}; }""")
                where = 'móvil' if phone else 'escritorio'
                check(f'1 · {where}: la lista está dentro de «Log Book» con las inmersiones de la cuenta ({st["rows"]})', st['rows'] >= 3 and st['title'], st)
                check(f'1 · {where}: la lista usa la letra de la web', st['font'] == st['body'], st)
                check(f'1 · {where}: el acento es el azul océano de la web', st['accent'] == 'rgb(7, 104, 152)', st)
                check(f'1 · {where}: nada se sale de la pantalla', st['wide'] <= 0, st)
                shot(pg, f'logbook-lista-{"movil" if phone else "escritorio"}', full=not phone)
                c.close()

            # ---------------------------------------------------------------- 2 · a new diver: the passport, in grey
            c1, n1 = ctx(); register(n1, 'Nora Quintana', 'nora.quintana@example.org'); open_logbook(n1)
            st = n1.evaluate("""() => { const t=document.querySelector('[data-c="toggle"]'); return {state: t.dataset.state, op: getComputedStyle(t).opacity,
                                 label: t.getAttribute('aria-label')}; }""")
            check('2 · usuario nuevo: el icono del pasaporte está bloqueado y en gris', st['state'] == 'locked' and float(st['op']) < 0.5, st)
            n1.click('[data-c="toggle"]'); n1.wait_for_timeout(500)
            check('2 · al pulsarlo sale la explicación', 'se desbloquea' in hint(n1), hint(n1))
            n1.wait_for_timeout(1200)
            check('2 · y el pasaporte no se abre', n1.evaluate("() => document.querySelector('[data-c=\"passport\"]').hidden && !document.querySelector('[data-c=\"classic\"]').hidden"))
            shot(n1, 'logbook-pasaporte-bloqueado')

            # ---------------------------------------------------------------- 3 · the centre: a dive and its QR
            cc, center = ctx(); login(center, 'centro.prueba')
            center.goto(srv.base + '/#/admin?tab=logbook'); center.wait_for_selector('#clb-form', timeout=20000)
            center.fill('#clb-site', 'Islas Medas · La Vaca'); center.fill('#clb-instructor', 'Pau Ferrer · PADI 412233')
            center.fill('#clb-depth', '18'); center.fill('#clb-time', '45'); center.fill('#clb-temp', '19'); center.fill('#clb-pos', '42.0473, 3.2257')
            center.check('.clb-types input[value="boat"]'); center.fill('#clb-qty', '2')
            with center.expect_response(lambda r: r.url.endswith('/api/center/logbook/dive') and r.request.method == 'POST') as resp:
                center.click('#clb-form button[type=submit]')
            created = resp.value.json(); qr = [x['url'] for x in created.get('qr', [])]
            check('3 · el centro crea la inmersión con 2 QR', resp.value.status == 200 and len(qr) == 2 and all('/scan/d/' in u for u in qr), created)
            center.wait_for_selector('#clb-qr-img', timeout=10000); center.wait_for_timeout(700)
            okimg = center.evaluate("() => { const i=document.querySelector('#clb-qr-img'); return i.complete && i.naturalWidth>0; }")
            check('3 · el QR se ve en la pantalla del centro', okimg)
            if cv2 is not None:
                got = read_qr(center.locator('#clb-qr-img').screenshot())
                check('3 · leído con la cámara (OpenCV), lleva a /scan/d/<token> de esa inmersión', got == qr[0], got)
            shot(center, 'logbook-centro-qr')
            center.click('#clb-qr .modal-close, #clb-qr [data-modal-close]'); center.wait_for_timeout(400)
            listed = center.evaluate("() => [...document.querySelectorAll('.clb-table tbody tr')].map(t=>t.innerText)")
            check('3 · la inmersión aparece en «Inmersiones con QR» con 0 de 2 usados', any('Islas Medas' in t and '0 / 2' in t for t in listed), listed)

            # the new diver scans it: verified, and the passport unlocked
            n1.goto(qr[0]); n1.wait_for_selector('#wd-logbook .dlc-head', timeout=20000); saved(n1); n1.wait_for_timeout(600)
            data = book(n1); ver = data['verified']
            check('3 · escanear el QR la añade al logbook, verificada (✓)', len(ver) == 1 and n1.locator('.dlc-badge').count() == 1, ver)
            check('3 · y desbloquea el pasaporte', bool(data['unlocked']) and n1.get_attribute('[data-c="toggle"]', 'data-state') == 'open', data['unlocked'])
            check('3 · con el aviso del componente', 'verificada por' in hint(n1).lower(), hint(n1))
            claim = srv.sql('SELECT slot FROM logbook_claims c JOIN users u ON u.id=c.user_id WHERE u.email=?', ('nora.quintana@example.org',))
            check('3 · y queda guardada en la cuenta (servidor)', claim and claim[0]['slot'] is not None, claim)
            shot(n1, 'logbook-inmersion-verificada')
            n1.goto(qr[0]); n1.wait_for_selector('#wd-logbook .dlc-head', timeout=20000); saved(n1); n1.wait_for_timeout(600)
            check('3 · escanearla otra vez no la duplica', len(book(n1)['verified']) == 1 and n1.locator('.dlc-badge').count() == 1)
            check('3 · y lo dice: «ya estaba en tu logbook»', 'ya estaba' in hint(n1), hint(n1))
            n1.goto(qr[1]); n1.wait_for_selector('#wd-logbook .dlc-head', timeout=20000); saved(n1); n1.wait_for_timeout(600)
            check('3 · ni con el otro QR de la misma inmersión', len(book(n1)['verified']) == 1)
            n1.click('[data-c="toggle"]'); n1.wait_for_timeout(2600)
            check('3 · el pasaporte se abre', n1.evaluate("() => !document.querySelector('[data-c=\"passport\"]').hidden"))
            shot(n1, 'logbook-pasaporte-abierto')
            n1.click('[data-c="toggle"]'); n1.wait_for_timeout(400)

            # ---------------------------------------------------------------- 4 · the centre's link: logo on the cover
            center.goto(srv.base + '/#/admin?tab=logbook'); center.wait_for_selector('#clb-cover-form', timeout=20000)
            center.fill('#clb-name', 'Bahía Coralina'); center.set_input_files('#clb-logo', str(logo))
            center.click('#clb-cover-form button[type=submit]'); center.wait_for_timeout(1500); center.wait_for_selector('#clb-cover-form')
            src = center.get_attribute('.clb-preview img', 'src') or ''
            check('4 · el centro sube su logo (PNG transparente) y se ve en la vista previa', src.startswith('/assets/uploads/pasaporte_'), src)
            invite = center.input_value('#clb-url')
            check('4 · el enlace de invitación es /registro?centro=<slug>', '/registro?centro=' in invite, invite)
            shot(center, 'logbook-centro-panel', full=True)
            c2, n2 = ctx(); n2.goto(invite); n2.wait_for_selector('.reg-invite', timeout=15000)
            check('4 · el registro con el enlace dice qué centro invita', 'Bahía Coralina' in n2.inner_text('.reg-invite'))
            shot(n2, 'logbook-registro-con-centro')
            register(n2, 'Iker Salvat', 'iker.salvat@example.org', url=invite)
            n2.wait_for_selector('#wd-logbook .dlc-head', timeout=20000); saved(n2); n2.wait_for_timeout(800)
            data = book(n2)
            check('4 · tras registrarse, su logo está en la portada del pasaporte', (data.get('cover') or {}).get('logo') == src and data['cover'].get('name') == 'Bahía Coralina', data.get('cover'))
            check('4 · y el pasaporte está desbloqueado', (data.get('unlocked') or {}).get('by') == 'center' and n2.get_attribute('[data-c="toggle"]', 'data-state') == 'open', data.get('unlocked'))
            check('4 · con la bienvenida del centro', 'Bahía Coralina' in hint(n2), hint(n2))
            n2.click('[data-c="toggle"]'); n2.wait_for_timeout(700)
            has_logo = n2.evaluate("(src) => [...document.querySelectorAll('.dlb-book image, .dlb-book img')].some(i=>(i.getAttribute('href')||i.getAttribute('src')||'').includes(src))", src)
            check('4 · y la portada lo muestra', has_logo)
            shot(n2, 'logbook-portada-del-centro')
            n2.click('[data-c="toggle"]'); n2.wait_for_timeout(400)

            # ---------------------------------------------------------------- 5 · buddies by QR
            prof = n1.evaluate("() => fetch('/api/logbook').then(r=>r.json()).then(d=>d.profile)")
            check('5 · cada buceador tiene su URL pública de buddy, no adivinable', '/buddy/' in prof['qrText'] and len(prof['qrText'].rsplit('/', 1)[1]) >= 16, prof)
            if cv2 is not None:
                q = n1.context.new_page(); q.set_viewport_size({'width': 400, 'height': 400}); q.goto(srv.base + prof['qrImage'])
                got = read_qr(q.screenshot()); q.close()
                check('5 · su QR personal (el del pasaporte) lleva a esa URL', got == prof['qrText'], got)
            n2.goto(prof['qrText']); n2.wait_for_selector('#wd-logbook .dlc-head', timeout=20000); n2.wait_for_timeout(600)
            check('5 · al escanearlo sale «Ahora sois buddies»', 'Ahora sois buddies' in (n2.text_content('.lb-notice') or '') and 'Nora Quintana' in (n2.text_content('.lb-notice') or ''))
            shot(n2, 'logbook-ahora-sois-buddies')
            n2.click('[data-c="add"]'); n2.wait_for_selector('.dlc-form input[name="buddy"]')
            opts = n2.evaluate("() => { const i=document.querySelector('.dlc-form input[name=\"buddy\"]'); return [...document.getElementById(i.getAttribute('list')).options].map(o=>o.value); }")
            check('5 · y aparece en «Compañero»', 'Nora Quintana' in opts, opts)
            n2.click('.dlc-form [data-f="cancel"]')
            open_logbook(n1)
            check('5 · la amistad va en los dos sentidos', 'Iker Salvat' in n1.evaluate(f'() => {LB}.friends.map(f=>f.name)'))

            # ---------------------------------------------------------------- 6 · two devices, two views
            cd, desk = ctx(); login(desk, 'buzo.prueba'); open_logbook(desk)
            desk.click('[data-c="add"]'); desk.wait_for_selector('.dlc-form input[name="site"]')
            for k, v in (('date', '12/10/2026'), ('site', 'Cala Montgó'), ('country', 'España'), ('depth', '21'), ('time', '50')):
                desk.fill(f'.dlc-form input[name="{k}"]', v)
            desk.click('.dlc-form button[type=submit]'); desk.wait_for_timeout(400); saved(desk)
            n_new = [n for n, d in dives(book(desk)).items() if d.get('site') == 'Cala Montgó']
            check('6 · ordenador: inmersión nueva guardada en la cuenta', len(n_new) == 1 and 'Guardado' in desk.text_content('#lb-sync'))
            cm, phone = ctx(True); login(phone, 'buzo.prueba'); open_logbook(phone)
            check('6 · móvil (otro dispositivo, sin datos locales): la misma inmersión', phone.locator('.dlc-row', has_text='Cala Montgó').count() == 1)
            for _ in range(5): phone.click('[data-c="toggle"]'); phone.wait_for_timeout(120)
            phone.wait_for_timeout(500)
            check('6 · el truco de los 5 toques desbloquea el pasaporte', 'Lo has encontrado' in hint(phone), hint(phone))
            phone.click('[data-c="toggle"]'); phone.wait_for_timeout(2600)
            n = n_new[0] if n_new else 0
            same = phone.evaluate("(n) => ['site','country','depth','time','date'].map(f=>document.querySelector(`[data-k=\"d:${n}:${f}\"]`)?.value)", n)
            check('6 · en el pasaporte se ven los mismos datos que en la lista', same == ['Cala Montgó', 'España', '21', '50', '12/10/2026'], same)
            shot(phone, 'logbook-pasaporte-movil')
            phone.evaluate("(n) => { const i=document.querySelector(`[data-k=\"d:${n}:depth\"]`); i.value='22'; i.dispatchEvent(new Event('input',{bubbles:true})); }", n)
            phone.wait_for_timeout(400); saved(phone)
            open_logbook(desk)
            depth = dives(book(desk)).get(n, {}).get('depth')
            check('6 · cada dispositivo abre en su vista: el ordenador, en la lista (por defecto)', desk.evaluate("() => !document.querySelector('[data-c=\"classic\"]').hidden"))
            row_txt = desk.locator('.dlc-row', has_text='Cala Montgó').all_inner_texts()
            check('6 · lo cambiado en el pasaporte del móvil se ve en la lista del ordenador', depth == '22' and len(row_txt) == 1 and '22 m' in row_txt[0], (depth, row_txt))
            check('6 · y el desbloqueo también (es de la cuenta)', bool(book(desk)['unlocked']))

            def add_dive(pg, site, date='13/10/2026'):
                pg.click('[data-c="add"]'); pg.wait_for_selector('.dlc-form input[name="site"]')
                pg.fill('.dlc-form input[name="date"]', date); pg.fill('.dlc-form input[name="site"]', site); pg.click('.dlc-form button[type=submit]')

            def server_sites(pg):
                return sorted(d.get('site', '') for d in dives(pg.evaluate("() => fetch('/api/logbook').then(r=>r.json()).then(d=>d.book.data)")).values())

            # both devices with the page open: each one saves on top of what the other saved (dive by dive)
            open_logbook(phone); phone.click('[data-c="toggle"]'); phone.wait_for_timeout(400)   # back to the list on the phone
            add_dive(phone, 'Punta del Molí'); phone.wait_for_timeout(300); saved(phone)
            add_dive(desk, 'Ses Negres'); desk.wait_for_timeout(300); saved(desk); desk.wait_for_timeout(600)
            sites = server_sites(desk)
            check('6 · dos dispositivos a la vez: lo apuntado en los dos queda en la cuenta', 'Punta del Molí' in sites and 'Ses Negres' in sites, sites)
            check('6 · y el ordenador ya enseña las dos', desk.locator('.dlc-row', has_text='Punta del Molí').count() == 1 and desk.locator('.dlc-row', has_text='Ses Negres').count() == 1)
            # back to the tab: what the other device saved appears without reloading
            add_dive(phone, 'Illa Mateua'); phone.wait_for_timeout(300); saved(phone)
            desk.evaluate("() => document.dispatchEvent(new Event('visibilitychange'))"); desk.wait_for_timeout(1500)
            check('6 · al volver a la pestaña, el ordenador trae lo guardado en el móvil', desk.locator('.dlc-row', has_text='Illa Mateua').count() == 1)
            # without connection: saved on this device, and to the account when the connection is back
            cd.set_offline(True); add_dive(desk, 'Cala Pedrosa'); desk.wait_for_timeout(1500)
            check('6 · sin conexión lo dice y lo guarda en el dispositivo', 'Sin conexión' in desk.text_content('#lb-sync'), desk.text_content('#lb-sync'))
            cd.set_offline(False); desk.evaluate("() => window.dispatchEvent(new Event('online'))"); saved(desk); desk.wait_for_timeout(500)
            check('6 · y al volver la conexión sube a la cuenta', 'Cala Pedrosa' in server_sites(desk))
            # without connection and the page closed: it goes up the next time the Log Book opens
            cd.set_offline(True); add_dive(desk, 'Es Furió'); desk.wait_for_timeout(1500); desk.close()
            cd.set_offline(False); desk = cd.new_page(); desk.on('pageerror', lambda e: errors.append(str(e))); open_logbook(desk); saved(desk); desk.wait_for_timeout(500)
            check('6 · cerrada la página sin conexión, sube al volver a abrir el Log Book', 'Es Furió' in server_sites(desk) and desk.locator('.dlc-row', has_text='Es Furió').count() == 1)

            # ---------------------------------------------------------------- 7 · locked fields of a verified dive
            open_logbook(n1)
            nv = int(next(iter(book(n1)['verified'])))
            n1.click(f'.dlc-row[data-n="{nv}"]'); n1.wait_for_selector('.dlc-form input[name="site"]')
            ro = n1.evaluate("() => ['date','site','country','center','pos','sign'].map(f=>document.querySelector(`.dlc-form input[name=\"${f}\"]`).readOnly)")
            check('7 · en pantalla: fecha, lugar, país, centro, posición e instructor son de solo lectura', all(ro), ro)
            check('7 · y lo dice («· centro»)', n1.locator('.dlc-form .dlc-field span', has_text='· centro').count() >= 5)
            shot(n1, 'logbook-campos-bloqueados')
            n1.click('.dlc-form [data-f="cancel"]')
            tamper = n1.evaluate("""async (n) => { const g=await fetch('/api/logbook').then(r=>r.json()); const d=g.book.data; d.v[`d:${n}:site`]='Otro sitio';
                const r=await fetch('/api/logbook',{method:'PUT',headers:{'Content-Type':'application/json','X-Logbook-Version':String(g.book.version)},body:JSON.stringify(d)});
                const j=await r.json(); const after=await fetch('/api/logbook').then(r=>r.json()); return {status:r.status, locked:j.locked, site:after.book.data.v[`d:${n}:site`]}; }""", nv)
            check('7 · manipulando la petición (PUT a mano): 409 y el lugar no cambia', tamper['status'] == 409 and tamper['locked'] and tamper['site'] == 'Islas Medas · La Vaca', tamper)
            n1.evaluate(f"(n) => {{ const lb={LB}; lb.data.v[`d:${{n}}:date`]='01/01/2026'; lb.save(); }}", nv)
            n1.wait_for_timeout(2600)
            back = dives(book(n1))[nv].get('date')
            server_date = n1.evaluate("(n) => fetch('/api/logbook').then(r=>r.json()).then(d=>d.book.data.v[`d:${n}:date`])", nv)
            check('7 · manipulando el componente: el servidor lo rechaza y la página vuelve a lo del centro', back == server_date and back != '01/01/2026', (back, server_date))
            audit = srv.sql("SELECT COUNT(*) AS n FROM audit_log WHERE action='logbook_locked_refused'")[0]['n']
            check('7 · cada intento queda registrado', audit >= 2, audit)

            # ---------------------------------------------------------------- the component in another language
            ce = browser.new_context(**{**DESK, 'locale': 'en-GB'})
            ce.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
            en = ce.new_page(); en.on('pageerror', lambda e: errors.append(str(e)))
            en.goto(srv.base + '/?lang=en#/login'); en.wait_for_selector('#login-form'); en.fill('#login', 'nora.quintana@example.org'); en.fill('#password', 'Buceo-Seguro-2026!')
            en.click('#login-form button[type=submit]'); en.wait_for_timeout(1500)
            open_logbook(en, '/?lang=en#/logbook')
            txt = en.evaluate("() => ({add: document.querySelector('[data-c=\"add\"]').textContent, stats: document.querySelector('.dlc-stats').textContent, site: document.querySelector('.dlc-row:not(.dlc-th) .dlc-site b').textContent})")
            check('idiomas · en inglés el componente habla inglés («+ Add dive», «underwater»)', txt['add'] == '+ Add dive' and 'underwater' in txt['stats'], txt)
            check('idiomas · y lo que escribió el buceador o su centro no se traduce', txt['site'] == 'Islas Medas · La Vaca', txt)
            en.click('.dlc-row[data-n]'); en.wait_for_selector('.dlc-form input[name="site"]')
            lab = en.evaluate("() => [...document.querySelectorAll('.dlc-form .dlc-field > span')].map(s=>s.textContent)")
            check('idiomas · los campos del centro, marcados en inglés («Date · centre»)', 'Date · centre' in lab and 'Time in' in lab and 'Time out' in lab, lab)
            shot(en, 'logbook-en-ingles')
            ce.close()

            for c in (c1, cc, c2, cd, cm): c.close()
            browser.close()
        check('sin errores de JavaScript', not errors, errors[:3])
        check('sin bloqueos de la política de seguridad (CSP)', not csp, csp[:3])
    finally:
        srv.stop()
    bad = [n for n, ok in rows if not ok]
    print(f'\n{len(rows) - len(bad)}/{len(rows)} comprobaciones OK')
    return not bad


if __name__ == '__main__':
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(0 if run(target) else 1)
