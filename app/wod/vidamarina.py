"""Marine life and route videos of the dive sites (v50.50).

- species: central catalogue managed by the administrator (scientific name, photo with its author and licence).
- species_texts: common name and a short sentence of each species in every language of the web.
- point_species: the species that can be seen at a dive site, how often (habitual, ocasional, rara) and in which months.
- route_videos: links to videos of the site's route (normal, 360° or virtual reality). Never a video file.

What centres and freelance professionals add waits for the administrator's approval; what the administrator adds is
published at once. The page of a dive site gets its species and videos in the same request as the site, with one
indexed query each (never one request per species or per video).
"""
from __future__ import annotations

import html
import json
import re
import unicodedata
import urllib.parse
from pathlib import Path

from . import imagenes, remoto
from . import videos as wvideos

LANGS = ('es', 'en', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'zh')
FREQUENCIES = ('common', 'occasional', 'rare')
FREQ_RANK = {'common': 0, 'occasional': 1, 'rare': 2}
STATUSES = ('pending', 'approved', 'rejected')
SPECIES_WIDTHS = (128, 640)        # v50.51: the round photo of the carousel (64 px at 2×) and the bubble
VIDEO_WIDTHS = (400, 800, 1280)
EXAMPLES = Path(__file__).resolve().parents[1] / 'data' / 'especies'

SCHEMA = (
    '''CREATE TABLE IF NOT EXISTS species (
         id INTEGER PRIMARY KEY AUTOINCREMENT, scientific_name TEXT NOT NULL,
         photo_base TEXT, photo_widths TEXT, photo_ratio REAL,
         photo_author TEXT, photo_license TEXT, photo_license_url TEXT, photo_source_url TEXT,
         example_key TEXT, active INTEGER NOT NULL DEFAULT 1,
         created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)''',
    'CREATE UNIQUE INDEX IF NOT EXISTS ux_species_scientific ON species(lower(scientific_name)) WHERE active=1',
    '''CREATE TABLE IF NOT EXISTS species_texts (
         species_id INTEGER NOT NULL REFERENCES species(id) ON DELETE CASCADE, lang TEXT NOT NULL,
         common_name TEXT NOT NULL, blurb TEXT, search_key TEXT NOT NULL, PRIMARY KEY(species_id, lang))''',
    'CREATE INDEX IF NOT EXISTS idx_species_texts_search ON species_texts(search_key)',
    '''CREATE TABLE IF NOT EXISTS point_species (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         dive_point_id INTEGER NOT NULL REFERENCES dive_points(id) ON DELETE CASCADE,
         species_id INTEGER NOT NULL REFERENCES species(id) ON DELETE CASCADE,
         frequency TEXT NOT NULL DEFAULT 'common' CHECK(frequency IN ('common','occasional','rare')),
         months INTEGER NOT NULL DEFAULT 0,
         status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')), review_note TEXT,
         contributor_kind TEXT NOT NULL DEFAULT 'admin', contributor_provider TEXT, contributor_name TEXT,
         created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
         reviewed_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, reviewed_at TEXT,
         active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)''',
    'CREATE INDEX IF NOT EXISTS idx_point_species_point ON point_species(dive_point_id, status, active)',
    'CREATE INDEX IF NOT EXISTS idx_point_species_species ON point_species(species_id)',
    'CREATE INDEX IF NOT EXISTS idx_point_species_queue ON point_species(status, active, created_at)',
    'CREATE INDEX IF NOT EXISTS idx_point_species_contrib ON point_species(contributor_provider, created_at)',
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_point_species ON point_species(dive_point_id, species_id) WHERE active=1 AND status<>'rejected'",
    '''CREATE TABLE IF NOT EXISTS route_videos (
         id INTEGER PRIMARY KEY AUTOINCREMENT,
         dive_point_id INTEGER NOT NULL REFERENCES dive_points(id) ON DELETE CASCADE,
         url TEXT NOT NULL, platform TEXT NOT NULL, platform_name TEXT, video_ref TEXT,
         kind TEXT NOT NULL DEFAULT 'normal' CHECK(kind IN ('normal','360','vr')),
         title TEXT, source_title TEXT, source_author TEXT,
         thumb_base TEXT, thumb_widths TEXT, thumb_tries INTEGER NOT NULL DEFAULT 0,
         sort_order INTEGER NOT NULL DEFAULT 0,
         status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending','approved','rejected')), review_note TEXT,
         contributor_kind TEXT NOT NULL DEFAULT 'admin', contributor_provider TEXT, contributor_name TEXT,
         created_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
         reviewed_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL, reviewed_at TEXT,
         legacy_virtual_id INTEGER, active INTEGER NOT NULL DEFAULT 1, created_at TEXT NOT NULL, updated_at TEXT NOT NULL)''',
    'CREATE INDEX IF NOT EXISTS idx_route_videos_point ON route_videos(dive_point_id, status, active, sort_order, id)',
    'CREATE INDEX IF NOT EXISTS idx_route_videos_queue ON route_videos(status, active, created_at)',
    'CREATE INDEX IF NOT EXISTS idx_route_videos_contrib ON route_videos(contributor_provider, created_at)',
    "CREATE UNIQUE INDEX IF NOT EXISTS ux_route_videos_link ON route_videos(dive_point_id, url) WHERE active=1 AND status<>'rejected'",
)


