"""Encargo del 17/10/2026 (Bloque 2) · Importador de la vida marina citada en fuentes públicas.

El archivo (JSON o CSV, el mismo formato para los próximos puntos) trae, por punto, cada especie citada con su
evidencia («en el punto» o «en la zona»), la frecuencia y la temporada solo si la fuente las dice, dónde se ve, si ya
estaba en el catálogo de 150, si sale al público y sus fuentes. Aquí no se toca la base de datos: se lee el archivo, se
normaliza cada cita y se decide su grupo del catálogo y su punto. Las fuentes son internas (solo el administrador).

Nada se rellena a ojo: el grupo sale del grupo del archivo y, en los grupos que mezclan varios del catálogo, de la
taxonomía del nombre científico (ascidias → tunicado, tortugas → reptil, géneros de nudibranquios → nudibranquio).
"""
from __future__ import annotations

import csv
import io
import json
import re
import unicodedata

# The groups of the catalogue (brief 2.2.4), with the icon of the web's own line icons for a species without a photo
GROUPS = {
    'pez': ('Peces', 'fish'), 'cefalopodo': ('Cefalópodos', 'octopus'), 'crustaceo': ('Crustáceos', 'crab'),
    'nudibranquio': ('Nudibranquios', 'nudibranch'), 'molusco': ('Moluscos', 'shell'), 'equinodermo': ('Equinodermos', 'starfish'),
    'cnidario': ('Cnidarios', 'coral'), 'esponja': ('Esponjas', 'sponge'), 'gusano': ('Gusanos', 'worm'), 'tunicado': ('Tunicados', 'tunicate'),
    'alga': ('Algas y plantas', 'seaweed'), 'reptil': ('Reptiles', 'turtle'), 'mamifero': ('Mamíferos', 'dolphin'),
}
FILE_GROUPS = {   # the groups of the file → the catalogue's (the mixed ones are split by taxonomy below)
    'peces': 'pez', 'cefalopodos': 'cefalopodo', 'crustaceos': 'crustaceo', 'equinodermos': 'equinodermo', 'esponjas': 'esponja',
    'algas y plantas marinas': 'alga', 'cnidarios (corales, gorgonias, anemonas, medusas)': 'cnidario',
    'nudibranquios y moluscos': 'molusco', 'reptiles y mamiferos': 'mamifero', 'gusanos y briozoos': 'gusano',
}
# taxonomy (facts, not a guess from the common name): nudibranch genera, tunicates and sea turtles
NUDIBRANCH_GENERA = {'peltodoris', 'rostanga', 'chromodoris', 'felimare', 'felimida', 'spurilla', 'hypselodoris', 'flabellina', 'edmundsella',
                     'cratena', 'discodoris', 'dendrodoris', 'doriopsilla', 'platydoris', 'facelina', 'caloria', 'janolus', 'tritonia', 'polycera',
                     'limacia', 'trapania', 'okenia', 'diaphorodoris', 'aeolidiella', 'berghia', 'godiva', 'coryphella', 'doris', 'nudibranchia'}
TUNICATE_GENERA = {'phallusia', 'botryllus', 'halocynthia', 'clavelina', 'ciona', 'ascidia', 'didemnum', 'microcosmus', 'pseudodistoma', 'ascidiacea'}
TURTLE_GENERA = {'caretta', 'chelonia', 'dermochelys', 'eretmochelys', 'lepidochelys', 'testudines'}

FREQ = {'habitual': 'habitual', 'frecuente': 'frecuente', 'ocasional': 'ocasional', 'raro': 'raro', 'rara': 'raro'}
LEGACY_FREQ = {'habitual': 'common', 'frecuente': 'common', 'ocasional': 'occasional', 'raro': 'rare'}
CATALOG = {'sí': 'si', 'si': 'si', 'no': 'no', 'genérico': 'generico', 'generico': 'generico'}
MAX_ROWS = 20000


def norm(s) -> str:
    s = unicodedata.normalize('NFKD', str(s or '')).encode('ascii', 'ignore').decode().lower()
    return re.sub(r'\s+', ' ', re.sub(r'[^a-z0-9]+', ' ', s)).strip()


def base_name(s) -> str:
    """The name of a site without what follows «(» or «,» («Islas Cíes, Galicia» → «islas cies»)."""
    return norm(re.split(r'[(,]', str(s or ''), maxsplit=1)[0])


