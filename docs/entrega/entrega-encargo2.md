# Entrega · Encargo 2: 6 mejoras de prioridad alta para centros (v50.39 → v50.42)

Fecha: 12/10/2026 · Rama: `claude/worlddives-audit-refactor-k0qm0s`

Requisito previo cumplido: Fase 1 (seguridad, v50.31) y Fase 1B (modos de reserva, v50.32) entregadas antes de empezar.

## 1. Notas de versión

| Versión | Puntos | Notas |
|---|---|---|
| v50.39 | 7 · Inicio de sesión y registro más sencillos | `docs/notas-de-version/v50.39.md` |
| v50.40 | 1 · Manifiesto de salida · 5 · Formularios firmados | `docs/notas-de-version/v50.40.md` |
| v50.41 | 2 · Cancelar salida por mal tiempo · 3 · Cambio de fecha · 4 · Lista de espera | `docs/notas-de-version/v50.41.md` |
| v50.42 | 6 · Check-in en el barco sin cobertura | `docs/notas-de-version/v50.42.md` |

Cada nota explica qué había antes, qué cambia, la migración (solo añade), el estado de cada parte, lo pendiente de decisión, lo que debe mirar el abogado y cómo se probó.

## 2. Tabla de estado

La tabla parte por parte, con lo que se hizo y cómo se probó, está en **`docs/entrega/estado-encargo2.md`**. En resumen:

| Punto | Estado |
|---|---|
| 1. Manifiesto de salida | Nuevo (emergencia con las reglas G1/G5 existentes: Completado) |
| 2. Cancelar una salida por mal tiempo | Nuevo (devoluciones y correos existentes: Completado) |
| 3. Cambio de fecha por el cliente | Nuevo (amplía el cambio que hacía el centro); diferencia de precio: Pendiente de decisión |
| 4. Lista de espera | Nuevo |
| 5. Formularios firmados antes de bucear | Nuevo; cuestionario médico: Pendiente de decisión (abogado) |
| 6. Check-in en el barco sin cobertura | Nuevo (la app instalable ya existía: Completado) |
| 7. Inicio de sesión y registro | Completado (diseño recuperado) y Nuevo (tarjetas, pantalla del segundo paso) |

**Cómo se integra:**
- Todo va donde el centro ya trabaja:
  - **planning:** «Manifiesto», «Cancelar salida» y «Check-in en el barco»;
  - **reserva:** solicitud de cambio, descargo y elección tras una cancelación;
  - **formulario del servicio:** cambio de fecha y lista de espera;
  - **Herramientas:** descargo.
- **Diseño:** los mismos botones, tarjetas, avisos y colores de la web; nada de colores nuevos.
- **Confirmaciones:** cada acción importante pide confirmación con un resumen («Se avisará a 2 reservas (3 buceadores)…», «Se repartirán 8 buceadores en 3 grupos…»).
- **Accesibilidad:** etiquetas enlazadas, foco visible en los controles nuevos y botones de 44 px en el barco.

## 3. Pruebas

Todas las pruebas usan **copias temporales** del catálogo de demostración. Ninguna usa una base con datos reales.

### Servidor: 164 pruebas correctas
`cd tests && python3 -m unittest discover -p 'test_*.py'`

| Archivo nuevo | Pruebas | Qué cubre |
|---|---|---|
| `test_e2_p7_auth.py` | 6 | Alta de los tres tipos, datos erróneos, nadie se hace centro o administrador al registrarse, segundo paso aparte, contraseña olvidada |
| `test_e2_p1_p5_manifest.py` | 6 | Niveles y reparto, filas y privacidad, barcos, grupos y avisos, permisos, descargo con versiones y firmas, PDF |
| `test_e2_p2_p3_p4.py` | 3 | Cancelar salida con elección y devolución automática (simulador de Stripe), cambio de fecha directo o con aprobación, lista de espera |
| `test_e2_p6_offline.py` | 2 | Paquete del día, sincronización y conflictos |

