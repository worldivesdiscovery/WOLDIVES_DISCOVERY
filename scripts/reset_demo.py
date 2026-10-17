#!/usr/bin/env python3
"""Restores the TEST environment (zip «-pruebas»): demonstration data and test accounts with dates from today.

    python scripts/reset_demo.py              → rebuilds data/pruebas/worldives.sqlite3 now (stop the server first)
    python scripts/reset_demo.py --si-hace-falta → only if the database is missing, older than 7 days or made by another
                                                   version of the web (start_pruebas)

With the server running, use the button Administración → Operación → «Restaurar demo» instead.
Never run it on the real server: the test accounts must never exist in the production database.
"""
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LIVE = Path(os.environ.get('WOD_DB_PATH') or ROOT / 'data' / 'pruebas' / 'worldives.sqlite3')
MAX_AGE_DAYS = 7


def app_version() -> str:
    m = re.search(r"^APP_VERSION = '([^']+)'", (ROOT / 'app' / 'server.py').read_text(encoding='utf-8'), re.M)
    return m.group(1) if m else ''


def generated(db: Path):
    """(day, version) the demonstration data was made on; (None, None) if unknown."""
    try:
        c = sqlite3.connect(f'file:{db}?mode=ro', uri=True)
        try: rows = dict(c.execute("SELECT key,value FROM site_settings WHERE key IN ('demo_generated_on','demo_generated_version')").fetchall())
        finally: c.close()
        return (dt.date.fromisoformat(rows['demo_generated_on']) if rows.get('demo_generated_on') else None), rows.get('demo_generated_version')
    except Exception:
        return None, None


def main():
    ap = argparse.ArgumentParser(); ap.add_argument('--si-hace-falta', action='store_true')
    a = ap.parse_args()
    if os.environ.get('WOD_ENV', '').lower() == 'production': raise SystemExit('reset_demo no se usa en producción.')
    if a.si_hace_falta:
        made, version = generated(LIVE) if LIVE.exists() else (None, None)
        # v50.51: data made by another version is rebuilt too (the v50.50 demo kept a v50.49 database without marine life)
        if made and (dt.date.today() - made).days < MAX_AGE_DAYS and version == app_version():
            print(f'Datos de demostración del {made.isoformat()} (v{version}): no hace falta regenerarlos.'); return
    tmp = LIVE.with_name('demo-nueva.sqlite3')
    if tmp.exists(): tmp.unlink()
    LIVE.parent.mkdir(parents=True, exist_ok=True)
    res = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(tmp)])
    if res.returncode != 0: raise SystemExit(res.returncode)
    for ext in ('', '-wal', '-shm'):
        p = Path(str(LIVE) + ext)
        if p.exists(): p.unlink()
    shutil.move(str(tmp), LIVE)
    print(f'Entorno de pruebas restaurado: {LIVE}')


if __name__ == '__main__':
    main()
