"""v50.58 · Reserva exprés desde la web del centro (encargo unificado del 16/10/2026, bloque 2).

Lo que la reserva exprés necesita del servidor y no depende de la base de datos: la tira de los próximos días, las
horas y días más cercanos con plazas cuando la elegida se ha llenado, el prefijo de teléfono que se propone según el
idioma, el enlace de «Escribir al centro por WhatsApp», el archivo de calendario de una reserva y los datos de los
acompañantes (nombre, titulación y tallas) que la persona completa después.

El servidor sigue decidiendo todo lo importante (plazas, precio, reglas): aquí solo se ordena y se limpia.
"""
from __future__ import annotations

import datetime as dt
import re

STRIP_DAYS = 14          # «una tira de días que se desliza, con los próximos 14 días»
ALTERNATIVES = 4         # las horas o los días más cercanos con plazas que se proponen
LEVELS = ('none', 'ow', 'aow', 'rescue')   # «Sin titulación», «Open Water», «Advanced», «Rescue o más»
SIZES = ('XS', 'S', 'M', 'L', 'XL', 'XXL')
COMPANIONS_MAX = 20

# El prefijo que se propone en el teléfono de quien reserva, según el idioma de la página (se puede cambiar).
PHONE_PREFIX = {'es': '+34', 'en': '+44', 'fr': '+33', 'de': '+49', 'it': '+39', 'pt': '+351', 'pl': '+48', 'nl': '+31', 'zh': '+86'}
# …o según el país del centro cuando el idioma no lo dice (un cliente inglés en España sigue viendo +44).
COUNTRY_PREFIX = {'españa': '+34', 'spain': '+34', 'francia': '+33', 'france': '+33', 'portugal': '+351', 'italia': '+39', 'italy': '+39',
                  'alemania': '+49', 'germany': '+49', 'méxico': '+52', 'mexico': '+52', 'reino unido': '+44', 'united kingdom': '+44',
                  'países bajos': '+31', 'netherlands': '+31', 'polonia': '+48', 'poland': '+48', 'china': '+86', 'egipto': '+20', 'egypt': '+20',
                  'tailandia': '+66', 'thailand': '+66', 'indonesia': '+62', 'filipinas': '+63', 'philippines': '+63', 'maldivas': '+960', 'maldives': '+960'}


def phone_prefix(lang: str, country: str | None = None) -> str:
    return PHONE_PREFIX.get((lang or '').lower()) or COUNTRY_PREFIX.get((country or '').strip().lower(), '+34')


def day_strip(today: str, slots: list[dict], days: int = STRIP_DAYS) -> list[dict]:
    """Los próximos `days` días desde hoy, cada uno con sus salidas (hora y plazas libres) y si quedan plazas."""
    start = dt.date.fromisoformat(today)
    by = {}
    for s in slots: by.setdefault(s['date'], []).append({'id': s['id'], 'time': s.get('time') or '', 'free': max(0, int(s.get('free') or 0))})
    out = []
    for i in range(days):
        d = (start + dt.timedelta(days=i)).isoformat()
        ss = sorted(by.get(d, []), key=lambda x: x['time'])
        out.append({'date': d, 'slots': ss, 'free': any(x['free'] > 0 for x in ss)})
    return out


def _minutes(hhmm: str) -> int:
    m = re.fullmatch(r'(\d{1,2}):(\d{2})', hhmm or '')
    return int(m.group(1)) * 60 + int(m.group(2)) if m else 12 * 60


def alternatives(slots: list[dict], want_date: str, want_time: str, pax: int, exclude: int | None = None, limit: int = ALTERNATIVES) -> list[dict]:
    """«Si no quedan plazas a esa hora, se proponen al momento las horas o los días más cercanos con plazas»: primero
    las otras horas del mismo día (las más cercanas a la elegida) y después los días más cercanos, antes o después."""
    try: want = dt.date.fromisoformat(want_date)
    except (TypeError, ValueError): return []
    t0 = _minutes(want_time)
    ok = [s for s in slots if s['id'] != exclude and int(s.get('free') or 0) >= max(1, pax)]

    def key(s):
        days = abs((dt.date.fromisoformat(s['date']) - want).days)
        return (days, abs(_minutes(s.get('time') or '') - t0), s['date'], s.get('time') or '')
    return [{'id': s['id'], 'date': s['date'], 'time': s.get('time') or '', 'free': int(s['free']), 'same_day': s['date'] == want_date}
            for s in sorted(ok, key=key)[:limit]]


