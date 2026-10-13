# WORLDIVES DISCOVERY v50.51 · Informe de auditoría

Auditoría del 13/10/2026: carga con 10.000 usuarios, seguridad y botones. Todo lo que estaba mal está corregido en
esta versión salvo lo marcado como **Pendiente de decisión**.

| Parte | Informe | Resultado en una línea |
|---|---|---|
| Carga | [`carga.md`](carga.md), con gráficos | En un equipo de 4 núcleos, 1.000 usuarios a la vez con páginas p95 33 ms y reservas p95 210 ms. Para 10.000: VPS de 32 vCPU (uso intenso) u 8 vCPU (normal); SQLite basta. 4 errores de concurrencia corregidos |
| Seguridad (OWASP Top 10) | [`seguridad.md`](seguridad.md) | 15 hallazgos (3 de gravedad media) y 3 menores: **todos corregidos**. 49 pruebas automáticas |
| Botones por pantalla y papel | [`botones.md`](botones.md) y el detalle en [`botones-inventario.md`](botones-inventario.md) (solo en el paquete DEMO y en el repositorio: nombra las cuentas de la demo) | 5.065 elementos en 345 pantallas y 6 papeles: 4.998 «Funciona», 21 «Depende de clave pendiente», 46 desactivados a propósito con explicación, **0 errores**. 9 fallos corregidos |

## Lista de correcciones

**Carga e integridad de las reservas**
- Doble envío de una reserva (doble clic o reintento): ya no crea dos reservas ni toma el doble de plazas.
- Doble «Aceptar» de una solicitud: ya no descuenta las plazas dos veces (también el cobro en el mostrador).
- Pago confirmado a la vez por varias vías: se cuenta una sola vez.
- Cambiar la capacidad de una salida mientras alguien reserva: sin plazas vendidas de más.
- Conexiones a la base de datos reutilizadas: cada página cuesta de 2 a 5 veces menos CPU.
- Inicios de sesión en avalancha: ya no frenan el resto de la web (límite común para todos los procesos; a 1.000
  usuarios, páginas de 2 s a 33 ms).
- Índices nuevos para el inicio de sesión y «Salidas cercanas».

**Seguridad**
- Permisos del equipo: recepción ya no cambia la ficha del centro y un instructor no ve los ingresos.
- Límite de intentos por cuenta (fuerza bruta desde muchas IP) y por «contraseña actual».
- Copias de seguridad cifradas (`WOD_BACKUP_KEY`); secretos de la verificación en dos pasos cifrados.
- Fotos públicas sin datos de ubicación (EXIF/GPS).
- Títulos escapados, denuncias sin enlaces `javascript:`, errores internos que ya no se envían, cabecera `Server`
  sin versión, tokens ocultos en los registros, contraseñas del equipo con la misma política que el registro.
- Versiones mínimas de Pillow y cryptography sin fallos conocidos.

**Botones**
- El instructor (y cualquier perfil del equipo sin «Estadísticas») no podía abrir el panel del centro.
- Las salidas de *Servicios y tarifas* no se abrían al pulsarlas (centro y freelance).
- Mapa pequeño de la ficha del punto: el zoom quedaba tapado y la nota de GEBCO tapaba el punto.
- «Buscar», «¿Te apetece bucear?» y «Validar un código» no hacían nada al enviarse vacíos.
- *Administración → Actividad* mostraba los detalles como texto técnico.
- El detalle de cada reserva pedía una «salida cancelada» inexistente (error en la consola).
- El resumen del instructor enseñaba lo cobrado y un acceso a las estadísticas, que su perfil no permite.

## Cómo repetirlo

| Parte | Orden |
|---|---|
| Carga | `python3 tests/carga/medir.py --dir <carpeta> --arrancar --workers 4 --pasos 100,250,500,1000` (base con `tests/carga/preparar.py construir`); informe con `tests/carga/informe.py` |
| Concurrencia (reservas dobles, plazas) | `python3 -m pytest tests/test_v50_51_concurrencia.py` |
| Seguridad | `python3 -m pytest tests/test_v50_51_seguridad.py tests/test_v50_51.py` |
| Botones | `python3 tests/navegador/inventario_botones.py --paralelo 4 --salida <carpeta>` |

Las herramientas de carga y de botones usan las cuentas de la demo y no van en el paquete de PRODUCCIÓN.
