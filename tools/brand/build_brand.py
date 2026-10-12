"""Builds every brand file of WORLDIVES DISCOVERY from the two originals (docs/marca/originales/).

    python tools/brand/build_brand.py

The originals are JPG on white. This script never redraws shapes: it only removes the white background (without
white halos: colour-to-alpha on the edge band), crops, scales and composes. The ocean of the globe is white in the
original and stays white (everything inside the circle of the globe is kept opaque). Output: public/assets/brand/
(web, PWA, emails, PDF) and movil/assets/ (Capacitor, Google Play, App Store).
"""
from __future__ import annotations

import io
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

ROOT = Path(__file__).resolve().parents[2]
SRC = ROOT / 'docs' / 'marca' / 'originales'
OUT = ROOT / 'public' / 'assets' / 'brand'
APP = ROOT / 'movil' / 'assets'

ABISMO = (0x01, 0x1C, 0x3C)
PROFUNDO = (0x04, 0x3D, 0x6C)
OCEANO = (0x07, 0x68, 0x98)
TURQUESA = (0x1C, 0xA5, 0xC7)
AGUA = (0x87, 0xE2, 0xEF)
WHITE = (255, 255, 255)

# Geometry of the full logo (worldives-logo-completo.jpg, 1280 × 853), measured on the original.
GLOBE_C, GLOBE_R = (625, 316), 284          # circle of the globe (bbox 341–909 × 32–600)
SYMBOL_BOX = (330, 22, 921, 611)            # symbol with a small margin
WORDMARK_BOX = (100, 608, 1168, 815)        # «WORLDIVES» + «— DISCOVERY —»
WORL_DIVES_X = 768                          # gap between «WORL» and «DIVES»
TEXT_TOP = 608


def remove_white(img: Image.Image, keep_circle=None, text_top=None) -> Image.Image:
    """White background → transparent. Only the white connected to the border is background; a thin band around
    the shapes gets a soft alpha (colour-to-alpha against white) so there are no white halos."""
    rgb = np.asarray(img.convert('RGB')).astype(np.float32)
    h, w, _ = rgb.shape
    whiteish = (rgb.min(2) > 226) & ((rgb.max(2) - rgb.min(2)) < 24)
    m = Image.fromarray((whiteish * 255).astype(np.uint8), 'L').copy()
    for p in [(0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)]:
        if m.getpixel(p) == 255: ImageDraw.floodfill(m, p, 128)
    bg = np.asarray(m) == 128
    if text_top is not None:            # inside the letters (O, R, D…) the white is a hole, not a shape
        bg[text_top:] |= whiteish[text_top:]
    if keep_circle:
        (cx, cy), r = keep_circle
        yy, xx = np.mgrid[0:h, 0:w]
        bg &= ((xx - cx) ** 2 + (yy - cy) ** 2) > (r - 1.5) ** 2
    # edge band: background pixels next to shapes and shape pixels next to background
    bgimg = Image.fromarray((bg * 255).astype(np.uint8))
    near_shape = np.asarray(Image.fromarray((~bg * 255).astype(np.uint8)).filter(ImageFilter.MaxFilter(5))) > 0
    near_bg = np.asarray(bgimg.filter(ImageFilter.MaxFilter(5))) > 0
    band = (bg & near_shape) | (~bg & near_bg)
    if keep_circle:
        band &= ((xx - cx) ** 2 + (yy - cy) ** 2) > (r - 1.5) ** 2
    alpha = np.where(bg, 0.0, 1.0)
    out = rgb.copy()
    a = np.clip((255.0 - rgb.min(2)) / 255.0, 0, 1)
    a = np.clip(a * 1.15, 0, 1)                      # firm up anti-aliased edges
    sel = band & (a > 0)
    safe = np.maximum(a, 1e-3)[..., None]
    unmixed = 255.0 - (255.0 - rgb) / safe
    out[sel] = np.clip(unmixed[sel], 0, 255)
    alpha[band] = a[band]
    rgba = np.dstack([out, alpha * 255]).astype(np.uint8)
    return Image.fromarray(rgba, 'RGBA')


