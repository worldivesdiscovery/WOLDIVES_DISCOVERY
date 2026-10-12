# WORLDIVES DISCOVERY v50.40: manifiesto de salida y descargo firmado (encargo 2, puntos 1 y 5)

## Qué había antes
- **Planning por salida:** hora, puntos, ocupación y la lista de personas, con «+ Reserva», «Crear cartel» y «Gestionar».
- **Por reserva:** la «Ficha del buceador» en PDF (una por reserva) y el correo de agenda de las 18:00 con el equipo pedido.
- **No existía:** barcos, guías por salida, grupos, ni un manifiesto con todos los buceadores de una salida.
- **No había descargos ni firmas.** Lo único parecido era la aceptación de las condiciones de reserva (`bookings.terms_version`).
- **Datos de salud:** no se guardan (Fase 1, G6), y así sigue.

## 1 · Manifiesto de salida (punto 1)
- **Botón «Manifiesto»** en cada salida del planning que tenga buceadores. Se abre `#/manifiesto?slot=…`, dentro del panel donde ya trabaja el centro.
- **Una fila por plaza:**
  - una reserva de 3 personas son 3 filas;
  - el titular lleva su nombre;
  - los acompañantes salen como «Acompañante de…», y el centro puede escribir su nombre;
  - cada fila lleva su nivel, Nitrox, alquiler y descargo firmado o sin firmar.
- **Barcos del centro, cada uno con su capacidad** (personas a bordo, buceadores y guías). Se crean y se editan desde el propio manifiesto («Barcos») y se pueden dejar «en uso» o no.
- **Grupos:**
  - cada grupo tiene barco y guía;
  - el guía es una persona del equipo (propietario o instructor, Fase 6.6) o un guía externo escrito a mano.
- **«Sugerir reparto» automático por nivel y titulación:**
  - **Nivel:** sale de la titulación de la ficha (sin titulación, inicial, avanzado, rescate, profesional, instructor).
  - **Grupos:** no se mezclan principiantes con buceadores experimentados, y las plazas de una misma reserva van juntas.
  - **Máximo por guía:** cada grupo tiene como mucho el máximo por guía.
  - **Barcos:** los grupos van a los barcos mientras caben.
  - **Confirmación previa** con un resumen: «Se repartirán 8 buceadores en 3 grupos… Los cambios hechos a mano se sustituirán», y cuántos grupos quedan sin guía o sin barco.
- **Mover a mano:** se arrastra en el ordenador; con el botón «Mover» en el móvil y con el teclado.
- **Máximo de buceadores por guía configurable** (4 por defecto), por centro o profesional.
- **Avisos visibles:**
  - grupo por encima del máximo;
  - grupo sin guía;
  - barco por encima de su capacidad;
  - buceadores sin grupo;
  - buceadores sin firmar el descargo.
- **Vista para imprimir (A4 limpio):** una tabla por grupo con nombre, nivel, alquiler, tallas, Nitrox, contacto de emergencia, descargo y una columna «A bordo» para marcar a mano. Sin menús ni colores.
- **Vista para el barco (móvil):** tarjetas por grupo con nombre, nivel, alquiler, tallas, Nitrox, teléfono y contacto de emergencia con enlace para llamar.
- **Privacidad:**
  - **Emergencia:** el contacto sale solo si el buceador lo ha compartido con el centro; si no, «No compartido».
  - **Tallas y teléfono:** solo con la ficha compartida o en un cliente propio del centro.
  - Son las mismas reglas que la ficha del buceador (G1/G5).
  - **Acompañantes:** sin datos personales más allá del nombre que escriba el centro.
- **Permisos:**
  - el propietario y recepción organizan;
  - el instructor solo lo ve;
  - otro centro, un buceador o una persona sin sesión no lo ven (403).

## 2 · Descargo de responsabilidad firmado (punto 5)
- **Panel → Herramientas → «Descargo de responsabilidad»:**
  - el centro o profesional escribe su propio texto;
  - cada vez que lo guarda se crea una **versión** nueva con su fecha;
  - lo ya firmado conserva el texto exacto que se firmó;
  - «Dejar de pedirlo» lo desactiva sin borrar firmas;
  - solo el propietario puede cambiarlo, con confirmación.
- **El buceador lo firma desde «Mi reserva»:**
  - lee el texto;
  - marca «He leído y acepto»;
  - escribe su nombre completo (nombre y apellidos);
  - dibuja su firma con el dedo o con el ratón.
  - Si van varios, cada persona firma su plaza.
- **En el check-in:** el centro abre la reserva en su dispositivo y cada buceador o acompañante firma en él («Firmar en el check-in»). Los instructores también pueden recoger firmas.
- **Lo que se guarda:**
  - versión y título;
  - el texto completo firmado;
  - nombre y trazos de la firma;
  - fecha y hora;
  - reserva y plaza;
  - si fue en «Mi reserva» o en el check-in;
  - quién lo registró;
  - la IP cifrada (hash) y el navegador.
