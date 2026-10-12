# Motor de agenda común: diseño (A1.2)

**Estado: propuesta pendiente de aprobación del titular.** No se programa nada hasta que apruebe las maquetas (`docs/agenda/maquetas/`).

Principio: **un solo motor** para todo. Lo usan los freelance por días, los cursos, las salidas de siempre, los instructores, los barcos y, más adelante, las aulas y el equipo. Se apoya en lo que ya existe (servicios, salidas, reservas, modos de reserva, pagos, avisos, equipo y barcos) y **no lo duplica**. La migración solo añade; lo actual sigue funcionando igual.

## 1. Conceptos

| Concepto | Qué es | Tabla |
|---|---|---|
| **Recurso** | Quién o qué se ocupa: el propio freelance, un instructor del centro, un barco y, en la tanda 2, una piscina, un aula o el equipo con stock. | `resources` (nueva) |
| **Horario habitual** | Días y horas de trabajo del recurso, más las temporadas cerradas. | `resource_hours` y `resource_closures` (nuevas) |
| **Bloque de ocupación** | El recurso está ocupado de *inicio* a *fin* por un motivo. | `resource_blocks` (nueva) |
| **Disponibilidad** | Horario habitual menos los bloques. Se calcula; no se guarda. | — |
| **Servicio** | Igual que hoy, más una **unidad de reserva**: salida, día, medio día, horas o curso. | `provider_services` (columnas nuevas) |
| **Salida o convocatoria** | Igual que hoy (`service_slots`). En un curso, la convocatoria tiene fecha de fin y **sesiones**. | `service_slots` (+ `end_date`), `slot_sessions` (nueva) |
| **Reserva** | Igual que hoy. En las reservas por días se añaden el rango o los días sueltos y la media jornada. | `bookings` (columnas nuevas), `booking_days` (nueva) |

### Tipos de bloque
- `booking`: reserva confirmada;
- `hold`: pago en curso, 15 min;
- `session`: sesión de curso o salida con el recurso asignado;
- `manual`: bloqueo a mano, sin motivo público;
- `holiday`: vacaciones;
- `unavailable`: no disponible;
- `external`: ocupado en un calendario externo importado (tanda 2).

Cada bloque guarda su referencia (`ref_type` y `ref_id`: reserva, sesión…), quién lo creó y su estado (`active` o `released`). Los bloques **no se borran**: se liberan, y así queda el historial.

## 2. Tablas nuevas (solo se añade)

```sql
resources(id, owner_center_id, owner_user_id,          -- centro o freelance dueño
          kind,                                        -- person | boat | room | equipment
          user_id, boat_id,                            -- enlace a la persona del equipo o al barco que ya existen
          name, capacity, timezone,                    -- zona IANA, p. ej. America/Cancun
          active, created_at, updated_at)
resource_hours(resource_id, weekday, start_time, end_time)          -- 0 = lunes
resource_closures(resource_id, date_from, date_to, label)           -- temporadas cerradas
resource_blocks(id, resource_id, starts_at, ends_at,                -- UTC, ISO
                local_date_from, local_date_to,                     -- días locales, para consultar rápido por mes
                kind, ref_type, ref_id, status, private_note, created_by, created_at, released_at)
slot_sessions(id, slot_id, day_index, kind, starts_at, ends_at, local_date, start_time, end_time,
              place, dive_point_id, boat_id)                        -- sesiones de una convocatoria de curso
session_resources(session_id, resource_id, role)                    -- instructores y barco de cada sesión
course_templates(id, owner_center_id NULL = plantilla común, name, sessions_json, ratio, created_at)
booking_days(booking_id, local_date, part)                          -- part: full | am | pm
```

**Columnas nuevas:**
- **`provider_services`:**
  - `booking_unit` (`slot` por defecto, `day`, `half_day`, `hours` o `course`);
  - `timezone`;
  - `unit_rules` (JSON: días mínimos y máximos, selección continua o suelta, antelación, horas de mañana y tarde, mínimo de horas);
  - `pricing` (JSON, §5);
  - `min_participants` y `min_check_days` (E3);
  - `private_price` (E4);
  - `ratio` (alumnos por instructor).
- **`service_slots`:** `end_date`, `private` y `min_ok_at`.
- **`bookings`:** `date_to` y `days_mode`.

**Recursos que se crean solos en la migración:**
- cada freelance tiene su recurso «yo»;
- cada instructor del equipo y cada barco tienen el suyo.

Así **no se duplican** las tablas de barcos ni de equipo.

## 3. Sin solapes, también con dos confirmaciones a la vez
- **Una sola función del servidor, `agenda_block(db, resource_ids, start, end, kind, ref)`,** hace todo dentro de una transacción `BEGIN IMMEDIATE`:
  1. busca bloques activos que se crucen (`starts_at < fin AND ends_at > inicio`) en esos recursos;
  2. si hay alguno, falla con el conflicto («Laura ya tiene Rescue de 9:00 a 13:00»);
  3. si no hay ninguno, inserta los bloques.