def whatsapp_link(phone: str | None, text: str = '') -> str:
    """«Escribir al centro por WhatsApp»: solo con un número internacional (con prefijo). Sin número, nada."""
    digits = re.sub(r'\D', '', phone or '')
    if not (phone or '').strip().startswith('+') or not 8 <= len(digits) <= 15: return ''
    from urllib.parse import quote
    return f'https://wa.me/{digits}' + (f'?text={quote(text)}' if text else '')


def maps_link(lat, lon, address: str = '') -> str:
    """«Cómo llegar»: el mapa del punto de encuentro o del centro (abre la aplicación de mapas del móvil)."""
    from urllib.parse import quote
    if lat is not None and lon is not None:
        try: return f'https://www.google.com/maps/dir/?api=1&destination={float(lat):.6f},{float(lon):.6f}'
        except (TypeError, ValueError): pass
    return f'https://www.google.com/maps/dir/?api=1&destination={quote(address)}' if (address or '').strip() else ''


def _ics_text(s: str) -> str:
    return re.sub(r'([,;\\])', r'\\\1', str(s or '')).replace('\r', '').replace('\n', '\\n')


def booking_ics(uid: str, title: str, start_utc: str, end_utc: str, location: str, description: str, stamp_utc: str) -> bytes:
    """«Añadir al calendario»: un evento con la hora de la salida (en UTC: cada calendario la enseña en su hora)."""
    f = lambda v: re.sub(r'[-:]', '', v)[:15] + 'Z'
    lines = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//WORLDIVES//Reserva//ES', 'CALSCALE:GREGORIAN', 'METHOD:PUBLISH', 'BEGIN:VEVENT',
             f'UID:{uid}', f'DTSTAMP:{f(stamp_utc)}', f'DTSTART:{f(start_utc)}', f'DTEND:{f(end_utc)}', f'SUMMARY:{_ics_text(title)}']
    if location: lines.append(f'LOCATION:{_ics_text(location)}')
    if description: lines.append(f'DESCRIPTION:{_ics_text(description)}')
    lines += ['END:VEVENT', 'END:VCALENDAR']
    out = []
    for ln in lines:   # RFC 5545: lines of at most 75 octets, folded with a space
        b = ln.encode('utf-8')
        while len(b) > 75:
            cut = 75
            while cut and (b[cut] & 0xC0) == 0x80: cut -= 1
            out.append(b[:cut]); b = b' ' + b[cut:]
        out.append(b)
    return b'\r\n'.join(out) + b'\r\n'


def clean_companions(raw, participants: int) -> list[dict]:
    """Los datos de los acompañantes (asientos 2…N): nombre, titulación y tallas, todo opcional menos el nombre."""
    if not isinstance(raw, list): raise ValueError('Datos de los acompañantes no válidos.')
    out = []
    for i, x in enumerate(raw[:max(0, min(participants, COMPANIONS_MAX) - 1)]):
        if not isinstance(x, dict): continue
        name = re.sub(r'\s+', ' ', str(x.get('name') or '')).strip()[:120]
        if not name: continue
        level = x.get('level') if x.get('level') in LEVELS else None
        size = str(x.get('size') or '').upper()
        shoe = str(x.get('shoe') or '').strip()
        out.append({'seat': i + 2, 'name': name, 'level': level, 'size': size if size in SIZES else None,
                    'shoe': shoe if re.fullmatch(r'\d{2}(\.5)?', shoe) and 20 <= float(shoe) <= 50 else None})
    return out


# Stripe.js and its form inside the booking (Embedded Checkout), with the addresses Stripe documents for its Content
# Security Policy (https://docs.stripe.com/security/guide#content-security-policy). Only the booking pages get them,
# and only when the server has the publishable key; every other page keeps its policy.
STRIPE_SCRIPT = ('https://js.stripe.com', 'https://*.js.stripe.com', 'https://maps.googleapis.com')
STRIPE_FRAME = ('https://js.stripe.com', 'https://*.js.stripe.com', 'https://hooks.stripe.com', 'https://checkout.stripe.com')
STRIPE_CONNECT = ('https://api.stripe.com', 'https://checkout.stripe.com', 'https://merchant-ui-api.stripe.com', 'https://maps.googleapis.com')
STRIPE_PAYMENT_ALLOW = '(self "https://js.stripe.com" "https://checkout.stripe.com")'   # Permissions-Policy: Apple Pay / Google Pay


def with_stripe(csp: str) -> str:
    out = []
    for part in csp.split('; '):
        name = part.split(' ', 1)[0]
        extra = {'script-src': STRIPE_SCRIPT, 'frame-src': STRIPE_FRAME, 'connect-src': STRIPE_CONNECT}.get(name)
        out.append(part + ''.join(' ' + x for x in extra if x not in part.split(' ')) if extra else part)
    return '; '.join(out)
