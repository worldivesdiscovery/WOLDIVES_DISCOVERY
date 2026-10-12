# App WORLDIVES · 3. Modelo de datos y API compartida con la web

Entregable 3 del encargo «App de reservas de buceo — iOS y Android (2027)».

## Principio: una sola fuente de verdad

La app **no tiene base de datos propia en el servidor**:
- Usa la misma base y el mismo servidor que la web (`app/server.py`, SQLite en modo WAL).
- Plazas, precios, horarios, políticas y pagos salen de las mismas tablas y de las mismas funciones que ya usa la web
  (presupuesto, creación de la reserva, devoluciones, avisos).
- Así nunca puede haber un precio o un hueco distinto en la web y en la app.

Se añade una **API versionada `/api/v1/`**, pensada para la app y para que la web se pase a ella poco a poco:

| Hoy (web) | `/api/v1/` (app, y la web después) |
|---|---|
| Sesión por cookie y comprobación de origen | Token por dispositivo (`Authorization: Bearer`), renovable y revocable |
| Rutas internas que cambian con la web | Contrato estable, descrito en OpenAPI y con pruebas de contrato |
| Ids numéricos en las rutas del panel | **Solo `uid` aleatorios** (cierra para la app el «Pendiente de decisión» 1 de v50.47) |
| Respuestas pensadas para cada pantalla de la web | Respuestas pensadas para pintar cada pantalla de la app con **una sola llamada** (Inicio, Hoy) |

**Reglas que no cambian:**
- **Datos de centro, por la capa de centro.** Toda ruta `/api/v1/pro/*` pasa por `app/wod/inquilinos.py`: el centro
  sale del token, nunca de la petición, y lo de otro centro da 404.
- **Lo público sigue siendo público:** salidas, precios, plazas, puntos y valoraciones.

## Lo que ya existe y la app reutiliza

| Concepto de la app | Tablas actuales | Nota |
|---|---|---|
| Buceador, ficha, tallas | `users`, `user_profiles` (`suit_size`, `boot_size`, `bcd_size`, `fin_size`, `mask_size`, `usual_weight_kg`, `certification_id`, teléfono cifrado) | Tallas y titulación se guardan una vez |
| Centro, freelance, inquilino | `centers`, `providers` (`c:<id>` / `f:<id>`), `center_members` (propietario, encargado, recepción, instructor) | Aislamiento de v50.47 |
| Servicio (inmersión, curso, bautizo) | `provider_services` (precio, `booking_mode` pago o petición, `deposit_type`/`deposit_value`, política de cancelación) | Señal y pago en el centro ya existen |
| Salida | `service_slots` (fecha, hora, `spots_total`/`spots_available`, punto, `meeting_point`, `uid`) | |
| Reserva | `bookings` (`uid`, estado, pago, personas, equipo, `slot_reserved`) | La plaza se aparta mientras se paga (`WOD_PAYMENT_HOLD_MINUTES`) |
| Pago y devolución | `payment_orders`, `payment_refunds` | Cobro directo en la cuenta Stripe del centro o del freelance, sin comisión (v50.34) |
| Manifiesto, grupos, barco, check-in | `manifest_entries` (`checked_in_at`, `no_show`), `slot_groups` (`boat_id`, `guide_user_id`), `boats` | Ya funciona sin conexión (v50.42) |
| Descargo firmado | `waiver_templates`, `waiver_signatures` | Se firma después de reservar |
| Puntos de buceo | `dive_points` (tipo, `min_depth`/`max_depth`, `recommended_certification_id`, coordenadas) | |
| Logbook | `logbook_entries` | |
| Valoraciones | `center_reviews` | Hoy basta una reserva pagada o confirmada; hay que exigir check-in (abajo) |
| Avisos | `notice_batches`, `notice_outbox`, `messages` | Se añade el canal push |
| Agenda del freelance | `resources`, `resource_blocks`, `resource_hours`, `resource_closures` | Días, medio día y bloqueos (v50.44) |
| Lista de espera, cambios de fecha | `waitlist_entries`, `reschedule_requests`, `slot_cancel_offers` | |
| Calendario | iCal del centro (`/api/provider/ical`) | Google Calendar se suscribe a ese iCal; no hace falta conectar cuentas |

## Lo que hay que añadir

Las migraciones siguen la regla de siempre: **añaden y transforman, nunca borran sin copia previa**.

