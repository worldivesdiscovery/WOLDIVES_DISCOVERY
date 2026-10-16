# WORLDIVES DISCOVERY v50.57 · Velocidad de la portada (revisión general 5.4)

Objetivo del encargo: **la portada con Lighthouse de 85 o más en móvil y la primera imagen visible en menos de 2,5 s
en 4G**. El vídeo de cabecera no se hace (3.2, decisión del titular): la portada se mide con su foto fija.

## Cómo se mide

- **Lighthouse 12.8.2**, perfil móvil de serie (Moto G Power: pantalla de 412 × 823, 4G lento simulado con 150 ms de
  latencia y 1,6 Mbit/s, procesador 4 veces más lento), sin extensiones y con Chromium en modo sin pantalla.
- Sobre una copia de la demo servida en **modo producción** (sin la franja de «Versión de demostración»), en este
  equipo. La v50.56 se mide igual, desde su propia copia del código.
- La portada, 5 pasadas (sus cifras cambian de una pasada a otra; se da la mediana y todas las pasadas); las
  demás páginas, 3 cada una (se da la mediana). La v50.56 y la v50.57, una detrás de otra, el 16/10/2026.
- Además, en un navegador real con 4G lento y el procesador 4 veces más lento (`tests/navegador/e2e_v50_57_portada.py`):
  la foto de la cabecera en menos de 2,5 s y sin saltos.

## Resultado de la portada

**Objetivo cumplido: 95 en móvil (pedido: 85 o más) y la foto de la cabecera a los 2,2 s (pedido: menos de 2,5 s).**

| Portada (móvil, 4G lento) | v50.56 | v50.57 |
|---|---|---|
| **Rendimiento** | 66 (65 · 66 · 64 · 67 · 67) | **95** (96 · 96 · 95 · 95 · 94) |
| **Primera imagen** (LCP: la foto de la cabecera) | 6,3 s | **2,2 s** (2,2 · 1,8 · 2,2 · 2,2 · 2,2) |
| Primer contenido (FCP) | 1,1 s | 1,2 s |
| Tiempo bloqueado (TBT) | 445 ms | 207 ms |
| Saltos al cargar (CLS) | 0,007 | 0,007 |
| Índice de velocidad | 1,9 s | 1,4 s |
| Peso total | 866 KB | 803 KB |
| Accesibilidad · Buenas prácticas · SEO | 100 · 96 · 100 | 100 · 100 · 100 |

El primer contenido sale 0,1 s más tarde que en la v50.56 (en todas las páginas: 1,2 s frente a 1,1 s); la foto de la
cabecera, 4,1 s antes.

En un navegador real con 4G lento y el procesador 4 veces más lento (`e2e_v50_57_portada.py`): ⟪E2E⟫

## Qué la frenaba y qué se ha cambiado

La foto de la cabecera ya se pintaba a los 0,26 s en la carga real, pero Lighthouse cuenta como necesario para esa
foto todo lo que empieza a descargarse antes de que aparezca. Y antes de la foto empezaban:

| Qué | Peso | Arreglo |
|---|---|---|
| El programa principal de la web | 355 KB | En la portada empieza cuando el navegador avisa de que la foto ya está pintada (en navegadores sin ese aviso, al terminar de cargar la página; como mucho a los 3 s). En cualquier otra página empieza al momento, con prioridad baja para no quitar sitio a la hoja de estilos |
| El paquete de idioma del visitante (inglés, en Lighthouse) | 165 KB | Igual que el programa principal (antes lo adelantaba el servidor en todas las páginas) |
| El mapa de la portada (Leaflet, el dibujo del mapa) | 90 KB y ~0,3 s de procesador | Se prepara cuando se ve, en cuanto se baja por la página o al «Buscar». En el ordenador, donde se ve al abrir, sale como antes |
| El aviso de arranque (`wd-arranque.js`) | 1 petición antes de la primera pintura | Va escrito dentro de la página (2,9 KB). La política de seguridad lo permite por su huella SHA-256: cualquier otro script escrito en una página se sigue rechazando |
| La foto de la portada en las demás páginas | 27 KB con prioridad alta | Solo se baja en la portada |
| La página sin comprimir | 16 KB | Comprimida (gzip): unos 6 KB |

Además, en **«Experiencias»** la lista de destinos empujaba hacia abajo un recuadro al cargar (CLS 0,393, también en
la v50.56): ahora guarda su sitio mientras carga (CLS 0,03).

## Todas las páginas públicas

Mediana de 3 pasadas (la portada, de 5). Rendimiento en móvil y, entre paréntesis, la primera imagen (LCP).

| Página | v50.56 | v50.57 | Cambio |
|---|---|---|---|
| Portada | 66 (6,3 s) | **95 (2,2 s)** | +29 |
| Puntos de buceo | 79 (4,8 s) | 79 (4,8 s) | = |
| Ficha de un punto | 65 (6,3 s) | 63 (6,6 s) | −2 |
| Centros | 77 (5,1 s) | 76 (5,2 s) | −1 |
| Ficha de un centro | 68 (5,5 s) | 66 (5,5 s) | −2 |
| Tipos de buceo | 76 (5,8 s) | 74 (6,1 s) | −2 |
| Top 10 | 72 (5,2 s) | 73 (5,2 s) | +1 |
| Experiencias | 61 (5,0 s) | **78 (5,1 s)** | +17 (CLS 0,393 → 0,028) |

- **El encargo pedía la portada.** Las demás páginas se pintan con el programa principal y su primera imagen (la foto
  de la cabecera de cada página) llega entre 4,8 y 6,6 s en 4G lento, como en la v50.56. Llevarlas a la cifra de la
  portada sería un trabajo aparte, como el de la portada (dibujar su cabecera sin esperar al programa).
- **Cambios de 1 o 2 puntos**: entran en lo que varía de una pasada a otra salvo en la ficha de un punto, donde las
  pasadas no se solapan (v50.56: 64 · 66 · 65; v50.57: 63 · 62 · 63). El programa principal pesa un 8 % más que en la
  v50.56 (353 KB comprimido frente a 327 KB) por lo nuevo de esta versión.
- **Accesibilidad, buenas prácticas y SEO**, en todas: 98 o 100, 96 o 100 y 100, como en la v50.56.

## Cómo repetirlo

```bash
# Lighthouse 12 (npm) con Chromium, perfil móvil (el de serie), contra la web en modo producción
lighthouse http://127.0.0.1:<puerto>/ --only-categories=performance,accessibility,best-practices,seo
python3 tests/navegador/e2e_v50_57_portada.py      # la portada en un navegador real, también con 4G lento
```
