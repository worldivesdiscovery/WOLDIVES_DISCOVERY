"""Short addresses of the QR codes (v50.57, revisión general, Bloque 4.4).

A QR printed on paper must keep working when the web changes, and it must only lead to WORLDIVES. So the QR holds a
short, stable address (/q/<code>) and the server decides where it goes each time it is scanned, from a list of
destinations: nobody types an address. If an internal route changes, only the table below changes and every QR
already printed keeps working. The scans are only counted (one number per QR), without data of anybody.

The destinations that need an item (a dive site, a centre, an experience, a service) keep its id; if the item
disappears, the QR leads to the list it belonged to and the panel says so («El destino ya no existe»)."""
from __future__ import annotations

import re
import secrets

ALPHABET = 'abcdefghjkmnpqrstuvwxyz23456789'   # 31 characters: no i, l, o, 0 or 1 (easy to read and to type)
CODE_LEN = 6                                   # 31^6 ≈ 887 million codes
CODE_RE = re.compile(f'[{ALPHABET}]{{{CODE_LEN}}}')

# (key, label, the item it needs: None or the kind chosen with the search)
ADMIN_DESTS = (
    ('portada', 'Portada', None),
    ('registro_centro', 'Registro de centros de buceo', None),
    ('registro_buceador', 'Registro de buceadores', None),
    ('registro_freelance', 'Registro de freelance', None),
    ('puntos', 'Explorar puntos de buceo', None),
    ('punto', 'Un punto de buceo', 'punto'),
    ('centros', 'Listado de centros', None),
    ('centro', 'Un centro', 'centro'),
    ('experiencias', 'Experiencias', None),
    ('experiencia', 'Una experiencia', 'experiencia'),
    ('app', 'Descargar la app', None),
)
# The QR of a centre, from its panel: its own pages only
CENTER_DESTS = (
    ('c_reservas', 'Tu página de reservas', None),
    ('c_servicio', 'Un servicio', 'servicio'),
    ('c_resena', 'Dejar una reseña', None),
    ('c_ficha', 'Tu ficha en WORLDIVES', None),
)
# Destinations listed but not available yet (Pendiente de decisión: the app is not published in the stores)
NOT_YET = {'app': 'La app todavía no está publicada: este destino se podrá elegir cuando exista.'}

# Where each destination leads (always a path of this web: never another site)
FIXED = {'portada': '/#/', 'registro_centro': '/#/registro?tipo=center', 'registro_buceador': '/#/registro?tipo=recreational',
         'registro_freelance': '/#/registro?tipo=freelance', 'puntos': '/#/puntos', 'centros': '/#/centros', 'experiencias': '/#/experiencias'}
ITEM = {'punto': '/#/punto?id={id}', 'centro': '/#/centro?id={id}', 'experiencia': '/#/experiencia?id={id}'}
FALLBACK = {'punto': '/#/puntos', 'centro': '/#/centros', 'experiencia': '/#/experiencias'}


def dests(for_center: bool):
    return CENTER_DESTS if for_center else ADMIN_DESTS


def spec(key, for_center: bool):
    """(label, kind of item it needs) of a destination of that list, or None."""
    return next(((label, need) for k, label, need in dests(for_center) if k == key), None)


def new_code(taken) -> str:
    """A random code that `taken(code)` says is free."""
    for _ in range(50):
        code = ''.join(secrets.choice(ALPHABET) for _ in range(CODE_LEN))
        if not taken(code): return code
    raise RuntimeError('No hay códigos libres')


def clean_code(value) -> str | None:
    """The code of an address /q/<code> (also written in capitals), or None."""
    code = str(value or '').strip().lower()
    return code if CODE_RE.fullmatch(code) else None


def is_internal(path: str) -> bool:
    """Only a path of this web: «/…», never «//host» or a full address."""
    return isinstance(path, str) and path.startswith('/') and not path.startswith('//') and '\\' not in path and '\n' not in path


def png_scale(modules: int, target: int = 2048) -> int:
    """Pixels per module for a PNG of at least `target` pixels (printing in large sizes)."""
    return max(10, -(-target // max(1, modules)))
