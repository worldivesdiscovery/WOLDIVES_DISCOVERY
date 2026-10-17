# Autenticación, sesiones y límites de intentos

Referencia: OWASP ASVS 5.0, capítulos V6 (autenticación) y V7 (sesiones). Informe completo en
[`docs/auditoria/v50.51/asvs-5.0-nivel2.md`](../auditoria/v50.51/asvs-5.0-nivel2.md). Todo lo que se describe aquí lo
comprueban `tests/test_v50_51_asvs.py`, `tests/test_v50_52_cobros_2fa.py` (verificación en dos pasos con cobros, v50.52)
y las pruebas anteriores de inicio de sesión.

## Vías de autenticación

Cada forma de entrar o de actuar sin contraseña, con su fuerza y quién la comprueba (todas en `app/server.py`). La
verificación en dos pasos obligatoria de la administración (`WOD_ADMIN_TOTP_REQUIRED=1`) vale en todas: una cuenta de
administración sin ella solo llega a «Mi cuenta» (`current_user` la trata como `admin_sin_2fa`). Desde la v50.52 pasa lo
mismo con quien cobra online (ver «Verificación en dos pasos»): `center_sin_2fa` / `freelance_sin_2fa`.

| Vía | Quién | Factores | Caducidad | Límite de intentos | Dónde |
|---|---|---|---|---|---|
| Contraseña (`POST /api/auth/login`) | Todos | Contraseña y, si está activada, código del autenticador o de recuperación | Sesión: ver «Sesiones» | Ver «Límites de intentos» | ruta `/api/auth/login`, `login_second_factor`, `check_totp_or_recovery` |
| Alta (`POST /api/auth/register`) | Buceadores; centros y freelance quedan pendientes de revisión | Contraseña nueva (política de abajo) | Sesión | 10 altas por hora y dirección (`WOD_REGISTER_MAX_PER_HOUR`) | ruta `/api/auth/register` |
| Invitación al equipo (`POST /api/team/join`) | Personas invitadas por el propietario de un centro | Enlace de un solo uso enviado al email invitado (32 bytes aleatorios, guardado con hash) + contraseña nueva | 7 días | — (el enlace no se puede adivinar) | ruta `/api/team/join` |
| Restablecer la contraseña (`/api/auth/forgot` y `/api/auth/reset`) | Todos | Enlace de un solo uso enviado al email de la cuenta | 1 hora | 5 por dirección y 5 por cuenta cada 15 min | rutas `/api/auth/forgot` y `/api/auth/reset` |
| Instalador web (`/api/setup`) | Solo en una instalación nueva | Crea la primera administración | Una vez | 10 por hora y dirección | Solo con `WOD_ALLOW_SETUP=1` o en el entorno de pruebas; el servidor no arranca en producción con él activo |
| Entrada rápida de pruebas (`/api/pruebas/entrar`) | Solo el entorno de pruebas (`WOD_DEMO_MODE=1`) | Ninguno: cuentas `*.prueba` inventadas | Sesión | — | **Nunca** la administración (403). El servidor no arranca con `WOD_DEMO_MODE=1` en la dirección de producción y las cuentas de prueba no existen en la base real |
| Clave de integración del centro (`X-WORLDIVES-API-Key` en `/api/integrations/bookings`) | El programa de reservas del centro | Clave aleatoria guardada con hash, que el centro puede desactivar y regenerar | Hasta que el centro la cambie | — | Solo crea reservas de ese centro |
| Enlace del resumen del barco (`/api/manifest/<id>/resumen.pdf?t=`) | Equipo del centro, para abrirlo en otro dispositivo | Firma HMAC con `WOD_SECRET_KEY` ligada a la salida y a la persona | 10 minutos | — | `boat_pdf_token` |
| Enlaces de los avisos (`/r/<token>`, `/api/r/<token>`) | Buceador que recibe un aviso | Firma HMAC con `WOD_SECRET_KEY` ligada a la reserva y al tipo de aviso | 14 días y al menos hasta 2 días después de la salida | — | Solo esa reserva; elegir reembolso o cambio solo con el enlace del aviso de salida cancelada |
| QR de la reserva | Equipo del centro al escanear | Testigo aleatorio de la reserva | Mientras exista la reserva | — | Solo lo valida el propio centro (`/api/pro/escanear`) |
| Calendario privado (`/ical/<token>.ics`) | Centro o freelance | Testigo aleatorio largo | Hasta que lo regenere | — | Solo lectura de su propio calendario |
| Avisos de Stripe y de WhatsApp | Stripe y Meta | Firma del proveedor (`STRIPE_WEBHOOK_SECRET`, `WHATSAPP_APP_SECRET`) | — | — | Nunca se marca un pago sin la confirmación firmada de Stripe |

## Política de contraseñas

