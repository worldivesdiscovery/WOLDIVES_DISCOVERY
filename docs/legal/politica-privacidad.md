# Ficha de revisión: Política de privacidad (por rol)

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

## Texto publicado

- Castellano (referencia): `app/legal/es/privacidad.md`. Inglés (oficial): `app/legal/en/privacidad.md`.
- Ruta pública: `#/legal/privacidad`. Enlazada en el pie, en el registro y en la página de cookies.
- Se acepta al registrarse y cada versión nueva se vuelve a aceptar al entrar (`LEGAL_ACCEPTANCE`, `legal_pending_for()`, `POST /api/legal/accept`, tabla `legal_acceptances`). Aviso por email al publicar una versión nueva (`notify_legal_change()`).
- Marcadores: `{{owner_name}}`, `{{trade_name}}`, `{{nif}}`, `{{address}}`, `{{dpo_email}}`, `{{hosting}}` (*Administración → Legal*, `LEGAL_FIELDS`).
- Plazos: valores por defecto de `RETENTION_DEFAULTS` en `app/server.py`, que la administración cambia dentro de `RETENTION_LIMITS` (*Administración → Legal → Conservación de datos*, `GET/POST /api/admin/retention`). Los aplica cada día `run_retention_jobs()` (prueba `test_retention_job`).

Esta ficha no repite el texto. Resume cada cláusula, la ordena **por rol**, indica en qué parte del código se apoya y lista lo que falta revisar. El detalle por actividad está en `docs/legal/registro-actividades-tratamiento.md`; el encargo del centro, en `docs/legal/anexo-encargado-tratamiento.md`.

## Plazos reales del código

| Dato | Valor por defecto | Límites | Dónde |
|---|---|---|---|
| Cuenta de buceador sin actividad | 36 meses, aviso por email y borrado 30 días después | 12–120 meses | `inactive_months`, `RETENTION_WARN_DAYS = 30`, plantilla `account_inactive`. Solo `role='recreational'`; no borra si hay reservas futuras |
| Documentos caducados | 12 meses después de la caducidad (archivo y fila) | 1–60 | `expired_docs_months`, `delete_document_file()` |
| Avisos de los centros (`messages`) | 24 meses | 3–120 | `notices_months` |
| Registro de actividad (`audit_log`) | 12 meses, conservando siempre las últimas 300 entradas | 3–120 / 50–100 000 | `audit_months`, `audit_keep` |
| Registro de accesos (`logs/access.log`) | 14 días, IP truncada (/24 o /48), sin cadena de consulta | 1–365 | `WOD_LOG_RETENTION_DAYS` (`app/wod/ops.py`), `log_ip()` (`app/wod/security.py`) |
| Sesiones | 8 horas desde el inicio de sesión | `WOD_SESSION_TTL_SECONDS` | `SESSION_TTL_SECONDS = 28800`; limpieza en el bucle de mantenimiento |
| Cola de correos (`email_outbox`, con el cuerpo) | 120 días | fijo | borrado diario en `app/server.py` (línea con `days=120`) |
| Enlaces de recuperación de contraseña | 1 hora | fijo | `new_password_reset()` |
| Enlace de eliminación de cuenta | 24 horas, un solo uso | fijo | `request_account_deletion()` |
| Reservas y pagos | El texto dice 6 años. **El código no los borra nunca** | — | `run_retention_jobs()` lo indica en su docstring |
| Aceptaciones legales y `consent_log` | El texto dice «hasta 5 años después». **El código no los borra** | — | ver desajustes |
| Copias de seguridad | 48 horarias, 30 diarias, 12 mensuales | `WOD_BACKUP_KEEP_*` | `app/wod/backup.py`, `run_backup_jobs()` |

## Cláusulas del texto

