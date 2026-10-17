#!/usr/bin/env python3
"""Prepara la base de datos de CARGA de WORLDIVES DISCOVERY y arranca el servidor para medirlo.

    python3 tests/carga/preparar.py construir --dir /tmp/wod-carga --buzos 500 --centros 20 --dias 30 --plazas 40
    python3 tests/carga/preparar.py arrancar  --dir /tmp/wod-carga --workers 4 [--pagos stripe-sim|centro] [--puerto 8300]
    python3 tests/carga/preparar.py parar     --dir /tmp/wod-carga
    python3 tests/carga/preparar.py sesiones  --dir /tmp/wod-carga   (v50.57: sesiones y salidas para la clase Reservas)
    python3 tests/carga/preparar.py comprobar --dir /tmp/wod-carga   (v50.57: al terminar, plazas y reservas repetidas en la base)
    python3 tests/carga/preparar.py todo      --dir /tmp/wod-carga --workers 4        (construir + arrancar)

construir
    1. Base de pruebas de siempre (scripts/crear_demo.py: centro.prueba, freelance.prueba, buzo.prueba…).
    2. Un servidor temporal sobre una copia y, por la API de la web (como una persona: contraseñas PBKDF2 y teléfonos
       cifrados los pone el propio servidor):
         - N cuentas de buceador  carga.buzo00001 … (contraseña CARGA_PASSWORD)
         - M centros de carga verificados (carga.centro01 …) con plan «pro», cuenta de cobros de prueba, puntos
           asociados y 3 servicios (2 «bajo petición», 1 «pago al reservar»)
         - salidas futuras con plazas para TODOS los servicios por salidas (también los de la demo) durante D días.
    3. Deja en --dir:  carga-base.sqlite3 (la base), cuentas.json (cuentas para Locust) y meta.json.
    Las iteraciones de PBKDF2 (--pbkdf2, 600 000 por defecto = producción) quedan guardadas: el servidor de la
    prueba se arranca con las mismas para que el inicio de sesión cueste lo mismo que en producción.

arrancar
    Copia limpia de carga-base.sqlite3 en --dir/run/ y arranca app/server.py con WOD_WORKERS=N, en segundo plano.
    Escribe --dir/run/estado.json (URL, PID, base, logs…) que leen locustfile.py y medir.py.
    --pagos stripe-sim (por defecto): STRIPE_SECRET_KEY de prueba + WOD_STRIPE_API_BASE apuntando a un simulador local
        (tests/stripe_mock.py) con un puerto de control para «pagar» una sesión (lo que haría la persona en la página de
        Stripe). NUNCA se llama al Stripe real.
    --pagos centro: sin claves de Stripe. Los servicios «pago al reservar» no se pueden reservar; las reservas «bajo
        petición» se aceptan y el centro registra el cobro en el centro (POST /api/bookings/<id>/payment).
    --correo smtp (por defecto, v50.57): los correos salen por SMTP, como en producción, a un servidor local que los
        recibe y no los envía a nadie. --correo archivos: se escriben como .eml (lo que hace el paquete DEMO).
    Las copias de seguridad automáticas se desactivan (WOD_BACKUP=off) salvo --con-copias: una copia de la base en mitad
    de un escalón falsearía la medida.

Requisitos: Python 3.11+, las dependencias de requirements.txt (stripe, cryptography…) y, para medir, `pip install locust psutil`.
"""
from __future__ import annotations

import argparse
import concurrent.futures as cf
import datetime as dt
import json
import os
import random
import shutil
import signal
import socket
import sqlite3
import subprocess
import sys
import time
import types
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
TESTS = ROOT / 'tests'
sys.path.insert(0, str(TESTS))
from helpers import Client  # noqa: E402

DEMO_PASSWORD = 'Worldives-Prueba-2026'
CARGA_PASSWORD = 'Carga-Worldives-2026'
ADMIN_USER = 'carga.admin'
ADMIN_PASSWORD = 'Carga-Admin-Worldives-2026'
SECRET_KEY = 'x' * 40            # la misma clave con la que scripts/crear_demo.py crea la base de pruebas
DEFAULT_DIR = Path(os.environ.get('WOD_CARGA_DIR') or '/tmp/wod-carga')
CITIES = [('Xàbia', 38.79, 0.18), ('Dénia', 38.84, 0.11), ('Calp', 38.64, 0.07), ('Altea', 38.60, -0.05), ("L'Estartit", 42.05, 3.20),
          ('Cartagena', 37.60, -0.98), ('Tossa de Mar', 41.72, 2.93), ('Cabo de Palos', 37.63, -0.69), ('Lanzarote', 29.04, -13.63),
          ('El Hierro', 27.64, -17.98), ('Tenerife', 28.29, -16.62), ('Mallorca', 39.57, 2.65), ('Menorca', 39.95, 4.11), ('Almería', 36.83, -2.46)]


# ----------------------------------------------------------------------------------------------- utilidades
def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


def free_port() -> int:
    s = socket.socket(); s.bind(('127.0.0.1', 0)); p = s.getsockname()[1]; s.close(); return p


def demo_data_key():
    sys.path.insert(0, str(ROOT / 'app'))
    from wod.cifrado import DEMO_DATA_KEY
    return DEMO_DATA_KEY


