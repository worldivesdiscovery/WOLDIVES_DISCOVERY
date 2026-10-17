# WORLDIVES DISCOVERY v50.58 · Prueba de carga con el código final (revisión y usabilidad, parte 7)

La parte 7 del encargo de los días 15 y 16/10/2026 pide repetir la prueba de la v50.57 con el código final. La prueba
es la misma, con las mismas herramientas (`tests/carga/`) y el mismo objetivo:
- **300 personas navegando a la vez**;
- **20 reservas por segundo en salidas distintas**;
- **reservas simultáneas a la misma salida**, sin sobreventa;
- el 95 % de las páginas en menos de 500 ms y ningún error.

## Resumen

| Lo que pide el encargo | Resultado (pasada oficial del 17/10/2026) | |
|---|---|---|
| 300 personas navegando (portada, explorar, fichas, mapa) | Páginas: p95 **17 ms** (p99 63 ms); pedido: menos de 500 ms | ✓ |
| 20 reservas por segundo en salidas distintas | **20,0 por segundo**, p95 **350 ms** (en otras tres pasadas: 380, 390 y 130 ms) | ✓ |
| Reservas a la vez a la misma salida, sin sobreventa | 8 ráfagas de 20 reservas para 3 plazas: **exactamente 3 aceptadas** cada vez | ✓ |
| Ningún error | **0 errores** en 74.416 peticiones al servidor; ningún bloqueo de la base ni error 500 | ✓ |

## Cómo se ha medido

Igual que en la v50.57 (`docs/auditoria/v50.57/carga.md`, «Cómo se ha medido»):
- con una copia de una base de carga, nunca la de datos reales: la demo más 500 buceadores con contraseña real, 22
  centros y 2.430 salidas futuras de 40 plazas;
- pagos con el simulador local de Stripe y correos por SMTP a un servidor local que no los envía a nadie;
- como el VPS contratado: el servidor con 2 procesos y fijado a 2 núcleos, y el generador de carga en los otros 2;
- 320 usuarios a la vez durante 280 s estables:
  - 300 visitantes navegando como personas;
  - 20 reservando una vez por segundo, cada vez en una salida distinta y con un buceador distinto;
  - cada 30 s, una ráfaga de 20 reservas a la vez a una salida de 3 plazas: 12 por la web, 4 manuales del centro y
    4 por la API.

## Resultados de la pasada oficial

| Grupo | Peticiones por segundo | p50 | p95 | p99 | Errores |
|---|---|---|---|---|---|
| **Páginas** (todo lo que pide la web al navegar) | 240 | 2 ms | **17 ms** | 63 ms | 0 de 67.093 |
| · de ellas, el contador de visitas (`/api/visita`, una escritura) | 51 | 3 ms | 58 ms | 190 ms | 0 de 15.231 |
| **Reservas** (`POST /api/bookings`, salidas distintas) | 20,0 | 83 ms | **350 ms** | 470 ms | 0 de 6.020 |
| Confirmar el pago al volver de Stripe | 6,1 | 17 ms | 100 ms | 210 ms | 0 de 1.850 |
| **Todo** | 266 | 3 ms | 72 ms | 250 ms | **0 de 74.416** |

- **Servidor** (2 núcleos): 88 % de CPU de media (máximo 124 %; el máximo posible es 200 %), 675 MB de memoria entre
  los dos procesos, WAL de 6,6 MB como mucho.
- **Registro del servidor**: 0 bloqueos de SQLite («database is locked») y 0 errores 500.

## ¿Va más lenta que la v50.57? No se ha podido medir ninguna diferencia

Las reservas de la pasada oficial (p50 83 ms, p95 350 ms) tardaron más que en la pasada oficial de la v50.57 (p50
19 ms, p95 110 ms). Antes de dar nada por bueno se buscó la causa:

1. **Una a una**, sin más tráfico (300 reservas seguidas), las dos versiones tardan lo mismo: **8 ms de mediana**
   (13,6 ms y 13,8 ms de p95). El trabajo de cada reserva no ha crecido.
2. Con el perfilador (py-spy), el tiempo de más se va en **esperar el turno para escribir** en la base (el comienzo de
   la transacción y la hora de la sesión), no en el código de la reserva.
