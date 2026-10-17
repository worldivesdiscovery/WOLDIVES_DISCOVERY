"""v50.57 · Revisión general, Bloque 4.3: plantillas de servicio de la administración.

Icono elegido de entre todos los que existen (vista previa en la web), borrar la que nadie usa (con confirmación en la
web), archivar la que usa algún centro (deja de salir para servicios nuevos; los que la usan no cambian; se dice
cuántos centros la usan) y ordenar arrastrando."""
import unittest

from helpers import IN_PERSON, ServerTestCase


class Plantillas(ServerTestCase):

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'pl1')
        cls.pro = t.make_freelance(cls.admin, 'pl2')
        cls.diver = t.make_diver('pl3')

    def new(self, name, **kw):
        r = self.admin.post('/api/admin/service-catalog/save', {'names': {'es': name}, 'service_type': 'inmersion', **kw})
        self.assertEqual(r.status, 200, r.json)
        return r.json['id']

    def admin_item(self, tid):
        return next((x for x in self.admin.get('/api/admin/service-catalog').json['items'] if x['id'] == tid), None)

    def mine(self):
        return self.center.get(f"/api/provider-services?provider_id={self.center.user['id']}").json['items']

    def public_ids(self):
        return [x['id'] for x in self.client().get('/api/service-catalog').json['items']]

    def test_1_icono_de_entre_todos(self):
        icons = self.admin.get('/api/admin/service-catalog').json['icons']
        for k in ('inmersion', 'bautizo', 'curso', 'salida_privada', 'viaje', 'alquiler_equipo', 'fotografia', 'nocturna', 'snorkel'):
            self.assertIn(k, icons)                                                          # the ones the brief names, and the rest
        tid = self.new('Nocturna en la bahía', icon='nocturna')
        self.assertEqual(self.admin_item(tid)['icon'], 'nocturna')
        pub = next(x for x in self.client().get('/api/service-catalog').json['items'] if x['id'] == tid)
        self.assertEqual(pub['icon'], 'nocturna')
        # without an icon: the one of its type; one that does not exist: refused
        tid2 = self.new('Curso sin icono', service_type='curso')
        self.assertEqual(self.admin_item(tid2)['icon'], 'curso')
        r = self.admin.post('/api/admin/service-catalog/save', {'names': {'es': 'Mala'}, 'icon': 'calavera'})
        self.assertEqual(r.status, 400); self.assertIn('Icono', r.json['error'])
        r = self.admin.post('/api/admin/service-catalog/save', {'names': {'es': 'Mala'}, 'icon': ['nocturna']})
        self.assertEqual(r.status, 400)
        # a service made from it shows its icon on the card
        sid = self.center.post('/api/provider-services', {'title': 'Nocturna', 'price': 50, 'template_id': tid}).json['id']
        card = next(s for s in self.client().get(f"/api/centers/{self.center.user['center_id']}").json.get('services', []) if s['id'] == sid)
        self.assertEqual(card['template']['icon'], 'nocturna')

    def test_2_borrar_la_que_nadie_usa(self):
        tid = self.new('Creada por error')
        self.assertFalse(self.admin_item(tid)['in_use'])
        r = self.admin.post('/api/admin/service-catalog/delete', {'id': tid})
        self.assertEqual(r.status, 200, r.json); self.assertTrue(r.json['deleted'])
        self.assertIsNone(self.admin_item(tid)); self.assertNotIn(tid, self.public_ids())
        self.assertEqual(self.server.sql("SELECT COUNT(*) AS n FROM audit_log WHERE action='service_template_deleted' AND entity_id=?", (tid,))[0]['n'], 1)
        self.assertEqual(self.admin.post('/api/admin/service-catalog/delete', {'id': tid}).status, 404)

    def test_3_archivar_la_que_usa_un_centro(self):
        tid = self.new('Bautizo de mar', icon='bautizo')
        sid = self.center.post('/api/provider-services', {'title': 'Bautizo en Xàbia', 'price': 70, 'template_id': tid}).json['id']
        r = self.pro.post('/api/provider-services', {'title': 'Bautizo con instructor', 'price': 65, 'template_id': tid, **IN_PERSON})
        self.assertEqual(r.status, 200, r.json)
        item = self.admin_item(tid)
        self.assertEqual((item['in_use'], item['providers']), (2, 2))
        r = self.admin.post('/api/admin/service-catalog/delete', {'id': tid})
        self.assertEqual(r.status, 200, r.json)
        self.assertEqual((r.json.get('archived'), r.json['services'], r.json['providers']), (True, 2, 2))   # how many centres use it
        item = self.admin_item(tid)
        self.assertTrue(item['archived_at'])                                                 # still there, archived
        self.assertNotIn(tid, self.public_ids())                                             # not offered for new services
        # the existing service does not break: it keeps its template (name, icon) and can be edited
        svc = next(s for s in self.mine() if s['id'] == sid)
        self.assertEqual(svc['template_id'], tid)
        self.assertEqual(self.center.post('/api/provider-services/update', {'id': sid, 'title': 'Bautizo en Xàbia (2 h)', 'price': 75, 'template_id': tid}).status, 200)
        svc = next(s for s in self.mine() if s['id'] == sid)
        self.assertEqual((svc['template_id'], svc['title']), (tid, 'Bautizo en Xàbia (2 h)'))
        card = next(s for s in self.client().get(f"/api/centers/{self.center.user['center_id']}").json.get('services', []) if s['id'] == sid)
        self.assertEqual(card['template']['icon'], 'bautizo')
        # a new service can no longer start from it
        new = self.center.post('/api/provider-services', {'title': 'Otro bautizo', 'price': 70, 'template_id': tid}).json['id']
        self.assertIsNone(next(s for s in self.mine() if s['id'] == new)['template_id'])
        # archiving again keeps the first date; «Recuperar» offers it again
        first = item['archived_at']
        self.admin.post('/api/admin/service-catalog/delete', {'id': tid})
        self.assertEqual(self.admin_item(tid)['archived_at'], first)
        self.assertEqual(self.admin.post('/api/admin/service-catalog/restore', {'id': tid}).status, 200)
        self.assertIsNone(self.admin_item(tid)['archived_at']); self.assertIn(tid, self.public_ids())
        self.assertEqual(self.admin.post('/api/admin/service-catalog/restore', {'id': 999999}).status, 404)

    def test_4_una_plantilla_guardada_tambien_es_uso(self):
        tid = self.new('Snorkel familiar', icon='snorkel')
        r = self.center.post('/api/service-templates/save', {'name': 'Mi snorkel', 'service_type': 'inmersion', 'template_id': tid})
        self.assertEqual(r.status, 200, r.json)
        r = self.admin.post('/api/admin/service-catalog/delete', {'id': tid})
        self.assertTrue(r.json.get('archived'), r.json); self.assertEqual(r.json['providers'], 1)

    def test_5_ordenar_arrastrando(self):
        ids = [x['id'] for x in self.admin.get('/api/admin/service-catalog').json['items']]
        self.assertGreater(len(ids), 2)
        order = list(reversed(ids))
        r = self.admin.post('/api/admin/service-catalog/order', {'ids': order})
        self.assertEqual(r.status, 200, r.json)
        self.assertEqual([x['id'] for x in self.admin.get('/api/admin/service-catalog').json['items']], order)
        pub = self.public_ids()
        self.assertEqual(pub, [i for i in order if i in pub])                                # the centres see the same order
        # a new one goes at the end
        tid = self.new('La última')
        self.assertEqual(self.admin.get('/api/admin/service-catalog').json['items'][-1]['id'], tid)
        ids = order + [tid]
        for bad in (ids[:-1], ids + [ids[0]], [ids[0]] * len(ids), ids[:-1] + [999999], 'todo', None, ids[:-1] + ['x']):
            self.assertEqual(self.admin.post('/api/admin/service-catalog/order', {'ids': bad}).status, 400, bad)

    def test_6_solo_la_administracion(self):
        tid = self.new('Solo admin')
        for c in (self.center, self.pro, self.diver, self.client()):
            for path, body in (('/api/admin/service-catalog/delete', {'id': tid}), ('/api/admin/service-catalog/restore', {'id': tid}),
                               ('/api/admin/service-catalog/order', {'ids': [tid]})):
                self.assertIn(c.post(path, body).status, (401, 403), (path, c.user))
        self.assertIsNotNone(self.admin_item(tid))


if __name__ == '__main__':
    unittest.main()
