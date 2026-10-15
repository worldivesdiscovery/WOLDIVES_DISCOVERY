"""v50.56 · Bloque 2: seguros de buceo, sin base de datos.

Regla legal (Real Decreto-ley 3/2020): WORLDIVES no es aseguradora ni mediador de seguros. No vende, no cobra, no
recomienda ni compara coberturas: informa de que hay aseguradoras colaboradoras y lleva a su web, donde se contrata y se
paga. Ninguna aseguradora está escrita en el código: todas se configuran en Administración → Seguros.

Aquí: tipos, zonas y estados; si una póliza cubre una fecha; las direcciones de contratación (https y solo los dominios
autorizados de cada aseguradora, con su código de colaborador); el orden neutral; los textos legales por defecto en los
9 idiomas; la lectura del texto de un PDF para proponer fechas y número de póliza; y la capa de proveedores
(InsuranceProvider) con el modo «enlace» de ahora y el modo «API» preparado y desactivado.
"""
from __future__ import annotations

import datetime as _dt
import re
import zlib
from urllib.parse import urlparse

# ------------------------------------------------------------------------------------------------ kinds and states
POLICY_KINDS = ('dia', 'semana', 'anio', 'otro')
PRODUCT_KINDS = ('dia', 'semana', 'anio', 'rc_centro')
KIND_LABELS = {'dia': 'Día', 'semana': 'Semana', 'anio': 'Año', 'otro': 'Otro', 'rc_centro': 'RC para centros'}
ZONES = ('espana', 'europa', 'mundo')
ZONE_LABELS = {'espana': 'España', 'europa': 'Europa', 'mundo': 'Mundo'}
AUDIENCES = ('buceador', 'centro')
# What a service asks for (decided by the centre): «No» · «Sí, se comprueba en el centro» (default) · «Sí, obligatorio
# para reservar online».
REQUIRE = ('no', 'center', 'online')
REQUIRE_LABELS = {'no': 'No', 'center': 'Sí, se comprueba en el centro', 'online': 'Sí, obligatorio para reservar online'}
DEFAULT_REQUIRE = 'center'

STATES = ('vigente', 'caduca_pronto', 'caducado', 'sin_seguro')
STATE_LABELS = {'vigente': 'Vigente', 'caduca_pronto': 'Caduca pronto', 'caducado': 'Caducado', 'sin_seguro': 'Sin seguro'}
STATE_ICONS = {'vigente': '🟢', 'caduca_pronto': '🟠', 'caducado': '🔴', 'sin_seguro': '⚪'}
SOON_DAYS = 30
NOTICE_DAYS = (30, 7, 1, 0)          # e-mail and app notice before the end (0 = the day it ends)
DEFAULT_RETENTION_MONTHS = 12         # expired policies are deleted after this (unless a booking is in dispute)
MAX_FILE_BYTES = 10 * 1024 * 1024
# A booking's insurance, as the centre and the API see it
BOOKING_STATES = ('not_required', 'ok', 'declared', 'at_center', 'missing', 'expired')

DATE_RE = re.compile(r'^\d{4}-\d{2}-\d{2}$')


def clean_date(value) -> str | None:
    s = str(value or '').strip()[:10]
    if not DATE_RE.fullmatch(s): return None
    try: _dt.date.fromisoformat(s)
    except ValueError: return None
    return s


def covers(policy, day: str) -> bool:
    """A policy covers a day (the local date of the dive) if the day is between its first and last day."""
    f, t = clean_date(_get(policy, 'valid_from')), clean_date(_get(policy, 'valid_to'))
    return bool(t) and (not f or f <= day) and day <= t


def state_of(policies, today: str) -> dict:
    """The state of a diver's insurance today: 🟢 vigente, 🟠 caduca pronto (less than 30 days), 🔴 caducado, ⚪ sin seguro.
    With several policies, the one that covers today and lasts longest; if none covers today, the last one that ended."""
    pols = [p for p in policies if clean_date(_get(p, 'valid_to'))]
    current = sorted((p for p in pols if covers(p, today)), key=lambda p: _get(p, 'valid_to'), reverse=True)
    if current:
        p = current[0]
        left = (_dt.date.fromisoformat(_get(p, 'valid_to')) - _dt.date.fromisoformat(today)).days
        st = 'caduca_pronto' if left < SOON_DAYS else 'vigente'
        return {'state': st, 'icon': STATE_ICONS[st], 'label': STATE_LABELS[st], 'days_left': left, 'policy': p}
    future = sorted((p for p in pols if (clean_date(_get(p, 'valid_from')) or '') > today), key=lambda p: _get(p, 'valid_from'))
    past = sorted((p for p in pols if _get(p, 'valid_to') < today), key=lambda p: _get(p, 'valid_to'), reverse=True)
    if past and not future:
        return {'state': 'caducado', 'icon': STATE_ICONS['caducado'], 'label': STATE_LABELS['caducado'], 'days_left': None, 'policy': past[0]}
    return {'state': 'sin_seguro', 'icon': STATE_ICONS['sin_seguro'], 'label': STATE_LABELS['sin_seguro'], 'days_left': None,
            'policy': future[0] if future else None}


