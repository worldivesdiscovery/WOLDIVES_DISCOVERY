# WORLDIVES DISCOVERY v50.44: motor de agenda común y freelance por días y medias jornadas (encargo unificado, bloque A: A2 y parte de A4)

Primera versión programada del encargo unificado, después de aprobar las maquetas (A1).

## Qué había antes
- **Un servicio solo podía venderse por salidas** de un día y una hora (`service_slots`).
- **Una reserva «solo con fecha»** no controlaba nada: dos clientes podían pedir el mismo día al mismo guía.
- **No había calendario de disponibilidad** ni agenda del freelance: ni bloqueos, ni vacaciones, ni horario habitual.
- **Las horas se calculaban siempre con la hora del servidor.**

## Motor de agenda común (A1.2, aprobado)
- **Tablas nuevas:**
  - **recursos:** quién se ocupa; hoy, el propio freelance;
  - **horario habitual y temporadas cerradas;**
  - **bloques de ocupación**, con su tipo (reserva, bloqueo, vacaciones) y su referencia;
  - **días de cada reserva.**
- **Nunca dos bloques a la vez:** el servidor comprueba los solapes dentro de una transacción exclusiva. Si se confirman los mismos días al mismo tiempo, solo gana una confirmación (comprobado con dos confirmaciones simultáneas).
- **Los bloques no se borran:** se liberan, y así queda el historial.
- **Zona horaria del lugar del servicio:**
  - los días y las horas se guardan en UTC y en día local;
  - un guía en Cancún y un cliente en España ven los mismos días;
  - probado con el cambio de hora, el fin de mes y el 29 de febrero.
- **Una sola función de precio:** tarifa por día, media jornada, tramos («desde 4 días, 150 € al día»), descuento («−10 % desde 3 días»), precio por grupo o por persona y extras por día o por reserva (y por persona).

## A2 · Freelance por días y medias jornadas
- **Formulario del servicio → «Unidad de reserva»:**
  - «Por salidas» (como hasta ahora), «Por días» o «Por días o medias jornadas»;
  - precio por día y de media jornada, por grupo o por persona;
  - días mínimos y máximos, días seguidos o sueltos y antelación mínima;
  - **«Más opciones» (plegado):** horarios del día completo, la mañana y la tarde; precio especial por tramo; descuento; hasta 3 extras; zona horaria.
- **Página pública `#/reservar-dias`** (maqueta 1):
  - calendario: blanco = libre, rojo = ocupado, medio rojo = media jornada libre, gris = no disponible;
  - se elige el primer y el último día, o días sueltos, o mañana/tarde;
  - si hay un día ocupado en medio, no deja elegirlo y explica por qué;
  - barra fija con el total al momento: «3 días · 2 personas · 606 €», con el desglose;
  - lo elegido viaja en el enlace: se conserva al iniciar sesión y se puede compartir.
- **«Mi agenda» del freelance** (maqueta 2):
  - mes y lista; los días confirmados se bloquean solos;
  - un toque bloquea o desbloquea un día; «Bloquear varios días…» para vacaciones, sin explicar el motivo;
  - al tocar un día se ve quién viene (cliente, servicio, personas, notas, estado del pago);
  - **las solicitudes** se ven en amarillo, con «Confirmar», «Rechazar» y el aviso de qué otra solicitud se rechazará sola;
  - **«Horario y temporadas»:** días que trabaja, temporadas cerradas y zona horaria.
- **Solicitar, confirmar y bloquear:**
  - **«Bajo petición»** (por defecto): la solicitud no bloquea nada; los días siguen en blanco y pueden llegar otras.
  - **Al confirmar, en una sola operación:**
    - se bloquean los días;
    - el cliente recibe el aviso y, si se cobra online, el enlace de pago con su plazo;
    - las solicitudes que se solapan se rechazan solas con el correo «Esas fechas ya no están disponibles. Mira otras fechas de…» y un enlace a su calendario.
  - **Impago, rechazo, caducidad o cancelación:** los días se liberan solos y se aplica la devolución de la Fase 2.
  - **«Pago al reservar»:** los días se guardan mientras se paga (15 min) y se confirman al pagar.
- **En la lista de servicios** del freelance, la tarjeta dice «Por días…» con «Ver como cliente» y «Mi agenda», sin botones de salidas. En el motor de reservas, el servicio lleva a su calendario.

## A4 · Común
- **Privacidad:** la API pública (`/api/agenda/public`) solo devuelve una palabra por día: libre, ocupado, mañana, tarde o no disponible. Nunca nombres, motivos, horas ni referencias (comprobado).
- **Exportación de datos:** nuevo CSV «Agenda» en Herramientas, con los bloques, las horas locales, la zona horaria, la reserva, la nota privada y el estado.
- **Avisos:** se reutilizan los correos de solicitud enviada, confirmada y rechazada, los recordatorios y la agenda de mañana. Nuevo: el rechazo por fechas ya ocupadas, en los 10 idiomas.
- **Rendimiento:** un mes de calendario público o de agenda con 500 recursos y 15.000 bloques en la base responde en menos de 300 ms (prueba automática).
- **Plan:** «Servicios por días y medias jornadas con calendario» (`agenda_days`) va en «Motor de reservas» y «Pro». Sin esa función, el servidor rechaza crear un servicio por días.

