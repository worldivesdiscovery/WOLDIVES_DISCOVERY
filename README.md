# WORLDIVES · Local 8

Aplicación local para WORLDIVES basada en **Python estándar + SQLite + HTML/CSS/JavaScript**. La portada se ha replanteado como una plataforma de descubrimiento y reservas, no como una colección de páginas aisladas.

## Arranque en Windows

1. Descomprime la carpeta.
2. Ejecuta `start_windows.bat`.
3. Abre `http://localhost:8000`.
4. Para probarla desde un móvil o tablet en la misma Wi-Fi, usa la IP del ordenador que se muestra en la ventana del servidor, por ejemplo `http://192.168.1.30:8000`.

No abras `index.html` con doble clic.

## Primera instalación

La primera vez que no existe ningún usuario, entra en `#/setup` desde la propia interfaz y crea la cuenta administradora. Después podrás crear centros, crear cuentas de usuario normales y asignar roles.

Roles disponibles:

- **Administrador**: catálogo, centros, usuarios, roles, correcciones de posiciones, QR y reservas.
- **Centro**: gestiona sus puntos, sus reservas y clientes asociados; puede crear QR del centro.
- **Recreativo / buceador**: consulta el mapa y catálogo, reserva inmersiones, mantiene su documentación y Log Book, usa recompensas/monedero y puede proponer correcciones de posición.
- **Profesional / freelance**: gestiona su perfil profesional y experiencias publicadas y conserva las funciones de usuario necesarias para explorar, reservar, mantener su Log Book y utilizar su cuenta.

## Reserva y QR

El usuario recreativo mantiene en su cuenta:

- datos de contacto;
- titulaciones;
- seguros;
- certificados/documentación adicional y caducidades;
- preferencias de equipo;
- necesidad de guía;
- nitrox/recogida;
- reservas;
- Log Book.

El centro puede ver la ficha completa que acompaña a una reserva, incluidas las fechas de documentación y las preferencias que el cliente haya indicado.

Cada centro puede generar un QR de recepción. El cliente lo escanea y, si ha iniciado sesión, se crea el vínculo en `center_links`. Esto prepara el flujo de check-in que podrá convertirse posteriormente en la integración comercial definitiva.

## Catálogo y mapa

El mapa usa Leaflet en el navegador y mantiene la fuente de datos en SQLite:

- Mapa OpenStreetMap.
- Satélite de Esri.
- Capa de relieve GEBCO.
- Puntos con latitud/longitud reales.
- Edición de posición por arrastre o clic desde administración.
- Correcciones de usuarios enviadas a revisión.

Las teselas cartográficas se descargan de Internet. El servidor y la base de datos son locales.

## Archivos y seguridad

Los documentos personales **no** se guardan dentro de `public/`. Se almacenan en `storage/documents` y se sirven mediante un endpoint autenticado. Las fotografías de puntos pueden ser públicas porque forman parte del catálogo.

Las sesiones actuales son de memoria porque esta fase es un prototipo local. Antes de publicar habrá que migrar la sesión a un almacenamiento persistente y habilitar HTTPS, protección CSRF, rate limiting, gestión de consentimientos, copias de seguridad, cifrado/retención documental y un proveedor de almacenamiento adecuado para documentación sensible.

## Base de datos

El archivo principal es:

`data/worldivesdiscovery.sqlite3`

La aplicación crea automáticamente tablas auxiliares para:

- `user_profiles`
- `user_documents`
- `center_links`
- `qr_codes`
- `bookings`
- `audit_log`
- `travel_offers`

además de conservar el catálogo que ya tenía la versión anterior.

## Siguiente evolución

La arquitectura está preparada para crecer hacia:

1. Back-office completo con edición visual de puntos y centros.
2. Reservas con disponibilidad/horarios reales de cada centro.
3. Gestión de miembros del centro y permisos más finos.
4. Notificaciones reales de caducidad.
5. Aplicación móvil reutilizando la misma API.
6. Migración a hosting/HTTPS sin rehacer la interfaz ni el modelo de datos.


## Arranque local
Ejecuta `start_windows.bat`. El lanzador detecta primero `py -3` para evitar el alias de Microsoft Store.

## Recorridos virtuales

Las fichas de puntos de buceo ya no presentan una galería fotográfica como experiencia principal. Cada punto puede tener uno o varios `virtual_experiences` en SQLite, con tipos `panorama`, `video360`, `streetview` o `external360`.

- `panorama`: preparado para una imagen/equirectangular 360 local cuando se incorpore el visor inmersivo.
- `video360`: admite una URL de vídeo 360 y se muestra dentro del visor.
- `streetview`: abre la visita del proveedor en una nueva ventana.
- `external360`: reservado para otros visores/servicios 360.

