# Ficha de revisión: Política de cookies y servicios de terceros

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

## Texto publicado

- Castellano (referencia): `app/legal/es/cookies.md`. Inglés (oficial): `app/legal/en/cookies.md`.
- Ruta pública: `#/legal/cookies`. Enlazada en el pie y desde el aviso de cookies (`cookieNotice()` en `public/js/world-dives-v8.js`).
- No necesita aceptación (no está en `LEGAL_ACCEPTANCE`): solo se usan cookies y almacenamiento técnicos (art. 22.2 LSSI-CE).

Esta ficha no repite el texto. Comprueba cada cookie, cada clave de almacenamiento y cada tercero contra el código.

## Método de comprobación

- Cookies: `grep Set-Cookie app/server.py` y `document.cookie` en el JS (no aparece).
- Almacenamiento: `grep localStorage|sessionStorage public/js/*.js` (solo `world-dives-v8.js` lo usa) y `public/sw.js` (Cache Storage).
- Terceros: CSP en `content_security_policy()` (`app/wod/security.py`), configuración de mapas `map_config()` (`app/server.py`, `GET /api/map/config`), vídeos en `DEFAULT_EMBED_DOMAINS` (`app/wod/config.py`) y, desde la v50.50, en `PLATFORMS` (`app/wod/videos.py`) y búsqueda de URLs `https://` en `public/index.html` y el JS.

## Cookies

| Nombre | Dónde | Atributos reales | Duración real | ¿En el texto? |
|---|---|---|---|---|
| `wd_session` | `COOKIE = 'wd_session'`; se crea al iniciar sesión y se borra al cerrar (`Set-Cookie … Max-Age=0`) | `Path=/; HttpOnly; SameSite=Lax`, más `Secure` con HTTPS. Valor: token aleatorio; en la base solo su hash (`sessions.token_hash`) | Cookie de sesión del navegador (sin `Max-Age`). En el servidor caduca a las **8 horas desde el inicio**, aunque haya actividad (`SESSION_TTL_SECONDS = 28800`, comprobación de `created_at`) | Sí, pero dice «8 horas sin actividad» (ver desajustes) |

No hay ninguna otra cookie propia. El JS no lee ni escribe `document.cookie`.

## Almacenamiento en el navegador

| Clave | Tipo | Qué guarda | Línea del JS | ¿En el texto? |
|---|---|---|---|---|
| `wod-language` (`LANG_KEY`) | localStorage | Idioma elegido | `LANG_KEY = 'wod-language'` | Sí («Idioma y filtros») |
| `wd_top10` | localStorage | `{geo:true}` si se usó «Usar mi ubicación» (sin coordenadas), o `{pick:{lat,lon,label}}` si se eligió un punto en el mapa o se buscó una localidad | `remember()` en el Top 10 | Sí, pero dice «ubicación y radio»: **el radio no se guarda** |
| `wd_cookie_notice` | localStorage | Fecha en que se cerró el aviso; el aviso vuelve a salir pasado 1 año | `cookieNotice()` | Sí |
| `wd_booking_draft` | sessionStorage | Reserva a medio hacer (centro y selección) para retomarla tras iniciar sesión; se borra al usarse | formulario de reserva | Sí |
| `wd_after_login` | sessionStorage | Página a la que volver tras iniciar sesión o registrarse | `renderLogin()`, `renderRegister()` | **No** |
| `wd_legal_later` | sessionStorage | Que el usuario pulsó «Más tarde» en el aviso de nuevas condiciones (documento y versión) | aviso de aceptación legal | **No** |
| `wd_theme_preview` | sessionStorage | Tema visual en vista previa (solo administradores) | `themePreviewId()` | **No** |
| `wd-i18n-debug` | localStorage (solo lectura) | Activa la auditoría de traducciones si alguien la pone a mano; la web nunca la escribe | línea 49 | No (no hace falta) |
| Caché `worldives-v50-38` | Cache Storage (service worker `public/sw.js`, registrado por `sw-register.js`) | Copia de la web (HTML, CSS, JS, iconos, Leaflet) para cargar más rápido y sin conexión. **Nunca** guarda respuestas de `/api/` ni teselas `/tiles/` | `public/sw.js` | **No** |

