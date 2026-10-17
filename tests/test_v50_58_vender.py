"""v50.58 (revisión y usabilidad 15-16/10/2026, Parte 5): «Reservas desde tu web e Instagram» on the server.

- The counter «Este mes te han reservado 12 personas desde tu web» (people of this month's bookings on the website,
  and apart those of the booking link; cancelled ones do not count).
- «Comprobar»: the server reads the centre's page (a local stand-in of the internet: nothing leaves the machine), finds
  its code and authorises the domain on its own; «Aún no lo encontramos» when the code is missing, the page does not
  exist or it is another centre's code. Never a local or private address.
- «Enviar las instrucciones a mi informático»: the code of the look chosen and the guide by email, the answer to the
  centre, a limit per day; only centres and freelances.
"""
import sys
import threading
import unittest
import urllib.parse
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from helpers import ServerTestCase  # noqa: E402

PAGES = {}


class Web:
    """The centres' websites: /fetch?url=<address> answers the page kept in PAGES for that host (404 if none)."""
    def __init__(self):
        class H(BaseHTTPRequestHandler):
            def log_message(self, *a):
                pass

            def do_GET(self):
                url = urllib.parse.parse_qs(urllib.parse.urlparse(self.path).query).get('url', [''])[0]
                host = urllib.parse.urlparse(url).hostname or ''
                body = PAGES.get(host)
                self.send_response(200 if body is not None else 404)
                self.send_header('Content-Type', 'text/html; charset=utf-8'); self.end_headers()
                self.wfile.write((body or '<h1>No existe</h1>').encode())
        self.httpd = ThreadingHTTPServer(('127.0.0.1', 0), H)
        self.base = f'http://127.0.0.1:{self.httpd.server_address[1]}'
        threading.Thread(target=self.httpd.serve_forever, daemon=True).start()

    def stop(self):
        self.httpd.shutdown()


def page(snippet=''):
    return f'<!doctype html><html><head><title>Buceo</title></head><body><h1>Bienvenidos</h1>{snippet}<footer>Contacto</footer></body></html>'


