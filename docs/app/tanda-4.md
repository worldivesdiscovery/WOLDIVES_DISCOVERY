# App móvil en 3 módulos · Tanda 4 (v50.49)

Encargo «App móvil en 3 módulos (Buceador, Centro PRO y Freelance PRO) y APK de pruebas».

La Tanda 4 entrega lo que hace que la app funcione en el barco y avise a tiempo: **sin conexión**, **avisos**
(push y recordatorios), **medidas** de las promesas y repaso de **accesibilidad**. Va con las Tandas 2 y 3 en la v50.49.

## Sin conexión

| Qué | Cómo |
|---|---|
| **Hoy y la agenda** | Lo último que se vio se guarda en el móvil. Sin cobertura se enseña con «Sin conexión: datos guardados en el móvil a las …». |
| **Listas del barco de hoy y de mañana** | Al abrir «Hoy» con cobertura se guardan en el móvil. En el barco se abren sin red. |
| **Marcar llegadas sin cobertura** | La marca se ve al momento y queda «Pendiente de enviar». Cuando vuelve la red (o al volver a la app) se envía sola. Si otra persona cambió lo mismo antes, gana lo del servidor y se avisa de quién lo cambió. |
| **Contar a bordo** | Funciona sin red con la lista guardada; el recuento solo se guarda en el historial cuando hay red (se avisa). |
| **Buceador: sus reservas y su QR** | Al abrir «Reservas» se guardan sus reservas próximas y el QR con el código de cada una. «Ver QR» funciona sin red («Funciona sin conexión: está guardado en este móvil»). |
| Escanear sin red | No puede comprobar la reserva en el servidor: dice que se busque a la persona en la lista del barco, que sí está guardada. |

## Avisos

| Qué | Estado |
|---|---|
| **Recordatorio en el móvil del equipo**, 45 minutos antes de la primera salida del día (aviso local, no sale nada del teléfono). Al tocarlo abre la lista del barco | **Nuevo** |
| **Notificaciones push** (Firebase): cada correo de una reserva llega también como push al móvil de la persona, con el mismo asunto en su idioma; al tocarla abre la reserva. Teléfonos que desinstalaron la app se dan de baja solos. El servidor está **listo y probado con un Firebase simulado** | **Pendiente**: crear la cuenta de Firebase de WORLDIVES |

**Para activar las push** (cuando quieras, sin tocar el código):
1. Crea el proyecto de Firebase de WORLDIVES y una cuenta de servicio con permiso de Firebase Cloud Messaging.
2. En el `.env` del servidor:
   ```
   WOD_FCM_PROJECT_ID=<id del proyecto>
   WOD_FCM_CREDENTIALS=/ruta/fuera/del/repositorio/firebase-servicio.json
   ```
   El archivo de la cuenta de servicio va en el servidor, **nunca** en el repositorio ni en los zips.
3. Pon `google-services.json` del proyecto en `movil/android/app/` y compila la app otra vez. La app solo pide el
   permiso de notificaciones cuando el servidor **y** la app tienen Firebase (si no, ni lo pregunta).

## Medidas de las promesas

La app mide en el propio móvil cuánto tarda cada pantalla en enseñar sus datos (`window.WDAMedidas`). Las pruebas
automáticas comprueban:

| Promesa | Medida |
|---|---|
| «Hoy» en menos de 5 s | Navegador (servidor local): menos de 1 s. Emulador de GitHub (sin aceleración gráfica, mucho más lento que un móvil): ver notas de la v50.49 |
| Nueva reserva por teléfono en menos de 45 s | Recorrido automático: unos 2 s (una persona necesita escribir el nombre y el teléfono) |
| Pasar lista sin deslizar, botones de 56 px | Comprobado en el navegador y en la pantalla del emulador |

## Accesibilidad

- Todos los botones de trabajo miden al menos 56 px (llegada, aceptar, rechazar, contar).
- Nada se sale de la pantalla a 360 px de ancho, con el texto **Normal** y **Enorme** (todas las pantallas PRO).
- Iconos con texto o con etiqueta para el lector de pantalla; los asientos de la salida se leen como frase
  («4 confirmados, 0 pendientes de pago, 8 libres»).
- Colores con su icono y su texto: nunca solo el color (urgente, pendiente, confirmada).
- La app PRO está entera en español, inglés y francés (comprobado: ningún texto sin traducir).

## Tabla de estado

| Punto | Estado |
|---|---|
| Sin conexión: Hoy, agenda, listas del barco, marcas pendientes de enviar | **Nuevo** |
| Sin conexión: reservas y QR del buceador | **Nuevo** |
| Recordatorio local de la primera salida del día | **Nuevo** |
| Push por Firebase: servidor, registro de teléfonos, envío y bajas | **Nuevo** (listo); **Pendiente**: cuenta de Firebase |
| Medidas de las pantallas en el móvil y comprobaciones automáticas | **Nuevo** |
| Repaso de accesibilidad (56 px, 360 px, Enorme, lector de pantalla, colores) | **Completado** |