- **PDF descargable** para el centro y para el buceador: la versión, el texto, la firma dibujada, el nombre, la fecha y la reserva. No lo ve nadie más.
- **El manifiesto marca quién ha firmado y quién no.**
- **Sin preguntas de salud.** El servidor rechaza cualquier pregunta (`questions`) mientras `WAIVER_HEALTH_QUESTIONS = False`. La tabla `waiver_templates` tiene ya la columna `questions`, preparada para cuando el abogado lo apruebe. El editor lo recuerda al centro.

## Migración `migrate_v50_40` (solo añade)
- **Tablas nuevas:**
  - `boats`
  - `slot_groups`
  - `manifest_entries`: incluye ya las columnas de presente, «no se presentó» y notas para el punto 6
  - `waiver_templates`
  - `waiver_signatures`
- **Columnas nuevas:** `centers.manifest_max_per_guide` y `users.manifest_max_per_guide`.
- No se borra nada.

## Estado

| Parte | Estado |
|---|---|
| 1. Manifiesto desde cada salida del planning | Nuevo |
| 1. Reparto por barco, guía y grupo | Nuevo |
| 1. Sugerencia automática por nivel y titulación; arrastrar y botones en el móvil | Nuevo |
| 1. Máximo por guía configurable y aviso | Nuevo |
| 1. Barcos con capacidad | Nuevo |
| 1. Vista para imprimir A4 y vista para el patrón | Nuevo |
| 1. Contacto de emergencia solo si se ha compartido | Completado (usa las reglas G1/G5 de la ficha del buceador) |
| 5. Descargo propio con versión y fecha | Nuevo |
| 5. Firma con casilla, nombre y firma dibujada, en «Mi reserva» o en el check-in | Nuevo |
| 5. Se guarda versión, fecha, hora y reserva; PDF para centro y buceador | Nuevo |
| 5. El manifiesto marca quién ha firmado | Nuevo |
| 5. Cuestionario médico | Pendiente de decisión (abogado); preparado y desactivado |

## Pendiente de decisión
- **Cuestionario médico o preguntas de salud en el descargo:** solo si el abogado lo aprueba. Está preparado y desactivado.
- **Plantilla de descargo:** cada centro escribe la suya. Si quieres ofrecer un texto base revisado por el abogado, se añade como «Usar el texto de ejemplo».
- **Niveles:** la correspondencia entre titulaciones y niveles sigue nombres habituales (PADI, SSI, CMAS, FEDAS). Si tu catálogo de titulaciones cambia, se ajusta en `app/wod/manifest.py`.

## Para el abogado
- **Firma dibujada como firma electrónica simple** (eIDAS): ¿basta con nombre, casilla, trazo, fecha, hora, IP en hash y texto exacto, o hace falta algo más (envío de copia por email, sellado de tiempo)?
- **Quién es responsable de los descargos y las firmas:** el centro, con WORLDIVES como encargado (anexo de encargado). Hay que fijar el plazo de conservación de las firmas (hoy se conservan con la reserva).
- **Menores:** no se registran, pero un acompañante podría ser menor. ¿Hace falta la firma del tutor?
- **Datos del manifiesto:** el contacto de emergencia solo con la ficha compartida, como hasta ahora. ¿Algo más en la política de privacidad?

## Cómo se probó
- **`tests/test_e2_p1_p5_manifest.py`, 6 pruebas:**
  - niveles por titulación;
  - reparto que no mezcla niveles, mantiene juntas las reservas, respeta el máximo y asigna guías y barcos;
  - filas del manifiesto, con emergencia y tallas solo si se han compartido;
  - barcos, grupos, máximo, avisos, nombres de acompañantes y quitar grupos;
  - permisos entre centros, de un buceador y de un instructor (solo lectura), con datos erróneos;
  - descargo con versiones, sin preguntas de salud;
  - firmas válidas y no válidas: sin casilla, nombre corto, trazo corto o fuera del recuadro, plaza inexistente, persona ajena, otro centro;
  - cambio de versión antes de firmar, firma única por plaza, firma en el check-in;
  - PDF solo para el buceador y el centro, y manifiesto marcado.
- **`tests/e2e_manifest.py`, 27/27 en navegador, en ordenador y en móvil:**
  - editor y publicación con confirmación;
  - botón «Manifiesto» en el planning;
  - reparto con confirmación;
  - arrastrar por encima del máximo con aviso;
  - guía externo;
  - vista para el barco con emergencia, tallas y Nitrox;
  - impresión A4 (captura y PDF);
  - firma real dibujada en «Mi reserva» en el móvil y en el check-in en el dispositivo del centro;
  - «Mover» en el móvil;
  - sin errores de JavaScript ni desbordamiento.
- **Capturas** en `docs/capturas/encargo2/punto1-5/`.
- **Suite completa: 159 pruebas correctas.**
