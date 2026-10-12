"""Common agenda engine (encargo unificado, bloque A · v50.44): pure helpers, no database access.

A *resource* (a freelance, an instructor, a boat…) is busy from *starts_at* to *ends_at* (UTC) because of a *block*.
Services booked by days or half days are shown and stored in the local time of the place of the service (its IANA
time zone), so a guide in Mexico and a diver in Spain see the same days. Everything here is deterministic and is
tested on its own (tests/test_v50_44_agenda.py).
"""
from __future__ import annotations

import datetime as _dt
import json
import re
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

UNITS = ('slot', 'day', 'half_day')            # «Por salida» (as before), «Por días», «Por días o medias jornadas»
DAY_UNITS = ('day', 'half_day')
PARTS = ('full', 'am', 'pm')
DEFAULT_TZ = 'Europe/Madrid'
DEFAULT_RULES = {'min_days': 1, 'max_days': 14, 'continuous': True, 'lead_hours': 48,
                 'am': ['08:00', '13:00'], 'pm': ['14:00', '19:00'], 'full': ['08:00', '16:00']}
# Default time zone by country (name as stored in profiles and centres, or ISO code). Anything else: DEFAULT_TZ.
COUNTRY_TZ = {
    'españa': 'Europe/Madrid', 'es': 'Europe/Madrid', 'spain': 'Europe/Madrid', 'portugal': 'Europe/Lisbon', 'pt': 'Europe/Lisbon',
    'francia': 'Europe/Paris', 'france': 'Europe/Paris', 'fr': 'Europe/Paris', 'italia': 'Europe/Rome', 'italy': 'Europe/Rome', 'it': 'Europe/Rome',
    'alemania': 'Europe/Berlin', 'germany': 'Europe/Berlin', 'de': 'Europe/Berlin', 'grecia': 'Europe/Athens', 'greece': 'Europe/Athens',
    'croacia': 'Europe/Zagreb', 'croatia': 'Europe/Zagreb', 'malta': 'Europe/Malta', 'reino unido': 'Europe/London', 'uk': 'Europe/London',
    'países bajos': 'Europe/Amsterdam', 'netherlands': 'Europe/Amsterdam', 'polonia': 'Europe/Warsaw', 'poland': 'Europe/Warsaw',
    'egipto': 'Africa/Cairo', 'egypt': 'Africa/Cairo', 'méxico': 'America/Cancun', 'mexico': 'America/Cancun', 'mx': 'America/Cancun',
    'estados unidos': 'America/New_York', 'usa': 'America/New_York', 'cuba': 'America/Havana', 'república dominicana': 'America/Santo_Domingo',
    'honduras': 'America/Tegucigalpa', 'belice': 'America/Belize', 'colombia': 'America/Bogota', 'ecuador': 'America/Guayaquil',
    'brasil': 'America/Sao_Paulo', 'tailandia': 'Asia/Bangkok', 'thailand': 'Asia/Bangkok', 'indonesia': 'Asia/Makassar',
    'filipinas': 'Asia/Manila', 'philippines': 'Asia/Manila', 'maldivas': 'Indian/Maldives', 'maldives': 'Indian/Maldives',
    'australia': 'Australia/Brisbane', 'japón': 'Asia/Tokyo', 'china': 'Asia/Shanghai', 'rusia': 'Europe/Moscow', 'russia': 'Europe/Moscow',
    'sudáfrica': 'Africa/Johannesburg', 'mozambique': 'Africa/Maputo', 'canarias': 'Atlantic/Canary'}
HHMM = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')


# ------------------------------------------------------------------------------------------------- time zones
def valid_tz(name) -> str | None:
    try:
        if name and isinstance(name, str) and len(name) < 64:
            ZoneInfo(name); return name
    except (ZoneInfoNotFoundError, ValueError):
        pass
    return None


def tz_for_country(country, fallback=DEFAULT_TZ) -> str:
    return COUNTRY_TZ.get(str(country or '').strip().lower(), fallback)


