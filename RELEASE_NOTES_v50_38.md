# WORLDIVES DISCOVERY v50.38: infraestructura, documentos legales y pasada final de idiomas (Fases 7 y 8)

## 1 · Base de datos y esquema (7.1, 7.2)
- **Esquema completo en el código** (`BASE_SCHEMA`). Una instalación limpia, sin ningún `.sqlite3`, crea todas las tablas. Una prueba compara una instalación limpia con una base antigua migrada: mismas tablas y mismas columnas.
- **Arranque sin base:**
  - **en pruebas**, si no hay base se copia el catálogo de demostración (`data/demo/catalogo-demo.sqlite3`);
  - **en producción**, o con `WOD_EMPTY_DB=1`, arranca vacía.
- **`tools/crear_base_produccion.py`:** crea la base de producción **limpia**, sin personas, centros, reservas, sesiones, correos ni pagos. Conserva los 280 puntos con sus textos propios en 10 idiomas y los datos legales del titular. Además:
  - nunca sobrescribe una base que ya existe;
  - crea el archivo con permisos `600`.
- **`.gitignore`:** `data/*.sqlite3`, copias, teselas y correos de prueba quedan fuera del repositorio. El catálogo de demostración pasa a `data/demo/`.
- **Migración `migrate_v50_38` (solo añade):** textos de los puntos que faltaban y `content_reports.lang`. Los índices se crean después de las migraciones, así que una base antigua ya no falla.

## 2 · Despliegue (7.3)
- **`deploy/`:**
  - Caddy (HTTPS automático) o nginx;
  - servicio systemd de producción y de pruebas;
  - script de copia externa.
- **Archivo `.env`:** el servidor lo lee él mismo, con comentarios al final de línea. Si una variable ya está en el entorno, gana esa. La clave de ArcGIS y los secretos solo van ahí, nunca en el código.
- **Avisos al arrancar en producción** si falta algo: dominio, Stripe y su webhook de Connect, correo, mapa base (PMTiles), clave de satélite, copias. Corregido: el aviso del webhook de Connect no aparecía cuando faltaba la clave de ArcGIS.
- **`docs/despliegue.md`:** guía paso a paso (servidor, usuario, `.env`, HTTPS, DNS del correo, Stripe, copias, actualización y vuelta atrás).

## 3 · Copias de seguridad (7.4)
- **Copias automáticas de la base:**
  - una cada hora y una diaria de los archivos subidos;
  - con la API de copia de SQLite, sin parar la web, comprimidas;
  - con `quick_check` y rotación configurable (horarias, diarias y mensuales).
- **Copia externa:** `WOD_BACKUP_COMMAND` recibe la ruta de cada copia. Hay un ejemplo con `rclone` en `deploy/backup-externo.sh`.
- **Comandos:**
  - `--backup-now` hace una copia al momento;
  - `--verify-backup <archivo>` comprueba una copia;
  - `--restore <archivo> --yes` restaura. Antes guarda la base actual como `.antes-de-restaurar-…`.
- **Las copias locales no están cifradas.** Si se quieren cifradas, se cifran en el destino externo (por ejemplo, con `rclone crypt`). La política de privacidad las llamaba «cifradas»: ver Pendiente de decisión.

## 4 · Monitorización y avisos (7.5)
- **Administración → Operación:**
  - salud del servidor: base, `quick_check`, espacio en disco, cola de correo, última copia, errores, uso del satélite;
  - aviso de mantenimiento o de incidencia en toda la web, con caducidad y email opcional a los centros.
- Las alertas por email de errores repetidos ya existían y se mantienen.

## 5 · Rendimiento (7.6)
- **`tools/prueba_carga.py`.** Resultados en un servidor de 4 núcleos, con el cliente en la misma máquina:
  - **1 proceso:** 96 peticiones/s con 50 usuarios (mediana 5 ms);
  - **4 procesos:** 390 peticiones/s con 200 usuarios (mediana 5 ms).
- En `docs/despliegue.md`, cuándo conviene pasar a PostgreSQL.
- **Pendiente:** repetir la prueba en el servidor real.

## 6 · Documentos en `docs/legal/` (Fase 8)
Los 18 documentos del encargo están redactados a partir del código real, con [PENDIENTE ABOGADO], [PENDIENTE TITULAR] o [PENDIENTE] donde hace falta una decisión.