| # | Qué dice | Dónde se apoya en el código |
|---|---|---|
| 1. Responsable | Datos del titular. El centro es **responsable independiente** de los datos que recibe al reservar. | Marcadores (`legal_fill()`). El papel del centro: ver «Papel de WORLDIVES y del centro». |
| 2. Qué datos | Cuenta, ficha opcional, documentos (sin datos de salud), reservas y pagos (solo marca y 4 últimos dígitos), Log Book, reseñas, puntos, avisos, consentimientos, datos técnicos, ubicación no guardada, datos de centros. | Tablas `users`, `user_profiles`, `user_documents` (`DOCUMENT_TYPES`, `MEDICAL_WORDS`, `test_g6_no_medical_certificates`), `bookings`, `payment_orders` (`card_brand`, `card_last4`), `logbook_entries`, `center_reviews`, `points_ledger`, `messages`, `consent_log`, `legal_acceptances`. Ubicación: `navigator.geolocation` en el navegador; las coordenadas van a `GET /api/top-dives?lat=…&lon=…`, no se guardan en la base y el registro de accesos no guarda la cadena de consulta. En `localStorage` (`wd_top10`) solo queda `{geo:true}`, no las coordenadas del GPS. |
| 3. Finalidades y bases | Contrato, obligación legal, interés legítimo, consentimiento para marketing, DSA para denuncias. Sin decisiones automatizadas; orden explicado en `#/legal/clasificacion`. | `set_marketing_consent()`; `content_reports`; `DIRECTORY_SORT_KEYS`. |
| 4. Destinatarios | Centro (ficha y documentos solo con reserva propia viva o datos compartidos por QR), Stripe, alojamiento, SMTP, mapas (base propio, Esri por proxy, GEBCO directo), vídeos tras clic, autoridades. | `center_can_see_user()`, `provider_can_see_user()`, `grant_data_share()` (`source='qr_checkin'`), pruebas `test_g1_documents_access`, `test_g5_checkin_requires_consent`, `test_g5_manual_booking_never_links_registered_account`. Mapas: `map_config`, proxy de satélite. Vídeos: ver `docs/legal/cookies-terceros.md`. |
| 5. Plazos | Tabla de plazos. | Ver «Plazos reales del código». |
| 6. Derechos | ZIP de datos, eliminar cuenta con confirmación por email, cambiar email con verificación, baja de novedades, resto por email en un mes, reclamación ante la AEPD. | Ver «Cómo se ejercen los derechos en la web». |
| 7. Seguridad | HTTPS, contraseñas cifradas, TOTP (obligatorio para administradores), accesos a documentos registrados, copias **cifradas**. | PBKDF2 (`app/wod/security.py`), `test_admin_works_only_with_totp`, `test_production_refuses_admins_without_totp`, `audit_log` (`document_access_denied`). Copias: **no están cifradas** en origen (ver desajustes). |
| 8. Menores | Mayores de 18; las reservas de menores las hace un adulto. | Casilla del registro (declaración, sin comprobar edad). |
| 9. Cambios | Aviso por email y nueva aceptación; versiones anteriores al final. | `legal_publish()`, `notify_legal_change()`, `/api/legal/history`, `test_new_version_must_be_accepted_again`. |

## Tablas por rol

### Visitante (sin cuenta)

| Aspecto | Contenido | Código |
|---|---|---|
| Datos | IP truncada en el registro de accesos; IP seudonimizada en memoria para no contar dos veces una visita; texto de búsqueda de localidad; coordenadas si pulsa «Usar mi ubicación» (no se guardan); si escribe a un centro: nombre, email, teléfono, mensaje, fecha, participantes, idioma, `ip_hash`; si denuncia: nombre, email, motivo, explicación, `ip_hash`; cookie de sesión no se crea sin iniciar sesión | `logs/access.log`; `_STAT_SEEN` / `provider_stats_daily`; `/api/geocode` → `geocode_search()` (solo el texto a Nominatim desde el servidor); `info_requests`; `content_reports` (`POST /api/reports`) |
| Finalidad | Seguridad; estadísticas agregadas para los centros; buscar localidades; hacer llegar la consulta al centro; tramitar denuncias | — |
| Base jurídica | Interés legítimo (seguridad, estadísticas); consentimiento para enviar la consulta al centro (casilla); obligación legal (DSA) para denuncias | **[PENDIENTE ABOGADO]** base de `info_requests` |
| Destinatarios | Alojamiento; el centro destinatario (consulta, email `info_request`); SMTP; Esri y Nominatim sin datos personales; GEBCO recibe la IP si se elige esa capa; YouTube/Vimeo/Google tras clic | `map_config`, proxy de satélite, `docs/legal/cookies-terceros.md` |
| Plazo | Accesos 14 días; memoria de visitas hasta reinicio; **consultas y denuncias sin plazo en el código** | ver desajustes |
| Derechos | Por email a `{{dpo_email}}`; no hay herramienta en la web | — |

### Buceador (rol `recreational`)

