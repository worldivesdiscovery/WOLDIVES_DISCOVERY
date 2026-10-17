"""v50.47 · parte G.1 y G.5: matriz de aislamiento entre centros.

Una sesión del centro A (propietario, recepción y encargado), de un freelance FA y de un antiguo empleado de B usa los
identificadores de B y del freelance FB en todas las rutas privadas: siempre 404 (nunca 403, que revelaría que existe)
y nada de B cambia (se compara una foto de todas sus filas antes y después). Control positivo: B sí puede usar sus
propios ids. Además: los campos de centro o de destinatarios que manda el navegador se ignoran y quedan registrados;
la base rechaza por sí misma una reserva que apunte a una salida de otro centro; las rutas públicas siguen mostrando
lo público y nunca los datos privados del centro."""
import datetime as dt
import hashlib
import json
import sqlite3
import unittest

from helpers import ServerTestCase, Client, IN_PERSON

DAY = lambda n: (dt.date.today() + dt.timedelta(days=n)).isoformat()


class Isolation(ServerTestCase):
    extra_env = {'WOD_AVISOS_DESHACER_SEGUNDOS': '120'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.A = t.make_center(cls.admin, 'aislaa', phone='+34 600 470 001')
        cls.B = t.make_center(cls.admin, 'aislab', phone='+34 600 470 002')
        cls.FA = t.make_freelance(cls.admin, 'aislfa')
        cls.FB = t.make_freelance(cls.admin, 'aislfb')
        cls.cidA, cls.cidB = cls.A.user['center_id'], cls.B.user['center_id']
        cls.diver = t.make_diver('aislad')
        cls.diver.post('/api/account/profile', {'phone': '+34 611 470 470', 'wa_consent': True})
        # --- B's private data -----------------------------------------------------------------------------
        B = cls.B
        cls.sB = B.post('/api/provider-services', {'title': 'Salida B', 'price': 30, 'booking_mode': 'request'}).json['id']
        cls.slB = B.post('/api/provider-services/slot', {'service_id': cls.sB, 'slot_date': DAY(9), 'slot_time': '09:00', 'spots_total': 8}).json['slot_id']
        cls.slB2 = B.post('/api/provider-services/slot', {'service_id': cls.sB, 'slot_date': DAY(10), 'slot_time': '09:00', 'spots_total': 8}).json['slot_id']
        r = cls.diver.post('/api/bookings', {'center_id': cls.cidB, 'service_id': cls.sB, 'slot_id': cls.slB, 'participants': 1})
        assert r.status == 200, r
        cls.bB = r.json['id']
        assert B.post(f'/api/bookings/{cls.bB}/status', {'status': 'confirmed'}).status == 200
        cls.boatB = B.post('/api/manifest/boats/save', {'name': 'Barco B', 'capacity': 10}).json['id']
        cls.manB = B.get(f'/api/manifest/{cls.slB}').json
        cls.gB = B.post(f'/api/manifest/{cls.slB}/groups/save', {}).json['id']
        cls.pB = B.post('/api/center/promotions', {'title': 'Promo B', 'value_text': '10 %', 'valid_until': DAY(60)}).json.get('id')
        cls.nbB = B.post('/api/avisos/cancelar', {'slot_id': cls.slB2, 'reason': 'weather', 'confirm': DAY(10)[8:10] + '/' + DAY(10)[5:7]}).json['uid']
        ir = Client(cls.server).post('/api/info-requests', {'center_id': cls.cidB, 'name': 'Cliente B', 'email': 'clienteb@diver.example.org', 'message': 'Quiero información', 'accept_privacy': True})
        cls.irB = (cls.server.sql('SELECT id FROM info_requests WHERE center_id=?', (cls.cidB,)) or [{'id': 0}])[0]['id']
        # --- FB's private data ----------------------------------------------------------------------------
        cls.sFB = cls.FB.post('/api/provider-services', {'title': 'Salida FB', 'price': 25, 'booking_mode': 'request', **IN_PERSON}).json['id']
        cls.slFB = cls.FB.post('/api/provider-services/slot', {'service_id': cls.sFB, 'slot_date': DAY(11), 'slot_time': '10:00', 'spots_total': 4}).json['slot_id']
        r = cls.diver.post('/api/bookings', {'service_id': cls.sFB, 'slot_id': cls.slFB, 'participants': 1, 'provider_user_id': cls.FB.user['id']})
        cls.bFB = r.json['id'] if r.status == 200 else None
        # --- A's own data (to have something to send) and team ---------------------------------------------
        cls.sA = cls.A.post('/api/provider-services', {'title': 'Salida A', 'price': 30, 'booking_mode': 'request'}).json['id']
        cls.slA = cls.A.post('/api/provider-services/slot', {'service_id': cls.sA, 'slot_date': DAY(9), 'slot_time': '09:00', 'spots_total': 8}).json['slot_id']
        cls.recA = cls.team_member(t, cls.A, 'aislarec', 'reception')
        cls.manA = cls.team_member(t, cls.A, 'aislaman', 'manager')

    @classmethod
    def team_member(cls, t, owner, tag, role):
        email = f'{tag}@diver.example.org'
        assert owner.post('/api/center/team/invite', {'email': email, 'member_role': role}).status in (200, 403), 'invite'
        inv = cls.server.sql('SELECT id FROM team_invites WHERE email=? ORDER BY id DESC', (email,))
        if not inv:    # plan without the team feature: the member is attached directly (test data)
            c = t.make_diver(tag); uid = c.user['id']
            cls.server.sql("UPDATE users SET role='center',center_id=? WHERE id=?", (owner.user['center_id'], uid))
            cls.server.sql("INSERT INTO center_members(center_id,user_id,member_role,created_at) VALUES(?,?,?,?)", (owner.user['center_id'], uid, role, '2026-01-01'))
            assert c.login(f'diver_{tag}').status == 200
            c.user = c.me()['user']; return c
        c = t.make_diver(tag); uid = c.user['id']
        cls.server.sql("UPDATE users SET role='center',center_id=? WHERE id=?", (owner.user['center_id'], uid))
        cls.server.sql("INSERT OR REPLACE INTO center_members(center_id,user_id,member_role,created_at) VALUES(?,?,?,?)", (owner.user['center_id'], uid, role, '2026-01-01'))
        assert c.login(f'diver_{tag}').status == 200
        c.user = c.me()['user']; return c

    # -------------------------------------------------------------------------------------------------- helpers
    def snapshot(self):
        """Every row that belongs to B or to FB (and the rows that hang from them)."""
        keys = (f"c:{self.cidB}", f"f:{self.FB.user['id']}")
        db = sqlite3.connect(self.server.db); db.row_factory = sqlite3.Row
        out = []
        try:
            for t in ('provider_services', 'service_slots', 'bookings', 'boats', 'waiver_templates', 'travel_experiences', 'info_requests', 'resources',
                      'payment_orders', 'center_tariffs', 'center_extras', 'promotions', 'qr_codes', 'team_invites', 'center_members', 'notice_batches',
                      'notice_outbox', 'provider_settings', 'whatsapp_accounts'):
                cols = [r[1] for r in db.execute(f'PRAGMA table_xinfo({t})')]
                if 'provider_id' not in cols: continue
                rows = db.execute(f"SELECT * FROM {t} WHERE provider_id IN (?,?) ORDER BY rowid", keys).fetchall()
                out.append((t, [tuple(r) for r in rows]))
            for t, q in (('manifest_entries', 'slot_id IN (SELECT id FROM service_slots WHERE provider_id IN (?,?))'),
                         ('slot_groups', 'slot_id IN (SELECT id FROM service_slots WHERE provider_id IN (?,?))'),
                         ('slot_cancel_offers', 'slot_id IN (SELECT id FROM service_slots WHERE provider_id IN (?,?))'),
                         ('messages', 'booking_id IN (SELECT id FROM bookings WHERE provider_id IN (?,?))'),
                         ('centers', 'id IN (SELECT center_id FROM providers WHERE id IN (?,?))')):
                out.append((t, [tuple(r) for r in db.execute(f'SELECT * FROM {t} WHERE {q} ORDER BY rowid', keys).fetchall()]))
            out.append(('email_outbox_diver', db.execute("SELECT COUNT(*) FROM email_outbox WHERE to_email='aislad@diver.example.org'").fetchone()[0]))
        finally:
            db.close()
        return hashlib.sha256(json.dumps(out, default=str).encode()).hexdigest()

    def calls(self):
        """(method, path, body) with the ids of B and FB."""
        bB, slB, sB = self.bB, self.slB, self.sB
        c = [('GET', f'/api/bookings/{bB}', None), ('GET', f'/api/bookings/{bB}/receipt.pdf', None), ('GET', f'/api/bookings/{bB}/qr.svg', None),
             ('GET', f'/api/bookings/{bB}/waiver', None), ('GET', f'/api/bookings/{bB}/diver-sheet.pdf', None), ('GET', f'/api/bookings/{bB}/change-date', None),
             ('GET', f'/api/manifest/{slB}', None), ('GET', f'/api/avisos/{self.nbB}', None), ('GET', f'/api/avisos?slot={slB}', None),
             ('GET', f'/api/center/poster-qr?service={sB}', None),
             ('POST', f'/api/bookings/{bB}/status', {'status': 'cancelled'}), ('POST', f'/api/bookings/{bB}/payment', {'payment_status': 'paid'}),
             ('POST', f'/api/bookings/{bB}/reschedule', {'slot_id': self.slB2}), ('POST', f'/api/bookings/{bB}/change-date/decide', {'approve': True}),
             ('POST', '/api/provider-services/update', {'id': sB, 'title': 'Robado', 'price': 1}), ('POST', '/api/provider-services/delete', {'id': sB}),
             ('POST', '/api/provider-services/options', {'id': sB, 'reschedule_mode': 'direct'}),
             ('POST', '/api/provider-services/slot', {'service_id': sB, 'slot_date': DAY(20), 'slot_time': '10:00'}),
             ('POST', '/api/provider-services/slot-update', {'slot_id': slB, 'slot_time': '11:00'}), ('POST', '/api/provider-services/slot-delete', {'slot_id': slB}),
             ('POST', '/api/provider-services/slot-close', {'slot_id': slB}), ('POST', '/api/provider-services/slot-cancel', {'slot_id': slB, 'reason': 'weather'}),
             ('POST', f'/api/manifest/{slB}/settings', {'max_per_guide': 2}), ('POST', f'/api/manifest/{slB}/suggest', {'apply': True}),
             ('POST', f'/api/manifest/{slB}/groups/save', {'id': self.gB, 'label': 'Robado'}), ('POST', f'/api/manifest/{slB}/groups/delete', {'id': self.gB}),
             ('POST', f'/api/manifest/{slB}/assign', {'moves': [{'booking_id': bB, 'seat': 1, 'group_id': self.gB}]}),
             ('POST', f'/api/manifest/{slB}/entry', {'booking_id': bB, 'seat': 1, 'note': 'x'}),
             ('POST', '/api/manifest/sync', {'changes': [{'slot_id': slB, 'booking_id': bB, 'seat': 1, 'field': 'status', 'base': '', 'value': 'present', 'at': '2026-01-01T00:00:00'}]}),
             ('POST', '/api/manifest/boats/save', {'id': self.boatB, 'name': 'Robado', 'capacity': 3}),
             ('POST', '/api/messages', {'booking_id': bB, 'subject': 'x', 'body': 'Mensaje de otro centro'}),
             ('POST', '/api/center/tariffs/save', {'service_id': sB, 'price': 1, 'effective_from': DAY(1)}),
             ('POST', '/api/center/info-requests/read', {'id': self.irB, 'status': 'done'}),
             ('POST', '/api/avisos/preview', {'slot_id': slB, 'kind': 'slot_cancelled'}),
             ('POST', '/api/avisos/cancelar', {'slot_id': slB, 'reason': 'weather', 'confirm': DAY(9)[8:10] + '/' + DAY(9)[5:7]}),
             ('POST', '/api/avisos/cambio', {'slot_id': slB, 'new_time': '11:00', 'confirm': DAY(9)[8:10] + '/' + DAY(9)[5:7]}),
             ('POST', f'/api/avisos/{self.nbB}/deshacer', {})]
        if self.pB:
            c += [('GET', f'/api/center/promotions/{self.pB}/codes', None), ('POST', f'/api/center/promotions/{self.pB}/status', {'status': 'archived'})]
        if self.bFB:
            c += [('GET', f'/api/bookings/{self.bFB}', None), ('POST', f'/api/bookings/{self.bFB}/status', {'status': 'confirmed'}),
                  ('POST', '/api/provider-services/update', {'id': self.sFB, 'title': 'Robado FB', 'price': 1}),
                  ('GET', f'/api/manifest/{self.slFB}', None), ('POST', '/api/avisos/preview', {'slot_id': self.slFB})]
        return c

    def run_matrix(self, who, label, allowed=(404,), center_only_403=False):
        before = self.snapshot()
        bad = []
        for method, path, body in self.calls():
            r = who.get(path) if method == 'GET' else who.post(path, body)
            ok = allowed + ((403,) if center_only_403 and path.startswith('/api/center/') else ())   # a freelance is not a centre: refused by role, whatever the id
            if r.status not in ok: bad.append(f'{label} {method} {path} → {r.status} {r.body[:120]!r}')
        self.assertEqual(bad, [], '\n'.join(bad))
        self.assertEqual(self.snapshot(), before, f'{label}: los datos de B han cambiado')

    # -------------------------------------------------------------------------------------------------- tests
    def test_1_owner_of_a_gets_404_for_everything_of_b(self):
        self.run_matrix(self.A, 'centro A')

    def test_2_freelance_gets_404(self):
        self.run_matrix(self.FA, 'freelance FA', center_only_403=True)

    def test_3_staff_of_a_gets_404_or_role_refusal(self):
        # Reception cannot cancel or notify at all (403 by role, before looking at the id); everything else is 404.
        self.run_matrix(self.recA, 'recepción de A', allowed=(403, 404))
        self.run_matrix(self.manA, 'encargado de A', allowed=(403, 404))

    def test_4_former_employee_of_b_keeps_nothing(self):
        """H1 of the audit: the person who created B's service, removed from B, has no access to anything of B."""
        t = self
        ex = t.make_diver('aislaex'); uid = ex.user['id']
        self.server.sql("UPDATE users SET role='center',center_id=? WHERE id=?", (self.cidB, uid))
        self.server.sql("INSERT OR REPLACE INTO center_members(center_id,user_id,member_role,created_at) VALUES(?,?,?,?)", (self.cidB, uid, 'reception', '2026-01-01'))
        self.assertEqual(ex.login('diver_aislaex').status, 200)
        sid = ex.post('/api/provider-services', {'title': 'Creado por el empleado', 'price': 10, 'booking_mode': 'request'}).json['id']
        self.assertEqual(self.B.post('/api/center/team/remove', {'user_id': uid}).status, 200)
        self.assertEqual(ex.login('diver_aislaex').status, 200)
        self.assertEqual(ex.post('/api/provider-services/update', {'id': sid, 'title': 'Robado', 'price': 1}).status, 403)   # a diver is not a provider
        self.assertEqual(ex.get(f'/api/manifest/{self.slB}').status, 404)
        self.assertEqual(ex.post('/api/provider-services/slot-cancel', {'slot_id': self.slB, 'reason': 'weather'}).status, 404)
        # …and after joining centre A
        self.server.sql("UPDATE users SET role='center',center_id=? WHERE id=?", (self.cidA, uid))
        self.assertEqual(ex.login('diver_aislaex').status, 200)
        before = self.snapshot()
        for path, body in (('/api/provider-services/update', {'id': sid, 'title': 'Robado', 'price': 1}), ('/api/provider-services/slot', {'service_id': sid, 'slot_date': DAY(30), 'slot_time': '09:00'}),
                           ('/api/provider-services/options', {'id': sid, 'reschedule_mode': 'direct'})):
            self.assertEqual(ex.post(path, body).status, 404, path)
        self.assertEqual(ex.get(f'/api/manifest/{self.slB}').status, 404)
        self.assertEqual(self.snapshot(), before)

    def test_5_positive_control_b_uses_its_own_ids(self):
        B = self.B
        self.assertEqual(B.get(f'/api/bookings/{self.bB}').status, 200)
        self.assertEqual(B.get(f'/api/manifest/{self.slB}').status, 200)
        self.assertEqual(B.get(f'/api/avisos/{self.nbB}').status, 200)
        self.assertEqual(B.post('/api/avisos/preview', {'slot_id': self.slB}).status, 200)
        self.assertEqual(B.post('/api/provider-services/options', {'id': self.sB, 'reschedule_mode': 'approval'}).status, 200)

    def test_6_tenant_fields_from_the_browser_are_ignored_and_logged(self):
        """G.5: provider_id, center_id or a list of phones/recipients sent by the browser are removed and logged."""
        n0 = len(self.server.sql("SELECT 1 FROM audit_log WHERE action='tenant_fields_ignored'"))
        r = self.A.post('/api/avisos/preview', {'slot_id': self.slA, 'center_id': self.cidB, 'provider_id': f'c:{self.cidB}',
                                                'phones': ['+34600000000'], 'recipients': [self.bB]})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['slot']['id'], self.slA)                    # still A's own departure
        self.assertEqual(r.json['recipients'], 0)                           # nobody from the list sent
        logged = self.server.sql("SELECT details FROM audit_log WHERE action='tenant_fields_ignored' ORDER BY id DESC LIMIT 1")
        self.assertGreater(len(self.server.sql("SELECT 1 FROM audit_log WHERE action='tenant_fields_ignored'")), n0)
        self.assertIn('phones', logged[0]['details']); self.assertNotIn('+34600000000', logged[0]['details'])   # the values are never stored
        r = self.A.post('/api/center/promotions', {'title': 'Promo con centro ajeno', 'value_text': '5 %', 'valid_until': DAY(30), 'center_id': self.cidB})
        if r.status == 200:
            self.assertEqual(self.server.sql('SELECT center_id FROM promotions WHERE id=?', (r.json['id'],))[0]['center_id'], self.cidA)

    def test_7_database_refuses_mixing_tenants(self):
        """B.5: even a buggy query cannot make a booking of A point to a departure of B."""
        from helpers import cifrado_for
        db = sqlite3.connect(self.server.db)
        cif = cifrado_for(self.server.env); db.create_function('wod_huella', 1, cif.sql_fingerprint); db.create_function('wod_cifrar', 1, cif.sql_encrypt)
        try:
            db.execute('PRAGMA foreign_keys=ON')
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('UPDATE bookings SET slot_id=? WHERE id=?', (self.slA, self.bB))
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute("INSERT INTO bookings(user_id,booking_date,participants,status,created_at,updated_at) VALUES(?, '2030-01-01', 1, 'requested', 'x', 'x')", (self.diver.user['id'],))
            with self.assertRaises(sqlite3.IntegrityError):
                db.execute('UPDATE service_slots SET service_id=? WHERE id=?', (self.sA, self.slB))
            nb = db.execute("SELECT id FROM notice_batches LIMIT 1").fetchone()
            if nb:
                with self.assertRaises(sqlite3.IntegrityError):
                    db.execute("INSERT INTO notice_outbox(uid,batch_id,provider_id,slot_id,booking_id,event,channel,template,lang,created_at,updated_at) VALUES('x',?,?,?,?,'e','app','t','es','x','x')",
                               (nb[0], f'c:{self.cidA}', self.slB, self.bB))
            self.assertEqual(db.execute("SELECT COUNT(*) FROM bookings WHERE provider_id IS NULL").fetchone()[0], 0)
            self.assertEqual(db.execute('PRAGMA foreign_key_check(bookings)').fetchall(), [])
        finally:
            db.rollback(); db.close()

    def test_8_public_stays_public_and_private_never_leaves(self):
        """«Lo público sigue siendo público»: the directory, a centre's page and its departures are visible to everyone,
        without the private columns of the centre (tax id, iCal token, insurance, plan…)."""
        anon = Client(self.server)
        page = anon.get(f'/api/centers/{self.cidB}')
        self.assertEqual(page.status, 200)
        for k in ('tax_id', 'ical_token', 'birth_date', 'insurance_policy', 'plan_code', 'stripe_account_id', 'fiscal_address'):
            self.assertNotIn(k, page.json['item'] if 'item' in page.json else page.json)
        listing = anon.get('/api/centers').json['items']
        self.assertTrue(listing)
        self.assertFalse(any(k in c for c in listing for k in ('tax_id', 'ical_token', 'insurance_policy')))
        svc = anon.get(f'/api/provider-services?center_id={self.cidB}').json['items']
        self.assertTrue(any(s['id'] == self.sB for s in svc))
        self.assertEqual(anon.get(f'/api/bookings/{self.bB}').status, 403)

    def test_9_admin_needs_a_reason(self):
        a = Client(self.server); a.admin_reason = None
        self.assertEqual(a.login('admin', 'admin-seguro-2026').status, 200)
        r = a.get(f'/api/bookings/{self.bB}')
        # v50.57 (revisión general, 4.1): seeing the data of a booking asks for the password and a reason (15 minutes)
        self.assertEqual(r.status, 403); self.assertTrue(r.json.get('admin_confirm_required'))
        # changing a centre's data still asks for a reason
        r = a.post(f'/api/bookings/{self.bB}/status', {'status': 'confirmed'})
        self.assertEqual(r.status, 403); self.assertTrue(r.json.get('admin_reason_required'))
        self.assertEqual(a.post('/api/admin/confirm', {'password': 'admin-seguro-2026', 'reason': 'Reclamación del cliente 123'}).status, 200)
        self.assertEqual(a.get(f'/api/bookings/{self.bB}').status, 200)
        logged = self.server.sql("SELECT details FROM audit_log WHERE action='admin_center_access' ORDER BY id DESC LIMIT 1")[0]['details']
        self.assertIn('Reclamación del cliente 123', logged)
        # The administrator never sends notices on behalf of a centre.
        self.assertEqual(a.post('/api/avisos/cancelar', {'slot_id': self.slB, 'reason': 'weather', 'confirm': 'x'}).status, 403)

    def test_10_staff_of_several_centres_switch_explicitly(self):
        t = self
        m = t.make_diver('aislamulti'); uid = m.user['id']
        self.server.sql("UPDATE users SET role='center',center_id=? WHERE id=?", (self.cidA, uid))
        self.server.sql("INSERT OR REPLACE INTO center_members(center_id,user_id,member_role,created_at) VALUES(?,?,?,?)", (self.cidA, uid, 'manager', '2026-01-01'))
        self.server.sql("INSERT OR REPLACE INTO center_members(center_id,user_id,member_role,created_at) VALUES(?,?,?,?)", (self.cidB, uid, 'reception', '2026-01-01'))
        self.assertEqual(m.login('diver_aislamulti').status, 200)
        self.assertEqual(m.get(f'/api/bookings/{self.bB}').status, 404)          # working in A: B does not exist
        cs = m.get('/api/team/centers').json['items']
        self.assertEqual(sorted(c['id'] for c in cs), sorted([self.cidA, self.cidB]))
        self.assertEqual(m.post('/api/team/switch', {'center': self.cidB}).status, 200)
        self.assertEqual(m.get(f'/api/bookings/{self.bB}').status, 200)          # now in B, explicitly
        self.assertEqual(m.post('/api/avisos/preview', {'slot_id': self.slB}).status, 403)   # reception in B: no mass notices
        self.assertEqual(m.post('/api/team/switch', {'center': 999999}).status, 404)
        self.assertTrue(self.server.sql("SELECT 1 FROM audit_log WHERE action='team_context_switch' AND user_id=?", (uid,)))


if __name__ == '__main__':
    unittest.main()
