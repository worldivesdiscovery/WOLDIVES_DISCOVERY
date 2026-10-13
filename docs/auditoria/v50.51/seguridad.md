# WORLDIVES DISCOVERY v50.51 · Auditoría de seguridad (OWASP Top 10, 2021)

Revisión hecha el 13/10/2026 sobre la v50.50 y corregida en la v50.51. Pruebas: `tests/test_v50_51_seguridad.py`
(46) y `tests/test_v50_51.py` (clase `SeguridadExtra`). **Las 49 pasan en la v50.51.**

## Estado de cada hallazgo en la v50.51

| ID | Gravedad | Qué era | Estado |
|---|---|---|---|
| A01-1 | media | Recepción podía cambiar nombre, email, teléfono, web, logo, redes y política de cancelación del centro; un instructor veía los ingresos | **Corregido**: esas rutas exigen el permiso «Ficha del centro y ajustes» y la analítica el de «Estadísticas» |
| A07-1 | media | Sin límite de intentos por cuenta (fuerza bruta desde muchas IP) | **Corregido**: 24 intentos fallidos cada 15 minutos por cuenta, con alerta de seguridad |
| A02-2 | media | Copias de seguridad sin cifrar | **Corregido**: AES-256-GCM con `WOD_BACKUP_KEY` (aparece en «Estado del sistema» si falta); `--verify-backup` y `--restore` descifran solos |
| A02-1 | baja | Secretos de la verificación en dos pasos en claro | **Corregido**: cifrados con `WOD_DATA_KEY`; la migración cifra los existentes |
| A02-3 | baja | Fotos públicas con EXIF y GPS | **Corregido**: se vuelven a guardar sin metadatos |
| A03-1 | baja | Cuatro títulos de ventanas sin escapar | **Corregido** |
| A04-1 | baja | Denuncias con enlaces `javascript:` | **Corregido**: solo direcciones http(s) o rutas de la web |
| A05-1 | baja | La cabecera `Server` decía la versión de Python | **Corregido** |
| A05-2 | baja | Errores de integridad con el mensaje interno de SQLite | **Corregido**: se registra en el servidor, no se envía |
| A05-3 | baja | La comprobación de los zips no vigilaba todas las claves | **Corregido**: también `WOD_DATA_KEY`, `WOD_DATA_KEY_OLD`, `WOD_BACKUP_KEY` y las de WhatsApp |
| A06-1 | baja | Versiones mínimas de Pillow y cryptography con fallos conocidos | **Corregido**: Pillow ≥ 10.3.0 y cryptography ≥ 42.0.4. Fijar versiones con hash: **Pendiente de decisión** (exige un archivo de versiones por sistema operativo) |
| A07-2 | baja | Se podía saber si un email tenía cuenta por el tiempo de respuesta | **Corregido**: se comprueba siempre una contraseña |
| A09-1 | baja | Tokens de iCal y enlaces cortos en el registro de accesos | **Corregido**: se guardan como `***` |
| A09-2 | baja | Inicios de sesión fallidos sin registro | **Corregido**: quedan en el registro de auditoría |
| A09-3 | baja | Enlaces de un solo uso legibles en Administración → Correos | **Corregido**: se muestran como `***` |
| — | baja | Límite de denuncias sin tope de memoria | **Corregido** |
| — | baja | Alta del equipo sin la política de contraseñas | **Corregido**: las mismas reglas que el registro |
| — | baja | Comprobaciones de la «contraseña actual» sin límite | **Corregido**: 10 intentos fallidos cada 15 minutos por persona |
| — | baja | Entorno de pruebas: entrada rápida sin contraseña en la app de pruebas y alta del primer administrador | **Ya estaba** controlado: solo existe con `WOD_DEMO_MODE=1`, que se niega a arrancar con la dirección de producción. Desde la v50.51 la demo trae su propia cuenta de administración, así que la pantalla de alta no aparece |

**Lo que ya estaba bien** (comprobado con pruebas): las 365 rutas exigen sesión salvo las públicas; un buceador no
entra en rutas de profesional ni de administración; un centro no ve ni cambia datos de otro (reservas, servicios,
extras, plantillas, barcos, tarifas, equipo, promociones, clientes); protección CSRF; SQL sin inyección; HTML escapado;
rutas de archivos protegidas; cabeceras de seguridad (CSP, HSTS, X-Frame-Options, nosniff); contraseñas con PBKDF2 de
600 000 iteraciones y sal única; sesiones con caducidad, cerradas al salir y al cambiar la contraseña; límites en
inicio de sesión, recuperación, registro y verificación en dos pasos; firmas de los webhooks; subidas comprobadas por
contenido y tamaño; protección contra SSRF; claves solo en el `.env`; copias comprobadas, rotadas y restaurables.

El informe original del revisor sigue debajo, con el detalle de cada comprobación y cómo se reproducía cada hallazgo
(las líneas citadas son de la v50.50).

---

## Resumen

Base de partida sólida: el aislamiento entre centros de v50.47 aguanta (barrido de 365 rutas, ids de otro centro, CSRF,
cabeceras, subidas, SQL, sesiones). Los hallazgos nuevos son sobre todo de **permisos dentro de un mismo centro**,
**autenticación** (fuerza bruta distribuida) y **protección de datos en reposo** (copias de seguridad y secretos TOTP).

| ID | Gravedad | Categoría | Dónde (líneas de `0795c14`) | Hallazgo |
|---|---|---|---|---|
| A01-1 | **media** | A01 | `app/wod/roles.py:143-161`; `app/server.py:13706`, `12796`, `13199`, `11692`, `10569` | Cuatro rutas de la ficha y ajustes del centro (y la de analítica) no están en las reglas de permisos del equipo: recepción cambia ficha pública, email/teléfono, política de cancelación, logo y redes; un instructor ve los ingresos. |
| A07-1 | **media** | A07 | `app/server.py:1062-1063`, `11576-11580` | No hay límite por cuenta: fuerza bruta distribuida (muchas IPs / un /64 de IPv6) contra la misma cuenta sin bloqueo. |
| A02-2 | **media** | A02 | `app/wod/backup.py:35`, `58`, `92`; `scripts/copia_externa.sh:8` | Copias de seguridad sin cifrar enviadas fuera del servidor (base completa y documentos privados). |
| A02-1 | baja | A02 | `app/server.py:11596`, `11606`, `2636` | Secretos TOTP (`totp_secret`, `totp_pending_secret`) en claro en la base. |
| A02-3 | baja | A02/privacidad | `app/server.py:2865` | Las fotos públicas (logo, portada, galería, fotos de puntos) conservan EXIF/GPS. |
| A03-1 | baja | A03 (XSS) | `public/js/world-dives-v8.js:2237`, `2249`, `4071`, `4095` (sumidero en `3308`) | Títulos de ventanas modales con texto de la base sin escapar (inyección de HTML; la CSP impide ejecutar scripts). |
| A04-1 | baja | A04 | `app/server.py:12878`; `public/js/world-dives-v8.js:5335` | El formulario público de denuncias guarda `target_url` con cualquier esquema (`javascript:`, `data:`) y la administración lo pinta como enlace. |
| A05-1 | baja | A05 | `app/server.py:9746` | La cabecera `Server` revela la versión de Python. |
| A05-2 | baja | A05 | `app/server.py:13963-13965` | Los errores de integridad devuelven el mensaje interno de SQLite (`detail`). |
| A05-3 | baja | A05 | `scripts/generar_zips.py:57` | La comprobación de secretos de los zips no vigila `WOD_DATA_KEY`, `WOD_DATA_KEY_OLD`, `WHATSAPP_APP_SECRET`, `WHATSAPP_VERIFY_TOKEN`. |
| A06-1 | baja | A06 | `requirements.txt:7`, `9`; `scripts/iniciar.py:31` | Las versiones mínimas admiten Pillow/cryptography con CVE conocidas y no hay versiones fijadas con hash. |
| A07-2 | baja | A07 | `app/server.py:11579` | Enumeración de cuentas por tiempo de respuesta (sin PBKDF2 si el usuario no existe). |
| A09-1 | baja | A09 | `app/server.py:9750` | Tokens que van en la ruta (`/ical/<token>.ics`, `/r/…`, `/api/r/…`) quedan en `logs/access.log`. |
| A09-2 | baja | A09 | `app/server.py:11579-11580` | Los inicios de sesión fallidos o bloqueados no quedan en `audit_log` ni generan alerta. |
| A09-3 | baja | A09 | `app/server.py:10335-10339` | `GET /api/admin/emails/<id>` devuelve los enlaces de un solo uso (restablecer contraseña, invitación de equipo…) en claro. |
| — | baja (sin prueba) | A04/A07/A05 | ver secciones | `REPORT_LIMIT` sin tope de memoria; `/api/team/join` no aplica la política de contraseñas; comprobaciones de la contraseña actual sin límite; entorno de pruebas con entrada sin contraseña y alta del primer administrador abierta. |

