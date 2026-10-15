/* WORLDIVES · app Centro PRO y Freelance PRO (v50.49, encargo «App móvil en 3 módulos», Tandas 2, 3 y 4).
   wd-app.js downloads this file only for centres and freelance professionals. It draws their own screens with the same
   look as the diver's app and uses only what the server already has:
   - Hoy: four numbers, what is urgent, today's departures with their seats, tomorrow folded; Freelance: today's jobs.
   - Agenda: month (coloured like a depth chart), week and day; create a departure (with the last values of that
     activity, weekly repetition); Freelance: block a day or half a day with one tap.
   - Escanear: the phone's camera reads the QR of a booking (or the code is typed) and marks the arrival; a promotion
     code is checked and redeemed; «ráfaga» opens the camera again after each diver.
   - Solicitudes and Pendientes de pago: countdown, accept (one or several), reject with a reason, offer another
     departure, remind by WhatsApp in the client's language, take the payment at the centre.
   - Salida (boat list): 56 px check-in, per-diver actions, add a diver, change the time or cancel and tell everybody
     (10 s to undo), summary for the boat (text to share and the PDF with its SHA-256 fingerprint), count on board.
     Marks made without coverage wait on the phone and are sent when it comes back.
   - Reservas, Nueva reserva (centres), Más (state of the account, «Disponible en la web», statistics, payments,
     changing centre, «Borrar mi cuenta para siempre»).
   Each person sees only what the permissions of their role allow (wod/roles.py); the server decides anyway. */
