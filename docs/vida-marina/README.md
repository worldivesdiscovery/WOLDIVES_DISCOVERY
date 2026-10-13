# Vida marina y vídeos de la ruta (v50.50, revisado en v50.51)

Encargo «Vídeos enlazados y carrusel de vida marina en los pun## Qué ve el buceador en la ficha de un punto (v50.51)

La ficha tiene **la misma distribución, orden y aspecto que en la v50.49**: foto y datos del punto, descripción,
formación recomendada, fotos, **Recorrido virtual**, centros que bucean aquí y puntos cercanos. Lo nuevo va dentro de
ese orden, sin cambiar el aspecto:

1. **Vida marina en esta inmersión**, justo encima de «Recorrido virtual»: un título pequeño con el número de especies
   y una franja de fotos pequeñas y redondas (60 px en el ordenador, 52 px en el móvil) con el nombre común debajo.
   - Se mueve despacio y sin parar, en bucle, con los bordes difuminados.
   - Se para al pasar el ratón, al tocarla, con el teclado, con una especie abierta y fuera de la pantalla. En el
     móvil también se desliza con el dedo.
   - Se queda quieta si caben todas o si el teléfono u ordenador tiene «reducir movimiento» (entonces se desplaza a mano).
   - Van primero las especies de temporada y las habituales.
   - Si el punto no tiene especies, no aparece.
2. **Bocadillo de cada especie**: al pulsar una foto se abre junto a ella (en el móvil, un panel pequeño desde abajo),
   sin salir de la página: foto más grande, nombre común, nombre científico en cursiva, frecuencia en esta inmersión
   (Habitual, Ocasional o Rara), mejor época, dos o tres líneas de información y el crédito de la foto. Se cierra con
   la X, tocando fuera o con Esc; solo hay uno abierto; es un diálogo accesible con el teclado y el lector de pantalla.
3. **Recorrido virtual** («Ruta 360»), con el aspecto de siempre (tarjetas con el cuadro de 58 px y el botón).
   - Los **vídeos enlazados** aprobados por la administración salen aquí, con su miniatura dentro del cuadro y la
     etiqueta «360°» o «VR» si corresponde, el logotipo de la plataforma y quién lo aportó.
   - Si la plataforma deja insertar su reproductor: «Entrar en el recorrido» abre el visor del recorrido virtual, con
     el aviso de privacidad sobre la miniatura; el vídeo solo se carga al pulsar «Cargar vídeo».
   - Si no lo deja: «Abrir en …» en una pestaña nueva, con el icono de enlace externo.
   - Los recorridos antiguos (panorámicas, Street View) siguen saliendo igual que antes.
   - Sin nada que enseñar, el mensaje de siempre: «Este punto aún no tiene recorrido 360°…».

**Por qué «no se veía» en la v50.50:** el lanzador de pruebas conservaba la base de datos de la v50.49 si tenía menos
de 7 días, y esa base no traía especies vinculadas. Desde la v50.51 la demo se regenera también cuando cambia la
versión, y cada punto de los dos centros de la demo trae entre 8 y 15 especies.

ni «próximamente».

## Privacidad

- Hasta que se pulsa «Reproducir» no se carga nada de la plataforma: la miniatura está guardada en nuestro servidor.
- YouTube se carga en su modo de privacidad mejorada (`youtube-nocookie.com`) y Vimeo sin seguimiento (`dnt=1`).
- La política de seguridad del navegador (CSP) solo deja cargar los reproductores de las plataformas insertables.
  Esa lista sale de `app/wod/videos.py`.
- El aviso de cookies no cambia: la web sigue usando solo cookies técnicas.
- La política de cookies, en los 9 idiomas, dice qué plataformas reciben tu IP al pulsar «Reproducir».

## Plataformas

La lista está en `app/wod/videos.py` (`PLATFORMS`). Para añadir una plataforma se añade una entrada con:
- los dominios de sus enlaces;
- cómo se lee el identificador del vídeo en el enlace;
- la dirección de su reproductor, si tiene uno oficial que se pueda insertar.

| Plataforma | Se ve en la ficha | Título y miniatura |
|---|---|---|
| YouTube (normal, 360° y VR; también `youtu.be` y Shorts) | Sí, modo de privacidad mejorada | oEmbed y la imagen de vista previa de YouTube (la grande; si no hay, la normal sin las bandas negras) |
| Vimeo | Sí, sin seguimiento | oEmbed |
| Dailymotion | Sí | oEmbed |
| TikTok | Sí (vertical) | oEmbed |
| Facebook | Sí | La imagen de vista previa de la página. Facebook suele pedir iniciar sesión: entonces se usa la foto del punto |
| Instagram (reels) | Sí (vertical) | Igual que Facebook. Las fotos de Instagram no son vídeos y se rechazan |
| Twitch, Streamable, Rumble, Bilibili | No: pestaña nueva | La imagen de vista previa de la página |
| Cualquier otra | No: pestaña nueva | Solo si la página dice que tiene un vídeo (`og:video`, `og:type=video…` o `VideoObject`) |

**Se rechazan**, con un mensaje claro:
- los enlaces que no son https;
- los enlaces acortados (bit.ly, t.co, vm.tiktok.com, fb.watch…);
- los enlaces con usuario y contraseña, con un puerto o a una dirección IP;
- los dominios con caracteres disfrazados (`xn--`);
- los archivos de vídeo sueltos (.mp4…) y los ejecutables;
- las páginas que no son vídeos.