def local_to_utc(day: str, hhmm: str, tz: str) -> str:
    """'2026-11-16', '08:00' in America/Cancun → '2026-11-16T13:00:00Z'. Wall times that do not exist (spring
    forward) move forward; repeated ones (fall back) take the first, as zoneinfo does with fold=0."""
    h, m = (int(x) for x in hhmm.split(':')) if hhmm != '24:00' else (0, 0)
    d = _dt.date.fromisoformat(day) + (_dt.timedelta(days=1) if hhmm == '24:00' else _dt.timedelta())
    local = _dt.datetime(d.year, d.month, d.day, h, m, tzinfo=ZoneInfo(tz))
    # normalise a non-existent wall time (DST gap): round-trip through UTC
    utc = local.astimezone(_dt.timezone.utc)
    return utc.strftime('%Y-%m-%dT%H:%M:%SZ')


def utc_to_local(iso_utc: str, tz: str) -> _dt.datetime:
    return _dt.datetime.strptime(iso_utc, '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=_dt.timezone.utc).astimezone(ZoneInfo(tz))


def today_in(tz: str, now_utc: _dt.datetime | None = None) -> _dt.date:
    n = now_utc or _dt.datetime.now(_dt.timezone.utc)
    return n.astimezone(ZoneInfo(tz)).date()


def to_server_local(day: str, hhmm: str, tz: str) -> _dt.datetime:
    """The same instant as a naive datetime in the server's local time (the clock used by the booking deadlines)."""
    utc = _dt.datetime.strptime(local_to_utc(day, hhmm, tz), '%Y-%m-%dT%H:%M:%SZ').replace(tzinfo=_dt.timezone.utc)
    return utc.astimezone().replace(tzinfo=None)


def month_days(month: str) -> list[str]:
    y, m = (int(x) for x in month.split('-'))
    first = _dt.date(y, m, 1)
    nxt = _dt.date(y + (m == 12), 1 if m == 12 else m + 1, 1)
    return [(first + _dt.timedelta(days=i)).isoformat() for i in range((nxt - first).days)]


def clean_month(value, tz=DEFAULT_TZ) -> str:
    v = str(value or '')
    if re.fullmatch(r'\d{4}-(0[1-9]|1[0-2])', v) and 2000 <= int(v[:4]) <= 2100: return v
    return today_in(tz).strftime('%Y-%m')


# ------------------------------------------------------------------------------------------------- rules & pricing
def _num(v, lo=None, hi=None, default=None, cast=float):
    try:
        x = cast(v)
    except (TypeError, ValueError):
        return default
    if lo is not None and x < lo: return default
    if hi is not None and x > hi: return default
    return x


def _window(v, default):
    if isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(x, str) and HHMM.match(x) for x in v) and v[0] < v[1]:
        return [v[0], v[1]]
    return list(default)


def clean_rules(raw) -> dict:
    """Rules of a service booked by days, from the service form (never trusted as they come)."""
    r = raw if isinstance(raw, dict) else (json.loads(raw) if isinstance(raw, str) and raw.strip().startswith('{') else {})
    out = dict(DEFAULT_RULES)
    out['min_days'] = _num(r.get('min_days'), 1, 60, 1, int)
    out['max_days'] = max(out['min_days'], _num(r.get('max_days'), 1, 90, 14, int))
    out['continuous'] = bool(r.get('continuous', True))
    out['lead_hours'] = _num(r.get('lead_hours'), 0, 24 * 60, 48, int)
    for k in ('am', 'pm', 'full'): out[k] = _window(r.get(k), DEFAULT_RULES[k])
    if out['am'][1] > out['pm'][0]:   # morning and afternoon must not overlap
        out['am'], out['pm'] = list(DEFAULT_RULES['am']), list(DEFAULT_RULES['pm'])
    return out


