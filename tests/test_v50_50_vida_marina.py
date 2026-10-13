"""v50.50 · Vídeos de la ruta (enlaces) y vida marina de los puntos de buceo.

The video platforms and Wikimedia Commons are simulated (tests/media_mock.py): nothing leaves the machine.
"""
import io
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from helpers import ServerTestCase  # noqa: E402
from media_mock import MediaMock  # noqa: E402


def photo_bytes(w=1600, h=1067, color=(30, 90, 140), fmt='JPEG'):
    from PIL import Image
    im = Image.new('RGB', (w, h), color)
    for x in range(0, w, 40):
        for y in range(h):
            im.putpixel((x, y), (240, 200, 60))
    out = io.BytesIO(); im.save(out, fmt, quality=85)
    return out.getvalue()


TEXTS = '{"es":{"name":"Mero","blurb":"Pez grande y curioso de las rocas."},"en":{"name":"Dusky grouper","blurb":"A big, curious rock fish."},"fr":{"name":"Mérou brun"}}'


class Links(unittest.TestCase):
    """Which links are accepted, without any server (wod.videos.parse_link)."""

    def test_platforms(self):
        from wod import videos as v
        ok = {'https://www.youtube.com/watch?v=dQw4w9WgXcQ': ('youtube', True), 'https://youtu.be/dQw4w9WgXcQ?t=20': ('youtube', True),
              'https://www.youtube.com/shorts/dQw4w9WgXcQ': ('youtube', True), 'https://vimeo.com/76979871': ('vimeo', True),
              'https://www.dailymotion.com/video/x8abc12': ('dailymotion', True), 'https://www.tiktok.com/@buceo/video/7234567890123456789': ('tiktok', True),
              'https://www.facebook.com/watch/?v=1234567890': ('facebook', True), 'https://www.instagram.com/reel/Cxyz12345/': ('instagram', True),
              'https://www.twitch.tv/videos/123456789': ('twitch', False), 'https://videos.otra-plataforma.example/ver/1': ('otra', False)}
        for url, (key, ins) in ok.items():
            got = v.parse_link(url)
            self.assertEqual(got['platform'], key, url)
            self.assertEqual(v.insertable(key), ins, url)
        self.assertEqual(v.player_url('youtube', 'dQw4w9WgXcQ').split('?')[0], 'https://www.youtube-nocookie.com/embed/dQw4w9WgXcQ')
        bad = {'http://www.youtube.com/watch?v=dQw4w9WgXcQ': 'https://', 'https://bit.ly/abc': 'acortado', 'https://10.0.0.1/v': 'sospechoso',
               'https://a:b@youtube.com/watch?v=dQw4w9WgXcQ': 'sospechoso', 'https://www.youtube.com/@canal': 'no es de un vídeo',
               'https://www.instagram.com/p/Cxyz12345/': 'reel', 'https://cdn.example.com/ruta.mp4': 'no el archivo', 'javascript:alert(1)': 'https://',
               'https://example.com:8080/v': 'sospechoso', 'https://xn--youtbe-9ya.com/watch': 'sospechoso', 'https://example.com/setup.exe': 'no es de un vídeo', '': 'Pega'}
        for url, msg in bad.items():
            with self.assertRaises(v.LinkError, msg=url) as cm:
                v.parse_link(url)
            self.assertIn(msg, str(cm.exception), url)

    def test_safe_fetch(self):
        from wod import remoto
        for url in ('http://example.com/a', 'https://127.0.0.1/a', 'https://example.com:8443/a', 'https://u:p@example.com/a'):
            with self.assertRaises(remoto.FetchError, msg=url):
                remoto.check_url(url)
        self.assertFalse(remoto.public_host('localhost'))

    def test_months_and_licences(self):
        from wod import vidamarina as m
        self.assertEqual(m.months_list(m.months_mask([6, 7, 8, 9])), [6, 7, 8, 9])
        self.assertEqual(m.months_mask(range(1, 13)), 0)
        for good in ('CC BY-SA 4.0', 'CC0', 'Public domain', 'Propia', 'Cedida por el autor'):
            m.clean_license(good)
        for bad in ('CC BY-NC 4.0', 'CC BY-ND 2.0', 'All rights reserved', '', 'Copiada de Google'):
            with self.assertRaises(ValueError, msg=bad):
                m.clean_license(bad)


