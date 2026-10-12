"""Fase 1D: 10 languages, retired ones archived and migrated, hreflang, translation files consistent."""
from __future__ import annotations

import json
import re
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from helpers import Server, ServerTestCase  # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
LANGS = ('es', 'en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh')   # v50.46: Russian retired
TOKENS = re.compile(r'\{[a-z0-9_]+\}|</?[a-z][a-z0-9]*\b')


def tokens(s):
    return sorted(TOKENS.findall(s))


class Languages(ServerTestCase):
    def test_html_lang_and_hreflang(self):
        c = self.client()
        for lang, tag in (('es', 'es'), ('pl', 'pl'), ('ru', 'en'), ('zh', 'zh-Hans'), ('ja', 'en'), ('zt', 'zh-Hans')):
            body = c.get(f'/?lang={lang}').body.decode()
            self.assertIn(f'<html lang="{tag}">', body, lang)
        body = c.get('/').body.decode()
        for lang in LANGS:
            self.assertIn(f'?lang={lang}"', body)
        self.assertIn('hreflang="x-default"', body)
        self.assertNotIn('hreflang="ja"', body); self.assertNotIn('hreflang="ru"', body)
        self.assertNotIn('<!--hreflang-->', body)

    def test_language_selector_has_nine(self):
        html = (ROOT / 'public' / 'index.html').read_text(encoding='utf-8')
        sel = re.search(r'<select[^>]*lang[^>]*>(.*?)</select>', html, re.S).group(1)
        self.assertEqual(sorted(re.findall(r'value="([a-z]+)"', sel)), sorted(LANGS))

    def test_retired_files_archived(self):
        for code in ('ja', 'ko', 'zt', 'ru'):
            self.assertFalse((ROOT / 'public' / 'idiomas' / f'{code}.json').exists())
            self.assertFalse((ROOT / 'app' / 'emails' / f'{code}.json').exists())
            self.assertTrue((ROOT / '_archivo' / 'idiomas' / 'web' / f'{code}.json').exists())
            self.assertTrue((ROOT / '_archivo' / 'idiomas' / 'emails' / f'{code}.json').exists())
        self.assertFalse((ROOT / 'app' / 'legal' / 'ru').exists()); self.assertTrue((ROOT / '_archivo' / 'idiomas' / 'legal' / 'ru').is_dir())

    def test_translation_files_consistent(self):
        """Every language has every reference text, and keeps the same {n}/{x} markers and HTML tags."""
        ref = json.loads((ROOT / 'public' / 'idiomas' / 'en.json').read_text(encoding='utf-8'))
        ref_pat = [p[0] for p in ref['patterns']]
        for lang in LANGS[1:]:
            d = json.loads((ROOT / 'public' / 'idiomas' / f'{lang}.json').read_text(encoding='utf-8'))
            missing = [k for k in ref['exact'] if k not in d['exact']]
            self.assertFalse(missing, f'{lang}: faltan {len(missing)}, p. ej. {missing[:3]}')
            pats = {p[0]: p[1] for p in d['patterns']}
            self.assertFalse([k for k in ref_pat if k not in pats], lang)
            for es, out in list(d['exact'].items()) + list(pats.items()):
                forms = out.values() if isinstance(out, dict) else [out]
                for f in forms:
                    self.assertEqual(tokens(es), tokens(f), f'{lang}: «{es}» → «{f}»')
            if lang == 'pl':
                self.assertTrue(any(re.search('[ąćęłńśźż]', v) for v in d['exact'].values() if isinstance(v, str)))


class RetiredLanguageMigration(unittest.TestCase):
    def test_users_and_queue_move(self):
        s = Server()
        try:
            s.start(); s.stop(cleanup=False)
            for uid, lang in ((9101, 'ja'), (9102, 'ko'), (9103, 'zt'), (9104, 'fr'), (9105, 'ru')):
                s.sql("INSERT INTO users(id,fullname,email,username,password_hash,role,created_at) VALUES(?,?,?,?,'!','recreational','x')", (uid, 'U', f'u{uid}@x.org', f'u{uid}'))
                s.sql('INSERT INTO user_profiles(user_id,preferred_language,updated_at) VALUES(?,?,\'x\')', (uid, lang))
            s.sql("INSERT INTO email_outbox(template,lang,to_email,subject,status,created_at) VALUES('t','ko','a@x.org','s','queued','x')")
            s.sql("INSERT INTO email_outbox(template,lang,to_email,subject,status,created_at) VALUES('t','ja','b@x.org','s','sent','x')")
            s.sql("INSERT INTO email_outbox(template,lang,to_email,subject,status,created_at) VALUES('t','ru','c@x.org','s','queued','x')")
            s.start()
            langs = {r['user_id']: r['preferred_language'] for r in s.sql('SELECT user_id,preferred_language FROM user_profiles WHERE user_id>9100')}
            self.assertEqual(langs, {9101: 'en', 9102: 'en', 9103: 'zh', 9104: 'fr', 9105: 'en'})
            out = {r['to_email']: r['lang'] for r in s.sql('SELECT to_email,lang FROM email_outbox')}
            self.assertEqual(out['a@x.org'], 'en'); self.assertEqual(out['c@x.org'], 'en')
            self.assertEqual(out['b@x.org'], 'ja')  # already sent: history untouched
        finally:
            s.stop()


if __name__ == '__main__':
    unittest.main(verbosity=2)
