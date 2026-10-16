"""v50.58 · encargo del 16/10/2026: el alquiler de equipo es un extra dentro de la inmersión, no un servicio.

Las comprobaciones del encargo, en el servidor (la web, la app, el widget y la API usan esta misma función):
1. El centro activa piezas, pone precios y un «Equipo completo»; crea «Inmersión simple» a 50 € con «Pago al reservar» y
   el alquiler sale activado.
2. Solo máscara y aletas a 5 €: 60 €. Dos buceadores (traje, máscara, aletas y escarpines; el otro solo boya). Una con
   «Equipo completo».
3. Botella y plomos nunca son piezas: siempre «Incluido».
4. La reserva, la lista del barco y «Equipo para preparar» muestran lo pedido con tallas.
5. Con 2 jackets M en stock, una tercera no se puede pedir ese día.
6. El buceador añade una linterna desde Mis reservas y se le cobra la diferencia; el centro añade una pieza en el
   mostrador como «Pagado en el centro».
7. «Bajo petición»: el equipo va en la solicitud y no se cobra nada hasta aceptar.
8. Las reservas antiguas (codigo:cantidad o texto) siguen viéndose y cobrándose bien.
"""
import csv
import io
import json
import sys
import time
import unittest
from pathlib import Path
from urllib.parse import quote

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from helpers import ServerTestCase, Client  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402
from wod import equipo as weq  # noqa: E402

WEBHOOK_SECRET = 'whsec_test_local'
FAR = '2099-12-31'
DAY = '2031-06-14'


class Helpers(unittest.TestCase):
    def test_list_has_no_tank_nor_weights(self):
        items, kit = weq.merge_catalog([{'code': 'tank', 'label': 'Botella', 'price': 5, 'active': 1}, {'code': 'wetsuit', 'label': 'Traje de neopreno', 'price': 8, 'active': 1}])
        codes = [i['code'] for i in items]
        self.assertEqual(len(codes), 11)
        self.assertNotIn('tank', codes); self.assertNotIn('weights', codes)
        self.assertEqual([i['label'] for i in items if i['code'] == 'wetsuit'], ['Traje o neopreno'], 'the old name becomes the new one')
        self.assertTrue([i for i in items if i['code'] == 'wetsuit'][0]['active'])
        self.assertEqual(weq.INCLUDED_TEXT, 'Incluido: botella y plomos')

    def test_kit_and_prep(self):
        items, kit = weq.merge_catalog([dict(code=c, label=weq.LABEL[c], price=5, active=1) for c in ('mask', 'fins', 'boots', 'wetsuit', 'bcd', 'regulator')]
                                       + [{'code': 'full_kit', 'label': 'Equipo completo', 'price': 25, 'active': 1}])
        mode, pieces, k = weq.service_offer(items, kit, 'offer', None)
        self.assertEqual(k['price'], 25); self.assertEqual(set(k['codes']), set(weq.DEFAULT_KIT))
        full = [{'code': c, 'size': {'fins': '42', 'boots': '42', 'wetsuit': 'M', 'bcd': 'M'}.get(c, ''), 'thick': ''} for c in k['codes']]
        sel = weq.check_selection([{'items': full, 'kit': True}], pieces, k)
        rows, lines, info = weq.price(sel, pieces, k, {'dive': 1, 'day': 1})
        self.assertEqual(sum(r['total'] for r in rows), 25.0, 'the closed price of the full kit')
        self.assertEqual(info['kit_broken'], [])
        sel = weq.check_selection([{'items': full[1:], 'kit': True}], pieces, k)
        rows, lines, info = weq.price(sel, pieces, k, {'dive': 1, 'day': 1})
        self.assertEqual(info['kit_broken'], [0]); self.assertEqual(sum(r['total'] for r in rows), 25.0, 'five pieces at 5 €, by pieces')
        g = weq.prep_groups([{'code': 'fins', 'label': 'Aletas', 'size': '39', 'thick': ''}, {'code': 'fins', 'label': 'Aletas', 'size': '39', 'thick': ''},
                             {'code': 'fins', 'label': 'Aletas', 'size': '42', 'thick': ''}, {'code': 'wetsuit', 'label': 'Traje', 'size': 'M', 'thick': '5'},
                             {'code': 'regulator', 'label': 'Regulador', 'size': '', 'thick': ''}])
        self.assertEqual(weq.prep_text(g), 'Aletas: 2 × 39, 1 × 42 · Trajes: 1 × M 5 mm · Reguladores: 1')

    def test_old_format(self):
        sel = weq.legacy_selection(['fins:1', 'mask', 'tank'], 2)
        self.assertEqual([[i['code'] for i in d['items']] for d in sel], [['fins', 'mask'], ['mask']])


