# WORLDIVES DISCOVERY v50.58 · Velocidad con el código final (revisión y usabilidad, parte 7)

La parte 7 pide repetir con el código final la medida de la v50.57 (`docs/auditoria/v50.57/lighthouse.md`). El objetivo
sigue siendo el mismo: **la portada con Lighthouse de 85 o más en el móvil, y la primera imagen visible en menos de
2,5 s en 4G**.

## Cómo se mide

Igual que en la v50.57:
- **Lighthouse 12.8.2**, con el perfil móvil de serie: Moto G Power, pantalla de 412 × 823, 4G lento simulado (150 ms
  de latencia y 1,6 Mbit/s) y procesador 4 veces más lento. Sin extensiones y con Chromium en modo sin pantalla.
- Sobre una copia de la demo servida en **modo producción**, sin la franja de «Versión de demostración», en este equipo.
- La portada se pasa 5 veces y las demás páginas 3 veces cada una. Se da la mediana, y entre paréntesis todas las
  pasadas.
- Las cifras cambian de un día a otro en este equipo: el código de la v50.57 dio 95 en la portada el 16/10 y da 97 el
  17/10. Por eso **la v50.57 se ha vuelto a medir hoy**, desde su código final (el último commit de la v50.57),
  justo antes de la v50.58 final. La comparación es entre esas dos medidas.
- Se han hecho dos parejas de medidas, v50.57 y v50.58 una detrás de otra. La primera, con un código de la v50.57 de
  unas horas antes de su entrega. La segunda, que es la que se da abajo, con los dos códigos finales. Las dos parejas
  dicen lo mismo, con diferencias de 1 o 2 puntos.

## Resultado de la portada

**Objetivo cumplido: 96 en el móvil (pedido: 85 o más) y la foto de la cabecera a los 2,3 s (pedido: menos de 2,5 s).**

| Portada (móvil, 4G lento) | v50.57 (código final, medida el 17/10) | v50.58 (código final) |
|---|---|---|
| **Rendimiento** | 97 (97 · 98 · 97 · 96 · 96) | **96** (97 · 98 · 95 · 96 · 96) |
| **Primera imagen** (LCP: la foto de la cabecera) | 2,3 s (2,3 · 1,8 · 2,3 · 2,3 · 1,8) | **2,3 s** (2,3 · 2,0 · 2,4 · 2,3 · 2,3) |
| Primer contenido (FCP) | 1,2 s | 1,2 s |
| Tiempo bloqueado (TBT) | 134 ms | 151 ms |
| Saltos al cargar (CLS) | 0,007 | 0,007 |
| Índice de velocidad | 1,7 s | 1,4 s |
| Peso total | 805 KB | 911 KB |
| Accesibilidad · Buenas prácticas · SEO | 100 · 100 · 100 | 100 · 100 · 100 |

En la portada, el programa principal empieza a bajar cuando la foto de la cabecera ya está pintada (lo hizo la
v50.57). Por eso los 106 KB de más no retrasan la foto: 2,3 s en las dos versiones.

## Todas las páginas públicas

Rendimiento en el móvil, mediana de 3 pasadas (la portada, de 5), y entre paréntesis la primera imagen (LCP).

| Página | v50.57 (código final, 17/10) | v50.58 (código final) | Cambio |
|---|---|---|---|
| Portada | 97 (2,3 s) | **96 (2,3 s)** | −1 |
| Puntos de buceo | 80 (4,8 s) | 78 (5,3 s) | −2 |
| Ficha de un punto | 67 (6,3 s) | 69 (6,3 s) | +2 |
| Centros | 79 (5,1 s) | 76 (5,7 s) | −3 |
| Ficha de un centro | 68 (5,4 s) | 65 (6,0 s) | −3 |
| Tipos de buceo | 75 (6,3 s) | 74 (6,4 s) | −1 |
| Top 10 | 73 (5,2 s) | 70 (5,8 s) | −3 |
| Experiencias | 80 (5,0 s) | 76 (5,6 s) | −4 |

- **Accesibilidad, buenas prácticas y SEO**, en todas las páginas: 98 o 100, 100 y 100.
- **La ficha de un punto** sube 2 puntos. Su mapa se carga ahora al acercarse a él (encargo de los vídeos), y el
  rendimiento no espera a sus mosaicos. Su nota de buenas prácticas pasa de 96 a 100, pero eso es de este equipo: el
  96 venía de errores en la consola al pedir los mosaicos del mapa, que aquí no llegan porque no hay internet. En la
  v50.58 Lighthouse ya no los pide. Con internet, las dos versiones darían 100.
- **Las demás páginas pierden entre 1 y 4 puntos**, y su primera imagen llega entre 0,1 y 0,6 s más tarde. En la
  mayoría, las pasadas de las dos versiones no se solapan, así que no es solo el ruido de este equipo.
- **Top 10**: los saltos al cargar (CLS) dan 0,042 o 0,074 según la pasada, en las dos versiones (la v50.57 también
  dio 0,074 en una). Depende del momento en que carga cada cosa, no del código, y queda por debajo de 0,1, el límite
  de «bueno».

## Por qué las demás páginas van algo más lentas

Fuera de la portada, la cabecera de cada página la dibuja el programa principal. Su primera imagen espera, por tanto, a
que ese programa baje y arranque. Y el programa ha crecido con todo lo nuevo de esta versión: el asistente de servicios,
el progreso del curso, el alquiler de equipo, el equipo con QR, la reserva exprés, los vídeos de los usuarios, el panel
con menú lateral y la foto por tipo.

| Archivo | v50.57 | v50.58 | Cambio |
|---|---|---|---|
| Programa principal (`world-dives-v8.js`), comprimido | 346 KB | 416 KB | +70 KB (+20 %) |
| Paquete de idioma (inglés, el de Lighthouse), comprimido | 160 KB | 183 KB | +23 KB |
| Hoja de estilos, comprimida | 74 KB | 87 KB | +12 KB |

Con 1,6 Mbit/s, 70 KB son unos 0,35 s de descarga, y el procesador lento tarda algo más en leer el programa. Cuadra con
los 0,5 a 0,6 s de más que se ven en la primera imagen de la mayoría de las páginas.

## Mejora propuesta (no hecha en esta versión)

Buena parte del programa principal solo se usa en los paneles de la administración, el centro y el freelance, pero
también lo descarga quien solo mira puntos o centros. Separar el código de los paneles en un archivo aparte, que solo
se baje al entrar en un panel, aligeraría todas las páginas públicas.

Es un cambio grande en el programa principal: casi 1,5 MB sin comprimir y muchas funciones compartidas. No se ha hecho
en la entrega de esta versión para no arriesgar lo que ya está probado. El encargo pedía la portada, y la portada
cumple con margen (96).

## Comprobado también en un navegador real

`tests/navegador/e2e_v50_57_portada.py` abre la portada en Chromium con 4G lento y el procesador 4 veces más lento.
Comprueba la foto de la cabecera en menos de 2,5 s y sin saltos. Va en la batería del navegador de esta versión (notas
de la versión, «Todas las pruebas»).


## Cómo repetirlo

```bash
# Lighthouse 12 (npm) con Chromium, perfil móvil (el de serie), contra la web en modo producción
lighthouse http://127.0.0.1:<puerto>/ --only-categories=performance,accessibility,best-practices,seo
python3 tests/navegador/e2e_v50_57_portada.py      # la portada en un navegador real, también con 4G lento
```
