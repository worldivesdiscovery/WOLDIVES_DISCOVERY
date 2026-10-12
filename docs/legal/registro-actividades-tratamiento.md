# Registro de actividades de tratamiento (art. 30 RGPD)

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

Registro interno de WORLDIVES DISCOVERY. Se ha elaborado leyendo el código: los campos salen de `BASE_SCHEMA` en `app/server.py` y de las rutas que los usan. Los plazos son los valores por defecto del código, que la administración puede cambiar en *Administración → Legal → Conservación de datos* (`RETENTION_DEFAULTS`, `RETENTION_LIMITS`, `run_retention_jobs()`).

Hay que **revisarlo en cada versión** que añada tablas o columnas con datos personales.

## Datos del responsable

| | |
|---|---|
| Responsable | {{owner_name}} ({{trade_name}}) |
| NIF | {{nif}} |
| Domicilio | {{address}} |
| Contacto de privacidad | {{dpo_email}} |
| Delegado de protección de datos | [pendiente de completar]. **[PENDIENTE ABOGADO]**: confirmar que no es obligatorio (art. 37 RGPD y art. 34 LOPDGDD) |
| Representante en la UE | No aplica (establecido en España) |

## Destinatarios y transferencias comunes

Para no repetirlos en cada actividad:

| Código | Destinatario | Papel | Ubicación y garantías |
|---|---|---|---|
| **HOST** | {{hosting}} (VPS) | Encargado | UE |
| **SMTP** | Proveedor de correo **[pendiente; recomendado Brevo]** (`WOD_SMTP_HOST`) | Encargado | Brevo: UE. Otro proveedor: comprobar |
| **BACKUP** | Almacenamiento externo de copias (`WOD_BACKUP_COMMAND`) **[pendiente]** | Encargado | Recomendado UE y cifrado (`docs/despliegue/README.md`, apartado 7) |
| **STRIPE** | Stripe Payments Europe Ltd. | **[PENDIENTE ABOGADO]** (ver el anexo de encargo, A.3) | Irlanda, con transferencias a Stripe, Inc. (EE. UU.) bajo el Marco de Privacidad de Datos UE-EE. UU. y cláusulas tipo |
| **CENTRO** | Centro o profesional con el que se reserva | Responsable independiente | Donde esté el centro (puede ser fuera del EEE: **[PENDIENTE ABOGADO]**, ver más abajo) |

**Transferencias a centros fuera del EEE.** Los centros pueden estar en Egipto, Indonesia, México… Cuando un buceador reserva con ellos, sus datos viajan a ese país. **[PENDIENTE ABOGADO]**: base de la transferencia (art. 49.1.b RGPD, necesaria para ejecutar el contrato pedido por el interesado) y cómo informarlo.

---

## 1. Cuentas y autenticación

| | |
|---|---|
| Finalidad | Crear y gestionar la cuenta; iniciar sesión; verificar el email; recuperar la contraseña; verificación en dos pasos; cambio de email; eliminación de la cuenta; equipo del centro |
| Base jurídica | Ejecución del contrato (art. 6.1.b) |
| Interesados | Buceadores, personal de centros, profesionales freelance, administradores |
| Datos | `users`: `fullname`, `email`, `username`, `password_hash` (PBKDF2), `role`, `requested_role`, `center_id`, `created_at`, `last_login`, `preferred_language` (en `user_profiles`), `avatar_url`, redes sociales del profesional, `provider_bio`, `email_verified_at`, `totp_secret`, `totp_enabled`, `totp_recovery` (hash), `totp_last_step`, `inactive_warned_at`. `sessions` (hash del token, fechas, segundo factor). `email_verifications`, `password_resets`, `account_deletion_requests` (hash del token). `center_members`, `team_invites` (email, perfil) |
| Destinatarios | HOST, SMTP |
| Transferencias | No |
| Plazo | Mientras exista la cuenta. Cuentas de buceador **sin actividad 36 meses**: aviso por email y eliminación **30 días** después si no entra (`inactive_months`, `RETENTION_WARN_DAYS`). Sesiones: **8 horas** (`SESSION_TTL_SECONDS`), borradas cada 10 minutos. Enlaces de recuperación: 1 hora, borrados a los 2 días de caducar. Eliminación de cuenta: `delete_user_account()` anonimiza la cuenta y borra ficha, documentos, Log Book, avisos y sesiones |
| Seguridad | PBKDF2-SHA256 600 000 iteraciones; sesiones con hash, HttpOnly, SameSite=Lax; TOTP (obligatorio para administradores); límites de intentos; cierre de sesiones al cambiar contraseña, rol o email; CSRF |

