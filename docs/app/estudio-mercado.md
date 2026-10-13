# Estudio de mercado: apps de reservas de buceo y gestión de centros

Encargo «App móvil en 3 módulos», apartado 1 · Tanda 0.

Fecha de consulta: 13/10/2026.

## Qué hemos comprobado y cómo

- Revisamos la tabla resumen del encargo, producto por producto.
- Solo usamos información pública: webs oficiales, fichas de App Store y Google Play, centros de ayuda, blogs oficiales y prensa.
- Herramienta usada: el buscador web. La herramienta para abrir páginas falló en todos los dominios que probamos (diveplannerpro.com, padi.com, blog.padi.com, apps.apple.com, docs.stripe.com). Daba error de DNS. El acceso directo con curl está bloqueado en este entorno.
- Por eso **ninguna página se abrió entera**. Todos los datos salen del texto que devuelve el buscador para cada URL oficial.
- **No hay capturas de las fichas de las tiendas.** Desde este entorno de trabajo la red bloquea play.google.com, apps.apple.com y las webs de la competencia (el proxy responde 403). Al final hay una lista de fichas para capturarlas desde un móvil o un ordenador normal.

**Cómo leer la columna «Estado»:**

- **verificado (búsqueda)**: el dato aparece en el resultado de búsqueda de la URL indicada. No abrimos la página. Antes de publicar, conviene abrir la URL y confirmarlo.
- **sin verificar**: no encontramos el dato, o las fuentes no coinciden, o solo lo dice un tercero.
- Cuando algo «no existe», casi nunca se puede demostrar. Lo marcamos como «sin verificar (no encontrado)».
- Casi todo lo que dicen los fabricantes es publicidad propia. Lo indicamos cuando importa.

Todas las fuentes se consultaron el 13/10/2026.

---

## 1. DivePlanner Pro

Web: https://diveplannerpro.com/

| Dato | Valor | Fuente | Estado |
|---|---|---|---|
| Qué es | Software web para gestionar centros de buceo: salidas, reservas online, pagos, material, personal y certificaciones. Lo publica Carbon Intelligence SAS (París). | https://diveplannerpro.com/ y https://www.diveplannerpro.com/terms (consultado el 13/10/2026) | verificado (búsqueda) |
| Plataformas | Web adaptada al móvil. Su propia tabla comparativa dice «Yes (PWA)», es decir, web que se puede instalar en el móvil. | https://diveplannerpro.com/blog/best-dive-center-software-comparison (consultado el 13/10/2026) | verificado (búsqueda) |
| App en tiendas | No encontramos ficha en App Store ni en Google Play. Ojo: en Google Play hay apps llamadas «Dive Planner Pro» que no tienen nada que ver (calculadoras de inmersión de otros autores). | https://play.google.com/store/apps/details?id=com.davidnac.diveplannerpro (otra app, no confundir) (consultado el 13/10/2026) | sin verificar (no encontrado) |
| Uso en el barco | Dice que la interfaz está pensada para móvil y tableta, para usarla desde el muelle o el barco. | https://diveplannerpro.com/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Condiciones del mar | Viento, marea y oleaje por punto de inmersión. Ayuda a decidir si se sale o no («Go/No-Go»). Está incluido también en el plan gratis. | https://diveplannerpro.com/ y https://diveplannerpro.com/pricing (consultado el 13/10/2026) | verificado (búsqueda) |
| Certificaciones | Dice que se verifican «en un toque». Cita PADI, SSI y CMAS. | https://diveplannerpro.com/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Sin conexión | Anuncia un modo sin conexión que se sincroniza al volver la cobertura. No explica qué pantallas funcionan así. | https://diveplannerpro.com/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Check-in / QR | Tiene un «Field Mode». En el plan gratis es solo «Roll Call» (pasar lista). En Pro y Business es completo («6 fases»). No encontramos ninguna mención a escanear QR. | https://diveplannerpro.com/pricing (consultado el 13/10/2026) | Field Mode: verificado (búsqueda). QR: sin verificar (no encontrado) |
| Notificaciones push | La página de precios habla de «notificaciones en la app». No dice si son push en el móvil. | https://diveplannerpro.com/pricing (consultado el 13/10/2026) | sin verificar |
| Idiomas | Inglés, francés y español. Lo dice para la interfaz y para la página de reservas. | https://diveplannerpro.com/ y https://diveplannerpro.com/pricing (consultado el 13/10/2026) | verificado (búsqueda) |
| Precio | Plan gratis (15 salidas al mes, 1 persona). Pro: la portada dice «desde 29 €/mes»; la tabla de precios dice 24 €/mes con pago anual (288 €/año). Business: 49 €/mes con pago anual (588 €/año) en la tabla, 59 €/mes en otras partes. Prueba de 14 días con tarjeta. | https://diveplannerpro.com/pricing y https://diveplannerpro.com/ (consultado el 13/10/2026) | verificado (búsqueda). Su web se contradice en las cifras |
| Comisión en pagos | Sí cobra. Página de precios: 5 % en Pro y 3 % en Business, además de la tarifa de Stripe. Sus condiciones legales dicen 3 % para todos los pagos online. Pagos con Stripe Connect; el dinero llega a la cuenta del centro. | https://diveplannerpro.com/pricing y https://www.diveplannerpro.com/terms (consultado el 13/10/2026) | verificado (búsqueda). El porcentaje exacto se contradice |
| Directorio público | Tiene fichas públicas de centros (dice 5.793 centros PADI y SSI en 157 países) y de puntos de inmersión. Es un listado, no sus clientes. | https://diveplannerpro.com/dive-centers y https://diveplannerpro.com/spots/fr (consultado el 13/10/2026) | verificado (búsqueda) |
| Clientes | Dice tener más de 50 centros en más de 12 países. Dato del propio fabricante. | https://diveplannerpro.com/ (consultado el 13/10/2026) | verificado (búsqueda) |

