# WORLDIVES DISCOVERY v50.57 · Prueba de carga (revisión general 5.2 y 5.3)

Objetivo del encargo: **300 usuarios a la vez navegando** (portada, explorar, fichas y mapa) y **20 reservas por
segundo en salidas distintas**, más **reservas simultáneas a la misma salida** para comprobar que no hay sobreventa.
Meta: **el 95 % de las páginas en menos de 500 ms y ningún error**.

## Resumen

| Lo que pedía el encargo | Resultado | |
|---|---|---|
| 300 personas navegando a la vez (portada, explorar, fichas, mapa) | Páginas: p95 **16 ms** (p99 41 ms); pedido: menos de 500 ms | ✓ |
| 20 reservas por segundo en salidas distintas | **20,0 por segundo**, p95 **110 ms** | ✓ |
| Reservas a la vez a la misma salida, sin sobreventa | 8 ráfagas de 20 reservas para 3 plazas: **exactamente 3 aceptadas** cada vez | ✓ |
| Ningún error | **0 errores** en 74.913 peticiones; ningún bloqueo de la base ni error 500 | ✓ |

- **Encontrado y corregido:** la cola de correos escrita en archivos (desarrollo y paquete DEMO) dejaba la base
  bloqueada hasta 2 s seguidos. En producción, con servidor de correo, no pasaba; la prueba oficial manda los correos
  como en producción.
- **5.3 · SQLite aguanta** con lo que ya estaba (WAL, índices y caché de las consultas públicas). Margen medido: sin un solo error hasta 60
  reservas por segundo (el triple de lo pedido); a 100 pedidas, la base ya no da abasto. PostgreSQL no hace falta.

## Cómo se ha medido

- **El programa del servidor de la v50.57**, en este equipo, con una copia de una base de carga (nunca la de datos
  reales): la demo más 500 buceadores con contraseña real (PBKDF2 de 600.000 iteraciones, como en producción), 22
  centros verificados y 2.448 salidas futuras de 40 plazas. Pagos con el simulador local de Stripe (nunca el real) y
  correos por SMTP, como en producción, a un servidor de correo local que los recibe y no los envía a nadie.
- **Arranca en modo desarrollo** (`WOD_ENV=development`), no en modo producción: el modo producción no arranca sin
  dominio con https, y este equipo no lo tiene. Para lo que se mide no cambia nada: el mismo programa, los mismos
  procesos, la misma base con WAL, la misma caché y el mismo envío de correos por SMTP.
- **Como el VPS contratado (Hostinger KVM 2, 2 vCPU)**: el servidor con `WOD_WORKERS=2` y fijado a **2 núcleos**
  (`taskset`); el generador de carga (Locust) en los otros 2, para que no le quite procesador al servidor. Equipo:
  Intel Xeon a 2,10 GHz, 4 núcleos y 15 GB de memoria. Con otro procesador las cifras cambian: en el VPS hay que
  repetirla (abajo, «Cómo repetirlo»).
- **320 usuarios a la vez** durante 280 s de régimen estable (después de 20 s de llegada y 10 s para asentarse):
  - **300 visitantes navegando** como personas: portada (con su mapa de puntos), explorar y listas de puntos, fichas
    de puntos y de centros, calendarios de salidas, buscador y salidas cercanas. Cada uno espera de 3 a 10 s entre
    una pantalla y otra (un uso intenso: una persona real suele tardar más) y tiene su propia IP, como detrás del
    proxy. Cada visita nueva baja la web entera, como el navegador: la página, los estilos, el programa principal, las
    librerías del mapa, las imágenes y, si lee en otro idioma (la mitad de los visitantes), su paquete de idioma. Las
    visitas siguientes la revalidan. Y en cada pantalla avisa al contador de visitas (`/api/visita`, nuevo en la 4.2:
    una escritura en la base por pantalla), con un navegador de verdad: el servidor no cuenta a los robots.
  - **20 usuarios reservando, cada uno una reserva por segundo**: 20 reservas por segundo, cada vez en una salida
    distinta y con la sesión de un buceador distinto (las sesiones se abren antes: 20 inicios de sesión por segundo,
    con su cálculo de contraseña deliberadamente lento, serían otra prueba). Si el servicio es de «pago al reservar»
    (uno de cada tres), la persona paga al momento en el simulador de Stripe y la página de vuelta confirma el pago,
    como en la web.
  - Con 440 cuentas (las otras 60 son de las ráfagas), 20 reservas por segundo son una reserva de cada cuenta cada
    22 s; en la realidad serían miles de personas distintas. Por eso, solo en esta prueba, el límite de 20 reservas por persona y hora se sube (se sigue
    consultando en cada reserva). El límite de 3 pagos sin terminar por persona sigue igual.
  - **Ráfagas a la misma salida**: cada 30 s, un centro abre una salida de 3 plazas de «pago al reservar» y le llegan
    **20 reservas a la vez**: 12 buceadores por la web (cada reserva ocupa su plaza mientras la persona paga), 4 reservas
    manuales del centro y 4 por la API del centro. Las 20 compiten por las mismas 3 plazas (el widget en la web del
    centro reserva con la misma función). Después se cuentan en la base las plazas tomadas y las reservas aceptadas.
