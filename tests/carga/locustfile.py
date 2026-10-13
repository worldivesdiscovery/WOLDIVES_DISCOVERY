"""Escenarios de carga de WORLDIVES DISCOVERY para Locust (https://locust.io).

Tres tipos de usuario, con la mezcla por defecto 70 / 20 / 10 (cambia con WOD_CARGA_MEZCLA="70,20,10"):

  Visitante  anónimo: carga la web (index, CSS, JS, imágenes; en visitas posteriores solo revalida con ETag) y navega:
             inicio, lista de puntos, ficha de punto, centros, ficha de centro, calendario de salidas, búsqueda,
             salidas cercanas. Cada tarea es una «vista de página» con las mismas llamadas a la API que hace la web.
  Buceador   entra (POST /api/auth/login, PBKDF2 real), mira un centro y su calendario, pide presupuesto, reserva
             (POST /api/bookings) y paga como lo hace la app en modo de pruebas:
               · «Pago al reservar» con el simulador de Stripe (preparar.py --pagos stripe-sim): la reserva abre el
                 pago, el usuario «paga» en el simulador y la web confirma con GET /api/payments/session/<id> (lo que
                 hace la página #/pago-ok). Nunca se llama al Stripe real.
               · «Bajo petición»: queda solicitada; cuando el centro la acepta, si el centro cobra online el
                 buceador la paga (POST /api/payments/checkout); si no, el centro registra el cobro en el centro.
             También mira «Mis reservas» y navega.
  Centro     personal del centro en el panel: planning del mes, reservas de la semana, solicitudes (las acepta),
             «Hoy» + lista del barco y check-in (POST /api/manifest/sync) y cobro en el centro.

Grupos (prefijo del nombre de cada petición, los usa medir.py para los umbrales):
  «pag …»  páginas y lecturas (umbral p95 1 s)   ·   «res …»  reserva, pago y escrituras del panel (umbral p95 2 s)
  «ses …»  inicio de sesión (PBKDF2 de 600 000 iteraciones: ~0,4 s de CPU cada uno; se informa aparte)
  «sim …»  simulador de Stripe (no es la web)   ·   «biz …» resultados de negocio (sin plazas, solicitud ya
  resuelta…): no son errores del servidor, se cuentan aparte.

Etiquetas (--tags / --exclude-tags): navegar, buscar, calendario, login, reservar, pagar, panel, aceptar, checkin, cobro.
Clases: se pueden elegir en la línea de órdenes (p. ej. `locust ... Visitante Buceador`).

Variables de entorno:
  WOD_CARGA_ESTADO   estado.json de preparar.py (cuentas, simulador de Stripe). Por defecto /tmp/wod-carga/run/estado.json
  WOD_CARGA_MEZCLA   pesos Visitante,Buceador,Centro (por defecto 70,20,10)
  WOD_CARGA_PENSAR   tiempo de lectura entre páginas en segundos, «min,max» (por defecto 3,10)
  WOD_CARGA_PAGO     proporción de reservas «pago al reservar» cuando el centro cobra online (por defecto 0.5)
  WOD_CARGA_HIST_DIR carpeta del histograma por ventanas de 10 s (lo escribe el master; lo usa medir.py)
  WOD_CARGA_MEDIR_DESDE  (opcional) hora epoch desde la que se anotan tiempos en el histograma
  WOD_CARGA_CUENTAS / WOD_CARGA_STRIPE_CONTROL  para generadores en otras máquinas (copia de cuentas.json y URL del
                     control del simulador de Stripe alcanzable desde ellas)

Uso directo (sin medir.py):
  WOD_CARGA_ESTADO=/tmp/wod-carga/run/estado.json locust -f tests/carga/locustfile.py --host http://127.0.0.1:8300 \
      --headless -u 200 -r 20 -t 2m --processes 4
"""
from __future__ import annotations

import datetime as dt
import json
import os
import random
import re
import threading
import time
from pathlib import Path

import gevent
from locust import FastHttpUser, between, events, tag, task

# ---------------------------------------------------------------------------------------------- configuración
ESTADO_PATH = Path(os.environ.get('WOD_CARGA_ESTADO') or '/tmp/wod-carga/run/estado.json')
try:
    ESTADO = json.loads(ESTADO_PATH.read_text())
except (OSError, ValueError):
    ESTADO = {}
