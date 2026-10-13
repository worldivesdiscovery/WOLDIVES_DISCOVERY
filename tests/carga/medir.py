#!/usr/bin/env python3
"""Mide WORLDIVES DISCOVERY por escalones de usuarios con Locust y busca el punto de rotura.

    # todo en uno: arranca el servidor (copia limpia de la base de carga), mide y lo para
    python3 tests/carga/medir.py --dir /tmp/wod-carga --arrancar --workers 4 --pasos 100,500,1000,2000,5000,10000

    # contra un servidor ya arrancado con preparar.py arrancar (lee --dir/run/estado.json)
    python3 tests/carga/medir.py --dir /tmp/wod-carga --pasos 100,500

Por cada escalón (N usuarios):
  - Locust sin interfaz, con --processes P (por defecto, un proceso por núcleo) para que el generador no sea el cuello
    de botella. Con --master-remoto K, este equipo solo coordina y espera K workers en otras máquinas:
        WOD_CARGA_CUENTAS=cuentas.json WOD_CARGA_STRIPE_CONTROL=http://<servidor>:<puerto> \\
        locust -f tests/carga/locustfile.py --worker --master-host <este equipo> --processes -1
  - rampa de --rampa segundos (por defecto N/50, mínimo 20) y --duracion segundos más; las estadísticas del escalón
    usan SOLO el régimen estable: desde el final de la rampa + --asentar (por defecto rampa/2, entre 10 y 60 s: los
    últimos usuarios aún cargan la web) hasta el final, en ventanas de 10 s del histograma que escribe locustfile.py.
    El detalle por ventanas queda en linea_temporal.csv (también la rampa).
  - mientras tanto, cada --muestreo segundos: CPU y memoria del árbol de procesos del servidor (psutil; con WOD_WORKERS
    se suman los procesos hijos), CPU del generador, CPU del sistema, tamaño de la base y del WAL.
  - del log de errores del servidor (stderr): bloqueos de SQLite («database is locked»), OperationalError y errores 500.
  - resultados en --salida/paso_<N>/: resultado.json, endpoints.csv, servidor.csv, locust_*.csv; y en --salida:
    resumen.csv (una fila por escalón y grupo) y resumen.json (con el punto de rotura).

Grupos: «pag» páginas y lecturas (rotura si p95 > 1 s) · «res» reserva, pago y escrituras del panel (rotura si
p95 > 2 s) · error > 1 % de las peticiones a la web (pag + res + ses). «ses» (inicio de sesión, PBKDF2) se informa
aparte (con --umbral-sesion MS cuenta también para la rotura). «biz» (sin plazas…) y «sim» (simulador de Stripe) se
informan aparte y no cuentan como errores. El primer escalón que incumple es el punto de rotura;
por defecto no se sigue subiendo (--seguir para continuar).

--perfil: py-spy record (pip install py-spy) sobre el servidor (y sus workers) durante cada escalón; deja
perfil_<N>.txt (pilas plegadas) y perfil_<N>_resumen.txt (funciones y líneas de app/ con más muestras, y CPU por ruta).
"""
from __future__ import annotations

import argparse
import csv
import json
import os
import re
import shutil
import signal
import subprocess
import sys
import threading
import time
from collections import Counter, defaultdict
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))

UMBRAL = {'pag': 1000.0, 'res': 2000.0, 'ses': None}   # 'ses' (inicio de sesión) solo con --umbral-sesion
ERROR_MAX = 0.01
LOCK_RE = re.compile(r'database is locked|database table is locked', re.I)
OPERR_RE = re.compile(r'OperationalError')
ERR500_RE = re.compile(r'^\[[^\]]+\] (GET|POST|HEAD|PUT|DELETE) \S+ -> ')


def log(msg):
    print(f'[{time.strftime("%H:%M:%S")}] {msg}', flush=True)


# ------------------------------------------------------------------------------------------------ estadísticas
def merge(hs):
    o = {'n': 0, 'fail': 0, 'sum': 0.0, 'max': 0.0, 'b': Counter()}
    for h in hs:
        o['n'] += h['n']; o['fail'] += h['fail']; o['sum'] += h['sum']; o['max'] = max(o['max'], h['max'])
        for k, v in h['b'].items(): o['b'][float(k)] += v
    return o


