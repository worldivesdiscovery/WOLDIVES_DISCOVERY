# WORLDIVES DISCOVERY v50.58 · Todos los botones con el código final (revisión y usabilidad, parte 7)

Fecha: 17/10/2026. Herramienta: `tests/navegador/inventario_botones.py` en Chromium real (escritorio 1366 × 900,
es-ES). Es la misma de la v50.57 (`docs/auditoria/v50.57/botones.md`), con las mismas reglas y sin rebajar ninguna
comprobación. El detalle pantalla por pantalla y elemento por elemento está en `botones-inventario.md`. Ese archivo va
en el paquete DEMO y en el repositorio, pero no en el de PRODUCCIÓN, porque nombra las cuentas de la demo.

## Cómo se ha probado

Igual que en la v50.57:
- Seis papeles: **visitante** sin sesión, **buceador**, **centro**, **instructor del centro**, **freelance** y
  **administración**. Cada papel tiene su propio servidor y una copia nueva de la base de la demo.
- Se abre cada pantalla a la que llega cada papel: pestañas, subpestañas y los formularios de «nuevo» y «editar».
- En cada pantalla se pulsa **cada** enlace, botón, desplegable y formulario por separado, sobre la pantalla recién
  abierta:
  - los formularios se envían vacíos;
  - las confirmaciones se cancelan;
  - «Cerrar sesión», «Borrar mi cuenta» y parecidos se prueban al final y solo hasta la confirmación.
- No hay claves externas ni salida a internet. Así se ve exactamente qué depende de cada clave.

Esta versión trae pantallas nuevas y todas se recorren:
- el menú lateral del panel (2.4);
- el asistente de servicios (parte 3);
- el progreso del curso (3.5);
- «Reservas desde tu web e Instagram» (parte 5);
- «Equipo de alquiler»;
- el equipo con QR;
- los vídeos de los puntos;
- la foto por tipo de buceo (6.4).

Por eso hay 31 pantallas y 308 elementos más que en la v50.57.

## Resumen (recorrido final, 17/10/2026)

| Papel | Pantallas | Elementos | Funciona | Depende de clave pendiente | Desactivado (correcto) | Sin efecto | Error | Desactivado (sin explicación) | No probado |
|---|---:|---:|---:|---:|---:|---:|---:|---:|---:|
| Visitante (sin sesión) | 35 | 731 | 719 | 3 | 5 | 0 | 0 | 0 | 4 |
| Buceador | 51 | 897 | 885 | 3 | 5 | 0 | 0 | 0 | 4 |
| Centro (propietario) | 89 | 1.237 | 1.218 | 7 | 8 | 0 | 0 | 0 | 4 |
| Instructor del centro | 76 | 1.085 | 1.069 | 4 | 8 | 0 | 0 | 0 | 4 |
| Freelance | 70 | 1.019 | 1.004 | 4 | 7 | 0 | 0 | 0 | 4 |
| Administración | 79 | 1.219 | 1.200 | 6 | 9 | 0 | 0 | 0 | 4 |
| **Total** | **400** | **6.188** | **6.095** | **27** | **42** | **0** | **0** | **0** | **24** |

Ninguna pantalla da error al abrirse. **Cada botón da «Funciona» o es un fallo ya corregido.** No queda ningún
«Error», ningún «Sin efecto» y ningún «Desactivado sin explicación». Los recuentos:
- **24 «No probado»**: los mismos cuatro elementos del mapa del buceo que en la v50.57. Están probados aparte (abajo).
- **27 «Depende de clave pendiente»**: repasados uno por uno (abajo).
- **42 «Desactivado (correcto)»**: repasados uno por uno (abajo).

## Fallos encontrados y corregidos

La primera pasada completa, con el código de antes de este arreglo, dio **3 «Sin efecto»** y **79 «No probado»**:

| # | Dónde | Qué pasaba | Arreglo | Estado |
|---|---|---|---|---|
| 1 | Menú lateral del panel (2.4): centro y su instructor › «OPERACIONES ▾»; freelance › «MI ACTIVIDAD ▾» | En el grupo de la sección abierta, el título del grupo **no plegaba** el grupo: no pasaba nada al pulsarlo. Los demás grupos sí se plegaban | El grupo de la sección abierta se pliega y se despliega como los demás. Al cambiar de sección, el grupo de la sección nueva se abre una sola vez y después se puede plegar (`wdPanelBind` en `world-dives-v8.js`) | **Fallo corregido.** Repetido con la herramienta: 0 «Sin efecto». `e2e_v50_56_panel.py` lo comprueba: 37/37 |
| 2 | La propia herramienta | Los 55 «No probado» de más (79 en lugar de 24) eran botones de grupos del menú plegados en una pasada anterior. El menú recuerda en el navegador qué grupos tiene plegados cada panel, así que esos botones ya no se veían al volver a abrir la pantalla | La herramienta borra lo que recuerda el menú (`wd-panel:*`) al abrir cada pantalla y así parte siempre del menú tal como lo ve quien entra por primera vez | **Corregido en la herramienta.** Repetido: 24 «No probado», los del mapa, como en la v50.57 |

En el recorrido final:
- los tres títulos del fallo n.º 1 dan **«Funciona»** («Cambia su estado: aria-expanded true → false»);
- los botones que antes quedaban sin probar se pulsan todos.