| Aspecto | Contenido | Código |
|---|---|---|
| Datos | Cuenta (nombre, email, usuario, contraseña con hash, idioma, TOTP opcional); ficha opcional (teléfono, país, ciudad, fecha de nacimiento, titulación, contacto de emergencia, tallas, lastre); documentos (titulación, seguro, identidad, adicional; sin salud); reservas y pagos; Log Book; reseñas; puntos y canjes; avisos de centros; consentimientos y aceptaciones | `users`, `user_profiles`, `user_documents`, `bookings`, `payment_orders`, `logbook_entries`, `center_reviews`, `points_ledger`, `reward_redemptions`, `messages`, `consent_log`, `legal_acceptances`, `data_shares` |
| Finalidad | Cuenta, reservas y emails del servicio; recordatorios 48 h y 24 h; caducidad de documentos; petición de reseña; puntos; marketing con consentimiento | `notify_booking()` (evento `review` → `review_request`), `queue_document_alerts()`, `set_marketing_consent()` |
| Base jurídica | Contrato; obligación legal (aceptaciones, conservación); interés legítimo (seguridad, petición de reseña); consentimiento (marketing) | **[PENDIENTE ABOGADO]** petición de reseña por interés legítimo; no hay casilla de oposición en la web |
| Destinatarios | Centro con el que reserva (datos de la reserva siempre; ficha y documentos solo con reserva online viva o `data_shares` activo); Stripe (en la cuenta del centro); alojamiento; SMTP; público (reseñas con nombre abreviado) | `center_can_see_user()`, `INACTIVE_BOOKING_STATES` |
| Plazo | Cuenta: mientras exista; 36 meses sin actividad → aviso → borrado a los 30 días. Documentos caducados: 12 meses. Avisos: 24 meses. Reservas: anonimizadas al borrar la cuenta, sin purga a los 6 años | `run_retention_jobs()`, `delete_user_account()` |
| Derechos en la web | ZIP de datos; JSON; eliminar cuenta con confirmación por email; cambio de email verificado; contraseña; TOTP; baja de marketing; «Centros que ven tu ficha» con revocación; borrar documentos | ver la tabla siguiente |

### Centro y su equipo (rol `center`, perfiles `owner`, `reception`, `instructor`)

| Aspecto | Contenido | Código |
|---|---|---|
| Datos | Cuentas del personal (nombre, email, contraseña, TOTP); perfil en el equipo; invitaciones por email; solicitud de alta y verificación (teléfono, email, web, nota, método); datos fiscales (`entity_type`, `legal_name`, `tax_id`, `tax_id_country`, `registration_number`, `fiscal_address`, `birth_date` si es autónomo); seguro (aseguradora, póliza, caducidad, certificado privado); cuenta de Stripe (solo el identificador y su estado); plan y cuota; acciones del equipo en `audit_log` | `users`, `center_members`, `team_invites` (`TEAM_ROLES`, `team_gate()`), `center_claims`, `centers`, `plan_payments`, `audit_log.center_id` |
| Finalidad | Gestionar la cuenta y el equipo; verificar el centro; justificantes con los datos del prestador; cobrar en su cuenta de Stripe; DAC7; plan anual; trazabilidad | `stripe_controller()`, `dac7_report()`, `run_plan_jobs()`, `run_insurance_alerts()` |
| Base jurídica | Contrato con el centro; obligación legal (DAC7 **[PENDIENTE GESTORÍA]**, contabilidad); interés legítimo (verificación, seguridad) | — |
| Destinatarios | Alojamiento; SMTP; Stripe (cuenta de WORLDIVES para la cuota; cuenta del centro para los cobros); Agencia Tributaria (modelo 238) si procede; público (ficha del centro: datos comerciales) | — |
| Plazo | Mientras dure la relación; **no se borran por inactividad**; plan: 6 años **[PENDIENTE GESTORÍA]**; DAC7: 10 años según la Directiva **[PENDIENTE GESTORÍA]** | `run_retention_jobs()` solo trata buceadores |
| Derechos en la web | ZIP y JSON de la cuenta personal; **exportación CSV** de clientes, reservas, servicios y pagos (pagos solo el propietario) en todos los planes; baja **solo escribiendo** (la web la rechaza) | `/api/account/export`, `/api/center/export?kind=…` (`provider_export()`), `/api/account/delete` devuelve «Las cuentas de centro… se dan de baja escribiéndonos» |
| Clientes del centro | Fichas sin cuenta creadas o importadas por el centro (`guest_center_id`), reservas manuales y por API, planning: WORLDIVES actúa como **encargado** | `is_guest_user()`, `/api/integrations/bookings`, `docs/legal/anexo-encargado-tratamiento.md` |

