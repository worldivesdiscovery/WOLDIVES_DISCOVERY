"""Linked videos of a dive site's route (v50.50). Videos are never uploaded to our server: a link is stored.

PLATFORMS is the list of video platforms the web knows. To add one, add an entry: the hosts of its links, how to read
the video's id from a link, and (when it has an official embeddable player) the player's address. The content security
policy (CSP) and the cookie policy follow this list: only the players of «insertable» platforms may load in the page,
and only after the visitor presses «Reproducir».

Any other platform is accepted when its page says it is a video (Open Graph «og:video» or «og:type=video…», or a
schema.org VideoObject); it then opens in a new tab. Shortened links, addresses with a user or a port, direct files
and pages that are not videos are refused with a clear message.

Environment (optional):
    WOD_VIDEO_EMBED_OFF=facebook,instagram    platforms whose player is not inserted (their videos open in a new tab)
"""
from __future__ import annotations

import hashlib
import html
import json
import re
import time
import urllib.parse
from dataclasses import dataclass, field
from html.parser import HTMLParser
from typing import Callable

from . import config as wcfg
from . import remoto

KINDS = ('normal', '360', 'vr')
KIND_LABELS = {'normal': 'Ruta normal', '360': 'Ruta 360°', 'vr': 'Realidad virtual'}

_YT_ID = re.compile(r'^[A-Za-z0-9_-]{11}$')
_DIGITS = re.compile(r'^\d{3,20}$')

SHORTENERS = {'bit.ly', 'tinyurl.com', 't.co', 'goo.gl', 'ow.ly', 'is.gd', 'buff.ly', 'cutt.ly', 'rebrand.ly', 'shorturl.at', 'rb.gy',
              'tiny.cc', 's.id', 'v.gd', 'lnkd.in', 'vm.tiktok.com', 'vt.tiktok.com', 'fb.watch', 'bitly.com', 'shorte.st', 'adf.ly',
              'linktr.ee', 'qrco.de', 'tr.im', 'x.co'}
BAD_EXT = re.compile(r'\.(exe|msi|apk|dmg|zip|rar|7z|scr|bat|cmd|js|jar|pdf|docx?|xlsx?|pptx?|svg|html?)$', re.I)
FILE_EXT = re.compile(r'\.(mp4|m4v|webm|mov|avi|mkv|m3u8|mpd|ogv)$', re.I)


class LinkError(ValueError):
    """A link that is refused; the message is for the person who pasted it."""


@dataclass(frozen=True)
class Platform:
    key: str
    name: str
    hosts: tuple[str, ...]
    parse: Callable[[urllib.parse.ParseResult], tuple[str, str] | None]     # → (video id, canonical link) or None
    player: Callable[[str], str] | None = None                              # video id → embeddable player (None: opens outside)
    frames: tuple[str, ...] = ()                                            # hosts of the player (CSP frame-src)
    oembed: Callable[[str], str] | None = None                              # canonical link → public oEmbed address
    thumbs: Callable[[str], list[str]] = field(default=lambda _id: [])     # direct preview images, best first
    vertical: bool = False                                                  # the player is portrait (9:16)
    hint: str = ''                                                          # message when a link of this site is not a video


def _host_is(host: str, hosts) -> bool:
    return any(host == h or host.endswith('.' + h) for h in hosts)


def _qs(p, name):
    v = urllib.parse.parse_qs(p.query).get(name)
    return v[0] if v else ''


def _seg(p):
    return [s for s in p.path.split('/') if s]


# --- YouTube ---------------------------------------------------------------------------------------------------------
def _youtube(p):
    host, seg = p.hostname, _seg(p)
    vid = ''
    if host == 'youtu.be' and seg: vid = seg[0]
    elif seg[:1] == ['watch']: vid = _qs(p, 'v')
    elif len(seg) >= 2 and seg[0] in ('shorts', 'embed', 'live', 'v', 'e'): vid = seg[1]
    if not _YT_ID.match(vid or ''): return None
    return vid, f'https://www.youtube.com/watch?v={vid}'


