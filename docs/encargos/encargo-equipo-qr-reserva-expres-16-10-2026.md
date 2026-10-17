# WORLDIVES DISCOVERY — Encargo unificado: equipo del centro enlazado por QR + reserva exprés desde la web del centro (16/10/2026)

Eres el programador de WORLDIVES DISCOVERY. Trabaja sobre la **última versión** del código. Este encargo junta dos bloques que se entregan en la **misma versión**:

- **Bloque 1:** equipo del centro con cuentas propias, enlazadas por QR.
- **Bloque 2:** reserva exprés desde la web del centro.

Hazlos en este orden. Los dos son independientes, pero el bloque 2 usa la función de reserva única del encargo del motor multicanal: si falta, se completa aquí.

## Reglas comunes

1. **Antes de cada punto,** comprueba si ya está hecho y márcalo «Ya estaba», «Completado», «Nuevo» o «Pendiente de decisión». No rehagas lo que funciona ni dupliques funciones.
2. **Textos nuevos en los 9 idiomas,** sin restos en inglés. Lo que falte, «Pendiente de traducción» con el castellano de reserva.
3. **Web y app** con la misma base y el mismo diseño, en Clásico y Futurista.
4. **Los permisos y los precios los decide siempre el servidor.**
5. **Entrega en dos zips:** `-produccion` (limpio) y `-pruebas` (con las cuentas fijas de admin, centro, freelance y buceador y los datos de demostración).
6. **Notas de versión** con dos apartados, «Equipo del centro» y «Reserva exprés», cada uno con la tabla de estado, las capturas de antes y después y lo «Pendiente de decisión».

---

# BLOQUE 1 — Equipo del centro con cuentas propias, enlazadas por QR

## Qué hay hoy y qué falta

En **Panel del centro → Equipo** están los perfiles (Propietario, Encargado, Recepción, Instructor, Instructor máster y «Crear perfil»), cada uno con la lista de lo que puede hacer. **Falta lo principal:** cómo entra cada persona. Si todos usan la cuenta del centro, tienen que estar cambiando de cuenta y no se sabe quién ha hecho qué.

## Cómo tiene que funcionar

1. **Cada persona del equipo tiene su propia cuenta de WORLDIVES.** Los instructores y divemasters, normalmente como **freelance**. La recepción puede usar una cuenta normal.
2. **El centro enlaza esa cuenta a un perfil de su equipo** (por ejemplo, Encargado) **escaneando el QR personal** de la persona desde la web o la app.
3. **A partir de ahí,** esa persona entra con **su** cuenta, en **su** móvil, y ve el centro con los permisos de su perfil. No tiene que meterse nunca en la cuenta del centro.
4. **Un freelance puede estar enlazado a varios centros a la vez,** también en otros países. En su agenda ve, día a día, su trabajo propio y lo que le ha asignado cada centro.

## Reglas de este bloque

1. **Antes de empezar,** revisa lo que ya existe y anótalo («Ya estaba», «Completado», «Nuevo» o «Pendiente de decisión»):
   - el equipo del centro y sus perfiles con permisos;
   - el selector de perfil de la app (encargo de la app en 3 módulos, punto 3.1);
   - el cambio de contexto entre centros y el aislamiento de datos (encargo de aislamiento entre centros, Parte B, punto 6);
   - el motor de agenda común con instructores y barcos.

   Amplía lo que hay. **No dupliques el sistema de roles ni la agenda.**

## Parte 1 · El QR personal de cada usuario

1. **«Mi QR»** en la app y en la web, en Mi área, y a un toque desde el menú de perfil. Lo tienen todos los usuarios: buceador, freelance y centro.
2. **Muestra:**
   - el QR, grande;
   - el nombre y la foto;
   - el tipo de cuenta;
   - un **código corto de 6 caracteres** debajo, para cuando no se puede escanear.