def server_env(run_dir: Path, db: Path, port: int, host: str, public_host: str, workers: int, iterations: int,
               pagos: str = 'centro', stripe_base: str | None = None, backups: bool = False, extra: dict | None = None,
               smtp_port: int | None = None) -> dict:
    """Entorno del servidor de carga: el de tests/helpers.py (desarrollo, sin servicios externos) con los límites de
    registro abiertos y, por defecto, sin copias de seguridad automáticas."""
    env = dict(os.environ)
    for k in ('STRIPE_SECRET_KEY', 'STRIPE_WEBHOOK_SECRET', 'STRIPE_CONNECT_WEBHOOK_SECRET', 'WOD_STRIPE_API_BASE', 'WOD_SMTP_HOST',
              'ARCGIS_API_KEY', 'WOD_DEMO_MODE', 'WOD_ALLOW_SETUP'):
        env.pop(k, None)
    env.update({
        'WOD_DB_PATH': str(db), 'WOD_STORAGE_DIR': str(run_dir / 'storage'), 'WOD_LOG_DIR': str(run_dir / 'logs'), 'WOD_DATA_DIR': str(run_dir),
        'WOD_UPLOADS_DIR': str(run_dir / 'uploads'), 'WOD_MAIL_FILE_DIR': str(run_dir / 'mail'), 'WOD_PORT': str(port), 'WOD_HOST': host,
        'WOD_PUBLIC_URL': f'http://{public_host}:{port}', 'WOD_ENV': 'development', 'WOD_SECRET_KEY': SECRET_KEY, 'WOD_DATA_KEY': demo_data_key(),
        'WOD_ADMIN_TOTP_REQUIRED': '0', 'WOD_PAYMENTS_TOTP_REQUIRED': '0', 'WOD_PBKDF2_ITERATIONS': str(iterations), 'WOD_REGISTER_MAX_PER_HOUR': '10000000',
        'WOD_NO_ENV_FILE': '1', 'PYTHONDONTWRITEBYTECODE': '1', 'WOD_WORKERS': str(workers), 'PYTHONUNBUFFERED': '1',
        # Como detrás de nginx: el generador manda X-Forwarded-For con una IP distinta por usuario simulado, así los
        # límites por IP, las visitas únicas (stat_bump) y los registros funcionan como con visitantes reales.
        'WOD_TRUSTED_PROXIES': '127.0.0.1,::1',
        # 20 reservas por segundo con 500 cuentas son una reserva por cuenta cada 25 s; en la realidad serían miles de
        # personas distintas. El límite de 20 reservas por persona y hora se sube (se sigue consultando en cada reserva).
        'WOD_BOOKING_MAX_PER_HOUR': '1000000',
    })
    if not backups: env['WOD_BACKUP'] = 'off'
    if pagos == 'stripe-sim':
        env.update({'STRIPE_SECRET_KEY': 'sk_test_carga_simulada', 'WOD_STRIPE_API_BASE': stripe_base})
    if smtp_port:
        # Como en producción: los correos salen por SMTP (aquí, a un servidor local que los recibe y no los envía a nadie).
        env.update({'WOD_SMTP_HOST': '127.0.0.1', 'WOD_SMTP_PORT': str(smtp_port), 'WOD_SMTP_SECURITY': 'none'})
    env.update(extra or {})
    return env


def wait_health(base: str, proc=None, timeout=60, err_file: Path | None = None):
    t0 = time.time()
    while time.time() - t0 < timeout:
        try:
            urllib.request.urlopen(base + '/api/health', timeout=2).read(); return True
        except Exception:
            if proc is not None and proc.poll() is not None:
                raise RuntimeError('El servidor no arranca:\n' + (err_file.read_text()[-3000:] if err_file and err_file.exists() else ''))
            time.sleep(0.2)
    raise RuntimeError(f'El servidor {base} no responde')


def start_server(env: dict, run_dir: Path, tag='servidor'):
    run_dir.mkdir(parents=True, exist_ok=True)
    out = open(run_dir / f'{tag}.out.log', 'a'); err = open(run_dir / f'{tag}.err.log', 'a')
    proc = subprocess.Popen([sys.executable, str(ROOT / 'app' / 'server.py')], env=env, cwd=str(run_dir), stdout=out, stderr=err,
                            start_new_session=True)
    out.close(); err.close()
    return proc


def stop_pgid(pid: int, timeout=15):
    """Para el servidor y sus procesos hijos (WOD_WORKERS hace fork: comparten grupo de procesos)."""
    try: pgid = os.getpgid(pid)
    except ProcessLookupError: return
    for sig in (signal.SIGTERM, signal.SIGKILL):
        try: os.killpg(pgid, sig)
        except ProcessLookupError: return
        t0 = time.time()
        while time.time() - t0 < timeout:
            try: os.waitpid(pid, os.WNOHANG)      # si es hijo nuestro, que no quede como zombi
            except ChildProcessError: pass
            if not _group_alive(pgid): return
            time.sleep(0.2)


def _group_alive(pgid: int) -> bool:
    """¿Queda algún proceso vivo (no zombi) en el grupo?"""
    try:
        os.killpg(pgid, 0)
    except ProcessLookupError:
        return False
    try:
        import psutil
        return any(p.info['status'] != psutil.STATUS_ZOMBIE for p in psutil.process_iter(['pid', 'status']) if _pgid(p.pid) == pgid)
    except ImportError:
        return True


def _pgid(pid):
    try: return os.getpgid(pid)
    except (ProcessLookupError, PermissionError): return None


