# WORLDIVES DISCOVERY — Encargo: revisión general antes del lanzamiento (15/10/2026)

Texto del encargo tal como lo mandó el titular, junto con 5 fotos (el vídeo de cabecera en .mov que menciona no llegó
con el encargo). Se trabaja en la v50.57.

---

Pega este documento entero en la sesión de código junto con las fotos y el vídeo de cabecera que adjunta el titular.

* Versión base: la última que has entregado.
* Antes de cada punto: comprueba si ya está hecho y márcalo «Ya estaba», «Completado», «Nuevo» o «Pendiente de decisión».
* Origen: el titular ha recorrido la web en los cuatro modos (administrador, centro, freelance y buceador) y ha encontrado lo que sigue.
* Prioridad: la web se lanza en breve. Tiene que funcionar toda, sin un solo botón muerto, verse profesional y aguantar mucho tráfico.

Orden de trabajo:

1. Bloque 1 (errores que bloquean).
2. Bloque 2 (navegación).
3. Bloque 4 (administración).
4. Bloque 3 (estética).
5. Bloque 5 (auditoría total y carga).

## Bloque 1 — Errores que bloquean (lo primero)

### 1.1 «No time zone found with key Europe/Madrid»

* Qué pasa: al entrar en el panel de un centro (y en Reservas, Planning y Mi agenda del freelance) sale «No se ha podido abrir esa sección, falta un dato obligatorio: No time zone found with key Europe/Madrid». No se puede ver nada del centro ni del freelance.
* Causa probable: el código usa `zoneinfo` de Python para las zonas horarias. En Windows Python no trae la base de datos de zonas horarias y necesita el paquete `tzdata`. En Linux (el VPS) suele funcionar, por eso pasa en el ordenador del titular.
* Solución obligatoria:
   1. Añadir `tzdata` a `requirements.txt` e instalarlo en los arranques (`iniciar.bat` e `iniciar.sh`).
   2. Al arrancar, comprobar que `ZoneInfo("Europe/Madrid")` funciona. Si no, mostrar un mensaje claro en la consola con la solución, en vez de fallar en mitad de una pantalla.
   3. Una zona horaria guardada mal o vacía en un centro o servicio nunca debe romper una pantalla: se usa la del país del centro, se avisa al administrador y se registra.
   4. Revisar cualquier otro sitio donde un dato que falte rompa una sección entera. El error se muestra solo en ese bloque, con un mensaje entendible, y el resto de la pantalla sigue funcionando.
* Prueba: arrancar en Windows limpio (sin `tzdata` previo) con los arranques oficiales y abrir panel del centro, reservas, planning y agenda del freelance sin errores. Igual en Linux.

### 1.2 Códigos QR rotos en la ficha de la reserva

* Qué pasa: en la ficha de una reserva el QR sale como imagen rota. En Administración, «crear QR» sí funciona.
* Solución:
   * encontrar por qué falla (ruta de la imagen, permisos, librería `qrcode`, tipo de contenido o caché);
   * usar un único generador de QR para toda la web;
   * el QR de la reserva debe verse en la ficha (buceador, centro y administración), en el justificante PDF y en el correo.
* Prueba: crear reservas en los dos modos y ver el QR en las tres fichas, en el PDF y en el correo. Escanearlo con un móvil y comprobar que abre la reserva correcta, solo para quien tiene permiso.

### 1.3 Exportaciones que no descargan (CSV / Excel)

* Qué pasa: en Actividad, Pagos y el informe DAC7, la exportación no descarga nada o dice que el dato no existe.
* Solución:
   1. Hacer una lista de todas las exportaciones de la web: administración, centro y freelance (actividad, reservas, pagos, clientes, servicios, DAC7, facturas…).
   2. Arreglar cada una para que descargue siempre, aunque esté vacía. Si no hay datos, el archivo sale con las cabeceras y un aviso «Sin datos en este periodo».
   3. Ofrecer los dos formatos:
      * Excel (.xlsx), por defecto: profesional, con columnas con nombre en español, fechas y euros con formato y la primera fila fija;
      * CSV en UTF-8 con BOM y separador `;`, para que Excel en español lo abra bien.
   4. Filtro de fechas (mes, trimestre, año, temporada o personalizado) en cada exportación.
   5. El informe DAC7:
      * con los campos que exige Hacienda por centro: identificación fiscal, país, importes por trimestre, número de actividades y comisión, que es 0;
      * con su ejercicio fiscal;
      * si a un centro le faltan datos fiscales, el informe sale igualmente con la lista de centros incompletos.