def clean_pricing(raw, base_price=0.0) -> dict:
    """{per: group|person, day, half, tiers: [{min_days, day}], discount: {min_days, pct}, extras: [{id, label, price, per}]}"""
    p = raw if isinstance(raw, dict) else (json.loads(raw) if isinstance(raw, str) and raw.strip().startswith('{') else {})
    out = {'per': 'person' if p.get('per') == 'person' else 'group',
           'day': round(_num(p.get('day'), 0, 1e6, float(base_price or 0)), 2),
           'half': round(_num(p.get('half'), 0, 1e6, 0.0), 2) if p.get('half') not in (None, '') else None,
           'tiers': [], 'discount': None, 'extras': []}
    for t in (p.get('tiers') or [])[:6]:
        d = _num((t or {}).get('min_days'), 2, 90, None, int); v = _num((t or {}).get('day'), 0, 1e6, None)
        if d and v is not None: out['tiers'].append({'min_days': d, 'day': round(v, 2)})
    out['tiers'].sort(key=lambda t: t['min_days'])
    dsc = p.get('discount') or {}
    d = _num(dsc.get('min_days'), 2, 90, None, int); pct = _num(dsc.get('pct'), 1, 90, None)
    if d and pct: out['discount'] = {'min_days': d, 'pct': round(pct, 2)}
    for i, x in enumerate((p.get('extras') or [])[:12]):
        label = re.sub(r'\s+', ' ', str((x or {}).get('label') or ''))[:80].strip(); price = _num((x or {}).get('price'), 0, 1e6, None)
        if label and price is not None:
            out['extras'].append({'id': str((x or {}).get('id') or f'x{i + 1}')[:20], 'label': label, 'price': round(price, 2),
                                  'per': 'booking' if x.get('per') == 'booking' else 'day', 'per_person': bool(x.get('per_person'))})
    return out


def quote(pricing: dict, days: list[str], part: str, participants: int, extra_ids=(), title='Servicio') -> tuple[float, list[dict]]:
    """Total and price lines of a booking by days. Half days count as one unit at the half-day price."""
    n = len(days); pax = max(1, int(participants or 1)); mult = pax if pricing.get('per') == 'person' else 1
    lines = []
    if part in ('am', 'pm'):
        unit = pricing.get('half') if pricing.get('half') is not None else round(pricing['day'] / 2, 2)
        label = f"{title} · {'mañana' if part == 'am' else 'tarde'}"
    else:
        unit = pricing['day']
        for t in pricing.get('tiers') or []:
            if n >= t['min_days']: unit = t['day']
        label = title
    lines.append({'kind': 'service', 'label': label, 'unit': round(unit, 2), 'qty': n * mult, 'days': n, 'total': round(unit * n * mult, 2)})
    base = lines[0]['total']
    dsc = pricing.get('discount')
    if dsc and part == 'full' and n >= dsc['min_days']:
        lines.append({'kind': 'discount', 'label': f"−{dsc['pct']:g} % desde {dsc['min_days']} días", 'unit': None, 'qty': 1,
                      'total': -round(base * dsc['pct'] / 100, 2)})
    wanted = {str(x) for x in (extra_ids or [])}
    for x in pricing.get('extras') or []:
        if x['id'] not in wanted: continue
        q = (n if x['per'] == 'day' else 1) * (pax if x['per_person'] else 1)
        lines.append({'kind': 'extra', 'id': x['id'], 'label': x['label'], 'unit': x['price'], 'qty': q, 'total': round(x['price'] * q, 2)})
    return round(sum(l['total'] for l in lines), 2), lines


# ------------------------------------------------------------------------------------------------- windows & states
def part_window(rules: dict, part: str) -> tuple[str, str]:
    """Hours a booking of that part keeps the resource busy. A full day keeps it busy the whole day."""
    if part == 'am': return tuple(rules['am'])
    if part == 'pm': return tuple(rules['pm'])
    return ('00:00', '24:00')


def block_span(day_from: str, day_to: str, part: str, rules: dict, tz: str) -> tuple[str, str]:
    a, b = part_window(rules, part)
    return local_to_utc(day_from, a, tz), local_to_utc(day_to, b, tz)


def overlaps(a_start: str, a_end: str, b_start: str, b_end: str) -> bool:
    return a_start < b_end and b_start < a_end


