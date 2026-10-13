#!/usr/bin/env python3
"""Texts of the app's own screens (v50.48+): the app speaks Spanish, English and French only.
    python3 scripts/idiomas/app_textos.py scripts/idiomas/datos/app_v50_49.json
The file holds {spanish: [english, french]}. Each text is added to scripts/idiomas/datos/app.json (the list the language
tests check) and to public/idiomas/en.json and fr.json. Existing translations are kept."""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]


def main(src):
    new = json.loads(Path(src).read_text(encoding='utf-8'))
    lst = ROOT / 'scripts' / 'idiomas' / 'datos' / 'app.json'
    texts = set(json.loads(lst.read_text(encoding='utf-8')))
    added = {'en': 0, 'fr': 0}
    for i, lang in enumerate(('en', 'fr')):
        f = ROOT / 'public' / 'idiomas' / f'{lang}.json'
        pack = json.loads(f.read_text(encoding='utf-8'))
        for es, tr in new.items():
            if es not in pack['exact']:
                pack['exact'][es] = tr[i]; added[lang] += 1
        f.write_text(json.dumps(pack, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    texts |= set(new)
    lst.write_text(json.dumps(sorted(texts), ensure_ascii=False, indent=1), encoding='utf-8')
    print(f"{len(new)} textos · nuevos en inglés {added['en']}, en francés {added['fr']} · lista de la app: {len(texts)}")


if __name__ == '__main__':
    main(sys.argv[1])
