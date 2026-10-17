# WORLDIVES DISCOVERY v50.58 · Los cuatro modos con el código final (revisión y usabilidad, parte 7)

La parte 7 del encargo de los días 15 y 16/10/2026 pide repetir la auditoría de la v50.57 con el código final de esta
versión. Esta versión trae el panel con menú lateral, el asistente de servicios, el progreso del curso, «Reservas desde
tu web e Instagram» y la foto por tipo. La auditoría se repite con la misma herramienta, sin rebajar ninguna
comprobación.

## Cómo se ha hecho

- `tests/navegador/e2e_v50_57_modos.py`, en Chromium, con las cuentas de la demo sobre una copia nueva de su base, en
  el **ordenador (1366 × 900)** y en el **móvil (390 × 844)**.
- Se recorren todas las pestañas del panel de administración, del centro y del freelance (las de esta versión
  incluidas: «Reservas desde tu web e Instagram», «Equipo de alquiler», «Vídeos y vida marina», «Tipos de buceo»…) y
  las páginas del buceador.
- En cada pantalla se comprueba que:
  - no hay errores de JavaScript ni respuestas de error del servidor;
  - no hay textos rotos («undefined», «NaN», «Error interno»…);
  - tiene contenido;
  - en el móvil, nada queda fuera de la pantalla.
- Las pantallas de especial atención (reservas, planning y agenda del centro y del freelance; destinos, puntos y
  plantillas de la administración) se abren con sus datos y se guardan sin cambios.

## Resultado

**186 de 186 comprobaciones correctas** con el código final, después de corregir lo que encontró la primera pasada:

| Encontrado | Qué pasaba | Arreglo |
|---|---|---|
| Administración → «Lotes nuevos», en el móvil | El ejemplo de lote JSON (`{"zone":"…","items":[…]}`) es una sola palabra muy larga: medía 507 px y se salía de una pantalla de 390 px | El ejemplo se parte en varias líneas (`.pa-upload code`) |
| La propia prueba, en el móvil | Esperaba a ver el primer botón del menú del panel. Desde la 2.4, en el móvil el menú está plegado tras «☰ Menú», así que el botón existe pero no se ve, y la prueba se paraba a los 20 s sin probar nada | Espera a que el menú esté en la página, no a que se vea. Las pantallas se siguen abriendo una a una y comprobando igual |

Las capturas de las pantallas nuevas de esta versión se miraron una a una durante su propio encargo, en el ordenador y
en el móvil:
- asistente de servicios: `docs/capturas/v50.58/asistente/`;
- progreso del curso: `docs/capturas/v50.58/curso/`;
- «Reservas desde tu web e Instagram»: `docs/capturas/v50.58/vender/`;
- foto por tipo de buceo: `docs/capturas/v50.58/fototipo/`.

## Cómo repetirlo

```bash
python3 tests/navegador/e2e_v50_57_modos.py [carpeta-de-capturas]
```
