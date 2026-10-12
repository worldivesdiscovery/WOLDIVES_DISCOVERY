# WORLDIVES DISCOVERY v50.45: dos zips por entrega, nueva marca y arreglo del yen (encargo 2b)

Corresponde a la fila **2b** del índice: «Bloques 1, 2 y arreglo del yen». El resto de monedas (bloque 3) y Buddies
(bloque 4) van en entregas posteriores.

## Entrega: dos zips

| Zip | Tamaño | Archivos | Para qué |
|---|---|---|---|
| `WORLDIVES-v50.45-produccion.zip` | 22,1 MB | 470 | El servidor real. Solo código y la semilla del catálogo |
| `WORLDIVES-v50.45-pruebas.zip` | 43,4 MB | 532 | Probarlo todo en tu ordenador (puerto 8100). **Nunca se sube al servidor real** |

Los dos se crean con `python scripts/build_release.py`. Antes de escribir cada zip, una **comprobación automática** se
para si encuentra alguna de estas cosas:
- cuentas o contraseña de prueba;
- claves reales (Stripe, webhooks, claves privadas, AWS, ArcGIS, Brevo);
- una base de datos que no sea la semilla, o una semilla con personas o actividad;
- un `.env`, o un `.env.example` con valores en las variables secretas;
- `WOD_DEMO_MODE=1` en un archivo de arranque o de despliegue;
- cachés, registros, subidas o archivos retirados.

Las dos comprobaciones de esta entrega han salido correctas.

## Bloque 1 · Zip de producción
- **Solo código.** No lleva base con personas, subidas, cachés, registros ni `.env`.
- **La base se crea en el primer arranque** a partir de `data/seed/catalogo.sqlite3`. La semilla solo tiene países,
  tipos, zonas, certificaciones, los 293 puntos, destinos y textos legales. Comprobado: 0 usuarios, 0 centros y
  0 reservas.
- **Primera cuenta de administración:** `scripts/crear_admin.sh` o `crear_admin.bat`. La contraseña se pide sin mostrarla.
- **`.env.example`:**
  - todas las variables van vacías y comentadas, con el valor recomendado en el comentario;
  - una variable vacía cuenta como «sin poner», así que copiar la plantilla tal cual arranca con los valores por defecto (comprobado).
- **Estructura:** `app/`, `public/`, `data/seed/`, `docs/`, `scripts/`, `tests/` y el README actualizado.
  - **Plan de separación en módulos:** `docs/estructura.md`, una zona por versión.
  - **En esta versión se separa** `app/wod/money.py` (importes y monedas).
- **Pruebas en el zip de producción:** la carpeta `tests/` va incluida, pero necesita el catálogo de demostración, que solo va en el zip de pruebas. Las pruebas se ejecutan desde ese zip o desde el repositorio.

## Bloque 1 · Zip de pruebas
- **Lo que añade al de producción:**
  - el mismo código;
  - la base de demostración (`data/pruebas/worldives.sqlite3`) y `CUENTAS-DE-PRUEBA.md` en la raíz;
  - `scripts/start_pruebas.bat` / `.sh`;
  - las capturas de esta entrega y de la anterior.
- **Al arrancar:**
  - puerto **8100** y banda «Entorno de pruebas» en las 10 lenguas;
  - los correos no salen: se guardan como `.eml` en `data/pruebas/correos/`;
  - Stripe solo en modo test.
- **Cuentas fijas:** administración (admin@example.com), centro (centro@example.com), freelance
  (freelance@example.com), buceador (buzo@example.com) y buceadores 2 a 6 (buzo2@example.com … buzo6@example.com).
  Los nombres de usuario y la contraseña común están en `CUENTAS-DE-PRUEBA.md`, que solo va en el zip de pruebas: así
  nunca aparecen en el zip de producción, y la comprobación automática lo vigila.

- **Datos de demostración, con fechas a partir de hoy** (los crea `scripts/crear_demo.py` a través de la API de la web, como lo haría una persona):
  - **Centro de Buceo Pruebas:**
    - logo;
    - «Doble inmersión en barco» bajo petición y «Bautizo de buceo» con pago al reservar;
    - 22 salidas entre mañana y dentro de 6 semanas;
    - 2 barcos y política de cancelación (48 h, 50 %).
  - **Freelance:**
    - «Cenotes con guía, por días»: día completo y medio día, descuento desde 3 días y extra de fotos;
    - horario de lunes a sábado y 3 días de vacaciones;
    - reservas por días confirmadas y pendientes.
  - **Experiencias:**
    - «Fin de semana en las Medas» y el vida a bordo «Vida a bordo en el Caribe mexicano», publicadas;
    - «Semana de cenotes y cavernas», pendiente de revisión.
  - **Buceador:**
    - reservas en todos los estados: solicitada, confirmada, aceptada pendiente de pago, pagada (pago simulado), cancelada, rechazada, caducada y completada;
    - Log Book con 3 inmersiones, puntos y perfil con contacto de emergencia.
  - **Administración:** una denuncia, una experiencia por revisar y un alta de centro pendiente.
