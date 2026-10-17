#!/usr/bin/env python3
"""Encargo del 17/10 · Bloque 8 · Lighthouse en el móvil de las pantallas públicas principales.

Sobre una copia nueva de la demo servida en modo producción (sin la franja de demostración), con Lighthouse 12.8.2 y
su perfil móvil de serie (Moto G Power, 4G lento simulado y procesador 4 veces más lento). Cada página se pasa varias
veces y se da la mediana.

    python3 scripts/rendimiento/lighthouse_publicas.py <salida.json> [--pasadas 3] [--solo inicio,puntos]
"""
from __future__ import annotations

import argparse
import json
import os
import statistics
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path[:0] = [str(ROOT / 'tests'), str(ROOT / 'app'), str(ROOT / 'scripts')]
from helpers import Server  # noqa: E402
from wod.cifrado import DEMO_DATA_KEY  # noqa: E402

CHROME = '/opt/pw-browsers/chromium-1194/chrome-linux/chrome'


def run_lh(url, out_json):
    cmd = ['npx', '-y', 'lighthouse@12.8.2', url, '--quiet', '--output=json', f'--output-path={out_json}',
           '--only-categories=performance,accessibility,best-practices,seo',
           '--chrome-flags=--headless=new --no-sandbox --disable-gpu']
    for attempt in range(3):   # Chromium sin pantalla falla a veces al arrancar: hasta 3 intentos, y el error si no
        p = subprocess.run(cmd, capture_output=True, text=True, timeout=300, env=dict(os.environ, CHROME_PATH=CHROME))
        if p.returncode == 0 and Path(out_json).exists(): break
        err = (p.stderr or p.stdout or '').strip().splitlines()
    else:
        raise RuntimeError(f'Lighthouse no ha podido medir {url}: ' + ' | '.join(l for l in err if 'at ' not in l)[-400:])
    r = json.loads(Path(out_json).read_text())
    a = r['audits']; c = r['categories']
    return {'rendimiento': round(c['performance']['score'] * 100), 'lcp_s': round(a['largest-contentful-paint']['numericValue'] / 1000, 2),
            'fcp_s': round(a['first-contentful-paint']['numericValue'] / 1000, 2), 'tbt_ms': round(a['total-blocking-time']['numericValue']),
            'cls': round(a['cumulative-layout-shift']['numericValue'], 3), 'si_s': round(a['speed-index']['numericValue'] / 1000, 2),
            'accesibilidad': round(c['accessibility']['score'] * 100), 'buenas_practicas': round(c['best-practices']['score'] * 100),
            'seo': round(c['seo']['score'] * 100), 'peso_kb': round(a['total-byte-weight']['numericValue'] / 1024)}


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('out'); ap.add_argument('--pasadas', type=int, default=3); ap.add_argument('--solo', default='')
    a = ap.parse_args()
    db = Path(tempfile.mkdtemp(prefix='wod-lh-')) / 'demo.sqlite3'
    r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(db)], capture_output=True, text=True)
    assert r.returncode == 0, r.stdout + r.stderr
    srv = Server({'WOD_DATA_KEY': DEMO_DATA_KEY, 'STRIPE_SECRET_KEY': ''}, seed=db).start()
    commit = subprocess.run(['git', 'rev-parse', '--short', 'HEAD'], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    report = {'fecha': time.strftime('%Y-%m-%d %H:%M'), 'commit': commit, 'lighthouse': '12.8.2 · móvil (perfil de serie)', 'paginas': {}}
    try:
        point = srv.sql("SELECT id FROM dive_points WHERE name LIKE 'El Moraig%' AND active=1")[0]['id']
        center = srv.sql("SELECT c.id FROM centers c JOIN users u ON u.center_id=c.id WHERE u.username='centro.prueba'")[0]['id']
        pages = [('inicio', 'Inicio', '/'), ('puntos', 'Puntos de buceo', '/#/puntos'), ('punto', 'Ficha de un punto', f'/#/punto?id={point}'),
                 ('centro', 'Ficha de un centro', f'/#/centro?id={center}'), ('centros', 'Centros', '/#/centros'), ('experiencias', 'Experiencias', '/#/experiencias'),
                 ('tipos', 'Tipos de buceo', '/#/tipos'), ('top10', 'Top 10', '/#/top10')]
        tmp = Path(tempfile.mkdtemp(prefix='wod-lhr-'))
        for key, label, path in pages:
            if a.solo and key not in a.solo.split(','): continue
            runs = [run_lh(srv.base + path, tmp / f'{key}-{i}.json') for i in range(a.pasadas)]
            med = {k: statistics.median(x[k] for x in runs) for k in runs[0]}
            report['paginas'][key] = {'pagina': label, 'ruta': path, 'mediana': med, 'pasadas': runs}
            print(f"{label:22} rendimiento {med['rendimiento']:>4} ({' · '.join(str(x['rendimiento']) for x in runs)}) · LCP {med['lcp_s']} s · TBT {med['tbt_ms']} ms · CLS {med['cls']}", flush=True)
    finally:
        srv.stop()
    Path(a.out).write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    print('→', a.out)


if __name__ == '__main__':
    main()
