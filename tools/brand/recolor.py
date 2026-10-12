"""One-off migration to the brand palette of v50.45 (kept for the record and to re-run safely: it is idempotent).
Every colour of the old brand family (teal/petrol blues: hue 180–212°, saturation ≥ 0.45) becomes the palette colour
with the closest lightness. Status colours (greens, reds, ambers), greys and the service colours chosen by centres are
not touched. CSS gets variables; JS (canvas posters), e-mails and PDF get the palette hex (they can not use CSS vars)."""
import colorsys, re, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
PAL = [('abismo', '#011C3C', (1, 28, 60)), ('profundo', '#043D6C', (4, 61, 108)), ('oceano', '#076898', (7, 104, 152)),
       ('turquesa', '#1CA5C7', (28, 165, 199)), ('agua', '#87E2EF', (135, 226, 239))]
# not brand colours: the service colours a centre chooses (planning), seasonal themes and the neon/magazine accents of
# the posters are design choices of their own
KEEP = {'#2563eb', '#3b82f6', '#7c3aed', '#d97706', '#059669', '#e11d48', '#0891b2', '#475569', '#ea580c',
        '#5b8fc4', '#3a6898', '#2ef2ff', '#58d6ff', '#3ee6c5'}


def pick(r, g, b):
    h, l, s = colorsys.rgb_to_hls(r / 255, g / 255, b / 255)
    if not (180 / 360 <= h <= 212 / 360 and s >= 0.45): return None
    if l < 0.20: return PAL[0]
    if l < 0.27: return PAL[1]
    if l < 0.40: return PAL[2]
    if l < 0.58: return PAL[3]
    if l < 0.86: return PAL[4]
    return None


def hexval(m):
    h = m.group(0)[1:]
    if len(h) == 3: h = ''.join(c * 2 for c in h)
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def run(path: Path, css: bool):
    s = path.read_text(encoding='utf-8'); n = 0
    def rep_hex(m):
        nonlocal n
        if m.group(0).lower() in KEEP: return m.group(0)
        p = pick(*hexval(m))
        if not p: return m.group(0)
        n += 1
        return f'var(--wd-{p[0]})' if css else p[1]
    def rep_rgba(m):
        nonlocal n
        r, g, b = int(m.group(1)), int(m.group(2)), int(m.group(3))
        p = pick(r, g, b)
        if not p: return m.group(0)
        n += 1
        return f'rgba({p[2][0]},{p[2][1]},{p[2][2]},{m.group(4)})'
    if css:
        # never touch the definitions of the palette tokens themselves
        parts = re.split(r'(--wd-[a-z]+:\s*#[0-9A-Fa-f]{6})', s)
        s = ''.join(x if x.startswith('--wd-') else re.sub(r'#[0-9a-fA-F]{6}\b|#[0-9a-fA-F]{3}\b(?![0-9a-fA-F])', rep_hex, x) for x in parts)
    else:
        s = re.sub(r"(?<=['\"(:, ])#[0-9a-fA-F]{6}\b", rep_hex, s)
    s = re.sub(r'rgba\((\d+),\s*(\d+),\s*(\d+),\s*([0-9.]+)\)', rep_rgba, s)
    path.write_text(s, encoding='utf-8'); print(path.relative_to(ROOT), n)


if __name__ == '__main__':
    if not sys.argv[1:]: run(ROOT / 'public/assets/css/world-dives-v8.css', True)
    for f in sys.argv[1:] or ('public/assets/js/world-dives-v8.js', 'app/server.py', 'app/wod/pdf.py', 'app/wod/manifest.py', 'public/index.html'):
        run(ROOT / f, False)