## Migración `migrate_v50_44` (solo añade)
- **Tablas nuevas:** `resources`, `resource_hours`, `resource_closures`, `resource_blocks` y `booking_days`, con sus índices.
- **Columnas nuevas:**
  - `provider_services`: `booking_unit` (por defecto `slot`), `unit_rules`, `pricing` y `timezone`;
  - `bookings`: `date_to` y `days_mode`.
- **Planes:** se añade `agenda_days` a «Motor de reservas» y «Pro».
- Los servicios y las salidas que ya existen funcionan exactamente igual.

## Estado

| Punto | Estado |
|---|---|
| A1 · Revisión, diseño y maquetas | Completado (aprobado el 12/10/2026) |
| Motor común: recursos, bloques, sin solapes, zona horaria e índices | Nuevo |
| A2.1 Servicio «Por días» con tarifas, tramos, extras, mínimo/máximo, continuo o suelto y antelación | Nuevo |
| A2.1 Medio día con horarios y precio propios; día medio rojo | Nuevo |
| A2.1 Etiqueta «A elegir fechas» en Experiencias | **Parcial:** en la página del servicio y en el motor de reservas; en el listado de Experiencias llega con el bloque B |
| A2.2 Agenda del freelance: horario, temporadas, bloqueos, detalle y vista lista | Nuevo |
| A2.2 Sincronización con su calendario (iCal privado de salida) | Ya estaba (Fase 6) |
| A2.3 Calendario público, selección y resumen al momento | Nuevo |
| A2.4 Solicitar, confirmar con rechazo automático, liberar por impago o cancelación, «Pago al reservar» | Nuevo |
| A4.1 Avisos de solicitud, confirmación, rechazo y recordatorios | Completado (correos existentes y nuevo rechazo por fechas ocupadas) |
| A4.1 «Solicitud a punto de caducar» y push | **Pendiente** (v50.45; para el push, ver «Pendiente de decisión») |
| A4.2 Exportación de la agenda | Nuevo |
| A4.3 Privacidad del calendario público | Nuevo |
| A4.4 Asistente «Convertir en curso de varios días» | **Pendiente** (v50.45, con los cursos) |
| A4.5 Rendimiento ≤ 300 ms | Nuevo (prueba automática) |
| A3 Cursos, instructores y barcos, planning y vista por recursos | **Pendiente** (v50.45) |

## Pendiente de decisión
- **Push (Web Push):**
  - el cifrado de los avisos push necesita una librería que hoy no usa el servidor (`cryptography`);
  - **propuesta:** añadirla a `requirements.txt` en la v50.45. ¿De acuerdo?
- **Horas de las reservas por días en los recordatorios y en la política de cancelación:** hoy se calculan con la hora del servidor (en España). Para un servicio en México hay unas horas de diferencia.
  - **propuesta:** pasar todos esos cálculos a la zona del servicio en la v50.45.

## Cómo se probó
- **`tests/test_v50_44_agenda.py`, 12 pruebas** sobre una copia del catálogo de demostración, con el simulador de Stripe:
  - **motor:** México y España, cambio de hora (25 y 23 horas), 29 de febrero, fin de mes;
  - **precios:** el ejemplo de la maqueta da 606 €; tramos con descuento; por persona; media jornada;
  - **estados del día:** antelación, semana habitual, temporadas cerradas y medias jornadas;
  - **API pública** sin nombres ni motivos;
  - **solicitudes:** una solicitud no bloquea; confirmar bloquea y rechaza las solapadas con su correo y enlace;
  - **impago:** los días se liberan;
  - **dos confirmaciones simultáneas:** solo una gana;
  - **«Pago al reservar»:** guarda los días y se confirma al pagar;
  - **medias jornadas;**
  - **permisos:** buceador, otro freelance;
  - **plan:** sin la función, no se puede crear un servicio por días;
  - **exportación;**
  - **rendimiento.**
- **`tests/e2e_agenda.py`, 35/35 en Chromium, en ordenador y en móvil:**
  - lunes a miércoles con 2 personas y fotos: «3 días · 2 personas · 606 €»;
  - un día ocupado en medio no se puede elegir;
  - sin sesión pide iniciarla y conserva los días;
  - la segunda solicitud entra;
  - en «Mi agenda», el aviso y la confirmación con resumen; la otra se rechaza sola con su correo;
  - el público ve los días en rojo;
  - el formulario tiene «Unidad de reserva»;
  - sin desbordamiento ni errores.
- **Textos en los 10 idiomas** (126 textos, 34 patrones y 1 texto de correo). El recolector, en inglés, ya no encuentra textos sin traducir en las pantallas nuevas.
- **Batería completa:** 182 pruebas de servidor correctas; recorridos anteriores 35/35, 31/31 y 26/26; `e2e_walk.py` sin errores.
- **Capturas** en `docs/capturas/agenda-v50-44/`.
