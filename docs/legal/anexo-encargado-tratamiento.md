# Anexo de encargo del tratamiento (art. 28 RGPD) entre el centro y WORLDIVES

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

Este documento tiene dos partes:

- **Parte A (interna):** cuándo WORLDIVES trata datos **por cuenta del centro** (encargado) y cuándo los trata **por su cuenta** (responsable independiente). Se ha hecho leyendo el código.
- **Parte B (plantilla):** las cláusulas del anexo que firmaría o aceptaría el centro, junto con las «Condiciones para centros» (`app/legal/es/centros.md`, ruta `#/legal/condiciones-centros`).

Hoy este anexo **no está publicado en la web** ni se acepta en ningún paso del alta. Para que forme parte del contrato habría que añadirlo a `legal_documents` (slug nuevo, por ejemplo `encargo-tratamiento`) y pedir su aceptación al centro, igual que se hace con `centros` en `legal_acceptances`. **[PENDIENTE ABOGADO]**: decidir si va como anexo de las condiciones para centros (aceptación en línea) o como documento aparte.

---

## Parte A · Papel de cada parte, según el código

### A.1 WORLDIVES como encargado del centro

Son datos que **el centro introduce o decide tratar** para su propio negocio. WORLDIVES solo los guarda y los procesa con las herramientas del panel.

| Escenario | Qué hace el código | Datos | Interesados |
|---|---|---|---|
| **Clientes importados** | `POST /api/center/import` → `import_clients()` en `app/server.py`. Crea una ficha sin acceso (`users.password_hash='!'`, `users.guest_center_id` = centro, `users.guest_email`) y una fila en `user_profiles` (`phone`, `notes` con titulación y notas). Hay vista previa, detección de duplicados y registro `clients_imported` en `audit_log`. | Nombre, email, teléfono, titulación, notas libres | Clientes del centro (no tienen cuenta) |
| **Reservas manuales y por API** | `find_or_create_customer()`: una reserva escrita por el centro o enviada a `/api/integrations/bookings` **nunca se enlaza** a una cuenta registrada (corrección G5). Se crea o reutiliza la ficha propia del centro. El email y el teléfono viajan con la reserva (`bookings.contact_email`, `contact_phone`, `contact_name`) para enviar la confirmación. | Nombre, email, teléfono, fecha, actividad, participantes, equipo, notas, `internal_notes`, precio y pago registrado | Clientes del centro |
| **Planning y agenda** | Salidas (`service_slots`), reservas del centro, agenda diaria por email (`queue_center_agendas()`, plantilla de agenda del día siguiente), feed iCal privado (`/ical/<token>.ics`, sin emails de clientes). | Nombre del cliente, participantes, equipo pedido, hora | Clientes del centro |
| **Avisos del centro a sus clientes** | Aviso ligado a una reserva (tabla `messages`, `kind` de aviso), enviado por email y a «Avisos». No hay respuesta por la plataforma. | Texto del aviso, contacto del centro | Clientes del centro |
| **Correos de servicio por cuenta del centro** | Confirmaciones, cambios de fecha, cancelaciones y devoluciones de reservas hechas por el centro (`email_outbox`). | Nombre, email, datos de la reserva | Clientes del centro |
| **Exportaciones** | `GET /api/center/export?kind=clients|bookings|services|payments` → `provider_export()`. Disponible en todos los planes. Los pagos solo los exporta el propietario. Cada exportación queda en `audit_log` (`provider_export`). | Lo exportado | Clientes del centro |
| **Equipo del centro** | Invitaciones (`team_invites`) y miembros (`center_members`) con perfiles propietario / recepción / instructor. Cada acción queda en `audit_log` con `center_id`. | Nombre y email del empleado, perfil, acciones | Personal del centro |
| **Cobros en mostrador y devoluciones** | «Cobrar el resto», «Devolver» (`payment_refunds`), incidencias. | Importes, estado de pago | Clientes del centro |

**[PENDIENTE ABOGADO]** Casos dudosos:

