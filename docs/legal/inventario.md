# Inventario: diagnóstico de la v50.29 comprobado en el código

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

Este documento parte de la «Parte 1 — Diagnóstico» del encargo (auditoría de la v50.29). Cada punto se ha comprobado en el código actual (`app/server.py`, `app/wod/*.py`, `public/js/world-dives-v8.js`, `tests/`). Los números de línea son de la v50.38 y cambiarán con nuevas versiones: sirven de orientación, el nombre de la función o la ruta es lo que cuenta.

**Estados**

- **Corregido**: era un fallo y ya no existe.
- **Completado**: existía a medias y se ha terminado.
- **Ya estaba**: existía y funciona como decía el diagnóstico.
- **Parcial**: hecho, pero con un hueco que se indica.
- **Pendiente**: no hecho, o depende de una decisión.
- **No encontrado**: no aparece en el código.

Las pruebas automáticas se ejecutan con `python3 -m unittest discover -s tests -p 'test_*.py'`. Trabajan siempre sobre una copia del catálogo de demostración (`data/demo/catalogo-demo.sqlite3`). La tabla de estado por fases está en `docs/entrega/estado.md`.

---

## 1. Fallos graves G1–G12

| # | Estado | Versión | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| **G1** Cualquier centro descargaba cualquier documento | Corregido | v50.31 | Ruta GET `/api/documents/file/<id>` (`app/server.py` ≈L7826). Acceso: el dueño; un centro solo si `center_can_see_user()` (reserva online propia del buceador no cancelada, o permiso en `data_shares`); el admin. Cada descarga y cada intento denegado van a `audit_log` (`document_downloaded`, `document_access_denied`). | `test_phase1_security.py`: `test_g1_documents_access`, `test_g1_real_file_type_and_size` |
| **G2** Toma de control de centros al registrarse | Corregido | v50.31 (v50.36 quita además la sugerencia por teléfono) | POST `/api/auth/register` (≈L8116): la cuenta nace siempre `recreational`, con `requested_role` y una fila en `center_claims`. El centro se crea oculto (`active=0`, `verification_status='pending_provider'`). Pedir `admin` se rechaza. Aprobación en `/api/admin/center-claims/review` (≈L9821) con método obligatorio (`VERIFICATION_METHODS`) y nota. | `test_g2_register_never_grants_center_role`, `test_g2_admin_role_cannot_be_requested`, `test_g2_freelance_needs_approval` |
| **G3** XSS almacenado en recorridos virtuales | Corregido | v50.31 | `clean_virtual_payload()` llama a `wsec.clean_embed_url()`: solo `https://` en los dominios de `WOD_EMBED_DOMAINS`. CSP en todas las respuestas (`wsec.content_security_policy()`, `app/wod/security.py`). El vídeo se carga solo tras pulsar «Cargar vídeo». | `test_g3_virtual_urls`, `test_csp_and_headers_everywhere`, `test_units.SecurityUnits.test_embed_rules` |
| **G4** Reservas públicas por número | Corregido | v50.31 | GET `/api/public/bookings/<id>?t=<token>` (≈L7703): hace falta la sesión del dueño o del centro, o `bookings.public_token`. No devuelve `user_id` y el nombre sale recortado (`short_name`). | `test_g4_public_booking_needs_token` |
| **G5** El centro veía perfiles ajenos | Corregido | v50.31 | `find_or_create_customer()` nunca enlaza por email: crea un cliente propio del centro (`users.guest_center_id`, `password_hash='!'`). El acceso al perfil pasa por `center_can_see_user()` y `provider_can_see_user()`. El buceador revoca el permiso en `/api/account/shares/revoke`. | `test_g5_manual_booking_never_links_registered_account`, `test_g5_checkin_requires_consent` |
| **G6** Certificado médico como documento | Corregido | v50.31 | `DOCUMENT_TYPES` ya no tiene tipo médico. `clean_document_type()` rechaza las palabras de `MEDICAL_WORDS`. La migración `migrate_v50_31` borraba los existentes y avisaba (no había ninguno). | `test_g6_no_medical_certificates` |
| **G7** Cuerpos de petición de 256 MB | Corregido | v50.31 | `MAX_BODY = wcfg.MAX_JSON_BYTES` (1 MB), `MAX_UPLOAD` (15 MB), `MAX_DOCUMENT_BYTES` (10 MB) y `MAX_WEBHOOK_BYTES` en `app/wod/config.py`. `body_length()` responde 413 antes de leer el cuerpo. | `test_g7_body_limits` |
| **G8** Documentos en caché pública y archivos huérfanos | Corregido | v50.31 | `send_private_file()` envía `Cache-Control: private, no-store, max-age=0` y `Content-Disposition`. `delete_document_file()` borra el archivo al borrar el documento (`/api/account/documents/delete`), al borrar la cuenta (`delete_user_account`) y en la tarea de conservación. | Cubierto por `test_g1_documents_access` (cabeceras y borrado) |
| **G9** El primer usuario era administrador | Corregido | v50.31 | `setup_allowed()` exige `WOD_ALLOW_SETUP=1`. El primer admin se crea con `python app/server.py --create-admin`. En producción, `check_production_settings()` no arranca con `WOD_ALLOW_SETUP=1`. | `test_g9_setup_disabled` (las demás pruebas crean el admin con el CLI) |
| **G10** CSRF sin `Origin` ni `Referer` | Corregido | v50.31 | `enforce_same_origin()` (≈L6678) rechaza un POST sin `Origin`/`Referer`, salvo `CSRF_EXEMPT` (webhooks de Stripe e integración). En producción `WOD_PUBLIC_URL` es obligatoria; en desarrollo se sigue usando la cabecera `Host`. | `test_g10_csrf` |
| **G11** Mensajes a cualquiera | Corregido | v50.31 | POST `/api/messages` (≈L8604): solo centros y freelance, siempre con `booking_id` o `experience_booking_id` propios (`booking_notice_recipient`), con límite por hora (`NOTICE_LIMIT`). No se puede responder. | `test_g11_no_free_messaging` |
| **G12** `/api/payments` devolvía datos internos | Corregido | v50.31 | GET `/api/payments` (≈L8551) elige los campos uno a uno: sin `platform_fee`, `connected_account_id` ni `checkout_url`. | `test_g12_payments_fields` |

