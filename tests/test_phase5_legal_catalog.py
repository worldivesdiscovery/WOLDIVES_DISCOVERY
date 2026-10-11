"""Fase 5 (v50.36): legal documents with versions, acceptance and notice; data rights (ZIP export, deletion confirmed
by email); retention; legal block of experience bookings; reviews (single reply, reports, moderation); catalogue
(verified centres only, «Centros asociados», own point descriptions, demo mode); maps (PMTiles with Range, satellite
through our server with a monthly limit); image origins; permissions and bad data.
Every test runs on a copy of the seed database (helpers.Server)."""
import datetime as dt
import http.server
import io
import json
import re
import threading
import time
import unittest
import zipfile

from helpers import ServerTestCase, Server, Client

PNG = (b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x06\x00\x00\x00\x1f\x15\xc4\x89'
       b'\x00\x00\x00\rIDATx\x9cc\xf8\x0f\x00\x00\x01\x01\x00\x05\x18\xd8N\x00\x00\x00\x00IEND\xaeB`\x82')
TODAY = dt.date.today()


def outbox(server, template, to=None):
    q = 'SELECT * FROM email_outbox WHERE template=?' + (' AND to_email=?' if to else '') + ' ORDER BY id DESC'
    return server.sql(q, (template, to) if to else (template,))


class LegalDocuments(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'legal5', phone='+34 600 500 001')
        cls.diver = t.make_diver('legal5')

    def test_routes_aliases_and_official_languages(self):
        c = self.client()
        for route, slug in (('condiciones-buceadores', 'terminos'), ('condiciones-centros', 'centros'), ('normas-resenas', 'resenas'),
                            ('condiciones-reserva', 'reservas'), ('privacidad', 'privacidad'), ('cookies', 'cookies'), ('puntos', 'puntos'),
                            ('accesibilidad', 'accesibilidad'), ('contacto', 'contacto'), ('creditos', 'creditos'), ('aviso-legal', 'aviso-legal')):
            r = c.get(f'/api/legal/doc?slug={route}&lang=es')
            self.assertEqual(r.status, 200, (route, r))
            self.assertEqual(r.json['slug'], slug)
            self.assertNotIn('{{', r.json['markdown'], route)
        en = c.get('/api/legal/doc?slug=privacidad&lang=en').json
        self.assertEqual(en['lang'], 'en'); self.assertTrue(en['official']); self.assertEqual(en['prevails_note'], '')
        self.assertEqual(c.get('/api/legal/doc?slug=no-existe').status, 404)
        info = c.get('/api/legal/info').json
        self.assertIn('condiciones-buceadores', info['docs']); self.assertIn('condiciones-buceadores', info['versions'])

    def test_translation_shows_spanish_prevails(self):
        r = self.admin.post('/api/admin/legal/publish', {'slug': 'cookies', 'lang': 'fr', 'title': 'Politique de cookies',
                            'markdown': '# Politique de cookies\n\nNous utilisons uniquement des cookies techniques nécessaires au fonctionnement.', 'effective_at': TODAY.isoformat()})
        self.assertEqual(r.status, 200, r)
        d = self.client().get('/api/legal/doc?slug=cookies&lang=fr').json
        self.assertEqual(d['lang'], 'fr'); self.assertFalse(d['official']); self.assertTrue(d['prevails_note'])

    def test_new_version_must_be_accepted_again(self):
        d = self.make_diver('legal5b')
        self.assertEqual(d.me()['legal']['pending'], [])
        r = self.admin.post('/api/admin/legal/publish', {'slug': 'terminos', 'lang': 'es', 'markdown': '# Condiciones de uso para buceadores\n\nTexto nuevo de prueba de las condiciones, con más de cuarenta caracteres.',
                            'summary': 'Cambio de prueba', 'effective_at': TODAY.isoformat()})
        self.assertEqual(r.status, 200, r)
        ver = r.json['version']
        pend = d.me()['legal']['pending']
        self.assertEqual([p['slug'] for p in pend], ['terminos']); self.assertEqual(pend[0]['version'], ver)
        self.assertTrue(outbox(self.server, 'legal_update', 'legal5b@diver.example.org'))
        r = d.post('/api/legal/accept', {'docs': ['terminos']})
        self.assertEqual(r.status, 200, r); self.assertEqual(r.json['pending'], [])
        row = self.server.sql("SELECT version FROM legal_acceptances WHERE user_id=? AND document='terminos' ORDER BY id DESC LIMIT 1", (d.user['id'],))[0]
        self.assertEqual(row['version'], ver)
        hist = self.client().get('/api/legal/history?slug=condiciones-buceadores').json['items']
        self.assertGreaterEqual(len(hist), 2); self.assertEqual(hist[0]['summary'], 'Cambio de prueba')
        old = self.client().get(f"/api/legal/version?id={hist[-1]['id']}").json
        self.assertIn('Condiciones', old['title']); self.assertNotIn('{{', old['markdown'])

    def test_centres_get_15_days_notice(self):
        md = '# Condiciones para centros y profesionales\n\nNueva versión de prueba con más de cuarenta caracteres de texto.'
        r = self.admin.post('/api/admin/legal/publish', {'slug': 'centros', 'lang': 'es', 'markdown': md, 'effective_at': (TODAY + dt.timedelta(days=5)).isoformat()})
        self.assertEqual(r.status, 400); self.assertIn('15 días', r.json['error'])
        eff = (TODAY + dt.timedelta(days=16)).isoformat()
        r = self.admin.post('/api/admin/legal/publish', {'slug': 'centros', 'lang': 'es', 'markdown': md, 'summary': 'Cambio para centros', 'effective_at': eff})
        self.assertEqual(r.status, 200, r)
        lg = self.center.me()['legal']
        self.assertEqual([u['slug'] for u in lg['upcoming']], ['centros']); self.assertEqual(lg['upcoming'][0]['effective_at'], eff)
        self.assertNotIn('centros', [u['slug'] for u in self.diver.me()['legal']['upcoming']])
        self.assertEqual(self.client().get('/api/legal/doc?slug=condiciones-centros').json['upcoming']['effective_at'], eff)
        r = self.center.post('/api/legal/accept', {'docs': ['centros'], 'upcoming': True})
        self.assertEqual(r.status, 200, r); self.assertEqual(r.json['upcoming'], [])

    def test_publish_bad_data_and_permissions(self):
        good = {'slug': 'puntos', 'lang': 'es', 'markdown': '# Puntos\n\n' + 'x' * 60, 'effective_at': TODAY.isoformat()}
        for bad in ({'slug': 'nada'}, {'markdown': 'corto'}, {'effective_at': '2001-01-01'}, {'effective_at': 'mañana'}):
            r = self.admin.post('/api/admin/legal/publish', {**good, **bad})
            self.assertEqual(r.status, 400, (bad, r))
        for who in (self.diver, self.center, self.client()):
            self.assertIn(who.post('/api/admin/legal/publish', good).status, (401, 403))
            self.assertIn(who.get('/api/admin/legal/doc?slug=terminos').status, (401, 403))
        r = self.admin.get('/api/admin/legal/doc?slug=privacidad&lang=es')
        self.assertEqual(r.status, 200); self.assertIn('{{trade_name}}', r.json['base_markdown'])


