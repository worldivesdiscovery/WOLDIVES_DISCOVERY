"""v50.54 · punto 8 del encargo del 14/10/2026: permisos de la administración.

- La administración edita el contenido de la plataforma (puntos, tipos, especies, portada…) y los centros del
  directorio que nadie gestiona todavía, pero NO el contenido de un centro con titular ni el de un freelance.
- Lo modera: lo oculta con un motivo; el titular recibe el aviso (en «Avisos» y por correo), lo corrige y lo envía a
  revisión; la administración lo vuelve a publicar tal como estaba o lo mantiene oculto con una nota. Todo queda en
  el registro de actividad (quién, cuándo, por qué).
- Datos personales: la administración solo ve lo que permiten las casillas de «Datos personales» (configurables sin
  tocar el código; por defecto, solo quién reserva y los correos). Cada acceso a datos personales queda registrado.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from helpers import Client, ServerTestCase  # noqa: E402


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


class PermisosAdministracion(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'mod')
        cls.cid = cls.center.user['center_id']
        cls.free = t.make_freelance(cls.admin, 'modfl')
        cls.diver = t.make_diver('moddiver')
        cls.sid = cls.center.post('/api/provider-services', {'title': 'Bautizo en la bahía', 'price': 40, 'booking_mode': 'request'}).json['id']
        slot = cls.center.post('/api/provider-services/slot', {'service_id': cls.sid, 'slot_date': day(5), 'slot_time': '10:00', 'spots_total': 8}).json['slot_id']
        r = cls.diver.post('/api/bookings', {'center_id': cls.cid, 'service_id': cls.sid, 'slot_id': slot, 'participants': 1})
        assert r.status == 200, r
        cls.bid = r.json['id']
        cls.server.sql("UPDATE bookings SET internal_notes='Nota interna del centro', contact_phone=wod_cifrar('+34 600 999 888') WHERE id=?", (cls.bid,))
        # a directory centre nobody has claimed: platform content
        cls.dir_cid = cls.server.sql("SELECT c.id FROM centers c WHERE NOT EXISTS(SELECT 1 FROM users u WHERE u.center_id=c.id) AND NOT EXISTS(SELECT 1 FROM center_members m WHERE m.center_id=c.id) LIMIT 1")[0]['id']

    def audit(self, action):
        return self.server.sql('SELECT * FROM audit_log WHERE action=? ORDER BY id', (action,))

    # ------------------------------------------------------------------ the administration does not edit their content
    def test_admin_cannot_edit_a_centre_with_owner(self):
        a = self.admin
        r = a.post('/api/centers/update', {'id': self.cid, 'name': 'Cambiado por la administración', 'country': 'España', 'latitude': 38.8, 'longitude': 0.17})
        self.assertEqual(r.status, 403); self.assertIn('la administración no lo modifica', r.json['error'])
        self.assertEqual(self.server.sql('SELECT name FROM centers WHERE id=?', (self.cid,))[0]['name'], 'Centro mod')
        for path, body in (('/api/center/extras/save', {'center_id': self.cid, 'name': 'Toalla', 'price': 2}),
                           ('/api/center-equipment', {'center_id': self.cid, 'code': 'fins', 'price': 5}),
                           ('/api/center-points/assign', {'center_id': self.cid, 'dive_point_id': 1}),
                           ('/api/qr/create', {'center_id': self.cid, 'purpose': 'center'}),
                           ('/api/travel-experiences', {'center_id': self.cid, 'title': 'Viaje', 'new_destination': 'Destino X'})):
            r = a.post(path, body)
            self.assertIn(r.status, (403,), (path, r))
        # its own content: the centre still edits it
        self.assertEqual(self.center.post('/api/center/extras/save', {'name': 'Toalla', 'price': 2}).status, 200)

    def test_admin_still_edits_platform_content(self):
        r = self.admin.post('/api/centers/update', {'id': self.dir_cid, 'name': 'Centro del directorio', 'country': 'España', 'latitude': 38.5, 'longitude': -0.1})
        self.assertEqual(r.status, 200, r)
        pid = self.server.sql('SELECT id FROM dive_points WHERE active=1 LIMIT 1')[0]['id']
        self.assertEqual(self.admin.post('/api/dive-points/conditions', {'id': pid, 'water_temp_min': 14}).status, 200)
        centres = self.admin.get('/api/centers').json['items']
        mine = next(c for c in centres if c['id'] == self.cid)
        self.assertTrue(mine['has_owner'])
        self.assertNotIn('has_owner', self.client().get('/api/centers').json['items'][0])   # only for the administration

    # ------------------------------------------------------------------ moderation: hide, tell, resubmit, publish again
    def test_hide_a_centre_and_publish_it_again(self):
        a, c = self.admin, self.center
        self.assertEqual(a.post('/api/admin/moderation/hide', {'target_type': 'center', 'target_id': self.cid, 'reason': 'corto'}).status, 400)
        r = a.post('/api/admin/moderation/hide', {'target_type': 'center', 'target_id': self.cid, 'reason': 'Las fotos de la ficha no son del centro.'})
        self.assertEqual(r.status, 200, r); case = r.json['id']
        self.assertEqual(a.post('/api/admin/moderation/hide', {'target_type': 'center', 'target_id': self.cid, 'reason': 'Otra vez el mismo motivo.'}).status, 400)
        self.assertNotIn(self.cid, [x['id'] for x in self.client().get('/api/centers').json['items']])
        self.assertEqual(self.client().get(f'/api/centers/{self.cid}').status, 404)
        self.assertEqual(c.get(f'/api/centers/{self.cid}').status, 200)          # its own panel keeps working
        # the owner is told: «Avisos» and an email, with the reason
        msg = self.server.sql("SELECT * FROM messages WHERE recipient_user_id=? AND kind='system' ORDER BY id DESC LIMIT 1", (c.user['id'],))[0]
        self.assertIn('Las fotos de la ficha no son del centro.', msg['body'])
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='moderation_hidden' AND related_id=?", (case,)))
        mine = c.get('/api/provider/moderation').json['items']
        self.assertEqual((mine[0]['id'], mine[0]['status'], mine[0]['reason']), (case, 'open', 'Las fotos de la ficha no son del centro.'))
        # nobody else answers for it
        other = self.make_center(a, 'otro')
        self.assertEqual(other.post('/api/provider/moderation/resubmit', {'id': case, 'note': 'Cambiadas las fotos'}).status, 404)
        self.assertEqual(c.post('/api/provider/moderation/resubmit', {'id': case, 'note': 'ok'}).status, 400)
        self.assertEqual(c.post('/api/provider/moderation/resubmit', {'id': case, 'note': 'He cambiado todas las fotos por las nuestras.'}).status, 200)
        # the administration is told at its contact address (Legal settings) and sees it first in «Moderación»
        self.assertEqual(self.admin.get('/api/admin/moderation').json['items'][0]['status'], 'resubmitted')
        self.assertEqual(self.client().get(f'/api/centers/{self.cid}').status, 404)   # still hidden until reviewed
        # kept hidden with a note, resubmitted again, published again
        self.assertEqual(a.post('/api/admin/moderation/keep', {'id': case, 'note': 'Falta la foto del barco.'}).status, 200)
        self.assertEqual(c.get('/api/provider/moderation').json['items'][0]['decision_note'], 'Falta la foto del barco.')
        self.assertEqual(c.post('/api/provider/moderation/resubmit', {'id': case, 'note': 'Añadida la foto del barco.'}).status, 200)
        self.assertEqual(a.post('/api/admin/moderation/restore', {'id': case, 'note': 'Correcto, gracias.'}).status, 200)
        self.assertEqual(self.client().get(f'/api/centers/{self.cid}').status, 200)
        self.assertEqual(a.post('/api/admin/moderation/restore', {'id': case}).status, 404)   # already closed
        steps = [r['action'] for r in self.server.sql("SELECT action FROM audit_log WHERE action LIKE 'moderation_%' AND entity_id=? ORDER BY id", (self.cid,))]
        self.assertEqual(steps, ['moderation_hidden', 'moderation_resubmitted', 'moderation_kept', 'moderation_resubmitted', 'moderation_restored'])
        hidden = self.audit('moderation_hidden')[-1]
        self.assertEqual(json.loads(hidden['details'])['reason'], 'Las fotos de la ficha no son del centro.')
        self.assertEqual(hidden['user_id'], a.me()['user']['id'])

    def test_hide_a_service_the_centre_cannot_republish_it_alone(self):
        a, c = self.admin, self.center
        sid = c.post('/api/provider-services', {'title': 'Nocturna con linterna', 'price': 45, 'booking_mode': 'request'}).json['id']
        case = a.post('/api/admin/moderation/hide', {'target_type': 'service', 'target_id': sid, 'reason': 'El precio no incluye el seguro obligatorio.'}).json['id']
        self.assertEqual(self.server.sql('SELECT active FROM provider_services WHERE id=?', (sid,))[0]['active'], 0)
        r = c.post('/api/provider-services/update', {'id': sid, 'title': 'Nocturna con linterna', 'price': 45, 'booking_mode': 'request', 'active': 1})
        self.assertEqual(self.server.sql('SELECT active FROM provider_services WHERE id=?', (sid,))[0]['active'], 0, r)
        a.post('/api/admin/moderation/restore', {'id': case})
        self.assertEqual(self.server.sql('SELECT active FROM provider_services WHERE id=?', (sid,))[0]['active'], 1)

    def test_hide_a_freelance_profile(self):
        a, f = self.admin, self.free
        uid = f.user['id']
        self.assertEqual(self.client().get(f'/api/providers/{uid}').status, 200)
        case = a.post('/api/admin/moderation/hide', {'target_type': 'freelance', 'target_id': uid, 'reason': 'La titulación que muestra no es válida.'}).json['id']
        self.assertEqual(self.client().get(f'/api/providers/{uid}').status, 404)
        self.assertEqual(f.get('/api/provider/moderation').json['items'][0]['id'], case)
        a.post('/api/admin/moderation/restore', {'id': case})
        self.assertEqual(self.client().get(f'/api/providers/{uid}').status, 200)

    def test_moderation_is_for_the_administration_only(self):
        self.assertEqual(self.center.post('/api/admin/moderation/hide', {'target_type': 'center', 'target_id': self.cid, 'reason': 'Me oculto a mí mismo.'}).status, 403)
        self.assertEqual(self.center.get('/api/admin/moderation').status, 403)
        self.assertEqual(self.diver.get('/api/provider/moderation').status, 403)

    # ------------------------------------------------------------------ personal data under switches, every access logged
    def test_bookings_without_private_data_by_default(self):
        b = next(x for x in self.admin.get('/api/bookings').json['items'] if x['id'] == self.bid)
        self.assertNotIn('internal_notes', b); self.assertNotIn('contact_phone', b)
        self.assertTrue(b.get('email'))                                         # who booked: open by default (support)
        r = self.admin.get(f'/api/bookings/{self.bid}'); self.assertEqual(r.status, 200, r); detail = r.json
        self.assertEqual(detail['profile'], {}); self.assertEqual(detail['documents'], [])
        self.assertNotIn('internal_notes', detail['booking'])
        for path in (f'/api/bookings/{self.bid}/waiver', f'/api/bookings/{self.bid}/diver-sheet.pdf', f'/api/center/clients?center_id={self.cid}'):
            r = self.admin.get(path)
            self.assertEqual(r.status, 403, path); self.assertIn('privacidad', r.json['error'])

    def test_switches_change_it_and_are_logged(self):
        a = self.admin
        self.assertEqual(a.post('/api/admin/data-permissions', {'allowed': {'telefonos': True}, 'reason': 'corto'}).status, 400)
        r = a.post('/api/admin/data-permissions', {'allowed': {'telefonos': True, 'notas_internas': True, 'clientes_centro': True}, 'reason': 'Prueba de soporte con el centro mod.'})
        self.assertEqual(r.status, 200, r)
        try:
            b = next(x for x in a.get('/api/bookings').json['items'] if x['id'] == self.bid)
            self.assertEqual(b['internal_notes'], 'Nota interna del centro'); self.assertEqual(b['contact_phone'], '+34 600 999 888')
            a.admin_reason = 'Llamada del centro mod por una reserva'
            self.assertEqual(a.get(f'/api/center/clients?center_id={self.cid}').status, 200)
            row = self.audit('admin_personal_data')[-1]
            det = json.loads(row['details'])
            self.assertEqual((det['permiso'], det['reason']), ('clientes_centro', 'Llamada del centro mod por una reserva'))
            change = json.loads(self.audit('admin_data_permissions')[-1]['details'])
            self.assertEqual(change['cambios']['telefonos'], {'antes': False, 'ahora': True})
            perms = {p['key']: p['allowed'] for p in a.get('/api/admin/data-permissions').json['items']}
            self.assertTrue(perms['telefonos']); self.assertFalse(perms['formularios_firmados'])
        finally:
            a.admin_reason = 'pruebas automáticas'
            a.post('/api/admin/data-permissions', {'allowed': {'telefonos': False, 'notas_internas': False, 'clientes_centro': False}, 'reason': 'Vuelta a la configuración inicial.'})

    def test_admin_lists_with_personal_data_are_logged(self):
        before = len(self.audit('admin_personal_data'))
        self.admin.get('/api/admin/users'); self.admin.get('/api/admin/center-claims')
        after = self.audit('admin_personal_data')
        self.assertEqual(len(after), before + 2)
        self.assertIn('lista de cuentas', json.loads(after[-2]['details'])['what'])
        self.assertEqual(self.center.post('/api/admin/data-permissions', {'allowed': {'telefonos': True}, 'reason': 'Un centro no puede.'}).status, 403)

    def test_reading_booking_contacts_is_logged(self):
        # the name and email of whoever booked (open by default for support) are personal data: each read is logged
        before = len(self.audit('admin_personal_data'))
        self.admin.admin_reason = 'Incidencia de pago de la reserva'
        self.admin.get('/api/bookings'); self.admin.get(f'/api/bookings/{self.bid}')
        rows = self.audit('admin_personal_data')[before:]
        whats = [json.loads(r['details'])['what'] for r in rows]
        self.assertEqual(len(rows), 2, whats)
        self.assertIn('lista de reservas', whats[0]); self.assertIn(f'reserva {self.bid}', whats[1])
        self.assertEqual(json.loads(rows[1]['details'])['reason'], 'Incidencia de pago de la reserva')
        # the centre reading its own bookings is not an administration access
        self.center.get('/api/bookings')
        self.assertEqual(len(self.audit('admin_personal_data')), before + 2)

    def test_payments_and_email_lists_follow_the_rules(self):
        self.server.sql("INSERT INTO payment_orders(user_id,booking_id,amount,currency,status,created_at,updated_at,payee_type,payee_id) "
                        "VALUES((SELECT user_id FROM bookings WHERE id=?),?,42,'EUR','paid',datetime('now'),datetime('now'),'center',?)", (self.bid, self.bid, self.cid))
        before = len(self.audit('admin_personal_data'))
        items = self.admin.get('/api/admin/payments').json['items']
        self.assertTrue(items and items[0].get('email'))                       # open by default (support and payments)…
        self.admin.get('/api/admin/emails')
        whats = [json.loads(r['details'])['what'] for r in self.audit('admin_personal_data')[before:]]
        self.assertTrue(any('lista de pagos' in w for w in whats), whats)         # …and logged
        r = self.admin.post('/api/admin/data-permissions', {'allowed': {'contacto_reservas': False}, 'reason': 'Prueba de privacidad de pagos.'})
        self.assertEqual(r.status, 200, r)
        try:
            item = self.admin.get('/api/admin/payments').json['items'][0]
            self.assertNotIn('email', item); self.assertLessEqual(len(item['fullname'].split()), 2)   # closed: first name and initial
        finally:
            self.admin.post('/api/admin/data-permissions', {'allowed': {'contacto_reservas': True}, 'reason': 'Vuelve a como estaba.'})


if __name__ == '__main__':
    unittest.main()
