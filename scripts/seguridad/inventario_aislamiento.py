"""Inventario de las tablas de centro (v50.47, parte A.1) a partir de una base nueva con todas las migraciones.

    python scripts/seguridad/inventario_aislamiento.py           → imprime la tabla en Markdown
    python scripts/seguridad/inventario_aislamiento.py --doc     → la escribe en docs/seguridad/aislamiento-centros.md
                                                                     (entre las marcas <!-- tablas:inicio/fin -->)
"""
from __future__ import annotations

import os
import sqlite3
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DOC = ROOT / 'docs' / 'seguridad' / 'aislamiento-centros.md'
INHERITED = {   # tables without their own tenant column: they hang from a parent that has it
    'manifest_entries': 'salida + reserva (disparador: misma empresa)', 'slot_groups': 'salida (disparador: el barco es del mismo centro)',
    'slot_cancel_offers': 'reserva + salida (disparador)', 'reschedule_requests': 'reserva + salida destino (disparador)', 'slot_events': 'salida',
    'service_slot_points': 'salida', 'waitlist_entries': 'salida (pública) + buceador', 'waiver_signatures': 'reserva', 'booking_days': 'reserva',
    'experience_bookings': 'experiencia', 'payment_refunds': 'pago', 'resource_blocks': 'recurso', 'resource_hours': 'recurso', 'resource_closures': 'recurso',
    'promotion_codes': 'promoción', 'promotion_redemptions': 'promoción + centro', 'promotion_partners': 'promoción (centros invitados)',
    'whatsapp_webhook_events': 'clave de evento (sin datos)', 'email_digest_log': 'centro (registro interno)',
}


def build():
    tmp = Path(tempfile.mkdtemp(prefix='wod-inv-')) / 'inv.sqlite3'
    env = {**os.environ, 'WOD_DB_PATH': str(tmp), 'WOD_EMPTY_DB': '1', 'WOD_SECRET_KEY': 'x' * 40, 'WOD_BACKUP_DIR': str(tmp.parent / 'b')}
    r = subprocess.run([sys.executable, '-c', 'import sys; sys.path.insert(0, "app"); import server; server.bootstrap()'], cwd=ROOT, env=env, capture_output=True, text=True)
    if r.returncode: raise SystemExit(r.stderr)
    db = sqlite3.connect(tmp)
    rows = []
    for (t,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%' ORDER BY name"):
        cols = {c[1]: c for c in db.execute(f'PRAGMA table_xinfo("{t}")')}
        fks = {f[3]: f[2] for f in db.execute(f'PRAGMA foreign_key_list("{t}")')}
        idx = [db.execute(f'PRAGMA index_info("{i[1]}")').fetchall() for i in db.execute(f'PRAGMA index_list("{t}")')]
        indexed = {cs[0][2] for cs in idx if cs}
        trig = [x[0] for x in db.execute("SELECT name FROM sqlite_master WHERE type='trigger' AND tbl_name=?", (t,))]
        if 'provider_id' in cols:
            c = cols['provider_id']
            if 'provider_type' in cols and (c[2] or '').upper().startswith('INT'):   # plans and statistics: numeric pair of before v50.47
                rows.append((t, '`provider_type` + `provider_id`', 'sí' if c[3] else 'no', 'no (identificador numérico)', 'sí' if 'provider_type' in indexed or 'provider_id' in indexed else 'no', len(trig)))
                continue
            kind = 'generada' if c[6] in (2, 3) else ('mantenida por disparador' if t == 'service_slots' else 'declarada')
            nn = 'sí' if c[3] else ('sí (disparador)' if t == 'service_slots' else 'no')
            rows.append((t, f'`provider_id` ({kind})', nn, 'sí → providers' if 'provider_id' in fks else 'no', 'sí' if 'provider_id' in indexed else 'no', len(trig)))
        elif t in INHERITED:
            rows.append((t, 'heredado: ' + INHERITED[t], '—', '—', '—', len(trig)))
    db.close()
    head = '| Tabla | Columna de centro | NOT NULL | Clave foránea | Índice (provider_id, …) | Disparadores |\n|---|---|---|---|---|---|'
    return head + '\n' + '\n'.join(f'| `{a}` | {b} | {c} | {d} | {e} | {f} |' for a, b, c, d, e, f in rows)


def main(argv):
    table = build()
    if '--doc' in argv:
        s = DOC.read_text(encoding='utf-8')
        a, b = s.index('<!-- tablas:inicio -->'), s.index('<!-- tablas:fin -->')
        DOC.write_text(s[:a] + '<!-- tablas:inicio -->\n' + table + '\n' + s[b:], encoding='utf-8')
        print('Inventario escrito en', DOC.relative_to(ROOT))
    else:
        print(table)


if __name__ == '__main__':
    main(sys.argv[1:])
