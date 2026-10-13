# Especies de ejemplo (v50.50)

16 especies para la demo y para empezar el catálogo.

**Origen y licencia de las imágenes:**
- Las 16 son **ilustraciones propias de WORLDIVES DISCOVERY**, dibujadas por programa (`scripts/especies/ilustraciones.py`).
- No son fotos ni copias de ninguna foto. Licencia: **«Ilustración propia»**.
- Están en `public/img/especies/<clave>-320|640|1280.webp`.

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

**Nombres y frases:** cada especie trae el nombre común y una frase breve en los 9 idiomas de la web, en
`app/data/especies/especies.json`.
- En neerlandés, polaco y chino, cuando no hay un nombre común extendido o no estaba seguro, he puesto el del grupo.
  Por ejemplo: «Tandbaars», «Granik» y «石斑鱼» para el mero; «海马» para el caballito.
- Es correcto pero menos preciso. **Conviene que lo revise un nativo** antes del lanzamiento. Se cambia en la ficha de
  cada especie.

## Dónde están en la demo (zip de pruebas)

Solo en puntos donde esas especies viven de verdad:

| Punto | Especies |
|---|---|
| Islas Medes, Costa Brava | Mero, pulpo, morena (habituales); espetón y sepia (ocasionales; sepia de marzo a junio); caballito, pez luna (mayo–agosto) y tortuga boba (junio–septiembre), raras |
| Medes – La Vaca | Mero, pulpo, morena, espetón y sepia |
| Cabo San Antonio | Mero, pulpo, morena, espetón y sepia. Además, **una propuesta del centro de pruebas** (pez luna) que espera tu aprobación |
| Similan – Richelieu Rock (Andamán) | Pez payaso y pez león (habituales); tiburón de puntas blancas y tortuga verde (ocasionales); napoleón, manta (feb–abr) y tiburón ballena (feb–abr), raros |
| Bonaire Marine Park (Caribe) | Tortuga verde y pez león (invasor en el Caribe), habituales; raya águila, ocasional; tortuga boba (abril–septiembre), rara |

La demo **no trae vídeos**: para probarlos hacen falta enlaces reales, y no me invento enlaces de vídeos.
`README-PRUEBAS.md`, apartado 9, explica cómo añadirlos.

En la web real el catálogo empieza vacío. **«Cargar las especies de ejemplo»** (Administración → Vida marina y vídeos →
Especies) añade estas 16 especies sin vincularlas a ningún punto, y solo las que falten.
