# Guía de operación

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

Tareas del titular o del administrador para mantener WORLDIVES DISCOVERY en marcha. Todo lo que aquí se cita existe en el código (`app/server.py`, `public/assets/js/world-dives-v8.js`, `tools/`). Si algo no existe, se dice.

Los comandos suponen la instalación de `docs/despliegue.md`:

- carpeta `/opt/worldives`;
- usuario `worldives`;
- servicio `worldives`;
- copias en `/var/backups/worldives`.

Prefijo de los comandos de la aplicación:

```bash
cd /opt/worldives && sudo -u worldives .venv/bin/python app/server.py …
```

---

## 1. Mapa de Administración

Entra en `#/admin` con tu cuenta de administración. La verificación en dos pasos es obligatoria: sin ella, el servidor no deja usar las funciones de administración (`admin_totp_required()`).

| Pestaña | Para qué | Rutas principales |
|---|---|---|
| **Inicio** | Resumen y accesos | — |
| **Verificaciones** | Aprobar o rechazar centros y freelance (ver `guia-verificacion-centros.md`) | `/api/admin/center-claims`, `/api/admin/center-claims/review` |
| **Usuarios** | Lista de cuentas y cambio de rol (cierra sus sesiones) | `/api/admin/users`, `/api/admin/users/role` |
| **Centros** | Fichas de centros | `/api/admin/centers`, `/api/centers/update` |
| **Puntos** y **Correcciones** | Puntos propuestos por usuarios y correcciones de posición | `/api/admin/dive-points/review`, `/api/admin/suggestions/review` |
| **Descripciones de puntos** | Revisar los textos propios de los puntos y completar los datos que faltan | `/api/admin/point-texts`, `/api/admin/point-texts/review` |
| **Reservas** | Ver reservas | — |
| **Pagos** | Ver cobros y devoluciones, marcar incidencias y resolver pagos «en revisión». **No mueve dinero** | `/api/admin/payments`, `/api/admin/payments/incident`, `/api/admin/payments/resolve` |
| **Correos** | Registro de envíos, reenviar, correo de prueba, vista previa de plantillas y comunicación comercial | `/api/admin/emails`, `/api/admin/emails/resend`, `/api/admin/emails/test`, `/api/admin/email-preview`, `/api/admin/marketing/send` |
| **Legal** | Datos del titular, documentos legales con versiones, **denuncias**, plazos de conservación | `/api/admin/legal`, `/api/admin/legal/publish`, `/api/admin/reports/resolve`, `/api/admin/retention` |
| **Mapas** | Tamaño del PMTiles, contador y límite de teselas satélite | `/api/admin/maps` |
| **Planes** | Planes, precios, prueba gratuita, asignación manual, excepciones, pagos de cuotas e **informe DAC7** | `/api/admin/plans*`, `/api/admin/dac7` |
| **Funciones** | Interruptores (Puntos, Promociones, Experiencias, Patrocinio, Reseñas, Pagos online), modo piloto e invitaciones | `/api/admin/features`, `/api/admin/invites` |
| **Operación** | Estado del servidor, copias, cola de correos, errores, disco, avisos de configuración y **banner** | `/api/admin/health`, `/api/admin/banner` |
| **Imágenes de la web** (medios) | Portada, temas y origen o licencia de cada imagen | `/api/admin/site-media`, `/api/admin/images` |
| **Patrocinio** | Publicaciones patrocinadas (etiqueta fija «Patrocinado»), patrocinadores y mínimo de «Centros asociados» | `/api/admin/site-promos*` |
| **Recorridos virtuales**, **Experiencias**, **Destinos**, **Recompensas**, **QR** | Contenido | — |
| **Actividad** | Registro de auditoría (`audit_log`) | `/api/admin/audit` |

---

## 2. Tareas por frecuencia

### Cada día (5–10 minutos)

- [ ] **Operación.** Comprueba:
  - `quick_check` = ok;
  - última copia de la base de menos de 2 h y de los archivos de menos de 26 h;
  - sin errores recientes;
  - disco libre por encima del 20 %;
  - sin avisos de configuración nuevos.
