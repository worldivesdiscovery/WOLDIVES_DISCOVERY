"""v50.58 · Fichas de punto más completas y catálogo ampliado (encargo del 16/10/2026).

- Los campos nuevos de la ficha y su validación (clean_fields) y lo que se enseña de ellos (public_fields).
- Nombres comparables y posibles duplicados (tokens, similarity, candidates): a menos de 300 m o con un nombre
  parecido, sin tildes, sin artículos y con sinónimos («Bajo» y «Bajón», «Illa» e «Isla», «Cap» y «Cabo»…).
- Unir dos fichas (merge): las fotos, los centros, la vida marina, los vídeos, las reservas y las fuentes de la que se
  va pasan a la que se queda, que además recibe los datos que le falten. La que se va queda archivada (nunca se borra)
  y en point_merges queda todo lo que tenía, para poder deshacerlo a mano.
- El registro privado de fuentes (add_source): de dónde salió cada dato y cuándo se comprobó. Solo lo ve la
  administración; la web pública no lo enseña nunca.
- Los lotes nuevos (add_batch, publish_item): una zona entra «Pendiente de verificar» en una tabla aparte y no se ve
  hasta que la administración la publica, entera o punto a punto.
- Las propuestas de cambio de los centros asociados a un punto y de los buceadores (clean_proposal, apply_proposal).

Nada se inventa: un dato que no viene de una fuente se queda vacío.
"""
from __future__ import annotations

import json
import math
import re
import unicodedata
from datetime import date, datetime
from difflib import SequenceMatcher

from . import costa
from .geo import haversine_km

LANGS = ('es', 'en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh')
ACCESS = {'boat': 'Barco', 'shore': 'Costa', 'both': 'Barco y costa'}
CURRENTS = {'none': 'Nula', 'mild': 'Suave', 'moderate': 'Moderada', 'strong': 'Fuerte', 'variable': 'Variable'}
BOTTOMS = {'rock': 'Roca', 'sand': 'Arena', 'posidonia': 'Posidonia', 'coral': 'Coral', 'wall': 'Pared', 'wreck': 'Pecio',
           'cave': 'Cueva', 'rubble': 'Cascajo'}
SEASONS = {'winter': 'Invierno', 'spring': 'Primavera', 'summer': 'Verano', 'autumn': 'Otoño'}
PROTECTIONS = {'none': 'Ninguna', 'marine_reserve': 'Reserva marina', 'national_park': 'Parque nacional',
               'natural_park': 'Parque natural', 'protected_area': 'Otro espacio protegido'}
SOURCE_KINDS = {'centre': 'Centro de buceo', 'wikidata': 'Wikidata (CC0)', 'osm': 'OpenStreetMap (ODbL)',
                'official': 'Datos oficiales', 'research': 'Investigación propia', 'admin': 'Administración',
                'proposal': 'Propuesta aceptada', 'catalogue': 'Catálogo inicial'}
SOURCE_FIELDS = ('*', 'name', 'position', 'depth', 'access', 'current', 'water_temps', 'visibility', 'bottom', 'best_months',
                 'species', 'warnings', 'protection', 'description', 'type', 'level')

# campo de la ficha → columna de dive_points
COLUMNS = {'min_depth': 'min_depth', 'max_depth': 'max_depth', 'access': 'access', 'current': 'current_level',
           'water_temps': 'water_temps', 'visibility_min': 'visibility_min', 'visibility_max': 'visibility_max',
           'bottom': 'bottom', 'best_months': 'best_months', 'warnings': 'warnings', 'warnings_i18n': 'warnings_i18n',
           'protection': 'protection', 'protection_name': 'protection_name', 'permit_required': 'permit_required'}
NEW_COLUMNS = [('access', 'TEXT'), ('current_level', 'TEXT'), ('water_temps', 'TEXT'), ('bottom', 'TEXT'), ('warnings', 'TEXT'),
               ('warnings_i18n', 'TEXT'), ('protection', 'TEXT'), ('protection_name', 'TEXT'), ('permit_required', 'INTEGER'),
               ('merged_into', 'INTEGER'), ('batch_id', 'INTEGER'), ('position_check', 'TEXT')]
# lo que nunca sale en la web pública (fuentes, lotes, comprobaciones internas, quién lo escribió)
PRIVATE = ('source_name', 'source_url', 'data_confidence', 'batch_id', 'position_check', 'merged_into', 'created_by_user_id',
           'updated_by_user_id', 'description_legacy', 'description_missing', 'description_reviewed_at', 'warnings_i18n')