### Permisos entre roles (encargo 2)
- **Otro centro:**
  - no ve ni toca el manifiesto, los barcos, los grupos, la cancelación de la salida, las solicitudes de cambio ni el check-in;
  - no ve los PDF de descargos ni puede firmar en reservas ajenas (403).
- **Buceador:**
  - no ve el manifiesto, el check-in ni el paquete del día;
  - no cancela salidas;
  - no cambia la fecha de reservas de otros, ni elige en salidas canceladas ajenas (enlace falso o ajeno: 403);
  - no ve el descargo de otra persona.
- **Equipo del centro:**
  - el propietario y recepción organizan el manifiesto, cancelan salidas y deciden cambios;
  - el texto del descargo solo lo cambia el propietario;
  - el instructor solo lee el manifiesto, pero puede marcar el check-in y recoger firmas;
  - las cuentas de centro no se apuntan a listas de espera.
- **Visitante sin sesión:** elige en una salida cancelada solo con el enlace privado de su reserva.

### Navegador real (Chromium), en ordenador y en móvil

| Recorrido | Resultado |
|---|---|
| `e2e_auth.py` (punto 7, 10 idiomas) | 58/58 |
| `e2e_manifest.py` (puntos 1 y 5) | 27/27 |
| `e2e_departures.py` (puntos 2, 3 y 4) | 31/31 |
| `e2e_offline.py` (punto 6, sin red) | 13/13 |
| `e2e_walk.py` (todas las pantallas, 5 roles) | Sin errores |
| Recorridos anteriores (reservas, pagos, puntos, legal, centros) | 35/35, 26/26, 20/20, 33/33, 32/32 |

**Textos:** los nuevos están en los 10 idiomas. Lo comprueba el recolector, que abre cada pantalla en inglés y anota todo texto sin traducir. Los 488 textos de correo están traducidos (`test_phase8_languages`).

## 4. Capturas antes y después (ordenador y móvil)

| Carpeta | Qué hay |
|---|---|
| `docs/capturas/encargo2/punto7/` | `antes-*`: v50.30 (versión anterior) · `despues-*`: inicio de sesión, registro (tarjetas y cada tipo), segundo paso, aviso de email y los 10 idiomas |
| `docs/capturas/encargo2/antes-despues/` | v50.38 frente a v50.42: planning de una salida, «Mi reserva» y salida completa en la página de reserva |
| `docs/capturas/encargo2/punto1-5/` | Manifiesto (sin repartir, reparto y móvil), «Mover», vista para el barco, impresión A4 (PNG y PDF), editor del descargo y firma en el móvil |
| `docs/capturas/encargo2/punto2-4/` | Cancelar salida, planning «Cancelada», elección en el móvil, cambiar fecha, solicitud en el centro, opciones del servicio, lista de espera y plaza guardada |
| `docs/capturas/encargo2/punto6/` | Hoy en el barco, check-in sin conexión y conflictos |

## 5. Pendiente de decisión
1. **Cambio de fecha con precio distinto** (punto 3): ¿cobrar o devolver la diferencia? Hoy la reserva mantiene su precio y se muestra la diferencia.
2. **Cuestionario médico en el descargo** (punto 5): solo si el abogado lo aprueba. Está preparado y desactivado.
3. **Texto base del descargo** revisado por el abogado para ofrecer a los centros (opcional).
4. **Opción por defecto del cambio de fecha** en los servicios: hoy «con mi aprobación».
5. **Lista de espera cuando la primera persona no cabe:** hoy se avisa a la siguiente que sí cabe.
6. **Casilla de comunicaciones comerciales en el registro:** hoy solo está en «Mi cuenta».
7. **Inicio de sesión con el usuario antiguo:** hoy se admite, aunque la etiqueta diga «Email».

## 6. Para el abogado
En `docs/legal/preguntas-abogado.md`, apartado 19:
- firma dibujada como firma electrónica simple;
- validez de un descargo frente a consumidores;
- cuestionario médico;
- responsable de los descargos y plazo de conservación de las firmas;
- acompañantes menores;
- contacto de emergencia en el manifiesto;
- cancelación por el centro con devolución automática;
- diferencia de precio;
- lista de espera.
