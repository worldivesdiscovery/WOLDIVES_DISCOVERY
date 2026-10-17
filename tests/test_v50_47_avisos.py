"""v50.47 · parte G: avisos masivos (WhatsApp, correo y app) sin mezclar centros.

Meta (WhatsApp Cloud API) y Stripe son simuladores locales: nada sale de la máquina. Cada prueba usa una copia
temporal de la base. Cubre: G.3 (12 buceadores, ninguno de B, sin duplicados con doble clic o reinicio), G.4 (mismo
buceador en dos centros), G.6 (teléfonos: sin permiso o sin prefijo no hay WhatsApp; un número no pasa de A a B; la
base no guarda teléfonos en claro), G.7 (cada aviso sale del número de su centro; un origen forzado se bloquea),
G.8 (webhooks: firma falsa, número de otro centro, repetidos), G.9 (devoluciones en la cuenta correcta y nunca dos
veces), G.10 (9 idiomas), G.11 (50 buceadores en cola en menos de 2 s) y el recordatorio y el cambio de hora."""
import datetime as dt
import json
import re
import sqlite3
import time
import unittest
from pathlib import Path

from helpers import ServerTestCase, Client
from meta_mock import MetaMock
from stripe_mock import StripeMock

CONNECT_SECRET = 'whsec_connect_local'
DAY = lambda n: (dt.date.today() + dt.timedelta(days=n)).isoformat()
SHORT = lambda d: f'{d[8:10]}/{d[5:7]}'
LANGS = ['es', 'en', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'zh']
META = {'es': 'es', 'en': 'en', 'fr': 'fr', 'de': 'de', 'it': 'it', 'pt': 'pt_PT', 'nl': 'nl', 'pl': 'pl', 'zh': 'zh_CN'}


def wait_for(fn, seconds=20):
    end = time.time() + seconds
    while time.time() < end:
        v = fn()
        if v: return v
        time.sleep(0.3)
    return fn()


