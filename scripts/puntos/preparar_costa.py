#!/usr/bin/env python3
"""v50.58 · Datos de costa para comprobar los puntos de buceo (encargo del 16/10/2026, parte B.6).

Hace app/data/costa/<zona>.json: la tierra de OpenStreetMap (línea de costa de 2017 simplificada con un error de 10 m,
paquete npm `@geo-maps/countries-land-10m` 0.6.0; los datos son © colaboradores de OpenStreetMap, licencia ODbL, y la
página de créditos lo dice) recortada a la caja de cada zona. Con ese archivo, app/wod/costa.py dice si un punto cae en
el mar o en tierra y a cuántos metros está de la orilla, sin conexión y sin paquetes de más.

    python3 scripts/puntos/preparar_costa.py                 # todas las zonas de ZONES
    python3 scripts/puntos/preparar_costa.py es              # solo España
    python3 scripts/puntos/preparar_costa.py es --tgz ruta   # con el paquete ya descargado

El paquete se descarga del registro de npm y se comprueba su huella (sha512) antes de abrirlo; solo se lee su GeoJSON.
"""
from __future__ import annotations

import argparse
import base64
import hashlib
import json
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'app' / 'data' / 'costa'
PACKAGE = '@geo-maps/countries-land-10m'
VERSION = '0.6.0'
TARBALL = f'https://registry.npmjs.org/{PACKAGE}/-/countries-land-10m-{VERSION}.tgz'
INTEGRITY = 'sha512-Ail+Nwvjkc2gKooGR8oPLzwnLuw44PymYicbv2LCiW9+OhAe/QL46Euv7phepKfupby6wTZxeWdx6wNUNjNs3g=='
SCALE = 100000            # coordenadas enteras en cienmilésimas de grado (≈ 1,1 m)

# Zona → (nombre, caja [oeste, sur, este, norte]). Entra la tierra de todos los países que tocan la caja, así dos zonas
# que se solapan dicen lo mismo en la parte común. Los bordes de cada caja caen en mar abierto o tierra adentro, lejos de
# los puntos de buceo: lo que el recorte añade sobre el borde no cuenta como orilla (app/wod/costa.py).
ZONES = {
    'es': ('España (península, Baleares, Canarias, Ceuta y Melilla) y sus vecinos', [-18.5, 27.4, 4.6, 44.0]),
    'mediterraneo': ('Mediterráneo central y oriental (Italia, Malta, Grecia, Croacia, Chipre, Turquía)', [4.6, 30.0, 36.5, 46.5]),
    'mar-rojo': ('Mar Rojo (Egipto, Sudán, Arabia Saudí, Jordania, Israel, Eritrea)', [32.0, 12.0, 44.0, 30.2]),
    'maldivas': ('Maldivas y Sri Lanka', [72.3, -1.0, 82.5, 10.2]),
    'sudeste-asiatico': ('Indonesia, Malasia, Tailandia, Filipinas y Timor', [94.5, -11.5, 141.5, 21.5]),
    'mexico-caribe': ('México, Centroamérica y el Caribe', [-118.5, 7.0, -59.0, 32.8]),
}


def download(dest: Path) -> Path:
    tgz = dest / 'countries-land-10m.tgz'
    with urllib.request.urlopen(TARBALL, timeout=120) as r, open(tgz, 'wb') as f:
        while chunk := r.read(1 << 20):
            f.write(chunk)
    return tgz


def check_integrity(tgz: Path):
    algo, _, want = INTEGRITY.partition('-')
    got = base64.b64encode(hashlib.new(algo, tgz.read_bytes()).digest()).decode()
    if got != want:
        raise SystemExit(f'La huella del paquete no coincide ({algo}): no se usa.')


def features(tgz: Path):
    """Cada país del GeoJSON (una línea por país) sin cargar el archivo entero en memoria."""
    with tarfile.open(tgz, 'r:gz') as tf:
        member = tf.getmember('package/map.geo.json')
        f = tf.extractfile(member)
        for raw in f:
            line = raw.decode('utf-8').strip().rstrip(',')
            if line.startswith('{"type":"Feature"'):
                yield json.loads(line)


