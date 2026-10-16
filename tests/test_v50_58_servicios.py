"""v50.58 (revisión y usabilidad 15-16/10/2026, Parte 3): the services wizard on the server.

- The kinds, the plan of days of a course (full day, morning, afternoon), its editions and their sessions (pure helpers).
- Publishing checks everything and answers with the errors next to each field, in plain words.
- A draft is saved with whatever there is, is not public and is published later.
- A course with two editions: each one ends when its plan says and its instructor is busy those days, without overlaps.
- «Todos los sábados a las 9:00» creates the departures; a price per group does not multiply by the people.
- «Duplicar servicio» makes a draft copy. Services from before v50.58 keep working (their kind and plan come from them).
"""
import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from helpers import ServerTestCase  # noqa: E402
from wod import servicios as wsv  # noqa: E402

FAR = '2099-12-31'


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


def next_weekday(wd, after=10):
    d = dt.date.today() + dt.timedelta(days=after)
    while d.weekday() != wd: d += dt.timedelta(days=1)
    return d


class Helpers(unittest.TestCase):
    def test_plan_sessions_and_summary(self):
        plan = wsv.clean_plan({'preset': '2am2full'})
        self.assertEqual(plan['days'], ['am', 'am', 'full', 'full'])
        self.assertEqual(wsv.plan_summary(plan), '2 mañanas + 2 días completos')
        items = wsv.plan_items(plan)
        self.assertEqual(len(items), 6, 'a full day is a morning and an afternoon')
        self.assertEqual([(i['day'], i['part']) for i in items], [(0, 'am'), (1, 'am'), (2, 'am'), (2, 'pm'), (3, 'am'), (3, 'pm')])
        self.assertEqual(items[-1]['label'], 'Día 4 · tarde')
        self.assertEqual(wsv.plan_summary(wsv.clean_plan({'days': ['full'] * 3})), '3 días completos')
        self.assertEqual(wsv.plan_summary(wsv.clean_plan({'days': ['am'] * 4})), '4 mañanas')

    def test_edition_dates(self):
        plan = wsv.clean_plan({'days': ['full', 'full', 'full']})
        self.assertEqual(wsv.edition_end('2027-06-07', plan), '2027-06-09')   # «del lunes 7 al miércoles 9»
        spans = wsv.edition_spans('2027-06-07', wsv.clean_plan({'preset': '2am2full'}))
        self.assertEqual(spans[0], ('2027-06-07', '09:00', '13:00'))
        self.assertEqual(spans[2], ('2027-06-09', '09:00', '19:00'))
        self.assertEqual(wsv.weekly_dates([0], '2027-06-01', '2027-06-30'), ['2027-06-07', '2027-06-14', '2027-06-21', '2027-06-28'])

    def test_legacy_courses_get_their_days(self):
        self.assertEqual(wsv.plan_from_legacy('Curso Open Water (3 días)', 480)['days'], ['full'] * 3)
        self.assertEqual(wsv.plan_from_legacy('Advanced', 2880)['days'], ['full'] * 2)
        self.assertEqual(wsv.kind_of({'service_type': 'curso', 'title': 'X'}), 'course')
        self.assertEqual(wsv.kind_of({'service_type': 'experiencia', 'title': 'Bautizo de buceo'}), 'baptism')
        self.assertEqual(wsv.kind_of({'service_type': 'inmersion', 'booking_unit': 'half_day', 'title': 'Guía'}), 'guide')

    def test_errors_in_plain_words(self):
        _, e = wsv.check_form({'kind': 'course', 'title': 'Open Water'}, 'center', True, '2027-01-01')
        self.assertEqual(e['plan'], 'Pon cuántos días dura el curso.')
        self.assertIn('precio', e['price'])
        self.assertIn('plazas', e['max_participants'])
        _, e = wsv.check_form({'kind': 'dive', 'title': 'Doble'}, 'center', True, '2027-01-01')
        self.assertIn('cuánto dura', e['duration']); self.assertIn('hora de salida', e['start_time'])
        _, e = wsv.check_form({'kind': 'dive'}, 'center', False, '2027-01-01')
        self.assertEqual(set(e), {'title'}, 'a draft only needs a name (and is saved without one)')


