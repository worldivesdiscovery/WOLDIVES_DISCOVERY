# WORLDIVES DISCOVERY v50.43: capas del mapa «Mapa», «Satélite» y «Relieve» (Fase 1C, puntos 9 y 10)

## Revisión del encargo
Se ha vuelto a pegar el encargo completo (auditoría v50.29, fases 1 a 8). Todo lo anterior está entregado en las versiones v50.31 a v50.38, y el encargo 2 en las v50.39 a v50.42: **Ya estaba**, no se ha rehecho. Lo único nuevo son los puntos 9 y 10 de la Fase 1C, que entrega esta versión.

## Qué había antes
- **Botones:** los mapas de la portada y de Explorar tenían cuatro: «Mapa», «Satélite», «Relieve marino» y «Mundo».
  - **«Mundo»** no era otra vista, sino el mismo mapa alejado hasta ver el mundo entero. Por eso se quita sin perder nada.
  - **«Satélite»** desaparecía sin explicación cuando no había clave de ArcGIS.
- **El relieve de GEBCO no se veía:**
  - la capa se pedía **transparente** y, al elegirla, se quitaba el mapa de debajo, así que quedaba un fondo vacío;
  - la atribución era la de 2024.
- **La ficha del punto, los editores y «Elegir en el mapa»** no tenían selector de capas.

## 9 · Capa «Relieve» (batimetría GEBCO)
- **Nombre exacto de la capa:** `GEBCO_LATEST`. Para la versión en color, `WOD_GEBCO_LAYER=GEBCO_LATEST_2` en el `.env`; cualquier otro valor se ignora.
- **Se ve:** la capa es **opaca y va sola** (`transparent:false`), porque la cuadrícula de GEBCO ya incluye la tierra. Se pide como WMS 1.3.0 en EPSG:3857.
- **La política de seguridad del navegador (CSP) no la bloqueaba:** permite imágenes de `https:`. Está comprobado con una prueba.
- **Si GEBCO no responde,** el mapa vuelve a «Mapa», sale el aviso «Relieve no disponible ahora» y el botón queda desactivado hasta recargar.
- **Atribución exacta** con la capa activa: «Imagery reproduced from the GEBCO_2026 Grid, GEBCO Compilation Group (2026) GEBCO 2026 Grid».
- **Aviso de GEBCO:**
  - en el mapa, con la capa activa: «Relieve orientativo (GEBCO). No sirve para navegar ni para la seguridad en el mar», con enlace a «Seguridad en el buceo»;
  - en el botón, al pasar el ratón: «Relieve del fondo marino (GEBCO): orientativo, no apto para la navegación»;
  - en el documento **«Seguridad en el buceo»**, apartado nuevo «Mapas y relieve del fondo marino», en los 10 idiomas. Se publica solo como versión nueva al arrancar, salvo que la administración haya editado ese documento: en ese caso hay que añadir el apartado a mano desde *Administración → Legal*.

## 10 · Selector de capas
- **Botones:** «Mapa», «Satélite» y «Relieve», en ese orden y con icono. Por defecto, «Mapa».
- **Es el mismo selector en todos los mapas:**
  - portada y Explorar (arriba a la izquierda, como antes);
  - ficha del punto, editor de puntos, editor de centros y «Elegir en el mapa» del Top 10 (versión compacta, arriba a la derecha).
- **Recuerda la última capa elegida** en el dispositivo y la usa en todos los mapas. Si no se puede guardar, empieza en «Mapa».
- **«Satélite»:**
  - **con `ARCGIS_API_KEY`** en el `.env`: Esri World Imagery a través de nuestro servidor, con el límite mensual de la Fase 5.10 (*Administración → Mapas*);
  - **sin clave** (o con el límite del mes alcanzado): el botón se ve **desactivado** con «Disponible próximamente»;
  - en *Administración* aparece el aviso «Añade la clave de ArcGIS para activar el satélite», con enlace a *Mapas*. El mismo aviso sale en *Mapas*;
  - **nunca** se usa el servidor público de Esri sin clave. La clave no llega al navegador (comprobado en la prueba).
- **Accesibilidad y móvil:**
  - el grupo tiene la etiqueta «Capas del mapa» y cada botón dice si está activo;
  - los botones desactivados lo indican;
  - en el móvil los tres botones caben en la pantalla, sin desplazamiento.