Nota: las cuentas profesionales y de administrador no se borran por inactividad (`run_retention_jobs()` solo trata `role='recreational'`).

## 2. Ficha del buceador

| | |
|---|---|
| Finalidad | Que el buceador tenga a mano sus datos para reservar y, si quiere, los comparta con el centro |
| Base jurídica | Ejecución del contrato; los campos son opcionales |
| Interesados | Buceadores; **terceros**: la persona de contacto de emergencia |
| Datos | `user_profiles`: `phone`, `country`, `city`, `date_of_birth`, `certification_id`, `emergency_contact_name`, `emergency_contact_phone`, `equipment_required`, tallas (`suit_type`, `suit_size`, `boot_size`, `bcd_size`, `fin_size`, `mask_size`), `usual_weight_kg` (lastre habitual), preferencias de botella y ordenador, `equipment_notes`, `notes` |
| Destinatarios | HOST; CENTRO solo si se cumple `center_can_see_user()` (reserva online propia viva o `data_shares` activo) |
| Transferencias | Ver CENTRO |
| Plazo | Mientras exista la cuenta; se borra al eliminarla |
| Seguridad | Acceso del centro limitado por `center_can_see_user()`; el buceador ve y revoca a quién comparte («Centros que ven tu ficha», `data_shares.revoked_at`) |

**[PENDIENTE ABOGADO]**: contacto de emergencia (datos de un tercero, art. 14 RGPD) y si algún campo puede considerarse dato de salud (ver `preguntas-abogado.md`).

## 3. Reservas

| | |
|---|---|
| Finalidad | Intermediar la reserva entre el buceador y el centro: solicitud, aceptación, plazos, confirmación, cambios, cancelación, recordatorios, check-in, justificante |
| Base jurídica | Ejecución del contrato; obligación legal para la conservación (art. 6.1.c) |
| Interesados | Buceadores que reservan; participantes (solo número); clientes de centros (reservas manuales: ver «Como encargado») |
| Datos | `bookings`: fecha, hora, participantes, equipo, guía, nitrox, recogida, notas, estado, modo, plazos, motivo de rechazo, precio, señal, importes, política de cancelación copiada, versión de condiciones (`terms_version`), `contact_name`, `contact_email`, `contact_phone`, `public_token`. `experience_bookings`. `center_links` (check-in). `data_shares` |
| Destinatarios | HOST, SMTP, CENTRO, STRIPE (si se paga online) |
| Transferencias | Ver CENTRO y STRIPE |
| Plazo | **6 años** según la política de privacidad. En el código, las reservas **nunca se borran** automáticamente; al eliminar la cuenta se anonimiza el nombre y se borran `contact_phone`, `notes`, `equipment_notes` y `guide_notes`. **Hallazgo:** `contact_email` y `contact_name` de la reserva no se borran. **[PENDIENTE TITULAR]**: borrarlos y añadir la purga a los 6 años |
| Seguridad | Página pública de la reserva solo con sesión o token aleatorio largo (G4), nombre abreviado («Laura M.»); planning del centro sin nombre mientras el pago está en curso |

## 4. Pagos y justificantes