3. **Las dos versiones, alternadas en este mismo equipo, el mismo día y con la misma carga** (pasadas de 5 minutos;
   mediana / p95 de las reservas):

   | Pasada | v50.57 (código de su pasada oficial) | v50.58 (código final) |
   |---|---|---|
   | 1 | 22 / 130 ms | 83 / 350 ms (la oficial) |
   | 2 | 39 / 260 ms | 70 / 380 ms |
   | 3 | 120 / 400 ms | 70 / 390 ms |
   | 4 | — | 20 / 130 ms |

   **El mismo código da entre 20 y 120 ms de mediana según la pasada.** Ese ruido de este equipo compartido es mayor
   que cualquier diferencia entre las versiones. Una búsqueda commit a commit con pasadas de 2 minutos dio el mismo
   ruido: dos commits con el mismo servidor (uno solo cambiaba la web) dieron 35 ms y 82 ms.
4. En **todas** las pasadas, de las dos versiones, el p95 de las reservas queda por debajo de los 500 ms del encargo y
   sin un solo error.

En el VPS conviene repetir la prueba (abajo): allí no compite con otras máquinas y las cifras serán las de verdad.

## Sobreventa

**Ninguna.** En las 8 ráfagas de 20 reservas a la vez a una salida de 3 plazas se aceptaron exactamente 3. Las otras 17
recibieron «Sin plazas: ya no quedan plazas libres para esa fecha».

| Ráfaga | Aceptadas (web · manual · API) | «Sin plazas» | Plazas tomadas | Libres después | Sobreventa |
|---|---|---|---|---|---|
| 1 | 3 (3 · 0 · 0) | 17 | 3 de 3 | 0 | no |
| 2 | 3 (2 · 1 · 0) | 17 | 3 de 3 | 0 | no |
| 3 | 3 (1 · 1 · 1) | 17 | 3 de 3 | 0 | no |
| 4 | 3 (3 · 0 · 0) | 17 | 3 de 3 | 0 | no |
| 5 | 3 (1 · 0 · 2) | 17 | 3 de 3 | 0 | no |
| 6 | 3 (2 · 0 · 1) | 17 | 3 de 3 | 0 | no |
| 7 | 3 (2 · 0 · 1) | 17 | 3 de 3 | 0 | no |
| 8 | 3 (1 · 2 · 0) | 17 | 3 de 3 | 0 | no |

Al terminar, la comprobación de la base da 7.686 reservas, todo en orden:
- ninguna salida con plazas libres negativas;
- ninguna con más plazas tomadas que las que tiene;
- ninguna reserva repetida;
- en todas las salidas futuras, el contador de plazas cuadra con lo tomado.

## Lo que cambió en la prueba

- **La comprobación final cuenta también los bloqueos de plaza.** La primera vez marcó una salida con el contador
  «descuadrado». Era la doble inmersión del sábado de la demo, que tiene 2 plazas apartadas para la Inmersión 4 del
  curso (3.5). El contador estaba bien; la comprobación solo sumaba reservas. Ahora suma reservas y bloqueos activos,
  como el propio contador (`tests/carga/preparar.py`, `comprobar`).

## Cómo repetirlo

Igual que en la v50.57, sobre una copia de una base de carga y nunca sobre la base real:

```bash
python3 tests/carga/preparar.py construir --dir <carpeta> --buzos 500 --centros 20 --dias 30 --plazas 40
taskset -c 0,1 python3 tests/carga/preparar.py arrancar --dir <carpeta> --workers 2
python3 tests/carga/preparar.py sesiones --dir <carpeta>
taskset -c 2,3 python3 tests/carga/medir.py --dir <carpeta> --pasos 320 --duracion 300 --clases Visitante,Reservas --procesos 2 --salida <resultados>
python3 tests/carga/rafagas.py --dir <carpeta> --esperar 60 --cada 30 --veces 8 --salida <resultados>/rafagas.json   # a la vez que medir.py
python3 tests/carga/preparar.py comprobar --dir <carpeta>
python3 tests/carga/preparar.py parar --dir <carpeta>
```

Como las cifras cambian de una pasada a otra, conviene hacer al menos tres pasadas y dar todas.
