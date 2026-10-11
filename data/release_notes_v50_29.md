# WORLDIVES DISCOVERY v50.29: pagos de confianza, área personal, promociones con QR y temporadas

## Portada y temporadas
- La portada vuelve a ser una sola foto fija: ya no cambia de imagen.
- Nuevo en Administración → Imágenes de la web: **Temas de temporada**.
  - Cada tema tiene su nombre, su color principal (Océano, Coral, Tropical, Atardecer, Invierno, Abisal), una frase opcional en la portada y sus propias fotos de portada para cada sección.
  - Se muestra por fechas cada año (por ejemplo, del 1 de junio al 31 de agosto) o «ahora, hasta que lo cambie». También se puede dejar como borrador.
  - Zona: para todo el mundo, solo el hemisferio norte o solo el hemisferio sur. El hemisferio se deduce de la zona horaria del visitante, porque en Australia o Argentina el verano es en enero.
  - Si coinciden dos temas, gana el activado a mano y, si no, el de fechas más cortas: una campaña de dos semanas se impone a toda la temporada.
  - Botón «Vista previa» para ver la web con el tema antes de publicarlo. Solo la ves tú.
  - Arriba se indica qué tema ve ahora cada hemisferio.
  - Fuera de las fechas de cualquier tema se ve el aspecto original.

## Pagos: seguros y claros para el cliente
- **Confirmación inmediata.** Al volver de Stripe, la web comprueba el pago con el banco en el momento. No espera al aviso de Stripe (webhook). La reserva pasa a «Confirmada · Pagado» y el cliente recibe un mensaje.
- **Comprobación de cada cobro.** Se verifica que el importe y la moneda cobrados coincidan exactamente con la reserva.
  - Si algo no cuadra, el pago queda «en revisión» y la reserva no se confirma sola.
  - El administrador lo resuelve en la nueva pestaña **Pagos**: «Aceptar» confirma la reserva; «Devolver» la marca para devolución y avisa al cliente.
- **Revisión automática cada 5 minutos.**
  - Los pagos cuyo aviso de Stripe no llegó se confirman igualmente.
  - Los pagos abandonados liberan las plazas.
  - Si el cliente cancela en la página de Stripe, las plazas se liberan al momento y vuelve a su reserva con un aviso: «no se te ha cobrado nada».
- **Corregido:** al abandonar un pago podían liberarse plazas que el centro ya había confirmado. Ahora solo se liberan las que reservó ese pago.
- **Si un centro aún no tiene los cobros online activos**, la reserva no da error: se reserva sin pagar y se indica «Pagas en el centro». Este era el problema al reservar.
- **Lo que ve el cliente:**
  - Al reservar, un panel «Pago 100 % seguro»: Stripe con 3D Secure, la tarjeta nunca pasa por WORLDIVES ni por el centro, y las tarjetas aceptadas.
  - Página de pago completado con el ticket: actividad, fecha, importe, tarjeta (Visa ···· 4242), nº de reserva y referencia del pago. Enlaces al justificante PDF y al recibo de Stripe.
  - En «Mi reserva», una tarjeta de pago con su estado real: pagado (fecha, tarjeta, recibo), pendiente (botón «Pagar ahora de forma segura»), en curso, en revisión o «pago en el centro».
- **Panel del administrador → Pagos:**
  - Todos los cobros, con los que están en revisión primero.
  - Totales cobrados y comisión de WORLDIVES.
  - Comprobación de que la clave de Stripe y el webhook están configurados.

## Reseñas
- Se puede escribir una reseña en cuanto la reserva está pagada o confirmada. Antes había que esperar a que el centro la marcara como completada, y por eso «no se podían poner».
- En la reserva aparece «¿Qué tal con el centro? Escribir reseña», que lleva directo al formulario.

## Comprobante PDF (para tenerlo sin internet)
- Rediseñado por completo:
  - Cabecera con el nº de reserva (WOD-000123).
  - Estado de la reserva y del pago en color.
  - Fecha escrita («Domingo, 11 de octubre de 2026»).
  - Detalles de la inmersión y QR de verificación.
  - Desglose del importe con la tarjeta usada.
  - Datos del centro y lista «Antes de bucear».
- Etiquetas en español e inglés para centros extranjeros.
- Ahora se ven bien las tildes y la ñ (Galápagos, Inmersión, Teléfono). También en la ficha operativa del centro.

## Área personal (buceador)
- Mi área, Log Book, Recompensas, Monedero y Mi cuenta comparten ahora:
  - la misma cabecera, con tu nombre y tu nivel;
  - las mismas pestañas;
  - el mismo diseño.
- **Mi área:**
  - Resumen con próximas reservas, pagos pendientes, mensajes y documentos (aviso si caducan).
  - Tarjeta de tu próxima inmersión: cuenta atrás, PDF sin conexión y «Cómo llegar».
  - Reservas en «Próximas» e «Historial».
  - Progreso de tu ficha de buceador, mensajes y documentación.
