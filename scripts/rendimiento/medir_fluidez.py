#!/usr/bin/env python3
"""Encargo del 17/10 · Bloque 8 · Medición de fluidez de las pantallas del punto 8.1, sin tocar la web.

Sobre una copia nueva de la demo (nunca la base con datos reales), en Chromium, con tres perfiles:

- «Android de gama media»: 390 × 844, pantalla táctil y procesador 4 veces más lento; pantalla de 60 Hz.
- «Móvil de 120 Hz»: 390 × 844, táctil y procesador 2 veces más lento (un móvil de gama alta); pantalla de 120 Hz.
- «Ordenador normal»: 1440 × 900, sin frenar el procesador; pantalla de 60 Hz.

Por cada pantalla mide la carga (LCP, CLS y tareas largas al cargar) y una interacción típica (desplazarse, mover el
mapa, abrir el calendario, pulsar en el menú…):

- Tareas largas (más de 50 ms) durante la interacción, con la más larga.
- INP: la respuesta más lenta a un toque o una tecla (Event Timing del propio navegador).
- Trabajo por fotograma en el hilo principal: desde que empieza el fotograma (requestAnimationFrame) hasta que el hilo
  queda libre después de pintar (un mensaje de MessageChannel puesto en ese mismo fotograma). Un fotograma que pasa de
  8,3 ms se pierde en una pantalla de 120 Hz, y uno que pasa de 16,7 ms, en una de 60 Hz.

Limitación: aquí no hay pantalla (Chromium sin pantalla dibuja siempre a 60 fotogramas por segundo y con la tarjeta
gráfica simulada). El trabajo por fotograma es una estimación del hilo principal; la medida con un móvil y un portátil
de 120 Hz de verdad queda para hacerla en esos aparatos (ver el informe).

    python3 scripts/rendimiento/medir_fluidez.py <salida.json> [--repeticiones 3]
"""
from __future__ import annotations

import argparse
import json
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'tests' / 'navegador'), str(ROOT / 'app'), str(ROOT / 'scripts')]
from helpers import Server  # noqa: E402
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402
from crear_demo import PASSWORD  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

EXE = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'
PROFILES = {
    'android': {'label': 'Android de gama media', 'cpu': 4, 'hz': 60,
                'ctx': {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 2.6}},
    'movil120': {'label': 'Móvil de 120 Hz', 'cpu': 2, 'hz': 120,
                 'ctx': {'viewport': {'width': 390, 'height': 844}, 'is_mobile': True, 'has_touch': True, 'device_scale_factor': 3}},
    'ordenador': {'label': 'Ordenador normal', 'cpu': 1, 'hz': 60, 'ctx': {'viewport': {'width': 1440, 'height': 900}}},
}

# Installed before the page: load vitals, long tasks, interactions (Event Timing) and the frame probe.
PROBE = r"""
(() => {
  const W = window.__wdPerf = {lcp: 0, cls: 0, long: [], events: [], frames: [], probing: false};
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) W.lcp = e.startTime; }).observe({type: 'largest-contentful-paint', buffered: true}); } catch (e) {}
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) if (!e.hadRecentInput) W.cls += e.value; }).observe({type: 'layout-shift', buffered: true}); } catch (e) {}
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) W.long.push([e.startTime, e.duration]); }).observe({type: 'longtask', buffered: true}); } catch (e) {}
  try { new PerformanceObserver(l => { for (const e of l.getEntries()) if (e.interactionId) W.events.push([e.startTime, e.duration, e.name]); })
          .observe({type: 'event', buffered: true, durationThreshold: 16}); } catch (e) {}
  const ch = new MessageChannel(); let pending = null;
  ch.port1.onmessage = () => { if (pending !== null) { W.frames.push(performance.now() - pending); pending = null; } };
  const tick = (t) => { if (!W.probing) return; pending = performance.now(); ch.port2.postMessage(0); requestAnimationFrame(tick); };
  W.start = () => { W.frames = []; W.t0 = performance.now(); W.probing = true; requestAnimationFrame(tick); };
  W.stop = () => { W.probing = false; W.t1 = performance.now(); };
})();
"""


