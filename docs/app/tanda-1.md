# App móvil en 3 módulos · Tanda 1 (v50.48)

Encargo «App móvil en 3 módulos (Buceador, Centro PRO y Freelance PRO) y APK de pruebas».

La Tanda 1 entrega:
- la estructura de la app;
- el módulo **Buceador completo**;
- la **primera APK de pruebas**.

**Se para aquí hasta que el titular pruebe la APK en su móvil.**

## Qué se entrega

| Entregable | Dónde |
|---|---|
| APK de pruebas **WORLDIVES Pruebas** (`com.worldives.app.pruebas`) | GitHub Actions, flujo «App Android (Capacitor)», artefacto **WORLDIVES-Pruebas-apk** (enlace en el mensaje de entrega) |
| Cómo instalarla y probarla en el móvil | `README-PRUEBAS.md`, apartado 8 (dentro del zip de pruebas) |
| Capturas del emulador Android (la APK de verdad, pantalla a pantalla) | Artefacto **WORLDIVES-Pruebas-emulador** del mismo flujo |
| Capturas de las pantallas de la app (390 × 844 y 360 × 800, Clásico y Noche, Normal y Enorme, es/en/fr) | `WORLDIVES-v50.48-capturas.zip` |
| La web y el servidor con lo que la app necesita | `WORLDIVES-v50.48-produccion.zip` y `WORLDIVES-v50.48-pruebas.zip` |
| Estas notas y la tabla de estado | este archivo y `docs/notas-de-version/v50.48.md` |

## Cómo es la app por dentro

La app es la web de WORLDIVES dentro de una app nativa (**Capacitor 8**, opción A, decidida por el titular).
- **WORLDIVES** (`com.worldives.app`) abre https://worldives.com.
- **WORLDIVES Pruebas** (`com.worldives.app.pruebas`) abre primero una pantalla para elegir el servidor de pruebas.
  Las dos se pueden tener instaladas a la vez.

Dentro de la app, la web se pone en **modo app**:
- sin la cabecera ni el pie de la web;
- pestañas abajo;
- pantallas propias para el buceador;
- las páginas de la web que ya existían (ficha del centro, detalle de la reserva, Log Book, Mi cuenta, panel del
  centro…) se abren dentro de la app, con su aspecto de siempre.

La web normal **no cambia**: los dos archivos del modo app (`public/js/wd-app.js` y `public/css/wd-app.css`) solo se
descargan dentro de la app (o con `?app=1` en un navegador, para enseñarla).

**Ventaja:** cada mejora de la web llega a la app sin publicar otra versión en las tiendas. Solo hace falta una
versión nueva cuando cambia la parte nativa: plugins, iconos, permisos.

## Decisiones del titular aplicadas

1. **Capacitor** (opción A).
2. **Tres idiomas en la app: español, inglés y francés.**
   - Un móvil en otro idioma ve la app en inglés.
   - La web sigue en sus 9 idiomas.
   - Los textos nuevos de la app están en `scripts/idiomas/datos/app.json`. Una comprobación automática exige que
     estén en inglés y en francés.
3. **Nombres:** `com.worldives.app` («WORLDIVES») y `com.worldives.app.pruebas` («WORLDIVES Pruebas»). Una sola app
   «WORLDIVES» para todos en las tiendas (decisión 9 de la Tanda 0).

**Recomendaciones de la Tanda 0 aplicadas mientras no digas otra cosa:**
- El tema oscuro se llama **«Noche»** (decisión 7).
- «Contar a bordo» va en la Tanda 2 (decisión 6).
- Tap to Pay, para una versión futura (decisión 8).
- Los roles del personal y el borrado de cuenta de centros y freelance se deciden en la Tanda 2 (decisiones 4 y 5).
  Hasta entonces, en la app, «Borrar mi cuenta» de un centro o freelance explica que hoy se hace escribiendo a
  WORLDIVES («Pendiente de decisión»).

## Tabla de estado

Leyenda:
- **Ya estaba:** existía y se usa tal cual.
- **Completado:** existía en parte y se ha terminado.
- **Nuevo:** no existía.
- **Pendiente:** no existe en el servidor y no se inventa.
- **Tanda N:** va en esa tanda.

### Estructura (apartado 3)

| Punto | Estado | Nota |
|---|---|---|
| Módulos Visitante y Buceador con sus pestañas | **Nuevo** | Visitante: Inicio · Explorar · Entrar. Buceador: Inicio · Explorar · Reservas · Buddies · Mi área |
| Centro PRO y Freelance PRO | **Tanda 2 y Tanda 3** | Mientras tanto, su panel de la web se abre dentro de la app (pestaña «Mi panel») con un aviso. Administración: «La administración se queda en la web» |
| Selector de perfil | **Completado** (lo que permite el servidor) | Hoy una cuenta tiene un solo perfil: Mi área lo enseña («Perfil: Buceador»). El cambio de perfil es «Cerrar sesión» y entrar con otra cuenta; en Pruebas, «Cambiar de servidor o de cuenta de prueba» |
| Contadores en las pestañas | **Nuevo** | Reservas: las que están pendientes de pago |
| Botón atrás de Android | **Nuevo** | Cierra la hoja abierta; luego vuelve atrás; en Inicio deja la app en segundo plano |
| Temas Clásico (por defecto), Noche y Automático | **Nuevo** | En las pantallas de la app. Las páginas de la web que se abren dentro siguen en claro (limitación 1) |
| Texto Normal, Grande y Enorme | **Nuevo** | Igual que el tema |
| Estados con color, icono y texto | **Nuevo** | Confirmada ✓ verde, pendiente de pago con reloj naranja, solicitud con sobre azul, cancelada gris tachada |

