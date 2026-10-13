#!/usr/bin/env bash
# WORLDIVES DISCOVERY · ENTORNO DE PRUEBAS para la app WORLDIVES Pruebas (v50.48). Nunca en el servidor real.
# Enseña la dirección que hay que escribir en el móvil (el móvil y este ordenador, en la misma wifi).
cd "$(dirname "$0")"
exec ./iniciar.sh --pruebas --red-local "$@"
