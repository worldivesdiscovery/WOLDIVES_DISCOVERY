# Mapas: mapa base propio, satélite y batimetría (v50.36)

Los mapas de WORLDIVES ya no usan los servidores públicos de OpenStreetMap ni el servidor de Esri sin clave.

| Capa | De dónde sale | Quién recibe la IP del visitante | Coste |
|---|---|---|---|
| Mapa base (predeterminado) | Archivo PMTiles propio (Protomaps, datos © OpenStreetMap contributors) servido por nuestro servidor | Nadie más | Solo el almacenamiento y el tráfico |
| Satélite (solo si el visitante lo elige) | Esri World Imagery con clave de ArcGIS Location Platform, **a través de nuestro servidor** | Nadie más: Esri solo ve nuestro servidor | Cuota gratuita mensual; límite configurable |
| Batimetría (solo si el visitante lo elige) | WMS de GEBCO, cargado por el navegador | GEBCO / BODC | Gratis |

## 1. Mapa base con Protomaps

1. Instala la herramienta `pmtiles` (binario único): https://github.com/protomaps/go-pmtiles/releases
2. Elige la última compilación diaria del planeta en https://maps.protomaps.com/builds (por ejemplo `20261001.pmtiles`).
3. Extrae solo lo necesario. Los puntos de buceo están en la costa; para verlos bien basta con el nivel 14 (calles y calas), y el mapa se sigue acercando ampliando ese nivel:

   ```bash
   mkdir -p data/tiles
   pmtiles extract https://build.protomaps.com/20261001.pmtiles data/tiles/worldives.pmtiles --maxzoom=14
   pmtiles show data/tiles/worldives.pmtiles     # comprueba el tamaño y los niveles
   ```

   **Tamaño orientativo** (compruébalo con `pmtiles show`, depende de la compilación): el planeta completo hasta el nivel 15 ronda los 120 GB; hasta el nivel 14, aproximadamente la mitad; hasta el 12, unos 15–20 GB. Si el disco es pequeño, empieza con `--maxzoom=12` y pon `WOD_PMTILES_MAXZOOM=12`: el mapa sigue funcionando y la vista satélite da el detalle de la costa.
4. En `.env`: `WOD_PMTILES_URL=/tiles/worldives.pmtiles` y `WOD_PMTILES_MAXZOOM=14` (el nivel que hayas extraído).
5. Reinicia. *Administración → Mapas* muestra el tamaño del archivo.

El servidor entrega el archivo con peticiones de rango HTTP (`Range`), que es como lo lee el navegador. Si hay un proxy delante (Nginx, Caddy), no debe comprimir ni almacenar en búfer `/tiles/`. También puedes alojar el archivo en un almacenamiento con CDN (Cloudflare R2, Bunny, S3) y poner su URL `https://…` en `WOD_PMTILES_URL`; la política de seguridad del navegador (CSP) la permite automáticamente.

**Actualizar cada 3–6 meses:** repite el paso 3 con una compilación nueva en un archivo temporal y sustitúyelo con `mv` (es atómico). No hace falta reiniciar.

**Estilo:** `public/assets/vendor/protomaps-leaflet/wd-flavor.js` (colores de mar y tierra de la web, nombres de lugar en el idioma del visitante).

## 2. Satélite (Esri World Imagery)

1. Crea una cuenta en ArcGIS Location Platform (facturación por teselas, no por sesiones) y una clave de API con el permiso «Basemaps».
2. Ponla en el `.env` del servidor: `ARCGIS_API_KEY=…`. **Nunca se escribe en el código ni en el repositorio.**
3. Reinicia. La capa «Satélite» aparece en los mapas.

El navegador pide `/api/tiles/satellite/z/y/x` y nuestro servidor la pide a Esri con la clave. Así la clave no llega nunca al navegador y el contador es exacto. Cada tesela servida suma 1 en el contador del mes (*Administración → Mapas*). El límite es de 1.900.000 por defecto, por debajo de las 2.000.000 gratuitas. Al llegar al 80 % se avisa por email a los administradores, y al llegar al límite la capa se oculta hasta el mes siguiente. Las teselas no se guardan en el servidor; el navegador las guarda 24 horas.

**Pendiente de confirmar (titular / abogado):** que los términos de ArcGIS Location Platform permiten servir las teselas a través de un servidor propio (proxy). Si no lo permitieran, la alternativa es una clave restringida al dominio, cargada desde el navegador; en ese caso el contador sería aproximado y mandaría el panel de uso de Esri.

**Atribución** (visible cuando la capa está activa): «Powered by Esri | Source: Esri, Maxar, Earthstar Geographics, and the GIS User Community».

## 3. Batimetría GEBCO

Se carga desde `wms.gebco.net` solo si el visitante elige «Relieve marino». Atribución: «GEBCO Compilation Group (2024) GEBCO 2024 Grid». Uso libre con atribución (https://www.gebco.net/data_and_products/gridded_bathymetry_data/).

## 4. Desarrollo

Si no hay archivo PMTiles y `WOD_ENV` no es `production`, los mapas usan los servidores de OpenStreetMap solo para desarrollo. En producción, sin archivo, el mapa se ve sin fondo y el servidor lo avisa al arrancar.
