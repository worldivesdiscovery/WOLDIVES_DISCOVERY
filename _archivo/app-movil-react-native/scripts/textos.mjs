// Lists every text of the app that needs a translation and checks that en.json and fr.json have all of them.
//   node scripts/textos.mjs            → list of missing texts per language (exit 1 if any)
//   node scripts/textos.mjs --lista    → every Spanish text
import { readFileSync, readdirSync, statSync } from 'node:fs';
import { join } from 'node:path';

const root = new URL('..', import.meta.url).pathname;
const files = [];
const walk = (d) => readdirSync(d).forEach((f) => { const p = join(d, f); statSync(p).isDirectory() ? walk(p) : /\.(tsx?|ts)$/.test(f) && files.push(p); });
walk(join(root, 'app')); walk(join(root, 'src'));
const texts = new Set();
for (const f of files) {
  const s = readFileSync(f, 'utf8');
  for (const m of s.matchAll(/\bt\(\s*'((?:\\'|[^'])*)'/g)) texts.add(m[1].replace(/\\'/g, "'"));
}
// Texts that come from the sample data and are translated with t(variable).
const demo = readFileSync(join(root, 'src/demo.ts'), 'utf8');
const dynamic = [
  ...demo.matchAll(/\btitle: '([^']+)'/g), ...demo.matchAll(/\blevel: '([^']+)'/g), ...demo.matchAll(/\btype: '([^']+)'/g),
  ...demo.matchAll(/\bnote: '([^']+)'/g), ...demo.matchAll(/\bwhat: '([^']+)'/g), ...demo.matchAll(/\bwho: '([^']+)'/g),
  ...demo.matchAll(/\brole: '([^']+)'/g), ...demo.matchAll(/\{ name: '([^']+)', until/g),
].map((m) => m[1]).filter((x) => !x.includes(' · ' + 'X'));
for (const m of demo.matchAll(/D\('[^']+', '([^']+)'/g)) dynamic.push(m[1]);
['descargo', 'seguro', 'Mal tiempo', 'Estado del mar', 'Avería del barco', 'Otro', 'Todos los niveles', 'Sin titulación', 'Open Water', 'Advanced',
 'Todo', 'Barco', 'Costa', 'Nocturna', 'Cualquier profundidad', 'Hasta 18 m', '18–30 m', 'Más de 30 m', 'Océano (oscuro)', 'Superficie (claro)', 'Sistema',
 'Cada uno elige', 'otra fecha o la devolución íntegra', 'Devolver ya a todos', 'desde tu cuenta de Stripe'].forEach((x) => dynamic.push(x));
dynamic.forEach((x) => texts.add(x));
const all = [...texts].sort((a, b) => a.localeCompare(b, 'es'));
if (process.argv.includes('--lista')) { console.log(JSON.stringify(all, null, 1)); process.exit(0); }
let bad = 0;
for (const lang of ['en', 'fr']) {
  const pack = JSON.parse(readFileSync(join(root, `src/idiomas/${lang}.json`), 'utf8'));
  const missing = all.filter((x) => !(x in pack));
  const vars = all.filter((x) => x in pack && [...x.matchAll(/\{(\w+)\}/g)].some((m) => !pack[x].includes(m[0])));
  if (missing.length || vars.length) { bad = 1; console.log(`${lang}: faltan ${missing.length}, variables mal ${vars.length}`); missing.slice(0, 50).forEach((x) => console.log('  - ' + x)); vars.forEach((x) => console.log('  ! ' + x)); }
  else console.log(`${lang}: ${all.length} textos, completo`);
}
process.exit(bad);
