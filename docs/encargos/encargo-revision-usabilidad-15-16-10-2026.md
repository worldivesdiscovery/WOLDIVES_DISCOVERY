# WORLDIVES DISCOVERY — Encargo unificado: revisión general y usabilidad (15 y 16/10/2026)

Pega este documento entero en la sesión de código **junto con las fotos y el vídeo de cabecera** que adjunta el titular. Une en uno solo los encargos «Revisión general 15/10» y «Usabilidad 16/10», sin repeticiones.

- **Versión base:** la última que has entregado.
- **Antes de cada punto:** comprueba si ya está hecho y márcalo «Ya estaba», «Completado», «Nuevo» o «Pendiente de decisión».
- **Origen:** el titular ha recorrido la web en los cuatro modos (administrador, centro, freelance y buceador) y ha encontrado lo que sigue.
- **Prioridad:** la web se lanza en breve. Tiene que funcionar **entera, sin un solo botón muerto**, verse profesional, aguantar mucho tráfico y ser tan sencilla que un centro diga **«qué fácil es»**. En cada pantalla:
  - pocas opciones a la vista;
  - lenguaje de buceador, no técnico;
  - valores por defecto sensatos;
  - lo avanzado escondido hasta que se pida.
- **Orden de trabajo:**
  1. Parte 1 (errores que bloquean).
  2. Parte 2 (navegación y paneles).
  3. **Parte 3 (editor de servicios, la más importante)**.
  4. Parte 4 (administración).
  5. Parte 5 (vender en tu web).
  6. Parte 6 (estética).
  7. Parte 7 (auditoría y carga).

---

## Parte 1 — Errores que bloquean (lo primero)

### 1.1 «No time zone found with key Europe/Madrid»

- **Qué pasa:** al entrar en el panel de un centro (y en Reservas, Planning y Mi agenda del freelance) sale «No se ha podido abrir esa sección, falta un dato obligatorio: No time zone found with key Europe/Madrid». **No se puede ver nada del centro ni del freelance.**
- **Causa probable:** el código usa `zoneinfo` de Python para las zonas horarias. En **Windows** Python no trae la base de datos de zonas horarias y necesita el paquete `tzdata`. En Linux (el VPS) suele funcionar, por eso pasa en el ordenador del titular.
- **Solución obligatoria:**
  1. Añadir `tzdata` a `requirements.txt` e instalarlo en los arranques (`iniciar.bat` e `iniciar.sh`).
  2. Al arrancar, comprobar que `ZoneInfo("Europe/Madrid")` funciona. Si no, mostrar un mensaje claro en la consola con la solución, en vez de fallar en mitad de una pantalla.
  3. Una zona horaria guardada mal o vacía en un centro o servicio **nunca** debe romper una pantalla: se usa la del país del centro, se avisa al administrador y se registra.
  4. Revisar cualquier otro sitio donde un dato que falte rompa una sección entera. El error se muestra solo en ese bloque, con un mensaje entendible, y el resto de la pantalla sigue funcionando.
- **Prueba:** arrancar en Windows limpio (sin `tzdata` previo) con los arranques oficiales y abrir panel del centro, reservas, planning y agenda del freelance sin errores. Igual en Linux.

### 1.2 Códigos QR rotos en la ficha de la reserva

- **Qué pasa:** en la ficha de una reserva el QR sale como imagen rota. En Administración, «crear QR» sí funciona.
- **Solución:**
  - encontrar por qué falla (ruta de la imagen, permisos, librería `qrcode`, tipo de contenido o caché);
  - usar **un único generador de QR** para toda la web;
  - el QR de la reserva debe verse en la ficha (buceador, centro y administración), en el justificante PDF y en el correo.
- **Prueba:** crear reservas en los dos modos y ver el QR en las tres fichas, en el PDF y en el correo. Escanearlo con un móvil y comprobar que abre la reserva correcta, solo para quien tiene permiso.

### 1.3 Exportaciones que no descargan (CSV / Excel)

