# Seguros de buceo · estado actual (v50.55, antes de cambiar nada)

Bloque 2, Parte A del encargo «Motor de reservas multicanal + seguros de buceo». Revisión del código tal como estaba
antes de la v50.56, sin cambiar nada. Las líneas son de `app/server.py` (S) y `public/js/world-dives-v8.js` (JS) en la
v50.55.

## 1. Resumen

| Pregunta del encargo | Respuesta |
|---|---|
| ¿Cómo sube hoy el buceador su seguro? | Como un documento más («Seguro») en «Documentación», con una fecha de caducidad **opcional** y sin aseguradora, número, tipo ni zona |
| ¿Cómo sube el centro su seguro de RC? | En «Datos fiscales y seguro»: aseguradora, número de póliza, fecha de caducidad (texto libre) y el certificado (Fase 6) |
| ¿Dónde se guardan? | En el almacenamiento privado (`storage/documents`, fuera de `/public`), con permisos `0600` y nombre aleatorio |
| ¿Quién puede verlos? | El buceador; el centro mientras el buceador tenga con él una reserva online activa o le haya dado permiso; la administración con motivo (y el interruptor de datos personales). El certificado de RC, solo la administración |
| ¿Hay caducidad y avisos? | Sí: documentos del buceador a 30 y 7 días y el día después de caducar; RC del centro a 30 y 7 días y al caducar |
| ¿Hay aseguradoras en el código? | **No.** Ni nombres, ni enlaces de afiliado. «DAN» solo aparece como ejemplo en un campo («Seguro DAN 2026…») |
| ¿La reserva comprueba el seguro? | **No.** Ningún servicio lo exige y ninguna reserva lo comprueba; el manifiesto y el check-in no lo enseñan |

## 2. Documentos del buceador

**Tabla `user_documents`** (S:557 y S:750): `id, user_id, document_type, title, file_path, original_name, expires_at
(opcional), status, uploaded_at`. Avisos enviados en `document_alerts(document_id, kind, sent_at)` (S:297).

**Tipos** (S:3026): `Titulación`, `Seguro`, `Documento de identidad`, `Documento adicional`. Máximo 30 documentos por
persona (S:3024).

**Subida** `POST /api/account/documents` (S:16082):
- tamaño: 10 MB por documento (`WOD_MAX_DOCUMENT_MB`, `wod/config.py:85`), 15 MB por petición;
- contenido real comprobado por los primeros bytes (`sniff_document`, `wod/security.py:442`): PDF (con `%%EOF` al final),
  JPEG, PNG o WEBP; las imágenes, además, abiertas con Pillow (`check_document`, S:2688);
- antivirus (ClamAV) si `WOD_AV_COMMAND` está configurado (S:2708);
- **los datos ocultos de las fotos (EXIF, GPS) no se borran** en los documentos: solo en las imágenes públicas
  (`wod/imagenes.py`). Pendiente → v50.56;
- el estado se guarda como `valid` (con fecha) o `uploaded` (sin fecha) y no se actualiza nunca (no hay «caducado» en la
  base: se calcula en la pantalla).

**Sin datos médicos** (S:3027, S:3184, S:2544): un tipo con «médic», «salud», «health»… se rechaza («No subas
certificados médicos…»); al arrancar se borran los que hubiera y se avisa al buceador. La pantalla también lo avisa.

**Descarga** `GET /api/documents/file/<id>` (S:14749): el dueño siempre; un **centro** si `center_can_see_user` (S:2999)
es cierto; la administración con motivo (`admin_data_gate`). Cada descarga queda en el registro (`document_downloaded`) y
cada intento denegado también (`document_access_denied`). Los PDF de otra persona se descargan, no se abren en el
navegador. Hallazgo: un **freelance** ve la lista de documentos en la reserva (`provider_can_see_user`) pero al
descargarlos recibe 404, porque la descarga solo contempla el rol `center`.

