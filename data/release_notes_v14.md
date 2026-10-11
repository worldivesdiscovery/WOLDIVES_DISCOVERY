# WORLDIVES DISCOVERY v14 — Backtest y estabilidad

- Corregida la migración de `user_profiles` para instalaciones existentes: fecha de nacimiento, contacto de emergencia y preferencias/equipo.
- Corregidos endpoints GET de recompensas/ofertas y verificaciones de centros usados por el panel de administración.
- El saldo económico del monedero ya no se genera automáticamente por actividad del usuario.
- Las ofertas monetarias sin centro asociado quedan desactivadas; los beneficios económicos deben pertenecer a un centro participante.
- Añadido flujo de saldo promocional concedido por administrador/centro, con control de que un centro solo pueda concederlo a clientes vinculados o con reserva.
- Manteniendo puntos, centros, tipos de buceo, cuentas, logbook, recompensas y monedero.

## Backtest realizado

- Sintaxis Python y JavaScript: OK.
- Salud de API y catálogo: OK.
- 283 puntos activos verificados en la base de distribución.
- Fichas de punto y centro: OK.
- Filtros semánticos de tipos de buceo: OK en pruebas HTTP.
- Inicio de sesión, cuenta y persistencia del perfil: OK.
- Log Book: alta y lectura: OK.
- Recompensas y monedero: lectura, concesión patrocinada y canje: OK.
- Registro y verificación de centro: OK.
- Gestión de recompensas de centro: OK.
- QR y check-in: OK.
- Reservas y estados de reserva: OK en pruebas de API.
- Experiencias/destinos/recorridos virtuales: endpoints principales compilados y probados en entorno de backtest.

Nota: el backtest es de API, rutas y lógica de cliente; antes de un lanzamiento público debe hacerse una prueba manual en navegador real y una revisión de seguridad/privacidad/producción.
