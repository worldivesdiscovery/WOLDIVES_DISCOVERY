/* Screens: Centro · WORLDIVES PRO. Sample data only. */
(function () {
  'use strict';
  const { D, C, ic, esc, dia, fCorta, fLarga, eur, MANANA } = P;
  const G = 'Centro PRO';
  const libres = (s) => s.total - s.ocup - s.pend;
  const pagoTag = (p) => p === 'ok' ? C.tag('ok', 'Pagado') : p === 'pend' ? C.tag('pend', 'Pendiente de pago') : `<span class="tag neutro">${ic('euro', '')}Paga en el centro</span>`;

  const cabecera = (rol = 'Dueña') => `<header class="cab bati"><div class="cab-fila"><img src="${D.centro.logo}" alt="" class="logo-centro"><div class="crece"><button class="selector-perfil" data-hoja="selector" aria-label="Cambiar de perfil"><img src="${D.centro.logo}" alt=""><span>${esc(D.centro.nombre)} · ${rol}</span>${ic('chevabajo', '')}</button></div></div>
    <div class="fila-entre"><h1 style="font-size:var(--t-l)">Hoy, ${fLarga(dia(0))}</h1></div>${C.mar()}</header>`;
  const tarjetaSalidaCentro = (s) => {
    const etiquetas = s.id === 's2' ? ['Alquilan equipo: 3', 'Nitrox: 2', 'Paga en el centro: 1', 'Busca compañero: 2'] : s.id === 's1' ? ['Alquilan equipo: 2', 'Nitrox: 3'] : ['Sin titulación', 'Equipo incluido'];
    return `<article class="tarjeta salida" data-go="c-salida" role="button" tabindex="0" aria-label="Salida de las ${s.hora}: ${esc(s.titulo)}"><div class="hora">${s.hora}<small>${s.barco === 'Desde la costa' ? 'costa' : 'barco'}</small></div>
      <div class="pila-8"><div class="fila-entre"><b>${esc(s.titulo)}</b><span class="num peq" style="font-weight:700">${s.ocup + s.pend}/${s.total}</span></div>
      <p class="suave peq">${esc(s.punto)} · ${esc(s.barco)} · ${esc(s.instr)}</p>${C.asientos(s.total, s.ocup, s.pend)}
      <div class="tags">${etiquetas.map((t) => `<span class="tag neutro">${esc(t)}</span>`).join('')}${s.pend ? C.tag('pend', s.pend + ' sin pagar') : ''}</div></div></article>`;
  };
  const leyendaAsientos = `<div class="leyenda"><span><i class="ok"></i>Pagado</span><span><i class="pend"></i>Pendiente de pago</span><span><i></i>Libre</span></div>`;

  /* ---------- Hoy ---------- */
  const hoy = (manana) => cabecera() + `<div class="cuerpo">
    <div class="cifras"><div class="tarjeta cifra"><b>${D.salidas.reduce((n, s) => n + s.ocup + s.pend, 0)}</b><span>buceadores hoy</span></div><div class="tarjeta cifra"><b>${D.salidas.reduce((n, s) => n + libres(s), 0)}</b><span>plazas libres</span></div>
    <button class="tarjeta cifra alerta" data-go="c-solicitudes" style="text-align:left;cursor:pointer"><b>6</b><span>pendientes · 3 solicitudes y 3 pagos</span></button><button class="tarjeta cifra" data-go="c-cobros" style="text-align:left;cursor:pointer"><b>1.240 €</b><span>cobrado hoy</span></button></div>
    <div class="aviso urg" role="alert">${ic('alerta', '')}<span class="crece"><b>1 solicitud caduca en menos de 3 h</b> y 2 pagos vencen a las 8:30.</span><button class="btn" data-go="c-solicitudes">Ver</button></div>
    <section class="pila-8"><div class="seccion-cab"><h2>Salidas de hoy</h2>${C.anillo(.74, '74 %', 'lleno')}</div>${leyendaAsientos}${D.salidas.map(tarjetaSalidaCentro).join('')}</section>
    <section class="tarjeta">${manana ? `<div class="pad pila-8" style="padding:14px"><div class="fila-entre"><h2>Mañana, ${fLarga(dia(1))}</h2><button class="btn texto" data-go="c-hoy">Plegar</button></div>
      ${[['08:30', 'Doble inmersión en barco', 'Cabo Negro', 8, 10, 1], ['09:00', 'Inmersión simple en barco', 'Isla del Portitxol', 6, 10, 1], ['16:00', 'Bautizo de buceo', 'Cala Granadella', 4, 6, 0]].map(([h, t, p, o, tot, pe]) =>
        `<div class="fila" style="padding:6px 0"><b class="num" style="width:52px">${h}</b><div class="crece"><p style="font-weight:600">${t}</p><p class="suave peq">${p} · ${o}/${tot}</p></div>${pe ? C.tag('pend', pe + ' sin pagar') : C.tag('ok', 'Todo pagado')}</div>`).join('')}</div>`
      : `<button class="lista-fila" data-go="c-hoy-manana">${ic('agenda')}<span class="crece"><b>Mañana:</b> ${MANANA.salidas} salidas · ${MANANA.buceadores} buceadores · ${MANANA.pend} pendientes de pago</span>${ic('chevabajo', 'chev')}</button>`}</section>
    <button class="btn sec ancho" data-go="c-agenda-semana">${ic('agenda', '')}Ver semana</button></div>`;
  P.reg('c-hoy', { grupo: G, titulo: 'Hoy (pantalla de inicio)', ref: '§5.1', mod: 'centro', tab: 'c-hoy',
    notas: ['0 toques: al abrir, el día completo en una pantalla (promesa: ≤ 5 s).', 'Cabecera con logo, fecha y franja del mar (agua, viento, ola; sin visibilidad).', '4 cifras grandes; aviso de lo urgente solo si lo hay.', 'Salidas por hora con las plazas dibujadas como asientos: verde pagado, naranja pendiente, blanco libre.', 'Mañana plegado en una línea; «Ver semana».', 'Indicador circular solo aquí (ocupación del día).'],
    web: ['Planning del centro (motor de agenda v50.44), manifiesto y pagos (v50.40–v50.42), solicitudes (Fase 1B), selector de perfil con contexto de centro (v50.47).'],
    falta: ['Condiciones del mar: la web no las tiene. Decidido: boyas de Puertos del Estado (doc. 02). En el prototipo son de ejemplo.'],
    html: () => hoy(false) });
  P.reg('c-hoy-manana', { grupo: G, titulo: 'Hoy con Mañana desplegado', ref: '§5.1.5', mod: 'centro', tab: 'c-hoy', notas: ['Un toque despliega mañana: salidas, ocupación y pendientes de pago.'], html: () => hoy(true),
    init: (r) => { const m = r.querySelector('.tarjeta .pad'); if (m) setTimeout(() => m.scrollIntoView({ block: 'center' }), 30); } });
  P.reg('c-selector', { grupo: G, titulo: 'Selector de perfil', ref: '§3.1', mod: 'centro', tab: 'c-hoy', notas: ['Una cuenta con varios roles cambia con un toque. Al cambiar de centro, la sesión cambia de contexto (encargo de aislamiento).'],
    web: ['Contexto de centro explícito en la sesión (v50.47).'], html: () => hoy(false), hoja: 'selector' });

  /* ---------- Agenda ---------- */
  const segAgenda = (act) => `<div class="seg" role="group" aria-label="Vista">${[['Mes', 'c-agenda-mes'], ['Semana', 'c-agenda-semana'], ['Día', 'c-agenda-dia'], ['Recursos', 'c-agenda-recursos']].map(([t, id]) => `<button aria-pressed="${t === act}" data-go="${id}">${t}</button>`).join('')}</div>`;
  const cabAgenda = (act, titulo) => `<div class="cuerpo" style="padding-bottom:0"><div class="fila-entre"><h1>Agenda</h1><button class="btn sec" style="min-height:44px">Hoy</button></div>${segAgenda(act)}
    <div class="fila-entre"><button class="btn texto" aria-label="Anterior">${ic('atras', '')}</button><h2>${titulo}</h2><button class="btn texto" aria-label="Siguiente">${ic('chev', '')}</button></div></div>`;
  const ocupMes = { 1: 1, 2: 2, 3: 2, 5: 3, 6: 4, 7: 2, 8: 3, 9: 4, 10: 5, 11: 5, 12: 3, 13: 4, 14: 3, 15: 3, 16: 2, 17: 4, 18: 5, 19: 2, 20: 1, 21: 2, 22: 3, 23: 2, 24: 4, 25: 3, 26: 1, 27: 2, 28: 1, 29: 1, 30: 2, 31: 3 };
  const mesHTML = (opts = {}) => {
    let h = ['L', 'M', 'X', 'J', 'V', 'S', 'D'].map((d) => `<div class="dsem">${d}</div>`).join('') + '<div></div><div></div><div></div>';
    for (let d = 1; d <= 31; d++) {
      const p = opts.freelance ? (opts.freelance[d] || 0) : (ocupMes[d] || 0); const bloq = opts.bloq && opts.bloq.includes(d); const medio = opts.medio && opts.medio.includes(d);
      const curso = !opts.freelance && [16, 17, 18].includes(d);
      h += `<button class="dia${d === 13 ? ' hoy' : ''}${bloq ? ' bloqueado' : ''}${medio ? ' medio' : ''}" ${bloq || medio ? '' : `data-p="${p}"`} ${opts.hoja ? `data-hoja="${opts.hoja}" data-arg="${d}"` : ''} aria-label="${d} de octubre${bloq ? ', bloqueado' : medio ? ', medio día ocupado' : ''}">${d}
        <span class="puntos">${p && !bloq ? '<i></i>'.repeat(Math.min(3, Math.ceil(p / 2))) : ''}${curso ? '<i class="curso"></i>' : ''}${bloq ? '<i class="bloq"></i>' : ''}</span></button>`;
    }
    return `<div class="mes" id="mes">${h}</div>`;
  };
  const oscuro = () => P.s.tema === 'futurista' || (P.s.tema === 'auto' && window.matchMedia && matchMedia('(prefers-color-scheme: dark)').matches);
  const escala = (t = oscuro() ? 'Más intenso = más lleno' : 'Más oscuro = más lleno') => `<div class="escala-prof" aria-label="Escala de ocupación">${['Sin salidas', '', '', '', '', 'Lleno'].map((t2, i) => `<i style="background:${i ? `var(--p${i})` : 'var(--sup)'}"></i>${t2 ? `<span>${t2}</span>` : ''}`).join('')}<span class="crece" style="text-align:right">${t}</span></div>`;
  const cursoBarras = (root) => { const mes = root.querySelector('#mes'); if (!mes) return; const cells = mes.querySelectorAll('.dia'); const a = cells[15], b = cells[17]; if (!a || !b) return;
    const bar = document.createElement('span'); bar.className = 'barra-curso'; bar.setAttribute('aria-hidden', 'true');
    bar.style.left = a.offsetLeft + 4 + 'px'; bar.style.width = (b.offsetLeft + b.offsetWidth - a.offsetLeft - 8) + 'px'; bar.style.top = (a.offsetTop + a.offsetHeight - 13) + 'px'; mes.appendChild(bar); };
  const notasAgenda = ['Una sola pantalla con Mes · Semana · Día (y Recursos si hay más de un barco o instructor) y botón Hoy.', 'Muy visual y con poco texto.'];
  const webAgenda = ['Motor de agenda común (v50.44): salidas, cursos de varios días, bloqueos, barcos e instructores (/api/agenda, /api/manifest).'];
  P.reg('c-agenda-mes', { grupo: G, titulo: 'Agenda · mes', ref: '§5.2.1', mod: 'centro', tab: 'c-agenda',
    notas: [...notasAgenda, 'Cada día coloreado por ocupación como una carta de profundidad (más oscuro = más lleno), con puntitos por tipo.', 'Cursos de varios días como barras que cruzan los días.', 'Tocar un día abre una hoja con sus salidas, «+ Salida» y «Cartel de plazas libres».'], web: webAgenda,
    html: () => cabAgenda('Mes', 'Octubre 2026') + `<div class="cuerpo"><div class="cifras"><div class="tarjeta cifra"><b>62</b><span>salidas</span></div><div class="tarjeta cifra"><b>418</b><span>buceadores</span></div><div class="tarjeta cifra"><b>68 %</b><span>ocupación media</span></div><div class="tarjeta cifra"><b>18.240 €</b><span>cobrado</span></div></div>
      ${mesHTML({ hoja: 'diaagenda' })}${escala()}<div class="leyenda"><span><i style="border-radius:50%;width:8px;height:8px;background:var(--texto)"></i>Salida</span><span><i style="background:var(--pend-s);border-color:var(--pend-s);height:7px"></i>Curso de varios días</span><span><i style="background:repeating-linear-gradient(135deg,var(--sup2) 0 3px,var(--sup) 3px 6px)"></i>Bloqueado</span></div></div>`,
    init: cursoBarras });
  P.reg('c-agenda-mes-dia', { grupo: G, titulo: 'Agenda · hoja del día', ref: '§5.2.1', mod: 'centro', tab: 'c-agenda', notas: ['Sus salidas, «+ Salida» y «Cartel de plazas libres».'], web: webAgenda,
    html: () => P.screens['c-agenda-mes'].html(), init: cursoBarras, hoja: 'diaagenda', hojaArg: '15' });
  P.hojas.diaagenda = (d) => ({ titulo: `${fLarga(dia((+d || 15) - 13))}`, sub: '3 salidas · 21 de 26 plazas · 2 pendientes de pago',
    html: `<div class="tarjeta plana lista">${[['08:30', 'Doble inmersión en barco', 'Cabo Negro · Neptuno', '9/10'], ['09:00', 'Curso Open Water · día 1 de 3', 'Piscina y teoría · Iván', '3/4'], ['16:00', 'Bautizo de buceo', 'Cala Granadella · costa', '5/6']].map(([h, t, s2, o]) => `<div class="salida" data-go="c-salida"><div class="hora">${h}</div><div class="pila"><b>${t}</b><span class="suave peq">${s2} · ${o}</span></div></div>`).join('')}</div>`,
    pie: `<div class="btn-fila"><button class="btn" data-go="c-crear-salida">${ic('mas1', '')}Salida</button><button class="btn sec" data-go="c-cartel">${ic('cartel', '')}Cartel de plazas</button></div>` });
  P.reg('c-agenda-semana', { grupo: G, titulo: 'Agenda · semana', ref: '§5.2.2', mod: 'centro', tab: 'c-agenda',
    notas: ['En vertical, una fila por día con mini-barras de sus salidas (hora + ocupadas/total) y el total de buceadores.', 'Deslizar cambia de semana; también hay flechas visibles.'], web: webAgenda,
    html: () => cabAgenda('Semana', `${fCorta(dia(-1))} – ${fCorta(dia(5))}`) + `<div class="cuerpo"><div class="tarjeta plana lista">${[-1, 0, 1, 2, 3, 4, 5].map((n) => {
      const sal = n === 3 ? [] : [['08:30', 6 + (n + 7) % 4, 10], ['09:00', 4 + (n + 9) % 6, 10], ['16:00', 2 + (n + 7) % 4, 6]].slice(0, n === 5 ? 2 : 3);
      const tot = sal.reduce((a, s) => a + s[1], 0);
      return `<div class="semana-dia" ${n === 0 ? 'style="background:var(--acento-suave)"' : ''}><div class="nd">${dia(n).getDate()}<small>${P.fCorta(dia(n)).slice(0, 3)}</small></div>
        <div class="mini-barras">${sal.length ? sal.map(([h, o, t]) => `<div class="mini-barra"><span>${h}</span><span class="pista"><i style="width:${o / t * 100}%"></i></span><span>${o}/${t}</span></div>`).join('') : '<span class="suave peq">Cerrado · bloqueo del centro</span>'}${n === 2 ? '<div class="mini-barra"><span>Curso</span><span class="pista"><i class="curso" style="width:75%"></i></span><span>3/4</span></div>' : ''}</div>
        <div class="centrado"><b class="num">${tot}</b><br><span class="suave" style="font-size:12px">buc.</span></div></div>`; }).join('')}</div>
      <p class="suave peq centrado">${ic('girar', '')} Gira el móvil para ver la cuadrícula de días y horas.</p></div>` });
  P.reg('c-agenda-semana-h', { grupo: G, titulo: 'Agenda · semana en horizontal', ref: '§5.2.2', mod: 'centro', tab: 'c-agenda', apaisado: true, sinTabs: true,
    notas: ['Con el móvil en horizontal: cuadrícula de días × horas con los bloques.'], web: webAgenda,
    html: () => { const dias = [-1, 0, 1, 2, 3, 4, 5]; const horas = ['08:00', '10:00', '12:00', '14:00', '16:00', '18:00'];
      const bloque = (d, h, t, o, cls = '') => `<div class="lt-bloque ${cls}" style="top:${h * 30 + 2}px;height:${cls ? 120 : 52}px"><b>${t}</b>${o}</div>`;
      return `<div style="display:grid;grid-template-columns:56px repeat(7,minmax(0,1fr));gap:0 4px;padding:6px 12px 0"><div></div>${dias.map((n) => `<div class="centrado peq" style="font-weight:600;${n === 0 ? 'color:var(--acento)' : ''}">${P.fCorta(dia(n)).slice(0, 6)}</div>`).join('')}
        <div style="display:grid">${horas.map((h) => `<div class="lt-hora" style="height:60px">${h}</div>`).join('')}</div>
        ${dias.map((n) => `<div style="position:relative;border-left:1px solid var(--linea)">${horas.map(() => '<div class="lt-hueco" style="height:60px"></div>').join('')}${n === 3 ? '' : bloque(n, 1, '08:30', ` ${6 + (n + 7) % 4}/10`) + bloque(n, 2.2, '09:00', ` ${4 + (n + 9) % 6}/10`) + bloque(n, 8, '16:00', ` ${2 + (n + 7) % 4}/6`)}${n === 2 ? bloque(n, 4.2, 'Curso', ' 3/4', 'curso') : ''}</div>`).join('')}</div>`; } });
  P.reg('c-agenda-dia', { grupo: G, titulo: 'Agenda · día', ref: '§5.2.3', mod: 'centro', tab: 'c-agenda',
    notas: ['Línea de tiempo con salidas y sesiones de curso como bloques (barco, instructor, plazas).', 'Filtro por barco o instructor con chips.', 'Tocar un hueco libre crea una salida a esa hora con el recurso ya puesto.'], web: webAgenda,
    html: () => cabAgenda('Día', 'Hoy, ' + fCorta(dia(0))) + `<div class="cuerpo"><div class="chips">${['Todo', 'Neptuno', 'Costa', 'Iván', 'Ana'].map((t, i) => `<button class="chip" aria-pressed="${i === 0}">${t}</button>`).join('')}</div>
      <div class="linea-tiempo"><div>${['08:00', '09:00', '10:00', '11:00', '12:00', '13:00', '14:00', '15:00', '16:00', '17:00'].map((h) => `<div class="lt-hora">${h}</div>`).join('')}</div>
      <div style="position:relative">${Array.from({ length: 10 }, (_, i) => `<div class="lt-hueco" data-go="c-crear-salida" aria-label="Crear salida a las ${8 + i}:00"></div>`).join('')}
      <div class="lt-bloque" style="top:34px;height:250px;right:52%" data-go="c-salida"><b>08:30 Doble inmersión</b>Neptuno · Iván<br>8/10</div>
      <div class="lt-bloque" style="top:66px;height:120px;left:50%" data-go="c-salida"><b>09:00 Simple</b>Neptuno · Iván<br>8/10</div>
      <div class="lt-bloque curso" style="top:322px;height:120px;left:50%"><b>Curso OW · día 2</b>Piscina · Ana · 3/4</div>
      <div class="lt-bloque" style="top:514px;height:120px" data-go="c-salida"><b>16:00 Bautizo de buceo</b>Costa · Ana · 3/6</div></div></div></div>` });
  P.reg('c-agenda-recursos', { grupo: G, titulo: 'Agenda · recursos', ref: '§5.2.4', mod: 'centro', tab: 'c-agenda',
    notas: ['Barcos e instructores × días, del motor de reservas. Solo aparece si el centro tiene más de un barco o instructor.'], web: webAgenda,
    falta: ['Segundo barco e instructores: la demo tiene un barco (Neptuno) y un instructor (Iván). Ana y «Costa» son de ejemplo.'],
    html: () => cabAgenda('Recursos', `${fCorta(dia(-1))} – ${fCorta(dia(5))}`) + `<div class="cuerpo"><div style="overflow-x:auto"><div class="recursos" style="min-width:340px"><div></div>${[-1, 0, 1, 2, 3, 4, 5].map((n) => `<div class="suave" style="font-weight:600">${dia(n).getDate()}</div>`).join('')}
      ${[['Neptuno', ['8/10', '8/10', '7/10', '9/10', '', '10/10', '6/10']], ['Costa', ['3/6', '3/6', '', '5/6', '', '2/6', '']], ['Iván', ['2', '2', '2', '1', '', '2', '1']], ['Ana', ['1', 'Curso', 'Curso', 'Curso', '', '1', '']]].map(([r, v]) =>
        `<div class="rnombre">${r}</div>${v.map((x) => `<div class="${x === 'Curso' ? 'curso' : x ? 'ocupado' : 'libre'}">${x || 'libre'}</div>`).join('')}`).join('')}</div></div>
      <p class="suave peq">Barcos: plazas ocupadas/total. Personas: número de salidas o curso.</p></div>` });
  P.reg('c-crear-salida', { grupo: G, titulo: 'Crear salida con plantilla', ref: '§5.2.5', mod: 'centro', tab: 'c-agenda',
    notas: ['Plantilla → fecha y hora → barco → guardar (≤ 30 s, ≤ 6 toques).', 'Repetir cada semana con un toque.'], web: ['Servicios y salidas (/api/provider-services/slot).'],
    html: () => P.screens['c-agenda-dia'].html(), hoja: 'crearsalida' });
  P.hojas.crearsalida = () => ({ titulo: 'Nueva salida', sub: 'Desde una plantilla de tus servicios', alto: '84%',
    html: `<section class="pila-8"><p class="eti">1 · Plantilla</p><div class="pila-8">${[['Inmersión simple en barco', '45 € · 10 plazas · pago al reservar', true], ['Doble inmersión en barco', '75 € · 10 plazas · bajo petición', false], ['Bautizo de buceo', '60 € · 6 plazas', false]].map(([t, s2, on]) =>
      `<button class="lista-fila tarjeta plana" style="${on ? 'border:2px solid var(--acento)' : ''}"><span class="crece"><b>${t}</b><br><span class="suave peq">${s2}</span></span>${on ? ic('check') : ''}</button>`).join('')}</div></section>
      <section class="pila-8"><p class="eti">2 · Fecha y hora</p><div class="btn-fila"><div class="campo"><label for="nf">Fecha</label><input id="nf" value="${fCorta(dia(0))}"></div><div class="campo"><label for="nh">Hora</label><input id="nh" value="11:00"></div></div></section>
      <section class="pila-8"><p class="eti">3 · Barco</p><div class="chips"><button class="chip" aria-pressed="true">${ic('barco', '')}Neptuno · 12</button><button class="chip" aria-pressed="false">Desde la costa</button></div></section>
      <label class="interruptor"><span>Repetir cada semana</span><input type="checkbox"></label>`,
    pie: '<button class="btn ancho grande" data-accion="guardasalida">Guardar salida</button>' });
  P.acc.guardasalida = () => { P.cerrarHoja(); P.toast('Salida creada: hoy 11:00 · Neptuno'); };

  /* ---------- Requests and pending payments ---------- */
  const tarjetaSolicitud = (r, sel) => {
    const horas = r.resta, cls = horas < 3 ? 'urg' : horas < 12 ? 'pend' : '';
    const txt = horas < 1 ? Math.round(horas * 60) + ' min' : Math.floor(horas) + ' h';
    return `<article class="tarjeta solicitud"><div class="fila"><button class="check-sel" role="checkbox" aria-checked="${!!sel}" aria-label="Seleccionar">${sel ? ic('check', '') : ''}</button><div class="avatar">${r.c}</div>
      <div class="crece pila"><b>${esc(r.quien)}</b><span class="suave peq">${esc(r.nivel)}</span></div>${C.anillo(1 - horas / r.total, txt, 'quedan', cls)}</div>
      <div class="pila"><p style="font-weight:600">${esc(r.act)}</p><p class="peq num">${esc(r.cuando)} · ${r.pers} ${r.pers === 1 ? 'persona' : 'personas'} · ${eur(r.importe)}</p><p class="suave peq">${esc(r.eq)}</p></div>
      <div class="btn-fila"><button class="btn peligro" data-hoja="rechazar" data-arg="${r.id}">${ic('x', '')}Rechazar</button><button class="btn ok" data-hoja="aceptar" data-arg="${r.id}">${ic('check', '')}Aceptar</button></div>
      <button class="btn texto" data-go="c-ofrecer">Sin plazas: ofrecer otra salida</button></article>`;
  };
  const segSol = (act) => `<div class="seg"><button aria-pressed="${act === 's'}" data-go="c-solicitudes">Solicitudes · 3</button><button aria-pressed="${act === 'p'}" data-go="c-pendientes">Pendientes de pago · 3</button></div>`;
  const notasSol = ['Cuenta atrás circular: rojo con menos de 3 h, ámbar con menos de 12 h.', 'Aceptar o rechazar con 1 toque + confirmar; motivo opcional en chips.', 'Aceptar varias a la vez.'];
  const webSol = ['Solicitudes «Bajo petición» con plazo (Fase 1B) y estados de la reserva (docs/estados-reserva.md).'];
  P.reg('c-solicitudes', { grupo: G, titulo: 'Solicitudes', ref: '§5.3', mod: 'centro', tab: 'c-solicitudes', notas: notasSol, web: webSol,
    html: () => `<div class="cuerpo"><h1>Solicitudes</h1>${segSol('s')}<div class="fila-entre"><span class="suave peq">1 seleccionada</span><button class="btn sec" style="min-height:44px" data-accion="aceptarvarias">${ic('check', '')}Aceptar seleccionadas</button></div>
      ${D.solicitudes.map((r, i) => tarjetaSolicitud(r, i === 1)).join('')}</div>` });
  P.hojas.aceptar = (id) => { const r = D.solicitudes.find((x) => x.id === id) || D.solicitudes[0]; return { titulo: `¿Aceptar a ${r.quien}?`, sub: `${esc(r.act)} · ${esc(r.cuando)}`,
    html: `<div class="aviso neutro">${ic('info', '')}<span>Le llega el aviso para pagar ${eur(r.importe)} en las próximas 12 h. Si no paga, la plaza vuelve a quedar libre.</span></div>`,
    pie: `<button class="btn ok ancho grande" data-accion="aceptada">${ic('check', '')}Aceptar</button><button class="btn sec ancho" data-cerrar>Volver</button>` }; };
  P.acc.aceptada = () => { P.cerrarHoja(); P.toast('Aceptada. Erik recibe el aviso para pagar.', { deshacer: () => P.toast('Deshecho'), segundos: 10 }); };
  P.acc.aceptarvarias = () => P.toast('1 solicitud aceptada', { deshacer: () => P.toast('Deshecho'), segundos: 10 });
  P.hojas.rechazar = (id) => { const r = D.solicitudes.find((x) => x.id === id) || D.solicitudes[0]; return { titulo: `Rechazar a ${r.quien}`, sub: 'El motivo es opcional. Se le envía en su idioma.',
    html: `<div class="tags">${['Sin plazas', 'Nivel insuficiente', 'Mal tiempo previsto', 'Otro'].map((t, i) => `<button class="chip" aria-pressed="${i === 0}">${t}</button>`).join('')}</div>
      <div class="campo"><label for="nm">Nota (opcional)</label><textarea id="nm">Ese día vamos completos. ¿Te va bien el jueves a la misma hora?</textarea></div>`,
    pie: '<button class="btn peligro ancho grande" data-accion="rechazada">Rechazar</button><button class="btn texto ancho" data-go="c-ofrecer">Mejor, ofrecer otra salida</button>' }; };
  P.acc.rechazada = () => { P.cerrarHoja(); P.toast('Rechazada y avisada', { deshacer: () => P.toast('Deshecho'), segundos: 10 }); };
  P.reg('c-solicitudes-rechazar', { grupo: G, titulo: 'Rechazar con motivo', ref: '§5.3', mod: 'centro', tab: 'c-solicitudes', notas: ['Motivo opcional en chips y nota.'], web: webSol,
    html: () => P.screens['c-solicitudes'].html(), hoja: 'rechazar', hojaArg: 'r1' });
  P.reg('c-ofrecer', { grupo: G, titulo: 'Ofrecer otra salida', ref: '§5.3', mod: 'centro', tab: 'c-solicitudes',
    notas: ['Sin plazas: se propone otra salida con plazas; el buceador acepta desde el aviso.'], web: ['Cambio de fecha y lista de espera (v50.41).'],
    falta: ['«Ofrecer otra salida» como propuesta que el buceador acepta: la web tiene cambio de fecha y lista de espera; comprobar en paridad si cubre esto.'],
    html: () => P.screens['c-solicitudes'].html(), hoja: 'ofrecer' });
  P.hojas.ofrecer = () => ({ titulo: 'Ofrecer otra salida a Erik', sub: 'Doble inmersión · 2 personas', html: `<div class="pila-8">${[[2, '08:30', 'Cabo Negro', 0], [3, '08:30', 'Cabo de San Antonio', 4], [4, '08:30', 'Cap Prim', 6]].map(([n, h, p, l]) =>
    `<button class="lista-fila tarjeta plana" ${l ? '' : 'disabled'} style="${n === 3 ? 'border:2px solid var(--acento)' : ''}"><span class="crece"><b class="num">${fCorta(dia(n))} · ${h}</b><br><span class="suave peq">${p} · ${l ? l + ' plazas' : 'completa'}</span></span>${n === 3 ? ic('check') : ''}</button>`).join('')}</div>`,
    pie: '<button class="btn ancho grande" data-accion="ofrecida">Enviar propuesta</button>' });
  P.acc.ofrecida = () => { P.cerrarHoja(); P.toast('Propuesta enviada a Erik'); };
  P.reg('c-pendientes', { grupo: G, titulo: 'Pendientes de pago', ref: '§5.3', mod: 'centro', tab: 'c-solicitudes',
    notas: ['Reservas aceptadas que no han pagado, con el plazo.', '«Recordar por WhatsApp» y «Cobrar en el centro».'], web: ['Pagos pendientes y cobro en el centro (Fase 2).'],
    html: () => `<div class="cuerpo"><h1>Solicitudes</h1>${segSol('p')}${D.pendientes.map((p) => `<article class="tarjeta pad pila-8"><div class="fila"><div class="avatar">${p.c}</div><div class="crece"><b>${esc(p.quien)}</b><p class="suave peq">${esc(p.act)}</p></div><span class="precio">${eur(p.importe)}</span></div>
      <div class="tags">${p.urg ? C.tag('urg', p.plazo) : C.tag('pend', p.plazo)}</div><div class="btn-fila"><button class="btn wa" data-hoja="whatsapp" data-arg="${esc(p.quien)}">${ic('wa', '')}Recordar</button><button class="btn sec">${ic('euro', '')}Cobrar en el centro</button></div></article>`).join('')}</div>` });

  /* ---------- Scanner ---------- */
  const escaner = (tab) => `<div class="cuerpo" style="padding-bottom:0"><h1>Escanear</h1><div class="seg"><button aria-pressed="${tab === 'c'}" data-go="c-escanear">Check-in reserva</button><button aria-pressed="${tab === 'p'}" data-go="c-canjear">Canjear promoción</button></div>
    <div class="escaner"><div class="fondo-cam"></div><div class="visor"><span class="linea-scan"></span></div><div class="linterna"><button>${ic('linterna', '')}Linterna</button></div><p class="txt">${tab === 'c' ? 'Apunta al QR de la reserva' : 'Apunta al QR de la promoción'}</p></div>
    <button class="btn sec ancho">${ic('teclado', '')}Escribir código</button>
    <section class="pila-8"><p class="eti">Solo en el prototipo: simular una lectura</p><div class="tags">${[['Válido', 'c-escaneo-ok'], ['Ya usado', 'c-escaneo-usado'], ['Caducado', 'c-escaneo-caducado'], ['De otro centro', 'c-escaneo-otro'], ['De otra salida', 'c-escaneo-otra-salida'], ['Cámara denegada', 'c-camara-denegada']].map(([t, id]) => `<button class="chip" data-go="${id}">${t}</button>`).join('')}</div></section></div>`;
  const notasEsc = ['Botón central de la barra. Pestañas Check-in reserva y Canjear promoción.', 'Escáner nativo, linterna y «Escribir código». Promesa: ≤ 5 s desde abrir el escáner.'];
  const webEsc = ['Check-in con QR sin conexión (v50.42) y canje de promociones con QR (Fase 3).'];
  P.reg('c-escanear', { grupo: G, titulo: 'Escanear · check-in', ref: '§5.4', mod: 'centro', tab: 'c-escanear', notas: notasEsc, web: webEsc, html: () => escaner('c') });
  P.reg('c-canjear', { grupo: G, titulo: 'Escanear · canjear promoción', ref: '§5.4', mod: 'centro', tab: 'c-escanear', notas: notasEsc, web: webEsc, html: () => escaner('p') });
  P.reg('c-escaneo-ok', { grupo: G, titulo: 'Resultado: reserva válida', ref: '§5.4.2', mod: 'centro', tab: 'c-escanear',
    notas: ['Resultado como una tarjeta de titulación: nivel, agencia, inmersiones, seguro, tallas, equipo y pago.', 'Botón grande «Subir a bordo · check-in» (56 px) y, si falta pagar, «Cobrar en el centro» al lado.'], web: webEsc,
    html: () => { const b = D.buceadores[1]; return `<div class="cuerpo">${C.volver('c-escanear', 'Escanear otro')}<div class="ficha-tit"><div class="cabeza"><div class="avatar">${b.c}</div><div class="crece"><h2>${esc(b.n)}</h2><p class="suave peq">Reserva WOD-000131 · hoy 09:00 · Inmersión simple</p></div></div>
      <dl class="datos"><div><dt>Titulación</dt><dd>${b.nivel} · PADI</dd></div><div><dt>Inmersiones</dt><dd>${b.inm}</dd></div><div><dt>Seguro</dt><dd>Vigente hasta mayo</dd></div><div><dt>Tallas</dt><dd>Traje L · 44 · chaleco L</dd></div><div><dt>Equipo</dt><dd>${b.eq}</dd></div><div><dt>Descargo</dt><dd>Firmado</dd></div></dl>
      <div class="tags">${C.tag('pend', 'Pendiente de pago · 45 €')}${C.tag('neutro', 'Busca compañero')}</div></div>
      <div class="btn-fila"><button class="btn sec grande">${ic('euro', '')}Cobrar en el centro</button><button class="btn ok grande" data-accion="abordo">${ic('check', '')}Subir a bordo</button></div></div>`; } });
  P.acc.abordo = () => P.toast('Check-in hecho: Tom Harris · 8 de 10 a bordo');
  const error = (id, titulo, txt, extra = '') => P.reg(id, { grupo: G, titulo: 'Resultado: ' + titulo.toLowerCase(), ref: '§5.4.3', mod: 'centro', tab: 'c-escanear',
    notas: ['Errores claros, sin revelar datos ajenos.'], web: webEsc, html: () => `<div class="cuerpo">${C.volver('c-escanear', 'Escanear otro')}<div class="aviso urg" role="alert" style="font-size:var(--t-b)">${ic('alerta', '')}<span><b>${titulo}</b><br>${txt}</span></div>${extra}<button class="btn ancho grande" data-go="c-escanear">${ic('escanear', '')}Escanear otro</button></div>` });
  error('c-escaneo-usado', 'QR ya usado', 'Esta reserva ya hizo check-in hoy a las 8:41.', `<p class="suave">Si es un error, búscala en la lista del barco.</p>`);
  error('c-escaneo-caducado', 'QR caducado', 'La reserva era del 2 de octubre.');
  error('c-escaneo-otro', 'Este QR es de otro centro', 'No se muestra ningún dato de esa reserva.');
  error('c-escaneo-otra-salida', 'Esta reserva es para las 16:00', 'Bautizo de buceo · Cala Granadella. Ahora estás en la salida de las 09:00.', '<button class="btn sec ancho">Ir a la salida de las 16:00</button>');
  P.reg('c-camara-denegada', { grupo: G, titulo: 'Escanear sin permiso de cámara', ref: '§11.5', mod: 'centro', tab: 'c-escanear', notas: ['Si se deniega la cámara, se puede escribir el código o marcar en la lista del barco.'],
    html: () => `<div class="cuerpo"><h1>Escanear</h1><div class="aviso pend">${ic('camara', '')}<span><b>La cámara está desactivada para WORLDIVES.</b><br>Actívala en los ajustes del móvil, o escribe el código de la reserva.</span></div>
      <button class="btn ancho grande">Abrir los ajustes del móvil</button><div class="campo"><label for="cod">Código de la reserva</label><input id="cod" placeholder="WOD-000131" autocapitalize="characters"></div><button class="btn sec ancho" data-go="c-escaneo-ok">Buscar</button><button class="btn texto ancho" data-go="c-salida">Marcar en la lista del barco</button></div>` });

  /* ---------- Trip and boat list ---------- */
  P.reg('c-salida', { grupo: G, titulo: 'Salida y lista del barco', ref: '§5.5', mod: 'centro', tab: 'c-hoy',
    notas: ['Cabecera con hora, punto, barco, instructor, plazas y mar.', 'Por buceador: nivel, inmersiones, tallas y equipo, nitrox, pago, check-in y «busca compañero».', 'Acciones de la salida arriba: check-in de todos con QR, añadir buceador, cambiar hora/punto y avisar, cancelar y avisar a todos.'],
    web: ['Manifiesto del barco (v50.40), check-in sin conexión (v50.42), avisos masivos con 10 s para deshacer (v50.47).'],
    html: () => { const s = D.salidas[1]; return `<header class="cab bati">${C.volver('c-hoy', 'Hoy')}<div class="fila-entre"><h1 style="font-size:var(--t-l)">${s.hora} · ${esc(s.titulo)}</h1></div>
      <p class="suave">${esc(s.punto)} · ${esc(s.barco)} · ${esc(s.instr)}</p><div class="fila-entre"><span class="num" style="font-weight:700;font-size:var(--t-m)">${s.ocup + s.pend}/${s.total} plazas</span><span class="peq">${C.tag('ok', '2 a bordo')}</span></div>${C.asientos(s.total, s.ocup, s.pend)}${C.mar()}</header>
      <div class="cuerpo"><div class="acciones">${C.accion('escanear', 'Check-in de todos', 'data-go="c-escanear"')}${C.accion('mas1', 'Añadir buceador', 'data-go="c-nueva-reserva"')}${C.accion('reloj', 'Cambiar hora y avisar')}${C.accion('x', 'Cancelar y avisar', 'data-go="c-cancelar"')}</div>
      <div class="btn-fila"><button class="btn sec" data-go="c-resumen-barco">${ic('documento', '')}Resumen para el barco</button><button class="btn sec" data-go="c-contar">${ic('buddies', '')}Contar a bordo</button></div>
      <div class="tarjeta plana lista">${D.buceadores.map((b) => `<div class="buceador-fila" data-hoja="accionesbuc" data-arg="${esc(b.n)}" role="button" tabindex="0"><span class="marca-check ${b.check ? 'si' : ''}" aria-label="${b.check ? 'Check-in hecho' : 'Sin check-in'}">${b.check ? ic('check', '') : ''}</span>
        <div class="pila"><b>${esc(b.n)}</b><span class="meta">${b.nivel} · ${b.inm} inm. · ${b.tallas} · ${b.eq}${b.nitrox ? ' · Nitrox' : ''}</span><div class="tags">${pagoTag(b.pago)}${b.busca ? C.tag('neutro', 'Busca compañero') : ''}</div></div>${ic('chev', 'chev')}</div>`).join('')}</div></div>`; } });
  P.hojas.accionesbuc = (n) => { const b = D.buceadores.find((x) => x.n === n) || D.buceadores[1]; return { titulo: b.n, sub: `${b.nivel} · ${b.inm} inmersiones · ${b.tallas}`,
    html: `<div class="tags">${pagoTag(b.pago)}${b.check ? C.tag('ok', 'A bordo') : C.tag('neutro', 'Sin check-in')}</div>
      <div class="acciones tres">${C.accion('tel', 'Llamar')}${C.accion('wa', 'WhatsApp', `data-hoja="whatsapp" data-arg="${esc(b.n)}"`, 'wa')}${C.accion('mover', 'Mover a otra salida', 'data-go="c-mover"')}${C.accion('euro', 'Cobrar')}${C.accion('ficha', 'Ver ficha', 'data-go="c-escaneo-ok"')}${C.accion('check', 'Check-in a mano', 'data-accion="abordo"')}</div>` }; };
  P.reg('c-salida-buceador', { grupo: G, titulo: 'Acciones de un buceador', ref: '§5.5.3', mod: 'centro', tab: 'c-hoy', notas: ['Llamar · WhatsApp · Mover a otra salida · Cobrar · Ver ficha.'], web: ['Reserva y contacto del buceador (con reserva en este centro).'],
    html: () => P.screens['c-salida'].html(), hoja: 'accionesbuc', hojaArg: 'Tom Harris' });
  P.reg('c-whatsapp', { grupo: G, titulo: 'WhatsApp con mensaje ya escrito', ref: '§7.1', mod: 'centro', tab: 'c-hoy',
    notas: ['Abre WhatsApp en el móvil del centro con el número del cliente y un mensaje inicial en su idioma (aquí, inglés).', 'Solo para clientes con reserva en este centro; si el número no es válido, no aparece y se ofrece Llamar o el correo.'],
    web: ['Teléfono cifrado y E.164 con permiso de WhatsApp, registro de vistas (v50.47).'], falta: ['Mensajes iniciales en los 9 idiomas: plantillas nuevas (los avisos automáticos ya existen).'],
    html: () => P.screens['c-salida'].html(), hoja: 'whatsapp', hojaArg: 'Tom Harris' });
  P.reg('c-mover', { grupo: G, titulo: 'Mover a otra salida', ref: '§5.5.3', mod: 'centro', tab: 'c-hoy', notas: ['Dos toques: elegir salida con plazas y confirmar. Se avisa al buceador.'], web: ['Cambio de fecha (v50.41).'],
    html: () => P.screens['c-salida'].html(), hoja: 'mover' });
  P.hojas.mover = () => ({ titulo: 'Mover a Tom Harris', sub: 'Elige una salida con plazas. Se le avisa en inglés.', html: `<div class="pila-8">${[[0, '16:00', 'Bautizo de buceo', 'no apta: es para sin titulación', false], [1, '09:00', 'Inmersión simple en barco', '4 plazas', true], [2, '09:00', 'Inmersión simple en barco', '7 plazas', true]].map(([n, h, t, s2, ok], i) =>
    `<button class="lista-fila tarjeta plana" ${ok ? '' : 'disabled style="opacity:.55"'} ${i === 1 ? 'style="border:2px solid var(--acento)"' : ''}><span class="crece"><b class="num">${n ? fCorta(dia(n)) : 'Hoy'} · ${h}</b><br><span class="suave peq">${t} · ${s2}</span></span>${i === 1 ? ic('check') : ''}</button>`).join('')}</div>`,
    pie: '<button class="btn ancho grande" data-accion="movido">Mover y avisar</button>' });
  P.acc.movido = () => { P.cerrarHoja(); P.toast('Movido a mañana 09:00 y avisado', { deshacer: () => P.toast('Deshecho'), segundos: 10 }); };
  P.reg('c-resumen-barco', { grupo: G, titulo: 'Resumen para el barco', ref: '§5.5.5', mod: 'centro', tab: 'c-hoy',
    notas: ['Letra grande, lo esencial: nombres, nivel, tallas, equipo, nitrox y contactos de emergencia si se compartieron.', 'Legible sin conexión y con «Compartir como PDF».'], web: ['Manifiesto en PDF (v50.40) y copia sin conexión (v50.42).'],
    html: () => `<div class="cuerpo">${C.volver('c-salida', 'Salida')}<div class="aviso neutro">${ic('sincon', '')}<span>Guardado en el móvil · se lee sin cobertura · datos de las 9:14</span></div>
      <h1>09:00 · Neptuno · Isla del Portitxol</h1><div class="resumen-barco">${D.buceadores.map((b) => `<div class="rb-fila"><b>${esc(b.n)}</b><span>${b.nivel} · ${b.tallas}</span><span class="suave">${b.eq}${b.nitrox ? ' · NITROX' : ''}</span></div>`).join('')}
      <div class="rb-fila"><b>Emergencias</b><span>Bea Buzo → Carlos Pruebas +34 600 000 999</span></div></div>
      <button class="btn sec ancho grande">${ic('compartir', '')}Compartir como PDF</button></div>` });
  P.reg('c-contar', { grupo: G, titulo: 'Contar a bordo', ref: '§5.5.6', mod: 'centro', tab: 'c-hoy',
    notas: ['Marcar a cada buceador al subir y al volver a bordo, con contador grande.'], falta: ['Pendiente de decisión del titular: ¿se incluye ya o más adelante? La web no lo tiene.'],
    html: () => `<div class="cuerpo">${C.volver('c-salida', 'Salida')}${C.pendiente('¿Se incluye ya «Contar a bordo» o más adelante?')}<div class="seg"><button aria-pressed="false">Al subir</button><button aria-pressed="true">Al volver a bordo</button></div>
      <p class="contar-cifra">5/7</p><p class="centrado suave">a bordo tras la inmersión</p>
      <div class="pila-8">${D.buceadores.map((b, i) => `<button class="contar-btn" aria-pressed="${i < 5}" data-accion="contar">${i < 5 ? ic('check', '') : ic('persona', '')}<span class="crece">${esc(b.n)}</span></button>`).join('')}</div></div>` });
  P.acc.contar = (b) => { b.setAttribute('aria-pressed', b.getAttribute('aria-pressed') === 'true' ? 'false' : 'true'); const n = P.tel().querySelectorAll('.contar-btn[aria-pressed="true"]').length; P.tel().querySelector('.contar-cifra').textContent = `${n}/7`; };
  P.reg('c-cancelar', { grupo: G, titulo: 'Cancelar salida y avisar a todos', ref: '§5.5.4', mod: 'centro', tab: 'c-hoy',
    notas: ['El flujo del encargo de avisos: motivo, escribir la fecha para confirmar y 10 s para deshacer.'], web: ['Avisos masivos por WhatsApp, correo y app (v50.47).'],
    html: () => P.screens['c-salida'].html(), hoja: 'cancelar' });
  P.hojas.cancelar = () => ({ titulo: 'Cancelar la salida de las 09:00', sub: '7 buceadores · se avisa a cada uno en su idioma', alto: '86%',
    html: `<section class="pila-8"><p class="eti">Motivo</p><div class="tags">${['Mal tiempo', 'Estado del mar', 'Avería del barco', 'Otro motivo'].map((t, i) => `<button class="chip" aria-pressed="${i === 0}">${t}</button>`).join('')}</div></section>
      <section class="pila-8"><p class="eti">Qué se ofrece</p><button class="lista-fila tarjeta plana" style="border:2px solid var(--acento)"><span class="crece"><b>Cada uno elige</b> otra fecha o la devolución íntegra</span>${ic('check')}</button><button class="lista-fila tarjeta plana"><span class="crece"><b>Devolver ya a todos</b> desde tu cuenta de Stripe</span></button></section>
      <div class="cifras"><div class="tarjeta cifra"><b>6</b><span>por WhatsApp</span></div><div class="tarjeta cifra"><b>7</b><span>por correo y app</span></div></div>
      <div class="campo"><label for="cf">Para confirmar, escribe la fecha de la salida (13/10)</label><input id="cf" placeholder="dd/mm" inputmode="numeric"></div>`,
    pie: '<button class="btn peligro ancho grande" data-accion="cancelada">Cancelar y avisar a 7</button><p class="suave peq centrado">Tendrás 10 segundos para deshacer antes de que salga nada.</p>' });
  P.acc.cancelada = () => { P.cerrarHoja(); P.toast('Avisando a 7 buceadores', { deshacer: () => P.toast('Deshecho: no ha salido ningún aviso'), segundos: 10 }); };

  /* ---------- Bookings ---------- */
  P.reg('c-reservas', { grupo: G, titulo: 'Reservas', ref: '§5.6', mod: 'centro', tab: 'c-mas',
    notas: ['Lista con buscador (nombre, fecha, estado) y filtros en chips.'], web: ['Reservas del centro con filtros.'],
    html: () => `<div class="cuerpo">${C.volver('c-mas', 'Más')}<div class="fila-entre"><h1>Reservas</h1><button class="btn" style="min-height:44px" data-go="c-nueva-reserva">${ic('mas1', '')}Nueva</button></div>
      <div class="buscador">${ic('buscar', '')}<input aria-label="Buscar reservas" placeholder="Nombre, fecha o código"></div><div class="chips">${['Todas', 'Hoy', 'Pendientes de pago', 'Solicitudes', 'Canceladas'].map((t, i) => `<button class="chip" aria-pressed="${i === 0}">${t}</button>`).join('')}</div>
      <div class="tarjeta plana lista">${[['Tom Harris', 'Inmersión simple · hoy 09:00', 'pend', 'Pendiente de pago'], ['Bea Buzo', 'Doble inmersión · ' + fCorta(dia(2)), 'ok', 'Pagada'], ['Erik Lindqvist', 'Doble inmersión · ' + fCorta(dia(2)), 'sol', 'Solicitud'], ['Hugo Blanco', 'Bautizo · ' + fCorta(dia(-3)), 'canc', 'Cancelada']].map(([n, s2, k, t]) =>
        `<button class="lista-fila" data-go="c-reserva-detalle"><span class="crece pila"><b>${n}</b><span class="suave peq">${s2}</span></span>${C.tag(k, t)}</button>`).join('')}</div></div>` });
  P.reg('c-nueva-reserva', { grupo: G, titulo: 'Nueva reserva manual', ref: '§5.6', mod: 'centro', tab: 'c-mas',
    notas: ['Salida → nombre y teléfono con prefijo → personas → pagado o en el centro → guardar, en ≤ 45 s.', 'Una reserva manual nunca se enlaza a una cuenta ajena sin confirmación (aislamiento).'], web: ['Reserva manual del centro y teléfono E.164 (v50.47).'],
    html: () => P.screens['c-reservas'].html(), hoja: 'nuevares' });
  P.hojas.nuevares = () => ({ titulo: 'Nueva reserva', alto: '88%',
    html: `<div class="campo"><label for="ns">Salida</label><select id="ns"><option>Hoy 09:00 · Inmersión simple · 2 plazas</option><option>Hoy 16:00 · Bautizo · 3 plazas</option></select></div>
      <div class="campo"><label for="nn">Nombre</label><input id="nn" value="Laura Sanz"></div>
      <div class="campo"><label for="nt">Teléfono</label><div class="fila"><select aria-label="Prefijo" style="width:110px;min-height:48px;border-radius:10px;border:1.5px solid var(--linea);background:var(--sup);padding:0 8px"><option>+34 ES</option><option>+33 FR</option></select><input id="nt" class="crece" value="611 222 333" inputmode="tel" style="min-height:48px;border-radius:10px;border:1.5px solid var(--linea);padding:0 12px"></div></div>
      <div class="contador"><span class="crece" style="font-weight:600">Personas</span><button aria-label="Menos">${ic('menos', '')}</button><b>1</b><button aria-label="Más">${ic('mas1', '')}</button></div>
      <div class="seg"><button aria-pressed="false">Ya ha pagado</button><button aria-pressed="true">Pagará en el centro</button></div>
      <div class="aviso neutro">${ic('info', '')}<span>Si este teléfono ya tiene cuenta en WORLDIVES, la reserva no se une a ella hasta que esa persona lo confirme.</span></div>`,
    pie: '<button class="btn ancho grande" data-accion="resguardada">Guardar reserva</button>' });
  P.acc.resguardada = () => { P.cerrarHoja(); P.toast('Reserva guardada: Laura Sanz · hoy 09:00'); };
  P.reg('c-reserva-detalle', { grupo: G, titulo: 'Detalle de reserva', ref: '§5.6', mod: 'centro', tab: 'c-mas',
    notas: ['Llamar, WhatsApp, Mover, Cobrar, Devolver (total o parcial) y Cancelar.'], web: ['Detalle de reserva, devoluciones (Fase 2), cancelar.'],
    html: () => `<div class="cuerpo">${C.volver('c-reservas', 'Reservas')}<h1>Tom Harris</h1><div class="tags">${C.tag('pend', 'Pendiente de pago')}<span class="tag neutro">WOD-000131</span></div>
      <dl class="datos tarjeta pad"><div><dt>Salida</dt><dd>Hoy 09:00 · Inmersión simple</dd></div><div><dt>Personas</dt><dd>1</dd></div><div><dt>Importe</dt><dd>45 €</dd></div><div><dt>Idioma</dt><dd>Inglés</dd></div><div><dt>Nivel</dt><dd>Open Water · 18 inm.</dd></div><div><dt>Tallas</dt><dd>L · 44 · L</dd></div></dl>
      <div class="acciones tres">${C.accion('tel', 'Llamar')}${C.accion('wa', 'WhatsApp', 'data-hoja="whatsapp" data-arg="Tom Harris"', 'wa')}${C.accion('mover', 'Mover', 'data-go="c-mover"')}${C.accion('euro', 'Cobrar')}${C.accion('descargar', 'Devolver')}${C.accion('x', 'Cancelar')}</div></div>` });

  /* ---------- More ---------- */
  P.reg('c-mas', { grupo: G, titulo: 'Más', ref: '§5.7', mod: 'centro', tab: 'c-mas',
    notas: ['Portada y logo, estado de cobros y verificación, y accesos.', 'Lo de oficina sale con «Disponible en la web» y abre la web con la sesión iniciada.'], web: ['Panel del centro (#/area).'],
    html: () => `<header class="cab bati"><div class="fila"><img src="${D.centro.logo}" class="logo-centro" alt="" style="width:56px;height:56px"><div class="crece"><h1 style="font-size:var(--t-l)">${esc(D.centro.nombre)}</h1><div class="tags">${C.tag('ok', 'Cobros online activos')}${C.tag('ok', 'Verificado')}</div></div></div></header>
      <div class="cuerpo"><div class="tarjeta plana lista">${[['reservas', 'Reservas', '', 'c-reservas'], ['euro', 'Servicios y tarifas', '5 servicios'], ['cobrar', 'Cobros y devoluciones', '1.240 € hoy', 'c-cobros'], ['buddies', 'Buceadores', '412 clientes'], ['regalo', 'Promociones y QR', '2 activas', 'c-promos'], ['cartel', 'Carteles', 'Plazas libres para compartir', 'c-cartel'],
        ['graficas', 'Estadísticas', 'Octubre', 'c-estadisticas'], ['barco', 'Barcos y puntos', 'Neptuno · 6 puntos'], ['equipo', 'Equipo del centro', 'Iván, Ana'], ['wa', 'WhatsApp Business', 'Conectado', 'c-wa-business'], ['resena', 'Reseñas por responder', '2'], ['descargar', 'Exportar datos', ''], ['tema', 'Apariencia', 'Clásico · Grande', 'ajustes'], ['ajustes', 'Ajustes', ''], ['persona', 'Cambiar de perfil', '', 'c-selector']].map(([i, t, s2, d]) => C.fila(i, t, esc(s2), d ? `data-go="${d}"` : '')).join('')}</div>
      <p class="eti">Disponible en la web</p><div class="tarjeta plana lista">${['Importar clientes (CSV)', 'Informes largos y DAC7', 'Textos legales', 'Tarifas por temporadas', 'Plan y cuota'].map((t) => C.fila('web', t, 'Se abre la web con tu sesión', 'data-hoja="soloweb" data-arg="' + esc(t) + '"')).join('')}</div></div>` });
  P.hojas.soloweb = (t) => ({ titulo: t || 'Disponible en la web', sub: 'Esto no cabe bien en un móvil. Se abre la web en el navegador, con tu sesión ya iniciada.',
    html: t === 'Plan y cuota' ? `<div class="aviso neutro">${ic('info', '')}<span>El plan se gestiona en la web. En iPhone la app no muestra precios ni enlaces de compra del plan.</span></div>` : '', pie: `<button class="btn ancho grande" data-cerrar>${ic('web', '')}Abrir en la web</button>` });
  P.reg('c-solo-web', { grupo: G, titulo: '«Disponible en la web»', ref: '§5.9', mod: 'centro', tab: 'c-mas', notas: ['Nada desaparece sin explicación: la opción está y abre la web.'],
    html: () => P.screens['c-mas'].html(), hoja: 'soloweb', hojaArg: 'Importar clientes (CSV)' });
  P.reg('c-promos', { grupo: G, titulo: 'Promociones y QR', ref: '§5.4.4', mod: 'centro', tab: 'c-mas',
    notas: ['Crear, ver, activar o pausar promociones con su QR; ver canjes; compartir.', 'QR del enlace de reservas del centro para el mostrador.'], web: ['Promociones con QR y canjes (Fase 3).'],
    html: () => `<div class="cuerpo">${C.volver('c-mas', 'Más')}<div class="fila-entre"><h1>Promociones y QR</h1><button class="btn" style="min-height:44px">${ic('mas1', '')}Nueva</button></div>
      ${[['10 % en la segunda inmersión', '14 canjes · hasta el 31/10', true], ['Bautizo 2×1 los martes', '3 canjes · pausada', false]].map(([t, s2, on]) => `<article class="tarjeta pad fila">${C.qr('worldives:promo:' + t, 72)}<div class="crece pila"><b>${t}</b><span class="suave peq">${s2}</span>${on ? C.tag('ok', 'Activa') : C.tag('canc', 'Pausada')}</div></article>`).join('')}
      <article class="tarjeta pad fila">${C.qr('https://worldives.example/c/centro-de-buceo-pruebas', 72)}<div class="crece pila"><b>QR de tu enlace de reservas</b><span class="suave peq">Para el mostrador</span><button class="btn sec" style="min-height:44px">${ic('compartir', '')}Compartir</button></div></article></div>` });
  P.reg('c-cartel', { grupo: G, titulo: 'Cartel de plazas libres', ref: '§5.4.4', mod: 'centro', tab: 'c-mas',
    notas: ['Se comparte por WhatsApp, Instagram o se descarga como imagen.'], web: ['Carteles del centro (la web ya genera carteles).'],
    html: () => `<div class="cuerpo">${C.volver('c-mas', 'Más')}<h1>Cartel de plazas libres</h1><div class="tarjeta" style="overflow:hidden"><div style="position:relative"><img src="img/arrecife.webp" alt="" style="height:220px;width:100%;object-fit:cover"><div style="position:absolute;inset:auto 0 0 0;padding:14px;background:linear-gradient(transparent,rgba(1,28,60,.85));color:#FFFFFF">
      <p style="font-size:22px;font-weight:700">Quedan plazas mañana</p><p>09:00 Isla del Portitxol · 4 plazas · 45 €</p><p>16:00 Bautizo · 2 plazas · 60 €</p></div></div><div class="pad fila" style="padding:12px 14px"><img src="${D.centro.logo}" class="logo-centro" alt=""><span class="crece peq"><b>${esc(D.centro.nombre)}</b><br>Reserva en worldives · enlace en el QR</span>${C.qr('https://worldives.example/c/centro-de-buceo-pruebas', 60)}</div></div>
      <div class="acciones tres">${C.accion('wa', 'WhatsApp', '', 'wa')}${C.accion('camara', 'Instagram')}${C.accion('descargar', 'Guardar imagen')}</div></div>` });
  P.reg('c-cobros', { grupo: G, titulo: 'Cobros y devoluciones', ref: '§5.7', mod: 'centro', tab: 'c-mas',
    notas: ['Lo cobrado de la semana (paso 7 del repaso de 3 minutos).', 'Textos llanos: «Cobrado», «Devuelto».'], web: ['Cobro directo por Stripe sin comisión y devoluciones (Fase 2).'],
    html: () => `<div class="cuerpo">${C.volver('c-mas', 'Más')}<h1>Cobros</h1><div class="seg"><button aria-pressed="false">Hoy</button><button aria-pressed="true">Semana</button><button aria-pressed="false">Mes</button></div>
      <div class="cifras"><div class="tarjeta cifra"><b>6.380 €</b><span>cobrado esta semana</span></div><div class="tarjeta cifra"><b>165 €</b><span>pendiente de pago</span></div></div>
      <div class="tarjeta plana lista">${[['Bea Buzo', 'Doble inmersión · tarjeta', '150 €', 'ok', 'Cobrado'], ['Lucía Pérez', 'Inmersión simple · Google Pay', '45 €', 'ok', 'Cobrado'], ['Hugo Blanco', 'Bautizo · mal tiempo', '−60 €', 'canc', 'Devuelto'], ['Pierre Dubois', 'Inmersión simple', '45 €', 'pend', 'En el centro']].map(([n, s2, imp, k, t]) =>
        `<div class="lista-fila"><span class="crece pila"><b>${n}</b><span class="suave peq">${s2}</span></span><span class="pila" style="justify-items:end"><b class="num">${imp}</b>${C.tag(k, t)}</span></div>`).join('')}</div>
      <p class="suave peq">Los cobros llegan a tu cuenta de Stripe. WORLDIVES no cobra comisión.</p></div>` });
  P.reg('c-estadisticas', { grupo: G, titulo: 'Estadísticas', ref: '§5.7', mod: 'centro', tab: 'c-mas',
    notas: ['Cifras simples y 2–3 gráficas de una sola serie, con el valor al tocar.'], web: ['Estadísticas del panel del centro.'],
    html: () => { const sem = [52, 61, 58, 70, 66, 74, 81, 77], max = 90; const W = 340, H = 150, bw = 26, gap = (W - 30 - sem.length * bw) / (sem.length - 1);
      const barras = sem.map((v, i) => { const x = 30 + i * (bw + gap), h = v / max * (H - 30); return `<rect class="barra${i === sem.length - 1 ? ' ultima' : ''}" x="${x.toFixed(1)}" y="${(H - 20 - h).toFixed(1)}" width="${bw}" height="${h.toFixed(1)}" rx="4"><title>Semana ${i + 1}: ${v} buceadores</title></rect>${i === sem.length - 1 || v === Math.max(...sem) ? `<text class="etiqueta" x="${(x + bw / 2).toFixed(1)}" y="${(H - 26 - h).toFixed(1)}" text-anchor="middle">${v}</text>` : ''}<text x="${(x + bw / 2).toFixed(1)}" y="${H - 4}" text-anchor="middle">S${i + 35}</text>`; }).join('');
      const grid = [0, 30, 60, 90].map((v) => `<line class="rejilla" x1="24" x2="${W}" y1="${(H - 20 - v / max * (H - 30)).toFixed(1)}" y2="${(H - 20 - v / max * (H - 30)).toFixed(1)}"/><text x="0" y="${(H - 16 - v / max * (H - 30)).toFixed(1)}">${v}</text>`).join('');
      const dias = [['L', 62], ['M', 70], ['X', 58], ['J', 64], ['V', 78], ['S', 94], ['D', 88]];
      return `<div class="cuerpo">${C.volver('c-mas', 'Más')}<h1>Estadísticas</h1><div class="cifras"><div class="tarjeta cifra"><b>418</b><span>buceadores en octubre</span></div><div class="tarjeta cifra"><b>68 %</b><span>ocupación media</span></div><div class="tarjeta cifra"><b>4,8</b><span>valoración (126)</span></div><div class="tarjeta cifra"><b>31 %</b><span>repiten</span></div></div>
        <section class="tarjeta pad pila-8"><h2>Buceadores por semana</h2><svg class="grafica" viewBox="0 0 ${W} ${H}" role="img" aria-label="Buceadores por semana, de 52 a 81">${grid}${barras}</svg></section>
        <section class="tarjeta pad pila-8"><h2>Ocupación por día de la semana</h2>${dias.map(([d, v]) => `<div class="mini-barra" style="grid-template-columns:20px minmax(0,1fr) 40px"><span>${d}</span><span class="pista"><i style="width:${v}%"></i></span><span class="num">${v} %</span></div>`).join('')}</section></div>`; } });
  P.reg('c-wa-business', { grupo: G, titulo: 'WhatsApp Business', ref: '§7.2', mod: 'centro', tab: 'c-mas',
    notas: ['Estado de la conexión y de los avisos masivos: el mismo sistema de la web, sin duplicar nada.'], web: ['WhatsApp Cloud API por centro, cola, estado y deshacer (v50.47).'],
    html: () => `<div class="cuerpo">${C.volver('c-mas', 'Más')}<h1>WhatsApp Business</h1><div class="aviso ok">${ic('check', '')}<span><b>Conectado</b> · +34 600 000 101 · los avisos salen de tu número y las respuestas te llegan a ti.</span></div>
      <h2>Últimos avisos masivos</h2><div class="tarjeta plana lista">${[['Cancelación por mal tiempo', fCorta(dia(-3)) + ' · 6 de 6 entregados', 'ok', 'Entregado'], ['Recordatorio del día antes', 'Ayer 18:00 · 18 de 18', 'ok', 'Entregado'], ['Cambio de hora', 'Hoy 8:02 · 3 de 4, 1 sin WhatsApp: por correo', 'pend', 'Enviando']].map(([t, s2, k, tt]) =>
        `<div class="lista-fila"><span class="crece pila"><b>${t}</b><span class="suave peq">${s2}</span></span>${C.tag(k, tt)}</div>`).join('')}</div></div>` });
  P.reg('c-instructor', { grupo: G, titulo: 'Vista de instructor', ref: '§5.10', mod: 'instructor', tab: 'c-instructor',
    notas: ['Instructor: Hoy, Agenda, sus salidas, la lista del barco y Escanear. No ve cobros ni ajustes.', 'Recepción: además Reservas y Solicitudes. Dueño y encargado: todo. Las mismas reglas del servidor que en la web.'], web: ['Roles del equipo del centro (instructor.prueba en la demo).'],
    html: () => `<header class="cab bati"><div class="cab-fila"><img src="${D.centro.logo}" alt="" class="logo-centro"><div class="crece"><p style="font-weight:600">${esc(D.centro.nombre)}</p><p class="suave peq">Iván · instructor</p></div></div><h1 style="font-size:var(--t-l)">Tus salidas de hoy</h1>${C.mar()}</header>
      <div class="cuerpo">${D.salidas.slice(0, 2).map(tarjetaSalidaCentro).join('')}<div class="aviso neutro">${ic('candado', '')}<span>Como instructor no ves cobros, tarifas ni ajustes del centro.</span></div></div>` });
  P.reg('c-instructor-mas', { grupo: G, titulo: 'Más (instructor)', ref: '§5.10', mod: 'instructor', tab: 'c-instructor-mas', notas: ['Menú reducido: sin cobros ni ajustes del centro.'],
    html: () => `<div class="cuerpo"><h1>Más</h1><div class="tarjeta plana lista">${C.fila('agenda', 'Mis salidas de la semana', '9 salidas')}${C.fila('documento', 'Resumen para el barco', '', 'data-go="c-resumen-barco"')}${C.fila('tema', 'Apariencia', 'Clásico · Grande', 'data-go="ajustes"')}${C.fila('persona', 'Cambiar de perfil', '')}</div></div>` });
})();