def recolor_text_for_dark(im: Image.Image, top: int, split_x: int) -> Image.Image:
    """«WORL», «DISCOVERY» and the lines in white; «DIVES» in Agua clara. The symbol keeps its colours."""
    a = np.asarray(im).copy()
    h, w, _ = a.shape
    yy, xx = np.mgrid[0:h, 0:w]
    text = (yy >= top) & (a[..., 3] > 0)
    dives = text & (xx >= split_x) & (yy < top + 135)
    other = text & ~dives
    a[other, :3] = WHITE
    a[dives, :3] = AGUA
    return Image.fromarray(a, 'RGBA')


def trim(im: Image.Image, pad=0) -> Image.Image:
    box = im.getbbox()
    im = im.crop(box)
    if pad:
        c = Image.new('RGBA', (im.width + 2 * pad, im.height + 2 * pad), (0, 0, 0, 0)); c.paste(im, (pad, pad)); im = c
    return im


def save(im: Image.Image, path: Path, webp=True, quality=92):
    path.parent.mkdir(parents=True, exist_ok=True)
    im.save(path.with_suffix('.png'), optimize=True)
    if webp: im.save(path.with_suffix('.webp'), quality=quality, method=6)


def fit(im: Image.Image, w=None, h=None) -> Image.Image:
    if w and not h: h = round(im.height * w / im.width)
    if h and not w: w = round(im.width * h / im.height)
    return im.resize((w, h), Image.LANCZOS)


