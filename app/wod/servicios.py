"""Services in the words of a diver (revisión y usabilidad 15-16/10/2026, Parte 3 · v50.58): pure helpers, no database.

What a centre or a freelance sells is chosen by its *kind* (an immersion, a course, a rental…) and only the fields that
make sense for that kind are asked for. The technical «unidad de reserva» is no longer on the screen: it follows from
the kind (a guide by days is booked by days or half days; everything else by departures or editions).

A *course* has a plan of days: each day is a full day, a morning or an afternoon. An *edition* of the course is one
start date: its end follows from the plan («Open Water del lunes 3 al miércoles 5 de junio»). Each edition keeps its
places and its instructor. The *sessions* of a course are its mornings and afternoons (a full day is a morning and an
afternoon): that is what the centre marks as done or moves to another day for one student (point 3.5).

Everything here is deterministic and tested on its own (tests/test_v50_58_servicios.py).
"""
from __future__ import annotations

import datetime as _dt
import json
import re

KINDS = ('dive', 'baptism', 'course', 'rental', 'guide', 'trip', 'other')
KIND_LABELS = {'dive': 'Inmersión o salida en barco', 'baptism': 'Bautizo', 'course': 'Curso', 'rental': 'Alquiler de equipo',
               'guide': 'Guía o instructor por días', 'trip': 'Viaje o experiencia', 'other': 'Otro'}
# The service_type each kind is saved with (the catalogue, the filters and the icons of the web already know them).
KIND_TYPE = {'dive': 'inmersion', 'baptism': 'experiencia', 'course': 'curso', 'rental': 'alquiler_equipo', 'guide': 'inmersion',
             'trip': 'viaje', 'other': 'experiencia'}
KIND_ICON = {'dive': 'inmersion', 'baptism': 'bautizo', 'course': 'curso', 'rental': 'alquiler_equipo', 'guide': 'salida_privada',
             'trip': 'viaje', 'other': 'extra'}
# «⚡ Reserva inmediata» is recommended where the dates are fixed; «✋ Tú apruebas cada reserva» where it is made to measure.
KIND_MODE = {'dive': 'payment', 'baptism': 'payment', 'rental': 'payment', 'course': 'request', 'guide': 'request', 'trip': 'request',
             'other': 'request'}
PARTS = ('full', 'am', 'pm')
PART_LABELS = {'full': 'Día completo', 'am': 'Mañana', 'pm': 'Tarde'}
DEFAULT_HOURS = {'am': ['09:00', '13:00'], 'pm': ['15:00', '19:00'], 'full': ['09:00', '18:00']}
PRESETS = {'3full': ['full', 'full', 'full'], '4am': ['am', 'am', 'am', 'am'], '2am2full': ['am', 'am', 'full', 'full']}
INCLUDES = {'equipo': 'Equipo', 'barco': 'Barco', 'seguro': 'Seguro', 'fotos': 'Fotos', 'titulacion': 'Titulación', 'guia': 'Guía',
            'transporte': 'Transporte', 'comida': 'Comida', 'nitrox': 'Nitrox'}
LANGS = ('es', 'en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh', 'ca')
HHMM = re.compile(r'^([01]\d|2[0-3]):[0-5]\d$')
MAX_COURSE_DAYS = 10
MAX_EDITIONS = 60


def as_json(raw, default):
    if isinstance(raw, (dict, list)): return raw
    if isinstance(raw, str) and raw.strip()[:1] in ('{', '['):
        try: return json.loads(raw)
        except ValueError: return default
    return default


def kind_of(svc) -> str:
    """The kind of a saved service. Services made before v50.58 have none: it follows from what they were."""
    def get(k):
        try: return svc[k]
        except (KeyError, IndexError, TypeError): return None
    k = get('kind')
    if k in KINDS: return k
    stype = get('service_type') or ''; unit = get('booking_unit') or 'slot'; title = (get('title') or '').lower()
    if unit in ('day', 'half_day'): return 'guide'
    if stype == 'curso': return 'course'
    if stype == 'alquiler_equipo': return 'rental'
    if stype in ('viaje', 'vida_a_bordo'): return 'trip'
    if 'bautiz' in title or 'try dive' in title or 'discover' in title: return 'baptism'
    if stype == 'experiencia': return 'other'
    return 'dive'