- **Qué pasa:** en Actividad, Pagos y el **informe DAC7**, la exportación no descarga nada o dice que el dato no existe.
- **Solución:**
  1. Hacer una lista de **todas** las exportaciones de la web: administración, centro y freelance (actividad, reservas, pagos, clientes, servicios, DAC7, facturas…).
  2. Arreglar cada una para que descargue siempre, aunque esté vacía. Si no hay datos, el archivo sale con las cabeceras y un aviso «Sin datos en este periodo».
  3. Ofrecer los **dos formatos**:
     - **Excel (.xlsx)**, por defecto: profesional, con columnas con nombre en español, fechas y euros con formato y la primera fila fija;
     - **CSV** en UTF-8 con BOM y separador `;`, para que Excel en español lo abra bien.
  4. Filtro de fechas (mes, trimestre, año, temporada o personalizado) en cada exportación.
  5. **El informe DAC7:**
     - con los campos que exige Hacienda por centro: identificación fiscal, país, importes por trimestre, número de actividades y comisión, que es 0;
     - con su ejercicio fiscal;
     - si a un centro le faltan datos fiscales, el informe sale igualmente con la lista de centros incompletos.
- **Prueba:** descargar cada exportación en los dos formatos, con datos y sin datos, y abrirla en Excel.

---

## Parte 2 — Navegación y paneles: ningún botón muerto y todo cómodo

### 2.1 Volver siempre a donde estabas

1. **Al editar y guardar algo desde Administración** (un punto de buceo, un centro, un destino, una plantilla…), al pulsar **Guardar** se vuelve automáticamente a **la pantalla de Administración de la que partió**, con el mensaje «Guardado». **Nunca** se manda a Explorar.
2. **Botón «← Volver»** visible en todas las pantallas de edición, que lleva al punto de origen. Además, **migas de pan** en Administración: «Centro de control › Puntos de buceo › Editar Islas Medas».
3. **Pulsar el menú de la sección en la que ya estás siempre funciona.** Hoy, estando en «Editar punto», pulsar «Administración» no hace nada y hay que ir atrás. El navegador interno debe recargar la sección aunque la dirección sea la misma.
4. **Cambiar de modo** (de Administración a la vista de un centro y vuelta) funciona siempre a la primera, sin ir atrás.
5. **El botón «atrás» del navegador y del móvil** funciona con lógica en toda la web y nunca saca de la web ni deja una pantalla en blanco.

### 2.2 Revisión de todos los botones (obligatoria)

1. **Prueba automática que recorre la web entera** (con Playwright) con las cuatro cuentas de prueba más la de administrador:
   - **pulsa cada botón, enlace, pestaña y menú** de cada pantalla;
   - comprueba que pasa algo: cambia de pantalla, abre una ventana, guarda o muestra un mensaje;
   - comprueba que no hay errores en la consola ni en el servidor.
2. **Informe** con cada botón probado y el resultado: OK o fallo corregido. El titular ha visto fallos sobre todo en **Administración → Destinos**, Puntos y Plantillas: revisarlos uno a uno.

### 2.3 Desplazamiento con la rueda del ratón donde está el cursor

- **Qué pasa:** en los paneles (administración, centro, freelance), al girar la rueda con el cursor sobre el **menú lateral izquierdo**, no se mueve el menú hasta que ha bajado del todo la página principal. Hay que esperar o ir al final.
- **Solución:**
  1. **Cada zona se desplaza por su cuenta:** el **menú lateral** y el **contenido principal** son dos zonas independientes, cada una con su propia barra de desplazamiento.
     - El menú ocupa el alto de la pantalla (menos la cabecera) y se queda fijo.
     - Si tiene más opciones de las que caben, se desplaza él solo.
  2. **La rueda mueve la zona que está debajo del cursor.** Cuando una zona llega a su final, **no arrastra** a la otra (`overscroll-behavior: contain`).
  3. Lo mismo en **ventanas emergentes, paneles laterales, listas largas y mapas**: la rueda sobre el mapa hace zoom en el mapa y no mueve la página. Fuera del mapa, la rueda mueve la página.
  4. **En móvil:** el menú lateral se convierte en un **panel deslizante** que se abre con el botón ☰, con su propio desplazamiento, y se cierra al elegir una opción.
- **Prueba:** con el cursor sobre el menú, la rueda mueve solo el menú; sobre el contenido, solo el contenido. En las tres zonas de paneles, en Chrome, Firefox, Safari y Edge, y con trackpad.

### 2.4 Administración con menú lateral, igual que el centro de buceo

