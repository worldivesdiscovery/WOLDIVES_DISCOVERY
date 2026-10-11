# Ficha de revisión: Reglas de los Puntos WORLDIVES

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

## Texto publicado

- Castellano (referencia): `app/legal/es/puntos.md`. Inglés (oficial): `app/legal/en/puntos.md`.
- Ruta pública: `#/legal/puntos`. Forma parte de las condiciones de uso (cláusula 6 de `terminos.md`); no se acepta aparte.
- Marcadores propios: `{{points_grant_month}}` = `POINTS_GRANT_CLIENT_MONTH` y `{{points_code_days}}` = `POINTS_CODE_DAYS` (se rellenan en `legal_fill()`, `app/server.py`).
- Decisión del titular nº 4: el antiguo monedero pasa a puntos 1:1; los puntos no son dinero.

Esta ficha no repite el texto. Resume cada cláusula, indica en qué parte del código se apoya y lista lo que falta revisar.

## Modelo de datos y límites

| Elemento | Dónde | Detalle |
|---|---|---|
| Libro de puntos | Tabla `points_ledger` | Única fuente: saldo = `SUM(points)` (`points_balance()`). Tipos `POINT_KINDS`: `earned`, `granted`, `redeemed`, `reversal`, `migrated`, `adjust`. Solo enteros (`points_add()` hace `int()`) |
| Logros | `reward_events` (uno por usuario y clave, `ensure_reward_event()`) | Se calculan en `sync_user_rewards()`, llamada desde `/api/rewards/seed` y antes de canjear |
| Ventajas | `reward_offers` (centro, coste en puntos, tipo `REWARD_TYPES`, existencias) | Solo las crea un centro (o la administración para un centro): `POST /api/provider/reward-offers`, con el plan que incluya `rewards` (plan Pro, `PLAN_DEFAULTS`) |
| Códigos | `reward_redemptions` (`code` `WOD-XXXXXXXX`, `status` `issued`/`redeemed`/`cancelled`/`expired`, `expires_at`, quién y dónde se validó) | QR en `GET /api/points/codes/<id>/qr.svg` |
| Caducidad del código | `WOD_POINTS_CODE_DAYS` | **180 días** por defecto (7–730) |
| Concesión por centro, por cliente y mes | `WOD_POINTS_GRANT_MAX_PER_CLIENT_MONTH` | **100** por defecto (0–100 000) |
| Concesión por centro, total al mes | `WOD_POINTS_GRANT_MAX_PER_CENTER_MONTH` | **3000** por defecto (0–10 000 000) |
| Interruptor general | `FEATURE_SWITCHES['points']` (`require_switch(db,'points')`) | La administración puede desactivar el programa |

Pruebas (`tests/test_phase3_points.py`): `test_points_are_earned_by_diving`, `test_exchange_and_validation_by_the_centre`, `test_not_enough_points`, `test_cancel_and_expiry_give_points_back`, `test_grants_with_monthly_limit`, `test_no_money_features`, `test_offers_belong_to_a_centre_and_cost_whole_points`, `test_wallet_becomes_points`. Recorrido: `tests/e2e_points_email.py`. Reescritura del texto: `docs/legal/puntos-reescritos.md`.

## Cláusulas

| # | Qué dice | Dónde se apoya en el código |
|---|---|---|
| 1. Cómo se consiguen | Perfil completo, Log Book (1, 5, 10, 25, 50, 100), titulación y seguro, reserva completada, check-in por QR (una vez por centro), concesión del centro con máximo `{{points_grant_month}}` al mes. Enteros. Saldo y movimientos en «Mis puntos». | `sync_user_rewards()`: perfil (teléfono, ciudad y titulación) 50; **cada** entrada del Log Book 10; hitos 50/100/150/300/600/1200; titulación 25 y seguro 25; reserva `completed` 40; check-in (`center_links`) 20 por centro. Concesión: `POST /api/provider/points-grant` (solo rol `center`, plan con `rewards`, cliente con cuenta y con reserva `confirmed`/`completed` o check-in en ese centro; límites por cliente y por centro). «Mis puntos»: `GET /api/points`. |
| 2. Para qué sirven | Ventajas que ofrece y paga cada centro; WORLDIVES no las financia; si el centro no cumple, se devuelven los puntos. | `reward_offers` siempre ligadas a `center_id`. Canje `POST /api/rewards/redeem`. **No hay herramienta** para devolver puntos por incumplimiento (ver desajustes). |
| 3. Códigos | Código con QR; el centro lo valida una vez; vale `{{points_code_days}}` días; anularlo o dejarlo caducar devuelve los puntos. | Validación `POST /api/center/redemptions/validate` (solo el centro de la ventaja; `status` pasa a `redeemed` una vez). Anulación `POST /api/points/codes/cancel` (`reversal`). Caducidad `run_points_jobs()` en `MAINTENANCE_JOBS` (`reversal` y devuelve existencias). |
| 4. Lo que no se puede hacer | Comprar, recargar, regalar por dinero, transferir, cambiar por dinero, pagar reservas online; datos falsos → anulación. | No existen rutas de recarga, transferencia, retirada ni monedero (`test_no_money_features`: `/api/points/topup`, `/transfer`, `/withdraw`, `/api/wallet` → 404; `/api/provider/wallet-grant` → 410). El cobro de Stripe (`create_stripe_checkout()`) no usa puntos. No hay herramienta de anulación por fraude (ver desajustes). |
| 5. Del monedero a los puntos | 1 € = 1 punto, redondeo hacia arriba; historial conservado. | Migración `50.35` en `app/server.py`: `math.ceil(round(bal, 2))`, tipo `migrated`; `wallet_transactions` se conserva. `test_wallet_becomes_points`. |
| 6. Fin del programa o de la cuenta | Al eliminar la cuenta desaparecen puntos y códigos sin usar. Cierre del programa con 30 días de aviso. | `delete_user_account()`: códigos `issued` → `cancelled` (sin devolver puntos); el libro queda ligado a la cuenta anonimizada. El aviso de 30 días no tiene soporte técnico: es un compromiso de procedimiento. |

