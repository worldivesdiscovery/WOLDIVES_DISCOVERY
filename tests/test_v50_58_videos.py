"""v50.58 · encargo del 16/10/2026: vídeos de los puntos de buceo más visibles y aportados por los usuarios.

Las comprobaciones del encargo en el servidor (las plataformas están simuladas en tests/media_mock.py: nada sale fuera):
1. Un buceador sin el correo confirmado o sin los datos obligatorios del perfil sabe qué le falta; con todo completo,
   un enlace válido queda en Pendientes y se publica al aprobarlo (y se le avisa en la web y por correo).
2. Un enlace de otra web se rechaza; solo YouTube (también Shorts), Instagram (publicaciones y Reels) y TikTok.
3. Un vídeo repetido en el punto se avisa (también un Short ya enviado como vídeo normal); 5 vídeos cada 24 horas.
4. Un vídeo borrado, privado o sin permiso de inserción se explica al enviarlo; uno publicado que desaparece queda
   marcado «no disponible» para la administración cuando la web no puede cargar su imagen.
5. Denunciar un vídeo lo lleva a Denunciados; «Retirar» lo quita de la ficha y avisa a las dos partes.
6. La administración: aprobar varios a la vez, rechazar con motivo opcional, editar el título, destacado primero,
   orden arrastrando, sus vídeos se publican directamente.
7. La miniatura es la de la plataforma (nada descargado en nuestro servidor) y la web pública no sabe quién envió el vídeo.
"""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from helpers import ServerTestCase  # noqa: E402
from media_mock import MediaMock  # noqa: E402

YT = 'https://www.youtube.com/watch?v='


class Unidades(unittest.TestCase):
    def test_platforms_and_orientation(self):
        from wod import videos as v
        self.assertEqual(v.USER_PLATFORMS, ('youtube', 'instagram', 'tiktok'))
        self.assertTrue(v.is_vertical('youtube', 'https://www.youtube.com/shorts/dQw4w9WgXcQ'))
        self.assertFalse(v.is_vertical('youtube', YT + 'dQw4w9WgXcQ'))
        self.assertTrue(v.is_vertical('youtube', YT + 'dQw4w9WgXcQ', {'width': 113, 'height': 200}))
        self.assertTrue(v.is_vertical('tiktok', '') and v.is_vertical('instagram', ''))
        self.assertEqual(v.parse_link('https://www.instagram.com/p/Cxyz12345/')['url'], 'https://www.instagram.com/p/Cxyz12345/')
        self.assertEqual(v.thumb_urls('youtube', 'dQw4w9WgXcQ'), {'src': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/maxresdefault.jpg',
                                                                   'fallback': 'https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg'})
        self.assertIsNone(v.thumb_urls('instagram', 'reel/x', None))
        legacy = v.public_row({'id': 1, 'url': YT + 'dQw4w9WgXcQ', 'platform': 'youtube', 'video_ref': 'dQw4w9WgXcQ', 'thumb_base': '/assets/uploads/videos/x',
                               'thumb_widths': '400', 'contributor_name': 'Laura', 'kind': 'normal'})
        self.assertTrue(legacy['thumb']['src'].startswith('https://i.ytimg.com/'), 'a video added before v50.58 shows the platform image')
        self.assertNotIn('contributor', legacy)

    def test_instagram_needs_meta_key(self):
        from wod import videos as v
        mock = MediaMock()
        old = {k: os.environ.get(k) for k in ('WOD_MEDIA_FETCH_BASE', 'WOD_META_OEMBED_TOKEN')}
        try:
            os.environ['WOD_MEDIA_FETCH_BASE'] = mock.base; os.environ.pop('WOD_META_OEMBED_TOKEN', None)
            link = v.parse_link('https://www.instagram.com/reel/Cxyz12345/')
            self.assertEqual(v.verify(link)['state'], 'no_key', 'without the key nothing is asked to Meta')
            self.assertFalse(mock.asked('graph.facebook.com'))
            os.environ['WOD_META_OEMBED_TOKEN'] = '123|abc'
            got = v.verify(link)
            self.assertEqual(got['state'], 'ok'); self.assertTrue(got['data']['thumbnail_url'].startswith('https://scontent.'))
            info = v.inspect('https://www.instagram.com/reel/Cxyz12345/', fresh=True)
            self.assertEqual(info['thumb']['src'], 'https://scontent.cdninstagram.com/v/prueba.jpg'); self.assertTrue(info['vertical'])
        finally:
            for k, val in old.items():
                if val is None: os.environ.pop(k, None)
                else: os.environ[k] = val
            mock.stop()


