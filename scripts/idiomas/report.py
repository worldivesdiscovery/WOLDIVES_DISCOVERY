#!/usr/bin/env python3
"""Translations report (Fase 1D).

    python scripts/idiomas/report.py            # report of missing / untranslated keys per language
    python scripts/idiomas/report.py --clean    # also removes junk keys (code fragments that slipped into the files)

Reference: the Spanish source strings = every key present in any language file plus scripts/idiomas/datos/source_strings.json
(strings collected from the real screens by scripts/idiomas/collect.py). Writes docs/i18n/informe.md.
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
WEB = ROOT / 'public' / 'idiomas'
EMAILS = ROOT / 'app' / 'emails'
LANGS = ['en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh']
JUNK = re.compile(r'^(["{\[]|null\}$)|["}]$|^[a-z_]+:[a-z_]+$')


def is_junk(k: str) -> bool:
    return bool(JUNK.search(k)) or not re.search(r'[^\W\d_]', k)


def load(p):
    return json.loads(p.read_text(encoding='utf-8')) if p.exists() else {'exact': {}, 'patterns': []}


def main():
    clean = '--clean' in sys.argv
    packs = {l: load(WEB / f'{l}.json') for l in LANGS}
    removed = {}
    for l, d in packs.items():
        bad = [k for k in d['exact'] if is_junk(k)]
        removed[l] = len(bad)
        if clean and bad:
            for k in bad: d['exact'].pop(k)
            (WEB / f'{l}.json').write_text(json.dumps(d, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    ref_exact = set()
    ref_pat = set()
    for d in packs.values():
        ref_exact |= {k for k in d['exact'] if not is_junk(k)}
        ref_pat |= {k for k, _ in d['patterns']}
    extra = ROOT / 'scripts' / 'idiomas' / 'datos' / 'source_strings.json'
    if extra.exists():
        ref_exact |= set(json.loads(extra.read_text(encoding='utf-8')))
    emails_ref = set()
    for l in LANGS:
        p = EMAILS / f'{l}.json'
        if p.exists(): emails_ref |= set(json.loads(p.read_text(encoding='utf-8')))
    out = ['# Informe de traducciones', '', f'Textos de referencia: {len(ref_exact)} frases y {len(ref_pat)} patrones de la web; {len(emails_ref)} textos de correos.', '',
           '| Idioma | Web: faltan | Web: sin traducir (igual que el castellano) | Correos: faltan | Claves basura |', '|---|---|---|---|---|']
    details = []
    for l in LANGS:
        d = packs[l]
        miss = sorted(ref_exact - set(d['exact'])) + sorted(ref_pat - {k for k, _ in d['patterns']})
        same = [k for k, v in d['exact'].items() if isinstance(v, str) and v == k and len(k) > 3 and re.search(r'[a-záéíóúñ]{4}', k)]
        em = json.loads((EMAILS / f'{l}.json').read_text(encoding='utf-8')) if (EMAILS / f'{l}.json').exists() else {}
        emiss = sorted(emails_ref - set(em))
        out.append(f'| {l} | {len(miss)} | {len(same)} | {len(emiss)} | {removed[l]}{" (eliminadas)" if clean else ""} |')
        details.append((l, miss, emiss))
    out.append('')
    for l, miss, emiss in details:
        if miss or emiss:
            out.append(f'## {l}: textos que faltan')
            out += [f'- {m}' for m in (miss + ['(correo) ' + e for e in emiss])[:400]]
            out.append('')
    target = ROOT / 'docs' / 'i18n' / 'informe.md'
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text('\n'.join(out), encoding='utf-8')
    print('\n'.join(out[:16]))


if __name__ == '__main__':
    main()
