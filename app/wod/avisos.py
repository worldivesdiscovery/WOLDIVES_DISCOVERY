"""Texts and signed links of the mass notices of the centres (v50.47, encargo «avisos masivos», partes D y E).

The notice engine (queue, transaction, sending, retries) lives in app/server.py; this module holds what does not
need the database: the texts in the language of each diver, the parameters of the WhatsApp templates and the links
that open one booking for a limited time.
"""
from __future__ import annotations

import base64
import hashlib
import hmac
import json
import re
import time
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data' / 'whatsapp_plantillas.json'
LANGS = ('es', 'en', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'zh')
KINDS = ('slot_cancelled', 'slot_changed', 'reminder')
REASONS = ('weather', 'sea', 'boat', 'other')
EVENT_CODES = {'slot_cancelled': 'c', 'slot_changed': 'm', 'reminder': 'r'}
NOTE_MAX = 200
_CACHE: dict = {}


def data() -> dict:
    if 'd' not in _CACHE: _CACHE['d'] = json.loads(DATA.read_text(encoding='utf-8'))
    return _CACHE['d']


def lang_of(lang) -> str:
    return lang if lang in LANGS else 'es'


def text(key, lang, **kw) -> str:
    t = data()['textos'].get(key, {})
    s = t.get(lang_of(lang)) or t.get('es') or key
    for k, v in kw.items(): s = s.replace('{' + k + '}', str(v))
    return s


def clean_note(note) -> str:
    """A note of the centre: plain text, one line, at most 200 characters (no HTML, no links that look like ours)."""
    s = re.sub(r'<[^>]*>', '', str(note or ''))
    s = re.sub(r'[\x00-\x1f\x7f]+', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    if len(s) > NOTE_MAX: raise ValueError(f'La nota puede tener como máximo {NOTE_MAX} caracteres.')
    return s


def reason_text(reason, lang) -> str:
    return text('reason_' + (reason if reason in REASONS else 'other'), lang)


def money_text(policy, paid, amount_text, lang) -> str:
    """What happens with the money of one booking, in the diver's language."""
    if policy == 'refund': return text('money_refund', lang, amount=amount_text) if paid > 0 else text('money_none', lang)
    return text('money_choice', lang, amount=amount_text) if paid > 0 else text('money_choice_free', lang)


def change_text(lang, new_time=None, new_point=None) -> str:
    parts = []
    if new_time: parts.append(text('change_time', lang, time=new_time))
    if new_point: parts.append(text('change_point', lang, point=new_point))
    return ', '.join(parts)


def body(kind, lang, params) -> str:
    """The text of a template with its variables filled (the preview shows exactly what the diver receives)."""
    s = data()[kind]['body'][lang_of(lang)]
    for i, v in enumerate(params, 1): s = s.replace('{{%d}}' % i, str(v))
    return s


def button_label(kind, lang) -> str:
    return data()[kind]['button'][lang_of(lang)]


def params(kind, lang, *, center, date, time_, reason=None, note=None, money=None, change=None, point=None, bring=None):
    """Variables of each template, in order. The note of the centre goes with the reason (one variable)."""
    lang = lang_of(lang)
    if kind == 'slot_cancelled':
        r = reason_text(reason, lang) + (f' ({note})' if note else '')
        return [center, date, time_, r, money or '']
    if kind == 'slot_changed':
        return [center, date, (change or '') + (f'. {text("note", lang, note=note)}' if note else '')]
    return [center, date, time_, point or '—', bring or text('bring_default', lang)]


def whatsapp_safe(value) -> str:
    """Meta refuses template variables with new lines, tabs or more than four spaces in a row."""
    s = re.sub(r'[\r\n\t]+', ' ', str(value or ''))
    return re.sub(r' {4,}', '   ', s).strip() or '—'


# ------------------------------------------------------------------------------------------------ signed links
def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).decode().rstrip('=')


def _b36(n: int) -> str:
    chars = '0123456789abcdefghijklmnopqrstuvwxyz'; out = ''
    n = int(n)
    while True:
        n, r = divmod(n, 36); out = chars[r] + out
        if not n: return out


def sign_link(secret: str, booking_id: int, kind: str, expires_at: int) -> str:
    """A token that opens ONLY this booking, only for this notice and only until expires_at (unix time)."""
    payload = f'{_b36(booking_id)}.{EVENT_CODES[kind]}.{_b36(expires_at)}'
    mac = hmac.new(hashlib.sha256(b'wod-enlace:' + secret.encode()).digest(), payload.encode(), hashlib.sha256).digest()[:16]
    return payload + '.' + _b64(mac)


def verify_link(secret: str, token: str, now=None):
    """(booking id, kind) when the token is genuine and not expired, else None."""
    try:
        b36, code, exp36, mac = str(token or '').split('.')
        payload = f'{b36}.{code}.{exp36}'
        good = _b64(hmac.new(hashlib.sha256(b'wod-enlace:' + secret.encode()).digest(), payload.encode(), hashlib.sha256).digest()[:16])
        if not hmac.compare_digest(good, mac): return None
        if int(exp36, 36) < int(now if now is not None else time.time()): return None
        kind = next((k for k, c in EVENT_CODES.items() if c == code), None)
        return (int(b36, 36), kind) if kind else None
    except (ValueError, TypeError):
        return None
