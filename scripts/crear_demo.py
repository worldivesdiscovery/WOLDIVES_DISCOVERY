#!/usr/bin/env python3
"""Builds the DEMO database (zip «-DEMO», v50.51): two INVENTED dive centres that look as if they had been working for
months, with their team, two freelance instructors, twenty divers, a year of planning around today, bookings in every
state, reviews, promotions and bonos, points, statistics and the marine life of every dive site.

    python scripts/crear_demo.py                 → data/pruebas/worldives-pruebas.sqlite3
    python scripts/crear_demo.py --out FILE      → somewhere else

It starts a temporary server on a copy of the demo catalogue and creates the accounts, profiles, services and today's
planning through the web's own API, as a person would. The months of history (past departures, check-ins, payments)
are written straight into the database: hundreds of past dives through the API would take minutes. Dates are relative
to TODAY. Everything is invented (names, centres, reviews) or the web's own (illustrations, photos of the site).
The accounts and their password are in CUENTAS-DEMO.txt (not in the code of the web). Never use this script, nor its
database, on the real server: the code refuses to start in demo mode with the production address.
"""
from __future__ import annotations

import argparse
import datetime as dt
import json
import random
import re
import secrets
import shutil
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'tests'))
from helpers import Client, Server, cifrado_for  # noqa: E402

DATA = json.loads((ROOT / 'scripts' / 'demo' / 'centros.json').read_text(encoding='utf-8'))
VIDEOS = ROOT / 'data' / 'demo' / 'videos-demo.json'      # optional real links for the demo (see README-PRUEBAS, 9)
PASSWORD = 'Worldives-Prueba-2026'
ACCOUNTS = {'admin': ('admin.prueba', 'admin@example.com', 'Nerea Galván'),
            'center': ('centro.prueba', 'hola@bahiacoralina.example.com', 'Marta Llorens'),
            'center2': ('centro2.prueba', 'hola@escafandramedes.example.com', 'Jordi Pujadas'),
            'freelance': ('freelance.prueba', 'diego.arenas@example.com', 'Diego Arenas'),
            'freelance2': ('freelance2.prueba', 'sara.molina@example.com', 'Sara Molina'),
            'diver': ('buzo.prueba', 'bea.navarro@example.com', 'Bea Navarro'),
            'instructor': ('instructor.prueba', 'ivan.soler@example.com', 'Iván Soler'),
            'master': ('master.prueba', 'elena.ribas@example.com', 'Elena Ribas'),
            'instructor2': ('instructor2.prueba', 'pau.ferrer@example.com', 'Pau Ferrer'),
            'recepcion': ('recepcion.prueba', 'clara.vidal@example.com', 'Clara Vidal')}
# (username, email, name, language, country)
EXTRA_DIVERS = [('buzo2.prueba', 'lukas.becker@example.com', 'Lukas Becker', 'de', 'Alemania'),
                ('buzo3.prueba', 'chloe.martin@example.com', 'Chloé Martin', 'fr', 'Francia'),
                ('buzo4.prueba', 'giulia.romano@example.com', 'Giulia Romano', 'it', 'Italia'),
                ('buzo5.prueba', 'tom.jansen@example.com', 'Tom Jansen', 'nl', 'Países Bajos'),
                ('buzo6.prueba', 'emily.clarke@example.com', 'Emily Clarke', 'en', 'Reino Unido'),
                ('buzo7.prueba', 'kasia.nowak@example.com', 'Kasia Nowak', 'pl', 'Polonia'),
                ('buzo8.prueba', 'wei.chen@example.com', 'Wei Chen', 'zh', 'China'),
                ('buzo9.prueba', 'joao.silva@example.com', 'João Silva', 'pt', 'Portugal'),
                ('buzo10.prueba', 'alvaro.ruiz@example.com', 'Álvaro Ruiz', 'es', 'España'),
                ('buzo11.prueba', 'nuria.costa@example.com', 'Nuria Costa', 'es', 'España'),
                ('buzo12.prueba', 'pierre.lambert@example.com', 'Pierre Lambert', 'fr', 'Francia'),
                ('buzo13.prueba', 'hannah.weber@example.com', 'Hannah Weber', 'de', 'Alemania'),
                ('buzo14.prueba', 'marco.bianchi@example.com', 'Marco Bianchi', 'it', 'Italia'),
                ('buzo15.prueba', 'sofie.devries@example.com', 'Sofie de Vries', 'nl', 'Países Bajos'),
                ('buzo16.prueba', 'james.walker@example.com', 'James Walker', 'en', 'Reino Unido'),
                ('buzo17.prueba', 'lucia.prieto@example.com', 'Lucía Prieto', 'es', 'España'),
                ('buzo18.prueba', 'raul.ortega@example.com', 'Raúl Ortega', 'es', 'España'),
                ('buzo19.prueba', 'anna.kowalska@example.com', 'Anna Kowalska', 'pl', 'Polonia'),
                ('buzo20.prueba', 'li.na@example.com', 'Li Na', 'zh', 'China')]
PENDING_CENTER = ('pendiente.prueba', 'hola@arrecifeazul.example.com', 'Rosa Domènech')
HISTORY_DAYS = 150
# Species of each dive site (name in the catalogue → [(example key, frequency, months)]): only species that live there.
MARINE = {
    'Cabo San Antonio': [('mero', 'common', []), ('corvina', 'common', []), ('sargo', 'common', []), ('castanuela', 'common', []), ('pez-verde', 'common', []),
                         ('morena', 'common', []), ('serrano', 'common', []), ('estrella-roja', 'common', []), ('pulpo', 'occasional', []), ('denton', 'occasional', []),
                         ('gorgonia-roja', 'occasional', []), ('langosta', 'rare', []), ('pez-luna', 'rare', [5, 6, 7, 8]), ('caballito', 'rare', [])],
    'Cabo San Martin / Cueva de la Virgen': [('morena', 'common', []), ('castanuela', 'common', []), ('pez-verde', 'common', []), ('serrano', 'common', []),
                                             ('estrella-roja', 'common', []), ('anemona', 'common', []), ('cabracho', 'occasional', []), ('langosta', 'occasional', []),
                                             ('flabelina', 'occasional', [3, 4, 5, 6]), ('pulpo', 'occasional', [])],
    'Portitxol Norte': [('posidonia', 'common', []), ('salpa', 'common', []), ('pulpo', 'common', []), ('castanuela', 'common', []), ('sargo', 'common', []),
                        ('pez-verde', 'common', []), ('estrella-roja', 'common', []), ('sepia', 'occasional', [3, 4, 5, 6]), ('espeton', 'occasional', []),
                        ('caballito', 'rare', []), ('tortuga-boba', 'rare', [6, 7, 8, 9])],
    'Piedras Rotas': [('pulpo', 'common', []), ('morena', 'common', []), ('castanuela', 'common', []), ('sargo', 'common', []), ('serrano', 'common', []),
                      ('salpa', 'common', []), ('anemona', 'common', []), ('estrella-roja', 'common', []), ('cabracho', 'occasional', [])],
    'Pared Negra': [('morena', 'common', []), ('pez-verde', 'common', []), ('castanuela', 'common', []), ('serrano', 'common', []), ('cabracho', 'occasional', []),
                    ('flabelina', 'occasional', [3, 4, 5, 6]), ('denton', 'occasional', []), ('gorgonia-roja', 'rare', []), ('langosta', 'rare', [])],
    'Montaña Sumergida - Cabo Negro': [('castanuela', 'common', []), ('sargo', 'common', []), ('espeton', 'common', []), ('denton', 'occasional', []),
                                       ('mero', 'occasional', []), ('corvina', 'occasional', []), ('gorgonia-roja', 'occasional', []),
                                       ('pez-ballesta', 'occasional', [6, 7, 8, 9]), ('pez-luna', 'rare', [5, 6, 7, 8])],
    'Islas Medes, Costa Brava': [('mero', 'common', []), ('corvina', 'common', []), ('espeton', 'common', []), ('sargo', 'common', []), ('castanuela', 'common', []),
                                 ('pez-verde', 'common', []), ('morena', 'common', []), ('gorgonia-roja', 'common', []), ('pulpo', 'occasional', []),
                                 ('denton', 'occasional', []), ('langosta', 'occasional', []), ('cabracho', 'occasional', []), ('caballito', 'rare', []),
                                 ('pez-luna', 'rare', [5, 6, 7, 8]), ('tortuga-boba', 'rare', [6, 7, 8, 9])],
    'Medes – La Vaca': [('mero', 'common', []), ('gorgonia-roja', 'common', []), ('corvina', 'common', []), ('morena', 'common', []), ('castanuela', 'common', []),
                        ('langosta', 'occasional', []), ('denton', 'occasional', []), ('espeton', 'occasional', []), ('flabelina', 'occasional', [3, 4, 5, 6]),
                        ('cabracho', 'occasional', [])],
    'Medes – Carall Bernat': [('gorgonia-roja', 'common', []), ('mero', 'common', []), ('morena', 'common', []), ('castanuela', 'common', []),
                              ('estrella-roja', 'common', []), ('corvina', 'occasional', []), ('langosta', 'occasional', []), ('flabelina', 'occasional', [3, 4, 5, 6]),
                              ('denton', 'occasional', [])],
    'Medes – Tascons': [('mero', 'common', []), ('corvina', 'common', []), ('sargo', 'common', []), ('salpa', 'common', []), ('posidonia', 'common', []),
                        ('pulpo', 'common', []), ('castanuela', 'common', []), ('pez-verde', 'common', []), ('serrano', 'common', []), ('estrella-roja', 'common', []),
                        ('anemona', 'common', []), ('sepia', 'occasional', [3, 4, 5, 6])],
}
POINTS_BAHIA = ['Cabo San Antonio', 'Cabo San Martin / Cueva de la Virgen', 'Portitxol Norte', 'Piedras Rotas', 'Pared Negra', 'Montaña Sumergida - Cabo Negro']
POINTS_MEDES = ['Islas Medes, Costa Brava', 'Medes – La Vaca', 'Medes – Carall Bernat', 'Medes – Tascons']


