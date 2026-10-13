# Paridad web → app · WORLDIVES

Encargo «App móvil en 3 módulos», apartado 8 · Tanda 0. El titular revisa esta tabla en cada entrega.

Inventario de **todo lo que la web hace hoy** para cada perfil, leído del código, y dónde iría en la app.
Leído de la web v50.47 (13/10/2026). No se ha cambiado código para hacerlo.

## Resumen en cifras

| Perfil | Funciones | Igual | Simplificada | Disponible en la web |
|---|---|---|---|---|
| Buceador (total) | **69** | 53 | 16 | 0 |
| · Visitante (sin cuenta) | 24 | 16 | 8 | 0 |
| · Buceador con cuenta | 45 | 37 | 8 | 0 |
| Centro (propietario y equipo) | **95** | 59 | 27 | 9 |
| Freelance | **55** | 30 | 24 | 1 |
| **Total** | **219** | 142 | 67 | 10 |

- **Buceador:** todo cabe en la app. Nada queda «Disponible en la web».
- **Centro:** lo que queda en la web es trabajo de oficina: importar CSV, informe CSV, DAC7, textos legales (descargo),
  precios avanzados (tarifas por temporada y precios especiales por días), el plan, el widget y la clave API.
- **Freelance:** todo en la app salvo «Mi plan», porque en iOS el plan no se puede vender dentro de la app.
- **Funciones del encargo comprobadas en el servidor (30):** 10 no existen, 8 existen en parte y 12 existen
  (apartado 4).

## Cómo se ha hecho y cómo leer las tablas

- **Fuentes:** rutas de la web (`route`, J:165), menús del panel del centro (J:3952) y del freelance (J:2735), las
  llamadas a la API del archivo JavaScript y las rutas del servidor (`do_GET` S:9137, `do_POST` S:10450,
  `do_DELETE` S:12940). Los permisos del equipo salen de `team_gate` (S:3528).
- **Abreviaturas:** `J:línea` = `public/js/world-dives-v8.js`; `S:línea` = `app/server.py`. Los módulos se citan por
  su nombre (`app/wod/…`).
- **Nombres:** se usan los textos en castellano que ve el usuario. `public/idiomas/es.json` **no existe**: el
  castellano es la base y va dentro del propio JavaScript (`docs/estructura.md`).
- **Una fila por función que el usuario ve.** No cuento los avisos solo informativos (cookies, cinta de «entorno de
  pruebas»), ni lo que el servidor tiene pero la web no usa (va en el apartado 5).
- **«En la app»:**
  - **Igual:** la misma función, con los mismos datos y reglas.
  - **Simplificada:** la misma función con menos opciones a la vista o adaptada al móvil (por ejemplo, Apple Pay en
    lugar de la página de Stripe).
  - **Disponible en la web:** la app enseña la opción con un botón «Abrir en la web».
- **«Pantalla de la app»:** la estructura del encargo. «Hoja de la salida» es la hoja que se abre sobre Inicio o
  Explorar (doc. `docs/app-movil/01-pantallas-y-flujos.md`, B2).

---

## 1. Buceador

«Buddies» (pestaña del encargo) no tiene ninguna función equivalente en la web: ver el apartado 4.

### 1.a Visitante (sin cuenta) · 24 funciones

| # | Función de la web | Dónde en la web (ruta #/... y pestaña) | Endpoint(s) | En la app | Pantalla de la app | Notas |
|---|---|---|---|---|---|---|
| V01 | Buscar puntos, centros y lugares desde la portada (con zonas del mundo y patrocinadores) | `#/` portada | `GET /api/point-directory`, `GET /api/center-directory`, `GET /api/dive-types`, `GET /api/site-promos` | Igual | Inicio | J:241 `bindHomeSearch`, J:774 |
| V02 | Mapa de puntos con capas «Mapa», «Satélite» y «Relieve», zonas y filtro por tipo | `#/explorar` (y mapa de la portada) | `GET /api/dive-points/map`, `GET /api/map/config`, `GET /api/tiles/satellite/…` | Simplificada | Explorar | Relieve GEBCO por WMS; satélite con clave ArcGIS (S:9385). La capa elegida se recuerda en el dispositivo (J:182) |
| V03 | Catálogo de puntos con filtros (zona, tipo, país, «con centro que lo ofrece», «confirmación inmediata») y orden | `#/puntos` | `GET /api/point-directory` | Simplificada | Explorar (lista) | J:836 |
| V04 | Ficha del punto: fotos, profundidad, nivel, tipo, coordenadas, centros que lo ofrecen o cercanos, puntos cercanos, abrir en el mapa, orientación según tu titulación | `#/punto?id=` | `GET /api/dive-points/{id}`, `…/photos`, `…/centers` | Igual | Explorar › ficha del punto | J:911; orientación por nivel J:350 |
| V05 | Recorrido virtual del punto (vídeo 360° o Street View) | `#/virtual?id=` | `GET /api/dive-points/{id}/virtual` | Simplificada | Explorar › ficha del punto | Abre el vídeo externo tras un aviso de privacidad (J:371) |
| V06 | Directorio de centros con filtros (país, tipo de buceo) y orden | `#/centros` | `GET /api/center-directory`, `GET /api/dive-types` | Igual | Explorar | J:527 |
| V07 | Ficha del centro: actividades y precios, próximas salidas, viajes, galería, reseñas, dónde bucea, contacto, «Ver en el mapa» | `#/centro?id=` | `GET /api/centers/{id}` | Igual | Explorar › ficha del centro | J:417 |
| V08 | Llamar o escribir un email al centro | `#/centro?id=` botones «Llamar» y «Escribir» | — (`tel:`, `mailto:`) | Igual | Explorar › ficha del centro | J:438. **No hay botón «WhatsApp del centro»** en la web |
| V09 | Tipos de buceo: lista y detalle (nivel, profundidad, dónde hacerlo, centros) | `#/tipos` | `GET /api/dive-types`, `GET /api/dive-types/{clave}` | Simplificada | Explorar (filtro «tipo») | J:617, J:646 |
| V10 | Experiencias: destinos y viajes (buscar, ordenar, viajes de un destino) | `#/experiencias`, `#/experiencia?id=` | `GET /api/travel-directory`, `GET /api/travel-offers/{id}` | Igual | Explorar › Viajes | J:977, J:1029 |
| V11 | Top 10 de buceos cerca de ti (ubicación o zona, radio) | `#/top10` | `GET /api/top-dives`, `GET /api/geocode` | Igual | Inicio («Cerca de mí») | J:1067. La ubicación no se guarda |
| V12 | Ficha de un profesional freelance (servicios y salidas) | `#/profesional?id=` | `GET /api/providers/{id}`, `GET /api/provider-services` | Igual | Explorar › ficha del profesional | J:1154 |
| V13 | Ver las salidas, plazas libres y precio final de un centro y calcular el total antes de entrar | `#/reservar?center=` | `GET /api/provider-services`, `GET /api/center-extras`, `GET /api/center-equipment`, `GET /api/booking-quote` | Igual | Inicio › hoja de la salida | Al pulsar «Continuar» pide cuenta y guarda lo elegido (J:1734) |
| V14 | Ver el calendario de días libres de un servicio por días | `#/reservar-dias?service=` | `GET /api/agenda/public`, `POST /api/agenda/quote` | Igual | Inicio › hoja de la salida | Solo «libre, ocupado, mañana, tarde, no disponible» (J:1513) |
| V15 | Solicitar información a un centro o profesional sin reserva online | `#/reservar` y `#/profesional` (ventana) | `POST /api/info-requests` | Igual | Explorar › ficha del centro o del profesional | Funciona sin cuenta (S:11474) |
| V16 | Crear cuenta de buceador, centro o freelance | `#/registro` | `POST /api/auth/register` | Simplificada | Entrar | Centro y freelance quedan «pendientes de verificación». Apple, Google y passkey no existen hoy |
| V17 | Iniciar sesión, con el código de verificación en dos pasos si está activo | `#/login`, `#/verificacion` | `POST /api/auth/login` | Simplificada | Entrar | Hoy es sesión por cookie; la app necesita token por dispositivo (doc. 02) |
| V18 | Recuperar y restablecer la contraseña | `#/recuperar`, `#/restablecer` | `POST /api/auth/forgot`, `POST /api/auth/reset` | Igual | Entrar | J:4865, J:4873 |
| V19 | Confirmar el email desde el enlace del correo | `#/verificar-email` | `POST /api/auth/verify-email` | Igual | Entrar (enlace universal) | J:4961 |
| V20 | Cambiar el idioma (9 idiomas) | Cabecera, selector de idioma | `POST /api/account/language` (con sesión) | Simplificada | Entrar · Mi área › Ajustes | La app irá en español, inglés y francés (decisión del 13/10) |
| V21 | Leer los textos legales, sus versiones anteriores e imprimirlos | `#/legal/{documento}` | `GET /api/legal/doc`, `…/info`, `…/history`, `…/version` | Simplificada | Entrar · Mi área › Ajustes | J:4724 |
| V22 | Denunciar un contenido (reseña, centro, punto, foto, promoción, perfil) | Botón «Denunciar» y `#/legal/denuncias` | `POST /api/reports` | Igual | Menú de cada ficha | J:399, J:4781 |
| V23 | Escribir a WORLDIVES (formulario de contacto) | `#/legal/contacto` | `POST /api/contact` | Igual | Entrar · Mi área › Ajustes | J:4799 |
| V24 | Darse de baja de las novedades desde el enlace del correo | `#/baja` | `POST /api/marketing/unsubscribe` | Igual | Enlace universal | J:5423 |