# ------------------------------------------------------------------------------------------------- course plan
def _hours(raw):
    out = {k: list(v) for k, v in DEFAULT_HOURS.items()}
    if isinstance(raw, dict):
        for k in PARTS:
            v = raw.get(k)
            if isinstance(v, (list, tuple)) and len(v) == 2 and all(isinstance(x, str) and HHMM.match(x) for x in v) and v[0] < v[1]:
                out[k] = [v[0], v[1]]
    if out['am'][1] > out['pm'][0]:   # a morning that ends after the afternoon starts: the usual hours
        out['am'], out['pm'] = list(DEFAULT_HOURS['am']), list(DEFAULT_HOURS['pm'])
    return out


def clean_plan(raw, fallback_days=None) -> dict:
    """{days: ['full'|'am'|'pm', …], hours: {am, pm, full}, labels: {seq: text}, dives: [seq, …]} from the form."""
    p = as_json(raw, {}) if not isinstance(raw, dict) else raw
    days = [d for d in (p.get('days') or []) if d in PARTS][:MAX_COURSE_DAYS] if isinstance(p, dict) else []
    if not days and isinstance(p, dict) and p.get('preset') in PRESETS: days = list(PRESETS[p['preset']])
    if not days and fallback_days: days = ['full'] * max(1, min(MAX_COURSE_DAYS, int(fallback_days)))
    labels = {}
    for k, v in ((p.get('labels') or {}).items() if isinstance(p, dict) and isinstance(p.get('labels'), dict) else []):
        if str(k).isdigit():
            t = re.sub(r'\s+', ' ', str(v or ''))[:60].strip()
            if t: labels[str(int(k))] = t
    dives = sorted({int(x) for x in ((p.get('dives') or []) if isinstance(p, dict) else []) if str(x).isdigit()})[:40]
    return {'days': days, 'hours': _hours(p.get('hours') if isinstance(p, dict) else None), 'labels': labels, 'dives': dives}


def plan_from_legacy(title, duration_minutes) -> dict:
    """A course saved before v50.58 (only minutes): «Curso Open Water (3 días)» or 4320 minutes → 3 full days."""
    m = re.search(r'(\d{1,2})\s*d[ií]as?', title or '', re.I)
    n = int(m.group(1)) if m else (round((duration_minutes or 0) / 1440) if (duration_minutes or 0) >= 1440 else 1)
    return clean_plan({'days': ['full'] * max(1, min(MAX_COURSE_DAYS, n))})


def plan_items(plan: dict) -> list[dict]:
    """The sessions of a course: its mornings and afternoons, in order. A full day is a morning and an afternoon, so the
    afternoon dive of the last day can be moved on its own («la inmersión de la tarde del último día»)."""
    out, seq = [], 0
    for i, part in enumerate(plan.get('days') or []):
        for p in (('am', 'pm') if part == 'full' else (part,)):
            seq += 1
            hours = plan['hours'][p]
            default = f"Día {i + 1} · {'mañana' if p == 'am' else 'tarde'}"
            out.append({'seq': seq, 'day': i, 'part': p, 'day_part': part, 'start': hours[0], 'end': hours[1],
                        'label': plan.get('labels', {}).get(str(seq)) or default, 'dive': seq in (plan.get('dives') or [])})
    return out


def plan_summary(plan: dict) -> str:
    """«3 días completos», «4 mañanas», «2 mañanas + 2 días completos», «1 día completo + 1 tarde»."""
    days = plan.get('days') or []
    if not days: return ''
    names = {'full': ('día completo', 'días completos'), 'am': ('mañana', 'mañanas'), 'pm': ('tarde', 'tardes')}
    order, counts = [], {}
    for d in days:
        if d not in counts: order.append(d); counts[d] = 0
        counts[d] += 1
    return ' + '.join(f"{counts[d]} {names[d][0] if counts[d] == 1 else names[d][1]}" for d in order)


def edition_days(start: str, plan: dict) -> list[str]:
    """The calendar days of an edition that starts on `start`: one per day of the plan, in a row."""
    d0 = _dt.date.fromisoformat(start)
    return [(d0 + _dt.timedelta(days=i)).isoformat() for i in range(max(1, len(plan.get('days') or [])))]


def edition_end(start: str, plan: dict) -> str:
    return edition_days(start, plan)[-1]


def edition_sessions(start: str, plan: dict) -> list[dict]:
    """Each session of an edition with its date: what the planning, the instructor's agenda and the students' progress use."""
    days = edition_days(start, plan)
    return [{**it, 'date': days[it['day']]} for it in plan_items(plan)]


