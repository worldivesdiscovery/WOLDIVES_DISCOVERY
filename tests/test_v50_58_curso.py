"""v50.58 (revisión y usabilidad 15-16/10/2026, punto 3.5): the progress of a course and moving a session to another day.

The three tests the brief asks for, on a temporary copy of the database, with Stripe as a local simulator:
- an Open Water of 4 dives with the 4th postponed joins Saturday's departure: the place goes down in that departure,
  the original booking shows the new date and nothing is charged twice;
- cancelling for bad weather a departure with 2 course students and 6 normal divers: the 6 get their refund and the
  2 students get «Pendiente de nueva fecha»;
- the course is «Completado» only when every session is done.
Plus: «Crear una sesión nueva» checks the instructor and the boat are free, the reminder for the centre, the student's
answer, the certification and that another centre cannot see or touch any of it.
"""
import datetime as dt
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from helpers import ServerTestCase, Client  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from wod import curso as wcur  # noqa: E402
from wod import servicios as wsv  # noqa: E402

FAR = '2099-12-31'
SECRET = 'whsec_connect_local'


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


def saturday(after):
    d = dt.date.today() + dt.timedelta(days=after)
    while d.weekday() != 5: d += dt.timedelta(days=1)
    return d.isoformat()


def wait_for(fn, seconds=15):
    end = time.time() + seconds
    while time.time() < end:
        if fn(): return True
        time.sleep(0.4)
    return False


class Helpers(unittest.TestCase):
    def test_sessions_and_summary(self):
        plan = wsv.clean_plan({'days': ['full', 'full'], 'dives': [1, 2, 3, 4]})
        items = wcur.sessions(plan, '2027-06-07')
        self.assertEqual([i['label'] for i in items], ['Inmersión 1', 'Inmersión 2', 'Inmersión 3', 'Inmersión 4'])
        self.assertEqual([i['date'] for i in items], ['2027-06-07', '2027-06-07', '2027-06-08', '2027-06-08'])
        st = {1: 'done', 2: 'done', 3: 'done', 4: 'moved'}
        self.assertEqual(wcur.summary(items, st)['text'], '3 de 4 inmersiones hechas · 1 pendiente')
        self.assertFalse(wcur.finished(items, st))
        self.assertTrue(wcur.finished(items, {**st, 4: 'done'}))
        self.assertTrue(wcur.finished(items, {**st, 4: 'cancelled'}), 'a session the centre cancelled does not count')
        self.assertEqual(wcur.session_label('Open Water', items[3]), 'Sesión de curso – Open Water (inmersión 4)')
        theory = wcur.sessions(wsv.clean_plan({'days': ['am', 'am']}), '2027-06-07')
        self.assertEqual(wcur.summary(theory, {})['text'], '0 de 2 sesiones hechas · 2 pendientes')


