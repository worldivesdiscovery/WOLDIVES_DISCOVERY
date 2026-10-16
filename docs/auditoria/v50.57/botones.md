# WORLDIVES DISCOVERY v50.57 · Revisión de todos los botones (revisión general 2.2)

Fecha: 15 y 16/10/2026 (recorrido final: 16/10/2026). Herramienta: `tests/navegador/inventario_botones.py` (Chromium real, escritorio 1366 × 900, es-ES),
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

| Papel | Pantallas | Elementos | Funciona | Depende de clave pendiente | Desactivado (correcto) | Sin efecto | Error | Desactivado (sin explicación) | No probado |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Visitante (sin sesión) | 35 | 724 | 712 | 3 | 5 | 0 | 0 | 0 | 4 |
| Buceador | 48 | 869 | 857 | 3 | 5 | 0 | 0 | 0 | 4 |
| Centro (propietario) | 81 | 1.182 | 1.162 | 7 | 9 | 0 | 0 | 0 | 4 |
| Instructor del centro | 68 | 1.025 | 1.008 | 4 | 9 | 0 | 0 | 0 | 4 |
| Freelance | 65 | 988 | 973 | 4 | 7 | 0 | 0 | 0 | 4 |
| Administración | 72 | 1.092 | 1.073 | 6 | 9 | 0 | 0 | 0 | 4 |
| **Total** | **369** | **5.880** | **5.785** | **27** | **44** | **0** | **0** | **0** | **24** |

**Cada botón: «Funciona» o «fallo corregido».** No queda ningún «Error», «Sin efecto» ni «Desactivado sin
explicación». Los 24 que la herramienta marcó «No probado» (cuatro elementos del mapa del buceo, en los seis papeles)
están probados aparte, uno a uno, y al hacerlo apareció el fallo n.º 3. Los 27 «Depende de clave pendiente» y los 44
«Desactivado (correcto)» se han repasado uno por uno (abajo): uno de estos no se explicaba en la pantalla y es el
fallo n.º 4. Los cuatro fallos están corregidos.

## Fallos encontrados y corregidos