- Entre 10 y 256 caracteres; se admiten espacios, frases y cualquier carácter; no se exige mezclar tipos de caracteres
  ni se obliga a cambiarla cada cierto tiempo (ASVS V6.2).
- Se rechazan (`wsec.password_problem`, la misma regla en el registro, el restablecimiento, el cambio y las altas del
  equipo y de la administración):
  - las 20.000 contraseñas de 10 o más caracteres que más aparecen en filtraciones públicas
    (`app/wod/contrasenas-comunes.txt`), también con números o símbolos añadidos al final;
  - las que solo son palabras de esta web o del buceo más números o símbolos (`CONTEXT_WORDS`): *worldives*,
    *worldivesdiscovery*, *worlddives*, *woldives*, *discovery*, *buceo*, *bucear*, *buceador(a)*, *scuba*, *diving*,
    *diver*, *padi*, *instructor(a)*, *centro*, *freelance*, *admin*, *administrador*, *prueba*, *demo*, *contraseña* y
    *password*, sin tener en cuenta mayúsculas ni acentos. Una frase que las contenga junto a otras palabras sí vale
    («buceo en Xàbia con mi familia»).
- Una contraseña de más de 256 caracteres al entrar cuenta como fallida (no se recorta).
- Se guardan con PBKDF2-SHA256 de 600.000 iteraciones y sal aleatoria; las antiguas se rehacen al entrar.

**Lista de contraseñas comunes.** Sale de SecLists (licencia MIT): `Passwords/Common-Credentials/Pwdb_top-1000000.txt`
y `100k-most-used-passwords-NCSC.txt`, en minúsculas, de 10 a 64 caracteres, sin repetidas, las 20.000 primeras en el
orden de frecuencia. Para rehacerla, descarga esas dos listas y aplica ese filtro; la cabecera del archivo lo explica.
No se consulta ningún servicio externo al registrarse (las contraseñas no salen del servidor).

## Límites de intentos

Todos son comunes a todos los procesos del servidor (`wod.security.SharedRateLimiter`, archivo
`<base>-limites.sqlite3` junto a la base) y cuentan en ventanas fijas. Una dirección IPv6 cuenta por su red /64
(`wsec.ip_group`): una conexión suele tener una /64 entera.

| Límite | Clave | Cuántos | Ventana | Variable |
|---|---|---|---|---|
| Inicio de sesión por cuenta y dirección | dirección + lo escrito | 8 | 15 min | `WOD_LOGIN_MAX_ATTEMPTS`, `WOD_LOGIN_WINDOW_SECONDS` |
| Inicio de sesión por dirección | dirección | 40 (5 × 8) | 15 min | las mismas |
| Inicio de sesión por cuenta | número de la cuenta (usuario y email comparten el contador) | 24 (3 × 8) | 15 min | las mismas |
| Código de dos pasos | cuenta | 6 | 15 min | — |
| «Contraseña actual» en cambios sensibles | cuenta | 10 | 15 min | — |
| Recuperar la contraseña | dirección; y cuenta | 5 y 5 | 15 min | — |
| Altas | dirección | 10 | 1 hora | `WOD_REGISTER_MAX_PER_HOUR` |

**Respuesta.** Pasado el límite se responde 429 «Demasiados intentos». Al llegar al límite por cuenta se avisa a la
administración (`security_alert('login_bruteforce')`) y cada fallo queda en la actividad de la cuenta (`login_failed`).
Las respuestas y el tiempo de respuesta son iguales exista o no la cuenta.

**Bloqueo malicioso.** Nadie puede dejar fuera al titular de una cuenta fallando a propósito:

- el límite por cuenta no se aplica desde una red desde la que el titular ya entró bien en los últimos 90 días (la misma
  IPv4 o la misma /64, guardada como huella en la actividad de la cuenta; `known_network`);
- lo mismo para pedir el enlace de recuperación;
- restablecer la contraseña desbloquea la cuenta al momento (quien lee el email de la cuenta es su titular).

## Sesiones

| Qué | Valor | Variable |
|---|---|---|
| Cierre por inactividad | 4 horas sin usarla | `WOD_SESSION_IDLE_SECONDS` |
| Duración máxima | 8 horas desde que se entró, aunque se use | `WOD_SESSION_TTL_SECONDS` |
| Sesiones a la vez | Sin límite: cada persona las ve en «Mi cuenta → Sesiones abiertas» y las cierra | — |
| Volver a entrar | Cierra la sesión que tenía ese navegador | — |
| Cambiar la contraseña, activar o desactivar la verificación en dos pasos o regenerar los códigos | Cierra las demás sesiones | — |
| Restablecer la contraseña | Cierra todas | — |
| Administración | Puede cerrar las sesiones de una cuenta o de todas, con motivo y registro | `POST /api/admin/sessions/close` |