| | |
|---|---|
| Finalidad | Cobrar reservas en la cuenta de Stripe del centro (cargos directos), registrar señal, resto, devoluciones, disputas e incidencias; emitir el **justificante de reserva** (no es factura) |
| Base jurídica | Ejecución del contrato; obligación legal (conservación mercantil y fiscal) |
| Interesados | Buceadores que pagan; prestadores |
| Datos | `payment_orders`: importe, moneda, estado, `payment_intent_id`, `provider_payment_id`, `card_brand`, `card_last4`, `receipt_url`, `connected_account_id`, devoluciones, incidencias. `payment_refunds`. Datos del prestador en el justificante (`legal_name`, `tax_id`, `fiscal_address`). WORLDIVES **no ve el número de tarjeta** |
| Destinatarios | STRIPE, CENTRO, HOST |
| Transferencias | STRIPE |
| Plazo | 6 años (no hay borrado automático en el código) |
| Seguridad | Webhooks firmados con secretos separados (`STRIPE_WEBHOOK_SECRET`, `STRIPE_CONNECT_WEBHOOK_SECRET`) e idempotentes (`stripe_webhook_events`); un evento de una cuenta nunca toca otra; `/api/payments` no devuelve datos internos al buceador (G12) |

## 5. Documentos del buceador

| | |
|---|---|
| Finalidad | Guardar titulación, seguro de buceo, documento de identidad y otros documentos para mostrarlos al centro con el que reserva; avisar de su caducidad |
| Base jurídica | Ejecución del contrato (el buceador los sube voluntariamente) |
| Interesados | Buceadores |
| Datos | `user_documents`: tipo (`DOCUMENT_TYPES`: Titulación, Seguro, Documento de identidad, Documento adicional), título, archivo, nombre original, caducidad. `document_alerts`. **Sin certificados médicos** (se rechazan; G6) |
| Destinatarios | HOST; CENTRO autorizado por `center_can_see_user()`; administración (registrado) |
| Transferencias | Ver CENTRO |
| Plazo | Hasta que el buceador los borre o elimine la cuenta. Documentos **caducados: se borran 12 meses** después de la caducidad (`expired_docs_months`), con su archivo |
| Seguridad | Fuera de `/public`, tipo comprobado por contenido, máximo 10 MB y 30 por cuenta, permisos `0600`, `Cache-Control: private, no-store`, cada descarga y cada denegación en `audit_log`; el archivo se borra con el documento |

**[PENDIENTE ABOGADO]**: necesidad de admitir el documento de identidad (minimización).

## 6. Log Book

| | |
|---|---|
| Finalidad | Diario de inmersiones del buceador |
| Base jurídica | Ejecución del contrato |
| Interesados | Buceadores |
| Datos | `logbook_entries`: fecha, lugar, país, profundidad, duración, tipo, notas, reserva vinculada |
| Destinatarios | HOST |
| Transferencias | No |
| Plazo | Mientras exista la cuenta; se borra al eliminarla |
| Seguridad | Solo lo ve su dueño |

## 7. Reseñas y denuncias

| | |
|---|---|
| Finalidad | Publicar reseñas verificadas de centros, la respuesta única del centro, invitar a reseñar tras la inmersión; tramitar denuncias de contenido y moderar (Reglamento (UE) 2022/2065) |
| Base jurídica | Reseñas: ejecución del contrato; invitación a reseñar: interés legítimo **[PENDIENTE ABOGADO]**; denuncias: obligación legal (art. 6.1.c, DSA arts. 16 y 17) |
| Interesados | Autores de reseñas, personal del centro que responde, denunciantes (pueden no tener cuenta), personas afectadas por la decisión |
| Datos | `center_reviews`: valoración, título, texto, verificada, respuesta (`reply_body`, `reply_user_id`), moderación (`moderated_at`, `moderation_reason`). `content_reports`: motivo, URL, explicación, nombre y email del denunciante, `user_id`, `ip_hash`, estado, resolución, contenido y persona afectada |
| Destinatarios | Público (reseñas y respuestas); HOST; SMTP |
| Transferencias | No |
| Plazo | Reseñas: mientras estén publicadas; al eliminar la cuenta se quedan **sin el nombre del autor**. Denuncias: **sin plazo en el código** (`content_reports` no se purga). **[PENDIENTE TITULAR / ABOGADO]**: fijar plazo |
| Seguridad | Reseña solo con reserva pagada o confirmada; límite de 10 denuncias por IP y hora; IP seudonimizada; resolución solo por administradores |