* Prueba: descargar cada exportación en los dos formatos, con datos y sin datos, y abrirla en Excel.

## Bloque 2 — Navegación: ningún botón muerto, nunca «tener que ir atrás»

### 2.1 Volver siempre a donde estabas

1. Al editar y guardar algo desde Administración (un punto de buceo, un centro, un destino, una plantilla…), al pulsar Guardar se vuelve automáticamente a la pantalla de Administración de la que partió, con el mensaje «Guardado». Nunca se manda a Explorar.
2. Botón «← Volver» visible en todas las pantallas de edición, que lleva al punto de origen. Además, migas de pan en Administración: «Centro de control › Puntos de buceo › Editar Islas Medas».
3. Pulsar el menú de la sección en la que ya estás siempre funciona. Hoy, estando en «Editar punto», pulsar «Administración» no hace nada y hay que ir atrás. El navegador interno debe recargar la sección aunque la dirección sea la misma.
4. Cambiar de modo (de Administración a la vista de un centro y vuelta) funciona siempre a la primera, sin ir atrás.
5. El botón «atrás» del navegador y del móvil funciona con lógica en toda la web y nunca saca de la web ni deja una pantalla en blanco.

### 2.2 Revisión de todos los botones (obligatoria)

1. Prueba automática que recorre la web entera (con Playwright) con las cuatro cuentas de prueba más la de administrador:
   * pulsa cada botón, enlace, pestaña y menú de cada pantalla;
   * comprueba que pasa algo: cambia de pantalla, abre una ventana, guarda o muestra un mensaje;
   * comprueba que no hay errores en la consola ni en el servidor.
2. Informe con cada botón probado y el resultado: OK o fallo corregido. El titular ha visto fallos sobre todo en Administración → Destinos, Puntos y Plantillas: revisarlos uno a uno.

## Bloque 3 — Estética: fotos nuevas y cabecera en movimiento

Regla: los textos, las letras y la maquetación se quedan como están. Solo cambian las fotos y la cabecera.

### 3.1 Fotos nuevas (adjuntas por el titular)

1. Retirar las fotos actuales que no encajan:
   * fondos de pantalla;
   * tarjetas de tipos de buceo;
   * experiencias y destinos;
   * imágenes de portada de secciones.

   Pasan a `_archivo/`, sin borrarlas.
2. Colocar las fotos del titular donde corresponda por su contenido:
   * fondo marino amplio → fondos y portadas;
   * buceador en acción → tipos de buceo;
   * barco o viaje → experiencias;
   * paisaje de costa → destinos;
   * y así con el resto.

   Entregar una tabla de qué foto va dónde. Si sobran sitios sin foto adecuada, dejarlos indicados para que el titular mande más, sin rellenar con fotos al azar.
3. Optimizar cada foto:
   * WebP en 3 tamaños (móvil, tablet y ordenador) con `srcset`, más JPG de respaldo;
   * carga diferida fuera de la primera pantalla;
   * texto alternativo descriptivo en los 9 idiomas;
   * en el campo de origen o licencia, «Propiedad de WORLDIVES DISCOVERY».
4. Encuadre: recorte inteligente para que el motivo principal (el buceador, la manta, el barco) no quede cortado en móvil. Indicar el punto de enfoque de cada foto.

### 3.2 Vídeo de cabecera (archivo .mov adjunto)

1. Convertir el .mov a MP4 (H.264) y WebM, comprimidos para web:
   * menos de 4 MB para ordenador;
   * una versión más ligera para móvil;
   * sin sonido.
