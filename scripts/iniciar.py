#!/usr/bin/env python3
"""Single start of WORLDIVES DISCOVERY (v50.46). Called by iniciar.bat / iniciar.sh (and iniciar-pruebas.*).

    iniciar                 the web on http://localhost:8000
    iniciar --red-local     also reachable from other devices of the same network (WOD_HOST=0.0.0.0)
    iniciar --pruebas --red-local   the test environment for the WORLDIVES Pruebas app: the phone opens
                            http://<IP of this computer>:8100 (v50.48; also iniciar-pruebas-movil.bat / .sh)
    iniciar --depuracion    every request is written in this window (WOD_ACCESS_LOG=stdout), no browser
    iniciar --pruebas       TEST ENVIRONMENT (zip «-pruebas»): port 8100, «Entorno de pruebas» band, test accounts,
                            emails saved in data/pruebas/correos, demonstration data with dates from today, and (v50.56)
                            the example website of a dive centre on http://localhost:8101 with the booking widget

The first time it installs what requirements.txt asks for (stripe, qrcode, fonttools, cryptography, Pillow) if it is missing,
and again whenever an installed version is not the one fixed there.
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
NEEDED = {'stripe': 'stripe', 'qrcode': 'qrcode', 'fontTools': 'fonttools', 'cryptography': 'cryptography', 'PIL': 'Pillow'}


def pinned():
    """{package: version} from requirements.txt (every line is «package==version»)."""
    out = {}
    for line in (ROOT / 'requirements.txt').read_text(encoding='utf-8').splitlines():
        line = line.split('#')[0].strip()
        if '==' in line:
            name, ver = line.split('==', 1); out[name.strip().lower()] = ver.strip()
    return out


def ensure_requirements():
    from importlib import metadata
    want = pinned()
    def wrong(pkg):
        try: return metadata.version(pkg) != want.get(pkg.lower(), metadata.version(pkg))
        except metadata.PackageNotFoundError: return True
    missing = [pkg for mod, pkg in NEEDED.items() if importlib.util.find_spec(mod) is None or wrong(pkg)]
    if not missing: return
    print(f'Instalando las versiones de requirements.txt ({", ".join(missing)})…')
    r = subprocess.run([sys.executable, '-m', 'pip', 'install', '--user', '-r', str(ROOT / 'requirements.txt')])
    if r.returncode != 0:
        r = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', str(ROOT / 'requirements.txt')])
    if r.returncode != 0:
        print('No se han podido instalar las dependencias. Ejecuta a mano:  python -m pip install -r requirements.txt'); sys.exit(1)


def lan_ip():
    """The address of this computer in its local network (wifi), or None. Nothing is sent: a UDP «connect» only asks
    the system which interface it would use."""
    import socket
    try:
        with socket.socket(socket.AF_INET, socket.SOCK_DGRAM) as s:
            s.connect(('10.255.255.255', 1)); ip = s.getsockname()[0]
        return None if ip.startswith('127.') else ip
    except OSError:
        return None


def example_site(public_url: str, db_path: str, host: str):
    """v50.56: the website of a dive centre, as an example (README-PRUEBAS, «Probar el motor multicanal»): a plain page on
    another address (http://localhost:8101) with the widget of Bahía Coralina, the first centre of the demo, in its three formats.
    Built from scripts/demo/web-de-centro-ejemplo.html each time the test environment starts."""
    import http.server
    import sqlite3
    tpl = ROOT / 'scripts' / 'demo' / 'web-de-centro-ejemplo.html'
    if not tpl.exists(): return None
    sid = ''
    try:
        c = sqlite3.connect(f'file:{db_path}?mode=ro', uri=True)
        try:
            r = c.execute("""SELECT s.id FROM provider_services s JOIN sales_settings ss ON ss.provider_kind='center' AND ss.provider_id=s.center_id
                             WHERE ss.slug='bahia-coralina' AND s.title='Snorkel en la Granadella' AND s.active=1""").fetchone()
            sid = str(r[0]) if r else ''
        finally: c.close()
    except sqlite3.Error:
        pass
    folder = ROOT / 'data' / 'pruebas' / 'web-centro'
    folder.mkdir(parents=True, exist_ok=True)
    html = tpl.read_text(encoding='utf-8').replace('__WORLDIVES__', public_url).replace('__CENTRO__', 'bahia-coralina').replace('__SERVICIO__', sid)
    (folder / 'index.html').write_text(html, encoding='utf-8')

    class Quiet(http.server.SimpleHTTPRequestHandler):
        def __init__(self, *a, **k): super().__init__(*a, directory=str(folder), **k)
        def log_message(self, *a): pass
    try:
        httpd = http.server.ThreadingHTTPServer((host, 8101), Quiet)
    except OSError:
        print('  (La web de ejemplo no arranca: el puerto 8101 está ocupado.)'); return None
    threading.Thread(target=httpd.serve_forever, daemon=True).start()
    return 'http://localhost:8101'


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
                    'WOD_ADMIN_TOTP_REQUIRED': '0', 'WOD_PAYMENTS_TOTP_REQUIRED': '0', 'WOD_SMTP_HOST': ''})
        (p / 'correos').mkdir(parents=True, exist_ok=True)
        r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'reset_demo.py'), '--si-hace-falta'], env=env)
        if r.returncode != 0: print('No se han podido preparar los datos de prueba.'); sys.exit(1)
    ip = None
    if a.red_local:
        env['WOD_HOST'] = '0.0.0.0'
        # WOD_IP_MOVIL: the address the phone uses when it is not this computer's wifi address (the Android emulator of
        # the automatic checks reaches the computer at 10.0.2.2).
        ip = env.get('WOD_IP_MOVIL') or lan_ip()
        if a.pruebas and ip:
            # v50.48: the phone (WORLDIVES Pruebas) uses http://<ip>:8100. Links, payments and the check of where each
            # request comes from use that address; the browser of this computer keeps working with localhost.
            local = f'http://localhost:{port},http://127.0.0.1:{port}'
            extra = env.get('WOD_ALLOWED_ORIGINS', '')
            env.update({'WOD_PUBLIC_URL': f'http://{ip}:{port}', 'WOD_ALLOWED_ORIGINS': ','.join(x for x in (extra, local) if x)})
    if a.depuracion: env['WOD_ACCESS_LOG'] = 'stdout'
    url = f'http://localhost:{port}'
    site = example_site(env['WOD_PUBLIC_URL'], env['WOD_DB_PATH'], '0.0.0.0' if a.red_local else '127.0.0.1') if a.pruebas else None
    print('=' * 64)
    print('  WORLDIVES DISCOVERY' + ('  ·  ENTORNO DE PRUEBAS' if a.pruebas else ''))
    print(f'  Abre {url}' + ('   (cuentas en README-PRUEBAS.md)' if a.pruebas else ''))
    if site: print(f'  Web de ejemplo de un centro, con el widget de reservas: {site}')
    if a.red_local:
        if ip: print(f'  En el móvil (misma wifi), escribe:  http://{ip}:{port}')
        else: print(f'  Desde otro dispositivo de tu red: http://<IP de este ordenador>:{port}')
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
