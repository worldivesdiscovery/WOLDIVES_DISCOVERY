"""WhatsApp Business Platform (Cloud API) for each centre (v50.47, encargo «avisos y aislamiento», parte D).

Only Meta's official API is used: never automated personal WhatsApp or unofficial libraries.

- Every centre connects ITS OWN WhatsApp Business number with Meta's Embedded Signup. With coexistence, the number
  keeps working in the WhatsApp Business app: the centre's reception answers there, outside WORLDIVES.
- WORLDIVES stores, per centre and encrypted: the WABA id, the phone number id, the visible number and the token.
  The token is never returned to the web.
- Notices are sent with «utility» templates approved by Meta. The templates are created in each centre's WABA when it
  connects (create_templates), in the 9 languages of the site.
- Webhooks: only message statuses (sent, delivered, read, failed) and template statuses. The text of the divers'
  replies is never stored.

Configuration (server .env only): WHATSAPP_ENABLED, WHATSAPP_APP_ID, WHATSAPP_APP_SECRET, WHATSAPP_VERIFY_TOKEN,
WHATSAPP_CONFIG_ID, optional WHATSAPP_GRAPH_VERSION and WHATSAPP_GRAPH_BASE (tests: a local simulator).
"""
from __future__ import annotations

import hashlib
import hmac
import json
import os
import urllib.error
import urllib.parse
import urllib.request

# Meta language codes of the 9 languages of the site
META_LANG = {'es': 'es', 'en': 'en', 'fr': 'fr', 'de': 'de', 'it': 'it', 'pt': 'pt_PT', 'nl': 'nl', 'pl': 'pl', 'zh': 'zh_CN'}
# Countries where Meta does not offer coexistence with the WhatsApp Business app (third-party sources, Oct 2026; Meta
# decides number by number when connecting). The owner can change the list with WHATSAPP_COEX_UNAVAILABLE.
COEX_UNAVAILABLE_DEFAULT = 'NG,ZA'
SEND_PER_SECOND = 10          # conservative: a coexistence number allows about 20 messages per second


def env(name, default=''):
    return (os.environ.get(name) or default).strip()


def enabled() -> bool:
    return env('WHATSAPP_ENABLED') in ('1', 'true', 'yes', 'on') and bool(env('WHATSAPP_APP_ID') and env('WHATSAPP_APP_SECRET'))


def graph_base() -> str:
    return (env('WHATSAPP_GRAPH_BASE') or 'https://graph.facebook.com').rstrip('/') + '/' + (env('WHATSAPP_GRAPH_VERSION') or 'v23.0')


def coex_unavailable(country_iso: str) -> bool:
    lst = {c.strip().upper() for c in (env('WHATSAPP_COEX_UNAVAILABLE', COEX_UNAVAILABLE_DEFAULT)).split(',') if c.strip()}
    return bool(country_iso) and country_iso.upper() in lst


class GraphError(Exception):
    """An answer of the Graph API with an error. `code` is Meta's error code (190 = token expired or revoked)."""
    def __init__(self, message, code=None, status=None, temporary=False):
        super().__init__(message); self.code = code; self.status = status; self.temporary = temporary


# Error codes of the Cloud API that are worth retrying later (rate limits, temporary problems of Meta)
TEMPORARY_CODES = {1, 2, 4, 17, 341, 80007, 130429, 131000, 131016, 131056, 133004, 133005}
TOKEN_CODES = {190, 102, 463, 467}


def _request(method, path, token=None, params=None, body=None, timeout=20):
    url = graph_base() + '/' + path.lstrip('/')
    if params: url += '?' + urllib.parse.urlencode(params)
    data = json.dumps(body).encode() if body is not None else None
    req = urllib.request.Request(url, data=data, method=method)
    if token: req.add_header('Authorization', 'Bearer ' + token)
    if data is not None: req.add_header('Content-Type', 'application/json')
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode() or '{}')
    except urllib.error.HTTPError as e:
        try: err = json.loads(e.read().decode() or '{}').get('error') or {}
        except Exception: err = {}
        code = err.get('code')
        raise GraphError(err.get('message') or f'HTTP {e.code}', code, e.code, temporary=(e.code >= 500 or code in TEMPORARY_CODES)) from None
    except (urllib.error.URLError, TimeoutError, OSError) as e:
        raise GraphError(f'Sin conexión con Meta: {e}', None, None, temporary=True) from None