2. Cabecera de la portada a pantalla completa:
   * `autoplay muted loop playsinline`;
   * imagen fija (póster) del primer fotograma mientras carga;
   * una capa oscura suave para que se lea el texto de la portada, que se mantiene igual.
3. Si el usuario tiene activado «reducir movimiento» o el ahorro de datos, se muestra solo la imagen fija.
4. El vídeo no puede retrasar la carga: la portada debe seguir cargando rápido (Bloque 5).

### 3.3 Filtros de «Puntos de buceo» (ocupan demasiado)

* Qué pasa: los filtros (Costa Brava, Comunidad Valenciana, Murcia…) ocupan más de un tercio de la pantalla al bajar, y apenas se ven puntos.
* Solución, como en las webs profesionales de reservas:
   1. Una sola barra compacta de una línea, fija arriba al bajar:
      * buscador;
      * botón «Filtros (n)» con el número de filtros activos;
      * orden;
      * cambio entre lista y mapa.
   2. Zonas como fichas en una fila con desplazamiento lateral, no en varias filas. En móvil, los filtros se abren en un panel deslizante desde abajo.
   3. Filtros activos como fichas pequeñas con una ✕ para quitarlos y «Borrar todo».
   4. Más puntos a la vista:
      * tarjetas más compactas;
      * en ordenador, 3 o 4 columnas;
      * en móvil, al menos 2 puntos completos visibles en la primera pantalla tras los filtros.
   5. Los filtros quedan guardados en la dirección de la página, para compartir la búsqueda.
* Prueba: capturas de antes y después a 360, 390, 768, 1024 y 1440 px. La barra de filtros ocupa como máximo una línea al bajar.

## Bloque 4 — Administración

### 4.1 Contraseña solo para ver datos sensibles

* Qué pasa: el sistema pide la contraseña para cada acción del administrador, incluso al entrar en el Centro de control.
* Solución:
   1. Entrar en el Centro de control y gestionar la web no pide contraseña otra vez: puntos, destinos, plantillas, centros, experiencias, estadísticas, QR, etc.
   2. Solo se pide confirmar la contraseña (o el código de doble factor si está activo) al ver datos personales o sensibles:
      * reservas de los centros con datos de clientes;
      * teléfonos y correos completos;
      * documentos;
      * pagos con datos personales;
      * exportaciones con datos personales;
      * el informe DAC7.
   3. Una confirmación vale 15 minutos (configurable) para todas las acciones sensibles. Pasado ese tiempo, se vuelve a pedir.
   4. Cada acceso sensible queda registrado con el motivo, como ya dice el encargo de aislamiento entre centros.
   5. Por defecto, el administrador ve las reservas de los centros solo en cifras agregadas, sin datos de clientes. WORLDIVES es el motor de reservas: el detalle lo gestiona cada centro. El detalle solo se abre con motivo (soporte, disputa o fraude) y confirmación.

### 4.2 Contador de visitas y reservas en «Actividad»

1. En Actividad, un bloque discreto con:
   * visitas (páginas vistas y visitantes únicos);
   * reservas (totales y por modo);
   * importe reservado.

   Para la temporada actual, el mes y el total desde el inicio.
2. Temporada configurable en Administración (por ejemplo, del 1 de abril al 31 de octubre).
3. El recuento de visitas es propio y sin cookies de seguimiento: contadores agregados en el servidor, sin guardar IP completas ni identificar a nadie, de forma que no hace falta banner de cookies para esto. Excluye los robots conocidos y las visitas del propio administrador.
4. El mismo contador para cada centro en su panel (visitas a su ficha y sus reservas).

### 4.3 Plantillas de servicio: icono y borrado

1. Al crear o editar una plantilla, selector visual de icono con todos los iconos que ya existen:
   * inmersión;
   * bautizo;
   * curso;
   * salida privada;
   * viaje de buceo;
   * alquiler de equipo;
   * fotografía;
   * nocturna;
   * snorkel;
   * y el resto.

   Se ve una vista previa de cómo queda.
2. Borrar plantillas creadas por error:
   * si ningún centro la usa, se borra, con confirmación;
   * si algún centro la usa, se archiva: deja de aparecer para nuevos servicios, pero los servicios existentes no se rompen. Se avisa de cuántos centros la usan.
