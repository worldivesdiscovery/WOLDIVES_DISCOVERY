"""v50.49 · la app, tandas 2 a 4: perfiles del equipo por centro, cerrar la cuenta de un centro o freelance (seis
meses para volver) y lo que la app profesional pide al servidor.

Stripe es un simulador local: nada sale de la máquina. Cada clase usa una copia temporal de la base."""
import datetime as dt
import time
import unittest

from helpers import Client, MiddayClock, ServerTestCase, IN_PERSON
from stripe_mock import StripeMock

CONNECT_SECRET = 'whsec_connect_local'
def outbox(server, template, to=None):
    q = 'SELECT * FROM email_outbox WHERE template=?' + (' AND to_email=?' if to else '') + ' ORDER BY id DESC'
    return server.sql(q, (template, to) if to else (template,))


DAY = lambda n: (dt.date.today() + dt.timedelta(days=n)).isoformat()


class ProBase(ServerTestCase):
    """Shared helpers: a centre with a service, departures and bookings."""

    def join(self, center, email, role, username):
        r = center.post('/api/center/team/invite', {'email': email, 'member_role': role})
        self.assertEqual(r.status, 200, r)
        import re
        tok = re.search(r'equipo\?token=([A-Za-z0-9_\-]+)', outbox(self.server, 'team_invite', email)[0]['text']).group(1)
        c = self.client()
        r = c.post('/api/team/join', {'token': tok, 'fullname': f'Persona {username}', 'username': username, 'password': 'buceo-seguro-2026', 'accept_terms': True})
        self.assertEqual(r.status, 200, r)
        c.user = c.me()['user']
        return c

    def slot(self, center, sid, days, time_='09:00', spots=20):
        r = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': DAY(days), 'slot_time': time_, 'spots_total': spots})
        self.assertEqual(r.status, 200, r)
        return r.json['slot_id']

    def booked(self, d, cid, sid, slot, status='confirmed', n=1):
        r = d.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': n})
        self.assertEqual(r.status, 200, r)
        if status: self.server.sql("UPDATE bookings SET status=?,payment_status='at_center' WHERE id=?", (status, r.json['id']))
        return r.json['id']