- Se miden el p50, p95 y p99 de cada grupo (páginas, reservas), los errores, la CPU y la memoria del servidor, el
  tamaño de la base y del WAL, y en el registro del servidor los bloqueos de SQLite («database is locked») y los
  errores 500.

## Resultados

Pasada oficial del 16/10/2026 (5 minutos y 20 s; las cifras, del régimen estable):

| Grupo | Peticiones por segundo | p50 | p95 | p99 | Errores |
|---|---|---|---|---|---|
| **Páginas** (todo lo que pide la web al navegar: página, estilos, programa, datos, contador de visitas) | 241 | 2 ms | **16 ms** | 41 ms | 0 de 67.514 |
| · de ellas, el contador de visitas (`/api/visita`, una escritura) | 51 | 3 ms | 33 ms | 85 ms | 0 de 14.240 |
| **Reservas** (`POST /api/bookings`, salidas distintas) | 20,0 | 19 ms | **110 ms** | 190 ms | 0 de 5.600 |
| Confirmar el pago al volver de Stripe | 6,4 | 15 ms | 53 ms | 96 ms | 0 de 1.799 |
| **Todo** | 268 | 3 ms | 28 ms | 85 ms | **0 de 74.913** |

- **Servidor** (2 núcleos): 87 % de CPU de media (máximo 125 %; el máximo posible es 200 %), 618 MB de memoria entre los dos procesos, WAL de 6,4 MB como mucho.
- **Registro del servidor**: 0 bloqueos de SQLite («database is locked») y 0 errores 500.
- Régimen estable de 280 s; la llegada (20 s) y el asentamiento (10 s) no cuentan en las cifras.

## Sobreventa

**Ninguna.** En las 8 ráfagas, de 20 reservas a la vez a una salida de 3 plazas, se aceptaron exactamente 3 y las
otras 17 recibieron «Sin plazas: ya no quedan plazas libres para esa fecha». Unas veces las ganaron los buceadores de
la web y otras el centro (a mano o por la API): da igual el camino, nunca más de las que hay.

| Ráfaga | Aceptadas (web · manual · API) | «Sin plazas» | Plazas tomadas | Libres después | Sobreventa |
|---|---|---|---|---|---|
| 1 | 3 (2 · 0 · 1) | 17 | 3 de 3 | 0 | no |
| 2 | 3 (0 · 3 · 0) | 17 | 3 de 3 | 0 | no |
| 3 | 3 (1 · 1 · 1) | 17 | 3 de 3 | 0 | no |
| 4 | 3 (2 · 0 · 1) | 17 | 3 de 3 | 0 | no |
| 5 | 3 (2 · 1 · 0) | 17 | 3 de 3 | 0 | no |
| 6 | 3 (2 · 0 · 1) | 17 | 3 de 3 | 0 | no |
| 7 | 3 (2 · 0 · 1) | 17 | 3 de 3 | 0 | no |
| 8 | 3 (0 · 2 · 1) | 17 | 3 de 3 | 0 | no |

