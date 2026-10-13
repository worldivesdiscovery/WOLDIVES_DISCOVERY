"""Push notifications to the app (v50.49) through Firebase Cloud Messaging (HTTP v1 API).

Off until the owner creates the Firebase project of WORLDIVES and writes in the server's .env:
    WOD_FCM_PROJECT_ID=<id of the Firebase project>
    WOD_FCM_CREDENTIALS=/a/path/outside/the/repository/firebase-service-account.json
Nothing of that goes in the code, the repository or the zips. While it is off, the app asks for nothing and registers
nothing; the server keeps working exactly as before (emails and the in-app notices).

What a push says is the subject of the email that goes with it, already in the person's language; tapping it opens the
booking in the app. Only the standard library and «cryptography» (already required since v50.47) are used.
"""
import base64
import json
import time
import urllib.error
import urllib.parse
import urllib.request

from . import config as wcfg

_TOKEN = {'v': None, 'exp': 0}


def enabled() -> bool:
    return bool(wcfg.env('WOD_FCM_PROJECT_ID') and wcfg.env('WOD_FCM_CREDENTIALS'))


def _b64(b: bytes) -> str:
    return base64.urlsafe_b64encode(b).rstrip(b'=').decode()


def _credentials():
    with open(wcfg.env('WOD_FCM_CREDENTIALS'), encoding='utf-8') as f:
        return json.load(f)


def _access_token():
    """OAuth 2 token of the service account (JWT signed with its key, RS256), kept until a minute before it expires."""
    if _TOKEN['v'] and _TOKEN['exp'] > time.time() + 60: return _TOKEN['v']
    from cryptography.hazmat.primitives import hashes, serialization
    from cryptography.hazmat.primitives.asymmetric import padding
    cred = _credentials(); now = int(time.time())
    uri = cred.get('token_uri') or 'https://oauth2.googleapis.com/token'
    head = _b64(json.dumps({'alg': 'RS256', 'typ': 'JWT'}).encode())
    claims = _b64(json.dumps({'iss': cred['client_email'], 'scope': 'https://www.googleapis.com/auth/firebase.messaging', 'aud': uri,
                              'iat': now, 'exp': now + 3600}).encode())
    key = serialization.load_pem_private_key(cred['private_key'].encode(), password=None)
    sig = _b64(key.sign(f'{head}.{claims}'.encode(), padding.PKCS1v15(), hashes.SHA256()))
    body = urllib.parse.urlencode({'grant_type': 'urn:ietf:params:oauth:grant-type:jwt-bearer', 'assertion': f'{head}.{claims}.{sig}'}).encode()
    req = urllib.request.Request(uri, data=body, headers={'Content-Type': 'application/x-www-form-urlencoded'})
    with urllib.request.urlopen(req, timeout=15) as r:
        d = json.loads(r.read())
    _TOKEN.update(v=d['access_token'], exp=now + int(d.get('expires_in', 3600)))
    return _TOKEN['v']


def send(token, title, body, data=None) -> str:
    """'ok', 'gone' (the phone uninstalled the app or the token is not valid any more) or 'retry'."""
    base = wcfg.env('WOD_FCM_API_BASE') or 'https://fcm.googleapis.com'
    msg = {'message': {'token': token, 'notification': {'title': str(title)[:120], 'body': str(body)[:200]},
                       'data': {k: str(v) for k, v in (data or {}).items()},
                       'android': {'priority': 'high', 'notification': {'channel_id': 'avisos'}}}}
    try:
        req = urllib.request.Request(f"{base}/v1/projects/{urllib.parse.quote(wcfg.env('WOD_FCM_PROJECT_ID'))}/messages:send", data=json.dumps(msg).encode(),
                                     headers={'Authorization': 'Bearer ' + _access_token(), 'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=15):
            return 'ok'
    except urllib.error.HTTPError as e:
        txt = e.read().decode('utf-8', 'replace')
        if e.code == 404 or 'UNREGISTERED' in txt: return 'gone'
        return 'retry'
    except (OSError, ValueError, KeyError):
        return 'retry'
