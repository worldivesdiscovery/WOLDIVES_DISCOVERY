#!/usr/bin/env python3
"""v50.56 · Bloque 1, Parte A: prueba real de sobreventa con los canales que existan (sin cambiar el servidor).

20 reservas a la vez a una salida con 3 plazas libres, mezclando los caminos de entrada que haya en el código:
  · WORLDIVES (buscador/mapa) y enlace directo: POST /api/bookings (el enlace abre la misma reserva de la web);
  · reserva manual del centro: POST /api/center/bookings/manual;
  · API de integración del centro: POST /api/integrations/bookings (X-WORLDIVES-API-Key).
Cuenta las plazas tomadas (reservas con slot_reserved=1) y las compara con las de la salida. Debe ser exactamente 3.

Además, dos comprobaciones de los caminos que no pasan por la salida:
  · reserva manual y por la API con fecha y hora, sin salida: ¿descuentan plazas?
  · el precio que manda la API: ¿lo acepta?

    python3 tests/carga/sobreventa_multicanal.py [--workers 4]
"""
from __future__ import annotations

import argparse
import json
import sys
import threading
import time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from helpers import Server, ServerTestCase  # noqa: E402
from stripe_mock import StripeMock  # noqa: E402


def at_once(calls):
    barrier = threading.Barrier(len(calls)); out = [None] * len(calls)

    def run(i, fn):
        try:
            barrier.wait(10); out[i] = fn()
        except Exception as e:  # noqa: BLE001 · the error is the result
            out[i] = e
    th = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
    for t in th: t.start()
    for t in th: t.join(120)
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--workers', type=int, default=1); a = ap.parse_args()
    stripe = StripeMock()
    env = {'STRIPE_SECRET_KEY': 'sk_test_mock', 'WOD_STRIPE_API_BASE': stripe.base}
    if a.workers > 1: env['WOD_WORKERS'] = str(a.workers)
    srv = Server(env).start(); ServerTestCase.server = srv
    out = {}
    try:
        t = ServerTestCase('run')
        admin = t.make_admin(); center = t.make_center(admin, 'sobreventa', phone='+34 600 000 056'); cid = center.user['center_id']
        srv.sql("UPDATE centers SET plan_code='pro',plan_status='active',stripe_account_id='acct_sobreventa',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cid,))
        key = center.post('/api/center/integration/regenerate', {}).json.get('api_key')
        divers = [t.make_diver(f'sv{i:02d}') for i in range(12)]
        sid = center.post('/api/provider-services', {'title': 'Doble inmersión', 'price': 60, 'booking_mode': 'payment', 'max_participants': 8}).json['id']
        slot = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-07-04', 'slot_time': '09:00', 'spots_total': 3}).json['slot_id']
        api = t.client()

        def worldives(d):
            return ('worldives', d.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': 1}))

        def manual(i):
            return ('manual', center.post('/api/center/bookings/manual', {'fullname': f'Cliente teléfono {i}', 'phone': f'+34 611 000 {i:03d}', 'service_id': sid, 'slot_id': slot,
                                                                         'participants': 1, 'status': 'confirmed', 'notify_client': False}))

        def integration(i):
            return ('api', api.post('/api/integrations/bookings', {'external_ref': f'web-{i}', 'fullname': f'Cliente web {i}', 'email': f'web{i}@example.com',
                                                                  'service_id': sid, 'slot_id': slot, 'participants': 1, 'status': 'confirmed'},
                                   headers={'X-WORLDIVES-API-Key': key}))
        calls = [lambda d=d: worldives(d) for d in divers[:12]] + [lambda i=i: manual(i) for i in range(4)] + [lambda i=i: integration(i) for i in range(4)]
        res = at_once(calls)
        by = {}
        for r in res:
            if isinstance(r, Exception): by.setdefault('error', []).append(repr(r)); continue
            ch, resp = r; by.setdefault(ch, []).append((resp.status, (resp.json or {}).get('error') or (resp.json or {}).get('status')))
        took = srv.sql('SELECT COUNT(*) n, COALESCE(SUM(participants),0) p FROM bookings WHERE slot_id=? AND slot_reserved=1', (slot,))[0]
        s = srv.sql('SELECT spots_total, spots_available FROM service_slots WHERE id=?', (slot,))[0]
        out['salida'] = {'plazas': s['spots_total'], 'libres_despues': s['spots_available'], 'reservas_con_plaza': took['n'], 'participantes_con_plaza': took['p']}
        out['respuestas'] = {k: {'200': sum(1 for x in v if x[0] == 200), 'otras': sorted({f'{x[0]} {x[1]}' for x in v if x[0] != 200})} for k, v in by.items()}
        # without a departure: date and time only
        slot2 = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': '2031-07-05', 'slot_time': '09:00', 'spots_total': 2}).json['slot_id']
        for i in range(3):
            center.post('/api/center/bookings/manual', {'fullname': f'Sin salida {i}', 'phone': f'+34 622 000 {i:03d}', 'service_id': sid, 'booking_date': '2031-07-05',
                                                         'booking_time': '09:00', 'participants': 2, 'status': 'confirmed', 'notify_client': False})
            api.post('/api/integrations/bookings', {'external_ref': f'sin-salida-{i}', 'fullname': f'Web sin salida {i}', 'service_id': sid, 'booking_date': '2031-07-05',
                                                   'booking_time': '09:00', 'participants': 2, 'status': 'confirmed'}, headers={'X-WORLDIVES-API-Key': key})
        n = srv.sql("SELECT COUNT(*) n, COALESCE(SUM(participants),0) p FROM bookings WHERE service_id=? AND booking_date='2031-07-05' AND status='confirmed'", (sid,))[0]
        s2 = srv.sql('SELECT spots_available FROM service_slots WHERE id=?', (slot2,))[0]
        out['sin_salida'] = {'salida_de_ese_dia_plazas': 2, 'libres_despues': s2['spots_available'], 'reservas_confirmadas_ese_dia': n['n'], 'participantes': n['p']}
        # the price sent by the API
        r = api.post('/api/integrations/bookings', {'external_ref': 'precio-1', 'fullname': 'Precio', 'service_id': sid, 'booking_date': '2031-07-06', 'booking_time': '09:00',
                                                   'participants': 2, 'price': 1}, headers={'X-WORLDIVES-API-Key': key})
        b = srv.sql('SELECT price FROM bookings WHERE id=?', ((r.json or {}).get('booking_id') or 0,))
        out['precio_api'] = {'precio_del_servicio_por_persona': 60, 'participantes': 2, 'precio_guardado': b[0]['price'] if b else None}
    finally:
        srv.stop(); stripe.stop()
    print(json.dumps(out, ensure_ascii=False, indent=2))


if __name__ == '__main__':
    main()
