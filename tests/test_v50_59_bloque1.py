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
        for path in ('/api/center/bookings', '/api/provider/stats', '/api/pro/hoy', '/api/center/clients'):
            r = self.ana.get(path)
            self.assertEqual(r.status, 404, (path, r.status)); self.assertEqual(r.json.get('error'), 'No existe.')
        self.assertEqual(self.ana.get('/api/admin/dive-type-fields').status, 403)   # the administration's: refused as always
        self.assertEqual(self.ana.get('/api/center-equipment?center_id=1').status, 200)   # public: the booking shows the rental equipment
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


class Categorias(ServerTestCase):
    """1.5 · Reservar por categorías: la categoría de cada servicio (sola por su tipo, o la que elige el centro), los
    dudosos marcados, el orden del centro y, si no, de más barato a más caro, y las categorías en los 9 idiomas."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'ct59')
        cls.other = t.make_center(cls.admin, 'ct59b')
        mk = lambda c, **kw: c.post('/api/provider-services', {'booking_mode': 'request', **kw}).json['id']
        cls.doble = mk(cls.center, title='Doble inmersión', price=70, service_type='inmersion')
        cls.simple = mk(cls.center, title='Inmersión simple', price=40, service_type='inmersion')
        cls.ow = mk(cls.center, title='Open Water', price=420, service_type='curso')
        cls.bau = mk(cls.center, title='Bautizo de buceo', price=60, service_type='inmersion')
        cls.foreign = mk(cls.other, title='Inmersión ajena', price=30, service_type='inmersion')
        w = t.client().get(f"/widget/center/{cls.center.user['center_id']}")
        cls.slug = w.headers['Location'].split('/w/')[1].split('?')[0]

    def services(self):
        return self.center.get(f"/api/provider-services?provider_id=0&center_id={self.center.user['center_id']}").json['items']

    def test_1_category_by_kind_and_cheapest_first(self):
        by = {s['id']: s['category'] for s in self.services()}
        self.assertEqual((by[self.simple], by[self.doble], by[self.ow], by[self.bau]), ('inmersiones', 'inmersiones', 'cursos', 'bautizos'))
        w = self.client().get(f'/api/w/{self.slug}').json
        self.assertEqual([c['key'] for c in w['categories']][:5], ['inmersiones', 'cursos', 'bautizos', 'tours', 'otros'])
        dives = [s['id'] for s in w['services'] if s['category'] == 'inmersiones']
        self.assertEqual(dives, [self.simple, self.doble])   # without an order of the centre: the cheapest first

    def test_2_centre_changes_category_and_orders(self):
        self.assertEqual(self.center.post('/api/provider-services/category', {'id': self.bau, 'category': 'cursos'}).status, 200)
        self.assertEqual({s['id']: s['category'] for s in self.services()}[self.bau], 'cursos')
        self.assertEqual(self.center.post('/api/provider-services/category', {'id': self.bau, 'category': 'inventada'}).status, 400)
        self.assertEqual(self.center.post('/api/provider-services/category', {'id': self.foreign, 'category': 'cursos'}).status, 404)   # not its service
        self.assertEqual(self.center.post('/api/provider-services/order', {'ids': [self.doble, self.simple, self.foreign]}).status, 404)
        self.assertEqual(self.center.post('/api/provider-services/order', {'ids': [self.doble, self.simple]}).status, 200)
        w = self.client().get(f'/api/w/{self.slug}').json
        self.assertEqual([s['id'] for s in w['services'] if s['category'] == 'inmersiones'], [self.doble, self.simple])
        self.assertEqual(self.center.post('/api/provider-services/category', {'id': self.bau, 'category': 'bautizos'}).status, 200)

    def test_3_doubtful_services_of_before_are_marked(self):
        import sys; sys.path.insert(0, str(__import__('pathlib').Path(__file__).resolve().parents[1] / 'app'))
        from wod import categorias as wcat, servicios as wsv
        old = {'kind': None, 'service_type': 'experiencia', 'title': 'Salida especial', 'booking_unit': 'slot'}   # «Bautizo / experiencia» of before: snorkel or try dive?
        self.assertTrue(wcat.doubtful(old, wsv.kind_of(old)))
        self.assertFalse(wcat.doubtful({**old, 'service_type': 'curso'}, wsv.kind_of({**old, 'service_type': 'curso'})))
        self.assertFalse(wcat.doubtful({**old, 'kind': 'other'}, 'other'))   # chosen in the wizard: it is not doubtful
        self.assertEqual(len(self.server.sql("SELECT 1 FROM schema_migrations WHERE version='50.59-categorias'")), 1)

    def test_4_admin_configures_in_9_languages(self):
        d = self.admin.get('/api/admin/booking-categories').json
        self.assertEqual(len(d['langs']), 8)   # Spanish is the name itself
        self.assertIn(self.center.get('/api/admin/booking-categories').status, (403, 404))
        r = self.admin.post('/api/admin/booking-categories', {'key': 'tours', 'label': 'Tours y experiencias', 'icon': 'viaje', 'sort_order': 40,
                                                             'labels_i18n': {'en': 'Tours and experiences', 'de': 'Touren und Erlebnisse'}})
        self.assertEqual(r.status, 200, r.json)
        en = {c['key']: c for c in self.client().get('/api/booking-categories?lang=en').json['items']}
        self.assertEqual(en['tours']['label'], 'Tours and experiences')
        fr = {c['key']: c for c in self.client().get('/api/booking-categories?lang=fr').json['items']}
        self.assertEqual(fr['tours']['label'], 'Tours y experiencias')   # its French was cleared: Spanish, never empty
        self.assertEqual(self.admin.post('/api/admin/booking-categories', {'key': 'tours', 'label': '<b>x</b>', 'icon': 'viaje'}).status, 400)
        self.assertEqual(self.admin.post('/api/admin/booking-categories', {'key': 'tours', 'label': 'X', 'icon': 'nada'}).status, 400)
        # hidden: its services go to the first category still shown, never lost
        self.assertEqual(self.admin.post('/api/admin/booking-categories', {'key': 'bautizos', 'label': 'Bautizos', 'icon': 'bautizo', 'sort_order': 30, 'active': 0}).status, 200)
        try:
            w = self.client().get(f'/api/w/{self.slug}').json
            self.assertNotIn('bautizos', [c['key'] for c in w['categories']])
            self.assertIn({s['id']: s['category'] for s in w['services']}[self.bau], [c['key'] for c in w['categories']])
        finally:
            self.admin.post('/api/admin/booking-categories', {'key': 'bautizos', 'label': 'Bautizos', 'icon': 'bautizo', 'sort_order': 30, 'active': 1})


class Gestoria(ServerTestCase):
    """1.6 · «Exportar para mi gestoría»: un Excel con 6 hojas siempre iguales, los totales que cuadran entre hojas y con
    el panel, los cobros del centro con su fecha, los impuestos por servicio (sin inventar ninguno), la plantilla del
    centro y el CSV de «Ventas» para Excel en español."""

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'ge59')
        cls.other = t.make_center(cls.admin, 'ge59b')
        cls.cid = cls.center.user['center_id']
        cls.server.sql("UPDATE centers SET country='España', region='Alicante', legal_name='Buceo Gestoría SL', tax_id='B00000000' WHERE id=?", (cls.cid,))
        mk = lambda **kw: cls.center.post('/api/provider-services', {'booking_mode': 'request', **kw}).json['id']
        cls.dive = mk(title='Inmersión en barco', price=50, service_type='inmersion')
        cls.course = mk(title='Curso Open Water', price=300, service_type='curso')
        man = lambda sid, d, n, pay, **kw: cls.center.post('/api/center/bookings/manual', {'fullname': f'Cliente {d}', 'email': f'c{d}{n}@diver.example.org', 'service_id': sid,
                                                                                          'booking_date': d, 'participants': n, 'payment_status': pay, **kw}).json
        cls.b1 = man(cls.dive, DAY(5), 2, 'paid', payment_method='efectivo')['id']                 # paid at the desk when writing it: 100 €
        cls.b2 = man(cls.course, DAY(6), 1, 'required')['id']                                        # paid later at the desk, card terminal
        r = cls.center.post(f'/api/bookings/{cls.b2}/payment', {'payment_status': 'paid', 'payment_method': 'card', 'reference': 'TPV-778'})
        assert r.status == 200, r.json
        cls.b3 = man(cls.dive, DAY(7), 1, 'required')['id']                                          # of before: paid, no payment recorded, part refunded
        cls.server.sql("UPDATE bookings SET payment_status='paid', payment_method='cash', amount_paid=50, refunded_total=20, status='confirmed' WHERE id=?", (cls.b3,))
        cls.b4 = cls.other.post('/api/center/bookings/manual', {'fullname': 'Ajeno', 'email': 'ajeno@diver.example.org', 'booking_date': DAY(5), 'payment_status': 'paid',
                                                                'service_id': cls.other.post('/api/provider-services', {'title': 'X', 'price': 999, 'booking_mode': 'request'}).json['id']}).json['id']
        cls.wide = {'periodo': 'personalizado', 'desde': DAY(-400), 'hasta': DAY(400)}

    def q(self, **kw):
        return '?' + urllib.parse.urlencode({**self.wide, **kw})

    def test_1_totals_match_the_panel_and_between_sheets(self):
        s = self.center.get('/api/exportar/gestoria' + self.q(fecha='servicio', vista=1)).json
        t = s['totals']
        self.assertEqual((t['reservas'], t['buceadores']), (3, 4))
        self.assertEqual((t['total'], t['centro'], t['online'], t['dev'], t['neto']), (450.0, 450.0, 0.0, 20.0, 430.0))
        income = sum(x['amount'] for x in self.center.get('/api/center/analytics').json['metrics']['income'])
        self.assertEqual(t['neto'], round(income, 2))   # the same figure as «Ingresos» in the panel, to the cent
        self.assertAlmostEqual(t['base'] + t['cuota'], t['total'], places=2)
        self.assertEqual(t['base'], round(sum(round(x / 1.21, 2) for x in (100, 300, 50)), 2))   # IVA 21 % included (general of Spain, not confirmed)
        self.assertTrue(any('sin confirmar' in p for p in s['pending']))
        self.assertTrue(any('Verifactu' in p for p in s['pending']))

    def test_2_by_payment_date_the_undated_ones_are_apart(self):
        s = self.center.get('/api/exportar/gestoria' + self.q(vista=1)).json
        self.assertEqual(s['mode'], 'cobro')
        self.assertEqual((s['totals']['reservas'], s['totals']['centro'], s['totals']['dev']), (2, 400.0, 0.0))   # 100 + 300 recorded today
        self.assertEqual(s['undated'], {'count': 2, 'paid': 50.0, 'refunded': 20.0})
        self.assertTrue(any('sin fecha registrada' in p for p in s['pending']))
        pays = self.server.sql('SELECT booking_id,amount,method,reference FROM booking_payments ORDER BY id')
        self.assertEqual([(p['booking_id'], p['amount'], p['reference']) for p in pays if p['booking_id'] in (self.b1, self.b2)], [(self.b1, 100.0, None), (self.b2, 300.0, 'TPV-778')])
        old = self.center.get('/api/exportar/gestoria' + self.q(vista=1, periodo='anio', valor=str(dt.date.today().year - 3))).json
        self.assertEqual(old['totals']['total'], 0.0)

    def test_3_the_excel_file(self):
        import io, re, zipfile
        r = self.center.get('/api/exportar/gestoria' + self.q(fecha='servicio'))
        self.assertEqual(r.status, 200)
        self.assertRegex(r.headers['Content-Disposition'], r'WORLDIVES_Ventas_Centro-ge59_.+\.xlsx')
        z = zipfile.ZipFile(io.BytesIO(r.body))
        wb = z.read('xl/workbook.xml').decode()
        self.assertEqual(re.findall(r'<sheet name="([^"]+)"', wb), ['Resumen', 'Ventas', 'Cobros', 'Devoluciones', 'Por servicio', 'Datos del informe'])
        ventas = z.read('xl/worksheets/sheet2.xml').decode()
        heads = re.findall(r'<c r="[A-Z]+1" s="1" t="inlineStr"><is><t>([^<]+)</t>', ventas)
        self.assertEqual(heads[:6], ['Fecha del servicio', 'Fecha del cobro', 'Número de reserva', 'Cliente', 'NIF del cliente', 'Servicio'])
        self.assertIn('state="frozen"', ventas); self.assertIn('<autoFilter', ventas)
        self.assertIn('>Total<', ventas)                                     # the totals row, in bold
        self.assertNotIn('Ajeno', z.read('xl/worksheets/sheet2.xml').decode())   # only its own bookings
        datos = z.read('xl/worksheets/sheet6.xml').decode()
        self.assertIn('B00000000', datos); self.assertIn('Pendiente de decisión', datos)
        c = self.center.get('/api/exportar/gestoria' + self.q(fecha='servicio', formato='csv'))
        self.assertTrue(c.body.startswith('﻿'.encode())); self.assertIn(b';', c.body); self.assertIn('100,00'.encode(), c.body)

    def test_4_taxes_and_template(self):
        tx = self.center.get('/api/provider-services/taxes').json
        self.assertEqual(tx['default'], {'rate': 21.0, 'name': 'IVA'})
        self.assertEqual(self.center.post('/api/provider-services/tax', {'items': [{'id': self.course, 'rate': 'x', 'name': 'IVA'}]}).status, 400)
        self.assertEqual(self.center.post('/api/provider-services/tax', {'items': [{'id': self.course, 'rate': 45, 'name': 'IVA'}]}).status, 400)
        self.assertEqual(self.other.post('/api/provider-services/tax', {'items': [{'id': self.course, 'rate': 0, 'name': 'IVA'}]}).status, 404)
        self.assertEqual(self.center.post('/api/provider-services/tax', {'items': [{'id': self.course, 'rate': 0, 'name': 'IVA'}, {'id': self.dive, 'rate': 21, 'name': 'IVA'}]}).status, 200)
        s = self.center.get('/api/exportar/gestoria' + self.q(fecha='servicio', vista=1)).json
        self.assertEqual(s['totals']['cuota'], round(sum(x - round(x / 1.21, 2) for x in (100, 50)), 2))   # the course, exempt by its gestoría
        self.assertFalse(any('sin confirmar' in p for p in s['pending']))
        self.assertEqual(self.center.post('/api/exportar/gestoria/plantilla', {'columns': ['cliente', 'total']}).status, 400)   # without the booking number
        self.assertEqual(self.center.post('/api/exportar/gestoria/plantilla', {'columns': ['reserva', 'cliente', 'total', 'inventada']}).status, 200)
        import io, re, zipfile
        z = zipfile.ZipFile(io.BytesIO(self.center.get('/api/exportar/gestoria' + self.q(fecha='servicio')).body))
        heads = re.findall(r'<c r="[A-Z]+1" s="1" t="inlineStr"><is><t>([^<]+)</t>', z.read('xl/worksheets/sheet2.xml').decode())
        self.assertEqual(heads, ['Número de reserva', 'Cliente', 'Total'])
        self.center.post('/api/exportar/gestoria/plantilla', {'reset': 1})
        self.assertIsNone(self.center.get('/api/exportar/gestoria/plantilla').json['columns'])

    def test_5_who_can(self):
        diver = self.make_diver('ge59d')
        self.assertIn(diver.get('/api/exportar/gestoria' + self.q()).status, (403, 404))
        self.assertIn(self.admin.get('/api/exportar/gestoria' + self.q()).status, (403, 404))
        s = self.other.get('/api/exportar/gestoria' + self.q(fecha='servicio', vista=1)).json
        self.assertEqual(s['totals']['total'], 999.0)   # only its own
        self.assertEqual(self.center.get('/api/exportar/gestoria?periodo=temporada&temporadas=2024,2025&vista=1').json['label'], 'temporada 2024-2025')