# --- Vimeo -----------------------------------------------------------------------------------------------------------
def _vimeo(p):
    seg = _seg(p)
    if p.hostname == 'player.vimeo.com':
        if len(seg) >= 2 and seg[0] == 'video' and _DIGITS.match(seg[1]):
            h = _qs(p, 'h')
            return (f'{seg[1]}:{h}' if re.fullmatch(r'[0-9a-f]{6,20}', h or '') else seg[1]), f'https://vimeo.com/{seg[1]}' + (f'/{h}' if h else '')
        return None
    nums = [i for i, s in enumerate(seg) if _DIGITS.match(s)]
    if not nums: return None
    i = nums[0]; vid = seg[i]
    if i and seg[0] not in ('channels', 'groups', 'album', 'showcase', 'video'): return None
    h = seg[i + 1] if len(seg) > i + 1 and re.fullmatch(r'[0-9a-f]{6,20}', seg[i + 1]) else ''
    return (f'{vid}:{h}' if h else vid), f'https://vimeo.com/{vid}' + (f'/{h}' if h else '')


def _vimeo_player(ref):
    vid, _, h = ref.partition(':')
    return f'https://player.vimeo.com/video/{vid}?dnt=1&autoplay=1' + (f'&h={h}' if h else '')


# --- Dailymotion -----------------------------------------------------------------------------------------------------
def _dailymotion(p):
    seg = _seg(p)
    vid = ''
    if p.hostname == 'dai.ly' and seg: vid = seg[0]
    elif len(seg) >= 2 and seg[0] == 'video': vid = seg[1]
    elif len(seg) >= 3 and seg[:2] == ['embed', 'video']: vid = seg[2]
    vid = vid.split('_')[0]
    if not re.fullmatch(r'[a-zA-Z0-9]{5,12}', vid or ''): return None
    return vid, f'https://www.dailymotion.com/video/{vid}'


# --- TikTok ----------------------------------------------------------------------------------------------------------
def _tiktok(p):
    seg = _seg(p)
    if len(seg) >= 3 and seg[0].startswith('@') and seg[1] == 'video' and _DIGITS.match(seg[2]):
        return seg[2], f'https://www.tiktok.com/{seg[0]}/video/{seg[2]}'
    if len(seg) >= 3 and seg[:2] in (['embed', 'v2'], ['player', 'v1']) and _DIGITS.match(seg[2]):
        return seg[2], f'https://www.tiktok.com/embed/v2/{seg[2]}'
    return None


# --- Facebook --------------------------------------------------------------------------------------------------------
def _facebook(p):
    seg = _seg(p)
    if seg[:1] == ['watch'] and _DIGITS.match(_qs(p, 'v')):
        v = _qs(p, 'v'); return v, f'https://www.facebook.com/watch/?v={v}'
    if len(seg) >= 2 and seg[0] == 'reel' and _DIGITS.match(seg[1]):
        return seg[1], f'https://www.facebook.com/reel/{seg[1]}'
    if len(seg) >= 3 and seg[1] == 'videos':
        vid = seg[-1] if _DIGITS.match(seg[-1]) else ''
        if vid: return vid, f'https://www.facebook.com/{seg[0]}/videos/{vid}'
    return None


def _facebook_player(ref):
    return 'https://www.facebook.com/plugins/video.php?show_text=false&autoplay=true&href=' + urllib.parse.quote(f'https://www.facebook.com/watch/?v={ref}', safe='')


# --- Instagram -------------------------------------------------------------------------------------------------------
def _instagram(p):
    seg = _seg(p)
    if len(seg) >= 2 and seg[0] in ('reel', 'reels', 'tv') and re.fullmatch(r'[A-Za-z0-9_-]{5,40}', seg[1]):
        kind = 'tv' if seg[0] == 'tv' else 'reel'
        return f'{kind}/{seg[1]}', f'https://www.instagram.com/{kind}/{seg[1]}/'
    return None


# --- Platforms that only open outside (no official player we can insert) -----------------------------------------------
def _twitch(p):
    seg = _seg(p)
    if p.hostname == 'clips.twitch.tv' and seg: return seg[0], f'https://clips.twitch.tv/{seg[0]}'
    if len(seg) >= 2 and seg[0] == 'videos' and _DIGITS.match(seg[1]): return seg[1], f'https://www.twitch.tv/videos/{seg[1]}'
    if len(seg) >= 3 and seg[1] == 'clip': return seg[2], f'https://www.twitch.tv/{seg[0]}/clip/{seg[2]}'
    return None


