"""v50.56 · Bloque 1, Partes F y G: reservas manuales, bloqueos de plazas sin cliente, enlace de pago e iCal.

Comprueba:
  - un bloqueo (grupo, agencia, hotel) sale del mismo inventario: ningún canal vende esas plazas; liberado, vuelven;
  - la reserva manual con «pago online con enlace»: el cliente paga con su enlace, en la cuenta del centro;
  - el calendario iCal del centro refleja al momento reservas de cualquier canal, con horas en UTC: 09:00 en Cancún
    (México) son las 14:00 UTC y 09:00 en Madrid en verano son las 07:00 UTC; los cursos de varios días son un evento
    de varios días; el instructor tiene su propio calendario;
  - importar un calendario de otro sistema bloquea las plazas de las salidas que coinciden (o los días de un
    freelance); si el evento desaparece, se liberan; nunca quita plazas ya vendidas; se repite solo cada 15 minutos.
"""
import datetime as dt
import http.server
import threading
import time
import unittest
import urllib.parse

from helpers import ServerTestCase, Client
from stripe_mock import StripeMock

FAR = '2099-12-31'
ICS = {}


class FetchStandIn:
    """WOD_MEDIA_FETCH_BASE: what «the other system» publishes at each address (only for the automatic tests)."""
    def __init__(self):
        class H(http.server.BaseHTTPRequestHandler):
            def do_GET(self):
                url = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('url', [''])[0]
                body = ICS.get(url)
                if body is None: self.send_response(404); self.end_headers(); return
                raw = body.encode(); self.send_response(200); self.send_header('Content-Type', 'text/calendar; charset=utf-8')
                self.send_header('Content-Length', str(len(raw))); self.end_headers(); self.wfile.write(raw)

            def log_message(self, *a):
                pass
        self.httpd = http.server.ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.base = f'http://127.0.0.1:{self.httpd.server_address[1]}'
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()


def day(n):
    return (dt.date.today() + dt.timedelta(days=n))


def vcal(*events):
    out = ['BEGIN:VCALENDAR', 'VERSION:2.0', 'PRODID:-//Otro sistema//ES']
    for uid, start, end, summary in events:
        out += ['BEGIN:VEVENT', f'UID:{uid}', f'DTSTART{start}', f'DTEND{end}', f'SUMMARY:{summary}', 'END:VEVENT']
    return '\r\n'.join(out + ['END:VCALENDAR']) + '\r\n'


