# WORLDIVES DISCOVERY v50.51 · Inventario de botones

Fecha: 13/10/2026. Herramienta: `tests/navegador/inventario_botones.py` (Chromium real, escritorio 1366×900, es-ES).
Inventario completo, pantalla por pantalla y elemento por elemento: `botones-inventario.md` (en el paquete DEMO y en
el repositorio; no va en el de PRODUCCIÓN porque nombra las cuentas de la demo).

## Cómo se ha probado

- Seis papeles, cada uno con su propio servidor y una copia nueva de la base de demostración (con las cuentas de
  `CUENTAS-DEMO.txt`): **visitante**, **buceador**, **centro propietario**, **instructor del centro**, **freelance** y
  **administración**.
- Se abren todas las pantallas a las que llega cada papel (siguiendo enlaces y pestañas, como una persona) y se pulsa
  **cada** enlace, botón, desplegable y formulario por separado, sobre la pantalla recién abierta. Los formularios se
  envían **vacíos** (lo que peor se suele tratar). Las confirmaciones se cancelan; «Cerrar sesión», «Borrar mi cuenta»
  y «Restaurar demo» se prueban al final y solo hasta la confirmación.
- Resultado de cada elemento:
  - **Funciona**: hace algo visible (cambia de pantalla, abre una ventana, avisa, valida…) sin errores.
  - **Depende de clave pendiente**: la propia web dice que falta configurar un servicio (Stripe, correo, WhatsApp,
    satélite…). Se activa al poner la clave en el `.env` y reiniciar.
  - **Corregido**: estaba mal en esta auditoría y está arreglado en la v50.51 (abajo).
  - **Desactivado (correcto)**: desactivado a propósito con un texto que explica por qué.
- Sin claves externas y sin salida a internet: así se ve exactamente qué depende de cada clave.

## Resumen

| Papel | Pantallas | Elementos | Funciona | Depende de clave pendiente | Desactivado (correcto) | Error | Sin efecto |
|---|---:|---:|---:|---:|---:|---:|---:|
| Visitante (sin sesión) | 34 | 632 | 624 | 3 | 5 | 0 | 0 |
| Buceador | 47 | 762 | 754 | 3 | 5 | 0 | 0 |
| Centro propietario | 75 | 1.006 | 991 | 5 | 10 | 0 | 0 |
| Instructor del centro | 66 | 930 | 917 | 3 | 10 | 0 | 0 |
| Freelance | 61 | 843 | 831 | 4 | 8 | 0 | 0 |
| Administración | 62 | 892 | 881 | 3 | 8 | 0 | 0 |
| **Total** | **345** | **5.065** | **4.998** | **21** | **46** | **0** | **0** |

**Antes de los arreglos** (primera pasada, misma herramienta): 23 «Error», 17 «Sin efecto» y 2 pantallas que no se
abrían; el instructor solo llegaba a 36 pantallas porque su panel no abría. **Después: 0, 0 y 0**, y el instructor
recorre sus 66 pantallas. Los elementos que estaban mal salen ahora como «Funciona» en el inventario completo; aquí
abajo están marcados como **Corregido**.

## Lo que estaba mal y está corregido