Y después de la pasada más dura (100 reservas por segundo pedidas, con la base ya saturada, abajo): 11.339 reservas,
ninguna salida con plazas libres negativas ni con más plazas tomadas que las que tiene, en todas las salidas futuras
el contador de plazas cuadra con las reservas y ninguna reserva repetida.

## Lo que encontró la prueba y está corregido

**La cola de correos escrita en archivos bloqueaba la base hasta 2 s seguidos.** Para encontrar por qué las reservas
tardaban, se midió cada transacción de escritura del servidor (cuánto espera para escribir y cuánto tiempo tiene la
base para él solo). La cola de correos sin servidor de correo (la que usan el modo desarrollo y el paquete DEMO) cogía
la base al marcar el primer correo y no la soltaba hasta escribir los 150 de la tanda, con su QR: hasta 2 s cada vez
(p95 1,57 s), un 31 % del tiempo. Mientras, ninguna reserva, pago ni visita podía guardarse: con esa cola, las
páginas daban p95 750 ms y las reservas p95 2,7 s (pasada de 2 minutos con la misma carga). Estas pasadas de
diagnóstico, con y sin el arreglo, se hicieron en el equipo en el que empezó la prueba, antes de que el entorno se
reiniciara en otro más rápido: compáralas entre sí, no con la pasada oficial.

- **Arreglo** (`app/server.py`, `spool_outbox_to_files`): primero se escriben los correos y después se marcan todos
  en una sola escritura corta (p95 61 ms). Prueba: `tests/test_v50_57_carga.py`, que falla con el código anterior.
- **En producción no pasaba:** con servidor de correo (SMTP), cada correo se marca en dos escrituras cortas y se envía
  sin tener la base; sin servidor de correo, los correos esperan en la cola. Por eso la prueba oficial manda los
  correos por SMTP, como en producción.
- **En el paquete DEMO**, con esta carga extrema (que no es para lo que sirve: probar la web en tu ordenador), las
  reservas siguen siendo lentas aunque ya no se bloquee la base: preparar 150 correos seguidos con su QR ocupa el
  procesador del mismo proceso (p95 de las reservas 2,1 s con correos en archivos).

**La prueba en sí, antes de esta pasada, medía menos de lo que pasa de verdad.** Se ha corregido en `tests/carga/`
antes de medir (la web no tenía culpa):

- las visitas nuevas ya no bajaban el programa principal ni las librerías del mapa (desde la v50.57 los pide el aviso
  de arranque) y no avisaban al contador de visitas de la 4.2;
- los dos procesos que generan la carga repetían la misma reserva a la vez: el servidor tomaba la segunda por un doble
  clic y solo había unas 10 reservas distintas por segundo, no 20;
- las reservas de «pago al reservar» se dejaban sin pagar y la regla de 3 pagos sin terminar por persona las
  rechazaba; ahora se pagan al momento, como hace una persona;
- las búsquedas con espacios o acentos («blue hole», «África y Mar Rojo») no se codificaban como en el navegador y no
  llegaban al servidor.

## 5.3 · ¿Aguanta SQLite?

**Estado: Ya estaba.** SQLite aguanta la carga del encargo sin cambiar nada de lo que pedía el punto 5.3, porque ya
estaba hecho:

- **Modo WAL**: las lecturas no esperan a las escrituras; escrituras con `synchronous=NORMAL` y hasta 10 s de espera
  si otra está escribiendo.
- **Índices**: 165 en la base (135 tablas), incluidos los de las búsquedas de esta prueba.
- **Caché de las consultas públicas**: el mapa de puntos, el directorio, los tipos de buceo, las fotos de la web, las
  promociones, los viajes y el catálogo de servicios se calculan una vez y se renuevan en segundo plano; las
  conexiones a la base se reutilizan (v50.51).

Lo que sí encontró la prueba está corregido: la cola de correos que bloqueaba la base (arriba) y, muy por encima
de lo pedido, el mensaje de las reservas que la base no puede guardar a tiempo (abajo).

**Dónde está el límite.** Las mismas 300 personas navegando y cada vez más reservas por segundo, en el mismo equipo
y con el servidor en 2 núcleos (pasadas de 2 minutos; la de 20, la oficial de 5):