SCHEMA = [
    '''CREATE TABLE IF NOT EXISTS point_sources (id INTEGER PRIMARY KEY AUTOINCREMENT,
         point_id INTEGER NOT NULL REFERENCES dive_points(id) ON DELETE CASCADE, field TEXT NOT NULL DEFAULT '*',
         kind TEXT NOT NULL, ref TEXT, license TEXT, checked_at TEXT, note TEXT, user_id INTEGER, created_at TEXT NOT NULL)''',
    'CREATE INDEX IF NOT EXISTS idx_point_sources_point ON point_sources(point_id)',
    '''CREATE TABLE IF NOT EXISTS point_batches (id INTEGER PRIMARY KEY AUTOINCREMENT, zone TEXT NOT NULL, title TEXT NOT NULL,
         notes TEXT, status TEXT NOT NULL DEFAULT 'pending', created_by INTEGER, created_at TEXT NOT NULL, published_at TEXT)''',
    '''CREATE TABLE IF NOT EXISTS point_batch_items (id INTEGER PRIMARY KEY AUTOINCREMENT,
         batch_id INTEGER NOT NULL REFERENCES point_batches(id) ON DELETE CASCADE, data TEXT NOT NULL,
         name TEXT NOT NULL, country TEXT, latitude REAL, longitude REAL, status TEXT NOT NULL DEFAULT 'pending',
         match_point_id INTEGER, match_kind TEXT, match_distance_m INTEGER, match_score REAL,
         position_status TEXT, position_note TEXT, problem TEXT, point_id INTEGER,
         decided_by INTEGER, decided_at TEXT, created_at TEXT NOT NULL)''',
    'CREATE INDEX IF NOT EXISTS idx_point_batch_items ON point_batch_items(batch_id, status)',
    '''CREATE TABLE IF NOT EXISTS point_duplicates (id INTEGER PRIMARY KEY AUTOINCREMENT, a_point_id INTEGER NOT NULL,
         b_point_id INTEGER NOT NULL, distance_m INTEGER, score REAL, kind TEXT, status TEXT NOT NULL DEFAULT 'open',
         keep_id INTEGER, created_at TEXT NOT NULL, decided_by INTEGER, decided_at TEXT, UNIQUE(a_point_id, b_point_id))''',
    '''CREATE TABLE IF NOT EXISTS point_merges (id INTEGER PRIMARY KEY AUTOINCREMENT, keep_id INTEGER NOT NULL,
         drop_id INTEGER NOT NULL, snapshot TEXT NOT NULL, user_id INTEGER, created_at TEXT NOT NULL)''',
    '''CREATE TABLE IF NOT EXISTS point_change_proposals (id INTEGER PRIMARY KEY AUTOINCREMENT,
         point_id INTEGER NOT NULL REFERENCES dive_points(id) ON DELETE CASCADE, user_id INTEGER NOT NULL, center_id INTEGER,
         role TEXT NOT NULL, changes TEXT NOT NULL, note TEXT, status TEXT NOT NULL DEFAULT 'pending',
         created_at TEXT NOT NULL, reviewed_by INTEGER, reviewed_at TEXT, review_note TEXT)''',
    'CREATE INDEX IF NOT EXISTS idx_point_proposals ON point_change_proposals(status, point_id)',
]

NEAR_M = 300          # B.4: a menos de 300 m
FAR_M = 2000          # con el mismo nombre, hasta 2 km (posición poco precisa en una de las dos)
SAME = .75            # nombre parecido: a menos de 300 m es el mismo punto
CLOSE_NAME = .86      # nombre casi igual: entre 300 m y 2 km, «posible duplicado»


def now():
    return datetime.now().isoformat(timespec='seconds')


# ------------------------------------------------------------------ campos de la ficha

def _num(v, lo, hi, label):
    if v in (None, ''): return None
    try: v = float(str(v).replace(',', '.'))
    except (TypeError, ValueError): raise ValueError(f'{label}: escribe un número.')
    if not math.isfinite(v) or not (lo <= v <= hi): raise ValueError(f'{label}: entre {lo:g} y {hi:g}.')
    return round(v, 1)


def _pick(v, allowed, label):
    if v in (None, ''): return None
    v = str(v).strip()
    if v not in allowed: raise ValueError(f'{label}: valor no válido.')
    return v


def _list(v):
    if v in (None, ''): return []
    if isinstance(v, str): v = [x for x in re.split(r'[\s,;]+', v) if x]
    return list(v) if isinstance(v, (list, tuple, set)) else [v]


def clean_months(v):
    try: months = sorted({int(m) for m in _list(v)})
    except (TypeError, ValueError): raise ValueError('Los meses deben ser números del 1 al 12.')
    if any(m < 1 or m > 12 for m in months): raise ValueError('Los meses deben ser números del 1 al 12.')
    return ','.join(map(str, months)) if months else None


def clean_temps(v):
    """{'winter': [mín, máx], …} → JSON con solo las estaciones que tienen dato (0–40 °C, mínima ≤ máxima)."""
    if v in (None, '', {}): return None
    if isinstance(v, str):
        try: v = json.loads(v)
        except ValueError: raise ValueError('Temperatura del agua: formato no válido.')
    if not isinstance(v, dict): raise ValueError('Temperatura del agua: formato no válido.')
    out = {}
    for s, label in SEASONS.items():
        pair = v.get(s)
        if pair in (None, '', []): continue
        if isinstance(pair, (int, float, str)): pair = [pair, pair]
        lo = _num(pair[0] if len(pair) > 0 else None, 0, 40, f'Agua en {label.lower()}')
        hi = _num(pair[1] if len(pair) > 1 else None, 0, 40, f'Agua en {label.lower()}')
        if lo is None and hi is None: continue
        if lo is not None and hi is not None and lo > hi: raise ValueError(f'Agua en {label.lower()}: la mínima no puede ser mayor que la máxima.')
        out[s] = [lo, hi]
    return json.dumps(out, separators=(',', ':')) if out else None


def clean_i18n(v, limit=280):
    if v in (None, '', {}): return None
    if isinstance(v, str):
        try: v = json.loads(v)
        except ValueError: return None
    out = {l: re.sub(r'\s+', ' ', str(t)).strip()[:limit] for l, t in (v or {}).items() if l in LANGS and l != 'es' and str(t or '').strip()}
    return json.dumps(out, ensure_ascii=False, separators=(',', ':')) if out else None