def pct(h, p):
    if not h['n']: return None
    target = p * h['n']; acc = 0
    for k in sorted(h['b']):
        acc += h['b'][k]
        if acc >= target: return k
    return max(h['b'])


def summary(h, seconds):
    n = h['n']
    return {'peticiones': n, 'fallos': h['fail'], 'error_pct': round(100.0 * h['fail'] / n, 3) if n else 0.0,
            'rps': round(n / seconds, 2) if seconds else None, 'media_ms': round(h['sum'] / n, 1) if n else None,
            'p50_ms': pct(h, 0.50), 'p95_ms': pct(h, 0.95), 'p99_ms': pct(h, 0.99), 'max_ms': round(h['max'], 1)}


def group_of(name):
    g = name.split(' ', 1)[0]
    return g if g in ('pag', 'res', 'ses', 'sim', 'biz') else 'otro'


def analyse_hist(path: Path, desde: float, hasta: float):
    """Endpoints y grupos con las ventanas completas de [desde, hasta)."""
    raw = json.loads(path.read_text())
    win = raw.get('window', 10)
    per_name = defaultdict(list); windows = []
    timeline = []
    for w, names in raw['data'].items():
        w = float(w)
        if w < desde or w + win > hasta + 0.5: continue
        windows.append(w)
        for name, h in names.items(): per_name[name].append(h)
    for w, names in sorted(raw['data'].items(), key=lambda x: float(x[0])):
        g = {gr: merge([h for nm, h in names.items() if group_of(nm) == gr]) for gr in ('pag', 'res', 'ses')}
        timeline.append({'t': w, **{f'{gr}_{k}': v for gr in g for k, v in (('n', g[gr]['n']), ('p95', pct(g[gr], .95)), ('fallos', g[gr]['fail']))}})
    seconds = len(set(windows)) * win
    endpoints = {name: summary(merge(hs), seconds) for name, hs in sorted(per_name.items())}
    groups = {}
    for gr in ('pag', 'res', 'ses', 'sim', 'biz'):
        groups[gr] = summary(merge([h for name, hs in per_name.items() if group_of(name) == gr for h in hs]), seconds)
    web = merge([h for name, hs in per_name.items() if group_of(name) in ('pag', 'res', 'ses') for h in hs])
    groups['web'] = summary(web, seconds)
    return endpoints, groups, seconds, timeline


# ------------------------------------------------------------------------------------------------ muestreo del servidor
class Sampler(threading.Thread):
    def __init__(self, server_pid, db, every, gen_proc=None):
        super().__init__(daemon=True)
        import psutil
        self.psutil = psutil
        self.server = psutil.Process(server_pid) if server_pid else None
        self.db = Path(db) if db else None; self.every = every; self.gen = gen_proc
        self.rows = []; self.stop_ev = threading.Event(); self.procs = {}

    def tree(self, root):
        try: return [root] + root.children(recursive=True)
        except self.psutil.Error: return []

    def cpu_mem(self, procs):
        cpu = rss = thr = 0.0; n = 0
        for p in procs:
            q = self.procs.get(p.pid)
            try:
                if q is None:
                    self.procs[p.pid] = p; p.cpu_percent(None); continue
                cpu += q.cpu_percent(None); mi = q.memory_info(); rss += mi.rss; thr += q.num_threads(); n += 1
            except self.psutil.Error:
                self.procs.pop(p.pid, None)
        return cpu, rss, thr, n

    def run(self):
        ps = self.psutil; ps.cpu_percent(None)
        while not self.stop_ev.wait(self.every):
            row = {'t': round(time.time(), 1)}
            if self.server:
                cpu, rss, thr, n = self.cpu_mem(self.tree(self.server))
                row.update(srv_cpu_pct=round(cpu, 1), srv_rss_mb=round(rss / 1e6, 1), srv_hilos=int(thr), srv_procesos=n)
            if self.gen:
                try: gp = ps.Process(self.gen.pid)
                except ps.Error: gp = None
                if gp:
                    cpu, rss, thr, n = self.cpu_mem(self.tree(gp))
                    row.update(gen_cpu_pct=round(cpu, 1), gen_procesos=n)
            row['sis_cpu_pct'] = ps.cpu_percent(None); row['sis_mem_pct'] = ps.virtual_memory().percent
            row['carga1'] = round(os.getloadavg()[0], 2)
            if self.db:
                for suf, key in (('', 'bd_mb'), ('-wal', 'wal_mb')):
                    p = Path(str(self.db) + suf)
                    row[key] = round(p.stat().st_size / 1e6, 2) if p.exists() else 0.0
            self.rows.append(row)

    def stop(self):
        self.stop_ev.set(); self.join(5)

    def stats(self, t_from=0.0, t_to=float('inf')):
        rows = [r for r in self.rows if t_from <= r['t'] <= t_to]
        def agg(key):
            v = [r[key] for r in rows if key in r]
            return {'media': round(sum(v) / len(v), 1), 'max': max(v)} if v else None
        out = {k: agg(k) for k in ('srv_cpu_pct', 'srv_rss_mb', 'srv_hilos', 'gen_cpu_pct', 'sis_cpu_pct', 'sis_mem_pct', 'carga1', 'bd_mb', 'wal_mb')}
        out['muestras'] = len(rows)
        return out