**Estado de las pruebas** (copia de trabajo actual): 46 pruebas, **28 pasan** (protecciones que funcionan) y **18 fallan**:
exactamente las 18 `test_hallazgo_*`, una por hallazgo (A01-1 tiene cuatro). Ningún error 500 del servidor durante la ejecución.

**Correcciones validadas**: se aplicaron las correcciones propuestas en una copia aparte (`app/`, `public/`, `scripts/`,
`requirements.txt`; parche en el anexo) y **las 46 pruebas pasan**. Con esa copia también pasan
`test_phase1_security`, `test_phase2_payments`, `test_phase4_email_totp`, `test_phase5_legal_catalog`, `test_phase6_centers`,
`test_phase7_infra`, `test_v50_47_rotacion` y `test_v50_47_estatico`. Hay que adaptar una prueba antigua: `tests/test_e2_p7_auth.py:92`
lee `totp_pending_secret` de la base para calcular el código; con A02-1 corregido ese valor va cifrado: tomad el secreto de
la respuesta de `/api/account/totp/setup` o descifradlo con `helpers.cifrado_for(self.server.env).decrypt_secret(...)`.
(`test_v50_48_app` y `test_v50_49_pro` fallan ya en la copia de trabajo, con o sin parche, porque `APP_VERSION` es 50.51 y
`sw.js`/`index.html` siguen en 50.50: es el cambio de versión en curso, no algo de esta auditoría.)

## Método

1. Lectura del código con evidencias: `app/server.py` (Handler, `do_GET` 10007, `do_POST` 11418, `do_DELETE` 13995 y sus
   funciones auxiliares), `app/wod/*.py` (security, roles, inquilinos, cifrado, backup, remoto, videos, imagenes, totp, config,
   movil, pro) y los sumideros de HTML de `public/js/world-dives-v8.js`, `wd-app.js` y `wd-app-pro.js`.
2. Rutas derivadas del propio `app/server.py` (comparaciones `path ==`, `path in (…)`, `startswith`/`endswith` y
   `re.fullmatch`): **365 rutas** (156 GET, 208 POST, 1 DELETE). La prueba las vuelve a derivar en cada ejecución.
3. Verificación empírica con el servidor de pruebas (`tests/helpers.py: Server`) de cada afirmación importante.
4. Para cada hallazgo, la corrección se aplicó en una copia y se comprobó con las pruebas (anexo).
5. Lo ya auditado y corregido en v50.31-v50.47 (`docs/seguridad.md`, `docs/seguridad/aislamiento-centros.md`) se ha
   vuelto a comprobar por encima, sin duplicar sus pruebas (`tests/test_phase1_security.py`, `tests/test_v50_47_*.py`).

---

## A01 · Control de acceso roto (incluye CSRF y salto de directorio)

### Qué se ha comprobado

| Comprobación | Evidencia | Resultado |
|---|---|---|
| Rutas privadas sin sesión | Barrido de las 365 rutas; las públicas a propósito están en una lista blanca explícita (`PUBLIC_GET`/`PUBLIC_POST` de la prueba). `require_user` (`app/server.py:2400`) y `require_role` (2407). | **Correcto**: todas las privadas dan 401/403/404 (`test_a01_rutas_privadas_sin_sesion_responden_401_403_404`). |
| Buceador en rutas de profesional/administración | Barrido de todas las rutas `admin/`, `center/`, `provider/`, `manifest`, `avisos`, `whatsapp`, `pro/`, `team/`, pagos Connect, agenda, plantillas, QR, puntos, servicios, experiencias, gestión de reservas, canje de promociones, respuestas a reseñas, vida marina. | **Correcto**: 403/404/410. Cuatro rutas validan el cuerpo antes que el rol (400 con un cuerpo vacío): con ids reales dan 403/404 y no cambian nada (`test_a01_buceador_con_ids_reales_de_otro_centro`). `/api/pro/escanear` responde 200 a un buceador, pero solo «no es de tu centro», sin datos. |
| IDOR entre centros (reservas, servicios, salidas, clientes, extras, plantillas, barcos, tarifas, equipo, invitaciones, promociones) | `owns_service` (3913), `can_manage_booking` (6957), `require_booking_provider` (6968), capa `app/wod/inquilinos.py`, SQL con `center_id=<sesión>`; `GET /api/center/clients` (11305) filtra por el centro de la sesión. | **Correcto**: 403/404 y foto de las filas de B idéntica antes y después (`test_a01_centro_no_lee_ni_cambia_datos_de_otro_centro_por_id`). Los servicios pausados de B no salen con `include_inactive=1`. |
| IDOR entre buceadores (reservas, cuaderno, documentos, pagos, cambios de fecha) | Consultas con `user_id=<sesión>` (13166-13180, 12178-12214, 12768, 11015, 11738, 12258); documentos con `center_can_see_user` (2419). | **Correcto** (`test_a01_buceador_no_toca_datos_de_otro_buceador`). |
| Motivo obligatorio del administrador | `admin_reason_gate` (3953), regex `ADMIN_CENTER_GET/POST` (3941-3946). | **Correcto** (ya cubierto por `tests/test_v50_47_aislamiento.py: test_9_admin_needs_a_reason`). |
| Campos de centro enviados por el navegador | `tenant_guard` (3971). | **Correcto** (cubierto en `test_v50_47_aislamiento.py: test_6`). |
| CSRF | `enforce_same_origin` (9833): todo POST/DELETE exige `Origin` (o `Referer`) igual a `WOD_PUBLIC_URL`; excepciones solo para webhooks firmados, la API con clave y la baja con token (`CSRF_EXEMPT`, 9831). Cookie `SameSite=Lax` (14038). Sin cabeceras CORS. Los GET no cambian estado (solo auditoría y contadores). | **Correcto**: con sesión válida, `Origin` ajeno, `null`, `http://127.0.0.1:PUERTO.evil.example` o sin `Origin`/`Referer` → 403 y nada cambia; `Referer` propio → 200 (`test_a01_csrf_…`). |
| Salto de directorio en archivos servidos | `/assets/uploads/` (10016) y estáticos (10025) con `resolve()` + `is_relative_to`; `/storage/` siempre 403 (10039); documentos solo por la API (`document_file_path`, 2275). | **Correcto** (`test_a05_rutas_de_archivos_sin_salto_de_directorio`). |
| Redirecciones abiertas | `redirect()` solo a `/#/r/…` (regex) y a rutas internas; `/app/vuelta` solo a los esquemas propios (`wod/movil.py:app_scheme`); `next` del login siempre `#…` (`world-dives-v8.js:1508`). | **Correcto**. |
| Permisos dentro del equipo de un centro | `team_gate` (3880) con `wod/roles.py: REGLAS_POST/REGLAS_GET` (143-161) y `necesita()` (168): una escritura sin regla propia pide «reservas»; una lectura sin regla es libre. | **Hallazgo A01-1**. |

### Hallazgo A01-1 · Rutas de ajustes del centro fuera de las reglas de permisos del equipo — **media**

`wod/roles.py` decide qué puede hacer cada perfil por el **prefijo** de la ruta. Varias rutas que cambian la ficha y los
ajustes del centro no están en la regla `'centro'` («Ficha del centro y ajustes») y caen en la regla por defecto de las
escrituras, `'reservas'`, que tienen recepción y cualquier perfil propio con «Reservas, solicitudes y clientes». Es el mismo
patrón que el fallo nº 7 de v50.47 (un alias fuera de la lista).

| Ruta | Línea | Qué cambia | Debería pedir | Pide hoy |
|---|---|---|---|---|
| `POST /api/center/profile` | 13706 | nombre, país, ciudad, dirección, **web, teléfono y email públicos**, descripción, coordenadas | `centro` | `reservas` |
| `POST /api/center/cancellation-policy` (alias de `/api/provider/cancellation-policy`) | 12796 | horas de cancelación gratuita y **% de reembolso** | `centro` | `reservas` |
| `POST /api/provider/profile` | 13199 (13203) | **redes sociales del centro** | `centro` | `reservas` |
| `POST /api/provider/avatar` | 11692 | **logo del centro** | `centro` | `reservas` |
| `GET /api/center/analytics` | 10569 | lee **ingresos** (`income`, `revenue`), reservas y canales | `estadisticas` | nada (lectura libre) |

