# Permisos por papel · quién puede leer y cambiar qué

Referencia: OWASP ASVS 5.0, V8 (autorización). Las reglas viven en el servidor; la web y la app solo esconden lo que
el servidor ya niega. El aislamiento entre centros (un centro nunca ve ni toca nada de otro) está en
[`aislamiento-centros.md`](aislamiento-centros.md); aquí se describe lo que cada papel hace **dentro** de lo suyo.
`tests/test_v50_51_asvs.py` (clase `PermisosDelEquipo` y `test_permissions_doc_matches_the_rules`) comprueba que este
documento y `app/wod/roles.py` dicen lo mismo.

## Papeles

| Papel | Quién | Ve | Cambia |
|---|---|---|---|
| Visitante | Sin sesión | Lo público: mapa, puntos, centros, servicios, salidas, precios, reseñas | Nada (puede registrarse, pedir información, denunciar y escribir a contacto) |
| Buceador | Cuenta personal | Lo público y lo suyo: reservas, puntos, Log Book, documentos, avisos | Lo suyo; reserva y paga; nunca datos de otros |
| Centro (propietario) | Titular del centro | Todo lo del centro | Todo lo del centro |
| Equipo del centro | Personas invitadas por el propietario con un perfil | Según los permisos del perfil (abajo) | Según los permisos del perfil |
| Freelance | Profesional independiente | Todo lo suyo (como un centro de una persona) | Todo lo suyo |
| Administración | Cuentas de la plataforma, con verificación en dos pasos | Todo, dejando motivo y registro para los datos de un centro | Revisión de centros, contenidos, usuarios; nunca cobra ni mueve dinero de un centro |

## Permisos del equipo

Cada centro da a cada perfil los permisos que quiera (*Equipo → Perfiles*). Por defecto: **Encargado** todos;
**Recepción** `checkin`, `todas_salidas`, `barco`, `reservas`, `salidas` y `estadisticas`; **Instructor** solo
`checkin`.

| Permiso | Nombre en la web | Permite |
|---|---|---|
| `checkin` | Pasar lista y escanear QR | Marcar llegadas, escanear QR, firmas a bordo y contar a bordo |
| `todas_salidas` | Ver todas las salidas | Sin él, solo las salidas en las que guía un grupo y las que aún no tienen guías: en la agenda, el manifiesto, la hoja del día y el resumen del barco |
| `barco` | Organizar barcos y grupos | Barcos, grupos y guías de cada salida |
| `reservas` | Reservas, solicitudes y clientes | Aceptar o rechazar solicitudes, crear y cambiar reservas, cobrar en el centro y escribir a los clientes. **Leer** las solicitudes, los clientes, las solicitudes de información, las exportaciones de reservas y clientes, las notas internas de las reservas y lo pagado en cada reserva (para cobrar el resto) |
| `salidas` | Salidas y servicios | Crear, cambiar y cerrar salidas y servicios |
| `avisos` | Cancelar salidas y avisar a todos | Cancelar o cambiar una salida y avisar a todos sus buceadores; WhatsApp |
| `cobros` | Cobros y devoluciones | Ver los cobros del centro (listado, ingresos, recibos), exportar los pagos y devolver dinero; también lo pagado en cada reserva |
| `centro` | Ficha del centro y ajustes | Ficha pública, fotos, tarifas, seguro, política de cancelación, descargo, integraciones, calendario e importar clientes |
| `estadisticas` | Estadísticas | Estadísticas del centro |

**Solo el propietario:** el equipo y sus perfiles, la cuenta de Stripe y los datos de cobro, los datos fiscales, el
plan, el registro de actividad y cerrar la cuenta del centro.

## Rutas del panel que piden un permiso

Primera regla que coincide; las demás rutas de lectura del panel están abiertas a todo el equipo del centro (con los
filtros por dato de abajo) y las de escritura piden `reservas`.

| Lectura (GET) | Permiso |
|---|---|
| `/api/provider/fiscal`, `/api/provider/plan`, `/api/center/team`, `/api/center/activity`, `/api/provider/cuenta` | Solo el propietario |
| `/api/provider/payments`, `/api/payments/center` | `cobros` |
| `/api/center/requests`, `/api/center/clients`, `/api/center/info-requests` | `reservas` |
| `/api/provider/ical` | `centro` |
| `/api/provider/stats`, `/api/center/analytics` | `estadisticas` |

| Escritura (POST) | Permiso |
|---|---|
| `/api/payments/connect/`, `/api/provider/payment-profile`, `/api/provider/fiscal`, `/api/provider/plan`, `/api/center/team`, `/api/provider/cuenta/` | Solo el propietario |
| `/api/auth/`, `/api/account/`, `/api/legal/accept`, `/api/reports`, `/api/contact`, `/api/me`, `/api/team/`, `/api/app/push/` | Cualquiera (su propia cuenta) |
| `/api/manifest/sync`, `/api/pro/escanear`, `/api/pro/contar`, firma del descargo a bordo | `checkin` |
| `/api/provider-services/slot-cancel`, `/api/avisos/`, `/api/whatsapp/` | `avisos` |
| `/api/manifest/` (el resto) | `barco` |
| `/api/bookings/refund`, `/api/bookings/<id>/refund` | `cobros` |
| `/api/provider/insurance`, `/api/provider/cancellation-policy`, `/api/center/cancellation-policy`, `/api/center/profile`, `/api/provider/profile`, `/api/provider/avatar`, `/api/provider/center-update`, `/api/provider/center-showcase`, `/api/provider/center-cover`, `/api/provider/center-gallery`, `/api/center/integration`, `/api/provider/ical`, `/api/center/import`, `/api/center/tariffs`, `/api/provider/waiver`, `/api/marina/` | `centro` |
| `/api/provider-services`, `/api/service-templates/`, `/api/agenda/` | `salidas` |
| Todo lo demás del panel | `reservas` |

## Datos sensibles: quién los lee y los cambia

| Dato | Buceador (lo suyo) | Equipo del centro | Administración |
|---|---|---|---|
| Teléfono y email del cliente | Sí | Con `reservas` en Clientes y exportaciones; en la reserva y el manifiesto mientras la reserva esté viva o el buceador haya compartido su ficha. Cada vista queda registrada | Con motivo |
| Contacto de emergencia, nivel, seguro, documentos | Sí | Solo con reserva viva o ficha compartida; el manifiesto, con `todas_salidas` o en las salidas que guía | Con motivo |
| Importes pagados, pendientes y devueltos de una reserva, forma de pago, justificante PDF | Sí | Con `cobros` o `reservas` (cobrar en el centro) | Sí (sin datos de tarjeta: los guarda Stripe) |
| Listado de cobros, ingresos y exportación de pagos | — | Solo con `cobros` | Sí |
| Notas internas de la reserva | Nunca | Solo con `reservas` | Con motivo |
| Datos fiscales del centro | — | Solo el propietario | Sí |
| Datos de tarjeta | Nunca los guarda WORLDIVES (Stripe) | Nunca | Nunca |

**Según el estado.** El centro ve la ficha completa del buceador (perfil, documentos, emergencia) solo mientras tenga
una reserva viva con él o el buceador la haya compartido (por ejemplo, haciendo check-in con su QR); después solo ve los
datos de la reserva. Una reserva cancelada, rechazada o caducada no se puede cobrar ni aceptar. La administración que
abre datos de un centro deja un motivo, que queda en el registro de actividad.
