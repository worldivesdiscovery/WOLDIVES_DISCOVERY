"""v50.56 · Motor de reservas multicanal (Bloque 1, Parte B): una sola función de reserva y un solo inventario.

Se comprueba:
  - en el código, solo create_booking inserta reservas y solo reserve/release_slot_spots tocan las plazas de una salida
    (más la edición de la capacidad de la salida por el propio centro, que recalcula desde las reservas);
  - 20 reservas a la vez por varios canales a 3 plazas: exactamente 3 con plaza y 17 «Sin plazas» con el mismo código;
  - lo mismo con los días de un freelance y con el instructor de un curso de 3 días (dos cursos, mismo instructor);
  - la misma petición 5 veces (misma clave de idempotencia) da 1 reserva y 1 cobro;
  - la retención mientras se paga (10 minutos por defecto): la plaza no está libre para nadie; al caducar, vuelve;
  - cancelar desde el panel libera la plaza al momento para todos los canales;
  - el precio lo pone siempre el servidor (la API de integración ya no puede mandar 1 €);
  - una fecha y hora de una salida, sin indicar la salida, descuenta de esa salida (fallo F1);
  - cada reserva guarda su canal, y el registro de cambios del proveedor (panel en vivo y webhooks) lo apunta.
"""
import datetime as dt
import re
import threading
import time
import unittest
import uuid
from pathlib import Path

from helpers import ServerTestCase
from stripe_mock import StripeMock

ROOT = Path(__file__).resolve().parents[1]
FAR = '2099-12-31'


def at_once(calls):
    barrier = threading.Barrier(len(calls))
    out = [None] * len(calls)

    def run(i, fn):
        try:
            barrier.wait(10)
            out[i] = fn()
        except Exception as e:  # el error se ve en el resultado
            out[i] = e
    th = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
    for t in th: t.start()
    for t in th: t.join(120)
    return out


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


def no_spots(r):
    return r.status in (400, 409) and (r.json or {}).get('code') == 'no_spots' and str((r.json or {}).get('error', '')).startswith('Sin plazas')