def install(db):
    for stmt in SCHEMA: db.execute(stmt)


# --- Months --------------------------------------------------------------------------------------------------------------
def months_mask(values) -> int:
    """[6, 7, 8] → bits of June, July and August. Nothing or all twelve → 0 (all year)."""
    if isinstance(values, str): values = [x for x in re.split(r'[,\s]+', values) if x]
    mask = 0
    for v in values or []:
        try:
            m = int(v)
        except (TypeError, ValueError):
            raise ValueError('Mes no válido.') from None
        if not 1 <= m <= 12: raise ValueError('Mes no válido.')
        mask |= 1 << (m - 1)
    return 0 if mask == 0xFFF else mask


def months_list(mask) -> list[int]:
    mask = int(mask or 0)
    return [m for m in range(1, 13) if mask & (1 << (m - 1))]


# --- Search in any language ------------------------------------------------------------------------------------------
def search_key(text) -> str:
    t = unicodedata.normalize('NFKD', str(text or '')).lower()
    return ' '.join(''.join(ch for ch in t if not unicodedata.combining(ch)).split())


# --- Photo licences --------------------------------------------------------------------------------------------------
_FREE = re.compile(r'^(cc0|cc[-\s]?zero|public domain|dominio p[uú]blico|pd(m|-.*)?|cc[-\s]by(-sa)?([-\s]\d(\.\d)?)?(\s?[a-z]{2,3})?)$', re.I)
_OWN = re.compile(r'^(propia|foto propia|ilustraci[oó]n propia|cedida|cedida por (el|la) autor[a]?.*|banco de im[aá]genes.*|licencia comprada.*)$', re.I)
_NOT_FREE = re.compile(r'\b(nc|nd)\b|non[-\s]?commercial|no[-\s]?deriv|all rights reserved|todos los derechos|fair use|uso justo', re.I)


def clean_license(text) -> str:
    t = ' '.join(str(text or '').split())[:80]
    if not t: raise ValueError('Indica la licencia de la foto (propia, cedida, banco de imágenes o Creative Commons).')
    if _NOT_FREE.search(t): raise ValueError('Esa licencia no permite usar la foto en la web (no comercial o sin modificaciones).')
    if not (_FREE.match(t) or _OWN.match(t)):
        raise ValueError('Licencia no admitida. Usa «Propia», «Cedida por el autor», «Banco de imágenes», CC0, dominio público, CC BY o CC BY-SA.')
    return t


def https_or_none(value, max_len=500):
    v = str(value or '').strip()[:max_len]
    if not v: return None
    p = urllib.parse.urlparse(v)
    if p.scheme != 'https' or not p.hostname or p.username or p.password: raise ValueError('El enlace del origen de la foto debe empezar por https://.')
    return v