- **Restaurar demo:**
  - con el servidor en marcha: botón **Administración → Operación → «Restaurar demo»**, que solo existe en modo pruebas;
  - con el servidor parado: `scripts/reset_demo.bat` / `.sh`;
  - si los datos tienen más de 7 días, se renuevan solos al arrancar.
- **Protecciones:**
  - El servidor **se niega a arrancar** con `WOD_DEMO_MODE=1` si:
    - la dirección pública es worldives.com, www.worldives.com u otra de `WOD_PRODUCTION_HOSTS`;
    - `WOD_ENV=production`;
    - hay una clave real de Stripe (`sk_live_`).
  - **Las cuentas de prueba nunca están en la base de producción:**
    - la semilla no tiene usuarios;
    - el código del zip de producción no contiene ni las cuentas ni la contraseña de prueba (salvo la propia lista de comprobación de `build_release.py`).
  - En modo pruebas **nunca se envía un correo real**, aunque el `.env` tenga SMTP.

## Bloque 2 · Nueva marca
- **Logo nuevo en todas partes:**
  - cabecera (horizontal), pie e inicio de sesión (versión para fondo oscuro);
  - favicon, icono de iPhone, app instalable (incluido el icono adaptable) y barra del navegador en Abismo;
  - imagen para compartir en redes (og:image 1200 × 630);
  - los correos (icono en la cabecera Abismo y barra Turquesa);
  - los PDF: recibo, ficha del buceador y descargo, con cabecera Abismo, el icono y el texto en Agua clara;
  - la caché de la app (`worldives-v50-45`).
- **Archivos:**
  - en `public/assets/brand/`: las variantes vertical, horizontal, oscuro, símbolo, iconos, favicon, PWA, maskable, correo, PDF y og;
  - en `movil/assets/`: Capacitor, Google Play y App Store;
  - se generan con `tools/brand/build_brand.py` a partir de los originales, sin redibujar.
- **Paleta** (Abismo, Profundo, Océano, Turquesa, Agua clara, Espuma y el degradado Océano → Turquesa):
  - los colores se escriben una sola vez, en variables CSS: 211 cambios en el CSS, 35 en la web y 21 en el servidor;
  - se mantienen aparte los colores que significan otra cosa: tipos de servicio, temas de temporada y carteles.
- **Contraste:**
  - todas las combinaciones de texto superan 4,5:1;
  - Turquesa sobre blanco (2,89:1) solo se usa para decoración;
  - informe completo en `docs/marca.md`.
- **Nombre:**
  - siempre «WORLDIVES DISCOVERY» o «WORLDIVES»;
  - la migración `migrate_v50_45` corrige los textos antiguos del catálogo sin borrar nada;
  - **la búsqueda final da cero resultados** fuera de `archive/` y de las capturas «antes».
- **Logo anterior:** retirado de `public/` y guardado en `archive/marca-anterior/`:
  - `wod-icon.png`, `wod-icon.ico`, `wod-icon-256.png` y `wod-icon-512.png`;
  - `world-dives-discovery-logo.png`.

  Las direcciones antiguas ya no responden (404, comprobado). Las notas antiguas de `data/` se han movido a `archive/notas-antiguas/`.
- **Capturas antes / después** (9 pantallas en ordenador y móvil, correo y PDF): `docs/capturas/marca-v50-45/`.
- **Tipografía:** no ha cambiado.
- **Temas:** la web tiene un solo tema (con imágenes por temporada). No existen temas «Clásico» ni «Futurista»; la paleta se aplica al tema único.

## Arreglo del yen (monedas sin decimales)
- **Antes:** todo se multiplicaba por 100. Una reserva de 10 000 JPY se cobraba como 1 000 000.
- **Ahora:** una sola función (`app/wod/money.py`) convierte a la unidad mínima de cada moneda. La usan:
  - el cobro;
  - la cuota del plan;
  - la comprobación del importe recibido;
  - las devoluciones y las devoluciones parciales.
- **Unidad mínima por moneda:**
  - EUR, MXN y THB: × 100;
  - JPY, KRW, CLP y el resto sin decimales: × 1;
  - KWD, BHD y el resto con 3 decimales: × 1000, terminando en 0.