def _get(p, k):
    if p is None: return None
    try: return p[k]
    except (KeyError, IndexError, TypeError): return getattr(p, k, None)


# ------------------------------------------------------------------------------------------------ countries
COUNTRY_ISO = {
    'españa': 'ES', 'spain': 'ES', 'canarias': 'ES', 'portugal': 'PT', 'francia': 'FR', 'france': 'FR', 'italia': 'IT', 'italy': 'IT',
    'alemania': 'DE', 'germany': 'DE', 'grecia': 'GR', 'greece': 'GR', 'croacia': 'HR', 'croatia': 'HR', 'malta': 'MT',
    'reino unido': 'GB', 'uk': 'GB', 'united kingdom': 'GB', 'países bajos': 'NL', 'paises bajos': 'NL', 'netherlands': 'NL', 'holanda': 'NL',
    'bélgica': 'BE', 'belgica': 'BE', 'belgium': 'BE', 'suiza': 'CH', 'switzerland': 'CH', 'austria': 'AT', 'irlanda': 'IE', 'ireland': 'IE',
    'polonia': 'PL', 'poland': 'PL', 'egipto': 'EG', 'egypt': 'EG', 'méxico': 'MX', 'mexico': 'MX', 'estados unidos': 'US', 'usa': 'US',
    'cuba': 'CU', 'república dominicana': 'DO', 'honduras': 'HN', 'belice': 'BZ', 'colombia': 'CO', 'ecuador': 'EC', 'brasil': 'BR',
    'tailandia': 'TH', 'thailand': 'TH', 'indonesia': 'ID', 'filipinas': 'PH', 'philippines': 'PH', 'maldivas': 'MV', 'maldives': 'MV',
    'australia': 'AU', 'japón': 'JP', 'japon': 'JP', 'china': 'CN', 'sudáfrica': 'ZA', 'mozambique': 'MZ'}


def iso_country(value) -> str:
    """'España' → 'ES'; an ISO code stays as it is. '' if unknown."""
    s = str(value or '').strip()
    if re.fullmatch(r'[A-Za-z]{2}', s): return s.upper()
    return COUNTRY_ISO.get(s.lower(), '')


def clean_countries(value) -> list[str]:
    items = value if isinstance(value, (list, tuple)) else re.split(r'[,;\s]+', str(value or ''))
    out = []
    for x in items:
        c = iso_country(x)
        if c and c not in out: out.append(c)
    return out[:80]


def sold_in(product_countries, *countries) -> bool:
    """A product with no countries is sold everywhere; otherwise, in the country of the diver or of the dive."""
    allowed = set(product_countries or [])
    return not allowed or any(c and c in allowed for c in countries)


# ------------------------------------------------------------------------------------------------ addresses
HOST_RE = re.compile(r'^(?=.{1,253}$)(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z]{2,63}$')


def clean_domains(value) -> list[str]:
    items = value if isinstance(value, (list, tuple)) else re.split(r'[,;\s]+', str(value or ''))
    out = []
    for x in items:
        h = str(x or '').strip().lower()
        h = re.sub(r'^https?://', '', h).split('/')[0].split(':')[0].lstrip('.')
        if h.startswith('www.'): h = h[4:]
        if h and HOST_RE.fullmatch(h) and h not in out: out.append(h)
    return out[:20]


def url_allowed(url, domains) -> bool:
    """Only https addresses of the domains authorised for that insurer (or their subdomains)."""
    try: p = urlparse(str(url or '').strip())
    except ValueError: return False
    host = (p.hostname or '').lower()
    if p.scheme != 'https' or not host or p.username or p.password or (p.port not in (None, 443)): return False
    return any(host == d or host.endswith('.' + d) for d in (domains or []))