**Observaciones**

- **G1, equipo del centro.** Las personas del equipo (recepción e instructor, tabla `center_members`) tienen `users.role='center'`. Por tanto pueden abrir los documentos de un cliente con las mismas reglas que el propietario. `team_gate()` solo limita las escrituras y algunas lecturas del propietario. **[PENDIENTE TITULAR]**: decidir si el instructor (solo lectura) debe ver documentos.
- **G2, texto desfasado.** Desde la v50.36, `suggested_center_id` siempre se guarda vacío. Aun así, la pantalla de *Administración → Verificaciones* (`adminCenterClaims()` en el JS) sigue diciendo «Si el teléfono coincide con un centro existente, solo aparece como sugerencia». Es un texto antiguo, sin efecto en el funcionamiento.
- **Permisos entre roles.** `test_cross_role_permissions` (cada rol intenta leer datos de otro) y `test_bad_data_everywhere` (datos erróneos → 4xx, nunca 500) cubren el conjunto.

---

## 2. Choques con las decisiones del titular (1.3)

| Punto | Estado | Versión | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Comisión del 10 % | Corregido | v50.34 | En el código ya no aparecen `WOD_PLATFORM_FEE_PERCENT` ni `application_fee_amount`. La columna `payment_orders.platform_fee` se conserva solo como historial. El informe DAC7 pone `comisiones = 0`. El README dice que no hay comisión. | `test_direct_charge_without_commission`, `test_no_commission_in_legal_texts_and_settings`, `test_centre_kpis_are_income_by_currency` |
| Cargos de destino (`transfer_data`) | Corregido | v50.34 | `create_stripe_checkout()` crea el Checkout en la cuenta conectada (`stripe_account=account_id`, ≈L6178) y `stripe_kw()` se usa en todas las llamadas. Las cuentas se crean con propiedades de controlador (`stripe_controller()`): comisiones a cargo de la cuenta (`WOD_STRIPE_FEES_PAYER=account`), pérdidas a cargo de Stripe (`WOD_STRIPE_LOSSES=stripe`) y panel completo (`WOD_STRIPE_DASHBOARD=full`). | `test_every_stripe_call_carries_the_account`, `test_onboarding_uses_controller_properties`, `test_connect_webhook_confirms_and_is_idempotent` |
| Monedero en euros | Corregido | v50.35 | Puntos en el libro `points_ledger` (`points_add`, `points_balance`). Las ventajas usan `reward_offers.cost_points`. `/api/provider/wallet-grant` responde 410. `/api/provider/points-grant` tiene un límite por cliente y mes (`WOD_POINTS_GRANT_MAX_PER_CLIENT_MONTH`, 100) y por centro (3000). Los códigos `WOD-XXXX` se validan en `/api/center/redemptions/validate` y caducan a los 180 días (`POINTS_CODE_DAYS`). Las tablas `wallet_transactions` y las columnas `cost_wallet` quedan solo como historial. Las ofertas de ejemplo en euros ya no están. | `WalletMigration.test_wallet_becomes_points`, `test_grants_with_monthly_limit`, `test_exchange_and_validation_by_the_centre`, `test_no_money_features`, `test_cancel_and_expiry_give_points_back` |
| Justificante sin prestador | Corregido | v50.34 | `booking_pdf()` (≈L6398, motor `app/wod/pdf.py`) identifica al prestador con `legal_name`, `tax_id` y `fiscal_address` de `centers` o de `users` (freelance) y dice «Este documento no es una factura». | `test_voucher_names_the_provider_and_is_not_an_invoice` |
| «Patrocinado» editable | Corregido | v50.34 | Constante `SPONSORED_LABEL='Patrocinado'` (≈L4017). Cada patrocinio se registra en la tabla `sponsorships` (`/api/admin/site-promos`). **[PENDIENTE TITULAR]**: el encargo habla de «Destacado»; la web usa «Patrocinado». | `test_sponsored_label_is_fixed_and_sponsor_registered` |

---

## 3. Riesgo legal del catálogo (1.4)