### 1.b Buceador con cuenta · 45 funciones

| # | Función de la web | Dónde en la web (ruta #/... y pestaña) | Endpoint(s) | En la app | Pantalla de la app | Notas |
|---|---|---|---|---|---|---|
| B01 | Mi área: próxima inmersión (cuándo, estado, pago) y cifras: próximas reservas, pagos pendientes, avisos sin leer, documentos que caducan | `#/area` | `GET /api/me`, `GET /api/me/area` | Igual | Inicio («Tu próxima inmersión») | J:1290 |
| B02 | «Cómo llegar» al centro (Google Maps) | `#/area` (próxima inmersión); enlaces `#/r/…` | — | Igual | Reservas › detalle | J:1305, J:2236 |
| B03 | Mis reservas: próximas e historial | `#/area` «Mis reservas» | `GET /api/me/area` | Igual | Reservas | |
| B04 | Detalle de la reserva con su QR y los datos del centro (teléfono, email, dirección) | `#/reserva?id=` | `GET /api/bookings/{id}`, `GET /api/bookings/{id}/qr.svg` | Igual | Reservas › detalle | El QR abre una página de verificación (S:10126). El encargo pide un QR firmado que valga sin conexión |
| B05 | Descargar el justificante en PDF («PDF sin conexión») | `#/area`, `#/reserva` | `GET /api/bookings/{id}/receipt.pdf` | Simplificada | Reservas › detalle (compartir) | En la app la reserva y su QR quedan guardados en el móvil |
| B06 | Reservar una salida: elegir centro, actividad, salida, personas, equipo de alquiler y tallas, extras (nitrox, guía, traslado, extras del centro), nota y total | `#/reservar?center=&service=&slot=` | `GET /api/provider-services`, `GET /api/booking-quote`, `POST /api/bookings` | Simplificada | Inicio / Explorar › hoja de la salida | J:1579. El encargo pide 2 toques. Sin sesión se guarda el borrador y se retoma al entrar |
| B07 | Pagar online con tarjeta y ver la confirmación del pago | Tras reservar; «Pagar ahora» en `#/reserva`; `#/pago-ok` | `POST /api/payments/checkout`, `GET /api/payments/session/{id}`, `POST /api/payments/cancel` | Simplificada | Hoja de la salida (monedero) | Hoy, página de Stripe Checkout; la app usa PaymentSheet con Apple Pay y Google Pay (doc. 02) |
| B08 | Solicitar plaza «Bajo petición» y pagar cuando el centro acepta, dentro del plazo | `#/reservar`, `#/reserva` | `POST /api/bookings`, `POST /api/payments/checkout` | Igual | Hoja de la salida · Reservas › Pagar | Plazos en J:1261 y J:1301 |
| B09 | Pagar solo la señal o pagar en el centro, según el servicio | `#/reservar` | `GET /api/booking-quote`, `POST /api/bookings` | Igual | Hoja de la salida | «Resto a pagar en el centro» (J:1697) |
| B10 | Reservar un servicio por días o medias jornadas (calendario, personas, extras, nota) | `#/reservar-dias?service=` | `GET /api/agenda/public`, `POST /api/agenda/quote`, `POST /api/bookings` | Simplificada | Hoja de la salida (calendario) | J:1486 |
| B11 | Lista de espera de una salida completa: «Avisarme si queda plaza» y «Salir de la lista» | `#/reservar` (salida completa) | `POST /api/waitlist/join`, `POST /api/waitlist/leave` | Igual | Hoja de la salida | J:2293 |
| B12 | Cancelar una reserva, viendo antes cuánto se devuelve según la política | `#/reserva` «¿No puedes ir?» | `POST /api/bookings/{id}/cancel` (vista previa y confirmación) | Igual | Reservas › detalle | J:4907 |
| B13 | Cambiar la fecha a otra salida del mismo servicio (directo o con aprobación del centro) | `#/reserva` «Cambiar fecha» | `GET /api/bookings/{id}/reschedule-options`, `POST /api/bookings/{id}/change-date` | Igual | Reservas › detalle | J:2260. No se cobra ni se devuelve la diferencia de precio |
| B14 | Salida cancelada por el centro: elegir otra fecha, la devolución o anular sin coste | `#/salida-cancelada`; enlace `#/r/{firma}` | `GET`/`POST /api/slot-cancel/{id}`, `GET`/`POST /api/r/{token}` | Igual | Reservas › detalle (desde el aviso) | Con el enlace firmado funciona sin iniciar sesión (J:2243) |
| B15 | Abrir una reserva desde el enlace firmado de un aviso (cambio, cancelación, recordatorio) | `#/r/{token}` | `GET /api/r/{token}` | Igual | Reservas › detalle (enlace universal) | J:2229 |
| B16 | Firmar el descargo de responsabilidad (cada plaza, con el dedo) y descargar el PDF firmado | `#/reserva` «Descargo» | `GET /api/bookings/{id}/waiver`, `POST /api/bookings/{id}/waiver/sign`, `GET /api/waivers/{id}.pdf` | Igual | Reservas › detalle › Descargo | J:2349, J:2364. Sin preguntas de salud |
| B17 | Escribir o editar la reseña del centro (1 a 5 estrellas, título, texto) | `#/centro?id=&resena=1` (aviso en la reserva) | `POST /api/centers/{id}/reviews` | Igual | Reservas › detalle («Valorar») | Basta una reserva pagada o confirmada; no exige check-in (S:10953) |
| B18 | Avisos de los centros: leer, marcar como leído, ir a la reserva, ver el contacto del centro | `#/area` «Avisos» | `GET /api/me/area`, `POST /api/messages/read` | Igual | Inicio (avisos) | No se pueden contestar (J:1319) |
| B19 | Recibir los avisos de reservas por WhatsApp (teléfono y permiso) | `#/cuenta` (teléfono) y `#/reservar` (casilla) | `POST /api/account/profile` (`wa_consent`) | Igual | Mi área › Mi ficha | J:2064 a J:2079 |
| B20 | Solicitar un viaje o vida a bordo y pagarlo si hace falta | `#/experienciareserva?id=` | `POST /api/experience-bookings`, `POST /api/payments/checkout` | Igual | Explorar › Viajes | J:1174. El buceador no puede cancelar la solicitud desde la web |
| B21 | Ver mis viajes y su estado | `#/area` «Viajes y vida a bordo» | `GET /api/me/area` | Igual | Reservas | |
| B22 | Mi ficha: nombre, teléfono, país, ciudad, fecha de nacimiento, idioma preferido | `#/cuenta` | `POST /api/account/identity`, `POST /api/account/profile` | Igual | Mi área › Mi ficha | J:1330 |
| B23 | Titulación y contacto de emergencia | `#/cuenta` | `POST /api/account/profile` | Igual | Mi área › Mi ficha | La titulación es un nombre de una lista; no hay niveles comparables entre agencias |
| B24 | Equipo y tallas: traje, botas, chaleco, aletas, máscara, lastre, botella, ordenador, notas | `#/cuenta` | `POST /api/account/profile` | Igual | Mi área › Mi ficha | |
| B25 | Documentos (titulación, seguro, identidad, otros): subir con caducidad, abrir, eliminar; aviso «Caduca en N días» | `#/cuenta?docs=1`; resumen en `#/area` | `POST /api/account/documents`, `POST /api/account/documents/delete`, `GET /api/documents/file/{id}` | Igual | Mi área › Documentos | Aviso a menos de 45 días, solo en pantalla (J:1299). Rechaza certificados médicos (J:1381) |
| B26 | Mis centros (donde hice check-in y última visita) | `#/cuenta` «Mis centros» | `GET /api/me` | Igual | Mi área › Mi ficha | |
| B27 | Check-in con el QR de un centro: compartir mi ficha con ese centro | `#/checkin/{código}` | `POST /api/checkin/{código}` | Igual | Enlace universal (hoja «Compartir mis datos») | Registra la visita al centro, no la presencia en una salida (S:12562) |
| B28 | Centros que ven mi ficha y «Dejar de compartir» | `#/cuenta` | `GET /api/account/shares`, `POST /api/account/shares/revoke` | Igual | Mi área › Ajustes | |
| B29 | Cambiar la contraseña (cierra las demás sesiones) | `#/cuenta` «Seguridad» | `POST /api/account/password` | Simplificada | Mi área › Ajustes | Con passkey, Apple o Google no hará falta contraseña |
| B30 | Email: reenviar la verificación y cambiar de email | `#/cuenta` «Email» | `POST /api/account/verify-email/resend`, `POST /api/account/email` | Igual | Mi área › Ajustes | |
| B31 | Verificación en dos pasos: activar, desactivar, nuevos códigos de recuperación | `#/cuenta` | `POST /api/account/totp/setup`, `…/enable`, `…/disable`, `…/recovery` | Simplificada | Mi área › Ajustes | En la app se suma Face ID o huella |
| B32 | Novedades y ofertas de WORLDIVES por email (sí o no) | `#/cuenta` | `POST /api/account/marketing` | Igual | Mi área › Ajustes | |
| B33 | Descargar mis datos (ZIP) | `#/cuenta` «Privacidad y datos» | `GET /api/account/export?format=zip` | Simplificada | Mi área › Ajustes | La app genera el archivo y lo comparte |
| B34 | Eliminar mi cuenta (contraseña y confirmación por email) | `#/cuenta`, `#/eliminar-cuenta` | `POST /api/account/delete`, `POST /api/account/delete/confirm` | Igual | Mi área › Ajustes | Apple lo exige. No deja si hay reservas próximas (S:11719) |
| B35 | Estado de mi solicitud de cuenta profesional | `#/cuenta` | `GET /api/me` | Igual | Mi área › Ajustes | J:4948 |
| B36 | Aceptar las condiciones nuevas cuando cambian | Ventana sobre cualquier pantalla | `POST /api/legal/accept` | Igual | Ventana al abrir la app | J:4767 |
| B37 | Cerrar sesión | Menú de la cuenta y `#/cuenta` | `POST /api/auth/logout` | Igual | Mi área › Ajustes | |
| B38 | Log Book: ver, añadir, editar y borrar inmersiones; las reservas completadas entran solas | `#/logbook` | `GET /api/logbook`, `POST /api/logbook`, `…/update`, `…/delete` | Igual | Mi área › Log Book | J:2504. Sin firma del guía |
| B39 | Recompensas: nivel, número de inmersiones, puntos y logros | `#/recompensas` | `GET /api/rewards` | Igual | Mi área › Nivel y Puntos | J:2628 |
| B40 | Canjear puntos por una ventaja de un centro | `#/recompensas` | `POST /api/rewards/redeem` | Igual | Mi área › Nivel y Puntos | |
| B41 | Mis puntos: saldo, movimientos e historial del antiguo monedero | `#/mis-puntos` | `GET /api/points` | Igual | Mi área › Mis puntos | J:2548 |
| B42 | Mis códigos de ventaja: ver el QR y anularlo (se recuperan los puntos) | `#/mis-puntos` | `GET /api/points/codes/{código}/qr.svg`, `POST /api/points/codes/cancel` | Igual | Mi área › Mis puntos | |
| B43 | Mis promociones con QR personal: verla en grande, condiciones, usos y centros | `#/recompensas`, `#/promo/{código}` | `GET /api/my/promotions`, `GET /api/promo/{código}`, `GET /api/promo/{código}/qr.svg` | Igual | Mi área › Promociones con QR | J:1848. No hay código de promoción al pagar online |
| B44 | Cómo funcionan los puntos | `#/como-funcionan-los-puntos` | — | Igual | Mi área › Nivel y Puntos | J:2566 |
| B45 | Proponer otra posición para un punto de buceo | `#/punto?id=` «¿La posición no es exacta?» | `POST /api/dive-points/{id}/suggest` | Simplificada | Explorar › ficha del punto | Elegir en el mapa con el dedo |

