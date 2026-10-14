"""v50.53 · tareas 1 y 8 (revisión del titular, 14/10/2026): «Puntos de buceo» del más cercano al más lejano, España
por zonas sin ubicación, búsqueda de una zona sin puntos y Top 10 que funciona con «Permitir», con «Bloquear» y sin
respuesta. El orden por distancia se calcula en el servidor con un filtro previo por zona de coordenadas (índice), y el
navegador recibe solo una página: nunca todos los puntos.
"""
import random
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
sys.path.insert(0, str(Path(__file__).resolve().parent))
from wod import geo  # noqa: E402
from helpers import ServerTestCase  # noqa: E402

MADRID = (40.42, -3.70)
VALENCIA = (39.47, -0.38)
TENERIFE = (28.29, -16.63)
PACIFICO = (-30.0, -140.0)      # in the middle of the ocean: nothing within 25 km


def brute(points, lat, lon):
    return sorted((geo.haversine_km(lat, lon, la, lo), pid) for pid, la, lo in points)


def fetch_from(points):
    def fetch(lat0, lat1, ranges):
        return [(pid, la, lo) for pid, la, lo in points if lat0 <= la <= lat1 and any(a <= lo <= b for a, b in ranges)]
    return fetch


class Geo(unittest.TestCase):
    def test_distances(self):
        self.assertAlmostEqual(geo.haversine_km(*MADRID, *VALENCIA), 302, delta=4)
        self.assertEqual(geo.haversine_km(*MADRID, *MADRID), 0)

    def test_box_crosses_the_antimeridian_and_the_poles(self):
        lat0, lat1, ranges = geo.box(-17.0, 179.8, 100)
        self.assertEqual(len(ranges), 2)                       # Fiji: both sides of ±180
        self.assertTrue(any(a <= -179.5 for a, _ in ranges) and any(b >= 179.9 for _, b in ranges))
        lat0, lat1, ranges = geo.box(89.5, 10, 200)
        self.assertEqual((lat1, ranges), (90, [(-180, 180)]))  # near a pole every longitude counts

    def test_nearest_is_exactly_the_brute_force_order(self):
        rnd = random.Random(53)
        points = [(i, rnd.uniform(-70, 70), rnd.uniform(-180, 180)) for i in range(1, 2001)]
        points += [(3000 + i, 39.0 + rnd.uniform(-1, 1), rnd.uniform(-1, 1)) for i in range(200)]   # a dense coast
        for lat, lon in (MADRID, TENERIFE, PACIFICO, (-16.9, 179.9), (65.0, -20.0)):
            for need in (1, 10, 37):
                got = geo.nearest(fetch_from(points), lat, lon, need)
                self.assertEqual([p for _, p in got], [p for _, p in brute(points, lat, lon)[:need]], (lat, lon, need))

    def test_nearest_with_a_filter(self):
        points = [(i, 40 + i / 100, -3) for i in range(100)]
        got = geo.nearest(fetch_from(points), 40, -3, 5, accept=lambda pid: pid % 2 == 1)
        self.assertEqual([p for _, p in got], [1, 3, 5, 7, 9])

    def test_areas_of_spain(self):
        areas = [dict(name=n, country='España', lat_min=a, lat_max=b, lon_min=c, lon_max=d) for n, a, b, c, d in geo.SPAIN_AREAS]
        cases = {(38.79, 0.18): 'Comunidad Valenciana', (37.64, -0.70): 'Murcia', (36.72, -2.19): 'Andalucía', (28.29, -16.63): 'Canarias',
                 (39.55, 2.40): 'Baleares', (42.04, 3.23): 'Costa Brava', (43.47, -3.80): 'Cantábrico', (42.33, -8.83): 'Galicia',
                 (41.10, 1.25): 'Costa Daurada y Barcelona', (40.47, 0.47): 'Comunidad Valenciana', (40.56, 0.53): 'Costa Daurada y Barcelona'}
        for (lat, lon), name in cases.items():
            self.assertEqual((geo.area_of(lat, lon, 'España', areas) or {}).get('name'), name, (lat, lon))
        self.assertIsNone(geo.area_of(21.3, -157.8, 'Estados Unidos', areas))          # Hawaii
        self.assertIsNone(geo.area_of(42.04, 3.23, 'Francia', areas))                   # an area belongs to its country

    def test_area_boxes_never_overlap(self):
        a = geo.SPAIN_AREAS
        for i in range(len(a)):
            for j in range(i + 1, len(a)):
                _, la0, la1, lo0, lo1 = a[i]; _, lb0, lb1, lc0, lc1 = a[j]
                overlap = min(la1, lb1) - max(la0, lb0) > 0 and min(lo1, lc1) - max(lo0, lc0) > 0
                self.assertFalse(overlap, (a[i][0], a[j][0]))


