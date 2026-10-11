# Entrega final del encargo · WORLDIVES DISCOVERY v50.31 → v50.38

Fecha: 11/10/2026 · Rama: `claude/worlddives-audit-refactor-k0qm0s`

Este documento reúne los cinco puntos de la «Entrega final» del encargo y enlaza el detalle de cada uno.

---

## 1. Notas de versión de cada fase

| Versión | Fase | Notas |
|---|---|---|
| v50.31 | Fase 1: seguridad urgente (G1–G12 y puntos 1–16) | `RELEASE_NOTES_v50_31.md` |
| v50.32 | Fase 1B: modos de reserva | `RELEASE_NOTES_v50_32.md` |
| v50.33 | Fase 1C: marcadores · Fase 1D: idiomas | `RELEASE_NOTES_v50_33.md` |
| v50.34 | Fase 2: pagos directos sin comisión | `RELEASE_NOTES_v50_34.md` |
| v50.35 | Fase 3: puntos · Fase 4: email y verificación en dos pasos | `RELEASE_NOTES_v50_35.md` |
| v50.36 | Fase 5: legal y privacidad en la web, catálogo propio y mapas | `RELEASE_NOTES_v50_36.md` |
| v50.37 | Fase 6: centros (datos fiscales, planes y herramientas) | `RELEASE_NOTES_v50_37.md` |
| v50.38 | Fase 7: infraestructura · Fase 8: documentos legales · pasada final de idiomas | `RELEASE_NOTES_v50_38.md` |

Cada nota tiene su tabla de estado, su lista «Pendiente de decisión», su lista para abogado o gestoría y cómo se probó.

## 2. Tabla de estado de todos los puntos

La tabla completa, punto por punto, está en **`docs/entrega/estado.md`**: estado, qué se hizo y cómo se probó. `docs/legal/inventario.md` añade dónde está cada punto en el código.

| Estado | Puntos |
|---|---|
| Ya estaba (existía tal cual; solo se ha probado) | 2 |
| Completado (existía a medias) | 31 |
| Nuevo | 66 |
| Pendiente (falta un paso fuera del código) | 2 |
| Pendiente de decisión | 8 filas (detalle en el punto 6) |

Las Fases 1 a 8 están hechas. Lo que queda depende de una decisión del titular, del abogado o la gestoría, o de un trámite (cuentas, dominio, servidor).

## 3. Resultado de las pruebas

**Todas las pruebas se ejecutan sobre copias temporales** del catálogo de demostración. Ninguna toca una base con datos reales.

### 3.1 Pruebas automáticas del servidor: 147 correctas
`cd tests && python3 -m unittest discover -p 'test_*.py'`

| Archivo | Pruebas | Qué cubre |
|---|---|---|
| `test_phase1_security.py` | 24 | G1–G12, puntos 1–16, permisos entre roles, datos erróneos |
| `test_phase1b_booking_modes.py` | 19 | «Pago al reservar» y «Bajo petición», plazos, caducidades |
| `test_phase1d_languages.py` | 5 | Idiomas, URL por idioma, hreflang |
| `test_phase2_payments.py` | 22 | Cargos directos, señal, devoluciones, webhooks, disputas, migración |
| `test_phase3_points.py` | 9 | Puntos 1:1, canje, validación, caducidad, límites, Log Book |
| `test_phase4_email_totp.py` | 8 | Correo, preferencias, verificación en dos pasos |
| `test_phase5_legal_catalog.py` | 23 | Textos legales y versiones, privacidad, reseñas, denuncias, catálogo, mapas |
| `test_phase6_centers.py` | 13 | Planes, datos fiscales, DAC7, herramientas, equipo, funciones |
| `test_phase7_infra.py` | 7 | Esquema, base de producción, `.env`, copias y restauración, salud |
| `test_phase8_languages.py` | 4 | Textos legales, correos y web en los 10 idiomas |
| `test_phase8_flows.py` | 4 | Recuperación de contraseña, cambio de email, sesiones, precio × participantes |
| `test_units.py` | 9 | Funciones sueltas |

### 3.2 Permisos entre roles
Las pruebas comprueban, en el servidor, que cada rol solo llega a lo suyo:

