# Motor de reservas multicanal · estado actual (v50.55, antes de cambiar nada)

Fecha: 15/10/2026. Encargo «Motor de reservas multicanal + seguros de buceo», Bloque 1, Parte A.
Revisión del código de la v50.55 (commit `c3bf2c3`) y prueba real contra el servidor, sin tocar nada.
Las líneas citadas son de `app/server.py` en ese commit.

**En pocas palabras:**
- **Las plazas de una salida ya no se venden dos veces**, entre por donde entre la reserva. Las tres rutas que crean
  reservas con salida descuentan con la misma operación atómica. La prueba real da exactamente 3 de 20, también con
  4 procesos.
- **Pero hay dos huecos graves.**
  - La reserva manual y la API de integración, **sin indicar la salida**, confirman reservas sin descontar plazas:
    12 personas en un día cuya salida tenía 2 plazas.
  - **La API de integración guarda el precio que le manda la web del centro**: 1 € en vez de 120 €.
- **No hay una función única de reserva.** Hay tres rutas, cada una con sus reglas, sus mensajes y sus olvidos.
- **El widget no reserva:** enseña una lista y abre WORLDIVES en otra pestaña. Se puede incrustar en cualquier web,
  no lleva la marca del centro y obliga a tener cuenta de WORLDIVES.
- **No existen** el campo «canal», la clave de idempotencia, la API v1 de lectura, los avisos automáticos
  (webhooks), la importación de calendarios ni la página propia del centro con QR.

## 1. Canales que existen hoy

| Canal | Cómo funciona hoy | ¿Mismas tablas y plazas que el buscador? |
|---|---|---|
| **Buscador y mapa de WORLDIVES** | `POST /api/bookings` (línea 15296). Exige una cuenta de WORLDIVES. Bloquea la base (`BEGIN IMMEDIATE`) mientras comprueba y crea. Precio calculado en el servidor (`booking_quote`, días con `wag.quote`) | Sí: es la referencia. Escribe `bookings` y descuenta `service_slots.spots_available` (`reserve_slot_spots`) o bloquea días en la agenda común (`claim_booking_days` → `agenda_claim`) |
| **Enlace directo** (Instagram, WhatsApp) | `#/reservar?center=…` o `#/profesional?id=…` (línea 12091). Abre la ficha y la reserva normal de la web | Sí: es la misma ruta que el buscador. No se distingue del buscador |
| **Widget** (Fase 6.5) | `GET /widget/center/<id>` (línea 11671). Página sin scripts con la lista de servicios y sus 3 próximas fechas. Cada botón abre la reserva de WORLDIVES en una pestaña nueva | Sí, porque no reserva: manda a la ruta del buscador. No se puede reservar sin salir de la web del centro |
| **Reserva manual del centro** (teléfono, mostrador) | `POST /api/center/bookings/manual` (línea 16294). Solo centros, no freelance. Ficha de cliente sin cuenta del centro (`find_or_create_customer`) | A medias: con salida descuenta plazas con la misma operación atómica. **Sin salida (fecha y hora) no descuenta nada.** No sirve para servicios por días. No bloquea la base |
| **API de integración** | `POST /api/integrations/bookings` (línea 14203), con la clave `X-WORLDIVES-API-Key` (una por centro, en hash SHA-256). Solo crea reservas: no hay consultas, ni disponibilidad, ni cancelaciones, ni avisos | A medias: con salida y estado «confirmed» descuenta plazas con su propia copia de la operación (línea 14227). **Sin salida no descuenta nada. Acepta el precio y el «pagado» que manda el cliente** |
| **Calendario iCal** (exportar) | `GET /ical/<token>.ics` (línea 11952; `ical_feed`, línea 4565). Por centro y por freelance, no por instructor. Se genera en cada petición, sin caché | Lee las mismas `bookings`: refleja cualquier reserva al momento. No hay importación |

**Avisos al centro:** la ruta del buscador avisa al centro por correo de cada reserva o solicitud
(`notify_booking`, línea 7652). La API de integración no avisa a nadie (línea 14234: solo deja constancia). La manual
no avisa al centro, que es quien la crea.

