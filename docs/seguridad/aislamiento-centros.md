# Aislamiento entre centros · auditoría y estado (v50.47)

Encargo «Avisos masivos y aislamiento total entre centros», parte A. Fecha: 12/10/2026.

**Regla de oro:** si hay cualquier duda sobre a qué centro pertenece un dato, no se envía, no se muestra y no se
modifica. Se registra el error y se avisa al administrador. Siempre fallar cerrado, nunca abierto.

**Qué se aísla y qué no.** Lo público sigue siendo público: mapa, Explorar, tablón de salidas, fichas de puntos y de
centros, servicios, salidas, precios, experiencias y reseñas, reservar y pagar. Se aísla solo lo privado del panel:
reservas y datos de clientes, teléfonos, pagos y devoluciones, ajustes, equipo y WhatsApp, y las acciones de cancelar,
editar y avisar. En este documento «centro» incluye al profesional freelance: cada uno es un inquilino (`provider_id`,
`c:<id del centro>` o `f:<id del usuario>`).

## Cómo se ha auditado

1. Se leyeron las 296 rutas del servidor (130 GET y 166 POST, más 2 DELETE), las tareas en segundo plano, las
   exportaciones, los PDF, el calendario iCal y el widget, en tres bloques (GET; POST hasta `/api/account/delete`;
   resto de POST, DELETE y tareas). Para cada ruta: de dónde sale el centro (sesión o petición), si la consulta filtra
   por centro y qué pasa si el centro A manda un identificador del centro B.
2. Cada fallo alto o medio se **reprodujo** contra el servidor real con una copia temporal de la base de pruebas.
3. Después de corregir, la **matriz de aislamiento** (`tests/test_v50_47_aislamiento.py`) repite lo mismo de forma
   automática en cada versión: propietario de A, recepción y encargado de A, un freelance y un antiguo empleado usan
   los ids de B y del freelance FB en 50 rutas privadas; siempre 404 y una foto de todas las filas de B idéntica
   antes y después.

## A.1 · Tablas de centro: columna, NOT NULL, clave foránea e índice

`provider_id` es obligatoria en la base de datos (no solo en el código):

- En las tablas que ya dicen quién es el dueño de cada fila (columna de centro + columna de freelance, o el
  beneficiario del pago) es una **columna generada** `NOT NULL` con **clave foránea** a `providers(id)`: se calcula de
  esas columnas, así que nunca puede contradecirlas.
- En `service_slots` (salidas) la mantienen disparadores a partir del servicio; una salida no puede pasar a otro centro.
- Las tablas nuevas (avisos, WhatsApp, ajustes) la tienen `NOT NULL REFERENCES providers(id)` desde su creación.
- Los planes y las estadísticas diarias (`plan_payments`, `plan_exceptions`, `provider_stats_daily`) usan desde antes
  el par numérico `provider_type` + `provider_id`, `NOT NULL` y con índice. No llevan clave foránea a `providers`
  porque su `provider_id` es el número del centro o del usuario, no la clave `c:`/`f:`. Solo los escribe y los lee el
  servidor, siempre con el centro de la sesión o de la tarea, y no contienen datos de clientes. Pasarlos a la clave
  nueva queda dentro del **Pendiente de decisión** de la lista revisada (prueba estática).
- La tabla la genera `scripts/seguridad/inventario_aislamiento.py --doc` leyendo el esquema real de una base nueva.
- Las tablas «solo de centro» (tarifas, extras, promociones, QR, equipo…) ya tenían `center_id NOT NULL` con clave
  foránea; además llevan `provider_id` generada e indexada.
- Una fila nueva sin centro la rechaza la propia base (`WOD: dato sin centro`). Las filas antiguas cuyo centro no se
  pudiera saber irían al inquilino `x:0` (cuarentena), que ningún centro ve; la migración lo registra y lo avisa. En
  la base de demostración y en las pruebas: 0 filas en cuarentena.

