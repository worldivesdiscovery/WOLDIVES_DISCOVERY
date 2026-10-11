"""Fase 3 (v50.35): «Monedero» → WORLDIVES points. Migration 1:1 rounded up, earning, exchange codes validated by
the centre, grants with monthly limits, and the prohibitions (no top-ups, transfers or money)."""
import sqlite3
import unittest

from helpers import ServerTestCase, Server


class Points(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.extra_env = {'WOD_MAINTENANCE_SECONDS': '2'}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(admin=cls.admin, tag='puntos', phone='+34 600 000 031')
        cls.other = t.make_center(admin=cls.admin, tag='otropuntos', phone='+34 600 000 032')
        cls.cid = cls.center.user['center_id']
        cls.diver = t.make_diver('pts1')
        cls.diver2 = t.make_diver('pts2')

    def give(self, user, pts):
        self.server.sql("INSERT INTO points_ledger(user_id,points,kind,description,created_at) VALUES(?,?,'adjust','test',datetime('now'))", (user.user['id'], pts))

    def balance(self, user):
        return user.get('/api/points').json['balance']

    def offer(self, center=None, cost=30, **extra):
        data = {'title': 'Descuento 10 %', 'reward_type': 'discount', 'cost_points': cost, 'value_text': '10 % de descuento'}
        data.update(extra)
        r = (center or self.center).post('/api/provider/reward-offers', data)
        self.assertEqual(r.status, 200, r)
        return r.json['id']

    def test_points_are_earned_by_diving(self):
        before = self.balance(self.diver2)
        r = self.diver2.post('/api/logbook', {'dive_date': '2026-09-01', 'site': 'Cala Blanca', 'country': 'España', 'depth': 12, 'duration': 40, 'dive_type': 'Arrecife'})
        self.assertEqual(r.status, 200, r)
        d = self.diver2.get('/api/points').json
        self.assertGreaterEqual(d['balance'] - before, 60)  # dive registered (10) + first dive (50)
        self.assertTrue(all(isinstance(x['points'], int) for x in d['items']))
        rw = self.diver2.get('/api/rewards').json
        self.assertEqual(rw['balance'], d['balance'])

    def test_logbook_points_cannot_be_farmed(self):
        diver = self.make_diver('granja3')
        ids = [diver.post('/api/logbook', {'dive_date': '2026-08-15', 'site': f'Inmersión {i}', 'country': 'España', 'dive_type': 'Arrecife'}).json['id'] for i in range(8)]
        diver.get('/api/points')
        per_entry = self.server.sql("SELECT COUNT(*) n FROM reward_events WHERE user_id=? AND event_key LIKE 'logbook:dive:%'", (diver.user['id'],))[0]['n']
        self.assertEqual(per_entry, 4)   # at most 4 entries of the same day give points
        single = diver.post('/api/logbook', {'dive_date': '2026-08-20', 'site': 'Sola', 'country': 'España', 'dive_type': 'Arrecife'}).json['id']
        before = self.balance(diver)
        self.assertEqual(diver.post('/api/logbook/delete', {'id': single}).status, 200)
        self.assertEqual(before - self.balance(diver), 10)   # deleting the entry takes its points back
        self.assertEqual(diver.post('/api/logbook', {'dive_date': '2099-01-01', 'site': 'Futuro', 'country': 'España', 'dive_type': 'Arrecife'}).status, 400)

    def test_exchange_and_validation_by_the_centre(self):
        oid = self.offer(cost=30)
        self.give(self.diver, 40)
        b0 = self.balance(self.diver)
        r = self.diver.post('/api/rewards/redeem', {'offer_id': oid})
        self.assertEqual(r.status, 200, r)
        code = r.json['code']
        self.assertEqual(self.balance(self.diver), b0 - 30)
        self.assertEqual(self.other.post('/api/center/redemptions/validate', {'code': code}).status, 403)  # not its advantage
        self.assertEqual(self.diver.post('/api/center/redemptions/validate', {'code': code}).status, 403)
        look = self.center.get('/api/center/redemptions?code=' + code)
        self.assertEqual((look.status, look.json['item']['status']), (200, 'issued'))
        self.assertNotIn('Pérez', look.json['item']['customer'])  # only «Nombre P.»
        self.assertEqual(self.center.post('/api/center/redemptions/validate', {'code': code}).status, 200)
        again = self.center.post('/api/center/redemptions/validate', {'code': code})
        self.assertEqual(again.status, 400)
        self.assertIn('ya se usó', again.json['error'])
        rid = self.server.sql('SELECT id FROM reward_redemptions WHERE code=?', (code,))[0]['id']
        self.assertEqual(self.diver.post('/api/points/codes/cancel', {'id': rid}).status, 400)  # already used
        row = self.server.sql('SELECT status,redeemed_at,redeemed_center_id FROM reward_redemptions WHERE code=?', (code,))[0]
        self.assertEqual((row['status'], row['redeemed_center_id']), ('redeemed', self.cid))
        self.assertTrue(row['redeemed_at'])

    def test_not_enough_points(self):
        oid = self.offer(cost=99999)
        r = self.diver2.post('/api/rewards/redeem', {'offer_id': oid})
        self.assertEqual(r.status, 400)
        self.assertIn('Te faltan', r.json['error'])

    def test_cancel_and_expiry_give_points_back(self):
        oid = self.offer(cost=10, stock=5)
        self.give(self.diver, 30)
        b0 = self.balance(self.diver)
        code = self.diver.post('/api/rewards/redeem', {'offer_id': oid}).json['code']
        rid = self.server.sql('SELECT id FROM reward_redemptions WHERE code=?', (code,))[0]['id']
        self.assertEqual(self.diver2.post('/api/points/codes/cancel', {'id': rid}).status, 404)  # not his
        self.assertEqual(self.diver.post('/api/points/codes/cancel', {'id': rid}).status, 200)
        self.assertEqual(self.balance(self.diver), b0)
        self.assertEqual(self.center.post('/api/center/redemptions/validate', {'code': code}).status, 400)
        self.assertEqual(self.server.sql('SELECT stock FROM reward_offers WHERE id=?', (oid,))[0]['stock'], 5)
        code2 = self.diver.post('/api/rewards/redeem', {'offer_id': oid}).json['code']
        self.server.sql("UPDATE reward_redemptions SET expires_at='2000-01-01T00:00:00+00:00' WHERE code=?", (code2,))
        import time
        end = time.time() + 15
        while time.time() < end and self.server.sql('SELECT status FROM reward_redemptions WHERE code=?', (code2,))[0]['status'] == 'issued':
            time.sleep(1)
        self.assertEqual(self.server.sql('SELECT status FROM reward_redemptions WHERE code=?', (code2,))[0]['status'], 'expired')
        self.assertEqual(self.balance(self.diver), b0)

    def test_grants_with_monthly_limit(self):
        client = self.make_diver('ptsclient')
        stranger = self.make_diver('ptsstranger')
        cid = self.cid
        self.server.sql("INSERT INTO center_links(user_id,center_id,first_checkin,last_checkin) VALUES(?,?,datetime('now'),datetime('now'))", (client.user['id'], cid))
        r = self.center.post('/api/provider/points-grant', {'user_id': client.user['id'], 'points': 60, 'reason': 'gracias'})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['left_this_month'], 40)
        over = self.center.post('/api/provider/points-grant', {'user_id': client.user['id'], 'points': 41})
        self.assertEqual(over.status, 400)
        self.assertIn('Límite por cliente', over.json['error'])
        self.assertEqual(self.center.post('/api/provider/points-grant', {'user_id': stranger.user['id'], 'points': 5}).status, 403)
        self.assertEqual(self.center.post('/api/provider/points-grant', {'user_id': client.user['id'], 'points': 2.5}).status, 400)
        self.assertEqual(client.post('/api/provider/points-grant', {'user_id': stranger.user['id'], 'points': 5}).status, 403)
        self.assertEqual(self.center.post('/api/provider/wallet-grant', {'user_id': client.user['id'], 'amount': 5}).status, 410)
        items = client.get('/api/points').json['items']
        self.assertTrue(any(x['kind'] == 'granted' and x['points'] == 60 for x in items))

    def test_no_money_features(self):
        for path in ('/api/points/topup', '/api/points/transfer', '/api/points/withdraw', '/api/wallet'):
            self.assertEqual(self.diver.post(path, {'amount': 10, 'points': 10, 'to_user_id': 1}).status, 404, path)
        self.assertEqual(self.diver.get('/api/wallet').status, 404)

    def test_offers_belong_to_a_centre_and_cost_whole_points(self):
        self.assertEqual(self.center.post('/api/provider/reward-offers', {'title': 'x', 'cost_points': 0}).status, 400)
        self.assertEqual(self.center.post('/api/provider/reward-offers', {'title': 'x', 'cost_points': '1.5'}).status, 400)
        self.assertEqual(self.center.post('/api/provider/reward-offers', {'title': 'x', 'cost_points': 5, 'reward_type': 'cash'}).status, 400)
        oid = self.offer(cost=12)
        self.assertEqual(self.other.post('/api/provider/reward-offers', {'id': oid, 'title': 'robada', 'cost_points': 1}).status, 403)
        self.assertEqual(self.diver.post('/api/provider/reward-offers', {'title': 'x', 'cost_points': 5}).status, 403)
        offers = self.diver.get('/api/rewards').json['offers']
        self.assertTrue(all(o['center_id'] for o in offers))


