# Experiencias: cómo están hoy (v50.43)

Revisión del encargo unificado, punto B1. No se ha cambiado código. Las referencias son a `app/server.py` (S:línea) y a `public/assets/js/world-dives-v8.js` (J:línea). Las capturas de la lista, la ficha, la reserva y el panel del organizador, en móvil y ordenador, están en `docs/capturas/experiencias-b1/`.

## Modelo
- **`travel_offers`** (S:511): el **destino** (título, región, tipo, imagen y textos). Lo crea el administrador, o el organizador al escribir un destino nuevo.
- **`travel_experiences`** (S:486): la **experiencia** de un organizador en ese destino. Tiene fechas, precio por persona, plazas, qué incluye, condiciones, estado, `image_url` y, opcionalmente, un servicio enlazado (`service_id`).
- **`experience_bookings`** (S:267): las solicitudes de las experiencias que no van enlazadas a un servicio.

## 1. Flujo de publicación
- **Quién crea:** centros, freelance y administrador, con `POST /api/travel-experiences` (S:10699).
  - Hace falta el interruptor general «Experiencias» y la función `experiences` del plan.
  - Desde el formulario de un servicio también se puede publicar como experiencia (`sync_service_experience`, S:2357).
- **Campos obligatorios:** solo el destino y el título. Las fechas, el precio, las plazas, qué incluye y las condiciones son opcionales.
- **Estado inicial:**
  - **centro:** `published` (se ve al momento);
  - **freelance:** `pending` (espera a que la apruebe el administrador).
  - No se comprueba que la cuenta del centro esté aprobada ni que haya aceptado las condiciones para centros.
- **Editar** (`/api/travel-experiences/update`, S:10939):
  - la experiencia de un centro sigue publicada;
  - la de un freelance mantiene su estado, así que una ya publicada cambia sin revisión y una rechazada no puede volver a enviarse;
  - «Eliminar» la oculta (`active=0`).
- **Administración:**
  - lista de todas las experiencias con «Publicar» y «Rechazar» (`adminTravelExperiences`, J:4185; `/api/admin/travel-experiences/status`, S:10742);
  - **no hay aviso** al administrador cuando se crea o se cambia una experiencia;
  - **no se avisa** al organizador cuando se aprueba o se rechaza la suya, ni se le dice el motivo;
  - todo queda en `audit_log`.
- **Lo que ve el público:** solo las experiencias activas y publicadas. Si van enlazadas a un servicio, ese servicio tiene que estar activo.
- **Detalle visto en las capturas:** la bandeja del administrador muestra el estado sin traducir («pending», «published»).

## 2. Imagen
- **El organizador puede subir su propia imagen** (`POST /api/provider/experience-image`, S:10681; ventana `openPhotoModal`, J:3307).
- **Controles al subir** (`save_public_image`, S:2401):
  - JPG, PNG o WebP;
  - **máximo 6 MB**;
  - se comprueba el contenido real del archivo (bytes mágicos), no solo la extensión.
- **Lo que falta:**
  - **no se borran los datos EXIF** (la ubicación GPS de la foto queda publicada);
  - no se reduce el tamaño ni se convierte a WebP;
  - no hay recorte ni vista previa;
  - no hay galería;
  - no hay aviso de derechos de imagen.
- **No hay opción de usar el logo del centro ni la foto de perfil.**
- **Sin imagen propia,** la tarjeta de la experiencia sale **sin imagen**, aunque la ventana de subida dice «se muestra la del destino». No hay imagen por defecto por tipo de experiencia.

## 3. Cómo se ve el organizador
- **Tarjeta** (`tripCard`, J:1000): «Centro de buceo» o «Profesional independiente» y el nombre, con enlace a su ficha. **Sin logo ni foto.**
- **Ficha:** la API ya devuelve `center_logo`, pero la web no lo usa.
- **Página de reserva** (`expLegalBlock`, J:1160): dice «Prestado por X (país)» y «WORLDIVES DISCOVERY es la plataforma de reservas: no organiza ni presta la actividad». Es lo mismo que pide el encargo con otras palabras; la frase exacta «WORLDIVES no organiza este viaje» no aparece.
- **No hay sello «Verificada»** ni valoración en las experiencias. Las reseñas solo existen para los centros.