---

## 2. Centro (propietario y equipo) · 95 funciones

### Perfiles del equipo que existen hoy en el código

Existen **los cuatro**: `owner` (propietario), `manager` (encargado), `reception` (recepción) e `instructor`
(`app/wod/inquilinos.py:28`). La web los explica así (J:5154): propietario, todo; encargado, como recepción y además
cancela salidas y avisa a todos; recepción, reservas, clientes, servicios y salidas; instructor, ve el planning y las
reservas sin cambiar nada. Los permisos los pone el servidor en `team_gate` (S:3528).

| Perfil | Qué puede hoy (código) | Qué pide el encargo | Diferencias |
|---|---|---|---|
| Instructor | Ve todo el panel salvo pagos, web e integraciones, escaparate, equipo, actividad, datos fiscales y plan (J:4532-4533, S:3519). Solo puede escribir en su cuenta, marcar presentes en el barco (`/api/manifest/sync`) y recoger firmas del descargo (S:3517-3518) | Hoy, Agenda, **sus** salidas, lista del barco y Escanear; sin pagos ni ajustes | No hay filtro «mis salidas»: ve todas. Ve también servicios, clientes, estadísticas… en solo lectura. No puede validar códigos de promoción ni de puntos (son escrituras) |
| Recepción | Reservas, clientes, servicios, salidas, manifiesto y barcos. No puede: Stripe, datos del prestador, política de cancelación, tarifas, escaparate, iCal, importar, clave API, descargo, equipo, plan, devoluciones (S:3510-3513, S:3539), ni cancelar salidas o enviar avisos masivos (S:3541) | Añade Reservas y Solicitudes | Puede más que en el encargo (servicios y salidas). **La web le enseña «Cobros y pagos», pero el servidor le responde 403** (J:4533 frente a S:3519) |
| Encargado | Como recepción, más cancelar salidas, avisos a todos y WhatsApp (S:3541, `inquilinos.can_send_notices`) | Todo, como el propietario | No puede devolver dinero, Stripe, tarifas, escaparate, equipo ni plan. **Tampoco puede guardar barcos** (S:10839, con el mensaje de error del instructor) |
| Propietario | Todo | Todo | — |

En la columna «Notas» de la tabla se indica cuando una función es solo del propietario o del propietario y el encargado.

### Tabla del centro

