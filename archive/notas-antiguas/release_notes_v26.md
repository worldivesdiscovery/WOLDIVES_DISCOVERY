# WORLDIVES DISCOVERY v26 — plazas y salidas automáticas

- Los servicios del centro/freelance se pueden editar desde su panel: nombre, tipo, precio, duración, máximo de participantes, modo de reserva y descripción.
- Las salidas programadas se pueden editar en fecha, hora y capacidad total.
- La capacidad disponible ya no se introduce manualmente: WORLDIVES calcula automáticamente `disponibles = capacidad total - plazas ocupadas`.
- Una reserva consume tantas plazas como participantes tenga, no una sola plaza fija.
- Las reservas confirmadas o pagadas descuentan automáticamente la capacidad de la salida. Las cancelaciones/rechazos liberan las plazas.
- El checkout de pago reserva la capacidad de forma atómica para evitar sobreventa; si el checkout expira, las plazas se liberan.
- En la reserva del cliente se muestran mensajes de disponibilidad como «¡Última plaza!» o «¡Quedan 2 plazas!».
- Se evita confirmar una reserva de pago mientras el pago siga pendiente.
- Las reservas antiguas se vinculan automáticamente con su salida por fecha/hora cuando existe coincidencia.
- Se mantiene la compatibilidad con las funciones anteriores de WORLDIVES DISCOVERY.
