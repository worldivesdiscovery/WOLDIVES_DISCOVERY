# WORLDIVES DISCOVERY v50.36: legal y privacidad en la web, catálogo propio y mapas (Fase 5)

## 1–3 · Documentos legales con versión, historial y aceptación

- **Datos del titular** (nombre o razón social, NIF, dirección, email, teléfono…) en *Administración → Legal*. Se insertan en todos los documentos, en los correos y ahora también **en el pie de la web**.
- **Documentos editables con versiones** (tabla `legal_documents`). Cada cambio crea una versión nueva con su **fecha de entrada en vigor** y un **resumen de cambios**. El historial completo es público al final de cada documento y cada versión anterior se puede leer tal cual se aceptó.
- **Rutas:** `#/legal/aviso-legal`, `condiciones-buceadores`, `condiciones-centros`, `condiciones-reserva`, `privacidad`, `cookies`, `normas-resenas`, `puntos`, `accesibilidad`, `contacto` y `creditos`. Las rutas antiguas (`terminos`, `centros`, `resenas`, `reservas`) siguen funcionando. Los enlaces del pie, del registro, del alta de centros, de la reserva y de «Mi cuenta» usan las rutas nuevas.
- **Idiomas:** el castellano y el inglés son oficiales (los 10 documentos ya están en inglés). Las traducciones a otros idiomas muestran «Traducción informativa. En caso de discrepancia prevalece la versión en castellano».
- **Textos nuevos o reescritos:** privacidad (completa: responsable, datos, finalidades y bases, destinatarios, plazos, derechos), cookies y servicios de terceros, condiciones de uso, condiciones de reserva (los dos modos, la señal y la política del centro, devoluciones hechas por el centro), normas de las reseñas, cómo ordenamos los resultados, **puntos**, **accesibilidad**, **contacto** y **créditos y licencias**.
- **Aceptación:** al registrarse ya había una casilla obligatoria sin marcar y otra comercial aparte. Ahora, si entra en vigor una versión nueva de las condiciones o de la privacidad, al entrar se pide aceptarla en una ventana (se puede posponer durante la visita). Cada aceptación guarda versión, fecha e IP (`legal_acceptances`).
- **Centros: 15 días de antelación.** Un cambio de las condiciones para centros no se puede publicar con menos de 15 días. Se avisa por email a centros y profesionales y en una banda de su panel, con el resumen de cambios, y pueden aceptarlo ya. Los demás cambios también se avisan por email (plantilla `legal_update`).
- **Editor en Administración → Legal:** tabla de documentos (versión vigente, idiomas, próxima versión), editor Markdown con vista previa, idioma, fecha de entrada en vigor y aviso por email.

## 4 · Cookies y terceros
Ya estaba: aviso de primera capa (solo cookies técnicas) y vídeos/mapas integrados solo tras pulsar. Se ha actualizado la política con la tabla de servicios que reciben la IP: el mapa base y el satélite pasan por nuestro servidor y no envían la IP a terceros; GEBCO sí la recibe y solo si se elige.

## 5 · Derechos de las personas usuarias
- **«Descargar mis datos (ZIP)»**: `datos.json` con todos los datos y la carpeta `documentos/` con los archivos subidos.
- **«Eliminar mi cuenta»** con contraseña y **confirmación desde el email** (enlace de un solo uso, 24 h). Sin email válido, basta la contraseña. Anonimiza la cuenta, borra la ficha, los documentos (también los archivos), el Log Book y los avisos, y conserva las reservas sin nombre.
- **Cascadas revisadas:** las solicitudes de alta (`center_claims`) se retiran y pierden teléfono, nota y email; los códigos de promoción se revocan; los códigos de puntos se anulan; se borran los avisos de caducidad de documentos.
- Cambio de email con verificación: ya estaba.