class DataRights(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()

    def test_zip_export_with_documents(self):
        d = self.make_diver('zip5')
        r = d.upload('/api/account/documents', {'document_type': 'seguro', 'title': 'Seguro de buceo', 'expires_at': '2031-01-01'}, 'seguro.png', PNG)
        self.assertEqual(r.status, 200, r)
        r = d.get('/api/account/export?format=zip')
        self.assertEqual(r.status, 200); self.assertEqual(r.headers.get('Content-Type'), 'application/zip')
        z = zipfile.ZipFile(io.BytesIO(r.body))
        names = z.namelist()
        self.assertIn('datos.json', names); self.assertTrue(any(n.startswith('documentos/') for n in names), names)
        data = json.loads(z.read('datos.json'))
        self.assertEqual(data['account']['email'], 'zip5@diver.example.org')
        self.assertNotIn('password_hash', json.dumps(data))
        self.assertIn(self.client().get('/api/account/export?format=zip').status, (401, 403))

    def test_deletion_is_confirmed_by_email(self):
        d = self.make_diver('borrar5')
        self.assertEqual(d.post('/api/account/delete', {'password': 'mala'}).status, 400)
        r = d.post('/api/account/delete', {'password': 'buceo-seguro-2026'})
        self.assertEqual(r.status, 200, r); self.assertTrue(r.json['email_sent'])
        self.assertEqual(self.server.sql('SELECT email FROM users WHERE id=?', (d.user['id'],))[0]['email'], 'borrar5@diver.example.org')
        mail = outbox(self.server, 'account_delete_confirm', 'borrar5@diver.example.org')[0]
        token = re.search(r'eliminar-cuenta\?token=([A-Za-z0-9_\-]+)', mail['text']).group(1)
        self.assertEqual(self.client().post('/api/account/delete/confirm', {'token': 'falso'}).status, 400)
        r = self.client().post('/api/account/delete/confirm', {'token': token})
        self.assertEqual(r.status, 200, r)
        u = self.server.sql('SELECT fullname,email FROM users WHERE id=?', (d.user['id'],))[0]
        self.assertEqual(u['fullname'], 'Usuario eliminado'); self.assertTrue(u['email'].endswith('.local'))
        self.assertEqual(self.client().post('/api/account/delete/confirm', {'token': token}).status, 400)
        self.assertFalse(self.server.sql('SELECT 1 FROM user_profiles WHERE user_id=?', (d.user['id'],)))

    def test_deletion_cascades(self):
        c = self.client()
        r = c.register('Pro Borrable', 'pro5@pro.example.org', 'pro_borrable5', account_type='freelance', phone='+34 611 222 333')
        self.assertEqual(r.status, 200)
        uid = c.me()['user']['id']
        # A pending professional application stays a diver account: the deletion withdraws the claim.
        self.server.sql("UPDATE users SET email='pro5@sin-email.worldives.local' WHERE id=?", (uid,))
        self.assertEqual(c.post('/api/account/delete', {'password': 'buceo-seguro-2026'}).status, 200)
        claim = self.server.sql('SELECT status,phone,email FROM center_claims WHERE user_id=?', (uid,))[0]
        self.assertEqual(claim['status'], 'withdrawn'); self.assertIsNone(claim['phone']); self.assertIsNone(claim['email'])

    def test_retention_job(self):
        d = self.make_diver('inactivo5')
        old = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=800)).isoformat(timespec='seconds')
        self.server.sql('UPDATE users SET last_login=?, created_at=? WHERE id=?', (old, old, d.user['id']))
        r = d.upload('/api/account/documents', {'document_type': 'titulacion', 'title': 'Titulación caducada', 'expires_at': '2020-01-01'}, 'tit.png', PNG)
        self.assertEqual(r.status, 200, r)
        for bad in ({'inactive_months': 1}, {'audit_keep': 'muchas'}, {'notices_months': 999}):
            self.assertEqual(self.admin.post('/api/admin/retention', bad).status, 400, bad)
        r = self.admin.post('/api/admin/retention', {'inactive_months': 24, 'run_now': True})
        self.assertEqual(r.status, 200, r)
        self.assertGreaterEqual(r.json['report']['warned'], 1); self.assertGreaterEqual(r.json['report']['documents_deleted'], 1)
        self.assertTrue(outbox(self.server, 'account_inactive', 'inactivo5@diver.example.org'))
        self.assertFalse(self.server.sql("SELECT 1 FROM user_documents WHERE user_id=? AND expires_at='2020-01-01'", (d.user['id'],)))
        warned = (dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=40)).isoformat(timespec='seconds')
        self.server.sql('UPDATE users SET inactive_warned_at=? WHERE id=?', (warned, d.user['id']))
        r = self.admin.post('/api/admin/retention', {'run_now': True})
        self.assertGreaterEqual(r.json['report']['accounts_deleted'], 1)
        self.assertEqual(self.server.sql('SELECT fullname FROM users WHERE id=?', (d.user['id'],))[0]['fullname'], 'Usuario eliminado')
        s = self.admin.get('/api/admin/retention').json
        self.assertEqual(s['settings']['inactive_months'], 24); self.assertTrue(s['last'])
        self.assertEqual(self.make_diver('curioso5').get('/api/admin/retention').status, 403)


