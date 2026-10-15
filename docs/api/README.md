# API de reservas de WORLDIVES (v1)

Para centros y profesionales que quieren conectar **su propio sistema** (su web hecha a medida, su programa de
gestión, una agencia) con sus plazas de WORLDIVES. Todo sale del **mismo inventario** que la web, el widget, los
enlaces y las reservas que se apuntan a mano: lo que se vende por la API desaparece de los demás canales al momento.

- Dirección base: `https://worlddivesdiscovery.com/api/v1`
- Formato: JSON en UTF-8. Fechas `AAAA-MM-DD`, horas `HH:MM` en la **hora local del lugar de la actividad** (cada
  respuesta trae su `timezone` y `starts_at_utc`).
- Incluida en los planes **«Motor de reservas»** y **«Pro»**.
- Avisos automáticos a tu servidor (webhooks): [webhooks.md](webhooks.md). Ejemplos para comprobar la firma en
  [ejemplos/](ejemplos/).

## 1. Claves

Panel del centro → **Vender en tu web → Claves de la API → Crear clave**. Cada clave:

- es de **solo lectura** (servicios, disponibilidad, reservas) o de **lectura y escritura** (además, crear y cancelar);
- se enseña **una sola vez** al crearla (`wdk_…`): guárdala en tu servidor, nunca en el navegador ni en una app;
- se puede **revocar** en cualquier momento (deja de funcionar al instante). Hasta 10 claves por centro.

Envíala en cada petición:

```
Authorization: Bearer wdk_tu_clave
```

(o en la cabecera `X-WORLDIVES-API-Key`). Una clave solo ve lo de **su** centro: nunca servicios, reservas ni clientes
de otro.

## 2. Límites

| Límite | Valor | Si se pasa |
|---|---|---|
| Peticiones por clave | 120 por minuto | `429 rate_limited` con `Retry-After: 60` |
| Reservas creadas por clave | 300 por hora | `429 rate_limited` con `Retry-After: 300` |

## 3. Errores

Siempre con el mismo formato y un código estable:

```json
{"error": {"code": "no_spots", "message": "Sin plazas: ya no quedan plazas libres para esa fecha."}}
```

| HTTP | `code` | Cuándo |
|---|---|---|
| 400 | `invalid_json`, `missing_service_id`, `invalid_date`, `invalid_range`, `invalid_channel`, `invalid_limit` | Petición mal formada |
| 401 | `invalid_key` | Falta la clave, no es válida o está revocada |
| 403 | `read_only_key` | Clave de solo lectura intentando crear o cancelar |
| 403 | `plan_required` | El plan del centro no incluye la API, o el centro no acepta reservas online |
| 404 | `not_found` | Servicio, reserva o ruta que no existe (o que es de otro centro) |
| 409 | `no_spots` | No quedan plazas suficientes |
| 409 | `not_cancellable` | La reserva ya no se puede cancelar |
| 415 | `unsupported_media_type` | Falta `Content-Type: application/json` |
| 422 | `invalid_request` (u otro más concreto) | Algún dato no es válido; `message` dice cuál |
| 429 | `rate_limited` | Límite superado (mira `Retry-After`) |
| 503 | `busy` | Servidor ocupado un instante: repite la petición |

## 4. Servicios

### `GET /services`

```bash
curl https://worlddivesdiscovery.com/api/v1/services -H "Authorization: Bearer wdk_tu_clave"
```

```json
{"data": [{
  "id": 41, "title": "Inmersión guiada en la Granadella", "type": "inmersion", "description": "…",
  "unit": "slot", "booking_mode": "request", "bookable": true,
  "price": 45.0, "price_per": "person", "currency": "EUR", "duration_minutes": 120, "max_participants": 6,
  "timezone": "Europe/Madrid", "pay_way": "online", "insurance_required": "online"
}]}
```