def edition_spans(start: str, plan: dict) -> list[tuple[str, str, str]]:
    """(date, from, to) the instructor is busy: a full day from the start of its morning to the end of its afternoon."""
    out = []
    days = edition_days(start, plan)
    for i, part in enumerate(plan.get('days') or []):
        h = plan['hours']
        a, b = (h['am'][0], h['pm'][1]) if part == 'full' else tuple(h[part])
        out.append((days[i], a, b))
    return out


# ------------------------------------------------------------------------------------------------- dates of the schedule
def weekly_dates(weekdays, date_from: str, date_to: str, limit=MAX_EDITIONS) -> list[str]:
    """«Todos los sábados» or «todos los lunes de junio»: the dates between two days that fall on those weekdays (0 = lunes)."""
    try:
        a = _dt.date.fromisoformat(str(date_from)[:10]); b = _dt.date.fromisoformat(str(date_to)[:10])
    except ValueError:
        return []
    wds = {int(x) for x in (weekdays or []) if str(x).isdigit() and 0 <= int(x) <= 6}
    if not wds or b < a or (b - a).days > 400: return []
    out, d = [], a
    while d <= b and len(out) < limit:
        if d.weekday() in wds: out.append(d.isoformat())
        d += _dt.timedelta(days=1)
    return out


def clean_dates(raw, today: str, limit=MAX_EDITIONS) -> list[str]:
    out = []
    for x in (raw or [])[:limit * 2]:
        s = str(x)[:10]
        try:
            if _dt.date.fromisoformat(s).isoformat() >= today and s not in out: out.append(s)
        except ValueError:
            continue
    return sorted(out)[:limit]


def nights(date_from: str, date_to: str) -> int:
    try: return max(0, (_dt.date.fromisoformat(date_to) - _dt.date.fromisoformat(date_from)).days)
    except ValueError: return 0


# ------------------------------------------------------------------------------------------------- the wizard's form
def _int(v, lo, hi):
    try:
        x = int(str(v).strip())
    except (TypeError, ValueError):
        return None
    return x if lo <= x <= hi else None


def _money(v):
    try:
        x = round(float(str(v).replace(',', '.').strip()), 2)
    except (TypeError, ValueError):
        return None
    return x if 0 <= x <= 1_000_000 else None


def _text(v, n):
    return re.sub(r'[ \t]+', ' ', str(v or '')).strip()[:n]