1. **Solicitudes de información** (`info_requests`, formulario «Solicitar información», `POST /api/info-requests`, que suma la estadística con `stat_bump(..., 'info_requests')` y envía las plantillas `info_request` al centro e `info_request_copy` al visitante). El formulario está en la web de WORLDIVES y pide aceptar la privacidad de WORLDIVES, pero el único fin es que el centro conteste. Opciones: (a) WORLDIVES responsable que **comunica** los datos al centro a petición del interesado; (b) WORLDIVES encargado del centro. Lo planteaba ya la v50.37 («Para abogado»).
2. **Personal del centro con cuenta propia.** El empleado tiene una cuenta de WORLDIVES (responsable WORLDIVES), pero su alta en el equipo y sus acciones en el panel las decide el centro.
3. **Buceadores registrados que reservan online.** Hoy las condiciones para centros (apartado 2) dicen que el centro es **responsable independiente** de los datos que recibe. Con eso, aquí no hay encargo. Hay que confirmar que es la calificación correcta.

### A.2 WORLDIVES como responsable independiente

| Tratamiento | Dónde está en el código |
|---|---|
| Cuentas de la plataforma, inicio de sesión, verificación en dos pasos | `users`, `sessions`, `email_verifications`, `password_resets`, `app/wod/totp.py` |
| Ficha del buceador y documentos que él mismo sube | `user_profiles`, `user_documents` (tipos en `DOCUMENT_TYPES`: Titulación, Seguro, Documento de identidad, Documento adicional; sin certificados médicos) |
| Reservas online hechas por el buceador **en la plataforma** (como intermediario) | `bookings` con `source='online'`, `payment_orders` |
| Log Book, reseñas, puntos, promociones, avisos | `logbook_entries`, `center_reviews`, `points_ledger`, `reward_redemptions`, `promotion_codes`, `messages` |
| Comunicaciones comerciales con consentimiento | `users.marketing_consent`, `consent_log` |
| Aceptaciones legales | `legal_acceptances` |
| Denuncias de contenido | `content_reports` |
| Alta y verificación de centros, datos fiscales y DAC7 | `center_claims`, columnas fiscales de `centers` y `users`, `dac7_report()` |
| Planes y cuota anual | `plans`, `plan_payments`, `plan_exceptions` |
| Estadísticas agregadas de la ficha | `provider_stats_daily` (sin datos personales; deduplicación diaria con IP seudonimizada en memoria, `stat_bump()`) |
| Seguridad, registros y copias | `audit_log`, `logs/access.log`, `app/wod/backup.py` |

El centro ve el perfil y los documentos de un buceador registrado solo si se cumple `center_can_see_user()`: reserva online hecha por el propio buceador y no cancelada, o consentimiento expreso (`data_shares`, check-in por QR o interruptor «Compartir mis datos»). Ese acceso es una **comunicación** de WORLDIVES al centro, no un encargo.

### A.3 Stripe

- **Reservas:** el cobro es un **cargo directo en la cuenta de Stripe del centro** (`stripe_kw()`, propiedades de controlador: `WOD_STRIPE_DASHBOARD=full`, `WOD_STRIPE_FEES_PAYER=account`, `WOD_STRIPE_LOSSES=stripe`). Stripe trata los datos de pago según su contrato con el centro. WORLDIVES, como plataforma Connect, crea el Checkout en esa cuenta y recibe por API y webhook solo lo necesario (`payment_intent_id`, importe, `card_brand`, `card_last4`, `receipt_url`, devoluciones y disputas).
- **Cuota anual:** se cobra en la cuenta de Stripe **de WORLDIVES** (`/api/provider/plan/checkout`, `kind=plan_fee`). Aquí Stripe actúa con WORLDIVES según el acuerdo de tratamiento de Stripe.
- **[PENDIENTE ABOGADO]** Papel de Stripe y de WORLDIVES en los cargos directos: ¿es Stripe subencargado de WORLDIVES, encargado del centro o responsable independiente? ¿Cómo se califica el acceso de WORLDIVES a los datos de la cuenta conectada? Mientras no se decida, **Stripe no figura como subencargado** en la cláusula 7.

### A.4 Hallazgos del código que afectan al anexo

Para corregir o decidir antes de publicar el anexo:

