# WORLDIVES DISCOVERY v50.9 — Security hardening

- Seguridad interna reforzada sin cambiar los flujos de negocio.
- El password_hash nunca se devuelve por `/api/me`.
- Cookies de sesión HttpOnly + SameSite=Lax y Secure automático bajo HTTPS.
- Sesiones con expiración configurable (8 h por defecto).
- Protección de origen para peticiones POST/DELETE con Origin/Referer.
- Rate limit básico de login (8 intentos / 15 min por IP + identificador).
- Cabeceras de seguridad HTTP.
- Servidor local enlazado a 127.0.0.1 por defecto; el modo LAN lo habilita explícitamente.
- `.gitignore`, `SECURITY.md` y workflow de comprobaciones para GitHub.
- Eliminados sidecars WAL/SHM del paquete de distribución.
