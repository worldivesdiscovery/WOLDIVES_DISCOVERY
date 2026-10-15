/* WORLDIVES · modo app · seguridad (v50.55, encargo 2 «Seguridad de la app WORLDIVES PRO»).
   Only inside the native app (Capacitor, plugin «Seguridad»: movil/android/.../SeguridadPlugin.java). In a browser,
   even with «?app=1», this file does nothing.

   - Unlock with the phone's own biometrics (fingerprint, or face when the phone counts it as strong) or the phone's
     code; without any screen lock, a 6-digit PIN of the app. The fingerprint never leaves the phone: the system only
     answers yes or no, and the device's refresh token lives in the Android Keystore protected by that unlock.
   - Asked when the app opens and when it comes back after 5 minutes in the background. On by default (and always on)
     for centres and freelance professionals; optional for divers (Ajustes).
   - 5 failed attempts: the session of this phone ends, its data are deleted and the password is asked again.
   - The access session lasts 15 minutes and is renewed by the phone with its refresh token. The page holds that token
     only for the instant it hands it to the phone after signing in; it is never written to the web storage.
     If the server revoked the device (closed from «Dispositivos conectados», a password change, the owner of the
     centre…), the phone deletes its data and shows the sign-in.
   - Offline data (the boat list, today's bookings, the QR codes…) are kept by the phone, encrypted (AES-GCM, key in
     the Keystore), and deleted after 7 days, when signing out and when the device is revoked. The rest of the app
     keeps using localStorage as before: the protected keys live decrypted only in memory, never in the web storage.
   - The panel is hidden in the recent apps screen. */