| Punto | Estado | Versión | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Origen PADI/SSI de centros y puntos | Completado (centros) · Pendiente (puntos) | v50.36–v50.38 | La producción empieza limpia: `scripts/crear_semilla.py` no copia ningún centro. En la demo, `scripts/herramientas/demo_centros_ficticios.py` sustituye los 28 centros por centros ficticios. Los 215 puntos «PADI / WORLDIVES curated seed» siguen en el catálogo, con descripciones reescritas (`app/wod/pointtext.py`, tabla `dive_point_texts`). **[PENDIENTE ABOGADO]**: si la lista de nombres y coordenadas procede de una base protegida (derecho *sui generis*). Ver `docs/legal/catalogo-origen.md`. | `Schema.test_production_database_has_no_personal_data`, `test_point_descriptions_in_10_languages`, `DemoMode.test_demo_mode` |
| Se presentaban como catálogo propio ocultando el origen | Completado | v50.36 | `point_row()` y `center_row()` siguen quitando `source_name` y `source_url` de la API pública (≈L3064, L3074). En producción no hay centros importados y las descripciones son propias. La página `#/legal/creditos` da las fuentes de los mapas. | `test_point_descriptions_in_10_languages` |
| Portada «Centros que ya reservan con nosotros» | Corregido | v50.36 | La banda se llama ahora «Centros asociados» (JS ≈L731). `_build_promos()` (≈L4035) solo incluye centros con `verification_status='verified'`, `logo_consent=1` y logo. El consentimiento se da en el panel del centro (`logo_consent`, `logo_consent_at`). La banda tiene un mínimo de centros configurable (6 por defecto). | `test_associated_centres_band`, `test_logo_consent_from_the_centre_panel`, `test_only_verified_centres_are_public` |
| Fichas no gestionadas parecían reservables | Parcial | v50.37 | Si el centro no tiene «reservas online» en su plan (`online_booking=false`, ≈L7592), el botón se convierte en «Solicitar información» (JS ≈L437). Hueco: un centro **con** plan de reservas pero **sin** servicios publicados sigue mostrando «Reservar con {centro}» en la columna lateral (JS ≈L419). La página dice entonces «Este centro todavía no ha publicado actividades». | `test_expired_plan_becomes_free_listing` |

---

## 4. Lo que ya existía (1.5)

| Punto | Estado | Dónde está en el código | Prueba automática |
|---|---|---|---|
| Sesiones con hash, 8 h, cookie HttpOnly y SameSite=Lax; se cierran al cambiar la contraseña | Ya estaba · Completado en v50.31 (también se cierran al cambiar de rol) | Tabla `sessions` (`token_hash`). `SESSION_TTL_SECONDS=28800`. La cookie se pone en `login_user()` (≈L10187) con `Secure` si la URL es https. Al cambiar la contraseña se borran las demás sesiones (≈L9375). | `test_13_role_change_closes_sessions`. Para el cierre al cambiar la contraseña no hay prueba específica. |
| SQL parametrizado | Ya estaba | Consultas con `?`. Los `f-string` en SQL solo componen nombres de tabla internos (`provider_table()`) o marcadores, nunca datos del usuario. | `test_bad_data_everywhere` (indirecta) |
| Concurrencia, tiempo de espera y límite de intentos de login | Ya estaba · Completado en v50.31 | `WOD_MAX_CONCURRENT` (64, ≈L10216), `WOD_SOCKET_TIMEOUT` (30 s, ≈L6592). `LOGIN_LIMIT` de 8 intentos en 15 min por cuenta e IP, más `LOGIN_IP_LIMIT` por IP. `wsec.RateLimiter` tiene un tamaño máximo. | `test_13_login_rate_limit`, `test_units.SecurityUnits.test_rate_limiter_bounded` |
| Cabeceras de seguridad | Ya estaba · Completado | `nosniff`, `X-Frame-Options: DENY`, `Referrer-Policy`, `Permissions-Policy`, HSTS si la URL es https, y CSP (≈L6658–6672). | `test_csp_and_headers_everywhere` |
| Stripe Connect | Completado en v50.34 | Rutas `/api/payments/connect/*` (alta, enlace, sincronización y panel). Dos webhooks con firma e idempotencia (tabla `stripe_webhook_events`): `/api/payments/webhook` (plataforma) y `/api/payments/webhook/connect`. El pago se confirma al volver (`/api/payments/session/`). Estado `review` si el importe no cuadra. `sweep_payment_orders()` se ejecuta cada 300 s. | `test_connect_webhook_confirms_and_is_idempotent`, `test_connect_event_of_another_account_is_ignored`, `test_webhook_secrets_are_separate`, `test_payment_mode_return_page_confirms` |
| «Pagas en el centro» y cobro en mostrador | Ya estaba | Panel del centro, reservas sin cobro online. | `test_deposit_then_rest_at_the_desk`, `test_request_accept_without_online_payments` |
| Reseñas solo con reserva pagada o confirmada | Ya estaba · Completado en v50.36 | `/api/centers/<id>` calcula `can_review` (≈L7572). La reseña lleva `center_reviews.verified`. El centro da una respuesta (`reply_body`) y se puede moderar (`moderation_reason`). | `ReviewsAndReports.test_single_editable_reply`, `test_admin_moderation_needs_reason` |
| Promociones con QR | Ya estaba | Tablas `promotions`, `promotion_codes` y `promotion_redemptions`. Ruta `/api/promo/<code>/qr.svg`. | `test_16_promo_qr_svg` |
| Puntos automáticos | Completado en v50.35 | `sync_user_rewards()` y `ensure_reward_event()` (≈L4129) escriben en `points_ledger`. | `test_points_are_earned_by_diving` |
| Organizador visible en Experiencias | Ya estaba · Completado en v50.36 | `enrich_experiences()`. Bloque legal de la reserva de experiencias (JS ≈L1130). | `test_experience_shows_provider_and_policy` |
| Panel del centro | Ya estaba · Completado en v50.37 | Rutas `/api/center/*` y `/api/provider/*`. | `CentreTools.*`, `TeamAndSwitches.*` |
| Fuente Inter alojada, sin analítica | Ya estaba | `public/fuentes/inter-*`. En `public/index.html` no hay scripts de terceros. | `test_csp_and_headers_everywhere` (CSP `script-src 'self'`) |
| localStorage mínimo; el Top 10 no guarda coordenadas | **Parcial** | Las claves son `wod-language`, `wd_cookie_notice`, `wd-i18n-debug` y `wd_top10`. Con GPS se guarda solo `{geo:true}`. Pero si el visitante elige un lugar en el mapa o lo busca, se guardan su latitud, longitud y nombre (`remember({pick:{lat,lon,label}})`, JS ≈L1092–1098). Se queda en el navegador y no se envía al servidor. | Sin prueba |
| El service worker no guarda la API en caché | Ya estaba | `public/sw.js` deja fuera `/api/`, `/tiles/` y las peticiones con `Range`. | Sin prueba automática |
| Accesibilidad parcial | Completado en v50.36 | `alt`, `lang` dinámico, `:focus-visible`, etiquetas enlazadas, página `#/legal/accesibilidad`. | Navegador (`tests/e2e_*.py`) |
| Crédito de las imágenes de portada | Ya estaba · Completado | `site_media.credit` y `origin`, `image_origins`, `images_report()`. | `test_image_origins_report` |