class Roles(ProBase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'roles9', phone='+34 600 490 001')
        cls.other = t.make_center(cls.admin, 'otro9', phone='+34 600 490 002')
        cls.cid = cls.center.user['center_id']
        cls.server.sql("UPDATE centers SET plan_code='pro',plan_status='active' WHERE id IN (?,?)", (cls.cid, cls.other.user['center_id']))

    def test_1_catalogue_and_builtin_roles(self):
        d = self.center.get('/api/center/team').json
        keys = [r['key'] for r in d['role_list']]
        self.assertEqual(keys[:4], ['owner', 'manager', 'reception', 'instructor'])
        self.assertEqual(d['roles']['manager'], 'Encargado')
        perms = {p['key'] for p in d['permissions']}
        self.assertTrue({'checkin', 'todas_salidas', 'barco', 'reservas', 'salidas', 'avisos', 'cobros', 'centro', 'estadisticas'} <= perms)
        self.assertIn('El plan', d['owner_only'])
        inst = [r for r in d['role_list'] if r['key'] == 'instructor'][0]
        self.assertEqual(inst['permissions'], ['checkin'])
        by = {r['key']: r['permissions'] for r in d['role_list']}
        self.assertEqual(len(by['manager']), len(d['permissions']))                 # «Encargado: todo lo demás» (13/10)
        self.assertNotIn('avisos', by['reception'])                                  # as in v50.47
        me = self.center.me()
        self.assertEqual(me['member_role'], 'owner'); self.assertIn('cobros', me['permissions']); self.assertIsNone(me['account_closed'])

    def test_2_custom_role_from_the_web_reaches_the_app(self):
        r = self.center.post('/api/center/team/roles/save', {'name': 'Instructor máster', 'permissions': ['checkin', 'todas_salidas', 'barco', 'inventado']})
        self.assertEqual(r.status, 200, r)
        key = r.json['key']; self.assertRegex(key, r'^r[0-9a-f]{8}$')
        self.assertEqual(self.center.post('/api/center/team/roles/save', {'name': 'instructor MÁSTER', 'permissions': []}).status, 400)   # same name
        self.assertEqual(self.center.post('/api/center/team/roles/save', {'name': '', 'permissions': []}).status, 400)
        m = self.join(self.center, 'master9@example.org', key, 'master9')
        me = m.me()
        self.assertEqual(me['member_role'], key); self.assertEqual(me['member_role_name'], 'Instructor máster')
        self.assertEqual(me['permissions'], ['checkin', 'todas_salidas', 'barco'])
        # what the role allows and what it does not
        sid = self.center.post('/api/provider-services', {'title': 'Doble roles', 'price': 40}).json['id']
        self.assertEqual(m.post('/api/provider-services', {'title': 'No', 'price': 1}).status, 403)         # salidas
        self.assertEqual(m.post('/api/manifest/boats/save', {'name': 'Neptuno', 'capacity': 12}).status, 200)  # barco
        self.assertEqual(m.get('/api/provider/payments').status, 403)                                        # cobros
        self.assertEqual(m.get('/api/provider/stats').status, 403)                                           # estadísticas
        self.assertEqual(m.post('/api/center/team/invite', {'email': 'x@example.org', 'member_role': 'reception'}).status, 403)
        self.assertEqual(m.post('/api/center/team/roles/save', {'name': 'Yo mismo', 'permissions': ['cobros']}).status, 403)   # only the owner
        # the owner changes the role in the web: the next request already uses the new permissions
        self.assertEqual(self.center.post('/api/center/team/roles/save', {'key': key, 'name': 'Instructor máster', 'permissions': ['checkin', 'estadisticas']}).status, 200)
        self.assertEqual(m.get('/api/provider/stats').status, 200)
        self.assertEqual(m.post('/api/manifest/boats/save', {'name': 'Tritón', 'capacity': 8}).status, 403)
        self.assertEqual(m.me()['permissions'], ['checkin', 'estadisticas'])
        # a role in use is not deleted; another centre cannot use it or change it
        self.assertEqual(self.center.post('/api/center/team/roles/delete', {'key': key}).status, 400)
        self.assertEqual(self.other.post('/api/center/team/roles/save', {'key': key, 'name': 'Robado', 'permissions': ['cobros']}).status, 400)
        self.assertEqual(self.other.post('/api/center/team/invite', {'email': 'y@example.org', 'member_role': key}).status, 400)
        self.assertEqual(self.center.post('/api/center/team/role', {'user_id': m.user['id'], 'member_role': 'instructor'}).status, 200)
        self.assertEqual(self.center.post('/api/center/team/roles/delete', {'key': key}).status, 200)
        acts = [a['action'] for a in self.center.get('/api/center/activity').json['items']]
        self.assertIn('team_role_saved', acts); self.assertIn('team_role_deleted', acts)
        self.assertTrue(sid)

    def test_3_builtin_roles_change_and_go_back(self):
        rec = self.join(self.center, 'recep9@example.org', 'reception', 'recep9')
        self.assertEqual(rec.post('/api/provider-services', {'title': 'Recepción crea', 'price': 20}).status, 200)
        self.assertEqual(self.center.post('/api/center/team/roles/save', {'key': 'reception', 'permissions': ['reservas']}).status, 200)
        self.assertEqual(rec.post('/api/provider-services', {'title': 'Ya no', 'price': 20}).status, 403)
        self.assertEqual(self.center.post('/api/center/team/roles/save', {'key': 'reception', 'reset': True}).status, 200)
        self.assertEqual(rec.post('/api/provider-services', {'title': 'Otra vez sí', 'price': 20}).status, 200)
        self.assertEqual(self.center.post('/api/center/team/roles/save', {'key': 'owner', 'permissions': []}).status, 400)
        self.assertEqual(self.center.post('/api/center/team/roles/delete', {'key': 'manager'}).status, 400)
        # the notices permission moves with the role
        man = self.join(self.center, 'manag9@example.org', 'manager', 'manag9')
        self.assertTrue(man.get('/api/avisos/ajustes').json['can_send'])
        self.assertFalse(rec.get('/api/avisos/ajustes').json['can_send'])
        self.assertEqual(self.center.post('/api/center/team/roles/save', {'key': 'reception', 'permissions': ['reservas', 'avisos']}).status, 200)
        self.assertTrue(rec.get('/api/avisos/ajustes').json['can_send'])
        self.assertEqual(self.center.post('/api/center/team/roles/save', {'key': 'reception', 'reset': True}).status, 200)

    def test_4_unknown_role_value_is_never_owner(self):
        u = self.join(self.center, 'raro9@example.org', 'instructor', 'raro9')
        self.server.sql("UPDATE center_members SET member_role='rdeadbeef' WHERE user_id=?", (u.user['id'],))
        me = u.me()
        self.assertEqual(me['permissions'], [])
        self.assertEqual(u.get('/api/provider/payments').status, 403)
        self.assertEqual(u.post('/api/manifest/sync', {'changes': []}).status, 403)


