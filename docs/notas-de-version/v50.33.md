# WORLDIVES DISCOVERY v50.33: marcadores del mapa (Fase 1C) e idiomas (Fase 1D)

## Fase 1C · Marcadores
- **Redondos y más pequeños.** El punto de inmersión se dibuja como un círculo con la bandera de buceo dentro (rojo con la diagonal blanca) y borde blanco: **19 px en ordenador y 23 px en móvil**; el marcador activo (ficha abierta) sube a 26 px con un anillo turquesa (#12a5b5). Al pasar el ratón o seleccionarlo se ve el mismo anillo.
- **Zona de toque de 44 px en móvil** (28 px en ordenador) aunque el dibujo sea pequeño: se acierta con el dedo sin agrandar el icono.
- **Agrupación** con `leaflet.markercluster` 1.5.3 (alojado en `public/assets/vendor/markercluster`, licencia MIT): radio 42 px, se deshace a partir del zoom 11, carga por tandas. El grupo es un círculo rojo liso con borde blanco y el número; se lee igual sobre mapa y satélite.
- Cada marcador lleva `title` y texto alternativo con el nombre del punto (lectores de pantalla y teclado).
- El mismo marcador en el explorador, la ficha del punto, el editor de puntos y el mapa para elegir punto.

### Medidas (tests/e2e_markers.py)
| | v50.30 | v50.33 |
|---|---|---|
| Dibujo en ordenador | 15 × 11 px (bandera rectangular) | 19 × 19 px |
| Dibujo en móvil | 15 × 11 px | 23 × 23 px |
| Zona de toque en móvil | 16 × 13 px | 44 × 44 px |
| Elementos dibujados en la vista inicial (móvil) | un icono por punto | 7 (marcadores + grupos) |
| Fluidez al arrastrar el mapa, móvil emulado con CPU ×4 | — | 60 fotogramas, 0 por encima de 50 ms, media 17 ms |

Capturas antes/después en `docs/capturas/fase-1c/` (ordenador y móvil, mapa y satélite, mundo y zoom).
**Nota honesta:** en el entorno de pruebas no hay salida a los servidores de teselas, así que el fondo de las capturas es una tesela simulada (clara para «mapa», oscura para «satélite»). Sirve para juzgar tamaño y contraste, no el aspecto final del mapa. Conviene repetir las capturas en el servidor real.
Los marcadores de v50.30 eran más pequeños que los de ahora; el cambio de tamaño cumple las cifras del encargo (18–20 px y 22–24 px). Lo que más despeja el mapa es la agrupación.

## Fase 1D · Idiomas
- **10 idiomas**: español, English, français, Deutsch, italiano, português, **polski**, Nederlands, 中文(简体), **русский**. Selector con el nombre de cada idioma en su idioma.
- **Retirados japonés, coreano y chino tradicional.** Sus archivos pasan a `archive/i18n/` (no se borran). Quien los tenía elegidos pasa a inglés (ja, ko) o a chino simplificado (zt), en el navegador y en la base (`users.preferred_language` y correos en cola), migración `migrate_v50_33`.
- **Polaco y ruso completos en la web**: 3 812 frases y 426 patrones cada uno (`public/assets/i18n/pl.json`, `ru.json`).
- **Plurales correctos** con `Intl.PluralRules`: los patrones admiten formas `one/few/many/other` (necesarias en polaco y ruso: «1 punkt, 2 punkty, 5 punktów»).
- **Fechas, horas e importes** con el formato de cada idioma (pl-PL, ru-RU incluidos), en la web y en los correos.
- **Primera visita**: si no hay idioma elegido, se usa el del navegador cuando la web lo tiene (antes, siempre castellano).
- **URL por idioma**: `?lang=xx` fija el idioma (y se recuerda). El servidor pone `<html lang>` y las etiquetas `hreflang` de los 10 idiomas más `x-default` en cada página. En modo demo, además, `noindex`.
- **Limpieza**: eliminadas 47 claves basura (fragmentos de código) de cada archivo de traducción. Informe con lo que falta por idioma: `python tools/i18n_report.py` → `docs/i18n/informe.md`.
- **Modo de depuración** de traducciones: con `localStorage['wd-i18n-debug']='1'`, el navegador reúne en `window.__wdI18nMisses` los textos que no encontró traducidos.
- **Tipografía**: la web usa la fuente del sistema (cubre polaco, cirílico y chino). Los carteles para redes cargan además los subconjuntos latin-ext y cirílico de Inter (licencia OFL) para que el polaco y el ruso no mezclen fuentes.

### Pendiente en idiomas (se hará en la pasada final de traducción)
- Correos en polaco y ruso: hoy salen en inglés (194 textos).
- Los textos nuevos de la Fase 1 en adelante, los títulos de los controles del mapa y los textos legales se traducirán a los 9 idiomas al final, en una sola pasada revisada.
- Los PDF (justificantes) en ruso, polaco y chino necesitan fuentes incrustadas: se resuelve con el rediseño del justificante en la Fase 2.
- Recomendación: que un hablante nativo revise polaco y ruso antes de anunciarlos.

## Cómo se probó
- `python -m unittest test_units test_phase1_security test_phase1b_booking_modes` (en `tests/`).
- `python tests/e2e_walk.py`, `python tests/e2e_booking_modes.py`, `python tests/e2e_markers.py docs/capturas/fase-1c --before-root <checkout v50.30>`.
- `tests/test_phase1d_languages.py` (5 pruebas): `<html lang>` y `hreflang`, selector con 10 idiomas, archivos retirados, marcadores y etiquetas iguales en todas las traducciones, migración de usuarios y correos en cola.
- Recorrido en polaco, ruso y chino (ordenador y móvil) con el modo de depuración: sin errores; solo quedan sin traducir los textos nuevos de la Fase 1, las descripciones de los centros de demostración (contenido de cada centro) y los títulos en inglés de los botones de zoom de Leaflet. Capturas en `docs/capturas/fase-1d/`.
