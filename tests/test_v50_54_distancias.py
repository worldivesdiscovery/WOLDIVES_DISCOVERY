"""v50.54 · punto 5 del encargo del 14/10/2026: distancias correctas o ninguna.

El fallo: desde Jávea/Dénia, «Cabo San Antonio a 556 km». Los datos y la fórmula eran correctos; la posición no: el
navegador daba una posición aproximada (por IP, o una guardada de hace 10 minutos) y la web la usaba como si fuera
exacta. Ahora el navegador pide la posición precisa y envía su precisión (acc, metros); el servidor solo da kilómetros
con 1 km de error o menos. Una posición aproximada, una zona, una localidad o un punto elegido en el mapa ordenan por
cercanía, pero sin kilómetros.

Prueba obligatoria del encargo: Jávea → Cabo San Antonio a menos de 15 km.
"""
from __future__ import annotations

import subprocess
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from wod import geo as wgeo  # noqa: E402

from helpers import ServerTestCase  # noqa: E402

JAVEA = (38.7893, 0.1662)    # town centre of Xàbia / Jávea
DENIA = (38.8408, 0.1057)    # town centre of Dénia
CABO = 'Cabo San Antonio'


class Unidades(unittest.TestCase):
    def test_precise_needs_a_known_accuracy_of_one_km_or_better(self):
        for acc in ('5', '35', '999.5', '1000', 20):
            self.assertTrue(wgeo.precise(acc), acc)
        for acc in (None, '', '0', '-3', 'nan', 'inf', '1000.1', '25000', 'x'):
            self.assertFalse(wgeo.precise(acc), acc)

    def test_no_false_decimals(self):
        self.assertEqual(wgeo.shown_km(3.2345, 38.8015, 0.1991), 3.2)   # 4 decimals: one decimal shown
        self.assertEqual(wgeo.shown_km(3.2345, 38.80, 0.20), 3.0)       # 2 decimals (±1 km): whole km
        self.assertEqual(wgeo.shown_km(3.7, 38.8, 0.19912), 4.0)
        self.assertIsNone(wgeo.shown_km(None, 1, 1))

    def test_position_rounded_to_about_100_m(self):
        self.assertEqual(wgeo.round_coord(38.789349), 38.789)
        self.assertLess(wgeo.haversine_km(38.7893, 0.1662, wgeo.round_coord(38.7893), wgeo.round_coord(0.1662)), 0.1)

    def test_haversine_against_known_distances(self):
        self.assertAlmostEqual(wgeo.haversine_km(40.4168, -3.7038, 41.3874, 2.1686), 505, delta=3)    # Madrid–Barcelona
        self.assertAlmostEqual(wgeo.haversine_km(*JAVEA, 38.8015, 0.1991), 3.2, delta=0.1)

    def test_coordinate_review_of_the_whole_catalogue(self):
        r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'revisar_coordenadas.py')], capture_output=True, text=True, timeout=60)
        self.assertEqual(r.returncode, 0, r.stdout[-2000:])
        self.assertIn('| Jávea / Xàbia (centro del pueblo) | Cabo San Antonio | 3,2 km | < 15 km | Correcto |', r.stdout)
        self.assertIn('| Dénia (centro del pueblo) | Cabo San Antonio | 9,2 km | < 15 km | Correcto |', r.stdout)
        self.assertIn('· 0 errores ·', r.stdout)


class DistanciasEnLaWeb(ServerTestCase):
    def directory(self, pos, acc=None, **extra):
        q = f'/api/point-directory?sort=distance&lat={pos[0]}&lon={pos[1]}&per_page=12' + (f'&acc={acc}' if acc is not None else '')
        q += ''.join(f'&{k}={v}' for k, v in extra.items())
        r = self.client().get(q); self.assertEqual(r.status, 200); return r.json

    def test_javea_to_cabo_san_antonio_under_15_km(self):
        for pos in (JAVEA, DENIA):
            d = self.directory(pos, acc=20)
            self.assertTrue(d['distances'])
            cabo = next(x for x in d['items'] if x['name'] == CABO)
            self.assertLess(cabo['distance_km'], 15, cabo)
            self.assertTrue(all(x['distance_km'] is not None and x['distance_km'] < 100 for x in d['items']), [(x['name'], x['distance_km']) for x in d['items']])
            kms = [x['distance_km'] for x in d['items']]
            self.assertTrue(all(b >= a - 1 for a, b in zip(kms, kms[1:])), kms)   # closest first (whole km on coarse sites)
        self.assertEqual(next(x for x in self.directory(JAVEA, acc=20)['items'] if x['name'] == CABO)['distance_km'], 3.2)

    def test_approximate_unknown_or_chosen_position_gives_no_km(self):
        precise = [x['id'] for x in self.directory(JAVEA, acc=20)['items']]
        for acc in (None, 0, 1500, 25000, 'abc'):
            d = self.directory(JAVEA, acc=acc)
            self.assertFalse(d['distances'], acc)
            self.assertTrue(all(x['distance_km'] is None for x in d['items']), acc)
            self.assertEqual([x['id'] for x in d['items']], precise)            # still sorted by closeness
        # Madrid by IP while the visitor is in Jávea: what produced «556 km» — now no kilometre at all.
        d = self.directory((40.4168, -3.7038), acc=30000)
        self.assertTrue(all(x['distance_km'] is None for x in d['items']))

    def test_top_10(self):
        c = self.client()
        r = c.get(f'/api/top-dives?lat={JAVEA[0]}&lon={JAVEA[1]}&radius=25&acc=15').json
        self.assertTrue(r['distances'])
        cabo = next(x for x in r['items'] if x['name'] == CABO)
        self.assertLess(cabo['distance_km'], 15)
        self.assertTrue(all(x['distance_km'] <= 25 for x in r['items']))
        order = [x['id'] for x in r['items']]
        for q in ('', '&acc=5000'):
            a = c.get(f'/api/top-dives?lat={JAVEA[0]}&lon={JAVEA[1]}&radius=25{q}').json
            self.assertFalse(a['distances']); self.assertEqual([x['id'] for x in a['items']], order)
            self.assertTrue(all(x['distance_km'] is None for x in a['items']))
        # the cached answer was not changed by the request without km
        self.assertEqual(c.get(f'/api/top-dives?lat={JAVEA[0]}&lon={JAVEA[1]}&radius=25&acc=15').json['items'][0]['distance_km'], r['items'][0]['distance_km'])
        far = c.get('/api/top-dives?lat=40.4168&lon=-3.7038&radius=25').json   # Madrid: nothing within 25 km
        if far['items'] == [] and far.get('nearest'): self.assertIsNone(far['nearest']['distance_km'])

    def test_departures_of_the_app(self):
        c = self.client()
        for q, shown in ((f'lat={JAVEA[0]}&lon={JAVEA[1]}&acc=30', True), (f'lat={JAVEA[0]}&lon={JAVEA[1]}', False), (f'lat={JAVEA[0]}&lon={JAVEA[1]}&acc=12000', False), ('', False)):
            d = c.get('/api/salidas-cercanas?' + q).json
            self.assertEqual(d['distances'], shown, q)
            if not shown: self.assertTrue(all(x['distance_km'] is None for x in d['items']), q)


if __name__ == '__main__':
    unittest.main()
