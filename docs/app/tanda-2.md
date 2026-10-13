# App móvil en 3 módulos · Tanda 2 (v50.49)

Encargo «App móvil en 3 módulos (Buceador, Centro PRO y Freelance PRO) y APK de pruebas».

La Tanda 2 entrega:
- el módulo **Centro PRO** completo en la app;
- los **perfiles del equipo** que cada centro decide en la web (decisión 4 del titular);
- **«Borrar mi cuenta para siempre»** para centros y freelance, con 6 meses para volver (decisión 5).

Por decisión del titular (13/10) **no se para entre tandas**: las Tandas 2, 3 y 4 van juntas en la v50.49 y se
prueban de una vez. Notas de la Tanda 3: `tanda-3.md`. Tanda 4: `tanda-4.md`.

## Qué ve el centro en la app

Pestañas: **Hoy · Agenda · Escanear · Solicitudes · Más**. «Escanear» es el botón central.

| Pantalla | Qué hace |
|---|---|
| **Hoy** | Cuatro cifras (salidas de hoy, llegados / buceadores, solicitudes, pendientes de pago). «Urgente»: lo que caduca en menos de 3 horas, con su cuenta atrás. Las salidas de hoy con sus plazas dibujadas como asientos (verde: confirmada; naranja punteado: falta el pago). «Mañana» plegado. «Ver semana». |
| **Agenda** | **Mes** coloreado como una carta de profundidad (más oscuro = más lleno), **Semana** con una barra por salida y **Día**. **Crear salida**: la actividad propone la hora y las plazas de su última salida (plantilla) y se puede repetir cada semana (hasta 12). |
| **Escanear** | La cámara del móvil lee el QR de la reserva y marca la llegada. Si no se puede escanear, se escribe el código que el buceador lleva debajo del QR (`1234-A1B2C3`). **Ráfaga**: después de cada buceador la cámara se abre sola. También comprueba y canjea códigos de promoción. |
| Resultado del escáner | Ficha grande: nombre, personas, actividad, hora, pagado, código, plazas sin firmar. Avisos claros: ya estaba marcada, otra salida, otro día, solicitud sin aceptar, falta el pago («Cobrar en el centro y marcar»), cancelada, **otro centro** (sin enseñar nada de esa reserva), código mal escrito. «Deshacer». |
| **Solicitudes** | «Por contestar», con anillo de cuenta atrás, plazas libres, precio y nota del buceador. **Aceptar** (botones de 56 px), **Rechazar** con motivos en un toque (salida completa, mal tiempo, sin guía, nivel, otro) y nota, **Aceptar varias**, **Ofrecer otra salida** del mismo servicio, WhatsApp y Llamar. |
| Pendientes de pago | Cuenta atrás del plazo de pago, **Recordar por WhatsApp** (texto con el enlace de pago, en el idioma del cliente) y **Cobrar en el centro** (efectivo, datáfono, transferencia o «pagará al llegar»). |
| **Salida** (lista del barco) | Buceadores por grupo y guía. Botón redondo de **56 px** para marcar la llegada (sin deslizar). Por buceador: «No vino», Llamar, WhatsApp en su idioma, nota para el barco, tallas, contacto de emergencia, firmar el descargo. Añadir buceador. **Cambiar la hora y avisar** y **Cancelar la salida y avisar a todos**, con 10 segundos para deshacer. |
| **Contar a bordo** | Se toca a cada persona que se ve en el barco (o + y −) y «Comprobar» dice si están todos, cuántos faltan o sobran y quién no se ha tocado. Queda en el historial de la salida. |
| **Resumen para el barco** | Letra grande: buceadores, nitrox, alquiler y grupos. **Compartir el resumen** (WhatsApp del patrón…) y **PDF firmado**: lleva su huella SHA-256 y quién lo generó, para comprobar una copia impresa. |
| **Reservas** | Buscador (nombre, email, nº) y filtros Hoy · Próximas · Pendientes de pago · Canceladas. |
| **Nueva reserva** | Por teléfono o en el mostrador: nombre, teléfono, actividad, salida, personas y «paga al llegar / ya ha pagado». Medido: menos de 45 s (prueba automática). |
| **Más** | Estado de WhatsApp Business y del plan; Reservas, Nueva reserva, Estadísticas, Cobros; **«Disponible en la web»** (servicios y precios, barcos y grupos, avisos, equipo y perfiles, ficha del centro, herramientas, mi plan) que se abre dentro de la app; Mi cuenta, Ajustes, cambiar de centro, cerrar sesión y **«Borrar mi cuenta para siempre»**. |

