# WORLDIVES DISCOVERY v27 — Flujo profesional de reservas y pagos

- En cuentas de **Centro de buceo**, el acceso principal del menú pasa de **Mi área** a **Gestionar mi centro**. Si se intenta abrir `#/area` estando autenticado como centro, se redirige automáticamente al panel profesional.
- Los freelance mantienen **Mi área** porque pueden actuar también como buceadores.
- Corregido el flujo **Solicitud + confirmación**: una solicitud con precio ya no obliga al buceador a pagar al crearla.
- El centro puede confirmar primero la disponibilidad de la inmersión.
- Al confirmar una solicitud con precio, la reserva pasa a `payment_status=required`, se reserva la plaza y el buceador recibe un mensaje indicando que el pago ya está habilitado.
- En la ficha de reserva aparece **Pagar y confirmar** cuando el centro ya ha confirmado y el pago está pendiente.
- El checkout se habilita para reservas ya confirmadas, incluso si la salida ha quedado llena porque la plaza de esa reserva ya estaba retenida.
- **Pago obligatorio** y **Reserva inmediata** mantienen el flujo de pago previo a la confirmación cuando el servicio tiene precio.
- El selector de modo de reserva del centro incluye una explicación más clara de cada modalidad.
- El precio y la capacidad siguen estando controlados por el servidor.
