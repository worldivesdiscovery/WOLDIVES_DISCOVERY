# Procedimiento de gestión de brechas de seguridad

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

Qué hacer si se pierden, se filtran, se alteran o quedan inaccesibles datos personales de WORLDIVES (arts. 33 y 34 RGPD). Se basa en las herramientas que **ya existen en el código**.

**Regla de oro:** ante la duda, se abre la brecha en el registro y se empieza a contar el plazo. Las 72 horas para avisar a la AEPD cuentan **desde que tenemos constancia**, no desde que sabemos todo.

## 1. Quién hace qué

| Papel | Quién | Qué hace |
|---|---|---|
| **Responsable de la brecha** | El titular ({{owner_name}}) | Decide, firma las notificaciones, habla con la AEPD, los afectados y los centros |
| **Técnico** | La persona que administra el servidor | Detecta, contiene, investiga, restaura y documenta lo técnico |
| **Asesor** | Abogado **[pendiente de designar]** | Valora el riesgo y revisa las notificaciones |
| Contactos | [pendiente de completar: teléfonos y emails de los tres, y del proveedor de hosting {{hosting}}] | |

Si titular y técnico son la misma persona, lo hace todo ella, pero **siempre** rellena el registro.

## 2. Cómo nos enteramos (fuentes que existen en el código)

| Fuente | Qué avisa | Dónde |
|---|---|---|
| **Alerta de errores 500** | 5 errores internos en 10 minutos (`WOD_ALERT_ERRORS`, `WOD_ALERT_WINDOW_MIN`). Email `admin_error_alert` a los administradores, como mucho uno por hora | `ErrorMonitor` en `app/wod/ops.py`; `_alert_errors()` en `app/server.py` |
| **Avisos de operación** | Copia de la base fallida, copia de archivos fallida, copia externa fallida, la base no supera `PRAGMA quick_check`. Email `admin_ops_alert`, uno al día por asunto | `ops_alert()` y `run_backup_jobs()` |
| **Administración → Operación** | Versión, integridad, últimas copias, cola de correos, errores recientes, disco libre, avisos de configuración | `admin_health()` |
| **Registro de actividad** | Inicios de sesión (`login`, con `ip_hash`), fallos de TOTP (`totp_failed`), descargas y denegaciones de documentos (`document_downloaded`, `document_access_denied`), cambios de rol, exportaciones (`provider_export`, `dac7_exported`), importaciones (`clients_imported`), eliminaciones de cuenta | Tabla `audit_log`; *Administración → Registro* (`/api/admin/audit`, últimas 300) |
| **Registro de accesos** | Peticiones con IP truncada (/24 o /48), sin cadena de consulta; 14 días | `logs/access.log` (`access_logger()`); o el journal de systemd si `WOD_ACCESS_LOG=stdout` |
| **Monitor externo** | La web no responde | `/api/health` (UptimeRobot, Better Stack…; `docs/despliegue.md`, apartado 8) |
| **Personas** | Un usuario, un centro, Stripe, el proveedor de hosting o de correo, un investigador de seguridad | {{email}}, {{dpo_email}} |

Limitaciones a tener en cuenta:

- No hay alerta automática por **accesos anómalos** (muchas descargas de documentos, muchos inicios de sesión fallidos). Se revisan a mano en `audit_log`.
- Los límites de intentos guardan sus contadores **en memoria** y se pierden al reiniciar.
- El registro de accesos guarda la IP truncada: sirve para ver patrones, no para identificar a una persona.
- `audit_log` se purga a los **12 meses** (salvo las últimas 300 entradas). Si hay una brecha, **exporta antes el registro** (paso 2).

## 3. Paso a paso

### Paso 1 · Abrir la brecha (hora 0)

- Anota en el **registro de brechas** (apartado 4) la fecha y hora de detección y quién la detecta.
- Avisa al titular. Desde aquí corren las **72 horas**.

### Paso 2 · Conservar las pruebas (primera hora)

Antes de tocar nada:

```bash
# Copia de la base en este momento (comprobada)
python app/server.py --backup-now
# Registro de actividad completo
sqlite3 data/worldives.sqlite3 ".mode csv" ".headers on" "SELECT * FROM audit_log" > /root/brecha-AAAAMMDD/audit_log.csv
# Registros de accesos
cp -a logs/ /root/brecha-AAAAMMDD/logs/
```

(Ajusta la ruta de la base si usas `WOD_DB_PATH`.) Guarda las pruebas fuera de la carpeta de la web y con permisos restringidos.