class ReviewsAndReports(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'resenas5', phone='+34 600 500 002')
        cls.other = t.make_center(cls.admin, 'otro5', phone='+34 600 500 003')
        cls.diver = t.make_diver('resena5')
        cid = cls.center.user['center_id']
        cls.server.sql('''INSERT INTO bookings(user_id,center_id,booking_date,participants,status,payment_status,created_at,updated_at)
                          VALUES(?,?,?,1,'confirmed','paid',?,?)''', (cls.diver.user['id'], cid, '2026-01-10', '2026-01-01T10:00:00+00:00', '2026-01-01T10:00:00+00:00'))

    def review(self):
        cid = self.center.user['center_id']
        r = self.diver.post(f'/api/centers/{cid}/reviews', {'rating': 4, 'title': 'Muy bien', 'body': 'Buen trato y buena organización.'})
        self.assertEqual(r.status, 200, r)
        return r.json['id']

    def test_single_editable_reply(self):
        rid = self.review(); cid = self.center.user['center_id']
        self.admin.post(f'/api/admin/reviews/{rid}/moderate', {'active': True})   # another test may have hidden it
        self.assertEqual(self.other.post(f'/api/reviews/{rid}/reply', {'body': 'Gracias por venir'}).status, 403)
        self.assertEqual(self.diver.post(f'/api/reviews/{rid}/reply', {'body': 'Me respondo'}).status, 403)
        self.assertEqual(self.center.post(f'/api/reviews/{rid}/reply', {'body': 'Hola'}).status, 400)
        self.assertEqual(self.center.post(f'/api/reviews/{rid}/reply', {'body': 'Gracias por bucear con nosotros.'}).status, 200)
        self.assertEqual(self.center.post(f'/api/reviews/{rid}/reply', {'body': 'Gracias de nuevo por bucear con nosotros.'}).status, 200)
        d = self.center.get(f'/api/centers/{cid}').json
        rv = [x for x in d['reviews'] if x['id'] == rid][0]
        self.assertNotIn(' ', rv['fullname'] or '')   # only the first name leaves the server
        self.assertEqual(rv['reply_body'], 'Gracias de nuevo por bucear con nosotros.')
        self.assertTrue(d['review']['can_reply'])
        self.assertEqual(len(outbox(self.server, 'review_replied', 'resena5@diver.example.org')), 1)   # only the first reply notifies
        self.assertEqual(self.center.post(f'/api/reviews/{rid}/reply', {'body': ''}).status, 200)
        self.assertIsNone(self.server.sql('SELECT reply_body FROM center_reviews WHERE id=?', (rid,))[0]['reply_body'])

    def test_report_review_and_decision_to_both_parties(self):
        rid = self.review(); anon = self.client()
        base = {'reason': 'fake_review', 'details': 'Esta reseña no parece de un cliente real del centro.', 'good_faith': True,
                'name': 'Denunciante', 'email': 'denuncia5@example.org'}
        self.assertEqual(anon.post('/api/reports', {**base, 'target_type': 'review', 'target_id': 999999}).status, 400)
        self.assertEqual(anon.post('/api/reports', {**base, 'target_type': 'review', 'target_id': rid, 'good_faith': False}).status, 400)
        r = anon.post('/api/reports', {**base, 'target_type': 'review', 'target_id': rid})
        self.assertEqual(r.status, 200, r)
        rep = self.server.sql('SELECT * FROM content_reports WHERE id=?', (r.json['id'],))[0]
        self.assertEqual(rep['affected_user_id'], self.diver.user['id'])
        self.assertEqual(self.diver.post('/api/admin/reports/resolve', {'id': rep['id'], 'status': 'actioned'}).status, 403)
        r = self.admin.post('/api/admin/reports/resolve', {'id': rep['id'], 'status': 'actioned', 'resolution': 'Incumple las normas de las reseñas.'})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.server.sql('SELECT active FROM center_reviews WHERE id=?', (rid,))[0]['active'], 0)
        self.assertTrue(outbox(self.server, 'report_resolved', 'denuncia5@example.org'))
        self.assertTrue(outbox(self.server, 'report_decision_affected', 'resena5@diver.example.org'))

    def test_reports_on_centre_point_photo(self):
        c = self.client(); cid = self.center.user['center_id']
        pid = self.server.sql('SELECT id FROM dive_points WHERE active=1 LIMIT 1')[0]['id']
        base = {'reason': 'false', 'details': 'La información de esta ficha no es correcta.', 'good_faith': True}
        # DSA art. 16.2: an anonymous notice needs a name and an email to receive the decision
        self.assertEqual(c.post('/api/reports', {**base, 'target_type': 'center', 'target_id': cid}).status, 400)
        base.update(name='Marta Denunciante', email='marta@example.org', lang='fr')
        for tt, tid in (('center', cid), ('point', pid), ('photo', cid)):
            r = c.post('/api/reports', {**base, 'target_type': tt, 'target_id': tid})
            self.assertEqual(r.status, 200, (tt, r))
        self.assertEqual(c.post('/api/reports', {**base, 'target_type': 'virus', 'target_id': 1}).status, 400)
        items = self.admin.get('/api/admin/legal').json['reports']
        self.assertTrue({'center', 'point', 'photo'} <= {x['target_type'] for x in items})
        rep = [x for x in items if x['target_type'] == 'point'][0]
        self.assertEqual(self.admin.post('/api/admin/reports/resolve', {'id': rep['id'], 'status': 'dismissed', 'resolution': 'ok'}).status, 400)
        self.assertEqual(self.admin.post('/api/admin/reports/resolve', {'id': rep['id'], 'status': 'dismissed', 'resolution': 'La ficha coincide con la información publicada por el centro.'}).status, 200)
        mail = self.server.sql("SELECT text FROM email_outbox WHERE template='report_resolved' AND to_email='marta@example.org'")[0]['text']
        self.assertIn('Après examen', mail)   # the reporter's language, with the redress options
        self.assertIn('2022/2065', mail)

    def test_admin_moderation_needs_reason(self):
        rid = self.review()
        self.assertEqual(self.admin.post(f'/api/admin/reviews/{rid}/moderate', {'active': False, 'reason': 'no'}).status, 400)
        self.assertEqual(self.center.post(f'/api/admin/reviews/{rid}/moderate', {'active': False, 'reason': 'Me molesta esta reseña'}).status, 403)
        self.assertEqual(self.admin.post(f'/api/admin/reviews/{rid}/moderate', {'active': False, 'reason': 'Contiene datos personales de un tercero.'}).status, 200)
        self.assertEqual(self.server.sql('SELECT active FROM center_reviews WHERE id=?', (rid,))[0]['active'], 0)
        self.review()   # editing a hidden review does not publish it again
        self.assertEqual(self.server.sql('SELECT active FROM center_reviews WHERE id=?', (rid,))[0]['active'], 0)
        self.assertEqual(self.admin.post(f'/api/admin/reviews/{rid}/moderate', {'active': True}).status, 200)
        self.assertEqual(self.server.sql('SELECT active FROM center_reviews WHERE id=?', (rid,))[0]['active'], 1)

    def test_professionals_cannot_review(self):
        pro = self.make_freelance(self.admin, 'resenapro5'); cid = self.center.user['center_id']
        self.assertEqual(pro.post(f'/api/centers/{cid}/reviews', {'rating': 5, 'body': 'Excelente'}).status, 403)

    def test_experience_shows_provider_and_policy(self):
        offer = self.server.sql('SELECT id FROM travel_offers LIMIT 1')[0]['id']
        r = self.center.post('/api/travel-experiences', {'travel_offer_id': offer, 'title': 'Salida de prueba', 'price': 80, 'spots_total': 6})
        self.assertEqual(r.status, 200, r)
        eid = r.json['id']
        item = self.client().get(f'/api/travel-experiences/{eid}?lang=es').json['item']
        self.assertIn('Centro resenas5', item['provider_legal']['name'])
        self.assertTrue(item['provider_legal']['policy_text'])


