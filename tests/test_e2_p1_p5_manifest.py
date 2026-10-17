"""Encargo 2, puntos 1 y 5 (v50.40): departure manifest (boats with capacity, groups with a guide, automatic split by
level that the centre can change, maximum per guide, warnings, the data the crew needs and the emergency contact only
when the diver shares it) and the liability waiver (versions, drawn signature, PDF, marked in the manifest, no
health questions). Permissions between centres, team roles and divers."""
import json
import sys
import unittest

from helpers import ServerTestCase, ROOT

sys.path.insert(0, str(ROOT / 'app'))
from wod import manifest as wmf  # noqa: E402

PW = 'buceo-seguro-2026'
SIG = [[[0.1, 0.5], [0.2, 0.4], [0.3, 0.6], [0.4, 0.4], [0.5, 0.6], [0.6, 0.4], [0.7, 0.55], [0.8, 0.45]]]
WAIVER = 'Declaro que conozco los riesgos del buceo, que seguiré las instrucciones del guía y que el equipo de alquiler se me entrega revisado.'


class LevelsAndSuggestion(unittest.TestCase):
    def test_levels(self):
        self.assertEqual([wmf.level_of(x) for x in ('OWD', 'AOWD', 'RESCUE', 'Divemaster PADI', 'Instructor SSI', 'Bautizo', None, 'TEC / TECHNICAL')], [1, 2, 3, 4, 5, 0, 1, 3])

    def test_split_keeps_bookings_and_levels_apart(self):
        books = [{'id': 1, 'seats': [1, 2], 'level': 1}, {'id': 2, 'seats': [1], 'level': 2}, {'id': 3, 'seats': [1, 2, 3], 'level': 1},
                 {'id': 4, 'seats': [1], 'level': 3}, {'id': 5, 'seats': [1, 2, 3, 4, 5, 6], 'level': 2}]
        g = wmf.suggest(books, 4, [{'id': 10, 'capacity': 8}, {'id': 11, 'capacity': 12}], [{'user_id': 7, 'name': 'Ana'}, {'user_id': 8, 'name': 'Luis'}])
        self.assertTrue(all(len(x['members']) <= 4 for x in g))
        lvl = {b['id']: b['level'] for b in books}
        for x in g:   # beginners and experienced divers never in the same group
            self.assertEqual(len({wmf.band(lvl[b]) for b, _ in x['members']}), 1)
        flat = [m for x in g for m in x['members']]
        self.assertEqual(len(flat), 13); self.assertEqual(len(set(flat)), 13)
        self.assertEqual([x['guide_user_id'] for x in g[:2]], [7, 8]); self.assertIsNone(g[2]['guide_user_id'])
        # the 3 seats of booking 3 go in the same group
        self.assertEqual(len({i for i, x in enumerate(g) for b, _ in x['members'] if b == 3}), 1)


