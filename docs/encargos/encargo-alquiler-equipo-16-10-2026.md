# WORLDIVES DISCOVERY — Encargo: alquiler de equipo como extra dentro de la inmersión (16/10/2026)

Eres el programador de WORLDIVES DISCOVERY. Trabaja sobre la **última versión** del código.

## Qué pasa hoy

El titular ha creado como centro un servicio «Inmersión simple», a 50 € por persona, con «Pago al reservar», política de cancelación y foto de plantilla. **No puede añadir el alquiler de equipo a esa inmersión.** Hoy el alquiler aparece como un servicio aparte, y eso no es como funciona un centro de buceo.

## Cómo tiene que funcionar

**El alquiler de equipo es un extra dentro de la inmersión, no un servicio.** El buceador reserva la inmersión y, en la misma reserva, marca las piezas que necesita. El centro las ve en la reserva y las tiene preparadas al llegar.

- **La botella y los plomos van siempre incluidos en la inmersión.** No aparecen como piezas de alquiler ni se cobran aparte. En la ficha y en la reserva se muestra «Incluido: botella y plomos».
- **El alquiler suelto como servicio aparte se mantiene, pero en segundo plano:** sigue existiendo la tarjeta «Alquiler de equipo» en el asistente de servicios (encargo del 15-16/10, punto 3.2) para quien solo quiera alquilar. No es el camino normal.

## Reglas generales

1. **Antes de empezar:** localiza lo que ya existe y anótalo en las notas («Ya estaba», «Completado», «Nuevo» o «Pendiente de decisión»):
   - el paso «Equipo» de la reserva de la v50.27, con las piezas, el contador y las tallas;
   - el precio por pieza en el servidor (`codigo:cantidad`);
   - el paso 4 «Extras» del asistente de servicios del encargo del 15-16/10.

   Reutiliza lo que sirva. **No crees un segundo sistema de extras.**
2. **Mismo diseño que el resto de la web y de la app:** mismas tarjetas, botones y colores, en Clásico y Futurista.
3. **Web y app** con la misma base.
4. **Textos nuevos** en los 9 idiomas, con «Pendiente de traducción» y el castellano de reserva si falta alguno.
5. **Entrega en dos zips:** `-produccion` (limpio) y `-pruebas` (con las cuentas fijas y los datos de demostración).

---

## Parte 1 · El centro configura su equipo de alquiler una sola vez

Nueva sección **Panel del centro → Equipo de alquiler**. El freelance que alquile equipo tiene la misma sección.

1. **Lista de piezas ya creada por defecto**, cada una con su icono, que el centro activa o desactiva con un interruptor:

   | Pieza | Tallas que se piden al reservar |
   |---|---|
   | Máscara | Opción «graduada» si el centro la tiene |
   | Aletas | Número de pie (UE) |
   | Escarpines | Número de pie (UE) |
   | Traje o neopreno | Talla (XS a XXL) y grosor que ofrece el centro (3, 5, 7 mm o semiseco) |
   | Capucha | Talla |
   | Guantes | Talla |
   | Chaleco (jacket) | Talla (XS a XXL) |
   | Regulador (con octopus y manómetro) | — |
   | Ordenador de buceo | — |
   | Linterna | — |
   | Boya de superficie | — |

   **Botella y plomos no salen en esta lista**: van siempre incluidos.
2. **El centro puede añadir piezas propias** con nombre, icono y tallas, por ejemplo «Cámara» o «Cuchillo».
3. **Precio de cada pieza:** por inmersión o por día, a elegir por el centro. Puede poner 0 € si la pieza va gratis.
4. **«Equipo completo» con precio cerrado:** el centro elige qué piezas forman su equipo completo y le pone un precio, normalmente más barato que la suma de las piezas.
5. **Stock por talla, opcional:** si el centro lo rellena (por ejemplo, 2 jackets talla M), no se pueden reservar más de las que tiene ese día. Si no lo rellena, no hay límite. Es el punto E11 del encargo del motor de reservas: hazlo con ese mismo motor.
6. **Datos de ejemplo** ya rellenos en la cuenta de prueba del centro, con precios orientativos que el centro cambia.

## Parte 2 · Cada servicio elige si ofrece alquiler

En el asistente de servicios (paso 4, «Precio y plazas → Extras»), y al editar un servicio ya creado:

1. **Interruptor «Ofrecer alquiler de equipo en este servicio».**
   - **Activado por defecto** en inmersiones y salidas en barco.
   - **En bautizos y cursos**, por defecto «Equipo incluido en el precio», porque normalmente el centro lo pone. El centro puede cambiarlo.
2. **Por defecto se ofrecen todas las piezas activas** del centro con sus precios. El centro puede quitar piezas o cambiar algún precio solo para ese servicio, en «Más opciones».
3. **La vista previa** del paso 6 enseña cómo lo verá el buceador.
4. **Los servicios que ya existen** pasan a ofrecer el alquiler con las piezas activas del centro, sin que el centro tenga que hacer nada.
5. **Si el centro todavía no ha configurado su equipo,** el interruptor lo lleva a la Parte 1 con un aviso: «Primero indica qué equipo alquilas».

