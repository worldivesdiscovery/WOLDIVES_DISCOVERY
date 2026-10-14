"""Distances and «what is near» for dive sites (v50.53).

The browser never receives every dive site to sort them itself: the server looks for the closest ones inside a box of
coordinates (an index on dive_points(latitude, longitude) answers it) and widens the box only while it has not found
enough. Areas («Costa Brava», «Canarias»…) are rows of the dive_areas table, not code: adding another country or area
needs no change here.

The visitor's position is used to sort and nothing else: it is never stored, never linked to the account and arrives
already rounded to about one kilometre (round_coord).
"""
from __future__ import annotations

import math

EARTH_KM = 6371.0088
HALF_EARTH_KM = 20038.0          # the farthest two points on Earth can be
KM_PER_DEGREE_LAT = 111.32


def haversine_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1); dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return EARTH_KM * 2 * math.atan2(math.sqrt(a), math.sqrt(max(0.0, 1 - a)))


def coord(value, kind: str) -> float | None:
    """A latitude (kind='lat') or longitude ('lon') sent by a browser, or None when it is missing or out of range."""
    try: v = float(value)
    except (TypeError, ValueError): return None
    if not math.isfinite(v): return None
    limit = 90.0 if kind == 'lat' else 180.0
    return v if -limit <= v <= limit else None


def round_coord(value: float, places: int = 2) -> float:
    """About 1 km at 2 decimals: enough to sort by distance, not enough to say where someone is."""
    return round(float(value), places)


def box(lat: float, lon: float, km: float) -> tuple[float, float, list[tuple[float, float]]]:
    """The latitude range and the longitude ranges (two when it crosses the 180° meridian) that contain every point at
    most `km` away. Near the poles (or for a box as big as the world) every longitude is included."""
    dlat = km / KM_PER_DEGREE_LAT
    lat0, lat1 = max(-90.0, lat - dlat), min(90.0, lat + dlat)
    cos = math.cos(math.radians(max(abs(lat0), abs(lat1))))
    if lat0 <= -89.9 or lat1 >= 89.9 or cos < 1e-6:
        return lat0, lat1, [(-180.0, 180.0)]
    dlon = km / (KM_PER_DEGREE_LAT * cos)
    if dlon >= 180: return lat0, lat1, [(-180.0, 180.0)]
    lo, hi = lon - dlon, lon + dlon
    if lo < -180: return lat0, lat1, [(lo + 360, 180.0), (-180.0, hi)]
    if hi > 180: return lat0, lat1, [(lo, 180.0), (-180.0, hi - 360)]
    return lat0, lat1, [(lo, hi)]


def nearest(fetch, lat: float, lon: float, need: int, accept=None, start_km: float = 60.0) -> list[tuple[float, int]]:
    """The `need` closest points, as [(km, id)] from closer to farther.

    fetch(lat0, lat1, lon_ranges) returns (id, latitude, longitude) of the active points inside the box (an indexed
    query). The box doubles until `need` accepted points lie inside the circle of radius km, so no closer point can be
    outside it; or until it covers the whole world, and then every accepted point is sorted."""
    accept = accept or (lambda _id: True)
    km = max(1.0, start_km)
    while True:
        world = km >= HALF_EARTH_KM
        lat0, lat1, ranges = box(lat, lon, HALF_EARTH_KM if world else km)
        found = []
        for pid, plat, plon in fetch(lat0, lat1, ranges):
            if plat is None or plon is None or not accept(pid): continue
            found.append((haversine_km(lat, lon, float(plat), float(plon)), pid))
        found.sort()
        inside = sum(1 for d, _ in found if d <= km)
        if world or inside >= need:
            return found[:need] if need else found
        km *= 2


def sql_box(lat0: float, lat1: float, ranges, prefix: str = '') -> tuple[str, list]:
    """WHERE fragment for a box of coordinates (uses the index on latitude, longitude)."""
    lon_sql = ' OR '.join(f'{prefix}longitude BETWEEN ? AND ?' for _ in ranges)
    args = [lat0, lat1] + [v for r in ranges for v in r]
    return f'{prefix}latitude BETWEEN ? AND ? AND ({lon_sql})', args


def area_of(lat, lon, country: str | None, areas) -> dict | None:
    """The first area (in sort order) whose box contains the point. Areas belong to a country: a point of another
    country never falls into them even if its coordinates are close to the border."""
    if lat is None or lon is None: return None
    for a in areas:
        if a['country'] and country and a['country'] != country: continue
        if a['lat_min'] <= lat <= a['lat_max'] and a['lon_min'] <= lon <= a['lon_max']:
            return a
    return None


# Dive areas of the launch country (v50.53). Order = how they are listed when the visitor has not shared the location.
# Boxes only share edges (the Valencia–Catalonia line is the mouth of the Sénia, 40.52); a Spanish point outside all of
# them is listed under «Otras zonas de España».
SPAIN_AREAS = [
    ('Costa Brava', 41.66, 42.50, 2.75, 3.40),
    ('Comunidad Valenciana', 37.845, 40.52, -1.20, 0.75),
    ('Murcia', 37.35, 37.845, -1.64, -0.60),
    ('Andalucía', 35.90, 37.60, -7.60, -1.64),
    ('Baleares', 38.60, 40.15, 1.10, 4.40),
    ('Canarias', 27.50, 29.50, -18.30, -13.30),
    ('Cantábrico', 43.25, 43.80, -7.05, -1.75),
    ('Galicia', 41.80, 43.80, -9.40, -7.05),
    ('Costa Daurada y Barcelona', 40.52, 41.66, 0.30, 2.75),
]
