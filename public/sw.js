const CACHE='worldives-v50-48';
const SHELL=['/img/marca/worldives-logo-horizontal-96.webp','/img/marca/worldives-logotipo-oscuro-260.webp','/img/marca/favicon.ico','/img/marca/worldives-icono-192.png','/img/marca/worldives-icono-512.png','/','/index.html','/manifest.webmanifest','/css/world-dives-v8.css?v=50.48','/js/world-dives-v8.js?v=50.48','/js/sw-register.js','/js/wd-app.js?v=50.48','/css/wd-app.css?v=50.48','/lib/leaflet/leaflet.js','/lib/leaflet/leaflet.css','/lib/markercluster/leaflet.markercluster.js','/lib/markercluster/MarkerCluster.css','/lib/protomaps-leaflet/protomaps-leaflet.js','/lib/protomaps-leaflet/wd-flavor.js'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  // Never cache API answers: they are personal (bookings, account) and must always be fresh.
  // Map tiles are read by byte ranges (PMTiles): they are never cached here (the browser cache handles them).
  if(e.request.method!=='GET'||u.origin!==location.origin||u.pathname.startsWith('/api/')||u.pathname.startsWith('/tiles/')||e.request.headers.has('range'))return;
  e.respondWith(fetch(e.request).then(r=>{if(r.ok&&r.status===200){const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy)).catch(()=>{});}return r}).catch(()=>caches.match(e.request).then(r=>r||caches.match('/'))));
});
