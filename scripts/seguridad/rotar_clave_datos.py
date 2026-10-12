"""Cambiar la clave de los datos cifrados (WOD_DATA_KEY) · v50.47, parte C.

Con el servidor PARADO:
  1. En el .env del servidor, mueve la clave actual a WOD_DATA_KEY_OLD y pon la nueva en WOD_DATA_KEY
     (python -c "import secrets;print(secrets.token_urlsafe(32))").
  2. python scripts/seguridad/rotar_clave_datos.py            (sin --aplicar solo comprueba y no cambia nada)
     python scripts/seguridad/rotar_clave_datos.py --aplicar
  3. Arranca el servidor. Guarda la clave antigua fuera del servidor: la necesitas para abrir las copias de seguridad
     anteriores. Cuando ya no la necesites, quítala de WOD_DATA_KEY_OLD.

Qué hace:
- Antes de tocar nada, una copia completa de la base en data/backups (nunca se cambian datos sin copia previa).
- En UNA transacción: vuelve a cifrar con la clave nueva todos los valores cifrados (teléfonos, correos en cola,
  credenciales de WhatsApp de cada centro…) y recalcula las huellas que dependen de la clave (búsqueda de teléfonos y
  números e identificadores de WhatsApp).
- Si un solo valor no se puede abrir con ninguna clave, no cambia nada y lo dice (falta una clave antigua).
- Al final comprueba que todo se abre con la clave nueva.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'app'))
import server  # noqa: E402  (loads the .env like the server)
from wod import cifrado as wcif  # noqa: E402


def encrypted_cells(db):
    for (t,) in db.execute("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'").fetchall():
        cols = [c[1] for c in db.execute(f'PRAGMA table_xinfo("{t}")').fetchall() if c[6] == 0 and (c[2] or '').upper() in ('', 'TEXT')]
        for col in cols:
            for rid, val in db.execute(f'SELECT rowid, "{col}" FROM "{t}" WHERE substr("{col}",1,5) IN (\'wdx1:\',\'wdk1:\')').fetchall():
                yield t, col, rid, val


def main(argv):
    apply = '--aplicar' in argv
    if not wcif.configured():
        raise SystemExit('Falta WOD_DATA_KEY en el .env del servidor.')
    db = server.connect()
    db.row_factory = sqlite3.Row
    pending, broken = [], []
    for t, col, rid, val in encrypted_cells(db):
        if not wcif.needs_rotation(val): continue
        if (wcif.decrypt(val) if wcif.is_encrypted(val) else wcif.decrypt_secret(val)) is None: broken.append(f'{t}.{col} (fila {rid})')
        else: pending.append((t, col, rid, val))
    print(f'Clave actual: {wcif.key_id()} · valores con una clave anterior: {len(pending)} · que no se pueden abrir: {len(broken)}')
    if broken:
        print('No se cambia nada. Estos valores no se abren con WOD_DATA_KEY ni con WOD_DATA_KEY_OLD (¿falta una clave antigua?):')
        for x in broken[:20]: print('  -', x)
        return 2
    if not apply:
        print('Comprobación sin cambios. Para cambiar la clave: --aplicar'); return 0
    copy = server.backup_database(db, 'rotar-clave')
    print('Copia previa:', copy)
    db.execute('BEGIN IMMEDIATE')
    try:
        for t, col, rid, val in pending:
            db.execute(f'UPDATE "{t}" SET "{col}"=? WHERE rowid=?', (wcif.rotate(val), rid))
        # Fingerprints that depend on the key.
        for t, cols in server.PHONE_COLUMNS.items():
            for col, hcol in cols:
                if hcol: db.execute(f'UPDATE {t} SET {hcol}=wod_huella({col}) WHERE {col} IS NOT NULL')
        for r in db.execute('SELECT provider_id, waba_id, phone_number_id, display_number FROM whatsapp_accounts').fetchall():
            db.execute('UPDATE whatsapp_accounts SET pnid_hash=?, number_hash=?, waba_hash=? WHERE provider_id=?',
                       (wcif.keyed_hash('pnid', wcif.decrypt_secret(r['phone_number_id'])), wcif.fingerprint(wcif.decrypt_secret(r['display_number'])),
                        wcif.keyed_hash('waba', wcif.decrypt_secret(r['waba_id'])), r['provider_id']))
        left = [1 for _t, _c, _r, v in encrypted_cells(db) if wcif.needs_rotation(v)]
        if left: raise RuntimeError(f'{len(left)} valores siguen con la clave anterior')
        db.commit()
    except Exception as exc:
        db.rollback()
        raise SystemExit(f'No se ha cambiado nada: {exc}')
    server.audit(db, None, 'data_key_rotated', 'system', None, {'valores': len(pending), 'clave': wcif.key_id()}); db.commit()
    print(f'Hecho: {len(pending)} valores cifrados con la clave nueva y huellas recalculadas.')
    return 0


if __name__ == '__main__':
    sys.exit(main(sys.argv[1:]))