class Wizard(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'asis')
        cls.cid = cls.center.user['center_id']
        cls.server.sql(f"UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}' WHERE id=?", (cls.cid,))
        for name in ('Marta Instructora', 'Leo Instructor'):
            cls.server.sql("INSERT INTO users(fullname,email,username,password_hash,role,center_id,created_at) VALUES(?,?,?,'!','center',?,datetime('now'))",
                           (name, name.split()[0].lower() + '@asis.example.org', 'ins_' + name.split()[0].lower(), cls.cid))
        rows = cls.server.sql("SELECT id, fullname FROM users WHERE username LIKE 'ins_%' ORDER BY id")
        cls.marta, cls.leo = rows[0]['id'], rows[1]['id']
        cls.diver = t.make_diver('asisdiver')

    def wizard(self, data):
        return self.center.post('/api/provider-services/wizard', data)

    def test_options(self):
        r = self.center.get('/api/provider-services/wizard-options')
        self.assertEqual(r.status, 200, r)
        self.assertIn('course', r.json['kinds'])
        self.assertIn(self.marta, [x['id'] for x in r.json['instructors']])

    def test_publish_incomplete_says_what_is_missing(self):
        r = self.wizard({'kind': 'course', 'title': 'Open Water', 'publish': True})
        self.assertEqual(r.status, 400, r)
        f = r.json['fields']
        self.assertEqual(f['plan'], 'Pon cuántos días dura el curso.')
        self.assertIn('price', f); self.assertIn('max_participants', f)
        self.assertEqual(self.server.sql("SELECT COUNT(*) AS n FROM provider_services WHERE title='Open Water'")[0]['n'], 0, 'nothing is saved')

    def test_draft_then_publish(self):
        r = self.wizard({'kind': 'baptism', 'title': 'Bautizo en playa', 'step': 2})
        self.assertEqual(r.status, 200, r); sid = r.json['id']
        row = self.server.sql('SELECT active, draft, kind FROM provider_services WHERE id=?', (sid,))[0]
        self.assertEqual((row['active'], row['draft'], row['kind']), (0, 1, 'baptism'))
        pub = self.diver.get(f'/api/provider-services?provider_id={self.center.user["id"]}').json['items']
        self.assertNotIn(sid, [x['id'] for x in pub], 'a draft is not public')
        sat = next_weekday(5)
        r = self.wizard({'id': sid, 'publish': True, 'kind': 'baptism', 'title': 'Bautizo en playa', 'hours': 2, 'minutes': 30, 'start_time': '10:00',
                         'price': 60, 'max_participants': 6, 'booking_mode': 'request', 'schedule': {'mode': 'dates', 'dates': [sat.isoformat()]}})
        self.assertEqual(r.status, 200, r)
        row = self.server.sql('SELECT active, draft, duration_minutes FROM provider_services WHERE id=?', (sid,))[0]
        self.assertEqual((row['active'], row['draft'], row['duration_minutes']), (1, 0, 150))
        self.assertEqual(self.server.sql('SELECT slot_date, slot_time FROM service_slots WHERE service_id=?', (sid,))[0]['slot_time'], '10:00')

    def test_course_with_two_editions_and_its_instructor(self):
        mon = next_weekday(0, 20)
        r = self.wizard({'publish': True, 'kind': 'course', 'title': 'Open Water 3 días', 'plan': {'preset': '3full'}, 'price': 450,
                         'max_participants': 4, 'booking_mode': 'request', 'instructor_user_id': self.marta,
                         'schedule': {'mode': 'dates', 'dates': [mon.isoformat(), (mon + dt.timedelta(days=7)).isoformat()]}})
        self.assertEqual(r.status, 200, r); sid = r.json['id']
        self.assertEqual(r.json['created'], 2)
        eds = self.server.sql('SELECT id, slot_date, date_to, instructor_user_id, kind, spots_total FROM service_slots WHERE service_id=? ORDER BY slot_date', (sid,))
        self.assertEqual([(e['slot_date'], e['date_to']) for e in eds], [(mon.isoformat(), (mon + dt.timedelta(days=2)).isoformat()),
                                                                       ((mon + dt.timedelta(days=7)).isoformat(), (mon + dt.timedelta(days=9)).isoformat())])
        self.assertEqual({e['kind'] for e in eds}, {'edition'}); self.assertEqual({e['spots_total'] for e in eds}, {4})
        blocks = self.server.sql("""SELECT b.local_date_from FROM resource_blocks b JOIN resources r ON r.id=b.resource_id
                                    WHERE r.user_id=? AND b.ref_type='edition' AND b.status='active' ORDER BY b.local_date_from""", (self.marta,))
        self.assertEqual(len(blocks), 6, 'three days of each edition: Marta is busy')
        svc = [x for x in self.center.get(f'/api/provider-services?provider_id={self.center.user["id"]}&include_inactive=1').json['items'] if x['id'] == sid][0]
        self.assertEqual(svc['plan_summary'], '3 días completos'); self.assertEqual(svc['kind'], 'course')
        # Another course with Marta on overlapping days: refused next to the instructor field
        r = self.wizard({'publish': True, 'kind': 'course', 'title': 'Advanced 2 días', 'plan': {'days': ['full', 'full']}, 'price': 300,
                         'max_participants': 4, 'booking_mode': 'request', 'instructor_user_id': self.marta,
                         'schedule': {'mode': 'dates', 'dates': [(mon + dt.timedelta(days=1)).isoformat()]}})
        self.assertEqual(r.status, 400, r); self.assertIn('ya tiene algo', r.json['fields']['instructor_user_id'])
        # Leo is free those days
        r = self.wizard({'publish': True, 'kind': 'course', 'title': 'Advanced con Leo', 'plan': {'days': ['full', 'full']}, 'price': 300,
                         'max_participants': 4, 'booking_mode': 'request', 'instructor_user_id': self.leo,
                         'schedule': {'mode': 'dates', 'dates': [(mon + dt.timedelta(days=1)).isoformat()]}})
        self.assertEqual(r.status, 200, r)
        # A diver books the first edition: the booking keeps its last day
        b = self.diver.post('/api/bookings', {'center_id': self.cid, 'service_id': sid, 'slot_id': eds[0]['id'], 'participants': 1})
        self.assertEqual(b.status, 200, b)
        self.assertEqual(self.server.sql('SELECT date_to FROM bookings WHERE id=?', (b.json['id'],))[0]['date_to'], eds[0]['date_to'])

    def test_every_saturday_and_price_per_group(self):
        a = next_weekday(5, 10); z = a + dt.timedelta(days=27)
        r = self.wizard({'publish': True, 'kind': 'dive', 'title': 'Salida privada en barco', 'hours': 4, 'minutes': 0, 'start_time': '09:00',
                         'price': 400, 'price_per': 'group', 'max_participants': 6, 'booking_mode': 'request',
                         'schedule': {'mode': 'weekly', 'weekdays': [5], 'from': a.isoformat(), 'to': z.isoformat()}})
        self.assertEqual(r.status, 200, r); sid = r.json['id']
        slots = self.server.sql('SELECT slot_date, slot_time FROM service_slots WHERE service_id=? ORDER BY slot_date', (sid,))
        self.assertEqual(len(slots), 4)
        self.assertTrue(all(dt.date.fromisoformat(s['slot_date']).weekday() == 5 and s['slot_time'] == '09:00' for s in slots))
        slot_id = self.server.sql('SELECT id FROM service_slots WHERE service_id=? ORDER BY slot_date LIMIT 1', (sid,))[0]['id']
        b = self.diver.post('/api/bookings', {'center_id': self.cid, 'service_id': sid, 'slot_id': slot_id, 'participants': 3})
        self.assertEqual(b.status, 200, b)
        self.assertEqual(self.server.sql('SELECT price FROM bookings WHERE id=?', (b.json['id'],))[0]['price'], 400, 'the group price, not 3 × 400')

    def test_rental_and_trip(self):
        r = self.wizard({'publish': True, 'kind': 'rental', 'title': 'Traje 5 mm', 'rental_per': 'dive', 'price': 12, 'booking_mode': 'request'})
        self.assertEqual(r.status, 200, r)
        row = self.server.sql('SELECT kind, service_type, rental_per FROM provider_services WHERE id=?', (r.json['id'],))[0]
        self.assertEqual((row['kind'], row['service_type'], row['rental_per']), ('rental', 'alquiler_equipo', 'dive'))
        r = self.wizard({'publish': True, 'kind': 'trip', 'title': 'Semana en el Mar Rojo', 'trip_from': day(60), 'trip_to': day(67), 'price': 1450,
                         'max_participants': 10, 'booking_mode': 'request'})
        self.assertEqual(r.status, 200, r)
        s = self.server.sql('SELECT slot_date, date_to, kind FROM service_slots WHERE service_id=?', (r.json['id'],))[0]
        self.assertEqual((s['slot_date'], s['date_to'], s['kind']), (day(60), day(67), 'trip'))

    def test_duplicate_is_a_draft_copy(self):
        r = self.wizard({'publish': True, 'kind': 'dive', 'title': 'Doble inmersión', 'hours': 4, 'start_time': '08:30', 'price': 70,
                         'max_participants': 8, 'booking_mode': 'request', 'languages': ['es', 'en'], 'includes': ['barco', 'guia']})
        self.assertEqual(r.status, 200, r)
        d = self.center.post('/api/provider-services/duplicate', {'id': r.json['id']})
        self.assertEqual(d.status, 200, d)
        row = self.server.sql('SELECT title, draft, active, languages, includes, price FROM provider_services WHERE id=?', (d.json['id'],))[0]
        self.assertEqual((row['title'], row['draft'], row['active'], row['price']), ('Doble inmersión (copia)', 1, 0, 70))
        self.assertEqual(row['languages'], '["es", "en"]')

    def test_another_centre_cannot_touch_it(self):
        r = self.wizard({'kind': 'dive', 'title': 'Mío'})
        other = self.make_center(self.admin, 'asisotro')
        self.assertEqual(other.post('/api/provider-services/wizard', {'id': r.json['id'], 'kind': 'dive', 'title': 'Robado'}).status, 404)
        self.assertEqual(other.post('/api/provider-services/duplicate', {'id': r.json['id']}).status, 404)


