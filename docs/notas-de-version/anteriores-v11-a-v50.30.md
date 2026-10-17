# Notas de versión anteriores (v11 a v50.30)

Las notas de las versiones anteriores a la v50.31 estaban sueltas en `data/` (42 archivos). En la v50.46 se reúnen aquí,
la más reciente arriba, sin cambiar su texto. Las notas desde la v50.31 están en esta misma carpeta, una por versión.


---

<!-- release_notes_v50_30.md -->

# WORLDIVES DISCOVERY v50.30: documentación legal, correos automáticos, cancelaciones con devolución, Explorar, Top 10 preciso y puntos de Jávea

## Documentación legal (nuevo)
Diez documentos completos, en español y en inglés, en `#/legal/…` y enlazados en el pie de todas las páginas:

| Documento | Para qué sirve |
|---|---|
| Aviso legal | Datos del titular (LSSI-CE art. 10), propiedad intelectual y responsabilidad. |
| Condiciones de uso | La plataforma como intermediario, cuentas para mayores de 18 años, uso correcto, retirada de contenidos. |
| Condiciones de reserva, pago y cancelación | Tipos de reserva, precio final, pago con Stripe, sin derecho de desistimiento en actividades con fecha (art. 103.l TRLGDCU), cancelaciones y devoluciones. |
| Política de privacidad | RGPD y LOPDGDD: datos, finalidades, bases legales, destinatarios (centros, Stripe, alojamiento, correo, mapas), plazos y derechos. |
| Política de cookies | Solo hay cookies técnicas, que no necesitan consentimiento. Incluye una tabla de cada cookie. |
| Condiciones para centros y profesionales | Reglamento P2B (UE 2019/1150): verificación, obligaciones, comisión, Stripe Connect, devoluciones, aviso de cambios con 15 días y de cierre con 30 días, reclamaciones. |
| Política de reseñas | Solo reseñan clientes con reserva (reseñas verificadas); no se ocultan las negativas. |
| Cómo ordenamos los resultados | Criterios del directorio y del Top 10, según la Directiva Ómnibus. Ningún centro paga por posición. |
| Denunciar contenido | Formulario según la Ley de Servicios Digitales (DSA), con acuse de recibo y decisión por email. |
| Seguridad en el buceo | Advertencias y responsabilidad sobre la información de los puntos. |

- **Datos del titular:** se rellenan en **Administración → Legal** (nombre o razón social, NIF, domicilio, email, teléfono, registro, alojamiento, comisión). Se insertan solos en los documentos y en el pie de los correos. Mientras falten, el texto muestra «pendiente de completar».
- **Aviso de cookies:** solo informativo, porque no hay cookies de publicidad ni de analítica.
- **Registro:** casilla obligatoria de condiciones, privacidad y mayoría de edad. Las cuentas profesionales aceptan además las condiciones para centros. Se guarda qué versión aceptó cada usuario.
- **Centros y freelance existentes:** ven un aviso para aceptar las condiciones para centros.
- **Reserva:** antes de pagar se muestran la política de cancelación del centro y las condiciones de reserva. Cada reserva guarda la versión de las condiciones.
- **Mi cuenta → Privacidad y datos:**
  - descargar todos tus datos (JSON);
  - eliminar la cuenta (con contraseña). Se borran o anonimizan los datos personales; los pagos se conservan anonimizados por obligación legal.
- **Denuncias (DSA):** se gestionan en Administración → Legal, con decisión motivada y aviso a quien denunció.
- ⚠️ **Los textos son plantillas completas, pero deben revisarlos un abogado antes de publicar la web.**

## Correos automáticos (nuevo)
33 plantillas con diseño de la marca, en el idioma de cada destinatario: español más 10 idiomas, igual que la web.

| Para | Correos |
|---|---|
| Buceador | Bienvenida; solicitud enviada; reserva confirmada (con PDF y «antes de bucear»); plaza aceptada y pago pendiente; recibo de pago; pago en revisión; solicitud rechazada; cancelada por el centro (con devolución); cancelada por ti (con devolución según política); recordatorio el día anterior; petición de reseña; promoción recibida; viajes (solicitud y respuesta); cuenta eliminada; restablecer contraseña y aviso de contraseña cambiada. |
| Centro y freelance | Bienvenida profesional; nueva reserva o solicitud; pago recibido; cancelación del cliente; agenda de mañana (cada tarde, con buceadores y equipo); invitación a promoción; solicitud de viaje; perfil verificado. |
| Administración | Nueva cuenta profesional; pago en revisión; devolución fallida; denuncia de contenido. |

- **Funcionamiento:**
  - Cada correo se prepara en el momento del evento y se guarda en una cola.
  - Un proceso en segundo plano lo envía por SMTP, con reintentos.
  - Si el correo aún no está configurado, no se pierde nada: los correos esperan en la cola.
- **Administración → Correos:**
  - estado del envío y botón de correo de prueba;
  - contadores por estado y lista de todos los envíos con buscador;
  - ver cada correo tal como llegó y reenviarlo;
  - vista previa de cada plantilla en cada idioma.
