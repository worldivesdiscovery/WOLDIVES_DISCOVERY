#!/usr/bin/env python3
"""v50.57 · Revisión general 5.1: los cuatro modos completos, pantalla a pantalla, en un navegador real (Chromium) sobre
una copia de la demo: administración, centro, freelance y buceador, en el ordenador (1366 px) y en el móvil (390 px).

En cada pantalla (cada pestaña de cada panel, y las páginas del buceador):
- sin errores de JavaScript ni respuestas de error del servidor (500) ni peticiones rechazadas que la web no esperaba;
- sin textos rotos («undefined», «NaN», «[object Object]», «No se ha podido abrir», «Error interno»);
- en el móvil, nada queda fuera de la pantalla (la web recorta lo que pasa del borde derecho: no se vería ni se podría
  alcanzar).
Con especial atención (el titular encontró fallos ahí):
- centro: reservas, planning y agenda con sus datos;
- freelance: reservas, planning y «Mi agenda» con sus datos;
- administración: destinos, puntos y plantillas: abrir uno, guardarlo sin cambios y volver a la lista con «Guardado».
En el móvil, «Visitas y reservas» (4.2) enseña todos sus números sin desplazar la tabla de lado.
Y, del recorrido de botones (2.2): el instructor del centro, sin permiso de avisos, ve por qué sus ajustes están apagados.

    python3 tests/navegador/e2e_v50_57_modos.py [carpeta-de-capturas]

Usa las cuentas de la demo: no va en el zip de producción (scripts/generar_zips.py)."""
from __future__ import annotations

import json
import re
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

ROOT = Path(__file__).resolve().parents[2]
BROKEN = re.compile(r'\bundefined\b|\bNaN\b|\[object Object\]|No se ha podido abrir|Error interno|Falta un dato obligatorio')
SIZES = {'ordenador': {'width': 1366, 'height': 900}, 'movil': {'width': 390, 'height': 844}}
DIVER_PAGES = ['#/area', '#/cuenta', '#/logbook', '#/recompensas', '#/mis-puntos', '#/seguro', '#/reserva?id={booking}']
# What reaches beyond the right edge of the screen. The web clips it (html and body have overflow-x: clip), so it can
# neither be seen nor reached, and the page never gets wider: document.documentElement.scrollWidth does not show it.
# Only the outermost boxes, and nothing inside a box that slides sideways on purpose (a table in its .table-wrap).
BEYOND = """() => { const W = innerWidth, out = [];
  const clipper = el => { for (let p = el.parentElement; p && p !== document.body; p = p.parentElement) if (getComputedStyle(p).overflowX !== 'visible') return p; return null; };
  const inView = p => p && p.getBoundingClientRect().right <= W + 1;
  for (const el of document.querySelectorAll('main *')) {
    const r = el.getBoundingClientRect(); if (!r.width || !r.height || r.right <= W + 1) continue;
    const cs = getComputedStyle(el); if (cs.position === 'fixed' || cs.visibility === 'hidden' || (el.closest('svg') && el.tagName.toLowerCase() !== 'svg')) continue;
    if (inView(clipper(el))) continue;
    const par = el.parentElement; if (par && par.getBoundingClientRect().right > W + 1 && !inView(clipper(par))) continue;
    out.push(el.tagName.toLowerCase() + (el.id ? '#' + el.id : '') + (el.classList.length ? '.' + [...el.classList].slice(0, 2).join('.') : '') + ' → ' + Math.round(r.right) + ' px');
  }
  return out.slice(0, 5); }"""