---

## 5. Lo que faltaba (1.6)

| Punto | Estado | Versión | Dónde está en el código | Prueba automática |
|---|---|---|---|---|
| Sistema de email | Completado | v50.30 + v50.35 | Cola `email_outbox` (`queue_email`, `deliver_outbox_once`, `email_scheduler`) y SMTP genérico (`smtp_config`). Sin `WOD_SMTP_HOST` en desarrollo escribe archivos `.eml` (`spool_outbox_to_files`). | `test_development_writes_emails_to_files`, `test_reminders_48h_and_24h`, `test_document_expiry_alerts`, `test_booking_change_by_the_provider` |
| 2FA y recuperación de contraseña | Completado | v50.30 + v50.35 | TOTP en `app/wod/totp.py` y `/api/account/totp/*`, obligatorio para admin (`admin_totp_required`). Recuperación con `/api/auth/forgot` y `/api/auth/reset` (tabla `password_resets`, enlace de 1 h). | `TwoStep.test_optional_totp_for_a_diver`, `AdminNeedsTotp.*`. La recuperación de contraseña no tiene prueba específica. |
| Textos legales | Completado | v50.36 | `app/legal/es/*.md` y `app/legal/en/*.md` (14 documentos), tabla `legal_documents` con versiones, `legal_publish()` y `/api/legal/doc`. | `LegalDocuments.test_routes_aliases_and_official_languages`, `test_translation_shows_spanish_prevails` |
| Aceptaciones | Completado | v50.30 + v50.36 | Casillas `accept_terms` y `accept_pro_terms` al registrarse. `record_acceptances()` guarda en `legal_acceptances` (con `ip_hash`). Se vuelve a pedir la aceptación con `legal_pending_for()` y `/api/legal/accept`. | `test_new_version_must_be_accepted_again`, `test_centres_get_15_days_notice` |
| Derechos (borrar, descargar, cambiar el email) | Completado | v50.30 + v50.36 | `/api/account/export?format=zip` (`export_user_zip`). `/api/account/delete` y `/api/account/delete/confirm` (enlace por email, 24 h, tabla `account_deletion_requests`). `/api/account/email` con verificación (`email_verifications`). | `DataRights.test_zip_export_with_documents`, `test_deletion_is_confirmed_by_email`, `test_deletion_cascades`. El cambio de email no tiene prueba. |
| Plazos de conservación | Completado | v50.36 | `run_retention_jobs()` (≈L10278) con `RETENTION_DEFAULTS`: cuentas inactivas 36 meses (aviso y borrado 30 días después), documentos caducados 12 meses, avisos 24 meses, registro de actividad 12 meses (se guardan las últimas 300 entradas). Se configura en *Administración → Legal* (`/api/admin/retention`). | `test_retention_job` |
| Denuncias, cola de moderación y respuesta del centro | Completado | v50.36 | Tabla `content_reports`. Rutas `/api/reports` y `/api/admin/reports/resolve` (avisa a quien denuncia y al afectado). Respuesta del centro en `/api/reviews/<id>/reply`. | `ReviewsAndReports.*` |
| Explicación del orden «Recomendados» | Parcial | v50.36 | Página `#/legal/clasificacion` (`app/legal/es/clasificacion.md`), enlazada desde los textos legales. **No hay enlace junto al selector de orden** del directorio (JS `CD_SORTS` ≈L491, `PT_SORTS` ≈L799). | `test_routes_aliases_and_official_languages` |
| Reserva: cancelación, desistimiento, condiciones e impuestos | Completado | v50.34 + v50.36 | Política por centro y servicio (`cancel_free_hours`, `cancel_refund_pct`) copiada en la reserva. Bloque legal en la reserva (JS ≈L1452) y en experiencias (≈L1130) con el art. 103.l TRLGDCU, «impuestos incluidos» y casilla de aceptación. | `test_policy_is_copied_into_the_booking`, `test_late_cancel_uses_percentage`, `test_experience_shows_provider_and_policy` |
| Pagos: señal | Completado | v50.34 | `provider_services.deposit_type` y `deposit_value`, `deposit_for()`, `bookings.deposit_amount` y `amount_due`. | `test_deposit_then_rest_at_the_desk` |
| Pagos: devoluciones por API | Completado | v50.34 | `refund_payment()` y `refund_booking()`. Ruta `/api/bookings/<id>/refund`, solo para el prestador. Tabla `payment_refunds`. | `test_partial_then_total_refund_by_centre`, `test_only_the_provider_refunds` |
| Pagos: un `charge.refunded` parcial cancelaba la reserva | Corregido | v50.34 | `handle_stripe_event()` → `sync_refunds_from_stripe()` registra el importe sin cancelar. | `test_refund_made_in_stripe_dashboard_is_recorded` |
| Experiencias: precio × participantes | Corregido | v50.34 | `start_experience_checkout()` (≈L6218): `price × participants`. | **Sin prueba automática** |
| Planes, cuota anual e interruptores | Completado | v50.37 | Tablas `plans`, `plan_exceptions` y `plan_payments`. `provider_plan()`, `require_feature()`, `FEATURE_SWITCHES` y `run_plan_jobs()`. | `Plans.*`, `test_feature_switches` |
| DAC7: datos fiscales, seguro, declaraciones | Completado | v50.37 | Columnas `FISCAL_FIELDS` en `centers` y `users`. Rutas `/api/provider/fiscal` y `/api/provider/insurance-doc`. `run_insurance_alerts()`. `dac7_report()` y `/api/admin/dac7?format=csv`. | `test_fiscal_data_and_insurance`, `test_dac7_report` |
| CSV, iCal e importación | Completado | v50.37 | `/api/center/export`, `/ical/<token>.ics` (`ical_feed`), `/api/center/import` (`import_clients`). | `test_exports_ical_widget`, `test_import_clients_with_preview` |
| Usuarios por empleado con roles; planning de todo el centro | Completado | v50.37 | `center_members.member_role` (owner, reception, instructor), `team_gate()`, `/api/center/team/*`, `team_invites`. | `test_roles_and_activity_log` |
| Registro de actividad del centro | Completado | v50.37 | `audit_log.center_id`, `/api/center/activity`. | `test_roles_and_activity_log` |
| «Solicitar información» | Completado | v50.37 | Tabla `info_requests`. Rutas `/api/info-requests` y `/api/center/info-requests`. | `test_expired_plan_becomes_free_listing` |
| Estadísticas de visitas | Completado | v50.37 | Tabla `provider_stats_daily`, `stat_bump()`, `/api/provider/stats`. | `test_statistics_are_aggregated` |
| Copias, integridad y alertas | Completado | v50.38 | `run_backup_jobs()` y `app/wod/backup.py`. `PRAGMA quick_check` diario. `ops_alert()` y `ErrorMonitor` (`app/wod/ops.py`). | `Backups.test_automatic_backup_verify_and_restore`, `test_backup_now_with_external_command`, `test_health_and_banner` |
| Esquema completo para una instalación limpia | Corregido | v50.38 | `BASE_SCHEMA` (`app/server.py` L68), aplicado en `bootstrap()`. | `Schema.test_clean_install_equals_migrated_database`, `test_server_starts_without_bundled_database` |
| `.gitignore` y la base `.sqlite3` | Corregido | v50.38 | `data/*.sqlite3` y `data/backups/` están excluidos. CI en `.github/workflows/security-test.yml`. | CI |
| `X-Forwarded-For` detrás del proxy | Corregido | v50.31 | `wsec.client_ip()` solo lo lee si el par TCP está en `WOD_TRUSTED_PROXIES`. | `test_units.SecurityUnits.test_trusted_proxy` |
| Mapas: teselas públicas de OSM | **Parcial** | v50.36 | El mapa público usa PMTiles propio (`map_config()`, `/tiles/…` con `Range`). En producción y sin archivo, `type: 'none'` (sin fondo). **Hueco:** el editor de centros de *Administración → Centros* (`editCenterForm()`, JS ≈L3804) carga siempre `tile.openstreetmap.org`, también en producción. Es poco tráfico, pero contradice la política de OSM y `docs/mapas.md`. | `test_pmtiles_served_with_range`, `test_satellite_proxy_counter_and_limit` |
| Mapas: atribuciones | Completado | v50.36 | `OSM_ATTRIBUTION`, `SAT_ATTRIBUTION` y `GEBCO_ATTRIBUTION`; página `#/legal/creditos`. | `test_pmtiles_served_with_range` (parcial) |
| Leaflet desde unpkg sin SRI | Corregido | v50.31 | Alojado en `public/lib/leaflet/`, junto con markercluster y protomaps-leaflet. | `test_csp_and_headers_everywhere` |
| Hosting: hace falta un VPS | Completado | v50.38 | `docs/despliegue/` (`Caddyfile`, `nginx.conf`, `worldives.service`, `worldives-pruebas.service` y `backup-externo.sh`), `docs/despliegue/README.md`. | `EnvFile.test_env_file_with_inline_comments` |