try:
    CUENTAS = json.loads(Path(os.environ.get('WOD_CARGA_CUENTAS') or ESTADO.get('cuentas') or '/tmp/wod-carga/cuentas.json').read_text())
except (OSError, ValueError):
    CUENTAS = {'buzos': [], 'centros': [], 'password': ''}
# Generadores en otras máquinas: WOD_CARGA_CUENTAS (copia de cuentas.json) y WOD_CARGA_STRIPE_CONTROL (URL alcanzable).
STRIPE_CONTROL = os.environ.get('WOD_CARGA_STRIPE_CONTROL') or (ESTADO.get('stripe_sim') or {}).get('control')


def _floats(var, default):
    try: return [float(x) for x in os.environ.get(var, '').split(',') if x.strip()] or default
    except ValueError: return default


MEZCLA = [int(x) for x in _floats('WOD_CARGA_MEZCLA', [70, 20, 10])] + [0, 0, 0]
PENSAR = _floats('WOD_CARGA_PENSAR', [3, 10])
P_PAGO = float(os.environ.get('WOD_CARGA_PAGO', '0.5') or 0.5)
MEDIR_DESDE = float(os.environ.get('WOD_CARGA_MEDIR_DESDE', '0') or 0)
HIST_DIR = os.environ.get('WOD_CARGA_HIST_DIR')
SEARCH_TERMS = ['medas', 'cabo', 'pecio', 'cueva', 'xabia', 'bonaire', 'similan', 'blue hole', 'roca', 'isla', 'arrecife', 'tenerife',
                'mallorca', 'egipto', 'maldivas', 'cenote', 'caribe', 'red sea', 'thailand', 'calp']
POSITIONS = [(38.79, 0.18), (42.05, 3.20), (28.29, -16.62), (39.57, 2.65), (37.60, -0.98), (20.63, -87.07), (12.15, -68.27), (27.25, 33.82)]
STATIC_FALLBACK = ['/lib/leaflet/leaflet.css', '/lib/markercluster/MarkerCluster.css', '/css/world-dives-v8.css?v=50.50', '/lib/leaflet/leaflet.js',
                   '/lib/markercluster/leaflet.markercluster.js', '/lib/protomaps-leaflet/protomaps-leaflet.js', '/lib/protomaps-leaflet/wd-flavor.js',
                   '/js/world-dives-v8.js?v=50.50', '/js/sw-register.js', '/manifest.webmanifest', '/img/marca/favicon-32.png']

# ---------------------------------------------------------------------------------------------- catálogo compartido (por proceso)
_CAT = {'points': [], 'centers': [], 'static': None, 'images': [], 'lock': threading.Lock()}
_counter = {'centro': random.randrange(1000), 'buzo': random.randrange(100000)}


def today():
    return dt.date.today().isoformat()


def stripe_session_id(url):
    m = re.search(r'(cs_[A-Za-z0-9_]+)', url or '')
    return m.group(1) if m else None


# ---------------------------------------------------------------------------------------------- histogramas (medir.py)
# Cada proceso guarda, por ventanas de 10 s, un histograma de tiempos por petición. Los workers (--processes o
# máquinas remotas con --worker) lo mandan al master con el informe periódico de Locust; el master (o el proceso
# único) lo escribe en WOD_CARGA_HIST_DIR/hist.json. medir.py elige las ventanas del régimen estable (sin la rampa).
WINDOW = 10
_HIST: dict = {}          # ventana -> nombre -> {'n','fail','sum','max','b':{cubo_ms: n}}
_DIRTY: set = set()
_FROM_WORKERS: dict = {}  # worker -> ventana -> nombre -> h
_HIST_LOCK = threading.Lock()


def _bucket(ms):
    ms = int(round(ms))
    if ms < 100: return ms
    if ms < 1000: return int(round(ms, -1))
    if ms < 10000: return int(round(ms, -2))
    return int(round(ms, -3))