def pct(xs, p):
    if not xs: return 0.0
    xs = sorted(xs); k = min(len(xs) - 1, max(0, round(p / 100 * (len(xs) - 1))))
    return xs[k]


def wheel(pg, steps, dy=420, pause=110):
    for _ in range(steps):
        pg.mouse.wheel(0, dy); pg.wait_for_timeout(pause)


def click_first(pg, selectors, wait=700):
    for s in selectors:
        loc = pg.locator(s)
        for i in range(min(loc.count(), 4)):
            el = loc.nth(i)
            try:
                if el.is_visible():
                    el.click(timeout=3000); pg.wait_for_timeout(wait); return s
            except Exception:
                continue
    return None


def drag_map(pg, sel):
    box = pg.locator(sel).first.bounding_box()
    if not box: return False
    cx, cy = box['x'] + box['width'] / 2, box['y'] + min(box['height'], 700) / 2
    for dx, dy in ((-160, 40), (140, -60), (-90, 120), (120, -80)):
        pg.mouse.move(cx, cy); pg.mouse.down()
        for k in range(1, 13): pg.mouse.move(cx + dx * k / 12, cy + dy * k / 12); pg.wait_for_timeout(16)
        pg.mouse.up(); pg.wait_for_timeout(350)
    pg.mouse.move(cx, cy)
    for _ in range(3): pg.mouse.wheel(0, -240); pg.wait_for_timeout(450)
    for _ in range(3): pg.mouse.wheel(0, 240); pg.wait_for_timeout(450)
    return True


def screens(ids):
    """(key, label, user or None, route, interaction(pg) → description)."""
    def home(pg):
        click_first(pg, ['#home-search'], 200); pg.keyboard.type('Xàbia', delay=90); pg.wait_for_timeout(900)
        pg.keyboard.press('Escape'); wheel(pg, 8); return 'escribir en el buscador y bajar por la portada'

    def explorar(pg):
        ok = drag_map(pg, '#explore-map'); return 'arrastrar el mapa 4 veces y acercar/alejar' + ('' if ok else ' (sin mapa)')

    def puntos(pg):
        wheel(pg, 16, 480); return 'bajar por el listado de puntos'

    def punto(pg):
        wheel(pg, 4); hit = click_first(pg, ['.vm-carousel', '.marine-strip', '.ml-track', '[data-marine]'], 400)
        wheel(pg, 10); return 'bajar por la ficha' + (' y tocar la vida marina' if hit else '')

    def centro(pg):
        wheel(pg, 5); hit = click_first(pg, ['[data-cal-next]', '.cal-next', 'button[aria-label*="siguiente" i]', 'button[aria-label*="Mes siguiente" i]'], 600)
        wheel(pg, 8); return 'bajar por la ficha' + (' y pasar el mes del calendario' if hit else '')

    def reservar(pg):
        hit = click_first(pg, ['.bk-svc button', '.svc-card button', '.svc-card', '[data-service]', '.wr-svc'], 900)
        hit2 = click_first(pg, ['[data-slot]', '.wr-slot', '.slot-btn', '.bk-slot'], 700)
        wheel(pg, 6); return 'elegir servicio' + (' y hora' if hit2 else '') + ' y bajar' if hit else 'bajar (sin servicios que tocar)'

    def area(pg):
        wheel(pg, 10); return 'bajar por Mi área'

    def planning(pg):
        wheel(pg, 4); hit = click_first(pg, ['#pl-month', '[data-pl-nav="next"]', '.pl-next', 'button[aria-label*="siguiente" i]'], 900)
        wheel(pg, 6); return 'bajar por el planning' + (' y cambiar de vista' if hit else '')

    def manifiesto(pg):
        wheel(pg, 10); return 'bajar por el manifiesto'

    def admin(pg):
        n = 0
        for tab in ('points', 'centers', 'bookings'):   # as the side menu does (on the phone it is folded behind «☰ Menú»)
            pg.evaluate(f"location.hash = '#/admin?tab={tab}'"); pg.wait_for_timeout(1300); n += 1
            wheel(pg, 4)
        return f'abrir {n} secciones del menú y bajar'

    return [
        ('inicio', 'Inicio y buscador', None, '#/', home),
        ('explorar', 'Explorar con el mapa', None, '#/explorar', explorar),
        ('puntos', 'Listado de puntos de buceo', None, '#/puntos', puntos),
        ('punto', 'Ficha del punto (vida marina y recorrido virtual)', None, f'#/punto?id={ids["point"]}', punto),
        ('centro', 'Ficha del centro con el calendario', None, f'#/centro?id={ids["center"]}', centro),
        ('reserva', 'Proceso de reserva', 'buzo.prueba', f'#/reservar?center={ids["center"]}', reservar),
        ('area', '«Mi área» del buceador', 'buzo.prueba', '#/area', area),
        ('planning', 'Panel del centro · planning', 'centro.prueba', '#/admin?tab=planning', planning),
        ('manifiesto', 'Panel del centro · manifiesto', 'centro.prueba', f'#/manifiesto?slot={ids["slot"]}', manifiesto),
        ('admin', 'Panel del administrador', 'admin.prueba', '#/admin', admin),
    ]


