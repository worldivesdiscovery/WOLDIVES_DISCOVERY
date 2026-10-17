# WORLDIVES DISCOVERY v50.31: seguridad urgente (Fase 1, fallos G1-G12)

Esta versión corrige los 12 fallos graves de la auditoría de la v50.29 y endurece contraseñas, sesiones, registros y cabeceras. No cambia el aspecto de la web salvo donde la seguridad lo exige (registro, check-in, documentos, recorridos virtuales y avisos).

## Documentos privados (G1, G8)
- **Quién puede abrir un documento:**
  - su dueño;
  - un centro, solo mientras el buceador tenga con él una reserva **hecha por el propio buceador** y no cancelada, o haya aceptado compartir sus datos;
  - el administrador, y queda anotado.
- **Cada descarga** (y cada intento denegado) se guarda en el historial de actividad.
- **Sin copias en cachés:** los documentos se sirven con `Cache-Control: private, no-store` y con su nombre de archivo.
- **Tipo real del archivo:** se comprueba por sus primeros bytes (PDF, JPG, PNG o WEBP), no por la extensión. Máximo 10 MB y 30 documentos por cuenta.
- **Al borrar un documento se borra también el archivo** del disco. También al eliminar la cuenta.

## Alta de centros y profesionales (G2)
- Nadie es centro ni profesional por registrarse. La cuenta empieza como buceador con una **solicitud pendiente**.
- El alta de un centro crea siempre una **ficha nueva oculta** hasta que el administrador la aprueba.
- Si el teléfono coincide con un centro del catálogo, solo aparece como **sugerencia** para el administrador. Nunca se enlaza.
- **Para aprobar** hay que indicar cómo se ha verificado (email del dominio del centro, llamada al teléfono público o documento) y una nota. Queda en el historial.
- La pantalla de verificación avisa cuando el email coincide con el dominio de la web del centro.
- **Corregido también:** el botón «Rechazar» de una verificación enviaba la orden a «Correcciones» por error.
- **Las 2 cuentas de centro de la v50.29:** ya no existen en la base entregada (0 usuarios). El historial muestra que se dieron de alta el 04/10/2026 como centro y quedaron enlazadas al instante a fichas nuevas (29 y 30) sin aprobación; una de ellas además fue «primer usuario = administrador». Para revisar una base de producción: `python app/server.py --report-center-accounts`.

## Recorridos virtuales y CSP (G3 y punto 4)
- Solo se admiten enlaces `https://` de `youtube-nocookie.com`, `player.vimeo.com` y `google.com/maps` (lista configurable con `WOD_EMBED_DOMAINS`). Se comprueba en el servidor y en el navegador.
- El vídeo **solo se carga al pulsar «Cargar vídeo»**, avisando de que se conecta con un tercero.
- Los enlaces antiguos que no cumplan la regla dejan de entregarse.
- Subidas 360° limitadas a 15 MB y comprobadas por contenido.
- **Content-Security-Policy** en todas las respuestas (también PDF, SVG y 304): scripts solo de la propia web, sin scripts en línea.
- **Leaflet alojado en el propio servidor** (`/assets/vendor/leaflet`), sin unpkg.
- La búsqueda de localidades del Top 10 pasa por el servidor (`/api/geocode`): la IP del visitante ya no llega a terceros.
- Las webs y redes sociales de centros y profesionales solo admiten enlaces `http(s)://`.

## Reservas públicas (G4)
- La página de comprobación del QR exige la sesión del dueño o del centro, o el **token aleatorio largo** que llevan el QR y el PDF.
- Ya no devuelve el identificador del usuario ni el apellido: «Laura M.».

## Clientes de los centros (G5)
- Una reserva manual o por API **nunca se enlaza** a una cuenta registrada: el centro tiene su propia ficha de cliente. El email y el teléfono viajan con la reserva para que el cliente reciba la confirmación.
- El centro ve el perfil y los documentos de un buceador registrado solo si **ha reservado él mismo** o **ha aceptado compartirlos**.
- El check-in por QR pide confirmación: «Compartir mis datos con [centro]».
- **Mi cuenta → Centros que ven tu ficha:** el buceador ve con quién comparte y puede dejar de compartir.