def _fold(value):
    """Igual que fold_text() del servidor: minúsculas sin acentos."""
    import unicodedata
    if value is None: return ''
    return ''.join(ch for ch in unicodedata.normalize('NFKD', str(value).lower()) if not unicodedata.combining(ch))


def sql_exec(db: Path, env: dict, statements: list[tuple[str, tuple]]):
    """SQL directo (con las funciones del servidor: los disparadores de la base cifran teléfonos con wod_cifrar)."""
    from helpers import cifrado_for
    cif = cifrado_for(env)
    c = sqlite3.connect(db, timeout=30)
    c.create_function('wod_cifrar', 1, cif.sql_encrypt); c.create_function('wod_huella', 1, cif.sql_fingerprint)
    c.create_function('fold', 1, _fold, deterministic=True)
    c.row_factory = sqlite3.Row
    try:
        out = []
        for q, a in statements:
            out.append([dict(r) for r in c.execute(q, a).fetchall()])
        c.commit()
        return out
    finally:
        c.close()


def copy_db(src: Path, dst: Path):
    """Copia coherente (incluye lo que esté en el WAL)."""
    dst.parent.mkdir(parents=True, exist_ok=True)
    for suf in ('', '-wal', '-shm'):
        p = Path(str(dst) + suf)
        if p.exists(): p.unlink()
    s = sqlite3.connect(src); d = sqlite3.connect(dst)
    try: s.backup(d)
    finally: d.close(); s.close()


def client(base):
    c = Client(types.SimpleNamespace(base=base))
    c.admin_reason = 'preparación de la prueba de carga'
    return c


def ok(r, what):
    if r.status != 200: raise RuntimeError(f'No se ha podido {what}: {r.status} {r.body[:300]!r}')
    return r.json


def day(n):
    return (dt.date.today() + dt.timedelta(days=n)).isoformat()