# Answers the web asks for knowing they may say no (checked by the screens themselves, not errors).
EXPECTED_4XX = ('/api/admin/confirm/status', '/api/logbook', '/api/insurance', '/api/me/insurance')


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else None
    db = Path(tempfile.mkdtemp(prefix='wod-modos-')) / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(db)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=db).start()
    rows, report = [], {}

    def check(what, ok, detail=''):
        rows.append((what, bool(ok)))
        print(('OK  ' if ok else 'MAL ') + what + ('' if ok else f'  → {str(detail)[:500]}'), flush=True)

    try:
        booking = srv.sql("SELECT b.id FROM bookings b JOIN users u ON u.id=b.user_id WHERE u.username='buzo.prueba' ORDER BY b.id DESC LIMIT 1")[0]['id']
        by_days = srv.sql("SELECT b.id FROM bookings b JOIN users u ON u.id=b.user_id WHERE u.username='buzo.prueba' AND b.price_breakdown LIKE '%\"discount\"%' ORDER BY b.id DESC LIMIT 1")
        with sync_playwright() as pw:
            browser = chromium(pw)
            for size, viewport in SIZES.items():
                for role, user in (('administración', 'admin.prueba'), ('centro', 'centro.prueba'), ('freelance', 'freelance.prueba'), ('buceador', 'buzo.prueba')):
                    ctx = browser.new_context(viewport=viewport, locale='es-ES')
                    ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                    pg = ctx.new_page(); errs = []; bad = []
                    pg.on('pageerror', lambda e: errs.append(str(e)[:200]))
                    pg.on('response', lambda rsp: bad.append(f'{rsp.status} {rsp.request.method} {rsp.url.split("?")[0].replace(srv.base, "")}')
                          if '/api/' in rsp.url and (rsp.status >= 500 or (rsp.status >= 400 and not rsp.url.split('?')[0].endswith(EXPECTED_4XX))) else None)
                    pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login-form')
                    pg.fill('#login', user); pg.fill('#password', PASSWORD); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1500)
                    if role == 'administración':   # 4.1: personal data with the password and a reason (as the window does)
                        pg.evaluate("""() => fetch('/api/admin/confirm', {method: 'POST', headers: {'Content-Type': 'application/json'},
                                       body: JSON.stringify({password: '%s', reason: 'Soporte: auditoría de los cuatro modos'})}).then(r => r.text())""" % PASSWORD)
                    if role == 'buceador':
                        screens = [p.format(booking=booking) for p in DIVER_PAGES]
                    else:
                        pg.goto(srv.base + '/#/admin'); pg.wait_for_selector('.cb-nav, .provider-tabs .tab', timeout=20000); pg.wait_for_timeout(800)
                        keys = pg.evaluate("[...document.querySelectorAll('.cb-nav[data-cbtab], .provider-tabs .tab[data-tab]')].map(b => b.dataset.cbtab || b.dataset.tab)")
                        screens = [f'#/admin?tab={k}' for k in dict.fromkeys(keys)]
                    seen = []
                    for route in screens:
                        errs.clear(); bad.clear()
                        pg.goto(srv.base + '/' + route); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(900)
                        txt = pg.inner_text('main') if pg.locator('main').count() else ''
                        broken = sorted(set(m.group(0) for m in BROKEN.finditer(txt)))
                        beyond = pg.evaluate(BEYOND) if size == 'movil' else []
                        ok = not errs and not bad and not broken and not beyond and len(txt.strip()) > 40
                        seen.append({'pantalla': route, 'ok': ok, 'errores_js': errs[:3], 'peticiones_con_error': bad[:5], 'textos_rotos': broken, 'fuera_de_la_pantalla': beyond,
                                     'texto': len(txt.strip())})
                        check(f'{size} · {role} · {route}', ok, seen[-1])
                        if out:   # every screen, on the computer and on the phone, to look at them one by one
                            (out / size).mkdir(parents=True, exist_ok=True)
                            pg.screenshot(path=str(out / size / f'{role}-{re.sub(r"[^a-z0-9]+", "-", route.lower()).strip("-")}.png'), full_page=True)
                    report[f'{size}/{role}'] = seen

                    # ------------------------------------------------------------ special attention
                    if size == 'ordenador' and role in ('centro', 'freelance'):
                        for tab, sel in (('bookings', '#cb-bookings .bk-row, #fl-bookings .bk-row'),
                                         ('planning', '#cb-planning .pl-cell.has-events, #fl-planning .pl-cell.has-events'),   # month view: days with dives
                                         ('agenda', '#fl-agenda .ag-item, #fl-agenda .dbk-card')):
                            if role == 'centro' and tab == 'agenda': continue          # the centre has «Planning / agenda» in one
                            pg.goto(f'{srv.base}/#/admin?tab={tab}'); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(900)
                            n = pg.locator(sel).count()
                            check(f'{role} · {tab}: se abre con sus datos', n > 0, n)
                    if role in ('centro', 'freelance'):
                        # 5.1: the time and number of each booking showed as «0…» (a style of the booking flow with the same
                        # name) and between 761 and 1180 px the state of the booking was hidden
                        pg.goto(f'{srv.base}/#/admin?tab=bookings'); pg.wait_for_selector('.bk-row'); pg.wait_for_timeout(700)
                        bk = pg.evaluate("""() => [...document.querySelectorAll('.bk-row')].slice(0, 5).map(r => { const t = r.querySelector('.bk-time strong'), n = r.querySelector('.bk-time span'), st = r.querySelector('.bk-state');
                            return [t.textContent, t.scrollWidth <= t.clientWidth + 1 && n.scrollWidth <= n.clientWidth + 1, !!st.offsetParent && st.getBoundingClientRect().width > 0]; })""")
                        check(f'{size} · {role} · reservas: la hora y el número se ven enteros y el estado se ve', bk and all(r[1] and r[2] for r in bk), bk)
                        # 5.1 (looking at every capture): the filters «Desde» and «Hasta» took the style of the day buttons of
                        # the booking flow (same class): boxes of 74 px where no date fits
                        dates = pg.evaluate("[...document.querySelectorAll('#bk-from, #bk-to')].map(i => Math.round(i.getBoundingClientRect().width))")
                        check(f'{size} · {role} · reservas: en «Desde» y «Hasta» cabe la fecha', len(dates) == 2 and min(dates) >= 120, dates)
                    if size == 'ordenador' and role == 'buceador':
                        # 5.1 (looking at every capture): the price of a booking by days with a discount said «−10 % desde
                        # 3 días: 1 × 0.00 €» (a discount has no unit price) and the amounts had a decimal point («486.00 EUR»)
                        check('buceador · la demo tiene una reserva por días con descuento', bool(by_days), by_days)
                        if by_days:
                            pg.goto(f"{srv.base}/#/reserva?id={by_days[0]['id']}"); pg.wait_for_selector('.booking-price-lines', timeout=20000); pg.wait_for_timeout(500)
                            price = pg.evaluate("(() => { const s = document.querySelector('.booking-price-lines'); return [s.previousElementSibling.textContent, s.innerText]; })()")
                            check('buceador · reserva por días: el descuento dice su importe y los importes van en euros con coma',
                                  '× 0' not in price[1] and re.search(r'desde \d+ días: [−-]\s?\d', price[1]) and 'EUR' not in price[0] and not re.search(r'\d\.\d\d', ' '.join(price)), price)
                    if size == 'movil' and role != 'buceador':
                        # 5.1 (looking at every capture): on a phone the numbers of «Visitas y reservas» (4.2) were all out of
                        # sight, at the right of a table that scrolled sideways
                        pg.goto(f"{srv.base}/#/admin?tab={'audit' if role == 'administración' else 'stats'}"); pg.wait_for_selector('.vc-block .table-wrap', timeout=20000); pg.wait_for_timeout(500)
                        fit = pg.evaluate("""() => { const w = document.querySelector('.vc-block .table-wrap'), r = w.getBoundingClientRect(), cells = [...w.querySelectorAll('tbody td')];
                            return {celdas: cells.length, fuera: cells.filter(c => c.getBoundingClientRect().right > r.right + 1).length, ancho: w.scrollWidth, caja: w.clientWidth}; }""")
                        check(f'{size} · {role} · «Visitas y reservas»: todos los números se ven sin desplazar de lado', fit['celdas'] > 0 and fit['fuera'] == 0, fit)
                    if size == 'ordenador' and role == 'administración':
                        # 2.2 (button walk): «Subir» on the first template and «Bajar» on the last did nothing; now they are off
                        pg.goto(f'{srv.base}/#/admin?tab=svctemplates'); pg.wait_for_selector('.st-card .st-up'); pg.wait_for_timeout(500)
                        arrows = pg.evaluate("(()=>{const c=[...document.querySelectorAll('.st-grid .st-card')];return c.map((x,i)=>[x.querySelector('.st-up').disabled,x.querySelector('.st-down').disabled])})()")
                        check('administración · plantillas: ↑ apagada en la primera y ↓ en la última, las demás activas',
                              arrows and arrows[0][0] and arrows[-1][1] and not any(a[0] for a in arrows[1:]) and not any(a[1] for a in arrows[:-1]), arrows)
                        why = pg.evaluate("[document.querySelector('.st-grid .st-card .st-up').title, [...document.querySelectorAll('.st-grid .st-card .st-down')].pop().title]")
                        check('administración · plantillas: la flecha apagada dice por qué', why == ['Ya es la primera: no se puede subir más', 'Ya es la última: no se puede bajar más'], why)
                        pg.locator('.st-grid .st-card').nth(1).locator('.st-up').click(); pg.wait_for_timeout(800)
                        arrows = pg.evaluate("(()=>{const c=[...document.querySelectorAll('.st-grid .st-card')];return c.map((x,i)=>[x.querySelector('.st-up').disabled,x.querySelector('.st-down').disabled])})()")
                        check('administración · plantillas: después de subir una, siguen bien las flechas', arrows[0][0] and not arrows[1][0] and arrows[-1][1], arrows)
                        for tab, edit, save in (('destinations', '.edit-destination', '#destination-form button.btn-primary'),
                                                ('points', '.edit-point', '#point-form button.btn-primary'),
                                                ('svctemplates', '.st-edit', 'button[type=submit][form=stf]')):
                            errs.clear(); bad.clear()
                            pg.goto(f'{srv.base}/#/admin?tab={tab}'); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(900)
                            btn = pg.locator(edit).first
                            if not btn.count():
                                check(f'administración · {tab}: hay algo que editar', False, edit); continue
                            btn.click(); pg.wait_for_timeout(1200)
                            sub = pg.locator(save).first
                            if not sub.count():
                                check(f'administración · {tab}: el formulario tiene «Guardar»', False, save); continue
                            sub.click(); pg.wait_for_timeout(1500)
                            toast = pg.evaluate("document.querySelector('#toast')?.textContent||''")
                            h = pg.evaluate('location.hash')
                            check(f'administración · {tab}: abrir uno y guardarlo sin cambios vuelve a la lista con «Guardado»',
                                  ('Guardado' in toast or 'guardad' in toast.lower()) and h.startswith(f'#/admin?tab={tab}') and 'edit=' not in h and not errs and not bad,
                                  {'aviso': toast, 'dirección': h, 'errores': errs[:2], 'peticiones': bad[:3]})
                    ctx.close()
            # 2.2 (button walk): a member of the team whose profile cannot send notices saw the notice settings switched
            # off with no word about why; now the panel says it (the owner, who can change them, does not see it)
            for user, can in (('instructor.prueba', False), ('centro.prueba', True)):
                ctx = browser.new_context(viewport=SIZES['ordenador'], locale='es-ES')
                ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg = ctx.new_page()
                pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login-form')
                pg.fill('#login', user); pg.fill('#password', PASSWORD); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1500)
                pg.goto(f'{srv.base}/#/admin?tab=avisos'); pg.wait_for_selector('#nt-set'); pg.wait_for_timeout(600)
                st = pg.evaluate("({note: document.querySelector('#nt-cannot')?.textContent || '', off: document.querySelector('#nt-hour').disabled})")
                if can:
                    check('centro · avisos: el propietario puede cambiar los ajustes y no ve el aviso de permiso', not st['note'] and not st['off'], st)
                else:
                    check('instructor del centro · avisos: los ajustes apagados dicen por qué', st['off'] and st['note'] ==
                          'Tu perfil no permite cancelar salidas ni avisar a todos los clientes. Pídeselo al propietario del centro.', st)
                ctx.close()
            browser.close()
    finally:
        srv.stop()
    if out: (out / 'modos.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    bad_rows = [n for n, ok in rows if not ok]
    print(f'\n{len(rows) - len(bad_rows)}/{len(rows)} comprobaciones correctas')
    return 1 if bad_rows else 0


if __name__ == '__main__':
    sys.exit(main())