class CloseAccount(ProBase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base, 'STRIPE_CONNECT_WEBHOOK_SECRET': CONNECT_SECRET}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'cierre9', phone='+34 600 491 001')
        cls.cid = cls.center.user['center_id']
        cls.server.sql("UPDATE centers SET stripe_account_id='acct_cierre9',stripe_charges_enabled=1,stripe_payouts_enabled=1,plan_code='pro',plan_status='active' WHERE id=?", (cls.cid,))
        cls.sid = cls.center.post('/api/provider-services', {'title': 'Doble cierre', 'price': 50, 'booking_mode': 'payment'}).json['id']

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def paid(self, d, slot):
        r = d.post('/api/bookings', {'center_id': self.cid, 'service_id': self.sid, 'slot_id': slot, 'participants': 1})
        self.assertEqual(r.status, 200, r)
        sess = self.stripe.last_session(); self.stripe.pay(sess['id'])
        ev = {'id': f'evt_{time.time_ns()}', 'type': 'checkout.session.completed', 'account': 'acct_cierre9', 'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
        payload, sig = StripeMock.signed(ev, CONNECT_SECRET)
        Client(self.server, origin=None).request('POST', '/api/payments/webhook/connect', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
        return r.json['id']

    def test_close_cancel_all_reopen_and_purge(self):
        rec = self.join(self.center, 'recep-c9@example.org', 'reception', 'recepc9')
        sl = self.slot(self.center, self.sid, 5)
        d1, d2 = self.make_diver('cierre9a'), self.make_diver('cierre9b')
        b_paid = self.paid(d1, sl)
        b_conf = self.booked(d2, self.cid, self.sid, sl)
        self.assertEqual(self.server.sql('SELECT status FROM bookings WHERE id=?', (b_paid,))[0]['status'], 'confirmed')
        # only the owner
        self.assertEqual(rec.get('/api/provider/cuenta').status, 403)
        self.assertEqual(rec.post('/api/provider/cuenta/cerrar', {'password': 'buceo-seguro-2026'}).status, 403)
        st = self.center.get('/api/provider/cuenta').json
        self.assertEqual(st['future_count'], 2); self.assertFalse(st['can_close']); self.assertEqual(st['refund_total'], 50); self.assertEqual(st['keep_days'], 183)
        # blocked while there are future bookings
        r = self.center.post('/api/provider/cuenta/cerrar', {'password': 'buceo-seguro-2026'})
        self.assertEqual(r.status, 409, r); self.assertEqual(r.json['future_count'], 2)
        self.assertEqual(self.center.post('/api/provider/cuenta/cancelar-todo', {}).status, 409)          # explicit confirmation
        r = self.center.post('/api/provider/cuenta/cancelar-todo', {'confirm': True})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['result']['cancelled'], 2); self.assertEqual(r.json['result']['refunded'], 1); self.assertEqual(r.json['result']['amount'], 50)
        self.assertTrue(r.json['can_close'])
        rows = {x['id']: x for x in self.server.sql('SELECT id,status,refunded_total FROM bookings WHERE id IN (?,?)', (b_paid, b_conf))}
        self.assertEqual(rows[b_paid]['status'], 'cancelled'); self.assertEqual(rows[b_conf]['status'], 'cancelled')
        self.assertEqual(float(rows[b_paid]['refunded_total'] or 0), 50.0)
        self.assertTrue(outbox(self.server, 'booking_cancelled_center', 'cierre9b@diver.example.org'))
        # wrong password, then closed
        self.assertEqual(self.center.post('/api/provider/cuenta/cerrar', {'password': 'mala'}).status, 400)
        r = self.center.post('/api/provider/cuenta/cerrar', {'password': 'buceo-seguro-2026'})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['purge_after'], (dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=183)).date().isoformat())
        # signed out; hidden from the public; nobody can book
        self.assertFalse(self.center.get('/api/me').json['authenticated'])
        self.assertEqual(self.server.sql('SELECT active FROM centers WHERE id=?', (self.cid,))[0]['active'], 0)
        self.assertNotEqual(self.make_diver('cierre9c').post('/api/bookings', {'center_id': self.cid, 'service_id': self.sid, 'slot_id': sl, 'participants': 1}).status, 200)
        # the owner signs in: reads, does not change anything, reopens
        self.assertEqual(self.center.login('center_cierre9').status, 200)
        me = self.center.me(); self.assertEqual(me['account_closed']['days_left'], 183)
        self.assertEqual(self.center.get('/api/bookings').status, 200)
        self.assertEqual(self.center.post('/api/provider-services', {'title': 'No', 'price': 1}).status, 403)
        self.assertEqual(rec.login('recepc9').status, 200)
        self.assertEqual(rec.get('/api/bookings').status, 403)                       # the team no longer sees the private data
        self.assertEqual(rec.post('/api/provider/cuenta/reabrir', {}).status, 403)     # only the owner reopens
        r = self.center.post('/api/provider/cuenta/reabrir', {})
        self.assertEqual(r.status, 200, r); self.assertIsNone(r.json['closed'])
        self.assertEqual(self.server.sql('SELECT active FROM centers WHERE id=?', (self.cid,))[0]['active'], 1)
        self.assertEqual(self.server.sql('SELECT active FROM provider_services WHERE id=?', (self.sid,))[0]['active'], 1)
        self.assertEqual(rec.get('/api/bookings').status, 200)
        # closed again and six months later: deleted except the payments
        self.assertEqual(self.center.post('/api/provider/cuenta/cerrar', {'password': 'buceo-seguro-2026'}).status, 200)
        self.server.sql("UPDATE provider_closures SET purge_after='2000-01-01T00:00:00+00:00' WHERE provider_oid=? AND reopened_at IS NULL", (self.cid,))
        r = self.admin.post('/api/admin/retention', {'run_now': True})
        self.assertEqual(r.status, 200, r)
        c = self.server.sql('SELECT name,phone,email,website,active,legal_name FROM centers WHERE id=?', (self.cid,))[0]
        self.assertEqual(c['name'], 'Centro eliminado'); self.assertIsNone(c['phone']); self.assertIsNone(c['website']); self.assertEqual(c['active'], 0)
        owner = self.server.sql('SELECT fullname,email,password_hash FROM users WHERE id=?', (self.center.user['id'],))[0]
        self.assertEqual(owner['fullname'], 'Usuario eliminado'); self.assertEqual(owner['password_hash'], '!')
        self.assertEqual(self.server.sql('SELECT fullname FROM users WHERE id=?', (rec.user['id'],))[0]['fullname'], 'Usuario eliminado')
        b = self.server.sql('SELECT contact_name,contact_email,price,refunded_total FROM bookings WHERE id=?', (b_paid,))[0]
        self.assertIsNone(b['contact_email']); self.assertEqual(float(b['refunded_total']), 50.0)
        self.assertTrue(self.server.sql('SELECT 1 FROM payment_orders WHERE booking_id=?', (b_paid,)))          # payments kept (law)
        self.assertFalse(self.server.sql('SELECT 1 FROM center_members WHERE center_id=?', (self.cid,)))
        cl = self.server.sql('SELECT purged_at,purge_report FROM provider_closures WHERE provider_oid=? ORDER BY id DESC LIMIT 1', (self.cid,))[0]
        self.assertIsNotNone(cl['purged_at'], cl['purge_report'])
        self.assertEqual(self.center.login('center_cierre9').status, 401)

    def test_freelance_close_and_reopen(self):
        f = self.make_freelance(self.admin, 'libre9')
        sid = f.post('/api/provider-services', {'title': 'Bautizo libre', 'price': 60, **IN_PERSON}).json['id']
        self.assertEqual(self.client().get(f"/api/providers/{f.user['id']}").status, 200)
        self.assertEqual(f.get('/api/provider/cuenta').json['future_count'], 0)
        self.assertEqual(f.post('/api/provider/cuenta/cerrar', {'password': 'buceo-seguro-2026'}).status, 200)
        self.assertEqual(self.client().get(f"/api/providers/{f.user['id']}").status, 404)
        self.assertEqual(self.server.sql('SELECT active FROM provider_services WHERE id=?', (sid,))[0]['active'], 0)
        self.assertEqual(f.login('pro_libre9').status, 200)
        self.assertEqual(f.post('/api/provider/cuenta/reabrir', {}).status, 200)
        self.assertEqual(self.client().get(f"/api/providers/{f.user['id']}").status, 200)
        self.assertEqual(self.server.sql('SELECT active FROM provider_services WHERE id=?', (sid,))[0]['active'], 1)



