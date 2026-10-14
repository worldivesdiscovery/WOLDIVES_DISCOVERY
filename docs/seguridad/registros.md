# Registros, sucesos de seguridad y niveles de protección de los datos

Referencia: OWASP ASVS 5.0, V14.1 (protección de datos) y V16 (registros). Todas las horas de los registros van en
**UTC** (`…Z` o `+00:00`), sea cual sea `WOD_TIMEZONE`; la hora del servidor se mantiene con NTP (`timedatectl`).

## Dónde queda cada registro

| Capa | Dónde | Qué guarda | Formato | Plazo | Quién lo lee | Protección |
|---|---|---|---|---|---|---|
| Accesos de la aplicación | `logs/access.log` (`WOD_ACCESS_LOG=file`) | Una línea por petición: hora, IP recortada (/24 o /48), método, ruta **sin la consulta**, estado y tamaño. Los testigos de `/ical/…` y de los enlaces `/r/…` salen como `***` | Texto | 14 días (`WOD_LOG_RETENTION_DAYS`), rota cada noche | Quien administra el servidor | Permisos 640 (`UMask=0027`) |
| Errores y avisos del servidor | Salida de errores → diario del sistema (`journalctl -u worldives`) | Errores 500 con método y ruta (sin consulta) y su traza; líneas `[seguridad]`, `[correo]`, `[geocode]`, `[satelite]`, `[antivirus]`, `[mantenimiento]` | Texto | 30 días (`MaxRetentionSec` de journald, `GUIA-VPS.md`) | Quien administra el servidor | journald |
| Actividad (`audit_log`) | Base de datos | Ver «Sucesos» abajo | Columna `details` en JSON | 12 meses, siempre las últimas 300 (*Administración → Legal*) | La administración (*Actividad*); cada centro la de su equipo | Base de datos y copias cifradas |
| Proxy (Caddy) | `/var/log/caddy/worldives.log` | Petición sin `t`, `token`, `lat`, `lon` ni `q` en la consulta, sin la clave de integración, IP recortada; Caddy ya oculta `Cookie` y `Authorization` | JSON | 14 días | Quien administra el servidor | Archivo de sistema |
| Correos de aviso a la administración | Proveedor SMTP | Avisos de seguridad (como mucho uno cada 15 minutos por tipo) y de errores repetidos, sin teléfonos ni testigos | Correo | El buzón | La administración | TLS comprobado |

Los caracteres de control de una petición se escriben como `\xNN`: nadie puede inventar líneas ni colores en los
registros.

**Nunca se escriben**: contraseñas, cookies o testigos de sesión, códigos de verificación, claves, teléfonos en claro,
el contenido de los documentos, la consulta de la URL (puede llevar coordenadas, búsquedas o testigos) ni la IP completa
(salvo `WOD_LOG_IP=full`, que no se recomienda). En la actividad, las IP van como huella (`ip_hash`).

## Sucesos de seguridad

En la actividad (`audit_log`), con la persona cuando la hay, la huella de la IP, la ruta y el método:

| Suceso | Cuándo |
|---|---|
| `login`, `logout`, `login_failed`, `totp_failed` | Entrar, salir, contraseña o código equivocados |
| `security_alert` · `login_blocked` | Un inicio de sesión frenado por los límites de intentos |
| `security_alert` · `login_unknown_account` | Intento con una cuenta que no existe |
| `security_alert` · `login_bruteforce` | Una cuenta llega a su límite (también por correo a la administración) |
| `security_alert` · `current_password_failed` | «Contraseña actual» equivocada en un cambio sensible |
| `security_alert` · `access_denied` | Alguien con sesión pide algo que su papel no permite |
| `security_alert` · `csrf_blocked` | Petición de cambio desde otra web o sin origen |
| `security_alert` · `stripe_bad_signature`, `integration_bad_key`, `webhook_bad_signature` | Avisos de Stripe o de Meta con firma falsa, clave de integración errónea |
| `security_alert` · `upload_malware` | El antivirus encontró algo en un documento |
| `admin_center_access` | La administración abre datos de un centro (con el motivo) |
| `admin_sessions_closed`, `password_reset_done`, `totp_enabled`, `totp_disabled`… | Cambios de seguridad de una cuenta |

Los sucesos que pueden repetirse en ráfaga (los cuatro de los límites, accesos denegados, CSRF, firmas y claves) se
guardan como mucho una vez por minuto por tipo, persona, dirección y ruta, para que nadie pueda llenar el registro.

## Niveles de protección de los datos

| Nivel | Datos | En la base | En el móvil o el navegador | En los registros | Quién accede |
|---|---|---|---|---|---|
| **Alto** | Teléfonos y teléfono de emergencia, credenciales de WhatsApp y de avisos, secretos del autenticador | **Cifrados** (AES-256-GCM, `WOD_DATA_KEY`); la base se niega a guardar un teléfono en claro | El manifiesto del día para trabajar sin cobertura lleva teléfono y contacto de emergencia (**excepción**: hacen falta en el barco); se borra al cerrar sesión y al pasar el día | Nunca | Su dueño; el centro solo con reserva viva o ficha compartida; la administración con motivo |
| **Alto** | Documentos (titulación, seguro) y datos fiscales | Archivos fuera de la web con permisos 600; datos fiscales solo del propietario del centro | No se guardan | Nunca su contenido | Igual que arriba; los fiscales, solo el propietario y la administración |
| **Medio** | Nombre, email, reservas, notas, Log Book, puntos, firmas de descargos | En la base; copias de seguridad cifradas | La app guarda las reservas y el QR de check-in del buceador; se borran al cerrar sesión | Solo el número de la persona | Su dueño y el centro de la reserva |
| **Bajo** | Catálogo público: puntos, centros, servicios, salidas, reseñas | En la base | Caché de la web | — | Cualquiera |

Plazos de conservación: los de la política de privacidad ([`docs/legal/politica-privacidad.md`](../legal/politica-privacidad.md)),
que aplica `run_retention_jobs` cada día; las reservas de más de 6 años se quedan sin datos de contacto ni notas.