3. **Seguridad:**
   - el QR **no lleva datos personales**, solo un código firmado;
   - **cambia cada 60 segundos** y solo sirve una vez, para que una captura de pantalla vieja no valga;
   - el código corto caduca a los 10 minutos;
   - el cambio de código es invisible para el usuario: siempre abre «Mi QR» y lo enseña, no tiene que hacer nada más.
4. **El mismo QR personal servirá en el futuro** para otras cosas (Buddies, check-in). Prepáralo como un servicio común que lee el QR y sabe qué hacer según quién lo escanee y desde dónde.

## Parte 2 · El centro enlaza a una persona a un perfil del equipo

1. **En cada perfil del equipo** (Encargado, Instructor…), botón **«Enlazar persona»**, junto a la lista de permisos.
2. **Tres formas de enlazar,** en este orden:
   - **Escanear su QR** con la cámara del móvil o del ordenador (la forma principal);
   - **escribir su código corto**;
   - **invitar por correo,** si la persona aún no tiene cuenta: le llega un enlace para crearla (como freelance o como cuenta normal) y queda enlazada al terminar.
3. **Al escanear, el centro ve** la foto y el nombre de la persona, su tipo de cuenta y sus titulaciones si las tiene subidas, y elige:
   - **perfil:** el que estaba abierto, que se puede cambiar;
   - **duración:**
     - **«Fijo en el equipo»**, sin fecha de fin;
     - **«Por días»**, con fechas de inicio y fin: por ejemplo, solo el 20/10 o del 20 al 27/10. Al terminar, el acceso se quita solo.
4. **La persona tiene que aceptar.** Le llega al momento un aviso en la app: «Centro de Buceo Mar Azul quiere añadirte a su equipo como Encargado, del 20 al 27/10. ¿Aceptas?».
   - Si los dos están juntos, acepta en un toque y queda enlazada en segundos.
   - **Nadie queda enlazado sin su «sí».**
5. **Una vez enlazada,** la persona aparece en la lista del equipo con su foto, su perfil, las fechas y su estado (Activo, Pendiente de aceptar o Terminado).

## Parte 3 · Qué ve la persona enlazada

1. **Una sola cuenta, varios perfiles.** En la app y en la web, arriba, el **selector de perfil** que ya está previsto: «Mi perfil freelance · Centro Mar Azul (Encargado) · Centro Coral (Instructor) · Buceador». Se cambia en un toque.
2. **Dentro de cada centro** ve solo lo que permite su perfil. Por ejemplo, el instructor ve Hoy, Agenda, sus salidas, la lista del barco y Escanear, pero no ve los cobros. Son los mismos permisos que ya tiene cada perfil.
3. **Su agenda (Mi agenda) junta todo,** día a día:
   - sus trabajos de freelance;
   - lo que le ha asignado cada centro: salidas, cursos y bautizos, con hora, punto, barco y número de buceadores.

   Cada centro con su color y su nombre. Ejemplo: «Martes 20 · Centro Mar Azul · 9:00 Doble inmersión · Barco Neptuno · 8 buceadores».
4. **Avisos:**
   - cuando un centro le asigna o le cambia una salida;
   - el resumen de la agenda de mañana, que ya existe.
5. **Al terminar el enlace,** o si el centro le quita del equipo, el perfil de ese centro desaparece de su selector y pierde el acceso al momento. Su historial de trabajos con ese centro le queda en su agenda pasada, sin datos de los clientes.

## Parte 4 · Qué ve el centro

1. **En el planning,** las personas enlazadas aparecen como recursos, igual que hoy los instructores: se les asignan salidas, cursos y bautizos.
2. **Disponibilidad real.** Si el freelance tiene ese día ocupado con su propio trabajo o con otro centro, el centro lo ve como **«Ocupado»**, sin ver con quién ni para qué, y no puede asignarle esa franja. Lo controla el motor de agenda común: nunca dos trabajos solapados.
3. **Registro de actividad:** cada acción queda con el nombre de quien la hizo, por ejemplo «Ana (Encargado) canceló la salida de las 16:00».

## Parte 5 · Privacidad y aislamiento

