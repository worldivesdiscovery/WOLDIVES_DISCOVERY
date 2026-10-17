"""v50.57 · El logbook de buceo de la cuenta: el componente «Dive Logbook» (lista clásica y pasaporte 3D) y su servidor.

The component (public/lib/logbook/logbook.js, as delivered) keeps all its state in one object:
    {v: {"d:<n>:<field>": text, "d:<n>:t_<type>": true, "o:<field>": text}, photo, pages,
     verified: {"<n>": {id, center, centerId, at, locked: [field…]}}, cover, unlocked, view, seenPassport}
where <n> is the dive's page in the book (1…120). The web saves that object in the account (logbook_books); this
module decides what the browser cannot be trusted with:
- a verified dive is one a centre registered (center_dives) and the diver claimed with its single-use QR
  (logbook_claims). Its official data is kept apart, and the fields the component locks on screen (date, place,
  country, centre, position and instructor) must be exactly those, on the same page: any change is refused, also a
  «verified» mark the person was never given;
- the centre's cover can only be the centre the person signed up with;
- the complete dives (a real date that is not in the future, and a place) are also rows of logbook_entries, so the
  points, the app, the exports and the dives of completed bookings keep working as before.
Pure functions: no database here (app/server.py reads and writes).
"""
from __future__ import annotations

import base64
import datetime as _dt
import json
import re

DIVE_FIELDS = ('no', 'date', 'site', 'country', 'center', 'depth', 'time', 'temp', 'vis', 'tin', 'tout', 'pstart', 'pend', 'weight',
               'suit', 'gas', 'buddy', 'buddyId', 'pos', 'sign', 'notes')
OWNER_FIELDS = ('first', 'last', 'nat', 'agency', 'level', 'certno', 'certdate', 'prev', 'ins', 'emerg', 'sign')
TYPES = (('boat', 'Barco'), ('shore', 'Costa'), ('night', 'Nocturna'), ('drift', 'Deriva'), ('wreck', 'Pecio'), ('deep', 'Profunda'))
TYPE_KEYS = tuple(k for k, _ in TYPES)
LOCKED_DEFAULT = ('date', 'site', 'country', 'center', 'pos', 'sign')   # DEFAULT_LOCKED of logbook.js
LABELS = {'date': 'La fecha', 'site': 'El lugar', 'country': 'El país', 'center': 'El centro', 'pos': 'La posición', 'sign': 'El instructor'}
MAX_PAGES = 60                      # the component's limit: 60 pages, 120 dives
MAX_DIVE = MAX_PAGES * 2
MAX_TEXT, MAX_NOTES, MAX_KEYS = 300, 2000, 4000
MAX_PHOTO = 400_000                 # characters of the holder's photo (a 240×310 JPEG from the component weighs ~40 KB)
KEY_RE = re.compile(r'd:(\d{1,3}):([A-Za-z_]{1,12})|o:([a-z]{1,10})')
_CTRL = re.compile(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]')
TIME_RE = re.compile(r'([01]?\d|2[0-3]):[0-5]\d')


class BookError(ValueError):
    """The logbook sent does not have the component's format."""


class LockedError(ValueError):
    """A change to what a centre registered (refused, never saved)."""


# ------------------------------------------------------------------------------------------------- small helpers
def _text(value, limit):
    s = _CTRL.sub('', str(value))
    return s[:limit]


def num_text(x):
    """18.0 → «18», 18.5 → «18.5», None → ''. The way the component shows numbers it receives as text."""
    if x is None or x == '': return ''
    try: f = float(x)
    except (TypeError, ValueError): return ''
    return str(int(f)) if f.is_integer() else str(round(f, 1))


def num_value(text, lo, hi):
    """«18,5» → 18.5 inside [lo, hi]; anything else → None."""
    try: f = float(str(text).replace(',', '.').strip())
    except (TypeError, ValueError): return None
    return round(f, 1) if lo <= f <= hi else None


