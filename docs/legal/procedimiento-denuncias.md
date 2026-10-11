# Procedimiento de denuncias de contenidos (notificación y acción)

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

Procedimiento interno para tramitar los avisos de contenido ilegal o contrario a las condiciones, conforme al Reglamento (UE) 2022/2065 de servicios digitales (DSA). Explica qué hace hoy la web, qué plazos internos se fijan, cómo decidir, qué se guarda y qué falta.

Texto publicado para el usuario: `app/legal/es/denuncias.md` (ruta `#/legal/denuncias`). Este documento no lo repite; lo desarrolla para quien modera.

## 1. Encaje en la DSA

WORLDIVES aloja contenidos de terceros y los difunde al público (fichas de centros, fotos, experiencias, promociones, perfiles de profesionales y reseñas). Es, por tanto, un **servicio de alojamiento** y, con mucha probabilidad, una **plataforma en línea** que permite celebrar contratos a distancia con comerciantes (centros y profesionales). **[PENDIENTE ABOGADO]**: confirmar la calificación.

| Artículo DSA | Obligación | Aplica a WORLDIVES | Estado en la web |
|---|---|---|---|
| 11 y 12 | Punto de contacto para autoridades y para usuarios | Sí | `{{email}}` en `denuncias.md` y en el aviso legal |
| 14 | Condiciones claras sobre moderación | Sí | Condiciones de uso, `resenas.md`, `denuncias.md` |
| 16 | Mecanismo de notificación y acción | Sí | `POST /api/reports` (ver 2) |
| 17 | Declaración de motivos al afectado | Sí | Correo `report_decision_affected` (ver 3); incompleto, ver 9 |
| 18 | Aviso a las autoridades de sospechas de delitos graves contra la vida o la seguridad | Sí | Sin soporte en el código; manual (ver 6.4) |
| 9 y 10 | Órdenes de las autoridades | Sí | Manual (ver 7) |
| 15 | Informe anual de transparencia | Exentas micro y pequeñas empresas (art. 15.2) | No existe informe en el código. **[PENDIENTE ABOGADO]** |
| 20 | Sistema interno de reclamaciones | Exentas micro y pequeñas (art. 19) | Respuesta al correo de decisión (ver 8) |
| 21 | Resolución extrajudicial | Exentas micro y pequeñas (art. 19), pero el art. 17.3.f obliga a informar de las vías de recurso | No se informa. **[PENDIENTE ABOGADO]** |
| 22 | Alertadores fiables | Exentas micro y pequeñas | Se tratan con prioridad igualmente (ver 6.3) |
| 23 | Medidas contra el uso indebido | Exentas micro y pequeñas | El texto publicado lo anuncia; sin herramienta (ver 9) |
| 24.3 | Dar a la autoridad, si la pide, la cifra de destinatarios activos | Sí, aunque sea micro o pequeña | No se mide como tal. **[PENDIENTE ABOGADO]** |
| 30–32 | Trazabilidad de comerciantes (mercados en línea) | Exentas micro y pequeñas (art. 29) | La verificación de centros cubre buena parte (`docs/legal/condiciones-centros.md`) |

**[PENDIENTE ABOGADO]** Exención de micro y pequeñas empresas (Recomendación 2003/361/CE: menos de 50 personas y menos de 10 M€ de volumen de negocio o balance). Confirmar: (a) que WORLDIVES la cumple desde el lanzamiento; (b) qué obligaciones siguen aplicando en todo caso (arts. 11–18 y 24.3); (c) si el art. 24.2 (publicar cada seis meses la media de destinatarios activos) también queda exento; (d) cuándo se pierde la exención (art. 19.2: hay 12 meses tras dejar de ser pequeña).

## 2. Qué hace el código al recibir una denuncia

### Vías de entrada

1. **Botón «Denunciar»** en el propio contenido. Abre `openReportModal()` (`public/assets/js/world-dives-v8.js`), que envía `target_type`, `target_id` y la URL de la página. Hoy hay botón en: reseña, centro, foto, punto de buceo y experiencia. **Promoción** y **perfil de profesional** se admiten en el servidor pero no tienen botón.
2. **Formulario general** en `#/legal/denuncias` (`#rp-*`): motivo, URL, explicación, nombre, email y casilla de buena fe. Sin `target_type`.
3. **Email** al punto de contacto. No entra en la base: quien modera debe darlo de alta a mano (ver 4.1).