def measure_once(browser, base, prof, user, route, action):
    ctx = browser.new_context(locale='es-ES', **prof['ctx'])
    ctx.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
    pg = ctx.new_page(); errors = []
    pg.on('pageerror', lambda e: errors.append(str(e)[:160]))
    if user:
        pg.goto(base + '/#/login'); pg.wait_for_selector('#login-form')
        pg.fill('#login', user); pg.fill('#password', PASSWORD); pg.click('#login-form button[type=submit]'); pg.wait_for_timeout(1500)
        if user.startswith('admin'):
            pg.evaluate("""() => fetch('/api/admin/confirm', {method: 'POST', headers: {'Content-Type': 'application/json'},
                           body: JSON.stringify({password: '%s', reason: 'Medición de fluidez (encargo del 17/10, bloque 8)'})}).then(r => r.text())""" % PASSWORD)
        pg.goto(base + '/#/'); pg.wait_for_timeout(500)
    ctx.add_init_script(PROBE)
    cdp = ctx.new_cdp_session(pg); cdp.send('Emulation.setCPUThrottlingRate', {'rate': prof['cpu']})
    pg.goto('about:blank'); pg.goto(base + '/' + route); pg.wait_for_load_state('networkidle'); pg.wait_for_timeout(1500)
    load = pg.evaluate("() => ({lcp: __wdPerf.lcp, cls: __wdPerf.cls, long: __wdPerf.long.slice()})")
    pg.evaluate('__wdPerf.start()'); t0 = time.time()
    what = action(pg)
    pg.wait_for_timeout(600); pg.evaluate('__wdPerf.stop()')
    run = pg.evaluate("() => ({frames: __wdPerf.frames, long: __wdPerf.long.filter(l => l[0] >= __wdPerf.t0), events: __wdPerf.events.filter(e => e[0] >= __wdPerf.t0), t: __wdPerf.t1 - __wdPerf.t0})")
    ctx.close()
    fr = run['frames']; budget = 1000 / prof['hz']
    return {
        'accion': what, 'segundos': round(time.time() - t0, 1), 'errores_js': errors[:3],
        'carga': {'lcp_ms': round(load['lcp']), 'cls': round(load['cls'], 3), 'tareas_largas': len(load['long']),
                  'bloqueo_ms': round(sum(max(0, d - 50) for _, d in load['long']))},
        'interaccion': {
            'fotogramas': len(fr), 'trabajo_p50_ms': round(pct(fr, 50), 1), 'trabajo_p95_ms': round(pct(fr, 95), 1), 'trabajo_max_ms': round(max(fr or [0]), 1),
            'perdidos_120hz_pct': round(100 * sum(1 for f in fr if f > 1000 / 120) / max(1, len(fr)), 1),
            'perdidos_60hz_pct': round(100 * sum(1 for f in fr if f > 1000 / 60) / max(1, len(fr)), 1),
            'perdidos_perfil_pct': round(100 * sum(1 for f in fr if f > budget) / max(1, len(fr)), 1),
            'tareas_largas': len(run['long']), 'tarea_mas_larga_ms': round(max([d for _, d in run['long']] or [0])),
            'inp_ms': round(max([d for _, d, _ in run['events']] or [0])),
        },
    }