---

## 2. PADI App y PADI Adventures

| Dato | Valor | Fuente | Estado |
|---|---|---|---|
| Qué es | **PADI Adventures**: app para reservar inmersiones, cursos y snorkel con centros PADI. **PADI App**: formación online, tarjetas digitales (eCards), diario de inmersiones y buscador de centros. | https://www.padi.com/scuba-diving-mobile-apps (consultado el 13/10/2026) | verificado (búsqueda) |
| Cambio importante | En julio de 2025 PADI lanzó una **PADI App unificada**. Junta PADI Training, PADI App y PADI Adventures. Adventures seguiría «durante un periodo de transición». PADI dijo que la retiraría después de la app Training (retirada prevista en noviembre de 2025). | https://pros-blog.padi.com/new-padi-app/ y https://pros-blog.padi.com/sunsetting-the-training-app/ (consultado el 13/10/2026) | verificado (búsqueda). Si Adventures sigue activa hoy: sin verificar |
| Plataformas | Las dos apps están en iOS y Android. | Ver fichas de tienda abajo (consultado el 13/10/2026) | verificado (búsqueda) |
| Reserva rápida | El blog de PADI dice que se reserva «con unos pocos clics». Es un texto de 2020. | https://blog.padi.com/awesome-features-padi-adventures/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Datos guardados | Guarda datos personales, de pago y preferencias de alquiler para pagar con un clic. Al reservar se envían la certificación y el material de alquiler. | https://apps.apple.com/us/app/padi-adventures-book-diving/id1497105546 y https://www.padi.com/scuba-diving-mobile-apps (consultado el 13/10/2026) | verificado (búsqueda) |
| Reserva para el compañero | Puedes guardar los datos de tu compañero: número de certificación, número de inmersiones, fecha de la última inmersión y preferencias de alquiler. Lo añades al pagar. | https://blog.padi.com/awesome-features-padi-adventures/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Tallas | No encontramos campos de tallas (traje, aletas, etc.). | — | sin verificar (no encontrado) |
| Buscador | Adventures muestra actividades cercanas por ubicación. La PADI App busca centros y puntos de inmersión (el blog que lo cuenta es antiguo). | https://apps.apple.com/us/app/padi/id1490797188 y https://blog.padi.com/dive-travel-in-the-palm-of-your-hand-the-revamped-padi-app/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Atado a PADI | Solo reserva con centros y resorts PADI. | https://www.divenewswire.com/?p=20023 y https://www.padi.com/scuba-diving-mobile-apps (consultado el 13/10/2026) | verificado (búsqueda) |
| Coste para el centro | Cobra al centro una tarifa por reserva (comisión + gastos de cobro). Los porcentajes no son públicos; están en el Extranet de PADI. Si el buceador está vinculado al centro, no hay comisión, pero sí un cargo de servicio del 4,9 %. | https://affiliates.padi.com/adventures/terms-06-2023/ y https://pros-blog.padi.com/top-faqs-about-padi-adventures/ (consultado el 13/10/2026) | verificado (búsqueda). Textos de 2023; pueden haber cambiado |
| ¿Gestión para centros? | Los centros usan un Extranet y un widget de reservas de PADI. No encontramos gestión de barcos, personal o material. | https://pros-blog.padi.com/introducing-the-new-padi-booking-widget/ (consultado el 13/10/2026) | sin verificar (no encontrado) |
| Sin conexión | La PADI App permite registrar inmersiones con y sin conexión. | https://apps.apple.com/us/app/padi/id1490797188 (consultado el 13/10/2026) | verificado (búsqueda) |
| QR | La PADI App usa el QR del instructor para validar inmersiones de formación. | https://apps.apple.com/us/app/padi/id1490797188 (consultado el 13/10/2026) | verificado (búsqueda) |
| Avisos | Adventures avisa de las próximas salidas del centro favorito. No dice si es por push. | https://apps.apple.com/us/app/padi-adventures-book-diving/id1497105546 (consultado el 13/10/2026) | sin verificar (push) |
| Precio para el buceador | Gratis. | https://apps.apple.com/us/app/padi-adventures-book-diving/id1497105546 (consultado el 13/10/2026) | verificado (búsqueda) |
| Idiomas | Un blog antiguo de PADI cita inglés, francés, alemán y español, entre otros. No sabemos la lista actual. | https://blog.padi.com/dive-travel-in-the-palm-of-your-hand-the-revamped-padi-app/ (consultado el 13/10/2026) | sin verificar |

---

## 3. FareHarbor (motor de reservas genérico)

