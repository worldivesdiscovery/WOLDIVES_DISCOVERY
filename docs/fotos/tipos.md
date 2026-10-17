# Foto de cada tipo de buceo (v50.58, punto 6.4)

Revisión y usabilidad del 15-16/10/2026, punto 6.4. Cada tipo de buceo tiene una foto que lo representa, nunca una
foto al azar. Un punto de buceo sin foto propia muestra la foto de su **tipo principal** (el primero de su lista de
tipos: «Pared · Cueva» → pared). Si su tipo aún no tiene una foto adecuada, el punto muestra el color del mar de la marca
(`/img/punto-sin-foto.svg`), no otra foto.

La foto se cambia en **Administración → Tipos de buceo**: «Cambiar foto» (o «Poner foto») abre una ventana para
encuadrarla (marco 16:10 que se arrastra, zoom y flechas del teclado) con la vista previa de la tarjeta del tipo, la
cabecera de su página y un punto de ese tipo sin foto propia. Al guardar, el servidor corta la parte elegida, la deja en
1600 × 1000 y la guarda en WebP con sus copias de 640, 960 y 1440 px (la web elige la que cabe en la pantalla con
`srcset`), y se carga solo cuando llega a la pantalla (`loading="lazy"`). El texto alternativo es «Foto representativa
de *tipo*» en los 9 idiomas (las fotos del titular conservan su propia descripción, también en los 9 idiomas).

## Tipo → foto

| Tipo del encargo | Tipo en la web | Foto | Qué muestra | Origen |
|---|---|---|---|---|
| Arrecife | Arrecifes | `/img/portada/fondosuperior.webp` | Arrecife de coral con peces y rayos de luz | Venía con la web (registro de origen) |
| Pared | Paredes | `/img/destinos/australia.webp` | Pared de coral vertical con un banco de peces | Venía con la web (registro de origen) |
| Pecio | Pecios y naufragios | `/img/portada/logbook1.webp` | Un barco hundido sobre la arena y un buceador | Venía con la web (registro de origen) |
| Cenote | Cenotes | `/img/destinos/mexico.webp` | Un cenote visto desde el aire, entre la selva | Venía con la web (registro de origen) |
| Cueva | Cuevas y cavernas | — | **Sin foto adecuada**: hace falta un buceador con linterna en una cueva | — |
| Nocturna | Nocturnas | `/img/titular/nocturna-pulpo.webp` | Pulpo y morena de noche, buceador con linterna | Foto del titular (6.1) |
| Deriva | Corrientes y deriva | — | **Sin foto adecuada**: buceadores llevados por la corriente, peces en banco | — |
| Fondo de arena o posidonia | Muck | `/img/titular/caballito-posidonia.webp` | Un caballito de mar entre la posidonia | Foto del titular (6.1) |
| Bloques y rocas | — (no existe como tipo) | — | **Pendiente de decisión**: en el catálogo solo aparece como tipo secundario («Pared · Chimenea · Bloques», «Arrecife · Fondo rocoso»); esos puntos toman la foto de su tipo principal. Si el titular quiere el tipo, se crea y se le pone foto | — |
| Bautizo o aguas someras | Playa y esnórquel | `/img/destinos/maldivas.webp` | Una tortuga en agua somera y turquesa, con playa y palmeras | Venía con la web (registro de origen) |
| Profunda | Aguas profundas | `/img/titular/barco-cadena.webp` | Un barco desde abajo y su cadena bajando hacia el azul | Foto del titular (6.1) |
| Canal | Canales | — | **Sin foto adecuada**: paso entre arrecifes con corriente y peces grandes | — |
| Cañón | Cañones | — | **Sin foto adecuada**: corredor de roca encajado | — |
| Pináculo | Pináculos | — | **Sin foto adecuada**: aguja de roca que sube desde el fondo, con vida | — |
| Lago | Lagos | — | **Sin foto adecuada**: buceo en agua dulce (lago, embalse) | — |
| Pilar | Pilares | — | **Sin foto adecuada**: columnas o formaciones verticales | — |

Los tipos sin foto adecuada **se dejan indicados y no se rellenan** (regla del encargo). En *Administración → Tipos de
buceo* aparecen como «Sin foto: pendiente de una foto adecuada» con el botón «Poner foto», listos para cuando el titular
mande más fotos.

## Cómo se elige el tipo principal de un punto

`pointTypeKey` en `public/js/world-dives-v8.js` toma el primer tipo de la ficha (separados por `·`, `,` o `/`), sin
acentos, y lo busca en este orden: cenote, pecio, cueva, pared, arrecife, arena/posidonia/muck, canal, cañón, pináculo,
corriente/deriva, profunda, nocturna, lago, pilar y playa/esnórquel/bautizo/aguas someras. Una cueva cuyo nombre dice
«cenote» toma la foto de los cenotes. Si el punto tiene fotos propias, siempre van primero.

## Comprobación

- `tests/test_v50_58_fototipo.py` (servidor): recorte, 1600 × 1000 en WebP, sus 3 copias, sin encuadre (el centro),
  avisos (encuadre roto, demasiado zoom, foto pequeña, formato), borrado de la foto anterior y al restaurar, solo la
  administración, las portadas siguen como antes.
- `tests/navegador/e2e_v50_58_fototipo.py` (navegador, 29 comprobaciones): pecio y pared con la foto de su tipo, canal
  con el color del mar, la ventana de encuadre y su vista previa, guardar, la foto nueva al momento en la tarjeta y en
  los puntos, inglés, móvil a 390 px, restaurar.
- Capturas en `docs/capturas/v50.58/fototipo/`.