1. **Los clientes importados sin reservas no se ven ni se exportan.** `/api/center/clients` y `provider_export(kind='clients')` solo listan a quien tiene reservas o check-in con el centro. Un cliente importado con `/api/center/import` que nunca ha reservado queda en la base pero el centro no lo ve ni lo puede exportar. Esto choca con la cláusula de devolución y con la decisión del titular «los datos del centro son suyos y los exporta siempre». **[PENDIENTE TITULAR]**: añadir esas fichas al listado y a la exportación.
2. **El centro no puede borrar una ficha de cliente.** No hay ruta para suprimir o rectificar un cliente propio. Si un cliente del centro ejerce sus derechos, hoy solo lo puede hacer la administración a mano en la base.
3. **No hay procedimiento de cierre de un centro en el código.** `delete_user_account()` anonimiza la cuenta de la persona, pero la ficha del centro, sus fichas de cliente (`guest_center_id`), sus reservas y sus `info_requests` se quedan. La supresión al terminar el encargo es hoy manual.
4. **No hay plazo de borrado automático** para `info_requests`, fichas de cliente del centro ni reservas (`run_retention_jobs()` no las toca: «Bookings and payments are never deleted here»).
5. **Las copias de seguridad no están cifradas en el servidor.** `backup.py` las comprime (gzip) con permisos `0600`. El cifrado solo existe si el destino externo lo aplica (recomendación de `docs/despliegue.md`: remoto `crypt` de rclone). La política de privacidad publicada dice «copias de seguridad cifradas». **[PENDIENTE TITULAR]**: cifrar en origen o corregir el texto.
6. **El secreto TOTP** (`users.totp_secret`) se guarda sin cifrar en la base. Los códigos de recuperación sí se guardan con hash.

---

## Parte B · Plantilla del anexo

> Los textos entre llaves se rellenan con los datos del titular (Administración → Legal). Los del centro salen de «Datos fiscales y seguro» (`/api/provider/fiscal`).

### Partes

- **Responsable del tratamiento («el centro»):** la persona física o jurídica titular del centro o profesional, con los datos fiscales que figuran en su panel (razón social, NIF/TIN, dirección fiscal).
- **Encargado del tratamiento («WORLDIVES»):** {{owner_name}} ({{trade_name}}), NIF {{nif}}, domicilio {{address}}, email de privacidad {{dpo_email}}.

### 1. Objeto

WORLDIVES trata por cuenta del centro los datos personales necesarios para prestarle las herramientas de gestión de la plataforma {{site_url}}:

- fichas de clientes propias del centro (creadas a mano, por importación CSV o por la API de reservas);
- reservas introducidas por el centro, planning, salidas y agenda;
- avisos y correos de servicio que el centro envía a sus clientes sobre sus reservas;
- registro de cobros en el centro y devoluciones;
- exportaciones de datos;
- gestión del equipo del centro;
- [PENDIENTE ABOGADO] solicitudes de información recibidas por el formulario de la ficha.

