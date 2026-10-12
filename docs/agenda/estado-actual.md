# Agenda y reservas: cómo está hoy (v50.43)

Revisión del encargo unificado, punto A1.1. No se ha cambiado código. Las referencias son a `app/server.py` (S:línea) y a `public/assets/js/world-dives-v8.js` (J:línea) de la v50.43.

## 1. Piezas actuales

| Pieza | Tabla / función | Qué guarda o hace |
|---|---|---|
| Servicio | `provider_services` (S:363) | Lo crea un centro o un freelance. Guarda el tipo (`inmersion`, `curso`, `salida`, `experiencia`, `vida_a_bordo`, `viaje`, `alquiler_equipo`, S:2213), el título, la duración en minutos, el precio, el máximo de personas, el color, el modo de reserva (Fase 1B), los plazos de respuesta y de pago, la señal (Fase 2), la política de cancelación, el cambio de fecha y la lista de espera (v50.41). |
| Salida | `service_slots` (S:440) | **Un día y una hora**, con sus plazas (`spots_total` y `spots_available`), su estado (`open`, `full` o `closed`) y su cancelación (v50.41). No puede haber dos salidas del mismo servicio el mismo día a la misma hora (`UNIQUE(service_id, slot_date, slot_time)`). |
| Puntos de la salida | `service_slot_points` (S:436) | Uno o varios puntos de buceo, o «según el tiempo» (`point_mode`). |
| Reserva | `bookings` (S:82) | Fecha (`booking_date`), hora, salida (`slot_id`), personas, estado, modo, plazos, importes, señal, devoluciones y token privado. |
| Tomar plazas | `reserve_slot_spots` (S:2311) | Una sola sentencia `UPDATE … WHERE spots_available>=?`, así que dos reservas a la vez nunca toman la misma plaza. |
| Liberar plazas | `release_slot_spots` (S:2316) | Devuelve plazas y avisa a la lista de espera (v50.41). |
| Precio | `booking_quote` (S:2270) | Precio por persona según la tarifa vigente (`center_tariffs`: historial de precios con fecha de inicio, no temporadas), más el alquiler de equipo y los extras por persona. |
| Equipo de alquiler | `center_equipment` (S:119) | Código, nombre y precio. **Sin stock por talla.** |
| Barcos | `boats` (S:656) | Nombre y capacidad, del centro o del freelance (v50.40). |
| Grupos del manifiesto | `slot_groups` (S:658) | Barco y guía de **cada salida** (v50.40). |
| Equipo del centro | `center_members` (S:149) | Roles: propietario, recepción e instructor (`TEAM_ROLES`, S:3081). |
| Planning | `center_planning` (S:4037), `renderCenterPlanning` (J:3604) | Vistas «Mes» y «Lista» de un mes: salidas y reservas. El freelance usa la misma pantalla (J:2295). |
| Hoy en el barco | `#/barco` (v50.42) | Salidas de hoy y de mañana, también sin conexión. |
| Calendario iCal | `ical_feed` (S:2952) | Enlace privado **de salida** con las reservas. No importa calendarios externos. |
| Planes | `PLAN_FEATURES` (S:2603) | Funciones activables por plan. Están preparadas para añadir más. |

## 2. Cómo se calculan las plazas
- **Cada salida tiene sus propias plazas.** Reservar resta personas de `spots_available` de forma atómica:
  - **«Pago al reservar»:** al empezar el pago. Si no se paga en 15 min (`HOLD_MINUTES`), se devuelven.
  - **«Bajo petición»:** al solicitar. Si el centro rechaza o no responde a tiempo, se devuelven.
- **Bajar la capacidad** por debajo de lo ocupado no se permite (S:9475).
- **Una reserva sin salida** (solo con fecha) **no controla ninguna capacidad**. Es lo que se usa hoy para servicios sin horario: el cliente elige un día y nada impide que otro elija el mismo.

## 3. Qué falta para los casos del encargo

| Caso | Qué pasa hoy |
|---|---|
| **Freelance por días** (Tito, de lunes a miércoles) | No existe. Solo puede publicar salidas sueltas de un día y una hora, o aceptar reservas «con fecha» sin control. No hay calendario público de disponibilidad, ni rango de días, ni medio día, ni bloqueos manuales, ni tramos por duración. |
| **Curso de varios días** (Open Water de 3 días) | Se crea como servicio `curso` con una salida el día 1. Los días 2 y 3 **no aparecen** en el planning, el instructor **no queda ocupado** y nada impide asignarle otra salida a la misma hora. No hay programa de sesiones ni plantillas. |
| **Instructores y barcos ocupados** | `slot_groups` asigna guía y barco a una salida (v50.40), pero **no comprueba solapes** con otras salidas ni la capacidad del barco entre salidas. |
| **Vista por recursos** | No existe. |
| **Zona horaria** | Las fechas y horas se guardan como hora local «sin zona». El servidor calcula los plazos con su propia hora (`local_now`, S:6051), y `WOD_TIMEZONE` solo se usa en el iCal. Un guía en México y un centro en España funcionarían con la hora del servidor: **hay que corregirlo**. |
| **Rendimiento** | El catálogo de demostración tiene 28 centros y ninguna salida. No hay medición de un mes con cientos de recursos. Índices actuales: `service_slots(service_id, slot_date, slot_time)` y reservas por centro y fecha. |

## 4. Lo que ya existe y se reutiliza (no se rehace)

| Del encargo | Estado | Dónde |
|---|---|---|
| Dos modos de reserva, plazos y caducidad | Ya estaba | Fase 1B, v50.32 |
| Cobro directo por Stripe, señal y devoluciones | Ya estaba | Fase 2, v50.34 |
| Equipo del centro con roles | Ya estaba | Fase 6.6, v50.37 |
| Barcos con capacidad | Ya estaba (sin control de solapes) | v50.40 |
| Manifiesto, descargo y check-in sin conexión (hoy y mañana) | Ya estaba | v50.40 y v50.42. Para E14 falta ampliarlo a 7 días y a cursos. |
| Lista de espera (salidas) | Ya estaba, con un plazo de 2 h | v50.41. Para E7 falta: plazo de 4 h configurable y que funcione con días y cursos. |
| Cambio de fecha por el cliente | Ya estaba, sin cobrar la diferencia | v50.41. Para E5 faltan el cobro o la devolución automáticos de la diferencia y el límite de «una vez». |
| Cancelar una salida con devolución íntegra | Ya estaba | v50.41. Se reutiliza para E3 (mínimo de participantes). |
| Calendario iCal privado (exportar) | Ya estaba | Fase 6. Para E10 falta la importación. |
| Exportación de datos del centro | Ya estaba | Fase 6.5. Falta añadir la agenda, los cursos y los bloqueos. |
| Códigos de promoción | Ya estaba | Siguen funcionando con las tarifas nuevas. |
| Avisos por correo en 10 idiomas | Ya estaba | Plantillas y cola de correo. **Push:** solo existe la app instalable, sin notificaciones push (ver diseño, §9). |
