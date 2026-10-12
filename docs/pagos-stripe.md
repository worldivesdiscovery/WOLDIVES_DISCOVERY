# Pagos con Stripe Connect

**WORLDIVES no cobra comisión por las reservas.** Su único ingreso es la cuota del plan anual de los centros. Los cobros online son **cargos directos**: el Checkout se crea en la cuenta de Stripe del centro (o del profesional freelance sin centro) con `stripe_account=…`, sin `application_fee_amount` ni `transfer_data`. El dinero va del buceador al prestador y nunca pasa por un saldo de WORLDIVES.

### Variables de servidor

Solo en el entorno del servidor (nunca en JavaScript, en el repositorio ni dentro del ZIP). Ver `.env.example`.

```text
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...           # endpoint de la plataforma
STRIPE_CONNECT_WEBHOOK_SECRET=whsec_...   # endpoint de Connect (eventos de las cuentas de los centros)
WOD_PUBLIC_URL=https://tu-dominio.example
# Configuración de las cuentas conectadas (valores por defecto = decisión del titular):
WOD_STRIPE_DASHBOARD=full        # panel completo de Stripe para el centro
WOD_STRIPE_FEES_PAYER=account    # las comisiones de Stripe las paga la cuenta del centro
WOD_STRIPE_LOSSES=stripe         # Stripe responde de los saldos negativos
WOD_STRIPE_CAPABILITIES=card_payments
```

### Alta de un centro o de un freelance

Desde **Cobros y pagos** en su panel. WORLDIVES crea una cuenta conectada con **propiedades de controlador** (Accounts v1: `controller.stripe_dashboard.type=full`, `controller.fees.payer=account`, `controller.losses.payments=stripe`, `requirement_collection=stripe`) y solo la capacidad `card_payments`, y abre el alta alojada por Stripe (Account Link). Se guardan solo el identificador de la cuenta y sus estados. No se puede cobrar online hasta que Stripe indique `charges_enabled` y `payouts_enabled`; `account.updated` los mantiene al día. Con el panel completo, el centro entra en `dashboard.stripe.com` con su propio usuario.

Las cuentas Express de prueba creadas con versiones anteriores no pueden cambiar de tipo: el administrador las desvincula (`POST /api/payments/connect/unlink`) y el centro conecta una nueva.

### Pago de una reserva

- «Pago al reservar»: Checkout al momento (total o **señal**), plazas bloqueadas 15 min, confirmación solo con el pago confirmado por Stripe.
- «Bajo petición»: Checkout cuando el centro acepta, con plazo para pagar.
- Señal: por servicio, porcentaje o importe por persona. La reserva guarda lo pagado (`amount_paid`) y lo pendiente (`amount_due`); el resto se registra con «Registrar cobro».

La reserva solo se considera pagada cuando Stripe lo confirma (webhook firmado, o consulta directa a Stripe al volver del pago). Los eventos se registran por ID para no procesarlos dos veces.

### Devoluciones

Las hace el centro desde su panel (botón «Devolver», total o parcial) con `Refund.create` en su cuenta, o desde su panel de Stripe; ambas llegan al historial `payment_refunds`. Un reembolso parcial no cancela la reserva. Si el buceador cancela una reserva pagada, se propone al centro el importe de su política y se le recuerda a las 72 h. El administrador solo ve pagos y devoluciones y marca incidencias.

### Webhooks

```text
POST https://tu-dominio.example/api/payments/webhook          (cuenta de la plataforma)
POST https://tu-dominio.example/api/payments/webhook/connect  (Connect: «eventos de las cuentas conectadas»)
```

Eventos: `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `checkout.session.expired`, `payment_intent.payment_failed`, `charge.refunded`, `refund.created`, `refund.updated`, `charge.dispute.created`, `charge.dispute.closed`, `account.updated`, `account.application.deauthorized`. En el endpoint de Connect, un evento de una cuenta nunca puede tocar un pago de otra.

### Importante antes de producción

Antes de aceptar dinero real: HTTPS, secretos fuera del repositorio, copias de seguridad, términos y política de cancelación revisados por un abogado y configuración fiscal revisada por la gestoría (ver `docs/legal/`).
