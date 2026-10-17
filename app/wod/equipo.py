"""v50.58 · encargo del 16/10/2026: el alquiler de equipo es un extra dentro de la inmersión, no un servicio.

The centre (or the freelance) says once which pieces it rents, their sizes, their price (per dive or per day), an
optional «Equipo completo» with a closed price and, if it wants, how many it has of each size. Each service offers
them (or says the equipment is included), and the diver marks, for each person of the booking, the pieces and the
sizes. The tank and the weights are always included: they are never a rental piece.

Pure logic, without the database: the server reads the rows and calls these functions, so the web, the app, the
widget and the API price the same selection in the same way."""
import json
import re
from collections import OrderedDict

# The list every centre finds already made (code, name, what is asked when booking).
CATALOG = (
    ('mask', 'Máscara', 'mask'),
    ('fins', 'Aletas', 'shoe'),
    ('boots', 'Escarpines', 'shoe'),
    ('wetsuit', 'Traje o neopreno', 'suit'),
    ('hood', 'Capucha', 'size'),
    ('gloves', 'Guantes', 'size'),
    ('bcd', 'Chaleco (jacket)', 'size'),
    ('regulator', 'Regulador (con octopus y manómetro)', 'none'),
    ('computer', 'Ordenador de buceo', 'none'),
    ('torch', 'Linterna', 'none'),
    ('smb', 'Boya de superficie', 'none'),
)
CODES = tuple(c for c, _, _ in CATALOG)
LABEL = {c: l for c, l, _ in CATALOG}
SIZE_KIND = {c: k for c, _, k in CATALOG}
KIT = 'full_kit'
KIT_LABEL = 'Equipo completo'
INCLUDED = ('tank', 'weights')                 # «Incluido: botella y plomos»: never a rental piece, never charged
INCLUDED_TEXT = 'Incluido: botella y plomos'
NOT_PIECES = ('botella', 'botellas', 'plomo', 'plomos', 'lastre', 'cinturón de plomos', 'tank', 'weights')
OLD_LABELS = {'wetsuit': 'Traje de neopreno', 'bcd': 'Chaleco BCD', 'regulator': 'Regulador'}   # before v50.58
LETTERS = ('XS', 'S', 'M', 'L', 'XL', 'XXL')
SHOE = tuple(str(n) for n in range(34, 49))   # EU
THICK = OrderedDict([('3', '3 mm'), ('5', '5 mm'), ('7', '7 mm'), ('semi', 'Semiseco')])
SIZE_KINDS = ('none', 'mask', 'shoe', 'suit', 'size', 'custom')
MASK = ('Normal', 'Graduada')
DEFAULT_KIT = ('mask', 'fins', 'boots', 'wetsuit', 'bcd', 'regulator')
PRICE_PER = ('dive', 'day')
RENTAL_MODES = ('offer', 'included', 'none')
# What a new service offers (Parte 2): rental in dives and boat trips; «Equipo incluido» in baptisms and courses.
DEFAULT_MODE = {'dive': 'offer', 'baptism': 'included', 'course': 'included', 'guide': 'offer', 'trip': 'offer', 'other': 'none', 'rental': 'none'}
CUSTOM_ICONS = ('camera', 'knife', 'scooter', 'tag', 'torch', 'bag')
MAX_CUSTOM = 20
MAX_DIVERS = 30
MAX_PRICE = 10000


def as_json(v, default):
    if v in (None, ''): return default
    if isinstance(v, (list, dict)): return v
    try: x = json.loads(v)
    except (TypeError, ValueError): return default
    return x if isinstance(x, type(default)) else default


def money(v, allow_none=True):
    """A price typed by the centre: 0 is valid (a piece that goes free); empty is «sin precio»."""
    if v in (None, ''):
        if allow_none: return None
        raise ValueError('Pon el precio de la pieza (0 € si va gratis).')
    try: x = round(float(str(v).replace(',', '.').replace('€', '').strip()), 2)
    except ValueError: raise ValueError('El precio no es válido.')
    if x < 0 or x > MAX_PRICE: raise ValueError('El precio no es válido.')
    return x


