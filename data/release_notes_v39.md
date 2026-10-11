# WORLDIVES DISCOVERY · v39

## Corrección crítica de reservas para perfiles no profesionales

- El catálogo de puntos asociados a un centro ya puede consultarse desde el flujo de reserva por usuarios `recreational` y `freelance` autenticados.
- Los usuarios `center` siguen viendo únicamente los puntos de su propio centro.
- El administrador puede consultar cualquier centro.
- Se valida que el centro solicitado esté activo antes de devolver sus puntos.
- El formulario de reserva carga puntos y actividades de forma independiente: si falla una fuente de catálogo, la otra sigue disponible y el error no bloquea toda la reserva.
- Se mantiene la misma lógica de plazas, salidas, pagos, solicitudes y permisos de la v38.
