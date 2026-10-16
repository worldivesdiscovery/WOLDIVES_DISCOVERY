# WORLDIVES DISCOVERY v50.57 · Auditoría de los cuatro modos (revisión general 5.1)

Encargo: repasar los cuatro modos completos, pantalla a pantalla (administración, centro, freelance y buceador), con
especial atención a **centro: reservas, planning y agenda**; **freelance: reservas, planning y mi agenda**; y
**administración: destinos, puntos y plantillas**. Corregir todo lo que falle y documentarlo.

## Cómo se ha hecho

- **En un navegador real** (Chromium), con las cuentas de la demo sobre una copia nueva de su base, en el **ordenador
  (1366 × 900)** y en el **móvil (390 × 844)**: `tests/navegador/e2e_v50_57_modos.py`.
- **Cada pantalla de cada modo**: todas las pestañas del panel de administración (27), del centro (23) y del
  freelance (16), y las páginas del buceador (7: su área, su cuenta, el Log Book, recompensas, puntos, seguro y una
  reserva). En cada una se comprueba que no hay errores de JavaScript, ni respuestas de error del servidor, ni
  textos rotos («undefined», «NaN», «Error interno»…), que tiene contenido y que en el móvil **nada queda fuera de la
  pantalla**.
- **Las pantallas de especial atención**, además:
  - centro y freelance: las reservas, el planning (vista de mes) y la agenda se abren **con sus datos**; la hora, el
    número y el estado de cada reserva se ven enteros en el ordenador y en el móvil; en «Desde» y «Hasta» cabe la
    fecha;
  - administración: en destinos, puntos y plantillas se **abre uno, se guarda sin cambios y se vuelve a la lista con
    «Guardado»**; las flechas de orden de las plantillas están bien en los extremos y después de mover una.
- **A ojo**: las capturas de todas las pantallas (ordenador a página entera y móvil, 146) se han mirado una a una;
  las de especial atención, con detalle. Así salieron casi todos los fallos de abajo, que ninguna comprobación
  automática veía; cada uno tiene ahora la suya.
- Y el recorrido de **todos los botones** de la revisión 2.2 (`botones.md`), que pasa por las mismas pantallas.

## Resultado

**⟪TOTAL⟫ comprobaciones correctas** en la pasada final: las 73 pantallas, en el ordenador y en el móvil, sin
errores, sin textos rotos y sin nada fuera de la pantalla; las de especial atención, con sus datos y guardando bien.

Se han corregido **nueve fallos** (abajo). Para comprobar que las pruebas nuevas los ven de verdad, se han pasado
también con el código anterior: con los estilos de antes de los arreglos del móvil, la prueba de los modos da
**150/166** (las 13 pantallas que se salían y el contador en los tres paneles); el justificante PDF de una reserva
por días falla con cualquiera de sus dos arreglos sin hacer.

## Lo que fallaba y está corregido

