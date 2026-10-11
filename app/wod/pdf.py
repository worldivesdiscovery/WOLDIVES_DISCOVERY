"""Small PDF writer with embedded TrueType fonts (v50.34).

The old vouchers used the 14 built-in PDF fonts, which only know Western European letters: Polish, Russian or
Chinese text came out as question marks. Here every text is written with Noto Sans / Noto Sans SC embedded as
CID fonts (Identity-H), so any of the 10 languages of the site prints correctly, and the PDF keeps a ToUnicode map
so the text can be searched and copied.

Only the standard library is required. When fontTools is installed the fonts are subset to the glyphs used
(a voucher weighs a few dozen KB); without it the whole font file is embedded.
"""
from __future__ import annotations

import struct
import zlib
from pathlib import Path

FONT_DIR = Path(__file__).resolve().parents[1] / 'fonts'
FAMILIES = {False: ('NotoSans-Regular.ttf', 'NotoSansSC-Regular.ttf'), True: ('NotoSans-Bold.ttf', 'NotoSansSC-Bold.ttf')}


class TrueType:
    """Reads what a PDF needs from a TrueType file: character map, advance widths and global metrics."""

    def __init__(self, path: Path):
        self.path = Path(path)
        self.data = self.path.read_bytes()
        d = self.data
        num = struct.unpack('>H', d[4:6])[0]
        self.tables = {}
        for i in range(num):
            tag, _, off, length = struct.unpack('>4sIII', d[12 + 16 * i:28 + 16 * i])
            self.tables[tag.decode('latin-1')] = (off, length)
        head = self._t('head')
        self.upem = struct.unpack('>H', head[18:20])[0]
        self.bbox = struct.unpack('>hhhh', head[36:44])
        hhea = self._t('hhea')
        self.ascent, self.descent = struct.unpack('>hh', hhea[4:8])
        nhm = struct.unpack('>H', hhea[34:36])[0]
        hmtx = self._t('hmtx')
        self.advances = [struct.unpack('>H', hmtx[4 * i:4 * i + 2])[0] for i in range(nhm)]
        self.cap_height = self.ascent
        if 'OS/2' in self.tables:
            os2 = self._t('OS/2')
            if len(os2) >= 90: self.cap_height = struct.unpack('>h', os2[88:90])[0]
        self.cmap = self._read_cmap()
        self.name = self.path.stem.replace(' ', '')

    def _t(self, tag):
        off, length = self.tables[tag]
        return self.data[off:off + length]

    def _read_cmap(self):
        t = self._t('cmap')
        n = struct.unpack('>H', t[2:4])[0]
        best = None
        for i in range(n):
            pid, eid, off = struct.unpack('>HHI', t[4 + 8 * i:12 + 8 * i])
            fmt = struct.unpack('>H', t[off:off + 2])[0]
            if pid in (0, 3) and fmt == 12: best = (off, 12); break
            if pid in (0, 3) and fmt == 4 and not best: best = (off, 4)
        out = {}
        if not best: return out
        off, fmt = best
        if fmt == 12:
            groups = struct.unpack('>I', t[off + 12:off + 16])[0]
            for g in range(groups):
                start, end, gid = struct.unpack('>III', t[off + 16 + 12 * g:off + 28 + 12 * g])
                for cp in range(start, end + 1): out[cp] = gid + cp - start
            return out
        segx2 = struct.unpack('>H', t[off + 6:off + 8])[0]; seg = segx2 // 2
        ends = struct.unpack(f'>{seg}H', t[off + 14:off + 14 + segx2])
        starts = struct.unpack(f'>{seg}H', t[off + 16 + segx2:off + 16 + 2 * segx2])
        deltas = struct.unpack(f'>{seg}h', t[off + 16 + 2 * segx2:off + 16 + 3 * segx2])
        ro_off = off + 16 + 3 * segx2
        ranges = struct.unpack(f'>{seg}H', t[ro_off:ro_off + segx2])
        for i in range(seg):
            for cp in range(starts[i], ends[i] + 1):
                if cp == 0xFFFF: continue
                if ranges[i] == 0: gid = (cp + deltas[i]) & 0xFFFF
                else:
                    p = ro_off + 2 * i + ranges[i] + 2 * (cp - starts[i])
                    gid = struct.unpack('>H', t[p:p + 2])[0]
                    if gid: gid = (gid + deltas[i]) & 0xFFFF
                if gid: out[cp] = gid
        return out

    def advance(self, gid):
        a = self.advances
        return (a[gid] if gid < len(a) else a[-1]) * 1000 / self.upem

    def embed_bytes(self, gids):
        """The font program for the PDF: subset to the glyphs used when fontTools is available (glyph ids kept)."""
        try:
            from fontTools import subset
            from fontTools.ttLib import TTFont
            import io
            f = TTFont(io.BytesIO(self.data))
            opts = subset.Options(); opts.retain_gids = True; opts.notdef_outline = True; opts.hinting = False
            opts.layout_features = []; opts.name_IDs = ['*']; opts.drop_tables += ['GSUB', 'GPOS', 'GDEF']
            s = subset.Subsetter(opts); s.populate(gids=sorted(set(gids) | {0})); s.subset(f)
            buf = io.BytesIO(); f.save(buf); return buf.getvalue()
        except Exception:
            return self.data


