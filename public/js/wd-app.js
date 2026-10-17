/* WORLDIVES · modo app (v50.48, encargo «App móvil en 3 módulos», Tanda 1).
   The app WORLDIVES (com.worldives.app) and WORLDIVES Pruebas (com.worldives.app.pruebas) show this same web inside a
   native shell (Capacitor, movil/). world-dives-v8.js loads this file only there (or with «?app=1» in a browser) and
   gives it its helpers in window.WD. Nothing here changes the normal web.

   - Shell: bottom tabs per module, Android back button, themes Clásico / Noche / Automático and text Normal / Grande /
     Enorme (this phone only), the band of WORLDIVES Pruebas with «Reportar fallo».
   - Buceador: Inicio (next dive, «Salidas con plazas cerca de ti», Repetir), Explorar (full-screen map with a sheet of
     three heights and a card synced with the markers), Buscar, fichas with Llamar · WhatsApp · Cómo llegar · Compartir
     and the fixed «Desde X € · Reservar» bar, quick booking in a sheet, Reservas, Buddies (v50.57: the QR and the
     buddies of the Log Book; groups still pending), Mi área and Ajustes.
   - Visitante: Inicio, Explorar and Entrar; booking asks for the session at the end.
   - Centro PRO and Freelance PRO (v50.49, Tandas 2 to 4) live in wd-app-pro.js, downloaded only by centres and
     freelance professionals; the web panel still opens inside the app for what is «Disponible en la web».
   Payments: Stripe Checkout opens in a browser tab (Google Pay works there) and comes back to the app by its link
   scheme (com.worldives.app://pago?…), see app/wod/movil.py. Only data the server already has: nothing is invented. */