def _first_segment(prefix=''):
    def parse(p):
        seg = _seg(p)
        if prefix:
            if len(seg) >= 2 and seg[0] == prefix and re.fullmatch(r'[A-Za-z0-9_-]{3,60}', seg[1]): return seg[1], p.geturl()
            return None
        if seg and re.fullmatch(r'[A-Za-z0-9_-]{3,160}(\.html)?', seg[0]): return seg[0], p.geturl()
        return None
    return parse


PLATFORMS: tuple[Platform, ...] = (
    Platform('youtube', 'YouTube', ('youtube.com', 'youtu.be', 'youtube-nocookie.com'), _youtube,
             player=lambda v: f'https://www.youtube-nocookie.com/embed/{v}?autoplay=1&rel=0&playsinline=1',
             frames=('www.youtube-nocookie.com',),
             oembed=lambda u: 'https://www.youtube.com/oembed?format=json&url=' + urllib.parse.quote(u, safe=''),
             thumbs=lambda v: [f'https://i.ytimg.com/vi/{v}/maxresdefault.jpg', f'https://i.ytimg.com/vi/{v}/hqdefault.jpg'],
             hint='En YouTube, copia el enlace del vídeo (youtube.com/watch?v=… o youtu.be/…).'),
    Platform('vimeo', 'Vimeo', ('vimeo.com',), _vimeo, player=_vimeo_player, frames=('player.vimeo.com',),
             oembed=lambda u: 'https://vimeo.com/api/oembed.json?width=1280&url=' + urllib.parse.quote(u, safe=''),
             hint='En Vimeo, copia el enlace del vídeo (vimeo.com/123456789).'),
    Platform('dailymotion', 'Dailymotion', ('dailymotion.com', 'dai.ly'), _dailymotion,
             player=lambda v: f'https://www.dailymotion.com/embed/video/{v}?autoplay=1', frames=('www.dailymotion.com',),
             oembed=lambda u: 'https://www.dailymotion.com/services/oembed?format=json&url=' + urllib.parse.quote(u, safe=''),
             hint='En Dailymotion, copia el enlace del vídeo (dailymotion.com/video/…).'),
    Platform('tiktok', 'TikTok', ('tiktok.com',), _tiktok, player=lambda v: f'https://www.tiktok.com/player/v1/{v}?autoplay=1',
             frames=('www.tiktok.com',), oembed=lambda u: 'https://www.tiktok.com/oembed?url=' + urllib.parse.quote(u, safe=''), vertical=True,
             hint='En TikTok, copia el enlace completo del vídeo (tiktok.com/@usuario/video/…).'),
    Platform('facebook', 'Facebook', ('facebook.com',), _facebook, player=_facebook_player, frames=('www.facebook.com',),
             hint='En Facebook, copia el enlace del vídeo (facebook.com/…/videos/… o facebook.com/watch/?v=…).'),
    Platform('instagram', 'Instagram', ('instagram.com',), _instagram, player=lambda v: f'https://www.instagram.com/{v}/embed/',
             frames=('www.instagram.com',), vertical=True,
             hint='En Instagram, copia el enlace de un reel (instagram.com/reel/…): las fotos no son vídeos.'),
    Platform('twitch', 'Twitch', ('twitch.tv',), _twitch, hint='En Twitch, copia el enlace de un vídeo o de un clip.'),
    Platform('streamable', 'Streamable', ('streamable.com',), _first_segment()),
    Platform('rumble', 'Rumble', ('rumble.com',), _first_segment()),
    Platform('bilibili', 'Bilibili', ('bilibili.com',), _first_segment('video')),
)
BY_KEY = {p.key: p for p in PLATFORMS}
OTHER = 'otra'


def embed_off() -> set[str]:
    return {x.strip().lower() for x in wcfg.env('WOD_VIDEO_EMBED_OFF').split(',') if x.strip()}


def insertable(key: str) -> bool:
    p = BY_KEY.get(key)
    return bool(p and p.player and key not in embed_off())


def player_url(key: str, ref: str | None) -> str | None:
    return BY_KEY[key].player(ref) if ref and insertable(key) else None


def frame_hosts() -> list[str]:
    """Hosts of the players that may load in the page (CSP frame-src)."""
    return sorted({h for p in PLATFORMS if insertable(p.key) for h in p.frames})


