#!/usr/bin/env python3
"""v50.54 · punto 8 en un navegador real (Chromium) sobre la demo: la administración modera, no edita.

1. Administración → Centros: un centro con titular no tiene «Editar», sí «Ocultar…». Se oculta con un motivo.
2. La ficha pública desaparece. El centro entra y ve el aviso con el motivo; lo envía a revisión con una nota.
3. Administración → Moderación: el caso aparece «Enviado a revisión» con la nota; «Volver a publicar». La ficha vuelve.
4. Administración → Datos personales: casillas con «PENDIENTE DE ABOGADO»; guardar pide un motivo.
5. Administración → Actividad: cada paso con su nombre, quién, cuándo y el motivo.

    python3 tests/navegador/e2e_v50_54_moderacion.py [carpeta-de-capturas]
"""
from __future__ import annotations

import subprocess
import sys
import tempfile
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1]), str(Path(__file__).resolve().parents[2] / 'app')]
from helpers import Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
REASON = 'Las fotos de la galería son de otro centro: súbelas propias.'


def main():
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='wod-e2e-mod-'))
    out.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp(prefix='wod-demo-')) / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(tmp)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=tmp).start()
    rows, problems = [], []

    def check(what, ok, detail=''):
        rows.append((what, bool(ok)))
        if not ok: problems.append(f'{what}: {detail}')

    try:
        cid = srv.sql("SELECT id FROM centers WHERE name LIKE 'Bahía Coralina%'")[0]['id']
        with sync_playwright() as pw:
            browser = chromium(pw)
            errors = []

            def session(cuenta):
                ctx = browser.new_context(viewport={'width': 1366, 'height': 900}, locale='es-ES')
                pg = ctx.new_page()
                pg.on('pageerror', lambda e: errors.append(str(e)))
                pg.on('console', lambda m: errors.append(m.text) if m.type == 'error' and 'ERR_TUNNEL' not in m.text and 'status of 4' not in m.text else None)
                pg.on('dialog', lambda d: d.accept('Correcto, gracias.') if d.type == 'prompt' else d.accept())
                pg.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
                pg.goto(srv.base + '/#/login'); pg.wait_for_selector('.demo-quick [data-demo-login]')
                pg.click(f'[data-demo-login="{cuenta}"]'); pg.wait_for_timeout(1800)
                return ctx, pg

            # 1. the administration hides a centre with an owner
            ctx, pg = session('admin.prueba')
            pg.goto(srv.base + '/#/admin?tab=centers'); pg.wait_for_selector('.mod-hide-btn'); pg.wait_for_timeout(400)
            row = pg.locator('tr', has_text='Bahía Coralina')
            check('Centros: un centro con titular no se edita, se oculta', row.locator('.edit-center').count() == 0 and row.locator('.mod-hide-btn').count() == 1)
            pg.screenshot(path=str(out / 'admin-centros.png'))
            row.locator('.mod-hide-btn').click(); pg.wait_for_selector('#mod-reason')
            pg.fill('#mod-reason', REASON); pg.screenshot(path=str(out / 'admin-ocultar-motivo.png'))
            pg.click('#mod-hide-ok'); pg.wait_for_timeout(1200)
            check('El servidor no deja editar el centro', pg.evaluate(f"fetch('/api/centers/update',{{method:'POST',headers:{{'Content-Type':'application/json','X-Admin-Reason':'prueba'}},body:JSON.stringify({{id:{cid},name:'X',country:'España',latitude:1,longitude:1}})}}).then(r=>r.status)") == 403)
            ctx.close()
            pub = browser.new_page(); pub.goto(srv.base + f'/#/centro?id={cid}'); pub.wait_for_timeout(1500)
            check('La ficha pública ya no se ve', 'Bahía Coralina' not in pub.inner_text('#app'))
            pub.close()

            # 2. the centre sees why and sends it for review
            ctx, pg = session('centro.prueba')
            pg.goto(srv.base + '/#/admin'); pg.wait_for_selector('.mod-banner'); pg.wait_for_timeout(300)
            check('El centro ve el aviso con el motivo', REASON in pg.inner_text('.mod-banner'))
            pg.screenshot(path=str(out / 'centro-aviso.png'))
            pg.fill('.mod-banner [data-mod-note]', 'He subido fotos propias de nuestro barco y del centro.')
            pg.click('.mod-banner [data-mod-resubmit]'); pg.wait_for_timeout(1200)
            check('Enviado a revisión', 'Lo estamos revisando' in pg.inner_text('.mod-banner'))
            ctx.close()

            # 3. the administration publishes it again
            ctx, pg = session('admin.prueba')
            pg.goto(srv.base + '/#/admin?tab=moderation'); pg.wait_for_selector('.mod-case'); pg.wait_for_timeout(300)
            case = pg.locator('.mod-case').first
            check('Moderación: enviado a revisión, con la nota del centro', 'Enviado a revisión' in case.inner_text() and 'fotos propias' in case.inner_text())
            pg.screenshot(path=str(out / 'admin-moderacion.png'))
            case.locator('[data-mod-restore]').click(); pg.wait_for_timeout(1200)
            check('Publicado de nuevo', 'Publicado de nuevo' in pg.inner_text('.mod-list'))
            # 4. personal data switches
            pg.goto(srv.base + '/#/admin?tab=privacy'); pg.wait_for_selector('#privacy-form'); pg.wait_for_timeout(300)
            txt = pg.inner_text('#admin-privacy')
            check('Datos personales: casillas y PENDIENTE DE ABOGADO', 'PENDIENTE DE ABOGADO' in txt and pg.locator('#privacy-form input[type=checkbox]').count() == 6)
            pg.screenshot(path=str(out / 'admin-datos-personales.png'))
            # 5. the activity log tells who, when and why, with readable names
            pg.goto(srv.base + '/#/admin?tab=audit'); pg.wait_for_selector('#admin-content table'); pg.wait_for_timeout(300)
            log = pg.inner_text('#admin-content')
            check('Actividad: los pasos con su nombre y el motivo', all(x in log for x in ('Contenido ocultado con un motivo', 'Corrección enviada a revisión',
                                                                                         'Publicado de nuevo tras la revisión', REASON)), log[:400])
            pg.screenshot(path=str(out / 'admin-actividad.png'))
            ctx.close()
            pub = browser.new_page(); pub.goto(srv.base + f'/#/centro?id={cid}'); pub.wait_for_timeout(1500)
            check('La ficha pública vuelve a verse', 'Bahía Coralina' in pub.inner_text('#app'))
            pub.close()
            steps = [r['action'] for r in srv.sql("SELECT action FROM audit_log WHERE action LIKE 'moderation_%' AND entity_id=? ORDER BY id", (cid,))]
            check('Todo queda en la actividad', steps == ['moderation_hidden', 'moderation_resubmitted', 'moderation_restored'], steps)
            browser.close()
            check('Sin errores en la consola', not errors, errors[:4])
    finally:
        srv.stop()
    for what, ok in rows: print(f"{'OK ' if ok else 'MAL'} {what}")
    print(f'Capturas en {out}')
    if problems:
        print('PROBLEMAS:\n - ' + '\n - '.join(problems)); sys.exit(1)
    print('OK: la administración modera, el centro corrige y se vuelve a publicar; todo registrado.')


if __name__ == '__main__':
    main()