- **Por qué es segura:** SQLite deja escribir a una sola transacción a la vez, así que de dos confirmaciones simultáneas solo gana una. La otra recibe el conflicto. Si un día la base pasa a PostgreSQL, se añade una restricción de exclusión (`EXCLUDE USING gist`) con el mismo comportamiento.
- **«Forzar»:** el responsable puede forzar un conflicto de forma consciente (A3.2). Queda marcado en el bloque y en `audit_log`.
- **La capacidad de un barco** se comprueba sumando las personas de las sesiones que se solapan.

## 4. Zona horaria
- **Cada servicio y cada recurso tiene zona horaria.** Por defecto, la del país del centro o del freelance (por ejemplo, Cancún para un guía en México).
- **Las horas de inicio y fin se guardan en UTC** (`starts_at`, `ends_at`), y además **el día local** (`local_date_from`, `local_date_to`).
- **El calendario público y la agenda se calculan con la zona del servicio**, con `zoneinfo` (incluido en Python, sin dependencias):
  - un cliente en España ve los mismos días que el guía en México;
  - los días son los del lugar del servicio, y así se indica: «Horario de Cancún».
- **Los plazos** (respuesta, pago, antelación) pasan a calcularse con la zona del servicio, no con la del servidor.
- **Pruebas previstas:**
  - cambio de hora (último domingo de marzo y de octubre en España; México ya no cambia la hora);
  - fin de mes;
  - 29 de febrero de 2028.

## 5. Precio (E2): una sola función
`booking_quote` (la de siempre) se amplía y sigue siendo la única fuente del precio. **Orden de cálculo**, con una línea de desglose para cada paso:
1. **Base por unidad:** por salida, día, media jornada u hora. Puede ser por persona o por grupo, con el máximo de personas.
2. **Temporada:** alta y baja por fechas. Se aplica **día a día**: un rango que cruza el cambio de temporada se cobra con el precio de cada día.
3. **Fin de semana:** recargo en sábado y domingo.
4. **Tramos por duración:** «1 día X €, 2 días Y €, 3 o más Z € por día» o «−10 % a partir de 3 días».
5. **Precio por número de personas:** 1, 2, 3 o «4 o más».
6. **Salida privada:** precio cerrado del grupo.
7. **Suplementos y extras:** nocturna, nitrox, fotos o vídeo, equipo y transporte, por día o por reserva.
8. **Código de promoción:** el sistema actual, sin cambios.
9. **Señal:** Fase 2, sin cambios.

**Ejemplo de resumen:** «3 días · 2 personas · 480 €», con el desglose plegable.

## 6. Flujos
- **Por días (A2):**
  - el público consulta `GET /api/agenda/public?service=ID&month=AAAA-MM`, que devuelve **solo** un estado por día: libre, ocupado, mañana ocupada, tarde ocupada, pasado o fuera de la antelación. Nada más;
  - la solicitud se guarda en `booking_days`. Mientras está pendiente **no bloquea**: el día sigue en blanco;
  - **al confirmar,** en una sola transacción:
    1. `agenda_block` ocupa los días;
    2. se envía el aviso y el enlace de pago con su plazo (Fase 1B);
    3. las demás solicitudes que se solapan se rechazan solas, con «Esas fechas ya no están disponibles. Mira otras fechas de Tito»;
  - **«Pago al reservar»:** bloque `hold` de 15 min mientras se paga, que pasa a `booking` al pagar;
  - **impago, cancelación o caducidad:** el bloque se libera (`released`).
- **Cursos (A3):**
  - **la convocatoria** es una salida (`service_slots`) con `end_date` y sus `slot_sessions`, que se crean desde el programa del servicio o desde una plantilla;
  - **al asignar instructores y barco** a cada sesión, se crean bloques `session`;
  - **las plazas** del curso son las de la convocatoria, con la misma función atómica de siempre;
  - **al reservar,** el alumno ocupa una plaza en todas las sesiones;
  - **cancelar la convocatoria** usa la cancelación de la v50.41 (avisos, elección y devolución íntegra) y libera instructores y barco.
- **Salidas de un día:** igual que hoy. Si llevan guía o barco en el manifiesto, esa asignación pasa a crear también bloques, y así se detectan los solapes entre salidas.

## 7. Planning
- **`/api/center/planning`** (el de siempre) añade los cursos como barras de varios días, con su nombre, plazas y color.
- **Vista día:** sesiones a su hora junto a las salidas: «Open Water · día 2 de 3 · mar 8:30 · Laura · Neptuno · 4 alumnos».
- **`/api/agenda/resources?from=&to=` (nueva) para la vista por recursos:**
  - filas = instructores y barcos; columnas = días;
  - en cada celda, los bloques del recurso;
  - al tocar un hueco se crea una salida o un curso con el recurso ya puesto.
