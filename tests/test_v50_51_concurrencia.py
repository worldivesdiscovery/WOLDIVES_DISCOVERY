"""v50.51 · Integridad de las reservas con peticiones simultáneas.

Muchas personas reservan a la vez la misma salida con pocas plazas, la misma persona pulsa dos veces «Reservar», el
centro pulsa dos veces «Aceptar» y la página de pago pregunta a la vez que otra pestaña. Se comprueba siempre:
  - nunca hay más participantes con plaza que spots_total;
  - spots_available = spots_total - participantes de las reservas que tienen la plaza tomada (slot_reserved=1);
  - un doble envío no crea dos reservas, no toma dos veces las plazas y no cuenta dos veces un pago;
  - ningún error interno (500) ni bloqueo de SQLite.
Stripe es el simulador local (tests/stripe_mock.py). La segunda clase repite todo con WOD_WORKERS=4 (varios procesos
sirviendo el mismo puerto, como en producción).
"""
import os
import signal
import socket
import threading
import time
import unittest

from helpers import ServerTestCase
from stripe_mock import StripeMock

LIVE = ('requested', 'pending', 'payment_in_progress', 'accepted_pending_payment', 'confirmed', 'completed')


def at_once(calls):
    """Ejecuta las funciones a la vez (todas salen de una barrera) y devuelve sus resultados en orden."""
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


