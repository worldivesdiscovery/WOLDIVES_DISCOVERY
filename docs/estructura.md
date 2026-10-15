# Estructura del proyecto y plan de separación en módulos

## Carpetas (desde v50.46)

```
WORLDIVES/
├── README.md               qué es, cómo arrancar, dónde está cada cosa
├── .env.example            todas las variables, vacías y comentadas
├── requirements.txt        stripe, qrcode, fonttools, cryptography (cifrado de teléfonos, v50.47), Pillow, tzdata (zonas horarias, v50.57)
├── iniciar.bat / iniciar.sh            un solo arranque por sistema (opciones --red-local y --depuracion)
├── iniciar-pruebas.bat / .sh           solo en el zip de pruebas (puerto 8100)
├── app/                    servidor
│   ├── server.py           rutas y lógica que aún no se ha separado
│   ├── wod/                módulos por área (ver abajo)
│   ├── emails/             textos de los correos en los 9 idiomas
│   ├── legal/<idioma>/     textos legales
│   ├── data/               datos comprobados de algunos puntos
│   └── fonts/              tipografías del PDF
├── public/                 web
│   ├── index.html  manifest.webmanifest  sw.js
│   ├── js/  css/
│   ├── idiomas/            las 8 traducciones (el castellano es la base y va en el propio código)
│   ├── img/marca/          los 11 archivos de marca que usa la web (logo, iconos, favicon, redes)
│   ├── img/portada/        cabeceras y fondos
│   ├── img/destinos/       fotos de destinos
│   ├── img/iconos/         imágenes de relleno
│   ├── fuentes/            Inter (carteles)
│   └── lib/                librerías del mapa (Leaflet, agrupación de marcadores, Protomaps)
├── data/seed/              datos iniciales: el catálogo de puntos (lo crea scripts/generar_zips.py)
├── data/demo/              catálogo de demostración para las pruebas (solo en el zip de pruebas)
├── docs/                   notas de versión, despliegue, legal, marca (con el kit en docs/marca/kit/), estructura…
├── scripts/                crear admin, copias, generar zips, crear la semilla, reset_demo, iniciar
│   ├── seguridad/          aislamiento entre centros: prueba estática del SQL, inventario de tablas, recuentos
│   │                       públicos y cambio de la clave de los datos cifrados (v50.47)
│   ├── marca/              generar el logo y sus variantes
│   ├── idiomas/            herramientas de traducción
│   └── herramientas/       prueba de carga y utilidades del catálogo
└── tests/                  pruebas de API y de navegador
```

En ningún zip van:
- `_archivo/` (idiomas, logos, imágenes y arranques retirados);
- `docs/capturas/` (capturas);
- `.github/`;
- lo que la web crea mientras funciona: la base, `data/subidas/`, `storage/`, `logs/` y las copias.

La base de datos **se crea sola en el primer arranque**:
- a partir de `data/seed/catalogo.sqlite3` si existe;
- si no existe y no es producción, a partir del catálogo de demostración;
- con `WOD_EMPTY_DB=1`, empieza vacía.

### Direcciones de la web

Las direcciones son cortas: `/js/`, `/css/`, `/idiomas/`, `/img/…`, `/fuentes/` y `/lib/`. Las antiguas `/assets/…`
redirigen solas a las nuevas (`app/wod/estaticos.py`), así siguen funcionando:
- los correos ya enviados;
- las cachés del navegador;
- los datos guardados antes de v50.46 (que además la migración `migrate_v50_46` actualiza).

Las fotos que suben los centros siguen en `/assets/uploads/…` y se guardan en `data/subidas/`. Una instalación anterior que aún las tenga en `public/assets/uploads/` sigue usando esa carpeta, sin mover nada.

### Reglas de orden

- Ninguna carpeta con más de unos 30 archivos sin agruparlos en subcarpetas con sentido.
- Ningún archivo que no se use.
- Nombres en minúsculas, sin espacios ni «copia».
- Lo que se retira va a `_archivo/`, no se borra.

## Plan de separación en módulos

`app/server.py` (unas 12 000 líneas) y `public/js/world-dives-v8.js` (unas 5 300) siguen siendo grandes.
Se separan **poco a poco, una zona por versión**, sin cambiar el comportamiento. Cada paso:

1. mueve funciones a un módulo nuevo y deja en `server.py` solo la llamada;
2. no cambia rutas, nombres de campos ni textos;
3. pasa la batería completa de pruebas antes de entregar.

### Ya separado (`app/wod/`)

| Módulo | Área |
|---|---|
| `config` | variables del `.env` |
| `security` | contraseñas, tokens y limpieza de datos |
| `totp` | verificación en dos pasos |
| `pdf` | justificantes y fichas en PDF |
| `backup` | copias de seguridad |
| `ops` | salud del servidor y avisos |
| `bookings` | estados de una reserva |
| `manifest` | manifiesto de salida |
| `pointtext` | descripciones de los puntos |
| `agenda` | motor de agenda (v50.44) |
| `money` | importes y monedas para Stripe (v50.45) |
| `formato` | fechas e importes en el idioma de cada persona (v50.46) |
| `estaticos` | direcciones de los archivos de la web (v50.46) |
| **`inquilinos`** | la capa por centro: de qué centro es cada dato, consultas siempre filtradas, 404 (**v50.47**) |
| **`cifrado`** | teléfonos y credenciales cifrados (AES-GCM), huellas para buscar, prefijos E.164 (**v50.47**) |
| **`avisos`** | textos de los avisos masivos en 9 idiomas y enlaces firmados (**v50.47**) |
| **`whatsapp`** | WhatsApp Cloud API de cada centro: alta, plantillas, envío y webhooks (**v50.47**) |

### Siguientes pasos

| Versión | Servidor (`app/wod/…`) | Web (`public/js/…`) |
|---|---|---|
| v50.48 | `payments.py`: Stripe Connect, checkout, webhooks, reembolsos | `wd-pagos.js`: cobros y reembolsos del panel |
| v50.49 | `emails.py`: cola, plantillas, envío SMTP y a archivo | `wd-i18n.js`: traducción del DOM y patrones |
| v50.50 | `catalog.py`: puntos, destinos, mapas | `wd-mapa.js`: mapa, capas y marcadores |
| v50.51 | `providers.py`: centros, freelance, planes, equipo | `wd-panel.js`: panel del centro y del freelance |
| v50.52 | `accounts.py`: registro, sesiones, perfil, privacidad | `wd-cuenta.js`: cuenta, Log Book y puntos |
| v50.53 | `admin.py`: administración, denuncias y contacto | `wd-admin.js`: administración |
| v50.54 | `routes.py`: tabla de rutas en lugar de la cadena de `if path==…` | `wd-app.js`: arranque y rutas |

**Pagos se aplaza de v50.47 a v50.48:** v50.47 es el encargo de avisos masivos y aislamiento entre centros, que ya
cambia reservas, devoluciones y la base de datos; mover a la vez los pagos a otro archivo mezclaría dos cambios
grandes en una entrega. Lo nuevo de v50.47 ya nace separado en módulos (`inquilinos`, `cifrado`, `avisos`, `whatsapp`)
y, al separar `payments.py`, las consultas de pagos pasarán por la capa `inquilinos`.

La web seguirá sin compilación: cada archivo se carga con `<script defer>` en orden y se añade al `sw.js`.
