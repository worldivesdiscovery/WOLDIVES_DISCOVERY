"""v50.53 · tarea 4 (revisión del titular, 14/10/2026): foto de fondo traslúcida en cada servicio.

Plantillas de servicios de la administración (nombre por idioma, texto, duración y foto con la compresión común), foto
de la plantilla o foto propia del centro o freelance (casilla de derechos obligatoria, máximo 6 MB, sin EXIF/GPS),
«Volver a la foto de la plantilla» borra la propia del disco, la administración puede retirar una foto propia, y el
cambio de foto de una plantilla llega al momento a todos los servicios que la usan salvo a los que tienen foto propia.
Cada rol solo puede lo suyo.
"""
import io
import json
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import PDF_BYTES, Server, ServerTestCase, Client, _png  # noqa: E402

try:
    from PIL import Image
except ImportError:      # the server needs Pillow for these photos (requirements.txt)
    Image = None


def photo(color=(20, 90, 140), size=(1200, 675), gps=True):
    """A JPG like the ones a phone takes: with the camera's model and the GPS position in its EXIF."""
    im = Image.new('RGB', size, color)
    for x in range(0, size[0], 40):            # some detail so it is not a flat colour
        im.paste((255, 255, 255), (x, size[1] // 3, x + 8, size[1] // 3 + 8))
    ex = Image.Exif(); ex[0x010F] = 'CamaraPrueba'
    if gps: ex[0x8825] = {1: 'N', 2: (40.0, 25.0, 1.0), 3: 'W', 4: (3.0, 42.0, 1.0)}
    b = io.BytesIO(); im.save(b, 'JPEG', quality=90, exif=ex)
    return b.getvalue()


@unittest.skipIf(Image is None, 'Pillow no está instalado')
class Tarjetas(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'tarjeta1')
        cls.center2 = t.make_center(cls.admin, 'tarjeta2', phone='+34 600 222 333')
        cls.pro = t.make_freelance(cls.admin, 'tarjeta3')
        cls.diver = t.make_diver('tarjeta4')
        cat = cls.admin.get('/api/admin/service-catalog').json['items']
        cls.tpl = {x['slug']: x['id'] for x in cat}

    # helpers -----------------------------------------------------------------------------------------------------
    def new_service(self, client=None, title='Curso Open Water Diver 3 días', template='open-water'):
        data = {'title': title, 'price': 390, 'booking_mode': 'request', 'service_type': 'curso'}
        if template: data['template_id'] = self.tpl[template]
        r = (client or self.center).post('/api/provider-services', data)
        self.assertEqual(r.status, 200, r)
        return r.json['id']

    def card(self, sid, owner=None):
        """The service as its owner's panel sees it (owner) or as the public sees it."""
        c = owner or self.center
        if owner:
            qs = f"provider_id={c.user['id']}&include_inactive=1"
        else:
            cid = self.server.sql('SELECT center_id FROM provider_services WHERE id=?', (sid,))[0]['center_id']
            qs = f'center_id={cid}' if cid else f"provider_id={self.server.sql('SELECT provider_user_id FROM provider_services WHERE id=?', (sid,))[0]['provider_user_id']}"
        items = self.client().get('/api/provider-services?' + qs).json['items'] if not owner else c.get('/api/provider-services?' + qs).json['items']
        return next(x for x in items if x['id'] == sid)

    def wait(self, sql, args, done, timeout=20):
        for _ in range(int(timeout * 10)):
            row = self.server.sql(sql, args)[0]
            if done(row): return row
            time.sleep(0.1)
        self.fail(f'no termina de procesarse: {row}')

    def wait_service(self, sid):
        return self.wait('SELECT * FROM provider_services WHERE id=?', (sid,), lambda r: not str(r['photo_status'] or '').startswith('processing'))

    def wait_template(self, tid):
        return self.wait('SELECT * FROM service_catalog WHERE id=?', (tid,), lambda r: not str(r['photo_status'] or '').startswith('processing'))

    def files(self, folder, base):
        return sorted((self.server.tmp / 'uploads' / folder).glob(f'{base}-*')) if base else []

    def upload_own(self, sid, client=None, rights='1', content=None, focal='30,60'):
        fields = {'id': sid, 'focal': focal}
        if rights is not None: fields['rights'] = rights
        return (client or self.center).upload('/api/provider-services/photo', fields, 'foto.jpg', content or photo())

    # catalogue -----------------------------------------------------------------------------------------------------
    def test_catalog_of_templates_in_nine_languages(self):
        c = self.client()
        es = c.get('/api/service-catalog?lang=es').json; en = c.get('/api/service-catalog?lang=en').json
        slugs = {x['slug'] for x in es['items']}
        for s in ('bautizo', 'open-water', 'advanced', 'rescue', 'divemaster', 'nitrox', 'especialidad', 'inmersion-simple', 'inmersion-doble',
                  'tercera-inmersion', 'nocturna', 'snorkel', 'salida-privada', 'viaje', 'vida-a-bordo'):
            self.assertIn(s, slugs)
        ow_es = next(x for x in es['items'] if x['slug'] == 'open-water'); ow_en = next(x for x in en['items'] if x['slug'] == 'open-water')
        self.assertNotEqual(ow_es['name'], ow_en['name'])
        self.assertTrue(ow_es['description'] and ow_es['duration_minutes'])
        self.assertFalse(ow_en['pending_translation'])
        admin = self.admin.get('/api/admin/service-catalog').json
        for x in admin['items']:
            if x['slug'] in self.tpl:                                               # the 16 seeded ones
                self.assertEqual(set(x['names']), {'es', 'en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh'}, x['slug'])
                self.assertEqual(x['missing_langs'], [], x['slug'])
        # Without a photo the template shows the neutral photo chosen by the administration, never an empty box.
        self.assertEqual(ow_es['photo']['source'], 'neutral')
        self.assertTrue(ow_es['photo']['src'])

    def test_a_language_without_text_falls_back_to_spanish_and_is_marked(self):
        r = self.admin.post('/api/admin/service-catalog/save', {'names': {'es': 'Buceo en cuevas'}, 'descriptions': {'es': 'Con guía de cuevas.'},
                                                               'service_type': 'inmersion', 'duration_minutes': 180})
        self.assertEqual(r.status, 200, r)
        item = next(x for x in self.client().get('/api/service-catalog?lang=de').json['items'] if x['id'] == r.json['id'])
        self.assertEqual((item['name'], item['pending_translation']), ('Buceo en cuevas', True))
        adm = next(x for x in self.admin.get('/api/admin/service-catalog').json['items'] if x['id'] == r.json['id'])
        self.assertEqual(len(adm['missing_langs']), 8)
        self.assertEqual(self.admin.post('/api/admin/service-catalog/save', {'names': {'en': 'Cave diving'}}).status, 400)   # Spanish required

    # photos ----------------------------------------------------------------------------------------------------------
    def test_template_photo_reaches_every_service_but_not_own_photos(self):
        a = self.new_service(title='Curso Advanced Open Water 2 días', template='advanced')
        b = self.new_service(title='Especialidad Advanced con foto propia', template='advanced')
        self.assertEqual(self.upload_own(b).status, 200)
        own = self.wait_service(b)
        self.assertEqual(self.card(a)['photo']['source'], 'neutral')
        tid = self.tpl['advanced']
        r = self.admin.upload('/api/admin/service-catalog/photo', {'id': tid, 'focal': '50,40'}, 'plantilla.jpg', photo((200, 120, 40)))
        self.assertEqual(r.status, 200, r)
        first = self.wait_template(tid)['photo_base']
        pa = self.card(a)['photo']
        self.assertEqual(pa['source'], 'template')
        self.assertIn(f'/assets/uploads/plantillas/{first}-', pa['src'])
        self.assertEqual(pa['focal'], '50,40')
        self.assertEqual(self.card(b)['photo']['source'], 'own')
        # A second photo for the template: instantly on A (no cache to wait for), B keeps its own, the old file is gone.
        self.admin.upload('/api/admin/service-catalog/photo', {'id': tid}, 'plantilla2.jpg', photo((10, 160, 90)))
        second = self.wait_template(tid)['photo_base']
        self.assertNotEqual(first, second)
        self.assertIn(second, self.card(a)['photo']['src'])
        self.assertIn(own['photo_base'], self.card(b)['photo']['src'])
        self.assertEqual(self.files('plantillas', first), [])
        self.assertTrue(self.files('plantillas', second))
        # The app mode uses the same card data (salidas cercanas, centre page).
        adm = next(x for x in self.admin.get('/api/admin/service-catalog').json['items'] if x['id'] == tid)
        self.assertEqual((adm['services'], adm['services_with_photo']), (2, 1))
        # Removing the template's photo: its services go back to the neutral photo.
        self.assertEqual(self.admin.post('/api/admin/service-catalog/photo-reset', {'id': tid}).status, 200)
        self.assertEqual(self.card(a)['photo']['source'], 'neutral')
        self.assertEqual(self.files('plantillas', second), [])

    def test_own_photo_needs_the_rights_box_and_loses_its_exif(self):
        sid = self.new_service(title='Doble inmersión con barco', template='inmersion-doble')
        r = self.upload_own(sid, rights=None)
        self.assertEqual(r.status, 400)
        self.assertIn('derechos', r.json['error'])
        self.assertEqual(self.upload_own(sid, rights='0').status, 400)
        r = self.upload_own(sid)
        self.assertEqual((r.status, r.json.get('status')), (200, 'processing'))
        row = self.wait_service(sid)
        self.assertEqual((row['photo_mode'], row['photo_status']), ('own', 'ready'))
        self.assertTrue(row['photo_rights_at'] and row['photo_at'])
        self.assertEqual(row['photo_by'], self.center.user['id'])                       # who and when
        self.assertEqual(self.server.sql("SELECT user_id FROM audit_log WHERE action='service_photo_uploaded' AND entity_id=?", (sid,))[0]['user_id'],
                         self.center.user['id'])
        files = self.files('servicios', row['photo_base'])
        names = {f.name.rsplit('-', 1)[1] for f in files}
        self.assertEqual(names, {'480.webp', '960.webp', '960.jpg'})                   # 1200 px wide: no 1440
        for f in files:
            data = f.read_bytes()
            self.assertNotIn(b'CamaraPrueba', data, f.name)
            with Image.open(f) as im:
                self.assertEqual(len(im.getexif()), 0, f.name)
        self.assertRegex(row['photo_base'], r'^s\d+-[0-9a-f]{12}$')                    # fingerprint in the name (cache)
        card = self.card(sid)
        self.assertEqual((card['photo']['source'], card['photo']['own'], card['photo']['focal']), ('own', True, '30,60'))
        self.assertIn('960w', card['photo']['srcset'])
        self.assertTrue(0 < card['photo']['veil']['light'] <= 0.95)
        for k in ('photo_base', 'photo_by', 'photo_rights_at', 'photo_note'):
            self.assertNotIn(k, card)                                                    # the public sees the card, not who uploaded it
        # Back to the template's photo: the own photo is deleted from the disk.
        self.assertEqual(self.center.post('/api/provider-services/photo-template', {'id': sid}).status, 200)
        self.assertEqual(self.files('servicios', row['photo_base']), [])
        self.assertEqual(self.card(sid)['photo']['source'], 'neutral')
        self.assertEqual(self.server.sql('SELECT photo_mode,photo_rights_at FROM provider_services WHERE id=?', (sid,))[0],
                         {'photo_mode': 'template', 'photo_rights_at': None})

    def test_replacing_an_own_photo_deletes_the_old_one(self):
        sid = self.new_service(title='Bautizo en la playa', template='bautizo')
        self.upload_own(sid); first = self.wait_service(sid)['photo_base']
        self.upload_own(sid, content=photo((240, 240, 230))); second = self.wait_service(sid)['photo_base']
        self.assertNotEqual(first, second)
        self.assertEqual(self.files('servicios', first), [])
        self.assertTrue(self.files('servicios', second))

    def test_upload_checks(self):
        sid = self.new_service(title='Especialidad Nitrox (EANx)', template='nitrox')
        r = self.upload_own(sid, content=PDF_BYTES)
        self.assertEqual(r.status, 400); self.assertIn('Formato', r.json['error'])
        r = self.upload_own(sid, content=_png(200, 100))
        self.assertEqual(r.status, 400); self.assertIn('320 × 180', r.json['error'])
        big = b'\xff\xd8\xff\xe0' + b'0' * (6 * 1024 * 1024 + 10)
        r = self.upload_own(sid, content=big)
        self.assertEqual(r.status, 400); self.assertIn('6 MB', r.json['error'])
        r = self.upload_own(sid, content=b'\xff\xd8\xff\xe0' + b'no es una foto' * 20)
        self.assertEqual(r.status, 400)
        self.assertIsNone(self.server.sql('SELECT photo_status FROM provider_services WHERE id=?', (sid,))[0]['photo_status'])
        # A portrait photo is fine (either orientation).
        self.assertEqual(self.upload_own(sid, content=photo(size=(600, 900))).status, 200)
        self.assertEqual(self.wait_service(sid)['photo_status'], 'ready')

    def test_admin_withdraws_an_unsuitable_own_photo(self):
        sid = self.new_service(title='Inmersión nocturna', template='nocturna')
        self.upload_own(sid); base = self.wait_service(sid)['photo_base']
        own = [x['id'] for x in self.admin.get('/api/admin/service-catalog').json['own_photos']]
        self.assertIn(sid, own)
        self.assertEqual(self.admin.post('/api/admin/service-photo/remove', {'id': sid, 'reason': 'no'}).status, 400)   # a reason is required
        r = self.admin.post('/api/admin/service-photo/remove', {'id': sid, 'reason': 'Aparecen personas reconocibles'})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.files('servicios', base), [])
        mine = self.card(sid, owner=self.center)
        self.assertEqual(mine['photo_mode'], 'template')
        self.assertEqual(mine['photo_note'], 'La administración ha retirado la foto: Aparecen personas reconocibles')
        self.assertNotIn('photo_note', self.card(sid))                                  # only the owner sees why
        self.assertEqual(self.admin.post('/api/admin/service-photo/remove', {'id': sid, 'reason': 'otra vez'}).status, 404)
        # A new own photo clears the note.
        self.upload_own(sid); self.wait_service(sid)
        self.assertNotIn('photo_note', {k: v for k, v in self.card(sid, owner=self.center).items() if v})

    def test_without_template_the_neutral_photo(self):
        sid = self.new_service(title='Sesión de fotos y vídeo bajo el agua', template=None)
        p = self.card(sid)['photo']
        self.assertEqual((p['source'], p['src']), ('neutral', '/img/portada/fondo.webp'))
        self.assertTrue(p['veil']['light'] >= 0.5 and p['veil']['dark'] >= 0.5)

    def test_veil_setting(self):
        self.assertEqual(self.admin.post('/api/admin/service-card-veil', {'value': 0.7}).json['value'], 0.7)
        self.assertEqual(self.client().get('/api/site-media').json['card_veil'], 0.7)
        self.assertEqual(self.admin.post('/api/admin/service-card-veil', {'value': 3}).json['value'], 0.95)
        self.assertEqual(self.admin.post('/api/admin/service-card-veil', {'value': 'mucho'}).status, 400)
        self.admin.post('/api/admin/service-card-veil', {'value': 0.8})

    def test_freelance_own_photo(self):
        sid = self.new_service(self.pro, title='Salida privada con guía', template='salida-privada')
        self.assertEqual(self.upload_own(sid, client=self.pro).status, 200)
        self.assertEqual(self.wait_service(sid)['photo_mode'], 'own')

    # roles ------------------------------------------------------------------------------------------------------------
    def test_each_role_only_what_is_its_own(self):
        sid = self.new_service(title='Snorkel guiado', template='snorkel')
        anon = self.client()
        # Without a session a POST answers 403 «Necesitas iniciar sesión.» (the CSRF check comes first), as everywhere.
        for c, code in ((anon, 403), (self.diver, 403)):
            self.assertEqual(self.upload_own(sid, client=c).status, code)
            self.assertEqual(c.post('/api/provider-services/photo-template', {'id': sid}).status, code)
            self.assertEqual(c.post('/api/provider-services/photo-focal', {'id': sid, 'focal': '10,10'}).status, code)
        for c in (self.center2, self.pro):                                               # another tenant: not even its existence
            self.assertEqual(self.upload_own(sid, client=c).status, 404)
            self.assertEqual(c.post('/api/provider-services/photo-template', {'id': sid}).status, 404)
        self.assertEqual(anon.get('/api/admin/service-catalog').status, 403)
        for c, code in ((anon, 403), (self.diver, 403), (self.center, 403), (self.pro, 403)):
            if c is not anon: self.assertEqual(c.get('/api/admin/service-catalog').status, code)
            self.assertEqual(c.post('/api/admin/service-catalog/save', {'names': {'es': 'X'}}).status, code)
            self.assertEqual(c.upload('/api/admin/service-catalog/photo', {'id': self.tpl['snorkel']}, 'x.jpg', photo()).status, code)
            self.assertEqual(c.post('/api/admin/service-catalog/photo-reset', {'id': self.tpl['snorkel']}).status, code)
            self.assertEqual(c.post('/api/admin/service-card-veil', {'value': 0.6}).status, code)
            self.assertEqual(c.post('/api/admin/service-photo/remove', {'id': sid, 'reason': 'por probar'}).status, code)
        self.assertEqual(self.server.sql('SELECT photo_status FROM provider_services WHERE id=?', (sid,))[0]['photo_status'], None)

    def test_template_choice_on_create_and_update(self):
        sid = self.new_service(title='Bautizo de buceo', template='bautizo')
        self.assertEqual(self.card(sid)['template']['slug'], 'bautizo')
        r = self.center.post('/api/provider-services/update', {'id': sid, 'title': 'Bautizo de buceo', 'price': 60, 'booking_mode': 'request', 'template_id': ''})
        self.assertEqual(r.status, 200, r)
        self.assertIsNone(self.card(sid)['template'])
        # A template that does not exist or is switched off is not kept.
        sid2 = self.center.post('/api/provider-services', {'title': 'X', 'price': 1, 'booking_mode': 'request', 'template_id': 99999}).json['id']
        self.assertIsNone(self.server.sql('SELECT template_id FROM provider_services WHERE id=?', (sid2,))[0]['template_id'])


@unittest.skipIf(Image is None, 'Pillow no está instalado')
class MigracionUnaVez(unittest.TestCase):
    """The services that existed before v50.53 are linked to their template once; one created later «Sin plantilla»
    keeps that choice after a restart. Nothing is deleted."""

    def test_existing_services_linked_once(self):
        first = Server().start()
        try:
            t = ServerTestCase('run'); ServerTestCase.server = first
            admin = t.make_admin(); center = t.make_center(admin, 'migra1')
            old = center.post('/api/provider-services', {'title': 'Curso Advanced Open Water 2 días', 'price': 300, 'booking_mode': 'request'}).json['id']
            mine = center.post('/api/provider-services', {'title': 'Bautizo de buceo', 'price': 60, 'booking_mode': 'request'}).json['id']
            # «Before v50.53»: the first service has no template and the migration has not run.
            first.sql('UPDATE provider_services SET template_id=NULL')
            first.sql("DELETE FROM schema_migrations WHERE version='50.53'")
        finally:
            first.stop(cleanup=False)
        first.sql('PRAGMA wal_checkpoint(TRUNCATE)')     # the copy must carry what is still in the WAL file
        second = Server(seed=first.db).start()
        try:
            rows = {r['id']: r['template_id'] for r in second.sql('SELECT id,template_id FROM provider_services')}
            slug = {r['id']: r['slug'] for r in second.sql('SELECT id,slug FROM service_catalog')}
            self.assertEqual(slug[rows[old]], 'advanced')
            self.assertEqual(slug[rows[mine]], 'bautizo')
            note = second.sql("SELECT notes FROM schema_migrations WHERE version='50.53'")[0]['notes']
            self.assertIn('2 servicios vinculados', note)
            second.sql('UPDATE provider_services SET template_id=NULL WHERE id=?', (mine,))   # the centre chose «Sin plantilla»
        finally:
            second.stop(cleanup=False)
        second.sql('PRAGMA wal_checkpoint(TRUNCATE)')
        third = Server(seed=second.db).start()
        try:
            self.assertIsNone(third.sql('SELECT template_id FROM provider_services WHERE id=?', (mine,))[0]['template_id'])
            self.assertEqual(third.sql('SELECT COUNT(*) AS n FROM service_catalog')[0]['n'], 16)
        finally:
            third.stop()
            import shutil
            shutil.rmtree(first.tmp, ignore_errors=True); shutil.rmtree(second.tmp, ignore_errors=True)


if __name__ == '__main__':
    unittest.main()