**No existen** «filtros de búsqueda» guardados: ninguna clave guarda filtros. El texto los menciona.

Todas las lecturas y escrituras van dentro de `try…catch`: si el navegador bloquea el almacenamiento, la web funciona igual.

## Terceros

### Política de seguridad del navegador (CSP)

`content_security_policy()` en `app/wod/security.py`:

| Directiva | Valor | Qué permite |
|---|---|---|
| `script-src` | `'self'` | Ningún script de terceros (Leaflet y Protomaps están en `/lib/`) |
| `style-src` | `'self' 'unsafe-inline'` | Sin hojas de estilo externas |
| `font-src` | `'self'` | Sin fuentes externas (no hay Google Fonts) |
| `img-src` | `'self' data: blob: https:` | **Cualquier imagen https** (ver desajustes) |
| `connect-src` | `'self'` + `WOD_CSP_EXTRA_CONNECT` + el origen de `WOD_PMTILES_URL` si es `https://` | Peticiones solo a nuestro servidor, salvo que se configure un CDN para el mapa |
| `frame-src` | Dominios de `WOD_EMBED_DOMAINS` (por defecto `youtube-nocookie.com`, `player.vimeo.com`, `google.com/maps`, y su variante `www.`) y, desde la v50.50, los reproductores de las plataformas insertables de `app/wod/videos.py` (`www.youtube-nocookie.com`, `player.vimeo.com`, `www.dailymotion.com`, `www.tiktok.com`, `www.facebook.com`, `www.instagram.com`; `WOD_VIDEO_EMBED_OFF` quita los que se indiquen) | Solo esos `iframe`, y solo después de pulsar «Reproducir» |
| `form-action`, `frame-ancestors`, `object-src` | `'self'`, `'none'`, `'none'` | — |

### Servicios que se cargan en el navegador

| Servicio | Cuándo se carga | ¿Recibe la IP del visitante? | Código | ¿En el texto? |
|---|---|---|---|---|
| Mapa base Protomaps (datos OSM) | Siempre que hay mapa | No: archivo PMTiles propio (`/tiles/worldives.pmtiles`). Si `WOD_PMTILES_URL` apunta a un CDN `https://`, el CDN sí recibe la IP | `map_config()`, `pmtiles_url()`, `docs/mapas.md` | Sí («desde nuestro servidor»); no prevé el CDN |
| Teselas de OpenStreetMap | **Solo fuera de producción** si falta el archivo PMTiles (`type: 'osm-dev'`) | Sí (`tile.openstreetmap.org`) | `map_config()`; `world-dives-v8.js` línea 191 | No (correcto, no se usa en producción) |
| Satélite Esri | Si se elige «Satélite» y hay clave | No: proxy `/api/tiles/satellite/{z}/{y}/{x}` | `sat_available()`, `ARCGIS_API_KEY`, `map_tile_usage` | Sí |
| Batimetría GEBCO | Si se elige la capa de profundidades | Sí (`https://wms.gebco.net/mapserv?`) | `map_config()['bathymetry']`, `L.tileLayer.wms` | Sí |
| YouTube (sin cookies), Vimeo, Google Maps | Solo tras pulsar «Cargar vídeo» en una experiencia virtual 360° | Sí, desde el clic | `wdEmbedAllowed()`, `#virtual-load` (línea 344), `clean_embed_url()` en el servidor | Sí |
| Stripe Checkout | Al pagar: la web **redirige** a la página de Stripe | Sí, en la página de Stripe | `create_stripe_checkout()` | Sí |
| Logotipos de centros por URL | Al ver la ficha o el directorio, **sin clic** | **Sí**, si el centro puso una URL `https://` externa en `logo_url` | `clean_local_or_http_url(data.get('logo_url'))` en las rutas de edición del centro; CSP `img-src https:` | **No** |
| Enlaces a Google Maps («Cómo llegar») y redes sociales | Solo si se pulsa el enlace (navegación normal) | Solo al pulsar | `world-dives-v8.js` (línea 1219 y perfiles) | No hace falta |

### Servicios que llama nuestro servidor (no reciben la IP del visitante)

