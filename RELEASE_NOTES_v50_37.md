# WORLDIVES DISCOVERY v50.37: centros (datos fiscales, planes y herramientas) (Fase 6)

## 1 · Datos fiscales, verificación y seguro (DAC7)
- **Panel → «Datos fiscales y seguro»**, para centros y profesionales. Recoge:
  - tipo de prestador (empresa o autónomo);
  - razón social o nombre;
  - NIF/TIN y país emisor;
  - registro mercantil (empresa) o fecha de nacimiento (autónomo);
  - dirección fiscal;
  - cuenta de cobro (la de Stripe);
  - declaraciones de licencias y de titulación del personal;
  - **seguro de responsabilidad civil**: aseguradora, póliza, caducidad y certificado privado, que solo ve la administración.
- **Avisos del seguro:** email 30 y 7 días antes de la caducidad y al caducar (una vez cada uno). También se avisa en el panel.
- **Informe DAC7 anual** (*Administración → Planes → Informe DAC7*, CSV). Incluye, por prestador:
  - los datos de identificación;
  - el importe cobrado a través de la web en cada trimestre (cobros menos devoluciones);
  - el número de actividades por trimestre;
  - **comisiones 0**.
  - Marca qué datos faltan.
- Se amplía `/api/provider/payment-profile` (Fase 2) con `/api/provider/fiscal`, sin duplicar la lógica.

## 2 · Planes y funciones
- **Administración → Planes:** «Ficha gratuita», «Motor de reservas» y «Pro». Para cada uno se configuran:
  - el precio anual y la moneda;
  - una descripción;
  - interruptores para 11 funciones: reservas online, cobros online, iCal, widget, importación, equipo, informes, promociones, experiencias, ventajas y puntos, y API;
  - límites de servicios y de personas del equipo.
  - Los precios empiezan **sin definir**: los fija el titular.
- **Excepciones por centro**, con motivo obligatorio y registro (alta y baja). Una función activada por excepción no queda limitada por el plan.
- **Comprobación en el servidor** en cada ruta protegida. Responde «Función no incluida en tu plan» y la web muestra el botón «Ver planes».
- **Prueba gratuita configurable** (60 días del plan Pro por defecto). Empieza cuando la administración aprueba el alta. Los centros y profesionales ya aprobados empiezan la prueba con la migración, así que nadie pierde funciones.
- **Cuota anual:**
  - se paga con Stripe en la cuenta de la **plataforma** (`/api/provider/plan/checkout` y webhook `kind=plan_fee`, idempotente);
  - o la administración la marca como pagada a mano, con nota (`plan_payments`);
  - avisos a 30, 7 y 1 días;
  - email al pagar y al terminar.
- **Al terminar el plan**, el centro pasa a ficha gratuita:
  - no acepta reservas online nuevas;
  - las existentes se atienden con normalidad (cambios, cobros pendientes y devoluciones);
  - la exportación sigue disponible siempre.
- **Prohibido y comprobado:**
  - nunca se muestra «sin plazas» por el plan: se muestra «no tiene reserva online» y «Solicitar información»;
  - las solicitudes de los clientes llegan siempre, por email y al panel;
  - la exportación nunca se bloquea.
- **Visibilidad pagada:** los planes no cambian el orden de los resultados. Las publicaciones pagadas siguen llevando la etiqueta «Patrocinado» (ver Pendiente de decisión).
- Página pública **`#/planes`** y «Mi plan» en el panel (estado, fecha, funciones, contratar o renovar, historial de pagos).

## 3 · Ficha gratuita: «Solicitar información»
Formulario con nombre, email, teléfono, fecha, personas, mensaje y aceptación de privacidad, con límite por IP. La solicitud llega al centro por email y a su panel («Solicitudes de información»: marcar como leída o contestada). El buceador recibe una copia que le explica que ese centro no tiene reserva online. Funciona en la ficha del centro, en la del profesional, en la página de reserva y en el widget.

## 4 · Datos para convencer al centro gratuito
- **Estadísticas en todos los planes**, agregadas y sin datos personales: visitas a la ficha (una por visitante y día), clics en «Reservar» y solicitudes, a 30, 90 o 365 días, con gráfico diario.
- **Comparación anónima con la zona** (región o país), solo cuando hay al menos 3 centros más.
- **Email mensual** el día 1.

## 5 · Herramientas
- **Exportación CSV** de clientes, reservas, servicios y pagos, en todos los planes. Los pagos solo los exporta el propietario. Lleva BOM para Excel y protección contra inyección de fórmulas.
- **Feed iCal privado** por centro y por profesional (`/ical/<token>.ics`): se puede regenerar y no incluye emails de los clientes.
- **Importación de clientes CSV:**
  - plantilla descargable;
  - vista previa con nuevos, duplicados (por email o teléfono, también dentro del archivo) y errores;
  - confirmación antes de importar.
  - Los importados son clientes solo del centro: no son cuentas y no reciben correos.
- **Widget de reservas** (`/widget/center/<id>`) para incrustar en cualquier web. Es HTML sin scripts ni formularios, con `frame-ancestors *` solo en esa ruta; el resto de la web sigue sin poder incrustarse. Lista actividades y salidas y abre la reserva en WORLDIVES.
- **Enlace directo** para Instagram y Google, y botón para compartir por WhatsApp.

