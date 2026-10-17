#!/usr/bin/env bash
# Runs inside reactivecircus/android-emulator-runner (GitHub Actions): installs WORLDIVES Pruebas on the emulator,
# opens it (measuring the cold start) and drives it with emulador.py against the test server of the computer.
set -euo pipefail
APK=$(ls apk/*.apk | head -n 1)
OUT=capturas-emulador
mkdir -p "$OUT"
adb install -r "$APK"
# The notifications permission is granted as a person would answer Android's dialog: the walk drives the app through
# DevTools, which goes on behind a dialog nobody answers (the app paused under it), something a person cannot do.
adb shell pm grant com.worldives.app.pruebas android.permission.POST_NOTIFICATIONS || true
adb shell am start -W -n com.worldives.app.pruebas/com.worldives.app.MainActivity | tee "$OUT/arranque.txt"
sleep 6
python3 movil/scripts/emulador.py "$OUT" data/pruebas
