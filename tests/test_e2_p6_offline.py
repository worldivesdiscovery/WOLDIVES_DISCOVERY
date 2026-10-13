"""Encargo 2, punto 6 (v50.42): the manifest of the day for the staff device (only today's or tomorrow's departures of
the centre, no documents) and the sync of check-ins, «no se presentó» and notes made without connection, with
conflicts when someone else changed the same thing meanwhile. Team roles (instructors check divers in)."""
import datetime as dt
import unittest

from helpers import MiddayClock, ServerTestCase

DAY = lambda n: (dt.date.today() + dt.timedelta(days=n)).isoformat()


class OfflineCheckin(MiddayClock, ServerTestCase):   # «today» at 23:59 must still be ahead
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'barco', phone='+34 600 470 001')
        cls.other = t.make_center(cls.admin, 'otrobarco', phone='+34 600 470 002')
        cls.cid = cls.center.user['center_id']
        sid = cls.center.post('/api/provider-services', {'title': 'Salida', 'price': 30, 'booking_mode': 'request'}).json['id']
        cls.today = cls.center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': DAY(0), 'slot_time': '23:59', 'spots_total': 8}).json['slot_id']
        cls.later = cls.center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': DAY(5), 'slot_time': '09:00', 'spots_total': 8}).json['slot_id']
        cls.diver = t.make_diver('barco6')
        cls.diver.post('/api/account/profile', {'certification_id': 2, 'emergency_contact_name': 'Rosa', 'emergency_contact_phone': '+34 600 000 001'})
        cls.bid = None
        for slot in (cls.today, cls.later):
            r = cls.diver.post('/api/bookings', {'center_id': cls.cid, 'service_id': sid, 'slot_id': slot, 'participants': 2})
            cls.server.sql("UPDATE bookings SET status='confirmed' WHERE id=?", (r.json['id'],))
            if slot == cls.today: cls.bid = r.json['id']
        # An instructor of the team
        cls.inst = t.make_diver('instbarco6')
        cls.server.sql("UPDATE users SET role='center', center_id=? WHERE id=?", (cls.cid, cls.inst.user['id']))
        cls.server.sql("INSERT INTO center_members(center_id,user_id,member_role,created_at) VALUES(?,?,'instructor','2026-01-01')", (cls.cid, cls.inst.user['id']))
        cls.inst.login('diver_instbarco6')

    def day(self, who=None, date=None):
        r = (who or self.center).get('/api/manifest/day' + (f'?date={date}' if date else ''))
        return r

    def test_1_day_bundle_only_today(self):
        r = self.day(); self.assertEqual(r.status, 200, r)
        d = r.json
        self.assertEqual([s['slot']['id'] for s in d['slots']], [self.today])     # nothing from other days
        rows = d['slots'][0]['divers']
        self.assertEqual(len(rows), 2)
        self.assertEqual(rows[0]['emergency'], {'name': 'Rosa', 'phone': '+34 600 000 001'})
        self.assertNotIn('documents', str(d))                                      # never documents
        self.assertEqual(self.day(date=DAY(1)).status, 200)                         # tomorrow, to prepare the evening before
        self.assertEqual(self.day(date=DAY(5)).status, 400)
        self.assertEqual(self.day(self.other).json['slots'], [])                    # another centre sees nothing of ours
        self.assertEqual(self.diver.get('/api/manifest/day').status, 403)
        self.assertEqual(self.day(self.inst).status, 200)

    def test_2_sync_and_conflicts(self):
        base = {'slot_id': self.today, 'booking_id': self.bid}
        # Offline on the boat: seat 1 present, seat 2 no-show with a note
        r = self.inst.post('/api/manifest/sync', {'changes': [{**base, 'seat': 1, 'field': 'status', 'base': '', 'value': 'present', 'offline': True},
                                                              {**base, 'seat': 2, 'field': 'status', 'base': '', 'value': 'no_show', 'offline': True},
                                                              {**base, 'seat': 2, 'field': 'note', 'base': '', 'value': 'Avisó tarde'}]})
        self.assertEqual((r.status, r.json['applied'], r.json['conflicts']), (200, 3, []), r)
        e = self.server.sql('SELECT seat,checked_in_at,no_show,note,checkin_source FROM manifest_entries WHERE booking_id=? ORDER BY seat', (self.bid,))
        self.assertTrue(e[0]['checked_in_at']); self.assertEqual((e[1]['no_show'], e[1]['note'], e[0]['checkin_source']), (1, 'Avisó tarde', 'offline'))
        # Meanwhile, at the desk, the owner marks seat 2 present; the boat (offline, still seeing «no_show») changes it to ''
        self.assertEqual(self.center.post('/api/manifest/sync', {'changes': [{**base, 'seat': 2, 'field': 'status', 'base': 'no_show', 'value': 'present'}]}).json['applied'], 1)
        r = self.inst.post('/api/manifest/sync', {'changes': [{**base, 'seat': 2, 'field': 'status', 'base': 'no_show', 'value': '', 'offline': True}]}).json
        self.assertEqual(r['applied'], 0); self.assertEqual(len(r['conflicts']), 1)
        self.assertEqual(r['conflicts'][0]['server_value'], 'present'); self.assertEqual(r['conflicts'][0]['server_by'], 'Gerente barco')
        # Same value on both sides is not a conflict
        self.assertEqual(self.inst.post('/api/manifest/sync', {'changes': [{**base, 'seat': 2, 'field': 'status', 'base': 'no_show', 'value': 'present'}]}).json['conflicts'], [])
        # «Keep mine» forces it
        r = self.inst.post('/api/manifest/sync', {'changes': [{**base, 'seat': 2, 'field': 'status', 'base': 'no_show', 'value': '', 'force': True}]}).json
        self.assertEqual(r['applied'], 1)
        # Permissions and bad data
        self.assertEqual(self.other.post('/api/manifest/sync', {'changes': [{**base, 'seat': 1, 'field': 'status', 'base': 'present', 'value': ''}]}).status, 404)  # v50.47 (B.3): what belongs to another centre does not exist (404)
        self.assertEqual(self.diver.post('/api/manifest/sync', {'changes': [{**base, 'seat': 1, 'field': 'status', 'base': 'present', 'value': ''}]}).status, 404)  # v50.47 (B.3)
        self.assertEqual(self.center.post('/api/manifest/sync', {'changes': [{**base, 'seat': 1, 'field': 'boat', 'value': 'x'}]}).status, 400)
        self.assertEqual(self.center.post('/api/manifest/sync', {'changes': [{**base, 'seat': 1, 'field': 'status', 'value': 'dormido'}]}).status, 400)
        self.assertEqual(self.center.post('/api/manifest/sync', {'changes': 'x'}).status, 400)
        self.assertIn('checkin_synced', {e['kind'] for e in self.center.get(f'/api/manifest/{self.today}').json['events']})


if __name__ == '__main__':
    unittest.main()
