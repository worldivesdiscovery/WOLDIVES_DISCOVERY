"""v50.57 · Exportaciones (revisión general, punto 1.3).

Cada exportación de la web (administración, centro y freelance) sale de aquí en dos formatos:

- Excel (.xlsx), el de por defecto: columnas con nombre en español, fechas y euros con formato, la primera fila fija y
  con filtro. Lo abren Excel, Numbers, LibreOffice y Google Sheets.
- CSV en UTF-8 con BOM y separador «;», con las fechas y los importes como los escribe Excel en español.

Siempre descargan, también vacías: el archivo sale con las cabeceras y la línea «Sin datos en este periodo».

Sin dependencias: el .xlsx es un zip de XML (Office Open XML, ECMA-376) escrito con la biblioteca estándar.
"""
from __future__ import annotations

import csv
import datetime as _dt
import io
import re
import zipfile
from dataclasses import dataclass, field
from xml.sax.saxutils import escape as _x

EMPTY = 'Sin datos en este periodo'
TYPES = ('text', 'date', 'datetime', 'money', 'int', 'number')
_EPOCH = _dt.datetime(1899, 12, 30)


@dataclass
class Sheet:
    title: str                                   # name of the tab (31 characters at most)
    columns: list                                # [(header, type)] with type in TYPES
    rows: list = field(default_factory=list)
    currency: str = 'EUR'                        # money columns: € unless another currency is said
    totals: list | None = None                   # 17/10 (1.6): a bold row of totals under the data (out of the filter)


def _as_date(v):
    if isinstance(v, _dt.datetime): return v
    if isinstance(v, _dt.date): return _dt.datetime(v.year, v.month, v.day)
    s = str(v or '').strip()
    if not s: return None
    try: return _dt.datetime.fromisoformat(s.replace('Z', '+00:00')[:19]) if len(s) > 10 else _dt.datetime.fromisoformat(s[:10])
    except ValueError: return None


def _as_number(v):
    if v is None or v == '': return None
    try: return float(v)
    except (TypeError, ValueError): return None


# ----------------------------------------------------------------------------------------------------- CSV
def _csv_value(v, kind):
    if v is None: return ''
    if kind == 'date':
        d = _as_date(v); return d.strftime('%d/%m/%Y') if d else str(v)
    if kind == 'datetime':
        d = _as_date(v); return d.strftime('%d/%m/%Y %H:%M') if d else str(v)
    if kind in ('money', 'number'):
        n = _as_number(v); return ('%.2f' % n).replace('.', ',') if n is not None else str(v)
    if kind == 'int':
        n = _as_number(v); return str(int(n)) if n is not None else str(v)
    s = str(v)
    # a text that a spreadsheet would read as a formula is written as text (CSV injection, ASVS V1.2.10)
    return "'" + s if s[:1] in ('=', '+', '-', '@', '\t', '\r') else s


def csv_bytes(sheet: Sheet) -> bytes:
    """UTF-8 with BOM, «;» and CRLF: Excel in Spanish opens it with the accents and the columns right."""
    buf = io.StringIO()
    w = csv.writer(buf, delimiter=';', quoting=csv.QUOTE_MINIMAL, lineterminator='\r\n')
    w.writerow([h for h, _ in sheet.columns])
    if not sheet.rows: w.writerow([EMPTY] + [''] * (len(sheet.columns) - 1))
    for r in sheet.rows:
        w.writerow([_csv_value(v, k) for v, (_, k) in zip(r, sheet.columns)])
    return ('﻿' + buf.getvalue()).encode('utf-8')


# ---------------------------------------------------------------------------------------------------- XLSX
_STYLE = {'text': 0, 'header': 1, 'date': 2, 'datetime': 3, 'money': 4, 'number': 5, 'int': 6, 'empty': 7, 'money_plain': 8}


def _col(i):
    s = ''
    i += 1
    while i: i, r = divmod(i - 1, 26); s = chr(65 + r) + s
    return s