- **Visitante (sin sesión):** sin acceso a reservas, área, documentos, Log Book ni reservas ajenas (403) (`test_cross_role_permissions`). No puede denunciar sin nombre ni email.
- **Buceador:**
  - no ve, cancela ni descarga reservas de otro buceador;
  - no entra en Administración ni en el panel de centro;
  - no publica avisos;
  - no paga solicitudes de otro (`test_cross_role_permissions`, `test_health_and_banner`, `test_price_times_participants_and_spots`).
- **Centro:**
  - no ve ni cambia reservas, cobros, fichas de buceador ni servicios de otro centro;
  - no modera reseñas;
  - no responde reseñas de otro centro;
  - no puede reseñar (`test_cross_role_permissions`, `test_single_editable_reply`, `test_admin_moderation_needs_reason`).
- **Equipo del centro:**
  - **recepción:** sin cobros, plan, datos fiscales, equipo ni ajustes;
  - **instructor:** solo lectura;
  - **propietario:** todo (`test_roles_and_activity_log`, más el recorrido en navegador de recepción en `e2e_centers.py`).
- **Freelance:**
  - no entra en Administración ni en el panel de centro;
  - no puede reseñar;
  - devuelve solo lo suyo (`test_cross_role_permissions`, `test_professionals_cannot_review`).
- **Administración:**
  - nadie puede pedir el rol de administrador al registrarse;
  - un cambio de rol cierra las sesiones;
  - las funciones de administración devuelven 403 a los demás roles (`test_g2_admin_role_cannot_be_requested`, `test_13_role_change_closes_sessions`, `test_publish_bad_data_and_permissions`).
- **Datos erróneos:** las rutas principales responden 4xx, nunca 500, con datos malformados (`test_bad_data_everywhere`).

### 3.3 Navegador real (Chromium)

| Recorrido | Resultado |
|---|---|
| `e2e_walk.py`: todas las pantallas con los 5 roles, en escritorio y en móvil | Sin errores de JavaScript, CSP ni servidor |
| `e2e_booking_modes.py` | 35/35 |
| `e2e_payments.py` | 26/26 |
| `e2e_points_email.py` | 20/20 |
| `e2e_legal_catalog.py` | 33/33 |
| `e2e_centers.py` | 32/32 |
| `e2e_markers.py` | Sin errores; tamaños y fluidez medidos |

### 3.4 Prueba de carga (4 núcleos, cliente en la misma máquina)
- **1 proceso:** 96 peticiones/s con 50 usuarios (mediana 5 ms).
- **4 procesos:** 390 peticiones/s con 200 usuarios (mediana 5 ms).

Falta repetirla en el servidor real.

## 4. Lista de lanzamiento

**`docs/legal/lista-lanzamiento.md`** tiene 14 grupos con casillas: titular, abogado, gestoría, servidor y dominio, seguridad, correo, Stripe, mapas, base de producción, copias, monitor externo, catálogo, planes y pruebas finales. Cada casilla dice qué hacer y cómo comprobar que está hecho.

**Hecho en el código** (no necesita más trabajo de programación para abrir):
- seguridad G1–G12;
- reservas y pagos directos sin comisión;
- puntos;
- correos en 10 idiomas;
- verificación en dos pasos;
- textos legales con versiones y aceptación;
- exportación y baja;
- denuncias;
- planes y herramientas para centros;
- copias;
- salud y avisos;
- instalación limpia y base de producción;
- guías de despliegue y operación.

**Pendiente para abrir** (fuera del código):
- **Cuentas y servicios:**
  - servidor y dominio;
  - cuenta de Stripe de la plataforma con Connect y sus dos webhooks;
  - proveedor de email con SPF, DKIM y DMARC;
  - clave de ArcGIS y archivo PMTiles;
  - destino externo de las copias;
  - monitor externo.
- **Datos legales del titular** en *Administración → Legal* y precios de los planes.
- **Arranque de producción:**
  - crear la base de producción (`tools/crear_base_produccion.py`);
  - crear el primer administrador con verificación en dos pasos;
  - hacer la prueba de restauración.
