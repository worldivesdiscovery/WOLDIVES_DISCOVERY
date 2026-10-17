# Especies de ejemplo (v50.50, ampliadas en v50.51)

31 especies para la demo y para empezar el catálogo de la web real.

**Origen y licencia de las imágenes:**
- Las 31 son **ilustraciones propias de WORLDIVES DISCOVERY**, dibujadas por programa (`scripts/especies/ilustraciones.py`).
- No son fotos ni copias de ninguna foto. Licencia: **«Ilustración propia»**.
- Están en `public/img/especies/<clave>-128|640.webp` (v50.51: 128 px para la foto redonda de la franja y 640 px para el bocadillo).

**Por qué ilustraciones y no fotos:** el encargo pide fotos propias o con licencia. Desde el entorno donde se ha hecho
este trabajo no se puede llegar a Wikimedia Commons: su red bloquea `commons.wikimedia.org` (respuesta 403). No he
intentado saltarme el bloqueo. Con ilustraciones propias no hay ninguna duda de licencia.

**Cómo cambiarlas por fotos reales** (en el servidor real, que sí tiene internet):
1. Ve a Administración → «Vida marina y vídeos» → Especies → Editar.
2. Pulsa «Buscar una foto libre en Wikimedia Commons».
3. Elige una de las fotos marcadas como libres.

El autor y la licencia de cada foto se toman de Commons y se guardan con la foto.

## Lista

| Especie (nombre científico) | Nombre común (es / en) | Imagen | Origen | Licencia |
|---|---|---|---|---|
| Epinephelus marginatus | Mero / Dusky grouper | `mero` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Octopus vulgaris | Pulpo común / Common octopus | `pulpo` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Muraena helena | Morena / Mediterranean moray | `morena` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Hippocampus guttulatus | Caballito de mar narigudo / Long-snouted seahorse | `caballito` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Sepia officinalis | Sepia común / Common cuttlefish | `sepia` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Mola mola | Pez luna / Ocean sunfish | `pez-luna` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Caretta caretta | Tortuga boba / Loggerhead sea turtle | `tortuga-boba` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Sphyraena sphyraena | Espetón / European barracuda | `espeton` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Rhincodon typus | Tiburón ballena / Whale shark | `tiburon-ballena` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Mobula birostris | Manta gigante / Giant manta ray | `manta` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Chelonia mydas | Tortuga verde / Green sea turtle | `tortuga-verde` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Amphiprion ocellaris | Pez payaso / Clown anemonefish | `pez-payaso` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Pterois volitans | Pez león / Red lionfish | `pez-leon` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Triaenodon obesus | Tiburón de puntas blancas de arrecife / Whitetip reef shark | `tiburon-puntas-blancas` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Aetobatus narinari | Raya águila moteada / Spotted eagle ray | `raya-aguila` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Cheilinus undulatus | Pez napoleón / Humphead wrasse | `napoleon` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Chromis chromis | Castañuela / Mediterranean chromis | `castanuela` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Thalassoma pavo | Pez verde / Ornate wrasse | `pez-verde` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Diplodus sargus | Sargo / White seabream | `sargo` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Serranus scriba | Serrano / Painted comber | `serrano` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Sciaena umbra | Corvina / Brown meagre | `corvina` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Dentex dentex | Dentón / Common dentex | `denton` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Sarpa salpa | Salpa / Salema | `salpa` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Scorpaena scrofa | Cabracho / Red scorpionfish | `cabracho` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Balistes capriscus | Pez ballesta / Grey triggerfish | `pez-ballesta` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Echinaster sepositus | Estrella de mar roja / Red starfish | `estrella-roja` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Flabellina affinis | Flabelina violeta / Purple flabellina | `flabelina` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Palinurus elephas | Langosta / European spiny lobster | `langosta` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Paramuricea clavata | Gorgonia roja / Violescent sea whip | `gorgonia-roja` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Posidonia oceanica | Posidonia / Neptune grass | `posidonia` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |
| Anemonia viridis | Anémona común / Snakelocks anemone | `anemona` | Ilustración de WORLDIVES DISCOVERY | Ilustración propia |

**Nombres y frases:** cada especie trae el nombre común y una frase breve en los 9 idiomas de la web, en
`app/data/especies/especies.json`.
- En neerlandés, polaco y chino, cuando no hay un nombre común extendido o no estaba seguro, he puesto el del grupo
  (por ejemplo «Strzępiel» para el serrano o «萨尔帕鲷» para la salpa).
