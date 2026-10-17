#!/usr/bin/env bash
# Prueba de restauración desde la copia EXTERNA (antes de abrir y luego una vez al mes). Como root, en el VPS:
#
#   sudo bash scripts/despliegue/restauracion_prueba.sh
#
# 1. Descarga la copia de la base de datos más reciente del destino externo (remoto «externo» de rclone, el mismo que
#    usa scripts/copia_externa.sh).
# 2. La comprueba (se descifra con WOD_BACKUP_KEY y pasa integrity_check) y la restaura en una carpeta temporal:
#    NUNCA sobre la base en uso, y sin arrancar ningún servidor con ella (no se envía ningún correo ni aviso).
# 3. Compara cuántos usuarios, centros y reservas tiene con la base en uso.
# 4. Escribe el resultado en /var/log/worldives/restauracion.log (lo lee scripts/despliegue/comprobar_lanzamiento.py)
#    y borra la copia temporal.
#
#   APP=/opt/worldives  REMOTO=externo:worldives-backups  USUARIO=worldives   (valores por defecto)
set -euo pipefail
APP="${APP:-/opt/worldives}"
REMOTO="${REMOTO:-externo:worldives-backups}"
USUARIO="${USUARIO:-worldives}"
LOG_DIR="${LOG_DIR:-/var/log/worldives}"
PY="$APP/.venv/bin/python"
[ -x "$PY" ] || PY="$(command -v python3)"

if [ "$(id -u)" -ne 0 ]; then echo "Ejecútalo con sudo." >&2; exit 1; fi
command -v rclone >/dev/null || { echo "Falta rclone (apt install rclone) y el remoto «externo» (rclone config)." >&2; exit 1; }
mkdir -p "$LOG_DIR"
TMP="$(mktemp -d /tmp/wod-restauracion.XXXXXX)"; chmod 700 "$TMP"; chown "$USUARIO": "$TMP"
trap 'rm -rf "$TMP"' EXIT
como() { sudo -u "$USUARIO" env HOME="$(getent passwd "$USUARIO" | cut -d: -f6)" RCLONE_CACHE_DIR="$TMP/.cache" "$@"; }

ULTIMA="$(como rclone lsf "$REMOTO/db/" --files-only | sort | tail -1)"
[ -n "$ULTIMA" ] || { echo "No hay copias en $REMOTO/db/" >&2; exit 1; }
echo "Copia externa más reciente: $ULTIMA"
como rclone copy "$REMOTO/db/$ULTIMA" "$TMP/"

cd "$APP"
COMPROBACION="$(como "$PY" app/server.py --verify-backup "$TMP/$ULTIMA")"
echo "$COMPROBACION"
case "$COMPROBACION" in *": ok"*) ;; *) echo "La copia no pasa la comprobación." >&2; exit 1 ;; esac
como env WOD_DB_PATH="$TMP/restaurada.sqlite3" "$PY" app/server.py --restore "$TMP/$ULTIMA" --yes

contar() {
  como "$PY" - "$1" <<'PYEOF'
import sqlite3, sys
db = sqlite3.connect(f'file:{sys.argv[1]}?mode=ro', uri=True)
q = lambda t: db.execute(f'SELECT COUNT(*) FROM {t}').fetchone()[0]
print(f"{q('users')} usuarios, {q('centers')} centros, {q('bookings')} reservas")
PYEOF
}
EN_USO="$(como "$PY" -c "import os,sys; sys.path.insert(0,'app'); from wod import config as c; print(os.environ.get('WOD_DB_PATH') or c.DB_PATH)" 2>/dev/null || echo "$APP/data/worldivesdiscovery.sqlite3")"
RESTAURADA="$(contar "$TMP/restaurada.sqlite3")"
ACTUAL="$(contar "$EN_USO" 2>/dev/null || echo 'no se pudo leer')"
echo "Restaurada: $RESTAURADA"
echo "En uso:     $ACTUAL"
LINEA="$(date -u +%Y-%m-%dT%H:%M:%SZ) ok copia=$ULTIMA restaurada=[$RESTAURADA] en_uso=[$ACTUAL]"
echo "$LINEA" >> "$LOG_DIR/restauracion.log"
echo "Prueba de restauración correcta. Anotada en $LOG_DIR/restauracion.log"
