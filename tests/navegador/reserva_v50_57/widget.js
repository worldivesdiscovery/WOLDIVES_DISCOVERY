/* WORLDIVES · widget de reservas (v50.56). Una línea en la web del centro:
 *   <script src="https://<WORLDIVES>/widget.js" async></script>
 *   <a href="https://<WORLDIVES>/c/<centro>" data-worldives="boton" data-centro="<centro>">Reservar</a>
 *   <div data-worldives="calendario" data-centro="<centro>" data-servicio="12"></div>
 *   <div data-worldives="lista" data-centro="<centro>" data-tipo="curso"></div>
 * Atributos opcionales: data-servicio, data-tipo, data-idioma (es, en, fr, de, it, pt, pl, nl, zh).
 * Todo ocurre dentro de un iframe de WORLDIVES: no toca los estilos de la página, no pone cookies y solo funciona en
 * los dominios que el centro ha autorizado. Eventos para la página: «worldives:reserva-iniciada» y
 * «worldives:reserva-completada» (CustomEvent en window) y el postMessage original {source:'worldives', event, booking}.
 */
(function () {
  'use strict';
  if (window.__worldivesWidget) return; window.__worldivesWidget = true;
  var me = document.currentScript || (function () { var s = document.getElementsByTagName('script'); for (var i = s.length - 1; i >= 0; i--) if (/\/widget\.js(\?|$)/.test(s[i].src)) return s[i]; return null; })();
  var BASE = me ? me.src.replace(/\/widget\.js.*$/, '') : '';
  if (!BASE) return;
  var ORIGIN = (function () { var a = document.createElement('a'); a.href = BASE; return a.protocol + '//' + a.host; })();
  var frames = [];

  function src(el, fmt) {
    var q = ['f=' + fmt, 'h=' + encodeURIComponent(location.host)];
    var s = el.getAttribute('data-servicio'), t = el.getAttribute('data-tipo'), l = el.getAttribute('data-idioma');
    if (s) q.push('servicio=' + encodeURIComponent(s));
    if (t) q.push('tipo=' + encodeURIComponent(t));
    if (l) q.push('lang=' + encodeURIComponent(l));
    return BASE + '/w/' + encodeURIComponent(el.getAttribute('data-centro') || '') + '?' + q.join('&');
  }

  function css(el, text) { text.split(';').forEach(function (d) { var i = d.indexOf(':'); if (i > 0) el.style.setProperty(d.slice(0, i).trim(), d.slice(i + 1).trim(), 'important'); }); }

  function frame(url, title) {
    var f = document.createElement('iframe');
    f.src = url; f.title = title || 'Reservas'; f.loading = 'lazy';
    f.setAttribute('allow', 'payment');
    // !important inline: the page's own CSS (even «iframe{…!important}») can not break the widget
    css(f, 'display:block;width:100%;max-width:100%;border:0;margin:0;padding:0;min-height:320px;height:520px;background:transparent;color-scheme:normal');
    frames.push(f);
    return f;
  }

  function inline(el, fmt) {
    if (el.__wd) return; el.__wd = true;
    el.appendChild(frame(src(el, fmt), el.getAttribute('data-titulo')));
  }

  var overlay = null, lastFocus = null;
  function close() {
    if (!overlay) return;
    overlay.parentNode && overlay.parentNode.removeChild(overlay);
    frames = frames.filter(function (f) { return document.documentElement.contains(f); });
    overlay = null; document.documentElement.style.overflow = '';
    if (lastFocus && lastFocus.focus) lastFocus.focus();
  }
  function open(el) {
    if (overlay) return; lastFocus = el;
    overlay = document.createElement('div');
    overlay.setAttribute('role', 'dialog'); overlay.setAttribute('aria-modal', 'true'); overlay.setAttribute('aria-label', el.textContent || 'Reservas');
    css(overlay, 'position:fixed;inset:0;z-index:2147483646;background:rgba(1,28,60,.55);display:flex;align-items:center;justify-content:center;padding:12px;margin:0;box-sizing:border-box;border:0');
    var box = document.createElement('div');
    css(box, 'position:relative;width:100%;max-width:560px;height:100%;max-height:760px;background:#fff;border-radius:14px;overflow:hidden;box-shadow:0 18px 60px rgba(0,0,0,.35);margin:0;padding:0;border:0;box-sizing:border-box');
    var f = frame(src(el, 'boton'), el.getAttribute('data-titulo'));
    f.loading = 'eager'; css(f, 'height:100%;min-height:0');
    box.appendChild(f); overlay.appendChild(box);
    overlay.addEventListener('click', function (e) { if (e.target === overlay) close(); });
    document.body.appendChild(overlay); document.documentElement.style.overflow = 'hidden';
    setTimeout(function () { f.focus(); }, 50);
  }
  document.addEventListener('keydown', function (e) { if (e.key === 'Escape') close(); });

  function scan(root) {
    var els = (root || document).querySelectorAll('[data-worldives]');
    for (var i = 0; i < els.length; i++) {
      var el = els[i], fmt = el.getAttribute('data-worldives');
      if (fmt === 'boton') {
        if (el.__wd) continue; el.__wd = true;
        el.addEventListener('click', (function (x) { return function (e) { e.preventDefault(); open(x); }; })(el));
      } else if (fmt === 'calendario' || fmt === 'lista') inline(el, fmt);
    }
  }

  var NAMES = { reserva_iniciada: 'worldives:reserva-iniciada', reserva_completada: 'worldives:reserva-completada' };
  window.addEventListener('message', function (e) {
    if (e.origin !== ORIGIN || !e.data || e.data.source !== 'worldives') return;
    var f = null;
    for (var i = 0; i < frames.length; i++) if (frames[i].contentWindow === e.source) f = frames[i];
    if (!f) return;
    if (e.data.type === 'height' && f !== (overlay && overlay.querySelector('iframe'))) { f.style.setProperty('height', Math.max(240, Math.min(4000, +e.data.h || 0)) + 'px', 'important'); return; }
    if (e.data.type === 'close') { close(); return; }
    if (e.data.event && NAMES[e.data.event]) {
      var ev;
      try { ev = new CustomEvent(NAMES[e.data.event], { detail: e.data.booking || {} }); } catch (x) { ev = document.createEvent('CustomEvent'); ev.initCustomEvent(NAMES[e.data.event], false, false, e.data.booking || {}); }
      window.dispatchEvent(ev);
    }
  });

  if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', function () { scan(); }); else scan();
  window.WORLDIVES = { abrir: function (el) { open(el); }, cerrar: close, buscar: scan };
})();
