# Claves y criptografía · inventario y política

Referencia: OWASP ASVS 5.0, V11 (criptografía) y V13.3 (secretos). Ninguna clave está en el código ni en el
repositorio: todas se leen del `.env` del servidor (`chmod 600`, propietario `worldives`), que nunca se copia al chat,
a un correo ni a una incidencia. El servidor no arranca en producción si falta una clave obligatoria o es corta
(`check_production_settings`). Revisión: en cada versión, con la lista de lanzamiento
([`docs/legal/lista-lanzamiento.md`](../legal/lista-lanzamiento.md)).

## Inventario

| Clave o secreto | Para qué | Algoritmo | Dónde se usa | Nunca se usa para |
|---|---|---|---|---|
| `WOD_SECRET_KEY` (≥32 caracteres) | Firmar enlaces que funcionan sin sesión: avisos de reservas (14 días), resumen del barco (10 min), reto de la verificación en dos pasos; huella de las direcciones IP y de las claves de los límites | HMAC-SHA256 | `notice_link`, `boat_pdf_token`, `login_second_factor`, `wsec.ip_hash`, `SharedRateLimiter` | Cifrar datos (eso es `WOD_DATA_KEY`) |
| `WOD_DATA_KEY` (≥32) y `WOD_DATA_KEY_OLD` | Cifrar teléfonos, credenciales de WhatsApp y secretos del autenticador; huella para buscar teléfonos | AES-256-GCM (nonce de 96 bits por valor, id de clave en cada valor); HMAC-SHA256 | `wod/cifrado.py` | Copias de seguridad |
| `WOD_BACKUP_KEY` (≥32) y `WOD_BACKUP_KEY_OLD` | Cifrar las copias de seguridad, también las que salen del servidor | AES-256-GCM por bloques de 4 MB (número y «último» autenticados) | `wod/backup.py` | Datos de la base |
| Contraseñas | Comprobar quién entra | PBKDF2-SHA256, 600.000 iteraciones, sal de 16 bytes | `wsec.hash_password` | — |
| Testigos de sesión | La cookie `__Host-wd_session` | 32 bytes aleatorios; en la base, SHA-256 | `login_user` | — |
| Enlaces de un solo uso (restablecer contraseña, invitación al equipo, borrar la cuenta) | Probar que se lee el email | 32 bytes aleatorios; en la base, SHA-256 | `new_password_reset`, `/api/center/team/invite`, `request_account_deletion` | — |
| Códigos de recuperación de la verificación en dos pasos | Entrar sin el autenticador | 120 bits aleatorios; en la base, SHA-256 | `wod/totp.py` | — |
| Autenticador (TOTP) | Segundo factor | HMAC-SHA1 de RFC 6238 (lo que usan las aplicaciones de autenticación; seguro para este uso) | `wod/totp.py` | — |
| Clave de integración del centro | Programas del centro que crean reservas | `wod_` + 32 bytes aleatorios; en la base, SHA-256 | `/api/integrations/bookings` | — |
| Calendario privado y QR de la reserva | Leer el calendario o comprobar una reserva | Testigo aleatorio largo | `/ical/…`, `/api/pro/escanear` | — |
| `STRIPE_SECRET_KEY` y `STRIPE_WEBHOOK_SECRET(_CONNECT)` | Cobros directos al centro y comprobar los avisos de Stripe | Los de Stripe (HMAC-SHA256 en los avisos) | `stripe_module`, `stripe_webhook` | Guardar tarjetas (nunca pasan por WORLDIVES) |
| `STRIPE_PUBLISHABLE_KEY` (v50.58) | El formulario de pago de Stripe dentro de la reserva exprés (Stripe.js). Es pública por diseño (`pk_…`), pero se pone solo en el `.env`; si no es del mismo modo que la secreta (test/live), no se usa | — | `stripe_publishable_key`, `sales_stripe` | Cobrar o leer pagos (eso solo lo hace la secreta, en el servidor) |
| `WHATSAPP_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN` y testigos de cada centro | Avisos por WhatsApp | HMAC-SHA256 en los avisos de Meta; testigos guardados con AES-256-GCM | `wod/whatsapp.py` | — |
| `WOD_FCM_CREDENTIALS` (cuenta de servicio de Firebase) | Avisos en el móvil | RSA-2048 con RS256 (**excepción aceptada**: la impone Google; el aviso al móvil está apagado si no se configura) | `wod/push.py` | — |
| `ARCGIS_API_KEY` | Vista satélite (el servidor la usa, nunca llega al navegador) | — | proxy `/api/tiles/satellite` | — |
| `WOD_SMTP_PASSWORD` | Enviar correos | TLS con certificado comprobado (STARTTLS o SSL) | `_smtp_open` | — |
| Certificado HTTPS | Cifrar la web | Lo emite y renueva Caddy (Let's Encrypt) | proxy | — |

## Política

| Paso | Regla |
|---|---|
| Generar | `python3 -c "import secrets;print(secrets.token_urlsafe(48))"` en el propio servidor. Nunca una frase ni una clave reutilizada |
| Guardar | Solo en el `.env` del servidor y una copia en el gestor de contraseñas del titular. Como mucho dos personas con acceso |
| Cambiar | Una vez al año y siempre que se sospeche una filtración o deje el proyecto alguien que la conocía |
| Retirar la antigua | Cuando ya no haga falta (abajo) se borra del `.env` y del gestor de contraseñas |

**Cómo se cambia cada una sin perder datos**

- `WOD_DATA_KEY`: la actual pasa a `WOD_DATA_KEY_OLD`, se pone la nueva y se ejecuta
  `scripts/seguridad/rotar_clave_datos.py`, que vuelve a cifrar todo con la nueva. Después se borra `WOD_DATA_KEY_OLD`.
- `WOD_BACKUP_KEY`: la actual pasa a `WOD_BACKUP_KEY_OLD` y se pone la nueva. Las copias nuevas usan la nueva; las
  anteriores se siguen abriendo con la antigua. Se borra `WOD_BACKUP_KEY_OLD` cuando la copia más antigua guardada sea
  posterior al cambio (12 meses con los valores por defecto).
- `WOD_SECRET_KEY`: se cambia y se reinicia. Efecto: se cierran los enlaces de avisos ya enviados (el buceador entra con
  su cuenta) y los enlaces del resumen del barco; las huellas de IP de la actividad dejan de coincidir con las nuevas
  (la «red conocida» de cada cuenta vuelve a aprenderse). No afecta a las sesiones ni a las contraseñas.
- Stripe, WhatsApp, ArcGIS, SMTP y Firebase: se genera la nueva en el panel del proveedor, se pone en el `.env`, se
  reinicia y se revoca la antigua en el proveedor.

**Si se filtra una clave**: cambiarla enseguida como arriba, revocar la antigua en el proveedor, revisar
*Administración → Actividad* y *Seguridad* y, si pudo afectar a datos personales, seguir el procedimiento de brechas de
[`docs/legal/guia-operacion.md`](../legal/guia-operacion.md).