## Perfiles del equipo (decisión 4)

- **En la web**, Panel del centro → **Equipo**: debajo de las personas está «Perfiles y lo que puede hacer cada uno».
  - Se crean perfiles con nombre propio («Instructor máster»…) y se marca lo que puede hacer cada uno.
  - Los cuatro perfiles de siempre (Encargado, Recepción, Instructor) también se pueden cambiar, y volver «a lo de
    siempre» con un botón. El Propietario no se cambia.
  - Un perfil que alguien tiene no se puede borrar (primero se le cambia el perfil a esa persona).
- **En la app** no hay ajustes de perfiles: cada persona ve solo lo que su perfil permite (pestañas, botones, «Más»).
  Lo que se cambia en la web se aplica en la siguiente pantalla que abre.
- **El servidor decide siempre**: aunque alguien llame a la dirección a mano, sin el permiso recibe «Tu perfil no
  permite…».

**Los permisos** (`app/wod/roles.py`):

| Permiso | Qué permite |
|---|---|
| Pasar lista y escanear QR | Marcar llegadas, escanear, firmas a bordo, contar a bordo |
| Ver todas las salidas | Sin él, solo las salidas donde guía un grupo y las que aún no tienen guías |
| Organizar barcos y grupos | Barcos, grupos y guías de cada salida |
| Reservas, solicitudes y clientes | Aceptar o rechazar, crear y cambiar reservas, cobrar en el centro, escribir a clientes |
| Salidas y servicios | Crear, cambiar y cerrar salidas y servicios |
| Cancelar salidas y avisar a todos | Avisos masivos (cancelar o cambiar la hora de una salida) |
| Cobros y devoluciones | Ver los cobros, exportar los pagos y devolver dinero |
| Ficha del centro y ajustes | Ficha pública, fotos, tarifas, seguro, política de cancelación, descargo, integraciones, importar clientes |
| Estadísticas | Ver las estadísticas |

**Solo el propietario** (no se puede dar a ningún perfil): el equipo y sus perfiles, la cuenta de Stripe y los datos
de cobro, los datos fiscales, el plan, el registro de actividad y cerrar la cuenta del centro.

**Cómo vienen los perfiles de siempre** (cada centro los cambia):

| Perfil | Permisos |
|---|---|
| Propietario | Todo |
| Encargado | Todo lo demás (todos los permisos de la tabla), como dejaste escrito el 13/10 |
| Recepción | Lo de antes: pasar lista, ver todas las salidas, barcos y grupos, reservas, salidas y servicios, estadísticas. **Sin avisos masivos** (lo fijó el encargo de avisos de la v50.47); se le pueden dar con un toque |
| Instructor | Pasar lista y escanear. Ve sus salidas |

## Borrar mi cuenta para siempre (decisión 5)

En la web (Mi cuenta → Privacidad y datos) y en la app (Más). Solo el propietario del centro o el freelance.

1. **Si hay reservas futuras**, no se puede cerrar todavía: se listan, con lo pagado de cada una.
   - **«Cancelar y avisar a todos»** las cancela todas, devuelve el 100 % de lo pagado y avisa a cada buceador por
     email y en la app, en su idioma.
2. **Cerrar mi cuenta** (con la contraseña):
   - la ficha y los servicios dejan de verse y nadie puede reservar;
   - todo el equipo sale de la sesión; el personal ya no ve los datos del centro;
   - el propietario puede seguir entrando para ver su historial y descargar sus datos, pero no puede cambiar nada.