### Paso 3 · Contener

Elige las acciones que correspondan (detalle en el apartado 7):

- cerrar sesiones, cambiar contraseñas o claves;
- desactivar la función afectada;
- cerrar el registro de cuentas;
- publicar el aviso de incidencia;
- si el servidor está comprometido, **pararlo** y restaurar en limpio.

### Paso 4 · Evaluar (antes de 48 h)

Responde por escrito en el registro:

1. **Qué datos:** tablas y campos afectados (usa `docs/legal/registro-actividades-tratamiento.md`). ¿Hay documentos de identidad, seguros, datos fiscales, fechas de nacimiento, contactos de emergencia, contraseñas (son hash PBKDF2), secretos TOTP (sin cifrar), tokens?
2. **De quién y cuántos:** buceadores, centros, clientes de centros (fichas con `guest_center_id`), personal de los centros. Número aproximado.
3. **Tipo:** confidencialidad (alguien accedió), integridad (se alteró), disponibilidad (se perdió o no se puede usar).
4. **Papel de WORLDIVES:** responsable (sus usuarios) o **encargado** (fichas de cliente y reservas que gestiona un centro; ver el anexo de encargo). Puede ser ambas cosas a la vez.
5. **Riesgo para las personas:** sin riesgo / riesgo / **alto riesgo** (suplantación, fraude, daño reputacional, datos de documentos de identidad…). Herramienta de ayuda: «Asesora Brecha» de la AEPD **[comprobar que sigue disponible]**.

### Paso 5 · Notificar

| Situación | A quién | Plazo | Quién |
|---|---|---|---|
| Cualquier brecha | **Registro interno** | Siempre | Técnico |
| WORLDIVES responsable y **probable riesgo** | **AEPD** (sede electrónica, formulario de notificación de brechas) | **72 h** desde la detección. Si falta información, se notifica lo que se sepa y se completa después | Titular |
| WORLDIVES responsable y **alto riesgo** | **Personas afectadas** | Sin dilación indebida | Titular |
| WORLDIVES **encargado** (datos de clientes de un centro) | **El centro afectado** (responsable). Él decide si notifica a la AEPD y a sus clientes | Sin dilación indebida; compromiso **[48 h — PENDIENTE TITULAR]** (anexo de encargo, cláusula 12) | Titular |
| Afecta a pagos o a claves de Stripe | Stripe (soporte) | En cuanto se sepa | Técnico |
| Afecta al hosting o al correo | Proveedor afectado | En cuanto se sepa | Técnico |
| Posible delito | Policía Nacional / Guardia Civil; INCIBE-CERT para apoyo técnico | Según el caso | Titular |

No hace falta avisar a las personas afectadas si los datos eran ininteligibles para terceros, si las medidas tomadas eliminan el alto riesgo o si exigiría un esfuerzo desproporcionado (en ese caso, aviso público). **[PENDIENTE ABOGADO]** en cada caso.

Si el incidente afecta al servicio, publica además el **aviso de incidencia** en la web y, si procede, el email a centros (apartado 7).

### Paso 6 · Cerrar

- Corrige la causa y comprueba que no se repite.
- Anota en el registro las medidas, las notificaciones hechas (con fecha y hora) y la fecha de cierre.
- Revisa este procedimiento si algo no ha funcionado.

## 4. Registro de brechas (plantilla)

El art. 33.5 RGPD obliga a documentar **todas** las brechas, también las que no se notifican. Lleva este registro **fuera del servidor** (por ejemplo, en una hoja privada del titular).

| Campo | Contenido |
|---|---|
| Nº | BR-AAAA-NN |
| Detectada | Fecha y hora; quién; cómo (fuente del apartado 2) |
| Ocurrió | Fecha y hora estimadas de inicio y fin |
| Descripción | Qué pasó, en pocas líneas |
| Tipo | Confidencialidad / integridad / disponibilidad |
| Datos afectados | Tablas, campos y archivos |
| Personas afectadas | Categorías y número aproximado |
| Registros afectados | Número aproximado |
| Papel de WORLDIVES | Responsable / encargado (qué centros) |
| Riesgo | Sin riesgo / riesgo / alto riesgo, con el motivo |
| Contención | Acciones y hora |
| AEPD | Notificada sí/no; fecha y hora; número de registro; motivo si no |
| Afectados | Avisados sí/no; fecha; medio; motivo si no |
| Centros | Avisados sí/no; cuáles; fecha |
| Otros | Stripe, hosting, correo, policía |
| Medidas correctoras | Qué se cambia para que no se repita |
| Cerrada | Fecha; responsable |

