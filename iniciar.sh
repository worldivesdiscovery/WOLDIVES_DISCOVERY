#!/usr/bin/env bash
# WORLDIVES DISCOVERY · arranque en Mac y Linux.
#   ./iniciar.sh                 la web en http://localhost:8000
#   ./iniciar.sh --red-local     también desde otros dispositivos de tu red
#   ./iniciar.sh --depuracion    muestra cada petición en la terminal
# En el servidor real (VPS) la web la arranca systemd: docs/despliegue/README.md
cd "$(dirname "$0")"
PY=$(command -v python3 || command -v python) || { echo "WORLDIVES DISCOVERY necesita Python 3.11 o superior: https://www.python.org/downloads/"; exit 1; }
exec "$PY" scripts/iniciar.py "$@"