class ProApp(MiddayClock, ProBase):   # «today» at 23:30 must still be ahead
    """What the professional app asks the server: Hoy, agenda, QR scan, headcount, WhatsApp and the boat summary."""
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.A = t.make_center(cls.admin, 'proa9', phone='+34 600 492 001')
        cls.B = t.make_center(cls.admin, 'prob9', phone='+34 600 492 002')
        cls.cidA, cls.cidB = cls.A.user['center_id'], cls.B.user['center_id']
        cls.server.sql("UPDATE centers SET plan_code='pro',plan_status='active' WHERE id IN (?,?)", (cls.cidA, cls.cidB))
        cls.sA = cls.A.post('/api/provider-services', {'title': 'Doble mañana', 'price': 45}).json['id']
        cls.sB = cls.B.post('/api/provider-services', {'title': 'Doble B', 'price': 30}).json['id']
        cls.at_midday(cls.sA, cls.sB)

    def token(self, bid):
        return self.server.sql('SELECT public_token FROM bookings WHERE id=?', (bid,))[0]['public_token']

    def test_1_today_scan_headcount(self):
        today = self.slot(self.A, self.sA, 0, '23:30'); tomorrow = self.slot(self.A, self.sA, 1, '09:00')
        d1 = self.make_diver('hoy9a'); d2 = self.make_diver('hoy9b')
        self.assertEqual(d1.post('/api/account/profile', {'phone': '+34 611 222 333', 'preferred_language': 'fr'}).status, 200)
        b1 = self.booked(d1, self.cidA, self.sA, today, n=2)
        b2 = self.booked(d2, self.cidA, self.sA, tomorrow)
        req = self.booked(self.make_diver('hoy9c'), self.cidA, self.sA, today, status=None)        # a request
        self.server.sql("UPDATE bookings SET response_deadline=? WHERE id=?", ((dt.datetime.now() + dt.timedelta(minutes=50)).isoformat(timespec='minutes'), req))
        h = self.A.get('/api/pro/hoy').json
        self.assertEqual(h['counts']['slots'], 1); self.assertEqual(h['counts']['divers'], 2)
        self.assertEqual([x['slot_id'] for x in h['slots']], [today]); self.assertEqual([x['slot_id'] for x in h['tomorrow_slots']], [tomorrow])
        self.assertEqual(h['requests'], 1); self.assertEqual(h['urgent'][0]['booking_id'], req)
        self.assertEqual(self.B.get('/api/pro/hoy').json['counts']['divers'], 0)                     # nothing of A
        ag = self.A.get('/api/pro/agenda?desde=' + DAY(0) + '&dias=7').json
        self.assertEqual(len(ag['days']), 7); self.assertEqual(ag['days'][1]['people'], 1)
        # scan: typed code, the other centre, wrong code, another day, twice
        code = f"{b1}-{self.token(b1)[:6].upper()}"
        self.assertEqual(self.B.post('/api/pro/escanear', {'code': code}).json['result'], 'otro_centro')
        self.assertEqual(self.A.post('/api/pro/escanear', {'code': f'{b1}-ZZZZZZ'}).json['result'], 'no_valido')
        self.assertEqual(self.A.post('/api/pro/escanear', {'code': 'hola'}).json['result'], 'no_valido')
        url = f"http://x/#/verificarreserva?id={b2}&t={self.token(b2)}"
        self.assertEqual(self.A.post('/api/pro/escanear', {'code': url}).json['result'], 'otro_dia')
        self.assertEqual(self.A.post('/api/pro/escanear', {'code': code, 'slot_id': tomorrow}).json['result'], 'otra_salida')
        r = self.A.post('/api/pro/escanear', {'code': code, 'slot_id': today}).json
        self.assertEqual(r['result'], 'ok', r); self.assertTrue(r['marked']); self.assertEqual(len(r['booking']['seats']), 2)
        self.assertEqual(self.A.post('/api/pro/escanear', {'code': code}).json['result'], 'usado')
        self.assertEqual(self.A.get('/api/pro/hoy').json['counts']['present'], 2)
        self.assertEqual(self.A.post('/api/pro/escanear', {'code': f"{req}-{self.token(req)[:6]}"}).json['result'], 'sin_aceptar')
        # headcount
        c = self.A.post('/api/pro/contar', {'slot_id': today, 'count': 3}).json
        self.assertEqual((c['counted'], c['present'], c['match'], c['diff']), (3, 2, False, 1))
        self.assertTrue(self.A.post('/api/pro/contar', {'slot_id': today, 'count': 2}).json['match'])
        self.assertEqual(self.B.post('/api/pro/contar', {'slot_id': today, 'count': 2}).status, 404)
        # an instructor (only «checkin») scans but does not accept requests; does not see «Solicitudes»
        ins = self.join(self.A, 'ins-pro9@example.org', 'instructor', 'inspro9')
        self.assertIsNone(ins.get('/api/pro/hoy').json['requests'])
        self.assertEqual(ins.post('/api/pro/escanear', {'code': code}).json['result'], 'usado')
        self.assertEqual(ins.post(f'/api/bookings/{req}/status', {'status': 'confirmed'}).status, 403)
        self.server.sql("UPDATE center_members SET member_role='reception' WHERE user_id=?", (ins.user['id'],))
        self.assertEqual(self.A.post('/api/center/team/roles/save', {'key': 'reception', 'permissions': ['reservas']}).status, 200)
        self.assertEqual(ins.post('/api/pro/escanear', {'code': code}).status, 403)                 # without «checkin»
        self.assertEqual(self.A.post('/api/center/team/roles/save', {'key': 'reception', 'reset': True}).status, 200)

    def test_2_whatsapp_in_the_clients_language_and_boat_summary(self):
        sl = self.slot(self.A, self.sA, 2, '10:00')
        d = self.make_diver('wa9')
        self.assertEqual(d.post('/api/account/profile', {'phone': '+33 6 12 34 56 78', 'preferred_language': 'fr'}).status, 200)
        bid = self.booked(d, self.cidA, self.sA, sl)
        w = self.A.get(f'/api/bookings/{bid}/whatsapp').json
        self.assertEqual(w['lang'], 'fr'); self.assertTrue(w['phone_ok'], w)
        self.assertTrue(w['url'].startswith('https://wa.me/33612345678?text=Bonjour'), w['url'])
        self.assertIn('Doble mañana', w['text'])
        p = self.A.get(f'/api/bookings/{bid}/whatsapp?tipo=pago').json
        self.assertIn('/#/reserva?id=', p['text'])
        self.assertEqual(self.B.get(f'/api/bookings/{bid}/whatsapp').status, 404)
        self.assertTrue(any(a['action'] == 'phones_viewed' for a in self.A.get('/api/center/activity').json['items']))
        r = self.A.get(f'/api/manifest/{sl}/resumen.pdf')
        self.assertEqual(r.status, 200); self.assertTrue(r.body.startswith(b'%PDF'))
        self.assertEqual(self.B.get(f'/api/manifest/{sl}/resumen.pdf').status, 404)
        ev = self.server.sql("SELECT details FROM slot_events WHERE slot_id=? AND kind='boat_summary'", (sl,))
        self.assertTrue(ev and 'sha256' in ev[0]['details'])

    def test_4_manual_booking_with_phone(self):
        """Fixed in v50.49: a booking typed by the centre with the client's phone was refused (phone stored in clear)."""
        sl = self.slot(self.A, self.sA, 4)
        r = self.A.post('/api/center/bookings/manual', {'fullname': 'Marta Teléfono', 'phone': '+34 622 000 111', 'service_id': self.sA, 'slot_id': sl, 'participants': 2})
        self.assertEqual(r.status, 200, r)
        import sqlite3
        con = sqlite3.connect(str(self.server.db))
        raw = con.execute('SELECT up.phone FROM user_profiles up JOIN bookings b ON b.user_id=up.user_id WHERE b.id=?', (r.json['id'],)).fetchone()[0]; con.close()
        self.assertNotIn('622', raw or '')                       # encrypted in the database
        w = self.A.get(f"/api/bookings/{r.json['id']}/whatsapp").json
        self.assertTrue(w['phone_ok'], w); self.assertIn('34622000111', w['url'])

    def test_3_booking_code_for_the_diver(self):
        sl = self.slot(self.A, self.sA, 3)
        d = self.make_diver('code9')
        bid = self.booked(d, self.cidA, self.sA, sl)
        b = d.get(f'/api/bookings/{bid}').json
        self.assertEqual(b.get('check_code') or b.get('booking', {}).get('check_code'), f"{bid}-{self.token(bid)[:6].upper()}")



