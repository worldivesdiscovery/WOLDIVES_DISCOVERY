# WORLDIVES DISCOVERY v50.32: modos de reserva (Fase 1B)

Solo quedan **dos modos de reserva**. «Reserva inmediata» desaparece. La lógica se cumple en el servidor y se ve igual en todas las pantallas.

## Los dos modos
| Modo | Qué ve el buceador | Qué pasa |
|---|---|---|
| **Pago al reservar** | «Pago al reservar · confirmación inmediata» y el botón «Reservar y pagar X €» | Paga en Stripe al momento. Mientras paga, las plazas quedan bloqueadas 15 minutos (`WOD_PAYMENT_HOLD_MINUTES`). Si el pago se confirma, la reserva queda **confirmada sola**. Si lo abandona o se acaba el tiempo, las plazas se liberan y la reserva queda «Caducada · no pagada», sin aparecer al centro. |
| **Bajo petición** | «Bajo petición · el centro responde en X h» y el botón «Enviar solicitud», con «No se cobra nada hasta que el centro acepte» | La solicitud no descuenta plazas. El centro acepta o rechaza (con motivo opcional) dentro de su plazo. Al aceptar se reservan las plazas; si cobra online y hay precio, el buceador tiene un plazo para pagar; si no, queda confirmada con pago en el centro. |

- **«Pago al reservar» exige cobros online.** Si el centro no los tiene, la opción aparece desactivada con «Activa los cobros online para usar esta opción» y un enlace a «Cobros y pagos».
- **Si el centro pierde los cobros online**, sus servicios en ese modo dejan de poder reservarse («No admite reservas ahora mismo») y el centro recibe un email para pasarlos a «Bajo petición». **Nunca se convierte en silencio en pago en el centro.**
- **Ningún camino confirma una reserva «Pago al reservar» sin el pago confirmado por Stripe**: ni el cambio de estado, ni el cobro en mostrador, ni un webhook sin pago.
- **Servicio gratis:** se confirma al momento sin pasar por Stripe.
- **Plazos** (por servicio): para responder (24 h por defecto) y para pagar tras aceptar (24 h). Nunca posteriores al inicio de la salida.
- **Tarea periódica cada minuto:** bloqueos de pago, plazos de respuesta y plazos de pago. Al caducar se avisa a ambos por email.
- **Al cambiar el modo** de un servicio, las reservas en curso conservan el suyo.

## Estados únicos
`solicitada`, `aceptada_pendiente_pago`, `pago_en_curso`, `confirmada`, `rechazada`, `caducada`, `cancelada`, `completada`. Mismos nombres en el servidor, el panel, «Mis reservas», los correos y los PDF (ver `docs/estados-reserva.md`).

## Dónde se ve
- Buscador de centros (insignia y **nuevo filtro «Confirmación inmediata»**) y de puntos (filtro).
- Ficha del centro (servicios y salidas, con el botón según el modo), ficha del punto, página de reserva, «Mis reservas» y la ficha de la reserva (con plazos).
- Panel del centro: servicios, formulario, planning (el pago en curso solo aparece en gris, sin nombre), reservas y **«Solicitudes pendientes»** con contador, tiempo para responder y botones Aceptar / Rechazar.
- **Enviar aviso al cliente** desde la reserva (Fase 1, G11).

## Formulario de servicio
- Solo dos opciones, con explicación y un ejemplo de lo que verá el cliente.
- «Bajo petición» muestra los plazos de respuesta y de pago.
- Las plantillas por defecto usan «Pago al reservar» si hay cobros online y «Bajo petición» si no.

## Migración
- Servicios en «Reserva inmediata»: con precio y cobros online → «Pago al reservar»; en cualquier otro caso → «Bajo petición». Igual las plantillas. Cada cambio queda en la tabla `booking_mode_migration` para revisarlo. En la base entregada no había ningún servicio.
- Reservas antiguas «pendientes» pasan al estado nuevo que corresponde.

## También
- El planning y las cifras del centro muestran todos los servicios del centro, no solo los de quien los creó (adelantado de la Fase 6.6).
- La pantalla de reserva ya muestra «Prestado por [centro]», precio final con impuestos, política de cancelación, aviso de desistimiento y enlace a las condiciones (adelantado de la Fase 5.7).
- Experiencias: el pago online multiplica precio × participantes (adelantado de la Fase 2.7).

## Comprobado
- `tests/test_phase1b_booking_modes.py`: 19 pruebas con un simulador local de Stripe, para cada combinación de modo × cobros online × precio: pago correcto (webhook y página de vuelta), pago abandonado, bloqueo caducado, intento de confirmar sin pagar (falla), webhook falso o sin pago (falla), centro que desactiva los cobros, aceptar, rechazar con motivo, no responder hasta caducar, aceptar sin plazas, aceptar y no pagar a tiempo, aceptar y pagar, cambio de modo con reservas en curso, migración.
- `tests/e2e_booking_modes.py`: navegador real en ordenador y móvil, 35/35 comprobaciones de etiqueta, botón y estado en cada pantalla.
- Pruebas de la Fase 1 y recorrido con los 5 roles: sin errores.