def app_version() -> str:
    return re.search(r"^APP_VERSION = '([^']+)'", (ROOT / 'app' / 'server.py').read_text(encoding='utf-8'), re.M).group(1)


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


def workdays(k, n=1, skip=()):
    """n consecutive days from today+k on which the freelance works (Monday to Saturday, not in skip)."""
    while True:
        ds = [dt.date.today() + dt.timedelta(days=k + i) for i in range(n)]
        if all(d.weekday() != 6 and (d - dt.date.today()).days not in skip for d in ds): return [d.isoformat() for d in ds]
        k += 1


def season(d: dt.date) -> float:
    """How busy a day of the year is on the Spanish Mediterranean coast (summer high season)."""
    return {7: 1.9, 8: 2.1, 6: 1.5, 9: 1.4, 5: 1.0, 10: .9, 4: .8}.get(d.month, .5) * (1.35 if d.weekday() >= 5 else 1.0)


def demo_pdf(*lines):
    """A small real PDF with text (v50.56, the test policies)."""
    import zlib
    content = b'BT /F1 12 Tf 72 760 Td ' + b' '.join(b'(' + l.encode('latin-1') + b') Tj 0 -18 Td' for l in lines) + b' ET'
    comp = zlib.compress(content)
    return (b'%PDF-1.4\n1 0 obj<</Type/Catalog/Pages 2 0 R>>endobj\n2 0 obj<</Type/Pages/Kids[3 0 R]/Count 1>>endobj\n'
            b'3 0 obj<</Type/Page/Parent 2 0 R/MediaBox[0 0 595 842]/Contents 4 0 R/Resources<</Font<</F1 5 0 R>>>>>>endobj\n'
            b'4 0 obj<</Length ' + str(len(comp)).encode() + b'/Filter/FlateDecode>>stream\n' + comp + b'\nendstream\nendobj\n'
            b'5 0 obj<</Type/Font/Subtype/Type1/BaseFont/Helvetica>>endobj\ntrailer<</Root 1 0 R>>\n%%EOF\n')


def ok(r, what):
    if r.status != 200: raise SystemExit(f'No se ha podido {what}: {r.status} {r.body[:300]!r}')
    return r.json