| Tabla o cambio | Columnas principales | Para qué |
|---|---|---|
| `devices` | `id`, `user_id`, `platform` (ios/android), `push_token` (cifrado), `app_version`, `lang`, `created_at`, `last_seen_at`, `revoked_at` | Notificaciones push y sesiones por dispositivo |
| `app_tokens` | `token_hash`, `device_id`, `user_id`, `kind` (acceso o renovación), `expires_at`, `rotated_from` | Token de acceso corto (15 min) y de renovación (60 días) con rotación. Al detectar la reutilización de uno ya usado se revoca toda la cadena |
| `passkeys` | `credential_id`, `user_id`, `public_key`, `sign_count`, `transports`, `name`, `created_at`, `last_used_at` | Entrar con passkey (WebAuthn) |
| `auth_identities` | `provider` (apple, google), `subject`, `user_id`, `email_verified`, `created_at` | Sign in with Apple y Google |
| `users.claimed_at` | — | Cuenta creada al pagar como invitado. Vale solo para ver y gestionar esa reserva hasta que el buceador la confirma (passkey o enlace del correo) |
| `cert_levels` y columnas en `certifications` | `agency` (PADI, SSI, CMAS/FEDAS…), `level_rank` (0 sin titulación, 1 Open Water, 2 Advanced, 3 Rescue, 4 Divemaster o más), `specialties` (nitrox, profunda, nocturna) | Comparar niveles de distintas agencias. Hoy las titulaciones son solo nombres |
| `provider_services.min_level_rank` y `requires_specialty` | — | Validación automática del nivel |
| `sea_conditions` | `dive_point_id`, `hour`, `wave_m`, `period_s`, `wind_kmh`, `wind_dir`, `water_c`, `source`, `fetched_at` | Estado del mar por punto, en caché por horas |
| `job_offers` | `uid`, `provider_id` (centro), `slot_id` o rango de fechas, `role` (guía o instructor), `fee`, `currency`, `freelance_user_id`, `status` (ofrecida, aceptada, rechazada, caducada, cancelada), `responded_at` | Ofertas de trabajo de centros a freelance. Al aceptar, la persona queda asignada en `slot_groups` |
| `medical_answers` | `booking_id`, `seat`, `result` (apto o necesita certificado), `answers` (cifradas), `version`, `signed_at`, `delete_after` | **Solo si se aprueba la decisión sobre datos médicos** (README) |
| `notice_outbox.channel` | se añade `push` | Cancelación por meteo y cambios, también por push |
| `funnel_metrics` | `day`, `platform`, `app_version`, `step`, `count`, percentiles p50/p90/p99 | Embudo y tiempo hasta reservar, **agregado, sin datos de personas** |
| Valoraciones | `center_reviews` exige una reserva de ese centro con check-in y fecha ya pasada | «Solo quien ha buceado» |
| `live_activity_tokens` (fase 3) | `booking_id`, `device_id`, `token`, `expires_at` | Actualizar la Live Activity si cambia la hora |

## API `/api/v1/` (REST + JSON)

**Convenciones:**
- Errores `{"error": {"code", "message"}}` en el idioma del usuario.
- Fechas ISO con la zona del centro.
- Importes en céntimos más la moneda.
- `ETag` en las lecturas para responder `304` y ahorrar datos en el barco.
- Paginación por cursor.
- **`Idempotency-Key` obligatoria** en lo que cobra, devuelve, cancela o crea: un doble toque o un reintento sin
  cobertura no repite nada.
- Límites de intentos por token y por IP.

### Identidad

| Método y ruta | Qué hace |
|---|---|
| `POST /auth/passkey/options`, `POST /auth/passkey/verify` | Alta y entrada con passkey |
| `POST /auth/apple`, `POST /auth/google` | Se verifica el token del proveedor con sus claves públicas y se crea o enlaza la cuenta |
| `POST /auth/email-code`, `POST /auth/email-code/verify` | Código por correo, para quien no tenga ninguno de los anteriores |
| `POST /auth/refresh`, `POST /auth/logout` | Rotación del token y cierre de sesión en ese dispositivo |
| `GET /me/devices`, `DELETE /me/devices/{id}` | Ver y cerrar sesiones abiertas |

### Buceador