La ruta `#/virtual?experience=ID&point=ID` queda separada de la ficha para poder evolucionar el visor sin modificar el catálogo.


## V12.5 — Centros verificados y logos
- Registro de centros con teléfono y datos empresariales.
- Coincidencia de teléfono con centros existentes -> solicitud de verificación para aprobación del administrador.
- Solicitud de nueva ficha de centro cuando no existe coincidencia.
- Centros verificados pueden editar su ficha y gestionar sus puntos; las coordenadas pasan por Correcciones.
- Nuevos puntos creados por centros quedan pendientes de aprobación administrativa.
- Las tarjetas de centros usan la marca/fav icon del sitio oficial en esta demo; el centro o administrador puede sustituirlo por la URL del logotipo oficial.

## v21 · pagos profesionales con Stripe Connect

Esta versión añade **solo la capa de pagos**, manteniendo la estructura existente de reservas, servicios, salidas, centros y perfiles. El modelo utilizado es un marketplace con **Stripe Connect + Checkout**: el cliente paga en una página segura de Stripe y, una vez confirmado el pago, Stripe transfiere el importe al centro conectado; WORLDIVES puede retener una comisión mediante `application_fee_amount`. Stripe documenta este patrón como **destination charges**.

### Variables de servidor

Configura estas variables de entorno en el servidor (no las pongas en JavaScript ni dentro del ZIP):

```text
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
WOD_PUBLIC_URL=https://tu-dominio.example
WOD_PLATFORM_FEE_PERCENT=10
```

Para producción, cambia la clave a `sk_live_...` y utiliza un webhook HTTPS de producción. `WOD_PLATFORM_FEE_PERCENT` controla la comisión de WORLDIVES; por defecto es 10%.

### Alta de un centro

El centro entra en **Gestionar mi centro → Cobros y pagos → Configurar cobros seguros**. WORLDIVES crea una cuenta Connect Express y redirige al centro al onboarding alojado por Stripe. WORLDIVES guarda únicamente el identificador de la cuenta conectada y sus estados de capacidad; los datos bancarios y de verificación permanecen en Stripe. Las Account Links son temporales y de un solo uso.

El centro no puede cobrar online hasta que Stripe indique `charges_enabled` y `payouts_enabled`. El webhook `account.updated` mantiene estos estados sincronizados.

### Pago de una reserva

Cuando un servicio está configurado como **Pago obligatorio** o **Reserva inmediata** con precio, el cliente crea la reserva y WORLDIVES genera una sesión de Stripe Checkout específica para esa reserva. El checkout utiliza: **importe total → comisión WORLDIVES → transferencia al centro conectado**.

La reserva solo se considera pagada cuando el servidor recibe y verifica el webhook firmado de Stripe. La URL de retorno del navegador no es la fuente de verdad del pago. Los eventos de webhook se registran con ID único para evitar procesarlos dos veces.

También se manejan expiraciones del Checkout y reembolsos, manteniendo el estado de la reserva y de la operación de pago vinculados.

### Webhook

Configura en Stripe un endpoint HTTPS apuntando a:

```text
POST https://tu-dominio.example/api/payments/webhook
```

Como mínimo, suscribe el endpoint a:

- `checkout.session.completed`
- `checkout.session.async_payment_succeeded`
- `checkout.session.expired`
- `payment_intent.payment_failed`
- `charge.refunded`
- `refund.updated`
- `account.updated`

### Importante antes de producción

La integración de pagos está separada de la aplicación y no almacena tarjetas. Antes de aceptar dinero real, el despliegue completo debe usar HTTPS, secretos fuera del repositorio, copias de seguridad, control de acceso, protección CSRF/rate limiting, política de cancelaciones y reembolsos, términos, privacidad/cookies y la configuración fiscal/legal correspondiente al modelo de marketplace. Stripe Connect proporciona el onboarding y la infraestructura de pagos; la responsabilidad comercial y legal de WORLDIVES debe definirse antes del lanzamiento.


## Seguridad y GitHub

La versión de distribución incluye `.gitignore` para evitar que secretos, configuraciones locales, almacenamiento privado y archivos WAL/SHM de SQLite terminen en GitHub. Usa `.env.example` como plantilla y define los secretos únicamente en el entorno donde se ejecuta el servidor.

Para uso local: `start_unix.sh` (Linux/macOS) o `start_windows.bat` (Windows). Para acceso desde otros dispositivos de la misma LAN, usa `start_windows_lan.bat` conscientemente.

Consulta `SECURITY.md` antes de publicar la aplicación.