1. **Mismo diseño que el panel del centro:** menú vertical a la izquierda y contenido a la derecha. Se quita la fila de controles de arriba.
2. **Un solo componente de panel** reutilizado en administración, centro y freelance. Así se ven y se comportan igual y los arreglos valen para los tres.
3. **Menú de administración agrupado y plegable**, con iconos y contador de pendientes donde aplique:
   - **Inicio:** Centro de control y Actividad;
   - **Revisión:** solicitudes de centros, experiencias y denuncias;
   - **Contenido:** puntos de buceo, destinos, tipos de buceo, especies e imágenes;
   - **Catálogo:** plantillas de servicio, planes y patrocinio;
   - **Herramientas:** códigos QR, exportaciones y DAC7;
   - **Seguros:** aseguradoras colaboradoras;
   - **Sistema:** ajustes, legal, registro de accesos y estado del sistema.
4. **La sección activa** queda marcada en el menú. Pulsarla otra vez siempre funciona (punto 2.1).
5. **Menú plegable a iconos** para ganar espacio en pantallas pequeñas de ordenador.

---

## Parte 3 — Editor de servicios del centro (lo más importante)

### 3.1 Qué está mal hoy

- La duración solo va en **minutos**, aunque un curso Open Water dura **3 días**.
- **«Unidad de reserva»** («por días», «por salidas», «por días o medias jornadas») no se entiende.
- **«Pago al reservar» y «Bajo petición»** son buenas opciones pero están explicadas de forma liosa.
- Hay demasiados campos a la vez, y muchos no aplican al tipo de servicio.

### 3.2 Cómo debe ser: un asistente de pocos pasos, según lo que vendes

**Paso 1 — «¿Qué vas a ofrecer?»** Tarjetas grandes con icono y una línea de ejemplo:

| Tarjeta | Ejemplo | Cómo se mide |
|---|---|---|
| **Inmersión o salida en barco** | «Doble inmersión en Islas Medas» | Horas y minutos, con hora de salida |
| **Bautizo** | «Bautizo de buceo en playa» | Horas y minutos |
| **Curso** | «Open Water, 3 días» | **Días o sesiones** (ver 3.3) |
| **Alquiler de equipo** | «Traje 5 mm» | Por día o por inmersión |
| **Guía o instructor por días** (freelance) | «Guía privado en cenotes» | Días completos o medias jornadas |
| **Viaje o experiencia** | «Semana en el Mar Rojo» | Fechas fijas de inicio y fin |
| **Otro** | Fotografía, nitrox, recarga… | A elegir |

Al elegir, **se rellena todo lo posible por defecto** a partir de la plantilla del administrador: icono, duración típica, plazas típicas, modo de reserva recomendado y política de cancelación habitual. **Solo se muestran los campos que tienen sentido para ese tipo.**

**Paso 2 — Lo básico** (una sola pantalla corta):
- nombre, foto e icono;
- descripción breve;
- qué incluye (casillas rápidas: equipo, barco, seguro, fotos, titulación…);
- nivel o titulación necesaria;
- edad mínima;
- idiomas;
- punto de encuentro.

**Paso 3 — Cuándo y cuánto dura** (cambia según el tipo, ver 3.3).

**Paso 4 — Precio y plazas:**
- precio **por persona** o **por grupo**, con un cálculo de ejemplo al momento: «2 personas × 1 curso = 900 €»;
- plazas por salida o por edición del curso;
- **extras** opcionales: alquiler de equipo, nitrox, fotos.

**Paso 5 — Cómo se reserva** (ver 3.4).

**Paso 6 — Revisar y publicar:**
- **vista previa «Así lo verá el buceador»**, con la tarjeta y la ficha tal como saldrán;
- botones **«Publicar»** y **«Guardar como borrador»**.

**Reglas del asistente:**
- **Opciones avanzadas plegadas** bajo «Más opciones» en cada paso: señal o depósito, antelación mínima, política de cancelación personalizada, temporada, instructor o barco asignado, etiquetas.
- **Volver atrás sin perder nada.** Se guarda solo como borrador.
- **Una barra de progreso** muestra en qué paso estás.
- **Para cambiar un servicio ya creado,** se abre en una sola página con secciones plegables (los mismos bloques del asistente), sin repetir todo el recorrido.
- **Botón «Duplicar servicio»,** para crear variantes rápidas (por ejemplo, Open Water en inglés).
- **Mensajes de error claros y junto al campo:** «Pon cuántos días dura el curso», nunca «campo inválido».

