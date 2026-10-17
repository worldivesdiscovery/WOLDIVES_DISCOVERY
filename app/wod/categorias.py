"""Encargo del 17/10/2026 (1.5) · Las actividades de un centro, ordenadas por categorías al reservar.

Primero la categoría (Inmersiones, Cursos, Bautizos, Tours y experiencias, Otros) y después solo sus servicios. Cada
servicio tiene su categoría: sale sola del tipo elegido en el asistente de servicios, y el centro puede cambiarla. Los
servicios de antes que no dejan clara su categoría quedan marcados para que el centro los revise. Las categorías (nombre
en los 9 idiomas, icono y orden) se configuran en Administración.
"""
from __future__ import annotations

import json
import re

SCHEMA = [
    '''CREATE TABLE IF NOT EXISTS booking_categories (key TEXT PRIMARY KEY, label TEXT NOT NULL, icon TEXT NOT NULL,
         sort_order INTEGER NOT NULL DEFAULT 0, active INTEGER NOT NULL DEFAULT 1, labels_i18n TEXT, updated_at TEXT)''',
]
DEFAULTS = [('inmersiones', 'Inmersiones', 'inmersion', 10), ('cursos', 'Cursos', 'curso', 20), ('bautizos', 'Bautizos', 'bautizo', 30),
            ('tours', 'Tours y experiencias', 'viaje', 40), ('otros', 'Otros', 'extra', 50)]
# the kind of the services wizard (wod.servicios.KINDS) → its category
KIND_CATEGORY = {'dive': 'inmersiones', 'guide': 'inmersiones', 'course': 'cursos', 'baptism': 'bautizos', 'trip': 'tours',
                 'rental': 'otros', 'other': 'otros'}
ICONS = ('inmersion', 'curso', 'bautizo', 'viaje', 'extra', 'snorkel', 'nocturna', 'fotografia', 'vida_a_bordo', 'salida_privada', 'alquiler_equipo')
LANGS = ('en', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'zh')
# the names of the categories of the start in the other 8 languages (Administración can change them)
DEFAULT_I18N = {
    'inmersiones': {'en': 'Dives', 'fr': 'Plongées', 'de': 'Tauchgänge', 'it': 'Immersioni', 'pt': 'Mergulhos', 'nl': 'Duiken', 'pl': 'Nurkowania', 'zh': '潜水'},
    'cursos': {'en': 'Courses', 'fr': 'Formations', 'de': 'Kurse', 'it': 'Corsi', 'pt': 'Cursos', 'nl': 'Cursussen', 'pl': 'Kursy', 'zh': '课程'},
    'bautizos': {'en': 'Try dives', 'fr': 'Baptêmes', 'de': 'Schnuppertauchen', 'it': 'Battesimi', 'pt': 'Batismos', 'nl': 'Proefduiken', 'pl': 'Nurkowania próbne', 'zh': '体验潜水'},
    'tours': {'en': 'Tours and experiences', 'fr': 'Excursions et expériences', 'de': 'Touren und Erlebnisse', 'it': 'Tour ed esperienze', 'pt': 'Passeios e experiências',
              'nl': 'Tours en belevenissen', 'pl': 'Wycieczki i przeżycia', 'zh': '旅行与体验'},
    'otros': {'en': 'Other', 'fr': 'Autres', 'de': 'Sonstiges', 'it': 'Altro', 'pt': 'Outros', 'nl': 'Overig', 'pl': 'Inne', 'zh': '其他'},
}


def seed(db, now):
    for key, label, icon, order in DEFAULTS:
        db.execute('INSERT OR IGNORE INTO booking_categories(key,label,icon,sort_order,labels_i18n,updated_at) VALUES(?,?,?,?,?,?)',
                   (key, label, icon, order, json.dumps(DEFAULT_I18N[key], ensure_ascii=False), now))
        # created before the translations of the start: they are added only where the row has none yet
        db.execute("UPDATE booking_categories SET labels_i18n=? WHERE key=? AND (labels_i18n IS NULL OR labels_i18n IN ('','{}'))",
                   (json.dumps(DEFAULT_I18N[key], ensure_ascii=False), key))


def rows(db, include_hidden=False):
    return [dict(r) for r in db.execute(f"SELECT * FROM booking_categories {'' if include_hidden else 'WHERE active=1'} ORDER BY sort_order, key").fetchall()]


def public_list(db, lang):
    """[{key, label, icon}] in the person's language; Spanish when a translation is missing."""
    out = []
    for r in rows(db):
        try: tr = json.loads(r['labels_i18n'] or '{}')
        except ValueError: tr = {}
        out.append({'key': r['key'], 'label': (tr.get(lang) or '').strip() or r['label'], 'icon': r['icon'], 'missing': [l for l in LANGS if not (tr.get(l) or '').strip()]})
    return out


def category_of(svc, kind, valid):
    """The category of a service: the one the centre chose (if it still exists) or the one of its kind."""
    try: c = svc['category']
    except (KeyError, IndexError, TypeError): c = None
    if c and c in valid: return c
    k = KIND_CATEGORY.get(kind, 'otros')
    return k if k in valid else (next(iter(valid)) if valid else k)


def doubtful(svc, kind):
    """A service of before whose category is not clear: its kind was not chosen in the wizard and it is «Otro»."""
    try: chosen = svc['kind']
    except (KeyError, IndexError, TypeError): chosen = None
    return (chosen is None) and kind == 'other'


def clean(data):
    label = re.sub(r'\s+', ' ', str(data.get('label') or '')).strip()[:60]
    if not label or re.search(r'[<>]', label): raise ValueError('Escribe el nombre de la categoría.')
    icon = str(data.get('icon') or 'extra')
    if icon not in ICONS: raise ValueError('Icono no válido.')
    tr = data.get('labels_i18n') if isinstance(data.get('labels_i18n'), dict) else {}
    tr = {l: re.sub(r'\s+', ' ', str(tr.get(l) or '')).strip()[:60] for l in LANGS if str(tr.get(l) or '').strip()}
    if any(re.search(r'[<>]', v) for v in tr.values()): raise ValueError('Una traducción tiene caracteres no permitidos.')
    try: order = int(data.get('sort_order') or 0)
    except (TypeError, ValueError): order = 0
    return label, icon, order, json.dumps(tr, ensure_ascii=False)
