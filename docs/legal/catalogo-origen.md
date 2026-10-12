# Origen de los datos del catálogo (v50.36)

Documento interno para el titular y su abogado. Explica de dónde viene cada dato del catálogo de puntos de buceo y de centros, qué es dato factual y qué es texto con posibles derechos de autor, y qué se ha hecho con cada uno antes del lanzamiento.

## 1. Puntos de buceo (283 en la base de partida)

| Origen (`source_name`) | Puntos | Campos que aporta | Textos |
|---|---|---|---|
| PADI / WORLDIVES curated seed | 215 | nombre, país, región, coordenadas, tipo, profundidad mínima y máxima, dificultad | La descripción era una frase genérica propia («Ubicación de referencia de destino; pendiente de verificación por WORLDIVES»). No había texto copiado. |
| WORLDIVES · catálogo inicial | 41 | nombre, país, región, coordenadas, tipo, dificultad | Frase genérica propia. Sin profundidades ni acceso verificados. |
| Sin origen indicado (Costa Blanca) | 27 | nombre, región, coordenadas, tipo, profundidades, dificultad, acceso | Descripciones de 1–2 frases cuyo origen no consta: **podrían proceder de webs de centros o guías**. |

**Datos factuales** (no protegidos por derechos de autor): nombre del punto, coordenadas, profundidades, tipo de inmersión, dificultad y forma de acceso. Se conservan.

**Descripciones: reescritas todas (decisión del titular).**

- Las 283 descripciones se han sustituido por **texto propio** generado a partir de los datos factuales de cada punto (`app/wod/pointtext.py`), con la misma estructura en los 10 idiomas: resumen (lugar, tipo, profundidad y nivel), qué se ve, acceso y consejos.
- Para los 27 puntos con texto de origen desconocido, primero se extrajeron los hechos (formaciones, especies citadas, acceso…) y después se redactó desde cero un párrafo «qué se ve» y un consejo práctico, sin parafrasear frase a frase (`app/data/point_extras.json`, con la lista de hechos de cada punto para comprobar que no se ha inventado nada).
- **No se inventan datos.** Lo que falta (sobre todo «qué se ve» en 256 puntos, la profundidad en 41 y el acceso en 256) queda vacío y marcado en *Administración → Descripciones de puntos → Datos que faltan*, para que el titular o los centros lo completen.
- El texto anterior se conserva en el campo interno `description_legacy` hasta que el titular marque cada punto como «Descripción revisada». Antes de la migración se hace una copia completa de la base (`data/backups/…-v50_36_points-…`).
- Lista para revisar: `docs/legal/puntos-reescritos.md`.

**Pendiente de decisión / abogado:** confirmar si la lista de 215 puntos (nombres y coordenadas) se elaboró a partir de un listado de PADI o de otra base de datos con derechos *sui generis* (Directiva 96/9/CE). Si es así, conviene verificar los puntos con fuentes propias o abiertas (OpenStreetMap, cartografía oficial) antes del lanzamiento.

## 2. Centros (28 en la base de partida)

| Origen | Centros | Datos |
|---|---|---|
| PADI public directory | 18 | nombre, ciudad, teléfono, web, **logo** |
| SSI / ScubaGO | 10 | nombre, ciudad, teléfono, web |

**Decisión del titular: solo de demostración, no pasan a producción.**

- En producción la base empieza limpia: los centros aparecen únicamente cuando se dan de alta ellos mismos y la administración los aprueba (`verification_status='verified'`).
- Se ha eliminado la lógica de «reclamar ficha por teléfono».
- Para la demo, `scripts/herramientas/demo_centros_ficticios.py` sustituye los 28 centros reales por centros ficticios (nombres inventados, sin logo, teléfono, email, web ni redes), con copia de seguridad previa.
- Los logos de los centros solo se muestran en la banda «Centros asociados» si el centro lo autoriza en su panel (`logo_consent`, con fecha).

## 3. Imágenes

Las 24 imágenes de la web (hoy en `public/img/`: portada, destinos, iconos) **no tienen origen ni licencia registrados**. Ver el informe «Imágenes sin origen» en *Administración → Medios* y `docs/legal/imagenes-origen.md`. Antes del lanzamiento hay que confirmar la licencia de cada una o sustituirla.

## 4. Mapas

- Mapa base: © OpenStreetMap contributors (ODbL), servido desde nuestro propio servidor con Protomaps.
- Satélite: Esri World Imagery, con clave de ArcGIS Location Platform (`ARCGIS_API_KEY`).
- Batimetría: GEBCO Compilation Group (2024) GEBCO 2024 Grid.

Detalle de licencias en la página pública `#/legal/creditos`.
