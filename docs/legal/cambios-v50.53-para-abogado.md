# Cambios en los textos legales (v50.53) · para la revisión del abogado

Fecha: 14/10/2026. Motivo: la revisión del titular sobre la demo (ubicación para ordenar por cercanía, Top 10 y fotos
de los servicios). **En esta versión no se ha cambiado ningún texto publicado** (`app/legal/`): lo que sigue son
propuestas, en castellano, marcadas como **Pendiente de decisión**. Cuando el abogado las apruebe se traducen a los 8
idiomas y se publican como versión nueva de cada documento, como siempre.

## 1. Ubicación (política de privacidad §2) — Pendiente de decisión

**Lo que hace la web desde la v50.53** (comprobado con pruebas: `tests/test_v50_53_cercania.py` y el recorrido
`tests/navegador/e2e_v50_53.py`):

- El permiso se pide **solo** cuando la persona pulsa «Usar mi ubicación», «Cerca de mí» o «Activar ubicación», o
  cuando entra en el **Top 10 «cerca de ti»**, que la necesita. **Nunca al abrir la web.**
- Si la persona ya dio permiso antes en ese navegador, «Puntos de buceo», «Explorar» y el Top 10 la usan para ordenar
  sin volver a preguntar (el permiso lo gestiona el navegador y se retira en sus ajustes).
- La posición se **redondea a unos 1 km** en el navegador antes de enviarse; el servidor la usa para ordenar y **no la
  guarda, no la registra** (el registro de accesos no guarda la cadena de consulta) **y no la asocia a la cuenta**.
- Si la persona **deniega** el permiso, el navegador recuerda solo eso (clave `wd_loc` = «denied») para no volver a
  preguntar. No guarda ninguna posición ni crea un perfil.
- En el Top 10, si la persona **elige a mano** una zona o una localidad, se recuerda esa elección (`wd_top10`): el
  nombre de la zona o el centro de la localidad, nunca su posición.

**Texto actual** (`app/legal/es/privacidad.md`): «Ubicación: si pulsas «Usar mi ubicación», tu navegador nos envía tus
coordenadas solo para calcular los puntos cercanos. No las guardamos.» No recoge que se pida al entrar en el Top 10, que
se use un permiso ya concedido sin pulsar el botón ni que se recuerde la negativa.

**Texto propuesto:**

> **Ubicación:** solo la usamos para ordenar resultados por cercanía (puntos de buceo, mapa y Top 10). Tu navegador te
> pide permiso cuando pulsas «Usar mi ubicación» o «Cerca de mí», o cuando entras en el Top 10 «cerca de ti»; nunca al
> abrir la web. Si ya diste permiso en este navegador, la usamos para ordenar sin volver a preguntarte; puedes retirarlo
> en los ajustes del navegador. Antes de enviarla la redondeamos a aproximadamente 1 km. No la guardamos, no la
> registramos y no la asociamos a tu cuenta. Si no das permiso, tu navegador recuerda solo eso, para no volver a
> preguntarte.

## 2. Almacenamiento en el navegador (política de cookies) — Pendiente de decisión

**Texto actual** de la fila `wd_top10`: «Recordar la ubicación y el radio que elegiste en el Top 10». Ya no es exacto
(no se guarda el radio ni la ubicación del GPS) y falta `wd_loc`.

**Filas propuestas:**

| Nombre | Tipo | Para qué sirve | Duración |
|---|---|---|---|
| wd_top10 | Almacenamiento local | Recordar la zona o la localidad que elegiste en el Top 10 (no tu ubicación) | Hasta que la borres o elijas otra |
| wd_loc | Almacenamiento local | Recordar que no quieres compartir tu ubicación, para no volver a preguntarte | Hasta que lo borres o des permiso |

Inventario técnico al día en `docs/legal/cookies-terceros.md`.

## 3. Fotos de los servicios (condiciones para centros y profesionales) — Pendiente de decisión

**Lo que hace la web desde la v50.53:** al subir una foto propia para un servicio, el centro o freelance debe marcar
«Declaro que tengo los derechos de esta imagen y que las personas que aparecen han dado su consentimiento» (sin la
casilla el servidor no la acepta). Se guarda **quién** la subió y **cuándo** (y la fecha de la declaración). La foto se
re-codifica: se eliminan los datos EXIF, incluida la posición GPS de la cámara. La administración puede **retirar** una
foto no adecuada indicando el motivo, que ve el centro; el servicio vuelve a la foto de su plantilla y el archivo se
borra. Una foto propia que se deja de usar se borra del disco.

**Texto propuesto** (nuevo punto en `app/legal/es/centros.md`):

> **Fotos de tus servicios.** Las fotos que subas deben ser tuyas o tener licencia para usarlas, y las personas que
> aparezcan deben haber dado su consentimiento; lo declaras al subir cada una. Guardamos quién subió cada foto y cuándo,
> y les quitamos los datos ocultos de la cámara (incluida la ubicación). Podemos retirar una foto que no cumpla estas
> condiciones; te diremos el motivo y tu servicio mostrará la foto de su plantilla.

## Preguntas para el abogado

1. **Ubicación al entrar en el Top 10.** El encargo lo pide expresamente («al entrar en una sección que la necesita»).
   ¿Basta el aviso del propio navegador más el texto propuesto, o hace falta una pantalla previa propia antes de que el
   navegador pregunte?
2. **Permiso ya concedido.** ¿Es correcto usar para ordenar, sin pulsar el botón, un permiso que la persona ya dio en ese
   navegador (redondeado a 1 km, no se guarda)?
3. **`wd_loc` y `wd_top10`.** ¿Los consideras almacenamiento técnico exento (art. 22.2 LSSI-CE, guía de la AEPD de
   2023), como el resto de claves?
4. **Fotos.** ¿Es suficiente la declaración con casilla (más el registro de quién y cuándo) para las fotos con
   personas, o conviene pedir algo más a los centros (por ejemplo, conservar ellos los consentimientos firmados)?