def _cell(ref, v, kind, currency, bold=False):
    if v is None or v == '': return ''
    if bold:   # the totals row: the same formats, in bold
        if kind in ('money', 'number', 'int') and _as_number(v) is not None:
            n = _as_number(v); st = {'money': 9 if currency == 'EUR' else 10, 'number': 10, 'int': 11}[kind]
            return f'<c r="{ref}" s="{st}"><v>{int(n) if kind == "int" else round(n, 2)}</v></c>'
        return f'<c r="{ref}" s="12" t="inlineStr"><is><t xml:space="preserve">{_x(str(v))}</t></is></c>'
    if kind in ('date', 'datetime'):
        d = _as_date(v)
        if d is None: kind = 'text'
        else:
            serial = (d.replace(tzinfo=None) - _EPOCH).total_seconds() / 86400
            if kind == 'date': serial = int(serial)
            return f'<c r="{ref}" s="{_STYLE[kind]}"><v>{serial:.6f}</v></c>'.replace('.000000<', '<')
    if kind in ('money', 'number', 'int'):
        n = _as_number(v)
        if n is not None:
            style = _STYLE['money'] if kind == 'money' and currency == 'EUR' else _STYLE['money_plain'] if kind == 'money' else _STYLE[kind]
            return f'<c r="{ref}" s="{style}"><v>{int(n) if kind == "int" else round(n, 2)}</v></c>'
    s = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f]', '', str(v))[:32000]
    return f'<c r="{ref}" t="inlineStr"><is><t xml:space="preserve">{_x(s)}</t></is></c>'


def _width(sheet, i):
    head, kind = sheet.columns[i]
    base = {'date': 12, 'datetime': 17, 'money': 13, 'number': 12, 'int': 9}.get(kind)
    if base: return max(base, min(len(head) + 3, 40))
    longest = max([len(str(r[i] or '')) for r in sheet.rows[:300] if i < len(r)] + [len(head)])
    return max(10, min(longest + 2, 60))


def _sheet_xml(sheet: Sheet) -> str:
    n = len(sheet.columns)
    last = _col(n - 1)
    rows_xml = ['<row r="1">' + ''.join(f'<c r="{_col(i)}1" s="1" t="inlineStr"><is><t>{_x(h)}</t></is></c>' for i, (h, _) in enumerate(sheet.columns)) + '</row>']
    if not sheet.rows:
        rows_xml.append(f'<row r="2"><c r="A2" s="7" t="inlineStr"><is><t>{EMPTY}</t></is></c></row>')
    for ri, r in enumerate(sheet.rows, start=2):
        rows_xml.append(f'<row r="{ri}">' + ''.join(_cell(f'{_col(i)}{ri}', v, k, sheet.currency) for i, (v, (_, k)) in enumerate(zip(r, sheet.columns))) + '</row>')
    end = max(2, len(sheet.rows) + 1)
    if sheet.totals:
        tr = end + 1
        rows_xml.append(f'<row r="{tr}">' + ''.join(_cell(f'{_col(i)}{tr}', v, k, sheet.currency, bold=True) for i, (v, (_, k)) in enumerate(zip(sheet.totals, sheet.columns))) + '</row>')
    cols = ''.join(f'<col min="{i + 1}" max="{i + 1}" width="{_width(sheet, i)}" customWidth="1"/>' for i in range(n))
    return ('<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
            '<worksheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships">'
            f'<dimension ref="A1:{last}{end + (1 if sheet.totals else 0)}"/>'
            '<sheetViews><sheetView workbookViewId="0"><pane ySplit="1" topLeftCell="A2" activePane="bottomLeft" state="frozen"/>'
            '<selection pane="bottomLeft" activeCell="A2" sqref="A2"/></sheetView></sheetViews>'
            '<sheetFormatPr defaultRowHeight="15"/>'
            f'<cols>{cols}</cols><sheetData>{"".join(rows_xml)}</sheetData>'
            f'<autoFilter ref="A1:{last}{end}"/>'
            '<pageMargins left="0.7" right="0.7" top="0.75" bottom="0.75" header="0.3" footer="0.3"/></worksheet>')


