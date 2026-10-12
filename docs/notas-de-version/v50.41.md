# WORLDIVES DISCOVERY v50.41: cancelar una salida, cambio de fecha por el cliente y lista de espera (encargo 2, puntos 2, 3 y 4)

## Qué había antes
- **Cancelar una salida:** existía la ruta `slot-close`, pero rechazaba las salidas con reservas y la web no la usaba. El centro tenía que cancelar reserva por reserva, con devolución íntegra (Fase 2), y el correo no decía el motivo.
- **Cambio de fecha:** solo lo podía hacer el centro (`/api/bookings/<id>/reschedule`, con el correo «Tu reserva ha cambiado»). El buceador no tenía esa opción.
- **Lista de espera:** no existía.
- **Historial de una salida:** solo había entradas del registro de actividad general.

## 2 · Cancelar una salida por mal tiempo
- **Botón «Cancelar salida»** en la salida del planning y en su manifiesto. Lo pueden usar el propietario y recepción; el instructor no.
- **Motivo:** mal tiempo, estado del mar u otro motivo (con explicación obligatoria), y una nota opcional para los buceadores.
- **Antes de confirmar se ve la lista de afectados y qué recibe cada uno:**
  - «Se avisará a 2 reservas (3 buceadores) por email.»
  - Si ha pagado: cambio de fecha o devolución íntegra del importe.
  - Si no ha pagado: cambio de fecha o anulación sin coste.
  - Pago en curso: se anula y no se cobra.
  - Si no hay otra salida con plazas, se avisa de que solo podrá elegir la devolución o la anulación.
- **Plazo para elegir configurable:** 48 h por defecto. Se recuerda como valor por defecto del centro.
- **Correo a cada buceador** con la plantilla de la marca: motivo, opciones, plazo y el botón «Elegir ahora».
  - El enlace funciona sin iniciar sesión, con la clave privada de la reserva.
  - En «Mi reserva» aparece además un aviso con el mismo botón.
- **Pantalla de elección (`#/salida-cancelada`):**
  - **Cambiar de fecha:** salidas del mismo servicio con plazas suficientes, con el mismo precio.
  - **Devolución íntegra o anulación:** cada opción pide confirmación con un resumen.
- **Sin respuesta dentro del plazo:** devolución íntegra automática (o anulación sin coste). La hace el trabajo periódico del servidor.
- **Se reutiliza lo que ya había:**
  - devoluciones de la Fase 2 (Stripe en la cuenta del centro, con aviso si falla);
  - correos de cancelación y de devolución;
  - cola de correos.
- **El centro recibe un correo** con la respuesta de cada buceador y ve el estado en la reserva («el cliente puede elegir hasta…»).
- **Mientras el buceador elige,** los plazos de respuesta y pago y los recordatorios de 48 h y 24 h no se aplican a esa reserva.
- **Historial de la salida** en su manifiesto: cancelación, elecciones, devoluciones automáticas y reservas movidas.

## 3 · Cambio de fecha por el cliente
- **«Cambiar fecha» en «Mi reserva»** si el servicio lo permite y está dentro de plazo (48 h antes por defecto). Muestra solo las salidas del mismo servicio con plazas libres para todas las personas de la reserva.
- **Mismo precio.** Si la nueva fecha tiene otra tarifa, se indica la diferencia antes de confirmar («precio distinto: +30 €»), pero la reserva mantiene su precio. Ver «Pendiente de decisión».
- **El centro elige por servicio** (formulario del servicio → «Cambios de fecha y lista de espera»):
  - cambio directo;
  - con su aprobación (opción por defecto);
  - no permitido;
  - y el plazo en horas.
- **Cambio directo:**
  - las plazas se mueven de forma atómica: primero se toman las nuevas y después se liberan las antiguas, en la misma transacción;
  - se avisa por correo al cliente y al centro.
- **Con aprobación:**
  - se envía una solicitud y el centro la ve en la reserva («Aceptar el cambio» / «Rechazar», con un motivo opcional);
  - el cliente recibe la respuesta por correo;
  - las solicitudes caducan si llega la salida original.
- **Una sola función de cambio de salida** para el centro, el buceador y las salidas canceladas. La de la Fase 1B se ha adaptado a ella.

## 4 · Lista de espera
- **En las salidas completas, «Avisarme si queda plaza»** en la página de reserva, con las personas elegidas. Muestra el puesto y permite «Salir de la lista».
- **Cuando se libera una plaza** (cancelación, rechazo, caducidad, cambio de fecha):
  - la primera persona de la lista que cabe recibe un correo;
  - sus plazas quedan **guardadas** 2 h, nunca después del inicio de la salida;
  - si no reserva, pasan a la siguiente.
- **La persona avisada ve «Te guardamos 1 plaza… hasta…»** y puede reservarla.
- **Respeta el modo de reserva:**
  - **«Pago al reservar»:** paga para reservar.
  - **«Bajo petición»:** la solicitud conserva la plaza mientras el centro responde.
