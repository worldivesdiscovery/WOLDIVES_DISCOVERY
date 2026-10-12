#!/usr/bin/env python3
"""Builds the TEST database of the «-pruebas» zip (encargo 2b · bloque 1): the fixed test accounts of
CUENTAS-DE-PRUEBA.md and demonstration data to try everything without preparing anything.

    python scripts/crear_demo.py                 → data/pruebas/worldives-pruebas.sqlite3 (snapshot)
    python scripts/crear_demo.py --out FILE      → somewhere else

It starts a temporary server on a copy of the demo catalogue and creates everything through the web's own API, as a
person would (registration, approval, services, departures, bookings…). Dates are relative to TODAY: «salida mañana»,
«curso la semana que viene»… Never use this script, nor its database, on the real server.
"""
from __future__ import annotations

import argparse
import datetime as dt
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from helpers import Client, Server  # noqa: E402

PASSWORD = 'Worldives-Prueba-2026'
ACCOUNTS = {'admin': ('admin.prueba', 'admin@example.com', 'Administración de pruebas'),
            'center': ('centro.prueba', 'centro@example.com', 'Ana Centro Pruebas'),
            'freelance': ('freelance.prueba', 'freelance@example.com', 'Tito Guía Pruebas'),
            'diver': ('buzo.prueba', 'buzo@example.com', 'Bea Buzo Pruebas')}
EXTRA_DIVERS = [(f'buzo{i}.prueba', f'buzo{i}@example.com', f'Buceador {i} Pruebas') for i in range(2, 7)]


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


def workdays(k, n=1, skip=()):
    """n consecutive days from today+k on which the freelance works (Monday to Saturday, not in skip)."""
    while True:
        ds = [dt.date.today() + dt.timedelta(days=k + i) for i in range(n)]
        if all(d.weekday() != 6 and (d - dt.date.today()).days not in skip for d in ds): return [d.isoformat() for d in ds]
        k += 1


def ok(r, what):
    if r.status != 200: raise SystemExit(f'No se ha podido {what}: {r.status} {r.body[:300]!r}')
    return r.json


