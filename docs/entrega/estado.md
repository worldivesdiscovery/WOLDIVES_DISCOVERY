# Tabla de estado del encargo (desde v50.31)

Estados: **Ya estaba** (existía tal cual; solo se ha probado) · **Completado** (existía a medias; se ha completado) · **Nuevo** · **Pendiente de decisión**.
Pruebas: `tests/test_*.py` (servidor sobre una copia de la base) y `tests/e2e_walk.py` (navegador real con los 5 roles).

## Fase 1 · Seguridad urgente (v50.31)

| Punto | Estado | Qué se hizo | Cómo se probó |
|---|---|---|---|
| 1. Documentos (G1, G8) | Completado | Acceso: dueño, centro con reserva del propio buceador no cancelada o datos compartidos, admin con registro. `private, no-store` + `Content-Disposition`. Tipo por bytes mágicos, 10 MB. Archivo borrado al borrar el documento o la cuenta. Cada descarga y cada intento denegado en `audit_log`. | `test_g1_documents_access`, `test_g1_real_file_type_and_size` |
| 2. Alta de centros (G2) | Completado | Cuenta nueva siempre `recreational` con solicitud; ficha nueva oculta; teléfono solo como sugerencia (`suggested_center_id`); aprobación con método (email del dominio, llamada, documento) y nota. Informe `--report-center-accounts`. | `test_g2_*` |
| 3. Recorridos virtuales (G3) | Nuevo | Lista de dominios https (`WOD_EMBED_DOMAINS`), validación en servidor y navegador, carga solo tras «Cargar vídeo», subidas 15 MB comprobadas por contenido. | `test_g3_virtual_urls` + navegador |
| 4. CSP | Nuevo | CSP en todas las respuestas (PDF, SVG, 304 incluidos). Leaflet alojado. Sin scripts ni manejadores en línea. Geocodificación por el servidor. | `test_csp_and_headers_everywhere` + navegador sin violaciones |
| 5. Reservas públicas (G4) | Nuevo | Sesión del dueño/centro o token aleatorio de 48 caracteres; sin `user_id` ni apellido. | `test_g4_public_booking_needs_token` |
| 6. Clientes de centros (G5) | Nuevo | Ficha de cliente propia del centro (`guest_center_id`), nunca enlace por email; perfil y documentos solo con reserva propia o datos compartidos (`data_shares`); check-in con consentimiento; «Centros que ven tu ficha» con revocación. | `test_g5_*` |
| 7. Datos de salud (G6) | Completado | Tipo médico eliminado y rechazado en servidor; aviso; migración que borra y avisa (no había ninguno); textos y opcionalidad de fecha de nacimiento, contacto de emergencia y lastre. | `test_g6_no_medical_certificates` |
| 8. Tamaños (G7) | Nuevo | JSON 1 MB, subidas 15 MB, documentos 10 MB, rechazo antes de leer el cuerpo (413). | `test_g7_body_limits` |
| 9. Instalación (G9) | Nuevo | `WOD_ALLOW_SETUP=1` obligatorio; `--create-admin`. | `test_g9_setup_disabled` y uso del CLI en todas las pruebas |
| 10. CSRF (G10) | Completado | Sin `Origin`/`Referer` se rechaza (salvo webhooks e integración). Producción exige `WOD_PUBLIC_URL`. | `test_g10_csrf` |
| 11. Mensajes (G11) | Completado | Solo avisos ligados a una reserva propia, por email y a «Avisos» con el contacto del centro, sin respuesta. | `test_g11_no_free_messaging` |
| 12. Pagos (G12) | Nuevo | Campos mínimos en `/api/payments`. | `test_g12_payments_fields` |
| 13. Contraseñas y sesiones | Completado | PBKDF2 600 000 con prefijo y re-hash; límites (login, registro, recuperación) seguros y acotados; sesiones cerradas al cambiar de rol; limpieza periódica. | `test_13_*` |
| 14. Proxy | Nuevo | `WOD_TRUSTED_PROXIES`. | Pruebas unitarias de `wod.security` (en `test_units.py`) |
| 15. Registros | Nuevo | Sin query string, IP truncada, rotación diaria con plazo, `/api/health` mínima, alerta de 500 repetidos. | `test_15_*` |
| 16. Errores menores | Ya estaba / Completado | `return` del QR de promoción ya estaba. Conexiones SQLite cerradas por petición (`_ClosingConnection`). | `test_16_promo_qr_svg` |

## Fase 1B · Modos de reserva (v50.32)

