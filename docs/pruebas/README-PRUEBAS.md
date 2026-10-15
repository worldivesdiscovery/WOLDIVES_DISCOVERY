# WORLDIVES DISCOVERY · Versión de demostración (paquete DEMO)

Este paquete sirve **solo para probar en tu ordenador**. No se sube nunca al servidor real: si detecta el dominio de
producción, se niega a arrancar. Todo lo que verás es **inventado**: los dos centros, las personas, las reseñas y las
reservas. Los pagos son de prueba y los correos no salen de tu ordenador.

## 1. Arrancar

| Sistema | Qué hacer |
|---|---|
| Windows | Doble clic en **`iniciar-pruebas.bat`** |
| Mac o Linux | En una terminal, dentro de esta carpeta: **`./iniciar-pruebas.sh`** |

Se abre solo el navegador en **http://localhost:8100**. Arriba verás un aviso discreto: «Versión de demostración».
Necesitas Python 3.11 o superior; lo que falte se instala solo la primera vez.

## 2. Cuentas

Las cuentas y su contraseña están en **`CUENTAS-DEMO.txt`**, en esta misma carpeta (no en el código de la web).
Hay una cuenta de **administración**, una por cada **centro** (y su equipo), **dos freelance** y **veinte
buceadores**. Se entra con el usuario o con el email.

## 3. Qué trae la demo

Dos centros inventados que llevan meses funcionando:

| | Bahía Coralina Centro de Buceo | Escafandra Medes |
|---|---|---|
| Dónde | Xàbia (Alicante), Cabo de San Antonio | L'Estartit (Girona), Islas Medes |
| Cuenta | `centro.prueba` | `centro2.prueba` |
| Equipo | instructor e instructora máster (perfil hecho en la web) | instructor y recepción |
| Servicios | inmersión simple y doble, bautizo, Open Water, Nitrox, alquiler, atardecer | Medas, nocturna, bautizo, Advanced, snorkel |
| Puntos | 6 (Cabo San Antonio, Portitxol, Cabo San Martín, Pared Negra…) | 4 (Medes, La Vaca, Carall Bernat, Tascons) |

- **Perfil en los 9 idiomas** de la web: cambia el idioma arriba y abre la página de cada centro.
- **Precios de temporada**: temporada baja desde enero, alta desde el 15 de junio, baja desde octubre y la próxima
  alta ya anunciada (*Panel del centro → Servicios → Tarifas*).
- **Planificación** de los dos próximos meses y **cinco meses de historial** (más de mil inmersiones con pase de
  lista, algún «no se presentó» y alguna cancelación).
- **Reseñas** verificadas con respuestas del centro, **promociones**, un **bono de 10 inmersiones** con usos ya
  descontados, una **promoción conjunta** de los dos centros, **puntos** y ventajas para canjear.
- **Estadísticas** de visitas, clics en «Reservar» y peticiones de información de cinco meses.
- **Vida marina**: entre 8 y 15 especies en cada punto de los dos centros (31 especies con ilustraciones propias).
- **Dos freelance**: un guía de cenotes en México (por días y medio día, otra zona horaria) y una guía y fotógrafa
  en Xàbia (medio día y curso de foto de dos días).

## 4. Qué probar con cada cuenta

- **Administración (`admin.prueba`):**
  - en **Verificaciones**, aprueba el centro pendiente («Arrecife Azul Dénia»);
  - en **Experiencias**, revisa «Semana de cenotes y cavernas»;
  - en **Legal**, mira la denuncia;
  - en **Vida marina y vídeos → Pendientes**, la propuesta de Bahía Coralina (caballito de mar en Piedras Rotas);
  - en **Operación**, el **Estado del sistema** y el botón **Restaurar demo**.
- **Centro (`centro.prueba`):**
  - en **Reservas**, acepta las solicitudes;
  - en **Planning**, crea una salida nueva y abre el **manifiesto** de una salida con buceadores;
  - en **Estadísticas**, los meses de actividad; en **Promociones**, el bono y sus usos;
  - en **Escaparate**, «En otros idiomas»: la presentación en cada idioma.
