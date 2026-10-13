# App móvil en 3 módulos · Tanda 3 (v50.49)

Encargo «App móvil en 3 módulos (Buceador, Centro PRO y Freelance PRO) y APK de pruebas».

La Tanda 3 entrega el módulo **Freelance PRO**. Va en la misma versión que las Tandas 2 y 4 (v50.49), por decisión del
titular del 13/10: se prueba todo junto.

El freelance usa las mismas pantallas que el centro (`tanda-2.md`), con lo suyo:

| Pantalla | Qué tiene de freelance |
|---|---|
| **Hoy** | **Trabajos de hoy**: las reservas por días o medio día de hoy (cliente, servicio, personas, punto) con **Llamar**, **WhatsApp** (en el idioma del cliente) y **Cómo llegar** (al punto de buceo, si la reserva lo tiene). Debajo, sus salidas de hoy y «Mañana» plegado con los trabajos de mañana. |
| **Agenda** | En el mes, los días bloqueados se ven rayados. **Bloquear un día con un toque**: todo el día, solo la mañana o solo la tarde, con una nota que solo ve él. **Desbloquear**. |
| **Solicitudes** | Las mismas que el centro, también las de días y medio día. |
| **Escanear** | Igual que el centro: QR o código de la reserva. |
| **Más** | Horario y días de cierre, ficha pública, servicios y precios, herramientas (calendario iCal, cartel, exportar), plan: **disponible en la web**, dentro de la app. Cobros y estadísticas. **Borrar mi cuenta para siempre**. |

Un freelance es siempre su propio propietario: tiene todos los permisos y no tiene equipo.

## Tabla de estado

| Punto | Estado |
|---|---|
| Hoy con los trabajos de hoy y Llamar · WhatsApp · Cómo llegar | **Nuevo** |
| Agenda con días bloqueados y bloquear o desbloquear con un toque (día, mañana, tarde) | **Nuevo** |
| Solicitudes, Escanear, Reservas, Estadísticas y Cobros | **Nuevo** (las mismas del centro) |
| Horario semanal, días de cierre y calendario iCal | **Disponible en la web** (dentro de la app) |
| Borrar mi cuenta para siempre, con 6 meses para volver | **Nuevo** |
| Nueva reserva por teléfono | **Pendiente**: hoy el servidor solo la tiene para centros (`/api/center/bookings/manual`). Se puede añadir para freelance si lo quieres |

## Comprobado

En el recorrido en navegador (`tests/navegador/e2e_app_pro.py`):
- las pestañas del freelance;
- bloquear un día con un toque (queda rayado en el mes);
- el trabajo de hoy con Llamar, WhatsApp y Cómo llegar;
- su perfil público desaparece al cerrar la cuenta y vuelve al reabrirla (`tests/test_v50_49_pro.py`).