| # | Dónde | Qué pasaba | Arreglo | Estado |
|---|---|---|---|---|
| 1 | Administración › *Plantillas de servicios* | «Subir» en la primera plantilla y «Bajar» en la última **no hacían nada** («Sin efecto») | Salen apagadas y, al pasar el ratón, dicen por qué («Ya es la primera: no se puede subir más»), en los 9 idiomas; se recolocan al mover una tarjeta (con las flechas o arrastrando). Las demás flechas guardan el orden («Orden guardado») | **Fallo corregido** (repetido con la herramienta: 0 «Sin efecto») |
| 2 | Centro y freelance › *Reservas* (encontrado en la auditoría de los cuatro modos, 5.1) | La hora y el número de cada reserva salían cortados («0…», «#1…»); entre 761 y 1180 px no se veía el estado de la reserva y en el móvil se cortaban el cliente y el estado | Ver `modos.md` | **Fallo corregido** |
| 3 | Mapa del buceo (`#/explorar`), todos los papeles (encontrado al probar aparte los «No probado») | «Filtrar puntos del mapa» con un texto que deja un solo punto, o varios muy separados («Portofino», «Costa del Sol», «Grenada»…), decía «1 punto en el mapa» y **el mapa salía vacío** | La librería que agrupa los puntos (Leaflet.markercluster 1.5.3) no dibujaba un punto sin otro con el que agruparse cuando el zoom mínimo del mapa no es un número entero, y el de nuestros mapas no lo es (el mundo ajustado a la caja, p. ej. 1,75). Se corrige desde nuestro programa (`wdClusterFix` en `world-dives-v8.js`); el archivo de la librería sigue tal cual se publica | **Fallo corregido** (`e2e_v50_57_explorar.py`: 22/22; con el código anterior, 19/22) |
| 4 | Instructor del centro › *Avisos y WhatsApp* (encontrado al repasar uno a uno los «Desactivado (correcto)») | Su perfil no tiene permiso de avisos y los ajustes de los avisos salían **apagados sin decir por qué**. La herramienta lo contó como «Desactivado (correcto)» por el texto de al lado («Cada buceador elige otra fecha o la devolución»), que no lo explica | El panel dice ahora «Tu perfil no permite cancelar salidas ni avisar a todos los clientes. Pídeselo al propietario del centro.» (el mismo texto que el servidor, ya traducido a los 9 idiomas); el propietario, que sí puede, no lo ve | **Fallo corregido** (`e2e_v50_57_modos.py`; con el código anterior, el aviso no sale) |

El recorrido completo se pasó antes de los arreglos n.º 3 y 4. El n.º 3 solo cambia cómo se dibujan los puntos en los
mapas y el n.º 4 añade un aviso: se han comprobado con sus pruebas y con la batería completa de pruebas en el navegador
(notas de la versión, «Pruebas»).

## Con especial atención: Administración › Destinos, Puntos y Plantillas

Las tres pantallas se recorrieron como el resto (cada botón, sobre la pantalla recién abierta) y, además, en la
auditoría de los cuatro modos (5.1, `modos.md`) se abre uno de cada y se **guarda sin cambios**: las tres vuelven a la
lista con «Guardado», sin errores ni peticiones rechazadas.

| Pantalla | Pantallas recorridas | Elementos | Resultado |
|---|---:|---:|---|
| **Destinos** | 3 (lista, «Nuevo destino», «Editar») | 14 | 14 Funciona |
| **Puntos** | 3 (lista, «Nuevo punto», «Editar») | 45 | 43 Funciona · 2 Depende de clave pendiente («Satélite») |
| **Plantillas** | 1 (lista con sus ventanas) | 15 | 13 Funciona · 2 Desactivado (correcto): el fallo n.º 1, corregido |

- **Destinos.** «Nuevo destino» y «Editar» abren el formulario con su propia dirección (`&edit=nuevo`, `&edit=7`).
  Enviado vacío, el navegador no lo deja pasar y señala «Nombre del destino» (obligatorio). «← Volver», las migas
  («Centro de control › Destinos») y «Cancelar» vuelven a la lista.
- **Puntos.** «Nuevo punto» y «Editar» (292 puntos: se prueban dos, el resto es el mismo botón) abren el formulario
  con su dirección. Vacío, señala «Nombre». Los desplegables (país, tipo, dificultad, centro asociado y orientación de
  titulación) se aplican al pulsar «Guardar punto». En el mapa del formulario, mover el marcador cambia la latitud y la
  longitud; funcionan el zoom, «Mapa» y «Relieve» (con su nota y el enlace «Seguridad en el buceo»). «Mejor época»
  guarda («Condiciones guardadas.»), «Vídeos de la ruta» pide el enlace y «Subir fotografía» pide el archivo.
  «Satélite» sale desactivado con «Disponible próximamente» hasta poner `ARCGIS_API_KEY`.
- **Plantillas.** «+ Nueva plantilla», «Editar», «Archivar» y «Borrar» abren su ventana (las dos últimas, una
  confirmación con el nombre de la plantilla); «Guardar intensidad» avisa «Intensidad guardada.»; cada flecha ↑/↓
  mueve la tarjeta y avisa «Orden guardado.». «Subir» en la primera y «Bajar» en la última salen apagadas y dicen por
  qué (era el fallo n.º 1). La prueba de los modos comprueba también las flechas después de mover una tarjeta.

## «No probado» por la herramienta: probados aparte

Son los mismos cuatro elementos del mapa del buceo (`#/explorar`) en los seis papeles (4 × 6 = 24): los grupos de
puntos «2» y «3», el punto «Costa del Sol, Málaga» y el enlace «Seguridad en el buceo» de la nota de «Relieve».

- Los grupos: la herramienta espera 10 s a que el mapa termine de moverse y, con tres navegadores a la vez, la
  animación tardó más.
- «Costa del Sol, Málaga» y «Seguridad en el buceo»: al volver a abrir la pantalla para pulsarlos ya no estaban donde
  la herramienta los vio (el mapa no siempre abre con la misma vista y la nota solo sale con «Relieve»). El mismo
  enlace «Seguridad en el buceo» sí se pulsó, y funciona, en el mapa del formulario de puntos de la administración.

Se han probado uno a uno, cada uno con la pantalla recién abierta, en `tests/navegador/e2e_v50_57_explorar.py`
(**22/22**): los grupos «2», «3», «5» y «9» se abren al pulsarlos (el mapa se acerca); cada punto abre su ficha lateral
con su nombre y «×» la cierra; «Ver ficha del punto» lleva a su ficha; «Costa del Sol, Málaga», buscado con «Filtrar
puntos del mapa» como lo haría una persona, abre su ficha lateral; y, con «Relieve», sale la nota «No sirve para
navegar…» y «Seguridad en el buceo» abre esa página (se ve al bajar y nada lo tapa). El mapa es el mismo para todos los
papeles, así que se prueba sin sesión.

Al buscar «Costa del Sol» apareció el **fallo n.º 3** (arriba): el filtro decía «1 punto en el mapa» y el mapa salía
vacío. Está corregido, y la prueba comprueba ahora también «Andalucía» (varios puntos), «Portofino» y «Grenada» (uno
solo) y que al borrar el filtro vuelven todos.

## Depende de una clave pendiente

Todo lo de esta lista **funciona** en cuanto se pone la clave en el `.env` del servidor y se reinicia; hasta entonces
la web lo dice con un aviso claro, no da error. Cada clave aparece en *Administración → Operación → Estado del
sistema*.

| Clave pendiente | Elementos | Cuáles |
|---|---:|---|
| **ArcGIS** (`ARCGIS_API_KEY`) | 23 | «Satélite» en la portada, el mapa del buceo y la ficha de cada punto (los seis papeles), y en el mapa de los formularios de punto y de centro: desactivado con «Disponible próximamente» |
| **Stripe** (`STRIPE_SECRET_KEY` y los dos webhooks) | 3 | Centro › *Cobros y pagos*: «Abrir mi panel de Stripe» y «Actualizar estado» avisan «Los cobros online todavía no están activados en WORLDIVES (el administrador debe configurar la clave de Stripe en el servidor)». Freelance › *Cobros*: «Activar los cobros online», con el mismo aviso |
| Contado aquí, pero **funciona** | 1 | Centro › *Vender en tu web* › «Actualizar» (abajo) |

Centro › *Vender en tu web* › «Actualizar» vuelve a cargar el panel (9 peticiones, todas correctas). La herramienta lo
contó como «depende de clave» porque el panel recargado enseña «● Sin configurar» en la «Conexión antigua» (el canal
«Importada»): es una opción del centro, que este centro de la demo no usa, no una clave del servidor.

Sin ser botones, estas pantallas también avisan de una clave pendiente (lo mismo: se activa al poner la clave):

| Clave pendiente | Dónde lo dice la pantalla |
|---|---|
| **Stripe** | Centro e instructor › *Servicios*: «2 servicios no se pueden reservar. Usan «Pago al reservar» y los cobros online no están activos…»; al reservar, esos servicios salen «No admite reservas ahora mismo» (abajo). Freelance › *Cobros*: «● Cobros sin configurar» |
| **WhatsApp** (Meta) | Centro, instructor y freelance › *Avisos y WhatsApp*: «WhatsApp aún no está activado en WORLDIVES. Mientras tanto, los avisos salen por correo y en la app» |
| **Correo** (`WOD_SMTP_*`) | Administración › *Operación*: «Sin WOD_SMTP_HOST: los correos esperan en la cola (72 h) hasta configurar el proveedor» |
| **ArcGIS** | Administración › *Mapas* y *Operación*: «Añade la clave de ArcGIS para activar el satélite» |
| Ciudad aproximada (la pasa el proxy) | *Mi cuenta* (los cinco papeles con sesión): «La ciudad aproximada aparecerá cuando el servidor la reciba de su proxy» |

## Desactivado (correcto): los 44, uno por uno

| Dónde | Elemento | Papeles | Por qué está desactivado (lo dice la pantalla) |
|---|---|---:|---|
| *Reservar* (centro de la demo) | «Bautizo de buceo» e «Inmersión simple en barco» | 6 × 2 | «No admite reservas ahora mismo»: usan «Pago al reservar» y faltan las claves de Stripe (arriba) |
| *Reservar* | «Elige una actividad» (el botón para seguir) | 6 | Su propio texto dice lo que falta: elegir antes la actividad |
| *Reservar* | «Una persona menos» | 6 | Ya está en el mínimo (una persona) |
| *Reservar* | «Una persona más» | 6 | Atenuado hasta elegir la actividad: «Elige primero la actividad» |
| *Recompensas* | «Canjear» (2 recompensas) | 4 × 2 | Faltan puntos: «Te faltan 150 puntos» (centro, instructor, freelance y administración tienen pocos puntos en la demo) |
| Centro e instructor › *Servicios* | «Guardar cambios» | 2 | Se enciende al cambiar algo |
| Centro › *Equipo* | «Perfil de …» en la fila de quien ha entrado (la propietaria) | 1 | Es su propia fila (pone «Tú»): nadie se cambia su propio perfil |
| Instructor › *Avisos y WhatsApp* | «Hora del recordatorio» (y el resto de los ajustes) | 1 | Su perfil no tiene permiso de avisos. No lo decía: **fallo n.º 4, corregido** |
| Administración › *Plantillas* | «Subir» en la primera, «Bajar» en la última | 2 | «Ya es la primera: no se puede subir más» / «Ya es la última: no se puede bajar más» (fallo n.º 1, corregido) |

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

Tarda unos 40 minutos con 3 papeles a la vez (el recorrido final: 2.407 s). No va en el paquete de PRODUCCIÓN (usa las cuentas de la demo).
