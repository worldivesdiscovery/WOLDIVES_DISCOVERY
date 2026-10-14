# Despliegue de WORLDIVES DISCOVERY (v50.38)

Guía para poner la web en un servidor propio (VPS) con HTTPS, reinicio automático, copias de seguridad y avisos.
Los archivos de ejemplo están en `docs/despliegue/`. Los mapas tienen su propia guía: `docs/mapas.md`.
**Instalación paso a paso en Hostinger (KVM 2, UE) con el zip de producción: `docs/despliegue/GUIA-VPS.md`** (v50.52).

## 1. Servidor

- **VPS Linux** (Debian 12 o Ubuntu 24.04) en la UE, con **2 vCPU y 4 GB de RAM** para empezar, y disco SSD de 40 GB más el mapa base (ver `docs/mapas.md`).
- **Python 3.11 o superior.** La web no necesita base de datos externa: usa SQLite (ver el apartado 9).
- Un usuario sin privilegios para la aplicación:

```bash
sudo adduser --system --group --home /opt/worldives worldives
# Con el zip de PRODUCCIÓN (docs/despliegue/GUIA-VPS.md, apartado 3), nunca con «git clone»: la carpeta .git (todo el
# historial) no debe quedar en el servidor (ASVS 5.0 V13.4.1).
sudo unzip worldives-v<versión>-PRODUCCION.zip -d /opt/ && sudo mv /opt/worldives-v<versión>-PRODUCCION/* /opt/worldives/ && sudo chown -R worldives: /opt/worldives
cd /opt/worldives && sudo -u worldives python3 -m venv .venv && sudo -u worldives .venv/bin/pip install -r requirements.txt
sudo mkdir -p /var/backups/worldives && sudo chown worldives: /var/backups/worldives
```

## 2. Variables de entorno

Copia `.env.example` a `/opt/worldives/.env`, rellénalo y protégelo (`chmod 600`, propietario `worldives`). El servidor y sus comandos lo leen solos (o el archivo de `WOD_ENV_FILE`); lo que venga del entorno tiene prioridad. **Las claves (Stripe, SMTP, ArcGIS, `WOD_SECRET_KEY`) solo viven en ese archivo, nunca en el repositorio.** Mínimo para producción:

```ini
WOD_ENV=production
WOD_PUBLIC_URL=https://worldivesdiscovery.com
WOD_SECRET_KEY=<64 caracteres aleatorios: python3 -c "import secrets;print(secrets.token_urlsafe(48))">
WOD_HOST=127.0.0.1
WOD_PORT=8000
WOD_TRUSTED_PROXIES=127.0.0.1
WOD_WORKERS=2
WOD_DB_PATH=/opt/worldives/data/worldives.sqlite3
WOD_BACKUP_DIR=/var/backups/worldives
WOD_BACKUP_COMMAND=/opt/worldives/scripts/copia_externa.sh
```

Con `WOD_ENV=production` el servidor **no arranca** si falta algo esencial (URL https, clave secreta, verificación en dos pasos de los administradores) y avisa al arrancar de lo recomendable (SMTP, Stripe, mapa base, satélite).

**`WOD_TRUSTED_PROXIES`**: la web solo cree la cabecera `X-Forwarded-For` (la IP real del visitante) si la petición llega desde una de estas direcciones. Con Caddy o nginx en el mismo servidor, `127.0.0.1`. Sin esto, los límites por IP (inicio de sesión, denuncias, registro) verían a todos los visitantes como si fueran el proxy.

## 3. Base de datos de producción (empieza limpia)

```bash
cd /opt/worldives
sudo -u worldives .venv/bin/python app/server.py --create-admin
```

La base se crea en el primer uso (el primer arranque o `--create-admin`, lo que llegue antes; v50.54) a partir de
`data/seed/catalogo.sqlite3`: puntos con sus descripciones
propias en 9 idiomas, zonas, tipos, países, titulaciones, textos legales y (v50.51) el catálogo de 31 especies con
ilustraciones propias. **No lleva usuarios, centros, reservas, mensajes, pagos ni registros.** El primer
administrador se crea con `--create-admin` y debe activar la verificación en dos pasos al entrar. En la web real no
hay pantalla de alta de administradores. Si da error o se olvida la contraseña (`--reset-admin-password`): pasos 9.2 y
9.3 de `GUIA-VPS.md`.