| Reservas por segundo | Hechas | Páginas p95 | Reservas p95 | Errores |
|---|---|---|---|---|
| 20 (el encargo) | 20,0 | 16 ms | 110 ms | 0 |
| 30 | 30,0 | 21 ms | 170 ms¹ | 0 |
| 40 | 40,0 | 28 ms | 180 ms | 0 |
| 50 | 49,8 | 39 ms | 250 ms | 0 |
| 60 | 59,3 | 58 ms | 440 ms | 0 |
| 80 | 67,8 | 190 ms | 1,9 s | 0 |
| 100 | 74,4 | 430 ms | 2,9 s | 4 reservas rechazadas por la base bloqueada (3 en los primeros 11 s) |

¹ Repetida: la primera pasada, nada más arrancar el equipo, dio 450 ms.

- **Hasta unas 60 reservas por segundo** todo va bien; a partir de ahí el servidor ya no llega a todas (80 pedidas,
  68 hechas) y las esperas crecen. El procesador no es el límite (el servidor no pasó del 140 % de sus 200 %): lo es
  que SQLite escribe de una en una.
- **En el equipo en el que empezó la prueba**, más lento (necesitaba un 50 % más de procesador para lo mismo), el
  límite llegó antes: 30 reservas por segundo sin errores (reservas p95 400 ms); 40 pedidas, 37 hechas, reservas p95
  1,3 s y una rechazada. Allí, con 20 reservas por segundo, la base estaba escribiendo el 57 % del tiempo (medido
  transacción a transacción): sobre todo las reservas, que guardan la reserva y sus correos en la misma escritura.
- **Las reservas rechazadas** fallaron al empezar a escribir, después de esperar 10 s su turno: no guardaron nada. La
  persona veía «Error interno». **Corregido:** ahora ve «Ahora mismo hay demasiadas operaciones a la vez y no se ha
  podido guardar. Vuelve a intentarlo en unos segundos.» (respuesta 503, en los 9 idiomas) y, al repetirla, la
  reserva se hace. Sigue apuntándose en el registro del servidor, porque avisa de que la base no da abasto. Prueba:
  `tests/test_v50_57_carga.py` (con el código anterior, «Error interno»).

**¿Hace falta PostgreSQL? No** para lo que pide el encargo ni para el lanzamiento: 20 reservas por segundo son 72.000
por hora. Conviene prepararlo si en hora punta se pasa de forma sostenida de unas 30 reservas por segundo (el límite
del equipo más lento en el que se ha medido; el del VPS hay que medirlo allí), si aparecen
errores «database is locked» en el registro del servidor, o en los otros casos de la guía (más de un servidor, base de
más de 10 GB, informes pesados a la vez que el tráfico). Cómo hacerlo y esos casos: `docs/despliegue/README.md`,
apartado 9, al día con estas cifras.

## Cómo repetirlo

Sobre una copia de una base de carga, nunca sobre la base real (`tests/carga/`, en el repositorio y en el paquete DEMO):

```bash
python3 tests/carga/preparar.py construir --dir <carpeta> --buzos 500 --centros 20 --dias 30 --plazas 40
taskset -c 0,1 python3 tests/carga/preparar.py arrancar --dir <carpeta> --workers 2   # simulador de Stripe y correo por SMTP local
python3 tests/carga/preparar.py sesiones --dir <carpeta>
taskset -c 2,3 python3 tests/carga/medir.py --dir <carpeta> --pasos 320 --duracion 300 --clases Visitante,Reservas --procesos 2 --salida <resultados>
python3 tests/carga/rafagas.py --dir <carpeta> --esperar 60 --cada 30 --veces 8 --salida <resultados>/rafagas.json   # a la vez que medir.py
python3 tests/carga/preparar.py comprobar --dir <carpeta>   # al terminar: plazas y reservas repetidas en la base
python3 tests/carga/preparar.py parar --dir <carpeta>

# el margen, N reservas por segundo (antes de cada una, base limpia: arrancar y sesiones)
WOD_CARGA_RESERVAS_USUARIOS=N taskset -c 2,3 python3 tests/carga/medir.py --dir <carpeta> --pasos $((300 + N)) --duracion 120 \
    --clases Visitante,Reservas --procesos 2 --seguir --salida <resultados>
```
