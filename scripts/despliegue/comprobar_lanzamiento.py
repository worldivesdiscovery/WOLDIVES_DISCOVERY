#!/usr/bin/env python3
"""Lista de comprobación antes de abrir el piloto (encargo de despliegue v50.52), comprobada en el propio VPS.

    sudo python3 /opt/worldives/scripts/despliegue/comprobar_lanzamiento.py
    sudo python3 /opt/worldives/scripts/despliegue/comprobar_lanzamiento.py --markdown /root/lista-lanzamiento.md

Cada casilla sale como:
  OK      comprobada aquí y correcta
  FALLO   comprobada aquí e incorrecta (el detalle dice qué falta)
  A MANO  no se puede comprobar desde el servidor (ubicación del VPS, copia de las claves, abogado…): dice cómo hacerlo
Termina con código 1 si hay algún FALLO. Solo lee: no cambia nada del servidor ni de la base de datos.
"""
from __future__ import annotations

import argparse
import base64
import datetime as dt
import json
import os
import pwd
import re
import shlex
import shutil
import socket
import sqlite3
import ssl
import stat
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

OK, FALLO, MANO = 'OK', 'FALLO', 'A MANO'
DEMO_DATA_KEY = 'demo-data-key'   # placeholder: the real demo key is read from the code below when available
EICAR = 'KkgrSCQhRUxJRi1UU0VULVNVUklWSVROQS1EUkFETkFUUy1SQUNJRSR9NylDQzcpXlAoNDVYWlBcNFtQQUAlUCFPNVg='   # reversed, base64
PRIVATE_RANGES = '10.0.0.0/8 172.16.0.0/12 192.168.0.0/16 169.254.0.0/16 100.64.0.0/10 fc00::/7 fe80::/10'


def run(cmd, timeout=60, **kw):
    try:
        r = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout, **kw)
        return r.returncode, (r.stdout or '') + (r.stderr or '')
    except FileNotFoundError:
        return 127, f'no está instalado: {cmd[0]}'
    except subprocess.TimeoutExpired:
        return 124, 'no responde (tiempo agotado)'


def read_env(path: Path) -> dict:
    out = {}
    if not path.is_file(): return out
    for raw in path.read_text(encoding='utf-8', errors='replace').splitlines():
        line = raw.strip()
        if not line or line.startswith('#') or '=' not in line: continue
        k, _, v = line.partition('=')
        k = k.strip().removeprefix('export ').strip(); v = v.strip()
        if v[:1] in ('"', "'") and v[1:].find(v[0]) >= 0: v = v[1:1 + v[1:].find(v[0])]
        elif v.startswith('#'): v = ''
        elif ' #' in v: v = v[:v.find(' #')].strip()
        if v: out[k] = v
    return out


class Lista:
    def __init__(self):
        self.items = []

    def add(self, seccion, casilla, estado, detalle=''):
        detalle = ' '.join(str(detalle).split())          # one line, whatever the command printed
        self.items.append((seccion, casilla, estado, detalle))
        print(f'[{estado:6}] {seccion} · {casilla}' + (f'  — {detalle}' if detalle else ''), flush=True)

    def markdown(self):
        out = ['# Lista de comprobación antes de abrir el piloto', '',
               f'Generada en el VPS el {dt.datetime.now(dt.timezone.utc).strftime("%d/%m/%Y %H:%M")} UTC con '
               '`scripts/despliegue/comprobar_lanzamiento.py`.', '',
               '| Sección | Casilla | Estado | Cómo se ha comprobado / qué falta |', '|---|---|---|---|']
        for s, c, e, d in self.items:
            out.append(f'| {s} | {c} | **{e}** | {d.replace("|", "/")} |')
        return '\n'.join(out) + '\n'


def http_status(url, timeout=10):
    class NoRedirect(urllib.request.HTTPRedirectHandler):
        def redirect_request(self, *a, **k): return None
    opener = urllib.request.build_opener(NoRedirect)
    try:
        r = opener.open(urllib.request.Request(url, method='GET'), timeout=timeout)
        return r.status, r.headers.get('Location', '')
    except urllib.error.HTTPError as e:
        return e.code, e.headers.get('Location', '')
    except Exception as e:
        return None, f'{type(e).__name__}: {e}'


