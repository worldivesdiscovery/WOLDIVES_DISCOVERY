"""Images optimised for the web (v50.50): WebP in several sizes, without the camera's hidden data (EXIF, GPS…).

Used for the preview images of the linked videos, the species photos and (v50.53) the photos of the service cards:
those add a JPG for browsers without WebP, the content's fingerprint in the file name (a changed photo is a new address,
so no cache shows the old one), the minimum veil each photo needs so the text on the card keeps WCAG AA contrast, and a
background worker so nobody waits while a photo is resized. Needs Pillow (requirements.txt; the start script installs
it). Without Pillow the image is still checked and kept as it came, in one size, so nothing breaks.
"""
from __future__ import annotations

import hashlib
import io
import queue
import sys
import threading
from pathlib import Path

MAX_PIXELS = 40_000_000          # a bigger image is refused (protection against «decompression bombs»)


def sniff(content: bytes) -> str | None:
    if content.startswith(b'\xff\xd8\xff'): return '.jpg'
    if content.startswith(b'\x89PNG\r\n\x1a\n'): return '.png'
    if content[:4] == b'RIFF' and content[8:12] == b'WEBP': return '.webp'
    if content[:6] in (b'GIF87a', b'GIF89a'): return '.gif'
    return None


def available() -> bool:
    try:
        import PIL.Image  # noqa: F401
        from PIL import features
        return bool(features.check('webp'))
    except Exception:
        return False


def without_metadata(content: bytes) -> bytes:
    """v50.56 (seguros): a private photo (a policy) without its hidden data (EXIF, GPS, camera, comments): the image is
    written again, turned the right way up, in the same format. Without Pillow it is kept as it came."""
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return content
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    with Image.open(io.BytesIO(content)) as im:
        fmt = (im.format or 'JPEG').upper()
        im = ImageOps.exif_transpose(im)
        if fmt == 'JPEG' and im.mode not in ('RGB', 'L'): im = im.convert('RGB')
        out = io.BytesIO()
        kw = {'quality': 92, 'optimize': True} if fmt == 'JPEG' else ({'quality': 90} if fmt == 'WEBP' else {'optimize': True})
        im.save(out, fmt, **kw)   # no exif=, no pnginfo=: nothing of the original metadata is copied
        return out.getvalue()


def variants(content: bytes, folder: Path, name: str, widths: tuple[int, ...], aspect: float | None = None, quality: int = 80) -> dict:
    """Writes <folder>/<name>-<w>.webp for every width (never bigger than the original) and returns
    {'widths': [..], 'ratio': width/height}. aspect: crop to this width/height ratio around the centre (16/9 for videos).
    Raises ValueError with a message for a person when the file is not a usable image."""
    ext = sniff(content)
    if not ext: raise ValueError('El archivo no es una imagen JPG, PNG, WEBP o GIF.')
    folder.mkdir(parents=True, exist_ok=True)
    if not available():
        out = folder / f'{name}-orig{ext}'
        out.write_bytes(content)
        return {'widths': [], 'ratio': None, 'original': out.name}
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        im = Image.open(io.BytesIO(content))
        im.load()
    except (Image.DecompressionBombError, Exception):
        raise ValueError('La imagen no se puede leer o es demasiado grande.') from None
    if im.width * im.height > MAX_PIXELS: raise ValueError('La imagen es demasiado grande.')
    im = ImageOps.exif_transpose(im)
    if im.mode not in ('RGB', 'RGBA'):
        im = im.convert('RGBA' if 'A' in im.getbands() or im.mode == 'P' else 'RGB')
    if im.mode == 'RGBA':
        bg = Image.new('RGB', im.size, (12, 37, 61)); bg.paste(im, mask=im.split()[3]); im = bg
    if aspect:
        w, h = im.size
        if w / h > aspect:
            nw = int(round(h * aspect)); left = (w - nw) // 2; im = im.crop((left, 0, left + nw, h))
        elif w / h < aspect:
            nh = int(round(w / aspect)); top = (h - nh) // 2; im = im.crop((0, top, w, top + nh))
    if im.width < 120 or im.height < 68: raise ValueError('La imagen es demasiado pequeña.')
    done = _save_widths(im, folder, name, widths, quality)
    return {'widths': done, 'ratio': round(im.width / im.height, 4)}


def _save_widths(im, folder: Path, name: str, widths, quality: int) -> list[int]:
    from PIL import Image
    done = []
    for target in sorted(set(widths)):
        if done and target > im.width: break
        w = min(target, im.width)
        h = max(1, int(round(im.height * w / im.width)))
        out = im if w == im.width else im.resize((w, h), Image.LANCZOS)
        out.save(folder / f'{name}-{target}.webp', 'WEBP', quality=quality, method=4)
        done.append(target)
    return done


