# Revisión de experiencia de usuario (UX) · v50.54

Encargo del 14/10/2026, punto 1: revisar toda la web, aplicar las prácticas de Nielsen Norman Group, Baymard y Core
Web Vitals, y entregar la lista de problemas con su corrección.

**Estados:**
- «Ya estaba»: existía y funciona.
- «Corregido»: no funcionaba bien.
- «Nuevo»: no existía.
- «Pendiente de decisión»: necesita algo tuyo.

## Cómo se ha revisado

- **Capturas «antes» y «después».** Antes es v50.53 y después v50.54. Las 12 pantallas públicas en ordenador
  (1366 px) y en móvil (390 px). Están en `docs/capturas/v50.54/antes` y `docs/capturas/v50.54/despues`, con el
  mismo nombre en las dos carpetas.
- **Criterios de NN/g.** Lo importante en el primer pantallazo, lectura rápida y blancos equilibrados. La misma
  estructura y las mismas palabras en pantallas parecidas. Estado visible de lo que pasa, y nada que salte o se corte.
- **Criterios de Baymard** (listados y filtros):
  - filtros a la vista y fijos al bajar, con el número de resultados de cada opción;
  - ninguna opción que lleve a cero resultados;
  - un mensaje útil cuando no hay nada;
  - carga progresiva;
  - al volver de una ficha, los mismos filtros y la misma posición.
- **Core Web Vitals en móvil**, con tres medidas:
  - Lighthouse 12.8.2 (móvil simulado, 4G lento);
  - los saltos (CLS), medidos con el propio navegador y 4G lento;
  - el tiempo de respuesta al tocar (INP), medido con el navegador y la CPU cuatro veces más lenta.

  Las tres medidas son pruebas automáticas: `tests/navegador/e2e_v50_54_velocidad.py`.
- **Ancho de cajas y selectores.** Un detector busca cajas de texto de menos de 120 px y selectores cuyo texto no cabe,
  a 360 y 390 px de ancho, en 11 pantallas. Está en `tests/navegador/e2e_v50_54_ux.py`.
- **Alcance:**
  - todas las pantallas públicas, el acceso y el registro;
  - de los paneles, las pantallas que cambian en esta versión: Moderación, Datos personales y el aviso al centro;
  - el resto de los paneles se revisó en v50.51 (inventario de botones) y no cambia.

## Problemas encontrados y corrección

### En toda la web

| # | Problema | Corrección | Estado |
|---|---|---|---|
| 1 | Nada quedaba fijo al bajar: el `overflow-x:hidden` del cuerpo de la página anula `position:sticky` en todo el sitio | `overflow-x:clip` (mismo efecto sin romper lo fijo). Los filtros de Puntos y la cabecera de ordenador quedan fijos | Corregido |
| 2 | En el móvil la cabecera ocupa dos filas (logo; idioma, cuenta y menú), unos 160 px del primer pantallazo | En el móvil la cabecera ya no se queda fija (no tapa el contenido al bajar). Ponerla en una fila cambia logo y navegación | **Pendiente de decisión**: propuesta, una fila con el logo más pequeño y el idioma dentro del menú |
| 3 | El selector de idioma se movía al aparecer el botón de la cuenta (salto en todas las páginas, CLS 0,02–0,04) | Idioma y cuenta aparecen juntos, ya en su sitio | Corregido |
| 4 | Las librerías del mapa (unos 90 KB comprimidos) se descargaban en todas las páginas, también sin mapa | Se descargan solo al dibujar un mapa | Corregido |
| 5 | Las fotos de cabecera y de las tarjetas se servían a tamaño completo (portada 367 KB; tarjetas de Tipos de hasta 1,3 MB) | Copias de 640, 960 y 1440 px de las mismas fotos; el navegador baja la que necesita | Corregido |
| 6 | Un visitante en otro idioma esperaba a que el programa principal arrancase para pedir sus textos | El servidor pide el paquete de idioma junto con la página | Corregido |
| 7 | Tres grises con contraste por debajo de 4,5:1 (reseñas «Nuevo», datos de las tarjetas, ficha sin recorrido virtual) | Los mismos grises, algo más oscuros | Corregido |
| 8 | Un mismo punto aparecía como «Moderado», «Intermedia» o «Intermedio» según la pantalla, y el filtro dice «Intermedio» | Siempre las tres palabras del filtro: «Para empezar», «Intermedio» y «Avanzado». Afecta a tarjetas, ficha, panel del mapa, Tipos y Top 10 | Corregido |
| 9 | «Volver» se montaba sobre los botones Lista/Mapa | Recolocado | Corregido |

### Inicio

| # | Problema | Corrección | Estado |
|---|---|---|---|
| 10 | Nada que corregir en diseño: buscador, accesos rápidos y cifras en el primer pantallazo | Sin cambios, como pide el encargo. La portada baja una foto de 56–111 KB en vez de 367 KB | Ya estaba |

### Explorar

