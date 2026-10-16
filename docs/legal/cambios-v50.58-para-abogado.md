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
