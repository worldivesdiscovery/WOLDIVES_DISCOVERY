"""Local stand-in of the video platforms and of Wikimedia Commons (v50.50). Nothing leaves the machine: the server is
started with WOD_MEDIA_FETCH_BASE=<this server> and every outside request arrives here as /fetch?url=<address>.

What it answers, by address:
  YouTube     oEmbed with title and author; preview images (maxresdefault 1280×720; for ids starting with «h» only
              hqdefault, 480×360 with black bands like the real one; for ids starting with «NOTHUMB», nothing).
  Vimeo, Dailymotion, TikTok   oEmbed with a preview image (TikTok portrait).
  Facebook    a page without preview (as when it asks to sign in): the web uses the dive site's photo.
  Twitch      a page with og:image (opens in a new tab).
  videos.otra-plataforma.example     a page that says it is a video (og:type video.other) with og:image.
  blog.example.com                   a page that is not a video.
  commons.wikimedia.org              search and file data with free and non-free licences; upload.wikimedia.org images.
v50.58 (vídeos de los puntos): YouTube ids starting with «GONE» answer 404 (deleted), «PRIV» 403 (private), «NOEMB» 401
(insertion turned off) and «SH» a portrait oEmbed (a Short); TikTok videos whose number starts with 404 are gone;
graph.facebook.com answers Instagram's oEmbed (only asked when WOD_META_OEMBED_TOKEN is set) with a portrait image.
Every request is kept in .seen (address list) so tests can check what was asked and when.
"""
from __future__ import annotations

import io
import json
import threading
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PHOTOS = sorted((ROOT / 'public' / 'img' / 'destinos').glob('*.webp'))


