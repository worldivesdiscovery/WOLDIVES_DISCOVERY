"""Encargo del 17/10/2026 (1.6) · «Exportar para mi gestoría»: un único Excel para el contable.

Hojas, siempre en el mismo orden y con los mismos nombres de columna: Resumen, Ventas, Cobros, Devoluciones, Por servicio
y Datos del informe. Este módulo no lee la base de datos: recibe las reservas del centro (con sus líneas, cobros y
devoluciones) y arma las hojas, así que los totales salen de una sola cuenta y cuadran entre hojas y con el panel.

Reglas que se cumplen aquí:
- La «fecha que manda» es la del cobro (por defecto) o la del servicio.
- Un cobro o una devolución sin fecha registrada (los de antes de que se guardara cada cobro) no se coloca en ningún mes
  con la fecha del cobro: se cuenta aparte en «Datos del informe». Con la fecha del servicio sí entra, con la del servicio.
- Los precios al público llevan el impuesto incluido. La base imponible y la cuota salen del tipo de cada servicio. Si
  un servicio no tiene tipo (ni el centro lo ha puesto ni se sabe el general de su país), la línea sale sin base ni
  cuota y el informe lo dice como «Pendiente de decisión». Nunca se inventa un tipo.
"""
from __future__ import annotations

import datetime as _dt
import re

from . import exportar as wexp

PENDING = 'Pendiente de decisión'

# General tax of the country of the centre, the default of a service until the centre confirms its own (brief 1.6:
# «por defecto el general del país del centro»). Only the ones that are known for certain; any other country: pending.
#   España peninsular y Baleares: IVA general 21 % (Ley 37/1992, art. 90.uno).
#   Canarias: IGIC general 7 % (Ley 4/2012 de Canarias, art. 27).
# Ceuta y Melilla (IPSI) and every other country are left for the centre and its gestoría.
CANARIAS_BOX = (27.4, 29.5, -18.4, -13.2)   # lat min, lat max, lon min, lon max


def country_default(country, region='', lat=None, lon=None):
    """(rate, name) of the general tax of the centre's place, or (None, None) when it is not known for certain."""
    c = (country or '').strip().lower()
    if c not in ('españa', 'espana', 'spain', 'es'): return None, None
    reg = (region or '').lower()
    try: canarias = lat is not None and lon is not None and CANARIAS_BOX[0] <= float(lat) <= CANARIAS_BOX[1] and CANARIAS_BOX[2] <= float(lon) <= CANARIAS_BOX[3]
    except (TypeError, ValueError): canarias = False
    if canarias or 'canari' in reg or 'las palmas' in reg or 'tenerife' in reg: return 7.0, 'IGIC'
    if 'ceuta' in reg or 'melilla' in reg: return None, None
    return 21.0, 'IVA'


def clean_rate(v):
    """A tax rate written by the centre: 0 to 30 %, two decimals at most (0 is valid: exempt)."""
    if v in (None, ''): return None
    try: r = round(float(str(v).replace(',', '.')), 2)
    except ValueError: raise ValueError('Escribe el tipo de impuesto como un número, por ejemplo 21.')
    if not 0 <= r <= 30: raise ValueError('El tipo de impuesto tiene que estar entre 0 y 30 %.')
    return r


TAX_NAMES = ('IVA', 'IGIC', 'IPSI', 'Otro')

METHOD_LABELS = {'online': 'Tarjeta online', 'link': 'Enlace de pago', 'cash': 'Efectivo', 'efectivo': 'Efectivo', 'card': 'Tarjeta en el centro',
                 'tarjeta': 'Tarjeta en el centro', 'datafono': 'Tarjeta en el centro', 'datáfono': 'Tarjeta en el centro', 'transfer': 'Transferencia',
                 'transferencia': 'Transferencia', 'bizum': 'Bizum'}


def method_label(m):
    m = (m or '').strip()
    return METHOD_LABELS.get(m.lower(), m[:1].upper() + m[1:] if m else 'Sin indicar')


# ------------------------------------------------------------------------------------------------------ periods
PERIOD_KINDS = ('temporada', 'anio', 'trimestre', 'mes', 'personalizado')


