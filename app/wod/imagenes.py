"""Images optimised for the web (v50.50): WebP in several sizes, without the camera's hidden data (EXIF, GPS…).

Used for the preview images of the linked videos and for the species photos. Needs Pillow (requirements.txt; the start
script installs it). Without Pillow the image is still checked and kept as it came, in one size, so nothing breaks.
"""
from __future__ import annotations

import io
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
    done = []
    for target in sorted(set(widths)):
        if done and target > im.width: break
        w = min(target, im.width)
        h = max(1, int(round(im.height * w / im.width)))
        out = im if w == im.width else im.resize((w, h), Image.LANCZOS)
        out.save(folder / f'{name}-{target}.webp', 'WEBP', quality=quality, method=4)
        done.append(target)
    return {'widths': done, 'ratio': round(im.width / im.height, 4)}


def srcset(base: str | None, widths) -> dict | None:
    """The address data the web needs: {'src', 'srcset'} from the stored base address and widths ('400,800')."""
    if not base: return None
    ws = [int(x) for x in str(widths or '').split(',') if str(x).strip().isdigit()]
    if not ws: return {'src': base, 'srcset': ''}
    return {'src': f'{base}-{ws[min(1, len(ws) - 1)]}.webp', 'srcset': ', '.join(f'{base}-{w}.webp {w}w' for w in ws)}
