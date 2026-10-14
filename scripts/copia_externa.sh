#!/usr/bin/env bash
# Sends a backup file outside the server. WOD_BACKUP_COMMAND=/opt/worldives/scripts/copia_externa.sh
# The server calls it with the path of each new copy. Example with rclone (configure the «externo» remote first, in the
# EU: docs/despliegue/GUIA-VPS.md, paso 10). Use a bucket with versioning/object lock if you can.
# Another destination: WOD_BACKUP_COMMAND="/opt/worldives/scripts/copia_externa.sh otro-remoto:carpeta" (the server
# passes only PATH, HOME and the RCLONE_* variables to this script, never the keys of the .env).
set -euo pipefail
if [ "$#" -ge 2 ]; then DESTINO="$1"; FILE="$2"; else DESTINO="externo:worldives-backups"; FILE="$1"; fi
# The service can only write in its data folders and the backup folder (ProtectSystem=strict): rclone keeps its cache there.
export RCLONE_CACHE_DIR="${RCLONE_CACHE_DIR:-$(dirname "$(dirname "$FILE")")/.cache-rclone}"
SUB="$(basename "$(dirname "$FILE")")"        # db | files
rclone copy "$FILE" "$DESTINO/$SUB/" --immutable