### `POST /api/reports` (`app/server.py`)

| Paso | Código |
|---|---|
| Límite de envíos | `report_rate_limited(ip)`: más de 10 denuncias en una hora desde la misma IP → error 429. El contador está en memoria (`REPORT_LIMIT`), se pierde al reiniciar y es por proceso |
| Motivo obligatorio | Debe ser una clave de `REPORT_REASONS` |
| Explicación | Obligatoria, de 20 a 3000 caracteres |
| Buena fe | Casilla `good_faith` obligatoria (art. 16.2.d DSA) |
| Nombre y email | **Opcionales.** Si hay sesión, se toman de la cuenta |
| Contenido | Si llega `target_type`, debe estar en `REPORT_TARGETS` y existir (`report_target()`); si no, error. La URL se completa sola |
| Afectado | `report_target()` devuelve las cuentas responsables del contenido; se guarda la primera en `affected_user_id` |
| Registro | Fila en `content_reports` con `status='open'` e IP cifrada (`ip_hash`) |
| Avisos | `notify_admins(..., 'admin_content_report')` a la administración; correo `report_received` al denunciante con la referencia `DEN-00000` (solo si el email es entregable) |
| Auditoría | `audit(..., 'content_reported', 'content_report', id, {reason})` en `audit_log` |

### Motivos (`REPORT_REASONS`)

| Clave | Texto | Orientación |
|---|---|---|
| `illegal` | Contenido ilegal | Delitos, publicidad ilícita, actividad sin licencia |
| `false` | Información falsa o engañosa | Precios, titulaciones, seguros, ubicación |
| `fake_review` | Reseña falsa o no auténtica | Reseña sin experiencia real, reseña comprada, conflicto de interés |
| `ip` | Uso no autorizado de fotos o textos | Propiedad intelectual e industrial, logos |
| `safety` | Riesgo para la seguridad | Prácticas de buceo peligrosas, información de un punto que pone en riesgo |
| `privacy` | Datos personales publicados sin permiso | Nombres, fotos o datos de terceros |
| `fraud` | Fraude o estafa | Centro inexistente, cobros indebidos, suplantación |
| `other` | Otro motivo | Incumplimiento de condiciones o normas de reseñas |

### Contenidos denunciables (`REPORT_TARGETS`)

| Tipo | Afectado al que se avisa (`report_target()`) |
|---|---|
| `review` | Autor de la reseña |
| `center`, `photo` | Cuentas con rol `center` de ese centro |
| `point` | Nadie (contenido de WORLDIVES) |
| `experience` | El profesional (`provider_user_id`) o las cuentas del centro |
| `promotion` | Nadie (hoy no se identifica al anunciante) **[PENDIENTE TITULAR]** |
| `profile` | El propio profesional (`role='freelance'`) |

## 3. Qué hace el código al decidir

### `POST /api/admin/reports/resolve` (solo `admin`)

Desde *Administración → Legal → Denuncias* (botón «Resolver», `renderAdminLegal()`).

1. Estado: `actioned` (retirar o corregir), `dismissed` (desestimar) u `open` (reabrir).
2. Guarda `resolution` (hasta 2000 caracteres), `resolved_by` y `resolved_at`.
3. Si no queda abierta y hay email: correo **`report_resolved`** al denunciante con la decisión, los motivos y la indicación de que puede responder al correo si no está de acuerdo.
4. Si es `actioned` y el contenido es una **reseña**: la oculta (`center_reviews.active=0`, `moderated_at`, `moderation_reason`).
5. Si el contenido está identificado: correo/aviso **`report_decision_affected`** a cada cuenta afectada, en su idioma (`user_lang()`), con el contenido, la decisión, los motivos y la vía de respuesta. Se marca `affected_notified_at`.
6. Auditoría: `content_report_actioned`, `content_report_dismissed` o `content_report_open`.