def build(out: Path):
    rnd = random.Random(5051)
    tmp_pass = secrets.token_urlsafe(18) + 'aA1!'
    # The accounts are made with a random password through the web, as anybody would; the documented password of the
    # test environment (CUENTAS-DEMO.txt) is put at the end: the server refuses it for real accounts because it is easy
    # to guess (it has the name of the web, ASVS 5.0 V6.2.11), and these accounts only exist in the test environment.
    pw = 'Construir-' + secrets.token_urlsafe(12)
    # v50.47: the fictitious phones are encrypted with the key of the test environment (wod.cifrado.DEMO_DATA_KEY).
    sys.path.insert(0, str(ROOT / 'app'))
    from wod.cifrado import DEMO_DATA_KEY
    srv = Server({'WOD_ADMIN_PASSWORD': tmp_pass, 'WOD_MAINTENANCE_SECONDS': '3600', 'WOD_DATA_KEY': DEMO_DATA_KEY}).start()
    now_s = lambda: dt.datetime.now().isoformat(timespec='seconds')
    today = dt.date.today()
    try:
        c = lambda: Client(srv)
        # --- the demo administrator (its password is in CUENTAS-DEMO.txt) ------------------------------------
        u, e, n = ACCOUNTS['admin']
        res = srv.run_cli('--create-admin', '--email', e, '--username', u, '--name', n, env={'WOD_ADMIN_PASSWORD': pw})
        if res.returncode != 0: raise SystemExit(res.stdout + res.stderr)
        admin = c(); ok(admin.login(u, pw), 'entrar como administración')

        def approve(email, method):
            claim = [x for x in admin.get('/api/admin/center-claims').json['items'] if x['email'] == email][0]
            ok(admin.post('/api/admin/center-claims/review', {'id': claim['id'], 'decision': 'approve', 'verification_method': method,
                                                              'verification_note': 'Cuenta de la demostración'}), 'aprobar ' + email)

        # --- the two centres, the two freelance instructors and the divers --------------------------------------
        bahia, medes = DATA['bahia'], DATA['medes']
        u, e, n = ACCOUNTS['center']
        center = c(); ok(center.register(n, e, u, pw, account_type='center', center_name=bahia['name'], phone='+34 600 000 101',
                                         city='Xàbia', website='https://bahiacoralina.example.com'), 'registrar el primer centro')
        approve(e, 'email_domain'); ok(center.login(u, pw), 'entrar como primer centro')
        cid = center.me()['user']['center_id']
        u, e, n = ACCOUNTS['center2']
        center2 = c(); ok(center2.register(n, e, u, pw, account_type='center', center_name=medes['name'], phone='+34 972 000 202',
                                           city="L'Estartit", website='https://escafandramedes.example.com'), 'registrar el segundo centro')
        approve(e, 'email_domain'); ok(center2.login(u, pw), 'entrar como segundo centro')
        cid2 = center2.me()['user']['center_id']
        u, e, n = ACCOUNTS['freelance']
        pro = c(); ok(pro.register(n, e, u, pw, account_type='freelance', phone='+52 998 000 0101', certification_text='Instructor y guía de cenotes'), 'registrar el freelance')
        approve(e, 'document'); ok(pro.login(u, pw), 'entrar como freelance')
        pro_id = pro.me()['user']['id']
        u, e, n = ACCOUNTS['freelance2']
        pro2 = c(); ok(pro2.register(n, e, u, pw, account_type='freelance', phone='+34 611 222 333', certification_text='Instructora y fotógrafa submarina'), 'registrar la freelance')
        approve(e, 'document'); ok(pro2.login(u, pw), 'entrar como freelance')
        pro2_id = pro2.me()['user']['id']
        divers, diver_ids = [], []
        u, e, n = ACCOUNTS['diver']
        for u, e, n in [(u, e, n)] + [(x[0], x[1], x[2]) for x in EXTRA_DIVERS]:
            d = c(); ok(d.register(n, e, u, pw), 'registrar ' + u); ok(d.login(u, pw), 'entrar como ' + u)
            divers.append(d); diver_ids.append(d.me()['user']['id'])
        buzo = divers[0]
        ok(buzo.post('/api/account/profile', {'certification_id': 2, 'emergency_contact_name': 'Carlos Navarro', 'emergency_contact_phone': '+34 600 000 999',
                                               'suit_size': 'M', 'phone': '+34 600 000 102', 'country': 'España', 'city': 'Valencia',
                                               'date_of_birth': '1990-05-14', 'preferred_language': 'es'}), 'completar el perfil')
        # Phones with the country prefix and WhatsApp consent (one without prefix and one without consent, to see both cases)
        for i, d_ in enumerate(divers):
            lang, country = ('es', 'España') if i == 0 else EXTRA_DIVERS[i - 1][3:5]
            body = {'phone': f'+34 611 000 {100 + i:03d}', 'wa_consent': True, 'preferred_language': lang, 'country': country}
            if i == 4: body['phone'] = '611 000 104'          # sin prefijo: no recibe WhatsApp (aviso en su perfil)
            if i == 5: body['wa_consent'] = False             # sin permiso: correo y app
            if i == 0: body.pop('preferred_language'); body['phone'] = '+34 600 000 102'
            ok(d_.post('/api/account/profile', body), 'teléfono y permiso de WhatsApp')

        # --- plans: everything unlocked for a year (the demo shows every function) ----------------------------
        until = day(365)
        for t, i in (('centers', cid), ('centers', cid2), ('users', pro_id), ('users', pro2_id)):
            srv.sql(f"UPDATE {t} SET plan_code='pro',plan_status='active',plan_started_at=?,plan_expires_at=? WHERE id=?", (day(-HISTORY_DAYS), until, i))

        # --- profiles in the 9 languages of the web (Escaparate), logos, photos ---------------------------------
        for cl, data_, extra in ((center, bahia, {'languages': 'Español, inglés, francés, alemán', 'opening_hours': 'Todos los días de 8:00 a 19:00'}),
                                 (center2, medes, {'languages': 'Español, catalán, inglés, francés', 'opening_hours': 'De marzo a noviembre, de 8:30 a 20:00'})):
            es = data_['texts']['es']
            ok(cl.post('/api/provider/center-showcase', {'tagline': es['tagline'], **extra, 'texts': {k: v for k, v in data_['texts'].items() if k != 'es'}}), 'guardar el escaparate')
            srv.sql('UPDATE centers SET description=? WHERE name=?', (es['description'], data_['name']))
        srv.sql("""UPDATE centers SET logo_url='/img/demo/bahia-coralina.png',logo_consent=1,cover_url='/img/portada/portada-arrecife.webp',gallery_json=?,
                   country='España',region='Alicante',cancel_free_hours=48,cancel_refund_pct=50,specialties='Nitrox, cursos, fotografía submarina',
                   address='Puerto de Xàbia, pantalán 3',latitude=38.7955,longitude=0.1876,
                   stripe_account_id='acct_test_pruebas',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?""",
                (json.dumps(['/img/portada/buceadores.webp', '/img/portada/fondosuperior.webp', '/img/portada/fondo1.webp', '/img/portada/logbook1.webp']), cid))
        srv.sql("""UPDATE centers SET logo_url='/img/demo/escafandra-medes.png',logo_consent=1,cover_url='/img/portada/fondo.webp',gallery_json=?,
                   country='España',region='Girona',cancel_free_hours=24,cancel_refund_pct=100,specialties='Reserva marina, inmersiones nocturnas, cursos',
                   address='Passeig Marítim, L''Estartit',latitude=42.0530,longitude=3.2050,
                   stripe_account_id='acct_test_pruebas2',stripe_charges_enabled=1,stripe_payouts_enabled=1 WHERE id=?""",
                (json.dumps(['/img/portada/fondosuperior.webp', '/img/portada/buceadores.webp', '/img/portada/portada-arrecife.webp']), cid2))
        # Dive sites of each centre
        pid_of = {r['name']: r['id'] for r in srv.sql('SELECT id,name FROM dive_points WHERE active=1')}
        for cl, names in ((center, POINTS_BAHIA), (center2, POINTS_MEDES)):
            for name in names:
                if name in pid_of: ok(cl.post('/api/center-points/assign', {'dive_point_id': pid_of[name]}), 'añadir ' + name)

        # --- services, seasonal prices and today's planning -----------------------------------------------------
        def services(cl, plan):
            out = {}
            for key, data_ in plan:
                mode = data_['booking_mode']
                out[key] = ok(cl.post('/api/provider-services', {**data_, 'booking_mode': 'request', 'cancel_free_hours': 48, 'cancel_refund_pct': 50}), 'crear ' + data_['title'])['id']
                if mode == 'payment': srv.sql("UPDATE provider_services SET booking_mode='payment' WHERE id=?", (out[key],))
            return out
        svc = services(center, (
            ('simple', {'title': 'Inmersión simple en barco', 'price': 45, 'max_participants': 10, 'booking_mode': 'payment', 'service_type': 'inmersion',
                        'duration_minutes': 120, 'description': 'Una inmersión guiada en la reserva marina. Botella y lastre incluidos.'}),
            ('doble', {'title': 'Doble inmersión en barco', 'price': 75, 'max_participants': 10, 'booking_mode': 'request', 'service_type': 'inmersion',
                       'duration_minutes': 240, 'description': 'Dos inmersiones en la reserva marina, guía y botellas incluidas.'}),
            ('bautizo', {'title': 'Bautizo de buceo', 'price': 60, 'max_participants': 6, 'booking_mode': 'payment', 'service_type': 'experiencia',
                         'duration_minutes': 150, 'description': 'Primera inmersión con instructor, en aguas tranquilas. Sin titulación.'}),
            ('curso', {'title': 'Curso Open Water (3 días)', 'price': 390, 'max_participants': 4, 'booking_mode': 'request', 'service_type': 'curso',
                       'duration_minutes': 480, 'description': 'Tres días: teoría, piscina y 4 inmersiones en el mar. Material y certificación incluidos. Se reserva el primer día.'}),
            ('nitrox', {'title': 'Curso de Nitrox', 'price': 160, 'max_participants': 6, 'booking_mode': 'request', 'service_type': 'curso',
                        'duration_minutes': 240, 'description': 'Teoría, análisis de botellas y dos inmersiones con aire enriquecido.'}),
            ('alquiler', {'title': 'Alquiler de equipo completo', 'price': 25, 'max_participants': 12, 'booking_mode': 'request', 'service_type': 'alquiler_equipo',
                          'duration_minutes': 480, 'description': 'Jacket, regulador, traje, máscara y aletas para un día.'})))
        svc2 = services(center2, (
            ('medas', {'title': 'Inmersión en las Islas Medas', 'price': 55, 'max_participants': 12, 'booking_mode': 'request', 'service_type': 'inmersion',
                       'duration_minutes': 150, 'description': 'Inmersión guiada en la reserva marina de las Medas. Tasa de la reserva incluida.'}),
            ('nocturna', {'title': 'Inmersión nocturna', 'price': 65, 'max_participants': 8, 'booking_mode': 'request', 'service_type': 'inmersion',
                          'duration_minutes': 120, 'description': 'Salida al atardecer con linterna incluida.'}),
            ('bautizo', {'title': 'Bautizo en las Medas', 'price': 70, 'max_participants': 4, 'booking_mode': 'payment', 'service_type': 'experiencia',
                         'duration_minutes': 150, 'description': 'Tu primera inmersión, con un instructor para dos personas como máximo.'}),
            ('advanced', {'title': 'Curso Advanced (2 días)', 'price': 320, 'max_participants': 4, 'booking_mode': 'request', 'service_type': 'curso',
                          'duration_minutes': 480, 'description': 'Cinco inmersiones de aventura: profunda, navegación, nocturna, pecio y flotabilidad.'}),
            ('snorkel', {'title': 'Snorkel guiado en las Medas', 'price': 30, 'max_participants': 10, 'booking_mode': 'payment', 'service_type': 'experiencia',
                         'duration_minutes': 120, 'description': 'Recorrido en superficie con guía, aletas y máscara incluidas.'})))
        # Seasonal prices (tariff history): low season since January, high season in summer, low season again since October
        # and next summer already announced. The price that applies is the one in force on the day of the booking.
        y = today.year
        for cl, sid, low, high in ((center, svc['simple'], 42, 49), (center, svc['doble'], 70, 82), (center, svc['bautizo'], 55, 65),
                                   (center2, svc2['medas'], 50, 60), (center2, svc2['nocturna'], 60, 70)):
            schedule = ((f'{y}-01-10', low), (f'{y}-06-15', high), (f'{y}-10-01', low), (f'{y + 1}-06-15', high))
            for frm, price in schedule:
                ok(cl.post('/api/center/tariffs/save', {'service_id': sid, 'price': price, 'effective_from': frm}), 'guardar la tarifa de temporada')
            # the price saved when the service was created (today) gives way to the season's one
            in_force = max((p for p in schedule if p[0] <= day(0)), default=schedule[0])[1]
            srv.sql('DELETE FROM center_tariffs WHERE service_id=? AND effective_from=? AND effective_from NOT IN (?,?,?,?)', (sid, day(0), *(p[0] for p in schedule)))
            srv.sql('UPDATE provider_services SET price=? WHERE id=?', (in_force, sid))
        price_of = {r['id']: r['price'] for r in srv.sql('SELECT id,price FROM provider_services')}

        # v50.55: each boat departure goes to one of the centre's dive sites (the point page lists them: «Ver salidas aquí»)
        pts1 = [pid_of[n] for n in POINTS_BAHIA if n in pid_of]; pts2 = [pid_of[n] for n in POINTS_MEDES if n in pid_of]
        to_point = lambda pts, key, k: {'dive_point_ids': [pts[k % len(pts)]]} if pts and key in ('simple', 'doble', 'nitrox', 'medas', 'nocturna') else {}
        slots = {}
        times = {'simple': '09:00', 'doble': '08:30', 'bautizo': '16:00', 'curso': '09:00', 'nitrox': '10:00', 'alquiler': '08:00'}
        spots = {'simple': 10, 'doble': 10, 'bautizo': 6, 'curso': 4, 'nitrox': 6, 'alquiler': 12}
        for k in (1, 2, 3, 4, 6, 8, 9, 10, 13, 16, 20, 27, 34, 41, 48, 55):          # the next two months
            for key, sid in svc.items():
                if key == 'curso' and k not in (3, 10, 27, 41): continue
                if key == 'nitrox' and k not in (6, 20, 48): continue
                slots[(key, k)] = ok(center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': day(k), 'slot_time': times[key], 'spots_total': spots[key], **to_point(pts1, key, k)}),
                                     'crear una salida')['slot_id']
        slots2 = {}
        for k in (1, 2, 3, 5, 9, 12, 16, 23, 30, 37, 44):
            for key, tm, sp in (('medas', '10:00', 12), ('nocturna', '20:30', 8), ('bautizo', '11:30', 4), ('snorkel', '17:00', 10)):
                if key == 'bautizo' and k % 2 == 0: continue
                slots2[(key, k)] = ok(center2.post('/api/provider-services/slot', {'service_id': svc2[key], 'slot_date': day(k), 'slot_time': tm, 'spots_total': sp, **to_point(pts2, key, k)}), 'salida')['slot_id']
            if k in (9, 30):
                slots2[('advanced', k)] = ok(center2.post('/api/provider-services/slot', {'service_id': svc2['advanced'], 'slot_date': day(k), 'slot_time': '09:00', 'spots_total': 4}), 'salida')['slot_id']
        ok(center.post('/api/manifest/boats/save', {'name': 'Neptuno', 'capacity': 12}), 'crear el barco')
        ok(center.post('/api/manifest/boats/save', {'name': 'Posidonia', 'capacity': 8}), 'crear el segundo barco')
        ok(center2.post('/api/manifest/boats/save', {'name': 'Medusa', 'capacity': 12}), 'crear el barco del segundo centro')

        # --- the team of each centre (roles made in the web) -----------------------------------------------------
        def join(cl, key, role):
            u, e, n = ACCOUNTS[key]
            ok(cl.post('/api/center/team/invite', {'email': e, 'member_role': role}), 'invitar a ' + n)
            mail = srv.sql("SELECT html FROM email_outbox WHERE template='team_invite' AND to_email=? ORDER BY id DESC LIMIT 1", (e,))[0]['html']
            token = re.search(r'#/equipo\?token=([A-Za-z0-9_-]+)', mail).group(1)
            ok(c().post('/api/team/join', {'token': token, 'fullname': n, 'username': u, 'password': pw, 'accept_terms': True}), 'dar de alta a ' + n)
        join(center, 'instructor', 'instructor')
        master_role = ok(center.post('/api/center/team/roles/save', {'name': 'Instructor máster', 'permissions': ['checkin', 'todas_salidas', 'barco', 'estadisticas']}), 'crear el perfil')['key']
        join(center, 'master', master_role)
        join(center2, 'instructor2', 'instructor')
        join(center2, 'recepcion', 'reception')                                         # a base profile of the web (wod.roles.BASE)

        # --- months of history: past departures, check-ins, payments, no-shows and cancellations ---------------------
        # Written straight into the database (the API does not create departures in the past). Same rules as the web:
        # a departure belongs to a service of its centre, a booking to its departure, a check-in to its booking.
        plan = {cid: [('doble', (5, 6), '08:30', 10), ('simple', (1, 3, 5), '09:00', 10), ('bautizo', (5,), '16:00', 6), ('curso', (0,), '09:00', 4)],
                cid2: [('medas', (2, 4, 5, 6), '10:00', 12), ('nocturna', (4,), '20:30', 8), ('bautizo', (5,), '11:30', 4), ('snorkel', (5, 6), '17:00', 10)]}
        sid_of = {cid: svc, cid2: svc2}
        pool = diver_ids[:]                                                    # every diver books now and then
        regulars = {cid: diver_ids[:9], cid2: diver_ids[0:4] + diver_ids[9:16]}   # some divers are regulars of a centre (some of both)
        links, history = {}, {cid: 0, cid2: 0}
        cif = cifrado_for(srv.env)
        hdb = sqlite3.connect(srv.db, timeout=30); hdb.execute('PRAGMA foreign_keys=ON')
        hdb.create_function('wod_cifrar', 1, cif.sql_encrypt); hdb.create_function('wod_huella', 1, cif.sql_fingerprint)
        q = lambda sql_, args=(): hdb.execute(sql_, args)
        names = {r[0]: r[1] for r in q("SELECT id,fullname FROM users WHERE role='recreational'")}
        for back in range(HISTORY_DAYS, 0, -1):
            d = today - dt.timedelta(days=back)
            for ccid, runs in plan.items():
                for key, weekdays, tm, cap in runs:
                    if d.weekday() not in weekdays and not (d.month in (7, 8) and key in ('doble', 'medas', 'simple') and d.weekday() < 5): continue
                    if rnd.random() < .07: continue                           # wind: no departure
                    sid = sid_of[ccid][key]; price = price_of[sid] if d.month in (6, 7, 8, 9) else price_of[sid] * .92
                    wanted = max(1, min(cap, int(rnd.gauss(cap * .3 * season(d), 1.2))))
                    slot_id = q('''INSERT INTO service_slots(service_id,slot_date,slot_time,spots_total,spots_available,status,created_at,updated_at)
                                   VALUES(?,?,?,?,?,?,?,?)''', (sid, d.isoformat(), tm, cap, max(0, cap - wanted), 'full' if wanted >= cap else 'open',
                                                                f'{d - dt.timedelta(days=20)}T10:00:00', f'{d}T{tm}:00')).lastrowid
                    people = rnd.sample(regulars[ccid], min(len(regulars[ccid]), max(1, wanted // 2))) + rnd.sample(pool, 1)
                    seats = 0
                    for uid in dict.fromkeys(people):
                        if seats >= wanted: break
                        pax = 2 if rnd.random() < .3 and seats + 2 <= wanted else 1; seats += pax
                        made = d - dt.timedelta(days=rnd.randint(1, 25))
                        r = rnd.random()
                        status, pay = ('cancelled', 'refunded') if r < .05 else ('completed', 'paid' if r < .62 else 'at_center')
                        bid = q('''INSERT INTO bookings(user_id,center_id,booking_date,booking_time,participants,status,created_at,updated_at,service_id,price,currency,
                                   payment_status,payment_method,amount_paid,slot_id,slot_reserved,confirmed_at,source,cancelled_at,cancelled_by)
                                   VALUES(?,?,?,?,?,?,?,?,?,?,'EUR',?,?,?,?,1,?,?,?,?)''',
                                      (uid, ccid, d.isoformat(), tm, pax, status, f'{made}T{rnd.randint(8, 22):02d}:{rnd.randint(0, 59):02d}:00', f'{d}T{tm}:00', sid,
                                       round(price * pax, 2), pay, 'card' if pay in ('paid', 'refunded') else 'cash', round(price * pax, 2) if pay != 'refunded' else 0,
                                       slot_id, f'{made}T21:00:00', 'web', f'{d - dt.timedelta(days=2)}T12:00:00' if status == 'cancelled' else None,
                                       uid if status == 'cancelled' else None)).lastrowid
                        if status == 'cancelled': continue
                        history[ccid] += 1
                        noshow = rnd.random() < .03
                        name = names[uid]
                        for seat in range(pax):
                            q('''INSERT INTO manifest_entries(booking_id,seat,slot_id,name,checked_in_at,no_show,updated_at,checkin_source)
                                       VALUES(?,?,?,?,?,?,?,?)''', (bid, seat, slot_id, name if seat == 0 else f'{name} (acompañante)', None if noshow else f'{d}T{tm}:00',
                                                                  1 if noshow else 0, f'{d}T{tm}:00', 'online'))
                        if not noshow:
                            first, last = links.get((uid, ccid), (d, d)); links[(uid, ccid)] = (min(first, d), max(last, d))
        for (uid, ccid), (first, last) in links.items():
            q('INSERT INTO center_links(user_id,center_id,first_checkin,last_checkin) VALUES(?,?,?,?)', (uid, ccid, f'{first}T09:00:00', f'{last}T09:00:00'))
        print(f'Historial: {history[cid]} reservas en {bahia["name"]}, {history[cid2]} en {medes["name"]}', flush=True)

        # --- visits of the public pages, clicks on «Reservar» and information requests (Estadísticas) ---------------
        # v50.57 (4.2): the same visitors in the counter of «Actividad» and «Estadísticas» (visit_counts: pages seen and
        # visitors of each day), with a generator of its own so that the rest of the demo stays the same
        vrnd, site = random.Random(4242), {}
        for ptype, pid, base in (('center', cid, 46), ('center', cid2, 34), ('freelance', pro_id, 14), ('freelance', pro2_id, 11)):
            for back in range(HISTORY_DAYS, -1, -1):
                d = today - dt.timedelta(days=back)
                views = max(0, int(rnd.gauss(base * season(d), base * .18)))
                q('INSERT OR REPLACE INTO provider_stats_daily(provider_type,provider_id,day,views,book_clicks,info_requests) VALUES(?,?,?,?,?,?)',
                  (ptype, pid, d.isoformat(), views, int(views * rnd.uniform(.06, .11)), int(views * rnd.uniform(.0, .025))))
                q('INSERT OR REPLACE INTO visit_counts(day,scope,views,uniques) VALUES(?,?,?,?)', (d.isoformat(), f'{ptype}:{pid}', int(views * vrnd.uniform(1.2, 1.6)), views))
                site[d] = site.get(d, 0) + views
        for d, n in site.items():   # the whole web: more visitors than the four pages, about three pages each
            u = int(n * vrnd.uniform(2.2, 2.8)); q('INSERT OR REPLACE INTO visit_counts(day,scope,views,uniques) VALUES(?,?,?,?)', (d.isoformat(), 'site', int(u * vrnd.uniform(2.6, 3.4)), u))
        hdb.commit(); hdb.close()

        # --- reviews of divers who dived with each centre, and the centre's replies ---------------------------------
        texts = DATA['reviews'][:]
        for ccid, cl, n_ in ((cid, center, 9), (cid2, center2, 6)):
            who = [uid for (uid, x) in links if x == ccid][:n_]
            for i, uid in enumerate(who):
                rating, title, body = texts[(i * 2 + (ccid % 2)) % len(texts)]
                ok(divers[diver_ids.index(uid)].post(f'/api/centers/{ccid}/reviews', {'rating': rating, 'title': title, 'body': body}), 'publicar una reseña')
            for k, row in enumerate(srv.sql('SELECT id,rating FROM center_reviews WHERE center_id=? ORDER BY id', (ccid,))):
                if k % 2 == 0 or row['rating'] <= 3:
                    reply = DATA['replies'][2] if row['rating'] <= 3 else DATA['replies'][k % 2]
                    ok(cl.post(f"/api/reviews/{row['id']}/reply", {'body': reply}), 'responder a la reseña')
            srv.sql("UPDATE center_reviews SET created_at=datetime('now','-'||(abs(random())%120)||' days'),updated_at=created_at WHERE center_id=?", (ccid,))

        # --- the demo diver's bookings in every state (with the first centre) ---------------------------------------
        def book(diver, key, k, pax=1):
            return ok(diver.post('/api/bookings', {'center_id': cid, 'service_id': svc[key], 'slot_id': slots[(key, k)], 'participants': pax}), 'reservar')['id']
        book(buzo, 'doble', 9, 2)                                                       # solicitada
        b_conf = book(buzo, 'doble', 4, 2); ok(center.post(f'/api/bookings/{b_conf}/status', {'status': 'confirmed'}), 'confirmar')   # confirmada
        b_pend = book(buzo, 'curso', 10)                                                # aceptada, pendiente de pago
        srv.sql("UPDATE bookings SET status='accepted_pending_payment',payment_status='required',payment_deadline=?,accepted_at=? WHERE id=?",
                ((dt.datetime.now() + dt.timedelta(days=2)).isoformat(timespec='minutes'), now_s(), b_pend))
        b_canc = book(buzo, 'doble', 16); ok(center.post(f'/api/bookings/{b_canc}/status', {'status': 'confirmed'}), 'confirmar')
        ok(center.post(f'/api/bookings/{b_canc}/status', {'status': 'cancelled', 'reason': 'Temporal previsto: el centro cancela la salida'}), 'cancelar')   # cancelada
        b_rej = book(buzo, 'alquiler', 20); ok(center.post(f'/api/bookings/{b_rej}/status', {'status': 'rejected', 'reason': 'No quedan trajes de tu talla ese día'}), 'rechazar')
        b_paid = book(buzo, 'doble', 6)                                                 # pagada online (pago de prueba)
        srv.sql("UPDATE bookings SET status='confirmed',payment_status='paid',payment_method='card',amount_paid=price,confirmed_at=? WHERE id=?", (now_s(), b_paid))
        b_exp = book(buzo, 'doble', 27)                                                 # caducada (no se pagó a tiempo)
        srv.sql("UPDATE bookings SET status='expired',payment_status='required' WHERE id=?", (b_exp,))
        b_done = book(buzo, 'doble', 1)                                                 # completada (en el pasado)
        srv.sql("UPDATE bookings SET status='completed',booking_date=?,confirmed_at=? WHERE id=?", (day(-8), now_s(), b_done))
        # Other divers in the next weeks (both centres; each centre only sees its own bookings)
        for i, d_ in enumerate(divers[1:13], start=1):
            for key, k in (('doble', (2, 4, 9, 13)[i % 4]), ('alquiler', (1, 3, 8, 10)[i % 4])):
                if rnd.random() < .55:
                    x = book(d_, key, k, 1 + (i % 2)); ok(center.post(f'/api/bookings/{x}/status', {'status': 'confirmed'}), 'confirmar')
        for i, d_ in enumerate(divers[:12]):
            key, k = (('medas', 5), ('nocturna', 9), ('medas', 2), ('nocturna', 3), ('medas', 16), ('nocturna', 16))[i % 6]
            x = ok(d_.post('/api/bookings', {'center_id': cid2, 'service_id': svc2[key], 'slot_id': slots2[(key, k)], 'participants': 1}), 'reservar en el segundo centro')['id']
            if i % 5: ok(center2.post(f'/api/bookings/{x}/status', {'status': 'confirmed'}), 'confirmar en el segundo centro')   # some wait for an answer
        # v50.56 · Motor multicanal: Bahía Coralina sells in its own website too (the example website of README-PRUEBAS,
        # http://localhost:8101, served by «iniciar --pruebas»), with its page /c/bahia-coralina and its colour.
        ok(center.post('/api/provider/vender', {'slug': 'bahia-coralina', 'color': '#0b7a75', 'domains': ['localhost:8101', '127.0.0.1:8101']}), 'vender en tu web')
        ok(center2.post('/api/provider/vender', {'slug': 'escafandra-medes', 'color': '#8a4b12'}), 'página de reservas')
        # A small departure every day (2 spots), for README-PRUEBAS «Probar el motor multicanal»: book on the example
        # website, take the last spot from WORLDIVES and see «Completo» in the widget.
        snorkel = ok(center.post('/api/provider-services', {'title': 'Snorkel en la Granadella', 'price': 30, 'max_participants': 2, 'booking_mode': 'request',
                                                             'service_type': 'experiencia', 'duration_minutes': 90,
                                                             'description': 'Snorkel con guía en la cala de la Granadella. Gafas, tubo y aletas incluidos.'}),
                     'crear el snorkel')['id']
        for k in range(1, 11):
            ok(center.post('/api/provider-services/slot', {'service_id': snorkel, 'slot_date': day(k), 'slot_time': '11:00', 'spots_total': 2}), 'salida de snorkel')
        # v50.56 · Bloque 2 (seguros): two test insurers configured in Administración → Seguros (no insurer is in the code),
        # that open a test page (example.com and example.org are reserved for examples); buzo.prueba with an EXPIRED policy,
        # buzo2.prueba with a VALID one; and a service of Bahía Coralina «obligatorio para reservar online»
        # (README-PRUEBAS «Probar los seguros», with docs/pruebas/poliza-de-prueba.pdf).
        for name, dom, code in (('Aseguradora Demo A', 'example.com', 'WD-DEMO-A'), ('Aseguradora Demo B', 'example.org', 'WD-DEMO-B')):
            prov = ok(admin.post('/api/admin/insurance/providers', {'name': name, 'allowed_domains': dom, 'website': f'https://{dom}/', 'partner_code': code,
                                                                     'collaborator': True, 'active': True}), 'aseguradora de prueba')['id']
            for kind, pname, price in (('dia', 'Seguro de buceo de un día', 6 if dom == 'example.com' else 7.5), ('semana', 'Seguro de buceo de una semana', 19),
                                       ('anio', 'Seguro de buceo anual', 59 if dom == 'example.com' else 64), ('rc_centro', 'RC para centros de buceo', 390)):
                url = f'https://{dom}/?seguro={kind}&colaborador={{codigo}}'
                ok(admin.post('/api/admin/insurance/products', {'provider_id': prov, 'kind': kind, 'name': pname, 'price_from': price, 'zones': ['europa', 'mundo'],
                                                                **({'center_url': url} if kind == 'rc_centro' else {'diver_url': url, 'center_url': url + '&para=centro'})}),
                   'producto de prueba')
        poliza = demo_pdf('Aseguradora Demo A', 'Poliza de seguro de buceo')
        ok(buzo.upload('/api/insurance/policies', {'insurer': 'Aseguradora Demo A', 'policy_number': 'DA-2025-0412', 'kind': 'anio', 'valid_from': day(-400),
                                                   'valid_to': day(-35), 'zone': 'europa', 'max_depth': '30'}, 'poliza.pdf', poliza), 'seguro caducado de buzo.prueba')
        ok(divers[1].upload('/api/insurance/policies', {'insurer': 'Aseguradora Demo B', 'policy_number': 'DB-77-1093', 'kind': 'anio', 'valid_from': day(-60),
                                                        'valid_to': day(305), 'zone': 'mundo', 'max_depth': '40'}, 'poliza.pdf', poliza), 'seguro vigente de buzo2.prueba')
        guiada = ok(center.post('/api/provider-services', {'title': 'Inmersión guiada en la Granadella', 'price': 45, 'max_participants': 6, 'booking_mode': 'request',
                                                           'service_type': 'inmersion', 'duration_minutes': 120, 'insurance_required': 'online',
                                                           'description': 'Inmersión con guía desde la cala. Para reservar online hace falta un seguro de buceo válido ese día.'}),
                    'crear la inmersión con seguro obligatorio')['id']
        for k in range(1, 11):
            ok(center.post('/api/provider-services/slot', {'service_id': guiada, 'slot_date': day(k), 'slot_time': '10:00', 'spots_total': 6}), 'salida de la inmersión guiada')
        # The files of these policies stay in this temporary server: in the demo they are listed without a document
        srv.sql('UPDATE insurance_policies SET file_path=NULL,original_name=NULL')
        # v50.49 (app Centro PRO): an evening dive every day of the week with divers, so «Hoy» has a boat list whatever
        # day the tester opens the app (the demo is rebuilt every 7 days), and a request that expires soon.
        # v50.54: the hour of the centre (Spain), not of the computer: at 20:00 UTC the 21:30 departure of Xàbia has
        # already started (UTC+2) and the demo could not be built in the evening.
        from zoneinfo import ZoneInfo
        local = dt.datetime.now(ZoneInfo('Europe/Madrid'))
        late = local.hour < 21 and local.date() == dt.date.today()
        tarde = ok(center.post('/api/provider-services', {'title': 'Inmersión al atardecer', 'price': 50, 'max_participants': 10, 'booking_mode': 'request', 'service_type': 'inmersion',
                                                          'duration_minutes': 120, 'description': 'Una inmersión cuando baja el sol. Linterna incluida.'}), 'crear la inmersión al atardecer')['id']
        for k in range(0 if late else 1, 8):
            sl = ok(center.post('/api/provider-services/slot', {'service_id': tarde, 'slot_date': day(k), 'slot_time': '21:30' if k == 0 else '18:30', 'spots_total': 10}),
                    'crear la salida del atardecer')['slot_id']
            # Today: three divers (four seats), so there is always someone left to mark on the boat list.
            for i, d_ in enumerate(divers[1:4] if k == 0 else divers[1:2 + k % 4]):
                x = ok(d_.post('/api/bookings', {'center_id': cid, 'service_id': tarde, 'slot_id': sl, 'participants': 1 + ((k + i) % 2)}), 'reservar al atardecer')['id']
                ok(center.post(f'/api/bookings/{x}/status', {'status': 'confirmed'}), 'confirmar')
            if k == 1:
                x = ok(divers[5].post('/api/bookings', {'center_id': cid, 'service_id': tarde, 'slot_id': sl, 'participants': 2, 'notes': 'Venimos dos amigos, uno sin experiencia nocturna'}), 'solicitar')['id']
                srv.sql('UPDATE bookings SET response_deadline=? WHERE id=?', ((dt.datetime.now() + dt.timedelta(hours=2)).isoformat(timespec='minutes'), x))
        for k, site, depth in ((-8, 'Cabo San Antonio', 18), (-35, 'Portitxol Norte', 22), (-60, 'Cabo San Martín', 12), (-95, 'Islas Medes', 24)):
            ok(buzo.post('/api/logbook', {'dive_date': day(k), 'site': site, 'country': 'España', 'depth': depth, 'duration': 48, 'dive_type': 'Barco',
                                          'notes': 'Mucha vida y buena visibilidad.'}), 'apuntar en el Log Book')

        # --- the two freelance instructors ---------------------------------------------------------------------------
        srv.sql("UPDATE users SET avatar_url='/img/portada/logbook1.webp',provider_bio='Guía e instructor en los cenotes de la Riviera Maya desde 2012.' WHERE id=?", (pro_id,))
        # v50.55: both freelance instructors are paid in person (no Stripe): ways of paying, WhatsApp and their own policy.
        ip1 = {'pay_way': 'in_person', 'pay_methods': ['cash', 'transfer'], 'pay_whatsapp': '+52 998 000 0101', 'accept_in_person_terms': True,
               'pay_policy': 'Cancelación gratuita hasta 48 horas antes. Después, se paga la mitad del precio.'}
        ip2 = {'pay_way': 'in_person', 'pay_methods': ['bizum', 'cash'], 'pay_whatsapp': '+34 611 222 333', 'accept_in_person_terms': True}
        days_sid = ok(pro.post('/api/provider-services', {'title': 'Cenotes con guía, por días', 'price': 180, 'max_participants': 4, 'booking_mode': 'request', **ip1,
                                                          'booking_unit': 'day', 'timezone': 'America/Cancun',
                                                          'description': 'Guía titulado, dos cenotes por día. Punto de encuentro: hotel en Tulum.',
                                                          'unit_rules': {'min_days': 1, 'max_days': 10, 'lead_hours': 24},
                                                          'pricing': {'day': 180, 'discount': {'min_days': 3, 'pct': 10}}}), 'crear el servicio por días')['id']
        half_sid = ok(pro.post('/api/provider-services', {'title': 'Cenote por la mañana o por la tarde', 'price': 110, 'max_participants': 4, 'booking_mode': 'request', **ip1,
                                                          'booking_unit': 'half_day', 'timezone': 'America/Cancun',
                                                          'description': 'Medio día: un cenote con guía, transporte desde Tulum.',
                                                          'unit_rules': {'min_days': 1, 'max_days': 5, 'lead_hours': 24},
                                                          'pricing': {'day': 200, 'half': 110}}), 'crear el servicio de medio día')['id']
        foto_sid = ok(pro.post('/api/provider-services', {'title': 'Sesión de fotos y vídeo bajo el agua', 'price': 90, 'max_participants': 2, 'booking_mode': 'request', **ip1,
                                                          'service_type': 'experiencia', 'duration_minutes': 180,
                                                          'description': 'Fotos y vídeo de tu inmersión en un cenote. Entrega en 48 horas.'}), 'crear la sesión de fotos')['id']
        for k in (4, 11, 18, 25):
            ok(pro.post('/api/provider-services/slot', {'service_id': foto_sid, 'slot_date': day(k), 'slot_time': '11:00', 'spots_total': 2}), 'crear una sesión')
        pro.post('/api/agenda/hours', {'weekdays': [0, 1, 2, 3, 4, 5], 'closures': [], 'timezone': 'America/Cancun'})
        pro.post('/api/agenda/block', {'date_from': day(12), 'date_to': day(14), 'kind': 'holiday'})
        holiday = range(12, 15)
        b = ok(divers[1].post('/api/bookings', {'service_id': days_sid, 'days': workdays(3, 2, holiday), 'part': 'full', 'participants': 2, 'notes': 'Primera vez en cenotes', 'in_person_ack': True}), 'reservar días')
        ok(pro.post(f"/api/bookings/{b['id']}/status", {'status': 'confirmed'}), 'confirmar días')
        ok(pro.post('/api/pro-mark', {'kind': 'booking', 'id': b['id'], 'mark': 'paid'}), 'marcar «Cobrado»')
        ok(divers[2].post('/api/bookings', {'service_id': half_sid, 'days': workdays(8, 1, holiday), 'part': 'am', 'participants': 1, 'in_person_ack': True}), 'reservar medio día')
        ok(buzo.post('/api/bookings', {'service_id': days_sid, 'days': workdays(18, 3, holiday), 'part': 'full', 'participants': 2, 'in_person_ack': True}), 'reservar tres días')
        # Sara Molina: guide and underwater photographer on the Costa Blanca (half days and a two-day course)
        srv.sql("UPDATE users SET avatar_url='/img/portada/buceadores.webp',provider_bio='Instructora y fotógrafa submarina en la Costa Blanca. Guías privadas y cursos de foto en grupos de dos.' WHERE id=?", (pro2_id,))
        guia = ok(pro2.post('/api/provider-services', {'title': 'Guía privada en Xàbia (medio día)', 'price': 85, 'max_participants': 2, 'booking_mode': 'request', **ip2,
                                                       'booking_unit': 'half_day', 'timezone': 'Europe/Madrid',
                                                       'description': 'Inmersión desde la orilla o en barco con un centro de la zona. Te guío y te hago las fotos.',
                                                       'unit_rules': {'min_days': 1, 'max_days': 4, 'lead_hours': 24}, 'pricing': {'day': 150, 'half': 85}}), 'crear la guía privada')['id']
        fotos = ok(pro2.post('/api/provider-services', {'title': 'Curso de fotografía submarina (2 días)', 'price': 240, 'max_participants': 2, 'booking_mode': 'request', **ip2,
                                                        'booking_unit': 'day', 'timezone': 'Europe/Madrid',
                                                        'description': 'Cámara, luz y composición bajo el agua. Incluye cuatro inmersiones y la revisión de tus fotos.',
                                                        'unit_rules': {'min_days': 2, 'max_days': 2, 'lead_hours': 48}, 'pricing': {'day': 120}}), 'crear el curso de foto')['id']
        pro2.post('/api/agenda/hours', {'weekdays': [0, 1, 2, 3, 4, 5], 'closures': [], 'timezone': 'Europe/Madrid'})
        x = ok(divers[6].post('/api/bookings', {'service_id': guia, 'days': workdays(5, 1), 'part': 'am', 'participants': 2, 'in_person_ack': True}), 'reservar la guía')
        ok(pro2.post(f"/api/bookings/{x['id']}/status", {'status': 'confirmed'}), 'confirmar la guía')
        ok(divers[10].post('/api/bookings', {'service_id': fotos, 'days': workdays(15, 2), 'part': 'full', 'participants': 1, 'notes': 'Tengo una cámara compacta con carcasa', 'in_person_ack': True}), 'reservar el curso')

        # v50.53: every demo service starts from its template (the same rule the migration uses for existing services),
        # so its card shows the template's photo and changes with it.
        sys.path.insert(0, str(ROOT / 'app'))
        from wod.plantillas import guess_slug
        slug_id = {r['slug']: r['id'] for r in srv.sql('SELECT id,slug FROM service_catalog')}
        for r in srv.sql('SELECT id,title,service_type FROM provider_services WHERE template_id IS NULL'):
            tid = slug_id.get(guess_slug(r['title'], r['service_type']))
            if tid: srv.sql('UPDATE provider_services SET template_id=? WHERE id=?', (tid, r['id']))

        # --- experiences: published and one waiting for review ----------------------------------------------------
        ok(center2.post('/api/travel-experiences', {'new_destination': 'Islas Medas', 'new_destination_region': 'España', 'title': 'Fin de semana en las Medas',
                                                    'start_date': day(23), 'end_date': day(24), 'price': 240, 'spots_total': 8, 'spots_available': 8,
                                                    'includes': '4 inmersiones, guía y botellas', 'summary': 'Dos días de buceo en la reserva marina.'}), 'crear experiencia')
        exp1 = srv.sql("SELECT id FROM travel_experiences ORDER BY id DESC LIMIT 1")[0]['id']
        ok(center.post('/api/travel-experiences', {'new_destination': 'Costa Blanca', 'new_destination_region': 'España', 'title': 'Tres días en la reserva del Cabo de San Antonio',
                                                   'start_date': day(31), 'end_date': day(33), 'price': 290, 'spots_total': 8, 'spots_available': 8,
                                                   'includes': '6 inmersiones, guía, botellas y nitrox', 'summary': 'Paredes, cuevas y la Montaña Sumergida.'}), 'crear experiencia')
        exp3 = srv.sql("SELECT id FROM travel_experiences ORDER BY id DESC LIMIT 1")[0]['id']
        offer = srv.sql("SELECT id FROM travel_offers WHERE title LIKE 'Riviera Maya%' LIMIT 1") or srv.sql("SELECT id FROM travel_offers ORDER BY id DESC LIMIT 1")
        offer = offer[0]['id']
        ok(pro.post('/api/travel-experiences', {'travel_offer_id': offer, 'title': 'Vida a bordo en el Caribe mexicano', 'start_date': day(45), 'end_date': day(51), **ip1,
                                                'price': 1450, 'spots_total': 12, 'spots_available': 12, 'includes': '6 noches, 15 inmersiones, pensión completa'}), 'crear el vida a bordo')
        exp2 = srv.sql("SELECT id FROM travel_experiences ORDER BY id DESC LIMIT 1")[0]['id']
        for x in (exp1, exp2, exp3): ok(admin.post('/api/admin/travel-experiences/status', {'id': x, 'status': 'published'}), 'publicar la experiencia')
        ok(pro.post('/api/travel-experiences', {'travel_offer_id': offer, 'title': 'Semana de cenotes y cavernas', 'start_date': day(60), 'end_date': day(66), **ip1,
                                                'price': 890, 'spots_total': 6, 'spots_available': 6, 'includes': '10 inmersiones en cenotes, transporte'}), 'crear la experiencia por revisar')

        # --- promotions, a bono of 10 dives, a joint promotion of both centres, points and advantages -------------------
        clients1 = [uid for (uid, x) in links if x == cid]
        promo = ok(center.post('/api/center/promotions', {'title': '10 % en tu próxima inmersión', 'value_text': '10 % de descuento', 'valid_from': day(-20), 'valid_until': day(70),
                                                         'description': 'Para clientes que ya han buceado con nosotros.', 'conditions': 'Una vez por persona. No acumulable.',
                                                         'uses_per_code': 1}), 'crear la promoción')['id']
        ok(center.post(f'/api/center/promotions/{promo}/assign', {'user_ids': clients1[:10]}), 'repartir la promoción')
        bono = ok(center.post('/api/center/promotions', {'title': 'Bono 10 inmersiones', 'value_text': '10 inmersiones al precio de 8', 'valid_from': day(-60), 'valid_until': day(300),
                                                        'description': 'Inmersiones en barco durante toda la temporada.', 'conditions': 'Personal. Se descuenta una inmersión en cada salida.',
                                                        'uses_per_code': 10, 'partner_ids': [cid2]}), 'crear el bono')['id']
        ok(center.post(f'/api/center/promotions/{bono}/assign', {'user_ids': [diver_ids[0], *clients1[:3]]}), 'dar el bono')
        ok(center2.post(f'/api/center/promotions/{bono}/partner', {'action': 'accepted'}), 'aceptar la promoción conjunta')
        for code in [r['code'] for r in srv.sql('SELECT code FROM promotion_codes WHERE promotion_id=? ORDER BY id', (bono,))][:3]:
            for _ in range(rnd.randint(2, 6)): ok(center.post(f'/api/promo/{code}/redeem', {'note': 'Inmersión en barco'}), 'descontar del bono')
        clients2 = [uid for (uid, x) in links if x == cid2]
        p2 = ok(center2.post('/api/center/promotions', {'title': 'Nocturna a mitad de precio', 'value_text': '50 % en la nocturna', 'valid_from': day(-5), 'valid_until': day(45),
                                                       'description': 'Si ya has buceado de día con nosotros, la nocturna te sale a mitad de precio.', 'uses_per_code': 1}), 'crear la promoción')['id']
        ok(center2.post(f'/api/center/promotions/{p2}/assign', {'user_ids': clients2[:8]}), 'repartir la promoción')
        for cl, title, kind, cost, value in ((center, 'Inmersión gratis', 'activity', 600, 'Una inmersión en barco'), (center, 'Camiseta del centro', 'gift', 150, 'Camiseta de algodón orgánico'),
                                             (center2, 'Alquiler de linterna gratis', 'gift', 120, 'Linterna para la nocturna'), (center2, '15 % en el curso Advanced', 'course_discount', 400, '15 % de descuento')):
            ok(cl.post('/api/provider/reward-offers', {'title': title, 'reward_type': kind, 'cost_points': cost, 'value_text': value, 'active': True}), 'crear la ventaja')
        for i, uid in enumerate(clients1[:8]):
            ok(center.post('/api/provider/points-grant', {'user_id': uid, 'points': (50, 75, 100)[i % 3], 'reason': 'Gracias por bucear con nosotros'}), 'conceder puntos')
        for uid in clients2[:5]:
            ok(center2.post('/api/provider/points-grant', {'user_id': uid, 'points': 80, 'reason': 'Bienvenida a las Medes'}), 'conceder puntos')

        # --- marine life of every dive site of both centres (8–15 species each; own illustrations) ------------------------
        ok(admin.post('/api/admin/marina/ejemplos', {}), 'cargar las especies de ejemplo')
        sp = {r['example_key']: r['id'] for r in srv.sql('SELECT id,example_key FROM species WHERE example_key IS NOT NULL')}
        for name, plan_ in MARINE.items():
            if name not in pid_of: continue
            for key, freq, months in plan_:
                ok(admin.post('/api/marina/especie-punto', {'point_id': pid_of[name], 'species_id': sp[key], 'frequency': freq, 'months': months}), f'vincular {key} a {name}')
        # A proposal of the first centre that waits for the administrator (Vida marina y vídeos → Pendientes)
        ok(center.post('/api/marina/especie-punto', {'point_id': pid_of['Piedras Rotas'], 'species_id': sp['caballito'], 'frequency': 'rare', 'months': []}), 'proponer una especie')
        # Route videos only from real links you choose (data/demo/videos-demo.json): no link is ever invented.
        for v in (json.loads(VIDEOS.read_text(encoding='utf-8')) if VIDEOS.exists() else []):
            if v.get('point') in pid_of and v.get('url'):
                r = admin.post('/api/marina/video', {'point_id': pid_of[v['point']], 'url': v['url'], 'kind': v.get('kind', 'normal'), 'title': v.get('title', '')})
                print(('Vídeo añadido: ' if r.status == 200 else 'Vídeo no añadido: ') + v['url'], flush=True)

        # --- simulated WhatsApp of both centres and their notice settings ------------------------------------------------
        for key_, number in ((f'c:{cid}', '+34 600 000 101'), (f'c:{cid2}', '+34 972 000 202')):   # different at a glance: +346…01 / +349…02
            pnid = 'pruebas-' + key_.replace(':', '-')
            tpl = {f'{t}:{l}': 'APPROVED' for t in ('worldives_salida_cancelada', 'worldives_cambio_salida', 'worldives_recordatorio')
                   for l in ('es', 'en', 'fr', 'de', 'it', 'pt_PT', 'nl', 'pl', 'zh_CN')}
            srv.sql('''INSERT INTO whatsapp_accounts(provider_id,status,waba_id,phone_number_id,display_number,token,pnid_hash,number_hash,waba_hash,verified_name,coexistence,
                       templates,connected_at,updated_at) VALUES(?,'connected',?,?,?,?,?,?,?,?,1,?,?,?)''',
                    (key_, cif.encrypt_secret('pruebas-' + key_), cif.encrypt_secret(pnid), cif.encrypt_secret(cif.normalize_phone(number)), cif.encrypt_secret('pruebas'),
                     cif.keyed_hash('pnid', pnid), cif.fingerprint(number), cif.keyed_hash('waba', 'pruebas-' + key_), 'WhatsApp de prueba', json.dumps(tpl), now_s(), now_s()))
        srv.sql("INSERT OR REPLACE INTO provider_settings(provider_id,notice_policy,reminder_enabled,reminder_hour,reminder_bring,updated_at) VALUES(?,?,?,?,?,?)",
                (f'c:{cid}', 'choice', 1, 18, 'Titulación, toalla y protector solar', now_s()))

        # --- administration inbox: a centre waiting for approval, an experience to review (above) and a report ---------
        ok(c().post('/api/reports', {'reason': 'false', 'details': 'El precio que aparece en la ficha no coincide con el que me dijeron por teléfono.', 'name': 'Persona de la demo',
                                     'email': 'denuncia@example.com', 'good_faith': True, 'target_url': f'/#/centro?id={cid}'}), 'enviar la denuncia')
        u, e, n = PENDING_CENTER
        ok(c().register(n, e, u, pw, account_type='center', center_name='Arrecife Azul Dénia', phone='+34 600 000 103', city='Dénia',
                        website='https://arrecifeazul.example.com'), 'registrar el centro pendiente')

        # --- finishing touches ----------------------------------------------------------------------------------------
        srv.sql("UPDATE users SET email_verified_at=? WHERE username LIKE '%.prueba'", (now_s(),))
        srv.sql("UPDATE users SET created_at=? WHERE username LIKE '%.prueba' AND role<>'admin'", (f'{today - dt.timedelta(days=HISTORY_DAYS + 30)}T10:00:00',))
        srv.sql("UPDATE centers SET created_at=? WHERE id IN (?,?)", (f'{today - dt.timedelta(days=HISTORY_DAYS + 30)}T10:00:00', cid, cid2))
        srv.sql('DELETE FROM email_outbox')                                             # nothing waits to be sent in a fresh demo
        srv.sql("INSERT OR REPLACE INTO site_settings(key,value,updated_at) VALUES('demo_generated_on',?,?)", (day(0), now_s()))
        srv.sql("INSERT OR REPLACE INTO site_settings(key,value,updated_at) VALUES('demo_generated_version',?,?)", (app_version(), now_s()))
        from wod.security import hash_password
        srv.sql("UPDATE users SET password_hash=? WHERE username LIKE '%.prueba'", (hash_password(PASSWORD),))
        admins = [r['username'] for r in srv.sql("SELECT username FROM users WHERE role='admin'")]
        if admins != [ACCOUNTS['admin'][0]]: raise SystemExit(f'La demo solo trae su cuenta de administración de demostración: {admins}')
    except BaseException:
        srv.stop(); raise
    srv.stop(cleanup=False)
    try:
        out.parent.mkdir(parents=True, exist_ok=True)
        src = sqlite3.connect(srv.db); dst = sqlite3.connect(out)
        src.backup(dst); dst.close(); src.close()
    finally:
        shutil.rmtree(srv.tmp, ignore_errors=True)
    print(f'Base de demostración creada: {out}')


def accounts_text() -> str:
    """CUENTAS-DEMO.txt: the demo accounts and their password, outside the code of the web."""
    rows = [('Administración', 'admin'), (f'Centro «{DATA["bahia"]["name"]}» (propietaria)', 'center'), (f'Centro «{DATA["medes"]["name"]}» (propietario)', 'center2'),
            ('Instructor del primer centro', 'instructor'), ('Instructora máster del primer centro (perfil hecho en la web)', 'master'),
            ('Instructor del segundo centro', 'instructor2'), ('Recepción del segundo centro', 'recepcion'),
            ('Freelance: cenotes en México', 'freelance'), ('Freelance: guía y fotógrafa en Xàbia', 'freelance2'), ('Buceadora con reservas en todos los estados', 'diver')]
    out = ['WORLDIVES DISCOVERY · Versión de demostración · Cuentas', '',
           f'Contraseña de todas las cuentas: {PASSWORD}', 'Se entra con el usuario o con el email.', '']
    out += [f'- {label}: {ACCOUNTS[k][0]}  ({ACCOUNTS[k][1]})' for label, k in rows]
    out += ['', f'Más buceadores: buzo2.prueba … buzo{len(EXTRA_DIVERS) + 1}.prueba (misma contraseña).',
            '', 'Todo es inventado: centros, personas, reseñas y reservas. Los pagos son de prueba y los correos no salen del ordenador.',
            'Estas cuentas no existen ni deben existir en la web real.', '']
    return '\n'.join(out)


if __name__ == '__main__':
    ap = argparse.ArgumentParser(); ap.add_argument('--out', default=str(ROOT / 'data' / 'pruebas' / 'worldives-pruebas.sqlite3'))
    ap.add_argument('--cuentas', help='también escribe el archivo de cuentas (CUENTAS-DEMO.txt) en esta ruta')
    a = ap.parse_args()
    out = Path(a.out)
    if out.exists(): out.unlink()
    build(out)
    if a.cuentas: Path(a.cuentas).write_text(accounts_text(), encoding='utf-8')
