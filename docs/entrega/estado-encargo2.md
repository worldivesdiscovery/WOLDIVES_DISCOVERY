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

## Puntos 1–6

| Punto | Estado | Versión |
|---|---|---|
| 1. Manifiesto de salida | Pendiente | v50.40 |
| 5. Formularios firmados antes de bucear | Pendiente | v50.40 |
| 2. Cancelar una salida por mal tiempo | Pendiente | v50.41 |
| 3. Cambio de fecha por el cliente | Pendiente | v50.41 |
| 4. Lista de espera | Pendiente | v50.41 |
| 6. Check-in en el barco sin cobertura | Pendiente | v50.42 |

## Pendiente de decisión
- Casilla de comunicaciones comerciales en el registro (hoy solo en «Mi cuenta»).
- Inicio de sesión con el usuario antiguo además del email (hoy se admite).
- Cambio de fecha con precio distinto: cobro o devolución de la diferencia (punto 3).
- Cuestionario médico en el descargo: solo si el abogado lo aprueba (punto 5).