class Manifest(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'manif', phone='+34 600 400 001')
        cls.other = t.make_center(cls.admin, 'otromanif', phone='+34 600 400 002')
        cls.cid = cls.center.user['center_id']
        cls.sid = cls.center.post('/api/provider-services', {'title': 'Salida en barco', 'price': 50, 'booking_mode': 'request'}).json['id']
        cls.slot = cls.center.post('/api/provider-services/slot', {'service_id': cls.sid, 'slot_date': '2031-07-15', 'slot_time': '09:00', 'spots_total': 12}).json['slot_id']
        cls.divers = {}
        for tag, cert, pax, extra in (('ana5', 2, 1, {'emergency_contact_name': 'Pedro Ana', 'emergency_contact_phone': '+34 600 999 001', 'suit_size': 'M', 'fin_size': '40-41'}),
                                      ('bea5', 1, 2, {}), ('carlos5', 3, 1, {}), ('dani5', 1, 3, {})):
            d = t.make_diver(tag)
            d.post('/api/account/profile', {'certification_id': cert, 'phone': '+34 611 000 111', **extra})
            r = d.post('/api/bookings', {'center_id': cls.cid, 'service_id': cls.sid, 'slot_id': cls.slot, 'participants': pax, 'nitrox': tag == 'carlos5'})
            assert r.status == 200, r
            cls.server.sql("UPDATE bookings SET status='confirmed' WHERE id=?", (r.json['id'],))
            cls.divers[tag] = (d, r.json['id'])
        # A booking typed by the centre (guest customer, never shared data)
        cls.server.sql("UPDATE bookings SET source='manual' WHERE id=?", (cls.divers['dani5'][1],))

    def m(self, who=None):
        r = (who or self.center).get(f'/api/manifest/{self.slot}')
        self.assertEqual(r.status, 200, r)
        return r.json

    def test_1_manifest_rows_and_privacy(self):
        d = self.m()
        self.assertEqual(len(d['divers']), 7)          # 1 + 2 + 1 + 3 seats
        ana = [x for x in d['divers'] if x['booking_id'] == self.divers['ana5'][1]][0]
        self.assertEqual((ana['level_name'], ana['level']), ('AOWD', 2))
        self.assertEqual(ana['emergency'], {'name': 'Pedro Ana', 'phone': '+34 600 999 001'})
        self.assertEqual(ana['sizes']['suit_size'], 'M')
        carlos = [x for x in d['divers'] if x['booking_id'] == self.divers['carlos5'][1]][0]
        self.assertTrue(carlos['nitrox'])
        dani = [x for x in d['divers'] if x['booking_id'] == self.divers['dani5'][1] and x['seat'] == 1][0]
        self.assertIsNone(dani['emergency'])            # not shared: no emergency contact, no sizes
        self.assertIsNone(dani['sizes'])
        comp = [x for x in d['divers'] if x['booking_id'] == self.divers['bea5'][1] and x['seat'] == 2][0]
        self.assertIsNone(comp['level_name']); self.assertTrue(comp['companion_of'])
        self.assertTrue(any(w['kind'] == 'unassigned' for w in d['warnings']))

    def test_2_boats_groups_suggestion_and_warnings(self):
        c = self.center
        self.assertEqual(c.post('/api/manifest/boats/save', {'name': 'Neptuno', 'capacity': 0}).status, 400)
        b1 = c.post('/api/manifest/boats/save', {'name': 'Neptuno', 'capacity': 6}).json['id']
        b2 = c.post('/api/manifest/boats/save', {'name': 'Tritón', 'capacity': 10}).json['id']
        self.assertEqual(c.post(f'/api/manifest/{self.slot}/settings', {'max_per_guide': 0}).status, 400)
        self.assertEqual(c.post(f'/api/manifest/{self.slot}/settings', {'max_per_guide': 3}).status, 200)
        prev = c.post(f'/api/manifest/{self.slot}/suggest', {}).json
        self.assertEqual(prev['divers'], 7)
        self.assertEqual(self.server.sql('SELECT COUNT(*) n FROM slot_groups WHERE slot_id=?', (self.slot,))[0]['n'], 0)   # preview changes nothing
        r = c.post(f'/api/manifest/{self.slot}/suggest', {'apply': True}).json
        d = self.m()
        self.assertEqual(len(d['groups']), r['groups'])
        self.assertTrue(all(not x['group_id'] is None for x in d['divers']))
        self.assertTrue(all(g['count'] <= 3 for g in d['groups']))
        self.assertTrue({g['boat_id'] for g in d['groups']} <= {b1, b2, None})
        # Move a diver by hand into the first group: over the maximum per guide -> warning
        g0 = d['groups'][0]
        others = [x for x in d['divers'] if x['group_id'] != g0['id']][:2]
        self.assertEqual(c.post(f'/api/manifest/{self.slot}/assign', {'moves': [{'booking_id': x['booking_id'], 'seat': x['seat'], 'group_id': g0['id']} for x in others]}).status, 200)
        d = self.m()
        self.assertTrue(any(w['kind'] == 'over_guide' and w['ref'] == g0['id'] for w in d['warnings']))
        # Small boat over capacity
        c.post(f'/api/manifest/{self.slot}/groups/save', {'id': g0['id'], 'boat_id': b1, 'guide_name': 'Guía externo'})
        for g in d['groups'][1:]:
            c.post(f'/api/manifest/{self.slot}/groups/save', {'id': g['id'], 'boat_id': b1})
        d = self.m()
        self.assertTrue(any(w['kind'] == 'over_boat' for w in d['warnings']))
        # Rename a companion; the main diver cannot be renamed here
        comp = [x for x in d['divers'] if x['seat'] == 2][0]
        self.assertEqual(c.post(f'/api/manifest/{self.slot}/entry', {'booking_id': comp['booking_id'], 'seat': 2, 'name': 'Marta Acompañante'}).status, 200)
        self.assertEqual(c.post(f'/api/manifest/{self.slot}/entry', {'booking_id': comp['booking_id'], 'seat': 1, 'name': 'X'}).status, 400)
        # Delete a group: its divers go back to «sin grupo»
        self.assertEqual(c.post(f'/api/manifest/{self.slot}/groups/delete', {'id': g0['id']}).status, 200)
        d = self.m()
        self.assertTrue(any(x['group_id'] is None for x in d['divers']))

    def test_3_permissions(self):
        # Another centre: nothing
        self.assertEqual(self.other.get(f'/api/manifest/{self.slot}').status, 404)  # v50.47 (B.3): what belongs to another centre does not exist (404)
        self.assertEqual(self.other.post(f'/api/manifest/{self.slot}/suggest', {'apply': True}).status, 404)  # v50.47 (B.3)
        b_other = self.other.post('/api/manifest/boats/save', {'name': 'Ajeno', 'capacity': 8}).json['id']
        self.assertEqual(self.center.post('/api/manifest/boats/save', {'id': b_other, 'name': 'Robado', 'capacity': 8}).status, 404)  # v50.47 (B.3)
        g = self.center.post(f'/api/manifest/{self.slot}/groups/save', {}).json['id']
        self.assertEqual(self.center.post(f'/api/manifest/{self.slot}/groups/save', {'id': g, 'boat_id': b_other}).status, 404)  # v50.47 (B.3)
        # A diver: nothing
        diver = self.divers['ana5'][0]
        self.assertEqual(diver.get(f'/api/manifest/{self.slot}').status, 404)  # v50.47 (B.3)
        self.assertEqual(diver.post(f'/api/manifest/{self.slot}/assign', {'moves': [{'booking_id': 1, 'seat': 1}]}).status, 404)  # v50.47 (B.3)
        # Team: an instructor reads but cannot change the split
        inst = self.make_diver('instr5')
        uid = inst.user['id']
        self.server.sql("UPDATE users SET role='center', center_id=? WHERE id=?", (self.cid, uid))
        self.server.sql("INSERT OR REPLACE INTO center_members(center_id,user_id,member_role,created_at) VALUES(?,?,'instructor','2026-01-01')", (self.cid, uid))
        inst.login('diver_instr5')
        self.assertEqual(inst.get(f'/api/manifest/{self.slot}').status, 200)
        self.assertFalse(inst.get(f'/api/manifest/{self.slot}').json['can_edit'])
        self.assertEqual(inst.post(f'/api/manifest/{self.slot}/suggest', {'apply': True}).status, 403)
        # Bad data
        for body in ({'moves': []}, {'moves': 'x'}, {'moves': [{'booking_id': 'a'}]}):
            self.assertLess(self.center.post(f'/api/manifest/{self.slot}/assign', body).status, 500)
        self.assertEqual(self.center.post('/api/manifest/999999/suggest', {}).status, 404)  # v50.47: a departure that does not exist is 404