# ------------------------------------------------------------------------------------------ connection (D.1)
def exchange_code(code: str) -> str:
    """Embedded Signup gives the browser a code; the server exchanges it for the business token of that centre."""
    r = _request('GET', 'oauth/access_token', params={'client_id': env('WHATSAPP_APP_ID'), 'client_secret': env('WHATSAPP_APP_SECRET'), 'code': code})
    tok = r.get('access_token')
    if not tok: raise GraphError('Meta no ha devuelto la autorización.')
    return tok


def granted_wabas(token: str) -> set:
    """The WhatsApp Business accounts the centre has just authorised for this token (debug_token, granular scopes)."""
    app_token = env('WHATSAPP_APP_ID') + '|' + env('WHATSAPP_APP_SECRET')
    r = _request('GET', 'debug_token', params={'input_token': token, 'access_token': app_token})
    data = r.get('data') or {}
    if str(data.get('app_id') or '') != env('WHATSAPP_APP_ID') or not data.get('is_valid'): raise GraphError('La autorización de Meta no es válida para WORLDIVES.')
    out = set()
    for s in data.get('granular_scopes') or []:
        if s.get('scope') in ('whatsapp_business_management', 'whatsapp_business_messaging'):
            out.update(str(x) for x in (s.get('target_ids') or []))
    return out


def phone_numbers(token: str, waba_id: str) -> list:
    r = _request('GET', f'{waba_id}/phone_numbers', token, params={'fields': 'id,display_phone_number,verified_name,quality_rating'})
    return r.get('data') or []


def subscribe_app(token: str, waba_id: str):
    _request('POST', f'{waba_id}/subscribed_apps', token, body={})


def register_number(token: str, phone_number_id: str, pin: str):
    """Only for numbers that are NOT shared with the WhatsApp Business app (coexistence numbers are already registered)."""
    _request('POST', f'{phone_number_id}/register', token, body={'messaging_product': 'whatsapp', 'pin': pin})


def verify_connection(token: str, waba_id: str, phone_number_id: str) -> dict:
    """D.1.5: the phone number belongs to the WABA and the WABA is one the centre has just authorised. Returns the
    number's data (display number, verified name) or raises GraphError: nothing is stored when it does not match."""
    wabas = granted_wabas(token)
    if not waba_id and len(wabas) == 1: waba_id = next(iter(wabas))
    if not waba_id or str(waba_id) not in wabas: raise GraphError('La cuenta de WhatsApp Business no es la que acabas de autorizar.')
    nums = phone_numbers(token, waba_id)
    if not phone_number_id and len(nums) == 1: phone_number_id = str(nums[0].get('id'))
    match = [n for n in nums if str(n.get('id')) == str(phone_number_id)]
    if not match: raise GraphError('Ese número no pertenece a la cuenta de WhatsApp Business autorizada.')
    n = match[0]
    return {'waba_id': str(waba_id), 'phone_number_id': str(phone_number_id), 'display_number': n.get('display_phone_number') or '',
            'verified_name': n.get('verified_name') or ''}


# ------------------------------------------------------------------------------------------- templates (D.2.2)
TEMPLATE_NAMES = {'slot_cancelled': 'worldives_salida_cancelada', 'slot_changed': 'worldives_cambio_salida', 'reminder': 'worldives_recordatorio'}


def template_payloads(texts: dict, site_url: str) -> list:
    """The templates to create in a centre's WABA: 3 notices × 9 languages, category UTILITY.
    texts: {event: {lang: body text with {{1}}… placeholders, 'button': {lang: label}, 'map_button': {lang: label}}}"""
    out = []
    for event, name in TEMPLATE_NAMES.items():
        t = texts[event]
        for lang, code in META_LANG.items():
            buttons = [{'type': 'URL', 'text': t['button'][lang], 'url': site_url.rstrip('/') + '/r/{{1}}', 'example': [site_url.rstrip('/') + '/r/ejemplo']}]
            if event == 'reminder':
                buttons.append({'type': 'URL', 'text': t['map_button'][lang], 'url': 'https://www.google.com/maps/search/?api=1&query={{1}}',
                                'example': ['https://www.google.com/maps/search/?api=1&query=Xabia']})
            out.append({'name': name, 'language': code, 'category': 'UTILITY',
                        'components': [{'type': 'BODY', 'text': t['body'][lang], 'example': {'body_text': [t['example']]}},
                                       {'type': 'BUTTONS', 'buttons': buttons}]})
    return out