Restricciones de coherencia (disparadores): una reserva no puede apuntar a un servicio ni a una salida de otro centro;
el manifiesto, los grupos (barco), las ofertas de salida cancelada, los cambios de fecha y los avisos no pueden mezclar
reserva y salida de centros distintos; un pago de una reserva tiene que ser del centro de esa reserva.

Tabla generada con `python scripts/seguridad/inventario_aislamiento.py --doc` sobre una base nueva con todas las
migraciones:

<!-- tablas:inicio -->
| Tabla | Columna de centro | NOT NULL | Clave foránea | Índice (provider_id, …) | Disparadores |
|---|---|---|---|---|---|
| `boats` | `provider_id` (generada) | sí | sí → providers | sí | 2 |
| `booking_days` | heredado: reserva | — | — | — | 0 |
| `bookings` | `provider_id` (generada) | sí | sí → providers | sí | 11 |
| `center_equipment` | `provider_id` (generada) | sí | sí → providers | sí | 0 |
| `center_extras` | `provider_id` (generada) | sí | sí → providers | sí | 0 |
| `center_integrations` | `provider_id` (generada) | sí | sí → providers | sí | 0 |
| `center_links` | `provider_id` (generada) | sí | sí → providers | sí | 0 |
| `center_members` | `provider_id` (generada) | sí | sí → providers | sí | 0 |
| `center_tariffs` | `provider_id` (generada) | sí | sí → providers | sí | 0 |
| `data_shares` | `provider_id` (generada) | sí | sí → providers | sí | 0 |
| `email_digest_log` | heredado: centro (registro interno) | — | — | — | 0 |
| `experience_bookings` | heredado: experiencia | — | — | — | 0 |
| `info_requests` | `provider_id` (generada) | sí | sí → providers | sí | 4 |
| `manifest_entries` | heredado: salida + reserva (disparador: misma empresa) | — | — | — | 2 |
| `notice_batches` | `provider_id` (declarada) | sí | sí → providers | sí | 1 |
| `notice_outbox` | `provider_id` (declarada) | sí | sí → providers | sí | 2 |
| `notice_refunds` | `provider_id` (declarada) | sí | sí → providers | sí | 1 |
| `payment_orders` | `provider_id` (generada) | sí | sí → providers | sí | 2 |
| `payment_refunds` | heredado: pago | — | — | — | 0 |
| `plan_exceptions` | `provider_type` + `provider_id` | sí | no (identificador numérico) | sí | 0 |
| `plan_payments` | `provider_type` + `provider_id` | sí | no (identificador numérico) | sí | 0 |
| `promotion_codes` | heredado: promoción | — | — | — | 0 |
| `promotion_partners` | heredado: promoción (centros invitados) | — | — | — | 0 |
| `promotion_redemptions` | heredado: promoción + centro | — | — | — | 0 |
| `promotions` | `provider_id` (generada) | sí | sí → providers | sí | 0 |
| `provider_services` | `provider_id` (generada) | sí | sí → providers | sí | 3 |
| `provider_settings` | `provider_id` (declarada) | sí | sí → providers | sí | 0 |
| `provider_stats_daily` | `provider_type` + `provider_id` | sí | no (identificador numérico) | sí | 0 |
| `qr_codes` | `provider_id` (generada) | sí | sí → providers | sí | 0 |
| `reschedule_requests` | heredado: reserva + salida destino (disparador) | — | — | — | 2 |
| `resource_blocks` | heredado: recurso | — | — | — | 0 |
| `resource_closures` | heredado: recurso | — | — | — | 0 |
| `resource_hours` | heredado: recurso | — | — | — | 0 |
| `resources` | `provider_id` (generada) | sí | sí → providers | sí | 2 |
| `service_slot_points` | heredado: salida | — | — | — | 0 |
| `service_slots` | `provider_id` (mantenida por disparador) | sí (disparador) | sí → providers | sí | 3 |
| `slot_cancel_offers` | heredado: reserva + salida (disparador) | — | — | — | 2 |
| `slot_events` | heredado: salida | — | — | — | 0 |
| `slot_groups` | heredado: salida (disparador: el barco es del mismo centro) | — | — | — | 2 |
| `team_invites` | `provider_id` (generada) | sí | sí → providers | sí | 0 |
| `travel_experiences` | `provider_id` (generada) | sí | sí → providers | sí | 2 |
| `waitlist_entries` | heredado: salida (pública) + buceador | — | — | — | 0 |
| `waiver_signatures` | heredado: reserva | — | — | — | 0 |
| `waiver_templates` | `provider_id` (generada) | sí | sí → providers | sí | 2 |
| `whatsapp_accounts` | `provider_id` (declarada) | sí | sí → providers | sí | 0 |
| `whatsapp_webhook_events` | heredado: clave de evento (sin datos) | — | — | — | 0 |
<!-- tablas:fin -->