# ----------------------------------------------------------------------------------------------- construir
def construir(a):
    work = Path(a.dir).resolve(); work.mkdir(parents=True, exist_ok=True)
    demo = work / 'demo.sqlite3'
    if not demo.exists() or not a.reusar_demo:
        log('Creando la base de pruebas (scripts/crear_demo.py)…')
        r = subprocess.run([sys.executable, str(ROOT / 'scripts' / 'crear_demo.py'), '--out', str(demo)], capture_output=True, text=True)
        if r.returncode != 0: raise SystemExit(r.stdout + r.stderr)
    tmp = work / 'construccion'; shutil.rmtree(tmp, ignore_errors=True); tmp.mkdir()
    db = tmp / 'carga.sqlite3'; copy_db(demo, db)
    port = free_port(); base = f'http://127.0.0.1:{port}'
    env = server_env(tmp, db, port, '127.0.0.1', '127.0.0.1', max(1, a.workers_construccion), a.pbkdf2)
    # Administración temporal para aprobar los centros de carga (se queda en la base: carga.admin).
    env_cli = dict(env, WOD_ADMIN_PASSWORD=ADMIN_PASSWORD, WOD_WORKERS='1')
    r = subprocess.run([sys.executable, str(ROOT / 'app' / 'server.py'), '--create-admin', '--email', 'carga.admin@carga.example.org', '--username', ADMIN_USER,
                        '--name', 'Administración Carga'], env=env_cli, cwd=str(tmp), capture_output=True, text=True, timeout=300)
    if r.returncode != 0: raise SystemExit(r.stdout + r.stderr)
    proc = start_server(env, tmp, 'construccion')
    rnd = random.Random(a.semilla)
    try:
        wait_health(base, proc, err_file=tmp / 'construccion.err.log')
        t0 = time.time()
        # --- buceadores -----------------------------------------------------------------------------
        def reg_diver(i):
            u = f'carga.buzo{i:05d}'
            r = client(base).register(f'Buceador Carga {i:05d}', f'carga.buzo{i:05d}@carga.example.org', u, CARGA_PASSWORD)
            if r.status != 200 and 'Ya existe' not in (r.json or {}).get('error', ''):
                raise RuntimeError(f'registro {u}: {r.status} {r.body[:200]!r}')
            return u
        log(f'Registrando {a.buzos} buceadores por la API (PBKDF2 {a.pbkdf2} iteraciones)…')
        with cf.ThreadPoolExecutor(max_workers=a.hilos) as ex:
            divers = list(ex.map(reg_diver, range(1, a.buzos + 1)))
        log(f'  {len(divers)} buceadores en {time.time() - t0:.0f} s')

        # --- centros de carga -----------------------------------------------------------------------
        admin = client(base); ok(admin.login(ADMIN_USER, ADMIN_PASSWORD), 'entrar como administración')
        points = [p['id'] for p in ok(admin.get('/api/dive-points'), 'leer los puntos')['items']]
        until = day(365)
        centers = []

        def make_center(i):
            u = f'carga.centro{i:02d}'; email = f'gerencia@carga-centro{i:02d}.example.org'
            city, lat, lon = CITIES[(i - 1) % len(CITIES)]
            c = client(base)
            r = c.register(f'Gerente Carga {i:02d}', email, u, CARGA_PASSWORD, account_type='center', center_name=f'Centro de Buceo Carga {i:02d}',
                           phone=f'+34 600 {100 + i:03d} {200 + i:03d}', city=city, website=f'https://carga-centro{i:02d}.example.org')
            if r.status != 200: raise RuntimeError(f'registro {u}: {r.status} {r.body[:200]!r}')
            return u, email, city, lat, lon

        log(f'Creando {a.centros} centros de carga…')
        with cf.ThreadPoolExecutor(max_workers=min(a.hilos, 8)) as ex:
            regs = list(ex.map(make_center, range(1, a.centros + 1)))
        claims = {x['email']: x for x in ok(admin.get('/api/admin/center-claims'), 'leer las solicitudes')['items']}
        for u, email, city, lat, lon in regs:
            ok(admin.post('/api/admin/center-claims/review', {'id': claims[email]['id'], 'decision': 'approve', 'verification_method': 'email_domain',
                                                             'verification_note': 'Centro de la prueba de carga'}), 'aprobar ' + u)
        for u, email, city, lat, lon in regs:
            c = client(base); ok(c.login(u, CARGA_PASSWORD), 'entrar como ' + u)
            cid = c.me()['user']['center_id']
            centers.append({'usuario': u, 'center_id': cid, 'city': city, 'lat': lat, 'lon': lon, '_c': c})
        sql_exec(db, env, [("""UPDATE centers SET plan_code='pro',plan_status='active',plan_started_at=?,plan_expires_at=?,country='España',
                               stripe_account_id='acct_carga_'||id,stripe_charges_enabled=1,stripe_payouts_enabled=1,latitude=?,longitude=?,
                               cancel_free_hours=24,cancel_refund_pct=100,tagline='Centro de la prueba de carga' WHERE id=?""",
                            (day(0), until, c['lat'] + rnd.uniform(-0.02, 0.02), c['lon'] + rnd.uniform(-0.02, 0.02), c['center_id'])) for c in centers])

        services = []   # (cliente, service_id, hora, plazas máximas por reserva)
        flip = []

        def setup_center(c):
            cc = c['_c']; mine = rnd.sample(points, min(len(points), 4))
            for pid in mine: ok(cc.post('/api/center-points/assign', {'dive_point_id': pid}), 'asociar un punto')
            out = []
            for title, price, maxp, mode, stype, hour in (('Inmersión guiada en barco', 50, 8, 'request', 'inmersion', '09:00'),
                                                          ('Doble inmersión', 80, 8, 'request', 'inmersion', '08:30'),
                                                          ('Bautizo de buceo', 60, 4, 'payment', 'experiencia', '16:00')):
                sid = ok(cc.post('/api/provider-services', {'title': title, 'price': price, 'max_participants': maxp, 'booking_mode': 'request', 'service_type': stype,
                                                            'duration_minutes': 150, 'description': f'{title} (prueba de carga).', 'cancel_free_hours': 24,
                                                            'cancel_refund_pct': 100}), 'crear un servicio')['id']
                if mode == 'payment': flip.append(sid)
                out.append((cc, sid, hour, mine))
            return out

        with cf.ThreadPoolExecutor(max_workers=min(a.hilos, 8)) as ex:
            for lst in ex.map(setup_center, centers): services += lst
        if flip: sql_exec(db, env, [("UPDATE provider_services SET booking_mode='payment' WHERE id=?", (sid,)) for sid in flip])

        # --- servicios por salidas de la demo (centro.prueba, centro2.prueba y freelance.prueba) -----------------
        demo_accounts = {}
        for u in ('centro.prueba', 'centro2.prueba', 'freelance.prueba'):
            c = client(base); ok(c.login(u, DEMO_PASSWORD), 'entrar como ' + u); demo_accounts[u] = c
        demo_cid = {r_['username']: r_['center_id'] for r_ in sql_exec(db, env, [("SELECT username, center_id FROM users WHERE username IN ('centro.prueba','centro2.prueba')", ())])[0]}
        rows = sql_exec(db, env, [("""SELECT s.id, s.center_id FROM provider_services s JOIN users u ON u.id=s.provider_user_id
                                      WHERE s.active=1 AND COALESCE(s.booking_unit,'slot')='slot'
                                        AND (s.center_id IN (?,?) OR (s.center_id IS NULL AND u.username='freelance.prueba'))""",
                                    (demo_cid.get('centro.prueba'), demo_cid.get('centro2.prueba')))])[0]
        for r_ in rows:
            owner = 'freelance.prueba' if not r_['center_id'] else ('centro2.prueba' if r_['center_id'] == demo_cid.get('centro2.prueba') else 'centro.prueba')
            # Otra hora distinta de las de la demo: la demo conserva sus salidas y sus reservas tal cual.
            services.append((demo_accounts[owner], r_['id'], '11:30' if r_['center_id'] else '15:00', []))

        # --- salidas futuras ------------------------------------------------------------------------
        jobs = []
        for cc, sid, hour, mine in services:
            for k in range(1, a.dias + 1):
                jobs.append((cc, sid, day(k), hour, mine))
                if a.dos_turnos and hour < '12:00': jobs.append((cc, sid, day(k), '17:30', mine))
            # Hoy, a última hora: para que «Hoy» y el check-in del panel tengan salidas (solo centros).
            if mine: jobs.append((cc, sid, day(0), '23:30', mine))
        log(f'Creando {len(jobs)} salidas con {a.plazas} plazas…')

        def make_slot(j):
            cc, sid, d_, h_, mine = j
            body = {'service_id': sid, 'slot_date': d_, 'slot_time': h_, 'spots_total': a.plazas}
            if mine: body['dive_point_ids'] = mine[:2]
            ok(cc.post('/api/provider-services/slot', body), 'crear una salida')

        with cf.ThreadPoolExecutor(max_workers=a.hilos) as ex:
            list(ex.map(make_slot, jobs))
        log(f'  salidas creadas ({time.time() - t0:.0f} s desde el principio)')

        cuentas = {'password': CARGA_PASSWORD, 'demo_password': DEMO_PASSWORD, 'buzos': divers,
                   'centros': [{'usuario': c['usuario'], 'password': CARGA_PASSWORD, 'center_id': c['center_id']} for c in centers]
                              + [{'usuario': 'centro.prueba', 'password': DEMO_PASSWORD, 'center_id': 31}, {'usuario': 'centro2.prueba', 'password': DEMO_PASSWORD, 'center_id': 32}],
                   'freelance': [{'usuario': 'freelance.prueba', 'password': DEMO_PASSWORD}],
                   'admin': {'usuario': ADMIN_USER, 'password': ADMIN_PASSWORD}}
        ids = sql_exec(db, env, [("SELECT username, center_id FROM users WHERE username IN ('centro.prueba','centro2.prueba')", ())])[0]
        for row in ids:
            for c in cuentas['centros']:
                if c['usuario'] == row['username']: c['center_id'] = row['center_id']
    finally:
        stop_pgid(proc.pid)
    # Limpieza: sin sesiones abiertas ni correos en cola; WAL volcado en la base.
    sql_exec(db, env, [('DELETE FROM sessions', ()), ('DELETE FROM email_outbox', ())])
    c = sqlite3.connect(db); c.execute('PRAGMA wal_checkpoint(TRUNCATE)'); c.close()
    copy_db(db, work / 'carga-base.sqlite3')
    (work / 'cuentas.json').write_text(json.dumps(cuentas, ensure_ascii=False, indent=1))
    counts = sql_exec(work / 'carga-base.sqlite3', env, [("SELECT (SELECT COUNT(*) FROM users) users, (SELECT COUNT(*) FROM service_slots WHERE slot_date>=date('now')) slots, "
                                                         "(SELECT COUNT(*) FROM centers c WHERE active=1 AND verification_status='verified') centers, "
                                                         "(SELECT COUNT(*) FROM dive_points WHERE active=1) points, (SELECT COUNT(*) FROM bookings) bookings", ())])[0][0]
    meta = {'creada': dt.datetime.now().isoformat(timespec='seconds'), 'pbkdf2': a.pbkdf2, 'buzos': a.buzos, 'centros': a.centros, 'dias': a.dias,
            'plazas': a.plazas, 'recuentos': counts}
    (work / 'meta.json').write_text(json.dumps(meta, ensure_ascii=False, indent=1))
    shutil.rmtree(tmp, ignore_errors=True)
    log(f'Base de carga lista: {work / "carga-base.sqlite3"} · {counts}')
    return meta


