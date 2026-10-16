# Cambios en los textos legales (v50.58) · para la revisión del abogado

Fecha: 16/10/2026. Motivo: dos encargos del titular del 16/10/2026: **«Vídeos de los puntos de buceo más visibles y
aportados por los usuarios»** y **«Fichas de punto más completas y catálogo de puntos ampliado»**. Los textos **quedan
pendientes de revisión del abogado** y no deben publicarse como versión nueva en el servidor real hasta entonces.

## 1. Lo que ha cambiado

| Documento | Dónde | Qué cambia |
|---|---|---|
| **Condiciones de uso para buceadores** (9 idiomas) | `app/legal/<idioma>/terminos.md`, §4 «Contenidos de los usuarios» | Párrafo nuevo «Vídeos de los puntos de buceo» (texto exacto en el punto 2). |
| **Política de cookies y servicios de terceros** (9 idiomas) | `app/legal/<idioma>/cookies.md`, tabla «Servicios de terceros» | La fila de vídeos dice ahora que la imagen del vídeo se carga desde la propia plataforma al ver la ficha (llega la IP, sin cookies) y que el reproductor (YouTube, Instagram, TikTok, con sus cookies) solo se carga al pulsar «Reproducir». Antes decía que la miniatura estaba guardada en nuestro servidor: ya no es así, por petición expresa del encargo. |
| **Créditos y licencias** (9 idiomas) | `app/legal/<idioma>/creditos.md`, «Mapas y datos geográficos» | Línea nueva: la línea de costa de © OpenStreetMap contributors (ODbL) que usa la web para comprobar que cada punto cae en el mar. |
| **Denuncias** (formulario existente) | motivos de un vídeo | Tres motivos propios de los vídeos: «No es de este punto», «Contenido inadecuado», «Es mío y no di permiso». Siguen pidiendo nombre, correo y la declaración de buena fe (DSA art. 16); para un vídeo el detalle es opcional, porque el motivo ya lo explica. |

## 2. Texto exacto del párrafo nuevo (castellano)

> **Vídeos de los puntos de buceo.** Cuando envías un vídeo para la ficha de un punto declaras que es de ese punto y que
> lo has grabado tú o tienes permiso de su autor. {{trade_name}} no copia ni guarda el vídeo: solo lo muestra desde la
> plataforma donde está publicado (YouTube, Instagram o TikTok), con el reproductor oficial de esa plataforma. Antes de
> publicarlo lo revisamos. Cualquier persona puede pedir que se retire un vídeo con el botón «Denunciar» («No es de este
> punto», «Contenido inadecuado» o «Es mío y no di permiso»); si su autor lo pide, lo retiramos.

## 3. Lo que hace la web (para comprobar que el texto dice la verdad)

- **Quién puede enviar:** cualquier usuario con el correo confirmado y los datos obligatorios del perfil. Debe marcar la
  casilla «El vídeo es de este punto de buceo y lo he grabado yo o tengo permiso de su autor» (queda en el registro de
  actividad con su cuenta, la fecha y el enlace).
- **Solo enlaces**, nunca archivos: YouTube (también Shorts), Instagram (publicaciones y Reels) y TikTok. El servidor
  comprueba con el servicio oficial oEmbed de la plataforma que el vídeo existe, es público y se puede insertar.
- **Revisión previa:** todo vídeo de un usuario queda pendiente hasta que la administración lo aprueba. Se avisa al
  usuario al aprobar o rechazar (en la web y por correo).
- **Retirada:** cualquier denuncia llega a «Administración → Vídeos de puntos → Denunciados»; «Retirar» quita el vídeo de
  la ficha en un clic y avisa a quien denunció y a quien lo envió (DSA art. 17, con los motivos).
- **Privacidad:** la web pública no muestra quién envió cada vídeo. La imagen del vídeo llega desde la plataforma (la IP
  del visitante llega a YouTube, TikTok o Instagram, sin cookies); el reproductor, con sus cookies, solo al pulsar. La
  primera vez que alguien reproduce un vídeo se le muestra la línea «Este vídeo se reproduce desde YouTube, Instagram o
  TikTok, que pueden usar cookies».

## 4. Preguntas para el abogado

1. ¿Basta la declaración con casilla para el uso de vídeos de terceros insertados (no copiados), o conviene pedir
   también el nombre del autor cuando no es quien lo envía?
2. La imagen del vídeo se carga desde la plataforma antes de pulsar (lo pide el encargo): la IP del visitante llega a
   Google, TikTok o Meta sin cookies. ¿Es suficiente informarlo en la política de cookies o hace falta pedir permiso
   antes, como con el reproductor? (Alternativa técnica posible: servir la imagen desde nuestro servidor, como antes.)
3. ¿Hay que pedir de nuevo la aceptación de las condiciones de uso por este párrafo, o basta con publicarlo como
   versión nueva informando a los usuarios?

## 5. Reserva exprés desde la web del centro (encargo unificado del 16/10/2026, bloque 2)

| Documento | Dónde | Qué cambia |
|---|---|---|
| **Política de cookies y servicios de terceros** (9 idiomas) | `app/legal/<idioma>/cookies.md`, primera tabla | Fila nueva `wd-reserva-datos-v1`: almacenamiento local **solo si la persona marca** «Recordar mis datos en este dispositivo» al reservar en la web de un centro (nombre, correo, teléfono y prefijo, en su propio navegador; nunca llegan a WORLDIVES por esta vía). Se borra con «Borrar mis datos de este dispositivo». |
| **Política de cookies y servicios de terceros** (9 idiomas) | misma, fila «Pago (Stripe)» | Ahora dice «la página de Stripe **o su formulario dentro de la reserva**»: con la clave pública en el servidor, Stripe.js se carga en la reserva (Stripe pone sus cookies contra el fraude, igual que en su página). |
| **Anexo de encargado del tratamiento** (documento interno) | `docs/legal/anexo-encargado-tratamiento.md` | Las dos filas anteriores y la de los **datos de los acompañantes** (nombre, titulación, tallas), que el cliente da con el enlace privado de su reserva y pasan a la lista del barco del centro. |

Lo que hace la web: el almacenamiento solo se escribe si la casilla está marcada al enviar (la prueba
`test_widget_js_ligero_y_sin_cookies` lo comprueba en el código) y se borra si se desmarca. Los acompañantes se borran
con la cuenta y con la retención de 6 años de las reservas (`tests/test_v50_58_reserva_expres.py`).

Preguntas:

4. La casilla «Recordar mis datos en este dispositivo» viene **desmarcada** y el dato solo vive en el navegador de la
   persona. Lo hemos tratado como almacenamiento «estrictamente necesario para un servicio pedido expresamente»
   (art. 22.2 LSSI-CE), sin aviso aparte. ¿Es correcto?
5. Los datos de los acompañantes los da quien reserva, no cada acompañante. ¿Basta con la información de privacidad del
   centro (encargo de tratamiento), o conviene un aviso corto en ese formulario («Comunícales que se los das al centro»)?
