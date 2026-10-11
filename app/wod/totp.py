"""Two-step verification with time-based one-time codes (RFC 6238, the codes of Google Authenticator,
Microsoft Authenticator, Aegis, 1Password…). Standard library only."""
from __future__ import annotations

import base64
import hashlib
import hmac
import secrets
import struct
import time
from urllib.parse import quote

STEP = 30
DIGITS = 6


def new_secret() -> str:
    return base64.b32encode(secrets.token_bytes(20)).decode().rstrip('=')


def _key(secret: str) -> bytes:
    s = secret.strip().replace(' ', '').upper()
    return base64.b32decode(s + '=' * (-len(s) % 8))


def code_at(secret: str, step: int) -> str:
    digest = hmac.new(_key(secret), struct.pack('>Q', step), hashlib.sha1).digest()
    off = digest[-1] & 0x0F
    num = struct.unpack('>I', digest[off:off + 4])[0] & 0x7FFFFFFF
    return str(num % 10 ** DIGITS).zfill(DIGITS)


def current_step(at: float | None = None) -> int:
    return int((time.time() if at is None else at) // STEP)


def verify(secret: str, code: str, last_step: int | None = None, window: int = 1, at: float | None = None):
    """Returns the time step of a valid code (to remember it and refuse its reuse), or None."""
    code = ''.join(ch for ch in str(code or '') if ch.isdigit())
    if len(code) != DIGITS or not secret: return None
    now = current_step(at)
    for step in range(now - window, now + window + 1):
        if last_step is not None and step <= int(last_step): continue  # a code is never accepted twice
        if hmac.compare_digest(code_at(secret, step), code): return step
    return None


def otpauth_uri(secret: str, account: str, issuer: str = 'WORLDIVES DISCOVERY') -> str:
    return f'otpauth://totp/{quote(issuer)}:{quote(account)}?secret={secret}&issuer={quote(issuer)}&algorithm=SHA1&digits={DIGITS}&period={STEP}'


def recovery_codes(n: int = 8) -> list[str]:
    return ['-'.join(secrets.token_hex(2).upper() for _ in range(3)) for _ in range(n)]


def hash_recovery(code: str) -> str:
    return hashlib.sha256(code.strip().upper().replace(' ', '').encode()).hexdigest()
