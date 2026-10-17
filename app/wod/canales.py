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


LOCAL_RE = re.compile(r'(localhost|127\.0\.0\.1):(\d{2,5})')


def clean_domain(value, allow_local: bool = False) -> str | None:
    """«https://www.BuceoMarAzul.com/reservas» → «www.buceomarazul.com». «*.marazul.com» allows its subdomains.
    No IP addresses, no localhost, no ports: a real website of the centre. Only the test package (never production,
    allow_local) accepts «localhost:8101» or «127.0.0.1:8101», for the example website of the centre."""
    s = str(value or '').strip().lower()
    s = re.sub(r'^[a-z][a-z0-9+.-]*://', '', s).split('/')[0].split('?')[0].split('#')[0].rstrip('.')
    if allow_local and LOCAL_RE.fullmatch(s): return s
    if ':' in s: s = s.split(':')[0]
    try:
        ipaddress.ip_address(s.lstrip('*.')); return None
    except ValueError:
        pass
    return s if HOST_RE.fullmatch(s) else None


def clean_domains(values, limit: int = 10, allow_local: bool = False) -> list[str]:
    out = []
    for v in (values if isinstance(values, (list, tuple)) else re.split(r'[\s,;]+', str(values or ''))):
        d = clean_domain(v, allow_local)
        if d and d not in out: out.append(d)
    return out[:limit]


def host_allowed(host: str, allowed: list[str]) -> bool:
    """«buceomarazul.com» also covers «www.buceomarazul.com»; «*.marazul.com» covers any subdomain (not the bare one).
    A local test entry («localhost:8101») must match host and port exactly."""
    raw = str(host or '').lower().rstrip('.')
    h = raw.split(':')[0]
    if not h: return False
    for d in allowed or []:
        if LOCAL_RE.fullmatch(d):
            if raw == d: return True
        elif d.startswith('*.'):
            if h.endswith(d[1:]) and h != d[2:]: return True
        elif h == d or h == 'www.' + d:
            return True
    return False


def frame_ancestors(allowed: list[str], extra=()) -> str:
    """CSP frame-ancestors for the widget of one centre: only its domains (https), never «*»."""
    parts = []
    for d in allowed or []:
        if LOCAL_RE.fullmatch(d):
            parts.append(f'http://{d}'); continue
        parts.append(f'https://{d}')
        if not d.startswith('*.') and not d.startswith('www.'): parts.append(f'https://www.{d}')
    parts += [x for x in extra if x]
    return ' '.join(dict.fromkeys(parts)) or "'none'"


def origin_host(url: str) -> str:
    """«https://www.marazul.com/reservas?x» → «www.marazul.com»; «http://localhost:8101/» → «localhost:8101»."""
    m = re.match(r'^[a-z][a-z0-9+.-]*://([^/?#]+)', str(url or '').strip().lower())
    if not m: return ''
    host = m.group(1).split('@')[-1]
    return host if LOCAL_RE.fullmatch(host) else host.split(':')[0]


# ------------------------------------------------------------------ the centre's page and widget (Partes C y D)
SLUG_RE = re.compile(r'[a-z0-9](?:[a-z0-9-]{1,58}[a-z0-9])')
RESERVED_SLUGS = frozenset({'admin', 'api', 'app', 'c', 'w', 'www', 'widget', 'worldives', 'reservar', 'reserva', 'centro', 'centros', 'pagar',
                            'mi-reserva', 'nuevo', 'demo', 'prueba', 'pruebas', 'login', 'registro', 'legal', 'ayuda', 'soporte'})
WIDGET_FORMATS = ('boton', 'calendario', 'lista')
COLOR_RE = re.compile(r'#[0-9a-f]{6}')


def slugify(text: str) -> str:
    """«Buceo Mar Azul · Xàbia» → «buceo-mar-azul-xabia» (letters and digits only, 3 to 60 characters)."""
    import unicodedata
    s = ''.join(ch for ch in unicodedata.normalize('NFKD', str(text or '').lower()) if not unicodedata.combining(ch))
    s = re.sub(r'[^a-z0-9]+', '-', s).strip('-')[:60].strip('-')
    return s


def clean_slug(value) -> str | None:
    s = slugify(value)
    return s if SLUG_RE.fullmatch(s or '') and s not in RESERVED_SLUGS else None


def clean_color(value) -> str | None:
    s = str(value or '').strip().lower()
    return s if COLOR_RE.fullmatch(s) else None


# ------------------------------------------------------------------ invisible check against bots (proof of work)
# Only after several attempts from the same address: the browser of a person solves it in about a second without
# seeing anything; a bot sending hundreds of bookings pays the work every time. No third-party service, no cookie.
POW_BITS = 14
POW_TTL = 300


def pow_challenge(secret_hash, now: int | None = None) -> str:
    """«<unix>.<random>.<bits>.<mac>»: the server keeps nothing; the MAC proves it issued the challenge."""
    ts = int(now if now is not None else time.time()); rnd = secrets.token_hex(8)
    body = f'{ts}.{rnd}.{POW_BITS}'
    return f'{body}.{secret_hash(body)[:24]}'


def pow_ok(secret_hash, challenge: str, nonce, now: int | None = None) -> bool:
    try:
        ts, rnd, bits, mac = str(challenge).split('.')
        ts, bits = int(ts), int(bits)
    except ValueError:
        return False
    if not hmac.compare_digest(secret_hash(f'{ts}.{rnd}.{bits}')[:24], mac): return False
    if bits < POW_BITS or abs(int(now if now is not None else time.time()) - ts) > POW_TTL: return False
    n = str(nonce or '')
    if not re.fullmatch(r'[0-9]{1,12}', n): return False
    digest = hashlib.sha256(f'{challenge}:{n}'.encode()).digest()
    value = int.from_bytes(digest[:4], 'big')
    return value >> (32 - bits) == 0


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