| Dato | Valor | Fuente | Estado |
|---|---|---|---|
| Qué es | Software de reservas para tours y actividades de todo tipo. La app es para operadores que ya usan FareHarbor. | https://apps.apple.com/us/app/fareharbor/id1053611279 (consultado el 13/10/2026) | verificado (búsqueda) |
| Plataformas | App para iPhone y Android (Android 8.0 o superior). Hay otra app para iPad, «FareHarbor Dock», para cobrar con lectores. | https://help.fareharbor.com/hc/en-us/articles/40897761048603-Using-the-FareHarbor-app-on-Android-devices y https://apps.apple.com/us/app/fareharbor-dock/id1666347047 (consultado el 13/10/2026) | verificado (búsqueda) |
| Agenda y reservas | Ver la agenda, añadir reservas, llamar o escribir al cliente. | https://apps.apple.com/us/app/fareharbor/id1053611279 (consultado el 13/10/2026) | verificado (búsqueda) |
| Check-in con QR | Sí. Se activa en ajustes. | https://apps.apple.com/us/app/fareharbor/id1053611279 y https://fareharbor.com/manage/mobile-app/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Sin conexión | Escaneo de QR sin conexión en iPhone; se sincroniza al volver. En Android lo anunciaron «más adelante». | https://marketing.fareharbor.com/blog/fareharbor-app-run-your-business-from-the-palm-of-your-hand/ (consultado el 13/10/2026) | iPhone: verificado (búsqueda). Android: sin verificar |
| Push | Sí. Se elige qué avisos llegan y a quién: nuevas reservas, cancelaciones, cambios, tripulación. | https://help.fareharbor.com/hc/en-us/articles/42957683138459-FareHarbor-Glossary y https://fareharbor.com/manage/mobile-app/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Cobro con el móvil | Tap to Pay en iPhone (al lanzarlo, solo para clientes en EE. UU.; iPhone XS o superior). Su centro de ayuda tiene guías de Tap to Pay en iPhone y en Android. Usa Stripe Terminal. También lectores Bluetooth. | https://fareharbor.com/blog/announcing-tap-to-pay-on-iphone-in-person-payments-made-easier/, https://help.fareharbor.com/hc/en-us/categories/39091374714395-Getting-Started y https://stripe.com/customers/fareharbor (consultado el 13/10/2026) | verificado (búsqueda). Países donde lo ofrece hoy: sin verificar |
| Barcos | **Sí gestiona barcos.** Tiene solución para tours en barco: capacidad por embarcación, lista de pasajeros en el móvil con recuento en vivo, asignar capitán y tripulación. Cita el buceo como uno de los usos. | https://fareharbor.com/solutions/boat-tours/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Funciones de buceo | No encontramos verificación de certificaciones, tallas ni puntos de inmersión. Sí tiene campos personalizados genéricos. | https://fareharbor.com/solutions/boat-tours/ (consultado el 13/10/2026) | sin verificar (no encontrado) |
| Modelo de cobro | Sin cuota mensual. Normalmente cobra un «booking fee» que paga el cliente al pagar. Sus condiciones también permiten un modelo de comisión al operador. El operador paga los gastos de cobro con tarjeta. FareHarbor no publica los porcentajes; webs de terceros hablan de hasta un 6 %. | https://fareharbor.com/legal/tos-providers/ y https://fareharbor.com/blog/new-ftc-rule-on-mandatory-fee-disclosure-what-tour-operators-need-to-know/ (consultado el 13/10/2026) | Modelo: verificado (búsqueda). Porcentajes: sin verificar |
| Idiomas | El proceso de reserva detecta el idioma del navegador y ofrece traducción automática. Su web de pago (FareHarbor Sites) admite hasta 3 idiomas. | https://help.fareharbor.com/website/integrations/lightframe/ y https://marketing.fareharbor.com/sell/fareharbor-sites/ (consultado el 13/10/2026) | verificado (búsqueda) |

---

## 4. Software de gestión de centros: Lueira, BukyApp y DiveOps

### 4.1 Lueira

Empresa: Maladeta Studio S.L. (España). Web: https://lueira.com/