class Ical(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock(); cls.fetch = FetchStandIn()
        cls.extra_env = dict(cls.extra_env, STRIPE_SECRET_KEY='sk_test_mock', WOD_STRIPE_API_BASE=cls.stripe.base, WOD_MEDIA_FETCH_BASE=cls.fetch.base,
                             WOD_MAINTENANCE_SECONDS='2')
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.es = t.make_center(cls.admin, 'icales'); cls.mx = t.make_center(cls.admin, 'icalmx', phone='+52 998 000 0000')
        cls.pro = t.make_freelance(cls.admin, 'icalpro')
        for c in (cls.es.user['center_id'], cls.mx.user['center_id']):
            cls.server.sql(f"UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_i{c}',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (c,))
        cls.server.sql("UPDATE centers SET country='México',city='Cancún' WHERE id=?", (cls.mx.user['center_id'],))
        cls.server.sql(f"UPDATE users SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_icalpro',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cls.pro.user['id'],))
        cls.es_sid = cls.es.post('/api/provider-services', {'title': 'Salida Madrid', 'price': 50, 'booking_mode': 'request', 'duration_minutes': 180}).json['id']
        cls.mx_sid = cls.mx.post('/api/provider-services', {'title': 'Cenote', 'price': 90, 'booking_mode': 'request', 'duration_minutes': 120}).json['id']
        cls.es_slot = cls.es.post('/api/provider-services/slot', {'service_id': cls.es_sid, 'slot_date': '2031-07-15', 'slot_time': '09:00', 'spots_total': 6}).json['slot_id']
        cls.mx_slot = cls.mx.post('/api/provider-services/slot', {'service_id': cls.mx_sid, 'slot_date': '2031-07-15', 'slot_time': '09:00', 'spots_total': 6}).json['slot_id']

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop(); cls.fetch.httpd.shutdown()

    def feed(self, client):
        r = client.get('/api/provider/ical')
        if not r.json.get('url'): client.post('/api/provider/ical/regenerate', {}); r = client.get('/api/provider/ical')
        path = '/' + r.json['url'].split('/', 3)[3]
        return Client(self.server, origin=None).get(path).body.decode()

    def free(self, slot):
        return self.server.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot,))[0]['spots_available']

    def test_bloqueo_de_plazas_sin_cliente(self):
        slot = self.es.post('/api/provider-services/slot', {'service_id': self.es_sid, 'slot_date': '2031-07-20', 'slot_time': '10:00', 'spots_total': 4}).json['slot_id']
        r = self.es.post('/api/provider/spot-blocks', {'slot_id': slot, 'qty': 3, 'label': 'Hotel Sol · grupo de 3'})
        self.assertEqual(r.status, 200, r); bid = r.json['id']
        self.assertEqual(self.free(slot), 1)
        r = self.es.post('/api/provider/spot-blocks', {'slot_id': slot, 'qty': 2, 'label': 'Agencia'})
        self.assertEqual((r.status, r.json.get('code')), (400, 'no_spots'))
        r = self.es.post('/api/center/bookings/manual', {'fullname': 'Uno', 'phone': '+34 611 222 333', 'service_id': self.es_sid, 'slot_id': slot, 'participants': 2, 'status': 'confirmed'})
        self.assertEqual(r.json.get('code'), 'no_spots')
        self.assertEqual(self.mx.post('/api/provider/spot-blocks', {'action': 'release', 'id': bid}).status, 404)   # another centre
        self.assertEqual(self.mx.post('/api/provider/spot-blocks', {'slot_id': slot, 'qty': 1}).status, 404)
        items = self.es.get(f'/api/provider/spot-blocks?slot={slot}').json['items']
        self.assertEqual([(i['qty'], i['label']) for i in items], [(3, 'Hotel Sol · grupo de 3')])
        self.assertIn('plazas bloqueadas: 3', self.feed(self.es))
        self.assertEqual(self.es.post('/api/provider/spot-blocks', {'action': 'release', 'id': bid}).status, 200)
        self.assertEqual(self.free(slot), 4)

    def test_reserva_manual_con_enlace_de_pago(self):
        sid = self.es.post('/api/provider-services', {'title': 'Curso con pago', 'price': 120, 'booking_mode': 'payment'}).json['id']
        slot = self.es.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-07-21', 'slot_time': '10:00', 'spots_total': 4}).json['slot_id']
        r = self.es.post('/api/center/bookings/manual', {'fullname': 'Pagará online', 'email': 'paga.online@example.org', 'service_id': sid, 'slot_id': slot,
                                                         'participants': 1, 'status': 'confirmed', 'payment_status': 'link'})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(r.json['status'], 'accepted_pending_payment'); self.assertIn('/mi-reserva/', r.json['pay_url']); self.assertTrue(r.json['pay_url'].endswith('?pagar=1'))
        self.assertEqual(self.free(slot), 3)                                                    # the spot is kept while he pays
        tok = r.json['pay_url'].split('/mi-reserva/')[1].split('?')[0]
        pay = Client(self.server).post(f'/api/mi-reserva/{tok}/pagar', {})
        self.assertEqual(pay.status, 200, pay)
        call = [c for c in self.stripe.calls if c['path'] == '/v1/checkout/sessions' and c['method'] == 'POST'][-1]
        self.assertEqual(call['account'], f"acct_i{self.es.user['center_id']}")
        self.stripe.pay(self.stripe.last_session()['id'])
        Client(self.server, origin=None).get(f'/mi-reserva/{tok}?pago=ok')
        self.assertEqual(self.server.sql('SELECT status, payment_status FROM bookings WHERE id=?', (int(tok.split('.')[0]),))[0], {'status': 'confirmed', 'payment_status': 'paid'})

    def test_ical_horas_locales_mexico_y_espana(self):
        a = self.es.post('/api/center/bookings/manual', {'fullname': 'Lucía Madrid', 'phone': '+34 611 000 111', 'service_id': self.es_sid, 'slot_id': self.es_slot, 'participants': 2, 'status': 'confirmed'})
        b = self.mx.post('/api/center/bookings/manual', {'fullname': 'Diego Cancún', 'phone': '+52 998 111 2222', 'service_id': self.mx_sid, 'slot_id': self.mx_slot, 'participants': 1, 'status': 'confirmed'})
        es, mx = self.feed(self.es), self.feed(self.mx)
        self.assertIn(f"UID:wod-booking-{a.json['id']}@", es); self.assertIn('DTSTART:20310715T070000Z', es); self.assertIn('DTEND:20310715T100000Z', es)
        self.assertIn(f"UID:wod-booking-{b.json['id']}@", mx); self.assertIn('DTSTART:20310715T140000Z', mx)
        self.assertNotIn('Diego', es); self.assertNotIn('Lucía', mx)                            # each centre, its own calendar
        self.assertIn('X-WR-TIMEZONE:America/Cancun', mx); self.assertIn('Manual', mx)
        self.assertTrue(all(len(line.encode()) <= 75 for line in es.split('\r\n')))
        # A booking from another channel appears at once
        c = Client(self.server).post(f"/api/w/{self.es.get('/api/provider/vender').json['slug']}/reservar",
                                     {'service_id': self.es_sid, 'slot_id': self.es_slot, 'participants': 1, 'fullname': 'Web Ana', 'email': 'web.ana@example.org', 'accept_policy': True, 'canal': 'link'})
        self.assertEqual(c.status, 200, c)
        self.assertIn(f"UID:wod-booking-{c.json['id']}@", self.feed(self.es))

    def test_ical_curso_de_varios_dias_e_instructor(self):
        rules = {'min_days': 1, 'max_days': 10, 'lead_hours': 0, 'am': ['08:00', '13:00'], 'pm': ['14:00', '19:00'], 'full': ['08:00', '16:00']}
        sid = self.mx.post('/api/provider-services', {'title': 'Open Water 3 días', 'price': 400, 'booking_mode': 'request', 'booking_unit': 'day', 'unit_rules': rules,
                                                      'pricing': {'day': 400}, 'instructor_user_id': self.mx.user['id']}).json['id']
        r = self.mx.post('/api/center/bookings/manual', {'fullname': 'Alumno MX', 'phone': '+52 998 333 4444', 'service_id': sid, 'days': ['2031-09-01', '2031-09-02', '2031-09-03'],
                                                         'part': 'full', 'participants': 1, 'status': 'confirmed'})
        self.assertEqual(r.status, 200, r)
        mx = self.feed(self.mx)
        self.assertIn('DTSTART;VALUE=DATE:20310901', mx); self.assertIn('DTEND;VALUE=DATE:20310904', mx)
        me = self.mx.get('/api/me/ical').json['url']
        inst = Client(self.server, origin=None).get('/' + me.split('/', 3)[3]).body.decode()
        self.assertIn('Open Water 3 días', inst); self.assertNotIn('Cenote', inst)

    def test_importar_calendario_bloquea_y_libera(self):
        d = day(40); ds = d.strftime('%Y%m%d')
        slot = self.es.post('/api/provider-services/slot', {'service_id': self.es_sid, 'slot_date': d.isoformat(), 'slot_time': '09:00', 'spots_total': 5}).json['slot_id']
        url = 'https://otro-sistema.example.com/cal/centro.ics'
        ICS[url] = vcal(('ev-1', f';TZID=Europe/Madrid:{ds}T080000', f';TZID=Europe/Madrid:{ds}T130000', 'Grupo de un touroperador'))
        self.es.post('/api/center/bookings/manual', {'fullname': 'Ya vendida', 'phone': '+34 611 999 000', 'service_id': self.es_sid, 'slot_id': slot, 'participants': 1, 'status': 'confirmed'})
        r = self.es.post('/api/provider/ical-imports', {'action': 'create', 'name': 'Touroperador', 'url': url.replace('https://', 'webcal://'), 'service_id': self.es_sid})
        self.assertEqual(r.status, 200, r); iid = r.json['id']
        self.assertEqual((r.json['sync']['events'], r.json['sync']['added']), (1, 1), r.json)
        self.assertEqual(self.free(slot), 0)
        self.assertEqual(self.server.sql("SELECT COUNT(*) n FROM bookings WHERE slot_id=? AND status='confirmed'", (slot,))[0]['n'], 1)   # the sold spot stays sold
        self.assertIn('no es instantánea', self.es.get('/api/provider/ical-imports').json['note'])
        # The event is gone from the other system: the spots come back on the next read
        ICS[url] = vcal()
        self.assertEqual(self.es.post('/api/provider/ical-imports', {'action': 'sync', 'id': iid}).json['events'], 0)
        self.assertEqual(self.free(slot), 4)
        # Every 15 minutes by itself (maintenance)
        ICS[url] = vcal(('ev-2', f';TZID=Europe/Madrid:{ds}T083000', f';TZID=Europe/Madrid:{ds}T093000', 'Otro grupo'))
        self.server.sql("UPDATE ical_imports SET last_sync_at='2000-01-01T00:00:00+00:00' WHERE id=?", (iid,))
        for _ in range(60):
            if self.free(slot) == 0: break
            time.sleep(0.2)
        self.assertEqual(self.free(slot), 0)
        self.assertEqual(self.mx.post('/api/provider/ical-imports', {'action': 'delete', 'id': iid}).status, 404)
        self.assertEqual(self.es.post('/api/provider/ical-imports', {'action': 'delete', 'id': iid}).status, 200)
        self.assertEqual(self.free(slot), 4)
        self.assertEqual(self.es.post('/api/provider/ical-imports', {'action': 'create', 'url': 'http://inseguro.example.com/a.ics', 'service_id': self.es_sid}).status, 400)

    def test_importar_dias_de_un_freelance(self):
        rules = {'min_days': 1, 'max_days': 10, 'lead_hours': 0, 'am': ['08:00', '13:00'], 'pm': ['14:00', '19:00'], 'full': ['08:00', '16:00']}
        sid = self.pro.post('/api/provider-services', {'title': 'Guía por días', 'price': 100, 'booking_mode': 'request', 'booking_unit': 'day', 'unit_rules': rules, 'pricing': {'day': 100}}).json['id']
        url = 'https://calendario.example.org/pro.ics'
        a = day(50)
        ICS[url] = vcal(('vac-1', f";VALUE=DATE:{a.strftime('%Y%m%d')}", f";VALUE=DATE:{(a + dt.timedelta(days=3)).strftime('%Y%m%d')}", 'Vacaciones'))
        r = self.pro.post('/api/provider/ical-imports', {'action': 'create', 'name': 'Mi calendario', 'url': url})
        self.assertEqual(r.status, 200, r)
        want = [(a + dt.timedelta(days=i)).isoformat() for i in range(-1, 4)]
        states = {}
        for m in sorted({x[:7] for x in want}):
            states.update(Client(self.server).get(f'/api/agenda/public?service={sid}&month={m}').json['days'])
        self.assertEqual([states[x] for x in want], ['free', 'busy', 'busy', 'busy', 'free'])
        d = Client(self.server).get(f'/api/agenda/public?service={sid}&month={a.isoformat()[:7]}').json
        self.assertNotIn('Vacaciones', str(d))                                                 # the public calendar shows no names or reasons
        diver = self.make_diver('icaldiver')
        r = diver.post('/api/bookings', {'service_id': sid, 'days': [(a + dt.timedelta(days=1)).isoformat()], 'part': 'full', 'participants': 1})
        self.assertEqual(r.json.get('code'), 'no_spots', r)


class IcalPuro(unittest.TestCase):
    def test_parser(self):
        import sys
        from pathlib import Path
        sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
        from wod import ical as wical
        text = vcal(('a', ':20311010T090000Z', ':20311010T100000Z', 'UTC'), ('b', ';TZID=America/Cancun:20311011T090000', ';TZID=America/Cancun:20311011T110000', 'Con zona'),
                    ('c', ':20311012T090000', ':20311012T100000', 'Flotante'), ('d', ';VALUE=DATE:20311013', ';VALUE=DATE:20311015', 'Día entero'),
                    ('e', ':20200101T090000Z', ':20200101T100000Z', 'Pasado')).replace('SUMMARY:Con zona', 'SUMMARY:Con zona\r\nSTATUS:CONFIRMED')
        text = text.replace('BEGIN:VEVENT\r\nUID:a', 'BEGIN:VEVENT\r\nUID:x\r\nDTSTART:20311020T090000Z\r\nSTATUS:CANCELLED\r\nEND:VEVENT\r\nBEGIN:VEVENT\r\nUID:a')
        ev = {e['uid']: e for e in wical.parse(text, 'Europe/Madrid', dt.date(2031, 10, 1))}
        self.assertEqual(set(ev), {'a', 'b', 'c', 'd'})
        self.assertEqual(ev['b']['start'], '2031-10-11T14:00:00Z')
        self.assertEqual(ev['c']['start'], '2031-10-12T07:00:00Z')                             # floating time: the centre's zone (Madrid, summer time)
        self.assertEqual((ev['d']['all_day'], ev['d']['local_from'], ev['d']['local_to']), (True, '2031-10-13', '2031-10-14'))
        folded = wical.fold(['DESCRIPTION:' + 'ñ' * 80])
        self.assertTrue(all(len(x.encode()) <= 75 for x in folded.split('\r\n')))
        self.assertEqual(wical.parse(folded.replace('DESCRIPTION', 'X'), 'Europe/Madrid'), [])