class CatalogueAndMaps(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.tile_server = http.server.ThreadingHTTPServer(('127.0.0.1', 0), TileHandler)
        threading.Thread(target=cls.tile_server.serve_forever, daemon=True).start()
        import tempfile, pathlib
        cls.tiles = pathlib.Path(tempfile.mkdtemp(prefix='wod-tiles-'))
        (cls.tiles / 'worldives.pmtiles').write_bytes(bytes(range(256)) * 40)
        cls.extra_env = {'ARCGIS_API_KEY': 'clave-de-prueba', 'WOD_ARCGIS_TILE_URL': f'http://127.0.0.1:{cls.tile_server.server_port}/tile/{{z}}/{{y}}/{{x}}',
                         'WOD_TILES_DIR': str(cls.tiles)}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.diver = t.make_diver('mapas5')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.tile_server.shutdown()

    def test_only_verified_centres_are_public(self):
        seed = self.server.sql("SELECT id FROM centers WHERE source_name LIKE 'PADI%' LIMIT 1")[0]['id']
        c = self.client()
        self.assertEqual(c.get(f'/api/centers/{seed}').status, 404)
        ids = [x['id'] for x in c.get('/api/center-directory?per_page=100').json.get('items', [])]
        self.assertNotIn(seed, ids)
        center = self.make_center(self.admin, 'verif5', phone='+34 600 500 004')
        self.assertEqual(c.get(f"/api/centers/{center.user['center_id']}").status, 200)

    def test_associated_centres_band(self):
        self.assertEqual(self.client().get('/api/site-promos').json['centers'], [])
        ids = [x['id'] for x in self.server.sql("SELECT id FROM centers WHERE source_name LIKE 'PADI%' LIMIT 6")]
        self.server.sql(f"UPDATE centers SET verification_status='verified', logo_url='/assets/images/1.webp', logo_consent=1 WHERE id IN ({','.join('?' * 6)})", ids)
        self.assertEqual(self.admin.post('/api/admin/site-promos/settings', {'partners_email': '', 'partners_text': '', 'partners_min_centers': 6}).status, 200)
        band = self.client().get('/api/site-promos').json['centers']
        self.assertEqual(sorted(x['id'] for x in band), sorted(ids))
        self.assertEqual(self.admin.post('/api/admin/site-promos/settings', {'partners_min_centers': 7}).status, 200)
        self.assertEqual(self.client().get('/api/site-promos').json['centers'], [])
        self.server.sql(f"UPDATE centers SET verification_status='source_public', logo_consent=0 WHERE id IN ({','.join('?' * 6)})", ids)
        self.admin.post('/api/admin/site-promos/settings', {'partners_min_centers': 6})

    def test_logo_consent_from_the_centre_panel(self):
        center = self.make_center(self.admin, 'logo5', phone='+34 600 500 005')
        r = center.post('/api/provider/center-update', {'name': 'Centro logo5', 'country': 'España', 'city': 'Xàbia', 'logo_consent': True})
        self.assertEqual(r.status, 200, r)
        row = self.server.sql('SELECT logo_consent,logo_consent_at FROM centers WHERE id=?', (center.user['center_id'],))[0]
        self.assertEqual(row['logo_consent'], 1); self.assertTrue(row['logo_consent_at'])

    def test_point_descriptions_in_10_languages(self):
        pid = self.server.sql("SELECT id FROM dive_points WHERE name='Cap Dor'")[0]['id']
        texts = self.server.sql('SELECT lang,description FROM dive_point_texts WHERE point_id=?', (pid,))
        self.assertEqual(len(texts), 10)
        es = self.client().get(f'/api/dive-points/{pid}?lang=es').json['item']
        self.assertIn('Torre de Cap d', es['description']); self.assertNotIn('description_legacy', es)
        en = self.client().get(f'/api/dive-points/{pid}?lang=en').json['item']
        self.assertEqual(en['description_lang'], 'en'); self.assertIn('Depth from 10 to 28 m', en['description'])
        legacy = self.server.sql('SELECT description_legacy FROM dive_points WHERE id=?', (pid,))[0]['description_legacy']
        self.assertIn('Punta de Moraira', legacy)   # the previous text is kept until reviewed
        padi = self.server.sql("SELECT description,description_missing FROM dive_points WHERE source_name LIKE 'PADI%' LIMIT 1")[0]
        self.assertNotIn('pendiente de verificación', padi['description'])
        self.assertIn('qué se ve', padi['description_missing'])
        self.assertEqual(self.diver.get('/api/admin/point-texts').status, 403)
        lst = self.admin.get('/api/admin/point-texts').json
        self.assertGreater(lst['total'], 200)
        r = self.admin.post('/api/admin/point-texts/review', {'id': pid, 'description': 'Texto revisado por el titular con datos comprobados.'})
        self.assertEqual(r.status, 200, r)
        row = self.server.sql('SELECT description,description_reviewed FROM dive_points WHERE id=?', (pid,))[0]
        self.assertEqual(row['description_reviewed'], 1)
        self.assertEqual(self.admin.post('/api/admin/point-texts/review', {'id': pid, 'description': 'corto'}).status, 400)
        self.assertEqual(self.admin.post('/api/admin/point-texts/review', {'id': pid, 'regenerate': True}).status, 200)

    def test_pmtiles_served_with_range(self):
        cfg = self.client().get('/api/map/config').json
        self.assertEqual(cfg['basemap']['type'], 'pmtiles'); self.assertIn('OpenStreetMap', cfg['basemap']['attribution'])
        c = self.client()
        r = c.request('GET', '/tiles/worldives.pmtiles', headers={'Range': 'bytes=0-9'})
        self.assertEqual(r.status, 206); self.assertEqual(r.body, bytes(range(10)))
        self.assertEqual(r.headers.get('Content-Range'), 'bytes 0-9/10240')
        self.assertEqual(c.request('GET', '/tiles/worldives.pmtiles', headers={'Range': 'bytes=99999-'}).status, 416)
        self.assertEqual(c.request('GET', '/tiles/worldives.pmtiles', headers={'Range': 'bytes=-16'}).body, (bytes(range(256)) * 40)[-16:])
        self.assertEqual(c.get('/tiles/otro.pmtiles').status, 404)
        self.assertFalse(c.get('/tiles/../data/test.sqlite3').body.startswith(b'SQLite'))

    def test_satellite_proxy_counter_and_limit(self):
        c = self.client()
        self.assertTrue(c.get('/api/map/config').json['satellite']['enabled'])
        r = c.get('/api/tiles/satellite/3/2/1')
        self.assertEqual(r.status, 200, r); self.assertEqual(r.body, PNG)
        self.assertEqual(TileHandler.last_token, 'clave-de-prueba')   # the key goes from our server to Esri, never to the browser
        self.assertNotIn('clave-de-prueba', json.dumps(c.get('/api/map/config').json))
        for bad in ('/api/tiles/satellite/30/1/1', '/api/tiles/satellite/2/9/9', '/api/tiles/satellite/a/b/c'):
            self.assertEqual(c.get(bad).status, 404, bad)
        st = self.admin.get('/api/admin/maps').json
        self.assertGreaterEqual(st['used'], 1); self.assertEqual(st['limit'], 1_900_000)
        self.assertEqual(self.diver.post('/api/admin/maps', {'limit': 5}).status, 403)
        self.assertEqual(self.admin.post('/api/admin/maps', {'limit': 'mucho'}).status, 400)
        used = st['used']
        self.assertEqual(self.admin.post('/api/admin/maps', {'limit': used + 1}).status, 200)
        self.assertEqual(c.get('/api/tiles/satellite/3/2/2').status, 200)   # reaches the limit (and 80 %)
        # 80 % alert (the test administrator has a .test address, so the email itself is not queued)
        self.assertTrue(self.server.sql("SELECT 1 FROM site_settings WHERE key LIKE 'maps_satellite_alert_%'"))
        self.assertFalse(c.get('/api/map/config').json['satellite']['enabled'])
        self.assertEqual(c.get('/api/tiles/satellite/3/2/3').status, 404)
        self.admin.post('/api/admin/maps', {'limit': 1_900_000})

    def test_image_origins_report(self):
        d = self.admin.get('/api/admin/images').json
        self.assertGreater(d['missing'], 0)
        path = d['items'][0]['path']
        self.assertEqual(self.admin.post('/api/admin/images', {'path': '/etc/passwd', 'origin': 'x'}).status, 400)
        self.assertEqual(self.admin.post('/api/admin/images', {'path': path, 'credit': 'Autor', 'origin': 'Foto propia'}).status, 200)
        d2 = self.admin.get('/api/admin/images').json
        self.assertEqual(d2['missing'], d['missing'] - 1)
        self.assertEqual(self.diver.get('/api/admin/images').status, 403)


class TileHandler(http.server.BaseHTTPRequestHandler):
    last_token = None

    def do_GET(self):
        TileHandler.last_token = self.path.split('token=')[-1]
        self.send_response(200); self.send_header('Content-Type', 'image/png'); self.send_header('Content-Length', str(len(PNG))); self.end_headers(); self.wfile.write(PNG)

    def log_message(self, *a):
        pass


class DemoMode(ServerTestCase):
    extra_env = {'WOD_DEMO_MODE': '1', 'STRIPE_SECRET_KEY': 'sk_test_no_se_usa'}

    def test_demo_mode(self):
        c = self.client()
        st = c.get('/api/setup/status').json
        self.assertTrue(st['demo']); self.assertFalse(st['registration_open'])
        r = c.get('/api/health')
        self.assertIn('noindex', r.headers.get('X-Robots-Tag', ''))
        seed = self.server.sql("SELECT id FROM centers WHERE source_name LIKE 'PADI%' LIMIT 1")[0]['id']
        item = c.get(f'/api/centers/{seed}').json['item']
        self.assertFalse(item['online_payments'])   # no real payments in the demo
        self.assertNotEqual(c.register('Demo', 'demo5@diver.example.org', 'demo5').status, 200)


if __name__ == '__main__':
    unittest.main()
