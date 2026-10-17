#!/usr/bin/env python3
"""v50.57 · Revisión general 5.2: ráfagas de reservas a la MISMA salida durante la prueba de carga (sin sobreventa).

Mientras Locust mide (300 personas navegando y 20 reservas por segundo), cada --cada segundos un centro de carga abre
una salida nueva con --plazas plazas y, a la vez, le llegan 20 reservas por los caminos que existen (Bloque 1 del
encargo multicanal): 12 buceadores por la web, 4 reservas manuales del centro y 4 por la API del centro.
Después cuenta en la base las plazas tomadas: tienen que ser exactamente las de la salida, nunca más.

--modo pago (por defecto): un servicio de «pago al reservar», en el que la reserva de la web ocupa su plaza al momento
(mientras la persona paga): las 20 compiten por las mismas plazas y solo se aceptan tantas como plazas.
--modo peticion: «bajo petición», en el que la web no ocupa plaza hasta que el centro acepta (solo compiten las manuales
y las de la API; las solicitudes de la web se aceptan mientras quedan plazas libres).

Usa las últimas 60 sesiones de run/sesiones.json; la clase Reservas de locustfile.py no las usa (sus reservas sin pagar
no cuentan así para el límite de 3 pagos sin terminar por persona).

    python3 tests/carga/rafagas.py --dir /tmp/wod-carga [--cada 30] [--veces 10] [--plazas 3] [--modo pago] [--salida informe.json]

Lee run/estado.json (servidor), cuentas.json (centros) y run/sesiones.json (sesiones de buceador de `preparar.py sesiones`).
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import sqlite3
import threading
import time
import urllib.error
import urllib.request
from http.cookiejar import CookieJar
from pathlib import Path


class Web:
    """Un cliente con su sesión (cookie) y su IP (X-Forwarded-For, el servidor de carga se fía de 127.0.0.1)."""

    def __init__(self, base, ip, cookie=None):
        self.base, self.ip, self.cookie = base, ip, cookie
        self.opener = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(CookieJar()))

    def post(self, path, data, headers=None):
        h = {'Content-Type': 'application/json', 'Origin': self.base, 'X-Forwarded-For': self.ip, **(headers or {})}
        if self.cookie: h['Cookie'] = self.cookie
        req = urllib.request.Request(self.base + path, data=json.dumps(data).encode(), method='POST', headers=h)
        try:
            with self.opener.open(req, timeout=60) as r:
                return r.status, json.loads(r.read() or b'{}')
        except urllib.error.HTTPError as e:
            try: body = json.loads(e.read() or b'{}')
            except ValueError: body = {}
            return e.code, body


def at_once(calls):
    barrier = threading.Barrier(len(calls)); out = [None] * len(calls)

    def run(i, fn):
        try:
            barrier.wait(20); out[i] = fn()
        except Exception as e:  # noqa: BLE001 · the error is the result
            out[i] = ('error', repr(e))
    th = [threading.Thread(target=run, args=(i, fn)) for i, fn in enumerate(calls)]
    for t in th: t.start()
    for t in th: t.join(120)
    return out


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dir', default='/tmp/wod-carga'); ap.add_argument('--cada', type=float, default=30); ap.add_argument('--veces', type=int, default=10)
    ap.add_argument('--plazas', type=int, default=3); ap.add_argument('--esperar', type=float, default=0, help='segundos antes de la primera ráfaga')
    ap.add_argument('--salida', default=None)
    ap.add_argument('--modo', choices=('pago', 'peticion'), default='pago', help='modo de reserva del servicio de las ráfagas (por defecto %(default)s)')
    a = ap.parse_args()
    work = Path(a.dir).resolve(); run = work / 'run'
    estado = json.loads((run / 'estado.json').read_text()); base = estado['base']
    cuentas = json.loads((work / 'cuentas.json').read_text()); ses = json.loads((run / 'sesiones.json').read_text())
    c = cuentas['centros'][-1]; cid = c['center_id']
    center = Web(base, '100.127.250.1')
    st, _ = center.post('/api/auth/login', {'login': c['usuario'], 'password': c['password']})
    if st != 200: raise SystemExit(f'El centro de carga no entra: HTTP {st}')
    st, d = center.post('/api/center/integration/regenerate', {})
    key = (d or {}).get('api_key')
    st, d = center.post('/api/provider-services', {'title': 'Ráfagas de la prueba de carga', 'price': 50, 'max_participants': 8,
                                                   'booking_mode': 'payment' if a.modo == 'pago' else 'request'})
    if st != 200: raise SystemExit(f'No se ha podido crear el servicio de las ráfagas: HTTP {st} {d}')
    sid = d['id']
    db = sqlite3.connect(f'file:{estado["db"]}?mode=ro', uri=True, timeout=30); db.row_factory = sqlite3.Row
    tokens = ses['tokens'][-60:]           # the last accounts: Locust's Reservas start at random places of the list
    out = {'plazas_por_salida': a.plazas, 'modo': a.modo, 'rafagas': []}
    time.sleep(a.esperar)
    for k in range(a.veces):
        t0 = time.time()
        day = (dt.date.today() + dt.timedelta(days=200 + k)).isoformat()
        st, d = center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': day, 'slot_time': '09:00', 'spots_total': a.plazas})
        if st != 200: out['rafagas'].append({'error': f'salida: HTTP {st} {d}'}); continue
        slot = d['slot_id']
        divers = [Web(base, f'100.126.{k}.{i + 1}', f"{ses['cookie']}={tokens[(k * 12 + i) % len(tokens)]}") for i in range(12)]
        calls = [lambda w=w: ('web',) + w.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slot, 'participants': 1}) for w in divers]
        calls += [lambda i=i: ('manual',) + center.post('/api/center/bookings/manual', {'fullname': f'Cliente teléfono {k}-{i}', 'phone': f'+34 611 {k:03d} {i:03d}',
                                                                                     'service_id': sid, 'slot_id': slot, 'participants': 1, 'status': 'confirmed', 'notify_client': False}) for i in range(4)]
        if key:
            api = Web(base, '100.125.0.1')
            calls += [lambda i=i: ('api',) + api.post('/api/integrations/bookings', {'external_ref': f'rafaga-{k}-{i}', 'fullname': f'Cliente web {k}-{i}', 'email': f'rafaga{k}{i}@example.com',
                                                                                    'service_id': sid, 'slot_id': slot, 'participants': 1, 'status': 'confirmed'},
                                                                         {'X-WORLDIVES-API-Key': key}) for i in range(4)]
        res = at_once(calls)
        ok = {}
        for r in res:
            ok.setdefault(r[0], {'200': 0, 'otras': {}})
            if len(r) == 3 and r[1] == 200: ok[r[0]]['200'] += 1
            else:
                why = f'{r[1]} {(r[2] or {}).get("error", "")[:60]}' if len(r) == 3 else str(r[1])[:80]
                ok[r[0]]['otras'][why] = ok[r[0]]['otras'].get(why, 0) + 1
        took = db.execute('SELECT COUNT(*) n, COALESCE(SUM(participants),0) p FROM bookings WHERE slot_id=? AND slot_reserved=1', (slot,)).fetchone()
        s = db.execute('SELECT spots_total, spots_available FROM service_slots WHERE id=?', (slot,)).fetchone()
        row = {'salida': slot, 'peticiones': len(calls), 'respuestas': ok, 'aceptadas': sum(v['200'] for v in ok.values()), 'plazas': s['spots_total'],
               'libres_despues': s['spots_available'], 'reservas_con_plaza': took['n'], 'plazas_tomadas': took['p'], 'sobreventa': took['p'] > s['spots_total'],
               'segundos': round(time.time() - t0, 2)}
        out['rafagas'].append(row)
        print(json.dumps(row, ensure_ascii=False), flush=True)
        time.sleep(max(0.0, a.cada - (time.time() - t0)))
    out['sobreventa'] = any(r.get('sobreventa') for r in out['rafagas'])
    out['todas_llenas_exactas'] = all(r.get('plazas_tomadas') == a.plazas and r.get('libres_despues') == 0 for r in out['rafagas'])
    if a.modo == 'pago':   # every booking accepted takes its spot: exactly as many accepted as spots
        out['aceptadas_exactas'] = all(r.get('aceptadas') == a.plazas for r in out['rafagas'])
    if a.salida: Path(a.salida).write_text(json.dumps(out, ensure_ascii=False, indent=1))
    print(json.dumps({k: out[k] for k in ('modo', 'sobreventa', 'todas_llenas_exactas', 'aceptadas_exactas') if k in out}), flush=True)


if __name__ == '__main__':
    main()