- [ ] **Correo del administrador.** Lee las alertas automáticas (`ops_alert`, como mucho una al día por motivo): copia fallida, copia externa fallida, `quick_check` fallido, errores 500 repetidos (5 en 10 min), cuota del satélite al 80 %.
- [ ] **Verificaciones.** Atiende las solicitudes pendientes. Llega un correo `admin_new_pro` por cada una.
- [ ] **Legal → Denuncias de contenido.** Resuelve las abiertas (sección 6).
- [ ] **Pagos.** Mira el filtro de incidencias (`status=incident`) y los pagos en estado `review` (importe o moneda que no cuadra): acéptalos o márcalos para devolución.

### Cada semana

- [ ] **Correos.** Ningún envío en `failed`. Reenvía los que hagan falta y revisa el último error (credenciales SMTP, dominio, rebotes).
- [ ] **Pagos.**
  - Devoluciones propuestas sin hacer: el servidor recuerda al centro a las 72 h (`run_refund_reminders()`).
  - Disputas abiertas (`charge.dispute.created` las marca solas).
- [ ] **Descripciones de puntos.** Avanza en la revisión (marcar «revisada» y completar «Datos que faltan»).
- [ ] **Puntos y Correcciones.** Revisa las propuestas de usuarios y centros.
- [ ] **Planes.** Prestadores con datos fiscales incompletos (`fiscal_missing`) y planes que caducan pronto.
- [ ] **Actividad.** Repasa el registro de auditoría en busca de cosas raras: muchos `document_access_denied`, cambios de rol, exportaciones DAC7.

### Cada mes

- [ ] **Prueba de restauración** en el entorno de pruebas (sección 4.3). Anota la fecha en `docs/legal/lista-lanzamiento.md`.
- [ ] **Mapas.** Contador de teselas satélite frente al límite (1 900 000 por defecto) y a la cuota del plan de ArcGIS.
- [ ] **Legal → Plazos de conservación.** Mira el último informe de la tarea diaria (`retention_last_report`): avisados, cuentas borradas, documentos borrados, avisos y registros eliminados.
- [ ] **Imágenes de la web.** El informe no debe tener imágenes «sin origen».
- [ ] **Sistema.** `sudo apt update && sudo apt upgrade` (si no hay actualizaciones automáticas) y revisión del espacio de `/var/backups/worldives` y del destino externo.
- [ ] El día 1, los centros reciben su email mensual de estadísticas (`run_monthly_stats_emails()`). Comprueba en *Correos* que salió.

### Cada trimestre

- [ ] Actualizar el mapa base PMTiles (`docs/mapas.md` §1). Se sustituye con `mv` y no hace falta reiniciar.
- [ ] Revisar las invitaciones del piloto caducadas o sin usar (*Funciones*).
- [ ] Revisar los textos legales por si hay cambios normativos **[PENDIENTE ABOGADO]**.

### Cada año

- [ ] **Enero: informe DAC7** (sección 9).
- [ ] Revisar los precios de los planes **[PENDIENTE TITULAR]** y el IVA de la cuota **[PENDIENTE GESTORÍA]**.
- [ ] Revisar el registro de actividades de tratamiento y los encargados (Stripe, SMTP, VPS, copia externa, ArcGIS).

---

## 3. Incidencias del servicio

### 3.1 Avisar con el banner y por email

1. *Administración → Operación → Aviso*. Datos del aviso:
   - **texto** (máximo 300 caracteres);
   - **nivel**: `info`, `maintenance` (mantenimiento programado) o `incident` (incidencia en el servicio);
   - **horas** que estará visible (de 1 a 336).
2. Opcional: marca «avisar a los centros». Se envía un email a todas las cuentas `center` y `freelance` en su idioma (`/api/admin/banner` con `notify_centers`).
3. El banner aparece arriba en toda la web hasta la hora fijada (`site_banner()`). Para quitarlo antes, guarda el aviso con el texto vacío.
4. Todo queda en `audit_log` (`site_banner_set` o `site_banner_removed`).

### 3.2 Si la web no responde

```bash
sudo systemctl status worldives
journalctl -u worldives -n 200 --no-pager
curl -s https://<dominio>/api/health          # {"ok": true, "version": "50.38"}
df -h /opt/worldives /var/backups/worldives
sudo systemctl restart worldives
```

