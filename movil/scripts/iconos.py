"""Android icons and splash screens of the app from the brand kit (docs/marca/app/). WORLDIVES Pruebas gets the same
icon with an orange «TEST» band (encargo «App móvil en 3 módulos», 9.1). Run: python3 movil/scripts/iconos.py"""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
MARCA = ROOT / 'docs' / 'marca' / 'app'
RES = ROOT / 'movil' / 'android' / 'app' / 'src'
FUENTE = ROOT / 'app' / 'fonts' / 'notosans-bold.ttf'
ABISMO = (1, 28, 60)
NARANJA = (224, 123, 0)
DENS = {'mdpi': 1, 'hdpi': 1.5, 'xhdpi': 2, 'xxhdpi': 3, 'xxxhdpi': 4}


def banda(im, y0, y1, texto):
    """An orange band across the image with TEST in dark text (readable on the dark blue icon)."""
    im = im.copy(); d = ImageDraw.Draw(im); w, h = im.size
    d.rectangle([0, int(h * y0), w, int(h * y1)], fill=NARANJA + (255,))
    size = int(h * (y1 - y0) * 0.7); f = ImageFont.truetype(str(FUENTE), size)
    tw = d.textlength(texto, font=f)
    d.text(((w - tw) / 2, h * y0 + (h * (y1 - y0) - size) / 2 - size * 0.12), texto, font=f, fill=(31, 19, 0, 255))
    return im


def redonda(im):
    m = Image.new('L', im.size, 0); ImageDraw.Draw(m).ellipse([0, 0, im.width - 1, im.height - 1], fill=255)
    out = Image.new('RGBA', im.size, (0, 0, 0, 0)); out.paste(im, (0, 0), m); return out


def iconos(variante, prueba):
    base = Image.open(MARCA / 'icon-only.png').convert('RGBA')
    fg = Image.open(MARCA / 'icon-foreground.png').convert('RGBA')
    if prueba:
        base = banda(base, 0.70, 0.86, 'TEST')
        fg = banda(fg, 0.64, 0.75, 'TEST')   # inside the 66/108 safe zone of adaptive icons
    for dens, k in DENS.items():
        d = RES / variante / 'res' / f'mipmap-{dens}'; d.mkdir(parents=True, exist_ok=True)
        s = int(48 * k); a = int(108 * k)
        base.resize((s, s), Image.LANCZOS).save(d / 'ic_launcher.png')
        redonda(base.resize((s, s), Image.LANCZOS)).save(d / 'ic_launcher_round.png')
        fg.resize((a, a), Image.LANCZOS).save(d / 'ic_launcher_foreground.png')


def splash():
    src = Image.open(MARCA / 'splash.png').convert('RGB')   # logo centred on Abismo, 2732×2732
    sizes = {'mdpi': (320, 480), 'hdpi': (480, 800), 'xhdpi': (720, 1280), 'xxhdpi': (960, 1600), 'xxxhdpi': (1280, 1920)}
    for dens, (w, h) in sizes.items():
        for orient, (ww, hh) in (('port', (w, h)), ('land', (h, w))):
            side = max(ww, hh); im = src.resize((side, side), Image.LANCZOS)
            im = im.crop(((side - ww) // 2, (side - hh) // 2, (side - ww) // 2 + ww, (side - hh) // 2 + hh))
            d = RES / 'main' / 'res' / f'drawable-{orient}-{dens}'; d.mkdir(parents=True, exist_ok=True); im.save(d / 'splash.png', optimize=True)
    src.resize((480, 480), Image.LANCZOS).crop((0, 80, 480, 400)).save(RES / 'main' / 'res' / 'drawable' / 'splash.png', optimize=True)


if __name__ == '__main__':
    iconos('main', False); iconos('pruebas', True); splash()
    print('iconos y pantallas de arranque generados')