# --- Rows for the web ------------------------------------------------------------------------------------------------
def species_public(r) -> dict:
    d = dict(r)
    return {'id': d['species_id'] if 'species_id' in d else d['id'], 'link_id': d.get('link_id'), 'scientific': d['scientific_name'],
            'name': d.get('common_name') or d['scientific_name'], 'name_lang': d.get('name_lang'), 'blurb': d.get('blurb') or '',
            'frequency': d.get('frequency'), 'months': months_list(d.get('months')),
            # 17/10 (Bloque 2): at the site or in the area, the frequency and the season only when a source says them, where
            # it is seen, its group (the icon of a species without a photo) and its number in the catalogue
            'evidence': d.get('evidence') or 'point', 'frequency_label': d.get('frequency_label'), 'season': d.get('season') or '',
            'where': d.get('where_text') or '', 'group': d.get('group_key') or '', 'catalog_no': d.get('catalog_no'),
            'photo': ({**(imagenes.srcset(d.get('photo_base'), d.get('photo_widths')) or {}), 'ratio': d.get('photo_ratio')} if d.get('photo_base') else None),
            'credit': ({'author': d.get('photo_author') or '', 'license': d.get('photo_license') or '', 'license_url': d.get('photo_license_url') or '',
                        'source': d.get('photo_source_url') or ''} if d.get('photo_base') else None)}


_NAMES = '''LEFT JOIN species_texts t1 ON t1.species_id=s.id AND t1.lang=?
            LEFT JOIN species_texts t2 ON t2.species_id=s.id AND t2.lang='en'
            LEFT JOIN species_texts t3 ON t3.species_id=s.id AND t3.lang='es' '''
_NAME_COLS = '''COALESCE(t1.common_name,t2.common_name,t3.common_name) AS common_name, COALESCE(t1.blurb,t2.blurb,t3.blurb) AS blurb,
                CASE WHEN t1.common_name IS NOT NULL THEN t1.lang WHEN t2.common_name IS NOT NULL THEN 'en' WHEN t3.common_name IS NOT NULL THEN 'es' END AS name_lang'''


def point_species(db, pid, lang, statuses=('approved',), public=True, with_no_photo=True) -> list[dict]:
    """The species of a dive site in the visitor's language (falls back to English, then Spanish): one query. The
    public list only has the visible ones (17/10: the generic, doubtful or shore ones of an import wait hidden), first
    those cited at the site and then those of the area, in the order the administrator set."""
    marks = ','.join('?' * len(statuses))
    vis = ' AND COALESCE(ps.visible,1)=1' + ('' if with_no_photo else ' AND s.photo_base IS NOT NULL') if public else ''
    rows = db.execute(f'''SELECT ps.id AS link_id, ps.frequency, ps.months, ps.status, ps.review_note, ps.contributor_name, ps.contributor_provider,
                                 ps.evidence, ps.frequency_label, ps.season, ps.where_text, ps.visible, ps.hidden_reason, ps.sort_order, ps.sources,
                                 s.id AS species_id, s.scientific_name, s.photo_base, s.photo_widths, s.photo_ratio, s.photo_author, s.photo_license,
                                 s.photo_license_url, s.photo_source_url, s.group_key, s.catalog_no, {_NAME_COLS}
                          FROM point_species ps JOIN species s ON s.id=ps.species_id AND s.active=1 {_NAMES}
                          WHERE ps.dive_point_id=? AND ps.active=1 AND ps.status IN ({marks}){vis}
                          ORDER BY CASE WHEN ps.evidence='zone' THEN 1 ELSE 0 END, CASE WHEN ps.sort_order IS NULL THEN 1 ELSE 0 END, ps.sort_order,
                                   CASE COALESCE(ps.frequency_label, ps.frequency) WHEN 'habitual' THEN 0 WHEN 'common' THEN 0 WHEN 'frecuente' THEN 1
                                   WHEN 'occasional' THEN 2 WHEN 'ocasional' THEN 2 ELSE 3 END, common_name''',
                      (lang, pid, *statuses)).fetchall()
    out = []
    names = {}
    for r in rows: names[(r['common_name'] or '').lower()] = names.get((r['common_name'] or '').lower(), 0) + 1
    for r in rows:
        d = species_public(r); d['contributor'] = r['contributor_name'] or 'WORLDIVES DISCOVERY'
        d['same_name'] = names.get((r['common_name'] or '').lower(), 0) > 1   # two species with one common name: the scientific one under it
        if not public:
            try: srcs = json.loads(r['sources'] or '[]')
            except ValueError: srcs = []
            d.update(status=r['status'], review_note=r['review_note'] or '', contributor_provider=r['contributor_provider'],
                     visible=bool(r['visible'] if r['visible'] is not None else 1), hidden_reason=r['hidden_reason'] or '', sort_order=r['sort_order'], sources=srcs)
        out.append(d)
    return out


