"""Encargo unificado del 17/10/2026 · Bloque 2: la vida marina de cada punto (servidor).

2.1/2.2  Importación del archivo de fuentes públicas: 529 citas, cada una con su punto (por nombre y municipio) y su
         especie (por nombre científico), las 124 especies nuevas numeradas desde la 151 («Sin foto», «Pendiente de
         traducción»), las genéricas guardadas sin salir, las dudosas y de orilla ocultas, las fuentes solo para el
         administrador; el mismo archivo otra vez no duplica nada; el CSV da lo mismo que el JSON.
2.3      La ficha pública: primero las citadas en el punto, después las de la zona; sin fuentes; «Mostrar especies sin
         foto»; «Ver todos los puntos donde se ve».
2.4      Administración: ocultar y mostrar, cambiar de zona a punto, ordenar, afinar una genérica, fotos «NNN_nombre».
2.5      Log Book: «¿Qué viste?», la colección del buceador, «Vista por buceadores recientemente» con 5 personas
         distintas, sin decir quién, y la especie nueva en un punto que pasa a revisión.
"""
from __future__ import annotations

import datetime as dt
import io
import json
from pathlib import Path

from helpers import ServerTestCase

ROOT = Path(__file__).resolve().parents[1]
DAY = lambda n: (dt.date.today() + dt.timedelta(days=n)).isoformat()


def tiny_jpeg():
    from PIL import Image
    b = io.BytesIO(); Image.new('RGB', (400, 300), (20, 90, 140)).save(b, 'JPEG'); return b.getvalue()