**Importante:** para centros, fotos, puntos, experiencias, promociones y perfiles, `actioned` **no retira nada por sí solo**. Quien modera debe editar u ocultar el contenido desde su pantalla de Administración **antes** de resolver, porque el correo dice «Hemos retirado o corregido este contenido».

### `POST /api/admin/reviews/<id>/moderate` (solo `admin`)

Moderación directa de reseñas, sin denuncia previa (botón en la propia reseña, `#rh-why`).

- Ocultar exige un motivo de al menos 10 caracteres, que se envía al autor con `report_decision_affected` y la referencia `RES-00000`.
- Restaurar (`active=1`) no avisa a nadie.
- Auditoría: `review_hidden` o `review_restored` con el motivo.

## 4. Procedimiento interno

### 4.1 Recepción (día 0)

- Revisar la bandeja de *Administración → Legal → Denuncias* y el buzón `{{email}}` **cada día laborable**.
- Las denuncias por email se dan de alta en el formulario `#/legal/denuncias` con los datos del denunciante, para que queden en `content_reports` y reciba el acuse.
- Si falta la URL o no se entiende el contenido, pedir aclaración por email. Un aviso sin los datos del art. 16.2 no da «conocimiento efectivo», pero se revisa igualmente.

### 4.2 Plazos internos que se asumen

La DSA no fija plazos en días: exige actuar «de manera oportuna, diligente, no arbitraria y objetiva» (art. 16.6). Plazos propuestos **[PENDIENTE TITULAR]**:

| Caso | Primera revisión | Decisión |
|---|---|---|
| Riesgo para la vida o la seguridad, abuso de menores, fraude en curso | El mismo día | En 24 h (retirada cautelar si hay duda razonable) |
| Datos personales o imágenes de personas sin permiso | 2 días laborables | 5 días laborables |
| Propiedad intelectual, información falsa, reseña falsa | 3 días laborables | 10 días laborables |
| Resto | 5 días laborables | 15 días laborables |
| Recurso del denunciante o del afectado | 5 días laborables | 15 días laborables, por otra persona si es posible |
| Orden de una autoridad | Inmediata | En el plazo que fije la orden |

El código no controla plazos ni avisa de denuncias antiguas. **[PENDIENTE TITULAR]**: añadir un recordatorio en el panel para denuncias abiertas más de 5 días.

### 4.3 Cómo decidir

1. **Ver el contenido** en la URL y comprobar si sigue publicado.
2. **Encajar el motivo**: ¿es ilegal (ley de la UE o del Estado) o solo contrario a las condiciones? Se resuelve igual, pero la explicación debe decir cuál de las dos cosas y en qué norma o cláusula se basa (art. 17.3.d y e).
3. **Pedir la versión del afectado** cuando la decisión no sea evidente y no haya urgencia (por ejemplo, una reseña que el centro dice falsa: comprobar que existe la reserva que la habilitó, `bookings` pagada o confirmada).
4. **Elegir la medida menos gravosa** que resuelva el problema: corregir un dato, ocultar una foto, ocultar una reseña, despublicar un servicio. La suspensión de cuentas no tiene herramienta en el código (ver 9).
5. **Escribir los motivos** en «Explicación de los motivos»: hechos, norma o cláusula, medida, alcance. Se envía tal cual al denunciante y al afectado, así que sin datos personales del otro.
6. Ejecutar la medida y después **resolver** la denuncia.

Reglas de criterio:

- **Reseñas:** aplicar `app/legal/es/resenas.md`. No se ocultan reseñas negativas por ser negativas (Directiva Ómnibus, práctica desleal). Solo por ser falsas, ofensivas, con datos personales, ajenas a la experiencia o ilegales.
- **Propiedad intelectual:** retirar si el denunciante acredita ser titular o representante y el centro no demuestra licencia.
- **Seguridad:** ante la duda, retirar o advertir.
- Quien modera **no** decide sobre su propio contenido ni sobre un centro con el que tenga relación.
- No se usan medios automáticos para decidir. Si se usaran, habría que decirlo en la decisión (art. 16.6 y 17.3.c).