### 3.3 La duración, en el idioma del buceador

1. **Inmersión, bautizo u otro:** selector de **horas y minutos** (por ejemplo, 3 h 30 min) y **hora de salida**, con salidas que se repiten: «todos los sábados a las 9:00» o fechas sueltas.
2. **Curso:**
   - **«¿Cuántos días dura?»**, con un selector de **1 a 10 días**;
   - **plan de sesiones**: cada día se marca como **Día completo**, **Mañana** o **Tarde** (horas configurables, por ejemplo 9:00-13:00 y 15:00-19:00);
   - **atajos de un toque**:
     - «3 días completos»;
     - «4 mañanas»;
     - «2 mañanas + 2 días completos»;
     - «Personalizado»;
   - **ediciones del curso**: el centro elige la **fecha de inicio** y la de fin se calcula sola según el plan. Ejemplo: «Open Water del lunes 3 al miércoles 5 de junio».

     Puede crear varias ediciones de golpe: «todos los lunes de junio» o fechas sueltas. Cada edición tiene sus plazas y su instructor;
   - **en el planning y en la agenda del instructor,** el curso aparece como **un bloque de varios días**, y cada sesión ocupa su mañana, tarde o día completo, sin solaparse (motor de agenda común A1).
3. **Guía o instructor freelance por días:** **días completos o medias jornadas (mañana o tarde)**, con su calendario libre/ocupado. Es lo ya definido en A2.
4. **Alquiler:** **por día** o **por inmersión**.
5. **Viaje o experiencia:** **fecha de inicio y de fin** fijas, con el número de noches calculado solo.
6. **Se elimina el campo técnico «unidad de reserva»** de la pantalla. Se deduce internamente del tipo y de lo que el centro ha elegido arriba. Los datos ya existentes se migran sin perder nada.

### 3.4 «¿Cómo quieres que te reserven?» (pago al reservar / bajo petición)

Dos tarjetas grandes, con un ejemplo cada una y la **recomendada marcada** según el tipo de servicio:

- **⚡ Reserva inmediata.** «El buceador paga y su plaza queda confirmada al momento. Tú no tienes que hacer nada.» Recomendada para inmersiones, bautizos y alquiler con fechas fijas.
- **✋ Tú apruebas cada reserva.** «El buceador te envía una solicitud. Tú la aceptas o la rechazas (tienes X horas). Si la aceptas, paga y queda confirmada.» Recomendada para cursos a medida, viajes y guías privados.

Debajo, plegado en «Más opciones»:
- cobrar una **señal** en lugar del total;
- **plazo de respuesta** de las solicitudes;
- **pago en el centro** (para países sin Stripe).

**Por dentro sigue siendo lo mismo de la Fase 1B; solo cambia cómo se presenta.**

### 3.5 Pasar una sesión o inmersión del curso a otro día (por alumno)

**El caso real:** un alumno empieza el Open Water. Por mal tiempo no se puede hacer la inmersión de la tarde del último día, y el curso queda a falta de esa inmersión. Hay que hacerla **otro día**, y debe seguir **unida a la misma reserva y al mismo curso**.

1. **Progreso del curso en cada reserva.** En la ficha de la reserva del curso (y en el planning) se ve la lista de sesiones e inmersiones con su estado:
   - ✔ hecha;
   - ⏳ pendiente;
   - ↪ aplazada;
   - ✖ cancelada.

   Y un resumen: **«3 de 4 inmersiones hechas · 1 pendiente»**.
2. **Marcar como hecha** cada sesión o inmersión con un toque, para todo el grupo o solo para algunos alumnos.
3. **Botón «Pasar a otro día»** en una sesión o inmersión pendiente, para **un alumno, varios o todo el grupo**. Dos opciones:
   - **«Unirlo a una salida que ya existe»:** se elige, por ejemplo, la salida del sábado a las 9:00. El alumno ocupa una plaza en esa salida como **«Sesión de curso – Open Water (inmersión 4)»** y su instructor queda asignado. No cuenta como una reserva nueva ni se cobra otra vez;
   - **«Crear una sesión nueva»:** fecha, hora, instructor y, si hace falta, barco, comprobando que estén libres.
4. **Todo queda unido a la reserva original:**
   - la sesión aplazada aparece en la ficha de la reserva con la nueva fecha;
   - el curso sigue «en curso» hasta que se completan todas las sesiones;
   - se pasa a **«Curso completado»** solo cuando todas están hechas. Entonces se activa el Log Book y el registro de la titulación.