---

## 6. Discrepancias entre documentos y código

1. **Sugerencia por teléfono (G2).** `docs/entrega/estado.md` (Fase 1, punto 2) y el texto de *Administración → Verificaciones* hablan de una «sugerencia» por teléfono. Desde la v50.36 el registro guarda siempre `suggested_center_id` vacío. Hay que actualizar el texto. **Corregido en v50.38:** texto de Verificaciones y `estado.md` actualizados; al rechazar se envía un correo al solicitante.
2. **Teselas de OSM en producción.** `docs/mapas.md` dice que los mapas ya no usan los servidores públicos de OpenStreetMap. El editor de centros del admin sí los usa (`editCenterForm`). **Corregido en v50.38:** el editor usa `wdBaseLayer()`, el mismo mapa base que el resto.
3. **Top 10 y localStorage.** El diagnóstico decía que las coordenadas no se guardan. Las de la ubicación GPS no se guardan, pero las de un lugar elegido en el mapa o buscado sí (`wd_top10`). Conviene mencionarlo en la política de cookies (almacenamiento local).
4. **Certificado del seguro.** `docs/notas-de-version/v50.37.md` dice que el certificado «solo lo ve la administración». Existe la ruta `/api/admin/insurance-doc?type=center&id=N`, pero **ninguna pantalla de Administración la enlaza**, y tampoco hay pantalla con los datos fiscales de un centro concreto: solo el CSV de DAC7.
5. **Aviso de webhook de Connect.** En `production_warnings()`, el aviso de falta de `STRIPE_CONNECT_WEBHOOK_SECRET` está en un `elif` que depende de `ARCGIS_API_KEY`. Sin clave de ArcGIS, nunca sale. Es un fallo menor de lógica. **Corregido en v50.38:** el aviso ya no depende de la clave de ArcGIS.
6. **Número de imágenes sin licencia.** `docs/legal/catalogo-origen.md` habla de 24 imágenes y `docs/notas-de-version/v50.36.md` de 23. El informe real está en *Administración → Imágenes de la web* (`images_report`).
7. **Baja de cuentas profesionales.** `/api/account/delete` solo admite cuentas `recreational`: centros, freelance y admins «se dan de baja escribiéndonos». No hay herramienta de administración para borrarlas: el admin solo puede cambiar el rol (`/api/admin/users/role`), y después la persona puede borrar la cuenta ella misma.
8. **Pruebas que faltan.** No hay prueba automática de recuperación de contraseña, cambio de email, precio × participantes en experiencias ni cierre de sesiones al cambiar la contraseña. **Corregido en v50.38:** `tests/test_phase8_flows.py` cubre los cuatro casos.

