#!/usr/bin/env bash
# Crea la primera cuenta de administración (pide la contraseña sin mostrarla).
# Uso: ./scripts/crear_admin.sh --email tu@dominio --username admin --name "Tu Nombre"
set -euo pipefail
cd "$(dirname "$0")/.."
exec python3 app/server.py --create-admin "$@"
