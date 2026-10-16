"""v50.44 · Common agenda engine and services booked by days or half days (encargo unificado, bloque A: A2, A4).

Pure engine (wod.agenda): time zones (Mexico / Spain, change of hour, end of month, 29 February), prices (tiers,
discount, extras, per person), day states (busy, half days, lead time, usual week, closed seasons) and the checks of
a selection. Server, on a temporary copy of the demo catalogue and with the Stripe simulator: public calendar
without names or reasons, a request does not block, confirming blocks and rejects the overlapping requests with a
kind email, two confirmations at the same time (only one wins), unpaid → the days are free again, «Pago al reservar»
holds the days while paying, half days, permissions, plan feature and the time of a month of agenda.
"""
from __future__ import annotations

import datetime as dt
import json
import sys
import threading
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from wod import agenda as wag  # noqa: E402

from helpers import Client, ServerTestCase  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402

CONNECT_SECRET = 'whsec_connect_agenda'
UTC = dt.timezone.utc


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


class EngineUnits(unittest.TestCase):
    def test_time_zones_mexico_spain_and_dst(self):
        # The same local day in Cancún is a different UTC instant than in Madrid, and both are kept.
        self.assertEqual(wag.local_to_utc('2026-11-16', '08:00', 'America/Cancun'), '2026-11-16T13:00:00Z')
        self.assertEqual(wag.local_to_utc('2026-11-16', '08:00', 'Europe/Madrid'), '2026-11-16T07:00:00Z')
        # 25 October 2026 (Spain goes back one hour): the day lasts 25 hours
        a = dt.datetime.strptime(wag.local_to_utc('2026-10-25', '00:00', 'Europe/Madrid'), '%Y-%m-%dT%H:%M:%SZ')
        b = dt.datetime.strptime(wag.local_to_utc('2026-10-25', '24:00', 'Europe/Madrid'), '%Y-%m-%dT%H:%M:%SZ')
        self.assertEqual(b - a, dt.timedelta(hours=25))
        # 28 March 2027 (forward one hour): 23 hours; 02:30 does not exist and moves forward
        a = dt.datetime.strptime(wag.local_to_utc('2027-03-28', '00:00', 'Europe/Madrid'), '%Y-%m-%dT%H:%M:%SZ')
        b = dt.datetime.strptime(wag.local_to_utc('2027-03-28', '24:00', 'Europe/Madrid'), '%Y-%m-%dT%H:%M:%SZ')
        self.assertEqual(b - a, dt.timedelta(hours=23))
        self.assertEqual(wag.utc_to_local(wag.local_to_utc('2027-03-28', '02:30', 'Europe/Madrid'), 'Europe/Madrid').strftime('%H:%M'), '03:30')
        # End of month, leap year
        self.assertEqual(len(wag.month_days('2028-02')), 29); self.assertEqual(len(wag.month_days('2027-02')), 28)
        self.assertEqual(wag.month_days('2026-12')[-1], '2026-12-31')
        self.assertEqual(wag.ranges(['2028-02-28', '2028-02-29', '2028-03-01', '2028-03-03']), [('2028-02-28', '2028-03-01'), ('2028-03-03', '2028-03-03')])
        self.assertEqual(wag.normalize_selection(None, '2028-02-27', '2028-03-01'), ['2028-02-27', '2028-02-28', '2028-02-29', '2028-03-01'])
        self.assertEqual(wag.normalize_selection(['2027-02-29', 'x', '2027-03-01']), ['2027-03-01'])   # 29/02/2027 does not exist
        self.assertEqual(wag.tz_for_country('México'), 'America/Cancun'); self.assertIsNone(wag.valid_tz('Mars/Olympus'))

    def test_prices(self):
        p = wag.clean_pricing({'day': 180, 'half': 110, 'tiers': [{'min_days': 4, 'day': 150}], 'discount': {'min_days': 3, 'pct': 10},
                               'extras': [{'id': 'foto', 'label': 'Fotos', 'price': 40, 'per': 'day'}, {'id': 'van', 'label': 'Transporte', 'price': 30, 'per': 'booking', 'per_person': True}]})
        three = ['2026-11-16', '2026-11-17', '2026-11-18']
        self.assertEqual(wag.quote(p, three, 'full', 2, ['foto'])[0], 606.0)   # the example of the approved mock-up
        total, lines = wag.quote(p, three + ['2026-11-19'], 'full', 2, ['van'])
        self.assertEqual(total, round(4 * 150 * 0.9 + 60, 2))                   # tier from 4 days, then −10 %, transport per person
        self.assertEqual(wag.quote(p, ['2026-11-16'], 'am', 3)[0], 110.0)      # half day, price per group
        pp = wag.clean_pricing({'day': 100, 'per': 'person'})
        self.assertEqual(wag.quote(pp, three, 'full', 2)[0], 600.0)
        self.assertEqual(wag.quote(pp, ['2026-11-16'], 'pm', 2)[0], 100.0)     # half day without its own price: half of the day
        bad = wag.clean_pricing({'day': -5, 'tiers': [{'min_days': 1, 'day': 1}], 'discount': {'min_days': 3, 'pct': 200}, 'extras': [{'label': '', 'price': 3}]})
        self.assertEqual((bad['day'], bad['tiers'], bad['discount'], bad['extras']), (0.0, [], None, []))

    def test_day_states_and_selection(self):
        r = wag.clean_rules({'lead_hours': 48, 'am': ['08:00', '13:00'], 'pm': ['14:00', '19:00']}); tz = 'America/Cancun'
        now = dt.datetime(2026, 11, 10, 12, 0, tzinfo=UTC)
        days = wag.month_days('2026-11')
        s, e = wag.block_span('2026-11-16', '2026-11-16', 'am', r, tz)
        blocks = [{'starts_at': s, 'ends_at': e}]
        s, e = wag.block_span('2026-11-20', '2026-11-21', 'full', r, tz); blocks.append({'starts_at': s, 'ends_at': e})
        st = wag.day_states(days, blocks, r, tz, 'half_day', working_days=[0, 1, 2, 3, 4, 5], closures=[{'from': '2026-11-27', 'to': '2026-11-28'}], now_utc=now)
        self.assertEqual(st['2026-11-11'], 'off')        # inside the 48 h notice
        self.assertEqual(st['2026-11-13'], 'free')
        self.assertEqual(st['2026-11-15'], 'off')        # Sunday: not a working day
        self.assertEqual(st['2026-11-16'], 'am')         # morning taken, afternoon free
        self.assertEqual((st['2026-11-20'], st['2026-11-21']), ('busy', 'busy'))
        self.assertEqual(st['2026-11-27'], 'off')        # closed season
        only_days = wag.day_states(days, blocks, r, tz, 'day', now_utc=now)
        self.assertEqual(only_days['2026-11-16'], 'busy')  # a service by full days can not use a half-taken day
        # Checks of a selection, in plain words
        self.assertIsNone(wag.check_selection(['2026-11-17', '2026-11-18', '2026-11-19'], 'full', 'half_day', r, st))
        self.assertIn('ocupado', wag.check_selection(['2026-11-19', '2026-11-20'], 'full', 'half_day', r, st))
        self.assertIsNone(wag.check_selection(['2026-11-16'], 'pm', 'half_day', r, st))
        self.assertIn('mañana', wag.check_selection(['2026-11-16'], 'am', 'half_day', r, st))
        self.assertIn('seguidos', wag.check_selection(['2026-11-17', '2026-11-19'], 'full', 'half_day', r, st))
        self.assertIn('completos', wag.check_selection(['2026-11-17'], 'am', 'day', r, st))
        self.assertIn('mínimo', wag.check_selection(['2026-11-17'], 'full', 'day', wag.clean_rules({'min_days': 2}), st))
        loose = wag.clean_rules({'continuous': False})
        self.assertIsNone(wag.check_selection(['2026-11-17', '2026-11-19'], 'full', 'half_day', loose, st))


