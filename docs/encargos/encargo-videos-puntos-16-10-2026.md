# WORLDIVES DISCOVERY — Encargo: vídeos de los puntos de buceo más visibles y aportados por los usuarios (16/10/2026)

Eres el programador de WORLDIVES DISCOVERY. Trabaja sobre la última versión del código. El titular adjunta una captura de cómo se ve ahora la ficha de un punto (`#/punto?id=355`, «Recorrido virtual» de El Rincón del Buzo).

## Qué pasa hoy

En la ficha del punto, el bloque «Recorrido virtual» enseña:

* una miniatura muy pequeña del vídeo;
* el texto «RUTA NORMAL» y el título;
* «YouTube · Aportado por WORLDIVES DISCOVERY»;
* un botón grande «Entrar en el recorrido».

Se ve más el botón que el vídeo. El bloque es una tarjeta blanca casi vacía y no da color a la página.

## Qué tiene que pasar

El vídeo es el protagonista. Se ve la imagen del vídeo en grande, con un botón de reproducir encima, como en YouTube. Al pulsar se abre el reproductor, como ahora. Además, cualquier usuario registrado con su perfil completo puede añadir vídeos de YouTube, Instagram o TikTok, y el administrador los aprueba o los borra.

## Reglas

1. Antes de empezar, localiza cómo funciona hoy el recorrido virtual:
   * dónde se guarda el enlace;
   * qué tipos hay («Ruta normal»…);
   * si hay vídeos 360°;
   * cómo se abre el reproductor.

   Reutilízalo y anótalo en las notas («Ya estaba», «Completado», «Nuevo» o «Pendiente de decisión»).
2. Mismo diseño de la web, en Clásico y Futurista, en la web y en el modo app.
3. Textos nuevos en los 9 idiomas, con «Pendiente de traducción» y el castellano de reserva si falta alguno.
4. Entrega en dos zips: `-produccion` y `-pruebas`.

## Parte 1 · Cómo se ve en la ficha del punto

1. Título del bloque: «Vídeos del punto». Si un vídeo es 360°, lleva la etiqueta «360°» encima de su imagen.
2. Quitar:
   * «Aportado por WORLDIVES DISCOVERY»;
   * el botón «Entrar en el recorrido»;
   * la tarjeta blanca vacía;
   * la etiqueta «RUTA NORMAL», que pasa a ser un detalle interno.
3. Con un solo vídeo:
   * la imagen del vídeo ocupa todo el ancho del bloque, en 16:9, con esquinas redondeadas y una sombra suave;
   * en el centro, un botón grande de reproducir (círculo blanco translúcido con el triángulo), que crece un poco al pasar el ratón;
   * abajo, sobre un degradado oscuro, el título corto en blanco y un icono pequeño de la plataforma (YouTube, Instagram o TikTok);
   * la imagen se puede pulsar entera, no solo el botón.
4. Con varios vídeos:
   * el primero (el destacado) en grande, como arriba;
   * los demás en una fila de miniaturas debajo, que se desliza de lado, con el mismo botón de reproducir en pequeño;
   * al pulsar una miniatura se reproduce;
   * en el móvil, un carrusel que se pasa con el dedo.
5. Vídeos verticales (Reels, TikTok o Shorts): se muestran como tarjetas verticales 9:16 en la misma fila, sin recortar la imagen.
6. Imagen de cada vídeo: se usa la miniatura oficial de la plataforma, en la mayor calidad disponible (en YouTube, `maxresdefault` y, si no existe, `hqdefault`). No se descarga ni se guarda en nuestro servidor: se carga desde la plataforma.
   * TikTok: su miniatura oficial (oEmbed).
   * Instagram: Meta exige una clave de aplicación para su oEmbed. Prepáralo con la clave en el `.env`, márcalo «Pendiente de decisión del titular» y, mientras no haya clave, enseña la foto del punto con el icono de Instagram y «Ver en Instagram».
7. Sin vídeos aprobados: el bloque no aparece, salvo el botón para añadir uno (Parte 2).
8. Posición en la ficha: justo debajo de «Sobre el punto», para que dé color a la pantalla en la primera bajada.

## Parte 2 · Reproducir

1. Al pulsar, el vídeo se abre en una ventana grande encima de la página, con el fondo oscurecido:
   * se cierra con ✕, con Esc o tocando fuera;
   * en el móvil, a pantalla completa.
2. Con varios vídeos, flechas ‹ › en la ventana para pasar al siguiente sin cerrarla.
3. Reproductor oficial de cada plataforma:
   * YouTube con `youtube-nocookie.com`;
   * Instagram y TikTok con su código de inserción oficial.