def parse_date(text, today=None):
    """«18/10/2026», «8-10-26», «2026-10-18» → '2026-10-18'; anything else → None (a draft of the diver)."""
    s = str(text or '').strip()
    today = today or _dt.date.today()
    m = re.fullmatch(r'(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{2}|\d{4})', s)
    if m:
        d, mo, y = int(m.group(1)), int(m.group(2)), int(m.group(3))
        if y < 100: y += 2000 if y <= today.year % 100 else 1900
    else:
        m = re.fullmatch(r'(\d{4})-(\d{1,2})-(\d{1,2})', s)
        if not m: return None
        y, mo, d = int(m.group(1)), int(m.group(2)), int(m.group(3))
    try: return _dt.date(y, mo, d).isoformat()
    except ValueError: return None


def date_text(iso):
    """'2026-10-18' → «18/10/2026» (how the component writes dates)."""
    try: return _dt.date.fromisoformat(str(iso)[:10]).strftime('%d/%m/%Y')
    except (TypeError, ValueError): return str(iso or '')


def pos_text(lat, lon):
    """The position as the component writes it («38.16000, -0.47000»), or ''."""
    if lat is None or lon is None: return ''
    try: return f'{float(lat):.5f}, {float(lon):.5f}'
    except (TypeError, ValueError): return ''


# ------------------------------------------------------------------------------------------------- the book
def blank(pages=10):
    return {'v': {}, 'photo': '', 'pages': pages, 'verified': {}, 'cover': None, 'unlocked': None, 'view': 'classic', 'seenPassport': False}


def clean_book(raw):
    """The logbook sent by the browser, checked and normalised (unknown keys of another version are dropped).
    Raises BookError when it is not a logbook at all."""
    if not isinstance(raw, dict): raise BookError('El logbook no tiene el formato esperado.')
    v_in = raw.get('v') if raw.get('v') is not None else {}
    if not isinstance(v_in, dict) or len(v_in) > MAX_KEYS: raise BookError('El logbook no tiene el formato esperado.')
    try: pages = int(raw.get('pages') or 10)
    except (TypeError, ValueError): raise BookError('El número de páginas no es válido.')
    pages = max(1, min(MAX_PAGES, pages))
    v = {}
    for k, val in v_in.items():
        m = KEY_RE.fullmatch(str(k))
        if not m or val is None or val is False or val == '': continue
        if m.group(1):
            n, f = int(m.group(1)), m.group(2)
            if not 1 <= n <= MAX_DIVE: raise BookError('Hay una inmersión fuera del cuaderno.')
            if f.startswith('t_'):
                if f[2:] in TYPE_KEYS and val in (True, 1, '1', 'true', 'on'): v[k] = True
                continue
            if f not in DIVE_FIELDS: continue
        elif m.group(3) not in OWNER_FIELDS: continue
        else: f = m.group(3)
        if not isinstance(val, (str, int, float)) or isinstance(val, bool): raise BookError('Un dato del logbook no es texto.')
        s = _text(val, MAX_NOTES if f == 'notes' else MAX_TEXT)
        if s: v[k] = s
    photo = raw.get('photo') or ''
    if not isinstance(photo, str) or len(photo) > MAX_PHOTO or not photo.startswith('data:image/jpeg;base64,'): photo = ''
    else:
        try: ok = base64.b64decode(photo[23:], validate=True)[:3] == b'\xff\xd8\xff'
        except (ValueError, TypeError): ok = False
        if not ok: photo = ''
    verified = {}
    ver_in = raw.get('verified') or {}
    if not isinstance(ver_in, dict): raise BookError('Las inmersiones verificadas no tienen el formato esperado.')
    for n_key, ver in ver_in.items():
        try: n = int(n_key)
        except (TypeError, ValueError): raise BookError('Una inmersión verificada no tiene número.')
        if not 1 <= n <= MAX_DIVE or not isinstance(ver, dict): raise BookError('Una inmersión verificada no tiene el formato esperado.')
        locked = ver.get('locked') or []
        if not isinstance(locked, list) or any(not isinstance(x, str) for x in locked): raise BookError('Una inmersión verificada no tiene el formato esperado.')
        verified[str(n)] = {'id': _text(ver.get('id') or '', 80), 'center': _text(ver.get('center') or '', 200), 'centerId': _text(ver.get('centerId') or '', 80),
                            'at': _text(ver.get('at') or '', 40), 'locked': [x for x in locked if x in DIVE_FIELDS][:len(DIVE_FIELDS)]}
    cover = raw.get('cover')
    if isinstance(cover, dict) and cover.get('logo'):
        cover = {'logo': _text(cover.get('logo'), 500), 'name': _text(cover.get('name') or '', 200),
                 'style': cover.get('style') if cover.get('style') in ('color', 'foil') else '', 'off': bool(cover.get('off'))}
    else: cover = None
    unlocked = raw.get('unlocked')
    unlocked = {'by': _text(unlocked.get('by') or '', 20), 'at': _text(unlocked.get('at') or '', 40)} if isinstance(unlocked, dict) else None
    return {'v': v, 'photo': photo, 'pages': pages, 'verified': verified, 'cover': cover, 'unlocked': unlocked,
            'view': 'passport' if raw.get('view') == 'passport' else 'classic', 'seenPassport': bool(raw.get('seenPassport'))}


