"""v50.55 · «Para terminar» del brief completo de la app (lo que no depende de cuentas ni de decisiones), servidor:

  · «Ver salidas aquí»: /api/salidas-cercanas?punto=<id> da solo las salidas con plazas que van a ese punto.
  · Solicitudes: siempre lo que caduca antes primero (también los pendientes de pago).
  · «Contar a la vuelta»: el recuento al volver queda aparte; «Hoy» y la lista del barco dicen si falta.
  · «Mis reservas»: cada reserva lleva la zona horaria y la duración de su actividad («Añadir al calendario»).
The screens are checked in the browser: tests/navegador/e2e_v50_55_terminar.py."""
import datetime as dt
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import MiddayClock, ServerTestCase  # noqa: E402

DAY = lambda n: (dt.date.today() + dt.timedelta(days=n)).isoformat()


class Terminar(MiddayClock, ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.A = t.make_center(cls.admin, 'fin55', phone='+34 600 555 001')
        cls.cid = cls.A.user['center_id']
        cls.server.sql("UPDATE centers SET plan_code='pro',plan_status='active' WHERE id=?", (cls.cid,))
        cls.pids = [r['id'] for r in cls.server.sql("SELECT id FROM dive_points WHERE active=1 ORDER BY id LIMIT 2")]
        for pid in cls.pids:
            assert cls.A.post('/api/center-points/assign', {'dive_point_id': pid}).status == 200
        cls.sid = cls.A.post('/api/provider-services', {'title': 'Doble en barco', 'price': 50}).json['id']
        cls.at_midday(cls.sid)

    def slot(self, days, time_='09:00', points=(), spots=10):
        r = self.A.post('/api/provider-services/slot', {'service_id': self.sid, 'slot_date': DAY(days), 'slot_time': time_, 'spots_total': spots,
                                                         'dive_point_ids': list(points)})
        self.assertEqual(r.status, 200, r)
        return r.json['slot_id']

    def booked(self, d, slot, status='confirmed', n=1):
        r = d.post('/api/bookings', {'center_id': self.cid, 'service_id': self.sid, 'slot_id': slot, 'participants': n})
        self.assertEqual(r.status, 200, r)
        if status: self.server.sql("UPDATE bookings SET status=?,payment_status='at_center' WHERE id=?", (status, r.json['id']))
        return r.json['id']

    def test_departures_of_a_dive_point(self):
        p1, p2 = self.pids
        a = self.slot(2, '09:00', [p1]); b = self.slot(3, '10:00', [p2]); c = self.slot(4, '11:00', [p1, p2]); self.slot(5, '12:00')
        full = self.slot(6, '09:00', [p1], spots=1)
        self.server.sql("UPDATE service_slots SET spots_available=0,status='full' WHERE id=?", (full,))   # no places left
        far = self.slot(40, '09:00', [p1])                                                    # beyond the 30 days
        got = [x['slot_id'] for x in self.client().get(f'/api/salidas-cercanas?punto={p1}&limite=20').json['items']]
        self.assertIn(a, got); self.assertIn(c, got)
        self.assertNotIn(b, got); self.assertNotIn(full, got); self.assertNotIn(far, got)
        self.assertEqual(got, sorted(got, key=lambda s: got.index(s)))
        item = next(x for x in self.client().get(f'/api/salidas-cercanas?punto={p1}').json['items'] if x['slot_id'] == a)
        self.assertEqual(item['center_id'], self.cid); self.assertTrue(item['bookable']); self.assertIn(p1, [p['id'] for p in item['points']])
        # without «punto», the nearby departures as before (all points, 14 days)
        allx = [x['slot_id'] for x in self.client().get('/api/salidas-cercanas?limite=50').json['items']]
        self.assertIn(b, allx); self.assertNotIn(far, allx)
        self.assertEqual(self.client().get('/api/salidas-cercanas?punto=abc').status, 200)   # a wrong value is ignored

    def test_requests_expire_first_first(self):
        s1 = self.slot(7, '09:00'); s2 = self.slot(8, '09:00')
        late = self.booked(self.make_diver('fin55r1'), s1, status=None)
        soon = self.booked(self.make_diver('fin55r2'), s2, status=None)
        none_ = self.booked(self.make_diver('fin55r3'), s2, status=None)
        base = dt.datetime.now()
        self.server.sql('UPDATE bookings SET response_deadline=? WHERE id=?', ((base + dt.timedelta(hours=20)).isoformat(timespec='minutes'), late))
        self.server.sql('UPDATE bookings SET response_deadline=? WHERE id=?', ((base + dt.timedelta(minutes=40)).isoformat(timespec='minutes'), soon))
        self.server.sql('UPDATE bookings SET response_deadline=NULL WHERE id=?', (none_,))
        ids = [x['id'] for x in self.A.get('/api/center/requests').json['items']]
        self.assertLess(ids.index(soon), ids.index(late)); self.assertEqual(ids[-1], none_)

    def test_short_code_with_dash_and_underscore(self):
        # v50.56: the 6 characters come from the booking's token, which can have «-» and «_» (1 code in 6 was refused)
        today = self.slot(0, '23:30')
        bid = self.booked(self.make_diver('fin55u'), today)
        self.server.sql('UPDATE bookings SET public_token=? WHERE id=?', ('a-B_c9' + 'x' * 26, bid))
        self.assertEqual(self.A.post('/api/pro/escanear', {'code': f'{bid}-A-B_C9', 'slot_id': today}).json['result'], 'ok')
        self.assertEqual(self.A.post('/api/pro/escanear', {'code': f'WOD-{bid:06d} · a-b_c9', 'slot_id': today}).json['result'], 'usado')   # the same code, read again
        self.assertEqual(self.A.post('/api/pro/escanear', {'code': f'{bid}-A-B_C8', 'slot_id': today}).json['result'], 'no_valido')

    def test_count_on_the_way_back(self):
        today = self.slot(0, '23:30')
        d = self.make_diver('fin55c')
        bid = self.booked(d, today, n=2)
        code = f"{bid}-{self.server.sql('SELECT public_token FROM bookings WHERE id=?', (bid,))[0]['public_token'][:6].upper()}"
        self.assertEqual(self.A.post('/api/pro/escanear', {'code': code, 'slot_id': today}).json['result'], 'ok')
        slot_of = lambda: next(x for x in self.A.get('/api/pro/hoy').json['slots'] if x['slot_id'] == today)
        self.assertFalse(slot_of()['return_pending'])                                        # nothing counted yet
        r = self.A.post('/api/pro/contar', {'slot_id': today, 'count': 2}).json
        self.assertEqual(r['fase'], 'salida'); self.assertTrue(r['headcounts']['return_pending'])
        self.assertTrue(slot_of()['return_pending'])
        man = self.A.get(f'/api/manifest/{today}').json
        self.assertEqual(man['headcounts']['salida']['counted'], 2); self.assertIsNone(man['headcounts']['vuelta'])
        r = self.A.post('/api/pro/contar', {'slot_id': today, 'count': 1, 'fase': 'vuelta'}).json
        self.assertEqual((r['fase'], r['match'], r['diff']), ('vuelta', False, -1))
        self.assertFalse(slot_of()['return_pending'])
        self.assertEqual(self.A.get(f'/api/manifest/{today}').json['headcounts']['vuelta']['counted'], 1)
        # a new count when leaving asks again for the one on the way back
        self.A.post('/api/pro/contar', {'slot_id': today, 'count': 2})
        self.assertTrue(slot_of()['return_pending'])
        self.assertEqual(self.A.post('/api/pro/contar', {'slot_id': today, 'count': 2, 'fase': 'otra'}).json['fase'], 'salida')

    def test_my_bookings_carry_the_zone_and_duration(self):
        self.server.sql("UPDATE provider_services SET duration_minutes=150 WHERE id=?", (self.sid,))
        d = self.make_diver('fin55z')
        bid = self.booked(d, self.slot(9, '08:30'))
        b = next(x for x in d.get('/api/me/area').json['bookings'] if x['id'] == bid)
        self.assertEqual(b['service_timezone'], self.midday_zone)
        self.assertEqual(b['service_duration'], 150)
        self.server.sql("UPDATE provider_services SET timezone=NULL WHERE id=?", (self.sid,))
        b = next(x for x in d.get('/api/me/area').json['bookings'] if x['id'] == bid)
        self.assertEqual(b['service_timezone'], 'Europe/Madrid')                               # the default zone
        self.at_midday(self.sid)


if __name__ == '__main__':
    unittest.main(verbosity=2)
