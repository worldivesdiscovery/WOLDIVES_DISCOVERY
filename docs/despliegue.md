# Despliegue de WORLDIVES DISCOVERY

> Este documento se completa en la Fase 7 (servidor, proxy, copias de seguridad y monitorización).
> Aquí está ya la parte de **correo electrónico** (Fase 4).

## Correo electrónico

WORLDIVES envía todos los correos por **SMTP genérico**: sirve cualquier proveedor y se cambia sin tocar el código.
El proveedor está **pendiente de decisión del titular**. Recomendado: **Brevo** (empresa europea, servidores en la UE,
SMTP y API en el plan gratuito, hasta 300 correos al día).

### Variables

| Variable | Ejemplo | Para qué |
|---|---|---|
| `WOD_SMTP_HOST` | `smtp-relay.brevo.com` | Servidor SMTP. Sin él no se envía nada (ver «Sin proveedor»). |
| `WOD_SMTP_PORT` | `587` | 587 (STARTTLS) o 465 (SSL). |
| `WOD_SMTP_SECURITY` | `starttls` | `starttls`, `ssl` o `none` (solo en pruebas locales). |
| `WOD_SMTP_USER` | `usuario@smtp-brevo.com` | Usuario SMTP que da el proveedor. |
| `WOD_SMTP_PASSWORD` | *(clave SMTP)* | Solo en el entorno del servidor, nunca en el repositorio. |
| `WOD_MAIL_FROM` | `reservas@tudominio.com` | Remitente. Debe ser del dominio autenticado (SPF/DKIM). |
| `WOD_MAIL_FROM_NAME` | `WORLDIVES DISCOVERY` | Nombre visible del remitente. |
| `WOD_MAIL_REPLY_TO` | `hola@tudominio.com` | Opcional: a dónde van las respuestas. |
| `WOD_MAIL_FILE_DIR` | `/var/lib/worldives/mail` | Opcional: escribe los correos como archivos `.eml` en vez de enviarlos. |

### Cómo funciona el envío

- Cada correo se prepara en el momento del suceso, en el idioma del destinatario, y se guarda en la **cola** (`email_outbox`)
  dentro de la misma transacción que el cambio que lo provoca: si el cambio no se guarda, el correo tampoco.
- Un proceso en segundo plano envía la cola por lotes reutilizando la conexión SMTP. Si falla, **reintenta** con espera
  creciente (2, 4, 8… hasta 60 minutos) y lo marca como fallido tras 6 intentos. Lo que lleva más de 72 h en cola caduca.
- **Registro**: en *Administración → Correos* se ven todos los envíos (estado, intentos, último error, canal SMTP o archivo),
  se puede reenviar uno y mandar un correo de prueba.

### Sin proveedor

- **En desarrollo** (`WOD_ENV` distinto de `production`), si no hay `WOD_SMTP_HOST`, los correos se escriben como archivos
  `.eml` en `data/mail-outbox/` (o en `WOD_MAIL_FILE_DIR`). Se abren con cualquier programa de correo.
- **En producción** sin `WOD_SMTP_HOST`, los correos esperan en la cola y se envían en cuanto se configure (hasta 72 h).
  El servidor avisa al arrancar.

### Autenticación del dominio (SPF, DKIM y DMARC)

Sin estos registros DNS los correos acaban en spam o se rechazan (Gmail y Yahoo los exigen desde 2024).
Con Brevo (los valores exactos los da el panel del proveedor en *Senders, Domains & Dedicated IPs → Domains*):

1. **SPF** (registro TXT en el dominio raíz). Si ya existe un SPF, se añade el `include` al mismo registro; nunca dos SPF:
   ```
   tudominio.com.  TXT  "v=spf1 include:spf.brevo.com ~all"
   ```
2. **DKIM** (registro TXT o CNAME que da Brevo, por ejemplo):
   ```
   brevo._domainkey.tudominio.com.  TXT  "k=rsa;p=MIGfMA0GCSqG…"
   ```
3. **Código de verificación de Brevo** (TXT `brevo-code:…`) para demostrar que el dominio es tuyo.
4. **DMARC** (TXT). Empezar en modo observación y endurecer cuando los informes salgan limpios:
   ```
   _dmarc.tudominio.com.  TXT  "v=DMARC1; p=none; rua=mailto:dmarc@tudominio.com; adkim=s; aspf=s"
   ```
   Después de 2–4 semanas sin fallos: `p=quarantine` y, más adelante, `p=reject`.
5. Comprobar con el panel del proveedor y con una herramienta externa (por ejemplo, mail-tester.com) que SPF, DKIM y DMARC
   salen «pass».

Otros proveedores SMTP europeos válidos: Mailjet (Francia), Scaleway TEM (Francia). Si se elige otro, solo cambian
`WOD_SMTP_*` y los registros DNS que indique.

### Comunicaciones comerciales

- Solo a quien dio su **consentimiento** expreso (casilla separada al registrarse o en *Mi cuenta*), con email verificado.
  Cada consentimiento y cada baja quedan en `consent_log`.
- Cada correo comercial lleva **baja en un clic**: enlace en el pie (`#/baja?t=…`) y cabeceras `List-Unsubscribe` y
  `List-Unsubscribe-Post: List-Unsubscribe=One-Click` (RFC 8058), que usan Gmail, Outlook y Yahoo.
- Se envían desde *Administración → Correos → Comunicación comercial*, primero como prueba al administrador.
- Los correos de servicio (reservas, pagos, seguridad, cambios legales) no son comerciales y no llevan baja.

### Correos automáticos

| Suceso | Plantilla |
|---|---|
| Registro / cambio de email | `verify_email`, `verify_email_change` |
| Recuperar contraseña (enlace de un solo uso, 1 h) | `password_reset`, `password_changed` |
| Reserva: solicitud, confirmación, pago, cambio de fecha u hora, cancelación, rechazo, caducidad | `booking_request`, `booking_confirmed`, `payment_receipt`, `booking_changed`, `booking_cancelled_*`, `booking_rejected`, `booking_expired` |
| Recordatorios | `reminder_48h` (2 días antes) y `reminder` (el día anterior) |
| Documentos (titulación, seguro) | `document_expiring` (30 y 7 días antes) y `document_expired` |
| Cambios en documentos legales | `legal_update` |
| Renovación de la cuota del centro | `plan_renewal` |
| Verificación en dos pasos activada | `totp_enabled` |
| Devoluciones y disputas | `refund_issued`, `center_refund_reminder`, `center_dispute` |

Todas las plantillas se pueden ver con datos de ejemplo en *Administración → Correos*, en los 10 idiomas de la web.