## 6 · Plazos de conservación (tarea diaria)
En *Administración → Legal → Conservación de datos*, con «Guardar y aplicar ahora»:
- cuentas de buceador sin actividad (36 meses): aviso por email y eliminación 30 días después si nadie entra;
- documentos caducados (12 meses tras la caducidad);
- avisos de los centros (24 meses);
- registro de actividad (12 meses, conservando siempre las últimas 300 entradas).
Ya estaba: las sesiones caducan a las 8 horas y los registros del servidor con IP rotan a los 14 días (`WOD_LOG_RETENTION_DAYS`). Las reservas y los pagos (6 años) nunca se borran aquí.

## 7 · Pantalla de reserva
La reserva de inmersiones ya mostraba todo lo pedido. La **solicitud de experiencias** muestra ahora el mismo bloque: quién la presta y su país, precio final con impuestos, política de cancelación del organizador, la ausencia del derecho de desistimiento de 14 días (art. 103.l TRLGDCU) y una casilla obligatoria de aceptación de las condiciones.

## 8 · Transparencia: reseñas y denuncias
- **Respuesta del centro:** una única respuesta pública por reseña, editable y borrable, sin hilos. Al publicarla se avisa a quien escribió la reseña.
- **«Denunciar»** en cada reseña y **«Denunciar contenido»** en las fichas de centro, punto y experiencia y en las fotos de la galería. Se abre una ventana con el motivo, la explicación y la declaración de buena fe.
- **Administración → Denuncias:** se ve el tipo de contenido y se resuelve con motivos. La decisión se envía **a quien denunció y a quien publicó el contenido** (plantilla nueva `report_decision_affected`). Retirar una reseña denunciada la oculta.
- **Moderación directa:** el administrador puede ocultar una reseña desde la ficha, indicando el motivo, que se envía al autor.
- «Cómo ordenamos los resultados» ya estaba y se ha actualizado.

## 9 · Centros y catálogo
- **Solo centros verificados y activos** en el directorio, el mapa, las fichas de punto, los tipos de buceo y la ficha pública. Si no hay centros, se muestra «Todavía no hay centros en esta zona» con «¿Tienes un centro? Únete a WORLDIVES».
- **«Centros asociados»** en la portada: solo centros verificados que han autorizado el uso de su logo (casilla nueva en su panel, con fecha), en orden aleatorio. La banda no aparece si hay menos de los configurados en *Administración → Promociones* (6 por defecto).
- **Eliminado «reclamar ficha por teléfono»:** el alta crea siempre un centro nuevo pendiente de aprobación.
- **Modo demostración** (`WOD_DEMO_MODE=1`): cinta fija «Versión de demostración: los centros y reservas que ves son ejemplos», sin pagos reales (Stripe desactivado aunque haya clave), sin registros y con `noindex`. Muestra los centros de ejemplo aunque no estén verificados.
- **`tools/demo_centros_ficticios.py`** sustituye en la base de la demo los 28 centros de PADI/SSI por centros ficticios (nombres inventados, sin logo, teléfono, email ni web), con copia de seguridad previa.
- **Descripciones de los 283 puntos reescritas con texto propio** en los 10 idiomas (`app/wod/pointtext.py`): resumen (lugar, tipo, profundidad y nivel), qué se ve, acceso y consejos. Para los 27 puntos con texto de origen desconocido se extrajeron primero los hechos y se redactó desde cero (`app/data/point_extras.json`, con la lista de hechos de cada uno). **No se inventa nada:** lo que falta queda marcado. El texto anterior se conserva en `description_legacy` y antes de la migración se hace una copia completa de la base.
- **Administración → Descripciones de puntos:** texto nuevo, datos que faltan y texto anterior. Permite editar, regenerar y marcar como «Descripción revisada».
- **Documentos:** `docs/legal/catalogo-origen.md` (origen de cada dato) y `docs/legal/puntos-reescritos.md` (lista para revisar).

