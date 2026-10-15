"""Checks WORLDIVES Pruebas on a real Android (the emulator of GitHub Actions), driving its WebView through Chrome
DevTools (adb forward → webview_devtools_remote_<pid>). The test server of the zip runs on the computer, which the
emulator reaches at http://10.0.2.2:8100 (scripts/iniciar.py --pruebas --red-local with WOD_IP_MOVIL=10.0.2.2).

1. The launcher: band, server field, quick-entry buttons and the native «Servidor» plugin.
2. Quick entry with buzo.prueba: the app restarts on the test server and the web opens in «modo app» with the real
   Capacitor plugins (App, Browser, Device, Share, Geolocation, SystemBars, Servidor).
3. Inicio, Explorar, Reservas, Mi área and Ajustes with the phone's own screenshots (adb screencap).
4. «Reportar fallo» with the native screenshot, saved by the server in its «fallos» folder.
5. Back button, «Cambiar de servidor» back to the launcher.
6. v50.49 · Centro PRO with centro.prueba: its tabs, «Hoy» in less than 5 s, the native plugins of the professional app
   (barcode scanner, local notifications, vibration, network, push), the boat list with the 56 px check-in, a mark
   made in airplane mode that is sent when the network comes back, and the instructor without «Solicitudes».
7. v50.55 · Seguridad de la app PRO (encargo 2), with the real plugin «Seguridad» (Android Keystore, BiometricPrompt):
   a centre on a phone without screen lock creates a 6-digit PIN; the session is renewed natively; back after the
   threshold (5 s here, 5 minutes in the real app) the PIN is asked; a wrong PIN says how many attempts are left; the
   offline data are not readable in the app's files (adb root, every file of the app searched for a diver's name);
   5 wrong PINs end the session on the server and wipe the phone; the owner closes the phone from «Dispositivos
   conectados» and the phone wipes itself; with a screen lock the system's own prompt (the phone's code) is used.
Usage: python3 emulador.py OUT_DIR DATA_DIR (DATA_DIR: data/pruebas of the test server). Exit 1 on any failure."""
import http.cookiejar
import json
import sqlite3
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import websocket  # websocket-client

PKG = 'com.worldives.app.pruebas'
SERVER = 'http://10.0.2.2:8100'
HOST = 'http://127.0.0.1:8100'          # the same test server, seen from the computer (the «web» of section 7)
PASSWORD = 'Worldives-Prueba-2026'      # the public password of the *.prueba accounts (README-PRUEBAS.md)
PIN = '246802'
OUT = Path(sys.argv[1]); OUT.mkdir(parents=True, exist_ok=True)
DATA = Path(sys.argv[2]) if len(sys.argv) > 2 else None
checks = []


def check(name, ok, detail=''):
    checks.append((name, bool(ok)))
    print(('OK  ' if ok else 'MAL ') + name + ('' if ok else f'  → {detail}'), flush=True)


def adb(*args, timeout=120):
    return subprocess.run(['adb', *args], capture_output=True, text=True, timeout=timeout).stdout.strip()


def captura(name):
    png = subprocess.run(['adb', 'exec-out', 'screencap', '-p'], capture_output=True, timeout=60).stdout
    (OUT / f'{name}.png').write_bytes(png)


def devtools():
    """Forward the WebView's DevTools socket of the app's current process to localhost:9222."""
    pid = ''
    for _ in range(40):
        pid = adb('shell', 'pidof', PKG)
        if pid: break
        time.sleep(1)
    if not pid: raise SystemExit('La app no está abierta')
    adb('forward', '--remove-all')
    adb('forward', 'tcp:9222', f'localabstract:webview_devtools_remote_{pid.split()[0]}')
    for _ in range(40):
        try:
            return json.loads(urllib.request.urlopen('http://127.0.0.1:9222/json/list', timeout=3).read())
        except Exception:
            time.sleep(1)
    raise SystemExit('Sin DevTools de la WebView')


