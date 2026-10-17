# Validación de datos, coherencia y límites de negocio

Referencia: OWASP ASVS 5.0, V1.4, V2.1–V2.4. Todo se comprueba **en el servidor** (`app/server.py` y `app/wod/`);
la web y la app repiten algunas comprobaciones solo para avisar antes. Pruebas: `tests/test_v50_51_asvs.py`
(clases `ValidacionYLimites` y `PuntosYPlazasVariosProcesos`) y las de cada función.

## Formato de cada dato

| Dato | Regla | Función |
|---|---|---|
| Cuerpo de la petición | JSON UTF-8, un objeto, como máximo `WOD_MAX_JSON_BYTES` (1 MB); `NaN` e `Infinity` no se aceptan | `json_body`, `body_length` |
| Texto | Sin caracteres de control (se conservan saltos de línea y tabuladores), recortado a la longitud de cada campo; una lista de valores simples se guarda como «a, b»; un objeto se rechaza | `clean_text` |
| Email | `algo@dominio.ext`, en minúsculas; los de dominios `.local` y `.test` no reciben correos | rutas de registro, cambio de email, contacto; `mail_deliverable` |
| Teléfono | Se guarda cifrado; para WhatsApp, E.164 (`+34600111222`) con prefijo internacional | `wod.cifrado.normalize_phone` |
| Contraseña | 10–256 caracteres, ni filtrada ni solo palabras de la web ([`seguridad/autenticacion.md`](seguridad/autenticacion.md)) | `wsec.password_problem` |
| Fecha | Día real `AAAA-MM-DD` (no 31 de febrero) | `clean_date` |
| Fecha del Log Book | Día real entre 1950 y hoy | `clean_logbook` |
| Hora | `HH:MM` de 00:00 a 23:59 | `clean_time` |
| Importe (precios, tarifas, extras, equipo, experiencias, integración) | Número finito de 0 a 1.000.000, redondeado a céntimos; admite coma decimal | `clean_money` |
| Señal | Porcentaje 1–99 o importe fijo mayor que 0 y menor que el precio | `clean_deposit` |
| Política de cancelación | Horas 0–720 y reembolso 0–100 % | `clean_policy_numbers` |
| Personas por reserva | Entero de 1 a 99 y no más que el máximo del servicio ni que las plazas libres | `clean_int`, ruta `/api/bookings` |
| Máximo de personas de un servicio | Entero 0–999 (0 = sin máximo) | `clean_int` |
| Duración de un servicio | Entero de 0 a 43.200 minutos (30 días) | `clean_int` |
| Plazas de una experiencia | Enteros 0–10.000; las libres no superan las totales | `clean_experience_numbers` |
| Profundidad y tiempo del Log Book | 0–350 m y 0–600 min | `clean_logbook` |
| Coordenadas | Latitud −90…90 y longitud −180…180 (0 = sin ubicación) | `clean_lat`, `clean_lng`, `clean_coord` |
| Enlaces | Solo `http(s)` sin usuario ni caracteres de control; los vídeos que se ven dentro de la web, solo de las plataformas permitidas (`WOD_EMBED_DOMAINS`) | `wsec.clean_http_url`, `wod.videos` |
| Identificadores | Enteros; uno demasiado grande responde 400 («Un número es demasiado grande»), nunca 500 | manejador de errores de `do_GET`/`do_POST` |
| Archivos | Tipo comprobado por su contenido, tamaño máximo y nombre propio del servidor | `save_upload`, `save_public_image` |

## Coherencia entre datos

| Regla | Dónde |
|---|---|
| La salida elegida manda: la fecha, la hora y el servicio de la reserva son los de la salida | `/api/bookings` |
| El servicio, la salida, los extras y el equipo son del mismo centro que la reserva | `/api/bookings`, `booking_quote` |
| El punto de buceo de la reserva es uno de los de la salida | `/api/bookings` |
| El precio lo calcula el servidor (tarifa vigente, extras, equipo, días); nunca se acepta el del navegador, y nunca puede quedar negativo | `booking_quote`, `effective_service_tariff` |
| La señal es menor que el precio | `clean_deposit` |
| La fecha de fin de una experiencia no es anterior a la de inicio | `clean_experience_numbers` |
| Una reserva se paga solo con la confirmación firmada de Stripe y por el importe del pedido | webhook de Stripe ([`pagos-stripe.md`](pagos-stripe.md)) |
| Los cambios de estado siguen las transiciones permitidas | `wod.booking` ([`estados-reserva.md`](estados-reserva.md)) |
| Las plazas, los saldos de puntos y las existencias se comprueban y se descuentan en la misma transacción (`BEGIN IMMEDIATE` y actualizaciones condicionadas) | `/api/bookings`, `/api/experience-bookings`, `/api/rewards/redeem`, `/api/provider/points-grant`, `/api/center/redemptions/validate` |

## Límites de negocio

