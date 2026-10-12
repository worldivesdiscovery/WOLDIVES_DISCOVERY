#!/usr/bin/env bash
# Sends a backup file outside the server. WOD_BACKUP_COMMAND=/opt/worldives/scripts/copia_externa.sh
# The server calls it with the path of each new copy. Example with rclone (configure the «externo» remote first:
# Backblaze B2, Hetzner Storage Box, S3…). Use a bucket with versioning/object lock if you can.
set -euo pipefail
FILE="$1"
SUB="$(basename "$(dirname "$FILE")")"        # db | files
rclone copy "$FILE" "externo:worldives-backups/$SUB/" --immutable