### 4.4 Uso indebido

`denuncias.md` avisa de que se pueden dejar de tramitar avisos manifiestamente infundados de forma reiterada. No hay herramienta: hoy solo el límite de 10 por hora y por IP. Antes de aplicar la medida: aviso previo, periodo razonable y decisión motivada (art. 23). **[PENDIENTE TITULAR]**

## 5. Registro y conservación

| Dónde | Qué queda | Conservación hoy |
|---|---|---|
| `content_reports` | Motivo, URL, tipo e id del contenido, explicación, nombre y email del denunciante, cuenta (`user_id`), `ip_hash`, estado, motivos, quién y cuándo resolvió, afectado y fecha de su aviso | **Sin plazo**: `run_retention_jobs()` no la purga |
| `audit_log` | `content_reported`, `content_report_*`, `review_hidden`, `review_restored` con quién y cuándo | Se purga a los 12 meses (`RETENTION_DEFAULTS['audit_months']`), conservando siempre las 300 últimas (`audit_keep`) |
| `center_reviews` | `active`, `moderated_at`, `moderation_reason` | Mientras exista la reseña |
| Correos | `report_received`, `report_resolved`, `report_decision_affected`, `admin_content_report` en la cola de correo | Según la limpieza de avisos (`notices_months`, 24 meses) |
| Buzón `{{email}}` | Denuncias, órdenes y recursos por email | Fuera de la web |

La administración solo ve las 200 denuncias más recientes (`LIMIT 200` en `/api/admin/legal`).

**[PENDIENTE TITULAR / ABOGADO]**: fijar un plazo para `content_reports` (propuesta: 3 años desde la resolución, o más si hay reclamación abierta) y añadirlo a `run_retention_jobs()`. Ver también `docs/legal/registro-actividades-tratamiento.md`. Si se fija un plazo más largo para las denuncias que para `audit_log`, conviene subir `audit_months` o copiar a la denuncia lo que hoy solo está en la auditoría (que ya está, salvo la restauración de reseñas).

## 6. Casos especiales

### 6.1 Denunciante anónimo

El código lo admite. No recibe acuse ni decisión. La denuncia se tramita igual, pero puede pesar menos en la valoración.

### 6.2 Afectado sin cuenta

Puntos de buceo y promociones no tienen afectado. Si el contenido es de un centro sin cuentas (por ejemplo, de la demostración), no se avisa a nadie.

### 6.3 Alertadores fiables

WORLDIVES, como pequeña empresa, no está obligada al art. 22. Aun así, los avisos de alertadores fiables designados por un coordinador de servicios digitales (en España, la CNMC) se tramitan **con prioridad**, en el primer tramo de la tabla de 4.2. El código no los distingue: anotar «Alertador fiable: <nombre>» al principio de la explicación al darlos de alta. **[PENDIENTE ABOGADO]**: confirmar coordinador español y lista pública.

### 6.4 Sospecha de delito grave (art. 18)

Si un contenido hace sospechar un delito que amenaza la vida o la seguridad de personas: avisar sin demora a la Policía Nacional o Guardia Civil (o a la autoridad del Estado afectado, o a Europol si no se sabe cuál), con toda la información disponible. Guardar copia del aviso en el buzón y anotarlo en la denuncia.

## 7. Órdenes de las autoridades (arts. 9 y 10)

1. Comprobar que la orden viene de una autoridad judicial o administrativa competente y que identifica el contenido o los datos.
2. Acusar recibo a la autoridad sin demora y ejecutar la orden en su plazo.
3. **Orden de actuar (art. 9):** retirar o bloquear el contenido, informar a la autoridad de lo hecho y de cuándo, e informar al afectado (salvo que la orden diga lo contrario) con los motivos y las vías de recurso.
4. **Orden de información (art. 10):** entregar solo los datos pedidos (de `users`, `centers`, `bookings`, `payment_orders`…) e informar al afectado salvo que la orden lo impida.
5. Registrar cada orden: fecha, autoridad, referencia, contenido, medida y fecha de cumplimiento. Hoy **no hay tabla** para esto; se lleva en una hoja aparte. **[PENDIENTE TITULAR]**
6. Revisar siempre con el abogado. **[PENDIENTE ABOGADO]**

