/* Screens: Freelance · WORLDIVES PRO. Sample data only (Tito Guía Pruebas, Tulum, as in the test environment). */
(function () {
  'use strict';
  const { C, ic, esc, dia, fCorta, fLarga, eur } = P;
  const G = 'Freelance PRO';
  const webAg = ['Motor de reservas por días y medio día, horario habitual, bloqueos y zona horaria (v50.44); iCal.'];

  const cab = () => `<header class="cab bati"><div class="cab-fila"><div class="avatar"><img src="img/tito.webp" alt=""></div><div class="crece"><button class="selector-perfil" data-hoja="selector"><img src="img/tito.webp" alt=""><span>Tito Guía Pruebas · Freelance</span>${ic('chevabajo', '')}</button></div></div>
    <h1 style="font-size:var(--t-l)">Hoy, ${fLarga(dia(0))}</h1><p class="suave peq">Hora de Tulum (UTC−5) · 8:14</p></header>`;
  const trabajo = (h, cliente, serv, punto, pers, pago) => `<article class="tarjeta pad pila-8"><div class="fila-entre"><span class="num" style="font-size:var(--t-l);font-weight:700">${h}</span>${pago}</div>
    <b>${esc(serv)}</b><p class="peq">${esc(cliente)} · ${pers} ${pers === 1 ? 'persona' : 'personas'}</p><p class="suave peq">${ic('pin', '')} ${esc(punto)}</p>
    <div class="acciones tres">${C.accion('tel', 'Llamar')}${C.accion('wa', 'WhatsApp', 'data-hoja="wafree"', 'wa')}${C.accion('ruta', 'Cómo llegar')}</div></article>`;
  P.hojas.wafree = () => ({ titulo: 'WhatsApp a Ana Ruiz', sub: 'Mensaje ya escrito en su idioma (español). Puedes cambiarlo.',
    html: '<div class="chat-fondo"><div class="burbuja" contenteditable="true">Hola Ana, soy Tito, tu guía de cenotes. Te espero mañana a las 8:00 en la puerta de tu hotel en Tulum. ¡Hasta mañana! </div></div>',
    pie: `<button class="btn wa ancho grande" data-accion="abrirwa">${ic('wa', '')}Abrir WhatsApp</button>` });

  P.reg('f-hoy', { grupo: G, titulo: 'Hoy', ref: '§6.1', mod: 'freelance', tab: 'f-hoy',
    notas: ['Trabajos de hoy y mañana con cliente, servicio, punto de encuentro, personas y pago.', 'Llamar · WhatsApp · Cómo llegar en cada trabajo.', 'Solicitudes pendientes y lo cobrado.'], web: ['Panel del freelance: reservas, solicitudes y cobros.'],
    html: () => cab() + `<div class="cuerpo"><div class="cifras"><button class="tarjeta cifra alerta" data-go="f-solicitudes" style="text-align:left;cursor:pointer"><b>1</b><span>solicitud por responder</span></button><div class="tarjeta cifra"><b>${eur(540)}</b><span>cobrado esta semana</span></div></div>
      <h2>Hoy</h2>${trabajo('11:00', 'Familia Ortega', 'Sesión de fotos y vídeo bajo el agua', 'Cenote Dos Ojos, entrada principal', 2, C.tag('ok', 'Pagado'))}
      <h2>Mañana</h2>${trabajo('08:00', 'Ana Ruiz', 'Cenotes con guía · día 1 de 3', 'Hotel en Tulum, puerta principal', 2, C.tag('pend', 'Señal pagada · resto en el sitio'))}</div>` });

  /* ---------- agenda ---------- */
  const segF = (act) => `<div class="seg">${[['Mes', 'f-agenda-mes'], ['Semana', 'f-agenda-semana'], ['Día', 'f-agenda-dia']].map(([t, id]) => `<button aria-pressed="${t === act}" data-go="${id}">${t}</button>`).join('')}</div>`;
  const mesF = () => {
    const ocup = { 14: 4, 15: 4, 16: 4, 21: 4, 22: 4, 23: 4, 31: 4 }, medio = [17, 28], bloq = [25, 26, 27];
    let h = ['L', 'M', 'X', 'J', 'V', 'S', 'D'].map((d) => `<div class="dsem">${d}</div>`).join('') + '<div></div><div></div><div></div>';
    for (let d = 1; d <= 31; d++) {
      const dom = new Date(2026, 9, d).getDay() === 0;
      const cls = bloq.includes(d) ? ' bloqueado' : medio.includes(d) ? ' medio' : '';
      h += `<button class="dia${d === 13 ? ' hoy' : ''}${cls}${d < 13 ? ' fuera' : ''}" ${cls ? '' : `data-p="${ocup[d] || 0}"`} data-hoja="bloquear" data-arg="${d}" aria-label="${d} de octubre${bloq.includes(d) ? ', bloqueado' : medio.includes(d) ? ', medio día ocupado' : ocup[d] ? ', ocupado' : dom ? ', cerrado (horario habitual)' : ', libre'}" ${dom && !cls && !ocup[d] ? 'style="color:var(--suave)"' : ''}>${d}</button>`;
    }
    return `<div class="mes">${h}</div>`;
  };
  P.reg('f-agenda-mes', { grupo: G, titulo: 'Agenda · mes', ref: '§6.2', mod: 'freelance', tab: 'f-agenda',
    notas: ['Días libres en blanco, ocupados en color y medio día partido en dos.', 'Bloquear días con un toque (vacaciones, trabajos fuera de WORLDIVES), sin motivo.', 'Horario habitual, temporadas cerradas e iCal.'], web: webAg,
    html: () => `<div class="cuerpo"><div class="fila-entre"><h1>Agenda</h1><button class="btn sec" style="min-height:44px">Hoy</button></div>${segF('Mes')}<h2>Octubre 2026</h2>${mesF()}
      <div class="leyenda"><span><i></i>Libre</span><span><i style="background:var(--p4);border-color:var(--p4)"></i>Ocupado</span><span><i style="background:linear-gradient(135deg,var(--p3) 50%,var(--sup) 50%)"></i>Medio día</span><span><i style="background:repeating-linear-gradient(135deg,var(--sup2) 0 3px,var(--sup) 3px 6px)"></i>Bloqueado</span></div>
      <div class="tarjeta plana lista">${C.fila('reloj', 'Horario habitual', 'Lunes a sábado · domingos cerrado')}${C.fila('bloquear', 'Temporadas cerradas', 'Ninguna')}${C.fila('agenda', 'Calendario iCal', 'Exportar a tu móvil · importar Google Calendar')}</div></div>` });
  P.hojas.bloquear = (d) => ({ titulo: `Bloquear el ${fLarga(dia((+d || 24) - 13))}`, sub: 'Sin motivo. Nadie podrá reservarte ese día.',
    html: `<div class="seg"><button aria-pressed="true">Día completo</button><button aria-pressed="false">Mañana</button><button aria-pressed="false">Tarde</button></div><div class="campo"><label for="hasta">Hasta (opcional)</label><input id="hasta" value="${fCorta(dia((+d || 24) - 13 + 2))}"></div>`,
    pie: `<button class="btn ancho grande" data-accion="bloqueado">${ic('bloquear', '')}Bloquear</button>` });
  P.acc.bloqueado = () => { P.cerrarHoja(); P.toast('Días bloqueados', { deshacer: () => P.toast('Deshecho'), segundos: 10 }); };
  P.reg('f-bloquear', { grupo: G, titulo: 'Bloquear días', ref: '§6.2', mod: 'freelance', tab: 'f-agenda', notas: ['Un toque en el día abre esta hoja; día completo o medio día.'], web: webAg,
    html: () => P.screens['f-agenda-mes'].html(), hoja: 'bloquear', hojaArg: '24' });
  P.reg('f-agenda-semana', { grupo: G, titulo: 'Agenda · semana', ref: '§6.2', mod: 'freelance', tab: 'f-agenda', notas: ['Una fila por día: trabajo de día completo, medio día o libre.'], web: webAg,
    html: () => `<div class="cuerpo"><h1>Agenda</h1>${segF('Semana')}<div class="tarjeta plana lista">${[[0, 'Sesión de fotos · 11:00', 'ok'], [1, 'Cenotes · Ana Ruiz · día 1', 'ok'], [2, 'Cenotes · Ana Ruiz · día 2', 'ok'], [3, 'Cenotes · Ana Ruiz · día 3', 'ok'], [4, 'Mañana libre · tarde: cenote con Leo', 'medio'], [5, 'Libre', ''], [6, 'Domingo · cerrado', 'cerr']].map(([n, t, k]) =>
      `<div class="semana-dia"><div class="nd">${dia(n).getDate()}<small>${fCorta(dia(n)).slice(0, 3)}</small></div><span class="${k === 'ok' ? '' : 'suave'}" style="font-weight:${k === 'ok' ? 600 : 400}">${t}</span>${k === 'ok' ? C.tag('neutro', 'Ocupado') : k === 'medio' ? C.tag('neutro', 'Medio día') : ''}</div>`).join('')}</div></div>` });
  P.reg('f-agenda-dia', { grupo: G, titulo: 'Agenda · día', ref: '§6.2', mod: 'freelance', tab: 'f-agenda', notas: ['Línea de tiempo del día con mañana y tarde.'], web: webAg,
    html: () => `<div class="cuerpo"><h1>Agenda</h1>${segF('Día')}<h2>Hoy, ${fCorta(dia(0))}</h2><div class="linea-tiempo"><div>${['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00'].map((h) => `<div class="lt-hora">${h}</div>`).join('')}</div>
      <div style="position:relative">${Array.from({ length: 8 }, () => '<div class="lt-hueco"></div>').join('')}<div class="lt-bloque" style="top:194px;height:186px"><b>11:00 Sesión de fotos y vídeo</b>Familia Ortega · Cenote Dos Ojos · 2</div></div></div></div>` });

  /* ---------- requests ---------- */
  const sol = (botones = true) => `<article class="tarjeta solicitud"><div class="fila"><div class="avatar">AR</div><div class="crece pila"><b>Ana Ruiz</b><span class="suave peq">Open Water · 15 inm. · español</span></div>${C.anillo(.35, '15 h', 'quedan', '')}</div>
    <div class="pila"><p style="font-weight:600">Cenotes con guía, por días</p><p class="num peq">${fCorta(dia(8))} → ${fCorta(dia(10))} · 2 personas · ${eur(972)}</p><p class="suave peq">Punto de encuentro: hotel en Tulum</p></div>
    <div class="aviso sol">${ic('info', '')}<span>Si aceptas, se bloquean esos 3 días y se rechaza sola la solicitud de Leo (${fCorta(dia(9))} por la tarde), que se solapa.</span></div>
    ${botones ? `<div class="btn-fila"><button class="btn peligro">${ic('x', '')}Rechazar</button><button class="btn ok" data-go="f-aceptada">${ic('check', '')}Aceptar</button></div><button class="btn texto">Ofrecer otras fechas</button>` : ''}</article>`;
  P.reg('f-solicitudes', { grupo: G, titulo: 'Solicitudes', ref: '§6.3', mod: 'freelance', tab: 'f-solicitudes',
    notas: ['Igual que el centro: Aceptar, Rechazar, Ofrecer otras fechas.', 'Al aceptar se bloquean los días y se rechazan solas las solicitudes que se solapan.'], web: ['Solicitudes que se solapan, según la decisión del 12/10 (docs/agenda/diseno.md §14).'],
    html: () => `<div class="cuerpo"><h1>Solicitudes</h1><div class="seg"><button aria-pressed="true">Solicitudes · 1</button><button aria-pressed="false">Pendientes de pago · 0</button></div>${sol()}</div>` });
  P.reg('f-aceptada', { grupo: G, titulo: 'Solicitud aceptada', ref: '§6.3', mod: 'freelance', tab: 'f-solicitudes', notas: ['Confirma lo que ha pasado: días bloqueados y la solicitud que se ha rechazado sola.', 'WhatsApp para saludar al cliente.'],
    html: () => `<div class="cuerpo"><div class="check-grande">${ic('check', '')}</div><h1 class="centrado">Aceptada</h1><div class="tarjeta pad pila-8"><b>Ana Ruiz · Cenotes por días</b><p class="num peq">${fCorta(dia(8))} → ${fCorta(dia(10))} · 2 personas</p></div>
      <div class="aviso ok">${ic('agenda', '')}<span><b>Bloqueados</b> ${fCorta(dia(8))}, ${fCorta(dia(9))} y ${fCorta(dia(10))}.</span></div><div class="aviso neutro">${ic('sobre', '')}<span><b>Rechazada sola:</b> Leo Martín (${fCorta(dia(9))} por la tarde). Se le ha avisado con otras fechas libres.</span></div>
      <button class="btn wa ancho grande" data-hoja="wafree">${ic('wa', '')}Saludar a Ana por WhatsApp</button><button class="btn sec ancho" data-go="f-hoy">Volver a Hoy</button></div>` });
  P.reg('f-push', { grupo: G, titulo: 'Aviso push en la pantalla bloqueada', ref: '§6.6', mod: 'freelance', sinTabs: true, sinScroll: true,
    notas: ['Ejemplo de la promesa: le entra una solicitud, la abre desde el aviso, ve fechas y cliente, Aceptar y WhatsApp. Todo en < 30 s.'], falta: ['Push: no existe en la web. Se programa en la Tanda 4 (Firebase en Android, APNs en iOS).'],
    html: () => `<div class="bloqueo"><p class="fecha">${fLarga(dia(0))}</p><p class="reloj num">8:14</p><p class="fecha">&nbsp;</p>
      <button class="notif" data-go="f-solicitud"><img src="img/simbolo.png" alt=""><span><b>WORLDIVES Pro · ahora</b><br>Nueva solicitud de Ana Ruiz: cenotes 3 días, 2 personas, ${eur(972)}.<br><small>Toca para responder · caduca en 15 h</small></span></button></div>` });
  P.reg('f-solicitud', { grupo: G, titulo: 'Solicitud abierta desde el aviso', ref: '§6.6', mod: 'freelance', tab: 'f-solicitudes', notas: ['Se abre directamente la solicitud, sin pasar por Hoy.'],
    html: () => `<div class="cuerpo">${C.volver('f-solicitudes', 'Solicitudes')}${sol()}</div>` });
  P.reg('f-escanear', { grupo: G, titulo: 'Escanear', ref: '§6.4', mod: 'freelance', tab: 'f-escanear', notas: ['Check-in de sus clientes y canje de sus promociones (el mismo escáner que el centro).'],
    html: () => P.screens['c-escanear'].html() });

  /* ---------- more ---------- */
  P.reg('f-mas', { grupo: G, titulo: 'Más', ref: '§6.5', mod: 'freelance', tab: 'f-mas', notas: ['Todo lo que gestiona en la web: servicios, experiencias, escaparate, cobros, reseñas, exportar, WhatsApp Business, apariencia y ajustes.'],
    web: ['Panel del freelance (#/area).'],
    html: () => `<header class="cab bati"><div class="fila"><div class="avatar" style="width:56px;height:56px"><img src="img/tito.webp" alt=""></div><div class="crece"><h1 style="font-size:var(--t-l)">Tito Guía Pruebas</h1><div class="tags">${C.tag('ok', 'Cobros online activos')}${C.tag('ok', 'Verificado')}</div></div></div></header>
      <div class="cuerpo"><div class="tarjeta plana lista">${[['euro', 'Mis servicios', '3 · por días, medio día y sesión', 'f-servicios'], ['experiencia', 'Mis experiencias', '1 publicada', 'f-experiencias'], ['tienda', 'Mi escaparate', 'worldives…/o/tito-guia', 'f-escaparate'], ['cobrar', 'Cobros', '540 € esta semana', 'f-cobros'],
        ['resena', 'Reseñas por responder', '1'], ['descargar', 'Exportar datos', ''], ['wa', 'WhatsApp Business', 'Sin conectar · usas tu WhatsApp'], ['tema', 'Apariencia', 'Clásico', 'ajustes'], ['ajustes', 'Ajustes', ''], ['persona', 'Cambiar de perfil', '', 'c-selector']].map(([i, t, s2, d]) => C.fila(i === 'experiencia' ? 'explorar' : i, t, esc(s2), d ? `data-go="${d}"` : '')).join('')}</div></div>` });
  P.reg('f-servicios', { grupo: G, titulo: 'Mis servicios', ref: '§6.5', mod: 'freelance', tab: 'f-mas',
    notas: ['Crear y editar, incluidos «Por días» y medio día, tarifas por tramos, extras, modo de reserva y señal.'], web: ['Servicios del freelance (/api/provider-services) con unidad día/medio día y descuentos (v50.44).'],
    html: () => `<div class="cuerpo">${C.volver('f-mas', 'Más')}<div class="fila-entre"><h1>Mis servicios</h1><button class="btn" style="min-height:44px">${ic('mas1', '')}Nuevo</button></div>
      ${[['Cenotes con guía, por días', '180 € por día · −10 % desde 3 días · 1–10 días · hasta 4 personas', 'Bajo petición · señal 30 %'], ['Cenote por la mañana o por la tarde', '110 € medio día · 200 € día completo', 'Bajo petición'], ['Sesión de fotos y vídeo bajo el agua', '90 € · 3 h · 2 personas', 'Bajo petición']].map(([t, s2, m]) =>
        `<article class="tarjeta pad pila-8"><div class="fila-entre"><b>${t}</b><button class="btn texto" style="min-height:40px">${ic('lapiz', '')}Editar</button></div><p class="suave peq">${s2}</p><div class="tags"><span class="tag neutro">${ic('sobre', '')}${m}</span>${C.tag('ok', 'Publicado')}</div></article>`).join('')}</div>` });
  P.reg('f-experiencias', { grupo: G, titulo: 'Mis experiencias', ref: '§6.5', mod: 'freelance', tab: 'f-mas', notas: ['Crear con imagen propia, plazas y estado de verificación.'], web: ['Experiencias y su revisión (bloque B).'],
    html: () => `<div class="cuerpo">${C.volver('f-mas', 'Más')}<h1>Mis experiencias</h1><article class="tarjeta" style="overflow:hidden"><img src="img/cenote.webp" alt="" style="height:140px;width:100%;object-fit:cover"><div class="pad pila-8" style="padding:14px"><b>Vida a bordo en el Caribe mexicano</b>
      <p class="num peq">${fCorta(dia(45))} → ${fCorta(dia(51))} · 12 plazas · ${eur(1450)}</p><p class="suave peq">6 noches, 15 inmersiones, pensión completa</p><div class="tags">${C.tag('ok', 'Publicada')}</div></div></article>
      <button class="btn sec ancho">${ic('mas1', '')}Nueva experiencia</button></div>` });
  P.reg('f-escaparate', { grupo: G, titulo: 'Mi escaparate', ref: '§6.5', mod: 'freelance', tab: 'f-mas', notas: ['Foto, presentación, idiomas, zonas, titulaciones, enlace /o/<nombre> y su QR para Instagram.'], web: ['Escaparate público del freelance.'],
    html: () => `<div class="cuerpo">${C.volver('f-mas', 'Más')}<h1>Mi escaparate</h1><div class="fila tarjeta pad"><div class="avatar" style="width:72px;height:72px"><img src="img/tito.webp" alt=""></div><div class="crece pila"><b>Tito Guía Pruebas</b><span class="suave peq">Instructor y guía de cenotes</span><button class="btn texto" style="justify-self:start;padding-left:0">Cambiar foto</button></div></div>
      <div class="campo"><label for="pres">Presentación</label><textarea id="pres">Guía e instructor en los cenotes de la Riviera Maya desde 2012.</textarea></div>
      <section class="pila-8"><p class="eti">Idiomas y zonas</p><div class="tags"><span class="tag neutro">Español</span><span class="tag neutro">English</span><span class="tag neutro">Riviera Maya</span><span class="tag neutro">Tulum</span></div></section>
      <section class="tarjeta pad pila-12"><div class="fila">${C.qr('https://worldives.example/o/tito-guia', 88)}<div class="crece pila"><b style="overflow-wrap:anywhere">worldives…/o/tito-guia</b><span class="suave peq">Para tu biografía de Instagram</span></div></div><div class="btn-fila"><button class="btn sec">${ic('copiar', '')}Copiar</button><button class="btn sec">${ic('compartir', '')}Compartir</button></div></section></div>` });
  P.reg('f-cobros', { grupo: G, titulo: 'Cobros', ref: '§6.5', mod: 'freelance', tab: 'f-mas', notas: ['Estado de Stripe, cobros y devoluciones.'], web: ['Cobro directo por Stripe sin comisión (Fase 2).'],
    html: () => `<div class="cuerpo">${C.volver('f-mas', 'Más')}<h1>Cobros</h1><div class="aviso ok">${ic('check', '')}<span><b>Stripe conectado.</b> Cobras directamente en tu cuenta, sin comisión de WORLDIVES.</span></div>
      <div class="cifras"><div class="tarjeta cifra"><b>${eur(540)}</b><span>esta semana</span></div><div class="tarjeta cifra"><b>${eur(324)}</b><span>señales por cobrar</span></div></div>
      <div class="tarjeta plana lista">${[['Familia Ortega', 'Sesión de fotos', '180 €', 'ok', 'Cobrado'], ['Ana Ruiz', 'Cenotes · señal', '324 €', 'pend', 'Por cobrar'], ['Leo Martín', 'Medio día', '110 €', 'ok', 'Cobrado']].map(([n, s2, imp, k, t]) =>
        `<div class="lista-fila"><span class="crece pila"><b>${n}</b><span class="suave peq">${s2}</span></span><span class="pila" style="justify-items:end"><b class="num">${imp}</b>${C.tag(k, t)}</span></div>`).join('')}</div></div>` });
})();