(() => {
  'use strict';
  const W = window.WD;
  if (!W || !W.app || !W.app.native) return;
  const S = window.Capacitor?.Plugins?.Seguridad;
  if (!S) return;   // an older app without the plugin: everything as before
  const APP = W.app, T = (s) => W.translateString(s), esc = W.escapeHtml;
  const PRO = (role) => ['center', 'freelance', 'admin'].includes(role);
  const UMBRAL = 300;   // seconds in the background before asking again (the brief: 5 minutes)
  const umbral = () => {
    if (APP.pruebas) { try { const v = Number(localStorage.getItem('wda-seg-umbral')); if (v >= 5) return v; } catch { /* default */ } }
    return UMBRAL;
  };
  const RENUEVA_MS = 12 * 60e3;   // renew before the 15 minutes of the access session end
  const PROTEGIDAS = /^(wd-day-|wd-sync-queue$|wda-pro-|wda-res:|wda-qr-|wda-push$)/;
  const SIETE_DIAS = 7 * 86400e3;

  /* ---------------------------------------------------------------- encrypted offline data */
  // The phone keeps them (plugin «Seguridad»: AES-GCM with a Keystore key that never reaches this page); here they live
  // decrypted only in memory. Old copies kept in clear by an earlier version are moved there and deleted from the web.
  const proto = Storage.prototype, orig = { get: proto.getItem, set: proto.setItem, del: proto.removeItem };
  const cache = new Map();
  let listos = false;   // the data were read from the phone (not while locked)
  const local = (st) => { try { return st === window.localStorage; } catch { return false; } };
  const realKeys = () => { try { return Object.keys(window.localStorage); } catch { return []; } };
  proto.getItem = function (k) {
    if (local(this) && PROTEGIDAS.test(String(k))) { const v = cache.get(String(k)); return v === undefined ? null : v.v; }
    return orig.get.call(this, k);
  };
  proto.setItem = function (k, v) {
    if (local(this) && PROTEGIDAS.test(String(k))) { cache.set(String(k), { v: String(v), at: Date.now() }); persistir(String(k)); return; }
    return orig.set.call(this, k, v);
  };
  proto.removeItem = function (k) {
    if (local(this) && PROTEGIDAS.test(String(k))) { cache.delete(String(k)); persistir(String(k)); return; }
    return orig.del.call(this, k);
  };
  const pendientes = new Set(); let tPersistir = 0;
  function persistir(k) {
    if (k) pendientes.add(k);
    clearTimeout(tPersistir);
    tPersistir = setTimeout(async () => {
      if (!listos || !pendientes.size) return;   // locked: kept in memory until the app is unlocked
      const items = {};
      for (const key of pendientes) { const e = cache.get(key); items[key] = e ? JSON.stringify(e) : null; }
      pendientes.clear();
      try { await S.datosGuardar({ items }); } catch { Object.keys(items).forEach((x) => pendientes.add(x)); }   // tried again
    }, 80);
  }
  async function cargarDatos() {
    let r; try { r = await S.datosLeer(); } catch { return false; }
    const ahora = Date.now();
    for (const [key, txt] of Object.entries(r.items || {})) {
      let e = null; try { e = JSON.parse(txt); } catch { /* unreadable */ }
      if (!e || ahora - (e.at || 0) > SIETE_DIAS) { pendientes.add(key); continue; }   // deleted after 7 days
      if (!cache.has(key)) cache.set(key, e);
    }
    for (const k of realKeys()) {
      if (k.startsWith('wdenc:')) { try { orig.del.call(window.localStorage, k); } catch { /* nothing */ } continue; }
      if (PROTEGIDAS.test(k)) {
        if (!cache.has(k)) cache.set(k, { v: orig.get.call(window.localStorage, k), at: ahora });
        try { orig.del.call(window.localStorage, k); } catch { /* nothing */ }
        pendientes.add(k);
      }
    }
    listos = true;
    persistir();
    return true;
  }
  function olvidarDatos() {
    cache.clear(); pendientes.clear(); listos = false;
    for (const k of realKeys()) if (k.startsWith('wdenc:') || PROTEGIDAS.test(k)) { try { orig.del.call(window.localStorage, k); } catch { /* nothing */ } }
    S.datosBorrar?.().catch(() => {});
  }
  setInterval(() => { const ahora = Date.now(); for (const [k, e] of cache) if (ahora - (e.at || 0) > SIETE_DIAS) { cache.delete(k); persistir(k); } }, 3600e3);

  /* ---------------------------------------------------------------- the lock screen */
  let desbloqueada = false, abierto = null;
  function capa(html) {
    let el = document.getElementById('wda-bloqueo');
    if (!el) { el = document.createElement('div'); el.id = 'wda-bloqueo'; el.className = 'wda'; el.setAttribute('role', 'dialog'); el.setAttribute('aria-modal', 'true'); document.body.appendChild(el); }
    el.innerHTML = `<div class="wda-bloqueo-in"><img src="/img/marca/worldives-icono-192.png" alt="" width="72" height="72">${html}</div>`;
    document.documentElement.classList.add('wda-bloqueada');
    return el;
  }
  function quitarCapa() { document.getElementById('wda-bloqueo')?.remove(); document.documentElement.classList.remove('wda-bloqueada'); }
  const teclado = () => `<div class="wda-pin" aria-live="polite"><span></span><span></span><span></span><span></span><span></span><span></span></div>
    <div class="wda-teclado">${[1, 2, 3, 4, 5, 6, 7, 8, 9, '', 0, '⌫'].map((n) => n === '' ? '<span></span>' : `<button type="button" data-t="${n}" aria-label="${n === '⌫' ? esc(T('Borrar')) : n}">${n}</button>`).join('')}</div>`;
  function leerPin(el, alCompletar) {
    let pin = '';
    const pinta = () => el.querySelectorAll('.wda-pin span').forEach((s, i) => s.classList.toggle('lleno', i < pin.length));
    el.querySelectorAll('[data-t]').forEach((b) => { b.onclick = async () => {
      const t = b.dataset.t;
      if (t === '⌫') pin = pin.slice(0, -1); else if (pin.length < 6) pin += t;
      pinta();
      if (pin.length === 6) { const p = pin; pin = ''; await alCompletar(p); pinta(); }
    }; });
    pinta();
  }

  /** Shows the lock and resolves when the app is unlocked (or the session ended: then false). */
  function pantallaBloqueo(st) {
    if (abierto) return abierto;
    abierto = new Promise((listo) => {
      const fin = (ok) => { abierto = null; if (ok) { desbloqueada = true; quitarCapa(); } listo(ok); };
      const msg = (txt, cls = '') => { const m = document.getElementById('wda-bloqueo-msg'); if (m) { m.textContent = txt; m.className = 'wda-bloqueo-msg ' + cls; } };
      const tras = async (r) => {
        if (r?.ok) { await cargarDatos(); fin(true); return; }
        if (r?.cerrar) { await sesionTerminada(r, 'fallos'); fin(false); return; }
        if (r?.reintentar) msg(T('Usa tu huella o el código del móvil: el desbloqueo facial de este móvil no basta.'), 'aviso');
        else if (r?.quedan != null) msg(`${T('PIN incorrecto.')} ${T('Intentos que quedan')}: ${r.quedan}`, 'error');
        else if (r?.cancelado && r.fallos) msg(`${T('Intentos fallidos')}: ${r.fallos} / 5`, 'aviso');
      };
      const salir = `<button type="button" class="wda-bloqueo-salir" id="wda-bloqueo-salir">${esc(T('Cerrar sesión en este móvil'))}</button>`;
      if (st.modo === 'pin') {
        const el = capa(`<h1>${esc(T('WORLDIVES está bloqueada'))}</h1><p>${esc(T('Escribe tu PIN de la app.'))}</p>${teclado()}<p id="wda-bloqueo-msg" class="wda-bloqueo-msg" role="status"></p>${salir}`);
        leerPin(el, async (pin) => tras(await S.desbloquearPin({ pin }).catch(() => null)));
      } else {
        const el = capa(`<h1>${esc(T('WORLDIVES está bloqueada'))}</h1><p>${esc(T('Desbloquéala con tu huella o con el código del móvil.'))}</p>
          <button type="button" class="wbtn ancho grande" id="wda-desbloquear">${esc(T('Desbloquear'))}</button><p id="wda-bloqueo-msg" class="wda-bloqueo-msg" role="status"></p>${salir}`);
        const pedir = async () => tras(await S.desbloquear({ titulo: T('Desbloquear WORLDIVES'), subtitulo: T('Huella, cara o el código del móvil') }).catch(() => null));
        el.querySelector('#wda-desbloquear').onclick = pedir;
        setTimeout(pedir, 250);
      }
      // Two taps (the lock covers everything, so no dialog over it): the first one says what happens.
      const bs = document.getElementById('wda-bloqueo-salir');
      bs.onclick = async () => {
        if (!bs.dataset.seguro) { bs.dataset.seguro = '1'; bs.textContent = T('Toca otra vez: se cierra la sesión y se borran los datos de este móvil'); return; }
        const r = await S.borrar().catch(() => ({}));
        await sesionTerminada(r, 'logout'); fin(false);
      };
    });
    return abierto;
  }

  /** The session of this phone ended (5 failures, revoked by the server, signing out): data deleted, sign-in shown. */
  async function sesionTerminada(r, motivo) {
    if (r?.dispositivo && r?.device_key) {
      fetch('/api/auth/device/forget', { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin',
        body: JSON.stringify({ device_id: r.dispositivo, device_key: r.device_key, reason: motivo === 'fallos' ? 'unlock_failures' : motivo }) }).catch(() => {});
    }
    olvidarDatos(); try { window.wdForgetDevice?.(); } catch { /* nothing */ }
    desbloqueada = false; W.state.me = null;
    const texto = { fallos: 'Has fallado 5 veces. Por seguridad hemos cerrado la sesión y borrado los datos guardados en este móvil.',
      revocado: 'Tu sesión en este móvil se ha cerrado (desde «Dispositivos conectados», por un cambio de contraseña o por el titular del centro). Hemos borrado los datos guardados en el móvil.',
      caducado: 'Han pasado 30 días desde que entraste en este móvil: vuelve a entrar con tu contraseña.',
      logout: 'Has cerrado la sesión en este móvil.' }[motivo] || 'Tu sesión en este móvil ha terminado.';
    const el = capa(`<h1>${esc(T('Sesión cerrada'))}</h1><p>${esc(T(texto))}</p><a class="wbtn ancho grande" href="#/login" id="wda-bloqueo-entrar">${esc(T('Entrar con mi contraseña'))}</a>`);
    el.querySelector('#wda-bloqueo-entrar').onclick = () => { quitarCapa(); };
    try { await W.loadMe(); } catch { /* nothing */ }
  }

  /* ---------------------------------------------------------------- the 15-minute access session */
  let renovando = null, tRenovar = 0;
  async function renovar() {
    if (renovando) return renovando;
    renovando = (async () => {
      const r = await S.renovar({ ua: navigator.userAgent }).catch(() => ({ ok: false }));
      if (r.ok) { programar(); return true; }
      if (r.revoked) { await sesionTerminada(r, r.reason === 'expired' ? 'caducado' : 'revocado'); return false; }
      return false;   // no network or locked: the app keeps working with what it has
    })();
    try { return await renovando; } finally { renovando = null; }
  }
  function programar() { clearTimeout(tRenovar); tRenovar = setTimeout(() => { if (desbloqueada && document.visibilityState === 'visible') renovar(); else programar(); }, RENUEVA_MS); }

  /* ---------------------------------------------------------------- after signing in */
  async function extraLogin() {
    try { return { app_device: await S.instalacion() }; } catch { return {}; }
  }
  /** Keeps the device's refresh token protected (PRO: always; divers: as they chose in Ajustes, by default no lock). */
  async function trasLogin(r) {
    if (!r?.refresh_token) return;
    const st = await S.estado();
    let modo = 'libre';
    let quiereBloqueo = false; try { quiereBloqueo = localStorage.getItem('wda-seg-bloqueo') === '1'; } catch { /* nothing */ }
    if (PRO(r.role) || quiereBloqueo) modo = st.seguro ? 'sistema' : 'pin';
    let res = null;
    if (modo === 'sistema') {
      for (let i = 0; i < 3 && !res?.ok; i++) {
        res = await S.activar({ token: r.refresh_token, dispositivo: r.device_id, modo, titulo: T('Protege WORLDIVES'), subtitulo: T('Confirma con tu huella o con el código del móvil') }).catch((e) => ({ error: e?.message }));
        if (!res?.ok && !await W.wdConfirm({ title: T('Protege tu cuenta'), text: T('Las cuentas profesionales se abren con tu huella o con el código del móvil. Vuelve a intentarlo.'), ok: T('Intentar de nuevo') })) break;
      }
    } else if (modo === 'pin') {
      res = await crearPin(r);
    } else {
      res = await S.activar({ token: r.refresh_token, dispositivo: r.device_id, modo: 'libre' }).catch(() => null);
    }
    if (!res?.ok) {
      // without protecting the token, this phone does not keep the session
      await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: '{}' }).catch(() => {});
      await S.borrar().catch(() => {});
      throw new Error(T('Sin desbloqueo no se puede usar la cuenta profesional en este móvil.'));
    }
    desbloqueada = true; programar();
    await cargarDatos();
    if (PRO(r.role) || modo !== 'libre') S.ocultarEnRecientes({ activo: true }).catch(() => {});
  }
  function crearPin(r) {
    return new Promise((listo) => {
      let primero = '';
      const el = capa(`<h1>${esc(T('Crea tu PIN de la app'))}</h1><p>${esc(T('Este móvil no tiene bloqueo de pantalla: WORLDIVES se abrirá con un PIN de 6 números. No lo compartas.'))}</p>${teclado()}<p id="wda-bloqueo-msg" class="wda-bloqueo-msg" role="status"></p>`);
      const msg = (t, c = '') => { const m = el.querySelector('#wda-bloqueo-msg'); m.textContent = t; m.className = 'wda-bloqueo-msg ' + c; };
      leerPin(el, async (pin) => {
        if (!primero) { primero = pin; el.querySelector('h1').textContent = T('Repite el PIN'); msg(''); return; }
        if (pin !== primero) { primero = ''; el.querySelector('h1').textContent = T('Crea tu PIN de la app'); msg(T('Los dos PIN no coinciden. Empieza de nuevo.'), 'error'); return; }
        const res = await S.activar({ token: r.refresh_token, dispositivo: r.device_id, modo: 'pin', pin }).catch(() => null);
        quitarCapa(); listo(res);
      });
    });
  }

  /* ---------------------------------------------------------------- opening and coming back */
  async function inicio() {
    let st; try { st = await S.estado(); } catch { return; }
    if (!st.token) { await cargarDatos(); return; }   // not signed in on this phone with the new system yet
    if (st.modo === 'libre') {
      const r = await S.desbloquear({}).catch(() => null);
      if (r?.cerrar) { await sesionTerminada(r, 'fallos'); return; }
      desbloqueada = !!r?.ok; await cargarDatos();
    } else {
      S.ocultarEnRecientes({ activo: true }).catch(() => {});
      if (!await pantallaBloqueo(st)) return;
    }
    await renovar();
  }
  /** After /api/me: a professional signed in on this phone without the protected token signs in again (once). */
  async function revisar() {
    const me = W.state.me; if (!me || !PRO(me.user?.role)) return;
    const st = await S.estado().catch(() => null); if (!st || st.token) return;
    const el = capa(`<h1>${esc(T('Protege tu cuenta'))}</h1><p>${esc(T('Desde esta versión, la app de los centros y los profesionales se abre con tu huella o con un PIN. Vuelve a entrar con tu contraseña para activarlo.'))}</p>
      <button type="button" class="wbtn ancho grande" id="wda-proteger">${esc(T('Entrar de nuevo'))}</button>`);
    el.querySelector('#wda-proteger').onclick = async () => {
      await fetch('/api/auth/logout', { method: 'POST', credentials: 'same-origin', headers: { 'Content-Type': 'application/json' }, body: '{}' }).catch(() => {});
      W.state.me = null; quitarCapa(); location.hash = '#/login'; await W.loadMe();
    };
  }
  const App = window.Capacitor?.Plugins?.App;
  App?.addListener?.('resume', async () => {
    const st = await S.estado().catch(() => null); if (!st?.token) return;
    if (st.modo !== 'libre' && !abierto) {
      const { segundos } = await S.tiempoFuera().catch(() => ({ segundos: -1 }));
      if (segundos >= umbral()) {
        desbloqueada = false; await S.bloquear().catch(() => {});
        if (!await pantallaBloqueo(st)) return;
      }
    }
    if (desbloqueada) renovar();
  });

  /* ---------------------------------------------------------------- Ajustes */
  async function estado() { const st = await S.estado().catch(() => null); return st ? { ...st, umbral: umbral() } : null; }
  /** Divers: switch the lock on or off (the token is saved again with the new protection). */
  async function cambiarBloqueo(activo) {
    const st = await S.estado();
    try { localStorage.setItem('wda-seg-bloqueo', activo ? '1' : '0'); } catch { /* nothing */ }
    if (!st.token) return { ok: true, sinToken: true };
    if (!activo) return S.cambiarModo({ modo: 'libre' });
    if (st.seguro) return S.cambiarModo({ modo: 'sistema', titulo: T('Protege WORLDIVES'), subtitulo: T('Confirma con tu huella o con el código del móvil') });
    return new Promise((listo) => {
      let primero = '';
      const el = capa(`<h1>${esc(T('Crea tu PIN de la app'))}</h1><p>${esc(T('Este móvil no tiene bloqueo de pantalla: WORLDIVES se abrirá con un PIN de 6 números. No lo compartas.'))}</p>${teclado()}<p id="wda-bloqueo-msg" class="wda-bloqueo-msg" role="status"></p>`);
      leerPin(el, async (pin) => {
        if (!primero) { primero = pin; el.querySelector('h1').textContent = T('Repite el PIN'); return; }
        if (pin !== primero) { primero = ''; el.querySelector('h1').textContent = T('Crea tu PIN de la app'); return; }
        const r = await S.cambiarModo({ modo: 'pin', pin }).catch(() => null); quitarCapa(); listo(r);
      });
    });
  }
  /** Signing out: the device session ends on the server too (even if the 15 minutes had passed), and the token, the keys
   *  and the offline data go; the theme and the language stay. */
  async function olvidar(motivo = 'logout') {
    const [st, ins] = await Promise.all([S.estado().catch(() => null), S.instalacion().catch(() => null)]);
    if (st?.dispositivo && ins?.device_key) {
      await fetch('/api/auth/device/forget', { method: 'POST', headers: { 'Content-Type': 'application/json' }, credentials: 'same-origin',
        body: JSON.stringify({ device_id: st.dispositivo, device_key: ins.device_key, reason: motivo }) }).catch(() => {});
    }
    olvidarDatos(); desbloqueada = false; clearTimeout(tRenovar);
    return S.borrar({ salir: true }).catch(() => null);
  }

  window.WD_SEC = { inicio, revisar, extraLogin, trasLogin, renovar: () => renovar(), renew: () => renovar(), estado, cambiarBloqueo, olvidar,
    keys: () => [...realKeys().filter((k) => !PROTEGIDAS.test(k)), ...cache.keys()], umbral, PRO };
})();