def clean_label(v, n=60):
    v = re.sub(r'\s+', ' ', str(v or '')).strip()
    return v[:n]


def custom_options(raw):
    """Sizes of a piece of the centre's own: «S, M, L» or a list. At most 20, each up to 16 characters."""
    items = raw if isinstance(raw, list) else re.split(r'[,;\n]', str(raw or ''))
    out = []
    for x in items:
        x = clean_label(x, 16)
        if x and x not in out: out.append(x)
    return out[:20]


def size_choices(item):
    """What the diver chooses for a piece: {'sizes': [...], 'thick': [...]}. Empty lists: nothing to choose."""
    k = item.get('size_kind') or SIZE_KIND.get(item.get('code'), 'none')
    if k == 'mask': return {'sizes': list(MASK) if item.get('prescription') else [], 'thick': []}
    if k == 'shoe': return {'sizes': list(SHOE), 'thick': []}
    if k == 'suit':
        th = [t for t in as_json(item.get('thicknesses'), []) if t in THICK] or ['5']
        return {'sizes': list(LETTERS), 'thick': th}
    if k == 'size': return {'sizes': list(LETTERS), 'thick': []}
    if k == 'custom': return {'sizes': as_json(item.get('size_options'), []), 'thick': []}
    return {'sizes': [], 'thick': []}


def merge_catalog(rows):
    """The centre's pieces: the 11 of the list (with what it saved) and its own, in order. A row of the old list
    («Botella») is never a piece. Each item: code, label, icon, price, price_per, active, size_kind, sizes…"""
    by = {r['code']: dict(r) for r in rows}
    out = []
    for i, (code, label, kind) in enumerate(CATALOG):
        r = by.get(code) or {}
        lab = r.get('label') or label
        if lab == OLD_LABELS.get(code): lab = label
        out.append({'code': code, 'label': lab, 'icon': r.get('icon') or code, 'price': r.get('price'),
                    'price_per': r.get('price_per') if r.get('price_per') in PRICE_PER else 'dive',
                    'active': bool(r.get('active')) and r.get('price') is not None, 'configured': bool(r), 'custom': False,
                    'size_kind': kind, 'thicknesses': as_json(r.get('thicknesses'), ['5']) if kind == 'suit' else [],
                    'prescription': bool(r.get('prescription')), 'in_kit': bool(r['in_kit']) if r.get('in_kit') is not None else code in DEFAULT_KIT,
                    'size_options': [], 'sort': i, 'id': r.get('id')})
    customs = sorted((r for r in by.values() if r.get('custom')), key=lambda r: (r.get('sort_order') or 0, r.get('id') or 0))
    for j, r in enumerate(customs):
        kind = r.get('size_kind') if r.get('size_kind') in SIZE_KINDS else 'none'
        out.append({'code': r['code'], 'label': r['label'], 'icon': r.get('icon') or 'tag', 'price': r.get('price'),
                    'price_per': r.get('price_per') if r.get('price_per') in PRICE_PER else 'dive',
                    'active': bool(r.get('active')) and r.get('price') is not None, 'configured': True, 'custom': True,
                    'size_kind': kind, 'thicknesses': [], 'prescription': False, 'in_kit': bool(r.get('in_kit')),
                    'size_options': as_json(r.get('size_options'), []), 'sort': 100 + j, 'id': r.get('id')})
    for it in out: it.update(size_choices(it))
    k = by.get(KIT) or {}
    kit = {'active': bool(k.get('active')) and k.get('price') is not None, 'price': k.get('price'),
           'price_per': k.get('price_per') if k.get('price_per') in PRICE_PER else 'dive', 'label': KIT_LABEL}
    return out, kit


def configured(items):
    """The centre already said what it rents: at least one piece switched on with its price (0 € included)."""
    return any(i['active'] for i in items)