Impacto: un recepcionista (o un empleado a punto de irse) cambia el email y el teléfono públicos del centro para desviar
clientes, cambia la política de reembolso de todas las reservas futuras o el logo; un instructor (solo «Pasar lista») ve los
ingresos del centro, cosa que `/api/provider/stats` (permiso «estadisticas») y `/api/provider/payments` («cobros») sí
impiden. Todo dentro del propio centro (no cruza inquilinos).

Reproducir (centro A con un miembro de perfil `reception`, sesión del miembro):

```
curl -b rec.txt -H "Origin: $BASE" -H 'Content-Type: application/json' \
     -d '{"name":"Centro A","country":"España","city":"Xàbia","email":"desvio@evil.example","phone":"+34 000","website":"https://evil.example","latitude":38.79,"longitude":0.18}' \
     $BASE/api/center/profile                       # 200 (debería 403); /api/provider/center-update da 403
curl -b rec.txt -H "Origin: $BASE" -H 'Content-Type: application/json' -d '{"cancel_free_hours":1,"cancel_refund_pct":100}' \
     $BASE/api/center/cancellation-policy           # 200; la ruta «oficial» /api/provider/cancellation-policy da 403
curl -b instructor.txt $BASE/api/center/analytics   # 200 con metrics.income; /api/provider/stats da 403
```

Corrección mínima (`app/wod/roles.py`, `REGLAS_POST` y `REGLAS_GET`):

```python
    ('centro', _P('/api/provider/insurance', '/api/provider/cancellation-policy', '/api/center/cancellation-policy', '/api/center/profile',
                  '/api/provider/profile', '/api/provider/avatar', '/api/provider/center-update', '/api/provider/center-showcase',
                  '/api/provider/center-cover', '/api/provider/center-gallery', '/api/center/integration', '/api/provider/ical', '/api/center/import',
                  '/api/center/tariffs', '/api/provider/waiver', '/api/marina/')),
...
    ('estadisticas', _P('/api/provider/stats', '/api/center/analytics')),
```

Recomendado además: invertir el criterio de las lecturas (una ruta `GET /api/center/…` o `/api/provider/…` sin regla
explícita solo para el propietario) para que una ruta nueva no nazca abierta, y una prueba que falle si una ruta de esos
prefijos no tiene regla.

Pruebas: `test_hallazgo_a01_recepcion_cambia_la_ficha_publica_con_api_center_profile`,
`test_hallazgo_a01_recepcion_cambia_la_politica_de_cancelacion_con_el_alias`,
`test_hallazgo_a01_recepcion_cambia_logo_y_redes_del_centro`, `test_hallazgo_a01_instructor_ve_los_ingresos_en_center_analytics`
(fallan hoy) y el control positivo `test_a01_equipo_respeta_permisos_en_las_rutas_principales` (pasa).

Observación (decisión de diseño, no hallazgo): «la lectura es libre» (`roles.py:168`), así que un instructor descarga
`GET /api/center/export?kind=clients|bookings` y `/api/center/clients` con teléfonos y emails de todos los clientes. Si el
perfil «instructor» debe ver solo sus salidas, añadid esas lecturas a la regla `'reservas'` de `REGLAS_GET`.

---

## A02 · Fallos criptográficos

### Qué se ha comprobado

| Comprobación | Evidencia | Resultado |
|---|---|---|
| Hash de contraseñas | `wod/security.py:35` PBKDF2-HMAC-SHA256, sal aleatoria de 16 bytes, formato `pbkdf2_sha256$it$sal$hash`, 600 000 iteraciones por defecto (`wod/config.py:90`, mínimo 100 000), comparación en tiempo constante (`:42`), re-hash de las antiguas (`server.py:11582`). | **Correcto** (`test_a02_contrasenas_con_pbkdf2_sal_unica_y_nunca_en_claro`: sal distinta para la misma contraseña, la contraseña no aparece en la base ni en el WAL). |
| Tokens de sesión, restablecimiento, verificación, invitación, API | `secrets.token_urlsafe(32)` y solo el SHA-256 en la base (`login_user` 14026, `new_password_reset` 7367, `team_invites`, `center_integrations`). | **Correcto**. |
| Datos personales cifrados | Teléfonos (`PHONE_COLUMNS`, 1511, con disparadores que rechazan un teléfono en claro) y cuerpos de los correos (`queue_email`, 5969) con AES-256-GCM (`wod/cifrado.py`); credenciales de WhatsApp con `encrypt_secret` (112). | **Correcto**. |
| Transporte | HSTS y `upgrade-insecure-requests` con `WOD_PUBLIC_URL=https://…`; cookie `Secure` (14037). | **Correcto** (`ConHttps.test_a05_hsts_y_cookie_secure_con_https`). |
| Secretos del segundo factor | `totp_secret`/`totp_pending_secret`. | **Hallazgo A02-1**. |
| Copias de seguridad | `wod/backup.py`. | **Hallazgo A02-2**. |
| Metadatos de fotos públicas | `save_public_image` (2865). | **Hallazgo A02-3**. |

### Hallazgo A02-1 · Secretos TOTP en claro — **baja**

`/api/account/totp/setup` guarda el secreto tal cual (`server.py:11596`) y `/enable` lo copia a `totp_secret` (11606);
`check_totp_or_recovery` (2636) lo lee en claro. Quien lea la base o una copia (ver A02-2) genera los códigos de cualquier
cuenta, incluidas las de administración, y el segundo factor deja de proteger frente a una filtración de la base. El resto de
credenciales (WhatsApp) ya usan `wcif.encrypt_secret`.

Reproducir: activar el segundo paso y `SELECT totp_secret FROM users WHERE id=…` → el mismo texto base32 que se mostró en
pantalla.

Corrección (`app/server.py`, validada):

```python
# /api/account/totp/setup
sec=wtotp.new_secret(); db.execute('UPDATE users SET totp_pending_secret=? WHERE id=?',(wcif.encrypt_secret(sec),u['id'])); db.commit()
# /api/account/totp/enable
sec=wcif.decrypt_secret(u['totp_pending_secret']) or u['totp_pending_secret']
... totp_secret=? ... (wcif.encrypt_secret(sec), now(), step, ...)
# check_totp_or_recovery
step = wtotp.verify(wcif.decrypt_secret(user['totp_secret']) or user['totp_secret'], code, ...)
```

Más una migración que cifre los existentes (`UPDATE … SET totp_secret=encrypt_secret(totp_secret)` donde no empiece por
`wdk1:`) y que `scripts/seguridad/rotar_clave_datos.py` los incluya. Adaptar `tests/test_e2_p7_auth.py:92` (ver Resumen).
Opcional: los códigos de recuperación son 48 bits guardados con SHA-256 sin sal (`wod/totp.py:52-57`); con la base
filtrada se pueden recuperar por fuerza bruta: usad HMAC con `WOD_SECRET_KEY` o PBKDF2 con sal.

Prueba: `test_hallazgo_a02_secreto_totp_guardado_en_claro`.

### Hallazgo A02-2 · Copias de seguridad sin cifrar — **media**

`backup_db` (`wod/backup.py:35`) hace una copia SQLite y la comprime con gzip; `backup_files` (58) empaqueta en `.tar.gz`
las fotos **y los documentos privados** (`storage/`: seguros, titulaciones, DNI); `ship` (92) ejecuta
`WOD_BACKUP_COMMAND` con el archivo tal cual, y el ejemplo `scripts/copia_externa.sh:8` lo sube con `rclone` a un almacenamiento
externo. La copia contiene en claro nombres, emails, hashes de contraseñas, secretos TOTP (A02-1), reservas, mensajes,
solicitudes de información, datos fiscales y auditoría; solo teléfonos y cuerpos de correo van cifrados (con
`WOD_DATA_KEY`, que no está en la copia). Quien acceda al bucket externo (credenciales del proveedor, bucket mal
configurado) tiene todo.

Lo demás de las copias es **correcto**: existen (cada hora la base, cada día los archivos; `run_backup_jobs`, 14202), se
comprueban con `quick_check` antes de guardarlas, rotan (48/30/12), son `0600`, avisan si fallan y `verify()`/`restore()`
funcionan (`test_copias_de_seguridad_se_comprueban_y_se_restauran`).

Reproducir: `python3 -c "from wod import backup; …backup_db(db)"` y `zcat worldives-*.sqlite3.gz | head -c 16` →
`SQLite format 3`.

