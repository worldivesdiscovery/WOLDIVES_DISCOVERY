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
  17/10. Por eso **la v50.57 se ha vuelto a medir hoy**, desde su propia copia del código, justo antes de la v50.58. La
  comparación es entre esas dos medidas.

## Resultado de la portada

**Objetivo cumplido: 96 en el móvil (pedido: 85 o más) y la foto de la cabecera a los 2,3 s (pedido: menos de 2,5 s).**

| Portada (móvil, 4G lento) | v50.57 (medida el 17/10) | v50.58 |
|---|---|---|
| **Rendimiento** | 97 (97 · 97 · 98 · 97 · 97) | **96** (96 · 97 · 97 · 95 · 95) |
| **Primera imagen** (LCP: la foto de la cabecera) | 2,2 s | **2,3 s** (las 5 pasadas: 2,3 s) |
| Primer contenido (FCP) | 1,2 s | 1,2 s |
| Tiempo bloqueado (TBT) | 153 ms | 174 ms |
| Saltos al cargar (CLS) | 0,007 | 0,007 |
| Índice de velocidad | 1,4 s | 1,6 s |
| Peso total | 803 KB | 910 KB |
| Accesibilidad · Buenas prácticas · SEO | 100 · 100 · 100 | 100 · 100 · 100 |

En la portada, el programa principal empieza a bajar cuando la foto de la cabecera ya está pintada (lo hizo la
v50.57). Por eso los 107 KB de más casi no tocan la foto: 0,1 s.

## Todas las páginas públicas

Rendimiento en el móvil, mediana de 3 pasadas (la portada, de 5), y entre paréntesis la primera imagen (LCP).

| Página | v50.57 (17/10) | v50.58 | Cambio |
|---|---|---|---|
| Portada | 97 (2,2 s) | **96 (2,3 s)** | −1 |
| Puntos de buceo | 81 (4,8 s) | 79 (5,3 s) | −2 |
| Ficha de un punto | 68 (6,1 s) | 68 (6,3 s) | = (buenas prácticas: 96 → 100) |
| Centros | 79 (5,1 s) | 75 (5,7 s) | −4 |
| Ficha de un centro | 72 (5,3 s) | 69 (5,9 s) | −3 |
| Tipos de buceo | 76 (6,2 s) | 74 (6,6 s) | −2 |
| Top 10 | 76 (5,2 s) | 73 (5,8 s) | −3 |
| Experiencias | 80 (5,0 s) | 77 (5,5 s) | −3 |

- **Accesibilidad, buenas prácticas y SEO**, en todas las páginas: 98 o 100, 100 y 100.
- **Las demás páginas pierden entre 2 y 4 puntos**, y su primera imagen llega entre 0,2 y 0,6 s más tarde. Las
  pasadas de las dos versiones no se solapan, así que no es solo el ruido de este equipo.

## Por qué las demás páginas van algo más lentas

Fuera de la portada, la cabecera de cada página la dibuja el programa principal. Su primera imagen espera, por tanto, a
que ese programa baje y arranque. Y el programa ha crecido con todo lo nuevo de esta versión: el asistente de servicios,
el progreso del curso, el alquiler de equipo, el equipo con QR, la reserva exprés, los vídeos de los usuarios, el panel
con menú lateral y la foto por tipo.

| Archivo | v50.57 | v50.58 | Cambio |
|---|---|---|---|
| Programa principal (`world-dives-v8.js`), comprimido | 345 KB | 416 KB | +71 KB (+20 %) |
| Paquete de idioma (inglés, el de Lighthouse), comprimido | 160 KB | 183 KB | +23 KB |
| Hoja de estilos, comprimida | 74 KB | 87 KB | +13 KB |

Con 1,6 Mbit/s, 71 KB son unos 0,35 s de descarga, y el procesador lento tarda algo más en leer el programa. Cuadra con
los 0,4 a 0,6 s de más que se ven en la primera imagen.

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

Nota: esta medida se hizo antes de los dos últimos arreglos de maquetación de la auditoría (las reservas y el menú
plegado, en `modos.md`). Esos arreglos solo añaden unos 600 bytes a la hoja de estilos y no cambian lo que se descarga
en estas páginas.

## Cómo repetirlo

```bash
# Lighthouse 12 (npm) con Chromium, perfil móvil (el de serie), contra la web en modo producción
lighthouse http://127.0.0.1:<puerto>/ --only-categories=performance,accessibility,best-practices,seo
python3 tests/navegador/e2e_v50_57_portada.py      # la portada en un navegador real, también con 4G lento
```