# ----------------------------------------------------------------------------------------------- arrancar / parar
def arrancar(dir_: str, workers: int = 1, pagos: str = 'stripe-sim', puerto: int = 0, host: str = '127.0.0.1', public_host: str | None = None,
             backups: bool = False, extra_env: dict | None = None, reutilizar_bd: bool = False, correo: str = 'smtp') -> dict:
    work = Path(dir_).resolve(); run = work / 'run'
    meta = json.loads((work / 'meta.json').read_text()) if (work / 'meta.json').exists() else None
    if not meta: raise SystemExit(f'Falta {work / "meta.json"}: ejecuta antes «preparar.py construir --dir {work}».')
    old = run / 'estado.json'
    if old.exists():
        try: parar(dir_, quiet=True)
        except Exception: pass
    if not reutilizar_bd:
        shutil.rmtree(run, ignore_errors=True)
    run.mkdir(parents=True, exist_ok=True)
    db = run / 'carga.sqlite3'
    if not reutilizar_bd or not db.exists(): copy_db(work / 'carga-base.sqlite3', db)
    port = puerto or free_port(); public_host = public_host or ('127.0.0.1' if host in ('127.0.0.1', '0.0.0.0') else host)
    base = f'http://{public_host}:{port}'
    estado = {'base': base, 'puerto': port, 'workers': workers, 'pagos': pagos, 'db': str(db), 'run_dir': str(run), 'cuentas': str(work / 'cuentas.json'),
              'log_err': str(run / 'servidor.err.log'), 'log_out': str(run / 'servidor.out.log'), 'access_log_dir': str(run / 'logs'), 'pbkdf2': meta['pbkdf2'],
              'arrancado': dt.datetime.now().isoformat(timespec='seconds')}
    stripe_base = None
    if pagos == 'stripe-sim':
        sim = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'stripe-sim', '--control-host', host, '--public-host', public_host], stdout=subprocess.PIPE, stderr=open(run / 'stripe-sim.err.log', 'a'),
                               text=True, start_new_session=True)
        line = sim.stdout.readline()
        info = json.loads(line)
        stripe_base = info['api']; estado['stripe_sim'] = {'api': info['api'], 'control': info['control'], 'pid': sim.pid}
    smtp_port = None
    if correo == 'smtp':
        sink = subprocess.Popen([sys.executable, str(Path(__file__).resolve()), 'smtp-sink'], stdout=subprocess.PIPE, stderr=open(run / 'smtp-sink.err.log', 'a'),
                                text=True, start_new_session=True)
        smtp_port = json.loads(sink.stdout.readline())['port']; estado['smtp_sink'] = {'port': smtp_port, 'pid': sink.pid}
    estado['correo'] = correo
    env = server_env(run, db, port, host, public_host, workers, meta['pbkdf2'], pagos, stripe_base, backups, extra_env, smtp_port)
    proc = start_server(env, run, 'servidor')
    estado['pid'] = proc.pid
    try:
        wait_health(base, proc, err_file=run / 'servidor.err.log')
    except Exception:
        stop_pgid(proc.pid); raise
    time.sleep(1.0 if workers > 1 else 0.2)   # los procesos hijos (fork) abren el puerto un instante después
    (run / 'estado.json').write_text(json.dumps(estado, ensure_ascii=False, indent=1))
    log(f'Servidor de carga en {base} · WOD_WORKERS={workers} · pagos={pagos} · correo={correo} · PID {proc.pid} · estado en {run / "estado.json"}')
    return estado


