# WORLDIVES DISCOVERY — Encargo: auditoría de experiencia y las 4 promesas

Pega este documento entero en la sesión de código.

## Objetivo
WORLDIVES compite con webs y apps que ya usan centros y buceadores. Para ganar, hace cuatro promesas que se tienen que poder **medir con un cronómetro**, no opinar:

| # | Promesa | Quién | Desde dónde empieza a contar | Dónde termina |
|---|---|---|---|---|
| 1 | **Reservar en 30 s o menos** | Buceador con cuenta | Abre la ficha de un servicio o salida | Ve «Solicitud enviada» o la pantalla de pago de Stripe |
| 2 | **Encontrar en 10 s o menos** | Visitante sin cuenta | Abre la portada | Ve la ficha del punto, centro o experiencia que buscaba |
| 3 | **El centro ve su día en 5 s o menos** | Centro con sesión iniciada | Abre la app o la web | Ve el planning de hoy con salidas, cursos, personas y barcos |
| 4 | **Publicar la primera salida en 10 min o menos** | Centro recién aprobado | Entra por primera vez al panel | Su primera salida se ve en público y se puede reservar |

## Reglas
- Versión base: la última disponible. Las partes A y B **no cambian el código**. Las partes C y D sí, y se entregan como versiones nuevas con notas en el estilo habitual.
- Antes de cada punto, comprobar si ya está hecho: «Ya estaba», «Completado», «Nuevo» o «Pendiente de decisión».
- Siempre sobre una **copia de la base**, nunca con datos reales.
- Se respetan las decisiones vigentes: intermediario sin comisión, cobro directo por Stripe, dos modos de reserva, puntos en lugar de monedero, sin mensajería ni red social, 10 idiomas, sin paquetes de varios organizadores, web y modo app con la misma base.

## Parte A — Medir (sin cambiar código)
1. **Scripts de recorrido** con Playwright en `tests/promesas/`, uno por promesa (`promesa1_reservar.py`, `promesa2_encontrar.py`, `promesa3_dia.py`, `promesa4_publicar.py`). Cada uno:
   - repite el recorrido de una persona real: clics, textos escritos y esperas visibles, sin atajos por la API;
   - mide el tiempo de reloj y lo separa en **tiempo de la persona** (leer, decidir, escribir, con tiempos fijos y documentados por acción) y **tiempo de la máquina** (carga, servidor, animaciones);
   - cuenta los **pasos**: pantallas, toques y campos que hay que rellenar;
   - funciona en **ordenador** y en **móvil de gama media** (CPU ×4 y red «4G lenta» de Chrome) y en **modo app** (la web instalada);
   - prueba **español e inglés**;
   - guarda capturas de cada paso y un vídeo del recorrido.
2. **Datos de prueba realistas** en la copia: 500 centros, 50 freelance, 3.000 puntos, 2.000 experiencias y un mes de salidas y reservas, creados por un script (`tools/datos_prueba.py`).
3. **Medidas técnicas** de las pantallas de los recorridos:
   - tiempo de respuesta del servidor;
   - peso de la página;
   - LCP, INP y CLS (Web Vitals);
   - número de peticiones.
4. **Accesibilidad básica** de esas pantallas: teclado, foco visible, contraste y etiquetas (axe-core).
5. **Entrega:** `docs/promesas/medicion-inicial.md` con una tabla por promesa (tiempo, pasos, cumple o no y dónde se pierde el tiempo), las capturas y los vídeos. Los scripts se dejan preparados para repetirse después de cada versión.

## Parte B — Comparar con la competencia (sin cambiar código)
1. **Elegir 6 a 8 competidores** y justificar la elección:
   - **reservas de buceo** (por ejemplo PADI Travel/Adventures, Scubaspots, Divezone);
   - **software de reservas para centros y actividades** (por ejemplo FareHarbor, Bókun, Checkfront, Peek, DiveShop360 o Evolution);
   - **un marketplace generalista de actividades** (por ejemplo GetYourGuide o Civitatis).
2. **Hacer en cada uno los mismos 4 recorridos** (o el más parecido), en su web pública o en la versión de prueba. Nunca reservar ni pagar de verdad y nunca crear cuentas falsas de centros: si un paso requiere eso, se describe con su documentación pública.
3. **Tabla comparativa:**
   - tiempo y pasos de cada recorrido;
   - qué pide al cliente;
   - comisión o precio para el centro (de su web pública, con la fecha);
   - idiomas;
   - app;
   - funciona sin conexión;
   - reserva por días o cursos;
   - avisos.
4. **Lo que hacen mejor que WORLDIVES** (como mínimo 10 puntos concretos, con su captura) y **lo que WORLDIVES ya hace mejor**.
5. **Entrega:** `docs/promesas/competencia.md`, con las fuentes y la fecha de cada dato. Nada de copiar textos, diseños ni marcas de otros.

## Parte C — Plan de mejora
1. Con los resultados de A y B, una **lista priorizada de mejoras** para cumplir las 4 promesas. Cada mejora indica:
   - qué promesa mejora y cuántos segundos o pasos ahorra (estimado);
   - el esfuerzo (pequeño, mediano o grande);
   - el riesgo;
   - si toca algo legal o de pagos.
2. **Mejoras típicas a valorar:**
   - **Promesa 1:**
     - datos del buceador ya rellenados;
     - menos campos;
     - Apple Pay y Google Pay en Stripe;
     - repetir una reserva anterior;
     - botón «Reservar» visible sin desplazar la pantalla.
   - **Promesa 2:**
     - buscador único con sugerencias al escribir;
     - búsqueda por cercanía;
     - resultados que cargan antes que el mapa.
   - **Promesa 3:**
     - «Hoy» como pantalla de inicio del centro;
     - datos del día guardados en el dispositivo;
     - carga sin esperar al resto del panel.
   - **Promesa 4:**
     - asistente de primera salida en 3 pasos con plantillas;
     - puntos de buceo sugeridos por cercanía;
     - publicar sin Stripe en modo «Bajo petición» y conectar Stripe después.
3. **Entrega:** `docs/promesas/plan-de-mejora.md`, con un calendario por versiones. Lo aprueba el titular antes de programar.

## Parte D — Programar y medir antes y después
1. **Programar las mejoras aprobadas,** en el orden del plan y una versión por tanda.
2. **Después de cada versión, repetir los 4 scripts** con los mismos datos y dispositivos. Ninguna versión puede empeorar una promesa: si una la empeora, se corrige antes de entregarla.
3. **Entrega:**
   - `docs/promesas/resultados.md` con una tabla de antes y después por promesa y por dispositivo, con capturas y vídeos;
   - notas de versión;
   - tabla de estado;
   - lista de lo pendiente de decisión.

## Pruebas
- **Scripts repetibles:** los 4 se lanzan con un solo comando (`python tests/promesas/todas.py`) y dejan un informe.
- **Comprobación automática en cada versión:** fallan si una promesa supera su límite en ordenador o en móvil de gama media.
