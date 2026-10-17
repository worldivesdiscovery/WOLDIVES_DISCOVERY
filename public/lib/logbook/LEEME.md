# Dive Logbook (componente del logbook de buceo)

Componente embebible entregado por el titular el 15/10/2026 (zip «Dive Logbook · Personalizar»): `logbook.js`,
`logbook.css` y `assets/`. Lo usa la sección **Log Book** de la web (`#/logbook`) con los datos guardados en la cuenta
(`GET/PUT /api/logbook`, ver `app/wod/logbook.py`).

| Archivo | Origen | Licencia |
|---|---|---|
| `logbook.js`, `logbook.css` | zip del titular. En v50.57: las 4 fuentes desde `fuentes/` en lugar de Google Fonts. En v50.58: el pasaporte como un libro (páginas rectas, tapa, lomo, grosor de las hojas, sombra, pasar hoja arrastrando la esquina, una página en el móvil, hojas montadas al acercarse); código propio, sin librería de terceros | del titular |
| `assets/fuente/page-left.jpg`, `assets/fuente/page-right.jpg` | zip del titular, sin cambios (fotos en ángulo de un libro real) | del titular |
| `assets/page-left.*`, `assets/page-right.*` (WebP y JPG) | las dos de `fuente/`, rectas, sin la tapa ni el fondo de la foto, con la misma proporción (`scripts/fotos/preparar_paginas_logbook.py`) | del titular |
| `assets/leather.jpg`, `assets/paper.jpg`, `assets/page-whale.jpg` | zip del titular, sin cambios | del titular |
| `fuentes/*.woff2` | Cinzel, EB Garamond, Caveat e IBM Plex Mono (paquetes `@fontsource/*` 5.3.0 de npm) | SIL Open Font License 1.1 (`fuentes/OFL-*.txt`) |
| `land-50m.json` | `world-atlas` 2.0.2 de npm (Natural Earth, dominio público) | ISC (`LICENSE-world-atlas.txt`) |

Por qué se sirve todo desde la web: la política de seguridad (CSP) solo carga scripts, fuentes y datos del propio
dominio, y así ningún dato del visitante va a Google o a un CDN. El QR personal del pasaporte no usa la librería
externa `qrcode-generator`: la web le pasa la imagen hecha por el generador único de la web (`/api/logbook/qr.svg`).
