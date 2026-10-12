#!/usr/bin/env bash
# Restaura los datos del entorno de pruebas (para el servidor de pruebas antes).
set -euo pipefail
cd "$(dirname "$0")/.."
export WOD_DB_PATH="$PWD/data/pruebas/worldives.sqlite3"
exec python3 scripts/reset_demo.py "$@"