5. **Sin cobro extra por defecto.** El centro puede añadir un suplemento opcional (por ejemplo, el barco) con su propio enlace de pago.
6. **Aviso automático al alumno** (correo, app y WhatsApp si lo tiene activado): «Tu inmersión 4 del Open Water pasa al sábado 14 a las 9:00 con Marta». Con un botón para confirmar asistencia o pedir otra fecha.
7. **Relación con la cancelación por mal tiempo** (encargo de avisos por WhatsApp): si el centro cancela por mal tiempo una salida en la que hay alumnos de un curso, a esos alumnos **no se les devuelve el dinero**. Su sesión pasa a **«Pendiente de nueva fecha»** y el centro ve en su panel una lista **«Sesiones de curso por recolocar»**. Los buceadores normales de la salida reciben la devolución como hasta ahora.
8. **Recordatorio para el centro:** si una sesión lleva pendiente más de un tiempo configurable (por ejemplo, 30 días), aparece un aviso en su panel.
9. **Agenda y plazas:** la sesión movida descuenta plaza en la salida a la que se une y ocupa al instructor en la nueva fecha, con las mismas reglas sin solapes del motor de agenda (A1) y del inventario único (encargo multicanal).

**Pruebas de esta parte:**
- un Open Water de 4 inmersiones con la 4.ª aplazada se une a la salida del sábado:
  - la plaza baja en esa salida;
  - la reserva original muestra la nueva fecha;
  - no se cobra dos veces;
- cancelar por mal tiempo una salida con 2 alumnos de curso y 6 buceadores normales: los 6 reciben su devolución y los 2 alumnos pasan a «Pendiente de nueva fecha»;
- el curso solo pasa a «Completado» cuando todas las sesiones están hechas.

### 3.6 Pruebas del editor (con personas reales, no solo automáticas)

1. **Prueba de tiempo:** una persona que no conoce WORLDIVES crea desde cero estos servicios:
   - un **Open Water de 3 días** con dos ediciones;
   - una **doble inmersión de los sábados**;
   - un **alquiler de traje**.

   Debe tardar **menos de 3 minutos en cada uno** y sin ayuda. Grabar la pantalla y anotar dónde duda.
2. **Planning:** el Open Water aparece como un bloque de 3 días con el instructor ocupado. La versión «2 mañanas + 2 días completos» respeta las mañanas.
3. **Reserva del buceador:** reservar el curso por una edición concreta, en los dos modos, por WORLDIVES y por el widget de la web del centro.
4. **Migración:** los servicios que ya existían se ven y funcionan igual después del cambio.
5. **Capturas:** cada paso del asistente, en móvil y ordenador.

---

## Parte 4 — Administración

### 4.1 Contraseña solo para ver datos sensibles

- **Qué pasa:** el sistema pide la contraseña para cada acción del administrador, incluso al entrar en el Centro de control.
- **Solución:**
  1. **Entrar en el Centro de control y gestionar la web no pide contraseña otra vez:** puntos, destinos, plantillas, centros, experiencias, estadísticas, QR, etc.
  2. **Solo se pide confirmar la contraseña** (o el código de doble factor si está activo) al ver **datos personales o sensibles**:
     - reservas de los centros con datos de clientes;
     - teléfonos y correos completos;
     - documentos;
     - pagos con datos personales;
     - exportaciones con datos personales;
     - el informe DAC7.
  3. **Una confirmación vale 15 minutos** (configurable) para todas las acciones sensibles. Pasado ese tiempo, se vuelve a pedir.
  4. **Cada acceso sensible** queda registrado con el motivo, como ya dice el encargo de aislamiento entre centros.
  5. **Por defecto, el administrador ve las reservas de los centros solo en cifras agregadas,** sin datos de clientes. WORLDIVES es el motor de reservas: el detalle lo gestiona cada centro. El detalle solo se abre con motivo (soporte, disputa o fraude) y confirmación.

### 4.2 Contador de visitas y reservas en «Actividad»

1. **En Actividad, un bloque discreto** con:
   - **visitas** (páginas vistas y visitantes únicos);
   - **reservas** (totales y por modo);
   - **importe reservado**.

   Para **la temporada actual**, el mes y el total desde el inicio.