**Cuándo los ve un centro** (`center_can_see_user`, S:2999): mientras el buceador tenga con ese centro una reserva
**online hecha por él** que no esté cancelada, rechazada ni caducada (una reserva **completada** cuenta, así que el
acceso no termina nunca), o mientras no revoque el permiso que dio en el check-in por QR (`data_shares`). Las reservas
que escribe el propio centro nunca dan acceso. **No hay un plazo** ligado a la fecha de la inmersión.

**Borrado:** el buceador borra su documento cuando quiere (`POST /api/account/documents/delete`, S:16091). Al borrar la
cuenta se borran todos. Retención: `run_retention_jobs` (S:18030) borra cada día los documentos **caducados hace más de
12 meses** (`expired_docs_months`, configurable de 1 a 60 en Administración → Legal → Conservación de datos). No mira si
hay una reserva en disputa.

## 3. Avisos de caducidad del buceador

`queue_document_alerts` (S:8009), cada hora a partir de las 9:00: documentos que caducan en los próximos 30 días o ayer.
Avisos «a 30 días», «a 7 días» y «caducado» (plantillas `document_expiring` y `document_expired`, S:7310), cada uno una
vez. Detalles: el día que caduca recibe el de 7 días; el de «caducado» llega el día siguiente; no hay aviso a 1 día; el
correo no ofrece contratar nada. En la pantalla: «Caducado», «Caduca en N días» (aviso a 45 días) o «Sin caducidad».

## 4. El seguro de responsabilidad civil del centro (Fase 6)

Columnas en `centers` y `users` (freelance): `insurance_company`, `insurance_policy`, `insurance_expires_at`,
`insurance_doc`, `insurance_alerts` (migración v50.37, S:2210).

- Se guardan en «Datos fiscales y seguro» (`POST /api/provider/fiscal`, S:16358; solo el propietario del equipo).
- El certificado se sube con `POST /api/provider/insurance-doc` (S:16363): mismas comprobaciones de los documentos, en la
  carpeta privada de ese centro (`documents/centros/c-<id>`), nombre aleatorio, `0600`.
- Solo lo ve la **administración** (`GET /api/admin/insurance-doc`, con motivo; ninguna pantalla lo enlaza). El propio
  centro no puede volver a descargarlo; la pantalla dice «Ya hay un certificado subido».
- Avisos (`run_insurance_alerts`, S:4574, una vez al día): a 30 y 7 días y al caducar, a los propietarios (plantillas
  `insurance_expiring` / `insurance_expired`, S:7156).
- No bloquea nada (ni publicar ni cobrar): es informativo.

## 5. El seguro en la reserva

No existe. No hay ajuste por servicio, ni comprobación al reservar, ni campo en la API, ni columna en el planning, el
manifiesto (`wod/manifest.py`), la hoja del buceador (`diver_sheet_pdf`) o el check-in. Lo único que ve el centro en el
detalle de una reserva es «Seguro / documentación: N documento(s) disponible(s)» o «No aportada» (JS:2678), sin colores
de caducidad. Los correos de confirmación y el justificante dicen «Lleva tu titulación y el seguro de buceo» (S:7567).

## 6. Lo que se conserva y lo que cambia en la v50.56

Se conserva: el almacenamiento privado, la comprobación del contenido, el antivirus, el rechazo de lo médico, el registro
de cada descarga, los avisos del seguro de RC y la retención configurable.

Cambia o es nuevo (ver `docs/notas-de-version/v50.56.md`, apartado «Seguros de buceo»):
- «Mi seguro de buceo» con aseguradora, número, tipo, fechas, zona y profundidad, estados 🟢🟠🔴⚪ y avisos a 30, 7 y
  1 días y el día que caduca, con «Renovar o contratar seguro»;
- EXIF borrado en las fotos de las pólizas; lectura opcional del PDF; borrado a los 12 meses salvo reserva en disputa;
- aseguradoras colaboradoras configurables (ninguna en el código) y el aviso legal;
- el seguro en la reserva por servicio («No» / «se comprueba en el centro» / «obligatorio») en todos los canales;
- el centro ve el estado del seguro de sus buceadores solo desde la confirmación hasta 7 días después, y el documento
  solo si el buceador lo comparte; cada vista queda registrada.