| Método y ruta | Qué hace |
|---|---|
| `GET /home?lat&lon&date=today\|tomorrow\|weekend` | **Todo el Inicio en una llamada:** próxima reserva o sugerencia, chips y salidas con plazas, precio final, nivel y estado del mar |
| `GET /slots?date&near&level&type` | Buscar salidas |
| `GET /slots/{uid}` | La hoja de la salida: precio desglosado, política y si es apta para el usuario |
| `POST /bookings/quote` | Precio exacto con personas y equipo (la misma función que `/api/booking-quote`) |
| `POST /bookings` (con `Idempotency-Key`) | Crea la reserva, aparta la plaza y devuelve los datos de pago: `client_secret` del PaymentIntent **en la cuenta del centro**, `stripe_account`, `ephemeral_key` y cliente. Para un invitado, la cuenta sale de los datos del monedero |
| `GET /bookings`, `GET /bookings/{uid}` | Próximas e historial; QR firmado para usarlo sin conexión |
| `POST /bookings/{uid}/cancel`, `POST /bookings/{uid}/change` | Con la política del centro y la devolución automática |
| `POST /bookings/{uid}/repeat` | La misma salida en la próxima fecha libre, directa a la hoja |
| `POST /bookings/{uid}/waiver`, `POST /bookings/{uid}/medical` | Después de pagar |
| `GET/PUT /me/profile`, `POST /me/certifications`, `POST /me/documents` | Ficha, tallas, titulaciones y seguro |
| `GET /me/logbook`, `POST /me/logbook` | Logbook |
| `GET /points/map`, `GET /points/{uid}` | Mapa y fichas (público) |
| `GET /stream?date&slots=…` | Plazas libres en tiempo real (abajo) |
| `POST /assistant` (fase 3) | Recomendación a partir de salidas reales, nivel y estado del mar. Nunca inventa salidas |

### Centro y freelance (`/pro/*`, siempre con el centro del token)

| Método y ruta | Qué hace |
|---|---|
| `GET /pro/today?date=` | **«Hoy» en una llamada:** salidas, ocupación, barco, personal, alertas, ingresos y reservas nuevas |
| `GET /pro/slots/{uid}` | La salida: buceadores con nivel, nº de inmersiones, documentos, tallas, pago y check-in |
| `GET /pro/equipment?date=` o `?slot=` | **Equipo a preparar**: tallas sumadas |
| `POST /pro/checkin` | Check-in por QR, con el token firmado de la reserva |
| `POST /pro/sync` | Cola de cambios hechos sin conexión (check-in, no presentados, notas). Es el mismo protocolo que `/api/manifest/sync` |
| `POST /pro/slots`, `PATCH /pro/slots/{uid}` | Crear o duplicar una salida, cambiar la hora, cerrar plazas |
| `POST /pro/slots/{uid}/notice/preview`, `/notice`, `/notice/{uid}/undo` | Cancelar por meteo o cambiar la hora: el motor de avisos de v50.47 con el canal push |
| `POST /pro/slots/{uid}/staff` | Asignar personal o crear una oferta para un freelance |
| `GET /pro/freelances?date=` | Freelance disponibles ese día, según su agenda |
| `GET /pro/stats?from&to` | Ocupación, ingresos, recurrentes, valoraciones |
| `PUT /pro/availability/{date}` | Freelance: bloquear o abrir un día o medio día |
| `GET /pro/jobs`, `POST /pro/jobs/{uid}/accept`, `/reject` | Freelance: ofertas de trabajo |
| `GET /pro/payouts` | Freelance: cobros, pendientes y facturas |

## Tiempo real: plazas libres

- **Server-Sent Events** en `GET /api/v1/stream`: el servidor envía `slot.updated {uid, spots_available, status}`
  cuando cambian las plazas. Funciona con el servidor actual sin librerías nuevas y atraviesa proxies y redes móviles.
- **Si se corta**, la app vuelve a pedir `GET /home` cada 30 s mientras la pantalla está abierta.
- **La verdad está en el servidor:** al crear la reserva la plaza se comprueba y se aparta. Si alguien se la llevó
  medio segundo antes, la hoja propone la salida siguiente y no se cobra nada.
- **Escala:** cada conexión ocupa un hilo del servidor actual, suficiente para cientos de pantallas abiertas a la vez.
  Si se pasa de ahí, el canal se mueve a un servicio pequeño aparte que lee los mismos cambios. La API no cambia.

## Pagos

- **Stripe PaymentSheet** en la app: Apple Pay y Google Pay como botón principal, y tarjeta como alternativa. Los
  servicios de buceo se consumen fuera de la app, así que no se usa el sistema de compras de Apple ni de Google.
- **Cobro directo en la cuenta Stripe del centro o del freelance** (como la web desde v50.34): el dinero no pasa por
  WORLDIVES y no hay comisión.
  - Repartir pagos entre un centro y un freelance (Connect con transferencias) solo hace falta si un mismo pago tiene
    que ir a los dos. Es una decisión pendiente (README).