- Es correcto pero menos preciso. **Conviene que lo revise un nativo** antes del lanzamiento. Se cambia en la ficha de
  cada especie.

## En la web real (paquete de PRODUCCIÓN)

Una instalación nueva carga las 31 especies en su primer arranque (sin vincularlas a ningún punto). Si se borran,
«Cargar las especies de ejemplo» (Administración → Vida marina y vídeos → Especies) vuelve a añadir las que falten.

## Dónde están en la demo (paquete DEMO)

Solo en puntos donde esas especies viven de verdad. Entre paréntesis, la frecuencia y, si la tiene, la temporada (meses).

| Punto | Especies | Detalle |
|---|---|---|
| Cabo San Antonio | 14 | Mero (habitual), Corvina (habitual), Sargo (habitual), Castañuela (habitual), Pez verde (habitual), Morena (habitual), Serrano (habitual), Estrella de mar roja (habitual), Pulpo común (ocasional), Dentón (ocasional), Gorgonia roja (ocasional), Langosta (rara), Pez luna (rara, 5/6/7/8), Caballito de mar narigudo (rara) |
| Cabo San Martin / Cueva de la Virgen | 10 | Morena (habitual), Castañuela (habitual), Pez verde (habitual), Serrano (habitual), Estrella de mar roja (habitual), Anémona común (habitual), Cabracho (ocasional), Langosta (ocasional), Flabelina violeta (ocasional, 3/4/5/6), Pulpo común (ocasional) |
| Portitxol Norte | 11 | Posidonia (habitual), Salpa (habitual), Pulpo común (habitual), Castañuela (habitual), Sargo (habitual), Pez verde (habitual), Estrella de mar roja (habitual), Sepia común (ocasional, 3/4/5/6), Espetón (ocasional), Caballito de mar narigudo (rara), Tortuga boba (rara, 6/7/8/9) |
| Piedras Rotas | 9 | Pulpo común (habitual), Morena (habitual), Castañuela (habitual), Sargo (habitual), Serrano (habitual), Salpa (habitual), Anémona común (habitual), Estrella de mar roja (habitual), Cabracho (ocasional) |
| Pared Negra | 9 | Morena (habitual), Pez verde (habitual), Castañuela (habitual), Serrano (habitual), Cabracho (ocasional), Flabelina violeta (ocasional, 3/4/5/6), Dentón (ocasional), Gorgonia roja (rara), Langosta (rara) |
| Montaña Sumergida - Cabo Negro | 9 | Castañuela (habitual), Sargo (habitual), Espetón (habitual), Dentón (ocasional), Mero (ocasional), Corvina (ocasional), Gorgonia roja (ocasional), Pez ballesta (ocasional, 6/7/8/9), Pez luna (rara, 5/6/7/8) |
| Islas Medes, Costa Brava | 15 | Mero (habitual), Corvina (habitual), Espetón (habitual), Sargo (habitual), Castañuela (habitual), Pez verde (habitual), Morena (habitual), Gorgonia roja (habitual), Pulpo común (ocasional), Dentón (ocasional), Langosta (ocasional), Cabracho (ocasional), Caballito de mar narigudo (rara), Pez luna (rara, 5/6/7/8), Tortuga boba (rara, 6/7/8/9) |
| Medes – La Vaca | 10 | Mero (habitual), Gorgonia roja (habitual), Corvina (habitual), Morena (habitual), Castañuela (habitual), Langosta (ocasional), Dentón (ocasional), Espetón (ocasional), Flabelina violeta (ocasional, 3/4/5/6), Cabracho (ocasional) |
| Medes – Carall Bernat | 9 | Gorgonia roja (habitual), Mero (habitual), Morena (habitual), Castañuela (habitual), Estrella de mar roja (habitual), Corvina (ocasional), Langosta (ocasional), Flabelina violeta (ocasional, 3/4/5/6), Dentón (ocasional) |
| Medes – Tascons | 12 | Mero (habitual), Corvina (habitual), Sargo (habitual), Salpa (habitual), Posidonia (habitual), Pulpo común (habitual), Castañuela (habitual), Pez verde (habitual), Serrano (habitual), Estrella de mar roja (habitual), Anémona común (habitual), Sepia común (ocasional, 3/4/5/6) |

La demo **no trae vídeos**: para probarlos hacen falta enlaces reales, y no me invento enlaces de vídeos.
`README-PRUEBAS.md`, apartado 9, explica cómo añadirlos (también desde `data/demo/videos-demo.json`).