- **El centro ve la lista en la salida** (manifiesto). La puede desactivar por servicio.
- **Si la salida se cancela,** la lista se cierra.

## Migración `migrate_v50_41` (solo añade)
- **Tablas nuevas:** `slot_events` (historial de la salida), `slot_cancel_offers`, `reschedule_requests` y `waitlist_entries`.
- **Columnas nuevas:**
  - `service_slots`: `cancelled_at`, `cancel_reason`, `cancel_note`, `cancelled_by`;
  - `provider_services`: `reschedule_mode` (por defecto «con aprobación»), `reschedule_hours`, `waitlist_enabled` (por defecto activada);
  - `centers` y `users`: `slot_cancel_choice_hours`.
- No se borra nada.

## Estado

| Parte | Estado |
|---|---|
| 2. Botón «Cancelar salida» con motivo | Nuevo |
| 2. Lista de afectados y qué recibe cada uno antes de confirmar | Nuevo |
| 2. Correo con dos opciones (otra fecha o devolución íntegra) | Nuevo |
| 2. Devolución automática si no elige en el plazo (48 h configurable) | Nuevo |
| 2. Usa las devoluciones y la cola de correos existentes; historial de la salida | Completado (devoluciones y correos de la Fase 2; el historial es nuevo) |
| 3. «Cambiar fecha» en «Mi reserva», dentro de plazo y si el centro lo permite | Nuevo |
| 3. Solo salidas del mismo servicio con plazas; mismo precio; diferencia indicada | Nuevo; cobro o devolución de la diferencia: Pendiente de decisión |
| 3. Cambio directo o con aprobación, por servicio | Nuevo |
| 3. Aviso al centro y al cliente; plazas movidas de forma atómica | Completado (amplía el cambio que hacía el centro) |
| 4. «Avisarme si queda plaza» en salidas completas | Nuevo |
| 4. Aviso al primero con plazo de 2 h, nunca después del inicio; después al siguiente | Nuevo |
| 4. Respeta el modo de reserva | Nuevo |
| 4. El centro ve la lista y la desactiva por servicio | Nuevo |

## Pendiente de decisión
- **Cambio de fecha con precio distinto:** ¿se cobra o se devuelve la diferencia? Hoy la reserva mantiene su precio y se muestra la diferencia al cliente y al centro.
- **Opción por defecto del cambio de fecha** en los servicios nuevos y existentes: hoy «con mi aprobación». ¿«Directo» o «No» como opción por defecto?
- **Lista de espera:** cuando la primera persona no cabe (pide más plazas de las libres), hoy se avisa a la siguiente que sí cabe y la primera sigue esperando. ¿O hay que esperar a que quepa la primera?

## Para el abogado
- **Cancelación por el centro (mal tiempo):** devolución íntegra o cambio de fecha, a elección del consumidor, con devolución automática si no elige. ¿Es suficiente frente al TRLGDCU? ¿El plazo de 48 h es razonable?
- **Diferencia de precio en el cambio de fecha:** ¿qué hay que informar si se cobra o se devuelve?
- **Lista de espera:** datos guardados (cuenta, salida, número de personas, fechas). ¿Alguna mención en la política de privacidad?

## Cómo se probó
- **`tests/test_e2_p2_p3_p4.py`, 3 pruebas** con el simulador de Stripe y sobre una copia de la base:
  - **Cancelar salida:** vista previa con lo que recibe cada uno; permisos de otro centro y de un buceador; datos erróneos (sin motivo, «otro» sin explicación, plazo 0); cancelación con correos; cambio de fecha desde el enlace sin iniciar sesión, con plazas movidas; una sola elección; devolución pedida con reembolso real; enlace ajeno o falso; historial y planning; devolución automática al vencer el plazo.
  - **Cambio de fecha:** opciones del servicio con permisos; diferencia de precio con otra tarifa; cambio directo con plazas movidas y correos; con aprobación (pendiente, una sola solicitud, permisos, aprobar y rechazar con correo); plazo de 48 h; modo «No».
  - **Lista de espera:** no se apunta si hay plazas ni una cuenta de centro, ni dos veces; orden; plaza guardada al primero que cabe sin pasar del inicio; correo; reserva «bajo petición» con la plaza; rechazo que pasa la plaza al siguiente; caducidad que la libera; historial; desactivada por servicio.
- **`tests/e2e_departures.py`, 31/31 en navegador, en ordenador y en móvil:**
  - cancelar con resumen y motivo;
  - etiqueta «Cancelada» en el planning e historial;
  - elección desde el enlace del correo en el móvil;
  - anulación desde «Mi reserva»;
  - cambio de fecha con aprobación, aceptado por el centro;
  - opciones en el formulario del servicio;
  - «Avisarme si queda plaza», puesto y «Te guardamos 1 plaza»;
  - sin errores de JavaScript ni desbordamiento.
- **Capturas** en `docs/capturas/encargo2/punto2-4/`.
