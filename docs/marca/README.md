# Marca WORLDIVES DISCOVERY (desde v50.45)

## Nombre

Siempre **WORLDIVES DISCOVERY** o, en corto, **WORLDIVES**, en mayúsculas. No se usan otras grafías: ni separado en
dos palabras, ni con mayúscula y minúscula, ni siglas. La comprobación final de v50.45 no encuentra ninguna fuera de
`_archivo/` (archivos retirados) y de las capturas «antes».

## Logo

Los originales aprobados están en `docs/marca/originales/` (icono de la app y logo completo). Todas las variantes se
generan con `python scripts/marca/generar_marca.py`, sin redibujar nada: solo se quita el fondo blanco, se recorta, se
escala y se compone. El océano del globo es blanco en el original y se mantiene blanco.

**En la web** (`public/img/marca/`, solo los 11 archivos que la web usa):

| Uso | Archivo |
|---|---|
| Logo horizontal de la cabecera | `worldives-logo-horizontal-96.webp` |
| Logotipo de solo texto, para fondos oscuros (inicio de sesión, registro, recuperar contraseña y pie) | `worldives-logotipo-oscuro-260.webp` |
| Icono de la app (PWA) | `worldives-icono-192.png`, `worldives-icono-512.png` y `worldives-icono-maskable-512.png` |
| Favicon | `favicon.ico` (16, 32 y 48 px) y `favicon-32.png` |
| iPhone y iPad | `apple-touch-icon-180.png` |
| Correos (cabecera Abismo) | `worldives-icono-correo-96.png` |
| PDF (recibos, ficha, descargo) | `worldives-icono-pdf.jpg` |
| Compartir en redes (og:image) | `og-image-1200x630.png` |

**Kit de marca** (`docs/marca/kit/`, para diseño, imprenta y redes; no se sirve en la web), cada archivo en PNG y WebP:

| Carpeta | Qué hay |
|---|---|
| `logo/` | Logo vertical (claro, oscuro, `-520` y `-240`), horizontal (claro, oscuro y `-96`) y logotipo de solo texto (claro, oscuro y `-260`) |
| `simbolo/` | Símbolo (globo y buceador) en tamaño original, 512, 256, 128 y 64 px |
| `iconos/` | Iconos de la app en WebP |
| `redes/` | Imagen para compartir en JPG |

App y tiendas (`docs/marca/app/`): `icon-only.png` (1024), `icon-foreground.png` y `icon-background.png` (iconos
adaptables de Android), `splash.png` y `splash-dark.png` (2732), `google-play-icono-512.png`,
`google-play-grafico-1024x500.png` y `app-store-icono-1024.png` (sin transparencia, como pide Apple).

**SVG:** pendiente. Los originales son JPG y un trazado automático no sería fiel al dibujo. Lo debe vectorizar un
diseñador a partir del archivo original.

**Logo anterior:** retirado de `public/` y guardado en `_archivo/marca-anterior/`. Las direcciones antiguas ya no
responden.

## Logo una sola vez por pantalla (v50.46)

El símbolo (globo y buceador) aparece **como mucho una vez en cada pantalla**. La cabecera ya lo muestra en el logo
horizontal, así que el resto de la página usa solo el texto de la marca o nada:

- **Inicio de sesión, registro y recuperar contraseña:** junto al formulario va el logotipo de solo texto con el lema
  «Tu buceo, en un solo sitio». La cabecera se queda como está.
- **Pie de página:** logotipo de solo texto.
- **Correos y PDF:** llevan el icono una sola vez, en la cabecera.
- **Portada, paneles y administración:** solo el logo de la cabecera.
- **Pantalla de carga de la app:** el logo una vez (`docs/marca/app/splash.png`).

La prueba `tests/navegador/e2e_legal_logo.py` comprueba en móvil y ordenador que ninguna de las pantallas revisadas muestra
el símbolo dos veces.

## Paleta

| Nombre | Color | Variable CSS | Uso |
|---|---|---|---|
| Abismo | `#011C3C` | `--wd-abismo` | Texto principal, cabecera de correos, pie, barra del navegador, PDF |
| Profundo | `#043D6C` | `--wd-profundo` | Botón al pasar el ratón, títulos sobre claro |
| Océano | `#076898` | `--wd-oceano` | Botón principal, enlaces, acentos |
| Turquesa | `#1CA5C7` | `--wd-turquesa` | Detalles, iconos, barra de color de los correos (nunca texto sobre blanco) |
| Agua clara | `#87E2EF` | `--wd-agua` | Texto sobre Abismo («DIVES», pie, PDF) |
| Espuma | `#FFFFFF` | `--wd-espuma` | Fondos y texto sobre oscuro |
| Degradado | Océano → Turquesa | `--wd-degradado` | Bandas y elementos destacados |

Los colores se escriben **una sola vez**, en las variables de `:root` de `world-dives-v8.css`. El resto del CSS usa
`var(--wd-…)`. Se mantienen aparte, a propósito, los colores que significan otra cosa: tipos de servicio, temas de
temporada y los acentos de los carteles.

**Temas:** la web tiene un único tema con temas de imagen por temporada. No existen temas «Clásico» ni
«Futurista»; la paleta se aplica al tema único.

## Contraste (mínimo 4,5:1 para texto)

| Combinación | Contraste |
|---|---|
| Texto Abismo sobre fondo papel | 15,36:1 ✔ |
| Texto Abismo sobre blanco | 17,04:1 ✔ |
| Texto secundario (gris) sobre papel | 4,58:1 ✔ |
| Botón principal: blanco sobre Océano | 6,10:1 ✔ |
| Botón al pasar: blanco sobre Profundo | 11,12:1 ✔ |
| Enlaces Océano sobre blanco / sobre papel | 6,10:1 / 5,50:1 ✔ |
| Blanco sobre Abismo | 17,04:1 ✔ |
| Agua clara sobre Abismo | 11,48:1 ✔ |
| Turquesa sobre Abismo | 5,89:1 ✔ |
| Texto del pie sobre Abismo | 10,42:1 ✔ |
| Turquesa sobre blanco | 2,89:1: **solo decoración**, nunca texto |

## Tipografía

No ha cambiado (Inter para el texto y Georgia para los títulos). Cambiarla necesita aprobación.

## Capturas

Antes y después, en ordenador y en móvil, correo y PDF: `docs/capturas/marca-v50-45/antes/` y `/despues/`.
