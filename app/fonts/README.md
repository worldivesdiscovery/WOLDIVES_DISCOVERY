# Fuentes de los PDF

Los justificantes y fichas en PDF incrustan estas fuentes para escribir bien en los 10 idiomas de la web
(latín con acentos y letras polacas, cirílico y chino simplificado).

| Archivo | Origen | Contenido |
|---|---|---|
| `NotoSans-Regular.ttf`, `NotoSans-Bold.ttf` | Google Fonts, `ofl/notosans/NotoSans[wdth,wght].ttf` (instancias 400 y 700, anchura 100) | Latín, latín extendido, griego, cirílico, signos y monedas |
| `NotoSansSC-Regular.ttf`, `NotoSansSC-Bold.ttf` | Google Fonts, `ofl/notosanssc/NotoSansSC[wght].ttf` (instancias 400 y 700) | Los 6 763 caracteres de GB 2312, signos CJK y formas de ancho completo |

Licencia: SIL Open Font License 1.1 (`OFL.txt`). Se pueden incrustar y redistribuir; no se pueden vender por separado.

Se recortaron con fontTools (`instancer` + `subset`) para que pesen poco. Al generar cada PDF, si `fonttools`
está instalado (ver `requirements.txt`), se incrustan solo las letras usadas (unos pocos KB); si no, la fuente completa.
