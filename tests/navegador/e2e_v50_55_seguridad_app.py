#!/usr/bin/env python3
"""v50.55 · Encargo 2 «Seguridad de la app WORLDIVES PRO», the web side of the app (public/js/wd-app-seg.js) in a
phone-sized Chromium with the user agent of WORLDIVES Pruebas and a test double of the native plugin «Seguridad»
(the real one, movil/android/.../SeguridadPlugin.java, is checked on the Android emulator: movil/scripts/emulador.py).

1. A diver signs in from the app: the device gets its refresh token (no lock by default), «Dispositivos conectados»
   shows it, the 15-minute access session is renewed alone (also after a 401), the offline data are encrypted in the
   web storage and come back after reopening; «Cerrar sesión» ends the device session and deletes the data.
2. A centre signs in from a phone without screen lock: it must create a 6-digit PIN; reopening asks for it; a wrong PIN
   says how many attempts are left; back after more than 5 minutes asks again, after less does not.
3. Five wrong PINs: the session of the phone ends on the server, the data go and the sign-in is shown.
4. The owner closes the phone from «Dispositivos conectados» on the computer: the phone deletes its data at the next
   renewal. A password change does the same. The sign-in on the computer sent «Nuevo inicio de sesión».
5. A phone with screen lock uses the system's own prompt (fingerprint or the phone's code). A professional signed in
   before this version is asked to sign in again to protect the account. A diver switches the lock on in Ajustes.

    python3 tests/navegador/e2e_v50_55_seguridad_app.py [carpeta-de-capturas]
"""
from __future__ import annotations

import json
import sys
import tempfile
import time
from pathlib import Path

sys.path[:0] = [str(Path(__file__).resolve().parent), str(Path(__file__).resolve().parents[1])]
from helpers import ServerTestCase, Server  # noqa: E402
from e2e_markers import chromium  # noqa: E402
from playwright.sync_api import sync_playwright  # noqa: E402

PW = 'buceo-seguro-2026'
UA = 'Mozilla/5.0 (Linux; Android 15; Pixel 8) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/140.0.0.0 Mobile Safari/537.36 WorldivesApp/1.0 pruebas'