def day_states(days: list[str], blocks: list[dict], rules: dict, tz: str, unit: str, working_days=None, closures=(),
               now_utc: _dt.datetime | None = None) -> dict[str, str]:
    """State of each day for the public calendar: free · busy · am (morning taken, afternoon free) · pm · off.
    Never names, reasons or hours: only one word per day."""
    now = now_utc or _dt.datetime.now(_dt.timezone.utc)
    earliest = (now + _dt.timedelta(hours=int(rules.get('lead_hours') or 0))).strftime('%Y-%m-%dT%H:%M:%SZ')
    work = set(working_days) if working_days else None
    out = {}
    for d in days:
        wd = _dt.date.fromisoformat(d).weekday()
        if (work is not None and wd not in work) or any(c['from'] <= d <= c['to'] for c in closures):
            out[d] = 'off'; continue
        am = local_to_utc(d, rules['am'][0], tz), local_to_utc(d, rules['am'][1], tz)
        pm = local_to_utc(d, rules['pm'][0], tz), local_to_utc(d, rules['pm'][1], tz)
        full = local_to_utc(d, '00:00', tz), local_to_utc(d, '24:00', tz)
        busy_am = any(overlaps(b['starts_at'], b['ends_at'], *am) for b in blocks)
        busy_pm = any(overlaps(b['starts_at'], b['ends_at'], *pm) for b in blocks)
        busy_any = any(overlaps(b['starts_at'], b['ends_at'], *full) for b in blocks)
        if unit != 'half_day':
            state = 'busy' if busy_any else 'free'
        else:
            state = 'busy' if (busy_am and busy_pm) else ('am' if busy_am else ('pm' if busy_pm else 'free'))
        # Too soon (or past): the start of what is still free must be after the lead time
        start_free = am[0] if state in ('free', 'pm') else pm[0]
        if state != 'busy' and (full[1] <= now.strftime('%Y-%m-%dT%H:%M:%SZ') or start_free < earliest):
            state = 'off'
        out[d] = state
    return out


def normalize_selection(raw_days, date_from=None, date_to=None) -> list[str]:
    days = []
    if raw_days:
        for d in list(raw_days)[:92]:
            s = str(d)[:10]
            if re.fullmatch(r'\d{4}-\d{2}-\d{2}', s):
                try: _dt.date.fromisoformat(s); days.append(s)
                except ValueError: pass
    elif date_from:
        try:
            a = _dt.date.fromisoformat(str(date_from)[:10]); b = _dt.date.fromisoformat(str(date_to or date_from)[:10])
        except ValueError:
            return []
        if b < a or (b - a).days > 91: return []
        days = [(a + _dt.timedelta(days=i)).isoformat() for i in range((b - a).days + 1)]
    return sorted(set(days))


def check_selection(days: list[str], part: str, unit: str, rules: dict, states: dict[str, str]) -> str | None:
    """None when the selection can be booked, else the reason in plain words (shown to the diver)."""
    if not days: return 'Elige al menos un día.'
    if part not in PARTS: return 'Elige día completo, mañana o tarde.'
    if part != 'full' and unit != 'half_day': return 'Este servicio se reserva por días completos.'
    if part != 'full' and len(days) != 1: return 'La media jornada se reserva de un día en un día.'
    if len(days) < rules['min_days'] and part == 'full': return f"Este servicio se reserva como mínimo {rules['min_days']} días."
    if len(days) > rules['max_days']: return f"Puedes reservar como máximo {rules['max_days']} días."
    if rules.get('continuous') and part == 'full':
        for a, b in zip(days, days[1:]):
            if (_dt.date.fromisoformat(b) - _dt.date.fromisoformat(a)).days != 1:
                return 'Elige días seguidos.'
    for d in days:
        s = states.get(d)
        ok = s == 'free' or (part == 'am' and s == 'pm') or (part == 'pm' and s == 'am')
        if not ok:
            day = _dt.date.fromisoformat(d)
            what = {'busy': 'está ocupado', 'off': 'no está disponible', 'am': 'tiene la mañana ocupada', 'pm': 'tiene la tarde ocupada'}.get(s, 'no está disponible')
            return f'El día {day.day}/{day.month} {what}. Elige otras fechas.'
    return None


def ranges(days: list[str]) -> list[tuple[str, str]]:
    """Consecutive runs of days: ['16','17','18','20'] → [('16','18'), ('20','20')]."""
    out = []
    for d in days:
        if out and (_dt.date.fromisoformat(d) - _dt.date.fromisoformat(out[-1][1])).days == 1: out[-1][1] = d
        else: out.append([d, d])
    return [tuple(x) for x in out]
