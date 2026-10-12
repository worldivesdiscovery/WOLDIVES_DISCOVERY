# WORLDIVES DISCOVERY · Cuentas de prueba

> **Solo para el entorno de pruebas** (zip `-pruebas`, puerto 8100). Estas cuentas **no existen** en la base de
> producción, y este archivo no va en el zip de producción. El servidor se niega a arrancar en modo pruebas con la
> dirección del dominio real.

## Cómo arrancar

| Sistema | Orden |
|---|---|
| Windows | doble clic en `scripts\start_pruebas.bat` |
| Mac / Linux | `./scripts/start_pruebas.sh` |

Abre **http://127.0.0.1:8100**. Arriba verás la banda «Entorno de pruebas». La primera vez (y si los datos tienen más
de 7 días) se crean solos los datos de demostración, con fechas a partir de hoy.

## Cuentas

Todas tienen la misma contraseña: **`Worldives-Prueba-2026`**

| Papel | Usuario | Email | Qué tiene |
|---|---|---|---|
| Administración | `admin.prueba` | admin@example.com | Sin verificación en dos pasos (solo en pruebas). Una denuncia, una experiencia para revisar y un centro pendiente de aprobar. |
| Centro | `centro.prueba` | centro@example.com | «Centro de Buceo Pruebas» (Xàbia) con logo, 2 servicios (uno bajo petición y otro de pago al reservar), salidas este mes y el que viene, 2 barcos, política de cancelación (48 h, 50 %) y la experiencia «Fin de semana en las Medas». |
| Freelance | `freelance.prueba` | freelance@example.com | Servicio «Cenotes con guía, por días» (día completo y medio día, descuento desde 3 días, extra de fotos), días ocupados, un bloque de vacaciones, un vida a bordo publicado y otra experiencia pendiente de revisar. |
| Buceador | `buzo.prueba` | buzo@example.com | Perfil completo y reservas en todos los estados: solicitada, confirmada, aceptada pendiente de pago, pagada, cancelada, rechazada, caducada y completada. Log Book con 3 inmersiones. |
| Buceadores 2 a 6 | `buzo2.prueba` … `buzo6.prueba` | buzo2@example.com … buzo6@example.com | Reservas confirmadas en salidas del centro (para ver el manifiesto lleno) y reservas por días con el freelance. |

Hay además una cuenta `pendiente.prueba` (pendiente@example.com) que ha pedido alta como centro y espera la aprobación.

## Qué probar en 5 minutos

1. Entra como `buzo.prueba` → **Mi área → Mis reservas** (pestañas «Próximas» e «Historial»): verás cada estado con su texto.
2. Entra como `centro.prueba` → **Reservas**: acepta la solicitada; abre **Planning** y el **manifiesto** de la salida de pasado mañana (ya tiene buceadores).
3. Entra como `freelance.prueba` → **Agenda**: días ocupados, medio día y vacaciones.
4. Entra como `admin.prueba` → **Experiencias**, **Verificaciones** (alta de centro pendiente) y las denuncias.

## Correos y pagos

- **Correos:** no se envía ninguno. Se guardan como archivos `.eml` en `data/pruebas/correos/` (se abren con
  Outlook, Thunderbird o Mail).
- **Pagos:** sin claves, el pago online aparece desactivado. Para probar Stripe pon en `.env` solo claves de **modo
  test** (`sk_test_…`). El entorno de pruebas se niega a arrancar con una clave real (`sk_live_…`).
  Tarjeta de prueba de Stripe: `4242 4242 4242 4242`, cualquier fecha futura y cualquier CVC.

## Volver a empezar

- Con el servidor en marcha: **Administración → Operación → «Restaurar demo»**.
- Con el servidor parado: `scripts\reset_demo.bat` (Windows) o `./scripts/reset_demo.sh` (Mac / Linux).

Los dos borran lo que hayas cambiado en pruebas y vuelven a crear las cuentas y los datos con fechas a partir de hoy.
