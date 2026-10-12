#!/usr/bin/env python3
"""Replaces the centres imported from public directories (PADI / SSI) by fictitious example centres.

Only for the DEMO database (WOD_DEMO_MODE=1). The 28 imported centres never go to production: in production the
centres sign up themselves and the administration approves them (Fase 5.9).

What it does, for every centre whose source is a public directory:
  - invented name («Centro de buceo de ejemplo …»), no logo, no real phone, email, web or social links;
  - the description says it is an example; the city, country and position are kept (they are not personal data
    and keep the map meaningful);
  - verification_status = 'demo'.
A full copy of the database is made before any change (data/backups). Nothing is deleted.

Usage:
    python3 scripts/herramientas/demo_centros_ficticios.py data/demo.sqlite3 --yes
"""
import argparse
import shutil
import sqlite3
import sys
from datetime import datetime, timezone
from pathlib import Path

NAMES = ['Azul Profundo', 'Arrecife Claro', 'Mar de Fondo', 'Las Gorgonias', 'Burbuja Lenta', 'Posidonia', 'El Mero Curioso',
         'Corriente Suave', 'Cala Serena', 'Roca Negra', 'Isla Pequeña', 'Faro Viejo', 'Pecio Dormido', 'Bajo Azul', 'Agua Clara',
         'Nudibranquio', 'Caballito de Mar', 'Pez Luna', 'La Morena', 'Coral Rojo', 'Ancla Perdida', 'Ola Tranquila',
         'Gruta Azul', 'Punta Brava', 'Brisa Marina', 'Horizonte', 'Medusa Blanca', 'Estrella de Mar', 'Delfín Gris', 'Tortuga Verde']
SOURCES = ('PADI public directory', 'SSI / ScubaGO')


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('db', help='SQLite database of the DEMO deployment')
    ap.add_argument('--yes', action='store_true', help='apply the changes (without it, only shows what would change)')
    a = ap.parse_args()
    path = Path(a.db)
    if not path.exists(): sys.exit(f'No existe {path}')
    db = sqlite3.connect(path); db.row_factory = sqlite3.Row
    rows = db.execute(f"SELECT id,name,city,country FROM centers WHERE source_name IN ({','.join('?' * len(SOURCES))}) ORDER BY id", SOURCES).fetchall()
    print(f'{len(rows)} centros importados de directorios públicos.')
    if not rows: return
    plan = [(r['id'], f"Centro de buceo de ejemplo {NAMES[i % len(NAMES)]}" + (f" {i // len(NAMES) + 1}" if i >= len(NAMES) else ''), r) for i, r in enumerate(rows)]
    for cid, new, r in plan: print(f"  #{cid}: {r['name']} ({r['city'] or ''}, {r['country'] or ''}) → {new}")
    if not a.yes:
        print('\nNo se ha cambiado nada. Repite con --yes para aplicarlo.'); return
    stamp = datetime.now(timezone.utc).strftime('%Y%m%d-%H%M%S')
    backup = path.parent / 'backups' / f'{path.stem}-antes-demo-ficticios-{stamp}.sqlite3'
    backup.parent.mkdir(parents=True, exist_ok=True)
    db.execute('PRAGMA wal_checkpoint(FULL)'); shutil.copy2(path, backup)
    print(f'Copia de seguridad: {backup}')
    now = datetime.now(timezone.utc).isoformat(timespec='seconds')
    cols = {r['name'] for r in db.execute('PRAGMA table_info(centers)')}
    blank = [c for c in ('phone', 'email', 'website', 'logo_url', 'logo_source', 'instagram_url', 'facebook_url', 'twitter_url', 'youtube_url',
                         'tiktok_url', 'address', 'cover_url', 'gallery_json', 'source_url', 'legal_name', 'tax_id', 'fiscal_address') if c in cols]
    for cid, new, r in plan:
        db.execute(f"UPDATE centers SET name=?, description=?, verification_status='demo', data_confidence='demo', source_name='Demo · centro ficticio', "
                   f"updated_at=?, {', '.join(c + '=NULL' for c in blank)} WHERE id=?",
                   (new, 'Centro ficticio de la versión de demostración. Sus actividades, precios y reseñas son ejemplos.', now, cid))
    db.commit()
    print(f'{len(plan)} centros sustituidos por centros ficticios.')


if __name__ == '__main__':
    main()
