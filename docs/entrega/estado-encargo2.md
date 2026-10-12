# Tabla de estado · Encargo 2: 6 mejoras de prioridad alta para centros (desde v50.39)

Estados: **Ya estaba** (existía tal cual; solo se ha probado) · **Completado** (existía a medias; se ha completado) · **Nuevo** · **Pendiente de decisión** · **Pendiente** (programado en una versión siguiente).

Requisito previo: Fase 1 (seguridad, v50.31) y Fase 1B (modos de reserva, v50.32) entregadas.

## Punto 7 · Inicio de sesión y registro (v50.39)

| Parte | Estado | Qué se hizo | Cómo se probó |
|---|---|---|---|
| Diseño de la versión anterior (dos columnas; móvil solo formulario) | Completado | Se quitan los campos que se veían sin deber (`hidden` anulado por el CSS) y la foto en el móvil | `e2e_auth.py` + capturas antes/después |
| Iniciar sesión: email, contraseña, «Entrar» y enlace pequeño | Completado | Sin campo de código; enlace debajo del botón | `e2e_auth.py` |
| Contraseña olvidada en pantalla aparte | Ya estaba | `#/recuperar` y `#/restablecer` | `test_phase8_flows`, `e2e_auth.py` |
| Verificación en dos pasos en pantalla aparte | Nuevo | `#/verificacion`; credenciales solo en memoria | `test_e2_p7_auth`, `e2e_auth.py` |
| Alta con tres tarjetas, campos por tipo y «Cambiar» | Nuevo | Buceador / Centro de buceo / Profesional; usuario creado a partir del email | `test_e2_p7_auth`, `e2e_auth.py` |
| Centro: país, ciudad y «Revisaremos tu centro…» | Completado | Pendiente de aprobación (Fase 1) | `test_e2_p7_auth`, `e2e_auth.py` |
| Profesional: titulación | Nuevo | De la lista o «Otra»; se guarda en la ficha y en la solicitud | `test_e2_p7_auth`, `e2e_auth.py` |
| Verificación del email por enlace y aviso discreto | Completado | Aviso con «Reenviar» en la cabecera de la cuenta | `e2e_auth.py` |
| Textos en 10 idiomas | Completado | 22 textos nuevos | `e2e_auth.py` (10 idiomas), `test_phase8_languages` |

## Puntos 1 y 5 · Manifiesto de salida y descargo firmado (v50.40)

| Parte | Estado | Qué se hizo | Cómo se probó |
|---|---|---|---|
| 1. Manifiesto desde cada salida del planning | Nuevo | Botón «Manifiesto» → `#/manifiesto?slot=` | `e2e_manifest.py` |
| 1. Barco, guía y grupo | Nuevo | Tablas `boats`, `slot_groups`, `manifest_entries` | `test_e2_p1_p5_manifest` |
| 1. Sugerencia por nivel y titulación; arrastrar y «Mover» en el móvil | Nuevo | `app/wod/manifest.py`; confirmación con resumen | ambos |
| 1. Máximo por guía configurable y aviso | Nuevo | 4 por defecto, por centro o profesional | ambos |
| 1. Barcos con capacidad y aviso | Nuevo | Personas a bordo (buceadores y guías) | ambos |
| 1. Vista para imprimir A4 y vista para el patrón | Nuevo | Tabla por grupo; tarjetas con teléfono y emergencia | `e2e_manifest.py` (captura y PDF) |
| 1. Emergencia solo si se ha compartido | Completado | Reglas G1/G5 de la ficha del buceador | `test_e2_p1_p5_manifest` |
| 5. Descargo propio con versión y fecha | Nuevo | Panel → Herramientas; solo el propietario lo cambia | ambos |
| 5. Firma con casilla, nombre y firma dibujada | Nuevo | «Mi reserva» y check-in (dispositivo del centro) | ambos |
| 5. Versión, fecha, hora y reserva; PDF | Nuevo | Texto exacto firmado; PDF para centro y buceador | ambos |
| 5. Manifiesto marca quién ha firmado | Nuevo | Etiqueta «Firmado / Sin firmar» y aviso | ambos |
| 5. Sin preguntas de salud | Pendiente de decisión | Preparado y desactivado (`WAIVER_HEALTH_QUESTIONS`) | `test_e2_p1_p5_manifest` |

## Puntos 2, 3 y 4 · Cancelar salida, cambio de fecha y lista de espera (v50.41)

| Parte | Estado | Qué se hizo | Cómo se probó |
|---|---|---|---|
| 2. «Cancelar salida» con motivo | Nuevo | En el planning y en el manifiesto; propietario y recepción | `test_e2_p2_p3_p4`, `e2e_departures.py` |
| 2. Lista de afectados y qué recibe cada uno antes de confirmar | Nuevo | Vista previa con importes y fechas alternativas | ambos |
| 2. Correo con otra fecha o devolución íntegra | Nuevo | Enlace con clave de la reserva (sin iniciar sesión) y aviso en «Mi reserva» | ambos |
| 2. Devolución automática si no elige (48 h configurable) | Nuevo | Trabajo periódico `run_slot_cancel_jobs` | `test_e2_p2_p3_p4` |
| 2. Devoluciones y cola de correos existentes; historial de la salida | Completado | `refund_booking`, `notify_booking`; tabla `slot_events` | ambos |
| 3. «Cambiar fecha» en «Mi reserva» dentro de plazo | Nuevo | 48 h por defecto, por servicio | ambos |
| 3. Mismo servicio y plazas libres; mismo precio; diferencia indicada | Nuevo | Cobro o devolución de la diferencia: pendiente de decisión | `test_e2_p2_p3_p4` |
| 3. Directo o con aprobación por servicio | Nuevo | Formulario del servicio; el centro acepta o rechaza en la reserva | ambos |
| 3. Avisos y plazas movidas de forma atómica | Completado | `move_booking`, común con el cambio del centro (Fase 1B) | ambos |
| 4. «Avisarme si queda plaza» | Nuevo | Página de reserva, con puesto y «Salir de la lista» | ambos |
| 4. Primero con plazo de 2 h (nunca después del inicio), luego el siguiente | Nuevo | Plazas guardadas al avisado; enganche en `release_slot_spots` | `test_e2_p2_p3_p4` |
| 4. Respeta el modo de reserva | Nuevo | «Bajo petición» conserva la plaza mientras responde el centro | `test_e2_p2_p3_p4` |
| 4. El centro ve la lista y la desactiva por servicio | Nuevo | Manifiesto y formulario del servicio | ambos |

## Punto 6

| Punto | Estado | Versión |
|---|---|---|
| 6. Check-in en el barco sin cobertura | Pendiente | v50.42 |

## Pendiente de decisión
- Casilla de comunicaciones comerciales en el registro (hoy solo en «Mi cuenta»).
- Inicio de sesión con el usuario antiguo además del email (hoy se admite).
- Cambio de fecha con precio distinto: cobro o devolución de la diferencia (punto 3).
- Cuestionario médico en el descargo: solo si el abogado lo aprueba (punto 5).
- Texto base del descargo revisado por el abogado para ofrecer a los centros (opcional).
- Opción por defecto del cambio de fecha en los servicios (hoy «con mi aprobación»).
- Lista de espera cuando la primera persona no cabe (hoy se avisa a la siguiente que sí cabe).