## 8. Puntos

| | |
|---|---|
| Finalidad | Programa de fidelización sin valor monetario: ganar puntos, canjearlos por ventajas que paga cada centro, validar códigos |
| Base jurídica | Ejecución del contrato |
| Interesados | Buceadores; personal del centro que concede o valida |
| Datos | `points_ledger`, `reward_events`, `reward_redemptions` (código, estado, caducidad, quién y dónde se validó), `promotion_codes`, `promotion_redemptions`; histórico `wallet_transactions` (antiguo monedero, conservado sin tocar) |
| Destinatarios | HOST; el centro que valida ve nombre e inicial y el estado del código |
| Transferencias | No |
| Plazo | Mientras exista la cuenta. Al eliminarla se anulan los códigos emitidos; el libro queda ligado a la cuenta anonimizada |
| Seguridad | Concesión limitada por cliente y mes y por centro y mes; códigos de un solo uso; validación registrada |

## 9. Avisos y correos de servicio

| | |
|---|---|
| Finalidad | Correos ligados al servicio: verificación, recuperación, reservas (confirmación, 48 h y 24 h antes, cambios, cancelación, devoluciones), avisos del centro sobre una reserva, caducidad de documentos, cambios legales, plan y seguro del centro, agenda diaria del centro, estadísticas mensuales |
| Base jurídica | Ejecución del contrato; cambios legales: obligación legal |
| Interesados | Usuarios, clientes de centros, centros |
| Datos | `email_outbox`: plantilla, idioma, destinatario, asunto, **cuerpo completo** (HTML y texto), estado, errores. `messages`: avisos del centro, contacto del centro |
| Destinatarios | SMTP, HOST |
| Transferencias | Según el proveedor SMTP |
| Plazo | Cola de correos: **120 días** (borrado diario). Avisos de los centros: **24 meses** (`notices_months`) |
| Seguridad | Sin proveedor configurado, en producción los correos esperan en la cola (no se escriben en disco) |

## 10. Comunicaciones comerciales

| | |
|---|---|
| Finalidad | Enviar novedades y ofertas de WORLDIVES |
| Base jurídica | Consentimiento (art. 6.1.a RGPD; art. 21 LSSI) |
| Interesados | Usuarios registrados con el email verificado que han marcado la casilla |
| Datos | `users.marketing_consent`, `marketing_consent_at`, `marketing_token`; `consent_log` (alta y baja con fecha e `ip_hash`) |
| Destinatarios | SMTP, HOST |
| Transferencias | Según el proveedor SMTP |
| Plazo | Hasta la baja; `consent_log` como prueba: **[PENDIENTE ABOGADO]** (la privacidad dice «hasta 5 años después»; el código no lo borra) |
| Seguridad | Solo con consentimiento y email verificado; nunca a clientes importados; baja en un clic con `List-Unsubscribe` y `List-Unsubscribe-Post` |

## 11. Estadísticas agregadas de centros

| | |
|---|---|
| Finalidad | Mostrar al centro visitas a su ficha, clics en «Reservar» y solicitudes; comparación anónima con la zona (mínimo 3 centros más); email mensual |
| Base jurídica | Interés legítimo / ejecución del contrato con el centro |
| Interesados | Visitantes (solo para no contar dos veces la misma visita) |
| Datos | `provider_stats_daily`: contadores por día, **sin datos personales**. Para deduplicar se usa en memoria la IP seudonimizada (`ip_hash`) durante el día (`_STAT_SEEN`), que no se guarda en la base |
| Destinatarios | El centro (solo cifras) |
| Transferencias | No |
| Plazo | Contadores sin plazo (no son datos personales); la memoria se vacía al reiniciar o al superar 200 000 entradas |
| Seguridad | Agregación |

## 12. Solicitudes de información

