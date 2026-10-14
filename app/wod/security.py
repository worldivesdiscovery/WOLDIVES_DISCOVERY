"""Security helpers: passwords, rate limits, client IP behind a trusted proxy, URL and file checks, CSP."""
from __future__ import annotations

import base64
import hashlib
import hmac
import ipaddress
import os
import re
import secrets
import sqlite3
import sys
import threading
import time
import unicodedata
from pathlib import Path
from urllib.parse import urlparse

from . import config

# ---------------------------------------------------------------------------
# Passwords: PBKDF2-SHA256 with a version prefix so the cost can be raised later
# without breaking existing accounts. Format: pbkdf2_sha256$<iterations>$<salt b64>$<hash b64>
# Accounts created before v50.31 store base64(salt16 + digest) with 240 000 iterations;
# they keep working and are re-hashed with the current cost at their next login.
# ---------------------------------------------------------------------------
LEGACY_ITERATIONS = 240_000
HASH_PREFIX = 'pbkdf2_sha256'


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).decode().rstrip('=')


def _unb64(txt: str) -> bytes:
    return base64.urlsafe_b64decode(txt + '=' * (-len(txt) % 4))


def hash_password(password: str, iterations: int | None = None) -> str:
    iterations = iterations or config.PBKDF2_ITERATIONS
    salt = secrets.token_bytes(16)
    digest = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, iterations)
    return f'{HASH_PREFIX}${iterations}${_b64(salt)}${_b64(digest)}'


def verify_password(password: str, stored: str | None) -> bool:
    if not stored or stored == '!':
        return False
    try:
        if stored.startswith(HASH_PREFIX + '$'):
            _, it, salt, digest = stored.split('$', 3)
            check = hashlib.pbkdf2_hmac('sha256', password.encode(), _unb64(salt), int(it))
            return hmac.compare_digest(check, _unb64(digest))
        raw = base64.urlsafe_b64decode(stored.encode())
        salt, digest = raw[:16], raw[16:]
        check = hashlib.pbkdf2_hmac('sha256', password.encode(), salt, LEGACY_ITERATIONS)
        return hmac.compare_digest(check, digest)
    except Exception:
        return False


def needs_rehash(stored: str | None) -> bool:
    if not stored or stored == '!':
        return False
    if not stored.startswith(HASH_PREFIX + '$'):
        return True
    try:
        return int(stored.split('$')[1]) < config.PBKDF2_ITERATIONS
    except Exception:
        return True


# Words of this web and of diving that make a password easy to guess (ASVS 5.0 V6.1.2 and V6.2.11). Documented in
# docs/seguridad/autenticacion.md; compared without accents, capitals, digits or symbols.
CONTEXT_WORDS = ('worldivesdiscovery', 'worldives', 'worlddives', 'woldives', 'discovery', 'buceadora', 'buceador', 'bucear',
                 'buceo', 'scuba', 'diving', 'diver', 'padi', 'instructora', 'instructor', 'centro', 'freelance', 'administrador',
                 'admin', 'prueba', 'demo', 'contrasena', 'password')
_COMMON: frozenset | None = None


def common_passwords() -> frozenset:
    """The 20 000 most frequent leaked passwords of 10+ characters (app/wod/contrasenas-comunes.txt), loaded once."""
    global _COMMON
    if _COMMON is None:
        try:
            lines = (Path(__file__).with_name('contrasenas-comunes.txt')).read_text(encoding='utf-8').splitlines()
        except OSError:
            lines = []
        _COMMON = frozenset(x.strip() for x in lines if x.strip() and not x.startswith('#'))
    return _COMMON


def _letters(text: str) -> str:
    plain = unicodedata.normalize('NFKD', text.lower())
    return ''.join(ch for ch in plain if ch.isalpha() and not unicodedata.combining(ch))