# The test double of the native plugin: same methods and answers as SeguridadPlugin.java. Its «phone storage» is a
# separate key of this origin (the real one lives in the Android Keystore and SharedPreferences, out of the WebView).
FAKE = r"""
(() => {
  // WORLDIVES Pruebas opens the test server over plain http (the wifi address): there the WebView has no WebCrypto.
  try { Object.defineProperty(Crypto.prototype, 'subtle', { get: () => undefined, configurable: true }); } catch {}
  const K = '__fake_native_seg', D = '__fake_native_datos';
  const get = () => { try { return JSON.parse(localStorage.getItem(K) || '{}'); } catch { return {}; } };
  const put = (p) => localStorage.setItem(K, JSON.stringify(p));
  let token = null, ultimo = {};
  window.__fake = { seguro: false, bio: 'ok', fuera: -1, renovaciones: 0 };
  const wipe = () => { const p = get(); ultimo = { dispositivo: p.dispositivo || 0, device_key: p.instalacion || null }; token = null;
    for (const k of Object.keys(localStorage)) if (k !== K) localStorage.removeItem(k); sessionStorage.removeItem(D); put({}); return { ok: true, ...ultimo }; };
  const cerrado = (motivo) => ({ ok: false, cerrar: true, motivo, ...ultimo });
  const fallo = () => { const p = get(); p.fallos = (p.fallos || 0) + 1; put(p); if (p.fallos >= 5) { wipe(); return cerrado('fallos'); } return { ok: false, fallos: p.fallos, quedan: 5 - p.fallos }; };
  const Seguridad = {
    async estado() { const p = get(); return { modo: p.modo || null, token: !!p.token, desbloqueado: !!token, fallos: p.fallos || 0, maxFallos: 5, seguro: __fake.seguro, huella: false, dispositivo: p.dispositivo || 0 }; },
    async instalacion() { const p = get(); if (!p.instalacion) { p.instalacion = 'fake-install-' + Math.random().toString(36).slice(2, 14); put(p); } return { device_key: p.instalacion, platform: 'android', model: 'Google Pixel 8', os: '15', app_version: '1.0.99' }; },
    async activar(o) { if (!o.token || o.token.length < 20) throw new Error('Falta el token'); const p = get();
      if (o.modo === 'sistema') { if (!__fake.seguro) throw new Error('sin_bloqueo'); if (__fake.bio !== 'ok') return { ok: false, cancelado: true, fallos: 0 }; }
      if (o.modo === 'pin' && !/^\d{6}$/.test(o.pin || '')) throw new Error('El PIN tiene 6 números');
      Object.assign(p, { modo: o.modo, token: o.token, pin: o.modo === 'pin' ? o.pin : undefined, fallos: 0 }); if (o.dispositivo > 0) p.dispositivo = o.dispositivo; put(p); token = o.token; return { ok: true }; },
    async desbloquear() { const p = get(); if (!p.token) throw new Error('sin_token');
      if (p.modo === 'libre') { token = p.token; return { ok: true }; } if (p.modo === 'pin') throw new Error('usa_pin');
      if (__fake.bio === 'ok') { token = p.token; p.fallos = 0; put(p); return { ok: true }; }
      if (__fake.bio === 'fail') return fallo(); return { ok: false, cancelado: true, fallos: p.fallos || 0 }; },
    async desbloquearPin(o) { const p = get(); if (!p.token) throw new Error('sin_token'); if (o.pin === p.pin) { token = p.token; p.fallos = 0; put(p); return { ok: true }; } return fallo(); },
    async bloquear() { token = null; return { ok: true }; },
    async tiempoFuera() { return { segundos: __fake.fuera }; },
    async renovar() { if (!token) return { ok: false, bloqueado: true }; __fake.renovaciones++;
      const r = await fetch('/api/auth/refresh', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ refresh_token: token }) });
      const d = await r.json().catch(() => ({})); if (r.ok) return { ok: true, status: 200 };
      if (r.status === 401 && d.revoked) { wipe(); return { ok: false, revoked: true, reason: d.reason || 'revoked' }; } return { ok: false, error: d.error }; },
    // the phone's encrypted store (here: sessionStorage, outside the web storage the checks look at)
    async datosLeer() { const p = get(); if (!token && (p.modo === 'sistema' || p.modo === 'pin')) throw new Error('bloqueado');
      const d = JSON.parse(sessionStorage.getItem(D) || '{}'); return { items: Object.fromEntries(Object.entries(d).map(([k, v]) => [k, decodeURIComponent(escape(atob(v)))])) }; },
    async datosGuardar(o) { const p = get(); if (!token && (p.modo === 'sistema' || p.modo === 'pin')) throw new Error('bloqueado');
      const d = JSON.parse(sessionStorage.getItem(D) || '{}'); for (const [k, v] of Object.entries(o.items || {})) { if (v == null) delete d[k]; else d[k] = btoa(unescape(encodeURIComponent(v))); }
      sessionStorage.setItem(D, JSON.stringify(d)); return { ok: true }; },
    async datosBorrar() { sessionStorage.removeItem(D); return { ok: true }; },
    async cambiarModo(o) { if (!token) throw new Error('bloqueado'); const p = get(); return Seguridad.activar({ ...o, token, dispositivo: p.dispositivo }); },
    async borrar(o) { if (o && o.salir) { const p = get(); token = null; sessionStorage.removeItem(D); put({ instalacion: p.instalacion }); return { ok: true }; } return wipe(); },
    async ocultarEnRecientes(o) { window.__fake.recientes = !!o.activo; return { ok: true }; },
  };
  const oyentes = {};
  const App = { addListener(n, f) { (oyentes[n] = oyentes[n] || []).push(f); return { remove() {} }; }, async getInfo() { return { name: 'WORLDIVES Pruebas', version: '1.0', build: '99' }; } };
  window.__fakeResume = async () => { for (const f of oyentes.resume || []) await f(); };
  window.Capacitor = { isNativePlatform: () => true, getPlatform: () => 'android', Plugins: { Seguridad, App } };
  try { localStorage.setItem('wd_cookie_notice', String(Date.now())); } catch {}
})();
"""