_STYLES_XML = (
    '<?xml version="1.0" encoding="UTF-8" standalone="yes"?>'
    '<styleSheet xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main">'
    '<numFmts count="4"><numFmt numFmtId="164" formatCode="dd/mm/yyyy"/><numFmt numFmtId="165" formatCode="dd/mm/yyyy hh:mm"/>'
    '<numFmt numFmtId="166" formatCode="#,##0.00\\ &quot;€&quot;"/><numFmt numFmtId="167" formatCode="#,##0.00"/></numFmts>'
    '<fonts count="4"><font><sz val="11"/><name val="Calibri"/><family val="2"/></font>'
    '<font><b/><sz val="11"/><color rgb="FFFFFFFF"/><name val="Calibri"/><family val="2"/></font>'
    '<font><i/><sz val="11"/><color rgb="FF65747D"/><name val="Calibri"/><family val="2"/></font>'
    '<font><b/><sz val="11"/><name val="Calibri"/><family val="2"/></font></fonts>'
    '<fills count="3"><fill><patternFill patternType="none"/></fill><fill><patternFill patternType="gray125"/></fill>'
    '<fill><patternFill patternType="solid"><fgColor rgb="FF011C3C"/><bgColor indexed="64"/></patternFill></fill></fills>'
    '<borders count="2"><border><left/><right/><top/><bottom/><diagonal/></border><border><left/><right/><top style="thin"><color rgb="FF011C3C"/></top><bottom/><diagonal/></border></borders>'
    '<cellStyleXfs count="1"><xf numFmtId="0" fontId="0" fillId="0" borderId="0"/></cellStyleXfs>'
    '<cellXfs count="13">'
    '<xf numFmtId="0" fontId="0" fillId="0" borderId="0" xfId="0"/>'
    '<xf numFmtId="0" fontId="1" fillId="2" borderId="0" xfId="0" applyFont="1" applyFill="1"><alignment vertical="center"/></xf>'
    '<xf numFmtId="164" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    '<xf numFmtId="165" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    '<xf numFmtId="166" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    '<xf numFmtId="167" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    '<xf numFmtId="1" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    '<xf numFmtId="0" fontId="2" fillId="0" borderId="0" xfId="0" applyFont="1"/>'
    '<xf numFmtId="167" fontId="0" fillId="0" borderId="0" xfId="0" applyNumberFormat="1"/>'
    '<xf numFmtId="166" fontId="3" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1"/>'
    '<xf numFmtId="167" fontId="3" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1"/>'
    '<xf numFmtId="1" fontId="3" fillId="0" borderId="1" xfId="0" applyNumberFormat="1" applyFont="1" applyBorder="1"/>'
    '<xf numFmtId="0" fontId="3" fillId="0" borderId="1" xfId="0" applyFont="1" applyBorder="1"/>'
    '</cellXfs><cellStyles count="1"><cellStyle name="Normal" xfId="0" builtinId="0"/></cellStyles></styleSheet>')


def _safe_title(t, used):
    t = re.sub(r'[\[\]:*?/\\]', ' ', str(t or 'Hoja')).strip()[:31] or 'Hoja'
    base, n = t, 2
    while t.lower() in used: t = f'{base[:28]} {n}'; n += 1
    used.add(t.lower()); return t


def xlsx_bytes(sheets: list[Sheet], title: str = 'WORLDIVES DISCOVERY') -> bytes:
    used = set(); names = [_safe_title(s.title, used) for s in sheets]
    now = _dt.datetime.now(_dt.timezone.utc).strftime('%Y-%m-%dT%H:%M:%SZ')
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, 'w', zipfile.ZIP_DEFLATED) as z:
        z.writestr('[Content_Types].xml',
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Types xmlns="http://schemas.openxmlformats.org/package/2006/content-types">'
                   '<Default Extension="rels" ContentType="application/vnd.openxmlformats-package.relationships+xml"/><Default Extension="xml" ContentType="application/xml"/>'
                   '<Override PartName="/xl/workbook.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet.main+xml"/>'
                   + ''.join(f'<Override PartName="/xl/worksheets/sheet{i + 1}.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.worksheet+xml"/>' for i in range(len(sheets)))
                   + '<Override PartName="/xl/styles.xml" ContentType="application/vnd.openxmlformats-officedocument.spreadsheetml.styles+xml"/>'
                   '<Override PartName="/docProps/core.xml" ContentType="application/vnd.openxmlformats-package.core-properties+xml"/>'
                   '<Override PartName="/docProps/app.xml" ContentType="application/vnd.openxmlformats-officedocument.extended-properties+xml"/></Types>')
        z.writestr('_rels/.rels',
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   '<Relationship Id="rId1" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/officeDocument" Target="xl/workbook.xml"/>'
                   '<Relationship Id="rId2" Type="http://schemas.openxmlformats.org/package/2006/relationships/metadata/core-properties" Target="docProps/core.xml"/>'
                   '<Relationship Id="rId3" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/extended-properties" Target="docProps/app.xml"/></Relationships>')
        z.writestr('docProps/core.xml',
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><cp:coreProperties xmlns:cp="http://schemas.openxmlformats.org/package/2006/metadata/core-properties" '
                   'xmlns:dc="http://purl.org/dc/elements/1.1/" xmlns:dcterms="http://purl.org/dc/terms/" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance">'
                   f'<dc:title>{_x(title)}</dc:title><dc:creator>WORLDIVES DISCOVERY</dc:creator>'
                   f'<dcterms:created xsi:type="dcterms:W3CDTF">{now}</dcterms:created><dcterms:modified xsi:type="dcterms:W3CDTF">{now}</dcterms:modified></cp:coreProperties>')
        z.writestr('docProps/app.xml',
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Properties xmlns="http://schemas.openxmlformats.org/officeDocument/2006/extended-properties">'
                   '<Application>WORLDIVES DISCOVERY</Application></Properties>')
        z.writestr('xl/workbook.xml',
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><workbook xmlns="http://schemas.openxmlformats.org/spreadsheetml/2006/main" '
                   'xmlns:r="http://schemas.openxmlformats.org/officeDocument/2006/relationships"><bookViews><workbookView/></bookViews><sheets>'
                   + ''.join(f'<sheet name="{_x(nm)}" sheetId="{i + 1}" r:id="rId{i + 1}"/>' for i, nm in enumerate(names)) + '</sheets>'
                   + '<definedNames>' + ''.join(f'<definedName name="_xlnm._FilterDatabase" localSheetId="{i}" hidden="1">{_x(repr_sheet(nm))}!$A$1:${_col(len(s.columns) - 1)}${max(2, len(s.rows) + 1)}</definedName>'
                                              for i, (nm, s) in enumerate(zip(names, sheets))) + '</definedNames>'
                   + '</workbook>')
        z.writestr('xl/_rels/workbook.xml.rels',
                   '<?xml version="1.0" encoding="UTF-8" standalone="yes"?><Relationships xmlns="http://schemas.openxmlformats.org/package/2006/relationships">'
                   + ''.join(f'<Relationship Id="rId{i + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/worksheet" Target="worksheets/sheet{i + 1}.xml"/>' for i in range(len(sheets)))
                   + f'<Relationship Id="rId{len(sheets) + 1}" Type="http://schemas.openxmlformats.org/officeDocument/2006/relationships/styles" Target="styles.xml"/></Relationships>')
        z.writestr('xl/styles.xml', _STYLES_XML)
        for i, s in enumerate(sheets):
            z.writestr(f'xl/worksheets/sheet{i + 1}.xml', _sheet_xml(s))
    return buf.getvalue()


