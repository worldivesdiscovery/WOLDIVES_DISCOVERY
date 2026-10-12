#!/usr/bin/env python3
"""Single start of WORLDIVES DISCOVERY (v50.46). Called by iniciar.bat / iniciar.sh (and iniciar-pruebas.*).

    iniciar                 the web on http://localhost:8000
    iniciar --red-local     also reachable from other devices of the same network (WOD_HOST=0.0.0.0)
    iniciar --depuracion    every request is written in this window (WOD_ACCESS_LOG=stdout), no browser
    iniciar --pruebas       TEST ENVIRONMENT (zip «-pruebas»): port 8100, «Entorno de pruebas» band, test accounts,
                            emails saved in data/pruebas/correos, demonstration data with dates from today

The first time it installs what requirements.txt asks for (stripe, qrcode, fonttools) if it is missing.
On the real server (VPS) the web is started by systemd: see docs/despliegue/README.md.
"""
from __future__ import annotations

import argparse
import importlib.util
import os
import subprocess
import sys
import threading
import time
import webbrowser
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NEEDED = {'stripe': 'stripe', 'qrcode': 'qrcode', 'fontTools': 'fonttools'}


def ensure_requirements():
    missing = [pkg for mod, pkg in NEEDED.items() if importlib.util.find_spec(mod) is None]
    if not missing: return
    print(f'Instalando lo que falta ({", ".join(missing)}) desde requirements.txt…')
    r = subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', '-r', str(ROOT / 'requirements.txt')])
    if r.returncode != 0:
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')])
    if r.returncode != 0:
        print('No se han podido instalar las dependencias. Ejecuta a mano:  python -m pip install -r requirements.txt'); sys.exit(1)


def main():
    ap = argparse.ArgumentParser(description='Arranca WORLDIVES DISCOVERY.')
    ap.add_argument('--pruebas', action='store_true', help='entorno de pruebas (puerto 8100, cuentas y datos de prueba)')
    ap.add_argument('--red-local', action='store_true', help='accesible desde otros dispositivos de la misma red')
    ap.add_argument('--depuracion', action='store_true', help='muestra cada petición en esta ventana y no abre el navegador')
    ap.add_argument('--sin-navegador', action='store_true', help='no abre el navegador')
    a = ap.parse_args()
    os.chdir(ROOT)
    ensure_requirements()
    env = os.environ
    port = env.get('WOD_PORT') or '8000'
    if a.pruebas:
        if not (ROOT / 'scripts' / 'reset_demo.py').exists():
            print('Este paquete no trae el entorno de pruebas (es el zip de producción).'); sys.exit(1)
        port = '8100'
        p = ROOT / 'data' / 'pruebas'
        env.update({'WOD_DEMO_MODE': '1', 'WOD_ENV': 'demo', 'WOD_PORT': port, 'WOD_PUBLIC_URL': f'http://127.0.0.1:{port}',
                    'WOD_DB_PATH': str(p / 'worldives.sqlite3'), 'WOD_STORAGE_DIR': str(p / 'storage'), 'WOD_LOG_DIR': str(p / 'logs'),
                    'WOD_UPLOADS_DIR': str(p / 'subidas'), 'WOD_MAIL_FILE_DIR': str(p / 'correos'), 'WOD_BACKUP_DIR': str(p / 'copias'),
                    'WOD_ADMIN_TOTP_REQUIRED': '0', 'WOD_SMTP_HOST': ''})
        (p / 'correos').mkdir(parents=True, exist_ok=True)
        r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'reset_demo.py'), '--si-hace-falta'], env=env)
        if r.returncode != 0: print('No se han podido preparar los datos de prueba.'); sys.exit(1)
    if a.red_local: env['WOD_HOST'] = '0.0.0.0'
    if a.depuracion: env['WOD_ACCESS_LOG'] = 'stdout'
    url = f'http://localhost:{port}'
    print('=' * 64)
    print('  WORLDIVES DISCOVERY' + ('  ·  ENTORNO DE PRUEBAS' if a.pruebas else ''))
    print(f'  Abre {url}' + ('   (cuentas en README-PRUEBAS.md)' if a.pruebas else ''))
    if a.red_local: print(f'  Desde otro dispositivo de tu red: http://<IP de este ordenador>:{port}')
    print('  Para pararlo: Ctrl+C')
    print('=' * 64)
    if not (a.depuracion or a.sin_navegador):
        threading.Thread(target=lambda: (time.sleep(2), webbrowser.open(url)), daemon=True).start()
    try:
        sys.exit(subprocess.call([sys.executable, str(ROOT / 'app' / 'server.py')], env=env))
    except KeyboardInterrupt:
        pass


if __name__ == '__main__':
    main()