def password_problem(password: str) -> str | None:
    """Minimum rules shared by registration, reset and change. Returns an error text or None."""
    if len(password) < 10:
        return 'La contraseña debe tener al menos 10 caracteres.'
    if len(password) > 256:
        return 'La contraseña es demasiado larga.'
    low = password.lower()
    common = common_passwords()
    if low in common or re.sub(r'[\W\d_]+$', '', low) in common or low in {'contraseña', 'contrasena1', 'worldives1'}:
        return 'Esa contraseña es demasiado fácil de adivinar.'
    letters = _letters(password)
    rest = letters
    for word in CONTEXT_WORDS:
        rest = rest.replace(word, '')
    if rest != letters and len(rest) < 5:   # only the name of the web or of diving, plus digits or symbols
        return 'Esa contraseña es demasiado fácil de adivinar.'
    return None


# ---------------------------------------------------------------------------
# Rate limiting: fixed window per key, thread-safe and with a bounded number of keys
# (old windows are dropped first) so an attacker cannot fill the memory.
# ---------------------------------------------------------------------------
class RateLimiter:
    def __init__(self, limit: int, window_seconds: int, max_keys: int = 20000):
        self.limit = limit
        self.window = window_seconds
        self.max_keys = max_keys
        self._lock = threading.Lock()
        self._hits: dict[str, list] = {}

    def _prune(self, current: float):
        if len(self._hits) < self.max_keys:
            return
        expired = [k for k, v in self._hits.items() if current - v[0] >= self.window]
        for k in expired:
            self._hits.pop(k, None)
        if len(self._hits) >= self.max_keys:
            for k, _ in sorted(self._hits.items(), key=lambda kv: kv[1][0])[: len(self._hits) // 4 or 1]:
                self._hits.pop(k, None)

    def blocked(self, key: str) -> bool:
        current = time.time()
        with self._lock:
            row = self._hits.get(key)
            if not row or current - row[0] >= self.window:
                return False
            return row[1] >= self.limit

    def hit(self, key: str) -> bool:
        """Counts one attempt. Returns True when the key is now over the limit."""
        current = time.time()
        with self._lock:
            row = self._hits.get(key)
            if not row or current - row[0] >= self.window:
                self._prune(current)
                self._hits[key] = [current, 1]
                return 1 > self.limit
            row[1] += 1
            return row[1] > self.limit

    def reset(self, key: str):
        with self._lock:
            self._hits.pop(key, None)

    def __len__(self):
        return len(self._hits)


class SharedRateLimiter(RateLimiter):
    """The same fixed window as RateLimiter, but counted once for the whole server: the counters live in a small SQLite
    file next to the database, so the WOD_WORKERS processes share them (v50.51: in memory, each process counted on its
    own and the real limit grew with the number of processes). Keys are stored hashed with WOD_SECRET_KEY (no IP or
    email in clear). If the file cannot be used, the limit falls back to the memory of the process."""
    _path = None
    _conn = None
    _pid = None
    _glock = threading.Lock()
    _warned = False

    def __init__(self, name: str, limit: int, window_seconds: int, max_keys: int = 20000):
        super().__init__(limit, window_seconds, max_keys)
        self.name = name
        self._writes = 0

    @classmethod
    def _db(cls):
        if cls._path is None: return None
        if cls._conn is None or cls._pid != os.getpid():   # never use a connection opened before fork()
            cls._path.parent.mkdir(parents=True, exist_ok=True)
            c = sqlite3.connect(str(cls._path), timeout=5, isolation_level=None, check_same_thread=False)
            c.execute('PRAGMA journal_mode=WAL'); c.execute('PRAGMA synchronous=NORMAL')
            c.execute('CREATE TABLE IF NOT EXISTS hits(name TEXT NOT NULL, key TEXT NOT NULL, start REAL NOT NULL, '
                      'count INTEGER NOT NULL, PRIMARY KEY(name, key)) WITHOUT ROWID')
            cls._conn, cls._pid = c, os.getpid()
        return cls._conn

    @classmethod
    def _failed(cls, exc):
        cls._conn = None
        if not cls._warned:
            cls._warned = True
            print(f'[límites] no se puede usar {cls._path} ({exc}); cada proceso cuenta por su cuenta', file=sys.stderr)

    def _k(self, key: str) -> str:
        pepper = config.env('WOD_SECRET_KEY', 'worldives')
        return hashlib.sha256(f'{pepper}|{self.name}|{key}'.encode()).hexdigest()[:32]

    def blocked(self, key: str) -> bool:
        with self._glock:
            try:
                c = self._db()
                if c is None: return super().blocked(key)
                row = c.execute('SELECT start, count FROM hits WHERE name=? AND key=?', (self.name, self._k(key))).fetchone()
            except sqlite3.Error as e:
                self._failed(e); return super().blocked(key)
        if not row or time.time() - row[0] >= self.window: return False
        return row[1] >= self.limit

    def hit(self, key: str) -> bool:
        """Counts one attempt. Returns True when the key is now over the limit."""
        now, k = time.time(), self._k(key)
        with self._glock:
            try:
                c = self._db()
                if c is None: return super().hit(key)
                c.execute('BEGIN IMMEDIATE')   # read and count in one step for every process
                try:
                    row = c.execute('SELECT start, count FROM hits WHERE name=? AND key=?', (self.name, k)).fetchone()
                    if not row or now - row[0] >= self.window:
                        count = 1; c.execute('INSERT OR REPLACE INTO hits VALUES(?,?,?,1)', (self.name, k, now))
                    else:
                        count = row[1] + 1; c.execute('UPDATE hits SET count=? WHERE name=? AND key=?', (count, self.name, k))
                    self._writes += 1
                    if self._writes % 500 == 1:   # expired windows are removed on the first count and every 500
                        c.execute('DELETE FROM hits WHERE name=? AND start<?', (self.name, now - self.window))
                    c.execute('COMMIT')
                except BaseException:
                    c.execute('ROLLBACK'); raise
            except sqlite3.Error as e:
                self._failed(e); return super().hit(key)
        return count > self.limit

    def reset(self, key: str):
        with self._glock:
            try:
                c = self._db()
                if c is not None: c.execute('DELETE FROM hits WHERE name=? AND key=?', (self.name, self._k(key)))
            except sqlite3.Error as e:
                self._failed(e)
        super().reset(key)

    def __len__(self):
        with self._glock:
            try:
                c = self._db()
                if c is not None: return c.execute('SELECT COUNT(*) FROM hits WHERE name=?', (self.name,)).fetchone()[0]
            except sqlite3.Error as e:
                self._failed(e)
        return super().__len__()


def configure_shared_limits(path):
    """Where the shared counters live (the server sets it next to its database); None = memory of each process."""
    from pathlib import Path
    with SharedRateLimiter._glock:
        SharedRateLimiter._path = Path(path) if path else None
        SharedRateLimiter._conn = None; SharedRateLimiter._pid = None


# ---------------------------------------------------------------------------
# Client IP and scheme behind a reverse proxy. X-Forwarded-* are only trusted when the
# TCP peer is listed in WOD_TRUSTED_PROXIES (IPs or CIDR ranges, comma separated).
# ---------------------------------------------------------------------------
_PROXY_CACHE: tuple[str, list] | None = None


def _trusted_networks():
    global _PROXY_CACHE
    raw = config.env('WOD_TRUSTED_PROXIES')
    if _PROXY_CACHE and _PROXY_CACHE[0] == raw:
        return _PROXY_CACHE[1]
    nets = []
    for part in raw.split(','):
        part = part.strip()
        if not part:
            continue
        try:
            nets.append(ipaddress.ip_network(part, strict=False))
        except ValueError:
            pass
    _PROXY_CACHE = (raw, nets)
    return nets


def is_trusted_proxy(ip: str) -> bool:
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return False
    return any(addr in n for n in _trusted_networks())


def client_ip(peer_ip: str, headers) -> str:
    if not is_trusted_proxy(peer_ip):
        return peer_ip
    fwd = headers.get('X-Forwarded-For') or ''
    # Walk from the right: the first address that is not one of our proxies is the client.
    for part in reversed([p.strip() for p in fwd.split(',') if p.strip()]):
        try:
            ipaddress.ip_address(part)
        except ValueError:
            continue
        if not is_trusted_proxy(part):
            return part
    real = (headers.get('X-Real-IP') or '').strip()
    return real or peer_ip


def ip_group(ip: str) -> str:
    """The address used in rate limits: an IPv6 /64 counts as one address (a single connection usually gets a whole
    /64, so per-address limits would be endless), IPv4 as itself (ASVS 5.0 V6.3.1)."""
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return ip
    if addr.version == 6:
        if addr.ipv4_mapped:
            return str(addr.ipv4_mapped)
        return str(ipaddress.ip_network(f'{addr}/64', strict=False))
    return str(addr)


def request_scheme(peer_ip: str, headers) -> str:
    if is_trusted_proxy(peer_ip):
        proto = (headers.get('X-Forwarded-Proto') or '').split(',')[0].strip().lower()
        if proto in {'http', 'https'}:
            return proto
    return 'https' if config.env_flag('WOD_HTTPS') else 'http'


def log_ip(ip: str) -> str:
    """IP as written to logs: WOD_LOG_IP=full | truncated (default) | none."""
    mode = config.env('WOD_LOG_IP', 'truncated').lower()
    if mode == 'full':
        return ip
    if mode == 'none':
        return '-'
    try:
        addr = ipaddress.ip_address(ip)
    except ValueError:
        return '-'
    if addr.version == 4:
        return str(ipaddress.ip_network(f'{ip}/24', strict=False).network_address)
    return str(ipaddress.ip_network(f'{ip}/48', strict=False).network_address)


def ip_hash(ip: str) -> str:
    """Pseudonymous IP for records that must not keep the address itself."""
    pepper = config.env('WOD_SECRET_KEY', 'worldives')
    return hashlib.sha256((pepper + '|' + ip).encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# URLs entered by users. Only http(s) links are ever stored for display; embeds must
# also be https and belong to an allowed provider.
# ---------------------------------------------------------------------------
_CTRL = re.compile(r'[\x00-\x20\x7f]')


def clean_http_url(value, max_len: int = 500, https_only: bool = False) -> str | None:
    if value is None:
        return None
    v = str(value).strip()[:max_len]
    if not v:
        return None
    if _CTRL.search(v):
        raise ValueError('El enlace contiene caracteres no válidos.')
    if v.startswith('www.'):
        v = 'https://' + v
    p = urlparse(v)
    allowed = {'https'} if https_only else {'http', 'https'}
    if p.scheme.lower() not in allowed or not p.netloc or '@' in p.netloc:
        raise ValueError('Escribe un enlace completo que empiece por https://')
    return v


SITE_IMAGE_PREFIXES = ('/img/', '/assets/uploads/')


def is_site_image(value) -> bool:
    """Our own image paths (v50.46): the site images (/img/…) and the uploads (/assets/uploads/…)."""
    v = str(value or '')
    return v.startswith(SITE_IMAGE_PREFIXES) and '..' not in v and not _CTRL.search(v)


def clean_local_or_http_url(value, max_len: int = 500) -> str | None:
    """Image references: either our own /img/… or /assets/uploads/… path or an http(s) URL."""
    if value is None:
        return None
    v = str(value).strip()[:max_len]
    if not v:
        return None
    if is_site_image(v):
        return v
    return clean_http_url(v, max_len)


def embed_allowed(url: str | None, domains: list[str] | None = None) -> bool:
    if not url:
        return False
    try:
        p = urlparse(str(url).strip())
    except Exception:
        return False
    if p.scheme != 'https' or not p.hostname or _CTRL.search(str(url)) or '@' in p.netloc:
        return False
    host = p.hostname.lower()
    path = p.path or '/'
    for rule in (domains if domains is not None else config.embed_domains()):
        rule_host, _, rule_path = rule.partition('/')
        if host == rule_host or host.endswith('.' + rule_host):
            if not rule_path or path.startswith('/' + rule_path):
                return True
    return False


def clean_embed_url(value, domains: list[str] | None = None) -> str | None:
    if value in (None, ''):
        return None
    v = str(value).strip()[:1000]
    if not embed_allowed(v, domains):
        allowed = ', '.join(domains if domains is not None else config.embed_domains())
        raise ValueError(f'Solo se admiten enlaces https:// de estos servicios: {allowed}.')
    return v


# ---------------------------------------------------------------------------
# File types checked by their first bytes, never by the name the browser sends.
# ---------------------------------------------------------------------------
def sniff_document(content: bytes) -> str | None:
    """PDF, JPG, PNG or WEBP. Returns the extension or None."""
    if content.startswith(b'%PDF-'):
        return '.pdf'
    if content.startswith(b'\xff\xd8\xff'):
        return '.jpg'
    if content.startswith(b'\x89PNG\r\n\x1a\n'):
        return '.png'
    if content[:4] == b'RIFF' and content[8:12] == b'WEBP':
        return '.webp'
    return None


def sniff_video(content: bytes) -> str | None:
    if content[4:8] == b'ftyp':
        brand = content[8:12]
        return '.mov' if brand == b'qt  ' else '.mp4'
    if content.startswith(b'\x1a\x45\xdf\xa3'):
        return '.webm'
    return None


DOCUMENT_TYPES = {'.pdf': 'application/pdf', '.jpg': 'image/jpeg', '.png': 'image/png', '.webp': 'image/webp'}


# ---------------------------------------------------------------------------
# Content-Security-Policy. Scripts and styles only from our own origin (Leaflet is
# self-hosted); map tiles from the configured providers; iframes only from the
# allowed embed providers and only after the visitor clicks «Cargar vídeo».
# ---------------------------------------------------------------------------
def content_security_policy() -> str:
    from . import videos   # v50.50: the players of the insertable video platforms (wod.videos.PLATFORMS)
    frames = sorted({'https://' + d.partition('/')[0] for d in config.embed_domains()} |
                    {'https://www.' + d.partition('/')[0] for d in config.embed_domains() if d.count('.') == 1} |
                    {'https://' + h for h in videos.frame_hosts()})
    connect = ["'self'"] + [x.strip() for x in config.env('WOD_CSP_EXTRA_CONNECT').split(',') if x.strip()]
    scripts = ["'self'"]
    # v50.47: «Conectar mi WhatsApp Business» uses Meta's Embedded Signup (Facebook JS SDK). Allowed only when the owner
    # has enabled WhatsApp in the .env; otherwise the policy stays exactly as before.
    if config.env('WHATSAPP_ENABLED') in ('1', 'true', 'yes', 'on') and config.env('WHATSAPP_APP_ID'):
        scripts.append('https://connect.facebook.net')
        connect += ['https://graph.facebook.com', 'https://www.facebook.com', 'https://connect.facebook.net']
        frames += ['https://www.facebook.com', 'https://web.facebook.com']
    pmtiles = config.env('WOD_PMTILES_URL')
    if pmtiles.startswith('https://'):
        p = urlparse(pmtiles)
        connect.append(f'{p.scheme}://{p.netloc}')
    return '; '.join([
        "default-src 'self'",
        'script-src ' + ' '.join(scripts),
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob: https:",
        "font-src 'self'",
        'connect-src ' + ' '.join(connect),
        'frame-src ' + (' '.join(frames) if frames else "'none'"),
        "media-src 'self' blob:",
        "worker-src 'self'",
        "manifest-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
    ] + (['upgrade-insecure-requests'] if config.public_url().startswith('https://') else []))


def constant_time_equals(a: str, b: str) -> bool:
    return hmac.compare_digest(str(a).encode(), str(b).encode())


def random_token(nbytes: int = 24) -> str:
    return secrets.token_urlsafe(nbytes)


_SECRET: bytes | None = None


def secret_key() -> bytes:
    """Server secret for signing short-lived tokens. WOD_SECRET_KEY in production; random per process otherwise."""
    global _SECRET
    if _SECRET is None:
        raw = config.env('WOD_SECRET_KEY')
        _SECRET = raw.encode() if raw else os.urandom(32)
    return _SECRET