- **Filtros:** por instructor, barco y tipo de servicio.
- **Agenda del freelance:**
  - la misma vista por recursos con una sola fila, más una vista de mes;
  - un toque bloquea o desbloquea un día;
  - al tocar un día ocupado se ve el detalle (cliente, servicio, personas, notas y estado del pago).

## 8. Experiencias (bloque B) sobre el mismo motor
- **Las experiencias de fechas fijas** pasan a ser convocatorias de un servicio de tipo experiencia o viaje. Heredan los modos de reserva, la señal, la caducidad, la lista de espera y las devoluciones.
- **Las experiencias «solas» que ya existen** se enlazan con una migración que solo añade: crea el servicio y su salida con las mismas plazas, y conserva las solicitudes.
- **Los servicios «A elegir fechas»** del freelance (por días) se muestran en Experiencias con esa etiqueta.

## 9. Avisos
- **Correo:** las plantillas y la cola de siempre, con textos nuevos en los 10 idiomas:
  - solicitud de días;
  - confirmada o rechazada con enlace a otras fechas;
  - recordatorio el día antes del inicio y de cada sesión;
  - solicitud a punto de caducar;
  - resumen de la agenda de mañana.
- **Push:** hoy no existe. **Propuesta:** Web Push en la app instalable, con las claves VAPID en el `.env` y la misma lista de avisos que el correo. Cada persona lo activa o desactiva en «Mi cuenta». Ver «Pendiente de decisión».

## 10. Privacidad y permisos
- **La API pública** solo devuelve el estado de cada día. Nunca da nombres, motivos, horas ni referencias.
- **La agenda y la vista por recursos** solo las ven el dueño y su equipo, con los permisos de la Fase 6.6:
  - el instructor ve su fila, en solo lectura;
  - recepción organiza;
  - otro centro recibe un 403.
- **La exportación de datos** (Fase 6.5) añade los recursos, los bloques, las convocatorias y las sesiones.

## 11. Rendimiento
- **Índices:**
  - `resource_blocks(resource_id, local_date_from)` y `(resource_id, starts_at, ends_at)` para las búsquedas de solapes;
  - `resources(owner_center_id, kind)`;
  - `slot_sessions(slot_id)` y `(local_date)`.
- **Un mes de agenda** son 2 consultas (los recursos y sus bloques del mes), sin una consulta por día.
- **Objetivo:** 300 ms o menos en el servidor para un mes de un centro con 20 instructores y 5 barcos, o para el calendario público de un freelance, **con 500 centros activos** en la base de pruebas. Se medirá con un script que crea esos datos en una copia de la base.

## 12. Opciones avanzadas (A5)
- **Cada opción se activa por servicio** en un apartado plegable, «Más opciones», y viene apagada por defecto.
- **Cada opción es también una función del plan** (`PLAN_FEATURES`), así que el titular decide después en qué plan va cada una.
  - Claves previstas: `agenda_days`, `courses`, `resources_view`, `flex_pricing`, `min_participants`, `private_trips`, `participant_links` (tanda 1), y `waitlist_plus`, `availability_alerts`, `multi_service`, `ical_import`, `equipment_stock`, `recurring`, `public_calendar`, `offline_week` (tanda 2).

## 13. Entregas previstas

| Versión | Contenido |
|---|---|
| v50.44 | Motor de agenda (recursos, bloques, zona horaria, sin solapes), freelance por días y medio día (A2) y avisos (A4) |
| v50.45 | Cursos de varios días, plantillas, instructores y barcos, planning con barras, vista día y vista por recursos (A3) |
| v50.46 | A5 tanda 1: E1–E6 (unidades, tarifas, mínimo de participantes, salidas privadas, reprogramar con diferencia y datos por participante) |
| v50.47–v50.48 | Bloque B: imagen, organizador reconocible, publicación inmediata con revisión, reserva sobre el motor común y agencia de viajes desactivada |
| v50.49–v50.50 | A5 tanda 2: E7–E14 |

## Pendiente de decisión del titular
1. **Aprobar las maquetas** de `docs/agenda/maquetas/` (o pedir cambios).
2. **Push:** ¿Web Push en la app instalable? (Necesita claves VAPID en el `.env`, sin coste.)
3. **En qué plan va cada opción avanzada.** Mientras tanto, todas quedan disponibles en todos los planes.
4. **Zona horaria por defecto** de un freelance sin dirección: la del país de su perfil, ¿de acuerdo?
5. **Solicitudes pendientes que se solapan:** ¿se rechazan solas al confirmar otra (como pide el encargo) o se avisa antes al freelance de cuántas se rechazarán? Propuesta: las dos cosas. Se avisa en la confirmación y se rechazan al confirmar.
