# Estructura del proyecto y plan de separación en módulos

## Carpetas (desde v50.45)

| Carpeta | Qué contiene | ¿Va en producción? |
|---|---|---|
| `app/` | Servidor (`server.py`), módulos `app/wod/`, plantillas de correo, textos legales y tipografías del PDF | Sí |
| `public/` | La web: `index.html`, `assets/js`, `assets/css`, imágenes, marca (`assets/brand/`), `manifest`, `sw.js` | Sí |
| `data/seed/` | Semilla del catálogo (`catalogo.sqlite3`): países, tipos, zonas, certificaciones, puntos, destinos y textos legales. Sin personas | Sí (la crea `build_release`) |
| `data/demo/` | Catálogo de demostración para las pruebas automáticas | Solo pruebas |
| `data/pruebas/` | Base del entorno de pruebas, correos guardados y copias | Solo pruebas (nunca en el repositorio) |
| `docs/` | Documentación, encargos, entregas, marca, legal | Sí (sin `docs/pruebas/`). Las capturas no van en ningún zip |
| `scripts/` | `build_release.py` (zips y comprobación), `crear_admin`, `crear_demo.py`, `reset_demo`, `start_pruebas` | Producción: solo `build_release` y `crear_admin` |
| `tests/` | Pruebas de API y de navegador (se ejecutan con el zip de pruebas, que trae el catálogo de demostración) | Sí |
| `tools/` | Herramientas (base de producción, marca, traducciones, prueba de carga) | Sí, salvo la de centros ficticios |
| `deploy/` | Plantillas de servidor (systemd, Caddy/nginx, copias) | Sí |
| `movil/` | Recursos de la app (Capacitor, Google Play, App Store) | Sí |
| `archive/` | Archivos retirados (logo anterior, notas antiguas). Fuera de `public/` | No |

La base de datos **se crea sola en el primer arranque**: a partir de `data/seed/catalogo.sqlite3` si existe. Si no
existe y no es producción, a partir del catálogo de demostración. Con `WOD_EMPTY_DB=1`, la base empieza vacía.

## Plan de separación en módulos

`app/server.py` (unas 12 000 líneas) y `public/assets/js/world-dives-v8.js` (unas 5 300) siguen siendo grandes.
Se separan **poco a poco, una zona por versión**, sin cambiar el comportamiento. Cada paso:

1. mueve funciones a un módulo nuevo y deja en `server.py` solo la llamada;
2. no cambia rutas, nombres de campos ni textos;
3. pasa la batería completa de pruebas antes de entregar.

Ya separado: `wod/config`, `security`, `totp`, `pdf`, `backup`, `ops`, `bookings` (estados), `manifest`, `pointtext`,
`agenda` (v50.44) y **`money` (v50.45: importes y monedas para Stripe)**.

| Versión | Servidor (`app/wod/…`) | Web (`public/assets/js/…`) |
|---|---|---|
| v50.46 | `payments.py`: Stripe Connect, checkout, webhooks, reembolsos | `wd-pagos.js`: cobros y reembolsos del panel |
| v50.47 | `emails.py`: cola, plantillas, envío SMTP y a archivo | `wd-i18n.js`: traducción del DOM y patrones |
| v50.48 | `catalog.py`: puntos, destinos, mapas | `wd-mapa.js`: mapa, capas y marcadores |
| v50.49 | `providers.py`: centros, freelance, planes, equipo | `wd-panel.js`: panel del centro y del freelance |
| v50.50 | `accounts.py`: registro, sesiones, perfil, privacidad | `wd-cuenta.js`: cuenta, Log Book y puntos |
| v50.51 | `admin.py`: administración y denuncias | `wd-admin.js`: administración |
| v50.52 | `routes.py`: tabla de rutas en lugar de la cadena de `if path==…` | `wd-app.js`: arranque y rutas |

La web seguirá sin compilación: cada archivo se carga con `<script defer>` en orden y se añade al `sw.js`.
Si una versión trae mucho trabajo de producto, el paso de separación se aplaza a la siguiente; nunca se mezclan dos
zonas en la misma entrega.