## Datos de salud (G6)
- Desaparece el tipo «Certificado médico» y su recompensa. El servidor rechaza documentos médicos.
- Aviso en Documentación: «No subas certificados médicos: entrégalos directamente al centro».
- Al actualizar, si existiera algún certificado médico se borra con su archivo y se avisa a su dueño. En la base entregada no hay ninguno.
- En el perfil se explica para qué sirven la fecha de nacimiento, el contacto de emergencia y el lastre, y se marcan como opcionales.

## Tamaños de petición (G7)
- JSON: 1 MB. Subidas: 15 MB (documentos 10 MB).
- Se rechaza **antes de leer el cuerpo** si `Content-Length` supera el límite (respuesta 413).

## Instalación inicial (G9)
- `#/setup` y «el primer usuario es administrador» solo existen con `WOD_ALLOW_SETUP=1`.
- Producción: `python app/server.py --create-admin --email … --username … --name …`.

## CSRF (G10)
- Se rechaza cualquier POST o DELETE sin `Origin` ni `Referer`, salvo el webhook de Stripe y `/api/integrations/bookings`.
- Con `WOD_ENV=production` el servidor no arranca sin `WOD_PUBLIC_URL` en https, sin `WOD_SECRET_KEY` o con `WOD_ALLOW_SETUP=1`.

## Avisos en vez de mensajes (G11)
- Se elimina la mensajería libre: nadie escribe a nadie fuera de una reserva.
- Un centro o freelance solo puede enviar un **aviso sobre una reserva suya** (por ejemplo, un cambio de hora). Llega por email y a «Avisos», con el teléfono y el email del centro. No se responde por la plataforma.

## Pagos (G12)
- `/api/payments` devuelve al buceador solo lo necesario: sin comisión, sin cuenta conectada y sin enlace de pago.

## Contraseñas y sesiones (13)
- PBKDF2 con **600 000 iteraciones** y prefijo de versión. Las contraseñas antiguas se actualizan solas al iniciar sesión.
- Límite de intentos en el inicio de sesión (por cuenta y por IP), en el registro, en la recuperación de contraseña y en la verificación de email. Seguro entre hilos y con tamaño acotado.
- Al cambiar el rol de un usuario se cierran sus sesiones.
- Borrado de sesiones caducadas cada 10 minutos.
- Verificación del email al registrarse y **cambio de email** con confirmación desde la nueva dirección.
- Casilla separada y opcional para recibir comunicaciones comerciales.

## Proxy y registros (14, 15)
- `X-Forwarded-For` y `X-Forwarded-Proto` solo se leen si la petición viene de `WOD_TRUSTED_PROXIES`.
- Los registros no guardan la cadena de consulta (coordenadas, búsquedas). La IP se guarda truncada (`WOD_LOG_IP`), en `logs/access.log` con rotación diaria y 14 días de conservación (`WOD_LOG_RETENTION_DAYS`).
- `/api/health` pública devuelve solo `ok` y la versión.
- Aviso por email a los administradores cuando hay 5 errores internos en 10 minutos.

## Errores menores (16)
- `/api/promo/<código>/qr.svg`: el `return` ya estaba en la v50.30 («Ya estaba»); se ha simplificado con el resto de QR.
- Las conexiones SQLite se cierran al terminar cada petición.
- **Corregidos también:**
  - el QR de «inmersión» consultaba tablas que no existen;
  - los QR y PDF usaban la cabecera `Host` (manipulable) para construir enlaces;
  - había rutas duplicadas inalcanzables para los recorridos virtuales;
  - tres manejadores de eventos en línea incompatibles con la CSP.

## Comprobado
- **Pruebas automáticas** (`tests/test_phase1_security.py`): 24 pruebas, todas correctas, sobre una copia de la base (nunca la real). Incluyen permisos entre roles (buceador ↔ buceador, centro ↔ centro, freelance, anónimo) y datos erróneos en las rutas principales (nunca un error 500).
- **Recorrido en navegador real** (`tests/e2e_walk.py`, Chromium) con los 5 roles, en ordenador y móvil: ningún error de JavaScript, ninguna violación de la CSP y ningún error 500.

**Instalación:** detén el servidor, copia el contenido encima y arranca. La primera línea debe decir `WORLDIVES DISCOVERY v50.31`. La base se actualiza sola (solo añade tablas y columnas).