class CourseProgress(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base, 'STRIPE_CONNECT_WEBHOOK_SECRET': SECRET,
                         'WOD_MAINTENANCE_SECONDS': '2', 'WOD_PAYMENTS_TOTP_REQUIRED': '0'}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'curso', phone='+34 600 580 001')
        cls.other = t.make_center(cls.admin, 'otrocurso', phone='+34 600 580 002')
        cls.cid = cls.center.user['center_id']
        cls.server.sql(f"""UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_curso',
                           stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?""", (cls.cid,))
        for name in ('Marta Instructora', 'Leo Instructor'):
            cls.server.sql("INSERT INTO users(fullname,email,username,password_hash,role,center_id,created_at) VALUES(?,?,?,'!','center',?,datetime('now'))",
                           (name, name.split()[0].lower() + '@curso.example.org', 'cur_' + name.split()[0].lower(), cls.cid))
        rows = cls.server.sql("SELECT id FROM users WHERE username LIKE 'cur_%' ORDER BY id")
        cls.marta, cls.leo = rows[0]['id'], rows[1]['id']
        cls.server.sql("INSERT INTO boats(center_id,name,capacity,active,created_at,updated_at) VALUES(?,'Neptuno',12,1,datetime('now'),datetime('now'))", (cls.cid,))
        cls.boat = cls.server.sql('SELECT id FROM boats WHERE center_id=?', (cls.cid,))[0]['id']
        # The Saturday departures (a double dive, paid online when booking)
        cls.dive = cls.center.post('/api/provider-services', {'title': 'Doble inmersión', 'price': 40, 'booking_mode': 'payment'}).json['id']
        mk = lambda d: cls.center.post('/api/provider-services/slot', {'service_id': cls.dive, 'slot_date': d, 'slot_time': '09:00', 'spots_total': 10}).json['slot_id']
        cls.sat1, cls.sat2 = saturday(10), saturday(17)
        cls.dep1, cls.dep2 = mk(cls.sat1), mk(cls.sat2)
        # Three Open Water courses of 4 dives (two full days), Marta teaches them; each test has its own
        cls.courses = {}
        for i, tag in enumerate(('A', 'B', 'C')):
            r = cls.center.post('/api/provider-services/wizard', {'publish': True, 'kind': 'course', 'title': f'Open Water {tag}',
                                                                  'plan': {'days': ['full', 'full'], 'dives': [1, 2, 3, 4]}, 'price': 450,
                                                                  'max_participants': 6, 'booking_mode': 'payment', 'instructor_user_id': cls.marta,
                                                                  'schedule': {'mode': 'dates', 'dates': [day(40 + 6 * i)]}})
            assert r.status == 200, r
            ed = cls.server.sql('SELECT id FROM service_slots WHERE service_id=?', (r.json['id'],))[0]['id']
            cls.courses[tag] = (r.json['id'], ed)
        cls.divers = [t.make_diver(f'curso{i}') for i in range(1, 11)]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    # ----------------------------------------------------------------------------------------------------- helpers
    def paid(self, diver, service, slot, pax=1):
        r = diver.post('/api/bookings', {'center_id': self.cid, 'service_id': service, 'slot_id': slot, 'participants': pax})
        self.assertEqual(r.status, 200, r)
        sess = self.stripe.last_session(); self.stripe.pay(sess['id'])
        ev = {'id': f'evt_{time.time_ns()}', 'type': 'checkout.session.completed', 'account': 'acct_curso',
              'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
        payload, sig = StripeMock.signed(ev, SECRET)
        Client(self.server, origin=None).request('POST', '/api/payments/webhook/connect', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
        self.assertEqual(self.server.sql('SELECT status FROM bookings WHERE id=?', (r.json['id'],))[0]['status'], 'confirmed')
        return r.json['id']

    def started_yesterday(self, edition):
        """The edition began yesterday: the first day of the course is over and today is its second (and last) day."""
        self.server.sql('UPDATE service_slots SET slot_date=?, date_to=? WHERE id=?', (day(-1), day(0), edition))
        self.server.sql('UPDATE bookings SET booking_date=?, date_to=? WHERE slot_id=?', (day(-1), day(0), edition))

    def view(self, client, bid):
        r = client.get(f'/api/bookings/{bid}/course')
        self.assertEqual(r.status, 200, r)
        return r.json

    def done(self, bid, seq, seats=None, **kw):
        return self.center.post(f'/api/center/bookings/{bid}/course/done', {'seq': seq, **({'seats': seats} if seats else {}), **kw})

    def spots(self, slot):
        return self.server.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot,))[0]['spots_available']

    def state(self, bid, seq, seat=1):
        return self.server.sql('SELECT * FROM booking_sessions WHERE booking_id=? AND seq=? AND seat=?', (bid, seq, seat))[0]

    # ----------------------------------------------------------------------------------------------------- the brief
    def test_1_fourth_dive_joins_saturday(self):
        sid, ed = self.courses['A']
        d = self.divers[0]
        bid = self.paid(d, sid, ed)
        self.started_yesterday(ed)
        v = self.view(d, bid)
        self.assertEqual(v['summary']['text'], '0 de 4 inmersiones hechas · 4 pendientes')
        self.assertEqual([s['label'] for s in v['sessions']], ['Inmersión 1', 'Inmersión 2', 'Inmersión 3', 'Inmersión 4'])
        self.assertFalse(v['can_edit'], 'the diver only sees his progress')
        self.assertTrue(self.view(self.center, bid)['can_edit'])
        for seq in (1, 2, 3): self.assertEqual(self.done(bid, seq).status, 200)
        v = self.view(d, bid)
        self.assertEqual(v['summary']['text'], '3 de 4 inmersiones hechas · 1 pendiente')
        self.assertEqual([s['students'][0]['icon'] for s in v['sessions']], ['✔', '✔', '✔', '⏳'])
        price, orders = (self.server.sql('SELECT price FROM bookings WHERE id=?', (bid,))[0]['price'],
                         self.server.sql('SELECT COUNT(*) AS n FROM payment_orders WHERE booking_id=?', (bid,))[0]['n'])
        n_bookings = self.server.sql('SELECT COUNT(*) AS n FROM bookings')[0]['n']
        before = self.spots(self.dep1)
        # «Pasar a otro día» → «Unirlo a una salida que ya existe»: Saturday at 9:00
        o = self.center.get(f'/api/center/bookings/{bid}/course/move-options?seq=4')
        self.assertEqual(o.status, 200, o)
        self.assertIn(self.dep1, [x['id'] for x in o.json['departures']])
        self.assertNotIn(ed, [x['id'] for x in o.json['departures']], 'never the edition itself')
        self.assertEqual(o.json['instructor_user_id'], self.marta)
        r = self.center.post(f'/api/center/bookings/{bid}/course/move', {'seq': 4, 'mode': 'join', 'slot_id': self.dep1})
        self.assertEqual(r.status, 200, r)
        # the place goes down in that departure
        self.assertEqual(self.spots(self.dep1), before - 1)
        blk = self.server.sql("SELECT label, source, qty FROM spot_blocks WHERE slot_id=? AND status='active'", (self.dep1,))
        self.assertEqual([(b['label'], b['source'], b['qty']) for b in blk], [('Sesión de curso – Open Water A (inmersión 4)', 'course', 1)])
        # the original booking shows the new date
        s4 = [s for s in self.view(d, bid)['sessions'] if s['seq'] == 4][0]['students'][0]
        self.assertEqual((s4['status'], s4['icon'], s4['date'], s4['start'], s4['instructor']), ('moved', '↪', self.sat1, '09:00', 'Marta Instructora'))
        self.assertIn('Doble inmersión', s4['where'])
        self.assertEqual(s4['moved_from'][:10], day(0))
        # no se cobra dos veces: same booking, same price, no new payment, still «en curso»
        self.assertEqual(self.server.sql('SELECT COUNT(*) AS n FROM bookings')[0]['n'], n_bookings)
        self.assertEqual(self.server.sql('SELECT price FROM bookings WHERE id=?', (bid,))[0]['price'], price)
        self.assertEqual(self.server.sql('SELECT COUNT(*) AS n FROM payment_orders WHERE booking_id=?', (bid,))[0]['n'], orders)
        b = self.server.sql('SELECT status, course_completed_at FROM bookings WHERE id=?', (bid,))[0]
        self.assertEqual((b['status'], b['course_completed_at']), ('confirmed', None))
        # her instructor is assigned: Marta is busy on Saturday in the common agenda
        self.assertTrue(self.server.sql("""SELECT 1 FROM resource_blocks rb JOIN resources r ON r.id=rb.resource_id WHERE r.user_id=? AND rb.ref_type='course_join'
                                           AND rb.ref_id=? AND rb.status='active'""", (self.marta, self.dep1)))
        # the manifest and the planning of Saturday show the student
        man = self.center.get(f'/api/manifest/{self.dep1}').json
        self.assertEqual([(x['text'], x['instructor']) for x in man['course']], [('Sesión de curso – Open Water A (inmersión 4)', 'Marta Instructora')])
        pl = self.center.get(f'/api/center/planning?month={self.sat1[:7]}').json
        slot = [x for x in pl['slots'] if x['id'] == self.dep1][0]
        self.assertIn('Sesión de curso – Open Water A (inmersión 4)', [x['label'] for x in slot.get('blocks', [])])
        # the student is told (app, email) and confirms
        msg = self.server.sql("SELECT subject, body FROM messages WHERE recipient_user_id=? AND booking_id=? ORDER BY id DESC LIMIT 1", (d.user['id'], bid))[0]
        self.assertEqual(msg['subject'], 'Nueva fecha para tu inmersión 4')
        self.assertIn('Tu inmersión 4 del Open Water A pasa al', msg['body']); self.assertIn('a las 09:00 con Marta Instructora', msg['body'])
        self.assertIn('no se te cobra otra vez', msg['body'])
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='course_session_moved' AND to_email=?", (d.user['email'],)))
        self.assertTrue([s for s in self.view(d, bid)['sessions'] if s['seq'] == 4][0]['students'][0]['can_answer'])
        r = d.post(f'/api/bookings/{bid}/course/answer', {'seq': 4, 'answer': 'ok'})
        self.assertEqual(r.status, 200, r); self.assertEqual(self.state(bid, 4)['reply'], 'ok')
        self.assertTrue(self.server.sql("SELECT 1 FROM messages WHERE recipient_user_id=? AND subject LIKE '%confirma inmersión 4%'", (self.center.user['id'],)))
        # it is marked as done when Saturday comes, not before; then the course is completed and goes to the Log Book
        r = self.done(bid, 4)
        self.assertEqual(r.status, 400, r); self.assertIn('cuando llegue el día', r.json['error'])
        self.server.sql('UPDATE booking_sessions SET local_date=? WHERE booking_id=? AND seq=4', (day(0), bid))
        r = self.done(bid, 4)
        self.assertEqual(r.status, 200, r); self.assertEqual(r.json['completed'], [bid])
        b = self.server.sql('SELECT status, course_completed_at FROM bookings WHERE id=?', (bid,))[0]
        self.assertEqual(b['status'], 'completed'); self.assertTrue(b['course_completed_at'])
        lb = self.server.sql("SELECT dive_type FROM logbook_entries WHERE user_id=? AND notes LIKE ?", (d.user['id'], f'% · reserva #{bid}'))
        self.assertEqual(len(lb), 4, 'the 4 dives of the course go to the Log Book'); self.assertEqual({x['dive_type'] for x in lb}, {'Curso'})
        self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='course_completed' AND to_email=?", (d.user['email'],)))
        # the certification
        r = self.center.post(f'/api/center/bookings/{bid}/course/certify', {'certification_id': 1})
        self.assertEqual(r.status, 200, r); self.assertEqual(r.json['profile'], 'saved')
        self.assertEqual(self.server.sql('SELECT certification_id FROM user_profiles WHERE user_id=?', (d.user['id'],))[0]['certification_id'], 1)
        # done means done: no undoing it once the course is completed
        self.assertEqual(self.done(bid, 4, value=False).status, 400)

    def test_2_bad_weather_two_students_six_divers(self):
        sid, ed = self.courses['B']
        normal = [self.paid(self.divers[i], self.dive, self.dep2) for i in range(1, 7)]
        students = [self.paid(self.divers[i], sid, ed) for i in (7, 8)]
        self.started_yesterday(ed)
        for seq in (1, 2, 3):
            r = self.done(students[0], seq, scope='edition')
            self.assertEqual(r.status, 200, r); self.assertEqual(r.json['marked'], 2, 'the whole group with one tap')
        # the 4th dive of the whole group goes to Saturday's departure
        r = self.center.post(f'/api/center/bookings/{students[0]}/course/move', {'seq': 4, 'mode': 'join', 'slot_id': self.dep2, 'scope': 'edition'})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.spots(self.dep2), 10 - 6 - 2)
        # the preview says who gets what
        p = self.center.post('/api/provider-services/slot-cancel', {'slot_id': self.dep2, 'preview': True}).json
        self.assertEqual(sorted(a['booking_id'] for a in p['affected']), sorted(normal))
        self.assertEqual({a['receives'] for a in p['affected']}, {'refund'})
        self.assertEqual(sorted(x['booking_id'] for x in p['course']), sorted(students))
        # cancel for bad weather
        r = self.center.post('/api/provider-services/slot-cancel', {'slot_id': self.dep2, 'reason': 'weather', 'note': 'Temporal de levante'})
        self.assertEqual((r.status, r.json.get('affected')), (200, 6), r)
        # the 2 students: «Pendiente de nueva fecha», no refund, the course goes on
        for bid in students:
            row = self.state(bid, 4)
            self.assertEqual((row['status'], row['slot_id'], row['block_id']), ('pending_new_date', None, None))
            b = self.server.sql('SELECT status, refunded_total FROM bookings WHERE id=?', (bid,))[0]
            self.assertEqual(b['status'], 'confirmed'); self.assertFalse(b['refunded_total'])
            self.assertFalse(self.server.sql('SELECT 1 FROM slot_cancel_offers WHERE booking_id=?', (bid,)))
            msg = self.server.sql("SELECT body FROM messages WHERE booking_id=? ORDER BY id DESC LIMIT 1", (bid,))[0]['body']
            self.assertIn('queda pendiente de nueva fecha', msg); self.assertIn('Mal tiempo', msg)
        self.assertFalse(self.server.sql("SELECT 1 FROM spot_blocks WHERE slot_id=? AND status='active'", (self.dep2,)))
        self.assertFalse(self.server.sql("""SELECT 1 FROM resource_blocks WHERE ref_type='course_join' AND ref_id=? AND status='active'""", (self.dep2,)),
                         'Marta is free again on that Saturday')
        # the 6 normal divers: their refund, as until now (the offer and, when its time is up, the automatic refund)
        self.assertEqual(len(self.server.sql(f"SELECT 1 FROM slot_cancel_offers WHERE booking_id IN ({','.join('?' * 6)})", normal)), 6)
        self.server.sql("UPDATE slot_cancel_offers SET deadline='2000-01-01T00:00:00' WHERE slot_id=?", (self.dep2,))
        ok = wait_for(lambda: len(self.server.sql(f"SELECT 1 FROM bookings WHERE status='cancelled' AND refunded_total>0 AND id IN ({','.join('?' * 6)})", normal)) == 6)
        self.assertTrue(ok, self.server.sql(f"SELECT id,status,refunded_total FROM bookings WHERE id IN ({','.join('?' * 6)})", normal))
        self.assertEqual(len(self.server.sql(f"SELECT DISTINCT booking_id FROM payment_refunds WHERE booking_id IN ({','.join('?' * 6)})", normal)), 6)
        # «Sesiones de curso por recolocar» in the centre's panel, with the reminder after 30 days
        pend = self.center.get('/api/center/course-pending').json
        mine = [x for x in pend['items'] if x['booking_id'] in students]
        self.assertEqual(len(mine), 2); self.assertEqual({x['state'] for x in mine}, {'Pendiente de nueva fecha'})
        self.assertEqual(pend['days'], 30); self.assertEqual(sum(1 for x in mine if x['old']), 0)
        self.server.sql("UPDATE booking_sessions SET pending_since=? WHERE status='pending_new_date' AND booking_id IN (?,?)", (day(-31) + 'T10:00:00', *students))
        pend = self.center.get('/api/center/course-pending').json
        self.assertEqual(sum(1 for x in pend['items'] if x['booking_id'] in students and x['old']), 2)
        self.assertEqual(self.center.post('/api/center/course-settings', {'reminder_days': 60}).status, 200)
        pend = self.center.get('/api/center/course-pending').json
        self.assertEqual(sum(1 for x in pend['items'] if x['booking_id'] in students and x['old']), 0)
        self.center.post('/api/center/course-settings', {'reminder_days': 30})
        self.assertNotIn(students[0], [x['booking_id'] for x in self.other.get('/api/center/course-pending').json['items']])
        # the centre gives them a new session of their own: free instructor and boat are checked
        when = {'seq': 4, 'mode': 'new', 'date': self.sat1, 'time': '09:30', 'end': '12:30', 'scope': 'edition'}
        r = self.center.post(f'/api/center/bookings/{students[0]}/course/move', {**when, 'instructor_user_id': self.marta})
        self.assertEqual(r.status, 400, r); self.assertIn('ya tiene trabajo', r.json['error'])   # Marta is with Open Water A on that Saturday
        r = self.center.post(f'/api/center/bookings/{students[0]}/course/move', {**when, 'instructor_user_id': self.leo, 'boat_id': self.boat})
        self.assertEqual(r.status, 200, r)
        for bid in students:
            row = self.state(bid, 4)
            self.assertEqual((row['status'], row['mode'], row['local_date'], row['start_time'], row['instructor_user_id'], row['boat_id']),
                             ('moved', 'new', self.sat1, '09:30', self.leo, self.boat))
        self.assertEqual(len(self.server.sql("""SELECT 1 FROM resource_blocks rb JOIN resources r ON r.id=rb.resource_id WHERE r.user_id=? AND rb.ref_type='course_new'
                                                AND rb.status='active'""", (self.leo,))), 1, 'one hour block for the group, not one per student')
        pl = self.center.get(f'/api/center/planning?month={self.sat1[:7]}').json
        chip = [x for x in pl['course_sessions'] if x['course'] == 'Open Water B']
        self.assertEqual([(x['date'], x['start'], x['students'], x['instructor'], x['boat']) for x in chip], [(self.sat1, '09:30', 2, 'Leo Instructor', 'Neptuno')])
        # the boat is not free for another session at the same time
        sid_c, ed_c = self.courses['C']
        other_bid = self.paid(self.divers[9], sid_c, ed_c)
        self.started_yesterday(ed_c)
        r = self.center.post(f'/api/center/bookings/{other_bid}/course/move', {'seq': 4, 'mode': 'new', 'date': self.sat1, 'time': '10:00', 'end': '11:00',
                                                                               'instructor_user_id': self.center.user['id'], 'boat_id': self.boat})
        self.assertEqual(r.status, 400, r); self.assertIn('El barco Neptuno ya sale', r.json['error'])
        self.server.sql("DELETE FROM booking_sessions WHERE booking_id=?", (other_bid,))
        self.server.sql("UPDATE bookings SET status='cancelled' WHERE id=?", (other_bid,))

    def test_3_completed_only_when_every_session_is_done(self):
        sid, ed = self.courses['C']
        d = self.divers[4]
        self.server.sql("UPDATE service_slots SET slot_date=?, date_to=? WHERE id=?", (day(40 + 12), day(41 + 12), ed))
        bid = self.paid(d, sid, ed, pax=2)
        self.started_yesterday(ed)
        v = self.view(self.center, bid)
        self.assertEqual(len(v['seats']), 2); self.assertEqual(len(v['sessions'][0]['students']), 2)
        for seq in (1, 2, 3): self.assertEqual(self.done(bid, seq).status, 200)
        r = self.done(bid, 4, seats=[1])
        self.assertEqual(r.status, 200, r); self.assertEqual(r.json['completed'], [], 'the second student still has the 4th dive')
        self.assertEqual(self.server.sql('SELECT status FROM bookings WHERE id=?', (bid,))[0]['status'], 'confirmed')
        v = self.view(d, bid)
        self.assertEqual([x['summary']['text'] for x in v['seats']], ['4 de 4 inmersiones hechas', '3 de 4 inmersiones hechas · 1 pendiente'])
        # marking the booking «completada» from the bookings list is refused while a session is missing
        r = self.center.post(f'/api/bookings/{bid}/status', {'status': 'completed'})
        self.assertEqual(r.status, 400, r); self.assertIn('faltan sesiones', r.json['error'])
        r = self.done(bid, 4, seats=[1])
        self.assertEqual(r.status, 400, r); self.assertIn('ya está hecha', r.json['error'])
        r = self.done(bid, 4, seats=[2])
        self.assertEqual(r.status, 200, r); self.assertEqual(r.json['completed'], [bid])
        self.assertEqual(self.server.sql('SELECT status FROM bookings WHERE id=?', (bid,))[0]['status'], 'completed')
        self.assertTrue(self.view(d, bid)['completed_at'])

    def test_4_nobody_else_sees_or_touches_it(self):
        sid, ed = self.courses['A']
        bid = self.server.sql('SELECT id FROM bookings WHERE service_id=? ORDER BY id LIMIT 1', (sid,))[0]['id']
        for c in (self.other, self.divers[5]):
            self.assertEqual(c.get(f'/api/bookings/{bid}/course').status, 404)
            self.assertIn(c.post(f'/api/center/bookings/{bid}/course/done', {'seq': 1}).status, (403, 404))
            self.assertIn(c.post(f'/api/center/bookings/{bid}/course/move', {'seq': 4, 'mode': 'join', 'slot_id': self.dep1}).status, (403, 404))
            self.assertIn(c.get(f'/api/center/bookings/{bid}/course/move-options?seq=4').status, (403, 404))
        self.assertEqual(self.other.post(f'/api/bookings/{bid}/course/answer', {'seq': 4, 'answer': 'other_date'}).status, 404)
        # a departure of another centre cannot be used
        foreign = self.other.post('/api/provider-services', {'title': 'Otra salida', 'price': 30, 'booking_mode': 'request'}).json['id']
        fslot = self.other.post('/api/provider-services/slot', {'service_id': foreign, 'slot_date': saturday(24), 'slot_time': '09:00', 'spots_total': 8}).json['slot_id']
        sid_b, _ed_b = self.courses['B']
        bid_b = self.server.sql('SELECT id FROM bookings WHERE service_id=? ORDER BY id LIMIT 1', (sid_b,))[0]['id']
        r = self.center.post(f'/api/center/bookings/{bid_b}/course/move', {'seq': 4, 'mode': 'join', 'slot_id': fslot, 'scope': 'edition'})
        self.assertEqual(r.status, 404, r)
        self.assertEqual(self.spots(fslot), 8)
        # a normal dive booking has no course progress
        nb = self.server.sql('SELECT id FROM bookings WHERE service_id=? ORDER BY id LIMIT 1', (self.dive,))[0]['id']
        self.assertEqual(self.center.get(f'/api/bookings/{nb}/course').status, 400)


if __name__ == '__main__':
    unittest.main()