## 10 · Mapas y licencias
- **Mapa base propio con Protomaps:** archivo PMTiles servido por nuestro servidor con peticiones de rango (`/tiles/worldives.pmtiles`), `protomaps-leaflet` 5.1.0 incluido en la web y estilo propio con los colores de la web y nombres en el idioma del visitante. Ya no se usa `tile.openstreetmap.org` (solo en desarrollo si falta el archivo). Instalación, tamaño, niveles de zoom y actualización en **`docs/mapas.md`**.
- **Satélite Esri con clave** (`ARCGIS_API_KEY`, solo en `.env`): las teselas pasan por nuestro servidor, así que la clave nunca llega al navegador y el contador es exacto. La capa no es la predeterminada y no aparece sin clave. **Contador mensual** con límite en *Administración → Mapas* (1.900.000 por defecto), aviso a los administradores al 80 % y capa oculta al llegar al límite hasta el mes siguiente. También hay un límite por IP para evitar abusos.
- **GEBCO** se mantiene, solo si se elige y con su atribución completa. Las atribuciones de OSM, Protomaps, Esri y GEBCO llevan enlace.
- **Créditos y licencias:** página `#/legal/creditos` con Leaflet, markercluster, protomaps-leaflet, Inter, Noto, qrcode, fontTools y Stripe.

## 11 · Imágenes
Nuevo campo **«Origen / licencia»** además del crédito, para cada imagen que publica la plataforma, en *Administración → Medios → Origen y licencia de las imágenes*. El informe marca las que no tienen origen: hoy son todas, 23 de 23 (`docs/legal/imagenes-origen.md`).

## 12 · Accesibilidad
- Todas las etiquetas quedan enlazadas a su campo. El registro y la reserva ya lo estaban; el resto (unas 90 en los paneles) se enlaza automáticamente al dibujar la pantalla. Los campos sin etiqueta reciben un nombre accesible.
- **Los 13 `outline:none`:** 10 ya tenían un anillo de foco visible y se ha añadido a los 3 que no lo tenían (buscador, marcadores del mapa y modo de alto contraste de Windows).
- Página `#/legal/accesibilidad`.

## Migración `migrate_v50_36` (solo añade y transforma)
- Tablas nuevas: `legal_documents`, `account_deletion_requests`, `dive_point_texts`, `map_tile_usage` e `image_origins`.
- Columnas nuevas:
  - en `users`, `inactive_warned_at`;
  - en `center_reviews`, la respuesta y la moderación;
  - en `content_reports`, el contenido denunciado y la persona afectada;
  - en `centers`, `logo_consent`;
  - en `dive_points`, `description_legacy`, `description_reviewed` y `description_missing`;
  - en `site_media` y en `site_theme_media`, `origin`.
- Antes de reescribir las descripciones se hace una copia completa (`data/backups/…-v50_36_points-…`). No se borra ningún dato.

## Estado de la Fase 5

| Punto | Estado |
|---|---|
| 5.1 Datos del titular en Administración, aviso legal y pie | Completado (ya estaba en Administración; nuevo en el pie) |
| 5.2 Páginas legales editables con versión e historial, rutas, es/en oficiales, enlaces | Nuevo |
| 5.3 Aceptaciones: registro, `legal_acceptances`, reaceptar, 15 días para centros | Completado (el registro y la tabla ya estaban) |
| 5.4 Cookies y terceros, iframes tras pulsar | Ya estaba; política actualizada |
| 5.5 Descargar datos (ZIP), borrar cuenta con email, cascadas | Nuevo / Completado |
| 5.6 Plazos de conservación con tarea diaria | Nuevo |
| 5.7 Bloque legal en la reserva (inmersiones y experiencias) | Completado |
| 5.8 Transparencia: respuesta única, Denunciar, moderación, aviso a las partes | Nuevo |
| 5.9 Centros solo verificados, banda «Centros asociados», sin reclamar por teléfono, modo demo, centros ficticios | Nuevo |
| 5.9 Origen del catálogo y descripciones reescritas en 10 idiomas | Nuevo (pendiente de revisión del titular) |
| 5.10 Protomaps propio, satélite con clave, contador y límite, GEBCO, créditos | Nuevo (proxy pendiente de confirmar, ver abajo) |
| 5.11 Origen y licencia de imágenes, informe | Nuevo |
| 5.12 Etiquetas, `outline:none`, página de accesibilidad | Completado |