def service_offer(items, kit, svc_mode, overrides):
    """What a service offers: (mode, pieces, kit). overrides = {'exclude': [codes], 'prices': {code: price}}."""
    if svc_mode not in RENTAL_MODES: svc_mode = 'offer'
    if svc_mode != 'offer': return svc_mode, [], None
    ov = overrides if isinstance(overrides, dict) else {}
    excl = set(ov.get('exclude') or []); prices = ov.get('prices') if isinstance(ov.get('prices'), dict) else {}
    pieces = []
    for it in items:
        if not it['active'] or it['code'] in excl: continue
        p = dict(it)
        if it['code'] in prices:
            try: p['price'] = money(prices[it['code']], allow_none=False)
            except ValueError: pass
        pieces.append(p)
    kit_codes = [p['code'] for p in pieces if p['in_kit']]
    k = None
    if kit and kit['active'] and len(kit_codes) >= 2:
        k = {'label': KIT_LABEL, 'price': kit['price'], 'price_per': kit['price_per'], 'codes': kit_codes,
             'pieces_total': round(sum(float(p['price'] or 0) for p in pieces if p['in_kit']), 2)}
    return 'offer', pieces, k


def clean_overrides(raw, codes):
    ov = as_json(raw, {}) if not isinstance(raw, dict) else raw
    excl = [c for c in (ov.get('exclude') or []) if c in codes]
    prices = {}
    for c, v in (ov.get('prices') or {}).items() if isinstance(ov.get('prices'), dict) else []:
        if c in codes and v not in (None, ''): prices[c] = money(v, allow_none=False)
    return {'exclude': sorted(set(excl)), 'prices': prices} if (excl or prices) else None


def legacy_selection(codes_qty, pax):
    """The old format (v50.27): «codigo» (every diver) or «codigo:cantidad» (the first ones). Without sizes."""
    divers = [{'items': [], 'kit': False} for _ in range(pax)]
    for raw in codes_qty or []:
        code, _, q = str(raw or '').strip().partition(':')
        code = code.strip()
        if not code or code in INCLUDED: continue
        try: n = int(q) if q else pax
        except ValueError: n = pax
        n = max(0, min(pax, n))
        if code == KIT:
            for d in divers[:n]: d['kit'] = True
            continue
        for d in divers[:n]: d['items'].append({'code': code, 'size': '', 'thick': ''})
    return divers


def parse_selection(raw, pax):
    """The pieces of each diver: [{'items': [{'code','size','thick'}], 'kit': bool}] (one per person, the first is
    the one who books). Accepts a list or its JSON. Unknown keys are ignored."""
    data = as_json(raw, []) if not isinstance(raw, list) else raw
    out = []
    for d in data[:MAX_DIVERS]:
        if not isinstance(d, dict): d = {}
        items, seen = [], set()
        for it in (d.get('items') or [])[:40]:
            if isinstance(it, str): it = {'code': it}
            if not isinstance(it, dict): continue
            code = clean_label(it.get('code'), 40)
            if not code or code in seen or code in INCLUDED or code == KIT: continue
            seen.add(code)
            items.append({'code': code, 'size': clean_label(it.get('size'), 16), 'thick': clean_label(it.get('thick'), 8)})
        out.append({'items': items, 'kit': bool(d.get('kit'))})
    while len(out) < pax: out.append({'items': [], 'kit': False})
    return out[:pax]


def who(i, names=None):
    names = names or []
    return (names[i] if i < len(names) and names[i] else ('Tú' if i == 0 else f'Buceador {i + 1}'))