---

## 7. Inventario del sistema

### 7.1 Tablas de datos por área

Esquema completo en la constante `BASE_SCHEMA` de `app/server.py`.

**Cuentas y seguridad**

| Tabla | Datos personales que guarda |
|---|---|
| `users` | Nombre completo, email, usuario, hash de contraseña, rol, último acceso, enlaces a redes y avatar. TOTP: secreto, códigos de recuperación y fecha de activación. Consentimiento comercial y token de baja. Versión y fecha de condiciones aceptadas. En freelance: datos fiscales (razón social, NIF, país, registro, **fecha de nacimiento**, dirección), seguro (aseguradora, póliza, caducidad, ruta del certificado), Stripe (`stripe_account_id`), plan y token iCal. En clientes creados por un centro: `guest_center_id` y `guest_email`. |
| `user_profiles` | Teléfono, país, ciudad, idioma, titulación, fecha de nacimiento (opcional), contacto de emergencia (opcional), tallas de equipo, lastre habitual (opcional) y notas. |
| `sessions` | Hash del token, usuario, fechas y si pasó el segundo factor. |
| `password_resets`, `email_verifications`, `account_deletion_requests` | Hash del token, usuario y email (en verificaciones) con fechas. |
| `consent_log`, `legal_acceptances` | Usuario, tipo de consentimiento o documento, versión, fecha y hash de la IP. |
| `audit_log` | Usuario que actúa, acción, entidad, detalles en JSON (puede incluir hash de IP o ids de otros usuarios), centro y fecha. |

**Buceador**

| Tabla | Datos personales que guarda |
|---|---|
| `user_documents` | Tipo (titulación, seguro, identidad, adicional), título, nombre original y ruta del archivo (fuera de `/public`), caducidad. |
| `document_alerts` | Avisos de caducidad enviados. |
| `logbook_entries` | Inmersiones: fecha, lugar, profundidad, duración y notas. |
| `points_ledger`, `reward_events`, `reward_redemptions`, `rewards`, `wallet_transactions` (historial) | Movimientos de puntos, logros y códigos de canje por usuario. |
| `data_shares`, `center_links` | Qué centros ven la ficha del buceador (check-in o permiso) y fechas. |
| `point_position_suggestions` | Correcciones de posición propuestas por el usuario. |

**Centros y profesionales**

| Tabla | Datos personales que guarda |
|---|---|
| `centers` | Datos públicos del centro (nombre, dirección, teléfono, email, web, redes, logo). Datos fiscales (razón social, NIF, registro, fecha de nacimiento si es persona física, dirección fiscal). Seguro y certificado. Stripe, plan, `logo_consent` y token iCal. |
| `center_claims` | Solicitud de alta: usuario, teléfono, ciudad, web, email, nota, método y nota de verificación, y quién la revisó. |
| `center_members`, `team_invites` | Equipo del centro con su rol, email de la invitación y hash del token. |
| `center_reviews` | Valoración, título, texto, respuesta del centro y moderación (autor = usuario). |
| `info_requests` | Nombre, email, teléfono, mensaje, fecha deseada, personas y hash de la IP. |
| `provider_stats_daily` | Solo contadores agregados (sin datos personales). |
| `center_integrations` | Hash de la clave API. |
| `promotions`, `promotion_codes`, `promotion_partners`, `promotion_redemptions`, `qr_codes` | Códigos asociados a un usuario y canjes. |
| `provider_services`, `service_slots`, `service_slot_points`, `service_templates`, `center_tariffs`, `center_extras`, `center_equipment`, `center_point_links`, `center_photos` | Catálogo del centro (sin datos personales, salvo el `provider_user_id`). |

**Reservas y pagos**