def link_for(template: str, partner_code: str | None) -> str:
    """The insurer's address with the partner code of WORLDIVES ({codigo} in the address, if the insurer uses it).
    Never personal data of the diver: in «enlace» mode nothing else is added."""
    return str(template or '').replace('{codigo}', re.sub(r'[^A-Za-z0-9_.\-]', '', partner_code or ''))


# ------------------------------------------------------------------------------------------------ neutral order
def ordered(providers, mode: str = 'alpha', today: _dt.date | None = None) -> list:
    """«Destacado» first (an insurer that pays to appear first, and it says so), by its order. The rest: alphabetical
    or, if the administration chooses it, rotated every day so no one is always first."""
    feat = sorted((p for p in providers if _get(p, 'featured')), key=lambda p: (_get(p, 'sort_order') or 0, (_get(p, 'name') or '').lower()))
    rest = sorted((p for p in providers if not _get(p, 'featured')), key=lambda p: (_get(p, 'name') or '').lower())
    if mode == 'rotate' and rest:
        k = (today or _dt.date.today()).toordinal() % len(rest)
        rest = rest[k:] + rest[:k]
    return feat + rest


# ------------------------------------------------------------------------------------------------ legal texts
# Editable in Administración → Seguros → Textos legales (these are the texts until the administration changes them).
# [PENDIENTE ABOGADO]: the exact wording (docs/legal/cambios-v50.56-para-abogado.md).
LEGAL_KEYS = ('notice', 'collaborator', 'featured')
LEGAL_DEFAULTS = {
    'es': {'notice': 'La contratación se realiza en la web de {insurer}. WORLDIVES no es aseguradora ni mediador de seguros.',
           'collaborator': 'Colaborador: WORLDIVES puede recibir una compensación de {insurer} si contratas desde este enlace. No cambia el precio que pagas.',
           'featured': 'Destacado: {insurer} paga para aparecer en primer lugar.'},
    'en': {'notice': 'The insurance is purchased on the {insurer} website. WORLDIVES is not an insurer or an insurance intermediary.',
           'collaborator': 'Partner: WORLDIVES may receive compensation from {insurer} if you buy through this link. It does not change the price you pay.',
           'featured': 'Featured: {insurer} pays to appear first.'},
    'fr': {'notice': "La souscription se fait sur le site de {insurer}. WORLDIVES n'est ni assureur ni intermédiaire en assurance.",
           'collaborator': "Partenaire : WORLDIVES peut recevoir une rémunération de {insurer} si vous souscrivez via ce lien. Cela ne change pas le prix que vous payez.",
           'featured': 'Mis en avant : {insurer} paie pour apparaître en premier.'},
    'de': {'notice': 'Der Abschluss erfolgt auf der Website von {insurer}. WORLDIVES ist weder Versicherer noch Versicherungsvermittler.',
           'collaborator': 'Partner: WORLDIVES kann von {insurer} eine Vergütung erhalten, wenn Sie über diesen Link abschließen. Ihr Preis ändert sich dadurch nicht.',
           'featured': 'Hervorgehoben: {insurer} bezahlt dafür, an erster Stelle zu erscheinen.'},
    'it': {'notice': "La sottoscrizione avviene sul sito di {insurer}. WORLDIVES non è un assicuratore né un intermediario assicurativo.",
           'collaborator': 'Partner: WORLDIVES può ricevere un compenso da {insurer} se sottoscrivi da questo link. Il prezzo che paghi non cambia.',
           'featured': 'In evidenza: {insurer} paga per comparire per primo.'},
    'pt': {'notice': 'A contratação é feita no site da {insurer}. A WORLDIVES não é seguradora nem mediadora de seguros.',
           'collaborator': 'Parceiro: a WORLDIVES pode receber uma compensação da {insurer} se contratar através desta ligação. O preço que paga não muda.',
           'featured': 'Destaque: a {insurer} paga para aparecer em primeiro lugar.'},
    'pl': {'notice': 'Ubezpieczenie zawiera się na stronie {insurer}. WORLDIVES nie jest ubezpieczycielem ani pośrednikiem ubezpieczeniowym.',
           'collaborator': 'Partner: WORLDIVES może otrzymać wynagrodzenie od {insurer}, jeśli kupisz przez ten link. Cena, którą płacisz, się nie zmienia.',
           'featured': 'Wyróżnione: {insurer} płaci za pojawienie się na pierwszym miejscu.'},
    'nl': {'notice': 'De verzekering wordt afgesloten op de website van {insurer}. WORLDIVES is geen verzekeraar of verzekeringsbemiddelaar.',
           'collaborator': 'Partner: WORLDIVES kan een vergoeding van {insurer} ontvangen als u via deze link afsluit. De prijs die u betaalt verandert niet.',
           'featured': 'Uitgelicht: {insurer} betaalt om als eerste te verschijnen.'},
    'zh': {'notice': '保险在 {insurer} 的网站上购买。WORLDIVES 不是保险公司，也不是保险中介。',
           'collaborator': '合作伙伴：如果您通过此链接购买，WORLDIVES 可能会从 {insurer} 获得报酬。您支付的价格不变。',
           'featured': '推荐：{insurer} 付费以排在第一位。'},
}