def clean_fields(data, partial=True):
    """Los campos nuevos (y los de profundidad, visibilidad y meses, que ya existían) que trae data, validados y listos
    para dive_points: {columna: valor}. Un campo vacío se guarda vacío (None). partial: solo los que vienen."""
    out = {}
    has = lambda k: (k in data) or not partial
    if has('min_depth'): out['min_depth'] = _num(data.get('min_depth'), 0, 200, 'Profundidad mínima')
    if has('max_depth'): out['max_depth'] = _num(data.get('max_depth'), 0, 200, 'Profundidad máxima')
    if out.get('min_depth') is not None and out.get('max_depth') is not None and out['min_depth'] > out['max_depth']:
        raise ValueError('La profundidad mínima no puede ser mayor que la máxima.')
    if has('access'): out['access'] = _pick(data.get('access'), ACCESS, 'Acceso')
    if has('current'): out['current_level'] = _pick(data.get('current'), CURRENTS, 'Corriente')
    if has('water_temps'): out['water_temps'] = clean_temps(data.get('water_temps'))
    # la del año entero (v50.54), para los puntos que aún no la tienen por estación
    if has('water_temp_min'): out['water_temp_min'] = _num(data.get('water_temp_min'), 0, 40, 'Temperatura mínima del año')
    if has('water_temp_max'): out['water_temp_max'] = _num(data.get('water_temp_max'), 0, 40, 'Temperatura máxima del año')
    if out.get('water_temp_min') is not None and out.get('water_temp_max') is not None and out['water_temp_min'] > out['water_temp_max']:
        raise ValueError('La temperatura mínima del año no puede ser mayor que la máxima.')
    if has('visibility_min'): out['visibility_min'] = _num(data.get('visibility_min'), 0, 80, 'Visibilidad mínima')
    if has('visibility_max'): out['visibility_max'] = _num(data.get('visibility_max'), 0, 80, 'Visibilidad máxima')
    if out.get('visibility_min') is not None and out.get('visibility_max') is not None and out['visibility_min'] > out['visibility_max']:
        raise ValueError('La visibilidad mínima no puede ser mayor que la máxima.')
    if has('bottom'):
        b = [x for x in _list(data.get('bottom')) if x]
        bad = [x for x in b if x not in BOTTOMS]
        if bad: raise ValueError('Tipo de fondo: valor no válido.')
        out['bottom'] = ','.join(k for k in BOTTOMS if k in b) or None
    if has('best_months'): out['best_months'] = clean_months(data.get('best_months'))
    if has('warnings'):
        w = re.sub(r'\s+', ' ', str(data.get('warnings') or '')).strip()
        if len(w) > 280: raise ValueError('Avisos: como mucho 280 caracteres.')
        out['warnings'] = w or None
    if has('warnings_i18n'): out['warnings_i18n'] = clean_i18n(data.get('warnings_i18n'))
    if has('protection'): out['protection'] = _pick(data.get('protection'), PROTECTIONS, 'Protección')
    if has('protection_name'):
        n = re.sub(r'\s+', ' ', str(data.get('protection_name') or '')).strip()
        out['protection_name'] = n[:140] or None
    if has('permit_required'):
        p = data.get('permit_required')
        out['permit_required'] = None if p in (None, '') else (1 if p in (True, 1, '1', 'true', 'yes', 'si', 'sí') else 0)
    if out.get('protection') in (None, 'none'):
        if 'protection_name' in out or not partial: out['protection_name'] = None
    return out


def months_of(v):
    try: return [int(x) for x in str(v or '').split(',') if x.strip()]
    except ValueError: return []


def season_of(month, lat=None):
    """La estación de un mes en el hemisferio del punto (al sur del ecuador, al revés)."""
    s = ('winter', 'winter', 'spring', 'spring', 'spring', 'summer', 'summer', 'summer', 'autumn', 'autumn', 'autumn', 'winter')[month - 1]
    if lat is not None and lat < 0:
        s = {'winter': 'summer', 'summer': 'winter', 'spring': 'autumn', 'autumn': 'spring'}[s]
    return s


def public_fields(row, lang='es', today=None):
    """Los datos nuevos de un punto para la ficha pública: solo los que tienen valor (lo vacío no se envía)."""
    r = dict(row)
    out = {}
    if r.get('access') in ACCESS: out['access'] = r['access']
    if r.get('current_level') in CURRENTS: out['current'] = r['current_level']
    try: temps = json.loads(r.get('water_temps') or 'null') or {}
    except ValueError: temps = {}
    temps = {s: v for s, v in temps.items() if s in SEASONS and isinstance(v, list) and any(x is not None for x in v)}
    if temps:
        out['water_temps'] = temps
        lat = r.get('latitude')
        out['season_now'] = season_of((today or date.today()).month, float(lat) if lat not in (None, '') else None)
    b = [x for x in str(r.get('bottom') or '').split(',') if x in BOTTOMS]
    if b: out['bottom'] = b
    # best_months, water_temp_min/max, visibility and depth already travel with the site (as «6,7,8», numbers)
    w = (r.get('warnings') or '').strip()
    if w:
        try: tr = json.loads(r.get('warnings_i18n') or 'null') or {}
        except ValueError: tr = {}
        if lang != 'es' and tr.get(lang): out['warnings'] = tr[lang]; out['warnings_lang'] = lang
        else:
            out['warnings'] = w; out['warnings_lang'] = 'es'
            if lang != 'es': out['warnings_pending_translation'] = True
    if r.get('protection') in PROTECTIONS and r['protection'] != 'none':
        out['protection'] = r['protection']
        if r.get('protection_name'): out['protection_name'] = r['protection_name']
    if r.get('permit_required') is not None and (r.get('protection') not in (None, 'none') or r['permit_required']):
        out['permit_required'] = bool(r['permit_required'])
    out['data_status'] = 'verified' if r.get('verification_status') == 'verified' else 'pending'
    return out


