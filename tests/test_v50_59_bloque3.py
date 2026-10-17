"""Encargo unificado del 17/10/2026 · Bloque 3: freelance en Experiencias (servidor).

3.2  Aparece todo freelance aprobado (gratuito o Pro) con foto, nombre, zona y una titulación, si no ha apagado
     «Aparecer en el directorio»; al que le falta algo se le dice qué.
3.3  La tarjeta, sin dirección, teléfono ni correo; filtros por zona, idioma, agencia, tipo de servicio y fecha; cerca de
     un punto; límite de consultas por IP.
3.4  «Mis profesionales»: solo con una reserva confirmada; los botones de contacto que el profesional activó, nunca a
     quien bloqueó; el buceador lo quita de su lista.
"""
from __future__ import annotations

import datetime as dt
import json

from helpers import ServerTestCase

DAY = lambda n: (dt.date.today() + dt.timedelta(days=n)).isoformat()


class Freelance(ServerTestCase):
    extra_env = {'WOD_FREELANCE_DIR_PER_HOUR': '40'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.ana = t.make_freelance(cls.admin, 'fl59a')
        cls.bea = t.make_freelance(cls.admin, 'fl59b')
        cls.diver = t.make_diver('fl59d')
        cls.other = t.make_diver('fl59e')
        cls.server.sql("INSERT INTO provider_services(provider_user_id,title,price,currency,booking_mode,service_type,active,created_at,updated_at) "
                       "VALUES(?,'Curso Open Water',350,'EUR','request','curso',1,datetime('now'),datetime('now'))", (cls.ana.user['id'],))
        sid = cls.server.sql('SELECT id FROM provider_services WHERE provider_user_id=?', (cls.ana.user['id'],))[0]['id']
        cls.server.sql("INSERT INTO service_slots(service_id,slot_date,slot_time,spots_total,spots_available,status,created_at,updated_at) VALUES(?,?,?,?,?,?,datetime('now'),datetime('now'))",
                       (sid, DAY(3), '09:00', 4, 4, 'open'))
        cls.sid = sid
        cls.server.sql("UPDATE users SET plan_code=NULL WHERE id IN (?,?)", (cls.ana.user['id'], cls.bea.user['id']))   # free plan: also in the directory (owner, 17/10)

    def directory(self, **q):
        import urllib.parse
        return self.client().get('/api/freelance?' + urllib.parse.urlencode(q)).json['items']

    def test_1_needs_the_minimum(self):
        own = self.ana.get('/api/freelance/perfil').json
        self.assertEqual(set(own['missing']), {'foto', 'zona donde trabajas', 'al menos una titulación profesional'})
        self.assertNotIn(self.ana.user['id'], [x['id'] for x in self.directory()])
        self.server.sql("UPDATE users SET avatar_url='/img/demo/avatar.webp' WHERE id=?", (self.ana.user['id'],))
        r = self.ana.post('/api/freelance/perfil', {'kind': 'instructor', 'zone': 'Xàbia, Alicante', 'lat': 38.79, 'lon': 0.17, 'languages': ['es', 'en', 'xx'],
                                                    'contact_whatsapp': 1, 'contact_email': 1})
        self.assertEqual(r.status, 200, r.json); self.assertEqual(r.json['missing'], ['al menos una titulación profesional'])
        self.assertEqual(self.ana.post('/api/freelance/titulacion', {'agency': 'Inventada', 'level': 'X'}).status, 400)
        r = self.ana.post('/api/freelance/titulacion', {'agency': 'PADI', 'level': 'Open Water Scuba Instructor', 'number': '123456'})
        self.assertEqual(r.status, 200); self.assertTrue(r.json['listed'])
        card = [x for x in self.directory() if x['id'] == self.ana.user['id']][0]
        self.assertEqual((card['kind_label'], card['zone'], card['languages'], card['price_from']), ('Instructor', 'Xàbia, Alicante', ['es', 'en'], 350.0))
        self.assertEqual(card['certifications'], [{'agency': 'PADI', 'level': 'Open Water Scuba Instructor', 'verified': False}])
        text = json.dumps(self.directory())
        for secret in ('fl59a@pro.example.org', '611 000 000', '123456'): self.assertNotIn(secret, text)   # no email, phone or number
        # the administration verifies the qualification
        cid = self.server.sql('SELECT id FROM pro_certifications WHERE user_id=?', (self.ana.user['id'],))[0]['id']
        self.assertIn(self.diver.post(f'/api/admin/freelance-titulaciones/{cid}', {'verified': 1}).status, (403, 404))
        self.assertEqual(self.admin.post(f'/api/admin/freelance-titulaciones/{cid}', {'verified': 1}).status, 200)
        self.assertTrue([x for x in self.directory() if x['id'] == self.ana.user['id']][0]['certifications'][0]['verified'])
        # switched off: it disappears at once
        self.ana.post('/api/freelance/perfil', {'kind': 'instructor', 'zone': 'Xàbia, Alicante', 'lat': 38.79, 'lon': 0.17, 'in_directory': 0})
        self.assertNotIn(self.ana.user['id'], [x['id'] for x in self.directory()])
        self.ana.post('/api/freelance/perfil', {'kind': 'instructor', 'zone': 'Xàbia, Alicante', 'lat': 38.79, 'lon': 0.17, 'languages': ['es', 'en'],
                                                'contact_whatsapp': 1, 'contact_email': 1})
        self.assertIn(self.diver.get('/api/freelance/perfil').status, (403, 404))

    def test_2_filters(self):
        self.test_1_needs_the_minimum() if not self.server.sql('SELECT 1 FROM pro_certifications WHERE user_id=?', (self.ana.user['id'],)) else None
        me = self.ana.user['id']
        ids = lambda **q: [x['id'] for x in self.directory(**q)]
        self.assertIn(me, ids(zona='xabia')); self.assertNotIn(me, ids(zona='Lanzarote'))
        self.assertIn(me, ids(idioma='en')); self.assertNotIn(me, ids(idioma='de'))
        self.assertIn(me, ids(agencia='PADI')); self.assertNotIn(me, ids(agencia='SSI'))
        self.assertIn(me, ids(tipo='cursos')); self.assertNotIn(me, ids(tipo='bautizos'))
        self.assertIn(me, ids(fecha=DAY(3))); self.assertNotIn(me, ids(fecha=DAY(4)))
        granadella = self.server.sql("SELECT id FROM dive_points WHERE name='La Granadella' AND active=1")[0]['id']
        cies = self.server.sql("SELECT id FROM dive_points WHERE name LIKE 'Islas Cíes%' AND active=1")[0]['id']
        self.assertIn(me, ids(punto=granadella)); self.assertNotIn(me, ids(punto=cies))

    def test_3_my_professionals_and_contact(self):
        self.test_1_needs_the_minimum() if not self.server.sql('SELECT 1 FROM pro_certifications WHERE user_id=?', (self.ana.user['id'],)) else None
        self.ana.post('/api/account/profile', {'phone': '+34 611 590 777'})
        self.assertEqual(self.diver.get('/api/mis-profesionales').json['items'], [])   # nothing booked: nothing, and no contact
        mk = lambda uid, st: self.server.sql("INSERT INTO bookings(user_id,provider_user_id,service_id,booking_date,status,participants,price,currency,created_at,updated_at) "
                                             "VALUES(?,?,?,?,?,1,350,'EUR',datetime('now'),datetime('now'))", (uid, self.ana.user['id'], self.sid, DAY(-5), st))
        mk(self.other.user['id'], 'requested')
        self.assertEqual(self.other.get('/api/mis-profesionales').json['items'], [])   # a request is not a confirmed booking
        mk(self.diver.user['id'], 'completed')
        items = self.diver.get('/api/mis-profesionales').json['items']
        self.assertEqual(len(items), 1); p = items[0]
        self.assertEqual((p['kind'], p['id'], p['book']), ('freelance', self.ana.user['id'], f"#/reservar?provider={self.ana.user['id']}"))
        self.assertEqual(set(p['contact']), {'whatsapp', 'email'})   # the phone call was not switched on
        self.assertEqual(self.ana.post('/api/freelance/bloquear', {'user_id': self.diver.user['id']}).status, 200)
        self.assertEqual(self.diver.get('/api/mis-profesionales').json['items'][0]['contact'], {})
        self.assertEqual(self.ana.post('/api/freelance/bloquear', {'user_id': self.bea.user['id']}).status, 404)   # never booked with her
        self.ana.post('/api/freelance/bloquear', {'user_id': self.diver.user['id'], 'block': 0})
        self.assertEqual(self.diver.post('/api/mis-profesionales/quitar', {'kind': 'freelance', 'id': self.ana.user['id']}).status, 200)
        self.assertEqual(self.diver.get('/api/mis-profesionales').json['items'], [])

    def test_4_limit_per_ip(self):
        statuses = [self.client().get('/api/freelance').status for _ in range(45)]
        self.assertIn(429, statuses)


class CentroDeDemostracion(ServerTestCase):
    """17/10 · demo data: every centre page of the test package (WOD_DEMO_MODE=1) carries «Centro de demostración»; the real site never."""
    extra_env = {'WOD_DEMO_MODE': '1', 'STRIPE_SECRET_KEY': 'sk_test_no_se_usa'}

    def test_demo_flag(self):
        self.server.sql("INSERT INTO centers(name,country,city,active,verification_status,created_at,updated_at) VALUES('Centro inventado','España','Xàbia',1,'verified',datetime('now'),datetime('now'))")
        cid = self.server.sql("SELECT id FROM centers WHERE name='Centro inventado'")[0]['id']   # the demo accepts no new accounts
        self.assertIs(self.client().get(f'/api/centers/{cid}').json['item']['demo'], True)


class CentroReal(ServerTestCase):
    def test_no_demo_flag(self):
        admin = self.make_admin(); center = self.make_center(admin, 'real59')
        self.assertIs(self.client().get(f"/api/centers/{center.user['center_id']}").json['item']['demo'], False)