class VidaMarina(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.moraig = cls.server.sql("SELECT id FROM dive_points WHERE name LIKE 'El Moraig%' AND active=1")[0]['id']
        cls.cies = cls.server.sql("SELECT id FROM dive_points WHERE name LIKE 'Islas Cíes%' AND active=1")[0]['id']

    def page(self, pid, c=None):
        j = (c or self.client()).get(f'/api/dive-points/{pid}').json
        return {**j['item'], 'species': j['species']}

    def test_1_import_of_the_brief(self):
        st = json.loads(self.server.sql("SELECT notes FROM schema_migrations WHERE version='50.59-vida-marina'")[0]['notes'])
        self.assertEqual((st['citas'], st['genericas'], st['sin_punto'], st['ocultas'], st['especies_nuevas'], st['puntos']), (529, 152, 0, 164, 124, 11))
        nums = self.server.sql('SELECT MIN(catalog_no) a, MAX(catalog_no) b, COUNT(*) n FROM species WHERE catalog_no IS NOT NULL')[0]
        self.assertEqual((nums['a'], nums['b'], nums['n']), (151, 274, 124))
        new = self.server.sql("SELECT * FROM species WHERE catalog_no=151")[0]
        self.assertIsNone(new['photo_base']); self.assertEqual(new['needs_translation'], 1)
        groups = {r['scientific_name']: r['group_key'] for r in self.server.sql("SELECT scientific_name,group_key FROM species WHERE scientific_name IN "
                                                                                 "('Phallusia mammillata','Caretta caretta','Felimare villafranca','Thuridilla hopei')")}
        self.assertEqual(groups, {'Phallusia mammillata': 'tunicado', 'Caretta caretta': 'reptil', 'Felimare villafranca': 'nudibranquio', 'Thuridilla hopei': 'molusco'})
        # the doubtful ones (the noble pen shell in El Moraig) wait hidden with their reason
        nacra = self.server.sql("SELECT ps.visible, ps.hidden_reason FROM point_species ps JOIN species s ON s.id=ps.species_id WHERE s.scientific_name='Pinna nobilis' AND ps.dive_point_id=?", (self.moraig,))[0]
        self.assertEqual((nacra['visible'], nacra['hidden_reason']), (0, 'dudosa: revisar'))
        # again: nothing duplicated
        before = self.server.sql('SELECT (SELECT COUNT(*) FROM point_species) a, (SELECT COUNT(*) FROM species) b, (SELECT COUNT(*) FROM marine_citations) c')[0]
        r = self.admin.post('/api/admin/marina/importar', {'text': (ROOT / 'app/data/importar/vida-marina-puntos.csv').read_text(encoding='utf-8'), 'filename': 'vida-marina-puntos.csv'})
        self.assertEqual(r.status, 200, r.json); self.assertEqual(r.json['summary']['citas'], 529); self.assertEqual(r.json['summary']['especies_nuevas'], 0)
        after = self.server.sql('SELECT (SELECT COUNT(*) FROM point_species) a, (SELECT COUNT(*) FROM species) b, (SELECT COUNT(*) FROM marine_citations) c')[0]
        self.assertEqual(before, after)
        self.assertEqual(self.admin.post('/api/admin/marina/importar', {'text': '{"puntos": 3}'}).status, 400)
        diver = self.make_diver('vm59d')
        self.assertIn(diver.post('/api/admin/marina/importar', {'text': '{}'}).status, (403, 404))

    def test_2_public_page(self):
        sp = self.page(self.moraig)['species']
        self.assertTrue(sp)
        ev = [x['evidence'] for x in sp]
        self.assertEqual(ev, sorted(ev, key=lambda e: e != 'point'))   # first the ones at the site, then the area
        self.assertNotIn('Pinna nobilis', [x['scientific'] for x in sp])   # hidden
        self.assertTrue(all('sources' not in x for x in sp))               # the sources are only for the administrator
        self.assertNotIn('denia.net', json.dumps(self.page(self.server.sql("SELECT id FROM dive_points WHERE name LIKE 'La Barra (Les Marines)%'")[0]['id'])))
        self.assertNotIn('Rhodophyta', [x['scientific'] for x in self.page(self.server.sql("SELECT id FROM dive_points WHERE name LIKE 'La Barra (Les Marines)%'")[0]['id'])['species']])
        n = len(sp)
        self.assertEqual(self.admin.post('/api/admin/marina/ajustes', {'show_no_photo': 0}).status, 200)
        try: self.assertLess(len(self.page(self.moraig)['species']), n)   # only the ones with a photo
        finally: self.admin.post('/api/admin/marina/ajustes', {'show_no_photo': 1})
        sid = sp[0]['id']
        pts = self.client().get(f'/api/especies/{sid}/puntos').json['items']
        self.assertIn(self.moraig, [p['id'] for p in pts])

    def test_3_admin_edits(self):
        d = self.admin.get(f'/api/admin/marina/vida/punto/{self.moraig}').json
        hidden = [x for x in d['items'] if not x['visible']][0]
        self.assertTrue(hidden['sources'])                                   # the administrator sees them
        self.assertEqual(self.admin.post(f"/api/admin/marina/enlace/{hidden['link_id']}", {'visible': 1}).status, 200)
        self.assertIn(hidden['id'], [x['id'] for x in self.page(self.moraig)['species']])
        self.admin.post(f"/api/admin/marina/enlace/{hidden['link_id']}", {'visible': 0, 'hidden_reason': 'dudosa: revisar'})
        zone = [x for x in d['items'] if x['evidence'] == 'zone' and x['visible']][0]
        self.assertEqual(self.admin.post(f"/api/admin/marina/enlace/{zone['link_id']}", {'evidence': 'point', 'frequency_label': 'habitual', 'where_text': 'Grietas a 12 m'}).status, 200)
        first = self.page(self.moraig)['species']
        moved = [x for x in first if x['id'] == zone['id']][0]
        self.assertEqual((moved['evidence'], moved['frequency_label'], moved['where']), ('point', 'habitual', 'Grietas a 12 m'))
        ids = [x['link_id'] for x in d['items']][::-1]
        self.assertEqual(self.admin.post('/api/admin/marina/orden', {'point_id': self.moraig, 'ids': ids}).status, 200)
        self.assertEqual(self.admin.post('/api/admin/marina/orden', {'point_id': self.cies, 'ids': ids}).status, 404)
        # a generic citation («sargos»…) refined to a species of the catalogue: now it is public
        g = d['generic'][0]
        target = self.server.sql("SELECT id FROM species WHERE scientific_name='Diplodus sargus' AND active=1") or self.server.sql("SELECT id FROM species WHERE catalog_no=200")
        self.assertEqual(self.admin.post(f"/api/admin/marina/cita/{g['id']}", {'species_id': target[0]['id']}).status, 200)
        self.assertEqual(self.server.sql('SELECT state FROM marine_citations WHERE id=?', (g['id'],))[0]['state'], 'linked')
        ov = self.admin.get('/api/admin/marina/vida').json
        self.assertGreater(ov['photos_missing'], 100)
        self.assertGreaterEqual(ov['photos'][0]['points'], ov['photos'][-1]['points'])   # the most seen first

    def test_4_bulk_photo_by_name(self):
        sp = self.server.sql('SELECT id,catalog_no,scientific_name FROM species WHERE catalog_no=152')[0]
        slug = sp['scientific_name'].lower().replace(' ', '-')
        up = lambda name: self.admin.upload('/api/admin/marina/foto-lote', {'photo_author': 'Autora de prueba', 'photo_license': 'CC BY 4.0'}, name, tiny_jpeg())
        self.assertEqual(up(f'152_otra-especie.jpg').status, 400)                 # number and name do not agree: nothing changes
        self.assertEqual(up('sin-numero.jpg').status, 400)
        r = up(f'152_{slug}.jpg'); self.assertEqual(r.status, 200, r.json)
        self.assertTrue(self.server.sql('SELECT photo_base FROM species WHERE id=?', (sp['id'],))[0]['photo_base'])

    def test_5_logbook_sightings(self):
        target = [x for x in self.page(self.moraig)['species'] if x['evidence'] == 'point'][0]
        other = self.server.sql("SELECT id FROM species WHERE catalog_no=270")[0]['id']   # not at this site
        divers = [self.make_diver(f'vm59s{i}') for i in range(5)]
        for i, d in enumerate(divers):
            r = d.post('/api/diver/sightings', {'dive_no': 3, 'point_id': self.moraig, 'species_ids': [target['id'], other], 'dive_date': DAY(-10)})
            self.assertEqual(r.status, 200, r.json)
            if i < 4: self.assertFalse([x for x in self.page(self.moraig)['species'] if x['id'] == target['id']][0]['recent'])
        self.assertEqual(divers[0].get('/api/diver/sightings').json['total'], 2)
        sp = [x for x in self.page(self.moraig)['species'] if x['id'] == target['id']][0]
        self.assertTrue(sp['recent']); self.assertNotIn('vm59s', json.dumps(sp))   # never who
        sug = self.admin.get('/api/admin/marina/vida').json['suggestions']
        self.assertIn((self.moraig, other), [(x['point_id'], x['species_id']) for x in sug])
        self.assertEqual(divers[0].post('/api/diver/sightings', {'dive_no': 999, 'species_ids': []}).status, 400)
        self.assertEqual(divers[0].post('/api/diver/sightings', {'dive_no': 4, 'species_ids': [999999]}).status, 400)
        self.assertEqual(divers[0].post('/api/diver/sightings', {'dive_no': 4, 'species_ids': [], 'dive_date': DAY(5)}).status, 400)
        self.assertIn(self.client().post('/api/diver/sightings', {'dive_no': 3}).status, (401, 403))