| Dato | Valor | Fuente | Estado |
|---|---|---|---|
| Qué es | Software de gestión y reservas para turismo activo. Tiene página propia para centros de buceo. | https://lueira.com/en/sector/diving-centers/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Barcos con capacidad | Sí. Salidas por barco, capacidad de cada barco y ocupación real. | https://lueira.com/en/sector/diving-centers/ (consultado el 13/10/2026) | verificado (búsqueda) |
| App para instructores | Sí. «Lueira Team» (antes «Lueira Instructors»), en iOS y Android: agenda, datos de la reserva, pasar lista y fichar. Una ficha de App Store dice «Solo para iPhone». | https://lueira.com/en/features/mobile-app/ y fichas de tienda abajo (consultado el 13/10/2026) | verificado (búsqueda) |
| App de administración | Sí. «Lueira Admin», en iOS (también iPad) y Android: crear y editar reservas, registrar pagos y enviar enlace de pago. La ficha de Google Play habla de notificaciones en tiempo real. | https://lueira.com/funcionalidades/aplicacion-movil/ y https://play.google.com/store/apps/details?id=studio.maladeta.lueiraadmin (consultado el 13/10/2026) | verificado (búsqueda). Push: sin verificar |
| Fichaje | App aparte, «Lueira Trackr». | https://apps.apple.com/us/app/lueira-trackr/id6740490238 (consultado el 13/10/2026) | verificado (búsqueda) |
| Mover cliente a otra salida | Desde el panel se puede reprogramar. El calendario permite arrastrar y soltar. No consta que se haga desde la app. | https://lueira.com/en/features/mobile-app/ (consultado el 13/10/2026) | verificado (búsqueda) en el panel. En la app: sin verificar |
| Reembolsos desde la app | No encontrado. | — | sin verificar (no encontrado) |
| Check-in | Formularios automáticos tras la reserva; el cliente los firma desde el móvil. No encontramos escaneo de QR. | https://lueira.com/en/blog/2025/07/30/digital-dive-check-in-integrated-in-your-management-software/ (consultado el 13/10/2026) | verificado (búsqueda). QR: sin verificar |
| Idiomas | 9 idiomas en el panel y en el motor de reservas: español, catalán, inglés, francés, alemán, neerlandés, euskera, italiano y portugués. | https://lueira.com/en/sector/diving-centers/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Precio | Basic: 99 €/mes, o 80 €/mes con pago anual, más 160 € de alta. Pro: 249 €/mes, o 212 €/mes con pago anual, más 430 € de alta. Premium: a consultar. Precios sin IVA. Mínimo 6 meses, según su calculadora. | https://lueira.com/en/pricing/ y https://lueira.com/en/calculator/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Comisión | Dice que no cobra comisión sobre ventas. | https://lueira.com/en/pricing/ (consultado el 13/10/2026) | verificado (búsqueda) |
| ¿Buscador para buceadores? | Cada centro tiene su tienda online y hay un portal para socios (B2B). No encontramos un buscador público para atraer buceadores. | https://lueira.com/en/features/partner-portal/ (consultado el 13/10/2026) | sin verificar (no encontrado) |
| Sin conexión | No encontrado. | — | sin verificar (no encontrado) |

### 4.2 BukyApp (Buky)

Web: https://www.bukyapp.com/

| Dato | Valor | Fuente | Estado |
|---|---|---|---|
| Qué es | Software de reservas y gestión para escuelas de surf, kite y centros de buceo (España). | https://www.bukyapp.com/en/dive-center-booking-software (consultado el 13/10/2026) | verificado (búsqueda) |
| Plataformas | Web en la nube que se adapta a PC, tableta y móvil. **No encontramos app en App Store ni Google Play.** La app «Buky» de las tiendas es de otra empresa (un robot de limpieza). | https://www.bukyapp.com/en/faq y https://play.google.com/store/apps/details?id=com.buky (otra app, no confundir) (consultado el 13/10/2026) | Web: verificado (búsqueda). Sin app nativa: sin verificar (no encontrado) |
| Barcos con capacidad | Sí. Plazas, barcos y material desde un sitio. Una plaza vendida se bloquea en todos los canales. | https://www.bukyapp.com/en/dive-center-booking-software (consultado el 13/10/2026) | verificado (búsqueda) |
| Instructores | Asignación manual o automática a cada inmersión. No encontramos app propia para instructores. | https://www.bukyapp.com/en/dive-center-booking-software (consultado el 13/10/2026) | Asignación: verificado (búsqueda). App de instructores: sin verificar |
| Mover cliente a otra salida | Sí. Anuncia el traslado fácil de clientes a otra inmersión. | https://www.bukyapp.com/en/dive-center-booking-software (consultado el 13/10/2026) | verificado (búsqueda) |
| Reembolsos | Sí, desde el sistema (la web). Total o parcial. Automático con Stripe, Redsys o Bizum; manual para efectivo o transferencia. | https://www.bukyapp.com/en/faq y https://support.bukyapp.com/c/pagos/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Check-in | Registro digital que el cliente firma en el móvil. | https://www.bukyapp.com/en/dive-center-booking-software (consultado el 13/10/2026) | verificado (búsqueda). QR: sin verificar |
| Mensajes al cliente | Confirmaciones y recordatorios por email o WhatsApp. | https://www.bukyapp.com/en/dive-center-booking-software (consultado el 13/10/2026) | verificado (búsqueda). Push: sin verificar |
| Pagos | Stripe, PayPal, Bizum y Redsys. | https://www.bukyapp.com/en/dive-center-booking-software (consultado el 13/10/2026) | verificado (búsqueda) |
| Idiomas | Motor de reservas de buceo: español, inglés, alemán, francés e italiano. Panel y check-in: los mismos más portugués (6). Más tarde añadieron catalán. | https://www.bukyapp.com/en/faq (consultado el 13/10/2026) | verificado (búsqueda). Las cifras varían según la página |
| Precio | Un resultado de búsqueda citó «Plan One» a 83 €/mes y «pago por uso» desde 19 €/mes con comisión del 0,9 % (manual) o 2,9 % (online). No lo pudimos confirmar después. | https://www.bukyapp.com/software-de-reservas-para-centros-de-buceo (consultado el 13/10/2026) | sin verificar |
| Otros | Conexión con GetYourGuide. Preparado para Verifactu. | https://www.bukyapp.com/en/dive-center-booking-software (consultado el 13/10/2026) | verificado (búsqueda) |
| Sin conexión | No encontrado. | — | sin verificar (no encontrado) |

