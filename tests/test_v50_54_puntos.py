"""v50.54 · puntos 2, 3 y 4 del encargo del 14/10/2026, lo que hace el servidor:

- «Puntos de buceo»: filtros de región, tipo, nivel y profundidad, cada uno con su número calculado con los demás
  filtros puestos (una región sin puntos no aparece); la vista «Mapa» con todos los puntos filtrados.
- Ficha del punto: condiciones opcionales (mejor época, temperatura del agua, visibilidad) que solo edita la
  administración o el centro dueño del punto, con sus comprobaciones; titulación recomendada del punto o, si no tiene,
  la del tipo de buceo más exigente.
"""
from __future__ import annotations

import sys
import unittest
from urllib.parse import quote
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from helpers import ServerTestCase  # noqa: E402


class Listado(ServerTestCase):
    def d(self, qs=''):
        r = self.client().get('/api/point-directory?' + qs); self.assertEqual(r.status, 200, qs); return r.json

    def test_facets_with_the_other_filters_applied(self):
        all_ = self.d('per_page=1')
        f = all_['facets']
        self.assertEqual(sum(a['count'] for a in f['areas']), all_['total'])
        self.assertTrue(all(a['count'] > 0 for a in f['areas']))            # a region with no points is not offered
        self.assertEqual([x['key'] for x in f['depths']], ['d18', 'd30', 'd40'])
        self.assertEqual([x['key'] for x in f['levels']], ['start', 'mid', 'adv'])
        area = next(a for a in f['areas'] if a['count'] >= 5)
        one = self.d('per_page=60&area=' + quote(area['name']))
        self.assertEqual(one['total'], area['count'])
        # with a depth band, every area count is the number of points of that band in that area
        band = next(x for x in f['depths'] if x['count'])
        with_band = self.d(f"per_page=1&depth={band['key']}")
        self.assertEqual(with_band['total'], band['count'])
        self.assertEqual(sum(a['count'] for a in with_band['facets']['areas']), band['count'])
        # the facet of a dimension ignores its own filter (the visitor can switch)
        self.assertEqual(with_band['facets']['depths'], f['depths'])

    def test_depth_bands(self):
        for key, lo, hi in (('d18', None, 18), ('d30', 18, 30), ('d40', 30, None)):
            items = self.d(f'per_page=60&depth={key}')['items']
            for p in items:
                self.assertIsNotNone(p['max_depth'])
                if lo is not None: self.assertGreater(p['max_depth'], lo, p)
                if hi is not None: self.assertLessEqual(p['max_depth'], hi, p)
        self.assertEqual(self.d('per_page=1&depth=nada')['total'], self.d('per_page=1')['total'])   # unknown value: ignored

    def test_type_counts_and_combination(self):
        f = self.d('per_page=1')['facets']
        t = next(x for x in f['types'] if x['count'] >= 3)
        self.assertEqual(self.d(f"per_page=1&type={t['key']}")['total'], t['count'])
        lv = self.d(f"per_page=1&type={t['key']}")['facets']['levels']
        for x in lv:
            if x['count']: self.assertEqual(self.d(f"per_page=1&type={t['key']}&level={x['key']}")['total'], x['count'])

    def test_map_view_has_every_filtered_point(self):
        f = self.d('per_page=1')['facets']
        area = next(a for a in f['areas'] if a['count'] >= 5)['name']
        m = self.d('view=map&area=' + quote(area))
        self.assertEqual(len(m['items']), m['total'])
        self.assertEqual(m['total'], self.d('per_page=1&area=' + quote(area))['total'])
        self.assertEqual(set(m['items'][0]), {'id', 'name', 'latitude', 'longitude', 'area', 'level', 'min_depth', 'max_depth', 'types'})
        self.assertGreater(len(self.d('view=map')['items']), 60)               # not one page: the whole list


class Ficha(ServerTestCase):
    def point(self, name='Cabo San Antonio'):
        pid = self.client().get('/api/point-directory?q=' + name.replace(' ', '%20')).json['items'][0]['id']
        return pid, self.client().get(f'/api/dive-points/{pid}').json['item']

    def test_recommended_certification(self):
        pid, p = self.point()
        self.assertTrue(p['recommended_cert'])                                  # from its type when the site has none
        self.server.sql("UPDATE dive_points SET recommended_certification_id=(SELECT id FROM certifications ORDER BY id LIMIT 1) WHERE id=?", (pid,))
        own = self.server.sql('SELECT name FROM certifications ORDER BY id LIMIT 1')[0]['name']
        self.assertEqual(self.client().get(f'/api/dive-points/{pid}').json['item']['recommended_cert'], own)

    def test_conditions_edited_and_checked(self):
        pid, p = self.point()
        self.assertIsNone(p.get('best_months')); self.assertIsNone(p.get('water_temp_min'))
        admin = self.make_admin()
        ok = admin.post('/api/dive-points/conditions', {'id': pid, 'best_months': [9, 6, 7, 8, 7], 'water_temp_min': 15, 'water_temp_max': '24.5',
                                                         'visibility_min': '', 'visibility_max': 25})
        self.assertEqual(ok.status, 200, ok)
        p = self.client().get(f'/api/dive-points/{pid}').json['item']
        self.assertEqual((p['best_months'], p['water_temp_min'], p['water_temp_max'], p['visibility_min'], p['visibility_max']), ('6,7,8,9', 15.0, 24.5, None, 25.0))
        for bad, why in (({'best_months': [0]}, 'meses'), ({'best_months': 'x'}, 'meses'), ({'water_temp_min': 50}, 'entre'),
                         ({'water_temp_min': 'frío'}, 'número'), ({'visibility_min': 30, 'visibility_max': 10}, 'mayor')):
            r = admin.post('/api/dive-points/conditions', {'id': pid, **bad})
            self.assertEqual(r.status, 400, bad); self.assertIn(why, r.json['error'])
        # all twelve months is «all year»: nothing to show
        admin.post('/api/dive-points/conditions', {'id': pid, 'best_months': list(range(1, 13))})
        self.assertIsNone(self.client().get(f'/api/dive-points/{pid}').json['item']['best_months'])
        self.assertTrue(self.server.sql("SELECT 1 FROM audit_log WHERE action='dive_point_conditions' AND entity_id=?", (pid,)))

    def test_only_admin_or_owner_centre(self):
        pid, _ = self.point()
        self.assertIn(self.client().post('/api/dive-points/conditions', {'id': pid, 'water_temp_min': 10}).status, (401, 403))   # no session
        diver = self.make_diver('cond')
        self.assertEqual(diver.post('/api/dive-points/conditions', {'id': pid, 'water_temp_min': 10}).status, 403)


if __name__ == '__main__':
    unittest.main()