class Vender(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.web = Web()
        cls.extra_env = {'WOD_MEDIA_FETCH_BASE': cls.web.base}
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'vend', phone='+34 600 590 001')
        cls.other = t.make_center(cls.admin, 'otrovend', phone='+34 600 590 002')
        cls.cid = cls.center.user['center_id']
        cls.server.sql("UPDATE centers SET email='reservas@buceo-vend.es' WHERE id=?", (cls.cid,))
        cls.diver = t.make_diver('vendbuceador')
        cls.v = cls.center.get('/api/provider/vender').json
        cls.slug = cls.v['slug']
        cls.other_slug = cls.other.get('/api/provider/vender').json['slug']

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.web.stop()

    def check(self, url, client=None):
        return (client or self.center).post('/api/provider/vender/check', {'url': url})

    def test_counter_of_the_month(self):
        self.assertEqual((self.v['month']['web'], self.v['month']['link']), (0, 0))
        uid = self.diver.user['id']
        for ch, pax, st in (('widget', 3, 'confirmed'), ('widget', 2, 'requested'), ('link', 4, 'confirmed'), ('widget', 5, 'cancelled'), ('worldives', 6, 'confirmed')):
            self.server.sql("""INSERT INTO bookings(user_id,center_id,booking_date,participants,status,channel,created_at,updated_at)
                               VALUES(?,?,date('now','+10 day'),?,?,?,strftime('%Y-%m-%dT%H:%M:%S','now'),strftime('%Y-%m-%dT%H:%M:%S','now'))""", (uid, self.cid, pax, st, ch))
        m = self.center.get('/api/provider/vender').json['month']
        self.assertEqual((m['web'], m['link']), (5, 4), 'the website: 3 + 2 people (the cancelled one does not count); the link: 4')

    def test_check_finds_the_button_and_authorises_the_domain(self):
        PAGES['buceo-con-boton.com'] = page(f'<script src="https://worlddivesdiscovery.com/widget.js" async></script>\n<a href="#" data-worldives="boton" data-centro="{self.slug}">Reservar</a>')
        r = self.check('buceo-con-boton.com')
        self.assertEqual(r.status, 200, r)
        self.assertTrue(r.json['ok']); self.assertEqual(r.json['text'], '✔ Tu botón está funcionando')
        self.assertEqual(r.json['authorized'], 'buceo-con-boton.com')
        v = self.center.get('/api/provider/vender').json
        self.assertIn('buceo-con-boton.com', v['domains'], 'step 4 authorises the domain by itself')
        self.assertTrue(v['check']['ok']); self.assertEqual(v['check']['url'], 'https://buceo-con-boton.com')
        # «www.» and a page inside: the bare domain (it covers www too), only once
        PAGES['www.buceo-con-boton.com'] = PAGES['buceo-con-boton.com']
        r = self.check('https://www.buceo-con-boton.com/reservas')
        self.assertTrue(r.json['ok'])
        self.assertEqual(self.center.get('/api/provider/vender').json['domains'].count('buceo-con-boton.com'), 1)
        # the widget frame or the booking page linked also count
        PAGES['buceo-con-marco.com'] = page(f'<iframe src="https://worlddivesdiscovery.com/w/{self.slug}?f=lista"></iframe>')
        self.assertTrue(self.check('buceo-con-marco.com').json['ok'])

    def test_check_not_found(self):
        PAGES['buceo-sin-boton.com'] = page('<p>Llámanos para reservar.</p>')
        r = self.check('buceo-sin-boton.com')
        self.assertEqual(r.status, 200, r)
        self.assertFalse(r.json['ok']); self.assertEqual(r.json['text'], 'Aún no lo encontramos'); self.assertEqual(r.json['reason'], 'no_code')
        self.assertIn('publica los cambios', r.json['hint'])
        self.assertNotIn('buceo-sin-boton.com', self.center.get('/api/provider/vender').json['domains'])
        r = self.check('web-que-no-existe.com')
        self.assertFalse(r.json['ok']); self.assertEqual(r.json['reason'], 'not_found')
        # another centre's code is not this centre's button
        PAGES['buceo-de-otro.com'] = page(f'<div data-worldives="lista" data-centro="{self.other_slug}"></div>')
        self.assertFalse(self.check('buceo-de-otro.com').json['ok'])
        self.assertNotIn('buceo-de-otro.com', self.center.get('/api/provider/vender').json['domains'])

    def test_check_refuses_what_is_not_a_website(self):
        for bad in ('', 'localhost', '127.0.0.1', 'http://10.0.0.5/admin', '*.buceo.com', 'ftp://buceo.com'):
            r = self.check(bad)
            self.assertEqual(r.status, 400, (bad, r))
        self.assertEqual(self.check('buceo-con-boton.com', self.diver).status, 403)

    def test_instructions_to_the_web_person(self):
        r = self.center.post('/api/provider/vender/instructions', {'email': 'Informatico@Empresa-Web.es', 'name': 'Jordi', 'fmt': 'calendario',
                                                                   'note': 'Ponlo en la página de inicio, por favor.'})
        self.assertEqual(r.status, 200, r); self.assertEqual(r.json['sent_to'], 'informatico@empresa-web.es')
        m = self.server.sql("SELECT * FROM email_outbox WHERE template='web_instructions' ORDER BY id DESC LIMIT 1")[0]
        self.assertEqual(m['to_email'], 'informatico@empresa-web.es'); self.assertEqual(m['reply_to'], 'reservas@buceo-vend.es', 'the answer goes to the centre')
        self.assertIn('Botón de reservas para la web de', m['subject'])
        html = self.admin.get(f"/api/admin/emails/{m['id']}").body.decode('utf-8', 'replace')
        self.assertIn('data-worldives=&quot;calendario&quot;', html); self.assertIn(f'data-centro=&quot;{self.slug}&quot;', html)
        self.assertIn('Hola Jordi', html); self.assertIn('Ponlo en la página de inicio', html); self.assertIn('WordPress', html)
        self.assertEqual(self.center.post('/api/provider/vender/instructions', {'email': 'no-es-un-correo'}).status, 400)
        self.assertIn(self.diver.post('/api/provider/vender/instructions', {'email': 'x@empresa.es'}).status, (403, 404))
        for _ in range(4): self.assertEqual(self.center.post('/api/provider/vender/instructions', {'email': 'otro@empresa-web.es'}).status, 200)
        r = self.center.post('/api/provider/vender/instructions', {'email': 'otro@empresa-web.es'})
        self.assertEqual(r.status, 400, r); self.assertIn('5 veces', r.json['error'])


if __name__ == '__main__':
    unittest.main()
