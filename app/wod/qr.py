"""v50.57 · Un único generador de códigos QR para toda la web (revisión general, punto 1.2).

Antes había cinco formas de hacer un QR (SVG de la reserva, SVG de la librería en «Crear QR», PNG del widget, la matriz
del cartel y la del PDF), cada una con su margen y su nivel de corrección. Ahora todas salen de matrix():

- svg(): una sola ruta (no un rectángulo por cuadro), ligera para ir dentro de la página de la reserva;
- png(): para correos (imagen incrustada), impresoras y aplicaciones que no abren SVG;
- pdf_ops(): las órdenes de dibujo de los PDF (justificante y ficha del buceador);
- rows(): la matriz como texto «0/1» que dibuja el navegador (cartel de la salida).

Nivel de corrección M (15 %): se lee aunque el papel esté algo doblado o mojado. El margen blanco alrededor (zona de
silencio) es de 4 módulos, el que pide la norma ISO/IEC 18004 para que cualquier móvil lo lea a la primera.
"""
from __future__ import annotations

import html
import io

QUIET = 4


def matrix(payload: str) -> list[list[bool]]:
    """The modules of the QR of `payload` (True = dark), without the quiet zone."""
    import qrcode   # requirements.txt
    qr = qrcode.QRCode(box_size=1, border=0, error_correction=qrcode.constants.ERROR_CORRECT_M)
    qr.add_data(payload); qr.make(fit=True)
    return [[bool(v) for v in row] for row in qr.get_matrix()]


def rows(payload: str) -> list[str]:
    """The same matrix as text rows of «0» and «1» (drawn by the browser)."""
    return [''.join('1' if v else '0' for v in row) for row in matrix(payload)]


def svg(payload: str, color: str = '#000000', size: int | None = None, quiet: int = QUIET) -> bytes:
    """A QR as SVG: one path with the runs of dark modules of each row, white background and quiet zone."""
    m = matrix(payload); n = len(m); full = n + 2 * quiet
    d = []
    for y, row in enumerate(m):
        x = 0
        while x < n:
            if row[x]:
                start = x
                while x < n and row[x]: x += 1
                d.append(f'M{start + quiet} {y + quiet}h{x - start}v1h-{x - start}z')
            else:
                x += 1
    px = size or full * 8
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {full} {full}" width="{px}" height="{px}" shape-rendering="crispEdges" role="img">'
            f'<rect width="{full}" height="{full}" fill="#ffffff"/><path fill="{html.escape(color)}" d="{"".join(d)}"/></svg>').encode()


def png(payload: str, scale: int = 10, quiet: int = QUIET, color: tuple = (0, 0, 0)) -> bytes:
    """A QR as PNG (Pillow): `scale` pixels per module."""
    from PIL import Image
    m = matrix(payload); n = len(m); full = n + 2 * quiet
    img = Image.new('RGB', (full, full), (255, 255, 255))
    px = img.load()
    for y, row in enumerate(m):
        for x, v in enumerate(row):
            if v: px[x + quiet, y + quiet] = color
    img = img.resize((full * scale, full * scale), Image.NEAREST)
    buf = io.BytesIO(); img.save(buf, 'PNG', optimize=True)
    return buf.getvalue()


def pdf_ops(payload: str, x0: float, y0: float, size: float, quiet: int = 2) -> list[str]:
    """PDF drawing operators: the QR in a `size` square whose bottom left corner is (x0, y0), with a white quiet zone."""
    m = matrix(payload); n = len(m); c = size / n
    q = quiet * c
    ops = ['q', '1 1 1 rg', f'{x0 - q:.2f} {y0 - q:.2f} {size + 2 * q:.2f} {size + 2 * q:.2f} re f', '0 0 0 rg']
    for r, row in enumerate(m):
        x = 0
        while x < n:
            if row[x]:
                start = x
                while x < n and row[x]: x += 1
                ops.append(f'{x0 + start * c:.2f} {y0 + (n - 1 - r) * c:.2f} {(x - start) * c + .03:.2f} {c + .03:.2f} re f')
            else:
                x += 1
    ops.append('Q')
    return ops