def group_of(file_group, scientific) -> str:
    g = {norm(k): v for k, v in FILE_GROUPS.items()}.get(norm(file_group))
    if g is None:   # a group written in another way: by its first word
        first = norm(file_group).split(' ')[0] if file_group else ''
        g = next((v for k, v in FILE_GROUPS.items() if norm(k).split(' ')[0] == first), 'pez')
    genus = norm(scientific).split(' ')[0] if scientific else ''
    if g == 'molusco' and genus in NUDIBRANCH_GENERA: return 'nudibranquio'
    if g == 'gusano' and genus in TUNICATE_GENERA: return 'tunicado'
    if g == 'mamifero' and genus in TURTLE_GENERA: return 'reptil'
    return g


def _clean(v, n=300):
    v = re.sub(r'[\x00-\x1f\x7f]', ' ', str(v or '')).strip()
    v = re.sub(r'\s+', ' ', v)[:n]
    return '' if norm(v) in ('', 'sin dato', 'sin datos') else v


def _sources(v):
    items = v if isinstance(v, list) else re.split(r'\s*\|\s*', str(v or ''))
    return [u.strip()[:500] for u in items if re.match(r'https?://', str(u).strip())][:12]


def _bool(v):
    return v is True or norm(v) in ('si', 'true', '1', 'yes')


def citation(point, municipio, s) -> dict:
    sci = _clean(s.get('cientifico') or s.get('nombre_cientifico'), 120)
    common = _clean(s.get('comun') or s.get('nombre_comun'), 120)
    if not sci and not common: raise ValueError('Una cita no tiene nombre.')
    ev = norm(s.get('evidencia'))
    cat = CATALOG.get(str(s.get('en_catalogo') or s.get('en_catalogo_150') or '').strip().lower(), 'no')
    return {'point': _clean(point, 200), 'municipio': _clean(municipio, 120), 'common': common or sci, 'scientific': sci or common,
            'group': group_of(s.get('grupo'), sci), 'group_label': _clean(s.get('grupo'), 80),
            'evidence': 'point' if ev.startswith('en el punto') else 'zone',
            'frequency': FREQ.get(norm(s.get('frecuencia')), None), 'season': _clean(s.get('temporada'), 120), 'where': _clean(s.get('donde'), 300),
            'catalog': cat, 'visible': _bool(s.get('visible')) and cat != 'generico', 'hidden_reason': _clean(s.get('motivo_oculta'), 120),
            'sources': _sources(s.get('fuentes'))}


def parse(raw: bytes | str, filename='') -> list[dict]:
    """The citations of a JSON ({puntos: [{punto, municipio, especies: [...]}]}) or CSV (one citation per row, «;»)."""
    text = raw.decode('utf-8-sig', 'replace') if isinstance(raw, (bytes, bytearray)) else str(raw).lstrip('﻿')
    text = text.strip()
    out = []
    if text[:1] in '{[':
        try: data = json.loads(text)
        except ValueError: raise ValueError('El archivo JSON no se puede leer.') from None
        puntos = data.get('puntos') if isinstance(data, dict) else data
        if not isinstance(puntos, list): raise ValueError('El JSON no tiene la lista «puntos».')
        for p in puntos:
            if not isinstance(p, dict) or not isinstance(p.get('especies'), list): raise ValueError('Cada punto del JSON necesita su lista «especies».')
            for s in p['especies']:
                if isinstance(s, dict): out.append(citation(p.get('punto'), p.get('municipio'), s))
    else:
        rows = list(csv.DictReader(io.StringIO(text), delimiter=';' if text.split('\n', 1)[0].count(';') >= text.split('\n', 1)[0].count(',') else ','))
        need = {'punto', 'municipio', 'nombre_cientifico', 'evidencia'}
        if not rows or not need <= set(rows[0].keys()): raise ValueError('El CSV necesita las columnas punto, municipio, nombre_cientifico y evidencia.')
        for r in rows: out.append(citation(r.get('punto'), r.get('municipio'), r))
    if not out: raise ValueError('El archivo no trae ninguna cita.')
    if len(out) > MAX_ROWS: raise ValueError(f'El archivo trae demasiadas citas (máximo {MAX_ROWS}).')
    return out


def match_point(points, name, municipio):
    """The id of the site of a citation by its name and municipality, or None («Sin punto», to link by hand).
    points: [(id, name, region, subregion)] of the active sites."""
    b = base_name(name)
    if not b: return None
    cands = [p for p in points if base_name(p[1]) == b]
    if not cands:
        cands = [p for p in points if len(b) >= 6 and (b in base_name(p[1]) or (len(base_name(p[1])) >= 6 and base_name(p[1]) in b))]
    if len(cands) <= 1: return cands[0][0] if cands else None
    towns = [t for t in re.split(r'[/,()]', norm(municipio).replace(' y ', '/')) if len(t.strip()) >= 3]
    near = [p for p in cands if any(t.strip() in norm(f'{p[2]} {p[3]}') for t in towns)]
    return near[0][0] if len(near) == 1 else None