| Punto | Estado | Qué se hizo | Cómo se probó |
|---|---|---|---|
| 1. Migración de «Reserva inmediata» | Nuevo | Servicios y plantillas a «Pago al reservar» o «Bajo petición»; lista en `booking_mode_migration`. | `InstantMigration.test_migration` |
| 2. «Pago al reservar» | Completado | Requisito de cobros online; bloqueo de plazas 15 min; invisible al centro hasta pagar; confirmación automática solo con Stripe; liberación al abandonar/caducar; gratis → confirmada; aviso si se desactivan los cobros. | `test_payment_mode_*`, `test_centre_disables_payments` |
| 3. «Bajo petición» | Completado | Sin plazas hasta aceptar; bandeja con contador y tiempo; aceptar/rechazar con motivo; plazos de respuesta y de pago; caducidad automática con avisos. | `test_request_*` |
| 4. Estados únicos | Nuevo | 8 estados en `wod/bookings.py`, usados en servidor, panel, «Mis reservas», correos y PDF; tarea cada minuto. | `test_units.BookingUnits` + pruebas anteriores |
| 5. Que se vea igual | Nuevo | Etiquetas y botones en buscador, ficha de centro y punto, reserva, «Mis reservas», panel; filtro «Confirmación inmediata». | `e2e_booking_modes.py` (35/35) |
| 6. Formulario de servicio | Completado | Dos opciones con explicación y ejemplo; plazos; plantillas por defecto según cobros; reservas en curso conservan su modo. | `test_mode_change_keeps_existing_bookings` + navegador |
| 7. Pruebas obligatorias | Nuevo | Todas las combinaciones listadas, más recorrido en navegador. | Ver arriba |
| Freelance sin centro con reservas de servicios | Pendiente (Fase 2) | La tabla de reservas exige un centro; se resuelve con las cuentas de cobro del freelance en la Fase 2. | — |

## Fase 1C · Marcadores (v50.33)

| Punto | Estado | Qué se hizo | Cómo se probó |
|---|---|---|---|
| Marcadores redondos y más pequeños | Nuevo | Círculo con la bandera de buceo, 19 px (ordenador) / 23 px (móvil), activo 26 px con anillo. | `e2e_markers.py` (medidas en `docs/capturas/fase-1c/medidas.txt`) |
| Zona de toque | Nuevo | 44 px en móvil sin agrandar el dibujo. | Medida en navegador |
| Agrupación | Nuevo | `leaflet.markercluster` alojado; grupo rojo liso legible en mapa y satélite. | Capturas antes/después y prueba de fluidez (0 fotogramas lentos, CPU ×4) |
| Accesibilidad | Nuevo | `title` y texto alternativo con el nombre del punto. | Navegador |

## Fase 1D · Idiomas (v50.33)

| Punto | Estado | Qué se hizo | Cómo se probó |
|---|---|---|---|
| 10 idiomas | Completado | es, en, fr, de, it, pt, pl, nl, zh, ru; nombres nativos en el selector. | `e2e_walk.py` y recorrido en pl/ru |
| Retirar ja, ko, zt | Nuevo | Archivados en `archive/i18n/`; usuarios y correos en cola pasan a en/zh (`migrate_v50_33`). | `test_units` (normalize_lang) + migración |
| Polaco y ruso | Nuevo | Web completa (3 812 frases + 426 patrones). Correos: pendiente pasada final. | Validador de marcadores/etiquetas y `tools/i18n_report.py` |
| Plurales | Nuevo | `Intl.PluralRules` con formas one/few/many/other. | Navegador (ru/pl) |
| Formatos | Completado | Fechas, horas e importes por idioma en web y correos. | Navegador |
| URL por idioma y hreflang | Nuevo | `?lang=`, `<html lang>`, `hreflang` + `x-default`. | `test_phase1d_languages` |
| Limpieza de traducciones | Nuevo | 47 claves basura eliminadas; informe por idioma. | `docs/i18n/informe.md` |
| Correos, textos legales y textos nuevos en 9 idiomas | Pendiente (pasada final) | Se traducirán juntos al final del encargo. | — |

## Fase 2 · Pagos (v50.34)

