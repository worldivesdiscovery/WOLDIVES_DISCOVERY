#!/usr/bin/env python3
"""v50.56 · Bloque 2 · Seguros de buceo, en un navegador real sobre la demo (README-PRUEBAS «Probar los seguros»):

 1. «Mi seguro de buceo» en sus 4 estados: 🟢 vigente (buzo2.prueba), 🟠 caduca pronto, 🔴 caducado (buzo.prueba) y
    ⚪ sin seguro.
 2. buzo.prueba reserva «Inmersión guiada en la Granadella» (seguro obligatorio para reservar online): el paso de la
    reserva avisa; la reserva espera el seguro y guarda las plazas.
 3. «Contrata tu seguro de buceo»: pestañas Día · Semana · Año, las dos aseguradoras de prueba, «Colaborador», el aviso
    legal; «Contratar en …» abre la página de prueba en otra pestaña con el código de colaborador y sin datos de la
    persona; se cuenta el clic.
 4. «¿Ya lo tienes? Sube tu póliza»: tipo y aseguradora ya puestos; la lectura del PDF propone las fechas; al guardar,
    la reserva sigue sola (solicitud enviada al centro).
 5. El centro la acepta y ve el seguro 🟢 del participante; en otra reserva, un participante con el seguro caducado 🔴.
 6. Administración → Seguros: aseguradoras, productos, textos legales y estadísticas.
 7. El widget: un cliente sin cuenta reserva el servicio obligatorio y sube su póliza en la misma ventana; uno que
    «se comprueba en el centro» se reserva sin rellenar el seguro.
 8. La ventana «Contrata tu seguro» en los 9 idiomas, y un repaso en inglés que apunta cualquier texto sin traducir.

    python3 tests/navegador/e2e_v50_56_seguros.py [carpeta-de-capturas]

Usa las cuentas de la demo: no va en el zip de producción (scripts/generar_zips.py)."""
from __future__ import annotations

import datetime as dt
import json
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app'),
                str(Path(__file__).resolve().parents[2] / 'scripts')]
from helpers import Client, Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402
from crear_demo import PASSWORD, demo_pdf  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DESK = {'viewport': {'width': 1366, 'height': 900}, 'locale': 'es-ES'}
PHONE = {'viewport': {'width': 390, 'height': 844}, 'locale': 'es-ES', 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2}
POLIZA = ROOT / 'docs' / 'pruebas' / 'poliza-de-prueba.pdf'
LANGS = ('es', 'en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh')
TEST_PAGE = '<!doctype html><meta charset="utf-8"><title>Aseguradora de prueba</title><h1>Página de prueba de la aseguradora</h1>'


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