- Registro de accesos: `logs/access.log` (`WOD_LOG_DIR`). Rota cada día y se guardan 14 días (`WOD_LOG_RETENTION_DAYS`), con la IP truncada y sin *query string*.
- Si aparece «No se puede arrancar en producción», el mensaje dice qué variable falta en `.env` (`check_production_settings()`).
- Si la base está dañada (`quick_check` distinto de `ok`): para el servicio y restaura la última copia buena (sección 4.2).
- **Posible brecha de datos** (acceso indebido, copia expuesta, robo de credenciales): sigue `docs/legal/procedimiento-brechas.md`. El plazo de notificación a la AEPD es de **72 h**.

---

## 4. Copias de seguridad

### 4.1 Automáticas (sin cron)

La tarea `run_backup_jobs()` (cada minuto, dentro del proceso principal) hace:

- **base de datos** cada `WOD_BACKUP_DB_MINUTES` (60), en `WOD_BACKUP_DIR/db/`, comprimida y comprobada;
- **fotos y documentos privados** una vez al día, en `WOD_BACKUP_DIR/files/` (`.tar.gz`);
- **copia externa** después de cada copia, con `WOD_BACKUP_COMMAND` (por ejemplo `deploy/backup-externo.sh` con rclone);
- **rotación**: 48 copias horarias, una diaria durante 30 días y una mensual durante 12 meses (`WOD_BACKUP_KEEP_*`);
- **`PRAGMA quick_check`** diario de la base en uso.

Si algo falla, llega un email al administrador y se ve en *Operación*.

### 4.2 Comandos

```bash
# Copia manual inmediata (antes de cada actualización o cambio delicado)
sudo -u worldives .venv/bin/python app/server.py --backup-now

# Comprobar una copia sin tocar nada → «ok · N tablas»
sudo -u worldives .venv/bin/python app/server.py --verify-backup /var/backups/worldives/db/<archivo>.sqlite3.gz

# Restaurar (con el servicio parado). La base actual se guarda al lado con «.antes-de-restaurar-…»
sudo systemctl stop worldives
sudo -u worldives .venv/bin/python app/server.py --restore /var/backups/worldives/db/<archivo>.sqlite3.gz --yes
sudo -u worldives tar -xzf /var/backups/worldives/files/<archivo>.tar.gz -C <carpeta temporal>   # fotos y documentos, si hacen falta
sudo systemctl start worldives
```

Sin `--yes`, `--restore` solo comprueba la copia y no restaura nada.

### 4.3 Prueba de restauración mensual

En el **entorno de pruebas**, nunca en producción:

1. Copia a pruebas la última copia horaria y el último `.tar.gz`.
2. `--verify-backup` sobre la copia.
3. Para `worldives-pruebas`, ejecuta `--restore … --yes` con el `.env` de pruebas y descomprime los archivos en su carpeta.
4. Arranca y comprueba:
   - entrar como admin;
   - abrir una reserva y su justificante PDF;
   - abrir un documento privado;
   - *Operación* sin errores.
5. Como la copia tiene datos reales, **anonimízala o bórrala** al acabar. Las pruebas nunca se hacen con la base real en uso.
6. Anota la fecha y el resultado.

---

## 5. Actualizar la aplicación

```bash
cd /opt/worldives
sudo -u worldives .venv/bin/python app/server.py --backup-now
sudo -u worldives git pull
sudo -u worldives .venv/bin/pip install -r requirements.txt
sudo systemctl restart worldives            # las migraciones se aplican solas al arrancar
journalctl -u worldives -n 50 --no-pager    # sin errores; anota los «Aviso:» de configuración
```

- Antes, prueba la versión nueva en el entorno de pruebas y ejecuta la suite: `python3 -m unittest discover -s tests -p 'test_*.py'`.
- Las migraciones (`migrate_v50_*`, tabla `schema_migrations`) solo añaden y transforman. Las que reescriben tablas guardan antes una copia completa en `data/backups/`.
- Para cambios largos, publica antes un banner `maintenance` (sección 3.1).
- Comprueba la versión en *Operación* o en `/api/health`.

---

## 6. Denuncias de contenido