2. **Temporada configurable** en Administración (por ejemplo, del 1 de abril al 31 de octubre).
3. **El recuento de visitas es propio y sin cookies de seguimiento:** contadores agregados en el servidor, sin guardar IP completas ni identificar a nadie, de forma que no hace falta banner de cookies para esto. Excluye los robots conocidos y las visitas del propio administrador.
4. **El mismo contador para cada centro** en su panel (visitas a su ficha y sus reservas).

### 4.3 Plantillas de servicio: icono y borrado

1. **Al crear o editar una plantilla,** selector visual de **icono** con todos los iconos que ya existen:
   - inmersión;
   - bautizo;
   - curso;
   - salida privada;
   - viaje de buceo;
   - alquiler de equipo;
   - fotografía;
   - nocturna;
   - snorkel;
   - y el resto.

   Se ve una vista previa de cómo queda.
2. **Borrar plantillas creadas por error:**
   - si **ningún** centro la usa, se borra, con confirmación;
   - si algún centro la usa, se **archiva**: deja de aparecer para nuevos servicios, pero los servicios existentes no se rompen. Se avisa de cuántos centros la usan.
3. **Ordenar las plantillas** arrastrándolas.

### 4.4 Códigos QR con destinos predefinidos (que funcionen)

- **Qué pasa:** hoy se puede escribir cualquier cosa y no está claro a dónde lleva el QR.
- **Solución:**
  1. **El administrador elige el destino de una lista**, nunca escribe una dirección a mano:
     - registro de centros de buceo;
     - registro de buceadores;
     - registro de freelance;
     - explorar puntos de buceo;
     - un punto de buceo concreto (con buscador);
     - listado de centros;
     - un centro concreto (con buscador);
     - experiencias;
     - una experiencia concreta;
     - descargar la app (cuando exista);
     - portada.
  2. **Nombre interno** del QR (por ejemplo «Recepción feria Madrid») y **contador de escaneos** de cada QR, agregado y sin datos personales.
  3. **Botón «Probar enlace»** que abre el destino real antes de descargar.
  4. **Descarga** en PNG en alta resolución, SVG y PDF listo para imprimir con el logo y un texto opcional («Regístrate como centro»).
  5. **QR para los centros desde su panel,** con sus propios destinos:
     - su página de reservas;
     - un servicio concreto;
     - dejar una reseña;
     - su ficha.

     Mismas descargas.
  6. **Dirección corta y estable** (por ejemplo `/q/abc123`), para que, si cambia la ruta interna, los QR ya impresos sigan funcionando. Solo puede apuntar a páginas de WORLDIVES.

---

## Parte 5 — «Vender en tu web», explicado para que lo entienda cualquiera

**Qué es (para el titular):** es la herramienta que permite a un centro poner **un botón de «Reservar» en su propia página web** (o un calendario de salidas). Los clientes reservan y pagan sin salir de la web del centro, y la reserva entra automáticamente en el planning de WORLDIVES. Es la Parte C del encargo multicanal.

**Hoy no se entiende. Debe quedar así:**

1. **Cambiar el nombre en el menú** a **«Reservas desde tu web e Instagram»**.
2. **Pantalla en tres pasos, con dibujos y frases cortas:**
   1. **«¿Qué quieres que reserven?»** Todo tu catálogo, un servicio concreto o un tipo (cursos, inmersiones…).
   2. **«¿Cómo quieres que se vea?»** Tres opciones con vista previa en vivo: un botón «Reservar», un calendario o una lista de próximas salidas. El color y el logo se cogen solos del perfil del centro.
   3. **«Ponlo en tu web»:**
      - un botón **«Copiar código»**;
      - una frase clara: «Pega este código en tu web donde quieras que aparezca el botón»;
      - guías de 3 pasos con capturas para **WordPress, Wix y Squarespace**;
      - un botón **«Enviar las instrucciones a mi informático»**, que manda el código y la guía por correo a quien el centro indique.
3. **Arriba de todo, la opción más fácil para quien no tiene web:**
   - **«Tu enlace de reservas»**, con los botones **Copiar**, **Compartir en WhatsApp** y **Descargar QR**;
   - una frase: «Ponlo en tu Instagram, en Google Maps o mándalo por WhatsApp».
