"""Fase 6 (v50.37): fiscal data (DAC7) and insurance, plans with trial / expiry / exceptions / annual fee, free listing
with «Solicitar información», statistics, CSV exports and import, iCal, widget, team roles, activity log, feature
switches and pilot mode. Every test runs on a copy of the seed database (helpers.Server)."""
import datetime as dt
import re
import json
import time
import unittest

from helpers import ServerTestCase, Client
from stripe_mock import StripeMock

WEBHOOK_SECRET = 'whsec_plan_local'
from helpers import PNG_BYTES as PNG  # noqa: E402  (a real image: uploads are opened and checked, ASVS 5.0 V5.2.2)
TODAY = dt.date.today()


def outbox(server, template, to=None):
    q = 'SELECT * FROM email_outbox WHERE template=?' + (' AND to_email=?' if to else '') + ' ORDER BY id DESC'
    return server.sql(q, (template, to) if to else (template,))


class Plans(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base, 'STRIPE_WEBHOOK_SECRET': WEBHOOK_SECRET, 'WOD_MAINTENANCE_SECONDS': '2'}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'plan6', phone='+34 600 600 001')
        cls.diver = t.make_diver('plan6')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def cid(self, c=None):
        return (c or self.center).user['center_id']

    def service(self, center, title=None):
        r = center.post('/api/provider-services', {'title': title or f'Inmersión {time.time_ns()}', 'price': 50, 'booking_mode': 'request'})
        self.assertEqual(r.status, 200, r)
        sid = r.json['id']
        r = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-06-10', 'slot_time': '10:00', 'spots_total': 6})
        self.assertEqual(r.status, 200, r)
        return sid, r.json['slot_id']

    def wait_for(self, fn, timeout=12):
        end = time.time() + timeout
        while time.time() < end:
            if fn(): return True
            time.sleep(0.5)
        return False

    def test_public_plans_and_trial_on_approval(self):
        d = self.client().get('/api/plans').json
        self.assertEqual([p['code'] for p in d['items']], ['free', 'booking', 'pro'])
        self.assertEqual(d['trial_days'], 60)
        plan = self.center.me()['plan']
        self.assertEqual(plan['code'], 'pro'); self.assertEqual(plan['status'], 'trial')
        self.assertEqual(plan['expires_at'], (TODAY + dt.timedelta(days=60)).isoformat())
        self.assertTrue(plan['features']['online_bookings'])

    def test_expired_plan_becomes_free_listing(self):
        c = self.make_center(self.admin, 'caduca6', phone='+34 600 600 002')
        sid, slot = self.service(c)
        r = self.diver.post('/api/bookings', {'center_id': self.cid(c), 'service_id': sid, 'slot_id': slot, 'participants': 1})
        self.assertEqual(r.status, 200, r); bid = r.json['id']
        self.server.sql("UPDATE centers SET plan_expires_at='2020-01-01' WHERE id=?", (self.cid(c),))
        self.assertEqual(c.me()['plan']['code'], 'free')
        r = self.diver.post('/api/bookings', {'center_id': self.cid(c), 'service_id': sid, 'slot_id': slot, 'participants': 1})
        self.assertEqual(r.status, 403); self.assertTrue(r.json.get('no_online_booking'))
        self.assertNotIn('plazas', r.json['error'])                      # never «sin plazas»
        self.assertEqual(c.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'}).status, 200)   # existing bookings go on
        self.assertEqual(c.get('/api/center/export?kind=bookings').status, 200)                  # export always available
        self.assertFalse(self.client().get(f'/api/centers/{self.cid(c)}').json['item']['online_booking'])
        r = c.post('/api/provider/ical/regenerate', {})
        self.assertEqual(r.status, 403); self.assertEqual(r.json['plan_required'], 'calendar_ical')
        # Information request instead
        anon = self.client()
        bad = {'center_id': self.cid(c), 'name': 'Ana', 'email': 'ana@example.org', 'message': 'Hola', 'accept_privacy': True}
        self.assertEqual(anon.post('/api/info-requests', bad).status, 400)
        self.assertEqual(anon.post('/api/info-requests', {**bad, 'message': 'Quiero hacer un bautizo en julio', 'accept_privacy': False}).status, 400)
        r = anon.post('/api/info-requests', {**bad, 'message': 'Quiero hacer un bautizo en julio', 'wanted_date': '2031-07-01', 'participants': 2})
        self.assertEqual(r.status, 200, r)
        self.assertTrue(outbox(self.server, 'info_request', 'caduca6@centro-caduca6.example.org'))
        self.assertTrue(outbox(self.server, 'info_request_copy', 'ana@example.org'))
        items = c.get('/api/center/info-requests').json
        self.assertEqual(items['unread'], 1)
        self.assertEqual(c.post('/api/center/info-requests/read', {'id': items['items'][0]['id'], 'answered': True}).status, 200)
        self.assertEqual(self.center.post('/api/center/info-requests/read', {'id': items['items'][0]['id']}).status, 404)  # other centre (v50.47: 404)
        w = self.client().get(f'/widget/center/{self.cid(c)}')
        self.assertEqual(w.status, 301)                                   # v50.56: the old address takes to the new widget
        slug = w.headers['Location'].split('/w/')[1].split('?')[0]
        self.assertFalse(self.client().get(f'/api/w/{slug}?canal=widget').json['bookable'])   # «Solicitar información» instead

    def test_renewal_notices_and_expiry_job(self):
        c = self.make_center(self.admin, 'aviso6', phone='+34 600 600 003')
        self.server.sql("UPDATE centers SET plan_expires_at=?, plan_reminders=NULL WHERE id=?", ((TODAY + dt.timedelta(days=6)).isoformat(), self.cid(c)))
        self.server.sql("DELETE FROM site_settings WHERE key='plans_last_run'")
        self.assertTrue(self.wait_for(lambda: outbox(self.server, 'plan_renewal', 'aviso6@centro-aviso6.example.org')))
        self.server.sql("DELETE FROM site_settings WHERE key='plans_last_run'"); time.sleep(3)
        self.assertEqual(len(outbox(self.server, 'plan_renewal', 'aviso6@centro-aviso6.example.org')), 1)   # once per threshold
        self.server.sql("UPDATE centers SET plan_expires_at=? WHERE id=?", ((TODAY - dt.timedelta(days=1)).isoformat(), self.cid(c)))
        self.server.sql("DELETE FROM site_settings WHERE key='plans_last_run'")
        self.assertTrue(self.wait_for(lambda: outbox(self.server, 'plan_expired', 'aviso6@centro-aviso6.example.org')))

    def test_annual_fee_with_stripe_and_webhook(self):
        c = self.make_center(self.admin, 'cuota6', phone='+34 600 600 004')
        self.assertEqual(c.post('/api/provider/plan/checkout', {'plan': 'pro'}).status, 400)   # no price yet
        self.assertEqual(self.diver.post('/api/admin/plans/save', {'code': 'pro', 'name': 'Pro'}).status, 403)
        r = self.admin.post('/api/admin/plans/save', {'code': 'pro', 'name': 'Pro', 'price_year': '390', 'currency': 'eur',
                            'features': {k: True for k in ('online_bookings', 'online_payments', 'calendar_ical', 'widget', 'import_csv', 'team', 'analytics', 'promotions', 'experiences', 'rewards', 'integration')},
                            'limits': {'services_max': 0, 'team_max': 20}})
        self.assertEqual(r.status, 200, r)
        r = c.post('/api/provider/plan/checkout', {'plan': 'pro'})
        self.assertEqual(r.status, 200, r)
        sess = self.stripe.last_session()
        self.assertEqual(sess['amount_total'], 39000); self.assertIsNone(sess['account'])    # platform account, not a connected one
        pp = self.server.sql('SELECT * FROM plan_payments WHERE stripe_session_id=?', (sess['id'],))[0]
        self.stripe.pay(sess['id'])
        event = {'id': 'evt_plan_1', 'type': 'checkout.session.completed', 'data': {'object': {**sess, 'payment_status': 'paid'}}}
        payload, sig = StripeMock.signed(event, WEBHOOK_SECRET)
        r = Client(self.server, origin=None).request('POST', '/api/payments/webhook', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.server.sql('SELECT status FROM plan_payments WHERE id=?', (pp['id'],))[0]['status'], 'paid')
        plan = c.me()['plan']
        self.assertEqual(plan['status'], 'active')
        self.assertGreaterEqual(plan['expires_at'], (TODAY + dt.timedelta(days=60 + 360)).isoformat())   # added to the trial
        self.assertTrue(outbox(self.server, 'plan_paid', 'cuota6@centro-cuota6.example.org'))
        r = Client(self.server, origin=None).request('POST', '/api/payments/webhook', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
        self.assertEqual(len(outbox(self.server, 'plan_paid', 'cuota6@centro-cuota6.example.org')), 1)   # idempotent

    def test_manual_plan_exceptions_and_limits(self):
        c = self.make_center(self.admin, 'excep6', phone='+34 600 600 005')
        ref = {'type': 'center', 'id': self.cid(c)}
        self.assertEqual(self.admin.post('/api/admin/plans/assign', {**ref, 'plan': 'free', 'note': ''}).status, 400)
        self.assertEqual(self.admin.post('/api/admin/plans/assign', {**ref, 'plan': 'free', 'note': 'baja voluntaria'}).status, 200)
        r = c.post('/api/center/team/invite', {'email': 'nuevo@example.org', 'member_role': 'reception'})
        self.assertEqual(r.status, 403); self.assertEqual(r.json['plan_required'], 'team')
        self.assertEqual(self.admin.post('/api/admin/plans/exception', {**ref, 'feature': 'team', 'enabled': True, 'reason': 'no'}).status, 400)
        r = self.admin.post('/api/admin/plans/exception', {**ref, 'feature': 'team', 'enabled': True, 'reason': 'Centro piloto con dos recepcionistas'})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(c.post('/api/center/team/invite', {'email': 'nuevo@example.org', 'member_role': 'reception'}).status, 200)
        self.assertTrue(self.server.sql("SELECT 1 FROM audit_log WHERE action='plan_exception_added'"))
        self.assertEqual(self.admin.post('/api/admin/plans/exception/remove', {'id': r.json['id']}).status, 200)
        # Paid manually for 12 months
        r = self.admin.post('/api/admin/plans/assign', {**ref, 'plan': 'booking', 'months': 12, 'amount': '190', 'note': 'transferencia 12/10'})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(c.me()['plan']['code'], 'booking')
        # services limit of the plan
        self.admin.post('/api/admin/plans/save', {'code': 'booking', 'name': 'Motor de reservas', 'features': {'online_bookings': True, 'online_payments': True}, 'limits': {'services_max': 1, 'team_max': 3}})
        self.service(c)
        r = c.post('/api/provider-services', {'title': 'Segundo servicio', 'price': 10})
        self.assertEqual(r.status, 403); self.assertEqual(r.json['plan_required'], 'services_max')
        self.admin.post('/api/admin/plans/save', {'code': 'booking', 'name': 'Motor de reservas', 'features': {k: True for k in ('online_bookings', 'online_payments', 'calendar_ical', 'widget', 'import_csv', 'analytics', 'integration')}, 'limits': {'services_max': 40, 'team_max': 3}})
        for bad in ({'code': 'Mal Código', 'name': 'x'}, {'code': 'free', 'name': 'Gratis', 'features': {'online_bookings': True}}, {'code': 'pro', 'name': 'Pro', 'price_year': '-5'}):
            self.assertEqual(self.admin.post('/api/admin/plans/save', bad).status, 400, bad)
        self.assertEqual(self.admin.post('/api/admin/plans/settings', {'trial_days': 400, 'trial_plan': 'pro'}).status, 400)


class CentreTools(ServerTestCase):
    extra_env = {'WOD_MAINTENANCE_SECONDS': '2'}

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'tools6', phone='+34 600 600 010')
        cls.other = t.make_center(cls.admin, 'otro6', phone='+34 600 600 011')
        cls.diver = t.make_diver('tools6')

    def cid(self):
        return self.center.user['center_id']

    def test_fiscal_data_and_insurance(self):
        f = self.center.get('/api/provider/fiscal').json
        self.assertIn('tax_id', f['missing'])
        for bad in ({'tax_id_country': 'ESP'}, {'birth_date': (TODAY - dt.timedelta(days=365 * 10)).isoformat()}, {'tax_id': '<script>'}, {'insurance_expires_at': '31/12/2027'}):
            self.assertEqual(self.center.post('/api/provider/fiscal', bad).status, 400, bad)
        r = self.center.post('/api/provider/fiscal', {'entity_type': 'company', 'legal_name': 'Buceo Tools SL', 'tax_id': 'B12345678', 'tax_id_country': 'es',
                             'registration_number': 'RM Alicante T1 F2', 'fiscal_address': 'Calle Mar 1, Xàbia', 'declares_licences': True, 'declares_qualified_staff': True,
                             'insurance_company': 'Aseguradora', 'insurance_policy': 'P-1', 'insurance_expires_at': (TODAY + dt.timedelta(days=5)).isoformat()})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['fiscal']['missing'], []); self.assertEqual(r.json['fiscal']['tax_id_country'], 'ES')
        self.assertEqual(self.center.upload('/api/provider/insurance-doc', {}, 'poliza.png', PNG).status, 200)
        self.assertEqual(self.admin.get(f"/api/admin/insurance-doc?type=center&id={self.cid()}").status, 200)
        self.assertEqual(self.diver.get(f"/api/admin/insurance-doc?type=center&id={self.cid()}").status, 403)
        self.server.sql("DELETE FROM site_settings WHERE key='plans_last_run'")
        end = time.time() + 12
        while time.time() < end and not outbox(self.server, 'insurance_expiring', 'tools6@centro-tools6.example.org'): time.sleep(0.5)
        self.assertTrue(outbox(self.server, 'insurance_expiring', 'tools6@centro-tools6.example.org'))

    def test_dac7_report(self):
        cid = self.other.user['center_id']; y = TODAY.year - 1
        for month, amount, refunded in ((2, 100, 0), (5, 80, 20), (11, 50, 0)):
            self.server.sql("""INSERT INTO payment_orders(user_id,amount,currency,status,provider,platform_fee,payee_type,payee_id,refunded_total,created_at,paid_at,updated_at)
                               VALUES(?,?, 'EUR','paid','stripe',0,'center',?,?,?,?,?)""",
                            (self.diver.user['id'], amount, cid, refunded, f'{y}-{month:02d}-10T10:00:00+00:00', f'{y}-{month:02d}-10T10:00:00+00:00', f'{y}-{month:02d}-10T10:00:00+00:00'))
        self.assertEqual(self.center.get(f'/api/admin/dac7?year={y}').status, 403)
        rows = [r for r in self.admin.get(f'/api/admin/dac7?year={y}').json['items'] if r['id'] == cid]
        self.assertEqual(len(rows), 1)
        r = rows[0]
        self.assertEqual((r['importe_t1'], r['importe_t2'], r['importe_t3'], r['importe_t4']), (100, 60, 0, 50))
        self.assertEqual(r['actividades_t1'] + r['actividades_t2'] + r['actividades_t4'], 3)
        self.assertEqual(r['comisiones'], 0); self.assertIn('tax_id', r['datos_incompletos'])
        csv = self.admin.get(f'/api/admin/dac7?year={y}&format=csv')
        self.assertEqual(csv.status, 200); self.assertIn('Importe T1', csv.body.decode('utf-8-sig'))   # v50.57: headers in Spanish
        self.assertEqual(self.admin.get('/api/admin/dac7?year=1990').status, 400)

    def test_statistics_are_aggregated(self):
        cid = self.cid(); anon = self.client()
        # v50.57 (4.2): the screen seen is counted (/api/visita, without robots or the administration), not the API of the ficha
        ua = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/126.0 Safari/537.36'}
        anon.get(f'/api/centers/{cid}', headers=dict(ua))
        for _ in range(2): anon.post('/api/visita', {'p': 'centro', 'id': cid}, headers=dict(ua))   # same visitor and day: one view
        anon.post('/api/stats/track', {'event': 'book_click', 'type': 'center', 'id': cid})
        st = self.center.get('/api/provider/stats').json
        self.assertGreaterEqual(st['totals']['views'], 1); self.assertGreaterEqual(st['totals']['book_clicks'], 1)
        row = self.server.sql("SELECT views FROM provider_stats_daily WHERE provider_type='center' AND provider_id=?", (cid,))[0]
        self.assertEqual(row['views'], 1)
        self.assertIsNone(st['zone'])     # fewer than 3 other centres in the zone: no comparison

    def test_exports_ical_widget(self):
        cid = self.cid()
        sid = self.center.post('/api/provider-services', {'title': 'Bautizo', 'price': 60, 'booking_mode': 'request'}).json['id']
        slot = self.center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-06-12', 'slot_time': '09:30', 'spots_total': 6}).json['slot_id']
        self.assertEqual(self.diver.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': 2}).status, 200)
        for kind in ('clients', 'bookings', 'services', 'payments'):
            r = self.center.get(f'/api/center/export?kind={kind}')
            self.assertEqual(r.status, 200, kind); self.assertTrue(r.body.startswith('﻿'.encode('utf-8')))
        self.assertIn('Bautizo', self.center.get('/api/center/export?kind=bookings').body.decode('utf-8-sig'))
        self.assertEqual(self.center.get('/api/center/export?kind=otra').status, 400)
        self.assertEqual(self.diver.get('/api/center/export?kind=bookings').status, 403)
        url = self.center.post('/api/provider/ical/regenerate', {}).json['url']
        ics = self.client().get('/ical/' + url.rsplit('/ical/', 1)[1])
        self.assertEqual(ics.status, 200); body = ics.body.decode()
        # v50.56: times in UTC (09:30 in Madrid in summer = 07:30 UTC); any calendar shows them in local time
        self.assertIn('BEGIN:VCALENDAR', body); self.assertIn('DTSTART:20310612T073000Z', body); self.assertIn('Bautizo', body)
        self.assertNotIn('tools6@diver', body)      # no emails in the feed
        self.assertEqual(self.client().get('/ical/' + 'x' * 30 + '.ics').status, 404)
        w = self.client().get(f'/widget/center/{cid}')
        self.assertEqual(w.status, 301)                                   # v50.56: the new widget, only on the centre's own domains
        slug = w.headers['Location'].split('/w/')[1].split('?')[0]
        w = self.client().get(f'/w/{slug}')
        self.assertEqual(w.status, 200); self.assertIn("frame-ancestors 'self'", w.headers.get('Content-Security-Policy'))   # no domain authorised yet: only the panel's preview
        self.assertIsNone(re.search(r'<script>(?!</script>)', w.body.decode()))                                              # no inline script
        self.assertIn('Bautizo', json.dumps(self.client().get(f'/api/w/{slug}').json, ensure_ascii=False))
        self.assertEqual(self.client().get('/widget/center/999999').status, 404)
        self.assertEqual(self.client().get('/').headers.get('X-Frame-Options'), 'DENY')     # the rest of the site cannot be framed

    def test_import_clients_with_preview(self):
        self.assertEqual(self.center.get('/api/center/import/template').status, 200)
        csv = 'nombre;email;telefono;titulacion\nAna García;ana@cli.example.org;+34 611 111 111;AOWD\nAna Bis;ANA@cli.example.org;;\nSin Email;;600 222 333;\n;x@y.z;;\nMal;no-es-email;;\n'
        r = self.center.post('/api/center/import', {'csv': csv})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['summary'], {'new': 2, 'duplicate': 1, 'error': 2}); self.assertEqual(r.json['created'], 0)
        r = self.center.post('/api/center/import', {'csv': csv, 'confirm': True})
        self.assertEqual(r.json['created'], 2)
        again = self.center.post('/api/center/import', {'csv': csv}).json['summary']
        self.assertEqual(again['new'], 0)
        g = self.server.sql("SELECT u.guest_center_id, u.password_hash FROM users u WHERE u.fullname='Ana García'")[0]
        self.assertEqual(g['guest_center_id'], self.cid()); self.assertEqual(g['password_hash'], '!')
        self.assertEqual(self.center.post('/api/center/import', {'csv': 'email\nx@y.z'}).status, 400)