### 4.3 DiveOps (ojo: hay dos empresas con ese nombre)

DiveOps.ai dice en su web que diveops.net es otra empresa, sin relación. No sabemos a cuál se refería el encargo.

| Dato | Valor | Fuente | Estado |
|---|---|---|---|
| Dos productos | DiveOps.ai y diveops.net son empresas distintas. | https://diveops.ai/diveops-vs-diveops-net (consultado el 13/10/2026) | verificado (búsqueda) |
| DiveOps.ai: qué es | Gestión de centros con recepción por WhatsApp con IA, en el idioma del buceador. Reservas y pagos, hojas de salida y grupos, GPS de barcos en vivo, mantenimiento de material, personal y nóminas, TPV. | https://diveops.ai/ y https://diveops.ai/features (consultado el 13/10/2026) | verificado (búsqueda) |
| DiveOps.ai: plataformas | Sus datos internos de la web dicen web, iOS y Android. No encontramos fichas en las tiendas. | https://diveops.ai/ (consultado el 13/10/2026) | sin verificar |
| DiveOps.ai: precio | Desde 99 £/mes, todo incluido, sin niveles. El precio exacto depende de los buceadores al año. | https://diveops.ai/features (consultado el 13/10/2026) | verificado (búsqueda) |
| diveops.net: qué es | Espacios por rol: centro, personal, dueño de barco y cliente. Reservas, salidas, personal, barcos y material. Personal interno y **freelance**, con «ofertas de marketplace». Asignación arrastrando y soltando. Pagos con Stripe. | https://diveops.net/ (consultado el 13/10/2026) | verificado (búsqueda) |
| diveops.net: precio | Planes según personal y barcos: gratis (2 personas, 1 barco) hasta «Elite» a 199,99 €/mes. Planes para personal: 0,99, 9,99 o 14,99 €/mes. | https://diveops.net/ (consultado el 13/10/2026) | verificado (búsqueda) |
| Capacidad de barcos | Ninguna de las dos lo explica. | — | sin verificar |
| App para instructores | No encontrada en ninguna de las dos. | — | sin verificar (no encontrado) |
| Mover cliente a otra salida | No encontrado. | — | sin verificar (no encontrado) |
| Reembolsos desde la app | No encontrado. | — | sin verificar (no encontrado) |

---

## 5. Stripe Tap to Pay (cobrar con el móvil, sin datáfono)

| Dato | Valor | Fuente | Estado |
|---|---|---|---|
| ¿Existe? | Sí, en iPhone y en Android, con Stripe Terminal. | https://docs.stripe.com/terminal/payments/setup-reader/tap-to-pay (consultado el 13/10/2026) | verificado (búsqueda) |
| España | España aparece en la tabla de Stripe para iPhone y para Android. | https://docs.stripe.com/terminal/payments/regional (consultado el 13/10/2026) | verificado (búsqueda). Conviene confirmar en la página: el buscador avisó de que las tablas no coinciden del todo |
| Otros países | EE. UU., Reino Unido, Canadá, Australia, Singapur y gran parte de Europa occidental. Otros países están «en prueba». | https://docs.stripe.com/terminal/payments/setup-reader/tap-to-pay (consultado el 13/10/2026) | Lista exacta: sin verificar |
| Requisitos iPhone | iPhone XS o posterior con iOS reciente. La app necesita un permiso especial de Apple. | https://docs.stripe.com/terminal/payments/setup-reader/tap-to-pay (consultado el 13/10/2026) | verificado (búsqueda) |
| Requisitos Android | Móvil con NFC, certificado por Google, sin «root» y con parches de seguridad recientes. La versión mínima de Android no la pudimos confirmar. | https://docs.stripe.com/terminal/payments/connect-reader?terminal-sdk-platform=android&reader-type=tap-to-pay (consultado el 13/10/2026) | verificado (búsqueda). Versión mínima: sin verificar |
| Historia | Al lanzar Android, Stripe lo ofrecía solo en EE. UU., Canadá, Reino Unido, Nueva Zelanda, Australia y Singapur. Es una nota antigua. | https://stripe.com/newsroom/news/tap-to-pay-android (consultado el 13/10/2026) | verificado (búsqueda) |

---

## 6. Tabla resumen corregida