- Entrada: botón «Denunciar contenido» en reseñas, centros, puntos, experiencias, fotos, promociones y perfiles (POST `/api/reports`, tabla `content_reports`, con límite por IP), y la página `#/legal/denuncias`.
- Gestión: *Administración → Legal → Denuncias de contenido*. Para cada una:
  1. Abre el contenido denunciado y compáralo con las normas (`#/legal/normas-resenas`, condiciones).
  2. Si hay que retirarlo:
     - para una reseña, ocúltala con motivo (moderación con `moderation_reason`, obligatorio);
     - para otro contenido, desactívalo desde su pestaña.
  3. Resuelve la denuncia como `actioned` (se actuó) o `dismissed` (desestimada), con una **resolución escrita** (`/api/admin/reports/resolve`). El servidor avisa por email a quien denunció y, si lo hay, al afectado.
- **[PENDIENTE ABOGADO]**: plazos de respuesta y vía de recurso según el Reglamento de Servicios Digitales.

---

## 7. Solicitudes de protección de datos (RGPD)

| Derecho | Cómo se atiende | Dónde está |
|---|---|---|
| **Acceso y portabilidad** | La persona lo descarga ella misma en *Mi cuenta → Descargar mis datos*: un ZIP con todos sus datos en JSON y sus documentos | `/api/account/export?format=zip` (`export_user_zip`, `export_user_data`) |
| **Rectificación** | La persona edita su perfil y su email (con verificación del nuevo email) | `/api/account/profile`, `/api/account/email` |
| **Supresión (buceador)** | *Mi cuenta → Eliminar mi cuenta*: pide la contraseña y envía un **enlace de confirmación por email** (24 h, un solo uso). No se puede con reservas futuras pendientes o confirmadas | `/api/account/delete`, `/api/account/delete/confirm`, `delete_user_account()` |
| **Oposición a comunicaciones comerciales** | Enlace de baja en un clic en cada correo comercial, o casilla en *Mi cuenta* | `/api/marketing/unsubscribe`, `consent_log` |
| **Retirar el acceso de un centro** | *Mi cuenta → Centros que ven tu ficha → Revocar* | `/api/account/shares/revoke` |

Qué hace la supresión:

- borra los documentos (también los archivos), el perfil, el Log Book, las sesiones y los avisos;
- anonimiza la cuenta («Usuario eliminado»);
- conserva las reservas y los pagos anonimizados, por las obligaciones fiscales del centro;
- deja las reseñas sin nombre del autor.

Cuando la petición llega por email al buzón de protección de datos:

1. **Identifica** a la persona: que escriba desde el email de la cuenta, o confírmalo respondiendo a ese email.
2. Si tiene cuenta y puede entrar, indícale el autoservicio de la tabla.
3. Si **no puede entrar**: en Administración **no hay** botón para exportar ni borrar los datos de otra persona. Las opciones son:
   - ayudarle a recuperar el acceso (`#/recuperar`, enlace de 1 h);
   - o hacerlo a mano en el servidor con la base, dejando constancia **[PENDIENTE TITULAR]**: decidir si se añade esa herramienta.
4. **Cuentas de centro, freelance o administración:** no pueden borrarse ellas mismas («se dan de baja escribiéndonos»). Procedimiento actual:
   1. el centro exporta sus datos (*Panel → «Exportar, calendario, widget»*: clientes, reservas, servicios y pagos en CSV, `/api/center/export`, disponible en todos los planes);
   2. se atienden o cancelan sus reservas futuras;
   3. el admin cambia la cuenta a `recreational` en *Usuarios*;
   4. la persona borra su cuenta desde *Mi cuenta*.

   La ficha del centro se desactiva desde *Centros*. No hay borrado automático de la ficha ni de sus datos fiscales **[PENDIENTE ABOGADO]**: plazo de conservación de los datos del centro.
5. **Personas sin cuenta** (quien envió «Solicitar información» o una denuncia): sus datos están en `info_requests` y `content_reports`. No hay herramienta en la web: se buscan y se borran a mano en la base.
6. Responde en **un mes** como máximo y guarda la petición y la respuesta.

**Conservación automática** (`run_retention_jobs()`, una vez al día; plazos en *Legal*):

