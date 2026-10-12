# App WORLDIVES · 4. Estimación por fases

Entregable 4 del encargo «App de reservas de buceo — iOS y Android (2027)».

Es un **orden de magnitud con ±20 %**. Depende de las decisiones pendientes del README; las que más mueven el plazo
son la mensajería, los datos médicos y el estado del mar.

## Equipo supuesto

| Papel | Dedicación |
|---|---|
| Diseño de producto (Figma, pruebas con usuarios) | 100 % en las fases 0 y 1, 50 % después |
| 2 × desarrollo móvil (React Native + Expo, TypeScript) | 100 % (uno de los dos hace de líder técnico) |
| 1 × backend (Python, el servidor actual) | 100 % |
| Pruebas (QA) | 50 % desde la fase 1 |

## Calendario

| Fase | Semanas | Personas-semana | Qué incluye |
|---|---|---|---|
| **0 · Diseño y base** (antes de programar) | 4 | ~12 | Figma completo; prueba del prototipo con 5 personas reales; contrato OpenAPI de `/api/v1/`; decisiones legales; cuentas de desarrollador de empresa; Apple Pay y Google Pay en Stripe; compilación y publicación automáticas; pruebas técnicas de lo arriesgado: Liquid Glass y Material 3 Expressive, PaymentSheet con cobro directo y passkeys |
| **1 · MVP** | 14 | ~63 | Flujo de reserva del buceador (invitado, Apple Pay y Google Pay, señal, pago en el centro, bajo petición); pagos; «Hoy» del centro con salida y equipo a preparar; check-in QR sin conexión; push y enlaces profundos; 9 idiomas; embudo de tiempo hasta reservar; pruebas automáticas de reserva y pago; beta (TestFlight y prueba cerrada de Google Play) y publicación |
| **2 · Profesionales y servicio** | 10 | ~40 | Panel del freelance (agenda, ofertas de trabajo, cobros, documentos); logbook; cancelación por meteo con push (sobre los avisos de v50.47); estadísticas; estado del mar; niveles entre agencias y validación automática; Google Calendar o iCal; cambiar y cancelar en 2 toques; valoraciones solo con check-in |
| **3 · Extras** | 10 | ~38 | Asistente IA; widgets; Live Activities y Dynamic Island; notificación en curso en Android; mapa avanzado (filtros, capas, mapa sin conexión) |
| **Total** | **38 (~9 meses)** | **~153** | MVP en tiendas a los ~4,5 meses de empezar |

### Detalle de la fase 1 (la que hay que clavar)

| Quién | Trabajo | Semanas |
|---|---|---|
| Backend | Tokens por dispositivo y renovación; passkeys, Apple, Google y código por correo; cuenta de invitado | 4,5 |
| Backend | `/api/v1/` del buceador (Inicio en una llamada, salidas, presupuesto, reservas, cancelar o cambiar) | 3 |
| Backend | PaymentSheet con cobro directo (reutiliza los webhooks actuales) | 1,5 |
| Backend | Push (dispositivos y canal push en el motor de avisos), enlaces universales | 2 |
| Backend | `/pro/today`, equipo a preparar, check-in y sincronización | 2 |
| Backend | Tiempo real (SSE) y embudo agregado | 1,5 |
| Móvil A | Base de la app, tema iOS y Android, oscuro y claro, accesibilidad, 9 idiomas | 2 |
| Móvil A | Inicio con chips, salidas y plazas en tiempo real | 2,5 |
| Móvil A | Hoja de la salida, presupuesto y pago; confirmación con animación y vibración; Wallet y Calendario | 5 |
| Móvil A | Reservas, QR sin conexión, cambiar o cancelar, firmar después de pagar | 3 |
| Móvil A | Pruebas automáticas del flujo de reserva y pago | 1,5 |
| Móvil B | Identidad (passkeys, Apple, Google, invitado), perfil, tallas y titulaciones | 5 |
| Móvil B | «Hoy» del centro, salida y equipo a preparar | 3,5 |
| Móvil B | Escáner QR sin conexión y cola de sincronización | 3 |
| Móvil B | Rendimiento (arranque < 2 s), publicación en tiendas, beta | 2,5 |

## Cómo se comprueba el criterio de aceptación

1. **Fase 0, con el prototipo**, antes de escribir código:
   - 5 personas que nunca lo han visto reservan sin ayuda, cronometradas;
   - 1 centro busca quién bucea mañana y qué equipo necesita.
   - Si alguien pasa de 30 s o de 10 s, se cambia el diseño y se repite.
2. **Fase 1, con la beta real:**
   - la misma prueba con otras 5 personas y 2 centros, en el muelle y con mala cobertura;
   - el embudo de producción (p90 < 30 s) y el abandono en cada paso se revisan cada semana.

## Costes externos (aparte del equipo)

- **Apple Developer Program:** cuota anual, como empresa. Necesita número D-U-N-S.
- **Google Play Console:** pago único, como empresa. Una cuenta personal nueva tendría que pasar antes una prueba
  cerrada con al menos 12 personas durante 14 días; la de empresa no.
- **Stripe:** la comisión de cada pago la paga el centro, porque el cobro es directo en su cuenta.
- **Push (APNs y FCM):** sin coste.
- **Estado del mar:**
  - según el proveedor (decisión en el README);
  - Puertos del Estado y Copernicus Marine se pueden usar citando la fuente;
  - los servicios comerciales piden licencia.
- **Compilación en la nube (Expo EAS):** plan de pago opcional; se puede compilar en máquinas propias.
- **Asistente IA (fase 3):** pago por uso del modelo de lenguaje, con límite mensual.

## Riesgos y cómo se cubren

| Riesgo | Medida |
|---|---|
| Rechazo en la revisión de Apple (cuentas de invitado, borrar la cuenta, Sign in with Apple, Apple Pay) | Revisión previa con las guías de la App Store en la fase 0; cuenta de demostración para el revisor; beta en TestFlight desde la semana 8 |
| Liquid Glass o Material 3 Expressive no disponibles en algún componente de React Native | Prueba técnica en la fase 0. Si falta algo, ese componente se hace nativo (Swift o Kotlin) o se imita con el mismo aspecto |
| Plazas en tiempo real con el servidor actual | SSE con respaldo de consultas cada 30 s; servicio aparte si se pasa de cientos de conexiones |
| El cronómetro de 30 s depende de la cobertura | Inicio guardado en el móvil; la plaza se comprueba en el servidor al pagar |
| Decisiones legales (datos médicos, analítica) | Se cierran en la fase 0 con el abogado, antes de diseñar esas pantallas en detalle |
| Doble trabajo web y app | La web se pasa a `/api/v1/` pantalla a pantalla. Desde la fase 1, ninguna regla de negocio nueva se escribe dos veces |