def dives_of(v):
    """{n: {field: value}} of the dives of the book (also the empty-looking ones)."""
    out = {}
    for k, val in v.items():
        m = KEY_RE.fullmatch(k)
        if m and m.group(1): out.setdefault(int(m.group(1)), {})[m.group(2)] = val
    return out


def is_empty(book, n):
    p = f'd:{n}:'
    return not any(k.startswith(p) for k in book['v']) and str(n) not in book['verified']


def free_slot(book):
    """The first free page, as the component does (it adds 10 pages when the book is full; 0 when it cannot)."""
    for i in range(1, book['pages'] * 2 + 1):
        if is_empty(book, i): return i
    if book['pages'] >= MAX_PAGES: return 0
    n = book['pages'] * 2 + 1
    book['pages'] = min(MAX_PAGES, book['pages'] + 10)
    return n


def put_dive(book, n, fields):
    for f, val in fields.items():
        if val not in (None, '', False): book['v'][f'd:{n}:{f}'] = val


def remove_dive(book, n):
    p = f'd:{n}:'
    for k in [k for k in book['v'] if k.startswith(p)]: del book['v'][k]
    book['verified'].pop(str(n), None)


# ------------------------------------------------------------------------------------------------- rows of logbook_entries
def row_fields(d, today=None):
    """The row of logbook_entries of a dive of the book, or None while it is a draft (no real date, a date in the
    future or no place)."""
    today = today or _dt.date.today()
    iso = parse_date(d.get('date'), today)
    site = str(d.get('site') or '').strip()
    if not iso or not site or iso > today.isoformat() or iso < '1950-01-01': return None
    dur = num_value(d.get('time'), 0, 600)
    return {'dive_date': iso, 'site': site[:200], 'country': str(d.get('country') or '').strip()[:100], 'depth': num_value(d.get('depth'), 0, 350),
            'duration': int(dur) if dur is not None else None, 'dive_type': ', '.join(label for key, label in TYPES if d.get('t_' + key))[:100],
            'notes': str(d.get('notes') or '').strip()[:2000]}


def dive_from_row(row):
    """The fields of the book for a row added by the app, the old form or a completed booking."""
    out = {'date': date_text(row['dive_date']), 'site': row['site'] or '', 'country': row['country'] or '', 'depth': num_text(row['depth']),
           'time': num_text(row['duration']), 'notes': row['notes'] or ''}
    labels = {label.lower(): key for key, label in TYPES}
    for part in str(row['dive_type'] or '').split(','):
        key = labels.get(part.strip().lower())
        if key: out['t_' + key] = True
    return {k: val for k, val in out.items() if val not in ('', None)}