- **Pago completo, señal o pago en el centro:** como ya está en `provider_services`.
- **Bajo petición:** sin cobro hasta que el centro acepta; después, «Pagar» con un toque desde el aviso.
- **La confirmación llega por el webhook de Stripe**, que ya existe, no por la app. Así, si el móvil se queda sin
  cobertura justo después de pagar, la reserva queda igual de confirmada.
- **Botones de Apple Pay y Google Pay** con su aspecto oficial (negro o blanco, según sus guías). El color de acento
  de la app es para el resto de acciones.

## Sin conexión (en el barco)

| Qué | Dónde se guarda | Cómo se sincroniza |
|---|---|---|
| Buceador: sus reservas, QR firmado, punto de encuentro, descargo | Base local cifrada (SQLite cifrada; la clave en Keychain o Keystore) | Al volver la cobertura |
| Centro: «Hoy» y «Mañana», manifiestos, tallas, alertas | Igual; se descarga al abrir «Hoy» y cada vez que cambia | Cola de cambios con `Idempotency-Key`. Si dos móviles hacen check-in de lo mismo, gana el primero y nadie pierde el dato |
| Escáner QR | El QR lleva la firma del servidor, así que se valida sin conexión con la clave pública | — |

## Notificaciones push

- **Cómo se envían:** APNs (iOS) y FCM (Android), desde el servidor con `devices`.
- **Qué se envía:**
  - reserva confirmada, recordatorio el día antes y cambios o cancelaciones (canal `push` del motor de avisos);
  - al centro: reservas nuevas y documentos que faltan;
  - al freelance: ofertas de trabajo.
- **Qué no lleva el texto del aviso:** datos personales. Abre la pantalla con un enlace profundo.
- **Enlaces universales (iOS) y App Links (Android):** `worldivesdiscovery.com/r/<enlace firmado>` (el de v50.47),
  `/reserva/<uid>` y `/salida/<uid>`. Sin la app instalada, abren la web.
- **Ficheros nuevos de la web:** `/.well-known/apple-app-site-association` y `/.well-known/assetlinks.json`. Sirven
  también para las passkeys, que quedan compartidas entre la web y la app.

## Idiomas

- La web ya está en **9 idiomas** (es, en, fr, de, it, pt, nl, pl, zh) y los correos también. Propuesta: la app nace
  con los mismos 9 y no solo con 5 (decisión en el README).
- Los textos de la app van en archivos por idioma, como `public/idiomas/*.json`, y comparten glosario con la web
  para que «salida», «señal» o «descargo» se digan igual en todas partes.
- Detección automática por el idioma del teléfono. El buceador puede cambiarlo, y los avisos le llegan en su idioma.

## Seguridad y RGPD

- **Tokens** en Keychain o Keystore, nunca en almacenamiento normal. Bloqueo con Face ID o huella opcional para el
  panel del centro.
- **Teléfonos y credenciales** cifrados en el servidor (v50.47, `WOD_DATA_KEY`).
- **Documentos** (titulación, seguro): almacenamiento privado del servidor, servidos solo al titular y al centro con
  reserva viva.
- **Cuestionario médico:** decisión pendiente (README), con el abogado: son datos de salud (art. 9 RGPD).
- **Analítica del embudo sin rastreo:**
  - la app manda al servidor «paso alcanzado» con milisegundos desde la apertura y un identificador de sesión que
    vive solo en memoria;
  - el servidor guarda únicamente totales por día;
  - sin SDK de terceros ni identificador publicitario, así que no hace falta el aviso de rastreo de Apple (ATT).
    Confirmar con el abogado si hace falta consentimiento.
- **Borrar la cuenta desde la app:** lo exige Apple. Ya existe en la web (`/api/account/delete`).

## Rendimiento

- **Arranque en frío < 2 s:**
  - la app pinta el último Inicio guardado al momento y lo refresca después;
  - pocas dependencias en el arranque;
  - imágenes en WebP o AVIF con varios tamaños desde el servidor.
- **Pantallas < 300 ms:** las hojas (salida, equipo) se abren sin pedir nada, con los datos que ya trae `/home` o
  `/pro/today`.
- **Medición en cada versión:** pruebas automáticas del flujo de reserva y pago (Maestro o Detox) con Stripe en modo
  test, y el embudo real en producción (objetivo p90 < 30 s).
