# Ficha de revisión: Declaración de accesibilidad

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

## Texto publicado

- Castellano (referencia): `app/legal/es/accesibilidad.md`. Inglés (oficial): `app/legal/en/accesibilidad.md`.
- Ruta pública: `#/legal/accesibilidad`. Enlazada en el pie.
- No necesita aceptación. Se creó en v50.36 (`docs/notas-de-version/v50.36.md`, apartado 12; punto 5.12 del encargo).

Esta ficha no repite el texto. Resume cada afirmación, indica en qué parte del código se apoya, separa lo hecho de lo no hecho y lista lo que falta revisar.

## Lo que se ha hecho (y dónde está)

| Afirmación del texto | Dónde se apoya en el código | Estado |
|---|---|---|
| Cada campo asociado a su etiqueta | `wdLinkLabels()` en `public/js/world-dives-v8.js`: al dibujar cada pantalla (un `MutationObserver` lo lanza 60 ms después de cada cambio del DOM) enlaza cada `label` sin `for` con su campo (le da `id` `wdf-N` si no tiene) y da `aria-label` (del `placeholder` o `title`) a los campos que siguen sin etiqueta. Registro y reserva ya tenían etiquetas en el HTML | Hecho. Es una corrección en tiempo de ejecución: los formularios nuevos deberían escribir `for`/`id` en el HTML |
| Mensajes de error en texto | `toast()` y los mensajes de error del servidor en texto; 12 regiones `role="status"`/`role="alert"`/`aria-live` | Parcial: no se ha comprobado que todos los errores se anuncien a lectores de pantalla |
| Uso con teclado y foco siempre visible | Regla general `:focus-visible{outline:none;box-shadow:var(--ring)}` y reglas propias en `public/css/world-dives-v8.css`; de los 13 `outline:none`, los 3 sin anillo se corrigieron (buscador, marcadores, alto contraste). `<main id="app" tabindex="-1">` en `public/index.html`. Diálogos con `aria-modal` y cierre con Escape | Hecho para el foco. Uso completo con teclado: **no verificado** pantalla a pantalla |
| Modo de alto contraste de Windows | `@media (forced-colors:active)` con contorno `CanvasText` en el foco y los campos | Hecho |
| Movimiento reducido | `@media (prefers-reduced-motion:reduce)` (4 bloques: transiciones, modales, carrusel, portada) | Hecho (el texto no lo menciona) |
| Textos alternativos en imágenes y marcadores | Todas las `<img>` del JS y de `index.html` tienen `alt` (31 con `alt=""` como decorativas). Marcadores: `<span class="wd-pin" role="img" aria-label="…">` en el `L.divIcon` | Hecho. **No revisado** si cada `alt=""` es de verdad decorativa (p. ej. logotipos de centros) |
| Contraste suficiente | Colores en variables CSS (`--sea`, `--muted`…) | **No medido**: no hay informe de contraste |
| Zonas táctiles de 44 × 44 px en el móvil | `min-height:44px` en campos, botones de formularios y menú móvil (`@media` de móvil) | Parcial: no en todos los controles (chips, enlaces de texto, controles del mapa) |
| Declara el idioma de cada página | `<html lang="es">` en `index.html`; `document.documentElement.lang` se cambia con el idioma elegido (`zh` → `zh-Hans`). Los PDF llevan `/Lang` en el catálogo (`app/wod/pdf.py`) | Hecho |
| Contenidos de terceros solo a petición | Vídeos 360° tras «Cargar vídeo» (`#virtual-load`) | Hecho (ver `docs/legal/cookies-terceros.md`, salvo logotipos externos) |
| Alternativa al mapa | Lista `#/puntos` con buscador y filtros | Hecho |
| PDF con texto real, sin etiquetar | `app/wod/pdf.py` genera PDF con texto, fuentes incrustadas y `/Lang`, sin árbol de estructura (`StructTreeRoot`) | Coincide con el texto |

## Lo que NO se ha hecho