class Estatico(unittest.TestCase):
    def test_solo_create_booking_inserta_reservas(self):
        hits = []
        for f in sorted((ROOT / 'app').rglob('*.py')):
            src = f.read_text(encoding='utf-8')
            for m in re.finditer(r'INSERT\s+(?:OR\s+\w+\s+)?INTO\s+bookings\s*\(', src):
                line = src.count('\n', 0, m.start()) + 1
                fn = re.findall(r'^def (\w+)\(', src[:m.start()], re.M)
                hits.append((f.name, line, fn[-1] if fn else None))
        self.assertEqual(len(hits), 1, f'Solo create_booking puede insertar reservas: {hits}')
        self.assertEqual((hits[0][0], hits[0][2]), ('server.py', 'create_booking'), hits)

    def test_solo_reserve_y_release_tocan_las_plazas(self):
        src = (ROOT / 'app' / 'server.py').read_text(encoding='utf-8')
        allowed_edits = ('UPDATE service_slots SET spots_total=?,spots_available', 'UPDATE service_slots SET slot_date=?,slot_time=?,spots_total=?,spots_available')
        for m in re.finditer(r"UPDATE service_slots SET[^'\"]*spots_available", src):
            fn = re.findall(r'^def (\w+)\(', src[:m.start()], re.M)[-1]
            stmt = src[m.start():m.end()]
            if fn in ('reserve_slot_spots', 'release_slot_spots'): continue
            # The centre edits the capacity of its own departure: recalculated from the spots taken, never more than total.
            self.assertTrue(stmt.startswith(allowed_edits), f'{fn}: {stmt}')

    def test_la_web_manda_su_clave_de_idempotencia(self):
        # Every attempt carries its key: the two booking pages of WORLDIVES (by departure and by days) and the manual one
        js = (ROOT / 'public' / 'js' / 'world-dives-v8.js').read_text(encoding='utf-8')
        calls = [m.start() for m in re.finditer(r"postJSON\('/api/bookings',", js)]
        self.assertEqual(len(calls), 2)
        for i in calls:
            self.assertRegex(js[i:i + 1500], r"idempotency_key:`\$\{(bkKey|dayKey)\}-[^`,]*`")
        self.assertIn('payload.idempotency_key=mbKey', js)

    def test_canales(self):
        import sys
        sys.path.insert(0, str(ROOT / 'app'))
        from wod import canales as wch
        self.assertEqual(wch.channel_of({'channel': None, 'source': 'web'}), 'import')
        self.assertEqual(wch.channel_of({'channel': 'widget', 'source': 'online'}), 'widget')
        self.assertEqual(wch.channel_of({'source': 'online'}), 'worldives')
        self.assertIsNone(wch.clean_idem_key('corta'))
        self.assertEqual(wch.clean_idem_key('a1b2c3d4-e5'), 'a1b2c3d4-e5')
        self.assertNotEqual(wch.idem_hash('u:1', 'clave-123456'), wch.idem_hash('u:2', 'clave-123456'))
        self.assertEqual(wch.clean_domain('https://www.BuceoMarAzul.com/reservas?x=1'), 'www.buceomarazul.com')
        self.assertIsNone(wch.clean_domain('http://127.0.0.1:8000'))
        self.assertIsNone(wch.clean_domain('localhost'))
        self.assertTrue(wch.host_allowed('www.marazul.com', ['marazul.com']))
        self.assertFalse(wch.host_allowed('marazul.com.evil.net', ['marazul.com']))
        self.assertTrue(wch.host_allowed('reservas.marazul.com', ['*.marazul.com']))
        self.assertFalse(wch.host_allowed('marazul.com', ['*.marazul.com']))
        self.assertEqual(wch.frame_ancestors([]), "'none'")
        body = b'{"type":"booking.created"}'
        sig = wch.sign('whsk_secreto', body, 1_800_000_000)
        self.assertTrue(wch.verify('whsk_secreto', sig, body, now=1_800_000_100))
        self.assertFalse(wch.verify('whsk_secreto', sig, body, now=1_800_000_400))      # más de 5 minutos: repetición
        self.assertFalse(wch.verify('otro', sig, body, now=1_800_000_100))
        self.assertFalse(wch.verify('whsk_secreto', sig, body + b' ', now=1_800_000_100))
        self.assertFalse(wch.webhook_url_ok('http://centro.example.com/hook'))
        self.assertFalse(wch.webhook_url_ok('https://10.0.0.1/hook'))
        self.assertTrue(wch.webhook_url_ok('https://centro.example.com/hook'))
        self.assertEqual([wch.retry_delay(i) for i in range(1, 8)], [60, 300, 1800, 7200, 21600, 86400, None])