3. Ordenar las plantillas arrastrándolas.

### 4.4 Códigos QR con destinos predefinidos (que funcionen)

* Qué pasa: hoy se puede escribir cualquier cosa y no está claro a dónde lleva el QR.
* Solución:
   1. El administrador elige el destino de una lista, nunca escribe una dirección a mano:
      * registro de centros de buceo;
      * registro de buceadores;
      * registro de freelance;
      * explorar puntos de buceo;
      * un punto de buceo concreto (con buscador);
      * listado de centros;
      * un centro concreto (con buscador);
      * experiencias;
      * una experiencia concreta;
      * descargar la app (cuando exista);
      * portada.
   2. Nombre interno del QR (por ejemplo «Recepción feria Madrid») y contador de escaneos de cada QR, agregado y sin datos personales.
   3. Botón «Probar enlace» que abre el destino real antes de descargar.
   4. Descarga en PNG en alta resolución, SVG y PDF listo para imprimir con el logo y un texto opcional («Regístrate como centro»).
   5. QR para los centros desde su panel, con sus propios destinos:
      * su página de reservas;
      * un servicio concreto;
      * dejar una reseña;
      * su ficha.

      Mismas descargas.
   6. Dirección corta y estable (por ejemplo `/q/abc123`), para que, si cambia la ruta interna, los QR ya impresos sigan funcionando. Solo puede apuntar a páginas de WORLDIVES.

## Bloque 5 — Auditoría total y preparado para mucho tráfico

1. Repasar los cuatro modos completos, pantalla a pantalla: administrador, centro, freelance y buceador. Con especial atención a:
   * centro: reservas, planning y agenda;
   * freelance: reservas, planning y mi agenda;
   * administración: destinos, puntos y plantillas.

   Corregir todo lo que falle y documentarlo.
2. Prueba de carga con k6 o Locust contra el servidor de producción en local:
   * 300 usuarios simultáneos navegando (portada, explorar, fichas y mapa);
   * 20 reservas por segundo en salidas distintas, más reservas simultáneas a la misma salida para comprobar que no hay sobreventa (Bloque 1 del encargo multicanal);
   * objetivo: el 95 % de las páginas en menos de 500 ms y ningún error.
3. Si la base de datos actual (SQLite) no aguanta ese objetivo:
   * activar el modo WAL, los índices que falten y una caché de las consultas públicas;
   * si aun así no llega, entregar al titular un informe con el plan de paso a PostgreSQL: qué cambia, cuánto cuesta en el VPS y cuándo conviene hacerlo.
4. Velocidad, con el vídeo de cabecera incluido: portada con Lighthouse de 85 o más en móvil y la primera imagen visible en menos de 2,5 segundos en 4G.

## Pruebas obligatorias (resumen)

* Bloque 1:
   * panel del centro y agenda del freelance sin el error de zona horaria, en Windows y Linux;
   * el QR de la reserva visible y que funciona;
   * todas las exportaciones descargan en Excel y CSV, también la DAC7.
* Bloque 2:
   * guardar en Administración vuelve al Centro de control;
   * ningún botón muerto, según el informe de la prueba automática.
* Bloque 3:
   * capturas de antes y después de la portada con el vídeo y de las pantallas con fotos nuevas;
   * filtros en una línea a todos los anchos.
* Bloque 4:
   * no pide contraseña al entrar y sí al ver datos sensibles (15 minutos);
   * el contador de Actividad funciona;
   * plantilla con icono y borrado o archivado;
   * un QR de cada destino que se escanea y llega bien.
* Bloque 5:
   * resultado de la prueba de carga;
   * Lighthouse;
   * lista de lo corregido en la auditoría.

## Entrega

* Todo en la próxima versión, en los dos zips.
* Notas de versión con el apartado «Revisión general 15/10/2026», que incluya:
   * la tabla de estado de cada punto;
   * la tabla de qué foto va dónde;
   * el informe de botones;
   * el resultado de la prueba de carga;
   * las capturas de antes y después.