| Tabla | Datos personales que guarda |
|---|---|
| `bookings` | Usuario, centro o profesional, fecha, personas, equipo, notas, teléfono, email y nombre de contacto, notas internas del centro, importes, política de cancelación copiada, devoluciones y `public_token`. |
| `experience_bookings` | Usuario, experiencia, personas, notas, estado e importes. |
| `payment_orders` | Usuario, prestador, importes, estado, ids de Stripe, marca y últimos 4 dígitos de la tarjeta, URL del recibo, incidencias. Columnas históricas: `platform_fee`, `connected_account_id`. |
| `payment_refunds` | Devoluciones con motivo y nota. |
| `stripe_webhook_events` | Id y tipo de evento (sin datos personales). |
| `plan_payments` | Cuotas de los centros (importe, método, periodo y nota). |
| `messages` | Avisos ligados a reservas: remitente, destinatario, texto, teléfono y email de contacto del centro. |
| `email_outbox`, `email_digest_log` | Destinatario, asunto y cuerpo de cada correo, estado y errores. |

**Contenido, catálogo y web**

| Tabla | Datos personales que guarda |
|---|---|
| `dive_points`, `dive_point_texts`, `dive_point_photos`, `dive_types`, `dive_zones`, `countries`, `certifications` | Catálogo. `dive_point_photos.uploaded_by` identifica a quien sube la foto. |
| `travel_offers`, `travel_experiences`, `virtual_experiences` | Catálogo de experiencias, con el prestador. |
| `content_reports` | Nombre, email e IP (hash) de quien denuncia, usuario afectado y resolución. |
| `legal_documents` | Textos legales con sus versiones. |
| `site_settings` | Ajustes, incluidos los **datos del titular** (Administración → Legal), el banner y el estado de las copias. |
| `site_media`, `site_theme_media`, `site_themes`, `site_promos`, `sponsorships`, `image_origins` | Contenido de la web. `sponsorships.sponsor_contact` puede tener datos de una persona de contacto. |
| `plans`, `plan_exceptions`, `pro_invites`, `map_tile_usage`, `schema_migrations`, `booking_mode_migration` | Configuración y registros técnicos. |

**Archivos fuera de la base:** documentos privados y certificados de seguro en `storage/` (`document_file_path`), fotos subidas en `public/assets/uploads` (`PHOTOS`), copias en `WOD_BACKUP_DIR` (`db/` cada hora, `files/` cada día), correos `.eml` en `data/mail-outbox/` (solo en desarrollo) y registros diarios en `logs/` (IP truncada, sin *query string*).

### 7.2 Servicios externos

| Servicio | Para qué | Cómo se conecta | Datos que recibe | Configuración |
|---|---|---|---|---|
| **Stripe** (plataforma) | Cuota anual de los planes | Checkout en la cuenta de WORLDIVES (`/api/provider/plan/checkout`, metadato `kind=plan_fee`) y webhook `/api/payments/webhook` | Email e importe del centro o profesional | `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` |
| **Stripe Connect** | Cobros de las reservas, como cargos directos en la cuenta del centro o del freelance | `stripe_account=` en todas las llamadas. Webhook `/api/payments/webhook/connect`. Alta con `/api/payments/connect/onboard` | Datos de pago del buceador (los recoge Stripe), importe y referencia de la reserva | `STRIPE_CONNECT_WEBHOOK_SECRET`, `WOD_STRIPE_DASHBOARD`, `WOD_STRIPE_FEES_PAYER`, `WOD_STRIPE_LOSSES`, `WOD_STRIPE_CAPABILITIES` |
| **SMTP** (recomendado Brevo, pendiente de decisión) | Todos los correos | `smtp_config()` y `_smtp_open()` | Email, nombre y contenido del correo | `WOD_SMTP_*`, `WOD_MAIL_FROM*` |
| **Esri World Imagery** (ArcGIS Location Platform) | Capa satélite | Proxy del servidor `/api/tiles/satellite/{z}/{y}/{x}`. La clave no llega al navegador | Solo la IP del servidor | `ARCGIS_API_KEY`, límite mensual en *Administración → Mapas* (`maps_satellite_limit`, 1 900 000 por defecto) |
| **GEBCO** (`wms.gebco.net`) | Batimetría, solo si el visitante la elige | Directo desde el navegador | IP del visitante | — |
| **Nominatim** (OpenStreetMap) | Buscar lugares (Top 10, editores) | Por el servidor: `/api/geocode` → `geocode_search()`, con espera entre peticiones | El texto buscado; Nominatim ve la IP del servidor | `WOD_GEOCODER_URL` |
| **Protomaps (archivo PMTiles)** | Mapa base | Archivo propio servido en `/tiles/…` con `Range`, o URL https externa (CDN) | Nadie (si es local) o el CDN elegido | `WOD_PMTILES_URL`, `WOD_PMTILES_MAXZOOM`, `WOD_TILES_DIR` |
| **OpenStreetMap (teselas públicas)** | Solo en desarrollo sin PMTiles (`osm-dev`), y en el editor de centros del admin (ver discrepancia 2) | Directo desde el navegador | IP del visitante o del admin | — |
| **Proveedores de vídeo** (youtube-nocookie, Vimeo, Google Maps) | Recorridos virtuales, tras pulsar «Cargar vídeo» | iframe | IP del visitante | `WOD_EMBED_DOMAINS` |
| **Hostinger** (VPS KVM 2, v50.52) | Alojamiento de la web, la base de datos y los archivos | Es el servidor: Alemania (Frankfurt) o Francia, elegido al contratar (no se cambia sin reinstalar) | Todo lo que guarda la web | hPanel; `docs/despliegue/GUIA-VPS.md` |
| **Copia externa** (rclone; proveedor en la UE fuera de Hostinger: **Pendiente de decisión**) | Copias fuera del servidor | `WOD_BACKUP_COMMAND` (`scripts/copia_externa.sh`), https | La base completa y los archivos, **cifrados** con `WOD_BACKUP_KEY` antes de salir | Remoto `externo` de rclone (`GUIA-VPS.md`, paso 12) |
| **Better Stack** (registros, región de datos Europa, v50.52) | Registros fuera del servidor y alertas | Vector en el VPS, https con el token en `/etc/vector/betterstack.env` (`docs/despliegue/vector.yaml`) | Sucesos de seguridad e inicios de sesión fallidos (número de persona, huella de la IP, ruta) y el registro de accesos de Caddy (IP recortada, sin consulta). 30 días (plan Nano UE) | `docs/seguridad/registros.md` |
| **Better Stack Uptime** (monitor) | Disponibilidad | Pide `/api/health` cada 3 minutos (solo `ok` y versión) | Nada personal | Fuera del código (`GUIA-VPS.md`, paso 11) |
| **ClamAV** (firmas, `database.clamav.net`) | Antivirus de los documentos | `freshclam` descarga las firmas por https; los documentos **no salen** del servidor (clamd local) | Nada | `WOD_AV_COMMAND` |
| **Meta Graph API** (WhatsApp Cloud) | Avisos por WhatsApp de cada centro | Por el servidor, https a `graph.facebook.com`, sin seguir redirecciones (`wod/whatsapp.py`) | Teléfono del buceador (con su permiso) y el texto del aviso | `WHATSAPP_*` |
| **Firebase** (`oauth2.googleapis.com`, `fcm.googleapis.com`) | Avisos en el móvil | Por el servidor, https, sin seguir redirecciones (`wod/push.py`) | El identificador del móvil y el texto del aviso | `WOD_FCM_CREDENTIALS` |
| **Plataformas de vídeo** (oEmbed de YouTube, Vimeo, Dailymotion, TikTok) | Título y miniatura de un vídeo enlazado | Por el servidor, https (`wod/videos.py`, `wod/remoto.py`) | El enlace del vídeo | Lista `PLATFORMS` |
| **Página que indique quien enlaza un vídeo de otra plataforma** | Comprobar que es un vídeo y leer su título e imagen | Por el servidor, solo https y solo direcciones públicas, cada salto comprobado, tamaño y tiempo limitados (`wod/videos.inspect`, `wod/remoto.fetch`). **La dirección la da el usuario** (centros, freelance y administración) | El enlace | — |
| **Wikimedia Commons** (`commons.wikimedia.org`, `upload.wikimedia.org`) | Buscar e importar fotos de especies con licencia libre | https desde el servidor, solo esos dos dominios (`wod/vidamarina.py`) | El nombre de la especie buscada | — |

