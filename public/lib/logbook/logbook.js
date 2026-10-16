/* =========================================================
   Dive Logbook — componente embebible

   Dos vistas con los mismos datos:
     · Clásica: lista sobria que hereda la letra y los colores de tu web.
     · Pasaporte: libro 3D. Se desbloquea con la primera inmersión verificada
       por un centro, al registrarse con el enlace de un centro, o tocando
       5 veces seguidas el icono del pasaporte.

   <link rel="stylesheet" href="logbook.css">
   <div class="dive-logbook" data-assets="assets/"></div>
   <script src="https://cdnjs.cloudflare.com/ajax/libs/qrcode-generator/1.4.4/qrcode.min.js"></script>  (QR personal, opcional)
   <script src="logbook.js"></script>

   Atributos opcionales: data-assets, data-storage-key, data-pages, data-title,
   data-view ("classic" | "passport"), data-require-unlock ("false" = siempre disponible),
   data-secret-unlock ("false" = sin truco de 5 toques), data-logbook-theme (JSON),
   data-center-logo, data-center-name.
   API y flujos de servidor: ver LEEME.md
   ========================================================= */
(function () {
  "use strict";

  /* página del libro: 400 px de ancho y la proporción de las ilustraciones (0,648); P: lo que la tapa asoma
     alrededor de las hojas. Las tapas se dibujan en 400 × 560 y se ajustan a su tamaño. */
  const W = 400, H = 617, P = 8, CW = 400, CH = 560, TURN_MS = 600;
  let UID = 0;

  const DEFAULT_THEME = { background: "transparent", cover: "#011c3c", foil: "#d4b26a", paper: "#f3ecdc", ink: "#1c3a6b" };   // v50.58: tapa azul Abismo, papel marfil
  const DEFAULT_LOCKED = ["date", "site", "country", "center", "pos", "sign"];

  /* ---------- utilidades ---------- */
  const esc = s => String(s == null ? "" : s).replace(/[&<>"']/g, c => ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" }[c]));
  const mrzClean = s => String(s || "").toUpperCase().normalize("NFD").replace(/[̀-ͯ]/g, "").replace(/[^A-Z0-9]+/g, "<").replace(/^<+|<+$/g, "");
  const fit = (s, n) => (s + "<".repeat(n)).slice(0, n);
  const num = v => { const x = parseFloat(String(v || "").replace(",", ".")); return isFinite(x) ? x : 0; };
  function rng(seed) { return function () { seed |= 0; seed = seed + 0x6D2B79F5 | 0; let t = Math.imul(seed ^ seed >>> 15, 1 | seed); t = t + Math.imul(t ^ t >>> 7, 61 | t) ^ t; return ((t ^ t >>> 14) >>> 0) / 4294967296; }; }
  function hex(c) {
    c = String(c || "").trim().replace("#", "");
    if (c.length === 3) c = c.split("").map(x => x + x).join("");
    const n = parseInt(c, 16);
    return isFinite(n) && c.length === 6 ? [n >> 16 & 255, n >> 8 & 255, n & 255] : null;
  }
  function mix(a, b, t) {
    const A = hex(a), B = hex(b);
    if (!A || !B) return a;
    return "#" + A.map((v, i) => Math.round(v + (B[i] - v) * t).toString(16).padStart(2, "0")).join("");
  }
  const rgba = (c, a) => { const A = hex(c) || [0, 0, 0]; return `rgba(${A[0]},${A[1]},${A[2]},${a})`; };

  /* ---------- arte vectorial de la tapa ---------- */
  function topo(seed, sets) {
    const r = rng(seed); let d = "";
    sets.forEach(([cx, cy, rx, ry, rings]) => {
      const ph = r() * 6.28, ph2 = r() * 6.28;
      for (let i = 1; i <= rings; i++) {
        const s = i / rings; let p = "";
        for (let k = 0; k <= 64; k++) {
          const a = k / 64 * Math.PI * 2;
          const m = 1 + .14 * Math.sin(3 * a + ph + i * .25) + .08 * Math.sin(5 * a + ph2) + .04 * Math.sin(9 * a + i);
          p += (k ? "L" : "M") + (cx + Math.cos(a) * rx * s * m).toFixed(1) + " " + (cy + Math.sin(a) * ry * s * m).toFixed(1);
        }
        d += p + "Z";
      }
    });
    return `<path d="${d}" fill="none" stroke="rgba(170,200,235,.12)" stroke-width=".9" transform="translate(0 .8)"/><path d="${d}" fill="none" stroke="rgba(0,0,0,.45)" stroke-width=".8"/>`;
  }

  function compassRing(cx, cy, R, g, letters = true) {
    let s = `<circle cx="${cx}" cy="${cy}" r="${R}" fill="none" stroke="url(#${g}-gold)" stroke-width="1.8"/>
      <circle cx="${cx}" cy="${cy}" r="${R - 7}" fill="none" stroke="url(#${g}-gold)" stroke-width=".8"/>`;
    for (let a = 0; a < 360; a += 5) {
      const rad = a * Math.PI / 180, long = a % 45 === 0, r1 = R - (long ? 12 : 7);
      s += `<line x1="${(cx + Math.sin(rad) * r1).toFixed(1)}" y1="${(cy - Math.cos(rad) * r1).toFixed(1)}" x2="${(cx + Math.sin(rad) * R).toFixed(1)}" y2="${(cy - Math.cos(rad) * R).toFixed(1)}" stroke="url(#${g}-gold)" stroke-width="${long ? 1.2 : .6}"/>`;
    }
    if (letters) {
      const L = (t, x, y) => `<text x="${x}" y="${y}" text-anchor="middle" font-family="Cinzel, Georgia, serif" font-size="${R * .17}" fill="url(#${g}-gold)">${t}</text>`;
      s += L("N", cx + R * .2, cy - R - 8) + L("S", cx - R * .2, cy + R + R * .22) + L("E", cx + R + R * .2, cy - R * .14) + L("W", cx - R - R * .18, cy + R * .24);
    }
    return s;
  }

  function compass(cx, cy, R, g) {
    let s = compassRing(cx, cy, R, g) +
      `<circle cx="${cx}" cy="${cy}" r="${R * .64}" fill="none" stroke="url(#${g}-gold)" stroke-width=".8"/>
       <circle cx="${cx}" cy="${cy}" r="${R * .6}" fill="none" stroke="url(#${g}-gold)" stroke-width=".4" stroke-dasharray="2 3"/>`;
    const point = (deg, len, w) => {
      const a = deg * Math.PI / 180, tx = cx + Math.sin(a) * len, ty = cy - Math.cos(a) * len;
      const px = Math.cos(a) * w, py = Math.sin(a) * w;
      return `<path d="M${cx} ${cy}L${(cx - px).toFixed(1)} ${(cy - py).toFixed(1)}L${tx.toFixed(1)} ${ty.toFixed(1)}Z" fill="url(#${g}-gold-l)"/>
        <path d="M${cx} ${cy}L${(cx + px).toFixed(1)} ${(cy + py).toFixed(1)}L${tx.toFixed(1)} ${ty.toFixed(1)}Z" fill="url(#${g}-gold-d)"/>`;
    };
    [45, 135, 225, 315].forEach(d => s += point(d, R * .8, R * .1));
    [0, 90, 180, 270].forEach(d => s += point(d, R * 1.36, R * .13));
    return s;
  }

  function manta(cx, cy, sc, rot, fill) {
    return `<g transform="translate(${cx} ${cy}) rotate(${rot}) scale(${sc})">
      <path d="M0 -20C5 -20 9 -16 13 -11C30 -9 50 -3 64 10C50 7 34 9 22 14C15 18 8 22 3 25L.8 64L-.8 64L-3 25C-8 22 -15 18 -22 14C-34 9 -50 7 -64 10C-50 -3 -30 -9 -13 -11C-9 -16 -5 -20 0 -20Z
        M-6 -18C-9 -24 -8 -28 -5 -29C-4 -25 -3 -22 -2 -19Z M6 -18C9 -24 8 -28 5 -29C4 -25 3 -22 2 -19Z" fill="${fill}" stroke="rgba(30,30,25,.35)" stroke-width=".5"/>
      <path d="M-12 -6C-4 -2 4 -2 12 -6M-20 4C-8 9 8 9 20 4" fill="none" stroke="rgba(60,55,40,.35)" stroke-width=".7"/>
    </g>`;
  }

  function goldDefs(g, foil) {
    const f = foil || DEFAULT_THEME.foil, F = hex(f) || [212, 178, 106];
    const fr = (F[0] / 255).toFixed(3), fg = (F[1] / 255).toFixed(3), fb = (F[2] / 255).toFixed(3);
    return `<defs>
      <linearGradient id="${g}-gold" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${mix(f, "#ffffff", .5)}"/><stop offset=".45" stop-color="${mix(f, "#000000", .05)}"/><stop offset=".7" stop-color="${mix(f, "#ffffff", .3)}"/><stop offset="1" stop-color="${mix(f, "#000000", .22)}"/></linearGradient>
      <linearGradient id="${g}-gold-l" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${mix(f, "#ffffff", .58)}"/><stop offset="1" stop-color="${mix(f, "#ffffff", .1)}"/></linearGradient>
      <linearGradient id="${g}-gold-d" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${mix(f, "#000000", .15)}"/><stop offset="1" stop-color="${mix(f, "#000000", .42)}"/></linearGradient>
      <linearGradient id="${g}-ray" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="${mix(f, "#ffffff", .72)}"/><stop offset=".5" stop-color="${mix(f, "#9a9a9a", .45)}"/><stop offset="1" stop-color="${mix(f, "#ffffff", .6)}"/></linearGradient>
      <filter id="${g}-foil" x="-5%" y="-5%" width="110%" height="110%" color-interpolation-filters="sRGB">
        <feOffset in="SourceAlpha" dy="-1" result="o1"/><feFlood flood-color="#000814" flood-opacity=".7"/><feComposite in2="o1" operator="in" result="dark"/>
        <feOffset in="SourceAlpha" dy="1.1" result="o2"/><feFlood flood-color="#9fbbe0" flood-opacity=".2"/><feComposite in2="o2" operator="in" result="light"/>
        <feGaussianBlur in="SourceAlpha" stdDeviation="1.1" result="b"/>
        <feSpecularLighting in="b" surfaceScale="2.6" specularConstant="1.05" specularExponent="20" lighting-color="${mix(f, "#ffffff", .75)}" result="spec"><feDistantLight azimuth="235" elevation="40"/></feSpecularLighting>
        <feComposite in="spec" in2="SourceAlpha" operator="in" result="specIn"/>
        <feComposite in="SourceGraphic" in2="specIn" operator="arithmetic" k2="1" k3=".5" result="lit"/>
        <feTurbulence type="fractalNoise" baseFrequency="1.4" numOctaves="2" seed="9" result="t"/>
        <feColorMatrix in="t" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 1.2 -.62" result="wear"/>
        <feComposite in="lit" in2="wear" operator="out" result="worn"/>
        <feMerge><feMergeNode in="dark"/><feMergeNode in="light"/><feMergeNode in="worn"/></feMerge>
      </filter>
      <filter id="${g}-tofoil" color-interpolation-filters="sRGB">
        <feColorMatrix type="matrix" values="0 0 0 0 ${fr}  0 0 0 0 ${fg}  0 0 0 0 ${fb}  0 0 0 1 0"/>
      </filter>
    </defs>`;
  }

  function chip(cx, cy, g) {
    return `<g stroke="url(#${g}-gold)" fill="none" stroke-width="1.3"><rect x="${cx - 13}" y="${cy - 8}" width="26" height="16" rx="2"/>
      <line x1="${cx - 13}" y1="${cy}" x2="${cx - 5}" y2="${cy}"/><line x1="${cx + 5}" y1="${cy}" x2="${cx + 13}" y2="${cy}"/>
      <circle cx="${cx}" cy="${cy}" r="4.6"/></g>`;
  }

  function frontCoverSVG(g, theme, cover) {
    const useLogo = cover && cover.logo && !cover.off;
    const cx = 200, cy = 236;
    let emblem;
    if (!useLogo) {
      emblem = `<g filter="url(#${g}-foil)">${compass(196, cy, 104, g)}${manta(cx, cy, 1.55, -32, `url(#${g}-ray)`)}</g>`;
    } else {
      const r = 76, logo = esc(cover.logo);
      const img = cover.style === "foil"
        ? `<g filter="url(#${g}-foil)"><image href="${logo}" x="${cx - r + 8}" y="${cy - r + 8}" width="${(r - 8) * 2}" height="${(r - 8) * 2}" preserveAspectRatio="xMidYMid meet" filter="url(#${g}-tofoil)"/></g>`
        : `<circle cx="${cx}" cy="${cy}" r="${r}" fill="${mix(theme.paper, "#ffffff", .35)}"/>
           <image href="${logo}" x="${cx - r + 10}" y="${cy - r + 10}" width="${(r - 10) * 2}" height="${(r - 10) * 2}" preserveAspectRatio="xMidYMid meet" clip-path="url(#${g}-clip)"/>
           <circle cx="${cx}" cy="${cy}" r="${r}" fill="none" stroke="rgba(0,0,0,.35)" stroke-width="3"/>`;
      emblem = `<clipPath id="${g}-clip"><circle cx="${cx}" cy="${cy}" r="${r - 2}"/></clipPath>
        <g filter="url(#${g}-foil)">${compassRing(cx, cy, 104, g)}<circle cx="${cx}" cy="${cy}" r="${r + 4}" fill="none" stroke="url(#${g}-gold)" stroke-width="2.4"/></g>${img}`;
    }
    const name = useLogo && cover.name
      ? `<text x="${CW / 2}" y="488" text-anchor="middle" font-family="Cinzel, Georgia, serif" font-size="10.5" letter-spacing="2.6" fill="url(#${g}-gold)">${esc(String(cover.name).toUpperCase().slice(0, 34))}</text>` : "";
    return `<svg viewBox="0 0 ${CW} ${CH}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">${goldDefs(g, theme.foil)}
      ${topo(7, [[330, 70, 130, 90, 9], [40, 380, 120, 150, 10], [360, 470, 70, 60, 6], [110, 70, 70, 50, 5]])}
      ${emblem}
      <g filter="url(#${g}-foil)">
      <text x="${CW / 2}" y="${name ? 458 : 462}" text-anchor="middle" font-family="Cinzel, Georgia, serif" font-size="27" letter-spacing="3" fill="url(#${g}-gold)">DIVE LOGBOOK</text>
      ${name}${chip(CW / 2, name ? 520 : 508, g)}</g></svg>`;
  }

  function backCoverSVG(g, theme) {
    return `<svg viewBox="0 0 ${CW} ${CH}" preserveAspectRatio="xMidYMid slice" aria-hidden="true">${goldDefs(g, theme.foil)}
      ${topo(19, [[90, 120, 140, 110, 10], [320, 400, 130, 170, 11]])}
      <g filter="url(#${g}-foil)" opacity=".9">${compass(CW / 2, 430, 34, g)}
      <text x="${CW / 2}" y="514" text-anchor="middle" font-family="Cinzel, Georgia, serif" font-size="9.5" letter-spacing="3" fill="url(#${g}-gold)">EXPLORE · RECORD · PROTECT</text></g></svg>`;
  }

  function compassWM() {
    let s = `<svg viewBox="0 0 200 200" class="dlb-wm compass" aria-hidden="true"><g fill="none" stroke="currentColor">
      <circle cx="100" cy="100" r="92" stroke-width="1.2"/><circle cx="100" cy="100" r="84" stroke-width=".6"/><circle cx="100" cy="100" r="50" stroke-width=".6"/>`;
    for (let a = 0; a < 360; a += 10) { const r = a * Math.PI / 180; s += `<line x1="${100 + Math.sin(r) * 84}" y1="${100 - Math.cos(r) * 84}" x2="${100 + Math.sin(r) * 92}" y2="${100 - Math.cos(r) * 92}" stroke-width=".6"/>`; }
    s += `</g><g fill="currentColor">`;
    [0, 90, 180, 270].forEach(d => s += `<path d="M100 100L94 100L100 18Z" transform="rotate(${d} 100 100)"/><path d="M100 100L106 100L100 18Z" opacity=".5" transform="rotate(${d} 100 100)"/>`);
    [45, 135, 225, 315].forEach(d => s += `<path d="M100 100L96 100L100 48Z" opacity=".7" transform="rotate(${d} 100 100)"/>`);
    return s + `</g></svg>`;
  }

  /* sello de pasaporte (normal o verificado por el centro) */
  const INKS = ["#2c4f7d", "#8b2e3b", "#2c6b61", "#94661a", "#4b3f7a"];
  function stampSVG(uid, n, site, date, verified) {
    const c = verified ? "#1f6b4f" : INKS[n % INKS.length], rot = ((n * 47) % 34) - 17, id = `${uid}-sp${n}`;
    const ring = verified ? `${verified.center || "DIVE CENTRE"} · ${site}` : site;
    const t = String(ring).toUpperCase().slice(0, verified ? 36 : 30);
    const mid = verified
      ? `<path d="M48 58l8 8 16-17" stroke-width="3.2" stroke-linecap="round" stroke-linejoin="round"/>
         <text x="60" y="80" text-anchor="middle" font-family="Cinzel, serif" font-size="7.5" letter-spacing="1.2" fill="${c}" stroke="none">VERIFIED</text>
         <text x="60" y="47" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="6.5" fill="${c}" stroke="none">${esc(String(date).slice(0, 12))}</text>`
      : `<text x="60" y="55" text-anchor="middle" font-family="Cinzel, serif" font-size="8.5" letter-spacing="1" fill="${c}" stroke="none">DIVE Nº</text>
         <text x="60" y="68" text-anchor="middle" font-family="Cinzel, serif" font-size="13" fill="${c}" stroke="none">${esc(n)}</text>
         <text x="60" y="80" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="7" fill="${c}" stroke="none">${esc(String(date).slice(0, 12))}</text>`;
    return `<svg viewBox="0 0 120 120" style="transform:rotate(${rot}deg)"><g filter="url(#${uid.replace(/m$/, "")}-ink)" fill="none" stroke="${c}">
      <defs><path id="${id}" d="M60 60m-41 0a41 41 0 1 1 82 0a41 41 0 1 1-82 0"/></defs>
      <circle cx="60" cy="60" r="55" stroke-width="3"/><circle cx="60" cy="60" r="50" stroke-width="1"/><circle cx="60" cy="60" r="31" stroke-width="1.4"/>
      <text font-family="IBM Plex Mono, monospace" font-size="${verified ? 7.6 : 9}" letter-spacing="1.1" fill="${c}" stroke="none"><textPath href="#${id}" startOffset="50%" text-anchor="middle">${esc(t)}</textPath></text>
      ${mid}
    </g></svg>`;
  }

  /* QR (usa qrcode-generator si está cargado) */
  function qrSVG(text, color) {
    if (!text || typeof window.qrcode !== "function") return "";
    try {
      const q = window.qrcode(0, "M"); q.addData(String(text)); q.make();
      const n = q.getModuleCount(); let d = "";
      for (let r = 0; r < n; r++) for (let c = 0; c < n; c++) if (q.isDark(r, c)) d += `M${c} ${r}h1v1h-1z`;
      return `<svg viewBox="-2 -2 ${n + 4} ${n + 4}" shape-rendering="crispEdges" aria-label="Código QR personal"><path d="${d}" fill="${color}"/></svg>`;
    } catch (e) { return ""; }
  }

  /* ---------- mapas: carta náutica grabada ---------- */
  const DEFAULT_MAP_DATA = "https://cdn.jsdelivr.net/npm/world-atlas@2.0.2/land-50m.json";
  const GEO = { url: null, promise: null, polys: null };

  // TopoJSON (world-atlas) o GeoJSON -> [{ rings: [[lon,lat]...], bbox }]
  function decodeGeo(t) {
    const polys = [];
    const push = rings => {
      if (!rings.length || !rings[0].length) return;
      const b = [180, 90, -180, -90];
      rings[0].forEach(([x, y]) => { if (x < b[0]) b[0] = x; if (y < b[1]) b[1] = y; if (x > b[2]) b[2] = x; if (y > b[3]) b[3] = y; });
      polys.push({ rings, bbox: b });
    };
    if (t && t.type === "Topology") {
      const tf = t.transform;
      const arcs = t.arcs.map(arc => { let x = 0, y = 0; return arc.map(p => { if (!tf) return p; x += p[0]; y += p[1]; return [x * tf.scale[0] + tf.translate[0], y * tf.scale[1] + tf.translate[1]]; }); });
      const arcPts = i => i >= 0 ? arcs[i] : arcs[~i].slice().reverse();
      const ring = ids => { const out = []; ids.forEach((i, k) => arcPts(i).forEach((p, j) => { if (!(k > 0 && j === 0)) out.push(p); })); return out; };
      const geom = g => {
        if (g.type === "GeometryCollection") g.geometries.forEach(geom);
        else if (g.type === "Polygon") push(g.arcs.map(ring));
        else if (g.type === "MultiPolygon") g.arcs.forEach(p => push(p.map(ring)));
      };
      const objs = t.objects || {};
      geom(objs.land || objs[Object.keys(objs)[0]]);
    } else if (t) {
      const geom = g => {
        if (!g) return;
        if (g.type === "FeatureCollection") g.features.forEach(f => geom(f.geometry));
        else if (g.type === "Feature") geom(g.geometry);
        else if (g.type === "GeometryCollection") g.geometries.forEach(geom);
        else if (g.type === "Polygon") push(g.coordinates);
        else if (g.type === "MultiPolygon") g.coordinates.forEach(push);
      };
      geom(t);
    }
    return polys;
  }
  function loadGeo(url) {
    if (GEO.promise && GEO.url === url) return GEO.promise;
    GEO.url = url;
    GEO.promise = fetch(url).then(r => { if (!r.ok) throw new Error(r.status); return r.json(); })
      .catch(() => /^https:\/\/cdn\.jsdelivr\.net\//.test(url) ? import(url + "/+esm").then(m => m.default || m) : null)
      .then(t => { GEO.polys = t ? decodeGeo(t) : null; return GEO.polys; })
      .catch(() => { GEO.polys = null; return null; });
    return GEO.promise;
  }

  function parsePos(s) {
    s = String(s || "").trim();
    if (!s) return null;
    const dms = [...s.matchAll(/(\d+(?:[.,]\d+)?)\s*[°º]?\s*(?:(\d+(?:[.,]\d+)?)\s*['′’]?\s*)?(?:(\d+(?:[.,]\d+)?)\s*(?:["″”]|'')?\s*)?([NSEWO])\b/gi)];
    if (dms.length >= 2) {
      const val = m => { const f = x => parseFloat(String(x || 0).replace(",", ".")); let v = f(m[1]) + f(m[2]) / 60 + f(m[3]) / 3600; return /[SWO]/i.test(m[4]) ? -v : v; };
      const a = dms.find(m => /[NS]/i.test(m[4])), b = dms.find(m => /[EWO]/i.test(m[4]));
      if (a && b) { const lat = val(a), lon = val(b); if (Math.abs(lat) <= 90 && Math.abs(lon) <= 180) return { lat, lon }; }
    }
    const m = s.replace(/;/g, ",").match(/(-?\d+(?:\.\d+)?)\s*[,\s]\s*(-?\d+(?:\.\d+)?)/);
    if (m) { const lat = parseFloat(m[1]), lon = parseFloat(m[2]); if (Math.abs(lat) <= 90 && Math.abs(lon) <= 180) return { lat, lon }; }
    return null;
  }
  function fmtDM(lat, lon) {
    const f = (v, pos, neg, w) => { const a = Math.abs(v), d = Math.floor(a), m = (a - d) * 60; return `${String(d).padStart(w, "0")}°${m.toFixed(1).padStart(4, "0")}′${v < 0 ? neg : pos}`; };
    return `${f(lat, "N", "S", 2)}  ${f(lon, "E", "W", 3)}`;
  }

  function mapColors(theme) {
    return { ink: theme.ink, water: mix(theme.paper, mix(theme.cover, "#9fbad3", .65), .22), land: mix(theme.paper, "#ffffff", .3), red: "#a5303d" };
  }
  function ringsPath(polys, X, Y, box, minStep, skip) {
    let d = "";
    polys.forEach(p => {
      if (box && (p.bbox[2] < box[0] || p.bbox[0] > box[2] || p.bbox[3] < box[1] || p.bbox[1] > box[3])) return;
      p.rings.forEach(r => {
        let px = null, py = null, seg = "", cnt = 0;
        for (let i = 0; i < r.length; i += skip || 1) {
          const x = X(r[i][0]), y = Y(r[i][1]);
          if (px !== null && Math.abs(x - px) < minStep && Math.abs(y - py) < minStep) continue;
          seg += (cnt ? "L" : "M") + x.toFixed(1) + " " + y.toFixed(1); px = x; py = y; cnt++;
        }
        if (cnt > 2) d += seg + "Z";
      });
    });
    return d;
  }
  function neatline(w, h, ink) {
    // borde de carta: doble filete con segmentos alternos
    let s = `<rect x=".6" y=".6" width="${w - 1.2}" height="${h - 1.2}" fill="none" stroke="${ink}" stroke-width="1.1"/>
      <rect x="3.6" y="3.6" width="${w - 7.2}" height="${h - 7.2}" fill="none" stroke="${ink}" stroke-width=".5"/>`;
    const seg = 9;
    for (let x = 3.6, k = 0; x < w - 3.6; x += seg, k++) if (k % 2) s += `<rect x="${x}" y="1.2" width="${Math.min(seg, w - 3.6 - x)}" height="2.4" fill="${ink}"/><rect x="${x}" y="${h - 3.6}" width="${Math.min(seg, w - 3.6 - x)}" height="2.4" fill="${ink}"/>`;
    for (let y = 3.6, k = 0; y < h - 3.6; y += seg, k++) if (k % 2) s += `<rect x="1.2" y="${y}" width="2.4" height="${Math.min(seg, h - 3.6 - y)}" fill="${ink}"/><rect x="${w - 3.6}" y="${y}" width="2.4" height="${Math.min(seg, h - 3.6 - y)}" fill="${ink}"/>`;
    return s;
  }
  function northArrow(x, y, ink) {
    return `<g transform="translate(${x} ${y})"><path d="M0 -8L2.6 3L0 1.4Z" fill="${ink}"/><path d="M0 -8L-2.6 3L0 1.4Z" fill="none" stroke="${ink}" stroke-width=".6"/>
      <text y="-10" text-anchor="middle" font-family="Cinzel, Georgia, serif" font-size="6.5" fill="${ink}">N</text></g>`;
  }
  function diveFlag(x, y, red) {
    return `<g transform="translate(${x.toFixed(1)} ${y.toFixed(1)})">
      <circle r="5.5" fill="none" stroke="${red}" stroke-width=".8" opacity=".55"/>
      <circle r="1.9" fill="${red}"/>
      <path d="M0 0V-15" stroke="#1d1d1d" stroke-width=".9"/>
      <rect x="0" y="-15" width="11" height="7.5" fill="${red}"/>
      <path d="M0 -15L11 -7.5" stroke="#fff" stroke-width="1.6"/>
    </g>`;
  }

  // carta regional de una inmersión
  function chartSVG(id, pos, polys, theme, w, h, km) {
    const c = mapColors(theme), ink = c.ink;
    const lat = pos.lat, lon = pos.lon, rad = Math.PI / 180;
    const kx = w / (km / (111.32 * Math.cos(lat * rad)));
    const ky = kx / rad;
    const merc = la => Math.log(Math.tan(Math.PI / 4 + la * rad / 2));
    const m0 = merc(lat);
    const X = lo => w / 2 + (lo - lon) * kx, Y = la => h / 2 - (merc(la) - m0) * ky;
    const inv = mm => (2 * Math.atan(Math.exp(mm)) - Math.PI / 2) / rad;
    const lonMin = lon - w / 2 / kx, lonMax = lon + w / 2 / kx;
    const latMax = inv(m0 + h / 2 / ky), latMin = inv(m0 - h / 2 / ky);
    const pad = (lonMax - lonMin) * .2;
    const land = polys ? ringsPath(polys, X, Y, [lonMin - pad, latMin - pad, lonMax + pad, latMax + pad], .5) : "";
    // retícula
    const span = lonMax - lonMin, steps = [.05, .1, .25, .5, 1, 2];
    const st = steps.find(s => span / s <= 3) || 2;
    let grid = "", lab = "";
    for (let g = Math.ceil(lonMin / st) * st; g <= lonMax; g += st) { const x = X(g); grid += `M${x.toFixed(1)} 0V${h}`; }
    for (let g = Math.ceil(latMin / st) * st; g <= latMax; g += st) { const y = Y(g); grid += `M0 ${y.toFixed(1)}H${w}`; }
    // escala gráfica
    const kmPx = w / km, nice = [1, 2, 5, 10, 20, 50, 100].find(v => v * kmPx >= w * .2) || 100;
    const sb = nice * kmPx;
    let waves = "";
    if (land) [[12, .16], [8, .22], [4.4, .32]].forEach(([o, op]) => {
      waves += `<path d="${land}" fill="none" stroke="${ink}" stroke-opacity="${op}" stroke-width="${o * 2}" stroke-linejoin="round"/><path d="${land}" fill="none" stroke="${c.water}" stroke-width="${o * 2 - .9}" stroke-linejoin="round"/>`;
    });
    return `<svg viewBox="0 0 ${w} ${h}" aria-hidden="true">
      <defs><clipPath id="${id}-c"><rect x="3.6" y="3.6" width="${w - 7.2}" height="${h - 7.2}"/></clipPath>
        <pattern id="${id}-h" width="3" height="3" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0V3" stroke="${ink}" stroke-width=".45" opacity=".3"/></pattern></defs>
      <rect width="${w}" height="${h}" fill="${c.water}"/>
      <g clip-path="url(#${id}-c)">
        ${waves}
        ${land ? `<path d="${land}" fill="${c.land}" fill-rule="evenodd"/><path d="${land}" fill="url(#${id}-h)" fill-rule="evenodd"/><path d="${land}" fill="none" stroke="${ink}" stroke-width=".8" stroke-linejoin="round"/>` : ""}
        <path d="${grid}" stroke="${ink}" stroke-width=".35" stroke-dasharray="1.5 2" opacity=".45"/>
        ${diveFlag(X(lon), Y(lat), c.red)}
        <rect x="6" y="${h - 22}" width="${w - 12}" height="13" fill="${c.water}" opacity=".82"/>
        <text x="${w / 2}" y="${h - 12.4}" text-anchor="middle" font-family="IBM Plex Mono, monospace" font-size="6.6" letter-spacing=".3" fill="${ink}">${fmtDM(lat, lon)}</text>
        <g transform="translate(9 ${h - 29})"><path d="M0 0H${sb.toFixed(1)}" stroke="${ink}" stroke-width="1.6"/><path d="M0 0H${(sb / 2).toFixed(1)}" stroke="${c.land}" stroke-width=".8"/>
          <text x="${(sb + 3).toFixed(1)}" y="2" font-family="IBM Plex Mono, monospace" font-size="5.6" fill="${ink}">${nice} km</text></g>
        ${northArrow(w - 13, 20, ink)}
      </g>
      ${neatline(w, h, ink)}
    </svg>`;
  }
  function emptyChartSVG(w, h, theme) {
    const c = mapColors(theme), ink = c.ink;
    return `<svg viewBox="0 0 ${w} ${h}" aria-hidden="true"><rect width="${w}" height="${h}" fill="${c.water}" opacity=".55"/>
      <g opacity=".35" stroke="${ink}" fill="none"><circle cx="${w / 2}" cy="${h / 2 - 8}" r="22" stroke-width=".7"/><circle cx="${w / 2}" cy="${h / 2 - 8}" r="17" stroke-width=".4" stroke-dasharray="1.5 2"/>
      <path d="M${w / 2} ${h / 2 - 36}V${h / 2 + 20}M${w / 2 - 28} ${h / 2 - 8}H${w / 2 + 28}" stroke-width=".5"/></g>
      <text x="${w / 2}" y="${h - 16}" text-anchor="middle" font-family="EB Garamond, Georgia, serif" font-style="italic" font-size="9" fill="${ink}" opacity=".6">Añade la posición GPS</text>
      ${neatline(w, h, ink)}</svg>`;
  }
  // mapa del mundo con todas las inmersiones
  function worldSVG(id, points, polys, theme, w, h, msg) {
    const c = mapColors(theme), ink = c.ink;
    const X = lo => (lo + 180) / 360 * w, Y = la => (80 - la) / 140 * h;
    const land = polys ? ringsPath(polys, X, Y, [-180, -60, 180, 80], .7, 2) : "";
    let grid = "";
    for (let g = -150; g < 180; g += 30) grid += `M${X(g).toFixed(1)} 0V${h}`;
    for (let g = -30; g <= 60; g += 30) grid += `M0 ${Y(g).toFixed(1)}H${w}`;
    const dots = points.map(p => `<circle cx="${X(p.lon).toFixed(1)}" cy="${Y(p.lat).toFixed(1)}" r="3.1" fill="${p.verified ? "#1f6b4f" : c.red}" stroke="${c.land}" stroke-width="1"/>`).join("");
    return `<svg viewBox="0 0 ${w} ${h}" aria-hidden="true">
      <defs><clipPath id="${id}-c"><rect x="3.6" y="3.6" width="${w - 7.2}" height="${h - 7.2}"/></clipPath>
        <pattern id="${id}-h" width="2.6" height="2.6" patternUnits="userSpaceOnUse" patternTransform="rotate(45)"><path d="M0 0V2.6" stroke="${ink}" stroke-width=".4" opacity=".35"/></pattern></defs>
      <rect width="${w}" height="${h}" fill="${c.water}"/>
      <g clip-path="url(#${id}-c)">
        <path d="${grid}" stroke="${ink}" stroke-width=".3" stroke-dasharray="1.5 2" opacity=".4"/>
        ${land ? `<path d="${land}" fill="${c.land}"/><path d="${land}" fill="url(#${id}-h)"/><path d="${land}" fill="none" stroke="${ink}" stroke-width=".45" opacity=".8"/>` : `<text x="${w / 2}" y="${h / 2 + 3}" text-anchor="middle" font-family="EB Garamond, Georgia, serif" font-style="italic" font-size="10" fill="${ink}" opacity=".55">${msg || "Cargando el mapa…"}</text>`}
        ${dots}
      </g>
      ${neatline(w, h, ink)}</svg>`;
  }

  /* ---------- plantillas de páginas ---------- */
  const fld = (k, es, en, ph = "", extra = "") =>
    `<label class="dlb-f"><span>${es}${en ? ` <i>${en}</i>` : ""}</span><input data-k="${k}" id="${k.replace(/:/g, "-")}" placeholder="${esc(ph)}" autocomplete="off" ${extra}></label>`;
  const gauge = (k, es, unit) =>
    `<label class="dlb-f dlb-gauge"><span>${es}</span><div class="dlb-unit"><input data-k="${k}" id="${k.replace(/:/g, "-")}" inputmode="decimal" autocomplete="off"><em>${unit}</em></div></label>`;
  const TYPES = [["boat", "Barco"], ["shore", "Costa"], ["night", "Nocturna"], ["drift", "Deriva"], ["wreck", "Pecio"], ["deep", "Profunda"]];

  function divePage(n, pno, assets, uid) {
    const k = f => `d:${n}:${f}`;
    const wm = n % 2 ? compassWM() : `<div class="dlb-wm whale" style="background-image:url('${assets}page-whale.jpg')"></div>`;
    return `${wm}<div class="dlb-verified" data-verified="${n}" hidden></div><div class="dlb-pg">
      <div class="dlb-head">
        <div class="dlb-title">INMERSIÓN <small>Dive</small> Nº <input class="dlb-num" data-k="${k("no")}" id="d-${n}-no" placeholder="${n}" inputmode="numeric" aria-label="Número de inmersión" autocomplete="off"></div>
        <label class="dlb-f" style="width:118px"><span>Fecha <i>Date</i></span><input data-k="${k("date")}" id="d-${n}-date" placeholder="dd/mm/aaaa" autocomplete="off"></label>
      </div>
      <div class="dlb-where">
        <div class="dlb-where-fields">
          ${fld(k("site"), "Lugar", "Dive site")}
          <div class="dlb-row c2">${fld(k("country"), "País / región", "Country")}${fld(k("center"), "Centro", "Dive centre")}</div>
          <label class="dlb-f dlb-gps"><span>Posición GPS <i>Position</i></span><div class="dlb-unit"><input data-k="${k("pos")}" id="d-${n}-pos" placeholder="38.16, -0.47" autocomplete="off" inputmode="decimal"><button type="button" class="dlb-locate" data-locate="${n}" aria-label="Usar mi ubicación actual" title="Usar mi ubicación actual"><svg viewBox="0 0 16 16" width="13" height="13" fill="none" stroke="currentColor" stroke-width="1.3"><circle cx="8" cy="8" r="4.2"/><circle cx="8" cy="8" r="1.3" fill="currentColor"/><path d="M8 1v2.4M8 12.6V15M1 8h2.4M12.6 8H15"/></svg></button></div></label>
        </div>
        <div class="dlb-map" data-map="${n}"></div>
      </div>
      <div class="dlb-row c4">${gauge(k("depth"), "Prof. máx", "m")}${gauge(k("time"), "Tiempo", "min")}${gauge(k("temp"), "Agua", "°C")}${gauge(k("vis"), "Visib.", "m")}</div>
      <div class="dlb-row c4">${fld(k("tin"), "Entrada", "In", "hh:mm")}${fld(k("tout"), "Salida", "Out", "hh:mm")}${fld(k("pstart"), "Bar inicio", "", "", 'inputmode="numeric"')}${fld(k("pend"), "Bar final", "", "", 'inputmode="numeric"')}</div>
      <div class="dlb-row" style="grid-template-columns:.7fr 1fr 1fr 1.6fr">${fld(k("weight"), "Lastre kg", "", "", 'inputmode="decimal"')}${fld(k("suit"), "Traje", "Suit")}${fld(k("gas"), "Gas", "Mix")}${fld(k("buddy"), "Compañero", "Buddy", "", `list="${uid}-friends"`)}</div>
      <div class="dlb-chips" role="group" aria-label="Tipo de inmersión">${TYPES.map(([t, l]) => `<label class="dlb-chip"><input type="checkbox" data-k="${k("t_" + t)}" id="d-${n}-t-${t}"><b>${l}</b></label>`).join("")}</div>
      <label class="dlb-f"><span>Observaciones · vida marina <i>Notes</i></span><textarea data-k="${k("notes")}" id="d-${n}-notes" rows="2"></textarea></label>
      <div class="dlb-foot">
        <div style="display:flex;flex-direction:column;gap:8px;min-width:0">${fld(k("sign"), "Firma / nº instructor", "Verified by")}<div class="dlb-mrz" data-mrz="${n}"></div></div>
        <div class="dlb-stampbox"><span>Sello<br>Stamp</span><div class="dlb-stamp" data-stamp="${n}"></div></div>
      </div>
    </div><div class="dlb-pno">${pno}</div>`;
  }

  function holderPage() {
    const ag = ["", "PADI", "SSI", "CMAS", "FEDAS", "NAUI", "SDI / TDI", "RAID", "GUE", "Otra"];
    return `${compassWM()}<div class="dlb-pg">
      <div class="dlb-head"><div class="dlb-title">TITULAR <small>Holder</small></div><div class="dlb-title" style="font-size:10px">LOG Nº 01</div></div>
      <div class="dlb-holder">
        <label class="dlb-photo" tabindex="0" aria-label="Añadir foto del titular"><span>Foto<br>Photo</span><input type="file" accept="image/*" data-photo></label>
        <div class="dlb-holder-fields">${fld("o:last", "Apellidos", "Surname")}${fld("o:first", "Nombre", "Given names")}${fld("o:nat", "Nacionalidad", "Nationality")}</div>
      </div>
      <div class="dlb-row c2">
        <label class="dlb-f"><span>Agencia <i>Agency</i></span><select data-k="o:agency" id="o-agency">${ag.map(a => `<option value="${a}">${a}</option>`).join("")}</select></label>
        ${fld("o:level", "Nivel", "Certification")}</div>
      <div class="dlb-row c2">${fld("o:certno", "Nº certificación", "Cert. no.")}${fld("o:certdate", "Fecha cert.", "Date", "dd/mm/aaaa")}</div>
      <div class="dlb-row c2">${fld("o:prev", "Inmersiones previas", "Prior dives", "", 'inputmode="numeric"')}${fld("o:ins", "Seguro de buceo", "Insurance")}</div>
      ${fld("o:emerg", "Contacto de emergencia", "Emergency contact")}
      <div class="dlb-foot dlb-foot-holder">
        <div style="display:flex;flex-direction:column;gap:8px;min-width:0">${fld("o:sign", "Firma del titular", "Signature")}<div class="dlb-mrz" data-mrz="o"></div></div>
        <div class="dlb-qrbox"><div class="dlb-qr" data-qr></div><span>Mi QR · <i>buddy</i></span></div>
      </div>
    </div><div class="dlb-pno">3</div>`;
  }

  function summaryPage(pno) {
    return `${compassWM()}<div class="dlb-pg">
      <div class="dlb-head"><div class="dlb-title">RESUMEN <small>Summary</small></div></div>
      <div class="dlb-stats">
        <div class="dlb-stat"><span>Inmersiones registradas</span><b data-sum="count">0</b></div>
        <div class="dlb-stat"><span>Tiempo bajo el agua</span><b data-sum="time">0<small>h</small></b></div>
        <div class="dlb-stat"><span>Profundidad máxima</span><b data-sum="depth">0<small>m</small></b></div>
        <div class="dlb-stat"><span>Lugares · países</span><b data-sum="sites">0</b></div>
      </div>
      <div class="dlb-f"><span>Mapa de inmersiones <i>Dive map</i></span></div>
      <div class="dlb-world" data-world></div>
      <div class="dlb-f"><span>Sellos <i>Stamps</i></span></div>
      <div class="dlb-mini" data-sum="stamps"></div>
      <div class="dlb-actions">
        <button type="button" data-act="add">Añadir 10 páginas</button>
        <button type="button" data-act="cover" hidden></button>
        <button type="button" data-act="export">Exportar copia</button>
        <button type="button" data-act="import">Importar copia</button><input type="file" accept="application/json,.json" data-import>
      </div>
      <div class="dlb-note" data-note aria-live="polite"></div>
    </div><div class="dlb-pno">${pno}</div>`;
  }

  /* ---------- utilidades de datos (compartidas por las dos vistas) ---------- */
  function divesOf(v) {
    const dives = {};
    Object.keys(v).forEach(k => { const m = k.match(/^d:(\d+):(\w+)$/); if (m) (dives[m[1]] = dives[m[1]] || {})[m[2]] = v[k]; });
    return Object.keys(dives).map(Number).sort((a, b) => a - b).map(n => ({ n, ...dives[n] }))
      .filter(d => d.site || d.date || d.depth || d.time);
  }
  function statsOf(v) {
    const list = divesOf(v);
    return {
      list,
      prev: parseInt(v["o:prev"], 10) || 0,
      minutes: list.reduce((s, d) => s + num(d.time), 0),
      depth: list.reduce((m, d) => Math.max(m, num(d.depth)), 0),
      sites: new Set(list.map(d => (d.site || "").trim().toLowerCase()).filter(Boolean)).size,
      countries: new Set(list.map(d => (d.country || "").trim().toLowerCase()).filter(Boolean)).size
    };
  }
  const fmtTime = m => `${Math.floor(m / 60)} h ${Math.round(m % 60)} min`;

  /* =========================================================
     Vista pasaporte: un libro de verdad (v50.58)
     Dos páginas rectas sobre las tapas azul marino, que asoman alrededor; lomo en el centro, grosor de las hojas en
     los bordes y sombra debajo. Una hoja se pasa arrastrando su esquina (se dobla por una línea y gira sobre el
     lomo), con un clic o un toque en el borde, con las flechas ‹ › y con ← →. Un móvil en vertical ve una sola
     página y la pasa deslizando el dedo. Con «reducir movimiento» el cambio es un fundido. Sin librerías: la
     geometría del doblez está aquí (fold) y solo se dibuja mientras una hoja se mueve.
     ========================================================= */
  const ART_2X = false;   // true cuando existan assets/page-*@2x.webp (scripts/fotos/preparar_paginas_logbook.py)
  const RM = window.matchMedia ? window.matchMedia("(prefers-reduced-motion: reduce)") : null;
  const reduced = () => !!(RM && RM.matches);
  const ease = k => k < .5 ? 4 * k * k * k : 1 - Math.pow(-2 * k + 2, 3) / 2;
  // transformación afín: [a, b, c, d, e, f] → x' = a·x + c·y + e, y' = b·x + d·y + f (como matrix() de CSS)
  const mul = (m, n) => [m[0] * n[0] + m[2] * n[1], m[1] * n[0] + m[3] * n[1], m[0] * n[2] + m[2] * n[3], m[1] * n[2] + m[3] * n[3],
    m[0] * n[4] + m[2] * n[5] + m[4], m[1] * n[4] + m[3] * n[5] + m[5]];
  const apply = (m, p) => ({ x: m[0] * p.x + m[2] * p.y + m[4], y: m[1] * p.x + m[3] * p.y + m[5] });
  const matrix = m => `matrix(${m.map(v => +v.toFixed(5)).join(",")})`;
  const polygon = pts => pts.length > 2 ? `polygon(${pts.map(p => `${p.x.toFixed(2)}px ${p.y.toFixed(2)}px`).join(",")})` : "polygon(0 0,0 0,0 0)";
  const ID = [1, 0, 0, 1, 0, 0], MIRROR = [-1, 0, 0, 1, W, 0];   // MIRROR: x → W − x (su propia inversa)
  // la parte del polígono donde sign·((X − M)·d) ≥ 0
  function halfPlane(pts, M, d, sign) {
    const s = p => sign * ((p.x - M.x) * d.x + (p.y - M.y) * d.y), out = [];
    pts.forEach((a, i) => {
      const b = pts[(i + 1) % pts.length], sa = s(a), sb = s(b);
      if (sa >= 0) out.push(a);
      if ((sa >= 0) !== (sb >= 0)) { const t = sa / (sa - sb); out.push({ x: a.x + (b.x - a.x) * t, y: a.y + (b.y - a.y) * t }); }
    });
    return out;
  }
  // El doblez de una hoja cuya esquina exterior C (arriba o abajo) se lleva al punto T. Coordenadas de la página que
  // se pasa: el lomo en x = 0 y la página de 0 a W. El papel no se estira: T queda a menos de W del extremo del lomo
  // en el mismo borde y a menos de la diagonal del otro.
  function fold(T, top) {
    const C = { x: W, y: top ? 0 : H }, B = { x: 0, y: top ? 0 : H }, A = { x: 0, y: top ? H : 0 };
    const lim = (O, r) => { const dx = T.x - O.x, dy = T.y - O.y, l = Math.hypot(dx, dy); if (l > r) T = { x: O.x + dx * r / l, y: O.y + dy * r / l }; };
    lim(B, W); lim(A, Math.hypot(W, H));
    const dx = T.x - C.x, dy = T.y - C.y, l = Math.hypot(dx, dy);
    if (l < .5) return null;
    const d = { x: dx / l, y: dy / l }, M = { x: (C.x + T.x) / 2, y: (C.y + T.y) / 2 }, k = 2 * (M.x * d.x + M.y * d.y);
    const rect = [{ x: 0, y: 0 }, { x: W, y: 0 }, { x: W, y: H }, { x: 0, y: H }];
    return { T, M, d, l, flat: halfPlane(rect, M, d, 1), lifted: halfPlane(rect, M, d, -1),
      R: [1 - 2 * d.x * d.x, -2 * d.x * d.y, -2 * d.x * d.y, 1 - 2 * d.y * d.y, k * d.x, k * d.y] };   // simetría en la línea del doblez
  }
  const INTERACTIVE = "input,textarea,select,button,a,label,[data-act],[contenteditable],.dlb-photo,.dlb-chip,.dlb-locate";
  const ICON_PREV = `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M14.5 5.5 8 12l6.5 6.5"/></svg>`;
  const ICON_NEXT = `<svg viewBox="0 0 24 24" width="22" height="22" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M9.5 5.5 16 12l-6.5 6.5"/></svg>`;

  class Logbook {
    constructor(root, ctrl) {
      this.root = root;
      this.ctrl = ctrl;
      this.uid = ctrl.uid + "p";
      this.assets = ctrl.assets;
      this.cur = 0; this.side = "right"; this.single = false; this.scale = 1;
      this.ts = null; this.anim = null; this.grab = null; this.peekKey = "";
      this.mount();
      this.build();
      this.bind();
      this.layout();
    }
    get data() { return this.ctrl.data; }
    get theme() { return this.ctrl.theme; }
    save() { this.ctrl.save(); }

    mount() {
      const s = this.root.style;
      s.setProperty("--dlb-leather-tex", `url("${this.assets}leather.jpg")`);
      s.setProperty("--dlb-paper-tex", `url("${this.assets}paper.jpg")`);
      s.setProperty("--pw", W + "px"); s.setProperty("--ph", H + "px"); s.setProperty("--pp", P + "px");
      this.root.innerHTML = `
        <svg width="0" height="0" style="position:absolute" aria-hidden="true"><filter id="${this.uid}-ink"><feTurbulence type="fractalNoise" baseFrequency=".85" numOctaves="2" seed="4" result="n"/><feColorMatrix in="n" type="matrix" values="0 0 0 0 0  0 0 0 0 0  0 0 0 0 0  0 0 0 -2.2 1.9" result="m"/><feComposite in="SourceGraphic" in2="m" operator="in"/></filter></svg>
        <datalist id="${this.uid}-friends"></datalist>
        <div class="dlb-stage">
          <div class="dlb-scale"><div class="dlb-book is-closed-front">
            <div class="dlb-ground"></div><div class="dlb-stack l"></div><div class="dlb-stack r"></div>
            <div class="dlb-leaves"></div>
            <div class="dlb-under" hidden><div class="dlb-under-shade"></div></div>
            <div class="dlb-spine"></div>
          </div></div>
          <button type="button" class="dlb-arrow" data-nav="prev" aria-label="Página anterior">${ICON_PREV}</button>
          <button type="button" class="dlb-arrow" data-nav="next" aria-label="Página siguiente">${ICON_NEXT}</button>
        </div>
        <div class="dlb-controls">
          <span class="dlb-count" aria-hidden="true"></span>
          <span class="dlb-label" aria-live="polite"></span>
          <button type="button" class="dlb-close" data-nav="close">Cerrar el libro</button>
        </div>`;
      const q = c => this.root.querySelector(c);
      this.stage = q(".dlb-stage"); this.scaleEl = q(".dlb-scale"); this.book = q(".dlb-book");
      this.leavesEl = q(".dlb-leaves"); this.stackL = q(".dlb-stack.l"); this.stackR = q(".dlb-stack.r");
      this.under = q(".dlb-under"); this.underShade = q(".dlb-under-shade"); this.spine = q(".dlb-spine");
      this.countEl = q(".dlb-count"); this.labelEl = q(".dlb-label"); this.closeEl = q(".dlb-close");
      this.prevEl = q('.dlb-arrow[data-nav="prev"]'); this.nextEl = q('.dlb-arrow[data-nav="next"]');
      this.renderFriends();
    }

    build() {
      if (this.anim) this.finish();
      if (this.ts) this.end(false);
      const A = this.assets, D = this.data.pages, faces = [];
      const art = name => `<picture><source type="image/webp" srcset="${A}${name}.webp${ART_2X ? `, ${A}${name}@2x.webp 2x` : ""}"><img src="${A}${name}.jpg" alt="" draggable="false" decoding="async"></picture>`;
      faces.push([{ kind: "cover", html: frontCoverSVG(this.uid + "f", this.theme, this.data.cover), name: "Portada" },
                  { kind: "art", html: art("page-left"), name: "Guarda" }]);
      faces.push([{ kind: "art", html: art("page-right"), name: "Introducción" },
                  { kind: "paper", html: holderPage(), name: "Titular" }]);
      for (let i = 0; i < D; i++) {
        const a = i * 2 + 1, b = a + 1;
        faces.push([{ kind: "paper", html: divePage(a, a + 3, A, this.uid), name: "Inmersión " + a, dive: a },
                    { kind: "paper", html: divePage(b, b + 3, A, this.uid), name: "Inmersión " + b, dive: b }]);
      }
      faces.push([{ kind: "paper", html: summaryPage(D * 2 + 4), name: "Resumen" },
                  { kind: "cover", html: backCoverSVG(this.uid + "b", this.theme), name: "Contraportada" }]);
      this.faces = faces;
      this.N = faces.length;
      this.cur = Math.min(this.cur, this.N);
      const N = this.N;
      // una hoja tiene dos caras (front: página derecha; back: la izquierda cuando se ha pasado). Las tapas son hojas
      // duras, un poco más grandes que el papel; la guarda y el resumen van pegados a ellas.
      const face = (f, which, hard) => {
        const side = which === "front" ? "r" : "l";
        if (f.kind === "cover") return `<div class="dlb-face ${which} dlb-cover">${f.html}</div>`;
        if (hard) return `<div class="dlb-face ${which} dlb-board"><div class="dlb-sheet ${side} dlb-${f.kind}">${f.html}</div></div>`;
        return `<div class="dlb-face ${which} dlb-sheet ${side} dlb-${f.kind}">${f.html}</div>`;
      };
      this.leavesEl.innerHTML = faces.map((f, i) => {
        const hard = i === 0 || i === N - 1;
        return `<div class="dlb-leaf${hard ? " hard" : ""}" data-i="${i}">${face(f[0], "front", hard)}${face(f[1], "back", hard)}</div>`;
      }).join("");
      this.leaves = [...this.leavesEl.children];

      this.root.querySelectorAll("[data-k]").forEach(el => {
        const v = this.data.v[el.dataset.k];
        if (el.type === "checkbox") el.checked = !!v; else if (v != null) el.value = v;
      });
      this.setPhoto(this.data.photo);
      for (let n = 1; n <= D * 2; n++) { this.applyVerified(n); this.updateStamp(n, false); this.updateMRZ(n); }
      this.updateMRZ("o");
      this.renderQR();
      this.updateSummary();
      this.updateCoverButton();
      this.renderMaps();
      this.update();
    }

    /* ---- mapas ---- */
    renderMaps() {
      const v = this.data.v;
      let need = false;
      this.root.querySelectorAll("[data-map]").forEach(el => { const n = +el.dataset.map; if (parsePos(v[`d:${n}:pos`])) need = true; this.renderMap(n); });
      this.renderWorld();
      if (need && !GEO.polys && !this._geoWait) {
        this._geoWait = true;
        loadGeo(this.ctrl.mapData).then(() => { this._geoWait = false; this._geoDone = true; this.renderMaps(); });
      }
    }
    renderMap(n) {
      const el = this.root.querySelector(`[data-map="${n}"]`);
      if (!el) return;
      const pos = parsePos(this.data.v[`d:${n}:pos`]);
      el.innerHTML = pos ? chartSVG(`${this.uid}-m${n}`, pos, GEO.polys, this.theme, 138, 122, this.ctrl.mapKm) : emptyChartSVG(138, 122, this.theme);
      el.classList.toggle("has-pos", !!pos);
      if (pos && !GEO.polys && !this._geoWait && !this._geoDone) { this._geoWait = true; loadGeo(this.ctrl.mapData).then(() => { this._geoWait = false; this._geoDone = true; this.renderMaps(); }); }
    }
    renderWorld() {
      const el = this.root.querySelector("[data-world]");
      if (!el) return;
      const v = this.data.v, pts = [];
      for (let n = 1; n <= this.data.pages * 2; n++) { const p = parsePos(v[`d:${n}:pos`]); if (p) pts.push({ lat: p.lat, lon: p.lon, verified: !!this.data.verified[n] }); }
      el.innerHTML = worldSVG(this.uid + "-w", pts, GEO.polys, this.theme, 336, 118,
        pts.length ? (this._geoDone ? "Mapa no disponible sin conexión" : "Cargando el mapa…") : "Las inmersiones con posición GPS aparecerán aquí");
      if (pts.length && !GEO.polys && !this._geoWait && !this._geoDone) { this._geoWait = true; loadGeo(this.ctrl.mapData).then(() => { this._geoWait = false; this._geoDone = true; this.renderMaps(); }); }
    }
    locate(n) {
      const el = this.root.querySelector(`[data-k="d:${n}:pos"]`);
      if (!el || el.readOnly) return;
      const fail = () => { el.placeholder = "No disponible"; setTimeout(() => el.placeholder = "38.16, -0.47", 2500); };
      if (!navigator.geolocation) return fail();
      try {
        navigator.geolocation.getCurrentPosition(p => {
          el.value = `${p.coords.latitude.toFixed(5)}, ${p.coords.longitude.toFixed(5)}`;
          this.onInput(el); this.renderMap(n); this.renderWorld();
        }, fail, { enableHighAccuracy: true, timeout: 10000 });
      } catch (e) { fail(); }
    }

    bind() {
      const r = this.root;
      r.addEventListener("click", e => {
        const nav = e.target.closest("[data-nav]");
        if (nav) { const a = nav.dataset.nav; a === "close" ? this.close() : this[a](); return; }
        const act = e.target.closest("[data-act]");
        if (act) { this.action(act.dataset.act); return; }
        const loc = e.target.closest("[data-locate]");
        if (loc) { this.locate(+loc.dataset.locate); return; }
        if (performance.now() - (this.acted || 0) < 450) return;   // ya lo hizo el gesto (arrastrar o tocar el borde)
        const cov = e.target.closest(".dlb-cover");
        if (cov) { cov.classList.contains("front") ? this.next() : this.prev(); }
      });
      r.addEventListener("input", e => this.onInput(e.target));
      r.addEventListener("change", e => {
        if (e.target.matches("[data-photo]")) this.readPhoto(e.target);
        else if (e.target.matches("[data-import]")) this.importFile(e.target);
        else this.onInput(e.target);
      });
      r.addEventListener("keydown", e => {
        if (e.target.classList.contains("dlb-photo") && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); e.target.querySelector("input").click(); }
      });
      // en una sola página, escribir en la otra página de las dos abiertas la trae a la vista
      r.addEventListener("focusin", e => {
        if (!this.single) return;
        const sheet = e.target.closest(".dlb-sheet");
        if (!sheet) return;
        const want = sheet.classList.contains("r") ? "right" : "left";
        if (want !== this.side) { this.side = want; this.update(); }
      });
      this.stage.addEventListener("scroll", () => { this.stage.scrollLeft = 0; this.stage.scrollTop = 0; });
      this.stage.addEventListener("pointerdown", e => this.down(e));
      this.stage.addEventListener("pointermove", e => this.move(e));
      this.stage.addEventListener("pointerup", e => this.up(e));
      this.stage.addEventListener("pointercancel", e => this.up(e, true));
      this.stage.addEventListener("pointerleave", e => { if (!this.grab && this.peekKey) this.peek(null); });
      this.stage.addEventListener("dragstart", e => e.preventDefault());
      const onKey = e => {
        if (!r.isConnected) { document.removeEventListener("keydown", onKey); return; }
        if (/INPUT|TEXTAREA|SELECT/.test(e.target.tagName) || e.target.isContentEditable) return;
        if (r.offsetParent === null) return; // vista oculta
        const b = r.getBoundingClientRect();
        if (b.bottom < 0 || b.top > innerHeight) return;
        if (e.key === "ArrowRight") this.next(); else if (e.key === "ArrowLeft") this.prev();
      };
      document.addEventListener("keydown", onKey);
      // el alto de la ventana cuenta (el libro cabe entero sin desplazarse): también al girar el móvil
      let rq = 0;
      const onResize = () => { if (!r.isConnected) { removeEventListener("resize", onResize); return; } cancelAnimationFrame(rq); rq = requestAnimationFrame(() => this.layout()); };
      addEventListener("resize", onResize);
      if ("ResizeObserver" in window) new ResizeObserver(() => this.layout()).observe(r);
    }

    /* ---- tamaño: el mayor que quepa entero (90 % del ancho, 85 % del alto bajo la cabecera) ---- */
    layout() {
      const cw = this.root.clientWidth;
      if (!cw) return;
      const vp = (typeof this.ctrl.viewport === "function" && this.ctrl.viewport()) || {};
      const vh = Math.max(260, innerHeight - (vp.top || 0) - (vp.bottom || 0));
      const single = cw < 600 && (innerHeight >= innerWidth || cw < 420);
      const bw = (single ? W : 2 * W) + 2 * P, bh = H + 2 * P;
      const s = Math.max(.3, Math.min(.9 * cw / bw, .85 * (vh - 56) / bh, 1.5));
      const changed = single !== this.single;
      this.single = single; this.scale = s; this.bw = bw;
      const pad = 14, left = (cw - bw * s) / 2;
      this.scaleEl.style.width = bw + "px"; this.scaleEl.style.height = bh + "px";
      this.scaleEl.style.left = left.toFixed(1) + "px"; this.scaleEl.style.top = pad + "px";
      this.scaleEl.style.transform = `scale(${s.toFixed(4)})`;
      this.stage.style.height = Math.round(bh * s + 2 * pad) + "px";
      const ax = Math.max(2, left - 50), ay = pad + bh * s / 2 - 22;
      this.prevEl.style.left = ax + "px"; this.nextEl.style.right = ax + "px";
      this.prevEl.style.top = this.nextEl.style.top = ay + "px";
      this.stage.classList.toggle("is-single", single);
      this.stage.classList.toggle("arrows-in", left < 54);
      if (changed) {
        if (this.anim) this.finish();
        if (this.ts) this.end(false);
        this.side = this.cur === this.N ? "left" : "right";
      }
      this.update();
    }

    // dónde queda el libro: la tapa sola centrada si está cerrado; en una sola página, la página que se ve
    place(cur, side) {
      const N = this.N;
      let c;   // centro de lo que se ve, en coordenadas del libro (lomo en x = W)
      if (cur === 0) c = 1.5 * W + P / 2;
      else if (cur === N) c = W / 2 - P / 2;
      else if (!this.single) c = W;
      else c = side === "left" ? W / 2 : 1.5 * W;
      const tx = this.bw / 2 - P - c;
      this.book.style.transform = `translate(${tx.toFixed(1)}px,0)`;
    }

    /* ---- gestos: arrastrar la esquina, tocar el borde, deslizar ---- */
    toBook(cx, cy) { const b = this.book.getBoundingClientRect(); return { x: (cx - b.left) / this.scale, y: (cy - b.top) / this.scale }; }
    // la página que se puede pasar bajo el punto: «next» la derecha, «prev» la izquierda; u: coordenadas de esa página
    target(p) {
      const N = this.N, cur = this.cur;
      if (p.x >= W) { if (cur < N && (!this.single || this.side === "right")) return { dir: "next", u: { x: p.x - W, y: p.y } }; }
      else if (cur > 0 && (!this.single || this.side === "left")) return { dir: "prev", u: { x: W - p.x, y: p.y } };
      return null;
    }
    zone(u) {
      const r = .22 * W;
      if (u.x > W + P + 4 || u.y < -P - 4 || u.y > H + P + 4) return "out";
      if (Math.hypot(W - u.x, H - u.y) < r) return "corner";
      if (Math.hypot(W - u.x, u.y) < r) return "corner";
      return u.x > W * .86 ? "edge" : "body";
    }
    down(e) {
      if (e.button > 0 || this.grab || !e.isPrimary) return;
      const p = this.toBook(e.clientX, e.clientY), t = this.target(p);
      const zone = t ? this.zone(t.u) : "body";
      // los campos se usan como siempre. Con el ratón, la hoja se coge por la esquina o el borde aunque haya texto impreso
      // de una casilla; con el dedo, un deslizamiento puede empezar en cualquier casilla (un toque la sigue abriendo),
      // pero no en un botón ni en el campo que se está escribiendo
      const hit = e.target.closest(INTERACTIVE);
      if (hit) {
        if (e.pointerType === "mouse" ? hit.matches("input,textarea,select,button,a,[contenteditable],[data-act],.dlb-locate")
          : (hit === document.activeElement || hit.matches("button,a,select,[contenteditable],[data-act],.dlb-locate"))) return;
      }
      if (zone === "out") return;
      if (this.peekKey) this.peek(null);
      if (this.anim) this.finish();
      if (e.pointerType === "mouse" && zone === "body") return;   // con el ratón se pasa desde la esquina o el borde
      this.grab = { id: e.pointerId, x: e.clientX, y: e.clientY, t: performance.now(), dir: t && t.dir, u0: t && t.u, zone,
        top: !!t && t.u.y < H / 2, moving: false, drag: false, swipe: false };
      if (e.pointerType === "mouse") e.preventDefault();
    }
    move(e) {
      const g = this.grab;
      if (!g) { if (e.pointerType === "mouse" && !this.anim && !reduced()) this.hover(e); return; }
      if (e.pointerId !== g.id) return;
      const dx = e.clientX - g.x, dy = e.clientY - g.y;
      if (!g.moving) {
        if (Math.hypot(dx, dy) < 8) return;
        if (g.zone === "body" && Math.abs(dy) > Math.abs(dx)) { this.grab = null; return; }   // desplazar la página
        g.moving = true;
        // la hoja sigue al dedo cuando el gesto va hacia donde se pasa esa página; si no, es un deslizamiento
        const way = dx < 0 ? "next" : "prev";
        if (!g.dir || reduced() || (g.zone === "body" && way !== g.dir) || !this.start(g.dir, g.top)) { g.swipe = true; return; }
        g.drag = true;
        try { this.stage.setPointerCapture(g.id); } catch (err) { /* sin captura: sigue igual */ }
      }
      if (g.drag) this.dragTo(e.clientX, e.clientY);
    }
    up(e, cancel) {
      const g = this.grab;
      if (!g || e.pointerId !== g.id) return;
      this.grab = null;
      const dx = e.clientX - g.x, dt = performance.now() - g.t;
      if (g.drag) {
        this.acted = performance.now();
        if (cancel) return this.play(false);
        const fast = Math.abs(dx) > 30 && dt < 320, toward = (dx < 0) === (g.dir === "next");
        const s = this.ts, past = s.hard ? s.p > .5 : (s.T ? s.T.x < W / 2 : false);
        return this.play(fast ? toward : past);
      }
      if (cancel) return;
      if (g.swipe) { if (Math.abs(dx) > 40 && Math.abs(dx) > Math.abs(e.clientY - g.y)) { this.acted = performance.now(); dx < 0 ? this.next() : this.prev(); } return; }
      if (!g.moving && g.dir && (g.zone === "edge" || g.zone === "corner")) { this.acted = performance.now(); g.dir === "next" ? this.next() : this.prev(); }
    }
    dragTo(cx, cy) {
      const s = this.ts, g = this.grab;
      if (!s || !g) return;
      const p = this.toBook(cx, cy), u = s.dir === "next" ? { x: p.x - W, y: p.y } : { x: W - p.x, y: p.y };
      if (s.hard) { const vx = (W + P) + (u.x - g.u0.x); this.setP(Math.min(1, Math.max(0, (W + P - vx) / (2 * (W + P))))); return; }
      // la esquina se mueve lo mismo que el dedo (aunque se coja la hoja por otro sitio)
      const C = { x: W, y: s.top ? 0 : H };
      this.setT({ x: C.x + (u.x - g.u0.x), y: C.y + (u.y - g.u0.y) });
    }
    // con el ratón cerca de una esquina, la esquina se levanta un poco
    hover(e) {
      const p = this.toBook(e.clientX, e.clientY), t = this.target(p);
      let want = null;
      if (t && this.zone(t.u) === "corner") want = { dir: t.dir, top: t.u.y < H / 2 };
      this.peek(want);
    }
    peek(want) {
      const key = want ? want.dir + (want.top ? "-top" : "") : "";
      if (key === this.peekKey) return;
      if (this.peekKey && this.ts) this.end(false);
      this.peekKey = ""; this.stage.style.cursor = "";
      if (!want || this.anim || !this.start(want.dir, want.top)) return;
      this.peekKey = key;
      this.stage.style.cursor = "grab";
      if (this.ts.hard) this.setP(.05); else this.setT({ x: W - 44, y: want.top ? 30 : H - 30 });
    }

    /* ---- una hoja que se mueve ---- */
    start(dir, top) {
      if (this.ts) return false;
      const j = dir === "next" ? this.cur : this.cur - 1, leaf = this.leaves[j];
      if (!leaf) return false;
      const hard = leaf.classList.contains("hard"), front = leaf.children[0], back = leaf.children[1];
      const s = this.ts = { dir, top: !!top, j, leaf, hard, front, back, T: null, p: 0, side0: this.side };
      leaf.style.display = ""; leaf.dataset.state = "turn"; leaf.style.zIndex = 3 * this.N + 5; leaf.inert = true;
      const k = this.leaves[dir === "next" ? j + 1 : j - 1];
      if (k) k.style.display = "";
      if (hard) { leaf.classList.add("is-turning"); this.setP(0); return true; }
      const flap = dir === "next" ? back : front;
      flap.style.left = "0px";
      s.shade = document.createElement("div"); s.shade.className = "dlb-flap-shade"; flap.appendChild(s.shade);
      this.under.style.left = (dir === "next" ? W : 0) + "px"; this.under.style.zIndex = 3 * this.N + 3; this.under.hidden = false;
      this.setT({ x: W, y: top ? 0 : H });
      return true;
    }
    // hoja dura (las tapas): gira sobre el lomo en 3D. p: 0 sin pasar, 1 pasada
    setP(p) {
      const s = this.ts;
      s.p = p;
      const deg = s.dir === "next" ? -180 * p : -180 * (1 - p);
      s.leaf.style.transform = `perspective(${(2.6 * W).toFixed(0)}px) rotateY(${deg.toFixed(2)}deg)`;
      s.leaf.style.setProperty("--turn", (Math.sin(Math.PI * p) * .55).toFixed(3));
    }
    // hoja de papel: la esquina en T (coordenadas de la página que se pasa)
    setT(T) {
      const s = this.ts, f = fold(T, s.top), fwd = s.dir === "next";
      const flat = fwd ? s.front : s.back, flap = fwd ? s.back : s.front;
      s.T = f ? f.T : { x: W, y: s.top ? 0 : H };
      if (!f) { flat.style.clipPath = ""; flap.style.visibility = "hidden"; this.underShade.style.opacity = "0"; return; }
      flap.style.visibility = "";
      const F = fwd ? [1, 0, 0, 1, W, 0] : [-1, 0, 0, 1, W, 0];   // página que se pasa → libro
      const Q = fwd ? MIRROR : ID;                               // cara que se levanta → página (el mismo papel por detrás)
      const Pf = fwd ? ID : MIRROR;                              // página → cara que se queda plana
      flat.style.clipPath = polygon(f.flat.map(p => apply(Pf, p)));
      flap.style.clipPath = polygon(f.lifted.map(p => apply(Q, p)));
      flap.style.transform = matrix(mul(F, mul(f.R, Q)));
      // sombras: sobre la página que aparece y sobre la hoja junto al doblez, más fuertes a mitad del giro
      const a = Math.sin(Math.PI * Math.min(1, f.l / (2 * W))), L = 2 * (W + H), n = { x: -f.d.y, y: f.d.x };
      const strip = [-f.d.x, -f.d.y, n.x, n.y, f.M.x - n.x * L / 2, f.M.y - n.y * L / 2];   // franja → página: del doblez hacia la esquina
      const us = this.underShade;
      us.style.width = Math.max(14, Math.min(W * .5, f.l * .5)).toFixed(1) + "px"; us.style.height = L + "px";
      us.style.transform = matrix(mul([1, 0, 0, 1, fwd ? -W : 0, 0], mul(F, strip)));
      us.style.opacity = (.25 + .6 * a).toFixed(3);
      const sh = s.shade;
      sh.style.width = Math.max(12, Math.min(W * .6, f.l * .55)).toFixed(1) + "px"; sh.style.height = L + "px";
      sh.style.transform = matrix(mul(Q, strip));
      sh.style.opacity = (.45 + .55 * a).toFixed(3);
    }
    tween(ms, step, done) {
      cancelAnimationFrame(this.raf);
      const t0 = performance.now();
      const a = this.anim = { step, done };
      const tick = now => {
        if (this.anim !== a) return;
        const k = Math.min(1, (now - t0) / ms);
        step(k);
        if (k < 1) this.raf = requestAnimationFrame(tick); else { this.anim = null; done(); }
      };
      this.raf = requestAnimationFrame(tick);
    }
    finish() { const a = this.anim; if (!a) return; cancelAnimationFrame(this.raf); this.anim = null; a.step(1); a.done(); }
    // termina el giro empezado (complete) o devuelve la hoja a su sitio
    play(complete, done) {
      const s = this.ts;
      if (!s) return;
      this.peekKey = "";
      if (s.hard) {
        const p0 = s.p, p1 = complete ? 1 : 0;
        this.tween(Math.max(180, TURN_MS * Math.abs(p1 - p0)), k => this.setP(p0 + (p1 - p0) * ease(k)), () => this.end(complete, done));
      } else {
        const C = { x: W, y: s.top ? 0 : H }, T0 = s.T || C, E = complete ? { x: -W, y: C.y } : C;
        const lift = complete ? (s.top ? 1 : -1) * H * .045 : 0;
        const ms = Math.max(180, TURN_MS * Math.min(1, Math.hypot(E.x - T0.x, E.y - T0.y) / (2 * W)));
        this.tween(ms, k => { const q = ease(k); this.setT({ x: T0.x + (E.x - T0.x) * q, y: T0.y + (E.y - T0.y) * q + lift * Math.sin(Math.PI * q) }); },
          () => this.end(complete, done));
      }
      // el libro se mueve a la vez: se abre o se cierra la tapa, o (una sola página) viene la página nueva
      if (complete) this.place(s.dir === "next" ? this.cur + 1 : this.cur - 1, s.dir === "next" ? "left" : "right");
    }
    end(complete, done) {
      const s = this.ts;
      if (!s) return;
      this.ts = null;
      if (complete) { this.cur += s.dir === "next" ? 1 : -1; this.side = s.dir === "next" ? "left" : "right"; }
      else this.side = s.side0;
      [s.front, s.back].forEach(f => { f.style.clipPath = ""; f.style.transform = ""; f.style.left = ""; f.style.visibility = ""; });
      s.leaf.style.transform = ""; s.leaf.classList.remove("is-turning"); s.leaf.style.removeProperty("--turn");
      if (s.shade) s.shade.remove();
      this.under.hidden = true;
      this.update();
      if (done) done(complete);
    }

    /* ---- navegación ---- */
    // un cambio sin pasar hoja: en una sola página, la otra página de las dos abiertas; con «reducir movimiento», todo
    change(fn) {
      if (reduced()) {
        this.stage.classList.add("is-fading");
        clearTimeout(this._fade);
        this._fade = setTimeout(() => { fn(); this.update(); this.stage.classList.remove("is-fading"); }, 150);
        return;
      }
      fn(); this.update();
    }
    next() {
      if (this.peekKey) this.peek(null);
      if (this.anim) this.finish();
      const N = this.N;
      if (this.single && this.cur > 0 && this.cur < N && this.side === "left") return this.change(() => { this.side = "right"; });
      if (this.cur >= N) return;
      if (reduced()) return this.change(() => { this.cur++; this.side = "left"; });
      if (this.start("next", false)) this.play(true);
    }
    prev() {
      if (this.peekKey) this.peek(null);
      if (this.anim) this.finish();
      const N = this.N;
      if (this.single && this.cur > 0 && this.cur < N && this.side === "right") return this.change(() => { this.side = "left"; });
      if (this.cur <= 0) return;
      if (reduced()) return this.change(() => { this.cur--; this.side = "right"; });
      if (this.start("prev", false)) this.play(true);
    }
    open() { if (this.cur === 0) this.next(); }
    close() { this.goTo(0, "right"); }
    // a una hoja lejana: salta sin animar hasta la anterior y pasa la última hoja
    goTo(target, side) {
      if (this.peekKey) this.peek(null);
      if (this.anim) this.finish();
      if (this.ts) this.end(false);
      target = Math.max(0, Math.min(this.N, target));
      const want = target === 0 ? "right" : target === this.N ? "left" : side || "right";
      const settle = () => { if (this.single && this.side !== want) this.change(() => { this.side = want; }); };
      if (target === this.cur) return settle();
      if (reduced()) return this.change(() => { this.cur = target; this.side = want; });
      const fwd = target > this.cur;
      this.cur = fwd ? target - 1 : target + 1;
      this.side = fwd ? "right" : "left";
      this.update();
      if (this.start(fwd ? "next" : "prev", false)) this.play(true, settle);
    }
    goToDive(n) {
      const leaf = Math.floor((n - 1) / 2) + 2;
      if (n % 2) this.goTo(leaf, "right"); else this.goTo(leaf + 1, "left");
    }
    showDive(n) {
      this.goToDive(n);
      setTimeout(() => { const box = this.root.querySelector(`[data-stamp="${n}"]`); if (box) { box.classList.remove("pop"); void box.offsetWidth; box.classList.add("pop"); } }, TURN_MS + 300);
    }

    // el libro quieto: qué hojas se ven, en qué orden, grosor de las hojas, sombra, indicador y flechas
    update() {
      const N = this.N, cur = this.cur;
      this.leaves.forEach((leaf, i) => {
        if (this.ts && leaf === this.ts.leaf) return;
        const flipped = i < cur, hard = leaf.classList.contains("hard");
        leaf.style.display = hard || (flipped ? i >= cur - 2 : i <= cur + 1) ? "" : "none";
        leaf.dataset.state = flipped ? "l" : "r";
        if (hard) leaf.style.transform = flipped ? "rotateY(-180deg)" : "";
        const board = hard && (i === 0 ? flipped : !flipped);   // la tapa debajo de las hojas
        leaf.style.zIndex = board ? 1 : flipped ? i + 3 : 2 * N - i + 3;
        const visible = this.single ? (this.side === "left" ? i === cur - 1 : i === cur) : (i === cur || i === cur - 1);
        leaf.inert = !visible;
      });
      this.place(cur, this.side);
      this.book.classList.toggle("is-closed-front", cur === 0);
      this.book.classList.toggle("is-closed-back", cur === N);
      this.book.classList.toggle("is-single", this.single);
      // grosor: unas líneas de papel en el borde, más en el lado con más hojas
      const a = mix(this.theme.paper, "#000000", .12), b = mix(this.theme.paper, "#ffffff", .2);
      const lines = (count, dir) => {
        if (count <= 0) return "none";
        const L = Math.min(4, Math.ceil(count / 3)), out = [];
        for (let j = 1; j <= L; j++) out.push(`${(dir * j * 1.15).toFixed(2)}px ${(j * .55).toFixed(2)}px 0 ${j % 2 ? a : b}`);
        return out.join(",");
      };
      const right = cur >= 1 && cur <= N - 2 ? N - 2 - cur : 0, left = cur >= 2 && cur <= N - 1 ? cur - 2 : 0;
      this.stackR.hidden = !right; this.stackL.hidden = !left;
      this.stackR.style.boxShadow = lines(right, 1); this.stackL.style.boxShadow = lines(left, -1);
      this.spine.hidden = cur === 0 || cur === N;
      this.spine.style.zIndex = 3 * N + 4;
      // indicador: páginas interiores (de la guarda al resumen)
      const total = 2 * N - 2, nm = (i, s) => (this.faces[i] && this.faces[i][s].name) || "";
      let count, label;
      if (cur === 0) { count = label = "PORTADA · TOCA PARA ABRIR"; }
      else if (cur === N) { count = label = "CONTRAPORTADA"; }
      else if (this.single) { const left = this.side === "left"; count = `${left ? 2 * cur - 1 : 2 * cur} / ${total}`; label = (left ? nm(cur - 1, 1) : nm(cur, 0)).toUpperCase(); }
      else {
        count = `${2 * cur - 1}–${2 * cur} / ${total}`;
        const l = this.faces[cur - 1][1], r = this.faces[cur][0];
        label = (l.dive && r.dive ? `INMERSIONES ${l.dive}–${r.dive}` : `${l.name} · ${r.name}`).toUpperCase();
      }
      this.countEl.textContent = count;
      this.labelEl.textContent = label;
      this.prevEl.disabled = cur === 0;
      this.nextEl.disabled = cur === N;
      this.closeEl.hidden = cur === 0;
    }

    onInput(el) {
      const k = el.dataset && el.dataset.k;
      if (!k || el.readOnly) return;
      if (el.type === "checkbox") { if (el.checked) this.data.v[k] = true; else delete this.data.v[k]; }
      else if (el.value === "") delete this.data.v[k]; else this.data.v[k] = el.value;
      const m = k.match(/^d:(\d+):(\w+)/);
      if (m) {
        const n = +m[1];
        if (m[2] === "buddy") {
          const f = this.ctrl.friends.find(x => x.name === el.value);
          if (f) this.data.v[`d:${n}:buddyId`] = f.id; else delete this.data.v[`d:${n}:buddyId`];
        }
        if (m[2] === "site" || m[2] === "date" || m[2] === "no") this.updateStamp(n, true);
        if (m[2] === "pos") { clearTimeout(this._pt); this._pt = setTimeout(() => { this.renderMap(n); this.renderWorld(); }, 450); }
        this.updateMRZ(n);
      } else this.updateMRZ("o");
      this.updateSummary();
      this.save();
    }

    applyVerified(n) {
      const ver = this.data.verified[n], badge = this.root.querySelector(`[data-verified="${n}"]`);
      if (!badge) return;
      badge.hidden = !ver;
      if (!ver) return;
      badge.textContent = `✓ Verificada por ${ver.center || "el centro"}`;
      (ver.locked || []).forEach(f => {
        const el = this.root.querySelector(`[data-k="d:${n}:${f}"]`);
        if (el) { el.readOnly = true; el.classList.add("dlb-locked"); el.title = "Dato registrado por el centro de buceo"; }
      });
    }

    updateStamp(n, animate) {
      const box = this.root.querySelector(`[data-stamp="${n}"]`);
      if (!box) return;
      const v = this.data.v, site = v[`d:${n}:site`], date = v[`d:${n}:date`];
      const has = !!(site && date);
      const was = box.dataset.on === "1";
      box.dataset.on = has ? "1" : "0";
      box.innerHTML = has ? stampSVG(this.uid, v[`d:${n}:no`] || n, site, date, this.data.verified[n]) : "";
      if (has && !was && animate) { box.classList.remove("pop"); void box.offsetWidth; box.classList.add("pop"); }
    }

    updateMRZ(n) {
      const el = this.root.querySelector(`[data-mrz="${n}"]`);
      if (!el) return;
      const v = this.data.v;
      if (n === "o") {
        const l1 = fit(`P<DVR${mrzClean(v["o:last"]) || "<"}<<${mrzClean(v["o:first"])}`, 34);
        const l2 = fit(`${fit(mrzClean(v["o:certno"]), 12)}${fit(mrzClean(v["o:agency"]), 5)}${fit(mrzClean(v["o:nat"]).slice(0, 3), 3)}${fit(mrzClean(v["o:level"]), 14)}`, 34);
        el.textContent = l1 + "\n" + l2;
      } else {
        const g = f => v[`d:${n}:${f}`];
        const no = String(g("no") || n).replace(/\D/g, "").padStart(4, "0");
        const l1 = fit(`DL<${no}<${mrzClean(g("site"))}<<${mrzClean(g("country"))}`, 33);
        const l2 = fit(`${String(g("date") || "").replace(/\D/g, "").padEnd(8, "<")}<${String(num(g("depth")) || "").padStart(3, "<")}M<${String(num(g("time")) || "").padStart(3, "<")}MIN<${mrzClean(g("gas")) || "<"}`, 33);
        el.textContent = l1 + "\n" + l2;
      }
    }

    updateSummary() {
      const q = s => this.root.querySelector(`[data-sum="${s}"]`);
      if (!q("count")) return;
      const st = statsOf(this.data.v);
      q("count").innerHTML = (st.list.length + st.prev) + (st.prev ? `<small> (${st.list.length} aquí)</small>` : "");
      q("time").innerHTML = `${Math.floor(st.minutes / 60)}<small>h</small> ${Math.round(st.minutes % 60)}<small>min</small>`;
      q("depth").innerHTML = `${st.depth}<small>m</small>`;
      q("sites").innerHTML = `${st.sites}<small> · ${st.countries}</small>`;
      const stamped = st.list.filter(d => d.site && d.date);
      q("stamps").innerHTML = stamped.length
        ? stamped.slice(-7).map(d => stampSVG(this.uid + "m", d.no || d.n, d.site, d.date, this.data.verified[d.n])).join("")
        : `<p>Los sellos aparecen cuando una inmersión tiene lugar y fecha.</p>`;
    }

    renderCover() {
      const face = this.leaves && this.leaves[0] && this.leaves[0].querySelector(".dlb-face.front");
      if (face) face.innerHTML = frontCoverSVG(this.uid + "f", this.theme, this.data.cover);
      this.updateCoverButton();
    }
    updateCoverButton() {
      const b = this.root.querySelector('[data-act="cover"]');
      if (!b) return;
      const c = this.data.cover;
      b.hidden = !(c && c.logo);
      if (c && c.logo) b.textContent = c.off ? `Usar portada de ${c.name || "mi centro"}` : "Usar portada clásica";
    }

    renderQR() {
      const box = this.root.querySelector("[data-qr]");
      if (!box) return;
      const p = this.ctrl.profile;
      const svg = qrSVG(p && (p.qrText || p.qr), this.theme.ink);
      if (svg) box.innerHTML = svg;
      else if (p && p.qrImage) box.innerHTML = `<img src="${esc(p.qrImage)}" alt="Código QR personal">`;
      else box.innerHTML = `<em>Aparece al<br>iniciar sesión</em>`;
    }
    renderFriends() {
      const dl = this.root.querySelector(`#${this.uid}-friends`);
      if (dl) dl.innerHTML = this.ctrl.friends.map(f => `<option value="${esc(f.name)}"></option>`).join("");
    }

    setPhoto(src) {
      const p = this.root.querySelector(".dlb-photo");
      if (!p) return;
      p.style.backgroundImage = src ? `url("${src}")` : "";
      p.classList.toggle("has-img", !!src);
    }
    readPhoto(input) {
      const f = input.files && input.files[0];
      if (!f) return;
      const fr = new FileReader();
      fr.onload = () => {
        const img = new Image();
        img.onload = () => {
          const c = document.createElement("canvas"); c.width = 240; c.height = 310;
          const s = Math.max(240 / img.width, 310 / img.height), w = img.width * s, h = img.height * s;
          c.getContext("2d").drawImage(img, (240 - w) / 2, (310 - h) / 2, w, h);
          this.data.photo = c.toDataURL("image/jpeg", .82);
          this.setPhoto(this.data.photo); this.save();
        };
        img.src = fr.result;
      };
      fr.readAsDataURL(f);
      input.value = "";
    }

    note(t) { const n = this.root.querySelector("[data-note]"); if (n) { n.textContent = t; clearTimeout(this._nt); this._nt = setTimeout(() => n.textContent = "", 4000); } }

    action(a) {
      if (a === "add") {
        if (this.data.pages >= 60) return this.note("Has llegado al máximo de 120 inmersiones en este cuaderno.");
        this.data.pages += 10; this.save();
        const keep = this.cur; this.build(); this.cur = Math.min(keep + 10, this.N - 1); this.update();
        this.note("Añadidas 20 inmersiones nuevas.");
      } else if (a === "cover") {
        const c = this.data.cover; if (!c) return;
        c.off = !c.off; this.save(); this.renderCover();
        this.note(c.off ? "Portada clásica activada." : `Portada de ${c.name || "tu centro"} activada.`);
      } else if (a === "export") {
        const json = JSON.stringify(this.data, null, 2);
        try {
          const url = URL.createObjectURL(new Blob([json], { type: "application/json" }));
          const link = document.createElement("a"); link.href = url; link.download = "dive-logbook.json";
          document.body.appendChild(link); link.click(); link.remove(); setTimeout(() => URL.revokeObjectURL(url), 2000);
        } catch (e) { /* descarga no disponible */ }
        if (navigator.clipboard) navigator.clipboard.writeText(json).then(() => this.note("Copia descargada y copiada al portapapeles."), () => this.note("Copia descargada."));
        else this.note("Copia descargada.");
      } else if (a === "import") {
        this.root.querySelector("[data-import]").click();
      }
    }
    importFile(input) {
      const f = input.files && input.files[0];
      if (!f) return;
      f.text().then(t => {
        const d = JSON.parse(t);
        if (!d || typeof d.v !== "object") throw 0;
        const keep = this.cur; this.ctrl.setData(d); this.cur = Math.min(keep, this.N - 1); this.update();
        this.note("Copia importada.");
      }).catch(() => this.note("Ese archivo no es una copia del logbook. Usa un .json exportado desde aquí."));
      input.value = "";
    }
  }

  /* =========================================================
     Vista clásica (lista integrada en la web) + controlador
     ========================================================= */
  const ICON_PASSPORT = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><rect x="4.5" y="2.5" width="15" height="19" rx="2"/><circle cx="12" cy="10" r="3.6"/><path d="M8.4 10h7.2M12 6.4c1.3 1.2 1.3 6 0 7.2M12 6.4c-1.3 1.2-1.3 6 0 7.2M9 17.5h6"/></svg>`;
  const ICON_LIST = `<svg viewBox="0 0 24 24" width="20" height="20" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" aria-hidden="true"><path d="M8 6.5h12M8 12h12M8 17.5h12"/><circle cx="4.2" cy="6.5" r=".9" fill="currentColor"/><circle cx="4.2" cy="12" r=".9" fill="currentColor"/><circle cx="4.2" cy="17.5" r=".9" fill="currentColor"/></svg>`;

  const F_DIVE = [
    ["no", "Nº", "", "numeric"], ["date", "Fecha", "dd/mm/aaaa"], ["site", "Lugar", "", "", "wide"], ["country", "País / región"], ["center", "Centro de buceo"],
    ["depth", "Prof. máx (m)", "", "decimal"], ["time", "Tiempo (min)", "", "numeric"], ["temp", "Agua (°C)", "", "decimal"], ["vis", "Visibilidad (m)", "", "decimal"],
    ["tin", "Entrada", "hh:mm"], ["tout", "Salida", "hh:mm"], ["pstart", "Bar inicio", "", "numeric"], ["pend", "Bar final", "", "numeric"],
    ["weight", "Lastre (kg)", "", "decimal"], ["suit", "Traje"], ["gas", "Gas"], ["buddy", "Compañero", "", "", "", "friends"],
    ["pos", "Posición GPS", "38.16, -0.47", "", "wide"],
    ["sign", "Firma / nº instructor", "", "", "wide"]
  ];
  const F_OWNER = [["first", "Nombre"], ["last", "Apellidos"], ["nat", "Nacionalidad"], ["agency", "Agencia"], ["level", "Nivel"], ["certno", "Nº certificación"],
    ["certdate", "Fecha certificación", "dd/mm/aaaa"], ["prev", "Inmersiones previas", "", "numeric"], ["ins", "Seguro de buceo"], ["emerg", "Contacto de emergencia", "", "", "wide"]];

  class LogbookApp {
    constructor(root, opts = {}) {
      const ds = root.dataset;
      this.root = root;
      this.uid = "dlb" + (++UID);
      this.assets = opts.assets || ds.assets || "assets/";
      this.key = opts.storageKey || ds.storageKey || "dive-logbook-v1";
      this.locked = opts.lockedFields || DEFAULT_LOCKED;
      this.title = opts.title != null ? opts.title : (ds.title != null ? ds.title : "Mi logbook");
      this.requireUnlock = opts.requireUnlock != null ? opts.requireUnlock : ds.requireUnlock !== "false";
      this.secretUnlock = opts.secretUnlock != null ? opts.secretUnlock : ds.secretUnlock !== "false";
      this.mapData = opts.mapData || ds.mapData || DEFAULT_MAP_DATA;
      this.mapKm = +(opts.mapKm || ds.mapKm) || 90;
      this.profile = opts.profile || null;
      this.friends = opts.friends || [];
      // lo que tapa la ventana arriba y abajo (cabecera fija, barra de pestañas): el libro cabe entero en el resto
      this.viewport = typeof opts.viewport === "function" ? opts.viewport : null;
      let t = opts.theme;
      if (!t && ds.logbookTheme) { try { t = JSON.parse(ds.logbookTheme); } catch (e) { /* JSON no válido */ } }
      this.theme = Object.assign({}, DEFAULT_THEME, t || {});
      this.data = this.blank(parseInt(ds.pages, 10) || 10);
      this.load();
      const cl = opts.centerLogo || ds.centerLogo;
      if (cl && !this.data.cover) {
        this.data.cover = { logo: cl, name: opts.centerName || ds.centerName || "", style: opts.centerLogoStyle || "" };
        if (!this.data.unlocked) this.data.unlocked = { by: "center", at: new Date().toISOString() };
      }
      this.mount();
      this.applyTheme();
      const startView = opts.view || ds.view;
      if (startView) this.data.view = startView;
      if (this.data.view === "passport" && this.isUnlocked) this.showPassport(false); else this.showClassic();
      if (this.data.cover && !this.data.cover.style) this.detectLogoStyle();
    }

    blank(pages) { return { v: {}, photo: "", pages: pages || 10, verified: {}, cover: null, unlocked: null, view: "classic", seenPassport: false }; }
    get isUnlocked() { return !this.requireUnlock || !!this.data.unlocked; }

    /* ---- almacenamiento ---- */
    load() {
      try { const s = localStorage.getItem(this.key); if (s) { const d = JSON.parse(s); if (d && d.v) this.data = Object.assign(this.data, d); } } catch (e) { /* sin almacenamiento */ }
      this.data.verified = this.data.verified || {};
    }
    save() {
      clearTimeout(this._st);
      this._st = setTimeout(() => {
        try { localStorage.setItem(this.key, JSON.stringify(this.data)); } catch (e) { /* lleno o bloqueado */ }
        this.emit("logbook:change", this.getData());
      }, 300);
    }
    emit(name, detail) { this.root.dispatchEvent(new CustomEvent(name, { detail })); }
    getData() { return JSON.parse(JSON.stringify(this.data)); }
    setData(d) {
      if (!d) return;
      this.data = Object.assign(this.blank(10), d);
      this.save(); this.refresh();
    }
    refresh() {
      if (this.pp) this.pp.build();
      this.renderClassic();
      this.renderTools();
    }

    /* ---- tema ---- */
    setTheme(t) { this.theme = Object.assign({}, DEFAULT_THEME, t || {}); this.applyTheme(); if (this.pp) this.pp.build(); }
    applyTheme() {
      const t = this.theme, s = this.root.style;
      const print = t.print || mix(t.ink, t.paper, .42);
      const set = (k, v) => s.setProperty(k, v);
      set("--dlb-bg", t.background || "transparent");
      set("--dlb-navy", t.cover); set("--dlb-navy-hi", mix(t.cover, "#ffffff", .1)); set("--dlb-navy-deep", mix(t.cover, "#000000", .42));
      set("--dlb-gold", t.foil); set("--dlb-gold-hi", mix(t.foil, "#ffffff", .5));
      set("--dlb-paper", t.paper); set("--dlb-paper-hi", mix(t.paper, "#ffffff", .3)); set("--dlb-paper-lo", mix(t.paper, "#000000", .03));
      set("--dlb-ink", t.ink); set("--dlb-ink-soft", mix(t.ink, t.paper, .22));
      set("--dlb-wash", rgba(mix(t.cover, "#ffffff", .55), .16));   // v50.58: papel marfil, apenas velado
      set("--dlb-print", print); set("--dlb-rule", rgba(print, .38)); set("--dlb-ph", rgba(print, .3));
    }

    /* ---- estructura ---- */
    mount() {
      const u = this.uid;
      this.root.classList.add("dlb-app");
      this.root.innerHTML = `
        <div class="dlc-head">
          <div class="dlc-headtext">${this.title ? `<h3 class="dlc-title">${esc(this.title)}</h3>` : ""}<div class="dlc-stats" data-c="stats"></div></div>
          <div class="dlc-tools">
            <button type="button" class="dlc-btn primary" data-c="add">+ Añadir inmersión</button>
            <button type="button" class="dlc-btn" data-c="owner">Mis datos</button>
            <button type="button" class="dlc-icon" data-c="toggle"></button>
          </div>
        </div>
        <div class="dlc-hint" data-c="hint" aria-live="polite" hidden></div>
        <datalist id="${u}-cfriends"></datalist>
        <div class="dlc" data-c="classic">
          <form class="dlc-form" data-c="form" hidden></form>
          <div class="dlc-list" data-c="list" role="list"></div>
        </div>
        <div class="dlb-pp" data-c="passport" hidden></div>`;
      const q = k => this.root.querySelector(`[data-c="${k}"]`);
      this.el = { stats: q("stats"), add: q("add"), owner: q("owner"), toggle: q("toggle"), hint: q("hint"), classic: q("classic"), form: q("form"), list: q("list"), passport: q("passport") };
      this.el.add.addEventListener("click", () => this.openForm("new"));
      this.el.owner.addEventListener("click", () => this.openForm("owner"));
      this.el.toggle.addEventListener("click", () => this.onToggle());
      this.el.list.addEventListener("click", e => { const r = e.target.closest("[data-n]"); if (r) this.openForm(+r.dataset.n); });
      this.el.list.addEventListener("keydown", e => { const r = e.target.closest("[data-n]"); if (r && (e.key === "Enter" || e.key === " ")) { e.preventDefault(); this.openForm(+r.dataset.n); } });
      this.el.form.addEventListener("submit", e => { e.preventDefault(); this.saveForm(); });
      this.el.form.addEventListener("click", e => {
        const b = e.target.closest("[data-f]"); if (!b) return;
        if (b.dataset.f === "cancel") this.closeForm();
        if (b.dataset.f === "delete") this.deleteFromForm(b);
      });
      this.renderFriends();
    }

    renderTools() {
      const t = this.el.toggle, inPassport = !this.el.passport.hidden;
      t.innerHTML = inPassport ? ICON_LIST : ICON_PASSPORT;
      t.dataset.state = this.isUnlocked ? "open" : "locked";
      const label = inPassport ? "Ver como lista"
        : this.isUnlocked ? "Ver como pasaporte" : "Vista pasaporte: se desbloquea con tu primera inmersión en un centro de buceo";
      t.title = label; t.setAttribute("aria-label", label);
      t.classList.toggle("glow", this.isUnlocked && !this.data.seenPassport && !inPassport);
      this.el.add.hidden = inPassport;
      this.el.owner.hidden = inPassport;
    }

    hint(text, ms = 5000) {
      const h = this.el.hint;
      h.textContent = text; h.hidden = !text;
      clearTimeout(this._ht);
      if (text && ms) this._ht = setTimeout(() => { h.hidden = true; }, ms);
    }

    onToggle() {
      if (!this.el.passport.hidden) return this.setView("classic");
      if (this.isUnlocked) return this.setView("passport");
      // bloqueado: pista discreta + truco de 5 toques
      const now = Date.now();
      this._taps = (this._taps || []).filter(x => now - x < 2500); this._taps.push(now);
      if (this.secretUnlock && this._taps.length >= 5) {
        this._taps = [];
        this.unlock("secret");
        this.hint("Lo has encontrado. Vista pasaporte desbloqueada.");
        return;
      }
      this.hint("La vista pasaporte se desbloquea con tu primera inmersión registrada en un centro de buceo.", 4000);
    }

    unlock(by) {
      if (this.data.unlocked) return false;
      this.data.unlocked = { by: by || "manual", at: new Date().toISOString() };
      this.save(); this.renderTools();
      this.emit("logbook:unlocked", this.data.unlocked);
      return true;
    }
    lock() { this.data.unlocked = null; this.data.seenPassport = false; this.save(); this.showClassic(); }

    setView(v) {
      if (v === "passport") {
        if (!this.isUnlocked) return false;
        this.data.view = "passport"; this.save(); this.showPassport(true);
      } else { this.data.view = "classic"; this.save(); this.showClassic(); }
      return true;
    }
    ensurePassport() { if (!this.pp) this.pp = new Logbook(this.el.passport, this); return this.pp; }
    showPassport(animate) {
      this.closeForm();
      this.el.classic.hidden = true;
      this.el.passport.hidden = false;
      const pp = this.ensurePassport();
      pp.build(); pp.layout();
      if (!this.data.seenPassport) { this.data.seenPassport = true; this.save(); }
      this.hint("");
      this.renderTools();
      if (animate) {
        if (pp.anim) pp.finish(); if (pp.ts) pp.end(false); pp.cur = 0; pp.side = "right"; pp.update();
        // el libro entero a la vista, centrado bajo la cabecera (medido antes de la animación de entrada)
        const vp = (this.viewport && this.viewport()) || {}, top = vp.top || 0, bottom = vp.bottom || 0;
        const b = this.el.passport.getBoundingClientRect(), gap = Math.max(8, (innerHeight - top - bottom - b.height) / 2);
        if (b.top < top + 4 || b.bottom > innerHeight - bottom) scrollTo({ top: Math.max(0, scrollY + b.top - top - gap), behavior: reduced() ? "auto" : "smooth" });
        this.el.passport.classList.remove("dlb-enter"); void this.el.passport.offsetWidth; this.el.passport.classList.add("dlb-enter");
        setTimeout(() => pp.open(), 650);
      }
    }
    showClassic() {
      this.el.passport.hidden = true;
      this.el.classic.hidden = false;
      this.renderClassic();
      this.renderTools();
    }

    /* ---- lista ---- */
    renderClassic() {
      const st = statsOf(this.data.v);
      const total = st.list.length + st.prev;
      this.el.stats.textContent = total
        ? `${total} ${total === 1 ? "inmersión" : "inmersiones"} · ${fmtTime(st.minutes)} bajo el agua · máx. ${st.depth} m`
        : "Todavía no hay inmersiones registradas";
      const rows = st.list.slice().reverse().map(d => {
        const ver = this.data.verified[d.n];
        const types = TYPES.filter(([t]) => d["t_" + t]).map(([, l]) => l).join(", ");
        return `<div class="dlc-row" role="listitem" tabindex="0" data-n="${d.n}" aria-label="Inmersión ${esc(d.no || d.n)}, ${esc(d.site || "sin lugar")}">
          <span class="dlc-no">${esc(d.no || d.n)}</span>
          <span class="dlc-date">${esc(d.date || "—")}</span>
          <span class="dlc-site"><b>${esc(d.site || "Sin lugar")}</b><small>${esc([d.country, d.center].filter(Boolean).join(" · "))}${types ? ` · ${esc(types)}` : ""}</small></span>
          <span class="dlc-num">${d.depth ? esc(d.depth) + " m" : "—"}</span>
          <span class="dlc-num">${d.time ? esc(d.time) + " min" : "—"}</span>
          <span class="dlc-ver">${ver ? `<span class="dlc-badge" title="Verificada por ${esc(ver.center)}">✓</span>` : ""}</span>
        </div>`;
      }).join("");
      this.el.list.innerHTML = rows
        ? `<div class="dlc-row dlc-th" aria-hidden="true"><span>Nº</span><span>Fecha</span><span>Lugar</span><span class="dlc-num">Prof.</span><span class="dlc-num">Tiempo</span><span></span></div>${rows}`
        : `<p class="dlc-empty">Añade tu primera inmersión o escanea el QR de tu centro de buceo.</p>`;
    }

    freeDive() {
      for (let i = 1; i <= this.data.pages * 2; i++) if (this.isEmptyDive(i)) return i;
      if (this.data.pages >= 60) return 0;
      const n = this.data.pages * 2 + 1; this.data.pages += 10; return n;
    }
    isEmptyDive(n) { const p = `d:${n}:`; return !Object.keys(this.data.v).some(k => k.startsWith(p)) && !this.data.verified[n]; }

    openForm(which) {
      const v = this.data.v, u = this.uid, f = this.el.form;
      this._form = which;
      const owner = which === "owner", n = typeof which === "number" ? which : null;
      const ver = n ? this.data.verified[n] : null;
      const lockedSet = new Set(ver ? ver.locked || [] : []);
      const fields = owner ? F_OWNER : F_DIVE;
      const val = k => (owner ? v["o:" + k] : n ? v[`d:${n}:${k}`] : "") || "";
      const input = ([k, label, ph, mode, wide, list]) => {
        const id = `${u}-f-${k}`, ro = lockedSet.has(k);
        return `<label class="dlc-field${wide ? " wide" : ""}" for="${id}"><span>${label}${ro ? " · centro" : ""}</span>
          <input id="${id}" name="${k}" value="${esc(val(k))}" placeholder="${esc(ph || "")}" ${mode ? `inputmode="${mode}"` : ""} ${list ? `list="${u}-cfriends"` : ""} ${ro ? "readonly" : ""} autocomplete="off"></label>`;
      };
      const head = owner ? "Mis datos de buceador" : n ? `Inmersión ${esc(v[`d:${n}:no`] || n)}` : "Nueva inmersión";
      f.innerHTML = `
        <div class="dlc-formhead"><strong>${head}</strong>${ver ? `<span class="dlc-verline">✓ Verificada por ${esc(ver.center)} · los datos marcados los registró el centro</span>` : ""}</div>
        <div class="dlc-grid">${fields.map(input).join("")}
          ${owner ? "" : `<fieldset class="dlc-field wide dlc-types"><legend>Tipo</legend>${TYPES.map(([t, l]) => `<label><input type="checkbox" name="t_${t}" ${n && v[`d:${n}:t_${t}`] ? "checked" : ""}> ${l}</label>`).join("")}</fieldset>
          <label class="dlc-field wide" for="${u}-f-notes"><span>Observaciones · vida marina</span><textarea id="${u}-f-notes" name="notes" rows="3">${esc(val("notes"))}</textarea></label>`}
        </div>
        <div class="dlc-formactions">
          <button type="submit" class="dlc-btn primary">Guardar</button>
          <button type="button" class="dlc-btn" data-f="cancel">Cancelar</button>
          ${n ? `<button type="button" class="dlc-btn danger" data-f="delete">Borrar</button>` : ""}
        </div>`;
      f.hidden = false;
      const first = f.querySelector("input:not([readonly])");
      if (first) first.focus({ preventScroll: true });
      f.scrollIntoView({ block: "nearest", behavior: "smooth" });
    }
    closeForm() { this.el.form.hidden = true; this.el.form.innerHTML = ""; this._form = null; }
    saveForm() {
      const f = this.el.form, which = this._form, v = this.data.v;
      if (which === "owner") {
        F_OWNER.forEach(([k]) => { const x = f.elements[k].value.trim(); if (x) v["o:" + k] = x; else delete v["o:" + k]; });
      } else {
        const n = which === "new" ? this.freeDive() : which;
        if (!n) { this.hint("El logbook está lleno (120 inmersiones)."); return; }
        const ver = this.data.verified[n], lockedSet = new Set(ver ? ver.locked || [] : []);
        F_DIVE.forEach(([k]) => {
          if (lockedSet.has(k)) return;
          const x = f.elements[k].value.trim(); if (x) v[`d:${n}:${k}`] = x; else delete v[`d:${n}:${k}`];
        });
        TYPES.forEach(([t]) => { if (f.elements["t_" + t].checked) v[`d:${n}:t_${t}`] = true; else delete v[`d:${n}:t_${t}`]; });
        const notes = f.elements.notes.value.trim(); if (notes) v[`d:${n}:notes`] = notes; else delete v[`d:${n}:notes`];
        const fr = this.friends.find(x => x.name === v[`d:${n}:buddy`]);
        if (fr) v[`d:${n}:buddyId`] = fr.id; else delete v[`d:${n}:buddyId`];
      }
      this.save(); this.closeForm(); this.renderClassic();
    }
    deleteFromForm(btn) {
      if (btn.dataset.armed !== "1") { btn.dataset.armed = "1"; btn.textContent = "Pulsa otra vez para borrar"; setTimeout(() => { btn.dataset.armed = ""; btn.textContent = "Borrar"; }, 3000); return; }
      const n = this._form, p = `d:${n}:`;
      Object.keys(this.data.v).forEach(k => { if (k.startsWith(p)) delete this.data.v[k]; });
      delete this.data.verified[n];
      this.save(); this.closeForm(); this.renderClassic();
    }

    /* ---- funciones del centro ---- */
    addDiveFromCenter(d) {
      if (!d) return null;
      if (d.id) {
        const prev = Object.keys(this.data.verified).find(n => this.data.verified[n].id === d.id);
        if (prev) { this.hint("Esta inmersión ya estaba en tu logbook."); if (this.pp && !this.el.passport.hidden) this.pp.goToDive(+prev); return +prev; }
      }
      const n = this.freeDive();
      if (!n) return null;
      const map = { date: d.date, site: d.site, country: d.country, center: d.center, depth: d.depth, time: d.time, temp: d.temp, vis: d.vis,
        tin: d.timeIn, tout: d.timeOut, gas: d.gas, suit: d.suit, weight: d.weight, pstart: d.pressureStart, pend: d.pressureEnd,
        buddy: d.buddy, notes: d.notes, sign: d.instructor,
        pos: d.lat != null && d.lon != null ? `${(+d.lat).toFixed(5)}, ${(+d.lon).toFixed(5)}` : d.pos };
      Object.keys(map).forEach(f => { if (map[f] != null && map[f] !== "") this.data.v[`d:${n}:${f}`] = String(map[f]); });
      (d.types || []).forEach(t => { this.data.v[`d:${n}:t_${t}`] = true; });
      if (d.buddyId) this.data.v[`d:${n}:buddyId`] = d.buddyId;
      this.data.verified[n] = { id: d.id || "", center: d.center || "", centerId: d.centerId || "", at: new Date().toISOString(),
        locked: d.locked || this.locked.filter(f => map[f] != null && map[f] !== "") };
      const fresh = this.unlock("center");
      this.save();
      if (this.pp && !this.el.passport.hidden) { this.pp.build(); this.pp.showDive(n); }
      else {
        this.renderClassic();
        const row = this.el.list.querySelector(`[data-n="${n}"]`);
        if (row) { row.classList.add("dlc-new"); setTimeout(() => row.classList.remove("dlc-new"), 2600); }
        this.hint(fresh ? `Inmersión verificada por ${d.center || "tu centro"}. Has desbloqueado la vista pasaporte: pulsa el icono de arriba.`
                        : `Inmersión verificada por ${d.center || "tu centro"} añadida.`, fresh ? 9000 : 4000);
      }
      this.emit("logbook:dive-added", { n, dive: d });
      return n;
    }

    setCover(c) {
      this.data.cover = c && c.logo ? { logo: c.logo, name: c.name || "", style: c.style || "", off: false } : null;
      if (c && c.logo && this.unlock("center") && this.el.passport.hidden) this.hint(`Bienvenido a ${c.name || "tu centro"}. Has desbloqueado la vista pasaporte.`, 8000);
      this.save();
      if (this.pp) this.pp.renderCover();
      if (this.data.cover && !this.data.cover.style) this.detectLogoStyle();
    }
    detectLogoStyle() {
      const c = this.data.cover;
      if (!c || !c.logo) return;
      const img = new Image();
      img.crossOrigin = "anonymous";
      img.onload = () => {
        let style = "color";
        try {
          const cv = document.createElement("canvas"); cv.width = cv.height = 24;
          const x = cv.getContext("2d"); x.drawImage(img, 0, 0, 24, 24);
          const px = x.getImageData(0, 0, 24, 24).data;
          let clear = 0; for (let i = 3; i < px.length; i += 4) if (px[i] < 20) clear++;
          if (clear > 24 * 24 * .25) style = "foil";
        } catch (e) { /* imagen de otro dominio sin CORS: medallón a color */ }
        if (this.data.cover === c) { c.style = style; this.save(); if (this.pp) this.pp.renderCover(); }
      };
      img.onerror = () => { if (this.data.cover === c) { c.style = "color"; if (this.pp) this.pp.renderCover(); } };
      img.src = c.logo;
    }

    setProfile(p) { this.profile = p || null; if (this.pp) this.pp.renderQR(); }
    setFriends(list) { this.friends = Array.isArray(list) ? list.filter(f => f && f.name) : []; this.renderFriends(); }
    addFriend(f) {
      if (!f || !f.name) return;
      if (!this.friends.some(x => (f.id && x.id === f.id) || x.name === f.name)) this.friends.push(f);
      this.renderFriends();
    }
    renderFriends() {
      const dl = this.root.querySelector(`#${this.uid}-cfriends`);
      if (dl) dl.innerHTML = this.friends.map(f => `<option value="${esc(f.name)}"></option>`).join("");
      if (this.pp) this.pp.renderFriends();
    }

    /* ---- navegación (vista pasaporte) ---- */
    open() { if (this.setView("passport")) this.pp.open(); }
    close() { if (this.pp) this.pp.close(); }
    next() { if (this.pp) this.pp.next(); }
    prev() { if (this.pp) this.pp.prev(); }
    goTo(i, side) { if (this.pp) this.pp.goTo(i, side); }
    goToDive(n) { if (this.pp && !this.el.passport.hidden) this.pp.goToDive(n); else this.openForm(n); }
  }

  const DiveLogbook = {
    instances: [],
    defaults: { theme: DEFAULT_THEME, lockedFields: DEFAULT_LOCKED, mapData: DEFAULT_MAP_DATA },
    parsePos,
    init(el, opts) { const lb = new LogbookApp(el, opts); this.instances.push(lb); return lb; }
  };
  window.DiveLogbook = DiveLogbook;

  const auto = () => document.querySelectorAll(".dive-logbook:not([data-ready]):not([data-manual])").forEach(el => { el.dataset.ready = "1"; DiveLogbook.init(el); });
  auto(); // los contenedores que ya existen (script al final del <body>)
  if (document.readyState === "loading") document.addEventListener("DOMContentLoaded", auto);
})();
