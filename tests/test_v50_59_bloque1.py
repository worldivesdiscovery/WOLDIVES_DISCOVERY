"""Encargo unificado del 17/10/2026 · Bloque 1 en el servidor.

1.2  Los datos propios de cada tipo de inmersión: los campos de cada tipo (configurables sin programar), los datos de
     las fuentes en los puntos de Xàbia y alrededores, lo vacío que no sale, la administración que los cambia, el centro
     que los propone y la administración que los acepta, el registro de fuentes y María Claudia que no es un pecio.
1.7  El buceador: las rutas de un profesional «no existen» para él (también la API a mano); Buddies que se aceptan o se
     rechazan; «¿Buceamos?» que abre WhatsApp entre los dos solo al aceptar; «Mi QR» del buceador para el check-in en el
     centro y para pedir ser Buddy; nadie ajeno ve ni contesta nada.
"""
from __future__ import annotations

import datetime as dt
import urllib.parse

from helpers import MiddayClock, ServerTestCase

DAY = lambda n: (dt.date.today() + dt.timedelta(days=n)).isoformat()


class TipoDatos(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'td59', phone='+34 600 590 911')
        cls.cid = cls.center.user['center_id']

    def point(self, name):
        return self.server.sql('SELECT * FROM dive_points WHERE name=? AND active=1', (name,))[0]

    def page(self, pid):
        return self.client().get(f'/api/dive-points/{pid}').json['item']

    def test_1_fields_of_the_brief_and_data_of_the_sources(self):
        rows = self.server.sql('SELECT type_key,field_key FROM dive_type_fields')
        keys = {(r['type_key'], r['field_key']) for r in rows}
        for k in (('pecios-y-naufragios', 'eslora'), ('pecios-y-naufragios', 'penetrable'), ('cuevas-y-cavernas', 'recorrido'), ('paredes', 'pared_desde'),
                  ('corrientes-y-deriva', 'direccion'), ('pinaculos', 'cima'), ('nocturnas', 'de_noche'), ('aguas-profundas', 'especialidad')):
            self.assertIn(k, keys)
        escull = self.page(self.point('Escull de Sant Pere (El Bergantí)')['id'])
        data = {x['label']: x['value'] for x in escull['type_data']}
        self.assertEqual(data, {'Longitud del recorrido': '25', 'La pared termina a': '31-33'})   # only what the source says
        self.assertTrue(all(x['value'] for x in escull['type_data']))
        masc = self.point('Acantilados del Mascarat (La Bodega)')
        self.assertEqual((masc['min_depth'], masc['current_level']), (3.0, 'variable'))
        self.assertEqual(self.point('La Barra (Les Marines)')['min_depth'], 7.0)
        self.assertEqual(self.page(self.point('El Tangó')['id'])['type_data'], [])   # nothing stated: nothing shown
        src = self.server.sql("SELECT * FROM point_sources WHERE point_id=? AND field='type'", (self.point('Escull de Sant Pere (El Bergantí)')['id'],))
        self.assertTrue(src and src[0]['kind'] == 'official' and 'Xàbia' in src[0]['note'])
        mc = self.server.sql("SELECT dive_type FROM dive_points WHERE name LIKE 'María Claudia%'")[0]['dive_type']
        self.assertNotIn('ecio', mc)
        # the migration is recorded once, and runs again without repeating anything
        self.assertEqual(len(self.server.sql("SELECT 1 FROM schema_migrations WHERE version='50.59-tipos'")), 1)

    def test_2_admin_configures_and_fills(self):
        r = self.admin.post('/api/admin/dive-type-fields', {'type_key': 'pecios-y-naufragios', 'label': 'Profundidad de la quilla', 'kind': 'number', 'unit': 'm'})
        self.assertEqual(r.status, 200, r.json); fid = r.json['id']
        self.assertEqual(self.admin.post('/api/admin/dive-type-fields', {'type_key': 'inventado', 'label': 'x'}).status, 400)
        self.assertIn(self.center.post('/api/admin/dive-type-fields', {'type_key': 'paredes', 'label': 'x'}).status, (403, 404))
        types = {t['key']: t for t in self.admin.get('/api/admin/dive-type-fields').json['types']}
        self.assertIn('Profundidad de la quilla', [f['label'] for f in types['pecios-y-naufragios']['fields']])
        # a wreck site: the administration writes its own data; a wrong number is refused; empty removes it
        r = self.admin.post('/api/dive-points', {'name': 'Pecio de prueba 59', 'country': 'España', 'dive_type': 'Pecio', 'latitude': 38.70, 'longitude': 0.25,
                                                 'difficulty': 'Intermedio', 'force_position': True, 'force_new': True, 'source_ref': 'Prueba', 'data_status': 'verified'})
        self.assertEqual(r.status, 200, r.json); pid = r.json['id']
        fields = {f['label']: f for f in self.admin.get(f'/api/admin/dive-points/{pid}').json['item']['type_fields']}
        self.assertIn('Eslora', fields); self.assertNotIn('Longitud del recorrido', fields)   # only the fields of its type
        ok = self.admin.post('/api/dive-points/update', {'id': pid, 'type_fields': {str(fields['Eslora']['id']): '32,5', str(fid): '18',
                                                                                     str(fields['Se puede penetrar']['id']): 'sí'}})
        self.assertEqual(ok.status, 200, ok.json)
        bad = self.admin.post('/api/dive-points/update', {'id': pid, 'type_fields': {str(fields['Eslora']['id']): 'mucha'}})
        self.assertEqual(bad.status, 400)
        page = {x['label']: x['value'] for x in self.page(pid)['type_data']}
        self.assertEqual(page, {'Eslora': '32.5', 'Se puede penetrar': 'si', 'Profundidad de la quilla': '18'})
        self.admin.post('/api/dive-points/update', {'id': pid, 'type_fields': {str(fid): ''}})
        self.assertNotIn('Profundidad de la quilla', {x['label'] for x in self.page(pid)['type_data']})
        # a hidden field keeps its value but stops showing
        self.admin.post('/api/dive-points/update', {'id': pid, 'type_fields': {str(fid): '18'}})
        self.admin.post('/api/admin/dive-type-fields', {'id': fid, 'active': 0})
        self.assertNotIn('Profundidad de la quilla', {x['label'] for x in self.page(pid)['type_data']})
        self.assertEqual(self.server.sql('SELECT value FROM dive_point_type_values WHERE point_id=? AND field_id=?', (pid, fid))[0]['value'], '18')

    def test_3_centre_proposes_admin_accepts(self):
        p = self.point('La Cullerà')
        self.server.sql("INSERT OR IGNORE INTO center_point_links(center_id,dive_point_id,created_at) VALUES(?,?,datetime('now'))", (self.cid, p['id']))
        defs = {f['label']: f['id'] for f in self.page(p['id'])['type_fields_def']}
        r = self.center.post(f"/api/dive-points/{p['id']}/propose", {'type_fields': {str(defs['Zona sin luz natural']): 'no'}, 'note': 'Lo vemos cada semana'})
        self.assertEqual(r.status, 200, r.json)
        self.assertNotIn('Zona sin luz natural', {x['label'] for x in self.page(p['id'])['type_data']})   # not before the review
        props = self.admin.get('/api/admin/dive-points/proposals').json['items']
        mine = [x for x in props if x['id'] == r.json['id']][0]
        self.assertEqual(mine['type_rows'][0]['label'], 'Zona sin luz natural'); self.assertEqual(mine['type_rows'][0]['new'], 'no')
        self.assertEqual(self.admin.post('/api/admin/dive-points/proposals/review', {'id': r.json['id'], 'decision': 'approve'}).status, 200)
        self.assertEqual({x['label']: x['value'] for x in self.page(p['id'])['type_data']}.get('Zona sin luz natural'), 'no')
        self.assertTrue(self.server.sql("SELECT 1 FROM point_sources WHERE point_id=? AND field='type' AND kind='centre'", (p['id'],)))
        # a diver cannot propose the own data of a type
        d = self.make_diver('td59d')
        r = d.post(f"/api/dive-points/{p['id']}/propose", {'type_fields': {str(defs['Longitud del recorrido']): '80'}})
        self.assertEqual(r.status, 400)