- **Freelance (`freelance.prueba` y `freelance2.prueba`):**
  - en **Mi agenda**, acepta los días que te piden;
  - mira los días ocupados, el medio día reservado y las vacaciones.
- **Buceador (`buzo.prueba`):**
  - en **Mi área → Mis reservas** (pestañas «Próximas» e «Historial») verás una reserva en cada estado: solicitada,
    aceptada pendiente de pago, confirmada, pagada, cancelada, rechazada, caducada y completada;
  - mira también el **Log Book**, **Mis puntos** y **Recompensas** (tiene el bono de 10 inmersiones);
  - reserva una «Doble inmersión en barco» (bajo petición).
- **Los dos centros a la vez:** muchos buceadores reservan en los dos. Comprueba que cada centro ve **solo sus
  reservas y sus clientes**: si pegas en la barra del navegador la dirección de una reserva del otro centro, sale
  «Reserva no encontrada».

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

En la demo **no se pide la verificación en dos pasos** para conectar Stripe ni para la administración, para que puedas
probarlo todo sin un móvil. En el servidor real es obligatoria: para la administración y para los centros y freelance
con cobros online (y para quien de su equipo tenga el permiso «Cobros»).

## 6. Correos

No se envía ningún correo real. Se guardan como archivos `.eml` en `data/pruebas/correos/`; se abren con Outlook,
Thunderbird o Mail.

## 7. Dejarlo todo como nuevo

- **Con el servidor en marcha:** Administración → Operación → **«Restaurar demo»** (tarda menos de un minuto). Si
  creaste otras cuentas de administración, se conservan.
- **Con el servidor parado:** `scripts\reset_demo.bat` (Windows) o `./scripts/reset_demo.sh` (Mac o Linux).

En los dos casos las fechas vuelven a empezar a partir de hoy. Al arrancar, los datos se renuevan solos si tienen más
de 7 días **o si los hizo otra versión** (por eso, al descomprimir una versión nueva encima, la demo se pone al día).

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

1. Descarga el archivo **`WORLDIVES-Pruebas-v50.55-….apk`** (el enlace llega con cada tanda) y ábrelo.
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


## 9. Vida marina y vídeos de la ruta (v50.51)

Cada punto de los dos centros trae entre 8 y 15 especies (ilustraciones propias, con su autor y licencia).

- **Cualquiera, sin cuenta:** abre Puntos de buceo → «Islas Medes, Costa Brava» o «Cabo San Antonio».
  - Justo encima de **Recorrido virtual** está la franja **«Vida marina en esta inmersión»** con el número de
    especies: fotos pequeñas y redondas que se mueven despacio. Se para al pasar el ratón o al tocarla; en el móvil
    se desliza con el dedo. Si cabe entera, o si tienes activado «reducir movimiento», se queda quieta.
  - Pulsa una especie: se abre un **bocadillo** junto a la foto (en el móvil, un panel pequeño desde abajo) con la
    foto grande, el nombre común, el científico, si es habitual, ocasional o rara en esta inmersión, la mejor época
    y su crédito. Se cierra con la X, tocando fuera o con Esc. También funciona con el teclado.
  - Cambia de idioma arriba y mira los nombres.
- **Vídeos del recorrido virtual:** la demo **no trae vídeos**, porque harían falta enlaces reales y no me invento
  enlaces. Si quieres que la demo los traiga, escribe sus enlaces en `data/demo/videos-demo.json`, por ejemplo:

  ```json
  [{"point": "Islas Medes, Costa Brava", "url": "https://www.youtube.com/watch?v=…", "kind": "360", "title": "Ruta por La Vaca"}]
  ```

  y pulsa **Restaurar demo** (con internet: el servidor descarga la miniatura). También puedes añadirlos a mano:
  *Administración → Puntos → Editar* un punto → «Vídeos de la ruta y vida marina» → pega el enlace → **Comprobar** →
  añadir. Después, en la ficha del punto, sale en **Recorrido virtual** con su miniatura: «Entrar en el recorrido» lo
  abre en el visor (se carga solo al pulsar «Cargar vídeo») o, si la plataforma no deja insertarlo, «Abrir en …» en
  una pestaña nueva.