def cert_issuer(host, timeout=10):
    ctx = ssl.create_default_context()
    with socket.create_connection((host, 443), timeout=timeout) as s, ctx.wrap_socket(s, server_hostname=host) as t:
        cert = t.getpeercert()
    issuer = dict(x[0] for x in cert.get('issuer', ()))
    return issuer.get('organizationName', ''), cert.get('notAfter', '')


def parse_ufw(out):
    """(active, (incoming, outgoing) defaults, inbound ports, outbound ports) from «ufw status verbose»."""
    active = 'Status: active' in out
    d = re.search(r'Default: (\w+) \(incoming\), (\w+) \(outgoing\)', out)
    ins = sorted({int(p) for p in re.findall(r'^(\d+)(?:/\w+)?\s+(?:ALLOW|LIMIT) IN', out, re.M)})
    outs = sorted({int(p) for p in re.findall(r'^(\d+)(?:/\w+)?\s+ALLOW OUT', out, re.M)})
    return active, (d.groups() if d else None), ins, outs


def firewall_ok(out):
    active, defaults, ins, outs = parse_ufw(out)
    return bool(active and defaults == ('deny', 'deny') and set(ins) <= {22, 80, 443} and set(outs) <= {53, 67, 80, 123, 443, 465, 587})


def parse_sshd(out):
    """«sshd -T» → dict (lower case)."""
    return dict(l.split(' ', 1) for l in out.lower().splitlines() if ' ' in l)


def ssh_ok(cfg):
    return cfg.get('passwordauthentication') == 'no' and cfg.get('permitrootlogin') == 'no' \
        and cfg.get('kbdinteractiveauthentication', 'no') == 'no' and cfg.get('pubkeyauthentication', 'yes') == 'yes'


