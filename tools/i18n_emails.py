#!/usr/bin/env python3
"""Spanish source texts of the emails (EMAIL_TEMPLATES and every literal mail_t(...)) and what each language lacks.
    python3 tools/i18n_emails.py            → tools/i18n/emails_missing.json  {lang: [texts]}"""
import ast
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LANGS = ['en', 'fr', 'de', 'it', 'pt', 'pl', 'nl', 'zh', 'ru']


def sources():
    src = (ROOT / 'app' / 'server.py').read_text(encoding='utf-8')
    tree = ast.parse(src)
    out = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Assign) and any(isinstance(t, ast.Name) and t.id == 'EMAIL_TEMPLATES' for t in node.targets):
            tpl = ast.literal_eval(node.value)
            for t in tpl.values():
                for k in ('subject', 'pre'):
                    if t.get(k): out.add(t[k])
                for kind, val in t['blocks']:
                    if kind in ('h', 'p', 'note', 'code'): out.add(val)
                    elif kind == 'list': out.update(val)
                    elif kind == 'button': out.add(val[0])
        if isinstance(node, ast.Call) and getattr(node.func, 'id', None) in ('mail_t', 't') and len(node.args) >= 2 and isinstance(node.args[1], ast.Constant) and isinstance(node.args[1].value, str):
            out.add(node.args[1].value)
        if isinstance(node, ast.Call) and getattr(node.func, 'id', None) == 't' and len(node.args) == 1 and isinstance(node.args[0], ast.Constant) and isinstance(node.args[0].value, str):
            out.add(node.args[0].value)
    # labels of the legal documents and plans used inside emails
    for m in re.finditer(r"mail_t\(\w+,\s*LEGAL_DOCS\[", src): pass
    return {s for s in out if re.search(r'[A-Za-zÁÉÍÓÚáéíóúñÑ]', s) and not re.fullmatch(r'\{\w+\}', s)}


def main():
    src = sources()
    miss = {}
    for l in LANGS:
        p = ROOT / 'app' / 'emails' / f'{l}.json'
        have = json.loads(p.read_text(encoding='utf-8')) if p.exists() else {}
        miss[l] = sorted(s for s in src if s not in have)
    out = ROOT / 'tools' / 'i18n' / 'emails_missing.json'
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(miss, ensure_ascii=False, indent=1), encoding='utf-8')
    print(f'{len(src)} textos de correo; faltan: ' + ', '.join(f'{l} {len(v)}' for l, v in miss.items()))


if __name__ == '__main__':
    main()
