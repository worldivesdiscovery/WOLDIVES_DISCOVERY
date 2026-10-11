"""Unit tests of the building blocks in app/wod (no server needed)."""
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / 'app'))
from wod import security as wsec  # noqa: E402
from wod import bookings as wbk  # noqa: E402


class SecurityUnits(unittest.TestCase):
    def test_trusted_proxy(self):
        os.environ['WOD_TRUSTED_PROXIES'] = '127.0.0.1,10.0.0.0/8'
        h = {'X-Forwarded-For': '1.2.3.4, 10.0.0.5'}
        self.assertEqual(wsec.client_ip('127.0.0.1', h), '1.2.3.4')
        # Not a trusted peer: the header is ignored (cannot be forged).
        self.assertEqual(wsec.client_ip('8.8.8.8', h), '8.8.8.8')
        self.assertEqual(wsec.request_scheme('127.0.0.1', {'X-Forwarded-Proto': 'https'}), 'https')
        self.assertEqual(wsec.request_scheme('8.8.8.8', {'X-Forwarded-Proto': 'https'}), 'http')
        os.environ['WOD_TRUSTED_PROXIES'] = ''
        self.assertEqual(wsec.client_ip('127.0.0.1', h), '127.0.0.1')

    def test_rate_limiter_bounded(self):
        rl = wsec.RateLimiter(3, 60, max_keys=100)
        for i in range(1000):
            rl.hit(f'k{i}')
        self.assertLessEqual(len(rl), 100)
        for _ in range(3):
            self.assertFalse(rl.hit('x'))
        self.assertTrue(rl.hit('x'))
        self.assertTrue(rl.blocked('x'))

    def test_embed_rules(self):
        ok = ['https://www.youtube-nocookie.com/embed/1', 'https://player.vimeo.com/video/2', 'https://www.google.com/maps/embed?pb=3']
        bad = ['http://www.youtube-nocookie.com/embed/1', 'javascript:alert(1)', 'https://www.google.com/search?q=x',
               'https://user:pw@player.vimeo.com/x', 'https://player.vimeo.com.evil.org/', 'https://youtube.com/embed/1']
        for u in ok:
            self.assertTrue(wsec.embed_allowed(u), u)
        for u in bad:
            self.assertFalse(wsec.embed_allowed(u), u)

    def test_urls(self):
        self.assertEqual(wsec.clean_http_url('www.centro.es'), 'https://www.centro.es')
        for bad in ('javascript:alert(1)', 'data:text/html,x', 'ftp://x.org', 'https://a@b.c'):
            with self.assertRaises(ValueError):
                wsec.clean_http_url(bad)
        self.assertEqual(wsec.clean_local_or_http_url('/assets/uploads/x.png'), '/assets/uploads/x.png')

    def test_sniff(self):
        self.assertEqual(wsec.sniff_document(b'%PDF-1.7'), '.pdf')
        self.assertEqual(wsec.sniff_document(b'\xff\xd8\xff\xe0'), '.jpg')
        self.assertIsNone(wsec.sniff_document(b'<html>'))
        self.assertEqual(wsec.sniff_video(b'\x00\x00\x00\x18ftypmp42'), '.mp4')

    def test_passwords(self):
        h = wsec.hash_password('una-clave-larga', iterations=100_000)
        self.assertTrue(wsec.verify_password('una-clave-larga', h))
        self.assertFalse(wsec.verify_password('otra', h))
        self.assertTrue(wsec.needs_rehash(h))  # below the configured 600 000
        self.assertFalse(wsec.verify_password('x', '!'))
        self.assertIsNotNone(wsec.password_problem('corta'))

    def test_log_ip(self):
        os.environ['WOD_LOG_IP'] = 'truncated'
        self.assertEqual(wsec.log_ip('83.44.12.200'), '83.44.12.0')
        os.environ['WOD_LOG_IP'] = 'none'
        self.assertEqual(wsec.log_ip('83.44.12.200'), '-')
        os.environ.pop('WOD_LOG_IP')


class BookingUnits(unittest.TestCase):
    def test_states(self):
        self.assertEqual(wbk.state_label('pending'), 'Solicitada')
        self.assertEqual(wbk.state_label('accepted_pending_payment'), 'Aceptada · pendiente de pago')
        self.assertEqual(wbk.mode_label('request', 12), 'Bajo petición · el centro responde en 12 h')
        self.assertEqual(wbk.mode_label('payment'), 'Pago al reservar · confirmación inmediata')

    def test_deadline_never_after_start(self):
        from datetime import datetime
        now = datetime(2030, 1, 1, 10, 0)
        start = datetime(2030, 1, 1, 18, 0)
        self.assertEqual(wbk.deadline_before_start(now, 24, start), start)
        self.assertEqual(wbk.deadline_before_start(now, 2, start), datetime(2030, 1, 1, 12, 0))


if __name__ == '__main__':
    unittest.main(verbosity=2)