def picture(w, h, seed=0, bands=False):
    """A JPEG made from the web's own destination photos (so screenshots look real), resized to w×h."""
    from PIL import Image, ImageOps
    if PHOTOS:
        im = Image.open(PHOTOS[seed % len(PHOTOS)]).convert('RGB')
        im = ImageOps.fit(im, (w, h if not bands else int(w * 9 / 16)))
    else:
        im = Image.new('RGB', (w, h), (20 + seed * 7 % 60, 80, 140))
    if bands:
        canvas = Image.new('RGB', (w, h), (0, 0, 0)); canvas.paste(im, (0, (h - im.height) // 2)); im = canvas
    out = io.BytesIO(); im.save(out, 'JPEG', quality=82)
    return out.getvalue()


def _seed(s):
    return sum(map(ord, s))


class MediaMock:
    def __init__(self):
        mock = self
        self.seen: list[str] = []

        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def send(self, code, body=b'', ctype='application/json', headers=None):
                self.send_response(code)
                self.send_header('Content-Type', ctype)
                for k, v in (headers or {}).items(): self.send_header(k, v)
                self.send_header('Content-Length', str(len(body)))
                self.end_headers(); self.wfile.write(body)

            def do_GET(self):
                q = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query)
                url = (q.get('url') or [''])[0]
                mock.seen.append(url)
                code, body, ctype, headers = mock.answer(url)
                self.send(code, body, ctype, headers)

        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.base = f'http://127.0.0.1:{self.httpd.server_address[1]}'
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def stop(self):
        self.httpd.shutdown()

    def asked(self, needle):
        return [u for u in self.seen if needle in u]

    # ------------------------------------------------------------------------------------------------------------
    def answer(self, url):
        j = lambda d: (200, json.dumps(d).encode(), 'application/json', None)
        img = lambda w, h, s, bands=False: (200, picture(w, h, s, bands), 'image/jpeg', None)
        html = lambda s: (200, s.encode(), 'text/html; charset=utf-8', None)
        not_found = (404, b'', 'text/plain', None)
        p = urllib.parse.urlparse(url); host = p.hostname or ''; qs = urllib.parse.parse_qs(p.query)
        inner = (qs.get('url') or [''])[0]
        if host == 'www.youtube.com' and p.path == '/oembed':
            vid = urllib.parse.parse_qs(urllib.parse.urlparse(inner).query).get('v', [''])[0]
            if vid.startswith('NOOEMB') or vid.startswith('GONE'): return not_found
            if vid.startswith('PRIV'): return (403, b'Forbidden', 'text/plain', None)
            if vid.startswith('NOEMB'): return (401, b'Unauthorized', 'text/plain', None)
            if vid.startswith('SH'):
                return j({'title': f'Short del pecio · {vid}', 'author_name': 'Canal de pruebas', 'width': 113, 'height': 200,
                          'thumbnail_url': f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'})
            return j({'title': f'Ruta del pecio · {vid}' if '360' not in vid else f'Ruta 360° por la pared · {vid}', 'author_name': 'Canal de pruebas',
                      'thumbnail_url': f'https://i.ytimg.com/vi/{vid}/hqdefault.jpg'})
        if host == 'i.ytimg.com':
            vid = p.path.split('/')[2]
            if vid.startswith('NOTHUMB'): return not_found
            if p.path.endswith('maxresdefault.jpg'): return not_found if vid.startswith('h') else img(1280, 720, _seed(vid))
            return img(480, 360, _seed(vid), bands=True)
        if host == 'vimeo.com' and p.path.startswith('/api/oembed'):
            vid = urllib.parse.urlparse(inner).path.strip('/').split('/')[0]
            return j({'title': f'Inmersión en Vimeo {vid}', 'author_name': 'Fotógrafo de pruebas', 'thumbnail_url': f'https://i.vimeocdn.com/video/{vid}-d_1280'})
        if host == 'i.vimeocdn.com': return img(1280, 720, 3)
        if host == 'www.dailymotion.com' and p.path.startswith('/services/oembed'):
            return j({'title': 'Buceo nocturno en Dailymotion', 'author_name': 'Club de pruebas', 'thumbnail_url': 'https://s1.dmcdn.net/v/prueba/x1080'})
        if host == 's1.dmcdn.net': return img(1920, 1080, 5)
        if host == 'www.tiktok.com' and p.path == '/oembed':
            if '/video/404' in inner: return (400, json.dumps({'code': 400, 'message': 'Something went wrong'}).encode(), 'application/json', None)
            return j({'title': 'Tortuga en la Restinga #buceo', 'author_name': '@buceo', 'thumbnail_url': 'https://p16-sign.tiktokcdn-eu.com/obj/prueba.jpeg'})
        if host.endswith('tiktokcdn-eu.com'): return img(720, 1280, 7)
        if host == 'graph.facebook.com' and p.path.endswith('/instagram_oembed'):
            if 'access_token' not in qs: return (400, b'{"error":{"message":"token"}}', 'application/json', None)
            return j({'title': 'Reel en la Restinga', 'author_name': 'buceo.restinga', 'thumbnail_url': 'https://scontent.cdninstagram.com/v/prueba.jpg',
                      'thumbnail_width': 640, 'thumbnail_height': 1136})
        if host.endswith('facebook.com'):
            return html('<html><head><title>Facebook</title></head><body>Inicia sesión para continuar.</body></html>')
        if host.endswith('twitch.tv'):
            return html('<html><head><meta property="og:title" content="Directo desde el barco"><meta property="og:image" content="https://static-cdn.jtvnw.net/prueba.jpg">'
                        '<meta property="og:type" content="video.other"></head></html>')
        if host == 'static-cdn.jtvnw.net': return img(1280, 720, 9)
        if host == 'videos.otra-plataforma.example' and p.path.startswith('/miniaturas/'): return img(1280, 720, 11)
        if host == 'videos.otra-plataforma.example':
            return html('<html><head><meta property="og:type" content="video.other"><meta property="og:title" content="Travesía por la cueva">'
                        '<meta property="og:site_name" content="Otra Plataforma"><meta property="og:image" content="/miniaturas/cueva.jpg"></head></html>')
        if host == 'blog.example.com':
            return html('<html><head><title>Mi blog</title><meta property="og:type" content="article"></head><body>Texto</body></html>')
        if host == 'commons.wikimedia.org' and p.path == '/w/api.php':
            return j(self.commons(qs))
        if host == 'upload.wikimedia.org': return img(1600, 1200, 13)
        return not_found

    @staticmethod
    def commons(qs):
        files = [
            ('File:Mero de pruebas.jpg', 'CC BY-SA 4.0', '<a href="//commons.wikimedia.org/wiki/User:Ana">Ana Pruebas</a>', 'image/jpeg'),
            ('File:Mero dominio publico.jpg', 'Public domain', 'NOAA de pruebas', 'image/jpeg'),
            ('File:Mero no comercial.jpg', 'CC BY-NC 4.0', 'Autor NC', 'image/jpeg'),
            ('File:Mero sin autor.jpg', 'CC BY 4.0', '', 'image/jpeg'),
        ]
        if 'titles' in qs: files = [f for f in files if f[0] == qs['titles'][0]]
        pages = []
        for i, (title, lic, author, mime) in enumerate(files):
            name = urllib.parse.quote(title[5:].replace(' ', '_'))
            pages.append({'pageid': 100 + i, 'ns': 6, 'title': title, 'index': i + 1, 'imageinfo': [{
                'url': f'https://upload.wikimedia.org/wikipedia/commons/a/ab/{name}', 'descriptionurl': f'https://commons.wikimedia.org/wiki/{urllib.parse.quote(title)}',
                'thumburl': f'https://upload.wikimedia.org/wikipedia/commons/thumb/a/ab/{name}/1600px-{name}', 'thumbwidth': 1600, 'thumbheight': 1200,
                'width': 4000, 'height': 3000, 'mime': mime,
                'extmetadata': {'Artist': {'value': author}, 'LicenseShortName': {'value': lic},
                                'LicenseUrl': {'value': 'https://creativecommons.org/licenses/by-sa/4.0' if 'SA' in lic else ''}}}]})
        return {'batchcomplete': True, 'query': {'pages': pages}}