### Profesional freelance (rol `freelance`)

| Aspecto | Contenido | Código |
|---|---|---|
| Datos | Como el centro, pero de una persona física: cuenta, perfil público (biografía, avatar, redes sociales), datos fiscales con `birth_date`, seguro, cuenta de Stripe propia, servicios, plan | `users` (`provider_bio`, `avatar_url`, `*_url`, `legal_name`, `tax_id`, `birth_date`, `stripe_account_id`), `provider_services` con `provider_user_id` |
| Finalidad | Publicar su perfil y servicios; cobrar en su cuenta de Stripe; justificantes; DAC7; plan | — |
| Base jurídica | Contrato; obligación legal (DAC7); interés legítimo (verificación) | — |
| Destinatarios | Público (perfil `#/profesional?id=…`, denunciable como `profile`); Stripe; alojamiento; SMTP; Agencia Tributaria si procede | `REPORT_TARGETS` |
| Plazo | Mientras dure la relación; no se borra por inactividad | — |
| Derechos en la web | ZIP y JSON; CSV de sus reservas y clientes (`provider_export()` con `provider_user_id`); ve la ficha del buceador solo con reserva online propia viva (`provider_can_see_user()`); baja escribiendo | — |

### Administrador (rol `admin`)

| Aspecto | Contenido | Código |
|---|---|---|
| Datos | Cuenta con TOTP obligatorio; todas sus acciones en `audit_log` (moderación, verificación, exportación DAC7, cambios legales y de conservación, acceso a documentos) | `test_admin_works_only_with_totp`, `audit()` |
| Finalidad | Operar la web; trazabilidad | — |
| Base jurídica | Relación con el titular (contrato laboral o de servicios) e interés legítimo (seguridad) | **[PENDIENTE ABOGADO]** informar al personal aparte |
| Destinatarios | Alojamiento | — |
| Plazo | Mientras tenga el rol; `audit_log` 12 meses / últimas 300 | — |
| Derechos en la web | ZIP y JSON; baja escribiendo | — |
| Acceso a datos de otros | Ve documentos de buceadores (registrado), denuncias, pagos, DAC7; no ve números de tarjeta | `audit_log`, `payment_orders` |

## Cómo se ejercen los derechos en la web

| Derecho | Dónde | Ruta / función | Prueba |
|---|---|---|---|
| Acceso y portabilidad | «Mi cuenta → Descargar mis datos» | `GET /api/account/export?format=zip` → `export_user_zip()` (`datos.json`, `LEEME.txt`, carpeta `documentos/`); `GET /api/account/export` (JSON, `export_user_data()`) | `test_zip_export_with_documents` |
| Supresión (buceador) | «Mi cuenta → Eliminar mi cuenta», con contraseña y enlace por email (24 h) | `POST /api/account/delete` → `request_account_deletion()`; `POST /api/account/delete/confirm` → `delete_user_account()`. Bloqueado si hay reservas futuras | `test_deletion_is_confirmed_by_email`, `test_deletion_cascades` |
| Supresión (centro, freelance, admin) | Solo por email | `/api/account/delete` lanza `PermissionError` | — |
| Rectificación | «Mi cuenta», ficha, email con verificación | `/api/account/profile`, `/api/account/email`, `/api/account/identity` | — |
| Retirar consentimiento de marketing | Enlace del email (un clic, `List-Unsubscribe`) o «Mi cuenta» | `GET/POST /api/marketing/unsubscribe?t=…` (página `#/baja`), `POST /api/account/marketing`, `set_marketing_consent()` + `consent_log` | `test_commercial_emails_only_with_consent_and_one_click_unsubscribe` |
| Dejar de compartir la ficha con un centro | «Mi cuenta → Centros que ven tu ficha» | `GET /api/account/shares`, `POST /api/account/shares/revoke` (`data_shares.revoked_at`) | `test_g5_checkin_requires_consent` |
| Oposición, limitación, resto | Email a `{{dpo_email}}` | Sin herramienta; plazo de un mes | — |

## Papel de WORLDIVES y del centro