### Módulo Buceador (apartado 4)

| Punto | Estado | Nota |
|---|---|---|
| Inicio: buscador grande y chips Cerca de mí · Hoy · Mañana · Este finde · Próximos 14 días | **Nuevo** | La ubicación se pide **solo** al tocar «Cerca de mí» |
| Inicio: próxima inmersión con anillo (días), Cómo llegar, Ver reserva y QR, WhatsApp al centro | **Nuevo** | Con los datos de Mi área (`/api/me/area`) |
| Inicio: «Salidas con plazas cerca de ti» | **Nuevo** | Servidor nuevo: `/api/salidas-cercanas`. Solo centros públicos y freelance; la más cercana primero cuando hay ubicación |
| Inicio: «Repetir» | **Nuevo** | Los centros donde ya reservó, con «Reservar de nuevo» |
| Inicio: tipos de buceo | **Nuevo** | Llevan al mapa filtrado |
| Explorar: mapa a pantalla completa, hoja de tres alturas, «Ver lista / Ver mapa» | **Nuevo** | Nada depende solo de deslizar: el asa y el botón también la mueven |
| Explorar: tarjeta sincronizada con el marcador | **Nuevo** | Tocar un marcador mueve la tarjeta; deslizar las tarjetas mueve el mapa |
| Explorar: «Buscar en esta zona», Capas (Mapa · Satélite · Relieve), Mi ubicación | **Nuevo** | Las capas son las de la web (v50.43) |
| Explorar: filtros Todos los puntos · Arrecifes · Pecios · Cuevas · Paredes · Salidas con plazas · Centros | **Nuevo** | |
| Buscar: centros y puntos al escribir | **Nuevo** | Con accesos a Viajes, Top 10 y Todos los centros |
| Fichas de centro, freelance y punto con Llamar · WhatsApp · Cómo llegar · Compartir | **Completado** | Las fichas son las de la web. La app añade las cuatro acciones (en el punto: Cómo llegar y Compartir) |
| Barra fija «Desde X € · Reservar» en la ficha | **Nuevo** | El precio más bajo de los servicios del centro |
| Reserva rápida en una hoja, con «Cambiar» en cada línea | **Nuevo** | Salida (otras fechas del mismo servicio), personas, titulación (de la ficha), equipo de alquiler con su precio, extras y nota. Total del servidor al momento. «Más opciones» abre la reserva completa de la web (guía, nitrox, recogida) |
| Reservar sin cuenta: la sesión se pide al final | **Nuevo** | Después de entrar, la hoja se vuelve a abrir con la salida elegida |
| Pago con Stripe Checkout (Apple Pay y Google Pay) que vuelve a la app | **Nuevo** | Se abre en una pestaña del navegador del móvil (así funciona Google Pay) y vuelve sola a la app («Confirmando tu pago»). Si se cancela, vuelve a la reserva |
| Reservas: Próximas e Historial, «Pagar ahora», «Ver QR», WhatsApp | **Nuevo** | El detalle (QR, cancelar, cambiar fecha, pagar) es el de la web |
| Buddies | **Pendiente** | No existe en el servidor (encargo de Buddies sin programar). La pestaña lo dice y no inventa nada |
| Mi área: puntos, inmersiones del Log Book, accesos a Log Book, Mis puntos, Recompensas, Avisos y documentos, Mi ficha y Ajustes | **Nuevo** (el hub) | Las pantallas de destino son las de la web |
| Ajustes: tema, tamaño del texto, idioma (3), Mi cuenta, textos legales, cerrar sesión, borrar la cuenta, versión | **Nuevo** | Borrar la cuenta del buceador: con su contraseña, como en la web |

### WhatsApp manual (apartado 7)

| Punto | Estado | Nota |
|---|---|---|
| WhatsApp al centro con el mensaje ya escrito en el idioma del cliente | **Nuevo** (lado buceador) | Hoja con el mensaje editable (nombre, actividad, fecha, hora y n.º de reserva) y «Abrir WhatsApp». Usa el teléfono público del centro **si tiene prefijo internacional**; si no, lo dice |
| El centro escribe al cliente por WhatsApp en su idioma | **Tanda 2** | Va con Centro PRO |

### APK de pruebas (apartado 9)