| Servicio | Para qué | Código |
|---|---|---|
| Esri (ArcGIS) | Satélite por proxy | `/api/tiles/satellite/…` |
| Nominatim (OpenStreetMap Foundation) | Buscar una localidad; se envía solo el texto, con caché de 1 día | `/api/geocode` → `geocode_search()`, `WOD_GEOCODER_URL` |
| Stripe API | Pagos, cuentas conectadas, webhooks | `stripe_controller()` |
| Proveedor SMTP | Emails | `WOD_SMTP_HOST` |

El texto de cookies no menciona Nominatim. Como no recibe datos personales, basta con citarlo en la privacidad (registro de actividades, apartado 17).

## Desajustes entre el texto y el código

1. **`wd_session`, duración.** El texto dice «hasta cerrar sesión o 8 horas sin actividad». El servidor cierra la sesión a las 8 horas del inicio aunque haya actividad, y la cookie es de sesión del navegador. Corregir el texto («hasta cerrar sesión, cerrar el navegador o 8 horas como máximo») o el código.
2. **«Idioma y filtros».** No se guardan filtros. Dejar «Idioma» (`wod-language`).
3. **`wd_top10`.** No guarda el radio. Guarda si se usó la ubicación (sin coordenadas) o la posición elegida en el mapa o buscada. Ajustar el texto.
4. **Claves que faltan en la tabla:** `wd_after_login`, `wd_legal_later`, `wd_theme_preview` (sessionStorage) y la caché del service worker (Cache Storage). Todas técnicas, pero deben listarse.
5. **Logotipos externos sin clic.** El centro puede poner un logotipo por URL `https://` de otro servidor, y la CSP permite cualquier imagen `https:`. Ese servidor recibe la IP de cada visitante sin que lo pida, en contra de «Ningún contenido de terceros se carga sin que lo pidas». **[PENDIENTE TITULAR]**: aceptar solo logotipos subidos (`/assets/…` o `/uploads/…`) y limitar `img-src` a `'self' data: blob:` más el CDN del mapa; o descargar la imagen al servidor al guardarla.
6. **CDN del mapa.** Si se usa `WOD_PMTILES_URL=https://…` (opción documentada en `docs/mapas.md`), el CDN recibe la IP. El texto dice que el mapa base no envía nada a terceros. Si se usa un CDN, añadirlo.
7. **Google Maps en `frame-src`.** Solo se usa en experiencias virtuales tras el clic. Correcto; el texto lo dice.

## Puntos para el abogado

- **[PENDIENTE ABOGADO]** Confirmar que todo el almacenamiento listado es técnico y exento (art. 22.2 LSSI-CE, Guía de cookies de la AEPD de 2023), incluido `wd_top10` (preferencia elegida por el usuario) y la caché del service worker.
- **[PENDIENTE ABOGADO]** Si basta un aviso informativo con un solo botón («Entendido») cuando no hay cookies que requieran consentimiento.
- **[PENDIENTE ABOGADO]** GEBCO (servidores del British Oceanographic Data Centre, Reino Unido): la IP sale al cargar la capa, que el visitante elige. Confirmar que basta con informar (decisión adecuada de la Comisión para el Reino Unido).
- **[PENDIENTE ABOGADO]** Vídeos tras clic: si el botón «Cargar vídeo» con el aviso actual vale como consentimiento para las cookies que pongan Vimeo o Google Maps (YouTube se usa en su modo sin cookies).
- **[PENDIENTE ABOGADO]** Cookies de Stripe en su página de pago: responsabilidad de Stripe; confirmar que basta con mencionarlo.


## Actualización v50.50 (vídeos de la ruta)

- **Vídeos de la ruta** (`docs/vida-marina/README.md`):
  - la ficha del punto solo enseña una miniatura guardada en nuestro servidor;
  - el reproductor de la plataforma se carga al pulsar «Reproducir»;
  - YouTube va con `youtube-nocookie.com` y Vimeo con `dnt=1`.
- La fila de vídeos del texto público (`app/legal/*/cookies.md`, 9 idiomas) nombra ahora todas las plataformas
  insertables y el botón «Reproducir».
- **La política de privacidad no se ha cambiado.**
  - Hoy nombra YouTube, Vimeo y Google Maps como ejemplos.
  - Si se cambia, todos los usuarios tienen que aceptarla otra vez (`LEGAL_ACCEPTANCE`).
  - **Pendiente de decisión** (notas de la v50.50).