class AgendaServer(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base, 'STRIPE_CONNECT_WEBHOOK_SECRET': CONNECT_SECRET, 'WOD_MAINTENANCE_SECONDS': '2'}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.pro = t.make_freelance(cls.admin, 'tito')
        cls.other = t.make_freelance(cls.admin, 'otropro')
        cls.server.sql("UPDATE users SET stripe_account_id='acct_tito',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.pro.user['id'],))
        rules = {'min_days': 1, 'max_days': 10, 'lead_hours': 24, 'am': ['08:00', '13:00'], 'pm': ['14:00', '19:00'], 'full': ['08:00', '16:00']}
        cls.sid = cls.pro.post('/api/provider-services', {'title': 'Cenotes por días', 'price': 180, 'max_participants': 4, 'booking_mode': 'request', 'booking_unit': 'half_day',
                                                          'timezone': 'America/Cancun', 'unit_rules': rules,
                                                          'pricing': {'day': 180, 'half': 110, 'discount': {'min_days': 3, 'pct': 10}, 'extras': [{'id': 'foto', 'label': 'Fotos', 'price': 40, 'per': 'day'}]}}).json['id']
        cls.pay_sid = cls.pro.post('/api/provider-services', {'title': 'Fotografía submarina por días', 'price': 100, 'booking_mode': 'payment', 'booking_unit': 'day',
                                                              'timezone': 'America/Cancun', 'unit_rules': rules, 'pricing': {'day': 100}}).json['id']
        cls.divers = [t.make_diver(f'cen{i}') for i in range(6)]

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def public(self, month, sid=None):
        return self.client().get(f'/api/agenda/public?service={sid or self.sid}&month={month}').json

    def ask(self, diver, days, part='full', pax=1, sid=None):
        return diver.post('/api/bookings', {'service_id': sid or self.sid, 'days': days, 'part': part, 'participants': pax})

    def status(self, bid):
        return self.server.sql('SELECT status FROM bookings WHERE id=?', (bid,))[0]['status']

    def test_public_calendar_has_no_names_or_reasons(self):
        d = day(40); m = d[:7]
        self.assertEqual(self.pro.post('/api/agenda/block', {'date_from': d, 'date_to': d, 'kind': 'holiday', 'note': 'boda de mi hermana'}).status, 200)
        pub = self.public(m)
        self.assertEqual(pub['days'][d], 'busy')
        txt = json.dumps(pub, ensure_ascii=False)
        for secret in ('boda', 'holiday', 'manual', 'Pérez', 'private_note', 'ref_id', 'client', 'starts_at'):
            self.assertNotIn(secret, txt)
        self.assertEqual(set(pub['days'].values()) - {'free', 'busy', 'am', 'pm', 'off'}, set())
        self.assertEqual(pub['timezone'], 'America/Cancun')
        self.assertEqual(self.client().get('/api/agenda/public?service=999999').status, 404)
        slot_sid = self.pro.post('/api/provider-services', {'title': 'Salida normal', 'price': 50}).json['id']   # v50.55: «other» may be on the free plan by now
        self.assertEqual(self.client().get(f'/api/agenda/public?service={slot_sid}').status, 404)

    def test_request_does_not_block_confirm_rejects_overlaps(self):
        a, b = self.divers[0], self.divers[1]
        days = [day(20), day(21), day(22)]
        ra = self.ask(a, days, pax=2); rb = self.ask(b, days[1:])
        self.assertEqual((ra.status, rb.status), (200, 200), (ra, rb))
        self.assertEqual(ra.json['status'], 'requested')
        self.assertEqual([self.public(d[:7])['days'][d] for d in days], ['free'] * 3)   # pending: still free for everybody
        self.assertEqual(self.ask(self.divers[2], days[:1], part='am').status, 200)      # a half day of the same days can still be asked
        r = self.pro.post(f"/api/bookings/{ra.json['id']}/status", {'status': 'confirmed'})
        self.assertEqual(r.status, 200, r)
        self.assertIn(self.status(ra.json['id']), ('accepted_pending_payment', 'confirmed'))
        self.assertEqual(self.status(rb.json['id']), 'rejected')
        self.assertEqual([self.public(d[:7])['days'][d] for d in days], ['busy'] * 3)
        mail = self.server.sql("SELECT text FROM email_outbox WHERE to_email=? AND subject LIKE 'Solicitud no disponible%' ORDER BY id DESC LIMIT 1", ('cen1@diver.example.org',))
        self.assertTrue(mail and 'ya no están disponibles' in mail[0]['text'] and f'reservar-dias?service={self.sid}' in mail[0]['text'], mail)
        # The freelance sees who comes; a diver or a centre does not see the agenda
        mine = self.pro.get(f'/api/agenda/mine?month={days[0][:7]}').json
        self.assertTrue(any(x.get('booking', {}).get('id') == ra.json['id'] for x in mine['blocks']))
        self.assertEqual(a.get('/api/agenda/mine').status, 403)
        self.assertEqual(self.other.get(f'/api/agenda/mine?month={days[0][:7]}').json['blocks'], [])
        # A block of a booking can not be removed by hand, nor a block of somebody else
        bl = [x for x in mine['blocks'] if x.get('booking')][0]
        self.assertEqual(self.pro.post('/api/agenda/unblock', {'id': bl['id']}).status, 400)
        self.assertEqual(self.other.post('/api/agenda/unblock', {'id': bl['id']}).status, 404)
        self.assertEqual(a.post('/api/agenda/block', {'date_from': day(30)}).status, 403)

    def test_unpaid_frees_the_days(self):
        days = [day(25), day(26)]
        r = self.ask(self.divers[3], days)
        self.pro.post(f"/api/bookings/{r.json['id']}/status", {'status': 'confirmed'})
        self.assertEqual(self.status(r.json['id']), 'accepted_pending_payment')      # charges online: a deadline to pay
        self.assertEqual(self.public(days[0][:7])['days'][days[0]], 'busy')
        past = (dt.datetime.now() - dt.timedelta(minutes=5)).isoformat(timespec='minutes')
        self.server.sql('UPDATE bookings SET payment_deadline=? WHERE id=?', (past, r.json['id']))
        for _ in range(20):
            if self.status(r.json['id']) == 'expired': break
            time.sleep(0.5)
        self.assertEqual(self.status(r.json['id']), 'expired')
        self.assertEqual([self.public(d[:7])['days'][d] for d in days], ['free', 'free'])

    def test_two_confirmations_at_the_same_time(self):
        days = [day(33), day(34)]
        r1 = self.ask(self.divers[4], days); r2 = self.ask(self.divers[5], days[1:])
        results = []
        def confirm(bid):
            c = Client(self.server); c.login('pro_tito')
            results.append(c.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'}).status)
        th = [threading.Thread(target=confirm, args=(b,)) for b in (r1.json['id'], r2.json['id'])]
        [x.start() for x in th]; [x.join() for x in th]
        states = sorted([self.status(r1.json['id']), self.status(r2.json['id'])])
        self.assertEqual(sum(s in ('confirmed', 'accepted_pending_payment') for s in states), 1, (states, results))
        self.assertIn('rejected', states)
        n = self.server.sql("""SELECT COUNT(DISTINCT ref_id) n FROM resource_blocks WHERE status='active' AND ref_type='booking' AND ref_id IN (?,?)""", (r1.json['id'], r2.json['id']))[0]['n']
        self.assertEqual(n, 1)

    def test_pay_to_book_holds_days_and_half_days(self):
        d = day(45); m = d[:7]
        r = self.ask(self.divers[0], [d], sid=self.pay_sid)
        self.assertEqual((r.status, r.json['status']), (200, 'payment_in_progress'), r)
        self.assertEqual(self.public(m, self.pay_sid)['days'][d], 'busy')        # held while paying
        self.assertEqual(self.public(m)['days'][d], 'busy')                       # same freelance, his other service too
        self.assertEqual(self.ask(self.divers[1], [d], sid=self.pay_sid).status, 400)
        sess = self.stripe.last_session(); self.stripe.pay(sess['id'])
        ev = {'id': f'evt_{time.time_ns()}', 'type': 'checkout.session.completed', 'account': 'acct_tito', 'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
        payload, sig = StripeMock.signed(ev, CONNECT_SECRET)
        Client(self.server, origin=None).request('POST', '/api/payments/webhook/connect', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
        self.assertEqual(self.status(r.json['id']), 'confirmed')
        # Half days: the morning of another day, then the afternoon; the full day is not possible any more
        h = day(47)
        ra = self.ask(self.divers[2], [h], part='am'); self.pro.post(f"/api/bookings/{ra.json['id']}/status", {'status': 'confirmed'})
        self.assertEqual(self.public(h[:7])['days'][h], 'am')
        self.assertEqual(self.ask(self.divers[3], [h], part='full').status, 400)
        self.assertEqual(self.ask(self.divers[3], [h], part='pm').status, 200)

    def test_export_includes_the_agenda(self):
        d = day(90)
        self.pro.post('/api/agenda/block', {'date_from': d, 'date_to': d, 'note': 'Revisión del equipo'})
        r = self.pro.get('/api/center/export?kind=agenda')
        self.assertEqual(r.status, 200, r)
        txt = r.body.decode('utf-8')
        # v50.57: the dates as Excel in Spanish writes them (dd/mm/yyyy)
        self.assertIn('Recurso', txt); self.assertIn('/'.join(reversed(d.split('-'))), txt); self.assertIn('Revisión del equipo', txt)

    def test_quote_and_rules(self):
        q = self.client().post('/api/agenda/quote', {'service_id': self.sid, 'days': [day(60), day(61), day(62)], 'part': 'full', 'participants': 2, 'agenda_extras': ['foto']})
        self.assertEqual((q.status, q.json['total']), (200, 606.0), q)
        self.assertEqual(self.client().post('/api/agenda/quote', {'service_id': self.sid, 'days': [day(60)], 'participants': 9}).status, 400)
        self.assertEqual(self.client().post('/api/agenda/quote', {'service_id': self.sid, 'days': [day(0)]}).status, 400)   # inside the notice
        self.assertEqual(self.client().post('/api/agenda/quote', {'service_id': self.sid, 'days': [day(60), day(62)]}).status, 400)   # not consecutive

    def test_hours_and_plan(self):
        self.assertEqual(self.pro.post('/api/agenda/hours', {'weekdays': [], 'closures': []}).status, 400)
        self.assertEqual(self.pro.post('/api/agenda/hours', {'weekdays': [0, 1, 2, 3, 4, 5, 6], 'closures': [{'from': day(80), 'to': day(85), 'label': 'Lluvias'}], 'timezone': 'America/Cancun'}).status, 200)
        self.assertEqual(self.public(day(82)[:7])['days'][day(82)], 'off')
        # Without the plan feature, no service by days (never a silent fallback)
        self.server.sql("UPDATE users SET plan_code='free',plan_expires_at=NULL WHERE id=?", (self.other.user['id'],))
        r = self.other.post('/api/provider-services', {'title': 'Por días sin plan', 'price': 50, 'booking_unit': 'day', 'pricing': {'day': 50}})
        # v50.58 (owner's decision, 16/10/2026): the free plan of a freelance has no own services at all
        self.assertEqual((r.status, r.json.get('plan_required')), (403, 'online_bookings'), r)

    def test_month_of_agenda_is_fast(self):
        """A4.5: a month of a provider with a busy agenda, among 500 others, in ≤ 300 ms on the server."""
        now = dt.datetime.now(UTC).strftime('%Y-%m-%dT%H:%M:%SZ')
        rows = []
        import sqlite3
        db = sqlite3.connect(self.server.db)
        try:
            for i in range(500):
                cur = db.execute("INSERT INTO resources(owner_user_id,kind,name,timezone,created_at,updated_at) VALUES(?,'person',?,'Europe/Madrid',?,?)", (self.admin_id(), f'r{i}', now, now))
                rid = cur.lastrowid
                for k in range(30):
                    dd = (dt.date.today() + dt.timedelta(days=k)).isoformat(); s, e = wag.block_span(dd, dd, 'full', wag.DEFAULT_RULES, 'Europe/Madrid')
                    rows.append((rid, s, e, dd, dd))
            db.executemany("INSERT INTO resource_blocks(resource_id,starts_at,ends_at,local_date_from,local_date_to,kind,status,created_at) VALUES(?,?,?,?,?,'manual','active','x')", rows)
            db.commit()
        finally:
            db.close()
        m = day(70)[:7]
        best = 9.0
        for _ in range(5):
            t0 = time.perf_counter(); r = self.client().get(f'/api/agenda/public?service={self.sid}&month={m}'); best = min(best, time.perf_counter() - t0)
            self.assertEqual(r.status, 200)
        self.assertLess(best, 0.3, best)
        t0 = time.perf_counter(); self.pro.get(f'/api/agenda/mine?month={m}'); self.assertLess(time.perf_counter() - t0, 0.3)

    def admin_id(self):
        return self.server.sql("SELECT id FROM users WHERE role='admin' LIMIT 1")[0]['id']


if __name__ == '__main__':
    unittest.main()
