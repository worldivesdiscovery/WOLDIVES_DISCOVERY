"""v50.56 · Encargo «motor de reservas multicanal», reglas puras (sin base de datos).

Un solo inventario: da igual por dónde entre una reserva (el buscador de WORLDIVES, la web del centro, un enlace
directo, la API o el propio centro por teléfono), todas pasan por la misma función del servidor (create_booking) y
descuentan del mismo sitio. Aquí: los canales, la clave de idempotencia, los dominios donde puede ir el widget, las
claves de API y la firma de los avisos automáticos (webhooks)."""
from __future__ import annotations

import hashlib
import hmac
import ipaddress
import re
import secrets
import time

# Where each booking came from. «import» is for bookings or blocks brought from another system (iCal, CSV).
CHANNELS = ('worldives', 'widget', 'link', 'api', 'manual', 'import')
CHANNEL_LABELS = {'worldives': 'WORLDIVES', 'widget': 'Tu web', 'link': 'Enlace directo', 'api': 'API', 'manual': 'Manual', 'import': 'Importada'}
ONLINE = ('worldives', 'widget', 'link', 'api')       # the customer books by himself: the rules of the service apply
# The old «source» column (v50.30) keeps working for older screens and exports.
_SOURCE = {'worldives': 'online', 'link': 'online', 'widget': 'widget', 'api': 'api', 'manual': 'manual', 'import': 'web'}

NO_SPOTS_TEXT = 'Sin plazas: ya no quedan plazas libres para esa fecha.'

IDEM_RE = re.compile(r'[A-Za-z0-9._:\-]{8,128}')
IDEM_KEEP_HOURS = 48


def source_for(channel: str) -> str:
    return _SOURCE.get(channel, 'online')


def channel_of(row) -> str:
    """The channel of a booking row, also for bookings made before v50.56 (only «source» then)."""
    try:
        ch = row['channel']
    except (KeyError, IndexError):
        ch = None
    if ch in CHANNELS: return ch
    try:
        src = row['source']
    except (KeyError, IndexError):
        src = None
    return {'manual': 'manual', 'web': 'import', 'api': 'api', 'widget': 'widget', 'import': 'import'}.get(src or '', 'worldives')


def clean_idem_key(raw) -> str | None:
    """The idempotency key sent by the browser or the API (Idempotency-Key): 8 to 128 safe characters, or nothing."""
    s = str(raw or '').strip()
    return s if IDEM_RE.fullmatch(s) else None


def idem_hash(scope: str, key: str) -> str:
    """The same key from two different customers or two different API keys never collides: the scope goes in."""
    return hashlib.sha256(f'{scope}\x00{key}'.encode('utf-8')).hexdigest()


# ------------------------------------------------------------------ the widget's authorised domains
HOST_RE = re.compile(r'(?:\*\.)?(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}')


def clean_domain(value) -> str | None:
    """«https://www.BuceoMarAzul.com/reservas» → «www.buceomarazul.com». «*.marazul.com» allows its subdomains.
    No IP addresses, no localhost, no ports: a real website of the centre."""
    s = str(value or '').strip().lower()
    s = re.sub(r'^[a-z][a-z0-9+.-]*://', '', s).split('/')[0].split('?')[0].split('#')[0].rstrip('.')
    if ':' in s: s = s.split(':')[0]
    try:
        ipaddress.ip_address(s.lstrip('*.')); return None
    except ValueError:
        pass
    return s if HOST_RE.fullmatch(s) else None


def clean_domains(values, limit: int = 10) -> list[str]:
    out = []
    for v in (values if isinstance(values, (list, tuple)) else re.split(r'[\s,;]+', str(values or ''))):
        d = clean_domain(v)
        if d and d not in out: out.append(d)
    return out[:limit]


def host_allowed(host: str, allowed: list[str]) -> bool:
    """«buceomarazul.com» also covers «www.buceomarazul.com»; «*.marazul.com» covers any subdomain (not the bare one)."""
    h = str(host or '').lower().split(':')[0].rstrip('.')
    if not h: return False
    for d in allowed or []:
        if d.startswith('*.'):
            if h.endswith(d[1:]) and h != d[2:]: return True
        elif h == d or h == 'www.' + d:
            return True
    return False


def frame_ancestors(allowed: list[str], extra=()) -> str:
    """CSP frame-ancestors for the widget of one centre: only its domains (https), never «*»."""
    parts = []
    for d in allowed or []:
        parts.append(f'https://{d}')
        if not d.startswith('*.') and not d.startswith('www.'): parts.append(f'https://www.{d}')
    parts += [x for x in extra if x]
    return ' '.join(dict.fromkeys(parts)) or "'none'"


# ------------------------------------------------------------------ API keys of a centre
API_SCOPES = ('read', 'write')


def new_api_key() -> tuple[str, str, str]:
    """(key shown once, prefix kept to recognise it, SHA-256 kept in the database)."""
    key = 'wdk_' + secrets.token_urlsafe(32)
    return key, key[:12], api_key_hash(key)


def api_key_hash(key: str) -> str:
    return hashlib.sha256(str(key or '').encode('utf-8')).hexdigest()


# ------------------------------------------------------------------ webhooks (signed notices to the centre)
WEBHOOK_EVENTS = ('booking.created', 'booking.confirmed', 'booking.paid', 'booking.cancelled', 'booking.changed')
WEBHOOK_TOLERANCE = 300           # seconds: an older signature is refused (replays)
WEBHOOK_RETRIES = (60, 300, 1800, 7200, 21600, 86400)   # after each failure: 1 min, 5 min, 30 min, 2 h, 6 h, 24 h


def new_webhook_secret() -> str:
    return 'whsk_' + secrets.token_urlsafe(32)


def sign(secret: str, body: bytes, ts: int | None = None) -> str:
    """Header X-WORLDIVES-Signature: «t=<unix>,v1=<hex HMAC-SHA256 of "t.body">» (the same idea as Stripe's)."""
    ts = int(ts if ts is not None else time.time())
    mac = hmac.new(secret.encode('utf-8'), f'{ts}.'.encode('ascii') + body, hashlib.sha256).hexdigest()
    return f't={ts},v1={mac}'


def verify(secret: str, header: str, body: bytes, now: int | None = None, tolerance: int = WEBHOOK_TOLERANCE) -> bool:
    """What the centre's server does with each notice (also in docs/api): the signature and the time must match."""
    try:
        parts = dict(p.split('=', 1) for p in str(header or '').split(','))
        ts = int(parts['t']); got = parts['v1']
    except (ValueError, KeyError):
        return False
    if abs(int(now if now is not None else time.time()) - ts) > tolerance: return False
    want = hmac.new(secret.encode('utf-8'), f'{ts}.'.encode('ascii') + body, hashlib.sha256).hexdigest()
    return hmac.compare_digest(want, got)


def webhook_url_ok(url: str) -> bool:
    """Only https to a public host name (the delivery itself also refuses private addresses, ASVS V12.6.1)."""
    m = re.fullmatch(r'https://([^/:?#]+)(:\d{2,5})?(/[^\s]*)?', str(url or '').strip())
    return bool(m and clean_domain(m.group(1)) and not m.group(1).startswith('*.') and len(url) <= 500)


def retry_delay(attempts: int) -> int | None:
    """Seconds before the next try after `attempts` failed deliveries; None: give up."""
    return WEBHOOK_RETRIES[attempts - 1] if 1 <= attempts <= len(WEBHOOK_RETRIES) else None