| # | Función de la web | Dónde en la web (ruta #/... y pestaña) | Endpoint(s) | En la app | Pantalla de la app | Notas |
|---|---|---|---|---|---|---|
| C01 | Resumen del día: reservas y buceadores de hoy, cifras (Hoy, Solicitudes pendientes, Por cobrar, Próximos 7 días, Cobrado), «Hoy y mañana» y «Requiere atención» | `#/admin` «Resumen» | `GET /api/bookings`, `GET /api/center/analytics`, `GET /api/provider-services`, `GET /api/center/clients` | Simplificada | Hoy | J:3987. El «Hoy» del encargo añade ocupación por salida, barco, personal y alertas (descargo, pago): no hay una llamada que lo junte |
| C02 | De dónde llegan las reservas y lo más vendido | `#/admin` «Resumen» | `GET /api/center/analytics` | Simplificada | Más › Estadísticas | |
| C03 | Cambiar de centro activo (quien trabaja en varios centros) | Cabecera del panel, «Centro activo» | `GET /api/team/centers`, `POST /api/team/switch` | Igual | Más › Cambiar de perfil | J:4537. No hay cambio de centro a buceador: la cuenta de centro no tiene «Mi área» (J:1291) |
| C04 | Ver mi página pública | Cabecera, «Ver mi página» | — | Igual | Más › Ajustes | |
| C05 | Aceptar las condiciones nuevas para centros | Aviso en el panel | `POST /api/legal/accept` | Igual | Ventana al abrir la app | J:4882 |
| C06 | Planning del mes: vistas Mes y Lista, cambiar de mes, cifras del mes (salidas, ocupación, reservas, ingresos, plazas libres) y tendencia | `#/admin?tab=planning` «Planning / agenda» | `GET /api/center/planning` | Simplificada | Agenda (Mes) | J:4055. Solo Mes y Lista (J:4102): no hay Semana, Día ni Recursos |
| C07 | Detalle de un día: salidas con ocupación, personas y estado de pago; reservas sin salida | Planning, toque en el día | `GET /api/center/planning` | Igual | Agenda (Día) | J:4133 |
| C08 | Crear una salida: fecha, hora, plazas, puntos o «según el estado del mar» | «Servicios y tarifas» › «+ Salida» | `POST /api/provider-services/slot` | Igual | Agenda · Hoy («Nueva salida») | No existe «duplicar la salida de ayer» |
| C09 | Editar una salida (fecha, hora, plazas, puntos) | «Servicios y tarifas» › «Salidas de…» | `POST /api/provider-services/slot-update` | Igual | Salida | No deja bajar las plazas por debajo de lo ocupado (S:11145) |
| C10 | Eliminar una salida sin reservas | «Servicios y tarifas» › «Salidas de…» | `POST /api/provider-services/slot-delete` | Igual | Salida | «Cerrar plazas» (`slot-close`, S:11167) existe en el servidor, pero la web no lo usa |
| C11 | Cambio de hora o punto de encuentro con aviso a todos: vista previa de afectados y canales, deshacer | Planning (día) y manifiesto | `GET /api/avisos/ajustes`, `POST /api/avisos/preview`, `POST /api/avisos/cambio`, `POST /api/avisos/{id}/deshacer` | Igual | Salida | Propietario y encargado (S:3541) |
| C12 | Cancelar una salida y avisar a todos: motivo, nota, «cada buceador elige» o «devolver ya a todos», deshacer | Planning (día) y manifiesto | `POST /api/avisos/preview`, `POST /api/avisos/cancelar`, `POST /api/avisos/{id}/deshacer` | Igual | Salida › Cancelar por meteo | Propietario y encargado. Máximo 10 avisos masivos por centro y día (notas v50.47) |
| C13 | Estado de un aviso por canal (correo, WhatsApp, app) | Tras enviarlo y en «Últimos avisos» | `GET /api/avisos/{id}` | Igual | Salida · Más › WhatsApp Business | J:2142 |
| C14 | Crear un cartel de plazas libres para redes: plantilla, color, formato, foto, textos, precio, QR; descargar, compartir, copiar el texto | Planning: «Crear cartel» en la salida o en «Plazas libres» del mes | `GET /api/center/poster-qr` | Igual | Más › Carteles (y desde la salida) | J:4413 |
| C15 | Manifiesto: grupos con barco y guía; añadir, editar y quitar grupos; mover buceadores | `#/manifiesto?slot=` «Vista de reparto» | `GET /api/manifest/{id}`, `POST /api/manifest/{id}/groups/save`, `…/groups/delete`, `…/assign` | Simplificada | Salida (manifiesto) | J:2378. En el móvil se mueve con el botón «Mover» |
| C16 | Sugerir reparto automático por nivel y fijar el máximo de buceadores por guía | `#/manifiesto` | `POST /api/manifest/{id}/suggest`, `POST /api/manifest/{id}/settings` | Igual | Salida | `app/wod/manifest.py:32` |
| C17 | Barcos: crear, cambiar la capacidad, dejar en uso o no | `#/manifiesto` «Barcos» | `POST /api/manifest/boats/save` | Igual | Más › Barcos y puntos | Solo propietario y recepción; el encargado no (S:10839) |
| C18 | Vista para el barco: tarjetas por grupo con teléfono y contacto de emergencia | `#/manifiesto?slot=&vista=barco` | `GET /api/manifest/{id}` | Igual | Salida | |
| C19 | Imprimir el manifiesto (A4, con columna «A bordo» para marcar a mano) | `#/manifiesto` «Imprimir» | — (impresión del navegador, J:2418) | Simplificada | Salida › Compartir PDF | No hay PDF del manifiesto en el servidor |
| C20 | Lista de espera, avisos del reparto e historial de la salida | `#/manifiesto` | `GET /api/manifest/{id}` | Igual | Salida | |
| C21 | Check-in en el barco sin conexión: «Presente», «No se presentó», nota, «Presentes x/y», cola de cambios y conflictos | `#/barco`, `#/barco?slot=` | `GET /api/manifest/day`, `POST /api/manifest/sync` | Igual | Hoy · Salida (check-in) | J:2007. Solo hoy y mañana (S:10090). El instructor también puede |
| C22 | Preparar mañana: guardar en el dispositivo las salidas del día siguiente | `#/barco` «Preparar mañana» | `GET /api/manifest/day` | Igual | Hoy (chip «Mañana») | |
| C23 | Reservas: vistas Hoy, Próximos 7 días, Solicitudes pendientes, Por cobrar, Todas las próximas e Historial; buscar y filtrar por actividad y fechas | `#/admin?tab=bookings` «Reservas» | `GET /api/bookings?…`, `GET /api/center/requests` | Simplificada | Reservas · Solicitudes | J:3385. Máximo 400 resultados |
| C24 | Aceptar una solicitud (con el tiempo que queda para responder) | «Reservas», ficha de la reserva, «Resumen» | `POST /api/bookings/{id}/status` (`confirmed`) | Igual | Solicitudes | |
| C25 | Rechazar una solicitud con motivo | «Reservas», ficha de la reserva | `POST /api/bookings/{id}/status` (`rejected`) | Igual | Solicitudes | J:2482 |
| C26 | Registrar un cobro en el centro o «Cobrar el resto» de la señal (forma de pago) | «Reservas» «Registrar cobro» | `POST /api/bookings/{id}/payment` | Igual | Solicitudes › Pendientes de pago | J:3458 |
| C27 | Marcar como no pagado | «Reservas» «···» | `POST /api/bookings/{id}/payment` | Igual | Reservas | |
| C28 | Completar una reserva ya pasada | «Reservas» | `POST /api/bookings/{id}/status` (`completed`) | Igual | Reservas | Pasa al Log Book del buceador |
| C29 | Cancelar una reserva con motivo; si cancela el centro, devuelve todo lo pagado | «Reservas» «···», ficha | `POST /api/bookings/{id}/status` (`cancelled`) | Igual | Reservas | J:1801 |
| C30 | Devolver dinero, total o parcial, con nota | «Reservas», ficha, «Cobros y pagos» › Devoluciones pendientes | `POST /api/bookings/{id}/refund` | Igual | Más › Cobros y devoluciones · Reservas | Solo propietario (S:3539) |
| C31 | Cambiar fecha u hora: mover la reserva a otra salida del mismo servicio | Ficha de la reserva | `GET /api/provider-services/{id}`, `POST /api/bookings/{id}/reschedule` | Igual | Reservas › detalle | J:5431. Solo dentro del mismo servicio (S:11799) |
| C32 | Aceptar o rechazar el cambio de fecha que pide el buceador | Ficha de la reserva | `POST /api/bookings/{id}/change-date/decide` | Igual | Solicitudes | J:2279 |
| C33 | Enviar un aviso al cliente sobre su reserva (le llega por email y a sus «Avisos») | «Reservas» «···», ficha | `POST /api/messages` | Igual | Reservas › detalle | J:2488. No hay WhatsApp manual ni chat |
| C34 | Nueva reserva manual (teléfono, mostrador, agencia): cliente, servicio, salida o fecha, personas, equipo y extras, estado, pago, precio pactado, notas | «Resumen», «Reservas», Planning «+ Reserva» | `GET /api/booking-quote`, `POST /api/center/bookings/manual` | Simplificada | Agenda · Reservas («+») | J:3466 |
| C35 | Ficha del buceador de una reserva: datos, emergencia, equipo y tallas, documentos | `#/reserva?id=` (vista del centro) | `GET /api/bookings/{id}`, `GET /api/documents/file/{id}` | Igual | Reservas › detalle · Salida | Solo si el buceador reservó él o compartió su ficha |
| C36 | Justificante en PDF con QR y ficha operativa en PDF | Ficha de la reserva | `GET /api/bookings/{id}/receipt.pdf`, `GET /api/bookings/{id}/diver-sheet.pdf` | Simplificada | Reservas › detalle (compartir) | |
| C37 | Recoger la firma del descargo en el dispositivo del centro (por plaza) y descargar el PDF | Ficha de la reserva «Firmar en el check-in» | `POST /api/bookings/{id}/waiver/sign`, `GET /api/waivers/{id}.pdf` | Igual | Salida › buceador | El instructor también puede (S:3518) |
| C38 | Clientes: lista con búsqueda (reservas, última, pagado, check-in con QR) | `#/admin?tab=clients` «Clientes» | `GET /api/center/clients` | Simplificada | Más › Buceadores | J:3890. Sin ficha del cliente ni botones de llamar o WhatsApp |
| C39 | Servicios: crear, editar, duplicar, pausar y eliminar (tipo, duración, plazas, precio, color, descripción) | `#/admin?tab=services` «Servicios y tarifas» | `GET`/`POST /api/provider-services`, `…/update`, `…/delete` | Simplificada | Más › Servicios y tarifas | J:3002 |
| C40 | Modo de reserva (pago al reservar o bajo petición) y plazos de respuesta y de pago | Formulario del servicio | `POST /api/provider-services/update`, `…/options` | Igual | Más › Servicios y tarifas | El pago online exige Stripe activo |
| C41 | Señal (porcentaje o importe por persona) y política de cancelación propia del servicio | Formulario del servicio | `POST /api/provider-services/update` | Igual | Más › Servicios y tarifas | |
| C42 | Cambios de fecha (no, con aprobación, directo; hasta X horas antes) y lista de espera del servicio | Formulario del servicio | `POST /api/provider-services/update` | Igual | Más › Servicios y tarifas | |
| C43 | Unidad de reserva «por días» o «por días o medias jornadas»: horas de mañana y tarde, días mínimos y máximos, antelación, días seguidos, zona horaria | Formulario del servicio «Unidad de reserva» | `POST /api/provider-services/update` (`booking_unit`, `unit_rules`) | Simplificada | Más › Servicios y tarifas | Plan con `agenda_days` (S:8773) |
| C44 | Precios avanzados de los servicios por días: precio especial desde X días, descuento, extras por día, reserva o persona | Formulario del servicio «Más opciones» | `POST /api/provider-services/update` (`pricing`) | Disponible en la web | Más › Servicios y tarifas (botón «Abrir en la web») | Configuración avanzada de precios |
| C45 | Publicar el servicio también en Experiencias (destino) | Formulario del servicio | `POST /api/provider-services/update` | Igual | Más › Servicios y tarifas | |
| C46 | Plantillas de servicio: guardar, usar y borrar | «Servicios y tarifas» › Plantillas | `GET /api/service-templates`, `POST …/save`, `POST …/delete` | Simplificada | Más › Servicios y tarifas | |
| C47 | Cambiar la tarifa vigente desde hoy | «Cambiar tarifa» | `GET /api/center/tariffs`, `POST /api/center/tariffs/save` | Igual | Más › Servicios y tarifas | Solo propietario (S:3512) |
| C48 | Programar una tarifa futura (temporada alta), ver el historial y anular cambios programados | «Cambiar tarifa» | `POST /api/center/tariffs/save`, `POST /api/center/tariffs/history-delete` | Disponible en la web | Más › Servicios y tarifas (botón «Abrir en la web») | Precios por temporada. Solo propietario |
| C49 | Extras (nitrox, fotografía, guía privado…): crear, editar, desactivar y borrar | «Servicios y tarifas» › Extras | `GET /api/center/extras`, `POST …/save`, `POST …/delete` | Igual | Más › Servicios y tarifas | |
| C50 | Precios de alquiler de equipo por artículo | «Servicios y tarifas» › Alquiler | `GET`/`POST /api/center-equipment` | Igual | Más › Servicios y tarifas | Sin stock por talla |
| C51 | Ver un servicio como cliente | «Servicios y tarifas» «Ver como cliente» | — | Igual | Más › Servicios y tarifas | |
| C52 | Experiencias (viajes, vida a bordo): crear, editar, foto, ocultar | `#/admin?tab=experiences` «Experiencias» | `GET /api/provider/experiences`, `POST /api/travel-experiences`, `…/update`, `POST /api/provider/experience-image` | Simplificada | Más › Servicios y tarifas | El «Más» del encargo no tiene «Experiencias» para el centro |
| C53 | Solicitudes de experiencias: aceptar, rechazar, cancelar | «Experiencias» | `POST /api/provider/experience-bookings/status` | Igual | Solicitudes | |
| C54 | Activar los cobros online con Stripe: alta, continuar la configuración, actualizar el estado | `#/admin?tab=payments` «Cobros y pagos» | `GET /api/payments/connect-status`, `POST /api/payments/connect/onboard`, `…/sync` | Simplificada | Más › Cobros y devoluciones | El alta se abre en Stripe. Solo propietario |
| C55 | Abrir mi panel de Stripe | «Cobros y pagos» | `POST /api/payments/connect/login` | Igual | Más › Cobros y devoluciones | Solo propietario |
| C56 | Devoluciones pendientes (clientes que cancelaron una reserva pagada) | «Cobros y pagos» | `GET /api/provider/payments` | Igual | Solicitudes · Más › Cobros y devoluciones | Solo propietario (S:3519) |
| C57 | Últimas operaciones de pago e incidencias | «Cobros y pagos» | `GET /api/provider/payments` | Simplificada | Más › Cobros y devoluciones | Solo propietario |
| C58 | Datos del prestador que salen en el justificante (razón social, NIF, dirección) | «Cobros y pagos» | `POST /api/provider/payment-profile` | Simplificada | Más › Cobros y devoluciones | Solo propietario |
| C59 | Política de cancelación general (horas gratis, porcentaje que se devuelve, nota) | «Cobros y pagos» | `POST /api/provider/cancellation-policy` | Igual | Más › Cobros y devoluciones | J:2859. Solo propietario |
| C60 | Puntos de buceo del centro: añadir uno existente o quitarlo | `#/admin?tab=points` «Puntos de buceo» | `GET /api/center-points`, `POST /api/center-points/assign`, `…/unassign` | Igual | Más › Barcos y puntos | J:3900 |
| C61 | Proponer un punto nuevo | «Puntos de buceo» «Nuevo punto» | `POST /api/dive-points` | Simplificada | Más › Barcos y puntos | Se elige en el mapa; pasa a revisión |
| C62 | Fotos de un punto: añadir con pie y quitar (máximo 24) | «Puntos de buceo» «Fotos» | `GET`/`POST /api/dive-points/{id}/photos`, `…/photos/delete` | Igual | Más › Barcos y puntos | J:3765 |
| C63 | Promociones con QR: crear, editar, finalizar | `#/admin?tab=qr` «Check-in / QR y promociones» › Promociones | `GET`/`POST /api/center/promotions`, `POST …/{id}/status` | Igual | Más › Promociones y QR | J:1867. Plan Pro |
| C64 | Dar una promoción a varios clientes (cada uno recibe su QR y un aviso) | Promociones «Dar a clientes» | `GET /api/center/clients`, `POST /api/center/promotions/{id}/assign` | Igual | Más › Promociones y QR | J:1914 |
| C65 | Ver los códigos de una promoción y anular uno | Promociones «Ver códigos» | `GET /api/center/promotions/{id}/codes`, `POST /api/center/promo-codes/{id}/revoke` | Igual | Más › Promociones y QR | |
| C66 | Promoción válida en otros centros: invitarlos, y aceptar o rechazar las de otros | Promociones | `GET /api/center/partner-search`, `POST /api/center/promotions/{id}/partner` | Igual | Más › Promociones y QR | |
| C67 | Validar y canjear el código promocional de un cliente (escribirlo o abrir su QR) | «Validar un código» y `#/promo/{código}` | `GET /api/promo/{código}`, `POST /api/promo/{código}/redeem` | Igual | Escanear | La web no escanea: la cámara del móvil abre el enlace del QR (J:1862) |
| C68 | Generar QR del centro (check-in, buceador, inmersión, reserva) y copiar el enlace | «QR de check-in» | `POST /api/qr/create`, `GET /api/qr/{código}` | Igual | Más › Promociones y QR | J:4494 |
| C69 | Comprobar una reserva escaneando su QR (página de verificación) | `#/verificarreserva?id=&t=` | `GET /api/public/bookings/{id}` | Igual | Escanear | Solo muestra los datos: no marca «Presente» (S:10046) |
| C70 | Ventajas para puntos: crear y editar (coste, stock, condiciones, activa) | `#/admin?tab=rewards` «Recompensas» | `GET`/`POST /api/provider/reward-offers` | Igual | Más › Promociones y QR | J:2577 |
| C71 | Validar el código de ventaja de un cliente (con la cámara o escribiéndolo) | «Recompensas» | `GET /api/center/redemptions`, `POST /api/center/redemptions/validate` | Igual | Escanear | Es el único escáner con cámara de la web (J:2617) |
| C72 | Conceder puntos a un cliente (con límite al mes) | «Recompensas» | `POST /api/provider/points-grant` | Igual | Más › Buceadores | |
| C73 | Ver los códigos canjeados | «Recompensas» | `GET /api/center/redemptions` | Simplificada | Más › Promociones y QR | |
| C74 | Escaparate: portada, logo, galería, presentación, especialidades, idiomas, horario, contacto, ubicación y redes | `#/admin?tab=center` «Escaparate y datos» | `GET /api/centers/{id}`, `POST /api/provider/center-cover`, `…/avatar`, `…/center-gallery`, `…/center-showcase`, `…/center-update` | Simplificada | Más › Ajustes (datos y escaparate) | J:3836. Solo propietario. El «Más» del encargo no tiene «Escaparate» para el centro |
| C75 | Conectar WhatsApp Business (Meta, coexistencia con la app), comprobar plantillas, reconectar, desconectar y ver el estado | `#/admin?tab=avisos` «Avisos y WhatsApp» | `GET /api/avisos/ajustes`, `POST /api/whatsapp/connect`, `…/disconnect`, `…/templates/refresh` | Simplificada | Más › WhatsApp Business | J:2175. La conexión con Meta se abre en el navegador. Propietario y encargado |
| C76 | Ajustes de avisos: opción por defecto al cancelar y recordatorio el día antes (hora y «qué llevar») | «Avisos y WhatsApp» | `POST /api/avisos/ajustes` | Igual | Más › WhatsApp Business | |
| C77 | Últimos avisos enviados | «Avisos y WhatsApp» | `GET /api/avisos` | Igual | Más › WhatsApp Business | |
| C78 | Solicitudes de información: ver, marcar como leída o contestada | `#/admin?tab=requests` «Solicitudes de información» | `GET /api/center/info-requests`, `POST …/read` | Igual | Solicitudes | Se contestan por email o teléfono |
| C79 | Analítica e informes: ingresos, participantes, conversión, cancelación, por día y por servicio | `#/admin?tab=analytics` «Analítica e informes» | `GET /api/center/analytics` | Simplificada | Más › Estadísticas | J:4032 |
| C80 | Exportar el informe en CSV | «Analítica e informes» «Exportar CSV» | — (se genera en el navegador) | Disponible en la web | Más › Estadísticas (botón «Abrir en la web») | Informe |
| C81 | Estadísticas: visitas, clics en «Reservar», solicitudes y comparación con la zona, por periodo | `#/admin?tab=stats` «Estadísticas» | `GET /api/provider/stats` | Simplificada | Más › Estadísticas | J:5112 |
| C82 | Exportar datos en CSV: clientes, reservas, servicios, agenda y pagos | `#/admin?tab=tools` «Herramientas» | `GET /api/center/export?kind=` | Simplificada | Más › Exportar datos | Pagos, solo propietario (S:9279). El archivo se comparte desde el móvil |
| C83 | Calendario iCal: copiar la dirección privada y generar otra | «Herramientas» | `GET /api/provider/ical`, `POST /api/provider/ical/regenerate` | Simplificada | Más › Ajustes | Solo propietario (S:3519) y con plan. Solo exporta |
| C84 | Enlace directo de reservas y «Compartir por WhatsApp» | «Herramientas» | `GET /api/provider/widget` | Igual | Más › Carteles | |
| C85 | Widget para pegar en la web del centro (código) | «Herramientas» | `GET /api/provider/widget` | Disponible en la web | Más › Ajustes (botón «Abrir en la web») | El código se pega en la web del centro, desde el ordenador |
| C86 | Importar clientes desde CSV (plantilla, vista previa, duplicados) | «Herramientas» | `GET /api/center/import/template`, `POST /api/center/import` | Disponible en la web | Más › Buceadores (botón «Abrir en la web») | Solo propietario |
| C87 | Descargo de responsabilidad: escribir el texto (cada cambio crea una versión) o dejar de pedirlo | «Herramientas» › «Descargo» | `GET`/`POST /api/provider/waiver` | Disponible en la web | Más › Ajustes (botón «Abrir en la web») | Texto legal. Solo propietario |
| C88 | Conexión con la web del centro: generar o regenerar la clave API | `#/admin?tab=integration` «Web e integraciones» | `GET /api/center/integration`, `POST /api/center/integration/regenerate` | Disponible en la web | Más › Ajustes (botón «Abrir en la web») | J:4037. Configuración técnica. Solo propietario |
| C89 | Equipo: invitar por email con un perfil, cambiar el perfil, quitar a alguien, anular invitaciones | `#/admin?tab=team` «Equipo» | `GET /api/center/team`, `POST …/invite`, `…/role`, `…/remove`, `…/invite/revoke` | Simplificada | Más › Equipo del centro | J:5149. Solo propietario; plan Pro |
| C90 | Aceptar una invitación al equipo (con mi cuenta o creando una) | `#/equipo?token=` | `GET /api/team/invite`, `POST /api/team/join` | Igual | Entrar (enlace universal) | J:5177 |
| C91 | Registro de actividad del centro (quién hizo qué) | `#/admin?tab=activity` «Registro de actividad» | `GET /api/center/activity` | Simplificada | Más › Equipo del centro | Solo propietario |
| C92 | Datos fiscales del prestador (DAC7): tipo, razón social, NIF, país, registro, fecha de nacimiento, dirección y declaraciones | `#/admin?tab=fiscal` «Datos fiscales y seguro» | `GET`/`POST /api/provider/fiscal` | Disponible en la web | Más › Ajustes (botón «Abrir en la web») | J:5068. DAC7. Solo propietario |
| C93 | Seguro de responsabilidad civil: aseguradora, póliza, caducidad (con aviso por correo) y certificado | `#/admin?tab=fiscal` | `POST /api/provider/fiscal`, `POST /api/provider/insurance-doc` | Simplificada | Más › Ajustes | Alertas de caducidad en S:3318. Solo propietario |
| C94 | Mi plan: plan y límites, comparar planes, renovar o cambiar (pago de la cuota) e historial de pagos | `#/admin?tab=plan` «Mi plan», `#/planes`, `#/mi-plan` | `GET /api/plans`, `GET /api/provider/plan`, `POST …/checkout`, `POST …/sync` | Disponible en la web | Más › Ajustes (botón «Abrir en la web») | En iOS no se puede vender el plan dentro de la app. Solo propietario |
| C95 | Responder a una reseña (una respuesta pública; editarla o borrarla) | Ficha pública del centro `#/centro?id=` | `POST /api/reviews/{id}/reply` | Igual | Más › Reseñas | J:462. **No hay lista de reseñas en el panel** |