def merge(runs):
    """Median of the repetitions, metric by metric (the worst long task of all of them)."""
    out = {'accion': runs[0]['accion'], 'errores_js': sorted({e for r in runs for e in r['errores_js']})[:3], 'repeticiones': len(runs)}
    for part in ('carga', 'interaccion'):
        out[part] = {k: (statistics.median(r[part][k] for r in runs) if k != 'tarea_mas_larga_ms' else max(r[part][k] for r in runs)) for k in runs[0][part]}
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--repeticiones', type=int, default=3)
    ap.add_argument('--solo', default=''); ap.add_argument('--perfiles', default=','.join(PROFILES))
    a = ap.parse_args()
    db = Path(tempfile.mkdtemp(prefix='wod-fluidez-')) / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(db)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=db).start()
    commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    report = {'fecha': time.strftime('%Y-%m-%d %H:%M'), 'commit': commit, 'perfiles': {k: {kk: v[kk] for kk in ('label', 'cpu', 'hz')} for k, v in PROFILES.items()}, 'pantallas': {}}
    try:
        ids = {'point': srv.sql("SELECT id FROM dive_points WHERE name LIKE 'El Moraig%' AND active=1")[0]['id'],
               'center': srv.sql("SELECT c.id FROM centers c JOIN users u ON u.center_id=c.id WHERE u.username='centro.prueba'")[0]['id']}
        ids['slot'] = srv.sql("""SELECT ss.id FROM service_slots ss JOIN bookings b ON b.slot_id=ss.id WHERE ss.provider_id=? AND ss.slot_date>=date('now')
                                 GROUP BY ss.id ORDER BY COUNT(*) DESC, ss.slot_date LIMIT 1""", (f'c:{ids["center"]}',))[0]['id']
        with sync_playwright() as p:
            browser = p.chromium.launch(executable_path=EXE) if Path(EXE).exists() else p.chromium.launch()
            for key, label, user, route, action in screens(ids):
                if a.solo and key not in a.solo.split(','): continue
                report['pantallas'][key] = {'pantalla': label, 'ruta': route, 'cuenta': user or 'visitante', 'perfiles': {}}
                for pk in a.perfiles.split(','):
                    runs = [measure_once(browser, srv.base, PROFILES[pk], user, route, action) for _ in range(a.repeticiones)]
                    m = merge(runs); report['pantallas'][key]['perfiles'][pk] = m
                    i = m['interaccion']; c = m['carga']
                    print(f"{label:52} {PROFILES[pk]['label']:22} LCP {c['lcp_ms']:>5} ms · CLS {c['cls']:.3f} · trabajo p95 {i['trabajo_p95_ms']:>5} ms · "
                          f"perdidos 120 Hz {i['perdidos_120hz_pct']:>5} % · tareas largas {i['tareas_largas']} (máx {i['tarea_mas_larga_ms']} ms) · INP {i['inp_ms']} ms", flush=True)
            browser.close()
    finally:
        srv.stop()
    Path(a.out).parent.mkdir(parents=True, exist_ok=True)
    Path(a.out).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    print('→', a.out)


if __name__ == '__main__':
    main()