Este anexo **no** cubre los datos que WORLDIVES trata como responsable (cuentas de la plataforma, reservas online hechas por los buceadores, reseñas, puntos, seguridad), que se rigen por la [Política de privacidad](#/legal/privacidad).

### 2. Duración

Mientras el centro tenga cuenta en WORLDIVES con cualquier plan, incluida la ficha gratuita. Al terminar, se aplica la cláusula 10.

### 3. Naturaleza y finalidad

| Operación | Finalidad |
|---|---|
| Recogida (formularios del panel, importación CSV, API) | Crear y mantener las fichas de cliente y las reservas del centro |
| Conservación | Alojamiento en la base de datos de la plataforma y en sus copias de seguridad |
| Consulta y modificación | Uso por el personal del centro según su perfil (propietario, recepción, instructor) |
| Comunicación | Envío por email de confirmaciones, cambios, avisos y agenda diaria; feed iCal sin emails de clientes |
| Extracción | Exportación CSV a petición del centro |
| Supresión | A petición del centro o al terminar el encargo |

WORLDIVES no usa estos datos para sus propios fines. En particular:

- los clientes importados **no reciben comunicaciones comerciales** de WORLDIVES (`import_clients()`: «they never become accounts nor receive marketing»; el envío comercial excluye `guest_center_id`);
- **no se enlazan** a cuentas registradas aunque coincida el email (`find_or_create_customer()`);
- **no se ceden** a otros centros.

### 4. Tipos de datos

Según las tablas del código (`BASE_SCHEMA` en `app/server.py`):

| Origen | Campos |
|---|---|
| Ficha de cliente del centro (`users` con `guest_center_id`, `user_profiles`) | Nombre y apellidos; email (`guest_email`); teléfono; titulación y notas libres (`user_profiles.notes`) |
| Reservas del centro (`bookings`) | Fecha y hora; actividad; participantes; equipo pedido y notas de equipo; guía; nitrox; recogida; notas; notas internas; contacto (`contact_name`, `contact_email`, `contact_phone`); precio, señal, importe pagado y pendiente, devoluciones; estado; referencia externa |
| Avisos (`messages`) | Asunto, texto, contacto del centro |
| Solicitudes de información (`info_requests`) | Nombre, email, teléfono, mensaje, fecha deseada, participantes, idioma; IP seudonimizada (`ip_hash`) |
| Equipo (`center_members`, `team_invites`) | Nombre, email, perfil, acciones registradas en `audit_log` |

**Datos de categorías especiales:** no están previstos. El centro se compromete a **no introducir datos de salud** (por ejemplo, en las notas o en la importación). WORLDIVES rechaza los certificados médicos (`MEDICAL_WORDS`, G6). **[PENDIENTE ABOGADO]**: las notas libres no se filtran; valorar si basta con esta obligación contractual.

### 5. Categorías de interesados

- Clientes y clientes potenciales del centro.
- Personas que piden información al centro.
- Personal del centro (propietarios, recepción, instructores).

### 6. Obligaciones de WORLDIVES

WORLDIVES se compromete a:

1. Tratar los datos **solo siguiendo las instrucciones documentadas del centro**. Las instrucciones son este anexo y el uso que el centro hace del panel. Si una instrucción infringe la normativa, avisará al centro.
2. Garantizar que las personas autorizadas (administradores de la plataforma) tienen **deber de confidencialidad**. El acceso de la administración a documentos queda registrado (`document_downloaded` en `audit_log`).
3. Aplicar las **medidas de seguridad** de la cláusula 8.
4. Respetar las condiciones para recurrir a **subencargados** (cláusula 7).
5. **Ayudar** al centro a atender los derechos de los interesados (cláusula 9).
6. Ayudar al centro con la seguridad, las brechas y, si hiciera falta, la evaluación de impacto, con la información de que disponga.
7. Al terminar, **devolver y suprimir** los datos (cláusula 10).
8. Poner a disposición del centro la información necesaria para demostrar el cumplimiento y permitir **auditorías** (cláusula 11).
9. Llevar el registro de actividades de tratamiento como encargado (art. 30.2 RGPD; ver `docs/legal/registro-actividades-tratamiento.md`, apartado «Como encargado»).

**Obligaciones del centro:** tener una base jurídica para tratar e importar los datos de sus clientes y haberles informado (art. 13 y 14 RGPD). **[PENDIENTE ABOGADO]**: la v50.37 pidió revisar la base legal del centro para importar a sus clientes.

### 7. Subencargados

El centro autoriza de forma general a WORLDIVES a recurrir a estos subencargados. WORLDIVES avisará de cualquier cambio con **[15 días — PENDIENTE TITULAR]** de antelación para que el centro pueda oponerse.

| Subencargado | Servicio | Datos | Ubicación |
|---|---|---|---|
| {{hosting}} | Servidor VPS (base de datos SQLite, archivos y copias locales) | Todos los de la cláusula 4 | UE (`docs/despliegue.md`, apartado 1) |
| Proveedor SMTP **[pendiente de decisión del titular; recomendado Brevo]** | Envío de correos (`WOD_SMTP_HOST`, cola `email_outbox`) | Nombre, email y contenido del correo | Brevo: UE |
| Almacenamiento externo de copias **[pendiente; recomendado en la UE con cifrado]** | Copia fuera del servidor (`WOD_BACKUP_COMMAND`, ejemplo `deploy/backup-externo.sh`) | Copia completa de la base y de los archivos | UE |
| Stripe **[PENDIENTE ABOGADO]** | Cobros en la cuenta del centro | Ver A.3 | Irlanda (Stripe Payments Europe Ltd.), con transferencias a EE. UU. |

No son subencargados porque **no reciben datos de los clientes del centro**:

- Esri (vista satélite): las teselas se piden desde el servidor, sin la IP del visitante.
- Nominatim/OpenStreetMap (`/api/geocode`): recibe solo el texto de búsqueda de una localidad, desde el servidor.
- El monitor externo de disponibilidad (`/api/health`): solo comprueba que la web responde.

### 8. Medidas de seguridad

Medidas que **ya están en el código** (v50.38):

| Medida | Dónde |
|---|---|
| Contraseñas con PBKDF2-SHA256, 600 000 iteraciones, sal aleatoria y prefijo de versión; actualización automática al entrar | `app/wod/security.py` (`hash_password`, `needs_rehash`), `WOD_PBKDF2_ITERATIONS` |
| Sesiones guardadas como hash SHA-256 del token, cookie HttpOnly y SameSite=Lax (Secure con https), caducidad a las 8 h, borrado periódico | `current_user()`, tabla `sessions`, `SESSION_TTL_SECONDS`, `maintenance_loop()` |
| Cierre de las demás sesiones al cambiar contraseña, rol, email o activar el segundo factor | rutas con `DELETE FROM sessions WHERE user_id=?` |
| Verificación en dos pasos (TOTP, RFC 6238) opcional para todos y **obligatoria para administradores** en producción | `app/wod/totp.py`, `WOD_ADMIN_TOTP_REQUIRED`, `check_production_settings()` |
| Límites de intentos en inicio de sesión, registro, recuperación y TOTP | `RateLimiter` en `security.py` |
| Protección CSRF: se rechaza todo POST/DELETE sin `Origin` ni `Referer` válidos (salvo webhooks firmados y la API de reservas con clave) | `CSRF_EXEMPT` en `Handler` |
| Content-Security-Policy estricta (sin scripts en línea ni de terceros, `frame-ancestors 'none'` salvo el widget) y cabeceras `nosniff`, `Referrer-Policy`, `Permissions-Policy`, HSTS | `content_security_policy()`, `security_headers()` |
| Documentos privados fuera de `/public`, tipo comprobado por los primeros bytes, máximo 10 MB, permisos `0600`, servidos con `Cache-Control: private, no-store`; acceso solo del dueño, del centro autorizado o de la administración; cada descarga y cada intento denegado se registran | `save_upload()`, `document_file_path()`, `center_can_see_user()`, `document_downloaded` / `document_access_denied` |
| Exportaciones y feeds sin caché (`no-store`); iCal sin emails; CSV con protección contra inyección de fórmulas | `/api/center/export`, `csv_text()` |
| Perfiles del equipo comprobados en el servidor (`team_gate`, `OWNER_ONLY_PREFIXES`) | `app/server.py` |
| Registro de actividad (`audit_log`, con `center_id` para las acciones del equipo) | `audit()` |
| Registro de accesos sin cadena de consulta, con **IP truncada** (/24 en IPv4, /48 en IPv6), rotación diaria y 14 días de conservación | `wod/ops.py` (`access_logger`), `log_ip()`, `WOD_LOG_IP`, `WOD_LOG_RETENTION_DAYS` |
| IP seudonimizada (hash con clave) en aceptaciones, consentimientos, denuncias y solicitudes | `ip_hash()` |
| Copias de seguridad: base cada hora con la API de copia de SQLite y comprobación `quick_check`; archivos cada día; rotación 48 horarias / 30 diarias / 12 mensuales; permisos `0600`; copia externa opcional; `PRAGMA quick_check` diario con aviso | `app/wod/backup.py`, `run_backup_jobs()`, `ops_alert()` |
| Aviso a los administradores ante 5 errores 500 en 10 minutos | `ErrorMonitor` en `wod/ops.py` |
| Tamaño de las peticiones limitado antes de leer el cuerpo | `wod/config.py` (`MAX_JSON_BYTES`, `MAX_UPLOAD_BYTES`) |
| Arranque bloqueado en producción sin https, sin `WOD_SECRET_KEY` de 32 caracteres, con `WOD_DEBUG` o sin TOTP de administradores | `check_production_settings()` |
| Proxy de confianza explícito para leer la IP real | `WOD_TRUSTED_PROXIES`, `client_ip()` |

Medidas organizativas: entorno de pruebas separado que nunca usa la base real (`docs/despliegue.md`, apartado 6) y procedimiento de brechas (`docs/legal/procedimiento-brechas.md`).

Mejoras previstas (ver A.4): cifrado de las copias en origen y del secreto TOTP.

### 9. Ejercicio de derechos

- Si un interesado se dirige a WORLDIVES por un dato que trata por cuenta del centro, WORLDIVES lo **reenviará al centro en un máximo de [5 días hábiles — PENDIENTE TITULAR]** y no contestará por su cuenta salvo instrucción del centro.
- El centro puede consultar y exportar los datos desde su panel. Hoy **no puede borrar ni editar** una ficha de cliente desde el panel (A.4): hasta que exista esa función, WORLDIVES hará la supresión o rectificación a petición escrita del centro en un máximo de **[10 días — PENDIENTE TITULAR]**.

### 10. Devolución y supresión de los datos

- **Exportación siempre disponible.** El centro puede descargar en CSV sus clientes, reservas, servicios y pagos en cualquier plan, también en la ficha gratuita y después de terminar un plan de pago (decisión del titular: «la exportación nunca se bloquea»; comprobado en `tests/test_phase6_centers.py`). Ver la limitación de los clientes importados sin reservas (A.4, punto 1).
- **Al terminar el encargo** (baja del centro):
  1. WORLDIVES avisa al centro y mantiene la exportación disponible durante **[30 días — PENDIENTE TITULAR]**.
  2. Pasado ese plazo, suprime las fichas de cliente propias del centro, las solicitudes de información y los avisos.
  3. Las reservas y los pagos se conservan **bloqueados** el tiempo que exija la ley **[PENDIENTE ABOGADO: quién conserva y durante cuánto: obligación del centro o de WORLDIVES; hoy el código nunca borra reservas]**.
  4. Los datos que queden en las copias de seguridad desaparecen con la rotación: como máximo **12 meses** con la configuración por defecto (`WOD_BACKUP_KEEP_MONTHLY=12`), más lo que conserve el destino externo.
- Este procedimiento **no está automatizado** en el código (A.4, punto 3). Mientras no lo esté, lo ejecuta la administración y lo anota en `audit_log`.

### 11. Información y auditorías

- WORLDIVES facilita al centro, a petición, este anexo, el registro de actividades, la lista de subencargados y el historial de actividad de su equipo (`audit_log` con su `center_id`).
- El centro puede auditar el cumplimiento, por sí mismo o por un auditor obligado a confidencialidad, con un preaviso de **[30 días — PENDIENTE TITULAR]**, en horario laborable y como máximo **[una vez al año — PENDIENTE TITULAR]**, salvo que haya habido una brecha. Cada parte asume sus costes **[PENDIENTE ABOGADO]**.

### 12. Brechas de seguridad

WORLDIVES avisará al centro **sin dilación indebida y, como máximo, en [48 horas — PENDIENTE TITULAR]** desde que tenga constancia de una brecha que afecte a sus datos, con la información del art. 33.3 RGPD de que disponga. Así el centro puede notificar a la AEPD dentro de sus 72 horas. Procedimiento interno en `docs/legal/procedimiento-brechas.md`.

### 13. Responsabilidad y ley aplicable

**[PENDIENTE ABOGADO]**: límite de responsabilidad entre las partes, prevalencia de este anexo sobre las condiciones para centros y ley aplicable (las condiciones para centros remiten a la ley española).

---

## Resumen de pendientes

| Tipo | Punto |
|---|---|
| ABOGADO | Forma de aceptación del anexo (en línea, anexo de `centros`, documento aparte) |
| ABOGADO | Papel de WORLDIVES en `info_requests` y con el personal del centro |
| ABOGADO | Calificación del centro como responsable independiente de los datos de reservas online |
| ABOGADO | Papel de Stripe en cargos directos |
| ABOGADO | Base legal del centro para importar clientes; notas libres y datos de salud |
| ABOGADO | Conservación de reservas y pagos tras la baja del centro |
| ABOGADO | Responsabilidad, costes de auditoría y ley aplicable |
| TITULAR | Plazos: aviso de subencargados, reenvío de derechos, supresión, devolución, auditorías, aviso de brechas |
| TITULAR | Mostrar y exportar los clientes importados sin reservas; borrar o editar fichas de cliente desde el panel |
| TITULAR | Procedimiento de baja de un centro en el código |
| TITULAR | Cifrado de las copias de seguridad (o corregir la política de privacidad) |