class VidaMarina(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock = MediaMock()
        cls.extra_env = {'WOD_MEDIA_FETCH_BASE': cls.mock.base}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'marina1')
        cls.pro = t.make_freelance(cls.admin, 'marina2')
        cls.diver = t.make_diver('marina3')
        pts = cls.admin.get('/api/dive-points').json['items']
        cls.pid, cls.pid2, cls.empty = pts[0]['id'], pts[1]['id'], pts[2]['id']

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.mock.stop()

    def species(self, sci='Epinephelus marginatus', texts=TEXTS, author='Ana Pruebas', lic='Propia'):
        r = self.admin.upload('/api/admin/marina/especie', {'scientific_name': sci, 'texts': texts, 'photo_author': author, 'photo_license': lic}, 'mero.jpg', photo_bytes())
        self.assertEqual(r.status, 200, r.json)
        return r.json['id']

    # ---------------------------------------------------------------------------------------------------- videos
    def test_01_preview_every_platform(self):
        cases = [('https://www.youtube.com/watch?v=Ab3dEf6hI9k', 'youtube', True, 'Ruta del pecio', 1280),
                 ('https://www.youtube.com/watch?v=Ab360Ef6hI9', 'youtube', True, 'Ruta 360°', 1280),
                 ('https://youtu.be/hB3dEf6hI9k', 'youtube', True, 'Ruta del pecio', 400),       # only hqdefault (480 wide, bands cut)
                 ('https://vimeo.com/76979871', 'vimeo', True, 'Inmersión en Vimeo', 1280),
                 ('https://www.dailymotion.com/video/x8abc12', 'dailymotion', True, 'Buceo nocturno', 1280),
                 ('https://www.tiktok.com/@buceo/video/7234567890123456789', 'tiktok', True, 'Tortuga', 400),
                 ('https://www.twitch.tv/videos/123456789', 'twitch', False, 'Directo desde el barco', 1280),
                 ('https://videos.otra-plataforma.example/ver/77', 'otra', False, 'Travesía por la cueva', 1280)]
        for url, key, ins, title, maxw in cases:
            r = self.admin.post('/api/marina/video/comprobar', {'url': url})
            self.assertEqual(r.status, 200, (url, r.json))
            d = r.json
            self.assertEqual((d['platform'], d['insertable']), (key, ins), url)
            self.assertIn(title, d['title'], url)
            self.assertTrue(d['thumb'] and d['thumb']['src'].startswith('/assets/uploads/videos/') and d['thumb']['src'].endswith('.webp'), (url, d))
            widths = [int(x.split()[-1][:-1]) for x in d['thumb']['srcset'].split(', ')]
            self.assertEqual(max(widths), maxw, url)
            img = self.client().get(d['thumb']['src'])
            self.assertEqual((img.status, img.headers.get('Content-Type')), (200, 'image/webp'), url)
            from PIL import Image
            im = Image.open(io.BytesIO(img.body))
            self.assertAlmostEqual(im.width / im.height, 16 / 9, delta=0.02, msg=url)
            if url.startswith('https://youtu.be/'):   # the black bands of hqdefault are cut away
                self.assertGreater(sum(im.getpixel((im.width // 2, 2))), 30)
        self.assertEqual(self.admin.post('/api/marina/video/comprobar', {'url': 'https://www.youtube.com/watch?v=Ab3dEf6hI9k'}).status, 200)
        self.assertEqual(len(self.mock.asked('i.ytimg.com/vi/Ab3dEf6hI9k/maxresdefault')), 1, 'the preview is downloaded once')

    def test_02_fallback_and_invalid(self):
        r = self.admin.post('/api/marina/video/comprobar', {'url': 'https://www.youtube.com/watch?v=NOTHUMB0001'})
        self.assertEqual(r.status, 200); self.assertIsNone(r.json['thumb'])
        r = self.admin.post('/api/marina/video/comprobar', {'url': 'https://www.facebook.com/watch/?v=1234567890'})
        self.assertEqual(r.status, 200); self.assertIsNone(r.json['thumb']); self.assertTrue(r.json['insertable'])
        for url, msg in (('https://blog.example.com/post', 'no es de un vídeo'), ('http://vimeo.com/76979871', 'https://'), ('https://bit.ly/x', 'acortado'),
                         ('https://www.youtube.com/@canal', 'no es de un vídeo'), ('https://desconocida.example/v', 'No hemos podido abrir')):
            r = self.admin.post('/api/marina/video/comprobar', {'url': url})
            self.assertEqual(r.status, 400, url); self.assertIn(msg, r.json['error'], url)

    def test_03_permissions_and_approval(self):
        url = 'https://www.youtube.com/watch?v=Pe3dEf6hI9k'
        r = self.diver.post('/api/marina/video', {'point_id': self.pid, 'url': url})
        self.assertEqual(r.status, 403); self.assertIn('buceadores', r.json['error'])
        self.assertEqual(self.diver.post('/api/marina/video/comprobar', {'url': url}).status, 403)
        r = self.center.post('/api/marina/video', {'point_id': self.pid, 'url': url, 'kind': '360', 'title': 'Pared de las gorgonias'})
        self.assertEqual((r.status, r.json['status']), (200, 'pending'), r.json)
        vid = r.json['id']
        public = self.client().get(f'/api/dive-points/{self.pid}').json
        self.assertNotIn(vid, [v['id'] for v in public['videos']], 'pending videos are not public')
        mine = self.center.get('/api/marina/mias').json['items']
        self.assertEqual([(x['type'], x['status']) for x in mine if x['id'] == vid], [('video', 'pending')])
        self.assertEqual(self.pro.post(f'/api/marina/video/{vid}', {'title': 'x'}).status, 403, 'another provider cannot change it')
        self.assertEqual(self.pro.post(f'/api/marina/video/{vid}/retirar').status, 403)
        q = self.admin.get('/api/admin/marina/pendientes').json
        self.assertIn(vid, [v['id'] for v in q['videos']]); self.assertGreaterEqual(q['count'], 1)
        r = self.admin.post('/api/admin/marina/revisar', {'type': 'video', 'id': vid, 'decision': 'reject'})
        self.assertEqual(r.status, 400, 'a rejection needs a reason')
        self.assertEqual(self.admin.post('/api/admin/marina/revisar', {'type': 'video', 'id': vid, 'decision': 'approve'}).status, 200)
        v = [x for x in self.client().get(f'/api/dive-points/{self.pid}').json['videos'] if x['id'] == vid][0]
        self.assertEqual((v['kind'], v['title'], v['contributor'], v['platform']), ('360', 'Pared de las gorgonias', 'Centro marina1', 'youtube'))
        self.assertTrue(v['player'].startswith('https://www.youtube-nocookie.com/embed/Pe3dEf6hI9k'))
        self.assertEqual(self.center.post(f'/api/marina/video/{vid}', {'title': 'otro'}).status, 403, 'reviewed: no more changes')
        # Freelance: proposal rejected with a reason, which it sees.
        r = self.pro.post('/api/marina/video', {'point_id': self.pid, 'url': 'https://vimeo.com/76979871'})
        self.assertEqual(r.json['status'], 'pending')
        self.assertEqual(self.admin.post('/api/admin/marina/revisar', {'type': 'video', 'id': r.json['id'], 'decision': 'reject', 'note': 'No se ve el punto'}).status, 200)
        mine = self.pro.get('/api/marina/mias').json['items']
        self.assertEqual([(x['status'], x['note']) for x in mine if x['id'] == r.json['id']], [('rejected', 'No se ve el punto')])
        # Administrator: published at once; the same link twice is refused.
        r = self.admin.post('/api/marina/video', {'point_id': self.pid, 'url': 'https://www.dailymotion.com/video/x8abc12'})
        self.assertEqual(r.json['status'], 'approved')
        r = self.admin.post('/api/marina/video', {'point_id': self.pid, 'url': 'https://dai.ly/x8abc12'})
        self.assertEqual(r.status, 400); self.assertIn('ya está', r.json['error'])

    def test_04_team_profile_needs_ficha(self):
        """A team member whose profile has no «Ficha del centro y ajustes» cannot propose."""
        from wod import roles
        self.assertEqual(roles.necesita('/api/marina/video', 'POST'), 'centro')
        self.assertEqual(roles.necesita('/api/marina/mias', 'GET'), '')

    def test_05_old_uploads_closed(self):
        r = self.admin.upload(f'/api/dive-points/{self.pid}/virtual/upload', {'title': 'v', 'experience_type': 'video360'}, 'v.mp4', b'\x00\x00\x00\x18ftypmp42' + b'0' * 100)
        self.assertEqual(r.status, 410); self.assertIn('enlace', r.json['error'])
        self.assertEqual(self.admin.post(f'/api/dive-points/{self.pid}/virtual', {'title': 't', 'experience_type': 'video360', 'url': 'https://www.youtube-nocookie.com/embed/abc'}).status, 410)

    def test_06_csp_and_order(self):
        csp = self.client().get('/').headers.get('Content-Security-Policy', '')
        frames = [x for x in csp.split(';') if 'frame-src' in x][0]
        for host in ('www.youtube-nocookie.com', 'player.vimeo.com', 'www.dailymotion.com', 'www.tiktok.com'):
            self.assertIn('https://' + host, frames)
        self.assertNotIn('twitch', frames); self.assertNotIn('www.youtube.com ', frames + ' ')
        a = self.admin.post('/api/marina/video', {'point_id': self.pid2, 'url': 'https://www.youtube.com/watch?v=Or1dEf6hI9k'}).json['id']
        b = self.admin.post('/api/marina/video', {'point_id': self.pid2, 'url': 'https://www.youtube.com/watch?v=Or2dEf6hI9k'}).json['id']
        self.assertEqual([v['id'] for v in self.client().get(f'/api/dive-points/{self.pid2}').json['videos']], [a, b])
        self.assertEqual(self.admin.post(f'/api/marina/video/{b}', {'move': 'up'}).status, 200)
        self.assertEqual([v['id'] for v in self.client().get(f'/api/dive-points/{self.pid2}').json['videos']], [b, a])

    # --------------------------------------------------------------------------------------------------- species
    def test_10_catalogue(self):
        self.assertEqual(self.center.upload('/api/admin/marina/especie', {'scientific_name': 'Octopus vulgaris', 'texts': TEXTS}, 'p.jpg', photo_bytes()).status, 403)
        r = self.admin.upload('/api/admin/marina/especie', {'scientific_name': 'Octopus vulgaris', 'texts': TEXTS, 'photo_author': 'X', 'photo_license': 'CC BY-NC 4.0'}, 'p.jpg', photo_bytes())
        self.assertEqual(r.status, 400); self.assertIn('no permite', r.json['error'])
        r = self.admin.upload('/api/admin/marina/especie', {'scientific_name': 'Octopus vulgaris', 'texts': TEXTS, 'photo_author': '', 'photo_license': 'Propia'}, 'p.jpg', photo_bytes())
        self.assertEqual(r.status, 400); self.assertIn('autor', r.json['error'])
        r = self.admin.upload('/api/admin/marina/especie', {'scientific_name': 'Octopus vulgaris', 'texts': TEXTS, 'photo_author': 'A', 'photo_license': 'Propia'}, 'p.svg', b'<svg onload=alert(1)>')
        self.assertEqual(r.status, 400)
        sid = self.species('Octopus vulgaris', '{"es":{"name":"Pulpo común"},"en":{"name":"Common octopus"},"de":{"name":"Gemeiner Krake"}}')
        item = self.admin.get(f'/api/admin/marina/especie/{sid}').json['item']
        self.assertEqual(sorted(item['texts']), ['de', 'en', 'es'])
        self.assertEqual(item['photo']['srcset'].count('.webp'), 3, item['photo'])
        img = self.client().get(item['photo']['src'])
        from PIL import Image
        im = Image.open(io.BytesIO(img.body)); self.assertEqual(im.format, 'WEBP'); self.assertNotIn('exif', im.info)
        # Search in any language (accents and case do not matter) and by scientific name.
        for q in ('krake', 'PULPO comun', 'octopus vulg', 'common'):
            names = [x['scientific'] for x in self.center.get('/api/marina/especies?q=' + q.replace(' ', '%20')).json['items']]
            self.assertIn('Octopus vulgaris', names, q)
        self.assertEqual(self.diver.get('/api/marina/especies?q=pulpo').status, 403)
        r = self.admin.upload('/api/admin/marina/especie', {'scientific_name': 'octopus Vulgaris', 'texts': TEXTS, 'photo_author': 'A', 'photo_license': 'Propia'}, 'p.jpg', photo_bytes())
        self.assertEqual(r.status, 400); self.assertIn('Ya hay', r.json['error'])

    def test_11_links_seasons_languages(self):
        sid = self.species('Caretta caretta', '{"es":{"name":"Tortuga boba","blurb":"Pasa por la zona en verano."},"en":{"name":"Loggerhead turtle"},"zh":{"name":"红海龟"}}')
        r = self.center.post('/api/marina/especie-punto', {'point_id': self.pid, 'species_id': sid, 'frequency': 'rare', 'months': [6, 7, 8, 9]})
        self.assertEqual((r.status, r.json['status']), (200, 'pending'))
        lid = r.json['id']
        self.assertEqual(self.diver.post('/api/marina/especie-punto', {'point_id': self.pid, 'species_id': sid}).status, 403)
        r = self.pro.post('/api/marina/especie-punto', {'point_id': self.pid, 'species_id': sid})
        self.assertEqual(r.status, 400); self.assertIn('ya está propuesta', r.json['error'])
        self.assertEqual(self.center.post(f'/api/marina/especie-punto/{lid}', {'frequency': 'occasional'}).status, 200, 'own proposal may change while pending')
        self.assertEqual(self.admin.post('/api/admin/marina/revisar', {'type': 'especie', 'id': lid, 'decision': 'approve'}).status, 200)
        for lang, name in (('es', 'Tortuga boba'), ('en', 'Loggerhead turtle'), ('zh', '红海龟'), ('fr', 'Loggerhead turtle'), ('pl', 'Loggerhead turtle')):
            sp = [s for s in self.client().get(f'/api/dive-points/{self.pid}?lang={lang}').json['species'] if s['id'] == sid][0]
            self.assertEqual(sp['name'], name, lang)
        self.assertEqual((sp['frequency'], sp['months'], sp['scientific']), ('occasional', [6, 7, 8, 9], 'Caretta caretta'))
        self.assertTrue(sp['credit']['author'] and sp['credit']['license'])
        self.assertNotIn('contributor_provider', sp); self.assertNotIn('status', sp)

    def test_12_thirty_species_one_request(self):
        ids = [self.species(f'Pruebaspecies alfa{chr(97 + i % 26)}{chr(97 + i // 26)}', '{"es":{"name":"Especie %02d"}}' % i) for i in range(30)]
        for i, sid in enumerate(ids):
            r = self.admin.post('/api/marina/especie-punto', {'point_id': self.pid2, 'species_id': sid, 'frequency': ('common', 'occasional', 'rare')[i % 3],
                                                             'months': [] if i % 4 else [1, 2]})
            self.assertEqual(r.json['status'], 'approved')
        d = self.client().get(f'/api/dive-points/{self.pid2}').json
        self.assertEqual(len(d['species']), 30)
        self.assertEqual([s['frequency'] for s in d['species']][:10], ['common'] * 10, 'habitual first')

    def test_13_empty_site(self):
        d = self.client().get(f'/api/dive-points/{self.empty}').json
        self.assertEqual((d['species'], d['videos']), ([], []))

    def test_14_commons(self):
        sid = self.species('Sciaena umbra', '{"es":{"name":"Corvallo"}}')
        items = self.admin.get('/api/admin/marina/commons?q=Epinephelus%20marginatus').json['items']
        state = {x['title']: (x['ok'], x['license']) for x in items}
        self.assertEqual(state['File:Mero de pruebas.jpg'], (True, 'CC BY-SA 4.0'))
        self.assertFalse(state['File:Mero no comercial.jpg'][0]); self.assertFalse(state['File:Mero sin autor.jpg'][0])
        self.assertEqual(self.admin.post(f'/api/admin/marina/especie/{sid}/commons', {'title': 'File:Mero no comercial.jpg'}).status, 400)
        r = self.admin.post(f'/api/admin/marina/especie/{sid}/commons', {'title': 'File:Mero de pruebas.jpg'})
        self.assertEqual(r.status, 200, r.json)
        c = r.json['item']['credit']
        self.assertEqual((c['author'], c['license']), ('Ana Pruebas', 'CC BY-SA 4.0'))
        self.assertTrue(c['source'].startswith('https://commons.wikimedia.org/wiki/'))
        self.assertEqual(self.center.get('/api/admin/marina/commons?q=mero').status, 403)

    def test_15_examples(self):
        n = self.admin.get('/api/admin/marina/especies').json['examples_missing']
        self.assertGreaterEqual(n, 12)
        r = self.admin.post('/api/admin/marina/ejemplos')
        self.assertEqual(r.json['added'], n)
        self.assertEqual(self.admin.post('/api/admin/marina/ejemplos').json['added'], 0, 'never twice')
        items = self.admin.get('/api/admin/marina/especies?lang=de').json['items']
        ex = [x for x in items if x['example']]
        self.assertEqual(len(ex), n)
        self.assertTrue(all(len(x['langs']) == 9 and x['credit']['license'] == 'Ilustración propia' for x in ex), [(x['scientific'], x['langs']) for x in ex if len(x['langs']) != 9])


class Migration(ServerTestCase):
    """The YouTube and Vimeo videos of the old «recorridos virtuales» become route videos; nothing is deleted."""

    @classmethod
    def setUpClass(cls):
        import shutil, sqlite3, tempfile
        from helpers import SEED_DB
        tmp = Path(tempfile.mkdtemp(prefix='wod-mig-')) / 'seed.sqlite3'; shutil.copy(SEED_DB, tmp)
        db = sqlite3.connect(tmp)
        have = {r[0] for r in db.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if 'route_videos' in have: db.execute('DROP TABLE route_videos')
        if 'schema_migrations' in have: db.execute("DELETE FROM schema_migrations WHERE version='50.50'")
        pid = db.execute('SELECT id FROM dive_points WHERE active=1 ORDER BY id LIMIT 1').fetchone()[0]
        rows = [(pid, 'Ruta 360', 'video360', 'https://www.youtube-nocookie.com/embed/Mg1dEf6hI9k'), (pid, 'Vimeo', 'external360', 'https://player.vimeo.com/video/76979871'),
                (pid, 'Street View', 'streetview', 'https://www.google.com/maps/@38.1,-0.4,3a'), (pid, 'Panorámica', 'panorama', None)]
        for p_, t, k, u in rows:
            db.execute("INSERT INTO virtual_experiences(dive_point_id,title,experience_type,url,active,created_at,updated_at) VALUES(?,?,?,?,1,'2026-01-01','2026-01-01')", (p_, t, k, u))
        db.commit(); db.close()
        cls.pid = pid
        from helpers import Server
        cls.server = Server(seed=tmp).start()

    def test_migrated(self):
        d = self.client().get(f'/api/dive-points/{self.pid}').json
        got = sorted((v['platform'], v['kind']) for v in d['videos'])
        self.assertEqual(got, [('vimeo', '360'), ('youtube', '360')])
        n = self.server.sql('SELECT COUNT(*) AS n FROM virtual_experiences WHERE active=1')
        self.assertGreaterEqual(n[0]['n'] if isinstance(n, list) else n, 4)


if __name__ == '__main__':
    unittest.main()