class Multicanal(ServerTestCase):
    N_DIVERS = 14
    workers = 1

    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = dict(cls.extra_env, STRIPE_SECRET_KEY='sk_test_mock', WOD_STRIPE_API_BASE=cls.stripe.base, WOD_MAINTENANCE_SECONDS='2')
        if cls.workers > 1: cls.extra_env['WOD_WORKERS'] = str(cls.workers)
        super().setUpClass()
        t = cls('run')
        tag = f'mc{cls.workers}'
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, tag, phone='+34 600 000 156')
        cls.cid = cls.center.user['center_id']
        cls.server.sql(f"UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_{tag}',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.cid,))
        cls.key = cls.center.post('/api/center/integration/regenerate', {}).json.get('api_key')
        cls.pro = t.make_freelance(cls.admin, f'{tag}pro')
        cls.server.sql(f"UPDATE users SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_{tag}pro',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.pro.user['id'],))
        cls.divers = [t.make_diver(f'{tag}b{i:02d}') for i in range(cls.N_DIVERS)]
        cls.api = t.client()
        cls.n = 0

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    # ------------------------------------------------------------------ ayudas
    def service(self, mode='payment', price=60, **extra):
        type(self).n += 1
        r = self.center.post('/api/provider-services', {'title': f'Doble inmersión {self.n}', 'price': price, 'booking_mode': mode, 'max_participants': 8, **extra})
        self.assertEqual(r.status, 200, r)
        return r.json['id']

    def slot(self, sid, spots, date=None, time_='09:00'):
        type(self).n += 1
        r = self.center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': date or day(30 + self.n), 'slot_time': time_, 'spots_total': spots})
        self.assertEqual(r.status, 200, r)
        return r.json['slot_id']

    def worldives(self, diver, sid, slot, pax=1, **kw):
        return diver.post('/api/bookings', {'center_id': self.cid, 'service_id': sid, 'slot_id': slot, 'participants': pax, **kw})

    def manual(self, i, sid, slot=None, pax=1, **kw):
        return self.center.post('/api/center/bookings/manual', {'fullname': f'Cliente teléfono {i}', 'phone': f'+34 611 000 {i:03d}', 'service_id': sid, 'slot_id': slot,
                                                                 'participants': pax, 'status': 'confirmed', 'notify_client': False, **kw})

    def importa(self, i, sid, slot=None, pax=1, **kw):
        return self.api.post('/api/integrations/bookings', {'external_ref': f'web-{uuid.uuid4().hex[:8]}-{i}', 'fullname': f'Cliente web {i}', 'email': f'web{i}@example.com',
                                                           'service_id': sid, 'slot_id': slot, 'participants': pax, 'status': 'confirmed', **kw},
                             headers={'X-WORLDIVES-API-Key': self.key})

    def taken(self, slot):
        r = self.server.sql('SELECT COALESCE(SUM(participants),0) p FROM bookings WHERE slot_id=? AND slot_reserved=1', (slot,))[0]['p']
        s = self.server.sql('SELECT spots_total, spots_available FROM service_slots WHERE id=?', (slot,))[0]
        self.assertEqual(s['spots_available'], s['spots_total'] - r, 'plazas libres = total - tomadas')
        return r, s['spots_available']

    def public_free(self, sid, slot):
        for s in self.client().get(f'/api/provider-services?center_id={self.cid}').json['items']:
            if s['id'] == sid:
                for x in s.get('slots') or []:
                    if x['id'] == slot: return x['spots_available']
        return None

    # ------------------------------------------------------------------ 20 a la vez, 4 canales, 3 plazas
    def test_sobreventa_20_reservas_4_canales_3_plazas(self):
        sid = self.service(); slot = self.slot(sid, 3)
        calls = ([lambda d=d: ('worldives', self.worldives(d, sid, slot)) for d in self.divers[:8]]
                 + [lambda d=d: ('link', self.worldives(d, sid, slot, channel='link')) for d in self.divers[8:12]]
                 + [lambda i=i: ('manual', self.manual(i, sid, slot)) for i in range(4)]
                 + [lambda i=i: ('import', self.importa(i, sid, slot)) for i in range(4)])
        res = at_once(calls)
        errors = [r for r in res if isinstance(r, Exception)]
        self.assertEqual(errors, [])
        ok = [(ch, r) for ch, r in res if r.status == 200]
        full = [(ch, r) for ch, r in res if no_spots(r)]
        self.assertEqual(len(ok), 3, [(ch, r.status, r.json) for ch, r in res])
        self.assertEqual(len(full), 17, [(ch, r.status, r.json) for ch, r in res if r.status != 200 and not no_spots(r)])
        self.assertEqual(self.taken(slot), (3, 0))
        rows = self.server.sql('SELECT channel FROM bookings WHERE slot_id=? AND slot_reserved=1', (slot,))
        self.assertEqual(sorted(r['channel'] for r in rows), sorted(ch for ch, _ in ok))
        self.assertEqual(self.public_free(sid, slot), 0)

    def test_fecha_y_hora_sin_salida_descuentan_de_la_salida(self):
        """Fallo F1: antes, la reserva manual y la API sin salida confirmaban sin descontar (12 personas en 2 plazas)."""
        sid = self.service(); d = day(200); slot = self.slot(sid, 2, date=d)
        res = []
        for i in range(3):
            res.append(self.manual(100 + i, sid, booking_date=d, booking_time='09:00', pax=2))
            res.append(self.importa(100 + i, sid, booking_date=d, booking_time='09:00', pax=2))
        self.assertEqual(sum(1 for r in res if r.status == 200), 1, [(r.status, r.json) for r in res])
        self.assertEqual(sum(1 for r in res if no_spots(r)), 5)
        self.assertEqual(self.taken(slot), (2, 0))
        n = self.server.sql("SELECT COUNT(*) n FROM bookings WHERE service_id=? AND booking_date=? AND status='confirmed'", (sid, d))[0]['n']
        self.assertEqual(n, 1)

    def test_precio_siempre_del_servidor(self):
        sid = self.service(price=60); d = day(210)
        r = self.importa(1, sid, booking_date=d, booking_time='10:00', pax=2, price=1, paid=True)
        self.assertEqual(r.status, 200, r)
        b = self.server.sql('SELECT price, channel, source, payment_status FROM bookings WHERE id=?', (r.json['booking_id'],))[0]
        self.assertEqual((b['price'], b['channel'], b['source']), (120, 'import', 'web'))
        r = self.worldives(self.divers[13], sid, self.slot(sid, 5), pax=2, price=1, total=1, amount=1)
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.server.sql('SELECT price FROM bookings WHERE id=?', (r.json['id'],))[0]['price'], 120)
        r = self.manual(300, sid, booking_date=day(211), booking_time='10:00', pax=2, price=1)
        self.assertEqual(self.server.sql('SELECT price FROM bookings WHERE id=?', (r.json['id'],))[0]['price'], 120)
        r = self.manual(301, sid, booking_date=day(212), booking_time='10:00', pax=2, price_override=100)   # el centro sí ajusta su propia reserva
        self.assertEqual(self.server.sql('SELECT price FROM bookings WHERE id=?', (r.json['id'],))[0]['price'], 100)

    # ------------------------------------------------------------------ idempotencia
    def test_misma_peticion_5_veces_1_reserva_1_cobro(self):
        sid = self.service(); slot = self.slot(sid, 6); key = 'intento-' + uuid.uuid4().hex
        diver = self.divers[12]
        res = at_once([lambda: diver.post('/api/bookings', {'center_id': self.cid, 'service_id': sid, 'slot_id': slot, 'participants': 2},
                                          headers={'Idempotency-Key': key}) for _ in range(5)])
        self.assertTrue(all(not isinstance(r, Exception) and r.status == 200 for r in res), res)
        ids = {r.json['id'] for r in res}
        self.assertEqual(len(ids), 1, res)
        bid = ids.pop()
        self.assertEqual({r.json.get('checkout_url') for r in res}, {res[0].json['checkout_url']})
        self.assertEqual(self.server.sql('SELECT COUNT(*) n FROM bookings WHERE slot_id=?', (slot,))[0]['n'], 1)
        self.assertEqual(self.server.sql('SELECT COUNT(*) n FROM payment_orders WHERE booking_id=?', (bid,))[0]['n'], 1)
        self.assertEqual(self.taken(slot), (2, 4))
        # The same key from the centre (manual) five times
        key2 = 'manual-' + uuid.uuid4().hex
        res = [self.center.post('/api/center/bookings/manual', {'fullname': 'Grupo hotel', 'phone': '+34 622 111 222', 'service_id': sid, 'slot_id': slot, 'participants': 1,
                                                                 'status': 'confirmed', 'notify_client': False}, headers={'Idempotency-Key': key2}) for _ in range(5)]
        self.assertEqual({r.status for r in res}, {200})
        self.assertEqual(len({r.json['id'] for r in res}), 1)
        self.assertEqual(self.taken(slot), (3, 3))
        # Another diver with the same key is another attempt (the key is per customer)
        r = self.divers[11].post('/api/bookings', {'center_id': self.cid, 'service_id': sid, 'slot_id': slot, 'participants': 1}, headers={'Idempotency-Key': key})
        self.assertEqual(r.status, 200); self.assertNotEqual(r.json['id'], bid)

    # ------------------------------------------------------------------ retención mientras se paga
    def test_retencion_de_10_minutos_y_liberacion(self):
        sid = self.service(); slot = self.slot(sid, 1)
        r = self.worldives(self.divers[10], sid, slot)
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['status'], 'payment_in_progress')
        hold = dt.datetime.fromisoformat(r.json['hold_expires_at'])
        mins = (hold - (dt.datetime.now(hold.tzinfo) if hold.tzinfo else dt.datetime.now())).total_seconds() / 60
        self.assertTrue(9 <= mins <= 10.1, mins)
        self.assertEqual(self.public_free(sid, slot), 0)                          # el contador público ya la descuenta
        self.assertTrue(no_spots(self.worldives(self.divers[9], sid, slot)))       # nadie más la puede coger
        self.assertTrue(no_spots(self.manual(400, sid, slot)))
        # Ten minutes later (moved back in time) the maintenance frees it, for every channel
        self.server.sql("UPDATE bookings SET hold_expires_at=? WHERE id=?", ((dt.datetime.now() - dt.timedelta(minutes=1)).isoformat(timespec='minutes'), r.json['id']))
        for _ in range(60):
            if self.server.sql('SELECT status FROM bookings WHERE id=?', (r.json['id'],))[0]['status'] == 'expired': break
            time.sleep(0.5)
        self.assertEqual(self.server.sql('SELECT status FROM bookings WHERE id=?', (r.json['id'],))[0]['status'], 'expired')
        self.assertEqual(self.public_free(sid, slot), 1)
        r2 = self.importa(401, sid, slot)
        self.assertEqual(r2.status, 200, r2)
        self.assertEqual(self.taken(slot), (1, 0))
        # An expired hold never reached the provider: no «booking.created» in its feed
        feed = self.server.sql('SELECT event FROM provider_feed WHERE booking_id=?', (r.json['id'],))
        self.assertEqual(feed, [])

    # ------------------------------------------------------------------ cancelación cruzada
    def test_cancelar_desde_el_panel_libera_en_todos_los_canales(self):
        sid = self.service(mode='request'); slot = self.slot(sid, 2)
        r = self.importa(500, sid, slot, pax=2)
        self.assertEqual(r.status, 200, r)
        bid = r.json['booking_id']
        self.assertEqual(self.public_free(sid, slot), 0)
        self.assertTrue(no_spots(self.manual(501, sid, slot)))
        rc = self.center.post(f'/api/bookings/{bid}/status', {'status': 'cancelled', 'reason': 'El cliente llama para anular'})
        self.assertEqual(rc.status, 200, rc)
        self.assertEqual(self.public_free(sid, slot), 2)
        self.assertEqual(self.taken(slot), (0, 2))
        rw = self.manual(502, sid, slot, pax=2)
        self.assertEqual(rw.status, 200, rw)
        ev = [x['event'] for x in self.server.sql('SELECT event FROM provider_feed WHERE booking_id=? ORDER BY id', (bid,))]
        self.assertEqual(ev, ['booking.created', 'booking.cancelled'])

    # ------------------------------------------------------------------ canal y registro de cambios
    def test_canal_de_cada_reserva_y_registro_de_cambios(self):
        sid = self.service(); slot = self.slot(sid, 10)
        a = self.worldives(self.divers[7], sid, slot); b = self.worldives(self.divers[6], sid, slot, channel='link')
        c = self.manual(600, sid, slot); d = self.importa(600, sid, slot)
        chans = {x['id']: x['channel'] for x in self.server.sql('SELECT id, channel FROM bookings WHERE slot_id=?', (slot,))}
        self.assertEqual([chans[a.json['id']], chans[b.json['id']], chans[c.json['id']], chans[d.json['booking_id']]], ['worldives', 'link', 'manual', 'import'])
        # «Pago al reservar» while the customer pays: not yet in the provider's feed (it appears once paid)
        self.assertEqual(self.server.sql('SELECT COUNT(*) n FROM provider_feed WHERE booking_id IN (?,?)', (a.json['id'], b.json['id']))[0]['n'], 0)
        feed = self.server.sql("SELECT booking_id, event, channel FROM provider_feed WHERE provider_kind='center' AND provider_id=? AND booking_id IN (?,?)",
                               (self.cid, c.json['id'], d.json['booking_id']))
        self.assertEqual(sorted((x['event'], x['channel']) for x in feed), [('booking.created', 'import'), ('booking.created', 'manual')])