| Límite | Valor | Por | Variable o constante |
|---|---|---|---|
| Reservas y solicitudes (también de experiencias) | 20 por hora | persona | `WOD_BOOKING_MAX_PER_HOUR` |
| Pagos sin terminar que retienen plazas | 3 a la vez (cada uno retiene 15 minutos) | persona | `PENDING_PAYMENTS_MAX`, `HOLD_MINUTES` |
| Inmersiones nuevas en el Log Book | 60 al día | persona | `LOGBOOK_LIMIT` |
| Puntos del Log Book | 4 inmersiones con puntos por fecha de inmersión y 10 por día en que se añaden | persona | `LOGBOOK_POINTS_PER_DAY`, `LOGBOOK_POINTS_PER_ENTRY_DAY` |
| Puntos que concede un centro | máximo al mes por cliente y por centro | centro | `POINTS_GRANT_CLIENT_MONTH`, `POINTS_GRANT_CENTER_MONTH` |
| Documentos privados | 30 | persona | `MAX_DOCUMENTS_PER_USER` |
| Plantillas de servicio | 50 | centro o freelance | `MAX_TEMPLATES_PER_PROVIDER` |
| Fotos de la galería del centro | 12 | centro | `MAX_GALLERY_IMAGES` |
| Servicios publicados y personas del equipo | según el plan | centro | `PLAN_LIMITS` (`services_max`, `team_max`) |
| Avisos masivos | 60 por hora | persona | `NOTICE_LIMIT` |
| Solicitudes de información, denuncias y mensajes de contacto | 10 por hora cada uno | dirección | `REPORT_LIMIT` |
| Altas | 10 por hora | dirección | `WOD_REGISTER_MAX_PER_HOUR` |
| Búsquedas de lugares | 30 por minuto | dirección | `GEOCODE_LIMIT` |
| Inicio de sesión, códigos y recuperación | ver [`seguridad/autenticacion.md`](seguridad/autenticacion.md) | | |
| Tamaño de las peticiones | JSON 1 MB, subidas 15 MB, documentos 10 MB | petición | `WOD_MAX_JSON_BYTES`, `WOD_MAX_UPLOAD_MB`, `WOD_MAX_DOCUMENT_MB` |

Pasado un límite por tiempo se responde 429 con un texto que dice cuánto esperar; un límite de cantidad responde 400
con lo que hay que hacer (por ejemplo, borrar una plantilla). Todos los límites por tiempo son comunes a todos los
procesos del servidor.

## Archivos subidos

| Qué | Quién | Tipos | Máximo | Cómo se comprueba | Cómo se guarda y se sirve |
|---|---|---|---|---|---|
| Logo, portada y galería del centro, foto de perfil del freelance, fotos de puntos, promociones, temas, destinos y experiencias | Centro, freelance, administración | JPG, PNG, WEBP | 6 MB, 40 Mpx | Firma del archivo y **se abre y se vuelve a guardar** con Pillow (sin metadatos ni GPS); si no se puede abrir, se rechaza | Nombre aleatorio en `data/fotos` (`/assets/uploads/…`); se sirve como imagen con `nosniff` y una política que no ejecuta nada (`sandbox`) |
| Fotos de especies | Centro, freelance, administración | JPG, PNG, WEBP | 12 MB, 40 Mpx | Igual; se guardan como WebP en tres tamaños | Igual |
| Documentos privados del buceador (titulación, seguro…) y seguro del centro o del freelance | Buceador, centro, freelance | PDF, JPG, PNG, WEBP | 10 MB (`WOD_MAX_DOCUMENT_MB`), 30 por persona | Firma del archivo; una imagen tiene que abrirse; un PDF tiene que estar entero (cabecera y final); antivirus si está configurado (`WOD_AV_COMMAND`) | Fuera de la web (`storage/`), permisos 600, nombre aleatorio. Solo los ve su dueño, el centro mientras tenga una reserva viva o la ficha compartida, y la administración (cada vista queda registrada). Nunca en caché; el nombre de la descarga lleva la extensión real; un PDF de otra persona se descarga en vez de abrirse |
| Captura de «Reportar fallo» | Solo el entorno de pruebas | JPG, PNG | 1,5 MB | Firma del archivo | Carpeta `fallos/` del entorno de pruebas |

Un archivo que no pasa una comprobación se rechaza con un 400 que explica qué hacer; uno con virus, además, deja un
aviso de seguridad para la administración.

## Funciones costosas

| Función | Qué cuesta | Cómo se defiende |
|---|---|---|
| Iniciar sesión, registrarse, cambiar la contraseña | PBKDF2 de 600.000 vueltas (unos 0,3 s de CPU) | Límites de intentos; como mucho la mitad de los núcleos calculando a la vez para todos los procesos; si hay que esperar más de 60 s, 503 enseguida |
| Buscar lugares (`/api/geocode`) | Una llamada a Nominatim, una por segundo | Caché de 24 h; 30 por minuto y dirección; si la cola pasa de 2 s, 503; tras 3 fallos seguidos no se llama durante un minuto |
| Vista satélite (`/api/tiles/satellite`) | Una llamada a ArcGIS por tesela | Solo con clave; límite por dirección y contador mensual; 10 s como mucho; tras 3 fallos seguidos, 503 durante un minuto |
| Comprobar vídeos y fotos de especies | Hasta 4 saltos de 8 s a otra web | Solo centros, freelance y administración; solo direcciones públicas por https; tamaño máximo |
| Fotos | Pillow (hasta 40 Mpx) | 6 MB (12 MB las especies); se rechazan imágenes más grandes en píxeles |
| PDF (justificante, manifiesto, resumen del barco, ficha) | Generarlos | Con sesión y permiso; el del barco con enlace de 10 minutos |
| Exportaciones (CSV, ZIP de mis datos) | Consultas grandes | Con sesión y el permiso de cada tipo |
| Avisos masivos | Muchos correos o mensajes | 60 por hora y persona, límite diario por centro, cola en segundo plano |
| Copias de seguridad | Disco y CPU | En segundo plano, con la API de copia de SQLite, sin bloquear la web |

El proxy espera 75 s (`proxy_read_timeout` de nginx), más que la espera más larga de la aplicación (60 s).