# ------------------------------------------------------------------------------------------------- verified dives
def official(row):
    """A dive registered by a centre (row of center_dives): what lb.addDiveFromCenter() receives, the values the book
    must keep and the fields locked on screen. Position goes as text (not lat/lon) so that the browser never rounds it."""
    dive = {'id': row['uid'], 'centerId': row['center_ref'] or '', 'center': row['center_name'], 'date': date_text(row['dive_date']),
            'site': row['site'], 'country': row['country'] or '', 'instructor': row['instructor'], 'depth': num_text(row['depth']),
            'time': num_text(row['duration']), 'temp': num_text(row['temp']), 'vis': num_text(row['vis']), 'timeIn': row['time_in'] or '',
            'timeOut': row['time_out'] or '', 'gas': row['gas'] or '', 'pos': pos_text(row['lat'], row['lon']), 'notes': row['notes'] or ''}
    try: types = [t for t in json.loads(row['types'] or '[]') if t in TYPE_KEYS]
    except (TypeError, ValueError): types = []
    dive = {k: val for k, val in dive.items() if val not in (None, '')}
    if types: dive['types'] = types
    # the same correspondence as addDiveFromCenter() in logbook.js (map = {date: d.date, …, sign: d.instructor, pos: d.pos})
    src = (('date', 'date'), ('site', 'site'), ('country', 'country'), ('center', 'center'), ('depth', 'depth'), ('time', 'time'), ('temp', 'temp'),
           ('vis', 'vis'), ('tin', 'timeIn'), ('tout', 'timeOut'), ('gas', 'gas'), ('notes', 'notes'), ('sign', 'instructor'), ('pos', 'pos'))
    fields = {f: str(dive[s]) for f, s in src if dive.get(s) not in (None, '')}
    return {'dive': dive, 'fields': fields, 'locked': [f for f in LOCKED_DEFAULT if f in fields], 'center': row['center_name'], 'centerId': row['center_ref'] or ''}


def check_verified(book, claims, officials):
    """Refuses (LockedError) any change to what a centre registered:
    - a «verified» mark of a dive this person did not claim with its QR, or the same dive twice;
    - a verified dive moved to another page;
    - another centre, another list of locked fields, or another value in any of them.
    claims: {dive id: page or None (claimed, not yet in the book)}; officials: {dive id: official(...)}.
    Returns {dive id: page} of the verified dives in the book (the server binds the new ones; a claimed dive that is
    no longer marked was deleted by the diver and can come back by scanning its QR again)."""
    seen = {}
    for n_key, ver in book['verified'].items():
        n, uid = int(n_key), ver.get('id') or ''
        if uid not in claims:
            raise LockedError('Esa inmersión no la ha verificado ningún centro para tu cuenta: no se puede marcar como verificada.')
        if uid in seen: raise LockedError('La misma inmersión verificada aparece dos veces en el logbook.')
        if claims[uid] is not None and claims[uid] != n: raise LockedError('Una inmersión verificada no se puede cambiar de página.')
        off = officials[uid]
        if sorted(ver.get('locked') or []) != sorted(off['locked']) or ver.get('center') != off['center'] or (ver.get('centerId') or '') != off['centerId']:
            raise LockedError('Los datos que registró el centro en una inmersión verificada no se pueden cambiar.')
        for f in off['locked']:
            if book['v'].get(f'd:{n}:{f}') != off['fields'][f]:
                raise LockedError(f'{LABELS.get(f, "Ese dato")} de una inmersión verificada lo registró el centro y no se puede cambiar.')
        seen[uid] = n
    return seen