## A.2 · Rutas privadas: de dónde sale el centro y si se filtra

Leyenda. **Centro de**: S = la sesión (nunca la petición). **Filtro**: «capa» = funciones de `app/wod/inquilinos.py`
(`get_slot`, `get_booking`, `slot_bookings`…, siempre `WHERE` por centro); «SQL» = la consulta filtra por centro;
«id + comprobación» = se lee por id y el código comprueba el centro antes de usarlo (y si no es del centro, 404).
**Otro centro**: lo que recibe A con un id de B (comprobado en la matriz).

### Panel (centros y freelance)

| Rutas | Centro de | Filtro | Otro centro |
|---|---|---|---|
| `GET /api/bookings`, `/api/center/requests`, `/api/center/planning`, `/api/manifest/day`, `/api/center/clients`, `/api/center/export`, `/api/center/info-requests`, `/api/provider/experiences`, `/api/provider/stats`, `/api/provider/payments` (y su alias `/api/payments/center`), `/api/center/team`, `/api/center/activity`, `/api/avisos`, `/api/whatsapp` | S | SQL | no aparece |
| `GET /api/bookings/<id>` y `/receipt(.pdf)`, `/qr.svg`, `/waiver`, `/diver-sheet.pdf`, `/change-date` | S | id + comprobación (`can_manage_booking`) | 404 |
| `GET /api/manifest/<salida>`, `POST /api/manifest/<salida>/*`, `POST /api/manifest/sync` | S | id + comprobación (`manifest_slot` → `owns_service` por centro) | 404 |
| `POST /api/bookings/<id>/status`, `/payment`, `/refund`, `/reschedule`, `/change-date/decide` | S | id + comprobación (`require_booking_provider`) | 404 |
| `POST /api/provider-services/update`, `/delete`, `/options`, `/slot`, `/slot-update`, `/slot-delete`, `/slot-close`, `/slot-cancel`; `GET /api/center/poster-qr` | S | id + comprobación (`owns_service`: centro de la sesión, nunca el creador) | 404 |
| `POST /api/travel-experiences/update`, `/api/provider/experience-bookings/status`, `/api/provider/experience-image` | S | id + comprobación (`owns_service`) | 404 |
| `POST /api/messages` | S | `booking_notice_recipient` (`can_manage_booking` / `owns_service`) | 404 |
| `POST /api/avisos/preview`, `/cancelar`, `/cambio`, `/<uid>/deshacer`; `GET /api/avisos/<uid>` | S | capa (`get_slot`, `slot_bookings`) + `uid` aleatorio + SQL por `provider_id` | 404 |
| `POST /api/whatsapp/connect`, `/disconnect`, `/templates/refresh` | S | SQL por `provider_id` | — |
| `POST /api/manifest/boats/save`, `/api/center/tariffs/*`, `/api/center/promotions/*`, `/api/center/extras/*`, `/api/provider/reward-offers`, `/api/center/info-requests/read`, `/api/center/team/*`, `/api/qr/create` | S | SQL (`… AND center_id=<sesión>`) | 404 |
| `POST /api/provider/fiscal`, `/insurance-doc`, `/ical/regenerate`, `/plan/*`, `/api/payments/connect/*` | S (`provider_ref`) | SQL | — |
| `POST /api/team/switch`, `GET /api/team/centers` | S | solo centros a los que pertenece la cuenta | 404 |