- **Recuperar la contraseña:** enlace «¿Has olvidado tu contraseña?» en el inicio de sesión. El enlace caduca en 1 hora, sirve una sola vez y cierra las demás sesiones.
- **Configurar el correo corporativo:** cuando lo tengas, añade estas variables al arrancar el servidor y reinicia. Después pulsa «Enviar prueba» en Administración → Correos.
  ```
  WOD_SMTP_HOST=smtp.hostinger.com
  WOD_SMTP_PORT=465
  WOD_SMTP_SECURITY=ssl          (o starttls con el puerto 587)
  WOD_SMTP_USER=reservas@tudominio.com
  WOD_SMTP_PASSWORD=********
  WOD_MAIL_FROM=reservas@tudominio.com
  WOD_MAIL_FROM_NAME=WORLDIVES DISCOVERY
  WOD_MAIL_REPLY_TO=info@tudominio.com   (opcional)
  ```

## Cancelaciones y devoluciones (nuevo)
- **Política de cada centro:** se elige en **Panel → Cobros y pagos** y se ve en la ficha, al reservar y en la reserva.
  - Flexible: gratis hasta 24 h antes.
  - Moderada (por defecto): gratis hasta 48 h antes.
  - Estricta: gratis hasta 7 días antes.
- **El buceador cancela** desde «Mi reserva»: antes de confirmar ve exactamente cuánto se le devuelve.
  - Dentro de plazo: devolución automática del 100 % con Stripe, revirtiendo la transferencia al centro y la comisión.
  - Fuera de plazo: sin devolución.
  - Las plazas se liberan solas.
- **Cuando cancela o rechaza el centro**, el cliente recibe siempre la devolución íntegra automáticamente.
- Si Stripe fallara, la devolución queda «pendiente» y el administrador recibe un aviso.
- **Corregido:** al aceptar una solicitud de un centro sin cobros online, la reserva quedaba como «pago pendiente». Ahora queda «pago en el centro».

## Explorar
- Mismo estilo que el resto de la web:
  - cabecera con foto, editable en Imágenes de la web;
  - cifras de puntos, países y zonas;
  - tarjeta de filtros y mapa.
- **Botón «Volver» corregido:** quedaba detrás del mapa y solo se leía «ver». Ahora está siempre por encima, en todas las páginas con mapa.
- **Marcadores:** ahora son la bandera de buceo, roja con franja blanca en diagonal, con el mismo tamaño discreto.

## Top 10: ubicación precisa
- **Por qué fallaba:** el navegador del ordenador daba una ubicación por la conexión a internet, no por GPS, con cientos de kilómetros de error. Por eso, estando en Dénia, salía Islas Cíes a 302 km.
- **Lectura del GPS:** «Usar mi ubicación» escucha el GPS hasta 12 segundos y se queda con la lectura más precisa. Muestra la precisión, por ejemplo «± 25 m».
- **Ubicación imprecisa:** si el margen supera los 20 km, no se muestra un ranking engañoso. Aparece un aviso claro con tres opciones: **Elegir en el mapa**, **Escribir mi localidad** o «Usar igualmente».
- **Nuevo buscador de localidad:** por ejemplo, Dénia o Jávea.
- **Nuevo «Elegir en el mapa»:** tocas el mapa donde estás.
- La elección se recuerda para la próxima visita.

## Puntos de buceo reales en Jávea y alrededores (10 nuevos)
Posiciones comprobadas en fuentes oficiales y de buceo (sin guardar la fuente en la web):

- **Dénia:**
  - La Barra (Les Marines);
  - La Cullerà (Reserva Marina del Cabo de San Antonio, con autorización);
  - Les Rotes · El Fresquito.