def build(out: Path):
    srv = Server({'WOD_ADMIN_PASSWORD': PASSWORD, 'WOD_MAINTENANCE_SECONDS': '3600'}).start()
    try:
        c = lambda: Client(srv)
        # --- accounts --------------------------------------------------------------------------------------
        u, e, n = ACCOUNTS['admin']
        res = srv.run_cli('--create-admin', '--email', e, '--username', u, '--name', n, env={'WOD_ADMIN_PASSWORD': PASSWORD})
        if res.returncode != 0: raise SystemExit(res.stdout + res.stderr)
        admin = c(); ok(admin.login(u, PASSWORD), 'entrar como administración')

        def approve(email, method):
            claim = [x for x in admin.get('/api/admin/center-claims').json['items'] if x['email'] == email][0]
            ok(admin.post('/api/admin/center-claims/review', {'id': claim['id'], 'decision': 'approve', 'verification_method': method,
                                                              'verification_note': 'Cuenta de pruebas'}), 'aprobar ' + email)

        u, e, n = ACCOUNTS['center']
        center = c(); ok(center.register(n, e, u, PASSWORD, account_type='center', center_name='Centro de Buceo Pruebas', phone='+34 600 000 101',
                                         city='Xàbia', website='https://centro-pruebas.example.com'), 'registrar el centro')
        approve(e, 'email_domain'); ok(center.login(u, PASSWORD), 'entrar como centro')
        cid = center.me()['user']['center_id']
        u, e, n = ACCOUNTS['freelance']
        pro = c(); ok(pro.register(n, e, u, PASSWORD, account_type='freelance', phone='+52 998 000 0101', certification_text='Instructor y guía de cenotes'), 'registrar el freelance')
        approve(e, 'document'); ok(pro.login(u, PASSWORD), 'entrar como freelance')
        pro_id = pro.me()['user']['id']
        divers = []
        for u, e, n in [ACCOUNTS['diver']] + EXTRA_DIVERS:
            d = c(); ok(d.register(n, e, u, PASSWORD), 'registrar ' + u); ok(d.login(u, PASSWORD), 'entrar como ' + u); divers.append(d)
        buzo = divers[0]
        ok(buzo.post('/api/account/profile', {'certification_id': 2, 'emergency_contact_name': 'Carlos Pruebas', 'emergency_contact_phone': '+34 600 000 999',
                                               'suit_size': 'M', 'phone': '+34 600 000 102', 'country': 'España', 'city': 'Valencia'}), 'completar el perfil')

        # --- centre: services in both modes, departures this month and next, a boat ----------------------------
        srv.sql("UPDATE centers SET logo_url='/assets/images/buceador1.png',country='España',cancel_free_hours=48,cancel_refund_pct=50 WHERE id=?", (cid,))
        req = ok(center.post('/api/provider-services', {'title': 'Doble inmersión en barco', 'price': 75, 'max_participants': 10, 'booking_mode': 'request',
                                                        'duration_minutes': 240, 'description': 'Dos inmersiones en la reserva marina, guía y botellas incluidas.',
                                                        'cancel_free_hours': 48, 'cancel_refund_pct': 50}), 'crear un servicio')['id']
        pay = ok(center.post('/api/provider-services', {'title': 'Bautizo de buceo', 'price': 60, 'max_participants': 6, 'booking_mode': 'request',
                                                        'service_type': 'experiencia', 'duration_minutes': 150}), 'crear un servicio')['id']
        # «Pago al reservar» needs online payments: in the test environment the centre has a test Stripe account
        srv.sql("UPDATE centers SET stripe_account_id='acct_test_pruebas',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cid,))
        srv.sql("UPDATE provider_services SET booking_mode='payment' WHERE id=?", (pay,))
        slots = {}
        for k in (1, 2, 4, 6, 9, 13, 16, 20, 27, 34, 41):
            for sid, tm in ((req, '09:00'), (pay, '16:00')):
                slots[(sid, k)] = ok(center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': day(k), 'slot_time': tm, 'spots_total': 10 if sid == req else 6}), 'crear una salida')['slot_id']
        center.post('/api/manifest/boats/save', {'name': 'Neptuno', 'capacity': 12})
        center.post('/api/manifest/boats/save', {'name': 'Tritón', 'capacity': 8})

        # --- freelance: by days and half days, with busy and free days -----------------------------------------
        days_sid = ok(pro.post('/api/provider-services', {'title': 'Cenotes con guía, por días', 'price': 180, 'max_participants': 4, 'booking_mode': 'request',
                                                          'booking_unit': 'half_day', 'timezone': 'America/Cancun',
                                                          'description': 'Guía titulado, dos cenotes por día y fotos del día. Punto de encuentro: hotel en Tulum.',
                                                          'unit_rules': {'min_days': 1, 'max_days': 10, 'lead_hours': 24},
                                                          'pricing': {'day': 180, 'half': 110, 'discount': {'min_days': 3, 'pct': 10},
                                                                      'extras': [{'id': 'foto', 'label': 'Fotos y vídeo', 'price': 40, 'per': 'day'}]}}), 'crear el servicio por días')['id']
        pro.post('/api/agenda/hours', {'weekdays': [0, 1, 2, 3, 4, 5], 'closures': [], 'timezone': 'America/Cancun'})
        pro.post('/api/agenda/block', {'date_from': day(12), 'date_to': day(14), 'kind': 'holiday'})
        holiday = range(12, 15)
        b = ok(divers[1].post('/api/bookings', {'service_id': days_sid, 'days': workdays(3, 2, holiday), 'part': 'full', 'participants': 2, 'notes': 'Primera vez en cenotes'}), 'reservar días')
        pro.post(f"/api/bookings/{b['id']}/status", {'status': 'confirmed'})
        ok(divers[2].post('/api/bookings', {'service_id': days_sid, 'days': workdays(8, 1, holiday), 'part': 'am', 'participants': 1}), 'reservar medio día')
        ok(buzo.post('/api/bookings', {'service_id': days_sid, 'days': workdays(18, 3, holiday), 'part': 'full', 'participants': 2}), 'reservar tres días')

        # --- experiences: one of each, a liveaboard with places, and one waiting for review ----------------------
        center.post('/api/travel-experiences', {'new_destination': 'Islas Medas', 'new_destination_region': 'España', 'title': 'Fin de semana en las Medas',
                                                'start_date': day(23), 'end_date': day(24), 'price': 240, 'spots_total': 8, 'spots_available': 8,
                                                'includes': '4 inmersiones, guía y botellas', 'summary': 'Dos días de buceo en la reserva marina.'})
        offer = srv.sql("SELECT id FROM travel_offers ORDER BY id DESC LIMIT 1")[0]['id']
        pro.post('/api/travel-experiences', {'travel_offer_id': offer, 'title': 'Vida a bordo en el Caribe mexicano', 'start_date': day(45), 'end_date': day(51),
                                             'price': 1450, 'spots_total': 12, 'spots_available': 12, 'includes': '6 noches, 15 inmersiones, pensión completa'})
        lab = srv.sql("SELECT id FROM travel_experiences ORDER BY id DESC LIMIT 1")[0]['id']
        ok(admin.post('/api/admin/travel-experiences/status', {'id': lab, 'status': 'published'}), 'publicar el vida a bordo')
        pro.post('/api/travel-experiences', {'travel_offer_id': offer, 'title': 'Semana de cenotes y cavernas', 'start_date': day(60), 'end_date': day(66),
                                             'price': 890, 'spots_total': 6, 'spots_available': 6, 'includes': '10 inmersiones en cenotes, transporte'})   # queda pendiente de revisar

        # --- the diver's bookings in every state ------------------------------------------------------------
        def book(diver, sid, k, pax=1):
            return ok(diver.post('/api/bookings', {'center_id': cid, 'service_id': sid, 'slot_id': slots[(sid, k)], 'participants': pax}), 'reservar')['id']
        b_req = book(buzo, req, 9, 2)                                             # solicitada
        b_conf = book(buzo, req, 4, 2); center.post(f'/api/bookings/{b_conf}/status', {'status': 'confirmed'})   # confirmada
        b_pend = book(buzo, req, 13)                                              # aceptada, pendiente de pago
        srv.sql("UPDATE bookings SET status='accepted_pending_payment',payment_status='required',payment_deadline=?,accepted_at=? WHERE id=?",
                ((dt.datetime.now() + dt.timedelta(days=2)).isoformat(timespec='minutes'), dt.datetime.now().isoformat(timespec='seconds'), b_pend))
        b_canc = book(buzo, req, 16); ok(center.post(f'/api/bookings/{b_canc}/status', {'status': 'confirmed'}), 'confirmar')
        ok(center.post(f'/api/bookings/{b_canc}/status', {'status': 'cancelled', 'reason': 'Mal tiempo previsto: cancelada para probar'}), 'cancelar')   # cancelada
        b_rej = book(buzo, req, 20); ok(center.post(f'/api/bookings/{b_rej}/status', {'status': 'rejected', 'reason': 'Salida completa para ese nivel'}), 'rechazar')   # rechazada
        b_paid = book(buzo, req, 6)                                               # pagada online (pago simulado)
        srv.sql("UPDATE bookings SET status='confirmed',payment_status='paid',payment_method='card',amount_paid=price,confirmed_at=? WHERE id=?", (dt.datetime.now().isoformat(timespec='seconds'), b_paid))
        b_exp = book(buzo, req, 27)                                               # caducada (no se pagó a tiempo)
        srv.sql("UPDATE bookings SET status='expired',payment_status='required' WHERE id=?", (b_exp,))
        b_done = book(buzo, req, 1)                                               # completada (en el pasado)
        srv.sql("UPDATE bookings SET status='completed',booking_date=?,confirmed_at=? WHERE id=?", (day(-8), dt.datetime.now().isoformat(timespec='seconds'), b_done))
        for d_, k in ((divers[3], 2), (divers[4], 2), (divers[5], 6)):
            x = book(d_, req, k); center.post(f'/api/bookings/{x}/status', {'status': 'confirmed'})
        # Log Book and points
        for k, site, depth in ((-8, 'Cabo de San Antonio', 18), (-35, 'Isla del Descubridor', 22), (-60, 'Cova Tallada', 12)):
            buzo.post('/api/logbook', {'dive_date': day(k), 'site': site, 'country': 'España', 'depth': depth, 'duration': 48, 'dive_type': 'Barco', 'notes': 'Inmersión de pruebas'})

        # --- administration: a report, an experience to review, a pending centre ----------------------------------
        ok(c().post('/api/reports', {'reason': 'false', 'details': 'Denuncia de pruebas: el precio que aparece no coincide con el del centro.', 'name': 'Persona de pruebas',
                                  'email': 'denuncia@example.com', 'good_faith': True, 'target_url': f'/#/centro?id={cid}'}), 'enviar la denuncia')
        c().register('Otro Centro Pendiente', 'pendiente@example.com', 'pendiente.prueba', PASSWORD, account_type='center', center_name='Centro Pendiente de Pruebas',
                     phone='+34 600 000 103', city='Dénia', website='https://pendiente.example.com')
        srv.sql("UPDATE users SET email_verified_at=? WHERE username LIKE '%.prueba'", (dt.datetime.now().isoformat(timespec='seconds'),))
        srv.sql("UPDATE users SET birth_date='1990-05-14' WHERE username=?", (ACCOUNTS['diver'][0],))
        srv.sql("INSERT OR REPLACE INTO site_settings(key,value,updated_at) VALUES('demo_generated_on',?,?)", (dt.date.today().isoformat(), dt.datetime.now().isoformat(timespec='seconds')))
    except BaseException:
        srv.stop(); raise
    srv.stop(cleanup=False)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        src = sqlite3.connect(srv.db); dst = sqlite3.connect(out)
        src.backup(dst); dst.close(); src.close()
    finally:
        shutil.rmtree(srv.tmp, ignore_errors=True)
    print(f'Base de pruebas creada: {out}')


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=str(ROOT / 'data' / 'pruebas' / 'worldives-pruebas.sqlite3'))
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists(): out.unlink()
    build(out)
