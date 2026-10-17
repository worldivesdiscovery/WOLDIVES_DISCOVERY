"""v50.53 · tareas 5 y 6 (revisión del titular, 14/10/2026): en la ficha del centro, «Puntos de buceo del centro» con
cada punto y su zona, y las reseñas de tres en tres (las 3 más recientes al entrar, «Ver más reseñas» trae 5 más sin
recargar), con la respuesta del centro debajo de su reseña.
"""
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ServerTestCase  # noqa: E402


class Ficha(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'ficha1')
        cls.cid = cls.center.user['center_id']
        divers = [t.make_diver(f'ficha{i}') for i in range(9)]
        for i, d in enumerate(divers):
            when = f'2026-09-{10 + i:02d}T10:00:00Z'
            reply = ('Gracias por venir. ' * 30) if i == 7 else None
            cls.server.sql('INSERT INTO center_reviews(center_id,user_id,rating,title,body,created_at,updated_at,reply_body,reply_at) VALUES(?,?,?,?,?,?,?,?,?)',
                           (cls.cid, d.user['id'], 3 + i % 3, f'Reseña {i}', f'Texto de la reseña {i}', when, when, reply, when if reply else None))

    def test_first_three_then_five_more(self):
        c = self.client()
        page = c.get(f'/api/centers/{self.cid}').json
        self.assertEqual([r['title'] for r in page['reviews']], ['Reseña 8', 'Reseña 7', 'Reseña 6'])   # most recent first
        more = c.get(f'/api/centers/{self.cid}/reviews?offset=3&limit=5').json
        self.assertEqual([r['title'] for r in more['items']], ['Reseña 5', 'Reseña 4', 'Reseña 3', 'Reseña 2', 'Reseña 1'])
        self.assertEqual((more['total'], more['has_more']), (9, True))
        last = c.get(f'/api/centers/{self.cid}/reviews?offset=8&limit=5').json
        self.assertEqual(([r['title'] for r in last['items']], last['has_more']), (['Reseña 0'], False))
        self.assertEqual(len(c.get(f'/api/centers/{self.cid}/reviews?offset=0&limit=500').json['items']), 9)   # at most 20 per page
        self.assertEqual(c.get(f'/api/centers/{self.cid}/reviews?offset=-4&limit=x').json['items'][0]['title'], 'Reseña 8')

    def test_the_reply_comes_with_its_review_and_no_personal_data(self):
        r = next(x for x in self.client().get(f'/api/centers/{self.cid}').json['reviews'] if x['title'] == 'Reseña 7')
        self.assertTrue(r['reply_body'].startswith('Gracias por venir.'))
        self.assertGreater(len(r['reply_body']), 220)                                     # long: the page folds it
        self.assertEqual(r['fullname'], 'Buceador')                                       # only the first name
        for k in ('user_id', 'email', 'reply_user_id'):
            self.assertNotIn(k, r)

    def test_reviews_of_a_centre_that_does_not_exist(self):
        self.assertEqual(self.client().get('/api/centers/999999/reviews').status, 404)
        self.assertEqual(self.client().get('/api/centers/abc/reviews').status, 404)

    def test_the_centre_dive_sites(self):
        pids = [r['id'] for r in self.server.sql("SELECT id FROM dive_points WHERE active=1 AND country='España' ORDER BY id LIMIT 2")]
        for pid in pids:
            self.assertEqual(self.center.post('/api/center-points/assign', {'dive_point_id': pid}).status, 200)
        pts = self.client().get(f'/api/centers/{self.cid}').json['points']
        self.assertEqual(sorted(p['id'] for p in pts), sorted(pids))
        for p in pts:
            self.assertTrue(p['name'] and p['country'])
            self.assertIn('zone', p)


if __name__ == '__main__':
    unittest.main()
