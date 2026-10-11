#!/usr/bin/env python3
"""List of the rewritten dive-point descriptions, for the owner's review (docs/legal/puntos-reescritos.md).

Usage: python3 tools/puntos_reescritos.py data/demo/catalogo-demo.sqlite3 > docs/legal/puntos-reescritos.md
Reads the database only (never writes)."""
import json
import sqlite3
import sys

db = sqlite3.connect(f'file:{sys.argv[1]}?mode=ro', uri=True); db.row_factory = sqlite3.Row
rows = db.execute('''SELECT id,name,country,region,description,description_legacy,description_missing,description_reviewed FROM dive_points
                     WHERE active=1 ORDER BY country,region,name''').fetchall()
print('# Puntos de buceo con descripción reescrita\n')
print(f'{len(rows)} puntos. Revísalos en *Administración → Descripciones de puntos* y márcalos como «Descripción revisada». '
      'Entre corchetes, los datos que faltan y no se han inventado.\n')
country = None
for r in rows:
    if r['country'] != country:
        country = r['country']; print(f'\n## {country}\n')
    miss = json.loads(r['description_missing'] or '[]')
    print(f"### {r['name']} ({r['region'] or '—'}) · #{r['id']}{' · revisada' if r['description_reviewed'] else ''}\n")
    print((r['description'] or '').replace('\n\n', '\n\n') + '\n')
    if miss: print(f"[Faltan: {', '.join(miss)}]\n")
    if r['description_legacy'] and r['description_legacy'] != r['description']:
        print(f"> Texto anterior: {r['description_legacy']}\n")
