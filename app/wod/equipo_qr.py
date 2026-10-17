"""v50.58 · Equipo del centro con cuentas propias, enlazadas por QR (encargo unificado del 16/10/2026, bloque 1).

Lo que no depende de la base de datos:
- el QR personal: un código firmado que no lleva datos personales (un identificador al azar de la cuenta, la hora, un
  número de un solo uso y la firma), que cambia cada 60 segundos y solo sirve una vez;
- el código corto de 6 caracteres (caduca a los 10 minutos) y el enlace «Compartir para enlazar» (24 horas, un uso);
- leer lo que se escanea o se pega: un QR, un código o un enlace;
- las reglas de los planes (quién se puede enlazar y con qué perfil) y de los enlaces «Fijo» o «Por días».
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import re
import secrets
from datetime import date
from urllib.parse import parse_qs, urlparse

QR_SECONDS = 60          # cada cuánto cambia el QR que enseña «Mi QR»
QR_GRACE = 30            # margen para quien escanea justo cuando cambia: una captura de hace 2 minutos ya no vale
CODE_SECONDS = 600       # el código corto, 10 minutos
SHARE_SECONDS = 86400    # «Compartir para enlazar», 24 horas
REF_SECONDS = 900        # lo que el centro tiene tras escanear, para elegir perfil y fechas: 15 minutos
CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'   # sin 0/O, 1/I/L: se dicta y se escribe sin dudas
CODE_LEN = 6
PRO_TEAM_MAX = 15        # decisión del titular (16/10/2026): Pro, el propietario y hasta 15 personas
BOOKING_TEAM_MAX = 1     # Motor de reservas: el propietario y una persona, solo Recepción
RECEPTION = 'reception'
STATES = ('pending', 'active', 'declined', 'cancelled', 'ended', 'paused')
# Colores de los centros en «Mi agenda» (el mismo centro, siempre el mismo color)
COLORS = ('#0f766e', '#7c3aed', '#c2410c', '#0369a1', '#be123c', '#4d7c0f', '#a16207', '#1d4ed8')


def _b64(raw: bytes) -> str:
    return base64.urlsafe_b64encode(raw).rstrip(b'=').decode()


def _sig(secret: str, msg: str, n: int = 16) -> str:
    return _b64(hmac.new(secret.encode(), msg.encode(), hashlib.sha256).digest()[:n])


def new_handle() -> str:
    """El identificador de una cuenta en su QR: al azar, no es su número ni su email."""
    return _b64(secrets.token_bytes(12))


def qr_token(secret: str, handle: str, now: int) -> str:
    nonce = _b64(secrets.token_bytes(9))
    body = f'q1.{handle}.{int(now)}.{nonce}'
    return f'{body}.{_sig(secret, body)}'


def qr_parse(secret: str, token: str, now: int):
    """(handle, hora, nonce) de un QR personal bueno y en su minuto; ValueError si no lo es."""
    parts = str(token or '').strip().split('.')
    if len(parts) != 5 or parts[0] != 'q1' or not parts[2].isdigit():
        raise ValueError('Ese código no es un QR de WORLDIVES.')
    body = '.'.join(parts[:4])
    if not hmac.compare_digest(_sig(secret, body), parts[4]):
        raise ValueError('Ese código no es un QR de WORLDIVES.')
    ts = int(parts[2])
    if ts > now + 5 or now - ts > QR_SECONDS + QR_GRACE:
        raise ValueError('Ese QR ha caducado. Pide a la persona que abra «Mi QR» y vuelve a escanearlo.')
    return parts[1], ts, parts[3]


def short_code(secret: str, handle: str, issued_at: int) -> str:
    """El código corto de una cuenta para un momento: se calcula, no se guarda en claro."""
    d = hmac.new(secret.encode(), f'code.{handle}.{int(issued_at)}'.encode(), hashlib.sha256).digest()
    return ''.join(CODE_ALPHABET[b % len(CODE_ALPHABET)] for b in d[:CODE_LEN])


def code_hash(secret: str, code: str) -> str:
    return hmac.new(secret.encode(), f'codeh.{code}'.encode(), hashlib.sha256).hexdigest()


def token_hash(token: str) -> str:
    return hashlib.sha256(str(token).encode()).hexdigest()


def clean_code(text: str) -> str:
    return re.sub(r'[\s\-·.]', '', str(text or '')).upper()


def read(text: str):
    """Qué es lo que se ha escaneado o pegado: ('qr', token), ('share', token), ('code', código) o ValueError."""
    raw = str(text or '').strip()
    if not raw: raise ValueError('Escanea el QR o escribe el código.')
    if len(raw) > 600: raise ValueError('Ese código no es de WORLDIVES.')
    if raw.startswith('q1.'): return 'qr', raw
    if '://' in raw or raw.startswith(('/', '#')):
        u = urlparse(raw if '://' in raw else 'https://x' + (raw if raw.startswith('/') else '/' + raw))
        m = re.fullmatch(r'/p/(q1\.[A-Za-z0-9_\-.]+)', u.path or '')
        if m: return 'qr', m.group(1)
        frag = u.fragment or ''
        m = re.match(r'/?p/(q1\.[A-Za-z0-9_\-.]+)', frag)
        if m: return 'qr', m.group(1)
        m = re.fullmatch(r'/e/([A-Za-z0-9_\-]{20,64})', u.path or '')
        if m: return 'share', m.group(1)
        q = parse_qs(frag.split('?', 1)[1]) if '?' in frag else parse_qs(u.query or '')
        tok = (q.get('i') or [''])[0]
        if re.fullmatch(r'[A-Za-z0-9_\-]{20,64}', tok): return 'share', tok
        raise ValueError('Ese enlace no es de WORLDIVES.')
    if re.fullmatch(r'[A-Za-z0-9_\-]{20,64}', raw): return 'share', raw
    code = clean_code(raw)
    if len(code) == CODE_LEN and all(c in CODE_ALPHABET for c in code): return 'code', code
    raise ValueError('El código tiene 6 letras y números. Revísalo con la persona.')


# ------------------------------------------------------------------ planes
def team_rules(plan_code: str, has_team: bool, any_profile: bool, limit: int):
    """Lo que permite el plan del centro: (cuántas personas además del propietario, solo Recepción, aviso si no se puede).
    limit 0 = sin límite (una excepción de la administración)."""
    if not has_team:
        return 0, False, 'Disponible en el plan Motor de reservas'
    if not any_profile:
        return BOOKING_TEAM_MAX, True, None
    return (limit or 0), False, None


def needs_freelance(member_role: str) -> bool:
    """Para los perfiles de trabajo (Instructor, Encargado, los propios…) hace falta una cuenta de freelance; Recepción
    se puede enlazar con una cuenta normal (decisión del titular, 16/10/2026)."""
    return member_role != RECEPTION


# ------------------------------------------------------------------ enlaces «Fijo» o «Por días»
def clean_dates(kind: str, starts_on, ends_on, today: str):
    if kind not in ('fixed', 'days'): raise ValueError('Elige «Fijo en el equipo» o «Por días».')
    if kind == 'fixed': return 'fixed', None, None
    try:
        a = date.fromisoformat(str(starts_on or '')[:10]); b = date.fromisoformat(str(ends_on or starts_on or '')[:10])
    except ValueError:
        raise ValueError('Pon el primer y el último día del enlace.')
    if b < a: raise ValueError('El último día no puede ser antes del primero.')
    if b.isoformat() < today: raise ValueError('Ese enlace ya habría terminado: elige días de hoy en adelante.')
    if (b - a).days > 366: raise ValueError('Un enlace «Por días» dura como mucho un año; para más, «Fijo en el equipo».')
    return 'days', a.isoformat(), b.isoformat()


def in_force(kind: str, starts_on, ends_on, today: str) -> bool:
    """¿Da acceso hoy? Un enlace fijo, siempre; uno por días, entre su primer y su último día (los dos incluidos)."""
    if kind != 'days': return True
    return (not starts_on or starts_on <= today) and (not ends_on or today <= ends_on)


def color_of(center_id: int) -> str:
    return COLORS[int(center_id or 0) % len(COLORS)]
