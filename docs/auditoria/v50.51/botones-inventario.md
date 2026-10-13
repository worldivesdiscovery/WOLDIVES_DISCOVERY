# Inventario de botones, enlaces y formularios

Generado el 13/10/2026 23:09 con `tests/navegador/inventario_botones.py` en Chromium (escritorio 1366×900, es-ES).
Cada papel usa su propio servidor con una copia nueva de la base de demostración (`scripts/crear_demo.py`), sin claves externas (Stripe, WhatsApp/Meta, SMTP, ArcGIS, Firebase) y sin salida a internet.

## Cómo se ha probado

- Se abren todas las pantallas a las que llega cada papel: rutas públicas, páginas de la cuenta, cada pestaña del panel y cada subpestaña (se descubren siguiendo los enlaces internos y las pestañas).
- En cada pantalla se enumeran los elementos visibles: `a[href]`, `button`, `[role=button]`, `input[type=submit|button]`, `select` y formularios. Cada uno se prueba aislado: se recarga la pantalla, se pulsa (un formulario se envía **vacío**; en un desplegable se elige otra opción), se cancela cualquier `confirm()`/`prompt()` y se observa durante ~1,5 s.
- **Funciona**: efecto visible (navegación, ventana, aviso, validación, cambio de estado o de contenido, descarga) sin error de JavaScript ni 5xx.
- **Depende de clave pendiente**: la respuesta o el aviso dicen que falta configurar un servicio (Stripe, WhatsApp, correo SMTP, ArcGIS/satélite, Firebase/push, Wikimedia).
- **Sin efecto**: no pasa nada visible ni se llama al servidor; antes de darlo por bueno se repite en una pantalla recién abierta esperando 3,5 s. **Error**: error de JavaScript, respuesta 5xx, enlace roto, ruta inexistente o mensaje técnico a la vista.
- **No probado**: el elemento ya no aparece al volver a abrir la pantalla (ni siquiera con una copia nueva de la base).
- **Desactivado (correcto)**: desactivado con un texto que explica por qué; **Desactivado (sin explicación)**: sin ese texto.
- Los enlaces externos no se abren: se comprueba que son direcciones `https` válidas (o `mailto:`/`tel:` bien formados). Los enlaces a archivos del propio servidor se piden y se comprueba la respuesta.
- La cabecera, el pie y el menú lateral de los paneles se prueban una vez por papel (en la primera pantalla donde aparecen). En listas de 3 o más elementos iguales se prueban los 2 primeros (el primero si son enlaces); un enlace interno que ya se ha pulsado en otra pantalla del mismo papel se anota con el mismo resultado («Mismo enlace…»).
- Con sesión, cada papel se recorre en dos partes a la vez (páginas públicas y páginas privadas: cuenta y panel), cada una con su servidor y su copia nueva de la base. Si una prueba cambia los datos y un elemento desaparece, se vuelve a una copia nueva.
- «Cerrar sesión», «Borrar/Cerrar mi cuenta», «Restaurar demo» y parecidos se prueban al final del papel, solo hasta la confirmación (que se cancela).

## Resumen por papel

| Papel | Pantallas | Pantallas con error al abrir | Elementos | Funciona | Depende de clave pendiente | Sin efecto | Error | Desactivado (correcto) | Desactivado (sin explicación) | No probado |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Visitante (sin sesión) | 34 | 0 | 632 | 624 | 3 | 0 | 0 | 5 | 0 | 0 |
| Buceador (buzo.prueba) | 47 | 0 | 762 | 754 | 3 | 0 | 0 | 5 | 0 | 0 |
| Centro propietario (centro.prueba) | 75 | 0 | 1006 | 991 | 5 | 0 | 0 | 10 | 0 | 0 |
| Instructor del centro (instructor.prueba) | 66 | 0 | 930 | 917 | 3 | 0 | 0 | 10 | 0 | 0 |
| Freelance (freelance.prueba) | 61 | 0 | 843 | 831 | 4 | 0 | 0 | 8 | 0 | 0 |
| Administración (cuenta creada para la prueba) | 62 | 0 | 892 | 881 | 3 | 0 | 0 | 8 | 0 | 0 |
| **Total** | 345 | 0 | 5065 | **4998** | **21** | **0** | **0** | **46** | **0** | **0** |

## Hallazgos: «Error» y «Sin efecto»

Ninguno.

## Depende de una clave pendiente

| Papel | Pantalla | Elemento | Detalle |
|---|---|---|---|
| Visitante (sin sesión) | Encuentra tu próxima inmersión `#/` | Satélite Disponible próximamente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Visitante (sin sesión) | El mapa del buceo `#/explorar` | Satélite Disponible próximamente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Visitante (sin sesión) | Blue Hole, Dahab `#/punto?id=34` | Satélite | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Relieve orientativo (GEBCO). No sirve para navegar ni para la seguridad en el mar. Seguridad en el buceo» |
| Buceador (buzo.prueba) | Encuentra tu próxima inmersión `#/` | Satélite Disponible próximamente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Buceador (buzo.prueba) | El mapa del buceo `#/explorar` | Satélite Disponible próximamente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Buceador (buzo.prueba) | Blue Hole, Dahab `#/punto?id=34` | Satélite | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Relieve orientativo (GEBCO). No sirve para navegar ni para la seguridad en el mar. Seguridad en el buceo» |
| Centro propietario (centro.prueba) | Encuentra tu próxima inmersión `#/` | Satélite Disponible próximamente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Centro propietario (centro.prueba) | El mapa del buceo `#/explorar` | Satélite Disponible próximamente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Centro propietario (centro.prueba) | Blue Hole, Dahab `#/punto?id=34` | Satélite | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Relieve orientativo (GEBCO). No sirve para navegar ni para la seguridad en el mar. Seguridad en el buceo» |
| Centro propietario (centro.prueba) | Bahía Coralina Centro de Buceo · ▤ Cobros y pagos `#/admin?tab=payments` | Abrir mi panel de Stripe | Clave pendiente: Stripe · Aviso: «Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el servidor).» · POST /api/payments/connect/login → 400 «Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el ser» |
| Centro propietario (centro.prueba) | Bahía Coralina Centro de Buceo · ▤ Cobros y pagos `#/admin?tab=payments` | Actualizar estado | Clave pendiente: Stripe · Aviso: «Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el servidor).» · POST /api/payments/connect/sync → 400 «Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el ser» |
| Centro propietario (centro.prueba) | Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas (y en 1 pantallas más) `#/admin?tab=services` | (aviso en la pantalla) | Stripe: «2 servicios no se pueden reservar. Usan «Pago al reservar» y los cobros online no están activos: Bautizo de buceo, Inmersión simple en barco. Actívalos en Cobros y pagos o cambia esos servicios a «Baj» |
| Centro propietario (centro.prueba) | Bahía Coralina Centro de Buceo · ↔ Web e integraciones `#/admin?tab=integration` | (aviso en la pantalla) | servicio sin configurar: «● Sin configurar» |
| Centro propietario (centro.prueba) | Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp `#/admin?tab=avisos` | (aviso en la pantalla) | WhatsApp (Meta): «WhatsApp aún no está activado en WORLDIVES. Mientras tanto, los avisos salen por correo y en la app.» |
| Instructor del centro (instructor.prueba) | Encuentra tu próxima inmersión `#/` | Satélite Disponible próximamente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Instructor del centro (instructor.prueba) | El mapa del buceo `#/explorar` | Satélite Disponible próximamente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Instructor del centro (instructor.prueba) | Blue Hole, Dahab `#/punto?id=34` | Satélite | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Relieve orientativo (GEBCO). No sirve para navegar ni para la seguridad en el mar. Seguridad en el buceo» |
| Instructor del centro (instructor.prueba) | Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas (y en 1 pantallas más) `#/admin?tab=services` | (aviso en la pantalla) | Stripe: «2 servicios no se pueden reservar. Usan «Pago al reservar» y los cobros online no están activos: Bautizo de buceo, Inmersión simple en barco. Actívalos en Cobros y pagos o cambia esos servicios a «Baj» |
| Instructor del centro (instructor.prueba) | Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp `#/admin?tab=avisos` | (aviso en la pantalla) | WhatsApp (Meta): «WhatsApp aún no está activado en WORLDIVES. Mientras tanto, los avisos salen por correo y en la app.» |
| Freelance (freelance.prueba) | Encuentra tu próxima inmersión `#/` | Satélite Disponible próximamente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Freelance (freelance.prueba) | El mapa del buceo `#/explorar` | Satélite Disponible próximamente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Freelance (freelance.prueba) | Blue Hole, Dahab `#/punto?id=34` | Satélite | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Relieve orientativo (GEBCO). No sirve para navegar ni para la seguridad en el mar. Seguridad en el buceo» |
| Freelance (freelance.prueba) | Diego Arenas · € Cobros y pagos `#/admin?tab=payments` | Activar los cobros online | Clave pendiente: Stripe · Aviso: «Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el servidor).» · POST /api/payments/connect/onboard → 400 «Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el ser» |
| Freelance (freelance.prueba) | Diego Arenas · € Cobros y pagos `#/admin?tab=payments` | (aviso en la pantalla) | servicio sin configurar: «● Cobros sin configurar» |
| Freelance (freelance.prueba) | Diego Arenas · ✆ Avisos y WhatsApp `#/admin?tab=avisos` | (aviso en la pantalla) | WhatsApp (Meta): «WhatsApp aún no está activado en WORLDIVES. Mientras tanto, los avisos salen por correo y en la app.» |
| Administración (cuenta creada para la prueba) | Encuentra tu próxima inmersión `#/` | Satélite Disponible próximamente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Administración (cuenta creada para la prueba) | El mapa del buceo `#/explorar` | Satélite Disponible próximamente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Administración (cuenta creada para la prueba) | Blue Hole, Dahab `#/punto?id=34` | Satélite | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Relieve orientativo (GEBCO). No sirve para navegar ni para la seguridad en el mar. Seguridad en el buceo» |
| Administración (cuenta creada para la prueba) | Centro de control de WORLDIVES · Inicio (y en 24 pantallas más) `#/admin` | (aviso en la pantalla) | ArcGIS (satélite): «Añade la clave de ArcGIS para activar el satélite.» |
| Administración (cuenta creada para la prueba) | Centro de control de WORLDIVES · Mapas `#/admin?tab=maps` | (aviso en la pantalla) | ArcGIS (satélite): «El mapa base se sirve desde nuestro servidor. La vista satélite pasa por nuestro servidor con la clave de ArcGIS, que nunca llega al navegador; aquí controlas cuántas teselas se sirven al mes para no » |
| Administración (cuenta creada para la prueba) | Centro de control de WORLDIVES · Mapas `#/admin?tab=maps` | (aviso en la pantalla) | ArcGIS (satélite): «Vista satélite (ARCGIS_API_KEY)» |
| Administración (cuenta creada para la prueba) | Centro de control de WORLDIVES · Mapas `#/admin?tab=maps` | (aviso en la pantalla) | ArcGIS (satélite): «Añade la clave de ArcGIS para activar el satélite. Ponla en ARCGIS_API_KEY, en el archivo .env del servidor (nunca en el código), y reinicia. Mientras tanto, los visitantes ven «Satélite» desactivado » |
| Administración (cuenta creada para la prueba) | Centro de control de WORLDIVES · Pagos `#/admin?tab=adminpay` | (aviso en la pantalla) | Stripe: «Clave de Stripe sin configurar» |
| Administración (cuenta creada para la prueba) | Centro de control de WORLDIVES · Pagos `#/admin?tab=adminpay` | (aviso en la pantalla) | servicio sin configurar: «Webhook de la plataforma sin configurar» |
| Administración (cuenta creada para la prueba) | Centro de control de WORLDIVES · Pagos `#/admin?tab=adminpay` | (aviso en la pantalla) | servicio sin configurar: «Webhook de Connect sin configurar» |
| Administración (cuenta creada para la prueba) | Centro de control de WORLDIVES · Correos `#/admin?tab=emails` | (aviso en la pantalla) | Correo (SMTP): «Envío pendiente de configurar» |
| Administración (cuenta creada para la prueba) | Centro de control de WORLDIVES · Correos `#/admin?tab=emails` | (aviso en la pantalla) | Correo (SMTP): «Los correos se guardan en la cola y se enviarán en cuanto configures el correo corporativo. En el servidor, define WOD_SMTP_HOST, WOD_SMTP_PORT, WOD_SMTP_USER, WOD_SMTP_PASSWORD y WOD_MAIL_FROM, y rei» |
| Administración (cuenta creada para la prueba) | Centro de control de WORLDIVES · Operación `#/admin?tab=ops` | (aviso en la pantalla) | Correo (SMTP): «Sin WOD_SMTP_HOST: los correos esperan en la cola (72 h) hasta configurar el proveedor (docs/despliegue/README.md).» |
| Administración (cuenta creada para la prueba) | Centro de control de WORLDIVES · Operación `#/admin?tab=ops` | (aviso en la pantalla) | Stripe: «Sin STRIPE_SECRET_KEY: los cobros online están desactivados.» |
| Administración (cuenta creada para la prueba) | Centro de control de WORLDIVES · Operación `#/admin?tab=ops` | (aviso en la pantalla) | ArcGIS (satélite): «Sin ARCGIS_API_KEY: la vista satélite no aparece.» |

## Inventario completo

### Visitante (sin sesión)

34 pantallas, 632 elementos probados en 10 min 34 s.

#### Cabecera, pie y elementos flotantes (comunes a todas las pantallas)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Encuentra tu próxima inmersión · flotante | Saltar al contenido | Enlace | Funciona | Desplaza la página · clic por JavaScript (no se puede pulsar con el ratón) |
| Encuentra tu próxima inmersión · cabecera | WORLDIVES DISCOVERY · inicio | Enlace | Funciona | Enlace a la pantalla en la que ya se está |
| Encuentra tu próxima inmersión · cabecera | Explorar | Enlace | Funciona | Abre #/explorar |
| Encuentra tu próxima inmersión · cabecera | Puntos de buceo | Enlace | Funciona | Abre #/puntos |
| Encuentra tu próxima inmersión · cabecera | Centros | Enlace | Funciona | Abre #/centros |
| Encuentra tu próxima inmersión · cabecera | Tipos de buceo | Enlace | Funciona | Abre #/tipos |
| Encuentra tu próxima inmersión · cabecera | Experiencias | Enlace | Funciona | Abre #/experiencias |
| Encuentra tu próxima inmersión · cabecera | Top 10 buceos | Enlace | Funciona | Abre #/top10 |
| Encuentra tu próxima inmersión · cabecera | Seleccionar idioma | Desplegable | Funciona | Recarga la página con /?lang=en |
| Encuentra tu próxima inmersión · cabecera | Iniciar sesión | Enlace | Funciona | Abre #/login |
| Encuentra tu próxima inmersión · pie de página | Explorar el mapa | Enlace | Funciona | Mismo enlace (#/explorar) que «Explorar» en «Encuentra tu próxima inmersión»: Abre #/explorar |
| Encuentra tu próxima inmersión · pie de página | Top 10 cerca de ti | Enlace | Funciona | Mismo enlace (#/top10) que «Top 10 buceos» en «Encuentra tu próxima inmersión»: Abre #/top10 |
| Encuentra tu próxima inmersión · pie de página | Centros de buceo | Enlace | Funciona | Mismo enlace (#/centros) que «Centros» en «Encuentra tu próxima inmersión»: Abre #/centros |
| Encuentra tu próxima inmersión · pie de página | Viajes y vida a bordo | Enlace | Funciona | Mismo enlace (#/experiencias) que «Experiencias» en «Encuentra tu próxima inmersión»: Abre #/experiencias |
| Encuentra tu próxima inmersión · pie de página | Mi cuenta | Enlace | Funciona | Abre #/login?next=%23%2Fcuenta |
| Encuentra tu próxima inmersión · pie de página | Log Book | Enlace | Funciona | Abre #/login?next=%23%2Flogbook |
| Encuentra tu próxima inmersión · pie de página | Recompensas | Enlace | Funciona | Abre #/login?next=%23%2Frecompensas |
| Encuentra tu próxima inmersión · pie de página | Mis puntos | Enlace | Funciona | Abre #/login?next=%23%2Fmis-puntos |
| Encuentra tu próxima inmersión · pie de página | Dar de alta mi centro | Enlace | Funciona | Abre #/registro |
| Encuentra tu próxima inmersión · pie de página | Panel del centro | Enlace | Funciona | Abre #/login?next=%23%2Fadmin |
| Encuentra tu próxima inmersión · pie de página | Condiciones para centros | Enlace | Funciona | Abre #/legal/condiciones-centros |
| Encuentra tu próxima inmersión · pie de página | Aviso legal | Enlace | Funciona | Abre #/legal/aviso-legal |
| Encuentra tu próxima inmersión · pie de página | Privacidad | Enlace | Funciona | Abre #/legal/privacidad |
| Encuentra tu próxima inmersión · pie de página | Cookies | Enlace | Funciona | Abre #/legal/cookies |
| Encuentra tu próxima inmersión · pie de página | Condiciones de uso | Enlace | Funciona | Abre #/legal/condiciones-buceadores |
| Encuentra tu próxima inmersión · pie de página | Condiciones de reserva | Enlace | Funciona | Abre #/legal/condiciones-reserva |
| Encuentra tu próxima inmersión · pie de página | Para centros | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Encuentra tu próxima inmersión · pie de página | Denunciar contenido | Enlace | Funciona | Abre #/legal/denuncias |
| Encuentra tu próxima inmersión (aviso de cookies) · aviso de cookies | Más información | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Encuentra tu próxima inmersión (aviso de cookies) · aviso de cookies | Entendido | Botón | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) |

#### Encuentra tu próxima inmersión · `#/`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Encuentra tu próxima inmersión | Buscar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «⌕ Escribe al menos dos letras El nombre de un punto, una ciudad, una isla o un centro de buceo.» |
| Encuentra tu próxima inmersión | Cerca de mí | Enlace | Funciona | Mismo enlace (#/top10) que «Top 10 buceos» en «Encuentra tu próxima inmersión»: Abre #/top10 |
| Encuentra tu próxima inmersión | Pecios | Enlace | Funciona | Abre #/tipos?t=pecios-y-naufragios |
| Encuentra tu próxima inmersión | Cuevas | Enlace | Funciona | Abre #/tipos?t=cuevas-y-cavernas |
| Encuentra tu próxima inmersión | Arrecifes | Enlace | Funciona | Abre #/tipos?t=arrecifes |
| Encuentra tu próxima inmersión | Centros con reserva online | Enlace | Funciona | Abre #/centros?only=online |
| Encuentra tu próxima inmersión | Abrir el explorador → | Enlace | Funciona | Mismo enlace (#/explorar) que «Explorar» en «Encuentra tu próxima inmersión»: Abre #/explorar |
| Encuentra tu próxima inmersión | 01 Europa 108 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (32 elementos): «4» |
| Encuentra tu próxima inmersión | 02 Asia 104 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (26 elementos): «15» |
| Encuentra tu próxima inmersión | 03 América 24 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (25 elementos): «3» |
| Encuentra tu próxima inmersión | 04 África y Mar Rojo 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (34 elementos): «2» |
| Encuentra tu próxima inmersión | 05 Oceanía 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (11 elementos): «2» |
| Encuentra tu próxima inmersión | 06 Caribe 17 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (27 elementos): «8» |
| Encuentra tu próxima inmersión | Mapa | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| Encuentra tu próxima inmersión | Satélite Disponible próximamente | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Encuentra tu próxima inmersión | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (18 elementos): «Leaflet» |
| Encuentra tu próxima inmersión | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (19 elementos): «2» · hay 15 más iguales en la lista (no se prueban todos) |
| Encuentra tu próxima inmersión | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (7 elementos): «Rainbow Reef» |
| Encuentra tu próxima inmersión | Mauritius – Cathedral | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» · hay 1 más iguales en la lista (no se prueban todos) |
| Encuentra tu próxima inmersión | Tofo – Manta Reef | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» |
| Encuentra tu próxima inmersión | Zoom in | Enlace | Funciona | Muestra contenido nuevo (64 elementos): «2» |
| Encuentra tu próxima inmersión | Zoom out | Enlace | Funciona | Cambia su estado (class: leaflet-control-zoom-out → leaflet-control-zoom-out leaflet-disabled) · Cambia la pantalla (4 elementos nuevos, 0 quitados) |
| Encuentra tu próxima inmersión | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Encuentra tu próxima inmersión | OpenStreetMap contributors | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Encuentra tu próxima inmersión | Ver todos los tipos → | Enlace | Funciona | Mismo enlace (#/tipos) que «Tipos de buceo» en «Encuentra tu próxima inmersión»: Abre #/tipos |
| Encuentra tu próxima inmersión | Aguas profundas | Enlace | Funciona | Abre #/tipos?t=aguas-profundas |
| Encuentra tu próxima inmersión | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| Encuentra tu próxima inmersión | Paredes | Enlace | Funciona | Abre #/tipos?t=paredes |
| Encuentra tu próxima inmersión | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| Encuentra tu próxima inmersión | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| Encuentra tu próxima inmersión | Pináculos | Enlace | Funciona | Abre #/tipos?t=pinaculos |

#### El mapa del buceo · `#/explorar`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| El mapa del buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| El mapa del buceo | Todos | Botón | Funciona | Muestra contenido nuevo (36 elementos): «2» |
| El mapa del buceo | Arrecifes | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (58 elementos): «2» |
| El mapa del buceo | Paredes | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (45 elementos): «2» |
| El mapa del buceo | Pecios | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (32 elementos): «2» |
| El mapa del buceo | Cuevas | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (32 elementos): «3» |
| El mapa del buceo | Muck | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (30 elementos): «3» |
| El mapa del buceo | Pináculos | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (27 elementos): «7» |
| El mapa del buceo | Profundas | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (59 elementos): «2» |
| El mapa del buceo | 01 Europa 108 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (40 elementos): «2» |
| El mapa del buceo | 02 Asia 104 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (22 elementos): «2» |
| El mapa del buceo | 03 América 24 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (15 elementos): «2» |
| El mapa del buceo | 04 África y Mar Rojo 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (25 elementos): «2» |
| El mapa del buceo | 05 Oceanía 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (31 elementos): «2» |
| El mapa del buceo | 06 Caribe 17 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (32 elementos): «2» |
| El mapa del buceo | Mapa | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (26 elementos): «Leaflet» |
| El mapa del buceo | Satélite Disponible próximamente | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| El mapa del buceo | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (26 elementos): «Leaflet» |
| El mapa del buceo | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (31 elementos): «2» · clic forzado (otro elemento lo tapa) · hay 29 más iguales en la lista (no se prueban todos) |
| El mapa del buceo | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (14 elementos): «Rainbow Reef» |
| El mapa del buceo | Mauritius – Cathedral | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» · hay 3 más iguales en la lista (no se prueban todos) |
| El mapa del buceo | Tofo – Manta Reef | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» |
| El mapa del buceo | Seguridad en el buceo | Enlace | Funciona | Abre #/legal/seguridad |
| El mapa del buceo | Zoom in | Enlace | Funciona | Muestra contenido nuevo (87 elementos): «2» |
| El mapa del buceo | Zoom out | Enlace | Funciona | Cambia la pantalla (10 elementos nuevos, 0 quitados) |
| El mapa del buceo | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |

#### Puntos de buceo · `#/puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Puntos de buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Puntos de buceo | Puntos de buceo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (68 elementos): «Todo el mundo» |
| Puntos de buceo | Zona Todo el mundo Europa (108) Asia (104) América (24) África y Mar Rojo (20) Oceanía (20) Caribe (17) | Desplegable | Funciona | Abre #/puntos?zone=Europa |
| Puntos de buceo | Para empezar | Botón | Funciona | Abre #/puntos?level=start |
| Puntos de buceo | Intermedio | Botón | Funciona | Abre #/puntos?level=mid |
| Puntos de buceo | Avanzado | Botón | Funciona | Abre #/puntos?level=adv |
| Puntos de buceo | Con centro que lo ofrece | Botón | Funciona | Abre #/puntos?only=centers |
| Puntos de buceo | Confirmación inmediata | Botón | Funciona | Abre #/puntos?only=instant |
| Puntos de buceo | Tipo de buceo Cualquier tipo Arrecifes Paredes Pecios y naufragios Cuevas y cavernas Cenotes Muck Canales Caño | Desplegable | Funciona | Abre #/puntos?type=arrecifes |
| Puntos de buceo | País Todos los países España (93) Filipinas (30) Indonesia (25) Malasia (15) Maldivas (13) Tailandia (13) Egip | Desplegable | Funciona | Abre #/puntos?country=Espa%C3%B1a |
| Puntos de buceo | Ordenar Recomendados Nombre A-Z Más profundos Menos profundos Mejor valorados | Desplegable | Funciona | Abre #/puntos?sort=name |
| Puntos de buceo | ¿Cómo ordenamos? | Enlace | Funciona | Abre #/legal/clasificacion |
| Puntos de buceo | #/punto?id=34 | Enlace | Funciona | Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Blue Hole, Dahab | Enlace | Funciona | Mismo enlace (#/punto?id=34) que «#/punto?id=34» en «Puntos de buceo»: Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Ver punto | Enlace | Funciona | Mismo enlace (#/punto?id=34) que «#/punto?id=34» en «Puntos de buceo»: Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Mostrar más puntos (281) | Botón | Funciona | Cambia su estado (disabled: sin atributo → vacío) · Muestra contenido nuevo (13 elementos): «Arrecifes Paredes Portitxol Norte Marina Alta · Xàbia · España Moderado Arrecife · Pared · Fondo arenoso Ubicación por v» |

#### Centros de buceo · `#/centros`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centros de buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Centros de buceo | Centros de buceo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (11 elementos): «Todos los países» |
| Centros de buceo | País Todos los países España (2) | Desplegable | Funciona | Abre #/centros?country=Espa%C3%B1a |
| Centros de buceo | Confirmación inmediata | Botón | Funciona | Abre #/centros?only=instant |
| Centros de buceo | Reserva online | Botón | Funciona | Abre #/centros?only=online |
| Centros de buceo | Plazas esta semana | Botón | Funciona | Abre #/centros?only=week |
| Centros de buceo | Cursos | Botón | Funciona | Abre #/centros?only=courses |
| Centros de buceo | Bautizos | Botón | Funciona | Abre #/centros?only=try |
| Centros de buceo | Viajes | Botón | Funciona | Abre #/centros?only=trips |
| Centros de buceo | Con reseñas | Botón | Funciona | Abre #/centros?only=reviews |
| Centros de buceo | Tipo de buceo Cualquier tipo de buceo Arrecifes Paredes Pecios y naufragios Cuevas y cavernas Cenotes Muck Can | Desplegable | Funciona | Abre #/centros?type=arrecifes |
| Centros de buceo | Ordenar Recomendados Mejor valorados Más reseñas Precio más bajo Nombre A-Z | Desplegable | Funciona | Abre #/centros?sort=rating |
| Centros de buceo | ¿Cómo ordenamos? | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Centros de buceo | Bajo petición Plazas esta semana | Enlace | Funciona | Abre #/centro?id=31 |
| Centros de buceo | Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Centros de buceo | Reservar | Enlace | Funciona | Abre #/reservar?center=31 |
| Centros de buceo | Bajo petición Plazas esta semana | Enlace | Funciona | Abre #/centro?id=32 |
| Centros de buceo | Escafandra Medes | Enlace | Funciona | Mismo enlace (#/centro?id=32) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=32 |
| Centros de buceo | Reservar | Enlace | Funciona | Abre #/reservar?center=32 |
| Centros de buceo | Dar de alta mi centro | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### ¿Qué inmersión te apetece? · `#/tipos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| ¿Qué inmersión te apetece? | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| ¿Qué inmersión te apetece? | Todos | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| ¿Qué inmersión te apetece? | Para empezar | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Con experiencia | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Avanzado y técnico | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| ¿Qué inmersión te apetece? | Paredes | Enlace | Funciona | Mismo enlace (#/tipos?t=paredes) que «Paredes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=paredes |
| ¿Qué inmersión te apetece? | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| ¿Qué inmersión te apetece? | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| ¿Qué inmersión te apetece? | Cenotes | Enlace | Funciona | Abre #/tipos?t=cenotes |
| ¿Qué inmersión te apetece? | Muck | Enlace | Funciona | Abre #/tipos?t=muck |
| ¿Qué inmersión te apetece? | Canales | Enlace | Funciona | Abre #/tipos?t=canales |
| ¿Qué inmersión te apetece? | Cañones | Enlace | Funciona | Abre #/tipos?t=canones |
| ¿Qué inmersión te apetece? | Pináculos | Enlace | Funciona | Mismo enlace (#/tipos?t=pinaculos) que «Pináculos» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pinaculos |
| ¿Qué inmersión te apetece? | Corrientes y deriva | Enlace | Funciona | Abre #/tipos?t=corrientes-y-deriva |
| ¿Qué inmersión te apetece? | Aguas profundas | Enlace | Funciona | Mismo enlace (#/tipos?t=aguas-profundas) que «Aguas profundas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=aguas-profundas |
| ¿Qué inmersión te apetece? | Lagos | Enlace | Funciona | Abre #/tipos?t=lagos |
| ¿Qué inmersión te apetece? | Pilares | Enlace | Funciona | Abre #/tipos?t=pilares |
| ¿Qué inmersión te apetece? | Nocturnas | Enlace | Funciona | Abre #/tipos?t=nocturnas |
| ¿Qué inmersión te apetece? | Playa y esnórquel | Enlace | Funciona | Abre #/tipos?t=playa-y-esnorquel |
| ¿Qué inmersión te apetece? | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| ¿Qué inmersión te apetece? | Muck | Enlace | Funciona | Mismo enlace (#/tipos?t=muck) que «Muck» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=muck |
| ¿Qué inmersión te apetece? | Lagos | Enlace | Funciona | Mismo enlace (#/tipos?t=lagos) que «Lagos» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=lagos |
| ¿Qué inmersión te apetece? | Pilares | Enlace | Funciona | Mismo enlace (#/tipos?t=pilares) que «Pilares» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=pilares |
| ¿Qué inmersión te apetece? | Paredes | Enlace | Funciona | Mismo enlace (#/tipos?t=paredes) que «Paredes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=paredes |
| ¿Qué inmersión te apetece? | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| ¿Qué inmersión te apetece? | Canales | Enlace | Funciona | Mismo enlace (#/tipos?t=canales) que «Canales» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=canales |
| ¿Qué inmersión te apetece? | Pináculos | Enlace | Funciona | Mismo enlace (#/tipos?t=pinaculos) que «Pináculos» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pinaculos |
| ¿Qué inmersión te apetece? | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| ¿Qué inmersión te apetece? | Cenotes | Enlace | Funciona | Mismo enlace (#/tipos?t=cenotes) que «Cenotes» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=cenotes |
| ¿Qué inmersión te apetece? | Cañones | Enlace | Funciona | Mismo enlace (#/tipos?t=canones) que «Cañones» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=canones |
| ¿Qué inmersión te apetece? | Corrientes y deriva | Enlace | Funciona | Mismo enlace (#/tipos?t=corrientes-y-deriva) que «Corrientes y deriva» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=corrientes-y-deriva |
| ¿Qué inmersión te apetece? | Aguas profundas | Enlace | Funciona | Mismo enlace (#/tipos?t=aguas-profundas) que «Aguas profundas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=aguas-profundas |

#### Viajes y vida a bordo · `#/experiencias`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Viajes y vida a bordo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Viajes y vida a bordo | Viajes y vida a bordo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (16 elementos): «Viaje 1 experiencia Costa Blanca España Experiencias de buceo organizadas por centros y profesionales. DESDE 290 € PRÓXI» |
| Viajes y vida a bordo | Todas | Botón | Funciona | Muestra contenido nuevo (8 elementos): «Viaje 1 experiencia Costa Blanca España Experiencias de buceo organizadas por centros y profesionales. DESDE 290 € PRÓXI» |
| Viajes y vida a bordo | Viaje | Botón | Funciona | Abre #/experiencias?kind=Viaje |
| Viajes y vida a bordo | Vida a bordo | Botón | Funciona | Abre #/experiencias?kind=Vida+a+bordo |
| Viajes y vida a bordo | Ordenar Con más salidas Precio más bajo Próxima salida Nombre A-Z | Desplegable | Funciona | Abre #/experiencias?sort=price |
| Viajes y vida a bordo | Viaje 1 experiencia | Enlace | Funciona | Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Costa Blanca | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Ver viajes | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Ver destino | Enlace | Funciona | Abre #/experiencia?id=5 · hay 3 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Empezar a publicar | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### ¿Te apetece bucear? · `#/top10`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| ¿Te apetece bucear? | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| ¿Te apetece bucear? | Radio 25 km 50 km 100 km 250 km 500 km | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Buscar» (sin efecto inmediato, correcto) |
| ¿Te apetece bucear? | Usar mi ubicación | Botón | Funciona | Muestra contenido nuevo (13 elementos): «1 ARRECIFES Cabo San Antonio Marina Alta · Xàbia · España 7–20 m Moderado ★ 4.4 (9) 1 centro 1,9 km Ver inmersión» |
| ¿Te apetece bucear? | Elegir en el mapa | Botón | Funciona | Abre la ventana «Elige tu ubicación» |
| ¿Te apetece bucear? | ¿Te apetece bucear? | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Buscar una localidad» (campo obligatorio) |
| ¿Te apetece bucear? | Marina Alta · Xàbia | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 ARRECIFES Piedras Rotas Marina Alta · Xàbia · España 7–20 m Fácil ★ 4.4 (9) 1 centro 0,8 km Ver inmersión» |
| ¿Te apetece bucear? | Marina Alta y Baixa · Calpe | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 19,3 km Ver inmersión» |
| ¿Te apetece bucear? | Canarias | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (9 elementos): «1 ARRECIFES Las Canteras, Gran Canaria Canarias · España Iniciación 48,3 km Ver inmersión» |
| ¿Te apetece bucear? | Palawan | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (4 elementos): «1 ARRECIFES El Nido – Cadlao Lagoon Palawan · Filipinas 5–20 m Principiante 72,9 km Ver inmersión» |
| ¿Te apetece bucear? | Comunitat Valenciana | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 25,7 km Ver inmersión» |
| ¿Te apetece bucear? | Andalucía | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (6 elementos): «1 ARRECIFES Costa del Sol, Málaga Andalucía · España Iniciación 52,4 km Ver inmersión» |
| ¿Te apetece bucear? | Marina Alta · Moraira | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 9,7 km Ver inmersión» |
| ¿Te apetece bucear? | Cebu | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (12 elementos): «1 ARRECIFES Moalboal – Sardine Run Cebu · Filipinas 5–25 m Principiante 28,1 km Ver inmersión» |
| ¿Te apetece bucear? | Cataluña | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (12 elementos): «1 ARRECIFES Medes – Tascons Islas Medes · España 6–25 m Intermedio ★ 4.8 (6) 1 centro 2,1 km Ver inmersión» |
| ¿Te apetece bucear? | Illes Balears | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (8 elementos): «1 PAREDES El Toro Mallorca · España 10–35 m Intermedio 12,9 km Ver inmersión» |

#### Planes de WORLDIVES · `#/planes`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Planes de WORLDIVES | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Planes de WORLDIVES | Dar de alta mi centro | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### Cómo funcionan los puntos · `#/como-funcionan-los-puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Cómo funcionan los puntos | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Cómo funcionan los puntos | Ver mis puntos | Enlace | Funciona | Mismo enlace (#/mis-puntos) que «Mis puntos» en «Encuentra tu próxima inmersión»: Abre #/login?next=%23%2Fmis-puntos |
| Cómo funcionan los puntos | Ver ventajas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Recompensas» en «Encuentra tu próxima inmersión»: Abre #/login?next=%23%2Frecompensas |

#### Aviso legal · `#/legal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Aviso legal | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Aviso legal | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Aviso legal | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Abre #/legal/reservas |
| Aviso legal | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Aviso legal | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Aviso legal | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Aviso legal | Normas de las reseñas | Enlace | Funciona | Abre #/legal/normas-resenas |
| Aviso legal | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Puntos WORLDIVES | Enlace | Funciona | Abre #/legal/puntos |
| Aviso legal | Declaración de accesibilidad | Enlace | Funciona | Abre #/legal/accesibilidad |
| Aviso legal | Contacto | Enlace | Funciona | Abre #/legal/contacto |
| Aviso legal | Créditos y licencias de terceros | Enlace | Funciona | Abre #/legal/creditos |
| Aviso legal | Condiciones de uso | Enlace | Funciona | Abre #/legal/terminos |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Leer | Botón | Funciona | Abre la ventana «Aviso legal» |
| Aviso legal | 1. Titular del sitio web | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 6 más iguales en la lista (no se prueban todos) |
| Aviso legal | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Iniciar sesión · `#/login`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Iniciar sesión | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Iniciar sesión | Iniciar sesión | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Email» (campo obligatorio) · El navegador no deja enviarlo: «Contraseña» (campo obligatorio) |
| Iniciar sesión | ¿Has olvidado tu contraseña? | Enlace | Funciona | Abre #/recuperar |
| Iniciar sesión | Crear cuenta | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### Crear cuenta · `#/registro`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Crear cuenta | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Crear cuenta | Buceador | Enlace | Funciona | Abre #/registro?tipo=recreational |
| Crear cuenta | Centro de buceo Publica tus salidas y cursos y gestiona tus reservas. | Enlace | Funciona | Abre #/registro?tipo=center |
| Crear cuenta | Profesional | Enlace | Funciona | Abre #/registro?tipo=freelance |
| Crear cuenta | Iniciar sesión | Enlace | Funciona | Mismo enlace (#/login) que «Iniciar sesión» en «Encuentra tu próxima inmersión»: Abre #/login |

#### ¿Has olvidado tu contraseña? · `#/recuperar`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| ¿Has olvidado tu contraseña? | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| ¿Has olvidado tu contraseña? | ¿Has olvidado tu contraseña? | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Email o usuario» (campo obligatorio) |
| ¿Has olvidado tu contraseña? | Volver a iniciar sesión | Enlace | Funciona | Mismo enlace (#/login) que «Iniciar sesión» en «Encuentra tu próxima inmersión»: Abre #/login |

#### Encuentra tu próxima inmersión (aviso de cookies) · `#/`

Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).

#### Condiciones para centros y profesionales · `#/legal/condiciones-centros`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones para centros y profesionales | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones para centros y profesionales | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones para centros y profesionales | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones para centros y profesionales | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones para centros y profesionales | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones para centros y profesionales | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones para centros y profesionales | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones para centros y profesionales | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones para centros y profesionales | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones para centros y profesionales | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones para centros y profesionales | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones para centros y profesionales | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones para centros y profesionales | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones para centros y profesionales | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones para centros y profesionales | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones para centros y profesionales | Planes | Enlace | Funciona | Abre #/planes |
| Condiciones para centros y profesionales | Planes | Enlace | Funciona | Mismo enlace (#/planes) que «Planes» en «Condiciones para centros y profesionales»: Abre #/planes |
| Condiciones para centros y profesionales | normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones para centros y profesionales | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones para centros y profesionales | Leer | Botón | Funciona | Abre la ventana «Condiciones para centros y profesionales» |
| Condiciones para centros y profesionales | 1. Alta y verificación | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 18 más iguales en la lista (no se prueban todos) |
| Condiciones para centros y profesionales | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones para centros y profesionales | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Aviso legal · `#/legal/aviso-legal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Aviso legal | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Aviso legal | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Aviso legal | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Aviso legal | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Aviso legal | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Aviso legal | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Aviso legal | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Aviso legal | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Aviso legal | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Aviso legal | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Aviso legal | Condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/terminos) que «Condiciones de uso» en «Aviso legal»: Abre #/legal/terminos |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Leer | Botón | Funciona | Abre la ventana «Aviso legal» |
| Aviso legal | 1. Titular del sitio web | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 6 más iguales en la lista (no se prueban todos) |
| Aviso legal | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Política de privacidad · `#/legal/privacidad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Política de privacidad | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Política de privacidad | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Política de privacidad | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Política de privacidad | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Política de privacidad | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Política de privacidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de privacidad | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Política de privacidad | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Política de privacidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de privacidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Política de privacidad | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Política de privacidad | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Política de privacidad | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Política de privacidad | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Política de privacidad | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Política de privacidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de privacidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de privacidad | www.aepd.es | Enlace externo | Funciona | Enlace externo a www.aepd.es (no se abre: dirección https válida) |
| Política de privacidad | Leer | Botón | Funciona | Abre la ventana «Política de privacidad» |
| Política de privacidad | 1. Responsable | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 8 más iguales en la lista (no se prueban todos) |
| Política de privacidad | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Política de privacidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Política de cookies y servicios de terceros · `#/legal/cookies`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Política de cookies y servicios de terceros | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Política de cookies y servicios de terceros | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Política de cookies y servicios de terceros | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Política de cookies y servicios de terceros | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Política de cookies y servicios de terceros | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Política de cookies y servicios de terceros | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de cookies y servicios de terceros | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Política de cookies y servicios de terceros | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Política de cookies y servicios de terceros | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de cookies y servicios de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Política de cookies y servicios de terceros | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Política de cookies y servicios de terceros | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Política de cookies y servicios de terceros | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Política de cookies y servicios de terceros | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Política de cookies y servicios de terceros | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Política de cookies y servicios de terceros | Leer | Botón | Funciona | Abre la ventana «Política de cookies y servicios de terceros» |
| Política de cookies y servicios de terceros | Qué usamos | Enlace | Funciona | Cambia tabindex en h2#que-usamos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Política de cookies y servicios de terceros | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Política de cookies y servicios de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de uso para buceadores · `#/legal/condiciones-buceadores`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de uso para buceadores | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de uso para buceadores | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de uso para buceadores | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de uso para buceadores | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de uso para buceadores | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Leer | Botón | Funciona | Abre la ventana «Condiciones de uso para buceadores» |
| Condiciones de uso para buceadores | 1. Qué es WORLDIVES DISCOVERY | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 9 más iguales en la lista (no se prueban todos) |
| Condiciones de uso para buceadores | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de reserva, pago y cancelación · `#/legal/condiciones-reserva`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de reserva, pago y cancelación | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de reserva, pago y cancelación | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de reserva, pago y cancelación | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de reserva, pago y cancelación | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de reserva, pago y cancelación | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de reserva, pago y cancelación | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de reserva, pago y cancelación | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de reserva, pago y cancelación | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de reserva, pago y cancelación | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de reserva, pago y cancelación | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Leer | Botón | Funciona | Abre la ventana «Condiciones de reserva, pago y cancelación» |
| Condiciones de reserva, pago y cancelación | 1. Quién presta la actividad | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 7 más iguales en la lista (no se prueban todos) |
| Condiciones de reserva, pago y cancelación | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Denunciar contenido · `#/legal/denuncias`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Denunciar contenido | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Denunciar contenido | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Denunciar contenido | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Denunciar contenido | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Denunciar contenido | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Denunciar contenido | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Denunciar contenido | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Denunciar contenido | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Denunciar contenido | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Denunciar contenido | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Denunciar contenido | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Denunciar contenido | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Denunciar contenido | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Denunciar contenido | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Denunciar contenido | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Denunciar contenido | Formulario de denuncia | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Motivo» (elige una opción de la lista) · El navegador no deja enviarlo: «Explica por qué es ilegal o incumple las condiciones» (campo obligatorio) |
| Denunciar contenido | Motivo | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Enviar denuncia» (sin efecto inmediato, correcto) |
| Denunciar contenido | Leer | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Denunciar contenido | Qué necesitamos | Enlace | Funciona | Cambia tabindex en h2#que-necesitamos (sin atributo → -1) · hay 2 más iguales en la lista (no se prueban todos) |
| Denunciar contenido | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Denunciar contenido | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Seguridad en el buceo · `#/legal/seguridad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Seguridad en el buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Seguridad en el buceo | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Seguridad en el buceo | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Seguridad en el buceo | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Seguridad en el buceo | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Seguridad en el buceo | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Seguridad en el buceo | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Seguridad en el buceo | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Seguridad en el buceo | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Seguridad en el buceo | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Seguridad en el buceo | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Seguridad en el buceo | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Seguridad en el buceo | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Seguridad en el buceo | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Seguridad en el buceo | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Seguridad en el buceo | Leer | Botón | Funciona | Abre la ventana «Seguridad en el buceo» |
| Seguridad en el buceo | Antes de reservar | Enlace | Funciona | Cambia tabindex en h2#antes-de-reservar (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Seguridad en el buceo | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Seguridad en el buceo | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Cómo ordenamos los resultados · `#/legal/clasificacion`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Cómo ordenamos los resultados | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Cómo ordenamos los resultados | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Cómo ordenamos los resultados | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Cómo ordenamos los resultados | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Cómo ordenamos los resultados | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Cómo ordenamos los resultados | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Cómo ordenamos los resultados | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Cómo ordenamos los resultados | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Cómo ordenamos los resultados | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Cómo ordenamos los resultados | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Cómo ordenamos los resultados | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Cómo ordenamos los resultados | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Cómo ordenamos los resultados | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Cómo ordenamos los resultados | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Cómo ordenamos los resultados | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Cómo ordenamos los resultados | Leer | Botón | Funciona | Abre la ventana «Cómo ordenamos los resultados» |
| Cómo ordenamos los resultados | Directorio de centros | Enlace | Funciona | Cambia tabindex en h2#directorio-de-centros (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Cómo ordenamos los resultados | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Cómo ordenamos los resultados | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Blue Hole, Dahab · `#/punto?id=34`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Blue Hole, Dahab | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Blue Hole, Dahab | Puntos de buceo | Enlace | Funciona | Mismo enlace (#/puntos) que «Puntos de buceo» en «Encuentra tu próxima inmersión»: Abre #/puntos |
| Blue Hole, Dahab | África y Mar Rojo | Enlace | Funciona | Abre #/puntos?zone=%C3%81frica+y+Mar+Rojo |
| Blue Hole, Dahab | Abrir en el mapa | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Blue Hole, Dahab | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Encuentra tu próxima inmersión»: Abre #/login?next=%23%2Fcuenta |
| Blue Hole, Dahab | ¿Tienes un centro? Únete a WORLDIVES | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |
| Blue Hole, Dahab | Blue Hole Dahab Dahab · Egipto 6–60 m · Avanzado a 0 km | Enlace | Funciona | Abre #/punto?id=247 |
| Blue Hole, Dahab | Canyon Dahab Dahab · Egipto 8–30 m · Intermedio a 2,9 km | Enlace | Funciona | Abre #/punto?id=248 |
| Blue Hole, Dahab | Blue Hole, Dahab | Elemento div (role=button) | Funciona | Mueve o amplía el mapa |
| Blue Hole, Dahab | Mapa | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (8 elementos): «Leaflet» |
| Blue Hole, Dahab | Satélite | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Relieve orientativo (GEBCO). No sirve para navegar ni para la seguridad en el mar. Seguridad en el buceo» |
| Blue Hole, Dahab | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (10 elementos): «Leaflet» |
| Blue Hole, Dahab | Zoom in | Enlace | Funciona | Cambia la pantalla (5 elementos nuevos, 2 quitados) |
| Blue Hole, Dahab | Zoom out | Enlace | Funciona | Cambia la pantalla (5 elementos nuevos, 2 quitados) |
| Blue Hole, Dahab | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Blue Hole, Dahab | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Blue Hole, Dahab | Abrir en OpenStreetMap | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Blue Hole, Dahab | Inicia sesión para proponerla | Enlace | Funciona | Abre #/login?next=%23%2Fpunto%3Fid%3D34 |
| Blue Hole, Dahab | Denunciar contenido | Botón | Funciona | Abre la ventana «Denunciar contenido» |

#### Bahía Coralina Centro de Buceo · `#/centro?id=31`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | Centros | Enlace | Funciona | Mismo enlace (#/centros) que «Centros» en «Encuentra tu próxima inmersión»: Abre #/centros |
| Bahía Coralina Centro de Buceo | Reservar | Enlace | Funciona | Mismo enlace (#/reservar?center=31) que «Reservar» en «Centros de buceo»: Abre #/reservar?center=31 |
| Bahía Coralina Centro de Buceo | Llamar | Enlace externo | Funciona | Teléfono +34600000101 |
| Bahía Coralina Centro de Buceo | Escribir | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | Lun, 19 oct 10:00 6 plazas | Enlace | Funciona | Abre #/reservar?center=31&service=7&slot=22 · POST /api/stats/track → 200 · hay 11 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Enviar solicitud | Enlace | Funciona | Abre #/reservar?center=31&service=7 · POST /api/stats/track → 200 · hay 3 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Añadir a una reserva | Enlace | Funciona | Abre #/reservar?center=31&service=8 · POST /api/stats/track → 200 |
| Bahía Coralina Centro de Buceo | Tres días en la reserva del Cabo de San Antonio | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Foto 1 de Bahía Coralina Centro de Buceo | Botón | Funciona | Abre la ventana «Bahía Coralina Centro de Buceo» · hay 2 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Foto 2 de Bahía Coralina Centro de Buceo | Botón | Funciona | Abre la ventana «Bahía Coralina Centro de Buceo» |
| Bahía Coralina Centro de Buceo | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» · hay 7 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34600000101 |
| Bahía Coralina Centro de Buceo | hola@bahiacoralina.example.com | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | bahiacoralina.example.com | Enlace externo | Funciona | Enlace externo a bahiacoralina.example.com (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo | Ver en el mapa | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo | Reservar con Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/reservar?center=31) que «Reservar» en «Centros de buceo»: Abre #/reservar?center=31 |
| Bahía Coralina Centro de Buceo | Denunciar contenido | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Bahía Coralina Centro de Buceo | Cabo San Antonio | Enlace | Funciona | Abre #/punto?id=329 · hay 5 más iguales en la lista (no se prueban todos) |

#### Bahía Coralina Centro de Buceo · `#/reservar?center=31`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | ← Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | Bautizo de buceo | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «No admite reservas ahora mismo» |
| Bahía Coralina Centro de Buceo | Curso Open Water (3 días) | Botón | Funciona | Muestra contenido nuevo (14 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Curso de Nitrox | Botón | Funciona | Muestra contenido nuevo (13 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Doble inmersión en barco | Botón | Funciona | Muestra contenido nuevo (26 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Inmersión al atardecer | Botón | Funciona | Muestra contenido nuevo (17 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Inmersión simple en barco | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «No admite reservas ahora mismo» |
| Bahía Coralina Centro de Buceo | Una persona menos | Botón | Desactivado (correcto) | Desactivado: es el límite del calendario o de la lista («Una persona menos») |
| Bahía Coralina Centro de Buceo | Una persona más | Botón | Desactivado (correcto) | No responde al ratón (pointer-events: none) y se ve atenuado; la pantalla explica: «Elige primero la actividad.» |
| Bahía Coralina Centro de Buceo | Elige una actividad | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Política de cancelación. Moderada: cancelación gratuita hasta 48 horas antes de la actividad; después no hay reembolso.» |
| Bahía Coralina Centro de Buceo | condiciones de reserva | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Bahía Coralina Centro de Buceo | condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34600000101 |

#### Costa Blanca · `#/experiencia?id=7`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Costa Blanca | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Costa Blanca | Experiencias | Enlace | Funciona | Mismo enlace (#/experiencias) que «Experiencias» en «Encuentra tu próxima inmersión»: Abre #/experiencias |
| Costa Blanca | BAHÍA CORALINA CENTRO DE BUCEO | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Costa Blanca | Solicitar plaza | Botón | Funciona | Abre #/login?next=%23%2Fexperienciareserva%3Fid%3D2 |
| Costa Blanca | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Costa Blanca | Publicar un viaje | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### Condiciones de reserva, pago y cancelación · `#/legal/reservas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de reserva, pago y cancelación | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de reserva, pago y cancelación | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de reserva, pago y cancelación | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de reserva, pago y cancelación | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de reserva, pago y cancelación | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de reserva, pago y cancelación | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de reserva, pago y cancelación | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de reserva, pago y cancelación | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de reserva, pago y cancelación | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de reserva, pago y cancelación | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Leer | Botón | Funciona | Abre la ventana «Condiciones de reserva, pago y cancelación» |
| Condiciones de reserva, pago y cancelación | 1. Quién presta la actividad | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 7 más iguales en la lista (no se prueban todos) |
| Condiciones de reserva, pago y cancelación | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Normas de las reseñas · `#/legal/normas-resenas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Normas de las reseñas | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Normas de las reseñas | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Normas de las reseñas | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Normas de las reseñas | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Normas de las reseñas | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Normas de las reseñas | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Normas de las reseñas | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Normas de las reseñas | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Normas de las reseñas | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Normas de las reseñas | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Normas de las reseñas | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Normas de las reseñas | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Normas de las reseñas | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Normas de las reseñas | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Normas de las reseñas | Leer | Botón | Funciona | Abre la ventana «Normas de las reseñas» |
| Normas de las reseñas | Quién puede escribir una reseña | Enlace | Funciona | Cambia tabindex en h2#quien-puede-escribir-una-resena (sin atributo → -1) · hay 4 más iguales en la lista (no se prueban todos) |
| Normas de las reseñas | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Puntos WORLDIVES · `#/legal/puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Puntos WORLDIVES | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Puntos WORLDIVES | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Puntos WORLDIVES | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Puntos WORLDIVES | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Puntos WORLDIVES | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Puntos WORLDIVES | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Puntos WORLDIVES | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Puntos WORLDIVES | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Puntos WORLDIVES | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Puntos WORLDIVES | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Puntos WORLDIVES | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Puntos WORLDIVES | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Puntos WORLDIVES | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Puntos WORLDIVES | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Puntos WORLDIVES | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Puntos WORLDIVES | Condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Puntos WORLDIVES | Leer | Botón | Funciona | Abre la ventana «Puntos WORLDIVES» |
| Puntos WORLDIVES | 1. Cómo se consiguen | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Puntos WORLDIVES | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Puntos WORLDIVES | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Declaración de accesibilidad · `#/legal/accesibilidad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Declaración de accesibilidad | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Declaración de accesibilidad | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Declaración de accesibilidad | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Declaración de accesibilidad | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Declaración de accesibilidad | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Declaración de accesibilidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Declaración de accesibilidad | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Declaración de accesibilidad | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Declaración de accesibilidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Declaración de accesibilidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Declaración de accesibilidad | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Declaración de accesibilidad | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Declaración de accesibilidad | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Declaración de accesibilidad | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Declaración de accesibilidad | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Declaración de accesibilidad | Leer | Botón | Funciona | Abre la ventana «Declaración de accesibilidad» |
| Declaración de accesibilidad | Situación actual | Enlace | Funciona | Cambia tabindex en h2#situacion-actual (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Declaración de accesibilidad | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Declaración de accesibilidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Contacto · `#/legal/contacto`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Contacto | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Contacto | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Contacto | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Contacto | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Contacto | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Contacto | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Contacto | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Contacto | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Contacto | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Contacto | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Contacto | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Contacto | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Contacto | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Contacto | Escríbenos | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Asunto» (elige una opción de la lista) · El navegador no deja enviarlo: «Tu nombre» (campo obligatorio) |
| Contacto | Ve a «Denunciar contenido» | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Asunto | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Enviar mensaje» (sin efecto inmediato, correcto) |
| Contacto | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Contacto | Leer | Botón | Funciona | Abre la ventana «Contacto» |
| Contacto | Quién somos | Enlace | Funciona | Cambia tabindex en h2#quien-somos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Contacto | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Créditos y licencias de terceros · `#/legal/creditos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Créditos y licencias de terceros | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Créditos y licencias de terceros | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Créditos y licencias de terceros | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Créditos y licencias de terceros | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Créditos y licencias de terceros | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Créditos y licencias de terceros | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Créditos y licencias de terceros | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Créditos y licencias de terceros | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Créditos y licencias de terceros | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Créditos y licencias de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Créditos y licencias de terceros | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Créditos y licencias de terceros | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Créditos y licencias de terceros | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Créditos y licencias de terceros | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Créditos y licencias de terceros | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Créditos y licencias de terceros | OpenStreetMap contributors | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Protomaps | Enlace externo | Funciona | Enlace externo a protomaps.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Esri World Imagery | Enlace externo | Funciona | Enlace externo a www.arcgis.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | gebco.net | Enlace externo | Funciona | Enlace externo a www.gebco.net (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leaflet.markercluster | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | protomaps-leaflet | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | qrcode | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | stripe-python | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | fontTools | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leer | Botón | Funciona | Abre la ventana «Créditos y licencias de terceros» |
| Créditos y licencias de terceros | Mapas y datos geográficos | Enlace | Funciona | Cambia tabindex en h2#mapas-y-datos-geograficos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Créditos y licencias de terceros | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Créditos y licencias de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de uso para buceadores · `#/legal/terminos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de uso para buceadores | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de uso para buceadores | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de uso para buceadores | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de uso para buceadores | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de uso para buceadores | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Leer | Botón | Funciona | Abre la ventana «Condiciones de uso para buceadores» |
| Condiciones de uso para buceadores | 1. Qué es WORLDIVES DISCOVERY | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 9 más iguales en la lista (no se prueban todos) |
| Condiciones de uso para buceadores | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

### Buceador (buzo.prueba)

47 pantallas, 762 elementos probados en 11 min 45 s.

#### Cabecera, pie y elementos flotantes (comunes a todas las pantallas)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Encuentra tu próxima inmersión · flotante | Saltar al contenido | Enlace | Funciona | Desplaza la página · clic por JavaScript (no se puede pulsar con el ratón) |
| Encuentra tu próxima inmersión · cabecera | WORLDIVES DISCOVERY · inicio | Enlace | Funciona | Enlace a la pantalla en la que ya se está |
| Encuentra tu próxima inmersión · cabecera | Explorar | Enlace | Funciona | Abre #/explorar |
| Encuentra tu próxima inmersión · cabecera | Puntos de buceo | Enlace | Funciona | Abre #/puntos |
| Encuentra tu próxima inmersión · cabecera | Centros | Enlace | Funciona | Abre #/centros |
| Encuentra tu próxima inmersión · cabecera | Tipos de buceo | Enlace | Funciona | Abre #/tipos |
| Encuentra tu próxima inmersión · cabecera | Experiencias | Enlace | Funciona | Abre #/experiencias |
| Encuentra tu próxima inmersión · cabecera | Top 10 buceos | Enlace | Funciona | Abre #/top10 |
| Encuentra tu próxima inmersión · cabecera | Seleccionar idioma | Desplegable | Funciona | Recarga la página con /?lang=en |
| Encuentra tu próxima inmersión · cabecera | BN Bea ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) |
| Encuentra tu próxima inmersión · pie de página | Explorar el mapa | Enlace | Funciona | Mismo enlace (#/explorar) que «Explorar» en «Encuentra tu próxima inmersión»: Abre #/explorar |
| Encuentra tu próxima inmersión · pie de página | Top 10 cerca de ti | Enlace | Funciona | Mismo enlace (#/top10) que «Top 10 buceos» en «Encuentra tu próxima inmersión»: Abre #/top10 |
| Encuentra tu próxima inmersión · pie de página | Centros de buceo | Enlace | Funciona | Mismo enlace (#/centros) que «Centros» en «Encuentra tu próxima inmersión»: Abre #/centros |
| Encuentra tu próxima inmersión · pie de página | Viajes y vida a bordo | Enlace | Funciona | Mismo enlace (#/experiencias) que «Experiencias» en «Encuentra tu próxima inmersión»: Abre #/experiencias |
| Encuentra tu próxima inmersión · pie de página | Mi cuenta | Enlace | Funciona | Abre #/cuenta |
| Encuentra tu próxima inmersión · pie de página | Log Book | Enlace | Funciona | Abre #/logbook |
| Encuentra tu próxima inmersión · pie de página | Recompensas | Enlace | Funciona | Abre #/recompensas |
| Encuentra tu próxima inmersión · pie de página | Mis puntos | Enlace | Funciona | Abre #/mis-puntos |
| Encuentra tu próxima inmersión · pie de página | Dar de alta mi centro | Enlace | Funciona | Abre #/registro |
| Encuentra tu próxima inmersión · pie de página | Panel del centro | Enlace | Funciona | Abre #/admin |
| Encuentra tu próxima inmersión · pie de página | Condiciones para centros | Enlace | Funciona | Abre #/legal/condiciones-centros |
| Encuentra tu próxima inmersión · pie de página | Aviso legal | Enlace | Funciona | Abre #/legal/aviso-legal |
| Encuentra tu próxima inmersión · pie de página | Privacidad | Enlace | Funciona | Abre #/legal/privacidad |
| Encuentra tu próxima inmersión · pie de página | Cookies | Enlace | Funciona | Abre #/legal/cookies |
| Encuentra tu próxima inmersión · pie de página | Condiciones de uso | Enlace | Funciona | Abre #/legal/condiciones-buceadores |
| Encuentra tu próxima inmersión · pie de página | Condiciones de reserva | Enlace | Funciona | Abre #/legal/condiciones-reserva |
| Encuentra tu próxima inmersión · pie de página | Para centros | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Encuentra tu próxima inmersión · pie de página | Denunciar contenido | Enlace | Funciona | Abre #/legal/denuncias |
| Hola, Bea · flotante | Saltar al contenido | Enlace | Funciona | Desplaza la página · clic por JavaScript (no se puede pulsar con el ratón) |

#### Encuentra tu próxima inmersión · `#/`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Encuentra tu próxima inmersión | Buscar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «⌕ Escribe al menos dos letras El nombre de un punto, una ciudad, una isla o un centro de buceo.» |
| Encuentra tu próxima inmersión | Cerca de mí | Enlace | Funciona | Mismo enlace (#/top10) que «Top 10 buceos» en «Encuentra tu próxima inmersión»: Abre #/top10 |
| Encuentra tu próxima inmersión | Pecios | Enlace | Funciona | Abre #/tipos?t=pecios-y-naufragios |
| Encuentra tu próxima inmersión | Cuevas | Enlace | Funciona | Abre #/tipos?t=cuevas-y-cavernas |
| Encuentra tu próxima inmersión | Arrecifes | Enlace | Funciona | Abre #/tipos?t=arrecifes |
| Encuentra tu próxima inmersión | Centros con reserva online | Enlace | Funciona | Abre #/centros?only=online |
| Encuentra tu próxima inmersión | Abrir el explorador → | Enlace | Funciona | Mismo enlace (#/explorar) que «Explorar» en «Encuentra tu próxima inmersión»: Abre #/explorar |
| Encuentra tu próxima inmersión | 01 Europa 108 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (32 elementos): «4» |
| Encuentra tu próxima inmersión | 02 Asia 104 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (26 elementos): «15» |
| Encuentra tu próxima inmersión | 03 América 24 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (25 elementos): «3» |
| Encuentra tu próxima inmersión | 04 África y Mar Rojo 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (34 elementos): «2» |
| Encuentra tu próxima inmersión | 05 Oceanía 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (11 elementos): «2» |
| Encuentra tu próxima inmersión | 06 Caribe 17 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (27 elementos): «8» |
| Encuentra tu próxima inmersión | Mapa | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| Encuentra tu próxima inmersión | Satélite Disponible próximamente | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Encuentra tu próxima inmersión | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (18 elementos): «Leaflet» |
| Encuentra tu próxima inmersión | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (19 elementos): «2» · hay 15 más iguales en la lista (no se prueban todos) |
| Encuentra tu próxima inmersión | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (7 elementos): «Rainbow Reef» |
| Encuentra tu próxima inmersión | Mauritius – Cathedral | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (146 elementos): «×» · hay 1 más iguales en la lista (no se prueban todos) |
| Encuentra tu próxima inmersión | Tofo – Manta Reef | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» |
| Encuentra tu próxima inmersión | Zoom in | Enlace | Funciona | Muestra contenido nuevo (64 elementos): «2» |
| Encuentra tu próxima inmersión | Zoom out | Enlace | Funciona | Cambia su estado (class: leaflet-control-zoom-out → leaflet-control-zoom-out leaflet-disabled) · Cambia la pantalla (4 elementos nuevos, 0 quitados) |
| Encuentra tu próxima inmersión | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Encuentra tu próxima inmersión | OpenStreetMap contributors | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Encuentra tu próxima inmersión | Ver todos los tipos → | Enlace | Funciona | Mismo enlace (#/tipos) que «Tipos de buceo» en «Encuentra tu próxima inmersión»: Abre #/tipos |
| Encuentra tu próxima inmersión | Aguas profundas | Enlace | Funciona | Abre #/tipos?t=aguas-profundas |
| Encuentra tu próxima inmersión | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| Encuentra tu próxima inmersión | Paredes | Enlace | Funciona | Abre #/tipos?t=paredes |
| Encuentra tu próxima inmersión | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| Encuentra tu próxima inmersión | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| Encuentra tu próxima inmersión | Pináculos | Enlace | Funciona | Abre #/tipos?t=pinaculos |

#### El mapa del buceo · `#/explorar`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| El mapa del buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| El mapa del buceo | Todos | Botón | Funciona | Muestra contenido nuevo (36 elementos): «2» |
| El mapa del buceo | Arrecifes | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (58 elementos): «2» |
| El mapa del buceo | Paredes | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (45 elementos): «2» |
| El mapa del buceo | Pecios | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (32 elementos): «2» |
| El mapa del buceo | Cuevas | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (32 elementos): «3» |
| El mapa del buceo | Muck | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (30 elementos): «3» |
| El mapa del buceo | Pináculos | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (27 elementos): «7» |
| El mapa del buceo | Profundas | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (59 elementos): «2» |
| El mapa del buceo | 01 Europa 108 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (40 elementos): «2» |
| El mapa del buceo | 02 Asia 104 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (22 elementos): «2» |
| El mapa del buceo | 03 América 24 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (15 elementos): «2» |
| El mapa del buceo | 04 África y Mar Rojo 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (25 elementos): «2» |
| El mapa del buceo | 05 Oceanía 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (31 elementos): «2» |
| El mapa del buceo | 06 Caribe 17 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (32 elementos): «2» |
| El mapa del buceo | Mapa | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (26 elementos): «Leaflet» |
| El mapa del buceo | Satélite Disponible próximamente | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| El mapa del buceo | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (26 elementos): «Leaflet» |
| El mapa del buceo | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (31 elementos): «2» · clic forzado (otro elemento lo tapa) · hay 29 más iguales en la lista (no se prueban todos) |
| El mapa del buceo | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (14 elementos): «Rainbow Reef» |
| El mapa del buceo | Mauritius – Cathedral | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (126 elementos): «×» · hay 3 más iguales en la lista (no se prueban todos) |
| El mapa del buceo | Tofo – Manta Reef | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» |
| El mapa del buceo | Seguridad en el buceo | Enlace | Funciona | Abre #/legal/seguridad |
| El mapa del buceo | Zoom in | Enlace | Funciona | Muestra contenido nuevo (87 elementos): «2» |
| El mapa del buceo | Zoom out | Enlace | Funciona | Cambia la pantalla (10 elementos nuevos, 0 quitados) |
| El mapa del buceo | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |

#### Puntos de buceo · `#/puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Puntos de buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Puntos de buceo | Puntos de buceo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (68 elementos): «Todo el mundo» |
| Puntos de buceo | Zona Todo el mundo Europa (108) Asia (104) América (24) África y Mar Rojo (20) Oceanía (20) Caribe (17) | Desplegable | Funciona | Abre #/puntos?zone=Europa |
| Puntos de buceo | Para empezar | Botón | Funciona | Abre #/puntos?level=start |
| Puntos de buceo | Intermedio | Botón | Funciona | Abre #/puntos?level=mid |
| Puntos de buceo | Avanzado | Botón | Funciona | Abre #/puntos?level=adv |
| Puntos de buceo | Con centro que lo ofrece | Botón | Funciona | Abre #/puntos?only=centers |
| Puntos de buceo | Confirmación inmediata | Botón | Funciona | Abre #/puntos?only=instant |
| Puntos de buceo | Tipo de buceo Cualquier tipo Arrecifes Paredes Pecios y naufragios Cuevas y cavernas Cenotes Muck Canales Caño | Desplegable | Funciona | Abre #/puntos?type=arrecifes |
| Puntos de buceo | País Todos los países España (93) Filipinas (30) Indonesia (25) Malasia (15) Maldivas (13) Tailandia (13) Egip | Desplegable | Funciona | Abre #/puntos?country=Espa%C3%B1a |
| Puntos de buceo | Ordenar Recomendados Nombre A-Z Más profundos Menos profundos Mejor valorados | Desplegable | Funciona | Abre #/puntos?sort=name |
| Puntos de buceo | ¿Cómo ordenamos? | Enlace | Funciona | Abre #/legal/clasificacion |
| Puntos de buceo | #/punto?id=34 | Enlace | Funciona | Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Blue Hole, Dahab | Enlace | Funciona | Mismo enlace (#/punto?id=34) que «#/punto?id=34» en «Puntos de buceo»: Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Ver punto | Enlace | Funciona | Mismo enlace (#/punto?id=34) que «#/punto?id=34» en «Puntos de buceo»: Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Mostrar más puntos (281) | Botón | Funciona | Cambia su estado (disabled: sin atributo → vacío) · Muestra contenido nuevo (13 elementos): «Arrecifes Paredes Portitxol Norte Marina Alta · Xàbia · España Moderado Arrecife · Pared · Fondo arenoso Ubicación por v» |

#### Centros de buceo · `#/centros`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centros de buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Centros de buceo | Centros de buceo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (11 elementos): «Todos los países» |
| Centros de buceo | País Todos los países España (2) | Desplegable | Funciona | Abre #/centros?country=Espa%C3%B1a |
| Centros de buceo | Confirmación inmediata | Botón | Funciona | Abre #/centros?only=instant |
| Centros de buceo | Reserva online | Botón | Funciona | Abre #/centros?only=online |
| Centros de buceo | Plazas esta semana | Botón | Funciona | Abre #/centros?only=week |
| Centros de buceo | Cursos | Botón | Funciona | Abre #/centros?only=courses |
| Centros de buceo | Bautizos | Botón | Funciona | Abre #/centros?only=try |
| Centros de buceo | Viajes | Botón | Funciona | Abre #/centros?only=trips |
| Centros de buceo | Con reseñas | Botón | Funciona | Abre #/centros?only=reviews |
| Centros de buceo | Tipo de buceo Cualquier tipo de buceo Arrecifes Paredes Pecios y naufragios Cuevas y cavernas Cenotes Muck Can | Desplegable | Funciona | Abre #/centros?type=arrecifes |
| Centros de buceo | Ordenar Recomendados Mejor valorados Más reseñas Precio más bajo Nombre A-Z | Desplegable | Funciona | Abre #/centros?sort=rating |
| Centros de buceo | ¿Cómo ordenamos? | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Centros de buceo | Bajo petición Plazas esta semana | Enlace | Funciona | Abre #/centro?id=31 |
| Centros de buceo | Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Centros de buceo | Reservar | Enlace | Funciona | Abre #/reservar?center=31 |
| Centros de buceo | Bajo petición Plazas esta semana | Enlace | Funciona | Abre #/centro?id=32 |
| Centros de buceo | Escafandra Medes | Enlace | Funciona | Mismo enlace (#/centro?id=32) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=32 |
| Centros de buceo | Reservar | Enlace | Funciona | Abre #/reservar?center=32 |
| Centros de buceo | Dar de alta mi centro | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### ¿Qué inmersión te apetece? · `#/tipos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| ¿Qué inmersión te apetece? | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| ¿Qué inmersión te apetece? | Todos | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| ¿Qué inmersión te apetece? | Para empezar | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Con experiencia | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Avanzado y técnico | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| ¿Qué inmersión te apetece? | Paredes | Enlace | Funciona | Mismo enlace (#/tipos?t=paredes) que «Paredes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=paredes |
| ¿Qué inmersión te apetece? | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| ¿Qué inmersión te apetece? | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| ¿Qué inmersión te apetece? | Cenotes | Enlace | Funciona | Abre #/tipos?t=cenotes |
| ¿Qué inmersión te apetece? | Muck | Enlace | Funciona | Abre #/tipos?t=muck |
| ¿Qué inmersión te apetece? | Canales | Enlace | Funciona | Abre #/tipos?t=canales |
| ¿Qué inmersión te apetece? | Cañones | Enlace | Funciona | Abre #/tipos?t=canones |
| ¿Qué inmersión te apetece? | Pináculos | Enlace | Funciona | Mismo enlace (#/tipos?t=pinaculos) que «Pináculos» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pinaculos |
| ¿Qué inmersión te apetece? | Corrientes y deriva | Enlace | Funciona | Abre #/tipos?t=corrientes-y-deriva |
| ¿Qué inmersión te apetece? | Aguas profundas | Enlace | Funciona | Mismo enlace (#/tipos?t=aguas-profundas) que «Aguas profundas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=aguas-profundas |
| ¿Qué inmersión te apetece? | Lagos | Enlace | Funciona | Abre #/tipos?t=lagos |
| ¿Qué inmersión te apetece? | Pilares | Enlace | Funciona | Abre #/tipos?t=pilares |
| ¿Qué inmersión te apetece? | Nocturnas | Enlace | Funciona | Abre #/tipos?t=nocturnas |
| ¿Qué inmersión te apetece? | Playa y esnórquel | Enlace | Funciona | Abre #/tipos?t=playa-y-esnorquel |
| ¿Qué inmersión te apetece? | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| ¿Qué inmersión te apetece? | Muck | Enlace | Funciona | Mismo enlace (#/tipos?t=muck) que «Muck» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=muck |
| ¿Qué inmersión te apetece? | Lagos | Enlace | Funciona | Mismo enlace (#/tipos?t=lagos) que «Lagos» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=lagos |
| ¿Qué inmersión te apetece? | Pilares | Enlace | Funciona | Mismo enlace (#/tipos?t=pilares) que «Pilares» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=pilares |
| ¿Qué inmersión te apetece? | Paredes | Enlace | Funciona | Mismo enlace (#/tipos?t=paredes) que «Paredes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=paredes |
| ¿Qué inmersión te apetece? | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| ¿Qué inmersión te apetece? | Canales | Enlace | Funciona | Mismo enlace (#/tipos?t=canales) que «Canales» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=canales |
| ¿Qué inmersión te apetece? | Pináculos | Enlace | Funciona | Mismo enlace (#/tipos?t=pinaculos) que «Pináculos» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pinaculos |
| ¿Qué inmersión te apetece? | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| ¿Qué inmersión te apetece? | Cenotes | Enlace | Funciona | Mismo enlace (#/tipos?t=cenotes) que «Cenotes» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=cenotes |
| ¿Qué inmersión te apetece? | Cañones | Enlace | Funciona | Mismo enlace (#/tipos?t=canones) que «Cañones» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=canones |
| ¿Qué inmersión te apetece? | Corrientes y deriva | Enlace | Funciona | Mismo enlace (#/tipos?t=corrientes-y-deriva) que «Corrientes y deriva» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=corrientes-y-deriva |
| ¿Qué inmersión te apetece? | Aguas profundas | Enlace | Funciona | Mismo enlace (#/tipos?t=aguas-profundas) que «Aguas profundas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=aguas-profundas |

#### Viajes y vida a bordo · `#/experiencias`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Viajes y vida a bordo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Viajes y vida a bordo | Viajes y vida a bordo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (16 elementos): «Viaje 1 experiencia Costa Blanca España Experiencias de buceo organizadas por centros y profesionales. DESDE 290 € PRÓXI» |
| Viajes y vida a bordo | Todas | Botón | Funciona | Muestra contenido nuevo (8 elementos): «Viaje 1 experiencia Costa Blanca España Experiencias de buceo organizadas por centros y profesionales. DESDE 290 € PRÓXI» |
| Viajes y vida a bordo | Viaje | Botón | Funciona | Abre #/experiencias?kind=Viaje |
| Viajes y vida a bordo | Vida a bordo | Botón | Funciona | Abre #/experiencias?kind=Vida+a+bordo |
| Viajes y vida a bordo | Ordenar Con más salidas Precio más bajo Próxima salida Nombre A-Z | Desplegable | Funciona | Abre #/experiencias?sort=price |
| Viajes y vida a bordo | Viaje 1 experiencia | Enlace | Funciona | Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Costa Blanca | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Ver viajes | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Ver destino | Enlace | Funciona | Abre #/experiencia?id=5 · hay 3 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Empezar a publicar | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### ¿Te apetece bucear? · `#/top10`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| ¿Te apetece bucear? | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| ¿Te apetece bucear? | Radio 25 km 50 km 100 km 250 km 500 km | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Buscar» (sin efecto inmediato, correcto) |
| ¿Te apetece bucear? | Usar mi ubicación | Botón | Funciona | Muestra contenido nuevo (13 elementos): «1 ARRECIFES Cabo San Antonio Marina Alta · Xàbia · España 7–20 m Moderado ★ 4.4 (9) 1 centro 1,9 km Ver inmersión» |
| ¿Te apetece bucear? | Elegir en el mapa | Botón | Funciona | Abre la ventana «Elige tu ubicación» |
| ¿Te apetece bucear? | ¿Te apetece bucear? | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Buscar una localidad» (campo obligatorio) |
| ¿Te apetece bucear? | Marina Alta · Xàbia | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 ARRECIFES Piedras Rotas Marina Alta · Xàbia · España 7–20 m Fácil ★ 4.4 (9) 1 centro 0,8 km Ver inmersión» |
| ¿Te apetece bucear? | Marina Alta y Baixa · Calpe | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 19,3 km Ver inmersión» |
| ¿Te apetece bucear? | Canarias | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (9 elementos): «1 ARRECIFES Las Canteras, Gran Canaria Canarias · España Iniciación 48,3 km Ver inmersión» |
| ¿Te apetece bucear? | Palawan | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (4 elementos): «1 ARRECIFES El Nido – Cadlao Lagoon Palawan · Filipinas 5–20 m Principiante 72,9 km Ver inmersión» |
| ¿Te apetece bucear? | Comunitat Valenciana | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 25,7 km Ver inmersión» |
| ¿Te apetece bucear? | Andalucía | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (6 elementos): «1 ARRECIFES Costa del Sol, Málaga Andalucía · España Iniciación 52,4 km Ver inmersión» |
| ¿Te apetece bucear? | Marina Alta · Moraira | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 9,7 km Ver inmersión» |
| ¿Te apetece bucear? | Cebu | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (12 elementos): «1 ARRECIFES Moalboal – Sardine Run Cebu · Filipinas 5–25 m Principiante 28,1 km Ver inmersión» |
| ¿Te apetece bucear? | Cataluña | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (12 elementos): «1 ARRECIFES Medes – Tascons Islas Medes · España 6–25 m Intermedio ★ 4.8 (6) 1 centro 2,1 km Ver inmersión» |
| ¿Te apetece bucear? | Illes Balears | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (8 elementos): «1 PAREDES El Toro Mallorca · España 10–35 m Intermedio 12,9 km Ver inmersión» |

#### Planes de WORLDIVES · `#/planes`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Planes de WORLDIVES | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Planes de WORLDIVES | Dar de alta mi centro | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### Cómo funcionan los puntos · `#/como-funcionan-los-puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Cómo funcionan los puntos | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Cómo funcionan los puntos | Ver mis puntos | Enlace | Funciona | Mismo enlace (#/mis-puntos) que «Mis puntos» en «Encuentra tu próxima inmersión»: Abre #/mis-puntos |
| Cómo funcionan los puntos | Ver ventajas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Recompensas» en «Encuentra tu próxima inmersión»: Abre #/recompensas |

#### Aviso legal · `#/legal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Aviso legal | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Aviso legal | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Aviso legal | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Abre #/legal/reservas |
| Aviso legal | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Aviso legal | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Aviso legal | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Aviso legal | Normas de las reseñas | Enlace | Funciona | Abre #/legal/normas-resenas |
| Aviso legal | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Puntos WORLDIVES | Enlace | Funciona | Abre #/legal/puntos |
| Aviso legal | Declaración de accesibilidad | Enlace | Funciona | Abre #/legal/accesibilidad |
| Aviso legal | Contacto | Enlace | Funciona | Abre #/legal/contacto |
| Aviso legal | Créditos y licencias de terceros | Enlace | Funciona | Abre #/legal/creditos |
| Aviso legal | Condiciones de uso | Enlace | Funciona | Abre #/legal/terminos |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Leer | Botón | Funciona | Abre la ventana «Aviso legal» |
| Aviso legal | 1. Titular del sitio web | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 6 más iguales en la lista (no se prueban todos) |
| Aviso legal | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Crear cuenta · `#/registro`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Crear cuenta | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Crear cuenta | Buceador | Enlace | Funciona | Abre #/registro?tipo=recreational |
| Crear cuenta | Centro de buceo Publica tus salidas y cursos y gestiona tus reservas. | Enlace | Funciona | Abre #/registro?tipo=center |
| Crear cuenta | Profesional | Enlace | Funciona | Abre #/registro?tipo=freelance |
| Crear cuenta | Iniciar sesión | Enlace | Funciona | Abre #/cuenta |

#### Condiciones para centros y profesionales · `#/legal/condiciones-centros`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones para centros y profesionales | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones para centros y profesionales | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones para centros y profesionales | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones para centros y profesionales | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones para centros y profesionales | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones para centros y profesionales | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones para centros y profesionales | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones para centros y profesionales | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones para centros y profesionales | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones para centros y profesionales | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones para centros y profesionales | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones para centros y profesionales | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones para centros y profesionales | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones para centros y profesionales | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones para centros y profesionales | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones para centros y profesionales | Planes | Enlace | Funciona | Abre #/planes |
| Condiciones para centros y profesionales | Planes | Enlace | Funciona | Mismo enlace (#/planes) que «Planes» en «Condiciones para centros y profesionales»: Abre #/planes |
| Condiciones para centros y profesionales | normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones para centros y profesionales | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones para centros y profesionales | Leer | Botón | Funciona | Abre la ventana «Condiciones para centros y profesionales» |
| Condiciones para centros y profesionales | 1. Alta y verificación | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 18 más iguales en la lista (no se prueban todos) |
| Condiciones para centros y profesionales | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones para centros y profesionales | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Aviso legal · `#/legal/aviso-legal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Aviso legal | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Aviso legal | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Aviso legal | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Aviso legal | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Aviso legal | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Aviso legal | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Aviso legal | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Aviso legal | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Aviso legal | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Aviso legal | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Aviso legal | Condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/terminos) que «Condiciones de uso» en «Aviso legal»: Abre #/legal/terminos |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Leer | Botón | Funciona | Abre la ventana «Aviso legal» |
| Aviso legal | 1. Titular del sitio web | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 6 más iguales en la lista (no se prueban todos) |
| Aviso legal | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Política de privacidad · `#/legal/privacidad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Política de privacidad | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Política de privacidad | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Política de privacidad | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Política de privacidad | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Política de privacidad | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Política de privacidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de privacidad | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Política de privacidad | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Política de privacidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de privacidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Política de privacidad | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Política de privacidad | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Política de privacidad | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Política de privacidad | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Política de privacidad | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Política de privacidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de privacidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de privacidad | www.aepd.es | Enlace externo | Funciona | Enlace externo a www.aepd.es (no se abre: dirección https válida) |
| Política de privacidad | Leer | Botón | Funciona | Abre la ventana «Política de privacidad» |
| Política de privacidad | 1. Responsable | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 8 más iguales en la lista (no se prueban todos) |
| Política de privacidad | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Política de privacidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Política de cookies y servicios de terceros · `#/legal/cookies`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Política de cookies y servicios de terceros | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Política de cookies y servicios de terceros | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Política de cookies y servicios de terceros | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Política de cookies y servicios de terceros | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Política de cookies y servicios de terceros | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Política de cookies y servicios de terceros | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de cookies y servicios de terceros | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Política de cookies y servicios de terceros | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Política de cookies y servicios de terceros | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de cookies y servicios de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Política de cookies y servicios de terceros | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Política de cookies y servicios de terceros | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Política de cookies y servicios de terceros | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Política de cookies y servicios de terceros | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Política de cookies y servicios de terceros | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Política de cookies y servicios de terceros | Leer | Botón | Funciona | Abre la ventana «Política de cookies y servicios de terceros» |
| Política de cookies y servicios de terceros | Qué usamos | Enlace | Funciona | Cambia tabindex en h2#que-usamos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Política de cookies y servicios de terceros | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Política de cookies y servicios de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de uso para buceadores · `#/legal/condiciones-buceadores`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de uso para buceadores | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de uso para buceadores | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de uso para buceadores | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de uso para buceadores | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de uso para buceadores | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Leer | Botón | Funciona | Abre la ventana «Condiciones de uso para buceadores» |
| Condiciones de uso para buceadores | 1. Qué es WORLDIVES DISCOVERY | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 9 más iguales en la lista (no se prueban todos) |
| Condiciones de uso para buceadores | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de reserva, pago y cancelación · `#/legal/condiciones-reserva`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de reserva, pago y cancelación | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de reserva, pago y cancelación | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de reserva, pago y cancelación | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de reserva, pago y cancelación | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de reserva, pago y cancelación | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de reserva, pago y cancelación | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de reserva, pago y cancelación | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de reserva, pago y cancelación | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de reserva, pago y cancelación | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de reserva, pago y cancelación | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Leer | Botón | Funciona | Abre la ventana «Condiciones de reserva, pago y cancelación» |
| Condiciones de reserva, pago y cancelación | 1. Quién presta la actividad | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 7 más iguales en la lista (no se prueban todos) |
| Condiciones de reserva, pago y cancelación | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Denunciar contenido · `#/legal/denuncias`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Denunciar contenido | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Denunciar contenido | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Denunciar contenido | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Denunciar contenido | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Denunciar contenido | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Denunciar contenido | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Denunciar contenido | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Denunciar contenido | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Denunciar contenido | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Denunciar contenido | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Denunciar contenido | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Denunciar contenido | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Denunciar contenido | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Denunciar contenido | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Denunciar contenido | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Denunciar contenido | Formulario de denuncia | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Motivo» (elige una opción de la lista) · El navegador no deja enviarlo: «Explica por qué es ilegal o incumple las condiciones» (campo obligatorio) |
| Denunciar contenido | Motivo | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Enviar denuncia» (sin efecto inmediato, correcto) |
| Denunciar contenido | Leer | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Denunciar contenido | Qué necesitamos | Enlace | Funciona | Cambia tabindex en h2#que-necesitamos (sin atributo → -1) · hay 2 más iguales en la lista (no se prueban todos) |
| Denunciar contenido | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Denunciar contenido | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Seguridad en el buceo · `#/legal/seguridad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Seguridad en el buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Seguridad en el buceo | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Seguridad en el buceo | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Seguridad en el buceo | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Seguridad en el buceo | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Seguridad en el buceo | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Seguridad en el buceo | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Seguridad en el buceo | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Seguridad en el buceo | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Seguridad en el buceo | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Seguridad en el buceo | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Seguridad en el buceo | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Seguridad en el buceo | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Seguridad en el buceo | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Seguridad en el buceo | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Seguridad en el buceo | Leer | Botón | Funciona | Abre la ventana «Seguridad en el buceo» |
| Seguridad en el buceo | Antes de reservar | Enlace | Funciona | Cambia tabindex en h2#antes-de-reservar (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Seguridad en el buceo | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Seguridad en el buceo | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Cómo ordenamos los resultados · `#/legal/clasificacion`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Cómo ordenamos los resultados | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Cómo ordenamos los resultados | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Cómo ordenamos los resultados | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Cómo ordenamos los resultados | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Cómo ordenamos los resultados | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Cómo ordenamos los resultados | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Cómo ordenamos los resultados | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Cómo ordenamos los resultados | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Cómo ordenamos los resultados | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Cómo ordenamos los resultados | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Cómo ordenamos los resultados | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Cómo ordenamos los resultados | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Cómo ordenamos los resultados | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Cómo ordenamos los resultados | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Cómo ordenamos los resultados | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Cómo ordenamos los resultados | Leer | Botón | Funciona | Abre la ventana «Cómo ordenamos los resultados» |
| Cómo ordenamos los resultados | Directorio de centros | Enlace | Funciona | Cambia tabindex en h2#directorio-de-centros (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Cómo ordenamos los resultados | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Cómo ordenamos los resultados | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Blue Hole, Dahab · `#/punto?id=34`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Blue Hole, Dahab | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Blue Hole, Dahab | Puntos de buceo | Enlace | Funciona | Mismo enlace (#/puntos) que «Puntos de buceo» en «Encuentra tu próxima inmersión»: Abre #/puntos |
| Blue Hole, Dahab | África y Mar Rojo | Enlace | Funciona | Abre #/puntos?zone=%C3%81frica+y+Mar+Rojo |
| Blue Hole, Dahab | Abrir en el mapa | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Blue Hole, Dahab | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Encuentra tu próxima inmersión»: Abre #/cuenta |
| Blue Hole, Dahab | ¿Tienes un centro? Únete a WORLDIVES | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |
| Blue Hole, Dahab | Blue Hole Dahab Dahab · Egipto 6–60 m · Avanzado a 0 km | Enlace | Funciona | Abre #/punto?id=247 |
| Blue Hole, Dahab | Canyon Dahab Dahab · Egipto 8–30 m · Intermedio a 2,9 km | Enlace | Funciona | Abre #/punto?id=248 |
| Blue Hole, Dahab | Blue Hole, Dahab | Elemento div (role=button) | Funciona | Mueve o amplía el mapa |
| Blue Hole, Dahab | Mapa | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (8 elementos): «Leaflet» |
| Blue Hole, Dahab | Satélite | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Relieve orientativo (GEBCO). No sirve para navegar ni para la seguridad en el mar. Seguridad en el buceo» |
| Blue Hole, Dahab | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (10 elementos): «Leaflet» |
| Blue Hole, Dahab | Zoom in | Enlace | Funciona | Cambia la pantalla (5 elementos nuevos, 2 quitados) |
| Blue Hole, Dahab | Zoom out | Enlace | Funciona | Cambia la pantalla (5 elementos nuevos, 2 quitados) |
| Blue Hole, Dahab | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Blue Hole, Dahab | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Blue Hole, Dahab | Abrir en OpenStreetMap | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Blue Hole, Dahab | Proponer nueva posición | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Latitud Longitud Motivo» |
| Blue Hole, Dahab | Denunciar contenido | Botón | Funciona | Abre la ventana «Denunciar contenido» |

#### Bahía Coralina Centro de Buceo · `#/centro?id=31`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | Centros | Enlace | Funciona | Mismo enlace (#/centros) que «Centros» en «Encuentra tu próxima inmersión»: Abre #/centros |
| Bahía Coralina Centro de Buceo | Reservar | Enlace | Funciona | Mismo enlace (#/reservar?center=31) que «Reservar» en «Centros de buceo»: Abre #/reservar?center=31 |
| Bahía Coralina Centro de Buceo | Llamar | Enlace externo | Funciona | Teléfono +34600000101 |
| Bahía Coralina Centro de Buceo | Escribir | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | Lun, 19 oct 10:00 6 plazas | Enlace | Funciona | Abre #/reservar?center=31&service=7&slot=22 · POST /api/stats/track → 200 · hay 11 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Enviar solicitud | Enlace | Funciona | Abre #/reservar?center=31&service=7 · POST /api/stats/track → 200 · hay 3 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Añadir a una reserva | Enlace | Funciona | Abre #/reservar?center=31&service=8 · POST /api/stats/track → 200 |
| Bahía Coralina Centro de Buceo | Tres días en la reserva del Cabo de San Antonio | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Foto 1 de Bahía Coralina Centro de Buceo | Botón | Funciona | Abre la ventana «Bahía Coralina Centro de Buceo» · hay 2 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Foto 2 de Bahía Coralina Centro de Buceo | Botón | Funciona | Abre la ventana «Bahía Coralina Centro de Buceo» |
| Bahía Coralina Centro de Buceo | Reseñas | Formulario | Funciona | Enviado vacío · Aviso: «Tu reseña se ha guardado.» · Muestra contenido nuevo (2 elementos): «← Volver» · POST /api/centers/31/reviews → 200 |
| Bahía Coralina Centro de Buceo | 1 estrellas | Botón | Funciona | Cambia class en button.pick-star (pick-star selected → pick-star) · hay 3 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | 2 estrellas | Botón | Funciona | Cambia class en button.pick-star (pick-star selected → pick-star) |
| Bahía Coralina Centro de Buceo | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» · hay 7 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34600000101 |
| Bahía Coralina Centro de Buceo | hola@bahiacoralina.example.com | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | bahiacoralina.example.com | Enlace externo | Funciona | Enlace externo a bahiacoralina.example.com (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo | Ver en el mapa | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo | Reservar con Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/reservar?center=31) que «Reservar» en «Centros de buceo»: Abre #/reservar?center=31 |
| Bahía Coralina Centro de Buceo | Denunciar contenido | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Bahía Coralina Centro de Buceo | Cabo San Antonio | Enlace | Funciona | Abre #/punto?id=329 · hay 5 más iguales en la lista (no se prueban todos) |

#### Bahía Coralina Centro de Buceo · `#/reservar?center=31`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | ← Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | Bautizo de buceo | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «No admite reservas ahora mismo» |
| Bahía Coralina Centro de Buceo | Curso Open Water (3 días) | Botón | Funciona | Muestra contenido nuevo (14 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Curso de Nitrox | Botón | Funciona | Muestra contenido nuevo (13 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Doble inmersión en barco | Botón | Funciona | Muestra contenido nuevo (26 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Inmersión al atardecer | Botón | Funciona | Muestra contenido nuevo (17 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Inmersión simple en barco | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «No admite reservas ahora mismo» |
| Bahía Coralina Centro de Buceo | Una persona menos | Botón | Desactivado (correcto) | Desactivado: es el límite del calendario o de la lista («Una persona menos») |
| Bahía Coralina Centro de Buceo | Una persona más | Botón | Desactivado (correcto) | No responde al ratón (pointer-events: none) y se ve atenuado; la pantalla explica: «Elige primero la actividad.» |
| Bahía Coralina Centro de Buceo | Elige una actividad | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Política de cancelación. Moderada: cancelación gratuita hasta 48 horas antes de la actividad; después no hay reembolso.» |
| Bahía Coralina Centro de Buceo | condiciones de reserva | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Bahía Coralina Centro de Buceo | condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34600000101 |

#### Costa Blanca · `#/experiencia?id=7`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Costa Blanca | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Costa Blanca | Experiencias | Enlace | Funciona | Mismo enlace (#/experiencias) que «Experiencias» en «Encuentra tu próxima inmersión»: Abre #/experiencias |
| Costa Blanca | BAHÍA CORALINA CENTRO DE BUCEO | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Costa Blanca | Solicitar plaza | Botón | Funciona | Abre #/experienciareserva?id=2 |
| Costa Blanca | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Costa Blanca | Publicar un viaje | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### Condiciones de reserva, pago y cancelación · `#/legal/reservas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de reserva, pago y cancelación | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de reserva, pago y cancelación | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de reserva, pago y cancelación | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de reserva, pago y cancelación | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de reserva, pago y cancelación | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de reserva, pago y cancelación | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de reserva, pago y cancelación | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de reserva, pago y cancelación | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de reserva, pago y cancelación | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de reserva, pago y cancelación | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Leer | Botón | Funciona | Abre la ventana «Condiciones de reserva, pago y cancelación» |
| Condiciones de reserva, pago y cancelación | 1. Quién presta la actividad | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 7 más iguales en la lista (no se prueban todos) |
| Condiciones de reserva, pago y cancelación | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Normas de las reseñas · `#/legal/normas-resenas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Normas de las reseñas | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Normas de las reseñas | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Normas de las reseñas | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Normas de las reseñas | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Normas de las reseñas | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Normas de las reseñas | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Normas de las reseñas | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Normas de las reseñas | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Normas de las reseñas | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Normas de las reseñas | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Normas de las reseñas | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Normas de las reseñas | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Normas de las reseñas | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Normas de las reseñas | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Normas de las reseñas | Leer | Botón | Funciona | Abre la ventana «Normas de las reseñas» |
| Normas de las reseñas | Quién puede escribir una reseña | Enlace | Funciona | Cambia tabindex en h2#quien-puede-escribir-una-resena (sin atributo → -1) · hay 4 más iguales en la lista (no se prueban todos) |
| Normas de las reseñas | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Puntos WORLDIVES · `#/legal/puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Puntos WORLDIVES | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Puntos WORLDIVES | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Puntos WORLDIVES | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Puntos WORLDIVES | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Puntos WORLDIVES | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Puntos WORLDIVES | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Puntos WORLDIVES | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Puntos WORLDIVES | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Puntos WORLDIVES | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Puntos WORLDIVES | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Puntos WORLDIVES | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Puntos WORLDIVES | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Puntos WORLDIVES | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Puntos WORLDIVES | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Puntos WORLDIVES | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Puntos WORLDIVES | Condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Puntos WORLDIVES | Leer | Botón | Funciona | Abre la ventana «Puntos WORLDIVES» |
| Puntos WORLDIVES | 1. Cómo se consiguen | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Puntos WORLDIVES | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Puntos WORLDIVES | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Declaración de accesibilidad · `#/legal/accesibilidad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Declaración de accesibilidad | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Declaración de accesibilidad | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Declaración de accesibilidad | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Declaración de accesibilidad | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Declaración de accesibilidad | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Declaración de accesibilidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Declaración de accesibilidad | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Declaración de accesibilidad | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Declaración de accesibilidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Declaración de accesibilidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Declaración de accesibilidad | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Declaración de accesibilidad | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Declaración de accesibilidad | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Declaración de accesibilidad | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Declaración de accesibilidad | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Declaración de accesibilidad | Leer | Botón | Funciona | Abre la ventana «Declaración de accesibilidad» |
| Declaración de accesibilidad | Situación actual | Enlace | Funciona | Cambia tabindex en h2#situacion-actual (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Declaración de accesibilidad | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Declaración de accesibilidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Contacto · `#/legal/contacto`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Contacto | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Contacto | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Contacto | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Contacto | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Contacto | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Contacto | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Contacto | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Contacto | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Contacto | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Contacto | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Contacto | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Contacto | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Contacto | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Contacto | Escríbenos | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Asunto» (elige una opción de la lista) · El navegador no deja enviarlo: «Tu nombre» (campo obligatorio) |
| Contacto | Ve a «Denunciar contenido» | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Asunto | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Enviar mensaje» (sin efecto inmediato, correcto) |
| Contacto | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Contacto | Leer | Botón | Funciona | Abre la ventana «Contacto» |
| Contacto | Quién somos | Enlace | Funciona | Cambia tabindex en h2#quien-somos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Contacto | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Créditos y licencias de terceros · `#/legal/creditos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Créditos y licencias de terceros | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Créditos y licencias de terceros | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Créditos y licencias de terceros | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Créditos y licencias de terceros | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Créditos y licencias de terceros | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Créditos y licencias de terceros | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Créditos y licencias de terceros | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Créditos y licencias de terceros | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Créditos y licencias de terceros | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Créditos y licencias de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Créditos y licencias de terceros | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Créditos y licencias de terceros | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Créditos y licencias de terceros | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Créditos y licencias de terceros | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Créditos y licencias de terceros | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Créditos y licencias de terceros | OpenStreetMap contributors | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Protomaps | Enlace externo | Funciona | Enlace externo a protomaps.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Esri World Imagery | Enlace externo | Funciona | Enlace externo a www.arcgis.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | gebco.net | Enlace externo | Funciona | Enlace externo a www.gebco.net (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leaflet.markercluster | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | protomaps-leaflet | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | qrcode | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | stripe-python | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | fontTools | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leer | Botón | Funciona | Abre la ventana «Créditos y licencias de terceros» |
| Créditos y licencias de terceros | Mapas y datos geográficos | Enlace | Funciona | Cambia tabindex en h2#mapas-y-datos-geograficos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Créditos y licencias de terceros | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Créditos y licencias de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de uso para buceadores · `#/legal/terminos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de uso para buceadores | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de uso para buceadores | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de uso para buceadores | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de uso para buceadores | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de uso para buceadores | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Leer | Botón | Funciona | Abre la ventana «Condiciones de uso para buceadores» |
| Condiciones de uso para buceadores | 1. Qué es WORLDIVES DISCOVERY | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 9 más iguales en la lista (no se prueban todos) |
| Condiciones de uso para buceadores | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Hola, Bea · `#/area`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Hola, Bea | Leyenda 8500 puntos | Enlace | Funciona | Abre #/recompensas |
| Hola, Bea | Mi área | Enlace | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| Hola, Bea | Log Book | Enlace | Funciona | Abre #/logbook |
| Hola, Bea | Recompensas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Leyenda 8500 puntos» en «Hola, Bea»: Abre #/recompensas |
| Hola, Bea | Mis puntos | Enlace | Funciona | Abre #/mis-puntos |
| Hola, Bea | Mi cuenta | Enlace | Funciona | Abre #/cuenta |
| Hola, Bea | Reservar una inmersión | Enlace | Funciona | Abre #/centros |
| Hola, Bea | 6 próximas reservas | Botón | Funciona | Desplaza la página |
| Hola, Bea | 3 avisos sin leer | Botón | Funciona | Desplaza la página |
| Hola, Bea | 0 documentos | Enlace | Funciona | Abre #/cuenta?docs=1 |
| Hola, Bea | Ver reserva y QR | Enlace | Funciona | Abre #/reserva?id=1231 |
| Hola, Bea | PDF sin conexión | Enlace | Funciona | Descarga /api/bookings/1231/receipt.pdf (200, application/pdf) |
| Hola, Bea | Cómo llegar | Enlace externo | Funciona | Enlace externo a www.google.com (no se abre: dirección https válida) |
| Hola, Bea | Próximas 6 | Botón | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) · Cambia el texto: «Ver las 6 reservas» |
| Hola, Bea | Historial 120 | Botón | Funciona | Cambia su estado (class: sin atributo → is-on) · Cambia la pantalla (0 elementos nuevos, 1 quitados) |
| Hola, Bea | 17 | Enlace | Funciona | Mismo enlace (#/reserva?id=1231) que «Ver reserva y QR» en «Hola, Bea»: Abre #/reserva?id=1231 |
| Hola, Bea | Explorar | Enlace | Funciona | Abre #/experiencias |
| Hola, Bea | Completar mi ficha | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Hola, Bea»: Abre #/cuenta |
| Hola, Bea | Marcar como leído | Botón | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) · POST /api/messages/read → 200 · hay 1 más iguales en la lista (no se prueban todos) |
| Hola, Bea | Marcar como leído | Botón | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) · POST /api/messages/read → 200 |
| Hola, Bea | Gestionar | Enlace | Funciona | Mismo enlace (#/cuenta?docs=1) que «0 documentos» en «Hola, Bea»: Abre #/cuenta?docs=1 |

#### Hola, Bea › Historial · `#/area` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Hola, Bea › Historial | 1 avisos sin leer | Botón | Funciona | Desplaza la página |
| Hola, Bea › Historial | 9 | Enlace | Funciona | Abre #/reserva?id=1236 · hay 5 más iguales en la lista (no se prueban todos) |
| Hola, Bea › Historial | Ver las 120 reservas | Botón | Funciona | Cambia su estado (hidden: sin atributo → vacío) · Cambia la pantalla (0 elementos nuevos, 1 quitados) |

#### Tu ficha de buceador · `#/cuenta`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Tu ficha de buceador | Leyenda 8500 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Leyenda 8500 puntos» en «Hola, Bea»: Abre #/recompensas |
| Tu ficha de buceador | Datos personales | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Nombre y apellidos» (campo obligatorio) |
| Tu ficha de buceador | Prefijo del país | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Idioma preferido | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Nivel de certificación | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | ¿Sueles alquilar equipo? | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Tipo de traje | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Documentación | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Título» (campo obligatorio) · El navegador no deja enviarlo: «Archivo (PDF o imagen, máximo 10 MB)» (falta el archivo) |
| Tu ficha de buceador | Tipo | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Bahía Coralina Centro de Buceo Xàbia, España Última visita 10/10/2026 | Enlace | Funciona | Abre #/centro?id=31 |
| Tu ficha de buceador | Escafandra Medes L'Estartit, España Última visita 10/10/2026 | Enlace | Funciona | Abre #/centro?id=32 |
| Tu ficha de buceador | Seguridad | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Contraseña actual» (campo obligatorio) · El navegador no deja enviarlo: «Nueva contraseña» (campo obligatorio) |
| Tu ficha de buceador | Activar | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Tu contraseña» (campo obligatorio) |
| Tu ficha de buceador | Descargar mis datos (ZIP) | Enlace | Funciona | Descarga /api/account/export?format=zip (200, application/zip) |
| Tu ficha de buceador | Privacidad | Enlace | Funciona | Abre #/legal/privacidad |
| Tu ficha de buceador | Condiciones de uso | Enlace | Funciona | Abre #/legal/condiciones-buceadores |
| Tu ficha de buceador | Condiciones de reserva | Enlace | Funciona | Abre #/legal/condiciones-reserva |
| Tu ficha de buceador | Cookies | Enlace | Funciona | Abre #/legal/cookies |
| Tu ficha de buceador | Eliminar mi cuenta | Botón | Funciona | [probado al final del papel] Abre la ventana «Eliminar mi cuenta» |
| Tu ficha de buceador | Cerrar sesión | Botón | Funciona | [probado al final del papel] Abre #/ · POST /api/auth/logout → 200 · cierra la sesión o cambia la cuenta: se vuelve a iniciar sesión |

#### Log Book · `#/logbook`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Log Book | Leyenda 8500 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Leyenda 8500 puntos» en «Hola, Bea»: Abre #/recompensas |
| Log Book | Exportar CSV | Botón | Funciona | Descarga «logbook-worldives.csv» |
| Log Book | Nueva inmersión | Botón | Funciona | Abre la ventana «Nueva inmersión» |
| Log Book | Editar | Botón | Funciona | Abre la ventana «Editar inmersión» · hay 23 más iguales en la lista (no se prueban todos) |
| Log Book | Editar | Botón | Funciona | Abre la ventana «Editar inmersión» |
| Log Book | Borrar inmersión | Botón | Funciona | Pide confirmación «¿Borrar la inmersión en Cabo San Antonio?» (cancelado) |
| Log Book | Borrar inmersión | Botón | Funciona | Pide confirmación «¿Borrar la inmersión en Portitxol Norte?» (cancelado) |
| Log Book | Ver las 120 inmersiones | Botón | Funciona | Cambia su estado (hidden: sin atributo → vacío) |

#### Recompensas · `#/recompensas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Recompensas | Leyenda 8500 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Leyenda 8500 puntos» en «Hola, Bea»: Abre #/recompensas |
| Recompensas | Ver promoción Nocturna a mitad de precio | Enlace | Funciona | Abre #/promo/R2NVR7SFW6 |
| Recompensas | Ver promoción Bono 10 inmersiones | Enlace | Funciona | Abre #/promo/5DVQ44NMUP |
| Recompensas | Ver promoción 10 % en tu próxima inmersión | Enlace | Funciona | Abre #/promo/MNTUER6N2R |
| Recompensas | Cómo funcionan | Enlace | Funciona | Abre #/como-funcionan-los-puntos |
| Recompensas | Canjear | Botón | Funciona | Pide confirmación «¿Canjear tus puntos por esta ventaja?» (cancelado) · hay 2 más iguales en la lista (no se prueban todos) |
| Recompensas | Canjear | Botón | Funciona | Pide confirmación «¿Canjear tus puntos por esta ventaja?» (cancelado) |

#### Mis puntos · `#/mis-puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Mis puntos | Leyenda 8500 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Leyenda 8500 puntos» en «Hola, Bea»: Abre #/recompensas |
| Mis puntos | Ver ventajas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Leyenda 8500 puntos» en «Hola, Bea»: Abre #/recompensas |
| Mis puntos | Más información sobre los puntos | Enlace | Funciona | Mismo enlace (#/como-funcionan-los-puntos) que «Cómo funcionan» en «Recompensas»: Abre #/como-funcionan-los-puntos |

#### WORLDIVES DISCOVERY · `#/admin`

Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).

#### Bahía Coralina Centro de Buceo · `#/reserva?id=1231`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | Mi área | Enlace | Funciona | Abre #/area |
| Bahía Coralina Centro de Buceo | Descargar esta reserva en PDF | Enlace | Funciona | Descarga /api/bookings/1231/receipt.pdf (200, application/pdf) |
| Bahía Coralina Centro de Buceo | Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bahía Coralina Centro de Buceo Xàbia, Es» en «Tu ficha de buceador»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34 600 000 101 |
| Bahía Coralina Centro de Buceo | hola@bahiacoralina.example.com | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | Cambiar fecha | Botón | Funciona | Abre la ventana «Cambiar fecha» |
| Bahía Coralina Centro de Buceo | Escribir reseña | Enlace | Funciona | Abre #/centro?id=31&resena=1 |
| Bahía Coralina Centro de Buceo | Condiciones de reserva | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Tu ficha de buceador»: Abre #/legal/condiciones-reserva |
| Bahía Coralina Centro de Buceo | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» · POST /api/bookings/1231/cancel → 200 |

#### Escafandra Medes · `#/reserva?id=1251`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Escafandra Medes | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Escafandra Medes | Mi área | Enlace | Funciona | Mismo enlace (#/area) que «Mi área» en «Bahía Coralina Centro de Buceo»: Abre #/area |
| Escafandra Medes | Descargar esta reserva en PDF | Enlace | Funciona | Descarga /api/bookings/1251/receipt.pdf (200, application/pdf) |
| Escafandra Medes | Escafandra Medes | Enlace | Funciona | Mismo enlace (#/centro?id=32) que «Escafandra Medes L'Estartit, España Últi» en «Tu ficha de buceador»: Abre #/centro?id=32 |
| Escafandra Medes | +34 972 000 202 | Enlace externo | Funciona | Teléfono +34 972 000 202 |
| Escafandra Medes | hola@escafandramedes.example.com | Enlace externo | Funciona | Correo hola@escafandramedes.example.com |
| Escafandra Medes | Cambiar fecha | Botón | Funciona | Abre la ventana «Cambiar fecha» |
| Escafandra Medes | Condiciones de reserva | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Tu ficha de buceador»: Abre #/legal/condiciones-reserva |
| Escafandra Medes | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» · POST /api/bookings/1251/cancel → 200 |

#### Bahía Coralina Centro de Buceo · `#/reserva?id=1235`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | Mi área | Enlace | Funciona | Mismo enlace (#/area) que «Mi área» en «Bahía Coralina Centro de Buceo»: Abre #/area |
| Bahía Coralina Centro de Buceo | Descargar esta reserva en PDF | Enlace | Funciona | Descarga /api/bookings/1235/receipt.pdf (200, application/pdf) |
| Bahía Coralina Centro de Buceo | Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bahía Coralina Centro de Buceo Xàbia, Es» en «Tu ficha de buceador»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34 600 000 101 |
| Bahía Coralina Centro de Buceo | hola@bahiacoralina.example.com | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | Justificante PDF | Enlace | Funciona | Descarga /api/bookings/1235/receipt.pdf (200, application/pdf) |
| Bahía Coralina Centro de Buceo | Cambiar fecha | Botón | Funciona | Abre la ventana «Cambiar fecha» |
| Bahía Coralina Centro de Buceo | Escribir reseña | Enlace | Funciona | Mismo enlace (#/centro?id=31&resena=1) que «Escribir reseña» en «Bahía Coralina Centro de Buceo»: Abre #/centro?id=31&resena=1 |
| Bahía Coralina Centro de Buceo | Condiciones de reserva | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Tu ficha de buceador»: Abre #/legal/condiciones-reserva |
| Bahía Coralina Centro de Buceo | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» · POST /api/bookings/1235/cancel → 200 |

#### Bahía Coralina Centro de Buceo · `#/reserva?id=1230`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | Mi área | Enlace | Funciona | Mismo enlace (#/area) que «Mi área» en «Bahía Coralina Centro de Buceo»: Abre #/area |
| Bahía Coralina Centro de Buceo | Descargar esta reserva en PDF | Enlace | Funciona | Descarga /api/bookings/1230/receipt.pdf (200, application/pdf) |
| Bahía Coralina Centro de Buceo | Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bahía Coralina Centro de Buceo Xàbia, Es» en «Tu ficha de buceador»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34 600 000 101 |
| Bahía Coralina Centro de Buceo | hola@bahiacoralina.example.com | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | Cambiar fecha | Botón | Funciona | Abre la ventana «Cambiar fecha» |
| Bahía Coralina Centro de Buceo | Condiciones de reserva | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Tu ficha de buceador»: Abre #/legal/condiciones-reserva |
| Bahía Coralina Centro de Buceo | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» · POST /api/bookings/1230/cancel → 200 |

#### Bahía Coralina Centro de Buceo · `#/reserva?id=1232`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | Mi área | Enlace | Funciona | Mismo enlace (#/area) que «Mi área» en «Bahía Coralina Centro de Buceo»: Abre #/area |
| Bahía Coralina Centro de Buceo | Descargar esta reserva en PDF | Enlace | Funciona | Descarga /api/bookings/1232/receipt.pdf (200, application/pdf) |
| Bahía Coralina Centro de Buceo | Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bahía Coralina Centro de Buceo Xàbia, Es» en «Tu ficha de buceador»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34 600 000 101 |
| Bahía Coralina Centro de Buceo | hola@bahiacoralina.example.com | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | Cambiar fecha | Botón | Funciona | Abre la ventana «Cambiar fecha» |
| Bahía Coralina Centro de Buceo | Condiciones de reserva | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Tu ficha de buceador»: Abre #/legal/condiciones-reserva |
| Bahía Coralina Centro de Buceo | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» · POST /api/bookings/1232/cancel → 200 |

#### Diego Arenas · `#/reserva?id=1285`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Diego Arenas | Mi área | Enlace | Funciona | Mismo enlace (#/area) que «Mi área» en «Bahía Coralina Centro de Buceo»: Abre #/area |
| Diego Arenas | Descargar esta reserva en PDF | Enlace | Funciona | Descarga /api/bookings/1285/receipt.pdf (200, application/pdf) |
| Diego Arenas | Diego Arenas | Enlace | Funciona | Abre #/centro?id=null |
| Diego Arenas | diego.arenas@example.com | Enlace externo | Funciona | Correo diego.arenas@example.com |
| Diego Arenas | Condiciones de reserva | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Tu ficha de buceador»: Abre #/legal/condiciones-reserva |
| Diego Arenas | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» · POST /api/bookings/1285/cancel → 200 |

#### Bahía Coralina Centro de Buceo · `#/reserva?id=1236`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | Mi área | Enlace | Funciona | Mismo enlace (#/area) que «Mi área» en «Bahía Coralina Centro de Buceo»: Abre #/area |
| Bahía Coralina Centro de Buceo | Descargar esta reserva en PDF | Enlace | Funciona | Descarga /api/bookings/1236/receipt.pdf (200, application/pdf) |
| Bahía Coralina Centro de Buceo | Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bahía Coralina Centro de Buceo Xàbia, Es» en «Tu ficha de buceador»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34 600 000 101 |
| Bahía Coralina Centro de Buceo | hola@bahiacoralina.example.com | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |

#### Bahía Coralina Centro de Buceo · `#/reserva?id=1234`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | Mi área | Enlace | Funciona | Mismo enlace (#/area) que «Mi área» en «Bahía Coralina Centro de Buceo»: Abre #/area |
| Bahía Coralina Centro de Buceo | Descargar esta reserva en PDF | Enlace | Funciona | Descarga /api/bookings/1234/receipt.pdf (200, application/pdf) |
| Bahía Coralina Centro de Buceo | Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bahía Coralina Centro de Buceo Xàbia, Es» en «Tu ficha de buceador»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34 600 000 101 |
| Bahía Coralina Centro de Buceo | hola@bahiacoralina.example.com | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |

#### Bahía Coralina Centro de Buceo · `#/reserva?id=1233`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | Mi área | Enlace | Funciona | Mismo enlace (#/area) que «Mi área» en «Bahía Coralina Centro de Buceo»: Abre #/area |
| Bahía Coralina Centro de Buceo | Descargar esta reserva en PDF | Enlace | Funciona | Descarga /api/bookings/1233/receipt.pdf (200, application/pdf) |
| Bahía Coralina Centro de Buceo | Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bahía Coralina Centro de Buceo Xàbia, Es» en «Tu ficha de buceador»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34 600 000 101 |
| Bahía Coralina Centro de Buceo | hola@bahiacoralina.example.com | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |

### Centro propietario (centro.prueba)

75 pantallas, 1006 elementos probados en 20 min 1 s.

#### Cabecera, pie y elementos flotantes (comunes a todas las pantallas)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Encuentra tu próxima inmersión · flotante | Saltar al contenido | Enlace | Funciona | Desplaza la página · clic por JavaScript (no se puede pulsar con el ratón) |
| Encuentra tu próxima inmersión · cabecera | WORLDIVES DISCOVERY · inicio | Enlace | Funciona | Enlace a la pantalla en la que ya se está |
| Encuentra tu próxima inmersión · cabecera | Explorar | Enlace | Funciona | Abre #/explorar |
| Encuentra tu próxima inmersión · cabecera | Puntos de buceo | Enlace | Funciona | Abre #/puntos |
| Encuentra tu próxima inmersión · cabecera | Centros | Enlace | Funciona | Abre #/centros |
| Encuentra tu próxima inmersión · cabecera | Tipos de buceo | Enlace | Funciona | Abre #/tipos |
| Encuentra tu próxima inmersión · cabecera | Experiencias | Enlace | Funciona | Abre #/experiencias |
| Encuentra tu próxima inmersión · cabecera | Top 10 buceos | Enlace | Funciona | Abre #/top10 |
| Encuentra tu próxima inmersión · cabecera | Seleccionar idioma | Desplegable | Funciona | Recarga la página con /?lang=en |
| Encuentra tu próxima inmersión · cabecera | ML Marta ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) |
| Encuentra tu próxima inmersión · pie de página | Explorar el mapa | Enlace | Funciona | Mismo enlace (#/explorar) que «Explorar» en «Encuentra tu próxima inmersión»: Abre #/explorar |
| Encuentra tu próxima inmersión · pie de página | Top 10 cerca de ti | Enlace | Funciona | Mismo enlace (#/top10) que «Top 10 buceos» en «Encuentra tu próxima inmersión»: Abre #/top10 |
| Encuentra tu próxima inmersión · pie de página | Centros de buceo | Enlace | Funciona | Mismo enlace (#/centros) que «Centros» en «Encuentra tu próxima inmersión»: Abre #/centros |
| Encuentra tu próxima inmersión · pie de página | Viajes y vida a bordo | Enlace | Funciona | Mismo enlace (#/experiencias) que «Experiencias» en «Encuentra tu próxima inmersión»: Abre #/experiencias |
| Encuentra tu próxima inmersión · pie de página | Mi cuenta | Enlace | Funciona | Abre #/cuenta |
| Encuentra tu próxima inmersión · pie de página | Log Book | Enlace | Funciona | Abre #/logbook |
| Encuentra tu próxima inmersión · pie de página | Recompensas | Enlace | Funciona | Abre #/recompensas |
| Encuentra tu próxima inmersión · pie de página | Mis puntos | Enlace | Funciona | Abre #/mis-puntos |
| Encuentra tu próxima inmersión · pie de página | Dar de alta mi centro | Enlace | Funciona | Abre #/registro |
| Encuentra tu próxima inmersión · pie de página | Panel del centro | Enlace | Funciona | Abre #/admin |
| Encuentra tu próxima inmersión · pie de página | Condiciones para centros | Enlace | Funciona | Abre #/legal/condiciones-centros |
| Encuentra tu próxima inmersión · pie de página | Aviso legal | Enlace | Funciona | Abre #/legal/aviso-legal |
| Encuentra tu próxima inmersión · pie de página | Privacidad | Enlace | Funciona | Abre #/legal/privacidad |
| Encuentra tu próxima inmersión · pie de página | Cookies | Enlace | Funciona | Abre #/legal/cookies |
| Encuentra tu próxima inmersión · pie de página | Condiciones de uso | Enlace | Funciona | Abre #/legal/condiciones-buceadores |
| Encuentra tu próxima inmersión · pie de página | Condiciones de reserva | Enlace | Funciona | Abre #/legal/condiciones-reserva |
| Encuentra tu próxima inmersión · pie de página | Para centros | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Encuentra tu próxima inmersión · pie de página | Denunciar contenido | Enlace | Funciona | Abre #/legal/denuncias |
| Bahía Coralina Centro de Buceo · ⌂ Resumen · flotante | Saltar al contenido | Enlace | Funciona | Desplaza la página · clic por JavaScript (no se puede pulsar con el ratón) |

#### Encuentra tu próxima inmersión · `#/`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Encuentra tu próxima inmersión | Buscar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «⌕ Escribe al menos dos letras El nombre de un punto, una ciudad, una isla o un centro de buceo.» |
| Encuentra tu próxima inmersión | Cerca de mí | Enlace | Funciona | Mismo enlace (#/top10) que «Top 10 buceos» en «Encuentra tu próxima inmersión»: Abre #/top10 |
| Encuentra tu próxima inmersión | Pecios | Enlace | Funciona | Abre #/tipos?t=pecios-y-naufragios |
| Encuentra tu próxima inmersión | Cuevas | Enlace | Funciona | Abre #/tipos?t=cuevas-y-cavernas |
| Encuentra tu próxima inmersión | Arrecifes | Enlace | Funciona | Abre #/tipos?t=arrecifes |
| Encuentra tu próxima inmersión | Centros con reserva online | Enlace | Funciona | Abre #/centros?only=online |
| Encuentra tu próxima inmersión | Abrir el explorador → | Enlace | Funciona | Mismo enlace (#/explorar) que «Explorar» en «Encuentra tu próxima inmersión»: Abre #/explorar |
| Encuentra tu próxima inmersión | 01 Europa 108 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (32 elementos): «4» |
| Encuentra tu próxima inmersión | 02 Asia 104 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (26 elementos): «15» |
| Encuentra tu próxima inmersión | 03 América 24 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (25 elementos): «3» |
| Encuentra tu próxima inmersión | 04 África y Mar Rojo 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (34 elementos): «2» |
| Encuentra tu próxima inmersión | 05 Oceanía 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (11 elementos): «2» |
| Encuentra tu próxima inmersión | 06 Caribe 17 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (27 elementos): «8» |
| Encuentra tu próxima inmersión | Mapa | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| Encuentra tu próxima inmersión | Satélite Disponible próximamente | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Encuentra tu próxima inmersión | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (18 elementos): «Leaflet» |
| Encuentra tu próxima inmersión | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (19 elementos): «2» · hay 15 más iguales en la lista (no se prueban todos) |
| Encuentra tu próxima inmersión | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (18 elementos): «2» · clic forzado (otro elemento lo tapa) |
| Encuentra tu próxima inmersión | Mauritius – Cathedral | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (143 elementos): «×» · hay 1 más iguales en la lista (no se prueban todos) |
| Encuentra tu próxima inmersión | Tofo – Manta Reef | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» |
| Encuentra tu próxima inmersión | Zoom in | Enlace | Funciona | Muestra contenido nuevo (64 elementos): «2» |
| Encuentra tu próxima inmersión | Zoom out | Enlace | Funciona | Cambia su estado (class: leaflet-control-zoom-out → leaflet-control-zoom-out leaflet-disabled) · Cambia la pantalla (4 elementos nuevos, 0 quitados) |
| Encuentra tu próxima inmersión | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Encuentra tu próxima inmersión | OpenStreetMap contributors | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Encuentra tu próxima inmersión | Ver todos los tipos → | Enlace | Funciona | Mismo enlace (#/tipos) que «Tipos de buceo» en «Encuentra tu próxima inmersión»: Abre #/tipos |
| Encuentra tu próxima inmersión | Aguas profundas | Enlace | Funciona | Abre #/tipos?t=aguas-profundas |
| Encuentra tu próxima inmersión | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| Encuentra tu próxima inmersión | Paredes | Enlace | Funciona | Abre #/tipos?t=paredes |
| Encuentra tu próxima inmersión | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| Encuentra tu próxima inmersión | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| Encuentra tu próxima inmersión | Pináculos | Enlace | Funciona | Abre #/tipos?t=pinaculos |

#### El mapa del buceo · `#/explorar`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| El mapa del buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| El mapa del buceo | Todos | Botón | Funciona | Muestra contenido nuevo (36 elementos): «2» |
| El mapa del buceo | Arrecifes | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (58 elementos): «2» |
| El mapa del buceo | Paredes | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (45 elementos): «2» |
| El mapa del buceo | Pecios | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (32 elementos): «2» |
| El mapa del buceo | Cuevas | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (32 elementos): «3» |
| El mapa del buceo | Muck | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (30 elementos): «3» |
| El mapa del buceo | Pináculos | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (27 elementos): «7» |
| El mapa del buceo | Profundas | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (59 elementos): «2» |
| El mapa del buceo | 01 Europa 108 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (40 elementos): «2» |
| El mapa del buceo | 02 Asia 104 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (22 elementos): «2» |
| El mapa del buceo | 03 América 24 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (15 elementos): «2» |
| El mapa del buceo | 04 África y Mar Rojo 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (25 elementos): «2» |
| El mapa del buceo | 05 Oceanía 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (31 elementos): «2» |
| El mapa del buceo | 06 Caribe 17 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (32 elementos): «2» |
| El mapa del buceo | Mapa | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (26 elementos): «Leaflet» |
| El mapa del buceo | Satélite Disponible próximamente | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| El mapa del buceo | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (26 elementos): «Leaflet» |
| El mapa del buceo | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (31 elementos): «2» · clic forzado (otro elemento lo tapa) · hay 29 más iguales en la lista (no se prueban todos) |
| El mapa del buceo | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (14 elementos): «Rainbow Reef» |
| El mapa del buceo | Mauritius – Cathedral | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» · hay 3 más iguales en la lista (no se prueban todos) |
| El mapa del buceo | Tofo – Manta Reef | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» |
| El mapa del buceo | Seguridad en el buceo | Enlace | Funciona | Abre #/legal/seguridad |
| El mapa del buceo | Zoom in | Enlace | Funciona | Muestra contenido nuevo (87 elementos): «2» |
| El mapa del buceo | Zoom out | Enlace | Funciona | Cambia la pantalla (10 elementos nuevos, 0 quitados) |
| El mapa del buceo | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |

#### Puntos de buceo · `#/puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Puntos de buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Puntos de buceo | Puntos de buceo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (68 elementos): «Todo el mundo» |
| Puntos de buceo | Zona Todo el mundo Europa (108) Asia (104) América (24) África y Mar Rojo (20) Oceanía (20) Caribe (17) | Desplegable | Funciona | Abre #/puntos?zone=Europa |
| Puntos de buceo | Para empezar | Botón | Funciona | Abre #/puntos?level=start |
| Puntos de buceo | Intermedio | Botón | Funciona | Abre #/puntos?level=mid |
| Puntos de buceo | Avanzado | Botón | Funciona | Abre #/puntos?level=adv |
| Puntos de buceo | Con centro que lo ofrece | Botón | Funciona | Abre #/puntos?only=centers |
| Puntos de buceo | Confirmación inmediata | Botón | Funciona | Abre #/puntos?only=instant |
| Puntos de buceo | Tipo de buceo Cualquier tipo Arrecifes Paredes Pecios y naufragios Cuevas y cavernas Cenotes Muck Canales Caño | Desplegable | Funciona | Abre #/puntos?type=arrecifes |
| Puntos de buceo | País Todos los países España (93) Filipinas (30) Indonesia (25) Malasia (15) Maldivas (13) Tailandia (13) Egip | Desplegable | Funciona | Abre #/puntos?country=Espa%C3%B1a |
| Puntos de buceo | Ordenar Recomendados Nombre A-Z Más profundos Menos profundos Mejor valorados | Desplegable | Funciona | Abre #/puntos?sort=name |
| Puntos de buceo | ¿Cómo ordenamos? | Enlace | Funciona | Abre #/legal/clasificacion |
| Puntos de buceo | #/punto?id=34 | Enlace | Funciona | Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Blue Hole, Dahab | Enlace | Funciona | Mismo enlace (#/punto?id=34) que «#/punto?id=34» en «Puntos de buceo»: Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Ver punto | Enlace | Funciona | Mismo enlace (#/punto?id=34) que «#/punto?id=34» en «Puntos de buceo»: Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Mostrar más puntos (281) | Botón | Funciona | Cambia su estado (disabled: sin atributo → vacío) · Muestra contenido nuevo (13 elementos): «Arrecifes Paredes Portitxol Norte Marina Alta · Xàbia · España Moderado Arrecife · Pared · Fondo arenoso Ubicación por v» |

#### Centros de buceo · `#/centros`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centros de buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Centros de buceo | Centros de buceo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (11 elementos): «Todos los países» |
| Centros de buceo | País Todos los países España (2) | Desplegable | Funciona | Abre #/centros?country=Espa%C3%B1a |
| Centros de buceo | Confirmación inmediata | Botón | Funciona | Abre #/centros?only=instant |
| Centros de buceo | Reserva online | Botón | Funciona | Abre #/centros?only=online |
| Centros de buceo | Plazas esta semana | Botón | Funciona | Abre #/centros?only=week |
| Centros de buceo | Cursos | Botón | Funciona | Abre #/centros?only=courses |
| Centros de buceo | Bautizos | Botón | Funciona | Abre #/centros?only=try |
| Centros de buceo | Viajes | Botón | Funciona | Abre #/centros?only=trips |
| Centros de buceo | Con reseñas | Botón | Funciona | Abre #/centros?only=reviews |
| Centros de buceo | Tipo de buceo Cualquier tipo de buceo Arrecifes Paredes Pecios y naufragios Cuevas y cavernas Cenotes Muck Can | Desplegable | Funciona | Abre #/centros?type=arrecifes |
| Centros de buceo | Ordenar Recomendados Mejor valorados Más reseñas Precio más bajo Nombre A-Z | Desplegable | Funciona | Abre #/centros?sort=rating |
| Centros de buceo | ¿Cómo ordenamos? | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Centros de buceo | Bajo petición Plazas esta semana | Enlace | Funciona | Abre #/centro?id=31 |
| Centros de buceo | Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Centros de buceo | Reservar | Enlace | Funciona | Abre #/reservar?center=31 |
| Centros de buceo | Bajo petición Plazas esta semana | Enlace | Funciona | Abre #/centro?id=32 |
| Centros de buceo | Escafandra Medes | Enlace | Funciona | Mismo enlace (#/centro?id=32) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=32 |
| Centros de buceo | Reservar | Enlace | Funciona | Abre #/reservar?center=32 |
| Centros de buceo | Dar de alta mi centro | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### ¿Qué inmersión te apetece? · `#/tipos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| ¿Qué inmersión te apetece? | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| ¿Qué inmersión te apetece? | Todos | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| ¿Qué inmersión te apetece? | Para empezar | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Con experiencia | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Avanzado y técnico | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| ¿Qué inmersión te apetece? | Paredes | Enlace | Funciona | Mismo enlace (#/tipos?t=paredes) que «Paredes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=paredes |
| ¿Qué inmersión te apetece? | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| ¿Qué inmersión te apetece? | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| ¿Qué inmersión te apetece? | Cenotes | Enlace | Funciona | Abre #/tipos?t=cenotes |
| ¿Qué inmersión te apetece? | Muck | Enlace | Funciona | Abre #/tipos?t=muck |
| ¿Qué inmersión te apetece? | Canales | Enlace | Funciona | Abre #/tipos?t=canales |
| ¿Qué inmersión te apetece? | Cañones | Enlace | Funciona | Abre #/tipos?t=canones |
| ¿Qué inmersión te apetece? | Pináculos | Enlace | Funciona | Mismo enlace (#/tipos?t=pinaculos) que «Pináculos» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pinaculos |
| ¿Qué inmersión te apetece? | Corrientes y deriva | Enlace | Funciona | Abre #/tipos?t=corrientes-y-deriva |
| ¿Qué inmersión te apetece? | Aguas profundas | Enlace | Funciona | Mismo enlace (#/tipos?t=aguas-profundas) que «Aguas profundas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=aguas-profundas |
| ¿Qué inmersión te apetece? | Lagos | Enlace | Funciona | Abre #/tipos?t=lagos |
| ¿Qué inmersión te apetece? | Pilares | Enlace | Funciona | Abre #/tipos?t=pilares |
| ¿Qué inmersión te apetece? | Nocturnas | Enlace | Funciona | Abre #/tipos?t=nocturnas |
| ¿Qué inmersión te apetece? | Playa y esnórquel | Enlace | Funciona | Abre #/tipos?t=playa-y-esnorquel |
| ¿Qué inmersión te apetece? | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| ¿Qué inmersión te apetece? | Muck | Enlace | Funciona | Mismo enlace (#/tipos?t=muck) que «Muck» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=muck |
| ¿Qué inmersión te apetece? | Lagos | Enlace | Funciona | Mismo enlace (#/tipos?t=lagos) que «Lagos» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=lagos |
| ¿Qué inmersión te apetece? | Pilares | Enlace | Funciona | Mismo enlace (#/tipos?t=pilares) que «Pilares» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=pilares |
| ¿Qué inmersión te apetece? | Paredes | Enlace | Funciona | Mismo enlace (#/tipos?t=paredes) que «Paredes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=paredes |
| ¿Qué inmersión te apetece? | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| ¿Qué inmersión te apetece? | Canales | Enlace | Funciona | Mismo enlace (#/tipos?t=canales) que «Canales» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=canales |
| ¿Qué inmersión te apetece? | Pináculos | Enlace | Funciona | Mismo enlace (#/tipos?t=pinaculos) que «Pináculos» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pinaculos |
| ¿Qué inmersión te apetece? | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| ¿Qué inmersión te apetece? | Cenotes | Enlace | Funciona | Mismo enlace (#/tipos?t=cenotes) que «Cenotes» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=cenotes |
| ¿Qué inmersión te apetece? | Cañones | Enlace | Funciona | Mismo enlace (#/tipos?t=canones) que «Cañones» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=canones |
| ¿Qué inmersión te apetece? | Corrientes y deriva | Enlace | Funciona | Mismo enlace (#/tipos?t=corrientes-y-deriva) que «Corrientes y deriva» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=corrientes-y-deriva |
| ¿Qué inmersión te apetece? | Aguas profundas | Enlace | Funciona | Mismo enlace (#/tipos?t=aguas-profundas) que «Aguas profundas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=aguas-profundas |

#### Viajes y vida a bordo · `#/experiencias`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Viajes y vida a bordo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Viajes y vida a bordo | Viajes y vida a bordo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (16 elementos): «Viaje 1 experiencia Costa Blanca España Experiencias de buceo organizadas por centros y profesionales. DESDE 290 € PRÓXI» |
| Viajes y vida a bordo | Todas | Botón | Funciona | Muestra contenido nuevo (8 elementos): «Viaje 1 experiencia Costa Blanca España Experiencias de buceo organizadas por centros y profesionales. DESDE 290 € PRÓXI» |
| Viajes y vida a bordo | Viaje | Botón | Funciona | Abre #/experiencias?kind=Viaje |
| Viajes y vida a bordo | Vida a bordo | Botón | Funciona | Abre #/experiencias?kind=Vida+a+bordo |
| Viajes y vida a bordo | Ordenar Con más salidas Precio más bajo Próxima salida Nombre A-Z | Desplegable | Funciona | Abre #/experiencias?sort=price |
| Viajes y vida a bordo | Viaje 1 experiencia | Enlace | Funciona | Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Costa Blanca | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Ver viajes | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Ver destino | Enlace | Funciona | Abre #/experiencia?id=5 · hay 3 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Empezar a publicar | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### ¿Te apetece bucear? · `#/top10`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| ¿Te apetece bucear? | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| ¿Te apetece bucear? | Radio 25 km 50 km 100 km 250 km 500 km | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Buscar» (sin efecto inmediato, correcto) |
| ¿Te apetece bucear? | Usar mi ubicación | Botón | Funciona | Muestra contenido nuevo (13 elementos): «1 ARRECIFES Cabo San Antonio Marina Alta · Xàbia · España 7–20 m Moderado ★ 4.4 (9) 1 centro 1,9 km Ver inmersión» |
| ¿Te apetece bucear? | Elegir en el mapa | Botón | Funciona | Abre la ventana «Elige tu ubicación» |
| ¿Te apetece bucear? | ¿Te apetece bucear? | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Buscar una localidad» (campo obligatorio) |
| ¿Te apetece bucear? | Marina Alta · Xàbia | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 ARRECIFES Piedras Rotas Marina Alta · Xàbia · España 7–20 m Fácil ★ 4.4 (9) 1 centro 0,8 km Ver inmersión» |
| ¿Te apetece bucear? | Marina Alta y Baixa · Calpe | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 19,3 km Ver inmersión» |
| ¿Te apetece bucear? | Canarias | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (9 elementos): «1 ARRECIFES Las Canteras, Gran Canaria Canarias · España Iniciación 48,3 km Ver inmersión» |
| ¿Te apetece bucear? | Palawan | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (4 elementos): «1 ARRECIFES El Nido – Cadlao Lagoon Palawan · Filipinas 5–20 m Principiante 72,9 km Ver inmersión» |
| ¿Te apetece bucear? | Comunitat Valenciana | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 25,7 km Ver inmersión» |
| ¿Te apetece bucear? | Andalucía | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (6 elementos): «1 ARRECIFES Costa del Sol, Málaga Andalucía · España Iniciación 52,4 km Ver inmersión» |
| ¿Te apetece bucear? | Marina Alta · Moraira | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 9,7 km Ver inmersión» |
| ¿Te apetece bucear? | Cebu | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (12 elementos): «1 ARRECIFES Moalboal – Sardine Run Cebu · Filipinas 5–25 m Principiante 28,1 km Ver inmersión» |
| ¿Te apetece bucear? | Cataluña | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (12 elementos): «1 ARRECIFES Medes – Tascons Islas Medes · España 6–25 m Intermedio ★ 4.8 (6) 1 centro 2,1 km Ver inmersión» |
| ¿Te apetece bucear? | Illes Balears | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (8 elementos): «1 PAREDES El Toro Mallorca · España 10–35 m Intermedio 12,9 km Ver inmersión» |

#### Planes de WORLDIVES · `#/planes`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Planes de WORLDIVES | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Planes de WORLDIVES | Gestionar mi plan | Enlace | Funciona | Abre #/admin?tab=plan |

#### Cómo funcionan los puntos · `#/como-funcionan-los-puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Cómo funcionan los puntos | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Cómo funcionan los puntos | Ver mis puntos | Enlace | Funciona | Mismo enlace (#/mis-puntos) que «Mis puntos» en «Encuentra tu próxima inmersión»: Abre #/mis-puntos |
| Cómo funcionan los puntos | Ver ventajas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Recompensas» en «Encuentra tu próxima inmersión»: Abre #/recompensas |

#### Aviso legal · `#/legal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Aviso legal | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Aviso legal | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Aviso legal | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Abre #/legal/reservas |
| Aviso legal | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Aviso legal | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Aviso legal | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Aviso legal | Normas de las reseñas | Enlace | Funciona | Abre #/legal/normas-resenas |
| Aviso legal | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Puntos WORLDIVES | Enlace | Funciona | Abre #/legal/puntos |
| Aviso legal | Declaración de accesibilidad | Enlace | Funciona | Abre #/legal/accesibilidad |
| Aviso legal | Contacto | Enlace | Funciona | Abre #/legal/contacto |
| Aviso legal | Créditos y licencias de terceros | Enlace | Funciona | Abre #/legal/creditos |
| Aviso legal | Condiciones de uso | Enlace | Funciona | Abre #/legal/terminos |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Leer | Botón | Funciona | Abre la ventana «Aviso legal» |
| Aviso legal | 1. Titular del sitio web | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 6 más iguales en la lista (no se prueban todos) |
| Aviso legal | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Crear cuenta · `#/registro`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Crear cuenta | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Crear cuenta | Buceador | Enlace | Funciona | Abre #/registro?tipo=recreational |
| Crear cuenta | Centro de buceo Publica tus salidas y cursos y gestiona tus reservas. | Enlace | Funciona | Abre #/registro?tipo=center |
| Crear cuenta | Profesional | Enlace | Funciona | Abre #/registro?tipo=freelance |
| Crear cuenta | Iniciar sesión | Enlace | Funciona | Abre #/cuenta |

#### Condiciones para centros y profesionales · `#/legal/condiciones-centros`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones para centros y profesionales | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones para centros y profesionales | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones para centros y profesionales | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones para centros y profesionales | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones para centros y profesionales | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones para centros y profesionales | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones para centros y profesionales | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones para centros y profesionales | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones para centros y profesionales | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones para centros y profesionales | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones para centros y profesionales | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones para centros y profesionales | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones para centros y profesionales | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones para centros y profesionales | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones para centros y profesionales | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones para centros y profesionales | Planes | Enlace | Funciona | Abre #/planes |
| Condiciones para centros y profesionales | Planes | Enlace | Funciona | Mismo enlace (#/planes) que «Planes» en «Condiciones para centros y profesionales»: Abre #/planes |
| Condiciones para centros y profesionales | normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones para centros y profesionales | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones para centros y profesionales | Leer | Botón | Funciona | Abre la ventana «Condiciones para centros y profesionales» |
| Condiciones para centros y profesionales | 1. Alta y verificación | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 18 más iguales en la lista (no se prueban todos) |
| Condiciones para centros y profesionales | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones para centros y profesionales | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Aviso legal · `#/legal/aviso-legal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Aviso legal | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Aviso legal | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Aviso legal | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Aviso legal | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Aviso legal | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Aviso legal | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Aviso legal | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Aviso legal | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Aviso legal | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Aviso legal | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Aviso legal | Condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/terminos) que «Condiciones de uso» en «Aviso legal»: Abre #/legal/terminos |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Leer | Botón | Funciona | Abre la ventana «Aviso legal» |
| Aviso legal | 1. Titular del sitio web | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 6 más iguales en la lista (no se prueban todos) |
| Aviso legal | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Política de privacidad · `#/legal/privacidad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Política de privacidad | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Política de privacidad | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Política de privacidad | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Política de privacidad | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Política de privacidad | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Política de privacidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de privacidad | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Política de privacidad | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Política de privacidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de privacidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Política de privacidad | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Política de privacidad | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Política de privacidad | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Política de privacidad | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Política de privacidad | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Política de privacidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de privacidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de privacidad | www.aepd.es | Enlace externo | Funciona | Enlace externo a www.aepd.es (no se abre: dirección https válida) |
| Política de privacidad | Leer | Botón | Funciona | Abre la ventana «Política de privacidad» |
| Política de privacidad | 1. Responsable | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 8 más iguales en la lista (no se prueban todos) |
| Política de privacidad | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Política de privacidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Política de cookies y servicios de terceros · `#/legal/cookies`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Política de cookies y servicios de terceros | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Política de cookies y servicios de terceros | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Política de cookies y servicios de terceros | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Política de cookies y servicios de terceros | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Política de cookies y servicios de terceros | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Política de cookies y servicios de terceros | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de cookies y servicios de terceros | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Política de cookies y servicios de terceros | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Política de cookies y servicios de terceros | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de cookies y servicios de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Política de cookies y servicios de terceros | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Política de cookies y servicios de terceros | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Política de cookies y servicios de terceros | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Política de cookies y servicios de terceros | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Política de cookies y servicios de terceros | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Política de cookies y servicios de terceros | Leer | Botón | Funciona | Abre la ventana «Política de cookies y servicios de terceros» |
| Política de cookies y servicios de terceros | Qué usamos | Enlace | Funciona | Cambia tabindex en h2#que-usamos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Política de cookies y servicios de terceros | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Política de cookies y servicios de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de uso para buceadores · `#/legal/condiciones-buceadores`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de uso para buceadores | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de uso para buceadores | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de uso para buceadores | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de uso para buceadores | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de uso para buceadores | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Leer | Botón | Funciona | Abre la ventana «Condiciones de uso para buceadores» |
| Condiciones de uso para buceadores | 1. Qué es WORLDIVES DISCOVERY | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 9 más iguales en la lista (no se prueban todos) |
| Condiciones de uso para buceadores | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de reserva, pago y cancelación · `#/legal/condiciones-reserva`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de reserva, pago y cancelación | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de reserva, pago y cancelación | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de reserva, pago y cancelación | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de reserva, pago y cancelación | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de reserva, pago y cancelación | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de reserva, pago y cancelación | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de reserva, pago y cancelación | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de reserva, pago y cancelación | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de reserva, pago y cancelación | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de reserva, pago y cancelación | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Leer | Botón | Funciona | Abre la ventana «Condiciones de reserva, pago y cancelación» |
| Condiciones de reserva, pago y cancelación | 1. Quién presta la actividad | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 7 más iguales en la lista (no se prueban todos) |
| Condiciones de reserva, pago y cancelación | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Denunciar contenido · `#/legal/denuncias`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Denunciar contenido | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Denunciar contenido | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Denunciar contenido | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Denunciar contenido | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Denunciar contenido | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Denunciar contenido | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Denunciar contenido | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Denunciar contenido | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Denunciar contenido | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Denunciar contenido | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Denunciar contenido | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Denunciar contenido | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Denunciar contenido | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Denunciar contenido | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Denunciar contenido | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Denunciar contenido | Formulario de denuncia | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Motivo» (elige una opción de la lista) · El navegador no deja enviarlo: «Explica por qué es ilegal o incumple las condiciones» (campo obligatorio) |
| Denunciar contenido | Motivo | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Enviar denuncia» (sin efecto inmediato, correcto) |
| Denunciar contenido | Leer | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Denunciar contenido | Qué necesitamos | Enlace | Funciona | Cambia tabindex en h2#que-necesitamos (sin atributo → -1) · hay 2 más iguales en la lista (no se prueban todos) |
| Denunciar contenido | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Denunciar contenido | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Seguridad en el buceo · `#/legal/seguridad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Seguridad en el buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Seguridad en el buceo | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Seguridad en el buceo | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Seguridad en el buceo | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Seguridad en el buceo | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Seguridad en el buceo | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Seguridad en el buceo | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Seguridad en el buceo | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Seguridad en el buceo | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Seguridad en el buceo | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Seguridad en el buceo | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Seguridad en el buceo | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Seguridad en el buceo | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Seguridad en el buceo | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Seguridad en el buceo | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Seguridad en el buceo | Leer | Botón | Funciona | Abre la ventana «Seguridad en el buceo» |
| Seguridad en el buceo | Antes de reservar | Enlace | Funciona | Cambia tabindex en h2#antes-de-reservar (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Seguridad en el buceo | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Seguridad en el buceo | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Cómo ordenamos los resultados · `#/legal/clasificacion`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Cómo ordenamos los resultados | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Cómo ordenamos los resultados | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Cómo ordenamos los resultados | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Cómo ordenamos los resultados | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Cómo ordenamos los resultados | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Cómo ordenamos los resultados | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Cómo ordenamos los resultados | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Cómo ordenamos los resultados | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Cómo ordenamos los resultados | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Cómo ordenamos los resultados | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Cómo ordenamos los resultados | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Cómo ordenamos los resultados | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Cómo ordenamos los resultados | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Cómo ordenamos los resultados | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Cómo ordenamos los resultados | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Cómo ordenamos los resultados | Leer | Botón | Funciona | Abre la ventana «Cómo ordenamos los resultados» |
| Cómo ordenamos los resultados | Directorio de centros | Enlace | Funciona | Cambia tabindex en h2#directorio-de-centros (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Cómo ordenamos los resultados | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Cómo ordenamos los resultados | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Blue Hole, Dahab · `#/punto?id=34`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Blue Hole, Dahab | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Blue Hole, Dahab | Puntos de buceo | Enlace | Funciona | Mismo enlace (#/puntos) que «Puntos de buceo» en «Encuentra tu próxima inmersión»: Abre #/puntos |
| Blue Hole, Dahab | África y Mar Rojo | Enlace | Funciona | Abre #/puntos?zone=%C3%81frica+y+Mar+Rojo |
| Blue Hole, Dahab | Abrir en el mapa | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Blue Hole, Dahab | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Encuentra tu próxima inmersión»: Abre #/cuenta |
| Blue Hole, Dahab | ¿Tienes un centro? Únete a WORLDIVES | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |
| Blue Hole, Dahab | Blue Hole Dahab Dahab · Egipto 6–60 m · Avanzado a 0 km | Enlace | Funciona | Abre #/punto?id=247 |
| Blue Hole, Dahab | Canyon Dahab Dahab · Egipto 8–30 m · Intermedio a 2,9 km | Enlace | Funciona | Abre #/punto?id=248 |
| Blue Hole, Dahab | Blue Hole, Dahab | Elemento div (role=button) | Funciona | Mueve o amplía el mapa |
| Blue Hole, Dahab | Mapa | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (8 elementos): «Leaflet» |
| Blue Hole, Dahab | Satélite | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Relieve orientativo (GEBCO). No sirve para navegar ni para la seguridad en el mar. Seguridad en el buceo» |
| Blue Hole, Dahab | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (10 elementos): «Leaflet» |
| Blue Hole, Dahab | Zoom in | Enlace | Funciona | Cambia la pantalla (5 elementos nuevos, 2 quitados) |
| Blue Hole, Dahab | Zoom out | Enlace | Funciona | Cambia la pantalla (5 elementos nuevos, 2 quitados) |
| Blue Hole, Dahab | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Blue Hole, Dahab | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Blue Hole, Dahab | Abrir en OpenStreetMap | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Blue Hole, Dahab | Proponer nueva posición | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Latitud Longitud Motivo» |
| Blue Hole, Dahab | Denunciar contenido | Botón | Funciona | Abre la ventana «Denunciar contenido» |

#### Bahía Coralina Centro de Buceo · `#/centro?id=31`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | Centros | Enlace | Funciona | Mismo enlace (#/centros) que «Centros» en «Encuentra tu próxima inmersión»: Abre #/centros |
| Bahía Coralina Centro de Buceo | Reservar | Enlace | Funciona | Mismo enlace (#/reservar?center=31) que «Reservar» en «Centros de buceo»: Abre #/reservar?center=31 |
| Bahía Coralina Centro de Buceo | Llamar | Enlace externo | Funciona | Teléfono +34600000101 |
| Bahía Coralina Centro de Buceo | Escribir | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | Lun, 19 oct 10:00 6 plazas | Enlace | Funciona | Abre #/reservar?center=31&service=7&slot=22 · POST /api/stats/track → 200 · hay 11 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Enviar solicitud | Enlace | Funciona | Abre #/reservar?center=31&service=7 · POST /api/stats/track → 200 · hay 3 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Añadir a una reserva | Enlace | Funciona | Abre #/reservar?center=31&service=8 · POST /api/stats/track → 200 |
| Bahía Coralina Centro de Buceo | Tres días en la reserva del Cabo de San Antonio | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Foto 1 de Bahía Coralina Centro de Buceo | Botón | Funciona | Abre la ventana «Bahía Coralina Centro de Buceo» · hay 2 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Foto 2 de Bahía Coralina Centro de Buceo | Botón | Funciona | Abre la ventana «Bahía Coralina Centro de Buceo» |
| Bahía Coralina Centro de Buceo | Responder | Botón | Funciona | Abre la ventana «Responder a la reseña» · hay 1 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» · hay 7 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Editar respuesta | Botón | Funciona | Abre la ventana «Responder a la reseña» · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Bahía Coralina Centro de Buceo | Editar respuesta | Botón | Funciona | Abre la ventana «Responder a la reseña» |
| Bahía Coralina Centro de Buceo | Responder | Botón | Funciona | Abre la ventana «Responder a la reseña» |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34600000101 |
| Bahía Coralina Centro de Buceo | hola@bahiacoralina.example.com | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | bahiacoralina.example.com | Enlace externo | Funciona | Enlace externo a bahiacoralina.example.com (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo | Ver en el mapa | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo | Reservar con Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/reservar?center=31) que «Reservar» en «Centros de buceo»: Abre #/reservar?center=31 |
| Bahía Coralina Centro de Buceo | Denunciar contenido | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Bahía Coralina Centro de Buceo | Cabo San Antonio | Enlace | Funciona | Abre #/punto?id=329 · hay 5 más iguales en la lista (no se prueban todos) |

#### Bahía Coralina Centro de Buceo · `#/reservar?center=31`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | ← Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | Bautizo de buceo | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «No admite reservas ahora mismo» |
| Bahía Coralina Centro de Buceo | Curso Open Water (3 días) | Botón | Funciona | Muestra contenido nuevo (14 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Curso de Nitrox | Botón | Funciona | Muestra contenido nuevo (13 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Doble inmersión en barco | Botón | Funciona | Muestra contenido nuevo (26 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Inmersión al atardecer | Botón | Funciona | Muestra contenido nuevo (17 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Inmersión simple en barco | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «No admite reservas ahora mismo» |
| Bahía Coralina Centro de Buceo | Una persona menos | Botón | Desactivado (correcto) | Desactivado: es el límite del calendario o de la lista («Una persona menos») |
| Bahía Coralina Centro de Buceo | Una persona más | Botón | Desactivado (correcto) | No responde al ratón (pointer-events: none) y se ve atenuado; la pantalla explica: «Elige primero la actividad.» |
| Bahía Coralina Centro de Buceo | Elige una actividad | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Política de cancelación. Moderada: cancelación gratuita hasta 48 horas antes de la actividad; después no hay reembolso.» |
| Bahía Coralina Centro de Buceo | condiciones de reserva | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Bahía Coralina Centro de Buceo | condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34600000101 |

#### Costa Blanca · `#/experiencia?id=7`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Costa Blanca | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Costa Blanca | Experiencias | Enlace | Funciona | Mismo enlace (#/experiencias) que «Experiencias» en «Encuentra tu próxima inmersión»: Abre #/experiencias |
| Costa Blanca | BAHÍA CORALINA CENTRO DE BUCEO | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Costa Blanca | Solicitar plaza | Botón | Funciona | Abre #/experienciareserva?id=2 |
| Costa Blanca | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Costa Blanca | Publicar un viaje | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### Condiciones de reserva, pago y cancelación · `#/legal/reservas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de reserva, pago y cancelación | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de reserva, pago y cancelación | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de reserva, pago y cancelación | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de reserva, pago y cancelación | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de reserva, pago y cancelación | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de reserva, pago y cancelación | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de reserva, pago y cancelación | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de reserva, pago y cancelación | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de reserva, pago y cancelación | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de reserva, pago y cancelación | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Leer | Botón | Funciona | Abre la ventana «Condiciones de reserva, pago y cancelación» |
| Condiciones de reserva, pago y cancelación | 1. Quién presta la actividad | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 7 más iguales en la lista (no se prueban todos) |
| Condiciones de reserva, pago y cancelación | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Normas de las reseñas · `#/legal/normas-resenas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Normas de las reseñas | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Normas de las reseñas | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Normas de las reseñas | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Normas de las reseñas | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Normas de las reseñas | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Normas de las reseñas | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Normas de las reseñas | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Normas de las reseñas | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Normas de las reseñas | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Normas de las reseñas | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Normas de las reseñas | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Normas de las reseñas | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Normas de las reseñas | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Normas de las reseñas | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Normas de las reseñas | Leer | Botón | Funciona | Abre la ventana «Normas de las reseñas» |
| Normas de las reseñas | Quién puede escribir una reseña | Enlace | Funciona | Cambia tabindex en h2#quien-puede-escribir-una-resena (sin atributo → -1) · hay 4 más iguales en la lista (no se prueban todos) |
| Normas de las reseñas | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Puntos WORLDIVES · `#/legal/puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Puntos WORLDIVES | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Puntos WORLDIVES | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Puntos WORLDIVES | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Puntos WORLDIVES | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Puntos WORLDIVES | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Puntos WORLDIVES | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Puntos WORLDIVES | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Puntos WORLDIVES | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Puntos WORLDIVES | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Puntos WORLDIVES | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Puntos WORLDIVES | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Puntos WORLDIVES | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Puntos WORLDIVES | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Puntos WORLDIVES | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Puntos WORLDIVES | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Puntos WORLDIVES | Condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Puntos WORLDIVES | Leer | Botón | Funciona | Abre la ventana «Puntos WORLDIVES» |
| Puntos WORLDIVES | 1. Cómo se consiguen | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Puntos WORLDIVES | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Puntos WORLDIVES | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Declaración de accesibilidad · `#/legal/accesibilidad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Declaración de accesibilidad | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Declaración de accesibilidad | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Declaración de accesibilidad | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Declaración de accesibilidad | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Declaración de accesibilidad | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Declaración de accesibilidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Declaración de accesibilidad | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Declaración de accesibilidad | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Declaración de accesibilidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Declaración de accesibilidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Declaración de accesibilidad | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Declaración de accesibilidad | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Declaración de accesibilidad | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Declaración de accesibilidad | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Declaración de accesibilidad | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Declaración de accesibilidad | Leer | Botón | Funciona | Abre la ventana «Declaración de accesibilidad» |
| Declaración de accesibilidad | Situación actual | Enlace | Funciona | Cambia tabindex en h2#situacion-actual (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Declaración de accesibilidad | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Declaración de accesibilidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Contacto · `#/legal/contacto`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Contacto | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Contacto | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Contacto | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Contacto | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Contacto | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Contacto | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Contacto | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Contacto | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Contacto | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Contacto | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Contacto | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Contacto | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Contacto | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Contacto | Escríbenos | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Asunto» (elige una opción de la lista) · El navegador no deja enviarlo: «Tu nombre» (campo obligatorio) |
| Contacto | Ve a «Denunciar contenido» | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Asunto | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Enviar mensaje» (sin efecto inmediato, correcto) |
| Contacto | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Contacto | Leer | Botón | Funciona | Abre la ventana «Contacto» |
| Contacto | Quién somos | Enlace | Funciona | Cambia tabindex en h2#quien-somos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Contacto | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Créditos y licencias de terceros · `#/legal/creditos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Créditos y licencias de terceros | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Créditos y licencias de terceros | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Créditos y licencias de terceros | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Créditos y licencias de terceros | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Créditos y licencias de terceros | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Créditos y licencias de terceros | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Créditos y licencias de terceros | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Créditos y licencias de terceros | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Créditos y licencias de terceros | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Créditos y licencias de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Créditos y licencias de terceros | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Créditos y licencias de terceros | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Créditos y licencias de terceros | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Créditos y licencias de terceros | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Créditos y licencias de terceros | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Créditos y licencias de terceros | OpenStreetMap contributors | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Protomaps | Enlace externo | Funciona | Enlace externo a protomaps.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Esri World Imagery | Enlace externo | Funciona | Enlace externo a www.arcgis.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | gebco.net | Enlace externo | Funciona | Enlace externo a www.gebco.net (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leaflet.markercluster | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | protomaps-leaflet | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | qrcode | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | stripe-python | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | fontTools | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leer | Botón | Funciona | Abre la ventana «Créditos y licencias de terceros» |
| Créditos y licencias de terceros | Mapas y datos geográficos | Enlace | Funciona | Cambia tabindex en h2#mapas-y-datos-geograficos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Créditos y licencias de terceros | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Créditos y licencias de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de uso para buceadores · `#/legal/terminos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de uso para buceadores | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de uso para buceadores | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de uso para buceadores | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de uso para buceadores | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de uso para buceadores | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Leer | Botón | Funciona | Abre la ventana «Condiciones de uso para buceadores» |
| Condiciones de uso para buceadores | 1. Qué es WORLDIVES DISCOVERY | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 9 más iguales en la lista (no se prueban todos) |
| Condiciones de uso para buceadores | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Bahía Coralina Centro de Buceo · ⌂ Resumen · `#/admin`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Ver mi página | Enlace | Funciona | Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Actualizar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Miércoles, 14 de octubre Buenos días. Hoy tienes 4 reservas con 6 buceadores. + Nueva reserva Abrir planning Hoy 4 6 per» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ⌂ Resumen | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Miércoles, 14 de octubre Buenos días. Hoy tienes 4 reservas con 6 buceadores. + Nueva reserva Abrir planning Hoy 4 6 per» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ▦ Planning / agenda | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (3 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ▣ Reservas 2 | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ♙ Clientes | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (1 elementos): «Base de clientes Clientes Todas las personas que han reservado con tu centro o han hecho check-in con tu QR. 20 clientes» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ◈ Servicios y tarifas | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (11 elementos): «Cargando catálogo…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ✈ Experiencias | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (3 elementos): «Cargando experiencias…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ▤ Cobros y pagos | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (3 elementos): «COBROS Y PAGOS Cobros del centro El cliente paga en una página segura de Stripe y el dinero va directamente a tu cuenta » |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ◔ Analítica e informes | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (1 elementos): «ANALÍTICA Informes y rendimiento Datos operativos del centro, calculados a partir de las reservas reales. Exportar CSV I» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ↔ Web e integraciones | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (1 elementos): «CONECTIVIDAD Web, API y sincronización Conecta el motor de reservas de la web del centro para que las reservas entren di» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ⌖ Puntos de buceo | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (22 elementos): «CENTRO · PUNTOS Mis puntos de buceo Asocia aquí los lugares a los que suele ir tu centro. No necesitas crear el punto de» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ◍ Vídeos y vida marina | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (3 elementos): «Cargando…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ▣ Check-in / QR y promociones | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (3 elementos): «Promociones Validar un código QR de check-in» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ✦ Escaparate y datos | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (2 elementos): «Tu página pública Escaparate Así ven tu centro los buceadores. Cambia la portada, las fotos y los textos cuando quieras.» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ★ Recompensas | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (2 elementos): «PUNTOS WORLDIVES Ventajas y puntos Los buceadores canjean sus puntos por las ventajas que tu centro define y paga. Los p» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ✆ Avisos y WhatsApp | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (3 elementos): «Avisos Avisos a tus clientes y WhatsApp Si cancelas una salida o cambias la hora o el punto de encuentro, avisamos a tod» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ✉ Solicitudes de información | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (2 elementos): «Solicitudes de información Mensajes de buceadores interesados Contesta directamente por email o teléfono. Te llegan tamb» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ◑ Estadísticas | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (2 elementos): «Estadísticas Cómo te encuentran los buceadores Datos agregados, sin datos personales. Disponibles en todos los planes. P» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ⇩ Herramientas | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (4 elementos): «Herramientas Exportar, calendario, widget e importación Exportar mis datos (CSV) Disponible siempre, en cualquier plan. » |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ☺ Equipo | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (2 elementos): «Equipo Personas que gestionan el centro Cada persona tiene un perfil. Abajo puedes cambiar lo que puede hacer cada perfi» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ☷ Registro de actividad | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (2 elementos): «Registro de actividad Quién ha hecho qué en el centro FECHA PERSONA ACCIÓN 2026-10-13 22:33 Marta Llorens login 2026-10-» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | § Datos fiscales y seguro | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (2 elementos): «Datos fiscales y verificación Datos del prestador (DAC7) y seguro La normativa europea DAC7 obliga a las plataformas a i» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ◆ Mi plan | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (2 elementos): «Mi plan Pro Activo Activo hasta el 13 de octubre de 2027. Las reservas que ya tienes se atienden siempre y puedes export» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | + Nueva reserva | Botón | Funciona | Abre la ventana «Nueva reserva» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Abrir planning | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Hoy 4 6 personas | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Solicitudes pendientes 2 Necesitan respuesta | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Por cobrar 390 € 1 reserva | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Próximos 7 días 30 reservas | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Cobrado 34.573,44 € total registrado | Botón | Funciona | Muestra contenido nuevo (1 elementos): «ANALÍTICA Informes y rendimiento Datos operativos del centro, calculados a partir de las reservas reales. Exportar CSV I» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Ver la semana | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | 08:00 | Enlace | Funciona | Abre #/reserva?id=1250 · hay 10 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Ir a reservas | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Programar salidas | Botón | Funciona | Muestra contenido nuevo (11 elementos): «Cargando catálogo…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Publicar un viaje | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando experiencias…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Editar escaparate | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Tu página pública Escaparate Así ven tu centro los buceadores. Cambia la portada, las fotos y los textos cuando quieras.» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Ver clientes | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Base de clientes Clientes Todas las personas que han reservado con tu centro o han hecho check-in con tu QR. 20 clientes» |

#### Tu ficha de buceador · `#/cuenta`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Tu ficha de buceador | Explorador 0 puntos | Enlace | Funciona | Abre #/recompensas |
| Tu ficha de buceador | Mi centro | Enlace | Funciona | Abre #/admin |
| Tu ficha de buceador | Log Book | Enlace | Funciona | Abre #/logbook |
| Tu ficha de buceador | Recompensas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Tu ficha de buceador»: Abre #/recompensas |
| Tu ficha de buceador | Mis puntos | Enlace | Funciona | Abre #/mis-puntos |
| Tu ficha de buceador | Mi cuenta | Enlace | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| Tu ficha de buceador | Datos personales | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Nombre y apellidos» (campo obligatorio) |
| Tu ficha de buceador | Prefijo del país | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Idioma preferido | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Nivel de certificación | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | ¿Sueles alquilar equipo? | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Tipo de traje | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Documentación | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Título» (campo obligatorio) · El navegador no deja enviarlo: «Archivo (PDF o imagen, máximo 10 MB)» (falta el archivo) |
| Tu ficha de buceador | Tipo | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Seguridad | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Contraseña actual» (campo obligatorio) · El navegador no deja enviarlo: «Nueva contraseña» (campo obligatorio) |
| Tu ficha de buceador | Activar | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Tu contraseña» (campo obligatorio) |
| Tu ficha de buceador | Descargar mis datos (ZIP) | Enlace | Funciona | Descarga /api/account/export?format=zip (200, application/zip) |
| Tu ficha de buceador | Privacidad | Enlace | Funciona | Abre #/legal/privacidad |
| Tu ficha de buceador | Condiciones de uso | Enlace | Funciona | Abre #/legal/condiciones-buceadores |
| Tu ficha de buceador | Condiciones de reserva | Enlace | Funciona | Abre #/legal/condiciones-reserva |
| Tu ficha de buceador | Cookies | Enlace | Funciona | Abre #/legal/cookies |
| Tu ficha de buceador | Abrir el panel | Enlace | Funciona | Mismo enlace (#/admin) que «Mi centro» en «Tu ficha de buceador»: Abre #/admin |
| Tu ficha de buceador | Borrar mi cuenta para siempre | Botón | Funciona | [probado al final del papel] Abre la ventana «Borrar mi cuenta para siempre» |
| Tu ficha de buceador | Cerrar sesión | Botón | Funciona | [probado al final del papel] Abre #/ · POST /api/auth/logout → 200 · cierra la sesión o cambia la cuenta: se vuelve a iniciar sesión |

#### Log Book · `#/logbook`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Log Book | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Tu ficha de buceador»: Abre #/recompensas |
| Log Book | Exportar CSV | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Tu historial de inmersiones. Las reservas completadas se añaden solas; el resto, en un momento.» |
| Log Book | Nueva inmersión | Botón | Funciona | Abre la ventana «Nueva inmersión» |
| Log Book | Añadir mi primera inmersión | Botón | Funciona | Abre la ventana «Nueva inmersión» |

#### Recompensas · `#/recompensas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Recompensas | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Tu ficha de buceador»: Abre #/recompensas |
| Recompensas | Cómo funcionan | Enlace | Funciona | Abre #/como-funcionan-los-puntos |
| Recompensas | Canjear | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Linterna para la nocturna» · hay 2 más iguales en la lista (no se prueban todos) |
| Recompensas | Canjear | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Te faltan 150 puntos» |

#### Mis puntos · `#/mis-puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Mis puntos | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Tu ficha de buceador»: Abre #/recompensas |
| Mis puntos | Ver ventajas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Tu ficha de buceador»: Abre #/recompensas |
| Mis puntos | Más información sobre los puntos | Enlace | Funciona | Mismo enlace (#/como-funcionan-los-puntos) que «Cómo funcionan» en «Recompensas»: Abre #/como-funcionan-los-puntos |

#### Hannah Weber · `#/reserva?id=1250`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Hannah Weber | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Hannah Weber | Reservas | Enlace | Funciona | Abre #/admin?tab=bookings |
| Hannah Weber | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1250/receipt.pdf (200, application/pdf) |
| Hannah Weber | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1250/diver-sheet.pdf (200, application/pdf) |
| Hannah Weber | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Hannah Weber | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Hannah Weber | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| Hannah Weber | PDF | Enlace | Funciona | Descarga /api/bookings/1250/diver-sheet.pdf (200, application/pdf) |
| Hannah Weber | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Emily Clarke · `#/reserva?id=1265`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Emily Clarke | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Emily Clarke | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Emily Clarke | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1265/receipt.pdf (200, application/pdf) |
| Emily Clarke | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1265/diver-sheet.pdf (200, application/pdf) |
| Emily Clarke | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Emily Clarke | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Emily Clarke | Aceptar | Botón | Funciona | Aviso: «Reserva confirmada.» · Muestra contenido nuevo (2 elementos): «← Volver» · POST /api/bookings/1265/status → 200 |
| Emily Clarke | Rechazar | Botón | Funciona | Abre la ventana «Rechazar la solicitud» |
| Emily Clarke | PDF | Enlace | Funciona | Descarga /api/bookings/1265/diver-sheet.pdf (200, application/pdf) |
| Emily Clarke | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Chloé Martin · `#/reserva?id=1264`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Chloé Martin | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Chloé Martin | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Chloé Martin | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1264/receipt.pdf (200, application/pdf) |
| Chloé Martin | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1264/diver-sheet.pdf (200, application/pdf) |
| Chloé Martin | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Chloé Martin | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Chloé Martin | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| Chloé Martin | PDF | Enlace | Funciona | Descarga /api/bookings/1264/diver-sheet.pdf (200, application/pdf) |
| Chloé Martin | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Lukas Becker · `#/reserva?id=1263`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Lukas Becker | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Lukas Becker | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Lukas Becker | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1263/receipt.pdf (200, application/pdf) |
| Lukas Becker | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1263/diver-sheet.pdf (200, application/pdf) |
| Lukas Becker | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Lukas Becker | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Lukas Becker | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| Lukas Becker | PDF | Enlace | Funciona | Descarga /api/bookings/1263/diver-sheet.pdf (200, application/pdf) |
| Lukas Becker | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Hannah Weber · `#/reserva?id=1249`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Hannah Weber | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Hannah Weber | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Hannah Weber | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1249/receipt.pdf (200, application/pdf) |
| Hannah Weber | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1249/diver-sheet.pdf (200, application/pdf) |
| Hannah Weber | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Hannah Weber | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Hannah Weber | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| Hannah Weber | PDF | Enlace | Funciona | Descarga /api/bookings/1249/diver-sheet.pdf (200, application/pdf) |
| Hannah Weber | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### João Silva · `#/reserva?id=1244`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| João Silva | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| João Silva | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| João Silva | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1244/receipt.pdf (200, application/pdf) |
| João Silva | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1244/diver-sheet.pdf (200, application/pdf) |
| João Silva | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| João Silva | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| João Silva | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| João Silva | PDF | Enlace | Funciona | Descarga /api/bookings/1244/diver-sheet.pdf (200, application/pdf) |
| João Silva | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Tom Jansen · `#/reserva?id=1239`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Tom Jansen | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Tom Jansen | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Tom Jansen | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1239/receipt.pdf (200, application/pdf) |
| Tom Jansen | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1239/diver-sheet.pdf (200, application/pdf) |
| Tom Jansen | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Tom Jansen | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Tom Jansen | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| Tom Jansen | PDF | Enlace | Funciona | Descarga /api/bookings/1239/diver-sheet.pdf (200, application/pdf) |
| Tom Jansen | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Giulia Romano · `#/reserva?id=1268`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Giulia Romano | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Giulia Romano | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Giulia Romano | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1268/receipt.pdf (200, application/pdf) |
| Giulia Romano | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1268/diver-sheet.pdf (200, application/pdf) |
| Giulia Romano | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Giulia Romano | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Giulia Romano | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| Giulia Romano | PDF | Enlace | Funciona | Descarga /api/bookings/1268/diver-sheet.pdf (200, application/pdf) |
| Giulia Romano | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Bea Navarro · `#/reserva?id=1230`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bea Navarro | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bea Navarro | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Bea Navarro | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1230/receipt.pdf (200, application/pdf) |
| Bea Navarro | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1230/diver-sheet.pdf (200, application/pdf) |
| Bea Navarro | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Bea Navarro | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Bea Navarro | Aceptar | Botón | Funciona | Aviso: «Reserva confirmada.» · Muestra contenido nuevo (2 elementos): «← Volver» · POST /api/bookings/1230/status → 200 |
| Bea Navarro | Rechazar | Botón | Funciona | Abre la ventana «Rechazar la solicitud» |
| Bea Navarro | PDF | Enlace | Funciona | Descarga /api/bookings/1230/diver-sheet.pdf (200, application/pdf) |
| Bea Navarro | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Bahía Coralina Centro de Buceo · ▦ Planning / agenda · `#/admin?tab=planning`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Actualizar | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Mes anterior | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Mes siguiente | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Mes | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Lista | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | + Reserva | Botón | Funciona | Abre la ventana «Nueva reserva» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Crear cartel | Botón | Funciona | Abre la ventana «Crear cartel para redes» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Abr | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | May 34 | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Oct 75 | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Nov | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» · hay 3 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Dic | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Jueves, 1 de octubre | Botón | Funciona | Abre la ventana «Jueves, 1 de octubre» · Cambia su estado (class: pl-cell  is-past  → pl-cell is-past is-open) · hay 2 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Viernes, 2 de octubre | Botón | Funciona | Abre la ventana «Viernes, 2 de octubre» · Cambia su estado (class: pl-cell  is-past  → pl-cell is-past is-open) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Sábado, 3 de octubre: 3 salidas, 4 buceadores | Botón | Funciona | Abre la ventana «Sábado, 3 de octubre» · Cambia su estado (class: pl-cell  is-past has-events → pl-cell is-past has-events is-open) · hay 6 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Domingo, 4 de octubre: 1 salidas, 3 buceadores | Botón | Funciona | Abre la ventana «Domingo, 4 de octubre» · Cambia su estado (class: pl-cell  is-past has-events → pl-cell is-past has-events is-open) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Martes, 13 de octubre | Botón | Funciona | Abre la ventana «Martes, 13 de octubre» · Cambia su estado (class: pl-cell is-today   → pl-cell is-today is-open) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Miércoles, 14 de octubre: 5 salidas, 7 buceadores | Botón | Funciona | Abre la ventana «Miércoles, 14 de octubre» · Cambia su estado (class: pl-cell   has-events → pl-cell has-events is-open) · hay 10 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Jueves, 15 de octubre: 5 salidas, 7 buceadores | Botón | Funciona | Abre la ventana «Jueves, 15 de octubre» · Cambia su estado (class: pl-cell   has-events → pl-cell has-events is-open) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Sábado, 24 de octubre | Botón | Funciona | Abre la ventana «Sábado, 24 de octubre» · Cambia su estado (class: pl-cell    → pl-cell is-open) · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Domingo, 25 de octubre | Botón | Funciona | Abre la ventana «Domingo, 25 de octubre» · Cambia su estado (class: pl-cell    → pl-cell is-open) |

#### Bahía Coralina Centro de Buceo · ▦ Planning / agenda › Lista · `#/admin?tab=planning` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda › Lista | 3 | Botón | Funciona | Abre la ventana «Sábado, 3 de octubre» · Cambia su estado (class: pl-lday-head → pl-lday-head is-open) · hay 18 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda › Lista | 4 | Botón | Funciona | Abre la ventana «Domingo, 4 de octubre» · Cambia su estado (class: pl-lday-head → pl-lday-head is-open) |

#### Bahía Coralina Centro de Buceo · ▣ Reservas · `#/admin?tab=bookings`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▣ Reservas | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Actualizar | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | + Nueva reserva | Botón | Funciona | Abre la ventana «Nueva reserva» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Hoy | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Próximos 7 días | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Solicitudes pendientes 2 | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Por cobrar 1 | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Todas las próximas | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Historial | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Actividad | Desplegable | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Registrar cobro | Botón | Funciona | Abre la ventana «Registrar pago» · hay 26 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Completar | Botón | Funciona | Aviso: «Solo puedes marcar como completada una reserva cuya fecha ya ha llegado.» · POST /api/bookings/1250/status → 400 «Solo puedes marcar como completada una reserva cuya fecha ya ha llegado.» · hay 1 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Registrar cobro | Botón | Funciona | Abre la ventana «Registrar pago» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Completar | Botón | Funciona | Aviso: «Solo puedes marcar como completada una reserva cuya fecha ya ha llegado.» · POST /api/bookings/1263/status → 400 «Solo puedes marcar como completada una reserva cuya fecha ya ha llegado.» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Aceptar | Botón | Funciona | Aviso: «Reserva aceptada.» · Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» · POST /api/bookings/1265/status → 200 |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Rechazar | Botón | Funciona | Abre la ventana «Rechazar la solicitud» |

#### Bahía Coralina Centro de Buceo · ▣ Reservas › Historial · `#/admin?tab=bookings` (1 clic en subpestaña)

Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).

#### Bahía Coralina Centro de Buceo · ▣ Reservas › Todas las próximas · `#/admin?tab=bookings` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▣ Reservas › Todas las próximas | Aceptar | Botón | Funciona | Aviso: «Reserva aceptada.» · Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» · POST /api/bookings/1230/status → 200 |
| Bahía Coralina Centro de Buceo · ▣ Reservas › Todas las próximas | Rechazar | Botón | Funciona | Abre la ventana «Rechazar la solicitud» |
| Bahía Coralina Centro de Buceo · ▣ Reservas › Todas las próximas | Registrar cobro | Botón | Funciona | Abre la ventana «Registrar pago» · hay 32 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▣ Reservas › Todas las próximas | Registrar cobro | Botón | Funciona | Abre la ventana «Registrar pago» |

#### Bahía Coralina Centro de Buceo · ▣ Reservas › Por cobrar · `#/admin?tab=bookings` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▣ Reservas › Por cobrar | ▣ Reservas 1 | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ▣ Reservas › Por cobrar | Solicitudes pendientes 1 | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |

#### Bahía Coralina Centro de Buceo · ▣ Reservas › Solicitudes pendientes · `#/admin?tab=bookings` (1 clic en subpestaña)

Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).

#### Bahía Coralina Centro de Buceo · ▣ Reservas › Hoy · `#/admin?tab=bookings` (1 clic en subpestaña)

Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).

#### Bahía Coralina Centro de Buceo · ♙ Clientes · `#/admin?tab=clients`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ♙ Clientes | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ♙ Clientes | Actualizar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Base de clientes Clientes Todas las personas que han reservado con tu centro o han hecho check-in con tu QR. 20 clientes» |
| Bahía Coralina Centro de Buceo · ♙ Clientes | bea.navarro@example.com | Enlace externo | Funciona | Correo bea.navarro@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | wei.chen@example.com | Enlace externo | Funciona | Correo wei.chen@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | pierre.lambert@example.com | Enlace externo | Funciona | Correo pierre.lambert@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | kasia.nowak@example.com | Enlace externo | Funciona | Correo kasia.nowak@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | nuria.costa@example.com | Enlace externo | Funciona | Correo nuria.costa@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | lukas.becker@example.com | Enlace externo | Funciona | Correo lukas.becker@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | chloe.martin@example.com | Enlace externo | Funciona | Correo chloe.martin@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | giulia.romano@example.com | Enlace externo | Funciona | Correo giulia.romano@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | tom.jansen@example.com | Enlace externo | Funciona | Correo tom.jansen@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | emily.clarke@example.com | Enlace externo | Funciona | Correo emily.clarke@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | alvaro.ruiz@example.com | Enlace externo | Funciona | Correo alvaro.ruiz@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | joao.silva@example.com | Enlace externo | Funciona | Correo joao.silva@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | hannah.weber@example.com | Enlace externo | Funciona | Correo hannah.weber@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | sofie.devries@example.com | Enlace externo | Funciona | Correo sofie.devries@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | raul.ortega@example.com | Enlace externo | Funciona | Correo raul.ortega@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | lucia.prieto@example.com | Enlace externo | Funciona | Correo lucia.prieto@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | anna.kowalska@example.com | Enlace externo | Funciona | Correo anna.kowalska@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | marco.bianchi@example.com | Enlace externo | Funciona | Correo marco.bianchi@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | james.walker@example.com | Enlace externo | Funciona | Correo james.walker@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | li.na@example.com | Enlace externo | Funciona | Correo li.na@example.com |

#### Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas · `#/admin?tab=services`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Actualizar | Botón | Funciona | Muestra contenido nuevo (11 elementos): «Cargando catálogo…» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | + Nuevo servicio | Botón | Funciona | Abre la ventana «Nuevo servicio» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Cobros y pagos | Enlace | Funciona | Abre #/admin?tab=payments |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Servicios 7 | Botón | Funciona | Muestra contenido nuevo (9 elementos): «Catálogo y precios Servicios y tarifas Lo que vende tu centro, su precio y sus salidas. + Nuevo servicio 2 servicios no » |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Extras 0 | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Catálogo y precios Servicios y tarifas Lo que vende tu centro, su precio y sus salidas. + Nuevo servicio 2 servicios no » |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Alquiler de equipo 0/8 | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Catálogo y precios Servicios y tarifas Lo que vende tu centro, su precio y sus salidas. + Nuevo servicio 2 servicios no » |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Todos | Botón | Funciona | Muestra contenido nuevo (8 elementos): «Alquiler de equipo completo Alquiler de equipo · 8 h A la venta 25 € tarifa base Cambiar tarifa Bajo petición · el centr» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Alquiler de equipo | Botón | Funciona | Cambia su estado (class: svc-chip  → svc-chip active) · Muestra contenido nuevo (2 elementos): «Alquiler de equipo completo Alquiler de equipo · 8 h A la venta 25 € tarifa base Cambiar tarifa Bajo petición · el centr» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Bautizo / experiencia | Botón | Funciona | Cambia su estado (class: svc-chip  → svc-chip active) · Muestra contenido nuevo (2 elementos): «Bautizo de buceo Bautizo / experiencia · 2 h 30 min A la venta 55 € por persona · desde el Mar, 15 jun: 65 € Cambiar tar» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Curso | Botón | Funciona | Cambia su estado (class: svc-chip  → svc-chip active) · Muestra contenido nuevo (3 elementos): «Curso de Nitrox Curso · 4 h A la venta 160 € por persona Cambiar tarifa Bajo petición · el centro responde en 24 h Hasta» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Inmersión | Botón | Funciona | Cambia su estado (class: svc-chip  → svc-chip active) · Muestra contenido nuevo (4 elementos): «Doble inmersión en barco Inmersión · 4 h A la venta 70 € por persona · desde el Mar, 15 jun: 82 € Cambiar tarifa Bajo pe» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Cambiar tarifa | Botón | Funciona | Abre la ventana «Tarifa» · hay 5 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Alquiler de equipo | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Catálogo y precios Servicios y tarifas Lo que vende tu centro, su precio y sus salidas. + Nuevo servicio 2 servicios no » |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Editar | Botón | Funciona | Abre la ventana «Editar servicio» · hay 5 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Cambiar tarifa | Botón | Funciona | Abre la ventana «Tarifa» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Ver las 16 | Botón | Funciona | Abre la ventana «Salidas de Bautizo de buceo» · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Mié, 14 oct 16:00 6 libres | Botón | Funciona | Abre la ventana «Editar salida» · hay 16 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Jue, 15 oct 16:00 6 libres | Botón | Funciona | Abre la ventana «Editar salida» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | + Salida | Botón | Funciona | Abre la ventana «Nueva salida» · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Agenda | Botón | Funciona | Abre la ventana «Salidas de Bautizo de buceo» · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Editar | Botón | Funciona | Abre la ventana «Editar servicio» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Ver las 3 | Botón | Funciona | Abre la ventana «Salidas de Curso de Nitrox» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | + Salida | Botón | Funciona | Abre la ventana «Nueva salida» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Agenda | Botón | Funciona | Abre la ventana «Salidas de Curso de Nitrox» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | + Nuevo servicio Inmersión, curso, bautizo, viaje… | Botón | Funciona | Abre la ventana «Nuevo servicio» |

#### Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas › Alquiler de equipo 0/ · `#/admin?tab=services` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas › Alquiler de equipo 0/ | Guardar cambios | Botón | Desactivado (correcto) | Desactivado hasta que se cambia algo (botón de guardar) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas › Alquiler de equipo 0/ | Guardar | Botón | Funciona | Aviso: «Precio guardado.» · Muestra contenido nuevo (1 elementos): «Catálogo y precios Servicios y tarifas Lo que vende tu centro, su precio y sus salidas. + Nuevo servicio 2 servicios no » · POST /api/center-equipment → 200 · hay 6 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas › Alquiler de equipo 0/ | Guardar | Botón | Funciona | Aviso: «Precio guardado.» · Muestra contenido nuevo (1 elementos): «Catálogo y precios Servicios y tarifas Lo que vende tu centro, su precio y sus salidas. + Nuevo servicio 2 servicios no » · POST /api/center-equipment → 200 |

#### Bahía Coralina Centro de Buceo · ✈ Experiencias · `#/admin?tab=experiences`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ✈ Experiencias | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ✈ Experiencias | Actualizar | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando experiencias…» |
| Bahía Coralina Centro de Buceo · ✈ Experiencias | + Nueva experiencia | Botón | Funciona | Abre la ventana «Nueva experiencia» |
| Bahía Coralina Centro de Buceo · ✈ Experiencias | Añadir foto | Botón | Funciona | Abre la ventana «Foto de la experiencia» |
| Bahía Coralina Centro de Buceo · ✈ Experiencias | Ver en la web | Enlace | Funciona | Abre #/experiencia?id=7 |
| Bahía Coralina Centro de Buceo · ✈ Experiencias | Editar | Botón | Funciona | Abre la ventana «Editar experiencia» |
| Bahía Coralina Centro de Buceo · ✈ Experiencias | Ocultar | Botón | Funciona | Pide confirmación «¿Ocultar esta experiencia de la web?» (cancelado) |

#### Bahía Coralina Centro de Buceo · ▤ Cobros y pagos · `#/admin?tab=payments`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▤ Cobros y pagos | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ▤ Cobros y pagos | Actualizar | Botón | Funciona | Muestra contenido nuevo (3 elementos): «COBROS Y PAGOS Cobros del centro El cliente paga en una página segura de Stripe y el dinero va directamente a tu cuenta » |
| Bahía Coralina Centro de Buceo · ▤ Cobros y pagos | Abrir mi panel de Stripe | Botón | Depende de clave pendiente | Clave pendiente: Stripe · Aviso: «Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el servidor).» · POST /api/payments/connect/login → 400 «Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el ser» |
| Bahía Coralina Centro de Buceo · ▤ Cobros y pagos | Actualizar estado | Botón | Depende de clave pendiente | Clave pendiente: Stripe · Aviso: «Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el servidor).» · POST /api/payments/connect/sync → 400 «Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el ser» |
| Bahía Coralina Centro de Buceo · ▤ Cobros y pagos | Datos del prestador del servicio | Formulario | Funciona | Enviado vacío · Aviso: «Datos guardados. Saldrán en los justificantes.» · POST /api/provider/payment-profile → 200 |
| Bahía Coralina Centro de Buceo · ▤ Cobros y pagos | Flexible Gratis hasta 24 h antes | Botón | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) · Cambia el texto: «Cancelación gratuita hasta 24 horas antes de la actividad; después no hay reembolso.» · Cambia el valor de «Cancelación gratuita hasta (horas antes)» (48 → 24) |
| Bahía Coralina Centro de Buceo · ▤ Cobros y pagos | Moderada Gratis hasta 48 h antes | Botón | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) · Cambia el texto: «Cancelación gratuita hasta 2 días antes de la actividad; después no hay reembolso.» · Cambia el valor de «Después se devuelve (%)» (50 → 0) |
| Bahía Coralina Centro de Buceo · ▤ Cobros y pagos | Estricta Gratis hasta 7 días antes | Botón | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) · Cambia el texto: «Cancelación gratuita hasta 7 días antes de la actividad; después no hay reembolso.» · Cambia el valor de «Cancelación gratuita hasta (horas antes)» (48 → 168) |
| Bahía Coralina Centro de Buceo · ▤ Cobros y pagos | Guardar política | Botón | Funciona | Aviso: «Política de cancelación guardada. Se aplica a las reservas nuevas.» · POST /api/provider/cancellation-policy → 200 |
| Bahía Coralina Centro de Buceo · ▤ Cobros y pagos | Condiciones para centros | Enlace | Funciona | Abre una pestaña nueva /?lang=es&_=212#/legal/condiciones-centros |

#### Bahía Coralina Centro de Buceo · ◔ Analítica e informes · `#/admin?tab=analytics`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ◔ Analítica e informes | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ◔ Analítica e informes | Actualizar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «ANALÍTICA Informes y rendimiento Datos operativos del centro, calculados a partir de las reservas reales. Exportar CSV I» |
| Bahía Coralina Centro de Buceo · ◔ Analítica e informes | Exportar CSV | Botón | Funciona | Descarga «worldives-informe-centro.csv» |

#### Bahía Coralina Centro de Buceo · ↔ Web e integraciones · `#/admin?tab=integration`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ↔ Web e integraciones | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ↔ Web e integraciones | Actualizar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «CONECTIVIDAD Web, API y sincronización Conecta el motor de reservas de la web del centro para que las reservas entren di» |
| Bahía Coralina Centro de Buceo · ↔ Web e integraciones | Generar API Key | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Guarda esta clave ahora. wod_tgu7UDSr_fg-bre3tBlWZVCpVQGGrPYSLpmQAqnQ8-g Por seguridad WORLDIVES no vuelve a mostrarla c» · POST /api/center/integration/regenerate → 200 |

#### Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo · `#/admin?tab=points`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Actualizar | Botón | Funciona | Muestra contenido nuevo (22 elementos): «CENTRO · PUNTOS Mis puntos de buceo Asocia aquí los lugares a los que suele ir tu centro. No necesitas crear el punto de» |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Nuevo punto | Botón | Funciona | Muestra contenido nuevo (42 elementos): «Gestión / Nuevo punto CATÁLOGO Nuevo punto La posición se puede introducir manualmente o seleccionando una localización » |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Fotos | Botón | Funciona | Abre la ventana «Fotos · Cabo San Antonio» · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Quitar | Botón | Funciona | Pide confirmación «¿Quitar este punto de los puntos habituales del centro?» (cancelado) · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Fotos | Botón | Funciona | Abre la ventana «Fotos · Cabo San Martin / Cueva de la Virgen» |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Quitar | Botón | Funciona | Pide confirmación «¿Quitar este punto de los puntos habituales del centro?» (cancelado) |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Añadir | Botón | Funciona | Aviso: «Punto asociado al centro.» · Muestra contenido nuevo (21 elementos): «CENTRO · PUNTOS Mis puntos de buceo Asocia aquí los lugares a los que suele ir tu centro. No necesitas crear el punto de» · POST /api/center-points/assign → 200 · hay 18 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Añadir | Botón | Funciona | Aviso: «Punto asociado al centro.» · Muestra contenido nuevo (21 elementos): «CENTRO · PUNTOS Mis puntos de buceo Asocia aquí los lugares a los que suele ir tu centro. No necesitas crear el punto de» · POST /api/center-points/assign → 200 |

#### Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina · `#/admin?tab=marina`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina | Actualizar | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando…» |
| Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina | Piedras Rotas | Enlace | Funciona | Abre #/punto?id=332 |
| Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina | Ver el punto | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Piedras Rotas» |
| Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina | Retirar | Botón | Funciona | Pide confirmación «¿Retirar esta propuesta?» (cancelado) |
| Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina | Cabo San Antonio | Botón | Funciona | Cambia su estado (class: mk-point → mk-point is-on) · Muestra contenido nuevo (3 elementos): «Cabo San Antonio» |
| Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina | Cabo San Martin / Cueva de la Virgen | Botón | Funciona | Cambia su estado (class: mk-point → mk-point is-on) · Muestra contenido nuevo (3 elementos): «Cabo San Martin / Cueva de la Virgen» |
| Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina | Galápagos | Botón | Funciona | Cambia su estado (class: mk-point → mk-point is-on) · Muestra contenido nuevo (3 elementos): «Galápagos» |
| Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina | Isla Guadalupe | Botón | Funciona | Cambia su estado (class: mk-point → mk-point is-on) · Muestra contenido nuevo (3 elementos): «Isla Guadalupe» |
| Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina | Montaña Sumergida - Cabo Negro | Botón | Funciona | Cambia su estado (class: mk-point → mk-point is-on) · Muestra contenido nuevo (3 elementos): «Montaña Sumergida - Cabo Negro» |
| Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina | Pared Negra | Botón | Funciona | Cambia su estado (class: mk-point → mk-point is-on) · Muestra contenido nuevo (3 elementos): «Pared Negra» |
| Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina | Piedras Rotas | Botón | Funciona | Cambia su estado (class: mk-point → mk-point is-on) · Muestra contenido nuevo (3 elementos): «Piedras Rotas» |
| Bahía Coralina Centro de Buceo · ◍ Vídeos y vida marina | Portitxol Norte | Botón | Funciona | Cambia su estado (class: mk-point → mk-point is-on) · Muestra contenido nuevo (3 elementos): «Portitxol Norte» |

#### Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones · `#/admin?tab=qr`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Actualizar | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Promociones Validar un código QR de check-in» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Promociones | Botón | Funciona | Muestra contenido nuevo (1 elementos): «FIDELIZACIÓN Promociones con QR Crea una promoción, dásela a clientes de tu base y cada uno recibe en su app un QR perso» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Validar un código | Botón | Funciona | Cambia su estado (class: pr-tab → pr-tab is-on) · Muestra contenido nuevo (1 elementos): «VALIDAR Comprobar un código promocional Escanea el QR del cliente con la cámara del móvil (se abre esta misma comprobaci» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | QR de check-in | Botón | Funciona | Cambia su estado (class: pr-tab → pr-tab is-on) · Muestra contenido nuevo (1 elementos): «IDENTIFICACIÓN DIGITAL Check-in / QR El centro ya está seleccionado automáticamente: Bahía Coralina Centro de Buceo. No » |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Nueva promoción | Botón | Funciona | Abre la ventana «Nueva promoción» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Dar a clientes | Botón | Funciona | Abre la ventana «Dar «Bono 10 inmersiones»» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Ver códigos | Botón | Funciona | Abre la ventana «Códigos de «Bono 10 inmersiones»» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Editar | Botón | Funciona | Abre la ventana «Editar promoción» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Finalizar | Botón | Funciona | Pide confirmación «¿Finalizar la promoción? Sus códigos dejarán de ser válidos.» (cancelado) |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Dar a clientes | Botón | Funciona | Abre la ventana «Dar «10 % en tu próxima inmersión»» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Ver códigos | Botón | Funciona | Abre la ventana «Códigos de «10 % en tu próxima inmersión»» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Editar | Botón | Funciona | Abre la ventana «Editar promoción» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Finalizar | Botón | Funciona | Pide confirmación «¿Finalizar la promoción? Sus códigos dejarán de ser válidos.» (cancelado) |

#### Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › QR de check-in · `#/admin?tab=qr` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › QR de check-in | 🏪 Centro Identificar el centro y hacer check-in | Botón | Funciona | Cambia su estado (class: cb-qr-purpose → cb-qr-purpose active) |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › QR de check-in | 🤿 Buceador Identificar al cliente al llegar | Botón | Funciona | Cambia su estado (class: cb-qr-purpose → cb-qr-purpose active) · Cambia el valor de «Nombre del QR» (Identificación del centro → Check-in del buceador) |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › QR de check-in | 🌊 Inmersión Compartir los datos de una salida con el Log Book | Botón | Funciona | Cambia su estado (class: cb-qr-purpose → cb-qr-purpose active) · Muestra contenido nuevo (78 elementos): «2026-10-14 · 08:00 · Alquiler de equipo completo» · Cambia el valor de «Nombre del QR» (Identificación del centro → Inmersión) |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › QR de check-in | 🎫 Reserva Identificar una reserva concreta | Botón | Funciona | Cambia su estado (class: cb-qr-purpose → cb-qr-purpose active) · Muestra contenido nuevo (150 elementos): «#1236 · 2026-11-09 · Doble inmersión en barco» · Cambia el valor de «Nombre del QR» (Identificación del centro → Reserva) |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › QR de check-in | Check-in / QR | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Nombre del QR» (campo obligatorio) |

#### Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › Validar un código · `#/admin?tab=qr` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › Validar un código | Comprobar un código promocional | Formulario | Funciona | Enviado vacío · Aviso: «Escribe el código completo.» |

#### Bahía Coralina Centro de Buceo · ✦ Escaparate y datos · `#/admin?tab=center`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ✦ Escaparate y datos | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ✦ Escaparate y datos | Actualizar | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Tu página pública Escaparate Así ven tu centro los buceadores. Cambia la portada, las fotos y los textos cuando quieras.» |
| Bahía Coralina Centro de Buceo · ✦ Escaparate y datos | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ✦ Escaparate y datos | Quitar | Botón | Funciona | Pide confirmación «¿Quitar la portada?» (cancelado) |
| Bahía Coralina Centro de Buceo · ✦ Escaparate y datos | Presentación | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Nombre del centro» (campo obligatorio) |
| Bahía Coralina Centro de Buceo · ✦ Escaparate y datos | Idioma | Desplegable | Funciona | Cambia su estado (data-cur: en → fr) · Cambia la pantalla (0 elementos nuevos, 1 quitados) · Cambia el valor de «Frase de presentación» (Boat diving at Cape San Antonio, in Xàbi → Plongée en bateau au cap Saint-Antoine, ) |
| Bahía Coralina Centro de Buceo · ✦ Escaparate y datos | Quitar foto | Botón | Funciona | Pide confirmación «¿Quitar esta foto de la galería?» (cancelado) · hay 2 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ✦ Escaparate y datos | Quitar foto | Botón | Funciona | Pide confirmación «¿Quitar esta foto de la galería?» (cancelado) |

#### Bahía Coralina Centro de Buceo · ★ Recompensas · `#/admin?tab=rewards`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ★ Recompensas | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Actualizar | Botón | Funciona | Muestra contenido nuevo (2 elementos): «PUNTOS WORLDIVES Ventajas y puntos Los buceadores canjean sus puntos por las ventajas que tu centro define y paga. Los p» |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Validar un código | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «WOD-XXXXXXXX» (campo obligatorio) |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Escanear | Botón | Funciona | Aviso: «Este navegador no puede escanear: escribe el código.» |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Conceder puntos | Formulario | Funciona | Enviado vacío · Aviso: «Indica cuántos puntos quieres conceder.» · POST /api/provider/points-grant → 400 «Indica cuántos puntos quieres conceder.» |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Cliente | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Bahía Coralina Centro de Buceo · ★ Recompensas | + Nueva ventaja | Botón | Funciona | Abre la ventana «Nueva ventaja» |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Editar | Botón | Funciona | Abre la ventana «Editar ventaja» |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Editar | Botón | Funciona | Abre la ventana «Editar ventaja» |

#### Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp · `#/admin?tab=avisos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp | Actualizar | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Avisos Avisos a tus clientes y WhatsApp Si cancelas una salida o cambias la hora o el punto de encuentro, avisamos a tod» |
| Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp | Al cancelar una salida, por defecto | Formulario | Funciona | Enviado vacío · Aviso: «Ajustes guardados.» · POST /api/avisos/ajustes → 200 |
| Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp | Hora del recordatorio | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp | Recordatorio del día antes | Botón | Funciona | Abre la ventana «Estado del aviso» |
| Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp | Recordatorio del día antes | Botón | Funciona | Abre la ventana «Estado del aviso» |

#### Bahía Coralina Centro de Buceo · ✉ Solicitudes de información · `#/admin?tab=requests`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ✉ Solicitudes de información | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ✉ Solicitudes de información | Actualizar | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Solicitudes de información Mensajes de buceadores interesados Contesta directamente por email o teléfono. Te llegan tamb» |

#### Bahía Coralina Centro de Buceo · ◑ Estadísticas · `#/admin?tab=stats`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ◑ Estadísticas | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ◑ Estadísticas | Actualizar | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Estadísticas Cómo te encuentran los buceadores Datos agregados, sin datos personales. Disponibles en todos los planes. P» |
| Bahía Coralina Centro de Buceo · ◑ Estadísticas | Periodo Últimos 30 días Últimos 90 días Últimos 365 días | Desplegable | Funciona | Muestra contenido nuevo (1 elementos): «Estadísticas Cómo te encuentran los buceadores Datos agregados, sin datos personales. Disponibles en todos los planes. P» |

#### Bahía Coralina Centro de Buceo · ⇩ Herramientas · `#/admin?tab=tools`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Actualizar | Botón | Funciona | Muestra contenido nuevo (4 elementos): «Herramientas Exportar, calendario, widget e importación Exportar mis datos (CSV) Disponible siempre, en cualquier plan. » |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Clientes | Enlace | Funciona | Descarga /api/center/export?kind=clients (200, text/csv) |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Reservas | Enlace | Funciona | Descarga /api/center/export?kind=bookings (200, text/csv) |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Servicios | Enlace | Funciona | Descarga /api/center/export?kind=services (200, text/csv) |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Agenda | Enlace | Funciona | Descarga /api/center/export?kind=agenda (200, text/csv) |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Pagos | Enlace | Funciona | Descarga /api/center/export?kind=payments (200, text/csv) |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Generar dirección | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Herramientas Exportar, calendario, widget e importación Exportar mis datos (CSV) Disponible siempre, en cualquier plan. » · POST /api/provider/ical/regenerate → 200 |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Copiar | Botón | Funciona | Aviso: «Copiado.» |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Compartir por WhatsApp | Enlace externo | Funciona | Enlace externo a wa.me (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Copiar | Botón | Funciona | Aviso: «Copiado.» |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | plantilla | Enlace | Funciona | Descarga /api/center/import/template (200, text/csv) |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Vista previa | Botón | Funciona | Aviso: «Elige el archivo CSV.» |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Descargo de responsabilidad | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Título» (campo obligatorio) · El navegador no deja enviarlo: «Texto» (campo obligatorio) |

#### Bahía Coralina Centro de Buceo · ☺ Equipo · `#/admin?tab=team`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ☺ Equipo | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ☺ Equipo | Actualizar | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Equipo Personas que gestionan el centro Cada persona tiene un perfil. Abajo puedes cambiar lo que puede hacer cada perfi» |
| Bahía Coralina Centro de Buceo · ☺ Equipo | Perfil de Marta Llorens | Desplegable | Desactivado (correcto) | Desactivado; la pantalla explica: «Solo tú, como propietario, puedes: El equipo y sus perfiles · La cuenta de Stripe y los datos de cobro · Los datos fiscales · El plan · El registro de actividad · Cerrar la cuenta del centro.» |
| Bahía Coralina Centro de Buceo · ☺ Equipo | Perfil de Elena Ribas | Desplegable | Funciona | Aviso: «Perfil cambiado.» · POST /api/center/team/role → 200 |
| Bahía Coralina Centro de Buceo · ☺ Equipo | Quitar | Botón | Funciona | Pide confirmación «Esta persona dejará de tener acceso al centro. ¿Continuar?» (cancelado) |
| Bahía Coralina Centro de Buceo · ☺ Equipo | Perfil de Iván Soler | Desplegable | Funciona | Aviso: «Perfil cambiado.» · POST /api/center/team/role → 200 |
| Bahía Coralina Centro de Buceo · ☺ Equipo | Quitar | Botón | Funciona | Pide confirmación «Esta persona dejará de tener acceso al centro. ¿Continuar?» (cancelado) |
| Bahía Coralina Centro de Buceo · ☺ Equipo | Personas que gestionan el centro | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Email» (campo obligatorio) |
| Bahía Coralina Centro de Buceo · ☺ Equipo | Perfil | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Enviar invitación» (sin efecto inmediato, correcto) |

#### Bahía Coralina Centro de Buceo · ☷ Registro de actividad · `#/admin?tab=activity`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ☷ Registro de actividad | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ☷ Registro de actividad | Actualizar | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Registro de actividad Quién ha hecho qué en el centro FECHA PERSONA ACCIÓN 2026-10-13 22:45 Marta Llorens Perfil del equ» |

#### Bahía Coralina Centro de Buceo · § Datos fiscales y seguro · `#/admin?tab=fiscal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · § Datos fiscales y seguro | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · § Datos fiscales y seguro | Actualizar | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Datos fiscales y verificación Datos del prestador (DAC7) y seguro La normativa europea DAC7 obliga a las plataformas a i» |
| Bahía Coralina Centro de Buceo · § Datos fiscales y seguro | Seguro de responsabilidad civil | Formulario | Funciona | Enviado vacío · Aviso: «Datos guardados.» · Muestra contenido nuevo (1 elementos): «Datos fiscales y verificación Datos del prestador (DAC7) y seguro La normativa europea DAC7 obliga a las plataformas a i» · POST /api/provider/fiscal → 200 |
| Bahía Coralina Centro de Buceo · § Datos fiscales y seguro | Tipo de prestador | Desplegable | Funciona | Cambia hidden en div.field (vacío → sin atributo) |

#### Bahía Coralina Centro de Buceo · ◆ Mi plan · `#/admin?tab=plan`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ◆ Mi plan | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ◆ Mi plan | Actualizar | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Mi plan Pro Activo Activo hasta el 13 de octubre de 2027. Las reservas que ya tienes se atienden siempre y puedes export» |
| Bahía Coralina Centro de Buceo · ◆ Mi plan | Comparar planes | Enlace | Funciona | Abre #/planes |

### Instructor del centro (instructor.prueba)

66 pantallas, 930 elementos probados en 16 min 25 s.

#### Cabecera, pie y elementos flotantes (comunes a todas las pantallas)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Encuentra tu próxima inmersión · flotante | Saltar al contenido | Enlace | Funciona | Desplaza la página · clic por JavaScript (no se puede pulsar con el ratón) |
| Encuentra tu próxima inmersión · cabecera | WORLDIVES DISCOVERY · inicio | Enlace | Funciona | Enlace a la pantalla en la que ya se está |
| Encuentra tu próxima inmersión · cabecera | Explorar | Enlace | Funciona | Abre #/explorar |
| Encuentra tu próxima inmersión · cabecera | Puntos de buceo | Enlace | Funciona | Abre #/puntos |
| Encuentra tu próxima inmersión · cabecera | Centros | Enlace | Funciona | Abre #/centros |
| Encuentra tu próxima inmersión · cabecera | Tipos de buceo | Enlace | Funciona | Abre #/tipos |
| Encuentra tu próxima inmersión · cabecera | Experiencias | Enlace | Funciona | Abre #/experiencias |
| Encuentra tu próxima inmersión · cabecera | Top 10 buceos | Enlace | Funciona | Abre #/top10 |
| Encuentra tu próxima inmersión · cabecera | Seleccionar idioma | Desplegable | Funciona | Recarga la página con /?lang=en · POST /api/account/language → 200 |
| Encuentra tu próxima inmersión · cabecera | IS Iván ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) |
| Encuentra tu próxima inmersión · pie de página | Explorar el mapa | Enlace | Funciona | Mismo enlace (#/explorar) que «Explorar» en «Encuentra tu próxima inmersión»: Abre #/explorar |
| Encuentra tu próxima inmersión · pie de página | Top 10 cerca de ti | Enlace | Funciona | Mismo enlace (#/top10) que «Top 10 buceos» en «Encuentra tu próxima inmersión»: Abre #/top10 |
| Encuentra tu próxima inmersión · pie de página | Centros de buceo | Enlace | Funciona | Mismo enlace (#/centros) que «Centros» en «Encuentra tu próxima inmersión»: Abre #/centros |
| Encuentra tu próxima inmersión · pie de página | Viajes y vida a bordo | Enlace | Funciona | Mismo enlace (#/experiencias) que «Experiencias» en «Encuentra tu próxima inmersión»: Abre #/experiencias |
| Encuentra tu próxima inmersión · pie de página | Mi cuenta | Enlace | Funciona | Abre #/cuenta |
| Encuentra tu próxima inmersión · pie de página | Log Book | Enlace | Funciona | Abre #/logbook |
| Encuentra tu próxima inmersión · pie de página | Recompensas | Enlace | Funciona | Abre #/recompensas |
| Encuentra tu próxima inmersión · pie de página | Mis puntos | Enlace | Funciona | Abre #/mis-puntos |
| Encuentra tu próxima inmersión · pie de página | Dar de alta mi centro | Enlace | Funciona | Abre #/registro |
| Encuentra tu próxima inmersión · pie de página | Panel del centro | Enlace | Funciona | Abre #/admin |
| Encuentra tu próxima inmersión · pie de página | Condiciones para centros | Enlace | Funciona | Abre #/legal/condiciones-centros |
| Encuentra tu próxima inmersión · pie de página | Aviso legal | Enlace | Funciona | Abre #/legal/aviso-legal |
| Encuentra tu próxima inmersión · pie de página | Privacidad | Enlace | Funciona | Abre #/legal/privacidad |
| Encuentra tu próxima inmersión · pie de página | Cookies | Enlace | Funciona | Abre #/legal/cookies |
| Encuentra tu próxima inmersión · pie de página | Condiciones de uso | Enlace | Funciona | Abre #/legal/condiciones-buceadores |
| Encuentra tu próxima inmersión · pie de página | Condiciones de reserva | Enlace | Funciona | Abre #/legal/condiciones-reserva |
| Encuentra tu próxima inmersión · pie de página | Para centros | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Encuentra tu próxima inmersión · pie de página | Denunciar contenido | Enlace | Funciona | Abre #/legal/denuncias |
| Bahía Coralina Centro de Buceo · ⌂ Resumen · flotante | Saltar al contenido | Enlace | Funciona | Desplaza la página · clic por JavaScript (no se puede pulsar con el ratón) |

#### Encuentra tu próxima inmersión · `#/`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Encuentra tu próxima inmersión | Buscar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «⌕ Escribe al menos dos letras El nombre de un punto, una ciudad, una isla o un centro de buceo.» |
| Encuentra tu próxima inmersión | Cerca de mí | Enlace | Funciona | Mismo enlace (#/top10) que «Top 10 buceos» en «Encuentra tu próxima inmersión»: Abre #/top10 |
| Encuentra tu próxima inmersión | Pecios | Enlace | Funciona | Abre #/tipos?t=pecios-y-naufragios |
| Encuentra tu próxima inmersión | Cuevas | Enlace | Funciona | Abre #/tipos?t=cuevas-y-cavernas |
| Encuentra tu próxima inmersión | Arrecifes | Enlace | Funciona | Abre #/tipos?t=arrecifes |
| Encuentra tu próxima inmersión | Centros con reserva online | Enlace | Funciona | Abre #/centros?only=online |
| Encuentra tu próxima inmersión | Abrir el explorador → | Enlace | Funciona | Mismo enlace (#/explorar) que «Explorar» en «Encuentra tu próxima inmersión»: Abre #/explorar |
| Encuentra tu próxima inmersión | 01 Europa 108 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (32 elementos): «4» |
| Encuentra tu próxima inmersión | 02 Asia 104 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (26 elementos): «15» |
| Encuentra tu próxima inmersión | 03 América 24 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (25 elementos): «3» |
| Encuentra tu próxima inmersión | 04 África y Mar Rojo 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (34 elementos): «2» |
| Encuentra tu próxima inmersión | 05 Oceanía 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (11 elementos): «2» |
| Encuentra tu próxima inmersión | 06 Caribe 17 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (27 elementos): «8» |
| Encuentra tu próxima inmersión | Mapa | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| Encuentra tu próxima inmersión | Satélite Disponible próximamente | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Encuentra tu próxima inmersión | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (18 elementos): «Leaflet» |
| Encuentra tu próxima inmersión | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (19 elementos): «2» · hay 15 más iguales en la lista (no se prueban todos) |
| Encuentra tu próxima inmersión | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (7 elementos): «Rainbow Reef» |
| Encuentra tu próxima inmersión | Mauritius – Cathedral | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (145 elementos): «×» · hay 1 más iguales en la lista (no se prueban todos) |
| Encuentra tu próxima inmersión | Tofo – Manta Reef | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» |
| Encuentra tu próxima inmersión | Zoom in | Enlace | Funciona | Muestra contenido nuevo (64 elementos): «2» |
| Encuentra tu próxima inmersión | Zoom out | Enlace | Funciona | Cambia su estado (class: leaflet-control-zoom-out → leaflet-control-zoom-out leaflet-disabled) · Cambia la pantalla (4 elementos nuevos, 0 quitados) |
| Encuentra tu próxima inmersión | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Encuentra tu próxima inmersión | OpenStreetMap contributors | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Encuentra tu próxima inmersión | Ver todos los tipos → | Enlace | Funciona | Mismo enlace (#/tipos) que «Tipos de buceo» en «Encuentra tu próxima inmersión»: Abre #/tipos |
| Encuentra tu próxima inmersión | Aguas profundas | Enlace | Funciona | Abre #/tipos?t=aguas-profundas |
| Encuentra tu próxima inmersión | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| Encuentra tu próxima inmersión | Paredes | Enlace | Funciona | Abre #/tipos?t=paredes |
| Encuentra tu próxima inmersión | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| Encuentra tu próxima inmersión | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| Encuentra tu próxima inmersión | Pináculos | Enlace | Funciona | Abre #/tipos?t=pinaculos |

#### El mapa del buceo · `#/explorar`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| El mapa del buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| El mapa del buceo | Todos | Botón | Funciona | Muestra contenido nuevo (36 elementos): «2» |
| El mapa del buceo | Arrecifes | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (58 elementos): «2» |
| El mapa del buceo | Paredes | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (45 elementos): «2» |
| El mapa del buceo | Pecios | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (32 elementos): «2» |
| El mapa del buceo | Cuevas | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (32 elementos): «3» |
| El mapa del buceo | Muck | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (30 elementos): «3» |
| El mapa del buceo | Pináculos | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (27 elementos): «7» |
| El mapa del buceo | Profundas | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (59 elementos): «2» |
| El mapa del buceo | 01 Europa 108 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (40 elementos): «2» |
| El mapa del buceo | 02 Asia 104 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (22 elementos): «2» |
| El mapa del buceo | 03 América 24 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (15 elementos): «2» |
| El mapa del buceo | 04 África y Mar Rojo 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (25 elementos): «2» |
| El mapa del buceo | 05 Oceanía 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (31 elementos): «2» |
| El mapa del buceo | 06 Caribe 17 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (32 elementos): «2» |
| El mapa del buceo | Mapa | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (26 elementos): «Leaflet» |
| El mapa del buceo | Satélite Disponible próximamente | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| El mapa del buceo | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (26 elementos): «Leaflet» |
| El mapa del buceo | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (31 elementos): «2» · clic forzado (otro elemento lo tapa) · hay 29 más iguales en la lista (no se prueban todos) |
| El mapa del buceo | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (14 elementos): «Rainbow Reef» |
| El mapa del buceo | Mauritius – Cathedral | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» · hay 3 más iguales en la lista (no se prueban todos) |
| El mapa del buceo | Tofo – Manta Reef | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» |
| El mapa del buceo | Seguridad en el buceo | Enlace | Funciona | Abre #/legal/seguridad |
| El mapa del buceo | Zoom in | Enlace | Funciona | Muestra contenido nuevo (87 elementos): «2» |
| El mapa del buceo | Zoom out | Enlace | Funciona | Cambia la pantalla (10 elementos nuevos, 0 quitados) |
| El mapa del buceo | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |

#### Puntos de buceo · `#/puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Puntos de buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Puntos de buceo | Puntos de buceo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (68 elementos): «Todo el mundo» |
| Puntos de buceo | Zona Todo el mundo Europa (108) Asia (104) América (24) África y Mar Rojo (20) Oceanía (20) Caribe (17) | Desplegable | Funciona | Abre #/puntos?zone=Europa |
| Puntos de buceo | Para empezar | Botón | Funciona | Abre #/puntos?level=start |
| Puntos de buceo | Intermedio | Botón | Funciona | Abre #/puntos?level=mid |
| Puntos de buceo | Avanzado | Botón | Funciona | Abre #/puntos?level=adv |
| Puntos de buceo | Con centro que lo ofrece | Botón | Funciona | Abre #/puntos?only=centers |
| Puntos de buceo | Confirmación inmediata | Botón | Funciona | Abre #/puntos?only=instant |
| Puntos de buceo | Tipo de buceo Cualquier tipo Arrecifes Paredes Pecios y naufragios Cuevas y cavernas Cenotes Muck Canales Caño | Desplegable | Funciona | Abre #/puntos?type=arrecifes |
| Puntos de buceo | País Todos los países España (93) Filipinas (30) Indonesia (25) Malasia (15) Maldivas (13) Tailandia (13) Egip | Desplegable | Funciona | Abre #/puntos?country=Espa%C3%B1a |
| Puntos de buceo | Ordenar Recomendados Nombre A-Z Más profundos Menos profundos Mejor valorados | Desplegable | Funciona | Abre #/puntos?sort=name |
| Puntos de buceo | ¿Cómo ordenamos? | Enlace | Funciona | Abre #/legal/clasificacion |
| Puntos de buceo | #/punto?id=34 | Enlace | Funciona | Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Blue Hole, Dahab | Enlace | Funciona | Mismo enlace (#/punto?id=34) que «#/punto?id=34» en «Puntos de buceo»: Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Ver punto | Enlace | Funciona | Mismo enlace (#/punto?id=34) que «#/punto?id=34» en «Puntos de buceo»: Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Mostrar más puntos (281) | Botón | Funciona | Cambia su estado (disabled: sin atributo → vacío) · Muestra contenido nuevo (13 elementos): «Arrecifes Paredes Portitxol Norte Marina Alta · Xàbia · España Moderado Arrecife · Pared · Fondo arenoso Ubicación por v» |

#### Centros de buceo · `#/centros`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centros de buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Centros de buceo | Centros de buceo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (11 elementos): «Todos los países» |
| Centros de buceo | País Todos los países España (2) | Desplegable | Funciona | Abre #/centros?country=Espa%C3%B1a |
| Centros de buceo | Confirmación inmediata | Botón | Funciona | Abre #/centros?only=instant |
| Centros de buceo | Reserva online | Botón | Funciona | Abre #/centros?only=online |
| Centros de buceo | Plazas esta semana | Botón | Funciona | Abre #/centros?only=week |
| Centros de buceo | Cursos | Botón | Funciona | Abre #/centros?only=courses |
| Centros de buceo | Bautizos | Botón | Funciona | Abre #/centros?only=try |
| Centros de buceo | Viajes | Botón | Funciona | Abre #/centros?only=trips |
| Centros de buceo | Con reseñas | Botón | Funciona | Abre #/centros?only=reviews |
| Centros de buceo | Tipo de buceo Cualquier tipo de buceo Arrecifes Paredes Pecios y naufragios Cuevas y cavernas Cenotes Muck Can | Desplegable | Funciona | Abre #/centros?type=arrecifes |
| Centros de buceo | Ordenar Recomendados Mejor valorados Más reseñas Precio más bajo Nombre A-Z | Desplegable | Funciona | Abre #/centros?sort=rating |
| Centros de buceo | ¿Cómo ordenamos? | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Centros de buceo | Bajo petición Plazas esta semana | Enlace | Funciona | Abre #/centro?id=31 |
| Centros de buceo | Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Centros de buceo | Reservar | Enlace | Funciona | Abre #/reservar?center=31 |
| Centros de buceo | Bajo petición Plazas esta semana | Enlace | Funciona | Abre #/centro?id=32 |
| Centros de buceo | Escafandra Medes | Enlace | Funciona | Mismo enlace (#/centro?id=32) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=32 |
| Centros de buceo | Reservar | Enlace | Funciona | Abre #/reservar?center=32 |
| Centros de buceo | Dar de alta mi centro | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### ¿Qué inmersión te apetece? · `#/tipos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| ¿Qué inmersión te apetece? | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| ¿Qué inmersión te apetece? | Todos | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| ¿Qué inmersión te apetece? | Para empezar | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Con experiencia | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Avanzado y técnico | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| ¿Qué inmersión te apetece? | Paredes | Enlace | Funciona | Mismo enlace (#/tipos?t=paredes) que «Paredes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=paredes |
| ¿Qué inmersión te apetece? | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| ¿Qué inmersión te apetece? | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| ¿Qué inmersión te apetece? | Cenotes | Enlace | Funciona | Abre #/tipos?t=cenotes |
| ¿Qué inmersión te apetece? | Muck | Enlace | Funciona | Abre #/tipos?t=muck |
| ¿Qué inmersión te apetece? | Canales | Enlace | Funciona | Abre #/tipos?t=canales |
| ¿Qué inmersión te apetece? | Cañones | Enlace | Funciona | Abre #/tipos?t=canones |
| ¿Qué inmersión te apetece? | Pináculos | Enlace | Funciona | Mismo enlace (#/tipos?t=pinaculos) que «Pináculos» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pinaculos |
| ¿Qué inmersión te apetece? | Corrientes y deriva | Enlace | Funciona | Abre #/tipos?t=corrientes-y-deriva |
| ¿Qué inmersión te apetece? | Aguas profundas | Enlace | Funciona | Mismo enlace (#/tipos?t=aguas-profundas) que «Aguas profundas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=aguas-profundas |
| ¿Qué inmersión te apetece? | Lagos | Enlace | Funciona | Abre #/tipos?t=lagos |
| ¿Qué inmersión te apetece? | Pilares | Enlace | Funciona | Abre #/tipos?t=pilares |
| ¿Qué inmersión te apetece? | Nocturnas | Enlace | Funciona | Abre #/tipos?t=nocturnas |
| ¿Qué inmersión te apetece? | Playa y esnórquel | Enlace | Funciona | Abre #/tipos?t=playa-y-esnorquel |
| ¿Qué inmersión te apetece? | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| ¿Qué inmersión te apetece? | Muck | Enlace | Funciona | Mismo enlace (#/tipos?t=muck) que «Muck» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=muck |
| ¿Qué inmersión te apetece? | Lagos | Enlace | Funciona | Mismo enlace (#/tipos?t=lagos) que «Lagos» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=lagos |
| ¿Qué inmersión te apetece? | Pilares | Enlace | Funciona | Mismo enlace (#/tipos?t=pilares) que «Pilares» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=pilares |
| ¿Qué inmersión te apetece? | Paredes | Enlace | Funciona | Mismo enlace (#/tipos?t=paredes) que «Paredes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=paredes |
| ¿Qué inmersión te apetece? | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| ¿Qué inmersión te apetece? | Canales | Enlace | Funciona | Mismo enlace (#/tipos?t=canales) que «Canales» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=canales |
| ¿Qué inmersión te apetece? | Pináculos | Enlace | Funciona | Mismo enlace (#/tipos?t=pinaculos) que «Pináculos» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pinaculos |
| ¿Qué inmersión te apetece? | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| ¿Qué inmersión te apetece? | Cenotes | Enlace | Funciona | Mismo enlace (#/tipos?t=cenotes) que «Cenotes» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=cenotes |
| ¿Qué inmersión te apetece? | Cañones | Enlace | Funciona | Mismo enlace (#/tipos?t=canones) que «Cañones» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=canones |
| ¿Qué inmersión te apetece? | Corrientes y deriva | Enlace | Funciona | Mismo enlace (#/tipos?t=corrientes-y-deriva) que «Corrientes y deriva» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=corrientes-y-deriva |
| ¿Qué inmersión te apetece? | Aguas profundas | Enlace | Funciona | Mismo enlace (#/tipos?t=aguas-profundas) que «Aguas profundas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=aguas-profundas |

#### Viajes y vida a bordo · `#/experiencias`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Viajes y vida a bordo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Viajes y vida a bordo | Viajes y vida a bordo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (16 elementos): «Viaje 1 experiencia Costa Blanca España Experiencias de buceo organizadas por centros y profesionales. DESDE 290 € PRÓXI» |
| Viajes y vida a bordo | Todas | Botón | Funciona | Muestra contenido nuevo (8 elementos): «Viaje 1 experiencia Costa Blanca España Experiencias de buceo organizadas por centros y profesionales. DESDE 290 € PRÓXI» |
| Viajes y vida a bordo | Viaje | Botón | Funciona | Abre #/experiencias?kind=Viaje |
| Viajes y vida a bordo | Vida a bordo | Botón | Funciona | Abre #/experiencias?kind=Vida+a+bordo |
| Viajes y vida a bordo | Ordenar Con más salidas Precio más bajo Próxima salida Nombre A-Z | Desplegable | Funciona | Abre #/experiencias?sort=price |
| Viajes y vida a bordo | Viaje 1 experiencia | Enlace | Funciona | Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Costa Blanca | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Ver viajes | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Ver destino | Enlace | Funciona | Abre #/experiencia?id=5 · hay 3 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Empezar a publicar | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### ¿Te apetece bucear? · `#/top10`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| ¿Te apetece bucear? | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| ¿Te apetece bucear? | Radio 25 km 50 km 100 km 250 km 500 km | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Buscar» (sin efecto inmediato, correcto) |
| ¿Te apetece bucear? | Usar mi ubicación | Botón | Funciona | Muestra contenido nuevo (13 elementos): «1 ARRECIFES Cabo San Antonio Marina Alta · Xàbia · España 7–20 m Moderado ★ 4.4 (9) 1 centro 1,9 km Ver inmersión» |
| ¿Te apetece bucear? | Elegir en el mapa | Botón | Funciona | Abre la ventana «Elige tu ubicación» |
| ¿Te apetece bucear? | ¿Te apetece bucear? | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Buscar una localidad» (campo obligatorio) |
| ¿Te apetece bucear? | Marina Alta · Xàbia | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 ARRECIFES Piedras Rotas Marina Alta · Xàbia · España 7–20 m Fácil ★ 4.4 (9) 1 centro 0,8 km Ver inmersión» |
| ¿Te apetece bucear? | Marina Alta y Baixa · Calpe | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 19,3 km Ver inmersión» |
| ¿Te apetece bucear? | Canarias | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (9 elementos): «1 ARRECIFES Las Canteras, Gran Canaria Canarias · España Iniciación 48,3 km Ver inmersión» |
| ¿Te apetece bucear? | Palawan | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (4 elementos): «1 ARRECIFES El Nido – Cadlao Lagoon Palawan · Filipinas 5–20 m Principiante 72,9 km Ver inmersión» |
| ¿Te apetece bucear? | Comunitat Valenciana | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 25,7 km Ver inmersión» |
| ¿Te apetece bucear? | Andalucía | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (6 elementos): «1 ARRECIFES Costa del Sol, Málaga Andalucía · España Iniciación 52,4 km Ver inmersión» |
| ¿Te apetece bucear? | Marina Alta · Moraira | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 9,7 km Ver inmersión» |
| ¿Te apetece bucear? | Cebu | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (12 elementos): «1 ARRECIFES Moalboal – Sardine Run Cebu · Filipinas 5–25 m Principiante 28,1 km Ver inmersión» |
| ¿Te apetece bucear? | Cataluña | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (12 elementos): «1 ARRECIFES Medes – Tascons Islas Medes · España 6–25 m Intermedio ★ 4.8 (6) 1 centro 2,1 km Ver inmersión» |
| ¿Te apetece bucear? | Illes Balears | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (8 elementos): «1 PAREDES El Toro Mallorca · España 10–35 m Intermedio 12,9 km Ver inmersión» |

#### Planes de WORLDIVES · `#/planes`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Planes de WORLDIVES | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Planes de WORLDIVES | Gestionar mi plan | Enlace | Funciona | Abre #/admin?tab=plan · GET /api/provider/plan → 403 «Solo el propietario del centro puede hacer esto.» |

#### Cómo funcionan los puntos · `#/como-funcionan-los-puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Cómo funcionan los puntos | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Cómo funcionan los puntos | Ver mis puntos | Enlace | Funciona | Mismo enlace (#/mis-puntos) que «Mis puntos» en «Encuentra tu próxima inmersión»: Abre #/mis-puntos |
| Cómo funcionan los puntos | Ver ventajas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Recompensas» en «Encuentra tu próxima inmersión»: Abre #/recompensas |

#### Aviso legal · `#/legal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Aviso legal | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Aviso legal | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Aviso legal | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Abre #/legal/reservas |
| Aviso legal | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Aviso legal | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Aviso legal | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Aviso legal | Normas de las reseñas | Enlace | Funciona | Abre #/legal/normas-resenas |
| Aviso legal | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Puntos WORLDIVES | Enlace | Funciona | Abre #/legal/puntos |
| Aviso legal | Declaración de accesibilidad | Enlace | Funciona | Abre #/legal/accesibilidad |
| Aviso legal | Contacto | Enlace | Funciona | Abre #/legal/contacto |
| Aviso legal | Créditos y licencias de terceros | Enlace | Funciona | Abre #/legal/creditos |
| Aviso legal | Condiciones de uso | Enlace | Funciona | Abre #/legal/terminos |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Leer | Botón | Funciona | Abre la ventana «Aviso legal» |
| Aviso legal | 1. Titular del sitio web | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 6 más iguales en la lista (no se prueban todos) |
| Aviso legal | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Crear cuenta · `#/registro`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Crear cuenta | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Crear cuenta | Buceador | Enlace | Funciona | Abre #/registro?tipo=recreational |
| Crear cuenta | Centro de buceo Publica tus salidas y cursos y gestiona tus reservas. | Enlace | Funciona | Abre #/registro?tipo=center |
| Crear cuenta | Profesional | Enlace | Funciona | Abre #/registro?tipo=freelance |
| Crear cuenta | Iniciar sesión | Enlace | Funciona | Abre #/cuenta |

#### Condiciones para centros y profesionales · `#/legal/condiciones-centros`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones para centros y profesionales | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones para centros y profesionales | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones para centros y profesionales | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones para centros y profesionales | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones para centros y profesionales | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones para centros y profesionales | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones para centros y profesionales | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones para centros y profesionales | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones para centros y profesionales | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones para centros y profesionales | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones para centros y profesionales | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones para centros y profesionales | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones para centros y profesionales | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones para centros y profesionales | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones para centros y profesionales | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones para centros y profesionales | Planes | Enlace | Funciona | Abre #/planes |
| Condiciones para centros y profesionales | Planes | Enlace | Funciona | Mismo enlace (#/planes) que «Planes» en «Condiciones para centros y profesionales»: Abre #/planes |
| Condiciones para centros y profesionales | normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones para centros y profesionales | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones para centros y profesionales | Leer | Botón | Funciona | Abre la ventana «Condiciones para centros y profesionales» |
| Condiciones para centros y profesionales | 1. Alta y verificación | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 18 más iguales en la lista (no se prueban todos) |
| Condiciones para centros y profesionales | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones para centros y profesionales | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Aviso legal · `#/legal/aviso-legal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Aviso legal | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Aviso legal | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Aviso legal | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Aviso legal | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Aviso legal | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Aviso legal | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Aviso legal | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Aviso legal | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Aviso legal | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Aviso legal | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Aviso legal | Condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/terminos) que «Condiciones de uso» en «Aviso legal»: Abre #/legal/terminos |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Leer | Botón | Funciona | Abre la ventana «Aviso legal» |
| Aviso legal | 1. Titular del sitio web | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 6 más iguales en la lista (no se prueban todos) |
| Aviso legal | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Política de privacidad · `#/legal/privacidad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Política de privacidad | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Política de privacidad | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Política de privacidad | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Política de privacidad | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Política de privacidad | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Política de privacidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de privacidad | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Política de privacidad | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Política de privacidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de privacidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Política de privacidad | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Política de privacidad | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Política de privacidad | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Política de privacidad | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Política de privacidad | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Política de privacidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de privacidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de privacidad | www.aepd.es | Enlace externo | Funciona | Enlace externo a www.aepd.es (no se abre: dirección https válida) |
| Política de privacidad | Leer | Botón | Funciona | Abre la ventana «Política de privacidad» |
| Política de privacidad | 1. Responsable | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 8 más iguales en la lista (no se prueban todos) |
| Política de privacidad | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Política de privacidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Política de cookies y servicios de terceros · `#/legal/cookies`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Política de cookies y servicios de terceros | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Política de cookies y servicios de terceros | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Política de cookies y servicios de terceros | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Política de cookies y servicios de terceros | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Política de cookies y servicios de terceros | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Política de cookies y servicios de terceros | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de cookies y servicios de terceros | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Política de cookies y servicios de terceros | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Política de cookies y servicios de terceros | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de cookies y servicios de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Política de cookies y servicios de terceros | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Política de cookies y servicios de terceros | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Política de cookies y servicios de terceros | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Política de cookies y servicios de terceros | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Política de cookies y servicios de terceros | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Política de cookies y servicios de terceros | Leer | Botón | Funciona | Abre la ventana «Política de cookies y servicios de terceros» |
| Política de cookies y servicios de terceros | Qué usamos | Enlace | Funciona | Cambia tabindex en h2#que-usamos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Política de cookies y servicios de terceros | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Política de cookies y servicios de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de uso para buceadores · `#/legal/condiciones-buceadores`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de uso para buceadores | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de uso para buceadores | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de uso para buceadores | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de uso para buceadores | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de uso para buceadores | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Leer | Botón | Funciona | Abre la ventana «Condiciones de uso para buceadores» |
| Condiciones de uso para buceadores | 1. Qué es WORLDIVES DISCOVERY | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 9 más iguales en la lista (no se prueban todos) |
| Condiciones de uso para buceadores | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de reserva, pago y cancelación · `#/legal/condiciones-reserva`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de reserva, pago y cancelación | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de reserva, pago y cancelación | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de reserva, pago y cancelación | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de reserva, pago y cancelación | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de reserva, pago y cancelación | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de reserva, pago y cancelación | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de reserva, pago y cancelación | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de reserva, pago y cancelación | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de reserva, pago y cancelación | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de reserva, pago y cancelación | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Leer | Botón | Funciona | Abre la ventana «Condiciones de reserva, pago y cancelación» |
| Condiciones de reserva, pago y cancelación | 1. Quién presta la actividad | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 7 más iguales en la lista (no se prueban todos) |
| Condiciones de reserva, pago y cancelación | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Denunciar contenido · `#/legal/denuncias`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Denunciar contenido | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Denunciar contenido | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Denunciar contenido | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Denunciar contenido | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Denunciar contenido | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Denunciar contenido | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Denunciar contenido | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Denunciar contenido | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Denunciar contenido | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Denunciar contenido | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Denunciar contenido | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Denunciar contenido | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Denunciar contenido | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Denunciar contenido | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Denunciar contenido | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Denunciar contenido | Formulario de denuncia | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Motivo» (elige una opción de la lista) · El navegador no deja enviarlo: «Explica por qué es ilegal o incumple las condiciones» (campo obligatorio) |
| Denunciar contenido | Motivo | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Enviar denuncia» (sin efecto inmediato, correcto) |
| Denunciar contenido | Leer | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Denunciar contenido | Qué necesitamos | Enlace | Funciona | Cambia tabindex en h2#que-necesitamos (sin atributo → -1) · hay 2 más iguales en la lista (no se prueban todos) |
| Denunciar contenido | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Denunciar contenido | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Seguridad en el buceo · `#/legal/seguridad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Seguridad en el buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Seguridad en el buceo | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Seguridad en el buceo | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Seguridad en el buceo | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Seguridad en el buceo | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Seguridad en el buceo | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Seguridad en el buceo | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Seguridad en el buceo | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Seguridad en el buceo | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Seguridad en el buceo | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Seguridad en el buceo | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Seguridad en el buceo | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Seguridad en el buceo | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Seguridad en el buceo | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Seguridad en el buceo | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Seguridad en el buceo | Leer | Botón | Funciona | Abre la ventana «Seguridad en el buceo» |
| Seguridad en el buceo | Antes de reservar | Enlace | Funciona | Cambia tabindex en h2#antes-de-reservar (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Seguridad en el buceo | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Seguridad en el buceo | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Cómo ordenamos los resultados · `#/legal/clasificacion`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Cómo ordenamos los resultados | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Cómo ordenamos los resultados | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Cómo ordenamos los resultados | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Cómo ordenamos los resultados | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Cómo ordenamos los resultados | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Cómo ordenamos los resultados | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Cómo ordenamos los resultados | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Cómo ordenamos los resultados | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Cómo ordenamos los resultados | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Cómo ordenamos los resultados | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Cómo ordenamos los resultados | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Cómo ordenamos los resultados | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Cómo ordenamos los resultados | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Cómo ordenamos los resultados | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Cómo ordenamos los resultados | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Cómo ordenamos los resultados | Leer | Botón | Funciona | Abre la ventana «Cómo ordenamos los resultados» |
| Cómo ordenamos los resultados | Directorio de centros | Enlace | Funciona | Cambia tabindex en h2#directorio-de-centros (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Cómo ordenamos los resultados | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Cómo ordenamos los resultados | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Blue Hole, Dahab · `#/punto?id=34`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Blue Hole, Dahab | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Blue Hole, Dahab | Puntos de buceo | Enlace | Funciona | Mismo enlace (#/puntos) que «Puntos de buceo» en «Encuentra tu próxima inmersión»: Abre #/puntos |
| Blue Hole, Dahab | África y Mar Rojo | Enlace | Funciona | Abre #/puntos?zone=%C3%81frica+y+Mar+Rojo |
| Blue Hole, Dahab | Abrir en el mapa | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Blue Hole, Dahab | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Encuentra tu próxima inmersión»: Abre #/cuenta |
| Blue Hole, Dahab | ¿Tienes un centro? Únete a WORLDIVES | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |
| Blue Hole, Dahab | Blue Hole Dahab Dahab · Egipto 6–60 m · Avanzado a 0 km | Enlace | Funciona | Abre #/punto?id=247 |
| Blue Hole, Dahab | Canyon Dahab Dahab · Egipto 8–30 m · Intermedio a 2,9 km | Enlace | Funciona | Abre #/punto?id=248 |
| Blue Hole, Dahab | Blue Hole, Dahab | Elemento div (role=button) | Funciona | Mueve o amplía el mapa |
| Blue Hole, Dahab | Mapa | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (8 elementos): «Leaflet» |
| Blue Hole, Dahab | Satélite | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Relieve orientativo (GEBCO). No sirve para navegar ni para la seguridad en el mar. Seguridad en el buceo» |
| Blue Hole, Dahab | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (10 elementos): «Leaflet» |
| Blue Hole, Dahab | Zoom in | Enlace | Funciona | Cambia la pantalla (5 elementos nuevos, 2 quitados) |
| Blue Hole, Dahab | Zoom out | Enlace | Funciona | Cambia la pantalla (5 elementos nuevos, 2 quitados) |
| Blue Hole, Dahab | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Blue Hole, Dahab | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Blue Hole, Dahab | Abrir en OpenStreetMap | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Blue Hole, Dahab | Proponer nueva posición | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Latitud Longitud Motivo» |
| Blue Hole, Dahab | Denunciar contenido | Botón | Funciona | Abre la ventana «Denunciar contenido» |

#### Bahía Coralina Centro de Buceo · `#/centro?id=31`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | Centros | Enlace | Funciona | Mismo enlace (#/centros) que «Centros» en «Encuentra tu próxima inmersión»: Abre #/centros |
| Bahía Coralina Centro de Buceo | Reservar | Enlace | Funciona | Mismo enlace (#/reservar?center=31) que «Reservar» en «Centros de buceo»: Abre #/reservar?center=31 |
| Bahía Coralina Centro de Buceo | Llamar | Enlace externo | Funciona | Teléfono +34600000101 |
| Bahía Coralina Centro de Buceo | Escribir | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | Lun, 19 oct 10:00 6 plazas | Enlace | Funciona | Abre #/reservar?center=31&service=7&slot=22 · POST /api/stats/track → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · hay 11 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Enviar solicitud | Enlace | Funciona | Abre #/reservar?center=31&service=7 · POST /api/stats/track → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · hay 3 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Añadir a una reserva | Enlace | Funciona | Abre #/reservar?center=31&service=8 · POST /api/stats/track → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» |
| Bahía Coralina Centro de Buceo | Tres días en la reserva del Cabo de San Antonio | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Foto 1 de Bahía Coralina Centro de Buceo | Botón | Funciona | Abre la ventana «Bahía Coralina Centro de Buceo» · hay 2 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Foto 2 de Bahía Coralina Centro de Buceo | Botón | Funciona | Abre la ventana «Bahía Coralina Centro de Buceo» |
| Bahía Coralina Centro de Buceo | Responder | Botón | Funciona | Abre la ventana «Responder a la reseña» · hay 1 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» · hay 7 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Editar respuesta | Botón | Funciona | Abre la ventana «Responder a la reseña» · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Bahía Coralina Centro de Buceo | Editar respuesta | Botón | Funciona | Abre la ventana «Responder a la reseña» |
| Bahía Coralina Centro de Buceo | Responder | Botón | Funciona | Abre la ventana «Responder a la reseña» |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34600000101 |
| Bahía Coralina Centro de Buceo | hola@bahiacoralina.example.com | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | bahiacoralina.example.com | Enlace externo | Funciona | Enlace externo a bahiacoralina.example.com (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo | Ver en el mapa | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo | Reservar con Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/reservar?center=31) que «Reservar» en «Centros de buceo»: Abre #/reservar?center=31 |
| Bahía Coralina Centro de Buceo | Denunciar contenido | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Bahía Coralina Centro de Buceo | Cabo San Antonio | Enlace | Funciona | Abre #/punto?id=329 · hay 5 más iguales en la lista (no se prueban todos) |

#### Bahía Coralina Centro de Buceo · `#/reservar?center=31`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | ← Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | Bautizo de buceo | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «No admite reservas ahora mismo» |
| Bahía Coralina Centro de Buceo | Curso Open Water (3 días) | Botón | Funciona | Muestra contenido nuevo (14 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Curso de Nitrox | Botón | Funciona | Muestra contenido nuevo (13 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Doble inmersión en barco | Botón | Funciona | Muestra contenido nuevo (26 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Inmersión al atardecer | Botón | Funciona | Muestra contenido nuevo (17 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Inmersión simple en barco | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «No admite reservas ahora mismo» |
| Bahía Coralina Centro de Buceo | Una persona menos | Botón | Desactivado (correcto) | Desactivado: es el límite del calendario o de la lista («Una persona menos») |
| Bahía Coralina Centro de Buceo | Una persona más | Botón | Desactivado (correcto) | No responde al ratón (pointer-events: none) y se ve atenuado; la pantalla explica: «Elige primero la actividad.» |
| Bahía Coralina Centro de Buceo | Elige una actividad | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Política de cancelación. Moderada: cancelación gratuita hasta 48 horas antes de la actividad; después no hay reembolso.» |
| Bahía Coralina Centro de Buceo | condiciones de reserva | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Bahía Coralina Centro de Buceo | condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34600000101 |

#### Costa Blanca · `#/experiencia?id=7`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Costa Blanca | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Costa Blanca | Experiencias | Enlace | Funciona | Mismo enlace (#/experiencias) que «Experiencias» en «Encuentra tu próxima inmersión»: Abre #/experiencias |
| Costa Blanca | BAHÍA CORALINA CENTRO DE BUCEO | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Costa Blanca | Solicitar plaza | Botón | Funciona | Abre #/experienciareserva?id=2 |
| Costa Blanca | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Costa Blanca | Publicar un viaje | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### Condiciones de reserva, pago y cancelación · `#/legal/reservas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de reserva, pago y cancelación | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de reserva, pago y cancelación | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de reserva, pago y cancelación | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de reserva, pago y cancelación | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de reserva, pago y cancelación | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de reserva, pago y cancelación | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de reserva, pago y cancelación | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de reserva, pago y cancelación | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de reserva, pago y cancelación | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de reserva, pago y cancelación | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Leer | Botón | Funciona | Abre la ventana «Condiciones de reserva, pago y cancelación» |
| Condiciones de reserva, pago y cancelación | 1. Quién presta la actividad | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 7 más iguales en la lista (no se prueban todos) |
| Condiciones de reserva, pago y cancelación | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Normas de las reseñas · `#/legal/normas-resenas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Normas de las reseñas | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Normas de las reseñas | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Normas de las reseñas | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Normas de las reseñas | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Normas de las reseñas | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Normas de las reseñas | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Normas de las reseñas | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Normas de las reseñas | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Normas de las reseñas | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Normas de las reseñas | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Normas de las reseñas | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Normas de las reseñas | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Normas de las reseñas | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Normas de las reseñas | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Normas de las reseñas | Leer | Botón | Funciona | Abre la ventana «Normas de las reseñas» |
| Normas de las reseñas | Quién puede escribir una reseña | Enlace | Funciona | Cambia tabindex en h2#quien-puede-escribir-una-resena (sin atributo → -1) · hay 4 más iguales en la lista (no se prueban todos) |
| Normas de las reseñas | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Puntos WORLDIVES · `#/legal/puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Puntos WORLDIVES | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Puntos WORLDIVES | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Puntos WORLDIVES | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Puntos WORLDIVES | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Puntos WORLDIVES | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Puntos WORLDIVES | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Puntos WORLDIVES | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Puntos WORLDIVES | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Puntos WORLDIVES | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Puntos WORLDIVES | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Puntos WORLDIVES | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Puntos WORLDIVES | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Puntos WORLDIVES | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Puntos WORLDIVES | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Puntos WORLDIVES | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Puntos WORLDIVES | Condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Puntos WORLDIVES | Leer | Botón | Funciona | Abre la ventana «Puntos WORLDIVES» |
| Puntos WORLDIVES | 1. Cómo se consiguen | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Puntos WORLDIVES | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Puntos WORLDIVES | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Declaración de accesibilidad · `#/legal/accesibilidad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Declaración de accesibilidad | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Declaración de accesibilidad | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Declaración de accesibilidad | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Declaración de accesibilidad | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Declaración de accesibilidad | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Declaración de accesibilidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Declaración de accesibilidad | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Declaración de accesibilidad | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Declaración de accesibilidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Declaración de accesibilidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Declaración de accesibilidad | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Declaración de accesibilidad | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Declaración de accesibilidad | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Declaración de accesibilidad | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Declaración de accesibilidad | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Declaración de accesibilidad | Leer | Botón | Funciona | Abre la ventana «Declaración de accesibilidad» |
| Declaración de accesibilidad | Situación actual | Enlace | Funciona | Cambia tabindex en h2#situacion-actual (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Declaración de accesibilidad | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Declaración de accesibilidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Contacto · `#/legal/contacto`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Contacto | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Contacto | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Contacto | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Contacto | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Contacto | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Contacto | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Contacto | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Contacto | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Contacto | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Contacto | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Contacto | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Contacto | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Contacto | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Contacto | Escríbenos | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Asunto» (elige una opción de la lista) · El navegador no deja enviarlo: «Tu nombre» (campo obligatorio) |
| Contacto | Ve a «Denunciar contenido» | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Asunto | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Enviar mensaje» (sin efecto inmediato, correcto) |
| Contacto | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Contacto | Leer | Botón | Funciona | Abre la ventana «Contacto» |
| Contacto | Quién somos | Enlace | Funciona | Cambia tabindex en h2#quien-somos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Contacto | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Créditos y licencias de terceros · `#/legal/creditos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Créditos y licencias de terceros | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Créditos y licencias de terceros | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Créditos y licencias de terceros | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Créditos y licencias de terceros | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Créditos y licencias de terceros | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Créditos y licencias de terceros | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Créditos y licencias de terceros | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Créditos y licencias de terceros | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Créditos y licencias de terceros | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Créditos y licencias de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Créditos y licencias de terceros | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Créditos y licencias de terceros | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Créditos y licencias de terceros | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Créditos y licencias de terceros | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Créditos y licencias de terceros | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Créditos y licencias de terceros | OpenStreetMap contributors | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Protomaps | Enlace externo | Funciona | Enlace externo a protomaps.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Esri World Imagery | Enlace externo | Funciona | Enlace externo a www.arcgis.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | gebco.net | Enlace externo | Funciona | Enlace externo a www.gebco.net (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leaflet.markercluster | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | protomaps-leaflet | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | qrcode | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | stripe-python | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | fontTools | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leer | Botón | Funciona | Abre la ventana «Créditos y licencias de terceros» |
| Créditos y licencias de terceros | Mapas y datos geográficos | Enlace | Funciona | Cambia tabindex en h2#mapas-y-datos-geograficos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Créditos y licencias de terceros | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Créditos y licencias de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de uso para buceadores · `#/legal/terminos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de uso para buceadores | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de uso para buceadores | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de uso para buceadores | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de uso para buceadores | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de uso para buceadores | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Leer | Botón | Funciona | Abre la ventana «Condiciones de uso para buceadores» |
| Condiciones de uso para buceadores | 1. Qué es WORLDIVES DISCOVERY | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 9 más iguales en la lista (no se prueban todos) |
| Condiciones de uso para buceadores | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Bahía Coralina Centro de Buceo · ⌂ Resumen · `#/admin`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Ver mi página | Enlace | Funciona | Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Actualizar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Miércoles, 14 de octubre Buenos días. Hoy tienes 4 reservas con 6 buceadores. + Nueva reserva Abrir planning Hoy 4 6 per» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ⌂ Resumen | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Miércoles, 14 de octubre Buenos días. Hoy tienes 4 reservas con 6 buceadores. + Nueva reserva Abrir planning Hoy 4 6 per» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ▦ Planning / agenda | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (3 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ▣ Reservas 2 | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ♙ Clientes | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (1 elementos): «Base de clientes Clientes Todas las personas que han reservado con tu centro o han hecho check-in con tu QR. 20 clientes» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ◈ Servicios y tarifas | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (11 elementos): «Cargando catálogo…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ✈ Experiencias | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (3 elementos): «Cargando experiencias…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ⌖ Puntos de buceo | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (22 elementos): «CENTRO · PUNTOS Mis puntos de buceo Asocia aquí los lugares a los que suele ir tu centro. No necesitas crear el punto de» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ▣ Check-in / QR y promociones | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (3 elementos): «Promociones Validar un código QR de check-in» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ★ Recompensas | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (2 elementos): «PUNTOS WORLDIVES Ventajas y puntos Los buceadores canjean sus puntos por las ventajas que tu centro define y paga. Los p» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ✆ Avisos y WhatsApp | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (3 elementos): «Avisos Avisos a tus clientes y WhatsApp Si cancelas una salida o cambias la hora o el punto de encuentro, avisamos a tod» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ✉ Solicitudes de información | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (2 elementos): «Solicitudes de información Mensajes de buceadores interesados Contesta directamente por email o teléfono. Te llegan tamb» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | ⇩ Herramientas | Botón | Funciona | Cambia su estado (class: cb-nav → cb-nav active) · Muestra contenido nuevo (4 elementos): «Herramientas Exportar, calendario, widget e importación Exportar mis datos (CSV) Disponible siempre, en cualquier plan. » · GET /api/provider/ical → 403 «Tu perfil no permite cambiar la ficha ni los ajustes del centro. Pídeselo al propietario del centro.» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | + Nueva reserva | Botón | Funciona | Abre la ventana «Nueva reserva» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Abrir planning | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Hoy 4 6 personas | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Solicitudes pendientes 2 Necesitan respuesta | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Por cobrar 390 € 1 reserva | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Próximos 7 días 30 reservas | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Ver la semana | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | 08:00 | Enlace | Funciona | Abre #/reserva?id=1250 · hay 10 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Ir a reservas | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Programar salidas | Botón | Funciona | Muestra contenido nuevo (11 elementos): «Cargando catálogo…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Publicar un viaje | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando experiencias…» |
| Bahía Coralina Centro de Buceo · ⌂ Resumen | Ver clientes | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Base de clientes Clientes Todas las personas que han reservado con tu centro o han hecho check-in con tu QR. 20 clientes» |

#### Tu ficha de buceador · `#/cuenta`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Tu ficha de buceador | Explorador 0 puntos | Enlace | Funciona | Abre #/recompensas |
| Tu ficha de buceador | Mi centro | Enlace | Funciona | Abre #/admin |
| Tu ficha de buceador | Log Book | Enlace | Funciona | Abre #/logbook |
| Tu ficha de buceador | Recompensas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Tu ficha de buceador»: Abre #/recompensas |
| Tu ficha de buceador | Mis puntos | Enlace | Funciona | Abre #/mis-puntos |
| Tu ficha de buceador | Mi cuenta | Enlace | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| Tu ficha de buceador | Datos personales | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Nombre y apellidos» (campo obligatorio) |
| Tu ficha de buceador | Prefijo del país | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Idioma preferido | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Nivel de certificación | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | ¿Sueles alquilar equipo? | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Tipo de traje | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Documentación | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Título» (campo obligatorio) · El navegador no deja enviarlo: «Archivo (PDF o imagen, máximo 10 MB)» (falta el archivo) |
| Tu ficha de buceador | Tipo | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Seguridad | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Contraseña actual» (campo obligatorio) · El navegador no deja enviarlo: «Nueva contraseña» (campo obligatorio) |
| Tu ficha de buceador | Activar | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Tu contraseña» (campo obligatorio) |
| Tu ficha de buceador | Descargar mis datos (ZIP) | Enlace | Funciona | Descarga /api/account/export?format=zip (200, application/zip) |
| Tu ficha de buceador | Privacidad | Enlace | Funciona | Abre #/legal/privacidad |
| Tu ficha de buceador | Condiciones de uso | Enlace | Funciona | Abre #/legal/condiciones-buceadores |
| Tu ficha de buceador | Condiciones de reserva | Enlace | Funciona | Abre #/legal/condiciones-reserva |
| Tu ficha de buceador | Cookies | Enlace | Funciona | Abre #/legal/cookies |
| Tu ficha de buceador | Abrir el panel | Enlace | Funciona | Mismo enlace (#/admin) que «Mi centro» en «Tu ficha de buceador»: Abre #/admin |
| Tu ficha de buceador | Cerrar sesión | Botón | Funciona | [probado al final del papel] Abre #/ · POST /api/auth/logout → 200 · cierra la sesión o cambia la cuenta: se vuelve a iniciar sesión |

#### Log Book · `#/logbook`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Log Book | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Tu ficha de buceador»: Abre #/recompensas |
| Log Book | Exportar CSV | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Tu historial de inmersiones. Las reservas completadas se añaden solas; el resto, en un momento.» |
| Log Book | Nueva inmersión | Botón | Funciona | Abre la ventana «Nueva inmersión» |
| Log Book | Añadir mi primera inmersión | Botón | Funciona | Abre la ventana «Nueva inmersión» |

#### Recompensas · `#/recompensas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Recompensas | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Tu ficha de buceador»: Abre #/recompensas |
| Recompensas | Cómo funcionan | Enlace | Funciona | Abre #/como-funcionan-los-puntos |
| Recompensas | Canjear | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Linterna para la nocturna» · hay 2 más iguales en la lista (no se prueban todos) |
| Recompensas | Canjear | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Te faltan 150 puntos» |

#### Mis puntos · `#/mis-puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Mis puntos | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Tu ficha de buceador»: Abre #/recompensas |
| Mis puntos | Ver ventajas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Tu ficha de buceador»: Abre #/recompensas |
| Mis puntos | Más información sobre los puntos | Enlace | Funciona | Mismo enlace (#/como-funcionan-los-puntos) que «Cómo funcionan» en «Recompensas»: Abre #/como-funcionan-los-puntos |

#### Hannah Weber · `#/reserva?id=1250`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Hannah Weber | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Hannah Weber | Reservas | Enlace | Funciona | Abre #/admin?tab=bookings |
| Hannah Weber | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1250/receipt.pdf (200, application/pdf) |
| Hannah Weber | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1250/diver-sheet.pdf (200, application/pdf) |
| Hannah Weber | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Hannah Weber | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Hannah Weber | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| Hannah Weber | PDF | Enlace | Funciona | Descarga /api/bookings/1250/diver-sheet.pdf (200, application/pdf) |
| Hannah Weber | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Emily Clarke · `#/reserva?id=1265`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Emily Clarke | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Emily Clarke | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Emily Clarke | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1265/receipt.pdf (200, application/pdf) |
| Emily Clarke | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1265/diver-sheet.pdf (200, application/pdf) |
| Emily Clarke | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Emily Clarke | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Emily Clarke | Aceptar | Botón | Funciona | Aviso: «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · POST /api/bookings/1265/status → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» |
| Emily Clarke | Rechazar | Botón | Funciona | Abre la ventana «Rechazar la solicitud» |
| Emily Clarke | PDF | Enlace | Funciona | Descarga /api/bookings/1265/diver-sheet.pdf (200, application/pdf) |
| Emily Clarke | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Chloé Martin · `#/reserva?id=1264`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Chloé Martin | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Chloé Martin | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Chloé Martin | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1264/receipt.pdf (200, application/pdf) |
| Chloé Martin | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1264/diver-sheet.pdf (200, application/pdf) |
| Chloé Martin | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Chloé Martin | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Chloé Martin | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| Chloé Martin | PDF | Enlace | Funciona | Descarga /api/bookings/1264/diver-sheet.pdf (200, application/pdf) |
| Chloé Martin | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Lukas Becker · `#/reserva?id=1263`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Lukas Becker | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Lukas Becker | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Lukas Becker | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1263/receipt.pdf (200, application/pdf) |
| Lukas Becker | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1263/diver-sheet.pdf (200, application/pdf) |
| Lukas Becker | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Lukas Becker | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Lukas Becker | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| Lukas Becker | PDF | Enlace | Funciona | Descarga /api/bookings/1263/diver-sheet.pdf (200, application/pdf) |
| Lukas Becker | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Hannah Weber · `#/reserva?id=1249`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Hannah Weber | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Hannah Weber | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Hannah Weber | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1249/receipt.pdf (200, application/pdf) |
| Hannah Weber | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1249/diver-sheet.pdf (200, application/pdf) |
| Hannah Weber | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Hannah Weber | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Hannah Weber | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| Hannah Weber | PDF | Enlace | Funciona | Descarga /api/bookings/1249/diver-sheet.pdf (200, application/pdf) |
| Hannah Weber | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### João Silva · `#/reserva?id=1244`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| João Silva | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| João Silva | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| João Silva | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1244/receipt.pdf (200, application/pdf) |
| João Silva | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1244/diver-sheet.pdf (200, application/pdf) |
| João Silva | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| João Silva | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| João Silva | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| João Silva | PDF | Enlace | Funciona | Descarga /api/bookings/1244/diver-sheet.pdf (200, application/pdf) |
| João Silva | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Tom Jansen · `#/reserva?id=1239`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Tom Jansen | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Tom Jansen | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Tom Jansen | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1239/receipt.pdf (200, application/pdf) |
| Tom Jansen | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1239/diver-sheet.pdf (200, application/pdf) |
| Tom Jansen | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Tom Jansen | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Tom Jansen | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| Tom Jansen | PDF | Enlace | Funciona | Descarga /api/bookings/1239/diver-sheet.pdf (200, application/pdf) |
| Tom Jansen | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Giulia Romano · `#/reserva?id=1268`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Giulia Romano | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Giulia Romano | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Giulia Romano | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1268/receipt.pdf (200, application/pdf) |
| Giulia Romano | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1268/diver-sheet.pdf (200, application/pdf) |
| Giulia Romano | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Giulia Romano | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Giulia Romano | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| Giulia Romano | PDF | Enlace | Funciona | Descarga /api/bookings/1268/diver-sheet.pdf (200, application/pdf) |
| Giulia Romano | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Bea Navarro · `#/reserva?id=1230`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bea Navarro | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bea Navarro | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |
| Bea Navarro | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1230/receipt.pdf (200, application/pdf) |
| Bea Navarro | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1230/diver-sheet.pdf (200, application/pdf) |
| Bea Navarro | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Bea Navarro | Cambiar fecha u hora | Botón | Funciona | Abre la ventana «Cambiar fecha u hora» |
| Bea Navarro | Aceptar | Botón | Funciona | Aviso: «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · POST /api/bookings/1230/status → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» |
| Bea Navarro | Rechazar | Botón | Funciona | Abre la ventana «Rechazar la solicitud» |
| Bea Navarro | PDF | Enlace | Funciona | Descarga /api/bookings/1230/diver-sheet.pdf (200, application/pdf) |
| Bea Navarro | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Hannah Weber»: Abre #/admin?tab=bookings |

#### Bahía Coralina Centro de Buceo · ▦ Planning / agenda · `#/admin?tab=planning`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Actualizar | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Mes anterior | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Mes siguiente | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Mes | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Lista | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | + Reserva | Botón | Funciona | Abre la ventana «Nueva reserva» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Crear cartel | Botón | Funciona | Abre la ventana «Crear cartel para redes» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Abr | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | May 34 | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Oct 75 | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Nov | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» · hay 3 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Dic | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Jueves, 1 de octubre | Botón | Funciona | Abre la ventana «Jueves, 1 de octubre» · Cambia su estado (class: pl-cell  is-past  → pl-cell is-past is-open) · hay 2 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Viernes, 2 de octubre | Botón | Funciona | Abre la ventana «Viernes, 2 de octubre» · Cambia su estado (class: pl-cell  is-past  → pl-cell is-past is-open) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Sábado, 3 de octubre: 3 salidas, 4 buceadores | Botón | Funciona | Abre la ventana «Sábado, 3 de octubre» · Cambia su estado (class: pl-cell  is-past has-events → pl-cell is-past has-events is-open) · hay 6 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Domingo, 4 de octubre: 1 salidas, 3 buceadores | Botón | Funciona | Abre la ventana «Domingo, 4 de octubre» · Cambia su estado (class: pl-cell  is-past has-events → pl-cell is-past has-events is-open) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Martes, 13 de octubre | Botón | Funciona | Abre la ventana «Martes, 13 de octubre» · Cambia su estado (class: pl-cell is-today   → pl-cell is-today is-open) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Miércoles, 14 de octubre: 5 salidas, 7 buceadores | Botón | Funciona | Abre la ventana «Miércoles, 14 de octubre» · Cambia su estado (class: pl-cell   has-events → pl-cell has-events is-open) · hay 10 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Jueves, 15 de octubre: 5 salidas, 7 buceadores | Botón | Funciona | Abre la ventana «Jueves, 15 de octubre» · Cambia su estado (class: pl-cell   has-events → pl-cell has-events is-open) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Sábado, 24 de octubre | Botón | Funciona | Abre la ventana «Sábado, 24 de octubre» · Cambia su estado (class: pl-cell    → pl-cell is-open) · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda | Domingo, 25 de octubre | Botón | Funciona | Abre la ventana «Domingo, 25 de octubre» · Cambia su estado (class: pl-cell    → pl-cell is-open) |

#### Bahía Coralina Centro de Buceo · ▦ Planning / agenda › Lista · `#/admin?tab=planning` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda › Lista | 3 | Botón | Funciona | Abre la ventana «Sábado, 3 de octubre» · Cambia su estado (class: pl-lday-head → pl-lday-head is-open) · hay 18 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▦ Planning / agenda › Lista | 4 | Botón | Funciona | Abre la ventana «Domingo, 4 de octubre» · Cambia su estado (class: pl-lday-head → pl-lday-head is-open) |

#### Bahía Coralina Centro de Buceo · ▣ Reservas · `#/admin?tab=bookings`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▣ Reservas | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Actualizar | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | + Nueva reserva | Botón | Funciona | Abre la ventana «Nueva reserva» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Hoy | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Próximos 7 días | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Solicitudes pendientes 2 | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Por cobrar 1 | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Todas las próximas | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Historial | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Actividad | Desplegable | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Todas las reservas del centro en un sitio: las de WORLDIVES, las de tu web y las que apunta» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Registrar cobro | Botón | Funciona | Abre la ventana «Registrar pago» · hay 26 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Completar | Botón | Funciona | Aviso: «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · POST /api/bookings/1250/status → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · hay 1 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Registrar cobro | Botón | Funciona | Abre la ventana «Registrar pago» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Completar | Botón | Funciona | Aviso: «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · POST /api/bookings/1263/status → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Aceptar | Botón | Funciona | Aviso: «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · POST /api/bookings/1265/status → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» |
| Bahía Coralina Centro de Buceo · ▣ Reservas | Rechazar | Botón | Funciona | Abre la ventana «Rechazar la solicitud» |

#### Bahía Coralina Centro de Buceo · ▣ Reservas › Historial · `#/admin?tab=bookings` (1 clic en subpestaña)

Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).

#### Bahía Coralina Centro de Buceo · ▣ Reservas › Todas las próximas · `#/admin?tab=bookings` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▣ Reservas › Todas las próximas | Aceptar | Botón | Funciona | Aviso: «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · POST /api/bookings/1230/status → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» |
| Bahía Coralina Centro de Buceo · ▣ Reservas › Todas las próximas | Rechazar | Botón | Funciona | Abre la ventana «Rechazar la solicitud» |
| Bahía Coralina Centro de Buceo · ▣ Reservas › Todas las próximas | Registrar cobro | Botón | Funciona | Abre la ventana «Registrar pago» · hay 32 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ▣ Reservas › Todas las próximas | Registrar cobro | Botón | Funciona | Abre la ventana «Registrar pago» |

#### Bahía Coralina Centro de Buceo · ▣ Reservas › Por cobrar · `#/admin?tab=bookings` (1 clic en subpestaña)

Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).

#### Bahía Coralina Centro de Buceo · ▣ Reservas › Solicitudes pendientes · `#/admin?tab=bookings` (1 clic en subpestaña)

Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).

#### Bahía Coralina Centro de Buceo · ▣ Reservas › Hoy · `#/admin?tab=bookings` (1 clic en subpestaña)

Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).

#### Bahía Coralina Centro de Buceo · ♙ Clientes · `#/admin?tab=clients`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ♙ Clientes | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ♙ Clientes | Actualizar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Base de clientes Clientes Todas las personas que han reservado con tu centro o han hecho check-in con tu QR. 20 clientes» |
| Bahía Coralina Centro de Buceo · ♙ Clientes | bea.navarro@example.com | Enlace externo | Funciona | Correo bea.navarro@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | wei.chen@example.com | Enlace externo | Funciona | Correo wei.chen@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | pierre.lambert@example.com | Enlace externo | Funciona | Correo pierre.lambert@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | kasia.nowak@example.com | Enlace externo | Funciona | Correo kasia.nowak@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | nuria.costa@example.com | Enlace externo | Funciona | Correo nuria.costa@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | lukas.becker@example.com | Enlace externo | Funciona | Correo lukas.becker@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | chloe.martin@example.com | Enlace externo | Funciona | Correo chloe.martin@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | giulia.romano@example.com | Enlace externo | Funciona | Correo giulia.romano@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | tom.jansen@example.com | Enlace externo | Funciona | Correo tom.jansen@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | emily.clarke@example.com | Enlace externo | Funciona | Correo emily.clarke@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | alvaro.ruiz@example.com | Enlace externo | Funciona | Correo alvaro.ruiz@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | joao.silva@example.com | Enlace externo | Funciona | Correo joao.silva@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | hannah.weber@example.com | Enlace externo | Funciona | Correo hannah.weber@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | sofie.devries@example.com | Enlace externo | Funciona | Correo sofie.devries@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | raul.ortega@example.com | Enlace externo | Funciona | Correo raul.ortega@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | lucia.prieto@example.com | Enlace externo | Funciona | Correo lucia.prieto@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | anna.kowalska@example.com | Enlace externo | Funciona | Correo anna.kowalska@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | marco.bianchi@example.com | Enlace externo | Funciona | Correo marco.bianchi@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | james.walker@example.com | Enlace externo | Funciona | Correo james.walker@example.com |
| Bahía Coralina Centro de Buceo · ♙ Clientes | li.na@example.com | Enlace externo | Funciona | Correo li.na@example.com |

#### Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas · `#/admin?tab=services`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Actualizar | Botón | Funciona | Muestra contenido nuevo (11 elementos): «Cargando catálogo…» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | + Nuevo servicio | Botón | Funciona | Abre la ventana «Nuevo servicio» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Cobros y pagos | Enlace | Funciona | Abre #/admin?tab=payments · GET /api/provider/payments → 403 «Tu perfil no permite ver cobros ni devolver dinero. Pídeselo al propietario del centro.» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Servicios 7 | Botón | Funciona | Muestra contenido nuevo (9 elementos): «Catálogo y precios Servicios y tarifas Lo que vende tu centro, su precio y sus salidas. + Nuevo servicio 2 servicios no » |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Extras 0 | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Catálogo y precios Servicios y tarifas Lo que vende tu centro, su precio y sus salidas. + Nuevo servicio 2 servicios no » |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Alquiler de equipo 0/8 | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Catálogo y precios Servicios y tarifas Lo que vende tu centro, su precio y sus salidas. + Nuevo servicio 2 servicios no » |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Todos | Botón | Funciona | Muestra contenido nuevo (8 elementos): «Alquiler de equipo completo Alquiler de equipo · 8 h A la venta 25 € tarifa base Cambiar tarifa Bajo petición · el centr» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Alquiler de equipo | Botón | Funciona | Cambia su estado (class: svc-chip  → svc-chip active) · Muestra contenido nuevo (2 elementos): «Alquiler de equipo completo Alquiler de equipo · 8 h A la venta 25 € tarifa base Cambiar tarifa Bajo petición · el centr» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Bautizo / experiencia | Botón | Funciona | Cambia su estado (class: svc-chip  → svc-chip active) · Muestra contenido nuevo (2 elementos): «Bautizo de buceo Bautizo / experiencia · 2 h 30 min A la venta 55 € por persona · desde el Mar, 15 jun: 65 € Cambiar tar» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Curso | Botón | Funciona | Cambia su estado (class: svc-chip  → svc-chip active) · Muestra contenido nuevo (3 elementos): «Curso de Nitrox Curso · 4 h A la venta 160 € por persona Cambiar tarifa Bajo petición · el centro responde en 24 h Hasta» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Inmersión | Botón | Funciona | Cambia su estado (class: svc-chip  → svc-chip active) · Muestra contenido nuevo (4 elementos): «Doble inmersión en barco Inmersión · 4 h A la venta 70 € por persona · desde el Mar, 15 jun: 82 € Cambiar tarifa Bajo pe» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Cambiar tarifa | Botón | Funciona | Abre la ventana «Tarifa» · hay 5 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Alquiler de equipo | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Catálogo y precios Servicios y tarifas Lo que vende tu centro, su precio y sus salidas. + Nuevo servicio 2 servicios no » |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Editar | Botón | Funciona | Abre la ventana «Editar servicio» · hay 5 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Cambiar tarifa | Botón | Funciona | Abre la ventana «Tarifa» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Ver las 16 | Botón | Funciona | Abre la ventana «Salidas de Bautizo de buceo» · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Mié, 14 oct 16:00 6 libres | Botón | Funciona | Abre la ventana «Editar salida» · hay 16 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Jue, 15 oct 16:00 6 libres | Botón | Funciona | Abre la ventana «Editar salida» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | + Salida | Botón | Funciona | Abre la ventana «Nueva salida» · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Agenda | Botón | Funciona | Abre la ventana «Salidas de Bautizo de buceo» · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Editar | Botón | Funciona | Abre la ventana «Editar servicio» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Ver las 3 | Botón | Funciona | Abre la ventana «Salidas de Curso de Nitrox» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | + Salida | Botón | Funciona | Abre la ventana «Nueva salida» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | Agenda | Botón | Funciona | Abre la ventana «Salidas de Curso de Nitrox» |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas | + Nuevo servicio Inmersión, curso, bautizo, viaje… | Botón | Funciona | Abre la ventana «Nuevo servicio» |

#### Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas › Alquiler de equipo 0/ · `#/admin?tab=services` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas › Alquiler de equipo 0/ | Guardar cambios | Botón | Desactivado (correcto) | Desactivado hasta que se cambia algo (botón de guardar) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas › Alquiler de equipo 0/ | Guardar | Botón | Funciona | Aviso: «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · POST /api/center-equipment → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · hay 6 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ◈ Servicios y tarifas › Alquiler de equipo 0/ | Guardar | Botón | Funciona | Aviso: «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · POST /api/center-equipment → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» |

#### Bahía Coralina Centro de Buceo · ✈ Experiencias · `#/admin?tab=experiences`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ✈ Experiencias | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ✈ Experiencias | Actualizar | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando experiencias…» |
| Bahía Coralina Centro de Buceo · ✈ Experiencias | + Nueva experiencia | Botón | Funciona | Abre la ventana «Nueva experiencia» |
| Bahía Coralina Centro de Buceo · ✈ Experiencias | Añadir foto | Botón | Funciona | Abre la ventana «Foto de la experiencia» |
| Bahía Coralina Centro de Buceo · ✈ Experiencias | Ver en la web | Enlace | Funciona | Abre #/experiencia?id=7 |
| Bahía Coralina Centro de Buceo · ✈ Experiencias | Editar | Botón | Funciona | Abre la ventana «Editar experiencia» |
| Bahía Coralina Centro de Buceo · ✈ Experiencias | Ocultar | Botón | Funciona | Pide confirmación «¿Ocultar esta experiencia de la web?» (cancelado) |

#### Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo · `#/admin?tab=points`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Actualizar | Botón | Funciona | Muestra contenido nuevo (22 elementos): «CENTRO · PUNTOS Mis puntos de buceo Asocia aquí los lugares a los que suele ir tu centro. No necesitas crear el punto de» |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Nuevo punto | Botón | Funciona | Muestra contenido nuevo (42 elementos): «Gestión / Nuevo punto CATÁLOGO Nuevo punto La posición se puede introducir manualmente o seleccionando una localización » |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Fotos | Botón | Funciona | Abre la ventana «Fotos · Cabo San Antonio» · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Quitar | Botón | Funciona | Pide confirmación «¿Quitar este punto de los puntos habituales del centro?» (cancelado) · hay 4 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Fotos | Botón | Funciona | Abre la ventana «Fotos · Cabo San Martin / Cueva de la Virgen» |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Quitar | Botón | Funciona | Pide confirmación «¿Quitar este punto de los puntos habituales del centro?» (cancelado) |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Añadir | Botón | Funciona | Aviso: «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · POST /api/center-points/assign → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · hay 18 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo · ⌖ Puntos de buceo | Añadir | Botón | Funciona | Aviso: «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · POST /api/center-points/assign → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» |

#### Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones · `#/admin?tab=qr`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Actualizar | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Promociones Validar un código QR de check-in» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Promociones | Botón | Funciona | Muestra contenido nuevo (1 elementos): «FIDELIZACIÓN Promociones con QR Crea una promoción, dásela a clientes de tu base y cada uno recibe en su app un QR perso» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Validar un código | Botón | Funciona | Cambia su estado (class: pr-tab → pr-tab is-on) · Muestra contenido nuevo (1 elementos): «VALIDAR Comprobar un código promocional Escanea el QR del cliente con la cámara del móvil (se abre esta misma comprobaci» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | QR de check-in | Botón | Funciona | Cambia su estado (class: pr-tab → pr-tab is-on) · Muestra contenido nuevo (1 elementos): «IDENTIFICACIÓN DIGITAL Check-in / QR El centro ya está seleccionado automáticamente: Bahía Coralina Centro de Buceo. No » |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Nueva promoción | Botón | Funciona | Abre la ventana «Nueva promoción» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Dar a clientes | Botón | Funciona | Abre la ventana «Dar «Bono 10 inmersiones»» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Ver códigos | Botón | Funciona | Abre la ventana «Códigos de «Bono 10 inmersiones»» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Editar | Botón | Funciona | Abre la ventana «Editar promoción» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Finalizar | Botón | Funciona | Pide confirmación «¿Finalizar la promoción? Sus códigos dejarán de ser válidos.» (cancelado) |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Dar a clientes | Botón | Funciona | Abre la ventana «Dar «10 % en tu próxima inmersión»» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Ver códigos | Botón | Funciona | Abre la ventana «Códigos de «10 % en tu próxima inmersión»» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Editar | Botón | Funciona | Abre la ventana «Editar promoción» |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones | Finalizar | Botón | Funciona | Pide confirmación «¿Finalizar la promoción? Sus códigos dejarán de ser válidos.» (cancelado) |

#### Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › QR de check-in · `#/admin?tab=qr` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › QR de check-in | 🏪 Centro Identificar el centro y hacer check-in | Botón | Funciona | Cambia su estado (class: cb-qr-purpose → cb-qr-purpose active) |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › QR de check-in | 🤿 Buceador Identificar al cliente al llegar | Botón | Funciona | Cambia su estado (class: cb-qr-purpose → cb-qr-purpose active) · Cambia el valor de «Nombre del QR» (Identificación del centro → Check-in del buceador) |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › QR de check-in | 🌊 Inmersión Compartir los datos de una salida con el Log Book | Botón | Funciona | Cambia su estado (class: cb-qr-purpose → cb-qr-purpose active) · Muestra contenido nuevo (78 elementos): «2026-10-14 · 08:00 · Alquiler de equipo completo» · Cambia el valor de «Nombre del QR» (Identificación del centro → Inmersión) |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › QR de check-in | 🎫 Reserva Identificar una reserva concreta | Botón | Funciona | Cambia su estado (class: cb-qr-purpose → cb-qr-purpose active) · Muestra contenido nuevo (150 elementos): «#1236 · 2026-11-09 · Doble inmersión en barco» · Cambia el valor de «Nombre del QR» (Identificación del centro → Reserva) |
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › QR de check-in | Check-in / QR | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Nombre del QR» (campo obligatorio) |

#### Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › Validar un código · `#/admin?tab=qr` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ▣ Check-in / QR y promociones › Validar un código | Comprobar un código promocional | Formulario | Funciona | Enviado vacío · Aviso: «Escribe el código completo.» |

#### Bahía Coralina Centro de Buceo · ★ Recompensas · `#/admin?tab=rewards`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ★ Recompensas | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Actualizar | Botón | Funciona | Muestra contenido nuevo (2 elementos): «PUNTOS WORLDIVES Ventajas y puntos Los buceadores canjean sus puntos por las ventajas que tu centro define y paga. Los p» |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Validar un código | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «WOD-XXXXXXXX» (campo obligatorio) |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Escanear | Botón | Funciona | Aviso: «Este navegador no puede escanear: escribe el código.» |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Conceder puntos | Formulario | Funciona | Enviado vacío · Aviso: «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» · POST /api/provider/points-grant → 403 «Tu perfil es de solo lectura para esto. Pídeselo al propietario del centro.» |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Cliente | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Bahía Coralina Centro de Buceo · ★ Recompensas | + Nueva ventaja | Botón | Funciona | Abre la ventana «Nueva ventaja» |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Editar | Botón | Funciona | Abre la ventana «Editar ventaja» |
| Bahía Coralina Centro de Buceo · ★ Recompensas | Editar | Botón | Funciona | Abre la ventana «Editar ventaja» |

#### Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp · `#/admin?tab=avisos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp | Actualizar | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Avisos Avisos a tus clientes y WhatsApp Si cancelas una salida o cambias la hora o el punto de encuentro, avisamos a tod» |
| Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp | Al cancelar una salida, por defecto | Formulario | Funciona | Enviado vacío · Aviso: «Tu perfil no permite cancelar salidas ni avisar a todos los clientes. Pídeselo al propietario del centro.» · POST /api/avisos/ajustes → 403 «Tu perfil no permite cancelar salidas ni avisar a todos los clientes. Pídeselo al propietario del centro.» |
| Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp | Hora del recordatorio | Desplegable | Desactivado (correcto) | Desactivado; la pantalla explica: «Cada buceador elige otra fecha o la devolución» |
| Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp | Recordatorio del día antes | Botón | Funciona | Abre la ventana «Estado del aviso» |
| Bahía Coralina Centro de Buceo · ✆ Avisos y WhatsApp | Recordatorio del día antes | Botón | Funciona | Abre la ventana «Estado del aviso» |

#### Bahía Coralina Centro de Buceo · ✉ Solicitudes de información · `#/admin?tab=requests`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ✉ Solicitudes de información | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ✉ Solicitudes de información | Actualizar | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Solicitudes de información Mensajes de buceadores interesados Contesta directamente por email o teléfono. Te llegan tamb» |

#### Bahía Coralina Centro de Buceo · ⇩ Herramientas · `#/admin?tab=tools`

Al abrirla, el servidor responde con error a: `GET /api/provider/ical → 403` (la pantalla se ve bien; revisar si sobran esas llamadas).

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Actualizar | Botón | Funciona | Muestra contenido nuevo (4 elementos): «Herramientas Exportar, calendario, widget e importación Exportar mis datos (CSV) Disponible siempre, en cualquier plan. » · GET /api/provider/ical → 403 «Tu perfil no permite cambiar la ficha ni los ajustes del centro. Pídeselo al propietario del centro.» |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Clientes | Enlace | Funciona | Descarga /api/center/export?kind=clients (200, text/csv) |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Reservas | Enlace | Funciona | Descarga /api/center/export?kind=bookings (200, text/csv) |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Servicios | Enlace | Funciona | Descarga /api/center/export?kind=services (200, text/csv) |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Agenda | Enlace | Funciona | Descarga /api/center/export?kind=agenda (200, text/csv) |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Copiar | Botón | Funciona | Aviso: «Copiado.» |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Compartir por WhatsApp | Enlace externo | Funciona | Enlace externo a wa.me (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo · ⇩ Herramientas | Copiar | Botón | Funciona | Aviso: «Copiado.» |

#### Bahía Coralina Centro de Buceo · `#/admin?tab=payments`

Al abrirla, el servidor responde con error a: `GET /api/provider/payments → 403` (la pantalla se ve bien; revisar si sobran esas llamadas).

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Ver mi página | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Ver mi página» en «Bahía Coralina Centro de Buceo · ⌂ Resum»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | Actualizar | Botón | Funciona | Muestra contenido nuevo (2 elementos): «No se pudo cargar la sección de cobros Tu perfil no permite ver cobros ni devolver dinero. Pídeselo al propietario del c» · GET /api/provider/payments → 403 «Tu perfil no permite ver cobros ni devolver dinero. Pídeselo al propietario del centro.» |

### Freelance (freelance.prueba)

61 pantallas, 843 elementos probados en 10 min 6 s.

#### Cabecera, pie y elementos flotantes (comunes a todas las pantallas)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Encuentra tu próxima inmersión · flotante | Saltar al contenido | Enlace | Funciona | Desplaza la página · clic por JavaScript (no se puede pulsar con el ratón) |
| Encuentra tu próxima inmersión · cabecera | WORLDIVES DISCOVERY · inicio | Enlace | Funciona | Enlace a la pantalla en la que ya se está |
| Encuentra tu próxima inmersión · cabecera | Explorar | Enlace | Funciona | Abre #/explorar |
| Encuentra tu próxima inmersión · cabecera | Puntos de buceo | Enlace | Funciona | Abre #/puntos |
| Encuentra tu próxima inmersión · cabecera | Centros | Enlace | Funciona | Abre #/centros |
| Encuentra tu próxima inmersión · cabecera | Tipos de buceo | Enlace | Funciona | Abre #/tipos |
| Encuentra tu próxima inmersión · cabecera | Experiencias | Enlace | Funciona | Abre #/experiencias |
| Encuentra tu próxima inmersión · cabecera | Top 10 buceos | Enlace | Funciona | Abre #/top10 |
| Encuentra tu próxima inmersión · cabecera | Seleccionar idioma | Desplegable | Funciona | Recarga la página con /?lang=en · POST /api/account/language → 200 |
| Encuentra tu próxima inmersión · cabecera | DA Diego ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) |
| Encuentra tu próxima inmersión · pie de página | Explorar el mapa | Enlace | Funciona | Mismo enlace (#/explorar) que «Explorar» en «Encuentra tu próxima inmersión»: Abre #/explorar |
| Encuentra tu próxima inmersión · pie de página | Top 10 cerca de ti | Enlace | Funciona | Mismo enlace (#/top10) que «Top 10 buceos» en «Encuentra tu próxima inmersión»: Abre #/top10 |
| Encuentra tu próxima inmersión · pie de página | Centros de buceo | Enlace | Funciona | Mismo enlace (#/centros) que «Centros» en «Encuentra tu próxima inmersión»: Abre #/centros |
| Encuentra tu próxima inmersión · pie de página | Viajes y vida a bordo | Enlace | Funciona | Mismo enlace (#/experiencias) que «Experiencias» en «Encuentra tu próxima inmersión»: Abre #/experiencias |
| Encuentra tu próxima inmersión · pie de página | Mi cuenta | Enlace | Funciona | Abre #/cuenta |
| Encuentra tu próxima inmersión · pie de página | Log Book | Enlace | Funciona | Abre #/logbook |
| Encuentra tu próxima inmersión · pie de página | Recompensas | Enlace | Funciona | Abre #/recompensas |
| Encuentra tu próxima inmersión · pie de página | Mis puntos | Enlace | Funciona | Abre #/mis-puntos |
| Encuentra tu próxima inmersión · pie de página | Dar de alta mi centro | Enlace | Funciona | Abre #/registro |
| Encuentra tu próxima inmersión · pie de página | Panel del centro | Enlace | Funciona | Abre #/admin?tab=dashboard |
| Encuentra tu próxima inmersión · pie de página | Condiciones para centros | Enlace | Funciona | Abre #/legal/condiciones-centros |
| Encuentra tu próxima inmersión · pie de página | Aviso legal | Enlace | Funciona | Abre #/legal/aviso-legal |
| Encuentra tu próxima inmersión · pie de página | Privacidad | Enlace | Funciona | Abre #/legal/privacidad |
| Encuentra tu próxima inmersión · pie de página | Cookies | Enlace | Funciona | Abre #/legal/cookies |
| Encuentra tu próxima inmersión · pie de página | Condiciones de uso | Enlace | Funciona | Abre #/legal/condiciones-buceadores |
| Encuentra tu próxima inmersión · pie de página | Condiciones de reserva | Enlace | Funciona | Abre #/legal/condiciones-reserva |
| Encuentra tu próxima inmersión · pie de página | Para centros | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Encuentra tu próxima inmersión · pie de página | Denunciar contenido | Enlace | Funciona | Abre #/legal/denuncias |
| Diego Arenas · ⌂ Resumen · flotante | Saltar al contenido | Enlace | Funciona | Desplaza la página · clic por JavaScript (no se puede pulsar con el ratón) |

#### Encuentra tu próxima inmersión · `#/`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Encuentra tu próxima inmersión | Buscar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «⌕ Escribe al menos dos letras El nombre de un punto, una ciudad, una isla o un centro de buceo.» |
| Encuentra tu próxima inmersión | Cerca de mí | Enlace | Funciona | Mismo enlace (#/top10) que «Top 10 buceos» en «Encuentra tu próxima inmersión»: Abre #/top10 |
| Encuentra tu próxima inmersión | Pecios | Enlace | Funciona | Abre #/tipos?t=pecios-y-naufragios |
| Encuentra tu próxima inmersión | Cuevas | Enlace | Funciona | Abre #/tipos?t=cuevas-y-cavernas |
| Encuentra tu próxima inmersión | Arrecifes | Enlace | Funciona | Abre #/tipos?t=arrecifes |
| Encuentra tu próxima inmersión | Centros con reserva online | Enlace | Funciona | Abre #/centros?only=online |
| Encuentra tu próxima inmersión | Abrir el explorador → | Enlace | Funciona | Mismo enlace (#/explorar) que «Explorar» en «Encuentra tu próxima inmersión»: Abre #/explorar |
| Encuentra tu próxima inmersión | 01 Europa 108 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (32 elementos): «4» |
| Encuentra tu próxima inmersión | 02 Asia 104 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (26 elementos): «15» |
| Encuentra tu próxima inmersión | 03 América 24 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (25 elementos): «3» |
| Encuentra tu próxima inmersión | 04 África y Mar Rojo 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (34 elementos): «2» |
| Encuentra tu próxima inmersión | 05 Oceanía 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (11 elementos): «2» |
| Encuentra tu próxima inmersión | 06 Caribe 17 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (27 elementos): «8» |
| Encuentra tu próxima inmersión | Mapa | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| Encuentra tu próxima inmersión | Satélite Disponible próximamente | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Encuentra tu próxima inmersión | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (18 elementos): «Leaflet» |
| Encuentra tu próxima inmersión | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (19 elementos): «2» · hay 15 más iguales en la lista (no se prueban todos) |
| Encuentra tu próxima inmersión | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (7 elementos): «Rainbow Reef» |
| Encuentra tu próxima inmersión | Mauritius – Cathedral | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» · hay 1 más iguales en la lista (no se prueban todos) |
| Encuentra tu próxima inmersión | Tofo – Manta Reef | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» |
| Encuentra tu próxima inmersión | Zoom in | Enlace | Funciona | Muestra contenido nuevo (64 elementos): «2» |
| Encuentra tu próxima inmersión | Zoom out | Enlace | Funciona | Cambia su estado (class: leaflet-control-zoom-out → leaflet-control-zoom-out leaflet-disabled) · Cambia la pantalla (4 elementos nuevos, 0 quitados) |
| Encuentra tu próxima inmersión | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Encuentra tu próxima inmersión | OpenStreetMap contributors | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Encuentra tu próxima inmersión | Ver todos los tipos → | Enlace | Funciona | Mismo enlace (#/tipos) que «Tipos de buceo» en «Encuentra tu próxima inmersión»: Abre #/tipos |
| Encuentra tu próxima inmersión | Aguas profundas | Enlace | Funciona | Abre #/tipos?t=aguas-profundas |
| Encuentra tu próxima inmersión | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| Encuentra tu próxima inmersión | Paredes | Enlace | Funciona | Abre #/tipos?t=paredes |
| Encuentra tu próxima inmersión | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| Encuentra tu próxima inmersión | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| Encuentra tu próxima inmersión | Pináculos | Enlace | Funciona | Abre #/tipos?t=pinaculos |

#### El mapa del buceo · `#/explorar`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| El mapa del buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| El mapa del buceo | Todos | Botón | Funciona | Muestra contenido nuevo (36 elementos): «2» |
| El mapa del buceo | Arrecifes | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (58 elementos): «2» |
| El mapa del buceo | Paredes | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (45 elementos): «2» |
| El mapa del buceo | Pecios | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (32 elementos): «2» |
| El mapa del buceo | Cuevas | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (32 elementos): «3» |
| El mapa del buceo | Muck | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (30 elementos): «3» |
| El mapa del buceo | Pináculos | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (27 elementos): «7» |
| El mapa del buceo | Profundas | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (59 elementos): «2» |
| El mapa del buceo | 01 Europa 108 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (40 elementos): «2» |
| El mapa del buceo | 02 Asia 104 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (22 elementos): «2» |
| El mapa del buceo | 03 América 24 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (15 elementos): «2» |
| El mapa del buceo | 04 África y Mar Rojo 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (25 elementos): «2» |
| El mapa del buceo | 05 Oceanía 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (31 elementos): «2» |
| El mapa del buceo | 06 Caribe 17 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (32 elementos): «2» |
| El mapa del buceo | Mapa | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (26 elementos): «Leaflet» |
| El mapa del buceo | Satélite Disponible próximamente | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| El mapa del buceo | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (26 elementos): «Leaflet» |
| El mapa del buceo | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (31 elementos): «2» · clic forzado (otro elemento lo tapa) · hay 29 más iguales en la lista (no se prueban todos) |
| El mapa del buceo | 2 | Elemento div (role=button) | Funciona | Cambia la pantalla (8 elementos nuevos, 4 quitados) |
| El mapa del buceo | Mauritius – Cathedral | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» · hay 3 más iguales en la lista (no se prueban todos) |
| El mapa del buceo | Tofo – Manta Reef | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» |
| El mapa del buceo | Seguridad en el buceo | Enlace | Funciona | Abre #/legal/seguridad |
| El mapa del buceo | Zoom in | Enlace | Funciona | Muestra contenido nuevo (87 elementos): «2» |
| El mapa del buceo | Zoom out | Enlace | Funciona | Cambia la pantalla (10 elementos nuevos, 0 quitados) |
| El mapa del buceo | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |

#### Puntos de buceo · `#/puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Puntos de buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Puntos de buceo | Puntos de buceo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (68 elementos): «Todo el mundo» |
| Puntos de buceo | Zona Todo el mundo Europa (108) Asia (104) América (24) África y Mar Rojo (20) Oceanía (20) Caribe (17) | Desplegable | Funciona | Abre #/puntos?zone=Europa |
| Puntos de buceo | Para empezar | Botón | Funciona | Abre #/puntos?level=start |
| Puntos de buceo | Intermedio | Botón | Funciona | Abre #/puntos?level=mid |
| Puntos de buceo | Avanzado | Botón | Funciona | Abre #/puntos?level=adv |
| Puntos de buceo | Con centro que lo ofrece | Botón | Funciona | Abre #/puntos?only=centers |
| Puntos de buceo | Confirmación inmediata | Botón | Funciona | Abre #/puntos?only=instant |
| Puntos de buceo | Tipo de buceo Cualquier tipo Arrecifes Paredes Pecios y naufragios Cuevas y cavernas Cenotes Muck Canales Caño | Desplegable | Funciona | Abre #/puntos?type=arrecifes |
| Puntos de buceo | País Todos los países España (93) Filipinas (30) Indonesia (25) Malasia (15) Maldivas (13) Tailandia (13) Egip | Desplegable | Funciona | Abre #/puntos?country=Espa%C3%B1a |
| Puntos de buceo | Ordenar Recomendados Nombre A-Z Más profundos Menos profundos Mejor valorados | Desplegable | Funciona | Abre #/puntos?sort=name |
| Puntos de buceo | ¿Cómo ordenamos? | Enlace | Funciona | Abre #/legal/clasificacion |
| Puntos de buceo | #/punto?id=34 | Enlace | Funciona | Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Blue Hole, Dahab | Enlace | Funciona | Mismo enlace (#/punto?id=34) que «#/punto?id=34» en «Puntos de buceo»: Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Ver punto | Enlace | Funciona | Mismo enlace (#/punto?id=34) que «#/punto?id=34» en «Puntos de buceo»: Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Mostrar más puntos (281) | Botón | Funciona | Cambia su estado (disabled: sin atributo → vacío) · Muestra contenido nuevo (13 elementos): «Arrecifes Paredes Portitxol Norte Marina Alta · Xàbia · España Moderado Arrecife · Pared · Fondo arenoso Ubicación por v» |

#### Centros de buceo · `#/centros`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centros de buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Centros de buceo | Centros de buceo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (11 elementos): «Todos los países» |
| Centros de buceo | País Todos los países España (2) | Desplegable | Funciona | Abre #/centros?country=Espa%C3%B1a |
| Centros de buceo | Confirmación inmediata | Botón | Funciona | Abre #/centros?only=instant |
| Centros de buceo | Reserva online | Botón | Funciona | Abre #/centros?only=online |
| Centros de buceo | Plazas esta semana | Botón | Funciona | Abre #/centros?only=week |
| Centros de buceo | Cursos | Botón | Funciona | Abre #/centros?only=courses |
| Centros de buceo | Bautizos | Botón | Funciona | Abre #/centros?only=try |
| Centros de buceo | Viajes | Botón | Funciona | Abre #/centros?only=trips |
| Centros de buceo | Con reseñas | Botón | Funciona | Abre #/centros?only=reviews |
| Centros de buceo | Tipo de buceo Cualquier tipo de buceo Arrecifes Paredes Pecios y naufragios Cuevas y cavernas Cenotes Muck Can | Desplegable | Funciona | Abre #/centros?type=arrecifes |
| Centros de buceo | Ordenar Recomendados Mejor valorados Más reseñas Precio más bajo Nombre A-Z | Desplegable | Funciona | Abre #/centros?sort=rating |
| Centros de buceo | ¿Cómo ordenamos? | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Centros de buceo | Bajo petición Plazas esta semana | Enlace | Funciona | Abre #/centro?id=31 |
| Centros de buceo | Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Centros de buceo | Reservar | Enlace | Funciona | Abre #/reservar?center=31 |
| Centros de buceo | Bajo petición Plazas esta semana | Enlace | Funciona | Abre #/centro?id=32 |
| Centros de buceo | Escafandra Medes | Enlace | Funciona | Mismo enlace (#/centro?id=32) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=32 |
| Centros de buceo | Reservar | Enlace | Funciona | Abre #/reservar?center=32 |
| Centros de buceo | Dar de alta mi centro | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### ¿Qué inmersión te apetece? · `#/tipos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| ¿Qué inmersión te apetece? | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| ¿Qué inmersión te apetece? | Todos | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| ¿Qué inmersión te apetece? | Para empezar | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Con experiencia | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Avanzado y técnico | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| ¿Qué inmersión te apetece? | Paredes | Enlace | Funciona | Mismo enlace (#/tipos?t=paredes) que «Paredes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=paredes |
| ¿Qué inmersión te apetece? | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| ¿Qué inmersión te apetece? | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| ¿Qué inmersión te apetece? | Cenotes | Enlace | Funciona | Abre #/tipos?t=cenotes |
| ¿Qué inmersión te apetece? | Muck | Enlace | Funciona | Abre #/tipos?t=muck |
| ¿Qué inmersión te apetece? | Canales | Enlace | Funciona | Abre #/tipos?t=canales |
| ¿Qué inmersión te apetece? | Cañones | Enlace | Funciona | Abre #/tipos?t=canones |
| ¿Qué inmersión te apetece? | Pináculos | Enlace | Funciona | Mismo enlace (#/tipos?t=pinaculos) que «Pináculos» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pinaculos |
| ¿Qué inmersión te apetece? | Corrientes y deriva | Enlace | Funciona | Abre #/tipos?t=corrientes-y-deriva |
| ¿Qué inmersión te apetece? | Aguas profundas | Enlace | Funciona | Mismo enlace (#/tipos?t=aguas-profundas) que «Aguas profundas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=aguas-profundas |
| ¿Qué inmersión te apetece? | Lagos | Enlace | Funciona | Abre #/tipos?t=lagos |
| ¿Qué inmersión te apetece? | Pilares | Enlace | Funciona | Abre #/tipos?t=pilares |
| ¿Qué inmersión te apetece? | Nocturnas | Enlace | Funciona | Abre #/tipos?t=nocturnas |
| ¿Qué inmersión te apetece? | Playa y esnórquel | Enlace | Funciona | Abre #/tipos?t=playa-y-esnorquel |
| ¿Qué inmersión te apetece? | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| ¿Qué inmersión te apetece? | Muck | Enlace | Funciona | Mismo enlace (#/tipos?t=muck) que «Muck» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=muck |
| ¿Qué inmersión te apetece? | Lagos | Enlace | Funciona | Mismo enlace (#/tipos?t=lagos) que «Lagos» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=lagos |
| ¿Qué inmersión te apetece? | Pilares | Enlace | Funciona | Mismo enlace (#/tipos?t=pilares) que «Pilares» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=pilares |
| ¿Qué inmersión te apetece? | Paredes | Enlace | Funciona | Mismo enlace (#/tipos?t=paredes) que «Paredes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=paredes |
| ¿Qué inmersión te apetece? | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| ¿Qué inmersión te apetece? | Canales | Enlace | Funciona | Mismo enlace (#/tipos?t=canales) que «Canales» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=canales |
| ¿Qué inmersión te apetece? | Pináculos | Enlace | Funciona | Mismo enlace (#/tipos?t=pinaculos) que «Pináculos» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pinaculos |
| ¿Qué inmersión te apetece? | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| ¿Qué inmersión te apetece? | Cenotes | Enlace | Funciona | Mismo enlace (#/tipos?t=cenotes) que «Cenotes» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=cenotes |
| ¿Qué inmersión te apetece? | Cañones | Enlace | Funciona | Mismo enlace (#/tipos?t=canones) que «Cañones» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=canones |
| ¿Qué inmersión te apetece? | Corrientes y deriva | Enlace | Funciona | Mismo enlace (#/tipos?t=corrientes-y-deriva) que «Corrientes y deriva» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=corrientes-y-deriva |
| ¿Qué inmersión te apetece? | Aguas profundas | Enlace | Funciona | Mismo enlace (#/tipos?t=aguas-profundas) que «Aguas profundas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=aguas-profundas |

#### Viajes y vida a bordo · `#/experiencias`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Viajes y vida a bordo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Viajes y vida a bordo | Viajes y vida a bordo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (16 elementos): «Viaje 1 experiencia Costa Blanca España Experiencias de buceo organizadas por centros y profesionales. DESDE 290 € PRÓXI» |
| Viajes y vida a bordo | Todas | Botón | Funciona | Muestra contenido nuevo (8 elementos): «Viaje 1 experiencia Costa Blanca España Experiencias de buceo organizadas por centros y profesionales. DESDE 290 € PRÓXI» |
| Viajes y vida a bordo | Viaje | Botón | Funciona | Abre #/experiencias?kind=Viaje |
| Viajes y vida a bordo | Vida a bordo | Botón | Funciona | Abre #/experiencias?kind=Vida+a+bordo |
| Viajes y vida a bordo | Ordenar Con más salidas Precio más bajo Próxima salida Nombre A-Z | Desplegable | Funciona | Abre #/experiencias?sort=price |
| Viajes y vida a bordo | Viaje 1 experiencia | Enlace | Funciona | Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Costa Blanca | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Ver viajes | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Ver destino | Enlace | Funciona | Abre #/experiencia?id=5 · hay 3 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Empezar a publicar | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### ¿Te apetece bucear? · `#/top10`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| ¿Te apetece bucear? | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| ¿Te apetece bucear? | Radio 25 km 50 km 100 km 250 km 500 km | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Buscar» (sin efecto inmediato, correcto) |
| ¿Te apetece bucear? | Usar mi ubicación | Botón | Funciona | Muestra contenido nuevo (13 elementos): «1 ARRECIFES Cabo San Antonio Marina Alta · Xàbia · España 7–20 m Moderado ★ 4.4 (9) 1 centro 1,9 km Ver inmersión» |
| ¿Te apetece bucear? | Elegir en el mapa | Botón | Funciona | Abre la ventana «Elige tu ubicación» |
| ¿Te apetece bucear? | ¿Te apetece bucear? | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Buscar una localidad» (campo obligatorio) |
| ¿Te apetece bucear? | Marina Alta · Xàbia | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 ARRECIFES Piedras Rotas Marina Alta · Xàbia · España 7–20 m Fácil ★ 4.4 (9) 1 centro 0,8 km Ver inmersión» |
| ¿Te apetece bucear? | Marina Alta y Baixa · Calpe | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 19,3 km Ver inmersión» |
| ¿Te apetece bucear? | Canarias | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (9 elementos): «1 ARRECIFES Las Canteras, Gran Canaria Canarias · España Iniciación 48,3 km Ver inmersión» |
| ¿Te apetece bucear? | Palawan | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (4 elementos): «1 ARRECIFES El Nido – Cadlao Lagoon Palawan · Filipinas 5–20 m Principiante 72,9 km Ver inmersión» |
| ¿Te apetece bucear? | Comunitat Valenciana | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 25,7 km Ver inmersión» |
| ¿Te apetece bucear? | Andalucía | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (6 elementos): «1 ARRECIFES Costa del Sol, Málaga Andalucía · España Iniciación 52,4 km Ver inmersión» |
| ¿Te apetece bucear? | Marina Alta · Moraira | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 9,7 km Ver inmersión» |
| ¿Te apetece bucear? | Cebu | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (12 elementos): «1 ARRECIFES Moalboal – Sardine Run Cebu · Filipinas 5–25 m Principiante 28,1 km Ver inmersión» |
| ¿Te apetece bucear? | Cataluña | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (12 elementos): «1 ARRECIFES Medes – Tascons Islas Medes · España 6–25 m Intermedio ★ 4.8 (6) 1 centro 2,1 km Ver inmersión» |
| ¿Te apetece bucear? | Illes Balears | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (8 elementos): «1 PAREDES El Toro Mallorca · España 10–35 m Intermedio 12,9 km Ver inmersión» |

#### Planes de WORLDIVES · `#/planes`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Planes de WORLDIVES | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Planes de WORLDIVES | Gestionar mi plan | Enlace | Funciona | Abre #/admin?tab=plan |

#### Cómo funcionan los puntos · `#/como-funcionan-los-puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Cómo funcionan los puntos | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Cómo funcionan los puntos | Ver mis puntos | Enlace | Funciona | Mismo enlace (#/mis-puntos) que «Mis puntos» en «Encuentra tu próxima inmersión»: Abre #/mis-puntos |
| Cómo funcionan los puntos | Ver ventajas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Recompensas» en «Encuentra tu próxima inmersión»: Abre #/recompensas |

#### Aviso legal · `#/legal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Aviso legal | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Aviso legal | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Aviso legal | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Abre #/legal/reservas |
| Aviso legal | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Aviso legal | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Aviso legal | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Aviso legal | Normas de las reseñas | Enlace | Funciona | Abre #/legal/normas-resenas |
| Aviso legal | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Puntos WORLDIVES | Enlace | Funciona | Abre #/legal/puntos |
| Aviso legal | Declaración de accesibilidad | Enlace | Funciona | Abre #/legal/accesibilidad |
| Aviso legal | Contacto | Enlace | Funciona | Abre #/legal/contacto |
| Aviso legal | Créditos y licencias de terceros | Enlace | Funciona | Abre #/legal/creditos |
| Aviso legal | Condiciones de uso | Enlace | Funciona | Abre #/legal/terminos |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Leer | Botón | Funciona | Abre la ventana «Aviso legal» |
| Aviso legal | 1. Titular del sitio web | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 6 más iguales en la lista (no se prueban todos) |
| Aviso legal | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Crear cuenta · `#/registro`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Crear cuenta | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Crear cuenta | Buceador | Enlace | Funciona | Abre #/registro?tipo=recreational |
| Crear cuenta | Centro de buceo Publica tus salidas y cursos y gestiona tus reservas. | Enlace | Funciona | Abre #/registro?tipo=center |
| Crear cuenta | Profesional | Enlace | Funciona | Abre #/registro?tipo=freelance |
| Crear cuenta | Iniciar sesión | Enlace | Funciona | Abre #/cuenta |

#### Condiciones para centros y profesionales · `#/legal/condiciones-centros`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones para centros y profesionales | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones para centros y profesionales | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones para centros y profesionales | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones para centros y profesionales | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones para centros y profesionales | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones para centros y profesionales | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones para centros y profesionales | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones para centros y profesionales | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones para centros y profesionales | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones para centros y profesionales | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones para centros y profesionales | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones para centros y profesionales | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones para centros y profesionales | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones para centros y profesionales | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones para centros y profesionales | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones para centros y profesionales | Planes | Enlace | Funciona | Abre #/planes |
| Condiciones para centros y profesionales | Planes | Enlace | Funciona | Mismo enlace (#/planes) que «Planes» en «Condiciones para centros y profesionales»: Abre #/planes |
| Condiciones para centros y profesionales | normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones para centros y profesionales | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones para centros y profesionales | Leer | Botón | Funciona | Abre la ventana «Condiciones para centros y profesionales» |
| Condiciones para centros y profesionales | 1. Alta y verificación | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 18 más iguales en la lista (no se prueban todos) |
| Condiciones para centros y profesionales | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones para centros y profesionales | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Aviso legal · `#/legal/aviso-legal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Aviso legal | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Aviso legal | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Aviso legal | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Aviso legal | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Aviso legal | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Aviso legal | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Aviso legal | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Aviso legal | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Aviso legal | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Aviso legal | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Aviso legal | Condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/terminos) que «Condiciones de uso» en «Aviso legal»: Abre #/legal/terminos |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Leer | Botón | Funciona | Abre la ventana «Aviso legal» |
| Aviso legal | 1. Titular del sitio web | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 6 más iguales en la lista (no se prueban todos) |
| Aviso legal | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Política de privacidad · `#/legal/privacidad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Política de privacidad | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Política de privacidad | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Política de privacidad | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Política de privacidad | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Política de privacidad | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Política de privacidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de privacidad | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Política de privacidad | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Política de privacidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de privacidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Política de privacidad | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Política de privacidad | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Política de privacidad | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Política de privacidad | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Política de privacidad | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Política de privacidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de privacidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de privacidad | www.aepd.es | Enlace externo | Funciona | Enlace externo a www.aepd.es (no se abre: dirección https válida) |
| Política de privacidad | Leer | Botón | Funciona | Abre la ventana «Política de privacidad» |
| Política de privacidad | 1. Responsable | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 8 más iguales en la lista (no se prueban todos) |
| Política de privacidad | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Política de privacidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Política de cookies y servicios de terceros · `#/legal/cookies`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Política de cookies y servicios de terceros | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Política de cookies y servicios de terceros | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Política de cookies y servicios de terceros | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Política de cookies y servicios de terceros | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Política de cookies y servicios de terceros | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Política de cookies y servicios de terceros | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de cookies y servicios de terceros | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Política de cookies y servicios de terceros | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Política de cookies y servicios de terceros | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de cookies y servicios de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Política de cookies y servicios de terceros | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Política de cookies y servicios de terceros | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Política de cookies y servicios de terceros | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Política de cookies y servicios de terceros | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Política de cookies y servicios de terceros | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Política de cookies y servicios de terceros | Leer | Botón | Funciona | Abre la ventana «Política de cookies y servicios de terceros» |
| Política de cookies y servicios de terceros | Qué usamos | Enlace | Funciona | Cambia tabindex en h2#que-usamos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Política de cookies y servicios de terceros | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Política de cookies y servicios de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de uso para buceadores · `#/legal/condiciones-buceadores`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de uso para buceadores | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de uso para buceadores | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de uso para buceadores | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de uso para buceadores | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de uso para buceadores | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Leer | Botón | Funciona | Abre la ventana «Condiciones de uso para buceadores» |
| Condiciones de uso para buceadores | 1. Qué es WORLDIVES DISCOVERY | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 9 más iguales en la lista (no se prueban todos) |
| Condiciones de uso para buceadores | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de reserva, pago y cancelación · `#/legal/condiciones-reserva`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de reserva, pago y cancelación | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de reserva, pago y cancelación | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de reserva, pago y cancelación | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de reserva, pago y cancelación | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de reserva, pago y cancelación | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de reserva, pago y cancelación | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de reserva, pago y cancelación | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de reserva, pago y cancelación | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de reserva, pago y cancelación | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de reserva, pago y cancelación | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Leer | Botón | Funciona | Abre la ventana «Condiciones de reserva, pago y cancelación» |
| Condiciones de reserva, pago y cancelación | 1. Quién presta la actividad | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 7 más iguales en la lista (no se prueban todos) |
| Condiciones de reserva, pago y cancelación | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Denunciar contenido · `#/legal/denuncias`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Denunciar contenido | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Denunciar contenido | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Denunciar contenido | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Denunciar contenido | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Denunciar contenido | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Denunciar contenido | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Denunciar contenido | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Denunciar contenido | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Denunciar contenido | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Denunciar contenido | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Denunciar contenido | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Denunciar contenido | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Denunciar contenido | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Denunciar contenido | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Denunciar contenido | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Denunciar contenido | Formulario de denuncia | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Motivo» (elige una opción de la lista) · El navegador no deja enviarlo: «Explica por qué es ilegal o incumple las condiciones» (campo obligatorio) |
| Denunciar contenido | Motivo | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Enviar denuncia» (sin efecto inmediato, correcto) |
| Denunciar contenido | Leer | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Denunciar contenido | Qué necesitamos | Enlace | Funciona | Cambia tabindex en h2#que-necesitamos (sin atributo → -1) · hay 2 más iguales en la lista (no se prueban todos) |
| Denunciar contenido | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Denunciar contenido | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Seguridad en el buceo · `#/legal/seguridad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Seguridad en el buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Seguridad en el buceo | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Seguridad en el buceo | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Seguridad en el buceo | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Seguridad en el buceo | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Seguridad en el buceo | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Seguridad en el buceo | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Seguridad en el buceo | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Seguridad en el buceo | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Seguridad en el buceo | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Seguridad en el buceo | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Seguridad en el buceo | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Seguridad en el buceo | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Seguridad en el buceo | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Seguridad en el buceo | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Seguridad en el buceo | Leer | Botón | Funciona | Abre la ventana «Seguridad en el buceo» |
| Seguridad en el buceo | Antes de reservar | Enlace | Funciona | Cambia tabindex en h2#antes-de-reservar (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Seguridad en el buceo | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Seguridad en el buceo | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Cómo ordenamos los resultados · `#/legal/clasificacion`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Cómo ordenamos los resultados | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Cómo ordenamos los resultados | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Cómo ordenamos los resultados | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Cómo ordenamos los resultados | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Cómo ordenamos los resultados | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Cómo ordenamos los resultados | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Cómo ordenamos los resultados | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Cómo ordenamos los resultados | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Cómo ordenamos los resultados | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Cómo ordenamos los resultados | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Cómo ordenamos los resultados | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Cómo ordenamos los resultados | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Cómo ordenamos los resultados | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Cómo ordenamos los resultados | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Cómo ordenamos los resultados | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Cómo ordenamos los resultados | Leer | Botón | Funciona | Abre la ventana «Cómo ordenamos los resultados» |
| Cómo ordenamos los resultados | Directorio de centros | Enlace | Funciona | Cambia tabindex en h2#directorio-de-centros (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Cómo ordenamos los resultados | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Cómo ordenamos los resultados | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Blue Hole, Dahab · `#/punto?id=34`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Blue Hole, Dahab | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Blue Hole, Dahab | Puntos de buceo | Enlace | Funciona | Mismo enlace (#/puntos) que «Puntos de buceo» en «Encuentra tu próxima inmersión»: Abre #/puntos |
| Blue Hole, Dahab | África y Mar Rojo | Enlace | Funciona | Abre #/puntos?zone=%C3%81frica+y+Mar+Rojo |
| Blue Hole, Dahab | Abrir en el mapa | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Blue Hole, Dahab | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Encuentra tu próxima inmersión»: Abre #/cuenta |
| Blue Hole, Dahab | ¿Tienes un centro? Únete a WORLDIVES | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |
| Blue Hole, Dahab | Blue Hole Dahab Dahab · Egipto 6–60 m · Avanzado a 0 km | Enlace | Funciona | Abre #/punto?id=247 |
| Blue Hole, Dahab | Canyon Dahab Dahab · Egipto 8–30 m · Intermedio a 2,9 km | Enlace | Funciona | Abre #/punto?id=248 |
| Blue Hole, Dahab | Blue Hole, Dahab | Elemento div (role=button) | Funciona | Mueve o amplía el mapa |
| Blue Hole, Dahab | Mapa | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (8 elementos): «Leaflet» |
| Blue Hole, Dahab | Satélite | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Relieve orientativo (GEBCO). No sirve para navegar ni para la seguridad en el mar. Seguridad en el buceo» |
| Blue Hole, Dahab | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (10 elementos): «Leaflet» |
| Blue Hole, Dahab | Zoom in | Enlace | Funciona | Cambia la pantalla (5 elementos nuevos, 2 quitados) |
| Blue Hole, Dahab | Zoom out | Enlace | Funciona | Cambia la pantalla (5 elementos nuevos, 2 quitados) |
| Blue Hole, Dahab | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Blue Hole, Dahab | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Blue Hole, Dahab | Abrir en OpenStreetMap | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Blue Hole, Dahab | Proponer nueva posición | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Latitud Longitud Motivo» |
| Blue Hole, Dahab | Denunciar contenido | Botón | Funciona | Abre la ventana «Denunciar contenido» |

#### Bahía Coralina Centro de Buceo · `#/centro?id=31`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | Centros | Enlace | Funciona | Mismo enlace (#/centros) que «Centros» en «Encuentra tu próxima inmersión»: Abre #/centros |
| Bahía Coralina Centro de Buceo | Reservar | Enlace | Funciona | Mismo enlace (#/reservar?center=31) que «Reservar» en «Centros de buceo»: Abre #/reservar?center=31 |
| Bahía Coralina Centro de Buceo | Llamar | Enlace externo | Funciona | Teléfono +34600000101 |
| Bahía Coralina Centro de Buceo | Escribir | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | Lun, 19 oct 10:00 6 plazas | Enlace | Funciona | Abre #/reservar?center=31&service=7&slot=22 · POST /api/stats/track → 200 · hay 11 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Enviar solicitud | Enlace | Funciona | Abre #/reservar?center=31&service=7 · POST /api/stats/track → 200 · hay 3 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Añadir a una reserva | Enlace | Funciona | Abre #/reservar?center=31&service=8 · POST /api/stats/track → 200 |
| Bahía Coralina Centro de Buceo | Tres días en la reserva del Cabo de San Antonio | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Foto 1 de Bahía Coralina Centro de Buceo | Botón | Funciona | Abre la ventana «Bahía Coralina Centro de Buceo» · hay 2 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Foto 2 de Bahía Coralina Centro de Buceo | Botón | Funciona | Abre la ventana «Bahía Coralina Centro de Buceo» |
| Bahía Coralina Centro de Buceo | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» · hay 7 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34600000101 |
| Bahía Coralina Centro de Buceo | hola@bahiacoralina.example.com | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | bahiacoralina.example.com | Enlace externo | Funciona | Enlace externo a bahiacoralina.example.com (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo | Ver en el mapa | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo | Reservar con Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/reservar?center=31) que «Reservar» en «Centros de buceo»: Abre #/reservar?center=31 |
| Bahía Coralina Centro de Buceo | Denunciar contenido | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Bahía Coralina Centro de Buceo | Cabo San Antonio | Enlace | Funciona | Abre #/punto?id=329 · hay 5 más iguales en la lista (no se prueban todos) |

#### Bahía Coralina Centro de Buceo · `#/reservar?center=31`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | ← Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | Bautizo de buceo | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «No admite reservas ahora mismo» |
| Bahía Coralina Centro de Buceo | Curso Open Water (3 días) | Botón | Funciona | Muestra contenido nuevo (14 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Curso de Nitrox | Botón | Funciona | Muestra contenido nuevo (13 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Doble inmersión en barco | Botón | Funciona | Muestra contenido nuevo (26 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Inmersión al atardecer | Botón | Funciona | Muestra contenido nuevo (17 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Inmersión simple en barco | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «No admite reservas ahora mismo» |
| Bahía Coralina Centro de Buceo | Una persona menos | Botón | Desactivado (correcto) | Desactivado: es el límite del calendario o de la lista («Una persona menos») |
| Bahía Coralina Centro de Buceo | Una persona más | Botón | Desactivado (correcto) | No responde al ratón (pointer-events: none) y se ve atenuado; la pantalla explica: «Elige primero la actividad.» |
| Bahía Coralina Centro de Buceo | Elige una actividad | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Política de cancelación. Moderada: cancelación gratuita hasta 48 horas antes de la actividad; después no hay reembolso.» |
| Bahía Coralina Centro de Buceo | condiciones de reserva | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Bahía Coralina Centro de Buceo | condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34600000101 |

#### Costa Blanca · `#/experiencia?id=7`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Costa Blanca | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Costa Blanca | Experiencias | Enlace | Funciona | Mismo enlace (#/experiencias) que «Experiencias» en «Encuentra tu próxima inmersión»: Abre #/experiencias |
| Costa Blanca | BAHÍA CORALINA CENTRO DE BUCEO | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Costa Blanca | Solicitar plaza | Botón | Funciona | Abre #/experienciareserva?id=2 |
| Costa Blanca | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Costa Blanca | Publicar un viaje | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### Condiciones de reserva, pago y cancelación · `#/legal/reservas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de reserva, pago y cancelación | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de reserva, pago y cancelación | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de reserva, pago y cancelación | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de reserva, pago y cancelación | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de reserva, pago y cancelación | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de reserva, pago y cancelación | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de reserva, pago y cancelación | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de reserva, pago y cancelación | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de reserva, pago y cancelación | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de reserva, pago y cancelación | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Leer | Botón | Funciona | Abre la ventana «Condiciones de reserva, pago y cancelación» |
| Condiciones de reserva, pago y cancelación | 1. Quién presta la actividad | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 7 más iguales en la lista (no se prueban todos) |
| Condiciones de reserva, pago y cancelación | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Normas de las reseñas · `#/legal/normas-resenas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Normas de las reseñas | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Normas de las reseñas | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Normas de las reseñas | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Normas de las reseñas | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Normas de las reseñas | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Normas de las reseñas | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Normas de las reseñas | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Normas de las reseñas | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Normas de las reseñas | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Normas de las reseñas | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Normas de las reseñas | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Normas de las reseñas | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Normas de las reseñas | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Normas de las reseñas | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Normas de las reseñas | Leer | Botón | Funciona | Abre la ventana «Normas de las reseñas» |
| Normas de las reseñas | Quién puede escribir una reseña | Enlace | Funciona | Cambia tabindex en h2#quien-puede-escribir-una-resena (sin atributo → -1) · hay 4 más iguales en la lista (no se prueban todos) |
| Normas de las reseñas | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Puntos WORLDIVES · `#/legal/puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Puntos WORLDIVES | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Puntos WORLDIVES | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Puntos WORLDIVES | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Puntos WORLDIVES | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Puntos WORLDIVES | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Puntos WORLDIVES | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Puntos WORLDIVES | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Puntos WORLDIVES | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Puntos WORLDIVES | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Puntos WORLDIVES | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Puntos WORLDIVES | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Puntos WORLDIVES | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Puntos WORLDIVES | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Puntos WORLDIVES | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Puntos WORLDIVES | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Puntos WORLDIVES | Condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Puntos WORLDIVES | Leer | Botón | Funciona | Abre la ventana «Puntos WORLDIVES» |
| Puntos WORLDIVES | 1. Cómo se consiguen | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Puntos WORLDIVES | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Puntos WORLDIVES | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Declaración de accesibilidad · `#/legal/accesibilidad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Declaración de accesibilidad | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Declaración de accesibilidad | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Declaración de accesibilidad | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Declaración de accesibilidad | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Declaración de accesibilidad | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Declaración de accesibilidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Declaración de accesibilidad | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Declaración de accesibilidad | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Declaración de accesibilidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Declaración de accesibilidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Declaración de accesibilidad | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Declaración de accesibilidad | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Declaración de accesibilidad | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Declaración de accesibilidad | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Declaración de accesibilidad | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Declaración de accesibilidad | Leer | Botón | Funciona | Abre la ventana «Declaración de accesibilidad» |
| Declaración de accesibilidad | Situación actual | Enlace | Funciona | Cambia tabindex en h2#situacion-actual (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Declaración de accesibilidad | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Declaración de accesibilidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Contacto · `#/legal/contacto`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Contacto | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Contacto | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Contacto | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Contacto | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Contacto | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Contacto | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Contacto | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Contacto | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Contacto | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Contacto | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Contacto | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Contacto | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Contacto | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Contacto | Escríbenos | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Asunto» (elige una opción de la lista) · El navegador no deja enviarlo: «Tu nombre» (campo obligatorio) |
| Contacto | Ve a «Denunciar contenido» | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Asunto | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Enviar mensaje» (sin efecto inmediato, correcto) |
| Contacto | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Contacto | Leer | Botón | Funciona | Abre la ventana «Contacto» |
| Contacto | Quién somos | Enlace | Funciona | Cambia tabindex en h2#quien-somos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Contacto | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Créditos y licencias de terceros · `#/legal/creditos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Créditos y licencias de terceros | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Créditos y licencias de terceros | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Créditos y licencias de terceros | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Créditos y licencias de terceros | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Créditos y licencias de terceros | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Créditos y licencias de terceros | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Créditos y licencias de terceros | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Créditos y licencias de terceros | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Créditos y licencias de terceros | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Créditos y licencias de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Créditos y licencias de terceros | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Créditos y licencias de terceros | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Créditos y licencias de terceros | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Créditos y licencias de terceros | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Créditos y licencias de terceros | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Créditos y licencias de terceros | OpenStreetMap contributors | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Protomaps | Enlace externo | Funciona | Enlace externo a protomaps.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Esri World Imagery | Enlace externo | Funciona | Enlace externo a www.arcgis.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | gebco.net | Enlace externo | Funciona | Enlace externo a www.gebco.net (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leaflet.markercluster | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | protomaps-leaflet | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | qrcode | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | stripe-python | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | fontTools | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leer | Botón | Funciona | Abre la ventana «Créditos y licencias de terceros» |
| Créditos y licencias de terceros | Mapas y datos geográficos | Enlace | Funciona | Cambia tabindex en h2#mapas-y-datos-geograficos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Créditos y licencias de terceros | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Créditos y licencias de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de uso para buceadores · `#/legal/terminos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de uso para buceadores | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de uso para buceadores | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de uso para buceadores | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de uso para buceadores | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de uso para buceadores | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Leer | Botón | Funciona | Abre la ventana «Condiciones de uso para buceadores» |
| Condiciones de uso para buceadores | 1. Qué es WORLDIVES DISCOVERY | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 9 más iguales en la lista (no se prueban todos) |
| Condiciones de uso para buceadores | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Diego Arenas · ⌂ Resumen · `#/admin?tab=dashboard`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ⌂ Resumen | Ver mi ficha pública | Enlace | Funciona | Abre #/profesional?id=8 |
| Diego Arenas · ⌂ Resumen | Mi cuenta | Enlace | Funciona | Abre #/cuenta |
| Diego Arenas · ⌂ Resumen | ⌂ Resumen | Botón | Funciona | Muestra contenido nuevo (4 elementos): «Cargando…» |
| Diego Arenas · ⌂ Resumen | ☰ Reservas 2 | Botón | Funciona | Abre #/admin?tab=bookings |
| Diego Arenas · ⌂ Resumen | ▦ Planning | Botón | Funciona | Abre #/admin?tab=planning |
| Diego Arenas · ⌂ Resumen | ▣ Mi agenda | Botón | Funciona | Abre #/admin?tab=agenda |
| Diego Arenas · ⌂ Resumen | ◈ Servicios y tarifas | Botón | Funciona | Abre #/admin?tab=services |
| Diego Arenas · ⌂ Resumen | ✈ Experiencias y solicitudes | Botón | Funciona | Abre #/admin?tab=experiences |
| Diego Arenas · ⌂ Resumen | € Cobros y pagos | Botón | Funciona | Abre #/admin?tab=payments |
| Diego Arenas · ⌂ Resumen | ✦ Perfil público | Botón | Funciona | Abre #/admin?tab=profile |
| Diego Arenas · ⌂ Resumen | ◍ Vídeos y vida marina | Botón | Funciona | Abre #/admin?tab=marina |
| Diego Arenas · ⌂ Resumen | ✆ Avisos y WhatsApp | Botón | Funciona | Abre #/admin?tab=avisos |
| Diego Arenas · ⌂ Resumen | ✉ Solicitudes de información | Botón | Funciona | Abre #/admin?tab=requests |
| Diego Arenas · ⌂ Resumen | ◑ Estadísticas | Botón | Funciona | Abre #/admin?tab=stats |
| Diego Arenas · ⌂ Resumen | ⇩ Herramientas | Botón | Funciona | Abre #/admin?tab=tools |
| Diego Arenas · ⌂ Resumen | § Datos fiscales y seguro | Botón | Funciona | Abre #/admin?tab=fiscal |
| Diego Arenas · ⌂ Resumen | ◆ Mi plan | Botón | Funciona | Abre #/admin?tab=plan |
| Diego Arenas · ⌂ Resumen | Log Book | Enlace | Funciona | Abre #/logbook |
| Diego Arenas · ⌂ Resumen | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Diego Arenas · ⌂ Resumen | Nuevo servicio | Botón | Funciona | Abre #/admin?tab=services |
| Diego Arenas · ⌂ Resumen | Ver planning | Botón | Funciona | Abre #/admin?tab=planning |
| Diego Arenas · ⌂ Resumen | Planning completo | Botón | Funciona | Abre #/admin?tab=planning |
| Diego Arenas · ⌂ Resumen | Gestionar | Botón | Funciona | Abre #/admin?tab=experiences |
| Diego Arenas · ⌂ Resumen | Completar mi ficha | Botón | Funciona | Abre #/admin?tab=profile |
| Diego Arenas · ⌂ Resumen | Copiar enlace de mi ficha | Botón | Funciona | Aviso: «Enlace copiado.» |

#### Hola, Diego · `#/area`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Hola, Diego | Explorador 0 puntos | Enlace | Funciona | Abre #/recompensas |
| Hola, Diego | Mi panel | Enlace | Funciona | Abre #/admin?tab=dashboard |
| Hola, Diego | Log Book | Enlace | Funciona | Mismo enlace (#/logbook) que «Log Book» en «Diego Arenas · ⌂ Resumen»: Abre #/logbook |
| Hola, Diego | Recompensas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Hola, Diego»: Abre #/recompensas |
| Hola, Diego | Mis puntos | Enlace | Funciona | Abre #/mis-puntos |
| Hola, Diego | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Hola, Diego | Reservar una inmersión | Enlace | Funciona | Abre #/centros |
| Hola, Diego | 0 próximas reservas | Botón | Funciona | Desplaza la página |
| Hola, Diego | 0 avisos sin leer | Botón | Funciona | Desplaza la página |
| Hola, Diego | 0 documentos | Enlace | Funciona | Abre #/cuenta?docs=1 |
| Hola, Diego | Buscar centros | Enlace | Funciona | Mismo enlace (#/centros) que «Reservar una inmersión» en «Hola, Diego»: Abre #/centros |
| Hola, Diego | Cerca de mí | Enlace | Funciona | Abre #/top10 |
| Hola, Diego | Próximas 0 | Botón | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) · Cambia el texto: «Ver las 0 reservas» |
| Hola, Diego | Historial 0 | Botón | Funciona | Cambia su estado (class: sin atributo → is-on) · Cambia la pantalla (0 elementos nuevos, 1 quitados) |
| Hola, Diego | Explorar | Enlace | Funciona | Abre #/experiencias |
| Hola, Diego | Completar mi ficha | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Hola, Diego | Gestionar | Enlace | Funciona | Mismo enlace (#/cuenta?docs=1) que «0 documentos» en «Hola, Diego»: Abre #/cuenta?docs=1 |

#### Hola, Diego › Historial · `#/area` (1 clic en subpestaña)

Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).

#### Tu ficha de buceador · `#/cuenta`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Tu ficha de buceador | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Hola, Diego»: Abre #/recompensas |
| Tu ficha de buceador | Datos personales | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Nombre y apellidos» (campo obligatorio) |
| Tu ficha de buceador | Prefijo del país | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Idioma preferido | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Nivel de certificación | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | ¿Sueles alquilar equipo? | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Tipo de traje | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Documentación | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Título» (campo obligatorio) · El navegador no deja enviarlo: «Archivo (PDF o imagen, máximo 10 MB)» (falta el archivo) |
| Tu ficha de buceador | Tipo | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Seguridad | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Contraseña actual» (campo obligatorio) · El navegador no deja enviarlo: «Nueva contraseña» (campo obligatorio) |
| Tu ficha de buceador | Activar | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Tu contraseña» (campo obligatorio) |
| Tu ficha de buceador | Descargar mis datos (ZIP) | Enlace | Funciona | Descarga /api/account/export?format=zip (200, application/zip) |
| Tu ficha de buceador | Privacidad | Enlace | Funciona | Abre #/legal/privacidad |
| Tu ficha de buceador | Condiciones de uso | Enlace | Funciona | Abre #/legal/condiciones-buceadores |
| Tu ficha de buceador | Condiciones de reserva | Enlace | Funciona | Abre #/legal/condiciones-reserva |
| Tu ficha de buceador | Cookies | Enlace | Funciona | Abre #/legal/cookies |
| Tu ficha de buceador | Abrir el panel | Enlace | Funciona | Mismo enlace (#/admin) que «Mi panel» en «Hola, Diego»: Abre #/admin?tab=dashboard |
| Tu ficha de buceador | Borrar mi cuenta para siempre | Botón | Funciona | [probado al final del papel] Abre la ventana «Borrar mi cuenta para siempre» |
| Tu ficha de buceador | Cerrar sesión | Botón | Funciona | [probado al final del papel] Abre #/ · POST /api/auth/logout → 200 · cierra la sesión o cambia la cuenta: se vuelve a iniciar sesión |

#### Log Book · `#/logbook`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Log Book | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Hola, Diego»: Abre #/recompensas |
| Log Book | Exportar CSV | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Tu historial de inmersiones. Las reservas completadas se añaden solas; el resto, en un momento.» |
| Log Book | Nueva inmersión | Botón | Funciona | Abre la ventana «Nueva inmersión» |
| Log Book | Añadir mi primera inmersión | Botón | Funciona | Abre la ventana «Nueva inmersión» |

#### Recompensas · `#/recompensas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Recompensas | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Hola, Diego»: Abre #/recompensas |
| Recompensas | Cómo funcionan | Enlace | Funciona | Abre #/como-funcionan-los-puntos |
| Recompensas | Canjear | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Linterna para la nocturna» · hay 2 más iguales en la lista (no se prueban todos) |
| Recompensas | Canjear | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Te faltan 150 puntos» |

#### Mis puntos · `#/mis-puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Mis puntos | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Hola, Diego»: Abre #/recompensas |
| Mis puntos | Ver ventajas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Hola, Diego»: Abre #/recompensas |
| Mis puntos | Más información sobre los puntos | Enlace | Funciona | Mismo enlace (#/como-funcionan-los-puntos) que «Cómo funcionan» en «Recompensas»: Abre #/como-funcionan-los-puntos |

#### Diego Arenas · ☰ Reservas · `#/admin?tab=bookings`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ☰ Reservas | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · ☰ Reservas | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Diego Arenas · ☰ Reservas | Hoy | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Las reservas y solicitudes de tus servicios. Hoy Próximos 7 días Solicitudes pendientes 2 P» |
| Diego Arenas · ☰ Reservas | Próximos 7 días | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Las reservas y solicitudes de tus servicios. Hoy Próximos 7 días Solicitudes pendientes 2 P» |
| Diego Arenas · ☰ Reservas | Solicitudes pendientes 2 | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Las reservas y solicitudes de tus servicios. Hoy Próximos 7 días Solicitudes pendientes 2 P» |
| Diego Arenas · ☰ Reservas | Por cobrar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Las reservas y solicitudes de tus servicios. Hoy Próximos 7 días Solicitudes pendientes 2 P» |
| Diego Arenas · ☰ Reservas | Todas las próximas | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Las reservas y solicitudes de tus servicios. Hoy Próximos 7 días Solicitudes pendientes 2 P» |
| Diego Arenas · ☰ Reservas | Historial | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Las reservas y solicitudes de tus servicios. Hoy Próximos 7 días Solicitudes pendientes 2 P» |
| Diego Arenas · ☰ Reservas | Actividad | Desplegable | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Las reservas y solicitudes de tus servicios. Hoy Próximos 7 días Solicitudes pendientes 2 P» |
| Diego Arenas · ☰ Reservas | Registrar cobro | Botón | Funciona | Abre la ventana «Registrar pago» |
| Diego Arenas · ☰ Reservas | Aceptar | Botón | Funciona | Aviso: «Reserva aceptada.» · Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Las reservas y solicitudes de tus servicios. Hoy Próximos 7 días Solicitudes pendientes 1 P» · POST /api/bookings/1284/status → 200 |
| Diego Arenas · ☰ Reservas | Rechazar | Botón | Funciona | Abre la ventana «Rechazar la solicitud» |

#### Diego Arenas · ☰ Reservas › Historial · `#/admin?tab=bookings` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ☰ Reservas › Historial | + Nueva reserva | Botón | Funciona | Aviso: «No tienes permisos para realizar esta acción.» · GET /api/center/extras → 403 «No tienes permisos para realizar esta acción.» |

#### Diego Arenas · ☰ Reservas › Todas las próximas · `#/admin?tab=bookings` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ☰ Reservas › Todas las próximas | Aceptar | Botón | Funciona | Aviso: «Reserva aceptada.» · Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Las reservas y solicitudes de tus servicios. Hoy Próximos 7 días Solicitudes pendientes 1 P» · POST /api/bookings/1285/status → 200 |
| Diego Arenas · ☰ Reservas › Todas las próximas | Rechazar | Botón | Funciona | Abre la ventana «Rechazar la solicitud» |

#### Diego Arenas · ☰ Reservas › Por cobrar · `#/admin?tab=bookings` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ☰ Reservas › Por cobrar | ☰ Reservas 1 | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Cargando reservas…» |
| Diego Arenas · ☰ Reservas › Por cobrar | Solicitudes pendientes 1 | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión de reservas Reservas Las reservas y solicitudes de tus servicios. Hoy Próximos 7 días Solicitudes pendientes 1 P» |

#### Diego Arenas · ☰ Reservas › Solicitudes pendientes · `#/admin?tab=bookings` (1 clic en subpestaña)

Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).

#### Diego Arenas · ☰ Reservas › Hoy · `#/admin?tab=bookings` (1 clic en subpestaña)

Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).

#### Diego Arenas · ▦ Planning · `#/admin?tab=planning`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ▦ Planning | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · ▦ Planning | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Diego Arenas · ▦ Planning | Mes anterior | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Diego Arenas · ▦ Planning | Mes siguiente | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Diego Arenas · ▦ Planning | Mes | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| Diego Arenas · ▦ Planning | Lista | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| Diego Arenas · ▦ Planning | Crear cartel | Botón | Funciona | Abre la ventana «Crear cartel para redes» |
| Diego Arenas · ▦ Planning | Abr | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» · hay 4 más iguales en la lista (no se prueban todos) |
| Diego Arenas · ▦ Planning | May | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Diego Arenas · ▦ Planning | Oct 3 | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Diego Arenas · ▦ Planning | Nov 2 | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» · hay 3 más iguales en la lista (no se prueban todos) |
| Diego Arenas · ▦ Planning | Dic | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Cargando el planning…» |
| Diego Arenas · ▦ Planning | Jueves, 1 de octubre | Botón | Funciona | Abre la ventana «Jueves, 1 de octubre» · Cambia su estado (class: pl-cell  is-past  → pl-cell is-past is-open) · hay 10 más iguales en la lista (no se prueban todos) |
| Diego Arenas · ▦ Planning | Viernes, 2 de octubre | Botón | Funciona | Abre la ventana «Viernes, 2 de octubre» · Cambia su estado (class: pl-cell  is-past  → pl-cell is-past is-open) |
| Diego Arenas · ▦ Planning | Martes, 13 de octubre | Botón | Funciona | Abre la ventana «Martes, 13 de octubre» · Cambia su estado (class: pl-cell is-today   → pl-cell is-today is-open) |
| Diego Arenas · ▦ Planning | Miércoles, 14 de octubre | Botón | Funciona | Abre la ventana «Miércoles, 14 de octubre» · Cambia su estado (class: pl-cell    → pl-cell is-open) · hay 11 más iguales en la lista (no se prueban todos) |
| Diego Arenas · ▦ Planning | Jueves, 15 de octubre | Botón | Funciona | Abre la ventana «Jueves, 15 de octubre» · Cambia su estado (class: pl-cell    → pl-cell is-open) |
| Diego Arenas · ▦ Planning | Viernes, 16 de octubre: 0 salidas, 2 buceadores | Botón | Funciona | Abre la ventana «Viernes, 16 de octubre» · Cambia su estado (class: pl-cell   has-events → pl-cell has-events is-open) · hay 3 más iguales en la lista (no se prueban todos) |
| Diego Arenas · ▦ Planning | Sábado, 17 de octubre: 1 salidas, 0 buceadores | Botón | Funciona | Abre la ventana «Sábado, 17 de octubre» · Cambia su estado (class: pl-cell   has-events → pl-cell has-events is-open) |

#### Diego Arenas · ▦ Planning › Lista · `#/admin?tab=planning` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ▦ Planning › Lista | 16 Vie Viernes, 16 de octubre 0 salidas · 2 buceadores › | Botón | Funciona | Abre la ventana «Viernes, 16 de octubre» · Cambia su estado (class: pl-lday-head → pl-lday-head is-open) · hay 3 más iguales en la lista (no se prueban todos) |
| Diego Arenas · ▦ Planning › Lista | 17 | Botón | Funciona | Abre la ventana «Sábado, 17 de octubre» · Cambia su estado (class: pl-lday-head → pl-lday-head is-open) |

#### Diego Arenas · ▣ Mi agenda · `#/admin?tab=agenda`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ▣ Mi agenda | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · ▣ Mi agenda | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Diego Arenas · ▣ Mi agenda | Mes | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Agenda Mi agenda Horario habitual: lun a sáb · Horario de Cancun Mes Lista Horario y temporadas» |
| Diego Arenas · ▣ Mi agenda | Lista | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Agenda Mi agenda Horario habitual: lun a sáb · Horario de Cancun Mes Lista Horario y temporadas» |
| Diego Arenas · ▣ Mi agenda | Horario y temporadas | Botón | Funciona | Abre la ventana «Horario y temporadas» |
| Diego Arenas · ▣ Mi agenda | Mes anterior | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Agenda Mi agenda Horario habitual: lun a sáb · Horario de Cancun Mes Lista Horario y temporadas» |
| Diego Arenas · ▣ Mi agenda | Mes siguiente | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Agenda Mi agenda Horario habitual: lun a sáb · Horario de Cancun Mes Lista Horario y temporadas» |
| Diego Arenas · ▣ Mi agenda | 1 | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Agenda Mi agenda Horario habitual: lun a sáb · Horario de Cancun Mes Lista Horario y temporadas» · hay 29 más iguales en la lista (no se prueban todos) |
| Diego Arenas · ▣ Mi agenda | 2 | Botón | Funciona | Muestra contenido nuevo (3 elementos): «Agenda Mi agenda Horario habitual: lun a sáb · Horario de Cancun Mes Lista Horario y temporadas» |

#### Diego Arenas · ◈ Servicios y tarifas · `#/admin?tab=services`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ◈ Servicios y tarifas | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · ◈ Servicios y tarifas | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Diego Arenas · ◈ Servicios y tarifas | + Nuevo servicio | Botón | Funciona | Abre la ventana «Nuevo servicio» |
| Diego Arenas · ◈ Servicios y tarifas | Todos | Botón | Funciona | Muestra contenido nuevo (4 elementos): «Cenote por la mañana o por la tarde Inmersión A la venta 200 € por día Bajo petición · el centro responde en 24 h Hasta » |
| Diego Arenas · ◈ Servicios y tarifas | Inmersión | Botón | Funciona | Cambia su estado (class: svc-chip  → svc-chip active) · Muestra contenido nuevo (3 elementos): «Cenote por la mañana o por la tarde Inmersión A la venta 200 € por día Bajo petición · el centro responde en 24 h Hasta » |
| Diego Arenas · ◈ Servicios y tarifas | Bautizo / experiencia | Botón | Funciona | Cambia su estado (class: svc-chip  → svc-chip active) · Muestra contenido nuevo (2 elementos): «Sesión de fotos y vídeo bajo el agua Bautizo / experiencia · 3 h A la venta 90 € por persona Bajo petición · el centro r» |
| Diego Arenas · ◈ Servicios y tarifas | Ver como cliente | Enlace | Funciona | Abre #/reservar-dias?service=16 |
| Diego Arenas · ◈ Servicios y tarifas | Mi agenda | Botón | Funciona | Abre #/admin?tab=agenda |
| Diego Arenas · ◈ Servicios y tarifas | Editar | Botón | Funciona | Abre la ventana «Editar servicio» · hay 1 más iguales en la lista (no se prueban todos) |
| Diego Arenas · ◈ Servicios y tarifas | Ver como cliente | Enlace | Funciona | Abre #/reservar-dias?service=15 |
| Diego Arenas · ◈ Servicios y tarifas | Mi agenda | Botón | Funciona | Abre #/admin?tab=agenda |
| Diego Arenas · ◈ Servicios y tarifas | Editar | Botón | Funciona | Abre la ventana «Editar servicio» |
| Diego Arenas · ◈ Servicios y tarifas | Ver las 4 | Botón | Funciona | Abre la ventana «Salidas de Sesión de fotos y vídeo bajo el agua» |
| Diego Arenas · ◈ Servicios y tarifas | Sáb, 17 oct 11:00 2 libres | Botón | Funciona | Abre la ventana «Editar salida» · hay 1 más iguales en la lista (no se prueban todos) |
| Diego Arenas · ◈ Servicios y tarifas | Sáb, 24 oct 11:00 2 libres | Botón | Funciona | Abre la ventana «Editar salida» |
| Diego Arenas · ◈ Servicios y tarifas | + Salida | Botón | Funciona | Abre la ventana «Nueva salida» |
| Diego Arenas · ◈ Servicios y tarifas | Agenda | Botón | Funciona | Abre la ventana «Salidas de Sesión de fotos y vídeo bajo el agua» |
| Diego Arenas · ◈ Servicios y tarifas | + Nuevo servicio Inmersión, curso, bautizo, viaje… | Botón | Funciona | Abre la ventana «Nuevo servicio» |

#### Diego Arenas · ✈ Experiencias y solicitudes · `#/admin?tab=experiences`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ✈ Experiencias y solicitudes | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · ✈ Experiencias y solicitudes | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Diego Arenas · ✈ Experiencias y solicitudes | + Nueva experiencia | Botón | Funciona | Abre la ventana «Nueva experiencia» |
| Diego Arenas · ✈ Experiencias y solicitudes | Añadir foto | Botón | Funciona | Abre la ventana «Foto de la experiencia» |
| Diego Arenas · ✈ Experiencias y solicitudes | Editar | Botón | Funciona | Abre la ventana «Editar experiencia» |
| Diego Arenas · ✈ Experiencias y solicitudes | Ocultar | Botón | Funciona | Pide confirmación «¿Ocultar esta experiencia de la web?» (cancelado) |
| Diego Arenas · ✈ Experiencias y solicitudes | Añadir foto | Botón | Funciona | Abre la ventana «Foto de la experiencia» |
| Diego Arenas · ✈ Experiencias y solicitudes | Ver en la web | Enlace | Funciona | Abre #/experiencia?id=3 |
| Diego Arenas · ✈ Experiencias y solicitudes | Editar | Botón | Funciona | Abre la ventana «Editar experiencia» |
| Diego Arenas · ✈ Experiencias y solicitudes | Ocultar | Botón | Funciona | Pide confirmación «¿Ocultar esta experiencia de la web?» (cancelado) |

#### Diego Arenas · € Cobros y pagos · `#/admin?tab=payments`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · € Cobros y pagos | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · € Cobros y pagos | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Diego Arenas · € Cobros y pagos | Activar los cobros online | Botón | Depende de clave pendiente | Clave pendiente: Stripe · Aviso: «Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el servidor).» · POST /api/payments/connect/onboard → 400 «Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el ser» |
| Diego Arenas · € Cobros y pagos | Datos del prestador del servicio | Formulario | Funciona | Enviado vacío · Aviso: «Datos guardados. Saldrán en los justificantes.» · POST /api/provider/payment-profile → 200 |
| Diego Arenas · € Cobros y pagos | Flexible Gratis hasta 24 h antes | Botón | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) · Cambia el texto: «Cancelación gratuita hasta 24 horas antes de la actividad; después no hay reembolso.» · Cambia el valor de «Cancelación gratuita hasta (horas antes)» (48 → 24) |
| Diego Arenas · € Cobros y pagos | Moderada Gratis hasta 48 h antes | Botón | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) · Cambia el texto: «Cancelación gratuita hasta 2 días antes de la actividad; después no hay reembolso.» |
| Diego Arenas · € Cobros y pagos | Estricta Gratis hasta 7 días antes | Botón | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) · Cambia el texto: «Cancelación gratuita hasta 7 días antes de la actividad; después no hay reembolso.» · Cambia el valor de «Cancelación gratuita hasta (horas antes)» (48 → 168) |
| Diego Arenas · € Cobros y pagos | Guardar política | Botón | Funciona | Aviso: «Política de cancelación guardada. Se aplica a las reservas nuevas.» · POST /api/provider/cancellation-policy → 200 |
| Diego Arenas · € Cobros y pagos | Condiciones para centros | Enlace | Funciona | Abre una pestaña nueva /?lang=es&_=129#/legal/condiciones-centros |

#### Diego Arenas · ✦ Perfil público · `#/admin?tab=profile`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ✦ Perfil público | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · ✦ Perfil público | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Diego Arenas · ✦ Perfil público | Ver cómo queda | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · ✦ Perfil público | Tu ficha de profesional | Formulario | Funciona | Enviado vacío · Aviso: «Ficha pública guardada.» · Cambia su estado (disabled: sin atributo → vacío) · Muestra contenido nuevo (1 elementos): «PERFIL PÚBLICO Tu ficha de profesional Es lo que ve un buceador al pulsar tu nombre en una experiencia o servicio. Ver c» · POST /api/provider/profile → 200 |

#### Diego Arenas · ◍ Vídeos y vida marina · `#/admin?tab=marina`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ◍ Vídeos y vida marina | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · ◍ Vídeos y vida marina | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |

#### Diego Arenas · ✆ Avisos y WhatsApp · `#/admin?tab=avisos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ✆ Avisos y WhatsApp | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · ✆ Avisos y WhatsApp | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Diego Arenas · ✆ Avisos y WhatsApp | Al cancelar una salida, por defecto | Formulario | Funciona | Enviado vacío · Aviso: «Ajustes guardados.» · POST /api/avisos/ajustes → 200 |
| Diego Arenas · ✆ Avisos y WhatsApp | Hora del recordatorio | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |

#### Diego Arenas · ✉ Solicitudes de información · `#/admin?tab=requests`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ✉ Solicitudes de información | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · ✉ Solicitudes de información | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |

#### Diego Arenas · ◑ Estadísticas · `#/admin?tab=stats`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ◑ Estadísticas | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · ◑ Estadísticas | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Diego Arenas · ◑ Estadísticas | Periodo Últimos 30 días Últimos 90 días Últimos 365 días | Desplegable | Funciona | Muestra contenido nuevo (1 elementos): «Estadísticas Cómo te encuentran los buceadores Datos agregados, sin datos personales. Disponibles en todos los planes. P» |

#### Diego Arenas · ⇩ Herramientas · `#/admin?tab=tools`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ⇩ Herramientas | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · ⇩ Herramientas | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Diego Arenas · ⇩ Herramientas | Clientes | Enlace | Funciona | Descarga /api/center/export?kind=clients (200, text/csv) |
| Diego Arenas · ⇩ Herramientas | Reservas | Enlace | Funciona | Descarga /api/center/export?kind=bookings (200, text/csv) |
| Diego Arenas · ⇩ Herramientas | Servicios | Enlace | Funciona | Descarga /api/center/export?kind=services (200, text/csv) |
| Diego Arenas · ⇩ Herramientas | Agenda | Enlace | Funciona | Descarga /api/center/export?kind=agenda (200, text/csv) |
| Diego Arenas · ⇩ Herramientas | Pagos | Enlace | Funciona | Descarga /api/center/export?kind=payments (200, text/csv) |
| Diego Arenas · ⇩ Herramientas | Generar dirección | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Herramientas Exportar, calendario, widget e importación Exportar mis datos (CSV) Disponible siempre, en cualquier plan. » · POST /api/provider/ical/regenerate → 200 |
| Diego Arenas · ⇩ Herramientas | Copiar | Botón | Funciona | Aviso: «Copiado.» |
| Diego Arenas · ⇩ Herramientas | Compartir por WhatsApp | Enlace externo | Funciona | Enlace externo a wa.me (no se abre: dirección https válida) |
| Diego Arenas · ⇩ Herramientas | Copiar | Botón | Funciona | Aviso: «Copiado.» |
| Diego Arenas · ⇩ Herramientas | Descargo de responsabilidad | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Título» (campo obligatorio) · El navegador no deja enviarlo: «Texto» (campo obligatorio) |

#### Diego Arenas · § Datos fiscales y seguro · `#/admin?tab=fiscal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · § Datos fiscales y seguro | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · § Datos fiscales y seguro | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Diego Arenas · § Datos fiscales y seguro | Seguro de responsabilidad civil | Formulario | Funciona | Enviado vacío · Aviso: «Datos guardados.» · Muestra contenido nuevo (1 elementos): «Datos fiscales y verificación Datos del prestador (DAC7) y seguro La normativa europea DAC7 obliga a las plataformas a i» · POST /api/provider/fiscal → 200 |
| Diego Arenas · § Datos fiscales y seguro | Tipo de prestador | Desplegable | Funciona | Cambia hidden en div.field (vacío → sin atributo) |

#### Diego Arenas · ◆ Mi plan · `#/admin?tab=plan`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Diego Arenas · ◆ Mi plan | Ver mi ficha pública | Enlace | Funciona | Mismo enlace (#/profesional?id=8) que «Ver mi ficha pública» en «Diego Arenas · ⌂ Resumen»: Abre #/profesional?id=8 |
| Diego Arenas · ◆ Mi plan | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Diego Arenas · ⌂ Resumen»: Abre #/cuenta |
| Diego Arenas · ◆ Mi plan | Comparar planes | Enlace | Funciona | Abre #/planes |

#### Lukas Becker · `#/reserva?id=1283`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Lukas Becker | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Lukas Becker | Reservas | Enlace | Funciona | Abre #/admin?tab=bookings |
| Lukas Becker | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1283/receipt.pdf (200, application/pdf) |
| Lukas Becker | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1283/diver-sheet.pdf (200, application/pdf) |
| Lukas Becker | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Lukas Becker | Cambiar fecha u hora | Botón | Funciona | Aviso: «No hay otras salidas de este servicio. Programa una nueva salida antes de cambiar la reserva.» |
| Lukas Becker | Cancelar reserva | Botón | Funciona | Abre la ventana «Cancelar la reserva» |
| Lukas Becker | PDF | Enlace | Funciona | Descarga /api/bookings/1283/diver-sheet.pdf (200, application/pdf) |
| Lukas Becker | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Lukas Becker»: Abre #/admin?tab=bookings |

#### Chloé Martin · `#/reserva?id=1284`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Chloé Martin | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Chloé Martin | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Lukas Becker»: Abre #/admin?tab=bookings |
| Chloé Martin | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1284/receipt.pdf (200, application/pdf) |
| Chloé Martin | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1284/diver-sheet.pdf (200, application/pdf) |
| Chloé Martin | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Chloé Martin | Cambiar fecha u hora | Botón | Funciona | Aviso: «No hay otras salidas de este servicio. Programa una nueva salida antes de cambiar la reserva.» |
| Chloé Martin | Aceptar | Botón | Funciona | Aviso: «Reserva confirmada.» · Muestra contenido nuevo (2 elementos): «← Volver» · POST /api/bookings/1284/status → 200 |
| Chloé Martin | Rechazar | Botón | Funciona | Abre la ventana «Rechazar la solicitud» |
| Chloé Martin | PDF | Enlace | Funciona | Descarga /api/bookings/1284/diver-sheet.pdf (200, application/pdf) |
| Chloé Martin | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Lukas Becker»: Abre #/admin?tab=bookings |

#### Bea Navarro · `#/reserva?id=1285`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bea Navarro | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bea Navarro | Reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Lukas Becker»: Abre #/admin?tab=bookings |
| Bea Navarro | Justificante PDF + QR | Enlace | Funciona | Descarga /api/bookings/1285/receipt.pdf (200, application/pdf) |
| Bea Navarro | Ficha operativa PDF | Enlace | Funciona | Descarga /api/bookings/1285/diver-sheet.pdf (200, application/pdf) |
| Bea Navarro | Enviar aviso al cliente | Botón | Funciona | Abre la ventana «Enviar aviso al cliente» |
| Bea Navarro | Cambiar fecha u hora | Botón | Funciona | Aviso: «No hay otras salidas de este servicio. Programa una nueva salida antes de cambiar la reserva.» |
| Bea Navarro | Aceptar | Botón | Funciona | Aviso: «Reserva confirmada.» · Muestra contenido nuevo (2 elementos): «← Volver» · POST /api/bookings/1285/status → 200 |
| Bea Navarro | Rechazar | Botón | Funciona | Abre la ventana «Rechazar la solicitud» |
| Bea Navarro | PDF | Enlace | Funciona | Descarga /api/bookings/1285/diver-sheet.pdf (200, application/pdf) |
| Bea Navarro | ← Volver a reservas | Enlace | Funciona | Mismo enlace (#/admin?tab=bookings) que «Reservas» en «Lukas Becker»: Abre #/admin?tab=bookings |

### Administración (cuenta creada para la prueba)

62 pantallas, 892 elementos probados en 12 min 4 s.

#### Cabecera, pie y elementos flotantes (comunes a todas las pantallas)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Encuentra tu próxima inmersión · flotante | Saltar al contenido | Enlace | Funciona | Desplaza la página · clic por JavaScript (no se puede pulsar con el ratón) |
| Encuentra tu próxima inmersión · cabecera | WORLDIVES DISCOVERY · inicio | Enlace | Funciona | Enlace a la pantalla en la que ya se está |
| Encuentra tu próxima inmersión · cabecera | Explorar | Enlace | Funciona | Abre #/explorar |
| Encuentra tu próxima inmersión · cabecera | Puntos de buceo | Enlace | Funciona | Abre #/puntos |
| Encuentra tu próxima inmersión · cabecera | Centros | Enlace | Funciona | Abre #/centros |
| Encuentra tu próxima inmersión · cabecera | Tipos de buceo | Enlace | Funciona | Abre #/tipos |
| Encuentra tu próxima inmersión · cabecera | Experiencias | Enlace | Funciona | Abre #/experiencias |
| Encuentra tu próxima inmersión · cabecera | Top 10 buceos | Enlace | Funciona | Abre #/top10 |
| Encuentra tu próxima inmersión · cabecera | Seleccionar idioma | Desplegable | Funciona | Recarga la página con /?lang=en · POST /api/account/language → 200 |
| Encuentra tu próxima inmersión · cabecera | AI Admin ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) |
| Encuentra tu próxima inmersión · pie de página | Explorar el mapa | Enlace | Funciona | Mismo enlace (#/explorar) que «Explorar» en «Encuentra tu próxima inmersión»: Abre #/explorar |
| Encuentra tu próxima inmersión · pie de página | Top 10 cerca de ti | Enlace | Funciona | Mismo enlace (#/top10) que «Top 10 buceos» en «Encuentra tu próxima inmersión»: Abre #/top10 |
| Encuentra tu próxima inmersión · pie de página | Centros de buceo | Enlace | Funciona | Mismo enlace (#/centros) que «Centros» en «Encuentra tu próxima inmersión»: Abre #/centros |
| Encuentra tu próxima inmersión · pie de página | Viajes y vida a bordo | Enlace | Funciona | Mismo enlace (#/experiencias) que «Experiencias» en «Encuentra tu próxima inmersión»: Abre #/experiencias |
| Encuentra tu próxima inmersión · pie de página | Mi cuenta | Enlace | Funciona | Abre #/cuenta |
| Encuentra tu próxima inmersión · pie de página | Log Book | Enlace | Funciona | Abre #/logbook |
| Encuentra tu próxima inmersión · pie de página | Recompensas | Enlace | Funciona | Abre #/recompensas |
| Encuentra tu próxima inmersión · pie de página | Mis puntos | Enlace | Funciona | Abre #/mis-puntos |
| Encuentra tu próxima inmersión · pie de página | Dar de alta mi centro | Enlace | Funciona | Abre #/registro |
| Encuentra tu próxima inmersión · pie de página | Panel del centro | Enlace | Funciona | Abre #/admin |
| Encuentra tu próxima inmersión · pie de página | Condiciones para centros | Enlace | Funciona | Abre #/legal/condiciones-centros |
| Encuentra tu próxima inmersión · pie de página | Aviso legal | Enlace | Funciona | Abre #/legal/aviso-legal |
| Encuentra tu próxima inmersión · pie de página | Privacidad | Enlace | Funciona | Abre #/legal/privacidad |
| Encuentra tu próxima inmersión · pie de página | Cookies | Enlace | Funciona | Abre #/legal/cookies |
| Encuentra tu próxima inmersión · pie de página | Condiciones de uso | Enlace | Funciona | Abre #/legal/condiciones-buceadores |
| Encuentra tu próxima inmersión · pie de página | Condiciones de reserva | Enlace | Funciona | Abre #/legal/condiciones-reserva |
| Encuentra tu próxima inmersión · pie de página | Para centros | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Encuentra tu próxima inmersión · pie de página | Denunciar contenido | Enlace | Funciona | Abre #/legal/denuncias |
| Centro de control de WORLDIVES · Inicio · flotante | Saltar al contenido | Enlace | Funciona | Desplaza la página · clic por JavaScript (no se puede pulsar con el ratón) |

#### Encuentra tu próxima inmersión · `#/`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Encuentra tu próxima inmersión | Buscar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «⌕ Escribe al menos dos letras El nombre de un punto, una ciudad, una isla o un centro de buceo.» |
| Encuentra tu próxima inmersión | Cerca de mí | Enlace | Funciona | Mismo enlace (#/top10) que «Top 10 buceos» en «Encuentra tu próxima inmersión»: Abre #/top10 |
| Encuentra tu próxima inmersión | Pecios | Enlace | Funciona | Abre #/tipos?t=pecios-y-naufragios |
| Encuentra tu próxima inmersión | Cuevas | Enlace | Funciona | Abre #/tipos?t=cuevas-y-cavernas |
| Encuentra tu próxima inmersión | Arrecifes | Enlace | Funciona | Abre #/tipos?t=arrecifes |
| Encuentra tu próxima inmersión | Centros con reserva online | Enlace | Funciona | Abre #/centros?only=online |
| Encuentra tu próxima inmersión | Abrir el explorador → | Enlace | Funciona | Mismo enlace (#/explorar) que «Explorar» en «Encuentra tu próxima inmersión»: Abre #/explorar |
| Encuentra tu próxima inmersión | 01 Europa 108 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (32 elementos): «4» |
| Encuentra tu próxima inmersión | 02 Asia 104 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (26 elementos): «15» |
| Encuentra tu próxima inmersión | 03 América 24 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (25 elementos): «3» |
| Encuentra tu próxima inmersión | 04 África y Mar Rojo 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (34 elementos): «2» |
| Encuentra tu próxima inmersión | 05 Oceanía 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (11 elementos): «2» |
| Encuentra tu próxima inmersión | 06 Caribe 17 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (27 elementos): «8» |
| Encuentra tu próxima inmersión | Mapa | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| Encuentra tu próxima inmersión | Satélite Disponible próximamente | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| Encuentra tu próxima inmersión | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (18 elementos): «Leaflet» |
| Encuentra tu próxima inmersión | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (19 elementos): «2» · hay 15 más iguales en la lista (no se prueban todos) |
| Encuentra tu próxima inmersión | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (7 elementos): «Rainbow Reef» |
| Encuentra tu próxima inmersión | Mauritius – Cathedral | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (139 elementos): «×» · hay 1 más iguales en la lista (no se prueban todos) |
| Encuentra tu próxima inmersión | Tofo – Manta Reef | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» |
| Encuentra tu próxima inmersión | Zoom in | Enlace | Funciona | Muestra contenido nuevo (64 elementos): «2» |
| Encuentra tu próxima inmersión | Zoom out | Enlace | Funciona | Cambia su estado (class: leaflet-control-zoom-out → leaflet-control-zoom-out leaflet-disabled) · Cambia la pantalla (4 elementos nuevos, 0 quitados) |
| Encuentra tu próxima inmersión | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Encuentra tu próxima inmersión | OpenStreetMap contributors | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Encuentra tu próxima inmersión | Ver todos los tipos → | Enlace | Funciona | Mismo enlace (#/tipos) que «Tipos de buceo» en «Encuentra tu próxima inmersión»: Abre #/tipos |
| Encuentra tu próxima inmersión | Aguas profundas | Enlace | Funciona | Abre #/tipos?t=aguas-profundas |
| Encuentra tu próxima inmersión | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| Encuentra tu próxima inmersión | Paredes | Enlace | Funciona | Abre #/tipos?t=paredes |
| Encuentra tu próxima inmersión | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| Encuentra tu próxima inmersión | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| Encuentra tu próxima inmersión | Pináculos | Enlace | Funciona | Abre #/tipos?t=pinaculos |

#### El mapa del buceo · `#/explorar`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| El mapa del buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| El mapa del buceo | Todos | Botón | Funciona | Muestra contenido nuevo (36 elementos): «2» |
| El mapa del buceo | Arrecifes | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (58 elementos): «2» |
| El mapa del buceo | Paredes | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (45 elementos): «2» |
| El mapa del buceo | Pecios | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (32 elementos): «2» |
| El mapa del buceo | Cuevas | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (32 elementos): «3» |
| El mapa del buceo | Muck | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (30 elementos): «3» |
| El mapa del buceo | Pináculos | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (27 elementos): «7» |
| El mapa del buceo | Profundas | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (59 elementos): «2» |
| El mapa del buceo | 01 Europa 108 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (40 elementos): «2» |
| El mapa del buceo | 02 Asia 104 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (22 elementos): «2» |
| El mapa del buceo | 03 América 24 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (15 elementos): «2» |
| El mapa del buceo | 04 África y Mar Rojo 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (25 elementos): «2» |
| El mapa del buceo | 05 Oceanía 20 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (31 elementos): «2» |
| El mapa del buceo | 06 Caribe 17 ⌄ | Botón | Funciona | Cambia su estado (aria-expanded: false → true) · Muestra contenido nuevo (32 elementos): «2» |
| El mapa del buceo | Mapa | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (26 elementos): «Leaflet» |
| El mapa del buceo | Satélite Disponible próximamente | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Disponible próximamente» |
| El mapa del buceo | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (26 elementos): «Leaflet» |
| El mapa del buceo | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (31 elementos): «2» · clic forzado (otro elemento lo tapa) · hay 29 más iguales en la lista (no se prueban todos) |
| El mapa del buceo | 2 | Elemento div (role=button) | Funciona | Muestra contenido nuevo (14 elementos): «Rainbow Reef» |
| El mapa del buceo | Mauritius – Cathedral | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» · hay 3 más iguales en la lista (no se prueban todos) |
| El mapa del buceo | Tofo – Manta Reef | Elemento div (role=button) | Funciona | Cambia su estado (class: leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive → leaflet-marker-icon wd-pin-wrap leaflet-zoom-animated leaflet-interactive is-sel) · Muestra contenido nuevo (150 elementos): «×» |
| El mapa del buceo | Seguridad en el buceo | Enlace | Funciona | Abre #/legal/seguridad |
| El mapa del buceo | Zoom in | Enlace | Funciona | Muestra contenido nuevo (87 elementos): «2» |
| El mapa del buceo | Zoom out | Enlace | Funciona | Cambia la pantalla (10 elementos nuevos, 0 quitados) |
| El mapa del buceo | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |

#### Puntos de buceo · `#/puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Puntos de buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Puntos de buceo | Puntos de buceo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (68 elementos): «Todo el mundo» |
| Puntos de buceo | Zona Todo el mundo Europa (108) Asia (104) América (24) África y Mar Rojo (20) Oceanía (20) Caribe (17) | Desplegable | Funciona | Abre #/puntos?zone=Europa |
| Puntos de buceo | Para empezar | Botón | Funciona | Abre #/puntos?level=start |
| Puntos de buceo | Intermedio | Botón | Funciona | Abre #/puntos?level=mid |
| Puntos de buceo | Avanzado | Botón | Funciona | Abre #/puntos?level=adv |
| Puntos de buceo | Con centro que lo ofrece | Botón | Funciona | Abre #/puntos?only=centers |
| Puntos de buceo | Confirmación inmediata | Botón | Funciona | Abre #/puntos?only=instant |
| Puntos de buceo | Tipo de buceo Cualquier tipo Arrecifes Paredes Pecios y naufragios Cuevas y cavernas Cenotes Muck Canales Caño | Desplegable | Funciona | Abre #/puntos?type=arrecifes |
| Puntos de buceo | País Todos los países España (93) Filipinas (30) Indonesia (25) Malasia (15) Maldivas (13) Tailandia (13) Egip | Desplegable | Funciona | Abre #/puntos?country=Espa%C3%B1a |
| Puntos de buceo | Ordenar Recomendados Nombre A-Z Más profundos Menos profundos Mejor valorados | Desplegable | Funciona | Abre #/puntos?sort=name |
| Puntos de buceo | ¿Cómo ordenamos? | Enlace | Funciona | Abre #/legal/clasificacion |
| Puntos de buceo | #/punto?id=34 | Enlace | Funciona | Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Blue Hole, Dahab | Enlace | Funciona | Mismo enlace (#/punto?id=34) que «#/punto?id=34» en «Puntos de buceo»: Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Ver punto | Enlace | Funciona | Mismo enlace (#/punto?id=34) que «#/punto?id=34» en «Puntos de buceo»: Abre #/punto?id=34 · hay 11 más iguales en la lista (no se prueban todos) |
| Puntos de buceo | Mostrar más puntos (281) | Botón | Funciona | Cambia su estado (disabled: sin atributo → vacío) · Muestra contenido nuevo (13 elementos): «Arrecifes Paredes Portitxol Norte Marina Alta · Xàbia · España Moderado Arrecife · Pared · Fondo arenoso Ubicación por v» |

#### Centros de buceo · `#/centros`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centros de buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Centros de buceo | Centros de buceo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (11 elementos): «Todos los países» |
| Centros de buceo | País Todos los países España (2) | Desplegable | Funciona | Abre #/centros?country=Espa%C3%B1a |
| Centros de buceo | Confirmación inmediata | Botón | Funciona | Abre #/centros?only=instant |
| Centros de buceo | Reserva online | Botón | Funciona | Abre #/centros?only=online |
| Centros de buceo | Plazas esta semana | Botón | Funciona | Abre #/centros?only=week |
| Centros de buceo | Cursos | Botón | Funciona | Abre #/centros?only=courses |
| Centros de buceo | Bautizos | Botón | Funciona | Abre #/centros?only=try |
| Centros de buceo | Viajes | Botón | Funciona | Abre #/centros?only=trips |
| Centros de buceo | Con reseñas | Botón | Funciona | Abre #/centros?only=reviews |
| Centros de buceo | Tipo de buceo Cualquier tipo de buceo Arrecifes Paredes Pecios y naufragios Cuevas y cavernas Cenotes Muck Can | Desplegable | Funciona | Abre #/centros?type=arrecifes |
| Centros de buceo | Ordenar Recomendados Mejor valorados Más reseñas Precio más bajo Nombre A-Z | Desplegable | Funciona | Abre #/centros?sort=rating |
| Centros de buceo | ¿Cómo ordenamos? | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Centros de buceo | Bajo petición Plazas esta semana | Enlace | Funciona | Abre #/centro?id=31 |
| Centros de buceo | Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Centros de buceo | Reservar | Enlace | Funciona | Abre #/reservar?center=31 |
| Centros de buceo | Bajo petición Plazas esta semana | Enlace | Funciona | Abre #/centro?id=32 |
| Centros de buceo | Escafandra Medes | Enlace | Funciona | Mismo enlace (#/centro?id=32) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=32 |
| Centros de buceo | Reservar | Enlace | Funciona | Abre #/reservar?center=32 |
| Centros de buceo | Dar de alta mi centro | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### ¿Qué inmersión te apetece? · `#/tipos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| ¿Qué inmersión te apetece? | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| ¿Qué inmersión te apetece? | Todos | Botón | Funciona | Ya estaba seleccionado: pulsarlo otra vez no cambia nada (correcto) |
| ¿Qué inmersión te apetece? | Para empezar | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Con experiencia | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Avanzado y técnico | Botón | Funciona | Cambia su estado (aria-pressed: false → true) |
| ¿Qué inmersión te apetece? | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| ¿Qué inmersión te apetece? | Paredes | Enlace | Funciona | Mismo enlace (#/tipos?t=paredes) que «Paredes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=paredes |
| ¿Qué inmersión te apetece? | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| ¿Qué inmersión te apetece? | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| ¿Qué inmersión te apetece? | Cenotes | Enlace | Funciona | Abre #/tipos?t=cenotes |
| ¿Qué inmersión te apetece? | Muck | Enlace | Funciona | Abre #/tipos?t=muck |
| ¿Qué inmersión te apetece? | Canales | Enlace | Funciona | Abre #/tipos?t=canales |
| ¿Qué inmersión te apetece? | Cañones | Enlace | Funciona | Abre #/tipos?t=canones |
| ¿Qué inmersión te apetece? | Pináculos | Enlace | Funciona | Mismo enlace (#/tipos?t=pinaculos) que «Pináculos» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pinaculos |
| ¿Qué inmersión te apetece? | Corrientes y deriva | Enlace | Funciona | Abre #/tipos?t=corrientes-y-deriva |
| ¿Qué inmersión te apetece? | Aguas profundas | Enlace | Funciona | Mismo enlace (#/tipos?t=aguas-profundas) que «Aguas profundas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=aguas-profundas |
| ¿Qué inmersión te apetece? | Lagos | Enlace | Funciona | Abre #/tipos?t=lagos |
| ¿Qué inmersión te apetece? | Pilares | Enlace | Funciona | Abre #/tipos?t=pilares |
| ¿Qué inmersión te apetece? | Nocturnas | Enlace | Funciona | Abre #/tipos?t=nocturnas |
| ¿Qué inmersión te apetece? | Playa y esnórquel | Enlace | Funciona | Abre #/tipos?t=playa-y-esnorquel |
| ¿Qué inmersión te apetece? | Arrecifes | Enlace | Funciona | Mismo enlace (#/tipos?t=arrecifes) que «Arrecifes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=arrecifes |
| ¿Qué inmersión te apetece? | Muck | Enlace | Funciona | Mismo enlace (#/tipos?t=muck) que «Muck» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=muck |
| ¿Qué inmersión te apetece? | Lagos | Enlace | Funciona | Mismo enlace (#/tipos?t=lagos) que «Lagos» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=lagos |
| ¿Qué inmersión te apetece? | Pilares | Enlace | Funciona | Mismo enlace (#/tipos?t=pilares) que «Pilares» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=pilares |
| ¿Qué inmersión te apetece? | Paredes | Enlace | Funciona | Mismo enlace (#/tipos?t=paredes) que «Paredes» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=paredes |
| ¿Qué inmersión te apetece? | Pecios y naufragios | Enlace | Funciona | Mismo enlace (#/tipos?t=pecios-y-naufragios) que «Pecios» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pecios-y-naufragios |
| ¿Qué inmersión te apetece? | Canales | Enlace | Funciona | Mismo enlace (#/tipos?t=canales) que «Canales» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=canales |
| ¿Qué inmersión te apetece? | Pináculos | Enlace | Funciona | Mismo enlace (#/tipos?t=pinaculos) que «Pináculos» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=pinaculos |
| ¿Qué inmersión te apetece? | Cuevas y cavernas | Enlace | Funciona | Mismo enlace (#/tipos?t=cuevas-y-cavernas) que «Cuevas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=cuevas-y-cavernas |
| ¿Qué inmersión te apetece? | Cenotes | Enlace | Funciona | Mismo enlace (#/tipos?t=cenotes) que «Cenotes» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=cenotes |
| ¿Qué inmersión te apetece? | Cañones | Enlace | Funciona | Mismo enlace (#/tipos?t=canones) que «Cañones» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=canones |
| ¿Qué inmersión te apetece? | Corrientes y deriva | Enlace | Funciona | Mismo enlace (#/tipos?t=corrientes-y-deriva) que «Corrientes y deriva» en «¿Qué inmersión te apetece?»: Abre #/tipos?t=corrientes-y-deriva |
| ¿Qué inmersión te apetece? | Aguas profundas | Enlace | Funciona | Mismo enlace (#/tipos?t=aguas-profundas) que «Aguas profundas» en «Encuentra tu próxima inmersión»: Abre #/tipos?t=aguas-profundas |

#### Viajes y vida a bordo · `#/experiencias`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Viajes y vida a bordo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Viajes y vida a bordo | Viajes y vida a bordo | Formulario | Funciona | Enviado vacío · Muestra contenido nuevo (16 elementos): «Viaje 1 experiencia Costa Blanca España Experiencias de buceo organizadas por centros y profesionales. DESDE 290 € PRÓXI» |
| Viajes y vida a bordo | Todas | Botón | Funciona | Muestra contenido nuevo (8 elementos): «Viaje 1 experiencia Costa Blanca España Experiencias de buceo organizadas por centros y profesionales. DESDE 290 € PRÓXI» |
| Viajes y vida a bordo | Viaje | Botón | Funciona | Abre #/experiencias?kind=Viaje |
| Viajes y vida a bordo | Vida a bordo | Botón | Funciona | Abre #/experiencias?kind=Vida+a+bordo |
| Viajes y vida a bordo | Ordenar Con más salidas Precio más bajo Próxima salida Nombre A-Z | Desplegable | Funciona | Abre #/experiencias?sort=price |
| Viajes y vida a bordo | Viaje 1 experiencia | Enlace | Funciona | Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Costa Blanca | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Ver viajes | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Ver destino | Enlace | Funciona | Abre #/experiencia?id=5 · hay 3 más iguales en la lista (no se prueban todos) |
| Viajes y vida a bordo | Empezar a publicar | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### ¿Te apetece bucear? · `#/top10`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| ¿Te apetece bucear? | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| ¿Te apetece bucear? | Radio 25 km 50 km 100 km 250 km 500 km | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Buscar» (sin efecto inmediato, correcto) |
| ¿Te apetece bucear? | Usar mi ubicación | Botón | Funciona | Muestra contenido nuevo (13 elementos): «1 ARRECIFES Cabo San Antonio Marina Alta · Xàbia · España 7–20 m Moderado ★ 4.4 (9) 1 centro 1,9 km Ver inmersión» |
| ¿Te apetece bucear? | Elegir en el mapa | Botón | Funciona | Abre la ventana «Elige tu ubicación» |
| ¿Te apetece bucear? | ¿Te apetece bucear? | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Buscar una localidad» (campo obligatorio) |
| ¿Te apetece bucear? | Marina Alta · Xàbia | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 ARRECIFES Piedras Rotas Marina Alta · Xàbia · España 7–20 m Fácil ★ 4.4 (9) 1 centro 0,8 km Ver inmersión» |
| ¿Te apetece bucear? | Marina Alta y Baixa · Calpe | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 19,3 km Ver inmersión» |
| ¿Te apetece bucear? | Canarias | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (9 elementos): «1 ARRECIFES Las Canteras, Gran Canaria Canarias · España Iniciación 48,3 km Ver inmersión» |
| ¿Te apetece bucear? | Palawan | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (4 elementos): «1 ARRECIFES El Nido – Cadlao Lagoon Palawan · Filipinas 5–20 m Principiante 72,9 km Ver inmersión» |
| ¿Te apetece bucear? | Comunitat Valenciana | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 25,7 km Ver inmersión» |
| ¿Te apetece bucear? | Andalucía | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (6 elementos): «1 ARRECIFES Costa del Sol, Málaga Andalucía · España Iniciación 52,4 km Ver inmersión» |
| ¿Te apetece bucear? | Marina Alta · Moraira | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (13 elementos): «1 PAREDES Pared Negra Marina Alta · Xàbia · España 8–16 m Intermedia ★ 4.4 (9) 1 centro 9,7 km Ver inmersión» |
| ¿Te apetece bucear? | Cebu | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (12 elementos): «1 ARRECIFES Moalboal – Sardine Run Cebu · Filipinas 5–25 m Principiante 28,1 km Ver inmersión» |
| ¿Te apetece bucear? | Cataluña | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (12 elementos): «1 ARRECIFES Medes – Tascons Islas Medes · España 6–25 m Intermedio ★ 4.8 (6) 1 centro 2,1 km Ver inmersión» |
| ¿Te apetece bucear? | Illes Balears | Botón | Funciona | Cambia su estado (aria-pressed: false → true) · Muestra contenido nuevo (8 elementos): «1 PAREDES El Toro Mallorca · España 10–35 m Intermedio 12,9 km Ver inmersión» |

#### Planes de WORLDIVES · `#/planes`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Planes de WORLDIVES | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Planes de WORLDIVES | Dar de alta mi centro | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### Cómo funcionan los puntos · `#/como-funcionan-los-puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Cómo funcionan los puntos | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Cómo funcionan los puntos | Ver mis puntos | Enlace | Funciona | Mismo enlace (#/mis-puntos) que «Mis puntos» en «Encuentra tu próxima inmersión»: Abre #/mis-puntos |
| Cómo funcionan los puntos | Ver ventajas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Recompensas» en «Encuentra tu próxima inmersión»: Abre #/recompensas |

#### Aviso legal · `#/legal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Aviso legal | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Aviso legal | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Aviso legal | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Abre #/legal/reservas |
| Aviso legal | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Aviso legal | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Aviso legal | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Aviso legal | Normas de las reseñas | Enlace | Funciona | Abre #/legal/normas-resenas |
| Aviso legal | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Puntos WORLDIVES | Enlace | Funciona | Abre #/legal/puntos |
| Aviso legal | Declaración de accesibilidad | Enlace | Funciona | Abre #/legal/accesibilidad |
| Aviso legal | Contacto | Enlace | Funciona | Abre #/legal/contacto |
| Aviso legal | Créditos y licencias de terceros | Enlace | Funciona | Abre #/legal/creditos |
| Aviso legal | Condiciones de uso | Enlace | Funciona | Abre #/legal/terminos |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Leer | Botón | Funciona | Abre la ventana «Aviso legal» |
| Aviso legal | 1. Titular del sitio web | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 6 más iguales en la lista (no se prueban todos) |
| Aviso legal | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Crear cuenta · `#/registro`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Crear cuenta | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Crear cuenta | Buceador | Enlace | Funciona | Abre #/registro?tipo=recreational |
| Crear cuenta | Centro de buceo Publica tus salidas y cursos y gestiona tus reservas. | Enlace | Funciona | Abre #/registro?tipo=center |
| Crear cuenta | Profesional | Enlace | Funciona | Abre #/registro?tipo=freelance |
| Crear cuenta | Iniciar sesión | Enlace | Funciona | Abre #/cuenta |

#### Condiciones para centros y profesionales · `#/legal/condiciones-centros`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones para centros y profesionales | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones para centros y profesionales | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones para centros y profesionales | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones para centros y profesionales | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones para centros y profesionales | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones para centros y profesionales | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones para centros y profesionales | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones para centros y profesionales | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones para centros y profesionales | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones para centros y profesionales | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones para centros y profesionales | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones para centros y profesionales | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones para centros y profesionales | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones para centros y profesionales | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones para centros y profesionales | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones para centros y profesionales | Planes | Enlace | Funciona | Abre #/planes |
| Condiciones para centros y profesionales | Planes | Enlace | Funciona | Mismo enlace (#/planes) que «Planes» en «Condiciones para centros y profesionales»: Abre #/planes |
| Condiciones para centros y profesionales | normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones para centros y profesionales | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones para centros y profesionales | Leer | Botón | Funciona | Abre la ventana «Condiciones para centros y profesionales» |
| Condiciones para centros y profesionales | 1. Alta y verificación | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 18 más iguales en la lista (no se prueban todos) |
| Condiciones para centros y profesionales | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones para centros y profesionales | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Aviso legal · `#/legal/aviso-legal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Aviso legal | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Aviso legal | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Aviso legal | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Aviso legal | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Aviso legal | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Aviso legal | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Aviso legal | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Aviso legal | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Aviso legal | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Aviso legal | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Aviso legal | Condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/terminos) que «Condiciones de uso» en «Aviso legal»: Abre #/legal/terminos |
| Aviso legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Aviso legal | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Aviso legal | Leer | Botón | Funciona | Abre la ventana «Aviso legal» |
| Aviso legal | 1. Titular del sitio web | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 6 más iguales en la lista (no se prueban todos) |
| Aviso legal | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Aviso legal | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Política de privacidad · `#/legal/privacidad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Política de privacidad | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Política de privacidad | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Política de privacidad | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Política de privacidad | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Política de privacidad | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Política de privacidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de privacidad | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Política de privacidad | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Política de privacidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de privacidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Política de privacidad | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Política de privacidad | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Política de privacidad | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Política de privacidad | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Política de privacidad | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Política de privacidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de privacidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de privacidad | www.aepd.es | Enlace externo | Funciona | Enlace externo a www.aepd.es (no se abre: dirección https válida) |
| Política de privacidad | Leer | Botón | Funciona | Abre la ventana «Política de privacidad» |
| Política de privacidad | 1. Responsable | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 8 más iguales en la lista (no se prueban todos) |
| Política de privacidad | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Política de privacidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Política de cookies y servicios de terceros · `#/legal/cookies`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Política de cookies y servicios de terceros | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Política de cookies y servicios de terceros | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Política de cookies y servicios de terceros | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Política de cookies y servicios de terceros | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Política de cookies y servicios de terceros | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Política de cookies y servicios de terceros | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Política de cookies y servicios de terceros | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Política de cookies y servicios de terceros | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Política de cookies y servicios de terceros | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Política de cookies y servicios de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Política de cookies y servicios de terceros | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Política de cookies y servicios de terceros | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Política de cookies y servicios de terceros | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Política de cookies y servicios de terceros | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Política de cookies y servicios de terceros | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Política de cookies y servicios de terceros | Leer | Botón | Funciona | Abre la ventana «Política de cookies y servicios de terceros» |
| Política de cookies y servicios de terceros | Qué usamos | Enlace | Funciona | Cambia tabindex en h2#que-usamos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Política de cookies y servicios de terceros | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Política de cookies y servicios de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de uso para buceadores · `#/legal/condiciones-buceadores`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de uso para buceadores | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de uso para buceadores | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de uso para buceadores | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de uso para buceadores | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de uso para buceadores | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Leer | Botón | Funciona | Abre la ventana «Condiciones de uso para buceadores» |
| Condiciones de uso para buceadores | 1. Qué es WORLDIVES DISCOVERY | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 9 más iguales en la lista (no se prueban todos) |
| Condiciones de uso para buceadores | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de reserva, pago y cancelación · `#/legal/condiciones-reserva`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de reserva, pago y cancelación | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de reserva, pago y cancelación | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de reserva, pago y cancelación | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de reserva, pago y cancelación | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de reserva, pago y cancelación | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de reserva, pago y cancelación | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de reserva, pago y cancelación | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de reserva, pago y cancelación | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de reserva, pago y cancelación | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de reserva, pago y cancelación | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Leer | Botón | Funciona | Abre la ventana «Condiciones de reserva, pago y cancelación» |
| Condiciones de reserva, pago y cancelación | 1. Quién presta la actividad | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 7 más iguales en la lista (no se prueban todos) |
| Condiciones de reserva, pago y cancelación | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Denunciar contenido · `#/legal/denuncias`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Denunciar contenido | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Denunciar contenido | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Denunciar contenido | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Denunciar contenido | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Denunciar contenido | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Denunciar contenido | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Denunciar contenido | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Denunciar contenido | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Denunciar contenido | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Denunciar contenido | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Denunciar contenido | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Denunciar contenido | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Denunciar contenido | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Denunciar contenido | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Denunciar contenido | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Denunciar contenido | Formulario de denuncia | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Motivo» (elige una opción de la lista) · El navegador no deja enviarlo: «Explica por qué es ilegal o incumple las condiciones» (campo obligatorio) |
| Denunciar contenido | Motivo | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Enviar denuncia» (sin efecto inmediato, correcto) |
| Denunciar contenido | Leer | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Denunciar contenido | Qué necesitamos | Enlace | Funciona | Cambia tabindex en h2#que-necesitamos (sin atributo → -1) · hay 2 más iguales en la lista (no se prueban todos) |
| Denunciar contenido | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Denunciar contenido | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Seguridad en el buceo · `#/legal/seguridad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Seguridad en el buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Seguridad en el buceo | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Seguridad en el buceo | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Seguridad en el buceo | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Seguridad en el buceo | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Seguridad en el buceo | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Seguridad en el buceo | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Seguridad en el buceo | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Seguridad en el buceo | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Seguridad en el buceo | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Seguridad en el buceo | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Seguridad en el buceo | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Seguridad en el buceo | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Seguridad en el buceo | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Seguridad en el buceo | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Seguridad en el buceo | Leer | Botón | Funciona | Abre la ventana «Seguridad en el buceo» |
| Seguridad en el buceo | Antes de reservar | Enlace | Funciona | Cambia tabindex en h2#antes-de-reservar (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Seguridad en el buceo | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Seguridad en el buceo | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Cómo ordenamos los resultados · `#/legal/clasificacion`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Cómo ordenamos los resultados | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Cómo ordenamos los resultados | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Cómo ordenamos los resultados | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Cómo ordenamos los resultados | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Cómo ordenamos los resultados | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Cómo ordenamos los resultados | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Cómo ordenamos los resultados | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Cómo ordenamos los resultados | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Cómo ordenamos los resultados | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Cómo ordenamos los resultados | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Cómo ordenamos los resultados | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Cómo ordenamos los resultados | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Cómo ordenamos los resultados | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Cómo ordenamos los resultados | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Cómo ordenamos los resultados | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Cómo ordenamos los resultados | Leer | Botón | Funciona | Abre la ventana «Cómo ordenamos los resultados» |
| Cómo ordenamos los resultados | Directorio de centros | Enlace | Funciona | Cambia tabindex en h2#directorio-de-centros (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Cómo ordenamos los resultados | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Cómo ordenamos los resultados | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Blue Hole, Dahab · `#/punto?id=34`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Blue Hole, Dahab | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Blue Hole, Dahab | Puntos de buceo | Enlace | Funciona | Mismo enlace (#/puntos) que «Puntos de buceo» en «Encuentra tu próxima inmersión»: Abre #/puntos |
| Blue Hole, Dahab | África y Mar Rojo | Enlace | Funciona | Abre #/puntos?zone=%C3%81frica+y+Mar+Rojo |
| Blue Hole, Dahab | Abrir en el mapa | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Blue Hole, Dahab | Mi cuenta | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Encuentra tu próxima inmersión»: Abre #/cuenta |
| Blue Hole, Dahab | ¿Tienes un centro? Únete a WORLDIVES | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |
| Blue Hole, Dahab | Blue Hole Dahab Dahab · Egipto 6–60 m · Avanzado a 0 km | Enlace | Funciona | Abre #/punto?id=247 |
| Blue Hole, Dahab | Canyon Dahab Dahab · Egipto 8–30 m · Intermedio a 2,9 km | Enlace | Funciona | Abre #/punto?id=248 |
| Blue Hole, Dahab | Blue Hole, Dahab | Elemento div (role=button) | Funciona | Mueve o amplía el mapa |
| Blue Hole, Dahab | Mapa | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (8 elementos): «Leaflet» |
| Blue Hole, Dahab | Satélite | Botón | Depende de clave pendiente | Desactivado (ArcGIS (satélite): sin ARCGIS_API_KEY el satélite sale desactivado): «Disponible próximamente · Relieve orientativo (GEBCO). No sirve para navegar ni para la seguridad en el mar. Seguridad en el buceo» |
| Blue Hole, Dahab | Relieve | Botón | Funciona | Cambia su estado (class: sin atributo → active) · Muestra contenido nuevo (10 elementos): «Leaflet» |
| Blue Hole, Dahab | Zoom in | Enlace | Funciona | Cambia la pantalla (5 elementos nuevos, 2 quitados) |
| Blue Hole, Dahab | Zoom out | Enlace | Funciona | Cambia la pantalla (5 elementos nuevos, 2 quitados) |
| Blue Hole, Dahab | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Blue Hole, Dahab | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Blue Hole, Dahab | Abrir en OpenStreetMap | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Blue Hole, Dahab | Proponer nueva posición | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Latitud Longitud Motivo» |
| Blue Hole, Dahab | Denunciar contenido | Botón | Funciona | Abre la ventana «Denunciar contenido» |

#### Bahía Coralina Centro de Buceo · `#/centro?id=31`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | Centros | Enlace | Funciona | Mismo enlace (#/centros) que «Centros» en «Encuentra tu próxima inmersión»: Abre #/centros |
| Bahía Coralina Centro de Buceo | Reservar | Enlace | Funciona | Mismo enlace (#/reservar?center=31) que «Reservar» en «Centros de buceo»: Abre #/reservar?center=31 |
| Bahía Coralina Centro de Buceo | Llamar | Enlace externo | Funciona | Teléfono +34600000101 |
| Bahía Coralina Centro de Buceo | Escribir | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | Lun, 19 oct 10:00 6 plazas | Enlace | Funciona | Abre #/reservar?center=31&service=7&slot=22 · POST /api/stats/track → 200 · hay 11 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Enviar solicitud | Enlace | Funciona | Abre #/reservar?center=31&service=7 · POST /api/stats/track → 200 · hay 3 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Añadir a una reserva | Enlace | Funciona | Abre #/reservar?center=31&service=8 · POST /api/stats/track → 200 |
| Bahía Coralina Centro de Buceo | Tres días en la reserva del Cabo de San Antonio | Enlace | Funciona | Mismo enlace (#/experiencia?id=7) que «Viaje 1 experiencia» en «Viajes y vida a bordo»: Abre #/experiencia?id=7 · hay 6 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Foto 1 de Bahía Coralina Centro de Buceo | Botón | Funciona | Abre la ventana «Bahía Coralina Centro de Buceo» · hay 2 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Foto 2 de Bahía Coralina Centro de Buceo | Botón | Funciona | Abre la ventana «Bahía Coralina Centro de Buceo» |
| Bahía Coralina Centro de Buceo | Ocultar reseña | Botón | Funciona | Abre la ventana «Ocultar reseña» · hay 7 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» · hay 7 más iguales en la lista (no se prueban todos) |
| Bahía Coralina Centro de Buceo | Ocultar reseña | Botón | Funciona | Abre la ventana «Ocultar reseña» |
| Bahía Coralina Centro de Buceo | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34600000101 |
| Bahía Coralina Centro de Buceo | hola@bahiacoralina.example.com | Enlace externo | Funciona | Correo hola@bahiacoralina.example.com |
| Bahía Coralina Centro de Buceo | bahiacoralina.example.com | Enlace externo | Funciona | Enlace externo a bahiacoralina.example.com (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo | Ver en el mapa | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Bahía Coralina Centro de Buceo | Reservar con Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/reservar?center=31) que «Reservar» en «Centros de buceo»: Abre #/reservar?center=31 |
| Bahía Coralina Centro de Buceo | Denunciar contenido | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Bahía Coralina Centro de Buceo | Cabo San Antonio | Enlace | Funciona | Abre #/punto?id=329 · hay 5 más iguales en la lista (no se prueban todos) |

#### Bahía Coralina Centro de Buceo · `#/reservar?center=31`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Bahía Coralina Centro de Buceo | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Bahía Coralina Centro de Buceo | ← Bahía Coralina Centro de Buceo | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Bahía Coralina Centro de Buceo | Bautizo de buceo | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «No admite reservas ahora mismo» |
| Bahía Coralina Centro de Buceo | Curso Open Water (3 días) | Botón | Funciona | Muestra contenido nuevo (14 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Curso de Nitrox | Botón | Funciona | Muestra contenido nuevo (13 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Doble inmersión en barco | Botón | Funciona | Muestra contenido nuevo (26 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Inmersión al atardecer | Botón | Funciona | Muestra contenido nuevo (17 elementos): «Bautizo de buceo 2 h 30 min Pago al reservar · confirmación inmediata · no disponible No admite reservas ahora mismo 55 » |
| Bahía Coralina Centro de Buceo | Inmersión simple en barco | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «No admite reservas ahora mismo» |
| Bahía Coralina Centro de Buceo | Una persona menos | Botón | Desactivado (correcto) | Desactivado: es el límite del calendario o de la lista («Una persona menos») |
| Bahía Coralina Centro de Buceo | Una persona más | Botón | Desactivado (correcto) | No responde al ratón (pointer-events: none) y se ve atenuado; la pantalla explica: «Elige primero la actividad.» |
| Bahía Coralina Centro de Buceo | Elige una actividad | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Política de cancelación. Moderada: cancelación gratuita hasta 48 horas antes de la actividad; después no hay reembolso.» |
| Bahía Coralina Centro de Buceo | condiciones de reserva | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Bahía Coralina Centro de Buceo | condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Bahía Coralina Centro de Buceo | +34 600 000 101 | Enlace externo | Funciona | Teléfono +34600000101 |

#### Costa Blanca · `#/experiencia?id=7`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Costa Blanca | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Costa Blanca | Experiencias | Enlace | Funciona | Mismo enlace (#/experiencias) que «Experiencias» en «Encuentra tu próxima inmersión»: Abre #/experiencias |
| Costa Blanca | BAHÍA CORALINA CENTRO DE BUCEO | Enlace | Funciona | Mismo enlace (#/centro?id=31) que «Bajo petición Plazas esta semana» en «Centros de buceo»: Abre #/centro?id=31 |
| Costa Blanca | Solicitar plaza | Botón | Funciona | Abre #/experienciareserva?id=2 |
| Costa Blanca | Denunciar | Botón | Funciona | Abre la ventana «Denunciar contenido» |
| Costa Blanca | Publicar un viaje | Enlace | Funciona | Mismo enlace (#/registro) que «Dar de alta mi centro» en «Encuentra tu próxima inmersión»: Abre #/registro |

#### Condiciones de reserva, pago y cancelación · `#/legal/reservas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de reserva, pago y cancelación | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de reserva, pago y cancelación | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de reserva, pago y cancelación | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de reserva, pago y cancelación | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de reserva, pago y cancelación | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de reserva, pago y cancelación | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de reserva, pago y cancelación | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de reserva, pago y cancelación | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de reserva, pago y cancelación | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de reserva, pago y cancelación | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de reserva, pago y cancelación | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de reserva, pago y cancelación | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de reserva, pago y cancelación | Leer | Botón | Funciona | Abre la ventana «Condiciones de reserva, pago y cancelación» |
| Condiciones de reserva, pago y cancelación | 1. Quién presta la actividad | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 7 más iguales en la lista (no se prueban todos) |
| Condiciones de reserva, pago y cancelación | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de reserva, pago y cancelación | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Normas de las reseñas · `#/legal/normas-resenas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Normas de las reseñas | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Normas de las reseñas | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Normas de las reseñas | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Normas de las reseñas | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Normas de las reseñas | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Normas de las reseñas | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Normas de las reseñas | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Normas de las reseñas | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Normas de las reseñas | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Normas de las reseñas | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Normas de las reseñas | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Normas de las reseñas | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Normas de las reseñas | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Normas de las reseñas | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Normas de las reseñas | Leer | Botón | Funciona | Abre la ventana «Normas de las reseñas» |
| Normas de las reseñas | Quién puede escribir una reseña | Enlace | Funciona | Cambia tabindex en h2#quien-puede-escribir-una-resena (sin atributo → -1) · hay 4 más iguales en la lista (no se prueban todos) |
| Normas de las reseñas | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Normas de las reseñas | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Puntos WORLDIVES · `#/legal/puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Puntos WORLDIVES | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Puntos WORLDIVES | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Puntos WORLDIVES | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Puntos WORLDIVES | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Puntos WORLDIVES | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Puntos WORLDIVES | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Puntos WORLDIVES | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Puntos WORLDIVES | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Puntos WORLDIVES | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Puntos WORLDIVES | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Puntos WORLDIVES | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Puntos WORLDIVES | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Puntos WORLDIVES | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Puntos WORLDIVES | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Puntos WORLDIVES | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Puntos WORLDIVES | Condiciones de uso | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Puntos WORLDIVES | Leer | Botón | Funciona | Abre la ventana «Puntos WORLDIVES» |
| Puntos WORLDIVES | 1. Cómo se consiguen | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 5 más iguales en la lista (no se prueban todos) |
| Puntos WORLDIVES | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Puntos WORLDIVES | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Declaración de accesibilidad · `#/legal/accesibilidad`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Declaración de accesibilidad | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Declaración de accesibilidad | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Declaración de accesibilidad | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Declaración de accesibilidad | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Declaración de accesibilidad | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Declaración de accesibilidad | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Declaración de accesibilidad | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Declaración de accesibilidad | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Declaración de accesibilidad | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Declaración de accesibilidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Declaración de accesibilidad | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Declaración de accesibilidad | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Declaración de accesibilidad | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Declaración de accesibilidad | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Declaración de accesibilidad | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Declaración de accesibilidad | Leer | Botón | Funciona | Abre la ventana «Declaración de accesibilidad» |
| Declaración de accesibilidad | Situación actual | Enlace | Funciona | Cambia tabindex en h2#situacion-actual (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Declaración de accesibilidad | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Declaración de accesibilidad | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Contacto · `#/legal/contacto`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Contacto | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Contacto | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Contacto | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Contacto | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Contacto | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Contacto | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Contacto | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Contacto | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Contacto | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Contacto | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Contacto | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Contacto | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Contacto | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Contacto | Escríbenos | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Asunto» (elige una opción de la lista) · El navegador no deja enviarlo: «Tu nombre» (campo obligatorio) |
| Contacto | Ve a «Denunciar contenido» | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Contacto | Asunto | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Enviar mensaje» (sin efecto inmediato, correcto) |
| Contacto | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Contacto | Leer | Botón | Funciona | Abre la ventana «Contacto» |
| Contacto | Quién somos | Enlace | Funciona | Cambia tabindex en h2#quien-somos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Contacto | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Contacto | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Créditos y licencias de terceros · `#/legal/creditos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Créditos y licencias de terceros | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Créditos y licencias de terceros | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Créditos y licencias de terceros | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Créditos y licencias de terceros | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Créditos y licencias de terceros | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Créditos y licencias de terceros | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Créditos y licencias de terceros | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Créditos y licencias de terceros | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Créditos y licencias de terceros | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Créditos y licencias de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Créditos y licencias de terceros | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Créditos y licencias de terceros | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Créditos y licencias de terceros | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Créditos y licencias de terceros | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Créditos y licencias de terceros | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Créditos y licencias de terceros | OpenStreetMap contributors | Enlace externo | Funciona | Enlace externo a www.openstreetmap.org (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Protomaps | Enlace externo | Funciona | Enlace externo a protomaps.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Esri World Imagery | Enlace externo | Funciona | Enlace externo a www.arcgis.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | gebco.net | Enlace externo | Funciona | Enlace externo a www.gebco.net (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leaflet | Enlace externo | Funciona | Enlace externo a leafletjs.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leaflet.markercluster | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | protomaps-leaflet | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | qrcode | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | stripe-python | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | fontTools | Enlace externo | Funciona | Enlace externo a github.com (no se abre: dirección https válida) |
| Créditos y licencias de terceros | Leer | Botón | Funciona | Abre la ventana «Créditos y licencias de terceros» |
| Créditos y licencias de terceros | Mapas y datos geográficos | Enlace | Funciona | Cambia tabindex en h2#mapas-y-datos-geograficos (sin atributo → -1) · hay 3 más iguales en la lista (no se prueban todos) |
| Créditos y licencias de terceros | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Créditos y licencias de terceros | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Condiciones de uso para buceadores · `#/legal/terminos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Condiciones de uso para buceadores | Volver a la pantalla anterior | Botón | Funciona | Vuelve a la página anterior |
| Condiciones de uso para buceadores | Aviso legal | Enlace | Funciona | Mismo enlace (#/legal/aviso-legal) que «Aviso legal» en «Encuentra tu próxima inmersión»: Abre #/legal/aviso-legal |
| Condiciones de uso para buceadores | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-buceadores |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/reservas) que «Condiciones de reserva, pago y cancelaci» en «Aviso legal»: Abre #/legal/reservas |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Encuentra tu próxima inmersión»: Abre #/legal/cookies |
| Condiciones de uso para buceadores | Condiciones para centros y profesionales | Enlace | Funciona | Mismo enlace (#/legal/condiciones-centros) que «Condiciones para centros» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-centros |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |
| Condiciones de uso para buceadores | Seguridad en el buceo | Enlace | Funciona | Mismo enlace (#/legal/seguridad) que «Seguridad en el buceo» en «El mapa del buceo»: Abre #/legal/seguridad |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Declaración de accesibilidad | Enlace | Funciona | Mismo enlace (#/legal/accesibilidad) que «Declaración de accesibilidad» en «Aviso legal»: Abre #/legal/accesibilidad |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Créditos y licencias de terceros | Enlace | Funciona | Mismo enlace (#/legal/creditos) que «Créditos y licencias de terceros» en «Aviso legal»: Abre #/legal/creditos |
| Condiciones de uso para buceadores | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Encuentra tu próxima inmersión»: Abre #/legal/privacidad |
| Condiciones de uso para buceadores | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Mismo enlace (#/legal/condiciones-reserva) que «Condiciones de reserva» en «Encuentra tu próxima inmersión»: Abre #/legal/condiciones-reserva |
| Condiciones de uso para buceadores | Normas de las reseñas | Enlace | Funciona | Mismo enlace (#/legal/normas-resenas) que «Normas de las reseñas» en «Aviso legal»: Abre #/legal/normas-resenas |
| Condiciones de uso para buceadores | Puntos WORLDIVES | Enlace | Funciona | Mismo enlace (#/legal/puntos) que «Puntos WORLDIVES» en «Aviso legal»: Abre #/legal/puntos |
| Condiciones de uso para buceadores | Cómo ordenamos los resultados | Enlace | Funciona | Mismo enlace (#/legal/clasificacion) que «¿Cómo ordenamos?» en «Puntos de buceo»: Abre #/legal/clasificacion |
| Condiciones de uso para buceadores | Contacto | Enlace | Funciona | Mismo enlace (#/legal/contacto) que «Contacto» en «Aviso legal»: Abre #/legal/contacto |
| Condiciones de uso para buceadores | Leer | Botón | Funciona | Abre la ventana «Condiciones de uso para buceadores» |
| Condiciones de uso para buceadores | 1. Qué es WORLDIVES DISCOVERY | Enlace | Funciona | Cambia tabindex en h2 (sin atributo → -1) · hay 9 más iguales en la lista (no se prueban todos) |
| Condiciones de uso para buceadores | Imprimir o guardar en PDF | Botón | Funciona | Abre la impresión |
| Condiciones de uso para buceadores | Denunciar contenido | Enlace | Funciona | Mismo enlace (#/legal/denuncias) que «Denunciar contenido» en «Encuentra tu próxima inmersión»: Abre #/legal/denuncias |

#### Centro de control de WORLDIVES · Inicio · `#/admin`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Inicio | Ver Mapas | Enlace | Funciona | Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Inicio | Inicio | Botón | Funciona | Muestra contenido nuevo (1 elementos): «CATÁLOGO Gestionar puntos de buceo 293 puntos activos. Crear, editar, archivar y corregir ubicaciones. VIDA MARINA Y VÍD» |
| Centro de control de WORLDIVES · Inicio | Puntos | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «Nuevo punto» |
| Centro de control de WORLDIVES · Inicio | Reservas | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «FECHA CLIENTE CENTRO SERVICIO / PUNTO ESTADO Lun, 9 nov 08:30 Bea Navarro bea.navarro@example.com Bahía Coralina Centro » |
| Centro de control de WORLDIVES · Inicio | Pagos | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «Seguridad de cobros Pagos online Cada cobro va directamente a la cuenta de Stripe del centro o profesional (cargo direct» |
| Centro de control de WORLDIVES · Inicio | Correos | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (3 elementos): «Correos automáticos Correos de la plataforma Cada reserva, pago, cancelación o aviso genera su correo en el idioma del d» |
| Centro de control de WORLDIVES · Inicio | Legal | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (6 elementos): «Legal Datos del titular y documentos legales Estos datos se insertan en el aviso legal, la privacidad, las condiciones y» |
| Centro de control de WORLDIVES · Inicio | Descripciones de puntos | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «Catálogo Descripciones de los puntos de buceo Todas las descripciones se han reescrito con texto propio a partir de los » |
| Centro de control de WORLDIVES · Inicio | Mapas | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «Mapas Mapa base, satélite y batimetría El mapa base se sirve desde nuestro servidor. La vista satélite pasa por nuestro » |
| Centro de control de WORLDIVES · Inicio | Planes | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «Planes Planes, cuotas y excepciones El precio es la cuota anual (pendiente de confirmar con la gestoría si se muestra co» |
| Centro de control de WORLDIVES · Inicio | Funciones | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «Funciones Activar u ocultar funciones de la web Al desactivar una función desaparece de la web y el servidor rechaza su » |
| Centro de control de WORLDIVES · Inicio | Operación | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «Operación Estado del servidor, copias y avisos Versión 50.51 · en marcha desde hace 0 h · 1 proceso(s) · base de 5.12 MB» |
| Centro de control de WORLDIVES · Inicio | Vida marina y vídeos | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (3 elementos): «Vida marina y vídeos de los puntos Catálogo de especies (nombre en cada idioma, foto con su autor y licencia) y vídeos d» |
| Centro de control de WORLDIVES · Inicio | Experiencias | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «Experiencias de viaje Los centros y profesionales pueden proponer viajes. Desde aquí el administrador puede publicar o r» |
| Centro de control de WORLDIVES · Inicio | Destinos | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (3 elementos): «Destinos de Experiencias Estos destinos alimentan la sección Experiencias. Puedes crear nuevos destinos desde aquí.» |
| Centro de control de WORLDIVES · Inicio | Imágenes de la web | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (6 elementos): «Apariencia Temas de temporada Cambia las fotos y el color de la web según la época del año o la zona del visitante. Fuer» |
| Centro de control de WORLDIVES · Inicio | Patrocinio | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (3 elementos): «Portada Patrocinio y colaboradores Lo que pongas aquí aparece en la parte baja de la portada: la banda de logos que se d» |
| Centro de control de WORLDIVES · Inicio | Usuarios | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (1 elementos): «NOMBRE EMAIL ROL CENTRO ALTA Admin Inventario admin@inventario.example.org Recreativo Centro Freelance Administrador — B» |
| Centro de control de WORLDIVES · Inicio | Centros | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «Nuevo centro» |
| Centro de control de WORLDIVES · Inicio | Verificaciones | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «Verificación de cuentas profesionales Nadie obtiene el rol de centro o profesional al registrarse. Antes de aprobar, com» |
| Centro de control de WORLDIVES · Inicio | Correcciones | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «Una corrección aprobada sustituye las coordenadas oficiales del punto y queda registrada.» |
| Centro de control de WORLDIVES · Inicio | QR | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (5 elementos): «Genera un QR para la recepción de un centro. El cliente lo escanea con el móvil; si ya ha iniciado sesión, el centro que» |
| Centro de control de WORLDIVES · Inicio | Actividad | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «Historial de las acciones administrativas y de gestión registradas por WORLDIVES.» |
| Centro de control de WORLDIVES · Inicio | Recompensas | Botón | Funciona | Cambia su estado (class: tab → tab active) · Muestra contenido nuevo (2 elementos): «PUNTOS WORLDIVES Ventajas de los centros Los buceadores canjean sus puntos por las ventajas que tu centro define y paga.» |
| Centro de control de WORLDIVES · Inicio | Gestionar puntos de buceo | Enlace | Funciona | Abre #/admin?tab=points |
| Centro de control de WORLDIVES · Inicio | Especies y vídeos de las rutas | Enlace | Funciona | Abre #/admin?tab=marina |
| Centro de control de WORLDIVES · Inicio | Gestionar experiencias | Enlace | Funciona | Abre #/admin?tab=experiences |
| Centro de control de WORLDIVES · Inicio | Gestionar destinos | Enlace | Funciona | Abre #/admin?tab=destinations |
| Centro de control de WORLDIVES · Inicio | Usuarios y permisos | Enlace | Funciona | Abre #/admin?tab=users |
| Centro de control de WORLDIVES · Inicio | PROVEEDORES Centros de buceo 2 centros y sus puntos asociados. | Enlace | Funciona | Abre #/admin?tab=centers |
| Centro de control de WORLDIVES · Inicio | OPERACIÓN Reservas 1000 reservas y solicitudes. | Enlace | Funciona | Abre #/admin?tab=bookings |
| Centro de control de WORLDIVES · Inicio | Actividad administrativa | Enlace | Funciona | Abre #/admin?tab=audit |

#### Hola, Admin · `#/area`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Hola, Admin | Explorador 0 puntos | Enlace | Funciona | Abre #/recompensas |
| Hola, Admin | Administración | Enlace | Funciona | Abre #/admin |
| Hola, Admin | Log Book | Enlace | Funciona | Abre #/logbook |
| Hola, Admin | Recompensas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Hola, Admin»: Abre #/recompensas |
| Hola, Admin | Mis puntos | Enlace | Funciona | Abre #/mis-puntos |
| Hola, Admin | Mi cuenta | Enlace | Funciona | Abre #/cuenta |
| Hola, Admin | Reservar una inmersión | Enlace | Funciona | Abre #/centros |
| Hola, Admin | 0 próximas reservas | Botón | Funciona | Desplaza la página |
| Hola, Admin | 0 avisos sin leer | Botón | Funciona | Desplaza la página |
| Hola, Admin | 0 documentos | Enlace | Funciona | Abre #/cuenta?docs=1 |
| Hola, Admin | Buscar centros | Enlace | Funciona | Mismo enlace (#/centros) que «Reservar una inmersión» en «Hola, Admin»: Abre #/centros |
| Hola, Admin | Cerca de mí | Enlace | Funciona | Abre #/top10 |
| Hola, Admin | Próximas 0 | Botón | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) · Cambia el texto: «Ver las 0 reservas» |
| Hola, Admin | Historial 0 | Botón | Funciona | Cambia su estado (class: sin atributo → is-on) · Cambia la pantalla (0 elementos nuevos, 1 quitados) |
| Hola, Admin | Explorar | Enlace | Funciona | Abre #/experiencias |
| Hola, Admin | Completar mi ficha | Enlace | Funciona | Mismo enlace (#/cuenta) que «Mi cuenta» en «Hola, Admin»: Abre #/cuenta |
| Hola, Admin | Gestionar | Enlace | Funciona | Mismo enlace (#/cuenta?docs=1) que «0 documentos» en «Hola, Admin»: Abre #/cuenta?docs=1 |

#### Hola, Admin › Historial · `#/area` (1 clic en subpestaña)

Sin elementos nuevos que probar (los comunes ya se han probado en otra pantalla).

#### Tu ficha de buceador · `#/cuenta`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Tu ficha de buceador | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Hola, Admin»: Abre #/recompensas |
| Tu ficha de buceador | Datos personales | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Nombre y apellidos» (campo obligatorio) |
| Tu ficha de buceador | Prefijo del país | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Idioma preferido | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Nivel de certificación | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | ¿Sueles alquilar equipo? | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Tipo de traje | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Documentación | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Título» (campo obligatorio) · El navegador no deja enviarlo: «Archivo (PDF o imagen, máximo 10 MB)» (falta el archivo) |
| Tu ficha de buceador | Tipo | Desplegable | Funciona | Campo de un formulario: el cambio se aplica al enviarlo (sin efecto inmediato, correcto) |
| Tu ficha de buceador | Seguridad | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Contraseña actual» (campo obligatorio) · El navegador no deja enviarlo: «Nueva contraseña» (campo obligatorio) |
| Tu ficha de buceador | Activar | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Tu contraseña» (campo obligatorio) |
| Tu ficha de buceador | Descargar mis datos (ZIP) | Enlace | Funciona | Descarga /api/account/export?format=zip (200, application/zip) |
| Tu ficha de buceador | Privacidad | Enlace | Funciona | Abre #/legal/privacidad |
| Tu ficha de buceador | Condiciones de uso | Enlace | Funciona | Abre #/legal/condiciones-buceadores |
| Tu ficha de buceador | Condiciones de reserva | Enlace | Funciona | Abre #/legal/condiciones-reserva |
| Tu ficha de buceador | Cookies | Enlace | Funciona | Abre #/legal/cookies |
| Tu ficha de buceador | Abrir el panel | Enlace | Funciona | Mismo enlace (#/admin) que «Administración» en «Hola, Admin»: Abre #/admin |
| Tu ficha de buceador | Cerrar sesión | Botón | Funciona | [probado al final del papel] Abre #/ · POST /api/auth/logout → 200 · cierra la sesión o cambia la cuenta: se vuelve a iniciar sesión |

#### Log Book · `#/logbook`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Log Book | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Hola, Admin»: Abre #/recompensas |
| Log Book | Exportar CSV | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Tu historial de inmersiones. Las reservas completadas se añaden solas; el resto, en un momento.» |
| Log Book | Nueva inmersión | Botón | Funciona | Abre la ventana «Nueva inmersión» |
| Log Book | Añadir mi primera inmersión | Botón | Funciona | Abre la ventana «Nueva inmersión» |

#### Recompensas · `#/recompensas`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Recompensas | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Hola, Admin»: Abre #/recompensas |
| Recompensas | Cómo funcionan | Enlace | Funciona | Abre #/como-funcionan-los-puntos |
| Recompensas | Canjear | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Linterna para la nocturna» · hay 2 más iguales en la lista (no se prueban todos) |
| Recompensas | Canjear | Botón | Desactivado (correcto) | Desactivado; la pantalla explica: «Te faltan 150 puntos» |

#### Mis puntos · `#/mis-puntos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Mis puntos | Explorador 0 puntos | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Hola, Admin»: Abre #/recompensas |
| Mis puntos | Ver ventajas | Enlace | Funciona | Mismo enlace (#/recompensas) que «Explorador 0 puntos» en «Hola, Admin»: Abre #/recompensas |
| Mis puntos | Más información sobre los puntos | Enlace | Funciona | Mismo enlace (#/como-funcionan-los-puntos) que «Cómo funcionan» en «Recompensas»: Abre #/como-funcionan-los-puntos |

#### Centro de control de WORLDIVES · Mapas · `#/admin?tab=maps`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Mapas | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Mapas | Mapa base, satélite y batimetría | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Límite mensual de teselas satélite» (campo obligatorio) |

#### Centro de control de WORLDIVES · Puntos · `#/admin?tab=points`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Puntos | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Puntos | Nuevo punto | Botón | Funciona | Muestra contenido nuevo (42 elementos): «Gestión / Nuevo punto CATÁLOGO Nuevo punto La posición se puede introducir manualmente o seleccionando una localización » |
| Centro de control de WORLDIVES · Puntos | Editar | Botón | Funciona | Muestra contenido nuevo (36 elementos): «Gestión / Editar punto CATÁLOGO Editar punto La posición se puede introducir manualmente o seleccionando una localizació» · hay 291 más iguales en la lista (no se prueban todos) |
| Centro de control de WORLDIVES · Puntos | Editar | Botón | Funciona | Muestra contenido nuevo (38 elementos): «Gestión / Editar punto CATÁLOGO Editar punto La posición se puede introducir manualmente o seleccionando una localizació» |

#### Centro de control de WORLDIVES · Vida marina y vídeos · `#/admin?tab=marina`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Vida marina y vídeos | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Vida marina y vídeos | Pendientes (1) | Botón | Funciona | Abre #/admin?tab=marina&sub=pendientes |
| Centro de control de WORLDIVES · Vida marina y vídeos | Especies | Botón | Funciona | Abre #/admin?tab=marina&sub=especies |
| Centro de control de WORLDIVES · Vida marina y vídeos | Vídeos | Botón | Funciona | Abre #/admin?tab=marina&sub=videos |
| Centro de control de WORLDIVES · Vida marina y vídeos | Piedras Rotas | Enlace | Funciona | Abre #/admin?tab=points&edit=332 |
| Centro de control de WORLDIVES · Vida marina y vídeos | Aprobar | Botón | Funciona | Aviso: «Publicado.» · Muestra contenido nuevo (2 elementos): «Vida marina y vídeos de los puntos Catálogo de especies (nombre en cada idioma, foto con su autor y licencia) y vídeos d» · POST /api/admin/marina/revisar → 200 |
| Centro de control de WORLDIVES · Vida marina y vídeos | Rechazar | Botón | Funciona | Pide un dato (prompt) «Motivo del rechazo (lo verá quien lo propuso):» (cancelado) |

#### Centro de control de WORLDIVES · Vida marina y vídeos › Vídeos · `#/admin?tab=marina&sub=videos` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Vida marina y vídeos › Vídeos | Estado | Desplegable | Funciona | Muestra contenido nuevo (1 elementos): «No hay vídeos con este filtro.» |

#### Centro de control de WORLDIVES · Vida marina y vídeos › Especies · `#/admin?tab=marina&sub=especies` (1 clic en subpestaña)

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Vida marina y vídeos › Especies | + Nueva especie | Botón | Funciona | Abre la ventana «Nueva especie» |
| Centro de control de WORLDIVES · Vida marina y vídeos › Especies | Editar | Botón | Funciona | Abre la ventana «Editar especie» · hay 29 más iguales en la lista (no se prueban todos) |
| Centro de control de WORLDIVES · Vida marina y vídeos › Especies | Editar | Botón | Funciona | Abre la ventana «Editar especie» |

#### Centro de control de WORLDIVES · Experiencias · `#/admin?tab=experiences`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Experiencias | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Experiencias | Publicar | Botón | Funciona | Aviso: «Estado actualizado.» · Muestra contenido nuevo (3 elementos): «CUENTA ADMINISTRADOR Centro de control de WORLDIVES Control administrativo de WORLDIVES DISCOVERY. Añade la clave de Arc» · POST /api/admin/travel-experiences/status → 200 |
| Centro de control de WORLDIVES · Experiencias | Rechazar | Botón | Funciona | Aviso: «Estado actualizado.» · Muestra contenido nuevo (3 elementos): «CUENTA ADMINISTRADOR Centro de control de WORLDIVES Control administrativo de WORLDIVES DISCOVERY. Añade la clave de Arc» · POST /api/admin/travel-experiences/status → 200 |

#### Centro de control de WORLDIVES · Destinos · `#/admin?tab=destinations`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Destinos | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Destinos | Nuevo destino | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión / Nuevo destino EXPERIENCIAS Nuevo destino Nombre del destino Región / país Tipo Foto del destino Sin foto Fotos» |
| Centro de control de WORLDIVES · Destinos | Editar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión / Editar destino EXPERIENCIAS Editar destino Nombre del destino Región / país Tipo Foto del destino Sin foto Fot» · hay 5 más iguales en la lista (no se prueban todos) |
| Centro de control de WORLDIVES · Destinos | Editar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Gestión / Editar destino EXPERIENCIAS Editar destino Nombre del destino Región / país Tipo Foto del destino Fotos reales» |

#### Centro de control de WORLDIVES · Usuarios · `#/admin?tab=users`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Usuarios | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Usuarios | ROL · Admin Inventario | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Admin Inventario | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | Guardar | Botón | Funciona | Aviso: «Rol actualizado.» · POST /api/admin/users/role → 200 · cierra la sesión o cambia la cuenta: se vuelve a iniciar sesión · hay 29 más iguales en la lista (no se prueban todos) |
| Centro de control de WORLDIVES · Usuarios | ROL · Nerea Galván | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Nerea Galván | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | Guardar | Botón | Funciona | Aviso: «Rol actualizado.» · POST /api/admin/users/role → 200 |
| Centro de control de WORLDIVES · Usuarios | ROL · Marta Llorens | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Marta Llorens | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Jordi Pujadas | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Jordi Pujadas | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Diego Arenas | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Diego Arenas | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Sara Molina | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Sara Molina | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Bea Navarro | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Bea Navarro | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Lukas Becker | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Lukas Becker | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Chloé Martin | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Chloé Martin | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Giulia Romano | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Giulia Romano | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Tom Jansen | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Tom Jansen | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Emily Clarke | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Emily Clarke | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Kasia Nowak | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Kasia Nowak | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Wei Chen | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Wei Chen | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · João Silva | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · João Silva | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Álvaro Ruiz | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Álvaro Ruiz | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Nuria Costa | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Nuria Costa | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Pierre Lambert | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Pierre Lambert | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Hannah Weber | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Hannah Weber | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Marco Bianchi | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Marco Bianchi | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Sofie de Vries | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Sofie de Vries | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · James Walker | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · James Walker | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Lucía Prieto | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Lucía Prieto | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Raúl Ortega | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Raúl Ortega | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Anna Kowalska | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Anna Kowalska | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Li Na | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Li Na | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Iván Soler | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Iván Soler | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Elena Ribas | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Elena Ribas | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Pau Ferrer | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Pau Ferrer | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Clara Vidal | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Clara Vidal | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | ROL · Rosa Domènech | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Usuarios | CENTRO · Rosa Domènech | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |

#### Centro de control de WORLDIVES · Centros · `#/admin?tab=centers`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Centros | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Centros | Nuevo centro | Botón | Funciona | Muestra contenido nuevo (36 elementos): «Gestión / Nuevo centro CENTROS Nuevo centro Nombre País Aruba Australia Bahamas Barbados Belice Bonaire Colombia Costa R» |
| Centro de control de WORLDIVES · Centros | Editar | Botón | Funciona | Muestra contenido nuevo (36 elementos): «Gestión / Editar centro CENTROS Editar centro Nombre País Aruba Australia Bahamas Barbados Belice Bonaire Colombia Costa» |
| Centro de control de WORLDIVES · Centros | Editar | Botón | Funciona | Muestra contenido nuevo (38 elementos): «Gestión / Editar centro CENTROS Editar centro Nombre País Aruba Australia Bahamas Barbados Belice Bonaire Colombia Costa» |

#### Centro de control de WORLDIVES · Reservas · `#/admin?tab=bookings`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Reservas | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Reservas | Ver ficha | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Mi área / Reserva WOD-001236 WORLDIVES DISCOVERY · RESERVA DEL CENTRO Bahía Coralina Centro de Buceo 9/11/2026 · 08:30 C» · hay 498 más iguales en la lista (no se prueban todos) |
| Centro de control de WORLDIVES · Reservas | Ver ficha | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Mi área / Reserva WOD-001285 WORLDIVES DISCOVERY · RESERVA DEL CENTRO Diego Arenas 2/11/2026 · 08:00 Solicitada TU INMER» |
| Centro de control de WORLDIVES · Reservas | Cancelar | Botón | Funciona | Aviso: «Estado actualizado.» · Muestra contenido nuevo (3 elementos): «CUENTA ADMINISTRADOR Centro de control de WORLDIVES Control administrativo de WORLDIVES DISCOVERY. Añade la clave de Arc» · POST /api/bookings/1262/status → 200 · hay 43 más iguales en la lista (no se prueban todos) |
| Centro de control de WORLDIVES · Reservas | Cancelar | Botón | Funciona | Aviso: «Estado actualizado.» · Muestra contenido nuevo (3 elementos): «CUENTA ADMINISTRADOR Centro de control de WORLDIVES Control administrativo de WORLDIVES DISCOVERY. Añade la clave de Arc» · POST /api/bookings/1255/status → 200 |

#### Centro de control de WORLDIVES · Actividad · `#/admin?tab=audit`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Actividad | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |

#### Centro de control de WORLDIVES · Pagos · `#/admin?tab=adminpay`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Pagos | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Pagos | Todos | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Seguridad de cobros Pagos online Cada cobro va directamente a la cuenta de Stripe del centro o profesional (cargo direct» |
| Centro de control de WORLDIVES · Pagos | Incidencias | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Seguridad de cobros Pagos online Cada cobro va directamente a la cuenta de Stripe del centro o profesional (cargo direct» |
| Centro de control de WORLDIVES · Pagos | En revisión | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Seguridad de cobros Pagos online Cada cobro va directamente a la cuenta de Stripe del centro o profesional (cargo direct» |
| Centro de control de WORLDIVES · Pagos | En curso | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Seguridad de cobros Pagos online Cada cobro va directamente a la cuenta de Stripe del centro o profesional (cargo direct» |
| Centro de control de WORLDIVES · Pagos | Cobrados | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Seguridad de cobros Pagos online Cada cobro va directamente a la cuenta de Stripe del centro o profesional (cargo direct» |
| Centro de control de WORLDIVES · Pagos | Devolución parcial | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Seguridad de cobros Pagos online Cada cobro va directamente a la cuenta de Stripe del centro o profesional (cargo direct» |
| Centro de control de WORLDIVES · Pagos | Devueltos | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Seguridad de cobros Pagos online Cada cobro va directamente a la cuenta de Stripe del centro o profesional (cargo direct» |
| Centro de control de WORLDIVES · Pagos | Caducados | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Seguridad de cobros Pagos online Cada cobro va directamente a la cuenta de Stripe del centro o profesional (cargo direct» |

#### Centro de control de WORLDIVES · Correos · `#/admin?tab=emails`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Correos | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Correos | Enviar prueba | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «tu@email.com» (campo obligatorio) |
| Centro de control de WORLDIVES · Correos | 0 En cola | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Correos automáticos Correos de la plataforma Cada reserva, pago, cancelación o aviso genera su correo en el idioma del d» |
| Centro de control de WORLDIVES · Correos | 0 Enviando | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Correos automáticos Correos de la plataforma Cada reserva, pago, cancelación o aviso genera su correo en el idioma del d» |
| Centro de control de WORLDIVES · Correos | 1 Enviado | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Correos automáticos Correos de la plataforma Cada reserva, pago, cancelación o aviso genera su correo en el idioma del d» |
| Centro de control de WORLDIVES · Correos | 0 Fallido | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Correos automáticos Correos de la plataforma Cada reserva, pago, cancelación o aviso genera su correo en el idioma del d» |
| Centro de control de WORLDIVES · Correos | 0 Sin email real | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Correos automáticos Correos de la plataforma Cada reserva, pago, cancelación o aviso genera su correo en el idioma del d» |
| Centro de control de WORLDIVES · Correos | 0 Caducado | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Correos automáticos Correos de la plataforma Cada reserva, pago, cancelación o aviso genera su correo en el idioma del d» |
| Centro de control de WORLDIVES · Correos | 1 Todos | Botón | Funciona | Muestra contenido nuevo (2 elementos): «Correos automáticos Correos de la plataforma Cada reserva, pago, cancelación o aviso genera su correo en el idioma del d» |
| Centro de control de WORLDIVES · Correos | Plantilla | Desplegable | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) |
| Centro de control de WORLDIVES · Correos | Idioma | Desplegable | Funciona | Cambia la pantalla (0 elementos nuevos, 1 quitados) |
| Centro de control de WORLDIVES · Correos | Comunicación comercial | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Asunto» (campo obligatorio) · El navegador no deja enviarlo: «Texto» (campo obligatorio) |
| Centro de control de WORLDIVES · Correos | Enviarme una prueba | Botón | Funciona | Aviso: «Escribe el asunto y el texto.» · POST /api/admin/marketing/send → 400 «Escribe el asunto y el texto.» |

#### Centro de control de WORLDIVES · Legal · `#/admin?tab=legal`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Legal | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Legal | Datos del titular y documentos legales | Formulario | Funciona | Enviado vacío · Aviso: «Datos legales guardados.» · Muestra contenido nuevo (5 elementos): «Legal Datos del titular y documentos legales Estos datos se insertan en el aviso legal, la privacidad, las condiciones y» · POST /api/admin/legal → 200 |
| Centro de control de WORLDIVES · Legal | Conservación de datos | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Cuentas de buceador sin actividad (meses)» (campo obligatorio) · El navegador no deja enviarlo: «Documentos caducados (meses)» (campo obligatorio) |
| Centro de control de WORLDIVES · Legal | Guardar y aplicar ahora | Botón | Funciona | Pide confirmación «Se borrarán ahora los datos que hayan superado los plazos. ¿Continuar?» (cancelado) |
| Centro de control de WORLDIVES · Legal | Aviso legal | Enlace | Funciona | Abre una pestaña nueva /?lang=es&_=183#/legal/aviso-legal |
| Centro de control de WORLDIVES · Legal | Editar | Botón | Funciona | Abre la ventana «Editar «Aviso legal»» · hay 12 más iguales en la lista (no se prueban todos) |
| Centro de control de WORLDIVES · Legal | Condiciones de uso para buceadores | Enlace | Funciona | Mismo enlace (#/legal/condiciones-buceadores) que «Condiciones de uso» en «Tu ficha de buceador»: Abre #/legal/condiciones-buceadores |
| Centro de control de WORLDIVES · Legal | Editar | Botón | Funciona | Abre la ventana «Editar «Condiciones de uso para buceadores»» |
| Centro de control de WORLDIVES · Legal | Condiciones de reserva, pago y cancelación | Enlace | Funciona | Abre una pestaña nueva /?lang=es&_=186#/legal/reservas |
| Centro de control de WORLDIVES · Legal | Política de privacidad | Enlace | Funciona | Mismo enlace (#/legal/privacidad) que «Privacidad» en «Tu ficha de buceador»: Abre #/legal/privacidad |
| Centro de control de WORLDIVES · Legal | Política de cookies y servicios de terceros | Enlace | Funciona | Mismo enlace (#/legal/cookies) que «Cookies» en «Tu ficha de buceador»: Abre #/legal/cookies |
| Centro de control de WORLDIVES · Legal | Condiciones para centros y profesionales | Enlace | Funciona | Abre una pestaña nueva /?lang=es&_=187#/legal/condiciones-centros |
| Centro de control de WORLDIVES · Legal | Normas de las reseñas | Enlace | Funciona | Abre una pestaña nueva /?lang=es&_=188#/legal/normas-resenas |
| Centro de control de WORLDIVES · Legal | Cómo ordenamos los resultados | Enlace | Funciona | Abre una pestaña nueva /?lang=es&_=189#/legal/clasificacion |
| Centro de control de WORLDIVES · Legal | Denunciar contenido | Enlace | Funciona | Abre una pestaña nueva /?lang=es&_=190#/legal/denuncias |
| Centro de control de WORLDIVES · Legal | Seguridad en el buceo | Enlace | Funciona | Abre una pestaña nueva /?lang=es&_=191#/legal/seguridad |
| Centro de control de WORLDIVES · Legal | Puntos WORLDIVES | Enlace | Funciona | Abre una pestaña nueva /?lang=es&_=192#/legal/puntos |
| Centro de control de WORLDIVES · Legal | Declaración de accesibilidad | Enlace | Funciona | Abre una pestaña nueva /?lang=es&_=193#/legal/accesibilidad |
| Centro de control de WORLDIVES · Legal | Contacto | Enlace | Funciona | Abre una pestaña nueva /?lang=es&_=194#/legal/contacto |
| Centro de control de WORLDIVES · Legal | Créditos y licencias de terceros | Enlace | Funciona | Abre una pestaña nueva /?lang=es&_=195#/legal/creditos |
| Centro de control de WORLDIVES · Legal | Abrir | Enlace | Funciona | Abre en otra pestaña /#/centro?id=31 (200, text/html) |
| Centro de control de WORLDIVES · Legal | Resolver | Botón | Funciona | Abre la ventana «Resolver denuncia» |

#### Centro de control de WORLDIVES · Descripciones de puntos · `#/admin?tab=pointtexts`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Descripciones de puntos | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Descripciones de puntos | Regenerar desde los datos | Botón | Funciona | Aviso: «Descripción regenerada.» · Muestra contenido nuevo (1 elementos): «Catálogo Descripciones de los puntos de buceo Todas las descripciones se han reescrito con texto propio a partir de los » · POST /api/admin/point-texts/review → 200 · hay 291 más iguales en la lista (no se prueban todos) |
| Centro de control de WORLDIVES · Descripciones de puntos | Guardar y marcar como revisada | Botón | Funciona | Aviso: «Descripción revisada.» · Muestra contenido nuevo (1 elementos): «Catálogo Descripciones de los puntos de buceo Todas las descripciones se han reescrito con texto propio a partir de los » · POST /api/admin/point-texts/review → 200 · hay 291 más iguales en la lista (no se prueban todos) |
| Centro de control de WORLDIVES · Descripciones de puntos | Regenerar desde los datos | Botón | Funciona | Aviso: «Descripción regenerada.» · Muestra contenido nuevo (1 elementos): «Catálogo Descripciones de los puntos de buceo Todas las descripciones se han reescrito con texto propio a partir de los » · POST /api/admin/point-texts/review → 200 |
| Centro de control de WORLDIVES · Descripciones de puntos | Guardar y marcar como revisada | Botón | Funciona | Aviso: «Descripción revisada.» · Muestra contenido nuevo (1 elementos): «Catálogo Descripciones de los puntos de buceo Todas las descripciones se han reescrito con texto propio a partir de los » · POST /api/admin/point-texts/review → 200 |

#### Centro de control de WORLDIVES · Planes · `#/admin?tab=plans`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Planes | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Planes | free | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Nombre» (campo obligatorio) |
| Centro de control de WORLDIVES · Planes | booking | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Nombre» (campo obligatorio) |
| Centro de control de WORLDIVES · Planes | pro | Formulario | Funciona | Enviado vacío · El navegador no deja enviarlo: «Nombre» (campo obligatorio) |
| Centro de control de WORLDIVES · Planes | Planes, cuotas y excepciones | Formulario | Funciona | Enviado vacío · Aviso: «Los días de prueba tienen que ser un número.» · POST /api/admin/plans/settings → 400 «Los días de prueba tienen que ser un número.» |
| Centro de control de WORLDIVES · Planes | Plan de la prueba | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Guardar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Planes | Año | Desplegable | Funciona | Cambia href en a#ap-dac7.btn (/api/admin/dac7?format=csv&yea → /api/admin/dac7?format=csv&yea) |
| Centro de control de WORLDIVES · Planes | Descargar CSV | Enlace | Funciona | Descarga /api/admin/dac7?format=csv&year=2025 (200, text/csv) |
| Centro de control de WORLDIVES · Planes | Gestionar | Botón | Funciona | Abre la ventana «Bahía Coralina Centro de Buceo» · hay 2 más iguales en la lista (no se prueban todos) |
| Centro de control de WORLDIVES · Planes | Gestionar | Botón | Funciona | Abre la ventana «Escafandra Medes» |

#### Centro de control de WORLDIVES · Funciones · `#/admin?tab=features`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Funciones | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Funciones | Activar u ocultar funciones de la web | Formulario | Funciona | Enviado vacío · Aviso: «Funciones guardadas.» · POST /api/admin/features → 200 |
| Centro de control de WORLDIVES · Funciones | Activar u ocultar funciones de la web | Formulario | Funciona | Enviado vacío · Aviso: «Invitación WOD-840A303E creada.» · Muestra contenido nuevo (1 elementos): «Funciones Activar u ocultar funciones de la web Al desactivar una función desaparece de la web y el servidor rechaza su » · POST /api/admin/invites → 200 |

#### Centro de control de WORLDIVES · Operación · `#/admin?tab=ops`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Operación | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Operación | Actualizar | Botón | Funciona | Muestra contenido nuevo (1 elementos): «Operación Estado del servidor, copias y avisos Versión 50.51 · en marcha desde hace 0 h · 1 proceso(s) · base de 5.12 MB» |
| Centro de control de WORLDIVES · Operación | Estado del servidor, copias y avisos | Formulario | Funciona | Enviado vacío · Aviso: «Escribe el texto del aviso.» |
| Centro de control de WORLDIVES · Operación | Tipo | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Publicar aviso» (sin efecto inmediato, correcto) |

#### Centro de control de WORLDIVES · Imágenes de la web · `#/admin?tab=media`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Imágenes de la web | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Imágenes de la web | Nuevo tema | Botón | Funciona | Abre la ventana «Nuevo tema» |
| Centro de control de WORLDIVES · Imágenes de la web | Guardar crédito | Botón | Funciona | Aviso: «Adjunta una foto.» · POST /api/admin/site-media → 400 «Adjunta una foto.» · hay 21 más iguales en la lista (no se prueban todos) |
| Centro de control de WORLDIVES · Imágenes de la web | Guardar crédito | Botón | Funciona | Aviso: «Adjunta una foto.» · POST /api/admin/site-media → 400 «Adjunta una foto.» |
| Centro de control de WORLDIVES · Imágenes de la web | Guardar | Botón | Funciona | Aviso: «Guardado.» · Muestra contenido nuevo (1 elementos): «Imágenes Origen y licencia de las imágenes Indica de dónde sale cada imagen (foto propia, banco de imágenes con su licen» · POST /api/admin/images → 200 · hay 55 más iguales en la lista (no se prueban todos) |
| Centro de control de WORLDIVES · Imágenes de la web | Guardar | Botón | Funciona | Aviso: «Guardado.» · Muestra contenido nuevo (1 elementos): «Imágenes Origen y licencia de las imágenes Indica de dónde sale cada imagen (foto propia, banco de imágenes con su licen» · POST /api/admin/images → 200 |

#### Centro de control de WORLDIVES · Patrocinio · `#/admin?tab=promos`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Patrocinio | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Patrocinio | + Añadir colaborador | Botón | Funciona | Abre la ventana «Nuevo colaborador» |
| Centro de control de WORLDIVES · Patrocinio | + Añadir oferta | Botón | Funciona | Abre la ventana «Nuevo oferta destacada» |
| Centro de control de WORLDIVES · Patrocinio | Contacto para marcas | Formulario | Funciona | Enviado vacío · Aviso: «Contacto guardado.» · POST /api/admin/site-promos/settings → 200 |

#### Centro de control de WORLDIVES · Verificaciones · `#/admin?tab=claims`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Verificaciones | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Verificaciones | https://arrecifeazul.example.com | Enlace externo | Funciona | Enlace externo a arrecifeazul.example.com (no se abre: dirección https válida) |
| Centro de control de WORLDIVES · Verificaciones | Cómo lo has verificado | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Aprobar» (sin efecto inmediato, correcto) |
| Centro de control de WORLDIVES · Verificaciones | Aprobar | Botón | Funciona | Aviso: «Indica cómo has verificado la cuenta: email del dominio del centro, llamada al teléfono público o documento.» · POST /api/admin/center-claims/review → 400 «Indica cómo has verificado la cuenta: email del dominio del centro, llamada al teléfono público o documento.» |
| Centro de control de WORLDIVES · Verificaciones | Rechazar | Botón | Funciona | Aviso: «Verificación guardada.» · Muestra contenido nuevo (3 elementos): «CUENTA ADMINISTRADOR Centro de control de WORLDIVES Control administrativo de WORLDIVES DISCOVERY. Añade la clave de Arc» · POST /api/admin/center-claims/review → 200 |

#### Centro de control de WORLDIVES · Correcciones · `#/admin?tab=suggestions`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Correcciones | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |

#### Centro de control de WORLDIVES · QR · `#/admin?tab=qr`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · QR | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · QR | Crear QR | Formulario | Funciona | Enviado vacío · Aviso: «QR creado.» · Muestra contenido nuevo (1 elementos): «http://127.0.0.1:45553/#/checkin/UWLVDZSN2UVT Copiar enlace» · POST /api/qr/create → 200 |
| Centro de control de WORLDIVES · QR | Centro | Desplegable | Funciona | Campo: el cambio se aplica al pulsar «Crear QR» (sin efecto inmediato, correcto) |

#### Centro de control de WORLDIVES · Recompensas · `#/admin?tab=rewards`

| Pantalla | Elemento | Tipo | Resultado | Detalle |
|---|---|---|---|---|
| Centro de control de WORLDIVES · Recompensas | Ver Mapas | Enlace | Funciona | Mismo enlace (#/admin?tab=maps) que «Ver Mapas» en «Centro de control de WORLDIVES · Inicio»: Abre #/admin?tab=maps |
| Centro de control de WORLDIVES · Recompensas | + Nueva ventaja | Botón | Funciona | Abre la ventana «Nueva ventaja» |
| Centro de control de WORLDIVES · Recompensas | Editar | Botón | Funciona | Abre la ventana «Editar ventaja» · hay 2 más iguales en la lista (no se prueban todos) |
| Centro de control de WORLDIVES · Recompensas | Editar | Botón | Funciona | Abre la ventana «Editar ventaja» |

