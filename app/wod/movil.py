"""What the server does only for the mobile app (v50.48, encargo «App móvil en 3 módulos», Tanda 1). Pure helpers:
app.server calls them and keeps the database and HTTP parts.

- The two apps and their own link schemes, used to come back to the app after paying in the browser tab.
- The date window of «Salidas con plazas cerca de ti» (Inicio of the diver).
- WORLDIVES Pruebas only (test environment): the bug reports of the testers («Reportar fallo»).
"""
from __future__ import annotations

import base64
import datetime as dt
import html
import json
import re
import secrets
from pathlib import Path
from urllib.parse import urlencode

# The two apps (applicationId on Android); each opens links with its own scheme: com.worldives.app://pago?…
SCHEMES = ('com.worldives.app', 'com.worldives.app.pruebas')
APP_NAMES = {'com.worldives.app': 'WORLDIVES', 'com.worldives.app.pruebas': 'WORLDIVES Pruebas'}
TEST_ACCOUNT_RE = re.compile(r'[a-z0-9]+\.prueba')   # the fixed accounts of the test environment (never in production)


def app_scheme(value):
    """The scheme of one of our apps, or None for anything else (never redirect to a scheme we do not own)."""
    v = (value or '').strip()
    return v if v in SCHEMES else None


def return_urls(base, scheme, booking_id=None):
    """Stripe success and cancel addresses for a payment started in the app: a page of this server that sends the
    phone back into the app (/app/vuelta), because Stripe only redirects to web addresses."""
    ok = f'{base}/app/vuelta?' + urlencode({'esquema': scheme}) + '&session_id={CHECKOUT_SESSION_ID}'
    ko = f'{base}/app/vuelta?' + urlencode({'esquema': scheme, 'pago': 'cancelado', **({'reserva': booking_id} if booking_id else {})})
    return ok, ko


def return_page(scheme, params):
    """The small page shown in the browser tab after paying: it opens the app (scheme://pago?…) and, if the browser
    does not do it by itself, a big button does. No script (the site's CSP forbids inline scripts)."""
    keep = {k: v for k, v in params.items() if k in ('session_id', 'pago', 'reserva') and re.fullmatch(r'[A-Za-z0-9_\-]{1,200}', v or '')}
    target = f'{scheme}://pago?' + urlencode(keep)
    intent = f'intent://pago?{urlencode(keep)}#Intent;scheme={scheme};package={scheme};end'
    name = APP_NAMES.get(scheme, 'WORLDIVES')
    t = html.escape(target, quote=True); i = html.escape(intent, quote=True)
    return f'''<!doctype html><html lang="es"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<meta http-equiv="refresh" content="0;url={t}"><title>Volver a {html.escape(name)}</title></head>
<body style="margin:0;background:#011C3C;color:#fff;font:17px/1.45 system-ui,sans-serif;display:grid;place-items:center;min-height:100vh;text-align:center">
<main style="padding:24px;max-width:420px"><p style="font-size:22px;font-weight:700;margin:0 0 8px">{'Pago cancelado' if keep.get('pago') == 'cancelado' else 'Pago recibido'}</p>
<p style="margin:0 0 24px;opacity:.85">Vuelve a la app para ver tu reserva.</p>
<a href="{i}" style="display:block;background:#1CA5C7;color:#011C3C;text-decoration:none;font-weight:700;padding:16px;border-radius:12px">Volver a {html.escape(name)}</a></main></body></html>'''


def departures_window(when, today=None):
    """(first day, last day) of «Salidas con plazas cerca de ti»: hoy, manana, finde (the next Saturday and Sunday,
    or this one if it is already the weekend) or, by default, the next 14 days."""
    today = today or dt.date.today()
    if when == 'hoy': return today, today
    if when == 'manana': return today + dt.timedelta(days=1), today + dt.timedelta(days=1)
    if when == 'finde':
        sat = today + dt.timedelta(days=(5 - today.weekday()) % 7)
        if today.weekday() == 6: sat = today - dt.timedelta(days=1)
        return max(sat, today), sat + dt.timedelta(days=1)
    return today, today + dt.timedelta(days=14)


# ---------------------------------------------------------------- «Reportar fallo» (WORLDIVES Pruebas only)
MAX_REPORT_IMAGE = 1_500_000
_DATA_URL = re.compile(r'data:image/(jpeg|png);base64,([A-Za-z0-9+/=]+)$')


def clean_report(data):
    """The fields of a bug report, trimmed; the screenshot decoded (JPEG or PNG, at most 1.5 MB) or None."""
    def txt(k, n): return str(data.get(k) or '').strip()[:n]
    report = {'texto': txt('texto', 3000), 'pantalla': txt('pantalla', 300), 'version': txt('version', 120), 'movil': txt('movil', 300),
              'idioma': txt('idioma', 10), 'hora_movil': txt('hora', 40)}
    image = None
    m = _DATA_URL.match(str(data.get('captura') or ''))
    if m:
        try:
            raw = base64.b64decode(m.group(2), validate=True)
        except ValueError:
            raw = b''
        if raw and len(raw) <= MAX_REPORT_IMAGE and (raw[:3] == b'\xff\xd8\xff' or raw[:8] == b'\x89PNG\r\n\x1a\n'):
            image = (raw, 'jpg' if m.group(1) == 'jpeg' else 'png')
    if not report['texto'] and not image: raise ValueError('Escribe qué ha pasado o adjunta la captura.')
    return report, image


def save_report(folder, report, image, user_label):
    """Saves the report as JSON (and its screenshot) in the test folder; returns its name."""
    folder = Path(folder); folder.mkdir(parents=True, exist_ok=True)
    name = 'fallo-' + dt.datetime.now().strftime('%Y%m%d-%H%M%S') + '-' + secrets.token_hex(3)
    report = dict(report, recibido=dt.datetime.now().isoformat(timespec='seconds'), cuenta=user_label)
    if image:
        (folder / f'{name}.{image[1]}').write_bytes(image[0]); report['captura'] = f'{name}.{image[1]}'
    (folder / f'{name}.json').write_text(json.dumps(report, ensure_ascii=False, indent=1), encoding='utf-8')
    return name