class Cercania(ServerTestCase):
    def setUp(self):
        self.c = self.client()

    def directory(self, qs=''):
        r = self.c.get('/api/point-directory?' + qs)
        self.assertEqual(r.status, 200, r)
        return r.json

    def active_points(self):
        return [(r['id'], r['latitude'], r['longitude']) for r in self.server.sql('SELECT id,latitude,longitude FROM dive_points WHERE active=1 AND latitude IS NOT NULL AND longitude IS NOT NULL')]

    def test_with_position_closest_first_with_km(self):
        everything = self.active_points()
        for lat, lon in (MADRID, VALENCIA, TENERIFE):
            d = self.directory(f'lat={lat}&lon={lon}&per_page=24')
            self.assertEqual((d['sort'], d['located']), ('distance', True))
            km = [x['distance_km'] for x in d['items']]
            self.assertEqual(km, sorted(km))
            want = [round(k, 1) for k, _ in brute(everything, lat, lon)[:24]]
            self.assertEqual(km, want, (lat, lon))
            d2 = self.directory(f'lat={lat}&lon={lon}&per_page=24&page=2')
            self.assertGreaterEqual(d2['items'][0]['distance_km'], km[-1])
            self.assertFalse({x['id'] for x in d['items']} & {x['id'] for x in d2['items']})
        # From Tenerife the closest are in the Canaries; from Valencia, on its coast.
        self.assertLess(self.directory('lat=28.29&lon=-16.63&per_page=3')['items'][0]['distance_km'], 60)
        self.assertLess(self.directory('lat=39.47&lon=-0.38&per_page=3')['items'][0]['distance_km'], 120)

    def test_without_position_spain_first_by_area(self):
        d = self.directory('per_page=60')
        self.assertEqual((d['sort'], d['located'], d['home_country']), ('area', False, 'España'))
        self.assertTrue(all('distance_km' not in x for x in d['items']))
        spain = [x for x in d['items'] if x['country'] == 'España']
        self.assertEqual(d['items'][:len(spain)], spain)                 # Spain before any other country
        order = [n for n, *_ in geo.SPAIN_AREAS]
        groups = []
        for x in spain:
            if not groups or groups[-1] != x['group']: groups.append(x['group'])
        self.assertEqual(len(groups), len(set(groups)))                  # each area once, together
        self.assertEqual(groups, sorted(groups, key=order.index))        # in the order of the areas
        self.assertIn('Comunidad Valenciana', groups)
        canarias = self.directory('area=Canarias&per_page=60')
        self.assertTrue(canarias['total'] > 0 and all(x['group'] == 'Canarias' for x in canarias['items']))

    def test_a_wrong_position_is_ignored(self):
        for qs in ('lat=999&lon=0', 'lat=abc&lon=1', 'lat=40', 'sort=distance'):
            d = self.directory(qs)
            self.assertEqual((d['sort'], d['located']), ('area', False), qs)

    def test_one_page_never_the_whole_catalogue(self):
        d = self.directory('per_page=5000&lat=40.42&lon=-3.70')
        self.assertEqual(len(d['items']), 60)
        self.assertGreater(d['total'], 60)

    def test_a_zone_without_points(self):
        d = self.directory('q=Hawaii')
        self.assertEqual(d['total'], 0)
        # The page then offers the closest that exist: what /api/dive-areas and the distance sort give.
        a = self.c.get('/api/dive-areas').json
        self.assertEqual(a['home_country'], 'España')
        self.assertEqual(a['areas'][0]['name'], 'Costa Brava')
        self.assertTrue(all(x['home'] for x in a['areas'][:5]))
        self.assertTrue(all({'lat', 'lon', 'count'} <= set(x) for x in a['areas']))
        self.assertGreater(len(a['places']), 10)
        self.assertLess(len(self.c.get('/api/dive-areas').body), 60_000)   # small: zones, not points

    def test_index_and_box_query(self):
        idx = [r['name'] for r in self.server.sql("PRAGMA index_list('dive_points')")]
        self.assertIn('idx_dive_points_geo', idx)
        plan = ' '.join(str(r) for r in self.server.sql(
            'EXPLAIN QUERY PLAN SELECT id,latitude,longitude FROM dive_points WHERE active=1 AND latitude BETWEEN 39 AND 41 AND longitude BETWEEN -4 AND -3'))
        self.assertIn('idx_dive_points_geo', plan)

    def test_position_is_not_written_anywhere(self):
        self.directory('lat=40.4168&lon=-3.7038')
        self.c.get('/api/top-dives?lat=40.4168&lon=-3.7038')
        logs = ''.join(p.read_text(errors='ignore') for p in self.server.tmp.rglob('*.log'))
        self.assertIn('GET /api/top-dives HTTP', logs)            # the request is in the access log, without its position
        self.assertNotIn('40.41', logs)
        self.assertNotIn('-3.70', logs)

    def test_top10_with_permission(self):
        madrid = self.c.get('/api/top-dives?lat=40.42&lon=-3.70').json
        self.assertEqual((madrid['scope'], madrid['auto']), ('near', True))
        self.assertIn(madrid['radius_km'], (25, 50, 100, 250, 500, 1000, 2500))
        self.assertEqual(len(madrid['items']), 10)
        self.assertTrue(all(x['distance_km'] <= madrid['radius_km'] for x in madrid['items']))
        valencia = self.c.get('/api/top-dives?lat=39.47&lon=-0.38&radius=auto').json
        self.assertLess(valencia['radius_km'], madrid['radius_km'])       # the coast has dive sites closer
        canarias = self.c.get('/api/top-dives?lat=28.29&lon=-16.63').json
        self.assertTrue(canarias['items'] and all(x['country'] == 'España' for x in canarias['items']))
        # Same zone of about 11 km: the same answer (kept per snapshot).
        self.assertEqual(self.c.get('/api/top-dives?lat=40.43&lon=-3.71').json['items'], madrid['items'])

    def test_top10_without_permission_is_spain(self):
        home = self.c.get('/api/top-dives?scope=home').json
        self.assertEqual((home['scope'], home['home_country']), ('home', 'España'))
        self.assertEqual(len(home['items']), 10)
        self.assertTrue(all(x['country'] == 'España' and 'distance_km' not in x for x in home['items']))

    def test_top10_fixed_radius_with_nothing_inside(self):
        d = self.c.get(f'/api/top-dives?lat={PACIFICO[0]}&lon={PACIFICO[1]}&radius=25').json
        self.assertEqual((d['items'], d['radius_km']), ([], 25.0))
        self.assertTrue(d['nearest'] and d['nearest']['distance_km'] > 25)

    def test_top10_needs_a_valid_position(self):
        for qs in ('', 'lat=100&lon=0', 'lat=x&lon=y'):
            self.assertEqual(self.c.get('/api/top-dives?' + qs).status, 400, qs)


class SinProfundidadHabitual(ServerTestCase):
    def test_dive_types_without_usual_depth(self):
        c = self.client()
        body = c.get('/api/dive-types').body.decode()
        self.assertNotIn('depth_min', body)
        self.assertNotIn('depth_max', body)
        root = Path(__file__).resolve().parents[1]
        for f in ('public/js/world-dives-v8.js', 'public/js/wd-app.js', 'public/js/wd-app-pro.js', 'app/server.py', 'scripts/crear_demo.py'):
            self.assertNotIn('Profundidad habitual', (root / f).read_text(encoding='utf-8'), f)


if __name__ == '__main__':
    unittest.main()
