"""v50.57 · El logbook de buceo de la cuenta (componente «Dive Logbook»): servidor.

Criterios de aceptación del encargo que se prueban aquí (el navegador, con el componente real, en
tests/navegador/e2e_v50_57_logbook.py):
- los datos se guardan en la cuenta: otro dispositivo (otra sesión) ve el mismo logbook; las dos vistas comparten datos;
- el QR de una inmersión de un centro la añade verificada; escanearlo otra vez no la duplica; otro buceador no puede usarlo;
- los campos bloqueados de una inmersión verificada no se pueden cambiar ni manipulando la petición al servidor
  (ni marcar como verificada una inmersión que no lo es, ni moverla de página, ni quitar campos de la lista bloqueada);
- registrarse con el enlace de un centro guarda el centro y pone su logo en la portada;
- el QR de otro buceador crea la amistad en los dos sentidos y aparece en «Compañero» (lista de amigos);
- las inmersiones completas siguen siendo filas del Log Book (puntos, app, exportaciones) y las de reservas completadas
  no se pierden.
"""
from __future__ import annotations

import copy
import datetime as dt
import io
import json
import sys
import time
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from helpers import ServerTestCase, PNG_BYTES  # noqa: E402

TODAY = dt.date.today()
DAY = (TODAY - dt.timedelta(days=1)).isoformat()
LOCKED_DEFAULT = ['date', 'site', 'country', 'center', 'pos', 'sign']


def add_dive_from_center(book, d):
    """The same as LogbookApp.addDiveFromCenter() of logbook.js (the delivered component): first free page, the same
    fields as text, the types, and the verified mark with the locked fields that have a value."""
    book = copy.deepcopy(book)
    for n, ver in book['verified'].items():
        if ver['id'] == d['id']: return book, int(n)
    n = next(i for i in range(1, book['pages'] * 2 + 1) if not any(k.startswith(f'd:{i}:') for k in book['v']) and str(i) not in book['verified'])
    mp = {'date': d.get('date'), 'site': d.get('site'), 'country': d.get('country'), 'center': d.get('center'), 'depth': d.get('depth'), 'time': d.get('time'),
          'temp': d.get('temp'), 'vis': d.get('vis'), 'tin': d.get('timeIn'), 'tout': d.get('timeOut'), 'gas': d.get('gas'), 'suit': d.get('suit'),
          'weight': d.get('weight'), 'pstart': d.get('pressureStart'), 'pend': d.get('pressureEnd'), 'buddy': d.get('buddy'), 'notes': d.get('notes'),
          'sign': d.get('instructor'), 'pos': d.get('pos')}
    for f, val in mp.items():
        if val is not None and val != '': book['v'][f'd:{n}:{f}'] = str(val)
    for t in d.get('types') or []: book['v'][f'd:{n}:t_{t}'] = True
    book['verified'][str(n)] = {'id': d['id'], 'center': d.get('center', ''), 'centerId': d.get('centerId', ''), 'at': '2026-10-15T10:00:00.000Z',
                                'locked': [f for f in LOCKED_DEFAULT if mp.get(f) not in (None, '')]}
    if not book.get('unlocked'): book['unlocked'] = {'by': 'center', 'at': '2026-10-15T10:00:00.000Z'}
    return book, n


