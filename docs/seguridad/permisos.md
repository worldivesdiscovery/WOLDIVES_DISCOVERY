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
| Equipo del centro | Personas invitadas por el propietario con un perfil o enlazadas con su QR personal (v50.58: entran con su propia cuenta y eligen el centro en el selector de perfil; solo mientras dura el enlace) | Según los permisos del perfil (abajo) | Según los permisos del perfil |
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
| `cobros` | Cobros y devoluciones | Ver los cobros del centro (listado, ingresos, recibos), exportar los pagos y devolver dinero; también lo pagado en cada reserva. **Si el centro cobra online, exige la verificación en dos pasos** (v50.52) |
| `centro` | Ficha del centro y ajustes | Ficha pública, fotos, tarifas, seguro, política de cancelación, descargo, integraciones, calendario e importar clientes |
| `estadisticas` | Estadísticas | Estadísticas del centro |

**Solo el propietario:** el equipo y sus perfiles, la cuenta de Stripe y los datos de cobro, los datos fiscales, el
plan, el registro de actividad y cerrar la cuenta del centro.

**Verificación en dos pasos obligatoria con cobros** (v50.52, ASVS V6.3.3): el propietario o freelance con Stripe
Connect conectado o en proceso y los miembros con `cobros` de esos centros solo llegan a «Mi cuenta» hasta activarla
(el propietario o freelance que ya cobraba tiene 14 días). No se puede conectar Stripe sin ella ni desactivarla con
cobros. Detalle en [`autenticacion.md`](autenticacion.md#verificación-en-dos-pasos).

## Rutas del panel que piden un permiso

Primera regla que coincide; las demás rutas de lectura del panel están abiertas a todo el equipo del centro (con los
filtros por dato de abajo) y las de escritura piden `reservas`.

**Lo que un perfil no puede leer no existe para él** (v50.58, encargo del equipo por QR, comprobación 7): una lectura
que su perfil no permite (cobros, estadísticas, las pantallas del propietario…) responde 404 «No existe.», igual que
una página que no está. Las lecturas que piden `reservas` siguen respondiendo 403 con el motivo, para que la persona
sepa a quién pedírselo; las escrituras denegadas, también 403.

| Lectura (GET) | Permiso |
|---|---|
| `/api/provider/fiscal`, `/api/provider/plan`, `/api/center/team`, `/api/center/activity`, `/api/provider/cuenta` | Solo el propietario |
| `/api/provider/payments`, `/api/payments/center` | `cobros` |
| `/api/center/requests`, `/api/center/clients`, `/api/center/info-requests`, `/api/provider/feed` (aviso de cada reserva nueva, v50.56), `/api/center/bookings/<id>/insurance` (seguro de los participantes, v50.56) | `reservas` |
| `/api/provider/ical`, `/api/provider/api-keys`, `/api/provider/webhooks`, `/api/provider/ical-imports` (v50.56) | `centro` |
| `/api/provider/stats`, `/api/center/analytics`, `/api/provider/ventas-canal` (ventas por canal, v50.56), `/api/provider/contador` (visitas y reservas de la temporada, el mes y el total, v50.57) | `estadisticas` |

| Escritura (POST) | Permiso |
|---|---|
| `/api/payments/connect/`, `/api/provider/payment-profile`, `/api/provider/fiscal`, `/api/provider/plan`, `/api/center/team`, `/api/provider/cuenta/` | Solo el propietario |
| `/api/auth/`, `/api/account/`, `/api/legal/accept`, `/api/reports`, `/api/contact`, `/api/me`, `/api/team/`, `/api/app/push/`; su propio Log Book y sus buddies (v50.57): `/api/logbook`, `/api/buddies`; la página vista, sin cookies (v50.57): `/api/visita`; su QR personal, sus enlaces para compartir, sus equipos y su agenda (v50.58): `/api/my/`; avisar de que un vídeo de un punto ya no se ve (v50.58): `/api/videos/` | Cualquiera (su propia cuenta) |
| `/api/center/logbook/dive` (inmersiones del centro y su QR para el Log Book de los buceadores, v50.57) | `checkin` |
| `/api/center/logbook/settings`, `/api/center/logbook/logo` (logo y nombre de la portada del pasaporte, v50.57); `/api/center/short-links/` (crear, cambiar o borrar los QR para imprimir del centro, v50.57; verlos y descargarlos, todo el equipo) | `centro` |
| `/api/manifest/sync`, `/api/pro/escanear`, `/api/pro/contar`, firma del descargo a bordo | `checkin` |
| `/api/provider-services/slot-cancel`, `/api/avisos/`, `/api/whatsapp/` | `avisos` |
| `/api/manifest/` (el resto) | `barco` |
| `/api/bookings/refund`, `/api/bookings/<id>/refund` | `cobros` |
| `/api/provider/insurance`, `/api/provider/cancellation-policy`, `/api/center/cancellation-policy`, `/api/center/profile`, `/api/provider/profile`, `/api/provider/avatar`, `/api/provider/center-update`, `/api/provider/center-showcase`, `/api/provider/center-cover`, `/api/provider/center-gallery`, `/api/center/integration`, `/api/provider/ical`, `/api/center/import`, `/api/center/tariffs`, `/api/provider/waiver`, `/api/marina/`; «Vender en tu web» (v50.56): `/api/provider/vender`, `/api/provider/api-keys`, `/api/provider/webhooks`, `/api/provider/ical-imports` | `centro` |
| `/api/provider-services`, `/api/service-templates/`, `/api/agenda/`, `/api/provider/spot-blocks` (bloqueos de plazas sin cliente, v50.56), `/api/provider/equipment` (piezas de alquiler, precios, equipo completo y stock, v50.58; «Equipo para preparar» lo lee todo el equipo) | `salidas` |
| Todo lo demás del panel (también la póliza que el centro sube para una reserva, v50.56) | `reservas` |

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
