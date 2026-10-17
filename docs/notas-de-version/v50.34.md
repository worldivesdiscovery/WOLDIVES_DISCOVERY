# WORLDIVES DISCOVERY v50.34: pagos alineados con las decisiones (Fase 2)

**WORLDIVES ya no cobra comisión por las reservas** y el dinero ya no pasa por la plataforma: cada cobro es un **cargo directo** en la cuenta de Stripe del centro o del profesional freelance.

## 1. Sin comisión
- Eliminados `WOD_PLATFORM_FEE_PERCENT`, `application_fee_amount`, `transfer_data`, el KPI «comisión WORLDIVES», el campo «Comisión por reserva (%)» de los datos legales y los textos del README y de las condiciones.
- Los pedidos antiguos conservan su `platform_fee` como historial (`charge_type='destination'`) y, si se devuelven, se hace como se cobraron (revirtiendo la transferencia).

## 2. Cargos directos y cuentas conectadas
- El Checkout se crea **en la cuenta del prestador** (`stripe_account=…`). Todas las consultas, caducidades y devoluciones llevan la misma cuenta (función única `stripe_kw`).
- Alta de cuentas con **propiedades de controlador** (Accounts v1): panel completo de Stripe para el centro, comisiones de Stripe a cargo de su cuenta, Stripe responsable de los saldos negativos, el centro gestiona devoluciones y disputas. Solo se pide la capacidad `card_payments`. Todo configurable con `WOD_STRIPE_DASHBOARD`, `WOD_STRIPE_FEES_PAYER`, `WOD_STRIPE_LOSSES`, `WOD_STRIPE_CAPABILITIES`.
- **Aviso (Accounts v2):** se ha usado v1 con propiedades de controlador, que es equivalente y estable con Checkout, Account Links y cargos directos. Accounts v2 sigue en fase de vista previa para plataformas Connect; cuando Stripe la publique como estable, el cambio afecta solo al alta (`/api/payments/connect/onboard`).
- «Abrir mi panel de Stripe» lleva a `dashboard.stripe.com` (las cuentas con panel completo no usan enlaces de acceso).
- **Cuenta Express de prueba:** en la base entregada no hay ninguna. Si el titular tiene una en su entorno de pruebas, no se puede convertir: el administrador la desvincula (`POST /api/payments/connect/unlink`) y el centro conecta una nueva.

## 3. Webhook de Connect
- Nuevo endpoint `POST /api/payments/webhook/connect` con su propio secreto `STRIPE_CONNECT_WEBHOOK_SECRET`. Procesa `event.account`; un evento de una cuenta **nunca** toca un pago de otra cuenta.
- Idempotencia por id de evento (tabla `stripe_webhook_events`), igual que el webhook de la plataforma. Los dos comparten una sola función (`handle_stripe_event`).
- Eventos nuevos: `refund.created/updated`, `charge.refunded` (también parciales), `charge.dispute.created/closed`, `account.application.deauthorized`.

## 4. Devoluciones
- **Las hace el prestador**: botón «Devolver» en la reserva y en el listado (total o parcial), con `Refund.create` en su cuenta. También las que haga en su panel de Stripe llegan por webhook. Todo queda en el historial `payment_refunds`.
- **Una devolución parcial no cancela la reserva.**
- **El buceador cancela una reserva pagada:** se calcula lo que corresponde según la política y se **propone** al prestador («Devoluciones pendientes» en su panel y email). Si a las 72 h no la ha hecho, se le recuerda una vez. El buceador ve «Devolución pendiente».
- **El prestador cancela:** se devuelve todo lo pagado (puede indicar otro importe; se le recuerda lo que corresponde).
- **El administrador** solo ve pagos y devoluciones, los ingresos de los prestadores por moneda y marca incidencias (devolución pendiente, disputa, queja). Un pago con importe distinto ya no lo devuelve la plataforma: se pide la devolución al prestador.

## 5. Señal
- Por servicio: cobrar el total o una señal (porcentaje del total o importe por persona). Vale para «Pago al reservar» y para el pago tras aceptar en «Bajo petición».
- La reserva guarda lo pagado (`amount_paid`), lo pendiente (`amount_due`) y la señal. El resto se registra con «Cobrar el resto» (el cobro en mostrador de siempre). Estado de pago nuevo: `deposit_paid` («Señal pagada»).

## 6. Política de cancelación
- Por prestador y, si se quiere, **por servicio**: «gratis hasta X horas antes; después se devuelve Y %». Las tres políticas de siempre (flexible, moderada, estricta) son atajos.
- La política que se ve antes de pagar **se copia en la reserva**: cambiarla después no afecta a reservas hechas.
- Se muestra en la página de reserva, en la reserva, en los correos y en el justificante.