def private_out(d):
    for k in PRIVATE: d.pop(k, None)
    return d


# ------------------------------------------------------------------ nombres y duplicados

ARTICLES = {'el', 'la', 'los', 'las', 'l', 'lo', 'els', 'les', 'es', 'sa', 'ses', 'so', 'sos', 'the', 'de', 'del', 'dels', 'd',
            'des', 'da', 'das', 'do', 'dos', 'di', 'du', 'al', 'a', 'y', 'i', 'e', 'and', 'of', 'en', 'o', 'u'}
SYNONYMS = {}
for _canon, _words in {
    'bajo': 'bajo bajon bajos bajones baja baix baixa baixos baixo baixon baixio bajio',
    'isla': 'isla islas illa illes illa illot illots islote islotes isleta illeta ilha ilhas island islet isola ile',
    'cueva': 'cueva cuevas cova coves covas gruta grutas grotta cave caves caverna',
    'cabo': 'cabo cap cape capo',
    'faro': 'faro far lighthouse',
    'pecio': 'pecio pecios wreck derelicte derelicto naufragio',
    'punta': 'punta puntal puntas point',
    'cala': 'cala caleta calas',
    'roca': 'roca rocas roque roques roc rocs penya pena penyal rock rocks scoglio',
    'arrecife': 'arrecife arrecifes escull esculls escollo escollos reef',
    'pared': 'pared paredes paret parets muralla wall',
    'playa': 'playa platja praia beach',
    'puerto': 'puerto port porto',
    'norte': 'norte nord north', 'sur': 'sur sud south', 'este': 'este est levante east', 'oeste': 'oeste oest poniente west',
    'grande': 'gran grande grans gros grossa', 'pequeno': 'pequeno pequena petit petita chico chica',
    'san': 'san sant santa santo sao saint st',
}.items():
    for _w in _words.split(): SYNONYMS[_w] = _canon


def fold(s):
    s = unicodedata.normalize('NFKD', str(s or '').lower())
    return ''.join(c for c in s if not unicodedata.combining(c))


def tokens(name):
    s = re.sub(r"[’'`´·.\-/]", ' ', fold(name))
    return [SYNONYMS.get(w, w) for w in re.findall(r'[a-z0-9ñ]+', s) if w not in ARTICLES]


def similarity(a, b):
    """0 a 1: lo parecidos que son dos nombres de punto (sin tildes, sin artículos, con sinónimos)."""
    ta, tb = tokens(a), tokens(b)
    if not ta or not tb: return 0.0
    sa, sb = ' '.join(ta), ' '.join(tb)
    if sa == sb: return 1.0
    seq = SequenceMatcher(None, sa, sb).ratio()
    A, B = set(ta), set(tb)
    jac = len(A & B) / len(A | B)
    common = ''.join(sorted(A & B))
    contained = .9 if (A <= B or B <= A) and len(common) >= 4 else 0.0
    return round(max(seq, jac, contained), 3)


def verdict(distance_m, score):
    """'same' (es el mismo punto), 'doubt' (que lo decida la administración) o None (son distintos)."""
    if distance_m <= NEAR_M:
        return 'same' if score >= SAME else 'doubt'
    if distance_m <= FAR_M and score >= CLOSE_NAME:
        return 'doubt'
    return None


def candidates(db, lat, lon, name, exclude=(), limit=6):
    """Los puntos publicados que pueden ser el mismo: a menos de 300 m, o hasta 2 km con un nombre casi igual."""
    try: lat, lon = float(lat), float(lon)
    except (TypeError, ValueError): return []
    dlat = FAR_M / 111320.0; dlon = dlat / max(.2, math.cos(math.radians(lat)))
    rows = db.execute('SELECT id,name,latitude,longitude FROM dive_points WHERE active=1 AND merged_into IS NULL '
                      'AND latitude BETWEEN ? AND ? AND longitude BETWEEN ? AND ?',
                      (lat - dlat, lat + dlat, lon - dlon, lon + dlon)).fetchall()
    out = []
    for r in rows:
        if r['id'] in exclude or r['latitude'] is None: continue
        d = haversine_km(lat, lon, float(r['latitude']), float(r['longitude'])) * 1000
        s = similarity(name, r['name'])
        k = verdict(d, s)
        if k: out.append({'id': r['id'], 'name': r['name'], 'distance_m': round(d), 'score': s, 'kind': k})
    out.sort(key=lambda c: (c['kind'] != 'same', c['distance_m']))
    return out[:limit]


def scan_duplicates(db):
    """Los posibles duplicados entre los puntos ya publicados (una vez por pareja: lo que la administración decidió no
    se vuelve a preguntar). Devuelve cuántas parejas nuevas quedan abiertas."""
    pts = [dict(r) for r in db.execute('SELECT id,name,latitude,longitude FROM dive_points WHERE active=1 AND merged_into IS NULL '
                                       'AND latitude IS NOT NULL AND longitude IS NOT NULL').fetchall()]
    grid = {}
    cell = FAR_M / 111320.0
    for p in pts:
        grid.setdefault((math.floor(p['latitude'] / cell), math.floor(p['longitude'] / cell)), []).append(p)
    seen = {(r[0], r[1]) for r in db.execute('SELECT a_point_id,b_point_id FROM point_duplicates').fetchall()}
    n = 0
    for p in pts:
        gy, gx = math.floor(p['latitude'] / cell), math.floor(p['longitude'] / cell)
        for dy in (-1, 0, 1):
            for dx in (-2, -1, 0, 1, 2):
                for q in grid.get((gy + dy, gx + dx), ()):
                    if q['id'] <= p['id']: continue
                    d = haversine_km(p['latitude'], p['longitude'], q['latitude'], q['longitude']) * 1000
                    if d > FAR_M: continue
                    s = similarity(p['name'], q['name']); k = verdict(d, s)
                    if not k or (p['id'], q['id']) in seen: continue
                    db.execute('INSERT OR IGNORE INTO point_duplicates(a_point_id,b_point_id,distance_m,score,kind,status,created_at) VALUES(?,?,?,?,?,?,?)',
                               (p['id'], q['id'], round(d), s, k, 'open', now()))
                    seen.add((p['id'], q['id'])); n += 1
    return n