1. **El centro no ve nada de la cuenta propia del freelance:** ni sus clientes, ni sus reservas, ni sus cobros, ni su trabajo con otros centros. Solo su nombre, foto, titulaciones y si está libre u ocupado.
2. **El freelance, dentro de un centro,** solo ve los datos de ese centro que permite su perfil, y solo mientras dure el enlace. Lo que vea de los clientes de un centro nunca pasa a su cuenta de freelance.
3. **Cambio de centro explícito:** al cambiar de perfil en el selector, la sesión cambia de contexto, como dice el encargo de aislamiento. Nunca se mezclan datos de dos centros en la misma pantalla.
4. **Desenlazar:**
   - el centro puede quitar a cualquiera del equipo;
   - la persona puede salir de un centro desde su cuenta;
   - el **Propietario** no se puede quitar; para cambiarlo hay un proceso aparte de «Transferir la propiedad», con confirmación por correo.
5. **Recepción en un ordenador compartido:** la persona entra con su cuenta y puede marcar «Mantener la sesión iniciada en este ordenador». Botón «Cerrar sesión» siempre visible.

## Parte 6 · Planes (decidido por el titular el 16/10/2026)

### 6.1 Planes del centro: cuántas personas de equipo

| Plan del centro | Equipo |
|---|---|
| **Ficha gratuita** | Nadie. Solo la cuenta del propietario. El botón «Enlazar persona» aparece bloqueado con «Disponible en el plan Motor de reservas». |
| **Motor de reservas** | El propietario **y una persona más, solo con el perfil Recepción**. Los demás perfiles se ven, pero bloqueados con «Disponible en el plan Pro». |
| **Pro** | El propietario y **hasta 15 personas** más, con cualquier perfil, y puede crear perfiles propios con los permisos que quiera. |

- **El límite lo comprueba el servidor** al enlazar y al aceptar. Las invitaciones pendientes cuentan para el límite.
- **Si un centro baja de plan** y tiene más personas de las que permite el nuevo plan:
  - elige quién se queda;
  - el resto queda **en pausa**, sin acceso, pero no se borra;
  - si vuelve a subir de plan, se reactivan con un clic.
- **No se muestran precios** en estos avisos, solo el nombre del plan y el botón «Ver planes».

### 6.2 Planes del freelance: para estar en un equipo hace falta cuenta de freelance

1. **Solo se pueden enlazar como Instructor, Instructor máster, Encargado u otros perfiles de trabajo** cuentas de **freelance**. Si el centro escanea a alguien con cuenta de buceador, le aparece: «Para unirse a tu equipo, tiene que activar su perfil de freelance (es gratis)», y a la persona le llega el enlace para activarlo en un minuto.
2. **El perfil Recepción** es la excepción: se puede enlazar con una cuenta normal.
3. **Plan gratuito del freelance:**
   - todo lo del buceador;
   - **que los centros le enlacen a su equipo**;
   - **ver en su agenda el planning que le asigna cada centro**, con avisos.

   **Nada más:** sin servicios propios, sin reservas ni cobros propios.
4. **Plan Pro del freelance:** todo lo del freelance completo (escaparate, servicios, reservas, cobros, agenda propia y carteles), más lo del plan gratuito.
5. Que el freelance gratuito tenga o no **escaparate público** queda **pendiente de confirmar por el titular**. Hasta que lo confirme, no se muestra.

### 6.3 Enlazar a distancia: «Mándame tu QR»

El caso real: el centro le pide al instructor por la noche «mándame tu QR» y le envía el planning de mañana.

1. Como el QR cambia cada 60 segundos, **una foto o captura del QR no sirve**. Por eso, en «Mi QR» hay un botón **«Compartir para enlazar»** que crea un **enlace de invitación**:
   - para enviarlo por WhatsApp, correo o cualquier app;
   - válido **24 horas** y para **un solo uso**.
