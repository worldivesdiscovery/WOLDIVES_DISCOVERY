/* What the web really has today for each screen, from docs/app/paridad.md (code read on 13/10/2026).
   Kept apart so the notes can be updated without touching the screens. S: = app/server.py, J: = public/js/world-dives-v8.js. */
(function () {
  'use strict';
  const fijar = (id, k, v) => { if (P.screens[id]) P.screens[id][k] = v; };
  const anadir = (ids, k, ...v) => [].concat(ids).forEach((id) => { const s = P.screens[id]; if (s) s[k] = [...(s[k] || []), ...v]; });
  const esc = ['c-escanear', 'c-canjear', 'c-escaneo-ok', 'c-escaneo-usado', 'c-escaneo-caducado', 'c-escaneo-otro', 'c-escaneo-otra-salida', 'c-camara-denegada', 'f-escanear'];
  esc.forEach((id) => fijar(id, 'web', ['Hoy el centro marca «Presente» a mano en la lista del barco (#/barco, v50.42).', 'Leer el QR de una reserva solo abre una página de consulta; el único escáner con cámara de la web es el de códigos de puntos (J:2617).']));
  anadir(esc, 'falta', 'Check-in leyendo el QR de la reserva y marcando la presencia en la salida: nuevo en el servidor (respuestas de usado, caducado, de otro centro y de otra salida).');
  anadir('f-escanear', 'falta', 'Promociones del freelance: no existen en la web (solo las del centro).');
  anadir(['c-salida', 'c-resumen-barco'], 'falta', 'Sin conexión: hoy el manifiesto se guarda para hoy y mañana (S:10090); el encargo pide 7 días.', 'PDF del manifiesto: hoy solo se imprime desde el navegador (J:2418).');
  anadir(['c-mover', 'c-salida-buceador'], 'falta', 'Mover: hoy solo a otra salida del mismo servicio (S:11799).');
  anadir(['c-whatsapp', 'c-pendientes', 'c-salida-buceador', 'c-reserva-detalle'], 'falta', 'Botón «WhatsApp» por cliente con mensaje ya escrito en su idioma: no existe en la web (sí los avisos automáticos de v50.47).');
  anadir(['b-inicio', 'b-ficha-centro', 'b-reserva-ok'], 'falta', '«WhatsApp al centro» para el buceador: no existe en la web.');
  anadir(['c-instructor', 'c-instructor-mas'], 'falta', 'Roles de hoy (app/wod/inquilinos.py:28): el encargado no puede devoluciones, Stripe, tarifas, escaparate, equipo ni plan, ni guardar barcos (S:10839). El encargo dice «Dueño y encargado: todo».', 'El instructor ve todas las salidas: no hay filtro «mis salidas».');
  anadir('c-cobros', 'falta', 'Fallo de la web: recepción y encargado ven «Cobros y pagos», pero el servidor les responde 403 (J:4533 frente a S:3519). Se corrige en la web, no en la app.');
  anadir('ajustes', 'falta', 'Borrar la cuenta: hoy solo los buceadores (S:11715). Centros y freelance tienen que escribir; Apple exige poder borrarla desde la app.', 'Lista de sesiones abiertas: no existe en la web.');
  anadir(['f-agenda-mes', 'f-bloquear'], 'falta', 'iCal: hoy solo exportar; importar no existe.');
  anadir('c-agenda-mes', 'falta', 'Cursos de varios días: hoy solo como servicio «por días»; las barras de curso en la agenda son nuevas.');
  anadir('c-mas', 'falta', 'Reseñas: el panel no tiene lista; se responden desde la página pública.', 'El encargo no pone «Experiencias» ni «Escaparate» del centro en Más, y la web los tiene.');
  anadir('f-mas', 'falta', 'La web también da al freelance Estadísticas, Carteles, Log Book y reservar como buceador; el encargo no los pone en Más.', 'Respecto al centro, al freelance le faltan en la web: reseñas, reservas manuales, extras, alquiler de equipo, tarifas programadas y promociones.');
  anadir(['b-reserva', 'b-reserva-cambiar'], 'web', 'Acompañantes con nombre: el servidor ya lo admite (S:10892) aunque la web no lo usa.');
  anadir('b-ficha-centro', 'falta', 'Reseñas: hoy se pide una reserva pagada, no un check-in (S:10953).');
})();
