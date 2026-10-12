"""Personal data encrypted at rest (v50.47, encargo «avisos y aislamiento», parte C).

Phone numbers of divers (profile, emergency contact, booking contact, information requests) and the WhatsApp
credentials of each centre are stored encrypted with AES-256-GCM (library `cryptography`). The key is in the server's
.env (WOD_DATA_KEY), never in the code. Searches never use the number in clear: they use an HMAC fingerprint of the
normalised number (fingerprint()).

Format of a stored value:  wdx1:<key id>:<base64url(nonce 12 bytes + ciphertext + tag)>
- <key id> is the first 8 hex characters of SHA-256 of the key, so a value can always be opened with the key that
  wrote it. Rotation: put the new key in WOD_DATA_KEY and the old one(s) in WOD_DATA_KEY_OLD (comma separated); values
  are opened with any of them and rewritten with the new one by scripts/seguridad/rotar_clave_datos.py.
- A value without the prefix is legacy plain text (before v50.47) and is returned as it is; the migration encrypts it.

Without WOD_DATA_KEY (development and the test environment only) the key is derived from WOD_SECRET_KEY. In production
the server refuses to start without WOD_DATA_KEY (see production_problems in app/server.py).
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import os
import re
import secrets

# Only for the FICTITIOUS data of the test environment («-pruebas» zip, WOD_DEMO_MODE=1): its database is built with
# this key so that it opens on any computer. Production refuses demo mode and requires its own WOD_DATA_KEY.
DEMO_DATA_KEY = 'worldives-pruebas:datos-ficticios-de-demostracion'
PREFIX = 'wdx1'          # personal data: opened automatically when read on the server (row_factory)
SECRET_PREFIX = 'wdk1'   # credentials (WhatsApp tokens…): opened only by the code that uses them, never by a SELECT
_CACHE: dict = {}


def _key_bytes(raw: str) -> bytes:
    """32 bytes from the configured value: base64 of 32 bytes, 64 hex characters, or any long secret (SHA-256)."""
    raw = (raw or '').strip()
    for decode in (lambda v: base64.urlsafe_b64decode(v + '=' * (-len(v) % 4)), bytes.fromhex):
        try:
            b = decode(raw)
            if len(b) == 32: return b
        except Exception:
            pass
    return hashlib.sha256(raw.encode('utf-8')).digest()


def configured() -> bool:
    return bool(os.environ.get('WOD_DATA_KEY', '').strip())


def _keys():
    """(current key, {key id: key}) — cached per value of the environment variables."""
    cur = os.environ.get('WOD_DATA_KEY', '').strip()
    old = os.environ.get('WOD_DATA_KEY_OLD', '').strip()
    secret = os.environ.get('WOD_SECRET_KEY', '').strip()
    cache_key = (cur, old, secret, os.environ.get('WOD_DEMO_MODE', ''))
    if cache_key in _CACHE: return _CACHE[cache_key]
    if not cur:
        # development and the test environment only (production refuses to start without WOD_DATA_KEY)
        if os.environ.get('WOD_DEMO_MODE', '').strip().lower() in ('1', 'true', 'yes', 'on'): cur = DEMO_DATA_KEY
        else: cur = 'derivada-de-WOD_SECRET_KEY:' + secret if secret else 'clave-de-desarrollo-sin-secreto'
    keys = {}
    current = _key_bytes(cur)
    for k in [cur] + [x for x in old.split(',') if x.strip()]:
        b = _key_bytes(k); keys[hashlib.sha256(b).hexdigest()[:8]] = b
    _CACHE.clear(); _CACHE[cache_key] = (current, keys)
    return current, keys


def key_id() -> str:
    current, _ = _keys()
    return hashlib.sha256(current).hexdigest()[:8]


def is_encrypted(value) -> bool:
    return isinstance(value, str) and value.startswith(PREFIX + ':')


def encrypt(value):
    """Plain text → wdx1:… (None and '' stay as they are; an encrypted value is not encrypted twice)."""
    if value is None or value == '' or is_encrypted(value): return value
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    current, _ = _keys()
    nonce = secrets.token_bytes(12)
    ct = AESGCM(current).encrypt(nonce, str(value).encode('utf-8'), PREFIX.encode())
    return f'{PREFIX}:{hashlib.sha256(current).hexdigest()[:8]}:' + base64.urlsafe_b64encode(nonce + ct).decode().rstrip('=')


def decrypt(value):
    """wdx1:… → plain text. Legacy plain text is returned as it is. A value that cannot be opened gives None (never
    the ciphertext: a broken value must not be shown or sent)."""
    if not is_encrypted(value): return value
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        _, kid, data = value.split(':', 2)
        _, keys = _keys()
        key = keys.get(kid)
        if not key: return None
        raw = base64.urlsafe_b64decode(data + '=' * (-len(data) % 4))
        return AESGCM(key).decrypt(raw[:12], raw[12:], PREFIX.encode()).decode('utf-8')
    except Exception:
        return None


def needs_rotation(value) -> bool:
    return (is_encrypted(value) or is_secret(value)) and value.split(':', 2)[1] != key_id()


def is_secret(value) -> bool:
    return isinstance(value, str) and value.startswith(SECRET_PREFIX + ':')


def encrypt_secret(value):
    """A credential: same AES-GCM, other prefix and associated data, so a row read from the database never carries
    it in clear by accident (decrypt_secret() is called only where the credential is used)."""
    if value is None or value == '': return None
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    current, _ = _keys()
    nonce = secrets.token_bytes(12)
    ct = AESGCM(current).encrypt(nonce, str(value).encode('utf-8'), SECRET_PREFIX.encode())
    return f'{SECRET_PREFIX}:{hashlib.sha256(current).hexdigest()[:8]}:' + base64.urlsafe_b64encode(nonce + ct).decode().rstrip('=')


def decrypt_secret(value):
    if not is_secret(value): return None
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        _, kid, data = value.split(':', 2)
        _, keys = _keys()
        key = keys.get(kid)
        if not key: return None
        raw = base64.urlsafe_b64decode(data + '=' * (-len(data) % 4))
        return AESGCM(key).decrypt(raw[:12], raw[12:], SECRET_PREFIX.encode()).decode('utf-8')
    except Exception:
        return None


def rotate(value):
    """Re-encrypts a value with the current key (rotation). Plain values are returned as they are."""
    if is_encrypted(value):
        clear = decrypt(value)
        return encrypt(clear) if clear is not None else value
    if is_secret(value):
        clear = decrypt_secret(value)
        return encrypt_secret(clear) if clear is not None else value
    return value


def row_factory(cursor, row):
    """sqlite3 row factory: values written with encrypt() come back in clear (a value that cannot be opened comes back
    as None, never as the ciphertext). Credentials (wdk1) are never opened here."""
    import sqlite3
    for v in row:
        if v.__class__ is str and v.startswith('wdx1:'):
            return sqlite3.Row(cursor, tuple(decrypt(x) if (x.__class__ is str and x.startswith('wdx1:')) else x for x in row))
    return sqlite3.Row(cursor, row)


def sql_encrypt(value):
    """SQL function wod_cifrar(x): the phone is encrypted before it reaches the table."""
    if value is None: return None
    v = str(value).strip()
    return encrypt(v) if v else None


def sql_fingerprint(value):
    """SQL function wod_huella(x): fingerprint of a (possibly encrypted) phone, for searches and duplicates."""
    if value is None: return None
    return fingerprint(decrypt(value) if is_encrypted(value) else value)


# ---------------------------------------------------------------------------------------------- phone numbers
E164 = re.compile(r'^\+[1-9]\d{7,14}$')


def normalize_phone(value):
    """The number in E.164 (+34600111222) when it has an international prefix, else None.
    Accepts spaces, dots, dashes, brackets and the 00 prefix (0034…)."""
    if not value: return None
    v = re.sub(r'[\s().\-/]', '', str(value))
    if v.startswith('00'): v = '+' + v[2:]
    return v if E164.match(v) else None


def phone_problem(value):
    """Text for the diver when the number cannot receive WhatsApp notices (empty when it is fine or empty)."""
    if not value or not str(value).strip(): return ''
    return '' if normalize_phone(value) else 'Revisa el número: sin prefijo no podrás recibir avisos por WhatsApp.'


def fingerprint(value):
    """HMAC-SHA256 of the normalised number (or of the digits when it has no prefix): for searches and uniqueness
    without storing the number in clear. None for an empty value."""
    if not value: return None
    v = normalize_phone(value) or re.sub(r'\D', '', str(value))
    if not v: return None
    current, _ = _keys()
    return hmac.new(hashlib.sha256(b'wod-huella:' + current).digest(), v.encode(), hashlib.sha256).hexdigest()[:40]


def mask_phone(value):
    """+34 6•• ••• •22 — to show that there is a number without showing it."""
    v = normalize_phone(value) or (str(value) if value else '')
    if len(v) < 6: return '•••'
    return v[:4] + '•' * max(3, len(v) - 6) + v[-2:]


def keyed_hash(label: str, value) -> str:
    """HMAC of an identifier (WhatsApp phone number id, business account id…) to find it without storing it in clear."""
    current, _ = _keys()
    return hmac.new(hashlib.sha256(b'wod-id:' + current).digest(), f'{label}:{value}'.encode(), hashlib.sha256).hexdigest()[:40]
