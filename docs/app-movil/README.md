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
  - reserva cronometrada (interactiva): con cuenta o por primera vez, iOS o Android, tema oscuro o claro;
  - Reservas, «Después de pagar» y Perfil.
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

Reservar cuesta **2 toques más la confirmación del monedero** (3 si se ajusta algo), en unos 18–28 s. El centro ve su
día al abrir la app y sabe quién bucea mañana, y con qué equipo, con 1 o 2 toques.

## Stack recomendado

**React Native + Expo (TypeScript)**, con una parte nativa pequeña en Swift y Kotlin para los widgets y las Live
Activities.
- **Usa los componentes del propio sistema** (pestañas, hojas, botones). Así Liquid Glass en iOS y Material 3
  Expressive en Android vienen de Apple y de Google y se actualizan con cada versión del sistema.
- **Flutter dibuja sus propios componentes:** imitar Liquid Glass y Material 3 Expressive sería trabajo nuestro, y
  siempre iría un paso por detrás.
- **Mismo lenguaje que la web** (JavaScript): se comparten los textos de los 9 idiomas, los formatos de fecha e
  importe y los tipos de la API.
- **Si el equipo que se contrate domina Flutter**, también es viable. El resto del diseño (API, datos, flujos) no
  cambia.

El servidor sigue siendo el actual (Python + SQLite). No hace falta Supabase ni Firebase como base de datos:
- **Firebase solo para enviar push en Android (FCM).** Es lo que exige Google.
- **El tiempo real va con SSE** desde el mismo servidor.

## Decisiones que necesito de ti

Algunas chocan con decisiones ya tomadas para la web. No he cambiado nada: te propongo una opción en cada caso.

| # | Tema | Conflicto o duda | Recomendación |
|---|---|---|---|
| 1 | **Stack** | Flutter o React Native | React Native + Expo (arriba) |
| 2 | **Mensajería con clientes y personal** | El encargo la pide. La decisión vigente es **«No hay chat en la web»**: los avisos salen del WhatsApp de cada centro y las respuestas le llegan a su WhatsApp (v50.47) | **Mantener sin chat**: botón «Escribir al centro» que abre su WhatsApp, más los avisos (push, WhatsApp, correo). Para el personal, notas por salida dentro de la app. Un chat propio supone moderación, guardar conversaciones (RGPD) y unas 4–6 semanas más |
| 3 | **Idiomas** | El encargo dice ES, EN, FR, DE e IT. La web ya está en **9** (también PT, NL, PL y ZH) | **Los 9 desde el primer día**: los textos y los correos ya existen y añadir 4 idiomas a la app cuesta poco |
| 4 | **Cuestionario médico** | El encargo pide guardarlo de forma segura. La web dice hoy «No subas certificados médicos»: son datos de salud (art. 9 RGPD) | Firmarlo en la app después de pagar y guardar **solo el resultado** («apto» o «necesita certificado médico») más las respuestas cifradas, visibles solo para el centro de esa reserva y **borradas a los 30 días** de la inmersión. Necesita consentimiento explícito y una evaluación de impacto (EIPD): **abogado** |
| 5 | **Reserva como invitado** | Hoy la web exige cuenta para reservar | Cuenta creada al pagar con los datos del monedero, sin contraseña. Sirve solo para esa reserva hasta que el buceador la confirma con una passkey o con el enlace del correo. **El invitado no puede elegir «pagar en el centro»**: paga la reserva o la señal, para evitar plazas fantasma |
| 6 | **Nivel exigido a un invitado** | Validar el nivel sin pedir datos rompería los 30 s | La hoja dice qué exige la salida y al pagar declara que lo tiene. El centro lo comprueba en el check-in. Si no lo tiene, cambio a una salida apta o devolución íntegra |
| 7 | **Estado del mar** | Hoy la web no tiene datos de oleaje ni viento | **Puertos del Estado** para España y **Copernicus Marine** para el resto (se pueden usar citando la fuente), en caché por horas. Un proveedor comercial único es más cómodo, pero tiene coste anual |
| 8 | **Pagos a freelance que trabajan para un centro** | El encargo pide repartir pagos con Stripe Connect. Hoy cada reserva se cobra directamente en la cuenta del centro o del freelance, sin comisión (v50.34) | Mantener el cobro directo. Lo que el centro paga al freelance por un trabajo va fuera de la app al principio (con factura) y la app lo registra en «Cobros». Repartir un mismo pago entre dos cuentas, solo si hace falta, en una fase posterior |
| 9 | **Analítica del embudo** | El encargo pide medir el tiempo hasta reservar. La web no usa analítica ni cookies de terceros | Medirlo en el servidor, con totales por día y sin guardar nada en el móvil ni usar SDK de terceros (doc. 2). **Abogado:** confirmar si hace falta consentimiento |
| 10 | **Cuentas de desarrollador** | Hacen falta para publicar, para Apple Pay y para las passkeys | Darlas de alta **como empresa** en Apple y Google (número D-U-N-S). Sin ellas no se puede empezar la fase 0 |

## Lo que no he hecho todavía, a propósito

- **No he escrito código de la app:** el encargo pide estos cuatro entregables antes de programar.
- **No he tocado la web.** Los cambios de servidor que hacen falta (API v1, tokens, push, invitado, niveles) están
  listados en el doc. 2 y empiezan en la fase 1.

## Siguiente paso

1. Respondes a las 10 decisiones.
2. **Fase 0** (4 semanas):
   - Figma completo a partir del lienzo;
   - prueba del prototipo con 5 personas reales y un centro, cronometrada;
   - contrato OpenAPI de `/api/v1/`;
   - cuentas de Apple, Google y Stripe preparadas.
