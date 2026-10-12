# WORLDIVES DISCOVERY — Encargo: app de Android e iOS

Pega este documento entero en la sesión de código.

## Objetivo
WORLDIVES tiene que estar en Google Play y en la App Store, para buceadores y para centros, **con la misma base que la web**: una sola aplicación, un solo servidor y las mismas cuentas, reservas, pagos e idiomas. La app aporta lo que la web no puede dar del todo:
- avisos push fiables;
- uso en el barco sin cobertura;
- cámara para escanear el QR del check-in y los documentos;
- acceso rápido desde la pantalla de inicio;
- presencia en las tiendas.

## Reglas
- **Versión base:** la última disponible. Se hace cuando estén terminados los encargos 1 y 2 de la tabla de orden, y mejor después del 9 (promesas).
- **Antes de cada punto, comprobar si ya está hecho:** «Ya estaba», «Completado», «Nuevo» o «Pendiente de decisión». Por ejemplo, la app instalable (PWA), el modo sin conexión del barco y el selector de idioma ya existen.
- **Decisiones vigentes:** intermediario sin comisión, cobro directo por Stripe, dos modos de reserva, puntos en lugar de monedero, sin mensajería ni red social, 10 idiomas, sin paquetes de varios organizadores.
- **Claves y certificados** (Apple, Google, Firebase, firma de la app) solo en el `.env` del servidor o en el gestor de secretos de la compilación, nunca en el código ni en el chat.

## 1. Tecnología (decisión recomendada)
1. **Capacitor:** envuelve la web actual en una app nativa de Android e iOS y añade los complementos nativos que hagan falta. Ventajas:
   - un solo código;
   - cada mejora de la web llega a la app sin publicar otra versión, salvo los cambios nativos.
2. **Complementos nativos:**
   - push (Firebase Cloud Messaging en Android y APNs en iOS);
   - cámara y escáner de QR;
   - almacenamiento seguro de la sesión;
   - compartir;
   - abrir enlaces de la web dentro de la app (enlaces universales y App Links);
   - pantalla de inicio y el icono.
3. **Para que Apple no la rechace por ser «solo una web»** (norma 4.2, funcionalidad mínima), la app ofrece:
   - push;
   - modo sin conexión;
   - escáner de QR;
   - acceso con Face ID o huella para volver a entrar;
   - el carné o Log Book disponible sin conexión.
4. **Alternativa** si un día se necesita: React Native o Flutter. Se descarta ahora porque obliga a mantener dos aplicaciones.

## 2. Funciones de la app
1. **Buceador:**
   - buscar;
   - reservar y pagar (Stripe, con Apple Pay y Google Pay);
   - «Mis reservas» sin conexión;
   - avisos (confirmación, pago, recordatorios, cambios y cancelaciones);
   - firmar el descargo;
   - Log Book y puntos.
2. **Centro y freelance:**
   - «Hoy» como pantalla de inicio;
   - planning y agenda;
   - manifiesto y check-in sin conexión (QR del buceador o lista);
   - aceptar o rechazar solicitudes desde el aviso;
   - avisos de reservas nuevas y de solicitudes a punto de caducar.
3. **Cuenta:**
   - inicio de sesión igual que la web, con verificación en dos pasos;
   - Face ID o huella para volver a entrar;
   - **borrar la cuenta desde la app** (obligatorio en las dos tiendas).
4. **Avisos:**
   - los mismos que el correo, en los 10 idiomas;
   - cada persona elige cuáles recibe en «Mi cuenta»;
   - nunca publicidad.

## 3. Pagos y normas de las tiendas
- **Las reservas son servicios que se disfrutan fuera de la app** (buceo, cursos, viajes). Las tiendas permiten cobrarlas con Stripe, sin la compra integrada de Apple ni de Google (App Store, norma 3.1.3(e); Google Play, política de pagos para bienes y servicios físicos).
- **Los planes de pago de los centros** (Fase 6.2) no se venden dentro de la app. Se contratan en la web, y la app no muestra precios ni enlaces de compra de planes. **Pendiente de confirmar con el abogado** antes de publicar.
- **Privacidad en las tiendas:**
  - etiquetas de privacidad de Apple y formulario de seguridad de datos de Google, iguales a la política de privacidad;
  - permiso de cámara, ubicación y avisos pedido solo cuando hace falta, con una frase que explica para qué.

## 4. Publicación
1. **Cuentas** (las abre el titular):
   - Apple Developer Program: unos 99 USD al año, a nombre de la empresa, con número D-U-N-S;
   - Google Play Console: unos 25 USD una sola vez.
2. **Fichas de las tiendas en los 10 idiomas:**
   - nombre, descripción, capturas de móvil y tableta, icono, categoría (Viajes o Deportes);
   - enlace a la política de privacidad y contacto de soporte.
3. **Pruebas cerradas** antes de publicar:
   - TestFlight (iOS);
   - prueba interna y cerrada de Google Play (Android pide un mínimo de personas y de días en las cuentas nuevas).
4. **Compilación y firma automáticas** con GitHub Actions, con las claves guardadas como secretos del repositorio.
5. **Versión mínima:**
   - Android 8;
   - iOS 15.
   - Comprobar el nivel de API que exige Google Play en el momento de publicar.

## 5. Pruebas
- **Dispositivos:** un Android de gama media y un iPhone de hace 3 años, además de emuladores.
- **Recorridos de las 4 promesas en la app**, con los scripts del encargo de experiencia.
- **Avisos push:** llegan con la app cerrada, en el idioma de la persona, y al tocarlos abren la pantalla correcta.
- **Sin conexión en el barco:** check-in, sincronización y conflictos (como en la web).
- **Seguridad:**
  - la sesión se guarda cifrada;
  - cerrar sesión borra los datos del dispositivo;
  - sin claves dentro de la app.
- **Accesibilidad:** tamaño de letra del sistema, lector de pantalla (TalkBack y VoiceOver) y modo oscuro.
- **Capturas y vídeos** en Android e iOS.

## Entrega
1. Notas de versión, tabla de estado y lista de lo pendiente de decisión del titular y del abogado.
2. Guía para el titular (`docs/app/publicar.md`) paso a paso para publicar y actualizar la app.
3. Apps en prueba cerrada en las dos tiendas.
4. Publicación cuando el titular lo apruebe.

## Pendiente del titular
- Abrir las cuentas de Apple y Google, y el número D-U-N-S de la empresa.
- Proyecto de Firebase para los avisos de Android.
- Textos e imágenes de las fichas de las tiendas, o aprobar los que se preparen.
- Abogado: pagos de planes fuera de la app, y las etiquetas de privacidad.
