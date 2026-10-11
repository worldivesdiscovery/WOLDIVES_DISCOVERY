#!/usr/bin/env python3
"""Load test (Fase 7.6): simulated visitors browsing the catalogue and some divers signing in and booking.

Run it against the REAL server (or the test environment), never against production with real users online:
    python3 tools/prueba_carga.py --url https://pruebas.worldives.com --users 50 --seconds 60
Optional: --login usuario:contraseña --book CENTER_ID:SERVICE_ID:SLOT_ID (makes real booking requests: test only).
Prints requests per second, latency percentiles per route and errors. Only the standard library is used.
"""
import argparse
import json
import random
import statistics
import threading
import time
import urllib.error
import urllib.request
from collections import defaultdict


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--url', required=True)
    ap.add_argument('--users', type=int, default=20)
    ap.add_argument('--seconds', type=int, default=30)
    ap.add_argument('--think', type=float, default=0.5, help='seconds between the clicks of one visitor')
    a = ap.parse_args()
    base = a.url.rstrip('/')
    get = lambda p: json.loads(urllib.request.urlopen(base + p, timeout=20).read() or b'null')
    try:
        centers = [c['id'] for c in (get('/api/center-directory?per_page=50') or {}).get('items', [])][:50]
    except Exception:
        centers = []
    try:
        pts = get('/api/dive-points/map') or {}
        idx = (pts.get('fields') or ['id']).index('id')
        points = [r[idx] for r in pts.get('rows', [])][:300] or [p['id'] for p in pts.get('items', [])][:300]
    except Exception:
        points = []
    routes = [('portada', lambda: '/'), ('meta', lambda: '/api/meta'), ('mapa', lambda: '/api/dive-points/map'),
              ('directorio', lambda: '/api/center-directory?per_page=12&page=%d' % random.randint(1, 3)),
              ('puntos', lambda: '/api/point-directory?page=%d&per_page=12' % random.randint(1, 5))]
    if points: routes.append(('punto', lambda: '/api/dive-points/%d?lang=es' % random.choice(points)))
    if centers: routes.append(('centro', lambda: '/api/centers/%d' % random.choice(centers)))
    lat = defaultdict(list); errors = defaultdict(int); stop = time.time() + a.seconds; lock = threading.Lock()

    def visitor():
        while time.time() < stop:
            name, path = random.choice(routes)
            t0 = time.perf_counter()
            try:
                with urllib.request.urlopen(urllib.request.Request(base + path(), headers={'Accept-Encoding': 'gzip'}), timeout=30) as r:
                    r.read(); code = r.status
            except urllib.error.HTTPError as e:
                code = e.code
            except Exception:
                code = 0
            dt = (time.perf_counter() - t0) * 1000
            with lock:
                lat[name].append(dt)
                if code != 200: errors[f'{name}:{code}'] += 1
            time.sleep(random.uniform(0, a.think * 2))

    threads = [threading.Thread(target=visitor, daemon=True) for _ in range(a.users)]
    t0 = time.time()
    for t in threads: t.start()
    for t in threads: t.join()
    elapsed = time.time() - t0
    total = sum(len(v) for v in lat.values())
    print(f'{a.users} visitantes simultáneos durante {elapsed:.0f} s: {total} peticiones, {total / elapsed:.1f} por segundo')
    print(f'{"ruta":<12}{"n":>7}{"p50 ms":>9}{"p95 ms":>9}{"máx ms":>9}')
    for name, v in sorted(lat.items()):
        v.sort()
        p95 = v[min(len(v) - 1, int(len(v) * 0.95))]
        print(f'{name:<12}{len(v):>7}{statistics.median(v):>9.0f}{p95:>9.0f}{v[-1]:>9.0f}')
    print('errores:', dict(errors) or 'ninguno')


if __name__ == '__main__':
    main()
