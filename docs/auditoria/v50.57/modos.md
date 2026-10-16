# WORLDIVES DISCOVERY v50.57 · Auditoría de los cuatro modos (revisión general 5.1)

Encargo: repasar los cuatro modos completos, pantalla a pantalla (administración, centro, freelance y buceador), con
especial atención a **centro: reservas, planning y agenda**; **freelance: reservas, planning y mi agenda**; y
**administración: destinos, puntos y plantillas**. Corregir todo lo que falle y documentarlo.

## Cómo se ha hecho

- **En un navegador real** (Chromium), con las cuentas de la demo sobre una copia nueva de su base, en el **ordenador
  (1366 × 900)** y en el **móvil (390 × 844)**: `tests/navegador/e2e_v50_57_modos.py`.
- **Cada pantalla de cada modo**: todas las pestañas del panel de administración (⟪N_ADMIN⟫), del centro (⟪N_CENTRO⟫)
  y del freelance (⟪N_FREELANCE⟫), y las páginas del buceador (⟪N_BUCEADOR⟫: su área, su cuenta, el Log Book,
  recompensas, puntos, seguro y una reserva). En cada una se comprueba que no hay errores de JavaScript, ni respuestas
  de error del servidor, ni textos rotos («undefined», «NaN», «Error interno»…), que tiene contenido y que en el
  móvil nada se sale por el lado.
- **Las pantallas de especial atención**, además:
  - centro y freelance: las reservas, el planning (vista de mes) y la agenda se abren **con sus datos**; la hora, el
    número y el estado de cada reserva se ven enteros en el ordenador y en el móvil;
  - administración: en destinos, puntos y plantillas se **abre uno, se guarda sin cambios y se vuelve a la lista con
    «Guardado»**; las flechas de orden de las plantillas están bien en los extremos y después de mover una.
- **A ojo**: las capturas de todas las pantallas (ordenador y móvil) se han mirado una a una; las de especial
  atención, con detalle. Así salió el fallo de las reservas, que ninguna comprobación automática veía.
- Y el recorrido de **todos los botones** de la revisión 2.2 (`botones.md`), que pasa por las mismas pantallas.

## Resultado

⟪RESULTADO⟫

## Lo que fallaba y está corregido

| # | Dónde | Qué pasaba | Arreglo |
|---|---|---|---|
| 1 | **Centro › Reservas** y **Freelance › Reservas** | La hora y el número de cada reserva salían cortados («0…», «#1…») en todos los anchos desde la v50.46: los botones de elegir hora al reservar usan la misma clase y sus bordes y rellenos caían sobre la primera columna de la lista. Lo mismo con «1 persona» | Los estilos de esos botones solo valen dentro de su rejilla; los de la reserva quedan igual (comprobado: mismo borde, relleno, letra y ancho) |
| 2 | **Centro › Reservas** y **Freelance › Reservas**, de 761 a 1180 px | El estado de cada reserva (Confirmada, Solicitud…) y su canal no se veían | Van en una segunda línea de la fila |
| 3 | **Centro › Reservas** y **Freelance › Reservas**, en el móvil | Los botones ocupaban la columna de la derecha y dejaban 72 px al cliente («Tom Jan…») y el estado cortado («C…», «W…») | El estado y los botones van cada uno en su línea; el nombre de la actividad, entero en hasta dos líneas |
| 4 | **Administración › Plantillas** (del recorrido de botones) | «Subir» en la primera y «Bajar» en la última no hacían nada | Salen apagadas y dicen por qué; se recolocan al mover una tarjeta |

Capturas de antes y después: `docs/capturas/v50.57/modos/`.

## Comprobado y correcto (sin cambios)

⟪CORRECTO⟫

## Cómo repetirlo

```bash
python3 tests/navegador/e2e_v50_57_modos.py <carpeta-de-capturas>
```

Usa las cuentas de la demo: no va en el paquete de PRODUCCIÓN.