def key_problem(name, value, others):
    if len(value) < 32: return f'{name} tiene {len(value)} caracteres (mínimo 32)'
    if len(set(value)) < 8: return f'{name} no parece aleatoria'
    if value in others: return f'{name} es igual que otra clave'
    if value in (DEMO_DATA_KEY, 'x' * 40, 'clave-de-datos-de-las-pruebas-0123456789'): return f'{name} es una clave de pruebas'
    return ''


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--app', default='/opt/worldives', help='carpeta de producción')
    ap.add_argument('--pruebas', default='/opt/worldives-pruebas', help='carpeta del entorno de pruebas')
    ap.add_argument('--dominio', default='worlddivesdiscovery.com')
    ap.add_argument('--usuario', default='worldives', help='usuario del servicio')
    ap.add_argument('--restauracion-log', default='/var/log/worldives/restauracion.log')
    ap.add_argument('--sin-red', action='store_true', help='no prueba las direcciones públicas (HTTPS, certificado, www)')
    ap.add_argument('--markdown', help='escribe también la lista en este archivo .md')
    a = ap.parse_args()
    L = Lista(); app = Path(a.app); env = read_env(app / '.env'); dom = a.dominio
    global DEMO_DATA_KEY
    m = re.search(r"DEMO_DATA_KEY\s*=\s*'([^']+)'", (app / 'app' / 'wod' / 'cifrado.py').read_text(encoding='utf-8')) if (app / 'app' / 'wod' / 'cifrado.py').exists() else None
    if m: DEMO_DATA_KEY = m.group(1)

    # ------------------------------------------------------------------------------------------------ Servidor
    S = 'Servidor'
    osr = Path('/etc/os-release').read_text() if Path('/etc/os-release').exists() else ''
    cpus = os.cpu_count() or 0
    mem = 0
    try: mem = int(re.search(r'MemTotal:\s+(\d+)', Path('/proc/meminfo').read_text()).group(1)) / 1024 / 1024
    except Exception: pass
    lts = 'Ubuntu' in osr and 'LTS' in osr
    L.add(S, 'VPS KVM 2 con Ubuntu LTS', OK if lts and cpus >= 2 and mem >= 7 else FALLO,
          f'{re.search(r"PRETTY_NAME=\"?([^\"\n]+)", osr).group(1) if "PRETTY_NAME" in osr else "sistema desconocido"}, {cpus} vCPU, {mem:.1f} GB de RAM')
    L.add(S, 'Centro de datos en Alemania o Francia', MANO, 'hPanel → VPS → Información general: «Ubicación» debe decir Alemania (Frankfurt) o Francia. Nada en Reino Unido ni fuera de la UE.')
    code, out = run(['sshd', '-T'])
    cfg = parse_sshd(out) if code == 0 else {}
    keys = [p for p in Path('/home').glob('*/.ssh/authorized_keys') if p.stat().st_size > 0] if Path('/home').exists() else []
    L.add(S, 'Solo con clave SSH, sin contraseña ni root', OK if ssh_ok(cfg) and keys else FALLO,
          f"sshd -T: passwordauthentication={cfg.get('passwordauthentication', '?')}, permitrootlogin={cfg.get('permitrootlogin', '?')}, "
          f"kbdinteractiveauthentication={cfg.get('kbdinteractiveauthentication', '?')}; claves autorizadas en {len(keys)} usuario(s)")
    code, out = run(['ufw', 'status', 'verbose'])
    active, defaults, ins, outs = parse_ufw(out)
    L.add(S, 'Cortafuegos de entrada y salida', OK if firewall_ok(out) else FALLO,
          f"ufw {'activo' if active else 'NO activo'}; por defecto {defaults or '?'}; entrada {ins}; salida {outs} (scripts/despliegue/cortafuegos.sh)")
    code, out = run(['caddy', 'validate', '--config', '/etc/caddy/Caddyfile', '--adapter', 'caddyfile'])
    L.add(S, 'caddy validate correcto', OK if code == 0 and 'Valid configuration' in out else FALLO, out.strip().splitlines()[-1][:160] if out.strip() else '')
    if a.sin_red:
        L.add(S, 'HTTPS con Let\'s Encrypt; /api por http da 403; www → raíz', MANO, 'sin red (--sin-red)')
    else:
        st, _ = http_status(f'http://{dom}/api/health')
        L.add(S, '/api por http da 403', OK if st == 403 else FALLO, f'GET http://{dom}/api/health → {st}')
        try:
            org, until = cert_issuer(dom)
            L.add(S, 'HTTPS con Let\'s Encrypt', OK if "Let's Encrypt" in org else FALLO, f'emisor «{org}», caduca {until}')
        except Exception as e:
            L.add(S, 'HTTPS con Let\'s Encrypt', FALLO, f'{type(e).__name__}: {e}')
        st, loc = http_status(f'https://www.{dom}/centros')
        L.add(S, 'www redirige a la raíz', OK if st in (301, 308) and loc.startswith(f'https://{dom}/') else FALLO, f'https://www.{dom}/centros → {st} {loc}')
        st, _ = http_status(f'https://{dom}/api/health')
        L.add(S, 'La web responde por https', OK if st == 200 else FALLO, f'GET https://{dom}/api/health → {st}')
    # Antivirus: the same check as «Estado del sistema» (the EICAR test file must be caught)
    av = env.get('WOD_AV_COMMAND', '')
    c1, _ = run(['systemctl', 'is-active', 'clamav-daemon']); c2, _ = run(['systemctl', 'is-active', 'clamav-freshclam'])
    if av:
        try:
            r = subprocess.run(shlex.split(av), input=base64.b64decode(EICAR)[::-1], capture_output=True, timeout=30, user=a.usuario)
            caught = r.returncode == 1
        except Exception as e:
            caught = False; av += f' ({type(e).__name__})'
    else:
        caught = False
    daily = [p for p in Path('/var/lib/clamav').glob('daily.c?d')] if Path('/var/lib/clamav').exists() else []
    fresh = bool(daily) and (dt.datetime.now().timestamp() - max(p.stat().st_mtime for p in daily)) < 3 * 86400
    L.add(S, 'ClamAV activo y en verde en «Estado del sistema»', OK if caught and c1 == 0 and c2 == 0 and fresh else FALLO,
          f"clamd {'activo' if c1 == 0 else 'parado'}, freshclam {'activo' if c2 == 0 else 'parado'}, firmas {'al día' if fresh else 'antiguas o ausentes'}; "
          f"WOD_AV_COMMAND {'detecta' if caught else 'NO detecta'} el archivo de prueba EICAR")
    code, out = run(['timedatectl', 'show', '-p', 'NTPSynchronized', '--value'])
    L.add(S, 'NTP sincronizado', OK if out.strip() == 'yes' else FALLO, f'timedatectl NTPSynchronized={out.strip() or "?"}')
    envp = app / '.env'
    if envp.exists():
        stt = envp.stat(); owner = pwd.getpwuid(stt.st_uid).pw_name
        mode_ok = stat.S_IMODE(stt.st_mode) == 0o600 and owner == a.usuario
        keys = {k: env.get(k, '') for k in ('WOD_SECRET_KEY', 'WOD_DATA_KEY', 'WOD_BACKUP_KEY')}
        probs = [key_problem(k, v, [w for kk, w in keys.items() if kk != k]) for k, v in keys.items()]
        probs = [p for p in probs if p]
        pr = read_env(Path(a.pruebas) / '.env')
        if pr and any(pr.get(k) and pr.get(k) == v for k, v in keys.items()): probs.append('alguna clave es igual que la del entorno de pruebas')
        setting = []
        if env.get('WOD_ENV') != 'production': setting.append('WOD_ENV no es production')
        if env.get('WOD_PUBLIC_URL') != f'https://{dom}': setting.append(f'WOD_PUBLIC_URL={env.get("WOD_PUBLIC_URL")!r}')
        if env.get('WOD_DEMO_MODE'): setting.append('WOD_DEMO_MODE no debe estar')
        for k in ('WOD_ADMIN_TOTP_REQUIRED', 'WOD_PAYMENTS_TOTP_REQUIRED'):
            if env.get(k, '1') in ('0', 'false', 'no', 'off'): setting.append(f'{k}=0')
        L.add(S, '.env con permisos 600 y claves nuevas de producción', OK if mode_ok and not probs and not setting else FALLO,
              f'permisos {oct(stat.S_IMODE(stt.st_mode))}, propietario {owner}; ' + ('; '.join(probs + setting) or 'claves de 32+ caracteres, distintas entre sí y de las de pruebas'))
    else:
        L.add(S, '.env con permisos 600 y claves nuevas de producción', FALLO, f'no existe {envp}')
    L.add(S, 'Copia de las claves fuera del servidor', MANO, 'Comprueba en el gestor de contraseñas del titular que están WOD_SECRET_KEY, WOD_DATA_KEY y WOD_BACKUP_KEY (sin WOD_DATA_KEY y WOD_BACKUP_KEY no se pueden restaurar las copias).')
    dbp = Path(env.get('WOD_DB_PATH') or app / 'data' / 'worldivesdiscovery.sqlite3')
    leftovers = [p for p in ('.git', 'CUENTAS-DEMO.txt', 'data/pruebas', 'data/demo', 'scripts/crear_demo.py') if (app / p).exists()]
    users = admins = admins_2fa = test_accounts = 0; db_err = ''
    try:
        db = sqlite3.connect(f'file:{dbp}?mode=ro', uri=True)
        users = db.execute('SELECT COUNT(*) FROM users').fetchone()[0]
        admins = db.execute("SELECT COUNT(*) FROM users WHERE role='admin'").fetchone()[0]
        admins_2fa = db.execute("SELECT COUNT(*) FROM users WHERE role='admin' AND COALESCE(totp_enabled,0)=1").fetchone()[0]
        test_accounts = db.execute("SELECT COUNT(*) FROM users WHERE lower(username) LIKE '%.prueba' OR lower(email) LIKE '%@example.com' OR lower(email) LIKE '%.prueba@%'").fetchone()[0]
        db.close()
    except Exception as e:
        db_err = f'{type(e).__name__}: {e}'
    L.add(S, 'Instalado desde el zip de PRODUCCIÓN, sin .git, base limpia, admin con --create-admin',
          OK if not leftovers and not db_err and admins >= 1 and test_accounts == 0 else FALLO,
          db_err or ((f'sobran: {", ".join(leftovers)}' if leftovers else 'sin .git ni restos de la demo')
                     + f'; {users} usuarios, {admins} administradores, {test_accounts} cuentas de prueba'))
    L.add(S, 'Verificación en dos pasos activada en la cuenta de administración', OK if admins and admins_2fa == admins else FALLO, f'{admins_2fa} de {admins} administradores con la verificación activada')
    # extra (brief, points 6, 10 and 11)
    code, out = run(['systemctl', 'is-enabled', 'unattended-upgrades'])
    auto = Path('/etc/apt/apt.conf.d/20auto-upgrades')
    auto_ok = code == 0 and auto.exists() and re.search(r'Unattended-Upgrade\s+"1"', auto.read_text())
    L.add(S, 'Actualizaciones de seguridad automáticas', OK if auto_ok else FALLO, f'unattended-upgrades {out.strip() or "?"}; {auto} {"con" if auto_ok else "sin"} Unattended-Upgrade "1"')
    jc = ' '.join(p.read_text() for p in [Path('/etc/systemd/journald.conf'), *Path('/etc/systemd/journald.conf.d').glob('*.conf')] if p.exists()) if Path('/etc/systemd').exists() else ''
    L.add(S, 'Diario del sistema: 30 días', OK if re.search(r'^\s*MaxRetentionSec\s*=\s*30day', jc, re.M) else FALLO, 'MaxRetentionSec=30day en journald.conf')
    code, out = run(['systemd-run', '--wait', '--pipe', '--quiet', '-p', f'User={a.usuario}', '-p', f'IPAddressDeny={PRIVATE_RANGES}', 'python3', '-c',
                     "import urllib.request,urllib.error\ntry: urllib.request.urlopen('https://api.stripe.com/v1', timeout=15)\nexcept urllib.error.HTTPError as e: print('http', e.code)"], timeout=60)
    L.add(S, 'La web sale a internet con el cortafuegos y IPAddressDeny', OK if code == 0 and 'http 401' in out else FALLO, f'HTTPS a api.stripe.com con las mismas restricciones que el servicio → {out.strip()[:120] or code}')
    pr_env = read_env(Path(a.pruebas) / '.env')
    c_pr, _ = run(['systemctl', 'is-active', 'worldives-pruebas'])
    pr_probs = []
    if c_pr != 0: pr_probs.append('worldives-pruebas parado')
    if pr_env.get('WOD_PUBLIC_URL') != f'https://pruebas.{dom}': pr_probs.append(f'WOD_PUBLIC_URL={pr_env.get("WOD_PUBLIC_URL")!r}')
    if not pr_env.get('STRIPE_SECRET_KEY', 'sk_test_').startswith('sk_test_'): pr_probs.append('Stripe de pruebas debe usar sk_test_')
    if Path(pr_env.get('WOD_DB_PATH') or Path(a.pruebas) / 'data' / 'worldivesdiscovery.sqlite3').resolve() == dbp.resolve(): pr_probs.append('usa la misma base que producción')
    if not a.sin_red:
        st, _ = http_status(f'https://pruebas.{dom}/')
        if st != 401: pr_probs.append(f'https://pruebas.{dom}/ sin contraseña → {st} (debe ser 401)')
    L.add(S, f'Entorno de pruebas (pruebas.{dom}) separado y con contraseña', OK if not pr_probs else FALLO, '; '.join(pr_probs) or 'servicio propio, base propia, sk_test_ y autenticación básica')

    # ------------------------------------------------------------------------------------------------ Copias y registros
    C = 'Copias y registros'
    remote_ok, last = False, ''
    cmd = env.get('WOD_BACKUP_COMMAND', '')
    if cmd:
        parts = cmd.split(); dest = parts[1] if len(parts) > 1 else 'externo:worldives-backups'
        home = pwd.getpwnam(a.usuario).pw_dir
        code, out = run(['sudo', '-u', a.usuario, 'env', f'HOME={home}', 'rclone', 'lsf', f'{dest}/db/', '--files-only'], timeout=120)
        names = sorted(l.strip() for l in out.splitlines() if l.strip().endswith(('.gz', '.sqlite3')))
        if code == 0 and names:
            last = names[-1]; m = re.search(r'(\d{8})-(\d{4})', last)
            age = (dt.datetime.now() - dt.datetime.strptime(''.join(m.groups()), '%Y%m%d%H%M')).total_seconds() / 3600 if m else 999
            remote_ok = age < 3
            last += f' (hace {age:.1f} h)'
        else:
            last = out.strip()[:160]
    rest = Path(a.restauracion_log)
    rest_line = rest.read_text().strip().splitlines()[-1] if rest.exists() and rest.read_text().strip() else ''
    rest_ok = False
    if rest_line and ' ok ' in rest_line:
        try: rest_ok = (dt.datetime.now(dt.timezone.utc) - dt.datetime.fromisoformat(rest_line.split()[0].replace('Z', '+00:00'))).days <= 35
        except ValueError: pass
    L.add(C, 'Copias externas funcionando', OK if remote_ok else FALLO, f'WOD_BACKUP_COMMAND {"puesto" if cmd else "NO puesto"}; última copia externa: {last or "ninguna"}')
    L.add(C, 'Restauración de prueba hecha', OK if rest_ok else FALLO, rest_line[:200] or f'sin resultado en {rest} (scripts/despliegue/restauracion_prueba.sh)')
    c_v, _ = run(['systemctl', 'is-active', 'vector'])
    bs = Path('/etc/vector/betterstack.env')
    bs_env = read_env(bs) if bs.exists() else {}
    bs_mode = stat.S_IMODE(bs.stat().st_mode) if bs.exists() else None
    code, out = run(['vector', 'validate', '--no-environment', '/etc/vector/vector.yaml'], env={**os.environ, **bs_env})
    host = bs_env.get('BETTERSTACK_HOST', '')
    bs_ok = c_v == 0 and bs_mode == 0o600 and bs_env.get('BETTERSTACK_TOKEN') and host and code == 0
    L.add(C, 'Registros llegando a Better Stack (región UE)', OK if bs_ok else FALLO,
          f"vector {'activo' if c_v == 0 else 'parado'}; {bs} {'permisos ' + oct(bs_mode) if bs_mode is not None else 'no existe'}; host «{host or '?'}»; "
          f"vector validate {'correcto' if code == 0 else 'con errores'}. En Better Stack: la fuente debe estar en la región Europa y recibir líneas «servicio: worldives» y «servicio: caddy».")
    L.add(C, 'Alertas probadas', MANO, 'Provoca cada una (docs/despliegue/GUIA-VPS.md, paso 9.4) y comprueba que llega el correo: 500 seguidos, pico de inicios fallidos, firma falsa, accesos denegados, /api/health caído.')

    # ------------------------------------------------------------------------------------------------ Código
    K = 'Código'
    srv = (app / 'app' / 'server.py').read_text(encoding='utf-8') if (app / 'app' / 'server.py').exists() else ''
    ver = re.search(r"APP_VERSION = '([\d.]+)'", srv)
    vtuple = tuple(int(x) for x in ver.group(1).split('.')) if ver else (0,)
    L.add(K, 'Verificación en dos pasos obligatoria para centros con cobros, con sus pruebas',
          OK if vtuple >= (50, 52) and env.get('WOD_PAYMENTS_TOTP_REQUIRED', '1') not in ('0', 'false', 'no', 'off') else FALLO,
          f'versión {ver.group(1) if ver else "?"}; WOD_PAYMENTS_TOTP_REQUIRED {"activa" if env.get("WOD_PAYMENTS_TOTP_REQUIRED", "1") != "0" else "apagada"}; pruebas: tests/test_v50_52_cobros_2fa.py')
    L.add(K, 'Batería completa en verde en el servidor de pruebas', MANO,
          f'cd {a.pruebas}/tests && sudo -u worldives-pruebas ../.venv/bin/python -m unittest discover   (y pytest tests/test_v50_51_asvs.py)')
    L.add(K, 'Prueba de carga en el VPS real', MANO, 'docs/auditoria/v50.51/carga.md: contra pruebas.<dominio>, por escalones; si la CPU se frena (Hostinger reduce la CPU con uso alto sostenido), pasar a KVM 4.')
    L.add(K, 'Reserva completa con pago real pequeño en Stripe y su devolución', MANO, 'Con sk_live_ en producción: un servicio de 1 €, reservar y pagar con una tarjeta propia, devolver desde la reserva y comprobar el aviso de Stripe en Administración → Pagos.')

    # ------------------------------------------------------------------------------------------------ Legal y cuentas
    G = 'Legal y cuentas'
    for c, d in (('SL constituida y datos puestos en Administración → Legal', 'Lo cierra el titular.'),
                 ('Stripe a nombre de la SL', 'Lo cierra el titular.'),
                 ('Textos legales actualizados y revisados por un abogado', 'docs/legal/cambios-v50.52-para-abogado.md')):
        L.add(G, c, MANO, d)
    for c, d in (('Prueba de intrusión independiente', 'Después del piloto, antes de abrir a todos.'),
                 ('Better Stack en plan de pago (30 días de retención)', 'Plan Nano en región UE antes de abrir a todos; la política de privacidad dice 30 días.')):
        L.add('Después del piloto', c, MANO, d)

    if a.markdown:
        Path(a.markdown).write_text(L.markdown(), encoding='utf-8'); print(f'\nLista escrita en {a.markdown}')
    fallos = sum(1 for x in L.items if x[2] == FALLO)
    print(f"\n{sum(1 for x in L.items if x[2] == OK)} OK · {fallos} FALLO · {sum(1 for x in L.items if x[2] == MANO)} A MANO")
    return 1 if fallos else 0


if __name__ == '__main__':
    sys.exit(main())