2. **El centro abre el enlace** (o pega el código) en «Enlazar persona» y sigue igual que con el QR: elige perfil y fechas.
3. **Al freelance le llega la petición** y la acepta en un toque. Al momento ve en su agenda las salidas que el centro ya le haya asignado para mañana.
4. El freelance puede **anular un enlace compartido** antes de que se use.

## Comprobaciones antes de entregar

1. **Enlazar con QR:**
   - el centro escanea el QR de `freelance.prueba` desde el móvil y desde el ordenador;
   - el freelance acepta y aparece como Encargado en segundos.
2. **QR caducado:** una captura del QR de hace 2 minutos no sirve. El código corto funciona y caduca a los 10 minutos.
3. **Invitación por correo** a alguien sin cuenta: crea la cuenta y queda enlazado.
4. **Enlace «Por días»:** el 20/10 tiene acceso y el 21/10 deja de tenerlo solo.
5. **Dos centros:** el mismo freelance enlazado a dos centros de prueba ve los dos en el selector y en su agenda, cada uno con su color. Ninguno de los dos centros ve los datos del otro ni los clientes propios del freelance.
6. **Solapes:** el centro no puede asignarle una salida a una hora en la que el freelance ya trabaja para el otro centro o para él mismo. Lo ve como «Ocupado».
7. **Permisos:** con cada perfil (Encargado, Recepción, Instructor, Instructor máster), probar en el servidor que solo puede hacer lo que su lista permite. Un instructor que intenta ver cobros recibe una respuesta de que no existe.
8. **Desenlazar,** desde el centro y desde la persona: el acceso se quita al momento, también en una sesión abierta en la app.
9. **Registro de actividad** con el nombre de cada persona.
10. **Planes:**
    - con Ficha gratuita no se puede enlazar a nadie;
    - con Motor de reservas solo una persona, y solo como Recepción;
    - con Pro hasta 15, y la persona número 16 se rechaza;
    - al bajar de Pro a Motor de reservas, el centro elige quién se queda y el resto queda en pausa sin borrarse.
11. **Freelance gratuito:**
    - se le puede enlazar y ve el planning asignado;
    - no puede crear servicios propios.

    Una cuenta de buceador no se puede enlazar como Instructor y recibe el enlace para activar su perfil de freelance.
12. **«Compartir para enlazar»:**
    - el enlace enviado por WhatsApp funciona una vez y caduca a las 24 horas;
    - una captura del QR no sirve.
13. **Datos de prueba:** en el zip de pruebas, `centro.prueba` con `freelance.prueba` ya enlazado como Instructor, y un segundo centro de prueba para probar los dos centros.
14. **Notas de versión** con el estado de cada parte, capturas en ordenador y móvil, y lo «Pendiente de decisión».

---

# BLOQUE 2 — Reserva exprés desde la web del centro

## Qué pasa hoy

El titular ha probado **Panel del centro → Vender en tu web** y la reserva que ve el cliente desde la web del centro:

- **no es atractiva;**
- **obliga a hacer mucho scroll** antes de reservar;
- **pide los nombres de todos los buceadores** antes de poder enviar;
- **tiene demasiadas pantallas** hasta pagar;
- tiene textos en inglés, como «Send request».

Un cliente que llega desde la web de un centro no conoce WORLDIVES. Si la reserva es lenta, se va.

## Objetivo (la regla de oro)

**Reservar y pagar en menos de 60 segundos**, con el objetivo de 30 segundos, desde que el cliente pulsa «Reservar» en la web del centro. Como mucho **dos pantallas y el pago**, y **8 toques** o menos para una reserva normal (un servicio, una fecha, 2 personas).

## Reglas de este bloque

1. **Antes de empezar,** mide el recorrido actual con un cronómetro: segundos, toques, pantallas y cuánto scroll. Haz capturas del **antes**.
2. **Un solo componente de reserva exprés,** con la función de reserva única del encargo multicanal, para:
   - el widget en la web del centro (botón, calendario incrustado y lista);
   - la página de reservas del centro y el enlace directo para Instagram y WhatsApp.

   **Pendiente de decisión del titular:** usarlo también en la ficha del centro dentro de WORLDIVES.