## 5. Datos para la notificación a la AEPD

Contenido mínimo del art. 33.3 RGPD. Prepáralo en este orden:

1. **Responsable:** {{owner_name}}, NIF {{nif}}, {{address}}; contacto: {{dpo_email}} [teléfono pendiente].
2. **Notificación:** inicial / completa / ampliación de la nº ___.
3. **Cronología:** inicio, fin (o «en curso»), detección, y motivo del retraso si se notifica pasadas 72 h.
4. **Naturaleza:** tipo (confidencialidad, integridad, disponibilidad) y causa (ataque externo, error interno, pérdida, robo…).
5. **Datos:** categorías (identificativos, contacto, documentos de identidad, datos fiscales, credenciales con hash, datos de reservas y pagos sin número de tarjeta…). ¿Datos de categorías especiales? En principio no: la web no admite certificados médicos.
6. **Personas:** categorías (buceadores, clientes de centros, personal de centros, menores: no hay cuentas de menores) y número aproximado.
7. **Consecuencias probables.**
8. **Medidas tomadas y previstas**, también para mitigar efectos.
9. **Comunicación a los afectados:** hecha, prevista o no necesaria (con el motivo).
10. **Transfronterizo:** ¿hay afectados en otros Estados de la UE? (habitual: buceadores extranjeros). La AEPD es la autoridad principal si el establecimiento está en España **[PENDIENTE ABOGADO]**.

## 6. Email a las personas afectadas (plantilla)

Lenguaje claro (art. 34.2 RGPD). Se envía en el idioma de la persona (`users.preferred_language`). En castellano:

> **Asunto:** Aviso importante sobre la seguridad de tus datos en WORLDIVES
>
> Hola {nombre}:
>
> El {fecha} detectamos un incidente de seguridad que afecta a tus datos en WORLDIVES.
>
> **Qué ha pasado:** {descripción breve y comprensible}.
>
> **Qué datos tuyos están afectados:** {lista}. {Si aplica: «Tu contraseña no está afectada: la guardamos cifrada de forma que no se puede leer.»}
>
> **Qué puede pasar:** {consecuencias probables, por ejemplo correos de suplantación que pidan tus datos o un pago}.
>
> **Qué hemos hecho:** {medidas}. Lo hemos comunicado a la Agencia Española de Protección de Datos.
>
> **Qué te recomendamos:**
> - {cambia tu contraseña en WORLDIVES y en otros sitios donde uses la misma};
> - activa la verificación en dos pasos en «Mi cuenta»;
> - desconfía de mensajes que pidan datos o pagos en nombre de WORLDIVES o de tu centro: nunca te pediremos la contraseña;
> - {otras}.
>
> Para cualquier duda, escríbenos a {{dpo_email}} indicando la referencia {BR-AAAA-NN}. También puedes reclamar ante la AEPD (www.aepd.es).
>
> {{owner_name}} · {{trade_name}}

Cómo enviarlo hoy: no hay una plantilla de brecha en `app/server.py`. Opciones: el envío comercial de *Administración → Correos* **no sirve** (solo llega a quien dio consentimiento); usar el proveedor SMTP directamente con la lista extraída de la base, o añadir una plantilla de servicio **[PENDIENTE TITULAR]**.

Para avisar a un **centro** como encargado, usa el mismo esquema añadiendo: número de fichas de cliente del centro afectadas, lista de campos, y la información del apartado 5 para que pueda notificar él.

## 7. Acciones técnicas de contención disponibles

### Sesiones

- **Cerrar todas las sesiones:** con el servidor en marcha, `sqlite3 data/worldives.sqlite3 "DELETE FROM sessions;"`. Todo el mundo tiene que volver a entrar. No hay botón para esto en Administración.
- **Cerrar las sesiones de una persona:** cambiarle el rol en Administración (cierra sus sesiones) o `DELETE FROM sessions WHERE user_id=…`. Cambiar la contraseña, activar el TOTP o cambiar el email también cierra las demás sesiones.

### Rotar `WOD_SECRET_KEY`: qué hace y qué no

Comprobado en el código (`app/wod/security.py`, `secret_key()` e `ip_hash()`; `login_second_factor()`):