| | |
|---|---|
| Finalidad | Hacer llegar al centro la consulta de un visitante cuando no hay reserva online (o en cualquier ficha) |
| Base jurídica | Consentimiento del interesado para enviar sus datos al centro (casilla «Acepta que enviemos tus datos al centro para que te conteste») **[PENDIENTE ABOGADO]**: o responsable que comunica, o encargado del centro (ver el anexo, A.1) |
| Interesados | Visitantes y buceadores |
| Datos | `info_requests`: nombre, email, teléfono, mensaje, fecha deseada, participantes, idioma, `ip_hash`, estado |
| Destinatarios | CENTRO (email `info_request` y panel), SMTP, HOST |
| Transferencias | Ver CENTRO |
| Plazo | **Sin plazo en el código.** **[PENDIENTE TITULAR]**: propuesta, 24 meses como los avisos |
| Seguridad | Límite por IP; solo el centro destinatario ve la solicitud |

## 13. Verificación de centros, datos fiscales y DAC7

| | |
|---|---|
| Finalidad | Comprobar que el centro o profesional es quien dice ser; recoger datos fiscales y del seguro; preparar el informe DAC7 |
| Base jurídica | Interés legítimo (verificación); obligación legal (Directiva (UE) 2021/514 y normativa española, **[PENDIENTE GESTORÍA/ABOGADO]** si WORLDIVES está obligada); ejecución del contrato |
| Interesados | Titulares de centros, profesionales freelance (personas físicas), solicitantes |
| Datos | `center_claims`: nombre del centro, teléfono, ciudad, web, nota, email, método y nota de verificación. En `centers` y `users`: `entity_type`, `legal_name`, `tax_id`, `tax_id_country`, `registration_number`, **`birth_date`** (autónomos), `fiscal_address`, cuenta de cobro (Stripe), declaraciones de licencias y de personal titulado, aseguradora, póliza, caducidad y **certificado del seguro** (privado). Informe `dac7_report()` |
| Destinatarios | HOST; Agencia Tributaria si procede (modelo 238) |
| Transferencias | No |
| Plazo | Mientras dure la relación y **[PENDIENTE GESTORÍA]**: plazo de conservación DAC7 (10 años según la Directiva) |
| Seguridad | Aprobación solo por administradores con método y nota; certificado del seguro solo visible para la administración; exportación DAC7 registrada (`dac7_exported`) |

## 14. Planes y cuota anual

| | |
|---|---|
| Finalidad | Gestionar el plan del centro, la prueba gratuita, la cuota anual y sus avisos |
| Base jurídica | Ejecución del contrato; obligación legal (contabilidad) |
| Interesados | Titulares de centros y profesionales |
| Datos | `plans`, `plan_payments` (importe, método, estado, sesión de Stripe, periodo, nota), `plan_exceptions`, columnas `plan_*` |
| Destinatarios | STRIPE (cuenta de WORLDIVES), HOST, SMTP |
| Transferencias | STRIPE |
| Plazo | 6 años (mercantil) **[PENDIENTE GESTORÍA]** |
| Seguridad | Webhook idempotente `kind=plan_fee` |

## 15. Seguridad y registros

| | |
|---|---|
| Finalidad | Seguridad de la web, prevención del fraude, investigación de incidentes, trazabilidad de acciones de administración y de los equipos de los centros |
| Base jurídica | Interés legítimo (art. 6.1.f); aceptaciones legales: obligación legal / prueba |
| Interesados | Todas las personas usuarias y visitantes |
| Datos | `logs/access.log`: fecha, **IP truncada** (/24 IPv4, /48 IPv6), método y ruta **sin cadena de consulta**, estado. `audit_log`: usuario, acción, entidad, detalles (algunos con `ip_hash`), `center_id`. `legal_acceptances` (documento, versión, fecha, `ip_hash`). Contadores de intentos en memoria |
| Destinatarios | HOST |
| Transferencias | No |
| Plazo | Registro de accesos: **14 días** (`WOD_LOG_RETENTION_DAYS`). Registro de actividad: **12 meses**, conservando siempre las **últimas 300 entradas** (`audit_months`, `audit_keep`). Aceptaciones: sin borrado en el código (la privacidad dice «hasta 5 años después») |
| Seguridad | `WOD_LOG_IP=truncated` por defecto; IP real solo desde proxies de confianza |