def position_check(lat, lon, access=None, dive_type=''):
    status, note = costa.verdict(lat, lon, access, dive_type)
    return {'status': status, 'note': note, 'checked_at': now()}


# ------------------------------------------------------------------ unir dos fichas

FILL = ('region', 'zone', 'subregion', 'dive_type', 'difficulty', 'min_depth', 'max_depth', 'access_info', 'access', 'current_level',
        'water_temps', 'water_temp_min', 'water_temp_max', 'visibility_min', 'visibility_max', 'bottom', 'best_months', 'warnings',
        'warnings_i18n', 'protection', 'protection_name', 'permit_required', 'recommended_certification_id')
# (tabla, columna) que apuntan a un punto: todo pasa a la ficha que se queda
MOVE = (('dive_point_photos', 'dive_point_id'), ('center_point_links', 'dive_point_id'), ('point_species', 'dive_point_id'),
        ('route_videos', 'dive_point_id'), ('virtual_experiences', 'dive_point_id'), ('bookings', 'dive_point_id'),
        ('service_slot_points', 'dive_point_id'), ('point_position_suggestions', 'dive_point_id'),
        ('point_change_proposals', 'point_id'), ('point_sources', 'point_id'))


def _table_exists(db, name):
    return bool(db.execute("SELECT 1 FROM sqlite_master WHERE type='table' AND name=?", (name,)).fetchone())


def merge(db, keep_id, drop_id, user_id=None):
    """Une drop en keep. Devuelve un resumen. Nada se borra: lo que no puede pasar (un centro que ya estaba enlazado a
    las dos, la misma especie en las dos) se queda en la ficha archivada."""
    if keep_id == drop_id: raise ValueError('Elige dos fichas distintas.')
    keep = db.execute('SELECT * FROM dive_points WHERE id=?', (keep_id,)).fetchone()
    drop = db.execute('SELECT * FROM dive_points WHERE id=?', (drop_id,)).fetchone()
    if not keep or not drop: raise ValueError('Punto no encontrado.')
    if drop['merged_into']: raise ValueError('Esa ficha ya se unió a otra.')
    if not keep['active'] or keep['merged_into']: raise ValueError('La ficha que se queda tiene que estar publicada.')
    snap = {'point': dict(drop), 'rows': {}}
    moved = {}
    for table, col in MOVE:
        if not _table_exists(db, table): continue
        ids = [r[0] for r in db.execute(f'SELECT rowid FROM {table} WHERE {col}=?', (drop_id,)).fetchall()]
        snap['rows'][table] = ids
        if not ids: continue
        cur = db.execute(f'UPDATE OR IGNORE {table} SET {col}=? WHERE {col}=?', (keep_id, drop_id))
        moved[table] = cur.rowcount
    if _table_exists(db, 'content_reports'):
        db.execute("UPDATE content_reports SET target_id=? WHERE target_type='point' AND target_id=?", (keep_id, drop_id))
    db.execute('UPDATE point_batch_items SET point_id=? WHERE point_id=?', (keep_id, drop_id))
    db.execute('UPDATE point_batch_items SET match_point_id=? WHERE match_point_id=?', (keep_id, drop_id))
    # los datos que faltan en la que se queda
    filled = []
    for f in FILL:
        if f in keep.keys() and keep[f] in (None, '') and drop[f] not in (None, ''):
            db.execute(f'UPDATE dive_points SET {f}=? WHERE id=?', (drop[f], keep_id)); filled.append(f)
    if keep['latitude'] is None and drop['latitude'] is not None:
        db.execute('UPDATE dive_points SET latitude=?, longitude=? WHERE id=?', (drop['latitude'], drop['longitude'], keep_id)); filled.append('position')
    db.execute("UPDATE dive_points SET active=0, merged_into=?, verification_status='merged', updated_by_user_id=?, updated_at=? WHERE id=?",
               (keep_id, user_id, now(), drop_id))
    db.execute('UPDATE dive_points SET updated_by_user_id=?, updated_at=? WHERE id=?', (user_id, now(), keep_id))
    db.execute("UPDATE point_duplicates SET status='merged', keep_id=?, decided_by=?, decided_at=? WHERE status='open' AND "
               "((a_point_id=? AND b_point_id=?) OR (a_point_id=? AND b_point_id=?))", (keep_id, user_id, now(), keep_id, drop_id, drop_id, keep_id))
    # las parejas abiertas de la ficha archivada pasan a la que se queda (sin repetir la misma pareja)
    for r in db.execute("SELECT id,a_point_id,b_point_id FROM point_duplicates WHERE status='open' AND (a_point_id=? OR b_point_id=?)", (drop_id, drop_id)).fetchall():
        other = r['b_point_id'] if r['a_point_id'] == drop_id else r['a_point_id']
        if other == keep_id: continue
        a, b = sorted((other, keep_id))
        if db.execute('SELECT 1 FROM point_duplicates WHERE a_point_id=? AND b_point_id=?', (a, b)).fetchone():
            db.execute("UPDATE point_duplicates SET status='merged', keep_id=?, decided_by=?, decided_at=? WHERE id=?", (keep_id, user_id, now(), r['id']))
        else:
            db.execute('UPDATE point_duplicates SET a_point_id=?, b_point_id=? WHERE id=?', (a, b, r['id']))
    db.execute('INSERT INTO point_merges(keep_id,drop_id,snapshot,user_id,created_at) VALUES(?,?,?,?,?)',
               (keep_id, drop_id, json.dumps(snap, ensure_ascii=False, default=str), user_id, now()))
    return {'keep_id': keep_id, 'drop_id': drop_id, 'moved': moved, 'filled': filled}