| # | Dónde | Qué pasaba | Arreglo |
|---|---|---|---|
| 1 | **Centro › Reservas** y **Freelance › Reservas** | La hora y el número de cada reserva salían cortados («0…», «#1…») en todos los anchos desde la v50.46: los botones de elegir hora al reservar usan la misma clase y sus bordes y rellenos caían sobre la primera columna de la lista. Lo mismo con «1 persona» | Los estilos de esos botones solo valen dentro de su rejilla; los de la reserva quedan igual (comprobado: mismo borde, relleno, letra y ancho) |
| 2 | **Centro › Reservas** y **Freelance › Reservas**, de 761 a 1180 px | El estado de cada reserva (Confirmada, Solicitud…) y su canal no se veían | Van en una segunda línea de la fila |
| 3 | **Centro › Reservas** y **Freelance › Reservas**, en el móvil | Los botones ocupaban la columna de la derecha y dejaban 72 px al cliente («Tom Jan…») y el estado cortado («C…», «W…») | El estado y los botones van cada uno en su línea; el nombre de la actividad, entero en hasta dos líneas |
| 4 | **Centro › Reservas** y **Freelance › Reservas**: filtros «Desde» y «Hasta» | Cogían el estilo de los botones de día al reservar (la misma clase, otra vez): cajas de 60 px en las que no cabía ninguna fecha, en el ordenador y en el móvil. Desde la v50.46 | Esos estilos valen solo dentro de su tira de días; los filtros miden 151 px y los botones de día al reservar quedan igual (74 px, mismo borde y relleno) |
| 5 | **En el móvil, 13 pantallas**: Cobros y pagos (centro y freelance), Ventajas (centro y administración), Seguros, Correos, Planning, Análisis, Vender en tu web, QR y promociones, Mapas, Moderación y el perfil del freelance | Bloques más anchos que la pantalla, y la web recorta lo que pasa del borde derecho (`overflow-x: clip`): frases cortadas y botones sin texto a la vista («Guardar», «Abrir mi panel de Stripe», «Nueva promoción»…). En *Cobros y pagos*, el bloque medía 900 px en una pantalla de 390 | Casi siempre, una rejilla de una columna que crecía hasta el ancho de una tabla de dentro (650-900 px): sus hijos pueden encogerse y las tablas siguen deslizándose de lado en su caja. Las cabeceras con botón y la fila de botones del planning pasan a dos líneas; los textos largos sin espacios («ARCGIS_API_KEY», direcciones) se parten. Barrido de todas las pantallas de los cuatro modos a 390 y a 360 px: nada fuera |
| 6 | **«Visitas y reservas»** (el contador de la 4.2) en el móvil, en administración, centro y freelance | La tabla medía 680-860 px (lo que los paneles dan a toda tabla) y todos sus números quedaban a la derecha, fuera de la vista; a 768 px, la última columna | La tabla de cuatro columnas cortas cabe: 360, 390, 768 y 1366 px con todos los números a la vista |
| 7 | **Ficha de una reserva por días con descuento** (buceador, centro y administración) y su **justificante PDF** | La línea del descuento decía «−10 % desde 3 días: 1 × 0.00 €» (un descuento no tiene precio por unidad) y los importes iban con punto («486.00 EUR»). En el PDF, «1 × 0 €» junto al descuento y «?10 %»: las fuentes del PDF no tienen el signo menos. Desde la v50.44 | La ficha escribe los importes con el formato del idioma y el descuento con su importe («−10 % desde 3 días: -54 €»); el PDF quita el precio por unidad del descuento y escribe el menos con la raya «–», que sus fuentes sí tienen |
| 8 | **Administración › Plantillas** (del recorrido de botones) | «Subir» en la primera y «Bajar» en la última no hacían nada | Salen apagadas y dicen por qué; se recolocan al mover una tarjeta |
| 9 | **Centro › Avisos y WhatsApp**, con el perfil de instructor (del recorrido de botones) | Sin permiso de avisos, los ajustes salían apagados sin decir por qué | El panel lo dice: «Tu perfil no permite cancelar salidas ni avisar a todos los clientes. Pídeselo al propietario del centro.»; el propietario no lo ve |

Capturas de antes y después en `docs/capturas/v50.57/modos/`: la fila de una reserva a 1366, 1100 y 390 px, los
filtros de fecha, el contador en el móvil, *Cobros y pagos* en el móvil, el precio de la reserva por días, el aviso
del instructor y los botones de hora y de día al reservar, que no cambian.

### Lo que se ha corregido en las propias pruebas

- **«Nada se sale por el lado» no veía nada**: comparaba el ancho de la página con el de la pantalla, y la web
  recorta lo que se sale, así que la página nunca era más ancha. Ahora la prueba busca los elementos que pasan del
  borde derecho (sin contar los que están dentro de una caja que se desliza a propósito, como las tablas). Así
  aparecieron las 13 pantallas del fallo 5.
- El recuento final de `e2e_v50_57_modos.py` fallaba: la lista de filas de reservas se llamaba igual que la de
  comprobaciones. Cada línea OK/MAL era correcta; el total, no. Corregido.
- `e2e_avisos.py` (de la v50.47) esperaba que la administración pidiera el motivo al abrir las reservas de los
  centros. Desde la 4.1 se ven en cifras sin pedir nada, y el detalle pide contraseña y motivo: la prueba lo hace así.

## Comprobado y correcto (sin cambios)

- **Centro › Reservas, planning y agenda**: se abren con las reservas de la demo; la vista de mes marca los días con
  salidas y la de lista las enseña día a día; *Planning / agenda* es una sola pestaña en el centro. Cada fila de
  reserva lleva su hora, número, cliente, actividad, personas, importe, estado, canal y seguro.
- **Freelance › Reservas, planning y «Mi agenda»**: con sus datos; el calendario de la agenda marca reservas,
  bloqueos y solicitudes, y «Horario y temporadas» abre sus ajustes.
- **Administración › Destinos, Puntos y Plantillas**: abrir uno y guardarlo sin cambios vuelve a la lista con
  «Guardado», sin errores ni peticiones rechazadas; las flechas de las plantillas, bien en los extremos y después
  de mover una.
- **Buceador**: su área, su cuenta, el Log Book, recompensas, puntos, seguro y la ficha de una reserva (con su QR),
  sin errores y enteras en el móvil.
- **En el móvil, las tablas anchas** (centros, puntos, usuarios, actividad, equipo…) se deslizan de lado dentro de
  su caja, como en el resto de la web: la página no se ensancha y todo se alcanza.
- **Los avisos de claves pendientes** (satélite, Stripe, WhatsApp, correo) salen como avisos claros, nunca como
  error (detalle en `botones.md`).

## Cómo repetirlo

```bash
python3 tests/navegador/e2e_v50_57_modos.py <carpeta-de-capturas>
```

Usa las cuentas de la demo: no va en el paquete de PRODUCCIÓN.
