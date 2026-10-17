// Service worker registration (kept out of index.html so the Content-Security-Policy can forbid inline scripts).
// v50.57: after the main script has loaded (on the home page it starts once the first screen is drawn), so that the
// worker's copy of the web comes from the browser and the same files are not downloaded twice on the first visit.
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => Promise.resolve(window.__wdMain).then(() => navigator.serviceWorker.register('/sw.js').catch(() => {})));
}
