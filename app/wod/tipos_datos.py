"""Encargo del 17/10/2026 (1.2) · Los datos propios de cada tipo de inmersión.

Un pecio tiene el nombre del barco y su eslora; una cueva, la longitud del recorrido; una pared, dónde empieza y dónde
termina… Cada tipo de buceo tiene su lista de campos, que la administración configura en «Administración → Tipos de
buceo» (añadir un campo nuevo no exige programar). Cada punto guarda solo los valores que se conocen: lo vacío no se
guarda ni se enseña. Los rellenan la administración (directamente) y los centros (como propuesta que la administración
acepta), y cada valor apunta de dónde sale en el registro privado de fuentes del punto.
"""
from __future__ import annotations

import re

SCHEMA = [
    '''CREATE TABLE IF NOT EXISTS dive_type_fields (id INTEGER PRIMARY KEY AUTOINCREMENT, type_key TEXT NOT NULL,
         field_key TEXT NOT NULL, label TEXT NOT NULL, kind TEXT NOT NULL CHECK(kind IN ('number','text','yesno')), unit TEXT,
         sort_order INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT,
         UNIQUE(type_key, field_key))''',
    '''CREATE TABLE IF NOT EXISTS dive_point_type_values (point_id INTEGER NOT NULL REFERENCES dive_points(id) ON DELETE CASCADE,
         field_id INTEGER NOT NULL REFERENCES dive_type_fields(id) ON DELETE CASCADE, value TEXT NOT NULL, updated_by INTEGER,
         updated_at TEXT NOT NULL, PRIMARY KEY(point_id, field_id))''',
]

KINDS = ('number', 'text', 'yesno')

# The fields of the brief (1.2), by type. The administration can add more, rename them or hide them.
DEFAULT_FIELDS = {
    'pecios-y-naufragios': [('barco', 'Nombre del barco', 'text', None), ('hundimiento', 'Año del hundimiento', 'number', None),
                            ('eslora', 'Eslora', 'number', 'm'), ('cubierta', 'Profundidad de la cubierta', 'number', 'm'),
                            ('penetrable', 'Se puede penetrar', 'yesno', None)],
    'cuevas-y-cavernas': [('recorrido', 'Longitud del recorrido', 'number', 'm'), ('sin_luz', 'Zona sin luz natural', 'yesno', None),
                          ('exige', 'Exige linterna o especialidad', 'text', None)],
    'paredes': [('pared_desde', 'La pared empieza a', 'number', 'm'), ('pared_hasta', 'La pared termina a', 'number', 'm')],
    'corrientes-y-deriva': [('direccion', 'Dirección habitual de la corriente', 'text', None), ('entrada', 'Punto de entrada', 'text', None),
                            ('salida', 'Punto de salida', 'text', None)],
    'arrecifes': [('cima', 'Profundidad de la cima', 'number', 'm')],
    'pinaculos': [('cima', 'Profundidad de la cima', 'number', 'm')],
    'nocturnas': [('de_noche', 'Se permite de noche', 'yesno', None), ('condiciones', 'Condiciones para bucear de noche', 'text', None)],
    'aguas-profundas': [('prof_recomendada', 'Profundidad máxima recomendada', 'number', 'm'), ('especialidad', 'Especialidad necesaria', 'text', None)],
}

NUMBER = re.compile(r'^\s*(\d{1,4}(?:[.,]\d{1,2})?)\s*(?:[-–]\s*(\d{1,4}(?:[.,]\d{1,2})?))?\s*$')


def seed(db, now):
    """Creates the fields of the brief that do not exist yet (never touches the ones the administration changed)."""
    n = 0
    for tkey, fields in DEFAULT_FIELDS.items():
        for i, (fkey, label, kind, unit) in enumerate(fields):
            n += db.execute('INSERT OR IGNORE INTO dive_type_fields(type_key,field_key,label,kind,unit,sort_order,created_at) VALUES(?,?,?,?,?,?,?)',
                            (tkey, fkey, label, kind, unit, i * 10, now)).rowcount
    return n


def clean_value(kind, raw):
    """The value as it is kept, or None when it is empty. A number may be a range («31-33»). ValueError if it is wrong."""
    if raw is None: return None
    s = re.sub(r'\s+', ' ', str(raw)).strip()
    if not s: return None
    if kind == 'yesno':
        v = s.lower()
        if v in ('si', 'sí', 'yes', 'true', '1'): return 'si'
        if v in ('no', 'false', '0'): return 'no'
        raise ValueError('Elige «Sí» o «No».')
    if kind == 'number':
        m = NUMBER.match(s)
        if not m: raise ValueError(f'«{s[:20]}» no es un número (puede ser un intervalo, por ejemplo 31-33).')
        a = m.group(1).replace(',', '.'); b = (m.group(2) or '').replace(',', '.')
        if b and float(b) < float(a): a, b = b, a
        return f'{a}-{b}' if b and b != a else a
    if re.search(r'[<>]', s): raise ValueError('Ese texto tiene caracteres no permitidos.')
    return s[:160]


