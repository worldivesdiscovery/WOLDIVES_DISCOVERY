# WORLDIVES DISCOVERY v50.35: puntos (Fase 3) y email + verificación en dos pasos (Fase 4)

## Fase 3 · Del monedero a los puntos

Los puntos **no son dinero**: se ganan buceando o los regala un centro, y solo se canjean por **ventajas que define y paga cada centro**.

### Migración (`migrate_v50_35`)
- Nuevo libro de puntos `points_ledger` (puntos enteros). El saldo es la suma del libro.
- Los logros ya conseguidos (`reward_events.points`) pasan al libro.
- El saldo del monedero de cada usuario se convierte **1 € = 1 punto, redondeando hacia arriba** («Saldo del monedero convertido a puntos (7,30 € = 8 puntos)»). El historial `wallet_transactions` se conserva sin tocar y se ve en «Mis puntos → Historial del antiguo monedero».
- `cost_wallet` (€) → `cost_points`, redondeando hacia arriba. Los códigos ya emitidos reciben fecha de caducidad.
- La base entregada no tenía saldos ni canjes. Solo añade y transforma; no borra nada.

### Recompensas y canje
- **Conceder puntos** (sustituye a `/api/provider/wallet-grant`, que ahora responde 410): solo a clientes del centro (reserva o check-in), con **límite por cliente y mes** (100 por defecto) y **por centro y mes** (3 000). Variables `WOD_POINTS_GRANT_MAX_PER_CLIENT_MONTH` y `WOD_POINTS_GRANT_MAX_PER_CENTER_MONTH`.
- Las ofertas de «€ de crédito / € de descuento» pasan a **ventajas del centro** (descuento, inmersión o actividad, descuento en curso, seguro de día pagado por el centro, regalo). Solo un centro puede ofrecerlas; las ofertas de WORLDIVES sin centro quedan desactivadas y se han quitado de los datos de demostración.
- **Canje**: el buceador recibe un código con QR (válido 180 días, `WOD_POINTS_CODE_DAYS`). Puede anularlo y recupera los puntos; si caduca sin usar, también.
- **Validación por el centro**: en su panel («Ventajas y puntos») escanea el QR con la cámara (si el navegador lo permite) o escribe el código, ve qué es, de quién (nombre e inicial) y su estado, y lo valida. Queda fecha, centro y persona que lo validó; un código usado no vuelve a valer.

### Prohibido (y comprobado)
No hay recargas con dinero, transferencias entre usuarios, conversión a dinero ni uso como saldo en Stripe: no existen esas rutas y el pago online nunca descuenta puntos.

### Textos
- «Monedero», «saldo» y «wallet» desaparecen de la web, del menú, del pie, de los correos y de los PDF. Nueva página **«Cómo funcionan los puntos»** (`#/como-funcionan-los-puntos`).
- **Pendiente de decisión — ruta:** el encargo pide que `#/monedero` redirija a `#/puntos`, pero `#/puntos` ya es la lista de **puntos de buceo** (enlazada desde todo el catálogo). Para no romperla, la página de puntos está en **`#/mis-puntos`** y `#/monedero` redirige allí. Si se prefiere, se puede mover la lista de puntos de buceo a `#/puntos-de-buceo` y usar `#/puntos` para los puntos.
- Los textos nuevos se traducirán a los 9 idiomas en la pasada final de traducción.

## Fase 4 · Email

- **SMTP genérico** (`WOD_SMTP_HOST`, `PORT`, `SECURITY`, `USER`, `PASSWORD`, `WOD_MAIL_FROM`…), sin atarse a ningún proveedor. **Recomendado: Brevo.** Guía con SPF, DKIM y DMARC en `docs/despliegue.md`.
- **Cola con reintentos y registro** (ya existía desde v50.30; ahora además guarda el canal de envío).
- **Sin proveedor, en desarrollo**: los correos se escriben como archivos `.eml` en `data/mail-outbox/` (o `WOD_MAIL_FILE_DIR`). En producción esperan en la cola y el servidor avisa al arrancar.
- **Plantillas nuevas**: recordatorio **48 h** (además del de 24 h), **cambio de fecha u hora** de una reserva (nueva acción del centro «Cambiar fecha u hora»), **documento a punto de caducar** (30 y 7 días) y **caducado**, **cambios legales**, **renovación de la cuota** (la usará la Fase 6), **verificación en dos pasos activada** y **comunicación comercial**. Ya existían: verificación de email, recuperación de contraseña con enlace de un solo uso de 1 h, confirmación y cancelación de reserva.
- **Comunicaciones comerciales** solo a quien dio su consentimiento (y tiene el email verificado), con **baja en un clic**: enlace en el pie (`#/baja?t=…`) y cabeceras `List-Unsubscribe` / `List-Unsubscribe-Post` (RFC 8058). Casilla «Novedades y ofertas» en «Mi cuenta». Envío desde *Administración → Correos*, con prueba previa al administrador. Cada alta y baja queda en `consent_log`.

## Fase 4 · Verificación en dos pasos (TOTP)

- **Opcional para todos**: en «Mi cuenta» se activa con la contraseña, un QR para la aplicación (Google Authenticator, Microsoft Authenticator, Aegis…) y un código. Se entregan 8 **códigos de recuperación** de un solo uso (se guardan cifrados con hash). Al activarla se cierran las demás sesiones y se avisa por email.
- **Obligatoria para administradores** (`WOD_ADMIN_TOTP_REQUIRED=1`, que en producción no se puede desactivar): sin ella, el administrador solo puede entrar en «Mi cuenta» para activarla; no puede desactivarla.
- Un código nunca se acepta dos veces; intentos limitados.
- Implementación propia según RFC 6238 (`app/wod/totp.py`), comprobada con los vectores de prueba del RFC.

## Cómo se probó
- `tests/test_phase3_points.py` (8): ganar puntos, canje y validación por el centro, permisos entre centros, anulación y caducidad con devolución de puntos y stock, concesión con límites y permisos, rutas de dinero inexistentes, ventajas solo de centros y en puntos enteros, migración 1:1 con redondeo e idempotencia.
- `tests/test_phase4_email_totp.py` (8): TOTP opcional completo (alta, login en dos pasos, código repetido rechazado, recuperación de un solo uso, baja), admin obligado, producción sin TOTP rechazada, correos a archivo, recordatorios 48/24 h una sola vez, avisos de caducidad, cambio de reserva con plazas y permisos, comunicaciones comerciales solo con consentimiento y baja en un clic sin sesión.
- `tests/e2e_points_email.py`: 20/20 en navegador (buceador en móvil, centro, administrador). Capturas en `docs/capturas/fase-3-4/`.
- Todas las pruebas anteriores siguen pasando.

## Para abogado / gestoría
- Revisar el texto «Cómo funcionan los puntos» (programa de fidelización sin valor monetario) y su encaje en las condiciones de uso.
- Confirmar el texto del consentimiento comercial y del pie de los correos (LSSI art. 21 y RGPD).