class WalletMigration(unittest.TestCase):
    def test_wallet_becomes_points(self):
        s = Server()
        try:
            s.start(); s.stop(cleanup=False)
            db = sqlite3.connect(s.db)
            db.execute("INSERT INTO users(id,fullname,email,username,password_hash,role,created_at) VALUES(9601,'U','u9601@x.org','u9601','!','recreational','2026-01-01')")
            db.execute("INSERT INTO reward_events(user_id,event_key,title,points,wallet_amount,created_at) VALUES(9601,'k1','Perfil',50,0,'2026-01-02')")
            db.execute("INSERT INTO reward_events(user_id,event_key,title,points,wallet_amount,created_at) VALUES(9601,'k2','Inmersión',10,0,'2026-01-03')")
            db.execute("INSERT INTO wallet_transactions(user_id,amount,description,created_at) VALUES(9601,12.30,'Saldo regalado','2026-01-04')")
            db.execute("INSERT INTO wallet_transactions(user_id,amount,description,created_at) VALUES(9601,-5,'Canje','2026-01-05')")
            cid = db.execute('SELECT id FROM centers LIMIT 1').fetchone()[0]
            db.execute("INSERT INTO reward_offers(center_id,title,reward_type,cost_wallet,active,created_at,updated_at) VALUES(?,'Oferta','dive_credit',4.5,1,'x','x')", (cid,))
            db.execute("DELETE FROM points_ledger"); db.execute("UPDATE reward_offers SET cost_points=NULL"); db.execute("DELETE FROM schema_migrations WHERE version='50.35'")
            db.commit(); db.close()
            s.start()
            rows = s.sql('SELECT points,kind FROM points_ledger WHERE user_id=9601 ORDER BY id')
            self.assertEqual(sorted((r['kind'], r['points']) for r in rows), [('earned', 10), ('earned', 50), ('migrated', 8)])  # 7,30 € → 8
            self.assertEqual(len(s.sql('SELECT 1 FROM wallet_transactions WHERE user_id=9601')), 2)  # history kept
            o = s.sql("SELECT cost_points,reward_type FROM reward_offers WHERE title='Oferta'")[0]
            self.assertEqual((o['cost_points'], o['reward_type']), (5, 'activity'))
            s.stop(cleanup=False); s.start()  # idempotent
            self.assertEqual(len(s.sql('SELECT 1 FROM points_ledger WHERE user_id=9601')), 3)
        finally:
            s.stop()


if __name__ == '__main__':
    unittest.main(verbosity=2)
