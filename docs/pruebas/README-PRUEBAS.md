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
| Freelance | `freelance.prueba` | freelance@example.com |
| Buceador | `buzo.prueba` | buzo@example.com |
| Instructor del centro | `instructor.prueba` | instructor@example.com |
| Buceadores extra (para Buddies, cuando esté hecho) | `buzo2.prueba` … `buzo6.prueba` | buzo2@example.com … buzo6@example.com |

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
