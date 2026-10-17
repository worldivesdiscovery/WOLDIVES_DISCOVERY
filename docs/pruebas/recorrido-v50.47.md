# Recorrido completo v50.47 (navegador real)

Fecha: 2026-10-12. Entorno de pruebas (base del zip «-pruebas», dos centros, WhatsApp de prueba, Stripe simulado). Escritorio 1366×900 y móvil 390×844. Capturas en `docs/capturas/v50.47/`.

| Resultado | Comprobación |
|---|---|
| OK | Crear la cuenta de administración (pantalla de pruebas) |
| OK | Buceador: pago con la tarjeta 4242 (Stripe simulado) → reserva confirmada y pagada |
| OK | Buceador: reserva bajo petición → «solicitada» |
| OK | Centro: aceptar la solicitud |
| OK | Visitante (escritorio): sin errores de JavaScript ni de política de contenido |
| OK | Visitante (escritorio): ninguna página más ancha que la pantalla |
| OK | Buceador (escritorio): móvil con selector de prefijo y casilla de permiso de WhatsApp |
| OK | Buceador (escritorio): aviso «Revisa el número…» con un número corto y sin aviso con el correcto |
| OK | Buceador (escritorio): sin errores de JavaScript ni de política de contenido |
| OK | Buceador (escritorio): ninguna página más ancha que la pantalla |
| OK | Freelance (escritorio): sin errores de JavaScript ni de política de contenido |
| OK | Freelance (escritorio): ninguna página más ancha que la pantalla |
| OK | Visitante (movil): sin errores de JavaScript ni de política de contenido |
| OK | Visitante (movil): ninguna página más ancha que la pantalla |
| OK | Buceador (movil): móvil con selector de prefijo y casilla de permiso de WhatsApp |
| OK | Buceador (movil): aviso «Revisa el número…» con un número corto y sin aviso con el correcto |
| OK | Buceador (movil): sin errores de JavaScript ni de política de contenido |
| OK | Buceador (movil): ninguna página más ancha que la pantalla |
| OK | Freelance (movil): sin errores de JavaScript ni de política de contenido |
| OK | Freelance (movil): ninguna página más ancha que la pantalla |
| OK | Confirmación: salida, recuento por canal, nombres con inicial, dinero y mensaje por idioma |
| OK | El botón queda desactivado hasta escribir la fecha |
| OK | Escribiendo la fecha se activa el botón |
| OK | Tras confirmar: «Deshacer» y cuenta atrás antes de enviar |
| OK | Panel de estado: cada buceador y canal |
| OK | Centro (escritorio): sin errores de JavaScript ni de política de contenido |
| OK | Centro (escritorio): ninguna página más ancha que la pantalla |
| OK | Cambio de hora: la salida y las reservas pasan a las 10:30 |
| OK | Centro (móvil): sin errores de JavaScript ni de política de contenido |
| OK | Centro (móvil): ninguna página más ancha que la pantalla |
| OK | Devolución en la cuenta Stripe del centro (una sola vez) |
| OK | Ningún aviso a reservas del segundo centro |
| OK | WhatsApp de prueba guardado en local, en la carpeta del centro |
| OK | Correo de la cancelación con el motivo y la nota del centro |
| OK | Correo del aviso guardado en local (entorno de pruebas: nunca se envía) |
| OK | Enlace del aviso (escritorio): abre solo esa reserva |
| OK | Buceador con aviso (escritorio): sin errores de JavaScript ni de política de contenido |
| OK | Buceador con aviso (escritorio): ninguna página más ancha que la pantalla |
| OK | Enlace del aviso (movil): abre solo esa reserva |
| OK | Buceador con aviso (movil): sin errores de JavaScript ni de política de contenido |
| OK | Buceador con aviso (movil): ninguna página más ancha que la pantalla |
| OK | Segundo centro: la reserva del primero da 404 |
| OK | Segundo centro: sin errores de JavaScript ni de política de contenido |
| OK | Segundo centro: ninguna página más ancha que la pantalla |
| OK | Exportación «bookings» del centro |
| OK | Exportación «clients» del centro |
| OK | Exportación «payments» del centro |
| OK | Justificante PDF de una reserva del centro |
| OK | Justificante PDF de otro centro: 404 |
| OK | Administración: el motivo se pide y queda en el registro |
| OK | Administración: sin errores de JavaScript ni de política de contenido |
| OK | Administración: ninguna página más ancha que la pantalla |
| OK | Sin errores 500 del servidor en todo el recorrido |

**Total: 53 OK, 0 fallos.**