### Buceador

| Rutas | Centro de | Filtro | Otro |
|---|---|---|---|
| `GET /api/me`, `/api/me/area`, `/api/account/*`, `/api/messages`, `/api/logbook`, `/api/points`, `/api/rewards`; `POST /api/account/*`, `/api/bookings/<id>/cancel`, `/api/bookings/<id>/change-date` | la cuenta | SQL `user_id=<sesión>` | 404 |
| `GET/POST /api/slot-cancel/<id>` (enlace del correo) y `GET/POST /api/r/<enlace>` (enlace firmado de los avisos) | la reserva del enlace | token de la reserva o enlace HMAC con caducidad | 404 |
| `GET /api/documents/file/<id>` | la cuenta o un centro con reserva viva o permiso | `center_can_see_user` | 404 |

### Administración y sistema

- `GET/POST /api/admin/*`: por diseño ven todos los centros. Desde v50.47 las que muestran o cambian **datos
  privados de un centro** (reservas, pagos, correos, documentos, seguro, DAC7, manifiestos, avisos, cambios de rol)
  exigen un **motivo** (`X-Admin-Reason`, la web lo pide una vez y lo guarda 30 minutos) que queda en `audit_log`
  (`admin_center_access`). El administrador **nunca** envía avisos en nombre de un centro (las rutas de avisos rechazan
  su sesión).
- Webhooks (`/api/payments/webhook*`, `/api/whatsapp/webhook`): sin sesión; firma obligatoria; el centro sale de la
  fila que se actualiza (pago, mensaje), nunca del cuerpo.
- Tareas en segundo plano: cada una toma el centro de la fila que procesa. Las nuevas (avisos, devoluciones,
  recordatorios) **no se ejecutan sin centro** (`job_without_tenant`) y vuelven a comprobarlo antes de cada envío.

### Campos de la petición que se ignoran (B.1)

En cualquier ruta privada de una sesión de centro o freelance, `provider_id`, `center_id`, `provider_user_id`,
`payee_id`, `payee_type`, `owner_center_id`, `owner_user_id`, `tenant_id`, `recipients`, `recipient_ids` y `phones`
se **eliminan** del cuerpo antes de que la ruta lo lea y el intento queda registrado (`tenant_fields_ignored`, solo los
nombres de los campos, nunca sus valores). Prueba: `test_6_tenant_fields_from_the_browser_are_ignored_and_logged`.

## A.3 · Fallos encontrados (todos corregidos en v50.47)

Las líneas son de `app/server.py` en v50.47.

