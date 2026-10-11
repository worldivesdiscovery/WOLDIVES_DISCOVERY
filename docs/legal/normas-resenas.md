# Ficha de revisión: Normas de las reseñas

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

## Texto publicado

- Castellano (referencia): `app/legal/es/resenas.md`. Inglés (oficial): `app/legal/en/resenas.md`.
- Ruta pública: `#/legal/normas-resenas`. Enlazada desde el pie y desde la sección de reseñas de cada centro.
- No necesita aceptación propia: forma parte de las condiciones de uso (cláusula 4 de `terminos.md`).
- Normativa de referencia: art. 20.7 y anexo I (puntos 23 ter y 23 quater) de la Directiva 2005/29/CE tras la Directiva (UE) 2019/2161 («Ómnibus»), traspuestos en el TRLGDCU y la Ley 3/1991 de Competencia Desleal; Reglamento (UE) 2022/2065 (DSA) para las denuncias.

Esta ficha no repite el texto. Resume cada cláusula, indica en qué parte del código se apoya y lista lo que falta revisar.

## Rutas y tablas

| Ruta | Quién | Qué hace |
|---|---|---|
| `POST /api/centers/<id>/reviews` | Usuario con sesión, salvo roles `center` y `admin` | Crea o edita su reseña (1–5 estrellas, título 120, texto 1200). Exige reserva con el centro **no cancelada ni rechazada** y **pagada o confirmada/completada**. Una por usuario y centro (si existe, se actualiza). Siempre `verified=1`. Interruptor `require_switch(db,'reviews')` |
| `GET /api/centers/<id>` | Público | Devuelve las **50 reseñas activas más recientes** (`ORDER BY created_at DESC`), con media y número de todas las activas |
| `POST /api/reviews/<id>/reply` | Cuenta `center` del centro valorado | Una respuesta (5–1000 caracteres) en la propia fila (`reply_body`, `reply_at`, `reply_user_id`); texto vacío la borra. Email al autor solo con la primera respuesta (`review_replied`) |
| `POST /api/reports` | Cualquiera, con o sin cuenta | Denuncia con motivo (`REPORT_REASONS`, incluye `fake_review`), explicación de 20 caracteres o más, casilla de buena fe; 10 por IP y hora (`report_rate_limited()`); acuse con referencia `DEN-00000` (`report_received`); aviso a administradores (`admin_content_report`) |
| `POST /api/admin/reports/resolve` | Administrador | Estado `actioned` o `dismissed` con motivo; si es una reseña y se actúa, se oculta (`active=0`, `moderated_at`, `moderation_reason`); email al denunciante (`report_resolved`) y al afectado (`report_decision_affected`) |
| `POST /api/admin/reviews/<id>/moderate` | Administrador | Oculta (motivo de 10 caracteres o más, obligatorio) o restaura; al ocultar, email al autor con el motivo |

Tabla `center_reviews` (`rating`, `title`, `body`, `active`, `verified`, `reply_*`, `moderated_at`, `moderation_reason`). Tabla `content_reports`. Todo queda en `audit_log` (`center_review_created/updated`, `review_reply_saved/deleted`, `review_hidden/restored`, `content_report_*`).

Pruebas: `test_single_editable_reply`, `test_report_review_and_decision_to_both_parties`, `test_admin_moderation_needs_reason`, `test_reports_on_centre_point_photo` (`tests/test_phase5_legal_catalog.py`), `test_feature_switches` (`tests/test_phase6_centers.py`), recorrido en `tests/e2e_legal_catalog.py`.

## Cláusulas

| # | Qué dice | Dónde se apoya en el código |
|---|---|---|
| 1. Quién puede escribir | Solo clientes con reserva pagada o confirmada; todas son verificadas; una por centro, editable. Centros, profesionales y administradores no pueden. | Consulta `completed` en `POST /api/centers/<id>/reviews`; `can_review` en `GET /api/centers/<id>`. Bloqueo de roles: solo `{'center','admin'}` (ver desajustes: **el freelance no está bloqueado**). |
| 2. Qué publicamos | Positivas y negativas, sin ordenar ni ocultar por valoración; media simple; nadie paga por quitar o mejorar. | Orden por fecha (`ORDER BY cr.created_at DESC`). Media `ROUND(AVG(rating),1)` de las activas. No hay ninguna ruta de pago ligada a reseñas ni filtro por valoración. Solo se muestran las 50 más recientes (ver desajustes). |
| 3. Qué retiramos | Insultos, datos de terceros, temas ajenos, falsas o pagadas sin decirlo. Botón «Denunciar»; decisión motivada; aviso a ambas partes. | Botón `wd-report` con `data-report="review"` en cada reseña (`reviewCard()` en `world-dives-v8.js`). `/api/reports`, `/api/admin/reports/resolve`, `/api/admin/reviews/<id>/moderate`. |
| 4. Respuesta del centro | Una única respuesta pública, editable o borrable; sin hilos; respetuosa y sin datos del cliente. | `POST /api/reviews/<id>/reply` (columna única, no tabla de mensajes). Sin hilos: decisión del titular nº 2, `test_g11_no_free_messaging`. El contenido de la respuesta no se filtra; se controla por denuncia. Perfiles del equipo: `owner` y `reception` pueden responder; `instructor` no (`team_gate()`, `INSTRUCTOR_POST_OK`). |
| 5. Después de la inmersión | Email opcional para invitar a valorar. | Tarea horaria (`run_booking_deadlines()` o la tarea de recordatorios): reservas `confirmed`/`completed` con fecha entre ayer y hace 7 días, una sola vez (`bookings.review_asked_at`), plantilla `review_request` (`notify_booking(…,'review')`). |