- cuentas de buceador inactivas 36 meses: aviso por email y borrado 30 días después si no entran (nunca con reservas futuras);
- documentos caducados hace 12 meses;
- avisos de más de 24 meses;
- registro de actividad de más de 12 meses (se guardan siempre las últimas 300 entradas);
- las reservas y los pagos **no** se borran (6 años, obligación legal).

---

## 8. Pagos, devoluciones y disputas

**Principio:** WORLDIVES **no mueve dinero de las reservas**. Los cobros son cargos directos en la cuenta Stripe de cada centro o freelance (`stripe_account=` en cada llamada). Las devoluciones las hace **solo el prestador** (`/api/bookings/<id>/refund` desde su panel, o desde su propio panel de Stripe; la web lo registra con el webhook). La administración ve y marca incidencias.

| Situación | Qué hace el servidor | Qué haces tú |
|---|---|---|
| El buceador cancela con derecho a devolución | Propone el importe según la política copiada en la reserva (`propose_refund`). Recuerda al centro a las 72 h | Si sigue sin devolverse, marca la incidencia `refund_pending` en *Pagos* y escribe al centro. **[PENDIENTE TITULAR]**: medida adicional (por ejemplo, desactivar sus cobros online con una excepción de plan) |
| Reclamación del cliente por el servicio | Nada automático | Marca `customer_complaint` con nota y remite al cliente al centro, que presta y responde del servicio. Si procede, se acude a la vía de consumo **[PENDIENTE ABOGADO]** |
| Disputa en Stripe (contracargo) | `charge.dispute.created` marca la incidencia `dispute` y avisa al centro. `charge.dispute.closed` la marca `dispute_closed` | Seguimiento. La disputa la defiende el centro en su panel de Stripe |
| Pago «en revisión» (importe o moneda distintos) | Estado `review` | *Pagos → Resolver*: aceptar, o marcar para que el centro devuelva |
| Devolución hecha en el panel de Stripe del centro | `charge.refunded` y `refund.*` la registran sin cancelar la reserva | Nada |

Al terminar, marca la incidencia como `resolved`.

---

## 9. Planes, renovaciones y pagos manuales

- **Avisos automáticos** (`run_plan_jobs()`, cada día): email al prestador a 30, 7 y 1 días del fin del plan o de la prueba, y al terminar (`plan_expired`). Al terminar pasa a ficha gratuita: sin reservas online nuevas, con «Solicitar información», las reservas existentes se mantienen y la exportación sigue disponible.
- **Pago con tarjeta:** el prestador paga desde *Mi plan* (`/api/provider/plan/checkout`). Es un Checkout en la cuenta de la **plataforma**. El webhook `/api/payments/webhook` (`kind=plan_fee`) activa el plan 12 meses. Si renueva el mismo plan antes de que termine, los meses se suman desde la fecha de fin (`set_provider_plan()`).
- **Pago manual** (transferencia, acuerdo): *Administración → Planes → Asignar plan*. Datos:
  - plan;
  - meses (de 1 a 36);
  - importe;
  - **nota obligatoria** (por ejemplo: «transferencia del 12/10, ref. …»).

  Queda en `plan_payments` con `method='manual'`. Para pasar a alguien a ficha gratuita, asigna `free`, también con nota.
- **Excepciones:** activar o desactivar una función concreta a un prestador, con motivo obligatorio. Se registra el alta y la baja (`plan_exceptions`).
- **Facturas de la cuota:** la web **no emite facturas**, solo registra el pago. Emítelas con el programa de facturación que indique la gestoría (Verifactu) **[PENDIENTE GESTORÍA]**.

---

## 10. Informe DAC7 (enero)

1. *Administración → Planes → Informe DAC7*. Elige el año (por defecto, el anterior) y descarga el CSV (`/api/admin/dac7?format=csv&year=AAAA`).
2. El CSV tiene una fila por prestador con cobros online en el año. Columnas:
   - identificación (razón social, persona física o jurídica, NIF/TIN, país, registro o fecha de nacimiento, dirección);
   - cuenta de cobro;
   - importes y número de actividades por trimestre (cobros menos devoluciones);
   - comisiones (siempre 0) e impuestos retenidos (0);
   - `datos_incompletos`.
