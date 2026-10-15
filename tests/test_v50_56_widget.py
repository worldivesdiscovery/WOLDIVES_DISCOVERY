"""v50.56 · Bloque 1, Partes C y D: el widget de reservas, la página del centro (/c/<centro>), los enlaces directos y QR.

Comprueba en el servidor:
  - solo en los dominios autorizados: CSP frame-ancestors por centro y comprobación de la web en cada reserva;
  - las páginas del widget no ponen cookies y la página del centro no se puede incrustar;
  - el precio y las plazas los pone el servidor; canal «widget» con la web de origen y canal «link» en la página;
  - la ficha gratuita (o un plan caducado) enseña «Solicitar información» y no reserva; las reservas ya hechas siguen;
  - límite por dirección, comprobación invisible (prueba de trabajo) y campo trampa;
  - la reserva de un cliente sin cuenta: se ve, se paga y se cancela con su enlace, nunca sin él;
  - aislamiento: el widget de un centro no reserva servicios de otro;
  - correos con la marca del centro y la respuesta al centro;
  - el panel: dirección, color, idioma y dominios; el equipo sin permiso de ajustes no los cambia;
  - textos completos en los 9 idiomas y widget.js de menos de 50 KB.
"""
import hashlib
import json
import re
import sys
import unittest
from pathlib import Path

from helpers import ServerTestCase, Client
from stripe_mock import StripeMock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'app'))
from wod import canales as wch  # noqa: E402
from wod import widget_textos as wtx  # noqa: E402

FAR = '2099-12-31'


class Puras(unittest.TestCase):
    def test_textos_en_9_idiomas(self):
        self.assertEqual(len(wtx.LANGS), 9)
        for lang in wtx.LANGS:
            with self.subTest(lang=lang):
                self.assertEqual(set(wtx.T[lang]), set(wtx.ES))
                for k, v in wtx.T[lang].items():
                    self.assertEqual(sorted(re.findall(r'\{\w+\}', v)), sorted(re.findall(r'\{\w+\}', wtx.ES[k])), (lang, k))
        self.assertEqual(wtx.pick_lang('de', 'fr', 'en'), 'de')
        self.assertEqual(wtx.pick_lang(None, None, 'pl-PL,pl;q=0.9,en;q=0.8'), 'pl')
        self.assertEqual(wtx.pick_lang(None, 'xx', 'ru'), 'es')

    def test_widget_js_ligero_y_sin_cookies(self):
        js = (ROOT / 'public' / 'widget.js').read_bytes()
        self.assertLess(len(js), 50 * 1024)
        for f in ('widget.js', 'js/wd-reservar.js'):
            src = (ROOT / 'public' / f).read_text(encoding='utf-8')
            self.assertNotIn('document.cookie', src, f)
            self.assertNotIn('localStorage', src, f)
            self.assertNotRegex(src, r'https?://(?!<WORLDIVES>)[a-z]', f)   # no third-party script, font or tracker

    def test_prueba_de_trabajo(self):
        sh = lambda b: hashlib.sha256(b.encode()).hexdigest()
        ch = wch.pow_challenge(sh)
        n = next(i for i in range(10 ** 6) if wch.pow_ok(sh, ch, i))
        self.assertTrue(wch.pow_ok(sh, ch, n))
        self.assertFalse(wch.pow_ok(sh, ch.replace(ch.split('.')[1], 'ffffffffffffffff'), n))   # changed challenge
        self.assertFalse(wch.pow_ok(sh, ch, n, now=int(ch.split('.')[0]) + wch.POW_TTL + 5))   # too old
        self.assertFalse(wch.pow_ok(lambda b: 'x' * 64, ch, n))                                # not issued by us


