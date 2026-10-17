"""v50.58 · ¿Mar o tierra? ¿A cuántos metros de la orilla? (encargo del 16/10/2026, parte B.6).

Cada punto de buceo nuevo se comprueba antes de publicarlo: tiene que caer en el mar, y un punto de costa a menos de
200 m de la orilla. Los datos son la tierra de OpenStreetMap (línea de costa simplificada con un error de 10 m, licencia
ODbL; la página de créditos lo dice), recortada por zonas en app/data/costa/<zona>.json con
scripts/puntos/preparar_costa.py. Fuera de esas zonas no se puede comprobar y se dice así (None), nunca se adivina.

Python puro: una rejilla con los tramos de costa contesta en menos de un milisegundo por punto.
"""
from __future__ import annotations

import json
import math
import threading
from pathlib import Path

DATA = Path(__file__).resolve().parents[1] / 'data' / 'costa'
CELL = 0.02                 # lado de la celda de la rejilla, en grados (≈ 2 km)
SEARCH = 0.25               # hasta dónde se busca la orilla (≈ 25 km): más lejos es «mar abierto»
SHORE_M = 200               # un punto de costa, a menos de 200 m de la orilla
M_PER_DEG = 111320.0
_lock = threading.Lock()
_zones = None


class _Zone:
    """Una zona: su caja enseguida; la rejilla de la costa, solo la primera vez que se pregunta por un punto suyo."""
    def __init__(self, path):
        self.path = path
        head = json.loads(path.read_text(encoding='utf-8'))
        self.zone, self.name, self.bbox = head['zone'], head['name'], head['bbox']
        self.rows = self.cells = None
        self._lock = threading.Lock()

    def index(self):
        if self.rows is not None: return
        with self._lock:
            if self.rows is not None: return
            data = json.loads(self.path.read_text(encoding='utf-8'))
            k = 1.0 / data['scale']
            w, s, e, n = self.bbox
            on_border = lambda a, b: ((a[0] == b[0] and (abs(a[0] - w) < 1e-9 or abs(a[0] - e) < 1e-9))
                                      or (a[1] == b[1] and (abs(a[1] - s) < 1e-9 or abs(a[1] - n) < 1e-9)))
            rows, cells = {}, {}   # fila → tramos que la cruzan (dentro/fuera); celda → tramos de orilla (distancia)
            for ring in data['rings']:
                pts, x, y = [], 0, 0
                for i in range(0, len(ring), 2):
                    x += ring[i]; y += ring[i + 1]; pts.append((x * k, y * k))
                for i, a in enumerate(pts):
                    b = pts[(i + 1) % len(pts)]
                    if a[1] == b[1] and a[0] == b[0]: continue
                    seg = (a[0], a[1], b[0], b[1])
                    for r in range(math.floor(min(a[1], b[1]) / CELL), math.floor(max(a[1], b[1]) / CELL) + 1):
                        rows.setdefault(r, []).append(seg)
                    if on_border(a, b): continue          # el borde de la caja no es orilla
                    for cx in range(math.floor(min(a[0], b[0]) / CELL), math.floor(max(a[0], b[0]) / CELL) + 1):
                        for cy in range(math.floor(min(a[1], b[1]) / CELL), math.floor(max(a[1], b[1]) / CELL) + 1):
                            cells.setdefault((cx, cy), []).append(seg)
            self.cells = cells; self.rows = rows

    def covers(self, lat, lon):
        w, s, e, n = self.bbox
        return w <= lon <= e and s <= lat <= n

    def land(self, lat, lon):
        """Par o impar: cuántas veces corta la orilla una línea desde el punto hacia el este."""
        inside = False
        for x1, y1, x2, y2 in self.rows.get(math.floor(lat / CELL), ()):
            if (y1 > lat) != (y2 > lat):
                xc = x1 + (lat - y1) * (x2 - x1) / (y2 - y1)
                if xc > lon: inside = not inside
        return inside

    def shore_m(self, lat, lon):
        """Metros hasta el tramo de orilla más cercano (None si no hay ninguno a menos de SEARCH grados)."""
        kx = math.cos(math.radians(lat))
        cx, cy = math.floor(lon / CELL), math.floor(lat / CELL)
        best, ring = None, 0
        while ring * CELL <= SEARCH:
            for i in range(cx - ring, cx + ring + 1):
                for j in range(cy - ring, cy + ring + 1):
                    if max(abs(i - cx), abs(j - cy)) != ring: continue
                    for x1, y1, x2, y2 in self.cells.get((i, j), ()):
                        ax, ay = (x1 - lon) * kx, y1 - lat
                        bx, by = (x2 - lon) * kx, y2 - lat
                        dx, dy = bx - ax, by - ay
                        L = dx * dx + dy * dy
                        t = 0.0 if L == 0 else max(0.0, min(1.0, -(ax * dx + ay * dy) / L))
                        d = math.hypot(ax + t * dx, ay + t * dy)
                        if best is None or d < best: best = d
            # lo encontrado a «ring» celdas puede no ser lo más cercano: una vuelta más lo asegura
            if best is not None and best <= ring * CELL: break
            ring += 1
        return None if best is None else best * M_PER_DEG


def _load():
    global _zones
    if _zones is None:
        with _lock:
            if _zones is None:
                zones = []
                for f in sorted(DATA.glob('*.json')):
                    try: zones.append(_Zone(f))
                    except (OSError, ValueError, KeyError): continue
                _zones = zones
    return _zones


def check(lat, lon):
    """{'zone', 'land', 'shore_m'} para un punto dentro de una zona con datos; None fuera de ellas (sin comprobar).
    shore_m es None cuando la orilla queda a más de ~25 km (mar abierto)."""
    try: lat, lon = float(lat), float(lon)
    except (TypeError, ValueError): return None
    if not (math.isfinite(lat) and math.isfinite(lon)): return None
    for z in _load():
        if z.covers(lat, lon):
            z.index()
            d = z.shore_m(lat, lon)
            return {'zone': z.zone, 'land': z.land(lat, lon), 'shore_m': None if d is None else round(d)}
    return None


# tipos de inmersión en agua dulce o tierra adentro: no se les pide estar en el mar
INLAND = ('cenote', 'lago', 'lake', 'cantera', 'quarry', 'río', 'rio', 'river', 'embalse', 'pantano', 'reservoir', 'mina', 'mine')


def verdict(lat, lon, access=None, dive_type=''):
    """Lo que se le dice al administrador de un punto: (estado, texto). estado: 'ok', 'warn', 'error' o 'unknown'."""
    if any(w in (dive_type or '').lower() for w in INLAND):
        return 'ok', 'Agua interior: no se comprueba la costa'
    c = check(lat, lon)
    if c is None:
        return 'unknown', 'Sin datos de costa para esta zona: comprobar a mano'
    d = c['shore_m']
    if c['land']:
        if d is not None and d <= 25:
            return 'warn', f'Sobre la línea de costa (a {d} m): comprobar que el punto está en el agua'
        return 'error', 'En tierra' + (f' (a {d} m de la orilla)' if d is not None else '')
    if access == 'shore' and (d is None or d > SHORE_M):
        return 'warn', 'Punto de costa a más de 200 m de la orilla' + (f' ({d} m)' if d is not None else '')
    if d is None:
        return 'ok', 'En el mar, lejos de la costa'
    return 'ok', f'En el mar, a {d} m de la orilla' if d < 1000 else f'En el mar, a {d / 1000:.1f} km de la orilla'