def point_videos(db, pid, statuses=('approved',), public=True) -> list[dict]:
    marks = ','.join('?' * len(statuses))
    rows = db.execute(f'''SELECT * FROM route_videos WHERE dive_point_id=? AND active=1 AND status IN ({marks}) ORDER BY featured DESC, sort_order, id''',
                      (pid, *statuses)).fetchall()
    out = []
    for r in rows:
        d = wvideos.public_row(dict(r))
        if not public: d.update(status=r['status'], review_note=r['review_note'] or '', sort_order=r['sort_order'],
                                contributor_provider=r['contributor_provider'], source_title=r['source_title'] or '',
                                contributor=r['contributor_name'] or 'WORLDIVES DISCOVERY')   # the editor only (v50.58: never public)
        out.append(d)
    return out


def search_species(db, q, lang, limit=30) -> list[dict]:
    key = search_key(q)
    where, args = 's.active=1', [lang]
    if key:
        where += ''' AND (s.id IN (SELECT species_id FROM species_texts WHERE search_key LIKE ?) OR lower(s.scientific_name) LIKE ?)'''
        args += [f'%{key}%', f'%{key}%']
    rows = db.execute(f'''SELECT s.*, {_NAME_COLS} FROM species s {_NAMES} WHERE {where} ORDER BY common_name LIMIT ?''', (*args, int(limit))).fetchall()
    return [species_public(r) for r in rows]


def species_full(db, sid) -> dict | None:
    r = db.execute('SELECT * FROM species WHERE id=? AND active=1', (sid,)).fetchone()
    if not r: return None
    d = species_public({**dict(r), 'common_name': None})
    d['texts'] = {t['lang']: {'name': t['common_name'], 'blurb': t['blurb'] or ''} for t in db.execute('SELECT * FROM species_texts WHERE species_id=?', (sid,)).fetchall()}
    d['name'] = (d['texts'].get('es') or d['texts'].get('en') or {}).get('name') or d['scientific']
    d['points'] = db.execute("SELECT COUNT(*) FROM point_species WHERE species_id=? AND active=1 AND status='approved'", (sid,)).fetchone()[0]
    d['example_key'] = r['example_key']
    return d


def save_texts(db, sid, texts: dict):
    """texts: {lang: {'name', 'blurb'}}. Spanish is required; the other languages are optional (the web falls back)."""
    clean = {}
    for lang in LANGS:
        t = texts.get(lang) or {}
        name = ' '.join(str(t.get('name') or '').split())[:80]
        blurb = ' '.join(str(t.get('blurb') or '').split())[:240]
        if name: clean[lang] = (name, blurb)
    if 'es' not in clean: raise ValueError('Escribe al menos el nombre común en español.')
    db.execute('DELETE FROM species_texts WHERE species_id=?', (sid,))
    for lang, (name, blurb) in clean.items():
        db.execute('INSERT INTO species_texts(species_id,lang,common_name,blurb,search_key) VALUES(?,?,?,?,?)', (sid, lang, name, blurb or None, search_key(name)))
    return clean


