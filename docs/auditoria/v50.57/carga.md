# WORLDIVES DISCOVERY v50.57 · Prueba de carga (revisión general 5.2 y 5.3)

Objetivo del encargo: **300 usuarios a la vez navegando** (portada, explorar, fichas y mapa) y **20 reservas por
segundo en salidas distintas**, más **reservas simultáneas a la misma salida** para comprobar que no hay sobreventa.
Meta: **el 95 % de las páginas en menos de 500 ms y ningún error**.

## Resumen

⟪RESUMEN⟫

## Cómo se ha medido

- **El programa del servidor de la v50.57**, en este equipo, con una copia de una base de carga (nunca la de datos
  reales): la demo más 500 buceadores con contraseña real (PBKDF2 de 600.000 iteraciones, como en producción), 22
  centros verificados y 2.448 salidas futuras de 40 plazas. Pagos con el simulador local de Stripe (nunca el real) y
  correos por SMTP, como en producción, a un servidor de correo local que los recibe y no los envía a nadie.
- **Arranca en modo desarrollo** (`WOD_ENV=development`), no en modo producción: el modo producción no arranca sin
  dominio con https, y este equipo no lo tiene. Para lo que se mide no cambia nada: el mismo programa, los mismos
  procesos, la misma base con WAL, la misma caché y el mismo envío de correos por SMTP.
- **Como el VPS contratado (Hostinger KVM 2, 2 vCPU)**: el servidor con `WOD_WORKERS=2` y fijado a **2 núcleos**
  (`taskset`); el generador de carga (Locust) en los otros 2, para que no le quite procesador al servidor.
- **⟪USUARIOS⟫ usuarios a la vez** durante ⟪DURACION⟫ de régimen estable (después de la llegada y de un tiempo para
  asentarse):
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
  - Con 500 cuentas, 20 reservas por segundo son una reserva de cada cuenta cada 25 s; en la realidad serían miles de
    personas distintas. Por eso, solo en esta prueba, el límite de 20 reservas por persona y hora se sube (se sigue
    consultando en cada reserva). El límite de 3 pagos sin terminar por persona sigue igual.
  - **Ráfagas a la misma salida**: cada ⟪CADA⟫ s, un centro abre una salida de ⟪PLAZAS⟫ plazas y le llegan **20 reservas
    a la vez** por los cuatro caminos del encargo multicanal: 12 buceadores por la web, 4 reservas manuales del centro y
    4 por la API del centro. Después se cuentan en la base las plazas tomadas.
- Se miden el p50, p95 y p99 de cada grupo (páginas, reservas), los errores, la CPU y la memoria del servidor, el
  tamaño de la base y del WAL, y en el registro del servidor los bloqueos de SQLite («database is locked») y los
  errores 500.

## Resultados

⟪RESULTADOS⟫

## Sobreventa

⟪SOBREVENTA⟫

## 5.3 · ¿Aguanta SQLite?

⟪SQLITE⟫

## Cómo repetirlo

```bash
python3 tests/carga/preparar.py construir --dir <carpeta> --buzos 500 --centros 20 --dias 30 --plazas 40
taskset -c 0,1 python3 tests/carga/preparar.py arrancar --dir <carpeta> --workers 2 --pagos stripe-sim
python3 tests/carga/preparar.py sesiones --dir <carpeta>
taskset -c 2,3 python3 tests/carga/medir.py --dir <carpeta> --pasos 320 --duracion 300 --clases Visitante,Reservas --procesos 2 --salida <resultados>
python3 tests/carga/rafagas.py --dir <carpeta> --esperar 60 --cada 30 --veces 8 --salida <resultados>/rafagas.json   # a la vez que medir.py
python3 tests/carga/preparar.py parar --dir <carpeta>
```
