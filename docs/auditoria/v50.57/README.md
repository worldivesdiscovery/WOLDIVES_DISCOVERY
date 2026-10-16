# WORLDIVES DISCOVERY v50.57 · Auditoría de la revisión general (15/10/2026)

Lo que pedían los bloques 2.2 y 5 de la «Revisión general antes del lanzamiento»: cada botón probado, los cuatro modos
pantalla a pantalla, la prueba de carga y la velocidad de la portada. Todo lo que estaba mal está corregido en esta
versión.

| Parte | Informe | Resultado en una línea |
|---|---|---|
| 2.2 · Todos los botones | [`botones.md`](botones.md) y el detalle en [`botones-inventario.md`](botones-inventario.md) (solo en el paquete DEMO y en el repositorio: nombra las cuentas de la demo) | 369 pantallas y 5.880 elementos con seis papeles: 0 «Error», 0 «Sin efecto», 0 desactivados sin explicación; cuatro fallos encontrados y corregidos |
| 5.1 · Los cuatro modos | [`modos.md`](modos.md), con capturas en `docs/capturas/v50.57/modos/` | ⟪MODOS⟫ |
| 5.2 y 5.3 · Carga y SQLite | [`carga.md`](carga.md) | 300 personas y 20 reservas por segundo: páginas p95 16 ms, reservas p95 110 ms, 0 errores en 74.913 peticiones y ninguna sobreventa. SQLite aguanta sin errores hasta 60 reservas por segundo (el triple): PostgreSQL no hace falta |
| 5.4 · Velocidad de la portada | [`lighthouse.md`](lighthouse.md) | Portada en el móvil: Lighthouse 66 → 95 (pedido: 85) y la foto de la cabecera de 6,3 s a 2,2 s en 4G (pedido: menos de 2,5 s) |

Cómo repetir cada parte: al final de cada informe.