class TeamAndSwitches(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'equipo6', phone='+34 600 600 020')
        cls.diver = t.make_diver('equipo6')

    def join(self, email, role, username):
        r = self.center.post('/api/center/team/invite', {'email': email, 'member_role': role})
        self.assertEqual(r.status, 200, r)
        mail = outbox(self.server, 'team_invite', email)[0]
        import re
        tok = re.search(r'equipo\?token=([A-Za-z0-9_\-]+)', mail['text']).group(1)
        c = self.client()
        self.assertEqual(c.get('/api/team/invite?token=' + tok).json['member_role'], role)
        r = c.post('/api/team/join', {'token': tok, 'fullname': f'Persona {role}', 'username': username, 'password': 'buceo-seguro-2026', 'accept_terms': True})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(c.post('/api/team/join', {'token': tok}).status, 400)
        c.user = c.me()['user']
        return c

    def test_roles_and_activity_log(self):
        rec = self.join('recepcion6@example.org', 'reception', 'recepcion6')
        ins = self.join('instructor6@example.org', 'instructor', 'instructor6')
        self.assertEqual(rec.user['center_id'], self.center.user['center_id']); self.assertEqual(rec.me()['member_role'], 'reception')
        # Reception: services yes; payments, plan, fiscal and team no
        r = rec.post('/api/provider-services', {'title': 'Salida de recepción', 'price': 30})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.center.post('/api/provider-services/update', {'id': r.json['id'], 'title': 'Salida de recepción', 'price': 35}).status, 200)   # owner edits the team's services
        self.assertEqual(self.make_center(self.admin, 'ajeno6', phone='+34 600 600 021').post('/api/provider-services/update', {'id': r.json['id'], 'title': 'x', 'price': 1}).status, 404)  # v50.47 (B.3): what belongs to another centre does not exist (404)
        for path in ('/api/provider/payment-profile', '/api/provider/fiscal', '/api/center/team/invite', '/api/provider/plan/checkout'):
            self.assertEqual(rec.post(path, {}).status, 403, path)
        self.assertEqual(rec.get('/api/provider/payments').status, 404)   # v50.58 (equipo por QR, comprobación 7): what a profile cannot read «does not exist» (404)
        self.assertEqual(rec.get('/api/center/export?kind=payments').status, 403)
        self.assertEqual(rec.get('/api/center/export?kind=bookings').status, 200)
        # Instructor: read only
        self.assertEqual(ins.post('/api/provider-services', {'title': 'No', 'price': 1}).status, 403)
        self.assertEqual(ins.get('/api/bookings').status, 200)
        # Planning shows the services of the whole centre (any creator)
        titles = [s['title'] for s in self.center.get(f"/api/provider-services?provider_id={self.center.user['id']}").json['items']]
        self.assertIn('Salida de recepción', titles)
        # Activity log of the centre
        acts = self.center.get('/api/center/activity').json['items']
        self.assertTrue(any(a['action'] == 'team_joined' for a in acts))
        self.assertEqual(rec.get('/api/center/activity').status, 404)   # v50.58 (equipo por QR, comprobación 7): what a profile cannot read «does not exist» (404)
        # Owner changes and removes
        self.assertEqual(self.center.post('/api/center/team/role', {'user_id': ins.user['id'], 'member_role': 'reception'}).status, 200)
        self.assertEqual(self.center.post('/api/center/team/role', {'user_id': self.center.user['id'], 'member_role': 'instructor'}).status, 400)
        self.assertEqual(self.center.post('/api/center/team/remove', {'user_id': ins.user['id']}).status, 200)
        self.assertEqual(self.server.sql('SELECT role FROM users WHERE id=?', (ins.user['id'],))[0]['role'], 'recreational')
        self.assertEqual(self.center.post('/api/center/team/invite', {'email': 'equipo6@diver.example.org', 'member_role': 'reception'}).status, 200)
        self.assertEqual(self.center.post('/api/center/team/invite', {'email': 'equipo6@centro-equipo6.example.org', 'member_role': 'reception'}).status, 400)

    def test_feature_switches(self):
        self.assertEqual(self.diver.post('/api/admin/features', {'switches': {'reviews': False}}).status, 403)
        r = self.admin.post('/api/admin/features', {'switches': {'reviews': False, 'points': False}})
        self.assertEqual(r.status, 200, r)
        self.assertFalse(self.client().get('/api/meta').json['features']['reviews'])
        cid = self.center.user['center_id']
        r = self.diver.post(f'/api/centers/{cid}/reviews', {'rating': 5})
        self.assertEqual(r.status, 403); self.assertEqual(r.json['feature_off'], 'reviews')
        self.assertEqual(self.client().get(f'/api/centers/{cid}').json['reviews'], [])
        self.assertEqual(self.diver.get('/api/points').status, 403)
        # codes already issued are still honoured at the desk (30 days' notice in the points rules)
        self.assertNotEqual(self.center.post('/api/center/redemptions/validate', {'code': 'NOEXISTE'}).json.get('feature_off'), 'points')
        self.assertFalse(self.center.me()['plan']['features']['rewards'])
        self.admin.post('/api/admin/features', {'switches': {'reviews': True, 'points': True}})
        self.assertEqual(self.diver.get('/api/points').status, 200)

    def test_pilot_mode_invites(self):
        self.admin.post('/api/admin/features', {'pilot_mode': True})
        c = self.client()
        r = c.register('Sin invitación', 'sininv6@example.org', 'sininv6', account_type='center', center_name='Centro sin invitación', phone='+34 600 600 099')
        self.assertEqual(r.status, 403)
        code = self.admin.post('/api/admin/invites', {'note': 'Centro amigo', 'days': 10}).json['code']
        r = self.client().register('Con invitación', 'coninv6@example.org', 'coninv6', account_type='center', center_name='Centro invitado', phone='+34 600 600 098', invite_code=code)
        self.assertEqual(r.status, 200, r)
        self.assertTrue(self.server.sql('SELECT used_at FROM pro_invites WHERE code=?', (code,))[0]['used_at'])
        self.admin.post('/api/admin/features', {'pilot_mode': False})


if __name__ == '__main__':
    unittest.main()