_FONTS = {}


def font(file):
    if file not in _FONTS: _FONTS[file] = TrueType(FONT_DIR / file)
    return _FONTS[file]


def _pdf_str(s):
    return '(' + s.replace('\\', '\\\\').replace('(', '\\(').replace(')', '\\)') + ')'


class Document:
    """A4 pages drawn with simple commands. Same drawing interface as the old PdfPage (text, width, fit, wrap,
    box, rect, line, check), plus new_page() for long documents."""
    W, H = 595, 842

    def __init__(self, title='', lang='es'):
        self.pages = [[]]
        self.c = self.pages[0]
        self.used = {}      # font file -> {gid: unicode}
        self.raw = []       # extra raw command lists (QR codes) are appended to self.c directly
        self.title = title
        self.lang = lang

    # --- text -----------------------------------------------------------------
    def _runs(self, text, bold):
        """Splits a text into runs of the same font (Noto Sans first, then Noto Sans SC)."""
        files = FAMILIES[bool(bold)]
        runs = []
        for ch in str(text or ''):
            cp = ord(ch)
            if cp in (0x202F, 0x00A0): cp = 0x20
            pick = None
            for f in files:
                if cp in font(f).cmap: pick = f; break
            if pick is None: pick = files[0]; ch = '?'; cp = 63
            gid = font(pick).cmap.get(cp, 0)
            if runs and runs[-1][0] == pick: runs[-1][1].append((gid, ch))
            else: runs.append([pick, [(gid, ch)]])
        return runs

    def width(self, text, size, bold=False):
        total = 0.0
        for f, glyphs in self._runs(text, bold):
            ft = font(f)
            total += sum(ft.advance(g) for g, _ in glyphs)
        return total * size / 1000

    def fit(self, text, size, maxw, bold=False):
        t = str(text or '')
        if self.width(t, size, bold) <= maxw: return t
        while t and self.width(t + '…', size, bold) > maxw: t = t[:-1]
        return t.rstrip() + '…'

    def wrap(self, text, size, maxw, bold=False, max_lines=3):
        """Word wrap; Chinese (no spaces) wraps by character."""
        words = []
        for w in str(text or '').split():
            if any(0x2E80 <= ord(ch) <= 0x9FFF or 0xFF00 <= ord(ch) <= 0xFFEF for ch in w) and self.width(w, size, bold) > maxw:
                words.extend(list(w))
            else:
                words.append(w)
        lines, cur = [], ''
        for wd in words:
            cjk = len(wd) == 1 and ord(wd) >= 0x2E80
            nxt = (cur + ('' if cjk or (cur and ord(cur[-1]) >= 0x2E80) else ' ') + wd) if cur else wd
            if self.width(nxt, size, bold) <= maxw: cur = nxt
            else:
                if cur: lines.append(cur)
                cur = wd
        if cur: lines.append(cur)
        if len(lines) > max_lines:
            lines = lines[:max_lines]; lines[-1] = self.fit(lines[-1] + ' …', size, maxw, bold)
        return lines or ['']

    def text(self, x, y, text, size=10, color=(0.03, 0.21, 0.29), bold=False, align='left'):
        text = str(text or '')
        if not text: return
        if align == 'right': x -= self.width(text, size, bold)
        elif align == 'center': x -= self.width(text, size, bold) / 2
        self.c += ['BT', '%.3f %.3f %.3f rg' % color, f'{x:.2f} {y:.2f} Td']
        for f, glyphs in self._runs(text, bold):
            used = self.used.setdefault(f, {})
            for g, ch in glyphs: used.setdefault(g, ch)
            key = self._font_key(f)
            self.c += [f'/{key} {size} Tf', '<' + ''.join(f'{g:04X}' for g, _ in glyphs) + '> Tj']
        self.c.append('ET')

    def _font_key(self, f):
        order = list(FAMILIES[False]) + list(FAMILIES[True])
        return f'F{order.index(f) + 1}'

    # --- shapes ---------------------------------------------------------------
    def box(self, x, y, w, h, fill=None, stroke=None, r=8, lw=0.7):
        k = 0.5523 * r
        path = [f'{x + r:.2f} {y:.2f} m', f'{x + w - r:.2f} {y:.2f} l', f'{x + w - r + k:.2f} {y:.2f} {x + w:.2f} {y + r - k:.2f} {x + w:.2f} {y + r:.2f} c', f'{x + w:.2f} {y + h - r:.2f} l',
                f'{x + w:.2f} {y + h - r + k:.2f} {x + w - r + k:.2f} {y + h:.2f} {x + w - r:.2f} {y + h:.2f} c', f'{x + r:.2f} {y + h:.2f} l', f'{x + r - k:.2f} {y + h:.2f} {x:.2f} {y + h - r + k:.2f} {x:.2f} {y + h - r:.2f} c',
                f'{x:.2f} {y + r:.2f} l', f'{x:.2f} {y + r - k:.2f} {x + r - k:.2f} {y:.2f} {x + r:.2f} {y:.2f} c', 'h']
        self.c.append('q')
        if fill: self.c.append('%.3f %.3f %.3f rg' % fill)
        if stroke: self.c += ['%.3f %.3f %.3f RG' % stroke, f'{lw} w']
        self.c += path + ['B' if fill and stroke else 'f' if fill else 'S', 'Q']

    def rect(self, x, y, w, h, fill):
        self.c += ['q', '%.3f %.3f %.3f rg' % fill, f'{x:.2f} {y:.2f} {w:.2f} {h:.2f} re f', 'Q']

    def line(self, x1, y1, x2, y2, color=(0.86, 0.89, 0.91), lw=0.7, dash=None):
        self.c += ['q', '%.3f %.3f %.3f RG' % color, f'{lw} w'] + ([f'[{dash} {dash}] 0 d'] if dash else []) + [f'{x1:.2f} {y1:.2f} m {x2:.2f} {y2:.2f} l S', 'Q']

    def check(self, x, y, color):
        self.c += ['q', '%.3f %.3f %.3f RG' % color, '1.4 w', '1 J 1 j', f'{x:.2f} {y + 3:.2f} m {x + 2.6:.2f} {y + 0.4:.2f} l {x + 7:.2f} {y + 6:.2f} l S', 'Q']

    def new_page(self):
        self.pages.append([]); self.c = self.pages[-1]

    # --- output ---------------------------------------------------------------
    def pdf(self) -> bytes:
        objs = []                      # index 0 -> object 1

        def add(body):
            objs.append(body); return len(objs)

        catalog = add(None); pages_id = add(None)
        font_refs = {}
        order = list(FAMILIES[False]) + list(FAMILIES[True])
        for f in order:
            used = self.used.get(f)
            if not used: continue
            ft = font(f)
            prog = zlib.compress(ft.embed_bytes(used.keys()))
            ff = add(f'<< /Length {len(prog)} /Filter /FlateDecode >>\nstream\n'.encode() + prog + b'\nendstream')
            name = 'WOD' + chr(65 + order.index(f)) * 6 + '+' + ft.name.replace('-', '')
            desc = add(f'<< /Type /FontDescriptor /FontName /{name} /Flags 32 /FontBBox [{" ".join(str(int(v * 1000 / ft.upem)) for v in ft.bbox)}] '
                       f'/ItalicAngle 0 /Ascent {int(ft.ascent * 1000 / ft.upem)} /Descent {int(ft.descent * 1000 / ft.upem)} '
                       f'/CapHeight {int(ft.cap_height * 1000 / ft.upem)} /StemV 80 /FontFile2 {ff} 0 R >>'.encode())
            gids = sorted(used)
            widths = ' '.join(f'{g} [{ft.advance(g):.0f}]' for g in gids)
            cid = add(f'<< /Type /Font /Subtype /CIDFontType2 /BaseFont /{name} /CIDSystemInfo << /Registry (Adobe) /Ordering (Identity) /Supplement 0 >> '
                      f'/FontDescriptor {desc} 0 R /CIDToGIDMap /Identity /DW 1000 /W [{widths}] >>'.encode())
            bf = '\n'.join(f'<{g:04X}> <{"".join(f"{b:02X}" for b in used[g].encode("utf-16-be"))}>' for g in gids)
            cmap = ('/CIDInit /ProcSet findresource begin 12 dict begin begincmap /CIDSystemInfo << /Registry (Adobe) /Ordering (UCS) /Supplement 0 >> def '
                    '/CMapName /Adobe-Identity-UCS def /CMapType 2 def 1 begincodespacerange <0000> <FFFF> endcodespacerange\n'
                    + ''.join(f'{min(100, len(gids) - i)} beginbfchar\n' + '\n'.join(bf.split('\n')[i:i + 100]) + '\nendbfchar\n' for i in range(0, len(gids), 100))
                    + 'endcmap CMapName currentdict /CMap defineresource pop end end').encode()
            tu = add(f'<< /Length {len(cmap)} >>\nstream\n'.encode() + cmap + b'\nendstream')
            font_refs[f'F{order.index(f) + 1}'] = add(f'<< /Type /Font /Subtype /Type0 /BaseFont /{name} /Encoding /Identity-H /DescendantFonts [{cid} 0 R] /ToUnicode {tu} 0 R >>'.encode())
        res = '<< /Font << ' + ' '.join(f'/{k} {v} 0 R' for k, v in font_refs.items()) + ' >> >>'
        kids = []
        for cmds in self.pages:
            content = zlib.compress('\n'.join(cmds).encode('latin-1'))
            cs = add(f'<< /Length {len(content)} /Filter /FlateDecode >>\nstream\n'.encode() + content + b'\nendstream')
            kids.append(add(f'<< /Type /Page /Parent {pages_id} 0 R /MediaBox [0 0 {self.W} {self.H}] /Resources {res} /Contents {cs} 0 R >>'.encode()))
        objs[catalog - 1] = f'<< /Type /Catalog /Pages {pages_id} 0 R /Lang {_pdf_str(self.lang)} >>'.encode()
        objs[pages_id - 1] = f'<< /Type /Pages /Kids [{" ".join(f"{k} 0 R" for k in kids)}] /Count {len(kids)} >>'.encode()
        title = 'FEFF' + ''.join(f'{b:02X}' for b in (self.title or 'WORLDIVES DISCOVERY').encode('utf-16-be'))
        info = add(f'<< /Title <{title}> /Producer (WORLDIVES DISCOVERY) >>'.encode())
        out = bytearray(b'%PDF-1.7\n%\xe2\xe3\xcf\xd3\n'); offs = []
        for i, body in enumerate(objs, 1):
            offs.append(len(out)); out += f'{i} 0 obj\n'.encode() + body + b'\nendobj\n'
        xref = len(out)
        out += f'xref\n0 {len(objs) + 1}\n0000000000 65535 f \n'.encode()
        for o in offs: out += f'{o:010d} 00000 n \n'.encode()
        out += f'trailer\n<< /Size {len(objs) + 1} /Root {catalog} 0 R /Info {info} 0 R >>\nstartxref\n{xref}\n%%EOF'.encode()
        return bytes(out)
