#!/usr/bin/env python3
"""v50.54 · Revisión de las coordenadas de todos los puntos de buceo (punto 5 del encargo del 14/10/2026).

Lee la base SOLO PARA CONSULTAR (nunca escribe) y busca lo que daría distancias falsas:

- sin coordenadas, 0,0 o fuera de rango;
- latitud y longitud cambiadas (al cambiarlas el punto queda mucho más cerca de los de su zona);
- puntos lejos de los demás de su zona (subregión) o de su región: posible error de signo o de cifra;
- coordenadas repetidas con nombres distintos;
- coordenadas con 2 decimales o menos (error de hasta 1 km);
- las comprobaciones fijas del encargo: Jávea y Dénia → Cabo San Antonio a menos de 15 km.

    python3 scripts/revisar_coordenadas.py [base.sqlite3] [--informe docs/auditoria/v50.54/coordenadas.md]

Por defecto revisa el catálogo de la demo (data/demo/catalogo-demo.sqlite3); en el servidor:
`sudo -u worldives .venv/bin/python scripts/revisar_coordenadas.py data/worldivesdiscovery.sqlite3`.
Termina con 1 si hay algún error (o falla una comprobación fija) y con 0 si solo hay avisos o nada.
"""
from __future__ import annotations

import sqlite3
import statistics
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from wod.geo import haversine_km  # noqa: E402

# Town centres (public, from the official municipal data) and the dive site each must be close to.
REFERENCES = [
    ('Jávea / Xàbia (centro del pueblo)', 38.7893, 0.1662, 'Cabo San Antonio', 15.0),
    ('Dénia (centro del pueblo)', 38.8408, 0.1057, 'Cabo San Antonio', 15.0),
]
SUBREGION_KM = 60.0     # a dive site this far from the others of its subregion is checked by hand
REGION_KM = 400.0       # … or from the others of its region (Canarias and Baleares are their own regions)


def decimals(v) -> int:
    s = repr(float(v))
    return len(s.split('.')[1].rstrip('0')) if '.' in s else 0


def median_point(rows):
    return statistics.median(r['latitude'] for r in rows), statistics.median(r['longitude'] for r in rows)


def review(db_path: Path):
    db = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True); db.row_factory = sqlite3.Row
    rows = db.execute('SELECT id,name,country,region,subregion,latitude,longitude FROM dive_points WHERE active=1 ORDER BY id').fetchall()
    db.close()
    issues, ok_rows = [], []
    for r in rows:
        lat, lon = r['latitude'], r['longitude']
        if lat is None or lon is None:
            issues.append(('error', r, 'sin coordenadas')); continue
        if not (-90 <= lat <= 90 and -180 <= lon <= 180):
            issues.append(('error', r, f'fuera de rango ({lat}, {lon})')); continue
        if abs(lat) < 0.01 and abs(lon) < 0.01:
            issues.append(('error', r, '0,0 (sin situar)')); continue
        ok_rows.append(r)
        if min(decimals(lat), decimals(lon)) <= 2:
            issues.append(('aviso', r, f'pocos decimales ({lat}, {lon}): error de hasta 1 km'))
    groups = {}
    for r in ok_rows:
        if r['subregion'] and r['subregion'] != r['region']: groups.setdefault(('sub', r['country'], r['subregion']), []).append(r)
        groups.setdefault(('reg', r['country'], r['region']), []).append(r)
    for (kind, _, name), members in groups.items():
        if len(members) < 3: continue
        limit = SUBREGION_KM if kind == 'sub' else REGION_KM
        for r in members:
            others = [x for x in members if x['id'] != r['id']]
            mlat, mlon = median_point(others)
            far = haversine_km(r['latitude'], r['longitude'], mlat, mlon)
            if far <= limit: continue
            swapped = haversine_km(r['longitude'], r['latitude'], mlat, mlon) if abs(r['longitude']) <= 90 else far
            sign = min(haversine_km(-r['latitude'], r['longitude'], mlat, mlon), haversine_km(r['latitude'], -r['longitude'], mlat, mlon))
            hint = (' — con latitud y longitud cambiadas quedaría a %.0f km' % swapped) if swapped < limit else \
                   (' — con el signo cambiado quedaría a %.0f km' % sign) if sign < limit else ''
            where = 'su zona' if kind == 'sub' else 'su región'
            issues.append(('error' if hint else 'aviso', r, f'a {far:.0f} km de los demás puntos de {where} «{name}»{hint}'))
    seen = {}
    for r in ok_rows:
        k = (round(r['latitude'], 4), round(r['longitude'], 4))
        if k in seen and seen[k]['name'].strip().lower() != r['name'].strip().lower():
            issues.append(('aviso', r, f"mismas coordenadas que «{seen[k]['name']}» (#{seen[k]['id']})"))
        seen.setdefault(k, r)
    # one line per point and problem (a point far from both its subregion and its region appears twice: keep both)
    refs = []
    by_name = {r['name'].strip().lower(): r for r in ok_rows}
    for label, lat, lon, target, limit in REFERENCES:
        t = by_name.get(target.lower())
        km = haversine_km(lat, lon, t['latitude'], t['longitude']) if t else None
        refs.append((label, target, km, limit, km is not None and km < limit))
    return rows, issues, refs


