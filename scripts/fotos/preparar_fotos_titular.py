#!/usr/bin/env python3
"""v50.57 · Revisión general 3.1: the photos sent by the owner, ready for the web.

From scripts/fotos/originales/<n>.webp (as they arrived; not shipped in any zip) to public/img/titular/:
- <name>.webp, the photo at its own width (≤ 2200 px);
- <name>-640.webp, <name>-960.webp and <name>-1440.webp for srcset (phone, tablet and computer);
- <name>.jpg, 1440 px, the fallback for browsers without WebP.
No camera data is kept (Pillow writes only the pixels); each file says whose it is in its EXIF (Copyright and Artist:
«Propiedad de WORLDIVES DISCOVERY»). The focus point of each photo, where its main subject is, lives in the web
(WD_PHOTOS in public/js/world-dives-v8.js) so that a crop for a phone never cuts it. What goes where: docs/fotos/README.md.

    python3 scripts/fotos/preparar_fotos_titular.py
"""
from __future__ import annotations

from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'scripts' / 'fotos' / 'originales'
OUT = ROOT / 'public' / 'img' / 'titular'
PHOTOS = {   # original → name on the web
    '3.webp': 'costa-barco',            # aerial view of a rocky coast with turquoise water and a dive boat
    '4.webp': 'nocturna-pulpo',         # night dive: octopus and moray on the reef, a diver with a torch behind
    '5.webp': 'buceador-rayos',         # a diver in open water under rays of sun, reef on the right
    '6.webp': 'barco-cadena',           # a boat seen from below and its anchor chain going down into the blue
    '7.webp': 'caballito-posidonia',    # a seahorse among posidonia
}
WIDTHS = (640, 960, 1440)
MAX_W = 2200


def owner_exif():
    """The licence of the photo, in its own metadata (EXIF Copyright and Artist)."""
    ex = Image.Exif()
    ex[0x8298] = 'Propiedad de WORLDIVES DISCOVERY'
    ex[0x013B] = 'WORLDIVES DISCOVERY'
    return ex.tobytes()


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    for src, name in PHOTOS.items():
        im = Image.open(SRC / src).convert('RGB')
        if im.width > MAX_W: im = im.resize((MAX_W, round(im.height * MAX_W / im.width)), Image.LANCZOS)
        w, h = im.size
        exif = owner_exif()
        im.save(OUT / f'{name}.webp', 'WEBP', quality=80, method=6, exif=exif)
        for width in WIDTHS:
            if width < w: im.resize((width, round(h * width / w)), Image.LANCZOS).save(OUT / f'{name}-{width}.webp', 'WEBP', quality=74, method=6, exif=exif)
        jw = min(1440, w)
        im.resize((jw, round(h * jw / w)), Image.LANCZOS).save(OUT / f'{name}.jpg', 'JPEG', quality=80, optimize=True, progressive=True, exif=exif)
        sizes = ', '.join(f'{p.name} {p.stat().st_size // 1024} KB' for p in sorted(OUT.glob(f'{name}*')))
        print(f'{name} ({w}×{h}): {sizes}')


if __name__ == '__main__':
    main()