def run(out: Path | None):
    rows = []

    def check(name, ok, detail=''):
        rows.append((name, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + name + ('' if ok else f'  → {str(detail)[:400]}'), flush=True)

    tmp = Path(tempfile.mkdtemp(prefix='wod-demo-')) / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(tmp)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=tmp).start()
    errors, misses = [], set()
    try:
        uid = lambda u: srv.sql('SELECT id FROM users WHERE username=?', (u,))[0]['id']
        cid = srv.sql("SELECT provider_id FROM sales_settings WHERE slug='bahia-coralina'")[0]['provider_id']
        sid = srv.sql("SELECT id FROM provider_services WHERE center_id=? AND title='Inmersión guiada en la Granadella'", (cid,))[0]['id']
        check('demo · el servicio «Inmersión guiada en la Granadella» exige el seguro para reservar online',
              srv.sql('SELECT insurance_required FROM provider_services WHERE id=?', (sid,))[0]['insurance_required'] == 'online')
        provs = [x['name'] for x in srv.sql('SELECT name FROM insurance_providers ORDER BY name')]
        check('demo · «Aseguradora Demo A» y «Demo B» configuradas en Administración', provs == ['Aseguradora Demo A', 'Aseguradora Demo B'], provs)
        pol = lambda u: [dict(x) for x in srv.sql("SELECT valid_to FROM insurance_policies WHERE user_id=? AND status='active'", (uid(u),))]
        check('demo · buzo.prueba con el seguro caducado y buzo2.prueba con uno vigente',
              all(p['valid_to'] < day(0) for p in pol('buzo.prueba')) and pol('buzo.prueba') and all(p['valid_to'] > day(30) for p in pol('buzo2.prueba')) and pol('buzo2.prueba'))
        # 🟠 «caduca pronto» (12 days left) for buzo4.prueba; buzo3.prueba has none
        b4 = Client(srv); assert b4.login('buzo4.prueba', PASSWORD).status == 200
        r = b4.upload('/api/insurance/policies', {'insurer': 'Aseguradora Demo B', 'kind': 'semana', 'valid_from': day(-2), 'valid_to': day(12), 'zone': 'europa'},
                      'poliza.pdf', demo_pdf('Aseguradora Demo B'))
        check('una póliza que caduca en 12 días', r.status == 200, r)
        center = Client(srv); assert center.login('centro.prueba', PASSWORD).status == 200
        slot = srv.sql("SELECT id, slot_date FROM service_slots WHERE service_id=? ORDER BY slot_date LIMIT 1", (sid,))[0]
        free = lambda: srv.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot['id'],))[0]['spots_available']
        spots0 = free()

        with sync_playwright() as pw:
            browser = chromium(pw)

            def ctx(opts=DESK, lang=None, debug=False):
                c = browser.new_context(**opts)
                init = "try{localStorage.setItem('wd_cookie_notice',String(Date.now()));"
                if lang: init += f"localStorage.setItem('wod-language','{lang}');"
                if debug: init += "localStorage.setItem('wd-i18n-debug','1');"
                c.add_init_script(init + "}catch(e){}")
                # The insurers' test pages (example.com / example.org): answered here, nothing goes out
                c.route('https://example.com/**', lambda rt: rt.fulfill(status=200, content_type='text/html', body=TEST_PAGE))
                c.route('https://example.org/**', lambda rt: rt.fulfill(status=200, content_type='text/html', body=TEST_PAGE))
                pg = c.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
                return c, pg

            def login(pg, user, lang=''):
                pg.goto(srv.base + (f'/?lang={lang}' if lang else '/') + '#/login'); pg.wait_for_selector('#login-form')
                pg.fill('#login', user); pg.fill('#password', PASSWORD); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1500)

            def go(pg, route, wait=1200):
                pg.goto(srv.base + '/#' + route); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(wait)

            def shot(pg, name, full=False):
                if not out: return
                out.mkdir(parents=True, exist_ok=True); pg.wait_for_timeout(350)
                pg.screenshot(path=str(out / f'{name}.png'), full_page=full)

            def collect(pg):
                m = pg.evaluate('window.__wdI18nMisses?[...window.__wdI18nMisses]:[]')
                misses.update(m)

            # 1. «Mi seguro de buceo» in its 4 states
            for user, label, name in (('buzo2.prueba', 'Vigente', 'vigente'), ('buzo4.prueba', 'Caduca pronto', 'caduca-pronto'),
                                      ('buzo.prueba', 'Caducado', 'caducado'), ('buzo3.prueba', 'Sin seguro', 'sin-seguro')):
                c, pg = ctx(); login(pg, user); go(pg, '/seguro')
                txt = pg.inner_text('.ins-status')
                check(f'1 · Mi seguro de {user}: «{label}»', label in txt, txt)
                buy = pg.locator('.ins-status [data-ins-buy]').count()
                check(f'1 · «Contratar seguro» {"no aparece" if name == "vigente" else "aparece"} ({label})', (buy == 0) if name == 'vigente' else (buy == 1), buy)
                shot(pg, f'seguro-1-estado-{name}', True)
                c.close()
            # also on a phone (no sideways scroll)
            c, pg = ctx(PHONE); login(pg, 'buzo.prueba'); go(pg, '/seguro')
            over = pg.evaluate('document.scrollingElement.scrollWidth - window.innerWidth')
            check('1 · en el móvil, sin desplazamiento lateral', over <= 1, over)
            shot(pg, 'seguro-1-movil-caducado', True)
            c.close()

            # 1b. The centre: a participant whose policy had expired (buzo.prueba, before step 4 gives her a new one)
            exp = srv.sql("""SELECT b.id FROM bookings b JOIN provider_services s ON s.id=b.service_id WHERE b.user_id=? AND b.center_id=? AND b.status='confirmed'
                             AND b.booking_date>=? AND COALESCE(s.insurance_required,'center')<>'no' ORDER BY b.booking_date LIMIT 1""", (uid('buzo.prueba'), cid, day(0)))
            check('1b · buzo.prueba tiene una reserva confirmada en el centro', bool(exp))
            c, pg = ctx(); login(pg, 'centro.prueba')
            if exp:
                go(pg, f'/reserva?id={exp[0]["id"]}', 1800); pg.wait_for_selector('#bk-insurance .ins-row')
                ins = pg.inner_text('#bk-insurance')
                check('1b · el centro ve al participante con el seguro caducado: 🔴 «Seguro caducado ese día»', '🔴' in ins and 'Seguro caducado ese día' in ins, ins)
                pg.locator('#bk-insurance').scroll_into_view_if_needed(); shot(pg, 'seguro-5-centro-caducado')
            go(pg, '/admin?tab=bookings', 2200)
            marks = pg.locator('.bk-ins').all_inner_texts()
            check('1b · la lista de reservas del centro marca el seguro de cada una (🟢 🔴 ⚪)', any('🔴' in m for m in marks) and any('🟢' in m for m in marks) and any('⚪' in m for m in marks), marks[:8])
            c.close()

            # 2. The booking step and the booking that waits for the insurance
            c, pg = ctx(); login(pg, 'buzo.prueba')
            go(pg, f'/reservar?center={cid}&service={sid}&slot={slot["id"]}', 2500)
            note = pg.locator('#bk-ins-note')
            check('2 · el paso de la reserva avisa del seguro obligatorio', note.count() and 'exige un seguro de buceo' in note.inner_text(), note.inner_text() if note.count() else '')
            shot(pg, 'seguro-2-paso-reserva')
            pg.locator('#bk-summary .bk-go').click()
            for _ in range(40):
                if pg.evaluate("location.hash").startswith('#/seguro?reserva='): break
                pg.wait_for_timeout(250)
            h = pg.evaluate('location.hash')
            check('2 · al reservar sin seguro válido, va a «Mi seguro» con la reserva', h.startswith('#/seguro?reserva='), h)
            bid = int(h.split('reserva=')[1].split('&')[0]) if 'reserva=' in h else 0
            row = srv.sql('SELECT status, insurance_status, slot_reserved FROM bookings WHERE id=?', (bid,))[0] if bid else {}
            check('2 · la reserva espera el seguro («Falta el seguro») y guarda las plazas', bid and row['status'] == 'insurance_pending' and row['slot_reserved'] == 1 and free() == spots0 - 1, (dict(row) if row else row, spots0, free()))
            pg.wait_for_selector('.ins-wait'); pg.wait_for_timeout(500)
            check('2 · «Tu reserva espera tu seguro de buceo»', 'espera tu seguro' in pg.inner_text('.ins-wait'))
            lst = center.get('/api/bookings').json
            items = lst.get('items', lst) if isinstance(lst, dict) else lst
            check('2 · todavía no es una reserva: no está en la lista del centro', bid not in [x.get('id') for x in items], [x.get('id') for x in items][:5])

            # 3. «Contrata tu seguro de buceo»
            pg.evaluate("window.scrollTo(0,0)"); pg.locator('.ins-status [data-ins-buy]').click()
            pg.wait_for_selector('#ins-offers .ins-offer'); pg.wait_for_timeout(400)
            tabs = pg.locator('#ins-offers [data-ins-kind-tab]').all_inner_texts()
            check('3 · pestañas Día · Semana · Año', tabs == ['Día', 'Semana', 'Año'], tabs)
            cards = pg.locator('#ins-offers .ins-offer')
            body = pg.inner_text('#ins-offers')
            check('3 · las dos aseguradoras, con «desde», zona y «Colaborador»', cards.count() == 2 and 'Aseguradora Demo A' in body and 'Aseguradora Demo B' in body
                  and 'desde' in body.lower() and 'colaborador' in body.lower() and 'Europa' in body, body[:500])
            check('3 · el aviso «La contratación se realiza en la web de … WORLDIVES no es aseguradora ni mediador de seguros.»',
                  'La contratación se realiza en la web de Aseguradora Demo A' in body and 'WORLDIVES no es aseguradora ni mediador de seguros' in body, body[:600])
            go_a = pg.locator('#ins-offers .ins-offer', has_text='Aseguradora Demo A').locator('a.ins-go')
            href, tgt, rel = go_a.get_attribute('href'), go_a.get_attribute('target'), go_a.get_attribute('rel') or ''
            check('3 · «Contratar en Aseguradora Demo A» abre otra pestaña, sin referencia', tgt == '_blank' and 'noopener' in rel and 'noreferrer' in rel and href.startswith('/seguros/ir/'), (href, tgt, rel))
            shot(pg, 'seguro-3-ventana-contratar')
            clicks0 = sum(x['clicks'] for x in srv.sql('SELECT clicks FROM insurance_clicks'))
            with pg.context.expect_page() as newp:
                go_a.click()
            tab = newp.value; tab.wait_for_load_state()
            url = tab.url
            check('3 · la web de la aseguradora (página de prueba) con el código de colaborador', url.startswith('https://example.com/') and 'colaborador=WD-DEMO-A' in url, url)
            check('3 · sin datos de la persona en la dirección', not any(x in url.lower() for x in ('bea', 'navarro', 'example.com/?email', '@', 'nombre', 'name=')), url)
            tab.close()
            check('3 · el clic se cuenta (sin datos personales)', sum(x['clicks'] for x in srv.sql('SELECT clicks FROM insurance_clicks')) == clicks0 + 1)
            pg.wait_for_selector('#ins-offers .ins-return'); pg.wait_for_timeout(300)
            check('3 · al volver: «¿Ya lo tienes? Sube tu póliza»', 'Sube tu póliza' in pg.inner_text('#ins-offers .ins-return'))
            shot(pg, 'seguro-3-ventana-vuelta')

            # 4. Upload the policy: the booking goes on by itself
            pg.locator('#ins-offers .ins-return [data-ins-have]').click(); pg.wait_for_timeout(1500)
            pg.wait_for_selector('#ins-form')
            check('4 · aseguradora y tipo ya puestos', pg.input_value('#ins-insurer') == 'Aseguradora Demo A' and pg.input_value('#ins-kind') == 'dia',
                  (pg.input_value('#ins-insurer'), pg.input_value('#ins-kind')))
            pg.set_input_files('#ins-file', str(POLIZA)); pg.locator('#ins-form [data-ins-read]').click()
            for _ in range(30):
                if pg.input_value('#ins-to'): break
                pg.wait_for_timeout(200)
            check('4 · la lectura del PDF propone las fechas y el número (sin guardar nada)', pg.input_value('#ins-to') == '2030-12-31' and pg.input_value('#ins-from') == '2026-01-01'
                  and pg.input_value('#ins-number') == 'DA-PRUEBA-2026' and srv.sql('SELECT COUNT(*) n FROM insurance_policies WHERE user_id=? AND booking_id IS NULL AND valid_to=?', (uid('buzo.prueba'), '2030-12-31'))[0]['n'] == 0,
                  (pg.input_value('#ins-from'), pg.input_value('#ins-to'), pg.input_value('#ins-number')))
            check('4 · «Revisa los datos: solo se guardan cuando tú los confirmas.»', 'solo se guardan cuando tú los confirmas' in pg.inner_text('#ins-form .ins-read-note'))
            pg.locator('#ins-upload').scroll_into_view_if_needed(); shot(pg, 'seguro-4-subir-poliza')
            pg.locator('#ins-form [type=submit]').click()
            for _ in range(40):
                if pg.evaluate('location.hash').startswith('#/reserva?id='): break
                pg.wait_for_timeout(250)
            row = srv.sql('SELECT status, insurance_status FROM bookings WHERE id=?', (bid,))[0]
            check('4 · al guardar, la solicitud llega al centro (seguro 🟢 para ese día)', (row['status'], row['insurance_status']) == ('requested', 'ok'), dict(row))
            check('4 · la póliza subida tras el clic se cuenta en las estadísticas', sum(x['policies'] for x in srv.sql('SELECT policies FROM insurance_clicks')) >= 1)
            pg.wait_for_timeout(800); shot(pg, 'seguro-4-reserva-con-seguro')
            check('4 · la reserva dice «Seguro de buceo vigente para ese día»', 'vigente para ese día' in pg.inner_text('main'))
            c.close()

            # 5. The centre: 🟢 for this one, 🔴 for a participant whose policy had expired
            r = center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})
            check('5 · el centro acepta la solicitud', r.status == 200, r)
            c, pg = ctx(); login(pg, 'centro.prueba')
            go(pg, f'/reserva?id={bid}', 1800)
            pg.wait_for_selector('#bk-insurance .ins-row')
            ins = pg.inner_text('#bk-insurance')
            check('5 · el centro ve 🟢 «Seguro vigente ese día», la aseguradora, el tipo y las fechas', '🟢' in ins and 'Seguro vigente ese día' in ins and 'Aseguradora Demo A' in ins and 'Día' in ins, ins)
            check('5 · y no ve el número de póliza', 'DA-PRUEBA-2026' not in ins)
            check('5 · «Dar de alta seguro» y «Subir póliza para esta reserva»', 'Dar de alta seguro' in ins and 'Subir póliza para esta reserva' in ins)
            pg.locator('#bk-insurance').scroll_into_view_if_needed(); shot(pg, 'seguro-5-centro-vigente')
            # «Dar de alta seguro»: the centre's own programme (link for centres), day insurance by default
            pg.locator('#bk-insurance [data-ins-alta]').click(); pg.wait_for_selector('#ins-offers .ins-offer')
            href = pg.locator('#ins-offers a.ins-go').first.get_attribute('href')
            check('5 · «Dar de alta seguro» abre las aseguradoras para centros (seguro de día)', 'para=centro' in href and pg.locator('#ins-offers .ins-tab.is-on').inner_text() == 'Día', href)
            shot(pg, 'seguro-5-centro-dar-de-alta')
            # RC of the centre, next to «Seguro de responsabilidad civil»
            go(pg, '/admin?tab=fiscal', 1800)
            btn = pg.locator('#fi-rc-buy')
            check('5 · «Contratar o renovar seguro de RC del centro» junto al seguro de RC', btn.count() == 1)
            if btn.count():
                btn.click(); pg.wait_for_selector('#ins-offers .ins-offer')
                t = pg.inner_text('#ins-offers')
                check('5 · la ventana de RC enseña los productos «RC para centros»', 'RC para centros de buceo' in t, t[:300])
                shot(pg, 'seguro-5-centro-rc')
            c.close()

            # 6. Administración → Seguros
            c, pg = ctx(); login(pg, 'admin.prueba')
            go(pg, '/admin?tab=seguros', 2000); pg.wait_for_selector('#admin-insurance .ins-admin-prov')
            t = pg.inner_text('#admin-insurance')
            check('6 · las dos aseguradoras con sus productos, «Colaborador» y el código', pg.locator('#admin-insurance .ins-admin-prov').count() == 2 and 'WD-DEMO-A' in t and 'Colaborador' in t, t[:400])
            check('6 · textos legales editables en los 9 idiomas', pg.locator('#ins-lang option').count() == 9)
            check('6 · estadísticas por aseguradora, producto, país y mes', 'Seguro de buceo de un día' in t.split('Estadísticas')[-1], t[-400:])
            shot(pg, 'seguro-6-admin-aseguradoras', True)
            c.close()

            # 7. The widget: a customer without an account books the «obligatorio» service and uploads the policy
            c, pg = ctx()
            pg.goto(f'{srv.base}/c/bahia-coralina?servicio={sid}'); pg.wait_for_selector('.wr-cal', timeout=15000)
            pg.locator(f'[data-day="{slot["slot_date"]}"]').click(); pg.locator('.wr-slot').first.click()
            pg.wait_for_selector('.wr-ins')
            check('7 · el widget avisa de que el servicio exige seguro', 'exige un seguro de buceo' in pg.inner_text('.wr-ins'))
            pg.fill('input[name=fullname]', 'Marta Widget'); pg.fill('input[name=email]', 'marta.widget@example.org')
            pg.locator('.wr-sum .wr-total').wait_for(timeout=8000)
            pg.check('input[name=accept_policy]'); pg.locator('[data-go]').click()
            pg.wait_for_selector('[data-ins-form]', timeout=15000)
            check('7 · tras reservar, pide la póliza (las plazas quedan guardadas)', 'Falta tu seguro de buceo' in pg.inner_text('main'))
            shot(pg, 'seguro-7-widget-subir-poliza', True)
            pg.fill('[data-ins-form] input[name=insurer]', 'Aseguradora Demo B'); pg.fill('[data-ins-form] input[name=valid_to]', '2030-12-31')
            pg.set_input_files('[data-ins-form] input[name=file]', str(POLIZA)); pg.locator('[data-ins-send]').click()
            pg.wait_for_selector('.wr-done h2', timeout=15000); pg.wait_for_timeout(400)
            check('7 · con la póliza, «Solicitud enviada»', 'Solicitud enviada' in pg.inner_text('.wr-done'), pg.inner_text('main')[:300])
            gb = srv.sql("SELECT status, insurance_status FROM bookings WHERE contact_email IS NOT NULL AND service_id=? AND channel='link' ORDER BY id DESC LIMIT 1", (sid,))
            check('7 · la reserva del cliente sin cuenta sigue sola con su seguro', gb and (gb[0]['status'], gb[0]['insurance_status']) == ('requested', 'ok'), gb and dict(gb[0]))
            # «Se comprueba en el centro»: the widget lets one book without saying anything about the insurance
            sn = srv.sql("SELECT id FROM provider_services WHERE center_id=? AND title='Snorkel en la Granadella'", (cid,))[0]['id']
            snslot = srv.sql("SELECT slot_date FROM service_slots WHERE service_id=? AND spots_available>0 ORDER BY slot_date LIMIT 1", (sn,))[0]
            pg.goto(f'{srv.base}/c/bahia-coralina?servicio={sn}'); pg.wait_for_selector('.wr-cal', timeout=15000)
            pg.locator(f'[data-day="{snslot["slot_date"]}"]').click(); pg.locator('.wr-slot').first.click()
            pg.wait_for_selector('.wr-ins')
            check('7 · «se comprueba en el centro»: el widget lo dice y no marca nada', 'comprobará tu seguro' in pg.inner_text('.wr-ins') and pg.locator('[name=ins_mode]:checked').count() == 0)
            pg.fill('input[name=fullname]', 'Pablo Playa'); pg.fill('input[name=email]', 'pablo.playa@example.org')
            pg.locator('.wr-sum .wr-total').wait_for(timeout=8000)
            pg.check('input[name=accept_policy]'); pg.locator('[data-go]').click()
            pg.wait_for_selector('.wr-done h2', timeout=15000)
            gb = srv.sql("SELECT status, insurance_status FROM bookings WHERE service_id=? AND contact_email IS NOT NULL ORDER BY id DESC LIMIT 1", (sn,))
            check('7 · y se reserva sin rellenar el seguro (el centro lo comprueba ese día)', 'Solicitud enviada' in pg.inner_text('.wr-done') and gb and gb[0]['status'] == 'requested', gb and dict(gb[0]))
            c.close()

            # 8. The window in the 9 languages, and an English pass that lists any text without translation
            titles = {}
            for lang in LANGS:
                c, pg = ctx(lang=lang); login(pg, 'buzo3.prueba', lang)
                pg.goto(f'{srv.base}/?lang={lang}#/seguro?contratar=dia'); pg.wait_for_selector('#ins-offers .ins-offer', timeout=15000); pg.wait_for_timeout(600)
                titles[lang] = (pg.inner_text('#ins-offers-title'), pg.inner_text('#ins-offers .ins-legal'), pg.locator('#ins-offers a.ins-go').first.inner_text())
                if lang in ('en', 'zh'): shot(pg, f'seguro-8-ventana-{lang}')
                c.close()
            es = titles['es']
            bad = [l for l in LANGS[1:] if titles[l][0] == es[0] or titles[l][1] == es[1] or titles[l][2] == es[2]]
            check('8 · la ventana «Contrata tu seguro» (título, aviso legal y botón) en los 9 idiomas', not bad, {l: titles[l] for l in bad})
            for user, routes in (('buzo4.prueba', ['/seguro', '/seguro?contratar=semana', '/cuenta', f'/reserva?id={bid}']),
                                 ('buzo.prueba', [f'/reservar?center={cid}&service={sid}&slot={slot["id"]}', '/seguro']),
                                 ('centro.prueba', [f'/reserva?id={bid}'] + ([f'/reserva?id={exp[0]["id"]}'] if exp else []) + ['/admin?tab=bookings', '/admin?tab=fiscal']),
                                 ('admin.prueba', ['/admin?tab=seguros'])):
                c, pg = ctx(lang='en', debug=True); login(pg, user, 'en')
                for rt in routes:
                    pg.goto(f'{srv.base}/?lang=en#{rt}'); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(1500)
                    if rt == '/seguro':
                        pg.locator('[data-ins-buy]').first.click(); pg.wait_for_selector('#ins-offers .ins-offer'); pg.wait_for_timeout(400)
                    if 'tab=fiscal' in rt and pg.locator('#fi-rc-buy').count():
                        pg.locator('#fi-rc-buy').click(); pg.wait_for_timeout(1200)
                    if rt.startswith('/reserva?') and pg.locator('[data-ins-subir]').count():
                        pg.locator('[data-ins-subir]').click(); pg.wait_for_timeout(1200)
                    collect(pg)
                c.close()
            ins_words = ('segur', 'póliza', 'asegura', 'Contrat', 'Caduc', 'Vigente', 'RC ', 'Colaborador', 'Destacado', 'buceador', 'participante', 'aseguradora')
            ours = sorted(m for m in misses if any(w.lower() in m.lower() for w in ins_words))
            if out:
                (out / 'textos-sin-traducir.json').write_text(json.dumps(sorted(misses), ensure_ascii=False, indent=1), encoding='utf-8')
            check('8 · en inglés, ningún texto de los seguros sin traducir', not ours, ours[:40])
            browser.close()
        check('sin errores de JavaScript', not errors, errors)
    finally:
        srv.stop()
    print(f"{sum(1 for _, ok in rows if ok)}/{len(rows)} comprobaciones")
    return all(ok for _, ok in rows)


if __name__ == '__main__':
    target = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    sys.exit(0 if run(target) else 1)
