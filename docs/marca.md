# Marca WORLDIVES DISCOVERY (desde v50.45)

## Nombre

Siempre **WORLDIVES DISCOVERY** o, en corto, **WORLDIVES**, en mayúsculas. No se usan otras grafías: ni separado en
dos palabras, ni con mayúscula y minúscula, ni siglas. La comprobación final de v50.45 no encuentra ninguna fuera de
`archive/` (archivos retirados) y de las capturas «antes».

## Logo

Los originales aprobados están en `docs/marca/originales/` (icono de la app y logo completo). Todas las variantes se
generan con `python tools/brand/build_brand.py`, sin redibujar nada: solo se quita el fondo blanco, se recorta, se
escala y se compone. El océano del globo es blanco en el original y se mantiene blanco.

| Uso | Archivo (`public/assets/brand/`) |
|---|---|
| Logo vertical (fondos claros) | `worldives-logo-vertical` (.png/.webp) y `-520` |
| Logo vertical para fondos oscuros (letras blancas, «DIVES» en Agua clara) | `worldives-logo-vertical-oscuro` y `-240` (pie de página, inicio de sesión) |
| Logo horizontal (cabecera de la web) | `worldives-logo-horizontal` y `-96` |
| Logo horizontal para fondos oscuros | `worldives-logo-horizontal-oscuro` y `-96` |
| Símbolo (globo y buceador) | `worldives-simbolo` y `-512`, `-256`, `-128`, `-64` |
| Icono de la app (PWA) | `worldives-icono-512`, `worldives-icono-192`, `worldives-icono-maskable-512` |
| Favicon | `favicon.ico` (16, 32 y 48 px) y `favicon-32.png` |
| iPhone / iPad | `apple-touch-icon-180.png` |
| Correos (cabecera Abismo) | `worldives-icono-correo-96.png` |
| PDF (recibos, ficha, descargo) | `worldives-icono-pdf.jpg` |
| Compartir en redes (og:image) | `og-image-1200x630` (.png/.jpg) |

App y tiendas (`movil/assets/`): `icon-only.png` (1024), `icon-foreground.png` y `icon-background.png` (iconos
adaptables de Android), `splash.png` y `splash-dark.png` (2732), `google-play-icono-512.png`,
`google-play-grafico-1024x500.png` y `app-store-icono-1024.png` (sin transparencia, como pide Apple).

**SVG:** pendiente. Los originales son JPG y un trazado automático no sería fiel al dibujo. Lo debe vectorizar un
diseñador a partir del archivo original.

**Logo anterior:** retirado de `public/` y guardado en `archive/marca-anterior/`. Las direcciones antiguas ya no
responden.

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