class Videos(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.mock = MediaMock()
        cls.extra_env = {'WOD_MEDIA_FETCH_BASE': cls.mock.base, 'WOD_VIDEO_CHECKS': '0'}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.diver = t.make_diver('videos1')
        cls.other = t.make_diver('videos2')
        cls.center = t.make_center(cls.admin, 'videos3')
        pts = cls.admin.get('/api/dive-points').json['items']
        cls.pid, cls.pid2, cls.pid3 = pts[3]['id'], pts[4]['id'], pts[5]['id']

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.mock.stop()

    def complete(self, client):
        """A diver with the email confirmed and the mandatory data of the profile."""
        self.server.sql("UPDATE users SET email_verified_at=datetime('now') WHERE id=?", (client.user['id'],))
        cert = self.server.sql('SELECT id FROM certifications ORDER BY id LIMIT 1')[0]['id']
        r = client.post('/api/account/profile', {'country': 'España', 'city': 'Valencia', 'certification_id': cert, 'preferred_language': 'es'})
        self.assertEqual(r.status, 200, r.json)

    def add(self, client, url, pid=None, **kw):
        return client.post(f'/api/dive-points/{pid or self.pid}/videos', {'url': url, 'confirm': True, **kw})

    # 1 -------------------------------------------------------------------------------------------------------------
    def test_1_diver_profile_pending_and_published(self):
        anon = self.client().get('/api/videos/puedo').json
        self.assertFalse(anon['logged'])
        miss = self.diver.get('/api/videos/puedo').json
        self.assertEqual({m['key'] for m in miss['missing']}, {'email', 'country', 'cert'}, miss)
        r = self.add(self.diver, YT + 'Dv1dEf6hI9k')
        self.assertEqual(r.status, 403); self.assertIn('correo', r.json['error']); self.assertIn('país', r.json['error'])
        self.complete(self.diver)
        self.assertEqual(self.diver.get('/api/videos/puedo').json['missing'], [])
        r = self.diver.post(f'/api/dive-points/{self.pid}/videos', {'url': YT + 'Dv1dEf6hI9k'})
        self.assertEqual(r.status, 400); self.assertIn('Confirma', r.json['error'], 'the checkbox is required')
        r = self.add(self.diver, YT + 'Dv1dEf6hI9k', title='Entrada por la pared')
        self.assertEqual((r.status, r.json['status']), (200, 'pending'), r.json)
        self.assertEqual(r.json['message'], 'Gracias. Lo revisaremos antes de publicarlo.')
        vid = r.json['id']
        self.assertNotIn(vid, [v['id'] for v in self.client().get(f'/api/dive-points/{self.pid}').json['videos']], 'pending is not public')
        pend = self.admin.get('/api/admin/videos?tab=pending').json
        item = next(x for x in pend['items'] if x['id'] == vid)
        self.assertEqual((item['contributor_kind'], item['point_id'], item['platform']), ('diver', self.pid, 'youtube'))
        self.assertTrue(item['contributor'].startswith('Buceador videos1')); self.assertGreaterEqual(pend['counts']['pending'], 1)
        r = self.admin.post('/api/admin/videos/approve', {'ids': [vid]})
        self.assertEqual((r.status, r.json['approved']), (200, 1))
        pub = next(v for v in self.client().get(f'/api/dive-points/{self.pid}').json['videos'] if v['id'] == vid)
        self.assertEqual(pub['title'], 'Entrada por la pared')
        self.assertTrue(pub['player'].startswith('https://www.youtube-nocookie.com/embed/Dv1dEf6hI9k'))
        self.assertEqual(pub['thumb']['src'], 'https://i.ytimg.com/vi/Dv1dEf6hI9k/maxresdefault.jpg')
        for k in ('contributor', 'email', 'contributor_kind'): self.assertNotIn(k, pub, 'who sent it is not public')
        # the person is told: «Avisos» inside the web and an email
        msgs = self.server.sql("SELECT subject FROM messages WHERE recipient_user_id=? AND kind='system'", (self.diver.user['id'],))
        self.assertTrue(any('ya está publicado' in m['subject'] for m in msgs), msgs)
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='video_approved' AND to_email=?", ('videos1@diver.example.org',)))
        self.assertFalse(self.mock.asked('i.ytimg.com'), 'nothing is downloaded: the image stays on the platform')

    # 2 -------------------------------------------------------------------------------------------------------------
    def test_2_only_three_platforms(self):
        self.complete(self.other)
        for url in ('https://vimeo.com/76979871', 'https://www.dailymotion.com/video/x8abc12', 'https://blog.example.com/post', 'https://videos.otra-plataforma.example/ver/77'):
            r = self.add(self.other, url, pid=self.pid2)
            self.assertEqual(r.status, 400, url); self.assertIn('Solo se admiten', r.json['error'], url)
        self.assertFalse(self.mock.asked('blog.example.com'), 'another website is refused before asking it anything')
        for url in ('https://www.youtube.com/shorts/SHo3tEf6hI9', 'https://www.tiktok.com/@buceo/video/7234567890123456789', 'https://www.instagram.com/reel/Cxyz12345/'):
            r = self.add(self.other, url, pid=self.pid2)
            self.assertEqual((r.status, r.json.get('status')), (200, 'pending'), (url, r.json))
        rows = {r['platform']: r for r in self.server.sql('SELECT platform,vertical,verified_state,thumb_url FROM route_videos WHERE dive_point_id=?', (self.pid2,))}
        self.assertEqual(rows['youtube']['vertical'], 1, 'a Short is portrait'); self.assertEqual(rows['tiktok']['vertical'], 1)
        self.assertEqual(rows['instagram']['verified_state'], 'no_key', 'Instagram without the Meta key: accepted unchecked, the administration decides')
        self.assertTrue(rows['tiktok']['thumb_url'].startswith('https://'), "TikTok's official preview (oEmbed)")

    # 3 -------------------------------------------------------------------------------------------------------------
    def test_3_repeated_and_daily_limit(self):
        self.complete(self.other)
        self.assertEqual(self.add(self.other, YT + 'Rp1dEf6hI9k', pid=self.pid3).status, 200)
        r = self.add(self.other, 'https://youtu.be/Rp1dEf6hI9k', pid=self.pid3)
        self.assertEqual(r.status, 400); self.assertIn('ya está enviado', r.json['error'])
        r = self.add(self.other, 'https://www.youtube.com/shorts/Rp1dEf6hI9k', pid=self.pid3)
        self.assertEqual(r.status, 400, 'the same video as a Short')
        a = self.admin.post(f'/api/dive-points/{self.pid3}/videos', {'url': YT + 'Ad1dEf6hI9k'})
        self.assertEqual((a.status, a.json['status']), (200, 'approved'), 'the administration publishes directly')
        r = self.add(self.other, YT + 'Ad1dEf6hI9k', pid=self.pid3)
        self.assertEqual(r.status, 400); self.assertIn('ya está en este punto', r.json['error'])
        left = self.other.get('/api/videos/puedo').json['left']
        for i in range(left):
            self.assertEqual(self.add(self.other, YT + f'Lm{i}dEf6hI9k', pid=self.pid3).status, 200)
        r = self.add(self.other, YT + 'LmXdEf6hI9k', pid=self.pid3)
        self.assertEqual(r.status, 400); self.assertIn('límite de 5', r.json['error'])

    # 4 -------------------------------------------------------------------------------------------------------------
    def test_4_unavailable(self):
        for vid, msg in (('GONEdEf6hI9', 'no existe o se ha borrado'), ('PRIVdEf6hI9', 'privado'), ('NOEMBEf6hI9', 'no permite')):
            r = self.admin.post(f'/api/dive-points/{self.pid}/videos', {'url': YT + vid})
            self.assertEqual(r.status, 400, vid); self.assertIn(msg, r.json['error'], vid)
        r = self.admin.post(f'/api/dive-points/{self.pid}/videos', {'url': 'https://www.tiktok.com/@buceo/video/4040000000000000000'})
        self.assertEqual(r.status, 400); self.assertIn('se ha borrado', r.json['error'])
        # a published video deleted later on the platform: the page cannot load its image and says so; the server asks the
        # platform itself and marks it for the administration
        ok = self.admin.post(f'/api/dive-points/{self.pid}/videos', {'url': YT + 'Ok4dEf6hI9k'}).json['id']
        self.server.sql("UPDATE route_videos SET url=?, video_ref='GONEdEf6hI9' WHERE id=?", (YT + 'GONEdEf6hI9', ok))
        r = self.client().post(f'/api/videos/{ok}/no-disponible')
        self.assertEqual((r.status, r.json['unavailable']), (200, True))
        pub = next(v for v in self.client().get(f'/api/dive-points/{self.pid}').json['videos'] if v['id'] == ok)
        self.assertTrue(pub['unavailable'])
        item = next(x for x in self.admin.get('/api/admin/videos?tab=published').json['items'] if x['id'] == ok)
        self.assertIn('se ha borrado', item['unavailable_reason'])
        self.assertGreaterEqual(self.admin.get('/api/admin/videos/summary').json['unavailable'], 1)
        asked = len(self.mock.asked('GONEdEf6hI9'))
        self.client().post(f'/api/videos/{ok}/no-disponible')
        self.assertEqual(len(self.mock.asked('GONEdEf6hI9')), asked, 'the platform is asked at most once an hour per video')

    # 5 -------------------------------------------------------------------------------------------------------------
    def test_5_report_and_take_down(self):
        self.complete(self.diver)
        vid = self.add(self.diver, YT + 'Dn5dEf6hI9k', pid=self.pid2).json['id']
        self.admin.post('/api/admin/videos/approve', {'ids': [vid]})
        base = {'target_type': 'video', 'target_id': vid, 'name': 'Autora Real', 'email': 'autora@ejemplo.org', 'good_faith': True}
        self.assertEqual(self.client().post('/api/reports', {**base, 'reason': 'not_mine'}).status, 200, 'the reason says enough: no details needed')
        self.assertEqual(self.client().post('/api/reports', {**base, 'target_type': 'point', 'target_id': self.pid2, 'reason': 'not_mine', 'details': 'x' * 30}).status, 400,
                         'the video reasons are only for videos')
        rep = self.admin.get('/api/admin/videos?tab=reported').json
        item = next(x for x in rep['items'] if x['id'] == vid)
        self.assertEqual(item['reports'][0]['reason_label'], 'Es mío y no di permiso'); self.assertGreaterEqual(rep['counts']['reported'], 1)
        self.assertEqual(self.admin.post('/api/admin/videos/remove', {'id': vid, 'reason': 'Retirado a petición de su autor.'}).status, 200)
        self.assertNotIn(vid, [v['id'] for v in self.client().get(f'/api/dive-points/{self.pid2}').json['videos']])
        self.assertFalse([x for x in self.admin.get('/api/admin/videos?tab=reported').json['items'] if x['id'] == vid])
        self.assertTrue(self.server.sql("SELECT 1 FROM content_reports WHERE target_type='video' AND target_id=? AND status='actioned'", (vid,)))
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='report_resolved' AND to_email='autora@ejemplo.org'"))
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='report_decision_affected' AND to_email='videos1@diver.example.org'"))
        # «Mantener»: the report is dismissed and the video stays
        keep = self.admin.post(f'/api/dive-points/{self.pid2}/videos', {'url': YT + 'Kp5dEf6hI9k'}).json['id']
        self.client().post('/api/reports', {**base, 'target_id': keep, 'reason': 'wrong_point'})
        self.assertEqual(self.admin.post('/api/admin/videos/keep', {'id': keep}).status, 200)
        self.assertIn(keep, [v['id'] for v in self.client().get(f'/api/dive-points/{self.pid2}').json['videos']])

    # 6 -------------------------------------------------------------------------------------------------------------
    def test_6_administration(self):
        pid = self.pid3
        self.complete(self.diver)
        ids = [self.add(self.diver, YT + f'Ad6{i}Ef6hI9k', pid=pid).json['id'] for i in range(3)]
        self.assertEqual(self.admin.post('/api/admin/videos/approve', {'ids': ids[:2]}).json['approved'], 2, 'several at once')
        r = self.admin.post('/api/admin/videos/reject', {'id': ids[2]})
        self.assertEqual(r.status, 200, 'the reason of a rejection is optional')
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='video_rejected'"))
        self.assertEqual(self.admin.post('/api/admin/videos/edit', {'id': ids[1], 'title': 'Título corto', 'featured': True}).status, 200)
        vids = self.client().get(f'/api/dive-points/{pid}').json['videos']
        self.assertEqual(vids[0]['id'], ids[1], 'the featured video comes first'); self.assertTrue(vids[0]['featured'])
        self.assertEqual(vids[0]['title'], 'Título corto')
        published = [v['id'] for v in vids]
        new_order = list(reversed(published))
        self.assertEqual(self.admin.post('/api/admin/videos/order', {'point_id': pid, 'ids': new_order}).status, 200)
        vids = [v['id'] for v in self.client().get(f'/api/dive-points/{pid}').json['videos']]
        self.assertEqual(vids[0], ids[1], 'the featured one stays first')
        self.assertEqual(vids[1:], [x for x in new_order if x != ids[1]])
        for c in (self.diver, self.center, self.client()):
            self.assertIn(c.get('/api/admin/videos?tab=pending').status, (401, 403))
            self.assertIn(c.post('/api/admin/videos/approve', {'ids': ids}).status, (401, 403))

    def test_7_existing_videos_stay(self):
        self.assertTrue(self.server.sql("SELECT 1 FROM schema_migrations WHERE version='50.58-videos'"))
        cols = {r['name'] for r in self.server.sql('PRAGMA table_info(route_videos)')}
        self.assertTrue({'thumb_url', 'vertical', 'featured', 'unavailable_at', 'removed_at'} <= cols)


if __name__ == '__main__':
    unittest.main()