3. Antes del plazo, escribe a los prestadores con `datos_incompletos` para que completen *Datos fiscales y seguro*.
4. Entrega el CSV a la gestoría para el **modelo 238** (plazo de enero) **[PENDIENTE GESTORÍA]**: confirmar si WORLDIVES está obligado, porque los cobros son cargos directos en la cuenta del centro.
5. Cada exportación queda en `audit_log` (`dac7_exported`). Guarda el CSV fuera del servidor con acceso limitado: tiene datos fiscales.

---

## 11. Publicar un cambio legal

1. Prepara el texto con el abogado.
2. *Administración → Legal → Documentos legales*: elige el documento, edita el Markdown y mira la **vista previa**. Pon:
   - un **resumen del cambio**, que va en el email;
   - la **fecha de entrada en vigor**.
3. Reglas del servidor (`legal_publish()`):
   - la fecha no puede ser anterior a hoy;
   - **condiciones para centros** (`centros`): como pronto **15 días** después de hoy (`LEGAL_NOTICE_DAYS`); si no, el servidor lo rechaza;
   - el castellano es la referencia: su versión es la fecha de entrada en vigor;
   - publica después la **traducción inglesa** (también oficial); hereda la versión del castellano.
4. Si el documento es de aceptación obligatoria (`terminos`, `privacidad`: todos; `centros`: centros y freelance), al publicar en castellano se envía el email `legal_update` a cada persona afectada, en su idioma.
5. Cuando la versión entra en vigor, la web pide aceptarla al entrar (`legal_pending_for()`, `/api/legal/accept`). Cada aceptación queda en `legal_acceptances`. A los centros les aparece además una banda de aviso en el panel durante el preaviso.
6. El historial público de versiones está en cada página legal (`/api/legal/history`).
7. Los datos del titular (`{{owner_name}}`, `{{nif}}`…) se cambian en *Legal → Datos del titular* sin publicar una versión nueva del texto.

---

## 12. Otras tareas

- **Comunicación comercial:** *Correos → Comunicación comercial*. Se envía primero como prueba al administrador. Solo llega a quien dio su consentimiento y tiene el email verificado, con baja en un clic.
- **Funciones:** desactivar una función (por ejemplo, Reseñas) la oculta en la web y el servidor rechaza su uso. Los datos se conservan.
- **Modo piloto:** con él activo, el alta profesional es solo con código de invitación (*Funciones → Invitaciones para el piloto*).
- **Cuota del satélite:** al 80 % llega un email (`admin_map_quota`). Al llegar al límite, la capa se oculta hasta el mes siguiente. El límite se cambia en *Mapas*.
- **Herramientas** (en el servidor, con el usuario `worldives`):

  | Herramienta | Para qué |
  |---|---|
  | `python app/server.py --create-admin` | Crear otro administrador. Al entrar debe activar TOTP |
  | `python app/server.py --report-center-accounts` | Informe de cuentas de centro y sus solicitudes |
  | `python3 tools/crear_base_produccion.py --source … --out …` | Solo para una instalación nueva |
  | `python3 tools/demo_centros_ficticios.py <base> --yes` | Solo para la demo |
  | `python3 tools/puntos_reescritos.py <base> > docs/legal/puntos-reescritos.md` | Regenerar la lista de descripciones reescritas |
  | `python3 tools/prueba_carga.py --url https://pruebas.<dominio> --users 100 --seconds 60` | Prueba de carga, siempre contra pruebas |
  | `tools/i18n_*.py` | Traducciones |

---

## 13. Huecos detectados para la operación

- **[PENDIENTE TITULAR]** No hay herramienta de administración para exportar o borrar los datos de otra persona, ni para dar de baja una cuenta de centro o freelance.
- **[PENDIENTE TITULAR]** No hay pantalla con los datos fiscales y el certificado de seguro de un centro (solo CSV de DAC7 y `/api/admin/insurance-doc?type=…&id=…`).
- **[PENDIENTE TITULAR]** El rechazo de una verificación no envía correo: hay que escribir a mano.
- El editor de centros del admin carga teselas de `tile.openstreetmap.org` también en producción (ver `inventario.md`).