def check_selection(sel, pieces, kit, strict=True, names=None):
    """Validates against what the service offers. strict: every piece with sizes needs its size (web, app, widget
    and API v1 with the new format). Raises ValueError with a sentence for the diver."""
    by = {p['code']: p for p in pieces}
    for i, d in enumerate(sel):
        keep = []
        for it in d['items']:
            p = by.get(it['code'])
            if not p: raise ValueError('Esa pieza de equipo ya no se alquila en este servicio. Revisa el equipo.')
            if p['sizes']:
                if it['size'] and it['size'] not in p['sizes']: raise ValueError(f"La talla de {p['label'].lower()} no es válida.")
                if not it['size']:
                    if p['size_kind'] == 'mask': it['size'] = 'Normal'
                    elif strict: raise ValueError(f"Elige la talla de {p['label'].lower()} ({who(i, names)}).")
            else: it['size'] = ''
            if p['thick']:
                if it['thick'] and it['thick'] not in p['thick']: raise ValueError('Ese grosor de traje no está disponible.')
                if not it['thick']: it['thick'] = p['thick'][0]
            else: it['thick'] = ''
            keep.append(it)
        d['items'] = keep
        if d['kit'] and not kit: d['kit'] = False
    return sel


def kit_applies(d, kit):
    return bool(kit and d.get('kit') and set(kit['codes']) <= {it['code'] for it in d['items']})


def size_text(p_or_label, it):
    parts = [it.get('size') or '', THICK.get(it.get('thick') or '', '')]
    if it.get('size') == 'Normal': parts[0] = ''
    return ' '.join(x for x in parts if x)


def price(sel, pieces, kit, units):
    """(rows, lines, info). rows: one per piece of each diver (what is saved in the booking, with its price of
    today). lines: the summary «Máscara ×2 · 10 €». units: {'dive': n dives, 'day': n days} of the activity."""
    by = {p['code']: p for p in pieces}
    rows, broken = [], []
    for i, d in enumerate(sel):
        with_kit = kit_applies(d, kit)
        if d.get('kit') and not with_kit: broken.append(i)
        if with_kit:
            n = max(1, int(units.get(kit['price_per'], 1)))
            rows.append({'diver': i, 'code': KIT, 'label': KIT_LABEL, 'size': '', 'thick': '', 'kit': 1, 'unit_price': float(kit['price'] or 0),
                         'units': n, 'price_per': kit['price_per'], 'total': round(float(kit['price'] or 0) * n, 2)})
        for it in d['items']:
            p = by.get(it['code'])
            if not p: continue
            in_kit = with_kit and it['code'] in kit['codes']
            n = max(1, int(units.get(p['price_per'], 1)))
            unit = 0.0 if in_kit else float(p['price'] or 0)
            rows.append({'diver': i, 'code': p['code'], 'label': p['label'], 'size': it.get('size') or '', 'thick': it.get('thick') or '',
                         'kit': 1 if in_kit else 0, 'unit_price': unit, 'units': n, 'price_per': p['price_per'], 'total': round(unit * n, 2)})
    return rows, lines_of(rows), {'kit_broken': broken}


def lines_of(rows):
    """The price lines of the booking, piece by piece («Inmersión 50 € + Máscara 5 € + Aletas 5 €»)."""
    agg = OrderedDict()
    for r in rows:
        if r['kit'] and r['code'] != KIT: continue   # a piece inside «Equipo completo» is in its price
        key = (r['code'], r['unit_price'], r['units'], r['price_per'])
        a = agg.setdefault(key, {'kind': 'equipment', 'code': r['code'], 'label': r['label'], 'qty': 0, 'per': r['price_per'], 'units': r['units'],
                                 'unit': round(r['unit_price'] * r['units'], 2), 'total': 0.0})
        a['qty'] += 1; a['total'] = round(a['total'] + r['total'], 2)
    out = []
    for a in agg.values():
        if a['units'] > 1: a['label'] = f"{a['label']} · {a['units']} {'días' if a['per'] == 'day' else 'inmersiones'}"
        out.append(a)
    return out


def diver_text(name, rows):
    """«Ana · Traje M 5 mm · Aletas 39 · Máscara» (what the centre prepares for that person)."""
    parts = []
    for r in rows:
        if r['code'] == KIT: parts.append(KIT_LABEL); continue
        lab = short_label(r['label'], r['code'])
        s = size_text(None, r)
        parts.append(f'{lab} {s}'.strip())
    return ' · '.join([name] + parts) if parts else ''


