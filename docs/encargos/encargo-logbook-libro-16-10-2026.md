WORLDIVES DISCOVERY — Encargo: Log Book que parezca un libro de verdad (16/10/2026)
Eres el programador de WORLDIVES DISCOVERY. Trabaja sobre la última versión del código. El titular adjunta una foto de cómo se ve ahora la página `#/logbook` en su ordenador.
Qué pasa hoy
El Log Book se abre bien, pulsando 5 veces como se acordó, pero no parece un libro. En la foto del titular se ve esto:

1. La imagen está cortada.
   * Arriba, el título «DIVE LOGBOOK» toca el borde y «DIVE» sale cortado.
   * Abajo, «EXPLORE · RECORD · PROTECT» sale pegado al borde y «PROTECT» queda cortado.
   * El borde izquierdo de la página izquierda también está recortado.
2. Parece una foto pegada, no un libro.
   * Las dos páginas son una sola imagen, que parece una fotografía de un libro hecha en ángulo: las páginas no son rectángulos y en la esquina superior derecha se ve la tapa oscura del libro original.
   * Hay un borde oscuro solo en el lado derecho y las esquinas redondeadas no coinciden con las del papel.
   * No hay lomo, ni grosor de páginas, ni sombra en el centro, ni tapa alrededor.
3. Dos triángulos blancos en las esquinas inferiores (izquierda y derecha) que tapan el dibujo y parecen un fallo.
4. El libro no está centrado y deja mucho espacio blanco vacío alrededor.

Qué hay que conseguir
Que al abrirlo parezca un pasaporte o cuaderno de buceo real, abierto encima de una mesa: dos páginas rectas, con su lomo en el centro, el grosor de las hojas en los bordes, la tapa azul marino asomando alrededor y una sombra suave debajo. Nada cortado y nada que tape el dibujo.
Reglas

1. Antes de tocar nada, explica en las notas por qué sale cortado. Puede ser:
   * una caja con alto fijo y `overflow: hidden`;
   * `object-fit: cover` en lugar de `contain`;
   * una imagen con otra proporción que la caja;
   * márgenes negativos.
Haz capturas del antes.
2. Se mantiene cómo se abre: pulsar 5 veces. No cambies esa regla.
3. Mismo diseño de la web (cabecera, colores, letra) y funciona en Clásico y Futurista, en la web y en el modo app.
4. Entrega en dos zips: `-produccion` y `-pruebas`.

Parte 1 · Las imágenes de las páginas

1. Separar las dos páginas en dos imágenes rectas, izquierda y derecha, con la misma proporción.
   * Si la imagen actual es una foto en perspectiva de un libro real, corrígela (enderezar en perspectiva) y recórtala justo por el borde del papel, sin la tapa ni el fondo de la foto.
   * Si la corrección pierde calidad o deforma el dibujo, márcalo «Pendiente de decisión» y pide al titular las ilustraciones originales en plano. No entregues una versión deformada.
2. No recortar nunca el dibujo: la imagen va entera dentro de la página (`object-fit: contain` o la proporción exacta). Los textos «DIVE LOGBOOK» y «EXPLORE · RECORD · PROTECT» deben verse completos y con margen.
3. Proporción de página fija, la de un pasaporte o cuaderno de buceo (por ejemplo 88 × 125 mm, unos 0,70 de ancho por alto). Si las ilustraciones tienen otra proporción, se usa la suya.
4. Calidad: WebP a doble resolución (2×) con JPG de respaldo, usando el sistema común de imágenes. Nada pixelado en pantallas de alta resolución.

Parte 2 · Que parezca un libro (con CSS, sin otra foto)
Construir el libro con capas, así se ve nítido a cualquier tamaño:

1. Tapa: azul Abismo `#011C3C` con textura suave de piel o tela. Asoma de 6 a 10 px alrededor de las páginas abiertas, con las esquinas algo redondeadas.
2. Lomo central: una sombra en degradado en el centro del libro, más oscura junto a la costura y que se aclara hacia fuera, para que las páginas parezcan curvarse hacia el lomo.
3. Grosor de las hojas: en los bordes exteriores, 3 o 4 líneas finas de color papel que simulan las páginas apiladas, más gruesas en el lado que tiene más hojas.
4. Papel: color marfil ligeramente cálido, con un brillo muy suave en la zona central de cada página y esquinas apenas redondeadas.
5. Sombra bajo el libro, como si estuviera apoyado en una mesa.
6. Fondo de la página web: un fondo neutro suave detrás del libro, por ejemplo azul muy claro o la textura de una mesa de madera clara, en lugar del blanco vacío. En Futurista, fondo oscuro.
7. Libro centrado en la pantalla, en horizontal y vertical, con el tamaño máximo que quepa entero sin hacer scroll: como mucho el 90 % del ancho y el 85 % del alto disponible bajo la cabecera.

Parte 3 · Pasar páginas

1. Quitar los dos triángulos blancos de las esquinas.
2. Pasar página como en un libro real:
   * arrastrando la esquina inferior con el ratón o el dedo, la hoja se dobla y gira sobre el lomo;
   * con un clic o toque en el borde de la página;
   * con flechas discretas a los lados (‹ ›) y con las teclas ← y → del teclado.
3. Animación de giro en 3D (unos 0,6 s), con la sombra de la hoja moviéndose al pasar. Puedes usar una librería de pasar páginas con licencia libre (por ejemplo StPageFlip, MIT). Indica cuál y su licencia en las notas.
4. Indicador discreto de página («2 / 24») bajo el libro.
5. Con «reducir movimiento» activado en el sistema, el cambio de página es un fundido simple, sin giro.

Parte 4 · En el móvil

1. En vertical: se ve una sola página a pantalla casi completa, con el lomo en el borde interior, y se pasa deslizando con el dedo.
2. En horizontal o tableta: el libro abierto con las dos páginas, igual que en el ordenador.
3. Nunca se corta nada en 360, 390, 414, 768, 1024, 1366, 1440 y 1920 px de ancho.

Parte 5 · Las páginas de inmersiones
Las páginas que siguen a la portada (cada inmersión del buceador) usan la misma página de papel, con:

* casillas impresas: fecha, punto, profundidad máxima, tiempo, temperatura, visibilidad, compañero y centro;
* el sello o la firma del centro, si la inmersión está validada.

Los datos se escriben encima como texto real, no como imagen, para que se lean nítidos y se puedan traducir. Si este diseño todavía no existe, déjalo preparado con una página de ejemplo y márcalo «Pendiente de decisión del titular» para que apruebe el aspecto.
Comprobaciones antes de entregar

1. Capturas de antes y después a 1440 y 1920 px en ordenador y a 390 px en móvil, en Clásico y Futurista. En la de después:
   * «DIVE LOGBOOK» y «EXPLORE · RECORD · PROTECT» completos;
   * ningún borde del dibujo recortado.
2. Que parezca un libro: tapa, lomo, grosor de las hojas y sombra visibles. No hay triángulos blancos ni bordes oscuros de la foto original.
3. Pasar páginas con el ratón, el dedo, las flechas y el teclado, hacia delante y hacia atrás, sin saltos ni parpadeos.
4. Se sigue abriendo pulsando 5 veces, igual que ahora.
5. Rendimiento: la página carga sin retraso visible y la animación va fluida en un móvil de gama media.
6. Consola sin errores.
7. Notas de versión con:
   * la causa del corte;
   * la librería usada y su licencia;
   * lo que quede «Pendiente de decisión».

Nota de recepción: el mensaje dice que adjunta una foto de la página `#/logbook`, pero en la conversación solo llegó el texto (sin imagen). Las capturas «antes» se hacen aquí, con la misma página.