- **Administración (`admin.prueba`):** *Vida marina y vídeos → Especies*: busca «krake» o «真蛸» y encontrarás el
  pulpo; **Editar** abre los 9 idiomas, la foto, su autor y su licencia; **Buscar una foto libre en Wikimedia
  Commons** necesita internet.
- **Centros y freelance:** Panel → **Vídeos y vida marina**: proponen vídeos y especies; quedan «Pendientes de
  aprobación» hasta que la administración los apruebe, y luego salen con «Aportado por…». El instructor no ve esa
  pestaña (su perfil no tiene «Ficha del centro y ajustes»).
- **Buceador (`buzo.prueba`)**: no ve nada para añadir vídeos o especies.

## 10. Repetir la auditoría (v50.51)

El informe está en `docs/auditoria/v50.51/`. Las herramientas van solo en este paquete (usan las cuentas de la demo):

- **Botones de cada pantalla y papel** (unos 30 minutos; necesita Chromium y `pip install playwright`):
  `python3 tests/navegador/inventario_botones.py --paralelo 4 --salida <carpeta>`. Abre un navegador real con cada
  cuenta, pulsa cada botón, enlace y formulario, y escribe el inventario con «Funciona», «Depende de clave pendiente»
  o el fallo encontrado.
- **Carga** (necesita `pip install locust psutil`): preparar una base de carga aparte con
  `python3 tests/carga/preparar.py construir --dir <carpeta>` y medir por escalones con
  `python3 tests/carga/medir.py --dir <carpeta> --arrancar --workers 4 --pasos 100,250,500,1000`. Nunca contra la web
  real: arranca su propio servidor con una copia.

## 11. Cercanía, Top 10 y tarjetas de servicio (v50.53)

- **Cualquiera, sin cuenta:**
  - **Top 10 buceos:** pulsa «Permitir» cuando el navegador lo pida y verás los mejores buceos cerca de ti con su
    distancia. Si pulsas «Bloquear», o el navegador no contesta en 8 segundos, sale el Top 10 de España con un botón
    para usar tu ubicación. Si ya lo bloqueaste antes, no vuelve a preguntarte.
  - **Puntos de buceo:** con la ubicación, del más cercano al más lejano con los km. Sin ella, España por zonas
    (Costa Brava, Comunidad Valenciana…). El mapa enseña los mismos puntos con el mismo número. Busca «Hawaii»: sale
    «Todavía no hay puntos de buceo en «Hawaii»» y debajo los más cercanos que existen.
  - **Ficha de Bahía Coralina:** las actividades con su foto de fondo, «Puntos de buceo del centro» y las reseñas de
    tres en tres («Ver más reseñas»). En el móvil, cada título cabe en una o dos líneas.
  - **Probar otra ubicación en Chrome:** pulsa F12, luego los tres puntos → *More tools* → *Sensors* y elige
    *Location*.
- **Administración (`admin.prueba`):** *Plantillas de servicios*:
  - sube una foto a una plantilla y abre la ficha del centro: los servicios de esa plantilla la llevan al momento,
    salvo los que tienen foto propia;
  - con el control de intensidad de la capa ves la tarjeta en claro y en oscuro;
  - abajo, en «Fotos propias de los centros», puedes retirar una con su motivo.
- **Centro (`centro.prueba`):** *Servicios → Nuevo servicio*:
  - elige una plantilla y se rellenan el nombre, el texto, la duración y la foto;
  - con «Subir mi propia foto» hay que marcar la casilla de derechos;
  - la vista previa sale en claro y en oscuro, y el punto focal se elige tocando la foto o con las flechas;
  - «Volver a la foto de la plantilla» borra la tuya.

## 12. Acceso rápido, distancias, Puntos, Tipos y moderación (v50.54)