class Logbook(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'lbmedas')
        cls.cid = cls.center.user['center_id']
        cls.diver = t.make_diver('lbana')
        cls.other = t.make_diver('lbpau')

    def put(self, client, book, version=None):
        headers = {'X-Logbook-Version': str(version)} if version is not None else {}
        return client.request('PUT', '/api/logbook', book, headers=headers)

    def book(self, client):
        r = client.get('/api/logbook'); self.assertEqual(r.status, 200, r.json); return r.json

    def new_dive(self, qty=1, **kw):
        data = {'date': DAY, 'site': 'Islas Medas · La Vaca', 'country': 'Girona, España', 'instructor': 'M. Pons · PADI 412873', 'depth': '18', 'time': '47',
                'temp': '21', 'vis': '15', 'timeIn': '10:05', 'timeOut': '10:52', 'gas': 'Aire', 'lat': '42.04780', 'lon': '3.22610', 'types': ['boat'], 'qty': qty}
        data.update(kw)
        r = self.center.post('/api/center/logbook/dive', data); self.assertEqual(r.status, 200, r.json); return r.json

    def token(self, url): return url.rsplit('/', 1)[1]

    # ------------------------------------------------------------------------------------------------ saved in the account
    def test_1_se_guarda_en_la_cuenta_y_se_ve_en_otro_dispositivo(self):
        c = self.make_diver('lbdisp')
        p = self.book(c)
        self.assertEqual(p['items'], []); self.assertEqual(p['book']['version'], 0); self.assertEqual(p['pending'], [])
        self.assertTrue(p['profile']['qrText'].endswith('/buddy/' + p['profile']['id'])); self.assertTrue(p['storage_key'].startswith('wd-logbook-'))
        book = p['book']['data']
        book['v'].update({'d:1:date': '12/10/2026', 'd:1:site': 'Cova dels Arcs', 'd:1:depth': '12', 'd:1:time': '55', 'd:1:t_shore': True,
                          'd:2:site': 'borrador sin fecha', 'o:first': 'Ana', 'o:emerg': 'Luis · 600 000 000'})
        r = self.put(c, book, 0); self.assertEqual(r.status, 200, r.json); self.assertEqual(r.json['version'], 1)
        # another device: another session of the same person
        c2 = self.client(); self.assertEqual(c2.login(c.user['username']).status, 200)
        p2 = self.book(c2)
        self.assertEqual(p2['book']['data']['v'], book['v']); self.assertEqual(p2['book']['version'], 1)
        # the complete dive is also a row of the Log Book (points, app, exports); the draft is not
        self.assertEqual([(i['dive_date'], i['site'], i['depth'], i['duration'], i['dive_type']) for i in p2['items']],
                         [('2026-10-12', 'Cova dels Arcs', 12.0, 55, 'Costa')])
        # stored encrypted (the emergency contact and the insurance are personal data)
        import sqlite3
        con = sqlite3.connect(self.server.db); raw = con.execute('SELECT data FROM logbook_books WHERE user_id=?', (c.user['id'],)).fetchone()[0]; con.close()
        self.assertTrue(raw.startswith('wdx1:')); self.assertNotIn('Luis', raw)
        # the other device saved with an old version: refused with the latest one
        r = self.put(c, book, 0); self.assertEqual(r.status, 409); self.assertTrue(r.json['conflict']); self.assertEqual(r.json['version'], 1)
        # deleting the dive in the book deletes its row
        book['v'] = {k: v for k, v in book['v'].items() if not k.startswith('d:1:')}
        self.assertEqual(self.put(c, book, 1).status, 200)
        self.assertEqual(self.book(c)['items'], [])

    def test_2_lo_de_antes_entra_en_el_libro(self):
        c = self.make_diver('lbantes')
        self.assertEqual(c.post('/api/logbook', {'dive_date': '2026-09-01', 'site': 'Bajo de Dentro', 'country': 'España', 'depth': 24, 'duration': 41,
                                                 'dive_type': 'Profunda'}).status, 200)
        b = self.book(c)['book']
        self.assertEqual(b['data']['v'].get('d:1:site'), 'Bajo de Dentro'); self.assertEqual(b['data']['v'].get('d:1:date'), '01/09/2026')
        self.assertEqual(b['data']['v'].get('d:1:depth'), '24'); self.assertIs(b['data']['v'].get('d:1:t_deep'), True)
        self.assertEqual(b['version'], 1)

    # ------------------------------------------------------------------------------------------------ the centre's dive and its QR
    def test_3_qr_de_inmersion_verificada_sin_duplicar(self):
        made = self.new_dive(qty=2)
        self.assertEqual(len(made['qr']), 2); self.assertTrue(all('/scan/d/' in q['url'] for q in made['qr']))
        tok = self.token(made['qr'][0]['url'])
        r = self.diver.post('/api/logbook/claim', {'token': tok}); self.assertEqual(r.status, 200, r.json); self.assertFalse(r.json['already'])
        d = r.json['dive']
        self.assertEqual((d['site'], d['center'], d['instructor'], d['date'], d['pos']), ('Islas Medas · La Vaca', 'Centro lbmedas', 'M. Pons · PADI 412873',
                                                                                          dt.date.fromisoformat(DAY).strftime('%d/%m/%Y'), '42.04780, 3.22610'))
        # the page receives it as pending and the component adds it (lb.addDiveFromCenter); the book is saved
        p = self.book(self.diver)
        self.assertEqual([x['id'] for x in p['pending']], [d['id']])
        book, n = add_dive_from_center(p['book']['data'], p['pending'][0])
        r = self.put(self.diver, book, p['book']['version']); self.assertEqual(r.status, 200, r.json)
        p = self.book(self.diver)
        self.assertEqual(p['pending'], []); self.assertEqual(p['book']['data']['verified'][str(n)]['id'], d['id'])
        self.assertEqual([i['site'] for i in p['items']], ['Islas Medas · La Vaca'])
        # scanned again (the same QR or the other QR of the same dive): «ya estaba», never twice
        for q in made['qr']:
            r = self.diver.post('/api/logbook/claim', {'token': self.token(q['url'])}); self.assertEqual(r.status, 200, r.json); self.assertTrue(r.json['already'])
        p = self.book(self.diver)
        self.assertEqual(p['pending'], []); self.assertEqual(len(p['book']['data']['verified']), 1); self.assertEqual(len(p['items']), 1)
        # the second QR was not used up by the second scan: another diver can still use it
        r = self.other.post('/api/logbook/claim', {'token': self.token(made['qr'][1]['url'])}); self.assertEqual(r.status, 200, r.json)
        # and the first one is already used
        r = self.make_diver('lbtercero').post('/api/logbook/claim', {'token': tok}); self.assertEqual(r.status, 409); self.assertTrue(r.json['used'])
        self.assertEqual(self.diver.post('/api/logbook/claim', {'token': 'x' * 24}).status, 404)
        # the centre sees how many were used
        dv = [x for x in self.center.get('/api/center/logbook').json['dives'] if x['uid'] == d['id']][0]
        self.assertEqual((dv['qr_total'], dv['qr_used'], dv['qr_free']), (2, 2, 0))

    def verified_book(self, client):
        made = self.new_dive()
        r = client.post('/api/logbook/claim', {'token': self.token(made['qr'][0]['url'])}); self.assertEqual(r.status, 200, r.json)
        p = self.book(client)
        book, n = add_dive_from_center(p['book']['data'], [x for x in p['pending'] if x['id'] == r.json['dive']['id']][0])
        r2 = self.put(client, book, p['book']['version']); self.assertEqual(r2.status, 200, r2.json)
        self.last_token = self.token(made['qr'][0]['url'])
        return book, n, r2.json['version'], r.json['dive']

    # ------------------------------------------------------------------------------------------------ locked fields
    def test_4_campos_bloqueados_no_se_cambian_ni_manipulando_la_peticion(self):
        c = self.make_diver('lbtrampa')
        book, n, ver, dive = self.verified_book(c)
        tries = []
        for f, val in (('site', 'Otro sitio'), ('date', '01/01/2020'), ('country', 'Maldivas'), ('center', 'Centro inventado'),
                       ('sign', 'Yo mismo'), ('pos', '1.00000, 1.00000')):
            b = copy.deepcopy(book); b['v'][f'd:{n}:{f}'] = val; tries.append((f'cambiar {f}', b))
        b = copy.deepcopy(book); b['verified'][str(n)]['locked'] = ['date']; tries.append(('quitar campos de la lista bloqueada', b))
        b = copy.deepcopy(book); b['verified'][str(n)]['center'] = 'Otro centro'; tries.append(('cambiar el centro del sello', b))
        b = copy.deepcopy(book); b['verified'][str(n + 5)] = b['verified'].pop(str(n))
        for k in [k for k in b['v'] if k.startswith(f'd:{n}:')]: b['v'][k.replace(f'd:{n}:', f'd:{n + 5}:')] = b['v'].pop(k)
        tries.append(('mover la inmersión de página', b))
        b = copy.deepcopy(book); b['v'].update({'d:9:site': 'Falsa', 'd:9:date': '01/10/2026'})
        b['verified']['9'] = {'id': 'WD-FALSA0001', 'center': 'Centro lbmedas', 'centerId': '', 'at': '', 'locked': ['date', 'site']}; tries.append(('sello inventado', b))
        b = copy.deepcopy(book); b['verified']['9'] = dict(b['verified'][str(n)]); tries.append(('la misma inmersión dos veces', b))
        for label, b in tries:
            r = self.put(c, b, ver)
            self.assertEqual(r.status, 409, label); self.assertTrue(r.json['locked'], label)
            self.assertEqual(r.json['data']['v'][f'd:{n}:site'], dive['site'], label)
        p = self.book(c)
        self.assertEqual(p['book']['version'], ver)          # nothing was saved
        self.assertEqual(p['book']['data']['v'][f'd:{n}:site'], dive['site'])
        refused = self.server.sql("SELECT COUNT(*) AS n FROM audit_log WHERE action='logbook_locked_refused' AND user_id=?", (c.user['id'],))[0]['n']
        self.assertEqual(refused, len(tries))
        # the fields that are not locked can be completed by the diver
        b = copy.deepcopy(book); b['v'][f'd:{n}:buddy'] = 'Laura'; b['v'][f'd:{n}:notes'] = 'Un mero enorme'; b['v'][f'd:{n}:depth'] = '19'
        self.assertEqual(self.put(c, b, ver).status, 200)
        # also the old form of the Log Book (and the app) cannot change them
        row = self.book(c)['items'][0]
        r = c.post('/api/logbook/update', {'id': row['id'], 'dive_date': row['dive_date'], 'site': 'Otro sitio', 'country': row['country'], 'depth': 19})
        self.assertEqual(r.status, 400); self.assertIn('registró el centro', r.json['error'])

    def test_5_borrar_una_verificada_y_volver_a_escanear(self):
        c = self.make_diver('lbborra')
        book, n, ver, dive = self.verified_book(c)
        b = copy.deepcopy(book)
        for k in [k for k in b['v'] if k.startswith(f'd:{n}:')]: del b['v'][k]
        del b['verified'][str(n)]
        self.assertEqual(self.put(c, b, ver).status, 200)
        p = self.book(c); self.assertEqual(p['pending'], []); self.assertEqual(p['items'], [])
        # the QR scanned again brings it back: pending again, once, and the component adds it again
        r = c.post('/api/logbook/claim', {'token': self.last_token}); self.assertEqual(r.status, 200, r.json); self.assertFalse(r.json['already'])
        self.assertTrue(c.post('/api/logbook/claim', {'token': self.last_token}).json['already'])
        p = self.book(c); self.assertEqual([x['id'] for x in p['pending']], [dive['id']])
        book2, n2 = add_dive_from_center(p['book']['data'], p['pending'][0])
        self.assertEqual(self.put(c, book2, p['book']['version']).status, 200)
        p = self.book(c); self.assertEqual(p['pending'], []); self.assertEqual(len(p['items']), 1); self.assertEqual(len(p['book']['data']['verified']), 1)

    # ------------------------------------------------------------------------------------------------ buddies
    def test_6_buddies_en_los_dos_sentidos(self):
        a, b = self.make_diver('lbmarc'), self.make_diver('lblaura')
        code_a = self.book(a)['profile']['id']
        self.assertEqual(a.post('/api/buddies', {'code': code_a}).status, 400)           # your own QR
        self.assertEqual(b.post('/api/buddies', {'code': 'noexiste12345'}).status, 404)
        r = b.post('/api/buddies', {'code': code_a}); self.assertEqual(r.status, 200, r.json); self.assertFalse(r.json['already'])
        self.assertEqual(r.json['friend']['name'], 'Buceador lbmarc Pérez')
        # encargo del 17/10 (1.7): the other person accepts the request (before, both became buddies at once)
        self.assertTrue(r.json['pending']); self.assertEqual(self.book(b)['friends'], [])
        req = a.get('/api/buddies').json['incoming'][0]
        self.assertEqual(a.post('/api/buddies/answer', {'id': req['id'], 'accept': True}).status, 200)
        self.assertEqual([f['name'] for f in self.book(b)['friends']], ['Buceador lbmarc Pérez'])
        self.assertEqual([f['name'] for f in self.book(a)['friends']], ['Buceador lblaura Pérez'])
        self.assertTrue(b.post('/api/buddies', {'code': code_a}).json['already'])
        # the QR of the person, made by the web's single generator, carries their public link
        svg = a.get('/api/logbook/qr.svg'); self.assertEqual(svg.status, 200); self.assertTrue(svg.body.startswith(b'<svg'))
        # /buddy/<code> and /scan/d/<token> open the web
        r = self.client().get('/buddy/' + code_a); self.assertIn(r.status, (301, 302, 303, 307, 308)); self.assertIn('#/buddy/' + code_a, r.headers.get('Location', ''))
        self.client().get('/scan/d/' + 'Q' * 24)
        # neither code reaches the access log (whoever reads the logs cannot add a buddy or take a dive)
        time.sleep(0.3)
        log = (self.server.tmp / 'logs' / 'access.log').read_text()
        self.assertIn('/buddy/***', log); self.assertIn('/scan/d/***', log)
        self.assertNotIn(code_a, log); self.assertNotIn('Q' * 24, log)

    # ------------------------------------------------------------------------------------------------ signing up with a centre's link
    def test_7_registro_con_el_enlace_del_centro(self):
        panel = self.center.get('/api/center/logbook').json
        self.assertIn('/registro?centro=', panel['invite_url'])
        slug = panel['invite_url'].rsplit('=', 1)[1]
        # the link opens the sign-up of a diver with that centre (a strange «centro» is simply left out)
        r = self.client().get(f'/registro?centro={slug}'); self.assertIn(r.status, (301, 302, 303, 307, 308))
        self.assertTrue(r.headers.get('Location', '').endswith(f'/#/registro?tipo=recreational&centro={slug}'), r.headers.get('Location'))
        r = self.client().get('/registro?centro=%22%3E%3Cscript%3E'); self.assertTrue(r.headers.get('Location', '').endswith('/#/registro'), r.headers.get('Location'))
        # the logo of the passport (PNG with transparency)
        r = self.center.upload('/api/center/logbook/logo', {}, 'logo.png', PNG_BYTES); self.assertEqual(r.status, 200, r.json)
        logo = r.json['logo']; self.assertTrue(logo.startswith('/assets/uploads/'))
        self.assertEqual(self.client().get(f'/api/public/invite?centro={slug}').json['center'], {'name': 'Centro lbmedas', 'logo': logo})
        c = self.client()
        r = c.register('Alumno Invitado', 'alumno@lb.example.org', 'alumno_lb', centro=slug); self.assertEqual(r.status, 200, r.json)
        self.assertEqual(c.login('alumno_lb').status, 200)
        p = self.book(c)
        self.assertEqual(p['center'], {'name': 'Centro lbmedas', 'logo': logo})
        # the page calls lb.setCover(): the cover can only be that centre's
        book = p['book']['data']; book['cover'] = {'logo': logo, 'name': 'Centro lbmedas', 'style': '', 'off': False}
        book['unlocked'] = {'by': 'center', 'at': '2026-10-15T10:00:00Z'}
        r = self.put(c, book, p['book']['version']); self.assertEqual(r.status, 200, r.json); self.assertNotIn('data', r.json)
        self.assertIsNone(self.book(c)['center'])   # once it is on the cover it is not passed again
        book['cover'] = {'logo': '/assets/uploads/otro.png', 'name': 'Otro', 'style': '', 'off': True}
        r = self.put(c, book); self.assertEqual(r.status, 200); self.assertEqual(r.json['data']['cover']['logo'], logo)
        self.assertTrue(r.json['data']['cover']['off'])   # the classic cover is the diver's choice
        # a diver without a centre cannot put one
        d = self.make_diver('lbsincentro'); b = self.book(d)['book']['data']; b['cover'] = {'logo': logo, 'name': 'x', 'style': '', 'off': False}
        self.assertIsNone(self.put(d, b).json['data']['cover'])
        # SVG logos: only shapes
        bad = b'<svg xmlns="http://www.w3.org/2000/svg"><script>alert(1)</script></svg>'
        self.assertEqual(self.center.upload('/api/center/logbook/logo', {}, 'logo.svg', bad).status, 400)
        ok = b'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 10 10"><path d="M0 0h10v10z" fill="#123"/></svg>'
        r = self.center.upload('/api/center/logbook/logo', {}, 'logo.svg', ok); self.assertEqual(r.status, 200, r.json); self.assertTrue(r.json['logo'].endswith('.svg'))

    # ------------------------------------------------------------------------------------------------ completed bookings, permissions, PDF
    def test_8_reserva_completada_no_se_pierde(self):
        c = self.make_diver('lbreserva')
        sid = self.center.post('/api/provider-services', {'title': 'Inmersión guiada', 'price': 40, 'booking_mode': 'request', 'max_participants': 6}).json['id']
        tomorrow = (TODAY + dt.timedelta(days=1)).isoformat()
        slot = self.center.post('/api/provider-services/slot', {'service_id': sid, 'slot_date': tomorrow, 'slot_time': '10:00', 'spots_total': 6}).json['slot_id']
        r = c.post('/api/bookings', {'center_id': self.cid, 'service_id': sid, 'slot_id': slot, 'participants': 1}); self.assertEqual(r.status, 200, r.json)
        bid = r.json['id']
        self.assertEqual(self.center.post(f'/api/bookings/{bid}/status', {'status': 'confirmed'}).status, 200)
        self.server.sql('UPDATE bookings SET booking_date=? WHERE id=?', (DAY, bid))   # the dive took place yesterday
        r = self.center.post(f'/api/bookings/{bid}/status', {'status': 'completed'}); self.assertEqual(r.status, 200, r.json)
        p = self.book(c); n = [k for k in p['book']['data']['v'] if k.endswith(':date')][0].split(':')[1]
        b = p['book']['data']
        for k in [k for k in b['v'] if k.startswith(f'd:{n}:')]: del b['v'][k]
        r = self.put(c, b, p['book']['version']); self.assertEqual(r.status, 200)
        self.assertIn(f'd:{n}:site', r.json['data']['v'])   # it comes back: the dives of a completed booking are not deleted
        self.assertEqual(len(self.book(c)['items']), 1)

    def test_9_permisos_y_pdf(self):
        # encargo del 17/10 (1.7): for a diver the routes of a centre «do not exist» (404), as an address that is not there
        self.assertEqual(self.diver.post('/api/center/logbook/dive', {'date': DAY, 'site': 'x', 'instructor': 'y'}).status, 404)
        self.assertEqual(self.diver.get('/api/center/logbook').status, 404)   # 17/10 (1.7): «no existe» for a diver
        r = self.center.post('/api/center/logbook/dive', {'date': (TODAY + dt.timedelta(days=5)).isoformat(), 'site': 'x', 'instructor': 'y'})
        self.assertEqual(r.status, 400)
        made = self.new_dive(qty=3)
        pdf = self.center.get(f"/api/center/logbook/dive/{made['id']}/qr.pdf")
        self.assertEqual(pdf.status, 200); self.assertTrue(pdf.body.startswith(b'%PDF'))
        svg = self.center.get(f"/api/center/logbook/dive/{made['id']}/qr/{made['qr'][0]['id']}.svg"); self.assertEqual(svg.status, 200)
        # another centre does not see it
        other = self.make_center(self.admin, 'lbotro')
        self.assertEqual(other.get(f"/api/center/logbook/dive/{made['id']}/qr.pdf").status, 404)
        # my data: the book readable, the verified dives and the buddies
        exp = self.diver.get('/api/account/export').json
        self.assertIn('logbook_verified_dives', exp); self.assertIn('buddies', exp)


if __name__ == '__main__':
    unittest.main()
