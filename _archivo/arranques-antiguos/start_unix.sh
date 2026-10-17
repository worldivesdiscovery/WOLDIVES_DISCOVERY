#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
command -v python3 >/dev/null 2>&1 || { echo "WORLDIVES DISCOVERY necesita Python 3."; exit 1; }
mkdir -p data storage/documents
exec python3 app/server.py