## 16. Copias de seguridad

| | |
|---|---|
| Finalidad | Recuperar la base y los archivos ante fallos o incidentes |
| Base jurídica | Interés legítimo; obligación de seguridad (art. 32 RGPD) |
| Interesados | Todos los de la base y los documentos |
| Datos | Copia completa de la base (`worldives-AAAAmmdd-HHMM.sqlite3.gz`) y de las carpetas de fotos y documentos privados (`archivos-….tar.gz`) |
| Destinatarios | HOST, BACKUP |
| Transferencias | Según BACKUP |
| Plazo | Rotación: **48 copias horarias, 30 diarias y 12 mensuales** (`WOD_BACKUP_KEEP_HOURLY/_DAILY/_MONTHLY`). Un dato borrado puede seguir en las copias hasta **12 meses**. Copias previas a migraciones (`backup_database()`): **sin rotación** **[PENDIENTE TITULAR]** |
| Seguridad | Permisos `0600`; comprobación `quick_check` de cada copia; aviso si falla la copia o la copia externa. **No están cifradas en origen** (ver el anexo, A.4) |

## 17. Mapas y búsqueda de localidades

| | |
|---|---|
| Finalidad | Mostrar mapas y buscar una localidad para el Top 10 |
| Base jurídica | Interés legítimo / ejecución del contrato |
| Interesados | Visitantes |
| Datos | Mapa base: archivo PMTiles propio (`/tiles/worldives.pmtiles`), sin terceros. Satélite Esri: **proxy** en el servidor; Esri no recibe la IP del visitante; contador mensual agregado (`map_tile_usage`) y límite por IP en memoria. Búsqueda: `/api/geocode` → `geocode_search()` envía **solo el texto** a Nominatim (`WOD_GEOCODER_URL`) desde el servidor, con caché de 1 día. «Usar mi ubicación»: coordenadas usadas solo para calcular, sin guardarlas. GEBCO: el navegador pide las teselas directamente (recibe la IP) solo si el visitante elige esa capa |
| Destinatarios | Esri y Nominatim (sin datos personales); GEBCO (IP, si se elige la capa) |
| Transferencias | Esri (EE. UU.) y Nominatim/OSMF (Reino Unido): sin datos personales. GEBCO: **[PENDIENTE ABOGADO]** |
| Plazo | No se guarda nada personal |
| Seguridad | Clave de Esri solo en el servidor (`ARCGIS_API_KEY`); CSP |

**[PENDIENTE ABOGADO]**: términos de ArcGIS Location Platform para el proxy (`docs/mapas.md`).

---

## Como encargado del tratamiento (art. 30.2 RGPD)

| | |
|---|---|
| Responsables | Cada centro o profesional con cuenta en WORLDIVES |
| Categorías de tratamiento | Fichas de cliente propias del centro (importación, reservas manuales y por API), planning y agenda, avisos y correos por cuenta del centro, cobros en mostrador, exportaciones, equipo; **[PENDIENTE ABOGADO]** solicitudes de información |
| Subencargados | HOST, SMTP, BACKUP |
| Transferencias | No (salvo el proveedor SMTP o de copias que se elija) |
| Seguridad | Las del anexo de encargo, cláusula 8 |

Detalle en `docs/legal/anexo-encargado-tratamiento.md`.

---

## Pendientes

| Tipo | Punto |
|---|---|
| TITULAR | Borrar `contact_email` y `contact_name` de las reservas al eliminar la cuenta |
| TITULAR | Purga de reservas y pagos pasados 6 años (hoy no existe) |
| TITULAR | Plazo para `info_requests`, `content_reports`, fichas de cliente del centro, `consent_log` y `legal_acceptances` |
| TITULAR | Rotación de las copias previas a migraciones |
| TITULAR | Cifrado de las copias |
| ABOGADO | DPO, transferencias a centros fuera del EEE, base de la invitación a reseñar, contacto de emergencia, documento de identidad, GEBCO, Esri, papel en `info_requests`, papel de Stripe |
| GESTORÍA | Obligación DAC7 y plazos de conservación fiscales |