| Producto | Qué hace bien en móvil | Qué le falta o dónde ganamos |
|---|---|---|
| **DivePlanner Pro** | Web instalable (PWA) pensada para usar en el barco. Condiciones del mar (viento, marea, oleaje) y decisión de salir o no. Certificaciones «en un toque». Modo sin conexión. Pasar lista («Field Mode»). Plan gratis. | No encontramos app en las tiendas. No encontramos QR; push sin confirmar. Solo 3 idiomas (inglés, francés, español). Cobra comisión: 5 % (Pro) o 3 % (Business), más Stripe. Pro: 29 €/mes, o 24 €/mes con pago anual. Ojo: también tiene un directorio público de centros y puntos de inmersión. |
| **PADI App (incluye la antigua PADI Adventures)** | Busca centros, actividades y puntos de inmersión. Reserva rápida. Guarda certificación, número de inmersiones, última inmersión y preferencias de alquiler, y los envía al centro. Reserva para tu compañero. Diario con y sin conexión. | Solo centros PADI. Cobra al centro por reserva (comisión + gastos de cobro; 4,9 % si el buceador está vinculado). No encontramos gestión de barcos, personal ni material. PADI está pasando Adventures a una sola PADI App. |
| **FareHarbor** | App de operador en iPhone y Android: agenda, añadir reservas, llamar o escribir al cliente, check-in con QR (sin conexión en iPhone), push configurable, cobro con el móvil (Tap to Pay) y lectores. Gestiona barcos: capacidad, lista de pasajeros y tripulación. | No es de buceo: no encontramos certificaciones, tallas ni puntos de inmersión. Normalmente cobra un cargo por reserva al cliente (o comisión al operador, según contrato). Solo para operadores, no es buscador de buceo. |
| **Lueira** | Barcos con capacidad. App de instructores (agenda, asistencia, fichaje) y app de administración (reservas, pagos, enlace de pago), en iOS y Android. Reprogramar en el calendario. Check-in con formularios en el móvil. 9 idiomas. Sin comisión. | No encontramos reembolsos desde la app ni modo sin conexión. Es gestión, no buscador para atraer buceadores. Cuota desde 80 €/mes + alta. |
| **BukyApp** | Barcos con capacidad. Asignar instructores. Mover clientes a otra inmersión. Reembolsos desde el sistema (Stripe, Redsys, Bizum). Check-in digital. WhatsApp. | Es una web adaptada al móvil: no encontramos app nativa ni push. 5–6 idiomas. Es gestión, no buscador. Precio sin confirmar. |
| **DiveOps** (dos empresas) | DiveOps.ai: recepción por WhatsApp con IA, hojas de salida, GPS de barcos. diveops.net: barcos, personal interno y freelance. | No encontramos app de instructores, mover clientes ni reembolsos desde la app. diveops.net ya ofrece algo para freelance. |

### Correcciones al resumen del encargo

1. **DivePlanner Pro, precio.** «29 €/mes» es el precio mensual que sale en su portada. La tabla de precios dice 24 €/mes con pago anual (288 €/año). Hay plan gratis. Ponemos las dos cifras.
2. **DivePlanner Pro, comisión.** Correcto que cobra comisión. Añadimos el porcentaje: 5 % en Pro y 3 % en Business, según la página de precios. Sus condiciones dicen 3 %. Su web se contradice.
3. **DivePlanner Pro, «no tiene app que descargar».** Lo matizamos: es una web instalable (PWA). No encontramos ficha en las tiendas. Hay otras apps llamadas «Dive Planner Pro» que no son la misma.
4. **DivePlanner Pro, «sin QR nativo ni push».** Pasa a «sin verificar». No encontramos QR. Anuncia «notificaciones en la app» y no sabemos si son push.
5. **DivePlanner Pro, «solo 3 idiomas».** Verificado: inglés, francés y español.
6. **DivePlanner Pro, nuevo dato.** Tiene un directorio público de centros y de puntos de inmersión. No es solo gestión.
7. **PADI.** PADI Adventures se está integrando en una sola PADI App (desde julio de 2025). No sabemos si Adventures sigue activa hoy.
8. **PADI, coste.** Añadimos que cobra al centro por reserva. Los porcentajes no son públicos (hay un 4,9 % de cargo de servicio para buceadores vinculados).
9. **PADI, «no es gestión para centros».** Pasa a «sin verificar (no encontrado)». No encontramos funciones de gestión; los centros usan un Extranet y un widget.
10. **PADI, tallas.** No encontramos que guarde tallas. Solo «preferencias de alquiler».
11. **FareHarbor, «sin barcos».** **Incorrecto.** FareHarbor gestiona barcos: capacidad por embarcación, lista de pasajeros y tripulación. Cita el buceo como uso. Mantenemos que no encontramos certificaciones, tallas ni puntos de inmersión.
12. **FareHarbor, comisión.** Lo matizamos: normalmente es un cargo que paga el cliente. Sus condiciones también permiten comisión al operador. El operador paga los gastos de tarjeta. No publica porcentajes.
13. **FareHarbor, Tap to Pay.** Verificado en iPhone y Android. Al lanzarlo en iPhone era solo para EE. UU. No sabemos en qué países lo ofrece hoy.
14. **Lueira, BukyApp y DiveOps no son iguales.** Separamos la fila en tres.
15. **Lueira.** Verificado: barcos con capacidad y app de instructores. Mover cliente: se reprograma en el calendario del panel. Reembolsos desde la app: sin verificar.
16. **BukyApp, «app para instructores».** **No confirmado.** Buky es una web adaptada al móvil; no encontramos app en las tiendas. Sí verificado: barcos, mover clientes y reembolsos desde el sistema.
17. **DiveOps.** El nombre es ambiguo (dos empresas). Ninguna de las funciones de la fila (app de instructores, mover clientes, reembolsos) se pudo verificar. Capacidad de barcos: sin verificar.
18. **«No son buscador ni marketplace».** Pasa a «sin verificar (no encontrado)» para Lueira y Buky. diveops.net habla de «ofertas de marketplace» para personal freelance.

