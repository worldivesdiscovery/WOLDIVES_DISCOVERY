# Encargo unificado: motor de reservas y Experiencias · estado

Fecha: 12/10/2026 · Versión base: v50.43

## Orden general (tabla del titular)

| # | Encargo | Estado |
|---|---|---|
| 1 | Auditoría · Fase 1 (seguridad G1-G12) | Ya estaba (v50.31) |
| 2 | Auditoría · Fases 1B, 1C y 1D | Ya estaba (v50.32-v50.33). Capas «Mapa», «Satélite» y «Relieve» en v50.43. |
| 3 | `encargo-auditoria-experiencia-y-promesas.md` · Partes A y B | **Pendiente: falta el documento.** No se ha pegado en la sesión. Hace falta para medir las promesas 1, 3 y 4 «con los mismos scripts». |
| 4 | Auditoría · Fases 2 y 3 | Ya estaba (v50.34-v50.35) |
| 5 | Encargo unificado · Bloque A, tanda 1 | **En curso:** A1 (revisión y diseño) entregado; **esperando la aprobación de las maquetas** |
| 6 | Encargo unificado · Bloque B | B1 (revisión) entregado. El resto, después de la tanda 1. |
| 7 | Auditoría · Fases 4 a 6 | Ya estaba (v50.35-v50.37) |
| 8 | Encargo unificado · Bloque A, tanda 2 | Pendiente (después del bloque B). Parte de E7 y E14 ya existe (v50.41 y v50.42). |
| 9 | Experiencia y promesas · Partes C y D | Pendiente (necesita el documento del punto 3) |
| 10 | Auditoría · Fases 7 y 8 | Ya estaba en código (v50.38). Falta contratar el VPS. |
| 11 | `encargo-app-android-ios.md` | Pendiente (falta el documento) |

## Entregado ahora (A1 y B1, sin cambiar código)

| Documento | Contenido |
|---|---|
| `docs/agenda/estado-actual.md` | Modelo actual, cálculo de plazas, qué pasa hoy con un curso de varios días y qué se reutiliza |
| `docs/agenda/diseno.md` | Motor común: recursos, bloques, disponibilidad, sin solapes con transacción, zona horaria, índices, precio, flujos, planning, privacidad, rendimiento, opciones por plan y versiones previstas |
| `docs/agenda/maquetas/` | 6 maquetas con capturas en ordenador y móvil, **para aprobar** |
| `docs/experiencias/estado-actual.md` | B1: publicación, imagen, organizador, filtros, reserva y pago, plazas y denuncias |
| `docs/capturas/experiencias-b1/` | Lista, ficha, reserva, panel del centro y del freelance, y administración, en ordenador y móvil |

## Hallazgos de la revisión (se corrigen en su tanda, no ahora)
- **Zona horaria:** los plazos se calculan con la hora del servidor. Un guía en México quedaría desfasado. Se corrige en v50.44.
- **Cursos de varios días:** los días 2 y 3 no se ven y el instructor no queda ocupado.
- **Solapes:** un guía o un barco puede estar en dos salidas a la vez sin aviso.
- **Experiencias:**
  - **EXIF:** las fotos subidas conservan sus datos, incluido el GPS. Se corrige en el bloque B.
  - **Sin aviso al administrador:** no se le avisa de las experiencias nuevas.
  - **Sin aviso al organizador:** no se le avisa al rechazar su experiencia.
  - **Las plazas no caducan** si el organizador no responde.
  - **Pago al momento:** la web intenta abrir el pago justo al enviar la solicitud. El servidor lo rechaza sin consecuencias.
  - **Estados sin traducir:** en la bandeja del administrador se ven «pending» y «published».
- **Push:** no existe. Hay una propuesta en el diseño.

## Pendiente de decisión del titular
1. **Aprobar las maquetas** (o pedir cambios). Hasta entonces no se programa el bloque A.
2. **Push con Web Push** en la app instalable.
3. **En qué plan va cada opción avanzada.**
4. **Zona horaria por defecto:** la del país del perfil.
5. **Solicitudes que se solapan:** avisar y rechazarlas al confirmar (propuesta).
6. **Pegar los documentos que faltan:** `encargo-auditoria-experiencia-y-promesas.md` y `encargo-app-android-ios.md`.

## Para el abogado
- **B6:** licencia de agencia de viajes cuando una experiencia incluya alojamiento y transporte. Se preparará como un campo desactivado.
- **B4 (DSA):** decisiones motivadas al ocultar, eliminar o pedir cambios en contenidos de terceros.