| # | Problema | Corrección | Estado |
|---|---|---|---|
| 11 | En el móvil el mapa empieza debajo de la cabecera y del cuadro de filtros | Sin cambios: el encargo pide no rehacer el mapa de Explorar | **Pendiente de decisión**: compactar la cabecera como en Puntos |

### Puntos de buceo (punto 2)

| # | Problema | Corrección | Estado |
|---|---|---|---|
| 12 | La cabecera grande empujaba la lista fuera del primer pantallazo | Título, buscador y Lista/Mapa en una sola franja | Corregido |
| 13 | Filtros que se perdían al bajar | Barra fija con región, tipo, nivel, profundidad, «Con centro» y orden | Nuevo |
| 14 | Regiones sin número, y algunas vacías | Píldoras con su número, calculado con los demás filtros; una región vacía no aparece | Nuevo |
| 15 | Rejilla y tarjeta | 3–4 columnas en el ordenador y lista de una en el móvil. La tarjeta lleva foto, nombre, región, profundidad, nivel y número de centros. No dice «Por confirmar»: lo que no hay, no sale | Corregido |
| 16 | El mapa del listado no enseñaba lo filtrado | Lista/Mapa en la misma página; el mapa enseña todos los puntos filtrados | Nuevo |
| 17 | Carga | Carga al bajar, con «Ver más» para el teclado | Nuevo |
| 18 | Al volver de una ficha se perdían filtros y posición | Vuelve con los mismos filtros, las mismas páginas y la misma posición | Nuevo |
| 19 | La lista bajaba de golpe al llegar los puntos (CLS 0,10 en Lighthouse) | Tarjetas de espera y la línea de ubicación ya puestas | Corregido (0,015) |

### Ficha del punto (punto 3)

| # | Problema | Corrección | Estado |
|---|---|---|---|
| 20 | Datos clave dispersos | Franja con iconos y orden fijo: profundidad, nivel, titulación recomendada, tipo, mejor época, temperatura y visibilidad. Solo los datos que existen | Nuevo |
| 21 | Orden distinto según el punto | Descripción, vida marina, recorrido virtual, centros con «Reservar» y mapa. La misma estructura en todos | Corregido |
| 22 | «Formación y adecuación» decía «Dificultad del punto: Por confirmar» y calculaba su propia titulación, que podía no coincidir con la franja | Usa la misma titulación y el mismo nivel que la franja; si falta el nivel, no sale | Corregido |
| 23 | El primer párrafo de «Sobre el punto» repite los datos de la franja («Tipo de inmersión: pared y arrecife. Profundidad de 7 a 20 m…»). Es texto del catálogo | No se toca contenido sin tu permiso | **Pendiente de decisión**: quitar ese párrafo generado cuando el punto tiene descripción propia |
| 24 | Mejor época, temperatura y visibilidad no existían | Campos opcionales que rellenan la administración o el centro dueño del punto | Nuevo. En la demo están vacíos: hay que rellenarlos punto a punto |

### Tipos de buceo (punto 4)

| # | Problema | Corrección | Estado |
|---|---|---|---|
| 25 | Elegir un tipo recargaba y subía arriba | Filtra en el sitio y baja suavemente a los resultados. La dirección cambia y «Atrás» funciona | Corregido |
| 26 | Sin números por tipo | Número de puntos por tipo; un tipo sin puntos aparece desactivado | Nuevo |
| 27 | Un filtro sin resultados dejaba la página vacía | Mensaje con sugerencias | Nuevo |
| 28 | La página descargaba 3,6 MB (fotos de 1,3 MB en tarjetas pequeñas) | 0,9 MB | Corregido |

### Centros y ficha del centro

| # | Problema | Corrección | Estado |
|---|---|---|---|
| 29 | Cabecera alta en Centros, Experiencias y Top 10 | Compactada | Corregido |
| 30 | En el móvil, «Cualquier tipo de buceo» se cortaba en «Cualquier tipo de» | Los dos selectores, uno debajo del otro, por debajo de 520 px | Corregido |
| 31 | La ruta «Centros / …» se leía mal sobre la foto: una regla posterior la pintaba de azul oscuro | En blanco y subrayada | Corregido |
| 32 | Los títulos de las tarjetas son `h3` sin un `h2` antes (Lighthouse, accesibilidad 98) | Cambiarlo toca los estilos de todas las tarjetas | **Pendiente de decisión** (bajo impacto) |

### Top 10

| # | Problema | Corrección | Estado |
|---|---|---|---|
| 33 | En móviles de 480 px o menos, la caja «O escribe una localidad» medía 34 px. Ya pasaba en v50.53: una regla general ponía los botones a todo el ancho | «Buscar» con su propio ancho; la caja ocupa el resto | Corregido |

### Acceso, registro y paneles

