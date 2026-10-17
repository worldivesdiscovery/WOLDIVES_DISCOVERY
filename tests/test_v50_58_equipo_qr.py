"""v50.58 · Equipo del centro con cuentas propias, enlazadas por QR (encargo unificado del 16/10/2026, bloque 1).

Las comprobaciones del encargo en el servidor:
1. Enlazar con QR: el centro escanea el QR de un freelance, elige Encargado; el freelance acepta y entra con su cuenta.
2. QR caducado: un QR de hace 2 minutos no vale; un QR ya escaneado tampoco. El código corto vale y caduca a los 10 min.
3. Invitación por correo a quien no tiene cuenta: crea su cuenta (de freelance) y queda enlazado.
4. «Por días»: hoy tiene acceso; al día siguiente del último lo pierde solo.
5. Dos centros: el selector enseña los dos; ninguno ve lo del otro ni lo propio del freelance.
7. Permisos: con cada perfil, solo lo de su lista; un instructor que pide los cobros recibe «no existe».
8. Desenlazar desde el centro y desde la persona: el acceso se quita al momento, también con la sesión abierta.
9. Registro de actividad con el nombre y el perfil de cada persona.
10. Planes: Ficha gratuita nadie; Motor de reservas una persona y solo Recepción; Pro hasta 15 y la 16 se rechaza; al
    bajar de plan, los que no caben quedan en pausa sin borrarse y se reactivan al subir.
11. Freelance gratuito: se le puede enlazar; no puede crear servicios. Un buceador no se enlaza como Instructor sin
    activar su perfil de freelance.
12. «Compartir para enlazar»: un uso, 24 horas; se puede anular.
"""
import re
import sys
import time
import unittest
from datetime import date, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from helpers import ServerTestCase  # noqa: E402
from wod import equipo_qr as wteq  # noqa: E402

# the centres of the tests are in Xàbia: their «today» is Madrid's (between 22:00 and 24:00 UTC it is already tomorrow there)
DAY = lambda n: (datetime.now(ZoneInfo('Europe/Madrid')).date() + timedelta(days=n)).isoformat()
SECRET = __import__('hashlib').sha256(('wod-qr-personal:' + 'x' * 40).encode()).hexdigest()   # the test server's WOD_SECRET_KEY


def outbox(server, template, to=None):
    q = 'SELECT * FROM email_outbox WHERE template=?' + (' AND to_email=?' if to else '') + ' ORDER BY id DESC'
    return server.sql(q, (template, to) if to else (template,))


