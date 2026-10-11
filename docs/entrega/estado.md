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