Después del recorrido final se corrigieron dos fallos de maquetación que salieron al mirar las capturas (`modos.md`):
- los botones de las reservas tapaban el canal y el estado;
- el menú plegado a iconos tenía separadores de 42 px.

Ninguno de los dos cambia lo que hace un botón. Están comprobados con sus pruebas y con la batería completa del
navegador (notas de la versión, «Todas las pruebas»).

## «No probado» por la herramienta: probados aparte

Son los mismos 24 que en la v50.57: cuatro elementos del mapa del buceo (`#/explorar`) en cada uno de los seis papeles.
- Los grupos de puntos «2» y «3»: con tres navegadores a la vez, el mapa tarda más de 10 s en terminar de moverse.
- «Costa del Sol, Málaga» y el enlace «Seguridad en el buceo»: al volver a abrir la pantalla ya no estaban donde la
  herramienta los vio. El mapa no siempre abre con la misma vista, y la nota solo sale con «Relieve».

Se prueban uno a uno en `tests/navegador/e2e_v50_57_explorar.py`, con el código final: **22/22**. La prueba comprueba
que:
- los grupos se abren al pulsarlos;
- cada punto abre su ficha lateral;
- «Costa del Sol, Málaga» se encuentra con «Filtrar puntos del mapa»;
- con «Relieve», «Seguridad en el buceo» abre su página.

El mapa es el mismo para todos los papeles, así que se prueba sin sesión.

## Depende de una clave pendiente (27)

Funcionan en cuanto se pone la clave en el `.env` del servidor y se reinicia. Hasta entonces, la web lo dice con un
aviso claro y no da error.

| Clave pendiente | Elementos | Cuáles |
|---|---:|---|
| **ArcGIS** (`ARCGIS_API_KEY`) | 23 | «Satélite» en la portada, el mapa del buceo y la ficha del punto (6 papeles × 3 = 18), y en el mapa de los formularios de punto (4) y de centro (1). Sale desactivado con «Disponible próximamente» |
| **Stripe** (`STRIPE_SECRET_KEY` y los dos webhooks) | 3 | Centro › *Cobros y pagos*: «Abrir mi panel de Stripe» y «Actualizar estado». Freelance › *Cobros*: «Activar los cobros online». Los tres avisan «Los cobros online todavía no están activados en WORLDIVES…» |
| Contado aquí, pero **funciona** | 1 | Centro › «Reservas desde tu web e Instagram» › «Actualizar» |

Sobre el último elemento: «Actualizar» vuelve a cargar el panel sin errores. La herramienta lo cuenta como «depende de
clave» porque el panel enseña «Sin configurar» en la conexión antigua. Es una opción del centro, que este centro de la
demo no usa, no una clave del servidor. Pasaba igual en la v50.57.

## Desactivado (correcto): los 42, uno por uno

| Dónde | Elemento | Papeles | Por qué está desactivado (lo dice la pantalla) |
|---|---|---:|---|
| *Reservar* (centro de la demo) | «Bautizo de buceo» e «Inmersión simple en barco» | 6 × 2 | «No admite reservas ahora mismo»: usan «Pago al reservar» y faltan las claves de Stripe |
| *Reservar* | «Elige una actividad» (el botón para seguir) | 6 | Su propio texto dice lo que falta: elegir antes la actividad |
| *Reservar* | «Una persona menos» | 6 | Ya está en el mínimo (una persona) |
| *Reservar* | «Una persona más» | 6 | Atenuado hasta elegir la actividad: «Elige primero la actividad» |
| *Recompensas* | «Canjear» (2 recompensas) | 4 × 2 | Faltan puntos: «Te faltan 150 puntos» |
| Centro › *Equipo* | «Perfil de …» en la fila de la propietaria | 1 | Es su propia fila: nadie se cambia su propio perfil |
| Instructor › *Avisos y WhatsApp* | «Hora del recordatorio» y el resto de los ajustes | 1 | Su perfil no tiene permiso de avisos: «Tu perfil no permite cancelar salidas ni avisar a todos los clientes. Pídeselo al propietario del centro.» Es el arreglo n.º 4 de la v50.57, que `e2e_v50_57_modos.py` sigue comprobando |
| Administración › *Plantillas de servicios* | «Subir» en la primera, «Bajar» en la última | 2 | «Ya es la primera: no se puede subir más» / «Ya es la última: no se puede bajar más» |

Hay dos menos que en la v50.57. Era «Guardar cambios» de los precios de alquiler en *Servicios* del centro y del
instructor, que salía apagado hasta cambiar algo. Desde el encargo de alquiler de equipo, esos precios están en
*Servicios › Equipo de alquiler › Piezas y precios*, y en esa pantalla todos los botones dan «Funciona».

## Volver a pasarlo

```bash
python3 tests/navegador/inventario_botones.py --paralelo 3 --salida <carpeta>
# solo algunos papeles:            --roles admin,centro
# rehacer el informe sin recorrer:  --solo-informe --trabajo <carpeta de trabajo>
python3 tests/navegador/e2e_v50_57_explorar.py      # el mapa del buceo, elemento a elemento
python3 tests/navegador/e2e_v50_56_panel.py         # el menú lateral del panel, plegar y desplegar
```

Tarda unos 47 minutos con 3 papeles a la vez (el recorrido final: 2.799 s). No va en el paquete de PRODUCCIÓN, porque
usa las cuentas de la demo.