class MulticanalAgenda(ServerTestCase):
    """Los mismos 20 a la vez con días de un freelance y con el instructor de un curso de 3 días."""

    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = dict(cls.extra_env, STRIPE_SECRET_KEY='sk_test_mock', WOD_STRIPE_API_BASE=cls.stripe.base)
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.pro = t.make_freelance(cls.admin, 'mcdias')
        cls.server.sql(f"UPDATE users SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_mcdias',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.pro.user['id'],))
        cls.center = t.make_center(cls.admin, 'mccurso', phone='+34 600 000 256')
        cls.cid = cls.center.user['center_id']
        cls.server.sql(f"UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_mccurso',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.cid,))
        cls.divers = [t.make_diver(f'mcd{i:02d}') for i in range(16)]
        rules = {'min_days': 1, 'max_days': 10, 'lead_hours': 24, 'am': ['08:00', '13:00'], 'pm': ['14:00', '19:00'], 'full': ['08:00', '16:00']}
        cls.days_sid = cls.pro.post('/api/provider-services', {'title': 'Guía por días', 'price': 100, 'booking_mode': 'payment', 'booking_unit': 'day',
                                                               'timezone': 'America/Cancun', 'unit_rules': rules, 'pricing': {'day': 100}}).json['id']
        ins = cls.center.user['id']
        cls.course_a = cls.center.post('/api/provider-services', {'title': 'Open Water (3 días)', 'price': 350, 'booking_mode': 'payment', 'booking_unit': 'day',
                                                                  'timezone': 'Europe/Madrid', 'unit_rules': rules, 'pricing': {'day': 350}, 'instructor_user_id': ins}).json['id']
        cls.course_b = cls.center.post('/api/provider-services', {'title': 'Advanced (3 días)', 'price': 300, 'booking_mode': 'payment', 'booking_unit': 'day',
                                                                  'timezone': 'Europe/Madrid', 'unit_rules': rules, 'pricing': {'day': 300}, 'instructor_user_id': ins}).json['id']

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def test_servicio_guarda_el_instructor(self):
        row = self.server.sql('SELECT instructor_user_id FROM provider_services WHERE id IN (?,?)', (self.course_a, self.course_b))
        self.assertEqual({r['instructor_user_id'] for r in row}, {self.center.user['id']})
        r = self.center.post('/api/provider-services', {'title': 'Curso con instructor ajeno', 'price': 100, 'booking_unit': 'day', 'pricing': {'day': 100},
                                                        'instructor_user_id': self.pro.user['id']})
        self.assertEqual(r.status, 400, r)

    def test_dias_de_freelance_20_a_la_vez(self):
        days = [day(40), day(41)]
        calls = ([lambda d=d: self.divers[d].post('/api/bookings', {'service_id': self.days_sid, 'days': days, 'part': 'full', 'participants': 1}) for d in range(12)]
                 + [lambda d=d: self.divers[d].post('/api/bookings', {'service_id': self.days_sid, 'days': days, 'part': 'full', 'participants': 1, 'channel': 'link'}) for d in range(12, 16)]
                 + [lambda i=i: self.pro.post('/api/provider/bookings/manual', {'fullname': f'Cliente {i}', 'phone': f'+52 998 000 {i:04d}', 'service_id': self.days_sid,
                                                                               'days': days, 'part': 'full', 'participants': 1, 'status': 'confirmed', 'notify_client': False}) for i in range(4)])
        res = at_once(calls)
        self.assertEqual([r for r in res if isinstance(r, Exception)], [])
        ok = [r for r in res if r.status == 200]
        self.assertEqual(len(ok), 1, [(r.status, r.json) for r in res])
        self.assertEqual(sum(1 for r in res if no_spots(r)), 19, [(r.status, r.json) for r in res if r.status != 200 and not no_spots(r)])

    def test_instructor_en_curso_de_3_dias(self):
        days = [day(50), day(51), day(52)]
        over = [day(52), day(53), day(54)]
        calls = ([lambda d=d: self.divers[d].post('/api/bookings', {'center_id': self.cid, 'service_id': self.course_a, 'days': days, 'part': 'full', 'participants': 1}) for d in range(8)]
                 + [lambda d=d: self.divers[d].post('/api/bookings', {'center_id': self.cid, 'service_id': self.course_b, 'days': over, 'part': 'full', 'participants': 1}) for d in range(8, 16)]
                 + [lambda i=i: self.center.post('/api/center/bookings/manual', {'fullname': f'Alumno {i}', 'phone': f'+34 633 000 {i:03d}', 'service_id': (self.course_a, self.course_b)[i % 2],
                                                                                'days': (days, over)[i % 2], 'part': 'full', 'participants': 1, 'status': 'confirmed', 'notify_client': False}) for i in range(4)])
        res = at_once(calls)
        self.assertEqual([r for r in res if isinstance(r, Exception)], [])
        self.assertEqual(sum(1 for r in res if r.status == 200), 1, [(r.status, r.json) for r in res])
        self.assertEqual(sum(1 for r in res if no_spots(r)), 19, [(r.status, r.json) for r in res if r.status != 200 and not no_spots(r)])
        # Later, a course on other days with the same instructor: free
        r = self.divers[0].post('/api/bookings', {'center_id': self.cid, 'service_id': self.course_b, 'days': [day(60), day(61), day(62)], 'part': 'full', 'participants': 1})
        self.assertEqual(r.status, 200, r)


class MulticanalCuatroProcesos(Multicanal):
    """Lo mismo con 4 procesos sirviendo el mismo puerto (como en producción)."""
    workers = 4


if __name__ == '__main__':
    unittest.main()