**Origen de la reserva:** solo existe `bookings.source` con tres valores: `online` (buscador, enlace y widget, sin
distinguir), `manual` y `web` (API). No se guarda el dominio de origen. El planning lo enseña como «WORLDIVES»,
«Manual» o «Tu web» (`BK_SOURCE`, `world-dives-v8.js` línea 4180).

## 2. Cómo se calculan y bloquean las plazas

- **Dónde se descuentan.** `service_slots.spots_available` guarda las plazas libres de cada salida.
  - `reserve_slot_spots` (línea 3532) descuenta con un solo `UPDATE … WHERE spots_available >= ?`. Es atómico en
    SQLite: de dos peticiones a la última plaza, una cambia la fila y la otra no.
  - `release_slot_spots` (línea 3537) devuelve plazas y avisa a la lista de espera.
  - Los servicios por días no tienen salidas. Ocupan bloques en `resource_blocks` (agenda común): `agenda_claim`
    (línea 11083) comprueba los solapes dentro de `BEGIN IMMEDIATE`.
- **Retención mientras se paga («Pago al reservar»).** La reserva queda en `payment_in_progress` con
  `hold_expires_at`. Las plazas se descuentan al momento, así que el contador público ya no las enseña.
  - Duración: **15 minutos por defecto** (`wod/bookings.py` línea 59), configurable de 5 a 60 con
    `WOD_PAYMENT_HOLD_MINUTES`. El encargo pide 10 por defecto.
  - Las retenciones caducadas las libera `run_booking_deadlines` (línea 8957). Corre en el mantenimiento cada
    60 segundos (línea 16611), así que se liberan con hasta un minuto de retraso.
  - Si alguien paga después de caducar, se vuelve a tomar la plaza si queda, y si no se devuelve el dinero
    (línea 6817).
- **«Bajo petición».** La solicitud no descuenta plazas. Al aceptar, `accept_booking` (línea 8904) las toma con
  `reserve_or_fail`. Si ya no quedan, el centro no puede aceptar y ve el motivo.
- **Cancelar, rechazar, caducar, cambiar de fecha.** Todo pasa por `release_booking_spots` (línea 8668) y
  `move_booking` (línea 10021). El cambio de capacidad de una salida (líneas 14345 y 14371) bloquea la base y no deja
  bajar de lo ocupado.
- **Dos personas, la última plaza, dos canales a la vez.** Gana la primera operación que llega a SQLite; la otra recibe
  un error. **El mensaje cambia según el canal:**
  - «Solo quedan 0 plazas disponibles.» (buscador);
  - «Las plazas acaban de cambiar. Revisa la salida.» (manual);
  - «La salida seleccionada no tiene plazas suficientes.» (API).

## 3. Prueba real de sobreventa

Script: `tests/carga/sobreventa_multicanal.py`, contra el servidor real con el simulador de Stripe. Lanza **20 reservas
a la vez** a una salida «Pago al reservar» con **3 plazas**:
- 12 por el buscador (el enlace y el widget van por la misma ruta);
- 4 manuales del centro;
- 4 por la API de integración.

| Ejecución | Reservas con plaza | Plazas libres al final | Respuestas |
|---|---|---|---|
| 1 proceso | **3** | 0 | Buscador 1 · manual 1 · API 1 · el resto rechazadas con los tres mensajes distintos de arriba |
| 4 procesos (`WOD_WORKERS=4`, como en producción) | **3** | 0 | Buscador 1 · manual 0 · API 2 |

**Con salida: correcto, exactamente 3.**

**Sin salida: sobreventa.** Al mismo servicio, mismo día y misma hora que una salida de 2 plazas, 3 reservas manuales y
3 por la API, de 2 personas cada una:

| | Resultado |
|---|---|
| Reservas confirmadas ese día | **6 (12 personas)** |
| Plazas libres de la salida de ese día | 2 (no se ha descontado nada) |

**Precio por la API:** reserva de 2 personas en un servicio de 60 € por persona, mandando `"price": 1` → se guarda
**1 €** en vez de 120 €.

## 4. Fallos encontrados

