// Service worker registration (kept out of index.html so the Content-Security-Policy can forbid inline scripts).
if ('serviceWorker' in navigator) {
  window.addEventListener('load', () => navigator.serviceWorker.register('/sw.js').catch(() => {}));
}