- **Xàbia:**
  - El Tangó;
  - María Claudia (Mona de l'Illa);
  - Escull de Sant Pere (El Bergantí);
  - Isla del Descubridor;
  - La Granadella.
- **Benitatxell:** El Moraig · Cova dels Arcs.
- **Calp / Altea:** Acantilados del Mascarat (La Bodega).

Cada punto incluye tipo de inmersión, nivel, profundidades cuando la fuente las da, acceso y descripción. No se ha inventado ningún dato.

Otros puntos conocidos se han dejado fuera porque no tienen una posición fiable publicada: el pecio Felguera (El Vaporet), Las Gorgonias, Cova Tallada y Cala Andragó. Un centro local puede darte su GPS y se añaden desde Administración → Puntos.

## Comprobado
- **Prueba del servidor:** 199 comprobaciones, todas correctas:
  - reserva inmediata, por solicitud y con pago;
  - cancelaciones dentro y fuera de plazo, con su devolución;
  - cancelación y rechazo por el centro;
  - pago en revisión;
  - restablecer la contraseña;
  - documentos legales en 3 idiomas;
  - denuncias;
  - exportar y eliminar la cuenta;
  - vista previa de las 33 plantillas en 4 idiomas;
  - envío real por SMTP.
- **Prueba en navegador real:** 52 comprobaciones, todas correctas:
  - Top 10 con GPS preciso, impreciso, mapa y buscador;
  - «Volver» en Explorar en ordenador y móvil;
  - marcadores;
  - los 10 documentos legales;
  - aviso de cookies;
  - registro con condiciones;
  - recuperar la contraseña;
  - cancelar una reserva;
  - política del centro;
  - administración de correos y legal.
- **Carga: 10.000 visitantes en 15 minutos**, con un catálogo de producción:
  - 528 centros, 4.100 cuentas, más de 100.000 reservas y 130.000 salidas.
  - Resultado: 110.234 peticiones (121 por segundo) y **0 errores**.
  - La mitad de las respuestas tardan 4 ms o menos; el 95 % tardan 18 ms o menos. Entrar y registrarse tardan unos 90 ms, porque la contraseña se cifra de forma segura a propósito.
  - Durante la prueba se prepararon y enviaron por SMTP 8.284 correos, y la cola quedó vacía al terminar.
  - El envío de correos se ha optimizado: los envía por lotes con una sola conexión, a unos 190 por segundo en la prueba local.
- **Clic en cada botón de cada pantalla con los 5 roles:** 1.920 pruebas.
  - Ningún error de JavaScript ni del servidor.
  - Los avisos que quedan son de la propia prueba: elementos en movimiento, como el carrusel de logos, o validaciones esperadas, como «Adjunta una foto».
- Instalación limpia sobre la v50.29 probada: arranca en v50.30, migra la base de datos y añade los puntos.
- **Corregido también:**
  - las ventanas emergentes se quedaban abiertas al cambiar de página;
  - el aviso de cookies tapaba el botón de reservar en el móvil;
  - un visitante que cierra la página a media petición ya no deja errores en el registro.

**Instalación:** detén el servidor, copia el contenido del zip encima de la carpeta actual y vuelve a arrancar. La primera línea debe decir `WORLDIVES DISCOVERY v50.30`. La base de datos se actualiza sola: se añaden tablas y puntos nuevos y no se borra nada.

---

<!-- release_notes_v50_29.md -->

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

---

<!-- release_notes_v50_17.md -->

# WORLDIVES DISCOVERY v50.17 — Restauración del catálogo público + aislamiento de datos de cuentas

- Se restaura el catálogo público existente de la versión original: 28 centros de buceo, 283 puntos de buceo, certificaciones y contenido público asociado.
- La base de datos parte sin usuarios registrados ni datos operativos de cuentas: reservas, servicios de centros, QR, extras, tarifas, vínculos de check-in y perfiles de usuario quedan a cero.
- Se mantiene la gestión avanzada del centro introducida en las versiones 50.10–50.16.
- La cuenta de centro gestiona exclusivamente su centro asociado; la navegación pública sigue permitiendo consultar otros centros, puntos y tipos de buceo.
- El QR continúa siendo una herramienta de la gestión interna del centro y no sustituye ni limita el catálogo público.

---

<!-- release_notes_v50_9.md -->

# WORLDIVES DISCOVERY v50.9 — Security hardening

- Seguridad interna reforzada sin cambiar los flujos de negocio.
- El password_hash nunca se devuelve por `/api/me`.
- Cookies de sesión HttpOnly + SameSite=Lax y Secure automático bajo HTTPS.
- Sesiones con expiración configurable (8 h por defecto).
- Protección de origen para peticiones POST/DELETE con Origin/Referer.
- Rate limit básico de login (8 intentos / 15 min por IP + identificador).
- Cabeceras de seguridad HTTP.
- Servidor local enlazado a 127.0.0.1 por defecto; el modo LAN lo habilita explícitamente.
- `.gitignore`, `SECURITY.md` y workflow de comprobaciones para GitHub.
- Eliminados sidecars WAL/SHM del paquete de distribución.

---

<!-- release_notes_v50_8.md -->

# WORLDIVES DISCOVERY v50.8 — traducción completa de interfaz

- Ampliada la capa de internacionalización del frontend.
- Traducidos encabezado, pie, navegación, buscador, portada y Top 10.
- Traducidas las pantallas de inicio de sesión, registro y primera instalación.
- Traducidos menús de cuenta, estados, reservas, QR y acciones habituales.
- La traducción se aplica también a contenido dinámico generado por las vistas cuando coincide con el catálogo de interfaz.
- Los mensajes de toast pasan por la misma capa de traducción.
- Se mantiene el selector de 11 idiomas de v50.7.
- No se modifica la lógica de reservas, pagos, usuarios, centros, servicios, salidas, administración, PDFs, QR ni base de datos.

---

<!-- release_notes_v50_7.md -->

# WORLDIVES DISCOVERY v50.7 — International language coverage

- Expanded the discreet header language selector from 6 to 11 languages: Spanish, English, French, German, Italian, Portuguese, Dutch, Japanese, Korean, Simplified Chinese and Traditional Chinese.
- Expanded the same language list in the user profile preference.
- Added localized date formatting for all supported languages.
- Expanded the existing interface translation dictionary for the principal navigation, booking, search, account and Top 10 interface labels.
- User-generated content such as dive-site names, center names, descriptions and reviews remains unchanged.
- No backend, database, booking, payment, authentication, PDF, QR, map or business logic was changed.

---

<!-- release_notes_v50_6.md -->

# WORLDIVES DISCOVERY v50.6 — International language selector

- Added a discreet language selector in the top-right header.
- Supported languages: Spanish, English, French, German, Italian and Simplified Chinese.
- Language preference is stored locally and survives navigation/reloads.
- Main navigation, account menu, common actions, search, booking labels and core interface copy are translated without changing routes, data or business logic.
- Dates now use the selected language locale.
- User-generated content such as dive-site names, center names, descriptions and reviews remains in its original language unless a translated version is explicitly stored; this prevents accidental alteration of catalog data.
- No backend, database, booking, payment, PDF or authentication logic was changed.

---

<!-- release_notes_v50_5.md -->

# WORLDIVES DISCOVERY v50.5

## Top 10 buceos local

- Añadida la pestaña **Top 10 buceos** junto a Experiencias.
- La nueva sección solicita la ubicación del navegador y calcula los 10 puntos de buceo más recomendables dentro de un radio local.
- La distancia se utiliza para priorizar la zona y las reseñas disponibles de centros asociados aportan la señal de valoración cuando existen.
- Si todavía no hay reseñas suficientes, se muestra claramente que la selección procede del catálogo curado y la proximidad.
- No se guardan las coordenadas del visitante: se usan para solicitar el ranking al servidor y no se persisten.
- La funcionalidad existente de reservas, pagos, perfiles, centros, servicios, salidas, logbook y PDF no se modifica.

---

<!-- release_notes_v50_3.md -->

# WORLDIVES DISCOVERY v50.3

- PDF generation reverted to the built-in PDF generator so the application does not require ReportLab/Pillow to be installed separately.
- Kept the existing QR generation through the already-declared `qrcode` dependency.
- Kept reservation, authentication, booking, payment, centre, diver and admin logic unchanged.
- Receipt endpoints `/api/bookings/{id}/receipt` and `/api/bookings/{id}/receipt.pdf` remain compatible.
- Diver sheet endpoint `/api/bookings/{id}/diver-sheet.pdf` remains compatible.

---

<!-- release_notes_v50_2.md -->

# WORLDIVES DISCOVERY v50.2 — documentos profesionales e identidad de marca

- Rediseño visual de los PDF de confirmación de reserva y ficha operativa del buceador.
- PDF generado con ReportLab, con maquetación profesional, estados, bloques de información, identidad visual, QR de verificación y pie documental.
- Se mantiene la descarga como archivo PDF y los endpoints anteriores son compatibles.
- Se añade `reportlab` como dependencia explícita.
- Revisión de textos visibles de la web para utilizar la denominación oficial **WORLDIVES DISCOVERY** y eliminar variantes incorrectas como “WORLD DIVES” o “World Dives”.
- No se modifica la lógica de reservas, pagos, perfiles, centros, servicios, salidas o permisos.

---

<!-- release_notes_v50_1.md -->

# WORLDIVES DISCOVERY — v50.1 PDF fix

- Fixed the reservation receipt PDF query: user phone numbers live in `user_profiles`, not `users`.
- Fixed the operational diver-sheet PDF query for the same schema issue.
- Kept the previous `/api/bookings/{id}/receipt` endpoint for compatibility.
- Added `/api/bookings/{id}/receipt.pdf` as the canonical PDF endpoint.
- Updated customer-facing PDF links in Mi área / Reserva to use the `.pdf` endpoint.
- Added receipt + QR and operational PDF actions to the center reservation view.
- PDF generation validated as a readable 1-page PDF with QR using a representative booking fixture.
- Existing authorization is preserved: owners can access their own reservation documents; centers can access reservations belonging to their center; administrators retain access.

---

<!-- release_notes_v47.md -->

# WORLDIVES v47 — Gestión de salidas y cobros

- Añadida eliminación individual de salidas programadas sin borrar el servicio.
- Una salida con reservas activas no puede eliminarse para preservar la integridad de las reservas.
- El calendario de Servicios y salidas muestra un resumen inline al pulsar un día: horarios, servicio, puntos, capacidad y plazas disponibles.
- La pantalla de Cobros y pagos del centro ya no muestra la comisión de WORLDIVES ni el importe neto; mantiene únicamente el total cobrado y número de pagos.
- Se mantienen los datos y la lógica de pagos profesionales de Stripe Connect.

---

<!-- release_notes_v40.md -->

# WORLDIVES DISCOVERY · v40

## Reseñas y valoraciones de centros
- Se añade un sistema real de valoraciones de 1 a 5 estrellas para centros de buceo.
- Las reseñas verificadas solo pueden publicarse después de completar una inmersión con ese centro.
- Cada buceador dispone de una única reseña por centro y puede actualizarla.
- La ficha pública del centro muestra media de estrellas, número de reseñas y reseñas recientes.
- Las reseñas muestran la etiqueta de inmersión verificada.
- El listado de centros permite ordenar por mejor valorados o por número de reseñas.
- Los centros asociados a un punto de buceo también muestran su valoración para facilitar la comparación.
- Se mantienen los flujos existentes de reservas, perfiles, puntos y gestión profesional.

---

<!-- release_notes_v39.md -->

# WORLDIVES DISCOVERY · v39

## Corrección crítica de reservas para perfiles no profesionales

- El catálogo de puntos asociados a un centro ya puede consultarse desde el flujo de reserva por usuarios `recreational` y `freelance` autenticados.
- Los usuarios `center` siguen viendo únicamente los puntos de su propio centro.
- El administrador puede consultar cualquier centro.
- Se valida que el centro solicitado esté activo antes de devolver sus puntos.
- El formulario de reserva carga puntos y actividades de forma independiente: si falla una fuente de catálogo, la otra sigue disponible y el error no bloquea toda la reserva.
- Se mantiene la misma lógica de plazas, salidas, pagos, solicitudes y permisos de la v38.

---

<!-- release_notes_v38.md -->

# WORLDIVES DISCOVERY v38 — Buscador controlado y perfiles verificados

- El buscador rápido de portada muestra sugerencias mientras se escribe, pero **no desplaza ni hace zoom automáticamente**.
- El desplazamiento suave al mapa y el `flyTo`/encuadre animado se ejecutan únicamente al pulsar **Buscar** o Enter.
- Las sugerencias de puntos y centros pueden seleccionarse para completar el campo sin mover la página.
- Las búsquedas que coinciden con varios puntos mantienen todos los resultados relevantes y el mapa encuadra el conjunto.
- La búsqueda de centros utiliza también sus coordenadas para llevar el mapa a la zona cuando corresponde.
- Se reforzó el funcionamiento del modo buceador/recreativo: reservas, detalle de reserva, recibo PDF, área, Log Book, recompensas y monedero.
- El modo freelance puede utilizar también el flujo de cliente para sus propias reservas y actividades de buceo, además de su panel profesional.
- Se corrigió el control de acceso de reservas: los perfiles no administrativos solo pueden consultar sus propias reservas; el centro solo las de su centro.
- El centro mantiene acceso a la ficha operativa y PDF interno del buceador.
- Se comprobó el flujo de centro: puntos asociados, servicios, salidas, reservas, confirmación y ficha PDF.
- Se comprobó el flujo administrativo principal y los endpoints de gestión.

---

<!-- release_notes_v37.md -->

# WORLDIVES DISCOVERY v37 — Búsqueda con transición al mapa

- Al pulsar Buscar desde el buscador rápido de la portada, la página hace scroll suave hasta el mapa.
- Si la búsqueda encuentra un único punto con coordenadas, el mapa hace `flyTo` animado y acerca el zoom al punto.
- Si encuentra varios puntos, el mapa ajusta el encuadre con una animación para mostrar todos los resultados.
- Se filtran visualmente los marcadores para destacar los resultados de la búsqueda.
- Al seleccionar un punto desde el desplegable, se realiza la misma transición al mapa y zoom animado.
- Se abre la ficha rápida del punto después del acercamiento cuando hay un único resultado.
- Se mantiene el buscador y el resto de funcionalidades de la v36.

---

<!-- release_notes_v35.md -->

# WORLDIVES DISCOVERY v35 — Buscador rápido mejorado

- El buscador de inicio ahora busca automáticamente mientras se escribe (desde 2 caracteres), sin necesidad de pulsar Buscar.
- Busca simultáneamente puntos de buceo y centros de buceo.
- Los puntos se filtran por nombre, país, región, subregión y descripción.
- Los resultados se ordenan por relevancia, priorizando coincidencias exactas y por nombre.
- Los centros se consultan mediante el catálogo real de centros.
- Resultados agrupados visualmente en «Puntos de buceo» y «Centros de buceo».
- Muestra el número total de coincidencias por grupo.
- Para Benidorm, el catálogo actual devuelve los 8 puntos disponibles, no solo el primero.
- Seleccionar un punto abre directamente su ficha/mapa; seleccionar un centro abre directamente su ficha.
- El desplegable tiene scroll propio y no queda limitado a una única sugerencia.
- Se mantiene la versión v34.1 y sus cambios de mapa, reservas y navegación.

---

<!-- release_notes_v34_1.md -->

# v34.1 — Ajuste de controles del mapa

- Controles +/− del mapa pasan a la esquina inferior derecha.
- Selector Mapa/Satélite/Relieve marino/Mundo permanece arriba a la izquierda.
- Panel informativo del mapa queda separado arriba a la derecha en escritorio.
- En móvil se evita que el panel informativo ocupe espacio y el selector permanece en una sola fila desplazable.
- Se mantienen reservas y navegación de v34 sin cambios funcionales.

---

<!-- release_notes_v34.md -->

# WORLDIVES DISCOVERY v34 — navegación y mapa

- El botón «Volver» ya no aparece en la página de inicio.
- «Volver» queda alineado a la derecha, con diseño discreto y consistente.
- El botón vuelve mediante historial del navegador cuando existe navegación previa.
- En los mapas principales, los controles de zoom pasan a la esquina superior derecha.
- El selector Mapa/Satélite/Relieve marino/Mundo permanece separado en la esquina superior izquierda.
- Responsive: el botón Volver se compacta en móvil/tablet y los controles del mapa mantienen zonas independientes.

---

<!-- release_notes_v33.md -->

# WORLDIVES DISCOVERY v33 — Ficha operativa y navegación

- La vista que recibe un centro al abrir una reserva se separa de la vista del cliente.
- El centro ve una ficha operativa del buceador: identidad, contacto, certificación, equipo/preferencias y documentación.
- Se eliminan de la ficha del centro los comandos repetidos de confirmar/rechazar/pagar y los datos de fecha/hora de la reserva.
- Añadida descarga de ficha operativa interna en PDF.
- La ficha mantiene acceso individual a los documentos aportados por el buceador.
- Añadido botón global de volver atrás en la interfaz.
- La ficha de un punto de buceo muestra primero exclusivamente los centros que tienen ese punto asociado.
- Si ningún centro realiza todavía ese punto, muestra centros cercanos (hasta 60 km), ordenados por distancia.
- Los centros cercanos no se mezclan con centros de otros países/regiones sin relación geográfica.
- Mantiene el flujo de reservas funcional de v32.

---

<!-- release_notes_v31.md -->

# WORLDIVES DISCOVERY v31 — Reserva de cliente simplificada

- Rediseño del flujo de reserva en 4 pasos: centro/punto, actividad/salida, participantes y extras.
- Los puntos asociados al centro se muestran como tarjetas; cada punto muestra próximas fechas programadas.
- Al seleccionar un punto, solo aparecen las salidas programadas en ese punto.
- La fecha y hora manuales dejan de aparecer cuando existe una salida programada: se elige directamente la salida.
- Las salidas muestran disponibilidad en tiempo real: última plaza, quedan X plazas, etc.
- El cliente puede seleccionar equipo mediante opciones visuales en lugar de escribirlo libremente.
- Los precios de alquiler de equipo pueden ser configurados por el centro desde Mi centro.
- Añadido catálogo base de equipo: aletas, máscara, traje, regulador, BCD, botella, ordenador y equipo completo.
- Guía adicional mantiene un campo de notas libre.
- Nitrox y traslado quedan como extras simples.
- Diseño responsive específico para móvil/tablet.

---

<!-- release_notes_v29.md -->

# WORLDIVES DISCOVERY v29

## Centro de buceo: puntos, calendario y ficha operativa

- Nuevo catálogo de **Mis puntos de buceo** para cada centro: permite asociar puntos existentes del catálogo sin duplicarlos y crear uno nuevo cuando no exista.
- Los puntos asociados al centro pasan a aparecer en su ficha pública y en el flujo de reserva.
- Las salidas de servicios admiten uno o varios puntos de buceo mediante una relación independiente.
- Nuevo **calendario mensual** dentro de Servicios y salidas para planificar visualmente fecha, hora, servicio y puntos.
- Al reservar, el buceador puede elegir un punto y WORLDIVES muestra únicamente las salidas del centro previstas para ese punto.
- Las plazas continúan calculándose en servidor y se descuentan al confirmar/pagar la reserva.
- La ficha de reserva para el centro es diferente a la del cliente: no muestra el QR/acreditación, sino la **ficha operativa del buceador** con titulación, contacto, necesidades de equipo, tallas, preferencias y documentación disponible.
- La verificación QR pública muestra también el estado del pago para que el centro pueda comprobar reserva y pago al hacer check-in.
- El checkout de servicios en modo **Solicitud + confirmación** queda bloqueado hasta que el centro confirme la solicitud.

---

<!-- release_notes_v28.md -->

# WORLDIVES DISCOVERY v28

## Gestión de servicios más clara
- El centro/freelance puede eliminar servicios que todavía no tienen reservas asociadas.
- Los servicios con historial de reservas no se destruyen: se pueden desactivar para conservar el contexto histórico.
- La edición identifica claramente qué servicio se está modificando y explica que los cambios afectan al servicio y a futuras salidas.
- Se añadió una acción visible “Eliminar servicio” con confirmación.
- Se mantienen las salidas, plazas automáticas y los tres modos de reserva de la v27.

---

<!-- release_notes_v27.md -->

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

---

<!-- release_notes_v26.md -->

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

---

<!-- release_notes_v25.md -->

# WORLDIVES DISCOVERY v25 — botones del panel de centro funcionales

- Corregido el botón «Ver reserva» del dashboard del centro: ahora es un enlace real a `#/reserva?id=...` y no depende de un listener que solo se registraba en la pestaña Reservas.
- La ficha de reserva mantiene el acceso a centro, teléfono, PDF y QR.
- Se mantienen todas las funciones de v24.

---

<!-- release_notes_v24.md -->

# WORLDIVES DISCOVERY v24 · Panel profesional de operaciones

## Cambio principal
Se rediseña el panel de centro de buceo para que funcione como un cuadro de mando operativo diario.

### El centro ve primero
- Reservas por confirmar.
- Reservas confirmadas.
- Reservas pagadas e ingresos cobrados.
- Pagos pendientes.
- Salidas de hoy y participantes.
- Puntos de buceo activos del centro.
- Próximas salidas de los siguientes 7 días.
- Clientes asociados.
- Recompensas activas.

### Navegación profesional
- Resumen
- Reservas
- Servicios y salidas
- Clientes
- Puntos de buceo
- Recompensas
- Correcciones
- QR / Check-in
- Mi centro

La edición de la ficha del centro (datos, redes, logo/foto y descripción) deja de ocupar espacio permanente en el resumen y pasa a `Mi centro`.

## Compatibilidad
Se mantienen las funciones anteriores y las rutas de administración existentes. El panel conserva la gestión de reservas, servicios, puntos, clientes, recompensas, correcciones y QR.

---

<!-- release_notes_v23.md -->

# WORLDIVES DISCOVERY v23 — Centro de operaciones

- Reorganizado el panel de centros de buceo como cuadro de mando operativo.
- Nuevo inicio con KPIs de reservas pendientes, confirmadas, salidas de hoy, próximos 7 días, pagos registrados y clientes.
- Nueva agenda visual de reservas pendientes, salidas del día y próximos 7 días.
- Acciones rápidas para Reservas, Servicios y salidas, Clientes, Puntos, QR y Recompensas.
- Separada la gestión comercial de servicios y salidas en su propia pestaña, manteniendo la funcionalidad existente.
- Se conserva la edición de ficha del centro y todas las funciones previas.
- La vista de reservas admite acceso directo filtrado por estado desde el cuadro de mando.
- Responsive para tablet y móvil.

---

<!-- release_notes_v22.md -->

# WORLDIVES DISCOVERY v22 — Recuperación de puntos Xàbia y Costa Blanca

- Restaurados los 27 puntos mediterráneos que estaban en la versión anterior y se habían eliminado al retirar la categoría duplicada `Europe`.
- Todos vuelven bajo la categoría canónica `Europa`, sin crear un segundo bloque regional.
- Los puntos se agrupan geográficamente en Xàbia/Marina Alta, Moraira, Calpe y Benidorm para facilitar la exploración del entorno.
- La procedencia de datos no se expone en la interfaz pública.
- Las coordenadas restauradas quedan como `curated_pending` para no presentar como verificación oficial lo que aún debe revisarse localmente.
- La búsqueda pública de puntos ahora también consulta la subregión, de modo que términos geográficos como «Xàbia» encuentran los puntos restaurados aunque el nombre del sitio use «Jávea».

---

<!-- release_notes_v21.md -->

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

---

<!-- release_notes_v20.md -->

# WORLDIVES DISCOVERY · v20

## Reserva verificable
- Corregida la vista "Ver mi reserva" para que sea una acreditación completa en pantalla.
- La acreditación muestra centro, teléfono, fecha, hora, punto, participantes, traslado, equipo, guía, Nitrox y estado.
- Se añade QR visible en la reserva.
- El PDF de reserva utiliza el mismo contenido y QR.
- El QR abre una verificación pública de WORLDIVES con el estado real de la reserva.
- Las reservas confirmadas y completadas aparecen como válidas en la verificación.
- Las reservas pendientes, rechazadas o canceladas no se presentan como confirmadas.
- Se mantiene la protección de acceso a los datos privados de la reserva.

---

<!-- release_notes_v19.md -->

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

---

<!-- release_notes_v15.md -->

# WORLDIVES DISCOVERY · v15

## Mi área del buceador
- Nuevo panel personal `#/area` para clientes autenticados.
- Agrupa reservas, viajes/vida a bordo, documentación, mensajes y accesos a Log Book, Recompensas y Monedero.
- Las reservas muestran centro, fecha, hora, punto, participantes, opciones y estado.
- Las solicitudes de experiencias aparecen junto a sus fechas, proveedor y cuenta atrás cuando existe fecha de inicio.
- Nueva bandeja de mensajes para avisos de centros/proveedores.
- Los centros/admin pueden enviar un mensaje directamente desde el detalle de una reserva.
- Los clientes pueden marcar mensajes como leídos.
- Nuevo detalle de reserva orientado al cliente.
- Nuevo recibo PDF de reserva con QR identificativo, generado sin dependencia externa adicional.
- Tras crear/iniciar sesión como buceador, el flujo puede llevar directamente a `Mi área`.

---

<!-- release_notes_v14.md -->

# WORLDIVES DISCOVERY v14 — Backtest y estabilidad

- Corregida la migración de `user_profiles` para instalaciones existentes: fecha de nacimiento, contacto de emergencia y preferencias/equipo.
- Corregidos endpoints GET de recompensas/ofertas y verificaciones de centros usados por el panel de administración.
- El saldo económico del monedero ya no se genera automáticamente por actividad del usuario.
- Las ofertas monetarias sin centro asociado quedan desactivadas; los beneficios económicos deben pertenecer a un centro participante.
- Añadido flujo de saldo promocional concedido por administrador/centro, con control de que un centro solo pueda concederlo a clientes vinculados o con reserva.
- Manteniendo puntos, centros, tipos de buceo, cuentas, logbook, recompensas y monedero.

## Backtest realizado

- Sintaxis Python y JavaScript: OK.
- Salud de API y catálogo: OK.
- 283 puntos activos verificados en la base de distribución.
- Fichas de punto y centro: OK.
- Filtros semánticos de tipos de buceo: OK en pruebas HTTP.
- Inicio de sesión, cuenta y persistencia del perfil: OK.
- Log Book: alta y lectura: OK.
- Recompensas y monedero: lectura, concesión patrocinada y canje: OK.
- Registro y verificación de centro: OK.
- Gestión de recompensas de centro: OK.
- QR y check-in: OK.
- Reservas y estados de reserva: OK en pruebas de API.
- Experiencias/destinos/recorridos virtuales: endpoints principales compilados y probados en entorno de backtest.

Nota: el backtest es de API, rutas y lógica de cliente; antes de un lanzamiento público debe hacerse una prueba manual en navegador real y una revisión de seguridad/privacidad/producción.

---

<!-- release_notes_v13_6.md -->

# WORLDIVES DISCOVERY v13.6 — Mi cuenta funcional

- Recuperada y corregida la ruta `#/cuenta` desde el menú de usuario.
- Corregido el error de renderizado que impedía abrir Mi cuenta.
- Mi cuenta incluye perfil, certificación, documentación, contacto de emergencia y ficha operativa de equipo.
- Preferencias de alquiler: traje, tallas, botas, BCD, aletas, máscara, kilos habituales, botella y ordenador.
- Los datos se guardan en `user_profiles` y quedan disponibles para el flujo de reservas del centro.
- Se mantiene el ecosistema de Log Book, Recompensas y Monedero de la versión base.

---

<!-- release_notes_v13_3.md -->

# Worldives Discovery v13.3 — Recompensas y monedero

- Sistema automático de puntos WOD y saldo de monedero.
- No requiere check-in diario ni tareas artificiales.
- Recompensas por actividad natural: Log Book, hitos de inmersiones, perfil, documentación, reservas completadas y check-in de centros.
- Niveles de progresión: Explorador, Buceador, Explorador del mundo, Navegante, Embajador WORLDIVES y Leyenda.
- Catálogo de recompensas canjeables mediante saldo: descuentos, cursos, seguro de día y crédito para inmersiones.
- Canjes con código único y registro de movimientos.
- Centros/admin pueden crear ofertas de recompensa mediante API.

---

<!-- release_notes_v13_2.md -->

# WORLDIVES DISCOVERY v13.2

- Fixed semantic dive-type navigation: category cards now open a filtered point list using the same server-side category rules.
- Category filters are exclusive to their semantic criteria; current catalog counts include 22 wrecks, 9 muck sites, 6 channels, 3 cenotes, etc.
- Added a real account dropdown with profile, Log Book, Rewards, Wallet and role-specific management links.
- First-install registration now exposes Administrator as a selectable account type; non-initial users cannot self-register as administrator.
- Center registrations remain pending until administrative verification; verified centers get center management access.
- Freelance accounts have a dedicated provider panel for their own services/experiences and do not receive global catalog administration.
- Administrators can edit existing center records as well as create new centers.

---

<!-- release_notes_v13_1.md -->

# WORLDIVES DISCOVERY v13.1

## Tipos de buceo corregidos

- El catálogo público ya no filtra por coincidencia literal del campo `dive_type`.
- Se han creado categorías semánticas para que cada botón devuelva los puntos que realmente corresponden.
- Aguas profundas: puntos cuyo `max_depth` catalogado supera 20 m.
- Arrecifes: tipos que identifican arrecife, separados de pecios.
- Pecios y naufragios: pecio/naufragio y sitios claramente identificados como wreck.
- Cuevas y cavernas: cuevas/cavernas, excluyendo cenotes para mantenerlos como categoría propia.
- Cenotes: por tipo, nombre o descripción.
- Muck: por tipo y descriptores de muck/lodo.
- Canales, cañones, pináculos, paredes, corrientes/deriva, nocturnas, lagos, pilares y playa/esnórquel tienen filtros específicos.
- El selector de `/puntos` usa las mismas categorías semánticas.
- La página `Tipos de buceo` muestra el número de puntos que devuelve cada categoría.

## Criterio de profundidad

Se aplica el criterio solicitado por el proyecto: `max_depth > 20 m`.

Las categorías son atributos del sitio y pueden solaparse cuando corresponde: un pecio puede ser profundo y un arrecife puede ser profundo. Al seleccionar "Pecios y naufragios", en cambio, el filtro se restringe a los sitios identificados como pecio/naufragio.

---

<!-- release_notes_v12_5.md -->

# WORLDIVES DISCOVERY — notas de versión

Esta versión incorpora mejoras de catálogo, centros, experiencias, verificación y gestión de la plataforma. La interfaz pública no muestra referencias externas de procedencia.

---

<!-- release_notes_v12_4.md -->

# WORLDIVES DISCOVERY — notas de versión

Esta versión incorpora mejoras de catálogo, centros, experiencias, verificación y gestión de la plataforma. La interfaz pública no muestra referencias externas de procedencia.

---

<!-- release_notes_v12.md -->

# WORLDIVES DISCOVERY — notas de versión

Esta versión incorpora mejoras de catálogo, centros, experiencias, verificación y gestión de la plataforma. La interfaz pública no muestra referencias externas de procedencia.

---

<!-- release_notes_v11.md -->

# WORLDIVES DISCOVERY — notas de versión

Esta versión incorpora mejoras de catálogo, centros, experiencias, verificación y gestión de la plataforma. La interfaz pública no muestra referencias externas de procedencia.