La cuenta personal de cada persona del centro (email, contraseña, dos pasos, descargar datos, cerrar sesión) es la
misma que la del buceador (B28 a B37) y va en «Más › Ajustes». **No puede eliminar su cuenta** desde la web
(S:11715: solo las cuentas de buceador).

---

## 3. Freelance · 55 funciones

| # | Función de la web | Dónde en la web (ruta #/... y pestaña) | Endpoint(s) | En la app | Pantalla de la app | Notas |
|---|---|---|---|---|---|---|
| F01 | Resumen: próxima salida, cifras (servicios activos, salidas del mes, solicitudes pendientes, experiencias), próximas salidas y solicitudes de experiencias | `#/admin` «Resumen» | `GET /api/provider-services`, `GET /api/center/planning`, `GET /api/provider/experiences` | Simplificada | Hoy | J:2767. El «Hoy» del encargo (dónde, a qué hora, con quién, «Cómo llegar») no existe así |
| F02 | Mi ficha pública: porcentaje completado y «Copiar enlace de mi ficha» | «Resumen» | — | Igual | Más › Mi escaparate | |
| F03 | Planning del mes (Mes y Lista, cifras del mes) | `#/admin?tab=planning` «Planning» | `GET /api/center/planning` | Simplificada | Agenda | Sin «+ Reserva» ni cambio o cancelación de salida desde el planning (J:2753, `canBook:false`) |
| F04 | Mi agenda: calendario del mes con reservas, bloqueos, solicitudes y días libres (Mes y Lista) | `#/admin?tab=agenda` «Mi agenda» | `GET /api/agenda/mine` | Igual | Agenda | J:2650 |
| F05 | Bloquear o desbloquear un día | «Mi agenda», toque en el día | `POST /api/agenda/block`, `POST /api/agenda/unblock` | Igual | Agenda (1 toque) | El público solo ve «ocupado» |
| F06 | Bloquear varios días o vacaciones | «Mi agenda» «Bloquear varios días…» | `POST /api/agenda/block` | Igual | Agenda | |
| F07 | Horario y temporadas: días que trabajo, temporadas cerradas, zona horaria | «Mi agenda» «Horario y temporadas» | `POST /api/agenda/hours` | Simplificada | Agenda › Ajustes | |
| F08 | Confirmar o rechazar (con motivo) una solicitud de días | «Mi agenda» | `POST /api/bookings/{id}/status` | Igual | Solicitudes | Al confirmar se bloquean los días |
| F09 | Reservas: vistas Hoy, Próximos 7 días, Solicitudes pendientes, Por cobrar, Todas las próximas e Historial; buscar y filtrar | `#/admin?tab=bookings` «Reservas» | `GET /api/bookings?…`, `GET /api/center/requests` | Simplificada | Solicitudes · Agenda (lista) | La estructura del encargo no tiene «Reservas» para el freelance |
| F10 | Aceptar o rechazar una solicitud de salida | «Reservas», ficha | `POST /api/bookings/{id}/status` | Igual | Solicitudes | |
| F11 | Registrar un cobro en mano, cobrar el resto o marcar como no pagado | «Reservas» | `POST /api/bookings/{id}/payment` | Igual | Solicitudes › Pendientes de pago | |
| F12 | Completar una reserva | «Reservas» | `POST /api/bookings/{id}/status` (`completed`) | Igual | Agenda › salida | |
| F13 | Cancelar una reserva (devuelve todo lo pagado) | «Reservas», ficha | `POST /api/bookings/{id}/status` (`cancelled`) | Igual | Agenda › salida | |
| F14 | Devolver dinero, total o parcial | «Reservas», ficha, «Cobros y pagos» | `POST /api/bookings/{id}/refund` | Igual | Más › Cobros | |
| F15 | Mover una reserva a otra salida del mismo servicio | Ficha de la reserva | `POST /api/bookings/{id}/reschedule` | Igual | Agenda › salida | |
| F16 | Aceptar o rechazar el cambio de fecha que pide el buceador | Ficha de la reserva | `POST /api/bookings/{id}/change-date/decide` | Igual | Solicitudes | |
| F17 | Enviar un aviso al cliente sobre su reserva | «Reservas», ficha | `POST /api/messages` | Igual | Agenda › salida › buceador | |
| F18 | Ficha del buceador, justificante y ficha operativa en PDF | `#/reserva?id=` | `GET /api/bookings/{id}`, `…/receipt.pdf`, `…/diver-sheet.pdf` | Simplificada | Agenda › salida › buceador | |
| F19 | Recoger la firma del descargo en el check-in | Ficha de la reserva | `POST /api/bookings/{id}/waiver/sign` | Igual | Agenda › salida › buceador | |
| F20 | Servicios: crear, editar, duplicar, pausar y eliminar | `#/admin?tab=services` «Servicios y tarifas» | `GET`/`POST /api/provider-services`, `…/update`, `…/delete` | Simplificada | Más › Mis servicios | Sin extras, alquiler de equipo ni tarifas programadas: son solo de centros (S:11024, S:12874, S:10977) |
| F21 | Modo de reserva, plazos, señal, política propia, cambios de fecha y lista de espera del servicio | Formulario del servicio | `POST /api/provider-services/update`, `…/options` | Igual | Más › Mis servicios | |
| F22 | Servicio por días o medias jornadas con sus precios: por día, media jornada, por grupo o persona, mínimos, máximos, precio especial, descuento, extras por día, zona horaria | Formulario del servicio «Unidad de reserva» | `POST /api/provider-services/update` | Simplificada | Más › Mis servicios | Plan con `agenda_days` |
| F23 | Publicar el servicio también en Experiencias | Formulario del servicio | `POST /api/provider-services/update` | Igual | Más › Mis servicios | |
| F24 | Plantillas de servicio | «Servicios y tarifas» | `GET /api/service-templates`, `POST …/save`, `POST …/delete` | Simplificada | Más › Mis servicios | |
| F25 | Ver un servicio como cliente | «Servicios y tarifas» | — | Igual | Más › Mis servicios | |
| F26 | Salidas: crear, editar y eliminar (fecha, hora, plazas) | «Servicios y tarifas» «+ Salida» | `POST /api/provider-services/slot`, `…/slot-update`, `…/slot-delete` | Igual | Agenda («Nueva salida») | Sin puntos de buceo: solo los centros los asocian |
| F27 | Cambio de hora o punto y cancelar la salida avisando a todos; estado y deshacer | Manifiesto | `POST /api/avisos/preview`, `…/cambio`, `…/cancelar`, `…/{id}/deshacer`, `GET /api/avisos/{id}` | Igual | Agenda › salida | En la web solo desde el manifiesto (J:2404) |
| F28 | Manifiesto: grupos, barcos, guía, mover, sugerir reparto, máximo por guía, vista para el barco, imprimir | `#/manifiesto?slot=` | `GET /api/manifest/{id}`, `POST /api/manifest/{id}/…`, `POST /api/manifest/boats/save` | Simplificada | Agenda › salida | |
| F29 | Check-in en el barco sin conexión y «Preparar mañana» | `#/barco` | `GET /api/manifest/day`, `POST /api/manifest/sync` | Igual | Hoy | |
| F30 | Comprobar una reserva escaneando su QR | `#/verificarreserva?id=&t=` | `GET /api/public/bookings/{id}` | Igual | Escanear | |
| F31 | Crear un cartel de plazas libres | Planning «Crear cartel» | `GET /api/center/poster-qr` | Igual | Más › Mi escaparate | El «Más» del freelance no tiene «Carteles» |
| F32 | Experiencias: crear, editar, foto, ocultar | `#/admin?tab=experiences` «Experiencias y solicitudes» | `GET /api/provider/experiences`, `POST /api/travel-experiences`, `…/update`, `POST /api/provider/experience-image` | Simplificada | Más › Mis experiencias | Las del freelance pasan a revisión (S:12488) |
| F33 | Solicitudes de experiencias: aceptar, rechazar, cancelar | «Experiencias y solicitudes» | `POST /api/provider/experience-bookings/status` | Igual | Solicitudes | |
| F34 | Activar los cobros con Stripe, ver el estado y abrir el panel de Stripe | `#/admin?tab=payments` «Cobros y pagos» | `GET /api/payments/connect-status`, `POST /api/payments/connect/onboard`, `…/sync`, `…/login` | Simplificada | Más › Cobros | El alta se abre en Stripe |
| F35 | Devoluciones pendientes y últimas operaciones | «Cobros y pagos» | `GET /api/provider/payments` | Simplificada | Más › Cobros | |
| F36 | Datos del prestador en el justificante | «Cobros y pagos» | `POST /api/provider/payment-profile` | Simplificada | Más › Cobros | |
| F37 | Política de cancelación general | «Cobros y pagos» | `POST /api/provider/cancellation-policy` | Igual | Más › Cobros | |
| F38 | Perfil público: foto, presentación, especialidad, web y redes | `#/admin?tab=profile` «Perfil público» | `POST /api/provider/profile`, `POST /api/provider/avatar` | Simplificada | Más › Mi escaparate | J:2791 |
| F39 | Ver mi ficha pública | Cabecera «Ver mi ficha pública» | — | Igual | Más › Mi escaparate | |
| F40 | Conectar WhatsApp Business, comprobar plantillas, desconectar y ver el estado | `#/admin?tab=avisos` «Avisos y WhatsApp» | `GET /api/avisos/ajustes`, `POST /api/whatsapp/connect`, `…/disconnect`, `…/templates/refresh` | Simplificada | Más › WhatsApp Business | |
| F41 | Ajustes de avisos (al cancelar, recordatorio) y últimos avisos | «Avisos y WhatsApp» | `POST /api/avisos/ajustes`, `GET /api/avisos` | Igual | Más › WhatsApp Business | |
| F42 | Solicitudes de información: ver, marcar como leída o contestada | `#/admin?tab=requests` | `GET /api/center/info-requests`, `POST …/read` | Igual | Solicitudes | |
| F43 | Estadísticas: visitas, clics en «Reservar», solicitudes, por periodo | `#/admin?tab=stats` | `GET /api/provider/stats` | Simplificada | Más › Mi escaparate | El «Más» del freelance no tiene «Estadísticas» |
| F44 | Exportar datos en CSV: clientes, reservas, servicios, agenda y pagos | `#/admin?tab=tools` «Herramientas» | `GET /api/center/export?kind=` | Simplificada | Más › Exportar datos | |
| F45 | Calendario iCal: copiar la dirección y generar otra | «Herramientas» | `GET /api/provider/ical`, `POST /api/provider/ical/regenerate` | Simplificada | Más › Ajustes | Con plan. Solo exporta |
| F46 | Enlace directo y «Compartir por WhatsApp» | «Herramientas» | `GET /api/provider/widget` | Igual | Más › Mi escaparate | |
| F47 | Widget para pegar en la web (código) | «Herramientas» | `GET /api/provider/widget` | Simplificada | Más › Mi escaparate | En la app, copiar o enviarse el código |
| F48 | Descargo: escribir el texto o dejar de pedirlo | «Herramientas» › «Descargo» | `GET`/`POST /api/provider/waiver` | Simplificada | Más › Ajustes | Editor de texto sencillo |
| F49 | Datos fiscales (DAC7) | `#/admin?tab=fiscal` «Datos fiscales y seguro» | `GET`/`POST /api/provider/fiscal` | Simplificada | Más › Ajustes | Formulario |
| F50 | Seguro de responsabilidad civil con caducidad y certificado | `#/admin?tab=fiscal` | `POST /api/provider/fiscal`, `POST /api/provider/insurance-doc` | Simplificada | Más › Ajustes | |
| F51 | Mi plan: ver, comparar, renovar o cambiar, historial de pagos | `#/admin?tab=plan` «Mi plan», `#/planes` | `GET /api/plans`, `GET /api/provider/plan`, `POST …/checkout`, `POST …/sync` | Disponible en la web | Más › Ajustes (botón «Abrir en la web») | En iOS no se puede vender el plan dentro de la app |
| F52 | Aceptar las condiciones nuevas para profesionales | Aviso en el panel | `POST /api/legal/accept` | Igual | Ventana al abrir la app | |
| F53 | Mi cuenta: email, contraseña, dos pasos, novedades, descargar datos, cerrar sesión | `#/cuenta` | `/api/account/…`, `POST /api/auth/logout` | Simplificada | Más › Ajustes | No puede eliminar su cuenta (S:11715) |
| F54 | Mi Log Book | Panel › «Log Book» (`#/logbook`) | `GET`/`POST /api/logbook…` | Igual | Más › Ajustes | No está en el «Más» del encargo |
| F55 | Usar la web como buceador: Mi área, reservar, Recompensas, Mis puntos | Menú de la cuenta (`#/area`, `#/recompensas`, `#/mis-puntos`) | `GET /api/me/area`, `POST /api/bookings`, `GET /api/rewards` | Simplificada | Más › Ajustes (falta «Cambiar de perfil») | La web lo permite (menú J:159; `POST /api/bookings` no limita el rol, S:11962) |

