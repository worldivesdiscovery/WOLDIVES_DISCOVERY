# App WORLDIVES · 1. Mapa de pantallas y flujos de los tres roles

Entregable 1 del encargo «App de reservas de buceo — iOS y Android (2027)». El prototipo navegable (entregable 2)
está en el lienzo «App WORLDIVES · prototipo». Este documento es la lista completa de pantallas, la que se dibujará
en Figma.

**Regla de este documento:** cada pantalla dice cuántos toques cuesta llegar a ella. También dice qué parte de la web ya
lo hace hoy, para reutilizarlo y no inventar otra versión.

## Cómo se cuentan los toques y el tiempo

- **Toque:** cada pulsación dentro de la app. Deslizar para ver más no cuenta.
- **Paso del sistema:** la confirmación del pago la pide el propio teléfono, no la app:
  - en iOS, doble clic en el botón lateral con Face ID o Touch ID;
  - en Android, el botón «Continuar» de Google Pay.
  Cuenta en el tiempo, pero no como toque de la app. Lo digo claro porque en Android es una pulsación más.
- **Los 30 segundos** empiezan al abrir la app y terminan en «Reserva confirmada».

| Tramo | Presupuesto |
|---|---|
| Arranque en frío | 2 s |
| Mirar la Home y elegir salida | 8–12 s |
| Revisar la hoja de la salida y, si hace falta, ajustar personas o equipo | 4–8 s |
| Pago con Apple Pay o Google Pay (paso del sistema) | 3–5 s |
| Animación de confirmación | 1 s |
| **Total** | **18–28 s** |

## Estructura de navegación

Un solo binario y tres «caras», según el tipo de cuenta:
- La barra inferior cambia según el rol.
- Las acciones principales van siempre en la mitad inferior, al alcance del pulgar.
- Quien es buceador y además trabaja en un centro cambia de cara desde «Perfil», como hoy en la web («Cambiar de
  centro», v50.47).

| Rol | Barra inferior (4 pestañas) |
|---|---|
| Buceador (y quien aún no tiene cuenta) | Inicio · Explorar (mapa) · Reservas · Perfil |
| Centro | Hoy · Agenda · Clientes · Más |
| Freelance | Hoy · Agenda · Trabajos · Cobros |

## Buceador

### Flujo principal: reservar en menos de 30 segundos (2 toques, 3 si ajusta algo)

```
Abrir app ─► Inicio ──(toque 1: la salida)──► Hoja de la salida ──(toque 2: Pagar)──► Monedero del sistema ──► ✓ Confirmada
                                   │                      │
                                   │                      └─ ajuste opcional (+/− personas, equipo): toque 3
                                   └─ chip de fecha si no es «Hoy»: cuenta como el toque de ajuste
```

| # | Pantalla | Qué se ve | Toques desde Inicio | En la web hoy |
|---|---|---|---|---|
| B1 | **Inicio** | Arriba, «Tu próxima inmersión» (cuenta atrás, punto de encuentro, QR) o una sugerencia según nivel, ubicación e historial. Chips **Hoy · Mañana · Finde · Elegir**. Lista de salidas con hora, punto, nivel exigido, plazas libres al momento, precio final y estado del mar | 0 | Explorar y fichas de centro (`/api/provider-services`, `/api/center-directory`) |
| B2 | **Hoja de la salida** (sobre el Inicio, no es pantalla nueva) | Foto o vídeo corto del punto, hora y punto de encuentro, «Apto para tu Advanced» o, si no hay datos, «Exige Advanced: lo confirmas al pagar», personas (+/−), equipo con **tallas guardadas**, precio total sin sorpresas, política de cancelación en una línea. Botón **Reservar con Apple Pay / Google Pay**. Debajo, en pequeño: «Pagar señal de X €» o «Pagar en el centro» si el centro lo permite. Sin cuenta: una línea «Se crea tu cuenta con Apple / Google» sobre el botón, y «Llamar al centro» | 1 | Reserva y presupuesto (`/api/booking-quote`, `POST /api/bookings`) |
| B3 | **Monedero** | Hoja de Apple Pay o Google Pay con el importe y el nombre del centro. La primera vez va precedida del «Continuar con Apple / Google» del sistema, que crea la cuenta | 2 | Pago con Stripe en el navegador (Checkout) |
| B4 | **Reserva confirmada** | Animación, vibración, «Añadir a Wallet / Calendario», QR de la reserva y aviso suave: «Firma el descargo antes de llegar (1 min)» | — | Página «pago-ok» y correo |
| B5 | **Después de pagar** | Descargo, titulación, seguro y tallas (sin cuestionario médico: decisión del 13/10). Se hace cuando quiera, antes de la salida. **Nunca bloquea la reserva** | desde B4 o un aviso | Descargo firmado (v50.40), documentos de la cuenta |

