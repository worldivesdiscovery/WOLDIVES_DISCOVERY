#!/usr/bin/env python3
"""Merges new translations into the language packs.
    python3 tools/i18n_merge.py DIR      (DIR holds <lang>_web.json and <lang>_emails.json: {spanish: translation})
Web → public/assets/i18n/<lang>.json («exact»); emails → app/emails/<lang>.json. Existing translations are kept;
a translation is only accepted if it keeps every {placeholder} of the Spanish text."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = ['en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh', 'ru']
PH = re.compile(r'\{\w+\}')


def ok(es, tr):
    return isinstance(tr, str) and tr.strip() and sorted(PH.findall(es)) == sorted(PH.findall(tr))


def main():
    src = Path(sys.argv[1])
    for l in LANGS:
        for kind, target in (('web', ROOT / 'public' / 'assets' / 'i18n' / f'{l}.json'), ('emails', ROOT / 'app' / 'emails' / f'{l}.json')):
            f = src / f'{l}_{kind}.json'
            if not f.exists(): continue
            new = json.loads(f.read_text(encoding='utf-8'))
            if kind == 'web':
                pack = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {'exact': {}, 'patterns': []}
                ex = pack['exact']
            else:
                ex = json.loads(target.read_text(encoding='utf-8')) if target.exists() else {}
            added = bad = 0
            for es, tr in new.items():
                if es in ex: continue
                if not ok(es, tr): bad += 1; continue
                ex[es] = tr; added += 1
            if kind == 'web':
                target.write_text(json.dumps(pack, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
            else:
                target.write_text(json.dumps(dict(sorted(ex.items())), ensure_ascii=False, indent=1), encoding='utf-8')
            print(f'{l} {kind}: +{added}' + (f' ({bad} rechazadas por los marcadores)' if bad else ''))


if __name__ == '__main__':
    main()