def legal_texts(saved: dict | None, lang: str) -> dict:
    """The legal texts of a language: what the administration saved, or the defaults."""
    base = LEGAL_DEFAULTS.get(lang) or LEGAL_DEFAULTS['es']
    mine = ((saved or {}).get(lang) or {})
    return {k: (str(mine.get(k) or '').strip() or base[k]) for k in LEGAL_KEYS}


def clean_legal(data) -> dict:
    out = {}
    for lang in LEGAL_DEFAULTS:
        d = (data or {}).get(lang) or {}
        row = {k: str(d.get(k) or '').strip()[:600] for k in LEGAL_KEYS if str(d.get(k) or '').strip()}
        if row: out[lang] = row
    return out


# ------------------------------------------------------------------------------------------------ PDF reading
_STREAM = re.compile(rb'stream\r?\n(.*?)\r?\nendstream', re.S)
_TEXT_OP = re.compile(rb'(?:\((?:\\.|[^\\)])*\)|<[0-9A-Fa-f\s]*>)\s*(?:Tj|\'|")|\[(?:[^\]]*)\]\s*TJ')
_STR = re.compile(rb'\((?:\\.|[^\\)])*\)|<[0-9A-Fa-f\s]*>')
_ESC = {b'n': b'\n', b'r': b'\r', b't': b'\t', b'b': b'\b', b'f': b'\f', b'(': b'(', b')': b')', b'\\': b'\\'}


def _unescape(s: bytes) -> bytes:
    out = bytearray(); i = 0
    while i < len(s):
        c = s[i:i + 1]
        if c == b'\\' and i + 1 < len(s):
            n = s[i + 1:i + 2]
            if n in _ESC: out += _ESC[n]; i += 2; continue
            m = re.match(rb'[0-7]{1,3}', s[i + 1:i + 4])
            if m: out.append(int(m.group(0), 8) & 0xFF); i += 1 + len(m.group(0)); continue
            i += 1; continue
        out += c; i += 1
    return bytes(out)


def pdf_text(raw: bytes, limit: int = 200_000) -> str:
    """The text of a PDF with real text (not a scanned image), read in memory: uncompressed and Flate streams, the
    strings of Tj/TJ. Nothing is stored. '' if there is none."""
    if not raw.startswith(b'%PDF'): return ''
    parts = []
    for m in _STREAM.finditer(raw[:MAX_FILE_BYTES]):
        data = m.group(1)
        try: data = zlib.decompress(data)
        except zlib.error: pass
        for op in _TEXT_OP.findall(data):
            for s in _STR.findall(op):
                if s[:1] == b'<':   # hex string (simple fonts); two-byte glyph codes give nothing readable, and that is fine
                    h = re.sub(rb'\s', b'', s[1:-1]); h += b'0' * (len(h) % 2)
                    try: parts.append(bytes.fromhex(h.decode()).decode('latin-1', 'replace'))
                    except ValueError: pass
                else:
                    parts.append(_unescape(s[1:-1]).decode('latin-1', 'replace'))
            parts.append(' ' if op.rstrip().endswith(b'TJ') or op.rstrip().endswith(b'Tj') else '\n')
        parts.append('\n')
        if sum(len(p) for p in parts) > limit: break
    text = ''.join(parts)
    return re.sub(r'[ \t]+', ' ', text).strip()[:limit]