**Modos de reserva que ya tiene la web** (el centro elige el de cada servicio):
- **Pago al reservar:** es el flujo de arriba.
- **Bajo petición:** el botón dice «Solicitar plaza» y no hay paso de monedero; el centro acepta y el buceador paga
  con un toque desde el aviso.
- **Señal o pago en el centro:** son variantes del botón en B2.

**Reglas que hacen posible el medio minuto:**
- **Sin pantalla de registro antes de reservar.** Sin cuenta solo se ve la información del centro y su teléfono
  (decisión del 13/10). La primera vez, el botón de pago abre primero «Continuar con Apple» o «Continuar con Google»
  del sistema, que crea la cuenta con nombre y correo sin formularios. Justo después se abre el monedero. Es el mismo
  toque; el sistema pide una confirmación más (Face ID, o elegir la cuenta de Google).
- **Nivel:** con titulación guardada, el Inicio solo muestra salidas aptas, y un interruptor «Ver todas» enseña el
  resto marcadas «No apta». En la primera reserva, la hoja dice qué exige la salida y el pago incluye la declaración
  «Tengo esa titulación». El centro la comprueba en el check-in. Si no la tiene, cambio a una salida apta o
  devolución íntegra.
- **Se guarda una sola vez:** datos, titulación, tallas y seguro. La web ya los guarda en la ficha del buceador.
- **El descargo va después de pagar.** No hay cuestionario médico en la app (decisión del 13/10).

### Resto de pantallas del buceador

| # | Pantalla | Para qué | Toques desde Inicio | En la web hoy |
|---|---|---|---|---|
| B6 | **Reservas** (pestaña) | Próximas, con QR que funciona sin cobertura, y el historial | 1 | Mi área → Mis reservas |
| B7 | **Repetir reserva** | Desde el historial: la misma salida, la próxima fecha libre, directo a B2 | 2 (Reservas → Repetir) | No existe |
| B8 | **Cambiar o cancelar** | Según la política del centro: «Cambiar a otra fecha» o «Cancelar y devolver X €», con la devolución automática | 2 desde la reserva | `/api/bookings/<id>/cancel`, `/change-date` |
| B9 | **Explorar** (mapa) | Puntos de buceo con filtros: nivel, profundidad, barco, costa, nocturna. Tocar un punto lleva a sus salidas | 1 | Mapa y fichas de puntos (`/api/dive-points/map`) |
| B10 | **Ficha del punto** | Fotos, profundidad, nivel recomendado, centros y sus salidas, valoraciones | 2 | Ficha del punto |
| B11 | **Ficha del centro** | Servicios, salidas, valoraciones de quien buceó. Botones **«WhatsApp del centro»** y **«Llamar»**. Es lo que ve quien no tiene cuenta | 2–3 | Ficha del centro |
| B12 | **Perfil** | Datos, titulaciones (foto o verificación), tallas, seguro, idioma (español, inglés o francés), privacidad, puntos | 1 | Mi cuenta |
| B13 | **Logbook** | Inmersiones con fecha, punto, profundidad, tiempo y firma del guía. Número de inmersiones | 2 | Log Book |
| B14 | **Avisos** | Cancelaciones, cambios y recordatorios, con «Ver mi reserva» | 1 (campana) | Mi área → Avisos (v50.47) |
| B15 | **Asistente** (fase 3) | «¿Qué buceo me recomiendas mañana?» Responde solo con salidas reales: nivel, plazas y estado del mar | 1 | No existe |
| B16 | **Valorar** | Solo tras una salida con check-in. Llega como aviso al día siguiente | desde el aviso | Reseñas de centro (hay que limitarlas a quien buceó: ver doc. 2) |

### Superficies fuera de la app (fase 3, salvo el aviso de recordatorio)

- **Widget de inicio:** la próxima inmersión, con cuenta atrás, hora y punto.
- **Live Activity y Dynamic Island (iOS)**, y **notificación en curso (Android)**:
  - se activan unas horas antes de la salida;
  - muestran la cuenta atrás, el punto de encuentro con su enlace al mapa y el QR;
  - se actualizan si el centro cambia la hora.

## Centro de buceo

### «Hoy» es la Home (todo lo importante en 1 toque)

