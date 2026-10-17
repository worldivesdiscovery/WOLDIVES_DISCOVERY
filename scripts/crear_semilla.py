#!/usr/bin/env python3
"""Creates the PRODUCTION database from scratch (Fase 7.1: «producción empieza limpia»).

It contains only the catalogue:
  - countries, types of dive, zones, certifications;
  - dive points with their own descriptions in 9 languages (dive_point_texts) and the review state;
  - destinations (travel_offers) without images unless their origin/licence is registered;
  - point photos only when their origin/licence is registered (Administración → Medios);
  - legal texts edited in Administración, the owner's legal data, plans and feature switches.
It never copies users, centres (the PADI/SSI ones stay in the demo), bookings, messages, payments, logs or sessions.
The first administrator is created afterwards with:  python app/server.py --create-admin

Usage:
    python3 scripts/crear_semilla.py --source data/demo/catalogo-demo.sqlite3 --out /srv/worldives/data/worldives.sqlite3
The source is only read. The output must not exist (it is never overwritten)."""
import argparse
import os
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOGUE = ['countries', 'dive_types', 'dive_zones', 'certifications']
POINT_COLS_CLEAR = {'center_id': None, 'created_by_user_id': None, 'updated_by_user_id': None}


def cols(db, table):
    return [r[1] for r in db.execute(f'PRAGMA table_info("{table}")')]


def copy_rows(src, dst, table, where='', transform=None):
    sc, dc = cols(src, table), cols(dst, table)
    common = [c for c in sc if c in dc]
    if not common: return 0
    n = 0
    for row in src.execute(f'SELECT {",".join(chr(34) + c + chr(34) for c in common)} FROM "{table}" {where}'):
        rec = dict(zip(common, row))
        if transform:
            rec = transform(rec)
            if rec is None: continue
        dst.execute(f'INSERT OR REPLACE INTO "{table}"({",".join(chr(34) + c + chr(34) for c in rec)}) VALUES({",".join("?" * len(rec))})', list(rec.values()))
        n += 1
    return n


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--source', required=True, help='database with the catalogue (read only)')
    ap.add_argument('--out', required=True, help='new production database (must not exist)')
    a = ap.parse_args()
    src_path, out = Path(a.source), Path(a.out)
    if not src_path.exists(): sys.exit(f'No existe {src_path}')
    if out.exists(): sys.exit(f'{out} ya existe: no se sobrescribe. Elige otra ruta o bórrala tú.')
    out.parent.mkdir(parents=True, exist_ok=True)
    # 1. Empty database with the complete schema and every migration (the server's own bootstrap).
    env = {**os.environ, 'WOD_DB_PATH': str(out), 'WOD_BACKUP_DIR': str(out.parent / 'backups')}
    env.pop('WOD_DEMO_MODE', None)
    r = subprocess.run([sys.executable, '-c', 'import sys; sys.path.insert(0, "app"); import server; server.bootstrap()'], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode: sys.exit('No se pudo crear el esquema:\n' + r.stderr)
    src = sqlite3.connect(f'file:{src_path}?mode=ro', uri=True)
    dst = sqlite3.connect(out)
    dst.execute('PRAGMA foreign_keys=OFF')
    report = {}
    # The new database is empty except for what the bootstrap seeds: the catalogue of the source replaces it.
    for t in CATALOGUE + ['dive_point_texts', 'dive_points']:
        dst.execute(f'DELETE FROM "{t}"')
    for t in CATALOGUE:
        report[t] = copy_rows(src, dst, t)
    report['dive_points'] = copy_rows(src, dst, 'dive_points', 'WHERE active=1', lambda r: {**r, **{k: v for k, v in POINT_COLS_CLEAR.items() if k in r}})
    if 'dive_point_texts' in [x[0] for x in src.execute("SELECT name FROM sqlite_master WHERE type='table'")]:
        report['dive_point_texts'] = copy_rows(src, dst, 'dive_point_texts', 'WHERE point_id IN (SELECT id FROM dive_points WHERE active=1)')
    licensed = set()
    if 'image_origins' in [x[0] for x in src.execute("SELECT name FROM sqlite_master WHERE type='table'")]:
        licensed = {x[0] for x in src.execute("SELECT path FROM image_origins WHERE COALESCE(origin,'')<>''")}
        report['image_origins'] = copy_rows(src, dst, 'image_origins', "WHERE COALESCE(origin,'')<>''", lambda r: {**r, 'updated_by': None})
    report['dive_point_photos'] = copy_rows(src, dst, 'dive_point_photos', '', lambda r: r if r.get('image_path') in licensed else None)
    report['travel_offers'] = copy_rows(src, dst, 'travel_offers', '', lambda r: {**r, 'image_path': r.get('image_path') if r.get('image_path') in licensed else None})
    tables = [x[0] for x in src.execute("SELECT name FROM sqlite_master WHERE type='table'")]
    if 'legal_documents' in tables:
        report['legal_documents (editados)'] = copy_rows(src, dst, 'legal_documents', "WHERE source='admin'", lambda r: {**{k: v for k, v in r.items() if k != 'id'}, 'created_by': None})
    if 'plans' in tables:
        report['plans'] = copy_rows(src, dst, 'plans')
    report['site_settings'] = copy_rows(src, dst, 'site_settings', "WHERE key LIKE 'legal\\_%' ESCAPE '\\' OR key LIKE 'feature\\_%' ESCAPE '\\' OR key LIKE 'plans\\_trial%' ESCAPE '\\' OR key LIKE 'retention\\_%' ESCAPE '\\' OR key LIKE 'maps\\_satellite\\_limit' OR key LIKE 'partners\\_%' ESCAPE '\\'",
                                        lambda r: {**r, 'updated_by': None} if 'updated_by' in r else r)
    dst.commit(); dst.close()
    # 2. Bootstrap again: own descriptions for every point that came without them (in 9 languages).
    r = subprocess.run([sys.executable, '-c', 'import sys; sys.path.insert(0, "app"); import server; server.bootstrap()'], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode: sys.exit('No se pudo completar la base:\n' + r.stderr)
    dst = sqlite3.connect(out)
    report['textos de puntos (9 idiomas)'] = dst.execute('SELECT COUNT(*) FROM dive_point_texts').fetchone()[0]
    # 3. Checks: nothing personal travelled.
    for t in ('users', 'centers', 'bookings', 'messages', 'payment_orders', 'sessions', 'email_outbox', 'audit_log', 'user_documents', 'logbook_entries', 'reward_offers'):
        n = dst.execute(f'SELECT COUNT(*) FROM "{t}"').fetchone()[0]
        if n: sys.exit(f'ERROR: {t} tiene {n} filas en la base de producción.')
    ok = dst.execute('PRAGMA integrity_check').fetchone()[0]
    dst.close(); src.close()
    os.chmod(out, 0o600)
    print(f'Base de producción creada: {out} (integridad: {ok})')
    for k, v in report.items(): print(f'  {k}: {v}')
    print('Sin usuarios, centros, reservas, mensajes, pagos ni registros.')
    print('Siguiente paso: python app/server.py --create-admin   (con WOD_DB_PATH apuntando a esta base)')


if __name__ == '__main__':
    main()