---

## 4. Lo que pide el encargo y NO existe hoy en el servidor

Resumen de las 30 comprobaciones: **no existe 10 · existe en parte 8 · existe 12.**

| Función del encargo | Hoy | Evidencia | Qué falta |
|---|---|---|---|
| Buddies: lista, «Mi código» QR, grupos, «¿Buceamos?» | **No existe** | Ninguna tabla, ruta ni texto de buddies o compañeros en `app/server.py`, `app/wod/` ni en la web. Lo más cercano: `slot_groups` son grupos de buceo de una salida (S:10861), no grupos de amigos | Todo: tablas, API y pantallas |
| Marca «busca compañero» | **No existe** | Sin campo en `user_profiles` ni en `bookings` | Campo, filtro y privacidad |
| Reservar para un buddy | **En parte** | Una reserva lleva N personas (`participants`); las plazas 2 a N son «Acompañante de…» sin cuenta (S:7375, J:2386). El nombre de un acompañante solo lo cambia el centro, con la acción `entry` (S:10892), que la web no usa | Reservar a nombre de otra cuenta, avisarle y que firme su descargo desde su móvil |
| Mover a un buceador a otra salida | **En parte** | Centro: `POST /api/bookings/{id}/reschedule` solo a otra salida **del mismo servicio** (S:11791-11800; J:5431). Buceador: cambio de fecha con o sin aprobación (S:10752; J:2260). El manifiesto solo mueve entre grupos de la misma salida (`assign`, S:10882) | Mover a una salida de otro servicio, cobrando o devolviendo la diferencia (pendiente de decisión en v50.41) |
| Reserva manual del centro | **Existe** | `POST /api/center/bookings/manual` (S:12783); ventana «Nueva reserva» (J:3466) | Solo centros: el freelance no puede (S:12785, `require_role center`) |
| «Cartel de plazas libres» | **Existe** | `openPosterStudio` (J:4413); `GET /api/center/poster-qr` (S:9549) | — |
| Promociones con QR y canje | **Existe** | Promociones del centro (J:1867-1936; S:9461-9490, S:12291-12365); canje `POST /api/promo/{código}/redeem` (S:12354) | Solo centros con plan Pro; el freelance no tiene promociones |
| Lista del barco y manifiesto sin conexión, y en PDF | **En parte** | Sin conexión: sí, `#/barco` guarda el día en el dispositivo (J:1971-2048; `GET /api/manifest/day`, S:10086), solo hoy y mañana (S:10090). PDF: no, solo la impresión del navegador (J:2418). Los PDF del servidor son el justificante (S:7096), la ficha del buceador (S:7222) y el descargo (S:7465) | PDF del manifiesto y más días (7 días y cursos, según `docs/agenda/estado-actual.md`) |
| Check-in con QR | **En parte** | El buceador escanea el QR del centro (`#/checkin`, `POST /api/checkin/{código}`, S:12562): comparte su ficha y se registra la visita, no la presencia en una salida. El QR de la reserva abre una página de solo lectura (S:10046; J:2495). La presencia se marca a mano en `#/barco` (J:2029) | Que escanear el QR de la reserva marque «Presente» en el manifiesto, también sin conexión (QR firmado) |
| Recuento a bordo | **En parte** | «Presentes x/y» por salida (J:2017, J:2031) y carga por barco «n/capacidad» en el manifiesto (J:2408) | Recuento de subida y de vuelta al barco |
| Estado del mar | **No existe** | Solo la opción de punto «Según el estado del mar» de una salida (S:11123; J:3274). No hay tabla `sea_conditions` (aparece en «Lo que hay que añadir», doc. 02) | Descarga de boyas de Puertos del Estado y datos por punto |
| Calendario iCal: exportar e importar | **En parte** | Exportar: sí (`ical_feed`, S:3368; `GET /api/provider/ical`, S:9289). Importar: no (`docs/agenda/estado-actual.md`: «No importa calendarios externos») | Importar calendarios externos |
| Medias jornadas | **Existe** | `UNITS` y `PARTS` (`app/wod/agenda.py:15-17`); «Por la mañana / Por la tarde» (J:1438-1440) | Con plan `agenda_days`. Los bloqueos de agenda son solo del freelance (`require_role freelance`, S:9544, S:11111) |
| Cursos de varios días | **En parte** | Se puede vender un servicio «por días» (días seguidos). No hay curso con programa de sesiones; un curso por salidas solo ocupa el día 1 (`docs/agenda/estado-actual.md`, §3) | Curso con sesiones, instructor ocupado todos los días y plantillas |
| Vista por recursos (barcos × instructores) | **No existe** | El planning solo tiene «Mes» y «Lista» (J:4102). La tabla `resources` existe (S:1696) pero solo la usa la agenda del freelance | Vista y control de solapes de barcos e instructores |
| Botón de WhatsApp manual con mensaje rellenado en el idioma del cliente | **No existe** | El único enlace `wa.me` comparte el enlace de reservas (S:9301). El aviso a un cliente va por email y a sus «Avisos» (`POST /api/messages`, J:2488) | Botón por cliente con texto en su idioma |
| Estado de la conexión de WhatsApp Business | **Existe** | Panel «Avisos y WhatsApp» (J:2175-2215); estado en `GET /api/avisos/ajustes` (S:9314); `verify_connection` (`app/wod/whatsapp.py:118`) | — |
| Panel de avisos masivos | **Existe** | Cancelar salida o cambiar hora o punto y avisar a todos, con vista previa, deshacer y estado (J:2087-2166; S:11590-11602); tipos en `app/wod/avisos.py:19` | Son avisos de una salida. No hay un aviso libre del centro a todos sus clientes (el envío de novedades es solo de administración, J:5442) |
| Devoluciones totales o parciales | **Existe** | `POST /api/bookings/{id}/refund` (S:11810); ventana «Devolver dinero» (J:1789) | Solo propietario (S:3539) |
| Reseñas y respuestas | **Existe** | Reseña del buceador (S:10941); respuesta del centro (S:11907); tarjetas (J:389-485) | Solo para centros (`center_reviews`): el freelance no tiene reseñas. Se responde desde la ficha pública, sin lista en el panel. Basta reserva pagada, no check-in (S:10953) |
| Exportar datos | **Existe** | Buceador: `GET /api/account/export` JSON y ZIP (S:9213-9218). Centro y freelance: CSV `GET /api/center/export` (S:9274) | — |
| Eliminar la cuenta | **En parte** | Solo cuentas de buceador (S:11715); centro y freelance «se dan de baja escribiéndonos» | Baja desde la app para centro y freelance (Apple exige poder borrar cualquier cuenta creada en la app) |
| Lista de sesiones abiertas | **No existe** | Hay tabla `sessions` (S:473), pero ninguna ruta para listarlas o cerrarlas. Solo se cierran las demás al cambiar la contraseña (S:12160) o activar los dos pasos (S:10621) | Lista por dispositivo y «cerrar» (`devices` en doc. 02) |
| Ajuste de unidades | **No existe** | Metros y kilos fijos: «Lastre habitual en kg» (J:1353), «Profundidad máxima (m)» (J:2527) | Metros/pies, kg/lb, °C/°F, bar/psi |
| Tamaño del texto | **No existe** | Ningún ajuste de tamaño de letra en la web | Respetar el tamaño del sistema y, si se quiere, un ajuste propio |
| Temas | **Un solo tema (confirmado)** | `docs/notas-de-version/v50.45.md`: «la web tiene un solo tema (con imágenes por temporada)». `applySiteTheme` (J:128) solo aplica el color de acento de la temporada que elige la administración. Hay 4 reglas de modo oscuro para unas etiquetas de avisos (CSS `world-dives-v8.css:3047-3050`) | Tema claro y oscuro de la app |
| Notificaciones push | **No existe (confirmado)** | Ni `PushManager` ni `showNotification` en la web; `public/sw.js` tiene 11 líneas y no recibe push. `docs/agenda/estado-actual.md`: «sin notificaciones push» | Tabla `devices`, APNs y FCM, canal `push` en los avisos |
| Log Book | **Existe** | `#/logbook` (J:2504); `GET`/`POST /api/logbook`, `…/update`, `…/delete` (S:10244, S:12134-12149) | Firma del guía |
| Documentos con aviso de caducidad | **Existe** | Buceador: «Caduca en N días» a menos de 45 días (J:1299, J:1321), solo en pantalla. Centro y freelance: seguro con avisos por correo (S:3318-3330) | Aviso (push o correo) de los documentos del buceador |
| Roles del personal | **Existe** | `TEAM_ROLES` (`app/wod/inquilinos.py:28`); permisos en `team_gate` (S:3528-3542) | Ajustarlos al encargo (ver apartado 2): «mis salidas» del instructor, encargado con todo, recepción sin servicios |

