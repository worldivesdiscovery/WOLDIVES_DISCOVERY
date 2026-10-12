# WORLDIVES DISCOVERY · Entorno de pruebas

Este paquete sirve **solo para probar en tu ordenador**. No se sube nunca al servidor real: si detecta el dominio de
producción, se niega a arrancar.

## 1. Arrancar

| Sistema | Qué hacer |
|---|---|
| Windows | Doble clic en **`iniciar-pruebas.bat`** |
| Mac o Linux | En una terminal, dentro de esta carpeta: **`./iniciar-pruebas.sh`** |

Se abre solo el navegador en **http://localhost:8100**. Arriba verás la banda «Entorno de pruebas».
Necesitas Python 3.11 o superior; lo que falte se instala solo la primera vez.

## 2. Crear tu cuenta de administración (la primera vez)

El entorno de pruebas no trae cuenta de administración: la creas tú.

1. Abre **http://localhost:8100/#/setup**. También hay un enlace en «Iniciar sesión».
2. Escribe tu nombre, email, usuario y una contraseña de 10 caracteres o más.
3. Entrarás directamente en **Administración**.

Esta pantalla solo existe en el entorno de pruebas. En el servidor real el administrador se crea con
`python app/server.py --create-admin`.

## 3. Cuentas de prueba

Todas usan la contraseña **`Worldives-Prueba-2026`**.

| Papel | Usuario | Correo |
|---|---|---|
| Centro de buceo | `centro.prueba` | centro@example.com |
| Segundo centro (para ver el aislamiento entre centros) | `centro2.prueba` | centro2@example.com |
| Freelance | `freelance.prueba` | freelance@example.com |
| Buceador | `buzo.prueba` | buzo@example.com |
| Instructor del centro | `instructor.prueba` | instructor@example.com |
| Buceadores extra (algunos reservan en los dos centros) | `buzo2.prueba` … `buzo6.prueba` | buzo2@example.com … buzo6@example.com |

## 4. Qué probar con cada cuenta

- **Administración (tu cuenta):**
  - en **Verificaciones**, aprueba el centro pendiente;
  - en **Experiencias**, revisa «Semana de cenotes y cavernas»;
  - en **Legal**, mira la denuncia.
- **Centro (`centro.prueba`):**
  - en **Reservas**, acepta la solicitud;
  - en **Planning**, crea una salida nueva;
  - abre el **manifiesto** de una salida con buceadores.

  Tiene 5 servicios (inmersión simple, doble, bautizo, curso Open Water y alquiler de equipo) con los dos modos de reserva, salidas esta semana, la próxima y el mes que viene, un barco y un instructor.
- **Freelance (`freelance.prueba`):**
  - en **Mi agenda**, acepta los días que te piden;
  - mira los días ocupados, el medio día reservado y las vacaciones.

  Tiene 3 servicios: guía por días, medio día y sesión de fotos y vídeo.
- **Buceador (`buzo.prueba`):**
  - en **Mi área → Mis reservas** (pestañas «Próximas» e «Historial») verás una reserva en cada estado: solicitada, aceptada pendiente de pago, confirmada, pagada, cancelada, rechazada, caducada y completada;
  - mira también el **Log Book** y **Mis puntos**;
  - reserva una «Doble inmersión en barco» (bajo petición).

- **Segundo centro (`centro2.prueba`):** tiene 2 servicios en las Islas Medas y reservas de `buzo.prueba`,
  `buzo2.prueba`, `buzo3.prueba` y `buzo4.prueba`, que también reservan en `centro.prueba`. Comprueba que cada centro
  ve **solo sus reservas y sus clientes**: si pegas en la barra del navegador la dirección de una reserva del otro
  centro, sale «Reserva no encontrada».

## 4 bis. Avisos a todos los buceadores (WhatsApp, correo y app)

En el entorno de pruebas el WhatsApp es **simulado**: los dos centros tienen un «WhatsApp de prueba» conectado y los
mensajes **no salen**; se guardan en `data/pruebas/avisos/c-<número del centro>/whatsapp/`, uno por archivo (una
carpeta por centro: así se ve que cada aviso sale del número de su centro). Los correos se guardan en
`data/pruebas/correos/` y los avisos de la app aparecen en «Mi área → Avisos» de cada buceador.

1. Entra como `centro.prueba` → **Planning** → abre una salida con buceadores (por ejemplo, la «Doble inmersión en
   barco» de dentro de 4 días) → **Cancelar salida y avisar a todos**.
2. Elige el motivo, escribe una nota si quieres y mira la confirmación: cuántos reciben cada canal, los nombres con
   inicial, qué pasa con el dinero y el mensaje en el idioma de cada buceador. Para confirmar, escribe la fecha que
   te indica (por ejemplo `16/10`).
3. Tienes 10 segundos para **Deshacer**. Después verás el **estado** de cada buceador y canal.
4. Prueba también **Cambio de hora o punto** en otra salida y, en **Avisos y WhatsApp**, la hora del recordatorio
   del día antes.
5. Entra como `buzo2.prueba`: en **Mi área → Avisos** está el aviso, con el enlace que abre solo esa reserva. Los
   avisos de `centro2.prueba` no se ven afectados.

Casos preparados: `buzo5.prueba` tiene el móvil **sin prefijo** (no recibe WhatsApp; su perfil le avisa) y
`buzo6.prueba` **no ha dado permiso** de WhatsApp (recibe correo y app). En **Mi cuenta** de cualquier buceador puedes
cambiar el prefijo y marcar o quitar «Recibir por WhatsApp los avisos de mis reservas del centro».

## 5. Pagar con la tarjeta de prueba de Stripe

Sin claves de Stripe, el pago online aparece desactivado. Para probar un pago completo:

1. En la carpeta de este paquete, crea un archivo `.env` con tus claves de **modo test** de Stripe:
   `STRIPE_SECRET_KEY=sk_test_…`. Nunca uses una clave real (`sk_live_…`): el entorno de pruebas no arranca con ella.
2. Vuelve a arrancar con `iniciar-pruebas`.
3. Entra como `centro.prueba` → **Cobros y pagos**, pulsa el botón de Stripe y completa el alta en modo test.
4. Entra como `buzo.prueba`, reserva la «Inmersión simple en barco» (pago al reservar) y paga con la tarjeta
   **`4242 4242 4242 4242`**, cualquier fecha futura y cualquier CVC.

## 6. Correos

No se envía ningún correo real. Se guardan como archivos `.eml` en `data/pruebas/correos/`; se abren con Outlook,
Thunderbird o Mail.

## 7. Dejarlo todo como nuevo

- **Con el servidor en marcha:** Administración → Operación → **«Restaurar demo»**. Tu cuenta de administración se conserva.
- **Con el servidor parado:** `scripts\reset_demo.bat` (Windows) o `./scripts/reset_demo.sh` (Mac o Linux). En este caso también se borra tu cuenta de administración y la vuelves a crear en el paso 2.

En los dos casos las fechas vuelven a empezar a partir de hoy. Si los datos tienen más de 7 días, se renuevan solos al arrancar.