def platform_names() -> list[dict]:
    return [{'key': p.key, 'name': p.name, 'insertable': insertable(p.key), 'vertical': p.vertical} for p in PLATFORMS]


def parse_link(raw) -> dict:
    """Checks a link pasted by a person. Returns {'platform', 'ref', 'url'} (ref None for other platforms).
    Raises LinkError with a clear message."""
    url = str(raw or '').strip()
    if not url: raise LinkError('Pega el enlace del vídeo.')
    if len(url) > 1000 or re.search(r'[\s\x00-\x1f\x7f<>"\\]', url): raise LinkError('El enlace no es válido.')
    if not url.lower().startswith('https://'):
        raise LinkError('Solo se admiten enlaces seguros, que empiezan por https://.')
    try:
        p = urllib.parse.urlparse(url)
        port = p.port
    except ValueError:
        raise LinkError('El enlace no es válido.') from None
    host = (p.hostname or '').lower().rstrip('.')
    if not host or '.' not in host or p.username or p.password or port not in (None, 443):
        raise LinkError('Este enlace parece sospechoso y no se admite.')
    if re.fullmatch(r'[\d.]+|\[?[0-9a-f:]+\]?', host) or host.startswith('xn--') or '.xn--' in host or host in ('localhost',):
        raise LinkError('Este enlace parece sospechoso y no se admite.')
    if host.removeprefix('www.') in SHORTENERS:
        raise LinkError('Usa el enlace completo del vídeo, no un enlace acortado.')
    for plat in PLATFORMS:
        if _host_is(host, plat.hosts):
            got = plat.parse(p._replace(netloc=host))
            if not got: raise LinkError('Este enlace no es de un vídeo. ' + (plat.hint or ''))
            return {'platform': plat.key, 'ref': got[0], 'url': got[1]}
    path = urllib.parse.unquote(p.path or '')
    if BAD_EXT.search(path): raise LinkError('Este enlace no es de un vídeo.')
    if FILE_EXT.search(path): raise LinkError('Enlaza la página del vídeo en su plataforma, no el archivo de vídeo.')
    return {'platform': OTHER, 'ref': None, 'url': p._replace(netloc=host, fragment='').geturl()}


class _Meta(HTMLParser):
    """Reads the <meta>, <title> and JSON-LD of a page (only the first 512 KB are read)."""
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.meta: dict[str, str] = {}; self.title = ''; self._in_title = False; self._ld = False; self.ld: list[str] = []

    def handle_starttag(self, tag, attrs):
        a = {k.lower(): (v or '') for k, v in attrs}
        if tag == 'meta':
            k = (a.get('property') or a.get('name') or a.get('itemprop') or '').lower()
            if k and a.get('content') and k not in self.meta: self.meta[k] = a['content'].strip()
        elif tag == 'title': self._in_title = True
        elif tag == 'script' and 'ld+json' in a.get('type', '').lower(): self._ld = True; self.ld.append('')

    def handle_endtag(self, tag):
        if tag == 'title': self._in_title = False
        if tag == 'script': self._ld = False

    def handle_data(self, data):
        if self._in_title and len(self.title) < 300: self.title += data
        if self._ld and self.ld and len(self.ld[-1]) < 100_000: self.ld[-1] += data


def _page_meta(url: str) -> dict:
    _, _, body = remoto.fetch(url, kinds=('text/html', 'application/xhtml'), max_bytes=768 * 1024, accept='text/html')
    m = _Meta()
    try:
        m.feed(body.decode('utf-8', 'replace')); m.close()
    except Exception:
        pass
    is_video = (m.meta.get('og:type', '').lower().startswith('video') or any(k.startswith('og:video') for k in m.meta)
                or 'twitter:player' in m.meta or any('videoobject' in x.lower() for x in m.ld))
    return {'title': m.meta.get('og:title') or m.meta.get('twitter:title') or html.unescape(m.title).strip(),
            'author': m.meta.get('author') or '', 'site': m.meta.get('og:site_name') or '',
            'thumb': m.meta.get('og:image') or m.meta.get('og:image:secure_url') or m.meta.get('twitter:image') or '', 'is_video': is_video}


_CACHE: dict[str, tuple[float, dict]] = {}


