# WORLDIVES DISCOVERY v50.58 · Auditoría con el código final (17/10/2026)

La parte 7 del encargo de revisión y usabilidad de los días 15 y 16/10/2026 pide repetir con el código final la
auditoría de la v50.57 (`docs/auditoria/v50.57/`): cada botón, los cuatro modos, la prueba de carga y la velocidad. Se
ha repetido con las mismas herramientas y sin rebajar ninguna comprobación. Todo lo que estaba mal está corregido en
esta versión.

| Parte | Informe | Resultado en una línea |
|---|---|---|
| Todos los botones (2.2) | [`botones.md`](botones.md), con el detalle en [`botones-inventario.md`](botones-inventario.md). El detalle va solo en el paquete DEMO y en el repositorio, porque nombra las cuentas de la demo | 400 pantallas y 6.188 elementos con seis papeles: 0 «Error», 0 «Sin efecto» y 0 desactivados sin explicación. Un fallo encontrado y corregido: el título del grupo de la sección abierta, en el menú lateral, no se plegaba |
| Los cuatro modos (5.1) | [`modos.md`](modos.md), con capturas del menú lateral en `docs/capturas/v50.58/panel/` | 190/190 en el ordenador y en el móvil. Tres fallos encontrados y corregidos: los botones de las reservas tapaban el canal y el estado, el menú plegado tenía separadores de 42 px, y el ejemplo de «Lotes nuevos» se salía en el móvil |
| Carga y SQLite (5.2 y 5.3) | [`carga.md`](carga.md) | 300 personas y 20 reservas por segundo: páginas p95 17 ms, reservas p95 350 ms (pedido: menos de 500 ms), 0 errores en 74.416 peticiones y ninguna sobreventa. Ninguna diferencia medible con la v50.57: el ruido de este equipo es mayor |
| Velocidad (5.4) | [`lighthouse.md`](lighthouse.md) | Portada en el móvil: 96 (pedido: 85) y su foto en 2,3 s en 4G (pedido: menos de 2,5 s). La ficha de un punto sube 2 puntos y las demás páginas pierden entre 1 y 4, porque el programa principal pesa un 20 % más. Se propone separar el código de los paneles |

Cómo repetir cada parte: al final de cada informe.