def check_form(data: dict, role: str, publish: bool, today: str) -> tuple[dict, dict]:
    """The wizard's answers, cleaned, and the errors next to each field in plain words («Pon cuántos días dura el
    curso», never «campo inválido»). A draft is saved with what there is; publishing asks for everything."""
    e, out = {}, {}
    kind = data.get('kind') if data.get('kind') in KINDS else None
    if not kind: e['kind'] = 'Elige qué vas a ofrecer.'
    kind = kind or 'dive'
    if kind == 'guide' and role != 'freelance': e['kind'] = 'Las reservas por días son para guías e instructores freelance.'
    out['kind'] = kind
    out['title'] = _text(data.get('title'), 180)
    if not out['title']: e['title'] = 'Pon un nombre al servicio. Por ejemplo: «Doble inmersión en Islas Medas».'
    out['description'] = _text(data.get('description'), 5000)
    out['icon'] = data.get('icon') if isinstance(data.get('icon'), str) and re.fullmatch(r'[a-z_]{2,30}', data.get('icon')) else KIND_ICON[kind]
    out['includes'] = [x for x in (data.get('includes') or []) if x in INCLUDES][:len(INCLUDES)]
    out['level_required'] = _text(data.get('level_required'), 120)
    out['min_age'] = _int(data.get('min_age'), 0, 99) if data.get('min_age') not in (None, '') else None
    if data.get('min_age') not in (None, '') and out['min_age'] is None: e['min_age'] = 'Pon la edad mínima en años (por ejemplo, 10).'
    out['languages'] = [x for x in (data.get('languages') or []) if x in LANGS][:len(LANGS)]
    out['meeting_point'] = _text(data.get('meeting_point'), 200)
    # ---- when and how long
    if kind in ('dive', 'baptism', 'other'):
        h = _int(data.get('hours') or 0, 0, 23); m = _int(data.get('minutes') or 0, 0, 59)
        mins = (h or 0) * 60 + (m or 0)
        if publish and not mins: e['duration'] = 'Pon cuánto dura: horas y minutos (por ejemplo, 3 h 30 min).'
        out['duration_minutes'] = mins or None
        t = str(data.get('start_time') or '')
        out['start_time'] = t if HHMM.match(t) else None
        if publish and not out['start_time']: e['start_time'] = 'Pon la hora de salida (por ejemplo, 09:00).'
    elif kind == 'course':
        plan = clean_plan(data.get('plan'))
        if not plan['days']: e['plan'] = 'Pon cuántos días dura el curso.' if publish else None
        out['plan'] = plan
        out['duration_minutes'] = len(plan['days']) * 1440 if plan['days'] else None
        out['start_time'] = plan['hours']['full' if plan['days'][:1] == ['full'] else (plan['days'][0] if plan['days'] else 'am')][0]
    elif kind == 'guide':
        out['half_days'] = bool(data.get('half_days'))
        out['duration_minutes'] = None
    elif kind == 'rental':
        out['rental_per'] = 'dive' if data.get('rental_per') == 'dive' else 'day'
        out['duration_minutes'] = None
    elif kind == 'trip':
        a, b = str(data.get('trip_from') or '')[:10], str(data.get('trip_to') or '')[:10]
        try: ok = bool(a and b and _dt.date.fromisoformat(a) <= _dt.date.fromisoformat(b))
        except ValueError: ok = False
        if publish and not ok: e['trip_dates'] = 'Pon la fecha de inicio y la de fin del viaje.'
        elif ok and a < today and publish: e['trip_dates'] = 'La fecha de inicio ya ha pasado.'
        out['trip_from'], out['trip_to'] = (a, b) if ok else (None, None)
        out['duration_minutes'] = (nights(a, b) + 1) * 1440 if ok else None
    # ---- price and places
    out['price_per'] = 'group' if data.get('price_per') == 'group' else 'person'
    out['price'] = _money(data.get('price'))
    if publish and (out['price'] is None or out['price'] <= 0): e['price'] = 'Pon el precio: es obligatorio y se publica tal cual.'
    if kind == 'guide':
        out['half_price'] = _money(data.get('half_price')) if out.get('half_days') and data.get('half_price') not in (None, '') else None
    seats = _int(data.get('max_participants'), 1, 999) if data.get('max_participants') not in (None, '') else None
    if publish and kind not in ('rental',) and not seats: e['max_participants'] = 'Pon cuántas plazas hay por salida (por ejemplo, 8).' if kind != 'course' else 'Pon cuántas plazas tiene cada edición del curso.'
    out['max_participants'] = seats
    out['extra_ids'] = sorted({int(x) for x in (data.get('extra_ids') or []) if str(x).isdigit()})[:30] if isinstance(data.get('extra_ids'), list) else None
    # ---- how it is booked (the two modes of Fase 1B, only presented differently)
    mode = data.get('booking_mode')
    out['booking_mode'] = mode if mode in ('payment', 'request') else KIND_MODE[kind]
    if kind == 'guide' and out['booking_mode'] == 'payment' and data.get('pay_way') == 'in_person': out['booking_mode'] = 'request'
    rh = data.get('response_hours')
    out['response_hours'] = _int(rh, 1, 168) if rh not in (None, '') else None
    if rh not in (None, '') and out['response_hours'] is None: e['response_hours'] = 'El plazo para responder va de 1 a 168 horas.'
    out['lead_hours'] = _int(data.get('lead_hours'), 0, 24 * 30) if data.get('lead_hours') not in (None, '') else None
    out['tags'] = _text(data.get('tags'), 200)
    return out, {k: v for k, v in e.items() if v}


def schedule_dates(data: dict, kind: str, today: str) -> tuple[list[str], str | None]:
    """The dates the wizard creates when publishing: departures of an immersion («todos los sábados a las 9:00» or loose
    dates) or editions of a course («todos los lunes de junio» or loose dates). Returns (dates, error)."""
    s = data.get('schedule') if isinstance(data.get('schedule'), dict) else {}
    if s.get('mode') == 'weekly':
        dates = [d for d in weekly_dates(s.get('weekdays'), max(str(s.get('from') or today)[:10], today), str(s.get('to') or '')[:10]) if d >= today]
        if not dates: return [], ('Elige los días de la semana y hasta cuándo.' if kind != 'course' else 'Elige el día de la semana de inicio y hasta cuándo.')
        return dates, None
    dates = clean_dates(s.get('dates'), today)
    return dates, None
