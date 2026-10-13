#!/usr/bin/env bash
# Runs inside reactivecircus/android-emulator-runner (GitHub Actions): installs WORLDIVES Pruebas on the emulator,
# opens it (measuring the cold start) and drives it with emulador.py against the test server of the computer.
set -euo pipefail
APK=$(ls apk/*.apk | head -n 1)
OUT=capturas-emulador
mkdir -p "$OUT"
adb install -r "$APK"
adb shell am start -W -n com.worldives.app.pruebas/com.worldives.app.MainActivity | tee "$OUT/arranque.txt"
sleep 6
python3 movil/scripts/emulador.py "$OUT" data/pruebas
