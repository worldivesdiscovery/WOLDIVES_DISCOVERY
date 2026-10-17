"""v50.47 · parte G.13: los recuentos públicos son los mismos que en la versión anterior.

Arranca dos servidores sobre copias de la MISMA base de catálogo de demostración (nunca datos reales): uno con el
código actual y otro con el código de la versión anterior (una carpeta con ese código, por ejemplo un `git worktree`).
Pide como visitante anónimo lo público (mapa, Explorar, centros, puntos, viajes, tipos, top 10, fichas, servicios,
salidas y opiniones) y compara cuántos elementos devuelve cada uno. El aislamiento entre centros solo afecta a los
datos privados del panel: si algo público cambia, es un fallo.

    git worktree add --detach /tmp/wod-v5046 f08bff2
    python scripts/seguridad/recuentos_publicos.py /tmp/wod-v5046 [--md docs/pruebas/recuentos-publicos-v50.47.md]
"""
from __future__ import annotations

import json
import os
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SEED = ROOT / 'data' / 'demo' / 'catalogo-demo.sqlite3'
PUBLIC = ['/api/dive-points/map', '/api/point-directory', '/api/center-directory', '/api/travel-directory', '/api/dive-types', '/api/top-dives?lat=38.8&lon=0.18',
          '/api/centers', '/api/dive-points', '/api/site-promos', '/api/meta']


def free_port():
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


def start(code: Path, seed: Path):
    tmp = Path(tempfile.mkdtemp(prefix='wod-recuentos-'))
    shutil.copy(seed, tmp / 'db.sqlite3')
    port = free_port()
    env = dict(os.environ, WOD_DB_PATH=str(tmp / 'db.sqlite3'), WOD_DATA_DIR=str(tmp), WOD_STORAGE_DIR=str(tmp / 'st'), WOD_LOG_DIR=str(tmp / 'logs'),
               WOD_UPLOADS_DIR=str(tmp / 'up'), WOD_PORT=str(port), WOD_HOST='127.0.0.1', WOD_ENV='development', WOD_PUBLIC_URL=f'http://127.0.0.1:{port}',
               WOD_SECRET_KEY='r' * 40, WOD_MAIL_FILE_DIR=str(tmp / 'mail'), WOD_NO_ENV_FILE='1', WOD_DATA_KEY='recuentos-publicos-clave-de-prueba-0123')
    for k in ('STRIPE_SECRET_KEY', 'WOD_DEMO_MODE', 'ARCGIS_API_KEY', 'WOD_SMTP_HOST'): env.pop(k, None)
    proc = subprocess.Popen([sys.executable, str(code / 'app' / 'server.py')], env=env, cwd=str(tmp), stdout=subprocess.DEVNULL, stderr=open(tmp / 'err.log', 'w'))
    base = f'http://127.0.0.1:{port}'
    for _ in range(300):
        try: urllib.request.urlopen(base + '/api/health', timeout=1); return proc, base, tmp
        except Exception:
            if proc.poll() is not None: raise SystemExit((tmp / 'err.log').read_text())
            time.sleep(0.1)
    raise SystemExit('no arranca')


def get(base, path):
    try:
        with urllib.request.urlopen(base + path, timeout=30) as r: return r.status, json.loads(r.read() or b'{}')
    except urllib.error.HTTPError as e: return e.code, {}


def counts(obj, prefix=''):
    """Length of every list (and every numeric «total») in the answer, by its path."""
    out = {}
    if isinstance(obj, list):
        out[prefix or '[]'] = len(obj)
    elif isinstance(obj, dict):
        for k, v in obj.items():
            if isinstance(v, (list, dict)): out.update(counts(v, f'{prefix}.{k}' if prefix else k))
            elif k in ('total', 'count', 'n') and isinstance(v, int): out[f'{prefix}.{k}' if prefix else k] = v
    return out


def snapshot(base):
    snap = {}
    for p in PUBLIC:
        st, js = get(base, p); snap[p] = {'status': st, **counts(js)}
    # Records of every centre with services: its page, its services and departures, its reviews.
    st, js = get(base, '/api/center-directory')
    items = js.get('items') or js.get('centers') or (js if isinstance(js, list) else [])
    ids = [x.get('id') for x in items if isinstance(x, dict)][:40]
    for cid in ids:
        st, c = get(base, f'/api/centers/{cid}'); snap[f'/api/centers/{cid}'] = {'status': st, **counts(c)}
        st, s = get(base, f'/api/provider-services?center_id={cid}')
        snap[f'/api/provider-services?center_id={cid}'] = {'status': st, **counts(s), 'slots': sum(len(x.get('slots') or []) for x in (s.get('items') or []))}
        for x in (s.get('items') or [])[:6]:
            st, ag = get(base, f"/api/agenda/public?service={x.get('id')}"); snap[f"/api/agenda/public?service={x.get('id')}"] = {'status': st, **counts(ag)}
    st, js = get(base, '/api/point-directory')
    pts = [x.get('id') for x in (js.get('items') or js.get('points') or []) if isinstance(x, dict)][:40]
    for pid in pts:
        st, d = get(base, f'/api/dive-points/{pid}'); snap[f'/api/dive-points/{pid}'] = {'status': st, **counts(d)}
    return snap


def main():
    if len(sys.argv) < 2: raise SystemExit(__doc__)
    old_code = Path(sys.argv[1]).resolve()
    md = Path(sys.argv[sys.argv.index('--md') + 1]) if '--md' in sys.argv else None
    seed = Path(sys.argv[sys.argv.index('--base') + 1]) if '--base' in sys.argv else SEED
    a = start(old_code, seed); b = start(ROOT, seed)
    try:
        old, new = snapshot(a[1]), snapshot(b[1])
    finally:
        for proc, _base, tmp in (a, b):
            proc.terminate(); proc.wait(10); shutil.rmtree(tmp, ignore_errors=True)
    rows, diff = [], 0
    for path in sorted(set(old) | set(new)):
        for k in sorted(set(old.get(path, {})) | set(new.get(path, {}))):
            o, n = old.get(path, {}).get(k), new.get(path, {}).get(k)
            same = o == n; diff += not same
            rows.append((path, k, o, n, same))
    lines = ['# Recuentos públicos: v50.47 frente a la versión anterior', '',
             f'Misma base para las dos versiones (`{seed.name}`, copia; nunca datos reales), visitante anónimo. Se comparan {len(old)} respuestas públicas '
             '(listados, fichas de centros y puntos, servicios y salidas de cada centro).', '',
             '| Ruta | Dato | Anterior | v50.47 | Igual |', '|---|---|---|---|---|']
    lines += [f'| `{p}` | {k} | {o} | {n} | {"sí" if s else "**NO**"} |' for p, k, o, n, s in rows]
    lines += ['', f'**{"Todo igual" if not diff else f"{diff} diferencias"}** en {len(old)} respuestas públicas.']
    print('\n'.join(lines))
    if md: md.parent.mkdir(parents=True, exist_ok=True); md.write_text('\n'.join(lines) + '\n', encoding='utf-8')
    return 0 if not diff else 1


if __name__ == '__main__':
    sys.exit(main())