- **No existe (10):** buddies, «busca compañero», estado del mar, vista por recursos, WhatsApp manual por cliente,
  lista de sesiones abiertas, unidades, tamaño del texto, push y temas (solo hay uno).
- **Existe en parte (8):** reservar para un buddy, mover a otra salida, manifiesto sin conexión y en PDF, check-in con
  QR, recuento a bordo, iCal (solo exportar), cursos de varios días y eliminar la cuenta (solo buceador).
- **Existe (12):** reserva manual, cartel de plazas libres, promociones con QR, medias jornadas, estado de WhatsApp
  Business, avisos masivos, devoluciones, reseñas y respuestas, exportar datos, Log Book, documentos con caducidad y
  roles del personal. La columna «Qué falta» anota sus límites.

---

## 5. Otras sorpresas y huecos encontrados

1. **Recepción y encargado ven «Cobros y pagos», pero el servidor les responde 403.** La web solo esconde esa pestaña
   al instructor (J:4533); el servidor la reserva al propietario (S:3519).
2. **El encargado no puede guardar barcos** y recibe el mensaje «Tu perfil de instructor es de solo lectura»
   (S:10839).
3. **Funciones del servidor sin pantalla en la web:** cerrar plazas de una salida (`slot-close`, S:11167),
   desvincular Stripe (`connect/unlink`, S:10463) y poner nombre a los acompañantes del manifiesto (`entry`, S:10892).
