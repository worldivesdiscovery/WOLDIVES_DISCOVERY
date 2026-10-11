# Estados de una reserva

Una sola lista de estados, definida en `app/wod/bookings.py`. En la base se guardan en inglés (como el resto de columnas) y se muestran siempre con su nombre oficial:

| Identificador | Nombre oficial | Significado | ¿Ocupa plazas? | ¿Lo ve el centro? |
|---|---|---|---|---|
| `requested` | solicitada | «Bajo petición»: enviada, sin cobro | No | Sí (Solicitudes pendientes) |
| `accepted_pending_payment` | aceptada_pendiente_pago | El centro aceptó; el buceador paga antes del plazo | Sí | Sí |
| `payment_in_progress` | pago_en_curso | «Pago al reservar»: el buceador está pagando (15 min) | Sí | Solo en gris en el planning |
| `confirmed` | confirmada | La plaza es del buceador | Sí | Sí |
| `rejected` | rechazada | El centro dijo que no | No | Sí |
| `expired` | caducada | Pasó un plazo (sin respuesta, sin pago o pago abandonado) | No | Solo si llegó a ser una reserva |
| `cancelled` | cancelada | Cancelada por el buceador o el centro | No | Sí |
| `completed` | completada | La actividad se hizo | — | Sí |

## Transiciones

```
Pago al reservar:  payment_in_progress --pago Stripe--> confirmed
                   payment_in_progress --abandono / 15 min--> expired (hold_expired, payment_cancelled)
                   (precio 0) → confirmed
Bajo petición:     requested --aceptar + cobro online--> accepted_pending_payment --pago--> confirmed
                   requested --aceptar sin cobro online o gratis--> confirmed (pago en el centro)
                   requested --rechazar--> rejected
                   requested --sin respuesta en plazo--> expired (no_response)
                   accepted_pending_payment --sin pago en plazo--> expired (not_paid)
Ambos:             confirmed / accepted_pending_payment --cancelar--> cancelled
                   confirmed --fecha pasada + completar--> completed
```

El motivo de una caducidad se guarda en `bookings.expired_reason`.