| # | Gravedad | Dónde | Fallo y cómo se explotaba | Corrección (estado) |
|---|---|---|---|---|
| 1 | **ALTA** | `center_row` (l. 3669); rutas públicas `/api/centers`, `/api/centers/<id>`, `/api/dive-points/<id>/centers`, `/api/providers/<id>` | `SELECT c.*` salía al público casi entero: NIF, razón social, dirección fiscal, **fecha de nacimiento** del autónomo, seguro, plan y el **token del calendario iCal**. Con el token, `GET /ical/<token>.ics` daba el **calendario privado de reservas** del centro (nombres de clientes, referencias). Sin iniciar sesión. | Lista blanca de columnas públicas; cualquier columna nueva es privada por defecto. El equipo del centro ve además lo suyo (consentimiento del logo). **Corregido** (`test_8_public_stays_public…`). |
| 2 | **ALTA** | `owns_service` (l. 3565); servicios, salidas, manifiesto (`manifest_slot`, l. 7293), cancelar salidas | La propiedad de un servicio era «de quien lo creó», para siempre. Un empleado despedido (ya cuenta de buceador) podía cancelar las salidas del centro con devolución automática en 1 h, leer manifiestos con teléfonos y contactos de emergencia, y tras entrar en otro centro editar o desactivar los servicios del anterior. | La propiedad es del **centro** (o del freelance sin centro), nunca del creador; las rutas comprueban el rol; lo de otro centro da 404. **Corregido** (`test_4_former_employee_of_b_keeps_nothing`). |
| 3 | **ALTA** | Experiencias: `/api/travel-experiences/update` (l. 12723), `/api/provider/experience-bookings/status` (l. 12737), `/api/provider/experience-image` (l. 12458, sin control de rol), `GET /api/provider/experiences` | Misma causa: el creador de una experiencia del centro A, ya fuera de A, podía editarla, confirmar o cancelar las solicitudes y leer nombre, correo y teléfono de los clientes; como buceador podía borrar la foto. | `owns_service` por centro, control de rol en la foto, consulta por inquilino (`experience_scope`, l. 3574). **Corregido**. |
| 4 | Media | `planning_scope` (l. 4531) | El freelance veía las reservas de servicios que creó para un centro (filtraba por creador sin `center_id IS NULL`). | Filtro por inquilino. **Corregido**. |
| 5 | Media | `provider_ref` (l. 3084), `payee_of` (l. 6217), `/api/admin/users/role` (l. 12537) | Un freelance con `center_id` puesto por la administración actuaba **como propietario** del centro (datos fiscales, Stripe del centro, exportaciones de pagos, iCal) y, al revés, los pagos de sus propios servicios **se cobraban en la cuenta Stripe del centro** y podía devolverlos desde ella. | Un freelance es **siempre su propio inquilino**; la administración solo asigna centro a cuentas de centro; la migración deja sin centro a los freelance que lo tenían (queda anotado en `audit_log`). **Corregido**. |
| 6 | Media | `POST /api/travel-experiences` (l. 12476) | Un freelance podía publicar una experiencia «del centro B» (mandando `center_id`): una vez aprobada, salía en la ficha de B y se cobraba en la cuenta de B. | El centro sale de la sesión; el campo se ignora y se registra. **Corregido**. |
| 7 | Media (dentro de un centro) | `GET /api/payments/center` (l. 9789) | Alias de `/api/provider/payments` que no estaba en la lista «solo propietario»: recepción e instructores veían todos los pagos y los datos fiscales. | Añadido a `OWNER_ONLY_GET` (l. 3519) junto con `/api/provider/ical`. **Corregido**. |
| 8 | Baja | `booking_notice_recipient` (l. 2540) | `None == None` dejaba a una cuenta de centro sin centro avisar a reservas de freelance. | Usa `can_manage_booking`; 404. **Corregido**. |
| 9 | Baja | `is_guest_user` (l. 2747) | No comprobaba qué centro creó la ficha de invitado. | Se pasa el centro. **Corregido**. |
| 10 | Baja | `/api/documents/file/<id>` | 403 para un id existente y 404 para uno inexistente: revelaba qué ids existen. | Siempre 404. **Corregido**. |
| 11 | Baja | `DELETE` (l. 12946) | Sin control de rol del equipo y devolvía el texto interno del error. | `team_gate` y mensaje genérico. **Corregido**. |
| 12 | Baja | `/api/center/tariffs/save` (l. 11023), `/api/center/info-requests/read` (l. 11506) | Respondían 400 «no pertenece a tu centro» (revelaba que existe) y la segunda dejaba a un freelance marcar solicitudes de un centro que le nombraran. | 404 y filtro por inquilino. **Corregido** (detectado por la matriz). |
| 13 | Baja | Devoluciones (`refund_payment`, l. 6452; `order_tenant_problem`, l. 6440) | La devolución no comprobaba que el pago fuera del centro de la reserva (solo pasaba con el fallo 5). | `order_tenant_problem`: si no se puede probar, se bloquea y se avisa. **Corregido**. |
| 14 | Baja | `is_center_client` | Contaba reservas abandonadas en el pago para enviar promociones. | Solo reservas que el centro ve. **Corregido**. |