- `unit`: `slot` (por salida), `day` (por días) o `half_day` (por días o medias jornadas).
- `booking_mode`: `payment` (se paga al reservar) o `request` (bajo petición: el centro acepta).
- `insurance_required`: `no`, `center` (se comprueba en el centro) u `online` (obligatorio para reservar online). Ver
  el punto 7.

`GET /services/{id}` devuelve `{"service": {…}}`.

### `GET /availability?service_id=41&from=2026-11-01&to=2026-11-30`

Plazas libres en tiempo real (máximo 92 días por petición; sin `from`, desde hoy; sin `to`, 31 días).

```json
{"service_id": 41, "unit": "slot", "timezone": "Europe/Madrid",
 "departures": [{"id": 912, "date": "2026-11-14", "time": "10:00", "spots_total": 6, "spots_free": 4,
                 "starts_at_utc": "2026-11-14T09:00:00Z"}]}
```

Para servicios por días: `{"unit": "day", "days": [{"date": "2026-11-14", "state": "free"}]}` con `state` = `free`,
`am` (solo la mañana libre), `pm` (solo la tarde) o `busy`.

## 5. Reservas

### `GET /bookings`

Filtros: `from`, `to` (fecha de la actividad), `status`, `channel` (`worldives`, `widget`, `link`, `api`, `manual`,
`import`), `limit` (1–100, por defecto 25) y `starting_after` (el `id` de la última que tienes) para pasar de página.
Devuelve `{"data": [ … ], "has_more": true}`, de la más nueva a la más antigua. Las reservas con el pago sin terminar no
salen.

`GET /bookings/{id}` devuelve `{"booking": {…}}`.

### El objeto reserva

```json
{
  "id": 1323, "ref": "WOD-001323", "status": "confirmed", "channel": "api", "origin": null,
  "service": {"id": 41, "title": "Inmersión guiada en la Granadella"}, "slot_id": 912,
  "date": "2026-11-14", "time": "10:00", "date_to": "2026-11-14", "days": null,
  "timezone": "Europe/Madrid", "starts_at_utc": "2026-11-14T09:00:00Z",
  "participants": 2, "price": 90.0, "currency": "EUR", "payment_status": "paid", "booking_mode": "payment",
  "external_ref": "PEDIDO-7781",
  "customer": {"name": "Marta Pérez", "email": "marta@example.org", "phone": "+34600000000"},
  "insurance": {"required": "online", "status": "ok", "valid_to": "2030-12-31", "insurer": "Aseguradora Demo A"},
  "created_at": "2026-10-15T10:21:04+00:00", "updated_at": "2026-10-15T10:21:09+00:00"
}
```

`status`: `requested` (pendiente de que el centro responda), `accepted_pending_payment`, `payment_in_progress`,
`insurance_pending` (espera el seguro del cliente, punto 7), `confirmed`, `completed`, `rejected`, `cancelled`,
`expired`.

### `POST /bookings` (clave de lectura y escritura)

```bash
curl https://worlddivesdiscovery.com/api/v1/bookings \
  -H "Authorization: Bearer wdk_tu_clave" -H "Content-Type: application/json" \
  -H "Idempotency-Key: pedido-7781" \
  -d '{"service_id": 41, "departure_id": 912, "participants": 2, "external_ref": "PEDIDO-7781",
       "customer": {"name": "Marta Pérez", "email": "marta@example.org", "phone": "+34600000000", "language": "es"},
       "insurance": {"insurer": "Aseguradora Demo A", "valid_to": "2030-12-31"},
       "insurance_participants": [{"name": "Luis Pérez", "insurer": "Aseguradora Demo B", "valid_to": "2027-06-30"}]}'
```

| Campo | |
|---|---|
| `service_id` | Obligatorio |
| `departure_id` | La salida (de `/availability`), en servicios por salida. O bien `date` + `time` |
| `days`, `part` | En servicios por días: la lista de fechas y `full`, `am` o `pm` |
| `participants` | Número de personas |
| `customer` | `name`, `email` (te mandamos ahí la confirmación), `phone`, `language` (`es`, `en`, `fr`, `de`, `it`, `pt`, `pl`, `nl`, `zh`) |
| `extras`, `equipment` | Ids de extras y códigos de equipo del centro (opcional) |
| `notes`, `external_ref` | Notas y tu propia referencia (opcional) |
| `insurance`, `insurance_participants` | Seguro de buceo (punto 7, opcional) |

