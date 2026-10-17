#!/usr/bin/env bash
cd "$(dirname "$0")"
PYTHONPATH="$PWD/vendor" python3 app/server.py