def clip(ring, box):
    """Sutherland–Hodgman: la parte del anillo dentro de la caja (los tramos sobre el borde los marca costa.py)."""
    w, s, e, n = box
    def cut(pts, inside, cross):
        out = []
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]
            ia, ib = inside(a), inside(b)
            if ia: out.append(a)
            if ia != ib: out.append(cross(a, b))
        return out
    def at_x(x):
        return lambda a, b: (x, a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]))
    def at_y(y):
        return lambda a, b: (a[0] + (b[0] - a[0]) * (y - a[1]) / (b[1] - a[1]), y)
    pts = [tuple(p) for p in ring[:-1]] if ring and ring[0] == ring[-1] else [tuple(p) for p in ring]
    for inside, cross in ((lambda p: p[0] >= w, at_x(w)), (lambda p: p[0] <= e, at_x(e)),
                          (lambda p: p[1] >= s, at_y(s)), (lambda p: p[1] <= n, at_y(n))):
        if not pts: break
        pts = cut(pts, inside, cross)
    return pts


def encode(pts):
    """Enteros en cienmilésimas de grado, cada punto como diferencia con el anterior (archivo más pequeño)."""
    out, px, py = [], 0, 0
    for x, y in pts:
        ix, iy = round(x * SCALE), round(y * SCALE)
        if out and ix == px and iy == py: continue
        out += [ix - px, iy - py]; px, py = ix, iy
    return out


def nested(rings):
    """Los anillos que caen dentro de otra tierra (lagos tierra adentro, restos del recorte de los datos): no son
    orilla del mar y harían pasar un punto de tierra por agua. Se mira un vértice de cada anillo que no comparta con
    ningún otro (las fronteras entre países comparten vértices)."""
    import math
    cell = 0.02
    rows, owner = {}, {}
    for idx, pts in enumerate(rings):
        for i, a in enumerate(pts):
            b = pts[(i + 1) % len(pts)]
            for r in range(math.floor(min(a[1], b[1]) / cell), math.floor(max(a[1], b[1]) / cell) + 1):
                rows.setdefault(r, []).append((idx, a[0], a[1], b[0], b[1]))
            owner.setdefault((round(a[0] * SCALE), round(a[1] * SCALE)), set()).add(idx)
    out = set()
    for idx, pts in enumerate(rings):
        if len(pts) > 5000: continue                     # un país o una isla grande nunca está dentro de otra tierra
        v = next((p for p in pts if len(owner[(round(p[0] * SCALE), round(p[1] * SCALE))]) == 1), None)
        if v is None: continue
        x, y = v[0], v[1] + 1e-7
        inside = False
        for j, x1, y1, x2, y2 in rows.get(math.floor(y / cell), ()):
            if j == idx or (y1 > y) == (y2 > y): continue
            if x1 + (y - y1) * (x2 - x1) / (y2 - y1) > x: inside = not inside
        if inside: out.add(idx)
    return out


def build(zone: str, tgz: Path):
    name, box = ZONES[zone]
    rings = []
    for ft in features(tgz):
        g = ft['geometry']
        polys = g['coordinates'] if g['type'] == 'MultiPolygon' else [g['coordinates']]
        for poly in polys:
            for ring in poly:
                xs = [p[0] for p in ring]; ys = [p[1] for p in ring]
                if max(xs) < box[0] or min(xs) > box[2] or max(ys) < box[1] or min(ys) > box[3]: continue
                pts = clip(ring, box)
                if len(pts) >= 3: rings.append(pts)
    drop = nested(rings)
    rings = [r for i, r in enumerate(rings) if i not in drop]
    vertices = sum(len(r) for r in rings)
    print(f'{zone}: {len(drop)} anillos dentro de otra tierra (lagos o restos), fuera')
    rings = [encode(r) for r in rings]
    OUT.mkdir(parents=True, exist_ok=True)
    data = {'zone': zone, 'name': name, 'bbox': box, 'scale': SCALE,
            'source': f'OpenStreetMap (ODbL), tierra simplificada con 10 m de error: {PACKAGE} {VERSION}',
            'rings': rings}
    path = OUT / f'{zone}.json'
    path.write_text(json.dumps(data, separators=(',', ':')), encoding='utf-8')
    print(f'{path.relative_to(ROOT)}: {len(rings)} anillos, {vertices} vértices, {path.stat().st_size // 1024} KB')


def main(argv):
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('zones', nargs='*', help='zonas (por defecto todas): ' + ', '.join(ZONES))
    ap.add_argument('--tgz', help='paquete ya descargado')
    a = ap.parse_args(argv)
    for z in a.zones:
        if z not in ZONES: raise SystemExit(f'Zona desconocida: {z}')
    with tempfile.TemporaryDirectory(prefix='wod-costa-') as tmp:
        tgz = Path(a.tgz) if a.tgz else download(Path(tmp))
        check_integrity(tgz)
        for z in a.zones or list(ZONES):
            build(z, tgz)


if __name__ == '__main__':
    main(sys.argv[1:])