Corrección: cifrar en `wod/backup.py` antes de `ship()` con una clave propia `WOD_BACKUP_KEY` (distinta de `WOD_DATA_KEY`,
guardada fuera del servidor para poder restaurar), y que `verify()`/`restore()` descifren. Implementación validada en el
anexo (`encrypt_file`, AES-256-GCM por bloques de 4 MB que autentican su número y si son el último). Añadir en
`check_production_settings` (14260): `if not wcfg.env('WOD_BACKUP_KEY'): problems.append('Define WOD_BACKUP_KEY …')`, y
documentar la clave en `.env.example` y `docs/despliegue/README.md`. Alternativa sin código: remoto `crypt` de rclone o
`age -r <clave pública>` en `copia_externa.sh` (entonces la prueba no aplica y habría que adaptarla).

Prueba: `test_hallazgo_copias_de_seguridad_sin_cifrar` (la prueba pone `WOD_BACKUP_KEY` y espera que la copia no sea un
SQLite legible).

### Hallazgo A02-3 · Fotos públicas con EXIF y GPS — **baja** (privacidad)

`save_public_image` (2865) comprueba los primeros bytes y guarda el archivo **tal cual** en `/assets/uploads/` (logo, avatar
del freelance, portada, galería, fotos de puntos, imágenes de promociones). Una foto de móvil conserva la posición GPS, la
cámara y la fecha: p. ej. el avatar de un instructor freelance hecho en su casa. `wod/imagenes.py` ya quita los metadatos
para vídeos y especies, pero esta ruta no lo usa.

Reproducir: subir a `/api/provider/avatar` un JPEG con EXIF y descargar la URL devuelta → contiene el bloque `Exif` y la
etiqueta GPS.

Corrección (validada, `save_public_image`, tras detectar `ext`):

```python
    try:
        from PIL import Image
        Image.MAX_IMAGE_PIXELS = 40_000_000
        im = Image.open(io.BytesIO(content)); im.load()
        out = io.BytesIO(); fmt = {'.jpg': 'JPEG', '.png': 'PNG', '.webp': 'WEBP'}[ext]
        if fmt == 'JPEG' and im.mode not in ('RGB', 'L'): im = im.convert('RGB')
        im.save(out, fmt, **({'quality': 90} if fmt != 'PNG' else {})); content = out.getvalue()   # sin exif=
    except Exception:
        pass   # Pillow ausente o archivo que no decodifica: se guarda como antes
```

(No es estricta a propósito: otras pruebas suben `PNG_BYTES`, que no es una imagen decodificable. Si preferís rechazar lo
que Pillow no abre, cambiad esas pruebas a una imagen real, p. ej. `tiny_png()` de la prueba nueva.)

Prueba: `test_hallazgo_a02_fotos_publicas_conservan_exif_y_gps`.

---

## A03 · Inyección (SQL y XSS)

### Qué se ha comprobado

| Comprobación | Evidencia | Resultado |
|---|---|---|
| SQL con f-strings | Análisis AST de las 206 sentencias SQL con f-string de `app/`: interpolan solo constantes (`public_center_sql()`, `CENTER_VISIBLE_SQL`), nombres de tabla/columna elegidos por el código (`provider_table(ptype)` con `ptype` validado, `col='center_id' if …`), listas de `?` (`','.join('?'*len(…))`) y fragmentos `WHERE` con `?` construidos por el código. Los únicos valores de la petición en SQL dinámico son `order` (solo dos valores fijos) y `limit` (`int`) en `GET /api/bookings` (11150-11152). Lo demás, siempre parámetros. | **Correcto** (`test_a03_sql_con_fstring_nunca_interpola_datos_de_la_peticion`, `test_a03_inyeccion_sql_en_login_y_busquedas_no_tiene_efecto`). Los `LIKE '%…%'` con texto del usuario son parámetros (solo comodines). |
| HTML generado por el servidor | Widget (`serve_widget`, 9778: `html.escape` en todo y CSP `default-src 'none'`), página `/app/vuelta` (`wod/movil.py:return_page`, parámetros filtrados por regex y escapados), `serve_spa` (11386: `lang` normalizado, `Host` filtrado y escapado), correos (`render_email`, 5847: `_esc` en todos los valores; vista previa en `iframe sandbox=""`). | **Correcto** (`test_a03_html_generado_por_el_servidor_escapado`). |
| Markdown de los textos legales | `wdMd` (`world-dives-v8.js:5021`): escapa primero (`escapeHtml`) y solo después añade `<strong>`, enlaces (`#/`, `http(s)://`, `mailto:`; lo demás `#`), tablas y títulos; `legal_fill` solo rellena marcadores con los ajustes del administrador. | **Correcto** (`test_a03_markdown_de_los_textos_legales_escapa_html_y_enlaces`, ejecuta la función real con Node si está instalado: `<script>`, `<img onerror>`, `javascript:`, `data:`, comillas en URLs, tablas, citas). |
| Traducción | `translateTree` (`world-dives-v8.js:90`) cambia `nodeValue` y atributos, nunca HTML. | **Correcto**. |
| `innerHTML` / plantillas en la web | 288 sumideros en `world-dives-v8.js`, 28 en `wd-app.js`, 34 en `wd-app-pro.js`. Revisión asistida: se buscaron todas las interpolaciones `${…}` con campos de texto de la base (`.name`, `.title`, `.email`, `.notes`, `.description`, `.city`, `.label`…) fuera de `esc()/escapeHtml()`, y se revisaron a mano las variables locales. Los iconos de Leaflet escapan el nombre (`pointIcon`, 247). Las URLs en `href` vienen validadas en el servidor (`clean_http_url`, `clean_promo_url`, `parse_link`) y escapadas. | **Correcto** salvo **A03-1** y **A04-1**. |
| CSP | `content_security_policy` (`wod/security.py:316`): `script-src 'self'` sin `unsafe-inline`, `object-src 'none'`, `base-uri 'self'`, `form-action 'self'`, `frame-ancestors 'none'`. | **Correcto**; por eso A03-1 no ejecuta scripts. `style-src 'unsafe-inline'` e `img-src https:` permiten maquetar contenido inyectado y cargar imágenes externas. |

### Hallazgo A03-1 · Títulos de ventanas modales sin escapar — **baja**

`wdOpenModal()` (`world-dives-v8.js:3308`) inserta `title` y `subtitle` como HTML (`insertAdjacentHTML`). Casi todas las
llamadas escapan, pero cuatro pasan texto de la base sin `escapeHtml`:

| Línea | Llamada | Origen del texto | Quién lo ve |
|---|---|---|---|
| 2237 | ``title:`Dar «${p.title}»` `` | título de una promoción (lo escribe cualquier miembro con «reservas») | el resto del equipo del centro |
| 2249 | ``title:`Códigos de «${p.title}»` `` | ídem | ídem |
| 4071 | ``title:`Fotos de «${t.name}»` `` | nombre de un tema de portada | administración |
| 4095 | ``title:`Fotos · ${point.name}` `` | nombre de un punto de buceo; **cualquier centro** crea puntos (`POST /api/dive-points`, 13232, `active=1`) | otros centros que lo asocian y la administración |

Impacto: inyección de HTML en el panel de otra persona (enlaces o formularios falsos, imágenes externas). La CSP bloquea
`<script>` y los manejadores `on…=`, por eso es baja.

Reproducir: crear un punto con nombre `<a href="https://evil.example" style="position:fixed;inset:0">Sesión caducada, entra aquí</a>`
y abrir «Fotos» de ese punto desde el panel.

Corrección (validada): ``title:`Dar «${escapeHtml(p.title)}»` ``, ``title:`Códigos de «${escapeHtml(p.title)}»` ``,
``title:`Fotos de «${escapeHtml(t.name)}»` ``, ``title:`Fotos · ${escapeHtml(point.name)}` ``. Mejor aún: que
`wdOpenModal` escape `title` siempre y acepte HTML solo con una opción explícita (`titleHtml`).

Prueba: `test_hallazgo_a03_titulos_de_ventanas_sin_escapar` (estática: falla si una llamada a `wdOpenModal` interpola
`…title`, `…name`, `…label`, `…email`… sin escapar).

---

## A04 · Diseño inseguro

### Qué se ha comprobado

Precios y descuentos calculados en el servidor (`booking_quote`, 2730; tarifas por fecha, 2714); reservas con plazas
reservadas de forma atómica (`reserve_slot_spots`, 2772); pagos confirmados por webhook firmado o consultando a Stripe;
devoluciones con comprobación de inquilino (`order_tenant_problem`, 6863); registro que nunca concede el rol de centro
(G2, cubierto); enlaces de avisos firmados con HMAC y caducidad (`signed_link_booking`, 8978). **Correcto.**

### Hallazgo A04-1 · Denuncias con enlaces `javascript:` — **baja**

