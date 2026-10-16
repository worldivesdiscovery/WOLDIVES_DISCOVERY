/* WORLDIVES · widget de reservas (v50.56; reserva exprés v50.58). Una línea en la web del centro:
 *   <script src="https://<WORLDIVES>/widget.js" async></script>
 *   <a href="https://<WORLDIVES>/c/<centro>" data-worldives="boton" data-centro="<centro>">Reservar</a>
 *   <div data-worldives="calendario" data-centro="<centro>" data-servicio="12"></div>
 *   <div data-worldives="lista" data-centro="<centro>" data-tipo="curso"></div>
 * Atributos opcionales: data-servicio, data-tipo, data-idioma (es, en, fr, de, it, pt, pl, nl, zh) y, para abrir
 * directamente en «Tus datos», data-fecha (2026-10-20), data-hora (09:00) y data-personas (2).
 * El botón abre la reserva en una hoja que sube desde abajo (móvil) o en una ventana centrada (ordenador); se cierra
 * con ✕ o tocando fuera, y si ya se ha elegido algo, pregunta antes. Todo ocurre dentro de un iframe de WORLDIVES: no
 * toca los estilos de la página, no pone cookies y solo funciona en los dominios que el centro ha autorizado.
 * Eventos para la página: «worldives:reserva-iniciada» y «worldives:reserva-completada» (CustomEvent en window) y el
 * postMessage original {source:'worldives', event, booking}.
 */