class Page:
    """The smallest CDP client: evaluate JavaScript in the page whose URL starts with `prefix`."""

    def __init__(self, prefix, timeout=60):
        end = time.time() + timeout; target = None
        while time.time() < end and not target:
            try:
                targets = devtools()
                target = next((t for t in targets if t.get('type') == 'page' and t.get('url', '').startswith(prefix)), None)
            except SystemExit:
                pass
            if not target: time.sleep(2)
        if not target: raise SystemExit(f'No se encuentra la página {prefix}: {[t.get("url") for t in targets]}')
        self.url = target['url']
        self.ws = websocket.create_connection(target['webSocketDebuggerUrl'], timeout=60, suppress_origin=True)
        self.n = 0

    def js(self, expr, wait=0.0):
        self.n += 1
        self.ws.send(json.dumps({'id': self.n, 'method': 'Runtime.evaluate', 'params': {'expression': expr, 'awaitPromise': True, 'returnByValue': True}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get('id') == self.n: break
        if wait: time.sleep(wait)
        res = msg.get('result', {})
        if 'exceptionDetails' in res: return {'error': res['exceptionDetails'].get('text')}
        return res.get('result', {}).get('value')

    def until(self, expr, timeout=30):
        end = time.time() + timeout
        while time.time() < end:
            try:
                if self.js(expr): return True
            except Exception:
                pass
            time.sleep(1)
        return False

    def go(self, hash_, wait=2.5):
        self.js(f"location.hash = {json.dumps(hash_)}", wait)


def pin(pg, digits):
    for d in digits:
        pg.js(f"document.querySelector('#wda-bloqueo [data-t=\"{d}\"]').click()", 0.2)
    time.sleep(0.8)


def crear_pin(pg, name=None):
    """v50.55: a professional on a phone without screen lock creates the app's PIN right after signing in."""
    if not pg.until("!!document.querySelector('#wda-bloqueo .wda-teclado')", 40): return False
    if name: captura(name)
    pin(pg, PIN); pin(pg, PIN)
    return pg.until("!document.getElementById('wda-bloqueo')", 20)


def ui(etiqueta):
    """What Android shows now (focused window and the texts on screen): to understand a failure without the screenshots."""
    foco = [l.strip() for l in adb('shell', 'dumpsys', 'window').splitlines() if 'mCurrentFocus' in l or 'mFocusedApp' in l][:2]
    adb('shell', 'uiautomator', 'dump', '/sdcard/ui.xml')
    import re as _re
    textos = [t for t in _re.findall(r'text="([^"]+)"', adb('shell', 'cat', '/sdcard/ui.xml')) if t.strip()][:25]
    print(f'   [{etiqueta}] ventana: {foco} · textos: {textos}', flush=True)
    return ' '.join(foco)


def esperar_ventana(patron, segundos=20):
    """Waits until the focused window matches (the system's prompt or the phone's code screen)."""
    fin = time.time() + segundos
    while time.time() < fin:
        foco = ' '.join(l for l in adb('shell', 'dumpsys', 'window').splitlines() if 'mCurrentFocus' in l)
        if any(x in foco for x in patron): return foco
        time.sleep(1)
    return ''


def db(query, args=()):
    c = sqlite3.connect(DATA / 'worldives.sqlite3'); c.row_factory = sqlite3.Row   # WOD_DB_PATH of scripts/iniciar.py --pruebas
    try:
        return [dict(r) for r in c.execute(query, args).fetchall()]
    finally:
        c.close()


def a_primer_plano(segundos):
    """Home, wait in the background, open the app again (same task: the WebView and its DevTools stay)."""
    adb('shell', 'input', 'keyevent', '3'); time.sleep(segundos)
    adb('shell', 'am', 'start', '-n', f'{PKG}/com.worldives.app.MainActivity'); time.sleep(3)


class Web:
    """The owner on a computer: the same test server through 127.0.0.1, with cookies and the Origin of a browser."""

    def __init__(self):
        self.op = urllib.request.build_opener(urllib.request.HTTPCookieProcessor(http.cookiejar.CookieJar()))

    def call(self, path, data=None):
        h = {'User-Agent': 'Mozilla/5.0 (X11; Linux x86_64) Chrome/140.0 Safari/537.36'}
        body = None
        if data is not None:
            body = json.dumps(data).encode(); h.update({'Content-Type': 'application/json', 'Origin': HOST})
        try:
            with self.op.open(urllib.request.Request(HOST + path, data=body, headers=h, method='POST' if data is not None else 'GET'), timeout=30) as r:
                return r.status, json.loads(r.read() or b'{}')
        except urllib.error.HTTPError as e:
            return e.code, json.loads(e.read() or b'{}')


def seguridad(start):
    """7. v50.55 · encargo 2 with the real native plugin."""
    start.js("document.querySelector('[data-cuenta=\"centro.prueba\"]').click()", 6)
    s = Page(SERVER, timeout=90)
    check('seguridad · centro en un móvil sin bloqueo de pantalla: crea un PIN de 6 números', crear_pin(s, '19-seguridad-crear-pin'))
    st = s.js("Capacitor.Plugins.Seguridad.estado()") or {}
    check('seguridad · token de renovación guardado en el Keystore y protegido por el PIN', st.get('token') is True and st.get('modo') == 'pin', st)
    r = s.js("Capacitor.Plugins.Seguridad.renovar({ua: navigator.userAgent})") or {}
    check('seguridad · el móvil renueva la sesión de 15 minutos con una petición nativa', r.get('ok') is True and s.js("fetch('/api/me').then(r => r.json()).then(d => d.authenticated)") is True, r)
    dev = (db("SELECT * FROM device_sessions WHERE revoked_at IS NULL ORDER BY id DESC LIMIT 1") or [{}])[0]
    check('seguridad · sesión del dispositivo en el servidor con modelo y sistema', dev.get('platform') == 'android' and bool(dev.get('model')), dev)
    # back from the background
    s.js("localStorage.setItem('wda-seg-umbral', '5')")
    adb('shell', 'input', 'keyevent', 'KEYCODE_APP_SWITCH'); time.sleep(2.5); captura('20-seguridad-recientes'); adb('shell', 'input', 'keyevent', '3')
    a_primer_plano(9)
    check('seguridad · tras el tiempo en segundo plano la app pide el PIN', s.until("!!document.querySelector('#wda-bloqueo .wda-teclado')", 20), s.js("document.body.innerText.slice(0, 200)"))
    captura('21-seguridad-bloqueada')
    pin(s, '000000')
    check('seguridad · un PIN incorrecto dice cuántos intentos quedan', s.until("/(quedan|left|restantes)\\D*4/i.test((document.getElementById('wda-bloqueo-msg') || {}).textContent || '')", 15),
          s.js("document.getElementById('wda-bloqueo') && document.getElementById('wda-bloqueo').innerText"))
    pin(s, PIN)
    check('seguridad · con el PIN correcto vuelve a la app', s.until("!document.getElementById('wda-bloqueo') && document.querySelectorAll('.wda-tab').length === 5", 20))
    # offline data: open today's departure so the boat list is kept on the phone, then look into the app's files
    sid = s.js("(document.querySelector('a[href^=\"#/salida?id=\"]') || {}).getAttribute ? document.querySelector('a[href^=\"#/salida?id=\"]').getAttribute('href') : null")
    if sid: s.go(sid, 4)
    nombre = s.js("""fetch('/api/manifest/day?date=' + WD.wdToday()).then(r => r.json()).then(d => ((d.slots || []).flatMap(x => x.divers || []).map(x => x.name).filter(n => n && n.length > 5)[0]) || null)""")
    guardado = s.js(f"WD_SEC.keys().some(k => /^(wd-day-|wda-pro-)/.test(k) && (localStorage.getItem(k) || '').includes({json.dumps(nombre or '#')}))")
    claves = s.js("Object.keys(localStorage)") or []
    check('sin conexión · el móvil guarda la lista del barco (con el nombre de un buceador)', bool(nombre) and guardado is True, (nombre, guardado))
    check('sin conexión · nada de esos datos queda en el almacenamiento de la web', not any(k.startswith(('wd-day-', 'wda-pro-', 'wda-res:', 'wda-qr-', 'wdenc:')) for k in claves), claves)
    time.sleep(8)   # the WebView writes its storage to disk a few seconds later
    copia = OUT / 'datos-app'
    print('   adb root:', adb('root'), flush=True); time.sleep(4); adb('wait-for-device')
    subprocess.run(['adb', 'pull', f'/data/data/{PKG}', str(copia)], capture_output=True, timeout=180)
    archivos = [f for f in copia.rglob('*') if f.is_file()]
    claro = []
    for f in archivos:
        data = f.read_bytes()
        if nombre and any(v in data for v in (nombre.encode('utf-8'), nombre.encode('utf-16-le'), nombre.encode('latin-1', 'ignore'))): claro.append(str(f.relative_to(copia)))
    cifrado = [str(f.relative_to(copia)) for f in archivos if f.name == 'worldives_datos.xml' and b'wda-pro-' in f.read_bytes()]   # the plugin's encrypted store
    print(f'   archivos de la app copiados: {len(archivos)} · almacén cifrado: {cifrado} · con el nombre en claro: {claro}', flush=True)
    check('sin conexión · copiando los archivos de la app, los datos guardados no se pueden leer', len(archivos) > 5 and bool(cifrado) and not claro, (len(archivos), cifrado[:3], claro))
    s = Page(SERVER, timeout=60)   # adb restarted as root: DevTools again
    # five wrong PINs
    a_primer_plano(9)
    s.until("!!document.querySelector('#wda-bloqueo .wda-teclado')", 20)
    for i in range(5):
        pin(s, '111111')
        s.until(f"/(quedan|left|restantes)\\D*{4 - i}/i.test((document.getElementById('wda-bloqueo-msg') || {{}}).textContent || '') || !!document.getElementById('wda-bloqueo-entrar')", 15)
    time.sleep(2)
    txt = s.js("document.getElementById('wda-bloqueo') && document.getElementById('wda-bloqueo').innerText") or ''
    st = s.js("Capacitor.Plugins.Seguridad.estado()") or {}
    ultimo = (db("SELECT revoked_reason FROM device_sessions ORDER BY id DESC LIMIT 1") or [{}])[0]
    fin_ok = s.js("!!document.getElementById('wda-bloqueo-entrar')")   # «Sesión cerrada» with «Entrar con mi contraseña» (in the phone's language)
    check('5 fallos · la app cierra la sesión, lo explica y borra el token', fin_ok and '5' in txt and st.get('token') is False, (txt, st))
    check('5 fallos · la sesión del móvil termina también en el servidor', ultimo.get('revoked_reason') == 'unlock_failures', ultimo)
    check('5 fallos · no queda nada guardado en la web del móvil', not [k for k in (s.js("Object.keys(localStorage)") or []) if k.startswith(('wdenc:', 'wd-day-', 'wda-pro-'))])
    captura('22-seguridad-cinco-fallos')
    # signed in again with the password, then closed from the computer
    s.js("document.getElementById('wda-bloqueo-entrar').click()", 2)
    s.until("!!document.getElementById('login-form')", 20)
    s.js(f"document.getElementById('login').value = 'centro.prueba'; document.getElementById('password').value = {json.dumps(PASSWORD)}; document.querySelector('#login-form button[type=submit]').click()")
    check('seguridad · vuelve a entrar con su contraseña y crea el PIN', crear_pin(s))
    web = Web()
    code, _ = web.call('/api/auth/login', {'login': 'centro.prueba', 'password': PASSWORD})
    _, devs = web.call('/api/account/devices')
    app = next((x for x in devs.get('items', []) if x.get('kind') == 'app'), None)
    correo = db("SELECT COUNT(*) AS n FROM email_outbox WHERE template = 'new_device_login'")
    check('correo · «Nuevo inicio de sesión» al entrar desde el ordenador', (correo or [{}])[0].get('n', 0) >= 1, correo)
    code2, res = web.call('/api/account/devices/close', {'id': app['id']}) if app else (0, {})
    check('ordenador · «Dispositivos conectados» lista el móvil y lo cierra', code == 200 and bool(app) and code2 == 200, (code, app, code2, res))
    ok = s.js("WD_SEC.renew()"); time.sleep(2)
    txt = s.js("document.getElementById('wda-bloqueo') && document.getElementById('wda-bloqueo').innerText") or ''
    st = s.js("Capacitor.Plugins.Seguridad.estado()") or {}
    check('móvil · cerrado desde el ordenador: sale, borra sus datos y vuelve al acceso', ok is False and s.js("!!document.getElementById('wda-bloqueo-entrar')") and st.get('token') is False, (ok, txt, st))
    captura('23-seguridad-cerrada-a-distancia')
    # with a screen lock: the phone's own code through the system prompt (the fingerprint needs a real finger)
    adb('shell', 'locksettings', 'set-pin', '1111'); time.sleep(2)
    s.js("document.getElementById('wda-bloqueo-entrar').click()", 2)
    s.until("!!document.getElementById('login-form')", 20)
    s.js(f"document.getElementById('login').value = 'centro.prueba'; document.getElementById('password').value = {json.dumps(PASSWORD)}; document.querySelector('#login-form button[type=submit]').click()", 2)
    foco = esperar_ventana(('ConfirmDeviceCredential', 'BiometricPrompt', 'systemui', 'Credential'), 20)
    ui('código del móvil al activar'); captura('24-seguridad-codigo-del-movil')
    adb('shell', 'input', 'text', '1111'); adb('shell', 'input', 'keyevent', '66'); time.sleep(4)
    if not (s.js("Capacitor.Plugins.Seguridad.estado()") or {}).get('token'): ui('tras escribir el código')
    st = s.js("Capacitor.Plugins.Seguridad.estado()") or {}
    check('con bloqueo de pantalla · protege el token con el código del móvil (BiometricPrompt)', st.get('modo') == 'sistema' and st.get('token') is True, st)
    s.js("localStorage.setItem('wda-seg-umbral', '5')")   # the wipe of the 5 failures took it with the web storage
    a_primer_plano(9)
    esperar_ventana(('ConfirmDeviceCredential', 'BiometricPrompt', 'systemui', 'Credential'), 15); ui('código del móvil al volver')
    captura('25-seguridad-desbloquear-con-codigo')
    adb('shell', 'input', 'text', '1111'); adb('shell', 'input', 'keyevent', '66'); time.sleep(4)
    check('con bloqueo de pantalla · al volver, se desbloquea con el código del móvil', s.until("!document.getElementById('wda-bloqueo') && document.querySelectorAll('.wda-tab').length === 5", 20),
          s.js("document.body.innerText.slice(0, 200)"))
    adb('shell', 'locksettings', 'clear', '--old', '1111')


def main():
    # 1. the launcher
    p = Page('https://localhost')
    check('lanzador · banda «ENTORNO DE PRUEBAS»', 'ENTORNO DE PRUEBAS' in (p.js('document.body.innerText') or '').upper())
    check('lanzador · siete cuentas de prueba', p.js("document.querySelectorAll('[data-cuenta]').length") == 7)
    check('lanzador · plugin nativo «Servidor»', p.js("!!(window.Capacitor && Capacitor.Plugins.Servidor)"))
    check('lanzador · versión visible', p.until("/WORLDIVES Pruebas \\d/.test(document.getElementById('version').textContent)", 10), p.js("document.getElementById('version').textContent"))
    captura('01-lanzador')
    p.js(f"document.getElementById('servidor').value = {json.dumps(SERVER)}; document.getElementById('probar').click()", 4)
    check('lanzador · «Probar la conexión» llega al servidor', 'Conectado' in (p.js("document.getElementById('estado').textContent") or ''), p.js("document.getElementById('estado').textContent"))
    captura('02-lanzador-conectado')
    p.js("document.querySelector('[data-cuenta=\"buzo.prueba\"]').click()", 6)

    # 2. the web in «modo app», with the real plugins
    w = Page(SERVER, timeout=90)
    ok = w.until("document.documentElement.classList.contains('wd-app-pruebas') && document.querySelectorAll('.wda-tab').length === 5", 45)
    check('app · entra con buzo.prueba y abre el módulo Buceador', ok, w.js("document.body.innerText.slice(0, 300)"))
    plugins = w.js("Object.keys((window.Capacitor && Capacitor.Plugins) || {}).sort()") or []
    check('app · plugins nativos disponibles en la web', all(x in plugins for x in ('App', 'Browser', 'Device', 'Geolocation', 'Servidor', 'Share', 'SystemBars')), plugins)
    check('app · banda fija de pruebas', w.js("!!document.querySelector('.wda-banda')"))
    check('app · el usuario es Bea Buzo', 'Bea' in (w.js("document.querySelector('.cab').innerText") or ''))
    # Layout on a real screen: the band under the status bar, the tabs above the gesture bar, nothing wider than the screen.
    lay = w.js("""(() => { const cs = getComputedStyle(document.documentElement), b = document.querySelector('.wda-banda').getBoundingClientRect(),
        t = document.querySelector('.wda-tabs').getBoundingClientRect();
        return { w: innerWidth, h: innerHeight, top: cs.getPropertyValue('--safe-area-inset-top').trim(), bottom: cs.getPropertyValue('--safe-area-inset-bottom').trim(),
                 banda: Math.round(b.top), tabs: Math.round(t.bottom), ancho: document.scrollingElement.scrollWidth, ua: navigator.userAgent }; })()""") or {}
    print('   pantalla:', json.dumps(lay, ensure_ascii=False), flush=True)
    top = float((lay.get('top') or '0px').replace('px', '') or 0)
    check('diseño · la banda queda debajo de la barra de estado', lay.get('banda', -1) >= top - 1, lay)
    check('diseño · las pestañas caben en la pantalla', 0 < lay.get('tabs', 0) <= lay.get('h', 0) + 1, lay)
    check('diseño · nada más ancho que la pantalla', lay.get('ancho', 9999) <= lay.get('w', 0), lay)
    w.until("document.querySelectorAll('#wda-salidas .tarjeta-salida').length > 0", 15)
    check('inicio · salidas con plazas del entorno de pruebas', (w.js("document.querySelectorAll('#wda-salidas .tarjeta-salida').length") or 0) > 0)
    captura('03-inicio')
    w.js("document.querySelector('#wda-salidas [data-reservar]')?.click()", 3)
    check('inicio · la reserva rápida se abre en una hoja', w.js("!!document.querySelector('.wda-capa.abierta .hoja')"))
    captura('04-reserva-rapida')
    # back button of Android closes the sheet
    adb('shell', 'input', 'keyevent', '4'); time.sleep(1.5)
    check('nativo · el botón atrás cierra la hoja', w.js("document.querySelectorAll('.wda-capa').length") == 0)
    for i, (h, name) in enumerate((('#/explorar', 'explorar'), ('#/reservas', 'reservas'), ('#/mi-area', 'mi-area'), ('#/ajustes', 'ajustes')), start=5):
        w.go(h, 3.5); captura(f'0{i}-{name}')
    check('ajustes · versión de la app y de la web', 'web v' in (w.js("document.getElementById('wda-version').textContent") or ''), w.js("document.getElementById('wda-version').textContent"))
    info = w.js("Capacitor.Plugins.Device.getInfo()") or {}
    check('nativo · Device.getInfo', info.get('platform') == 'android', info)
    shot = w.js("Capacitor.Plugins.Servidor.captura().then(r => r.captura.length)") or 0
    check('nativo · captura de pantalla para «Reportar fallo»', isinstance(shot, int) and shot > 5000, shot)
    # 4. «Reportar fallo» end to end
    w.go('#/', 2.5)
    w.js("document.getElementById('wda-fallo').click()", 4)
    check('reportar fallo · hoja con la captura', w.js("!!document.querySelector('.wda-capa img.captura-mini')"))
    captura('09-reportar-fallo')
    w.js("document.getElementById('wda-qp').value = 'Prueba automática desde el emulador'; document.getElementById('wda-enviar-fallo').click()", 4)
    if DATA:
        saved = sorted((DATA / 'fallos').glob('*.json')) if (DATA / 'fallos').exists() else []
        last = json.loads(saved[-1].read_text(encoding='utf-8')) if saved else {}
        check('reportar fallo · guardado en el servidor con su captura', last.get('cuenta') == 'buzo.prueba' and bool(last.get('captura')) and 'android' in last.get('movil', '').lower(), last)
    # 5. back to the launcher
    w.go('#/ajustes', 2.5)
    w.js("document.getElementById('wda-r-servidor').click()", 6)
    p2 = Page('https://localhost', timeout=60)
    check('ajustes · «Cambiar de servidor» vuelve al lanzador con la última dirección', p2.js("document.getElementById('servidor').value") == SERVER, p2.js("document.getElementById('servidor').value"))
    captura('10-vuelta-al-lanzador')

    # 6. v50.49 · Centro PRO
    p2.js("document.querySelector('[data-cuenta=\"centro.prueba\"]').click()", 6)
    c = Page(SERVER, timeout=90)
    check('centro · v50.55: tras entrar crea el PIN de la app (móvil sin bloqueo de pantalla)', crear_pin(c))
    ok = c.until("document.querySelectorAll('.wda-tab').length === 5 && !!document.querySelector('.cifras')", 45)
    tabs = c.js("[...document.querySelectorAll('.wda-tab')].map(a => a.getAttribute('href'))")
    check('centro · entra con centro.prueba: Hoy, Agenda, Escanear, Solicitudes, Más', ok and tabs == ['#/', '#/agenda', '#/escanear', '#/solicitudes', '#/mas'], tabs)
    t_hoy = c.js("window.WDAMedidas && window.WDAMedidas.hoy")
    check('centro · «Hoy» en menos de 5 s en el móvil', isinstance(t_hoy, (int, float)) and t_hoy < 5000, t_hoy)
    print('   «Hoy» se ha visto en', t_hoy, 'ms', flush=True)
    plugins = c.js("Object.keys((window.Capacitor && Capacitor.Plugins) || {}).sort()") or []
    check('centro · plugins nativos de la app PRO', all(x in plugins for x in ('CapacitorBarcodeScanner', 'LocalNotifications', 'Haptics', 'Network', 'PushNotifications', 'PushListo')), plugins)
    check('centro · sin Firebase todavía: la app no pide notificaciones push', (c.js("Capacitor.Plugins.PushListo.estado()") or {}).get('firebase') is False)
    captura('11-centro-hoy')
    sid = c.js("(document.querySelector('a[href^=\"#/salida?id=\"]') || {}).getAttribute ? document.querySelector('a[href^=\"#/salida?id=\"]').getAttribute('href') : null")
    check('centro · hoy hay una salida con buceadores (datos de prueba)', bool(sid), c.js("document.body.innerText.slice(0, 400)"))
    if sid:
        c.go(sid, 4)
        sizes = c.js("[...document.querySelectorAll('.marca-check')].map(b => [b.offsetWidth, b.offsetHeight])") or []
        check('salida · botones de llegada de 56 px en la pantalla del móvil', sizes and all(w >= 56 and h >= 56 for w, h in sizes), sizes)
        captura('12-salida')
        c.js("document.querySelector('.marca-check:not(.si)').click()", 2)
        check('salida · marcar una llegada', (c.js("document.querySelectorAll('.marca-check.si').length") or 0) >= 1)
        # airplane mode: the mark waits on the phone and goes when the network is back
        adb('shell', 'cmd', 'connectivity', 'airplane-mode', 'enable'); time.sleep(4)
        offline = c.js("fetch('/api/health', {cache: 'no-store'}).then(() => false).catch(() => true)")
        if offline:
            c.js("(document.querySelector('.marca-check:not(.si)') || document.querySelector('.marca-check'))?.click()", 1)
            c.until("JSON.parse(localStorage.getItem('wda-pro-cola') || '[]').length === 1", 30)
            queued = c.js("JSON.parse(localStorage.getItem('wda-pro-cola') || '[]').length")
            check('sin conexión · la marca queda guardada en el móvil', queued == 1, (queued, c.js("navigator.onLine")))
            captura('13-sin-conexion')
            adb('shell', 'cmd', 'connectivity', 'airplane-mode', 'disable')
            check('sin conexión · al volver la red se envía sola', c.until("JSON.parse(localStorage.getItem('wda-pro-cola') || '[]').length === 0", 60),
                  c.js("localStorage.getItem('wda-pro-cola')"))
        else:
            adb('shell', 'cmd', 'connectivity', 'airplane-mode', 'disable')
            print('   (el emulador sigue llegando al servidor en modo avión: la prueba sin conexión se hace en el navegador)', flush=True)
    for i, (h, name) in enumerate((('#/agenda', 'agenda'), ('#/escanear', 'escanear'), ('#/solicitudes', 'solicitudes'), ('#/mas', 'mas')), start=14):
        c.go(h, 3.5); captura(f'{i}-centro-{name}')
        if name == 'escanear': check('escanear · botón de la cámara', c.js("!!document.getElementById('wda-scan')"))
    c.go('#/ajustes', 2.5)
    c.js("document.getElementById('wda-r-servidor').click()", 6)
    p3 = Page('https://localhost', timeout=60)
    p3.js("document.querySelector('[data-cuenta=\"instructor.prueba\"]').click()", 6)
    i_ = Page(SERVER, timeout=90)
    if not crear_pin(i_):
        print('   instructor sin PIN:', i_.js("document.body.innerText.slice(0, 300)"), '· aviso:', i_.js("(document.getElementById('toast') || {}).innerText"), flush=True); ui('instructor')
    i_.until("document.querySelectorAll('.wda-tab').length > 0", 45)
    tabs = i_.js("[...document.querySelectorAll('.wda-tab')].map(a => a.getAttribute('href'))")
    names = i_.js("[...document.querySelectorAll('.wda-tab > span:nth-child(2)')].map(e => e.textContent.trim())")
    check('instructor · sin la pestaña Solicitudes', tabs == ['#/', '#/agenda', '#/escanear', '#/mas'], tabs)
    print('   pestañas del instructor (en su idioma):', names, flush=True)
    captura('18-instructor-hoy')

    # 7. v50.55 · Seguridad de la app PRO
    i_.go('#/ajustes', 2.5)
    i_.js("document.getElementById('wda-r-servidor').click()", 6)
    seguridad(Page('https://localhost', timeout=60))

    bad = [n for n, ok in checks if not ok]
    print(f'\n{len(checks) - len(bad)}/{len(checks)} comprobaciones correctas en el emulador')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