| # | Gravedad | Dónde | Fallo |
|---|---|---|---|
| F1 | **Grave** | `app/server.py` 14222–14230 y 16308–16334 | La reserva manual y la API **sin salida** (fecha y hora libres) confirman reservas sin descontar plazas. Sobreventa demostrada (12 personas en una salida de 2) |
| F2 | **Grave** | `app/server.py` 14224 | La API de integración guarda el **precio que manda el cliente** (`clean_money(data.get('price'))`) |
| F3 | **Grave** | `app/server.py` 14224–14229 | La API **confirma sin cobrar** y marca «pagado» si el cliente lo dice (`data.get('paid')`). No respeta el modo de reserva del servicio, ni el plan del centro, ni la fecha pasada, ni el máximo de participantes, ni el pago en persona |
| F4 | Media | líneas 14230, 15434, 16334 | **Tres rutas** que insertan reservas, cada una con sus reglas. Solo la del buscador comprueba el plan, la fecha pasada, el máximo por reserva, el pago en persona, los días y la lista de espera |
| F5 | Media | líneas 15354, 16331, 14223 | Mensajes distintos para lo mismo («Sin plazas») según el canal |
| F6 | Media | líneas 15320–15335; 14209; 16294 | **No hay clave de idempotencia.** El buscador detecta el doble clic por una heurística (misma persona, salida y participantes en 2 minutos). La API, por `external_ref`. La manual no tiene nada: un doble toque crea dos reservas |
| F7 | Media | `wod/bookings.py` 59; línea 16611 | Retención de 15 minutos (el encargo pide 10) y liberación con hasta 1 minuto de retraso |
| F8 | Media | líneas 11671–11709 | El widget **no reserva** dentro de la web del centro, se puede incrustar en **cualquier** dominio (`frame-ancestors *`), no lleva logo ni color del centro, tiene un solo formato (lista) y **obliga a tener cuenta** de WORLDIVES (`require_user`, línea 15297) |
| F9 | Media | esquema línea 132; línea 1435 | **No hay campo «canal».** Widget, enlace y buscador son el mismo `online`. No se guarda el dominio de origen. No hay informe por canal |
| F10 | Media | líneas 4565–4600 | **iCal:** horas «flotantes» con la zona del servidor (`X-WR-TIMEZONE`), no la del centro. Un centro de México vería las salidas a la hora de Madrid. Las reservas de varios días salen como un solo día. No hay feed por instructor. No se puede importar |
| F11 | Media | línea 16296 | La reserva manual es solo de centros (el freelance no puede apuntar una reserva por teléfono). No hay bloqueos de plazas sin cliente (grupo, agencia, hotel) ni enlace de pago |
| F12 | Media | líneas 14191–14234 | **No hay API v1**: una sola clave por centro, sin permisos de solo lectura, sin consultas de servicios, disponibilidad ni reservas, sin cancelación, sin avisos automáticos (webhooks) y sin límite de uso por clave |
| F13 | Media | línea 14234 | Las reservas que entran por la API **no avisan** ni al centro ni al cliente |
| F14 | Baja | líneas 11050–11062 | La agenda común de un centro solo conoce el servicio, no al **instructor**: nada impide que el mismo instructor tenga dos cursos de 3 días que se solapen |
| F15 | Baja | línea 12091 | El enlace directo es una dirección con número (`#/reservar?center=12`), sin página propia del centro, sin enlaces a una fecha y sin QR |

## 5. Lo que ya funciona y se conserva

- La operación atómica de las plazas y el bloqueo de la base en la ruta del buscador (v50.51).
- La retención durante el pago, la caducidad de solicitudes y pagos, la lista de espera y el pago tardío.
- La agenda común sin solapes para los días del freelance (v50.44).
- Las fichas de cliente del centro, que nunca se enlazan a una cuenta real (G5).
- Precio, extras y descuentos calculados en el servidor en la ruta del buscador.
- Las pruebas de concurrencia de `tests/test_v50_51_concurrencia.py` (también con 4 procesos).

Siguiente paso (Parte B): una sola función `create_booking` para todos los canales, que corrige F1 a F7, F9 y F13.
