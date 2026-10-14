#!/usr/bin/env bash
# WORLDIVES DISCOVERY · ENTORNO DE PRUEBAS (zip «-DEMO»), puerto 8100. Nunca en el servidor real.
cd "$(dirname "$0")"
exec ./iniciar.sh --pruebas "$@"
