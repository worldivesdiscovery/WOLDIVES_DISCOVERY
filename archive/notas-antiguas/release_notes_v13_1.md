# WORLDIVES DISCOVERY v13.1

## Tipos de buceo corregidos

- El catálogo público ya no filtra por coincidencia literal del campo `dive_type`.
- Se han creado categorías semánticas para que cada botón devuelva los puntos que realmente corresponden.
- Aguas profundas: puntos cuyo `max_depth` catalogado supera 20 m.
- Arrecifes: tipos que identifican arrecife, separados de pecios.
- Pecios y naufragios: pecio/naufragio y sitios claramente identificados como wreck.
- Cuevas y cavernas: cuevas/cavernas, excluyendo cenotes para mantenerlos como categoría propia.
- Cenotes: por tipo, nombre o descripción.
- Muck: por tipo y descriptores de muck/lodo.
- Canales, cañones, pináculos, paredes, corrientes/deriva, nocturnas, lagos, pilares y playa/esnórquel tienen filtros específicos.
- El selector de `/puntos` usa las mismas categorías semánticas.
- La página `Tipos de buceo` muestra el número de puntos que devuelve cada categoría.

## Criterio de profundidad

Se aplica el criterio solicitado por el proyecto: `max_depth > 20 m`.

Las categorías son atributos del sitio y pueden solaparse cuando corresponde: un pecio puede ser profundo y un arrecife puede ser profundo. Al seleccionar "Pecios y naufragios", en cambio, el filtro se restringe a los sitios identificados como pecio/naufragio.
