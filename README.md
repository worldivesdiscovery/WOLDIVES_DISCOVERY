# WORLDIVES DISCOVERY

Plataforma de descubrimiento y reservas de buceo:
- catálogo de puntos y centros con mapa;
- reservas y cobros directos con Stripe Connect (sin comisión por reserva);
- ficha, Log Book y puntos del buceador;
- panel de centros y profesionales con planes;
- administración completa.

**Python 3.11+ con la biblioteca estándar, SQLite y HTML/CSS/JavaScript sin compilar.** Dependencias mínimas en
`requirements.txt` (`stripe`, `qrcode`, `fonttools`, `cryptography` y, desde la v50.50, `Pillow`): el arranque las instala si faltan.

## Arrancar

| Dónde | Qué hacer |
|---|---|
| Windows | Doble clic en `iniciar.bat` |
| Mac o Linux | `./iniciar.sh` |
| Desde otros dispositivos de tu red | `iniciar.bat --red-local` o `./iniciar.sh --red-local` |
| Ver cada petición en la ventana | `--depuracion` |
| Servidor real (VPS) | systemd, HTTPS y copias: `docs/despliegue/README.md` |

Abre `http://localhost:8000`. La primera vez la base de datos se crea sola a partir de `data/seed/catalogo.sqlite3`:
solo el catálogo de puntos, países, tipos, zonas, titulaciones, destinos y textos legales, **sin ninguna cuenta**.

## Crear el administrador (al instalar)

El paquete de producción no trae ninguna cuenta, tampoco de administración. Créala en el servidor, en la carpeta de
la web:

```bash
python app/server.py --create-admin --email tu@dominio.com --username admin --name "Tu Nombre"
```

La contraseña se pide sin mostrarla, y la verificación en dos pasos se activa al entrar por primera vez. Atajo:
`scripts/crear_admin.sh` o `scripts\crear_admin.bat` con los mismos datos.

## Configuración

Copia `.env.example` a `.env` y rellena lo que necesites. Todas las variables vienen vacías y comentadas: vacía
significa «valor por defecto». **Claves y contraseñas solo en el `.env` del servidor**, nunca en el código ni en el
repositorio. Para producción son obligatorias `WOD_ENV=production`, `WOD_PUBLIC_URL` (https), `WOD_SECRET_KEY` y,
desde v50.47, `WOD_DATA_KEY` (cifra los teléfonos y las credenciales de WhatsApp: guarda una copia fuera del servidor).
Los avisos por WhatsApp de cada centro se activan con `WHATSAPP_ENABLED=1` y las claves de la app de Meta; los pasos
están en `docs/notas-de-version/v50.47.md`, apartado «Para el titular».

## Dónde está cada cosa

| Carpeta | Qué hay |
|---|---|
| `app/` | El servidor (`server.py`) y sus módulos por área (`app/wod/`), correos, textos legales y fuentes del PDF |
| `public/` | La web: `index.html`, `js/`, `css/`, `idiomas/` (los 9 idiomas), `img/` (marca, portada, destinos, iconos), `fuentes/`, `lib/` (mapa) |
| `data/seed/` | Datos iniciales: el catálogo de puntos |
| `docs/` | Notas de versión, despliegue, legal, marca, estructura, mapas, pagos y seguridad |
| `scripts/` | Crear el administrador, copias, generar los zips, crear la semilla, herramientas de marca e idiomas y de seguridad (`scripts/seguridad/`) |
| `tests/` | Pruebas automáticas (API y navegador) |

Mientras la web funciona, crea `data/worldivesdiscovery.sqlite3`, `data/subidas/` (fotos de los centros), `storage/`
(documentos privados) y `logs/`. Son datos: no se borran al actualizar y entran en las copias.

## Documentación

| Tema | Dónde |
|---|---|
| Qué cambia en cada versión | `docs/notas-de-version/` (la más reciente: la de número más alto) |
| Despliegue en el VPS, HTTPS, systemd, copias y restauración | `docs/despliegue/README.md` |
| Estructura del proyecto y plan de módulos | `docs/estructura.md` |
| Marca: logo, colores y contraste | `docs/marca/README.md` |
| Pagos con Stripe Connect | `docs/pagos-stripe.md` |
| Mapas | `docs/mapas.md` |
| Estados de una reserva | `docs/estados-reserva.md` |
| Documentos legales, inventario y guías | `docs/legal/` |
| Seguridad | `docs/seguridad.md` |
| Aislamiento entre centros: auditoría, tablas, rutas y fallos | `docs/seguridad/aislamiento-centros.md` |

## Base de datos

SQLite en modo WAL. El esquema está en el código (`BASE_SCHEMA` en `app/server.py`). Las migraciones se aplican solas
al arrancar: solo añaden y transforman, y antes de reescribir datos hacen una copia completa.

## Entregas

Cada versión se entrega en dos zips, que se crean con `python scripts/generar_zips.py` tras una comprobación
automática:
- **`WORLDIVES-vXX.XX-produccion.zip`**, para subirlo tal cual al VPS;
- **`WORLDIVES-vXX.XX-pruebas.zip`**, para probarlo todo en tu ordenador (puerto 8100). Lleva cuentas y datos de demostración, y sus instrucciones en `README-PRUEBAS.md`. Nunca se sube al servidor real.

## Pruebas

Usan el catálogo de demostración, que va en el zip de pruebas: ejecútalas desde ese zip o desde el repositorio.

```bash
cd tests && python -m unittest discover -p 'test_*.py'      # API (siempre sobre una copia de la base)
python tests/navegador/e2e_centers.py                         # navegador (Playwright)
python tests/navegador/e2e_avisos.py                          # recorrido completo con avisos y capturas (v50.47)
python scripts/seguridad/sql_centros.py                       # prueba estática: SQL de datos de centro sin filtro
```