`POST /api/reports` es público (12870) y guarda `target_url` solo recortado (12878), sin comprobar el esquema. La
administración lo pinta como `<a href="${esc(r.target_url)}" target="_blank">Abrir</a>` (`world-dives-v8.js:5335`): `esc()`
no impide `javascript:` ni `data:`. Hoy lo frena la CSP (no ejecuta URLs `javascript:`) y `target="_blank"`, pero un anónimo
no debería poder guardar un enlace activo que se muestra a un administrador.

Reproducir: `POST /api/reports {"reason":…, "details":"…20 caracteres…", "name":"Ana", "email":"ana@example.org",
"good_faith":true, "target_url":"javascript:alert(document.cookie)"}` → 200 y `content_reports.target_url` lo contiene.

Corrección (validada), tras la línea 12878:

```python
                    if target and not target.startswith('#/'): target=wsec.clean_http_url(target,500) or ''
```

(`clean_http_url` lanza `ValueError` → 400 para cualquier esquema que no sea http/https.)

Prueba: `test_hallazgo_a04_denuncia_guarda_enlaces_javascript`.

### Menores sin prueba automática (baja)

- **`REPORT_LIMIT` sin tope** (`server.py:7686-7696`): diccionario normal, sin bloqueo ni poda, usado por denuncias,
  contacto y solicitudes de información. Con muchas IPs (IPv6) crece sin límite. Corrección: `REPORT_LIMIT = wsec.RateLimiter(10, 3600)` y
  `report_rate_limited = lambda key: REPORT_LIMIT.hit(key)` (como el resto de límites).
- **Entorno de pruebas** (`WOD_DEMO_MODE=1`, nunca producción por `demo_guard`, 1465): `POST /api/pruebas/entrar` (11554) abre
  sesión **sin contraseña** en cualquier cuenta `*.prueba`, sin mirar el rol; y `setup_allowed()` (2450) deja crear el primer
  administrador a quien llegue primero mientras no haya uno. Si el entorno de pruebas se publica en internet (o en una wifi
  compartida con `iniciar-pruebas-movil`), alguien puede adelantarse al titular. Corrección: en `/api/pruebas/entrar`
  rechazar `user['role']=='admin'`; para el alta inicial exigir un código de un solo uso impreso en la consola al arrancar.

---

## A05 · Configuración de seguridad incorrecta

### Qué se ha comprobado

| Comprobación | Evidencia | Resultado |
|---|---|---|
| Cabeceras en HTML, API, estáticos, 404 y redirecciones | `security_headers` (9817) en `send_json`, `send_file`, `send_bytes`, `redirect` y, por `end_headers` (9996), en cualquier otra respuesta (errores). CSP, `X-Frame-Options: DENY`, `frame-ancestors 'none'`, `nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`; `Cache-Control: no-store` en la API; HSTS con https. El widget es la única página enmarcable (`frame-ancestors *`, sin scripts). | **Correcto** (`test_a05_cabeceras_…`, `ConHttps`). |
| Arranque en producción | `check_production_settings` (14260): https obligatorio, `WOD_SECRET_KEY` y `WOD_DATA_KEY` ≥ 32, sin `WOD_ALLOW_SETUP`, sin `WOD_DEBUG`, TOTP obligatorio para administración. | **Correcto**, con una condición: solo se aplica con `WOD_ENV=production`; con `WOD_ENV` sin poner el servidor arranca como «development» aunque tenga dirección pública. Recomendación: tratar como producción cualquier `WOD_PUBLIC_URL` https que no sea `localhost` o 127.0.0.1. |
| Errores | Respuesta genérica en 500 (`detail` solo con `WOD_DEBUG`). | **Hallazgo A05-2** en los 409. |
| Versión del software | `Handler.server_version` (9746). | **Hallazgo A05-1**. |
| Zips de entrega | `scripts/generar_zips.py`: fuera `.env`, bases, subidas, registros; patrones de claves. | **Hallazgo A05-3**. |

### Hallazgo A05-1 · `Server: WORLDIVES Python/3.x` — **baja**

`BaseHTTPRequestHandler.version_string()` añade `sys_version`: todas las respuestas llevan `Server: WORLDIVES Python/3.13.x`.
Facilita buscar fallos conocidos de esa versión (detrás de nginx la cabecera se sustituye; detrás de Caddy, según la
configuración, puede pasar).

Reproducir: `curl -sI $BASE/api/health | grep -i server`.

Corrección (clase `Handler`, 9745):

```python
    server_version = 'WORLDIVES'
    sys_version = ''

    def version_string(self):
        return self.server_version
```

Prueba: `test_hallazgo_a05_cabecera_server_revela_la_version_de_python`.

### Hallazgo A05-2 · Errores de integridad con el detalle interno — **baja**

`do_POST` (13963-13965): `except sqlite3.IntegrityError as e: … self.send_json({…, 'detail': str(e)}, 409)`. Devuelve al
navegador nombres de tablas y columnas y los mensajes de los disparadores de aislamiento (`WOD: dato sin centro`,
`NOT NULL constraint failed: centers.country`…), útiles para tantear el esquema y las reglas de la base.

Reproducir (propietario de un centro): `POST /api/center/profile {"name":"x"}` → 409 con
`"detail":"NOT NULL constraint failed: centers.country"`.

Corrección (validada): `log_exception(self, e); self.send_json({'error':'El dato ya existe o no cumple una regla de integridad.'},409)`.

Prueba: `test_hallazgo_a05_error_de_integridad_devuelve_el_detalle_interno` (estática sobre el manejador).

### Hallazgo A05-3 · La comprobación de los zips no vigila todas las claves — **baja**

`SECRET_VARS` (`scripts/generar_zips.py:57`) obliga a que ciertas variables del `.env.example` vayan vacías, pero no incluye
`WOD_DATA_KEY`, `WOD_DATA_KEY_OLD`, `WHATSAPP_APP_SECRET` ni `WHATSAPP_VERIFY_TOKEN` (ni la futura `WOD_BACKUP_KEY`). Un
`.env.example` con la clave de cifrado rellena (p. ej. copiado del `.env` real) saldría en el zip sin aviso; las expresiones
de `SECRETS` tampoco la detectan (es un texto aleatorio).

Corrección: añadir `'WOD_DATA_KEY', 'WOD_DATA_KEY_OLD', 'WHATSAPP_APP_SECRET', 'WHATSAPP_VERIFY_TOKEN', 'WOD_BACKUP_KEY'` a
`SECRET_VARS`. Prueba: `test_hallazgo_generar_zips_no_vigila_todas_las_claves`.

Secretos en general (**correcto**): ningún secreto en el código ni en la web (`test_secretos_fuera_del_codigo_y_env_example_vacio`);
`.env` en `.gitignore`; `.env.example` con todas las claves vacías; el CI busca claves de Stripe/ArcGIS en el repositorio
(`.github/workflows/security-test.yml`); `DEMO_DATA_KEY` (`wod/cifrado.py:28`) solo para datos ficticios y rechazada en
producción (14270).

---

## A06 · Componentes vulnerables y obsoletos

### Hallazgo A06-1 · Versiones mínimas con CVE conocidas y sin fijar — **baja**

