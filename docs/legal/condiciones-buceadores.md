# Ficha de revisión: Condiciones para buceadores

Versión v50.38 · 11/10/2026
Estado: borrador para revisión

## Textos publicados

Son dos documentos:

| Documento | Archivo (castellano, referencia) | Inglés (oficial) | Ruta pública | Aceptación |
|---|---|---|---|---|
| Condiciones de uso para buceadores | `app/legal/es/terminos.md` | `app/legal/en/terminos.md` | `#/legal/condiciones-buceadores` | Todos los usuarios (`LEGAL_ACCEPTANCE['terminos'] = 'all'`) |
| Condiciones de reserva, pago y cancelación | `app/legal/es/reservas.md` | `app/legal/en/reservas.md` | `#/legal/condiciones-reserva` | No se acepta aparte: se enlaza en el registro y antes de reservar |

- Se aceptan al registrarse (casilla obligatoria en `#/registro`, que incluye «Soy mayor de 18 años») y se guardan en `legal_acceptances` (documento, versión, fecha, IP seudonimizada).
- Si se publica una versión nueva, el usuario debe aceptarla al entrar (`legal_pending_for()`, `POST /api/legal/accept`) y recibe un email (`notify_legal_change()`, plantilla `legal_update`). Prueba: `test_new_version_must_be_accepted_again`.
- Historial público de versiones: `/api/legal/history` y `/api/legal/version`.

## Condiciones de uso (`terminos.md`)

| # | Qué dice | Dónde se apoya en el código |
|---|---|---|
| 1. Qué es | Mercado en línea. El contrato de la actividad es entre el buceador y el centro, que responde de ella. Si el centro cobra online, se paga directamente al centro por su cuenta de Stripe; WORLDIVES no recibe el dinero ni cobra comisión. Cada ficha dice quién ofrece la actividad. | Cargos directos con `stripe_account` (`app/server.py`, creación de Checkout, `stripe_kw()`); sin `application_fee_amount`. Pruebas `test_direct_charge_without_commission`, `test_every_stripe_call_carries_the_account`. «Prestado por…» en reserva, justificante y experiencias (`test_experience_shows_provider_and_policy`). Solo se publican centros verificados (`public_center_sql()`, `test_only_verified_centres_are_public`). |
| 2. Tu cuenta | Mayor de 18 años; menores con un adulto. Datos ciertos. Contraseña y verificación en dos pasos opcional. Descargar datos y eliminar la cuenta desde «Mi cuenta». | Casilla «Soy mayor de 18 años» en el registro (`world-dives-v8.js`, `#register-form`): es una declaración, no se comprueba la edad. TOTP: `/api/account/totp/*`, `test_optional_totp_for_a_diver`. Exportación: `/api/account/export?format=zip` (`export_user_zip()`), `test_zip_export_with_documents`. Baja: `/api/account/delete` + confirmación por email (`request_account_deletion()`, `/api/account/delete/confirm`, `delete_user_account()`), `test_deletion_is_confirmed_by_email`, `test_deletion_cascades`. |
| 3. Uso correcto | Prohibiciones (información falsa, reseñas no auténticas, acceso a datos ajenos, extracción automatizada…). Podemos retirar contenidos y suspender o cerrar cuentas, explicando el motivo. | Retirada de contenidos: `/api/admin/reports/resolve`, `/api/admin/reviews/<id>/moderate` (motivo obligatorio y aviso al autor). Límites de peticiones (`app/wod/security.py`). **No hay** herramienta para suspender o cerrar una cuenta (ver desajustes). |
| 4. Contenidos de los usuarios | Reseñas, fotos y sugerencias propias y verdaderas; licencia gratuita y no exclusiva; botón «Denunciar». | Reseñas: `/api/centers/<id>/reviews`. Sugerencias de posición: `point_position_suggestions`. Denuncias: `/api/reports`. |
| 5. Avisos de los centros | No es red social. Los centros solo envían avisos ligados a reservas, por email y a «Avisos», con su teléfono y email; no se contesta por la plataforma. | Ruta de avisos con `booking_id` obligatorio (corrección G11, `test_g11_no_free_messaging`). Tabla `messages`. |
| 6. Puntos | Se ganan, se canjean por ventajas de cada centro, no son dinero. | Ver `docs/legal/reglas-puntos.md`. |
| 7. Precios y ordenación | Precio final con impuestos, fijado por el centro. Remite a `#/legal/clasificacion`. Nadie paga por subir; lo pagado lleva «Patrocinado». | `DIRECTORY_SORT_KEYS` (`app/server.py`). Etiqueta fija «Patrocinado» y registro del patrocinador (`sponsorships`, `test_sponsored_label_is_fixed_and_sponsor_registered`). El precio con impuestos no se comprueba: lo introduce el centro. |
| 8. Responsabilidad | WORLDIVES responde de la intermediación; el centro de la actividad, seguridad, seguro y titulaciones. No limita los derechos del consumidor. | Seguro de responsabilidad civil del centro con avisos (`run_insurance_alerts()`). |
| 9. Cambios | Aviso por email antes de la entrada en vigor y nueva aceptación. Las reservas hechas se rigen por las condiciones de su momento. Versiones anteriores al final de la página. | `legal_publish()`, `notify_legal_change()`, `legal_pending_for()`, `/api/legal/history`. La política de cancelación se copia en cada reserva (`test_policy_is_copied_into_the_booking`). |
| 10. Reclamaciones y ley | Email; hojas oficiales del centro; Juntas Arbitrales si el centro está adherido. Ley española; juzgados del domicilio del consumidor. | Sin soporte técnico necesario. |