class Concurrencia(ServerTestCase):
    N_DIVERS = 24
    tag = 'c1'

    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = dict(cls.extra_env, STRIPE_SECRET_KEY='sk_test_mock', WOD_STRIPE_API_BASE=cls.stripe.base)
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, f'conc{cls.tag}', phone='+34 600 000 051')
        cls.cid = cls.center.user['center_id']
        cls.server.sql("UPDATE centers SET stripe_account_id='acct_concurrencia',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.cid,))
        cls.divers = [t.make_diver(f'{cls.tag}buzo{i:02d}') for i in range(cls.N_DIVERS)]
        cls.day = 0

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        cls.stripe.stop()

    # ------------------------------------------------------------------ ayudas
    def service_slot(self, mode, spots, price=40, max_participants=10):
        r = self.center.post('/api/provider-services', {'title': f'Concurrencia {mode} {time.time_ns()}', 'price': price, 'booking_mode': mode,
                                                         'max_participants': max_participants})
        self.assertEqual(r.status, 200, r)
        sid = r.json['id']
        type(self).day += 1
        r = self.center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': f'2031-06-{type(self).day:02d}', 'slot_time': '10:00', 'spots_total': spots})
        self.assertEqual(r.status, 200, r)
        return sid, r.json['slot_id']

    def book(self, diver, sid, slot, pax=1):
        return diver.post('/api/bookings', {'center_id': self.cid, 'service_id': sid, 'slot_id': slot, 'participants': pax})

    def slot_row(self, slot):
        return self.server.sql('SELECT spots_total, spots_available, status FROM service_slots WHERE id=?', (slot,))[0]

    def assert_slot_consistent(self, slot):
        """La invariante de las plazas de una salida."""
        s = self.slot_row(slot)
        held = self.server.sql('SELECT COALESCE(SUM(participants),0) n FROM bookings WHERE slot_id=? AND slot_reserved=1', (slot,))[0]['n']
        confirmed = self.server.sql("SELECT COALESCE(SUM(participants),0) n FROM bookings WHERE slot_id=? AND status IN ('confirmed','completed')", (slot,))[0]['n']
        self.assertGreaterEqual(s['spots_available'], 0, s)
        self.assertLessEqual(held, s['spots_total'], f'más participantes con plaza ({held}) que plazas ({s["spots_total"]})')
        self.assertLessEqual(confirmed, s['spots_total'], f'más participantes confirmados ({confirmed}) que plazas ({s["spots_total"]})')
        self.assertEqual(s['spots_available'], s['spots_total'] - held,
                         f'spots_available={s["spots_available"]} no cuadra: {s["spots_total"]} plazas y {held} tomadas por reservas')
        return s, held

    def assert_no_server_errors(self, results):
        for r in results:
            self.assertNotIsInstance(r, Exception, r)
            self.assertLess(r.status, 500, r)

    # ------------------------------------------------------------------ 1. muchas personas, pocas plazas
    def test_pago_al_reservar_nunca_vende_mas_plazas_que_las_que_hay(self):
        sid, slot = self.service_slot('payment', spots=5)
        pax = [1 if i % 3 else 2 for i in range(len(self.divers))]
        res = at_once([lambda d=d, p=p: self.book(d, sid, slot, p) for d, p in zip(self.divers, pax)])
        self.assert_no_server_errors(res)
        ok = [(r, p) for r, p in zip(res, pax) if r.status == 200]
        self.assertTrue(ok, 'ninguna reserva ha entrado')
        self.assertLessEqual(sum(p for _, p in ok), 5)
        for r in res:
            if r.status != 200: self.assertIn('plazas', (r.json or {}).get('error', ''), r)
        s, held = self.assert_slot_consistent(slot)
        self.assertEqual(held, sum(p for _, p in ok))

    def test_bajo_peticion_aceptaciones_simultaneas_respetan_las_plazas(self):
        sid, slot = self.service_slot('request', spots=4)
        ids = []
        for d in self.divers[:12]:
            r = self.book(d, sid, slot, 1); self.assertEqual(r.status, 200, r); ids.append(r.json['id'])
        self.assertEqual(self.slot_row(slot)['spots_available'], 4, 'una solicitud no toma plazas hasta que el centro acepta')
        res = at_once([lambda b=b: self.center.post(f'/api/bookings/{b}/status', {'status': 'confirmed'}) for b in ids])
        self.assert_no_server_errors(res)
        accepted = [r for r in res if r.status == 200]
        self.assertEqual(len(accepted), 4, [r.json for r in res])
        for r in res:
            if r.status != 200: self.assertIn('plazas', (r.json or {}).get('error', ''), r)
        s, held = self.assert_slot_consistent(slot)
        self.assertEqual(held, 4); self.assertEqual(s['spots_available'], 0)

    # ------------------------------------------------------------------ 2. doble envío
    def test_doble_envio_de_la_misma_reserva_bajo_peticion(self):
        duplicated = []
        for i in range(4):
            sid, slot = self.service_slot('request', spots=8)
            diver = self.divers[i]
            res = at_once([lambda: self.book(diver, sid, slot, 2), lambda: self.book(diver, sid, slot, 2)])
            self.assert_no_server_errors(res)
            n = self.server.sql(f"SELECT COUNT(*) n FROM bookings WHERE slot_id=? AND user_id=? AND status IN {LIVE}", (slot, diver.user['id']))[0]['n']
            if n != 1: duplicated.append((slot, n))
            self.assert_slot_consistent(slot)
        self.assertEqual(duplicated, [], f'el doble clic en «Reservar» ha creado reservas repetidas (salida, reservas): {duplicated}')

    def test_doble_envio_de_la_misma_reserva_con_pago(self):
        duplicated = []
        for i in range(4):
            sid, slot = self.service_slot('payment', spots=8)
            diver = self.divers[4 + i]
            res = at_once([lambda: self.book(diver, sid, slot, 2), lambda: self.book(diver, sid, slot, 2)])
            self.assert_no_server_errors(res)
            n = self.server.sql(f"SELECT COUNT(*) n FROM bookings WHERE slot_id=? AND user_id=? AND status IN {LIVE}", (slot, diver.user['id']))[0]['n']
            s, held = self.assert_slot_consistent(slot)
            if n != 1 or held != 2: duplicated.append((slot, n, held))
        self.assertEqual(duplicated, [], f'el doble clic en «Reservar y pagar» ha creado reservas repetidas (salida, reservas, plazas tomadas): {duplicated}')

    def test_doble_aceptacion_de_la_misma_solicitud(self):
        problems = []
        for i in range(4):
            sid, slot = self.service_slot('request', spots=6)
            r = self.book(self.divers[8 + i], sid, slot, 2); self.assertEqual(r.status, 200, r); bid = r.json['id']
            res = at_once([lambda: self.center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'}),
                           lambda: self.center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'})])
            self.assert_no_server_errors(res)
            s = self.slot_row(slot)
            notices = self.server.sql("SELECT COUNT(*) n FROM audit_log WHERE action='booking_status_changed' AND entity_id=?", (bid,))[0]['n']
            if s['spots_available'] != 4 or notices != 1: problems.append({'reserva': bid, 'plazas_libres': s['spots_available'], 'esperado': 4, 'cambios_de_estado': notices})
            self.assert_slot_consistent(slot)
        self.assertEqual(problems, [], f'«Aceptar» pulsado dos veces toma las plazas dos veces: {problems}')

    # ------------------------------------------------------------------ 3. el pago se confirma una sola vez
    def test_confirmacion_simultanea_del_pago_no_cuenta_dos_veces(self):
        problems = []
        for i in range(3):
            sid, slot = self.service_slot('payment', spots=8, price=45)
            diver = self.divers[12 + i]
            r = self.book(diver, sid, slot, 1); self.assertEqual(r.status, 200, r)
            bid = r.json['id']; sess = self.stripe.last_session(); self.stripe.pay(sess['id'])
            # La página #/pago-ok pregunta mientras otra pestaña (o la app) también lo hace.
            res = at_once([lambda: diver.get(f'/api/payments/session/{sess["id"]}') for _ in range(4)])
            self.assert_no_server_errors(res)
            b = self.server.sql('SELECT status, payment_status, amount_paid, price FROM bookings WHERE id=?', (bid,))[0]
            done = self.server.sql("SELECT COUNT(*) n FROM audit_log WHERE action='payment_completed' AND entity_id=(SELECT id FROM payment_orders WHERE booking_id=?)", (bid,))[0]['n']
            msgs = self.server.sql("SELECT COUNT(*) n FROM messages WHERE booking_id=? AND subject LIKE 'Pago recibido%'", (bid,))[0]['n']
            if b['status'] != 'confirmed' or abs(float(b['amount_paid']) - float(b['price'])) > 0.001 or done != 1 or msgs != 1:
                problems.append({'reserva': bid, 'estado': b['status'], 'pagado': b['amount_paid'], 'precio': b['price'], 'pagos_completados': done, 'avisos': msgs})
            self.assert_slot_consistent(slot)
        self.assertEqual(problems, [], f'el mismo pago se ha contado varias veces: {problems}')

    def test_sin_bloqueos_ni_errores_internos(self):
        # Al final de la clase (orden alfabético: «test_s…» va después del resto): nada de «database is locked» ni 500.
        err = (self.server.tmp / 'stderr.log').read_text() if (self.server.tmp / 'stderr.log').exists() else ''
        self.assertNotIn('database is locked', err)
        self.assertEqual([l for l in err.splitlines() if ' -> ' in l and l.startswith('[')], [])


def child_pids(pid):
    """Procesos hijos (los workers que crea WOD_WORKERS con fork), leídos de /proc."""
    out = []
    for d in os.listdir('/proc'):
        if not d.isdigit(): continue
        try:
            with open(f'/proc/{d}/stat') as f: stat = f.read()
            if int(stat.rsplit(')', 1)[1].split()[1]) == pid: out.append(int(d))
        except (OSError, ValueError, IndexError):
            pass
    return out


@unittest.skipUnless(hasattr(os, 'fork') and hasattr(socket, 'SO_REUSEPORT') and os.path.isdir('/proc'), 'WOD_WORKERS necesita Linux')
class ConcurrenciaVariosProcesos(Concurrencia):
    """Lo mismo con WOD_WORKERS=4: cuatro procesos atienden el mismo puerto (SO_REUSEPORT) sobre la misma base."""
    extra_env = {'WOD_WORKERS': '4'}
    N_DIVERS = 16
    tag = 'c4'

    @classmethod
    def tearDownClass(cls):
        # helpers.Server.stop() solo para el proceso principal: los workers se paran aquí.
        kids = child_pids(cls.server.proc.pid) if cls.server.proc else []
        for k in kids:
            try: os.kill(k, signal.SIGTERM)
            except ProcessLookupError: pass
        super().tearDownClass()
        for k in kids:
            for _ in range(50):
                try: os.kill(k, 0); time.sleep(0.1)
                except ProcessLookupError: break


if __name__ == '__main__':
    unittest.main()