| # | Dónde | Qué pasaba | Arreglo | Estado |
|---|---|---|---|---|
| 1 | **Instructor** (y cualquier perfil del equipo sin «Estadísticas»): *Mi centro*, *Abrir el panel*, *Panel del centro*, *Gestionar mi plan* | El panel del centro **no se abría**: «No se ha podido abrir esta sección». El panel pedía las estadísticas y el servidor, con razón, se las negaba | El panel se abre sin estadísticas cuando el perfil no las tiene (o el plan no las incluye); el servidor sigue negándolas | **Corregido** |
| 2 | Centro y freelance › *Servicios y tarifas* › *Próximas salidas* | Pulsar una salida («Mié, 14 oct 16:00 · 6 libres») **no hacía nada**: buscaba el servicio con el número de la salida | Busca el servicio de la salida | **Corregido** |
| 3 | Ficha del punto › *Ubicación* (todos) | En el mapa pequeño, el «+» del zoom quedaba debajo de la barra Mapa/Satélite/Relieve, y la nota de GEBCO tapaba el punto | El zoom va abajo a la izquierda (con los créditos del mapa a su derecha, sin taparlo) y la nota de «Relieve» va debajo del mapa | **Corregido** |
| 4 | Portada › *Buscar* con la caja vacía (todos) | No hacía nada | Dice «Escribe al menos dos letras» y deja el cursor en la caja | **Corregido** |
| 5 | *¿Te apetece bucear?* (`#/top10`) enviado vacío (todos) | No hacía nada | El navegador pide rellenar la caja | **Corregido** |
| 6 | Centro › *Recompensas* › *Validar un código* vacío | No hacía nada | El navegador pide el código | **Corregido** |
| 7 | Administración › *Actividad* | Los detalles salían como texto técnico: `{"from": "confirmed", "to": "completed", "reason": null}` | Se leen así: «de Confirmada a Completada», sin los valores vacíos | **Corregido** |
| 8 | Detalle de cada reserva (buceador) | Pedía siempre la «salida cancelada» aunque no la hubiera, y el navegador mostraba un error en rojo en la consola | Solo la pide cuando hay una salida cancelada pendiente de elegir | **Corregido** |
| 9 | Instructor › *Resumen* del panel | Salía «Cobrado 34.573,44 €» y, al pulsarlo, intentaba abrir las estadísticas, que su perfil no permite; también los gráficos de ventas, vacíos | El resumen solo enseña los accesos a pestañas que ese perfil tiene, y los gráficos de ventas solo con «Estadísticas» | **Corregido** |
| 10 | Mapa del buceo (`#/explorar`) | El inventario vio un grupo de puntos («2») «debajo» del panel lateral | Comprobado con una captura: el grupo está fuera del área visible del mapa, recortado por su borde; nadie lo ve ni lo pulsa. Al mover el mapa aparece y se puede pulsar. El inventario ya no cuenta como «tapado» lo que está recortado | **No es un fallo** |

## Depende de una clave pendiente

Todo lo de esta lista **funciona** en cuanto se pone la clave en el `.env` y se reinicia; hasta entonces la web lo
dice con un aviso claro, no da error. Cada clave aparece en *Administración → Operación → Estado del sistema*.

| Clave pendiente | Botones afectados |
|---|---|
| **ArcGIS** (`ARCGIS_API_KEY`) | «Satélite» en la portada, el mapa del buceo y la ficha de cada punto (todos los papeles): desactivado con «Disponible próximamente» |
| **Stripe** (`STRIPE_SECRET_KEY` y los dos webhooks) | Centro › *Cobros y pagos*: «Abrir mi panel de Stripe» y «Actualizar estado». Freelance: «Activar los cobros online». Los servicios con «Pago al reservar» salen como «No admite reservas ahora mismo». Administración › *Pagos* y *Operación* lo indican |
| **Correo** (`WOD_SMTP_*`) | Administración › *Correos*: «Envío pendiente de configurar» (los correos se guardan, no se pierden) |
| **WhatsApp** (Meta) | Centro y freelance › *Avisos y WhatsApp*: «WhatsApp aún no está activado en WORLDIVES» (los avisos salen por la app y el correo) |
| Avisos en el móvil (Firebase) | Ningún botón de la web depende de esta clave |

## Volver a pasarlo

```bash
python3 tests/navegador/inventario_botones.py --paralelo 4 --salida <carpeta>
# solo algunos papeles:            --roles instructor,centro
# con una base de demo ya creada:  --demo <base.sqlite3>
```

Tarda unos 30 minutos con 4 papeles a la vez. No va en el paquete de PRODUCCIÓN (usa las cuentas de la demo).