@events.request.add_listener
def _record(request_type, name, response_time, response_length, exception=None, **_):
    if MEDIR_DESDE and time.time() < MEDIR_DESDE: return
    w = int(time.time() // WINDOW * WINDOW); rt = response_time or 0
    with _HIST_LOCK:
        win = _HIST.setdefault(w, {})
        h = win.get(name)
        if h is None: h = win[name] = {'n': 0, 'fail': 0, 'sum': 0.0, 'max': 0.0, 'b': {}}
        h['n'] += 1; h['sum'] += rt
        if rt > h['max']: h['max'] = rt
        if exception is not None: h['fail'] += 1
        k = str(_bucket(rt)); h['b'][k] = h['b'].get(k, 0) + 1
        _DIRTY.add(w)


@events.report_to_master.add_listener
def _to_master(client_id, data, **_):
    with _HIST_LOCK:
        if _DIRTY:
            data['wod_hist'] = json.dumps({str(w): _HIST[w] for w in _DIRTY if w in _HIST})
            _DIRTY.clear()


@events.worker_report.add_listener
def _from_worker(client_id, data, **_):
    raw = data.get('wod_hist')
    if not raw: return
    with _HIST_LOCK:
        mine = _FROM_WORKERS.setdefault(client_id, {})
        for w, names in json.loads(raw).items(): mine[w] = names     # la ventana completa de ese worker (sustituye)


def _merged():
    with _HIST_LOCK:
        sources = list(_FROM_WORKERS.values()) + [{str(w): v for w, v in _HIST.items()}]
        out: dict = {}
        for src in sources:
            for w, names in src.items():
                ow = out.setdefault(w, {})
                for name, h in names.items():
                    o = ow.setdefault(name, {'n': 0, 'fail': 0, 'sum': 0.0, 'max': 0.0, 'b': {}})
                    o['n'] += h['n']; o['fail'] += h['fail']; o['sum'] += h['sum']; o['max'] = max(o['max'], h['max'])
                    for k, v in h['b'].items(): o['b'][k] = o['b'].get(k, 0) + v
        return out


def _dump_hist():
    if not HIST_DIR: return
    data = json.dumps({'window': WINDOW, 'written': time.time(), 'workers': len(_FROM_WORKERS), 'data': _merged()})
    p = Path(HIST_DIR) / 'hist.json'; p.parent.mkdir(parents=True, exist_ok=True)
    tmp = p.with_suffix(f'.{os.getpid()}.tmp'); tmp.write_text(data); tmp.replace(p)


def _dump_loop():
    while True:
        gevent.sleep(5)
        try: _dump_hist()
        except Exception: pass


@events.init.add_listener
def _on_init(environment, **_):
    from locust.runners import WorkerRunner
    if HIST_DIR and not isinstance(environment.runner, WorkerRunner): gevent.spawn(_dump_loop)


@events.quitting.add_listener
def _on_quit(environment, **_):
    from locust.runners import WorkerRunner
    if isinstance(environment.runner, WorkerRunner): return
    try: _dump_hist()
    except Exception: pass


# ---------------------------------------------------------------------------------------------- base común
class Web(FastHttpUser):
    abstract = True
    wait_time = between(PENSAR[0], PENSAR[-1])
    connection_timeout = 30.0
    network_timeout = 60.0

    def __init__(self, *a, **kw):
        super().__init__(*a, **kw)
        # Una IP por usuario simulado (X-Forwarded-For): el servidor de carga confía en 127.0.0.1 como proxy.
        self.ip = f'100.{random.randint(64, 127)}.{random.randint(0, 255)}.{random.randint(1, 254)}'
        self.etags = {}; self.views = 0; self.next_visit = random.randint(8, 20)

    def on_start(self):
        self.cargar_web(primera=True)

    def hdr(self, extra=None):
        h = {'X-Forwarded-For': self.ip}
        if extra: h.update(extra)
        return h

    # --- peticiones con nombre de grupo -----------------------------------------------------------
    def get(self, path, name, grupo='pag', ok_codes=(200,), headers=None):
        with self.client.get(path, name=f'{grupo} GET {name}', headers=self.hdr(headers), catch_response=True) as r:
            if r.status_code in ok_codes or r.status_code == 304:
                r.success()
            else:
                r.failure(f'HTTP {r.status_code}: {(r.text or "")[:120]}')
            return r

    def get_json(self, path, name, grupo='pag'):
        r = self.get(path, name, grupo)
        if r.status_code == 200:
            try: return r.json()
            except Exception: return None
        return None

    def post(self, path, data, name, grupo='res', negocio=()):
        """POST con Origin (como el navegador). Los 4xx cuyo texto contiene una de las palabras de `negocio` son
        resultados de negocio (sin plazas, ya resuelta…): cuentan como correctos y se anotan como «biz …»."""
        with self.client.post(path, json=data, name=f'{grupo} POST {name}', headers=self.hdr({'Origin': self.host}), catch_response=True) as r:
            body = None
            try: body = r.json()
            except Exception: pass
            if r.status_code == 200:
                r.success()
            elif 400 <= r.status_code < 500 and r.status_code != 429 and any(w in (r.text or '') for w in negocio):
                r.success(); self.biz(f'{name} · ' + re.sub(r'\d+', 'N', str((body or {}).get('error', ''))[:60]))
            else:
                r.failure(f'HTTP {r.status_code}: {(r.text or "")[:160]}')
            return r.status_code, body

    def biz(self, what):
        events.request.fire(request_type='BIZ', name=f'biz {what}', response_time=0, response_length=0, exception=None, context={})

    def pensar(self, a, b):
        gevent.sleep(random.uniform(a, b))

    # --- carga de la web (estáticos + arranque de la SPA) ------------------------------------------
    def estaticos(self):
        if _CAT['static'] is None:
            with self.client.get('/', name='pag GET / (index)', headers=self.hdr(), catch_response=True) as r:
                html = r.text or ''
                links = re.findall(r'(?:src|href)="(/[^"#]+?\.(?:js|css|png|ico|webmanifest|svg)(?:\?[^"]*)?)"', html)
                _CAT['static'] = links or STATIC_FALLBACK
                r.success() if r.status_code == 200 else r.failure(f'HTTP {r.status_code}')
        else:
            self.get('/', '/ (index)')
        for path in _CAT['static']:
            h = {'If-None-Match': self.etags[path]} if path in self.etags else None
            r = self.get(path, 'estático ' + ('.js' if '.js' in path else '.css' if '.css' in path else 'otro'), headers=h)
            et = r.headers.get('ETag') if r.headers else None
            if et: self.etags[path] = et

    def cargar_web(self, primera=False):
        """Lo que hace el navegador al abrir la web: index + CSS + JS (la primera vez completos; después 304)
        y el arranque de la SPA (/api/me, /api/meta, /api/site-media, /api/map/config) + la portada."""
        self.estaticos()
        self.get('/api/me', '/api/me')
        self.get('/api/meta', '/api/meta')
        media = self.get_json(f'/api/site-media?h={random.choice((1, 2))}', '/api/site-media')
        self.get('/api/map/config', '/api/map/config')
        self.get('/api/setup/status', '/api/setup/status')
        if primera and media and isinstance(media.get('items'), dict):
            imgs = [v.get('url') for v in media['items'].values() if isinstance(v, dict) and str(v.get('url') or '').startswith('/img/')]
            for u in random.sample(imgs, min(3, len(imgs))):
                self.get(u, 'imagen')
        self.portada()

    def portada(self):
        layer = self.get_json('/api/dive-points/map', '/api/dive-points/map')
        if layer and not _CAT['points']:
            fields = layer.get('fields') or []
            i = fields.index('id') if 'id' in fields else 0
            _CAT['points'] = [row[i] for row in layer.get('rows', [])]
        self.get('/api/dive-types', '/api/dive-types')
        self.get('/api/site-promos', '/api/site-promos')

    def contar_vista(self):
        self.views += 1
        if self.views >= self.next_visit:     # vuelve otro día: nueva visita (revalidación con ETag)
            self.views = 0; self.next_visit = random.randint(8, 20); self.cargar_web()

    # --- ayudas del catálogo --------------------------------------------------------------------
    def punto(self):
        if not _CAT['points']: self.portada()
        return random.choice(_CAT['points']) if _CAT['points'] else 1

    def centro_publico(self):
        if not _CAT['centers']:
            d = self.get_json('/api/center-directory?page=1&per_page=60', '/api/center-directory')
            if d: _CAT['centers'] = [x['id'] for x in d.get('items', [])]
        ids = _CAT['centers'] or [c['center_id'] for c in CUENTAS.get('centros', []) if c.get('center_id')]
        return random.choice(ids) if ids else 31

    def centro_reservable(self):
        ids = [c['center_id'] for c in CUENTAS.get('centros', []) if c.get('center_id')]
        return random.choice(ids) if ids else self.centro_publico()

    # --- páginas públicas -----------------------------------------------------------------------
    def ver_punto(self, pid=None):
        pid = pid or self.punto()
        self.get(f'/api/dive-points/{pid}?lang=es', '/api/dive-points/[id]')
        self.get('/api/me', '/api/me')
        self.get(f'/api/dive-points/{pid}/centers', '/api/dive-points/[id]/centers')

    def ver_centro(self, cid=None):
        cid = cid or self.centro_publico()
        return self.get_json(f'/api/centers/{cid}', '/api/centers/[id]')

    def calendario(self, cid):
        """Página «Reservar» de un centro: catálogo con salidas y plazas, equipo y extras."""
        d = self.get_json(f'/api/provider-services?provider_id=0&center_id={cid}', '/api/provider-services?center_id')
        self.get(f'/api/center-equipment?center_id={cid}', '/api/center-equipment')
        self.get(f'/api/center-extras?center_id={cid}', '/api/center-extras')
        return d


# ---------------------------------------------------------------------------------------------- visitante anónimo
class Visitante(Web):
    weight = MEZCLA[0]

    @tag('navegar')
    @task(3)
    def inicio(self):
        self.portada(); self.contar_vista()

    @tag('navegar')
    @task(3)
    def lista_puntos(self):
        d = self.get_json('/api/point-directory?page=1&per_page=24&sort=recommended', '/api/point-directory')
        if d and d.get('zones') and random.random() < 0.6:
            z = random.choice(d['zones'])['name']
            self.get(f'/api/point-directory?zone={z}&page=1&per_page=24&sort=recommended', '/api/point-directory')
        if d and d.get('pages', 1) > 1 and random.random() < 0.3:
            self.get(f'/api/point-directory?page={random.randint(2, min(5, d["pages"]))}&per_page=24&sort=recommended', '/api/point-directory')
        self.contar_vista()

    @tag('navegar')
    @task(4)
    def ficha_punto(self):
        self.ver_punto(); self.contar_vista()

    @tag('navegar')
    @task(2)
    def lista_centros(self):
        self.get('/api/dive-types', '/api/dive-types')
        d = self.get_json('/api/center-directory?page=1&per_page=24', '/api/center-directory')
        if d and d.get('countries') and random.random() < 0.4:
            self.get(f'/api/center-directory?country={d["countries"][0]["name"]}&page=1&per_page=24', '/api/center-directory')
        self.contar_vista()

    @tag('navegar')
    @task(3)
    def ficha_centro(self):
        self.ver_centro(); self.contar_vista()

    @tag('calendario')
    @task(2)
    def calendario_salidas(self):
        cid = self.centro_reservable()
        self.ver_centro(cid)
        self.calendario(cid)
        self.contar_vista()

    @tag('buscar')
    @task(2)
    def buscar(self):
        term = random.choice(SEARCH_TERMS)
        self.get(f'/api/center-directory?q={term}&per_page=8', '/api/center-directory?q')
        self.get(f'/api/point-directory?q={term}&page=1&per_page=24&sort=recommended', '/api/point-directory?q')
        self.contar_vista()

    @tag('navegar')
    @task(1)
    def cercanas(self):
        lat, lon = random.choice(POSITIONS)
        if random.random() < 0.5:
            self.get(f'/api/salidas-cercanas?lat={lat}&lon={lon}&limite=20', '/api/salidas-cercanas')
        else:
            self.get(f'/api/top-dives?lat={lat}&lon={lon}&radius=80', '/api/top-dives')
        self.contar_vista()


# ---------------------------------------------------------------------------------------------- buceador
class Buceador(Web):
    weight = MEZCLA[1]

    def on_start(self):
        super().on_start()
        self.login()

    def login(self):
        buzos = CUENTAS.get('buzos') or []
        if not buzos: raise RuntimeError('No hay cuentas de buceador: ejecuta preparar.py construir y define WOD_CARGA_ESTADO.')
        _counter['buzo'] += 1
        self.usuario = buzos[_counter['buzo'] % len(buzos)]
        st, _ = self.post('/api/auth/login', {'login': self.usuario, 'password': CUENTAS['password']}, '/api/auth/login', grupo='ses')
        self.get('/api/me', '/api/me')
        return st == 200

    @tag('reservar')
    @task(5)
    def reservar(self):
        cid = self.centro_reservable()
        self.ver_centro(cid)
        self.pensar(2, 5)
        cat = self.calendario(cid) or {}
        pax = 1 if random.random() < 0.75 else 2
        hoy = today()
        options = []
        for s in cat.get('items', []):
            if not s.get('bookable') or (s.get('booking_mode') == 'payment' and not s.get('instant')): continue
            if s.get('max_participants') and pax > int(s['max_participants']): continue
            for sl in s.get('slots', []):
                if sl.get('slot_date', '') > hoy and int(sl.get('spots_available') or 0) >= pax:
                    options.append((s, sl))
        if not options:
            self.biz('reserva · sin salidas con plazas'); return
        pay = [o for o in options if o[0].get('booking_mode') == 'payment']
        req = [o for o in options if o[0].get('booking_mode') != 'payment']
        pool = pay if pay and (not req or random.random() < P_PAGO) else req
        s, sl = random.choice(pool[:60])
        self.get(f'/api/booking-quote?center_id={cid}&service_id={s["id"]}&slot_id={sl["id"]}&participants={pax}', '/api/booking-quote', grupo='res')
        self.pensar(3, 8)          # rellena el formulario
        body = {'center_id': cid, 'service_id': s['id'], 'slot_id': sl['id'], 'participants': pax, 'notes': 'Reserva de la prueba de carga'}
        if sl.get('points'): body['dive_point_id'] = sl['points'][0]['id']
        st, d = self.post('/api/bookings', body, '/api/bookings', negocio=('plazas', 'ya no está disponible', 'ya ha empezado'))
        if st != 200 or not d: return
        if d.get('payment_required'):
            self.pagar(d.get('checkout_url'), d.get('id'))
        else:
            self.get(f'/api/bookings/{d["id"]}', '/api/bookings/[id]')

    def pagar(self, checkout_url, bid=None):
        """El paso de pago de la web en modo de pruebas: la persona paga en (el simulador de) Stripe y vuelve a
        #/pago-ok, que pregunta al servidor hasta que el pago deja de estar pendiente."""
        sid = stripe_session_id(checkout_url)
        if not sid or not STRIPE_CONTROL:
            self.biz('pago · sin simulador de Stripe'); return
        self.pensar(5, 12)        # en la página de pago
        with self.client.post(f'{STRIPE_CONTROL}/pagar/{sid}', json={}, name='sim POST stripe /pagar', catch_response=True) as r:
            r.success() if r.status_code == 200 else r.failure(f'HTTP {r.status_code}')
        status = None
        for _ in range(6):
            d = self.get_json(f'/api/payments/session/{sid}', '/api/payments/session/[id]', grupo='res')
            status = ((d or {}).get('payment') or {}).get('status')
            if status != 'pending': break
            gevent.sleep(1.5)
        if status != 'paid': self.biz(f'pago · no confirmado ({status})')
        if bid: self.get(f'/api/bookings/{bid}', '/api/bookings/[id]')

    @tag('reservar')
    @task(3)
    def mis_reservas(self):
        d = self.get_json('/api/bookings', '/api/bookings (buceador)')
        items = (d or {}).get('items') or []
        if items: self.get(f'/api/bookings/{random.choice(items[:20])["id"]}', '/api/bookings/[id]')

    @tag('pagar')
    @task(1)
    def pagar_aceptadas(self):
        """Solicitudes aceptadas por un centro que cobra online: el buceador las paga desde su reserva."""
        d = self.get_json('/api/bookings', '/api/bookings (buceador)')
        pend = [b for b in (d or {}).get('items', []) if b.get('status') == 'accepted_pending_payment']
        if not pend or not STRIPE_CONTROL: return
        b = random.choice(pend)
        st, r = self.post('/api/payments/checkout', {'booking_id': b['id'], 'service_id': b.get('service_id'), 'slot_id': b.get('slot_id')},
                          '/api/payments/checkout', negocio=('plazo', 'ya está pagada', 'no tiene ningún pago'))
        if st == 200 and r and r.get('checkout_url'): self.pagar(r['checkout_url'], b['id'])

    @tag('navegar')
    @task(2)
    def navegar(self):
        self.ver_punto() if random.random() < 0.5 else self.ver_centro()
        self.contar_vista()


# ---------------------------------------------------------------------------------------------- personal del centro
class Centro(Web):
    weight = MEZCLA[2]

    def on_start(self):
        self.next_visit = 10 ** 9
        self.estaticos()
        centros = CUENTAS.get('centros') or []
        if not centros: raise RuntimeError('No hay cuentas de centro: ejecuta preparar.py construir y define WOD_CARGA_ESTADO.')
        _counter['centro'] += 1
        acc = centros[_counter['centro'] % len(centros)]
        self.post('/api/auth/login', {'login': acc['usuario'], 'password': acc['password']}, '/api/auth/login', grupo='ses')
        self.get('/api/me', '/api/me')
        self.slots_con_reservas = []
        self.solicitudes()

    @tag('panel')
    @task(3)
    def planning(self):
        m = dt.date.today()
        if random.random() < 0.3: m = (m.replace(day=1) + dt.timedelta(days=32))
        d = self.get_json(f'/api/center/planning?month={m.strftime("%Y-%m")}', '/api/center/planning')
        if d:
            self.slots_con_reservas = [s['id'] for s in d.get('slots', []) if any(b.get('status') == 'confirmed' for b in s.get('bookings', []))]

    @tag('panel')
    @task(3)
    def reservas(self):
        t = dt.date.today()
        d = self.get_json(f'/api/bookings?from={t.isoformat()}&to={(t + dt.timedelta(days=7)).isoformat()}&order=asc', '/api/bookings (centro, semana)')
        items = (d or {}).get('items') or []
        if items and random.random() < 0.5:
            self.get(f'/api/bookings/{random.choice(items)["id"]}', '/api/bookings/[id] (centro)')

    @tag('panel', 'aceptar')
    @task(3)
    def solicitudes(self):
        d = self.get_json('/api/center/requests', '/api/center/requests')
        items = (d or {}).get('items') or []
        for it in items[:random.randint(1, 3)]:
            self.pensar(1, 3)
            if it.get('enough_spots', True):
                self.post(f'/api/bookings/{it["id"]}/status', {'status': 'confirmed'}, '/api/bookings/[id]/status (aceptar)',
                          negocio=('ya no está pendiente', 'plazas', 'plazo', 'no se puede confirmar', 'pagando',
                                   'espera el pago'))   # another person of the same centre accepted it a moment before
            else:
                self.post(f'/api/bookings/{it["id"]}/status', {'status': 'rejected', 'reason': 'No quedan plazas en esa salida'},
                          '/api/bookings/[id]/status (rechazar)', negocio=('ya no se puede rechazar', 'ya no está pendiente'))

    @tag('panel', 'checkin')
    @task(2)
    def hoy_y_checkin(self):
        d = self.get_json('/api/pro/hoy', '/api/pro/hoy')
        slots = [s['slot_id'] for s in (d or {}).get('slots', []) if s.get('confirmed')]
        sid = random.choice(slots) if slots else (random.choice(self.slots_con_reservas) if self.slots_con_reservas else None)
        if not sid: return
        m = self.get_json(f'/api/manifest/{sid}', '/api/manifest/[id]')
        pend = [x for x in (m or {}).get('divers', []) if not x.get('checked_in_at') and x.get('status') == 'confirmed']
        if not pend: return
        self.pensar(1, 3)
        changes = [{'slot_id': sid, 'booking_id': x['booking_id'], 'seat': x['seat'], 'field': 'status', 'base': '', 'value': 'present',
                    'at': dt.datetime.now().isoformat(timespec='seconds')} for x in pend[:random.randint(1, 4)]]
        self.post('/api/manifest/sync', {'changes': changes}, '/api/manifest/sync (check-in)')

    @tag('panel', 'cobro')
    @task(1)
    def cobro_en_centro(self):
        """Pago sin Stripe: el centro registra el cobro de una reserva confirmada «a pagar en el centro»."""
        d = self.get_json('/api/bookings?payment=at_center&order=asc&limit=50', '/api/bookings (centro, cobros)')
        items = [b for b in (d or {}).get('items', []) if b.get('status') == 'confirmed']
        if not items: return
        b = random.choice(items)
        self.post(f'/api/bookings/{b["id"]}/payment', {'payment_status': 'paid', 'payment_method': 'Efectivo'}, '/api/bookings/[id]/payment (en el centro)',
                  negocio=('plazas', 'pago online', 'Stripe'))