## 6 · Equipo del centro
- **Perfiles:**
  - **Propietario:** todo.
  - **Recepción:** reservas, clientes, servicios y salidas, sin cobros, plan, datos fiscales, equipo ni ajustes.
  - **Instructor:** solo lectura.
  - Se comprueba en el servidor en una única puerta (`team_gate`).
- **Invitaciones** por email (7 días), con creación de cuenta o con la cuenta existente del mismo email. El propietario puede cambiar perfiles y quitar personas; la cuenta de quien sale se queda como cuenta de buceador. Hay un límite por plan.
- **Corregido:** el catálogo y las salidas del centro son de todo el equipo. Antes, solo quien creaba un servicio podía verlo en la lista de gestión, editarlo o gestionar sus salidas. El planning ya mostraba todos los servicios.
- **Registro de actividad del centro:** cada acción del equipo queda marcada con el centro (`audit_log.center_id`).

## 7 · Funciones activables
- **Administración → Funciones:** Puntos, Promociones, Experiencias, Patrocinio, Reseñas y Pagos online. Al desactivar una función desaparece de la web y el servidor rechaza su uso; los datos se conservan.
- **Modo piloto** (ya existía en el servidor): ahora tiene su interruptor y una gestión de invitaciones (crear con nota y caducidad, y anular).

## Migración `migrate_v50_37` (solo añade)
- Columnas nuevas en `centers` y `users`:
  - datos fiscales y seguro;
  - plan, estado, caducidad y avisos;
  - token iCal.
- Tablas nuevas: `plans`, `plan_exceptions`, `plan_payments`, `info_requests`, `provider_stats_daily` y `team_invites`.
- `audit_log.center_id`.
- Los planes por defecto se crean sin precio. No se borra nada.

## Estado de la Fase 6

| Punto | Estado |
|---|---|
| 6.1 Datos fiscales, declaraciones, seguro con avisos, informe DAC7 | Nuevo (amplía los datos fiscales de la Fase 2) |
| 6.2 Planes, excepciones, comprobación en servidor, cuota, prueba, degradación | Nuevo |
| 6.3 Ficha gratuita con «Solicitar información» | Nuevo |
| 6.4 Estadísticas agregadas, comparación con la zona, email mensual | Nuevo |
| 6.5 CSV, iCal, importación, widget y enlaces | Nuevo |
| 6.6 Roles del equipo, planning de todo el centro, registro de actividad | Completado (`center_members` ya existía; la gestión, los permisos y la corrección del catálogo son nuevos) |
| 6.7 Funciones activables y modo piloto | Completado (el modo piloto existía solo en el servidor) |

## Pendiente de decisión
- **Precios** de «Motor de reservas» y «Pro». Las funciones y los límites por defecto son una propuesta.
- **Plan y duración de la prueba gratuita:** Pro, 60 días.
- **Etiqueta:** el encargo dice «Destacado» para toda visibilidad pagada. La web y los textos legales usan «Patrocinado» desde la Fase 2, y los planes no dan visibilidad. Hay que elegir una sola palabra.
- **Altas de profesionales con centro:** el freelance que trabaja para un centro se gestiona como miembro de su equipo. Si un freelance tiene a la vez centro propio y servicios propios, cuenta como su centro.
- **Plantilla de importación:** clientes. Si también se quieren importar servicios o salidas, se puede añadir con la misma vista previa.

## Para abogado / gestoría
- **IVA de la cuota anual:** precio con o sin IVA, tipo para clientes de España, de la UE (B2B con NIF-IVA, inversión del sujeto pasivo) y de fuera de la UE. **Facturas** de la cuota y **Verifactu**: hoy la web registra el pago pero no emite factura.
- **DAC7:** confirmar si WORLDIVES es «operador de plataforma» obligado al ver que no cobra a través de la plataforma (son cargos directos en la cuenta del centro). Revisar el formato del modelo 238 y el plazo (enero), y los prestadores excluidos.
- **Condiciones para centros:** planes, degradación, ausencia de comisión, datos del equipo e importación (base legal del centro para importar a sus clientes).
- **Protección de datos:** formulario «Solicitar información» (WORLDIVES transmite los datos al centro) y feed iCal.

## Cómo se probó
- **`tests/test_phase6_centers.py`, 13 pruebas:**
  - planes públicos y prueba al aprobar;
  - plan terminado: ficha gratuita sin «sin plazas», reservas existentes que siguen, exportación, iCal bloqueado, solicitud de información con emails y permisos, widget;
  - avisos de renovación una sola vez y aviso de fin;
  - cuota con Stripe en la cuenta de la plataforma, webhook idempotente y prórroga sobre la prueba;
  - asignación manual, excepciones con motivo, límite de servicios y datos erróneos;
  - datos fiscales con validaciones, certificado privado y aviso de seguro;
  - DAC7 por trimestre con devoluciones;
  - estadísticas sin duplicar visitas;
  - exportaciones, iCal y widget (y el resto de la web sigue sin poder incrustarse);
  - importación con vista previa y duplicados;
  - roles del equipo (recepción, instructor, propietario), edición del catálogo del equipo y registro de actividad;
  - interruptores de funciones;
  - modo piloto con invitaciones.
- **`tests/e2e_centers.py`, 30/30 en navegador:**
  - planes en móvil;
  - ficha gratuita con solicitud de información;
  - las 7 pestañas nuevas del propietario, con todas las etiquetas enlazadas;
  - invitación al equipo y panel de recepción;
  - Administración → Planes y Funciones.
  - Capturas en `docs/capturas/fase-6/`.
- **Suite completa: 130 pruebas correctas.**
