"""Informe de una medición de carga (tests/carga/medir.py) en Markdown con gráficos SVG propios, sin dependencias.

    python3 tests/carga/informe.py RESULTADOS SALIDA_DIR [--titulo "…"]

RESULTADOS es la carpeta con resumen.json (y paso_N/). Escribe en SALIDA_DIR: carga.md, latencia.svg, rps.svg y cpu.svg.
"""
from __future__ import annotations

import argparse
import json
from pathlib import Path

W, H, PAD_L, PAD_B, PAD_T, PAD_R = 640, 300, 64, 44, 30, 20
COLORS = ('#0c4a6e', '#e9775f', '#2f9a6a', '#8a6129')


def _nice(v):
    for m in (1, 2, 2.5, 5, 10):
        for e in range(-1, 7):
            step = m * 10 ** e
            if step * 5 >= v: return step
    return v / 5


def line_chart(title, xs, series, unit, limit=None, limit_label=''):
    """series: [(label, [y…])]. A dashed horizontal line marks the target (limit)."""
    ys = [y for _, s in series for y in s if y is not None] + ([limit] if limit else [])
    top = max(ys or [1]) * 1.1; step = _nice(top / 5); top = step * (int(top / step) + 1)
    pw, ph = W - PAD_L - PAD_R, H - PAD_T - PAD_B
    X = lambda i: PAD_L + (pw * i / max(1, len(xs) - 1))
    Y = lambda v: PAD_T + ph - ph * (v / top)
    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" width="{W}" height="{H}" font-family="Inter,Arial,sans-serif" font-size="12">',
           f'<rect width="{W}" height="{H}" fill="#fff"/><text x="{PAD_L}" y="18" font-size="14" font-weight="700" fill="#0b2f40">{title}</text>']
    v = 0
    while v <= top + 1e-9:
        out.append(f'<line x1="{PAD_L}" x2="{W - PAD_R}" y1="{Y(v):.1f}" y2="{Y(v):.1f}" stroke="#e3e7e6"/>'
                   f'<text x="{PAD_L - 8}" y="{Y(v) + 4:.1f}" text-anchor="end" fill="#5d6f77">{v:g}</text>')
        v += step
    for i, x in enumerate(xs):
        out.append(f'<text x="{X(i):.1f}" y="{H - PAD_B + 18}" text-anchor="middle" fill="#5d6f77">{x:,}</text>'.replace(',', '.'))
    out.append(f'<text x="{PAD_L + pw / 2:.0f}" y="{H - 6}" text-anchor="middle" fill="#35505d">usuarios simultáneos</text>'
               f'<text x="14" y="{PAD_T + ph / 2:.0f}" transform="rotate(-90 14 {PAD_T + ph / 2:.0f})" text-anchor="middle" fill="#35505d">{unit}</text>')
    if limit:
        out.append(f'<line x1="{PAD_L}" x2="{W - PAD_R}" y1="{Y(limit):.1f}" y2="{Y(limit):.1f}" stroke="#b23b26" stroke-dasharray="6 4"/>'
                   f'<text x="{W - PAD_R}" y="{Y(limit) - 6:.1f}" text-anchor="end" fill="#b23b26">{limit_label}</text>')
    for k, (label, s) in enumerate(series):
        c = COLORS[k % len(COLORS)]
        pts = [(X(i), Y(y)) for i, y in enumerate(s) if y is not None]
        out.append(f'<polyline fill="none" stroke="{c}" stroke-width="2.5" points="{" ".join(f"{a:.1f},{b:.1f}" for a, b in pts)}"/>')
        out += [f'<circle cx="{a:.1f}" cy="{b:.1f}" r="3.5" fill="{c}"/>' for a, b in pts]
        out.append(f'<rect x="{PAD_L + 10 + k * 170}" y="{PAD_T + 2}" width="12" height="4" fill="{c}"/>'
                   f'<text x="{PAD_L + 28 + k * 170}" y="{PAD_T + 8}" fill="#35505d">{label}</text>')
    out.append('</svg>')
    return '\n'.join(out)


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('resultados'); ap.add_argument('salida'); ap.add_argument('--titulo', default='Prueba de carga')
    a = ap.parse_args()
    res, out = Path(a.resultados), Path(a.salida); out.mkdir(parents=True, exist_ok=True)
    d = json.loads((res / 'resumen.json').read_text(encoding='utf-8'))
    pasos = d['pasos']; xs = [p['usuarios'] for p in pasos]
    g = lambda p, grupo, k: (p['grupos'].get(grupo) or {}).get(k)
    srv = lambda p, k: ((p.get('servidor') or {}).get(k) or {}).get('media')
    (out / 'latencia.svg').write_text(line_chart('Tiempo de respuesta p95 (régimen estable)', xs,
                                                 [('Páginas (p95)', [g(p, 'pag', 'p95_ms') for p in pasos]), ('Reservas y panel (p95)', [g(p, 'res', 'p95_ms') for p in pasos])],
                                                 'ms', limit=1000, limit_label='objetivo páginas: 1 s'), encoding='utf-8')
    (out / 'rps.svg').write_text(line_chart('Peticiones por segundo atendidas', xs,
                                            [('Páginas', [g(p, 'pag', 'rps') for p in pasos]), ('Reservas y panel', [g(p, 'res', 'rps') for p in pasos])], 'r/s'), encoding='utf-8')
    (out / 'cpu.svg').write_text(line_chart('CPU del servidor y del sistema', xs,
                                            [('Servidor (% de 1 núcleo)', [srv(p, 'srv_cpu_pct') for p in pasos]), ('Sistema (% total)', [srv(p, 'sis_cpu_pct') for p in pasos])], '%'), encoding='utf-8')
    rows = []
    for p in pasos:
        s = p.get('servidor') or {}; lg = p.get('log_servidor') or {}
        rows.append(f"| {p['usuarios']:,} | {g(p, 'pag', 'rps') or 0:.0f} | {g(p, 'pag', 'media_ms') or 0:.0f} / {g(p, 'pag', 'p95_ms') or 0:.0f} | "
                    f"{g(p, 'res', 'media_ms') or 0:.0f} / {g(p, 'res', 'p95_ms') or 0:.0f} | {g(p, 'ses', 'p95_ms') or 0:.0f} | "
                    f"{max(g(p, k, 'error_pct') or 0 for k in ('pag', 'res', 'ses')):.2f} % | {srv(p, 'srv_cpu_pct') or 0:.0f} % | "
                    f"{(s.get('srv_rss_mb') or {}).get('max') or 0:.0f} MB | {lg.get('bloqueos_sqlite', 0)} / {lg.get('errores_500', 0)} | "
                    f"{'; '.join(p.get('rotura') or []) or 'correcto'} |".replace(',', '.'))
    rot = d.get('rotura')
    md = [f'# {a.titulo}', '', f"Servidor: {d['servidor'].get('workers', '?')} procesos (`WOD_WORKERS`). Rotura: "
          + (f"**{rot['usuarios']:,} usuarios** ({'; '.join(rot['motivo'])}); último escalón correcto: {rot['ultimo_correcto']}".replace(',', '.') if rot else 'no alcanzada') + '.', '',
          '| Usuarios | r/s páginas | Páginas media / p95 (ms) | Reservas media / p95 (ms) | Inicio de sesión p95 (ms) | Errores | CPU servidor | Memoria | Bloqueos / 500 | Resultado |',
          '|---|---|---|---|---|---|---|---|---|---|', *rows, '', '![Latencia](latencia.svg)', '', '![Peticiones por segundo](rps.svg)', '', '![CPU](cpu.svg)', '']
    (out / 'carga.md').write_text('\n'.join(md), encoding='utf-8')
    print(out / 'carga.md')


if __name__ == '__main__':
    main()
