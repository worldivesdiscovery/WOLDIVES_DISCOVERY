# WORLDIVES DISCOVERY — seguridad

## OWASP ASVS 5.0, nivel 2 (v50.51)

Revisión de los 253 requisitos de nivel 1 y 2 y arreglos: [`docs/auditoria/v50.51/asvs-5.0-nivel2.md`](auditoria/v50.51/asvs-5.0-nivel2.md).
Documentos de referencia que pide ASVS:

- [`seguridad/autenticacion.md`](seguridad/autenticacion.md): vías de autenticación, política de contraseñas, límites
  de intentos, bloqueo malicioso, sesiones y verificación en dos pasos.
- [`seguridad/permisos.md`](seguridad/permisos.md): qué puede leer y cambiar cada papel y cada perfil del equipo, y
  quién ve cada dato sensible.
- [`validacion.md`](validacion.md): formato de cada dato, coherencia, límites de negocio y archivos subidos.
- [`seguridad/claves.md`](seguridad/claves.md): inventario criptográfico y cómo se generan, guardan y cambian las claves.
- [`seguridad/registros.md`](seguridad/registros.md): qué se registra y dónde, sucesos de seguridad y niveles de
  protección de los datos.

## Dependencias

| Componente | Versión | De dónde sale | Cómo se revisa |
|---|---|---|---|
| Python | 3.11 o superior (la de Debian 12 / Ubuntu 24.04) | Paquetes del sistema | Actualizaciones de seguridad del sistema (`unattended-upgrades`) |
| Librerías de Python | Versiones exactas en `requirements.txt` (stripe, qrcode, fonttools, cryptography, Pillow) | PyPI | `pip-audit` cada lunes y en cada cambio (`.github/workflows/dependencias.yml`); el servidor instala exactamente esas versiones |
| App del móvil (Capacitor) | `movil/package-lock.json` | npm | `npm audit` en el mismo flujo semanal |
| Leaflet | 1.9.4 | leafletjs.com, copiado en `public/lib/leaflet` | A mano en cada versión (avisos de seguridad de Leaflet) |
| protomaps-leaflet | 5.1.0 (BSD-3) | github.com/protomaps, `public/lib/protomaps-leaflet` | A mano en cada versión |
| Leaflet.markercluster | 1.5.3 (MIT): `leaflet.markercluster.js` y `MarkerCluster.css` son idénticos byte a byte a los de npm (el `.js` es el mismo en 1.5.2 y 1.5.3; 1.5.3 es la última). SHA-256 del `.js`: `1e4e1d22972a3926f48598e0caf14e3fe7049835d428a344fed4f9e3665b3508` | github.com/Leaflet/Leaflet.markercluster, `public/lib/markercluster` | A mano en cada versión |

**Plazos de corrección** desde que se publica el aviso: crítica, 7 días; alta, 30 días; media y baja, en la versión
siguiente. Responsable: el titular del proyecto (o quien mantenga el servidor). Una dependencia sin mantenimiento se
sustituye. Fijar también los hashes de las librerías (archivo de bloqueo) y generar un SBOM con cada paquete queda
como **Pendiente de decisión** (más seguridad en la cadena de suministro a cambio de un paso más al actualizar).

## Aislamiento entre centros y datos cifrados (v50.47)

- **Cada dato privado lleva su centro.** El centro (o el freelance) de cada dato privado es obligatorio en la propia
  base de datos, con clave foránea, disparadores de coherencia e índices.
- **Una sola capa de consulta** (`app/wod/inquilinos.py`) que siempre filtra por el centro de la sesión.
- **Lo de otro centro da 404.** Los campos de centro que mande el navegador se ignoran y quedan registrados.
- **La administración da un motivo** para ver o cambiar datos de un centro, y queda registrado.
- **Teléfonos y credenciales de WhatsApp cifrados** (AES-256-GCM, `WOD_DATA_KEY`), con búsqueda por huella HMAC. La
  clave se cambia con `scripts/seguridad/rotar_clave_datos.py`.
- **Detalle:** auditoría, inventario de tablas y rutas, fallos corregidos y cómo se comprueba en cada versión, en
  `docs/seguridad/aislamiento-centros.md`.

## Medidas aplicadas (v50.31 a v50.38)

