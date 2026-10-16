#!/usr/bin/env python3
"""v50.58 · Log Book: the two illustrated pages of the passport (left «DIVE LOGBOOK», right «A DIFFERENT WORLD…»).

What came in the owner's zip (public/lib/logbook/assets/page-left.jpg 350×540 and page-right.jpg 366×545) are crops
of a photo of a real book taken at an angle: near the spine the paper curves, so the top edge dips and the dark
background shows in a corner; the right page also shows its stack of sheets and the navy cover on the outer edge.
Straightening that curve would bend the drawing (the lines of text would tilt), so this script does NOT warp it:
- the dark slivers of the photo (background, cover, stack of sheets: 3 to 35 px at the edges) are covered with the
  paper next to them, mirrored, so the page is a straight rectangle and nothing of the drawing moves;
- both pages get the same proportion (the narrower one decides), cutting only paper at the outer edge;
- each page is saved as WebP (the page) and JPG (fallback), at the size of the source. A 2× copy is written only
  when the source is at least twice the page on the screen (never enlarged): with these sources there is none.

When the owner sends the flat originals (scripts/fotos/originales/logbook-izquierda.* and logbook-derecha.*), the
script takes them instead, without any correction, and writes the 1× and 2× copies.

    python3 scripts/fotos/preparar_paginas_logbook.py
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[2]
ASSETS = ROOT / 'public' / 'lib' / 'logbook' / 'assets'
ORIG = ROOT / 'scripts' / 'fotos' / 'originales'
SRC = ASSETS / 'fuente'          # the two photos as they came in the zip (kept, not modified)
PAGE_W = 400                     # width of a page in the book at scale 1 (CSS px): the 2× copy needs 800 px
QUALITY = 86


def flat_original(side):
    for ext in ('png', 'tif', 'tiff', 'webp', 'jpg', 'jpeg'):
        f = ORIG / f'logbook-{side}.{ext}'
        if f.exists():
            return f
    return None


def mirror_down(a, top):
    """Rows above top(x) (background of the photo) get the paper just below the edge, mirrored."""
    h = a.shape[0]
    for x, t in enumerate(top):
        t = int(round(t))
        if t <= 0:
            continue
        src = np.clip(2 * t - np.arange(t), 0, h - 1)
        a[:t, x] = a[src, x]


def mirror_up(a, bottom):
    h = a.shape[0]
    for x, b in enumerate(bottom):
        b = int(round(b))
        if b >= h - 1:
            continue
        rows = np.arange(b + 1, h)
        a[b + 1:, x] = a[np.clip(2 * b - rows, 0, h - 1), x]


def mirror_left(a, edge, rows):
    """Columns right of edge(y) (stack of sheets and cover) get the paper just left of the edge, mirrored."""
    w = a.shape[1]
    for y in rows:
        e = int(round(edge(y)))
        if e >= w - 1:
            continue
        cols = np.arange(e + 1, w)
        a[y, e + 1:] = a[y, np.clip(2 * e - cols, 0, w - 1)]


def clean_left(im):
    a = np.asarray(im.convert('RGB')).copy()
    h, w, _ = a.shape
    # top edge of the paper, curving down towards the spine (right): 0 up to x≈190, 35 px at the right edge
    xs = np.arange(w)
    top = (np.clip(xs - 190, 0, None) / (w - 1 - 190)) ** 1.25 * 37
    mirror_down(a, top + 2)
    # bottom edge, dark sliver at the outer corner (left): 13 px at x=0, none from x≈160
    bottom = np.where(xs < 160, h - 1 - (13 * (1 - xs / 160)), h - 1)
    mirror_up(a, bottom - 2)
    return Image.fromarray(a)


def clean_right(im):
    a = np.asarray(im.convert('RGB')).copy()
    h, w, _ = a.shape
    xs = np.arange(w)
    # top edge dipping towards the spine (left): 34 px at x=0, none from x≈152
    top = np.where(xs < 152, 34 * (1 - xs / 152), 0)
    mirror_down(a, top + 2)
    # outer edge with the stack of sheets and the navy cover, slanting out of the photo at y≈270
    mirror_left(a, lambda y: 334 + 0.118 * y, range(0, 275))
    return Image.fromarray(a.copy()[:h - 3])


def same_ratio(left, right):
    """Both pages with the proportion of the narrower one, cutting paper at the outer edge only."""
    r = min(left.width / left.height, right.width / right.height)
    def cut(im, outer_left):
        w = round(im.height * r)
        return im.crop((im.width - w, 0, im.width, im.height)) if outer_left else im.crop((0, 0, w, im.height))
    return cut(left, True), cut(right, False)


def save(im, name):
    im = im.convert('RGB')
    im.save(ASSETS / f'{name}.webp', 'WEBP', quality=QUALITY, method=6)
    im.save(ASSETS / f'{name}.jpg', 'JPEG', quality=QUALITY, optimize=True, progressive=True)
    out = [f'{name}.webp {im.width}×{im.height}']
    two = ASSETS / f'{name}@2x.webp'
    if im.width >= 2 * PAGE_W:
        im.save(two, 'WEBP', quality=QUALITY, method=6)
        small = im.resize((PAGE_W, round(im.height * PAGE_W / im.width)), Image.LANCZOS)
        small.save(ASSETS / f'{name}.webp', 'WEBP', quality=QUALITY, method=6)
        small.save(ASSETS / f'{name}.jpg', 'JPEG', quality=QUALITY, optimize=True, progressive=True)
        out.append(f'{two.name} {im.width}×{im.height}')
    elif two.exists():
        two.unlink()
    return out


def main():
    lo, ro = flat_original('izquierda'), flat_original('derecha')
    if lo and ro:
        left, right = same_ratio(Image.open(lo), Image.open(ro))
        how = 'originales en plano del titular'
    else:
        left = clean_left(Image.open(SRC / 'page-left.jpg'))
        right = clean_right(Image.open(SRC / 'page-right.jpg'))
        left, right = same_ratio(left, right)
        how = 'fotos del zip (sin enderezar: franjas oscuras cubiertas con el papel de al lado)'
    print(how)
    for line in save(left, 'page-left') + save(right, 'page-right'):
        print(' ', line)
    print(f'  proporción {left.width / left.height:.4f} (ancho / alto)')


if __name__ == '__main__':
    main()
