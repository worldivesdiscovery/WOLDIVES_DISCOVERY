"""Encargo del 17/10/2026 (Bloque 3) · Directorio de freelance y «Mis profesionales».

- Aparecen todos los freelance aprobados (plan gratuito o Pro, decisión del titular del 17/10) que tienen lo mínimo:
  foto, nombre, zona donde trabajan y al menos una titulación profesional, y que no han apagado «Aparecer en el
  directorio». Al que le falta algo, su panel le dice qué.
- La tarjeta lleva lo público (nunca la dirección, el teléfono ni el correo). El orden es igual para todos: cercanía y
  disponibilidad, o valoración; si el plan Pro tiene ventaja es «Pendiente de decisión».
- «Mis profesionales»: con una reserva confirmada, el profesional queda en la lista del buceador, que puede quitarlo.
  Los botones de contacto salen solo si el profesional los activó, el buceador reservó con él y no lo ha bloqueado.
Aquí no se toca la base de datos (lo hace app/server.py).
"""
from __future__ import annotations

import math
import re

SCHEMA = [
    '''CREATE TABLE IF NOT EXISTS freelance_profiles (user_id INTEGER PRIMARY KEY REFERENCES users(id) ON DELETE CASCADE,
         kind TEXT CHECK(kind IN ('instructor','guia')), zone TEXT, lat REAL, lon REAL, languages TEXT, in_directory INTEGER NOT NULL DEFAULT 1,
         contact_whatsapp INTEGER NOT NULL DEFAULT 0, contact_phone INTEGER NOT NULL DEFAULT 0, contact_email INTEGER NOT NULL DEFAULT 0,
         updated_at TEXT NOT NULL)''',
    '''CREATE TABLE IF NOT EXISTS pro_certifications (id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
         agency TEXT NOT NULL, level TEXT NOT NULL, number TEXT, verified INTEGER NOT NULL DEFAULT 0, verified_by INTEGER, verified_at TEXT,
         created_at TEXT NOT NULL)''',
    'CREATE INDEX IF NOT EXISTS idx_pro_certifications_user ON pro_certifications(user_id)',
    # «Mis profesionales»: the ones the diver removed from the list, and the divers a professional blocked
    '''CREATE TABLE IF NOT EXISTS my_pros_hidden (user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE, kind TEXT NOT NULL, ref_id INTEGER NOT NULL,
         created_at TEXT NOT NULL, PRIMARY KEY(user_id, kind, ref_id))''',
    '''CREATE TABLE IF NOT EXISTS pro_blocks (kind TEXT NOT NULL, ref_id INTEGER NOT NULL, user_id INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
         created_at TEXT NOT NULL, PRIMARY KEY(kind, ref_id, user_id))''',
]

KINDS = {'instructor': 'Instructor', 'guia': 'Guía'}
AGENCIES = ('PADI', 'SSI', 'CMAS', 'FEDAS', 'NAUI', 'SDI/TDI', 'RAID', 'GUE', 'BSAC', 'ACUC', 'IANTD', 'Otra')
LANGS = ('es', 'en', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'zh', 'ca', 'eu', 'gl', 'ru', 'sv', 'da', 'no', 'ja', 'ar')


def _txt(v, n):
    v = re.sub(r'\s+', ' ', str(v or '')).strip()[:n]
    if re.search(r'[<>]', v): raise ValueError('El texto tiene caracteres no permitidos.')
    return v


def clean_profile(data: dict) -> dict:
    kind = data.get('kind') if data.get('kind') in KINDS else None
    zone = _txt(data.get('zone'), 120)
    try:
        lat = float(data['lat']) if data.get('lat') not in (None, '') else None
        lon = float(data['lon']) if data.get('lon') not in (None, '') else None
    except (TypeError, ValueError):
        raise ValueError('Ubicación no válida.') from None
    if (lat is None) != (lon is None) or (lat is not None and not (-90 <= lat <= 90 and -180 <= lon <= 180)): raise ValueError('Ubicación no válida.')
    langs = [l for l in (data.get('languages') or []) if l in LANGS][:12]
    b = lambda k: 1 if data.get(k) in (1, True, '1', 'true') else 0
    return {'kind': kind, 'zone': zone or None, 'lat': lat, 'lon': lon, 'languages': ','.join(dict.fromkeys(langs)) or None,
            'in_directory': 0 if data.get('in_directory') in (0, False, '0', 'false') else 1,
            'contact_whatsapp': b('contact_whatsapp'), 'contact_phone': b('contact_phone'), 'contact_email': b('contact_email')}


def clean_cert(data: dict) -> tuple:
    agency = str(data.get('agency') or '')
    if agency not in AGENCIES: raise ValueError('Elige la agencia de la titulación.')
    level = _txt(data.get('level'), 80)
    if len(level) < 2: raise ValueError('Escribe la titulación (por ejemplo «Open Water Scuba Instructor»).')
    return agency, level, _txt(data.get('number'), 40) or None


def missing(user, profile, certs) -> list:
    """What a freelance still needs to appear in the directory (empty: nothing)."""
    out = []
    if not (user.get('avatar_url') or '').strip(): out.append('foto')
    if not (user.get('fullname') or '').strip(): out.append('nombre')
    if not (profile or {}).get('zone'): out.append('zona donde trabajas')
    if not certs: out.append('al menos una titulación profesional')
    return out


def km(a_lat, a_lon, b_lat, b_lon):
    if None in (a_lat, a_lon, b_lat, b_lon): return None
    r = math.radians
    d = math.sin(r(b_lat - a_lat) / 2) ** 2 + math.cos(r(a_lat)) * math.cos(r(b_lat)) * math.sin(r(b_lon - a_lon) / 2) ** 2
    return round(6371 * 2 * math.asin(min(1, math.sqrt(d))), 1)
