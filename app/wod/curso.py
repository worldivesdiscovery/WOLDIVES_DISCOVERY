"""v50.58 (revisión y usabilidad 15-16/10/2026, punto 3.5): the progress of a course in each booking.

A course edition has its sessions (the mornings and afternoons of its plan, wod/servicios.plan_items); some of them
are dives. Each student of a booking (each seat) has a state for each session:

    pending ⏳ · done ✔ · moved ↪ (to an existing departure or to a new session, with its date) · cancelled ✖ ·
    pending_new_date ⏳ (its departure was cancelled for the weather: the centre places it again)

Pure helpers: the sessions with their dates, the summary («3 de 4 inmersiones hechas · 1 pendiente») and whether a
student has finished. The database work is in server.py (course_*)."""
from __future__ import annotations

import datetime as _dt

from . import servicios as wsv

STATES = ('pending', 'done', 'moved', 'cancelled', 'pending_new_date')
LABELS = {'pending': 'Pendiente', 'done': 'Hecha', 'moved': 'Aplazada', 'cancelled': 'Cancelada', 'pending_new_date': 'Pendiente de nueva fecha'}
ICONS = {'pending': '⏳', 'done': '✔', 'moved': '↪', 'cancelled': '✖', 'pending_new_date': '⏳'}
OPEN = ('pending', 'moved', 'pending_new_date')        # still to be done
PENDING_DAYS = 30                                        # a session pending for longer: a notice in the centre's panel
MOVE_MODES = ('join', 'new')


def sessions(plan: dict, start: str) -> list[dict]:
    """The sessions of an edition that starts on `start`, with their date, hours and name: «Inmersión 4» for a dive,
    «Día 2 · mañana» (or the centre's own name) for the rest."""
    d0 = _dt.date.fromisoformat(start)
    out, n = [], 0
    for it in wsv.plan_items(plan):
        if it['dive']: n += 1
        own = (plan.get('labels') or {}).get(str(it['seq']))
        out.append({'seq': it['seq'], 'day': it['day'], 'part': it['part'], 'date': (d0 + _dt.timedelta(days=it['day'])).isoformat(),
                    'start': it['start'], 'end': it['end'], 'dive': bool(it['dive']), 'dive_no': n if it['dive'] else None,
                    'label': own or (f'Inmersión {n}' if it['dive'] else it['label'])})
    return out


def summary(items: list[dict], states: dict) -> dict:
    """{done, total, pending, word, text} of one student: over the dives if the course has any, else over all the
    sessions. A cancelled session does not count."""
    pool = [s for s in items if s['dive']] or items
    word = 'inmersiones' if any(s['dive'] for s in items) else 'sesiones'
    live = [s for s in pool if states.get(s['seq'], 'pending') != 'cancelled']
    done = sum(1 for s in live if states.get(s['seq'], 'pending') == 'done')
    pending = len(live) - done
    text = f'{done} de {len(live)} {word} hechas' + (f' · {pending} pendiente' + ('s' if pending != 1 else '') if pending else '')
    return {'done': done, 'total': len(live), 'pending': pending, 'word': word, 'text': text}


def finished(items: list[dict], states: dict) -> bool:
    """A student finishes the course when every session is done (a session the centre cancelled does not count)."""
    live = [s for s in items if states.get(s['seq'], 'pending') != 'cancelled']
    return bool(live) and all(states.get(s['seq']) == 'done' for s in live)


def session_label(course_title: str, item: dict) -> str:
    """«Sesión de curso – Open Water (inmersión 4)»: what the place in another departure is called."""
    lab = item['label']   # a dict or a row of the database
    what = lab[0].lower() + lab[1:] if lab else f"sesión {item['seq']}"
    return f'Sesión de curso – {course_title} ({what})'[:160]


def minutes_between(a: str, b: str) -> int:
    ha, ma = (int(x) for x in a.split(':')); hb, mb = (int(x) for x in b.split(':'))
    return max(30, (hb * 60 + mb) - (ha * 60 + ma))


def add_minutes(hhmm: str, minutes: int) -> str:
    h, m = (int(x) for x in hhmm.split(':')); t = min(23 * 60 + 59, h * 60 + m + minutes)
    return f'{t // 60:02d}:{t % 60:02d}'