def repr_sheet(name):
    return "'" + name.replace("'", "''") + "'"


# ------------------------------------------------------------------------------------------------- periods
PERIODS = ('mes', 'mes_anterior', 'trimestre', 'trimestre_anterior', 'anio', 'anio_anterior', 'temporada', 'todo', 'personalizado')


def period(kind: str, today: _dt.date, season=('04-01', '10-31'), desde=None, hasta=None):
    """(from, to, label) of a period: this or last month, quarter or year, the season (configured in Administración) or
    two dates. «todo» has no limits."""
    kind = kind if kind in PERIODS else 'mes'
    y, m = today.year, today.month
    if kind == 'mes': a = today.replace(day=1); b = (a + _dt.timedelta(days=32)).replace(day=1) - _dt.timedelta(days=1); lab = a.strftime('%m/%Y')
    elif kind == 'mes_anterior':
        b = today.replace(day=1) - _dt.timedelta(days=1); a = b.replace(day=1); lab = a.strftime('%m/%Y')
    elif kind in ('trimestre', 'trimestre_anterior'):
        q = (m - 1) // 3
        if kind == 'trimestre_anterior': q -= 1
        if q < 0: q, y = 3, y - 1
        a = _dt.date(y, q * 3 + 1, 1); b = (_dt.date(y, q * 3 + 3, 1) + _dt.timedelta(days=32)).replace(day=1) - _dt.timedelta(days=1); lab = f'T{q + 1} {y}'
    elif kind in ('anio', 'anio_anterior'):
        y = y - 1 if kind == 'anio_anterior' else y; a, b = _dt.date(y, 1, 1), _dt.date(y, 12, 31); lab = str(y)
    elif kind == 'temporada':
        s, e = season
        a = _dt.date(y, int(s[:2]), int(s[3:5])); b = _dt.date(y, int(e[:2]), int(e[3:5]))
        if b < a:   # a season over new year (e.g. 1 November to 30 April)
            if today < a: a = _dt.date(y - 1, a.month, a.day)
            else: b = _dt.date(y + 1, b.month, b.day)
        lab = f'temporada {a.strftime("%d/%m/%Y")}–{b.strftime("%d/%m/%Y")}'
    elif kind == 'todo': return None, None, 'todo'
    else:
        try: a = _dt.date.fromisoformat(str(desde)[:10]); b = _dt.date.fromisoformat(str(hasta)[:10])
        except ValueError: raise ValueError('Elige las dos fechas del periodo.')
        if b < a: a, b = b, a
        if (b - a).days > 3660: raise ValueError('El periodo puede ser como mucho de 10 años.')
        lab = f'{a.strftime("%d/%m/%Y")}–{b.strftime("%d/%m/%Y")}'
    return a.isoformat(), b.isoformat(), lab


def filename(base: str, label: str, fmt: str) -> str:
    slug = re.sub(r'[^a-z0-9]+', '-', (base + '-' + label).lower().replace('/', '-').replace('–', '-')).strip('-')
    return f'worldives-{slug}.{"xlsx" if fmt == "xlsx" else "csv"}'