- **Textos nuevos en los 10 idiomas** (12 textos y 1 patrón).

## Migración
- Ninguna: esta versión no cambia la base de datos.
- **Variable nueva y opcional en `.env.example`:** `WOD_GEBCO_LAYER`.

## Estado

| Punto | Estado |
|---|---|
| 9. Relieve GEBCO visible, con el nombre exacto de la capa (y `GEBCO_LATEST_2` opcional) | Completado |
| 9. CSP comprobada y capa visible (opaca, sola) | Completado (la CSP ya lo permitía; la causa era la transparencia) |
| 9. Aviso «Relieve no disponible ahora» si GEBCO falla | Nuevo |
| 9. Atribución exacta 2026 | Completado |
| 9. Aviso de GEBCO en «Seguridad en el buceo» y en el mapa | Nuevo |
| 9. Prueba en un navegador real con GEBCO de verdad | Pendiente (ver abajo) |
| 10. «Mapa», «Satélite», «Relieve» en ese orden; sin «Mundo» | Completado |
| 10. «Satélite» con clave, o desactivado con «Disponible próximamente»; aviso en Administración | Completado |
| 10. Mismo selector en todos los mapas y 10 idiomas | Nuevo |
| 10. Recordar la última capa; «Mapa» por defecto | Nuevo |

## Pendiente
- **Probar GEBCO de verdad.** El servidor de pruebas no tiene acceso a internet (la red bloquea `wms.gebco.net`), así que en las pruebas GEBCO, el mapa base y Esri están **simulados**. Las peticiones son las mismas que en la web real; solo cambian las imágenes. Para comprobarlo en tu equipo:
  1. abre la web y elige «Relieve»;
  2. si no se ve, abre la consola con F12 → *Red* y busca `wms.gebco.net`;
  3. si quieres la versión en color, pon `WOD_GEBCO_LAYER=GEBCO_LATEST_2` y reinicia.
- **Clave de ArcGIS:** hasta que la pongas en el `.env`, «Satélite» se verá desactivado («Disponible próximamente»).

## Pendiente de decisión
- **Versión del relieve por defecto:** sombreada (`GEBCO_LATEST`, la de ahora) o en color (`GEBCO_LATEST_2`).

## Para el abogado
- Nada nuevo. El aviso de GEBCO («no apto para la navegación») reproduce la condición de uso de GEBCO; solo conviene que lo lea junto con el resto de «Seguridad en el buceo».

## Cómo se probó
- **`tests/test_v50_43_layers.py`, 6 pruebas:**
  - configuración con `GEBCO_LATEST` y la atribución exacta;
  - `GEBCO_LATEST_2` con la variable y valores extraños ignorados;
  - satélite desactivado sin clave, sin rastro de Esri y con su ruta en 404;
  - CSP que permite las imágenes de GEBCO;
  - aviso en «Seguridad en el buceo» en los 10 idiomas (archivo y API);
  - sin «Mundo» y con el mismo selector en todos los mapas.
- **`tests/e2e_layers.py`, 68/68 en Chromium, en ordenador y en móvil, en la portada y en Explorar:**
  - orden de los botones, «Mapa» por defecto y «Satélite» desactivado sin clave;
  - «Relieve»: parámetros exactos de la petición WMS, teselas cargadas, sin el mapa debajo, atribución 2026 y aviso con enlace;
  - última capa recordada entre páginas y selector en la ficha del punto;
  - GEBCO caído: vuelve a «Mapa» con el aviso;
  - inglés, alemán y chino;
  - aviso en Administración y en *Mapas*;
  - **con clave:** satélite por nuestro servidor, nada pedido a Esri desde el navegador, la clave nunca en la página y teselas contadas;
  - sin errores de JavaScript ni desbordamiento.
- **Batería completa:** 170 pruebas de servidor correctas; `e2e_walk.py` sin errores; `e2e_legal_catalog.py` 33/33; `e2e_centers.py` 32/32.
- **Capturas** de las tres capas en la portada, Explorar y la ficha del punto, en ordenador y en móvil, además de «Relieve no disponible ahora» y *Administración → Mapas* sin clave: `docs/capturas/fase-1c-capas/`. Las imágenes de los mapas son simuladas.
