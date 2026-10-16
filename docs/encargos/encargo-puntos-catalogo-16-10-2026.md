# WORLDIVES DISCOVERY — Encargo: fichas de punto más completas y catálogo de puntos ampliado (16/10/2026)

https://www.buscabuceo.com/es/inmersiones-de-buceo/

Eres el programador de WORLDIVES DISCOVERY. Trabaja sobre la **última versión** del código.

**Objetivo:** tener el catálogo de puntos de buceo más completo y mejor informado del mercado, empezando por España. Cada punto, bien situado en el mapa, sin duplicados y con toda la información que necesita un buceador para decidir.

## Reglas

1. **Antes de cada punto,** comprueba si ya está hecho y márcalo «Ya estaba», «Completado», «Nuevo» o «Pendiente de decisión».
2. **Nada inventado.** Un dato que no se puede comprobar se deja vacío, nunca se rellena «a ojo».
3. **Textos en los 9 idiomas,** con «Pendiente de traducción» y el castellano de reserva si falta alguno.
4. **Entrega en dos zips:** `-produccion` y `-pruebas`.

---

## Parte A · Ficha de punto más completa

### A.1 Campos nuevos

Además de los que ya hay (nombre, posición, tipo, nivel, titulación recomendada, profundidad y descripción), añadir:

| Campo | Cómo se rellena |
|---|---|
| Profundidad mínima y máxima | Metros |
| Acceso | Barco · Costa · Los dos |
| Corriente | Nula · Suave · Moderada · Fuerte · Variable |
| Temperatura del agua | Mínima y máxima por estación (invierno, primavera, verano, otoño), en °C |
| Visibilidad habitual | Tramo en metros (por ejemplo 10–20 m) |
| Tipo de fondo | Varias opciones: roca, arena, posidonia, coral, pared, pecio, cueva, cascajo |
| Mejor época | Meses |
| Vida marina destacada | Enlace a las especies del catálogo de especies (las 150 del encargo de la biblioteca de imágenes) |
| Avisos | Texto corto: tráfico de barcos, corriente en la punta, zona de anclaje… |
| Protección | Reserva marina, parque natural o ninguna, y si hace falta permiso |
| Estado del dato | Verificado · Pendiente de verificar |

### A.2 Cómo se ve

1. **Ficha del punto:** los datos nuevos en una franja de iconos bajo el título (profundidad, corriente, visibilidad, temperatura, acceso), con el mismo diseño que el resto de la web. Los datos vacíos no se muestran.
2. **Temperatura del agua:** se ve la de la estación actual, y al pulsar, las cuatro.
3. **Vida marina:** carrusel con las fotos de las especies enlazadas.
4. **Filtros nuevos en Puntos de buceo y Explorar,** dentro del panel «Filtros» compacto del encargo del 15/10: acceso, corriente, tipo de fondo y profundidad máxima.

### A.3 Quién lo edita

1. **El administrador** edita todos los campos desde Administración → Puntos.
2. **Los centros asociados a un punto** pueden proponer cambios (posición, corriente, visibilidad, avisos). El administrador los acepta o rechaza con un clic.
3. **Los buceadores** pueden proponer una corrección desde la ficha. Ya existe para la posición: amplíalo a los campos nuevos.

---

## Parte B · Ampliar el catálogo con fuentes que se puedan usar

### B.1 Qué fuentes valen

1. **Datos abiertos:**
   - **Wikidata:** licencia CC0, se puede usar sin citar;
   - **OpenStreetMap,** puntos etiquetados como sitios de buceo: licencia ODbL, que exige una línea de atribución en la página de créditos y licencias. No hace falta citarla en cada punto;
   - **datos oficiales** de reservas marinas y espacios protegidos (Ministerio, comunidades autónomas), con sus condiciones de reutilización.
2. **Información que aportan los centros** al darse de alta o en su panel: sus puntos con GPS. Es la fuente más fiable.
3. **Investigación propia, zona por zona,** como en la v50.30:
   - contrastar cada punto en **al menos dos fuentes públicas distintas**;
   - escribir la descripción **con palabras propias**.

### B.2 Qué no se hace

1. **No copiar en bloque** la base de datos, el listado o el mapa de otra web de buceo o de un competidor, aunque se vea en abierto.
2. **No copiar textos ni fotos** de otras webs.
3. **No saltarse** las condiciones de uso ni el `robots.txt` de ninguna web, y no hacer descargas masivas automáticas.

### B.3 Registro de fuentes (interno, no se publica)

1. Por cada punto se guarda **en privado**, solo visible para el administrador, de dónde salió cada dato y la fecha en que se comprobó.
2. En la web pública no aparece la fuente de cada punto. Solo la línea de créditos obligatoria de las licencias abiertas, en la página de créditos.
3. Sirve para defender el catálogo si alguien pregunta, y para revisar los datos más adelante.

### B.4 Sin duplicados

1. **Antes de añadir un punto,** buscar los que ya existen a menos de 300 m o con un nombre parecido (sin tildes, sin «El» o «La», con sinónimos como «Bajo» y «Bajón»).
2. **Si coincide,** se completa la ficha existente con los datos que falten. No se crea una ficha nueva.
3. **Si hay dudas,** queda en una lista «Posibles duplicados» para que el administrador decida con un clic: unir o mantener separados.
4. **Al unir dos fichas,** las reseñas, fotos y centros asociados pasan a la ficha que se queda.

### B.5 Orden de trabajo

1. **España primero,** por zonas: Comunidad Valenciana, Murcia, Andalucía, Cataluña (Costa Brava), Baleares, Canarias y la costa cantábrica y gallega.
2. **Después,** los destinos de las experiencias que ya tiene la web (Mar Rojo, Maldivas, Indonesia, México…).
3. **Cada zona se entrega como un lote** en estado «Pendiente de verificar». El administrador lo revisa en Administración → Puntos → Lotes nuevos y lo publica entero o punto a punto.

### B.6 En el mapa

1. **Cada punto nuevo** se coloca con su GPS y se comprueba que cae en el mar, no en tierra.
2. **Los puntos de costa** van a menos de 200 m de la orilla.
3. **Agrupación al alejar** con el marcador circular de la bandera de buceo, que ya existe.
4. **El mapa sigue fluido** con 3.000 puntos o más en un móvil de gama media.

---

## Comprobaciones antes de entregar

1. **Ficha completa** de un punto con todos los campos nuevos, en ordenador y en móvil, en Clásico y Futurista.
2. **Ficha con campos vacíos:** no se ven huecos ni guiones.
3. **Filtros nuevos** funcionando en lista y en mapa.
4. **Duplicados:**
   - añadir un punto a 100 m de uno que ya existe y con nombre parecido lo detecta;
   - unir dos fichas conserva las reseñas.
5. **Ningún punto nuevo** cae en tierra.
6. **Registro de fuentes:** visible solo para el administrador; un buceador o un centro no puede verlo.
7. **Página de créditos** con la línea de atribución de OpenStreetMap si se ha usado.
8. **Notas de versión** con:
   - cuántos puntos se han añadido por zona;
   - cuántos se han unido como duplicados;
   - cuántos quedan pendientes de verificar.

---

Nota de recepción: el enlace del principio (un listado de puntos de otra web de buceo) se toma solo como referencia de lo que ya ofrece el mercado. Según la regla B.2, de esa web no se copia nada: ni el listado, ni el mapa, ni textos, ni fotos.