## 4. HTTPS y proxy

- **Caddy (recomendado):** `docs/despliegue/Caddyfile`. Obtiene y renueva el certificado solo. `sudo systemctl reload caddy`.
- **nginx + certbot:** `docs/despliegue/nginx.conf`.

En los dos, `/tiles/` (el mapa base) va sin compresión ni búfer, porque el navegador lo lee por rangos.

## 5. Servicio con reinicio automático

```bash
sudo cp docs/despliegue/worldives.service /etc/systemd/system/
sudo systemctl daemon-reload && sudo systemctl enable --now worldives
journalctl -u worldives -f          # registro
```

## 6. Entorno de pruebas separado

Otra carpeta (`/opt/worldives-pruebas`) con el **mismo zip de PRODUCCIÓN**, otro usuario, otra base, otro `.env` (`WOD_PORT=8001`, claves propias, **claves de prueba de Stripe**) y otro servicio (`docs/despliegue/worldives-pruebas.service`), en `pruebas.worldivesdiscovery.com` con contraseña (bloque del `Caddyfile`). El paquete DEMO nunca va al servidor real: el servidor se niega a arrancar con `WOD_DEMO_MODE=1` en `worldivesdiscovery.com` y en cualquiera de sus subdominios (v50.52). **Nunca se prueba con la base real**: para reproducir algo, se restaura una copia en pruebas y se anonimiza.

## 7. Copias de seguridad

Automáticas, sin cron:

| Qué | Cuándo | Dónde |
|---|---|---|
| Base de datos (API de copia de SQLite, consistente con la web funcionando, comprobada con `quick_check` y comprimida) | Cada hora (`WOD_BACKUP_DB_MINUTES`) | `WOD_BACKUP_DIR/db/` |
| Fotos subidas y documentos privados (`.tar.gz`) | Cada día | `WOD_BACKUP_DIR/files/` |
| Copia fuera del servidor | Tras cada copia | `WOD_BACKUP_COMMAND` (ejemplo con rclone en `scripts/copia_externa.sh`) |
| `PRAGMA quick_check` de la base en uso | Cada día | Aviso por email si falla |

**Rotación:** se guardan las últimas 48 copias horarias, una por día durante 30 días y una por mes durante 12 meses (`WOD_BACKUP_KEEP_*`). Si una copia o su envío fuera falla, los administradores reciben un email (máximo uno al día por motivo) y queda en *Administración → Operación*.

**Destino externo recomendado:** un almacenamiento en la UE con versiones o bloqueo de objetos (Backblaze B2 en Ámsterdam, Hetzner Storage Box, Scaleway…). Las copias contienen datos personales: cifra el destino (por ejemplo, un remoto `crypt` de rclone) y limita quién tiene acceso.

**Cifrado (v50.51):** con `WOD_BACKUP_KEY` en el `.env`, cada copia se guarda cifrada (AES-256-GCM). `--verify-backup`
y `--restore` la descifran solos con esa clave. Guárdala también fuera del servidor: sin ella no se puede restaurar.

**Copia manual:** `python app/server.py --backup-now`.

### Restaurar (y prueba de restauración)

Haz la prueba **una vez al mes en el entorno de pruebas**:

```bash
# 1. Comprobar una copia sin tocar nada
python app/server.py --verify-backup /var/backups/worldives/db/worldives-20261012-0300.sqlite3.gz
#    → «ok · N tablas» (integrity_check correcto)
# 2. Restaurar (con el servicio parado). La base actual se guarda al lado con «.antes-de-restaurar-…»
sudo systemctl stop worldives
sudo -u worldives .venv/bin/python app/server.py --restore /var/backups/worldives/db/worldives-20261012-0300.sqlite3.gz --yes
tar -xzf /var/backups/worldives/files/archivos-20261012-0300.tar.gz -C /tmp/restaurar   # fotos y documentos
sudo systemctl start worldives
# 3. Comprobar: entrar como admin, abrir una reserva y un documento, y mirar Administración → Operación.
```

Anota en la lista de lanzamiento la fecha de la última prueba de restauración.

## 8. Monitorización y avisos