def log_errors(path: Path, offset: int):
    if not path or not path.exists(): return {'bloqueos_sqlite': 0, 'operational_error': 0, 'errores_500': 0, 'ejemplos': []}, offset
    with path.open('rb') as f:
        f.seek(offset); chunk = f.read().decode('utf-8', 'replace'); end = f.tell()
    lines = chunk.splitlines()
    ex = [l for l in lines if ERR500_RE.match(l) or LOCK_RE.search(l)]
    return {'bloqueos_sqlite': sum(1 for l in lines if LOCK_RE.search(l)), 'operational_error': sum(1 for l in lines if OPERR_RE.search(l)),
            'errores_500': sum(1 for l in lines if ERR500_RE.match(l)), 'ejemplos': list(dict.fromkeys(ex))[:15]}, end


# ------------------------------------------------------------------------------------------------ perfil (py-spy)
APP_RE = re.compile(r'^(?:.*/)?(?:app/)?(?:server\.py|wod/[A-Za-z_]+\.py)$')
STDLIB_SERVER = ('http/server.py', 'socketserver.py')
FRAME_RE = re.compile(r'^(?P<fn>.*?) \((?P<file>[^():]+):(?P<line>\d+)\)$')


def profile_summary(raw: Path, out: Path, top=40):
    """Resumen de las pilas plegadas de py-spy: hoja (dónde se gasta la CPU), última línea de app/ en la pila
    (qué línea de la aplicación la provoca) y línea de do_GET/do_POST (qué ruta)."""
    leaf = Counter(); app_line = Counter(); app_func_incl = Counter(); route = Counter(); total = 0
    for line in raw.read_text(errors='replace').splitlines():
        if not line.strip(): continue
        stack, _, n = line.rpartition(' ')
        try: n = int(n)
        except ValueError: continue
        total += n
        frames = [f for f in stack.split(';') if f]
        parsed = []
        for f in frames:
            m = FRAME_RE.match(f.strip())
            if m: parsed.append((m['fn'], m['file'], int(m['line'])))
        if not parsed: continue
        fn, fl, ln = parsed[-1]; leaf[f'{fn} ({short(fl)})'] += n
        apps = [(fn, fl, ln) for fn, fl, ln in parsed if APP_RE.match(fl) and not fl.endswith(STDLIB_SERVER)]
        if apps:
            fn, fl, ln = apps[-1]; app_line[f'{short(fl)}:{ln} {fn}'] += n
            for fn2, fl2, _ in dict.fromkeys((a[0], a[1], 0) for a in apps): app_func_incl[f'{fn2} ({short(fl2)})'] += n
        for fn, fl, ln in parsed:
            if fn in ('do_GET', 'do_POST') and APP_RE.match(fl) and not fl.endswith(STDLIB_SERVER):
                route[f'{fn} server.py:{ln}'] += n; break
    lines = [f'Muestras: {total}', '', '== Funciones hoja (CPU propia) ==']
    lines += [f'{v:7d} {100 * v / total:5.1f}%  {k}' for k, v in leaf.most_common(top)]
    lines += ['', '== Última línea de app/ en la pila (dónde lo provoca la aplicación) ==']
    lines += [f'{v:7d} {100 * v / total:5.1f}%  {k}' for k, v in app_line.most_common(top)]
    lines += ['', '== Funciones de app/ (tiempo inclusivo) ==']
    lines += [f'{v:7d} {100 * v / total:5.1f}%  {k}' for k, v in app_func_incl.most_common(top)]
    lines += ['', '== Ruta (línea de do_GET/do_POST que llama) ==']
    lines += [f'{v:7d} {100 * v / total:5.1f}%  {k}' for k, v in route.most_common(top)]
    out.write_text('\n'.join(lines) + '\n')
    return total


