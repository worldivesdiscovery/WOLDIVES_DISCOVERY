# WORLDIVES DISCOVERY v50.57 · Velocidad de la portada (revisión general 5.4)

Objetivo del encargo: **la portada con Lighthouse de 85 o más en móvil y la primera imagen visible en menos de 2,5 s
en 4G**. El vídeo de cabecera no se hace (3.2, decisión del titular): la portada se mide con su foto fija.

## Cómo se mide

- **Lighthouse 12.8.2**, perfil móvil de serie (Moto G Power: pantalla de 412 × 823, 4G lento simulado con 150 ms de
  latencia y 1,6 Mbit/s, procesador 4 veces más lento), sin extensiones y con Chromium en modo sin pantalla.
- Sobre una copia de la demo servida en **modo producción** (sin la franja de «Versión de demostración»), en este
  equipo. La v50.56 se mide igual, desde su propia copia del código.
- La portada, ⟪VECES⟫ pasadas (sus cifras cambian de una pasada a otra; se da la mediana y todas las pasadas); las
  demás páginas, ⟪VECES_OTRAS⟫.
- Además, en un navegador real con 4G lento y el procesador 4 veces más lento (`tests/navegador/e2e_v50_57_portada.py`):
  la foto de la cabecera en menos de 2,5 s y sin saltos.

## Resultado de la portada

⟪PORTADA⟫

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

⟪TABLA⟫

## Cómo repetirlo

```bash
# Lighthouse 12 (npm) con Chromium, perfil móvil (el de serie), contra la web en modo producción
lighthouse http://127.0.0.1:<puerto>/ --only-categories=performance,accessibility,best-practices,seo
python3 tests/navegador/e2e_v50_57_portada.py      # la portada en un navegador real, también con 4G lento
```