- **Mínimos de Stripe por moneda:** por ejemplo, 0,50 €, 10 MXN, 10 THB o 50 JPY. Por debajo del mínimo, la reserva online se rechaza con un mensaje claro en los 10 idiomas: «El importe online mínimo en MXN es 10. Pide al centro que cobre esta reserva en el centro.»
- **Probado con el simulador de Stripe:**
  - un cobro de 2 × 5 000 JPY = 10 000;
  - la comprobación lo acepta y la reserva queda confirmada;
  - una devolución de 3 000 JPY se envía como 3 000;
  - 5 MXN se rechaza;
  - también EUR, MXN, THB y KWD en pruebas unitarias.

## Pruebas
- **Batería completa de API:** 196 pruebas, todas correctas. Las nuevas son:
  - `test_v50_45_brand_money` (6): monedas, yen de principio a fin, marca, correo y PDF;
  - `test_v50_45_release` (8): protecciones del modo pruebas, la comprobación de los zips, la plantilla `.env.example` y «Restaurar demo».
- **Navegador:** las 13 suites, todas correctas (agenda 35, inicio de sesión 58, modos de reserva 35, centros 32, salidas 31, capas 68, legal y catálogo 33, manifiesto 27, marcadores, sin conexión 13, pagos 26, puntos y correo 20, recorrido sin errores).
  - Se han adaptado 3 pruebas antiguas: la banda de pruebas tiene texto nuevo; el informe de imágenes incluye ahora la marca; el botón «Satélite» desactivado sin clave ya no se pulsa (este fallo venía de v50.43).
- **Recorrido del zip de pruebas (18 comprobaciones, todas correctas):**
  - banda en español e inglés;
  - entrada con las cuentas fijas;
  - todos los estados en «Mi área → Historial»;
  - botón «Restaurar demo».

  Capturas en `docs/capturas/pruebas-v50-45/`.
- **Zips desempaquetados y arrancados:**
  - producción crea la base desde la semilla, con 0 usuarios;
  - pruebas arranca en el 8100 y entra con la cuenta del buceador;
  - con la dirección real o una clave `sk_live_`, el arranque se para (código 2).

## Estado

| Punto | Estado |
|---|---|
| Dos zips con comprobación automática | Hecho |
| Base creada en el primer arranque y semilla del catálogo | Hecho |
| `.env.example` vacío y comentado | Hecho |
| Separación en módulos | Plan en `docs/estructura.md`; esta versión separa `money.py` |
| Zip de pruebas: cuentas fijas, datos, puerto 8100, correos a carpeta, «Restaurar demo» | Hecho |
| Datos de cursos en la demo | Pendiente: los cursos llegan en una versión posterior (A3) |
| Datos de Buddies en la demo | Pendiente: bloque 4 |
| Logo y paleta en web, paneles, correos, PDF, app, redes, manifest y caché | Hecho |
| SVG del logo | Pendiente: los originales son JPG y un trazado automático no sería fiel. Lo debe vectorizar un diseñador |
| Carteles con QR | Usan la paleta; el logo en imagen dentro del cartel queda pendiente |
| Contraste ≥ 4,5:1 | Hecho, con informe |
| Arreglo del yen y mínimos de Stripe | Hecho |
| Resto de monedas (bloque 3) | Siguiente entrega |

## Lo que no se ha podido comprobar aquí
- **Clientes de correo reales** (Gmail, Outlook, Apple Mail): los correos se han revisado como HTML en Chromium.
- **Stripe real en modo test:** sin claves `sk_test_` aquí, se ha usado el simulador de Stripe de las pruebas.

## Archivos principales cambiados
- **Servidor:**
  - `app/server.py`: marca, PDF, `demo_guard`, «Restaurar demo», arranque desde la semilla, importes con `money`, `migrate_v50_45`;
  - `app/wod/money.py` (nuevo);
  - `app/wod/pdf.py`: imágenes JPEG en el PDF;
  - `app/wod/config.py`: variables vacías.
- **Web:**
  - `public/index.html`, `manifest.webmanifest`, `sw.js`, `assets/css/world-dives-v8.css` y `assets/js/world-dives-v8.js`;
  - `assets/brand/` (nuevo);
  - las 9 traducciones.
- **Scripts:** `build_release.py`, `crear_demo.py`, `reset_demo`, `start_pruebas` y `crear_admin` (nuevos).
- **Herramientas:** `tools/brand/` (nuevo).
- **Documentación:**
  - `docs/marca.md`, `docs/estructura.md`, `docs/pruebas/CUENTAS-DE-PRUEBA.md` y `docs/marca/originales/`;
  - el README.
- **Pruebas:** `tests/test_v50_45_brand_money.py`, `tests/test_v50_45_release.py` y `tests/shots_brand.py`.
