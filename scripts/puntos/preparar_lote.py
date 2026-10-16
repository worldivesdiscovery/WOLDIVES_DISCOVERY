#!/usr/bin/env python3
"""v50.58 · Lotes de puntos de buceo con datos abiertos (encargo del 16/10/2026, partes B.1, B.3, B.4 y B.5).

Convierte lo que dicen Wikidata (licencia CC0) y OpenStreetMap (licencia ODbL: la página de créditos lleva su línea)
sobre los sitios de buceo de una zona en el archivo de un lote, que se sube en Administración → Puntos → Lotes nuevos.
El lote entra «Pendiente de verificar»: no se ve en la web hasta que la administración lo revisa y lo publica.

Qué hace y qué no hace:
- Solo toma lo que la fuente dice: el nombre y la posición (y el país, si la fuente lo da). Lo demás (profundidad,
  corriente, descripción…) se deja vacío: nada se rellena «a ojo».
- Cada punto lleva sus fuentes (enlace a la ficha de Wikidata o de OpenStreetMap, licencia y fecha): es el registro
  privado de fuentes, que solo ve la administración.
- Un mismo sitio que sale en las dos fuentes (a menos de 300 m y con un nombre parecido) va una sola vez, con las dos
  fuentes. Los duplicados con los puntos ya publicados los marca el servidor al subir el lote.
- No consulta ninguna web de buceo ni de la competencia. Hace como mucho una consulta a cada servicio abierto por zona
  (las dos permiten este uso en sus condiciones), con un nombre de programa que lo identifica; nada de descargas
  masivas.

Uso:
    python3 scripts/puntos/preparar_lote.py zonas
    python3 scripts/puntos/preparar_lote.py consultas murcia            # las dos consultas, para lanzarlas a mano
    python3 scripts/puntos/preparar_lote.py descargar murcia --dir datos/  # las lanza (una a cada servicio)
    python3 scripts/puntos/preparar_lote.py convertir murcia --osm datos/murcia-osm.json \\
            --wikidata datos/murcia-wikidata.json [--pais España] --out lote-murcia.json

`--pais` solo cuando todos los puntos de la caja son de ese país (la caja de una zona puede tocar la de un vecino):
si no, el país queda vacío en los puntos que la fuente no lo dice, y se completa al revisar el lote.
"""
from __future__ import annotations

import argparse
import json
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'app'))
from wod import puntos as wpun  # noqa: E402
from wod.geo import haversine_km  # noqa: E402

MAX_ITEMS = 2000          # lo que admite un lote (app/wod/puntos.py, add_batch)
AGENT = 'WorldivesDiscovery-catalogo/50.58 (lotes de puntos de buceo con datos abiertos; revisión manual antes de publicar)'
OVERPASS = 'https://overpass-api.de/api/interpreter'
WIKIDATA = 'https://query.wikidata.org/sparql'

# Orden de trabajo del encargo (B.5): España primero, por zonas; después, los destinos de las experiencias.
# Cajas [oeste, sur, este, norte] en grados: solo dicen dónde buscar; el mar y la tierra los mira el servidor.
ZONES = {
    'comunidad-valenciana': ('Comunidad Valenciana', [-1.6, 37.8, 0.7, 40.8]),
    'murcia': ('Región de Murcia', [-2.0, 37.3, -0.6, 38.0]),
    'andalucia': ('Andalucía', [-7.6, 36.0, -1.6, 37.6]),
    'cataluna': ('Cataluña (Costa Brava y resto de la costa)', [0.1, 40.5, 3.4, 42.9]),
    'baleares': ('Islas Baleares', [1.1, 38.6, 4.4, 40.15]),
    'canarias': ('Islas Canarias', [-18.3, 27.5, -13.3, 29.5]),
    'cantabrico-galicia': ('Costa cantábrica y gallega', [-9.4, 41.8, -1.7, 43.9]),
    'mar-rojo': ('Mar Rojo', [32.0, 12.0, 44.0, 30.2]),
    'maldivas': ('Maldivas', [72.3, -1.0, 74.0, 7.2]),
    'indonesia': ('Indonesia', [94.5, -11.5, 141.5, 6.5]),
    'mexico': ('México (Pacífico, Golfo y Caribe)', [-118.5, 14.0, -86.5, 32.8]),
}


