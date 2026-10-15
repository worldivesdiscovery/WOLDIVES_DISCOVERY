# WORLDIVES DISCOVERY v50.57 · Revisión de todos los botones (revisión general 2.2)

Fecha: 15/10/2026. Herramienta: `tests/navegador/inventario_botones.py` (Chromium real, escritorio 1366 × 900, es-ES),
la misma de la auditoría de la v50.51, ampliada en esta versión (abajo). El detalle pantalla por pantalla y elemento
por elemento está en `botones-inventario.md` (en el paquete DEMO y en el repositorio; no va en el de PRODUCCIÓN
porque nombra las cuentas de la demo).

## Cómo se ha probado

- Seis papeles, cada uno con su propio servidor y una copia nueva de la base de la demo: las cuatro cuentas de prueba
  (**buceador**, **centro**, **instructor del centro** y **freelance**), la **administración** y el **visitante** sin
  sesión.
- Se abren todas las pantallas a las que llega cada papel (siguiendo enlaces, pestañas, subpestañas y, desde esta
  versión, los formularios de «nuevo» y «editar» que se abren con un botón) y se pulsa **cada** enlace, botón,
  desplegable y formulario por separado, sobre la pantalla recién abierta. Los formularios se envían **vacíos** (lo
  que peor se suele tratar). Las confirmaciones se cancelan; «Cerrar sesión», «Borrar mi cuenta» y parecidos se
  prueban al final y solo hasta la confirmación.
- Resultado de cada elemento:
  - **Funciona**: hace algo visible (cambia de pantalla, abre una ventana, avisa, valida, guarda…) sin errores.
  - **Depende de clave pendiente**: la propia web dice que falta configurar un servicio externo (Stripe, satélite,
    WhatsApp, correo). Se activa al poner la clave en el `.env` del servidor y reiniciar.
  - **Desactivado (correcto)**: desactivado a propósito y la pantalla dice por qué.
  - **Fallo corregido**: estaba mal en esta revisión y está arreglado en la v50.57 (abajo).
- Sin claves externas y sin salida a internet: así se ve exactamente qué depende de cada clave.

## Resumen

⟪TABLA⟫

**Cada botón: «Funciona» o «fallo corregido».** No queda ningún «Error», «Sin efecto» ni «Desactivado sin
explicación». Los elementos que la herramienta marcó «No probado» están probados aparte, uno a uno (abajo).

## Fallos encontrados y corregidos

| # | Dónde | Qué pasaba | Arreglo | Estado |
|---|---|---|---|---|
| 1 | Administración › *Plantillas de servicios* | «Subir» en la primera plantilla y «Bajar» en la última **no hacían nada** («Sin efecto») | Salen apagadas y, al pasar el ratón, dicen por qué («Ya es la primera: no se puede subir más»), en los 9 idiomas; se recolocan al mover una tarjeta (con las flechas o arrastrando). Las demás flechas guardan el orden («Orden guardado») | **Fallo corregido** (repetido con la herramienta: 0 «Sin efecto») |
| 2 | Centro y freelance › *Reservas* (encontrado en la auditoría de los cuatro modos, 5.1) | La hora y el número de cada reserva salían cortados («0…», «#1…»); entre 761 y 1180 px no se veía el estado de la reserva y en el móvil se cortaban el cliente y el estado | Ver `modos.md` | **Fallo corregido** |

## Con especial atención: Administración › Destinos, Puntos y Plantillas

⟪ESPECIAL⟫

## «No probado» por la herramienta: probados aparte

Todos están en el mapa del buceo (`#/explorar`): grupos de puntos («2», «3»), algún punto suelto y el enlace
«Seguridad en el buceo» de la nota de «Relieve». No es un fallo de la web: con varios navegadores a la vez, la
animación del mapa pasó de los 10 s que espera la herramienta, o el mapa ya se había movido por una prueba anterior.
Los mismos elementos salieron «Funciona» con otras cuentas en la misma pasada. Se han probado uno a uno, cada uno con
la pantalla recién abierta, en `tests/navegador/e2e_v50_57_explorar.py` (**17/17**): los grupos «2», «3», «5» y «9» se
abren al pulsarlos (el mapa se acerca), cada punto abre su ficha lateral con su nombre y «×» la cierra, «Ver ficha del
punto» lleva a su ficha y, con «Relieve», sale la nota «No sirve para navegar…» y «Seguridad en el buceo» abre esa
página (se ve al bajar y nada lo tapa). El mapa es el mismo para todos los papeles.

## Depende de una clave pendiente

Todo lo de esta lista **funciona** en cuanto se pone la clave en el `.env` del servidor y se reinicia; hasta entonces
la web lo dice con un aviso claro, no da error. Cada clave aparece en *Administración → Operación → Estado del
sistema*.

| Clave pendiente | Botones afectados |
|---|---|
| **ArcGIS** (`ARCGIS_API_KEY`) | «Satélite» en la portada, el mapa del buceo y la ficha de cada punto (todos los papeles): desactivado con «Disponible próximamente» |
| **Stripe** (`STRIPE_SECRET_KEY` y los dos webhooks) | Centro › *Cobros y pagos*: «Abrir mi panel de Stripe» y «Actualizar estado». Freelance: «Activar los cobros online». Los servicios con «Pago al reservar» salen como «No admite reservas ahora mismo» |
| **WhatsApp** (Meta) | Centro y freelance › *Avisos y WhatsApp*: «WhatsApp aún no está activado en WORLDIVES» (los avisos salen por correo y en la app) |
| **Correo** (`WOD_SMTP_*`) | Administración › *Operación*: los correos esperan en la cola hasta configurarlo |
| Ciudad aproximada (proxy) | *Mi cuenta*: «La ciudad aproximada aparecerá cuando el servidor la reciba de su proxy» |

Un caso que la herramienta contó en esta lista y que **funciona**: Centro › *Vender en tu web* › «Actualizar» vuelve a
cargar el panel (8 peticiones, todas correctas); lo contó como «depende de clave» porque el panel recargado dice
«Envío pendiente de configurar» de la conexión antigua del centro, que el centro aún no ha configurado.

## Lo que se ha mejorado en la herramienta

- Recorre también los formularios de **«nuevo» y «editar»** que se abren con un botón (por ejemplo
  `#/admin?tab=points&edit=12`): desde la v50.57 (2.1) la edición tiene su propia dirección y antes contaba como la
  lista, así que sus botones no se pulsaban.

## Volver a pasarlo

```bash
python3 tests/navegador/inventario_botones.py --paralelo 3 --salida <carpeta>
# solo algunos papeles:            --roles admin,centro
# rehacer el informe sin recorrer:  --solo-informe --trabajo <carpeta de trabajo>
python3 tests/navegador/e2e_v50_57_explorar.py      # el mapa del buceo, elemento a elemento
```

Tarda unos 50 minutos con 3 papeles a la vez. No va en el paquete de PRODUCCIÓN (usa las cuentas de la demo).