Para no insertar el reproductor de una plataforma (sus vídeos se abrirían en una pestaña nueva), en el `.env`:
`WOD_VIDEO_EMBED_OFF=facebook,instagram`.

**Miniaturas**:
- Se descargan una sola vez, al comprobar o añadir el enlace.
- Se guardan en WebP en tres tamaños (400, 800 y 1280 px) y recortadas a 16:9, en `/assets/uploads/videos/`.
- Si la plataforma no respondía en ese momento, el servidor lo vuelve a intentar 3 veces, con 10 minutos entre
  intentos.

**Descargas desde otras webs** (`app/wod/remoto.py`):
- solo https y solo direcciones públicas (nunca la red interna del servidor);
- máximo 3 redirecciones, cada una comprobada;
- límite de tiempo y de tamaño;
- solo el tipo de contenido esperado.

## Especies

- Hay un **catálogo central**, que solo gestiona la administración. Cada especie tiene:
  - el nombre científico;
  - el nombre común y una frase breve en cada idioma de la web (el español es obligatorio);
  - una foto con su autor, su licencia y, si quieres, la página de origen.
- **Las fotos**:
  - Se guardan en WebP en dos tamaños (v50.51): 128 px para la foto redonda de la franja y 640 px para el bocadillo,
    sin los datos ocultos de la cámara, y se cargan en diferido.
  - Licencias admitidas: propia, ilustración propia, cedida por el autor, banco de imágenes, CC0, dominio público,
    CC BY y CC BY-SA.
  - Se rechazan las licencias no comerciales (NC) y las que prohíben modificar (ND).
- **«Buscar una foto libre en Wikimedia Commons»** (al editar una especie):
  - Busca por el nombre científico y enseña el autor y la licencia de cada foto, tomados de Commons.
  - Las fotos no libres o sin autor salen marcadas y no se pueden usar.
  - Al elegir una, el servidor vuelve a pedir sus datos a Commons y la guarda con su autor, su licencia y su página de
    origen.
- **Especies de un punto**: frecuencia (Habitual, Ocasional o Rara) y temporada opcional (los meses en que se ve).
- **Buscador**: encuentra una especie por su nombre en cualquier idioma, sin importar los acentos, o por su nombre
  científico. Por ejemplo, «krake» encuentra el pulpo.

## Quién añade qué

| Quién | Vídeos | Especies de un punto | Catálogo de especies |
|---|---|---|---|
| Administración | Los publica al momento; ordena y quita | Las publica al momento; cambia la frecuencia y la temporada | Crea, edita y borra; fotos de Commons |
| Centro (propietario, o perfiles con «Ficha del centro y ajustes») y freelance | Los propone: esperan la aprobación | Las propone: esperan la aprobación | No |
| Buceador | No | No | No |

- **Centros y freelance** proponen desde su panel → «Vídeos y vida marina».
  - Arriba ven sus propuestas con su estado: pendiente, aprobada o rechazada con el motivo.
  - Pueden retirar una propuesta.
  - Pueden proponer en sus puntos, que salen primero, o buscar cualquier otro punto.
  - En la ficha aparece su nombre: «Aportado por…».
- **La administración** aprueba o rechaza en Administración → «Vida marina y vídeos» → Pendientes. Rechazar pide un
  motivo, que ve quien lo propuso.
- **El servidor decide siempre**: un buceador recibe 403 aunque llame a la dirección a mano. Un centro no puede cambiar
  lo que propuso otro.

## Rendimiento

- La ficha del punto trae las especies, los vídeos y los recorridos antiguos **en la misma petición**, con una
  consulta indexada para cada cosa. Nunca se hace una petición por especie o por vídeo.
- Índices: por punto (`point_species`, `route_videos`), por especie y por estado (la cola de aprobación).
- Medido en el navegador con 30 especies moviéndose en un móvil con la CPU 4 veces más lenta: fotograma mediano y
  p95 de 16,7 ms (60 por segundo). La franja se mueve con `transform` (sin recalcular la página).

## Los recorridos 360° antiguos

- Los vídeos de YouTube y Vimeo que había se copiaron en la v50.50 a vídeos enlazados (salen en «Recorrido virtual»).
- Todo lo demás (panorámicas, Street View) sale en «Recorrido virtual» como antes de la v50.50.
- **No se pueden subir archivos de vídeo**: los vídeos se añaden como enlace.

## Archivos

- `app/wod/videos.py`, `remoto.py`, `imagenes.py` y `vidamarina.py`.
- `app/server.py`, apartado «v50.50 · Vídeos de la ruta…» y migración `migrate_v50_50`.
- `public/js/world-dives-v8.js`, apartado «v50.50 · Vida marina y vídeos de la ruta».
- `public/css/world-dives-v8.css`.
- Especies de ejemplo: `app/data/especies/especies.json` e imágenes `public/img/especies/`
  (`scripts/especies/ilustraciones.py`). Detalle en `especies-de-ejemplo.md`.
- Pruebas: `tests/test_v50_50_vida_marina.py`, `tests/test_v50_51.py`, `tests/navegador/e2e_vida_marina.py` y
  `tests/navegador/e2e_demo_v50_51.py`. Las plataformas y Commons están simulados en `tests/media_mock.py`.
