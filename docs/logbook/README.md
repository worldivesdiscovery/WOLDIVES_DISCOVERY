# Log Book con el componente «Dive Logbook» (v50.57)

Encargo del 15/10/2026, texto completo en `docs/encargos/encargo-logbook-15-10-2026.md`. El componente es el del zip
del titular (`public/lib/logbook/`, origen y licencias en su `LEEME.md`); aquí se ha construido lo que el encargo pedía
alrededor: el servidor, la página de la web, el panel del centro y las pruebas.

Cada punto lleva su estado: **Ya estaba**, **Completado**, **Nuevo** o **Pendiente de decisión**.

| Punto del encargo | Estado | Qué hay |
|---|---|---|
| Vista clásica integrada en la web (letra y colores de la web, solo `--dlc-accent`) | **Nuevo** | La lista va dentro de «Log Book» (Mi cuenta). Solo se fija `--dlc-accent` al azul océano de la web; letra Inter, la de toda la web. Probado en escritorio y móvil: misma letra, acento `rgb(7, 104, 152)` y nada se sale de la pantalla |
| Vista pasaporte «que se gana» (QR de un centro, enlace de un centro, 5 toques) | **Ya estaba** en el componente; **Nuevo** lo que llega del servidor | El icono sale en gris y explica cómo se desbloquea. Los dos primeros caminos los da el servidor (abajo); el truco de los 5 toques es del componente y se queda así |
| 1 · Guardar el logbook en la cuenta | **Nuevo** | `GET /api/logbook` → el componente; cada `logbook:change` → `PUT /api/logbook`. Clave local distinta por cuenta (`wd-logbook-<huella>`) que se borra al cerrar la sesión |
| 2 · QR de inmersión del centro | **Nuevo** | Token de un solo uso (`/scan/d/<token>`), inicio de sesión y vuelta, sin duplicar, datos oficiales guardados aparte y el servidor rechaza cualquier cambio en los campos bloqueados |
| 3 · Buddies | **Nuevo** | URL pública no adivinable (`/buddy/<código>`), amistad en los dos sentidos, «Ahora sois buddies», `lb.setFriends()` al cargar |
| 4 · Registro con enlace de centro | **Nuevo** | `/registro?centro=<slug>` guarda el centro en la cuenta; el Log Book pone su logo en la portada (`lb.setCover`), lo que desbloquea el pasaporte. CORS no hace falta: los logos se sirven desde la propia web |
| 5 · Panel del centro (mínimo) | **Nuevo** | Pestaña «Logbook y pasaporte»: logo y nombre de la portada, crear inmersiones con sus QR (en pantalla uno tras otro, «Otro QR» o PDF para imprimir) y copiar el enlace de invitación |
| Colores del pasaporte | **Pendiente de decisión** | El encargo dejó el hueco «[Pegar aquí el código copiado desde personalizar.html → "Copiar código"]» sin el código. Mientras tanto, el pasaporte usa los colores de fábrica del componente (tapa azul marino, dorado, papel crema). Pegar el código lo cambia sin tocar nada más |
| «y más adelante en la app» | **Completado** en lo que ya existía | El modo app abre la misma página de Log Book. Su pestaña «Buddies» (que decía «todavía no existe») enseña ahora tu QR y tus buddies; los grupos y «¿Buceamos?» siguen pendientes de su propio encargo |

## Cómo funciona

**Archivos**
- `public/lib/logbook/`: el componente sin cambios (salvo las fuentes, servidas desde la web), el mapa (`land-50m.json`)
  y las fuentes. Se descargan solo al abrir el Log Book.
- `app/wod/logbook.py`: las reglas sin servidor (limpieza del libro, datos oficiales, comprobación de lo bloqueado, validación
  de la inmersión del centro, saneado de logos SVG).
- `app/server.py`: tablas, `GET/PUT /api/logbook`, `/api/logbook/claim`, `/api/buddies`, `/api/logbook/center-link`,
  `/api/center/logbook…`, y las redirecciones `/scan/d/…`, `/buddy/…` y `/registro?centro=…`.
- `public/js/world-dives-v8.js`: `renderLogbook` (la página), `renderScanDive`, `renderBuddyLink`, el registro con
  invitación y `renderCenterLogbook` (el panel del centro). `public/js/wd-app.js`: la pestaña «Buddies» de la app.

**Guardado.** El libro del componente se guarda **cifrado** en la cuenta, con un número de versión. La página manda los
cambios 0,7 s después del último (`X-Logbook-Version`). Si otro dispositivo guardó antes (409), une los cambios
inmersión por inmersión: lo cambiado solo aquí se queda, una inmersión nueva va a la siguiente página libre y, si los dos
cambiaron la misma, se queda la del otro dispositivo y se avisa. Sin conexión, lo cambiado se guarda en este
dispositivo y sube al volver la conexión o al abrir de nuevo el Log Book. Al volver a la pestaña, la página trae lo que
otro dispositivo haya guardado. La vista (lista o pasaporte) es de cada dispositivo: la lista por defecto.

**Lo de antes no se pierde.** Las inmersiones apuntadas en el Log Book anterior y las de las reservas completadas
entran en el libro la primera vez; las que se apuntan en el libro se guardan también como filas (puntos, app y
exportaciones siguen funcionando).

**Inmersión verificada.** El centro registra la inmersión una vez (`center_dives`); cada QR es un token aleatorio de un
solo uso (se guarda su huella SHA-256 y, cifrado, el propio token para reimprimirlo), caduca a los 90 días. Al
escanearlo, el servidor asocia la inmersión a la cuenta (`logbook_claims`); escanear otra vez (ese QR u otro de la misma
inmersión) no la duplica, y un QR ya usado por otro buceador se rechaza. La página llama a `lb.addDiveFromCenter()`.