def short(path):
    p = path.replace('\\', '/')
    for mark in ('/app/', '/site-packages/', '/dist-packages/', '/lib/python'):
        if mark in p: return p.split(mark, 1)[1] if mark != '/app/' else 'app/' + p.split(mark, 1)[1]
    return p.rsplit('/', 1)[-1]


# ------------------------------------------------------------------------------------------------ un escalón
def run_step(a, estado, users, out_dir: Path, log_offset: int):
    step_dir = out_dir / f'paso_{users}'; shutil.rmtree(step_dir, ignore_errors=True); step_dir.mkdir(parents=True)
    hist_dir = step_dir / 'hist'; hist_dir.mkdir()
    ramp = a.rampa if a.rampa is not None else max(20, users / 50)
    rate = max(1.0, users / ramp)
    total = int(ramp + a.duracion)
    env = dict(os.environ, WOD_CARGA_ESTADO=str(a.estado_path), WOD_CARGA_HIST_DIR=str(hist_dir), PYTHONUNBUFFERED='1')
    for k, v in (('WOD_CARGA_MEZCLA', a.mezcla), ('WOD_CARGA_PENSAR', a.pensar), ('WOD_CARGA_PAGO', a.pago)):
        if v: env[k] = str(v)
    cmd = [sys.executable, '-m', 'locust', '-f', str(HERE / 'locustfile.py'), '--headless', '-u', str(users), '-r', f'{rate:.2f}', '-t', f'{total}s',
           '--host', estado['base'], '--csv', str(step_dir / 'locust'), '--stop-timeout', '15', '--only-summary', '--loglevel', a.loglevel,
           '--reset-stats']
    if a.master_remoto:
        cmd += ['--master', '--expect-workers', str(a.master_remoto), '--master-bind-host', a.master_bind]
    elif a.procesos != 1:
        cmd += ['--processes', str(a.procesos)]
    if a.tags: cmd += ['--tags', *a.tags.split(',')]
    if a.exclude_tags: cmd += ['--exclude-tags', *a.exclude_tags.split(',')]
    if a.clases: cmd += a.clases.split(',')
    log(f'Escalón {users} usuarios: rampa {ramp:.0f} s ({rate:.1f}/s) + {a.duracion} s estables · {" ".join(cmd[3:])}')
    t0 = time.time()
    lf = open(step_dir / 'locust.log', 'w')
    gen = subprocess.Popen(cmd, env=env, stdout=lf, stderr=subprocess.STDOUT, cwd=str(step_dir), start_new_session=True)
    sampler = Sampler(estado.get('pid'), estado.get('db'), a.muestreo, gen); sampler.start()
    spy = None
    if a.perfil:
        spy_cmd = ['py-spy', 'record', '--pid', str(estado['pid']), '--subprocesses', '--rate', str(a.perfil_rate), '--format', 'raw', '--nonblocking',
                   '--output', str(step_dir / f'perfil_{users}.txt'), '--duration', str(max(5, int(a.duracion) - 4))]
        spy_delay = ramp + 2
        def start_spy():
            nonlocal spy
            time.sleep(spy_delay)
            if gen.poll() is None:
                spy = subprocess.Popen(spy_cmd, stdout=open(step_dir / 'py-spy.log', 'w'), stderr=subprocess.STDOUT)
        threading.Thread(target=start_spy, daemon=True).start()
    try:
        gen.wait(timeout=total + 180)
    except subprocess.TimeoutExpired:
        log('  Locust no termina: se para.'); os.killpg(gen.pid, signal.SIGTERM); gen.wait(30)
    t1 = time.time()
    time.sleep(2)
    try: os.killpg(gen.pid, signal.SIGTERM)       # algún worker de --processes rezagado
    except (ProcessLookupError, PermissionError): pass
    sampler.stop(); lf.close()
    if spy is not None:
        try: spy.wait(timeout=60)
        except subprocess.TimeoutExpired: spy.terminate()
    errs, log_offset = log_errors(Path(estado['log_err']) if estado.get('log_err') else None, log_offset)
    settle = a.asentar if a.asentar is not None else max(10.0, min(60.0, ramp / 2))
    desde = t0 + ramp + settle; hasta = t0 + total
    hist = hist_dir / 'hist.json'
    if not hist.exists():
        raise SystemExit(f'Locust no ha dejado {hist}. Mira {step_dir / "locust.log"}:\n' + (step_dir / 'locust.log').read_text()[-3000:])
    endpoints, groups, seconds, timeline = analyse_hist(hist, desde, hasta)
    res = {'usuarios': users, 'rampa_s': round(ramp, 1), 'asentar_s': round(settle, 1), 'estable_s': seconds, 'inicio': time.strftime('%Y-%m-%dT%H:%M:%S', time.localtime(t0)),
           'duracion_real_s': round(t1 - t0, 1), 'grupos': groups, 'servidor': sampler.stats(desde, hasta), 'servidor_con_rampa': sampler.stats(),
           'log_servidor': errs, 'endpoints': endpoints,
           'workers_servidor': estado.get('workers'), 'procesos_locust': a.procesos if not a.master_remoto else f'remoto:{a.master_remoto}',
           'locust_exit': gen.returncode}
    why = []
    for g, lim in UMBRAL.items():
        if not lim: continue
        p95 = groups[g]['p95_ms']
        if p95 is not None and p95 > lim: why.append(f'p95 {g} {p95:.0f} ms > {lim:.0f} ms')
    if groups['web']['peticiones'] and groups['web']['error_pct'] > 100 * ERROR_MAX: why.append(f'errores {groups["web"]["error_pct"]:.2f} % > {100 * ERROR_MAX:.0f} %')
    if not groups['web']['peticiones']: why.append('sin peticiones medidas')
    gen_cpu = (res['servidor'].get('gen_cpu_pct') or {}).get('media')
    nproc = (a.procesos if a.procesos > 0 else os.cpu_count()) if not a.master_remoto else None
    res['generador_saturado'] = bool(nproc and gen_cpu and gen_cpu / max(1, nproc) > 85)
    res['rotura'] = why
    (step_dir / 'resultado.json').write_text(json.dumps(res, ensure_ascii=False, indent=1))
    with (step_dir / 'endpoints.csv').open('w', newline='') as f:
        w = csv.writer(f); w.writerow(['nombre', 'grupo', 'peticiones', 'fallos', 'error_pct', 'rps', 'media_ms', 'p50_ms', 'p95_ms', 'p99_ms', 'max_ms'])
        for name, s in sorted(endpoints.items(), key=lambda x: -(x[1]['peticiones'] or 0)):
            w.writerow([name, group_of(name), s['peticiones'], s['fallos'], s['error_pct'], s['rps'], s['media_ms'], s['p50_ms'], s['p95_ms'], s['p99_ms'], s['max_ms']])
    if sampler.rows:
        keys = sorted({k for r in sampler.rows for k in r}, key=lambda k: (k != 't', k))
        with (step_dir / 'servidor.csv').open('w', newline='') as f:
            w = csv.DictWriter(f, fieldnames=keys); w.writeheader(); w.writerows(sampler.rows)
    with (step_dir / 'linea_temporal.csv').open('w', newline='') as f:
        if timeline:
            w = csv.DictWriter(f, fieldnames=list(timeline[0])); w.writeheader(); w.writerows(timeline)
    if a.perfil and (step_dir / f'perfil_{users}.txt').exists():
        profile_summary(step_dir / f'perfil_{users}.txt', step_dir / f'perfil_{users}_resumen.txt')
    g = groups
    log(f'  pag: {g["pag"]["rps"]} r/s p50 {g["pag"]["p50_ms"]} p95 {g["pag"]["p95_ms"]} p99 {g["pag"]["p99_ms"]} ms · '
        f'res: {g["res"]["rps"]} r/s p50 {g["res"]["p50_ms"]} p95 {g["res"]["p95_ms"]} p99 {g["res"]["p99_ms"]} ms · '
        f'login: {g["ses"]["peticiones"]} p95 {g["ses"]["p95_ms"]} ms · '
        f'errores {g["web"]["error_pct"]} % · CPU servidor {(res["servidor"].get("srv_cpu_pct") or {}).get("media")} % · '
        f'bloqueos SQLite {errs["bloqueos_sqlite"]} · 500 {errs["errores_500"]}' + (f' · ROTURA: {"; ".join(why)}' if why else ''))
    if res['generador_saturado']: log('  AVISO: el generador (Locust) pasa del 85 % de CPU: añade procesos o máquinas (--master-remoto).')
    return res, log_offset