## 8. Recursos

- Los correos `report_resolved` y `report_decision_affected` dicen: si no estás de acuerdo, **responde a este correo** y lo revisaremos de nuevo.
- Las respuestas llegan a la dirección de `WOD_MAIL_REPLY_TO` (cabecera `Reply-To`, `app/server.py`) o, si no está definida, al remitente. Configurarla con el buzón que se revisa (`{{email}}`). **[PENDIENTE TITULAR]**
- La revisión la hace, si es posible, otra persona distinta de la que decidió. Se reabre la denuncia (`status='open'`), se revisa y se vuelve a resolver con nuevos motivos (vuelven a salir los correos).
- El recurso es gratuito y no tiene plazo en el código. Propuesta: 6 meses desde la decisión, como el art. 20.1. **[PENDIENTE ABOGADO]**
- **Falta** informar de la resolución extrajudicial (art. 21) y de la vía judicial, que el art. 17.3.f exige en la declaración de motivos. **[PENDIENTE ABOGADO]**: texto a añadir a las plantillas `report_resolved` y `report_decision_affected`.

## 9. Desajustes y mejoras antes del lanzamiento

1. **Nombre y email.** `denuncias.md` dice que son necesarios (art. 16.2.c); el servidor los deja vacíos. O se piden (salvo motivo `illegal` con abuso de menores) o se ajusta el texto. **[PENDIENTE TITULAR]**
2. **URL.** El formulario general no obliga a dar la URL (art. 16.2.b). **[PENDIENTE TITULAR]**
3. **Idioma de los correos al denunciante.** `report_received` y `report_resolved` se envían siempre en castellano (`'es'`); el aviso al afectado sí va en su idioma.
4. **«Retirar» sin retirar.** Fuera de las reseñas, `actioned` no oculta nada. Riesgo de prometer una retirada que no se hizo (ver 3).
5. **Explicación vacía.** El servidor acepta resolver sin motivos; la interfaz lo pide pero no lo bloquea. El art. 17 exige motivos. Hacerla obligatoria en el servidor.
6. **Declaración de motivos incompleta** (art. 17.3): faltan las vías de recurso extrajudicial y judicial y, en su caso, si la medida es una restricción de visibilidad, de la cuenta o de pagos.
7. **Suspensión de cuentas.** No existe la herramienta (ver `docs/legal/condiciones-buceadores.md` y `condiciones-centros.md`).
8. **Sin botón** para denunciar promociones y perfiles de profesionales.
9. **Restaurar una reseña** no avisa a nadie ni guarda el motivo en `content_reports`.
10. **Límite por IP en memoria**: suficiente para un solo proceso; no frena abusos distribuidos.
11. **Sin informe de transparencia ni cifras.** Si el abogado concluye que hace falta (o para el art. 24.3), se pueden sacar de `content_reports` (por motivo, estado y tiempo medio entre `created_at` y `resolved_at`) y de `audit_log` (`review_hidden`). No existe aún la consulta.

## 10. Puntos pendientes

| Para | Punto |
|---|---|
| ABOGADO | Calificación de WORLDIVES (alojamiento, plataforma en línea, mercado en línea) |
| ABOGADO | Exención de micro y pequeñas empresas: alcance y art. 24.2 / 24.3 |
| ABOGADO | Texto de recurso extrajudicial y judicial en los correos (art. 17.3.f) |
| ABOGADO | Plazo de recurso y de conservación de `content_reports` |
| ABOGADO | Coordinador de servicios digitales español y alertadores fiables |
| ABOGADO | Revisión de cada orden de autoridad |
| TITULAR | Plazos internos (4.2), recordatorio de denuncias antiguas |
| TITULAR | Nombre, email y URL obligatorios; idioma de los correos; motivos obligatorios en el servidor |
| TITULAR | Herramientas de suspensión de cuentas y de uso indebido; registro de órdenes |
| TITULAR | Botones de denuncia para promociones y perfiles; anunciante de las promociones |