## Ventajas que paga el centro y planes

- Solo los centros con el plan que incluye `rewards` (por defecto, Pro) pueden **crear** ventajas y **conceder** puntos (`require_feature(db,user,'rewards')`).
- Si el plan caduca, las ventajas ya publicadas **siguen visibles** (`/api/rewards/offers` no mira el plan), el buceador puede canjearlas y el centro puede **validar** los códigos (la validación no mira el plan). Así no se perjudica al buceador (freemium sin perjuicio).
- Los profesionales freelance no pueden crear ventajas ni conceder puntos (solo rol `center`). El texto habla siempre de «centro»: coincide.
- El coste de cada ventaja lo asume el centro; WORLDIVES no cobra ni paga nada por los canjes.

## Desajustes entre el texto y el código

1. **Límite de concesión.** El texto dice «máximo de `{{points_grant_month}}` puntos al mes **por centro**», pero ese valor es el límite **por cliente** y centro (100). Hay además un límite total por centro (3000) que el texto no menciona. Corregir: «hasta {{points_grant_month}} puntos al mes de cada centro».
2. **Devolución si el centro no cumple.** El texto promete devolver los puntos. Existe el tipo `adjust`, pero **no hay ninguna ruta** de administración que lo use. Hoy solo se podría hacer en la base de datos. **[PENDIENTE TITULAR]**: crear «Ajustar puntos» en *Administración* con motivo y registro.
3. **Anulación por datos falsos.** Igual: no hay herramienta para anular puntos ni para suspender la cuenta (ver `docs/legal/condiciones-buceadores.md`, desajuste 1).
4. **Log Book sin límite.** Cada entrada del Log Book da 10 puntos, sin tope diario ni comprobación, y **borrar la entrada no resta los puntos** (`/api/logbook/delete` no toca el libro; `ensure_reward_event()` ya lo concedió). Con eso se pueden conseguir ventajas reales que paga el centro. **[PENDIENTE TITULAR]**: tope por día o por mes, o restar al borrar.
5. **Programa desactivado.** Si la administración apaga `points`, quedan bloqueadas la anulación y la validación de códigos ya emitidos (`require_switch`), aunque la caducidad sigue devolviendo puntos. El texto promete 30 días de aviso: hay que dejar activa la validación durante ese plazo o avisar antes de apagar.
6. **Reserva completada.** Los puntos se dan con el estado `completed`, que pone el centro. Si el centro no marca la reserva como completada, el buceador no los recibe. El texto no lo explica.
7. Sin desajuste en: enteros, caducidad y devolución, código de un solo uso, sin dinero ni transferencias, conversión 1:1 con redondeo hacia arriba.

## Puntos para el abogado

- **[PENDIENTE ABOGADO]** Confirmar que los puntos no son dinero electrónico ni medio de pago (Ley 21/2011; exclusión de redes limitadas del art. 3.k de la Directiva (UE) 2015/2366) y que el programa no necesita autorización.
- **[PENDIENTE ABOGADO]** Pérdida de los puntos al eliminar la cuenta y al cerrar el programa con 30 días de aviso: validez frente a consumidores (cláusulas abusivas, art. 85 TRLGDCU).
- **[PENDIENTE ABOGADO]** Conversión del monedero: si el saldo en euros antiguo era un crédito exigible del usuario y si convertirlo en puntos necesitaba su consentimiento.
- **[PENDIENTE ABOGADO]** Responsabilidad de WORLDIVES si un centro no cumple la ventaja (el texto solo promete devolver los puntos).
- **[PENDIENTE GESTORÍA]** Tratamiento fiscal de las ventajas que da el centro (descuentos o regalos) y de los puntos concedidos.