3. **Durante 6 meses** (183 días): al entrar, «Tu cuenta está cerrada… La guardamos hasta el …» y **«Reabrir mi
   cuenta»**, que lo devuelve todo tal como estaba (ficha, servicios, experiencias, equipo).
4. **Pasados los 6 meses** se borra todo, con una copia de la base hecha justo antes. **Se guarda por ley**:
   - los pagos y las devoluciones;
   - las fechas e importes de las reservas, **sin** nombres, emails, teléfonos ni notas;
   - los datos fiscales (DAC7);
   - el registro de seguridad, con su propio plazo.

## Lo que la app pide al servidor (nuevo)

| Dirección | Para qué |
|---|---|
| `GET /api/pro/hoy` | «Hoy»: cifras, urgente, salidas de hoy y de mañana, trabajos del freelance |
| `GET /api/pro/agenda?desde=&dias=` | Mes, semana y día (hasta 42 días) |
| `POST /api/pro/escanear` | QR o código de una reserva: marca la llegada como la lista del barco |
| `POST /api/pro/contar` | Contar a bordo (queda en el historial de la salida) |
| `GET /api/bookings/{id}/whatsapp?tipo=reserva\|pago` | Enlace de WhatsApp con el texto en el idioma del cliente (queda registrado como vista de teléfono) |
| `GET /api/manifest/{id}/resumen.pdf`, `POST …/resumen-enlace` | PDF firmado del barco; el enlace vale 10 minutos sin sesión, para abrirlo en el navegador del móvil |
| `GET/POST /api/center/team/roles/…` | Perfiles del centro (solo el propietario) |
| `GET /api/provider/cuenta`, `POST …/cancelar-todo`, `…/cerrar`, `…/reabrir` | Borrar la cuenta (solo el propietario) |

`/api/me` devuelve ahora `permissions`, `member_role_name` y `account_closed`.

## Tabla de estado

| Punto | Estado |
|---|---|
| Hoy, Agenda (mes, semana, día), crear salida con plantilla y repetición | **Nuevo** |
| Escanear (cámara nativa, código escrito, ráfaga, promociones, todos los avisos) | **Nuevo** |
| Solicitudes y Pendientes de pago (aceptar varias, motivos, otra salida, recordar, cobrar en el centro) | **Nuevo** |
| Lista del barco, contar a bordo, resumen y PDF firmado, avisos con deshacer | **Nuevo** |
| Reservas, Nueva reserva, Estadísticas, Cobros, Más con «Disponible en la web» | **Nuevo** |
| Perfiles del equipo editables en la web y aplicados en la app y en el servidor | **Nuevo** |
| Borrar mi cuenta para siempre (web y app), 6 meses, reabrir, borrado con copia previa | **Nuevo** |
| Código de la reserva debajo del QR del buceador (web y app) | **Nuevo** |
| Reserva manual con teléfono: fallaba (el teléfono no se guardaba cifrado) | **Completado** (arreglado) |
| Grupos, barcos y guías: se organizan en la web (dentro de la app) | **Disponible en la web** |
| Cartel de la salida y fotos | **Disponible en la web** |

## Comprobado

| Comprobación | Resultado |
|---|---|
| Pruebas del servidor de perfiles, cierre de cuenta, Hoy, escáner, contar, WhatsApp, PDF, reserva manual, push (`tests/test_v50_49_pro.py`) | 13 de 13 |
| Recorrido en navegador del Centro PRO, instructor, freelance, en/fr, 360 px y cerrar la cuenta (`tests/navegador/e2e_app_pro.py`) | 63 de 63 |
| Todas las pruebas del servidor | Correctas (ver notas de la v50.49) |
| APK y emulador Android con `centro.prueba` e `instructor.prueba` | Ver notas de la v50.49 |

## Limitaciones conocidas

1. **El PDF del barco en el móvil** se abre en el navegador del teléfono con un enlace que caduca a los 10 minutos
   (el navegador no tiene la sesión de la app).
2. **Grupos y guías** se reparten en la web; la app los enseña y pasa lista por grupos.
3. **Cobrar con el móvil (Tap to Pay)** sigue para una versión futura (decisión 8 de la Tanda 0).