3. **Sin cuenta obligatoria:** se reserva como invitado. La cuenta se ofrece al final, opcional.

## Parte 1 · Cómo se ve

1. **Con la imagen del centro:**
   - arriba, una franja compacta con la foto de portada del centro, su logo, su nombre y su valoración;
   - el color de los botones es el que elige el centro;
   - WORLDIVES solo aparece en el pie: «Reservas con tecnología de WORLDIVES».
2. **En el móvil,** se abre como una **hoja que sube desde abajo** a pantalla casi completa. **En el ordenador,** una ventana centrada de unos 480 px de ancho encima de la web del centro. Se cierra con ✕ o tocando fuera, preguntando antes si ya se había elegido algo.
3. **Cada pantalla cabe sin scroll** en un móvil de 390 × 844 para un servicio normal.
4. **Barra fija abajo,** siempre visible:
   - a la izquierda, el **total** («2 × 50 € = 100 €»), que al tocarlo se despliega con el desglose;
   - a la derecha, el **botón principal**, que dice lo que va a pasar: «Continuar», «Pagar 100 €» o «Enviar solicitud».
5. **Confianza a la vista,** en una línea con iconos pequeños:
   - «Pago seguro»;
   - la política de cancelación en corto, por ejemplo «Cancelación gratis hasta 48 h antes»;
   - «Confirmación inmediata» o «El centro confirma en menos de X h».
6. **Detalles cuidados:**
   - esqueletos de carga en lugar de pantallas en blanco;
   - transiciones suaves de 150 a 250 ms entre pasos;
   - estados claros al pulsar;
   - letra legible (16 px o más en los campos);
   - tema claro por defecto, con el color del centro.

## Parte 2 · Pantalla 1: «¿Qué y cuándo?»

Todo en una sola pantalla.

1. **El servicio:**
   - si el cliente viene de un botón de un servicio concreto («Reservar bautizo»), **ya está elegido** y no se pregunta;
   - si no, tarjetas compactas con foto, nombre, duración y precio «desde», en una fila que se desliza. Un toque y se elige.
2. **La fecha:** una **tira de días** que se desliza, con los próximos 14 días y un punto verde en los días con plazas. Al final, «Más fechas» abre el calendario del mes. **Se marca sola la primera fecha disponible.**
3. **La hora:** botones con cada salida («9:00 · Quedan 3»). Si solo hay una hora ese día, ya va marcada.
4. **Personas:** botones − / + (por defecto 1), limitados a las plazas libres.
5. **Equipo:** una línea plegada, «¿Necesitas equipo de alquiler?», que despliega las piezas del encargo de alquiler de equipo. Plegada por defecto.
6. **Extras** (nitrox, fotos): igual, plegados, solo si el servicio los tiene.
7. **Botón «Continuar»** en la barra fija.

## Parte 3 · Pantalla 2: «Tus datos»

1. **Solo los datos de quien reserva:**
   - nombre y apellidos;
   - correo;
   - teléfono, con el prefijo del país puesto según el idioma o la ubicación.

   Con autocompletado del navegador (`autocomplete="name"`, `email`, `tel`), para que se rellenen en un toque.
2. **No pedir ahora los nombres de los demás buceadores.** Debajo, una línea: «Los datos de tus acompañantes los puedes completar después; te enviamos un enlace». Ese enlace es el punto E6 del encargo del motor de reservas: cada participante pone su nombre, su titulación y sus tallas antes de la inmersión.
3. **Titulación o nivel,** solo si el servicio lo exige y solo de quien reserva, con botones rápidos: «Sin titulación», «Open Water», «Advanced», «Rescue o más».
4. **Aceptar la política de cancelación y las condiciones del centro** con una sola casilla, con el enlace para leerlas.
5. **Pago en la misma pantalla,** debajo de los datos, sin pasar a otra página:
   - con **«Pago al reservar»**: formulario de pago de Stripe integrado, con **Apple Pay, Google Pay y Link** arriba. Se cobra en la cuenta del centro. El botón dice «Pagar 100 €»;
   - con **«Bajo petición»**: no se pide tarjeta. El botón dice «Enviar solicitud» y debajo: «No se cobra nada hasta que el centro acepte».