4. **Comprobación automática:** el centro escribe la dirección de su web y WORLDIVES le dice **«✔ Tu botón está funcionando»** o **«Aún no lo encontramos»**.
5. **Lo técnico va al final, plegado** bajo «Para programadores»: API, claves, webhooks y dominios autorizados. El dominio de la web del centro se autoriza solo en el paso 4.
6. **Contador sencillo:** «Este mes te han reservado 12 personas desde tu web».

---

## Parte 6 — Estética: fotos, vídeo de cabecera, tipos de buceo y filtros

**Regla:** los textos, las letras y la maquetación **se quedan como están**. Solo cambian las fotos y la cabecera.

### 6.1 Fotos nuevas (adjuntas por el titular)

1. **Retirar las fotos actuales** que no encajan:
   - fondos de pantalla;
   - tarjetas de **tipos de buceo**;
   - **experiencias** y **destinos**;
   - imágenes de portada de secciones.

   Pasan a `_archivo/`, sin borrarlas.
2. **Colocar las fotos del titular donde corresponda por su contenido:**
   - fondo marino amplio → fondos y portadas;
   - buceador en acción → tipos de buceo;
   - barco o viaje → experiencias;
   - paisaje de costa → destinos;
   - y así con el resto.

   Entregar una **tabla de qué foto va dónde**. Si sobran sitios sin foto adecuada, dejarlos indicados para que el titular mande más, sin rellenar con fotos al azar.
3. **Optimizar cada foto:**
   - WebP en 3 tamaños (móvil, tablet y ordenador) con `srcset`, más JPG de respaldo;
   - carga diferida fuera de la primera pantalla;
   - texto alternativo descriptivo en los 9 idiomas;
   - en el campo de origen o licencia, «Propiedad de WORLDIVES DISCOVERY».
4. **Encuadre:** recorte inteligente para que el motivo principal (el buceador, la manta, el barco) no quede cortado en móvil. Indicar el punto de enfoque de cada foto.

### 6.2 Vídeo de cabecera (archivo .mov adjunto)

1. **Convertir el .mov** a **MP4 (H.264)** y **WebM**, comprimidos para web:
   - menos de 4 MB para ordenador;
   - una versión más ligera para móvil;
   - sin sonido.
2. **Cabecera de la portada a pantalla completa:**
   - `autoplay muted loop playsinline`;
   - imagen fija (póster) del primer fotograma mientras carga;
   - una capa oscura suave para que se lea el texto de la portada, que se mantiene igual.
3. **Si el usuario tiene activado «reducir movimiento» o el ahorro de datos**, se muestra solo la imagen fija.
4. **El vídeo no puede retrasar la carga:** la portada debe seguir cargando rápido (Parte 7).

### 6.3 Filtros de «Puntos de buceo» (ocupan demasiado)

- **Qué pasa:** los filtros (Costa Brava, Comunidad Valenciana, Murcia…) ocupan **más de un tercio de la pantalla** al bajar, y apenas se ven puntos.
- **Solución, como en las webs profesionales de reservas:**
  1. **Una sola barra compacta** de una línea, fija arriba al bajar:
     - buscador;
     - botón **«Filtros (n)»** con el número de filtros activos;
     - orden;
     - cambio entre lista y mapa.
  2. **Zonas como fichas en una fila con desplazamiento lateral**, no en varias filas. En móvil, los filtros se abren en un **panel deslizante desde abajo**.
  3. **Filtros activos como fichas pequeñas** con una ✕ para quitarlos y «Borrar todo».
  4. **Más puntos a la vista:**
     - tarjetas más compactas;
     - en ordenador, 3 o 4 columnas;
     - en móvil, al menos 2 puntos completos visibles en la primera pantalla tras los filtros.
  5. **Los filtros quedan guardados en la dirección** de la página, para compartir la búsqueda.
- **Prueba:** capturas de antes y después a 360, 390, 768, 1024 y 1440 px. La barra de filtros ocupa como máximo una línea al bajar.

### 6.4 Fotos coherentes con el tipo de buceo

1. **Cada tipo de buceo tiene su foto representativa,** acorde a lo que es:
   - arrecife;
   - pared;
   - pecio;
   - cueva o cenote;
   - nocturna;
   - deriva;
   - fondo de arena o posidonia;
   - bloques y rocas;
   - bautizo o aguas someras;
   - profunda;
   - y el resto de tipos que existan.

   Nunca fotos al azar.
