# WORLDIVES DISCOVERY — seguridad

## Baseline aplicado

- Las sesiones usan tokens aleatorios de alta entropía, cookies `HttpOnly` y `SameSite=Lax`.
- En despliegues HTTPS, la cookie de sesión puede marcarse automáticamente como `Secure`.
- Las sesiones expiran por inactividad/antigüedad mediante `WOD_SESSION_TTL_SECONDS` (8 horas por defecto).
- Las peticiones `POST` y `DELETE` con cabecera `Origin` se comprueban contra el origen público configurado para reducir CSRF.
- Se añaden cabeceras `X-Content-Type-Options`, `X-Frame-Options`, `Referrer-Policy` y `Permissions-Policy`; HSTS se activa cuando `WOD_PUBLIC_URL` usa HTTPS.
- El servidor local escucha en `127.0.0.1` por defecto. El lanzador LAN lo expone explícitamente en `0.0.0.0` solo cuando se solicita.
- Los documentos privados permanecen fuera de `/public`; `/storage/` no se sirve directamente.
- Las consultas SQL de entrada usan parámetros; no se construyen consultas con valores de usuario concatenados en los endpoints auditados.
- Las credenciales Stripe y secretos de webhook se leen desde variables de entorno y no deben entrar en Git.
- `.gitignore` excluye secretos, archivos runtime y los sidecars WAL/SHM de SQLite.

## Antes de producción

1. Usar HTTPS real y configurar `WOD_PUBLIC_URL` con `https://...`.
2. Definir `STRIPE_SECRET_KEY`, `STRIPE_WEBHOOK_SECRET` y `WOD_PUBLIC_URL` únicamente en el entorno del servidor.
3. No subir `.env`, bases de datos de producción ni `storage/` al repositorio.
4. Ejecutar la aplicación detrás de un proxy HTTPS/reverse proxy y con copias de seguridad de SQLite.
5. Revisar dependencias y actualizarlas periódicamente.
6. Configurar límites y observabilidad del servidor de producción (rate limiting, logs centralizados, backups y alertas).

Este archivo describe una línea base de endurecimiento; no sustituye una auditoría de penetración independiente antes de un lanzamiento comercial de gran escala.