**Lo bloqueado se comprueba en el servidor.** En cada `PUT`, `check_verified` compara cada inmersión marcada como
verificada con los datos oficiales del centro: no se puede marcar como verificada una inmersión que no se escaneó, ni
duplicarla, ni moverla de página, ni cambiar fecha, lugar, país, centro, posición o instructor, ni la lista de campos
bloqueados. Si algo no cuadra: 409, la página vuelve a lo que hay en la cuenta y queda registrado
(`logbook_locked_refused`). La antigua `/api/logbook/update` tampoco deja cambiarlos. Borrar una inmersión verificada sí
se puede (es el libro del buceador): vuelve escaneando su QR.

**Buddies.** Cada cuenta tiene un código aleatorio (`buddy_code`, no adivinable). Su URL va en el QR del pasaporte
(imagen hecha por el generador de QR de la web, sin librerías externas). Abrirla con sesión crea la amistad en los dos
sentidos; tu propio QR no te añade a ti mismo. Al componente solo le llega el nombre y una referencia (nunca el id ni el
correo).

**Centro de la invitación.** `/registro?centro=<slug>` lleva al registro de buceador con el aviso «Invitación de …». Al
crear la cuenta se guarda el centro; quien ya tenía cuenta lo une al abrir el enlace (si aún no tenía centro). La portada
solo puede llevar el logo de ese centro: el servidor corrige cualquier otro. El buceador puede volver a la portada
clásica. Los logos SVG se aceptan solo con formas (sin código, enlaces externos ni entidades).

**Permisos del equipo del centro.** Crear inmersiones y QR: perfil con «check-in». Logo y nombre de la portada: perfil
con «centro». El enlace de invitación lo ve todo el equipo.

**Privacidad.** El libro, sus inmersiones verificadas y los buddies salen en «Descargar mis datos» y se borran al
eliminar la cuenta. La copia local del componente se borra al cerrar la sesión.

## Criterios de aceptación y sus pruebas

| Criterio | Prueba |
|---|---|
| La lista se ve integrada en escritorio y móvil, con nuestra tipografía | Navegador, 1: letra igual a la de la web, acento de la web, sin salirse de la pantalla (escritorio 1366 px y móvil 390 px) |
| Usuario nuevo: icono del pasaporte en gris; al pulsarlo sale la explicación y no se abre | Navegador, 2 |
| Escanear el QR de una inmersión la añade verificada y desbloquea; otra vez no la duplica | Navegador, 3 (el QR se lee con OpenCV, como un móvil; el mismo QR y el otro QR de la misma inmersión no duplican) y servidor `test_3` |
| Registrarse con el enlace de un centro pone su logo en la portada y desbloquea | Navegador, 4 (logo PNG transparente subido por el centro) y servidor `test_7` |
| Escanear el QR de otro buceador lo añade como amigo y aparece en «Compañero» | Navegador, 5 (QR del pasaporte leído con OpenCV; amistad en los dos sentidos) y servidor `test_6` |
| Los datos se conservan al cambiar de dispositivo y son los mismos en las dos vistas | Navegador, 6 (inmersión apuntada en el ordenador, vista en el pasaporte del móvil, cambiada allí y vista en la lista del ordenador) y servidor `test_1` |
| Los campos bloqueados no se pueden cambiar ni manipulando la petición | Navegador, 7 (PUT hecho a mano y cambio forzado en el componente: 409 y vuelve lo del centro) y servidor `test_4` (9 intentos distintos) |

- `tests/test_v50_57_logbook.py` (servidor, 9 pruebas).
- `tests/navegador/e2e_v50_57_logbook.py` (navegador, 58 comprobaciones sobre una copia de la demo; usa las cuentas de la
  demo, por eso no va en el zip de producción). Pasada final con la versión entregada: **58/58**. Capturas (13) y el
  resultado de esa pasada (`recorrido.txt`) en `docs/capturas/v50.57/logbook/`.

## Decisiones tomadas por el camino (se pueden cambiar)

- **Campos bloqueados**: los del componente (fecha, lugar, país, centro, posición GPS e instructor). El encargo nombra
  cinco; la posición también la registra el centro.
- **QR**: hasta 40 por inmersión al crearla y 200 en total; caducan a los 90 días.
- **Idiomas**: la lista, los avisos y los botones del componente salen en los 9 idiomas; lo que escribe el buceador o su
  centro no se traduce nunca. El pasaporte conserva sus rótulos bilingües (español e inglés), como un pasaporte.
- Las cuentas de centro y de profesional no se unen a otro centro con un enlace de invitación; un buceador que ya está
  unido a un centro lo conserva.

## Lo que no ha podido descargarse desde este entorno

El componente trae por defecto el mapa de `cdn.jsdelivr.net`, la librería de QR de `cdnjs.cloudflare.com` y las fuentes
de Google Fonts. Desde el entorno de trabajo, `cdn.jsdelivr.net` y `cdnjs.cloudflare.com` no respondieron (sin
conexión) y `github.com` devolvió 403 (proxy). No se ha intentado saltar ese bloqueo: el mapa (`world-atlas` 2.0.2) y las
fuentes (`@fontsource/*` 5.3.0) se han tomado de sus paquetes oficiales del registro de npm, y el QR lo hace el generador
de la propia web. En producción la web no necesita ninguno de esos servidores (la política de seguridad solo permite el
propio dominio).