6. **Errores junto a cada campo,** en el momento («Revisa el correo»), nunca al final con un mensaje general.

## Parte 4 · Pantalla final: «¡Reservado!»

1. **Confirmación grande:**
   - el servicio, la fecha, la hora, el punto de encuentro y el total pagado;
   - el **QR de la reserva**.
2. **Botones:**
   - «Añadir al calendario»;
   - «Cómo llegar»;
   - «Escribir al centro por WhatsApp»;
   - «Completar los datos de mis acompañantes», si faltan.
3. **Al final, opcional:** «Guarda tu inmersión en tu Log Book: crea tu cuenta de WORLDIVES con un toque». Los datos ya están rellenos; solo falta la contraseña o entrar con Google o Apple.
4. **El correo de confirmación** sale al momento, con el logo del centro.

## Parte 5 · Más rápido todavía

1. **Enlaces con todo elegido:** el centro puede crear un enlace o un botón con el servicio y la fecha ya puestos, por ejemplo «Reserva el bautizo del sábado». El cliente entra directamente en la pantalla 2.
2. **Recordar al cliente,** solo si quiere: casilla «Recordar mis datos en este dispositivo». La próxima vez, los datos ya aparecen rellenos. Se guardan en el propio dispositivo, sin cookies de seguimiento.
3. **Plazas apartadas mientras paga,** 10 minutos, como dice el encargo multicanal, con un contador discreto: «Te guardamos las plazas 9:58».
4. **Si no quedan plazas a esa hora,** se proponen al momento las horas o los días más cercanos con plazas, sin volver atrás.

## Parte 6 · «Vender en tu web» en el panel del centro

La pantalla del centro también tiene que convencer.

1. **Vista previa en vivo,** con los datos reales del centro, en dos marcos: **móvil** y **ordenador**. Al cambiar un ajuste, se ve el cambio al momento.
2. **Ajustes visibles:**
   - formato (botón, calendario o lista);
   - color de los botones;
   - qué servicios se muestran;
   - idioma.
3. **Un solo botón «Copiar código»** y, debajo, guías de 3 pasos con capturas para WordPress, Wix y Squarespace.
4. **Botón «Probar como cliente»:** abre la reserva exprés tal como la verá un cliente, en modo prueba, sin cobrar.

## Comprobaciones antes de entregar

1. **Cronómetro de antes y después,** con una prueba automática que se mueve a ritmo humano (con pausas de lectura) desde el clic en «Reservar» hasta la confirmación:
   - **Pago al reservar,** 2 personas, con Apple o Google Pay de prueba: menos de 30 segundos y 8 toques o menos;
   - **con tarjeta escrita a mano:** menos de 60 segundos;
   - **Bajo petición:** menos de 30 segundos.
2. **Sin scroll** en las pantallas 1 y 2 a 390 × 844 para un servicio normal sin extras.
3. **Los nombres de los acompañantes no se piden** antes de reservar, y les llega el enlace para completarlos.
4. **Todo traducido** en los 9 idiomas. Ningún texto en inglés si el idioma es otro.
5. **El widget pegado en `web-de-centro-ejemplo.html`** funciona en los tres formatos, en móvil y en ordenador, y no rompe los estilos de la página.
6. **Enlace con servicio y fecha ya elegidos:** entra directo en «Tus datos».
7. **Sin plazas:** propone otras horas al momento.
8. **El widget carga en menos de 2 segundos** en un móvil 4G de gama media.
9. **Capturas de antes y después** de cada pantalla, en móvil y ordenador, con dos colores de centro distintos.
10. **Notas de versión** con:
    - tiempos y toques antes y después;
    - lo que quede «Pendiente de decisión».