## Parte 3 · El buceador lo elige al reservar

En el paso «Equipo» de la reserva, en la web, la app, el widget y el enlace directo:

1. **Dos tarjetas grandes:** «Llevo mi equipo» (marcada por defecto) y «Necesito equipo».
2. **Al elegir «Necesito equipo»** se despliega una cuadrícula de piezas con su icono, nombre y precio, que se marcan con un toque. Debajo, «Incluido: botella y plomos».
3. **Por buceador.** Si la reserva es para varias personas, una pestaña o fila por buceador («Tú», «Buceador 2»…). Cada uno marca sus piezas y sus tallas. Botón «Igual que el anterior» para copiar.
4. **Tallas solo de las piezas marcadas,** con selectores rápidos (número de pie, talla de traje). Nada de escribir a mano, salvo una nota opcional: «Algo más que deba saber el centro».
5. **«Equipo completo» en un toque,** si el centro lo ofrece: marca todas sus piezas y aplica el precio cerrado. Si el buceador desmarca una pieza, se vuelve al precio por piezas y se le avisa con el importe nuevo.
6. **Precio a la vista:** el resumen de la reserva suma el equipo línea a línea al momento, por ejemplo «Inmersión 50 € + Máscara 5 € + Aletas 5 € = 60 €». **El precio lo calcula siempre el servidor.**
7. **Sin stock** de una talla: esa talla sale como «No disponible» y no se puede marcar.
8. **Con los dos modos de reserva:**
   - «Pago al reservar»: el equipo se cobra junto con la inmersión;
   - «Bajo petición»: va en la solicitud, y el centro lo ve antes de aceptar.
9. **Cambiar el equipo después:** el buceador puede añadir o quitar piezas desde Mis reservas hasta el plazo de cancelación del servicio. La diferencia se cobra o se devuelve automáticamente.
10. **Recordar la elección:** la próxima vez que reserve en ese centro, las tallas aparecen ya puestas.

## Parte 4 · El centro lo ve y lo prepara

1. **En la ficha de la reserva:** cada buceador con sus piezas y tallas, por ejemplo «Ana · Traje M 5 mm · Aletas 39 · Máscara».
2. **En la lista del barco** (manifiesto) y en la pantalla **Hoy** de la app, en la fila de cada buceador.
3. **Resumen «Equipo para preparar»** por salida y por día, agrupado por pieza y talla: «Aletas: 2 × 39, 1 × 42 · Trajes: 2 × M, 1 × L · Reguladores: 3». Se puede imprimir y compartir como PDF.
4. **Si al llegar al centro falta algo** («se me ha olvidado la linterna»), el centro añade la pieza a la reserva desde su panel en un toque, y elige «Pagado en el centro» o «Enviar enlace de pago».
5. **El aviso de reserva nueva** al centro (correo y app) incluye el equipo pedido.

## Parte 5 · Datos y compatibilidad

1. **Las reservas antiguas** con el formato `codigo:cantidad` siguen viéndose y cobrándose bien.
2. **Los extras de equipo se guardan por buceador**, con pieza, talla y precio en el momento de la reserva. Si el centro cambia luego sus precios, las reservas ya hechas no cambian.
3. **Exportaciones:** el equipo de cada reserva sale en la exportación a Excel y CSV de reservas.
4. **API y widget:** la disponibilidad y el precio del equipo se consultan y se envían por la misma función de reserva única del encargo multicanal.

---

## Comprobaciones antes de entregar

1. **Como centro:**
   - activar unas piezas, poner precios y un «Equipo completo»;
   - crear «Inmersión simple» a 50 € con «Pago al reservar»;
   - comprobar que el alquiler aparece activado y bien en la vista previa.
2. **Reservas como buceador:**
   - solo máscara y aletas: total 60 € con las piezas a 5 €;
   - dos buceadores, uno con traje, máscara, aletas y escarpines, y otro solo con boya;
   - una con «Equipo completo».
3. **Que no aparezcan botella ni plomos** como piezas de alquiler en ningún sitio, y sí como «Incluido».
4. **Lo que ve el centro:** la reserva, el manifiesto, Hoy y el resumen «Equipo para preparar» muestran exactamente lo pedido, con tallas.
5. **Stock:** con 2 jackets M en stock, una tercera reserva no puede pedir jacket M.
6. **Cambios:** el buceador añade una linterna desde Mis reservas y se le cobra la diferencia. El centro añade una pieza en el mostrador como «Pagado en el centro».
7. **Con «Bajo petición»:** el equipo llega en la solicitud y se cobra solo al pagar tras aceptar.
8. **Reservas antiguas** de la demo siguen funcionando.
9. **Pantallas a revisar** en ordenador y en móvil a 360 px, en Clásico y Futurista, sin errores en la consola:
   - el paso «Equipo» de la reserva;
   - la configuración del equipo;
   - el resumen «Equipo para preparar».
10. **Notas de versión** con el estado de cada parte y capturas.
