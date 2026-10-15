# Fotos del titular: qué foto va dónde (v50.57)

Revisión general del 15/10/2026, punto 3.1. Las 5 fotos que envió el titular, colocadas por su contenido. Regla del
encargo: los textos, las letras y la maquetación no cambian; solo las fotos. Donde no hay una foto adecuada, el sitio se
queda sin foto (el color del mar de la marca) y se indica abajo para que el titular mande más: no se rellena al azar.

## Las fotos

Todas son **propiedad de WORLDIVES DISCOVERY**: así consta en el registro de origen de las imágenes
(*Administración → Medios → Origen y licencia*) y en los metadatos de cada archivo (EXIF *Copyright* y *Artist*).

| Foto | Qué muestra | Dónde va | Punto de enfoque |
|---|---|---|---|
| `buceador-rayos` | Buceador en aguas abiertas bajo los rayos del sol, junto a un arrecife | Cabecera de la portada (fondo marino amplio con buceador) | 78 % 66 % (el buceador) |
| `costa-barco` | Costa rocosa desde el aire, agua turquesa y un barco de buceo fondeado | Cabecera de «Explorar el mapa» (vista aérea); foto de los destinos y experiencias que no tienen foto propia (paisaje de costa); en la demo, destino «Costa Blanca» y portada de Bahía Coralina (Xàbia, salidas en barco) | 74 % 70 % (el barco) |
| `barco-cadena` | Un barco visto desde debajo del agua y su cadena de fondeo bajando hacia el azul | Cabecera de «Experiencias» (barco y viaje); tarjeta del tipo «Aguas profundas» | 35 % 8 % (el barco y el arranque de la cadena) |
| `nocturna-pulpo` | Inmersión nocturna: pulpo y morena en el arrecife, buceador con linterna al fondo | Tarjeta del tipo «Nocturnas»; en la demo, galería de Escafandra Medes (inmersiones nocturnas) | 28 % 64 % (el pulpo) |
| `caballito-posidonia` | Un caballito de mar entre la posidonia | Tarjeta del tipo «Muck» (fondos de arena y macro); en la demo, destino «Islas Medas» y galería de Escafandra Medes | 34 % 42 % (el caballito) |

El punto de enfoque (`object-position`, desde la izquierda y desde arriba) está en `WD_PHOTOS`
(`public/js/world-dives-v8.js`): cuando la foto se recorta para un móvil o una tarjeta, ese punto queda a la vista.

Cada foto se sirve en WebP en 3 tamaños (640, 960 y 1440 px, con `srcset`) más el original (≤ 2200 px) y un JPG de
respaldo para navegadores sin WebP (`<picture>`). Las cabeceras se cargan con prioridad; las tarjetas, solo cuando
llegan a la pantalla (`loading="lazy"`). El texto alternativo describe cada foto y está en los 9 idiomas.
Origen: `scripts/fotos/originales/` (tal como llegaron) → `python3 scripts/fotos/preparar_fotos_titular.py` →
`public/img/titular/`.

## Sitios sin foto adecuada (para que el titular mande más)

| Sitio | Qué foto haría falta | Qué había antes (retirada de ahí) |
|---|---|---|
| Tipo «Cuevas y cavernas» | Buceador con linterna en una cueva o cavidad | Lobos marinos de Galápagos |
| Tipo «Canales» | Paso entre arrecifes con corriente y peces grandes | Delfines en blanco y negro (Egipto) |
| Tipo «Cañones» | Pared o corredor de roca encajado | Rayos de luz en azul, genérica |
| Tipo «Pináculos» | Aguja de roca que sube desde el fondo, con vida | Buceadores sobre arrecife, genérica |
| Tipo «Corrientes y deriva» | Buceadores llevados por la corriente, peces en banco | Olas vistas desde el aire |
| Tipo «Lagos» | Buceo en agua dulce (lago, embalse) | Rayos de luz en azul, genérica |
| Tipo «Pilares» | Columnas o formaciones verticales | Buceadores sobre arrecife, genérica |

Mientras tanto, esas tarjetas muestran el color del mar de la marca, sin foto. En *Administración → Imágenes de la web*
aparecen como «Sin foto: pendiente de una foto adecuada» y desde ahí se les pone foto en cuanto llegue.

## Retiradas y archivo

- La portada (`portada-arrecife`, arrecife tropical) deja de usarse: pasa a `_archivo/fotos/portada/` con sus copias,
  **sin borrarla**. Su dirección antigua (y la de antes de v50.46, `/assets/images/…`) lleva a la foto que la sustituye.
- Las demás fotos que se retiran de un sitio siguen en uso donde sí encajan (destinos de su país, otras cabeceras), así
  que no se mueven: Galápagos, Egipto, México, Maldivas, Australia, Micronesia, Tailandia y California.
- Siguen igual porque encajan: cabeceras de «Centros», «Puntos de buceo», «Tipos de buceo», «Top 10» e «Iniciar sesión»;
  tipos «Arrecifes», «Paredes», «Pecios», «Cenotes» y «Playa y esnórquel»; las fotos de cada destino de viaje.

## Comprobación

- `tests/test_v50_57_fotos.py`: tamaños y formatos, licencia en los metadatos y en el registro de origen, cada foto en
  su sitio, sitios sin foto, texto alternativo en los 9 idiomas, punto de enfoque, archivo y direcciones antiguas.
- Capturas de antes y después en `docs/capturas/v50.57/fotos/antes/` y `docs/capturas/v50.57/fotos/despues/`
  (portada, tipos de buceo, experiencias, explorar y ficha de un centro; `escritorio-*` a 1440 px y `movil-*` a 390 px;
  `*-tipos-entera` es la página de tipos completa).