- **Entrar:** en «Iniciar sesión», el recuadro «Acceso rápido a la demostración» entra con un clic como
  Administrador, Centro de buceo 1, Centro de buceo 2, Freelance o Buceador. El formulario normal también funciona,
  abras la demo en `http://localhost:8100` o en `http://127.0.0.1:8100`. Ese recuadro solo existe en esta demo.
- **Distancias** (sin cuenta):
  - con la ubicación precisa, el Top 10 y «Puntos de buceo» dan los km;
  - con una ubicación aproximada, ordenan igual pero sin km, y avisan.

  Para probar Jávea en Chrome: F12 → tres puntos → *More tools* → *Sensors* → *Location*. Elige *Other…*, latitud
  `38.7893` y longitud `0.1662`. Cabo San Antonio sale a 3,2 km.
- **Puntos de buceo:**
  - la barra de filtros se queda fija al bajar, y cada región, tipo, nivel y profundidad lleva su número;
  - «Mapa» enseña todos los puntos filtrados;
  - entra en un punto y pulsa «Volver»: vuelves a la misma posición con los mismos filtros.
- **Tipos de buceo:** elige un tipo. La página baja a sus puntos sin recargarse, y «Atrás» vuelve a como estaba.
- **Moderación (`admin.prueba`):**
  1. En *Centros*, «Ocultar…» en Bahía Coralina, con un motivo.
  2. Entra como `centro.prueba`: el aviso sale arriba del panel. Escribe qué has corregido y «Enviar a revisión».
  3. Vuelve como administración: *Moderación* → «Volver a publicar».
  4. *Actividad* enseña cada paso con su motivo.
- **Datos personales (`admin.prueba`):** son casillas, cada una con su explicación. Marca «Teléfonos de clientes»,
  guarda con un motivo y abre una reserva: ahora sí se ven los teléfonos. Cada consulta queda en *Actividad* como
  «Acceso a datos personales».

## 13. Pago en persona y seguridad de la app (v50.55)

**Pago en persona** (los dos freelance de la demo cobran así):
1. Sin cuenta, abre la ficha de **Diego Arenas** (Freelance) y su «Sesión de fotos y vídeo bajo el agua». La tarjeta y
   la ficha dicen «Pago en persona al profesional», con el mismo precio en todas partes.
2. Entra como `buzo.prueba` y reserva una sesión. «Enviar solicitud» no se activa hasta marcar la casilla del aviso.
   En la reserva no hay ningún WhatsApp todavía.
3. Entra como `freelance.prueba` y acepta la solicitud. Puedes marcarla «Cobrado» o «No se presentó»: solo lo ves tú.
4. Vuelve como `buzo.prueba`: la reserva dice «Confirmada · pago en persona» y aparece «Hablar por WhatsApp». El
   correo de confirmación (`data/pruebas/correos/`) y el justificante PDF llevan el aviso y el «Precio publicado».
5. Como `freelance.prueba`, edita un servicio: «Forma de cobro». «Pago online» está desactivado (Diego no tiene su
   cuenta de Stripe conectada) y «Pago en persona» solo deja «Bajo petición».

**Seguridad de la app** (APK WORLDIVES Pruebas v50.55):
1. Entra como **Centro** o **Freelance**. La app pide proteger la cuenta con la huella o el código del móvil (o, si
   el móvil no tiene bloqueo de pantalla, con un PIN de 6 números).
2. Sal de la app más de **5 minutos** y vuelve: pide la huella, el código o el PIN.
3. Falla 5 veces seguidas (el PIN de la app o la huella): la sesión se cierra, el móvil borra sus datos y pide
   entrar de nuevo.
4. En el ordenador, entra con la misma cuenta y abre **Mi cuenta → Dispositivos conectados**: sale el móvil. Pulsa
   «Cerrar sesión» en él. En el móvil, al volver a la app, sale y vuelve a la pantalla de acceso.
5. Al entrar desde un dispositivo nuevo llega el correo «Nuevo inicio de sesión» (en `data/pruebas/correos/`).
6. Con el **Buceador**, el bloqueo es opcional: **Mi área → Ajustes → Seguridad**.