La cookie es `__Host-wd_session` con HTTPS (`HttpOnly`, `Secure`, `SameSite=Lax`, `Path=/`); el servidor solo guarda el
hash del testigo. Justificación frente a NIST SP 800-63B (AAL2 pide volver a entrar cada 12 h y tras 30 min sin uso):
las 8 h máximas cumplen la primera parte; las 4 h sin uso son un equilibrio para el equipo de un centro que trabaja en
la playa o en el barco, compensado por la cookie `HttpOnly`/`SameSite`, la verificación en dos pasos obligatoria de la
administración, la lista de sesiones abiertas y la contraseña + código que se piden para cambiar el email o la
contraseña. Se puede bajar con `WOD_SESSION_IDLE_SECONDS`.

## Verificación en dos pasos

- Autenticador (TOTP, RFC 6238, 30 s, ±1 paso); cada código vale una sola vez, también con varios intentos a la vez.
- 8 códigos de recuperación de 120 bits, de un solo uso, guardados con hash.
- Obligatoria para la administración con `WOD_ADMIN_TOTP_REQUIRED=1` (en producción no se puede apagar).
- **Obligatoria con cobros online** (v50.52, decisión del titular del 14/10/2026, ASVS V6.3.3), con
  `WOD_PAYMENTS_TOTP_REQUIRED=1` (en producción no se puede apagar; solo el entorno de pruebas lo apaga):

  | Quién | Cuándo se le exige | Sin ella |
  |---|---|---|
  | Cuenta de centro (propietario) o freelance con **Stripe Connect conectado o en proceso** (`stripe_account_id`) | Antes de conectar Stripe: sin ella, «Activar los cobros online» responde 403 y no se crea la cuenta en Stripe. Si ya tenía cobros: **14 días** desde que el servidor lo detecta (aviso en el panel y por correo, `totp_required_payments`) | Pasado el plazo, solo «Mi cuenta» |
  | Miembro del equipo de un centro con cobros online que tenga el permiso **«Cobros»** (también el «Encargado», que lo tiene todo) | En su siguiente uso del panel, sin plazo | Solo «Mi cuenta» |
  | Centros sin cobros online, sus equipos y los buceadores | Nunca: opcional, recomendada en el panel | — |

  «Solo «Mi cuenta»» quiere decir: `/api/me`, cerrar sesión, `/api/account/…` (su propia cuenta, incluida la activación),
  aceptar los textos legales y cambiar de centro (`PROVIDER_WITHOUT_2FA_PATHS`). Cualquier ruta del panel (reservas,
  clientes, cobros, exportaciones, manifiesto, agenda, avisos, equipo…) responde 403 con «Activa la verificación en dos
  pasos en «Mi cuenta»…» (`PROVIDER_PANEL_PREFIXES`), y la web y la app profesional enseñan esa pantalla. Las reservas y
  los pagos de sus clientes siguen funcionando: los avisos de Stripe (webhooks) no usan sesión.
- **No se puede desactivar** mientras la cuenta tenga cobros online o el perfil tenga «Cobros» (403 y suceso
  `totp_disable_refused`). Sin cobros se puede desactivar como antes.
- **Registro** (en la actividad): `totp_enabled`, `totp_disabled`, `totp_recovery_regenerated`, `totp_deadline_set`
  (empieza el plazo de 14 días), `stripe_connect_needs_totp` (intento de conectar Stripe sin ella) y los sucesos de
  seguridad `totp_required_block` (petición frenada por no tenerla, uno por minuto como mucho) y `totp_disable_refused`.
- Para el resto (buceadores y centros sin cobros) la compensan los límites de intentos, el aviso de inicio de sesión
  fallido en la actividad, la lista de sesiones abiertas y la contraseña + código para los cambios sensibles.

**Si alguien pierde el autenticador y los códigos.** No hay ruta automática. La administración:

1. pide a la persona que escriba desde el email de la cuenta (y, para centros y freelance, la misma comprobación que en
   la revisión de su solicitud: documento o dominio del centro; con cobros online, además, que confirme desde su panel de
   Stripe un dato que solo tiene el titular, por ejemplo los cuatro últimos dígitos de la cuenta bancaria de cobro);
2. con esa prueba, desactiva la verificación en dos pasos desde la línea de órdenes del servidor
   (`sqlite3 <base> "UPDATE users SET totp_enabled=0,totp_secret=NULL,totp_recovery=NULL,totp_last_step=NULL WHERE id=<n>"`)
   y cierra sus sesiones (*Administración → Usuarios → Cerrar sesiones*);
3. lo anota en el registro de incidencias con la prueba de identidad usada. La persona la vuelve a activar en «Mi cuenta»
   (con cobros online, el panel no se abre hasta que lo haga: la cuenta queda protegida mientras tanto).