| Punto | Estado | Qué se hizo | Cómo se probó |
|---|---|---|---|
| 1. Sin comisión | Completado | Fuera la comisión del código, KPIs, datos legales, textos y README; historial conservado. | `test_direct_charge_without_commission`, `test_no_commission_in_legal_texts_and_settings`, `test_admin_sees_income_by_currency…` |
| 2. Cargos directos | Nuevo | Checkout en la cuenta del prestador; `stripe_account` en todas las llamadas; cuentas con propiedades de controlador (v1) y solo `card_payments`. | `test_every_stripe_call_carries_the_account`, `test_onboarding_uses_controller_properties` |
| 3. Webhook de Connect | Nuevo | Endpoint y secreto propios, `event.account`, idempotencia. | `test_connect_webhook_…`, `test_webhook_secrets_are_separate` |
| 4. Devoluciones | Nuevo | Por el prestador, totales o parciales; propuesta al cancelar el buceador con recordatorio; admin solo ve e incidencias. | `test_partial_then_total_refund_by_centre`, `test_only_the_provider_refunds`, `test_diver_cancel_proposes_refund_by_policy`, `test_refund_made_in_stripe_dashboard_is_recorded`, `test_dispute_marks_an_incident` |
| 5. Señal | Nuevo | Porcentaje o importe por persona; pagado y pendiente en la reserva; resto en mostrador. | `test_deposit_then_rest_at_the_desk` + navegador |
| 6. Política por centro y servicio | Completado | Horas + % devuelto; copia en la reserva; visible antes de pagar y en el justificante. | `test_late_cancel_uses_percentage`, `test_policy_is_copied_into_the_booking` |
| 7. Experiencias y freelance | Nuevo | Freelance con cuenta propia, reservas sin centro (tabla reconstruida con copia), panel de reservas y cobros. | `test_freelance_takes_bookings_and_payments` + navegador |
| 8. Justificante | Completado | Nuevo diseño y motor PDF Unicode con fuentes incrustadas; «Ingresos». | `test_voucher_names_the_provider_and_is_not_an_invoice` |
| 9. Precios e impuestos | Completado | Texto de impuestos; KPIs por moneda. | `test_centre_kpis_are_income_by_currency` |
| 10. Patrocinio | Nuevo | Etiqueta fija «Patrocinado»; registro de patrocinios. | `test_sponsored_label_is_fixed_and_sponsor_registered` + navegador |
| Migración | Nuevo | Copia previa, reconstrucción segura, `schema_migrations`. | `MigrationV5034` |
| Accounts v2 | Pendiente de decisión | Se usa v1 con propiedades de controlador (aviso en notas). | — |
| Devolución propuesta no hecha | Pendiente de decisión | Recordatorio a 72 h e incidencia; falta decidir medida adicional. | — |

## Fase 3 · Monedero → Puntos (v50.35)

| Punto | Estado | Qué se hizo | Cómo se probó |
|---|---|---|---|
| 1. Migración | Nuevo | Libro `points_ledger`; logros al libro; saldo € → puntos 1:1 redondeando hacia arriba; `cost_points`; historial conservado. | `WalletMigration` |
| 2. Recompensas | Completado | Concesión de puntos con límite por cliente y mes y por centro; ventajas definidas y pagadas por cada centro. | `test_grants_with_monthly_limit`, `test_offers_belong_to_a_centre…` |
| 3. Canje | Nuevo | Código con QR; el centro lo comprueba y valida (escanear o escribir) con estado y fecha; anulación y caducidad devuelven puntos. | `test_exchange_and_validation_by_the_centre`, `test_cancel_and_expiry_give_points_back` + navegador |
| 4. Prohibido | Nuevo | Sin recargas, transferencias, dinero ni Stripe. | `test_no_money_features` |
| 5. Textos | Completado | Sin «Monedero/saldo/wallet» en web, menú, pie, correos y PDF; página «Cómo funcionan los puntos». | navegador |
| Ruta `#/monedero` → `#/puntos` | Pendiente de decisión | `#/puntos` ya es la lista de puntos de buceo: se usa `#/mis-puntos`. | — |

## Fase 4 · Email y verificación en dos pasos (v50.35)

| Punto | Estado | Qué se hizo | Cómo se probó |
|---|---|---|---|
| 1. Envío | Completado | SMTP genérico, cola con reintentos y registro (ya existían); archivo `.eml` sin proveedor en desarrollo; guía Brevo + SPF/DKIM/DMARC. | `test_development_writes_emails_to_files` |
| 2. Plantillas | Completado | Nuevas: 48 h, cambio de reserva, caducidad de documentos, cambios legales, renovación de cuota, TOTP activado, comercial. | `test_reminders_48h_and_24h`, `test_document_expiry_alerts`, `test_booking_change_by_the_provider` |
| 3. Comerciales | Completado | Solo con consentimiento, baja en un clic (enlace y cabeceras RFC 8058), registro de consentimientos. | `test_commercial_emails_only_with_consent…` + navegador |
| 4. Doble verificación | Nuevo | TOTP opcional para todos, obligatorio para admin (no desactivable en producción), códigos de recuperación. | `TwoStep`, `AdminNeedsTotp` + navegador |
| Proveedor de email | Pendiente de decisión | Recomendado Brevo; solo cambia la configuración. | — |