def keep_separate(db, dup_id, user_id=None):
    db.execute("UPDATE point_duplicates SET status='separate', decided_by=?, decided_at=? WHERE id=? AND status='open'", (user_id, now(), dup_id))


# ------------------------------------------------------------------ registro de fuentes (privado)

def add_source(db, point_id, kind, ref=None, field='*', license=None, checked_at=None, note=None, user_id=None):
    if kind not in SOURCE_KINDS: raise ValueError('Tipo de fuente no válido.')
    field = field if field in SOURCE_FIELDS else '*'
    ref = re.sub(r'\s+', ' ', str(ref or '')).strip()[:500] or None
    if ref and re.match(r'(?i)^(javascript|data):', ref): raise ValueError('Referencia no válida.')
    checked = str(checked_at or date.today().isoformat())[:10]
    try: date.fromisoformat(checked)
    except ValueError: raise ValueError('Fecha de comprobación no válida (aaaa-mm-dd).')
    db.execute('INSERT INTO point_sources(point_id,field,kind,ref,license,checked_at,note,user_id,created_at) VALUES(?,?,?,?,?,?,?,?,?)',
               (point_id, field, kind, ref, (str(license or '').strip()[:80] or None), checked,
                (re.sub(r'\s+', ' ', str(note or '')).strip()[:500] or None), user_id, now()))


def sources_of(db, point_id):
    return [dict(r) for r in db.execute('SELECT id,field,kind,ref,license,checked_at,note,created_at FROM point_sources WHERE point_id=? ORDER BY checked_at DESC, id DESC', (point_id,)).fetchall()]


# ------------------------------------------------------------------ propuestas de cambio

POSITION = ('latitude', 'longitude')
CENTRE_FIELDS = POSITION + ('current', 'visibility_min', 'visibility_max', 'warnings')
DIVER_FIELDS = POSITION + ('min_depth', 'max_depth', 'access', 'current', 'water_temps', 'visibility_min', 'visibility_max', 'bottom',
                           'best_months', 'warnings', 'protection', 'protection_name', 'permit_required')


def clean_proposal(point, data, role):
    """Lo que cambia de verdad respecto a la ficha, validado: {campo: valor nuevo}. Solo los campos de su papel."""
    allowed = CENTRE_FIELDS if role == 'center' else DIVER_FIELDS
    p = dict(point); changes = {}
    if any(k in data for k in POSITION):
        try:
            lat, lon = float(data.get('latitude')), float(data.get('longitude'))
        except (TypeError, ValueError):
            raise ValueError('Marca la posición en el mapa.')
        if not (-90 <= lat <= 90 and -180 <= lon <= 180): raise ValueError('Posición fuera de rango.')
        if p.get('latitude') is None or haversine_km(lat, lon, float(p['latitude']), float(p['longitude'])) * 1000 > 5:
            changes['latitude'] = round(lat, 6); changes['longitude'] = round(lon, 6)
    sub = {k: data[k] for k in allowed if k in data and k not in POSITION}
    vals = clean_fields(sub)
    for field in sub:
        col = COLUMNS.get(field)
        if not col or col not in vals: continue
        new = vals[col]
        old = p.get(col)
        if col in ('min_depth', 'max_depth', 'visibility_min', 'visibility_max'):
            same = (old is None and new is None) or (old is not None and new is not None and abs(float(old) - float(new)) < .05)
        else:
            same = (old or None) == (new or None)
        if not same and new is not None: changes[field] = data[field] if field in ('water_temps', 'bottom', 'best_months') else new
    if not changes: raise ValueError('No has cambiado nada.')
    return changes


def apply_proposal(db, prop, user_id):
    """Aplica una propuesta aceptada: la ficha cambia y cada dato apunta su fuente (la propuesta, con su fecha)."""
    point = db.execute('SELECT * FROM dive_points WHERE id=?', (prop['point_id'],)).fetchone()
    if not point: raise ValueError('Punto no encontrado.')
    changes = json.loads(prop['changes'])
    sets, args = [], []
    if 'latitude' in changes:
        sets += ['latitude=?', 'longitude=?']; args += [float(changes['latitude']), float(changes['longitude'])]
    vals = clean_fields({k: v for k, v in changes.items() if k not in POSITION})
    for col, v in vals.items():
        sets.append(f'{col}=?'); args.append(v)
    if not sets: return
    sets += ['updated_by_user_id=?', 'updated_at=?']; args += [user_id, now(), prop['point_id']]
    db.execute(f'UPDATE dive_points SET {", ".join(sets)} WHERE id=?', args)
    kind = 'centre' if prop['role'] == 'center' else 'proposal'
    fields = {'position' if k in POSITION else 'depth' if k.endswith('_depth') else 'visibility' if k.startswith('visibility')
              else 'protection' if k.startswith('protection') or k == 'permit_required' else k for k in changes}
    for f in sorted(fields):
        add_source(db, prop['point_id'], kind, f'Propuesta #{prop["id"]}', field=f, user_id=user_id,
                   note=('Centro #' + str(prop['center_id'])) if prop['center_id'] else ('Usuario #' + str(prop['user_id'])))