def overpass_query(bbox):
    """Sitios de buceo de OpenStreetMap en la caja (no los centros ni las tiendas de buceo)."""
    w, s, e, n = bbox
    box = f'{s},{w},{n},{e}'
    return (f'[out:json][timeout:120];\n(\n'
            f'  nwr["sport"="scuba_diving"]["name"]["amenity"!="dive_centre"]["shop"!~"."]["club"!~"."]({box});\n'
            f'  nwr["scuba_diving:divespot"="yes"]["name"]({box});\n'
            f');\nout center tags;')


def wikidata_query(bbox):
    """Elementos de Wikidata que son (o son un tipo de) «dive site», con coordenadas dentro de la caja.
    La clase se busca por su nombre en inglés, sin escribir aquí su código."""
    w, s, e, n = bbox
    return ('SELECT ?item ?itemLabel ?coord ?countryLabel WHERE {\n'
            '  ?class rdfs:label "dive site"@en .\n'
            '  ?item wdt:P31/wdt:P279* ?class .\n'
            '  SERVICE wikibase:box {\n'
            '    ?item wdt:P625 ?coord .\n'
            f'    bd:serviceParam wikibase:cornerSouthWest "Point({w} {s})"^^geo:wktLiteral .\n'
            f'    bd:serviceParam wikibase:cornerNorthEast "Point({e} {n})"^^geo:wktLiteral .\n'
            '  }\n'
            '  OPTIONAL { ?item wdt:P17 ?country . }\n'
            '  SERVICE wikibase:label { bd:serviceParam wikibase:language "es,en". }\n'
            '}')


def inside(bbox, lat, lon):
    w, s, e, n = bbox
    return s <= lat <= n and w <= lon <= e


def from_osm(data, bbox, today):
    out = []
    for el in (data or {}).get('elements') or []:
        tags = el.get('tags') or {}
        name = (tags.get('name:es') or tags.get('name') or '').strip()
        lat = el.get('lat', (el.get('center') or {}).get('lat'))
        lon = el.get('lon', (el.get('center') or {}).get('lon'))
        if not name or lat is None or lon is None or el.get('type') not in ('node', 'way', 'relation'): continue
        if not inside(bbox, lat, lon): continue
        item = {'name': name[:180], 'latitude': round(float(lat), 6), 'longitude': round(float(lon), 6)}
        country = (tags.get('addr:country') or tags.get('is_in:country') or '').strip()
        if country and len(country) > 2: item['country'] = country[:100]   # un nombre, no un código de dos letras
        item['sources'] = [{'kind': 'osm', 'ref': f'https://www.openstreetmap.org/{el["type"]}/{el["id"]}', 'license': 'ODbL',
                            'field': '*', 'checked_at': today, 'note': 'Nombre y posición de OpenStreetMap'}]
        out.append(item)
    return out


def from_wikidata(data, bbox, today):
    out = []
    for b in ((data or {}).get('results') or {}).get('bindings') or []:
        uri = (b.get('item') or {}).get('value', '')
        name = (b.get('itemLabel') or {}).get('value', '').strip()
        wkt = (b.get('coord') or {}).get('value', '')
        if not uri.startswith('http://www.wikidata.org/entity/Q') or not wkt.startswith('Point('): continue
        qid = uri.rsplit('/', 1)[1]
        if not name or name == qid: continue          # sin nombre en castellano ni en inglés
        try: lon, lat = (float(x) for x in wkt[6:-1].split())
        except ValueError: continue
        if not inside(bbox, lat, lon): continue
        item = {'name': name[:180], 'latitude': round(lat, 6), 'longitude': round(lon, 6)}
        country = (b.get('countryLabel') or {}).get('value', '').strip()
        if country and not country.startswith('Q'): item['country'] = country[:100]
        item['sources'] = [{'kind': 'wikidata', 'ref': f'https://www.wikidata.org/wiki/{qid}', 'license': 'CC0',
                            'field': '*', 'checked_at': today, 'note': 'Nombre y posición de Wikidata'}]
        out.append(item)
    return out


def join(items):
    """Un mismo sitio en las dos fuentes (o dos veces en una) va una sola vez, con todas sus fuentes (regla de B.4)."""
    kept = []
    for it in items:
        for k in kept:
            d = haversine_km(it['latitude'], it['longitude'], k['latitude'], k['longitude']) * 1000
            if wpun.verdict(d, wpun.similarity(it['name'], k['name'])) == 'same':
                refs = {s['ref'] for s in k['sources']}
                k['sources'] += [s for s in it['sources'] if s['ref'] not in refs]
                if not k.get('country') and it.get('country'): k['country'] = it['country']
                break
        else:
            kept.append(it)
    return kept


