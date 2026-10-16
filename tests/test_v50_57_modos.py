"""v50.57 (revisión general, 5.1): what the audit of the four modes found on the server side.

- The receipt (PDF) of a booking by days with a discount («−10 % desde 3 días») wrote «1 × 0 €» next to the
  discount (a discount has no unit price, only its amount) and «?10 %»: the fonts of the PDF have no minus sign.
  Now the line shows «–10 % desde 3 días» and its amount alone.
"""
import datetime as dt
import re
import shutil
import subprocess
import tempfile
import unittest
from pathlib import Path

from helpers import ServerTestCase


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


@unittest.skipUnless(shutil.which('pdftotext'), 'hace falta pdftotext para leer el PDF')
class ReceiptDiscount(ServerTestCase):
    def test_the_discount_line_shows_its_amount_and_no_unit_price(self):
        admin = self.make_admin()
        pro = self.make_freelance(admin, 'cenotes')
        rules = {'min_days': 1, 'max_days': 10, 'lead_hours': 24, 'am': ['08:00', '13:00'], 'pm': ['14:00', '19:00'], 'full': ['08:00', '16:00']}
        sid = pro.post('/api/provider-services', {'title': 'Cenotes por días', 'price': 180, 'max_participants': 4, 'booking_mode': 'request', 'booking_unit': 'half_day',
                                                  'pay_way': 'in_person', 'pay_methods': ['cash'], 'pay_whatsapp': '+34 611 000 111',
                                                  'pay_policy': 'Gratis hasta 24 horas antes.', 'accept_in_person_terms': True,
                                                  'timezone': 'America/Cancun', 'unit_rules': rules,
                                                  'pricing': {'day': 180, 'half': 110, 'discount': {'min_days': 3, 'pct': 10}}}).json['id']
        diver = self.make_diver('cenotes')
        r = diver.post('/api/bookings', {'service_id': sid, 'days': [day(40), day(41), day(42)], 'part': 'full', 'participants': 1, 'in_person_ack': True})
        self.assertEqual(r.status, 200, r)
        bid = r.json['id']
        self.assertEqual(self.server.sql('SELECT price FROM bookings WHERE id=?', (bid,))[0]['price'], 486)   # 3 × 180 − 10 %
        pdf = diver.get(f'/api/bookings/{bid}/receipt.pdf')
        self.assertEqual(pdf.status, 200, pdf)
        with tempfile.TemporaryDirectory() as tmp:
            f = Path(tmp) / 'r.pdf'; f.write_bytes(pdf.body)
            text = ' '.join(subprocess.run(['pdftotext', '-layout', str(f), '-'], capture_output=True, text=True).stdout.split())
        self.assertNotIn('?10 %', text)
        self.assertRegex(text, r'–10 % desde 3 días\s+[−–-]\s?54(,00)?\s?€', 'the discount line shows its sign and its amount')
        self.assertIsNone(re.search(r'1\s?×\s?0(,00)?\s?€', text), 'no unit price «1 × 0 €» for the discount')
        self.assertRegex(text, r'3\s?×\s?180(,00)?\s?€', 'the days still show their unit price')


if __name__ == '__main__':
    unittest.main()