(() => {
  'use strict';
  const A = window.WDA;
  if (!A) return;
  const { W, APP, ic, esc, T, plugin, pintar, abrirHoja, cerrarHoja, abrirFuera, compartir, dinero, fecha, cuando, esqueleto, vivo, modulo, cuenta, pintarTabs } = A;
  const { $, $$, api, postJSON, state } = W;

  /* ---------------------------------------------------------------- who can do what */
  const esFree = () => modulo() === 'freelance';
  const esDueno = () => esFree() || (state.me?.member_role || 'owner') === 'owner';
  const puede = (p) => esDueno() || (state.me?.permissions || []).includes(p);
  A.filtrarTabs = (tabs) => tabs.filter(([h]) => (h === '#/solicitudes' ? puede('reservas') : h === '#/escanear' ? puede('checkin') : true));

  /* ---------------------------------------------------------------- small helpers */
  const hoyISO = () => W.wdToday();
  const sumaDias = (iso, n) => { const d = new Date(iso + 'T12:00:00'); d.setDate(d.getDate() + n); return d.toISOString().slice(0, 10); };
  const diaLargo = (iso) => fecha(iso, { weekday: 'long', day: 'numeric', month: 'long' });
  const corto = (iso) => fecha(iso, { day: 'numeric', month: 'short' });
  const fd = (txt) => `<span translate="no">${esc(txt)}</span>`;   // dates already in the phone's language
  const plural = (n, uno, varios) => `<span class="num">${n}</span> <span>${n === 1 ? uno : varios}</span>`;
  const minutos = (m) => (m == null ? '' : m < 60 ? `${m} min` : m < 1440 ? `${Math.floor(m / 60)} h ${m % 60 ? (m % 60) + ' min' : ''}`.trim() : `${Math.floor(m / 1440)} d`);
  function vibrar(tipo) {
    const H = plugin('Haptics');
    if (H?.notification) { H.notification({ type: tipo }).catch(() => {}); return; }
    try { navigator.vibrate?.(tipo === 'ERROR' ? [80, 60, 80] : 40); } catch { /* nothing */ }
  }
  const sinRed = (e) => !e || !e.status;
  const fallo = (box, e, reintentar) => {
    if (!vivo(box)) return;
    box.innerHTML = `<div class="tarjeta vacio"><p>${esc(sinRed(e) ? T('Sin conexión. Lo que ya estaba guardado en el móvil sigue aquí.') : e.message)}</p>${reintentar ? `<button class="wbtn sec mini" type="button" data-reintentar>${T('Reintentar')}</button>` : ''}</div>`;
    $('[data-reintentar]', box)?.addEventListener('click', reintentar);
  };
  // What the phone keeps to work without coverage (T4): today's and tomorrow's lists, «Hoy» and the agenda.
  const guardado = {
    leer(k) { try { return JSON.parse(localStorage.getItem('wda-pro-' + k) || 'null'); } catch { return null; } },
    escribir(k, v) { try { localStorage.setItem('wda-pro-' + k, JSON.stringify({ at: Date.now(), v })); } catch { /* storage full or blocked */ } },
  };
  async function conCopia(k, url) {
    try { const v = await api(url); guardado.escribir(k + ':' + (state.me?.user?.center_id || state.me?.user?.id), v); return { v, viejo: false }; }
    catch (e) {
      const c = sinRed(e) ? guardado.leer(k + ':' + (state.me?.user?.center_id || state.me?.user?.id)) : null;
      if (c) return { v: c.v, viejo: true, at: c.at };
      throw e;
    }
  }
  const avisoViejo = (r) => (r.viejo ? `<div class="aviso pend">${ic('alerta')}<div>${T('Sin conexión: datos guardados en el móvil a las')} <span class="num">${new Date(r.at).toLocaleTimeString(W.wdLocale(), { hour: '2-digit', minute: '2-digit' })}</span>.</div></div>` : '');
  // Measured on the phone: how long each screen takes until it shows its data (Tanda 4, «medir las promesas»).
  const medidas = (window.WDAMedidas = window.WDAMedidas || {});
  const medir = (nombre, t0) => { medidas[nombre] = Math.round(performance.now() - t0); };

  /* ---------------------------------------------------------------- account closed */
  function cuentaCerrada() {
    // v50.52 (ASVS V6.3.3): with online payments or «Cobros», two-step verification first (only «Mi cuenta» meanwhile).
    if (state.me?.security?.totp_blocked) {
      pintar(`<div class="cuerpo"><h1>${T('Activa la verificación en dos pasos')}</h1><div class="aviso urg">${ic('alerta')}<div>${T('Es obligatoria para quien puede cobrar o ver los pagos. Las reservas y los pagos de tus clientes siguen funcionando con normalidad.')}</div></div>
        <a class="wbtn ancho grande" href="#/cuenta?seguridad=1">${ic('check', '')}${T('Activarla ahora')}</a>
        <div class="tarjeta plana lista"><button class="lista-fila" type="button" id="wda-salir2">${ic('salir')}<span class="crece">${T('Cerrar sesión')}</span></button></div></div>`);
      $('#wda-salir2')?.addEventListener('click', A.salir);
      return true;
    }
    const c = state.me?.account_closed; if (!c) return false;
    pintar(`<div class="cuerpo"><h1>Cuenta cerrada</h1><div class="aviso urg">${ic('alerta')}<div><b>${T('Tu cuenta está cerrada')}</b> <span>${T('desde el')}</span> <span class="num">${fd(corto(c.closed_at.slice(0, 10)))}</span>. ${T('Nadie la ve ni puede reservar.')}
        <p>${T('La guardamos hasta el')} <b class="num">${fd(corto(c.purge_after))}</b> (${plural(c.days_left, 'día', 'días')}). ${T('Después la borraremos para siempre.')}</p></div></div>
      ${esDueno() ? `<button class="wbtn ancho grande" type="button" id="wda-reabrir">${ic('check', '')}Reabrir mi cuenta</button>` : `<p class="suave">${T('El propietario del centro ha cerrado la cuenta. Solo él puede reabrirla.')}</p>`}
      <div class="tarjeta plana lista"><a class="lista-fila" href="#/cuenta">${ic('ficha')}<span class="crece">Mi cuenta</span>${ic('chev', 'chev')}</a><button class="lista-fila" type="button" id="wda-salir2">${ic('salir')}<span class="crece">Cerrar sesión</span>${ic('chev', 'chev')}</button></div></div>`);
    $('#wda-reabrir')?.addEventListener('click', async (e) => {
      e.currentTarget.disabled = true;
      try { await postJSON('/api/provider/cuenta/reabrir', {}); await W.loadMe(); W.toast(T('Tu cuenta vuelve a estar abierta, con todo como estaba.')); location.hash = '#/'; A.rutasPro.home(); }
      catch (err) { e.currentTarget.disabled = false; W.toast(err.message); }
    });
    $('#wda-salir2')?.addEventListener('click', A.salir);
    return true;
  }

  /* ---------------------------------------------------------------- the centre (several centres: switch) */
  function cabecera(titulo, extra = '') {
    const me = state.me, u = me?.user || {}, centros = me?.centers || [];
    const nombre = esFree() ? u.fullname : (centros.find((c) => c.id === u.center_id)?.name || me?.center?.name || '');
    const rolTxt = esFree() ? T('Freelance PRO') : (me?.member_role_name || 'Centro PRO');
    return `<header class="cab"><div class="cab-fila"><div class="wavatar">${esc(W.initials(nombre || u.fullname || ''))}</div>
      <div class="crece pila">${centros.length > 1 ? `<button type="button" class="selector-perfil" id="wda-centro"><span translate="no">${esc(nombre)}</span>${ic('mover', '')}</button>` : `<b translate="no">${esc(nombre)}</b>`}
      <span class="suave peq">${esc(rolTxt)}</span></div>${extra}</div><h1>${titulo}</h1></header>`;
  }
  function enlazarCentro(root) {
    $('#wda-centro', root)?.addEventListener('click', () => {
      const centros = state.me?.centers || [];
      const capa = abrirHoja({ titulo: T('Cambiar de centro'), html: `<div class="tarjeta plana lista">${centros.map((c) => `<button class="lista-fila" type="button" data-c="${c.id}">${ic('tienda')}<span class="crece" translate="no">${esc(c.name)}</span>${c.id === state.me.user.center_id ? ic('check', '') : ''}</button>`).join('')}</div>` });
      $$('[data-c]', capa).forEach((b) => { b.onclick = async () => {
        try { await postJSON('/api/team/switch', { center: +b.dataset.c }); await W.loadMe(); cerrarHoja(); W.toast(T('Ahora trabajas en este centro.')); location.hash = '#/'; A.rutasPro.home(); }
        catch (e) { W.toast(e.message); }
      }; });
    });
  }

  /* ---------------------------------------------------------------- seats of a departure */
  function asientos(s) {
    const total = Math.max(s.spots_total, s.confirmed + s.pending_payment), max = 40;
    const html = [];
    for (let i = 0; i < Math.min(total, max); i++) html.push(`<span class="asiento${i < s.confirmed ? ' ok' : i < s.confirmed + s.pending_payment ? ' pend' : ''}"></span>`);
    return `<div class="asientos" role="img" translate="no" aria-label=""${s.confirmed} ${T('confirmados')}, ${s.pending_payment} ${T('pendientes de pago')}, ${Math.max(0, s.spots_total - s.confirmed - s.pending_payment)} ${T('libres')}">${html.join('')}${total > max ? `<span class="suave peq">+${total - max}</span>` : ''}</div>`;
  }
  function tarjetaSalidaPro(s) {
    const gente = s.confirmed + s.pending_payment;
    const canc = s.status === 'cancelled';
    return `<a class="tarjeta pad pila-8" href="#/salida?id=${s.slot_id}" style="color:inherit;text-decoration:none${canc ? ';opacity:.6' : ''}">
      <div class="fila"><div class="fecha-b hora"><b class="num">${esc(s.time || '—')}</b></div><div class="crece pila"><b translate="no">${esc(s.service)}</b>
        <span class="suave peq">${canc ? `<span class="wtag canc">${ic('x', '')}${T('Cancelada')}</span>` : `${plural(gente, 'buceador', 'buceadores')} · <span class="num">${s.present}</span> <span>${T('han llegado')}</span>`}${s.guides.length ? ` · <span translate="no">${esc(s.guides.join(', '))}</span>` : ''}</span></div>${ic('chev', 'chev')}</div>
      ${canc ? '' : asientos(s)}
      <div class="wtags">${s.unsigned ? `<span class="wtag pend">${ic('documento', '')}<span class="num">${s.unsigned}</span> ${T('sin firmar')}</span>` : ''}${s.requested ? `<span class="wtag sol">${ic('sobre', '')}<span class="num">${s.requested}</span> ${T('por aceptar')}</span>` : ''}${s.mine ? `<span class="wtag ok">${ic('check', '')}${T('Guías tú')}</span>` : ''}${s.return_pending ? `<span class="wtag urg">${ic('area', '')}${T('Falta contar a la vuelta')}</span>` : ''}${!canc && s.spots_available <= 0 ? `<span class="wtag neutro">${T('Completa')}</span>` : ''}</div></a>`;
  }

  /* ================================================================ HOY */
  async function hoy() {
    const t0 = performance.now();
    if (cuentaCerrada()) return;
    const root = pintar(cabecera(T('Tu día'), `<button class="wbtn sec mini" type="button" id="wda-act" aria-label="${T('Actualizar')}">${ic('reloj', '')}</button>`) + `<div class="cuerpo" id="wda-hoy">${esqueleto(3)}</div>`);
    enlazarCentro(root);
    $('#wda-act', root).onclick = () => hoy();
    let r;
    try { r = await conCopia('hoy', '/api/pro/hoy'); } catch (e) { fallo($('#wda-hoy', root), e, hoy); return; }
    if (!vivo(root)) return;
    const d = r.v, c = d.counts;
    cuenta.solicitudes = d.requests || 0; pintarTabs('home');
    const cifra = (href, valor, txt, cls = '') => `<a class="tarjeta cifra ${cls}" href="${href}"><b class="num">${valor}</b><span>${txt}</span></a>`;
    const urg = (d.urgent || []).map((u) => `<a class="tarjeta pad fila" href="#/solicitudes?ver=${u.kind === 'pago' ? 'pago' : 'sol'}" style="color:inherit;text-decoration:none">
        <div class="anillo peq ${u.minutes_left < 60 ? 'urg' : 'pend'}">${anilloMin(u.minutes_left)}</div><div class="crece pila"><b translate="no">${esc(u.name)}</b>
        <span class="suave peq">${u.kind === 'pago' ? T('Falta el pago') : T('Solicitud por contestar')} · <span translate="no">${esc(u.service || '')}</span> · ${fd(cuando(u.date))}</span></div>${ic('chev', 'chev')}</a>`).join('');
    const trabajos = (d.jobs || []).filter((j) => j.local_date === d.date);
    const manana = d.tomorrow_slots || [], trabajosM = (d.jobs || []).filter((j) => j.local_date === d.tomorrow);
    $('#wda-hoy', root).innerHTML = `${avisoViejo(r)}
      <div class="cifras">${cifra('#/agenda?vista=dia', c.slots, T(c.slots === 1 ? 'salida hoy' : 'salidas hoy'))}${cifra('#/agenda?vista=dia', `${c.present}/${c.divers}`, T('han llegado'))}
        ${d.requests != null ? cifra('#/solicitudes', d.requests, T('solicitudes'), d.requests ? 'alerta' : '') + cifra('#/solicitudes?ver=pago', d.awaiting_payment, T('pendientes de pago'), d.awaiting_payment ? 'alerta' : '') : ''}</div>
      ${urg ? `<section class="pila-8"><h2>${ic('alerta', '')} ${T('Urgente')}</h2>${urg}</section>` : ''}
      ${esFree() || trabajos.length ? `<section class="pila-8"><h2>${T('Trabajos de hoy')}</h2>${trabajos.length ? trabajos.map(tarjetaTrabajo).join('') : `<div class="tarjeta vacio"><p>${T('Hoy no tienes trabajos por días.')}</p></div>`}</section>` : ''}
      <section class="pila-8"><div class="seccion-cab"><h2>${T('Salidas de hoy')}</h2></div>${d.slots.length ? d.slots.map(tarjetaSalidaPro).join('') : `<div class="tarjeta vacio"><p>${T('Hoy no hay salidas.')}</p>${puede('salidas') ? `<a class="wbtn sec mini" href="#/agenda?vista=dia&crear=1">${ic('mas1', '')}${T('Crear salida')}</a>` : ''}</div>`}</section>
      <details class="tarjeta pad"><summary><b>${T('Mañana')}</b> · <span class="suave">${manana.length + trabajosM.length ? plural(manana.reduce((n, s) => n + s.confirmed + s.pending_payment, 0), 'buceador', 'buceadores') + ' · ' + plural(manana.length, 'salida', 'salidas') : T('Nada todavía')}</span></summary>
        <div class="pila-8" style="margin-top:10px">${manana.map(tarjetaSalidaPro).join('')}${trabajosM.map(tarjetaTrabajo).join('')}</div></details>
      <a class="wbtn sec ancho" href="#/agenda?vista=semana">${ic('agenda', '')}${T('Ver semana')}</a>`;
    W.translateTree($('#wda-hoy', root));
    $$('[data-trabajo]', root).forEach((b) => enlazarTrabajo(b));
    medir('hoy', t0);
    // Keep today's and tomorrow's boat lists on the phone for the boat (no coverage at sea).
    if (!r.viejo && puede('checkin')) guardarListasDelDia();
  }
  function anilloMin(m) {
    const v = Math.max(0.05, Math.min(1, (m || 0) / 180)), rr = 32, cc = 2 * Math.PI * rr;
    return `<svg viewBox="0 0 76 76"><circle class="pista" cx="38" cy="38" r="${rr}" fill="none" stroke-width="7"/><circle class="valor" cx="38" cy="38" r="${rr}" fill="none" stroke-width="7" stroke-dasharray="${(cc * v).toFixed(1)} ${cc.toFixed(1)}"/></svg><b class="num">${m == null ? '—' : m < 60 ? m + '′' : Math.floor(m / 60) + 'h'}</b>`;
  }
  function tarjetaTrabajo(j) {
    return `<article class="tarjeta pad pila-8"><div class="fila"><div class="fecha-b hora"><b>${esc(j.part === 'am' ? T('Mañana') : j.part === 'pm' ? T('Tarde') : T('Día'))}</b></div>
      <div class="crece pila"><b translate="no">${esc(j.client || '')}</b><span class="suave peq"><span translate="no">${esc(j.service || '')}</span> · ${plural(j.participants || 1, 'persona', 'personas')}${j.point_name ? ` · <span translate="no">${esc(j.point_name)}</span>` : ''}</span></div>${A.estadoTag(j)}</div>
      <div class="acciones tres"><button class="accion" type="button" data-trabajo="tel" data-id="${j.id}">${ic('tel')}<span>Llamar</span></button><button class="accion" type="button" data-trabajo="wa" data-id="${j.id}">${ic('wa')}<span>WhatsApp</span></button>
      <button class="accion" type="button" data-trabajo="ruta" data-lat="${j.latitude ?? ''}" data-lon="${j.longitude ?? ''}" ${j.latitude == null ? 'disabled' : ''}>${ic('ruta')}<span>Cómo llegar</span></button></div></article>`;
  }
  function enlazarTrabajo(b) {
    b.onclick = async () => {
      if (b.dataset.trabajo === 'ruta') { abrirFuera(A.mapsDestino({ lat: b.dataset.lat, lon: b.dataset.lon })); return; }
      contactar(+b.dataset.id, b.dataset.trabajo);
    };
  }
  // Call or WhatsApp a client: the server gives the number only to the centre of the booking, and the text in the client's language.
  async function contactar(bid, como, tipo = 'reserva') {
    try {
      const r = await api(`/api/bookings/${bid}/whatsapp?tipo=${tipo}`);
      if (!r.phone_ok) { W.toast(r.reason || T('Esta reserva no tiene un teléfono válido.')); return; }
      if (como === 'tel') { abrirFuera(r.tel); return; }
      if (APP.pruebas) { W.toast(T('WORLDIVES Pruebas: no se abre WhatsApp. Texto:') + ' ' + r.text); return; }
      abrirFuera(r.url);
    } catch (e) { W.toast(e.message); }
  }
  async function guardarListasDelDia() {
    // ASVS V14.3.3: the lists carry phones and emergency contacts; those of past days are not kept.
    try { const hoy = hoyISO(); for (const k of (window.WD_SEC?.keys?.() || Object.keys(localStorage))) { const m = /^wda-pro-dia:(\d{4}-\d{2}-\d{2}):/.exec(k); if (m && m[1] < hoy) localStorage.removeItem(k); } } catch { /* storage blocked */ }
    try {
      for (const d of [hoyISO(), sumaDias(hoyISO(), 1)]) guardado.escribir('dia:' + d + ':' + (state.me?.user?.center_id || state.me?.user?.id), await api('/api/manifest/day?date=' + d));
    } catch { /* tried again next time */ }
  }

  /* ================================================================ AGENDA */
  const vistaAg = { v: null, dia: null, mes: null };
  async function agenda(params) {
    const t0 = performance.now();
    if (cuentaCerrada()) return;
    const p = params || new URLSearchParams();
    vistaAg.v = p.get('vista') || vistaAg.v || A.pref('agenda', 'mes', ['mes', 'semana', 'dia']);
    vistaAg.dia = p.get('dia') || vistaAg.dia || hoyISO();
    vistaAg.mes = vistaAg.mes || vistaAg.dia.slice(0, 7);
    const seg = (k, t) => `<button type="button" data-vista="${k}" aria-pressed="${vistaAg.v === k}">${t}</button>`;
    const root = pintar(`<div class="cuerpo"><div class="seccion-cab"><h1>Agenda</h1>${puede('salidas') ? `<button class="wbtn mini" type="button" id="wda-crear">${ic('mas1', '')}Crear salida</button>` : ''}</div>
      <div class="seg" role="group" aria-label="Vista">${seg('mes', 'Mes')}${seg('semana', 'Semana')}${seg('dia', 'Día')}</div><div id="wda-ag" class="pila-12">${esqueleto(3)}</div></div>`);
    $$('[data-vista]', root).forEach((b) => { b.onclick = () => { vistaAg.v = b.dataset.vista; A.guardarPref('agenda', vistaAg.v); agenda(); }; });
    $('#wda-crear', root)?.addEventListener('click', () => crearSalida(vistaAg.dia));
    if (p.get('crear')) setTimeout(() => crearSalida(vistaAg.dia), 50);
    const box = $('#wda-ag', root);
    try {
      if (vistaAg.v === 'mes') await agendaMes(box);
      else if (vistaAg.v === 'semana') await agendaSemana(box);
      else await agendaDia(box);
    } catch (e) { fallo(box, e, () => agenda()); return; }
    medir('agenda-' + vistaAg.v, t0);
  }
  const nivel = (occ, n) => (!n ? 0 : occ >= 0.9 ? 5 : occ >= 0.7 ? 4 : occ >= 0.45 ? 3 : occ >= 0.2 ? 2 : 1);
  async function agendaMes(box) {
    const [y, m] = vistaAg.mes.split('-').map(Number);
    const primero = new Date(y, m - 1, 1, 12), desplaz = (primero.getDay() + 6) % 7;
    const inicio = sumaDias(`${vistaAg.mes}-01`, -desplaz);
    const [r, bl] = await Promise.all([conCopia('ag:' + inicio, `/api/pro/agenda?desde=${inicio}&dias=42`), esFree() ? api('/api/agenda/mine?month=' + vistaAg.mes).catch(() => null) : null]);
    if (!vivo(box)) return;
    const bloqueados = new Set();
    (bl?.blocks || []).filter((b) => !b.booking).forEach((b) => { for (let d = b.from; d <= b.to; d = sumaDias(d, 1)) bloqueados.add(d); });
    const nombresDias = Array.from({ length: 7 }, (_, i) => new Date(2024, 0, 1 + i, 12).toLocaleDateString(W.wdLocale(), { weekday: 'narrow' }));
    const titulo = primero.toLocaleDateString(W.wdLocale(), { month: 'long', year: 'numeric' });
    box.innerHTML = `${avisoViejo(r)}<div class="seccion-cab"><button class="wbtn sec mini" type="button" data-mes="-1" aria-label="${T('Mes anterior')}">${ic('atras', '')}</button><h2 class="crece" style="text-align:center" translate="no">${esc(titulo)}</h2><button class="wbtn sec mini" type="button" data-mes="1" aria-label="${T('Mes siguiente')}">${ic('chev', '')}</button></div>
      <div class="mes" role="grid">${nombresDias.map((n) => `<span class="dsem" aria-hidden="true" translate="no">${esc(n)}</span>`).join('')}
      ${r.v.days.map((d) => { const n = d.slots.filter((s) => s.status !== 'cancelled').length, fuera = !d.date.startsWith(vistaAg.mes);
        return `<button type="button" translate="no" class="dia${fuera ? ' fuera' : ''}${d.date === hoyISO() ? ' hoy' : ''}${bloqueados.has(d.date) ? ' bloqueado' : ''}" data-p="${nivel(d.occupancy, n)}" data-dia="${d.date}" aria-pressed="${d.date === vistaAg.dia}" aria-label="${esc(diaLargo(d.date))}: ${n} ${T(n === 1 ? 'salida' : 'salidas')}, ${d.people} ${T('buceadores')}">${Number(d.date.slice(8))}${n ? `<span class="puntos">${'<i></i>'.repeat(Math.min(3, n))}</span>` : ''}</button>`; }).join('')}</div>
      <div class="escala-prof"><span>${T('Ocupación')}</span>${[1, 2, 3, 4, 5].map((k) => `<i class="dia" data-p="${k}" style="aspect-ratio:auto;padding:0"></i>`).join('')}<span>${T('llena')}</span>${esFree() ? `<i class="dia bloqueado" style="aspect-ratio:auto;padding:0"></i><span>${T('bloqueado')}</span>` : ''}</div>
      <div id="wda-ag-dia" class="pila-8"></div>`;
    W.translateTree(box);
    $$('[data-mes]', box).forEach((b) => { b.onclick = () => { const d = new Date(y, m - 1 + Number(b.dataset.mes), 1, 12); vistaAg.mes = d.toISOString().slice(0, 7); agenda(); }; });
    const pintarDia = (iso) => {
      vistaAg.dia = iso; $$('[data-dia]', box).forEach((x) => x.setAttribute('aria-pressed', String(x.dataset.dia === iso)));
      const d = r.v.days.find((x) => x.date === iso), cont = $('#wda-ag-dia', box);
      cont.innerHTML = `<div class="seccion-cab"><h2>${fd(diaLargo(iso))}</h2>${esFree() ? botonBloqueo(iso, bloqueados.has(iso), bl) : ''}</div>${d && d.slots.length ? d.slots.map(tarjetaSalidaPro).join('') : `<div class="tarjeta vacio"><p>${T('Sin salidas este día.')}</p></div>`}`;
      W.translateTree(cont); enlazarBloqueo(cont, bl);
    };
    $$('[data-dia]', box).forEach((b) => { b.onclick = () => pintarDia(b.dataset.dia); });
    pintarDia(r.v.days.some((d) => d.date === vistaAg.dia) ? vistaAg.dia : `${vistaAg.mes}-01`);
  }
  async function agendaSemana(box) {
    const d0 = vistaAg.dia, lunes = sumaDias(d0, -((new Date(d0 + 'T12:00:00').getDay() + 6) % 7));
    const r = await conCopia('ag:' + lunes, `/api/pro/agenda?desde=${lunes}&dias=7`);
    if (!vivo(box)) return;
    box.innerHTML = `${avisoViejo(r)}<div class="seccion-cab"><button class="wbtn sec mini" type="button" data-sem="-7" aria-label="${T('Semana anterior')}">${ic('atras', '')}</button><h2 class="crece" style="text-align:center"><span class="num">${fd(corto(lunes))} – ${fd(corto(sumaDias(lunes, 6)))}</span></h2><button class="wbtn sec mini" type="button" data-sem="7" aria-label="${T('Semana siguiente')}">${ic('chev', '')}</button></div>
      <div class="tarjeta plana lista">${r.v.days.map((d) => { const dt = new Date(d.date + 'T12:00:00');
        return `<button type="button" class="semana-dia lista-fila" data-dia="${d.date}" ${d.date === hoyISO() ? 'aria-current="date"' : ''}><span class="nd" translate="no"><small>${esc(dt.toLocaleDateString(W.wdLocale(), { weekday: 'short' }))}</small>${dt.getDate()}</span>
          <span class="mini-barras">${d.slots.length ? d.slots.map((s) => `<span class="mini-barra"><span class="num">${esc(s.time || '')}</span><span class="pista"><i style="width:${s.spots_total ? Math.min(100, Math.round(100 * (s.confirmed + s.pending_payment) / s.spots_total)) : 0}%"></i></span><span class="num">${s.confirmed + s.pending_payment}/${s.spots_total}</span></span>`).join('') : `<span class="suave peq">${T('Sin salidas')}</span>`}</span>${ic('chev', 'chev')}</button>`; }).join('')}</div>`;
    W.translateTree(box);
    $$('[data-sem]', box).forEach((b) => { b.onclick = () => { vistaAg.dia = sumaDias(vistaAg.dia, Number(b.dataset.sem)); agenda(); }; });
    $$('[data-dia]', box).forEach((b) => { b.onclick = () => { vistaAg.dia = b.dataset.dia; vistaAg.v = 'dia'; agenda(); }; });
  }
  async function agendaDia(box) {
    const r = await conCopia('ag:' + vistaAg.dia + ':1', `/api/pro/agenda?desde=${vistaAg.dia}&dias=1`);
    if (!vivo(box)) return;
    const d = r.v.days[0];
    box.innerHTML = `${avisoViejo(r)}<div class="seccion-cab"><button class="wbtn sec mini" type="button" data-d="-1" aria-label="${T('Día anterior')}">${ic('atras', '')}</button><h2 class="crece" style="text-align:center">${fd(diaLargo(d.date))}</h2><button class="wbtn sec mini" type="button" data-d="1" aria-label="${T('Día siguiente')}">${ic('chev', '')}</button></div>
      ${d.slots.length ? d.slots.map(tarjetaSalidaPro).join('') : `<div class="tarjeta vacio"><p>${T('Sin salidas este día.')}</p></div>`}`;
    W.translateTree(box);
    $$('[data-d]', box).forEach((b) => { b.onclick = () => { vistaAg.dia = sumaDias(vistaAg.dia, Number(b.dataset.d)); agenda(); }; });
  }
  // Freelance: block a whole day or half a day with one tap (the server keeps the days the person works).
  function botonBloqueo(iso, bloqueado) {
    return bloqueado ? `<button class="wbtn sec mini" type="button" data-desbloquear="${iso}">${ic('check', '')}${T('Desbloquear')}</button>`
      : `<button class="wbtn sec mini" type="button" data-bloquear="${iso}">${ic('bloquear', '')}${T('Bloquear')}</button>`;
  }
  function enlazarBloqueo(cont, bl) {
    $('[data-bloquear]', cont)?.addEventListener('click', (e) => {
      const iso = e.currentTarget.dataset.bloquear;
      const capa = abrirHoja({ titulo: T('Bloquear'), sub: fd(diaLargo(iso)), html: `<div class="pila-8">${[['full', 'Todo el día'], ['am', 'Solo la mañana'], ['pm', 'Solo la tarde']].map(([k, t]) => `<button class="contar-btn" type="button" data-part="${k}">${ic('bloquear', '')}<span>${T(t)}</span></button>`).join('')}
        <div class="campo"><label for="wda-bl-n">${T('Nota (solo la ves tú)')}</label><input id="wda-bl-n" maxlength="200"></div></div>` });
      $$('[data-part]', capa).forEach((b) => { b.onclick = async () => {
        try { await postJSON('/api/agenda/block', { date_from: iso, date_to: iso, part: b.dataset.part, kind: 'manual', note: $('#wda-bl-n', capa).value }); cerrarHoja(); vibrar('SUCCESS'); W.toast(T('Bloqueado.')); agenda(); }
        catch (err) { W.toast(err.message); }
      }; });
    });
    $('[data-desbloquear]', cont)?.addEventListener('click', async (e) => {
      const iso = e.currentTarget.dataset.desbloquear;
      const ids = (bl?.blocks || []).filter((b) => !b.booking && b.from <= iso && iso <= b.to).map((b) => b.id);
      try { for (const id of ids) await postJSON('/api/agenda/unblock', { id }); W.toast(T('Desbloqueado.')); agenda(); } catch (err) { W.toast(err.message); }
    });
  }
  // Create a departure: the activity's last values (time and spots) as a template, and weekly repetition.
  async function crearSalida(diaIni) {
    let servicios = [];
    try { servicios = (await api('/api/provider-services?provider_id=' + state.me.user.id)).items.filter((s) => s.active !== 0 && s.booking_unit !== 'day' && s.booking_unit !== 'half_day'); }
    catch (e) { W.toast(e.message); return; }
    if (!servicios.length) { W.toast(T('Primero crea una actividad en la web (Servicios).')); return; }
    const plantilla = (sid) => { const s = servicios.find((x) => String(x.id) === String(sid)); const ult = (s?.slots || []).slice(-1)[0]; return { hora: ult?.slot_time || '09:00', plazas: ult?.spots_total || s?.max_participants || 10 }; };
    const p0 = plantilla(servicios[0].id);
    const capa = abrirHoja({ titulo: T('Crear salida'), html: `<div class="pila-12">
      <div class="campo"><label for="cs-s">${T('Actividad')}</label><select id="cs-s">${servicios.map((s) => `<option value="${s.id}" translate="no">${esc(s.title)}</option>`).join('')}</select></div>
      <div class="fila"><div class="campo crece"><label for="cs-d">${T('Día')}</label><input id="cs-d" type="date" value="${esc(diaIni || hoyISO())}" min="${hoyISO()}"></div><div class="campo"><label for="cs-h">${T('Hora')}</label><input id="cs-h" type="time" value="${esc(p0.hora)}"></div></div>
      <div class="campo"><label for="cs-p">${T('Plazas')}</label><input id="cs-p" type="number" inputmode="numeric" min="1" max="200" value="${p0.plazas}"></div>
      <div class="campo"><label for="cs-r">${T('Repetir cada semana')}</label><select id="cs-r">${[0, 1, 2, 3, 4, 6, 8, 12].map((n) => `<option value="${n}">${n ? n + ' ' + T(n === 1 ? 'semana más' : 'semanas más') : T('No repetir')}</option>`).join('')}</select></div>
      <p class="suave peq">${T('Para el cartel o las fotos de la salida, usa la web (Herramientas).')}</p></div>`,
      pie: `<button class="wbtn ancho grande" type="button" id="cs-ok">${ic('check', '')}${T('Crear')}</button>` });
    $('#cs-s', capa).onchange = (e) => { const p = plantilla(e.target.value); $('#cs-h', capa).value = p.hora; $('#cs-p', capa).value = p.plazas; };
    $('#cs-ok', capa).onclick = async (e) => {
      const b = e.currentTarget; b.disabled = true;
      const base = { service_id: +$('#cs-s', capa).value, slot_time: $('#cs-h', capa).value, spots_total: +$('#cs-p', capa).value };
      const n = +$('#cs-r', capa).value; let hechas = 0; const errores = [];
      for (let i = 0; i <= n; i++) {
        try { await postJSON('/api/provider-services/slot', { ...base, slot_date: sumaDias($('#cs-d', capa).value, 7 * i) }); hechas++; }
        catch (err) { errores.push(err.message); }
      }
      b.disabled = false;
      if (hechas) { cerrarHoja(); vibrar('SUCCESS'); W.toast(`${hechas} ${T(hechas === 1 ? 'salida creada.' : 'salidas creadas.')}${errores.length ? ' ' + errores[0] : ''}`); vistaAg.dia = $('#cs-d', capa)?.value || vistaAg.dia; agenda(); }
      else W.toast(errores[0] || T('No se ha podido crear.'));
    };
  }

  /* ================================================================ ESCANEAR */
  const esc_ = { rafaga: false, salida: null };
  async function escanear(params) {
    if (cuentaCerrada()) return;
    if (!puede('checkin')) { location.replace('#/'); return; }
    esc_.salida = params?.get?.('salida') || null;
    const root = pintar(`<div class="cuerpo"><div class="escaner-cab">${ic('escanear')}<h1>Escanear</h1><p>${esc_.salida ? T('Las llegadas se marcan en esta salida.') : T('El QR de la reserva del buceador o un código de promoción.')}</p></div>
      <button class="wbtn ancho grande" type="button" id="wda-scan" style="min-height:96px">${ic('camara', '')}${T('Abrir la cámara')}</button>
      <label class="fila tarjeta pad"><input type="checkbox" id="wda-rafaga" ${esc_.rafaga ? 'checked' : ''} style="width:24px;height:24px"><span class="crece pila"><b>${T('Ráfaga')}</b><span class="suave peq">${T('Después de cada buceador la cámara se abre otra vez.')}</span></span></label>
      <form class="tarjeta pad pila-8" id="wda-cod"><label for="wda-cod-i"><b>${T('Escribir código')}</b></label><span class="suave peq">${T('Está debajo del QR de la reserva, por ejemplo 1234-A1B2C3, o es el código de una promoción.')}</span>
        <div class="fila campo"><input id="wda-cod-i" class="crece" autocomplete="off" autocapitalize="characters" inputmode="text" maxlength="60" style="font-size:20px;letter-spacing:.06em"><button class="wbtn" type="submit">${T('Comprobar')}</button></div></form>
      <div id="wda-res" aria-live="polite"></div></div>`);
    $('#wda-rafaga', root).onchange = (e) => { esc_.rafaga = e.target.checked; };
    $('#wda-scan', root).onclick = () => abrirCamara(root);
    $('#wda-cod', root).onsubmit = (e) => { e.preventDefault(); const v = $('#wda-cod-i', root).value.trim(); if (v) comprobar(root, v); };
  }
  async function abrirCamara(root) {
    const S = plugin('CapacitorBarcodeScanner');
    if (!S) { W.toast(T('La cámara solo se abre dentro de la app. Escribe el código.')); $('#wda-cod-i', root)?.focus(); return; }
    try {
      const r = await S.scanBarcode({ hint: 0, scanInstructions: T('Apunta al QR de la reserva'), scanButton: false, cameraDirection: 1 });
      const v = r?.ScanResult || r?.scanResult || '';
      if (v) comprobar(root, v);
    } catch (e) {
      const m = String(e?.message || e || '');
      if (/denied|permission|permiso/i.test(m)) {
        $('#wda-res', root).innerHTML = `<div class="aviso urg">${ic('camara')}<div><b>${T('Sin permiso para la cámara.')}</b> ${T('Actívalo en los ajustes del móvil (Aplicaciones › WORLDIVES › Permisos) o escribe el código.')}</div></div>`;
        W.translateTree($('#wda-res', root));
      } else if (!/cancel/i.test(m)) W.toast(m || T('No se ha podido leer el código.'));
    }
  }
  async function comprobar(root, code) {
    const box = $('#wda-res', root); box.innerHTML = esqueleto(1);
    let r;
    try { r = await postJSON('/api/pro/escanear', { code, slot_id: esc_.salida ? +esc_.salida : undefined }); }
    catch (e) { box.innerHTML = `<div class="aviso urg">${ic('alerta')}<div>${esc(sinRed(e) ? T('Sin conexión. Busca a la persona en la lista del barco: allí se guarda en el móvil.') : e.message)}</div></div>`; vibrar('ERROR'); return; }
    if (r.result === 'no_valido' && !/^\d+\s*[-\s·.]/.test(code) && !/verificarreserva/.test(code)) { if (await promo(box, code)) return; }
    pintarResultado(root, box, r, code);
  }
  function pintarResultado(root, box, r, code) {
    const b = r.booking, ok = r.result === 'ok', usado = r.result === 'usado';
    const cls = ok ? '' : ['pendiente_pago', 'otro_dia', 'otra_salida', 'sin_aceptar', 'usado', 'sin_lista'].includes(r.result) ? 'pend' : 'urg';
    vibrar(ok ? 'SUCCESS' : cls === 'pend' ? 'WARNING' : 'ERROR');
    box.innerHTML = `<article class="ficha-tit ${cls}"><div class="fila">${ic(ok ? 'check' : cls === 'pend' ? 'alerta' : 'x')}<b class="crece" style="font-size:var(--t-l)">${esc(T(r.message))}</b></div>
      ${b ? `<dl class="datos"><div><dt>${T('Buceador')}</dt><dd translate="no">${esc(b.name || '—')}</dd></div><div><dt>${T('Personas')}</dt><dd class="num">${b.participants}</dd></div>
        <div><dt>${T('Actividad')}</dt><dd translate="no">${esc(b.service || '—')}</dd></div><div><dt>${T('Cuándo')}</dt><dd>${fd(cuando(b.date))}${b.time ? ' · ' + esc(b.time) : ''}</dd></div>
        <div><dt>${T('Pagado')}</dt><dd class="num">${b.paid > 0 ? dinero(b.paid, b.currency) : '—'}</dd></div><div><dt>${T('Código')}</dt><dd class="num" translate="no">${esc(b.code)}</dd></div></dl>
        ${b.unsigned ? `<div class="aviso pend">${ic('documento')}<div><span class="num">${b.unsigned}</span> ${T('sin firmar el descargo. Pueden firmar en la lista del barco.')}</div></div>` : ''}` : ''}
      <div class="btn-fila">${ok && r.marked ? `<button class="wbtn sec" type="button" id="sc-deshacer">${ic('atras', '')}${T('Deshacer')}</button>` : ''}
        ${r.result === 'pendiente_pago' && puede('reservas') ? `<button class="wbtn" type="button" id="sc-cobrar">${ic('cobrar', '')}${T('Cobrar en el centro y marcar')}</button>` : ''}
        ${r.result === 'sin_aceptar' && puede('reservas') ? `<a class="wbtn" href="#/solicitudes">${T('Ver solicitudes')}</a>` : ''}
        ${b?.slot_id && (ok || usado || r.result === 'otra_salida') ? `<a class="wbtn sec" href="#/salida?id=${b.slot_id}">${ic('barco', '')}${T('Lista del barco')}</a>` : ''}
        <button class="wbtn sec" type="button" id="sc-otro">${ic('camara', '')}${T('Escanear otro')}</button></div></article>`;
    W.translateTree(box);
    $('#sc-otro', box).onclick = () => abrirCamara(root);
    $('#sc-deshacer', box)?.addEventListener('click', async () => {
      try { await postJSON('/api/manifest/sync', { changes: b.seats.map((s) => ({ slot_id: b.slot_id, booking_id: b.booking_id, seat: s.seat, field: 'status', base: 'present', value: '', force: true })) }); W.toast(T('Llegada deshecha.')); box.innerHTML = ''; }
      catch (e) { W.toast(e.message); }
    });
    $('#sc-cobrar', box)?.addEventListener('click', async () => {
      try { await postJSON(`/api/bookings/${b.booking_id}/payment`, { payment_status: 'paid', payment_method: 'en el centro' }); const r2 = await postJSON('/api/pro/escanear', { code, force: true }); pintarResultado(root, box, r2, code); }
      catch (e) { W.toast(e.message); }
    });
    if (ok && esc_.rafaga) setTimeout(() => { if (vivo(box)) abrirCamara(root); }, 1400);
  }
  // A promotion code (the web's «Validar un código»): checked, then redeemed with one more tap.
  async function promo(box, code) {
    let p;
    try { p = await api('/api/promo/' + encodeURIComponent(code.trim().toUpperCase())); } catch { return false; }
    const ok = p && (p.valid ?? p.ok ?? (p.status === 'active'));
    box.innerHTML = `<article class="ficha-tit ${ok ? '' : 'urg'}"><div class="fila">${ic(ok ? 'regalo' : 'x')}<b class="crece" style="font-size:var(--t-l)">${esc(ok ? T('Promoción válida') : (p.error || p.message || T('Esta promoción no se puede usar.')))}</b></div>
      ${p.title || p.promotion?.title ? `<p translate="no"><b>${esc(p.title || p.promotion?.title)}</b></p>` : ''}${p.holder || p.name ? `<p class="suave" translate="no">${esc(p.holder || p.name)}</p>` : ''}
      ${ok ? `<button class="wbtn ancho grande" type="button" id="pr-canjear">${ic('check', '')}${T('Canjear ahora')}</button>` : ''}</article>`;
    W.translateTree(box);
    $('#pr-canjear', box)?.addEventListener('click', async () => {
      try { await postJSON('/api/promo/' + encodeURIComponent(code.trim().toUpperCase()) + '/redeem', {}); vibrar('SUCCESS'); W.toast(T('Promoción canjeada.')); box.innerHTML = ''; }
      catch (e) { W.toast(e.message); }
    });
    return true;
  }

  /* ================================================================ SOLICITUDES */
  async function solicitudes(params) {
    const t0 = performance.now();
    if (cuentaCerrada()) return;
    if (!puede('reservas')) { location.replace('#/'); return; }
    const ver = params?.get?.('ver') === 'pago' ? 'pago' : 'sol';
    const root = pintar(`<div class="cuerpo"><h1>Solicitudes</h1><div class="seg" role="group" aria-label="${T('Solicitudes')}"><button type="button" data-ver="sol" aria-pressed="${ver === 'sol'}">${T('Por contestar')}</button><button type="button" data-ver="pago" aria-pressed="${ver === 'pago'}">${T('Pendientes de pago')}</button></div>
      <div id="wda-sol" class="pila-12">${esqueleto(2)}</div></div>`);
    $$('[data-ver]', root).forEach((b) => { b.onclick = () => { location.hash = '#/solicitudes' + (b.dataset.ver === 'pago' ? '?ver=pago' : ''); }; });
    let d;
    try { d = await api('/api/center/requests'); } catch (e) { fallo($('#wda-sol', root), e, () => solicitudes(params)); return; }
    if (!vivo(root)) return;
    cuenta.solicitudes = d.count; pintarTabs('solicitudes');
    $('[data-ver="sol"]', root).insertAdjacentHTML('beforeend', ` <span class="num">${d.count}</span>`);
    $('[data-ver="pago"]', root).insertAdjacentHTML('beforeend', ` <span class="num">${d.awaiting_payment}</span>`);
    const box = $('#wda-sol', root);
    if (ver === 'sol') pintarSolicitudes(box, d.items, () => solicitudes(params));
    else pintarPagos(box, d.awaiting_items || [], () => solicitudes(params));
    medir('solicitudes', t0);
  }
  const MOTIVOS = ['Salida completa', 'Mal tiempo', 'Sin guía disponible', 'Nivel insuficiente para esta inmersión', 'Otro motivo'];
  function pintarSolicitudes(box, items, recargar) {
    if (!items.length) { box.innerHTML = `<div class="tarjeta vacio"><p>${T('No tienes solicitudes por contestar.')}</p></div>`; return; }
    box.innerHTML = `<div class="fila"><span class="crece suave peq">${T('Toca «Aceptar» o elige varias.')}</span><button class="wbtn sec mini" type="button" id="sol-varias">${ic('check', '')}${T('Aceptar varias')}</button></div>
      ${items.map((s) => `<article class="tarjeta solicitud" data-id="${s.id}"><div class="fila"><label class="sol-sel" hidden><input type="checkbox" value="${s.id}" style="width:24px;height:24px" aria-label="${T('Elegir')}"></label>
        <div class="anillo peq ${s.minutes_left != null && s.minutes_left < 60 ? 'urg' : 'pend'}" title="${esc(minutos(s.minutes_left))}">${anilloMin(s.minutes_left)}</div>
        <div class="crece pila"><b translate="no">${esc(s.fullname)}</b><span class="suave peq"><span translate="no">${esc(s.service_title || '')}</span> · ${fd(cuando(s.booking_date))}${s.booking_time ? ' · ' + esc(s.booking_time) : ''} · ${plural(s.participants || 1, 'persona', 'personas')}</span>
        <div class="wtags">${s.enough_spots ? `<span class="wtag ok">${T('Hay plazas')}</span>` : `<span class="wtag canc">${T('No quedan plazas')}</span>`}${Number(s.price) > 0 ? `<span class="wtag neutro num">${dinero(s.price, s.currency)}</span>` : ''}${s.minutes_left != null ? `<span class="wtag pend">${ic('reloj', '')}${esc(minutos(s.minutes_left))}</span>` : ''}</div></div></div>
        ${s.notes ? `<p class="suave peq" translate="no">«${esc(s.notes)}»</p>` : ''}
        <div class="btn-fila"><button class="wbtn" type="button" data-ok="${s.id}">${ic('check', '')}${T('Aceptar')}</button><button class="wbtn sec" type="button" data-no="${s.id}">${ic('x', '')}${T('Rechazar')}</button>
        <button class="wbtn sec" type="button" data-mas="${s.id}" aria-label="${T('Más opciones')}">${ic('mas', '')}</button></div></article>`).join('')}
      <div class="btn-fila" id="sol-lote" hidden><button class="wbtn ancho grande" type="button" id="sol-lote-ok">${ic('check', '')}${T('Aceptar las elegidas')}</button></div>`;
    W.translateTree(box);
    const aceptar = async (id) => { await postJSON(`/api/bookings/${id}/status`, { status: 'confirmed' }); };
    $$('[data-ok]', box).forEach((b) => { b.onclick = async () => { b.disabled = true; try { await aceptar(b.dataset.ok); vibrar('SUCCESS'); W.toast(T('Aceptada. El buceador recibe el aviso.')); recargar(); } catch (e) { b.disabled = false; W.toast(e.message); } }; });
    $$('[data-no]', box).forEach((b) => { b.onclick = () => rechazar(+b.dataset.no, recargar); });
    $$('[data-mas]', box).forEach((b) => { b.onclick = () => masSolicitud(items.find((x) => String(x.id) === b.dataset.mas), recargar); });
    $('#sol-varias', box).onclick = () => { $$('.sol-sel', box).forEach((l) => { l.hidden = !l.hidden; }); $('#sol-lote', box).hidden = !$('#sol-lote', box).hidden; };
    $('#sol-lote-ok', box).onclick = async (e) => {
      const ids = $$('.sol-sel input:checked', box).map((x) => x.value); if (!ids.length) { W.toast(T('Elige al menos una.')); return; }
      e.currentTarget.disabled = true; let ok = 0; const err = [];
      for (const id of ids) { try { await aceptar(id); ok++; } catch (x) { err.push(x.message); } }
      vibrar(err.length ? 'WARNING' : 'SUCCESS'); W.toast(`${ok} ${T(ok === 1 ? 'aceptada.' : 'aceptadas.')}${err.length ? ' ' + err[0] : ''}`); recargar();
    };
  }
  function rechazar(id, recargar) {
    const capa = abrirHoja({ titulo: T('Rechazar la solicitud'), sub: T('El buceador recibe el motivo. No se le cobra nada.'),
      html: `<div class="wchips" role="group" aria-label="${T('Motivo')}">${MOTIVOS.map((m, i) => `<button type="button" class="wchip" data-m="${i}" aria-pressed="false">${T(m)}</button>`).join('')}</div>
        <div class="campo"><label for="rj-n">${T('Explícaselo (opcional)')}</label><textarea id="rj-n" maxlength="400"></textarea></div>`,
      pie: `<button class="wbtn peligro ancho grande" type="button" id="rj-ok">${ic('x', '')}${T('Rechazar')}</button>` });
    let motivo = '';
    $$('[data-m]', capa).forEach((b) => { b.onclick = () => { motivo = T(MOTIVOS[+b.dataset.m]); $$('[data-m]', capa).forEach((x) => x.setAttribute('aria-pressed', String(x === b))); }; });
    $('#rj-ok', capa).onclick = async () => {
      const nota = $('#rj-n', capa).value.trim(), reason = [motivo, nota].filter(Boolean).join('. ');
      try { await postJSON(`/api/bookings/${id}/status`, { status: 'rejected', reason }); cerrarHoja(); W.toast(T('Rechazada.')); recargar(); } catch (e) { W.toast(e.message); }
    };
  }
  function masSolicitud(s, recargar) {
    const capa = abrirHoja({ titulo: esc(s.fullname), sub: `<span translate="no">${esc(s.service_title || '')}</span> · ${fd(cuando(s.booking_date))}`,
      html: `<div class="tarjeta plana lista"><button class="lista-fila" type="button" data-a="otra">${ic('agenda')}<span class="crece pila"><b>${T('Ofrecer otra salida')}</b><span class="suave peq">${T('Del mismo servicio, con plazas')}</span></span>${ic('chev', 'chev')}</button>
        <button class="lista-fila" type="button" data-a="wa">${ic('wa')}<span class="crece">${T('Escribir por WhatsApp')}</span>${ic('chev', 'chev')}</button><button class="lista-fila" type="button" data-a="tel">${ic('tel')}<span class="crece">${T('Llamar')}</span>${ic('chev', 'chev')}</button>
        <a class="lista-fila" href="#/reserva?id=${s.id}">${ic('ficha')}<span class="crece">${T('Ver la reserva completa')}</span>${ic('chev', 'chev')}</a></div>` });
    $('[data-a="wa"]', capa).onclick = () => contactar(s.id, 'wa');
    $('[data-a="tel"]', capa).onclick = () => contactar(s.id, 'tel');
    $('[data-a="otra"]', capa).onclick = () => otraSalida(s.id, recargar);
  }
  async function otraSalida(bid, recargar) {
    let b, servicios;
    try { b = await api('/api/bookings/' + bid); servicios = (await api('/api/provider-services?provider_id=' + state.me.user.id)).items; } catch (e) { W.toast(e.message); return; }
    const bk = b.booking || b, svc = servicios.find((x) => x.id === bk.service_id);
    const libres = (svc?.slots || []).filter((x) => x.id !== bk.slot_id && x.status === 'open' && Number(x.spots_available) >= Number(bk.participants || 1) && x.slot_date >= hoyISO()).slice(0, 20);
    const capa = abrirHoja({ titulo: T('Ofrecer otra salida'), sub: T('La reserva se cambia a la salida que elijas y el buceador recibe el aviso.'),
      html: libres.length ? `<div class="tarjeta plana lista">${libres.map((x) => `<button class="lista-fila" type="button" data-sl="${x.id}">${ic('agenda')}<span class="crece pila"><b>${fd(cuando(x.slot_date))} · ${esc(x.slot_time || '')}</b><span class="suave peq">${plural(Number(x.spots_available), 'plaza libre', 'plazas libres')}</span></span>${ic('chev', 'chev')}</button>`).join('')}</div>`
        : `<div class="tarjeta vacio"><p>${T('No hay otras salidas de este servicio con plazas.')}</p></div>` });
    $$('[data-sl]', capa).forEach((x) => { x.onclick = async () => {
      try { await postJSON(`/api/bookings/${bid}/reschedule`, { slot_id: +x.dataset.sl, reason: T('El centro te ofrece esta salida.') }); cerrarHoja(); W.toast(T('Cambiada. El buceador recibe el aviso.')); recargar(); }
      catch (e) { W.toast(e.message); }
    }; });
  }
  function pintarPagos(box, items, recargar) {
    if (!items.length) { box.innerHTML = `<div class="tarjeta vacio"><p>${T('No hay reservas esperando el pago.')}</p></div>`; return; }
    box.innerHTML = items.map((s) => `<article class="tarjeta solicitud"><div class="fila"><div class="anillo peq ${s.minutes_left != null && s.minutes_left < 60 ? 'urg' : 'pend'}">${anilloMin(s.minutes_left)}</div>
      <div class="crece pila"><b translate="no">${esc(s.fullname)}</b><span class="suave peq"><span translate="no">${esc(s.service_title || '')}</span> · ${fd(cuando(s.booking_date))}${s.booking_time ? ' · ' + esc(s.booking_time) : ''}</span>
      <div class="wtags"><span class="wtag pend num">${dinero(s.amount_due || s.price, s.currency)}</span>${s.minutes_left != null ? `<span class="wtag pend">${ic('reloj', '')}${esc(minutos(s.minutes_left))}</span>` : ''}</div></div></div>
      <div class="btn-fila"><button class="wbtn sec" type="button" data-rec="${s.id}">${ic('wa', '')}${T('Recordar por WhatsApp')}</button><button class="wbtn" type="button" data-cob="${s.id}">${ic('cobrar', '')}${T('Cobrar en el centro')}</button></div></article>`).join('');
    W.translateTree(box);
    $$('[data-rec]', box).forEach((b) => { b.onclick = () => contactar(+b.dataset.rec, 'wa', 'pago'); });
    $$('[data-cob]', box).forEach((b) => { b.onclick = () => cobrarEnCentro(+b.dataset.cob, recargar); });
  }
  function cobrarEnCentro(id, recargar) {
    const capa = abrirHoja({ titulo: T('Cobrar en el centro'), sub: T('La plaza queda confirmada.'),
      html: `<div class="pila-8">${[['efectivo', 'Efectivo', 'cobrar'], ['tarjeta', 'Tarjeta (datáfono)', 'cobrar'], ['transferencia', 'Transferencia', 'cobrar'], ['luego', 'Pagará al llegar', 'reloj']].map(([k, t, i]) => `<button class="contar-btn" type="button" data-pm="${k}">${ic(i, '')}<span>${T(t)}</span></button>`).join('')}</div>` });
    $$('[data-pm]', capa).forEach((b) => { b.onclick = async () => {
      const luego = b.dataset.pm === 'luego';
      try { await postJSON(`/api/bookings/${id}/payment`, luego ? { payment_status: 'at_center' } : { payment_status: 'paid', payment_method: b.dataset.pm }); cerrarHoja(); vibrar('SUCCESS'); W.toast(luego ? T('Anotado: paga al llegar.') : T('Cobro anotado. Plaza confirmada.')); recargar(); }
      catch (e) { W.toast(e.message); }
    }; });
  }

  /* ================================================================ SALIDA (boat list) */
  const COLA = 'wda-pro-cola';
  const cola = () => { try { return JSON.parse(localStorage.getItem(COLA) || '[]'); } catch { return []; } };
  const guardarCola = (c) => { try { localStorage.setItem(COLA, JSON.stringify(c)); } catch { /* nothing */ } };
  async function enviarCola() {
    const c = cola(); if (!c.length) return;
    try {
      const r = await postJSON('/api/manifest/sync', { changes: c.map((x) => ({ ...x, offline: true })) });
      guardarCola([]);
      W.toast(r.conflicts?.length ? `${T('Enviadas las marcas guardadas sin conexión.')} ${r.conflicts.length} ${T('no se aplicaron porque alguien las cambió antes.')}` : T('Enviadas las marcas guardadas sin conexión.'));
      if (A.nombreRuta() === 'salida') A.rutasPro.salida(new URLSearchParams(location.hash.split('?')[1] || ''));
    } catch { /* still without coverage */ }
  }
  window.addEventListener('online', enviarCola);
  plugin('Network')?.addListener?.('networkStatusChange', (s) => { if (s.connected) enviarCola(); });
  plugin('App')?.addListener?.('resume', enviarCola);

  async function salida(params) {
    const t0 = performance.now();
    if (cuentaCerrada()) return;
    const id = +(params?.get?.('id') || 0);
    const root = pintar(`<div class="cuerpo" id="wda-sal">${esqueleto(4)}</div>`);
    let d, viejo = null;
    try { d = await api('/api/manifest/' + id); guardado.escribir('man:' + id, d); }
    catch (e) {
      const c = sinRed(e) ? guardado.leer('man:' + id) : null;
      if (!c) { fallo($('#wda-sal', root), e, () => salida(params)); return; }
      d = c.v; viejo = c.at;
    }
    if (!vivo(root)) return;
    // Marks waiting in the queue are shown as done.
    const pend = cola().filter((x) => x.slot_id === id);
    pend.forEach((x) => { const dv = d.divers.find((y) => y.booking_id === x.booking_id && y.seat === x.seat); if (dv && x.field === 'status') { dv.checked_in_at = x.value === 'present' ? x.at : null; dv.no_show = x.value === 'no_show'; dv._cola = true; } });
    const s = d.slot, presentes = d.divers.filter((x) => x.checked_in_at).length;
    const porGrupo = new Map(); d.groups.forEach((g) => porGrupo.set(g.id, { g, l: [] })); porGrupo.set(null, { g: null, l: [] });
    d.divers.forEach((x) => (porGrupo.get(x.group_id) || porGrupo.get(null)).l.push(x));
    const fila = (x) => `<div class="buceador-fila" data-b="${x.booking_id}" data-s="${x.seat}"><button type="button" translate="no" class="marca-check${x.checked_in_at ? ' si' : ''}" data-check aria-pressed="${!!x.checked_in_at}" aria-label="${x.checked_in_at ? T('Ha llegado') : T('Marcar llegada')}: ${esc(x.name || '')}">${ic(x.checked_in_at ? 'check' : x.no_show ? 'x' : 'area', '')}</button>
      <button type="button" class="crece pila" data-diver style="background:none;border:0;text-align:left;color:inherit;padding:0;min-height:56px"><b translate="no">${esc(x.name || T('Acompañante'))}</b><span class="meta">${[x.level_name ? `<span translate="no">${esc(x.level_name)}</span>` : '', x.nitrox ? 'Nitrox' : '', (x.rental || []).length ? `<span translate="no">${esc(x.rental.join(', '))}</span>` : '', d.waiver && !x.signed ? `<span class="wtag pend">${T('Sin firmar')}</span>` : '', x.no_show ? `<span class="wtag canc">${T('No vino')}</span>` : '', x._cola ? `<span class="wtag neutro">${T('Pendiente de enviar')}</span>` : ''].filter(Boolean).join(' · ')}</span></button>${ic('chev', 'chev')}</div>`;
    const grupos = [...porGrupo.values()].filter((x) => x.l.length).map(({ g, l }) => `<section class="pila-8"><h2>${g ? `<span translate="no">${esc(g.label)}</span>${g.guide ? ` · <span translate="no">${esc(g.guide)}</span>` : ''}` : T(d.groups.length ? 'Sin grupo' : 'Buceadores')} <span class="suave num">${l.filter((x) => x.checked_in_at).length}/${l.length}</span></h2><div class="tarjeta plana lista">${l.map(fila).join('')}</div></section>`).join('');
    const canc = !!d.cancelled;
    $('#wda-sal', root).innerHTML = `${viejo ? avisoViejo({ viejo: true, at: viejo }) : ''}${pend.length ? `<div class="aviso pend">${ic('reloj')}<div><span class="num">${pend.length}</span> ${T('marcas guardadas en el móvil: se envían al volver la cobertura.')}</div></div>` : ''}
      <div class="pila"><p class="suave peq">${fd(cuando(s.slot_date))} · <span class="num">${esc(s.slot_time || '')}</span></p><h1 translate="no">${esc(s.service_title)}</h1>
      <p><b class="num">${presentes}/${d.divers.length}</b> <span>${T('han llegado')}</span>${d.points.length ? ` · <span translate="no">${esc(d.points.map((p) => p.name).join(', '))}</span>` : ''}</p></div>
      ${canc ? `<div class="aviso urg">${ic('x')}<div><b>${T('Salida cancelada')}</b> ${esc(d.cancelled.note || '')}</div></div>` : ''}
      <div class="acciones tres">${puede('checkin') ? `<a class="accion" href="#/escanear?salida=${s.id}">${ic('escanear')}<span>Escanear</span></a><a class="accion" href="#/contar?id=${s.id}">${ic('area')}<span>Contar a bordo</span></a>` : ''}<a class="accion" href="#/resumen-barco?id=${s.id}">${ic('barco')}<span>Resumen barco</span></a></div>
      ${vueltaAviso(d, s)}
      ${d.warnings?.length ? `<div class="aviso pend">${ic('alerta')}<div>${d.warnings.map((w) => esc(w.text)).join('<br>')}</div></div>` : ''}
      ${d.divers.length ? grupos : `<div class="tarjeta vacio"><p>${T('Todavía no hay buceadores en esta salida.')}</p></div>`}
      <div class="tarjeta plana lista">${puede('reservas') && !esFree() && !canc ? `<a class="lista-fila" href="#/nueva-reserva?salida=${s.id}&servicio=${s.service_id}">${ic('mas1')}<span class="crece">${T('Añadir buceador')}</span>${ic('chev', 'chev')}</a>` : ''}
        ${puede('avisos') && !canc ? `<button class="lista-fila" type="button" id="sal-cambio">${ic('reloj')}<span class="crece">${T('Cambiar la hora y avisar')}</span>${ic('chev', 'chev')}</button><button class="lista-fila" type="button" id="sal-cancelar">${ic('alerta')}<span class="crece">${T('Cancelar la salida y avisar a todos')}</span>${ic('chev', 'chev')}</button>` : ''}
        <a class="lista-fila" href="#/admin?tab=planning">${ic('web')}<span class="crece pila"><b>${T('Grupos, barcos y guías')}</b><span class="suave peq">${T('Disponible en la web')}</span></span>${ic('chev', 'chev')}</a></div>`;
    W.translateTree($('#wda-sal', root));
    $$('.buceador-fila', root).forEach((f) => {
      const x = d.divers.find((y) => String(y.booking_id) === f.dataset.b && String(y.seat) === f.dataset.s);
      $('[data-check]', f).onclick = (e) => marcar(root, d, x, x.checked_in_at ? '' : 'present', e.currentTarget);
      $('[data-diver]', f).onclick = () => accionesBuceador(root, d, x, params);
    });
    $('#sal-cambio', root)?.addEventListener('click', () => avisar(s, 'cambio', () => salida(params)));
    $('#sal-cancelar', root)?.addEventListener('click', () => avisar(s, 'cancelar', () => salida(params)));
    medir('salida', t0);
  }
  async function marcar(root, d, x, valor, btn) {
    if (!puede('checkin')) { W.toast(T('Tu perfil no permite pasar lista.')); return; }
    const base = x.checked_in_at ? 'present' : x.no_show ? 'no_show' : '';
    const cambio = { slot_id: d.slot.id, booking_id: x.booking_id, seat: x.seat, field: 'status', base, value: valor, at: new Date().toISOString() };
    // At once on the screen; the server confirms.
    x.checked_in_at = valor === 'present' ? cambio.at : null; x.no_show = valor === 'no_show';
    if (btn) { btn.classList.toggle('si', valor === 'present'); btn.setAttribute('aria-pressed', String(valor === 'present')); btn.innerHTML = ic(valor === 'present' ? 'check' : valor === 'no_show' ? 'x' : 'area', ''); }
    vibrar(valor === 'present' ? 'SUCCESS' : 'WARNING');
    const aCola = () => { const c = cola().filter((y) => !(y.slot_id === cambio.slot_id && y.booking_id === cambio.booking_id && y.seat === cambio.seat && y.field === 'status')); c.push(cambio); guardarCola(c); guardado.escribir('man:' + d.slot.id, d); W.toast(T('Sin conexión: guardado en el móvil.')); };
    if (navigator.onLine === false) { aCola(); return; }
    try {
      const r = await postJSON('/api/manifest/sync', { changes: [cambio] });
      if (r.conflicts?.length) { const c = r.conflicts[0]; W.toast(`${T('Lo cambió antes')} ${c.server_by || T('otra persona')}.`); }
      guardado.escribir('man:' + d.slot.id, d);
    } catch (e) {
      if (sinRed(e)) aCola();
      else W.toast(e.message);
    }
  }
  function accionesBuceador(root, d, x, params) {
    const capa = abrirHoja({ titulo: `<span translate="no">${esc(x.name || T('Acompañante'))}</span>`, sub: [x.level_name, x.nitrox ? 'Nitrox' : ''].filter(Boolean).map(esc).join(' · '),
      html: `${x.sizes ? `<dl class="datos">${Object.entries(x.sizes).map(([k, v]) => `<div><dt>${esc(T({ suit_type: 'Traje', suit_size: 'Talla de traje', boot_size: 'Escarpines', bcd_size: 'Chaleco', fin_size: 'Aletas', mask_size: 'Máscara', usual_weight_kg: 'Lastre (kg)' }[k] || k))}</dt><dd translate="no">${esc(v)}</dd></div>`).join('')}</dl>` : ''}
        ${x.emergency ? `<div class="aviso neutro">${ic('tel')}<div><b>${T('Contacto de emergencia')}</b> <span translate="no">${esc(x.emergency.name || '')} · ${esc(x.emergency.phone || '')}</span></div></div>` : ''}
        ${x.notes ? `<p class="suave" translate="no">«${esc(x.notes)}»</p>` : ''}
        <div class="tarjeta plana lista">${puede('checkin') ? `<button class="lista-fila" type="button" data-a="ns">${ic('x')}<span class="crece">${x.no_show ? T('Quitar «No vino»') : T('No vino')}</span></button>` : ''}
          <button class="lista-fila" type="button" data-a="tel">${ic('tel')}<span class="crece">${T('Llamar')}</span></button><button class="lista-fila" type="button" data-a="wa">${ic('wa')}<span class="crece">${T('WhatsApp en su idioma')}</span></button>
          ${puede('checkin') ? `<button class="lista-fila" type="button" data-a="nota">${ic('lapiz')}<span class="crece">${T('Nota para el barco')}</span></button>` : ''}
          ${d.waiver && !x.signed ? `<a class="lista-fila" href="#/reserva?id=${x.booking_id}">${ic('documento')}<span class="crece pila"><b>${T('Firmar el descargo')}</b><span class="suave peq">${T('Desde la reserva, en este móvil')}</span></span>${ic('chev', 'chev')}</a>` : ''}
          <a class="lista-fila" href="#/reserva?id=${x.booking_id}">${ic('ficha')}<span class="crece">${T('Ver la reserva')}</span>${ic('chev', 'chev')}</a></div>` });
    $('[data-a="tel"]', capa).onclick = () => contactar(x.booking_id, 'tel');
    $('[data-a="wa"]', capa).onclick = () => contactar(x.booking_id, 'wa');
    $('[data-a="ns"]', capa)?.addEventListener('click', async () => { cerrarHoja(); await marcar(root, d, x, x.no_show ? '' : 'no_show', null); salida(params); });
    $('[data-a="nota"]', capa)?.addEventListener('click', () => {
      const c2 = abrirHoja({ titulo: T('Nota para el barco'), html: `<div class="campo"><label for="nt-t">${T('Solo la ve el equipo')}</label><textarea id="nt-t" maxlength="500">${esc(x.note || '')}</textarea></div>`, pie: `<button class="wbtn ancho grande" type="button" id="nt-ok">${T('Guardar')}</button>` });
      $('#nt-ok', c2).onclick = async () => {
        try { await postJSON('/api/manifest/sync', { changes: [{ slot_id: d.slot.id, booking_id: x.booking_id, seat: x.seat, field: 'note', base: x.note || '', value: $('#nt-t', c2).value, force: true }] }); cerrarHoja(); salida(params); }
        catch (e) { W.toast(e.message); }
      };
    });
  }
  // Change the time or cancel a departure and tell everybody (WhatsApp, email and the app). 10 s to undo.
  async function avisar(s, que, despues) {
    const kind = que === 'cancelar' ? 'slot_cancelled' : 'slot_changed';
    const capa = abrirHoja({ titulo: T(que === 'cancelar' ? 'Cancelar la salida y avisar a todos' : 'Cambiar la hora y avisar'), sub: `<span translate="no">${esc(s.service_title)}</span> · ${fd(cuando(s.slot_date))} · ${esc(s.slot_time || '')}`,
      html: `<div class="pila-12">${que === 'cancelar' ? `<div class="wchips" role="group" aria-label="${T('Motivo')}">${[['weather', 'Mal tiempo'], ['sea', 'Estado del mar'], ['boat', 'Avería del barco'], ['other', 'Otro motivo']].map(([k, t], i) => `<button type="button" class="wchip" data-r="${k}" aria-pressed="${i === 0}">${T(t)}</button>`).join('')}</div>`
        : `<div class="campo"><label for="av-h">${T('Nueva hora')}</label><input id="av-h" type="time" value="${esc(s.slot_time || '')}"></div><div class="campo"><label for="av-p">${T('Punto de encuentro (opcional)')}</label><input id="av-p" maxlength="160"></div>`}
        <div class="campo"><label for="av-n">${T('Nota para los buceadores (opcional)')}</label><textarea id="av-n" maxlength="300"></textarea></div><div id="av-prev"></div></div>`,
      pie: `<button class="wbtn ancho grande" type="button" id="av-ver">${T('Ver a quién avisamos')}</button>` });
    let reason = 'weather';
    $$('[data-r]', capa).forEach((b) => { b.onclick = () => { reason = b.dataset.r; $$('[data-r]', capa).forEach((x) => x.setAttribute('aria-pressed', String(x === b))); }; });
    const datos = () => ({ slot_id: s.id, kind, reason: que === 'cancelar' ? reason : undefined, note: $('#av-n', capa).value, new_time: $('#av-h', capa)?.value || undefined, meeting_point: $('#av-p', capa)?.value || undefined });
    $('#av-ver', capa).onclick = async () => {
      let p; try { p = await postJSON('/api/avisos/preview', datos()); } catch (e) { W.toast(e.message); return; }
      const prev = p.previews?.[0];
      $('#av-prev', capa).innerHTML = `<div class="aviso ${que === 'cancelar' ? 'urg' : 'pend'}">${ic('avisos')}<div><b class="num">${p.recipients}</b> ${T(p.recipients === 1 ? 'buceador recibe el aviso' : 'buceadores reciben el aviso')} ${p.whatsapp?.connected ? T('por WhatsApp, email y la app.') : T('por email y la app.')}</div></div>
        ${prev ? `<p class="suave peq" style="white-space:pre-line">${esc(prev.whatsapp).slice(0, 600)}</p>` : ''}
        <div class="campo"><label for="av-c">${T('Para confirmar, escribe la fecha de la salida')} (<span class="num">${esc(p.confirm_hint.date)}</span>)</label><input id="av-c" inputmode="numeric" autocomplete="off"></div>`;
      W.translateTree($('#av-prev', capa));
      const pie = capa.querySelector('.hoja-pie'); pie.innerHTML = `<button class="wbtn ${que === 'cancelar' ? 'peligro' : ''} ancho grande" type="button" id="av-ok">${ic('avisos', '')}${T(que === 'cancelar' ? 'Cancelar y avisar' : 'Cambiar y avisar')}</button>`; W.translateTree(pie);
      $('#av-ok', capa).onclick = async (e) => {
        e.currentTarget.disabled = true;
        try {
          const r = await postJSON(que === 'cancelar' ? '/api/avisos/cancelar' : '/api/avisos/cambio', { ...datos(), confirm: $('#av-c', capa).value });
          cerrarHoja(); deshacer(r, despues);
        } catch (err) { e.currentTarget.disabled = false; W.toast(err.message); }
      };
    };
  }
  function deshacer(r, despues) {
    const el = document.createElement('div'); el.className = 'wda wda-deshacer'; el.setAttribute('role', 'status');
    let n = r.undo_seconds || 10;
    el.innerHTML = `<span class="crece">${T('Avisos en cola. Salen en')} <b class="num" id="dh-n">${n}</b> <span translate="no">s</span></span><button class="wbtn sec mini" type="button" id="dh-b">${T('Deshacer')}</button>`;
    document.body.appendChild(el); W.translateTree(el);
    const t = setInterval(() => { n--; const x = $('#dh-n', el); if (x) x.textContent = String(n); if (n <= 0) { clearInterval(t); el.remove(); W.toast(T('Avisos enviados.')); despues(); } }, 1000);
    $('#dh-b', el).onclick = async () => { clearInterval(t); try { await postJSON(`/api/avisos/${r.uid}/deshacer`, {}); W.toast(T('Deshecho: no se ha avisado a nadie.')); } catch (e) { W.toast(e.message); } el.remove(); despues(); };
  }

  /* ---------------------------------------------------------------- summary for the boat and counting on board */
  async function resumenBarco(params) {
    const id = +(params?.get?.('id') || 0);
    const root = pintar(`<div class="cuerpo" id="wda-rb">${esqueleto(3)}</div>`);
    let d; try { d = await api('/api/manifest/' + id); } catch (e) { const c = sinRed(e) ? guardado.leer('man:' + id) : null; if (!c) { fallo($('#wda-rb', root), e, () => resumenBarco(params)); return; } d = c.v; }
    if (!vivo(root)) return;
    const s = d.slot, nx = d.divers.filter((x) => x.nitrox).length, alq = d.divers.filter((x) => (x.rental || []).length).length;
    const grupos = d.groups.length ? d.groups.map((g) => ({ g, l: d.divers.filter((x) => x.group_id === g.id) })).concat([{ g: null, l: d.divers.filter((x) => !x.group_id) }]).filter((x) => x.l.length) : [{ g: null, l: d.divers }];
    const texto = [`${s.service_title} · ${s.slot_date} ${s.slot_time || ''}`, `${d.divers.length} ${T('buceadores')} · Nitrox ${nx} · ${T('Alquiler')} ${alq}`,
      ...grupos.map(({ g, l }) => `\n${g ? g.label + (g.guide ? ' · ' + g.guide : '') : T('Sin grupo')}\n` + l.map((x) => `- ${x.name || T('Acompañante')}${x.level_name ? ' (' + x.level_name + ')' : ''}${x.nitrox ? ' Nx' : ''}`).join('\n'))].join('\n');
    $('#wda-rb', root).innerHTML = `<div class="resumen-barco"><p class="suave peq">${fd(cuando(s.slot_date))} · <span class="num">${esc(s.slot_time || '')}</span></p><h1 translate="no">${esc(s.service_title)}</h1>
      <div class="cifras"><div class="tarjeta cifra"><b class="num">${d.divers.length}</b><span>${T('buceadores')}</span></div><div class="tarjeta cifra"><b class="num">${nx}</b><span>Nitrox</span></div><div class="tarjeta cifra"><b class="num">${alq}</b><span>${T('con alquiler')}</span></div></div>
      ${grupos.map(({ g, l }) => `<div class="rb-fila"><b>${g ? `<span translate="no">${esc(g.label)}</span>${g.guide ? ` · <span translate="no">${esc(g.guide)}</span>` : ''}` : T('Sin grupo')}</b>${l.map((x) => `<span translate="no">${esc(x.name || T('Acompañante'))}${x.level_name ? ' · ' + esc(x.level_name) : ''}${x.nitrox ? ' · Nx' : ''}</span>`).join('')}</div>`).join('')}</div>
      <div class="btn-fila"><button class="wbtn" type="button" id="rb-comp">${ic('compartir', '')}${T('Compartir el resumen')}</button><button class="wbtn sec" type="button" id="rb-pdf">${ic('documento', '')}${T('PDF firmado')}</button></div>
      <p class="suave peq">${T('El PDF lleva su huella SHA-256 y quién lo generó: la copia impresa se puede comprobar con el servidor.')}</p>`;
    W.translateTree($('#wda-rb', root));
    $('#rb-comp', root).onclick = () => compartir({ titulo: s.service_title, texto, url: '' });
    $('#rb-pdf', root).onclick = async () => {
      // In a browser the tab is opened at once (inside the tap) and receives the link; in the app the phone's browser opens it.
      const tab = APP.native ? null : window.open('about:blank', '_blank');
      try { const r = await postJSON(`/api/manifest/${id}/resumen-enlace`, {}); if (tab) tab.location.href = r.url; else abrirFuera(r.url); }
      catch (e) { tab?.close(); W.toast(e.message); }
    };
  }
  // v50.55 (brief de la app): count again when coming back, before the departure is over.
  function vueltaAviso(d, s) {
    const h = d.headcounts || {};
    if (!h.salida || !puede('checkin') || d.cancelled) return '';
    if (h.vuelta) return `<div class="aviso ${h.vuelta.match ? 'ok' : 'urg'}">${ic(h.vuelta.match ? 'check' : 'alerta')}<div><b>${T('Contados a la vuelta')}:</b> <span class="num">${h.vuelta.counted}/${h.vuelta.present}</span></div></div>`;
    return `<div class="aviso urg">${ic('area')}<div class="crece"><b>${T('Falta contar a la vuelta')}</b><p>${T('Al salir contaste')} <span class="num">${h.salida.counted}</span>.</p><p>${T('Antes de terminar la salida, cuenta otra vez a todos en el barco.')}</p>
      <a class="wbtn mini" href="#/contar?id=${s.id}&fase=vuelta">${ic('area', '')}${T('Contar a la vuelta')}</a></div></div>`;
  }
  async function contar(params) {
    const id = +(params?.get?.('id') || 0), fase = params?.get?.('fase') === 'vuelta' ? 'vuelta' : 'salida';
    const root = pintar(`<div class="cuerpo" id="wda-ct">${esqueleto(3)}</div>`);
    let d; try { d = await api('/api/manifest/' + id); } catch (e) { const c = sinRed(e) ? guardado.leer('man:' + id) : null; if (!c) { fallo($('#wda-ct', root), e, () => contar(params)); return; } d = c.v; }
    if (!vivo(root)) return;
    const lista = d.divers.filter((x) => x.checked_in_at);
    let n = 0; const tocados = new Set();
    $('#wda-ct', root).innerHTML = `<h1>${T(fase === 'vuelta' ? 'Contar a la vuelta' : 'Contar a bordo')}</h1><p class="suave">${T('Toca a cada persona que ves en el barco, o cuenta con + y −.')}</p>
      <div class="contar-cifra num" id="ct-n" aria-live="polite">0</div><p class="suave" style="text-align:center"><span>${T('de')}</span> <b class="num">${lista.length}</b> <span>${T('que han llegado')}</span></p>
      <div class="btn-fila"><button class="wbtn sec grande crece" type="button" id="ct-menos" aria-label="${T('Uno menos')}">${ic('menos', '')}</button><button class="wbtn sec grande crece" type="button" id="ct-mas" aria-label="${T('Uno más')}">${ic('mas1', '')}</button></div>
      <div class="pila-8">${lista.map((x, i) => `<button class="contar-btn" type="button" data-i="${i}" aria-pressed="false">${ic('area', '')}<span class="crece" translate="no">${esc(x.name || T('Acompañante'))}</span></button>`).join('')}</div>
      <button class="wbtn ancho grande" type="button" id="ct-ok">${ic('check', '')}${T('Comprobar')}</button><div id="ct-res"></div>`;
    W.translateTree($('#wda-ct', root));
    const pon = (v) => { n = Math.max(0, v); $('#ct-n', root).textContent = String(n); };
    $('#ct-mas', root).onclick = () => { pon(n + 1); vibrar('SUCCESS'); };
    $('#ct-menos', root).onclick = () => pon(n - 1);
    $$('[data-i]', root).forEach((b) => { b.onclick = () => { const on = !tocados.has(b.dataset.i); on ? tocados.add(b.dataset.i) : tocados.delete(b.dataset.i); b.setAttribute('aria-pressed', String(on)); pon(n + (on ? 1 : -1)); }; });
    $('#ct-ok', root).onclick = async () => {
      let r; try { r = await postJSON('/api/pro/contar', { slot_id: id, count: n, fase }); } catch (e) { r = { counted: n, present: lista.length, match: n === lista.length, diff: n - lista.length, sinRed: sinRed(e) }; }
      const falta = lista.filter((x, i) => !tocados.has(String(i)));
      vibrar(r.match ? 'SUCCESS' : 'ERROR');
      $('#ct-res', root).innerHTML = r.match ? `<div class="aviso ok">${ic('check')}<div><b>${T('Están todos.')}</b> <span class="num">${r.counted}</span> ${T('a bordo.')}</div></div>`
        : `<div class="aviso urg">${ic('alerta')}<div><b>${r.diff < 0 ? `${T('Faltan')} <span class="num">${-r.diff}</span>` : `${T('Sobran')} <span class="num">${r.diff}</span>`}</b>${r.diff < 0 && tocados.size ? `<p>${T('Sin tocar:')} <span translate="no">${falta.map((x) => esc(x.name || '')).join(', ')}</span></p>` : ''}</div></div>`;
      if (r.sinRed) $('#ct-res', root).insertAdjacentHTML('beforeend', `<p class="suave peq">${T('Sin conexión: el recuento no se ha guardado en el historial.')}</p>`);
      W.translateTree($('#ct-res', root));
    };
  }

  /* ================================================================ RESERVAS */
  const filtroRes = { q: '', chip: 'proximas' };
  async function reservasPro() {
    if (cuentaCerrada()) return;
    const chips = [['hoy', 'Hoy'], ['proximas', 'Próximas'], ['pago', 'Pendientes de pago'], ['canceladas', 'Canceladas']];
    const root = pintar(`<div class="cuerpo"><div class="seccion-cab"><h1>Reservas</h1>${puede('reservas') && !esFree() ? `<a class="wbtn mini" href="#/nueva-reserva">${ic('mas1', '')}Nueva</a>` : ''}</div>
      <label class="buscador">${ic('buscar', '')}<input id="rs-q" type="search" placeholder="${T('Nombre, email o nº de reserva')}" value="${esc(filtroRes.q)}" style="border:0;background:none;flex:1;font:inherit;color:inherit;min-width:0" aria-label="${T('Buscar reservas')}"></label>
      <div class="wchips" role="group" aria-label="${T('Filtro')}">${chips.map(([k, t]) => `<button type="button" class="wchip" data-chip="${k}" aria-pressed="${filtroRes.chip === k}">${T(t)}</button>`).join('')}</div>
      <div id="rs-l" class="pila-8">${esqueleto(3)}</div></div>`);
    const cargar = async () => {
      const q = new URLSearchParams({ limit: '60' }); const h = hoyISO();
      if (filtroRes.q) q.set('q', filtroRes.q);
      if (filtroRes.chip === 'hoy') { q.set('from', h); q.set('to', h); }
      if (filtroRes.chip === 'proximas') { q.set('from', h); q.set('order', 'asc'); }
      if (filtroRes.chip === 'pago') q.set('status', 'accepted_pending_payment');
      if (filtroRes.chip === 'canceladas') q.set('status', 'cancelled');
      const box = $('#rs-l', root);
      let d; try { d = await api('/api/bookings?' + q); } catch (e) { fallo(box, e, cargar); return; }
      if (!vivo(box)) return;
      const items = (d.items || []).filter((b) => filtroRes.chip !== 'proximas' || !['cancelled', 'rejected', 'expired'].includes(b.status));
      box.innerHTML = items.length ? `<div class="tarjeta plana lista">${items.map((b) => `<a class="lista-fila" href="#/reserva?id=${b.id}"><div class="fecha-b"><b class="num">${Number(String(b.booking_date).slice(8, 10))}</b><small translate="no">${esc(fecha(b.booking_date, { month: 'short' }).replace('.', ''))}</small></div>
        <div class="crece pila"><b translate="no">${esc(b.fullname || b.contact_name || '')}</b><span class="suave peq"><span translate="no">${esc(b.service_title || '')}</span>${b.booking_time ? ' · ' + esc(b.booking_time) : ''} · ${plural(Number(b.participants || 1), 'persona', 'personas')}</span><div class="wtags">${A.estadoTag(b)}</div></div>${ic('chev', 'chev')}</a>`).join('')}</div>`
        : `<div class="tarjeta vacio"><p>${T('No hay reservas con este filtro.')}</p></div>`;
      W.translateTree(box);
    };
    let t = null;
    $('#rs-q', root).oninput = (e) => { clearTimeout(t); t = setTimeout(() => { filtroRes.q = e.target.value.trim(); cargar(); }, 300); };
    $$('[data-chip]', root).forEach((b) => { b.onclick = () => { filtroRes.chip = b.dataset.chip; $$('[data-chip]', root).forEach((x) => x.setAttribute('aria-pressed', String(x === b))); cargar(); }; });
    cargar();
  }
  // A booking taken by phone or at the desk: name, activity, departure, people. Less than 45 seconds.
  async function nuevaReserva(params) {
    const t0 = performance.now();
    if (esFree() || !puede('reservas')) { location.replace('#/mas'); return; }
    let servicios;
    try { servicios = (await api('/api/provider-services?provider_id=' + state.me.user.id)).items.filter((s) => s.active !== 0); } catch (e) { W.toast(e.message); return; }
    const sv0 = params?.get?.('servicio') || servicios[0]?.id, sl0 = params?.get?.('salida') || '';
    const salidasDe = (sid) => (servicios.find((s) => String(s.id) === String(sid))?.slots || []).filter((x) => x.slot_date >= hoyISO() && ['open', 'full'].includes(x.status)).slice(0, 40);
    const root = pintar(`<div class="cuerpo"><h1>Nueva reserva</h1><form id="nr" class="pila-12">
      <div class="campo"><label for="nr-n">${T('Nombre del cliente')}</label><input id="nr-n" required maxlength="180" autocomplete="off" enterkeyhint="next"></div>
      <div class="fila"><div class="campo crece"><label for="nr-t">${T('Teléfono')}</label><input id="nr-t" type="tel" inputmode="tel" placeholder="+34 600 000 000" autocomplete="off"></div></div>
      <div class="campo"><label for="nr-e">${T('Email (opcional)')}</label><input id="nr-e" type="email" inputmode="email" autocomplete="off"></div>
      <div class="campo"><label for="nr-s">${T('Actividad')}</label><select id="nr-s">${servicios.map((s) => `<option value="${s.id}" ${String(s.id) === String(sv0) ? 'selected' : ''} translate="no">${esc(s.title)}</option>`).join('')}</select></div>
      <div class="campo"><label for="nr-sl">${T('Salida')}</label><select id="nr-sl"></select></div>
      <div class="campo"><span class="eti">${T('Personas')}</span><div class="fila"><button class="wbtn sec grande" type="button" id="nr-m" aria-label="${T('Una menos')}">${ic('menos', '')}</button><b class="num crece" id="nr-p" style="text-align:center;font-size:32px">1</b><button class="wbtn sec grande" type="button" id="nr-mas" aria-label="${T('Una más')}">${ic('mas1', '')}</button></div></div>
      <div class="seg" role="group" aria-label="${T('Pago')}"><button type="button" data-pg="required" aria-pressed="true">${T('Paga al llegar')}</button><button type="button" data-pg="paid" aria-pressed="false">${T('Ya ha pagado')}</button></div>
      <button class="wbtn ancho grande" type="submit">${ic('check', '')}${T('Guardar la reserva')}</button></form></div>`);
    let p = 1, pago = 'required';
    const llenar = () => { const l = salidasDe($('#nr-s', root).value); $('#nr-sl', root).innerHTML = l.length ? l.map((x) => `<option value="${x.id}" ${String(x.id) === String(sl0) ? 'selected' : ''}>${fd(cuando(x.slot_date))} · ${esc(x.slot_time || '')} · ${x.spots_available} ${T('libres')}</option>`).join('') : `<option value="">${T('Sin salidas: se guarda con la fecha de hoy')}</option>`; };
    llenar(); $('#nr-s', root).onchange = llenar;
    $('#nr-m', root).onclick = () => { p = Math.max(1, p - 1); $('#nr-p', root).textContent = p; };
    $('#nr-mas', root).onclick = () => { p = Math.min(50, p + 1); $('#nr-p', root).textContent = p; };
    $$('[data-pg]', root).forEach((b) => { b.onclick = () => { pago = b.dataset.pg; $$('[data-pg]', root).forEach((x) => x.setAttribute('aria-pressed', String(x === b))); }; });
    $('#nr-n', root).focus();
    $('#nr', root).onsubmit = async (e) => {
      e.preventDefault(); const btn = e.submitter || $('#nr [type=submit]', root); btn.disabled = true;
      const slot = $('#nr-sl', root).value;
      try {
        const r = await postJSON('/api/center/bookings/manual', { fullname: $('#nr-n', root).value, phone: $('#nr-t', root).value, email: $('#nr-e', root).value, service_id: +$('#nr-s', root).value,
          slot_id: slot ? +slot : undefined, booking_date: slot ? undefined : hoyISO(), participants: p, status: 'confirmed', payment_status: pago });
        medir('nueva-reserva', t0); vibrar('SUCCESS'); W.toast(T('Reserva guardada.'));
        location.hash = slot ? '#/salida?id=' + slot : '#/reserva?id=' + r.id;
      } catch (err) { btn.disabled = false; W.toast(err.message); }
    };
  }

  /* ================================================================ MÁS */
  async function mas() {
    if (cuentaCerrada()) return;
    const me = state.me, pl = me?.plan;
    const fila = (href, icono, a, b = '', web = false) => `<a class="lista-fila" href="${href}">${ic(icono)}<span class="crece pila"><b>${a}</b>${b || web ? `<span class="suave peq">${b ? `<span>${b}</span>` : ''}${web ? `${b ? ' · ' : ''}${ic('web', 'ic-mini')} <span>${T('Disponible en la web')}</span>` : ''}</span>` : ''}</span>${ic('chev', 'chev')}</a>`;
    const root = pintar(cabecera(T('Más')) + `<div class="cuerpo">
      ${pl && pl.status !== 'active' ? `<div class="aviso pend">${ic('info')}<div>${pl.status === 'trial' ? `${T('Prueba gratuita del plan')} <span translate="no">${esc(pl.name || '')}</span>` : T('Tu plan ha terminado: tu ficha sigue visible con lo básico.')}</div></div>` : ''}
      <div id="mas-wa"></div>
      <p class="eti">${T('Trabajo diario')}</p><div class="tarjeta plana lista">${fila('#/reservas', 'reservas', T('Reservas'), T('Buscar, cobrar, cambiar'))}${puede('reservas') && !esFree() ? fila('#/nueva-reserva', 'mas1', T('Nueva reserva'), T('Por teléfono o en el mostrador')) : ''}
        ${puede('estadisticas') ? fila('#/estadisticas', 'graficas', T('Estadísticas'), T('Visitas, clics en «Reservar» y solicitudes')) : ''}${puede('cobros') ? fila('#/cobros-app', 'cobrar', T('Cobros'), T('Lo cobrado y las devoluciones pendientes')) : ''}</div>
      <p class="eti">${ic('web', 'ic-mini')} <span>${T('Disponible en la web')}</span></p><div class="tarjeta plana lista">${fila('#/admin?tab=services', 'agenda', T('Servicios y precios'))}${!esFree() ? fila('#/admin?tab=planning', 'barco', T('Barcos, grupos y guías')) : ''}
        ${puede('avisos') ? fila('#/admin?tab=avisos', 'avisos', T('Avisos y WhatsApp Business')) : ''}${esDueno() && !esFree() ? fila('#/admin?tab=team', 'equipo', T('Equipo y perfiles'), T('Quién entra y qué puede hacer')) : ''}
        ${esFree() ? fila('#/admin?tab=agenda', 'reloj', T('Horario y días de cierre')) : ''}${puede('centro') ? fila('#/admin?tab=' + (esFree() ? 'profile' : 'center'), 'tienda', T(esFree() ? 'Mi ficha pública' : 'Ficha del centro')) : ''}${fila('#/admin?tab=tools', 'cartel', T('Herramientas'), T('Calendario (iCal), cartel, exportar'))}${esDueno() ? fila('#/admin?tab=plan', 'puntos', T('Mi plan')) : ''}</div>
      <p class="eti">${T('Cuenta')}</p><div class="tarjeta plana lista">${fila('#/cuenta', 'ficha', T('Mi cuenta'), T('Datos, contraseña e idioma'))}${fila('#/ajustes', 'ajustes', T('Ajustes'), T('Tema y tamaño del texto'))}${fila('#/legal', 'documento', T('Privacidad y textos legales'))}
        ${(me?.centers || []).length > 1 ? `<button class="lista-fila" type="button" id="wda-centro">${ic('mover')}<span class="crece">${T('Cambiar de centro')}</span>${ic('chev', 'chev')}</button>` : ''}
        <button class="lista-fila" type="button" id="mas-salir">${ic('salir')}<span class="crece">${T('Cerrar sesión')}</span>${ic('chev', 'chev')}</button>
        ${esDueno() ? `<a class="lista-fila" href="#/cerrar-cuenta" style="color:var(--urg-t)">${ic('papelera')}<span class="crece">${T('Borrar mi cuenta para siempre')}</span>${ic('chev', 'chev')}</a>` : ''}</div>
      <p class="version" id="mas-v" translate="no">WORLDIVES</p></div>`);
    enlazarCentro(root);
    $('#mas-salir', root).onclick = A.salir;
    A.infoApp().then((i) => { const v = $('#mas-v', root); if (v) v.textContent = i.version; }).catch(() => {});
    if (puede('avisos')) api('/api/avisos/ajustes').then((c) => {
      const box = $('#mas-wa', root); if (!vivo(box)) return;
      const w = c.whatsapp || {};
      box.innerHTML = `<div class="aviso ${w.connected ? 'ok' : 'neutro'}">${ic('wa')}<div><b translate="no">WhatsApp Business</b> · ${w.connected ? `<span>${T('conectado')}</span>${w.number ? ` <span class="num" translate="no">${esc(w.number)}</span>` : ''}` : `<span>${T('sin conectar: los avisos salen por email y en la app.')}</span>`}</div></div>`;
      W.translateTree(box);
    }).catch(() => {});
  }
  async function estadisticas() {
    if (!puede('estadisticas')) { location.replace('#/mas'); return; }
    const root = pintar(`<div class="cuerpo"><h1>Estadísticas</h1><div class="seg" role="group" aria-label="${T('Periodo')}">${[7, 30, 90].map((n) => `<button type="button" data-d="${n}" aria-pressed="${n === 30}"><span class="num">${n}</span> ${T('días')}</button>`).join('')}</div><div id="es" class="pila-12">${esqueleto(2)}</div></div>`);
    const cargar = async (dias) => {
      const box = $('#es', root);
      let d; try { d = await api('/api/provider/stats?days=' + dias); } catch (e) { fallo(box, e, () => cargar(dias)); return; }
      const t = d.totals, z = d.zone, max = Math.max(1, ...d.series.map((x) => x.views));
      box.innerHTML = `<div class="cifras"><div class="tarjeta cifra"><b class="num">${t.views}</b><span>${T('visitas a tu ficha')}</span></div><div class="tarjeta cifra"><b class="num">${t.book_clicks}</b><span>${T('clics en «Reservar»')}</span></div><div class="tarjeta cifra"><b class="num">${t.info_requests}</b><span>${T('solicitudes de información')}</span></div></div>
        <div class="tarjeta pad"><div class="graf-barras" role="img" aria-label="${T('Visitas por día')}">${d.series.map((x) => `<span style="height:${Math.round(100 * x.views / max)}%" title="${esc(x.day)}: ${x.views}"></span>`).join('')}</div></div>
        ${z ? `<p class="suave">${T('Media de los centros de')} <span translate="no">${esc(z.name)}</span>: <span class="num">${z.views}</span> ${T('visitas y')} <span class="num">${z.book_clicks}</span> ${T('clics en «Reservar».')}</p>` : ''}`;
      W.translateTree(box);
    };
    $$('[data-d]', root).forEach((b) => { b.onclick = () => { $$('[data-d]', root).forEach((x) => x.setAttribute('aria-pressed', String(x === b))); cargar(+b.dataset.d); }; });
    cargar(30);
  }
  async function cobros() {
    if (!puede('cobros')) { location.replace('#/mas'); return; }
    const root = pintar(`<div class="cuerpo"><h1>Cobros</h1><div id="cb" class="pila-12">${esqueleto(3)}</div></div>`);
    const box = $('#cb', root);
    let d; try { d = await api('/api/provider/payments'); } catch (e) { fallo(box, e, cobros); return; }
    if (!vivo(box)) return;
    box.innerHTML = `<div class="cifras">${(d.income.length ? d.income : [{ currency: 'EUR', net: 0, n: 0, refunded: 0 }]).map((x) => `<div class="tarjeta cifra"><b class="num">${dinero(x.net, x.currency)}</b><span><span class="num">${x.n}</span> ${T('cobros online, netos de devoluciones')}</span></div>`).join('')}</div>
      ${d.pending_refunds.length ? `<div class="aviso urg">${ic('alerta')}<div><b class="num">${d.pending_refunds.length}</b> ${T('devoluciones por hacer. Se hacen desde la reserva.')}</div></div><div class="tarjeta plana lista">${d.pending_refunds.map((b) => `<a class="lista-fila" href="#/reserva?id=${b.id}">${ic('cobrar')}<span class="crece pila"><b translate="no">${esc(b.customer_name)}</b><span class="suave peq num">${dinero(b.refund_proposed, b.currency)} · ${fd(corto(b.booking_date))}</span></span>${ic('chev', 'chev')}</a>`).join('')}</div>` : ''}
      <h2>${T('Últimos cobros')}</h2><div class="tarjeta plana lista">${d.items.slice(0, 30).map((p) => `<a class="lista-fila" href="${p.booking_id ? '#/reserva?id=' + p.booking_id : '#/admin?tab=payments'}">${ic('cobrar')}<span class="crece pila"><b translate="no">${esc(p.customer_name || '')}</b><span class="suave peq"><span translate="no">${esc(p.service_title || '')}</span> · ${fd(corto((p.paid_at || p.created_at || '').slice(0, 10)))}</span></span><b class="num">${dinero(p.amount_received || p.amount, p.currency)}</b></a>`).join('') || `<div class="lista-fila suave">${T('Todavía no hay cobros online.')}</div>`}</div>
      <a class="wbtn sec ancho" href="#/admin?tab=payments">${ic('web', '')}${T('Todo en la web: Stripe, facturas y exportar')}</a>`;
    W.translateTree(box);
  }

  /* ---------------------------------------------------------------- «Borrar mi cuenta para siempre» */
  async function cerrarCuenta() {
    if (!esDueno()) { location.replace('#/mas'); return; }
    if (state.me?.account_closed) { cuentaCerrada(); return; }
    const root = pintar(`<div class="cuerpo" id="cc">${esqueleto(2)}</div>`);
    const box = $('#cc', root);
    let st; try { st = await api('/api/provider/cuenta'); } catch (e) { fallo(box, e, cerrarCuenta); return; }
    if (!vivo(box)) return;
    const lista = st.future.slice(0, 15).map((b) => `<div class="lista-fila">${ic('agenda')}<span class="crece pila"><b translate="no">${esc(b.name || '')}</b><span class="suave peq">${fd(cuando(b.booking_date))}${b.booking_time ? ' · ' + esc(b.booking_time) : ''} · <span translate="no">${esc(b.service_title || '')}</span>${b.paid > 0 ? ` · ${T('pagado')} <span class="num">${dinero(b.paid, b.currency)}</span>` : ''}</span></span></div>`).join('');
    box.innerHTML = `<h1>Borrar mi cuenta para siempre</h1>
      <div class="aviso neutro">${ic('info')}<div><span>${T('Tu cuenta se cierra ahora: deja de verse y nadie puede reservar.')}</span> <b>${T('Guardamos todo durante 6 meses')}</b>: <span>${T('si en ese tiempo entras y pulsas «Reabrir mi cuenta», lo recuperas tal como estaba. Pasados los 6 meses lo borramos todo, salvo los pagos y los datos fiscales que la ley obliga a guardar.')}</span></div></div>
      ${st.future_count ? `<div class="aviso urg">${ic('alerta')}<div><span>${T('Tienes')}</span> <b class="num">${st.future_count}</b> <span>${T(st.future_count === 1 ? 'reserva próxima. Antes de cerrar hay que resolverla.' : 'reservas próximas. Antes de cerrar hay que resolverlas.')}</span></div></div>
        <div class="tarjeta plana lista">${lista}${st.future.length > 15 ? `<div class="lista-fila suave">… ${st.future.length - 15} ${T('más')}</div>` : ''}</div>
        <p class="suave"><span>${T('«Cancelar y avisar a todos» cancela todas, devuelve lo pagado completo')}</span>${st.refund_total > 0 ? ` (<span class="num">${dinero(st.refund_total)}</span>)` : ''} <span>${T('y avisa a cada buceador por email y en la app, en su idioma.')}</span></p>
        <button class="wbtn peligro ancho grande" type="button" id="cc-todo">${ic('avisos', '')}${T('Cancelar y avisar a todos')}</button>`
        : `<div class="campo"><label for="cc-pw">${T('Escribe tu contraseña para confirmar')}</label><input id="cc-pw" type="password" autocomplete="current-password"></div>
        <button class="wbtn peligro ancho grande" type="button" id="cc-ok">${ic('papelera', '')}${T('Cerrar mi cuenta')}</button>`}
      <a class="wbtn sec ancho" href="#/mas">${T('No, volver')}</a>`;
    W.translateTree(box);
    $('#cc-todo', box)?.addEventListener('click', (e) => {
      const capa = abrirHoja({ titulo: T('¿Cancelar todas las reservas?'), html: `<p>${T('Se cancelan')} <b class="num">${st.future_count}</b> ${T('reservas y se devuelve todo lo pagado. No se puede deshacer.')}</p>`,
        pie: `<button class="wbtn peligro ancho grande" type="button" id="cc-si">${T('Sí, cancelar y avisar')}</button><button class="wbtn sec ancho" type="button" data-cerrar>${T('No, volver')}</button>` });
      $('#cc-si', capa).onclick = async (ev) => {
        ev.currentTarget.disabled = true;
        try { const r = await postJSON('/api/provider/cuenta/cancelar-todo', { confirm: true }); cerrarHoja(); W.toast(`${r.result.cancelled} ${T('reservas canceladas. Hemos avisado a todos.')}`); cerrarCuenta(); }
        catch (err) { ev.currentTarget.disabled = false; W.toast(err.message); }
      };
    });
    $('#cc-ok', box)?.addEventListener('click', async (e) => {
      e.currentTarget.disabled = true;
      try { const r = await postJSON('/api/provider/cuenta/cerrar', { password: $('#cc-pw', box).value }); state.me = null; await W.loadMe(); W.toast(`${T('Tu cuenta se ha cerrado. Puedes reabrirla hasta el')} ${corto(r.purge_after)}.`); location.hash = '#/'; }
      catch (err) { e.currentTarget.disabled = false; W.toast(err.message); }
    });
  }

  /* ---------------------------------------------------------------- push and local reminders (Tanda 4) */
  // Push needs the Firebase account of WORLDIVES (pendiente). Until then the app reminds the staff with local
  // notifications of today's first departure; nothing leaves the phone.
  async function recordatorioLocal() {
    const L = plugin('LocalNotifications'); if (!L || !A.pref('recordar', 'si', ['si', 'no']).startsWith('s')) return;
    try {
      const h = guardado.leer('hoy:' + (state.me?.user?.center_id || state.me?.user?.id))?.v; if (!h) return;
      const prox = (h.slots || []).filter((s) => s.status !== 'cancelled' && s.time).map((s) => ({ s, at: new Date(`${h.date}T${s.time}:00`).getTime() - 45 * 60e3 })).filter((x) => x.at > Date.now()).sort((a, b) => a.at - b.at)[0];
      if (!prox) return;
      const perm = await L.checkPermissions(); if (perm.display !== 'granted' && (await L.requestPermissions()).display !== 'granted') return;
      await L.cancel({ notifications: [{ id: 4901 }] }).catch(() => {});
      await L.schedule({ notifications: [{ id: 4901, title: T('Salida en 45 minutos'), body: `${prox.s.time} · ${prox.s.service} · ${prox.s.confirmed + prox.s.pending_payment} ${T('buceadores')}`, schedule: { at: new Date(prox.at) }, extra: { ruta: '#/salida?id=' + prox.s.slot_id },
        isExactNotification: false }] });   // v50.55: an exact alarm opens Android's «Alarms & reminders» settings in the middle of «Hoy»
    } catch { /* without notifications */ }
  }
  plugin('LocalNotifications')?.addListener?.('localNotificationActionPerformed', (e) => { const r = e?.notification?.extra?.ruta; if (r) location.hash = r; });

  /* ---------------------------------------------------------------- routes */
  Object.assign(A.rutasPro, {
    home: async (p) => { await hoy(p); recordatorioLocal(); },
    agenda, escanear, solicitudes, salida, reservas: reservasPro, 'nueva-reserva': nuevaReserva, mas, 'mi-area': mas, estadisticas, 'cobros-app': cobros,
    'cerrar-cuenta': cerrarCuenta, 'resumen-barco': resumenBarco, contar,
  });
  enviarCola();
})();