def convert(zone, osm=None, wikidata=None, country=None, today=None):
    label, bbox = ZONES[zone]
    today = today or date.today().isoformat()
    items = join(from_wikidata(wikidata, bbox, today) + from_osm(osm, bbox, today))
    for it in items:
        if country and not it.get('country'): it['country'] = country
    items.sort(key=lambda it: (it['latitude'], it['longitude']))
    used = [n for n, d in (('Wikidata (CC0)', wikidata), ('OpenStreetMap (ODbL)', osm)) if d is not None]
    notes = (f'Datos abiertos de {" y ".join(used)}, consultados el {today}. Solo nombre y posición'
             f'{" y país cuando la fuente lo dice" if not country else f"; país «{country}» indicado al preparar el lote"}. '
             'El resto de la ficha queda vacío hasta comprobarlo.')
    files = []
    for i in range(0, max(len(items), 1), MAX_ITEMS):
        part = items[i:i + MAX_ITEMS]
        suffix = f' ({i // MAX_ITEMS + 1})' if len(items) > MAX_ITEMS else ''
        files.append({'zone': zone, 'title': f'{label} · datos abiertos{suffix}', 'notes': notes, 'items': part})
    return files


def fetch(url, data=None):
    req = urllib.request.Request(url, data=data, headers={'User-Agent': AGENT, 'Accept': 'application/json'})
    with urllib.request.urlopen(req, timeout=180) as r:
        return json.loads(r.read().decode('utf-8'))


def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd', required=True)
    sub.add_parser('zonas', help='las zonas y sus cajas')
    q = sub.add_parser('consultas', help='las dos consultas de una zona'); q.add_argument('zona', choices=ZONES)
    d = sub.add_parser('descargar', help='lanza las dos consultas (una a cada servicio)'); d.add_argument('zona', choices=ZONES)
    d.add_argument('--dir', default='.', help='carpeta donde guardar las respuestas')
    c = sub.add_parser('convertir', help='hace el archivo del lote'); c.add_argument('zona', choices=ZONES)
    c.add_argument('--osm'); c.add_argument('--wikidata'); c.add_argument('--pais'); c.add_argument('--out', required=True)
    a = ap.parse_args(argv)

    if a.cmd == 'zonas':
        for k, (label, box) in ZONES.items(): print(f'{k:22} {label}  {box}')
        return 0
    label, bbox = ZONES[a.zona]
    if a.cmd == 'consultas':
        print(f'# {label}\n\n## OpenStreetMap (Overpass, {OVERPASS})\n{overpass_query(bbox)}\n\n## Wikidata ({WIKIDATA})\n{wikidata_query(bbox)}')
        return 0
    if a.cmd == 'descargar':
        out = Path(a.dir); out.mkdir(parents=True, exist_ok=True); bad = 0
        for name, run in (('osm', lambda: fetch(OVERPASS, urllib.parse.urlencode({'data': overpass_query(bbox)}).encode())),
                          ('wikidata', lambda: fetch(WIKIDATA + '?' + urllib.parse.urlencode({'query': wikidata_query(bbox), 'format': 'json'})))):
            dest = out / f'{a.zona}-{name}.json'
            try:
                dest.write_text(json.dumps(run(), ensure_ascii=False), encoding='utf-8'); print(f'{dest}: guardado')
            except Exception as e:   # sin conexión, servicio ocupado o bloqueado: se dice, no se reintenta en bucle
                bad += 1; print(f'{name}: no se pudo consultar ({e}). Lanza la consulta a mano («consultas {a.zona}») y guarda la respuesta en {dest}.')
        return 1 if bad else 0
    if not a.osm and not a.wikidata:
        ap.error('convertir necesita --osm, --wikidata o los dos')
    load = lambda p: json.loads(Path(p).read_text(encoding='utf-8')) if p else None
    files = convert(a.zona, load(a.osm), load(a.wikidata), a.pais)
    out = Path(a.out)
    for i, f in enumerate(files):
        dest = out if len(files) == 1 else out.with_name(f'{out.stem}-{i + 1}{out.suffix}')
        dest.write_text(json.dumps(f, ensure_ascii=False, indent=1), encoding='utf-8')
        sin_pais = sum(1 for it in f['items'] if not it.get('country'))
        dobles = sum(1 for it in f['items'] if len(it['sources']) > 1)
        print(f'{dest}: {len(f["items"])} puntos ({dobles} en las dos fuentes; {sin_pais} sin país, a completar al revisar)')
    return 0


if __name__ == '__main__':
    sys.exit(main())
