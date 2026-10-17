/* WORLDIVES app · prototipo navegable (Tanda 0). Core: navigation, sheets, toasts, icons, sample data and the map.
   Screens live in pantallas-*.js and register themselves with P.reg(). Everything here is sample data. */
(function () {
  'use strict';

  /* ---------------- icons: stroke SVG, 24 px grid ---------------- */
  const I = {
    inicio: '<path d="M3 10.5 12 3l9 7.5"/><path d="M5 9.5V21h5v-6h4v6h5V9.5"/>',
    explorar: '<path d="M9 4 3 6.5v13.5L9 17.5l6 2.5 6-2.5V4l-6 2.5z"/><path d="M9 4v13.5M15 6.5V20"/>',
    reservas: '<path d="M3 8a2 2 0 0 0 2-2h14a2 2 0 0 0 2 2v2a2 2 0 0 0 0 4v2a2 2 0 0 0-2 2H5a2 2 0 0 0-2-2v-2a2 2 0 0 0 0-4z"/><path d="M13 6v2M13 11v2M13 16v2"/>',
    buddies: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0"/><circle cx="17" cy="9" r="2.8"/><path d="M16.5 14.2a5 5 0 0 1 5 5"/>',
    area: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    hoy: '<circle cx="12" cy="12" r="4"/><path d="M12 2v2.5M12 19.5V22M2 12h2.5M19.5 12H22M4.9 4.9l1.8 1.8M17.3 17.3l1.8 1.8M4.9 19.1l1.8-1.8M17.3 6.7l1.8-1.8"/>',
    agenda: '<rect x="3" y="5" width="18" height="16" rx="2.5"/><path d="M3 10h18M8 3v4M16 3v4"/>',
    escanear: '<path d="M4 8V5a1 1 0 0 1 1-1h3M16 4h3a1 1 0 0 1 1 1v3M20 16v3a1 1 0 0 1-1 1h-3M8 20H5a1 1 0 0 1-1-1v-3"/><path d="M7 12h10"/>',
    solicitudes: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    mas: '<circle cx="5" cy="12" r="1.6"/><circle cx="12" cy="12" r="1.6"/><circle cx="19" cy="12" r="1.6"/>',
    entrar: '<path d="M14 4h4a2 2 0 0 1 2 2v12a2 2 0 0 1-2 2h-4"/><path d="M10 16l4-4-4-4M14 12H4"/>',
    buscar: '<circle cx="11" cy="11" r="7"/><path d="m20 20-3.5-3.5"/>',
    filtros: '<path d="M4 6h10M18 6h2M4 12h4M12 12h8M4 18h12M20 18h0"/><circle cx="16" cy="6" r="2"/><circle cx="10" cy="12" r="2"/><circle cx="18" cy="18" r="2"/>',
    ubicacion: '<circle cx="12" cy="12" r="7"/><circle cx="12" cy="12" r="2.5"/><path d="M12 2v3M12 19v3M2 12h3M19 12h3"/>',
    capas: '<path d="m12 3 9 5-9 5-9-5z"/><path d="m3 13 9 5 9-5"/>',
    lista: '<path d="M8 6h13M8 12h13M8 18h13"/><circle cx="4" cy="6" r="1"/><circle cx="4" cy="12" r="1"/><circle cx="4" cy="18" r="1"/>',
    mapa: '<path d="M9 4 3 6.5v13.5L9 17.5l6 2.5 6-2.5V4l-6 2.5z"/><path d="M9 4v13.5M15 6.5V20"/>',
    reloj: '<circle cx="12" cy="12" r="9"/><path d="M12 7v5l3 2"/>',
    pin: '<path d="M12 21s-7-6.2-7-11.5A7 7 0 0 1 19 9.5C19 14.8 12 21 12 21z"/><circle cx="12" cy="9.5" r="2.5"/>',
    ola: '<path d="M2 9c2 0 2-2 4-2s2 2 4 2 2-2 4-2 2 2 4 2 2-2 4-2"/><path d="M2 15c2 0 2-2 4-2s2 2 4 2 2-2 4-2 2 2 4 2 2-2 4-2"/>',
    viento: '<path d="M3 8h11a3 3 0 1 0-3-3"/><path d="M3 12h16a3 3 0 1 1-3 3"/><path d="M3 16h7"/>',
    termo: '<path d="M14 14.8V5a2 2 0 0 0-4 0v9.8a4 4 0 1 0 4 0z"/><path d="M12 10v6"/>',
    check: '<path d="m5 12.5 4.5 4.5L19 7.5"/>',
    x: '<path d="M6 6l12 12M18 6 6 18"/>',
    mas1: '<path d="M12 5v14M5 12h14"/>',
    menos: '<path d="M5 12h14"/>',
    chev: '<path d="m9 6 6 6-6 6"/>',
    chevabajo: '<path d="m6 9 6 6 6-6"/>',
    atras: '<path d="m15 6-6 6 6 6"/>',
    tel: '<path d="M5 4h3.5l1.5 4.5-2.2 1.4a11 11 0 0 0 6.3 6.3l1.4-2.2L20 15.5V19a2 2 0 0 1-2 2A16 16 0 0 1 3 6a2 2 0 0 1 2-2z"/>',
    wa: '<path d="M4 20l1.3-4.2A8.5 8.5 0 1 1 8.4 19z"/><path d="M9 9.2c.2 2.6 2.4 4.9 5 5.2l1.2-1.2-1.8-.9-.8.8c-.9-.4-1.7-1.2-2.1-2.1l.8-.8-.9-1.8z"/>',
    ruta: '<path d="M3 11 21 3l-8 18-2-8z"/>',
    compartir: '<circle cx="18" cy="5" r="2.5"/><circle cx="6" cy="12" r="2.5"/><circle cx="18" cy="19" r="2.5"/><path d="m8.2 10.8 7.6-4.6M8.2 13.2l7.6 4.6"/>',
    calmas: '<rect x="3" y="5" width="18" height="16" rx="2.5"/><path d="M3 10h18M8 3v4M16 3v4M12 13v5M9.5 15.5h5"/>',
    recibo: '<path d="M6 3h12v18l-3-2-3 2-3-2-3 2z"/><path d="M9 8h6M9 12h6M9 16h3"/>',
    estrella: '<path d="m12 3 2.7 5.6 6.1.9-4.4 4.3 1 6.1L12 17l-5.4 2.9 1-6.1L3.2 9.5l6.1-.9z"/>',
    alerta: '<path d="M12 3 2 20h20z"/><path d="M12 10v4.5M12 17.5v.01"/>',
    info: '<circle cx="12" cy="12" r="9"/><path d="M12 11v5.5M12 7.5v.01"/>',
    euro: '<path d="M17.5 6.5A7 7 0 1 0 17.5 17.5"/><path d="M4 10.5h9M4 13.5h9"/>',
    barco: '<path d="M3 15h18l-2.5 5h-13z"/><path d="M6 15V9h12v6M12 9V4M9 6h3"/>',
    persona: '<circle cx="12" cy="8" r="4"/><path d="M4 21a8 8 0 0 1 16 0"/>',
    linterna: '<path d="M8 3h8v4l-2 3v11h-4V10L8 7z"/><path d="M8 7h8"/>',
    teclado: '<rect x="2" y="6" width="20" height="13" rx="2"/><path d="M6 10h.01M10 10h.01M14 10h.01M18 10h.01M7 15h10"/>',
    camara: '<path d="M4 8h3l2-3h6l2 3h3a1 1 0 0 1 1 1v10a1 1 0 0 1-1 1H4a1 1 0 0 1-1-1V9a1 1 0 0 1 1-1z"/><circle cx="12" cy="13.5" r="3.5"/>',
    qr: '<rect x="3" y="3" width="7" height="7" rx="1"/><rect x="14" y="3" width="7" height="7" rx="1"/><rect x="3" y="14" width="7" height="7" rx="1"/><path d="M14 14h3v3h-3zM20 14v.01M14 20h.01M17 20h4v-3"/>',
    mover: '<path d="M4 8h14l-3-3M20 16H6l3 3"/>',
    cobrar: '<rect x="2.5" y="5" width="19" height="14" rx="2.5"/><path d="M2.5 10h19M6 15h4"/>',
    ficha: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><circle cx="9" cy="11" r="2.2"/><path d="M5.5 16.5a3.5 3.5 0 0 1 7 0M14.5 10h4M14.5 13.5h3"/>',
    lapiz: '<path d="M4 20h4L19 9l-4-4L4 16z"/><path d="m13.5 6.5 4 4"/>',
    papelera: '<path d="M4 7h16M9 7V4h6v3M6 7l1 14h10l1-14"/>',
    ajustes: '<circle cx="12" cy="12" r="3"/><path d="M19.4 15a1.7 1.7 0 0 0 .3 1.8l.1.1a2 2 0 1 1-2.8 2.8l-.1-.1a1.7 1.7 0 0 0-1.8-.3 1.7 1.7 0 0 0-1 1.5V21a2 2 0 1 1-4 0v-.1a1.7 1.7 0 0 0-1.1-1.5 1.7 1.7 0 0 0-1.8.3l-.1.1a2 2 0 1 1-2.8-2.8l.1-.1a1.7 1.7 0 0 0 .3-1.8 1.7 1.7 0 0 0-1.5-1H3a2 2 0 1 1 0-4h.1a1.7 1.7 0 0 0 1.5-1.1 1.7 1.7 0 0 0-.3-1.8l-.1-.1a2 2 0 1 1 2.8-2.8l.1.1a1.7 1.7 0 0 0 1.8.3H9a1.7 1.7 0 0 0 1-1.5V3a2 2 0 1 1 4 0v.1a1.7 1.7 0 0 0 1 1.5 1.7 1.7 0 0 0 1.8-.3l.1-.1a2 2 0 1 1 2.8 2.8l-.1.1a1.7 1.7 0 0 0-.3 1.8V9a1.7 1.7 0 0 0 1.5 1H21a2 2 0 1 1 0 4h-.1a1.7 1.7 0 0 0-1.5 1z"/>',
    idioma: '<circle cx="12" cy="12" r="9"/><path d="M3 12h18M12 3a14 14 0 0 1 0 18M12 3a14 14 0 0 0 0 18"/>',
    texto: '<path d="M4 7V5h10v2M9 5v14M7 19h4M14 12v-1.5h6V12M17 10.5V19M15.5 19h3"/>',
    tema: '<circle cx="12" cy="12" r="9"/><path d="M12 3v18a9 9 0 0 0 0-18z" fill="currentColor"/>',
    avisos: '<path d="M6 16V11a6 6 0 0 1 12 0v5l1.5 2h-15z"/><path d="M10 20a2 2 0 0 0 4 0"/>',
    salir: '<path d="M10 4H6a2 2 0 0 0-2 2v12a2 2 0 0 0 2 2h4"/><path d="M14 16l4-4-4-4M18 12H9"/>',
    documento: '<path d="M6 3h8l4 4v14H6z"/><path d="M14 3v4h4M9 12h6M9 16h6"/>',
    libro: '<path d="M4 4.5A1.5 1.5 0 0 1 5.5 3H20v15H5.5A1.5 1.5 0 0 0 4 19.5z"/><path d="M4 19.5A1.5 1.5 0 0 0 5.5 21H20v-3"/>',
    regalo: '<rect x="3" y="8" width="18" height="4" rx="1"/><path d="M5 12v9h14v-9M12 8v13M12 8S10.5 3 8 4.5 9.5 8 12 8zM12 8s1.5-5 4-3.5S14.5 8 12 8z"/>',
    puntos: '<circle cx="12" cy="9" r="6"/><path d="m8.5 14-1.5 7 5-2.5 5 2.5-1.5-7"/>',
    web: '<path d="M14 4h6v6M20 4l-9 9"/><path d="M18 14v5a1 1 0 0 1-1 1H5a1 1 0 0 1-1-1V7a1 1 0 0 1 1-1h5"/>',
    descargar: '<path d="M12 4v11M7 10l5 5 5-5M5 20h14"/>',
    graficas: '<path d="M4 20V10M10 20V4M16 20v-7M22 20H2"/>',
    cartel: '<rect x="4" y="3" width="16" height="18" rx="2"/><path d="M8 8h8M8 12h8M8 16h5"/>',
    equipo: '<circle cx="9" cy="8" r="3.5"/><path d="M2.5 20a6.5 6.5 0 0 1 13 0M19 8v6M16 11h6"/>',
    resena: '<path d="M4 5h16v11H9l-5 4z"/><path d="m12 7.5.9 1.9 2 .3-1.4 1.4.3 2-1.8-1-1.8 1 .3-2-1.4-1.4 2-.3z"/>',
    candado: '<rect x="5" y="10" width="14" height="11" rx="2"/><path d="M8 10V7a4 4 0 0 1 8 0v3"/>',
    sincon: '<path d="M2 8.5a15 15 0 0 1 20 0M5.5 12a10 10 0 0 1 13 0M9 15.5a5 5 0 0 1 6 0M12 19v.01M3 3l18 18"/>',
    bug: '<rect x="7" y="8" width="10" height="12" rx="5"/><path d="M12 8v12M9 5l1.5 3M15 5l-1.5 3M3 12h4M17 12h4M4 18l3-2M20 18l-3-2M4 7l3 2M20 7l-3 2"/>',
    tienda: '<path d="M4 9.5 5.5 4h13L20 9.5M4 9.5V20h16V9.5M4 9.5a2.7 2.7 0 0 0 5.3 0 2.7 2.7 0 0 0 5.4 0 2.7 2.7 0 0 0 5.3 0"/><path d="M10 20v-5h4v5"/>',
    bloquear: '<circle cx="12" cy="12" r="9"/><path d="m5.6 5.6 12.8 12.8"/>',
    servidor: '<rect x="3" y="4" width="18" height="7" rx="1.5"/><rect x="3" y="13" width="18" height="7" rx="1.5"/><path d="M7 7.5h.01M7 16.5h.01"/>',
    ola2: '<path d="M2 12c2.5 0 2.5-3 5-3s2.5 3 5 3 2.5-3 5-3 2.5 3 5 3"/>',
    bandera: '<rect x="4" y="4" width="16" height="16" rx="3"/><path d="m5 19 14-14"/>',
    girar: '<rect x="3" y="8" width="18" height="11" rx="2"/><path d="M8 4.5A8 8 0 0 1 18 5l1 1.5M19 3v3.5h-3.5"/>',
    sobre: '<rect x="3" y="5" width="18" height="14" rx="2.5"/><path d="m3.5 7 8.5 6 8.5-6"/>',
    ojo: '<path d="M2 12s3.5-7 10-7 10 7 10 7-3.5 7-10 7S2 12 2 12z"/><circle cx="12" cy="12" r="3"/>',
    tanque: '<rect x="8" y="6" width="8" height="15" rx="4"/><path d="M10 6V3.5h4V6M12 3.5V2"/>',
    copiar: '<rect x="8" y="8" width="12" height="12" rx="2"/><path d="M16 8V5a1 1 0 0 0-1-1H5a1 1 0 0 0-1 1v10a1 1 0 0 0 1 1h3"/>',
  };
  const ic = (n, cls = 'ic') => `<svg class="${cls}" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true">${I[n] || ''}</svg>`;
  const esc = (s) => String(s ?? '').replace(/[&<>"']/g, (c) => ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));

  /* ---------------- fixed «today» so every capture is the same ---------------- */
  const HOY = new Date(2026, 9, 13, 9, 14);
  const DSEM = ['domingo', 'lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado'];
  const MES = ['enero', 'febrero', 'marzo', 'abril', 'mayo', 'junio', 'julio', 'agosto', 'septiembre', 'octubre', 'noviembre', 'diciembre'];
  const dia = (n) => { const d = new Date(HOY); d.setDate(d.getDate() + n); return d; };
  const fCorta = (d) => `${DSEM[d.getDay()].slice(0, 3)} ${d.getDate()} ${MES[d.getMonth()].slice(0, 3)}`;
  const fLarga = (d) => `${DSEM[d.getDay()]} ${d.getDate()} de ${MES[d.getMonth()]}`;
  const eur = (n) => `${String(n).replace('.', ',')} €`;

  /* ---------------- sample data (names follow the test environment) ---------------- */
  const D = {
    centro: { nombre: 'Centro de Buceo Pruebas', corto: 'Buceo Pruebas', ciudad: 'Xàbia', tel: '+34 600 000 101', barco: 'Neptuno', plazasBarco: 12,
      lema: 'Buceo en la reserva marina del Cabo de San Antonio', logo: 'img/logo-centro.webp', portada: 'img/arrecife.webp', valoracion: 4.8, resenas: 126 },
    mar: { agua: '19 °C', viento: '12 km/h NE', ola: '0,4 m', fuente: 'Puertos del Estado', hora: '9:00' },
    puntos: [
      { id: 'p1', nombre: 'Isla del Portitxol', tipo: 'Arrecife', prof: '6–18 m', nivel: 'Open Water', foto: 'img/arrecife.webp', x: 620, y: 430 },
      { id: 'p2', nombre: 'Cabo de San Antonio', tipo: 'Pared', prof: '10–30 m', nivel: 'Advanced', foto: 'img/pared.webp', x: 600, y: 250 },
      { id: 'p3', nombre: 'Cabo Negro', tipo: 'Pared', prof: '12–32 m', nivel: 'Advanced', foto: 'img/arrecife2.webp', x: 640, y: 560 },
      { id: 'p4', nombre: 'Cala Granadella', tipo: 'Arrecife', prof: '3–12 m', nivel: 'Sin titulación', foto: 'img/buceadores.webp', x: 585, y: 760 },
      { id: 'p5', nombre: 'Cap Prim', tipo: 'Pared', prof: '15–38 m', nivel: 'Advanced', foto: 'img/pared.webp', x: 660, y: 660 },
      { id: 'p6', nombre: 'Pecio del Cabo', tipo: 'Pecio', prof: '22–28 m', nivel: 'Advanced', foto: 'img/nocturna.webp', x: 720, y: 330 },
    ],
    centros: [
      { id: 'c1', nombre: 'Centro de Buceo Pruebas', x: 520, y: 470 },
      { id: 'c2', nombre: 'Centro de Buceo Pruebas Dos', x: 470, y: 640 },
    ],
    salidas: [
      { id: 's1', hora: '08:30', titulo: 'Doble inmersión en barco', punto: 'Cabo de San Antonio', modo: 'solicitud', precio: 75, total: 10, ocup: 6, pend: 2, foto: 'img/pared.webp', instr: 'Iván', barco: 'Neptuno', dia: 0 },
      { id: 's2', hora: '09:00', titulo: 'Inmersión simple en barco', punto: 'Isla del Portitxol', modo: 'pago', precio: 45, total: 10, ocup: 7, pend: 1, foto: 'img/arrecife.webp', instr: 'Iván', barco: 'Neptuno', dia: 0 },
      { id: 's3', hora: '16:00', titulo: 'Bautizo de buceo', punto: 'Cala Granadella', modo: 'pago', precio: 60, total: 6, ocup: 3, pend: 0, foto: 'img/buceadores.webp', instr: 'Ana', barco: 'Desde la costa', dia: 0 },
    ],
    buceadores: [
      { n: 'Bea Buzo', c: 'BB', nivel: 'Advanced OW', inm: 64, tallas: 'M · 42 · M', eq: 'Equipo completo', nitrox: true, pago: 'ok', check: true, busca: false, idioma: 'es', tel: '+34 600 000 102' },
      { n: 'Tom Harris', c: 'TH', nivel: 'Open Water', inm: 18, tallas: 'L · 44 · L', eq: 'Traje y aletas', nitrox: false, pago: 'pend', check: false, busca: true, idioma: 'en', tel: '+44 7700 900123' },
      { n: 'Lucía Pérez', c: 'LP', nivel: 'Rescue', inm: 140, tallas: 'S · 38 · S', eq: 'Propio', nitrox: true, pago: 'ok', check: true, busca: false, idioma: 'es', tel: '+34 600 000 103' },
      { n: 'Pierre Dubois', c: 'PD', nivel: 'Niveau 2', inm: 55, tallas: 'L · 43 · L', eq: 'Propio', nitrox: false, pago: 'centro', check: false, busca: false, idioma: 'fr', tel: '+33 6 12 34 56 78' },
      { n: 'Sven Andersen', c: 'SA', nivel: 'Advanced OW', inm: 300, tallas: 'XL · 45 · XL', eq: 'Propio', nitrox: true, pago: 'ok', check: false, busca: false, idioma: 'de', tel: '+49 151 2345678' },
      { n: 'Ana Martín', c: 'AM', nivel: 'Open Water', inm: 9, tallas: 'M · 40 · M', eq: 'Equipo completo', nitrox: false, pago: 'ok', check: false, busca: true, idioma: 'es', tel: '+34 600 000 104' },
      { n: 'Giulia Ferri', c: 'GF', nivel: 'Open Water', inm: 22, tallas: 'S · 37 · S', eq: 'Traje', nitrox: false, pago: 'pend', check: false, busca: false, idioma: 'it', tel: '+39 312 345 6789' },
    ],
    solicitudes: [
      { id: 'r1', quien: 'Erik Lindqvist', c: 'EL', nivel: 'Advanced OW · 85 inm.', act: 'Doble inmersión en barco', cuando: fCorta(dia(2)) + ' · 08:30', pers: 2, eq: 'Alquila: 2 trajes L, aletas 44', resta: 2.4, total: 24, importe: 150 },
      { id: 'r2', quien: 'Paula Gómez', c: 'PG', nivel: 'Open Water · 12 inm.', act: 'Doble inmersión en barco', cuando: fCorta(dia(2)) + ' · 08:30', pers: 1, eq: 'Equipo propio', resta: 9, total: 24, importe: 75 },
      { id: 'r3', quien: 'Marco Rossi', c: 'MR', nivel: 'Sin titulación', act: 'Curso Open Water (3 días)', cuando: fCorta(dia(3)) + ' → ' + fCorta(dia(5)), pers: 1, eq: 'Alquila equipo completo', resta: 20, total: 24, importe: 390, curso: true },
    ],
    pendientes: [
      { quien: 'Tom Harris', c: 'TH', act: 'Inmersión simple · hoy 09:00', importe: 45, plazo: 'Paga antes de las 8:30', urg: true, idioma: 'en' },
      { quien: 'Giulia Ferri', c: 'GF', act: 'Inmersión simple · hoy 09:00', importe: 45, plazo: 'Paga antes de las 8:30', urg: true, idioma: 'it' },
      { quien: 'Nora Weber', c: 'NW', act: 'Doble inmersión · ' + fCorta(dia(1)), importe: 75, plazo: 'Plazo: mañana a las 7:00', urg: false, idioma: 'de' },
    ],
  };
  const MANANA = { salidas: 3, buceadores: 18, pend: 2 };

  /* ---------------- bathymetry background (generated, very soft) ---------------- */
  function batiImg(color) {
    let p = '';
    for (let k = 0; k < 6; k++) {
      let d = `M -10 ${20 + k * 28}`;
      for (let x = 0; x <= 380; x += 20) d += ` L ${x} ${(20 + k * 28 + Math.sin(x / 47 + k) * 9 + Math.cos(x / 23 + k * 2) * 4).toFixed(1)}`;
      p += `<path d='${d}' fill='none' stroke='${color}' stroke-width='1.2'/>`;
    }
    return `url("data:image/svg+xml,${encodeURIComponent(`<svg xmlns='http://www.w3.org/2000/svg' width='360' height='180'>${p}</svg>`)}")`;
  }

  /* ---------------- tiny components ---------------- */
  const C = {
    ic, esc,
    tag(kind, text) {
      const icn = { ok: 'check', pend: 'reloj', sol: 'sobre', canc: 'x', urg: 'alerta', neutro: '' }[kind];
      return `<span class="tag ${kind}">${icn ? ic(icn, '') : ''}${esc(text)}</span>`;
    },
    asientos(total, ok, pend) {
      let h = '<div class="asientos" role="img" aria-label="' + `${ok} pagadas, ${pend} pendientes de pago, ${total - ok - pend} libres de ${total}` + '">';
      for (let i = 0; i < total; i++) h += `<span class="asiento ${i < ok ? 'ok' : i < ok + pend ? 'pend' : ''}"></span>`;
      return h + '</div>';
    },
    anillo(frac, texto, sub, cls = '') {
      const r = 26, cir = 2 * Math.PI * r, v = Math.max(0, Math.min(1, frac));
      return `<div class="anillo ${cls}" role="img" aria-label="${esc(texto + ' ' + (sub || ''))}"><svg viewBox="0 0 64 64"><circle class="pista" cx="32" cy="32" r="${r}" fill="none" stroke-width="6"/>` +
        `<circle class="valor" cx="32" cy="32" r="${r}" fill="none" stroke-width="6" stroke-dasharray="${(cir * v).toFixed(1)} ${cir.toFixed(1)}"/></svg><b>${esc(texto)}${sub ? `<small>${esc(sub)}</small>` : ''}</b></div>`;
    },
    accion(icon, text, attrs = '', cls = '') { return `<button class="accion ${cls}" ${attrs}>${ic(icon, '')}<span>${esc(text)}</span></button>`; },
    fila(icon, titulo, sub, attrs = '', der = '') {
      return `<button class="lista-fila" ${attrs}>${icon ? ic(icon) : ''}<span class="crece pila"><span style="font-weight:600">${esc(titulo)}</span>${sub ? `<span class="suave peq">${sub}</span>` : ''}</span>${der}${ic('chev', 'chev')}</button>`;
    },
    volver(dest, texto = 'Volver') { return `<button class="btn texto" data-go="${dest}" style="justify-self:start;padding-left:0">${ic('atras', '')}${esc(texto)}</button>`; },
    qr(texto, px = 132) {
      try {
        const q = window.qrcode(0, 'M'); q.addData(texto); q.make();
        const n = q.getModuleCount(), s = px / n; let r = '';
        for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) if (q.isDark(y, x)) r += `<rect x="${(x * s).toFixed(2)}" y="${(y * s).toFixed(2)}" width="${(s + .3).toFixed(2)}" height="${(s + .3).toFixed(2)}"/>`;
        return `<div class="qr"><svg width="${px}" height="${px}" viewBox="0 0 ${px} ${px}" fill="#0A2239" role="img" aria-label="Código QR">${r}</svg></div>`;
      } catch (e) { return `<div class="qr" style="width:${px}px;height:${px}px">QR</div>`; }
    },
    mar() {
      return `<div class="mar-franja" aria-label="Condiciones del mar"><span>${ic('termo', '')}Agua <b>${D.mar.agua}</b></span><span>${ic('viento', '')}Viento <b>${D.mar.viento}</b></span>` +
        `<span>${ic('ola', '')}Ola <b>${D.mar.ola}</b></span><span class="peq">${esc(D.mar.fuente)} · ${D.mar.hora} · ejemplo</span></div>`;
    },
    pendiente(texto) { return `<div class="pendiente"><b>Pendiente de decisión.</b> ${esc(texto)}</div>`; },
  };

  /* ---------------- the prototype object ---------------- */
  const P = window.P = {
    D, C, ic, esc, dia, fCorta, fLarga, eur, HOY, MANANA,
    screens: {}, orden: [], hojas: {}, acc: {},
    s: { pant: 'b-inicio', tema: 'clasico', tam: 'normal', ancho: 390, captura: false, sel: {}, mapa: {} },
    reg(id, def) { this.screens[id] = def; this.orden.push(id); },
    go(id, opts = {}) {
      if (!this.screens[id]) return;
      this.s.pant = id; this.s.sel = opts.sel || {}; this.render();
      try { if (!this.s.captura) history.replaceState(null, '', '#' + id); } catch (e) { /* sandboxed */ }
    },
    tel() { return document.querySelector('.tel'); },
    render() {
      const def = this.screens[this.s.pant]; const tel = this.tel(); if (!def || !tel) return;
      const apaisado = !!def.apaisado;
      const w = apaisado ? 844 : this.s.ancho, h = apaisado ? (this.s.ancho === 360 ? 360 : 390) : (this.s.ancho === 360 ? 800 : 844);
      tel.style.width = w + 'px'; tel.style.height = h + 'px';
      tel.dataset.tema = this.s.tema; tel.dataset.tamano = this.s.tam;
      const tabs = def.sinTabs ? '' : this.tabs(def.mod, def.tab);
      tel.innerHTML = `<div class="tel-estado" aria-hidden="true"><span>9:14</span><svg viewBox="0 0 44 12"><rect x="0" y="6" width="3" height="6" rx="1" fill="currentColor"/><rect x="5" y="4" width="3" height="8" rx="1" fill="currentColor"/><rect x="10" y="2" width="3" height="10" rx="1" fill="currentColor"/><rect x="15" y="0" width="3" height="12" rx="1" fill="currentColor"/><rect x="23" y="1" width="18" height="10" rx="2.5" fill="none" stroke="currentColor"/><rect x="25" y="3" width="11" height="6" rx="1" fill="currentColor"/></svg></div>` +
        (def.pruebas ? '<div class="banda-pruebas">ENTORNO DE PRUEBAS · v0.2</div>' : '') +
        `<main class="tel-pantalla${def.sinScroll ? ' sin-scroll' : ''}" id="pantalla">${def.html(this.s)}</main>${tabs}<div class="capa" id="capa"><div class="velo" data-cerrar></div></div>`;
      tel.style.setProperty('--bati-img', batiImg(getComputedStyle(tel).getPropertyValue('--bati').trim() || 'rgba(7,104,152,.14)'));
      if (def.init) def.init(tel.querySelector('#pantalla'), this.s);
      if (def.hoja) this.abrirHoja(def.hoja, def.hojaArg);
      this.pintarIndice(); this.pintarNotas();
    },
    tabs(mod, actual) {
      const T = {
        visitante: [['v-inicio', 'inicio', 'Inicio'], ['v-explorar', 'explorar', 'Explorar'], ['entrada', 'entrar', 'Entrar']],
        buceador: [['b-inicio', 'inicio', 'Inicio'], ['b-explorar', 'explorar', 'Explorar'], ['b-reservas', 'reservas', 'Reservas', 1], ['b-buddies', 'buddies', 'Buddies'], ['b-mi-area', 'area', 'Mi área']],
        centro: [['c-hoy', 'hoy', 'Hoy'], ['c-agenda-mes', 'agenda', 'Agenda'], ['c-escanear', 'escanear', 'Escanear', 0, true], ['c-solicitudes', 'solicitudes', 'Solicitudes', 3], ['c-mas', 'mas', 'Más']],
        instructor: [['c-instructor', 'hoy', 'Hoy'], ['c-agenda-dia', 'agenda', 'Agenda'], ['c-escanear', 'escanear', 'Escanear', 0, true], ['c-salida', 'barco', 'Mi salida'], ['c-instructor-mas', 'mas', 'Más']],
        freelance: [['f-hoy', 'hoy', 'Hoy'], ['f-agenda-mes', 'agenda', 'Agenda'], ['f-escanear', 'escanear', 'Escanear', 0, true], ['f-solicitudes', 'solicitudes', 'Solicitudes', 1], ['f-mas', 'mas', 'Más']],
      }[mod];
      if (!T) return '';
      return `<nav class="tabs" aria-label="Secciones">${T.map(([id, icn, txt, n, central]) => {
        const cur = actual === id || (actual && id.startsWith(actual));
        return `<button class="tab${central ? ' central' : ''}" data-go="${id}" ${cur ? 'aria-current="page"' : ''}><span class="tab-ic">${ic(icn, '')}</span><span>${txt}</span>${n ? `<span class="cont" aria-label="${n} pendientes">${n}</span>` : ''}</button>`;
      }).join('')}</nav>`;
    },
    /* bottom sheet inside the phone */
    abrirHoja(nombre, arg) {
      const f = this.hojas[nombre]; if (!f) return; const def = f(arg, this.s);
      const capa = this.tel().querySelector('#capa');
      capa.querySelectorAll('.hoja').forEach((h) => h.remove());
      const hoja = document.createElement('section');
      hoja.className = 'hoja'; hoja.setAttribute('role', 'dialog'); hoja.setAttribute('aria-modal', 'true'); hoja.setAttribute('aria-label', def.titulo || 'Hoja');
      if (def.alto) hoja.style.height = def.alto;
      hoja.innerHTML = `<div class="hoja-asa" data-cerrar-asa aria-hidden="true"></div>` +
        (def.titulo ? `<header class="hoja-cab"><div><h2>${esc(def.titulo)}</h2>${def.sub ? `<p class="suave peq">${def.sub}</p>` : ''}</div><button class="hoja-cerrar" data-cerrar aria-label="Cerrar">${ic('x', '')}</button></header>` : '') +
        `<div class="hoja-cuerpo">${def.html}</div>${def.pie ? `<footer class="hoja-pie">${def.pie}</footer>` : ''}`;
      capa.appendChild(hoja);
      requestAnimationFrame(() => capa.classList.add('abierta'));
      if (this.s.captura) capa.classList.add('abierta');
      if (def.init) def.init(hoja, this.s);
    },
    cerrarHoja() { const capa = this.tel()?.querySelector('#capa'); if (capa) { capa.classList.remove('abierta'); setTimeout(() => capa.querySelectorAll('.hoja').forEach((h) => h.remove()), 260); } },
    toast(msg, opts = {}) {
      const tel = this.tel(); tel.querySelectorAll('.toast').forEach((t) => t.remove());
      const t = document.createElement('div'); t.className = 'toast'; t.setAttribute('role', 'status');
      let seg = opts.segundos || 0;
      const pintar = () => { t.innerHTML = `<span class="crece">${esc(msg)}${seg ? ` · ${seg} s` : ''}</span>${opts.deshacer ? '<button data-deshacer>Deshacer</button>' : ''}`; };
      pintar(); tel.appendChild(t);
      const iv = seg ? setInterval(() => { seg--; if (seg <= 0) { clearInterval(iv); t.remove(); opts.alTerminar && opts.alTerminar(); } else pintar(); }, 1000) : setTimeout(() => t.remove(), 3200);
      t.addEventListener('click', (e) => { if (e.target.closest('[data-deshacer]')) { clearInterval(iv); t.remove(); opts.deshacer(); } });
    },
    /* index of screens and notes, outside the phone */
    pintarIndice() {
      const ind = document.getElementById('indice'); if (!ind) return;
      if (!ind.dataset.hecho) {
        const grupos = {}; this.orden.forEach((id) => { const g = this.screens[id].grupo; (grupos[g] = grupos[g] || []).push(id); });
        let n = 0;
        ind.querySelector('[data-lista]').innerHTML = Object.entries(grupos).map(([g, ids]) => `<h2>${esc(g)}</h2><ol>${ids.map((id) => `<li><a href="#${id}" data-ir="${id}"><span>${++n}</span>${esc(this.screens[id].titulo)}</a></li>`).join('')}</ol>`).join('');
        ind.dataset.hecho = '1';
      }
      ind.querySelectorAll('a[data-ir]').forEach((a) => a.setAttribute('aria-current', a.dataset.ir === this.s.pant ? 'true' : 'false'));
      const t = document.getElementById('titulo-movil'); if (t) t.textContent = this.screens[this.s.pant].titulo;
    },
    pintarNotas() {
      const box = document.getElementById('notas-pantalla'); if (!box) return; const d = this.screens[this.s.pant];
      box.innerHTML = `<h2>${esc(d.titulo)}</h2><p class="ref">${esc(d.grupo)} · encargo ${esc(d.ref || '')}</p>` +
        (d.notas?.length ? `<h3>Qué enseña</h3><ul>${d.notas.map((x) => `<li>${x}</li>`).join('')}</ul>` : '') +
        (d.web?.length ? `<h3>Qué usa de la web</h3><ul>${d.web.map((x) => `<li>${x}</li>`).join('')}</ul>` : '') +
        (d.falta?.length ? `<h3>Falta en el servidor</h3><ul>${d.falta.map((x) => `<li><span class="proto-falta">Pendiente</span> ${x}</li>`).join('')}</ul>` : '');
      document.querySelectorAll('[data-ctl]').forEach((b) => { const [k, v] = b.dataset.ctl.split(':'); b.setAttribute('aria-pressed', String(this.s[k]) === v ? 'true' : 'false'); });
    },
    ajustar(k, v) { this.s[k] = k === 'ancho' ? +v : v; try { localStorage.setItem('wd-proto', JSON.stringify({ tema: this.s.tema, tam: this.s.tam, ancho: this.s.ancho })); } catch (e) { /* no storage */ } this.render(); },
  };

  /* ---------------- shared sheets ---------------- */
  P.hojas.whatsapp = (quien) => {
    const b = D.buceadores.find((x) => x.n === quien) || D.pendientes.find((x) => x.quien === quien) || D.buceadores[1];
    const idioma = b.idioma || 'en';
    const nombre = (b.n || b.quien).split(' ')[0];
    const msg = {
      es: `Hola ${nombre}, te escribimos de ${D.centro.nombre} por tu reserva de hoy, martes 13, a las 9:00 en Isla del Portitxol. `,
      en: `Hi ${nombre}, this is ${D.centro.nombre} about your booking today, Tuesday 13, at 9:00 at Isla del Portitxol. `,
      fr: `Bonjour ${nombre}, ici ${D.centro.nombre} au sujet de votre réservation d’aujourd’hui, mardi 13, à 9h00 à Isla del Portitxol. `,
      de: `Hallo ${nombre}, hier ist ${D.centro.nombre} wegen deiner Buchung heute, Dienstag 13., um 9:00 Uhr an der Isla del Portitxol. `,
      it: `Ciao ${nombre}, ti scriviamo da ${D.centro.nombre} per la tua prenotazione di oggi, martedì 13, alle 9:00 a Isla del Portitxol. `,
    }[idioma];
    const nomIdioma = { es: 'español', en: 'inglés', fr: 'francés', de: 'alemán', it: 'italiano' }[idioma];
    return {
      titulo: `WhatsApp a ${b.n || b.quien}`, sub: `Mensaje ya escrito en ${nomIdioma}, el idioma del cliente. Puedes cambiarlo antes de enviarlo.`,
      html: `<div class="chat-fondo"><div class="burbuja" contenteditable="true" spellcheck="false" aria-label="Mensaje">${esc(msg)}</div></div>
        <ul class="suave peq" style="margin:0;padding-left:18px;display:grid;gap:4px"><li>Se abre WhatsApp (o WhatsApp Business) en este móvil, con el número del cliente.</li><li>El número se pide al servidor en el momento; no se guarda en el móvil.</li><li>En el registro del centro queda que se abrió el contacto, sin el texto.</li></ul>`,
      pie: `<button class="btn wa ancho grande" data-accion="abrirwa">${ic('wa', '')}Abrir WhatsApp</button><button class="btn sec ancho" data-cerrar>Cancelar</button>`,
    };
  };
  P.acc.abrirwa = () => { P.cerrarHoja(); P.toast('Abriendo WhatsApp… (en el prototipo no se abre)'); };

  P.hojas.selector = () => ({
    titulo: 'Cambiar de perfil', sub: 'Esta cuenta tiene tres perfiles. Al cambiar de centro, la sesión cambia de contexto y no se ve nada del otro.',
    html: `<div class="lista tarjeta plana">${[
      ['b-inicio', 'area', 'Buceador', 'Bea Buzo · reservas, Log Book y puntos'],
      ['c-hoy', 'tienda', 'Centro de Buceo Pruebas', 'Dueña · todo el centro'],
      ['f-hoy', 'persona', 'Freelance', 'Guía e instructora por libre'],
    ].map(([id, icn, t, s]) => C.fila(icn, t, esc(s), `data-go="${id}"`)).join('')}</div>`,
  });

  /* ---------------- events (one delegated listener on the phone) ---------------- */
  document.addEventListener('click', (e) => {
    const a = e.target.closest('[data-ir]'); if (a) { e.preventDefault(); P.go(a.dataset.ir); document.getElementById('indice')?.classList.remove('abierto'); return; }
    const ctl = e.target.closest('[data-ctl]'); if (ctl) { const [k, v] = ctl.dataset.ctl.split(':'); P.ajustar(k, v); return; }
    const tel = e.target.closest('.tel'); if (!tel) return;
    const cer = e.target.closest('[data-cerrar]'); if (cer) { P.cerrarHoja(); return; }
    const go = e.target.closest('[data-go]'); if (go) { e.preventDefault(); P.cerrarHoja(); P.go(go.dataset.go, { sel: go.dataset.sel ? { v: go.dataset.sel } : {} }); return; }
    const h = e.target.closest('[data-hoja]'); if (h) { e.preventDefault(); P.abrirHoja(h.dataset.hoja, h.dataset.arg); return; }
    const ac = e.target.closest('[data-accion]'); if (ac && P.acc[ac.dataset.accion]) { e.preventDefault(); P.acc[ac.dataset.accion](ac, e); }
  });
  document.addEventListener('keydown', (e) => { if (e.key === 'Escape') P.cerrarHoja(); });

  /* ---------------- the map (stylised coast of Xàbia, generated) ---------------- */
  const costaX = (y) => 470 + Math.sin(y / 110) * 38 + Math.sin(y / 37) * 9 + (y > 200 && y < 300 ? 60 * Math.sin((y - 200) / 100 * Math.PI) : 0) +
    (y > 520 && y < 620 ? 50 * Math.sin((y - 520) / 100 * Math.PI) : 0) + (y > 640 && y < 720 ? 42 * Math.sin((y - 640) / 80 * Math.PI) : 0);
  P.mapaSVG = function (opts = {}) {
    const pts = []; for (let y = -20; y <= 1270; y += 10) pts.push([costaX(y), y]);
    const tierra = `M -10 -20 ${pts.map(([x, y]) => `L ${x.toFixed(1)} ${y}`).join(' ')} L -10 1270 Z`;
    const iso = [40, 95, 170, 260, 370].map((o, i) => `<path d="M ${pts.map(([x, y]) => `${(x + o + Math.sin(y / 60 + i) * 8).toFixed(1)} ${y}`).join(' L ')}" fill="none" stroke="var(--mapa-iso)" stroke-width="1.4"/>`).join('');
    const pin = (p, act) => `<g class="pin${act ? ' activo' : ''}" data-pin="${p.id}" transform="translate(${p.x} ${p.y})" role="button" tabindex="0" aria-label="${esc(p.nombre)}, ${esc(p.tipo)}">
      <circle r="22" fill="transparent"/><circle class="halo" r="17" fill="transparent"/><circle class="borde" r="${act ? 14 : 12}"/>
      <g clip-path="url(#recorte${act ? 'G' : ''})"><circle r="${act ? 12.5 : 10.5}" fill="#D42A1F"/><path d="${act ? 'M-15 7 L7 -15 L15 -7 L-7 15Z' : 'M-13 6 L6 -13 L13 -6 L-6 13Z'}" fill="#FFFFFF"/></g></g>`;
    const centro = (c) => `<g transform="translate(${c.x} ${c.y})" role="img" aria-label="${esc(c.nombre)}"><circle r="22" fill="transparent"/><circle r="17" fill="#FFFFFF" stroke="#076898" stroke-width="2.5"/><image href="img/logo-centro.webp" x="-12" y="-12" width="24" height="24" clip-path="url(#recorteC)"/></g>`;
    const grupo = (x, y, n) => `<g transform="translate(${x} ${y})" role="img" aria-label="${n} puntos agrupados"><circle r="19" fill="#C8281E" stroke="#FFFFFF" stroke-width="2.5"/><text text-anchor="middle" dy="5" fill="#FFFFFF" font-size="14" font-weight="700" font-family="Inter, sans-serif">${n}</text></g>`;
    return `<svg class="mapa-svg" viewBox="0 0 1190 1250" aria-label="Mapa de la costa de Xàbia (dibujo de ejemplo)">
      <defs><clipPath id="recorte"><circle r="10.5"/></clipPath><clipPath id="recorteG"><circle r="12.5"/></clipPath><clipPath id="recorteC"><circle r="12"/></clipPath></defs>
      <rect width="1190" height="1250" fill="var(--mapa-mar)"/>${iso}
      <path d="${tierra}" fill="var(--mapa-tierra)" stroke="var(--mapa-costa)" stroke-width="2"/>
      <ellipse cx="640" cy="440" rx="26" ry="15" fill="var(--mapa-tierra)" stroke="var(--mapa-costa)" stroke-width="2"/>
      <text x="300" y="470" fill="var(--suave)" font-size="15" font-weight="600" font-family="Inter, sans-serif">Xàbia</text>
      <text x="270" y="790" fill="var(--suave)" font-size="13" font-family="Inter, sans-serif">Benitatxell</text>
      ${D.centros.map(centro).join('')}${grupo(760, 980, 7)}${grupo(820, 120, 12)}${grupo(560, 1080, 5)}
      ${D.puntos.map((p) => pin(p, opts.activo === p.id)).join('')}</svg>`;
  };
  P.mapaInit = function (root, alMover) {
    const svg = root.querySelector('.mapa-svg'); if (!svg) return;
    const m = P.s.mapa; m.x = m.x ?? -230; m.y = m.y ?? 60;
    const poner = () => { svg.style.transform = `translate(${m.x}px, ${m.y}px)`; };
    poner();
    let ini = null;
    svg.addEventListener('pointerdown', (e) => { if (e.target.closest('[data-pin]')) return; ini = { x: e.clientX, y: e.clientY, mx: m.x, my: m.y }; svg.setPointerCapture(e.pointerId); });
    svg.addEventListener('pointermove', (e) => { if (!ini) return; m.x = ini.mx + e.clientX - ini.x; m.y = ini.my + e.clientY - ini.y; poner(); });
    svg.addEventListener('pointerup', () => { if (ini && (Math.abs(m.x - ini.mx) + Math.abs(m.y - ini.my) > 12)) alMover && alMover(); ini = null; });
    P.centrarEn = (p) => { const r = root.getBoundingClientRect(); m.x = r.width / 2 - (p.x - 200) ; m.y = r.height * 0.36 - (p.y - 200); svg.style.transition = 'transform .3s'; poner(); setTimeout(() => { svg.style.transition = ''; }, 320); };
  };

  /* ---------------- boot ---------------- */
  P.arrancar = function () {
    try { const g = JSON.parse(localStorage.getItem('wd-proto') || '{}'); Object.assign(P.s, g); } catch (e) { /* no storage */ }
    const h = (location.hash || '').slice(1);
    if (document.body.classList.contains('captura')) P.s.captura = true;
    P.go(P.screens[h] ? h : 'b-inicio');
    document.getElementById('abrir-indice')?.addEventListener('click', () => document.getElementById('indice').classList.add('abierto'));
    document.getElementById('cerrar-indice')?.addEventListener('click', () => document.getElementById('indice').classList.remove('abierto'));
    document.getElementById('abrir-notas')?.addEventListener('click', () => document.getElementById('notas').classList.toggle('abierto'));
    window.addEventListener('hashchange', () => { const k = location.hash.slice(1); if (P.screens[k] && k !== P.s.pant) P.go(k); });
  };
})();