def short_label(label, code):
    return {'wetsuit': 'Traje', 'bcd': 'Jacket', 'regulator': 'Regulador', 'computer': 'Ordenador', 'smb': 'Boya'}.get(code, label)


def booking_text(rows, names):
    """One line per diver with pieces: «Ana · Traje M 5 mm · Aletas 39 · Máscara | Buceador 2 · Boya»."""
    by = OrderedDict()
    for r in rows: by.setdefault(r['diver'], []).append(r)
    return ' | '.join(t for t in (diver_text(who(i, names), rs) for i, rs in sorted(by.items())) if t)


PLURAL = {'mask': 'Máscaras', 'fins': 'Aletas', 'boots': 'Escarpines', 'wetsuit': 'Trajes', 'hood': 'Capuchas', 'gloves': 'Guantes',
          'bcd': 'Jackets', 'regulator': 'Reguladores', 'computer': 'Ordenadores', 'torch': 'Linternas', 'smb': 'Boyas'}


def prep_groups(rows):
    """«Equipo para preparar»: grouped by piece and size. rows: booking_equipment of the departures of a day (the
    pieces of an «Equipo completo» come with their sizes). Returns [{'code','label','count','sizes':[(size, n)]}]."""
    groups = OrderedDict()
    order = {c: i for i, c in enumerate(CODES)}
    for r in sorted(rows, key=lambda r: (order.get(r['code'], 99), r['label'])):
        if r['code'] == KIT: continue
        g = groups.setdefault(r['code'], {'code': r['code'], 'label': PLURAL.get(r['code'], r['label']), 'count': 0, 'sizes': OrderedDict()})
        g['count'] += 1
        s = size_text(None, r) or ''
        g['sizes'][s] = g['sizes'].get(s, 0) + 1
    out = []
    for g in groups.values():
        sz = sorted(g['sizes'].items(), key=lambda kv: size_order(kv[0]))
        out.append({'code': g['code'], 'label': g['label'], 'count': g['count'], 'sizes': [[s, n] for s, n in sz]})
    return out


def size_order(s):
    first = (s or '').split(' ')[0]
    if first in LETTERS: return (0, LETTERS.index(first), s)
    if first.isdigit(): return (1, int(first), s)
    return (2, 0, s)


def prep_text(groups):
    """«Aletas: 2 × 39, 1 × 42 · Trajes: 2 × M, 1 × L · Reguladores: 3»."""
    parts = []
    for g in groups:
        sized = [(s, n) for s, n in g['sizes'] if s]
        if sized: parts.append(f"{g['label']}: " + ', '.join(f'{n} × {s}' for s, n in sized) + (f" (+{g['count'] - sum(n for _, n in sized)} sin talla)" if sum(n for _, n in sized) < g['count'] else ''))
        else: parts.append(f"{g['label']}: {g['count']}")
    return ' · '.join(parts)


def stock_key(it):
    """Stock is counted per piece and size («2 jackets talla M»); a suit's thickness does not change its size, and a
    mask is a mask (graduated or not)."""
    return (it['code'], '' if it['code'] == 'mask' else (it.get('size') or ''))


def clean_stock(raw, items):
    """{code: {size: n}} typed by the centre. Empty = no limit for that size; 0 = none to rent."""
    by = {i['code']: i for i in items}
    out = {}
    for code, sizes in (raw or {}).items() if isinstance(raw, dict) else []:
        it = by.get(code)
        if not it or not isinstance(sizes, dict): continue
        allowed = set(it['sizes']) if it['sizes'] and it['size_kind'] != 'mask' else {''}
        for s, n in sizes.items():
            s = '' if s in (None, '_') else str(s)
            if s not in allowed: continue
            if n in (None, ''): out.setdefault(code, {})[s] = None; continue
            try: v = int(n)
            except (TypeError, ValueError): raise ValueError('El stock tiene que ser un número entero.')
            if v < 0 or v > 999: raise ValueError('El stock tiene que estar entre 0 y 999.')
            out.setdefault(code, {})[s] = v
    return out