| Punto | Estado | Nota |
|---|---|---|
| `com.worldives.app.pruebas`, nombre «WORLDIVES Pruebas», icono con franja TEST | **Nuevo** | Convive con la app de producción |
| Banda fija siempre visible | **Nuevo** | Naranja, con el servidor y el botón «Reportar fallo» |
| Servidor configurable (solo en pruebas) | **Nuevo** | Pantalla de entrada; se cambia desde Ajustes |
| HTTP sin cifrar solo en pruebas | **Nuevo** | Comprobado automáticamente en cada compilación |
| Entrada rápida con las cuentas de prueba | **Nuevo** | Solo responde con el entorno de pruebas en marcha (`WOD_DEMO_MODE=1`): fuera de él, la dirección no existe (404) |
| «Reportar fallo» con captura, pantalla, versión, modelo y hora | **Nuevo** | Desde la banda, desde Ajustes o agitando el móvil. Se guarda en `data/pruebas/fallos/` del ordenador |
| Stripe en modo test | **Ya estaba** | Las claves de test van en el `.env` del entorno de pruebas (README-PRUEBAS, apartado 5) |
| Sin WhatsApp ni correos reales | **Completado** | Correos: ya se guardaban en archivos. WhatsApp: en Pruebas la app enseña el mensaje y no abre WhatsApp |
| Firmada con una clave de pruebas; versión visible; se instala encima de la anterior conservando la sesión | **Nuevo** | La clave vive en la caché de GitHub, nunca en el repositorio. La versión, en la entrada y en Ajustes |
| Variante de producción `com.worldives.app` sin nada de pruebas, comprobado automáticamente | **Nuevo** | Sin cuentas de prueba, sin ajuste de servidor, sin HTTP sin cifrar, sin depuración |

### Pruebas (apartado 11)

| Punto | Estado | Nota |
|---|---|---|
| Pruebas del servidor de la app | **Nuevo** | `tests/test_v50_48_app.py`: 11 pruebas |
| Recorrido en navegador a tamaño de móvil (390 y 360), es/en/fr, Clásico y Noche, Normal y Enorme | **Nuevo** | `tests/navegador/e2e_app.py`: 78 comprobaciones, todas correctas |
| La APK de verdad en un emulador Android | **Nuevo** | `movil/scripts/emulador.py` en GitHub Actions: **21 de 21** (Android 14, pantalla de 320 px): entrada, servidor, entrada rápida, plugins nativos, botón atrás, captura y «Reportar fallo» guardado en el ordenador, vuelta al lanzador y que todo cabe en la pantalla |
| Medir las promesas (reserva ≤ 30 s y ≤ 5 toques, «Hoy» ≤ 5 s, arranque ≤ 2 s) | **Tanda 4** | Primera medida: ver abajo |

## Promesas: primera medida

- **Reserva:**
  - en el recorrido automático, de «Reservar» a la página de pago tarda unos 6 s, con dos cambios por el camino;
  - el camino corto son 3 toques: «Reservar» → «Reservar y pagar» → Google Pay.
- **Arranque en frío:**
  - en el emulador de GitHub, 5,6 s hasta la pantalla de entrada (`arranque.txt` en las capturas del emulador);
  - ese emulador no tiene aceleración gráfica y es mucho más lento que un móvil, así que la medida buena se hace en
    la Tanda 4 con móviles reales.

## Limitaciones conocidas

1. **Tema y tamaño del texto:** solo cambian las pantallas propias de la app. Las páginas de la web que se abren
   dentro siguen en claro y con su tamaño.
2. **Justificante en PDF:** dentro de la app se esconde el botón. El navegador del móvil no tiene la sesión de la app
   y no podría descargarlo. El QR y los datos de la reserva están en el detalle de la reserva.
3. **Enlaces que abren directamente la app (App Links) de `/r/…`:** necesitan la clave de firma de producción y el
   archivo `assetlinks.json` en el dominio. Van cuando haya cuenta de desarrollador (número DUNS).
4. **Google Pay:** solo aparece en la pestaña del navegador (Custom Tabs), por eso el pago se abre ahí.
5. **Pagos en la app de pruebas:** necesitan la clave de test de Stripe en el `.env` del entorno de pruebas. Sin ella,
   el pago online sale desactivado, como en la web.
6. **Volver de Stripe:** algunos navegadores piden tocar «Volver a WORLDIVES Pruebas» en vez de volver solos. La
   página de vuelta tiene ese botón grande.
7. **Mapa en el entorno de pruebas sin mapa base:** si el ordenador no tiene el mapa base (`data/tiles`), se ven los
   puntos sobre fondo azul, como en la web.

## Pendiente de decisión del titular

1. **Buddies:** hay que programarlo primero en el servidor (encargo de Buddies). ¿Lo metemos antes de la Tanda 4?
2. **Roles del personal y borrado de cuenta de centros y freelance:** decisiones 4 y 5 de la Tanda 0, se necesitan
   para la Tanda 2.
3. **Más idiomas en la app:** cuando quieras, los textos de `scripts/idiomas/datos/app.json` se traducen a los otros
   seis idiomas de la web y se activan.
