"""v50.56 · Calendarios iCal (RFC 5545), sin base de datos: escribir el calendario privado de un centro, de un freelance o
de un instructor, y leer el calendario de otro sistema para bloquear plazas o días (Parte G).

Escribir: cada hora va en UTC («…Z»): cualquier calendario (Google, Apple, Outlook) la enseña en la hora de quien lo
mira, y un centro de México ve sus salidas a la hora de México. Las reservas de varios días son un evento de varios
días. Leer: DTSTART/DTEND con TZID, en UTC, flotantes (en la zona del centro) o de día entero."""
from __future__ import annotations

import datetime as _dt
import re
from zoneinfo import ZoneInfo

MAX_EVENTS = 500


def escape(text) -> str:
    return str(text or '').replace('\\', '\\\\').replace(';', '\\;').replace(',', '\\,').replace('\r\n', '\\n').replace('\n', '\\n')


def fold(lines: list[str]) -> str:
    """Lines of at most 75 octets (RFC 5545 §3.1), CRLF."""
    out = []
    for line in lines:
        b = line.encode('utf-8')
        while len(b) > 75:
            cut = 75
            while (b[cut] & 0xC0) == 0x80: cut -= 1
            out.append(b[:cut].decode('utf-8')); b = b' ' + b[cut:]
        out.append(b.decode('utf-8'))
    return '\r\n'.join(out) + '\r\n'


def utc_stamp(iso_utc: str) -> str:
    """'2031-07-04T07:00:00Z' → '20310704T070000Z'."""
    return re.sub(r'[-:]', '', iso_utc[:19]) + 'Z'


def date_stamp(iso_date: str) -> str:
    return iso_date[:10].replace('-', '')


# ------------------------------------------------------------------ reading
def _unfold(text: str) -> list[str]:
    lines = []
    for raw in re.split(r'\r\n|\n|\r', text):
        if raw[:1] in (' ', '\t') and lines: lines[-1] += raw[1:]
        elif raw: lines.append(raw)
    return lines


def _when(prop: str, value: str, default_tz: str):
    """(utc_iso, all_day, local_date) of a DTSTART/DTEND."""
    params = dict(p.split('=', 1) for p in prop.split(';')[1:] if '=' in p)
    v = value.strip()
    if params.get('VALUE') == 'DATE' or re.fullmatch(r'\d{8}', v):
        d = _dt.date(int(v[:4]), int(v[4:6]), int(v[6:8]))
        start = _dt.datetime(d.year, d.month, d.day, tzinfo=ZoneInfo(default_tz)).astimezone(_dt.timezone.utc)
        return start.strftime('%Y-%m-%dT%H:%M:%SZ'), True, d.isoformat()
    m = re.fullmatch(r'(\d{4})(\d{2})(\d{2})T(\d{2})(\d{2})(\d{2})?(Z?)', v)
    if not m: raise ValueError('fecha')
    y, mo, d, h, mi, s, z = m.groups()
    naive = _dt.datetime(int(y), int(mo), int(d), int(h), int(mi), int(s or 0))
    if z: aware = naive.replace(tzinfo=_dt.timezone.utc)
    else:
        tz = params.get('TZID', '').strip('"') or default_tz
        try: zone = ZoneInfo(tz)
        except Exception: zone = ZoneInfo(default_tz)
        aware = naive.replace(tzinfo=zone)
    loc = aware.astimezone(ZoneInfo(default_tz))
    return aware.astimezone(_dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ'), False, loc.date().isoformat()


def parse(text: str, default_tz: str, today: _dt.date | None = None, horizon_days: int = 400) -> list[dict]:
    """The events of a calendar that end after today and start within the horizon: uid, start/end (UTC), all_day,
    local dates, summary. Cancelled events are left out. At most MAX_EVENTS."""
    today = today or _dt.date.today()
    limit = (today + _dt.timedelta(days=horizon_days)).isoformat()
    events, cur = [], None
    for line in _unfold(text):
        if line == 'BEGIN:VEVENT': cur = {}; continue
        if line == 'END:VEVENT':
            if cur is not None and cur.get('start'): events.append(cur)
            cur = None; continue
        if cur is None or ':' not in line: continue
        prop, value = line.split(':', 1); name = prop.split(';')[0].upper()
        try:
            if name == 'DTSTART': cur['start'], cur['all_day'], cur['local_from'] = _when(prop, value, default_tz)
            elif name == 'DTEND': cur['end'], _, cur['local_to'] = _when(prop, value, default_tz); cur['end_all_day'] = 'VALUE=DATE' in prop or re.fullmatch(r'\d{8}', value.strip()) is not None
            elif name == 'UID': cur['uid'] = value.strip()[:200]
            elif name == 'SUMMARY': cur['summary'] = value.replace('\\,', ',').replace('\\;', ';').replace('\\n', ' ')[:200]
            elif name == 'STATUS': cur['status'] = value.strip().upper()
        except (ValueError, KeyError):
            cur['bad'] = True
    out = []
    for e in events:
        if e.get('bad') or e.get('status') == 'CANCELLED': continue
        if not e.get('end'):
            # No end: one day for a whole-day event, one hour otherwise (RFC 5545 §3.6.1)
            st = _dt.datetime.strptime(e['start'], '%Y-%m-%dT%H:%M:%SZ')
            e['end'] = (st + (_dt.timedelta(days=1) if e['all_day'] else _dt.timedelta(hours=1))).strftime('%Y-%m-%dT%H:%M:%SZ')
            e['local_to'] = e['local_from']
        elif e.get('all_day') and e.get('end_all_day'):
            # DTEND of a whole-day event is the day after the last one
            e['local_to'] = (_dt.date.fromisoformat(e['local_to']) - _dt.timedelta(days=1)).isoformat()
        if e['end'] <= e['start']: continue
        if e['local_to'] < today.isoformat() or e['local_from'] > limit: continue
        e['uid'] = e.get('uid') or f"sin-uid-{e['start']}"
        e['key'] = f"{e['uid']}@{e['start']}/{e['end']}"[:300]
        out.append({k: e.get(k) for k in ('uid', 'key', 'start', 'end', 'all_day', 'local_from', 'local_to', 'summary')})
        if len(out) >= MAX_EVENTS: break
    return out
