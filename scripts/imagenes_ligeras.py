#!/usr/bin/env python3
"""v50.54 · Lighter copies of the photos that come with the web (public/img/portada and public/img/destinos).

The originals stay as they are (same photos, same look). Next to each one, copies 640, 960 and 1440 px wide
(«nombre-640.webp»…) that the page offers to the browser with srcset: a phone downloads ~60 KB instead of
~400 KB–1.3 MB, and the first screen appears sooner (LCP). A copy is made only when it is narrower than the original.

    python3 scripts/imagenes_ligeras.py            # makes the missing copies
    python3 scripts/imagenes_ligeras.py --todas    # remakes all of them
    python3 scripts/imagenes_ligeras.py --tabla    # prints the widths for WD_IMG_W in world-dives-v8.js
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
FOLDERS = ('portada', 'destinos')
WIDTHS = (640, 960, 1440)
QUALITY = 72
COPY = re.compile(r'-(\d+)$')


def originals():
    for folder in FOLDERS:
        for f in sorted((ROOT / 'public' / 'img' / folder).glob('*.webp')):
            if not COPY.search(f.stem): yield folder, f


def main(argv):
    redo = '--todas' in argv
    table = {}
    for folder, f in originals():
        im = Image.open(f); w, h = im.size
        table[f'{folder}/{f.stem}'] = w
        for width in WIDTHS:
            if width >= w: continue
            out = f.with_name(f'{f.stem}-{width}.webp')
            if out.exists() and not redo: continue
            small = im.convert('RGB').resize((width, round(h * width / w)), Image.LANCZOS)
            small.save(out, 'WEBP', quality=QUALITY, method=6)
            print(f'{out.relative_to(ROOT)}  {out.stat().st_size // 1024} KB (original {f.stat().st_size // 1024} KB)')
    if '--tabla' in argv:
        print('{' + ','.join(f"'{k}':{v}" for k, v in table.items()) + '}')


if __name__ == '__main__':
    main(sys.argv[1:])
