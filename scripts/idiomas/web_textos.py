#!/usr/bin/env python3
"""New texts of the web in its 9 languages (v50.49+).
    python3 scripts/idiomas/web_textos.py scripts/idiomas/datos/web_v50_49.json
The file holds {"exact": {spanish: {lang: text}}, "patterns": {spanish with {n}: {lang: text or {plural form: text}}}}. They are added to
public/idiomas/<lang>.json; existing translations are kept and a translation must keep every {placeholder}."""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
LANGS = ['en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh']
PH = re.compile(r'\{\w+\}')


def same_placeholders(es, tr):
    """A translation (or each plural form of it: {"one": …, "other": …}) keeps every {placeholder} of the Spanish text."""
    forms = list(tr.values()) if isinstance(tr, dict) else [tr]
    return bool(forms) and all(isinstance(f, str) and f.strip() and sorted(PH.findall(es)) == sorted(PH.findall(f)) for f in forms)


def main(src):
    data = json.loads(Path(src).read_text(encoding='utf-8'))
    for lang in LANGS:
        f = ROOT / 'public' / 'idiomas' / f'{lang}.json'
        pack = json.loads(f.read_text(encoding='utf-8'))
        added = 0
        for es, tr in data.get('exact', {}).items():
            t = tr.get(lang)
            if t and es not in pack['exact'] and same_placeholders(es, t):
                pack['exact'][es] = t; added += 1
        have = {p[0] for p in pack['patterns']}
        for es, tr in data.get('patterns', {}).items():
            t = tr.get(lang)
            if t and es not in have and same_placeholders(es, t):
                pack['patterns'].append([es, t]); added += 1
        f.write_text(json.dumps(pack, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
        print(f'{lang}: {added} textos nuevos')


if __name__ == '__main__':
    main(sys.argv[1])