## Pendiente de decisión
- **Proxy de las teselas de Esri.** Está montado a través de nuestro servidor, con la clave oculta y el contador exacto. Falta confirmar en los términos de ArcGIS Location Platform que se permite. Si no se permitiera, la alternativa es una clave restringida al dominio cargada desde el navegador; en ese caso el contador sería aproximado y mandaría el panel de Esri.
- **Nivel de zoom del mapa base:** recomendado hasta el 14. Si el disco del servidor es pequeño, hasta el 12, y la vista satélite da el detalle de la costa.
- **Mínimo de centros asociados:** 6 por defecto (configurable).
- **Revisión de las 283 descripciones:** el titular debe marcarlas como revisadas y completar lo que falta (sobre todo «qué se ve» en 256 puntos).
- **Ruta de «Mis puntos»** (de v50.35): sigue en `#/mis-puntos`.

## Para abogado / gestoría
- Revisar todos los textos legales: privacidad, cookies y terceros, condiciones de uso, de reserva y para centros, normas de las reseñas, puntos, accesibilidad, contacto y créditos. En particular:
  - plazos de conservación;
  - base legal de la invitación a reseñar;
  - tratamiento de los datos que recibe el centro;
  - transferencias internacionales.
- Confirmar el procedimiento de denuncias y de recurso conforme al Reglamento de Servicios Digitales (2022/2065), y si aplica el régimen de pequeñas empresas.
- Términos de ArcGIS Location Platform: uso a través de un proxy, atribución y caché de 24 h en el navegador.
- **Lista de 215 puntos de buceo:** confirmar si viene de una base de datos de PADI u otra con derechos *sui generis* (`docs/legal/catalogo-origen.md`).
- **Licencias de las 23 imágenes** de la web (`docs/legal/imagenes-origen.md`).
- **Declaración de accesibilidad:** la web no es de una administración pública, pero conviene revisar las obligaciones de la Ley 11/2023 (Acta Europea de Accesibilidad) para servicios de comercio electrónico.

## Cómo se probó
- **`tests/test_phase5_legal_catalog.py`, 22 pruebas.** Todas sobre una copia de la base:
  - rutas y alias;
  - idiomas oficiales y nota de prevalencia;
  - reaceptar una versión nueva, historial y versión anterior;
  - 15 días para centros;
  - datos erróneos y permisos del editor;
  - exportación ZIP con documentos;
  - borrado confirmado por email, con token falso y token reutilizado;
  - cascadas;
  - conservación (avisos, eliminación a los 30 días, documentos caducados, valores fuera de rango);
  - respuesta única con permisos entre centros;
  - denuncias con aviso a ambas partes;
  - denuncias de centro, punto y foto;
  - moderación con motivo;
  - bloque legal de experiencias;
  - solo centros verificados;
  - banda «Centros asociados» con mínimo;
  - consentimiento de logo;
  - descripciones en 10 idiomas, revisión y regeneración;
  - PMTiles con rangos 206 y 416;
  - proxy satélite: la clave no llega al navegador, el contador, el límite y el aviso del 80 %;
  - informe de imágenes;
  - modo demostración.
- **`tests/e2e_legal_catalog.py`, 33/33 en navegador:**
  - visitante: legal, punto en castellano y en inglés, denuncia;
  - centro: aviso de cambio y respuesta a una reseña;
  - buceador en móvil: reaceptar, ZIP, borrado por email y sin desbordamiento horizontal;
  - administrador: editor legal, conservación, mapas, descripciones e imágenes;
  - todas las etiquetas enlazadas en el registro y en Administración;
  - sin el servidor público de Esri;
  - cinta de la demo.
  - Capturas en `docs/capturas/fase-5/`.
- Suite completa: **117 pruebas correctas**. Una prueba de la Fase 1 se ha actualizado porque ya no existe la sugerencia por teléfono.
- Los textos nuevos de la interfaz y de los correos se traducirán a los 9 idiomas en la pasada final de traducción. Los documentos legales ya están en castellano y en inglés.
