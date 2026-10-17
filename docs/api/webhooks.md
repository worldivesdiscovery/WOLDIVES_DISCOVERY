# Avisos automáticos (webhooks)

WORLDIVES avisa a **tu servidor** cada vez que cambia una reserva de tu centro, venga del canal que venga (WORLDIVES,
tu web, un enlace, la API, una reserva a mano). Así tu sistema se entera sin tener que preguntar.

Panel del centro → **Vender en tu web → Avisos automáticos (webhooks) → Añadir aviso**: la dirección `https://` de tu
servidor (solo `https` y una dirección pública) y los avisos que quieres. Al crearlo te damos un **secreto**
(`whsk_…`) para comprobar la firma. Hasta 5 direcciones por centro.

## Avisos

| `type` | Cuándo |
|---|---|
| `booking.created` | Entra una reserva o solicitud nueva (las que esperan el pago o el seguro, cuando siguen) |
| `booking.confirmed` | Queda confirmada |
| `booking.paid` | Se cobra (el total o la señal) |
| `booking.cancelled` | Se cancela, se rechaza o caduca (`data.booking.status` dice cuál) |
| `booking.changed` | Cambia la fecha, la hora, la salida o las personas, o pasa a «aceptada, pendiente de pago» o «realizada» |

## Qué llega

Un `POST` con `Content-Type: application/json` y estas cabeceras:

```
X-WORLDIVES-Event: booking.confirmed
X-WORLDIVES-Delivery: 5531
X-WORLDIVES-Signature: t=1792065664,v1=3f0c9b…e41a
```

```json
{"id": "evt_8c1f…", "type": "booking.confirmed", "created": 1792065664,
 "data": {"booking": { …el mismo objeto reserva de la API (README.md, punto 5)… }}}
```

`data.booking.status` es el estado **en el momento del aviso**.

## Comprobar la firma (importante)

Cualquiera puede mandar un `POST` a tu dirección: comprueba siempre que el aviso viene de WORLDIVES.

`X-WORLDIVES-Signature` es `t=<segundos unix>,v1=<firma>`, donde la firma es el **HMAC-SHA256** en hexadecimal, con
tu secreto `whsk_…` como clave, de este texto:

```
<t> + "." + <el cuerpo tal como llega, sin tocarlo>
```

1. Lee el cuerpo **en bruto** (antes de convertirlo a JSON: un espacio de más cambia la firma).
2. Calcula el HMAC y compáralo con `v1` con una comparación de tiempo constante.
3. Rechaza el aviso si `t` se aleja más de **5 minutos** de tu hora (evita que alguien reenvíe un aviso viejo).
4. Usa `id` (o `X-WORLDIVES-Delivery`) para no procesar dos veces el mismo aviso.

Ejemplos listos para copiar: [Python](ejemplos/verificar_firma.py), [Node.js](ejemplos/verificar-firma.js) y
[PHP](ejemplos/verificar-firma.php). Los tres se comprueban con la firma real del servidor
(`tests/test_v50_56_api_docs.py`).

## Respuesta y reintentos

- Responde con un código **2xx** en menos de 10 segundos (guarda el aviso y procésalo después si tardas).
- Si no responde o no es 2xx, se reintenta tras **1 min, 5 min, 30 min, 2 h, 6 h y 24 h**. Después queda «fallido».
- En **Registro de envíos** (en el mismo panel) ves cada aviso, su resultado y los intentos; los fallidos tienen
  «Reintentar».
- Una dirección nueva solo recibe los cambios posteriores a su creación.