- **[PENDIENTE]** Auditoría formal WCAG 2.1 AA (o EN 301 549 v3.2.1) por una persona o empresa experta, con muestra de páginas e informe.
- **[PENDIENTE]** Prueba con lectores de pantalla reales (NVDA o JAWS en Windows, VoiceOver en macOS e iOS, TalkBack en Android).
- **[PENDIENTE]** Herramientas automáticas: el texto dice que se usaron, pero en el repositorio **no hay** ninguna (ni axe, ni pa11y, ni Lighthouse en `tests/` o `tools/`) ni informe guardado. Pasar axe-core a las pantallas principales y guardar el resultado, o quitar la frase.
- **[PENDIENTE]** Medición de contraste de todos los colores, incluidos los temas que la administración puede cambiar (*Administración → Temas*).
- **[PENDIENTE]** Recorrido completo solo con teclado: registro, búsqueda, ficha de centro, reserva y pago (la página de Stripe es de Stripe), «Mi cuenta», panel del centro y administración.
- **[PENDIENTE]** Enlace «Saltar al contenido»: no existe en `public/index.html`.
- **[PENDIENTE]** Landmarks: el panel del centro y la administración ponen un `<main class="cb-main">` **dentro** de `<main id="app">`. Dos `main` anidados confunden a los lectores de pantalla; cambiar el interior por `<div>` o `<section>`.
- **[PENDIENTE]** Anuncio de cambios de ruta en la SPA (título de página y foco al cambiar de pantalla): no comprobado.
- **[PENDIENTE]** Los emails (plantillas HTML) no se han revisado para accesibilidad.
- **[PENDIENTE]** No hay pruebas automáticas de accesibilidad en `tests/`.

## Desajustes entre el texto y el código

1. **«Herramientas automáticas de comprobación».** No hay rastro de ellas en el repositorio. Hacer la prueba y guardar el informe, o cambiar la frase.
2. **«Uso completo con teclado».** No está verificado; además falta el enlace de salto y hay `main` anidados. Mejor pasarlo a «Hemos trabajado en el uso con teclado» y listar lo que falta.
3. **«Contraste suficiente».** No medido.
4. **«Zonas táctiles de 44 × 44».** Solo en parte de los controles.
5. **«Parcialmente conforme».** Sin auditoría no se puede afirmar el grado de conformidad. Es honesto decir «parcialmente», pero la lista de «contenido no accesible» está incompleta (falta lo anterior).
6. **Respuesta en «20 días hábiles».** No hay procedimiento ni buzón propio: llega al email general (`{{email}}`). Definir quién responde. **[PENDIENTE TITULAR]**
7. **Fecha de la declaración.** El texto no dice cuándo se preparó ni cuándo se revisó por última vez (la usa `{{version}}`). Las declaraciones suelen indicar la fecha de la evaluación.

## Puntos para el abogado

- **[PENDIENTE ABOGADO]** Aplicación de la **Ley 11/2023** (traspone la Directiva (UE) 2019/882, «Acta Europea de Accesibilidad»), exigible desde el 28/06/2025 a los «servicios de comercio electrónico» dirigidos a consumidores: confirmar si WORLDIVES lo es (reserva y pago de actividades en línea) y si la excepción de **microempresa** (menos de 10 personas y volumen de negocio o balance de hasta 2 millones de euros) la exime de los requisitos de servicios.
- **[PENDIENTE ABOGADO]** Si aplica, qué información de accesibilidad debe publicar (anexo V de la Directiva: descripción del servicio y de cómo cumple los requisitos) y quién es la autoridad de control.
- **[PENDIENTE ABOGADO]** Si los centros que usan el panel y el widget (`/api/provider/ical`, widget de reservas) son también prestadores de comercio electrónico y quién responde de la accesibilidad del widget en su web.
- **[PENDIENTE ABOGADO]** El Real Decreto 1112/2018 solo obliga al sector público: confirmar que no aplica y que la vía de reclamación correcta es la de consumo (como dice el texto) y no la de la Administración.
- **[PENDIENTE ABOGADO]** Ley General de derechos de las personas con discapacidad (RDL 1/2013) y su régimen de infracciones para servicios de la sociedad de la información.