def create_templates(token: str, waba_id: str, payloads: list) -> dict:
    """Creates (or finds already created) templates. Returns {(name, language): status}."""
    status = {}
    for p in payloads:
        key = f"{p['name']}:{p['language']}"
        try:
            r = _request('POST', f'{waba_id}/message_templates', token, body=p)
            status[key] = (r.get('status') or 'PENDING').upper()
        except GraphError as e:
            # 2388023/2388024: a template with that name and language already exists (connecting again)
            status[key] = 'EXISTS' if e.code in (100, 2388023, 2388024) else 'ERROR'
    return status


def template_statuses(token: str, waba_id: str) -> dict:
    r = _request('GET', f'{waba_id}/message_templates', token, params={'fields': 'name,language,status', 'limit': 200})
    return {f"{t.get('name')}:{t.get('language')}": (t.get('status') or '').upper() for t in r.get('data') or []}


# ------------------------------------------------------------------------------------------------- send (D.2)
def send_template(token: str, phone_number_id: str, to_e164: str, name: str, lang: str, body_params: list, button_params: list) -> str:
    """Sends one template message. Returns the wamid. Raises GraphError (temporary or not)."""
    comps = [{'type': 'body', 'parameters': [{'type': 'text', 'text': str(p)} for p in body_params]}]
    for i, bp in enumerate(button_params):
        comps.append({'type': 'button', 'sub_type': 'url', 'index': str(i), 'parameters': [{'type': 'text', 'text': str(bp)}]})
    body = {'messaging_product': 'whatsapp', 'recipient_type': 'individual', 'to': to_e164.lstrip('+'), 'type': 'template',
            'template': {'name': name, 'language': {'code': META_LANG.get(lang, 'es')}, 'components': comps}}
    r = _request('POST', f'{phone_number_id}/messages', token, body=body)
    msgs = r.get('messages') or []
    if not msgs or not msgs[0].get('id'): raise GraphError('Meta no ha devuelto el identificador del mensaje.', temporary=True)
    return msgs[0]['id']


# ------------------------------------------------------------------------------------------------ webhooks (D.2.6)
def valid_signature(raw: bytes, header: str) -> bool:
    """X-Hub-Signature-256: sha256=<hex HMAC-SHA256 of the raw body with the app secret>."""
    secret = env('WHATSAPP_APP_SECRET')
    if not secret or not header or not header.startswith('sha256='): return False
    expected = hmac.new(secret.encode(), raw, hashlib.sha256).hexdigest()
    return hmac.compare_digest(expected, header[7:].strip())


def statuses_of(payload: dict):
    """(phone_number_id, wamid, status, timestamp, error code) for every message status of the webhook. Incoming
    messages (the divers' replies) are deliberately ignored: their text is never read or stored."""
    for entry in payload.get('entry') or []:
        for ch in entry.get('changes') or []:
            if ch.get('field') != 'messages': continue
            v = ch.get('value') or {}
            pnid = str((v.get('metadata') or {}).get('phone_number_id') or '')
            for s in v.get('statuses') or []:
                errs = s.get('errors') or []
                yield pnid, str(s.get('id') or ''), str(s.get('status') or ''), str(s.get('timestamp') or ''), (errs[0].get('code') if errs else None)


def template_updates_of(payload: dict):
    """(waba_id, template name, language, status) of message_template_status_update events."""
    for entry in payload.get('entry') or []:
        waba = str(entry.get('id') or '')
        for ch in entry.get('changes') or []:
            if ch.get('field') != 'message_template_status_update': continue
            v = ch.get('value') or {}
            yield waba, str(v.get('message_template_name') or ''), str(v.get('message_template_language') or ''), str(v.get('event') or '').upper()
