"""v50.58 · encargo del 16/10/2026: fichas de punto más completas y catálogo de puntos ampliado.

Las comprobaciones del encargo en el servidor:
1. Ficha completa con todos los campos nuevos; con campos vacíos no llega nada vacío (la web no enseña huecos).
2. Filtros nuevos (acceso, corriente, tipo de fondo; la profundidad ya estaba) en la lista y en el mapa.
3. Duplicados: un punto a 100 m de otro con un nombre parecido se detecta; unir dos fichas conserva fotos, centros
   (y con ellos sus reseñas) y la ficha archivada lleva a la que se queda.
4. Ningún punto nuevo cae en tierra (la costa de OpenStreetMap con 10 m de error).
5. El registro de fuentes solo lo ve la administración; un buceador o un centro no.
6. Lotes «Pendiente de verificar»: nada se ve hasta publicarlo; lo repetido completa la ficha existente; lo dudoso
   espera la decisión; lo que cae en tierra no se publica.
7. Propuestas de cambio: el centro asociado (posición, corriente, visibilidad, avisos) y el buceador (también los
   campos nuevos); la administración acepta o rechaza con un clic y cada dato apunta su fuente.
"""
import json
import sys
import unittest
from datetime import date
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from helpers import ServerTestCase, PNG_BYTES  # noqa: E402
from wod import costa, puntos as wpun  # noqa: E402


def sea_near(lat, lon, metres=100):
    """Un punto en el mar a unos `metres` del dado (busca alrededor, sin inventar nada: lo dice la costa)."""
    for dlat, dlon in ((0, 1), (0, -1), (1, 0), (-1, 0), (.7, .7), (-.7, .7), (.7, -.7), (-.7, -.7)):
        la = lat + dlat * metres / 111320.0
        lo = lon + dlon * metres / (111320.0 * 0.78)
        c = costa.check(la, lo)
        if c and not c['land']: return round(la, 6), round(lo, 6)
    return None


class Helpers(unittest.TestCase):
    def test_names(self):
        self.assertEqual(wpun.similarity('Bajo de Dentro', 'Bajón de Dentro'), 1.0)
        self.assertEqual(wpun.similarity('El Bajo de Fuera', 'Bajo de Fuera'), 1.0, 'sin artículos')
        self.assertEqual(wpun.similarity("Illa de l'Aire", 'Isla del Aire'), 1.0, 'catalán y castellano')
        self.assertEqual(wpun.similarity("Cap d'Or", 'Cabo de Or'), 1.0)
        self.assertGreaterEqual(wpun.similarity('Isla del Descubridor', 'Descubridor'), .86)
        self.assertLess(wpun.similarity('La Catedral', 'Cueva de la Virgen'), .5)
        self.assertEqual(wpun.verdict(100, .9), 'same'); self.assertEqual(wpun.verdict(100, .2), 'doubt')
        self.assertEqual(wpun.verdict(1500, .95), 'doubt'); self.assertIsNone(wpun.verdict(1500, .5)); self.assertIsNone(wpun.verdict(5000, 1))

    def test_fields(self):
        f = wpun.clean_fields({'access': 'boat', 'current': 'mild', 'water_temps': {'winter': [13, 15], 'summer': [24, 27]},
                               'bottom': ['posidonia', 'rock'], 'best_months': [9, 6, 7], 'warnings': 'Tráfico de barcos en la boca',
                               'protection': 'marine_reserve', 'protection_name': 'Reserva Marina de Cabo de Palos', 'permit_required': True})
        self.assertEqual((f['access'], f['current_level'], f['bottom'], f['best_months'], f['permit_required']), ('boat', 'mild', 'rock,posidonia', '6,7,9', 1))
        self.assertEqual(json.loads(f['water_temps']), {'winter': [13.0, 15.0], 'summer': [24.0, 27.0]})
        for bad, why in (({'current': 'huracán'}, 'Corriente'), ({'water_temps': {'winter': [20, 12]}}, 'mínima'), ({'bottom': ['lava']}, 'fondo'),
                         ({'min_depth': 40, 'max_depth': 12}, 'mínima'), ({'warnings': 'x' * 300}, '280'), ({'best_months': [13]}, 'meses')):
            with self.assertRaises(ValueError) as e: wpun.clean_fields(bad)
            self.assertIn(why, str(e.exception), bad)
        empty = wpun.public_fields({'verification_status': 'curated_pending'})
        self.assertEqual(empty, {'data_status': 'pending'}, 'nothing empty travels to the page')

    def test_season_and_hemisphere(self):
        self.assertEqual(wpun.season_of(1, 38.7), 'winter'); self.assertEqual(wpun.season_of(1, -8.3), 'summer')
        r = wpun.public_fields({'water_temps': '{"winter":[14,15]}', 'latitude': 38.7}, today=date(2026, 1, 20))
        self.assertEqual(r['season_now'], 'winter')

    def test_land_or_sea(self):
        self.assertTrue(costa.check(40.4168, -3.7038)['land'], 'Madrid')
        self.assertTrue(costa.check(28.2724, -16.6425)['land'], 'el Teide')
        sea = costa.check(39.5, 1.5)
        self.assertFalse(sea['land']); self.assertIsNone(sea['shore_m'], 'mar abierto')
        self.assertEqual(costa.verdict(40.4168, -3.7038)[0], 'error')
        self.assertEqual(costa.verdict(42.0453, 3.2050, 'shore')[0], 'warn', 'un punto de costa a más de 200 m')
        self.assertEqual(costa.verdict(40.53, -2.70, None, 'Lago')[0], 'ok', 'agua interior: no se mira la costa')
        self.assertIsNone(costa.check(-33.9, 151.3), 'sin datos de esa costa: no se adivina')