- **Sesiones** en la tabla `sessions` con el token guardado como hash SHA-256, caducidad de 8 h (`WOD_SESSION_TTL_SECONDS`), cookie `HttpOnly`, `SameSite=Lax` y `Secure` con https. Se cierran al cambiar la contraseña, el email o el rol; las caducadas se borran cada 10 minutos.
- **Contraseñas** con PBKDF2-SHA256 a 600 000 iteraciones y prefijo de versión (`pbkdf2_sha256$…`), con re-hash automático de las antiguas al iniciar sesión.
- **Límites de intentos** (seguros entre hilos y con memoria acotada) en inicio de sesión (por cuenta y por IP), registro, recuperación de contraseña, verificación de email, avisos y geocodificación.
- **CSRF:** todo POST/DELETE debe traer `Origin` o `Referer` del propio dominio (`WOD_PUBLIC_URL`), salvo los webhooks de Stripe y la API de integración (que se autentican con firma o clave).
- **Content-Security-Policy** en todas las respuestas: scripts solo propios, sin scripts en línea, iframes solo de los proveedores permitidos y cargados tras un clic.
- **Cabeceras:** `nosniff`, `X-Frame-Options: DENY`, `frame-ancestors 'none'`, `Referrer-Policy`, `Permissions-Policy`, `Cross-Origin-Opener-Policy`, HSTS con https.
- **Tamaño de las peticiones:** JSON 1 MB, subidas 15 MB (documentos 10 MB), comprobado con `Content-Length` antes de leer el cuerpo.
- **Documentos privados** fuera de `public/` (`WOD_STORAGE_DIR`), tipo comprobado por contenido, servidos con `private, no-store`, acceso solo del dueño, del centro con reserva del propio buceador o datos compartidos, y del administrador; cada descarga queda en `audit_log`.
- **Proxy de confianza:** `X-Forwarded-For/Proto` solo desde `WOD_TRUSTED_PROXIES`.
- **Registros** sin cadena de consulta, IP truncada, rotación diaria y conservación limitada.
- **SQL** siempre parametrizado.
- **Secretos** solo en variables de entorno (`.env`, nunca en el repositorio).
- **Verificación en dos pasos (TOTP, RFC 6238)** opcional para todos y obligatoria para la administración (v50.35); códigos de recuperación de un solo uso guardados con hash.
- **Equipos de centro (v50.37):** perfiles propietario, recepción e instructor comprobados en el servidor en un único punto (`team_gate`); los pagos, el plan, los datos fiscales y el equipo solo para el propietario.
- **Widget incrustable (v50.37):** `/widget/…` es la única ruta que puede mostrarse en otra web (`frame-ancestors *`), sin scripts ni formularios.
- **Claves de terceros en el servidor:** la clave de ArcGIS nunca llega al navegador (proxy de teselas con límite por IP y contador mensual).
- **Copias de seguridad (v50.38)** cada hora con la API de copia de SQLite, comprobadas, rotadas y enviadas fuera del servidor (`WOD_BACKUP_COMMAND`), con `quick_check` diario y avisos.
- **Instalación:** sin `WOD_ALLOW_SETUP=1` no existe el instalador web; el administrador se crea con `--create-admin`. En `WOD_ENV=production` el servidor no arranca con una configuración insegura.

## Antes de producción

1. Servidor detrás de Caddy o nginx con HTTPS y `WOD_TRUSTED_PROXIES` (ver `docs/despliegue/README.md`).
2. `WOD_ENV=production`, `WOD_PUBLIC_URL=https://…`, `WOD_SECRET_KEY` aleatoria.
3. Verificación en dos pasos activa para todas las cuentas de administración.
4. Copias de seguridad automáticas probadas con una restauración.
5. Monitor externo sobre `/api/health` y aviso de errores por email.
6. Pruebas: `cd tests && python -m unittest discover -p 'test_*.py'` y las pruebas en navegador `tests/navegador/e2e_*.py`.
7. Lista completa: `docs/legal/lista-lanzamiento.md`.

## Avisar de un problema de seguridad

Escribe al email de contacto del aviso legal indicando «Seguridad» en el asunto. No publiques el fallo hasta que esté corregido.

Este documento describe una línea base; no sustituye una auditoría de intrusión independiente antes de un lanzamiento comercial a gran escala.
