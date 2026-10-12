#!/usr/bin/env python3
"""Builds the TEST database of the «-pruebas» zip: the fixed test accounts of README-PRUEBAS.md and demonstration
data to try everything one by one, without preparing anything (v50.46, cambios del 12/10/2026, punto 4.2).

    python scripts/crear_demo.py                 → data/pruebas/worldives-pruebas.sqlite3
    python scripts/crear_demo.py --out FILE      → somewhere else

It starts a temporary server on a copy of the demo catalogue and creates everything through the web's own API, as a
person would (registration, approval, services, departures, bookings…). Dates are relative to TODAY, so there are
always future departures. There is NO administrator account: the owner creates it the first time with the
«Crea tu cuenta de administración» screen, which only exists in the test environment. A temporary administrator
approves the centre and the freelance while the data is built and is deleted at the end.
Never use this script, nor its database, on the real server.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import secrets
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from helpers import Client, Server, cifrado_for  # noqa: E402

PASSWORD = 'Worldives-Prueba-2026'
ACCOUNTS = {'center': ('centro.prueba', 'centro@example.com', 'Ana Centro Pruebas'),
            'freelance': ('freelance.prueba', 'freelance@example.com', 'Tito Guía Pruebas'),
            'diver': ('buzo.prueba', 'buzo@example.com', 'Bea Buzo Pruebas'),
            'instructor': ('instructor.prueba', 'instructor@example.com', 'Iván Instructor Pruebas'),
            'center2': ('centro2.prueba', 'centro2@example.com', 'Carla Centro Dos Pruebas')}
EXTRA_DIVERS = [(f'buzo{i}.prueba', f'buzo{i}@example.com', f'Buceador {i} Pruebas') for i in range(2, 7)]
PENDING_CENTER = ('pendiente.prueba', 'pendiente@example.com', 'Otro Centro Pendiente')
TEMP_ADMIN = 'generador-demo'


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
    tmp_pass = secrets.token_urlsafe(18) + 'aA1!'
    # v50.47: the fictitious phones are encrypted with the key of the test environment (wod.cifrado.DEMO_DATA_KEY).
    sys.path.insert(0, str(ROOT / 'app'))
    from wod.cifrado import DEMO_DATA_KEY
    srv = Server({'WOD_ADMIN_PASSWORD': tmp_pass, 'WOD_MAINTENANCE_SECONDS': '3600', 'WOD_DATA_KEY': DEMO_DATA_KEY}).start()
    now_s = lambda: dt.datetime.now().isoformat(timespec='seconds')
    try:
        c = lambda: Client(srv)
        # --- temporary administrator (deleted at the end) ---------------------------------------------------
        res = srv.run_cli('--create-admin', '--email', 'generador@example.invalid', '--username', TEMP_ADMIN, '--name', 'Generador de la demo')
        if res.returncode != 0: raise SystemExit(res.stdout + res.stderr)
        admin = c(); ok(admin.login(TEMP_ADMIN, tmp_pass), 'entrar como administración temporal')

        def approve(email, method):
            claim = [x for x in admin.get('/api/admin/center-claims').json['items'] if x['email'] == email][0]
            ok(admin.post('/api/admin/center-claims/review', {'id': claim['id'], 'decision': 'approve', 'verification_method': method,
                                                              'verification_note': 'Cuenta de pruebas'}), 'aprobar ' + email)

        # --- accounts ---------------------------------------------------------------------------------------
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
                                               'suit_size': 'M', 'phone': '+34 600 000 102', 'country': 'España', 'city': 'Valencia',
                                               'date_of_birth': '1990-05-14', 'preferred_language': 'es'}), 'completar el perfil')

        # --- plans: everything unlocked for a year (the test environment shows every function) ----------------
        until = (dt.date.today() + dt.timedelta(days=365)).isoformat()
        srv.sql("UPDATE centers SET plan_code='pro',plan_status='active',plan_started_at=?,plan_expires_at=? WHERE id=?", (day(0), until, cid))
        srv.sql("UPDATE users SET plan_code='pro',plan_status='active',plan_started_at=?,plan_expires_at=? WHERE id=?", (day(0), until, pro_id))

        # --- centre: logo, photos, 5 services in both modes, departures, a boat, an instructor -----------------
        gallery = '["/img/portada/buceadores.webp","/img/portada/fondosuperior.webp","/img/destinos/maldivas.webp"]'
        srv.sql("""UPDATE centers SET logo_url='/img/iconos/buceador1.png',logo_consent=1,cover_url='/img/portada/portada-arrecife.webp',gallery_json=?,
                   country='España',tagline='Buceo en la reserva marina del Cabo de San Antonio',cancel_free_hours=48,cancel_refund_pct=50 WHERE id=?""", (gallery, cid))
        # «Pago al reservar» needs online payments: in the test environment the centre has a test Stripe account
        # (to really pay with the 4242 card, connect your own Stripe account in test mode: README-PRUEBAS.md).
        srv.sql("UPDATE centers SET stripe_account_id='acct_test_pruebas',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (cid,))
        svc = {}
        for key, data in (
                ('simple', {'title': 'Inmersión simple en barco', 'price': 45, 'max_participants': 10, 'booking_mode': 'payment', 'service_type': 'inmersion',
                            'duration_minutes': 120, 'description': 'Una inmersión guiada en la reserva marina. Botella y lastre incluidos.'}),
                ('doble', {'title': 'Doble inmersión en barco', 'price': 75, 'max_participants': 10, 'booking_mode': 'request', 'service_type': 'inmersion',
                           'duration_minutes': 240, 'description': 'Dos inmersiones en la reserva marina, guía y botellas incluidas.'}),
                ('bautizo', {'title': 'Bautizo de buceo', 'price': 60, 'max_participants': 6, 'booking_mode': 'payment', 'service_type': 'experiencia',
                             'duration_minutes': 150, 'description': 'Primera inmersión con instructor, en aguas tranquilas. Sin titulación.'}),
                ('curso', {'title': 'Curso Open Water (3 días)', 'price': 390, 'max_participants': 4, 'booking_mode': 'request', 'service_type': 'curso',
                           'duration_minutes': 480, 'description': 'Tres días: teoría, piscina y 4 inmersiones en el mar. Material y certificación incluidos. Se reserva el primer día.'}),
                ('alquiler', {'title': 'Alquiler de equipo completo', 'price': 25, 'max_participants': 12, 'booking_mode': 'request', 'service_type': 'alquiler_equipo',
                              'duration_minutes': 480, 'description': 'Jacket, regulador, traje, máscara y aletas para un día.'})):
            mode = data['booking_mode']
            svc[key] = ok(center.post('/api/provider-services', {**data, 'booking_mode': 'request', 'cancel_free_hours': 48, 'cancel_refund_pct': 50}), 'crear ' + data['title'])['id']
            if mode == 'payment': srv.sql("UPDATE provider_services SET booking_mode='payment' WHERE id=?", (svc[key],))
        slots = {}
        times = {'simple': '09:00', 'doble': '08:30', 'bautizo': '16:00', 'curso': '09:00', 'alquiler': '08:00'}
        spots = {'simple': 10, 'doble': 10, 'bautizo': 6, 'curso': 4, 'alquiler': 12}
        for k in (1, 2, 3, 4, 6, 8, 9, 10, 13, 16, 20, 27, 34, 41):          # this week, next week and next month
            for key, sid in svc.items():
                if key == 'curso' and k not in (3, 10, 27): continue
                slots[(key, k)] = ok(center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': day(k), 'slot_time': times[key], 'spots_total': spots[key]}),
                                     'crear una salida')['slot_id']
        ok(center.post('/api/manifest/boats/save', {'name': 'Neptuno', 'capacity': 12}), 'crear el barco')
        u, e, n = ACCOUNTS['instructor']
        ok(center.post('/api/center/team/invite', {'email': e, 'member_role': 'instructor'}), 'invitar al instructor')
        mail = srv.sql("SELECT html FROM email_outbox WHERE template='team_invite' AND to_email=? ORDER BY id DESC LIMIT 1", (e,))[0]['html']
        token = re.search(r'#/equipo\?token=([A-Za-z0-9_-]+)', mail).group(1)
        ok(c().post('/api/team/join', {'token': token, 'fullname': n, 'username': u, 'password': PASSWORD, 'accept_terms': True}), 'dar de alta al instructor')

        # --- freelance: photo, 3 services (days, half days, photo session), calendar -------------------------
        srv.sql("UPDATE users SET avatar_url='/img/portada/logbook1.webp',provider_bio='Guía e instructor en los cenotes de la Riviera Maya desde 2012.' WHERE id=?", (pro_id,))
        days_sid = ok(pro.post('/api/provider-services', {'title': 'Cenotes con guía, por días', 'price': 180, 'max_participants': 4, 'booking_mode': 'request',
                                                          'booking_unit': 'day', 'timezone': 'America/Cancun',
                                                          'description': 'Guía titulado, dos cenotes por día. Punto de encuentro: hotel en Tulum.',
                                                          'unit_rules': {'min_days': 1, 'max_days': 10, 'lead_hours': 24},
                                                          'pricing': {'day': 180, 'discount': {'min_days': 3, 'pct': 10}}}), 'crear el servicio por días')['id']
        half_sid = ok(pro.post('/api/provider-services', {'title': 'Cenote por la mañana o por la tarde', 'price': 110, 'max_participants': 4, 'booking_mode': 'request',
                                                          'booking_unit': 'half_day', 'timezone': 'America/Cancun',
                                                          'description': 'Medio día: un cenote con guía, transporte desde Tulum.',
                                                          'unit_rules': {'min_days': 1, 'max_days': 5, 'lead_hours': 24},
                                                          'pricing': {'day': 200, 'half': 110}}), 'crear el servicio de medio día')['id']
        foto_sid = ok(pro.post('/api/provider-services', {'title': 'Sesión de fotos y vídeo bajo el agua', 'price': 90, 'max_participants': 2, 'booking_mode': 'request',
                                                          'service_type': 'experiencia', 'duration_minutes': 180,
                                                          'description': 'Fotos y vídeo de tu inmersión en un cenote. Entrega en 48 horas.'}), 'crear la sesión de fotos')['id']
        for k in (4, 11, 18):
            ok(pro.post('/api/provider-services/slot', {'service_id': foto_sid, 'slot_date': day(k), 'slot_time': '11:00', 'spots_total': 2}), 'crear una sesión')
        pro.post('/api/agenda/hours', {'weekdays': [0, 1, 2, 3, 4, 5], 'closures': [], 'timezone': 'America/Cancun'})
        pro.post('/api/agenda/block', {'date_from': day(12), 'date_to': day(14), 'kind': 'holiday'})
        holiday = range(12, 15)
        b = ok(divers[1].post('/api/bookings', {'service_id': days_sid, 'days': workdays(3, 2, holiday), 'part': 'full', 'participants': 2, 'notes': 'Primera vez en cenotes'}), 'reservar días')
        ok(pro.post(f"/api/bookings/{b['id']}/status", {'status': 'confirmed'}), 'confirmar días')
        ok(divers[2].post('/api/bookings', {'service_id': half_sid, 'days': workdays(8, 1, holiday), 'part': 'am', 'participants': 1}), 'reservar medio día')
        ok(buzo.post('/api/bookings', {'service_id': days_sid, 'days': workdays(18, 3, holiday), 'part': 'full', 'participants': 2}), 'reservar tres días')

        # --- experiences: published (centre and freelance liveaboard) and one waiting for review ---------------
        ok(center.post('/api/travel-experiences', {'new_destination': 'Islas Medas', 'new_destination_region': 'España', 'title': 'Fin de semana en las Medas',
                                                   'start_date': day(23), 'end_date': day(24), 'price': 240, 'spots_total': 8, 'spots_available': 8,
                                                   'includes': '4 inmersiones, guía y botellas', 'summary': 'Dos días de buceo en la reserva marina.'}), 'crear experiencia')
        exp1 = srv.sql("SELECT id FROM travel_experiences ORDER BY id DESC LIMIT 1")[0]['id']
        offer = srv.sql("SELECT id FROM travel_offers WHERE title LIKE 'Riviera Maya%' LIMIT 1") or srv.sql("SELECT id FROM travel_offers ORDER BY id DESC LIMIT 1")
        offer = offer[0]['id']
        ok(pro.post('/api/travel-experiences', {'travel_offer_id': offer, 'title': 'Vida a bordo en el Caribe mexicano', 'start_date': day(45), 'end_date': day(51),
                                                'price': 1450, 'spots_total': 12, 'spots_available': 12, 'includes': '6 noches, 15 inmersiones, pensión completa'}), 'crear el vida a bordo')
        exp2 = srv.sql("SELECT id FROM travel_experiences ORDER BY id DESC LIMIT 1")[0]['id']
        for x in (exp1, exp2): ok(admin.post('/api/admin/travel-experiences/status', {'id': x, 'status': 'published'}), 'publicar la experiencia')
        ok(pro.post('/api/travel-experiences', {'travel_offer_id': offer, 'title': 'Semana de cenotes y cavernas', 'start_date': day(60), 'end_date': day(66),
                                                'price': 890, 'spots_total': 6, 'spots_available': 6, 'includes': '10 inmersiones en cenotes, transporte'}), 'crear la experiencia por revisar')

        # --- the diver's bookings in every state --------------------------------------------------------------
        def book(diver, key, k, pax=1):
            return ok(diver.post('/api/bookings', {'center_id': cid, 'service_id': svc[key], 'slot_id': slots[(key, k)], 'participants': pax}), 'reservar')['id']
        book(buzo, 'doble', 9, 2)                                                       # solicitada
        b_conf = book(buzo, 'doble', 4, 2); ok(center.post(f'/api/bookings/{b_conf}/status', {'status': 'confirmed'}), 'confirmar')   # confirmada
        b_pend = book(buzo, 'curso', 10)                                                # aceptada, pendiente de pago
        srv.sql("UPDATE bookings SET status='accepted_pending_payment',payment_status='required',payment_deadline=?,accepted_at=? WHERE id=?",
                ((dt.datetime.now() + dt.timedelta(days=2)).isoformat(timespec='minutes'), now_s(), b_pend))
        b_canc = book(buzo, 'doble', 16); ok(center.post(f'/api/bookings/{b_canc}/status', {'status': 'confirmed'}), 'confirmar')
        ok(center.post(f'/api/bookings/{b_canc}/status', {'status': 'cancelled', 'reason': 'Mal tiempo previsto: cancelada para probar'}), 'cancelar')   # cancelada
        b_rej = book(buzo, 'alquiler', 20); ok(center.post(f'/api/bookings/{b_rej}/status', {'status': 'rejected', 'reason': 'No quedan trajes de tu talla ese día'}), 'rechazar')
        b_paid = book(buzo, 'doble', 6)                                                 # pagada online (pago simulado)
        srv.sql("UPDATE bookings SET status='confirmed',payment_status='paid',payment_method='card',amount_paid=price,confirmed_at=? WHERE id=?", (now_s(), b_paid))
        b_exp = book(buzo, 'doble', 27)                                                 # caducada (no se pagó a tiempo)
        srv.sql("UPDATE bookings SET status='expired',payment_status='required' WHERE id=?", (b_exp,))
        b_done = book(buzo, 'doble', 1)                                                 # completada (en el pasado)
        srv.sql("UPDATE bookings SET status='completed',booking_date=?,confirmed_at=? WHERE id=?", (day(-8), now_s(), b_done))
        for d_, key, k in ((divers[3], 'doble', 2), (divers[4], 'doble', 2), (divers[5], 'doble', 3), (divers[3], 'alquiler', 3)):
            x = book(d_, key, k); ok(center.post(f'/api/bookings/{x}/status', {'status': 'confirmed'}), 'confirmar')
        for k, site, depth in ((-8, 'Cabo de San Antonio', 18), (-35, 'Isla del Descubridor', 22), (-60, 'Cova Tallada', 12)):
            ok(buzo.post('/api/logbook', {'dive_date': day(k), 'site': site, 'country': 'España', 'depth': depth, 'duration': 48, 'dive_type': 'Barco',
                                          'notes': 'Inmersión de pruebas'}), 'apuntar en el Log Book')

        # --- v50.47: a second centre with divers in common (isolation between centres, mass notices) ------------
        u, e, n = ACCOUNTS['center2']
        center2 = c(); ok(center2.register(n, e, u, PASSWORD, account_type='center', center_name='Centro de Buceo Pruebas Dos', phone='+34 600 000 201',
                                           city="L'Estartit", website='https://centro2-pruebas.example.com'), 'registrar el segundo centro')
        approve(e, 'email_domain'); ok(center2.login(u, PASSWORD), 'entrar como segundo centro')
        cid2 = center2.me()['user']['center_id']
        srv.sql("UPDATE centers SET plan_code='pro',plan_status='active',plan_started_at=?,plan_expires_at=?,country='España',logo_url='/img/iconos/buceador2.png',"
                "cover_url='/img/destinos/maldivas.webp',tagline='Buceo en las Islas Medas',cancel_free_hours=24,cancel_refund_pct=100,"
                "stripe_account_id='acct_test_pruebas2',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?", (day(0), until, cid2))
        svc2 = {}
        for key, data in (('medas', {'title': 'Inmersión en las Islas Medas', 'price': 55, 'max_participants': 12, 'booking_mode': 'request', 'service_type': 'inmersion',
                                     'duration_minutes': 150, 'description': 'Inmersión guiada en la reserva marina de las Medas.'}),
                          ('nocturna', {'title': 'Inmersión nocturna', 'price': 65, 'max_participants': 8, 'booking_mode': 'request', 'service_type': 'inmersion',
                                        'duration_minutes': 120, 'description': 'Salida al atardecer con linterna incluida.'})):
            svc2[key] = ok(center2.post('/api/provider-services', data), 'crear ' + data['title'])['id']
        slots2 = {}
        for k in (2, 3, 5, 9, 16):
            slots2[('medas', k)] = ok(center2.post('/api/provider-services/slot', {'service_id': svc2['medas'], 'slot_date': day(k), 'slot_time': '10:00', 'spots_total': 12}), 'salida')['slot_id']
            slots2[('nocturna', k)] = ok(center2.post('/api/provider-services/slot', {'service_id': svc2['nocturna'], 'slot_date': day(k), 'slot_time': '20:30', 'spots_total': 8}), 'salida')['slot_id']
        ok(center2.post('/api/manifest/boats/save', {'name': 'Medusa', 'capacity': 12}), 'crear el barco del segundo centro')
        # Phones with the country prefix and WhatsApp consent (one without prefix and one without consent, to see both cases)
        for i, d_ in enumerate(divers):
            body = {'phone': f'+34 611 000 {100 + i:03d}', 'wa_consent': True, 'preferred_language': ['es', 'en', 'fr', 'de', 'it', 'es'][i]}
            if i == 4: body['phone'] = '611 000 104'          # sin prefijo: no recibe WhatsApp (aviso en su perfil)
            if i == 5: body['wa_consent'] = False             # sin permiso: correo y app
            if i == 0: body.pop('preferred_language'); body['phone'] = '+34 600 000 102'
            ok(d_.post('/api/account/profile', body), 'teléfono y permiso de WhatsApp')
        # Divers in common: the same people book with both centres (each centre only sees its own bookings)
        for d_, key, k in ((buzo, 'medas', 5), (divers[1], 'medas', 5), (divers[2], 'medas', 5), (divers[3], 'nocturna', 9), (buzo, 'nocturna', 16)):
            x = ok(d_.post('/api/bookings', {'center_id': cid2, 'service_id': svc2[key], 'slot_id': slots2[(key, k)], 'participants': 1}), 'reservar en el segundo centro')['id']
            ok(center2.post(f'/api/bookings/{x}/status', {'status': 'confirmed'}), 'confirmar en el segundo centro')
        for d_, key, k in ((divers[1], 'doble', 4), (divers[2], 'doble', 4)):          # and with the first centre on another day
            x = book(d_, key, k); ok(center.post(f'/api/bookings/{x}/status', {'status': 'confirmed'}), 'confirmar')
        # Simulated WhatsApp numbers of both centres (test environment: messages are saved, never sent)
        cif = cifrado_for(srv.env)
        for key_, number in ((f'c:{cid}', '+34 600 000 101'), (f'c:{cid2}', '+34 600 000 201')):
            pnid = 'pruebas-' + key_.replace(':', '-')
            tpl = {f'{t}:{l}': 'APPROVED' for t in ('worldives_salida_cancelada', 'worldives_cambio_salida', 'worldives_recordatorio')
                   for l in ('es', 'en', 'fr', 'de', 'it', 'pt_PT', 'nl', 'pl', 'zh_CN')}
            srv.sql('''INSERT INTO whatsapp_accounts(provider_id,status,waba_id,phone_number_id,display_number,token,pnid_hash,number_hash,waba_hash,verified_name,coexistence,
                       templates,connected_at,updated_at) VALUES(?,'connected',?,?,?,?,?,?,?,?,1,?,?,?)''',
                    (key_, cif.encrypt_secret('pruebas-waba'), cif.encrypt_secret(pnid), cif.encrypt_secret(cif.normalize_phone(number)), cif.encrypt_secret('pruebas'),
                     cif.keyed_hash('pnid', pnid), cif.fingerprint(number), cif.keyed_hash('waba', 'pruebas-' + key_), 'WhatsApp de prueba', __import__('json').dumps(tpl), now_s(), now_s()))
        srv.sql("INSERT OR REPLACE INTO provider_settings(provider_id,notice_policy,reminder_enabled,reminder_hour,reminder_bring,updated_at) VALUES(?,?,?,?,?,?)",
                (f'c:{cid}', 'choice', 1, 18, 'Titulación, toalla y protector solar', now_s()))

        # --- administration inbox: a pending centre, an experience to review (above) and a report -------------
        ok(c().post('/api/reports', {'reason': 'false', 'details': 'Denuncia de pruebas: el precio que aparece no coincide con el del centro.', 'name': 'Persona de pruebas',
                                     'email': 'denuncia@example.com', 'good_faith': True, 'target_url': f'/#/centro?id={cid}'}), 'enviar la denuncia')
        u, e, n = PENDING_CENTER
        ok(c().register(n, e, u, PASSWORD, account_type='center', center_name='Centro Pendiente de Pruebas', phone='+34 600 000 103', city='Dénia',
                        website='https://pendiente.example.com'), 'registrar el centro pendiente')

        # --- finishing touches and the temporary administrator out ------------------------------------------
        srv.sql("UPDATE users SET email_verified_at=? WHERE username LIKE '%.prueba'", (now_s(),))
        tmp_id = srv.sql('SELECT id FROM users WHERE username=?', (TEMP_ADMIN,))[0]['id']
        srv.sql('DELETE FROM sessions WHERE user_id=?', (tmp_id,)); srv.sql('DELETE FROM user_profiles WHERE user_id=?', (tmp_id,))
        srv.sql('DELETE FROM users WHERE id=?', (tmp_id,))
        srv.sql('DELETE FROM email_outbox')                                             # nothing waits to be sent in a fresh test environment
        srv.sql("INSERT OR REPLACE INTO site_settings(key,value,updated_at) VALUES('demo_generated_on',?,?)", (day(0), now_s()))
        if srv.sql("SELECT 1 FROM users WHERE role='admin'"): raise SystemExit('La base de pruebas no debe traer cuentas de administración.')
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