def until(pg, expr, timeout=15000):
    """wait_for_function evaluates a string with eval, which the site's CSP refuses: poll with evaluate instead."""
    end = time.time() + timeout / 1000
    while time.time() < end:
        try:
            if pg.evaluate(expr): return True
        except Exception:
            pass
        pg.wait_for_timeout(200)
    raise AssertionError(f'No se cumple a tiempo: {expr}')


def run(shots: Path):
    rows = []

    def check(name, ok, detail=''):
        rows.append((name, bool(ok), detail))
        print(('OK  ' if ok else 'MAL ') + name + ('' if ok else f'  → {detail}'), flush=True)

    ServerTestCase.server = Server().start(); srv = ServerTestCase.server
    errors = []
    try:
        t = ServerTestCase('run')
        admin = t.make_admin()
        diver = t.make_diver('segapp')
        centre = t.make_center(admin, 'segapp')
        srv.sql("UPDATE centers SET plan_code='pro', plan_status='active' WHERE id=?", (centre.user['center_id'],))
        with sync_playwright() as pw:
            browser = chromium(pw)

            def phone():
                ctx = browser.new_context(viewport={'width': 390, 'height': 844}, is_mobile=True, has_touch=True, locale='es-ES', user_agent=UA)
                ctx.add_init_script(FAKE)
                pg = ctx.new_page(); pg.on('pageerror', lambda e: errors.append(str(e)))
                return ctx, pg

            def login(pg, who):
                pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login-form')
                pg.fill('#login', who); pg.fill('#password', PW); pg.click('#login-form button[type=submit]')

            def pin(pg, digits):
                for d in digits: pg.click(f'#wda-bloqueo [data-t="{d}"]')
                pg.wait_for_timeout(250)

            def native(pg):
                return pg.evaluate('Capacitor.Plugins.Seguridad.estado()')

            def last_device(uid):
                r = srv.sql('SELECT * FROM device_sessions WHERE user_id=? ORDER BY id DESC LIMIT 1', (uid,))
                return r[0] if r else {}

            # 1 · diver ------------------------------------------------------------------------------------
            ctx, pg = phone()
            login(pg, 'diver_segapp')
            until(pg, "document.querySelectorAll('.wda-tab').length===5", timeout=15000)
            st = native(pg)
            check('buceador · la app guarda su token de renovación sin bloqueo (opcional para buceadores)', st['token'] and st['modo'] == 'libre', st)
            dev = last_device(diver.user['id'])
            check('buceador · sesión del dispositivo en el servidor (Android, modelo y versión de la app)', dev.get('platform') == 'android' and 'Pixel 8' in (dev.get('model') or '') and dev.get('app_version') == '1.0.99', dev)
            check('buceador · el token no se guarda en el almacenamiento de la web', not pg.evaluate("Object.keys(localStorage).filter(k=>k!=='__fake_native_seg').some(k=>/^[A-Za-z0-9_-]{40,}$/.test(localStorage.getItem(k)||''))"))
            acc = srv.sql('SELECT expires_at-created_at AS ttl FROM sessions WHERE device_id=?', (dev['id'],))
            check('buceador · la sesión de acceso dura 15 minutos', acc and 899 <= acc[0]['ttl'] <= 901, acc)
            items = pg.evaluate("WD.api('/api/account/devices').then(d=>d.items)")
            mine = [x for x in items if x.get('current')]
            check('Dispositivos conectados · este móvil aparece como «Este dispositivo» con tipo y sistema', mine and mine[0]['kind'] == 'app' and 'Android' in (mine[0].get('system') or ''), items)
            # renewal
            ok = pg.evaluate('WD_SEC.renew()')
            check('renovación · el móvil renueva la sesión de 15 minutos con su token', ok is True and pg.evaluate("WD.api('/api/me').then(d=>d.authenticated)"))
            srv.sql('UPDATE sessions SET expires_at=1 WHERE device_id=?', (dev['id'],))
            n0 = pg.evaluate('__fake.renovaciones')
            r = pg.evaluate("WD.api('/api/account/devices').then(d=>d.items.length).catch(e=>'error '+e.message)")
            check('renovación · tras un 401 la app renueva sola y repite la petición', isinstance(r, int) and pg.evaluate('__fake.renovaciones') == n0 + 1, (r, n0))
            # encrypted offline data
            pg.evaluate("localStorage.setItem('wda-pro-dia:2099-01-01:x', JSON.stringify({at:Date.now(), v:{nombre:'Buceadora Secreta Ñandú'}})); localStorage.setItem('wd-sync-queue', JSON.stringify([{id:1,nota:'Cola Secreta'}]))")
            pg.wait_for_timeout(400)
            # what is really on disk: the named properties of localStorage do not go through getItem
            disk = pg.evaluate("(()=>{ const out={}; for (const k of Object.keys(localStorage)) out[k]=localStorage[k]; return out; })()")
            real = list(disk)
            plain = [k for k, v in disk.items() if 'Secreta' in str(v) or k.startswith(('wda-pro-', 'wd-sync-queue', 'wd-day-'))]
            native_keys = pg.evaluate("Object.keys(JSON.parse(sessionStorage.getItem('__fake_native_datos') || '{}'))")
            check('sin conexión · nada de esos datos queda en el almacenamiento de la web', not plain, (real, plain))
            check('sin conexión · los guarda el móvil (cifrados por el plugin)', 'wda-pro-dia:2099-01-01:x' in native_keys and 'wd-sync-queue' in native_keys, native_keys)
            check('sin conexión · la app los lee en claro mientras está abierta', 'Ñandú' in (pg.evaluate("localStorage.getItem('wda-pro-dia:2099-01-01:x')") or ''), disk)
            pg.reload(); until(pg, "document.querySelectorAll('.wda-tab').length===5", timeout=15000); pg.wait_for_timeout(300)
            check('sin conexión · al volver a abrir la app se descifran', 'Cola Secreta' in (pg.evaluate("localStorage.getItem('wd-sync-queue')") or ''))
            pg.evaluate("localStorage.removeItem('wd-sync-queue')")
            # Ajustes: the security section
            pg.goto(srv.base + '/#/ajustes'); pg.wait_for_selector('#wda-seg .lista-fila', timeout=10000)
            txt = pg.inner_text('#wda-seg')
            check('ajustes · sección Seguridad con el bloqueo y «Dispositivos conectados»', 'Bloqueo de la app' in txt and 'Dispositivos conectados' in txt and pg.is_visible('#wda-seg-bloqueo'), txt)
            pg.screenshot(path=str(shots / 'app-ajustes-seguridad-buceador.png'))
            # the diver switches the lock on (phone with screen lock: the system prompt)
            pg.evaluate('__fake.seguro = true')
            pg.click('#wda-seg-bloqueo'); pg.wait_for_timeout(600)
            check('ajustes · el buceador activa el bloqueo (huella o código del móvil)', native(pg)['modo'] == 'sistema', native(pg))
            pg.evaluate('__fake.seguro = false')
            pg.click('#wda-seg-bloqueo'); pg.wait_for_timeout(600)
            check('ajustes · y lo vuelve a quitar', native(pg)['modo'] == 'libre', native(pg))
            # sign out
            pg.goto(srv.base + '/#/ajustes'); pg.wait_for_selector('#wda-salir'); pg.click('#wda-salir'); pg.wait_for_timeout(1200)
            dev = last_device(diver.user['id'])
            left = pg.evaluate("Object.keys(localStorage).filter(k=>k.startsWith('wdenc:')||/^(wd-day-|wd-sync-queue$|wda-pro-|wda-res:|wda-qr-|wda-push$)/.test(k))")
            check('cerrar sesión · la sesión del dispositivo termina en el servidor', dev.get('revoked_reason') == 'logout', dev)
            check('cerrar sesión · el móvil borra el token y los datos guardados', not native(pg)['token'] and not left, (native(pg), left))
            ctx.close()

            # 2 · centre: PIN ------------------------------------------------------------------------------
            ctx, pg = phone()
            login(pg, 'center_segapp')
            pg.wait_for_selector('#wda-bloqueo .wda-teclado', timeout=15000)
            check('centro · sin bloqueo de pantalla en el móvil, la app pide crear un PIN de 6 números', 'Crea tu PIN' in pg.inner_text('#wda-bloqueo'))
            pg.screenshot(path=str(shots / 'app-crear-pin.png'))
            pin(pg, '123456'); pin(pg, '654321')
            check('centro · si los dos PIN no coinciden, vuelve a empezar', 'no coinciden' in pg.inner_text('#wda-bloqueo'))
            pin(pg, '246802'); pin(pg, '246802')
            until(pg, "!document.getElementById('wda-bloqueo')", timeout=10000)
            until(pg, "document.querySelectorAll('.wda-tab').length===5", timeout=15000)
            st = native(pg)
            check('centro · token guardado protegido por el PIN', st['token'] and st['modo'] == 'pin', st)
            check('centro · el panel se oculta en la pantalla de apps recientes', pg.evaluate('__fake.recientes') is True)
            mails = srv.sql("SELECT COUNT(*) AS n FROM email_outbox WHERE template='new_device_login' AND to_email LIKE 'segapp@centro-segapp%'")
            check('correo · «Nuevo inicio de sesión» al entrar desde un móvil que la cuenta no conocía', mails[0]['n'] == 1, mails)
            pg.reload()
            pg.wait_for_selector('#wda-bloqueo .wda-teclado', timeout=15000)
            check('al abrir · la app está bloqueada y pide el PIN antes de enseñar nada', 'WORLDIVES está bloqueada' in pg.inner_text('#wda-bloqueo') and not pg.evaluate("WD.state.me"))
            pg.screenshot(path=str(shots / 'app-bloqueada-pin.png'))
            pin(pg, '000000')
            check('al abrir · un PIN incorrecto dice cuántos intentos quedan', 'Intentos que quedan: 4' in pg.inner_text('#wda-bloqueo'), pg.inner_text('#wda-bloqueo'))
            pg.screenshot(path=str(shots / 'app-pin-incorrecto.png'))
            pin(pg, '246802')
            until(pg, "!document.getElementById('wda-bloqueo') && document.querySelectorAll('.wda-tab').length===5", timeout=15000)
            check('al abrir · con el PIN correcto entra (y se renueva la sesión)', pg.evaluate("WD.state.me && WD.state.me.user.role") == 'center')
            pg.evaluate('__fake.fuera = 299'); pg.evaluate('void __fakeResume()'); pg.wait_for_timeout(500)
            check('segundo plano · menos de 5 minutos: no vuelve a pedirlo', not pg.is_visible('#wda-bloqueo'))
            pg.evaluate('__fake.fuera = 301'); pg.evaluate('void __fakeResume()')
            pg.wait_for_selector('#wda-bloqueo .wda-teclado', timeout=5000)
            check('segundo plano · más de 5 minutos: vuelve a pedirlo', True)
            pin(pg, '246802'); until(pg, "!document.getElementById('wda-bloqueo')", timeout=10000)
            # 3 · five wrong PINs ----------------------------------------------------------------------------
            pg.evaluate("localStorage.setItem('wda-pro-cola', JSON.stringify([{x:'Dato Secreto'}]))"); pg.wait_for_timeout(300)
            pg.reload(); pg.wait_for_selector('#wda-bloqueo .wda-teclado', timeout=15000)
            for _ in range(5): pin(pg, '111111')
            pg.wait_for_timeout(800)
            txt = pg.inner_text('#wda-bloqueo')
            dev = last_device(centre.user['id'])
            check('5 fallos · la app cierra la sesión y lo explica', 'Sesión cerrada' in txt and '5 veces' in txt, txt)
            pg.screenshot(path=str(shots / 'app-cinco-fallos.png'))
            check('5 fallos · la sesión del móvil termina en el servidor', bool(dev.get('revoked_at')) and dev.get('revoked_reason') == 'unlock_failures', dev)
            check('5 fallos · el móvil borra token y datos', not native(pg)['token'] and not [k for k in pg.evaluate('Object.keys(localStorage)') if k != '__fake_native_seg'])
            check('5 fallos · ya no hay sesión', pg.evaluate("fetch('/api/me').then(r=>r.json()).then(d=>d.authenticated)") is False)
            pg.click('#wda-bloqueo-entrar'); pg.wait_for_timeout(500)
            check('5 fallos · «Entrar con mi contraseña» lleva al acceso', '#/login' in pg.url and not pg.is_visible('#wda-bloqueo'))
            ctx.close()

            # 4 · closed from the computer, password change ----------------------------------------------------
            ctx, pg = phone()
            login(pg, 'center_segapp'); pg.wait_for_selector('#wda-bloqueo .wda-teclado', timeout=15000)
            pin(pg, '135790'); pin(pg, '135790'); until(pg, "document.querySelectorAll('.wda-tab').length===5", timeout=15000)
            desk = browser.new_context(viewport={'width': 1366, 'height': 900}, locale='es-ES'); dp = desk.new_page(); dp.on('pageerror', lambda e: errors.append(str(e)))
            dp.add_init_script("try{localStorage.setItem('wd_cookie_notice',String(Date.now()))}catch(e){}")
            dp.goto(srv.base + '/#/login'); dp.fill('#login', 'center_segapp'); dp.fill('#password', PW); dp.click('#login-form button[type=submit]'); dp.wait_for_timeout(1500)
            dp.goto(srv.base + '/#/cuenta?dispositivos=1'); dp.wait_for_selector('#acc-sessions-list [data-close-dev]', timeout=15000)
            listing = dp.inner_text('#acc-sessions-list')
            check('ordenador · «Dispositivos conectados» lista el móvil (tipo, sistema, última actividad)', 'Pixel 8' in listing and 'Android' in listing and 'Última actividad' in listing, listing)
            dp.locator('#acc-sessions').screenshot(path=str(shots / 'web-dispositivos-conectados.png'))
            app_btn = dp.evaluate("[...document.querySelectorAll('[data-close-dev]')].map(b=>b.dataset.closeDev).find(x=>x.startsWith('a:'))")
            dp.click(f'[data-close-dev="{app_btn}"]'); dp.wait_for_selector('#wd-confirm-ok', timeout=5000)
            dp.click('#wd-confirm-ok'); dp.wait_for_timeout(1200)
            dev = last_device(centre.user['id'])
            check('ordenador · «Cerrar sesión» en el móvil lo anula en el servidor', dev.get('revoked_reason') == 'closed_by_owner', dev)
            ok = pg.evaluate('WD_SEC.renew()'); pg.wait_for_timeout(600)
            txt = pg.inner_text('#wda-bloqueo') if pg.is_visible('#wda-bloqueo') else ''
            check('móvil · en la siguiente renovación sale, borra sus datos y lo explica', ok is False and 'Sesión cerrada' in txt and 'Dispositivos conectados' in txt and not native(pg)['token'], (ok, txt, native(pg)))
            pg.screenshot(path=str(shots / 'app-cerrada-a-distancia.png'))
            # password change closes the phone too
            pg.click('#wda-bloqueo-entrar'); pg.wait_for_timeout(300)
            login(pg, 'center_segapp'); pg.wait_for_selector('#wda-bloqueo .wda-teclado', timeout=15000)
            pin(pg, '135790'); pin(pg, '135790'); until(pg, "document.querySelectorAll('.wda-tab').length===5", timeout=15000)
            r = dp.evaluate("""fetch('/api/account/password',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({current_password:%s,new_password:'otra-clave-segura-2026'})}).then(r=>r.status)""" % json.dumps(PW))
            dev = last_device(centre.user['id'])
            ok = pg.evaluate('WD_SEC.renew()')
            check('contraseña · cambiarla en el ordenador cierra la sesión del móvil', r == 200 and bool(dev.get('revoked_at')) and ok is False and not native(pg)['token'], (r, dev, ok))
            desk.close(); ctx.close()

            # 5 · phone with screen lock, old session, team ------------------------------------------------------
            ctx, pg = phone()
            pg.goto(srv.base + '/#/login'); pg.wait_for_selector('#login-form'); pg.evaluate('__fake.seguro = true')
            pg.fill('#login', 'center_segapp'); pg.fill('#password', 'otra-clave-segura-2026'); pg.click('#login-form button[type=submit]')
            until(pg, "document.querySelectorAll('.wda-tab').length===5", timeout=15000)
            check('con bloqueo de pantalla · usa la huella o el código del móvil (sin PIN propio)', native(pg)['modo'] == 'sistema', native(pg))
            pg.evaluate('__fake.bio = "cancel"'); pg.reload(); pg.wait_for_selector('#wda-desbloquear', timeout=15000)
            check('con bloqueo de pantalla · al abrir, el botón «Desbloquear» llama al sistema', 'Desbloquéala con tu huella' in pg.inner_text('#wda-bloqueo'))
            pg.screenshot(path=str(shots / 'app-bloqueada-huella.png'))
            pg.evaluate('__fake.bio = "ok"'); pg.click('#wda-desbloquear')
            until(pg, "!document.getElementById('wda-bloqueo') && document.querySelectorAll('.wda-tab').length===5", timeout=15000)
            check('con bloqueo de pantalla · desbloqueada con la huella', pg.evaluate("WD.state.me && WD.state.me.user.role") == 'center')
            ctx.close()
            ctx, pg = phone()
            pg.goto(srv.base + '/'); pg.wait_for_timeout(800)
            pg.evaluate("""fetch('/api/auth/login',{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({login:'center_segapp',password:'otra-clave-segura-2026'})})""")
            pg.reload(); pg.wait_for_selector('#wda-proteger', timeout=15000)
            check('versión anterior · un profesional sin token protegido tiene que volver a entrar', 'Protege tu cuenta' in pg.inner_text('#wda-bloqueo'))
            pg.screenshot(path=str(shots / 'app-proteger-cuenta.png'))
            ctx.close()
            check('sin errores de JavaScript', not errors, errors)
    finally:
        srv.stop()
    bad = [r for r in rows if not r[1]]
    print(f'\n{len(rows) - len(bad)}/{len(rows)} comprobaciones correctas · capturas en {shots}')
    return 1 if bad else 0


if __name__ == '__main__':
    out = Path(sys.argv[1]) if len(sys.argv) > 1 else Path(tempfile.mkdtemp(prefix='wod-seg-app-'))
    out.mkdir(parents=True, exist_ok=True)
    sys.exit(run(out))