class FreelanceGuide(ServerTestCase):
    def test_guide_by_half_days(self):
        admin = self.make_admin(); pro = self.make_freelance(admin, 'asisguia')
        self.server.sql(f"UPDATE users SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}' WHERE id=?", (pro.user['id'],))
        r = pro.post('/api/provider-services/wizard', {'publish': True, 'kind': 'guide', 'title': 'Guía privado en cenotes', 'half_days': True,
                                                       'price': 180, 'half_price': 110, 'max_participants': 4, 'booking_mode': 'request',
                                                       'pay_way': 'in_person', 'pay_methods': ['cash']})
        self.assertEqual(r.status, 400, r)   # «Pago en persona» asks for its own data (WhatsApp, terms): said, nothing saved
        self.assertTrue(r.json.get('error'))
        r = pro.post('/api/provider-services/wizard', {'publish': True, 'kind': 'guide', 'title': 'Guía privado en cenotes', 'half_days': True,
                                                       'price': 180, 'half_price': 110, 'max_participants': 4, 'booking_mode': 'request',
                                                       'pay_way': 'in_person', 'pay_methods': ['cash'], 'pay_whatsapp': '+34 611 000 111',
                                                       'pay_policy': 'Gratis hasta 24 horas antes.', 'accept_in_person_terms': True})
        self.assertEqual(r.status, 200, r)
        row = self.server.sql('SELECT booking_unit, kind, pay_way, pricing FROM provider_services WHERE id=?', (r.json['id'],))[0]
        self.assertEqual((row['booking_unit'], row['kind'], row['pay_way']), ('half_day', 'guide', 'in_person'))
        self.assertIn('"half": 110', row['pricing'])


if __name__ == '__main__':
    unittest.main()