Respuesta `201`:

```json
{"booking": {…}, "payment_required": true, "booking_url": "https://worlddivesdiscovery.com/mi-reserva/1323.…",
 "checkout_url": "https://checkout.stripe.com/…", "hold_expires_at": "2026-10-15T12:31:04"}
```

- **Idempotencia.** Con la misma `Idempotency-Key` (por ejemplo, el número de tu pedido) una petición repetida no crea
  otra reserva: devuelve la primera con `"duplicate": true` y `200`. Úsala siempre que reintentes.
- **Pago al reservar** (`payment_required: true`): manda al cliente a `checkout_url`. Las plazas se guardan hasta
  `hold_expires_at`; si no paga, la reserva caduca y las plazas vuelven.
- **Bajo petición**: queda `requested` hasta que el centro acepta en el panel.
- `booking_url`: la página de la reserva del cliente (verla, pagar, cancelar). Sin cuenta de WORLDIVES.

### `POST /bookings/{id}/cancel`

```bash
curl -X POST https://worlddivesdiscovery.com/api/v1/bookings/1323/cancel \
  -H "Authorization: Bearer wdk_tu_clave" -H "Content-Type: application/json" \
  -d '{"reason": "El cliente no puede venir", "refund_amount": 90}'
```

Una solicitud se rechaza; una reserva confirmada se cancela con la política del centro (la devolución sale de la cuenta
de Stripe del centro; `refund_amount` es opcional). Devuelve `{"booking": {…}, "refund": "…"}`.

## 6. Calendarios iCal

- **Exportar**: Vender en tu web → «6 · Calendario (iCal)» → «Crear mi enlace de calendario». Un `.ics` con las reservas de todos los
  canales para suscribirse desde Google Calendar, Apple u Outlook. El enlace es secreto: si se filtra, créalo de nuevo.
- **Importar**: pega la dirección `https://` o `webcal://` de otro calendario (un portal, tu programa anterior, tus
  vacaciones). Sus eventos **bloquean** plazas o días aquí. No es instantáneo: se lee de nuevo cada 15 minutos (lo
  que se vende en WORLDIVES sí cuenta al momento en todos los canales).

## 7. Seguro de buceo

Cada servicio dice en `insurance_required` qué pide:

| Valor | Qué pasa al reservar por la API |
|---|---|
| `no` | Nada. `insurance.status` es `not_required`. |
| `center` | Se reserva siempre. Si mandas `insurance` (`{"insurer", "valid_to"}`) queda `declared`; con `{"at_center": true}`, `at_center`; sin nada, `missing`. El centro lo comprueba el día de la inmersión. |
| `online` | Si mandas `insurance` con un `valid_to` que cubre el día (tu sistema lo ha comprobado), la reserva sigue como siempre (`declared`). Si no, queda **`insurance_pending`**: las plazas se guardan 60 minutos, la respuesta trae `"insurance_required": true` y el cliente sube su póliza en `booking_url`; entonces la reserva sigue sola (pago o solicitud). Si no la sube, caduca. |

`insurance_participants` lleva el seguro de los acompañantes (`name`, `insurer`, `valid_to`); sin datos, «lo
presentará en el centro». El objeto reserva trae `insurance` con `required`, `status` (`not_required`, `ok`,
`declared`, `at_center`, `missing`, `expired`) y, si consta, `insurer`, `valid_to` y `deadline`.

WORLDIVES no es aseguradora ni mediador de seguros: la API no vende seguros.

## 8. Conexión antigua (`/api/integrations/bookings`)

La conexión de versiones anteriores sigue funcionando: tu sistema envía reservas que ya tiene y entran con el canal
«Importada». Para lo nuevo, usa la API v1.