| # | Problema | Corrección | Estado |
|---|---|---|---|
| 34 | Nadie podía entrar en la demo: el formulario se rechazaba por «otro origen» (localhost / 127.0.0.1) | Corregido, y «Acceso rápido a la demostración» solo en la demo | Corregido / Nuevo (punto 6) |
| 35 | La administración editaba lo que publica un centro | Moderación con motivo, aviso, corrección y revisión. «Datos personales» con casillas | Nuevo (punto 8) |

## Core Web Vitals en móvil

### Lighthouse (móvil simulado, 4G lento, CPU 4×)

Antes es v50.53 y después v50.54, con la misma base de demostración y las mismas páginas.

| Página | Rendimiento | Accesibilidad | LCP | CLS | TBT | Descarga |
|---|---|---|---|---|---|---|
| Inicio | 67 → **72** | 100 → 100 | 7,1 → **5,9 s** | 0,046 → **0,036** | 380 → **310 ms** | 1.084 → **782 KB** |
| Puntos de buceo | 71 → **84** | 95 → **100** | 6,8 → **4,2 s** | 0,032 → **0,015** | 270 → **140 ms** | 1.483 → **785 KB** |
| Ficha del punto | 67 → **73** | 97 → **100** | 5,4 → **5,2 s** | 0,032 → **0,011** | 490 → **330 ms** | 704 → **693 KB** |
| Tipos de buceo | 73 → **79** | 100 → 100 | 11,2 → **5,1 s** | 0,032 → **0,011** | 160 → **150 ms** | 3.645 → **921 KB** |
| Un tipo | 73 → **76** | 96 → **100** | 8,1 → **5,8 s** | 0,032 → **0,011** | 180 → 180 ms | 1.863 → **918 KB** |
| Top 10 | 73 → **79** | 100 → 100 | 6,7 → **4,7 s** | 0,032 → **0,021** | 220 → 220 ms | 995 → **628 KB** |
| Centros | 75 → **80** | 95 → **98** | 5,3 → **4,8 s** | 0,032 → **0,011** | 280 → **180 ms** | 1.348 → **770 KB** |
| Ficha del centro | 63 → **77** | 100 → 100 | 7,0 → **5,2 s** | 0,032 → **0,011** | 540 → **240 ms** | 1.029 → **690 KB** |

- **Variación entre pasadas.** El LCP varía alrededor de ±1 s entre pasadas: «Un tipo» dio 3,9 s en una y 5,8 s
  en otra. La tabla recoge la última pasada.
- **SEO 63 solo en la demo.** El modo demo pide a los buscadores que no indexen (`noindex`).
- **Buenas prácticas 96 en Inicio y en la ficha del punto.** Son los mosaicos de OpenStreetMap, que el proxy de este
  entorno bloquea. En el servidor real el mapa base sale de nuestro propio archivo.

### Medidas en el navegador

| Medida | Objetivo | Resultado |
|---|---|---|
| **CLS**, con 4G lento, en Inicio, Puntos, ficha del punto, Tipos, Top 10, Centros y ficha del centro | < 0,1 | **0,007–0,023**. En v50.53 la misma medida daba 0,026 en Centros y 0,034 en Puntos |
| **INP**, con la CPU 4× más lenta: región y Lista/Mapa en Puntos, menú del móvil, filtros y tipo en Tipos, filtro de Centros | < 200 ms | **40–96 ms** |
| **LCP** (Lighthouse) | < 2,5 s | **4,2–5,9 s. No se cumple**. Ver abajo |

### Por qué el LCP sigue por encima de 2,5 s

- **Qué tarda.** La primera pintura llega en 1,1 s. Lo que tarda es lo que dibuja el programa de la web, y la foto de
  cabecera es el elemento LCP.
- **La cadena hasta la foto:**
  1. la página;
  2. el programa principal: 990 KB, 293 KB comprimidos, con los paneles de centro y administración dentro;
  3. sus llamadas de arranque y, si no lees en castellano, tus textos: 139 KB comprimidos con los textos de todos
     los paneles;
  4. por fin, la foto.
- **Qué falta.** En 4G lento, solo bajar y ejecutar el programa lleva unos 3 s. Para bajar de 2,5 s hay que separar
  el código público del de los paneles, y los textos públicos de los de los paneles. Es un cambio de estructura y
  queda como **«Pendiente de decisión»** en las notas de la versión.

## Comprobación automática

- `tests/navegador/e2e_v50_54_ux.py`:
  - cajas y selectores a 360 y 390 px en 11 pantallas;
  - el nivel con las palabras del filtro, y nunca «Por confirmar»;
  - la ruta del centro sobre la foto.
- `tests/navegador/e2e_v50_54_velocidad.py`:
  - todos los mapas;
  - la copia ligera en el móvil;
  - CLS en 7 pantallas e INP en 7 interacciones.
- `tests/test_v50_54_velocidad.py`:
  - las librerías del mapa no van en la página;
  - las copias ligeras coinciden con la tabla de anchos;
  - el paquete de idioma adelantado.
- `tests/navegador/e2e_v50_54_puntos_tipos.py`: Puntos, ficha del punto y Tipos (puntos 2, 3 y 4).