Todas las conexiones salientes del servidor van por https (puerto 443), salvo el correo (587 o 465 con TLS comprobado),
el DNS (53), la hora (123), DHCP (67) y los repositorios de Ubuntu por http (80, paquetes firmados). El cortafuegos del
VPS solo deja salir por esos puertos y entrar por 22 (desde IPs conocidas), 80 y 443
(`scripts/despliegue/cortafuegos.sh`, ASVS V13.2.5); el servicio de la web, además, no puede conectarse a la red interna
del proveedor (`IPAddressDeny` en `worldives.service`).

### 7.3 Roles

| Rol | Cómo se obtiene | Qué ve y qué hace | Dónde se comprueba |
|---|---|---|---|
| **Visitante** (sin sesión) | — | Catálogo, centros verificados, puntos, experiencias, textos legales, «Solicitar información» y denuncias. Justificante de reserva solo con el token. | Rutas públicas. `public_center_sql()` filtra los verificados. |
| **Buceador** (`recreational`) | Registro (`/api/auth/register`) | Reservas, pagos, Log Book, documentos, puntos y canjes, reseñas con reserva. Exporta y borra su cuenta. Permisos de datos a centros. TOTP opcional. | `require_user()` y filtros por `user_id`. |
| **Centro: propietario** (`role='center'`, `center_members.member_role='owner'`) | Aprobación de la administración (`center_claims` → review) | Todo el panel: reservas, clientes (con las reglas de G5), servicios, cobros y devoluciones, plan, datos fiscales, equipo, exportaciones e integración. | `require_role({'center'})`, `require_feature()`, `team_gate()`. |
| **Centro: recepción** (`member_role='reception'`) | Invitación del propietario (`/api/center/team/invite`) | Reservas, clientes, servicios y salidas. Sin cobros, plan, datos fiscales, equipo ni ajustes. | `team_gate()`, `OWNER_ONLY_PREFIXES`. |
| **Centro: instructor** (`member_role='instructor'`) | Invitación | Solo lectura (salvo `INSTRUCTOR_POST_OK`). Ver la observación de G1 sobre documentos. | `team_gate()`. |
| **Freelance** (`role='freelance'`) | Aprobación de la administración | Servicios y reservas propias sin centro, cobros con su propia cuenta Stripe, datos fiscales, plan y experiencias. Si tiene `center_id`, cuenta como ese centro. | `provider_ref()`, `provider_can_see_user()`. |
| **Administración** (`role='admin'`) | Solo `python app/server.py --create-admin`. TOTP obligatorio (en producción no se puede desactivar) | Aprobaciones, moderación, legal, planes, funciones, mapas, correos, operación, pagos (solo lectura e incidencias: no mueve dinero) y DAC7. Accede a documentos con registro en `audit_log`. | `require_role({'admin'})`, `admin_totp_required()`. |