| Documento | Archivo |
|---|---|
| 1. Inventario (Parte 1 verificada y completada) | `inventario.md` |
| 2. Aviso legal | `aviso-legal.md` |
| 3. Condiciones para buceadores | `condiciones-buceadores.md` |
| 4. Condiciones para centros (planes, degradación, datos, Stripe, reseñas, orden, 15 días, DAC7, logo) | `condiciones-centros.md` |
| 5. Anexo de encargado del tratamiento | `anexo-encargado-tratamiento.md` |
| 6. Política de privacidad por rol | `politica-privacidad.md` |
| 7. Cookies y terceros | `cookies-terceros.md` |
| 8. Normas de reseñas | `normas-resenas.md` |
| 9. Reglas de los Puntos | `reglas-puntos.md` |
| 10. Declaración de accesibilidad | `declaracion-accesibilidad.md` |
| 11. Registro de actividades de tratamiento | `registro-actividades-tratamiento.md` |
| 12. Procedimiento de brechas (AEPD en 72 h) | `procedimiento-brechas.md` |
| 13. Procedimiento de denuncias | `procedimiento-denuncias.md` |
| 14. Preguntas para el abogado | `preguntas-abogado.md` |
| 15. Preguntas para la gestoría | `preguntas-gestoria.md` |
| 16. Lista de lanzamiento | `lista-lanzamiento.md` |
| 17. Guía de verificación de centros | `guia-verificacion-centros.md` |
| 18. Guía de operación | `guia-operacion.md` |

Cada ficha termina con los **desajustes entre el texto publicado y el código**. Los que eran errores del código se han corregido en esta versión (apartado 8). Los demás están en «Pendiente de decisión» o en las preguntas para el abogado.

## 7 · Pasada final de idiomas (Fase 1D, cierre)
- **Textos legales en los 10 idiomas:** los 14 documentos de la web están en fr, de, it, pt, nl, pl, ru y zh, además de es y en. Una prueba comprueba, para cada documento y cada idioma, que tiene los mismos datos variables, los mismos enlaces internos, los mismos títulos y las mismas filas de tabla que el castellano. Las traducciones muestran «en caso de discrepancia prevalece el castellano».
- **Correos en los 9 idiomas:** los 449 textos de correo están traducidos. La prueba saca los textos del propio código, así que un texto nuevo sin traducir hace fallar la suite.
- **Web:** los textos añadidos desde v50.34 (recogidos visitando todas las pantallas con los 5 roles y del código) están en los 9 paquetes (743). Corregida una traducción errónea: «Funciones» del menú de Administración.

## 8 · Correcciones de esta versión
- **Denuncias (DSA):**
  - nombre y email obligatorios (art. 16.2), en el servidor y en los dos formularios;
  - los motivos de la decisión son obligatorios;
  - el correo al denunciante va en su idioma;
  - los dos correos de decisión mencionan los órganos de resolución extrajudicial y los tribunales (arts. 20 y 21).
  - En Administración, la ventana de resolución avisa de que «Retirar o corregir» solo oculta automáticamente las reseñas: fichas, fotos, promociones y perfiles se corrigen antes desde su pestaña.
- **Reseñas:**
  - una reseña ocultada por moderación ya no vuelve a publicarse cuando su autor la edita;
  - las cuentas freelance no pueden reseñar centros (las de centro y administración ya no podían);
  - la API solo devuelve el nombre de pila del autor.
- **Puntos:**
  - en el Log Book, como mucho 4 inmersiones del mismo día dan puntos, y al borrar una inmersión se descuentan sus puntos;
  - con los Puntos desactivados, los códigos ya emitidos se pueden validar en el centro y anular, como prometen las reglas (30 días de aviso).
- **Altas de profesionales:**
  - al rechazar una verificación, la persona recibe un correo en su idioma, sin la nota interna;
  - el texto de ayuda ya no habla de «sugerencia por teléfono».
- **Orden de resultados:** enlace «¿Cómo ordenamos?» junto al selector de orden en Centros y Puntos (P2B art. 5).
- **Ficha de centro:** «Reservar con…» solo aparece si el centro tiene actividades publicadas.
- **Mapa del editor de centros (Administración):** usa el mismo mapa base que el resto de la web, ya no las teselas públicas de OpenStreetMap.
- **Accesibilidad:**
  - enlace «Saltar al contenido»;
  - el panel ya no tiene un `<main>` dentro de otro.
- **Experiencias:** error de JavaScript al salir de la página antes de que terminara de cargar.

## Estado de las Fases 7 y 8

| Punto | Estado |
|---|---|
| 7.1 Esquema completo, base limpia, herramienta de producción | Nuevo |
| 7.2 `.gitignore` | Completado |
| 7.3 Despliegue | Nuevo |
| 7.4 Copias | Nuevo |
| 7.5 Monitorización y avisos | Completado (las alertas por email ya estaban) |
| 7.6 Rendimiento | Nuevo; prueba en el servidor real: Pendiente |
| 8.1–8.18 Documentos | Nuevo (8.1 completa el diagnóstico de la Parte 1) |
| 1D Correos, textos legales y textos nuevos en 9 idiomas | Completado |