# --- Wikimedia Commons ---------------------------------------------------------------------------------------------------
COMMONS_API = 'https://commons.wikimedia.org/w/api.php'
_TAGS = re.compile(r'<[^>]+>')


def _plain(v) -> str:
    return ' '.join(html.unescape(_TAGS.sub(' ', str(v or ''))).split())[:200]


def _commons_item(page) -> dict | None:
    info = (page.get('imageinfo') or [None])[0]
    if not info: return None
    meta = info.get('extmetadata') or {}
    lic = _plain((meta.get('LicenseShortName') or {}).get('value'))
    author = _plain((meta.get('Artist') or {}).get('value')) or _plain((meta.get('Credit') or {}).get('value'))
    ok, why = True, ''
    try:
        lic = clean_license(lic)
    except ValueError as e:
        ok, why = False, str(e)
    if ok and not author: ok, why = False, 'La foto no indica su autor.'
    if (info.get('mime') or '') not in ('image/jpeg', 'image/png', 'image/webp'): ok, why = False, 'Formato no admitido.'
    return {'title': page.get('title') or '', 'thumb': info.get('thumburl') or '', 'width': info.get('width'), 'height': info.get('height'),
            'author': author, 'license': lic, 'license_url': _plain((meta.get('LicenseUrl') or {}).get('value')),
            'page': info.get('descriptionurl') or '', 'download': info.get('thumburl') or '', 'ok': ok, 'why': why}


def commons_search(q: str, limit: int = 12) -> list[dict]:
    q = ' '.join(str(q or '').split())[:100]
    if len(q) < 3: raise ValueError('Escribe al menos 3 letras (mejor el nombre científico).')
    url = COMMONS_API + '?' + urllib.parse.urlencode({
        'action': 'query', 'format': 'json', 'formatversion': '2', 'generator': 'search', 'gsrnamespace': '6', 'gsrlimit': str(limit),
        'gsrsearch': f'{q} filetype:bitmap', 'prop': 'imageinfo', 'iiprop': 'url|size|mime|extmetadata', 'iiurlwidth': '480',
        'iiextmetadatafilter': 'Artist|Credit|LicenseShortName|LicenseUrl'})
    d = remoto.fetch_json(url, max_bytes=2 * 1024 * 1024)
    pages = sorted(((d.get('query') or {}).get('pages') or []), key=lambda p: p.get('index', 0))
    return [x for x in (_commons_item(p) for p in pages) if x]


def commons_file(title: str) -> dict:
    """The data of one file, asked again to Commons (nothing the browser sends is trusted), with a 1600 px copy."""
    title = str(title or '').strip()[:250]
    if not title.startswith('File:'): raise ValueError('Elige una foto de la lista.')
    url = COMMONS_API + '?' + urllib.parse.urlencode({'action': 'query', 'format': 'json', 'formatversion': '2', 'titles': title, 'prop': 'imageinfo',
                                                      'iiprop': 'url|size|mime|extmetadata', 'iiurlwidth': '1600',
                                                      'iiextmetadatafilter': 'Artist|Credit|LicenseShortName|LicenseUrl'})
    d = remoto.fetch_json(url, max_bytes=512 * 1024)
    pages = (d.get('query') or {}).get('pages') or []
    item = _commons_item(pages[0]) if pages else None
    if not item: raise ValueError('No se ha encontrado esa foto en Wikimedia Commons.')
    if not item['ok']: raise ValueError(item['why'])
    if urllib.parse.urlparse(item['download']).hostname != 'upload.wikimedia.org': raise ValueError('Dirección de la foto no admitida.')
    return item


# --- Example species (own illustrations, see docs/vida-marina/especies-de-ejemplo.md) ---------------------------------------
def examples() -> list[dict]:
    f = EXAMPLES / 'especies.json'
    if not f.exists(): return []
    return json.loads(f.read_text(encoding='utf-8'))['especies']
