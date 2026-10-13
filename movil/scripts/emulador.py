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
Usage: python3 emulador.py OUT_DIR DATA_DIR (DATA_DIR: data/pruebas of the test server). Exit 1 on any failure."""
import json
import subprocess
import sys
import time
import urllib.request
from pathlib import Path

import websocket  # websocket-client

PKG = 'com.worldives.app.pruebas'
SERVER = 'http://10.0.2.2:8100'
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
            c.js("document.querySelector('.marca-check:not(.si)')?.click()", 1)
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
    i_.until("document.querySelectorAll('.wda-tab').length > 0", 45)
    tabs = i_.js("[...document.querySelectorAll('.wda-tab')].map(a => a.getAttribute('href'))")
    names = i_.js("[...document.querySelectorAll('.wda-tab > span:nth-child(2)')].map(e => e.textContent.trim())")
    check('instructor · sin la pestaña Solicitudes', tabs == ['#/', '#/agenda', '#/escanear', '#/mas'], tabs)
    print('   pestañas del instructor (en su idioma):', names, flush=True)
    captura('18-instructor-hoy')

    bad = [n for n, ok in checks if not ok]
    print(f'\n{len(checks) - len(bad)}/{len(checks)} comprobaciones correctas en el emulador')
    return 1 if bad else 0


if __name__ == '__main__':
    sys.exit(main())