def parar(dir_: str, quiet=False):
    st = Path(dir_).resolve() / 'run' / 'estado.json'
    if not st.exists():
        if not quiet: log('No hay ningún servidor de carga registrado.')
        return
    e = json.loads(st.read_text())
    stop_pgid(int(e['pid']))
    if e.get('stripe_sim'): stop_pgid(int(e['stripe_sim']['pid']), 5)
    if e.get('smtp_sink'): stop_pgid(int(e['smtp_sink']['pid']), 5)
    if not quiet: log(f'Servidor {e["base"]} parado.')


# ----------------------------------------------------------------------------------------------- sesiones y salidas
def sesiones(dir_: str, n: int = 0, hilos: int = 8):
    """v50.57 (revisión general 5.2) · Para «20 reservas por segundo» (clase Reservas de locustfile.py): abre una sesión
    de cada cuenta de buceador en el servidor de carga ya arrancado (run/sesiones.json) y apunta las salidas futuras
    con plazas que la web deja reservar (run/salidas.json), como las elige la clase Buceador. Las sesiones se abren
    antes de medir: 20 inicios de sesión por segundo (PBKDF2) serían otra prueba."""
    work = Path(dir_).resolve(); run = work / 'run'
    estado = json.loads((run / 'estado.json').read_text()); base = estado['base']
    cuentas = json.loads((work / 'cuentas.json').read_text())
    buzos = cuentas['buzos'][:n] if n else cuentas['buzos']

    def login(i_usuario):
        i, usuario = i_usuario
        body = json.dumps({'login': usuario, 'password': cuentas['password']}).encode()
        req = urllib.request.Request(base + '/api/auth/login', data=body, method='POST', headers={
            'Content-Type': 'application/json', 'Origin': base, 'X-Forwarded-For': f'100.{64 + i // 65000 % 64}.{i // 255 % 255}.{i % 254 + 1}'})
        with urllib.request.urlopen(req, timeout=60) as r:
            cookie = r.headers.get('Set-Cookie') or ''
        name, _, rest = cookie.partition('=')
        return name.strip(), rest.split(';', 1)[0]

    with cf.ThreadPoolExecutor(hilos) as ex:
        got = list(ex.map(login, enumerate(buzos)))
    names = {g[0] for g in got if g[1]}
    tokens = [g[1] for g in got if g[1]]
    if len(names) != 1 or not tokens: raise SystemExit(f'No se han podido abrir las sesiones: {sorted(names)} · {len(tokens)}')
    (run / 'sesiones.json').write_text(json.dumps({'cookie': names.pop(), 'tokens': tokens}))
    hoy = dt.date.today().isoformat(); salidas = []
    for c in cuentas.get('centros', []):
        cid = c.get('center_id')
        with urllib.request.urlopen(f'{base}/api/provider-services?provider_id=0&center_id={cid}', timeout=60) as r:
            cat = json.loads(r.read())
        for s in cat.get('items', []):
            if not s.get('bookable') or (s.get('booking_mode') == 'payment' and not s.get('instant')): continue
            for sl in s.get('slots', []):
                if sl.get('slot_date', '') > hoy and int(sl.get('spots_available') or 0) >= 1: salidas.append([cid, s['id'], sl['id']])
    random.Random(57).shuffle(salidas)
    (run / 'salidas.json').write_text(json.dumps({'salidas': salidas}))
    log(f'{len(tokens)} sesiones de buceador abiertas y {len(salidas)} salidas con plazas en {run}')
    return len(tokens), len(salidas)


# ----------------------------------------------------------------------------------------------- simulador de Stripe
def stripe_sim(control_host='127.0.0.1', public_host='127.0.0.1'):
    """Simulador local de Stripe (tests/stripe_mock.py) + un puerto de control: POST /pagar/<session_id> marca la sesión
    como pagada (lo que haría la persona en la página de pago de Stripe). Imprime una línea JSON con los puertos."""
    from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
    import threading
    from stripe_mock import StripeMock
    mock = StripeMock()

    class Ctl(BaseHTTPRequestHandler):
        protocol_version = 'HTTP/1.1'

        def log_message(self, *a): pass

        def _send(self, status, obj):
            raw = json.dumps(obj).encode()
            self.send_response(status); self.send_header('Content-Type', 'application/json'); self.send_header('Content-Length', str(len(raw)))
            self.end_headers(); self.wfile.write(raw)

        def do_POST(self):
            n = int(self.headers.get('Content-Length') or 0)
            if n: self.rfile.read(n)
            if self.path.startswith('/pagar/'):
                sid = self.path.rsplit('/', 1)[1]
                if sid not in mock.sessions: return self._send(404, {'error': 'sesión desconocida'})
                mock.pay(sid); return self._send(200, {'ok': True, 'id': sid})
            self._send(404, {'error': 'no encontrado'})

        def do_GET(self):
            self._send(200, {'ok': True, 'sessions': len(mock.sessions), 'refunds': len(mock.refunds)})

    ctl = ThreadingHTTPServer((control_host, 0), Ctl); ctl.daemon_threads = True
    threading.Thread(target=ctl.serve_forever, daemon=True).start()
    print(json.dumps({'api': mock.base, 'control': f'http://{public_host}:{ctl.server_address[1]}'}), flush=True)
    while True:            # el registro de llamadas del simulador crece sin límite: se vacía cada 10 s
        time.sleep(10); del mock.calls[:]