class Notices(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.meta = MetaMock()
        cls.meta.add_business('codeA', 'wabaA', [('pnidA', '+34 600 000 111')])
        cls.meta.add_business('codeB', 'wabaB', [('pnidB', '+34 600 000 222')])
        cls.meta.add_business('codeB2', 'wabaB2', [('pnidB2', '+34 600 000 111')])      # A's number inside another business
        cls.extra_env = {**cls.meta.env(), 'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base, 'STRIPE_CONNECT_WEBHOOK_SECRET': CONNECT_SECRET,
                         'WOD_AVISOS_DESHACER_SEGUNDOS': '3', 'WOD_AVISOS_SEGUNDOS': '1', 'WOD_MAINTENANCE_SECONDS': '2', 'WOD_DATA_KEY': 'clave-de-datos-de-las-pruebas-0123456789'}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.A = t.make_center(cls.admin, 'avisa', phone='+34 600 480 001')
        cls.B = t.make_center(cls.admin, 'avisb', phone='+34 600 480 002')
        cls.cidA, cls.cidB = cls.A.user['center_id'], cls.B.user['center_id']
        for cid, acct in ((cls.cidA, 'acct_avisa'), (cls.cidB, 'acct_avisb')):
            cls.server.sql("UPDATE centers SET stripe_account_id=?,stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (acct, cid))
        cls.sA = cls.A.post('/api/provider-services', {'title': 'Doble A', 'price': 40, 'booking_mode': 'payment'}).json['id']
        cls.sB = cls.B.post('/api/provider-services', {'title': 'Doble B', 'price': 30, 'booking_mode': 'payment'}).json['id']
        assert cls.A.post('/api/whatsapp/connect', {'code': 'codeA', 'waba_id': 'wabaA', 'phone_number_id': 'pnidA'}).status == 200
        assert cls.B.post('/api/whatsapp/connect', {'code': 'codeB', 'waba_id': 'wabaB', 'phone_number_id': 'pnidB'}).status == 200
        cls.divers = {}

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop(); cls.meta.stop()

    # ------------------------------------------------------------------------------------------------- helpers
    def diver(self, tag, phone='+34 611 {n}', consent=True, lang='es'):
        if tag in self.divers: return self.divers[tag]
        d = self.make_diver(tag)
        n = len(self.divers) + 100
        body = {'preferred_language': lang, 'wa_consent': consent}
        if phone: body['phone'] = phone.format(n=f'{n:03d} {n:03d}')
        assert d.post('/api/account/profile', body).status == 200
        self.divers[tag] = d
        return d

    def slot(self, center, sid, days, spots=60):
        return center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': DAY(days), 'slot_time': '09:00', 'spots_total': spots}).json['slot_id']

    def paid(self, d, center, cid, sid, slot, acct):
        r = d.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': 1})
        self.assertEqual(r.status, 200, r)
        sess = self.stripe.last_session(); self.stripe.pay(sess['id'])
        ev = {'id': f'evt_{time.time_ns()}', 'type': 'checkout.session.completed', 'account': acct, 'data': {'object': {'id': sess['id'], 'object': 'checkout.session', 'metadata': sess['metadata']}}}
        payload, sig = StripeMock.signed(ev, CONNECT_SECRET)
        Client(self.server, origin=None).request('POST', '/api/payments/webhook/connect', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})
        return r.json['id']

    def booked(self, d, cid, sid, slot):
        """A booking without payment (the centre has «payment» mode, so a direct SQL confirmation is used here)."""
        r = d.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': 1})
        self.assertEqual(r.status, 200, r)
        self.server.sql("UPDATE bookings SET status='confirmed',payment_status='at_center' WHERE id=?", (r.json['id'],))
        return r.json['id']

    def cancel(self, center, slot, **kw):
        body = {'slot_id': slot, 'reason': 'weather', 'note': 'Levante', 'confirm': SHORT(self.server.sql('SELECT slot_date FROM service_slots WHERE id=?', (slot,))[0]['slot_date']), **kw}
        r = center.post('/api/avisos/cancelar', body)
        self.assertEqual(r.status, 200, r)
        return r.json['uid']

    def finished(self, center, uid):
        st = wait_for(lambda: (lambda s: s if s['status'] in ('done', 'failed', 'blocked', 'undone') else None)(center.get(f'/api/avisos/{uid}').json), 25)
        self.assertIsNotNone(st, 'el aviso no ha terminado'); return st

    # ------------------------------------------------------------------------------------------------- G.3 / G.9
    def test_1_twelve_divers_nobody_of_b_no_duplicates_refunds_once(self):
        slA = self.slot(self.A, self.sA, 6); slB = self.slot(self.B, self.sB, 6)
        ds = [self.diver(f'doce{i}') for i in range(12)]
        bids = [self.paid(d, self.A, self.cidA, self.sA, slA, 'acct_avisa') for d in ds[:4]] + [self.booked(d, self.cidA, self.sA, slA) for d in ds[4:]]
        b_other = self.booked(self.diver('soloB'), self.cidB, self.sB, slB)
        pv = self.A.post('/api/avisos/preview', {'slot_id': slA, 'kind': 'slot_cancelled', 'reason': 'weather', 'policy': 'refund'}).json
        self.assertEqual(pv['recipients'], 12); self.assertEqual(pv['counts'], {'whatsapp': 12, 'email': 12, 'app': 12})
        self.assertTrue(all(p['name'] == 'Buceador d.' for p in pv['people']), pv['people'])                # first name + initial only
        self.assertEqual(pv['money']['refund'], 160.0)
        no_uid = {**pv, 'slot': {k: v for k, v in pv['slot'].items() if k != 'uid'}}                     # (the slot uid is random hex: it can contain «611»)
        self.assertNotIn('611', json.dumps(no_uid))                                                     # no diver phone in the preview
        refunds0 = len(self.stripe.refunds); sent0 = len(self.meta.sent)
        uid = self.cancel(self.A, slA, policy='refund')
        self.assertEqual(self.cancel(self.A, slA, policy='refund'), uid)                                  # double click: the same notice
        st = self.finished(self.A, uid)
        self.assertEqual(st['status'], 'done', st)
        mine = self.meta.sent[sent0:]
        self.assertEqual(len(mine), 12); self.assertEqual({m['phone_number_id'] for m in mine}, {'pnidA'})
        self.assertEqual(len({m['to'] for m in mine}), 12)
        rows = self.server.sql('SELECT channel,COUNT(*) n FROM notice_outbox WHERE batch_id=(SELECT id FROM notice_batches WHERE uid=?) GROUP BY channel', (uid,))
        self.assertEqual({r['channel']: r['n'] for r in rows}, {'whatsapp': 12, 'email': 12, 'app': 12})
        self.assertFalse(self.server.sql('SELECT 1 FROM notice_outbox WHERE booking_id=?', (b_other,)))   # nobody of B
        self.assertEqual(self.server.sql('SELECT status FROM bookings WHERE id=?', (b_other,))[0]['status'], 'confirmed')
        # Refunds: on A's account, one per paid booking, never twice (even if the worker runs again)
        wait_for(lambda: len(self.stripe.refunds) - refunds0 >= 4, 15)
        time.sleep(3)
        new = self.stripe.refunds[refunds0:]
        self.assertEqual(len(new), 4, new)
        self.assertEqual({r.get('account') for r in new}, {'acct_avisa'})                               # A's own Stripe account
        self.assertEqual(self.server.sql("SELECT COUNT(*) n FROM notice_refunds WHERE status='done'")[0]['n'] >= 4, True)
        # «Restart»: a row left «sending» is never sent again (it becomes «unknown»)
        self.server.sql("UPDATE notice_outbox SET status='sending',updated_at='2000-01-01T00:00:00+00:00' WHERE id=(SELECT MIN(id) FROM notice_outbox WHERE batch_id=(SELECT id FROM notice_batches WHERE uid=?))", (uid,))
        wait_for(lambda: self.server.sql("SELECT 1 FROM notice_outbox WHERE status='unknown'"), 10)
        time.sleep(2)
        self.assertEqual(len(self.meta.sent) - sent0, 12)
        # App notices in «Mi área → Avisos», with the link that opens only that booking
        msgs = ds[0].get('/api/me/area').json['messages']
        self.assertTrue(any('/r/' in (m['body'] or '') for m in msgs))
        link = re.search(r'/r/([0-9a-z]+\.c\.[0-9a-z]+\.[A-Za-z0-9_\-]+)', [m['body'] for m in msgs if '/r/' in (m['body'] or '')][0]).group(1)
        view = Client(self.server).get(f'/api/r/{link}')
        self.assertEqual(view.status, 200); self.assertEqual(view.json['booking']['ref'], f'WOD-{bids[0]:06d}')
        self.assertEqual(Client(self.server).get(f'/api/r/{link[:-2]}xx').status, 404)                   # tampered link
        self.assertNotIn('phone', json.dumps(view.json['booking']).replace('center_phone', ''))

    # ------------------------------------------------------------------------------------------------- G.4
    def test_2_same_diver_in_two_centres(self):
        both = self.diver('ambos')
        slA = self.slot(self.A, self.sA, 7); slB = self.slot(self.B, self.sB, 7)
        bA = self.booked(both, self.cidA, self.sA, slA); bB = self.booked(both, self.cidB, self.sB, slB)
        sent0 = len(self.meta.sent)
        uid = self.cancel(self.A, slA)
        self.finished(self.A, uid)
        mine = [m for m in self.meta.sent[sent0:]]
        self.assertEqual(len(mine), 1); self.assertEqual(mine[0]['phone_number_id'], 'pnidA')
        self.assertIn('Centro avisa', json.dumps(mine[0]['components']))                               # the centre's own name in the text
        self.assertEqual(self.server.sql('SELECT status,slot_id FROM bookings WHERE id=?', (bB,))[0], {'status': 'confirmed', 'slot_id': slB})
        self.assertFalse(self.server.sql('SELECT 1 FROM slot_cancel_offers WHERE booking_id=?', (bB,)))
        # Two centres notify the same diver at once: each email names its own centre
        uidB = self.cancel(self.B, slB)
        self.finished(self.B, uidB)
        mails = self.server.sql("SELECT text FROM email_outbox WHERE to_email='ambos@diver.example.org' AND template IN ('slot_cancelled','booking_cancelled_center') ORDER BY id")
        self.assertEqual(len(mails), 2)
        self.assertIn('Centro avisa', mails[0]['text']); self.assertNotIn('Centro avisb', mails[0]['text'])
        self.assertIn('Centro avisb', mails[1]['text']); self.assertNotIn('Centro avisa', mails[1]['text'])
        wa_b = [m for m in self.meta.sent[sent0:] if m['phone_number_id'] == 'pnidB']
        self.assertEqual(len(wa_b), 1)

    # ------------------------------------------------------------------------------------------------- G.6
    def test_3_phones_consent_and_prefix(self):
        sl = self.slot(self.A, self.sA, 8)
        no_consent = self.diver('sinpermiso', consent=False)
        no_prefix = self.diver('sinprefijo', phone='611 222 333')
        warn = no_prefix.post('/api/account/profile', {'phone': '611 222 333', 'wa_consent': True}).json
        self.assertIn('sin prefijo', warn['phone_warning'])
        for d in (no_consent, no_prefix): self.booked(d, self.cidA, self.sA, sl)
        pv = self.A.post('/api/avisos/preview', {'slot_id': sl}).json
        self.assertEqual(pv['counts'], {'whatsapp': 0, 'email': 2, 'app': 2})
        sent0 = len(self.meta.sent)
        self.finished(self.A, self.cancel(self.A, sl))
        self.assertEqual(len(self.meta.sent), sent0)
        # The number of A cannot be connected by B (another business with the same number): error without the centre
        r = self.B.post('/api/whatsapp/connect', {'code': 'codeB2', 'waba_id': 'wabaB2', 'phone_number_id': 'pnidB2'})
        self.assertEqual(r.status, 400); self.assertNotIn('avisa', r.body.decode().lower())
        time.sleep(0.5)
        self.assertTrue(self.server.sql("SELECT 1 FROM audit_log WHERE action='security_alert' AND entity_type='whatsapp_number_taken'"))
        # No phone in clear anywhere in the database file (profiles, bookings, notices, WhatsApp credentials)
        wal = Path(str(self.server.db) + '-wal'); raw = Path(self.server.db).read_bytes() + (wal.read_bytes() if wal.exists() else b'')
        for phone in ['611100100', '611 100 100', '600000111'] + list(self.meta.tokens):   # (the mock's wamid contains «pnidA»: it is Meta's message id, not a credential)
            self.assertNotIn(phone.encode(), raw, phone)
        self.assertFalse(self.server.sql("SELECT 1 FROM user_profiles WHERE phone IS NOT NULL AND phone NOT LIKE 'wdx1:%'"))
        with self.assertRaises(sqlite3.IntegrityError):
            self.server.sql("UPDATE user_profiles SET phone='+34600123123' WHERE user_id=?", (no_prefix.user['id'],))
        # A centre cannot write a diver's phone for notices: a manual booking's phone never becomes a WhatsApp recipient
        raw_db = sqlite3.connect(self.server.db)
        try: recips = [r[0] for r in raw_db.execute('SELECT recipient FROM notice_outbox')]
        finally: raw_db.close()
        self.assertTrue(recips and all(r is None or r.startswith('wdx1:') for r in recips))           # the snapshot of the recipient is encrypted too

    # ------------------------------------------------------------------------------------------------- G.7
    def test_4_each_notice_leaves_from_its_own_number_and_forced_mismatch_is_blocked(self):
        # Normal case: A's notices leave from A's number and B's from B's (also checked in test_2).
        sl = self.slot(self.A, self.sA, 9)
        self.booked(self.diver('origen'), self.cidA, self.sA, sl)
        sent0 = len(self.meta.sent)
        self.finished(self.A, self.cancel(self.A, sl))
        self.assertEqual([m['phone_number_id'] for m in self.meta.sent[sent0:]], ['pnidA'])
        self.server.sql("UPDATE users SET email='seguridad@worldives-pruebas.org' WHERE username='admin'")   # an address that receives the alert
        # Simulated bug: A's WhatsApp row ends up with the credentials of B's number. Nothing may leave from it.
        keyA, keyB = f'c:{self.cidA}', f'c:{self.cidB}'
        accA = self.server.sql('SELECT phone_number_id, token FROM whatsapp_accounts WHERE provider_id=?', (keyA,))[0]
        accB = self.server.sql('SELECT phone_number_id, token FROM whatsapp_accounts WHERE provider_id=?', (keyB,))[0]
        db = sqlite3.connect(self.server.db)
        try:
            db.execute('UPDATE whatsapp_accounts SET phone_number_id=?, token=? WHERE provider_id=?', (accB['phone_number_id'], accB['token'], keyA)); db.commit()
        finally: db.close()
        try:
            sl2 = self.slot(self.A, self.sA, 10)
            self.booked(self.diver('origen2'), self.cidA, self.sA, sl2)
            sent0 = len(self.meta.sent)
            uid2 = self.cancel(self.A, sl2)
            self.finished(self.A, uid2)
            row = self.server.sql("SELECT status,skip_reason FROM notice_outbox WHERE channel='whatsapp' AND batch_id=(SELECT id FROM notice_batches WHERE uid=?)", (uid2,))[0]
            self.assertEqual((row['status'], row['skip_reason']), ('blocked', 'Bloqueado por seguridad'))
            self.assertEqual(self.meta.sent[sent0:], [])                                               # nothing from B's number
            time.sleep(0.5)
            self.assertTrue(self.server.sql("SELECT 1 FROM audit_log WHERE action='security_alert' AND entity_type='notice_tenant_mismatch'"))
            self.assertTrue(self.server.sql("SELECT 1 FROM email_outbox WHERE template='admin_security_alert'"))
            ch = {r['channel']: r['status'] for r in self.server.sql("SELECT channel,status FROM notice_outbox WHERE batch_id=(SELECT id FROM notice_batches WHERE uid=?)", (uid2,))}
            self.assertEqual((ch['email'], ch['app']), ('sent', 'sent'))                              # email and app still reach the diver
        finally:
            db = sqlite3.connect(self.server.db)
            try:
                db.execute('UPDATE whatsapp_accounts SET phone_number_id=?, token=? WHERE provider_id=?', (accA['phone_number_id'], accA['token'], keyA)); db.commit()
            finally: db.close()

    # ------------------------------------------------------------------------------------------------- G.8
    def test_5_webhooks(self):
        sl = self.slot(self.A, self.sA, 11)
        self.booked(self.diver('webhook'), self.cidA, self.sA, sl)
        uid = self.cancel(self.A, sl); self.finished(self.A, uid)
        wamid = self.server.sql("SELECT wamid FROM notice_outbox WHERE channel='whatsapp' AND batch_id=(SELECT id FROM notice_batches WHERE uid=?)", (uid,))[0]['wamid']
        hook = lambda payload, sig=None: Client(self.server, origin=None).request('POST', '/api/whatsapp/webhook', raw=(raw := json.dumps(payload).encode()) if sig is None else payload,
                                                                                    content_type='application/json', headers={'X-Hub-Signature-256': sig or MetaMock.signed(payload)[1]})
        # fake signature
        raw, _ = MetaMock.signed(MetaMock.status_event('pnidA', wamid, 'read'))
        r = Client(self.server, origin=None).request('POST', '/api/whatsapp/webhook', raw=raw, content_type='application/json', headers={'X-Hub-Signature-256': 'sha256=' + '0' * 64})
        self.assertEqual(r.status, 403)
        # B's number reporting A's message: discarded
        raw, sig = MetaMock.signed(MetaMock.status_event('pnidB', wamid, 'read', ts='1700000001'))
        r = Client(self.server, origin=None).request('POST', '/api/whatsapp/webhook', raw=raw, content_type='application/json', headers={'X-Hub-Signature-256': sig})
        self.assertEqual((r.status, r.json['applied'], r.json['ignored']), (200, 0, 1))
        self.assertEqual(self.server.sql('SELECT status FROM notice_outbox WHERE wamid=?', (wamid,))[0]['status'], 'sent')
        # the right number: delivered, then read; repeated events are ignored
        for status, ts in (('delivered', '1700000010'), ('read', '1700000020'), ('read', '1700000020')):
            raw, sig = MetaMock.signed(MetaMock.status_event('pnidA', wamid, status, ts=ts))
            r = Client(self.server, origin=None).request('POST', '/api/whatsapp/webhook', raw=raw, content_type='application/json', headers={'X-Hub-Signature-256': sig})
            self.assertEqual(r.status, 200)
        self.assertEqual(r.json['ignored'], 1)
        self.assertEqual(self.server.sql('SELECT status FROM notice_outbox WHERE wamid=?', (wamid,))[0]['status'], 'read')
        # a diver's reply (incoming message) is never stored
        reply = {'object': 'whatsapp_business_account', 'entry': [{'id': 'wabaA', 'changes': [{'field': 'messages', 'value': {'metadata': {'phone_number_id': 'pnidA'},
                 'messages': [{'from': '34611000000', 'id': 'wamid.in.1', 'type': 'text', 'text': {'body': 'TEXTO-DE-RESPUESTA-SECRETO'}}]}}]}]}
        raw, sig = MetaMock.signed(reply)
        self.assertEqual(Client(self.server, origin=None).request('POST', '/api/whatsapp/webhook', raw=raw, content_type='application/json', headers={'X-Hub-Signature-256': sig}).status, 200)
        self.assertNotIn(b'TEXTO-DE-RESPUESTA-SECRETO', Path(self.server.db).read_bytes())
        # webhook verification
        self.assertEqual(Client(self.server).get('/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=verificar-pruebas&hub.challenge=123').body, b'123')
        self.assertEqual(Client(self.server).get('/api/whatsapp/webhook?hub.mode=subscribe&hub.verify_token=otro&hub.challenge=123').status, 403)

    # ------------------------------------------------------------------------------------------------- G.10
    def test_6_nine_languages(self):
        sl = self.slot(self.A, self.sA, 12)
        ds = {l: self.diver(f'idioma{l}', lang=l) for l in LANGS}
        for d in ds.values(): self.booked(d, self.cidA, self.sA, sl)
        pv = self.A.post('/api/avisos/preview', {'slot_id': sl}).json
        self.assertEqual(sorted(p['lang'] for p in pv['previews']), sorted(LANGS))
        sent0 = len(self.meta.sent)
        self.finished(self.A, self.cancel(self.A, sl))
        mine = self.meta.sent[sent0:]
        self.assertEqual(sorted(m['lang'] for m in mine), sorted(META.values()))
        for l, d in ds.items():
            subj = [m['subject'] for m in d.get('/api/me/area').json['messages'] if m['kind'] == 'notice'][0]
            expected = json.loads((Path(__file__).resolve().parents[1] / 'app' / 'data' / 'whatsapp_plantillas.json').read_text(encoding='utf-8'))['textos']['app_subject_slot_cancelled'][l].split('{')[0].strip()
            self.assertTrue(subj.startswith(expected), (l, subj))
        # the Meta templates exist in the 9 languages in each centre's account
        self.assertEqual(len([k for k in self.meta.templates['wabaA'] if k.startswith('worldives_salida_cancelada:')]), 9)

    # ------------------------------------------------------------------------------------------------- G.11
    def test_7_fifty_divers_queued_in_less_than_two_seconds(self):
        sl = self.slot(self.A, self.sA, 13, spots=60)
        for i in range(50):
            self.booked(self.diver(f'cin{i}'), self.cidA, self.sA, sl)
        uid = self.cancel(self.A, sl)
        st = self.finished(self.A, uid)
        counts = json.loads(self.server.sql('SELECT counts FROM notice_batches WHERE uid=?', (uid,))[0]['counts'])
        self.assertEqual(counts['destinatarios'], 50)
        self.assertLess(counts['ms'], 2000, counts)
        self.assertEqual(self.server.sql("SELECT COUNT(*) n FROM notice_outbox WHERE batch_id=(SELECT id FROM notice_batches WHERE uid=?)", (uid,))[0]['n'], 150)

    # ------------------------------------------------------------------------------------------------- E.1
    def test_8_undo_change_and_reminder(self):
        sl = self.slot(self.A, self.sA, 14)
        b = self.booked(self.diver('deshacer'), self.cidA, self.sA, sl)
        uid = self.cancel(self.A, sl)
        self.assertEqual(self.A.post(f'/api/avisos/{uid}/deshacer', {}).status, 200)
        time.sleep(5)
        self.assertEqual(self.A.get(f'/api/avisos/{uid}').json['status'], 'undone')
        self.assertIsNone(self.server.sql('SELECT cancelled_at FROM service_slots WHERE id=?', (sl,))[0]['cancelled_at'])
        self.assertFalse(self.server.sql('SELECT 1 FROM notice_outbox WHERE booking_id=?', (b,)))
        # Change of time and meeting point
        sent0 = len(self.meta.sent)
        r = self.A.post('/api/avisos/cambio', {'slot_id': sl, 'new_time': '10:30', 'meeting_point': 'Puerto de Xàbia, pantalán 3', 'confirm': SHORT(DAY(14))})
        self.assertEqual(r.status, 200, r)
        self.finished(self.A, r.json['uid'])
        self.assertEqual(self.server.sql('SELECT slot_time,meeting_point FROM service_slots WHERE id=?', (sl,))[0], {'slot_time': '10:30', 'meeting_point': 'Puerto de Xàbia, pantalán 3'})
        self.assertEqual(self.server.sql('SELECT booking_time FROM bookings WHERE id=?', (b,))[0]['booking_time'], '10:30')
        self.assertEqual([m['template'] for m in self.meta.sent[sent0:]], ['worldives_cambio_salida'])
        # Day-before reminder at the hour the centre chose (here: now)
        tomorrow = self.slot(self.A, self.sA, 1)
        self.booked(self.diver('recordar'), self.cidA, self.sA, tomorrow)
        self.assertEqual(self.A.post('/api/avisos/ajustes', {'reminder_enabled': True, 'reminder_hour': 0, 'reminder_bring': 'Titulación y toalla'}).status, 200)
        wait_for(lambda: [m for m in self.meta.sent[sent0:] if m['template'] == 'worldives_recordatorio'], 25)
        rem = [m for m in self.meta.sent[sent0:] if m['template'] == 'worldives_recordatorio']
        self.assertEqual(len(rem), 1)
        self.assertIn('Titulación y toalla', json.dumps(rem[0]['components'], ensure_ascii=False))
        self.assertEqual(len(rem[0]['components']), 3)                       # body + link button + map button
        # Reception cannot send mass notices; the type-to-confirm is required
        self.assertEqual(self.A.post('/api/avisos/cancelar', {'slot_id': sl, 'reason': 'weather', 'confirm': 'otra cosa'}).status, 400)

    def test_9_disconnect_and_expired_token(self):
        c = self.make_center(self.admin, 'aviscc', phone='+34 600 480 003')
        self.meta.add_business('codeC', 'wabaC', [('pnidC', '+34 600 000 333')])
        self.assertEqual(c.post('/api/whatsapp/connect', {'code': 'codeC', 'waba_id': 'wabaC', 'phone_number_id': 'pnidC'}).status, 200)
        st = c.get('/api/whatsapp').json
        self.assertTrue(st['connected']); self.assertNotIn('token', json.dumps(st).lower().replace('verify', ''))
        tok = [k for k, v in self.meta.tokens.items() if v == 'wabaC'][0]
        self.meta.revoked.add(tok)
        sid = c.post('/api/provider-services', {'title': 'Doble C', 'price': 20, 'booking_mode': 'request'}).json['id']
        sl = self.slot(c, sid, 15)
        self.booked(self.diver('caducado'), c.user['center_id'], sid, sl)
        self.finished(c, self.cancel(c, sl))
        self.assertEqual(c.get('/api/whatsapp').json['status'], 'reconnect')
        ch = {r['channel']: r['status'] for r in self.server.sql("SELECT channel,status FROM notice_outbox WHERE slot_id=?", (sl,))}
        self.assertEqual((ch['email'], ch['app'], ch['whatsapp']), ('sent', 'sent', 'failed'))
        self.assertEqual(c.post('/api/whatsapp/disconnect', {}).status, 200)
        self.assertFalse(self.server.sql("SELECT 1 FROM whatsapp_accounts WHERE provider_id=?", (f"c:{c.user['center_id']}",)))
        self.assertTrue(self.server.sql("SELECT 1 FROM audit_log WHERE action='whatsapp_disconnected'"))


if __name__ == '__main__':
    unittest.main()