---

## 7. Patrón «mapa + hoja inferior» (Google Maps y Airbnb)

### Qué es el patrón

- El mapa ocupa toda la pantalla.
- Encima hay una hoja que sale desde abajo («bottom sheet»).
- La hoja tiene tres alturas:
  - **Asomada**: solo se ve una franja con el título o el número de resultados.
  - **Media**: la mitad de la pantalla. Se ven mapa y lista a la vez.
  - **Completa**: la lista ocupa casi todo.
- Se cambia de altura arrastrando la hoja.

### Lo que dicen las guías escritas

| Dato | Valor | Fuente | Estado |
|---|---|---|---|
| Hoja estándar sobre un mapa | Material Design 3 pone como ejemplo una hoja inferior con información de un lugar sobre un mapa. | https://m3.material.io/components/bottom-sheets/guidelines (consultado el 13/10/2026) | verificado (búsqueda) |
| Altura media en Android | El componente de Android tiene estados «plegado», «medio» y «expandido». El medio, por defecto, es la mitad. | https://developer.android.com/reference/com/google/android/material/bottomsheet/BottomSheetBehavior (consultado el 13/10/2026) | verificado (búsqueda) |
| Alturas en iPhone | Apple llama «detents» a las alturas donde se para la hoja. Trae «medium» (mitad) y «large» (completa). Con las dos, la hoja se puede redimensionar. | https://developer.apple.com/videos/play/wwdc2021/10063/ y https://developer.apple.com/design/human-interface-guidelines/sheets (consultado el 13/10/2026) | verificado (búsqueda) |

### Google Maps

| Dato | Valor | Fuente | Estado |
|---|---|---|---|
| Tarjeta abajo que se desliza hacia arriba | La ayuda de Google Maps describe una tarjeta de información abajo; se desliza hacia arriba para ver más y hacia abajo para ocultar. Lo dice para la navegación. | https://support.google.com/maps/answer/3273406 (consultado el 13/10/2026) | verificado (búsqueda) |
| Resultados y ficha del lugar en hoja con tres alturas | La lista de resultados y la ficha del sitio salen en una hoja que se arrastra. | — | patrón observado, sin fuente escrita |
| Botón «Buscar en esta zona» | Aparece al mover el mapa. Repite la búsqueda solo en la zona visible. Solo lo explica una guía de terceros, no la ayuda de Google. | https://www.addictivetips.com/ios/search-a-specific-area-in-google-maps (consultado el 13/10/2026) | sin verificar en fuente oficial. Patrón observado |
| Marcador y tarjeta sincronizados | Al tocar un marcador se abre su ficha abajo; al ver una ficha, el marcador se destaca. | — | patrón observado, sin fuente escrita |

### Airbnb

| Dato | Valor | Fuente | Estado |
|---|---|---|---|
| Mover el mapa para ver más | La ayuda de Airbnb dice que puedes acercar o mover el mapa para ver más alojamientos. | https://www.airbnb.com/help/article/252 (consultado el 13/10/2026) | verificado (búsqueda) |
| Mapa y lista pueden diferir | La ayuda de Airbnb avisa de que el mapa y la lista pueden mostrar alojamientos distintos. | https://www.airbnb.com/help/article/39 o /252 (el buscador no dejó claro cuál) (consultado el 13/10/2026) | sin verificar (fuente exacta) |
| Tarjetas en la lista, precios en el mapa | El blog técnico de Airbnb explica que los resultados salen como tarjetas en la lista y como «pines» ovalados con el precio en el mapa. En ordenador, muestra 18 alojamientos junto al mapa, y los menos probables como «mini-pines» sin precio. También recentra el mapa hacia los mejores resultados. | https://airbnb.tech/ai-ml/improving-search-ranking-for-maps/ y https://arxiv.org/abs/2407.00091 (consultado el 13/10/2026) | verificado (búsqueda) |
| Botón para cambiar entre mapa y lista | En el móvil, un botón flotante cambia entre lista y mapa. | https://strspecialist.com/airbnb-map-view-search (guía de terceros) (consultado el 13/10/2026) | patrón observado; sin fuente oficial |
| Hoja con lista sobre el mapa | En la app, la lista va en una hoja que se arrastra sobre el mapa. | — | patrón observado, sin fuente escrita |
| «Buscar al mover el mapa» | La búsqueda se actualiza al mover el mapa. No encontramos el texto oficial con ese nombre. | — | patrón observado, sin fuente escrita |

### Qué tomamos para WORLDIVES

- Mapa de puntos de inmersión y centros a pantalla completa.
- Hoja inferior con tres alturas: asomada (número de resultados), media (mapa + tarjetas) y completa (lista).
- Botón «Buscar en esta zona» cuando el usuario mueve el mapa.
- Botón flotante «Mapa / Lista».
- Tocar un marcador abre su tarjeta. Pasar por una tarjeta destaca su marcador.
- Marcadores con precio (como Airbnb) para las salidas.

---

## 8. Qué adoptamos (conclusiones del encargo, comprobadas)

Son las conclusiones del encargo. Al lado de cada una, lo que dicen los datos de arriba.