`requirements.txt` pide `cryptography>=42` (l. 7) y `Pillow>=10.0` (l. 9), sin límite superior ni hashes, y
`scripts/iniciar.py:31` (`ensure_requirements`) solo instala lo que **falta**: un servidor que ya tenga Pillow 10.0.0 lo
conserva. Pillow 10.0.0 lleva libwebp vulnerable (CVE-2023-4863, corregida en 10.0.1) y < 10.3.0 tiene CVE-2024-28219; el
servidor abre imágenes WebP/JPEG subidas por los centros (`wod/imagenes.py` y, con A02-3, `save_public_image`).
`cryptography` < 42.0.4 tiene CVE-2024-26130 (PKCS#12; no se usa, pero es el mínimo razonable). `stripe>=12,<13`,
`qrcode` y `fonttools` no tienen avisos aplicables al uso que se hace. El CI instala siempre la última versión, así que el
riesgo es de las instalaciones existentes.

Corrección: `cryptography>=42.0.4` y `Pillow>=10.3.0` (validado); mejor, un `requirements.lock` con versiones exactas y
`--require-hashes` (`pip-compile --generate-hashes`), `pip install -U -r` en el script de arranque y `pip-audit` en el CI.

Prueba: `test_hallazgo_a06_requirements_admite_versiones_vulnerables`. Las librerías del navegador (Leaflet y sus
complementos) están alojadas en el propio sitio (sin CDN), lo que la CSP exige.

---

## A07 · Fallos de identificación y autenticación

### Qué se ha comprobado

| Comprobación | Evidencia | Resultado |
|---|---|---|
| Límite de inicio de sesión | 8 fallos por IP+cuenta y 40 por IP en 15 min (`LOGIN_LIMIT`/`LOGIN_IP_LIMIT`, 1062-1063; ruta 11572-11591); `RateLimiter` seguro entre hilos y con memoria acotada (`wod/security.py:84`); IP real solo desde `WOD_TRUSTED_PROXIES`. | **Correcto** para una sola IP (`test_a07_inicio_de_sesion_limitado_por_ip_y_cuenta`). **Hallazgo A07-1** para muchas IPs. |
| Recuperación, restablecimiento, verificación de email | `FORGOT_LIMIT` 5/15 min por IP y por email (12282, 12293, 11658); misma respuesta exista o no la cuenta; enlace de 1 h y de un solo uso; restablecer cierra todas las sesiones. | **Correcto** (`test_a07_recuperacion_y_restablecimiento_limitados`, `test_a07_cambio_de_contrasena_…`). |
| Registro | `REGISTER_LIMIT` por IP (11499). | **Correcto** (`RegistroLimitado`). El registro dice «Ya existe una cuenta con ese email» (11518): enumeración aceptada a cambio de usabilidad y limitada por IP. |
| Segundo factor | TOTP RFC 6238, ventana ±1, sin reutilizar un código (`totp_last_step`), 6 intentos/15 min por cuenta al activar y al entrar (`login_second_factor`, 2652), obligatorio para administración en producción. | **Correcto** (`test_a07_segundo_factor_limitado`). |
| Sesiones | Token aleatorio de 256 bits, en la base solo su SHA-256; cookie `HttpOnly; SameSite=Lax; Path=/` y `Secure` con https, sin `Max-Age` (se borra al cerrar el navegador); caducidad absoluta de 8 h y por inactividad (`current_user`, 2349); salir borra la sesión en el servidor; cambiar la contraseña cierra las demás, restablecerla o cambiar el email o el rol las cierra todas. | **Correcto** (`test_a07_cookie_…`, `test_a07_cambio_de_contrasena_restablecimiento_y_salida_cierran_sesiones`). Mejora opcional: prefijo `__Host-` en la cookie. |
| Política de contraseñas | Mínimo 10, máximo 256, lista corta de contraseñas obvias (`wod/security.py: password_problem`). | **Correcto** (en línea con NIST 800-63B), salvo `/api/team/join` (abajo). |
| Tiempo de respuesta del login | 11579. | **Hallazgo A07-2**. |

### Hallazgo A07-1 · Sin límite por cuenta: fuerza bruta distribuida — **media**

La clave del límite es `f'{ip}:{login}'` y la de IP `f'ip:{ip}'` (11574-11580). Nada cuenta los fallos **de una cuenta**: con
30 IPs distintas se prueban 30 contraseñas contra la misma cuenta sin ningún 429, y con 1 000 IPs (botnet, proxies, o un /64
de IPv6, que el limitador trata como 2^64 IPs) son 8 000 intentos cada 15 minutos. La documentación (`docs/seguridad.md`)
dice «por cuenta y por IP».

Reproducir (servidor con `WOD_TRUSTED_PROXIES=127.0.0.1` para simular IPs):

```
for i in $(seq 1 30); do curl -s -o /dev/null -w '%{http_code} ' -H "X-Forwarded-For: 203.0.113.$i" -H "Origin: $BASE" \
  -H 'Content-Type: application/json' -d "{\"login\":\"diver_x\",\"password\":\"intento-$i\"}" $BASE/api/auth/login; done
# 401 ×30, nunca 429; después la contraseña buena desde otra IP entra (200)
```

Corrección (validada, `app/server.py`):

```python
LOGIN_ACCOUNT_LIMIT = wsec.RateLimiter(LOGIN_MAX_ATTEMPTS * 3, LOGIN_WINDOW_SECONDS)   # 24 fallos / 15 min por cuenta
...
                    acct_key='acct:'+login
                    if login_rate_limited(rate_key) or LOGIN_IP_LIMIT.blocked(ip_key) or LOGIN_ACCOUNT_LIMIT.blocked(acct_key):
                        self.send_json({'error':'Demasiados intentos. Espera unos minutos y vuelve a intentarlo.'},429); return
...
                    if not user or not ok_pw:
                        record_login_failure(rate_key); LOGIN_IP_LIMIT.hit(ip_key)
                        if LOGIN_ACCOUNT_LIMIT.hit(acct_key): security_alert('login_bruteforce', {'account': wsec.ip_hash(login)})
```

Funciona igual exista o no la cuenta (no revela cuáles existen). Contrapartida conocida: un atacante puede bloquear 15
minutos el inicio de sesión de una cuenta concreta; el titular sigue pudiendo restablecer la contraseña, y la alerta avisa
a la administración. Recomendado además: en `wod/security.client_ip`/`log_ip`, agrupar IPv6 por /64 en las claves de los
límites.

Prueba: `test_hallazgo_a07_fuerza_bruta_distribuida_contra_una_cuenta`.

### Hallazgo A07-2 · Enumeración de cuentas por tiempo de respuesta — **baja**

`if not user or not verify_password(password, user['password_hash'])` (11579): si la cuenta no existe no se calcula PBKDF2.
Con 600 000 iteraciones la diferencia en producción es de cientos de milisegundos (medido en pruebas, con 100 000: ~0,09 s
frente a ~0,03 s). El mensaje es el mismo, pero el tiempo dice qué emails están registrados (útil para A07-1 y para
phishing dirigido a clientes de buceo).

Corrección (validada):

```python
_DUMMY_HASH = []
def dummy_password_hash():
    if not _DUMMY_HASH: _DUMMY_HASH.append(wsec.hash_password(secrets.token_urlsafe(16)))
    return _DUMMY_HASH[0]
...
                    ok_pw=verify_password(password,user['password_hash'] if user else dummy_password_hash())
                    if not user or not ok_pw:
```

Prueba: `test_hallazgo_a07_enumeracion_de_cuentas_por_tiempo_de_respuesta` (mediana de 7 intentos; falla si la diferencia
supera 30 ms).

### Menores sin prueba automática (baja)

- **`/api/team/join` sin la política de contraseñas** (12701): solo `len(pw)<10`; no llama a `check_new_password` (máximo 256
  y lista de contraseñas obvias). Corrección: `check_new_password(pw)`.
- **Comprobación de la contraseña actual sin límite**: `/api/account/password` (13182), `/api/account/email` (11677) y
  `/api/account/totp/disable|recovery` (11613) verifican la contraseña sin limitador. Con una sesión robada se puede probar
  la contraseña sin freno (para luego entrar en otros sitios donde se repita). Corrección: `LOGIN_LIMIT.hit(f"pw:{user['id']}")`
  antes de verificar y 429 al superar el límite.

---

## A08 · Fallos de integridad del software y de los datos

| Comprobación | Evidencia | Resultado |
|---|---|---|
| Webhooks | Stripe con `Webhook.construct_event` y secreto (`stripe_webhook`, 7227; 503 sin secreto, 400 con firma falsa); WhatsApp con HMAC-SHA256 en tiempo constante (`wod/whatsapp.py:192`, 403 y alerta); verificación de Meta solo con `WHATSAPP_VERIFY_TOKEN`. | **Correcto** (`test_a08_webhooks_e_integracion_exigen_firma_o_clave`). |
| API de integración | Clave `wod_`+256 bits, solo su SHA-256 en la base; el centro sale de la clave, nunca del cuerpo (11998). | **Correcto**. |
| Subidas | Tipo por los primeros bytes (`sniff_document`, `wod/security.py:286`; `IMAGE_SIGNATURES`, 2860): PDF/JPG/PNG/WEBP; SVG, HTML y GIF rechazados; extensión elegida por el servidor y nombre aleatorio; límites por `Content-Length` antes de leer (JSON 1 MB, multipart 15 MB, documentos 10 MB, imágenes 6 MB; `precheck_write`, 11398); documentos privados fuera de `public/` (`save_upload`, 2245) con `0600`; descargas con `Content-Disposition`, `no-store` y control de acceso; servidos siempre con su tipo y `nosniff`. | **Correcto** (`test_a08_subidas_comprueban_contenido_tamano_y_tipo_servido`: un PNG con HTML detrás se guarda como `.png` y se sirve `image/png` + `nosniff`). Ver A02-3 (metadatos). |
| Cadena de suministro | Dependencias sin hashes ni versiones fijas (A06-1); el CI compila y pasa pruebas; el service worker y los recursos llevan la versión. | Ver A06-1. |

---

## A09 · Fallos de registro y monitorización

### Qué se ha comprobado

`log_message` (9750): sin cadena de consulta, IP truncada (/24, /48) salvo `WOD_LOG_IP=full`, rotación diaria y 14 días
(`wod/ops.py`); errores 500 con traza en stderr y alerta por correo si se repiten (`ErrorMonitor`); `audit_log` de inicio de
sesión, cambios de contraseña, exportaciones, accesos a documentos, accesos de la administración con motivo, teléfonos
vistos (`log_phone_access`); alertas de seguridad sin teléfonos ni tokens (`security_alert`, 2301). **Correcto**
(`test_a09_registro_de_accesos_sin_consulta_ni_ip_completa`). En desarrollo sin SMTP, `spool_outbox_to_files` (6228) escribe
los correos (con enlaces) en disco: solo desarrollo, pero que no se active en producción.

### Hallazgo A09-1 · Tokens de la ruta en `access.log` — **baja**

`log_message` quita `?…` pero no los secretos que van **en la ruta**: `/ical/<ical_token>.ics` (calendario privado de
reservas del centro: nombres de clientes; el token no caduca), `/r/<enlace firmado>` y `/api/r/<enlace firmado>` (abren una
reserva sin sesión). Quien lea `logs/access.log` (administrador del sistema, copia de registros, herramienta de
monitorización) obtiene esos accesos.

Reproducir: `curl $BASE/ical/ABCDEF…xyz.ics; grep ABCDEF logs/access.log`.

Corrección (validada, en `log_message` tras quitar la consulta):

```python
            line = re.sub(r'(/ical/)[^/\s"]+(\.ics)', r'\1***\2', line)
            line = re.sub(r'(/(?:api/)?r/)[^/\s"]+', r'\1***', line)
```

Prueba: `test_hallazgo_a09_tokens_de_la_ruta_quedan_en_el_registro`.

### Hallazgo A09-2 · Inicios de sesión fallidos sin auditoría ni alerta — **baja**

Un 401 o un 429 del login (11576-11580) solo deja una línea anónima en `access.log`; `audit_log` registra los inicios
correctos (`login`) y los fallos de TOTP, pero no los de contraseña, y no hay alerta al alcanzar el límite. Un ataque contra
una cuenta (A07-1) pasa desapercibido.

Corrección (validada): en la rama de fallo,
`if user: audit(db,user['id'],'login_failed',details={'ip':wsec.ip_hash(ip)}); db.commit()` y
`security_alert('login_bruteforce', …)` cuando salte el límite por cuenta (A07-1); añadir la etiqueta a
`SECURITY_ALERT_LABELS`. Prueba: `test_hallazgo_a09_intentos_fallidos_de_inicio_de_sesion_sin_auditoria`.

### Hallazgo A09-3 · Enlaces de un solo uso legibles en Administración → Correos — **baja**

Los cuerpos de `email_outbox` están cifrados en la base (5969), pero se descifran al leerlos y
`GET /api/admin/emails/<id>` (10335-10339) devuelve el `text` y el `html` completos: el enlace de restablecimiento
(`#/restablecer?token=…`, válido 1 h), el de verificación de email, el de invitación al equipo (7 días) y el de borrado de
cuenta. Un administrador (o quien tenga su sesión) entra en cualquier cuenta sin que quede como acción suya: en
`audit_log` figura `password_reset_done` del propio usuario. Verificado: el token leído en la vista de administración sirve
para cambiar la contraseña del buceador.

Corrección (validada): enmascarar los tokens al devolver el correo:

```python
                    it=dict(r)
                    for k in ('text','html'): it[k]=re.sub(r'([?&](?:t|token)=)[A-Za-z0-9_\-]{12,}', r'\1***', it.get(k) or '')
                    self.send_json({'item':it}); return
```

y, mejor, guardar ya enmascarado (o vaciar `text`/`html`) en las plantillas con enlace de un solo uso una vez enviado el
correo; `/api/admin/emails/resend` debe generar un enlace nuevo en vez de reenviar el antiguo.
Prueba: `test_hallazgo_a09_enlace_de_restablecimiento_legible_en_administracion`.

---

## A10 · Falsificación de peticiones del lado del servidor (SSRF)

| Comprobación | Evidencia | Resultado |
|---|---|---|
| Lecturas de webs de terceros (vídeos, miniaturas, Wikimedia) | `wod/remoto.py`: solo `https://` al puerto 443, sin usuario/contraseña ni IP literal (`check_url`, 54); todas las IP del nombre deben ser públicas (`public_host`, 38); redirecciones sin seguir automáticamente y comprobadas una a una (máx. 3); tiempo y tamaño máximos y tipo de contenido esperado. Solo administración, centros y freelance, 60 comprobaciones/10 min por persona (`marina_rate`, 2906). | **Correcto** (`test_a10_ssrf_direcciones_internas_rechazadas`, `test_a10_guardia_ssrf_de_wod_remoto`: 127.0.0.1, `localhost`, 169.254.169.254, `[::1]`, 10.x, puertos, `file:`, `gopher:`, `http:`). |
| Teselas de satélite, geocodificación, push, WhatsApp, Stripe | Hosts fijos de la configuración; en las teselas solo enteros en la ruta (10270). | **Correcto**. |

Observación (sin hallazgo): `public_host()` resuelve el nombre y `urlopen` lo vuelve a resolver (posible DNS rebinding);
queda neutralizado porque solo se admite https con verificación de certificado contra el nombre pedido, de modo que una IP
interna no presenta un certificado válido. Si algún día se admite `http://`, conectad a la IP ya comprobada.

---

## Copias de seguridad, secretos y dependencias (resumen)

- **Copias**: existen, se comprueban, rotan, se envían fuera y se restauran (correcto); **no van cifradas** (A02-2, media).
- **Secretos**: solo en `.env` / entorno; `.env.example` vacío; nada en el código (correcto); la comprobación de los zips no
  vigila cuatro claves (A05-3, baja).
- **Dependencias**: mínimos con CVE y sin hashes (A06-1, baja).

---

## Anexo · Parche validado (aplicado en la v50.51)

Aplicado en una copia aparte de `app/`, `public/`, `scripts/` y `requirements.txt` (no en el repositorio): con él pasan las
46 pruebas de `test_v50_51_seguridad.py` y las suites antiguas citadas en el Resumen. Generado contra la copia de trabajo del
13/10/2026 a las 18:50 (v50.51 en curso); los números de línea de los `@@` son de esa copia.

### `app/wod/roles.py`

```diff
@@ -148,7 +148,8 @@
     ('cobros', _P('/api/bookings/refund', re.compile(r'/api/bookings/\d+/refund'))),
-    ('centro', _P('/api/provider/insurance', '/api/provider/cancellation-policy', '/api/provider/center-update', '/api/provider/center-showcase',
+    ('centro', _P('/api/provider/insurance', '/api/provider/cancellation-policy', '/api/center/cancellation-policy', '/api/center/profile',
+                  '/api/provider/profile', '/api/provider/avatar', '/api/provider/center-update', '/api/provider/center-showcase',
                   '/api/provider/center-cover', '/api/provider/center-gallery', '/api/center/integration', '/api/provider/ical', '/api/center/import',
@@ -157,7 +158,7 @@
-    ('estadisticas', _P('/api/provider/stats',)),
+    ('estadisticas', _P('/api/provider/stats', '/api/center/analytics')),
```

### `app/server.py`

```diff
@@ -1061,6 +1061,11 @@
 LOGIN_IP_LIMIT = wsec.RateLimiter(LOGIN_MAX_ATTEMPTS * 5, LOGIN_WINDOW_SECONDS)
+LOGIN_ACCOUNT_LIMIT = wsec.RateLimiter(LOGIN_MAX_ATTEMPTS * 3, LOGIN_WINDOW_SECONDS)
+_DUMMY_HASH = []
+def dummy_password_hash():
+    if not _DUMMY_HASH: _DUMMY_HASH.append(wsec.hash_password(secrets.token_urlsafe(16)))
+    return _DUMMY_HASH[0]
@@ -2675,7 +2680,7 @@ def check_totp_or_recovery(db, user, code):
-    step = wtotp.verify(user['totp_secret'], code, user['totp_last_step'] if 'totp_last_step' in user.keys() else None)
+    step = wtotp.verify(wcif.decrypt_secret(user['totp_secret']) or user['totp_secret'], code, user['totp_last_step'] if 'totp_last_step' in user.keys() else None)
@@ -2910,6 +2915,17 @@ def save_public_image(file_info, prefix):
     if not ext: raise ValueError('Formato no admitido. Usa una foto JPG, PNG o WEBP.')
+    try:
+        from PIL import Image
+        Image.MAX_IMAGE_PIXELS = 40_000_000
+        im = Image.open(io.BytesIO(content)); im.load()
+        out = io.BytesIO(); fmt = {'.jpg': 'JPEG', '.png': 'PNG', '.webp': 'WEBP'}[ext]
+        if fmt == 'JPEG' and im.mode not in ('RGB', 'L'): im = im.convert('RGB')
+        im.save(out, fmt, **({'quality': 90} if fmt != 'PNG' else {})); content = out.getvalue()
+    except ImportError:
+        pass
+    except Exception:
+        pass   # not decodable: kept as it came (only its first bytes were checked)
     PHOTOS.mkdir(parents=True,exist_ok=True)
@@ -9782,6 +9798,10 @@
 class Handler(BaseHTTPRequestHandler):
     server_version = 'WORLDIVES'
+    sys_version = ''
+
+    def version_string(self):
+        return self.server_version
@@ -9791,6 +9811,8 @@ def log_message(self, fmt, *args):
             if '?' in line: line = re.sub(r'\?[^\s"]*', '', line)
+            line = re.sub(r'(/ical/)[^/\s"]+(\.ics)', r'\1***\2', line)
+            line = re.sub(r'(/(?:api/)?r/)[^/\s"]+', r'\1***', line)
@@ -10374,7 +10396,9 @@  (GET /api/admin/emails/<id>)
                     if not r: self.send_json({'error':'Correo no encontrado'},404); return
-                    self.send_json({'item':dict(r)}); return
+                    it=dict(r)
+                    for k in ('text','html'): it[k]=re.sub(r'([?&](?:t|token)=)[A-Za-z0-9_\-]{12,}', r'\1***', it.get(k) or '')
+                    self.send_json({'item':it}); return
@@ -11620,11 +11644,16 @@  (POST /api/auth/login)
-                    if login_rate_limited(rate_key) or LOGIN_IP_LIMIT.blocked(ip_key):
+                    acct_key='acct:'+login
+                    if login_rate_limited(rate_key) or LOGIN_IP_LIMIT.blocked(ip_key) or LOGIN_ACCOUNT_LIMIT.blocked(acct_key):
                         self.send_json({'error':'Demasiados intentos. Espera unos minutos y vuelve a intentarlo.'},429); return
                     user=db.execute('SELECT * FROM users WHERE lower(email)=? OR lower(username)=?',(login,login)).fetchone()
-                    if not user or not verify_password(password,user['password_hash']):
-                        record_login_failure(rate_key); LOGIN_IP_LIMIT.hit(ip_key); self.send_json({'error':'Usuario o contraseña incorrectos.'},401); return
+                    ok_pw=verify_password(password,user['password_hash'] if user else dummy_password_hash())
+                    if not user or not ok_pw:
+                        record_login_failure(rate_key); LOGIN_IP_LIMIT.hit(ip_key)
+                        if LOGIN_ACCOUNT_LIMIT.hit(acct_key): security_alert('login_bruteforce', {'account': wsec.ip_hash(login)})
+                        if user: audit(db,user['id'],'login_failed',details={'ip':wsec.ip_hash(ip)}); db.commit()
+                        self.send_json({'error':'Usuario o contraseña incorrectos.'},401); return
@@ -11640,17 +11669,17 @@  (POST /api/account/totp/*)
-                        sec=wtotp.new_secret(); db.execute('UPDATE users SET totp_pending_secret=? WHERE id=?',(sec,u['id'])); db.commit()
+                        sec=wtotp.new_secret(); db.execute('UPDATE users SET totp_pending_secret=? WHERE id=?',(wcif.encrypt_secret(sec),u['id'])); db.commit()
-                        sec=u['totp_pending_secret']
+                        sec=wcif.decrypt_secret(u['totp_pending_secret']) or u['totp_pending_secret']
-                        db.execute('UPDATE users SET totp_secret=?,…',(sec,now(),step,…))
+                        db.execute('UPDATE users SET totp_secret=?,…',(wcif.encrypt_secret(sec),now(),step,…))
@@ -12923,6 +12952,7 @@  (POST /api/reports)
                     target=clean_text(data.get('target_url'),500) or ''
+                    if target and not target.startswith('#/'): target=wsec.clean_http_url(target,500) or ''
@@ -14010,7 +14040,7 @@  (do_POST, IntegrityError)
-                self.send_json({'error':'El dato ya existe o no cumple una regla de integridad.','detail':str(e)},409)
+                log_exception(self, e); self.send_json({'error':'El dato ya existe o no cumple una regla de integridad.'},409)
```

### `app/wod/backup.py` (A02-2)

```python
MAGIC = b'WODBK1\n'
CHUNK = 4 * 1024 * 1024


def _backup_key():
    """32-byte key from WOD_BACKUP_KEY (never the data key): None when not configured (development only)."""
    import hashlib
    raw = config.env('WOD_BACKUP_KEY')
    return hashlib.sha256(raw.encode('utf-8')).digest() if raw else None


def encrypt_file(path: Path) -> None:
    """Encrypts a finished copy in place with AES-256-GCM, chunk by chunk (each chunk authenticates its number and
    whether it is the last one, so a copy cannot be cut or reordered)."""
    key = _backup_key()
    if not key: return
    import secrets, struct
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM
    aes = AESGCM(key); tmp = path.with_name(path.name + '.enc-tmp')
    with open(path, 'rb') as fi, open(tmp, 'wb') as fo:
        fo.write(MAGIC); n = 0; block = fi.read(CHUNK)
        while True:
            nxt = fi.read(CHUNK); last = not nxt; nonce = secrets.token_bytes(12)
            ct = aes.encrypt(nonce, block, struct.pack('>Q?', n, last))
            fo.write(struct.pack('>I', len(ct)) + nonce + ct); n += 1
            if last: break
            block = nxt
    os.replace(tmp, path); os.chmod(path, 0o600)


def _plain_copy(path: Path, out: Path) -> None:
    """Writes the decrypted (and still gzip-compressed if it was) content of a copy to out."""
    import struct
    with open(path, 'rb') as fi:
        head = fi.read(len(MAGIC))
        if head != MAGIC:
            fi.seek(0)
            with open(out, 'wb') as fo: shutil.copyfileobj(fi, fo)
            return
        key = _backup_key()
        if not key: raise RuntimeError('Esta copia está cifrada: falta WOD_BACKUP_KEY.')
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        aes = AESGCM(key); n = 0
        with open(out, 'wb') as fo:
            while True:
                size = fi.read(4)
                if not size: raise RuntimeError('Copia cifrada incompleta.')
                ln = struct.unpack('>I', size)[0]; nonce = fi.read(12); ct = fi.read(ln)
                peek = fi.read(1); last = not peek
                if peek: fi.seek(-1, 1)
                fo.write(aes.decrypt(nonce, ct, struct.pack('>Q?', n, last))); n += 1
                if last: break
```

y: `encrypt_file(out)` al final de `backup_db` y de `backup_files` (tras el `chmod`); en `verify()` y `restore()`,
`_plain_copy(path, plain)` antes de descomprimir y leer de `plain` en lugar de `path` (borrando `plain` al terminar). El
nombre del archivo no cambia, así que `rotate()` sigue igual. Falta añadir `WOD_BACKUP_KEY` a `.env.example`, a
`check_production_settings` y a `SECRET_VARS` de `generar_zips.py`.

### `public/js/world-dives-v8.js` (A03-1)

Cuatro sustituciones: ``title:`Dar «${escapeHtml(p.title)}»` `` (2237), ``title:`Códigos de «${escapeHtml(p.title)}»` `` (2249),
``title:`Fotos de «${escapeHtml(t.name)}»` `` (4071), ``title:`Fotos · ${escapeHtml(point.name)}` `` (4095). Hay que subir la
versión de los recursos (`?v=` de `index.html` y `sw.js`) como en cualquier cambio de la web.

### `requirements.txt` y `scripts/generar_zips.py`

```diff
-cryptography>=42
+cryptography>=42.0.4
-Pillow>=10.0
+Pillow>=10.3.0

-SECRET_VARS = ('WOD_SECRET_KEY', 'STRIPE_SECRET_KEY', …
+SECRET_VARS = ('WOD_SECRET_KEY', 'WOD_DATA_KEY', 'WOD_DATA_KEY_OLD', 'WHATSAPP_APP_SECRET', 'WHATSAPP_VERIFY_TOKEN', 'WOD_BACKUP_KEY', 'STRIPE_SECRET_KEY', …
```

### Pruebas antiguas a adaptar con el parche

- `tests/test_e2_p7_auth.py:92`: el secreto TOTP pendiente va cifrado (A02-1): usar el `secret` de la respuesta de
  `/api/account/totp/setup` o `helpers.cifrado_for(self.server.env).decrypt_secret(valor)`.
