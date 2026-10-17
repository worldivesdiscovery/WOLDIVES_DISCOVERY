"""Encargo del 17/10/2026 (1.7) · Buddies: compañeros de buceo, no una red social.

- Añadir un Buddy con su QR o su enlace: a la otra persona le llega una petición que acepta o rechaza. Si las dos se han
  escaneado a la vez, la segunda petición acepta la primera.
- «¿Buceamos?»: un buceador propone a uno o varios Buddies una fecha y, si quiere, un punto. A cada uno le llega un aviso.
  Si acepta, se abre WhatsApp entre los dos para organizarse (el teléfono de cada uno solo lo ve el otro después de
  aceptar, y solo el que esa persona escribió en su perfil).
- Sin chat dentro de WORLDIVES, sin muro, sin publicaciones y sin seguidores.
"""
from __future__ import annotations

import re
import urllib.parse
from datetime import date

SCHEMA = [
    '''CREATE TABLE IF NOT EXISTS buddy_requests (id INTEGER PRIMARY KEY AUTOINCREMENT, from_user INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
         to_user INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, status TEXT NOT NULL DEFAULT 'pending'
         CHECK(status IN ('pending','accepted','rejected','cancelled')), created_at TEXT NOT NULL, responded_at TEXT)''',
    'CREATE INDEX IF NOT EXISTS idx_buddy_requests_to ON buddy_requests(to_user, status)',
    'CREATE INDEX IF NOT EXISTS idx_buddy_requests_from ON buddy_requests(from_user, status)',
    '''CREATE TABLE IF NOT EXISTS dive_invites (id INTEGER PRIMARY KEY AUTOINCREMENT, from_user INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
         to_user INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, dive_date TEXT NOT NULL, point_id INTEGER, note TEXT,
         status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','accepted','rejected','cancelled')), created_at TEXT NOT NULL, responded_at TEXT)''',
    'CREATE INDEX IF NOT EXISTS idx_dive_invites_to ON dive_invites(to_user, status)',
    'CREATE INDEX IF NOT EXISTS idx_dive_invites_from ON dive_invites(from_user, status)',
]

MAX_INVITE_BUDDIES = 10
MAX_PENDING_REQUESTS = 30


def are_buddies(db, a, b):
    return bool(db.execute('SELECT 1 FROM user_buddies WHERE user_id=? AND buddy_id=?', (a, b)).fetchone())


def link(db, a, b, now):
    for x, y in ((a, b), (b, a)): db.execute('INSERT OR IGNORE INTO user_buddies(user_id,buddy_id,created_at) VALUES(?,?,?)', (x, y, now))


def request(db, from_user, to_user, now):
    """'already' (they were buddies), 'accepted' (the other one had asked first: both are buddies now), 'pending'
    (a new request, or the one that was already waiting)."""
    if from_user == to_user: raise ValueError('Este es tu propio QR: enséñaselo a tu compañero para que lo escanee él.')
    if are_buddies(db, from_user, to_user): return 'already', None
    back = db.execute("SELECT id FROM buddy_requests WHERE from_user=? AND to_user=? AND status='pending'", (to_user, from_user)).fetchone()
    if back:
        db.execute("UPDATE buddy_requests SET status='accepted', responded_at=? WHERE id=?", (now, back['id']))
        link(db, from_user, to_user, now); return 'accepted', back['id']
    mine = db.execute("SELECT id FROM buddy_requests WHERE from_user=? AND to_user=? AND status='pending'", (from_user, to_user)).fetchone()
    if mine: return 'pending', mine['id']
    if db.execute("SELECT COUNT(*) FROM buddy_requests WHERE from_user=? AND status='pending'", (from_user,)).fetchone()[0] >= MAX_PENDING_REQUESTS:
        raise ValueError('Tienes muchas peticiones sin contestar. Espera a que te respondan.')
    rid = db.execute('INSERT INTO buddy_requests(from_user,to_user,status,created_at) VALUES(?,?,?,?)', (from_user, to_user, 'pending', now)).lastrowid
    return 'pending', rid


def answer_request(db, uid, rid, accept, now):
    r = db.execute("SELECT * FROM buddy_requests WHERE id=? AND to_user=? AND status='pending'", (rid, uid)).fetchone()
    if not r: raise LookupError('Esa petición ya no está pendiente.')
    db.execute('UPDATE buddy_requests SET status=?, responded_at=? WHERE id=?', ('accepted' if accept else 'rejected', now, rid))
    if accept: link(db, r['from_user'], uid, now)
    return r


def remove(db, uid, other):
    db.execute('DELETE FROM user_buddies WHERE (user_id=? AND buddy_id=?) OR (user_id=? AND buddy_id=?)', (uid, other, other, uid))
    db.execute("UPDATE dive_invites SET status='cancelled' WHERE status='pending' AND ((from_user=? AND to_user=?) OR (from_user=? AND to_user=?))",
               (uid, other, other, uid))


def clean_invite(data, today):
    try: d = date.fromisoformat(str(data.get('date') or '')[:10])
    except ValueError: raise ValueError('Elige la fecha.')
    if d < today: raise ValueError('La fecha ya ha pasado.')
    if (d - today).days > 365: raise ValueError('Elige una fecha dentro del próximo año.')
    note = re.sub(r'\s+', ' ', str(data.get('note') or '')).strip()[:200] or None
    if note and re.search(r'[<>]', note): raise ValueError('La nota tiene caracteres no permitidos.')
    try: point = int(data.get('point_id') or 0) or None
    except (TypeError, ValueError): point = None
    return d.isoformat(), point, note


def whatsapp_url(phone, text):
    """wa.me with the international number (only digits) and the first message written; None without a phone."""
    digits = re.sub(r'\D', '', str(phone or ''))
    if len(digits) < 8: return None
    return f'https://wa.me/{digits}?text={urllib.parse.quote(text)}'