# ----------------------------------------------------------------------------------------------- comprobar la base
def comprobar(dir_: str, bd: str | None = None) -> dict:
    """Después de medir (v50.57): plazas y reservas en la base de la ejecución, solo leyendo. Todo tiene que ser 0:
    salidas con plazas libres negativas o con más plazas tomadas que las que tienen, salidas futuras cuyo contador de
    plazas no cuadra con sus reservas, y reservas activas repetidas (la misma persona y la misma salida por la web).
    Las salidas pasadas de la demo no se miran: su historia se creó con el generador de la demo."""
    if not bd:
        st = Path(dir_).resolve() / 'run' / 'estado.json'
        bd = json.loads(st.read_text())['db'] if st.exists() else str(Path(dir_).resolve() / 'run' / 'carga.sqlite3')
    db = sqlite3.connect(f'file:{bd}?mode=ro', uri=True, timeout=30)
    q = lambda sql: db.execute(sql).fetchone()[0]
    out = {
        'reservas': q("SELECT COUNT(*) FROM bookings"),
        'salidas_con_reservas': q("SELECT COUNT(DISTINCT slot_id) FROM bookings WHERE slot_id IS NOT NULL"),
        'salidas_libres_negativas': q("SELECT COUNT(*) FROM service_slots WHERE spots_available < 0"),
        'salidas_con_mas_tomadas_que_plazas': q("""SELECT COUNT(*) FROM (SELECT s.id, s.spots_total, SUM(b.participants) t FROM service_slots s
            JOIN bookings b ON b.slot_id=s.id AND b.slot_reserved=1 GROUP BY s.id HAVING t > s.spots_total)"""),
        # v50.58: the places taken are those of the bookings and of the active blocks (a course session moved to a
        # departure, places blocked by the centre), which the counter of the departure also takes
        'salidas_futuras_contador_distinto': q("""SELECT COUNT(*) FROM (SELECT s.id, s.spots_total, s.spots_available,
            COALESCE((SELECT SUM(b.participants) FROM bookings b WHERE b.slot_id=s.id AND b.slot_reserved=1),0)
            + COALESCE((SELECT SUM(k.qty) FROM spot_blocks k WHERE k.slot_id=s.id AND k.status='active'),0) t
            FROM service_slots s WHERE s.slot_date >= date('now') AND s.id IN (SELECT DISTINCT slot_id FROM bookings WHERE slot_id IS NOT NULL)
            AND s.spots_total - s.spots_available <> t)"""),
        'reservas_repetidas_activas': q("""SELECT COUNT(*) FROM (SELECT user_id, slot_id, COUNT(*) n FROM bookings WHERE slot_id IS NOT NULL
            AND user_id IS NOT NULL AND status NOT IN ('cancelled','rejected','expired') AND channel IN ('worldives','link') GROUP BY 1,2 HAVING n > 1)"""),
    }
    db.close()
    out['correcta'] = not any(out[k] for k in ('salidas_libres_negativas', 'salidas_con_mas_tomadas_que_plazas',
                                                  'salidas_futuras_contador_distinto', 'reservas_repetidas_activas'))
    print(json.dumps(out, ensure_ascii=False), flush=True)
    return out


# ----------------------------------------------------------------------------------------------- servidor SMTP local
def smtp_sink(host='127.0.0.1'):
    """Servidor SMTP mínimo que acepta los correos y los descarta (no los envía a nadie): el servidor de carga manda sus
    correos por SMTP, como en producción, con una conexión y dos escrituras cortas en la base por correo. Imprime una
    línea JSON con el puerto. Sin TLS (WOD_SMTP_SECURITY=none, que el servidor solo admite fuera de producción)."""
    import socketserver

    class H(socketserver.StreamRequestHandler):
        def handle(self):
            w = lambda line: (self.wfile.write(line.encode() + b'\r\n'), self.wfile.flush())
            w('220 carga ESMTP')
            while True:
                line = self.rfile.readline()
                if not line: return
                cmd = line.decode('latin-1').strip().upper()
                if cmd.startswith('EHLO'):
                    self.wfile.write(b'250-carga\r\n250-8BITMIME\r\n250 SIZE 52428800\r\n'); self.wfile.flush()
                elif cmd.startswith(('HELO', 'MAIL', 'RCPT', 'RSET', 'NOOP')):
                    w('250 OK')
                elif cmd == 'DATA':
                    w('354 Fin con <CRLF>.<CRLF>')
                    while True:
                        d = self.rfile.readline()
                        if not d or d in (b'.\r\n', b'.\n'): break
                    w('250 OK recibido')
                elif cmd == 'QUIT':
                    w('221 Adiós'); return
                else:
                    w('502 No implementado')

    class S(socketserver.ThreadingTCPServer):
        daemon_threads = True; allow_reuse_address = True

    srv = S((host, 0), H)
    print(json.dumps({'port': srv.server_address[1]}), flush=True)
    srv.serve_forever()