| Afecta | No afecta |
|---|---|
| El **hash seudónimo de IP** (`ip_hash`): las IP nuevas ya no se pueden relacionar con las guardadas en `legal_acceptances`, `consent_log`, `content_reports`, `info_requests` y `audit_log` | **Las sesiones:** se guardan como SHA-256 del token **sin clave**. Rotar la clave **no** cierra sesiones: hay que vaciar `sessions` |
| El **reto de inicio de sesión con TOTP** (válido 5 minutos): quien esté a mitad del segundo paso tiene que empezar de nuevo | Los enlaces de recuperación de contraseña, verificación de email, eliminación de cuenta e invitaciones al equipo (SHA-256 sin clave). Para anularlos: `UPDATE password_resets SET used_at=datetime('now') WHERE used_at IS NULL;` y lo mismo en `email_verifications`, `account_deletion_requests` y `team_invites` (`revoked_at`) |
| | Las contraseñas (PBKDF2 con sal propia) y los secretos TOTP |

La clave se lee una vez por proceso: hay que **reiniciar el servicio** tras cambiarla en `.env`. En producción debe tener al menos 32 caracteres (`check_production_settings()`).

### Otras claves

| Clave | Dónde se cambia | Efecto |
|---|---|---|
| `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET`, `STRIPE_CONNECT_WEBHOOK_SECRET` | Panel de Stripe y `.env` | Reiniciar. Los pagos pendientes se confirman al volver o por la revisión periódica |
| `WOD_SMTP_PASSWORD` | Panel del proveedor y `.env` | Los correos esperan en la cola mientras tanto |
| `ARCGIS_API_KEY` | Panel de Esri y `.env` | Sin clave, la vista satélite desaparece |
| Clave de la API de reservas de un centro (`center_integrations`) | El centro la regenera en su panel (`/api/center/integration`) | La anterior deja de valer |
| Token iCal de un centro (`ical_token`) | El centro lo regenera en su panel | El enlace anterior deja de valer |
| Contraseña de un administrador y su TOTP | «Mi cuenta» | — |

### Funciones y accesos

- **Administración → Funciones** (`/api/admin/features`, `FEATURE_SWITCHES`): desactivar **Puntos, Promociones, Viajes y experiencias, Patrocinio, Reseñas o Pagos online**. La función desaparece de la web y el servidor rechaza su uso; los datos se conservan.
- **Modo piloto** (mismo panel): solo entran profesionales con invitación.
- **Cerrar el registro de cuentas:** `WOD_REGISTRATION_CLOSED=1` en `.env` y reiniciar.
- **Quitar el rol** de centro o administrador a una cuenta comprometida (Administración → Usuarios).
- **Parar el servidor:** `systemctl stop worldives` (unidad en `deploy/worldives.service`).
- No hay una función para **bloquear** una cuenta sin borrarla **[PENDIENTE TITULAR]**.

### Aviso en la web y a los centros

*Administración → Operación → Aviso* (`/api/admin/banner`): texto de nivel «información», «mantenimiento» o «incidencia» en todas las páginas durante 1 hora a 14 días, y opcionalmente email `service_notice` a **todos los centros y profesionales**.

### Restaurar

```bash
python app/server.py --verify-backup /var/backups/worldives/db/worldives-AAAAmmdd-HHMM.sqlite3.gz   # «ok · N tablas»
systemctl stop worldives
python app/server.py --restore /var/backups/worldives/db/worldives-AAAAmmdd-HHMM.sqlite3.gz --yes  # la base actual se guarda al lado
tar -xzf /var/backups/worldives/files/archivos-AAAAmmdd-HHMM.tar.gz -C /tmp/restaurar             # fotos y documentos
systemctl start worldives
```

Elige una copia **anterior al incidente**. Los datos posteriores a esa copia se pierden: anótalo en el registro (puede ser en sí una brecha de disponibilidad). Detalle en `docs/despliegue.md`, apartado 7.

## 8. Pendientes

| Tipo | Punto |
|---|---|
| TITULAR | Designar técnico y asesor y completar los contactos |
| TITULAR | Botón «cerrar todas las sesiones» y función para bloquear una cuenta |
| TITULAR | Plantilla de correo de servicio para avisar de una brecha a usuarios y a centros |
| TITULAR | Alertas automáticas de accesos anómalos (descargas de documentos, fallos de inicio de sesión) |
| TITULAR | Cifrar los secretos TOTP y las copias de seguridad |
| ABOGADO | Criterios de riesgo, excepciones al aviso a afectados, autoridad principal con afectados de otros países, plazo de aviso a los centros |
| ABOGADO | Si aplica alguna obligación de la Directiva NIS2 (en principio no, por tamaño) |