class FcmMock:
    """Local stand-in of Google's token endpoint and Firebase Cloud Messaging (nothing leaves the machine)."""
    def __init__(self):
        import json as _j, threading
        from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
        mock = self; self.sent = []; self.tokens = 0
        class H(BaseHTTPRequestHandler):
            def log_message(self, *a): pass
            def do_POST(self):
                body = self.rfile.read(int(self.headers.get('Content-Length') or 0))
                if self.path == '/token':
                    mock.tokens += 1; out, code = {'access_token': 'ya29.prueba', 'expires_in': 3600}, 200
                else:
                    msg = _j.loads(body)['message']
                    if msg['token'] == 'movil-desinstalado': out, code = {'error': {'status': 'NOT_FOUND', 'details': [{'errorCode': 'UNREGISTERED'}]}}, 404
                    else:
                        mock.sent.append({'auth': self.headers.get('Authorization'), **msg}); out, code = {'name': 'projects/p/messages/1'}, 200
                raw = _j.dumps(out).encode(); self.send_response(code); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(raw))); self.end_headers(); self.wfile.write(raw)
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.base = f'http://127.0.0.1:{self.httpd.server_address[1]}'
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def credentials(self, folder):
        from cryptography.hazmat.primitives import serialization
        from cryptography.hazmat.primitives.asymmetric import rsa
        import json as _j
        key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
        pem = key.private_bytes(serialization.Encoding.PEM, serialization.PrivateFormat.PKCS8, serialization.NoEncryption()).decode()
        p = folder / 'firebase-prueba.json'
        p.write_text(_j.dumps({'type': 'service_account', 'client_email': 'prueba@worldives-pruebas.iam.gserviceaccount.com', 'private_key': pem, 'token_uri': self.base + '/token'}))
        return str(p)

    def stop(self):
        self.httpd.shutdown()