class Waiver(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'firma', phone='+34 600 400 011')
        cls.other = t.make_center(cls.admin, 'otrafirma', phone='+34 600 400 012')
        cls.cid = cls.center.user['center_id']
        sid = cls.center.post('/api/provider-services', {'title': 'Bautizo', 'price': 60, 'booking_mode': 'request'}).json['id']
        cls.slot = cls.center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-08-01', 'slot_time': '10:00', 'spots_total': 8}).json['slot_id']
        cls.diver = t.make_diver('firma5')
        cls.bid = cls.diver.post('/api/bookings', {'center_id': cls.cid, 'service_id': sid, 'slot_id': cls.slot, 'participants': 2}).json['id']
        cls.server.sql("UPDATE bookings SET status='confirmed' WHERE id=?", (cls.bid,))
        cls.stranger = t.make_diver('ajeno5')

    def sign(self, who, tpl, seat=1, name='Lucía Firma Pérez', strokes=SIG, accept=True):
        return who.post(f'/api/bookings/{self.bid}/waiver/sign', {'template_id': tpl, 'seat': seat, 'signer_name': name, 'strokes': strokes, 'accept': accept})

    def test_waiver_versions_signature_pdf_and_manifest(self):
        c = self.center
        self.assertIsNone(self.diver.get(f'/api/bookings/{self.bid}/waiver').json['waiver'])
        self.assertEqual(c.post('/api/provider/waiver', {'title': 'Descargo', 'body': 'corto'}).status, 400)
        self.assertEqual(c.post('/api/provider/waiver', {'title': 'Descargo', 'body': WAIVER, 'questions': [{'q': '¿Asma?'}]}).status, 403)   # no health questions
        v1 = c.post('/api/provider/waiver', {'title': 'Descargo de responsabilidad', 'body': WAIVER}).json
        self.assertEqual(v1['version'], 1)
        self.assertTrue(c.post('/api/provider/waiver', {'title': 'Descargo de responsabilidad', 'body': WAIVER}).json.get('unchanged'))
        w = self.diver.get(f'/api/bookings/{self.bid}/waiver').json
        self.assertEqual((w['waiver']['version'], w['can_sign'], w['participants']), (1, True, 2))
        # Bad data
        self.assertEqual(self.sign(self.diver, v1['id'], accept=False).status, 400)
        self.assertEqual(self.sign(self.diver, v1['id'], name='Lu').status, 400)
        self.assertEqual(self.sign(self.diver, v1['id'], strokes=[[[0.5, 0.5]]]).status, 400)
        self.assertEqual(self.sign(self.diver, v1['id'], strokes=[[[2, 5]]]).status, 400)
        self.assertEqual(self.sign(self.diver, v1['id'], seat=3).status, 400)
        self.assertEqual(self.sign(self.stranger, v1['id']).status, 403)
        self.assertEqual(self.sign(self.other, v1['id']).status, 403)
        # The centre changes the text: whoever had it open must read it again
        v2 = c.post('/api/provider/waiver', {'title': 'Descargo de responsabilidad', 'body': WAIVER + ' Versión revisada.'}).json
        self.assertEqual(v2['version'], 2)
        self.assertEqual(self.sign(self.diver, v1['id']).status, 400)
        r = self.sign(self.diver, v2['id'])
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.sign(self.diver, v2['id']).status, 400)                 # once per seat
        # The companion signs at the check-in, on the centre's device
        self.assertEqual(self.sign(c, v2['id'], seat=2, name='Marta Acompañante Ruiz').status, 200)
        sigs = self.server.sql('SELECT seat,method,version,body FROM waiver_signatures WHERE booking_id=? ORDER BY seat', (self.bid,))
        self.assertEqual([(s['seat'], s['method'], s['version']) for s in sigs], [(1, 'online', 2), (2, 'checkin', 2)])
        self.assertIn('Versión revisada', sigs[0]['body'])
        # PDF for the diver and for the centre, not for others
        pdf = self.diver.get(r.json['pdf_url'])
        self.assertEqual(pdf.status, 200); self.assertTrue(pdf.body.startswith(b'%PDF'))
        self.assertEqual(c.get(r.json['pdf_url']).status, 200)
        self.assertEqual(self.stranger.get(r.json['pdf_url']).status, 404)  # v50.47 (B.3)
        self.assertEqual(self.other.get(r.json['pdf_url']).status, 404)  # v50.47 (B.3)
        # The manifest shows who signed
        d = c.get(f'/api/manifest/{self.slot}').json
        self.assertTrue(all(x['signed'] for x in d['divers']))
        self.assertFalse(any(w['kind'] == 'unsigned' for w in d['warnings']))
        # Reception cannot change the text (owner only)
        hist = c.get('/api/provider/waiver').json
        self.assertEqual([x['version'] for x in hist['versions']], [2, 1]); self.assertEqual(hist['signed'], 2); self.assertFalse(hist['health_questions'])


if __name__ == '__main__':
    unittest.main()
