"""Addresses of the files of the web (v50.46, «carpetas limpias»): public/js, css, idiomas, img/{marca,portada,destinos,
iconos}, fuentes and lib. The old /assets/… addresses (e-mails already sent, old caches, data saved before
v50.46) are redirected to the new ones. Separated from app/server.py (plan of docs/estructura.md). Pure functions."""
from __future__ import annotations

STATIC_PREFIXES = ('/js/', '/css/', '/idiomas/', '/img/', '/fuentes/', '/lib/')
_LEGACY_IMAGES = {**{n: 'destinos' for n in ('australia', 'california', 'egipto', 'galapagos', 'maldivas', 'mexico', 'micronesia', 'tailandia')},
                  **{n: 'portada' for n in ('portada-arrecife', 'fondosuperior', 'fondo1', 'fondo', 'logbook1')}}
LEGACY_ASSET_PREFIXES = (('/assets/vendor/', '/lib/'), ('/assets/js/', '/js/'), ('/assets/css/', '/css/'),
                         ('/assets/i18n/', '/idiomas/'), ('/assets/fonts/', '/fuentes/'))


# The brand files the web uses (public/img/marca/). The rest of the brand kit (big logos, the symbol in every size,
# PNG/WebP twins) is in docs/marca/kit/, delivered but not served (v50.46: no file that is not used).
BRAND_WEB_FILES = ('worldives-logo-horizontal-96.webp', 'worldives-logotipo-oscuro-260.webp', 'favicon.ico', 'favicon-32.png',
                   'worldives-icono-192.png', 'worldives-icono-512.png', 'worldives-icono-maskable-512.png', 'apple-touch-icon-180.png',
                   'worldives-icono-correo-96.png', 'worldives-icono-pdf.jpg', 'og-image-1200x630.png')


def brand_folder(name):
    """Subfolder of the brand kit (docs/marca/kit/) for a brand file: logo, simbolo, iconos or redes."""
    if name.startswith(('worldives-logo', 'worldives-logotipo')): return 'logo'
    if name.startswith('worldives-simbolo'): return 'simbolo'
    if name.startswith('og-image'): return 'redes'
    return 'iconos'


def legacy_asset_url(path):
    """The new address of an old /assets/… address (links in emails already sent, old caches, old data), or None."""
    if path.startswith('/assets/brand/'):
        name = path[len('/assets/brand/'):]
        return f'/img/marca/{name}' if name in BRAND_WEB_FILES else None
    for old, new in LEGACY_ASSET_PREFIXES:
        if path.startswith(old):
            rest = path[len(old):]
            return new + (rest.lower() if old == '/assets/fonts/' else rest)    # font files are lower case since v50.46
    if path.startswith('/assets/images/'):
        name = path[len('/assets/images/'):]
        if name == 'BUCEADORES.webp': return '/img/portada/buceadores.webp'
        if name.startswith('buceador') and name.endswith('.png'): return '/img/iconos/' + name
        stem = name.rsplit('.', 1)[0]
        if stem in _LEGACY_IMAGES: return f'/img/{_LEGACY_IMAGES[stem]}/{name}'
    return None


def legacy_path_map():
    """Old → new exact paths for the data migration (the images and brand files the site ships)."""
    out = {'/assets/images/BUCEADORES.webp': '/img/portada/buceadores.webp', '/assets/images/buceador1.png': '/img/iconos/buceador1.png',
           '/assets/images/buceador2.png': '/img/iconos/buceador2.png'}
    for stem, folder in _LEGACY_IMAGES.items(): out[f'/assets/images/{stem}.webp'] = f'/img/{folder}/{stem}.webp'
    for name in BRAND_WEB_FILES: out[f'/assets/brand/{name}'] = f'/img/marca/{name}'
    return out
