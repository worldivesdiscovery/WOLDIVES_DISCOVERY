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

## Pagos con Stripe Connect (v50.34)

**WORLDIVES no cobra comisión por las reservas.** Su único ingreso es la cuota del plan anual de los centros. Los cobros online son **cargos directos**: el Checkout se crea en la cuenta de Stripe del centro (o del profesional freelance sin centro) con `stripe_account=…`, sin `application_fee_amount` ni `transfer_data`. El dinero va del buceador al prestador y nunca pasa por un saldo de WORLDIVES.

### Variables de servidor

Solo en el entorno del servidor (nunca en JavaScript, en el repositorio ni dentro del ZIP). Ver `.env.example`.

```text
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...           # endpoint de la plataforma
STRIPE_CONNECT_WEBHOOK_SECRET=whsec_...   # endpoint de Connect (eventos de las cuentas de los centros)
WOD_PUBLIC_URL=https://tu-dominio.example
# Configuración de las cuentas conectadas (valores por defecto = decisión del titular):
WOD_STRIPE_DASHBOARD=full        # panel completo de Stripe para el centro
WOD_STRIPE_FEES_PAYER=account    # las comisiones de Stripe las paga la cuenta del centro
WOD_STRIPE_LOSSES=stripe         # Stripe responde de los saldos negativos
WOD_STRIPE_CAPABILITIES=card_payments
```

### Alta de un centro o de un freelance

Desde **Cobros y pagos** en su panel. WORLDIVES crea una cuenta conectada con **propiedades de controlador** (Accounts v1: `controller.stripe_dashboard.type=full`, `controller.fees.payer=account`, `controller.losses.payments=stripe`, `requirement_collection=stripe`) y solo la capacidad `card_payments`, y abre el alta alojada por Stripe (Account Link). Se guardan solo el identificador de la cuenta y sus estados. No se puede cobrar online hasta que Stripe indique `charges_enabled` y `payouts_enabled`; `account.updated` los mantiene al día. Con el panel completo, el centro entra en `dashboard.stripe.com` con su propio usuario.

Las cuentas Express de prueba creadas con versiones anteriores no pueden cambiar de tipo: el administrador las desvincula (`POST /api/payments/connect/unlink`) y el centro conecta una nueva.

### Pago de una reserva

- «Pago al reservar»: Checkout al momento (total o **señal**), plazas bloqueadas 15 min, confirmación solo con el pago confirmado por Stripe.
- «Bajo petición»: Checkout cuando el centro acepta, con plazo para pagar.
- Señal: por servicio, porcentaje o importe por persona. La reserva guarda lo pagado (`amount_paid`) y lo pendiente (`amount_due`); el resto se registra con «Registrar cobro».

La reserva solo se considera pagada cuando Stripe lo confirma (webhook firmado, o consulta directa a Stripe al volver del pago). Los eventos se registran por ID para no procesarlos dos veces.

### Devoluciones

Las hace el centro desde su panel (botón «Devolver», total o parcial) con `Refund.create` en su cuenta, o desde su panel de Stripe; ambas llegan al historial `payment_refunds`. Un reembolso parcial no cancela la reserva. Si el buceador cancela una reserva pagada, se propone al centro el importe de su política y se le recuerda a las 72 h. El administrador solo ve pagos y devoluciones y marca incidencias.

### Webhooks

```text
POST https://tu-dominio.example/api/payments/webhook          (cuenta de la plataforma)
POST https://tu-dominio.example/api/payments/webhook/connect  (Connect: «eventos de las cuentas conectadas»)
```

Eventos: `checkout.session.completed`, `checkout.session.async_payment_succeeded`, `checkout.session.async_payment_failed`, `checkout.session.expired`, `payment_intent.payment_failed`, `charge.refunded`, `refund.created`, `refund.updated`, `charge.dispute.created`, `charge.dispute.closed`, `account.updated`, `account.application.deauthorized`. En el endpoint de Connect, un evento de una cuenta nunca puede tocar un pago de otra.

### Importante antes de producción

Antes de aceptar dinero real: HTTPS, secretos fuera del repositorio, copias de seguridad, términos y política de cancelación revisados por un abogado y configuración fiscal revisada por la gestoría (ver `docs/`).


## Seguridad y GitHub

La versión de distribución incluye `.gitignore` para evitar que secretos, configuraciones locales, almacenamiento privado y archivos WAL/SHM de SQLite terminen en GitHub. Usa `.env.example` como plantilla y define los secretos únicamente en el entorno donde se ejecuta el servidor.

Para uso local: `start_unix.sh` (Linux/macOS) o `start_windows.bat` (Windows). Para acceso desde otros dispositivos de la misma LAN, usa `start_windows_lan.bat` conscientemente.

Consulta `SECURITY.md` antes de publicar la aplicación.