# ----------------------------------------------------------------------------------------------- CLI
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest='cmd')

    def common_build(p):
        p.add_argument('--dir', default=str(DEFAULT_DIR), help='carpeta de trabajo (por defecto %(default)s o $WOD_CARGA_DIR)')
        p.add_argument('--buzos', type=int, default=500, help='cuentas de buceador a registrar (por defecto %(default)s)')
        p.add_argument('--centros', type=int, default=20, help='centros de carga verificados (por defecto %(default)s)')
        p.add_argument('--dias', type=int, default=30, help='días de salidas futuras (por defecto %(default)s)')
        p.add_argument('--plazas', type=int, default=40, help='plazas por salida (por defecto %(default)s)')
        p.add_argument('--dos-turnos', action='store_true', help='también una salida de tarde en los servicios de mañana')
        p.add_argument('--pbkdf2', type=int, default=600_000, help='iteraciones PBKDF2 (por defecto las de producción: %(default)s)')
        p.add_argument('--hilos', type=int, default=16, help='peticiones simultáneas durante la preparación')
        p.add_argument('--workers-construccion', type=int, default=4, help='WOD_WORKERS del servidor temporal de preparación')
        p.add_argument('--semilla', type=int, default=2026)
        p.add_argument('--reusar-demo', action='store_true', help='no regenerar demo.sqlite3 si ya existe')

    def common_run(p):
        if not any(x.dest == 'dir' for x in p._actions): p.add_argument('--dir', default=str(DEFAULT_DIR))
        p.add_argument('--workers', type=int, default=int(os.environ.get('WOD_WORKERS', '1') or 1), help='WOD_WORKERS del servidor medido')
        p.add_argument('--pagos', choices=('stripe-sim', 'centro'), default='stripe-sim')
        p.add_argument('--puerto', type=int, default=0, help='0 = uno libre')
        p.add_argument('--host', default='127.0.0.1', help='WOD_HOST (0.0.0.0 si Locust corre en otras máquinas)')
        p.add_argument('--public-host', default=None, help='nombre o IP con el que lo ven los generadores (WOD_PUBLIC_URL y Origin)')
        p.add_argument('--con-copias', action='store_true', help='deja activas las copias de seguridad automáticas')
        p.add_argument('--reutilizar-bd', action='store_true', help='sigue con la base de la ejecución anterior en lugar de una copia limpia')
        p.add_argument('--correo', choices=('smtp', 'archivos'), default='smtp',
                       help='smtp (por defecto, como en producción): a un servidor SMTP local que no envía nada; archivos: .eml en la carpeta de la ejecución')
        p.add_argument('--env', action='append', default=[], metavar='CLAVE=VALOR', help='variable extra para el servidor (p. ej. WOD_MAX_CONCURRENT=128; '
                       'con generadores remotos, WOD_TRUSTED_PROXIES=<sus IPs> para que cuente su X-Forwarded-For)')

    common_build(sub.add_parser('construir', help='crea la base de carga'))
    common_run(sub.add_parser('arrancar', help='arranca el servidor de carga en segundo plano'))
    p = sub.add_parser('todo', help='construir + arrancar'); common_build(p); common_run(p)
    p = sub.add_parser('parar', help='para el servidor de carga'); p.add_argument('--dir', default=str(DEFAULT_DIR))
    p = sub.add_parser('sesiones', help='abre las sesiones de los buceadores y apunta las salidas con plazas (clase Reservas)')
    p.add_argument('--dir', default=str(DEFAULT_DIR)); p.add_argument('--n', type=int, default=0, help='cuántas cuentas (0 = todas)'); p.add_argument('--hilos', type=int, default=8)
    p = sub.add_parser('stripe-sim', help=argparse.SUPPRESS); p.add_argument('--control-host', default='127.0.0.1'); p.add_argument('--public-host', default='127.0.0.1')
    sub.add_parser('smtp-sink', help=argparse.SUPPRESS)
    p = sub.add_parser('comprobar', help='después de medir: plazas y reservas repetidas en la base (solo lee)')
    p.add_argument('--dir', default=str(DEFAULT_DIR)); p.add_argument('--bd', default=None, help='otra base (por defecto, la de la ejecución)')
    a = ap.parse_args(argv)
    if a.cmd == 'stripe-sim': return stripe_sim(a.control_host, a.public_host)
    if a.cmd == 'smtp-sink': return smtp_sink()
    if a.cmd in ('construir', 'todo'): construir(a)
    if a.cmd in ('arrancar', 'todo'):
        extra = dict(kv.split('=', 1) for kv in a.env)
        arrancar(a.dir, a.workers, a.pagos, a.puerto, a.host, a.public_host, a.con_copias, extra, a.reutilizar_bd, a.correo)
    if a.cmd == 'parar': parar(a.dir)
    if a.cmd == 'sesiones': sesiones(a.dir, a.n, a.hilos)
    if a.cmd == 'comprobar' and not comprobar(a.dir, a.bd)['correcta']: raise SystemExit(1)
    if not a.cmd: ap.print_help()


if __name__ == '__main__':
    main()
