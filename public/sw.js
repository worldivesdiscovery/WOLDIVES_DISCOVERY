const CACHE='worldives-v50-45';
const SHELL=['/assets/brand/worldives-logo-horizontal-96.webp','/assets/brand/worldives-logo-vertical-oscuro-240.webp','/assets/brand/favicon.ico','/assets/brand/worldives-icono-192.png','/assets/brand/worldives-icono-512.png','/','/index.html','/manifest.webmanifest','/assets/css/world-dives-v8.css?v=50.45','/assets/js/world-dives-v8.js?v=50.45','/assets/js/sw-register.js','/assets/vendor/leaflet/leaflet.js','/assets/vendor/leaflet/leaflet.css','/assets/vendor/markercluster/leaflet.markercluster.js','/assets/vendor/markercluster/MarkerCluster.css','/assets/vendor/protomaps-leaflet/protomaps-leaflet.js','/assets/vendor/protomaps-leaflet/wd-flavor.js'];
self.addEventListener('install',e=>e.waitUntil(caches.open(CACHE).then(c=>c.addAll(SHELL)).then(()=>self.skipWaiting())));
self.addEventListener('activate',e=>e.waitUntil(caches.keys().then(keys=>Promise.all(keys.filter(k=>k!==CACHE).map(k=>caches.delete(k)))).then(()=>self.clients.claim())));
self.addEventListener('fetch',e=>{
  const u=new URL(e.request.url);
  // Never cache API answers: they are personal (bookings, account) and must always be fresh.
  // Map tiles are read by byte ranges (PMTiles): they are never cached here (the browser cache handles them).
  if(e.request.method!=='GET'||u.origin!==location.origin||u.pathname.startsWith('/api/')||u.pathname.startsWith('/tiles/')||e.request.headers.has('range'))return;
  e.respondWith(fetch(e.request).then(r=>{if(r.ok&&r.status===200){const copy=r.clone();caches.open(CACHE).then(c=>c.put(e.request,copy)).catch(()=>{});}return r}).catch(()=>caches.match(e.request).then(r=>r||caches.match('/'))));
});