# ------------------------------------------------------------------------------------------------ principal
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument('--dir', default=os.environ.get('WOD_CARGA_DIR') or '/tmp/wod-carga', help='carpeta de preparar.py')
    ap.add_argument('--pasos', default='100,500,1000,2000,5000,10000', help='usuarios por escalón, separados por comas')
    ap.add_argument('--duracion', type=int, default=180, help='segundos de régimen estable por escalón (por defecto %(default)s)')
    ap.add_argument('--rampa', type=float, default=None, help='segundos de rampa (por defecto usuarios/50, mínimo 20)')
    ap.add_argument('--asentar', type=float, default=None, help='segundos tras la rampa que no se miden (por defecto rampa/2, entre 10 y 60): '
                    'los últimos usuarios todavía están cargando la web')
    ap.add_argument('--pausa', type=int, default=15, help='segundos entre escalones')
    ap.add_argument('--procesos', type=int, default=-1, help='procesos de Locust (-1 = uno por núcleo, 1 = sin --processes)')
    ap.add_argument('--master-remoto', type=int, default=0, metavar='K', help='este equipo solo coordina: espera K workers remotos')
    ap.add_argument('--master-bind', default='*', help='interfaz del master para los workers remotos')
    ap.add_argument('--muestreo', type=float, default=2.0, help='segundos entre muestras de CPU/memoria')
    ap.add_argument('--mezcla', default=None, help='pesos Visitante,Buceador,Centro (por defecto 70,20,10)')
    ap.add_argument('--pensar', default=None, help='tiempo de lectura entre páginas «min,max» en segundos (por defecto 3,10)')
    ap.add_argument('--pago', default=None, help='proporción de reservas «pago al reservar» (por defecto 0.5)')
    ap.add_argument('--tags', default=None); ap.add_argument('--exclude-tags', default=None)
    ap.add_argument('--clases', default=None, help='solo estas clases de usuario, p. ej. Visitante,Buceador')
    ap.add_argument('--salida', default=None, help='carpeta de resultados (por defecto --dir/resultados/<fecha>)')
    ap.add_argument('--seguir', action='store_true', help='seguir subiendo después del punto de rotura')
    ap.add_argument('--perfil', action='store_true', help='py-spy record del servidor durante cada escalón')
    ap.add_argument('--perfil-rate', type=int, default=67, help='muestras por segundo de py-spy')
    ap.add_argument('--umbral-sesion', type=float, default=None, metavar='MS', help='cuenta también el p95 del inicio de sesión para la rotura')
    ap.add_argument('--loglevel', default='WARNING')
    ap.add_argument('--arrancar', action='store_true', help='arranca el servidor (copia limpia de la base) y lo para al final')
    ap.add_argument('--workers', type=int, default=1, help='con --arrancar: WOD_WORKERS')
    ap.add_argument('--pagos', choices=('stripe-sim', 'centro'), default='stripe-sim', help='con --arrancar: cómo se paga')
    ap.add_argument('--env', action='append', default=[], metavar='CLAVE=VALOR', help='con --arrancar: variable extra del servidor')
    a = ap.parse_args(argv)
    if a.umbral_sesion: UMBRAL['ses'] = a.umbral_sesion
    try:
        import psutil  # noqa: F401
        import locust  # noqa: F401
    except ImportError as e:
        raise SystemExit(f'Falta {e.name}: pip install locust psutil')
    work = Path(a.dir).resolve()
    estado_path = work / 'run' / 'estado.json'
    started = None
    if a.arrancar:
        import preparar
        started = preparar.arrancar(str(work), a.workers, a.pagos, extra_env=dict(kv.split('=', 1) for kv in a.env))
    if not estado_path.exists(): raise SystemExit(f'No hay servidor de carga: falta {estado_path} (preparar.py arrancar o --arrancar).')
    a.estado_path = estado_path
    estado = json.loads(estado_path.read_text())
    out = Path(a.salida) if a.salida else work / 'resultados' / time.strftime('%Y%m%d-%H%M%S')
    out.mkdir(parents=True, exist_ok=True)
    log(f'Servidor {estado["base"]} (WOD_WORKERS={estado.get("workers")}, pagos={estado.get("pagos")}) · resultados en {out}')
    log_path = Path(estado['log_err']) if estado.get('log_err') else None
    offset = log_path.stat().st_size if log_path and log_path.exists() else 0
    steps = [int(x) for x in a.pasos.split(',') if x.strip()]
    results = []; breaking = None
    try:
        for i, n in enumerate(steps):
            res, offset = run_step(a, estado, n, out, offset)
            results.append(res)
            with (out / 'resumen.csv').open('a', newline='') as f:
                w = csv.writer(f)
                if f.tell() == 0:
                    w.writerow(['usuarios', 'grupo', 'rps', 'media_ms', 'p50_ms', 'p95_ms', 'p99_ms', 'error_pct', 'peticiones', 'fallos', 'cpu_servidor_media',
                                'cpu_servidor_max', 'rss_servidor_max_mb', 'cpu_generador_media', 'wal_max_mb', 'bloqueos_sqlite', 'errores_500', 'rotura'])
                for g in ('pag', 'res', 'ses', 'web'):
                    s = res['grupos'][g]; sv = res['servidor']
                    w.writerow([n, g, s['rps'], s['media_ms'], s['p50_ms'], s['p95_ms'], s['p99_ms'], s['error_pct'], s['peticiones'], s['fallos'],
                                (sv.get('srv_cpu_pct') or {}).get('media'), (sv.get('srv_cpu_pct') or {}).get('max'), (sv.get('srv_rss_mb') or {}).get('max'),
                                (sv.get('gen_cpu_pct') or {}).get('media'), (sv.get('wal_mb') or {}).get('max'), res['log_servidor']['bloqueos_sqlite'],
                                res['log_servidor']['errores_500'], '; '.join(res['rotura'])])
            if res['rotura'] and breaking is None:
                breaking = {'usuarios': n, 'motivo': res['rotura'], 'ultimo_correcto': steps[i - 1] if i else None}
                if not a.seguir:
                    log(f'Punto de rotura en {n} usuarios: {"; ".join(res["rotura"])}. Se para (--seguir para continuar).'); break
            if i + 1 < len(steps): time.sleep(a.pausa)
    finally:
        summary_ = {'servidor': estado, 'pasos': [{k: v for k, v in r.items() if k != 'endpoints'} for r in results], 'rotura': breaking,
                    'umbrales': {'p95_pag_ms': UMBRAL['pag'], 'p95_res_ms': UMBRAL['res'], 'error_max_pct': 100 * ERROR_MAX}}
        (out / 'resumen.json').write_text(json.dumps(summary_, ensure_ascii=False, indent=1))
        if started:
            import preparar
            preparar.parar(str(work))
    log(f'Hecho. Punto de rotura: {breaking or "no alcanzado"} · {out / "resumen.json"}')


if __name__ == '__main__':
    main()
