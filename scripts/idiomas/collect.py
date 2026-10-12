#!/usr/bin/env python3
"""Collects the texts of the web that have no translation yet (Fase 1D / final pass).

Starts a test server on a COPY of the demo catalogue, creates the five roles (visitor, diver, centre, freelance,
administrator) with some data, and visits every screen in English with the translation audit on (localStorage
«wd-i18n-debug»=1). Every text the page could not translate is saved in scripts/idiomas/datos/missing.json, and every text seen
(translated or not) is added to scripts/idiomas/datos/source_strings.json (the reference of scripts/idiomas/report.py).

    python3 scripts/idiomas/collect.py
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'tests'))
from helpers import ServerTestCase, Server  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

OUT = ROOT / 'scripts' / 'idiomas' / 'datos'
PW = 'buceo-seguro-2026'
PUBLIC = ['#/', '#/explorar', '#/puntos', '#/centros', '#/tipos', '#/experiencias', '#/top10', '#/planes', '#/login', '#/registro', '#/registro?tipo=recreational', '#/registro?tipo=center',
          '#/registro?tipo=freelance', '#/recuperar',
          '#/como-funcionan-los-puntos', '#/legal/aviso-legal', '#/legal/condiciones-buceadores', '#/legal/privacidad', '#/legal/cookies',
          '#/legal/denuncias', '#/legal/accesibilidad', '#/legal/contacto', '#/legal/creditos', '#/reservar']
DIVER = ['#/area', '#/cuenta', '#/logbook', '#/mis-puntos', '#/recompensas', '#/reservas']
CENTER_TABS = ['dashboard', 'planning', 'bookings', 'clients', 'services', 'experiences', 'payments', 'analytics', 'integration', 'points', 'qr', 'center',
               'rewards', 'requests', 'stats', 'tools', 'team', 'activity', 'fiscal', 'plan']
FREE_TABS = ['dashboard', 'bookings', 'planning', 'services', 'experiences', 'payments', 'profile', 'requests', 'stats', 'tools', 'fiscal', 'plan']
ADMIN_TABS = ['overview', 'adminpay', 'emails', 'legal', 'pointtexts', 'maps', 'plans', 'features', 'ops', 'media', 'promos', 'virtual', 'audit',
              'destinations', 'experiences', 'users', 'centers', 'claims', 'suggestions', 'qr', 'rewards', 'bookings', 'points']


def chromium(p):
    exe = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
    return p.chromium.launch(executable_path=exe) if Path(exe).exists() else p.chromium.launch()


def main():
    ServerTestCase.server = Server().start()
    srv = ServerTestCase.server
    t = ServerTestCase('run')
    misses, seen = set(), set()
    try:
        admin = t.make_admin()
        center = t.make_center(admin, 'i18n')
        free = t.make_freelance(admin, 'i18npro')
        diver = t.make_diver('i18n')
        cid = center.user['center_id']
        sid = center.post('/api/provider-services', {'title': 'Inmersión de prueba', 'price': 45, 'booking_mode': 'request'}).json['id']
        slot = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-06-10', 'slot_time': '10:00', 'spots_total': 8}).json['slot_id']
        diver.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': 2})
        pid = srv.sql('SELECT id FROM dive_points WHERE active=1 LIMIT 1')[0]['id']
        with sync_playwright() as p:
            browser = chromium(p)

            def ctx_for(login=None, pw=PW, width=1366):
                ctx = browser.new_context(viewport={'width': width, 'height': 900}, locale='en-GB')
                ctx.add_init_script("try{localStorage.setItem('wd-i18n-debug','1');localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                page = ctx.new_page()
                page.goto(srv.base + '/?lang=en#/'); page.wait_for_load_state('networkidle')
                if login:
                    page.goto(srv.base + '/?lang=en#/login'); page.wait_for_selector('#login'); page.fill('#login', login); page.fill('#password', pw)
                    page.click('#login-form button[type=submit]'); page.wait_for_timeout(1000)
                return ctx, page

            def harvest(page):
                try:
                    m = page.evaluate('window.__wdI18nMisses?[...window.__wdI18nMisses]:[]')
                    misses.update(m)
                    seen.update(page.evaluate("[...document.querySelectorAll('body *')].flatMap(e=>[...e.childNodes].filter(n=>n.nodeType===3).map(n=>n.nodeValue.trim())).filter(Boolean).slice(0,5000)"))
                except Exception:
                    pass

            def visit(page, route, wait=900, click=None):
                page.goto(srv.base + '/?lang=en' + route); page.wait_for_load_state('networkidle'); page.wait_for_timeout(wait)
                if click:
                    for sel in click:
                        try: page.locator(sel).first.click(timeout=1500); page.wait_for_timeout(500); harvest(page); page.keyboard.press('Escape')
                        except Exception: pass
                harvest(page)

            ctx, page = ctx_for()
            for r in PUBLIC: visit(page, r)
            visit(page, f'#/punto?id={pid}', click=['.wd-report'])
            visit(page, f'#/centro?id={cid}', click=['.wd-report[data-report="center"]'])
            visit(page, f'#/reservar?center={cid}&service={sid}')
            ctx.close()
            for login, pw, routes in (('diver_i18n', PW, DIVER), ):
                ctx, page = ctx_for(login, pw)
                for r in routes: visit(page, r)
                visit(page, '#/cuenta', click=['#acc-delete'])
                ctx.close()
            ctx, page = ctx_for('center_i18n')
            for tab in CENTER_TABS: visit(page, f'#/admin?tab={tab}', 1200)
            ctx.close()
            ctx, page = ctx_for('pro_i18npro')
            for tab in FREE_TABS: visit(page, f'#/admin?tab={tab}', 1200)
            ctx.close()
            ctx, page = ctx_for('admin', 'admin-seguro-2026')
            for tab in ADMIN_TABS: visit(page, f'#/admin?tab={tab}', 1400)
            visit(page, '#/admin?tab=legal', 1400, click=['.adl-edit'])
            visit(page, '#/admin?tab=plans', 1400, click=['.ap-manage'])
            ctx.close()
            browser.close()
    finally:
        srv.stop()
    OUT.mkdir(parents=True, exist_ok=True)
    clean = sorted(m for m in misses if len(m) < 600)
    (OUT / 'missing.json').write_text(json.dumps(clean, ensure_ascii=False, indent=1), encoding='utf-8')
    src = OUT / 'source_strings.json'
    old = set(json.loads(src.read_text(encoding='utf-8'))) if src.exists() else set()
    (src).write_text(json.dumps(sorted(old | set(clean)), ensure_ascii=False, indent=0), encoding='utf-8')
    print(f'{len(clean)} textos sin traducir → {OUT / "missing.json"}')


if __name__ == '__main__':
    main()