## Condiciones de reserva (`reservas.md`)

| # | Qué dice | Dónde se apoya en el código |
|---|---|---|
| 1. Quién presta | El centro o profesional («Prestado por…»); WORLDIVES gestiona la reserva. | Justificante `GET /api/bookings/<id>/receipt.pdf` (`app/wod/pdf.py`), `test_voucher_names_the_provider_and_is_not_an_invoice`. |
| 2. Modos de reserva | «Pago al reservar»: se confirma al pagar; la plaza se guarda unos minutos. «Bajo petición»: el centro acepta o rechaza en su plazo; se paga después. Emails en cada paso y recordatorios 2 días y 1 día antes. | `app/wod/bookings.py` (estados, `DEFAULT_HOLD_MINUTES = 15`, `DEFAULT_RESPONSE_HOURS = 24`, `DEFAULT_PAYMENT_HOURS = 24`), `run_booking_deadlines()`, `accept_booking()`, `reject_booking()`, `expire_booking()`. Recordatorios `reminder_48h` y `reminder` (`test_reminders_48h_and_24h`). Pruebas `tests/test_phase1b_booking_modes.py`. |
| 3. Precio y pago | Precio final. Stripe con 3D Secure; nadie guarda la tarjeta. Se paga directamente al centro. Señal posible. Pago en el centro si no cobra online. Justificante en PDF. | Checkout de Stripe en la cuenta conectada; solo se guardan `card_brand` y `card_last4` (`payment_orders`). Señal: `test_deposit_then_rest_at_the_desk`. |
| 4. Sin desistimiento | Art. 103.l) TRLGDCU: no hay 14 días; se aplica la política del centro. | `booking_policy()`, `booking_cancel_terms()`. |
| 5. Si cancelas tú | Desde la reserva, con vista previa del importe. 100 % dentro del plazo gratuito; fuera, el porcentaje de la política. La devolución la hace el centro; aviso al buceador y recordatorio al centro. | `POST /api/bookings/<id>/cancel` (con `preview`), `propose_refund()`, `run_refund_reminders()` (72 h). Pruebas `test_diver_cancel_proposes_refund_by_policy`, `test_late_cancel_uses_percentage`. |
| 6. Si cancela o cambia el centro | Si cancela, devuelve el 100 %. Si cambia fecha u hora, aviso por email y opción de cancelar. Rechazo de solicitud sin cargo. | Cancelación del centro: `POST /api/bookings/<id>/status` con `status='cancelled'` y `refund_booking()` (`test_centre_cancel_refunds_everything`). Cambio: plantilla `booking_changed` (`test_booking_change_by_the_provider`). Rechazo: `reject_booking()` devuelve lo cobrado. |
| 7. Requisitos para bucear | Titulación, salud, seguro, indicaciones del guía. **No se suben datos de salud** a WORLDIVES. | `DOCUMENT_TYPES` sin certificado médico y bloqueo de palabras médicas (`MEDICAL_WORDS`), `test_g6_no_medical_certificates`. |
| 8. Reclamaciones | Email con el número WOD-…; mediación con el centro; hojas oficiales. | Incidencias de pago marcadas por la administración (`/api/admin/payments/incident`), sin mover dinero. |

## Desajustes entre el texto y el código

1. **Suspensión y cierre de cuentas (condiciones de uso, cláusula 3).** El texto dice que podemos suspender o cerrar cuentas y explicar el motivo. En el código no existe esa función: la administración solo puede cambiar el rol (`/api/admin/users/role`) y moderar contenidos. Hace falta una herramienta de suspensión con motivo y aviso, o quitar la frase. **[PENDIENTE TITULAR]**
2. **Cancelación por el centro (reservas, cláusula 6).** El texto dice que el centro devuelve el 100 %. El código propone el 100 % por defecto, pero deja al centro poner un importe menor (`refund_amount` en el cambio de estado a `cancelled`). Conviene limitarlo en el servidor o explicar en el texto qué pasa si el centro devuelve menos. **[PENDIENTE ABOGADO]**
3. **Edad.** El texto exige 18 años; el código se basa en la casilla del registro y no pide fecha de nacimiento. Es habitual, pero conviene que el abogado lo confirme.
4. **Traducción inglesa de las condiciones para centros** (no de estas): antes decía que el cliente recibía la devolución «automáticamente». Se corrigió en v50.38 al revisar `centros.md`.

## Puntos para el abogado

- **[PENDIENTE ABOGADO]** Calificación de WORLDIVES como intermediario y no como organizador: confirmar que el texto lo deja claro y que no hay «servicios de viaje vinculados» (Directiva (UE) 2015/2302). WORLDIVES no combina servicios de varios proveedores (decisión del titular nº 5).
- **[PENDIENTE ABOGADO]** Art. 103.l) TRLGDCU: confirmar que la excepción al desistimiento cubre cursos de varios días y viajes, y cómo se informa antes de pagar.
- **[PENDIENTE ABOGADO]** Ley aplicable y jurisdicción para buceadores de fuera de España (Reglamento Roma I, art. 6) y para actividades prestadas fuera de España.
- **[PENDIENTE ABOGADO]** Responsabilidad de WORLDIVES por la información orientativa de los puntos de buceo y por los centros verificados.
- **[PENDIENTE ABOGADO]** Señal y cancelaciones: validez de una política con 0 % de devolución fuera de plazo y límites de la cláusula penal en contratos de consumo.
- **[PENDIENTE ABOGADO]** Menores: cómo acepta el adulto las condiciones del centro en nombre del menor.