- **Monitor externo**: Better Stack (región UE) contra `https://worldivesdiscovery.com/api/health` cada 3 minutos, con aviso por correo, junto con los registros y las alertas (`GUIA-VPS.md`, paso 11).
- **Errores 500 repetidos:** si hay 5 en 10 minutos (`WOD_ALERT_ERRORS`, `WOD_ALERT_WINDOW_MIN`), se envía un email a los administradores (como mucho uno por hora).
- **Administración → Operación:** versión, tiempo en marcha, integridad de la base, últimas copias, cola de correos, errores recientes, disco libre y ajustes pendientes.
- **Aviso de mantenimiento o incidencia:** en *Administración → Operación* se publica un texto que aparece arriba en toda la web durante las horas que elijas. Opcionalmente se envía un email a todos los centros y profesionales.

### Actualizar a una versión nueva

Con el zip nuevo, como explica `docs/despliegue/GUIA-VPS.md`, apartado 9 (copia antes, sin tocar `data/`, `storage/` ni
`.env`, y con la carpeta anterior guardada para volver atrás).

Las migraciones solo añaden y transforman, sin borrar datos; las que reescriben una tabla o textos guardan antes una copia completa de la base. Además, haz `--backup-now` antes de cada actualización, como arriba.

## 9. Rendimiento y cuándo pasar a PostgreSQL

**Prueba de carga** (`scripts/herramientas/prueba_carga.py`): visitantes simultáneos que navegan por la portada, el mapa, el directorio de centros, la lista de puntos y las fichas. **Repítela en el servidor real** (en el entorno de pruebas, con la misma máquina):

```bash
python3 scripts/herramientas/prueba_carga.py --url https://pruebas.worldivesdiscovery.com --users 100 --seconds 60
```

Resultados de referencia, medidos en una máquina de 4 núcleos con el cliente en la misma máquina (orientativos; el servidor real dará otras cifras):

| Configuración | Visitantes simultáneos | Peticiones/s | Mediana | p95 | Errores |
|---|---|---|---|---|---|
| 1 proceso (`WOD_WORKERS=1`) | 50 | 96 | 5 ms | 13 ms | 0 |
| 1 proceso | 200 | 175 | ~500 ms | ~1,2 s | 0 |
| 4 procesos (`WOD_WORKERS=4`) | 50 | 96 | 4 ms | 9 ms | 0 |
| 4 procesos | 200 | 390 | 5 ms | 15 ms | 0 |

Con 1 proceso la web va sobrada hasta unos 50 visitantes navegando a la vez. Por encima, el procesador se satura y conviene **`WOD_WORKERS` = número de núcleos**: con 4 procesos, 200 visitantes simultáneos responden en milisegundos. Como referencia, 200 visitantes a la vez equivalen a varios miles de visitas al día.

Los procesos comparten las sesiones (en la base de datos) y los límites de intentos (en `data/<base>-limites.sqlite3`, junto a la base). Ese archivo solo guarda contadores de los últimos minutos: no hace falta copiarlo y se puede borrar con el servidor parado.

**Cuándo migrar a PostgreSQL.** SQLite en modo WAL admite muchas lecturas simultáneas, pero **una sola escritura a la vez**. Las escrituras de WORLDIVES son pocas y cortas (reservas, pagos, inicios de sesión, estadísticas). Conviene empezar a preparar la migración cuando se cumpla **cualquiera** de estas condiciones de forma sostenida:

- más de **50 escrituras por segundo** en hora punta (equivale a unas **20 000 reservas o solicitudes al día**), o errores «database is locked» en el registro;
- la base supera **10 GB**, o las copias horarias tardan más de un minuto;
- hace falta **más de un servidor** de aplicación (alta disponibilidad o varias regiones), porque SQLite es un archivo local;
- se necesitan **informes pesados** en paralelo con el tráfico.

Hasta entonces, SQLite es más simple, más rápido y más barato de operar. El código usa SQL estándar casi en todo; la migración consistiría en un adaptador de conexión, cambiar `INSERT … ON CONFLICT` y las funciones propias (`fold`), y un volcado de datos.


## 10. Correo electrónico

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

Todas las plantillas se pueden ver con datos de ejemplo en *Administración → Correos*, en los 9 idiomas de la web.