## Avisos (notificaciones)

| Hecho | A quién | Plantilla |
|---|---|---|
| Nueva reseña | **Nadie** (el centro no recibe aviso) | — |
| Primera respuesta del centro | Autor de la reseña | `review_replied` |
| Edición de la respuesta | Nadie | — |
| Denuncia recibida | Denunciante (si dio email) y administradores | `report_received`, `admin_content_report` |
| Denuncia resuelta | Denunciante y afectados (autor de la reseña) | `report_resolved`, `report_decision_affected` |
| Reseña ocultada por la administración | Autor | `report_decision_affected` (referencia `RES-00000`) |
| Reseña restaurada | Nadie | — |
| Tras la inmersión | Buceador | `review_request` |

## Desajustes entre el texto y el código

1. **Una reseña ocultada se puede volver a publicar editándola.** `POST /api/centers/<id>/reviews` busca la reseña del usuario sin mirar `active` y la actualiza con `active=1`. Así se salta la moderación. **[PENDIENTE TITULAR]**: no reactivar si `moderated_at` está puesto (o pasar la edición a revisión).
2. **Profesionales freelance.** El texto dice que no pueden escribir reseñas; el código solo bloquea `center` y `admin`. Añadir `freelance` al bloqueo.
3. **«Inmersión verificada».** La etiqueta de cada reseña dice «✓ Inmersión verificada» y la sección dice «buceadores que han completado una inmersión», pero el código solo exige una reserva pagada o confirmada: se puede reseñar **antes** de la actividad. El texto legal («reserva pagada o confirmada») es correcto; la interfaz exagera. Elegir: exigir que la fecha haya pasado (o estado `completed`), o cambiar la etiqueta a «Reserva verificada». **[PENDIENTE ABOGADO]** (Directiva Ómnibus: informar de cómo se verifica).
4. **«Publicamos todas».** La ficha muestra solo las 50 más recientes, aunque la media cuenta todas. Añadir paginación o decirlo.
5. **Nombre completo en la API.** `GET /api/centers/<id>` devuelve `u.fullname` completo de cada autor; la web solo muestra el primer nombre. Devolver solo el nombre de pila (minimización).
6. **«El centro o profesional valorado».** Solo se pueden valorar centros: no hay reseñas de profesionales freelance. Quitar «o profesional» o crear las reseñas de freelance.
7. **Interruptor general.** La administración puede desactivar todas las reseñas (`/api/admin/features`, `reviews`); entonces la ficha no muestra ninguna. El texto no lo prevé; conviene decir que, si se desactivan, se desactivan todas por igual.
8. **Reseña de una reserva cancelada después.** La reseña sigue publicada aunque la reserva se cancele más tarde. Decidir. **[PENDIENTE TITULAR]**
9. Sin desajuste en: respuesta única, aviso a ambas partes, motivo obligatorio, orden por fecha y media simple.

## Puntos para el abogado

- **[PENDIENTE ABOGADO]** Información sobre la verificación de reseñas (art. 20.7 TRLGDCU tras la Ley 4/2022 y el RDL 24/2021): si el texto basta y si la etiqueta debe decir «reserva» en lugar de «inmersión».
- **[PENDIENTE ABOGADO]** Base jurídica de la invitación a reseñar (interés legítimo) y si el email debe llevar un enlace para no recibir más.
- **[PENDIENTE ABOGADO]** DSA: si la plataforma es «plataforma en línea» (arts. 16, 17 y 20): declaración de motivos, vía de recurso interno contra la decisión (hoy no existe una ruta para recurrir; solo responder al email) y transparencia.
- **[PENDIENTE ABOGADO]** Plazo de conservación de reseñas ocultas y de `content_reports` (hoy sin plazo).
- **[PENDIENTE ABOGADO]** Responsabilidad de WORLDIVES por el contenido de reseñas y respuestas (art. 6 DSA, exención de alojamiento).