def inspect(raw) -> dict:
    """Checks the link and reads its public data once (title, author, preview image). Kept 30 minutes in memory so that
    «Comprobar» and «Añadir» do not ask the platform twice. Raises LinkError."""
    v = parse_link(raw)
    hit = _CACHE.get(v['url'])
    if hit and hit[0] > time.time(): return dict(hit[1])
    plat = BY_KEY.get(v['platform'])
    info = {'title': '', 'author': '', 'thumbs': [], 'site': plat.name if plat else ''}
    if plat:
        if plat.oembed:
            try:
                d = remoto.fetch_json(plat.oembed(v['url']))
                if isinstance(d, dict):
                    info['title'] = str(d.get('title') or '')[:300]; info['author'] = str(d.get('author_name') or '')[:200]
                    if d.get('thumbnail_url'): info['thumbs'].append(str(d['thumbnail_url']))
            except remoto.FetchError:
                pass
        info['thumbs'] = plat.thumbs(v['ref']) + info['thumbs']
        if not info['thumbs'] and not plat.oembed:
            try:
                pm = _page_meta(v['url'])
                info['title'] = info['title'] or pm['title']
                if pm['thumb']: info['thumbs'].append(urllib.parse.urljoin(v['url'], pm['thumb']))
            except remoto.FetchError:
                pass
    else:
        try:
            pm = _page_meta(v['url'])
        except remoto.FetchError:
            raise LinkError('No hemos podido abrir ese enlace para comprobar que es un vídeo. Revisa que la página sea pública.') from None
        if not pm['is_video']: raise LinkError('Ese enlace no es de un vídeo (la página no dice que tenga un vídeo).')
        host = urllib.parse.urlparse(v['url']).hostname or ''
        info.update(title=pm['title'], author=pm['author'], site=(pm['site'] or host.removeprefix('www.'))[:60])
        if pm['thumb']: info['thumbs'].append(urllib.parse.urljoin(v['url'], pm['thumb']))
    out = {**v, **info, 'title': re.sub(r'\s+', ' ', info['title']).strip()[:180], 'platform_name': info['site'] or (plat.name if plat else ''),
           'insertable': insertable(v['platform']), 'kind_guess': guess_kind(info['title'])}
    if len(_CACHE) > 500: _CACHE.clear()
    _CACHE[v['url']] = (time.time() + 1800, out)
    return dict(out)


def guess_kind(title: str) -> str:
    t = (title or '').lower()
    if re.search(r'\bvr\b|realidad virtual|virtual reality|réalité virtuelle', t): return 'vr'
    if '360' in t: return '360'
    return 'normal'


def thumb_name(url: str) -> str:
    """Files of a link's preview are named after the link, so the same video never downloads its image twice."""
    return 'v' + hashlib.sha256(url.encode()).hexdigest()[:20]


def fetch_thumbnail(info: dict) -> bytes | None:
    """The first preview image that can be downloaded (only https and only images; every hop is checked)."""
    for t in info.get('thumbs') or []:
        if not str(t).startswith('https://'): continue
        try:
            body = remoto.fetch_image(t)
        except remoto.FetchError:
            continue
        # YouTube answers «maxresdefault» with a small grey picture when the video has no big preview.
        if len(body) < 2500: continue
        return body
    return None


def public_row(row: dict) -> dict:
    """What the web receives of a video: the player only for insertable platforms, never anything else to load."""
    from . import imagenes
    key = row.get('platform') or OTHER
    plat = BY_KEY.get(key)
    return {'id': row['id'], 'url': row['url'], 'platform': key, 'platform_name': row.get('platform_name') or (plat.name if plat else ''),
            'insertable': insertable(key), 'player': player_url(key, row.get('video_ref')), 'vertical': bool(plat and plat.vertical),
            'kind': row.get('kind') or 'normal', 'title': row.get('title') or row.get('source_title') or '',
            'thumb': imagenes.srcset(row.get('thumb_base'), row.get('thumb_widths')), 'contributor': row.get('contributor_name') or 'WORLDIVES DISCOVERY',
            'contributor_kind': row.get('contributor_kind') or 'admin'}


def legacy_to_link(url: str | None) -> dict | None:
    """Old «recorrido virtual» videos (embed addresses of YouTube or Vimeo) as links of the new list; None otherwise."""
    if not url: return None
    try:
        v = parse_link(url)
    except LinkError:
        return None
    return v if v['platform'] in BY_KEY else None


def dumps(o) -> str:
    return json.dumps(o, ensure_ascii=False)