- **Log Book:**
  - Totales: inmersiones, profundidad máxima, tiempo bajo el agua y países.
  - Historial numerado por años, con buscador.
  - Añadir, editar y borrar inmersiones, y exportar a CSV. Se comprueban las fechas y que las profundidades sean posibles.
- **Recompensas:**
  - Nivel y progreso.
  - **Mis promociones**, con su QR.
  - Recompensas para canjear, indicando cuánto saldo te falta.
  - Logros agrupados («Inmersión registrada ×40»).
- **Monedero:**
  - Saldo destacado y movimientos con entradas y salidas.
  - Códigos de canje con botón para copiarlos.
  - «Cómo funciona».
- **Mi cuenta:**
  - Ficha por bloques: datos personales, titulación y seguridad, equipo y tallas.
  - Botón de guardar siempre visible.
  - Documentación, tus centros, y cambio de contraseña (cierra las demás sesiones).
  - Ahora también puedes cambiar tu nombre.

## Promociones con QR (centro → Check-in / QR y promociones)
- El centro crea una promoción, por ejemplo «Curso Open Water + 1 año de equipo gratis»:
  - lo que recibe el cliente;
  - las condiciones;
  - la fecha de caducidad;
  - los usos por cliente (1 o, para bonos, hasta 50).
- «Dar a clientes»: eliges clientes de tu base, con buscador y «seleccionar todos». Cada uno recibe un **QR personal** en Recompensas → Mis promociones y un aviso en su buzón.
- **Cadenas de centros:** al crear la promoción puedes invitar a otros centros.
  - El centro invitado la acepta o la rechaza desde su panel.
  - Solo después de aceptar puede canjearla. Así nadie se compromete a algo que no ha aceptado.
- **Validar:** el centro escanea el QR con la cámara del móvil o escribe el código.
  - Ve en grande «Promoción activa» o el motivo por el que no vale: caducada, ya utilizada, anulada o no válida en tu centro.
  - Pulsa «Canjear ahora» y queda registrado qué centro la usó y cuándo.
- Lista de códigos por promoción, con el uso de cada cliente y opción de anular un código. También se puede finalizar o reactivar la promoción.
- Privacidad: quien escanea el QR sin ser el titular ni uno de los centros de la promoción no ve el nombre ni el email del cliente.

## Panel del profesional freelance
- Mismo diseño que el panel del centro, con menú lateral: Resumen, Planning, Servicios y tarifas, Experiencias y solicitudes, y Perfil público.
- El Resumen muestra:
  - las próximas salidas y las solicitudes pendientes (también con contador en el menú);
  - el progreso de tu ficha pública;
  - un botón para copiar el enlace de tu ficha.
- Perfil público con vista previa de la foto, contador de caracteres de la presentación y redes sociales.

## Top 10
- El radio máximo es 500 km (25, 50, 100, 250 y 500 km). El servidor también lo limita.

## Comprobado
- Prueba nueva v50.29 con 44 comprobaciones en un navegador real, todas superadas:
  - temas;
  - pago completo hasta el recibo;
  - PDF;
  - reseñas;
  - promociones entre dos centros (canje, aceptación y anulación);
  - área personal en ordenador y móvil;
  - panel freelance;
  - Top 10.
- Pagos probados con un simulador de Stripe en tres casos: pago correcto, pago sin completar (cancelar libera las plazas) e importe distinto (queda en revisión).
- Pruebas anteriores al día: v50.24, Centros y Tipos, imágenes, reserva y v50.26/27/28.
- Recorrido de páginas con los 5 roles y pruebas con datos erróneos en todas las rutas: sin errores internos.
- Clic en cada botón de cada pantalla con los 5 roles: 2.225 pruebas. Lo que no reaccionaba eran formularios vacíos (bloqueados a propósito) y confirmaciones canceladas.
- Textos nuevos traducidos a los 10 idiomas: 625 frases y 80 plantillas, sin ninguna falta ni variable rota. Revisión en inglés, alemán y japonés: solo quedan en español los nombres propios y lo que escribe cada centro.
- Carga con 3.000 personas en 3 minutos: 0 errores.

## Idiomas
- Todo lo nuevo (área personal, pagos, promociones, temas, panel freelance y administración) está traducido a los 10 idiomas.
- Los nombres de las personas ya no se traducen por error: por ejemplo, un usuario llamado «Buzo» se mostraba como «Diver».
- Corregido «Top 10 cerca de ti» en el pie de página, que salía a medias en algunos idiomas.

**Instalación:** copia los archivos del zip encima de la versión anterior. La base de datos se actualiza sola al arrancar: se añaden tablas nuevas y no se borra nada.

**Pagos reales:** hacen falta `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` y `WOD_PUBLIC_URL`. En el panel de Stripe, el webhook debe apuntar a `/api/payments/webhook` con los eventos `checkout.session.completed` y `checkout.session.expired`.
