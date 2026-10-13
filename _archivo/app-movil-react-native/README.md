# App WORLDIVES · versión de pruebas 0.1

App de reservas de buceo para Android e iOS, hecha con **React Native + Expo** (TypeScript). El diseño, la API y la
estimación están en `docs/app-movil/`.

**Qué es la 0.1:**
- las pantallas de los tres perfiles: buceador (con cuenta y por primera vez), centro y freelance;
- en español, inglés y francés;
- **datos de ejemplo**. Los pagos y el inicio de sesión con Apple o Google están **simulados**; sus hojas dicen
  «Simulado»;
- todavía no habla con el servidor de la web. Eso llega en la 0.2.

## Conseguir el APK e instalarlo

GitHub lo compila solo con cada cambio en `app-movil/`.
1. En el repositorio, pestaña **Actions** → flujo **«App Android (APK de pruebas)»** → la última ejecución en verde.
2. Abajo, en **Artifacts**, descarga **WORLDIVES-apk-pruebas** (un zip con el APK dentro). Se guarda 30 días.
3. Pasa el APK al móvil Android y ábrelo. La primera vez Android pide permiso para **instalar apps de origen
   desconocido** desde esa app (Archivos, Chrome o la que uses): concédelo solo para instalar esta.
4. Las siguientes versiones se instalan encima y conservan lo guardado.

Para compilarlo a mano: Actions → «App Android (APK de pruebas)» → **Run workflow**.

El APK va firmado con la clave de pruebas de la plantilla de Expo. **No sirve para Google Play.** La versión de la
tienda llevará su propia clave, guardada fuera del repositorio.

## Probarla

Al abrir, la pantalla **«Ver la app como»** deja elegir perfil:
- **Buceador con cuenta:** titulación y tallas guardadas; reserva en 2 toques más la confirmación del pago.
- **Buceador por primera vez:** sin cuenta; el botón de pago crea la cuenta con Google o Apple (simulado).
- **Centro de buceo:** Hoy y Mañana, equipo a preparar, cancelar por meteo con 10 s para deshacer, y check-in con la
  cámara.
- **Freelance:** su día, agenda (un toque bloquea o abre un día), ofertas de trabajo y cobros.

**Pruebas cronometradas** (misma pantalla):
- «Reservar en menos de 30 s» (con cuenta y primera vez);
- «Centro: quién bucea mañana (10 s)».

El cronómetro arranca al pulsar y se para solo. Cada resultado queda guardado con tiempo y toques en **Perfil**
(buceador) o **Más** (centro). Para volver a elegir perfil: «Cambiar de perfil de prueba».

**Check-in:** el QR de cada reserva (pantalla Reservas del buceador) lleva el texto `worldives:reserva:WOD-000124`.
Con un segundo móvil, el centro lo lee desde Hoy → abrir la salida → Check-in. También se puede marcar a mano.

## Trabajar en el código

```bash
cd app-movil
npm ci
npx expo start          # Expo Go o un emulador
npm run web             # en el navegador, para revisar pantallas
npm run typecheck       # TypeScript
node scripts/textos.mjs # comprueba que en.json y fr.json tienen todos los textos
```

- **Pantallas:** `app/`, una por archivo (expo-router).
- **Piezas comunes:** `src/ui.tsx` (botones, tarjetas, hojas, QR), `src/theme.ts` (colores oscuro y claro),
  `src/icons.tsx`.
- **Estado guardado en el móvil:** `src/store.tsx`.
- **Datos de ejemplo:** `src/demo.ts`. Desaparecen en la 0.2.

**Textos:** se escriben en español dentro de `t('…')`. La traducción va en `src/idiomas/en.json` y `fr.json`, con el
texto español como clave. `node scripts/textos.mjs --lista` saca todos los textos. El flujo de GitHub se para si falta
alguno o si una traducción pierde una variable `{n}`.

**Fotos:** `assets/foto-*.jpg` son tres fotos de la web que aún no tienen el origen registrado
(`docs/legal/imagenes-origen.md`). Antes de enseñar la app fuera del equipo hay que cambiarlas por fotos con licencia.

## Lo que falta para la 0.2

- **Servidor:** la API `/api/v1/` en la web (doc. 2) y conectar salidas, reservas, check-in y avisos reales.
- **Estado del mar:** boyas de Puertos del Estado, con fuente y hora (doc. 2, «Estado del mar»).
- **Pagos e identidad:**
  - Stripe con Google Pay en el APK;
  - Apple Pay y la versión de iOS cuando estén las cuentas de desarrollador (D-U-N-S);
  - inicio de sesión real con Google y Apple, y passkeys.
- **Push** (Firebase en Android y APNs en iOS).