def report(db_path, rows, issues, refs):
    errors = [i for i in issues if i[0] == 'error']; warns = [i for i in issues if i[0] == 'aviso']
    out = [f'# Revisión de coordenadas de los puntos de buceo', '',
           f'Base revisada: `{db_path.name}` · {len(rows)} puntos activos · {len(errors)} errores · {len(warns)} avisos.', '',
           'Fórmula de distancia: Haversine (radio medio de la Tierra 6371,0088 km), la misma que usa el servidor.', '',
           '## Comprobaciones fijas del encargo', '', '| Desde | Hasta | Distancia | Límite | Resultado |', '|---|---|---|---|---|']
    for label, target, km, limit, ok in refs:
        out.append(f"| {label} | {target} | {'—' if km is None else f'{km:.1f} km'.replace('.', ',')} | < {limit:.0f} km | {'Correcto' if ok else 'FALLA'} |")
    place = [i for i in issues if not i[2].startswith('pocos decimales')]
    coarse = [i for i in issues if i[2].startswith('pocos decimales')]
    out += ['', '## Puntos a revisar', '']
    if not place:
        out.append('Ninguno: todas las coordenadas están dentro de su zona y de su región, y no hay repetidas.')
    else:
        out += ['| Nivel | # | Punto | Zona | Coordenadas | Qué pasa |', '|---|---|---|---|---|---|']
        for level, r, why in sorted(place, key=lambda i: (i[0] != 'error', i[1]['id'])):
            out.append(f"| {level} | {r['id']} | {r['name']} | {r['subregion'] or r['region'] or ''} ({r['country']}) | {r['latitude']}, {r['longitude']} | {why} |")
    out += ['', f'## Coordenadas con 2 decimales o menos ({len(coarse)} de {len(rows)})', '',
            'Error de hasta 1 km. La web no da decimales falsos: en estos puntos la distancia se muestra en kilómetros enteros. '
            'Conviene afinarlas (6 decimales) desde Administración → Puntos de buceo, empezando por los que tienen centros.', '']
    if coarse:
        out.append(' · '.join(f"#{r['id']} {r['name']} ({r['latitude']}, {r['longitude']})" for _, r, _ in sorted(coarse, key=lambda i: i[1]['id'])))
    out += ['', '«Error»: casi seguro mal (sin situar, fuera de rango, cifras cambiadas). «Aviso»: lejos de los suyos o con pocos '
            'decimales; puede ser correcto (un punto aislado), hay que mirarlo en el mapa. Nada se cambia solo: cada punto se '
            'corrige a mano desde Administración → Puntos de buceo.', '']
    return '\n'.join(out)


def main(argv):
    args = list(argv)
    out_path = None
    if '--informe' in args:
        i = args.index('--informe'); out_path = Path(args[i + 1]); del args[i:i + 2]
    db_path = Path(args[0]) if args else ROOT / 'data' / 'demo' / 'catalogo-demo.sqlite3'
    if not db_path.exists():
        print(f'No existe la base {db_path}.'); return 1
    rows, issues, refs = review(db_path)
    text = report(db_path, rows, issues, refs)
    if out_path:
        out_path.parent.mkdir(parents=True, exist_ok=True); out_path.write_text(text, encoding='utf-8'); print(f'Informe: {out_path}')
    print(text)
    return 1 if any(i[0] == 'error' for i in issues) or not all(r[4] for r in refs) else 0


if __name__ == '__main__':
    raise SystemExit(main(sys.argv[1:]))