- **Revisiones y pruebas:**
  - revisión del abogado y de la gestoría (punto 5);
  - pruebas finales en el servidor real, incluida la prueba de carga.

## 5. Lo que necesita abogado, gestoría o trámite oficial

### Abogado
Todas las preguntas están en **`docs/legal/preguntas-abogado.md`**, cada una con el código o el texto del que sale:

1. Papel de cada parte en protección de datos (WORLDIVES y centro) y anexo de encargado.
2. Datos de salud: no se suben certificados médicos; solo hay una declaración.
3. Viajes combinados y servicios de viaje vinculados (experiencias).
4. Ley aplicable y consumidores extranjeros, idioma que prevalece (incluida la frase «the Spanish version prevails» en 4 textos en inglés) y reclamaciones.
5. Responsabilidad como intermediario.
6. Señal, cancelaciones y desistimiento.
7. DSA: exención de pequeñas empresas, declaración de motivos y denuncias sin nombre.
8. Reglamento P2B (orden de resultados, condiciones para centros).
9. Planes, degradación y cuotas.
10. Cuentas del equipo e importación de clientes.
11. Reseñas verificadas: etiqueta y momento en que se puede reseñar.
12. Comunicaciones comerciales y cookies.
13. Menores.
14. Catálogo, imágenes y mapas: licencias, términos de ArcGIS y del proxy de Esri.
15. Programa de puntos: fuera de dinero electrónico.
16. DAC7.
17. Otros textos: accesibilidad (Ley 11/2023 y Acta Europea de Accesibilidad).

También: **revisión jurídica de los textos legales**, al menos en castellano y en inglés (oficiales). Las traducciones a los otros 8 idiomas están hechas, pero no revisadas por un traductor jurídico.

### Gestoría
Todas las preguntas están en **`docs/legal/preguntas-gestoria.md`**:

1. Alta y forma jurídica.
2. IVA de la cuota anual (España, UE con NIF-IVA, fuera de la UE).
3. Facturas de la cuota y Verifactu: hoy la web registra el pago pero no emite factura.
4. DAC7 (modelos 040 y 238, plazo de enero).
5. Gastos y facturas de proveedores.
6. Justificantes de reserva.
7. Declaraciones y conservación.

### Trámites oficiales y de terceros
- Alta censal (modelo 036/037) y, si aplica, alta como operador de plataforma para DAC7 (modelo 040).
- Registro del dominio y datos del titular en el aviso legal (LSSI-CE art. 10).
- Delegado de protección de datos: valorar si hace falta y, si es así, comunicarlo a la AEPD.
- Contratos con encargados (servidor, email, Stripe, ArcGIS) y transferencias internacionales.
- Verificación de la cuenta de Stripe de la plataforma y activación de Connect.
- Términos de uso de ArcGIS para la vista satélite (proxy y contador mensual).

## 6. Pendiente de decisión del titular

### De fases anteriores
- **Precios de los planes** y plan y duración de la prueba gratuita (hoy Pro, 60 días).
- **«Destacado» o «Patrocinado»:** hoy «Patrocinado».
- **Proveedor de email:** recomendado Brevo; solo cambia la configuración.
- **Stripe Accounts v2:** hoy v1 con propiedades de controlador.
- **Devolución propuesta y no hecha por el centro:** hay recordatorio a 72 h e incidencia; falta decidir una medida adicional.
- **Ruta del monedero:** `#/mis-puntos` (porque `#/puntos` es la lista de puntos de buceo).
- **Proxy de Esri:** confirmar los términos de ArcGIS.

### De v50.38
- **Duración de la sesión:** 8 horas desde la entrada o 8 horas sin actividad.
- **Copias cifradas** en el destino externo o cambiar el texto de privacidad.
- **Logotipos solo subidos a WORLDIVES** o enlaces externos.
- **Etiqueta de las reseñas:** «Inmersión verificada» o «Reserva verificada».
- **Documentos de clientes:** quién del equipo puede verlos.
- **Borrado desde la web de las cuentas de centro y freelance.**
- **Herramientas de Administración** para devolver y anular puntos.
- **Inglés oficial** o traducción.