def horizontal(symbol: Image.Image, wordmark: Image.Image, height=300) -> Image.Image:
    s = fit(symbol, h=height)
    t = fit(wordmark, h=round(height * 0.52))
    gap = round(height * 0.10)
    c = Image.new('RGBA', (s.width + gap + t.width, height), (0, 0, 0, 0))
    c.alpha_composite(s, (0, 0)); c.alpha_composite(t, (s.width + gap, (height - t.height) // 2))
    return c


def on_bg(im: Image.Image, size, bg, scale=0.8, radius=0) -> Image.Image:
    w, h = size if isinstance(size, tuple) else (size, size)
    c = Image.new('RGBA', (w, h), bg + (255,))
    k = min(w * scale / im.width, h * scale / im.height)
    s = im.resize((round(im.width * k), round(im.height * k)), Image.LANCZOS)
    c.alpha_composite(s, ((w - s.width) // 2, (h - s.height) // 2))
    if radius:
        mask = Image.new('L', (w, h), 0); ImageDraw.Draw(mask).rounded_rectangle((0, 0, w - 1, h - 1), radius=radius, fill=255)
        c.putalpha(mask)
    return c


def main():
    logo = Image.open(SRC / 'worldives-logo-completo.jpg')
    icon = Image.open(SRC / 'worldives-icono-app.jpg')

    full = remove_white(logo, keep_circle=(GLOBE_C, GLOBE_R), text_top=TEXT_TOP)
    full_dark = recolor_text_for_dark(full, TEXT_TOP, WORL_DIVES_X)
    vertical = trim(full, 16); vertical_dark = trim(full_dark, 16)
    symbol = trim(full.crop(SYMBOL_BOX), 6)
    wordmark = trim(full.crop(WORDMARK_BOX)); wordmark_dark = trim(full_dark.crop(WORDMARK_BOX))

    save(vertical, OUT / 'worldives-logo-vertical'); save(vertical_dark, OUT / 'worldives-logo-vertical-oscuro')
    save(fit(vertical, w=520), OUT / 'worldives-logo-vertical-520'); save(fit(vertical_dark, w=240), OUT / 'worldives-logo-vertical-oscuro-240')
    hz = horizontal(symbol, wordmark); hz_dark = horizontal(symbol, wordmark_dark)
    save(hz, OUT / 'worldives-logo-horizontal'); save(hz_dark, OUT / 'worldives-logo-horizontal-oscuro')
    save(fit(hz, h=96), OUT / 'worldives-logo-horizontal-96'); save(fit(hz_dark, h=96), OUT / 'worldives-logo-horizontal-oscuro-96')
    save(symbol, OUT / 'worldives-simbolo')
    for n in (512, 256, 128, 64):
        save(fit(symbol, w=n), OUT / f'worldives-simbolo-{n}')

    # App icon: the rounded navy square of the original, corners made transparent (white connected to the border)
    app = trim(remove_white(icon))
    side = max(app.size); sq = Image.new('RGBA', (side, side), (0, 0, 0, 0)); sq.alpha_composite(app, ((side - app.width) // 2, (side - app.height) // 2))
    # full-bleed version (no transparent corners) for Apple, Google Play, App Store, maskable and PDF
    inner = app.crop((int(app.width * .06), int(app.height * .06), int(app.width * .94), int(app.height * .94)))
    bleed = on_bg(inner, 1024, ABISMO, scale=1.0)
    save(fit(sq, w=512), OUT / 'worldives-icono-512'); save(fit(sq, w=192), OUT / 'worldives-icono-192')
    save(fit(sq, w=32), OUT / 'favicon-32', webp=False)
    fit(bleed, w=180).convert('RGB').save(OUT / 'apple-touch-icon-180.png', optimize=True)
    # maskable: the symbol inside the 80 % safe zone on Abismo
    mask = on_bg(inner, 512, ABISMO, scale=0.80)
    save(mask, OUT / 'worldives-icono-maskable-512', webp=False)
    sq.resize((48, 48), Image.LANCZOS).save(OUT / 'favicon.ico', sizes=[(16, 16), (32, 32), (48, 48)])
    # for e-mails (on the dark header) and PDF (JPEG, no transparency needed on Abismo)
    fit(bleed, w=96).convert('RGB').save(OUT / 'worldives-icono-correo-96.png', optimize=True)
    fit(bleed, w=240).convert('RGB').save(OUT / 'worldives-icono-pdf.jpg', quality=92)

    # Share image (og:image) 1200 × 630: dark horizontal logo on a brand gradient
    og = Image.new('RGBA', (1200, 630), ABISMO + (255,))
    grad = np.zeros((630, 1200, 3), np.float32)
    t = np.linspace(0, 1, 1200)[None, :, None]
    grad[:] = np.array(ABISMO) * (1 - t) + np.array(PROFUNDO) * t
    og = Image.fromarray(grad.astype(np.uint8)).convert('RGBA')
    lg = fit(vertical_dark, h=470)
    og.alpha_composite(lg, ((1200 - lg.width) // 2, (630 - lg.height) // 2))
    og.convert('RGB').save(OUT / 'og-image-1200x630.png', optimize=True); og.convert('RGB').save(OUT / 'og-image-1200x630.jpg', quality=90)

    # App (Capacitor) and stores
    APP.mkdir(parents=True, exist_ok=True)
    bleed.convert('RGB').save(APP / 'icon-only.png')                                   # 1024, no alpha
    on_bg(inner, 1024, ABISMO, scale=1.0).save(APP / 'icon-background-full.png')
    fg = Image.new('RGBA', (1024, 1024), (0, 0, 0, 0)); s = fit(symbol, w=round(1024 * 0.62)); fg.alpha_composite(s, ((1024 - s.width) // 2, (1024 - s.height) // 2))
    fg.save(APP / 'icon-foreground.png'); Image.new('RGB', (1024, 1024), ABISMO).save(APP / 'icon-background.png')
    for name, lg_ in (('splash.png', vertical_dark), ('splash-dark.png', vertical_dark)):
        sp = Image.new('RGBA', (2732, 2732), ABISMO + (255,)); l2 = fit(lg_, w=1100); sp.alpha_composite(l2, ((2732 - l2.width) // 2, (2732 - l2.height) // 2)); sp.convert('RGB').save(APP / name)
    fit(bleed, w=512).convert('RGB').save(APP / 'google-play-icono-512.png')
    fg_ = Image.fromarray(grad.astype(np.uint8)).resize((1024, 500)).convert('RGBA'); l3 = fit(hz_dark, h=300); fg_.alpha_composite(l3, ((1024 - l3.width) // 2, 100)); fg_.convert('RGB').save(APP / 'google-play-grafico-1024x500.png')
    bleed.convert('RGB').save(APP / 'app-store-icono-1024.png')
    print('ok')


if __name__ == '__main__':
    main()
