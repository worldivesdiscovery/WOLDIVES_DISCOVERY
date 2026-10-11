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