def clean_field_def(data):
    """A field as the administration writes it: (label, kind, unit). ValueError if something is missing."""
    label = re.sub(r'\s+', ' ', str(data.get('label') or '')).strip()[:80]
    if not label or re.search(r'[<>]', label): raise ValueError('Escribe el nombre del dato.')
    kind = str(data.get('kind') or 'text')
    if kind not in KINDS: raise ValueError('Tipo de dato no válido.')
    unit = re.sub(r'\s+', ' ', str(data.get('unit') or '')).strip()[:12] or None
    if unit and re.search(r'[<>]', unit): raise ValueError('Unidad no válida.')
    return label, kind, (unit if kind == 'number' else None)


def field_key(label, taken):
    base = re.sub(r'[^a-z0-9]+', '_', label.lower().translate(str.maketrans('áéíóúüñ', 'aeiouun'))).strip('_')[:40] or 'dato'
    k, i = base, 2
    while k in taken: k, i = f'{base}_{i}', i + 1
    return k


def fields_for(db, type_keys, include_hidden=False):
    """The fields of the types of a dive site, in order, without repeating a field (a reef that is also a pinnacle has one
    «Profundidad de la cima»)."""
    keys = [k for k in type_keys if k]
    if not keys: return []
    rows = db.execute(f"SELECT * FROM dive_type_fields WHERE type_key IN ({','.join('?' * len(keys))}) {'' if include_hidden else 'AND active=1'} ORDER BY sort_order, id",
                      keys).fetchall()
    order = {k: i for i, k in enumerate(keys)}
    seen, out = set(), []
    for r in sorted(rows, key=lambda r: (order.get(r['type_key'], 99), r['sort_order'], r['id'])):
        sig = (r['field_key'], r['label'])
        if sig in seen: continue
        seen.add(sig); out.append(dict(r))
    return out


def values_of(db, point_id):
    return {r['field_id']: r['value'] for r in db.execute('SELECT field_id,value FROM dive_point_type_values WHERE point_id=?', (point_id,)).fetchall()}


def public_data(db, point_id, type_keys):
    """What the public page of the site shows: only the fields with a value, of the types of the site."""
    vals = values_of(db, point_id)
    if not vals: return []
    out = []
    for f in fields_for(db, type_keys):
        v = vals.get(f['id'])
        if v is None: continue
        out.append({'id': f['id'], 'label': f['label'], 'kind': f['kind'], 'unit': f['unit'], 'value': v, 'type': f['type_key']})
    return out


def save_values(db, point_id, type_keys, data, user_id, now):
    """{field_id: value} from the administration: empty removes the value. Only fields of the types of the site.
    Returns the field ids that changed."""
    allowed = {f['id']: f for f in fields_for(db, type_keys, include_hidden=True)}
    old = values_of(db, point_id); changed = []
    for raw_id, raw in (data or {}).items():
        try: fid = int(raw_id)
        except (TypeError, ValueError): continue
        f = allowed.get(fid)
        if not f: raise ValueError('Ese dato no es de los tipos de este punto.')
        v = clean_value(f['kind'], raw)
        if v == old.get(fid): continue
        if v is None: db.execute('DELETE FROM dive_point_type_values WHERE point_id=? AND field_id=?', (point_id, fid))
        else:
            db.execute('INSERT INTO dive_point_type_values(point_id,field_id,value,updated_by,updated_at) VALUES(?,?,?,?,?) '
                       'ON CONFLICT(point_id,field_id) DO UPDATE SET value=excluded.value, updated_by=excluded.updated_by, updated_at=excluded.updated_at',
                       (point_id, fid, v, user_id, now))
        changed.append(fid)
    return changed


def clean_proposal(db, point_id, type_keys, data):
    """A centre's proposal of these data: {field_id: value} with what really changes (an empty value is not a proposal)."""
    allowed = {f['id']: f for f in fields_for(db, type_keys)}
    old = values_of(db, point_id); out = {}
    for raw_id, raw in (data or {}).items():
        try: fid = int(raw_id)
        except (TypeError, ValueError): continue
        f = allowed.get(fid)
        if not f: continue
        v = clean_value(f['kind'], raw)
        if v is not None and v != old.get(fid): out[str(fid)] = v
    return out
