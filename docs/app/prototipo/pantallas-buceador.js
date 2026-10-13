/* Screens: entry (production and test variant), settings, visitor and diver module. Sample data only. */
(function () {
  'use strict';
  const { D, C, ic, esc, dia, fCorta, fLarga, eur } = P;
  const G1 = 'Entrada y comunes', GV = 'Visitante', GB = 'Buceador';

  const modo = (s) => s.modo === 'pago' ? `<span class="tag neutro">${ic('cobrar', '')}Pago al reservar</span>` : `<span class="tag neutro">${ic('sobre', '')}Bajo petición</span>`;
  const libres = (s) => s.total - s.ocup - s.pend;
  const tarjetaSalida = (s) => `<article class="tarjeta tarjeta-salida"><img class="foto" src="${s.foto}" alt="${esc(s.punto)}" loading="lazy">
    <div class="pad"><div class="fila-entre"><span class="eti num">Hoy · ${s.hora}</span>${modo(s)}</div>
    <h3>${esc(s.titulo)}</h3><p class="suave peq">${esc(D.centro.nombre)} · ${esc(s.punto)}</p>
    <div class="fila-entre"><span class="peq"><b class="num">${libres(s)}</b> plazas libres</span><span class="precio">desde ${eur(s.precio)}</span></div>
    <button class="btn ancho" data-hoja="reserva" data-arg="${s.id}">Reservar</button></div></article>`;
  const cabeceraInicio = (nombre) => `<header class="cab bati"><div class="cab-fila"><div class="avatar">${nombre ? 'BB' : ic('persona', '')}</div><div class="crece"><p class="suave peq">${nombre ? 'Hola, ' + nombre : 'Hola'}</p><p style="font-weight:600">${nombre ? 'Advanced Open Water · 64 inmersiones' : 'Bienvenido a WORLDIVES'}</p></div>
    ${nombre ? C.accion('avisos', 'Avisos', 'data-go="ajustes" style="min-height:56px;padding:6px 8px;border:0;background:none"') : '<button class="btn sec" data-go="entrada" style="min-height:44px">Entrar</button>'}</div>
    <h1>¿Dónde quieres bucear?</h1>
    <button class="buscador" data-go="b-buscar" style="text-align:left;cursor:text">${ic('buscar', '')}<span class="suave">Puntos, centros, freelance, experiencias…</span></button>
    <div class="chips">${['Cerca de mí', 'Hoy', 'Mañana', 'Este finde', 'Arrecifes', 'Pecios', 'Cuevas y cenotes', 'Bautizos', 'Cursos'].map((t, i) => `<button class="chip" aria-pressed="${i === 0}" data-go="${i === 0 ? 'b-explorar' : 'b-explorar-media'}">${i === 0 ? ic('ubicacion', '') : ''}${t}</button>`).join('')}</div></header>`;
  const tipos = () => `<section class="pila-8"><h2>Tipos de buceo</h2><div class="carrusel-h">${[['Arrecifes', 'img/arrecife2.webp'], ['Pecios', 'img/nocturna.webp'], ['Cuevas y cenotes', 'img/cenote.webp'], ['Bautizos', 'img/buceadores.webp']].map(([t, f]) =>
    `<button class="tarjeta" data-go="b-explorar-media" style="padding:0;overflow:hidden;text-align:left;cursor:pointer;flex-basis:44%"><img src="${f}" alt="" style="height:96px;width:100%;object-fit:cover"><span style="display:block;padding:8px 10px;font-weight:600">${t}</span></button>`).join('')}</div></section>`;

  /* ---------- entry ---------- */
  P.reg('entrada', { grupo: G1, titulo: 'Entrada', ref: '§3.1', mod: 'visitante', tab: 'entrada', sinTabs: true,
    notas: ['Al entrar, la app abre el módulo del rol de la cuenta.', 'Sin cuenta se puede mirar todo y reservar: la sesión se pide al final.'],
    web: ['Inicio de sesión y registro de la web (v50.39), con verificación en dos pasos.'],
    html: () => `<div class="entrada bati"><div class="pila-12 centrado"><img class="logo" src="img/logo-horizontal.webp" alt="WORLDIVES">
      <p class="suave">Reserva tu próxima inmersión en menos de un minuto. Centros y freelance: tu día en el móvil.</p></div>
      <div class="pila-8"><button class="btn ancho grande" data-go="b-inicio">Entrar</button><button class="btn sec ancho grande" data-go="b-mi-ficha">Crear cuenta</button>
      <button class="btn texto ancho" data-go="v-inicio">Seguir sin cuenta</button><p class="version">WORLDIVES 1.0 · prototipo</p></div></div>` });

  P.reg('entrada-pruebas', { grupo: G1, titulo: 'Entrada · variante de pruebas', ref: '§9', mod: 'visitante', sinTabs: true, pruebas: true,
    notas: ['Solo en «WORLDIVES Pruebas» (com.worldives.app.pruebas), que convive con la de producción.', 'Ajuste «Servidor» para el ordenador del titular o el VPS de pruebas. HTTP sin cifrar solo aquí y solo hacia esa dirección.',
      'Botones de entrada rápida con las cuentas de prueba fijas. La variante de producción no tiene ni rastro de ellos (comprobación automática).', 'Versión visible aquí y en Ajustes.'],
    web: ['Cuentas de prueba del zip de pruebas (scripts/crear_demo.py).', 'Pagos en modo test de Stripe; WhatsApp y correos sin envío real (carpeta local).'],
    html: () => `<div class="entrada"><div class="pila-12 centrado"><img class="logo" src="img/logo-horizontal.webp" alt="WORLDIVES" style="width:180px;margin-top:6px">
      <p style="font-weight:600">WORLDIVES Pruebas</p></div>
      <section class="tarjeta pad pila-8"><div class="campo"><label for="srv">${ic('servidor', '')} Servidor</label><input id="srv" value="http://192.168.1.50:8100" inputmode="url">
      <span class="ayuda">El ordenador donde arrancas el zip de pruebas, en tu misma wifi. Más adelante, el VPS de pruebas.</span></div>
      <div class="fila"><span class="crece">${C.tag('ok', 'Conectado · v50.47 de pruebas')}</span><button class="btn sec" style="min-height:44px" data-accion="probar">Probar</button></div></section>
      <section class="pila-8"><p class="eti">Entrada rápida (solo pruebas)</p><div class="cuentas-prueba">
      ${[['buzo.prueba', 'b-inicio'], ['centro.prueba', 'c-hoy'], ['centro2.prueba', 'c-hoy'], ['freelance.prueba', 'f-hoy'], ['instructor.prueba', 'c-instructor'], ['admin.prueba', '']].map(([u, d]) => `<button class="btn sec" ${d ? `data-go="${d}"` : 'data-accion="admin"'}>${u}</button>`).join('')}</div>
      <p class="suave peq">Contraseña de todas: la del zip de pruebas. Pagos con la tarjeta 4242 4242 4242 4242.</p></section>
      <p class="version">WORLDIVES Pruebas 0.2 · web v50.47 · Android</p></div>` });
  P.acc.probar = () => P.toast('Conexión correcta con el servidor de pruebas');
  P.acc.admin = () => P.toast('La administración se queda en la web: se abre el navegador');

  P.reg('ajustes', { grupo: G1, titulo: 'Ajustes', ref: '§4.5 y §2.2', mod: 'buceador', tab: 'b-mi-area',
    notas: ['Tema Clásico (claro) por defecto para todos; Futurista sobrio y Automático como opción.', 'Tamaño de texto Normal, Grande y Enorme. A los centros se les sugiere «Grande» la primera vez.', 'Borrar la cuenta en dos toques (obligatorio en las tiendas).', 'Prueba: los botones de tema y tamaño cambian este prototipo.'],
    web: ['Idioma, avisos y sesiones abiertas de «Mi cuenta».'], falta: ['Unidades (métrico/imperial): no lo he encontrado en la web.', 'Tema y tamaño de texto: la web tiene un solo tema; es nuevo de la app.'],
    html: (s) => `<div class="cuerpo">${C.volver('b-mi-area', 'Mi área')}<h1>Ajustes</h1>
      <section class="pila-8"><p class="eti">Apariencia</p><div class="seg" role="group" aria-label="Tema">${[['clasico', 'Clásico'], ['futurista', 'Futurista'], ['auto', 'Automático']].map(([v, t]) => `<button aria-pressed="${s.tema === v}" data-accion="tema" data-v="${v}">${t}</button>`).join('')}</div>
      <div class="seg" role="group" aria-label="Tamaño del texto">${[['normal', 'Normal'], ['grande', 'Grande'], ['enorme', 'Enorme']].map(([v, t]) => `<button aria-pressed="${s.tam === v}" data-accion="tam" data-v="${v}">${t}</button>`).join('')}</div></section>
      <section class="tarjeta plana lista">${C.fila('idioma', 'Idioma', 'Español')}${C.fila('ola2', 'Unidades', 'Metros, °C, bar')}${C.fila('avisos', 'Avisos', 'Reservas, pagos, recordatorios y cambios')}${C.fila('candado', 'Sesiones abiertas', 'Este móvil y 1 ordenador')}${C.fila('documento', 'Privacidad y textos legales', '')}</section>
      <section class="tarjeta plana lista">${C.fila('bug', 'Reportar fallo', 'Solo en la variante de pruebas', 'data-go="reportar"')}${C.fila('salir', 'Cerrar sesión', '')}</section>
      <button class="btn peligro ancho" data-hoja="borrar">${ic('papelera', '')}Borrar mi cuenta</button><p class="version">WORLDIVES 1.0 · prototipo de la Tanda 0</p></div>` });
  P.acc.tema = (b) => P.ajustar('tema', b.dataset.v);
  P.acc.tam = (b) => P.ajustar('tam', b.dataset.v);
  P.hojas.borrar = () => ({ titulo: '¿Borrar tu cuenta?', sub: 'Se borran tus datos personales. Las reservas pasadas se guardan sin tu nombre, como dice la ley.',
    html: C.pendiente('Las reservas futuras: ¿se cancelan solas o se pide anularlas antes? Hoy la web pide anularlas antes.'), pie: '<button class="btn peligro ancho grande" data-accion="borrado">Sí, borrar mi cuenta</button><button class="btn sec ancho" data-cerrar>No, volver</button>' });
  P.acc.borrado = () => { P.cerrarHoja(); P.toast('Cuenta borrada (prototipo)'); };

  P.reg('reportar', { grupo: G1, titulo: 'Reportar fallo (pruebas)', ref: '§9.4', mod: 'buceador', tab: 'b-mi-area', pruebas: true,
    notas: ['Desde Ajustes o agitando el móvil, solo en la variante de pruebas.', 'Guarda captura, pantalla, versión, modelo de móvil y hora, y lo envía al correo o la carpeta de pruebas.'],
    falta: ['Dónde se reciben: correo o carpeta de pruebas configurada (decisión del titular).'],
    html: () => `<div class="cuerpo">${C.volver('ajustes', 'Ajustes')}<h1>Reportar fallo</h1>
      <div class="fila tarjeta pad"><div style="width:72px;height:128px;border-radius:10px;background:var(--sup2);display:grid;place-items:center;flex:none" aria-label="Captura de la pantalla">${ic('camara', '')}</div>
      <dl class="datos crece" style="grid-template-columns:1fr"><div><dt>Pantalla</dt><dd>Centro · Hoy</dd></div><div><dt>Versión</dt><dd>Pruebas 0.2 · web v50.47</dd></div><div><dt>Móvil</dt><dd>Android 15 · gama media</dd></div><div><dt>Hora</dt><dd>13/10/2026 9:14</dd></div></dl></div>
      <div class="campo"><label for="qp">¿Qué ha pasado?</label><textarea id="qp">Al aceptar la solicitud de Erik, el contador de Solicitudes no ha bajado.</textarea></div>
      <button class="btn ancho grande" data-accion="enviarfallo">Enviar</button></div>` });
  P.acc.enviarfallo = () => P.toast('Enviado a la carpeta de pruebas. Gracias.');

  /* ---------- visitor ---------- */
  P.reg('v-inicio', { grupo: GV, titulo: 'Inicio sin cuenta', ref: '§3.2 y §4.1', mod: 'visitante', tab: 'v-inicio',
    notas: ['Pestañas: Inicio · Explorar · Entrar.', 'Ve salidas con precio y plazas cerca de él (promesa: ≤ 10 s).', '«Reservar» funciona sin cuenta: la sesión se pide al final.'],
    web: ['Buscador y salidas públicas de la portada.'],
    html: () => cabeceraInicio('') + `<div class="cuerpo"><section class="pila-8"><div class="seccion-cab"><h2>Salidas con plazas cerca de ti</h2><button class="btn texto" data-go="v-explorar">Ver todas</button></div>
      <div class="carrusel-h">${D.salidas.map(tarjetaSalida).join('')}</div></section>${tipos()}</div>` });
  P.reg('v-explorar', { grupo: GV, titulo: 'Explorar sin cuenta', ref: '§4.2', mod: 'visitante', tab: 'v-explorar', sinScroll: true,
    notas: ['El mismo mapa que el buceador; la ubicación solo se pide al tocar «Mi ubicación».'], html: (s) => mapa(s, 'asomada'), init: (r, s) => mapaInit(r, s) });
  P.reg('v-reserva-sin-cuenta', { grupo: GV, titulo: 'Reservar sin cuenta: entrar al final', ref: '§4.4.6', mod: 'visitante', tab: 'v-inicio',
    notas: ['La sesión se pide al final, con registro mínimo, y vuelve al mismo punto de la reserva.'], web: ['Registro de la web (nombre, email, contraseña).'],
    falta: ['Inicio rápido con Google o Apple: la web no lo tiene hoy. ¿Se añade?'],
    html: () => cabeceraInicio(''), hoja: 'sincuenta' });
  P.hojas.sincuenta = () => ({ titulo: 'Para terminar, entra o crea tu cuenta', sub: 'Inmersión simple en barco · hoy 09:00 · 45 €. Tu reserva te espera aquí.',
    html: `<div class="seg"><button aria-pressed="false">Ya tengo cuenta</button><button aria-pressed="true">Crear cuenta</button></div>
      <div class="campo"><label for="rn">Nombre y apellidos</label><input id="rn" autocomplete="name" value="Bea Buzo"></div>
      <div class="campo"><label for="re">Correo</label><input id="re" type="email" autocomplete="email" value="bea@example.com"></div>
      <div class="campo"><label for="rp">Contraseña</label><input id="rp" type="password" autocomplete="new-password" value="••••••••••"><span class="ayuda">Mínimo 10 caracteres.</span></div>`,
    pie: '<button class="btn ancho grande" data-hoja="reserva" data-arg="s2">Crear cuenta y seguir con la reserva</button>' });

  /* ---------- diver: home ---------- */
  P.reg('b-inicio', { grupo: GB, titulo: 'Inicio', ref: '§4.1', mod: 'buceador', tab: 'b-inicio',
    notas: ['Buscador grande y chips (Cerca de mí, Hoy, Mañana, Este finde, Arrecifes, Pecios, Cuevas y cenotes, Bautizos, Cursos).', 'Tarjeta «Próxima inmersión» con cuenta atrás, punto de encuentro, Cómo llegar, Justificante y WhatsApp al centro.', 'Carrusel de salidas con plazas: «Reservar» abre la reserva rápida en una hoja.', 'Carrusel «Repetir» con los centros donde ya reservó.'],
    web: ['Salidas, plazas y precios (/api/provider-services), reservas del buceador, justificante en PDF.'],
    html: () => cabeceraInicio('Bea') + `<div class="cuerpo">
      <section class="tarjeta pad pila-12" aria-label="Próxima inmersión"><div class="fila">${C.anillo(.72, '2', 'días', 'grande')}<div class="crece pila"><span class="eti">Próxima inmersión</span><h2>Doble inmersión en barco</h2>
      <p class="peq"><b class="num">${fCorta(dia(2))} · 08:30</b> · Cabo de San Antonio</p><p class="suave peq">Encuentro: Puerto de Xàbia, pantalán 3</p></div></div>
      <div class="tags">${C.tag('ok', 'Confirmada y pagada')}</div>
      <div class="acciones tres">${C.accion('ruta', 'Cómo llegar')}${C.accion('recibo', 'Justificante')}${C.accion('wa', 'WhatsApp al centro', 'data-hoja="wacentro"', 'wa')}</div></section>
      <section class="pila-8"><div class="seccion-cab"><h2>Salidas con plazas cerca de ti</h2><button class="btn texto" data-go="b-explorar-media">Ver todas</button></div><div class="carrusel-h">${D.salidas.map(tarjetaSalida).join('')}</div></section>
      <section class="pila-8"><h2>Repetir</h2><div class="tarjeta pad fila"><img src="${D.centro.logo}" alt="" class="logo-centro"><div class="crece"><p style="font-weight:600">${esc(D.centro.nombre)}</p><p class="suave peq">4 reservas · la última, ${fCorta(dia(-20))}</p></div><button class="btn sec" data-hoja="reserva" data-arg="s2" style="min-height:44px">Reservar de nuevo</button></div></section>
      ${tipos()}</div>` });
  P.hojas.wacentro = () => ({ titulo: 'WhatsApp a ' + D.centro.nombre, sub: 'Número público del centro y un mensaje con tu reserva. Puedes cambiarlo antes de enviarlo.',
    html: `<div class="chat-fondo"><div class="burbuja" contenteditable="true">Hola, soy Bea Buzo. Tengo reserva para la doble inmersión del ${fLarga(dia(2))} a las 8:30 (WOD-000117). </div></div>`,
    pie: `<button class="btn wa ancho grande" data-accion="abrirwa">${ic('wa', '')}Abrir WhatsApp</button><button class="btn sec ancho" data-cerrar>Cancelar</button>` });

  /* ---------- diver: explore (map + bottom sheet) ---------- */
  function mapa(s, altura, opts = {}) {
    const activo = opts.activo;
    const tarjetas = D.puntos.map((p) => `<article class="tarjeta" data-punto="${p.id}"><div class="mini"><img src="${p.foto}" alt="${esc(p.nombre)}"><div class="crece"><h3>${esc(p.nombre)}</h3>
      <p class="suave peq">${p.tipo} · ${p.prof} · ${p.nivel}</p><p class="peq"><b>Próxima:</b> hoy 09:00 · <b class="num">3</b> plazas · desde ${eur(45)}</p>
      <div class="btn-fila" style="margin-top:4px"><button class="btn" style="min-height:44px;padding:6px 8px" data-go="b-ficha-punto">Ver salidas</button><button class="btn sec" style="min-height:44px;padding:6px 8px" data-go="b-ficha-punto">Ficha</button></div></div></div></article>`).join('');
    const filas = D.puntos.map((p) => `<button class="tarjeta mini" style="text-align:left;cursor:pointer;width:100%" data-go="b-ficha-punto"><img src="${p.foto}" alt="" style="width:72px;height:72px"><span class="crece"><b>${esc(p.nombre)}</b><span class="suave peq">${p.tipo} · ${p.prof} · ${p.nivel}</span><span class="peq">Hoy 09:00 · 3 plazas · desde ${eur(45)}</span></span></button>`).join('');
    return `<div class="mapa" id="mapa">${P.mapaSVG({ activo })}</div>
      <div class="mapa-sup"><div class="buscador">${ic('buscar', '')}<input aria-label="Buscar" placeholder="Buscar en el mapa" value="Xàbia"><button class="btn sec" data-hoja="filtros">${ic('filtros', '')}Filtros · 2</button></div>
      <div class="chips">${['Puntos', 'Centros', 'Salidas hoy', 'Freelance', 'Experiencias'].map((t, i) => `<button class="chip" aria-pressed="${i < 2}">${t}</button>`).join('')}</div></div>
      <div class="mapa-lado"><button data-hoja="ubicacion">${ic('ubicacion', '')}Mi ubicación</button><button data-hoja="capas">${ic('capas', '')}Capas</button></div>
      <button class="btn zona-btn" data-accion="zona" ${opts.zona ? '' : 'hidden'}>${ic('buscar', '')}Buscar en esta zona</button>
      ${activo ? `<div class="carrusel" id="carrusel">${tarjetas}</div>` :
        `<section class="mapa-hoja" id="mhoja" data-altura="${altura}" aria-label="Resultados"><div class="hoja-asa" id="masa" role="button" tabindex="0" aria-label="Cambiar la altura de la lista"></div>
        <header class="hoja-cab"><div><h2>32 puntos · 11 centros en esta zona</h2>${altura === 'asomada' ? '<p class="suave peq">Arrastra hacia arriba o toca «Ver lista»</p>' : ''}</div></header>
        <div class="hoja-cuerpo">${altura === 'completa' ? `<div class="chips">${['Cerca', 'Precio', 'Valoración', 'Próxima salida'].map((t, i) => `<button class="chip" aria-pressed="${i === 0}">${t}</button>`).join('')}</div>` : ''}${filas}</div></section>`}
      <button class="btn ver-lista" data-accion="verlista">${altura === 'completa' ? ic('mapa', '') + 'Ver mapa' : ic('lista', '') + 'Ver lista'}</button>`;
  }
  function mapaInit(root, s) {
    P.mapaInit(root, () => { const z = root.querySelector('.zona-btn'); if (z) z.hidden = false; });
    root.addEventListener('click', (e) => { const pin = e.target.closest('[data-pin]'); if (pin) P.go('b-explorar-tarjeta', { sel: { v: pin.dataset.pin } }); });
    const hoja = root.querySelector('#mhoja'), asa = root.querySelector('#masa'), orden = ['asomada', 'media', 'completa'];
    const poner = (a) => { hoja.dataset.altura = a; const b = root.querySelector('.ver-lista'); b.innerHTML = a === 'completa' ? ic('mapa', '') + 'Ver mapa' : ic('lista', '') + 'Ver lista'; };
    if (hoja && asa) {
      let y0 = null;
      asa.addEventListener('pointerdown', (e) => { y0 = e.clientY; asa.setPointerCapture(e.pointerId); });
      asa.addEventListener('pointerup', (e) => { if (y0 == null) return; const dy = e.clientY - y0, i = orden.indexOf(hoja.dataset.altura); y0 = null;
        poner(Math.abs(dy) < 8 ? orden[(i + 1) % 3] : orden[Math.max(0, Math.min(2, i + (dy < 0 ? 1 : -1)))]); });
      asa.addEventListener('keydown', (e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); poner(orden[(orden.indexOf(hoja.dataset.altura) + 1) % 3]); } });
    }
    P.acc.verlista = () => { if (hoja) poner(hoja.dataset.altura === 'completa' ? 'asomada' : 'completa'); else P.go('b-explorar-lista'); };
    P.acc.zona = (b) => { b.hidden = true; P.toast('Buscando en esta zona: 9 puntos y 3 centros'); };
    const car = root.querySelector('#carrusel');
    if (car) {
      const ir = (id) => { root.querySelectorAll('[data-pin]').forEach((g) => g.classList.toggle('activo', g.dataset.pin === id)); const p = D.puntos.find((x) => x.id === id); if (p) P.centrarEn(p); };
      const idx = D.puntos.findIndex((p) => p.id === s.sel.v);
      requestAnimationFrame(() => { car.scrollLeft = Math.max(0, idx) * (car.firstElementChild.offsetWidth + 10); });
      let t; car.addEventListener('scroll', () => { clearTimeout(t); t = setTimeout(() => { const i = Math.round(car.scrollLeft / (car.firstElementChild.offsetWidth + 10)); ir(D.puntos[i]?.id); }, 120); });
      ir(s.sel.v || D.puntos[0].id);
    }
  }
  const notasMapa = ['Mapa a pantalla completa con buscador, Filtros (con contador), chips deslizables, Mi ubicación y Capas.', 'Hoja inferior con tres alturas: se arrastra con el dedo y también hay un botón «Ver lista / Ver mapa» siempre visible.',
    'Marcadores con la bandera de buceo circular de la web (Fase 1C), 44 px de zona táctil; centros con su logo; grupos con número.'];
  const webMapa = ['Puntos, centros, freelance y experiencias del buscador y del mapa de la web (Leaflet + capas Mapa, Satélite y Relieve, v50.43).'];
  P.reg('b-explorar', { grupo: GB, titulo: 'Explorar · hoja asomada', ref: '§4.2', mod: 'buceador', tab: 'b-explorar', sinScroll: true, notas: notasMapa, web: webMapa,
    html: (s) => mapa(s, 'asomada'), init: mapaInit });
  P.reg('b-explorar-media', { grupo: GB, titulo: 'Explorar · hoja media', ref: '§4.2.2', mod: 'buceador', tab: 'b-explorar', sinScroll: true, notas: ['Lista de tarjetas de lo visible en el mapa.'], web: webMapa,
    html: (s) => mapa(s, 'media'), init: mapaInit });
  P.reg('b-explorar-lista', { grupo: GB, titulo: 'Explorar · lista completa', ref: '§4.2.2', mod: 'buceador', tab: 'b-explorar', sinScroll: true, notas: ['Lista a pantalla completa con orden: Cerca, Precio, Valoración, Próxima salida.'], web: webMapa,
    html: (s) => mapa(s, 'completa'), init: mapaInit });
  P.reg('b-explorar-tarjeta', { grupo: GB, titulo: 'Explorar · tarjeta del marcador', ref: '§4.2.3', mod: 'buceador', tab: 'b-explorar', sinScroll: true,
    notas: ['Al tocar un marcador sube una tarjeta con foto, tipo, profundidad, nivel, próxima salida con plazas y precio, «Ver salidas» y «Ficha».', 'Deslizar la tarjeta a los lados pasa al punto vecino y el mapa se centra en él.'], web: webMapa,
    html: (s) => mapa(s, 'asomada', { activo: s.sel.v || 'p1' }), init: mapaInit });
  P.reg('b-explorar-zona', { grupo: GB, titulo: 'Explorar · «Buscar en esta zona»', ref: '§4.2.5', mod: 'buceador', tab: 'b-explorar', sinScroll: true,
    notas: ['Aparece al mover el mapa. No recarga sola en cada movimiento, para ahorrar datos y no marear.'], web: webMapa,
    html: (s) => mapa(s, 'asomada', { zona: true }), init: mapaInit });
  P.reg('b-capas', { grupo: GB, titulo: 'Explorar · capas', ref: '§4.2.1', mod: 'buceador', tab: 'b-explorar', sinScroll: true, notas: ['Mapa, Satélite y Relieve en una hoja inferior, no en un menú.'], web: webMapa,
    html: (s) => mapa(s, 'asomada'), init: mapaInit, hoja: 'capas' });
  P.reg('b-filtros', { grupo: GB, titulo: 'Explorar · filtros', ref: '§4.3', mod: 'buceador', tab: 'b-explorar', sinScroll: true,
    notas: ['Fecha, tipo, nivel, precio, idioma, confirmación inmediata, nitrox, alquiler de equipo, barco o costa.', 'Los filtros se guardan en el enlace (para compartir) y se recuerdan.'], web: ['Filtros del buscador de la web.'],
    html: (s) => mapa(s, 'asomada'), init: mapaInit, hoja: 'filtros' });
  P.hojas.capas = () => ({ titulo: 'Capas del mapa', html: `<div class="pila-8">${[['Mapa', 'var(--mapa-tierra)', true], ['Satélite', '#4b5d3f', false], ['Relieve', '#c9d6c0', false]].map(([t, c, on]) =>
    `<button class="lista-fila tarjeta plana" aria-pressed="${on}" style="${on ? 'border-color:var(--acento);border-width:2px' : ''}"><span style="width:56px;height:40px;border-radius:8px;background:${c};border:1px solid var(--linea);flex:none"></span><span class="crece" style="font-weight:600">${t}</span>${on ? ic('check') : ''}</button>`).join('')}</div>` });
  P.hojas.ubicacion = () => ({ titulo: '¿Usar tu ubicación?', sub: 'Solo para enseñarte lo que tienes cerca. Se pide ahora porque has tocado «Mi ubicación», nunca al abrir la app.',
    html: `<div class="aviso neutro">${ic('info', '')}<span>Si dices que no, el mapa sigue funcionando: se queda en tu última búsqueda (Xàbia).</span></div>`,
    pie: '<button class="btn ancho grande" data-accion="ubi">Permitir</button><button class="btn sec ancho" data-accion="noubi">Ahora no</button>' });
  P.acc.ubi = () => { P.cerrarHoja(); P.toast('Centrado en tu ubicación'); };
  P.acc.noubi = () => { P.cerrarHoja(); P.toast('Sin ubicación: seguimos en Xàbia'); };
  P.hojas.filtros = () => ({ titulo: 'Filtros', alto: '86%',
    html: `<section class="pila-8"><p class="eti">Fecha</p><div class="chips">${['Hoy', 'Mañana', 'Este finde', 'Elegir fecha'].map((t, i) => `<button class="chip" aria-pressed="${i === 0}">${t}</button>`).join('')}</div></section>
      <section class="pila-8"><p class="eti">Tipo de inmersión</p><div class="tags">${['Arrecife', 'Pared', 'Pecio', 'Cueva o cenote', 'Nocturna', 'Bautizo', 'Curso'].map((t, i) => `<button class="chip" aria-pressed="${i === 1}">${t}</button>`).join('')}</div></section>
      <section class="pila-8"><p class="eti">Nivel</p><div class="tags">${['Sin titulación', 'Open Water', 'Advanced', 'Rescue o más'].map((t, i) => `<button class="chip" aria-pressed="${i === 2}">${t}</button>`).join('')}</div></section>
      <section class="pila-8"><p class="eti">Precio por persona</p><div class="btn-fila"><div class="campo"><label for="pmin">Desde</label><input id="pmin" value="0 €" inputmode="numeric"></div><div class="campo"><label for="pmax">Hasta</label><input id="pmax" value="100 €" inputmode="numeric"></div></div></section>
      <div class="campo"><label for="fid">Idioma del guía</label><select id="fid"><option>Cualquiera</option><option>Español</option><option>English</option><option>Français</option><option>Deutsch</option></select></div>
      <section class="tarjeta plana" style="padding:0 14px">${[['Confirmación inmediata (pago al reservar)', false], ['Nitrox', false], ['Alquiler de equipo', true]].map(([t, on]) => `<label class="interruptor"><span>${t}</span><input type="checkbox" ${on ? 'checked' : ''}></label>`).join('<div class="separa"></div>')}</section>
      <section class="pila-8"><p class="eti">Salida</p><div class="seg"><button aria-pressed="true">Barco o costa</button><button aria-pressed="false">Barco</button><button aria-pressed="false">Costa</button></div></section>`,
    pie: '<button class="btn ancho grande" data-cerrar>Ver 18 resultados</button><button class="btn texto ancho">Borrar filtros</button>' });

  P.reg('b-buscar', { grupo: GB, titulo: 'Buscador con resultados al escribir', ref: '§4.3', mod: 'buceador', tab: 'b-explorar',
    notas: ['El mismo buscador de la web: centros, puntos, buceos cercanos, freelance y experiencias, agrupados por tipo mientras escribe.'], web: ['Buscador de la web (autocompletado).'],
    html: () => `<div class="cuerpo"><div class="fila"><button class="btn texto" data-go="b-inicio" aria-label="Volver">${ic('atras', '')}</button><div class="buscador crece">${ic('buscar', '')}<input aria-label="Buscar" value="gra" autofocus></div></div>
      ${[['Puntos de buceo', [['pin', 'Cala Granadella', 'Arrecife · 3–12 m · Xàbia', 'b-ficha-punto']]], ['Salidas', [['reloj', 'Bautizo de buceo · Cala Granadella', 'Hoy 16:00 · 3 plazas · 60 €', 'b-ficha-centro']]],
        ['Centros', [['tienda', 'Centro de Buceo Pruebas Dos', 'Bucea en Cala Granadella · Xàbia', 'b-ficha-centro']]], ['Freelance', [['persona', 'Tito Guía Pruebas', 'Guía en cenotes · Tulum', 'b-ficha-freelance']]], ['Experiencias', []]].map(([g, rows]) =>
        `<section class="pila-8"><p class="eti">${g}</p>${rows.length ? `<div class="tarjeta plana lista">${rows.map(([i, t, s2, d]) => C.fila(i, t, esc(s2), `data-go="${d}"`)).join('')}</div>` : '<p class="suave peq">Nada con «gra» en experiencias.</p>'}</section>`).join('')}</div>` });

  /* ---------- profile pages ---------- */
  const barraReservar = (desde, arg) => `<div class="barra-fija"><div class="crece"><span class="suave peq">Desde</span><p class="precio">${eur(desde)}</p></div><button class="btn grande" data-hoja="reserva" data-arg="${arg}">Reservar</button></div>`;
  P.reg('b-ficha-centro', { grupo: GB, titulo: 'Ficha del centro', ref: '§4.3', mod: 'buceador', tab: 'b-explorar',
    notas: ['Portada, datos clave, etiqueta del modo de reserva, pestañas Salidas · Servicios · Info · Reseñas y barra fija «Desde X € · Reservar».', 'Llamar · WhatsApp · Cómo llegar · Compartir.'], web: ['Ficha pública del centro, servicios y reseñas.'],
    html: () => `<img src="${D.centro.portada}" alt="Portada del centro" style="height:170px;width:100%;object-fit:cover"><div class="cuerpo" style="margin-top:-34px">
      <div class="fila"><img src="${D.centro.logo}" alt="" class="logo-centro" style="width:64px;height:64px;border:3px solid var(--sup)"><div class="crece" style="padding-top:28px"><h1 style="font-size:var(--t-l)">${esc(D.centro.nombre)}</h1></div></div>
      <p class="suave">${esc(D.centro.lema)}</p><div class="tags"><span class="tag neutro">${ic('estrella', '')}${D.centro.valoracion} · ${D.centro.resenas} reseñas</span><span class="tag neutro">${ic('pin', '')}Xàbia</span><span class="tag neutro">${ic('cobrar', '')}Pago al reservar en 3 servicios</span></div>
      <div class="acciones">${C.accion('tel', 'Llamar')}${C.accion('wa', 'WhatsApp', 'data-hoja="wacentro"', 'wa')}${C.accion('ruta', 'Cómo llegar')}${C.accion('compartir', 'Compartir')}</div>
      <div class="seg"><button aria-pressed="true">Salidas</button><button aria-pressed="false">Servicios</button><button aria-pressed="false">Info</button><button aria-pressed="false">Reseñas</button></div>
      <div class="tarjeta plana lista">${D.salidas.map((s) => `<div class="salida" data-hoja="reserva" data-arg="${s.id}"><div class="hora">${s.hora}<small>hoy</small></div><div class="pila"><b>${esc(s.titulo)}</b><span class="suave peq">${esc(s.punto)} · ${libres(s)} plazas · ${eur(s.precio)}</span>${modo(s)}</div></div>`).join('')}</div></div>${barraReservar(45, 's2')}` });
  P.reg('b-ficha-punto', { grupo: GB, titulo: 'Ficha del punto de buceo', ref: '§4.3', mod: 'buceador', tab: 'b-explorar',
    notas: ['Profundidad, nivel, tipo y las próximas salidas de los centros que bucean allí.'], web: ['Ficha del punto (#/punto) y salidas por punto.'],
    html: () => `<img src="img/arrecife.webp" alt="Isla del Portitxol" style="height:190px;width:100%;object-fit:cover"><div class="cuerpo">${C.volver('b-explorar', 'Mapa')}
      <h1>Isla del Portitxol</h1><div class="tags"><span class="tag neutro">Arrecife</span><span class="tag neutro">6–18 m</span><span class="tag neutro">Open Water</span><span class="tag neutro">Barco</span></div>
      <p>Islote frente a la cala de Portitxol. Praderas de posidonia, meros, pulpos y nudibranquios. Poca corriente.</p>
      <h2>Próximas salidas aquí</h2><div class="tarjeta plana lista">${[D.salidas[1]].concat([{ hora: '09:00', titulo: 'Inmersión simple en barco', punto: 'Isla del Portitxol', modo: 'pago', precio: 45, total: 10, ocup: 2, pend: 0, id: 's2' }]).map((s, i) => `<div class="salida" data-hoja="reserva" data-arg="s2"><div class="hora">${s.hora}<small>${i ? fCorta(dia(1)) : 'hoy'}</small></div><div class="pila"><b>${esc(D.centro.nombre)}</b><span class="suave peq">${libres(s)} plazas · ${eur(s.precio)}</span>${modo(s)}</div></div>`).join('')}</div></div>${barraReservar(45, 's2')}` });
  P.reg('b-ficha-freelance', { grupo: GB, titulo: 'Ficha del freelance', ref: '§4.3', mod: 'buceador', tab: 'b-explorar',
    notas: ['Escaparate del freelance: foto, presentación, idiomas, zonas, titulaciones, servicios por días y medio día.'], web: ['Escaparate /o/<nombre> y servicios del freelance.'],
    html: () => `<div class="cab bati" style="padding-top:16px"><div class="fila"><div class="avatar" style="width:84px;height:84px"><img src="img/tito.webp" alt="Tito"></div><div class="crece"><h1 style="font-size:var(--t-l)">Tito Guía Pruebas</h1><p class="suave">Instructor y guía de cenotes · Tulum</p></div></div></div>
      <div class="cuerpo"><div class="tags"><span class="tag neutro">Español</span><span class="tag neutro">English</span><span class="tag neutro">Riviera Maya</span><span class="tag neutro">Cuevas y cenotes</span></div>
      <p>Guía e instructor en los cenotes de la Riviera Maya desde 2012.</p><div class="acciones">${C.accion('tel', 'Llamar')}${C.accion('wa', 'WhatsApp', 'data-hoja="wacentro"', 'wa')}${C.accion('ruta', 'Cómo llegar')}${C.accion('compartir', 'Compartir')}</div>
      <h2>Servicios</h2><div class="tarjeta plana lista">${[['Cenotes con guía, por días', '180 € por día · 10 % menos desde 3 días'], ['Cenote por la mañana o por la tarde', '110 € medio día'], ['Sesión de fotos y vídeo bajo el agua', '90 € · entrega en 48 h']].map(([t, s2]) => C.fila('', t, esc(s2), 'data-go="b-reserva-dias"')).join('')}</div></div>
      <div class="barra-fija"><div class="crece"><span class="suave peq">Desde</span><p class="precio">${eur(90)}</p></div><button class="btn grande" data-go="b-reserva-dias">Reservar</button></div>` });
  P.reg('b-ficha-experiencia', { grupo: GB, titulo: 'Ficha de una experiencia', ref: '§4.3', mod: 'buceador', tab: 'b-explorar',
    notas: ['Experiencia de varios días de un centro, con plazas y lo que incluye.'], web: ['Experiencias (#/experiencias) y su reserva.'],
    html: () => `<img src="img/experiencia.webp" alt="Islas Medas" style="height:190px;width:100%;object-fit:cover"><div class="cuerpo">${C.volver('b-explorar', 'Mapa')}<h1>Fin de semana en las Medas</h1>
      <p class="suave">${esc(D.centro.nombre)} · Islas Medas, España</p><div class="tags"><span class="tag neutro">${ic('agenda', '')}${fCorta(dia(23))} → ${fCorta(dia(24))}</span><span class="tag neutro">8 plazas</span><span class="tag neutro">${ic('sobre', '')}Bajo petición</span></div>
      <p>Dos días de buceo en la reserva marina. Incluye 4 inmersiones, guía y botellas.</p></div>
      <div class="barra-fija"><div class="crece"><span class="suave peq">Por persona</span><p class="precio">${eur(240)}</p></div><button class="btn grande" data-hoja="reserva" data-arg="s1">Reservar</button></div>` });

  /* ---------- quick booking in a sheet ---------- */
  P.hojas.reserva = (arg, s) => {
    const sal = D.salidas.find((x) => x.id === arg) || D.salidas[1];
    const pago = sal.modo === 'pago', st = s.reserva || (s.reserva = { pers: 1, equipo: true, nitrox: false, abierta: '' });
    const total = (sal.precio + (st.equipo ? 25 : 0) + (st.nitrox ? 8 : 0)) * st.pers;
    const linea = (k, icon, t, sub, editor) => `<div><div class="linea-res">${ic(icon)}<div class="crece"><p style="font-weight:600">${t}</p><p class="suave peq">${sub}</p></div><button class="btn texto" data-accion="cambiar" data-k="${k}">${st.abierta === k ? 'Listo' : 'Cambiar'}</button></div>${st.abierta === k ? `<div class="editor">${editor}</div>` : ''}</div>`;
    return { titulo: sal.titulo, sub: `${esc(D.centro.nombre)} · ${modo(sal)}`, alto: '88%',
      html: `<div>${linea('fecha', 'agenda', `Hoy, ${fLarga(dia(0))} · ${sal.hora}`, esc(sal.punto) + ' · encuentro en el puerto, pantalán 3',
          `<div class="chips">${[0, 1, 2, 3].map((n) => `<button class="chip" aria-pressed="${n === 0}">${n ? fCorta(dia(n)) : 'Hoy'} · ${sal.hora}</button>`).join('')}</div>`)}
        ${linea('pers', 'buddies', st.pers === 1 ? 'Tú (Bea)' : `Tú y ${st.pers - 1} más`, 'Añade a un buddy y él completa sus datos con su enlace',
          `<div class="contador"><button data-accion="pers" data-d="-1" aria-label="Una persona menos">${ic('menos', '')}</button><b>${st.pers}</b><button data-accion="pers" data-d="1" aria-label="Una persona más">${ic('mas1', '')}</button><span class="suave peq">personas</span></div>
          <button class="btn sec" data-accion="pers" data-d="1">${ic('buddies', '')}Añadir buddy: Lucía Pérez</button>`)}
        ${linea('tit', 'ficha', 'Advanced Open Water · 64 inmersiones', 'De tu perfil · el centro lo comprueba en el muelle', '<p class="peq">Se cambia en Mi ficha. Esta reserva usa lo último que guardaste.</p>')}
        ${linea('tallas', 'persona', 'Traje M · escarpines 42 · chaleco M', 'De tu perfil y de tu última reserva con este centro',
          '<div class="btn-fila"><div class="campo"><label for="t1">Traje</label><select id="t1"><option>S</option><option selected>M</option><option>L</option></select></div><div class="campo"><label for="t2">Escarpines</label><select id="t2"><option>41</option><option selected>42</option><option>43</option></select></div></div>')}</div>
        <section class="tarjeta plana" style="padding:0 14px"><label class="interruptor"><span><b>Alquilar equipo completo</b><br><span class="suave peq">+25 € por persona</span></span><input type="checkbox" data-accion="sw" data-k="equipo" ${st.equipo ? 'checked' : ''}></label>
        <div class="separa"></div><label class="interruptor"><span><b>Nitrox</b><br><span class="suave peq">+8 € por persona · extra del servicio</span></span><input type="checkbox" data-accion="sw" data-k="nitrox" ${st.nitrox ? 'checked' : ''}></label></section>
        <p class="suave peq">Cancelación gratis hasta 48 h antes; después se devuelve el 50 %.</p>`,
      pie: `<div class="fila-entre"><span>Total · ${st.pers} ${st.pers === 1 ? 'persona' : 'personas'}</span><span class="precio">${eur(total)}</span></div>
        <button class="btn ancho grande" data-accion="confirmar" data-arg="${sal.id}">${pago ? `Reservar y pagar ${eur(total)}` : 'Enviar solicitud'}</button>
        <p class="suave peq centrado">${pago ? 'Pago seguro con Stripe: Apple Pay, Google Pay, Link o tarjeta.' : 'No pagas nada hasta que el centro acepte.'}</p>` };
  };
  const reabrir = () => { const capa = P.tel().querySelector('#capa .hoja-cuerpo'); const sc = capa ? capa.scrollTop : 0; P.abrirHoja('reserva', P.s.reservaArg); const n = P.tel().querySelector('#capa .hoja-cuerpo'); if (n) n.scrollTop = sc; };
  P.acc.cambiar = (b) => { const st = P.s.reserva; st.abierta = st.abierta === b.dataset.k ? '' : b.dataset.k; reabrir(); };
  P.acc.pers = (b) => { const st = P.s.reserva; st.pers = Math.max(1, Math.min(6, st.pers + (+b.dataset.d))); reabrir(); };
  P.acc.sw = (b) => { P.s.reserva[b.dataset.k] = b.checked; reabrir(); };
  const abrirReserva = P.abrirHoja.bind(P);
  P.abrirHoja = function (nombre, arg) { if (nombre === 'reserva') P.s.reservaArg = arg; return abrirReserva(nombre, arg); };
  P.acc.confirmar = (b) => { const sal = D.salidas.find((x) => x.id === b.dataset.arg) || D.salidas[1]; P.s.reserva = null;
    if (sal.modo === 'pago') { P.toast('Abriendo el pago seguro de Stripe…'); setTimeout(() => P.abrirHoja('confirmada', sal.id), 900); } else P.abrirHoja('solicitada', sal.id); };
  P.hojas.confirmada = (arg) => { const sal = D.salidas.find((x) => x.id === arg) || D.salidas[1]; return { alto: '88%',
    html: `<div class="check-grande">${ic('check', '')}</div><div class="centrado pila"><h1 style="font-size:var(--t-xl)">Reserva confirmada</h1><p class="suave">Has vuelto de Stripe a la app (/r/…). Te hemos enviado el justificante.</p></div>
      <section class="tarjeta pad pila-8"><div class="fila-entre"><b>${esc(sal.titulo)}</b>${C.tag('ok', 'Pagada')}</div><p class="num" style="font-size:var(--t-l);font-weight:700">Hoy · ${sal.hora}</p><p class="suave">Encuentro: Puerto de Xàbia, pantalán 3 · 30 min antes</p></section>
      <div class="acciones">${C.accion('calmas', 'Añadir al calendario')}${C.accion('ruta', 'Cómo llegar')}${C.accion('wa', 'WhatsApp al centro', 'data-hoja="wacentro"', 'wa')}${C.accion('recibo', 'Justificante')}</div>`,
    pie: '<button class="btn sec ancho grande" data-go="b-reservas">Ver mis reservas</button>' }; };
  P.hojas.solicitada = (arg) => { const sal = D.salidas.find((x) => x.id === arg) || D.salidas[0]; return { alto: '80%',
    html: `<div class="check-grande" style="background:var(--sol-s)">${ic('sobre', '')}</div><div class="centrado pila"><h1 style="font-size:var(--t-xl)">Solicitud enviada</h1><p class="suave">El centro responde antes de 24 h. Te avisamos al momento; si acepta, pagas desde el aviso.</p></div>
      <section class="tarjeta pad pila-8"><div class="fila-entre"><b>${esc(sal.titulo)}</b>${C.tag('sol', 'Solicitud')}</div><p class="num" style="font-weight:700">${fCorta(dia(2))} · ${sal.hora}</p><p class="suave">${esc(sal.punto)}</p></section>
      <div class="acciones tres">${C.accion('calmas', 'Añadir al calendario')}${C.accion('wa', 'WhatsApp al centro', 'data-hoja="wacentro"', 'wa')}${C.accion('x', 'Anular solicitud')}</div>`,
    pie: '<button class="btn sec ancho grande" data-go="b-reservas">Ver mis reservas</button>' }; };
  const notasRes = ['Hoja inferior, no página nueva: todo rellenado del perfil y de la última reserva con ese centro.', 'Cada línea tiene «Cambiar» sin salir de la hoja.', 'Botón «Reservar y pagar X €» (Pago al reservar) o «Enviar solicitud» (Bajo petición).'];
  const webRes = ['Reserva y pago de la web (Fase 1B: dos modos), extras nitrox/guía/traslado de la reserva, tallas del perfil.', 'Stripe Checkout con Apple Pay, Google Pay y Link; vuelta por /r/<token>.'];
  P.reg('b-reserva', { grupo: GB, titulo: 'Reserva rápida (pago al reservar)', ref: '§4.4', mod: 'buceador', tab: 'b-inicio', notas: notasRes, web: webRes, html: () => cabeceraInicio('Bea'), hoja: 'reserva', hojaArg: 's2' });
  P.reg('b-reserva-cambiar', { grupo: GB, titulo: 'Reserva rápida · cambiar una línea', ref: '§4.4.5', mod: 'buceador', tab: 'b-inicio', notas: ['Ejemplo: añadir un buddy y subir a 2 personas sin salir de la hoja.'], web: webRes,
    html: (s) => { s.reserva = { pers: 2, equipo: true, nitrox: false, abierta: 'pers' }; return cabeceraInicio('Bea'); }, hoja: 'reserva', hojaArg: 's2' });
  P.reg('b-reserva-solicitud', { grupo: GB, titulo: 'Reserva rápida (bajo petición)', ref: '§4.4.2', mod: 'buceador', tab: 'b-inicio', notas: ['«Enviar solicitud»: no se paga hasta que el centro acepta.'], web: webRes,
    html: (s) => { s.reserva = null; return cabeceraInicio('Bea'); }, hoja: 'reserva', hojaArg: 's1' });
  P.reg('b-reserva-ok', { grupo: GB, titulo: 'Reserva confirmada', ref: '§4.4.4', mod: 'buceador', tab: 'b-inicio', notas: ['✓ grande, hora, punto de encuentro, Añadir al calendario, Cómo llegar, WhatsApp al centro y Justificante, en la misma hoja.'], web: webRes,
    html: () => cabeceraInicio('Bea'), hoja: 'confirmada', hojaArg: 's2' });
  P.reg('b-reserva-enviada', { grupo: GB, titulo: 'Solicitud enviada', ref: '§4.4.2', mod: 'buceador', tab: 'b-inicio', notas: ['Bajo petición: el centro tiene un plazo para responder; el buceador recibe el aviso y paga desde él.'], web: webRes,
    html: () => cabeceraInicio('Bea'), hoja: 'solicitada', hojaArg: 's1' });

  /* booking by days (motor de reservas: calendar white/red and fixed total bar) */
  P.reg('b-reserva-dias', { grupo: GB, titulo: 'Reserva por días (freelance)', ref: '§4.4.8', mod: 'buceador', tab: 'b-explorar',
    notas: ['Servicio «Por días»: calendario con días libres en blanco y ocupados en rojo, y barra fija con el total.', 'El descuento por días se aplica solo.'], web: ['Motor de reservas por días y medio día (v50.44, /api/agenda).'],
    html: () => {
      const ocup = new Set([1, 2, 12, 13, 14, 18, 19, 20]), sel = new Set([6, 7, 8]);
      let cel = ['L', 'M', 'X', 'J', 'V', 'S', 'D'].map((d) => `<div class="dsem">${d}</div>`).join('');
      for (let i = 0; i < 3; i++) cel += '<div></div>';
      for (let d = 1; d <= 31; d++) { const n = d - 13; const est = ocup.has(n) ? 'style="background:var(--urg-f);color:var(--urg-t);border-color:transparent;text-decoration:line-through"' : sel.has(n) ? 'style="background:var(--marca);color:var(--sobre-marca);border-color:transparent"' : '';
        cel += `<button class="dia${d < 14 ? ' fuera' : ''}" ${est} aria-label="${d} de octubre${ocup.has(n) ? ', ocupado' : ''}">${d}</button>`; }
      return `<div class="cuerpo">${C.volver('b-ficha-freelance', 'Tito Guía')}<h1 style="font-size:var(--t-l)">Cenotes con guía, por días</h1><p class="suave">180 € por día · 10 % menos desde 3 días · hasta 4 personas</p>
        <div class="leyenda"><span><i></i>Libre</span><span><i style="background:var(--urg-f);border-color:var(--urg-s)"></i>Ocupado</span><span><i style="background:var(--marca);border-color:var(--marca)"></i>Tu elección</span></div>
        <h2>Octubre 2026</h2><div class="mes">${cel}</div><div class="contador"><span class="crece">Personas</span><button aria-label="Menos">${ic('menos', '')}</button><b>2</b><button aria-label="Más">${ic('mas1', '')}</button></div></div>
        <div class="barra-fija"><div class="crece"><span class="suave peq">3 días · 2 personas · −10 %</span><p class="precio">${eur(972)}</p></div><button class="btn grande" data-accion="soldias">Enviar solicitud</button></div>`;
    } });
  P.acc.soldias = () => P.toast('Solicitud enviada a Tito. Responde antes de 24 h.');

  /* ---------- bookings, buddies, my area ---------- */
  const tarjetaReserva = (t, sub, cuando, estado, acc, extra = '') => `<article class="tarjeta pad pila-8"><div class="fila-entre"><b>${t}</b>${estado}</div><p class="num" style="font-weight:700">${cuando}</p><p class="suave peq">${sub}</p>${extra}${acc}</article>`;
  P.reg('b-reservas', { grupo: GB, titulo: 'Reservas · próximas', ref: '§4.5', mod: 'buceador', tab: 'b-reservas',
    notas: ['Tarjetas con estado (color + icono + texto) y acciones: Pagar, Justificante, Cómo llegar, Llamar, WhatsApp, Cambiar fecha si se permite, Anular.'], web: ['Mis reservas, pago pendiente, cambio de fecha (v50.41), anular y justificante.'],
    html: () => `<div class="cuerpo"><h1>Reservas</h1><div class="seg"><button aria-pressed="true">Próximas · 3</button><button aria-pressed="false" data-go="b-reservas-historial">Historial</button></div>
      ${tarjetaReserva('Cenotes con guía, por días', 'Tito Guía Pruebas · Tulum · 2 personas', `${fCorta(dia(18))} → ${fCorta(dia(20))}`, C.tag('pend', 'Pendiente de pago'),
        `<button class="btn ancho grande">${ic('cobrar', '')}Pagar 324 € de señal</button><p class="suave peq">Tito aceptó tu solicitud. Plazo para pagar: mañana a las 12:00.</p>`)}
      ${tarjetaReserva('Doble inmersión en barco', esc(D.centro.nombre) + ' · Cabo de San Antonio', `${fCorta(dia(2))} · 08:30`, C.tag('ok', 'Confirmada'),
        `<div class="acciones">${C.accion('recibo', 'Justificante')}${C.accion('ruta', 'Cómo llegar')}${C.accion('tel', 'Llamar')}${C.accion('wa', 'WhatsApp', 'data-hoja="wacentro"', 'wa')}</div><div class="btn-fila"><button class="btn sec">Cambiar fecha</button><button class="btn sec">Anular</button></div>`,
        `<div class="fila">${C.qr('worldives:reserva:WOD-000117', 84)}<p class="suave peq crece">Enseña este QR en el muelle. Funciona sin cobertura.</p></div>`)}
      ${tarjetaReserva('Fin de semana en las Medas', esc(D.centro.nombre) + ' · 1 persona', `${fCorta(dia(23))} → ${fCorta(dia(24))}`, C.tag('sol', 'Solicitud enviada'),
        '<p class="suave peq">El centro responde antes de 24 h.</p><div class="btn-fila"><button class="btn sec">Anular solicitud</button></div>')}</div>` });
  P.reg('b-reservas-historial', { grupo: GB, titulo: 'Reservas · historial', ref: '§4.5', mod: 'buceador', tab: 'b-reservas', notas: ['«Repetir reserva» con un toque. Las canceladas, en gris y tachadas.'], web: ['Historial de reservas.'],
    html: () => `<div class="cuerpo"><h1>Reservas</h1><div class="seg"><button aria-pressed="false" data-go="b-reservas">Próximas · 3</button><button aria-pressed="true">Historial</button></div>
      ${tarjetaReserva('Inmersión simple en barco', esc(D.centro.nombre) + ' · Isla del Portitxol', fCorta(dia(-20)) + ' · 09:00', C.tag('ok', 'Buceada'), '<button class="btn sec ancho" data-hoja="reserva" data-arg="s2">Repetir reserva</button>')}
      ${tarjetaReserva('Bautizo de buceo', esc(D.centro.nombre) + ' · Cala Granadella', fCorta(dia(-41)) + ' · 16:00', C.tag('canc', 'Cancelada por el centro'), '<p class="suave peq">Mal tiempo. Devolución completa hecha el ' + fCorta(dia(-41)) + '.</p>')}</div>` });
  P.reg('b-buddies', { grupo: GB, titulo: 'Buddies', ref: '§4.5', mod: 'buceador', tab: 'b-buddies',
    notas: ['Según el encargo de Buddies, sin chat: mis buddies, «Mi código» en QR, grupos y «¿Buceamos?».'], falta: ['Buddies no existe todavía en la web (bloque 4 pendiente desde v50.45). Hay que programarlo en el servidor antes que en la app.'],
    html: () => `<div class="cuerpo"><h1>Buddies</h1>${C.pendiente('Buddies aún no existe en la web. Esta pantalla sigue el encargo de Buddies; se programa primero en el servidor.')}
      <section class="tarjeta pad fila">${C.qr('worldives:buddy:BEA-7K2Q', 96)}<div class="crece pila"><b>Mi código</b><p class="suave peq">Enséñalo para que te añadan como buddy.</p><button class="btn sec" style="min-height:44px">${ic('compartir', '')}Compartir</button></div></section>
      <h2>Mis buddies</h2><div class="tarjeta plana lista">${[['LP', 'Lucía Pérez', 'Rescue · 140 inm.'], ['SA', 'Sven Andersen', 'Advanced · 300 inm.']].map(([c, n, s2]) => `<div class="lista-fila"><div class="avatar">${c}</div><div class="crece"><b>${n}</b><p class="suave peq">${s2}</p></div><button class="btn sec" style="min-height:44px">¿Buceamos?</button></div>`).join('')}</div>
      <h2>Grupos</h2><div class="tarjeta plana lista">${C.fila('buddies', 'Club de los martes', '5 buddies')}</div></div>` });
  P.reg('b-mi-area', { grupo: GB, titulo: 'Mi área', ref: '§4.5', mod: 'buceador', tab: 'b-mi-area',
    notas: ['Nivel y Puntos, Log Book, Mis puntos, Promociones con su QR, Documentos con aviso de caducidad, Mi ficha y Ajustes.'], web: ['Área del buceador (#/area), Log Book, puntos (Fase 3), promociones, documentos.'],
    html: () => `<div class="cab bati"><div class="fila"><div class="avatar" style="width:64px;height:64px;font-size:var(--t-l)">BB</div><div class="crece"><h1 style="font-size:var(--t-l)">Bea Buzo</h1><p class="suave">Advanced Open Water · 64 inmersiones</p></div></div>
      <div class="cifras"><div class="tarjeta cifra"><b>1.240</b><span>puntos</span></div><div class="tarjeta cifra"><b>64</b><span>inmersiones en el Log Book</span></div></div></div>
      <div class="cuerpo"><div class="tarjeta plana lista">${C.fila('libro', 'Log Book', '64 inmersiones · la última, Isla del Portitxol', 'data-go="b-logbook"')}${C.fila('puntos', 'Mis puntos', '1.240 puntos · cómo se ganan')}${C.fila('regalo', 'Promociones', '2 activas, con su QR')}
      ${C.fila('documento', 'Documentos', '<span class="tag pend">' + ic('reloj', '') + 'El seguro caduca en 32 días</span>', 'data-go="b-documentos"')}${C.fila('ficha', 'Mi ficha', 'Titulación, tallas, teléfono y WhatsApp', 'data-go="b-mi-ficha"')}${C.fila('ajustes', 'Ajustes', 'Tema, tamaño de texto, idioma, avisos', 'data-go="ajustes"')}</div></div>` });
  P.reg('b-logbook', { grupo: GB, titulo: 'Log Book', ref: '§4.5', mod: 'buceador', tab: 'b-mi-area', notas: ['Cifras y entradas; disponible sin conexión.'], web: ['Log Book de la web.'],
    html: () => `<div class="cuerpo">${C.volver('b-mi-area', 'Mi área')}<h1>Log Book</h1><div class="cifras"><div class="tarjeta cifra"><b>64</b><span>inmersiones</span></div><div class="tarjeta cifra"><b>31 m</b><span>profundidad máxima</span></div><div class="tarjeta cifra"><b>48 h</b><span>bajo el agua</span></div><div class="tarjeta cifra"><b>12</b><span>puntos distintos</span></div></div>
      <div class="tarjeta plana lista">${[['Isla del Portitxol', fCorta(dia(-20)) + ' · 18 m · 46 min'], ['Cabo de San Antonio', fCorta(dia(-34)) + ' · 22 m · 41 min'], ['Cala Granadella', fCorta(dia(-60)) + ' · 12 m · 55 min']].map(([t, s2]) => C.fila('ola2', t, esc(s2))).join('')}</div>
      <button class="btn sec ancho">${ic('mas1', '')}Añadir inmersión</button></div>` });
  P.reg('b-documentos', { grupo: GB, titulo: 'Documentos', ref: '§4.5', mod: 'buceador', tab: 'b-mi-area', notas: ['Aviso de caducidad con color, icono y texto.'], web: ['Documentos del perfil (titulación, seguro) y descargos firmados (v50.40).'],
    html: () => `<div class="cuerpo">${C.volver('b-mi-area', 'Mi área')}<h1>Documentos</h1><div class="tarjeta plana lista">
      <div class="lista-fila">${ic('ficha')}<div class="crece"><b>Titulación</b><p class="suave peq">Advanced Open Water · PADI</p></div>${C.tag('ok', 'Comprobada')}</div>
      <div class="lista-fila">${ic('documento')}<div class="crece"><b>Seguro de buceo</b><p class="suave peq">Hasta el ${fCorta(dia(32))}</p></div>${C.tag('pend', 'Caduca en 32 días')}</div>
      <div class="lista-fila">${ic('lapiz')}<div class="crece"><b>Descargo firmado</b><p class="suave peq">${esc(D.centro.nombre)} · versión 3</p></div>${C.tag('ok', 'Firmado')}</div></div>
      <button class="btn sec ancho">${ic('camara', '')}Subir documento</button></div>` });
  P.reg('b-mi-ficha', { grupo: GB, titulo: 'Mi ficha', ref: '§4.5', mod: 'buceador', tab: 'b-mi-area',
    notas: ['Lo que rellena sola la reserva: titulación, inmersiones, tallas, equipo, teléfono con prefijo y permiso de WhatsApp.'], web: ['Perfil del buceador: tallas (traje, escarpines, chaleco, aletas, máscara), lastre, equipo, contacto de emergencia, teléfono E.164 y permiso de WhatsApp (v50.47).'],
    html: () => `<div class="cuerpo">${C.volver('b-mi-area', 'Mi área')}<h1>Mi ficha</h1>
      <section class="tarjeta pad pila-8"><h2>Buceo</h2><dl class="datos"><div><dt>Titulación</dt><dd>Advanced Open Water</dd></div><div><dt>Inmersiones</dt><dd>64</dd></div><div><dt>Lastre habitual</dt><dd>6 kg</dd></div><div><dt>Equipo propio</dt><dd>Ordenador y máscara</dd></div></dl></section>
      <section class="tarjeta pad pila-8"><h2>Tallas</h2><dl class="datos"><div><dt>Traje</dt><dd>M · 5 mm</dd></div><div><dt>Escarpines</dt><dd>42</dd></div><div><dt>Chaleco</dt><dd>M</dd></div><div><dt>Aletas</dt><dd>42–43</dd></div></dl></section>
      <section class="tarjeta pad pila-8"><h2>Contacto</h2><div class="campo"><label for="tf">Teléfono</label><input id="tf" value="+34 600 000 102" inputmode="tel"></div>
      <label class="interruptor"><span>Los centros con los que reservo pueden escribirme por WhatsApp</span><input type="checkbox" checked></label>
      <dl class="datos"><div><dt>Contacto de emergencia</dt><dd>Carlos Pruebas</dd></div><div><dt>Su teléfono</dt><dd>+34 600 000 999</dd></div></dl></section></div>` });
})();