class Catalogue(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'puntos')
        cls.cid = cls.center.user['center_id']
        cls.diver = t.make_diver('puntos1')
        # a Spanish site of the demo catalogue that is in the sea, as the base for duplicates
        rows = cls.server.sql("SELECT id,name,latitude,longitude FROM dive_points WHERE country='España' AND active=1 AND latitude IS NOT NULL ORDER BY id")
        cls.base = next(r for r in rows if (c := costa.check(r['latitude'], r['longitude'])) and not c['land'])

    def new_point(self, **kw):
        lat, lon = sea_near(self.base['latitude'], self.base['longitude'], kw.pop('metres', 1500))
        data = {'name': kw.pop('name', 'Punto de prueba'), 'country': 'España', 'region': 'Comunitat Valenciana', 'dive_type': 'Arrecife',
                'difficulty': 'Intermedio', 'latitude': lat, 'longitude': lon, **kw}
        return self.admin.post('/api/dive-points', data)

    # 1 ------------------------------------------------------------------------------------------------
    def test_1_full_and_empty_site(self):
        r = self.new_point(name='Bajo Completo de Prueba', metres=2500, min_depth=6, max_depth=32, access='both', current='moderate',
                           water_temps={'winter': [13, 15], 'spring': [15, 18], 'summer': [23, 27], 'autumn': [19, 23]},
                           visibility_min=10, visibility_max=20, bottom=['rock', 'posidonia', 'wall'], best_months=[6, 7, 8, 9],
                           warnings='Tráfico de barcos en la punta; corriente en la cara norte', protection='marine_reserve',
                           protection_name='Reserva Marina de prueba', permit_required=True, description='Una pared con posidonia arriba y una punta con corriente.')
        self.assertEqual(r.status, 200, r.json); pid = r.json['id']
        it = self.client().get(f'/api/dive-points/{pid}?lang=es').json['item']
        self.assertEqual((it['min_depth'], it['max_depth'], it['access'], it['current']), (6, 32, 'both', 'moderate'))
        self.assertEqual(set(it['water_temps']), {'winter', 'spring', 'summer', 'autumn'}); self.assertIn(it['season_now'], it['water_temps'])
        self.assertEqual((it['visibility_min'], it['visibility_max'], it['bottom'], it['best_months']), (10, 20, ['rock', 'posidonia', 'wall'], '6,7,8,9'))
        self.assertEqual((it['protection'], it['protection_name'], it['permit_required'], it['data_status']), ('marine_reserve', 'Reserva Marina de prueba', True, 'verified'))
        self.assertTrue(it['warnings'].startswith('Tráfico'))
        self.assertEqual(it['description'], 'Una pared con posidonia arriba y una punta con corriente.', 'the text written by the administration is the one shown')
        en = self.client().get(f'/api/dive-points/{pid}?lang=en').json['item']
        self.assertTrue(en.get('warnings_pending_translation'), 'Spanish as the fallback, marked «pending translation»')
        for k in wpun.PRIVATE: self.assertNotIn(k, it, k)
        # a site with nothing new: no empty keys at all
        r = self.new_point(name='Punto Vacío de Prueba', metres=3200)
        self.assertEqual(r.status, 200, r.json)
        it = self.client().get(f"/api/dive-points/{r.json['id']}").json['item']
        for k in ('access', 'current', 'water_temps', 'season_now', 'bottom', 'warnings', 'protection', 'permit_required'): self.assertNotIn(k, it, k)
        self.assertEqual(it['data_status'], 'verified')

    def test_1b_admin_edits_every_field_and_keeps_the_certification(self):
        pid = self.new_point(name='Punto Editable', metres=4000).json['id']
        cert = self.server.sql('SELECT id FROM certifications ORDER BY id LIMIT 1')[0]['id']
        self.assertEqual(self.admin.post('/api/dive-points/update', {'id': pid, 'recommended_certification_id': cert}).status, 200)
        r = self.admin.post('/api/dive-points/update', {'id': pid, 'current': 'strong', 'zone': 'Europa', 'subregion': 'Prueba', 'data_status': 'pending',
                                                        'description': 'Texto nuevo escrito a mano por la administración.'})
        self.assertEqual(r.status, 200, r.json)
        row = self.server.sql('SELECT recommended_certification_id,current_level,zone,subregion,verification_status FROM dive_points WHERE id=?', (pid,))[0]
        self.assertEqual(dict(row), {'recommended_certification_id': cert, 'current_level': 'strong', 'zone': 'Europa', 'subregion': 'Prueba', 'verification_status': 'pending_review'},
                         'a save without the certification keeps it (it was wiped)')
        it = self.client().get(f'/api/dive-points/{pid}').json['item']
        self.assertEqual(it['description'], 'Texto nuevo escrito a mano por la administración.')
        self.assertEqual(it['data_status'], 'pending')
        full = self.admin.get(f'/api/admin/dive-points/{pid}').json
        self.assertIn('current', [s['field'] for s in full['sources']], 'the change is in the register of sources')
        self.assertEqual(full['item']['position_check']['status'], 'ok')

    # 2 ------------------------------------------------------------------------------------------------
    def test_2_filters_in_list_and_map(self):
        a = self.new_point(name='Filtro Barco Fuerte', metres=5000, access='boat', current='strong', bottom=['wreck']).json['id']
        b = self.new_point(name='Filtro Costa Suave', metres=5600, access='shore', current='mild', bottom=['sand', 'posidonia']).json['id']
        c = self.new_point(name='Filtro Los Dos', metres=6200, access='both', current='mild', bottom=['posidonia']).json['id']
        get = lambda q: {x['id'] for x in self.client().get('/api/point-directory?per_page=60&sort=name&' + q).json['items']}
        self.assertTrue({a, c} <= get('access=boat') and b not in get('access=boat'), '«Barco» also finds the sites reached both ways')
        self.assertTrue({b, c} <= get('access=shore') and a not in get('access=shore'))
        self.assertEqual(get('current=strong') & {a, b, c}, {a})
        self.assertEqual(get('bottom=posidonia') & {a, b, c}, {b, c})
        self.assertEqual(get('access=shore&bottom=sand') & {a, b, c}, {b})
        f = self.client().get('/api/point-directory?access=boat').json['facets']
        self.assertTrue({x['key'] for x in f['bottoms']} >= set(wpun.BOTTOMS)); self.assertTrue(any(x['count'] for x in f['currents']))
        m = self.client().get('/api/dive-points/map').json
        idx = {k: i for i, k in enumerate(m['fields'])}
        row = next(r for r in m['rows'] if r[idx['id']] == a)
        self.assertEqual((row[idx['access']], row[idx['current_level']], row[idx['bottom']]), ('boat', 'strong', 'wreck'), 'the map filters by itself')

    # 3 ------------------------------------------------------------------------------------------------
    def test_3_duplicates_detected_and_merged(self):
        base = self.base
        lat, lon = sea_near(base['latitude'], base['longitude'], 100)
        r = self.admin.post('/api/dive-points', {'name': 'El ' + base['name'], 'country': 'España', 'dive_type': 'Arrecife', 'latitude': lat, 'longitude': lon})
        self.assertEqual(r.status, 409, 'a site 100 m away with a similar name is detected'); self.assertEqual(r.json['duplicates'][0]['id'], base['id'])
        self.assertLess(r.json['duplicates'][0]['distance_m'], 300)
        # created anyway (the administration insists): it waits in «Posibles duplicados»
        r = self.admin.post('/api/dive-points', {'name': 'El ' + base['name'], 'country': 'España', 'dive_type': 'Arrecife', 'latitude': lat, 'longitude': lon, 'force_new': True})
        self.assertEqual(r.status, 200, r.json); dup_id = r.json['id']
        pair = next(p for p in self.admin.get('/api/admin/dive-points/duplicates').json['pairs'] if {p['a_point_id'], p['b_point_id']} == {base['id'], dup_id})
        # the copy has a photo and a centre (whose reviews give the rating of the site): both go to the one that stays
        self.server.sql('INSERT INTO dive_point_photos(dive_point_id,image_path,caption,sort_order) VALUES(?,?,?,?)', (dup_id, '/img/portada/fondo.webp', 'foto de la copia', 1))
        self.server.sql("INSERT INTO center_point_links(center_id,dive_point_id,created_at) VALUES(?,?,datetime('now'))", (self.cid, dup_id))
        r = self.admin.post('/api/admin/dive-points/duplicates/decide', {'id': pair['id'], 'decision': 'merge', 'keep_id': base['id']})
        self.assertEqual(r.status, 200, r.json)
        self.assertEqual(self.server.sql('SELECT COUNT(*) AS n FROM dive_point_photos WHERE dive_point_id=? AND caption=?', (base['id'], 'foto de la copia'))[0]['n'], 1)
        self.assertEqual(self.server.sql('SELECT COUNT(*) AS n FROM center_point_links WHERE dive_point_id=? AND center_id=?', (base['id'], self.cid))[0]['n'], 1)
        gone = self.client().get(f'/api/dive-points/{dup_id}')
        self.assertEqual((gone.status, gone.json.get('merged_into')), (404, base['id']), 'old links lead to the site that stays')
        self.assertEqual(self.server.sql('SELECT active,merged_into FROM dive_points WHERE id=?', (dup_id,))[0]['merged_into'], base['id'], 'archived, never deleted')
        self.assertTrue(self.server.sql('SELECT snapshot FROM point_merges WHERE drop_id=?', (dup_id,)), 'what it had is kept')
        # «Mantener separados»: never asked again
        far = self.new_point(name='Punto Distinto Cercano', metres=180).json
        open_pairs = [p for p in self.admin.get('/api/admin/dive-points/duplicates').json['pairs'] if far.get('id') in (p['a_point_id'], p['b_point_id'])]
        for p in open_pairs: self.assertEqual(self.admin.post('/api/admin/dive-points/duplicates/decide', {'id': p['id'], 'decision': 'separate'}).status, 200)
        self.admin.post('/api/admin/dive-points/duplicates/scan')
        self.assertFalse([p for p in self.admin.get('/api/admin/dive-points/duplicates').json['pairs'] if far.get('id') in (p['a_point_id'], p['b_point_id'])])

    # 4 ------------------------------------------------------------------------------------------------
    def test_4_no_new_site_on_land(self):
        r = self.admin.post('/api/dive-points', {'name': 'Punto en Madrid', 'country': 'España', 'dive_type': 'Arrecife', 'latitude': 40.4168, 'longitude': -3.7038})
        self.assertEqual(r.status, 409); self.assertIn('tierra', r.json['error'])
        chk = self.center.get('/api/admin/dive-points/check?lat=40.4168&lon=-3.7038').json
        self.assertEqual(chk['position']['status'], 'error')
        self.assertEqual(self.diver.get('/api/admin/dive-points/check?lat=40.4&lon=-3.7').status, 403)

    # 5 ------------------------------------------------------------------------------------------------
    def test_5_sources_only_for_the_administration(self):
        pid = self.new_point(name='Punto con Fuentes', metres=7000, source_ref='https://www.ejemplo.org/reserva', source_note='GPS del centro').json['id']
        ok = self.admin.post('/api/admin/dive-points/sources', {'point_id': pid, 'kind': 'official', 'field': 'protection', 'ref': 'BOE de la reserva', 'checked_at': '2026-10-16'})
        self.assertEqual(ok.status, 200, ok.json)
        self.assertEqual({s['kind'] for s in ok.json['sources']} >= {'admin', 'official'}, True)
        for c in (self.diver, self.center, self.client()):
            self.assertIn(c.get(f'/api/admin/dive-points/{pid}').status, (401, 403))
            self.assertIn(c.post('/api/admin/dive-points/sources', {'point_id': pid, 'kind': 'admin'}).status, (401, 403))
        public = json.dumps(self.client().get(f'/api/dive-points/{pid}').json) + json.dumps(self.client().get('/api/dive-points').json)
        for word in ('ejemplo.org', 'BOE de la reserva', 'GPS del centro', 'position_check', 'source_name', 'batch_id'):
            self.assertNotIn(word, public, word)

    # 6 ------------------------------------------------------------------------------------------------
    def test_6_batch_pending_until_published(self):
        base = self.base
        sea1 = sea_near(base['latitude'], base['longitude'], 9000); sea2 = sea_near(base['latitude'], base['longitude'], 120)
        sea3 = sea_near(base['latitude'], base['longitude'], 250)
        src = [{'kind': 'research', 'ref': 'Fuente pública 1', 'checked_at': '2026-10-16'}, {'kind': 'research', 'ref': 'Fuente pública 2', 'checked_at': '2026-10-16'}]
        items = [{'name': 'Lote Nuevo en el Mar', 'country': 'España', 'zone': 'Europa', 'subregion': 'Prueba', 'dive_type': 'Arrecife', 'latitude': sea1[0], 'longitude': sea1[1],
                  'max_depth': 18, 'access': 'boat', 'description': 'Descripción con palabras propias.', 'sources': src},
                 {'name': 'Lote en Tierra', 'country': 'España', 'dive_type': 'Arrecife', 'latitude': 40.4168, 'longitude': -3.7038, 'sources': src},
                 {'name': base['name'], 'country': 'España', 'dive_type': 'Arrecife', 'latitude': sea2[0], 'longitude': sea2[1], 'current': 'variable', 'sources': src},
                 {'name': 'Nombre Muy Distinto', 'country': 'España', 'dive_type': 'Arrecife', 'latitude': sea3[0], 'longitude': sea3[1], 'sources': src}]
        r = self.admin.post('/api/admin/dive-points/batches', {'zone': 'Comunidad Valenciana', 'title': 'Lote de prueba', 'items': items})
        self.assertEqual(r.status, 200, r.json); bid = r.json['id']
        s = r.json['summary']; self.assertEqual((s['pending'], s['land'], s['same'], s['doubts']), (4, 1, 1, 1))
        names = lambda: {x['name'] for x in self.client().get('/api/dive-points').json['items']}
        self.assertNotIn('Lote Nuevo en el Mar', names(), 'nothing is public before it is published')
        r = self.admin.post('/api/admin/dive-points/batches/publish', {'batch_id': bid})
        self.assertEqual(r.status, 200, r.json)
        self.assertEqual(sorted(x['status'] for x in r.json['done']), ['merged', 'published'])
        self.assertEqual(len(r.json['skipped']), 2, 'on land and the doubt wait')
        self.assertIn('Lote Nuevo en el Mar', names())
        merged = next(x for x in r.json['done'] if x['status'] == 'merged')
        self.assertEqual(merged['point_id'], base['id'], self.admin.get(f'/api/admin/dive-points/batches/{bid}').json['items'])
        self.assertEqual(self.server.sql('SELECT current_level FROM dive_points WHERE id=?', (base['id'],))[0]['current_level'], 'variable', 'the existing site gets what it lacked')
        new_id = next(x['point_id'] for x in r.json['done'] if x['status'] == 'published')
        self.assertEqual(self.client().get(f'/api/dive-points/{new_id}').json['item']['data_status'], 'pending', '«Pendiente de verificar» until checked')
        self.assertEqual(len([s for s in self.admin.get(f'/api/admin/dive-points/{new_id}').json['sources'] if s['kind'] == 'research']), 2, 'two public sources, kept privately')
        items = self.admin.get(f'/api/admin/dive-points/batches/{bid}').json['items']
        land = next(i for i in items if i['name'] == 'Lote en Tierra'); doubt = next(i for i in items if i['name'] == 'Nombre Muy Distinto')
        bad = self.admin.post('/api/admin/dive-points/batches/publish', {'item_id': land['id']})
        self.assertEqual(bad.status, 400); self.assertIn('tierra', bad.json['error'].lower())
        fix = self.admin.post('/api/admin/dive-points/batches/item', {'item_id': land['id'], 'latitude': sea1[0] + .01, 'longitude': sea1[1]})
        self.assertEqual(fix.status, 200, fix.json)
        self.assertEqual(self.admin.post('/api/admin/dive-points/batches/discard', {'item_id': land['id']}).status, 200)
        ask = self.admin.post('/api/admin/dive-points/batches/publish', {'item_id': doubt['id']})
        self.assertEqual(ask.status, 400); self.assertIn('elige', ask.json['error'])
        self.assertEqual(self.admin.post('/api/admin/dive-points/batches/publish', {'item_id': doubt['id'], 'decision': 'new'}).status, 200)
        self.assertEqual(self.admin.get('/api/admin/dive-points/batches').json['items'][0]['status'], 'published')

    # 7 ------------------------------------------------------------------------------------------------
    def test_7_proposals_from_centres_and_divers(self):
        pid = self.new_point(name='Punto con Propuestas', metres=8000, current='mild', visibility_min=8, visibility_max=12).json['id']
        self.server.sql("INSERT OR IGNORE INTO center_point_links(center_id,dive_point_id,created_at) VALUES(?,?,datetime('now'))", (self.cid, pid))
        r = self.center.post(f'/api/dive-points/{pid}/propose', {'current': 'strong', 'visibility_min': 15, 'visibility_max': 25, 'bottom': ['sand'], 'note': 'lo vemos cada día'})
        self.assertEqual(r.status, 200, r.json); self.assertEqual(r.json['fields'], ['current', 'visibility_max', 'visibility_min'], 'a centre: position, current, visibility, warnings')
        d = self.diver.post(f'/api/dive-points/{pid}/propose', {'bottom': ['sand', 'rock'], 'water_temps': {'summer': [24, 26]}, 'warnings': 'Mucho tráfico en agosto'})
        self.assertEqual(d.status, 200, d.json)
        self.assertEqual(self.diver.post(f'/api/dive-points/{pid}/propose', {'current': 'mild'}).status, 400, 'nothing changes')
        props = {p['id']: p for p in self.admin.get('/api/admin/dive-points/proposals').json['items'] if p['point_id'] == pid}
        pc, pd = props[r.json['id']], props[d.json['id']]
        self.assertEqual((pc['role'], pd['role']), ('center', 'diver'))
        self.assertEqual(pc['current']['current'], 'mild'); self.assertEqual(pc['changes']['current'], 'strong')
        self.assertEqual(self.admin.post('/api/admin/dive-points/proposals/review', {'id': pc['id'], 'decision': 'approve'}).status, 200)
        self.assertEqual(self.admin.post('/api/admin/dive-points/proposals/review', {'id': pd['id'], 'decision': 'reject'}).status, 200)
        it = self.client().get(f'/api/dive-points/{pid}').json['item']
        self.assertEqual((it['current'], it['visibility_min'], it['visibility_max']), ('strong', 15, 25)); self.assertNotIn('bottom', it)
        self.assertIn('centre', {s['kind'] for s in self.admin.get(f'/api/admin/dive-points/{pid}').json['sources']})
        # a position proposed by a diver, accepted: the site moves and is checked again (land or sea)
        lat, lon = sea_near(*[self.server.sql('SELECT latitude,longitude FROM dive_points WHERE id=?', (pid,))[0][k] for k in ('latitude', 'longitude')], 60)
        p = self.diver.post(f'/api/dive-points/{pid}/propose', {'latitude': lat, 'longitude': lon})
        self.assertEqual(p.status, 200, p.json)
        item = next(x for x in self.admin.get('/api/admin/dive-points/proposals').json['items'] if x['id'] == p.json['id'])
        self.assertLess(item['moved_m'], 120); self.assertIn(item['position']['status'], ('ok', 'warn'))
        self.assertEqual(self.admin.post('/api/admin/dive-points/proposals/review', {'id': p.json['id'], 'decision': 'approve'}).status, 200)
        self.assertAlmostEqual(self.server.sql('SELECT latitude FROM dive_points WHERE id=?', (pid,))[0]['latitude'], lat, 5)
        self.assertEqual(self.diver.get('/api/admin/dive-points/proposals').status, 403)

    def test_8_migration_and_existing_sites(self):
        self.assertTrue(self.server.sql("SELECT 1 FROM schema_migrations WHERE version='50.58-puntos'"))
        n = self.server.sql("SELECT COUNT(*) AS n FROM dive_points WHERE position_check IS NOT NULL")[0]['n']
        self.assertGreater(n, 250, 'every site with a position got its land-or-sea check')
        self.assertTrue(self.server.sql("SELECT 1 FROM dive_points WHERE access IS NOT NULL"), 'the access read from the old text where it says it clearly')

    def test_9_one_queue_counters_and_positions(self):
        # the old «position correction» (/suggest) arrives in the same queue as the proposals; «my corrections» lists it
        pid = self.new_point(name='Punto de la Cola Única', metres=12000).json['id']
        row = self.server.sql('SELECT latitude,longitude FROM dive_points WHERE id=?', (pid,))[0]
        lat, lon = sea_near(row['latitude'], row['longitude'], 80)
        r = self.diver.post(f'/api/dive-points/{pid}/suggest', {'latitude': lat, 'longitude': lon, 'note': 'GPS del barco', 'current': 'strong'})
        self.assertEqual(r.status, 200, r.json); self.assertEqual(r.json['fields'], ['latitude', 'longitude'], 'only the position travels by /suggest')
        mine = self.diver.get('/api/my/position-suggestions').json['items']
        self.assertTrue(any(m.get('dive_point_id') == pid and m['status'] == 'pending' for m in mine))
        n = self.admin.get('/api/admin/dive-points/summary').json
        self.assertGreaterEqual(n['proposals'], 1); self.assertIn('batch_items', n); self.assertIn('duplicates', n)
        self.assertEqual(self.diver.get('/api/admin/dive-points/summary').status, 403)
        # a published site on land is listed to be corrected by hand (the migration checked every site)
        land = self.admin.post('/api/dive-points', {'name': 'Punto Tierra Adentro', 'country': 'España', 'dive_type': 'Arrecife', 'latitude': 40.4168, 'longitude': -3.7038, 'force_position': True})
        self.assertEqual(land.status, 200, land.json)
        pos = self.admin.get('/api/admin/dive-points/positions').json
        self.assertIn(land.json['id'], [p['id'] for p in pos['items']])
        self.assertEqual(self.admin.post('/api/admin/dive-points/positions/recheck').status, 200)
        # only the administration keeps a site on land or creates a second one where one already exists
        cen = self.center.post('/api/dive-points', {'name': 'Otro en Madrid', 'country': 'España', 'dive_type': 'Arrecife', 'latitude': 40.42, 'longitude': -3.70, 'force_position': True})
        self.assertEqual(cen.status, 409, cen.json)
        # the year-round water temperature is edited with the rest of the site
        self.assertEqual(self.admin.post('/api/dive-points/update', {'id': pid, 'water_temp_min': 14, 'water_temp_max': 26}).status, 200)
        self.assertEqual(self.client().get(f'/api/dive-points/{pid}').json['item']['water_temp_max'], 26)
        self.assertEqual(self.admin.post('/api/dive-points/update', {'id': pid, 'water_temp_min': 30, 'water_temp_max': 20}).status, 400)

    # 10 -----------------------------------------------------------------------------------------------
    def test_10_open_data_batch(self):
        """scripts/puntos/preparar_lote.py: lo que dicen Wikidata y OpenStreetMap entra como lote, con sus fuentes.
        Los archivos son de ejemplo (nombres inventados): este equipo no llega a esos servicios."""
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'scripts' / 'puntos'))
        import preparar_lote as pl
        base = self.base
        zone = next((k for k, (_, box) in pl.ZONES.items() if pl.inside(box, base['latitude'], base['longitude'])), None)
        self.assertIsNotNone(zone, 'the base site is in one of the zones')
        far = sea_near(base['latitude'], base['longitude'], 7000); near = sea_near(base['latitude'], base['longitude'], 110)
        twin = sea_near(far[0], far[1], 60)
        osm = {'elements': [
            {'type': 'node', 'id': 101, 'lat': far[0], 'lon': far[1], 'tags': {'sport': 'scuba_diving', 'name': 'Bajo Inventado de Prueba'}},
            {'type': 'node', 'id': 102, 'lat': near[0], 'lon': near[1], 'tags': {'sport': 'scuba_diving', 'name': base['name']}},
            {'type': 'node', 'id': 103, 'lat': far[0], 'lon': far[1], 'tags': {'sport': 'scuba_diving'}},                 # sin nombre
            {'type': 'node', 'id': 104, 'lat': -33.9, 'lon': 151.3, 'tags': {'sport': 'scuba_diving', 'name': 'Fuera de la caja'}}]}
        wd = {'results': {'bindings': [
            {'item': {'value': 'http://www.wikidata.org/entity/Q999000001'}, 'itemLabel': {'value': 'El Bajón Inventado de Prueba'},
             'coord': {'value': f'Point({twin[1]} {twin[0]})'}, 'countryLabel': {'value': 'España'}},
            {'item': {'value': 'http://www.wikidata.org/entity/Q999000002'}, 'itemLabel': {'value': 'Q999000002'},     # sin nombre
             'coord': {'value': f'Point({far[1]} {far[0]})'}}]}}
        files = pl.convert(zone, osm, wd, today='2026-10-16')
        self.assertEqual(len(files), 1); lote = files[0]
        self.assertEqual(len(lote['items']), 2, lote['items'])
        both = next(i for i in lote['items'] if len(i['sources']) == 2)
        self.assertEqual({s['kind'] for s in both['sources']}, {'osm', 'wikidata'}, 'the same site in both sources goes once')
        self.assertEqual(both['country'], 'España', 'the country only when a source says it')
        other = next(i for i in lote['items'] if i is not both)
        self.assertNotIn('country', other, 'no country made up')
        for it in lote['items']:
            self.assertEqual(set(it) - {'country'}, {'name', 'latitude', 'longitude', 'sources'}, 'only what the source says')
        r = self.admin.post('/api/admin/dive-points/batches', lote)
        self.assertEqual(r.status, 200, r.json); bid = r.json['id']
        self.assertEqual((r.json['summary']['pending'], r.json['summary']['same']), (2, 1), r.json['summary'])
        self.assertNotIn('Bajón Inventado de Prueba', {x['name'] for x in self.client().get('/api/dive-points').json['items']})
        r = self.admin.post('/api/admin/dive-points/batches/publish', {'batch_id': bid})
        self.assertEqual(sorted(x['status'] for x in r.json['done']), ['merged', 'published'], r.json)
        new_id = next(x['point_id'] for x in r.json['done'] if x['status'] == 'published')
        kinds = {(s['kind'], s['license']) for s in self.admin.get(f'/api/admin/dive-points/{new_id}').json['sources']}
        self.assertEqual(kinds, {('osm', 'ODbL'), ('wikidata', 'CC0')})
        self.assertNotIn('openstreetmap.org', json.dumps(self.client().get(f'/api/dive-points/{new_id}').json), 'the sources stay private')
        self.assertEqual(self.client().get(f'/api/dive-points/{new_id}').json['item']['data_status'], 'pending')


if __name__ == '__main__':
    unittest.main()
