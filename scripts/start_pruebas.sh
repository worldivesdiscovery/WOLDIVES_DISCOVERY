#!/usr/bin/env bash
# WORLDIVES DISCOVERY · ENTORNO DE PRUEBAS (zip «-pruebas»). Nunca en el servidor real.
# Puerto 8100, banda «Entorno de pruebas», cuentas de prueba (CUENTAS-DE-PRUEBA.md), correos guardados en
# data/pruebas/correos (no se envía nada), Stripe solo en modo test si pones claves sk_test_ en .env.
set -euo pipefail
cd "$(dirname "$0")/.."
command -v python3 >/dev/null 2>&1 || { echo "WORLDIVES DISCOVERY necesita Python 3."; exit 1; }
export WOD_DEMO_MODE=1 WOD_ENV=demo WOD_PORT=8100 WOD_HOST=127.0.0.1 WOD_PUBLIC_URL=http://127.0.0.1:8100
export WOD_DB_PATH="$PWD/data/pruebas/worldives.sqlite3" WOD_STORAGE_DIR="$PWD/data/pruebas/storage" WOD_LOG_DIR="$PWD/data/pruebas/logs"
export WOD_MAIL_FILE_DIR="$PWD/data/pruebas/correos" WOD_BACKUP_DIR="$PWD/data/pruebas/copias" WOD_ADMIN_TOTP_REQUIRED=0 WOD_SMTP_HOST=
export PYTHONPATH="$PWD/vendor${PYTHONPATH:+:$PYTHONPATH}"
mkdir -p data/pruebas/correos
python3 scripts/reset_demo.py --si-hace-falta
echo "Entorno de pruebas en http://127.0.0.1:8100 · cuentas en CUENTAS-DE-PRUEBA.md · Ctrl+C para parar"
exec python3 app/server.py
