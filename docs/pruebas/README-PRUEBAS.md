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
| Instructor del centro (solo pasa lista y escanea) | `instructor.prueba` | instructor@example.com |
| Instructora máster (perfil propio del centro: pasa lista, ve todas las salidas, organiza barcos y grupos, ve estadísticas) | `master.prueba` | master@example.com |
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

## 8. Probar la app en tu móvil Android (WORLDIVES Pruebas)

La app de pruebas se instala al lado de la app normal (no la sustituye) y se conecta a **este** entorno de pruebas,
que corre en tu ordenador. El móvil y el ordenador tienen que estar **en la misma wifi**.

**En el ordenador**

| Sistema | Qué hacer |
|---|---|
| Windows | Doble clic en **`iniciar-pruebas-movil.bat`**. Si Windows pregunta por el cortafuegos, pulsa **Permitir** (red privada) |
| Mac o Linux | En una terminal, dentro de esta carpeta: **`./iniciar-pruebas-movil.sh`** |

La ventana muestra una línea como esta: **«En el móvil (misma wifi), escribe: http://192.168.1.50:8100»**.
Apunta esa dirección: es la de tu ordenador.

**En el móvil, la primera vez**

1. Descarga el archivo **`WORLDIVES-Pruebas-v50.49-….apk`** (el enlace llega con cada tanda) y ábrelo.
2. Android avisa de que es una app de fuera de Google Play: pulsa **Configuración → Permitir de esta fuente**, vuelve
   atrás y pulsa **Instalar**. Si Google Play Protect pregunta, pulsa **Instalar de todas formas**.
3. Abre **WORLDIVES Pruebas** (icono con la franja naranja «TEST»).

**Cada vez que pruebes**

1. En el campo **Servidor de pruebas** escribe la dirección que te dio el ordenador (basta con `192.168.1.50`: el
   `:8100` se pone solo) y pulsa **Probar la conexión**. Tiene que decir «Conectado».
2. Pulsa una cuenta de **Entrar rápido**: Buceador, Centro, Segundo centro, Freelance, Instructor o Instructora máster.
   Entras sin escribir contraseña (solo en pruebas). También puedes **Entrar sin cuenta** para verla como visitante.
3. La app recuerda el servidor y la sesión: la próxima vez se abre directamente.
4. Para cambiar de cuenta o de servidor: **Mi área → Ajustes → Cambiar de servidor o de cuenta de prueba**.

**Si algo falla:** pulsa **Reportar fallo** en la banda naranja de arriba (o **agita el móvil**). Escribe qué hacías
y qué esperabas y pulsa **Enviar**. Llega a la carpeta **`data/pruebas/fallos/`** del ordenador, con la captura de la
pantalla, la pantalla en la que estabas, la versión, el modelo del móvil y la hora.

**Qué es distinto en la app de pruebas:** la banda naranja siempre visible, los pagos en modo test de Stripe
(apartado 5: tarjeta `4242 4242 4242 4242`), WhatsApp que no se abre (enseña el mensaje que se enviaría) y correos
que se guardan en `data/pruebas/correos/`.

**Al instalar una versión nueva** encima de la anterior se conservan el servidor y la sesión. Solo si Android dice
«La app no está instalada» o «conflicto de firma», desinstala WORLDIVES Pruebas y vuelve a instalarla (pasa si la
clave de firma de pruebas se ha renovado).

### 8.1 Qué probar en la app con cada cuenta (v50.49)

Los datos de prueba tienen **una salida al atardecer cada día de la semana** con buceadores, para que «Hoy» tenga
siempre una lista del barco, y una solicitud que caduca pronto.

- **Centro (`centro.prueba`)**, pestañas Hoy · Agenda · Escanear · Solicitudes · Más:
  - **Hoy**: las cifras, «Urgente», la salida de hoy con sus asientos y «Mañana».
  - Toca la salida: **lista del barco**. Marca llegadas con el botón redondo. Prueba **sin cobertura** (modo avión):
    marca a alguien, vuelve a quitar el modo avión y mira cómo se envía sola.
  - **Contar a bordo** y **Resumen barco** (comparte el resumen y abre el PDF firmado).
  - **Escanear**: con otra cuenta (`buzo.prueba`) en otro móvil o en el ordenador abre la reserva y su QR; escanéalo
    con la cámara o escribe el código que hay debajo. Prueba también un código de otro centro.
  - **Solicitudes**: rechaza una con un motivo, acepta otra, «Aceptar varias», «Ofrecer otra salida»; en
    **Pendientes de pago**, «Recordar por WhatsApp» (en pruebas enseña el texto) y «Cobrar en el centro».
  - **Agenda**: mes, semana y día; **Crear salida** repitiéndola una semana.
  - **Más → Nueva reserva**: una reserva por teléfono en menos de 45 s.
  - **Más → Borrar mi cuenta para siempre**: verás las reservas futuras y «Cancelar y avisar a todos». (Si lo pruebas
    entero, la cuenta se cierra: vuelve a entrar con `centro.prueba` y pulsa **Reabrir mi cuenta**; o restaura la
    demo, apartado 7.)
- **Instructor (`instructor.prueba`)**: no tiene «Solicitudes», ni cobros, ni equipo. Pasa lista y escanea.
- **Instructora máster (`master.prueba`)**: perfil creado por el centro en la web. En la web, con `centro.prueba`,
  **Panel → Equipo → Perfiles**: cambia lo que puede hacer «Instructor máster» y mira cómo cambia su app.
- **Freelance (`freelance.prueba`)**: **Hoy** con sus trabajos por días; en **Agenda**, toca un día y **Bloquear**
  (todo el día, mañana o tarde).
- **Buceador (`buzo.prueba`)**: en **Reservas**, «Ver QR» funciona también sin cobertura.