class Buceador(MiddayClock, ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'bz59', phone='+34 600 590 922')
        cls.cid = cls.center.user['center_id']
        cls.server.sql("UPDATE centers SET plan_code='pro',plan_status='active' WHERE id=?", (cls.cid,))
        cls.ana = t.make_diver('bz59ana'); cls.luis = t.make_diver('bz59luis'); cls.otro = t.make_diver('bz59otro')
        cls.ana.post('/api/account/profile', {'phone': '+34 611 590 101'})
        cls.luis.post('/api/account/profile', {'phone': '+34 611 590 202'})

    def test_1_professional_routes_do_not_exist(self):
        for path in ('/api/center/bookings', '/api/provider/stats', '/api/pro/hoy', '/api/admin/dive-type-fields', '/api/center/clients'):
            r = self.ana.get(path)
            self.assertEqual(r.status, 404, (path, r.status)); self.assertEqual(r.json.get('error'), 'No existe.')
        r = self.ana.post('/api/pro/escanear', {'code': 'x'})
        self.assertEqual(r.status, 404)
        self.assertEqual(self.ana.get('/api/buddies').status, 200)   # what is his works
        self.assertEqual(self.ana.get('/api/me/area').status, 200)

    def code_of(self, who):
        return self.server.sql('SELECT buddy_code FROM users WHERE id=?', (who.user['id'],))[0]['buddy_code'] or who.get('/api/logbook').json and \
            self.server.sql('SELECT buddy_code FROM users WHERE id=?', (who.user['id'],))[0]['buddy_code']

    def test_2_buddies_accept_and_buceamos(self):
        self.luis.get('/api/logbook')   # his buddy code exists
        r = self.ana.post('/api/buddies', {'code': self.code_of(self.luis)})
        self.assertEqual(r.status, 200, r.json); self.assertTrue(r.json['pending'])
        self.assertEqual(self.ana.get('/api/buddies').json['buddies'], [])             # not yet
        inc = self.luis.get('/api/buddies').json['incoming']
        self.assertEqual([x['name'] for x in inc], [self.ana.user['fullname']])
        self.assertEqual(self.otro.post('/api/buddies/answer', {'id': inc[0]['id'], 'accept': True}).status, 404)   # not his
        self.assertEqual(self.luis.post('/api/buddies/answer', {'id': inc[0]['id'], 'accept': True}).status, 200)
        mine = self.ana.get('/api/buddies').json
        self.assertEqual([x['name'] for x in mine['buddies']], [self.luis.user['fullname']])
        self.assertTrue(self.server.sql("SELECT 1 FROM messages WHERE recipient_user_id=? AND subject='Ya sois Buddies'", (self.ana.user['id'],)))
        # «¿Buceamos?»: no phone travels before accepting
        ref = mine['buddies'][0]['id']
        self.assertEqual(self.ana.post('/api/buddies/dive', {'buddies': [ref], 'date': DAY(-1)}).status, 400)
        r = self.ana.post('/api/buddies/dive', {'buddies': [ref], 'date': DAY(5), 'note': 'Si hace bueno'})
        self.assertEqual(r.json['sent'], 1)
        inv = self.luis.get('/api/buddies').json['invites_in']
        self.assertEqual(len(inv), 1); self.assertNotIn('611', str(inv))
        self.assertEqual(self.otro.post('/api/buddies/dive/answer', {'id': inv[0]['id'], 'accept': True}).status, 404)
        r = self.luis.post('/api/buddies/dive/answer', {'id': inv[0]['id'], 'accept': True})
        self.assertEqual(r.status, 200, r.json)
        url = urllib.parse.urlparse(r.json['whatsapp'])
        self.assertEqual((url.netloc, url.path), ('wa.me', '/34611590101'))     # Ana's own phone, only now
        msg = self.server.sql("SELECT body FROM messages WHERE recipient_user_id=? AND subject='¡Buceáis juntos!'", (self.ana.user['id'],))
        self.assertTrue(msg and 'wa.me/34611590202' in msg[0]['body'])
        # someone outside cannot invite Luis (he is not their buddy)
        self.assertEqual(self.otro.post('/api/buddies/dive', {'buddies': [ref], 'date': DAY(5)}).status, 404)
        # removing a buddy
        self.assertEqual(self.ana.post('/api/buddies/remove', {'ref': ref}).status, 200)
        self.assertEqual(self.luis.get('/api/buddies').json['buddies'], [])

    def test_3_mi_qr_check_in_and_buddy(self):
        sid = self.center.post('/api/provider-services', {'title': 'Doble 59', 'price': 40}).json['id']
        self.at_midday(sid)
        slot = self.center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': DAY(0), 'slot_time': '23:30', 'spots_total': 10}).json['slot_id']
        b = self.otro.post('/api/bookings', {'center_id': self.cid, 'service_id': sid, 'slot_id': slot, 'participants': 1})
        self.assertEqual(b.status, 200, b.json)
        self.server.sql("UPDATE bookings SET status='confirmed',payment_status='at_center' WHERE id=?", (b.json['id'],))
        q = self.otro.get('/api/my/qr').json
        r = self.center.post('/api/pro/escanear', {'code': q['token']})
        self.assertEqual(r.json['result'], 'ok', r.json); self.assertEqual(r.json['booking']['booking_id'], b.json['id'])
        self.assertEqual(self.center.post('/api/pro/escanear', {'code': q['token']}).json['result'], 'no_valido')   # one use
        q2 = self.luis.get('/api/my/qr').json   # Luis has no booking today here
        self.assertEqual(self.center.post('/api/pro/escanear', {'code': q2['token']}).json['result'], 'sin_reserva')
        # another diver scans «Mi QR»: a Buddy request
        q3 = self.otro.get('/api/my/qr').json
        r = self.ana.post('/api/buddies/qr', {'code': q3['token']})
        self.assertEqual(r.status, 200, r.json); self.assertEqual(r.json['status'], 'pending')
        self.assertEqual([x['name'] for x in self.otro.get('/api/buddies').json['incoming']], [self.ana.user['fullname']])
