"""Final translation pass (v50.38): the legal documents exist in the 9 languages with the same placeholders, links
and structure as the Spanish reference; every email text is translated into the 9 languages; the interface texts
added since v50.34 are in every language pack; and a translated legal document is served with «prevalece el
castellano»."""
import json
import re
import sys
import unittest
from pathlib import Path

from helpers import ServerTestCase, ROOT

LANGS = ['en', 'fr', 'de', 'it', 'pt', 'nl', 'pl', 'zh']
LEGAL = ROOT / 'app' / 'legal'


def shape(text):
    return {'placeholders': re.findall(r'\{\{\w+\}\}', text), 'links': re.findall(r'\]\((#/[^)\s]+)\)', text),
            'headings': len(re.findall(r'^#{1,3} ', text, re.M)), 'table_rows': len(re.findall(r'^\|', text, re.M))}


class LegalTranslations(unittest.TestCase):
    def test_every_document_in_every_language(self):
        for src in sorted((LEGAL / 'es').glob('*.md')):
            ref = shape(src.read_text(encoding='utf-8'))
            for lang in LANGS:
                p = LEGAL / lang / src.name
                with self.subTest(doc=src.name, lang=lang):
                    self.assertTrue(p.exists(), f'falta {lang}/{src.name}')
                    got = shape(p.read_text(encoding='utf-8'))
                    self.assertEqual(sorted(got['placeholders']), sorted(ref['placeholders']))
                    self.assertEqual(got['links'], ref['links'])
                    self.assertEqual(got['headings'], ref['headings'])
                    self.assertEqual(got['table_rows'], ref['table_rows'])


class EmailTranslations(unittest.TestCase):
    def test_every_email_text_in_every_language(self):
        sys.path.insert(0, str(ROOT / 'scripts' / 'idiomas'))
        import emails as i18n_emails
        src = i18n_emails.sources()
        for lang in LANGS:
            pack = json.loads((ROOT / 'app' / 'emails' / f'{lang}.json').read_text(encoding='utf-8'))
            missing = sorted(s for s in src if s not in pack)
            with self.subTest(lang=lang):
                self.assertEqual(missing, [], f'{lang}: {len(missing)} textos de correo sin traducir')
                bad = [k for k, v in pack.items() if sorted(re.findall(r'\{\w+\}', k)) != sorted(re.findall(r'\{\w+\}', v))]
                self.assertEqual(bad, [], f'{lang}: marcadores distintos')


class InterfaceTranslations(unittest.TestCase):
    def test_new_interface_texts_in_every_pack(self):
        ref = set()
        for f in ('missing.json', 'missing_extra.json'):   # texts collected by scripts/idiomas/collect.py and from the code of v50.34-38
            ref |= set(json.loads((ROOT / 'scripts' / 'idiomas' / 'datos' / f).read_text(encoding='utf-8')))
        for lang in LANGS:
            pack = json.loads((ROOT / 'public' / 'idiomas' / f'{lang}.json').read_text(encoding='utf-8'))['exact']
            with self.subTest(lang=lang):
                left = sorted(ref - set(pack))
                self.assertEqual(left, [], f'{lang}: {len(left)} textos sin traducir')


class ServedTranslation(ServerTestCase):
    def test_translated_document_shows_spanish_prevails(self):
        c = self.client()
        for lang in ('fr', 'de', 'pl', 'zh'):
            d = c.get(f'/api/legal/doc?slug=condiciones-centros&lang={lang}').json
            self.assertEqual(d['lang'], lang); self.assertFalse(d['official']); self.assertTrue(d['prevails_note'])
            self.assertNotIn('{{', d['markdown'])
        en = c.get('/api/legal/doc?slug=privacidad&lang=en').json
        self.assertTrue(en['official']); self.assertEqual(en['prevails_note'], '')


if __name__ == '__main__':
    unittest.main()