2. **Un punto de buceo sin foto propia** muestra la foto de **su tipo principal**. Si el punto tiene foto propia, se usa la suya.
3. **En Administración → Tipos de buceo,** se puede cambiar la foto de cada tipo, con recorte y vista previa.
4. **Se usan las fotos que adjuntó el titular** (punto 6.1). Entregar la **tabla tipo → foto**. Si para algún tipo no hay foto adecuada, **se deja indicado** para que el titular la mande; no se rellena con otra que no corresponda.
5. **Mismas reglas de optimización** que en el punto 6.1: WebP en 3 tamaños, carga diferida y texto alternativo en 9 idiomas.

---

## Parte 7 — Auditoría total y preparado para mucho tráfico

1. **Repasar los cuatro modos completos,** pantalla a pantalla: administrador, centro, freelance y buceador. Con especial atención a:
   - centro: reservas, planning y agenda;
   - freelance: reservas, planning y mi agenda;
   - administración: destinos, puntos y plantillas.

   Corregir todo lo que falle y documentarlo.
2. **Prueba de carga** con k6 o Locust contra el servidor de producción en local:
   - **300 usuarios simultáneos navegando** (portada, explorar, fichas y mapa);
   - **20 reservas por segundo** en salidas distintas, más **reservas simultáneas a la misma salida** para comprobar que no hay sobreventa (Bloque 1 del encargo multicanal);
   - objetivo: el 95 % de las páginas en menos de 500 ms y ningún error.
3. **Si la base de datos actual (SQLite) no aguanta ese objetivo:**
   - activar el modo WAL, los índices que falten y una caché de las consultas públicas;
   - si aun así no llega, entregar al titular un **informe con el plan de paso a PostgreSQL**: qué cambia, cuánto cuesta en el VPS y cuándo conviene hacerlo.
4. **Velocidad, con el vídeo de cabecera incluido:** portada con Lighthouse de 85 o más en móvil y la primera imagen visible en menos de 2,5 segundos en 4G.

---

## Pruebas obligatorias (resumen)

- **Parte 1:**
  - el panel del centro y la agenda del freelance abren sin el error de zona horaria, en Windows y en Linux;
  - el QR de la reserva se ve y funciona;
  - todas las exportaciones descargan en Excel y en CSV, también la DAC7.
- **Parte 2:**
  - al guardar en Administración se vuelve al Centro de control;
  - ningún botón muerto, según el informe de la prueba automática;
  - la rueda del ratón mueve la zona que está bajo el cursor;
  - Administración tiene el menú lateral.
- **Parte 3:** las pruebas de los puntos 3.5 (pasar sesiones a otro día) y 3.6 (prueba de tiempo con una persona real, planning, reserva y migración).
- **Parte 4:**
  - la contraseña no se pide al entrar y sí al ver datos sensibles, durante 15 minutos;
  - el contador de Actividad funciona;
  - las plantillas tienen icono y se pueden borrar o archivar;
  - un QR de cada destino se escanea y lleva bien.
- **Parte 5:**
  - un centro sin conocimientos pone su botón de reservas en una web de prueba y el aviso «✔ Tu botón está funcionando» aparece;
  - el enlace y el QR para Instagram funcionan.
- **Parte 6:**
  - capturas de antes y después de la portada con el vídeo, de las fotos nuevas y de los tipos de buceo;
  - los filtros caben en una sola línea en todos los anchos.
- **Parte 7:**
  - resultado de la prueba de carga;
  - Lighthouse;
  - lista de lo corregido en la auditoría.

## Entrega

- Todo en la **próxima versión**, en los dos zips.
- Notas de versión con el apartado **«Revisión general y usabilidad 15-16/10/2026»**, que incluya:
  - la tabla de estado de cada punto;
  - la tabla de qué foto va en cada sitio y la tabla de tipo de buceo → foto;
  - el informe de botones;
  - el resultado de la prueba de tiempo del editor, con lo que se cambió después;
  - el resultado de la prueba de carga;
  - las capturas de antes y después.
- **En el zip de pruebas,** `centro.prueba` debe traer ya creados con el editor nuevo:
  - un Open Water de 3 días;
  - un curso de «2 mañanas + 2 días completos»;
  - una doble inmersión los sábados;
  - un alquiler;
  - una reserva de curso con una inmersión aplazada, para probar el punto 3.5.