class Widget(ServerTestCase):
    @classmethod
    def setUpClass(cls):
        cls.stripe = StripeMock()
        cls.extra_env = dict(cls.extra_env, STRIPE_SECRET_KEY='sk_test_mock', WOD_STRIPE_API_BASE=cls.stripe.base, WOD_WIDGET_MAX_PER_HOUR='60', WOD_TRUSTED_PROXIES='127.0.0.1')
        super().setUpClass()
        t = cls('run')
        cls.admin = t.make_admin()
        cls.center = t.make_center(cls.admin, 'wgt')
        cls.cid = cls.center.user['center_id']
        cls.other = t.make_center(cls.admin, 'wgtotro', phone='+34 600 000 357')
        for c in (cls.cid, cls.other.user['center_id']):
            cls.server.sql(f"UPDATE centers SET plan_code='pro',plan_status='active',plan_expires_at='{FAR}',stripe_account_id='acct_w{c}',stripe_charges_enabled=1,stripe_payouts_enabled=1,email='reservas@wgt{c}.example.org' WHERE id=?", (c,))
        cls.req_sid = cls.center.post('/api/provider-services', {'title': 'Bautizo', 'price': 75, 'booking_mode': 'request', 'max_participants': 4}).json['id']
        cls.pay_sid = cls.center.post('/api/provider-services', {'title': 'Doble inmersión', 'price': 60, 'booking_mode': 'payment'}).json['id']
        cls.req_slot = cls.center.post('/api/provider-services/slot', {'service_id': cls.req_sid, 'slot_date': '2031-05-10', 'slot_time': '10:00', 'spots_total': 20}).json['slot_id']
        cls.pay_slot = cls.center.post('/api/provider-services/slot', {'service_id': cls.pay_sid, 'slot_date': '2031-05-11', 'slot_time': '09:00', 'spots_total': 20}).json['slot_id']
        cls.slug = cls.center.get('/api/provider/vender').json['slug']
        assert cls.center.post('/api/provider/vender', {'domains': 'buceowgt.com, *.wgt.example.net', 'color': '#0b7a75', 'lang': ''}).status == 200
        cls.other_sid = cls.other.post('/api/provider-services', {'title': 'Otro centro', 'price': 50, 'booking_mode': 'request'}).json['id']
        cls.other_slug = cls.other.get('/api/provider/vender').json['slug']
        cls.n = 0

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass(); cls.stripe.stop()

    def book(self, **kw):
        type(self).n += 1
        body = {'service_id': self.req_sid, 'slot_id': self.req_slot, 'participants': 1, 'fullname': f'Cliente {self.n}', 'email': f'cliente{self.n}@example.org',
                'accept_policy': True, 'canal': 'widget', 'host_url': 'https://www.buceowgt.com/reservas', 'lang': 'es'}
        ip = kw.pop('_ip', f'198.51.100.{self.n % 250}')
        body.update(kw)
        return Client(self.server).post(f'/api/w/{self.slug}/reservar', body, headers={'Idempotency-Key': f'test-widget-{self.n:06d}', 'X-Forwarded-For': ip})

    def test_cabeceras_dominios_y_sin_cookies(self):
        anon = Client(self.server, origin=None)
        r = anon.get(f'/w/{self.slug}?f=lista')
        csp = r.headers.get('Content-Security-Policy', '')
        self.assertEqual(r.status, 200)
        self.assertIn('frame-ancestors https://buceowgt.com https://www.buceowgt.com https://*.wgt.example.net', csp)
        self.assertNotIn("frame-ancestors 'none'", csp); self.assertNotIn('*;', csp.replace('https://*.', ''))
        self.assertIsNone(r.headers.get('X-Frame-Options')); self.assertIsNone(r.headers.get('Set-Cookie'))
        self.assertIn("script-src 'self'", csp)
        page = anon.get(f'/c/{self.slug}')
        self.assertEqual((page.status, page.headers.get('X-Frame-Options')), (200, 'DENY'))
        self.assertIn("frame-ancestors 'none'", page.headers.get('Content-Security-Policy', ''))
        self.assertIsNone(page.headers.get('Set-Cookie'))
        self.assertNotRegex(page.body.decode(), r'<script>(?!</script>)')      # no inline script
        self.assertEqual(anon.get('/w/no-existe-este-centro').status, 404)
        self.assertEqual(anon.get(f'/widget/center/{self.cid}').headers.get('Location'), f'/w/{self.slug}?f=lista')
        # A centre without domains: no website may frame the widget (only the preview of the panel of WORLDIVES itself)
        r = anon.get(f'/w/{self.other_slug}')
        self.assertIn("frame-ancestors 'self';", r.headers.get('Content-Security-Policy', '') + ';')

    def test_solo_dominios_autorizados(self):
        self.assertEqual(self.book(host_url='https://buceowgt.com/').status, 200)
        self.assertEqual(self.book(host_url='https://reservas.wgt.example.net/x').status, 200)
        for bad in ('https://buceowgt.com.evil.net/', 'https://evil.example.org/', 'https://wgt.example.net/', ''):
            with self.subTest(bad=bad):
                r = self.book(host_url=bad, host='')
                self.assertEqual(r.status, 403, r)

    def test_canal_origen_precio_y_plazas(self):
        before = self.server.sql('SELECT spots_available FROM service_slots WHERE id=?', (self.pay_slot,))[0]['spots_available']
        r = self.book(service_id=self.pay_sid, slot_id=self.pay_slot, participants=2, price=1, total=1)
        self.assertEqual(r.status, 200, r)
        b = self.server.sql('SELECT channel, channel_origin, source, price, status, slot_reserved, timezone FROM bookings WHERE id=?', (r.json['id'],))[0]
        self.assertEqual((b['channel'], b['channel_origin'], b['source'], b['price'], b['status'], b['slot_reserved']),
                         ('widget', 'www.buceowgt.com', 'widget', 120.0, 'payment_in_progress', 1))
        self.assertEqual(b['timezone'], 'Europe/Madrid')
        self.assertTrue(r.json['checkout_url'].startswith('https://'))
        call = [c for c in self.stripe.calls if c['path'] == '/v1/checkout/sessions' and c['method'] == 'POST'][-1]
        self.assertIn(f"/w/pago/{r.json['token']}?r=ok", call['params']['success_url']); self.assertIn('?r=cancel', call['params']['cancel_url'])
        self.assertEqual(call['account'], f'acct_w{self.cid}')                       # charged on the centre's own account
        self.assertEqual(self.server.sql('SELECT spots_available FROM service_slots WHERE id=?', (self.pay_slot,))[0]['spots_available'], before - 2)
        # The centre's page: channel «link»
        r = Client(self.server).post(f'/api/w/{self.slug}/reservar', {'service_id': self.req_sid, 'slot_id': self.req_slot, 'participants': 1, 'fullname': 'Desde la página',
                                                                       'email': 'pagina@example.org', 'accept_policy': True, 'canal': 'link'}, headers={'X-Forwarded-For': '203.0.113.77'})
        self.assertEqual(r.status, 200, r)
        self.assertEqual(self.server.sql('SELECT channel, channel_origin FROM bookings WHERE id=?', (r.json['id'],))[0], {'channel': 'link', 'channel_origin': None})

    def test_politica_y_campo_trampa(self):
        r = self.book(accept_policy=False)
        self.assertEqual(r.status, 400); self.assertIn('política', r.json['error'])
        r = self.book(website='http://spam.example.com')
        self.assertEqual(r.status, 400)
        self.assertEqual(self.book(email='').status, 400)

    def test_comprobacion_invisible_y_limite(self):
        ip = '192.0.2.200'
        codes = [self.book(_ip=ip).status for _ in range(5)]
        self.assertEqual(codes, [200] * 5)
        r = self.book(_ip=ip)
        self.assertEqual(r.status, 428, r); self.assertEqual(r.json['code'], 'challenge')
        ch, bits = r.json['challenge'], r.json['bits']
        nonce = next(i for i in range(10 ** 7) if (int.from_bytes(hashlib.sha256(f'{ch}:{i}'.encode()).digest()[:4], 'big') >> (32 - bits)) == 0)
        r = self.book(_ip=ip, pow={'challenge': ch, 'nonce': str(nonce)})
        self.assertEqual(r.status, 200, r)
        r = self.book(_ip=ip, pow={'challenge': ch, 'nonce': str(nonce)})      # a solved challenge is used once
        self.assertEqual(r.status, 428)

    def test_ficha_gratuita_solicitar_informacion(self):
        oc = self.other.user['center_id']
        self.server.sql("UPDATE centers SET plan_code='free',plan_expires_at=NULL WHERE id=?", (oc,))
        try:
            cat = Client(self.server).get(f'/api/w/{self.other_slug}?canal=widget').json
            self.assertFalse(cat['bookable'])
            r = Client(self.server).post(f'/api/w/{self.other_slug}/reservar', {'service_id': self.other_sid, 'booking_date': '2031-06-01', 'fullname': 'X Y', 'email': 'x@example.org',
                                                                                 'accept_policy': True, 'canal': 'link'})
            self.assertEqual(r.status, 403); self.assertTrue(r.json.get('no_online_booking'))
            r = Client(self.server).post('/api/info-requests', {'center_id': oc, 'name': 'Ana Info', 'email': 'ana.info@example.org', 'message': 'Hola, ¿tenéis salidas en junio?',
                                                                'accept_privacy': True})
            self.assertEqual(r.status, 200, r)
        finally:
            self.server.sql(f"UPDATE centers SET plan_code='pro',plan_expires_at='{FAR}' WHERE id=?", (oc,))

    def test_plan_caducado_conserva_las_reservas(self):
        r = self.book()
        self.assertEqual(r.status, 200)
        self.server.sql("UPDATE centers SET plan_expires_at='2020-01-01' WHERE id=?", (self.cid,))
        try:
            self.assertFalse(Client(self.server).get(f'/api/w/{self.slug}?canal=widget').json['bookable'])
            self.assertEqual(self.book().status, 403)
            self.assertEqual(self.server.sql('SELECT status FROM bookings WHERE id=?', (r.json['id'],))[0]['status'], 'requested')
            self.assertEqual(Client(self.server).get(f"/api/mi-reserva/{r.json['token']}").status, 200)
        finally:
            self.server.sql(f"UPDATE centers SET plan_expires_at='{FAR}' WHERE id=?", (self.cid,))

    def test_aislamiento_entre_centros(self):
        r = self.book(service_id=self.other_sid, slot_id=None, booking_date='2031-06-02')
        self.assertEqual(r.status, 404, r)
        r = Client(self.server).get(f'/api/w/{self.slug}/fechas?servicio={self.other_sid}&mes=2031-06')
        self.assertEqual(r.status, 404)
        names = [s['title'] for s in Client(self.server).get(f'/api/w/{self.slug}').json['services']]
        self.assertNotIn('Otro centro', names)

    def test_reserva_sin_cuenta_con_su_enlace(self):
        r = self.book(lang='en')
        tok = r.json['token']; bid = r.json['id']
        anon = Client(self.server)
        v = anon.get(f'/api/mi-reserva/{tok}').json['booking']
        self.assertEqual((v['ref'], v['status'], v['channel']), (f'WOD-{bid:06d}', 'requested', 'widget'))
        self.assertNotIn('internal_notes', json.dumps(v)); self.assertNotIn('contact_phone', json.dumps(v))
        self.assertEqual(anon.get(f'/api/mi-reserva/{bid}.{"x" * 32}').status, 404)
        self.assertEqual(anon.get(f'/mi-reserva/{bid}.{"x" * 32}').status, 404)
        self.assertEqual(anon.get(f'/mi-reserva/{tok}').status, 200)
        r = anon.post(f'/api/mi-reserva/{tok}/cancelar', {'preview': True})
        self.assertEqual(r.status, 200); self.assertIn('terms', r.json)
        r = anon.post(f'/api/mi-reserva/{tok}/cancelar', {})
        self.assertEqual((r.status, r.json['refund']), (200, 'none_paid'))
        self.assertEqual(self.server.sql('SELECT status, cancelled_by FROM bookings WHERE id=?', (bid,))[0], {'status': 'cancelled', 'cancelled_by': 'diver'})
        mail = self.server.sql("SELECT subject, lang, reply_to FROM email_outbox WHERE to_email=? ORDER BY id", (f'cliente{self.n}@example.org',))
        self.assertTrue(mail and all(m['lang'] == 'en' for m in mail), mail)
        self.assertTrue(all(m['reply_to'] == f'reservas@wgt{self.cid}.example.org' for m in mail), mail)

    def test_correo_con_la_marca_del_centro(self):
        r = self.book()
        row = self.server.sql("SELECT id FROM email_outbox WHERE to_email=? ORDER BY id DESC LIMIT 1", (f'cliente{self.n}@example.org',))[0]
        html = self.admin.get(f"/api/admin/emails/{row['id']}").body.decode('utf-8', 'replace')
        self.assertIn('Centro wgt', html); self.assertIn('Reservas con tecnología de WORLDIVES', html); self.assertIn('#0b7a75', html)
        self.assertIn(f"/mi-reserva/{r.json['token']}", html)

    def test_qr_y_enlaces(self):
        anon = Client(self.server, origin=None)
        svg = anon.get(f'/c/{self.slug}/qr.svg?servicio={self.req_sid}&fecha=2031-05-10')
        self.assertEqual((svg.status, svg.headers.get('Content-Type')), (200, 'image/svg+xml'))
        self.assertIn(b'<svg', svg.body)
        png = anon.get(f'/c/{self.slug}/qr.png?descargar=1')
        self.assertEqual(png.body[:8], b'\x89PNG\r\n\x1a\n'); self.assertIn('attachment', png.headers.get('Content-Disposition'))
        cfg = self.center.get('/api/provider/vender').json
        self.assertEqual(set(cfg['snippets']), {'boton', 'calendario', 'lista'})
        for fmt, snip in cfg['snippets'].items():
            self.assertLessEqual(len(snip.splitlines()), 2, fmt); self.assertIn('/widget.js', snip)
        self.assertTrue(any(s['link'].endswith(f'/c/{self.slug}?servicio={self.req_sid}') for s in cfg['services']))

    def test_panel_direccion_color_idioma(self):
        c = self.center
        self.assertEqual(c.post('/api/provider/vender', {'slug': 'api'}).status, 400)            # reserved
        self.assertEqual(c.post('/api/provider/vender', {'slug': self.other_slug}).status, 400)  # taken by another centre
        self.assertEqual(c.post('/api/provider/vender', {'color': 'red'}).status, 400)
        self.assertEqual(c.post('/api/provider/vender', {'domains': 'http://192.168.1.1'}).status, 400)
        r = c.post('/api/provider/vender', {'lang': 'de'})
        self.assertEqual(r.json['lang'], 'de')
        page = Client(self.server, origin=None).get(f'/w/{self.slug}', headers={'Accept-Language': 'fr'}).body.decode()
        self.assertIn('"lang": "de"', page)                                                       # fixed by the centre
        c.post('/api/provider/vender', {'lang': ''})
        page = Client(self.server, origin=None).get(f'/w/{self.slug}', headers={'Accept-Language': 'fr-FR,fr'}).body.decode()
        self.assertIn('"lang": "fr"', page)                                                       # automatic
        self.assertIn(Client(self.server).post('/api/provider/vender', {'color': '#000000'}).status, (401, 403))
        self.assertEqual(self.other.post('/api/provider/vender', {'slug': self.slug}).status, 400)


    def test_aviso_al_momento_y_ventas_por_canal(self):
        """Parte H: el panel ve cada reserva nueva al momento (con su canal), el centro recibe el correo con el canal y
        «Ventas por canal» la cuenta en su mes. Nada de esto se ve desde otro centro."""
        import datetime as _dt
        year = _dt.date.today().year
        sales = lambda c: c.get(f'/api/provider/ventas-canal?year={year}').json
        before, other_before = sales(self.center)['totals'], sales(self.other)['totals']
        last = self.center.get('/api/provider/feed').json['last']
        other_last = self.other.get('/api/provider/feed').json['last']
        bid = self.book().json['id']
        feed = self.center.get(f'/api/provider/feed?after={last}').json
        item = [i for i in feed['items'] if i['booking_id'] == bid]
        self.assertEqual([(i['event'], i['channel'], i['channel_label'], i['status']) for i in item], [('booking.created', 'widget', 'Tu web', 'requested')])
        self.assertEqual(item[0]['fullname'], f'Cliente {self.n}.')   # first name and initial only; self.assertEqual(item[0]['service_title'], 'Bautizo')
        self.assertGreaterEqual(feed['last'], item[0]['id'])
        self.assertEqual(self.center.get(f"/api/provider/feed?after={feed['last']}").json['items'], [])
        self.assertNotIn(bid, [i['booking_id'] for i in self.other.get(f'/api/provider/feed?after={max(other_last, 1)}').json['items']])
        self.assertIn(Client(self.server).get(f'/api/provider/feed?after={last}').status, (401, 403))
        mail = self.server.sql("SELECT to_email, text FROM email_outbox WHERE template='center_new_booking' AND related_id=?", (bid,))
        self.assertTrue(mail, 'sin correo al centro')
        self.assertTrue(all('Canal: Tu web · www.buceowgt.com' in m['text'] for m in mail), mail)
        self.assertTrue(all('Reservas con tecnología' not in m['text'] for m in mail))     # the centre's own notice is not branded
        after, other_after = sales(self.center), sales(self.other)['totals']
        self.assertEqual(after['totals']['widget']['bookings'], before['widget']['bookings'] + 1)
        self.assertEqual(other_after, other_before)
        self.assertEqual(len(after['months']), 12)
        self.assertEqual([c['key'] for c in after['channels']], list(wch.CHANNELS))
        month = _dt.date.today().strftime('%Y-%m')
        self.assertGreaterEqual(next(m for m in after['months'] if m['month'] == month)['by']['widget']['bookings'], 1)
        self.assertEqual(self.center.get('/api/provider/ventas-canal?year=dosmil').status, 400)

    def test_cliente_del_widget_es_del_centro(self):
        """Parte I: quien reserva en la web del centro es cliente del centro: ficha propia sin cuenta, nunca recibe
        publicidad de WORLDIVES y ningún otro centro lo ve."""
        bid = self.book().json['id']
        u = self.server.sql('SELECT u.id, u.password_hash, u.guest_center_id, u.email, u.marketing_consent FROM bookings b JOIN users u ON u.id=b.user_id WHERE b.id=?', (bid,))[0]
        self.assertEqual((u['password_hash'], u['guest_center_id'], u['marketing_consent']), ('!', self.cid, 0))
        self.assertTrue(u['email'].endswith('@sin-email.worldives.local'), u['email'])
        contact = f'cliente{self.n}@example.org'
        # Even with a consent flag set by mistake, the commercial e-mails of WORLDIVES skip the centre's customers
        self.server.sql("UPDATE users SET marketing_consent=1, email_verified_at='2026-01-01T00:00:00Z' WHERE id=?", (u['id'],))
        try:
            r = self.admin.post('/api/admin/marketing/send', {'subject': 'Ofertas de buceo', 'body': 'Texto de prueba'})
            self.assertEqual(r.status, 200, r)
            to = {m['to_email'] for m in self.server.sql("SELECT to_email FROM email_outbox WHERE template='marketing'")}
            self.assertNotIn(u['email'], to); self.assertNotIn(contact, to)
        finally:
            self.server.sql('UPDATE users SET marketing_consent=0, email_verified_at=NULL WHERE id=?', (u['id'],))
        self.assertIn(self.other.get(f'/api/bookings/{bid}').status, (403, 404))
        self.assertNotIn(f'Cliente {self.n}', self.other.get('/api/center/clients').body.decode('utf-8', 'replace'))
        self.assertNotIn(contact, self.other.get('/api/center/export?kind=clients').body.decode('utf-8', 'replace'))
        self.assertIn(f'Cliente {self.n}', self.center.get('/api/center/clients').body.decode('utf-8', 'replace'))

if __name__ == '__main__':
    unittest.main()
