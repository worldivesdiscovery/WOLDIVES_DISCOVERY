"""Departure manifest (encargo 2, punto 1): level of each qualification and the automatic split of the divers of a
departure into groups (one guide each) and boats. Pure functions: the server gives the data and stores the result."""
from __future__ import annotations

# Level of a qualification from its name, 0 (no qualification / try dive) to 5 (instructor). Names come from the
# certifications table (PADI, SSI, CMAS, FEDAS…); unknown names count as an entry level so nobody is put with the
# most experienced divers by mistake.
LEVEL_WORDS = (
    (5, ('instructor', 'monitor', 'trainer', '3 estrellas instructor')),
    (4, ('divemaster', 'dive master', 'dive guide', 'guía', 'guide', 'cmas ***', '3*', '3 estrellas', 'assistant instructor')),
    (3, ('rescue', 'rescate', 'master scuba', 'stress', 'cmas **', '2*', '2 estrellas', 'deep', 'profundo', 'cave', 'cavern', 'tec', 'technical', 'trimix')),
    (2, ('advanced', 'avanzado', 'aowd', 'adventure', 'cmas *', '1*', '1 estrella', 'b1e', 'b2e', 'nitrox', 'especialidad', 'specialty')),
    (1, ('open water', 'aguas abiertas', 'owd', 'scuba diver', 'básico', 'basico', 'nivel 1')),
    (0, ('bautizo', 'try', 'discover', 'dsd', 'intro', 'sin titulación', 'sin titulacion')),
)
LEVEL_LABELS = {0: 'Sin titulación', 1: 'Inicial', 2: 'Avanzado', 3: 'Rescate', 4: 'Profesional', 5: 'Instructor'}


def level_of(cert_name: str | None) -> int:
    name = (cert_name or '').lower()
    if not name: return 1
    for level, words in LEVEL_WORDS:
        if any(w in name for w in words): return level
    return 1


def band(level: int) -> int:
    """Groups are not mixed between beginners (0–1) and experienced divers (2+)."""
    return 0 if level <= 1 else 1


def suggest(bookings: list[dict], max_per_guide: int, boats: list[dict], guides: list[dict]) -> list[dict]:
    """bookings: [{'id', 'seats': [1..n], 'level'}]; boats: [{'id', 'capacity'}]; guides: [{'user_id', 'name'}].
    Returns groups: [{'boat_id', 'guide_user_id', 'guide_name', 'members': [(booking_id, seat)…]}].
    The seats of one booking stay together unless the booking alone is larger than a group; beginners and experienced
    divers go in different groups; each group has at most max_per_guide divers; groups go to the boats in order while
    they fit (divers plus the guide), the rest without a boat."""
    size = max(1, int(max_per_guide or 1))
    order = sorted(bookings, key=lambda b: (band(b['level']), b['level'], -len(b['seats']), b['id']))
    groups: list[dict] = []
    for b in order:
        seats = list(b['seats'])
        # First group of the same band with room for the whole booking; a booking larger than a group is split.
        fit = next((g for g in groups if g['band'] == band(b['level']) and size - len(g['members']) >= len(seats)), None) if len(seats) <= size else None
        if fit:
            fit['members'] += [(b['id'], s) for s in seats]; continue
        while seats:
            g = {'band': band(b['level']), 'members': []}; groups.append(g)
            take, seats = seats[:size], seats[size:]
            g['members'] += [(b['id'], s) for s in take]
    # Boats and guides
    load = {bt['id']: 0 for bt in boats}
    for i, g in enumerate(groups):
        guide = guides[i] if i < len(guides) else None
        g['guide_user_id'] = guide.get('user_id') if guide else None
        g['guide_name'] = guide.get('name') if guide else None
        need = len(g['members']) + (1 if guide else 0)
        g['boat_id'] = None
        for bt in boats:
            if load[bt['id']] + need <= int(bt['capacity'] or 0):
                g['boat_id'] = bt['id']; load[bt['id']] += need; break
        g.pop('band', None)
    return groups


def warnings(groups: list[dict], boats: list[dict], max_per_guide: int, unassigned: int) -> list[dict]:
    """groups: [{'id', 'label', 'boat_id', 'guide', 'count'}]. Each warning: {'kind', 'text', 'ref'} (Spanish; the web translates)."""
    out = []
    size = max(1, int(max_per_guide or 1))
    cap = {b['id']: b for b in boats}
    on_boat: dict = {}
    for g in groups:
        if g['count'] > size:
            out.append({'kind': 'over_guide', 'ref': g['id'], 'text': f"{g['label']}: {g['count']} buceadores con un guía (máximo {size})."})
        if g['count'] and not g['guide']:
            out.append({'kind': 'no_guide', 'ref': g['id'], 'text': f"{g['label']}: sin guía asignado."})
        if g['boat_id'] in cap:
            on_boat[g['boat_id']] = on_boat.get(g['boat_id'], 0) + g['count'] + (1 if g['guide'] else 0)
    for bid, n in on_boat.items():
        if n > int(cap[bid]['capacity'] or 0):
            out.append({'kind': 'over_boat', 'ref': bid, 'text': f"{cap[bid]['name']}: {n} personas a bordo (capacidad {cap[bid]['capacity']})."})
    if unassigned:
        out.append({'kind': 'unassigned', 'ref': None, 'text': f"{unassigned} {'buceador sin grupo' if unassigned == 1 else 'buceadores sin grupo'}."})
    return out