def periods(kind, today, season, value='', desde='', hasta='', seasons=()):
    """[(from, to)] and a label. temporada: one or several seasons (years); anio: a year; trimestre: «2026-T3»;
    mes: «2026-07»; personalizado: two dates."""
    def season_of(y):
        s, e = season
        a = _dt.date(y, int(s[:2]), int(s[3:5])); b = _dt.date(y, int(e[:2]), int(e[3:5]))
        if b < a: b = _dt.date(y + 1, b.month, b.day)   # a season over new year belongs to the year it starts
        return a, b
    if kind == 'temporada':
        years = sorted({int(y) for y in (seasons or [today.year]) if re.fullmatch(r'\d{4}', str(y))})
        if not years: raise ValueError('Elige al menos una temporada.')
        if len(years) > 10: raise ValueError('Elige como mucho 10 temporadas.')
        rs = [season_of(y) for y in years]
        return [(a.isoformat(), b.isoformat()) for a, b in rs], 'temporada ' + (str(years[0]) if len(years) == 1 else '-'.join(str(y) for y in years))
    if kind == 'anio':
        y = int(value) if re.fullmatch(r'\d{4}', str(value or '')) else today.year
        return [(f'{y}-01-01', f'{y}-12-31')], str(y)
    if kind == 'trimestre':
        m = re.fullmatch(r'(\d{4})-T([1-4])', str(value or ''))
        y, q = (int(m.group(1)), int(m.group(2))) if m else (today.year, (today.month - 1) // 3 + 1)
        a = _dt.date(y, q * 3 - 2, 1); b = (_dt.date(y, q * 3, 1) + _dt.timedelta(days=32)).replace(day=1) - _dt.timedelta(days=1)
        return [(a.isoformat(), b.isoformat())], f'{y}-T{q}'
    if kind == 'mes':
        m = re.fullmatch(r'(\d{4})-(\d{2})', str(value or ''))
        y, mo = (int(m.group(1)), int(m.group(2))) if m and 1 <= int(m.group(2)) <= 12 else (today.year, today.month)
        a = _dt.date(y, mo, 1); b = (a + _dt.timedelta(days=32)).replace(day=1) - _dt.timedelta(days=1)
        return [(a.isoformat(), b.isoformat())], f'{y}-{mo:02d}'
    a, b, lab = wexp.period('personalizado', today, season, desde, hasta)
    return [(a, b)], lab.replace('/', '-').replace('–', '_')


def in_periods(d, ranges):
    d = (d or '')[:10]
    return bool(d) and any(a <= d <= b for a, b in ranges)


# -------------------------------------------------------------------------------------------------------- sheets
SALES_COLUMNS = [   # (key, header, type): the order of the brief; «Mi plantilla de gestoría» chooses and orders them
    ('fecha_servicio', 'Fecha del servicio', 'date'), ('fecha_cobro', 'Fecha del cobro', 'date'), ('reserva', 'Número de reserva', 'text'),
    ('cliente', 'Cliente', 'text'), ('nif', 'NIF del cliente', 'text'), ('servicio', 'Servicio', 'text'), ('categoria', 'Categoría', 'text'),
    ('unidades', 'Unidades', 'number'), ('precio', 'Precio unitario', 'money'), ('base', 'Base imponible', 'money'), ('impuesto', 'Impuesto', 'text'),
    ('tipo', 'Tipo de impuesto (%)', 'number'), ('cuota', 'Cuota', 'money'), ('total', 'Total', 'money'), ('metodo', 'Método de pago', 'text'),
    ('canal', 'Canal', 'text'), ('estado', 'Estado', 'text'), ('moneda', 'Moneda', 'text')]
SALES_KEYS = [k for k, _, _ in SALES_COLUMNS]
REQUIRED_KEYS = ('reserva', 'total')   # a template can leave out any column but these two


def clean_template(cols):
    keys = [k for k in (cols or []) if k in SALES_KEYS]
    keys = list(dict.fromkeys(keys))
    for k in REQUIRED_KEYS:
        if k not in keys: raise ValueError('La plantilla tiene que llevar el número de reserva y el total.')
    return keys


def _split(total, rate):
    """(base, cuota) of a price with the tax included; (None, None) without a rate."""
    if rate is None: return None, None
    base = round(total / (1 + rate / 100.0), 2)
    return base, round(total - base, 2)


def _month(d):
    return (d or '')[:7] or 'Sin fecha'


def build(bookings, *, mode, ranges, provider, plabel, generated, template=None):
    """The 6 sheets and a summary for the screen. Each booking:
    {id, ref, service_date, client, service, category, channel, status, currency, lines:[{label, qty, unit, total, rate,
     tax_name, confirmed}], payments:[{date|None, amount, method, kind: online|centre, ref}], refunds:[{date|None,
     amount, reason, ref}]}."""
    by_cobro = mode != 'servicio'
    sales, pays, refs = [], [], []
    undated_p = undated_r = 0.0; n_undated = 0; no_rate = 0; unconfirmed = set()
    month_rows = {}

    def mrow(month, cur):
        return month_rows.setdefault((month, cur), {'reservas': set(), 'buceadores': 0, 'base': 0.0, 'cuota': 0.0, 'total': 0.0,
                                                    'online': 0.0, 'centro': 0.0, 'dev': 0.0})
    for b in bookings:
        cur = b['currency']
        dated = sorted(p['date'][:10] for p in b['payments'] if p.get('date'))
        if by_cobro:
            in_p = [p for p in b['payments'] if p.get('date') and in_periods(p['date'], ranges)]
            in_r = [r for r in b['refunds'] if r.get('date') and in_periods(r['date'], ranges)]
            # the sale belongs to the period of its first payment (a booking paid in two periods is counted once)
            first = dated[0] if dated else None
            sale_in = first is not None and in_periods(first, ranges); sale_month = _month(first)
            for x in b['payments']:
                if not x.get('date'): undated_p += x['amount']; n_undated += 1
            for x in b['refunds']:
                if not x.get('date'): undated_r += x['amount']; n_undated += 1
        else:
            inside = in_periods(b['service_date'], ranges)
            in_p = b['payments'] if inside else []
            in_r = b['refunds'] if inside else []
            sale_in = inside; sale_month = _month(b['service_date'])
        methods = ', '.join(dict.fromkeys(method_label(p['method']) for p in b['payments'])) or 'Sin cobrar'
        if sale_in:
            row = mrow(sale_month, cur); row['reservas'].add(b['id']); row['buceadores'] += int(b.get('participants') or 0)
            for ln in b['lines']:
                base, cuota = _split(ln['total'], ln['rate'])
                if ln['rate'] is None: no_rate += 1
                elif not ln.get('confirmed'): unconfirmed.add(b['service'])
                row['total'] += ln['total']; row['base'] += base or 0; row['cuota'] += cuota or 0
                sales.append({'fecha_servicio': b['service_date'], 'fecha_cobro': dated[0] if dated else None, 'reserva': b['ref'], 'cliente': b['client'],
                              'nif': b.get('nif') or '', 'servicio': ln['label'], 'categoria': b['category'], 'unidades': ln['qty'], 'precio': ln['unit'],
                              'base': base, 'impuesto': ln.get('tax_name') or (PENDING if ln['rate'] is None else ''), 'tipo': ln['rate'], 'cuota': cuota,
                              'total': ln['total'], 'metodo': methods, 'canal': b['channel'], 'estado': b['status'], 'moneda': cur, '_svc': b['service']})
        for p in in_p:
            m = _month(p.get('date')) if by_cobro else sale_month
            mrow(m, cur)['online' if p['kind'] == 'online' else 'centro'] += p['amount']
            pays.append([p.get('date'), b['ref'], p['amount'], method_label(p['method']), p.get('ref') or '', cur])
        for r in in_r:
            m = _month(r.get('date')) if by_cobro else sale_month
            mrow(m, cur)['dev'] += r['amount']
            refs.append([r.get('date'), b['ref'], r['amount'], r.get('reason') or '', r.get('ref') or '', cur])

    currencies = sorted({k[1] for k in month_rows} | {s['moneda'] for s in sales}) or ['EUR']
    multi = len(currencies) > 1
    money_cur = currencies[0] if not multi else 'XXX'
    S = wexp.Sheet
    # ---- Resumen: one row per month (and currency, if there are several) and the totals
    rcols = [('Mes', 'text')] + ([('Moneda', 'text')] if multi else []) + [('Reservas', 'int'), ('Buceadores', 'int'), ('Base imponible', 'money'),
             ('Impuesto', 'money'), ('Total', 'money'), ('Cobrado online', 'money'), ('Cobrado en el centro', 'money'), ('Devoluciones', 'money'), ('Neto cobrado', 'money')]
    rrows = []; tot = {'reservas': 0, 'buceadores': 0, 'base': 0.0, 'cuota': 0.0, 'total': 0.0, 'online': 0.0, 'centro': 0.0, 'dev': 0.0}
    for (month, cur) in sorted(month_rows):
        r = month_rows[(month, cur)]
        label = _dt.date(int(month[:4]), int(month[5:7]), 1).strftime('%m/%Y') if re.fullmatch(r'\d{4}-\d{2}', month) else month
        vals = [len(r['reservas']), r['buceadores'], round(r['base'], 2), round(r['cuota'], 2), round(r['total'], 2), round(r['online'], 2), round(r['centro'], 2),
                round(r['dev'], 2), round(r['online'] + r['centro'] - r['dev'], 2)]
        rrows.append([label] + ([cur] if multi else []) + vals)
        for k in ('base', 'cuota', 'total', 'online', 'centro', 'dev'): tot[k] += r[k]
        tot['reservas'] += len(r['reservas']); tot['buceadores'] += r['buceadores']
    totals = {k: round(v, 2) if isinstance(v, float) else v for k, v in tot.items()}
    totals['neto'] = round(tot['online'] + tot['centro'] - tot['dev'], 2)
    resumen = S('Resumen', rcols, rrows, money_cur)
    resumen.totals = ['Total'] + ([''] if multi else []) + [totals['reservas'], totals['buceadores'], totals['base'], totals['cuota'], totals['total'],
                                                            totals['online'], totals['centro'], totals['dev'], totals['neto']]
    # ---- Ventas (the columns of «Mi plantilla de gestoría», if there is one)
    keys = template or SALES_KEYS
    cols = [(h, t) for k in keys for kk, h, t in SALES_COLUMNS if kk == k]
    ventas = S('Ventas', cols, [[s[k] for k in keys] for s in sales], money_cur)
    ventas.totals = ['Total' if i == 0 else round(sum((s[k] or 0) for s in sales), 2) if k in ('base', 'cuota', 'total', 'unidades') else ''
                     for i, k in enumerate(keys)]
    # ---- Cobros and Devoluciones
    cobros = S('Cobros', [('Fecha', 'date'), ('Número de reserva', 'text'), ('Importe', 'money'), ('Método', 'text'), ('Referencia del pago', 'text'), ('Moneda', 'text')],
               sorted(pays, key=lambda x: (x[0] or '9999', x[1])), money_cur)
    cobros.totals = ['Total', '', round(sum(x[2] for x in pays), 2), '', '', '']
    devol = S('Devoluciones', [('Fecha', 'date'), ('Número de reserva', 'text'), ('Importe', 'money'), ('Motivo', 'text'), ('Referencia', 'text'), ('Moneda', 'text')],
              sorted(refs, key=lambda x: (x[0] or '9999', x[1])), money_cur)
    devol.totals = ['Total', '', round(sum(x[2] for x in refs), 2), '', '', '']
    # ---- Por servicio: a row per service, then a row per category, then the total
    per = {}
    for s in sales:
        k = (s['categoria'], s['_svc'], s['moneda'])
        g = per.setdefault(k, {'reservas': set(), 'unidades': 0.0, 'base': 0.0, 'cuota': 0.0, 'total': 0.0})
        g['reservas'].add(s['reserva']); g['unidades'] += s['unidades'] or 0; g['base'] += s['base'] or 0; g['cuota'] += s['cuota'] or 0; g['total'] += s['total']
    prows = []
    for (cat, svc, cur), g in sorted(per.items()):
        prows.append([cat, svc, len(g['reservas']), round(g['unidades'], 2), round(g['base'], 2), round(g['cuota'], 2), round(g['total'], 2), cur])
    cats = {}
    for r in prows:
        c = cats.setdefault((r[0], r[7]), [0, 0.0, 0.0, 0.0, 0.0])
        c[0] += r[2]; c[1] += r[3]; c[2] += r[4]; c[3] += r[5]; c[4] += r[6]
    for (cat, cur), c in sorted(cats.items()):
        prows.append([cat, f'Total {cat}', c[0], round(c[1], 2), round(c[2], 2), round(c[3], 2), round(c[4], 2), cur])
    por = S('Por servicio', [('Categoría', 'text'), ('Servicio', 'text'), ('Reservas', 'int'), ('Unidades', 'number'), ('Base imponible', 'money'),
                             ('Impuesto', 'money'), ('Total', 'money'), ('Moneda', 'text')], prows, money_cur)
    por.totals = ['Total', '', sum(r[2] for r in prows[:len(per)]), round(sum(r[3] for r in prows[:len(per)]), 2), totals['base'], totals['cuota'], totals['total'], '']
    # ---- Datos del informe
    pend = []
    if no_rate: pend.append(f'Tipo de impuesto: {no_rate} líneas sin tipo (el país del centro no tiene un tipo general conocido o el servicio no lo tiene). Confírmalo con tu gestoría en «Impuestos de tus servicios».')
    if unconfirmed: pend.append(f'Tipo de impuesto sin confirmar por el centro (se ha usado el general del país) en: {", ".join(sorted(unconfirmed))}.')
    if n_undated and by_cobro:
        pend.append(f'Cobros y devoluciones sin fecha registrada (anteriores a que se guardara cada cobro): {n_undated}, '
                    f'{wexp_money(undated_p)} cobrados y {wexp_money(undated_r)} devueltos. No entran por fecha del cobro; sí con la fecha del servicio.')
    pend.append('NIF del cliente: la reserva todavía no pide datos de factura, así que la columna sale vacía.')
    pend.append('Facturas: WORLDIVES no emite facturas (el justificante de la reserva dice «Este documento no es una factura»). Si un día las emite, '
                'tendrá que cumplir la normativa de sistemas de facturación (Verifactu en España): decisión del titular y su gestoría.')
    info = [['Centro', provider.get('name') or ''], ['Razón social', provider.get('legal_name') or PENDING], ['NIF', provider.get('tax_id') or PENDING],
            ['Periodo', plabel + ' (' + '; '.join(f'{_dmy(a)} a {_dmy(b)}' for a, b in ranges) + ')'],
            ['Fecha que manda', 'Fecha del cobro (cuándo entró el dinero)' if by_cobro else 'Fecha del servicio (cuándo se buceó)'],
            ['Generado', generated], ['Moneda', ', '.join(currencies)],
            ['Precios', 'Los precios al público llevan el impuesto incluido: la base imponible y la cuota salen del tipo de cada servicio.'],
            ['Neto cobrado', 'Cobrado online + cobrado en el centro − devoluciones.']] + [[PENDING, p] for p in pend]
    datos = S('Datos del informe', [('Dato', 'text'), ('Valor', 'text')], info)
    summary = {'totals': totals, 'rows': {'ventas': len(sales), 'cobros': len(pays), 'devoluciones': len(refs)}, 'currencies': currencies,
               'pending': pend, 'undated': {'count': n_undated, 'paid': round(undated_p, 2), 'refunded': round(undated_r, 2)}}
    return [resumen, ventas, cobros, devol, por, datos], summary


def wexp_money(v):
    return ('%.2f €' % v).replace('.', ',')


def _dmy(iso):
    return f'{iso[8:10]}/{iso[5:7]}/{iso[:4]}' if iso and len(iso) >= 10 else ''


def file_name(center, plabel, ext='xlsx'):
    clean = lambda s: re.sub(r'[^A-Za-z0-9]+', '-', __import__('unicodedata').normalize('NFKD', s or '').encode('ascii', 'ignore').decode()).strip('-') or 'centro'
    return f'WORLDIVES_Ventas_{clean(center)}_{clean(plabel)}.{ext}'