def fingerprint(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()[:12]


# Service cards (v50.53): the photo fills the card; the CSS crops it from the focal point.
CARD_WIDTHS = (480, 960, 1440)
CARD_JPG_WIDTH = 960
# Colours of the card (world-dives-v8.css, .svc2): the veil and the faintest text on it, light and dark.
CARD_LIGHT = {'veil': (255, 255, 255), 'text': (0x3a, 0x4d, 0x58)}
CARD_DARK = {'veil': (0x01, 0x1c, 0x3c), 'text': (0xb9, 0xcf, 0xdd)}
AA = 4.5
CARD_SMALL_MESSAGE = 'La foto es demasiado pequeña: el mínimo es 320 × 180 px (mejor 1440 × 810 px o más).'


def card_photo(content: bytes, folder: Path, prefix: str, quality: int = 80) -> dict:
    """The photo of a service card or template: WebP sizes plus a JPG, re-encoded (no EXIF or GPS), named
    <prefix>-<fingerprint>. Returns {'base', 'widths', 'jpg', 'ratio', 'veil': {'light', 'dark'}} where base is the
    file name without size or extension and veil the minimum opacity of the veil for AA contrast in each theme."""
    ext = sniff(content)
    if not ext: raise ValueError('El archivo no es una imagen JPG, PNG, WEBP o GIF.')
    folder.mkdir(parents=True, exist_ok=True)
    name = f'{prefix}-{fingerprint(content)}'
    if not available():
        (folder / f'{name}-orig{ext}').write_bytes(content)
        return {'base': name, 'widths': [], 'jpg': None, 'original': f'{name}-orig{ext}', 'ratio': None, 'veil': {'light': 0.86, 'dark': 0.82}}
    from PIL import Image, ImageOps
    Image.MAX_IMAGE_PIXELS = MAX_PIXELS
    try:
        im = Image.open(io.BytesIO(content)); im.load()
    except (Image.DecompressionBombError, Exception):
        raise ValueError('La imagen no se puede leer o es demasiado grande.') from None
    if im.width * im.height > MAX_PIXELS: raise ValueError('La imagen es demasiado grande.')
    im = ImageOps.exif_transpose(im)
    if im.mode != 'RGB':
        if im.mode in ('RGBA', 'LA', 'P'):
            im = im.convert('RGBA'); bg = Image.new('RGB', im.size, (12, 37, 61)); bg.paste(im, mask=im.split()[3]); im = bg
        else:
            im = im.convert('RGB')
    if max(im.size) < 320 or min(im.size) < 180: raise ValueError(CARD_SMALL_MESSAGE)
    widths = _save_widths(im, folder, name, CARD_WIDTHS, quality)
    jw = min(CARD_JPG_WIDTH, im.width)
    jpg = im if jw == im.width else im.resize((jw, max(1, int(round(im.height * jw / im.width)))), Image.LANCZOS)
    jpg.save(folder / f'{name}-{jw}.jpg', 'JPEG', quality=82, optimize=True, progressive=True)
    return {'base': name, 'widths': widths, 'jpg': jw, 'ratio': round(im.width / im.height, 4), 'veil': veil_needed(im)}


_LIN = [((c / 255) / 12.92) if c / 255 <= 0.04045 else (((c / 255) + 0.055) / 1.055) ** 2.4 for c in range(256)]


def _lum(r: float, g: float, b: float) -> float:
    return 0.2126 * _LIN[int(r + .5)] + 0.7152 * _LIN[int(g + .5)] + 0.0722 * _LIN[int(b + .5)]


def contrast(l1: float, l2: float) -> float:
    hi, lo = max(l1, l2), min(l1, l2)
    return (hi + 0.05) / (lo + 0.05)


def _veil_ok(pixels, veil, text_l, alpha, share=0.995) -> bool:
    need = int(len(pixels) * share + 0.999); good = 0
    vr, vg, vb = veil; a, b = alpha, 1 - alpha
    for (r, g, bl) in pixels:
        if contrast(_lum(a * vr + b * r, a * vg + b * g, a * vb + b * bl), text_l) >= AA: good += 1
    return good >= need


def veil_needed(im) -> dict:
    """Minimum opacity of the card's veil so its faintest text keeps WCAG AA (4.5:1) over 99.5 % of the photo, for the
    light veil (white, dark text) and the dark one (navy, light text). The browser blends the veil in sRGB like here."""
    small = im.convert('RGB').copy(); small.thumbnail((64, 64))
    px = list(small.getdata())
    out = {}
    for key, theme in (('light', CARD_LIGHT), ('dark', CARD_DARK)):
        tl = _lum(*theme['text']); lo, hi = 0.0, 1.0
        if _veil_ok(px, theme['veil'], tl, 0.0):
            out[key] = 0.0; continue
        for _ in range(10):
            mid = (lo + hi) / 2
            if _veil_ok(px, theme['veil'], tl, mid): hi = mid
            else: lo = mid
        out[key] = round(min(1.0, hi + 0.01), 2)
    return out


class Worker:
    """One background thread that processes uploaded photos in order, so the request that uploads them answers at
    once. wait_idle() is for tests and for the end of the process."""
    def __init__(self, name: str, size: int = 200):
        self.name = name; self.q: queue.Queue = queue.Queue(maxsize=size); self.lock = threading.Lock(); self.thread = None

    def submit(self, fn, *args) -> bool:
        with self.lock:
            if self.thread is None or not self.thread.is_alive():
                self.thread = threading.Thread(target=self._run, name=f'imagenes-{self.name}', daemon=True); self.thread.start()
        try:
            self.q.put_nowait((fn, args)); return True
        except queue.Full:
            return False

    def _run(self):
        while True:
            fn, args = self.q.get()
            try: fn(*args)
            except Exception as exc:
                sys.stderr.write(f'[imagenes {self.name}] {type(exc).__name__}: {exc}\n')
            finally: self.q.task_done()

    def wait_idle(self, timeout: float = 30.0) -> bool:
        import time
        end = time.time() + timeout
        while time.time() < end:
            if self.q.unfinished_tasks == 0: return True
            time.sleep(0.05)
        return False


def srcset(base: str | None, widths) -> dict | None:
    """The address data the web needs: {'src', 'srcset'} from the stored base address and widths ('400,800')."""
    if not base: return None
    ws = [int(x) for x in str(widths or '').split(',') if str(x).strip().isdigit()]
    if not ws: return {'src': base, 'srcset': ''}
    return {'src': f'{base}-{ws[min(1, len(ws) - 1)]}.webp', 'srcset': ', '.join(f'{base}-{w}.webp {w}w' for w in ws)}