(() => {
  'use strict';
  const W = window.WD;
  if (!W || !W.app) return;
  const { $, $$, api, postJSON, state } = W;
  const esc = W.escapeHtml;
  const T = (s) => W.translateString(s);
  const APP = W.app;
  const plugin = (name) => (APP.native && window.Capacitor?.Plugins?.[name]) || null;

  /* ---------------------------------------------------------------- icons: stroke SVG, 24 px grid (as the prototype) */
  const I = {
    inicio: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h5v-6h4v6h5V9.5"/>',
    explorar: '<path d="M9 4 3 6.5v13.5L9 17.5l6 2.5 6-2.5V4l-6 2.5z"/><path d="M9 4v13.5M15 6.5V20"/>',
    reservas: '<path d="M3 8a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-2a2 2 0 0 0 0-4z"/><path d="M13 6v2M13 11v2M13 16v2"/>',
    buddies: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><circle cx="17" cy="9" r="2.8"/><path d="M16.5 14.2a5 5 0 0 1 5 5"/>',
    area: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    hoy: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/>',
    agenda: '<rect x="3" y="5" width="18" height="16" rx="2.5"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    entrar: '<path d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4"/><path d="M10 16l4-4-4-4M14 12H4"/>',
    escanear: '<path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3"/><path d="M7 12h10"/>',
    solicitudes: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    mas: '<circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/>',
    mover: '<path d="M4 8h14l-3-3M20 16H6l3 3"/>',
    lapiz: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>',
    linterna: '<path d="M8 3h8v4l-2 3v11h-4V10L8 7z"/><path d="M8 7h8"/>',
    teclado: '<rect x="2" y="6" width="20" height="13" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M7 15h10"/>',
    graficas: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    cartel: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    equipo: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M19 8v6M16 11h6"/>',
    resena: '<path d="M4 5h16v11H9l-5 4z"/><path d="m12 7.5.9 1.9 2 .3-1.4 1.4.3 2-1.8-1-1.8 1 .3-2-1.4-1.4 2-.3z"/>',
    descargar: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
    bloquear: '<circle cx="12" cy="12" r="9"/><path d="m5.6 5.6 12.8 12.8"/>',
    copiar: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>',
    atras: '<path d="m15 6-6 6 6 6"/>',
    buscar: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    ubicacion: '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    capas: '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
    lista: '<path d="M8 6h13M8 12h13M8 18h13"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/>',
    mapa: '<path d="M9 4 3 6.5v13.5L9 17.5l6 2.5 6-2.5V4l-6 2.5z"/><path d="M9 4v13.5M15 6.5V20"/>',
    reloj: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    pin: '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    mas1: '<path d="M12 5v14M5 12h14"/>',
    menos: '<path d="M5 12h14"/>',
    chev: '<path d="m9 6 6 6-6 6"/>',
    tel: '<path d="M5 4h3.5l1.5 4.5-2.2 1.4a11 11 0 0 0 6.3 6.3l1.4-2.2L20 15.5V19a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
    wa: '<path d="M4 20l1.3-4.2A8.5 8.5 0 1 1 8.4 19z"/><path d="M9 9.2c.2 2.6 2.4 4.9 5 5.2l1.2-1.2-1.8-.9-.8.8c-.9-.4-1.7-1.2-2.1-2.1l.8-.8-.9-1.8z"/>',
    ruta: '<path d="M3 11 21 3l-8 18-2-8z"/>',
    compartir: '<circle cx="18" cy="5" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="19" r="2.5"/><path d="m8.2 10.8 7.6-4.6M8.2 13.2l7.6 4.6"/>',
    alerta: '<path d="M12 3 2 20h20z"/><path d="M12 10v4.5M12 17.5v.01"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5v.01"/>',
    barco: '<path d="M3 15h18l-2.5 5h-13z"/><path d="M6 15V9h12v6M12 9V4M9 6h3"/>',
    camara: '<path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"/><circle cx="12" cy="13.5" r="3.5"/>',
    qr: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h3v3h-3zM20 14v.01M14 20h.01M17 20h4v-3"/>',
    cobrar: '<rect x="2.5" y="5" width="19" height="14" rx="2.5"/><path d="M2.5 10h19M6 15h4"/>',
    ficha: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><circle cx="9" cy="11" r="2.2"/><path d="M5.5 16.5a3.5 3.5 0 0 1 7 0M14.5 10h4M14.5 13.5h3"/>',
    papelera: '<path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14"/>',
    ajustes: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    idioma: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    avisos: '<path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    salir: '<path d="M10 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4"/><path d="M14 16l4-4-4-4M18 12H9"/>',
    documento: '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
    libro: '<path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H20v15H5.5A1.5 1.5 0 0 0 4 19.5z"/><path d="M4 19.5A1.5 1.5 0 0 0 5.5 21H20v-3"/>',
    regalo: '<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M5 12v9h14v-9M12 8v13M12 8S10.5 3 8 4.5 9.5 8 12 8zM12 8s1.5-5 4-3.5S14.5 8 12 8z"/>',
    puntos: '<circle cx="12" cy="9" r="6"/><path d="m8.5 14-1.5 7 5-2.5 5 2.5-1.5-7"/>',
    web: '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    candado: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    bug: '<rect x="7" y="8" width="10" height="12" rx="5"/><path d="M12 8v12M9 5l1.5 3M15 5l-1.5 3M3 12h4M17 12h4M4 18l3-2M20 18l-3-2M4 7l3 2M20 7l-3 2"/>',
    tienda: '<path d="M4 9.5 5.5 4h13L20 9.5M4 9.5V20h16V9.5M4 9.5a2.7 2.7 0 0 0 5.3 0 2.7 2.7 0 0 0 5.4 0 2.7 2.7 0 0 0 5.3 0"/><path d="M10 20v-5h4v5"/>',
    servidor: '<rect x="3" y="4" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><path d="M7 7.5h.01M7 16.5h.01"/>',
    ola2: '<path d="M2 12c2.5 0 2.5-3 5-3s2.5 3 5 3 2.5-3 5-3 2.5 3 5 3"/>',
    sobre: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    tanque: '<rect x="8" y="6" width="8" height="15" rx="4"/><path d="M10 6V3.5h4V6M12 3.5V2"/>',
    tema: '<circle cx="12" cy="12" r="9"/><path d="M12 3v18a9 9 0 0 0 0-18z" fill="currentColor"/>',
    texto: '<path d="M4 7V5h10v2M9 5v14M7 19h4M14 12v-1.5h6V12M17 10.5V19M15.5 19h3"/>',
  };
  const ic = (n, cls = 'ic') => `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${I[n] || ''}</svg>`;

  /* ---------------------------------------------------------------- this phone's conveniences (theme and text size) */
  const TEMAS = ['clasico', 'noche', 'auto'], TAMANOS = ['normal', 'grande', 'enorme'];
  const pref = (k, def, ok) => { try { const v = localStorage.getItem('wda-' + k); return ok.includes(v) ? v : def; } catch { return def; } };
  const guardarPref = (k, v) => { try { localStorage.setItem('wda-' + k, v); } catch { /* without storage: just this time */ } };
  // Very soft bathymetry lines for the headers (as the prototype).
  function bati(color) {
    let p = '';
    for (let k = 0; k < 6; k++) {
      let d = `M -10 ${20 + k * 28}`;
      for (let x = 0; x <= 380; x += 20) d += ` L ${x} ${(20 + k * 28 + Math.sin(x / 47 + k) * 9 + Math.cos(x / 23 + k * 2) * 4).toFixed(1)}`;
      p += `<path d='${d}' fill='none' stroke='${color}' stroke-width='1.2'/>`;
    }
    return `url("data:image/svg+xml,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='360' height='180'>${p}</svg>`)}")`;
  }
  const oscuro = () => { const t = document.documentElement.dataset.wdaTema; return t === 'noche' || (t === 'auto' && matchMedia('(prefers-color-scheme: dark)').matches); };
  function aplicarAspecto() {
    const h = document.documentElement;
    h.dataset.wdaTema = pref('tema', 'clasico', TEMAS);
    h.dataset.wdaTamano = pref('tamano', 'normal', TAMANOS);
    h.style.setProperty('--wda-bati', bati(oscuro() ? 'rgba(135,226,239,.10)' : 'rgba(7,104,152,.14)'));
    // Status bar icons: dark on the light themes and on the orange band of Pruebas, light on Noche.
    plugin('SystemBars')?.setStyle?.({ style: oscuro() && !APP.pruebas ? 'DARK' : 'LIGHT' })?.catch?.(() => {});
  }
  try { matchMedia('(prefers-color-scheme: dark)').addEventListener('change', aplicarAspecto); } catch { /* old WebView */ }

  /* ---------------------------------------------------------------- small helpers */
  const dinero = (n, cur) => W.wdMoney(n, cur || 'EUR');
  const km = (d) => (d < 10 ? String(d.toFixed(1)).replace('.', W.wdLocale().startsWith('en') ? '.' : ',') : Math.round(d)) + ' km';
  const fecha = (iso, opts) => { try { return new Date(iso + 'T12:00:00').toLocaleDateString(W.wdLocale(), opts); } catch { return iso; } };
  function cuando(iso) { const n = W.daysUntil(iso); if (n === 0) return T('Hoy'); if (n === 1) return T('Mañana'); return fecha(iso, { weekday: 'short', day: 'numeric', month: 'short' }); }
  const rol = () => state.me?.user?.role || null;
  function modulo() { const r = rol(); return !r ? 'visitante' : r === 'center' ? 'centro' : r === 'freelance' ? 'freelance' : r === 'admin' ? 'admin' : 'buceador'; }
  const vivo = (el) => !!el && document.body.contains(el);
  const esqueleto = (n) => Array.from({ length: n }, () => '<div class="tarjeta esqueleto" aria-hidden="true"></div>').join('');
  // Status of a booking: colour + icon + text (the text is the web's own).
  const ESTADO = { requested: ['sol', 'sobre'], pending: ['sol', 'sobre'], accepted_pending_payment: ['pend', 'reloj'], payment_in_progress: ['pend', 'reloj'], confirmed: ['ok', 'check'],
    completed: ['neutro', 'check'], rejected: ['canc', 'x'], cancelled: ['canc', 'x'], expired: ['canc', 'reloj'] };
  function estadoTag(b) { const [cls, icono] = ESTADO[b.status] || ['neutro', 'info']; return `<span class="wtag ${cls}">${ic(icono, '')}${esc(W.bookingStatus(b.status, b.status_label)[0])}</span>`; }
  // v50.55: a freelance service paid in person to the professional carries its label everywhere.
  const enPersona = (x) => !!x && x.pay_way === 'in_person';
  const personaTag = (x) => enPersona(x) ? `<span class="wtag pend">${ic('cobrar', '')}${esc(T('Pago en persona al profesional'))}</span>` : '';
  const AVISO_PERSONA = 'Este profesional cobra directamente, no a través de WORLDIVES. El precio es el publicado aquí. Acuerda con él la forma de pago y los detalles por WhatsApp. En este servicio WORLDIVES no gestiona pagos, devoluciones, cancelaciones ni incidencias.';
  const FORMAS = { cash: 'Efectivo', bizum: 'Bizum', transfer: 'Transferencia', other: 'Otra' };
  // The professional's WhatsApp of a booking paid in person: only once he has accepted (the server sends it then).
  function whatsappReserva(b) {
    if (enPersona(b)) { if (b.pro_whatsapp) abrirFuera(b.pro_whatsapp); else W.toast(T('El botón «Hablar por WhatsApp» aparece cuando el profesional acepta tu solicitud.')); return; }
    whatsappCentro({ nombre: b.center_name, telefono: b.center_phone, reserva: b });
  }
  function modoTag(s) { return (enPersona(s) ? personaTag(s) + ' ' : '') + (s.instant ? `<span class="wtag ok">${ic('cobrar', '')}${esc(s.mode_label || 'Pago al reservar')}</span>` : `<span class="wtag sol">${ic('sobre', '')}${esc(s.mode_label || 'Bajo petición')}</span>`); }
  const pedirEntrar = (titulo, texto) => `<div class="cuerpo"><h1>${titulo}</h1><div class="tarjeta pad pila-12"><p>${texto}</p><a class="wbtn ancho grande" href="#/login?next=${encodeURIComponent(location.hash || '#/')}">Entrar</a><a class="wbtn sec ancho" href="#/registro">Crear cuenta</a></div></div>`;

  function pintar(html, clase = '') {
    const app = $('#app');
    app.innerHTML = `<div class="wda${clase ? ' ' + clase : ''}">${html}</div>`;
    W.translateTree(app);
    window.scrollTo(0, 0);
    return app.firstElementChild;
  }
  // Open outside the app: maps, phone, WhatsApp. Inside the app Android opens the right app; in a browser, a new tab.
  function abrirFuera(url) {
    if (APP.native) { location.href = url; return; }
    window.open(url, '_blank', 'noopener');
  }
  const mapsDestino = ({ lat, lon, direccion }) => lat != null && lon != null ? `https://www.google.com/maps/dir/?api=1&destination=${encodeURIComponent(lat + ',' + lon)}`
    : direccion ? `https://www.google.com/maps/search/?api=1&query=${encodeURIComponent(direccion)}` : '';
  async function compartir({ titulo, texto, url }) {
    const S = plugin('Share');
    try {
      if (S) { await S.share({ title: titulo, text: texto, url, dialogTitle: T('Compartir') }); return; }
      if (navigator.share) { await navigator.share({ title: titulo, text: texto, url }); return; }
      await navigator.clipboard.writeText(url); W.toast('Enlace copiado.');
    } catch { /* closed without sharing */ }
  }
  // Where the phone is: only when the person taps «Cerca de mí» or «Mi ubicación» (never when the app opens).
  // v50.53: the same location service as the web (W.wdLocation), which also uses the Android app's Geolocation plugin.
  async function posicion() {
    try { return await W.wdLocation.get({ timeout: 12000 }); }
    catch (e) { throw new Error(T(e.code === 'denied' ? 'Sin permiso de ubicación. Puedes buscar por zona en el mapa.' : W.wdLocation.message(e.code))); }
  }
  const mem = { pos: null, cuando: '', salidas: new Map(), area: null, areaAt: 0 };
  async function miArea(fresca) {
    if (!state.me) return null;
    if (!fresca && mem.area && Date.now() - mem.areaAt < 30000) return mem.area;
    mem.area = await api('/api/me/area'); mem.areaAt = Date.now(); contadores(); return mem.area;
  }
  const vigente = (b) => !['completed', 'cancelled', 'rejected', 'expired'].includes(b.status) && (b.booking_date || '9999') >= W.wdToday();
  const porPagar = (b) => vigente(b) && ['accepted_pending_payment', 'payment_in_progress'].includes(b.status);

  /* ---------------------------------------------------------------- bottom sheets (never popups when a screen opens) */
  let hoja = null;
  function abrirHoja({ titulo, sub = '', html, pie = '', alCerrar = null }) {
    cerrarHoja(true);
    const capa = document.createElement('div');
    capa.className = 'wda-capa';
    capa.setAttribute('role', 'dialog'); capa.setAttribute('aria-modal', 'true');
    capa.innerHTML = `<div class="velo" data-cerrar></div><section class="hoja"><div class="hoja-asa" aria-hidden="true"></div>
      <header class="hoja-cab"><div><h2 id="wda-hoja-tit">${titulo}</h2>${sub ? `<p class="suave peq">${sub}</p>` : ''}</div><button type="button" class="hoja-cerrar" data-cerrar aria-label="Cerrar">${ic('x', '')}</button></header>
      <div class="hoja-cuerpo">${html}</div>${pie ? `<footer class="hoja-pie">${pie}</footer>` : ''}</section>`;
    capa.setAttribute('aria-labelledby', 'wda-hoja-tit');
    document.body.appendChild(capa);
    W.translateTree(capa);
    capa.addEventListener('click', (e) => { if (e.target.closest('[data-cerrar]')) cerrarHoja(); });
    // Pull the sheet down from its top to close it (there is always the «×» button as well).
    let y0 = null;
    const cab = capa.querySelector('.hoja-asa'), cab2 = capa.querySelector('.hoja-cab'), h = capa.querySelector('.hoja');
    [cab, cab2].forEach((el) => {
      el.addEventListener('touchstart', (e) => { y0 = e.touches[0].clientY; }, { passive: true });
      el.addEventListener('touchmove', (e) => { if (y0 == null) return; const dy = Math.max(0, e.touches[0].clientY - y0); h.style.transition = 'none'; h.style.transform = `translateY(${dy}px)`; }, { passive: true });
      el.addEventListener('touchend', (e) => { if (y0 == null) return; const dy = e.changedTouches[0].clientY - y0; y0 = null; h.style.transition = ''; h.style.transform = ''; if (dy > 90) cerrarHoja(); });
    });
    requestAnimationFrame(() => capa.classList.add('abierta'));
    hoja = { capa, alCerrar };
    return capa;
  }
  function cerrarHoja(ya) {
    const h = hoja; if (!h) return false;
    hoja = null; h.capa.classList.remove('abierta');
    setTimeout(() => h.capa.remove(), ya ? 0 : 280);
    try { h.alCerrar?.(); } catch { /* nothing */ }
    return true;
  }

  /* ---------------------------------------------------------------- shell: tabs, band, back button */
  const TABS = {
    visitante: [['#/', 'inicio', 'Inicio'], ['#/explorar', 'explorar', 'Explorar'], ['#/login', 'entrar', 'Entrar']],
    buceador: [['#/', 'inicio', 'Inicio'], ['#/explorar', 'explorar', 'Explorar'], ['#/reservas', 'reservas', 'Reservas'], ['#/buddies', 'buddies', 'Buddies'], ['#/mi-area', 'area', 'Mi área']],
    // Centro PRO and Freelance PRO (encargo §3.2): Hoy · Agenda · Escanear (central) · Solicitudes · Más. wd-app-pro.js
    // removes what each person's role does not allow (an instructor has no Solicitudes).
    centro: [['#/', 'hoy', 'Hoy'], ['#/agenda', 'agenda', 'Agenda'], ['#/escanear', 'escanear', 'Escanear', 'central'], ['#/solicitudes', 'solicitudes', 'Solicitudes'], ['#/mas', 'mas', 'Más']],
    freelance: [['#/', 'hoy', 'Hoy'], ['#/agenda', 'agenda', 'Agenda'], ['#/escanear', 'escanear', 'Escanear', 'central'], ['#/solicitudes', 'solicitudes', 'Solicitudes'], ['#/mas', 'mas', 'Más']],
    admin: [['#/', 'inicio', 'Inicio'], ['#/explorar', 'explorar', 'Explorar'], ['#/mi-area', 'area', 'Mi área']],
  };
  const TAB_DE = { home: '#/', explorar: '#/explorar', buscar: '#/explorar', punto: '#/explorar', puntos: '#/explorar', centro: '#/explorar', centros: '#/explorar', profesional: '#/explorar',
    experiencia: '#/explorar', experiencias: '#/explorar', experienciareserva: '#/explorar', tipos: '#/explorar', top10: '#/explorar', reservar: '#/explorar', 'reservar-dias': '#/explorar',
    reservas: '#/reservas', reserva: '#/reservas', 'pago-ok': '#/reservas', verificarreserva: '#/reservas', buddies: '#/buddies',
    'mi-area': '#/mi-area', ajustes: '#/mi-area', area: '#/mi-area', cuenta: '#/mi-area', logbook: '#/mi-area', 'mis-puntos': '#/mi-area', recompensas: '#/mi-area', 'como-funcionan-los-puntos': '#/mi-area', legal: '#/mi-area',
    login: '#/login', registro: '#/login', verificacion: '#/login', recuperar: '#/login', restablecer: '#/login', admin: '#/admin' };
  // Tabs of the PRO modules (the same route names mean their own screens there).
  const TAB_PRO = { home: '#/', agenda: '#/agenda', salida: '#/agenda', barco: '#/agenda', manifiesto: '#/agenda', escanear: '#/escanear', solicitudes: '#/solicitudes',
    mas: '#/mas', admin: '#/mas', reservas: '#/mas', reserva: '#/mas', ajustes: '#/mas', cuenta: '#/mas', 'mi-area': '#/mas', 'cerrar-cuenta': '#/mas', legal: '#/mas', explorar: '#/mas', equipo: '#/mas' };
  const esPro = () => ['centro', 'freelance'].includes(modulo());
  // The web pages of each tab's «home»: no «Volver» there.
  const RAICES = ['home', 'explorar', 'reservas', 'buddies', 'mi-area', 'login', 'admin', 'agenda', 'escanear', 'solicitudes', 'mas'];
  let tabActual = '#/', cuenta = { reservas: 0, solicitudes: 0 };
  function pintarTabs(nombre) {
    const mod = modulo(); let tabs = TABS[mod] || TABS.visitante;
    if (esPro() && WDA.filtrarTabs) tabs = WDA.filtrarTabs(tabs);
    tabActual = (esPro() ? TAB_PRO[nombre] : TAB_DE[nombre]) || (nombre === 'home' ? '#/' : tabActual);
    let nav = $('#wda-tabs');
    if (!nav) { nav = document.createElement('nav'); nav.id = 'wda-tabs'; nav.className = 'wda-tabs'; nav.setAttribute('aria-label', T('Secciones')); document.body.appendChild(nav); }
    const banda = $('.wda-banda'); if (banda && !banda.dataset.traducida && W.currentLanguage() !== 'es') { W.translateTree(banda); banda.dataset.traducida = '1'; }
    nav.innerHTML = tabs.map(([href, icono, txt, central]) => {
      const n = href === '#/reservas' ? cuenta.reservas : href === '#/solicitudes' ? cuenta.solicitudes : 0;
      const que = href === '#/reservas' ? 'pendientes de pago' : 'pendientes';
      return `<a class="wda-tab${central ? ' central' : ''}" href="${href}" ${href === tabActual ? 'aria-current="page"' : ''}><span class="wda-tab-ic">${ic(icono, '')}</span><span>${T(txt)}</span>${n ? `<span class="cont" aria-label="${n} ${T(que)}">${n}</span>` : ''}</a>`;
    }).join('');
  }
  function contadores() {
    const d = mem.area; cuenta.reservas = d ? (d.bookings || []).filter(porPagar).length : 0;
    pintarTabs(nombreRuta());
  }
  const nombreRuta = () => (location.hash.replace(/^#\/?/, '').split('?')[0] || 'home');
  function banda() {
    if (!APP.pruebas || $('.wda-banda')) return;
    document.body.insertAdjacentHTML('afterbegin', `<div class="wda-banda" role="note"><span><span>Pruebas</span> · <span translate="no">${esc(location.host)}</span></span><button type="button" id="wda-fallo">Reportar fallo</button></div>`);
    $('#wda-fallo').onclick = () => reportarFallo();
  }
  // Android back button: close the sheet, then go back; on Inicio the app goes to the background.
  function atras() {
    if (cerrarHoja()) return;
    const n = nombreRuta();
    if (n === 'home') { const A = plugin('App'); A?.minimizeApp ? A.minimizeApp().catch(() => A.exitApp()) : A?.exitApp?.(); return; }
    if (RAICES.includes(n)) { location.hash = '#/'; return; }
    if (history.length > 1) history.back(); else location.hash = '#/';
  }

  /* ---------------------------------------------------------------- Inicio */
  const TIPOS = [['arrecifes', 'Arrecifes'], ['pecios-y-naufragios', 'Pecios'], ['cuevas-y-cavernas', 'Cuevas y cenotes'], ['paredes', 'Paredes'], ['muck', 'Muck']];
  async function inicio() {
    const mod = modulo();
    if (mod === 'admin') return inicioProfesional(mod);
    const me = state.me, nombre = me?.user?.fullname?.split(' ')[0] || '';
    const chip = (v, t, icono = '') => `<button type="button" class="wchip" data-cuando="${v}" aria-pressed="${mem.cuando === v}">${icono ? ic(icono, '') : ''}${t}</button>`;
    const root = pintar(`<header class="cab"><div class="cab-fila"><div class="wavatar">${me ? esc(W.initials(me.user.fullname)) : ic('area', '')}</div>
        <div class="crece"><p class="suave peq"><span>Hola</span>${nombre ? `<span translate="no">, ${esc(nombre)}</span>` : ''}</p></div>${me ? '' : '<a class="wbtn sec mini" href="#/login">Entrar</a>'}</div>
        <h1>¿Dónde quieres bucear?</h1>
        <a class="buscador" href="#/buscar">${ic('buscar', '')}<span>Puntos, centros y experiencias</span></a>
        <div class="wchips" role="group" aria-label="Cuándo">${chip('cerca', 'Cerca de mí', 'ubicacion')}${chip('hoy', 'Hoy')}${chip('manana', 'Mañana')}${chip('finde', 'Este finde')}${chip('', 'Próximos 14 días')}</div></header>
      <div class="cuerpo">${avisoCookies()}
        <section id="wda-proxima" class="pila-8" hidden></section>
        <section class="pila-8"><div class="seccion-cab"><h2>Salidas con plazas cerca de ti</h2></div><div class="carrusel-h" id="wda-salidas">${esqueleto(2)}</div></section>
        <section id="wda-repetir" class="pila-8" hidden></section>
        <section class="pila-8"><h2>Tipos de buceo</h2><div class="wchips">${TIPOS.map(([k, t]) => `<a class="wchip" href="#/explorar?tipo=${k}">${t}</a>`).join('')}</div></section>
      </div>`);
    if (mem.cuando === 'cerca' && !mem.pos) mem.cuando = '';
    $('#wda-ck-ok', root)?.addEventListener('click', () => { try { localStorage.setItem('wd_cookie_notice', String(Date.now())); } catch { /* nothing */ } $('#wda-ck', root)?.remove(); });
    $$('[data-cuando]', root).forEach((b) => { b.setAttribute('aria-pressed', String(b.dataset.cuando === mem.cuando)); b.onclick = () => elegirCuando(b.dataset.cuando, root); });
    cargarSalidas(root);
    if (me && rol() === 'recreational') miArea().then((d) => vivo(root) && pintarProxima(root, d)).catch(() => {});
  }
  // The web's cookie notice floats over the page; in the app it is a card at the top of Inicio, the same text, once a year.
  function avisoCookies() {
    let visto = 0; try { visto = Number(localStorage.getItem('wd_cookie_notice') || 0); } catch { return ''; }
    if (visto && Date.now() - visto < 365 * 864e5) return '';
    return `<div class="aviso neutro ck" id="wda-ck" role="region" aria-label="Aviso de cookies">${ic('candado')}<div><span>Solo usamos cookies técnicas, necesarias para que la web funcione (por ejemplo, para mantener tu sesión). No usamos cookies de publicidad ni de analítica.</span>
      <span class="ck-acc"><a href="#/legal/cookies">Más información</a><button class="wbtn texto" type="button" id="wda-ck-ok">Entendido</button></span></div></div>`;
  }
  async function elegirCuando(v, root) {
    if (v === 'cerca') {
      if (mem.cuando === 'cerca') { mem.cuando = ''; mem.pos = null; }
      else {
        try { W.toast('Buscando dónde estás…'); mem.pos = await posicion(); mem.cuando = 'cerca'; } catch (e) { W.toast(e.message); return; }
      }
    } else mem.cuando = v;
    $$('[data-cuando]', root).forEach((b) => b.setAttribute('aria-pressed', String(b.dataset.cuando === mem.cuando)));
    cargarSalidas(root);
  }
  async function cargarSalidas(root) {
    const box = $('#wda-salidas', root); if (!box) return;
    box.innerHTML = esqueleto(2);
    const q = new URLSearchParams({ limite: '12' });
    if (mem.cuando && mem.cuando !== 'cerca') q.set('cuando', mem.cuando);
    if (mem.pos) Object.entries(W.wdLocation.params(mem.pos)).forEach(([k, v]) => q.set(k, v));   // v50.54: km only if precise
    let d;
    try { d = await api('/api/salidas-cercanas?' + q); } catch (e) { if (vivo(box)) box.innerHTML = `<div class="tarjeta vacio"><p>${esc(T('No se han podido cargar las salidas.'))}</p><button class="wbtn sec mini" type="button" data-reintentar>${T('Reintentar')}</button></div>`; $('[data-reintentar]', box)?.addEventListener('click', () => cargarSalidas(root)); return; }
    if (!vivo(box)) return;
    (d.items || []).forEach((s) => mem.salidas.set(String(s.slot_id), s));
    box.innerHTML = d.items?.length ? d.items.map(tarjetaSalida).join('')
      : `<div class="tarjeta vacio"><p>No hay salidas con plazas en estas fechas.</p><a class="wbtn sec mini" href="#/explorar">Ver el mapa</a></div>`;
    W.translateTree(box);
  }
  // v50.53: the same service card as the web (W.wdServiceCard), with the photo of the service (own, template's or neutral).
  function tarjetaSalida(s) {
    const donde = [s.provider_name, ...(s.points || []).slice(0, 2).map((p) => p.name)].filter(Boolean).map((x) => `<span translate="no">${esc(x)}</span>`).join(' · ');
    return W.wdServiceCard(s, {
      kicker: `<span class="num">${esc(cuando(s.date))} · ${esc(s.time || '')}</span>${s.distance_km != null ? ` · <span class="num">${km(s.distance_km)}</span>` : ''}`,
      meta: `${modoTag(s)}`, body: `<p class="svc2-note">${donde}</p><p class="svc2-note"><b class="num">${s.spots_left}</b> <span>${s.spots_left === 1 ? 'plaza libre' : 'plazas libres'}</span></p>`,
      price: s.price ? `<small>desde</small><strong>${dinero(s.price, s.currency)}</strong>` : '',
      actions: `<button class="wbtn" type="button" data-reservar="${s.slot_id}"${s.bookable === false ? ' disabled' : ''}>Reservar</button>${s.bookable === false && s.unavailable_reason ? `<p class="svc2-note">${esc(s.unavailable_reason)}</p>` : ''}`,
      cls: 'tarjeta-salida' });
  }
  function anillo(n) {
    const v = Math.max(0.04, 1 - Math.min(n, 30) / 30), r = 32, c = 2 * Math.PI * r;
    const txt = n === 0 ? `<b>${T('Hoy')}</b>` : `<b>${n}<small>${T(n === 1 ? 'día' : 'días')}</small></b>`;
    return `<div class="anillo"><svg viewBox="0 0 76 76"><circle class="pista" cx="38" cy="38" r="${r}" fill="none" stroke-width="7"/><circle class="valor" cx="38" cy="38" r="${r}" fill="none" stroke-width="7" stroke-dasharray="${(c * v).toFixed(1)} ${c.toFixed(1)}"/></svg>${txt}</div>`;
  }
  function pintarProxima(root, d) {
    const proximas = (d?.bookings || []).filter(vigente).sort((a, b) => String(a.booking_date + a.booking_time).localeCompare(String(b.booking_date + b.booking_time)));
    const b = proximas[0], box = $('#wda-proxima', root);
    if (b && box) {
      const n = Math.max(0, W.daysUntil(b.booking_date) || 0);
      box.hidden = false;
      box.innerHTML = `<div class="tarjeta pad pila-12" aria-label="Próxima inmersión"><div class="fila">${anillo(n)}<div class="crece pila"><span class="eti">Próxima inmersión</span><h2${b.service_title ? ' translate="no"' : ''}>${esc(b.service_title || 'Inmersión')}</h2>
        <p class="peq"><b class="num">${esc(W.wdLongDay(b.booking_date))}${b.booking_time ? ' · ' + esc(b.booking_time) : ''}</b></p>
        <p class="suave peq"><span translate="no">${esc(b.center_name || '')}</span>${b.point_name ? ` · <span translate="no">${esc(b.point_name)}</span>` : ''}</p></div></div>
        <div class="wtags">${estadoTag(b)}${personaTag(b)}</div>
        <div class="acciones tres"><button class="accion" type="button" data-llegar>${ic('ruta')}<span>Cómo llegar</span></button><a class="accion" href="#/reserva?id=${b.id}">${ic('qr')}<span>Ver reserva y QR</span></a>
        <button class="accion wa" type="button" data-wa>${ic('wa')}<span>WhatsApp al centro</span></button></div></div>`;
      W.translateTree(box);
      const llegar = mapsDestino({ direccion: [b.center_address, b.city].filter(Boolean).join(', ') });
      const bl = $('[data-llegar]', box); if (!llegar) bl.setAttribute('aria-disabled', 'true');
      bl.onclick = () => llegar ? abrirFuera(llegar) : W.toast('El centro no ha publicado su dirección.');
      $('[data-wa]', box).onclick = () => whatsappReserva(b);
    }
    // «Repetir»: the centres where this diver has already booked.
    const vistos = new Map();
    (d?.bookings || []).filter((x) => !['cancelled', 'rejected', 'expired'].includes(x.status)).forEach((x) => {
      const k = x.center_id ? 'c' + x.center_id : x.provider_user_id ? 'p' + x.provider_user_id : null; if (!k) return;
      const v = vistos.get(k) || { n: 0, ultima: '', x }; v.n++; if ((x.booking_date || '') > v.ultima) { v.ultima = x.booking_date || ''; v.x = x; } vistos.set(k, v);
    });
    const rep = [...vistos.values()].sort((a, b2) => b2.ultima.localeCompare(a.ultima)).slice(0, 3), caja = $('#wda-repetir', root);
    if (rep.length && caja) {
      caja.hidden = false;
      caja.innerHTML = `<h2>Repetir</h2><div class="tarjeta plana lista">${rep.map((v) => {
        const href = v.x.center_id ? `#/centro?id=${v.x.center_id}` : `#/profesional?id=${v.x.provider_user_id}`;
        return `<div class="lista-fila"><div class="wavatar">${esc(W.initials(v.x.center_name || ''))}</div><div class="crece pila"><b translate="no">${esc(v.x.center_name || '')}</b>
          <span class="suave peq"><span class="num">${v.n}</span> <span>${v.n === 1 ? 'reserva' : 'reservas'}</span>${v.ultima ? ` · <span class="num">${esc(fecha(v.ultima, { day: 'numeric', month: 'short', year: 'numeric' }))}</span>` : ''}</span></div>
          <a class="wbtn sec mini" href="${href}">Reservar de nuevo</a></div>`;
      }).join('')}</div>`;
      W.translateTree(caja);
    }
  }
  function inicioProfesional(mod) {
    const me = state.me, nombre = me?.user?.fullname?.split(' ')[0] || '';
    const textos = { admin: ['La administración se queda en la web.', 'La app es para buceadores, centros y freelance. Puedes abrir la administración aquí o en un ordenador.', 'Abrir la administración'] }[mod];
    pintar(`<header class="cab"><div class="cab-fila"><div class="wavatar">${esc(W.initials(me?.user?.fullname || ''))}</div><div class="crece"><p class="suave peq"><span>Hola</span><span translate="no">, ${esc(nombre)}</span></p></div></div><h1>${mod === 'admin' ? 'Administración' : 'Tu día'}</h1></header>
      <div class="cuerpo"><div class="aviso sol">${ic('info')}<div><b>${textos[0]}</b> ${textos[1]}</div></div>
        <a class="wbtn ancho grande" href="#/admin">${textos[2]}</a>
        <div class="tarjeta plana lista"><a class="lista-fila" href="#/explorar">${ic('explorar')}<span class="crece">Explorar el mapa</span>${ic('chev', 'chev')}</a>
        <a class="lista-fila" href="#/ajustes">${ic('ajustes')}<span class="crece">Ajustes</span>${ic('chev', 'chev')}</a></div></div>`);
  }

  /* ---------------------------------------------------------------- WhatsApp to the centre: the message already written */
  const MSG = {
    es: (n, b) => `Hola, soy ${n}.` + (b ? ` Tengo una reserva para «${b.s}» el ${b.f}${b.h ? ' a las ' + b.h : ''} (reserva ${b.id}). ` : ' '),
    en: (n, b) => `Hello, this is ${n}.` + (b ? ` I have a booking for “${b.s}” on ${b.f}${b.h ? ' at ' + b.h : ''} (booking ${b.id}). ` : ' '),
    fr: (n, b) => `Bonjour, je suis ${n}.` + (b ? ` J’ai une réservation pour « ${b.s} » le ${b.f}${b.h ? ' à ' + b.h : ''} (réservation ${b.id}). ` : ' '),
  };
  function telefonoWa(t) { const s = String(t || '').trim(); if (!/^(\+|00)/.test(s)) return ''; const d = s.replace(/^00/, '').replace(/\D/g, ''); return d.length >= 8 ? d : ''; }
  function whatsappCentro({ nombre, telefono, reserva }) {
    const num = telefonoWa(telefono), lang = W.currentLanguage();
    const yo = state.me?.user?.fullname || '';
    const b = reserva ? { s: reserva.service_title || 'Inmersión', f: fecha(reserva.booking_date, { day: 'numeric', month: 'long' }), h: reserva.booking_time || '', id: reserva.code || ('#' + reserva.id) } : null;
    const texto = (MSG[lang] || MSG.en)(yo || '—', b).trim();
    const pie = APP.pruebas
      ? `<div class="aviso pend">${ic('info')}<div>En WORLDIVES Pruebas no se abre WhatsApp: así quedaría el mensaje.</div></div><button class="wbtn sec ancho" type="button" data-cerrar>Cerrar</button>`
      : num ? `<button class="wbtn wa ancho grande" type="button" id="wda-abrir-wa">${ic('wa', '')}Abrir WhatsApp</button><button class="wbtn sec ancho" type="button" data-cerrar>Cancelar</button>`
        : `<div class="aviso neutro">${ic('info')}<div>Este centro no tiene un móvil con prefijo internacional. Llámale o escríbele desde su ficha.</div></div>`;
    const capa = abrirHoja({ titulo: `${T('WhatsApp a')} <span translate="no">${esc(nombre || '')}</span>`, sub: 'Número público del centro y un mensaje con tu reserva. Puedes cambiarlo antes de enviarlo.',
      html: `<div class="chat-fondo"><label class="sr-only" for="wda-wa-txt">Mensaje</label><textarea class="burbuja" id="wda-wa-txt" rows="4"></textarea></div>`, pie });
    $('#wda-wa-txt', capa).value = texto;
    $('#wda-abrir-wa', capa)?.addEventListener('click', () => { abrirFuera(`https://wa.me/${num}?text=${encodeURIComponent($('#wda-wa-txt', capa).value)}`); cerrarHoja(); });
  }

  /* ---------------------------------------------------------------- quick booking in a sheet (≤ 5 taps, ≤ 30 s) */
  const PENDIENTE = 'wda-reserva-pendiente';
  const recuerda = (s) => { try { sessionStorage.setItem(PENDIENTE, JSON.stringify(s)); } catch { /* the person chooses again */ } };
  function pendiente() { try { const v = JSON.parse(sessionStorage.getItem(PENDIENTE) || 'null'); sessionStorage.removeItem(PENDIENTE); return v; } catch { return null; } }
  async function abrirReserva(sal) {
    if (!sal) return;
    const st = { sal, pax: 1, abierta: '', eq: W.eqValue(1, []), extras: new Set(), nota: '', quote: null, enviando: false, otras: null, rental: null, extrasList: [], aviso: false };
    const me = state.me, perfil = me?.profile || {};
    const cid = sal.center_id || 0;
    // Extras of the centre (a freelance has none), the service (with its rental: v50.58) and its other departures.
    const [ex, cat] = await Promise.allSettled(cid ? [api('/api/center-extras?center_id=' + cid), api('/api/provider-services?provider_id=0&center_id=' + cid)]
      : [Promise.resolve({ items: [] }), api('/api/provider-services?provider_id=' + sal.provider_id)]);
    st.extrasList = (ex.status === 'fulfilled' ? ex.value.items || [] : []).filter((e) => e.active !== 0);
    const serv = cat.status === 'fulfilled' ? (cat.value.items || []).find((s) => String(s.id) === String(sal.service_id)) : null;
    // v50.58 · Rental inside the dive: the same picker as the web (one per diver, sizes, «Equipo completo»); the tank
    // and the weights are always included. The sizes of last time with this centre come already chosen.
    st.rental = serv?.rental || null;
    const alquila = st.rental?.mode === 'offer' && (st.rental.pieces || []).length > 0;
    let tallasMem = {};
    if (alquila && me) api('/api/equipment/my-sizes?' + (cid ? 'center_id=' + cid : 'provider_id=' + sal.provider_id)).then((r) => { tallasMem = r.sizes || {}; }).catch(() => {});
    const nombres = () => Array.from({ length: st.pax }, (_, i) => i === 0 ? T('Tú') : T('Buceador {n}').replace('{n}', i + 1));
    const eqTitulo = () => {
      if (!st.eq.rent) return T('Llevo mi equipo');
      const lab = Object.fromEntries((st.rental.pieces || []).map((p) => [p.code, p.label]));
      const por = st.eq.divers.map((d, i) => { const it = Object.keys(d.items).map((c) => lab[c]).filter(Boolean); return it.length ? (st.pax > 1 ? `${nombres()[i]}: ` : '') + (d.kit ? T('Equipo completo') : it.join(', ')) : ''; }).filter(Boolean);
      return por.length ? por.join(' · ') : T('Necesito equipo');
    };
    let eqPick = null;
    st.otras = (serv?.slots || []).filter((x) => x.status === 'open' && Number(x.spots_available) > 0).slice(0, 12);
    const persona = enPersona(sal) || enPersona(serv), info = serv || sal;
    const avisoPersona = () => !persona ? '' : `<div class="aviso pend">${ic('cobrar')}<div class="pila"><b>${esc(T('Pago en persona al profesional'))}</b><span>${esc(T(info.pay_notice || AVISO_PERSONA))}</span>
      ${(info.pay_methods || []).length ? `<span class="peq"><b>${esc(T('Formas de pago que acepta'))}:</b> ${esc(info.pay_methods.map((m) => m === 'other' ? (info.pay_other || '') : T(FORMAS[m] || m)).filter(Boolean).join(' · '))}</span>` : ''}
      <span class="peq"><b>${esc(T('Política del profesional'))}:</b> ${esc(info.pay_policy || T('Este profesional no ha publicado una política de cancelación. WORLDIVES no gestiona cancelaciones ni devoluciones en este servicio.'))}</span>
      <label class="marcar"><input type="checkbox" id="wda-aviso" ${st.aviso ? 'checked' : ''}><span class="crece">${esc(T('He leído el aviso: pago en persona al profesional'))}</span></label></div></div>`;
    const linea = (k, icono, titulo, sub, editor) => `<div class="bloque-res"><div class="linea-res">${ic(icono)}<div class="crece"><p style="font-weight:600">${titulo}</p>${sub ? `<p class="suave peq">${sub}</p>` : ''}</div>
      ${editor ? `<button class="wbtn texto" type="button" data-cambiar="${k}" aria-expanded="${st.abierta === k}">${st.abierta === k ? T('Listo') : T('Cambiar')}</button>` : ''}</div>${editor && st.abierta === k ? `<div class="editor">${editor}</div>` : ''}</div>`;
    const html = () => {
      const s = st.sal, puntos = (s.points || []).map((p) => p.name).join(', ');
      const exSel = st.extrasList.filter((e) => st.extras.has(String(e.id)));
      return linea('fecha', 'agenda', `${esc(cuando(s.date))} · ${esc(s.time || '')}`, puntos ? `<span translate="no">${esc(puntos)}</span>` : esc(T('Punto a concretar con el centro')),
        st.otras?.length > 1 ? `<div class="wchips">${st.otras.map((x) => `<button type="button" class="wchip" data-slot="${x.id}" aria-pressed="${String(x.id) === String(s.slot_id)}">${esc(cuando(x.slot_date))} · ${esc(x.slot_time || '')}</button>`).join('')}</div>` : '')
        + linea('pers', 'buddies', st.pax === 1 ? T('1 persona') : `${st.pax} ${T('personas')}`, `${s.spots_left} ${T(s.spots_left === 1 ? 'plaza libre' : 'plazas libres')}`,
          `<div class="contador"><button type="button" data-pax="-1" aria-label="${T('Una persona menos')}">${ic('menos', '')}</button><b>${st.pax}</b><button type="button" data-pax="1" aria-label="${T('Una persona más')}">${ic('mas1', '')}</button><span class="suave peq">${T('personas')}</span></div>`)
        + (me ? linea('tit', 'ficha', perfil.certification_name ? `<span translate="no">${esc(perfil.certification_name)}</span>` : esc(T('Sin titulación en tu ficha')), esc(T('De tu ficha · el centro la comprueba antes de bucear')),
          `<p class="peq">${T('Se cambia en Mi ficha. Esta reserva usa lo último que guardaste.')}</p><a class="wbtn sec mini" href="#/cuenta">${T('Abrir Mi ficha')}</a>`) : '')
        + (alquila ? linea('equipo', 'tanque', `<span id="wda-eq-tit">${esc(eqTitulo())}</span>`, esc(T('Incluido: botella y plomos')), '<div id="wda-eq" class="wda-eq"></div>')
          : st.rental?.mode === 'included' ? linea('equipo', 'tanque', esc(T('Equipo incluido en el precio')), esc(T('Incluido: botella y plomos')), '') : '')
        + (st.extrasList.length ? linea('extras', 'mas1', exSel.length ? esc(exSel.map((e) => e.name).join(', ')) : esc(T('Sin extras')), '',
          st.extrasList.map((e) => `<label class="marcar"><input type="checkbox" data-extra="${e.id}" ${st.extras.has(String(e.id)) ? 'checked' : ''}><span class="crece" translate="no">${esc(e.name)}</span><span class="peq num">+${dinero(e.price, s.currency)}</span></label>`).join('')) : '')
        + linea('nota', 'documento', st.nota ? esc(st.nota.slice(0, 60)) : esc(T('Sin nota para el centro')), '', `<div class="campo"><label for="wda-nota">${T('Nota para el centro')}</label><textarea id="wda-nota" maxlength="500">${esc(st.nota)}</textarea></div>`)
        + (rol() === 'recreational' ? `<label class="interruptor"><span><b>${T('Avisos de esta reserva por WhatsApp')}</b><br><span class="suave peq">${T(me.whatsapp?.phone_ok ? 'El centro te escribe a tu móvil.' : 'Añade tu móvil con prefijo en «Mi cuenta» para recibirlos.')}</span></span><input type="checkbox" id="wda-wa" ${me.whatsapp?.consent ? 'checked' : ''}></label>` : '')
        + avisoPersona()
        + `<a class="wbtn texto" href="${cid ? `#/reservar?center=${cid}&service=${s.service_id}&slot=${s.slot_id}` : `#/reservar?provider=${s.provider_id}&service=${s.service_id}&slot=${s.slot_id}`}" data-cerrar>${T('Más opciones: guía, nitrox, recogida…')}</a>`;
    };
    const pie = () => {
      const q = st.quote, s = st.sal, total = q ? dinero(q.total, q.currency) : '…';
      const pagar = s.instant;
      const titulo = !me ? 'Entrar y reservar' : pagar ? 'Reservar y pagar' : 'Enviar solicitud';
      return `<div class="fila-entre"><span>${T('Total')} · ${st.pax === 1 ? T('1 persona') : `${st.pax} ${T('personas')}`}</span><span class="precio">${total}</span></div>
        ${q?.deposit ? `<p class="suave peq">${T('Ahora pagas la señal')}: <b>${dinero(q.deposit, q.currency)}</b>. ${T('El resto, en el centro')}: <b>${dinero(q.due_at_center, q.currency)}</b>.</p>` : ''}
        <button class="wbtn ancho grande" type="button" id="wda-confirmar" ${st.enviando || s.bookable === false ? 'disabled' : ''}><span>${titulo}</span>${me && pagar ? `<span class="num">${total}</span>` : ''}</button>
        <p class="suave peq centrado">${pagar ? T('Pago seguro con Stripe: Google Pay, Apple Pay o tarjeta.') : persona ? T('No pagas nada a través de WORLDIVES: acuerdas el pago con el profesional por WhatsApp cuando acepte.') : T('No pagas nada hasta que el centro acepte.')}</p>`;
    };
    const capa = abrirHoja({ titulo: `<span translate="no">${esc(sal.title)}</span>`, sub: `<span translate="no">${esc(sal.provider_name || '')}</span> · ${modoTag(sal)}`, html: html(), pie: pie() });
    const cuerpo = $('.hoja-cuerpo', capa), piePie = $('.hoja-pie', capa);
    const montarEquipo = () => {
      const host = $('#wda-eq', cuerpo); eqPick = null; if (!host) return;
      const q = st.quote?.equipment || {};
      const aviso = (q.kit_broken || []).includes(st.eq.tab) && st.eq.rent ? T('Has quitado una pieza del equipo completo: ahora se cobra por piezas. Nuevo importe: {t}.').replace('{t}', dinero(st.quote.total, st.quote.currency)) : '';
      eqPick = W.wdEquipPicker(host, { pieces: st.rental.pieces, kit: st.rental.kit, pax: st.pax, names: nombres(), stock: q.stock, memory: tallasMem, value: st.eq, kitNotice: aviso,
        onChange: (v, escribiendo) => { const t = $('#wda-eq-tit', cuerpo); if (t) t.textContent = eqTitulo(); if (!escribiendo) cotizar(); } });
    };
    const repintar = () => { const y = cuerpo.scrollTop; cuerpo.innerHTML = html(); W.translateTree(cuerpo); montarEquipo(); cuerpo.scrollTop = y; };
    const repintarPie = () => { piePie.innerHTML = pie(); W.translateTree(piePie); $('#wda-confirmar', piePie).onclick = confirmar; };
    let qn = 0;
    const cotizar = async () => {
      const n = ++qn, s = st.sal;
      const p = new URLSearchParams({ center_id: String(cid || 0), service_id: String(s.service_id), slot_id: String(s.slot_id), participants: String(st.pax),
        extras: [...st.extras].join(',') });
      if (alquila && st.eq.rent) p.set('equipment_sel', JSON.stringify(W.eqPayload(st.eq)));
      try { const q = await api('/api/booking-quote?' + p); if (n === qn) { st.quote = q; repintarPie(); eqPick?.redraw({ stock: q.equipment?.stock }); } } catch { /* keep the last total */ }
    };
    cuerpo.addEventListener('click', (e) => {
      const b = e.target.closest('button'); if (!b) return;
      if (b.dataset.cambiar) { st.nota = $('#wda-nota', cuerpo)?.value ?? st.nota; st.abierta = st.abierta === b.dataset.cambiar ? '' : b.dataset.cambiar; repintar(); return; }
      if (b.dataset.pax) { st.pax = Math.max(1, Math.min(Number(st.sal.spots_left) || 1, st.pax + Number(b.dataset.pax))); repintar(); cotizar(); return; }
      if (b.dataset.slot) {
        const x = st.otras.find((o) => String(o.id) === b.dataset.slot); if (!x) return;
        st.sal = { ...st.sal, slot_id: x.id, date: x.slot_date, time: x.slot_time, spots_left: Number(x.spots_available), points: x.points || st.sal.points };
        st.pax = Math.min(st.pax, st.sal.spots_left || 1); repintar(); cotizar();
      }
    });
    cuerpo.addEventListener('change', (e) => {
      const t = e.target;
      if (t.dataset.extra) { t.checked ? st.extras.add(t.dataset.extra) : st.extras.delete(t.dataset.extra); cotizar(); }
      if (t.id === 'wda-nota') st.nota = t.value;
      if (t.id === 'wda-aviso') st.aviso = t.checked;
    });
    async function confirmar() {
      if (st.enviando) return;
      st.nota = $('#wda-nota', cuerpo)?.value ?? st.nota;
      if (!state.me) { recuerda(st.sal); cerrarHoja(); W.toast('Entra o crea tu cuenta para terminar. Guardamos la salida que has elegido.'); location.hash = '#/login?next=' + encodeURIComponent(location.hash || '#/'); return; }
      const s = st.sal, wa = $('#wda-wa', cuerpo);
      if (persona && !st.aviso) { W.toast(T('Marca la casilla del aviso: este profesional cobra directamente, no a través de WORLDIVES.')); $('#wda-aviso', cuerpo)?.focus(); return; }
      const falta = alquila ? W.eqMissing(st.eq, st.rental.pieces, nombres()) : null;   // a piece still without its size
      if (falta) { st.eq.tab = falta.diver; st.abierta = 'equipo'; repintar(); W.toast(falta.text); $('#wda-eq', cuerpo)?.scrollIntoView({ block: 'center' }); return; }
      st.enviando = true; repintarPie(); const btn = $('#wda-confirmar', piePie); btn.textContent = T('Enviando…');
      try {
        const c = await postJSON('/api/bookings', { ...(wa ? { wa_consent: wa.checked, lang: W.currentLanguage() } : {}), ...W.wdAppPay(), center_id: cid || null, service_id: s.service_id, slot_id: s.slot_id,
          dive_point_id: s.points?.length === 1 ? s.points[0].id : null, dive_point_name: s.points?.length === 1 ? s.points[0].name : null, booking_date: s.date, booking_time: s.time, participants: st.pax,
          equipment: alquila ? W.eqPayload(st.eq) : [], equipment_notes: alquila && st.eq.rent ? st.eq.note : '', extra_ids: [...st.extras].map(Number), notes: st.nota, in_person_ack: persona && st.aviso });
        mem.areaAt = 0;
        if (c.checkout_url) { btn.textContent = T('Abriendo el pago seguro…'); pagoEnCurso = c.id; W.wdOpenCheckout(c.checkout_url); setTimeout(() => { st.enviando = false; cerrarHoja(); }, 1500); return; }
        cerrarHoja(); hechoReserva(c);
      } catch (err) { st.enviando = false; repintarPie(); W.toast(err.message); }
    }
    $('#wda-confirmar', piePie).onclick = confirmar;
    cotizar();
  }
  function hechoReserva(c) {
    const ok = c.status === 'confirmed';
    const capa = abrirHoja({ titulo: ok ? T('¡Reserva confirmada!') : T('Solicitud enviada'), sub: '',
      html: `<div class="check-grande">${ic(ok ? 'check' : 'sobre', '')}</div><p class="centrado">${ok ? T('Tienes tu plaza. El QR para el barco está en tu reserva.') : T('El centro te contestará pronto. No se cobra nada hasta que te acepten.')}</p>`,
      pie: `<a class="wbtn ancho grande" href="#/reserva?id=${c.id}" data-cerrar>${T('Ver mi reserva')}</a><a class="wbtn sec ancho" href="#/reservas" data-cerrar>${T('Mis reservas')}</a>` });
    W.translateTree(capa);
  }
  let pagoEnCurso = null;
  document.addEventListener('click', (e) => {
    const b = e.target.closest('[data-reservar]'); if (!b) return;
    e.preventDefault();
    abrirReserva(mem.salidas.get(b.dataset.reservar));
  });

  /* ---------------------------------------------------------------- Explorar: full-screen map + sheet of three heights */
  const ALTURAS = ['asomada', 'media', 'completa'];
  async function explorar(params) {
    const tipo = params.get('tipo') || '', ver = params.get('ver') || 'puntos';
    const chip = (k, t, v = 'puntos') => `<button type="button" class="wchip" data-ver="${v}" data-tipo="${k}">${t}</button>`;
    const root = pintar(`<div class="mapa-lienzo" id="wda-mapa"></div>
      <div class="mapa-sup"><a class="buscador" href="#/buscar">${ic('buscar', '')}<span>Puntos, centros y experiencias</span></a>
        <div class="wchips" role="group" aria-label="Qué ver en el mapa">${chip('', 'Todos los puntos')}${TIPOS.slice(0, 4).map(([k, t]) => chip(k, t)).join('')}${chip('', 'Salidas con plazas', 'salidas')}${chip('', 'Centros', 'centros')}</div></div>
      <div class="mapa-lado"><button type="button" id="wda-capas">${ic('capas')}<span>Capas</span></button><button type="button" id="wda-yo">${ic('ubicacion')}<span>Mi ubicación</span></button></div>
      <button type="button" class="wbtn zona-btn" id="wda-zona" hidden>${ic('buscar', '')}Buscar en esta zona</button>
      <div class="carrusel" id="wda-carrusel" hidden></div>
      <section class="mapa-hoja" id="wda-hoja" data-altura="asomada" aria-label="Lista"><button type="button" class="hoja-asa" id="wda-asa" aria-label="Cambiar la altura de la lista"></button>
        <header class="hoja-cab"><div><h2 id="wda-cuenta">…</h2><p class="suave peq" id="wda-cuenta-sub"></p></div></header><div class="hoja-cuerpo"><div class="tarjeta plana lista" id="wda-lista"></div></div></section>
      <button type="button" class="wbtn sec ver-lista" id="wda-verlista">${ic('lista', '')}<span>Ver lista</span></button>`, 'wda-mapa');
    const ex = { ver, tipo, todos: [], vis: [], marcas: new Map(), capa: null, map: null, sync: null };
    $$('[data-ver]', root).forEach((b) => {
      const on = () => b.dataset.ver === ex.ver && (ex.ver !== 'puntos' || b.dataset.tipo === ex.tipo);
      b.setAttribute('aria-pressed', String(on()));
      b.onclick = () => { ex.ver = b.dataset.ver; ex.tipo = b.dataset.tipo; $$('[data-ver]', root).forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.ver === ex.ver && (ex.ver !== 'puntos' || x.dataset.tipo === ex.tipo)))); cargar(true); };
    });
    if (!window.L) { $('#wda-mapa', root).innerHTML = `<div class="vacio"><p>${esc(T('El mapa no está disponible ahora mismo.'))}</p></div>`; return; }
    W.wdTileDefaults();
    const map = L.map($('#wda-mapa', root), { zoomControl: false, attributionControl: true, worldCopyJump: false }).setView([30, -5], 3);
    ex.map = map; W.wdLimitMap(map);
    // The layer selector of the web (Mapa · Satélite · Relieve), shown in a sheet.
    const sel = document.createElement('div'); sel.className = 'capas-sel'; sel.innerHTML = W.wdLayerToolbar();
    W.wdMapLayers(map, sel);
    $('#wda-capas', root).onclick = () => {
      const capa = abrirHoja({ titulo: T('Capas del mapa'), sub: T('El relieve es orientativo (GEBCO): no sirve para navegar.'), html: '<div id="wda-capas-sitio"></div>', alCerrar: () => sel.remove() });
      $('#wda-capas-sitio', capa).appendChild(sel); W.translateTree(sel);
    };
    $('#wda-yo', root).onclick = async () => {
      try { W.toast('Buscando dónde estás…'); mem.pos = await posicion(); solo(() => map.setView([mem.pos.lat, mem.pos.lon], 11)); setTimeout(() => zona(), 400); }
      catch (e) { W.toast(e.message); }
    };
    // The sheet: three heights, dragged or with its handle; «Ver lista / Ver mapa» always does it with one tap.
    const hojaM = $('#wda-hoja', root), verLista = $('#wda-verlista', root);
    const altura = (a) => { hojaM.dataset.altura = a; verLista.innerHTML = a === 'completa' ? `${ic('mapa', '')}<span>${T('Ver mapa')}</span>` : `${ic('lista', '')}<span>${T('Ver lista')}</span>`; $('#wda-carrusel', root).hidden = a !== 'asomada' || !ex.sync; };
    verLista.onclick = () => altura(hojaM.dataset.altura === 'completa' ? 'asomada' : 'completa');
    $('#wda-asa', root).onclick = () => altura(ALTURAS[(ALTURAS.indexOf(hojaM.dataset.altura) + 1) % 3]);
    let y0 = null, a0 = 'asomada';
    hojaM.querySelector('.hoja-cab').addEventListener('touchstart', (e) => { y0 = e.touches[0].clientY; a0 = hojaM.dataset.altura; }, { passive: true });
    [$('#wda-asa', root), hojaM.querySelector('.hoja-cab')].forEach((el) => el.addEventListener('touchstart', (e) => { y0 = e.touches[0].clientY; a0 = hojaM.dataset.altura; }, { passive: true }));
    hojaM.addEventListener('touchend', (e) => {
      if (y0 == null) return; const dy = e.changedTouches[0].clientY - y0; y0 = null; if (Math.abs(dy) < 40) return;
      const i = ALTURAS.indexOf(a0); altura(ALTURAS[Math.max(0, Math.min(2, i + (dy < 0 ? 1 : -1)))]);
    });
    // «Buscar en esta zona»: appears when the person moves the map (not when the app moves it).
    let movido = false, auto = 0;
    const solo = (fn) => { auto = Date.now(); fn(); };
    map.on('dragstart', () => { movido = true; });
    map.on('zoomstart', () => { if (Date.now() - auto > 900) movido = true; });
    map.on('moveend', () => { if (movido) $('#wda-zona', root).hidden = false; });
    $('#wda-zona', root).onclick = () => { zona(); };
    function zona() { $('#wda-zona', root).hidden = true; movido = false; listar(); }

    const ICONO_C = (activo) => L.divIcon({ className: '', html: `<span class="marca-c${activo ? ' is-sync' : ''}" role="img" aria-label="${esc(T('Centro de buceo'))}">${ic('tienda', '')}</span>`, iconSize: [40, 40], iconAnchor: [20, 20] });
    async function cargar(encuadrar) {
      ex.sync = null; $('#wda-carrusel', root).hidden = true;
      if (ex.capa) { map.removeLayer(ex.capa); ex.capa = null; } ex.marcas.clear();
      $('#wda-cuenta', root).textContent = T('Cargando…'); ex.sinSitio = [];
      try {
        if (ex.ver === 'centros') {
          const d = await api('/api/centers');
          ex.todos = (d.items || []).filter((c) => c.latitude != null && c.longitude != null).map((c) => ({ k: 'c' + c.id, tipo: 'centro', id: c.id, nombre: c.name, lat: +c.latitude, lon: +c.longitude, sub: [c.city, c.country].filter(Boolean).join(' · '), logo: c.logo_url, href: `#/centro?id=${c.id}` }));
        } else if (ex.ver === 'salidas') {
          const q = new URLSearchParams({ limite: '50' }); if (mem.pos) Object.entries(W.wdLocation.params(mem.pos)).forEach(([k, v]) => q.set(k, v));
          const d = await api('/api/salidas-cercanas?' + q);
          (d.items || []).forEach((s) => mem.salidas.set(String(s.slot_id), s));
          // Departures of a centre that has not placed itself on the map: in the list, never on the map.
          ex.sinSitio = (d.items || []).filter((s) => s.lat == null || s.lon == null);
          ex.todos = (d.items || []).filter((s) => s.lat != null && s.lon != null).map((s) => ({ k: 's' + s.slot_id, tipo: 'salida', id: s.slot_id, nombre: s.title, lat: +s.lat, lon: +s.lon, sal: s,
            sub: `${cuando(s.date)} · ${s.time || ''} · ${s.provider_name || ''}`, href: s.center_id ? `#/centro?id=${s.center_id}` : `#/profesional?id=${s.provider_id}` }));
        } else {
          const layer = await W.loadMapLayer();
          ex.todos = (layer.items || []).filter((p) => p.latitude != null && (!ex.tipo || !p.types || p.types.includes(ex.tipo)))
            .map((p) => ({ k: 'p' + p.id, tipo: 'punto', id: p.id, nombre: p.name, lat: +p.latitude, lon: +p.longitude, p, sub: [p.zone === p.country ? '' : p.region, p.country].filter(Boolean).join(' · '), prof: p.max_depth, href: `#/punto?id=${p.id}` }));
        }
      } catch (e) { $('#wda-cuenta', root).textContent = T('No se ha podido cargar el mapa'); W.toast(e.message); return; }
      if (!vivo(root)) return;
      const capa = ex.ver === 'puntos' ? W.wdMarkerLayer() : L.layerGroup();
      // Several departures of the same centre share one marker (same place); its card shows the first one.
      const sitios = new Map();
      ex.todos.forEach((it) => {
        const lugar = it.tipo === 'punto' ? it.k : `${it.lat.toFixed(5)},${it.lon.toFixed(5)}`;
        let m = sitios.get(lugar);
        if (!m) {
          m = L.marker([it.lat, it.lon], { icon: it.tipo === 'punto' ? W.pointIcon(it.p) : ICONO_C(false), keyboard: true, title: it.nombre });
          m.on('click', () => sincronizar(it.k, true)); sitios.set(lugar, m); capa.addLayer(m);
        }
        ex.marcas.set(it.k, m);
      });
      ex.capa = capa.addTo(map);
      // Room for the search box on top and the sheet at the bottom.
      if (encuadrar && ex.todos.length && ex.todos.length < 400) { try { solo(() => map.fitBounds(L.latLngBounds(ex.todos.map((x) => [x.lat, x.lon])), { paddingTopLeft: [40, 170], paddingBottomRight: [90, 140], maxZoom: 11 })); } catch { /* nothing */ } }
      setTimeout(listar, 50);
    }
    function listar() {
      if (!vivo(root)) return;
      const b = map.getBounds();
      ex.vis = ex.todos.filter((x) => b.contains([x.lat, x.lon]));
      const n = ex.vis.length, nombre = ex.ver === 'centros' ? (n === 1 ? 'centro' : 'centros') : ex.ver === 'salidas' ? (n === 1 ? 'salida con plazas' : 'salidas con plazas') : (n === 1 ? 'punto de buceo' : 'puntos de buceo');
      $('#wda-cuenta', root).textContent = `${n.toLocaleString(W.wdLocale())} ${T(nombre)} ${T('en esta zona')}`;
      $('#wda-cuenta-sub', root).textContent = n > 80 ? T('Acércate al mapa para ver menos y más cerca.') : '';
      const lista = $('#wda-lista', root);
      lista.innerHTML = ex.vis.slice(0, 80).map((x) => `<a class="lista-fila" href="${x.href}">${x.tipo === 'punto' ? ic('pin') : x.tipo === 'centro' ? ic('tienda') : ic('barco')}<div class="crece pila"><b translate="no">${esc(x.nombre)}</b><span class="suave peq" translate="no">${esc(x.sub || '')}</span></div>${x.tipo === 'salida' && x.sal.price ? `<span class="peq num">${dinero(x.sal.price, x.sal.currency)}</span>` : ic('chev', 'chev')}</a>`).join('')
        || `<div class="vacio"><p>${esc(T('Nada en esta zona. Aleja el mapa o cambia el filtro.'))}</p></div>`;
      if (ex.ver === 'salidas' && ex.sinSitio?.length) {
        lista.insertAdjacentHTML('beforeend', `<p class="eti" style="padding:12px 14px 4px">${esc(T('Sin ubicación en el mapa'))}</p>` + ex.sinSitio.slice(0, 40).map((x) => `<button type="button" class="lista-fila" data-reservar="${x.slot_id}">${ic('barco')}<div class="crece pila"><b translate="no">${esc(x.title)}</b><span class="suave peq">${esc(cuando(x.date))} · ${esc(x.time || '')} · <span translate="no">${esc(x.provider_name || '')}</span></span></div>${x.price ? `<span class="peq num">${dinero(x.price, x.currency)}</span>` : ''}</button>`).join(''));
      }
      if (ex.sync && !ex.vis.some((x) => x.k === ex.sync)) { ex.sync = null; $('#wda-carrusel', root).hidden = true; }
    }
    // A marker and its card: tapping one moves the other.
    function sincronizar(k, desdeMapa) {
      const it = ex.todos.find((x) => x.k === k); if (!it) return;
      if (!ex.vis.some((x) => x.k === k)) listar();
      const cerca = ex.vis.length ? ex.vis : [it];
      const lote = cerca.length > 30 ? cerca.slice(Math.max(0, cerca.findIndex((x) => x.k === k) - 10)).slice(0, 30) : cerca;
      const car = $('#wda-carrusel', root);
      if (desdeMapa || car.hidden) {
        car.innerHTML = lote.map((x) => `<article class="tarjeta" data-k="${x.k}"><div class="mini">${x.tipo === 'centro' && x.logo ? `<img class="logo-c" src="${esc(x.logo)}" alt="">` : `<div class="wavatar">${ic(x.tipo === 'punto' ? 'pin' : x.tipo === 'centro' ? 'tienda' : 'barco', '')}</div>`}
          <div class="crece"><b translate="no">${esc(x.nombre)}</b><span class="suave peq" translate="no">${esc(x.sub || '')}</span>${x.prof ? `<span class="peq num"><span>hasta</span> ${esc(x.prof)} m</span>` : ''}${x.tipo === 'salida' && x.sal.price ? `<span class="precio">${dinero(x.sal.price, x.sal.currency)}</span>` : ''}</div></div>
          <div class="btn-fila mini-acc"><a class="wbtn sec mini" href="${x.href}">Ver ficha</a>${x.tipo === 'salida' ? `<button class="wbtn mini" type="button" data-reservar="${x.id}">Reservar</button>` : ''}</div></article>`).join('');
        W.translateTree(car);
      }
      ex.sync = k; car.hidden = false; altura('asomada');
      marcar(k);
      // The marker stays in sight: between the search box on top and the card at the bottom.
      try {
        const pt = map.latLngToContainerPoint([it.lat, it.lon]), alto = map.getSize().y, abajo = alto - 360, arriba = 190;
        if (pt.y > abajo) solo(() => map.panBy([0, pt.y - abajo], { animate: true })); else if (pt.y < arriba) solo(() => map.panBy([0, pt.y - arriba], { animate: true }));
      } catch { /* nothing */ }
      const card = car.querySelector(`[data-k="${k}"]`);
      if (card && desdeMapa) car.scrollTo({ left: card.offsetLeft - 24, behavior: 'smooth' });
    }
    function marcar(k) {
      const activa = k ? ex.marcas.get(k) : null;
      new Set(ex.marcas.values()).forEach((m) => { const el = m.getElement?.(); if (!el) return; const on = m === activa; el.querySelector('.wd-pin, .marca-c')?.classList.toggle('is-sync', on); el.classList.toggle('is-sync', on); });
    }
    let t0 = null;
    $('#wda-carrusel', root).addEventListener('scroll', (e) => {
      clearTimeout(t0); t0 = setTimeout(() => {
        const car = e.target, mid = car.scrollLeft + car.clientWidth / 2;
        let best = null, dist = 1e9; car.querySelectorAll('[data-k]').forEach((c) => { const d = Math.abs(c.offsetLeft + c.offsetWidth / 2 - mid); if (d < dist) { dist = d; best = c; } });
        if (!best || best.dataset.k === ex.sync) return;
        ex.sync = best.dataset.k; marcar(ex.sync);
        const it = ex.todos.find((x) => x.k === ex.sync); if (it) solo(() => map.panTo([it.lat, it.lon], { animate: true }));
      }, 140);
    }, { passive: true });
    map.on('click', () => { ex.sync = null; $('#wda-carrusel', root).hidden = true; marcar(null); });
    await cargar(ex.ver !== 'puntos' || !!ex.tipo);
    setTimeout(() => map.invalidateSize(), 120);
  }

  /* ---------------------------------------------------------------- Buscar */
  async function buscar() {
    const root = pintar(`<div class="cuerpo"><label class="buscador">${ic('buscar', '')}<span class="sr-only">Buscar</span><input id="wda-q" type="search" placeholder="Puntos, centros y experiencias" autocomplete="off" enterkeyhint="search"></label>
      <div id="wda-res" class="pila-12"><div class="tarjeta plana lista"><a class="lista-fila" href="#/experiencias">${ic('barco')}<span class="crece">Viajes y vida a bordo</span>${ic('chev', 'chev')}</a>
      <a class="lista-fila" href="#/top10">${ic('ubicacion')}<span class="crece">Top 10 cerca de ti</span>${ic('chev', 'chev')}</a><a class="lista-fila" href="#/centros">${ic('tienda')}<span class="crece">Todos los centros</span>${ic('chev', 'chev')}</a></div></div></div>`);
    const input = $('#wda-q', root), res = $('#wda-res', root), inicial = res.innerHTML;
    setTimeout(() => input.focus(), 60);
    let n = 0, t = null;
    input.addEventListener('input', () => { clearTimeout(t); t = setTimeout(ir, 220); });
    async function ir() {
      const q = input.value.trim(), k = ++n;
      if (q.length < 2) { res.innerHTML = inicial; W.translateTree(res); return; }
      const f = W.wdFold(q), palabras = f.split(/\s+/);
      const [capa, centros] = await Promise.allSettled([W.loadMapLayer(), api('/api/centers?q=' + encodeURIComponent(q))]);
      if (k !== n || !vivo(res)) return;
      const puntos = capa.status === 'fulfilled' ? (capa.value.items || []).filter((p) => { const txt = W.wdFold([p.name, p.country, p.region, p.zone].join(' ')); return palabras.every((w) => txt.includes(w)); }).slice(0, 8) : [];
      const cs = centros.status === 'fulfilled' ? (centros.value.items || []).slice(0, 8) : [];
      const fila = (href, icono, a, b) => `<a class="lista-fila" href="${href}">${ic(icono)}<div class="crece pila"><b translate="no">${esc(a)}</b><span class="suave peq" translate="no">${esc(b || '')}</span></div>${ic('chev', 'chev')}</a>`;
      res.innerHTML = (cs.length ? `<section class="pila-8"><h2>Centros</h2><div class="tarjeta plana lista">${cs.map((c) => fila(`#/centro?id=${c.id}`, 'tienda', c.name, [c.city, c.country].filter(Boolean).join(' · '))).join('')}</div></section>` : '')
        + (puntos.length ? `<section class="pila-8"><h2>Puntos de buceo</h2><div class="tarjeta plana lista">${puntos.map((p) => fila(`#/punto?id=${p.id}`, 'pin', p.name, [p.region, p.country].filter(Boolean).join(' · '))).join('')}</div></section>` : '')
        || `<div class="tarjeta vacio"><p>No hay resultados. Prueba con el nombre de una zona o de un país.</p></div>`;
      W.translateTree(res);
    }
  }

  /* ---------------------------------------------------------------- fichas of the web: actions and the fixed bar */
  async function decorarFicha(nombre, params) {
    const id = Number(params.get('id') || 0); if (!id) return;
    const app = $('#app'); const marca = 'wda-ficha-' + nombre + id;
    let datos = null, salidas = [];
    try {
      if (nombre === 'centro') {
        const [c, s] = await Promise.allSettled([api('/api/centers/' + id), api('/api/provider-services?provider_id=0&center_id=' + id)]);
        const x = c.status === 'fulfilled' ? c.value.item : null; if (!x) return;
        datos = { nombre: x.name, tel: x.phone, lat: x.latitude, lon: x.longitude, dir: [x.address, x.city, x.country].filter(Boolean).join(', '), url: `${location.origin}/#/centro?id=${id}` };
        salidas = s.status === 'fulfilled' ? (s.value.items || []) : [];
      } else if (nombre === 'profesional') {
        const p = await api('/api/providers/' + id);
        datos = { nombre: p.fullname, tel: null, lat: null, lon: null, dir: '', url: `${location.origin}/#/profesional?id=${id}` };
        salidas = (await api('/api/provider-services?provider_id=' + id).catch(() => ({ items: [] }))).items || [];
      } else if (nombre === 'punto') {
        const p = (await W.loadMapLayer()).items.find((x) => String(x.id) === String(id));
        datos = p ? { nombre: p.name, tel: null, lat: p.latitude, lon: p.longitude, dir: '', url: `${location.origin}/#/punto?id=${id}` } : null;
      }
    } catch { return; }
    if (!datos || !$('#app') || app.dataset.ficha === marca) return;
    if (nombreRuta() !== nombre) return;
    app.dataset.ficha = marca;
    const llegar = mapsDestino({ lat: datos.lat, lon: datos.lon, direccion: datos.dir });
    const box = document.createElement('div'); box.className = 'wda wda-ficha';
    box.innerHTML = nombre === 'punto' ? `<div class="acciones dos"><button class="accion" type="button" data-llegar ${llegar ? '' : 'aria-disabled="true"'}>${ic('ruta')}<span>Cómo llegar</span></button>
      <button class="accion" type="button" data-compartir>${ic('compartir')}<span>Compartir</span></button></div>` : `<div class="acciones">${datos.tel ? `<a class="accion" href="tel:${esc(String(datos.tel).replace(/[^\d+]/g, ''))}">${ic('tel')}<span>Llamar</span></a>` : `<span class="accion" aria-disabled="true">${ic('tel')}<span>Llamar</span></span>`}
      <button class="accion wa" type="button" data-wa ${telefonoWa(datos.tel) ? '' : 'aria-disabled="true"'}>${ic('wa')}<span>WhatsApp</span></button>
      <button class="accion" type="button" data-llegar ${llegar ? '' : 'aria-disabled="true"'}>${ic('ruta')}<span>Cómo llegar</span></button>
      <button class="accion" type="button" data-compartir>${ic('compartir')}<span>Compartir</span></button></div>`;
    // Under the page's header (name, photo), where the prototype has them; otherwise at the top.
    const ancla = app.querySelector('header, [class*="hero"]'), sitio = app.querySelector('.global-back');
    if (ancla) ancla.after(box); else if (sitio) sitio.after(box); else app.prepend(box);
    W.translateTree(box);
    if ($('[data-wa]', box)) $('[data-wa]', box).onclick = () => telefonoWa(datos.tel) ? whatsappCentro({ nombre: datos.nombre, telefono: datos.tel }) : W.toast('Este centro no tiene un móvil con prefijo internacional.');
    $('[data-llegar]', box).onclick = () => llegar ? abrirFuera(llegar) : W.toast('Sin dirección publicada.');
    $('[data-compartir]', box).onclick = () => compartir({ titulo: datos.nombre, texto: datos.nombre + ' · WORLDIVES', url: datos.url });
    // The fixed bar «Desde X € · Reservar»: the cheapest open departure with places.
    const abiertas = [];
    salidas.filter((s) => s.service_type !== 'alquiler_equipo').forEach((s) => (s.slots || []).forEach((sl) => { if (sl.status === 'open' && Number(sl.spots_available) > 0) abiertas.push({ s, sl }); }));
    const precios = salidas.map((s) => Number(s.price)).filter((p) => p > 0);
    if (nombre === 'punto') return;
    const desde = precios.length ? Math.min(...precios) : null, cur = salidas[0]?.currency || 'EUR';
    const reservarHref = nombre === 'centro' ? `#/reservar?center=${id}` : `#/reservar?provider=${id}`;
    const barra = document.createElement('div'); barra.className = 'wda wda-barra'; barra.id = 'wda-barra';
    barra.innerHTML = `<div class="crece">${desde != null ? `<span class="suave">Desde</span><p class="precio">${dinero(desde, cur)}</p>` : `<span class="suave">${abiertas.length ? 'Salidas con plazas' : 'Sin salidas publicadas ahora'}</span>`}</div><a class="wbtn grande" href="${reservarHref}">Reservar</a>`;
    document.body.appendChild(barra); document.documentElement.classList.add('wda-con-barra');
    W.translateTree(barra);
  }
  function quitarBarra() { $('#wda-barra')?.remove(); document.documentElement.classList.remove('wda-con-barra'); const app = $('#app'); if (app) delete app.dataset.ficha; }

  /* ---------------------------------------------------------------- Reservas */
  async function reservas() {
    if (!state.me) { pintar(pedirEntrar(T('Reservas'), T('Entra para ver tus reservas, pagar las pendientes y enseñar el QR en el barco.'))); return; }
    if (rol() !== 'recreational') { location.replace('#/admin'); return; }
    const root = pintar(`<div class="cuerpo"><h1>Reservas</h1><div class="seg" role="group" aria-label="Reservas"><button type="button" data-seg="prox" aria-pressed="true">Próximas</button><button type="button" data-seg="hist" aria-pressed="false">Historial</button></div><div id="wda-res" class="pila-12">${esqueleto(2)}</div></div>`);
    let d, viejo = null;
    const clave = 'wda-res:' + state.me.user.id;
    try { d = await miArea(true); try { localStorage.setItem(clave, JSON.stringify({ at: Date.now(), d: { bookings: d.bookings || [], experience_bookings: d.experience_bookings || [] } })); } catch { /* storage full */ } }
    catch (e) {
      // v50.49: without coverage (on the boat) the bookings and their QR codes saved on this phone are shown.
      let c = null; try { c = !e.status ? JSON.parse(localStorage.getItem(clave) || 'null') : null; } catch { /* nothing */ }
      if (!c) { $('#wda-res', root).innerHTML = `<div class="tarjeta vacio"><p>${esc(e.message)}</p></div>`; return; }
      d = c.d; viejo = c.at;
    }
    if (!vivo(root)) return;
    if (viejo) $('#wda-res', root).insertAdjacentHTML('beforebegin', `<div class="aviso pend">${ic('alerta')}<div><span>${T('Sin conexión: datos guardados en el móvil a las')}</span> <span class="num">${new Date(viejo).toLocaleTimeString(W.wdLocale(), { hour: '2-digit', minute: '2-digit' })}</span>.</div></div>`);
    const todas = d.bookings || [];
    if (!viejo) todas.filter((b) => vigente(b) && !porPagar(b)).slice(0, 6).forEach(guardarQR);
    const prox = todas.filter(vigente).sort((a, b) => String(a.booking_date + a.booking_time).localeCompare(String(b.booking_date + b.booking_time)));
    const hist = todas.filter((b) => !vigente(b));
    const fila = (b) => {
      const dt = new Date((b.booking_date || W.wdToday()) + 'T12:00:00');
      return `<article class="tarjeta pad pila-12"><a class="fila" href="#/reserva?id=${b.id}" style="color:inherit;text-decoration:none"><div class="fecha-b"><b class="num">${dt.getDate()}</b><small translate="no">${esc(dt.toLocaleDateString(W.wdLocale(), { month: 'short' }).replace('.', ''))}</small></div>
        <div class="crece pila"><b${b.service_title ? ' translate="no"' : ''}>${esc(b.service_title || 'Inmersión')}</b><span class="suave peq"><span translate="no">${esc(b.center_name || '')}</span>${b.booking_time ? ' · ' + esc(b.booking_time) : ''} · <span class="num">${b.participants || 1}</span> <span>${Number(b.participants) === 1 ? 'buceador' : 'buceadores'}</span></span>
        <div class="wtags">${estadoTag(b)}${personaTag(b)}${Number(b.price) > 0 && b.payment_status === 'paid' ? `<span class="wtag ok">${ic('cobrar', '')}Pagada</span>` : ''}</div></div>${ic('chev', 'chev')}</a>
        ${porPagar(b) ? `<a class="wbtn ancho grande pagar-ya" href="#/reserva?id=${b.id}">${ic('cobrar', '')}<span>Pagar</span> <span class="num">${dinero(Number(b.amount_due) > 0 ? b.amount_due : b.price, b.currency)}</span></a>
          ${b.payment_deadline ? `<p class="cuenta-atras" data-hasta="${esc(b.payment_deadline)}" role="timer" aria-live="off"></p>` : ''}` : ''}
        ${vigente(b) ? `<div class="btn-fila envolver">${porPagar(b) ? '' : `<button class="wbtn sec mini" type="button" data-qr="${b.id}">${ic('qr', '')}Ver QR</button>`}<button class="wbtn sec mini" type="button" data-wa="${b.id}">${ic('wa', '')}WhatsApp</button>${porPagar(b) ? '' : `<button class="wbtn sec mini" type="button" data-cal="${b.id}">${ic('agenda', '')}Calendario</button>`}</div>` : ''}
        ${!vigente(b) && repetirHref(b) ? `<div class="btn-fila"><a class="wbtn sec mini" href="${repetirHref(b)}">${ic('reloj', '')}Repetir reserva</a></div>` : ''}</article>`;
    };
    const pintarLista = (k) => {
      const lista = k === 'prox' ? prox : hist, box = $('#wda-res', root);
      box.innerHTML = lista.length ? lista.map(fila).join('') : `<div class="tarjeta vacio"><p>${k === 'prox' ? 'No tienes reservas próximas.' : 'Aquí verás las inmersiones que ya has hecho.'}</p>${k === 'prox' ? '<a class="wbtn mini" href="#/">Buscar una salida</a>' : ''}</div>`;
      const exps = d.experience_bookings || [];
      if (k === 'prox' && exps.length) box.insertAdjacentHTML('beforeend', `<h2>Viajes y vida a bordo</h2><div class="tarjeta plana lista">${exps.map((e) => `<div class="lista-fila">${ic('barco')}<div class="crece pila"><b translate="no">${esc(e.title)}</b><span class="suave peq">${esc(e.start_date ? fecha(e.start_date, { day: 'numeric', month: 'short', year: 'numeric' }) : '')}</span></div><span class="wtag neutro">${esc(W.experienceStatus(e.status)[0])}</span></div>`).join('')}</div>`);
      W.translateTree(box);
      $$('[data-wa]', box).forEach((b) => { b.onclick = () => whatsappReserva(todas.find((y) => String(y.id) === b.dataset.wa)); });
      $$('[data-qr]', box).forEach((b) => { b.onclick = () => verQR(todas.find((y) => String(y.id) === b.dataset.qr)); });
      $$('[data-cal]', box).forEach((b) => { b.onclick = () => alCalendario(todas.find((y) => String(y.id) === b.dataset.cal)); });
      cuentasAtras(box);
    };
    $$('[data-seg]', root).forEach((b) => { b.onclick = () => { $$('[data-seg]', root).forEach((x) => x.setAttribute('aria-pressed', String(x === b))); pintarLista(b.dataset.seg); }; });
    $('[data-seg="prox"]', root).insertAdjacentHTML('beforeend', ` <span class="num">${prox.length}</span>`);
    $('[data-seg="hist"]', root).insertAdjacentHTML('beforeend', ` <span class="num">${hist.length}</span>`);
    pintarLista('prox');
  }

  // v50.55 (brief de la app, «Mis reservas»): the time left to pay, under the big «Pagar» button; it updates by itself.
  function cuentasAtras(box) {
    const pinta = () => {
      if (!box.isConnected) return false;
      $$('.cuenta-atras', box).forEach((el) => {
        const ms = new Date(el.dataset.hasta) - Date.now();
        if (!Number.isFinite(ms)) { el.textContent = ''; return; }
        if (ms <= 0) { el.textContent = T('El plazo para pagar ha terminado.'); el.classList.add('vencido'); return; }
        const min = Math.ceil(ms / 60000), h = Math.floor(min / 60), d = Math.floor(h / 24);
        const resto = d >= 1 ? `${d} d ${h % 24} h` : h >= 1 ? `${h} h ${min % 60} min` : `${min} min`;
        el.innerHTML = `${esc(T('Tiempo para pagar'))}: <b class="num">${resto}</b>`;
        el.classList.toggle('urg', min < 180);
      });
      return true;
    };
    if (!pinta()) return;
    const t = setInterval(() => { if (!pinta()) clearInterval(t); }, 30000);
  }
  // «Repetir reserva» from the history: the same activity with the same centre (or the professional's page).
  function repetirHref(b) {
    if (b.center_id && b.service_id) return `#/reservar?center=${b.center_id}&service=${b.service_id}`;
    if (b.center_id) return `#/centro?id=${b.center_id}`;
    if (b.provider_user_id) return `#/profesional?id=${b.provider_user_id}`;
    return '';
  }
  // «Añadir al calendario»: the phone's calendar app (Google Calendar) with the activity at the centre's local hour.
  function alCalendario(b) {
    if (!b?.booking_date) return;
    const hora = /^\d{2}:\d{2}/.test(b.booking_time || '') ? b.booking_time.slice(0, 5) : '09:00';
    const ini = new Date(`${b.booking_date}T${hora}:00Z`), fin = new Date(ini.getTime() + (Number(b.service_duration) || 180) * 60000);
    const f = (d) => d.toISOString().replace(/[-:]/g, '').slice(0, 15);   // the same digits as the local hour: «ctz» says its zone
    const txt = [b.service_title || T('Inmersión'), b.center_name].filter(Boolean).join(' · ');
    const lugar = [b.point_name, b.center_address, b.city].filter(Boolean).join(', ');
    const det = `${T('Reserva')} #${b.id} · WORLDIVES`;
    const url = `https://calendar.google.com/calendar/render?action=TEMPLATE&text=${encodeURIComponent(txt)}&dates=${f(ini)}/${f(fin)}&ctz=${encodeURIComponent(b.service_timezone || 'Europe/Madrid')}&details=${encodeURIComponent(det)}&location=${encodeURIComponent(lugar)}`;
    abrirFuera(url);
  }
  // The QR of a booking and its code, kept on the phone: they are shown on the boat without coverage.
  async function guardarQR(b) {
    const k = 'wda-qr-' + b.id;
    try { if (JSON.parse(localStorage.getItem(k) || 'null')) return; } catch { /* nothing */ }
    try {
      const [svg, det] = await Promise.all([fetch(`/api/bookings/${b.id}/qr.svg`, { credentials: 'same-origin' }).then((r) => (r.ok ? r.text() : null)), api('/api/bookings/' + b.id)]);
      const code = det?.check_code || det?.booking?.check_code || '';
      if (svg && svg.startsWith('<')) localStorage.setItem(k, JSON.stringify({ svg, code, at: Date.now() }));
    } catch { /* tried again next time */ }
  }
  async function verQR(b) {
    if (!b) return;
    let c = null; try { c = JSON.parse(localStorage.getItem('wda-qr-' + b.id) || 'null'); } catch { /* nothing */ }
    if (!c) { await guardarQR(b); try { c = JSON.parse(localStorage.getItem('wda-qr-' + b.id) || 'null'); } catch { /* nothing */ } }
    if (!c) { location.hash = '#/reserva?id=' + b.id; return; }
    abrirHoja({ titulo: T('Tu QR para el barco'), sub: `<span translate="no">${esc(b.service_title || '')} · ${esc(b.center_name || '')}</span>`,
      html: `<div class="pila-12" style="text-align:center"><img alt="${T('QR de la reserva')}" src="data:image/svg+xml;base64,${btoa(unescape(encodeURIComponent(c.svg)))}" style="width:min(280px,80vw);background:#fff;padding:12px;border-radius:16px;margin:0 auto">
        ${c.code ? `<p><span>${T('Código')}</span>: <b class="num" translate="no" style="font-size:22px;letter-spacing:.08em">${esc(c.code)}</b></p>` : ''}<p class="suave peq">${T('Funciona sin conexión: está guardado en este móvil.')}</p>
        <a class="wbtn sec ancho" href="#/reserva?id=${b.id}">${T('Ver la reserva completa')}</a></div>` });
  }

  /* ---------------------------------------------------------------- Buddies (v50.57): the ones of the Log Book */
  // Your QR (scanned with a phone, you become buddies both ways) and your buddies, from the Log Book. Groups and
  // «¿Buceamos?» come with the Buddies brief: still pending on the server.
  async function buddies() {
    const logbook = `<div class="tarjeta plana lista"><a class="lista-fila" href="#/logbook">${ic('libro')}<div class="crece pila"><b>Log Book</b><span class="suave peq">Tus inmersiones y con quién buceaste</span></div>${ic('chev', 'chev')}</a></div>`;
    pintar(`<div class="cuerpo"><h1>Buddies</h1><p class="suave">${T('Cargando…')}</p></div>`);
    let d = null;
    try { d = await api('/api/logbook'); } catch { /* without connection: only the link to the Log Book */ }
    const lista = (d?.friends || []).map((f) => `<div class="lista-fila">${ic('buddies')}<div class="crece pila"><b translate="no">${esc(f.name)}</b></div></div>`).join('');
    pintar(`<div class="cuerpo"><h1>Buddies</h1>
      ${d ? `<div class="tarjeta pad wda-buddy-qr"><img src="${esc(d.profile.qrImage)}" alt="Tu QR de buddy" width="180" height="180"><p class="suave peq">Enséñale este QR a tu compañero: al escanearlo con su móvil seréis buddies, y aparecerá en «Compañero» de vuestro Log Book.</p></div>
        <div class="tarjeta plana lista">${lista || '<p class="suave pad">Todavía no tienes buddies.</p>'}</div>` : ''}
      <div class="pendiente"><b>Pendiente.</b> Los grupos y «¿Buceamos?» llegan con el encargo de Buddies.</div>${logbook}</div>`);
  }

  /* ---------------------------------------------------------------- Mi área and Ajustes */
  // v50.58 (equipo por QR): «Trabajar como» (the profile selector: one's own profile or a centre where one works today),
  // «Mi QR», «Mi equipo» and «Mi agenda». The same screens as the web; the server decides who sees what.
  function filasEquipo() {
    const me = state.me; if (!me) return '';
    const own = me.own_role || me.user.role; if (!['freelance', 'recreational', 'center'].includes(own)) return '';
    const n = me.team_requests || 0, perfiles = me.profiles || [], actual = perfiles.find((p) => p.active);
    const fila = (href, icono, a, b) => `<a class="lista-fila" href="${href}">${ic(icono)}<span class="crece pila"><b>${a}</b><span class="suave peq">${b}</span></span>${ic('chev', 'chev')}</a>`;
    return (perfiles.length > 1 ? `<button class="lista-fila" type="button" id="wda-perfil">${ic('mover')}<span class="crece pila"><b>${T('Trabajar como')}</b><span class="suave peq" ${actual?.center_id ? 'translate="no"' : ''}>${esc(actual?.label || '')}</span></span>${ic('chev', 'chev')}</button>` : '')
      + fila('#/mi-qr', 'qr', T('Mi QR'), T('Para que un centro te añada a su equipo'))
      + (own !== 'center' ? fila('#/mi-equipo', 'equipo', T('Mi equipo') + (n ? ` <span class="wda-num-aviso">${n}</span>` : ''), T('Peticiones y centros donde trabajas'))
        + fila('#/mi-agenda', 'agenda', T('Mi agenda'), T('Lo que te toca en cada centro')) : '');
  }
  function enlazarPerfil(root) {
    $('#wda-perfil', root)?.addEventListener('click', () => {
      const perfiles = state.me?.profiles || [];
      const capa = abrirHoja({ titulo: T('Trabajar como'), sub: T('Cada centro, con lo que permite tu perfil. Nunca se mezclan.'), html: `<div class="tarjeta plana lista">${perfiles.map((p) => `<button class="lista-fila" type="button" data-p="${p.center_id || 0}"><span class="wda-color" style="--c:${esc(p.color || '#334155')}" aria-hidden="true"></span><span class="crece pila"><b ${p.center_id ? 'translate="no"' : ''}>${esc(p.label)}</b>${p.role_name ? `<span class="suave peq">${esc(p.role_name)}</span>` : ''}</span>${p.active ? ic('check', '') : ''}</button>`).join('')}</div>` });
      $$('[data-p]', capa).forEach((b) => { b.onclick = async () => {
        try { await postJSON('/api/team/switch', { center: +b.dataset.p }); await W.loadMe(); cerrarHoja(); W.toast(T(+b.dataset.p ? 'Ahora trabajas en este centro.' : 'Has vuelto a tu perfil.')); if (['', '#/', '#'].includes(location.hash)) W.route(); else location.hash = '#/'; }
        catch (e) { W.toast(e.message); }
      }; });
    });
  }
  async function miAreaPantalla() {
    const me = state.me;
    if (!me) { pintar(pedirEntrar(T('Mi área'), T('Entra para ver tu Log Book, tus puntos, tu ficha y tus ajustes.')) + `<div class="cuerpo" style="padding-top:0"><a class="wbtn sec ancho" href="#/ajustes">${ic('ajustes', '')}Ajustes</a></div>`); return; }
    const u = me.user, buzo = u.role === 'recreational';
    const perfil = { recreational: 'Buceador', center: 'Centro PRO', freelance: 'Freelance PRO', admin: 'Administración' }[u.role] || 'Buceador';
    const fila = (href, icono, a, b = '') => `<a class="lista-fila" href="${href}">${ic(icono)}<div class="crece pila"><b>${a}</b>${b ? `<span class="suave peq">${b}</span>` : ''}</div>${ic('chev', 'chev')}</a>`;
    const root = pintar(`<header class="cab"><div class="cab-fila"><div class="wavatar" style="width:64px;height:64px;font-size:var(--t-l)">${esc(W.initials(u.fullname))}</div><div class="crece pila"><h1 style="font-size:var(--t-l)" translate="no">${esc(u.fullname)}</h1>
        <span class="suave peq">${me.profile?.certification_name ? `<span translate="no">${esc(me.profile.certification_name)}</span>` : `<span>${perfil}</span>`}</span></div></div>
        ${buzo ? '<div class="cifras"><div class="tarjeta cifra"><b id="wda-c-puntos">—</b><span>Puntos disponibles</span></div><div class="tarjeta cifra"><b id="wda-c-log">—</b><span>inmersiones en el Log Book</span></div></div>' : ''}</header>
      <div class="cuerpo"><p class="eti">Perfil: <span>${perfil}</span></p>
        <div class="tarjeta plana lista">${buzo ? fila('#/logbook', 'libro', 'Log Book', 'Tus inmersiones') + fila('#/mis-puntos', 'puntos', 'Mis puntos', 'Cómo se ganan y se canjean') + fila('#/recompensas', 'regalo', 'Recompensas', 'Ventajas de cada centro')
          + fila('#/area', 'avisos', 'Avisos y documentos', 'Mensajes de los centros, titulación y seguro') : fila('#/admin', 'agenda', u.role === 'admin' ? 'Administración' : 'Mi panel', 'En la web, dentro de la app')}
          ${fila('#/cuenta', 'ficha', buzo ? 'Mi ficha' : 'Mi cuenta', buzo ? 'Titulación, tallas, teléfono y WhatsApp' : 'Datos, seguridad e idioma')}${fila('#/ajustes', 'ajustes', 'Ajustes', 'Tema, tamaño del texto, idioma y cuenta')}</div>
        ${filasEquipo() ? `<p class="eti">Equipos de centros</p><div class="tarjeta plana lista">${filasEquipo()}</div>` : ''}
        <button class="wbtn sec ancho" type="button" id="wda-salir">${ic('salir', '')}Cerrar sesión</button></div>`);
    $('#wda-salir', root).onclick = salir; enlazarPerfil(root);
    if (buzo) {
      api('/api/points').then((d) => { const el = $('#wda-c-puntos', root); if (el) el.textContent = Number(d.balance || 0).toLocaleString(W.wdLocale()); }).catch(() => {});
      api('/api/logbook').then((d) => { const el = $('#wda-c-log', root); if (el) el.textContent = (d.items || []).length.toLocaleString(W.wdLocale()); }).catch(() => {});
    }
  }
  async function salir() {
    // Check-ins made without coverage and not sent yet would be lost with the session (they are forgotten below).
    let pend = 0; try { pend = (JSON.parse(localStorage.getItem('wda-pro-cola') || '[]') || []).length; } catch { /* nothing */ }
    if (pend && !await W.wdConfirm({ title: 'Cerrar sesión', text: 'Hay cambios de check-in sin enviar. Si cierras sesión ahora, se perderán.', ok: 'Cerrar sesión', danger: true })) return;
    let t = null; try { t = localStorage.getItem('wda-push'); } catch { /* nothing */ }
    if (t) await postJSON('/api/app/push/unregister', { token: t }).catch(() => {});
    pushHecho = false;
    try { await postJSON('/api/auth/logout', {}); } catch { /* the session ends anyway */ }
    window.wdForgetDevice?.();   // ASVS V14.3.1: bookings, QR codes and lists kept on the phone go with the session
    await window.WD_SEC?.olvidar?.();   // v50.55: and the device's token and keys
    state.me = null; mem.area = null; cuenta.reservas = 0; await W.loadMe(); location.hash = '#/';
  }
  let webVersion = null;
  async function infoApp() {
    const A = plugin('App'), D = plugin('Device');
    const [a, d, h] = await Promise.all([A?.getInfo?.().catch(() => null), D?.getInfo?.().catch(() => null), webVersion ? { version: webVersion } : api('/api/health').catch(() => ({}))]);
    webVersion = h?.version || webVersion;
    return { version: (a ? `${a.name} ${a.version} (${a.build})` : 'WORLDIVES') + (webVersion ? ` · web v${webVersion}` : ''),
      movil: d ? `${d.manufacturer || ''} ${d.model || ''} · ${d.operatingSystem || ''} ${d.osVersion || ''}`.trim() : navigator.userAgent.slice(0, 140) };
  }
  async function ajustes() {
    const lang = W.currentLanguage(), me = state.me;
    const seg = (k, opciones, actual, etiqueta) => `<div class="seg" role="group" aria-label="${etiqueta}">${opciones.map(([v, t]) => `<button type="button" data-${k}="${v}" aria-pressed="${actual === v}">${t}</button>`).join('')}</div>`;
    const fila = (href, icono, a, b = '', extra = '') => `<a class="lista-fila" href="${href}" ${extra}>${ic(icono)}<div class="crece pila"><b>${a}</b>${b ? `<span class="suave peq">${b}</span>` : ''}</div>${ic('chev', 'chev')}</a>`;
    const root = pintar(`<div class="cuerpo"><h1>Ajustes</h1>
      <section class="pila-8"><p class="eti">Apariencia</p>${seg('tema', [['clasico', 'Clásico'], ['noche', 'Noche'], ['auto', 'Automático']], pref('tema', 'clasico', TEMAS), 'Tema')}
        <p class="eti">Tamaño del texto</p>${seg('tamano', [['normal', 'Normal'], ['grande', 'Grande'], ['enorme', 'Enorme']], pref('tamano', 'normal', TAMANOS), 'Tamaño del texto')}</section>
      <section class="pila-8"><p class="eti">Idioma</p>${seg('lang', W.APP_LANGS.map((l) => [l, W.LANGS[l]]), lang, 'Idioma')}<p class="suave peq">De momento la app está en español, inglés y francés. La web sigue en sus 9 idiomas.</p></section>
      <section class="tarjeta plana lista">${me ? fila('#/cuenta', 'ficha', 'Mi cuenta', 'Datos, contraseña, sesiones abiertas y avisos') : fila('#/login', 'entrar', 'Entrar', 'O crear una cuenta')}${fila('#/legal', 'documento', 'Privacidad y textos legales')}</section>
      ${me && window.WD_SEC ? '<section class="pila-8" id="wda-seg"></section>' : ''}
      ${APP.pruebas ? `<section class="pila-8"><p class="eti">Solo en WORLDIVES Pruebas</p><div class="tarjeta plana lista"><button class="lista-fila" type="button" id="wda-r-fallo">${ic('bug')}<div class="crece pila"><b>Reportar fallo</b><span class="suave peq">También agitando el móvil</span></div>${ic('chev', 'chev')}</button>
        <button class="lista-fila" type="button" id="wda-r-servidor">${ic('servidor')}<div class="crece pila"><b>Cambiar de servidor o de cuenta de prueba</b><span class="suave peq" translate="no">${esc(location.origin)}</span></div>${ic('chev', 'chev')}</button></div></section>` : ''}
      ${me ? `<section class="pila-8"><button class="wbtn sec ancho" type="button" id="wda-salir">${ic('salir', '')}Cerrar sesión</button><button class="wbtn peligro ancho" type="button" id="wda-borrar">${ic('papelera', '')}Borrar mi cuenta</button></section>` : ''}
      <p class="version" id="wda-version" translate="no">WORLDIVES</p></div>`);
    $$('[data-tema]', root).forEach((b) => { b.onclick = () => { guardarPref('tema', b.dataset.tema); aplicarAspecto(); $$('[data-tema]', root).forEach((x) => x.setAttribute('aria-pressed', String(x === b))); }; });
    $$('[data-tamano]', root).forEach((b) => { b.onclick = () => { guardarPref('tamano', b.dataset.tamano); aplicarAspecto(); $$('[data-tamano]', root).forEach((x) => x.setAttribute('aria-pressed', String(x === b))); }; });
    $$('[data-lang]', root).forEach((b) => { b.onclick = async () => {
      if (b.dataset.lang === lang) return;
      try { localStorage.setItem(W.LANG_KEY, b.dataset.lang); } catch { /* nothing */ }
      if (me) await postJSON('/api/account/language', { lang: b.dataset.lang }).catch(() => {});
      location.href = location.pathname + '?lang=' + encodeURIComponent(b.dataset.lang) + location.hash;
    }; });
    $('#wda-salir', root)?.addEventListener('click', salir);
    $('#wda-borrar', root)?.addEventListener('click', borrarCuenta);
    $('#wda-r-fallo', root)?.addEventListener('click', () => reportarFallo());
    $('#wda-r-servidor', root)?.addEventListener('click', async () => {
      const S = plugin('Servidor'); if (!S) { W.toast('Solo dentro de la app de pruebas.'); return; }
      // v50.55: changing server or test account ends this session on the phone (token, keys and saved data)
      if (state.me) await postJSON('/api/auth/logout', {}).catch(() => {});
      await window.WD_SEC?.olvidar?.('cambio_de_servidor');   // also a session the page had not loaded yet
      await S.olvidar();
    });
    if ($('#wda-seg', root)) seguridadAjustes($('#wda-seg', root));
    const info = await infoApp(); const v = $('#wda-version', root);
    if (v) v.textContent = info.version;
  }
  // v50.55 (encargo 2): how this phone opens the app, and where the account is signed in.
  async function seguridadAjustes(box) {
    const st = await window.WD_SEC.estado(); if (!st || !vivo(box)) return;
    const pro = window.WD_SEC.PRO(rol());
    const modo = st.modo === 'pin' ? T('PIN de la app (6 números)') : st.modo === 'sistema' ? T('Huella, cara o el código del móvil') : T('Sin bloqueo');
    box.innerHTML = `<p class="eti">${T('Seguridad')}</p><div class="tarjeta plana lista">
      <div class="lista-fila">${ic('candado')}<div class="crece pila"><b>${T('Bloqueo de la app')}</b><span class="suave peq">${esc(modo)}${st.token ? '' : ' · ' + esc(T('se activa al volver a entrar'))}</span>
        <span class="suave peq">${pro ? esc(T('Siempre activado en las cuentas de centros y profesionales.')) : esc(T('Pide tu huella o el código al abrir la app y al volver después de 5 minutos.'))}</span></div>
        ${pro ? '' : `<label class="interruptor"><span class="sr-only">${T('Bloqueo de la app')}</span><input type="checkbox" id="wda-seg-bloqueo" ${st.modo && st.modo !== 'libre' ? 'checked' : ''}></label>`}</div>
      <a class="lista-fila" href="#/cuenta?dispositivos=1">${ic('tel')}<div class="crece pila"><b>${T('Dispositivos conectados')}</b><span class="suave peq">${T('Dónde está abierta tu cuenta y cerrar sesión a distancia')}</span></div>${ic('chev', 'chev')}</a></div>
      ${APP.pruebas ? `<p class="suave peq">${T('Solo en Pruebas')}: ${T('bloqueo tras')} <span class="num">${st.umbral}</span> s · ${T('intentos fallidos')}: <span class="num">${st.fallos}</span> / ${st.maxFallos}</p>` : ''}`;
    W.translateTree(box);
    $('#wda-seg-bloqueo', box)?.addEventListener('change', async (e) => {
      const r = await window.WD_SEC.cambiarBloqueo(e.target.checked).catch((err) => ({ error: err?.message }));
      if (!r?.ok) { e.target.checked = !e.target.checked; W.toast(T('No se ha podido cambiar el bloqueo.')); }
      else W.toast(e.target.checked ? T('Bloqueo activado.') : T('Bloqueo desactivado.'));
      seguridadAjustes(box);
    });
  }
  function borrarCuenta() {
    // v50.49: centres (their owner) and freelance close the account in «Más» (six months to come back).
    if (rol() === 'freelance' || (rol() === 'center' && (state.me?.member_role || 'owner') === 'owner')) { location.hash = '#/cerrar-cuenta'; return; }
    if (rol() !== 'recreational') { W.toast(T('Solo el propietario del centro puede cerrar la cuenta del centro.')); return; }
    const capa = abrirHoja({ titulo: T('¿Borrar tu cuenta?'), sub: T('Esta acción no se puede deshacer.'),
      html: `<div class="aviso urg">${ic('alerta')}<div>${T('Borraremos tu ficha, tu documentación, tu Log Book, tus mensajes y tus recompensas. Las reservas pasadas se conservan sin tu nombre, porque la ley obliga a guardar los datos de los pagos. Si tienes reservas próximas, cancélalas antes.')}</div></div>
        <div class="campo"><label for="wda-del-pw">${T('Escribe tu contraseña para confirmar')}</label><input id="wda-del-pw" type="password" autocomplete="current-password"></div>`,
      pie: `<button class="wbtn peligro ancho grande" type="button" id="wda-del-ok">${T('Sí, borrar mi cuenta')}</button><button class="wbtn sec ancho" type="button" data-cerrar>${T('No, volver')}</button>` });
    $('#wda-del-ok', capa).onclick = async () => {
      try {
        const r = await postJSON('/api/account/delete', { password: $('#wda-del-pw', capa).value }); cerrarHoja();
        if (r && r.email_sent) { W.toast('Te hemos enviado un email para confirmar la eliminación. El enlace caduca en 24 horas.'); return; }
        state.me = null; await W.loadMe(); W.toast('Tu cuenta se ha eliminado.'); location.hash = '#/';
      } catch (e) { W.toast(e.message); }
    };
  }

  /* ---------------------------------------------------------------- WORLDIVES Pruebas only */
  async function reportarFallo() {
    if (!APP.pruebas) return;
    if (hoja && $('#wda-enviar-fallo')) return;
    let captura = null;
    const S = plugin('Servidor');
    if (S?.captura) { try { captura = (await S.captura()).captura; } catch { /* without screenshot */ } }
    const info = await infoApp();
    const pantalla = `${nombreRuta()} · ${location.hash || '#/'}`, hora = new Date().toLocaleString(W.wdLocale());
    const capa = abrirHoja({ titulo: T('Reportar fallo'), sub: T('Llega a la carpeta «fallos» del servidor de pruebas, con la captura y estos datos.'),
      html: `<div class="fila tarjeta pad">${captura ? `<img class="captura-mini" src="${captura}" alt="${T('Captura de la pantalla')}">` : `<div class="captura-mini">${ic('camara', '')}</div>`}
        <dl class="datos crece"><div><dt>${T('Pantalla')}</dt><dd translate="no">${esc(pantalla)}</dd></div><div><dt>${T('Versión')}</dt><dd translate="no">${esc(info.version)}</dd></div>
        <div><dt>${T('Móvil')}</dt><dd translate="no">${esc(info.movil)}</dd></div><div><dt>${T('Hora')}</dt><dd translate="no">${esc(hora)}</dd></div></dl></div>
        <div class="campo"><label for="wda-qp">${T('¿Qué ha pasado?')}</label><textarea id="wda-qp" placeholder="${esc(T('Qué hacías, qué esperabas y qué ha pasado'))}"></textarea></div>`,
      pie: `<button class="wbtn ancho grande" type="button" id="wda-enviar-fallo">${T('Enviar')}</button>` });
    $('#wda-enviar-fallo', capa).onclick = async (e) => {
      const b = e.currentTarget; b.disabled = true;
      try {
        await postJSON('/api/pruebas/fallo', { texto: $('#wda-qp', capa).value, pantalla, version: info.version, movil: info.movil, idioma: W.currentLanguage(), hora, captura });
        cerrarHoja(); W.toast('Enviado a la carpeta de pruebas. Gracias.');
      } catch (err) { b.disabled = false; W.toast(err.message); }
    };
  }
  // Shake the phone to report a bug (WORLDIVES Pruebas only).
  if (APP.pruebas) {
    let ultimo = 0, golpes = 0, t = 0;
    window.addEventListener('devicemotion', (e) => {
      const a = e.accelerationIncludingGravity; if (!a) return;
      const f = Math.sqrt((a.x || 0) ** 2 + (a.y || 0) ** 2 + (a.z || 0) ** 2);
      const now = Date.now(); if (f > 24) { if (now - t > 1000) golpes = 0; golpes++; t = now; }
      if (golpes >= 3 && now - ultimo > 4000) { ultimo = now; golpes = 0; reportarFallo(); }
    });
  }
  async function entrarPrueba(params) {
    const c = params.get('cuenta') || '';
    pintar(`<div class="cuerpo"><div class="vacio"><p>${esc(T('Entrando…'))}</p></div></div>`);
    try { const r = await postJSON('/api/pruebas/entrar', { cuenta: c, ...(await window.WD_SEC?.extraLogin?.() || {}) }); await window.WD_SEC?.trasLogin?.(r); await W.loadMe(); plugin('Servidor')?.inicioHecho?.().catch(() => {}); W.toast(T('Has entrado como') + ' ' + c); }
    catch (e) { W.toast(e.message); }
    location.replace('#/');
  }

  /* ---------------------------------------------------------------- payment: back from Stripe to the app */
  function vueltaPago(url) {
    let u; try { u = new URL(url); } catch { return; }
    if (u.protocol.replace(':', '') !== APP.scheme || u.host !== 'pago') return;
    plugin('Browser')?.close?.().catch(() => {});
    const sid = u.searchParams.get('session_id'), reserva = u.searchParams.get('reserva') || pagoEnCurso;
    pagoEnCurso = null; mem.areaAt = 0;
    if (sid && u.searchParams.get('pago') !== 'cancelado') { location.hash = '#/pago-ok?session_id=' + encodeURIComponent(sid); return; }
    W.toast('Pago cancelado. Tu reserva sigue guardada: puedes pagarla desde Reservas.');
    location.hash = reserva ? '#/reserva?id=' + encodeURIComponent(reserva) : '#/reservas';
  }

  /* ---------------------------------------------------------------- router hooks (called from world-dives-v8.js) */
  const PROPIAS = { home: inicio, explorar, buscar, reservas, buddies, 'mi-area': miAreaPantalla, ajustes, 'pruebas-entrar': entrarPrueba };
  // Centro PRO and Freelance PRO live in /js/wd-app-pro.js: only centres and freelance download it.
  const PRO_RUTAS = ['home', 'agenda', 'escanear', 'solicitudes', 'mas', 'salida', 'reservas', 'nueva-reserva', 'resumen-barco', 'contar', 'estadisticas',
    'cobros-app', 'cerrar-cuenta', 'ajustes', 'mi-area'];
  let proCargado = null;
  function cargarPro() {
    if (!proCargado) proCargado = new Promise((ok) => { const js = document.createElement('script'); js.src = '/js/wd-app-pro.js?v=' + (W.APP_ASSETS || ''); js.onload = js.onerror = () => ok(); document.body.appendChild(js); setTimeout(ok, 8000); });
    return proCargado;
  }
  window.WDApp = {
    route(nombre, params) {
      cerrarHoja(true); quitarBarra();
      if (nombre === 'pruebas-entrar' && !APP.pruebas) return null;
      document.documentElement.classList.remove('wda-sin-tabs');
      // Own screens of Centro PRO / Freelance PRO; any other page (#/admin, #/reserva…) is drawn by the web inside the app.
      if (esPro() && PRO_RUTAS.includes(nombre)) {
        return cargarPro().then(() => {
          pintarTabs(nombre);
          const fn = WDA.rutasPro[nombre] || PROPIAS[nombre];
          return Promise.resolve(fn ? fn(params) : null).then(() => despues(nombre));
        });
      }
      const fn = PROPIAS[nombre]; pintarTabs(nombre);
      return fn ? Promise.resolve(fn(params)).then(() => despues(nombre)) : null;
    },
    after(nombre, params) {
      pintarTabs(nombre);
      // The web's «Volver» is not needed on the tabs' own pages.
      if (RAICES.includes(nombre)) $('#global-back')?.remove();
      if (['centro', 'profesional', 'punto'].includes(nombre)) decorarFicha(nombre, params);
      despues(nombre);
    },
    failed(err) { pintar(`<div class="cuerpo"><div class="tarjeta vacio"><h2>${esc(T('No se ha podido abrir esta sección'))}</h2><p>${esc(err?.message || '')}</p><button class="wbtn" type="button" data-reload>${esc(T('Reintentar'))}</button></div></div>`); },
  };
  /* ---------------------------------------------------------------- push (v50.49): only when the server has Firebase and this build carries it */
  let pushHecho = false;
  async function activarPush() {
    const P = plugin('PushNotifications'), L = plugin('PushListo');
    if (!P || !L || !state.me || pushHecho) return;
    pushHecho = true;
    try {
      if (!(await L.estado()).firebase || !(await api('/api/app/push')).enabled) return;
      let perm = await P.checkPermissions();
      if (perm.receive === 'prompt' || perm.receive === 'prompt-with-rationale') perm = await P.requestPermissions();
      if (perm.receive !== 'granted') return;
      await P.addListener('registration', (t) => { try { localStorage.setItem('wda-push', t.value); } catch { /* nothing */ } postJSON('/api/app/push/register', { token: t.value, platform: 'android', app: APP.scheme }).catch(() => {}); });
      await P.addListener('pushNotificationActionPerformed', (e) => { const r = e?.notification?.data?.ruta; if (r && r.startsWith('#/')) location.hash = r; });
      await P.createChannel?.({ id: 'avisos', name: T('Avisos'), importance: 4 }).catch(() => {});
      await P.register();
    } catch { /* without push: the emails and the notices in the app still arrive */ }
  }
  function despues(nombre) {
    if (state.me) activarPush();
    // A booking chosen before signing in: back on any screen with the session open, the sheet opens again.
    if (state.me && nombre !== 'login') { const p = pendiente(); if (p) setTimeout(() => abrirReserva(p), 300); }
  }

  /* ---------------------------------------------------------------- what wd-app-pro.js uses from here */
  const WDA = window.WDA = {
    W, APP, I, ic, esc, T, plugin, pintar, abrirHoja, cerrarHoja, abrirFuera, compartir, mapsDestino, dinero, fecha, cuando, km, anillo, estadoTag, modoTag,
    telefonoWa, esqueleto, vivo, rol, modulo, mem, cuenta, pintarTabs, filasEquipo, enlazarPerfil, nombreRuta, infoApp, salir, borrarCuenta, reportarFallo, pref, guardarPref, aplicarAspecto,
    rutasPro: {}, filtrarTabs: null, ajustes, miAreaPantalla, explorar, buscar,
  };

  /* ---------------------------------------------------------------- start */
  aplicarAspecto();
  banda();
  if (APP.native) {
    const A = plugin('App');
    A?.addListener?.('backButton', atras);
    A?.addListener?.('appUrlOpen', (e) => vueltaPago(e.url));
    A?.addListener?.('resume', () => { mem.areaAt = 0; });
    plugin('Browser')?.addListener?.('browserFinished', () => {
      if (pagoEnCurso) { const id = pagoEnCurso; pagoEnCurso = null; W.toast('No has terminado el pago. Tu reserva sigue guardada: puedes pagarla desde Reservas.'); location.hash = '#/reserva?id=' + id; }
    });
    // External links of the web pages (maps, PDF, social networks): out of the app, as Android does.
    document.addEventListener('click', (e) => {
      const a = e.target.closest('a[target="_blank"]'); if (!a) return;
      const href = a.getAttribute('href') || ''; if (!/^https?:/i.test(href) || href.startsWith(location.origin)) return;
      e.preventDefault(); abrirFuera(href);
    }, true);
  }
  setTimeout(() => plugin('SplashScreen')?.hide?.().catch(() => {}), 200);
})();