class Equipment(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': cls.stripe.base, 'STRIPE_WEBHOOK_SECRET': WEBHOOK_SECRET}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'equipo')
        cls.cid = cls.center.user['center_id']
        cls.server.sql(f"UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_test_eq',"
                       "stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.cid,))
        cls.diver = t.make_diver('equipo1'); cls.diver2 = t.make_diver('equipo2'); cls.diver3 = t.make_diver('equipo3'); cls.diver4 = t.make_diver('equipo4'); cls.diver5 = t.make_diver('equipo5')
        r = cls.center.post('/api/provider/equipment', {
            'items': [{'code': 'mask', 'active': True, 'price': 5}, {'code': 'fins', 'active': True, 'price': 5}, {'code': 'boots', 'active': True, 'price': 3},
                      {'code': 'wetsuit', 'active': True, 'price': 10, 'thicknesses': ['5', '7']}, {'code': 'bcd', 'active': True, 'price': 8},
                      {'code': 'regulator', 'active': True, 'price': 8}, {'code': 'torch', 'active': True, 'price': 4}, {'code': 'smb', 'active': True, 'price': 2}],
            'kit': {'active': True, 'price': 30}, 'stock': {'bcd': {'M': 2}}})
        assert r.status == 200, r
        cls.sid, cls.slot = cls.make_service(cls, 'Inmersión simple', 'payment')
        cls.rsid, cls.rslot = cls.make_service(cls, 'Inmersión bajo petición', 'request')

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.stripe.stop()

    def make_service(self, title, mode):
        r = self.center.post('/api/provider-services/wizard', {'publish': True, 'kind': 'dive', 'title': title, 'hours': 2, 'minutes': 0, 'start_time': '10:00',
                                                                'price': 50, 'max_participants': 10, 'booking_mode': mode,
                                                                'schedule': {'mode': 'dates', 'dates': [DAY]}})
        assert r.status == 200, r
        slot = self.server.sql('SELECT id FROM service_slots WHERE service_id=?', (r.json['id'],))[0]['id']
        return r.json['id'], slot

    def webhook(self, event):
        payload, sig = StripeMock.signed(event, WEBHOOK_SECRET)
        return Client(self.server, origin=None).request('POST', '/api/payments/webhook', raw=payload, content_type='application/json', headers={'Stripe-Signature': sig})

    def pay_last(self, tag):
        sess = self.stripe.last_session(); self.stripe.pay(sess['id'])
        r = self.webhook({'id': f'evt_{tag}_{time.time_ns()}', 'type': 'checkout.session.completed', 'data': {'object': {'id': sess['id'], 'metadata': sess['metadata']}}})
        self.assertEqual(r.status, 200, r)
        return sess

    def book(self, diver, equipment, sid=None, slot=None, pax=None, **extra):
        data = {'center_id': self.cid, 'service_id': sid or self.sid, 'slot_id': slot or self.slot, 'participants': pax or max(1, len(equipment)), 'equipment': equipment}
        data.update(extra)
        return diver.post('/api/bookings', data)

    def bk(self, bid):
        return self.server.sql('SELECT * FROM bookings WHERE id=?', (bid,))[0]

    # 1 · configuration and the service
    def test_1_config_and_service_offer(self):
        cfg = self.center.get('/api/provider/equipment').json
        self.assertTrue(cfg['configured'])
        self.assertEqual(len([i for i in cfg['items'] if not i['custom']]), 11)
        self.assertNotIn('tank', [i['code'] for i in cfg['items']])
        self.assertEqual(cfg['stock'], {'bcd': {'M': 2}})
        self.assertEqual(cfg['kit']['price'], 30)
        r = self.center.post('/api/provider/equipment', {'items': [{'code': 'computer', 'active': True}]})
        self.assertEqual(r.status, 400); self.assertIn('Pon el precio', r.json['error'])
        self.assertEqual(self.center.post('/api/provider/equipment/custom', {'label': 'Botella'}).status, 400, 'the tank is never a piece')
        self.assertEqual(self.center.post('/api/center-equipment', {'code': 'tank', 'price': 5}).status, 400)
        r = self.center.post('/api/provider/equipment/custom', {'label': 'Cámara', 'icon': 'camera', 'price': 15})
        self.assertEqual(r.status, 200, r); self.assertIn('Cámara', [i['label'] for i in r.json['items']])
        svc = [x for x in self.diver.get(f'/api/provider-services?center_id={self.cid}').json['items'] if x['id'] == self.sid][0]
        self.assertEqual(svc['rental']['mode'], 'offer', 'a dive offers the rental by default')
        self.assertEqual(svc['rental']['included'], 'Incluido: botella y plomos')
        codes = [p['code'] for p in svc['rental']['pieces']]
        self.assertIn('mask', codes); self.assertNotIn('tank', codes); self.assertIn('Cámara', [p['label'] for p in svc['rental']['pieces']])
        pub = self.diver.get(f'/api/center-equipment?center_id={self.cid}').json
        self.assertNotIn('tank', [i['code'] for i in pub['items']]); self.assertEqual(pub['included'], 'Incluido: botella y plomos')
        # A course: the equipment is included in the price by default
        r = self.center.post('/api/provider-services/wizard', {'publish': True, 'kind': 'course', 'title': 'Open Water incluido', 'plan': {'preset': '3full'},
                                                                'price': 400, 'max_participants': 4, 'booking_mode': 'request', 'schedule': {'mode': 'dates', 'dates': [DAY]}})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.server.sql('SELECT rental_mode FROM provider_services WHERE id=?', (r.json['id'],))[0]['rental_mode'], 'included')
        slot = self.server.sql('SELECT id FROM service_slots WHERE service_id=?', (r.json['id'],))[0]['id']
        b = self.book(self.diver3, [{'items': [{'code': 'mask'}]}], r.json['id'], slot)
        self.assertEqual(b.status, 400); self.assertIn('incluido en el precio', b.json['error'])

    # 2 · prices
    def test_2_mask_and_fins_is_60(self):
        q = self.diver.get(f'/api/booking-quote?center_id={self.cid}&service_id={self.sid}&slot_id={self.slot}&participants=1'
                           '&equipment_sel=' + '[{"items":[{"code":"mask"},{"code":"fins","size":"39"}]}]').json
        self.assertEqual(q['total'], 60.0, q)
        self.assertEqual([(l['label'], l['total']) for l in q['lines']], [('Inmersión simple', 50.0), ('Máscara', 5.0), ('Aletas', 5.0)])
        self.assertEqual(q['equipment']['included'], 'Incluido: botella y plomos')
        r = self.book(self.diver, [{'items': [{'code': 'mask'}, {'code': 'fins'}]}])
        self.assertEqual(r.status, 400); self.assertIn('Elige la talla de aletas', r.json['error'])
        r = self.book(self.diver, [{'items': [{'code': 'mask'}, {'code': 'fins', 'size': '39'}]}])
        self.assertEqual(r.status, 200, r); self.assertEqual(r.json['status'], 'payment_in_progress')
        self.assertEqual(self.stripe.last_session()['amount_total'], 6000, 'the equipment is charged with the dive')
        b = self.bk(r.json['id'])
        self.assertEqual(b['price'], 60.0)
        self.assertEqual(b['equipment_items'].split(' · ', 1)[1], 'Máscara · Aletas 39')
        rows = self.server.sql('SELECT code,size,unit_price,total FROM booking_equipment WHERE booking_id=? ORDER BY id', (r.json['id'],))
        self.assertEqual([(x['code'], x['size'], x['total']) for x in rows], [('mask', None, 5.0), ('fins', '39', 5.0)])

    def test_3_two_divers(self):
        r = self.book(self.diver2, [{'items': [{'code': 'wetsuit', 'size': 'M', 'thick': '5'}, {'code': 'mask'}, {'code': 'fins', 'size': '42'}, {'code': 'boots', 'size': '42'}]},
                                    {'items': [{'code': 'smb'}]}])
        self.assertEqual(r.status, 200, r)
        b = self.bk(r.json['id'])
        self.assertEqual(b['price'], 2 * 50 + 10 + 5 + 5 + 3 + 2)
        self.assertIn('Traje M 5 mm · Máscara · Aletas 42 · Escarpines 42', b['equipment_items'])
        self.assertIn('| Buceador 2 · Boya', b['equipment_items'])
        self.pay_last('dos')
        man = self.center.get(f'/api/manifest/{self.slot}').json
        rentals = {(d['booking_id'], d['seat']): d['rental'] for d in man['divers']}
        self.assertEqual(rentals[(r.json['id'], 1)], ['Traje M 5 mm', 'Máscara', 'Aletas 42', 'Escarpines 42'])
        self.assertEqual(rentals[(r.json['id'], 2)], ['Boya'])
        prep = self.center.get(f'/api/provider/equipment/prep?date={DAY}').json
        self.assertIn('Boyas: 1', prep['day']['text']); self.assertIn('Aletas: ', prep['day']['text'])
        pdf = self.center.get(f'/api/provider/equipment/prep.pdf?date={DAY}')
        self.assertEqual(pdf.status, 200); self.assertTrue(pdf.body.startswith(b'%PDF'))
        csv_ = self.center.get('/api/exportar/reservas?formato=csv&periodo=todo')
        self.assertEqual(csv_.status, 200)
        text = csv_.body.decode('utf-8-sig')
        head = next(csv.reader(io.StringIO(text), delimiter=';'))
        self.assertIn('Equipo de alquiler', head); self.assertIn('Escarpines 42', text)
        api = self.center.get(f"/api/bookings/{r.json['id']}/equipment").json
        self.assertEqual(len(api['rows']), 5)

    def test_4_full_kit(self):
        kit = [{'code': 'mask'}, {'code': 'fins', 'size': '40'}, {'code': 'boots', 'size': '40'}, {'code': 'wetsuit', 'size': 'L', 'thick': '7'},
               {'code': 'bcd', 'size': 'L'}, {'code': 'regulator'}]
        q = self.diver3.get(f'/api/booking-quote?center_id={self.cid}&service_id={self.sid}&slot_id={self.slot}&participants=1&equipment_sel='
                            + quote(json.dumps([{'items': kit, 'kit': True}]))).json
        self.assertEqual(q['total'], 80.0, q)
        self.assertEqual([l['label'] for l in q['lines']], ['Inmersión simple', 'Equipo completo'])
        q = self.diver3.get(f'/api/booking-quote?center_id={self.cid}&service_id={self.sid}&slot_id={self.slot}&participants=1&equipment_sel='
                            + quote(json.dumps([{'items': kit[1:], 'kit': True}]))).json
        self.assertEqual(q['equipment']['kit_broken'], [0]); self.assertEqual(q['total'], 50 + 5 + 3 + 10 + 8 + 8)
        r = self.book(self.diver3, [{'items': kit, 'kit': True}])
        self.assertEqual(r.status, 200, r); self.assertEqual(self.bk(r.json['id'])['price'], 80.0)

    # 5 · stock
    def test_5_stock_of_a_size(self):
        r = self.book(self.diver, [{'items': [{'code': 'bcd', 'size': 'M'}]}, {'items': [{'code': 'bcd', 'size': 'M'}]}], sid=self.rsid, slot=self.rslot)
        self.assertEqual(r.status, 200, r)
        q = self.diver2.get(f'/api/booking-quote?center_id={self.cid}&service_id={self.rsid}&slot_id={self.rslot}&participants=1').json
        self.assertEqual(q['equipment']['stock'], {'bcd': {'M': 0}})
        r2 = self.book(self.diver2, [{'items': [{'code': 'bcd', 'size': 'M'}]}], sid=self.rsid, slot=self.rslot)
        self.assertEqual(r2.status, 400, r2); self.assertEqual(r2.json['code'], 'no_spots'); self.assertIn('talla M', r2.json['error'])
        self.assertEqual(self.book(self.diver2, [{'items': [{'code': 'bcd', 'size': 'L'}]}], sid=self.rsid, slot=self.rslot).status, 200, 'another size: no limit')
        # The centre rejects the first request: its jackets are free again
        self.assertEqual(self.center.post(f"/api/bookings/{r.json['id']}/status", {'status': 'rejected', 'reason': 'Lleno'}).status, 200)
        self.assertEqual(self.book(self.diver3, [{'items': [{'code': 'bcd', 'size': 'M'}]}], sid=self.rsid, slot=self.rslot).status, 200)

    # 6 · changes after booking
    def test_6_add_a_torch_and_desk(self):
        r = self.book(self.diver4, [{'items': [{'code': 'mask'}, {'code': 'fins', 'size': '41'}]}])
        self.assertEqual(r.status, 200, r); bid = r.json['id']
        self.pay_last('antorcha')
        self.assertEqual(self.bk(bid)['payment_status'], 'paid')
        st = self.diver4.get(f'/api/bookings/{bid}/equipment').json
        self.assertTrue(st['can_change'])
        c = self.diver4.post(f'/api/bookings/{bid}/equipment', {'equipment': [{'items': [{'code': 'mask'}, {'code': 'fins', 'size': '41'}, {'code': 'torch'}]}]})
        self.assertEqual(c.status, 200, c); self.assertEqual(c.json['diff'], 4.0)
        self.assertTrue(c.json['checkout_url'].startswith('https://checkout.stripe.test/'))
        self.assertEqual(self.stripe.last_session()['amount_total'], 400, 'only the difference')
        self.pay_last('dif')
        b = self.bk(bid)
        self.assertEqual((b['price'], b['amount_paid'], b['payment_status']), (64.0, 64.0, 'paid'))
        # Removing it: the difference is refunded to the card
        c = self.diver4.post(f'/api/bookings/{bid}/equipment', {'equipment': [{'items': [{'code': 'mask'}, {'code': 'fins', 'size': '41'}]}]})
        self.assertEqual(c.status, 200, c); self.assertEqual((c.json['diff'], c.json['refund']), (-4.0, 'refunded'))
        self.assertEqual(self.bk(bid)['price'], 60.0)
        # At the desk: a computer for the second… the only diver, paid at the centre
        d = self.center.post(f'/api/center/bookings/{bid}/equipment', {'code': 'regulator', 'diver': 0, 'pay': 'desk'})
        self.assertEqual(d.status, 200, d)
        b = self.bk(bid)
        self.assertEqual(b['price'], 68.0); self.assertEqual(b['amount_due'], 0.0, 'paid at the centre: nothing due')
        self.assertIn('Regulador', b['equipment_items'])
        self.assertEqual(self.server.sql("SELECT source, paid_at_desk FROM booking_equipment WHERE booking_id=? AND code='regulator'", (bid,))[0]['paid_at_desk'], 1)
        # Another centre cannot touch it
        other = self.make_center(self.admin, 'equipootro')
        self.assertEqual(other.post(f'/api/center/bookings/{bid}/equipment', {'code': 'torch', 'pay': 'desk'}).status, 404)
        self.assertEqual(self.diver2.post(f'/api/bookings/{bid}/equipment', {'equipment': []}).status, 404)
        # The sizes come back next time
        self.assertEqual(self.diver4.get(f'/api/equipment/my-sizes?center_id={self.cid}').json['sizes'].get('fins'), {'size': '41', 'thick': ''})

    # 7 · on request
    def test_7_on_request(self):
        r = self.book(self.diver5, [{'items': [{'code': 'wetsuit', 'size': 'S', 'thick': '7'}]}], sid=self.rsid, slot=self.rslot)
        self.assertEqual(r.status, 200, r); self.assertEqual(r.json['status'], 'requested')
        b = self.bk(r.json['id'])
        self.assertEqual((b['price'], b['amount_paid']), (60.0, 0.0)); self.assertIn('Traje S 7 mm', b['equipment_items'])
        mine = [x for x in self.center.get('/api/bookings').json['items'] if x['id'] == r.json['id']]
        self.assertTrue(mine and 'Traje S 7 mm' in (mine[0].get('equipment_items') or ''), 'the centre sees it before accepting')

    # 8 · the old bookings
    def test_8_old_format_still_works(self):
        r = self.diver2.post('/api/bookings', {'center_id': self.cid, 'service_id': self.rsid, 'slot_id': self.rslot, 'participants': 2, 'equipment_codes': ['fins:1', 'tank']})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.bk(r.json['id'])['price'], 2 * 50 + 5, 'the tank is never charged')
        self.server.sql("INSERT INTO bookings(user_id,center_id,service_id,slot_id,booking_date,booking_time,participants,status,price,currency,equipment_items,price_breakdown,created_at,updated_at) "
                        "VALUES(?,?,?,?,?,'10:00',1,'confirmed',58,'EUR','Traje de neopreno ×1','[{\"kind\":\"equipment\",\"label\":\"Traje de neopreno\",\"qty\":1,\"unit\":8,\"total\":8}]',datetime('now'),datetime('now'))",
                        (self.diver2.user['id'], self.cid, self.rsid, self.rslot, DAY))
        old = self.server.sql("SELECT id FROM bookings WHERE equipment_items='Traje de neopreno ×1'")[0]['id']
        man = self.center.get(f'/api/manifest/{self.rslot}').json
        self.assertIn(['Traje de neopreno'], [d['rental'] for d in man['divers'] if d['booking_id'] == old])
        prep = self.center.get(f'/api/provider/equipment/prep?date={DAY}&slot_id={self.rslot}').json
        self.assertTrue(any('Traje de neopreno' in d['text'] for dep in prep['departures'] for d in dep['divers']))


if __name__ == '__main__':
    unittest.main()