- El texto dice que el centro es **responsable independiente** de los datos que recibe al reservar, y que WORLDIVES es responsable de la plataforma.
- Para los clientes que el centro crea, importa o reserva a mano, y para su planning, el anexo trata a WORLDIVES como **encargado** del centro (`docs/legal/anexo-encargado-tratamiento.md`). **El texto publicado no lo menciona.**
- **[PENDIENTE ABOGADO]** Confirmar el reparto: responsables independientes para las reservas online; encargo para las fichas de cliente del centro; y decidir si las solicitudes de información (`info_requests`) y la ficha compartida por QR (`data_shares`) son comunicación entre responsables o encargo. Descartar la corresponsabilidad (art. 26 RGPD).
- **[PENDIENTE ABOGADO]** Papel de Stripe en los cargos directos (responsable frente al buceador y al centro, según sus condiciones).

## Desajustes entre el texto y el código

1. **Reservas y pagos «6 años».** El código no los borra nunca (`run_retention_jobs()` lo excluye a propósito). Además, al eliminar la cuenta se borran `contact_phone` y notas de la reserva, pero **no `contact_email` ni `contact_name`**. **[PENDIENTE TITULAR]**
2. **Aceptaciones y consentimientos «hasta 5 años después».** `legal_acceptances` y `consent_log` no se borran: la fila del usuario se anonimiza y no se elimina, así que el `ON DELETE CASCADE` no actúa. **[PENDIENTE TITULAR]**
3. **Sesiones «8 horas sin actividad».** El código cierra la sesión a las 8 horas **desde que se inició**, aunque haya actividad (`current - session['created_at'] > SESSION_TTL_SECONDS`). Cambiar el texto («8 horas como máximo») o el código.
4. **Copias «cifradas».** Las copias no se cifran en origen (`app/wod/backup.py`; registro de actividades, apartado 16). Quitar la palabra o cifrarlas. **[PENDIENTE TITULAR]**
5. **«Eliminar mi cuenta: en Mi cuenta».** Solo vale para buceadores. Centros, freelance y administradores deben escribir. El texto no lo dice.
6. **Datos que el texto no menciona:** solicitudes de información a centros (`info_requests`), datos del denunciante (`content_reports`), datos fiscales y fecha de nacimiento de autónomos (DAC7), certificado del seguro, equipo del centro e invitaciones, perfil público del freelance, cola de correos con el cuerpo (120 días), estadísticas agregadas. Conviene una sección por rol en el texto o al menos una línea para cada uno.
7. **Plazos que faltan en el texto** y tampoco existen en el código: `info_requests`, `content_reports`, fichas de cliente del centro. Las cuentas profesionales no se borran por inactividad (el texto habla de «cuentas» en general).
8. **Ubicación:** coincide (coordenadas enviadas a `/api/top-dives` sin guardarse). Matiz: si el visitante elige un punto en el mapa o busca una localidad, esa posición sí queda en su navegador (`localStorage` `wd_top10`); ver `docs/legal/cookies-terceros.md`.
9. **Al eliminar la cuenta** no se revocan los `data_shares` ni se pone `marketing_consent=0`. No hay fuga (la ficha se borra y el email anonimizado termina en `.local`, que `mail_deliverable()` descarta), pero conviene limpiarlo.
10. **Contacto de emergencia** (datos de un tercero) no se menciona en el texto.

## Puntos para el abogado

- **[PENDIENTE ABOGADO]** Papel de WORLDIVES frente al centro (ver apartado anterior).
- **[PENDIENTE ABOGADO]** Transferencias a centros fuera del EEE (art. 49.1.b RGPD) y cómo informarlas.
- **[PENDIENTE ABOGADO]** Base jurídica de la petición de reseña y si hace falta un enlace de oposición en el propio email.
- **[PENDIENTE ABOGADO]** Contacto de emergencia (art. 14 RGPD); documento de identidad (minimización); campos que podrían ser datos de salud (lastre, notas de equipo).
- **[PENDIENTE ABOGADO]** Delegado de protección de datos: confirmar que no es obligatorio.
- **[PENDIENTE ABOGADO]** Plazos de conservación de denuncias, solicitudes de información, aceptaciones legales y consentimientos.
- **[PENDIENTE ABOGADO]** Edad mínima: 18 años declarada con casilla; si basta sin comprobación (art. 7 LOPDGDD fija 14 para el consentimiento).
- **[PENDIENTE GESTORÍA]** Plazos de conservación fiscales (6 años mercantiles, 4 años tributarios, 10 años DAC7).
