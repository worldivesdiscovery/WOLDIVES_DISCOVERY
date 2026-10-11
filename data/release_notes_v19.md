# WORLDIVES DISCOVERY v19

## Cliente: reservas y navegación
- Añadida la ruta real `#/reserva?id=...` para que "Detalles" y "Ver mi reserva" abran la ficha de la reserva.
- La ficha muestra centro, fecha, hora, punto, participantes, equipo, guía, nitrox, recogida/traslado, notas y estado.
- El centro aparece enlazado a su ficha pública.
- Teléfono del centro enlazado como llamada desde móvil y acceso directo a la ficha del centro.
- Se conserva el recibo PDF + QR.

## Log Book automático
- Al marcar una reserva como `completed`, se crea automáticamente una entrada de Log Book vinculada a esa reserva.
- Las reservas completadas existentes se incorporan una sola vez al arrancar esta versión.
- La entrada automática deja profundidad y duración vacías para que el buceador pueda completarlas con los datos de su ordenador posteriormente.
- Se añade `booking_id` e índice único parcial para evitar duplicados.

## Menús
- El desplegable de cuenta se cierra al cambiar de ruta.
- El menú principal móvil también se cierra al navegar.
- Se evita el comportamiento anterior en el que el desplegable quedaba abierto después de entrar en Mi cuenta/Mi área.