# ------------------------------------------------------------------------------------------------- a centre's dive
def clean_center_dive(data, today=None):
    """The dive a centre creates in its panel to hand out its QR. Raises ValueError with the reason."""
    today = today or _dt.date.today()
    iso = parse_date(data.get('date') or data.get('dive_date'), today)
    if not iso: raise ValueError('Indica la fecha de la inmersión.')
    if iso > (today + _dt.timedelta(days=1)).isoformat(): raise ValueError('La fecha de la inmersión no puede ser posterior a mañana.')
    if iso < (today - _dt.timedelta(days=366)).isoformat(): raise ValueError('La fecha de la inmersión es de hace más de un año.')
    site = _text(str(data.get('site') or '').strip(), 160).strip()
    if not site: raise ValueError('Indica el lugar de la inmersión.')
    instructor = _text(str(data.get('instructor') or '').strip(), 120).strip()
    if not instructor: raise ValueError('Indica el instructor o guía (nombre y nº de titulación).')

    def number(key, lo, hi, label):
        raw = data.get(key)
        if raw in (None, ''): return None
        val = num_value(raw, lo, hi)
        if val is None: raise ValueError(f'{label}: escribe un número entre {lo} y {hi}.')
        return val

    def hhmm(key, label):
        raw = str(data.get(key) or '').strip()
        if not raw: return None
        if not TIME_RE.fullmatch(raw): raise ValueError(f'{label}: escribe la hora como 10:05.')
        h, m = raw.split(':')
        return f'{int(h):02d}:{m}'

    def coord(raw, lim):
        try: f = float(str(raw).replace(',', '.').strip())
        except (TypeError, ValueError): return None
        return round(f, 5) if -lim <= f <= lim else None

    lat, lon = data.get('lat'), data.get('lon')
    if lat not in (None, '') or lon not in (None, ''):
        lat, lon = coord(lat, 90), coord(lon, 180)
        if lat is None or lon is None: raise ValueError('La posición no es válida (latitud y longitud).')
    else: lat = lon = None
    types = [t for t in (data.get('types') or []) if t in TYPE_KEYS] if isinstance(data.get('types'), list) else []
    dur = number('time', 0, 600, 'Tiempo')
    return {'dive_date': iso, 'site': site, 'country': _text(str(data.get('country') or '').strip(), 100).strip(), 'instructor': instructor,
            'depth': number('depth', 0, 350, 'Profundidad'), 'duration': int(dur) if dur is not None else None,
            'temp': number('temp', -2, 40, 'Temperatura del agua'), 'vis': number('vis', 0, 100, 'Visibilidad'),
            'time_in': hhmm('timeIn', 'Entrada al agua'), 'time_out': hhmm('timeOut', 'Salida del agua'), 'gas': _text(str(data.get('gas') or '').strip(), 40).strip(),
            'lat': lat, 'lon': lon, 'types': json.dumps(types), 'notes': _text(str(data.get('notes') or '').strip(), 500).strip()}


# ------------------------------------------------------------------------------------------------- the centre's logo
_SVG_BAD = re.compile(r'<\s*(script|foreignobject|iframe|object|embed|audio|video|animate|set|handler|listener)\b|\son[a-z]+\s*=|javascript:|'
                      r'<!entity|<!doctype|(?:xlink:)?href\s*=\s*["\']?\s*(?!#)|url\(\s*["\']?\s*(?!#)|@import', re.I)


def clean_logo_svg(raw: bytes) -> bytes:
    """A centre's logo in SVG for the cover of the passport: only shapes. No scripts, events, entities or anything
    loaded from elsewhere (a reference inside the same file, «#id», is allowed)."""
    if len(raw) > 300_000: raise ValueError('El logo pesa demasiado: máximo 300 KB.')
    try: text = raw.decode('utf-8')
    except UnicodeDecodeError: raise ValueError('Ese SVG no se puede leer (UTF-8).')
    if '<svg' not in text[:5000].lower(): raise ValueError('Ese archivo no es un SVG.')
    if _SVG_BAD.search(text): raise ValueError('El SVG trae código o enlaces a otros archivos: expórtalo solo con formas o súbelo en PNG transparente.')
    import xml.etree.ElementTree as ET
    try: root = ET.fromstring(text)
    except ET.ParseError: raise ValueError('El SVG está dañado.')
    if not root.tag.endswith('svg'): raise ValueError('Ese archivo no es un SVG.')
    return raw