| # | Pantalla | Qué se ve | Toques | En la web hoy |
|---|---|---|---|---|
| C1 | **Hoy** | Chips **Hoy · Mañana · Semana**. Ingresos del día y de la semana, y reservas nuevas. Cada salida con hora, punto, barco, **ocupación 9/12**, personal asignado y alertas («2 sin descargo», «1 sin pagar») con icono y texto, no solo color. Abajo: **Escanear QR** y **Nueva salida** | 0 | Panel → Resumen y Planning (`/api/center/planning`, `/api/manifest/day`) |
| C2 | **Salida** (se despliega dentro de Hoy) | Cada buceador con nivel, nº de inmersiones, documentos pendientes (alerta), tallas, si ha pagado y check-in. Acciones: cerrar plazas, cambiar hora, cancelar por meteo, asignar personal | 1 | Manifiesto (v50.40) |
| C3 | **Equipo a preparar** | Tallas sumadas de la salida o del día: «Trajes: 2 S · 3 M · 1 L», y lo mismo con escarpines, chalecos, aletas y lastre | 1 (botón en C1) | Datos en la ficha; el resumen es nuevo |
| C4 | **Escáner QR** | Funciona sin cobertura. Verde: nombre y salida. Ámbar: falta descargo o pago | 1 | Check-in sin conexión (v50.42, `/api/manifest/sync`) |
| C5 | **Nueva o editar salida** | Servicio, fecha, hora, plazas, barco y punto. Duplicar la de ayer | 1–2 | Planning (`/api/provider-services/slot`) |
| C6 | **Cancelar por meteo** | El flujo de v50.47: motivo, quién recibe cada canal (push, WhatsApp, correo), dinero (devolver o elegir otra fecha), escribir la fecha, 10 s para deshacer y panel de estado | 2 | Avisos masivos (v50.47) |
| C7 | **Asignar personal** | Personal del centro y freelance disponibles ese día. Tocar asigna u ofrece el trabajo | 2 | Grupos del manifiesto (`slot_groups.guide_user_id`); ofertas a freelance: nuevo |
| C8 | **Clientes** | Buscador, recurrentes, nivel y última inmersión | 1 | Panel → Clientes |
| C9 | **Contacto con clientes** | Sin chat (decisión del 13/10). Desde la ficha de cada buceador, «WhatsApp» y «Llamar»; los clientes escriben al WhatsApp del centro. Notas internas por salida para el personal | 2 | Avisos de una reserva; sin chat |
| C10 | **Estadísticas** | Ocupación, ingresos, clientes recurrentes, valoraciones | 2 (Más → Estadísticas) | Analítica e informes |
| C11 | **Ajustes** | Cobros (Stripe), WhatsApp, avisos y recordatorio, calendario (iCal o Google Calendar), equipo y roles | 2 | Panel (v50.34 a v50.47) |

**Criterio de aceptación del centro:** saber quién bucea mañana y qué equipo necesita en menos de 10 segundos.
- Toque 1: «Mañana». Se ven las salidas, cuántos van y el resumen de equipo de cada una.
- Toque 2, opcional: «Equipo a preparar», con el total del día.

## Freelance

| # | Pantalla | Qué se ve | Toques | En la web hoy |
|---|---|---|---|---|
| F1 | **Hoy** | Dónde, a qué hora y con quién (centro, salida, nº de buceadores y nivel), con «Cómo llegar». Igual de clara que la del centro | 0 | Mi agenda |
| F2 | **Agenda** | Semana en tiras: tocar un día lo **bloquea o lo abre** (1 toque). Medio día y vacaciones | 1 | Motor de agenda (v50.44: días, medio día y bloqueos) |
| F3 | **Trabajos** | Ofertas de los centros con fecha, salida, papel (guía o instructor) e importe. **Aceptar o rechazar** con un toque | 1 | Nuevo |
| F4 | **Mis clientes y reservas directas** | Las reservas de sus propios servicios | 1–2 | Panel del freelance → Reservas |
| F5 | **Cobros** | Cobrado, pendiente y facturas de sus reservas directas (Stripe) y de los trabajos de centros | 1 | Cobros y pagos (v50.34) |
| F6 | **Documentos** | Titulaciones, seguro y licencias, con aviso 45 días antes de caducar | 2 | Seguro y documentos (con caducidad) |

## Acciones de cada rol, contadas

| Acción | Toques | Objetivo del encargo |
|---|---|---|
| Buceador: reservar (titulación guardada, sin ajustes) | 2 + paso del sistema | ≤ 3 |
| Buceador: reservar con un ajuste (personas, fecha o equipo) | 3 + paso del sistema | ≤ 3 |
| Buceador: repetir una reserva | 2 (Reservas → Repetir) + Pagar | — |
| Buceador: cancelar o cambiar | 2 desde la reserva | 2 |
| Centro: ver el día | 0 (es la Home) | 1 |
| Centro: quién bucea mañana y qué equipo | 1–2 | < 10 s |
| Centro: check-in | 1 (Escanear) | ≤ 2 |
| Centro: cancelar por meteo | 2, más escribir la fecha para confirmar | ≤ 2 |
| Freelance: bloquear un día | 1 | 1 |
| Freelance: aceptar una oferta | 1 | 1 |