Bajas que **no** se tocan (no cruzan centros, se documentan): estadísticas de clics anónimos (`/api/stats/track`),
invitaciones de promociones conjuntas (requieren aceptación), puntos canjeables en otros centros (diseño del programa),
y que el administrador pueda devolver un pago desde `/status` (ahora exige motivo y queda registrado).

### Hallazgos de v50.29: siguen cerrados

| Hallazgo | Estado | Comprobación |
|---|---|---|
| Documentos (S:3021 en v50.29) | **Cerrado** | Solo el titular, un centro con reserva viva o permiso explícito, o el administrador con motivo; todo queda registrado; ahora 404 en vez de 403 (`test_g1_documents_access`). |
| Registro por teléfono (S:3290-3329) | **Cerrado** | El teléfono del registro no enlaza fichas de centros (`suggested=None`); además ahora se guarda cifrado y las búsquedas usan su huella. |
| Consulta pública de reservas (S:2939) | **Cerrado** | `/api/public/bookings/<id>` exige el token de la reserva o la sesión del dueño o del centro; si no, 404 (sin oráculo). |
| Concesión de saldo (S:4283) | **Cerrado** | `/api/provider/wallet-grant` responde 410; `points-grant` exige cliente real del centro y topes mensuales. |

## Parte B · La capa única y lo que la base garantiza

- **Una sola puerta:** `app/wod/inquilinos.py` (`Ctx`, `ctx_from_user`, `get_service`, `get_slot`, `get_booking`,
  `get_payment_order`, `slot_bookings`, `same_tenant`, `owner_filter`). Siempre añaden `WHERE` por centro y, si el
  objeto es de otro centro, lanzan `NotFound` (404). Toda la funcionalidad nueva (avisos, WhatsApp) la usa.
- **Prueba estática** (`tests/test_v50_47_estatico.py` con `scripts/seguridad/sql_centros.py`): lee con el analizador
  de Python cada sentencia SQL de `app/`. Hoy: 537 sentencias sobre tablas de centro, 192 filtran por centro en el propio
  SQL, 10 están en la capa y 344 son código anterior que lee una fila por su id **después** de comprobar en el código
  que es del centro de la sesión (o tareas de sistema que recorren todos los centros y toman el centro de cada fila).
  Esas 344 están revisadas en `docs/seguridad/sql-sin-filtro.json`; la lista **solo puede acortarse**: cualquier
  sentencia nueva sin filtro hace fallar la prueba. Reescribir las 344 de golpe no aportaba seguridad adicional a la
  que ya dan la matriz y los disparadores, y sí riesgo de romper la web: se irán pasando a la capa al tocar cada parte.
- **404 y no 403** para lo de otro centro en todas las rutas (matriz).
- **Ids no adivinables:** avisos (`uid` de 128 bits), enlaces firmados (HMAC con caducidad), documentos y archivos
  (nombre aleatorio), lotes y filas de la cola. Reservas y salidas tienen además un `uid` aleatorio; el panel sigue
  usando su número interno, que de nada sirve sin ser del centro (404). Pasar todo el panel a `uid` queda como
  **Pendiente de decisión** (cambio grande en la web sin ganancia de seguridad tras el filtro por centro).
- **Roles:** propietario, **encargado** (nuevo), recepción e instructor. Solo propietario y encargado cancelan salidas,
  envían avisos masivos y conectan WhatsApp. Quien trabaja en varios centros elige el centro de cada sesión
  (`/api/team/switch`, registrado); por defecto, su centro.
- **Archivos:** los documentos de cada centro (seguro) van a `storage/documents/centros/<c-12|f-34>/` con nombre
  aleatorio; solo se sirven a través del servidor comprobando la sesión.
- **Tareas y cachés:** las cachés de la web son solo de datos públicos; las colas nuevas llevan `provider_id` y una
  tarea sin centro no se ejecuta.

## Cómo se comprueba en cada versión

```
python -m unittest discover -s tests -p "test_v50_47_*.py"
python scripts/seguridad/sql_centros.py          # resumen de la prueba estática
python scripts/seguridad/inventario_aislamiento.py   # tabla A.1
```