4. **El freelance no tiene:** reseñas, reserva manual (S:12785), extras, alquiler ni tarifas programadas (S:11024),
   promociones ni ventajas para puntos. Las «ofertas de trabajo» de centros a freelance (`job_offers`) no existen.
5. **Solo el buceador puede borrar su cuenta** (S:11715). Para la App Store hará falta también en centro y freelance.
6. **El instructor ve todas las salidas del centro:** no hay filtro «mis salidas», aunque el guía de cada grupo se
   guarda (`slot_groups.guide_user_id`).
7. **Sin botón «WhatsApp del centro»** para el buceador: la ficha del centro solo tiene «Llamar» y «Escribir» (J:438).
8. **No existe «Repetir reserva»** ni el resumen «Equipo a preparar» (tallas sumadas) que pide el diseño de la app.
9. **Código muerto:** `centerTariffsView` y `loadCenterTariffs` (J:4481-4493) y la vista antigua del centro dentro de
   `renderAdmin` (J:4547-4613) no se llegan a usar, porque el centro entra siempre por `renderCenterWorkspace` (J:4546).
10. **La web usa sesión por cookie** y rutas con ids numéricos. La app necesitará la API `/api/v1/` con token por
    dispositivo descrita en `docs/app-movil/02-datos-y-api.md`, que aún no existe.

---

## 6. Administración: se queda en la web

La administración no pasa a la app. Hoy tiene estas pestañas (J:4572): Inicio, Puntos (alta, edición, archivo,
revisión de propuestas y recorridos virtuales), Reservas, Pagos (incidencias y resolución), Correos (cola, reenvío,
prueba y vista previa), Legal (publicar versiones, retención de datos, contacto y denuncias), Descripciones de puntos,
Mapas, Planes (precios, asignación, excepciones y exportación DAC7), Funciones (interruptores e invitaciones),
Operación (salud del servidor, aviso en la web y restaurar la demo), Recorridos virtuales, Experiencias, Destinos,
Imágenes de la web y temas de temporada, Patrocinio, Usuarios (roles), Centros, Verificaciones de centros,
Correcciones, QR, Actividad y Recompensas; además, moderar reseñas y enviar novedades por correo. Todo esto **se
queda en la web**.
