"""v50.55 · Encargo 2 (seguridad de la app WORLDIVES PRO): sessions per device.

- The app signs in like the web, and also gets a refresh token for its device. The phone keeps that token in the
  Android Keystore (iOS Keychain), protected by the fingerprint / Face ID / PIN of the app; the server keeps only its
  SHA-256.
- The session cookie of the app (the access token) lasts 15 minutes; the app renews it with the refresh token, which
  the server can revoke at any time. A device session lasts 30 days at most: then the password is asked again.
- «Dispositivos conectados»: every open web session and every app device, with its type, system, last activity and
  approximate city (only when the reverse proxy sends it: no IP geolocation inside the server).
- A sign-in from a device (or browser) this account never used sends an e-mail.

Here: the pure rules (no database). The routes and the tables are in server.py."""
from __future__ import annotations

import hashlib
import re
import secrets

ACCESS_TTL = 15 * 60                 # the app's session cookie (access token)
REFRESH_MAX_DAYS = 30                # a device session, at most
REFRESH_TTL = REFRESH_MAX_DAYS * 86400
KNOWN_COOKIE = 'wd_dev'              # a random id of the browser, to know if it is a new device (not a secret)
KNOWN_COOKIE_DAYS = 400
PLATFORMS = ('android', 'ios', 'web')
APP_MARK = 'WorldivesApp/'


def new_token() -> str:
    return secrets.token_urlsafe(32)


def token_hash(token: str) -> str:
    return hashlib.sha256(str(token or '').encode()).hexdigest()


def is_app(user_agent: str) -> bool:
    return APP_MARK in (user_agent or '')


def _clean(v, n):
    return re.sub(r'[^\w .,+()/:-]', '', str(v or ''))[:n].strip()


def clean_device(raw) -> dict | None:
    """What the app says about itself when it signs in (nothing secret): platform, model, system, app version and a
    random id of the installation (device_key, at least 16 characters)."""
    if not isinstance(raw, dict): return None
    key = re.sub(r'[^A-Za-z0-9_-]', '', str(raw.get('device_key') or ''))[:80]
    if len(key) < 16: return None
    platform = str(raw.get('platform') or '').lower()
    return {'platform': platform if platform in PLATFORMS else 'android', 'model': _clean(raw.get('model'), 60), 'os': _clean(raw.get('os'), 40),
            'app_version': _clean(raw.get('app_version'), 20), 'device_key': key}


def browser_label(user_agent: str) -> tuple[str, str]:
    """(device type, system) of a web session from its User-Agent."""
    ua = user_agent or ''
    if is_app(ua):
        system = 'Android' if 'Android' in ua else ('iOS' if any(k in ua for k in ('iPhone', 'iPad')) else '')
        return 'App WORLDIVES', system
    browser = next((n for k, n in (('Edg/', 'Edge'), ('OPR/', 'Opera'), ('Firefox/', 'Firefox'), ('Chrome/', 'Chrome'), ('Safari/', 'Safari')) if k in ua), 'Navegador')
    system = next((n for k, n in (('Android', 'Android'), ('iPhone', 'iPhone'), ('iPad', 'iPad'), ('Windows', 'Windows'), ('Mac OS', 'Mac'), ('Linux', 'Linux')) if k in ua), '')
    kind = 'Móvil' if system in ('Android', 'iPhone') or 'Mobile' in ua else ('Tableta' if system == 'iPad' else 'Ordenador')
    return f'{browser} · {kind}', system


def app_label(dev) -> tuple[str, str]:
    platform = (dev.get('platform') if isinstance(dev, dict) else dev['platform']) or 'android'
    model = (dev.get('model') if isinstance(dev, dict) else dev['model']) or ''
    os_ = (dev.get('os') if isinstance(dev, dict) else dev['os']) or ''
    system = {'android': 'Android', 'ios': 'iOS'}.get(platform, '')
    return ('App WORLDIVES' + (f' · {model}' if model else '')), (f'{system} {os_}'.strip() if system else os_)


def city_from_headers(headers, header_name: str) -> str:
    """The approximate city when the reverse proxy adds it (WOD_GEOIP_HEADER, e.g. «X-Geo-City»). Empty otherwise."""
    if not header_name: return ''
    v = headers.get(header_name) or ''
    return re.sub(r'[^\w .,\'()-]', '', v)[:60].strip()