## 4. Lista, filtros y buscador
- **`#/experiencias`** (`renderExperiences`, J:969) lista los **destinos**. Al entrar en uno se ven sus experiencias.
- **Filtros que hay:**
  - tipo;
  - texto libre (título, región, tipo, resumen);
  - orden por recomendado, precio, fecha o nombre.
  - Se guardan en el enlace.
- **Filtros que faltan:** fechas, precio, plazas, organizador, «Solo verificadas» y «Centro o Profesional».
- **No se puede buscar por el nombre del organizador.**
- **No hay enlace propio del organizador** (`/o/<nombre>`). Sus páginas son `#/centro?id=` y `#/profesional?id=`.
- **No hay comparador** de experiencias al mismo destino.

## 5. Reserva y pago
- **Experiencia enlazada a un servicio:** reserva con el motor normal. Usa los dos modos (Fase 1B), la señal (Fase 2) y el precio por persona multiplicado por los participantes.
- **Experiencia sola** (`/api/experience-bookings`, S:10724):
  - **siempre es «bajo petición»**: no usa los dos modos;
  - el organizador recibe un correo y acepta o rechaza;
  - el pago se cobra después, por Stripe en la cuenta del organizador (cargo directo, Fase 2).
- **Precio por persona × participantes:** se cobra bien (`start_experience_checkout`, S:6390). **S:3546 está corregido en el cobro.**
- **Señal:** en las experiencias solas no hay señal.
- **Freelance sin centro:** puede cobrar online con su propia cuenta de Stripe (`payee_of`, S:5710).
- **Fallo encontrado:** al enviar la solicitud, la web intenta abrir el pago al momento (J:1175). El servidor lo rechaza porque la solicitud aún no está aceptada; la web oculta el error y solo muestra «solicitud enviada». No hace daño, pero sobra.

## 6. Plazas
- **Experiencia sola:**
  - las plazas se restan al **enviar la solicitud** (S:10732);
  - vuelven si el organizador la rechaza o la cancela;
  - **no caducan**: si el organizador no responde, quedan ocupadas;
  - el buceador no tiene botón para cancelar.
- **Experiencia enlazada a un servicio:** las plazas son las de sus salidas (`service_slots`), con la caducidad de la Fase 1B.

## 7. Denuncias
- **El botón «Denunciar» de la tarjeta** crea un aviso en `content_reports`, y la administración recibe un correo (`admin_content_report`).
- **Hoy es una bandeja distinta** de la revisión de experiencias.

## Resumen para el bloque B

| Punto | Estado de partida |
|---|---|
| B2 Imagen del organizador | **Completado parcial:** la subida es segura (tipo y tamaño). Faltan EXIF, tamaños WebP, recorte, logo o cara, galería, aviso de derechos e imagen por defecto. |
| B3 Organizador reconocible | **Parcial:** el nombre y el enlace ya están. Faltan la insignia con logo o cara, la valoración, «Verificada», los filtros, `/o/<nombre>` y el comparador. |
| B4 Publicación inmediata y revisión | **Parcial:** los centros ya publican al momento; los freelance no. Faltan los requisitos para publicar, el aviso al administrador, «Verificar», «Pedir cambios» y «Ocultar» con motivo, la bandeja «Por revisar» unida a las denuncias y el aviso a los afectados. |
| B5 Reserva y pago | **Parcial:** el precio por persona ya se cobra bien y el freelance sin centro cobra. En las experiencias solas faltan los dos modos, la señal y la caducidad. |
| B6 Agencia de viajes | **Nuevo**, pendiente del abogado. |

**Decisión de diseño propuesta:** que una experiencia de fechas fijas sea siempre una **convocatoria del motor común** (un servicio con su salida o sus sesiones). Así las experiencias «solas» dejan de tener su propio sistema de plazas y pagos, y heredan los dos modos, la señal, la caducidad, la lista de espera y las devoluciones. Las experiencias solas que ya existen se convertirán con una migración que solo añade. Ver `docs/agenda/diseno.md`, §8.