4. Privacidad y cookies:
   * antes de pulsar, la página solo carga la imagen, nunca el reproductor;
   * el reproductor de la plataforma (que instala sus cookies) se carga solo cuando el usuario pulsa;
   * la primera vez se muestra una línea: «Este vídeo se reproduce desde YouTube, Instagram o TikTok, que pueden usar cookies»;
   * añadir las tres plataformas a la política de cookies y servicios de terceros.
5. Si el autor ha desactivado la inserción o ha borrado el vídeo: se muestra «Este vídeo ya no está disponible» con el enlace a la plataforma, y el vídeo queda marcado para el administrador.

## Parte 3 · Los usuarios aportan vídeos

1. Quién puede añadirlos:
   * cualquier usuario registrado, con el correo verificado y los datos obligatorios del perfil completos (buceador, centro o freelance);
   * si le falta algo, el botón le dice qué completar.
2. Botón «Añadir un vídeo de este punto» en el bloque, discreto, debajo de los vídeos.
3. Formulario corto:
   * enlace del vídeo;
   * título corto (opcional; si no, se usa el de la plataforma);
   * casilla obligatoria: «El vídeo es de este punto de buceo y lo he grabado yo o tengo permiso de su autor».
4. Comprobaciones al enviar:
   * solo se admiten enlaces de YouTube (`youtube.com`, `youtu.be`, Shorts), Instagram (publicaciones y Reels) y TikTok. Cualquier otra dirección se rechaza;
   * el vídeo existe, es público y se puede insertar (comprobado con oEmbed). Si no, se explica el motivo;
   * no se repite: si ese vídeo ya está en el punto, se avisa;
   * límite de 5 vídeos al día por usuario.
5. Queda pendiente de aprobación. El usuario ve «Gracias. Lo revisaremos antes de publicarlo» y recibe un aviso cuando se aprueba o se rechaza.
6. Cualquiera puede denunciar un vídeo publicado («No es de este punto», «Contenido inadecuado», «Es mío y no di permiso»), con el sistema de denuncias que ya existe.

## Parte 4 · El administrador decide

1. Administración → Vídeos de puntos, con pestañas Pendientes, Publicados y Denunciados, y un contador de pendientes en el menú.
2. Cada vídeo muestra:
   * su imagen, para verlo sin salir del panel;
   * el punto, quién lo envió y cuándo;
   * la plataforma.
3. Acciones:
   * Aprobar (con un clic, o varios a la vez);
   * Rechazar con motivo opcional;
   * Borrar un vídeo publicado;
   * Editar el título;
   * Marcar como destacado, que sale el primero y en grande;
   * Cambiar el orden arrastrando.
4. Los vídeos que añade el administrador se publican directamente.
5. Los vídeos que ya existen (como el de El Rincón del Buzo) quedan publicados y pasan al nuevo diseño sin hacer nada.

## Parte 5 · Legal

1. Añadir a las condiciones de uso un apartado de contenido aportado por los usuarios:
   * quien envía un vídeo declara que es suyo o que tiene permiso de su autor;
   * WORLDIVES solo lo inserta desde la plataforma original, sin copiarlo;
   * cualquiera puede pedir que se retire.

   Queda pendiente de revisión del abogado.
2. Si el autor de un vídeo pide retirarlo («Es mío y no di permiso»), el administrador lo retira desde Denunciados en un clic.

## Comprobaciones antes de entregar

1. Captura de antes y después de la ficha de El Rincón del Buzo en ordenador (1440 px) y móvil (390 px), en Clásico y Futurista.
2. Con 1, 3 y 8 vídeos, y con vídeos horizontales y verticales mezclados.
3. Reproducir vídeos de YouTube, Shorts, Instagram y TikTok. Antes de pulsar, ninguna petición a esas plataformas salvo la miniatura.
4. Enviar como buceador:
   * un enlace válido queda en Pendientes y se publica al aprobarlo;
   * un enlace de otra web se rechaza;
   * un vídeo repetido se avisa;
   * un usuario sin el perfil completo ve qué le falta.
5. Un vídeo borrado en YouTube muestra «Este vídeo ya no está disponible» y aparece marcado en Administración.
6. Denunciar un vídeo lo lleva a Denunciados.
7. Consola sin errores y Lighthouse de la ficha del punto sin empeorar.
8. Notas de versión con el estado de cada parte y lo que quede «Pendiente de decisión» (la clave de Meta para Instagram y el texto legal).
