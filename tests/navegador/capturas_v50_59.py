#!/usr/bin/env python3
"""Encargo del 17/10/2026 · capturas «antes» y «después» de la primera entrega (Bloques 1 a 3).

Siempre sobre una copia nueva de la demo (nunca la base con datos reales), en escritorio (1440 × 900) y en móvil
(390 × 844). Con --raiz se hace con el código de otra carpeta (la copia del código de antes del encargo) para las
capturas «antes»; las pantallas que todavía no existían allí se anotan como «no existía».

    python3 tests/navegador/capturas_v50_59.py docs/capturas/v50.59/despues
    python3 tests/navegador/capturas_v50_59.py docs/capturas/v50.59/antes --raiz <carpeta con el código de antes>
"""
from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--raiz', default=str(Path(__file__).resolve().parents[2]))
ap.add_argument('--solo', default='')
A = ap.parse_args()
ROOT = Path(A.raiz).resolve()
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'app')]
from helpers import Server  # noqa: E402
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PASSWORD = re.search(r"PASSWORD = '([^']+)'", (Path(__file__).resolve().parent / 'e2e_avisos.py').read_text()).group(1)
CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
OUT = Path(A.out); OUT.mkdir(parents=True, exist_ok=True)
SIZES = {'escritorio': (1440, 900), 'movil': (390, 844)}


def shots(ids):
    """(name, account, address, steps, element to capture or None for the screen). Steps: 'click:<css>'."""
    pid, cid = ids['punto'], ids['centro']
    return [
        ('1.1-menu-perfil', 'buzo.prueba', '#/area', ['click:#account-toggle'], None),
        ('1.2-ficha-punto-franja', None, f'#/punto?id={pid}', ['scroll:.pt-strip,.point-strip,.pt-icons'], None),
        ('1.2-admin-datos-por-tipo', 'admin.prueba', '#/admin?tab=divetypes', ['click:.tf-type summary'], '#admin-typefields'),
        ('1.3-cabecera-centros', None, '#/centros', [], None),
        ('1.3-cabecera-tipos', None, '#/tipos', [], None),
        ('1.3-cabecera-puntos', None, '#/puntos', [], None),
        ('1.3-cabecera-experiencias', None, '#/experiencias', [], None),
        ('1.3-cabecera-top10', None, '#/top10', [], None),
        ('1.3-cabecera-freelance', None, '#/freelance', [], None),
        ('1.4-menu-centro', 'centro.prueba', '#/admin', [], '.cb-sidebar'),
        ('1.5-reservar-categorias', None, f'#/reservar?center={cid}', [], '#bk-services'),
        ('1.5-reservar-una-categoria', None, f'#/reservar?center={cid}', ['click:.bk-cat'], '#bk-services'),
        ('1.5-servicios-categoria', 'centro.prueba', '#/admin?tab=services', [], None),
        ('1.5-servicios-ordenar', 'centro.prueba', '#/admin?tab=services', ['click:.svc-order-open'], '#svc-order .wd-modal-card'),
        ('1.5-admin-categorias', 'admin.prueba', '#/admin?tab=svctemplates', ['click:.bc-cat summary'], '#admin-book-cats'),
        ('1.6-exportar-gestoria', 'centro.prueba', '#/admin?tab=analytics', ['click:[data-gestoria]', 'wait:.ge-kpis'], '#gestoria .wd-modal-card'),
        ('1.7-menu-buceador', 'buzo.prueba', '#/area', ['click:#account-toggle'], '#account-dropdown'),
        ('1.7-buddies', 'buzo.prueba', '#/buddies', [], None),
        ('1.7-mi-qr', 'buzo.prueba', '#/mi-qr', [], None),
        ('1.7-ruta-profesional', 'buzo.prueba', '#/mi-agenda', [], None),
    ]


def main():
    db = Path(tempfile.mkdtemp(prefix='wod-cap-')) / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(db)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=db).start()
    report = {}
    try:
        ids = {'punto': srv.sql("SELECT id FROM dive_points WHERE name LIKE 'Escull de Sant Pere%' AND active=1")[0]['id'],
               'centro': srv.sql("SELECT c.id FROM centers c JOIN users u ON u.center_id=c.id WHERE u.username='centro.prueba'")[0]['id']}
        with sync_playwright() as p:
            b = p.chromium.launch(executable_path=CHROME)
            for size, (w, h) in SIZES.items():
                for name, user, url, steps, el in shots(ids):
                    if A.solo and not any(s in name for s in A.solo.split(',')): continue
                    ctx = b.new_context(viewport={'width': w, 'height': h}, locale='es-ES', has_touch=size == 'movil', is_mobile=size == 'movil')
                    ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                    pg = ctx.new_page(); errors = []
                    pg.on('pageerror', lambda e: errors.append(str(e)[:160]))
                    if user:
                        pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login-form'); pg.fill('#login', user); pg.fill('#password', PASSWORD)
                        pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1500)
                    pg.goto(srv.base + '/' + url); pg.wait_for_timeout(2200)
                    note = ''
                    for st in steps:
                        kind, _, sel = st.partition(':')
                        try:
                            if kind == 'click': pg.click(sel, timeout=5000); pg.wait_for_timeout(1000)
                            elif kind == 'wait': pg.wait_for_selector(sel, timeout=10000)
                            elif kind == 'scroll': pg.locator(sel).first.scroll_into_view_if_needed(timeout=5000); pg.wait_for_timeout(400)
                        except Exception:
                            note = f'no existía ({sel})'
                    path = OUT / f'{name}-{size}.png'
                    try:
                        if el and not note: pg.locator(el).first.screenshot(path=str(path), timeout=8000)
                        else: pg.screenshot(path=str(path))
                    except Exception:
                        pg.screenshot(path=str(path)); note = note or f'no existía ({el})'
                    report[f'{name}-{size}'] = {'url': url, 'nota': note, 'errores': errors}
                    print(f'{name:32} {size:10} {note}', flush=True)
                    ctx.close()
            b.close()
    finally:
        srv.stop()
    (OUT / 'capturas.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')


if __name__ == '__main__':
    main()
