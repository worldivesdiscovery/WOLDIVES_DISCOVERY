"""Reading a page or an image from another website, safely (v50.50, vídeos enlazados y vida marina).

The server only fetches what a person asked for while adding a video link or choosing a species photo: the video's
public data (oEmbed or the page's preview tags), its preview image and Wikimedia Commons. Every request:
  - goes only to https:// on the standard port, never with a user or password in the address;
  - is refused when the name resolves to a private, local or reserved address (nothing inside the server's network);
  - follows at most 3 redirections, checking each one again;
  - stops after a few seconds and after a size limit, and only accepts the expected type of content.

For the automatic tests, WOD_MEDIA_FETCH_BASE can send every request to a local stand-in of the platforms
(http://127.0.0.1:<port>); it is ignored for any other address, so it can never open the server's network.
"""
from __future__ import annotations

import ipaddress
import socket
import sys
import urllib.error
import urllib.parse
import urllib.request

from . import config as wcfg

UA = 'WORLDIVES-DISCOVERY/1.0 (vídeos y vida marina de los puntos de buceo)'
TIMEOUT = 8
MAX_REDIRECTS = 3


class FetchError(Exception):
    """The other website could not be read (down, too slow, too big, wrong type or not allowed)."""


def _test_base() -> str | None:
    base = wcfg.env('WOD_MEDIA_FETCH_BASE').rstrip('/')
    p = urllib.parse.urlparse(base)
    return base if p.scheme == 'http' and p.hostname in ('127.0.0.1', 'localhost') else None


def public_host(host: str) -> bool:
    """True when every address of the name is a public one (not loopback, private, link-local, reserved…)."""
    try:
        infos = socket.getaddrinfo(host, 443, proto=socket.IPPROTO_TCP)
    except (socket.gaierror, UnicodeError, OSError):
        return False
    if not infos: return False
    for info in infos:
        try:
            ip = ipaddress.ip_address(info[4][0].split('%')[0])
        except ValueError:
            return False
        if not ip.is_global or ip.is_multicast: return False
    return True


def check_url(url: str) -> urllib.parse.ParseResult:
    p = urllib.parse.urlparse(url)
    if p.scheme != 'https' or not p.hostname or p.username or p.password or (p.port not in (None, 443)):
        raise FetchError('Dirección no permitida.')
    try:
        ipaddress.ip_address(p.hostname)
        raise FetchError('Dirección no permitida.')
    except ValueError:
        pass
    return p


class _NoRedirect(urllib.request.HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


_OPENER = urllib.request.build_opener(_NoRedirect)


def open_once(req, timeout: float):
    """urlopen for the services WORLDIVES calls itself (geocoder, satellite, WhatsApp, push): a redirection is an
    error, so a key or a token is never sent to another address (ASVS 5.0 V15.3.2)."""
    return _OPENER.open(req, timeout=timeout)


def fetch(url: str, *, kinds: tuple[str, ...], max_bytes: int, accept: str = '*/*') -> tuple[str, str, bytes]:
    """GET url and return (final address, content type, body). kinds: accepted content types (prefixes)."""
    test = _test_base()
    current = url
    for _ in range(MAX_REDIRECTS + 1):
        if test:
            req = urllib.request.Request(test + '/fetch?url=' + urllib.parse.quote(current, safe=''), headers={'User-Agent': UA, 'Accept': accept})
        else:
            p = check_url(current)
            if not public_host(p.hostname): raise FetchError('Dirección no permitida.')
            req = urllib.request.Request(current, headers={'User-Agent': UA, 'Accept': accept, 'Accept-Language': 'es,en;q=0.8'})
        try:
            resp = _OPENER.open(req, timeout=TIMEOUT)
        except urllib.error.HTTPError as e:
            if e.code in (301, 302, 303, 307, 308) and e.headers.get('Location'):
                current = urllib.parse.urljoin(current, e.headers['Location']); continue
            raise FetchError(f'La web respondió {e.code}.') from None
        except (urllib.error.URLError, OSError, ValueError) as e:
            sys.stderr.write(f'[remoto] {urllib.parse.urlparse(current).hostname}: {type(e).__name__}: {str(e)[:160]}\n')   # ASVS V16.3.4
            raise FetchError('No se ha podido conectar con la web.') from None
        with resp:
            ctype = (resp.headers.get('Content-Type') or '').split(';')[0].strip().lower()
            if kinds and not any(ctype.startswith(k) for k in kinds): raise FetchError('La web no devolvió lo esperado.')
            try:
                body = resp.read(max_bytes + 1)
            except (OSError, ValueError):
                raise FetchError('No se ha podido leer la web.') from None
            if len(body) > max_bytes: raise FetchError('La respuesta es demasiado grande.')
            return current, ctype, body
    raise FetchError('Demasiadas redirecciones.')


def fetch_json(url: str, max_bytes: int = 256 * 1024):
    import json
    _, _, body = fetch(url, kinds=('application/json', 'text/json', 'text/javascript', 'text/plain'), max_bytes=max_bytes, accept='application/json')
    try:
        return json.loads(body.decode('utf-8', 'replace'))
    except ValueError:
        raise FetchError('Respuesta no válida.') from None


def fetch_image(url: str, max_bytes: int = 8 * 1024 * 1024) -> bytes:
    _, _, body = fetch(url, kinds=('image/',), max_bytes=max_bytes, accept='image/webp,image/jpeg,image/png,image/*;q=0.8')
    return body
