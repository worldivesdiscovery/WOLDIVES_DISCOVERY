# Encargo «Logbook de buceo» (15/10/2026)

Texto del encargo tal como llegó, con el componente adjunto (`Dive Logbook · Personalizar.zip`: `logbook.js`,
`logbook.css`, `assets/`, `LEEME.md` y `personalizar.html`). Lo que se ha hecho, punto por punto, está en
`docs/logbook/README.md` y en las notas de la v50.57.

En el mismo mensaje, sobre la revisión general: «Cabecera con vídeo (pendiente del .mov) esto no te lo voy a enviar así
que no lo hagas». El punto 3.2 de la revisión general (cabecera con vídeo) queda fuera: no se hace, por decisión del
titular.

---

CONTEXTO
Queremos integrar un logbook de buceo en la sección "Logbook" de nuestra web (y más adelante en la app). Adjunto dive-logbook.zip con el componente ya hecho (HTML/CSS/JS sin frameworks). Lee primero LEEME.md: explica la instalación, la API y el formato de datos. Abre personalizar.html para ver cómo debe funcionar.

LA IDEA
El logbook tiene dos vistas que comparten los mismos datos:
1. Vista clásica (por defecto): una lista sobria de inmersiones con su formulario. Debe verse como una parte más de la web: hereda nuestra tipografía y colores. Solo hay que ajustar el color de acento con --dlc-accent si hace falta.
2. Vista pasaporte: un libro 3D con forma de pasaporte de buceo. Es un extra "que se gana". Se abre con un icono discreto arriba a la derecha de la lista. Está bloqueado hasta que el buceador:
   - registra su primera inmersión verificada por un centro de buceo (QR), o
   - se registra con el enlace de invitación de un centro, o
   - toca el icono 5 veces seguidas (truco oculto, se queda así a propósito).

LO QUE YA HACE EL COMPONENTE (no hay que programarlo)
- Las dos vistas, el desbloqueo, la animación y el guardado local.
- Recibir una inmersión verificada: lb.addDiveFromCenter({...}). Rellena la siguiente página libre, bloquea en pantalla lugar, fecha, país, centro e instructor, y pone el sello "Verified".
- Logo del centro en la portada del pasaporte: lb.setCover({ logo, name }). El buceador puede volver a la portada clásica.
- QR personal en la página del titular: lb.setProfile({ id, qrText }).
- Amigos que aparecen al escribir en "Compañero": lb.setFriends([...]) / lb.addFriend({...}).
- Eventos: logbook:change, logbook:dive-added, logbook:unlocked.

LO QUE HAY QUE CONSTRUIR (servidor + integración)
1. Guardar el logbook en la cuenta del usuario.
   - Al cargar la página: GET /api/logbook → lb.setData(datos).
   - En el evento logbook:change: PUT /api/logbook con e.detail.
   - Usar data-storage-key distinto por usuario.

2. QR de inmersión del centro.
   - El centro crea la inmersión en su panel (fecha, lugar, país, instructor, y opcionalmente profundidad, tiempo, etc.).
   - El servidor genera un token de un solo uso. El QR apunta a https://NUESTRAWEB/scan/d/<token>.
   - Al abrirlo: si no hay sesión, login y volver. Validar el token y asociar la inmersión a la cuenta (sin duplicar si se escanea dos veces).
   - Redirigir al logbook y llamar a lb.addDiveFromCenter(datos).
   - IMPORTANTE: guardar aparte los datos oficiales de cada inmersión verificada y rechazar en el servidor cualquier cambio en los campos bloqueados. El bloqueo en pantalla no es suficiente.

3. Buddies (amigos).
   - Cada usuario tiene una URL pública no adivinable: https://NUESTRAWEB/buddy/<idPublico>. Pasarla con lb.setProfile({ id, qrText: url }).
   - Al abrir la URL de otro con sesión iniciada: crear la amistad en los dos sentidos y mostrar "Ahora sois buddies".
   - Al cargar el logbook: lb.setFriends(listaDeAmigos).

4. Registro con enlace de centro.
   - Enlace de invitación: https://NUESTRAWEB/registro?centro=<slug>. Guardar centerId en la cuenta.
   - La primera vez que el alumno abre el logbook: lb.setCover({ logo: urlLogoCentro, name: nombreCentro }). Esto ya desbloquea el pasaporte.
   - Los logos de los centros: PNG/SVG con fondo transparente (salen estampados en dorado). Si se sirven desde otro dominio, activar CORS.

5. Panel del centro de buceo (mínimo):
   - subir logo y nombre,
   - crear inmersiones y generar/imprimir su QR,
   - copiar su enlace de invitación.

COLORES DEL PASAPORTE
[Pegar aquí el código copiado desde personalizar.html → "Copiar código"]

CRITERIOS DE ACEPTACIÓN
- La lista se ve integrada en la web en escritorio y móvil, con nuestra tipografía.
- Un usuario nuevo ve el icono del pasaporte en gris; al pulsarlo sale la explicación y no se abre.
- Escanear el QR de una inmersión la añade verificada y desbloquea el pasaporte. Escanearlo otra vez no la duplica.
- Registrarse con el enlace de un centro pone su logo en la portada y desbloquea el pasaporte.
- Escanear el QR de otro buceador lo añade como amigo y aparece en "Compañero".
- Los datos se conservan al cambiar de dispositivo (servidor) y son los mismos en las dos vistas.
- Los campos bloqueados de una inmersión verificada no se pueden cambiar ni manipulando la petición al servidor.