## 7. Experiencias y freelance sin centro
- Experiencias: precio × participantes (ya desde v50.32).
- **Freelance sin centro**: cuenta de Stripe propia (mismas propiedades), alta desde su panel («Cobros y pagos»), comprobación de cobros (`payee_ready`). Sus servicios se reservan desde su ficha de profesional («Reservar y pagar» / «Enviar solicitud») y sus experiencias se pagan online igual que las de un centro.
- Las reservas ya no exigen un centro: `bookings.center_id` es opcional y `bookings.provider_user_id` dice quién presta el servicio. Panel del freelance con «Reservas» (aceptar, rechazar, cancelar, devolver, avisos) y «Cobros y pagos».
- En el justificante, el prestador es el freelance con sus datos fiscales.

## 8. Justificante
- Título **«Justificante de reserva»**, **«Prestador del servicio»** con razón social, NIF y dirección (nueva sección «Datos del prestador» en «Cobros y pagos»), **«WORLDIVES DISCOVERY: plataforma de reservas»** y **«Este documento no es una factura»**.
- Importe con «Precio final fijado por el centro, impuestos incluidos», señal pagada, resto en el centro, devoluciones y política de cancelación.
- **Todos los idiomas se imprimen bien**: nuevo motor PDF (`app/wod/pdf.py`) con Noto Sans y Noto Sans SC incrustadas (OFL), mapa ToUnicode (texto buscable y copiable). La ficha del buceador usa el mismo motor. Se ha retirado el motor antiguo (Helvetica, solo Europa occidental).
- KPI «Facturación» → **«Ingresos»**.

## 9. Precios e impuestos
- Texto «Precio final fijado por el centro, impuestos incluidos» en la reserva y el justificante.
- KPIs **agrupados por moneda** (centro, freelance y administrador); nunca se suman monedas distintas.

## 10. Patrocinio
- Etiqueta **«Patrocinado»** fija y no editable en las ofertas destacadas y en la banda de patrocinadores.
- **Registro de patrocinios** (`sponsorships`): quién patrocina, contacto, fechas, importe y notas. Una oferta no se puede guardar sin indicar el patrocinador. El registro se conserva aunque se borre la publicación.

## Migración `migrate_v50_34`
- **Copia de seguridad previa** de la base (`data/backups/…-antes-v50_34-….sqlite3`, o `WOD_BACKUP_DIR`) cuando hay reservas, porque se reconstruye la tabla `bookings` (procedimiento oficial de SQLite, con índices y disparadores). Registro en la nueva tabla `schema_migrations`.
- Columnas nuevas en reservas, pedidos, servicios, centros y usuarios; tablas `payment_refunds` y `sponsorships`. Las devoluciones antiguas pasan al historial. Nada se borra.

## Cómo se probó
- `tests/test_phase2_payments.py`: 22 pruebas (cargo directo sin comisión, cuenta en todas las llamadas, webhook de Connect idempotente y aislado por cuenta, secretos separados, alta con propiedades de controlador, devoluciones parciales/totales y permisos, propuesta y recordatorio, porcentaje fuera de plazo, copia de la política, cancelación del centro, señal y resto, freelance completo, devoluciones hechas en Stripe, disputas, admin sin comisión, textos legales, KPIs por moneda, justificante, patrocinio, migración con copia).
- `tests/e2e_payments.py`: 26/26 comprobaciones en navegador (centro, buceador en móvil, freelance y administrador). Capturas en `docs/capturas/fase-2/`.
- Todas las pruebas anteriores siguen pasando (79 en total) y `e2e_walk.py` y `e2e_booking_modes.py` sin errores.

## Pendiente de decisión del titular
- Si el centro **no** hace una devolución propuesta, ¿qué hace WORLDIVES además del recordatorio y la incidencia (por ejemplo, suspender los cobros online del centro)?
- La señal fija se ha definido **por persona**. Confirmar si se prefiere por reserva.

## Para abogado / gestoría
- Revisar las nuevas cláusulas de cuota, cobros directos, devoluciones y disputas en «Condiciones para centros» y «Condiciones de reserva».
- Confirmar que el justificante (no factura) es suficiente para el buceador y qué datos fiscales mínimos debe mostrar el prestador.
- Al cambiar las condiciones para centros, los centros deben volver a aceptarlas (se hará con el sistema de versiones de la Fase 5, con aviso de 15 días).
