# WORLDIVES DISCOVERY v21 · Plataforma profesional y pagos

## Gestión profesional
- Centros de buceo y profesionales/freelance pueden crear servicios propios.
- Cada servicio admite tipo, descripción, duración, precio, moneda, plazas máximas y modo de reserva.
- Se pueden programar salidas con fecha, hora, plazas totales y disponibles.
- Los servicios publicados aparecen en la ficha pública del centro y en el flujo de reserva.
- Las reservas guardan el servicio y el precio vigente en el momento de la reserva.

## Identidad profesional
- Los centros pueden actualizar redes sociales desde su sesión.
- Los centros pueden subir una nueva foto/logo.
- Los freelance pueden actualizar redes, biografía y foto profesional.

## Pagos
- Añadido modelo de órdenes de pago separado de la reserva.
- Checkout preparado para Stripe Checkout.
- WORLDIVES no almacena tarjetas, CVV ni credenciales de pago.
- La confirmación real del pago se realiza mediante webhook firmado de Stripe.
- Un pago confirmado puede pasar la reserva a confirmada y actualizar el estado de pago.
- Configuración mediante `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` y `WOD_PUBLIC_URL`.
- Si las claves no están configuradas, el sistema no simula un pago: informa de que el checkout seguro no está configurado.

## Seguridad
- Autorización por proveedor para crear/modificar servicios y salidas.
- Órdenes de pago vinculadas al usuario y al servicio.
- Auditoría de creación/modificación de servicios, salidas y pagos.