# ------------------------------------------------------------------ lotes nuevos

def _item_fields(it):
    """De un elemento de lote: (nombre, lat, lon, columnas de la ficha) o ValueError."""
    name = re.sub(r'\s+', ' ', str(it.get('name') or '')).strip()[:180]
    if not name: raise ValueError('Falta el nombre.')
    try: lat, lon = float(it.get('latitude')), float(it.get('longitude'))
    except (TypeError, ValueError): raise ValueError('Falta la posición GPS.')
    if not (-90 <= lat <= 90 and -180 <= lon <= 180) or (lat == 0 and lon == 0): raise ValueError('Posición GPS fuera de rango.')
    return name, round(lat, 6), round(lon, 6), clean_fields({k: v for k, v in it.items() if k in (
        'min_depth', 'max_depth', 'access', 'current', 'water_temps', 'visibility_min', 'visibility_max', 'bottom', 'best_months',
        'warnings', 'warnings_i18n', 'protection', 'protection_name', 'permit_required')})


def assess_item(db, row_id):
    """Vuelve a mirar un elemento del lote: posibles duplicados (con lo publicado y con el resto del lote) y mar/tierra."""
    it = db.execute('SELECT * FROM point_batch_items WHERE id=?', (row_id,)).fetchone()
    data = json.loads(it['data'])
    try:
        name, lat, lon, cols = _item_fields(data)
        problem = None
    except ValueError as e:
        db.execute("UPDATE point_batch_items SET problem=?, position_status='error', position_note=? WHERE id=?", (str(e), str(e), row_id)); return
    cand = candidates(db, lat, lon, name)
    match = cand[0] if cand else None
    if not match:   # dos veces el mismo punto en el mismo lote
        for o in db.execute("SELECT id,name,latitude,longitude FROM point_batch_items WHERE batch_id=? AND id<? AND status='pending'", (it['batch_id'], row_id)).fetchall():
            if o['latitude'] is None: continue
            d = haversine_km(lat, lon, o['latitude'], o['longitude']) * 1000; s = similarity(name, o['name'])
            if verdict(d, s) == 'same':
                problem = f'Repetido en el lote (elemento {o["id"]})'
                break
    pos = position_check(lat, lon, data.get('access'), data.get('dive_type') or '')
    db.execute('UPDATE point_batch_items SET name=?, latitude=?, longitude=?, match_point_id=?, match_kind=?, match_distance_m=?, match_score=?, '
               'position_status=?, position_note=?, problem=? WHERE id=?',
               (name, lat, lon, match['id'] if match else None, match['kind'] if match else None, match['distance_m'] if match else None,
                match['score'] if match else None, pos['status'], pos['note'], problem, row_id))


def add_batch(db, zone, title, items, user_id=None, notes=''):
    """Un lote de una zona, «Pendiente de verificar»: nada se publica hasta que la administración lo decide."""
    zone = re.sub(r'\s+', ' ', str(zone or '')).strip()[:80]; title = re.sub(r'\s+', ' ', str(title or '')).strip()[:160]
    if not zone or not title: raise ValueError('El lote necesita zona y título.')
    if not isinstance(items, list) or not items: raise ValueError('El lote está vacío.')
    if len(items) > 2000: raise ValueError('Como mucho 2.000 puntos por lote.')
    cur = db.execute('INSERT INTO point_batches(zone,title,notes,status,created_by,created_at) VALUES(?,?,?,?,?,?)',
                     (zone, title, str(notes or '')[:2000] or None, 'pending', user_id, now()))
    bid = cur.lastrowid
    for it in items:
        if not isinstance(it, dict): continue
        c = db.execute('INSERT INTO point_batch_items(batch_id,data,name,country,status,created_at) VALUES(?,?,?,?,?,?)',
                       (bid, json.dumps(it, ensure_ascii=False), str(it.get('name') or '?')[:180], str(it.get('country') or '')[:100] or None, 'pending', now()))
        assess_item(db, c.lastrowid)
    return bid


def _insert_point(db, data, name, lat, lon, cols, user_id, batch_id, verified):
    base = {'name': name, 'country': str(data.get('country') or '').strip()[:100], 'region': str(data.get('region') or '').strip()[:120] or None,
            'zone': str(data.get('zone') or '').strip()[:80] or None, 'subregion': str(data.get('subregion') or '').strip()[:120] or None,
            'dive_type': str(data.get('dive_type') or 'Inmersión').strip()[:100], 'difficulty': str(data.get('difficulty') or '').strip()[:50] or None,
            'description': re.sub(r'\s+', ' ', str(data.get('description') or '')).strip()[:5000] or None,
            'latitude': lat, 'longitude': lon, 'verification_status': 'verified' if verified else 'curated_pending',
            'data_confidence': 'batch', 'source_name': f'Lote #{batch_id}' if batch_id else None, 'batch_id': batch_id,
            'created_by_user_id': user_id, 'updated_by_user_id': user_id, 'active': 1, 'created_at': now(), 'updated_at': now()}
    if not base['country']: raise ValueError('Falta el país.')
    base.update(cols)
    names = [name] + [f'{name} ({x})' for x in (base['subregion'], base['region']) if x]
    for n in names:
        if not db.execute('SELECT 1 FROM dive_points WHERE name=? AND country=?', (n, base['country'])).fetchone():
            base['name'] = n; break
    else:
        raise ValueError(f'Ya hay otro punto llamado «{name}» en {base["country"]}: cámbiale el nombre en el lote.')
    keys = list(base)
    cur = db.execute(f'INSERT INTO dive_points({",".join(keys)}) VALUES({",".join("?" * len(keys))})', [base[k] for k in keys])
    return cur.lastrowid


