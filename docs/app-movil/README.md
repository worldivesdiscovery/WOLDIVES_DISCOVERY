# App WORLDIVES para iOS y Android (2027) · diseño previo

Respuesta al encargo **«App de reservas de buceo — iOS y Android (2027)»**, en la parte «Antes de programar
entrega».

| # | Entregable | Dónde |
|---|---|---|
| 1 | Mapa de pantallas y flujos de los 3 roles | `01-pantallas-y-flujos.md` y el lienzo del prototipo (una fila por rol) |
| 2 | Prototipo navegable del flujo de reserva, cronometrado | Lienzo **«App WORLDIVES · prototipo»** (Artifact privado: https://claude.ai/artifact/2mSm2bXiqjoLwfnLtWdUpU; para enseñarlo hay que compartirlo desde su menú «Compartir») |
| 3 | Modelo de datos y API compartida con la web | `02-datos-y-api.md` |
| 4 | Estimación por fases | `03-estimacion.md` |

**Sobre el entregable 2:** el encargo pide Figma. El prototipo es un lienzo interactivo que se abre con un enlace en
el móvil o en el ordenador y mide solo el tiempo y los toques de quien lo prueba. Sirve para la prueba con 5 personas
de la fase 0. Las pantallas se pasan a Figma al empezar esa fase.

**Qué hay en el lienzo:**
- **Buceador:**
  - reserva cronometrada (interactiva): con cuenta o por primera vez (la cuenta se crea con el botón de pago), iOS o
    Android, tema oscuro o claro;
  - Reservas (con «WhatsApp del centro»), «Después de pagar» (sin cuestionario médico) y Perfil.
- **Centro:**
  - «Hoy» cronometrado (interactivo): quién bucea mañana y qué equipo preparar;
  - check-in sin cobertura y cancelar por meteo.
- **Freelance** (interactivo): Hoy, agenda (bloquear o abrir un día con un toque) y ofertas de trabajo.

Los datos son de ejemplo. Las fotos son tres de la propia web, que aún no tienen el origen registrado
(`docs/legal/imagenes-origen.md`): antes de enseñar el prototipo fuera del equipo, hay que cambiarlas por fotos con
licencia.

## En una frase

La app es **otra cara de la misma web**:
- misma base de datos y mismas reglas de precios, plazas, pagos y aislamiento entre centros;
- una API versionada (`/api/v1/`) que primero usa la app y después la web.

Reservar cuesta **2 toques más la confirmación del monedero** (3 si se ajusta algo), en unos 18–28 s. La primera vez,
el mismo botón de pago crea la cuenta con Apple o Google (Face ID o la cuenta de Google del teléfono) y paga a
continuación: no hay pantalla de registro. El centro ve su día al abrir la app y sabe quién bucea mañana, y con qué
equipo, con 1 o 2 toques.

## Stack (decidido el 13/10: React Native + Expo)

**React Native + Expo (TypeScript)**, con una parte nativa pequeña en Swift y Kotlin para los widgets y las Live
Activities.
- **Usa los componentes del propio sistema** (pestañas, hojas, botones). Así Liquid Glass en iOS y Material 3
  Expressive en Android vienen de Apple y de Google y se actualizan con cada versión del sistema.
- **Flutter dibuja sus propios componentes:** imitar Liquid Glass y Material 3 Expressive sería trabajo nuestro, y
  siempre iría un paso por detrás.
- **Mismo lenguaje que la web** (JavaScript): se comparten los textos (la app va en español, inglés y francés), los
  formatos de fecha e importe y los tipos de la API.
- **Si el equipo que se contrate domina Flutter**, también es viable. El resto del diseño (API, datos, flujos) no
  cambia.

El servidor sigue siendo el actual (Python + SQLite). No hace falta Supabase ni Firebase como base de datos:
- **Firebase solo para enviar push en Android (FCM).** Es lo que exige Google.
- **El tiempo real va con SSE** desde el mismo servidor.

## Decisiones tomadas (13/10/2026)

| Tema | Decisión | Cómo queda |
|---|---|---|
| **Mensajería** | No hay chat. El botón **«WhatsApp del centro»** abre el WhatsApp del centro de buceo | Sigue la decisión de la web (v50.47). Las respuestas a los avisos también llegan al WhatsApp del centro. Para el personal, notas por salida dentro de la app |
| **Idiomas de la app** | **Español, inglés y francés** | Si el teléfono está en otro idioma, la app se abre en inglés. Los avisos push van en el idioma de la app. **La web sigue con sus 9 idiomas** salvo que digas lo contrario |
| **Cuestionario médico** | **Nada de cuestionarios médicos** en la app | No se piden ni se guardan datos de salud. Después de pagar solo quedan el descargo, la titulación, el seguro y las tallas. Si un centro necesita el cuestionario, lo hace en papel en el muelle, como hasta ahora |
| **Sin cuenta (invitado)** | Sin cuenta solo se ve la información del centro (salidas, precios, cómo llegar) y el **teléfono para llamar** | No hay reserva sin cuenta. Para no perder los 30 s, el botón de pago crea la cuenta con Apple o Google y paga después, sin formularios. Quien no quiera cuenta tiene «Llamar al centro» en la hoja de la salida y en la ficha |
| **Comisiones** | **Sin comisión** de WORLDIVES de momento | Como hoy (v50.34): cobro directo en la cuenta Stripe del centro o del freelance, que paga la comisión de Stripe. **Cobrar al cliente la comisión de Stripe como recargo por pagar con tarjeta no está permitido** con tarjetas de particulares en la UE (directiva de servicios de pago, PSD2). Lo legal es que cada centro ponga su precio final ya con eso incluido, sin línea aparte. Si algún día se quiere unos «gastos de gestión» visibles, iguales para cualquier forma de pago y dentro del precio final desde el principio, primero lo revisa el abogado |
| **Pagos a freelance** | Sin reparto de pagos por ahora | Lo que un centro paga a un freelance por un trabajo va fuera de la app (con factura) y la app lo registra en «Cobros» |
| **Tecnología** | **React Native + Expo** (TypeScript) | La versión 0.1 ya está hecha con ella, en `app-movil/` |
| **Estado del mar** | **Boyas de Puertos del Estado** y, si no hay dato, la fuente más fiable disponible | Detalle en el doc. 2, «Estado del mar: de dónde salen los datos». La 0.1 enseña datos de ejemplo |
| **Cuentas de desarrollador** | Todavía no hay número D-U-N-S | Se empieza con un **APK de pruebas para Android** que se instala fuera de Google Play. Cuando llegue el D-U-N-S se dan de alta las cuentas de Apple y Google como empresa |

## Decisiones que siguen pendientes

| # | Tema | Recomendación |
|---|---|---|
| 1 | **Nivel exigido en la primera reserva** | La hoja dice qué exige la salida y, al pagar, el buceador declara que tiene esa titulación. El centro lo comprueba en el check-in. Si no la tiene, cambio a una salida apta o devolución íntegra. Así no hace falta un toque más. **Es lo que hace la 0.1** |
| 2 | **Analítica del embudo** | Medirla en el servidor, con totales por día, sin guardar nada en el móvil ni usar SDK de terceros (doc. 2). **Abogado:** confirmar si hace falta consentimiento |
| 3 | **D-U-N-S y cuentas de Apple y Google** | Pedir el D-U-N-S (gratuito; puede tardar varios días laborables) y dar de alta las dos cuentas **como empresa**. Sin ellas no hay TestFlight, ni prueba interna en Google Play, ni Apple Pay real |

## Versión de pruebas 0.1 (APK para Android)

Está en `app-movil/` (instrucciones en `app-movil/README.md`).
- **Qué es:** las pantallas de los tres perfiles, en español, inglés y francés, con datos de ejemplo, pagos e inicio de
  sesión simulados (las hojas de Apple y Google dicen «Simulado») y el cronómetro de las pruebas de 30 s y 10 s.
- **Qué funciona de verdad:** la cámara para leer el QR en el check-in, la firma con el dedo, abrir WhatsApp, llamar,
  cómo llegar, y que los cambios se guarden en el móvil.
- **Cómo se consigue el APK:** GitHub lo compila solo en cada cambio de `app-movil/` (flujo «App Android (APK de
  pruebas)») y lo deja para descargar 30 días.
- **No toca la web ni el servidor:** la web no cambia y los zips de la web no llevan la app.

## Siguiente paso

1. **Probar el APK** con 5 personas y un centro, con las pruebas cronometradas de la pantalla de inicio. Los
   resultados quedan en el propio móvil (Perfil o Más).
2. **Versión 0.2:** empezar la API `/api/v1/` en el servidor (doc. 2) y conectar la app: salidas, reservas y check-in
   reales, y el estado del mar de las boyas.
3. **Con el D-U-N-S:** cuentas de Apple y Google, Stripe con Apple Pay y Google Pay reales, y la primera versión en
   TestFlight y en prueba interna de Google Play.