class Team(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.c1 = t.make_center(cls.admin, 'mar')
        cls.c2 = t.make_center(cls.admin, 'coral')
        cls.cid1 = cls.c1.user['center_id']; cls.cid2 = cls.c2.user['center_id']
        cls.pro = t.make_freelance(cls.admin, 'ana')            # freelance Pro (trial)
        cls.diver = t.make_diver('bea')
        for cid in (cls.cid1, cls.cid2):
            cls.plan(cid, 'pro')

    @classmethod
    def plan(cls, cid, code):
        cls.server.sql('UPDATE centers SET plan_code=?, plan_status=?, plan_expires_at=? WHERE id=?',
                       (code, 'active' if code != 'free' else 'free', DAY(300) if code != 'free' else None, cid))

    # helpers --------------------------------------------------------------------------------------
    def scan(self, center, who, field='token'):
        q = who.get('/api/my/qr').json
        r = center.post('/api/center/team/scan', {'code': q['url'] if field == 'url' else q[field]})
        return r, q

    def link(self, center, who, role='instructor', **kw):
        r, _ = self.scan(center, who)
        self.assertEqual(r.status, 200, r.json)
        r = center.post('/api/center/team/link', {'ref': r.json['ref'], 'member_role': role, **kw})
        self.assertEqual(r.status, 200, r.json)
        return r.json['id']

    def accept(self, who, lid, **kw):
        r = who.post('/api/my/teams/respond', {'id': lid, 'accept': True, **kw})
        self.assertEqual(r.status, 200, r.json)
        return r.json

    def switch(self, who, cid):
        return who.post('/api/team/switch', {'center': cid})

    def end_all(self, who):
        for x in who.get('/api/my/teams').json['links'] + who.get('/api/my/teams').json['requests']:
            if x['status'] in ('pending', 'active', 'paused'): who.post('/api/my/teams/leave', {'id': x['id']})
        self.switch(who, 0)

    # 1 ------------------------------------------------------------------------------------------------
    def test_1_link_with_qr_and_accept(self):
        r, q = self.scan(self.c1, self.pro, 'url')
        self.assertEqual(r.status, 200, r.json)
        handle = self.server.sql('SELECT qr_handle FROM users WHERE id=?', (self.pro.user['id'],))[0]['qr_handle']
        self.assertEqual(q['token'].split('.')[1], handle, 'only a random handle of the account')
        for personal in (self.pro.user['username'], self.pro.user['email'], self.pro.user['fullname']):
            self.assertNotIn(personal, q['token'] + q['url'])
        p = r.json['person']
        self.assertEqual((p['name'], p['account']), (self.pro.user['fullname'], 'freelance'))
        self.assertNotIn('email', p)
        lid = self.c1.post('/api/center/team/link', {'ref': r.json['ref'], 'member_role': 'manager'}).json['id']
        self.assertEqual(self.c1.post('/api/center/team/link', {'ref': r.json['ref'], 'member_role': 'manager'}).status, 400, 'the scan is used once')
        # nobody is linked without their «yes»
        self.assertEqual(self.switch(self.pro, self.cid1).status, 404)
        reqs = self.pro.get('/api/my/teams').json['requests']
        self.assertEqual([x['id'] for x in reqs], [lid]); self.assertEqual(reqs[0]['role_name'], 'Encargado')
        self.assertTrue(self.server.sql("SELECT 1 FROM messages WHERE recipient_user_id=? AND body LIKE '%quiere añadirte a su equipo como Encargado%'", (self.pro.user['id'],)))
        self.accept(self.pro, lid)
        team = self.c1.get('/api/center/team').json
        self.assertEqual([(x['name'], x['role_name'], x['status']) for x in team['links']], [(self.pro.user['fullname'], 'Encargado', 'active')])
        profiles = self.pro.me()['profiles']
        self.assertEqual([p['key'] for p in profiles], ['own', f'c:{self.cid1}'])
        r = self.switch(self.pro, self.cid1)
        self.assertEqual(r.status, 200, r.json)
        me = self.pro.me()
        self.assertEqual((me['user']['role'], me['user']['center_id'], me['own_role'], me['member_role']), ('center', self.cid1, 'freelance', 'manager'))
        r = self.pro.get(f'/api/provider-services?provider_id={self.pro.user["id"]}&include_inactive=1')
        self.assertEqual(r.status, 200, r.json)
        self.assertEqual(self.pro.get('/api/center/team').status, 404, 'the team is the owner\'s')
        self.assertEqual(self.switch(self.pro, 0).status, 200)
        self.assertEqual(self.pro.me()['user']['role'], 'freelance')
        self.end_all(self.pro)

    # 2 ------------------------------------------------------------------------------------------------
    def test_2_old_qr_used_qr_and_short_code(self):
        self.pro.get('/api/my/qr')
        handle = self.server.sql('SELECT qr_handle FROM users WHERE id=?', (self.pro.user['id'],))[0]['qr_handle']
        old = wteq.qr_token(SECRET, handle, int(time.time()) - 120)        # a screenshot from 2 minutes ago
        r = self.c1.post('/api/center/team/scan', {'code': old})
        self.assertEqual(r.status, 400); self.assertIn('caducado', r.json['error'])
        fresh = wteq.qr_token(SECRET, handle, int(time.time()))
        self.assertEqual(self.c1.post('/api/center/team/scan', {'code': fresh}).status, 200)
        r = self.c1.post('/api/center/team/scan', {'code': fresh})
        self.assertEqual(r.status, 400); self.assertIn('ya se ha usado', r.json['error'])
        forged = fresh[:-3] + ('AAA' if not fresh.endswith('AAA') else 'BBB')
        self.assertEqual(self.c1.post('/api/center/team/scan', {'code': forged}).status, 400)
        q = self.pro.get('/api/my/qr').json
        self.assertEqual(len(q['code']), 6); self.assertGreater(q['code_expires_in'], 590)
        self.assertEqual(self.pro.get('/api/my/qr').json['code'], q['code'], 'the same code for 10 minutes')
        self.assertEqual(self.c1.post('/api/center/team/scan', {'code': q['code'][:3] + ' ' + q['code'][3:].lower()}).status, 200)
        self.assertEqual(self.c1.post('/api/center/team/scan', {'code': q['code']}).status, 400, 'a code is used once')
        q2 = self.pro.get('/api/my/qr').json
        self.assertNotEqual(q2['code'], q['code'], 'a new code once used')
        self.server.sql('UPDATE personal_codes SET expires_at=? WHERE user_id=?', (int(time.time()) - 1, self.pro.user['id']))
        r = self.c1.post('/api/center/team/scan', {'code': q2['code']})
        self.assertEqual(r.status, 400); self.assertIn('caducado', r.json['error'])

    # 3 ------------------------------------------------------------------------------------------------
    def test_3_email_invite_without_account(self):
        email = 'nuevo.instructor@pro.example.org'
        self.assertEqual(self.c1.post('/api/center/team/link-email', {'email': email, 'member_role': 'instructor'}).status, 200)
        tok = re.search(r'equipo\?token=([A-Za-z0-9_\-]+)', outbox(self.server, 'team_invite', email)[0]['text']).group(1)
        c = self.client()
        r = c.post('/api/team/join', {'token': tok, 'fullname': 'Nuevo Instructor', 'username': 'nuevo.instructor', 'password': 'buceo-seguro-2026', 'accept_terms': True})
        self.assertEqual(r.status, 200, r.json)
        me = c.me()
        self.assertEqual((me['user']['role'], me['own_role']), ('freelance', 'freelance'), 'an instructor needs a freelance account')
        self.assertEqual([p['key'] for p in me['profiles']], ['own', f'c:{self.cid1}'])
        self.assertEqual(c.post('/api/team/join', {'token': tok}).status, 400, 'used once')
        c.post('/api/my/teams/leave', {'id': c.get('/api/my/teams').json['links'][0]['id']})

    # 4 ------------------------------------------------------------------------------------------------
    def test_4_link_by_days_ends_by_itself(self):
        lid = self.link(self.c1, self.pro, 'instructor', kind='days', starts_on=DAY(0), ends_on=DAY(0))
        self.accept(self.pro, lid)
        self.assertEqual(self.switch(self.pro, self.cid1).status, 200)
        self.assertEqual(self.pro.me()['user']['center_id'], self.cid1)
        # the next day: the link's last day is yesterday
        self.server.sql('UPDATE team_links SET starts_on=?, ends_on=? WHERE id=?', (DAY(-1), DAY(-1), lid))
        me = self.pro.me()
        self.assertEqual((me['user']['role'], me['user'].get('center_id')), ('freelance', None), 'back to the own profile, by itself')
        self.assertEqual(self.switch(self.pro, self.cid1).status, 404)
        self.assertEqual(self.server.sql('SELECT status FROM team_links WHERE id=?', (lid,))[0]['status'], 'ended')
        # a link that starts tomorrow does not give access today
        self.assertEqual(self.c1.post('/api/center/team/link-email', {'email': 'x@y.org', 'member_role': 'instructor', 'kind': 'days',
                                                                      'starts_on': DAY(-3), 'ends_on': DAY(-2)}).status, 400)

    # 5 ------------------------------------------------------------------------------------------------
    def test_5_two_centres_never_mixed(self):
        a = self.link(self.c1, self.pro, 'instructor'); self.accept(self.pro, a)
        b = self.link(self.c2, self.pro, 'manager'); self.accept(self.pro, b)
        profiles = self.pro.me()['profiles']
        self.assertEqual({p['key'] for p in profiles}, {'own', f'c:{self.cid1}', f'c:{self.cid2}'})
        self.assertEqual(len({p.get('color') for p in profiles if p['key'] != 'own'}), 2, 'each centre with its colour')
        # each centre's own services, and the freelance's own one, never cross
        s1 = self.c1.post('/api/provider-services', {'title': 'Bautizo Mar', 'price': 50, 'booking_mode': 'request'}).json['id']
        s2 = self.c2.post('/api/provider-services', {'title': 'Bautizo Coral', 'price': 55, 'booking_mode': 'request'}).json['id']
        own = self.pro.post('/api/provider-services', {'title': 'Guía privado de Ana', 'price': 90, 'booking_mode': 'request', 'pay_way': 'in_person',
                                                       'pay_methods': ['cash'], 'pay_whatsapp': '+34 611 222 333', 'pay_policy': 'Gratis hasta 24 horas antes.',
                                                       'accept_in_person_terms': True})
        self.assertEqual(own.status, 200, own.json)
        ids = lambda c: {x['id'] for x in c.get(f'/api/provider-services?provider_id={c.user["id"]}&include_inactive=1').json['items']}
        self.switch(self.pro, self.cid1); in1 = ids(self.pro)
        self.switch(self.pro, self.cid2); in2 = ids(self.pro)
        self.switch(self.pro, 0); mine = ids(self.pro)
        self.assertIn(s1, in1); self.assertNotIn(s2, in1); self.assertNotIn(own.json['id'], in1)
        self.assertIn(s2, in2); self.assertNotIn(s1, in2); self.assertNotIn(own.json['id'], in2)
        self.assertEqual(mine & {s1, s2}, set())
        self.assertNotIn(own.json['id'], ids(self.c1)); self.assertNotIn(own.json['id'], ids(self.c2))
        self.end_all(self.pro)

    # 6 ------------------------------------------------------------------------------------------------
    def test_6_busy_never_overlapping_and_my_agenda(self):
        a = self.link(self.c1, self.pro, 'instructor'); self.accept(self.pro, a)
        b = self.link(self.c2, self.pro, 'instructor'); self.accept(self.pro, b)
        uid = self.pro.user['id']; day = DAY(5)
        def slot(center, title, hhmm):
            sid = center.post('/api/provider-services', {'title': title, 'price': 60, 'booking_mode': 'request', 'duration_minutes': 120}).json['id']
            r = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': day, 'slot_time': hhmm, 'spots_total': 8})
            self.assertEqual(r.status, 200, r.json)
            return r.json['slot_id']
        s1 = slot(self.c1, 'Doble inmersión Mar', '09:00')
        s2 = slot(self.c2, 'Bautizo Coral', '10:00')
        s3 = slot(self.c2, 'Nocturna Coral', '15:00')
        r = self.c1.post('/api/provider-services/slot-update', {'id': s1, 'instructor_user_id': uid})
        self.assertEqual(r.status, 200, r.json)
        msg = self.server.sql("SELECT subject, body FROM messages WHERE recipient_user_id=? AND subject LIKE '%te ha asignado una salida%' ORDER BY id DESC", (uid,))
        self.assertTrue(msg and 'Doble inmersión Mar' in msg[0]['body'] and '8 buceadores' not in msg[0]['body'], msg)
        av = {p['user_id']: p['busy'] for p in self.c2.get(f'/api/center/availability?slot_id={s2}').json['people']}
        self.assertTrue(av[uid], 'busy with the other centre, «Ocupado»')
        people = self.c2.get(f'/api/center/availability?slot_id={s2}').json['people']
        self.assertEqual(set(people[0]) - {'user_id', 'name', 'member_role', 'busy', 'role_name'}, set(), 'never with whom nor what for')
        r = self.c2.post('/api/provider-services/slot-update', {'id': s2, 'instructor_user_id': uid})
        self.assertEqual(r.status, 400); self.assertIn('Ocupado', r.json['error'])
        self.assertFalse({p['user_id']: p['busy'] for p in self.c2.get(f'/api/center/availability?slot_id={s3}').json['people']}[uid])
        self.assertEqual(self.c2.post('/api/provider-services/slot-update', {'id': s3, 'instructor_user_id': uid}).status, 200)
        # her own freelance work counts too
        own = self.pro.post('/api/provider-services', {'title': 'Guía privado', 'price': 90, 'booking_mode': 'request', 'duration_minutes': 120, 'pay_way': 'in_person',
                                                       'pay_methods': ['cash'], 'pay_whatsapp': '+34 611 222 333', 'pay_policy': 'Gratis hasta 24 horas antes.',
                                                       'accept_in_person_terms': True}).json['id']
        so = self.pro.post('/api/provider-services/slot', {'service_id': own, 'slot_date': DAY(6), 'slot_time': '10:00', 'spots_total': 2}).json['slot_id']
        self.server.sql('UPDATE service_slots SET spots_available=1 WHERE id=?', (so,))       # somebody booked it
        s4 = slot(self.c1, 'Doble inmersión tarde', '09:00')
        self.server.sql('UPDATE service_slots SET slot_date=?, slot_time=? WHERE id=?', (DAY(6), '11:00', s4))
        r = self.c1.post('/api/provider-services/slot-update', {'id': s4, 'instructor_user_id': uid})
        self.assertEqual(r.status, 400, 'busy with her own work'); self.assertIn('Ocupado', r.json['error'])
        # «Mi agenda»: both centres with their colours, her own work, no clients
        ag = self.pro.get(f'/api/my/agenda?from={day}&to={DAY(6)}').json['items']
        centres = {(i['center'], i['color']) for i in ag if i['kind'] == 'centre'}
        self.assertEqual(len(centres), 2); self.assertEqual(len({c for _, c in centres}), 2)
        self.assertTrue(any(i['kind'] == 'own' for i in ag))
        self.assertTrue(all(set(i) <= {'date', 'time', 'kind', 'center_id', 'center', 'color', 'line', 'what', 'divers'} for i in ag))
        # a change of time is told to whoever works in it
        self.assertEqual(self.c2.post('/api/provider-services/slot-update', {'id': s3, 'slot_time': '16:00'}).status, 200)
        self.assertTrue(self.server.sql("SELECT 1 FROM messages WHERE recipient_user_id=? AND subject LIKE '%ha cambiado una salida tuya%'", (uid,)))
        # after leaving a centre, its future work disappears from the agenda
        self.pro.post('/api/my/teams/leave', {'id': b})
        ag = self.pro.get(f'/api/my/agenda?from={day}&to={DAY(6)}').json['items']
        self.assertFalse(any(i.get('center_id') == self.cid2 for i in ag))
        self.end_all(self.pro)

    # 7 ------------------------------------------------------------------------------------------------
    def test_7_permissions_by_profile(self):
        lid = self.link(self.c1, self.pro, 'instructor'); self.accept(self.pro, lid)
        self.switch(self.pro, self.cid1)
        r = self.pro.get('/api/provider/payments')
        self.assertEqual(r.status, 404, 'payments «do not exist» for an instructor')
        self.assertEqual(self.pro.post('/api/provider-services', {'title': 'X', 'price': 1}).status, 403)
        self.assertEqual(self.pro.get('/api/center/activity').status, 404)
        self.switch(self.pro, 0)
        self.c1.post('/api/center/team/link/role', {'id': lid, 'member_role': 'manager'})
        self.switch(self.pro, self.cid1)
        self.assertEqual(self.pro.get('/api/provider/payments').status, 200, 'a manager sees payments')
        self.end_all(self.pro)

    # 8 / 9 ---------------------------------------------------------------------------------------------
    def test_8_unlink_at_once_and_9_activity_with_names(self):
        lid = self.link(self.c1, self.pro, 'manager'); self.accept(self.pro, lid)
        self.switch(self.pro, self.cid1)
        r = self.pro.post('/api/provider-services', {'title': 'Salida de Ana', 'price': 40, 'booking_mode': 'request'})
        self.assertEqual(r.status, 200, r.json)
        act = [x for x in self.c1.get('/api/center/activity').json['items'] if x.get('actor_name') == self.pro.user['fullname']]
        self.assertTrue(act, 'the action is in the centre\'s log with the person\'s name')
        self.assertEqual(act[0]['actor_role'], 'Encargado')
        # the centre removes her: the open session loses the centre on its next request
        self.assertEqual(self.c1.post('/api/center/team/link/end', {'id': lid}).status, 200)
        me = self.pro.me()
        self.assertEqual(me['user']['role'], 'freelance'); self.assertEqual([p['key'] for p in me['profiles']], ['own'])
        self.assertEqual(self.switch(self.pro, self.cid1).status, 404)
        # and the person leaves by herself
        lid = self.link(self.c1, self.pro, 'manager'); self.accept(self.pro, lid); self.switch(self.pro, self.cid1)
        self.assertEqual(self.pro.post('/api/my/teams/leave', {'id': lid}).status, 200)
        self.assertEqual(self.pro.me()['user']['role'], 'freelance')

    # 10 -----------------------------------------------------------------------------------------------
    def test_10_plans(self):
        c3 = self.make_center(self.admin, 'plan'); cid = c3.user['center_id']
        others = [self.make_diver(f'p{i}') for i in range(3)]
        self.plan(cid, 'free')
        r, _ = self.scan(c3, others[0])
        self.assertEqual(r.status, 403); self.assertEqual(r.json.get('plan_required'), 'team')
        self.assertIn('Motor de reservas', r.json['error'])
        self.plan(cid, 'booking')
        r, _ = self.scan(c3, others[0])
        self.assertEqual(c3.post('/api/center/team/link', {'ref': r.json['ref'], 'member_role': 'instructor'}).json.get('plan_required'), 'team_profiles')
        r, _ = self.scan(c3, others[0])
        lid = c3.post('/api/center/team/link', {'ref': r.json['ref'], 'member_role': 'reception'}).json['id']
        self.accept(others[0], lid)
        r, _ = self.scan(c3, others[1])
        x = c3.post('/api/center/team/link', {'ref': r.json['ref'], 'member_role': 'reception'})
        self.assertEqual((x.status, x.json.get('plan_required')), (403, 'team'), 'one person with Motor de reservas')
        # Pro: up to 15, the 16th is refused (pending requests count)
        self.plan(cid, 'pro')
        for i in range(14):
            self.server.sql("INSERT INTO team_links(center_id,user_id,member_role,kind,status,requested_at) VALUES(?,?,?,?,?,?)",
                            (cid, self.admin.user['id'] if False else others[1].user['id'] if i == 0 else 10_000 + i, 'instructor', 'fixed', 'pending', '2026-10-16'))
        r, _ = self.scan(c3, others[2])
        x = c3.post('/api/center/team/link', {'ref': r.json['ref'], 'member_role': 'reception'})
        self.assertEqual(x.json.get('plan_required'), 'team', 'the 16th is refused')
        self.server.sql("DELETE FROM team_links WHERE center_id=? AND status='pending'", (cid,))
        # down to Motor de reservas: whoever does not fit is paused, not deleted; back to Pro, reactivated
        r, _ = self.scan(c3, others[1])
        l2 = c3.post('/api/center/team/link', {'ref': r.json['ref'], 'member_role': 'instructor'}).json['id']
        others[1].post('/api/my/activate-freelance', {'accept_terms': True})
        self.accept(others[1], l2)
        self.plan(cid, 'booking')
        team = c3.get('/api/center/team').json
        st = {x['id']: x['status'] for x in team['links']}
        self.assertEqual((st[lid], st[l2]), ('active', 'paused'))
        self.assertEqual(self.switch(others[1], cid).status, 404, 'paused: no access')
        self.plan(cid, 'pro')
        self.assertEqual(c3.post('/api/center/team/link/reactivate', {'id': l2}).status, 200)
        self.assertEqual(self.switch(others[1], cid).status, 200)

    # 11 -----------------------------------------------------------------------------------------------
    def test_11_free_freelance_and_diver(self):
        free = self.make_freelance(self.admin, 'gratis')
        self.server.sql("UPDATE users SET plan_code='free', plan_status='free', plan_expires_at=NULL WHERE id=?", (free.user['id'],))
        r = free.post('/api/provider-services', {'title': 'Mío', 'price': 10})
        self.assertEqual((r.status, r.json.get('plan_required')), (403, 'online_bookings'))
        lid = self.link(self.c2, free, 'instructor'); self.accept(free, lid)
        self.assertEqual(self.switch(free, self.cid2).status, 200)
        self.switch(free, 0)
        # not shown to the public until the owner decides (6.2.5)
        self.assertNotIn(free.user['id'], [x.get('id') for x in self.client().get('/api/professionals').json.get('items', [])] if self.client().get('/api/professionals').status == 200 else [])
        # a diver: as Instructor, only after activating the (free) freelance profile
        r, _ = self.scan(self.c2, self.diver)
        self.assertEqual(r.json['person']['account'], 'diver')
        x = self.c2.post('/api/center/team/link', {'ref': r.json['ref'], 'member_role': 'instructor'})
        self.assertTrue(x.json['needs_freelance']); self.assertIn('activar su perfil de freelance', x.json['message'])
        bad = self.diver.post('/api/my/teams/respond', {'id': x.json['id'], 'accept': True})
        self.assertEqual(bad.status, 403); self.assertIn('freelance', bad.json['error'])
        ok = self.diver.post('/api/my/teams/respond', {'id': x.json['id'], 'accept': True, 'activate_freelance': True, 'accept_terms': True})
        self.assertEqual(ok.status, 200, ok.json)
        self.assertEqual(self.diver.me()['user']['role'], 'freelance')
        # Recepción can be a normal account
        d2 = self.make_diver('recep')
        r, _ = self.scan(self.c2, d2)
        x = self.c2.post('/api/center/team/link', {'ref': r.json['ref'], 'member_role': 'reception'})
        self.assertFalse(x.json['needs_freelance'])
        self.accept(d2, x.json['id'])
        self.assertEqual(self.switch(d2, self.cid2).status, 200)
        self.assertEqual(d2.me()['own_role'], 'recreational')

    # 12 -----------------------------------------------------------------------------------------------
    def test_12_share_link(self):
        s = self.pro.post('/api/my/qr/share').json
        self.assertEqual(s['expires_in'], 86400)
        r = self.c2.post('/api/center/team/scan', {'code': s['url']})
        self.assertEqual(r.status, 200, r.json); self.assertEqual(r.json['source'], 'share')
        self.assertEqual(self.c2.post('/api/center/team/scan', {'code': s['url']}).status, 400, 'one use')
        s2 = self.pro.post('/api/my/qr/share').json
        self.server.sql('UPDATE team_share_links SET expires_at=? WHERE id=?', (int(time.time()) - 1, s2['id']))
        self.assertIn('caducado', self.c2.post('/api/center/team/scan', {'code': s2['url']}).json['error'])
        s3 = self.pro.post('/api/my/qr/share').json
        self.assertEqual(self.pro.post('/api/my/qr/share/revoke', {'id': s3['id']}).status, 200)
        self.assertIn('anulado', self.c2.post('/api/center/team/scan', {'code': s3['url']}).json['error'])
        states = {x['id']: x['state'] for x in self.pro.get('/api/my/qr/shares').json['items']}
        self.assertEqual((states[s['id']], states[s2['id']], states[s3['id']]), ('used', 'expired', 'revoked'))

    def test_13_transfer_ownership_by_email(self):
        c4 = self.make_center(self.admin, 'propiedad'); cid = c4.user['center_id']; self.plan(cid, 'pro')
        nuevo = self.make_freelance(self.admin, 'nuevo')
        lid = self.link(c4, nuevo, 'manager'); self.accept(nuevo, lid)
        r = c4.post('/api/center/team/transfer', {'user_id': nuevo.user['id']})
        self.assertEqual(r.status, 200, r.json)
        tok = re.search(r'propiedad\?token=([A-Za-z0-9_\-]+)', outbox(self.server, 'team_transfer')[0]['text']).group(1)
        self.assertEqual(nuevo.post('/api/team/transfer/confirm', {'token': tok}).status, 403, 'only the owner confirms')
        self.assertEqual(c4.post('/api/team/transfer/confirm', {'token': tok}).status, 200)
        self.switch(nuevo, cid)
        self.assertEqual(nuevo.me()['member_role'], 'owner')
        self.assertEqual(c4.post('/api/center/team/link/end', {'id': lid}).status, 403, 'the old owner is now Encargado: the team is the owner\'s')
        self.assertEqual(nuevo.post('/api/my/teams/leave', {'id': lid}).status, 400, 'the owner cannot leave')

if __name__ == '__main__':
    unittest.main()