def _complete_point(db, pid, data, cols, user_id):
    """Completa una ficha existente con lo que le falta (nunca pisa un dato que ya tiene)."""
    p = db.execute('SELECT * FROM dive_points WHERE id=?', (pid,)).fetchone()
    filled = []
    extra = {'region': data.get('region'), 'subregion': data.get('subregion'), 'zone': data.get('zone'), 'difficulty': data.get('difficulty')}
    for col, v in list(cols.items()) + [(k, v) for k, v in extra.items() if v]:
        if v in (None, '') or col not in p.keys() or p[col] not in (None, ''): continue
        db.execute(f'UPDATE dive_points SET {col}=? WHERE id=?', (v, pid)); filled.append(col)
    if filled: db.execute('UPDATE dive_points SET updated_by_user_id=?, updated_at=? WHERE id=?', (user_id, now(), pid))
    return filled


def publish_item(db, item_id, user_id=None, decision=None, verified=False):
    """Publica un elemento del lote. decision: 'complete' (completa la ficha que ya existe) o 'new' (ficha nueva);
    obligatoria si es un posible duplicado. Devuelve (estado, id del punto)."""
    it = db.execute('SELECT * FROM point_batch_items WHERE id=?', (item_id,)).fetchone()
    if not it: raise ValueError('Elemento no encontrado.')
    if it['status'] != 'pending': raise ValueError('Ese punto del lote ya está decidido.')
    data = json.loads(it['data'])
    name, lat, lon, cols = _item_fields(data)
    if it['position_status'] == 'error': raise ValueError(f'«{name}»: {it["position_note"]}. Corrige la posición antes de publicarlo.')
    if it['problem']: raise ValueError(f'«{name}»: {it["problem"]}.')
    if it['match_kind'] == 'doubt' and decision not in ('complete', 'new'):
        raise ValueError(f'«{name}» puede ser la ficha «{_name(db, it["match_point_id"])}»: elige completar esa ficha o crear una nueva.')
    if it['match_point_id'] and (decision == 'complete' or (it['match_kind'] == 'same' and decision != 'new')):
        pid = it['match_point_id']; filled = _complete_point(db, pid, data, cols, user_id); status = 'merged'
    else:
        pid = _insert_point(db, data, name, lat, lon, cols, user_id, it['batch_id'], verified); filled = None; status = 'published'
        db.execute('UPDATE dive_points SET position_check=? WHERE id=?',
                   (json.dumps({'status': it['position_status'], 'note': it['position_note'], 'checked_at': now()}, ensure_ascii=False), pid))
    for s in data.get('sources') or [{'kind': 'admin', 'ref': f'Lote #{it["batch_id"]}'}]:
        try: add_source(db, pid, s.get('kind') or 'research', s.get('ref'), s.get('field') or '*', s.get('license'), s.get('checked_at'), s.get('note'), user_id)
        except ValueError: continue
    db.execute('UPDATE point_batch_items SET status=?, point_id=?, decided_by=?, decided_at=? WHERE id=?', (status, pid, user_id, now(), item_id))
    _batch_status(db, it['batch_id'])
    return status, pid, filled


def discard_item(db, item_id, user_id=None):
    it = db.execute('SELECT batch_id,status FROM point_batch_items WHERE id=?', (item_id,)).fetchone()
    if not it or it['status'] != 'pending': raise ValueError('Ese punto del lote ya está decidido.')
    db.execute("UPDATE point_batch_items SET status='discarded', decided_by=?, decided_at=? WHERE id=?", (user_id, now(), item_id))
    _batch_status(db, it['batch_id'])


def _batch_status(db, bid):
    left = db.execute("SELECT COUNT(*) FROM point_batch_items WHERE batch_id=? AND status='pending'", (bid,)).fetchone()[0]
    done = db.execute("SELECT COUNT(*) FROM point_batch_items WHERE batch_id=? AND status IN ('published','merged')", (bid,)).fetchone()[0]
    st = 'pending' if left and not done else 'partial' if left else 'published'
    db.execute('UPDATE point_batches SET status=?, published_at=CASE WHEN ?=\'published\' THEN ? ELSE published_at END WHERE id=?', (st, st, now(), bid))


def _name(db, pid):
    r = db.execute('SELECT name FROM dive_points WHERE id=?', (pid,)).fetchone()
    return r['name'] if r else '?'


def batch_summary(db, bid):
    rows = db.execute('SELECT status, COUNT(*) AS n FROM point_batch_items WHERE batch_id=? GROUP BY status', (bid,)).fetchall()
    out = {r['status']: r['n'] for r in rows}
    flags = db.execute("""SELECT SUM(position_status='error') AS land, SUM(position_status IN ('warn','unknown')) AS check_pos,
                                 SUM(match_kind='doubt') AS doubts, SUM(match_kind='same') AS same, SUM(problem IS NOT NULL) AS problems
                            FROM point_batch_items WHERE batch_id=? AND status='pending'""", (bid,)).fetchone()
    out.update({k: flags[k] or 0 for k in flags.keys()})
    return out