class Push(ProBase):
    """Push to the app through Firebase, only when it is configured in the .env (here a local simulator)."""
    @classmethod
    def setUpClass(cls):
        import tempfile
        from pathlib import Path
        cls.fcm = FcmMock(); folder = Path(tempfile.mkdtemp(prefix='wod-fcm-'))
        cls.extra_env = {'WOD_FCM_PROJECT_ID': 'worldives-pruebas', 'WOD_FCM_CREDENTIALS': cls.fcm.credentials(folder), 'WOD_FCM_API_BASE': cls.fcm.base, 'WOD_MAINTENANCE_SECONDS': '2'}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'push9', phone='+34 600 493 001')
        cls.cid = cls.center.user['center_id']
        cls.sid = cls.center.post('/api/provider-services', {'title': 'Doble push', 'price': 40, 'booking_mode': 'request'}).json['id']

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.fcm.stop()

    def test_push_follows_the_email_in_the_divers_language(self):
        d = self.make_diver('push9a')
        self.assertTrue(d.get('/api/app/push').json['enabled'])
        self.assertEqual(d.post('/api/app/push/register', {'token': 'movil-de-prueba-1', 'platform': 'android'}).json, {'ok': True, 'enabled': True})
        self.assertEqual(d.post('/api/account/language', {'lang': 'fr'}).status, 200)
        sl = self.slot(self.center, self.sid, 3)
        bid = self.booked(d, self.cid, self.sid, sl, status=None)
        self.assertEqual(self.center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'}).status, 200)
        end = time.time() + 15
        while time.time() < end and not any(m['data'].get('ruta') == f'#/reserva?id={bid}' for m in self.fcm.sent): time.sleep(0.3)
        mine = [m for m in self.fcm.sent if m['token'] == 'movil-de-prueba-1']
        self.assertTrue(mine, self.server.sql('SELECT * FROM push_outbox'))
        self.assertEqual(mine[-1]['auth'], 'Bearer ya29.prueba')
        self.assertIn('application', mine[-1]['notification']['body'])                                 # French
        self.assertTrue(any(m['data']['ruta'] == f'#/reserva?id={bid}' for m in mine))
        # a phone that uninstalled the app is switched off; unregister on sign out
        self.server.sql("INSERT INTO app_devices(user_id,token,platform,created_at,active) VALUES(?,?,?,?,1)", (d.user['id'], 'movil-desinstalado', 'android', '2026-01-01'))
        self.assertEqual(self.center.post(f'/api/bookings/{bid}/status', {'status': 'cancelled', 'reason': 'Prueba'}).status, 200)
        end = time.time() + 15
        while time.time() < end and self.server.sql("SELECT active FROM app_devices WHERE token='movil-desinstalado'")[0]['active']: time.sleep(0.3)
        self.assertEqual(self.server.sql("SELECT active FROM app_devices WHERE token='movil-desinstalado'")[0]['active'], 0)
        self.assertEqual(d.post('/api/app/push/unregister', {'token': 'movil-de-prueba-1'}).status, 200)
        self.assertEqual(self.server.sql("SELECT active FROM app_devices WHERE token='movil-de-prueba-1'")[0]['active'], 0)
        # an instructor can register their phone too (it is their own account, not the centre's data)
        ins = self.join(self.center, 'ins-push9@example.org', 'instructor', 'inspush9')
        self.assertEqual(ins.post('/api/app/push/register', {'token': 'movil-instructor', 'platform': 'android'}).status, 200)


class PushOff(ProBase):
    def test_without_firebase_nothing_is_asked_nor_stored(self):
        t = self; admin = t.make_admin(); d = t.make_diver('nopush9')
        self.assertFalse(d.get('/api/app/push').json['enabled'])
        self.assertEqual(d.post('/api/app/push/register', {'token': 'x'}).json, {'ok': False, 'enabled': False})
        self.assertFalse(self.server.sql('SELECT 1 FROM app_devices'))
        self.assertTrue(admin)



class StaticChecks(unittest.TestCase):
    def test_pro_script_is_cached_and_clean(self):
        import re
        import sys
        from pathlib import Path
        root = Path(__file__).resolve().parents[1]
        version = re.search(r"^APP_VERSION = '([^']+)'", (root / 'app' / 'server.py').read_text(encoding='utf-8'), re.M).group(1)
        sw = (root / 'public' / 'sw.js').read_text(encoding='utf-8')
        self.assertIn(f"'/js/wd-app-pro.js?v={version}'", sw)
        sys.path.insert(0, str(root / 'scripts'))
        from generar_zips import TEST_ACCOUNT
        for f in ('wd-app-pro.js', 'wd-app.js'):
            js = (root / 'public' / 'js' / f).read_text(encoding='utf-8')
            self.assertIsNone(TEST_ACCOUNT.search(js), f)
            self.assertNotRegex(js, r'sk_(?:live|test)_|pk_(?:live|test)_|AIza[0-9A-Za-z_-]{20}')
        self.assertFalse(list((root / 'movil').rglob('google-services.json')), 'el archivo de Firebase no va en el repositorio')


if __name__ == '__main__':
    unittest.main()