## Pendiente de decisión
- **Duración de la sesión.** El código cierra la sesión 8 horas después de entrar aunque se esté usando. Los textos dicen «8 horas sin actividad». ¿Se cambia el código (8 horas sin actividad, con un máximo) o el texto?
- **Copias cifradas.** La política de privacidad dice «cifradas». O se cifran en el destino externo (`rclone crypt`, recomendado) o se cambia el texto.
- **Logotipos externos.** Un centro puede poner su logo como enlace `https://` externo, y el navegador del visitante lo carga desde ese servidor sin que el visitante haga clic. ¿Solo logos subidos a WORLDIVES (recomendado) o se avisa en cookies?
- **Etiqueta «✓ Inmersión verificada».** Se puede reseñar con una reserva pagada o confirmada, antes de la actividad. ¿Se exige la reserva completada o se cambia la etiqueta a «Reserva verificada»? (También está en las preguntas para el abogado.)
- **Equipo y documentos de clientes.** Recepción e instructor ven los documentos de los clientes con las mismas reglas que el propietario. ¿Se restringe a propietario y recepción?
- **Cuentas profesionales.** Las cuentas de centro y freelance no se pueden borrar desde la web (hay que escribir). ¿Se añade el borrado con un plazo para las reservas pendientes?
- **Herramientas de puntos en Administración:** devolver puntos cuando un centro no cumple una ventaja, y anularlos por fraude. Hoy no hay pantalla para hacerlo.
- **Inglés oficial.** Cuatro textos en inglés dicen «the Spanish version prevails». ¿Se quita (el inglés es oficial) o el inglés pasa a ser traducción?
- **Precios de los planes, etiqueta «Destacado/Patrocinado» y proveedor de email:** siguen pendientes de las fases anteriores.

## Para abogado / gestoría
- Todo está en `docs/legal/preguntas-abogado.md` y `docs/legal/preguntas-gestoria.md`. En esta versión se han añadido o actualizado:
  - la prevalencia del castellano en los textos en inglés;
  - la declaración de motivos de la DSA (lo que ya incluyen los correos);
  - las denuncias sin nombre (excepción del art. 16.2.c para abuso sexual de menores);
  - las reseñas verificadas.
- **Traducciones de los textos legales:** están hechas para que el texto se entienda en cada idioma. Antes de publicar, un abogado o traductor jurídico debe revisar al menos la versión en inglés (oficial). Los nombres de botones citados en los textos traducidos deben coincidir con los de la web en cada idioma.
- **Accesibilidad:** está pendiente una auditoría WCAG 2.1 AA formal y una prueba con lector de pantalla. La obligación según la Ley 11/2023 y la Acta Europea de Accesibilidad está marcada [PENDIENTE ABOGADO].

## Cómo se probó
- **Suite completa: 147 pruebas correctas** (`cd tests && python3 -m unittest discover -p 'test_*.py'`).
  - **Nuevas de la Fase 7** (`test_phase7_infra.py`, 7 pruebas): instalación limpia igual que la migrada, arranque sin base, base de producción sin datos personales, `.env` con comentarios, copias automáticas, rotación, verificación y restauración sobre una copia, copia externa, salud y aviso.
  - **Idiomas** (`test_phase8_languages.py`): textos legales de los 10 idiomas con la misma estructura, correos y textos de la web traducidos, documento traducido servido con la nota de prevalencia.
  - **Flujos que no tenían prueba** (`test_phase8_flows.py`, 4 pruebas): recuperación de contraseña de un solo uso que cierra las sesiones, cambio de contraseña que cierra las otras sesiones, cambio de email confirmado desde la dirección nueva, y precio de una experiencia × participantes con control de plazas y de quién paga.
  - **Correcciones** en las pruebas de las fases 1, 3, 5 y 6: denuncia sin nombre (rechazada), decisión sin motivos (rechazada), correo en francés con las vías de recurso, reseña oculta que no se republica, freelance sin reseñas, Log Book sin acumulación, códigos válidos con los Puntos desactivados, correo de rechazo sin la nota interna, solo el nombre de pila en las reseñas.
- **Navegador (Chromium):**
  - recorrido de todas las pantallas con los 5 roles sin errores de JavaScript, de CSP ni de servidor (`e2e_walk.py`);
  - `e2e_legal_catalog.py` 33/33, `e2e_centers.py` 32/32, `e2e_booking_modes.py` 35/35, `e2e_payments.py` 26/26, `e2e_points_email.py` 20/20, y `e2e_markers.py` sin errores.
- **Todas las pruebas usan copias temporales** del catálogo de demostración, nunca una base con datos reales.