_DATE = re.compile(r'(\d{1,2})[/.\-](\d{1,2})[/.\-](\d{4})|(\d{4})-(\d{2})-(\d{2})')
_END_WORDS = re.compile(r'hasta|vencimiento|caducidad|fecha de fin|fin de (?:la )?cobertura|expir\w*|valid until|valid to|end date|g[uü]ltig bis|scadenza|validade|fim', re.I)
_START_WORDS = re.compile(r'desde|inicio|fecha de efecto|efecto|valid from|start date|g[uü]ltig ab|decorrenza|in[ií]cio', re.I)
_NUM = r'(?:\s*(?:n[uú]m(?:ero)?\.?|nr\.?|no\.?|number|n[ºo°.]*))?'
_POLICY = re.compile(r'(?:n[ºo°.]*\s*(?:de\s*)?p[oó]liza|p[oó]liza' + _NUM + r'|policy' + _NUM + r'|polizza' + _NUM + r'|ap[oó]lice' + _NUM + r'|polisnummer|police' + _NUM
                     + r')\s*[:#]?\s*([A-Z0-9][A-Z0-9\-/.]{4,30})', re.I)


def _as_date(m) -> str | None:
    d, mo, y = (m.group(1), m.group(2), m.group(3)) if m.group(1) else (m.group(6), m.group(5), m.group(4))
    try: return _dt.date(int(y), int(mo), int(d)).isoformat()
    except ValueError: return None


def _date_after(flat: str, words) -> str | None:
    """The first date that comes right after one of the words (within 40 characters)."""
    for w in words.finditer(flat):
        m = _DATE.search(flat, w.end(), w.end() + 40)
        if m and _as_date(m): return _as_date(m)
    return None


def propose(text: str) -> dict:
    """What the text of a policy seems to say: last day, first day and policy number. Only a proposal: the diver
    confirms or corrects it, and nothing is saved without that confirmation."""
    out = {}
    if not text: return out
    flat = ' '.join(text.split())
    to, fr = _date_after(flat, _END_WORDS), _date_after(flat, _START_WORDS)
    if not to:
        dates = sorted({d for d in (_as_date(m) for m in _DATE.finditer(flat)) if d})
        if dates: to = dates[-1]; fr = fr or (dates[0] if len(dates) > 1 else None)
    if to: out['valid_to'] = to
    if fr and (not to or fr <= to): out['valid_from'] = fr
    m = _POLICY.search(flat)
    if m and re.search(r'\d', m.group(1)): out['policy_number'] = m.group(1).strip('.-/')
    return out


# ------------------------------------------------------------------------------------------------ providers
class NotAvailable(Exception):
    """The direct connection (API) is not active: there is no agreement with that insurer yet."""


class InsuranceProvider:
    """«enlace» mode (the one used now): WORLDIVES only links to the insurer's website with its partner code. Adding an
    insurer means configuring it in Administración, never changing this code."""
    mode = 'link'

    def __init__(self, row):
        self.row = row

    def offer_url(self, product, audience: str) -> str:
        url = (_get(product, 'center_url') if audience == 'centro' else None) or _get(product, 'diver_url')
        url = link_for(url, _get(self.row, 'partner_code'))
        if not url_allowed(url, clean_domains(_get(self.row, 'allowed_domains_list') or [])): raise ValueError('Dirección no autorizada.')
        return url

    def supports_prefill(self) -> bool:
        return False   # in «enlace» mode no personal data ever goes to the insurer

    def quote(self, *a, **k):
        raise NotAvailable('Precio en directo: pendiente de acuerdo con la aseguradora.')

    def purchase(self, *a, **k):
        raise NotAvailable('Contratación directa: pendiente de acuerdo con la aseguradora.')


class ApiInsuranceProvider(InsuranceProvider):
    """«API» mode (future): price, purchase and the issued policy arriving by itself in the profile through a signed
    notice. Prepared, switched off until there is an agreement (WOD_INSURANCE_API=1 and the insurer's configuration)."""
    mode = 'api'

    def __init__(self, row, enabled: bool = False):
        super().__init__(row); self.enabled = enabled

    def supports_prefill(self) -> bool:
        return self.enabled

    def quote(self, *a, **k):
        if not self.enabled: raise NotAvailable('Conexión directa desactivada hasta que haya acuerdo con la aseguradora.')
        raise NotAvailable('Sin implementar: depende de la API de cada aseguradora.')

    purchase = quote


def provider_for(row, api_enabled: bool = False) -> InsuranceProvider:
    return ApiInsuranceProvider(row, api_enabled) if _get(row, 'mode') == 'api' else InsuranceProvider(row)