(function () {
  'use strict';
  if (window.__worldivesWidget) return; window.__worldivesWidget = true;
  var me = document.currentScript || (function () { var s = document.getElementsByTagName('script'); for (var i = s.length - 1; i >= 0; i--) if (/\/widget\.js(\?|$)/.test(s[i].src)) return s[i]; return null; })();
  var BASE = me ? me.src.replace(/\/widget\.js.*$/, '') : '';
  if (!BASE) return;
  var ORIGIN = (function () { var a = document.createElement('a'); a.href = BASE; return a.protocol + '//' + a.host; })();
  var frames = [];
  var reduce = window.matchMedia && window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  function src(el, fmt) {
    var q = ['f=' + fmt, 'h=' + encodeURIComponent(location.host)];
    var map = { 'data-servicio': 'servicio', 'data-tipo': 'tipo', 'data-idioma': 'lang', 'data-fecha': 'fecha', 'data-hora': 'hora', 'data-personas': 'personas' };
    for (var a in map) { var v = el.getAttribute(a); if (v) q.push(map[a] + '=' + encodeURIComponent(v)); }
    return BASE + '/w/' + encodeURIComponent(el.getAttribute('data-centro') || '') + '?' + q.join('&');
  }

  function css(el, text) { text.split(';').forEach(function (d) { var i = d.indexOf(':'); if (i > 0) el.style.setProperty(d.slice(0, i).trim(), d.slice(i + 1).trim(), 'important'); }); }

  function frame(url, title) {
    var f = document.createElement('iframe');
    f.src = url; f.title = title || 'Reservas'; f.loading = 'lazy';
    f.setAttribute('allow', 'payment *');   // Apple Pay / Google Pay inside Stripe's form
    // !important inline: the page's own CSS (even «iframe{…!important}») can not break the widget
    css(f, 'display:block;width:100%;max-width:100%;border:0;margin:0;padding:0;min-height:320px;height:520px;background:transparent;color-scheme:normal');
    frames.push(f);
    return f;
  }

  function inline(el, fmt) {
    if (el.__wd) return; el.__wd = true;
    el.appendChild(frame(src(el, fmt), el.getAttribute('data-titulo')));
  }

  // The sheet (phone) or the window (computer)
  var overlay = null, box = null, lastFocus = null, dirty = false;
  function phone() { return (window.innerWidth || document.documentElement.clientWidth) < 640; }
  function close() {
    if (!overlay) return;
    var o = overlay, b = box; overlay = null; box = null; dirty = false;
    var gone = function () { if (o.parentNode) o.parentNode.removeChild(o); frames = frames.filter(function (f) { return document.documentElement.contains(f); }); };
    if (reduce) gone();
    else { css(o, 'background:rgba(1,28,60,0)'); css(b, phone() ? 'transform:translateY(100%)' : 'transform:scale(.96);opacity:0'); setTimeout(gone, 200); }
    document.documentElement.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  function askClose() {
    // Something chosen: the booking asks the person (inside the sheet); nothing chosen: it closes at once.
    var f = box && box.querySelector('iframe');
    if (dirty && f && f.contentWindow) { try { f.contentWindow.postMessage({ source: 'worldives-host', type: 'ask-close' }, ORIGIN); return; } catch (e) { /* closed */ } }
    close();
  }
  function open(el) {
    if (overlay) return; lastFocus = el; dirty = false;
    var mobile = phone();
    overlay = document.createElement('div');
    overlay.setAttribute('role', 'dialog'); overlay.setAttribute('aria-modal', 'true'); overlay.setAttribute('aria-label', el.textContent || 'Reservas');
    css(overlay, 'position:fixed;inset:0;z-index:2147483646;background:rgba(1,28,60,0);display:flex;justify-content:center;margin:0;border:0;box-sizing:border-box;' +
      (mobile ? 'align-items:flex-end;padding:0' : 'align-items:center;padding:16px') + (reduce ? '' : ';transition:background .2s ease'));
    box = document.createElement('div');
    css(box, 'position:relative;width:100%;background:#fff;overflow:hidden;margin:0;padding:0;border:0;box-sizing:border-box;box-shadow:0 18px 60px rgba(0,0,0,.35);' +
      (mobile ? 'max-width:100%;height:94vh;height:94dvh;max-height:840px;border-radius:16px 16px 0 0;transform:translateY(100%)'
        : 'max-width:480px;height:88vh;max-height:780px;border-radius:16px;transform:scale(.96);opacity:0') +
      (reduce ? '' : ';transition:transform .22s cubic-bezier(.2,.8,.2,1),opacity .18s ease,height .2s ease'));
    if (mobile) {   // the handle of the sheet (decoration: closing is ✕ or a tap outside)
      var h = document.createElement('span'); h.setAttribute('aria-hidden', 'true');
      css(h, 'position:absolute;top:6px;left:50%;width:40px;height:4px;margin-left:-20px;border-radius:4px;background:rgba(255,255,255,.75);z-index:2;pointer-events:none');
      box.appendChild(h);
    }
    var f = frame(src(el, 'boton'), el.getAttribute('data-titulo'));
    f.loading = 'eager'; css(f, 'height:100%;min-height:0');
    box.appendChild(f); overlay.appendChild(box);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) askClose(); });
    document.body.appendChild(overlay); document.documentElement.style.overflow = 'hidden';
    requestAnimationFrame(function () { requestAnimationFrame(function () { css(overlay, 'background:rgba(1,28,60,.55)'); css(box, mobile ? 'transform:translateY(0)' : 'transform:scale(1);opacity:1'); }); });
    setTimeout(function () { f.focus(); }, 60);
  }
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape' && overlay) askClose(); });
  // The booking says how tall it is: the sheet or window takes that height (between 420 px and the page's limit)
  function fitBox(h) {
    if (!box || !h) return;
    var vh = window.innerHeight || document.documentElement.clientHeight, max = phone() ? Math.min(vh * 0.94, 840) : Math.min(vh * 0.88, 780);
    css(box, 'height:' + Math.round(Math.max(Math.min(420, max), Math.min(h, max))) + 'px');
  }

  // Faster first open: the connection to WORLDIVES and the booking's own files are ready before the tap
  var warmed = false;
  function warm() {
    if (warmed) return; warmed = true;
    [['preconnect', ORIGIN], ['prefetch', BASE + '/js/wd-reservar.js'], ['prefetch', BASE + '/css/wd-reservar.css']].forEach(function (x) {
      var l = document.createElement('link'); l.rel = x[0]; l.href = x[1]; if (x[0] === 'preconnect') l.crossOrigin = ''; document.head.appendChild(l);
    });
  }

  function scan(root) {
    var els = (root || document).querySelectorAll('[data-worldives]');
    for (var i = 0; i < els.length; i++) {
      var el = els[i], fmt = el.getAttribute('data-worldives');
      if (fmt === 'boton') {
        if (el.__wd) continue; el.__wd = true;
        el.addEventListener('click', (function (x) { return function (e) { e.preventDefault(); open(x); }; })(el));
        el.addEventListener('pointerenter', warm, { once: true }); el.addEventListener('touchstart', warm, { once: true, passive: true }); el.addEventListener('focus', warm, { once: true });
        if ('requestIdleCallback' in window) requestIdleCallback(warm, { timeout: 4000 }); else setTimeout(warm, 2500);
      } else if (fmt === 'calendario' || fmt === 'lista') inline(el, fmt);
    }
  }

  var NAMES = { reserva_iniciada: 'worldives:reserva-iniciada', reserva_completada: 'worldives:reserva-completada' };
  window.addEventListener('message', function (e) {
    if (e.origin !== ORIGIN || !e.data || e.data.source !== 'worldives') return;
    var f = null;
    for (var i = 0; i < frames.length; i++) if (frames[i].contentWindow === e.source) f = frames[i];
    if (!f) return;
    var inSheet = box && box.contains(f);
    if (e.data.type === 'height' && !inSheet) { f.style.setProperty('height', Math.max(240, Math.min(4000, +e.data.h || 0)) + 'px', 'important'); return; }
    if (e.data.type === 'dirty' && inSheet) { dirty = !!e.data.v; return; }
    if (e.data.type === 'sheet-h' && inSheet) { fitBox(+e.data.h || 0); return; }
    if (e.data.type === 'close') { if (inSheet) close(); return; }
    if (e.data.event && NAMES[e.data.event]) {
      var ev;
      try { ev = new CustomEvent(NAMES[e.data.event], { detail: e.data.booking || {} }); } catch (x) { ev = document.createEvent('CustomEvent'); ev.initCustomEvent(NAMES[e.data.event], false, false, e.data.booking || {}); }
      window.dispatchEvent(ev);
    }
  });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { scan(); }); else scan();
  window.WORLDIVES = { abrir: function (el) { open(el); }, cerrar: close, buscar: scan };
})();