1. **Perfil del buceador que rellena solo la reserva** (titulación, número de inmersiones, tallas, equipo) y
   **reservar para un buddy**, como PADI.
   - Verificado (búsqueda): PADI guarda certificación, inmersiones, última inmersión y preferencias de alquiler, y deja
     guardar los datos del compañero.
   - No encontramos que PADI guarde tallas: ahí podemos ir un paso más allá (la web de WORLDIVES ya guarda traje,
     escarpines, chaleco, aletas, máscara y lastre).
2. **«Llamar» y «WhatsApp» al cliente en cada reserva**, como FareHarbor (con WhatsApp en lugar de SMS).
   - Verificado (búsqueda): la app de operador de FareHarbor deja llamar o escribir al cliente.
3. **Mover un buceador a otra salida en dos toques**, como BukyApp.
   - Verificado (búsqueda): BukyApp anuncia el traslado de clientes a otra inmersión. Lueira lo hace arrastrando en el
     calendario del panel.
4. **Manifiesto del barco sin conexión**, como DivePlanner Pro.
   - Verificado (búsqueda): DivePlanner Pro anuncia modo sin conexión y «Field Mode» (pasar lista). No explica qué
     pantallas funcionan sin cobertura.

## 9. Qué nos diferencia (conclusiones del encargo, con los matices de los datos)

1. **App nativa de verdad para los tres perfiles** (escáner QR, push, sin conexión), frente a una web.
   - Frente a DivePlanner Pro y BukyApp, que son webs: se mantiene.
   - **Matiz:** FareHarbor y Lueira ya tienen apps nativas en las tiendas (Lueira, una para administración y otra para
     instructores). La diferencia es tener las tres caras (buceador, centro y freelance) en una sola app.
2. **Buscador + motor de reservas + gestión en una sola app, sin comisión.**
   - Se mantiene frente a PADI (solo centros PADI, cobra por reserva), FareHarbor (cargo por reserva) y DivePlanner Pro
     (3–5 % de comisión).
   - **Matiz:** DivePlanner Pro también tiene un directorio público de centros y puntos. Lueira tampoco cobra comisión y
     DiveOps.ai cobra una cuota fija: frente a ellos, lo que nos diferencia es el buscador, no la comisión.
3. **9 idiomas.**
   - Frente a DivePlanner Pro (3), BukyApp (5–6) y FareHarbor (traducción automática): se mantiene.
   - **Matiz:** Lueira también tiene 9.
   - **Pendiente de decisión:** el 13/10 se decidió que la app fuera solo en español, inglés y francés. Si se mantiene,
     esto deja de ser una diferencia de la app (sí de la web). Ver `docs/app/tanda-0.md`.
4. **Velocidad medible** (las promesas del apartado 0 del encargo).
   - Ningún competidor publica tiempos de reserva comparables. Lo más parecido es «en pocos clics» de PADI (2020).
   - Se mide en la Tanda 4 con los scripts de recorrido.

### Idea para más adelante

**Cobro en persona con el móvil (Tap to Pay de Stripe).** Existe en iPhone y Android, y España aparece en la tabla de
Stripe (verificado por búsqueda; hay que confirmarlo en la página antes de prometerlo). **Pendiente de decisión** del
titular (apartado 13.3 del encargo).

---

## 10. Fichas de tienda para hacer capturas

| App | App Store | Google Play |
|---|---|---|
| PADI Adventures | https://apps.apple.com/us/app/padi-adventures-book-diving/id1497105546 | https://play.google.com/store/apps/details?id=com.padi |
| PADI (app principal) | https://apps.apple.com/us/app/padi/id1490797188 | https://play.google.com/store/apps/details?id=com.duns.padiapp |
| FareHarbor | https://apps.apple.com/us/app/fareharbor/id1053611279 | https://play.google.com/store/apps/details?id=com.fareharbor |
| FareHarbor Dock (iPad) | https://apps.apple.com/us/app/fareharbor-dock/id1666347047 | — |
| Lueira Admin | https://apps.apple.com/es/app/lueira-admin/id6737696608 | https://play.google.com/store/apps/details?id=studio.maladeta.lueiraadmin |
| Lueira Team (instructores) | https://apps.apple.com/es/app/lueira-team/id6444336598 | https://play.google.com/store/apps/details?id=studio.maladeta.lueira_instructors |
| Lueira Trackr (fichaje) | https://apps.apple.com/us/app/lueira-trackr/id6740490238 | https://play.google.com/store/apps/details?id=studio.maladeta.trackr |
| DivePlanner Pro | No encontrada (web) | No encontrada (web) |
| BukyApp | No encontrada (web) | No encontrada (web) |
| DiveOps.ai / diveops.net | No encontrada | No encontrada |

Para las webs sin app, capturar en el móvil: https://diveplannerpro.com/, https://www.bukyapp.com/en/dive-center-booking-software, https://diveops.ai/ y https://diveops.net/.

## 11. Pendiente para la versión final

- Abrir cada URL y confirmar los datos marcados «verificado (búsqueda)».
- Confirmar en Stripe que Tap to Pay funciona en España en iPhone y Android, y la versión mínima de Android.
- Confirmar si PADI Adventures sigue activa.
- Pedir precio a BukyApp.
- Saber a qué «DiveOps» se refería el encargo.
- Hacer las capturas de la lista de arriba.
