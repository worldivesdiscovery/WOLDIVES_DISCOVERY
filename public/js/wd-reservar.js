/* WORLDIVES · reserva exprés desde la web del centro (v50.58, encargo del 16/10/2026, bloque 2).
 * Una sola aplicación para: el widget (/w/<centro>, dentro de un iframe en la web del centro: hoja que sube desde abajo
 * en el móvil y ventana centrada en el ordenador, o incrustado como calendario o lista), la página del centro
 * (/c/<centro>), la página de una reserva sin cuenta (/mi-reserva/…) y la vuelta del pago (/w/pago/…).
 * Dos pantallas y el pago: «¿Qué y cuándo?» y «Tus datos»; después, «¡Reservado!». El servidor decide todo lo
 * importante (plazas, precio, reglas): aquí solo se pregunta y se enseña. Sin cookies, sin analítica, sin librerías;
 * Stripe.js solo se carga para pagar, y solo si el servidor tiene su clave pública.
 */
(function () {
  'use strict';
  var boot = JSON.parse(document.getElementById('wd-boot').textContent || '{}');
  var T = boot.t || {}; var app = document.getElementById('wr-app'); var lang = boot.lang || 'es';
  var inFrame = window.top !== window;
  var hostUrl = (location.ancestorOrigins && location.ancestorOrigins.length ? location.ancestorOrigins[0] : '') || (inFrame ? document.referrer : '') || '';
  var hostOrigin = (function () { try { return hostUrl ? new URL(hostUrl).origin : ''; } catch (e) { return ''; } })();
  var channel = boot.mode === 'widget' ? 'widget' : 'link';
  var sheet = boot.mode === 'widget' && boot.fmt === 'boton';           // the sheet (phone) or window (computer) over the centre's page
  var STRIPE_JS = 'https://js.stripe.com/v3/';
  var REMEMBER = 'wd-reserva-datos-v1';
  var LEVELS = ['none', 'ow', 'aow', 'rescue'];
  var SIZES = ['XS', 'S', 'M', 'L', 'XL', 'XXL'];
  var PREFIXES = ['+34', '+44', '+33', '+49', '+39', '+351', '+31', '+32', '+41', '+43', '+48', '+353', '+45', '+46', '+47', '+358', '+30', '+420', '+36', '+40',
    '+1', '+52', '+54', '+55', '+56', '+57', '+51', '+20', '+212', '+90', '+971', '+972', '+66', '+62', '+63', '+60', '+65', '+84', '+86', '+81', '+82', '+91', '+960', '+61', '+64', '+27'];

  function t(k, v) { return String(T[k] || k).replace(/\{(\w+)\}/g, function (m, n) { return v && v[n] != null ? v[n] : m; }); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function money(v, cur) { try { return new Intl.NumberFormat(lang, { style: 'currency', currency: cur || 'EUR', maximumFractionDigits: (+v % 1 ? 2 : 0) }).format(+v || 0); } catch (e) { return (+v || 0).toFixed(2) + ' ' + (cur || 'EUR'); } }
  function fmt(iso, opts) { try { return new Intl.DateTimeFormat(lang, Object.assign({ timeZone: 'UTC' }, opts)).format(new Date(iso + 'T12:00:00Z')); } catch (e) { return iso; } }
  function day(iso, opts) { return fmt(iso, Object.assign({ weekday: 'short', day: 'numeric', month: 'short' }, opts || {})); }
  function monthName(ym) { var s = fmt(ym + '-15', { month: 'long', year: 'numeric' }); return s.charAt(0).toUpperCase() + s.slice(1); }
  function addMonth(ym, n) { var d = new Date(ym + '-15T12:00:00Z'); d.setUTCMonth(d.getUTCMonth() + n); return d.toISOString().slice(0, 7); }
  function addDays(iso, n) { var d = new Date(iso + 'T12:00:00Z'); d.setUTCDate(d.getUTCDate() + n); return d.toISOString().slice(0, 10); }
  function tzName(tz) { return String(tz || '').split('/').pop().replace(/_/g, ' '); }
  function key() { try { return crypto.randomUUID(); } catch (e) { return 'k' + Date.now().toString(36) + Math.random().toString(36).slice(2, 12); } }
  function num(n) { try { return new Intl.NumberFormat(lang, { maximumFractionDigits: 1 }).format(n); } catch (e) { return String(n); } }
  function hours(min) { return min ? t('rx_hours', { n: num(Math.round(min / 6) / 10) }) : ''; }
  function store(k, v) { try { if (v == null) localStorage.removeItem(k); else localStorage.setItem(k, JSON.stringify(v)); } catch (e) { /* private mode or blocked */ } }
  function stored(k) { try { return JSON.parse(localStorage.getItem(k) || 'null'); } catch (e) { return null; } }

  // ------------------------------------------------------------------ talking to the page that embeds the widget
  function toHost(msg) {
    if (!inFrame || !hostOrigin) return;
    msg.source = 'worldives';
    try { window.parent.postMessage(msg, hostOrigin); } catch (e) { /* the page went away */ }
  }
  if (inFrame && !sheet && 'ResizeObserver' in window) {
    var lastH = 0;
    new ResizeObserver(function () { var h = Math.ceil(document.body.getBoundingClientRect().height); if (Math.abs(h - lastH) > 2) { lastH = h; toHost({ type: 'height', h: h }); } }).observe(document.body);
  }
  window.addEventListener('message', function (e) {
    // the page asks before closing the sheet (a tap outside, Escape): if something was chosen, ask the person
    if (!hostOrigin || e.origin !== hostOrigin || !e.data || e.data.source !== 'worldives-host') return;
    if (e.data.type === 'ask-close') askClose();
  });
  if (sheet) document.addEventListener('keydown', function (e) { if (e.key === 'Escape') askClose(); });
  if (boot.mode === 'widget' && !inFrame && boot.slug) { location.replace(boot.base + '/c/' + boot.slug + location.search.replace(/[?&]f=[^&]*/, '')); return; }

  function api(path, body, extra) {
    var o = { method: body ? 'POST' : 'GET', headers: { Accept: 'application/json' }, credentials: boot.mode === 'widget' ? 'omit' : 'same-origin' };
    if (body) { o.headers['Content-Type'] = 'application/json'; o.body = JSON.stringify(body); }
    if (extra && extra.idem) o.headers['Idempotency-Key'] = extra.idem;
    return fetch(path, o).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (d) { if (!r.ok) { var e = new Error(d.error || t('error')); e.status = r.status; e.data = d; throw e; } return d; });
    });
  }
  function upload(path, form) {
    return fetch(path, { method: 'POST', body: new FormData(form), headers: { Accept: 'application/json' }, credentials: boot.mode === 'widget' ? 'omit' : 'same-origin' }).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (d) { if (!r.ok) { var e = new Error(d.error || t('error')); e.status = r.status; e.data = d; throw e; } return d; });
    });
  }
  function errText(e) {
    if (!e) return t('error');
    if (e.data && e.data.code === 'no_spots') return t('no_spots');
    if (e.status === 429) return t('too_many');
    if (lang !== 'es' && (e.status >= 500 || !e.status)) return t('error');
    if (lang !== 'es' && e.data && e.data.error) return t('error');
    return e.message || t('error');
  }

  // ------------------------------------------------------------------ the invisible check (only after several attempts)
  function solve(ch, bits) {
    var enc = new TextEncoder(); var n = 0;
    function batch() {
      var jobs = [];
      for (var i = 0; i < 256; i++) jobs.push(crypto.subtle.digest('SHA-256', enc.encode(ch + ':' + (n + i))));
      return Promise.all(jobs).then(function (rs) {
        for (var i = 0; i < rs.length; i++) { var v = new DataView(rs[i]).getUint32(0); if ((v >>> (32 - bits)) === 0) return String(n + i); }
        n += 256; return batch();
      });
    }
    return batch();
  }
  function book(body, idem) {
    return api('/api/w/' + boot.slug + '/reservar', body, { idem: idem }).catch(function (e) {
      if (e.status === 428 && e.data && e.data.challenge) {
        say(t('verifying'), 'info');
        return solve(e.data.challenge, e.data.bits || 14).then(function (nonce) { body.pow = { challenge: e.data.challenge, nonce: nonce }; return api('/api/w/' + boot.slug + '/reservar', body, { idem: idem }); });
      }
      throw e;
    });
  }

  // ------------------------------------------------------------------ diving insurance (v50.56, Bloque 2)
  // The service decides: «no», «se comprueba en el centro» (declared here or shown at the centre) or «obligatorio para
  // reservar online» (the policy is uploaded after booking; the spots are held meanwhile). WORLDIVES does not sell
  // insurance: the links only open the insurer's website, with nothing about the person.
  var insClick = null;
  function insBox(s) {
    var need = s.insurance || 'no'; if (need === 'no') return '';
    var main = need === 'online' ? '<p class="wr-note">' + esc(t('ins_online_after')) + '</p>'
      : '<label class="wr-check"><input type="radio" name="ins_mode" value="have"><span>' + esc(t('ins_have')) + '</span></label>' +
        '<div class="wr-two" data-ins-have hidden><label>' + esc(t('ins_insurer')) + '<input type="text" name="ins_insurer" maxlength="120" autocomplete="off"></label>' +
        '<label>' + esc(t('ins_valid_to')) + '<input type="date" name="ins_valid_to"></label></div>' +
        '<label class="wr-check"><input type="radio" name="ins_mode" value="center"><span>' + esc(t('ins_at_center')) + '</span></label>';
    return '<details class="wr-fold wr-ins"' + (need === 'online' ? ' open' : '') + '><summary><span>' + esc(t('ins_title')) + '</span></summary><div class="wr-fold-in"><p class="wr-note">' +
      esc(t(need === 'online' ? 'ins_online' : 'ins_center')) + '</p>' + main +
      '<div data-ins-others></div><button type="button" class="wr-link" data-ins-offers>' + esc(t('ins_buy')) + '</button><div data-ins-list></div></div></details>';
  }
  function insOthers(n) {
    var box = app.querySelector('[data-ins-others]'); if (!box) return;
    var keep = []; box.querySelectorAll('[data-ins-p]').forEach(function (r) { keep.push([r.querySelector('[name=insp_name]').value, r.querySelector('[name=insp_insurer]').value, r.querySelector('[name=insp_to]').value]); });
    var html = '';
    for (var i = 1; i < n; i++) {
      var k = keep[i - 1] || ['', '', ''];
      html += '<div class="wr-ins-p" data-ins-p><b>' + esc(t('ins_person', { n: i + 1 })) + '</b><div class="wr-three"><label>' + esc(t('name')) + '<input type="text" name="insp_name" maxlength="120" value="' + esc(k[0]) + '"></label>' +
        '<label>' + esc(t('ins_insurer')) + '<input type="text" name="insp_insurer" maxlength="120" value="' + esc(k[1]) + '"></label><label>' + esc(t('ins_valid_to')) + '<input type="date" name="insp_to" value="' + esc(k[2]) + '"></label></div></div>';
    }
    box.innerHTML = n > 1 ? '<p class="wr-note">' + esc(t('ins_others')) + '</p>' + html : '';
  }
  function insOffers(box, country) {
    if (!box) return;
    box.innerHTML = '<p class="wr-note">' + esc(t('loading')) + '</p>';
    api('/api/w/' + boot.slug + '/seguros?tipo=dia&lang=' + lang + (country ? '&pais=' + encodeURIComponent(country) : '')).then(function (r) {
      box.innerHTML = '<p class="wr-note">' + esc(r.not_insurer || '') + '</p>' + (r.offers.length ? r.offers.map(function (o) {
        return '<div class="wr-offer"><div><b>' + esc(o.insurer) + '</b> · ' + esc(o.product) + (o.price_from != null ? ' · ' + esc(t('from')) + ' ' + esc(money(o.price_from, o.currency)) : '') +
          (o.featured ? ' <span class="wr-tag">' + esc(t('ins_featured')) + '</span>' : '') + (o.collaborator ? ' <span class="wr-tag">' + esc(t('ins_collaborator')) + '</span>' : '') + '</div>' +
          '<a class="wr-btn wr-sec" href="' + esc(o.url) + '" target="_blank" rel="noopener noreferrer" data-ins-go="' + o.product_id + '">' + esc(t('ins_buy_in', { insurer: o.insurer })) + ' ↗</a>' +
          '<small class="wr-note">' + esc(o.notice) + (o.collaborator_text ? ' ' + esc(o.collaborator_text) : '') + (o.featured_text ? ' ' + esc(o.featured_text) : '') + '</small></div>';
      }).join('') : '<p class="wr-note">' + esc(t('ins_none')) + '</p>');
      box.querySelectorAll('[data-ins-go]').forEach(function (a) { a.addEventListener('click', function () { insClick = +a.getAttribute('data-ins-go'); }); });
    }).catch(function (e) { box.innerHTML = '<p class="wr-msg err">' + esc(errText(e)) + '</p>'; });
  }
  function insCollect(f, data) {
    var need = S.svc && S.svc.insurance; if (!need || need === 'no') return true;
    var mode = f.elements.ins_mode ? (f.querySelector('[name=ins_mode]:checked') || {}).value : 'center';
    if (need !== 'online') {
      // «Se comprueba en el centro»: it can always be booked (as on WORLDIVES); saying what one has is optional
      var ins = f.elements.ins_insurer ? (f.elements.ins_insurer.value || '').trim() : '', to = f.elements.ins_valid_to ? f.elements.ins_valid_to.value : '';
      if (mode === 'center') data.insurance = { at_center: true };
      else if (ins || to || mode === 'have') {
        if (!ins || !to) { say(t('ins_need_fields')); return false; }
        data.insurance = { insurer: ins, valid_to: to };
      }
    }
    var others = [];
    f.querySelectorAll('[data-ins-p]').forEach(function (r) {
      others.push({ name: r.querySelector('[name=insp_name]').value.trim(), insurer: r.querySelector('[name=insp_insurer]').value.trim(), valid_to: r.querySelector('[name=insp_to]').value });
    });
    if (others.length) data.insurance_participants = others;
    return true;
  }
  // «Obligatorio»: the policy for the day of the dive, before the booking goes on (the same form on /mi-reserva/).
  function insUploadForm(deadline) {
    return '<form novalidate data-ins-form enctype="multipart/form-data"><h3>' + esc(t('ins_pending_title')) + '</h3>' +
      '<p class="wr-note">' + esc(deadline ? t('ins_pending', { time: String(deadline).slice(11, 16) }) : t('ins_online')) + '</p>' +
      '<div class="wr-two"><label>' + esc(t('ins_insurer')) + '<input type="text" name="insurer" maxlength="120" required></label><label>' + esc(t('ins_number')) + '<input type="text" name="policy_number" maxlength="60"></label></div>' +
      '<div class="wr-two"><label>' + esc(t('ins_kind')) + '<select name="kind"><option value="dia">' + esc(t('ins_k_dia')) + '</option><option value="semana">' + esc(t('ins_k_semana')) + '</option><option value="anio">' + esc(t('ins_k_anio')) + '</option><option value="otro">' + esc(t('ins_k_otro')) + '</option></select></label>' +
      '<label>' + esc(t('ins_valid_to')) + '<input type="date" name="valid_to" required></label></div>' +
      '<label>' + esc(t('ins_valid_from')) + '<input type="date" name="valid_from"></label>' +
      '<label>' + esc(t('ins_file')) + '<input type="file" name="file" accept=".pdf,.jpg,.jpeg,.png,application/pdf,image/jpeg,image/png" required></label>' +
      '<p class="wr-note">' + esc(t('ins_no_medical')) + '</p><input type="hidden" name="after_click" value=""><input type="hidden" name="ventana" value="' + (boot.mode === 'widget' ? '1' : '') + '">' +
      '<button class="wr-btn wr-full" type="submit" data-ins-send>' + esc(t('ins_upload')) + '</button>' +
      '<button type="button" class="wr-link" data-ins-offers>' + esc(t('ins_buy')) + '</button><div data-ins-list></div></form>';
  }
  function insBindUpload(token, onDone) {
    var form = app.querySelector('[data-ins-form]'); if (!form) return;
    var off = form.querySelector('[data-ins-offers]'); if (off) off.addEventListener('click', function () { insOffers(form.querySelector('[data-ins-list]')); });
    form.addEventListener('submit', function (ev) {
      ev.preventDefault();
      var file = form.elements.file.files[0];
      if (!form.elements.insurer.value.trim() || !form.elements.valid_to.value || !file) return say(t('ins_need_upload'));
      if (file.size > 10 * 1024 * 1024) return say(t('ins_too_big'));
      form.elements.after_click.value = insClick || '';
      var go = form.querySelector('[data-ins-send]'); go.disabled = true; say('', 'info');
      upload('/api/mi-reserva/' + token + '/seguro', form).then(function (r) { go.disabled = false; onDone(r); }).catch(function (e) { go.disabled = false; say(errText(e)); });
    });
  }
  function insStep(r) {
    S.step = 'ins';
    frame('<div class="wr-done wr-left"><p class="wr-msg info">' + esc(t('ins_online')) + '</p>' + (r.ref ? '<p><b>' + esc(t('reference')) + ':</b> ' + esc(r.ref) + '</p>' : '') + insUploadForm(r.insurance && r.insurance.deadline) + '</div>', null);
    insBindUpload(r.token, function (out) {
      var b = out.booking || {};
      if (b.checkout_url) {
        if (boot.mode !== 'widget') { location.href = b.checkout_url; return; }
        return paying({ checkout_url: b.checkout_url, token: r.token, booking_url: r.booking_url }, null);
      }
      done({ status: b.status || 'requested', ref: r.ref, token: r.token, booking_url: r.booking_url });
    });
  }

  // ------------------------------------------------------------------ state and drawing
  // step: 1 «¿Qué y cuándo?» · 2 «Tus datos» · pay · done · ins · people · info
  var S = { cat: null, svc: null, strip: null, from: null, day: null, slot: null, sel: null, pax: 1, quote: null, extras: {}, level: '', step: 1, dirty: false,
    busy: false, eq: null, more: false, month: null, dates: null, alt: null, showBd: false, form: {}, booking: null, checkout: null, timer: null };
  function say(text, kind) { var m = app.querySelector('[data-msg]'); if (m) { m.className = 'wr-msg ' + (kind || 'err'); m.textContent = text; m.hidden = !text; } }
  function dirty(v) { if (S.dirty !== v) { S.dirty = v; toHost({ type: 'dirty', v: v }); } }
  function provider() { return (S.cat && S.cat.provider) || (boot.booking && boot.booking.provider) || {}; }

  function band() {
    var p = provider(), r = p.rating;
    var close = sheet ? '<button class="wr-x" type="button" data-close aria-label="' + esc(t('close')) + '">✕</button>' : '';
    var stars = r && r.count ? '<span class="wr-stars" aria-label="' + esc(t('rx_rating', { avg: num(r.avg), n: r.count })) + '">★ ' + esc(num(r.avg)) + ' <small>(' + r.count + ')</small></span>' : '';
    return '<header class="wr-band' + (p.cover ? ' has-cover' : '') + '"' + (p.cover ? ' style="--cover:url(&quot;' + esc(encodeURI(p.cover)) + '&quot;)"' : '') + '>' +
      (p.logo ? '<img class="wr-logo" src="' + esc(p.logo) + '" alt="" width="44" height="44">' : '<span class="wr-logo wr-initial" aria-hidden="true">' + esc((p.name || 'W').charAt(0)) + '</span>') +
      '<div class="wr-band-t"><h1>' + esc(p.name || '') + '</h1><p>' + stars + (stars && p.place ? ' · ' : '') + esc(p.place || '') + '</p></div>' + close + '</header>';
  }
  function testBanner() { return boot.test ? '<p class="wr-test" role="status">' + esc(t('rx_test')) + '</p>' : ''; }
  function powered() { return '<footer class="wr-foot"><span>' + esc(t('powered')) + '</span><a href="' + esc(boot.privacy) + '" target="_blank" rel="noopener">' + esc(t('privacy')) + '</a></footer>'; }

  // The whole component: band, the screen (it scrolls inside the sheet if it must), the fixed bar and the footer.
  function frame(screen, bar, name) {
    app.innerHTML = '<div class="wr-shell' + (sheet ? ' wr-sheet' : '') + '">' + band() + testBanner() +
      '<section class="wr-screen" data-screen="' + esc(name || S.step) + '"><div class="wr-in wr-enter">' + screen + '<p class="wr-msg" data-msg hidden role="alert"></p></div></section>' +
      (bar || '') + powered() + '</div>';
    var c = app.querySelector('[data-close]'); if (c) c.addEventListener('click', askClose);
    var sc = app.querySelector('.wr-screen'); if (sc) sc.scrollTop = 0;
    fit();
  }
  // The sheet or window takes the height of what it shows (up to the page's limit): no empty space, no jumps.
  var fitObs = null, lastFit = 0;
  function fit() {
    if (!sheet) return;
    var shell = app.querySelector('.wr-shell'), sc = app.querySelector('.wr-screen'), inn = app.querySelector('.wr-in');
    if (!shell || !sc || !inn) return;
    var send = function () {
      var cs = getComputedStyle(sc), h = Math.ceil(shell.offsetHeight - sc.clientHeight + inn.offsetHeight + parseFloat(cs.paddingTop) + parseFloat(cs.paddingBottom));
      if (Math.abs(h - lastFit) > 2) { lastFit = h; toHost({ type: 'sheet-h', h: h }); }
    };
    if (fitObs) fitObs.disconnect();
    if ('ResizeObserver' in window) { fitObs = new ResizeObserver(send); fitObs.observe(inn); var b = app.querySelector('[data-bar]'); if (b) fitObs.observe(b); }
    send();
  }
  function skeleton() {
    app.innerHTML = '<div class="wr-shell' + (sheet ? ' wr-sheet' : '') + '" aria-busy="true"><header class="wr-band wr-skel-band"><span class="wr-logo wr-skel"></span><div class="wr-band-t"><span class="wr-skel wr-skel-t"></span><span class="wr-skel wr-skel-s"></span></div></header>' +
      '<section class="wr-screen"><span class="wr-skel wr-skel-h"></span><div class="wr-skel-row"><span class="wr-skel wr-skel-card"></span><span class="wr-skel wr-skel-card"></span></div>' +
      '<span class="wr-skel wr-skel-h"></span><div class="wr-skel-row">' + new Array(7).join('<span class="wr-skel wr-skel-day"></span>') + '</div><span class="wr-skel wr-skel-line"></span></section>' +
      '<div class="wr-bar"><span class="wr-skel wr-skel-bar"></span></div><p class="wr-sr">' + esc(t('loading')) + '</p></div>';
  }

  // ------------------------------------------------------------------ closing the sheet: ask when something was chosen
  function askClose() {
    if (!sheet) return;
    if (!S.dirty || S.step === 'done' || S.step === 'people') { toHost({ type: 'close' }); return; }
    if (app.querySelector('.wr-ask')) return;
    var box = document.createElement('div'); box.className = 'wr-ask'; box.setAttribute('role', 'alertdialog'); box.setAttribute('aria-modal', 'true');
    box.innerHTML = '<div class="wr-ask-in"><h2>' + esc(t('rx_exit_title')) + '</h2><p>' + esc(t(S.step === 'pay' ? 'rx_exit_pay' : 'rx_exit_text')) + '</p>' +
      '<button class="wr-btn wr-full" type="button" data-stay>' + esc(t('rx_exit_stay')) + '</button><button class="wr-btn wr-sec wr-full" type="button" data-go-out>' + esc(t('rx_exit_go')) + '</button></div>';
    app.querySelector('.wr-shell').appendChild(box);
    box.querySelector('[data-stay]').focus();
    box.querySelector('[data-stay]').addEventListener('click', function () { box.remove(); });
    box.querySelector('[data-go-out]').addEventListener('click', function () {
      if (S.step === 'pay' && S.booking && S.booking.token) api('/api/mi-reserva/' + S.booking.token + '/cancelar', {}).catch(function () { /* the hold ends by itself */ });
      box.remove(); toHost({ type: 'close' });
    });
  }

  // ------------------------------------------------------------------ the trust line and the bar
  function trust(s) {
    var bits = [];
    if (s && s.mode === 'payment') bits.push(['🔒', t('rx_secure')]);
    if (s && s.pay_way !== 'in_person' && s.free_hours != null) {
      bits.push(['↺', +s.free_hours > 0 ? (s.free_hours >= 48 && s.free_hours % 24 === 0 ? t('rx_free_cancel_days', { d: s.free_hours / 24 }) : t('rx_free_cancel', { h: s.free_hours })) : t('rx_no_free_cancel')]);
    }
    if (s) bits.push(s.mode === 'payment' ? ['⚡', t('rx_instant')] : ['⏱', t('rx_reply', { h: s.response_hours || 24 })]);
    if (s && s.mode !== 'payment') bits.push(['✓', t('rx_nothing_charged')]);
    return bits.length ? '<p class="wr-trust">' + bits.map(function (b) { return '<span><i aria-hidden="true">' + b[0] + '</i> ' + esc(b[1]) + '</span>'; }).join('') + '</p>' : '';
  }
  function bar(label, enabled, opts) {
    opts = opts || {}; var s = S.svc, q = S.quote;
    var total = q ? money(q.total, q.currency) : (s ? t('from') + ' ' + money(s.price, s.currency) : '');
    var sub = q ? (q.lines && q.lines.length > 1 ? t('rx_breakdown') : (s && s.price_per === 'group' ? t('rx_per_group') : (S.pax > 1 ? t('rx_people_n', { n: S.pax }) : t('rx_people_1')))) : (s ? t(s.per === 'day' ? 'per_day' : 'per_person') : '');
    var bd = q && q.lines ? '<div class="wr-bd" data-bd-box' + (S.showBd ? '' : ' hidden') + '>' + q.lines.map(function (l) {
      return '<div><span>' + esc(l.label) + (l.qty > 1 ? ' × ' + l.qty : '') + '</span><span>' + esc(money(l.total, q.currency)) + '</span></div>';
    }).join('') + (q.deposit ? '<div class="wr-bd-dep"><span>' + esc(t('rx_deposit_now')) + '</span><span>' + esc(money(q.deposit, q.currency)) + '</span></div>' : '') + '</div>' : '';
    return '<div class="wr-bar" data-bar>' + (opts.noTrust ? '' : trust(s)) + bd + '<div class="wr-bar-row"><button type="button" class="wr-total" data-bd' + (q && q.lines ? ' aria-expanded="' + !!S.showBd + '"' : ' disabled') + '>' +
      '<small>' + esc(t('total')) + '</small><b data-total>' + esc(total) + '</b><span>' + esc(sub) + '</span></button>' +
      (label ? '<button type="button" class="wr-btn wr-primary" data-primary' + (enabled ? '' : ' disabled') + '>' + esc(label) + '</button>' : '') + '</div></div>';
  }
  function bindBar(onPrimary) {
    var bd = app.querySelector('[data-bd]');
    if (bd) bd.addEventListener('click', function () { S.showBd = !S.showBd; var b = app.querySelector('[data-bd-box]'); if (b) b.hidden = !S.showBd; bd.setAttribute('aria-expanded', S.showBd); });
    var p = app.querySelector('[data-primary]'); if (p && onPrimary) p.addEventListener('click', onPrimary);
  }
  function payLabel() {
    var q = S.quote; if (!q) return t('rx_pay_plain');
    return t('rx_pay', { amount: money(q.deposit || q.total, q.currency) });
  }

  // ------------------------------------------------------------------ choosing: the service, the strip, the times
  function choice() {
    var s = S.svc; var b = { service_id: s.id, participants: S.pax };
    if (S.slot) b.slot_id = S.slot.id; else if (S.sel && S.sel.days) { b.days = S.sel.days; b.part = S.sel.part || 'full'; }
    var ex = Object.keys(S.extras).filter(function (k) { return S.extras[k]; }); if (ex.length) b.extra_ids = ex.map(Number);
    if (S.eq && S.eq.rent) { b.equipment = eqPayload(); b.equipment_notes = S.eq.note || ''; }
    return b;
  }
  function ready() { return !!(S.svc && S.svc.bookable && (S.slot || (S.sel && S.sel.days && S.sel.days.length))); }
  var qTimer = null, qSeq = 0;
  function requote(then) {
    clearTimeout(qTimer);
    if (!ready()) { S.quote = null; paintBar(); return; }
    qTimer = setTimeout(function () {
      var mine = ++qSeq;
      api('/api/w/' + boot.slug + '/precio', choice()).then(function (q) { if (mine !== qSeq) return; S.quote = q; paintBar(); if (S.step === 1) eqDraw(); if (then) then(); })
        .catch(function (e) { if (mine !== qSeq) return; S.quote = null; paintBar(); say(errText(e)); });
    }, 120);
  }
  function paintBar() {
    var b = app.querySelector('[data-bar]'); if (!b) return;
    var html = S.step === 1 ? bar(t('rx_continue'), ready()) : S.step === 2 ? bar(S.svc.mode === 'payment' ? payLabel() : t('send_request'), true) : null;
    if (html == null) return;
    var tmp = document.createElement('div'); tmp.innerHTML = html; b.replaceWith(tmp.firstChild);
    bindBar(S.step === 1 ? toDetails : submit);
  }
  function loadStrip(from) {
    S.from = from || null;
    return api('/api/w/' + boot.slug + '/dias?servicio=' + S.svc.id + (from ? '&desde=' + from : '')).then(function (d) {
      (d.days || []).forEach(function (x) { (x.slots || []).forEach(function (z) { z.date = x.date; }); });
      S.strip = d; return d;
    });
  }
  function pickService(id) {
    S.svc = S.cat.services.filter(function (s) { return s.id === id; })[0] || null;
    S.slot = null; S.sel = null; S.day = null; S.quote = null; S.alt = null; S.extras = {}; S.level = ''; S.more = false; S.pax = Math.max(1, Math.min(S.pax, (S.svc && S.svc.max_participants) || 20));
    if (!S.svc) return s1();
    eqInit();
    s1();
    return loadStrip(boot.date && boot.date > todayIso() ? boot.date : null).then(function () { autoPick(); s1(); }).catch(function (e) { S.strip = { days: [] }; s1(); say(errText(e)); });
  }
  function todayIso() { return (S.strip && S.strip.today) || new Date().toISOString().slice(0, 10); }
  function freeSlots(d) { return (d && d.slots || []).filter(function (x) { return x.free >= S.pax; }); }
  // The nearest day with spots is already chosen; if that day has a single time with spots, that time too.
  function autoPick() {
    var days = (S.strip && S.strip.days) || [];
    if (boot.slot && !S.usedSlot) {   // «salida»: one departure, from a link
      S.usedSlot = true;
      for (var i = 0; i < days.length; i++) {
        var hit = days[i].slots.filter(function (x) { return x.id === boot.slot && x.free >= S.pax; })[0];
        if (hit) { S.day = days[i].date; S.slot = hit; return; }
      }
    }
    var want = boot.date ? days.filter(function (d) { return d.date === boot.date; })[0] : null;
    var d = want && want.free ? want : days.filter(function (x) { return x.free; })[0];
    if (!d) return;
    S.day = d.date;
    if (S.strip.unit === 'slot') {
      var ok = freeSlots(d);
      if (boot.time) { var w = ok.filter(function (x) { return x.time === boot.time; })[0]; if (w) { S.slot = w; return; } }
      if (ok.length === 1) S.slot = ok[0];
    } else S.sel = { days: [d.date], part: 'full' };
  }
  function dayObj(iso) { return ((S.strip && S.strip.days) || []).filter(function (d) { return d.date === iso; })[0]; }

  function servicesBlock() {
    var list = S.cat.services;
    if (S.svc && (list.length === 1 || !S.showAll)) {
      return '<div class="wr-svc-one"><div><b>' + esc(S.svc.title) + '</b><small>' + esc(svcMeta(S.svc)) + '</small></div>' +
        (list.length > 1 ? '<button type="button" class="wr-link" data-all>' + esc(t('rx_change')) + '</button>' : '') + '</div>';
    }
    return '<h2 class="wr-h">' + esc(t('rx_what')) + '</h2><div class="wr-svcs" role="radiogroup" aria-label="' + esc(t('rx_what')) + '">' + list.map(function (s) {
      var on = S.svc && S.svc.id === s.id;
      return '<button type="button" class="wr-svc" role="radio" aria-checked="' + !!on + '" data-svc="' + s.id + '"' + (s.bookable ? '' : ' disabled') + '>' +
        (s.photo && s.photo.src ? '<img src="' + esc(s.photo.src) + '" alt="" loading="lazy" width="56" height="56">' : '<span class="wr-svc-ph" aria-hidden="true"></span>') +
        '<span class="wr-svc-t"><b>' + esc(s.title) + '</b><small>' + esc(s.bookable ? svcMeta(s) : (s.reason || t('no_online'))) + '</small></span></button>';
    }).join('') + '</div>';
  }
  function svcMeta(s) {
    return [t('from') + ' ' + money(s.price, s.currency) + (s.price_per === 'group' ? ' ' + t('rx_per_group') : ''), hours(s.duration), s.rental && s.rental.mode === 'included' ? t('rx_eq_inc') : ''].filter(Boolean).join(' · ');
  }
  function stripBlock() {
    var st = S.strip; if (!st) return '<h2 class="wr-h">' + esc(t('rx_when')) + '</h2><div class="wr-strip">' + new Array(8).join('<span class="wr-skel wr-skel-day"></span>') + '</div>';
    var month = S.day ? fmt(S.day, { month: 'long' }) : fmt(st.from, { month: 'long' });
    var chips = st.days.map(function (d, i) {
      var first = i === 0 || d.date.slice(8) === '01';
      return '<button type="button" class="wr-dchip' + (d.free ? '' : ' none') + '" role="option" aria-selected="' + (S.day === d.date) + '" data-day="' + d.date + '"' + (d.free ? '' : ' disabled') +
        ' aria-label="' + esc(fmt(d.date, { weekday: 'long', day: 'numeric', month: 'long' }) + (d.free ? '' : ' · ' + t('rx_day_full'))) + '"><small>' + esc(fmt(d.date, { weekday: 'short' })) + '</small><b>' + +d.date.slice(8) + '</b>' +
        '<i class="wr-dot" aria-hidden="true"></i>' + (first ? '<em>' + esc(fmt(d.date, { month: 'short' })) + '</em>' : '') + '</button>';
    }).join('') + '<button type="button" class="wr-dchip more" data-more><b>📅</b><small>' + esc(t('rx_more_dates')) + '</small></button>';
    var none = !st.days.some(function (d) { return d.free; });
    return '<div class="wr-h-row"><h2 class="wr-h">' + esc(t('rx_when')) + '</h2><span class="wr-note">' + esc(month.charAt(0).toUpperCase() + month.slice(1)) + ' · ' + esc(t('local_time', { tz: tzName(st.timezone) })) + '</span></div>' +
      '<div class="wr-strip" role="listbox" aria-label="' + esc(t('rx_when')) + '">' + chips + '</div>' +
      (none ? '<p class="wr-note wr-none">' + esc(t('rx_no_days')) + (st.next ? ' <button type="button" class="wr-link" data-next-free="' + st.next + '">' + esc(t('rx_next_free', { date: day(st.next) })) + '</button>' : '') + '</p>' : '');
  }
  function timesBlock() {
    var st = S.strip; if (!st || !S.day) return '';
    var d = dayObj(S.day); if (!d) return '';
    if (st.unit !== 'slot') {
      if (S.svc.unit !== 'half_day' || !S.sel || S.sel.days.length !== 1) return '';
      var part = S.sel.part || 'full';
      return '<div class="wr-times" role="radiogroup">' + ['full', 'am', 'pm'].map(function (p) {
        var can = p === 'full' ? d.state === 'free' : (d.state === 'free' || d.state === p);
        return '<button type="button" class="wr-time" role="radio" aria-checked="' + (part === p) + '" data-part="' + p + '"' + (can ? '' : ' disabled') + '>' + esc(t({ full: 'full_day', am: 'morning', pm: 'afternoon' }[p])) + '</button>';
      }).join('') + '</div>';
    }
    if (!d.slots.length) return '';
    return '<div class="wr-times" role="radiogroup" aria-label="' + esc(t('time')) + '">' + d.slots.map(function (x) {
      var enough = x.free >= S.pax, full = x.free <= 0;
      var left = full ? t('full') : (x.free === 1 ? t('rx_left1') : t('rx_left', { n: x.free }));
      return '<button type="button" class="wr-time' + (enough ? '' : ' full') + (x.free > 0 && x.free <= 2 ? ' low' : '') + '" role="radio" aria-checked="' + !!(S.slot && S.slot.id === x.id) + '" data-slot="' + x.id + '">' +
        '<b>' + esc(x.time) + '</b> · <span>' + esc(left) + '</span></button>';
    }).join('') + '</div>' + altBlock();
  }
  function altBlock() {
    if (!S.alt) return '';
    if (!S.alt.list.length) return '<div class="wr-alt" data-alt><p>' + esc(t('rx_alt_none')) + '</p></div>';
    return '<div class="wr-alt" data-alt role="status"><p>' + esc(t('rx_alt_title', { n: S.pax })) + '</p><div class="wr-times">' + S.alt.list.map(function (a) {
      return '<button type="button" class="wr-time" data-alt-pick="' + a.id + '" data-alt-date="' + a.date + '"><b>' + esc(a.same_day ? a.time : day(a.date) + ' ' + a.time) + '</b> · <span>' +
        esc(a.free === 1 ? t('rx_left1') : t('rx_left', { n: a.free })) + '</span></button>';
    }).join('') + '</div></div>';
  }
  function peopleBlock() {
    var max = maxPax();
    return '<div class="wr-row wr-people"><span>' + esc(t('people')) + '</span><div class="wr-step"><button type="button" data-pax="-1" aria-label="' + esc(t('rx_less')) + '"' + (S.pax <= 1 ? ' disabled' : '') + '>−</button>' +
      '<output data-paxv aria-live="polite">' + S.pax + '</output><button type="button" data-pax="1" aria-label="' + esc(t('rx_more')) + '"' + (S.pax >= max ? ' disabled' : '') + '>+</button></div></div>';
  }
  function maxPax() { return Math.min(S.svc.max_participants || 20, 20); }
  function foldsBlock() {
    var s = S.svc, out = '', r = s.rental || {};
    if (r.mode === 'offer' && (r.pieces || []).length) {
      out += '<details class="wr-fold" data-eqfold' + (S.eq && S.eq.open ? ' open' : '') + '><summary><span>' + esc(t('eq_title')) + '</span><em data-eqsum>' + esc(eqSummary()) + '</em></summary><div class="wr-fold-in wr-eq" data-eq></div></details>';
    }
    if ((s.extras || []).length) {
      var n = Object.keys(S.extras).filter(function (k) { return S.extras[k]; }).length;
      out += '<details class="wr-fold" data-exfold><summary><span>' + esc(t('rx_extras')) + '</span><em>' + esc(n ? t('rx_extras_n', { n: n }) : t('rx_extras_none')) + '</em></summary><div class="wr-fold-in">' +
        s.extras.map(function (x) {
          return '<label class="wr-check"><input type="checkbox" data-extra="' + x.id + '"' + (S.extras[x.id] ? ' checked' : '') + '><span>' + esc(x.name) + ' <small>+' + esc(money(x.price, s.currency)) + ' ' + esc(t('per_person')) + '</small></span></label>';
        }).join('') + '</div></details>';
    }
    return out;
  }
  function eqSummary() {
    if (!S.eq || !S.eq.rent) return t('eq_own');
    var n = 0; S.eq.divers.forEach(function (d) { n += Object.keys(d.items).length; });
    return n ? t('rx_eq_pieces', { n: n }) : t('eq_need');
  }

  function s1() {
    S.step = 1;
    if (!S.cat.bookable) return info();
    var body = servicesBlock();
    if (S.svc) {
      if (S.more) body += moreDates();
      else body += stripBlock() + timesBlock();
      body += peopleBlock() + foldsBlock();
    }
    frame(body, bar(t('rx_continue'), ready()), 1);
    bindS1();
    if (S.svc) { eqDraw(); eqBind(function () { dirty(true); var sm = app.querySelector('[data-eqsum]'); if (sm) sm.textContent = eqSummary(); requote(); }); }
    var sel = app.querySelector('.wr-dchip[aria-selected="true"]'); if (sel && sel.scrollIntoView) { var strip = sel.parentNode; strip.scrollLeft = Math.max(0, sel.offsetLeft - strip.clientWidth / 2 + sel.clientWidth / 2); }
    requote();
  }
  function bindS1() {
    bindBar(toDetails);
    app.querySelectorAll('[data-svc]').forEach(function (b) { b.addEventListener('click', function () { dirty(true); S.showAll = false; pickService(+b.getAttribute('data-svc')); }); });
    var all = app.querySelector('[data-all]'); if (all) all.addEventListener('click', function () { S.showAll = true; s1(); });
    app.querySelectorAll('[data-day]').forEach(function (b) {
      b.addEventListener('click', function () {
        dirty(true); S.day = b.getAttribute('data-day'); S.slot = null; S.alt = null;
        if (S.strip.unit === 'slot') { var ok = freeSlots(dayObj(S.day)); if (ok.length === 1) S.slot = ok[0]; }
        else S.sel = { days: [S.day], part: 'full' };
        s1();
      });
    });
    var more = app.querySelector('[data-more]'); if (more) more.addEventListener('click', function () { S.more = true; S.month = (S.day || todayIso()).slice(0, 7); loadMonth().then(s1); });
    var nf = app.querySelector('[data-next-free]'); if (nf) nf.addEventListener('click', function () { var d = nf.getAttribute('data-next-free'); loadStrip(d).then(function () { S.day = null; autoPick(); s1(); }); });
    app.querySelectorAll('[data-slot]').forEach(function (b) {
      b.addEventListener('click', function () {
        dirty(true);
        var x = dayObj(S.day).slots.filter(function (z) { return z.id === +b.getAttribute('data-slot'); })[0];
        if (x.free >= S.pax) { S.slot = x; S.alt = null; s1(); return; }
        // «Si no quedan plazas a esa hora, se proponen al momento las horas o los días más cercanos con plazas»
        S.slot = null; showAlternatives(x.id);
      });
    });
    app.querySelectorAll('[data-alt-pick]').forEach(function (b) {
      b.addEventListener('click', function () {
        var id = +b.getAttribute('data-alt-pick'), d = b.getAttribute('data-alt-date');
        var go = function () { S.day = d; S.slot = (dayObj(d) || { slots: [] }).slots.filter(function (z) { return z.id === id; })[0] || null; S.alt = null; s1(); };
        if (dayObj(d)) go(); else loadStrip(d).then(go);
      });
    });
    app.querySelectorAll('[data-part]').forEach(function (b) { b.addEventListener('click', function () { S.sel.part = b.getAttribute('data-part'); dirty(true); s1(); }); });
    app.querySelectorAll('[data-pax]').forEach(function (b) {
      b.addEventListener('click', function () {
        dirty(true); S.pax = Math.max(1, Math.min(maxPax(), S.pax + +b.getAttribute('data-pax'))); eqFit();
        if (S.slot && S.slot.free < S.pax) { var gone = S.slot.id; S.slot = null; s1(); showAlternatives(gone); return; }
        if (!S.slot && S.day && S.strip.unit === 'slot') { var ok = freeSlots(dayObj(S.day)); if (ok.length === 1) S.slot = ok[0]; }
        s1();
      });
    });
    app.querySelectorAll('[data-extra]').forEach(function (c) { c.addEventListener('change', function () { dirty(true); S.extras[c.getAttribute('data-extra')] = c.checked; var sm = c.closest('details').querySelector('summary em'); var n = Object.keys(S.extras).filter(function (k) { return S.extras[k]; }).length; sm.textContent = n ? t('rx_extras_n', { n: n }) : t('rx_extras_none'); requote(); }); });
    var ef = app.querySelector('[data-eqfold]'); if (ef) ef.addEventListener('toggle', function () { S.eq.open = ef.open; });
    bindMore();
  }
  function showAlternatives(slotId) {
    S.alt = { list: [] };
    api('/api/w/' + boot.slug + '/alternativas?servicio=' + S.svc.id + '&salida=' + slotId + '&personas=' + S.pax).then(function (r) { S.alt = { list: r.alternatives || [] }; s1(); })
      .catch(function () { S.alt = { list: [] }; s1(); });
  }

  // «Más fechas»: the month calendar (and, for a service by days, a range of days)
  function loadMonth() {
    return api('/api/w/' + boot.slug + '/fechas?servicio=' + S.svc.id + '&mes=' + S.month).then(function (d) { S.dates = d; S.month = d.month; }).catch(function (e) { S.dates = { slots: [], days: {} }; say(errText(e)); });
  }
  function moreDates() {
    var d = S.dates || { slots: [], days: {} }, by = {};
    (d.slots || []).forEach(function (x) { (by[x.date] = by[x.date] || []).push(x); });
    var isOn = S.svc.unit === 'slot' ? function (iso) { return (by[iso] || []).some(function (x) { return x.free > 0; }); } : function (iso) { var st = (d.days || {})[iso]; return st === 'free' || st === 'am' || st === 'pm'; };
    var isSel = function (iso) { return S.svc.unit === 'slot' ? iso === S.day : ((S.sel && S.sel.days) || []).indexOf(iso) >= 0; };
    var first = new Date(S.month + '-01T12:00:00Z'); var off = (first.getUTCDay() + 6) % 7; var n = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth() + 1, 0)).getUTCDate();
    var wk = []; for (var i = 0; i < 7; i++) wk.push('<span>' + esc(new Intl.DateTimeFormat(lang, { weekday: 'narrow', timeZone: 'UTC' }).format(new Date(Date.UTC(2024, 0, 1 + i, 12)))) + '</span>');
    var cells = []; for (i = 0; i < off; i++) cells.push('<span></span>');
    for (var dd = 1; dd <= n; dd++) {
      var iso = S.month + '-' + (dd < 10 ? '0' : '') + dd, on = isOn(iso);
      cells.push('<button type="button" class="wr-day' + (on ? ' on' : '') + (isSel(iso) ? ' sel' : '') + '" data-cal="' + iso + '"' + (on ? '' : ' disabled') + ' aria-label="' + esc(fmt(iso, { weekday: 'long', day: 'numeric', month: 'long' })) + '">' + dd + '</button>');
    }
    var today = (d.today || todayIso()).slice(0, 7);
    return '<div class="wr-h-row"><h2 class="wr-h">' + esc(S.svc.unit === 'slot' ? t('choose_date') : t('choose_days')) + '</h2><button type="button" class="wr-link" data-cal-back>' + esc(t('rx_back_strip')) + '</button></div>' +
      '<div class="wr-cal"><div class="wr-cal-top"><button type="button" data-mon="-1" aria-label="' + esc(t('prev_month')) + '"' + (S.month <= today ? ' disabled' : '') + '>‹</button><b>' + esc(monthName(S.month)) +
      '</b><button type="button" data-mon="1" aria-label="' + esc(t('next_month')) + '">›</button></div><div class="wr-week">' + wk.join('') + '</div><div class="wr-days">' + cells.join('') + '</div></div>';
  }
  function bindMore() {
    var back = app.querySelector('[data-cal-back]'); if (back) back.addEventListener('click', function () { S.more = false; s1(); });
    app.querySelectorAll('[data-mon]').forEach(function (b) { b.addEventListener('click', function () { S.month = addMonth(S.month, +b.getAttribute('data-mon')); loadMonth().then(s1); }); });
    app.querySelectorAll('[data-cal]').forEach(function (b) {
      b.addEventListener('click', function () {
        var iso = b.getAttribute('data-cal'); dirty(true);
        if (S.svc.unit === 'slot') {
          var start = iso < addDays(todayIso(), 14) ? null : iso;
          loadStrip(start).then(function () { S.more = false; S.day = iso; S.slot = null; var ok = freeSlots(dayObj(iso)); if (ok.length === 1) S.slot = ok[0]; s1(); });
          return;
        }
        var cur = (S.sel && S.sel.days) || [];
        if (cur.length === 1 && iso > cur[0]) {   // second tap: a range of consecutive days
          var out = [], x = cur[0];
          while (x <= iso) { out.push(x); x = addDays(x, 1); }
          S.sel = { days: out, part: 'full' };
        } else S.sel = { days: [iso], part: 'full' };
        S.day = S.sel.days[0];
        s1();
      });
    });
  }

  // ------------------------------------------------------------------ v50.58 (16/10): the rental equipment of each diver
  // «Llevo mi equipo» or «Necesito equipo»; the pieces of each person with their sizes; the price comes from the server.
  function eqLabel(p) { return p.custom ? p.label : (T['eqp_' + p.code] ? t('eqp_' + p.code) : p.label); }
  function eqInit() { S.eq = { rent: false, tab: 0, note: '', divers: [], open: false }; eqFit(); }
  function eqFit() { if (!S.eq) return; while (S.eq.divers.length < S.pax) S.eq.divers.push({ kit: false, items: {} }); S.eq.divers.length = Math.max(1, S.pax); if (S.eq.tab >= S.eq.divers.length) S.eq.tab = 0; }
  function eqPayload() {
    return S.eq.divers.map(function (d) { return { kit: !!d.kit, items: Object.keys(d.items).map(function (c) { return { code: c, size: d.items[c].size || '', thick: d.items[c].thick || '' }; }) }; });
  }
  function eqWho(i) { return i === 0 ? t('eq_you') : t('eq_diver', { n: i + 1 }); }
  function eqStart(code) { var p = (S.svc.rental.pieces || []).filter(function (x) { return x.code === code; })[0] || {}; return { size: '', thick: (p.thick || [])[0] || '' }; }
  function eqMissing() {
    if (!S.eq || !S.eq.rent) return null; var ps = (S.svc.rental && S.svc.rental.pieces) || [];
    for (var i = 0; i < S.eq.divers.length; i++) for (var c in S.eq.divers[i].items) {
      var p = ps.filter(function (x) { return x.code === c; })[0];
      if (p && (p.sizes || []).length && p.size_kind !== 'mask' && !S.eq.divers[i].items[c].size) return { diver: i, text: t('eq_size_needed', { piece: eqLabel(p).toLowerCase(), who: eqWho(i) }) };
    }
    return null;
  }
  function eqThick(th) { return th === 'semi' ? t('eq_semi') : th + ' mm'; }
  function eqDraw() {
    var box = app.querySelector('[data-eq]'); if (!box || !S.svc) return; var r = S.svc.rental || {};
    if (r.mode !== 'offer' || !(r.pieces || []).length) { box.innerHTML = '<p class="wr-note wr-eq-inc">' + (r.mode === 'included' ? esc(t('eq_inc_price')) + ' ' : '') + '✓ ' + esc(t('eq_included')) + '</p>'; return; }
    eqFit(); var e = S.eq, d = e.divers[e.tab], q = S.quote || {}, stock = (q.equipment && q.equipment.stock) || {}, cur = S.svc.currency;
    var out = function (code, size) { var st = stock[code]; if (!st) return false; var k = code === 'mask' ? '' : (size || ''); return (k in st) && +st[k] === 0; };
    var per = function (p) { return t(p.price_per === 'day' ? 'eq_per_day' : 'eq_per_dive'); };
    var html = '<div class="wr-eq-mode" role="radiogroup">' +
      '<button type="button" role="radio" class="wr-eq-card" aria-checked="' + !e.rent + '" data-eqrent="0">' + esc(t('eq_own')) + '</button>' +
      '<button type="button" role="radio" class="wr-eq-card" aria-checked="' + e.rent + '" data-eqrent="1">' + esc(t('eq_need')) + '</button></div>';
    if (e.rent) {
      if (e.divers.length > 1) html += '<div class="wr-chips" role="tablist">' + e.divers.map(function (x, i) {
        var n = Object.keys(x.items).length; return '<button type="button" role="tab" class="wr-chip" aria-pressed="' + (i === e.tab) + '" data-eqtab="' + i + '">' + esc(eqWho(i)) + (n ? ' · ' + n : '') + '</button>'; }).join('') + '</div>' +
        (e.tab > 0 ? '<button type="button" class="wr-link" data-eqcopy>' + esc(t('eq_copy')) + '</button>' : '');
      if (r.kit) { var all = r.kit.codes.every(function (c) { return d.items[c]; });
        html += '<button type="button" class="wr-eq-kit" aria-pressed="' + !!(d.kit && all) + '" data-eqkit><b>' + esc(t('eq_kit')) + '</b><span>' + esc(money(r.kit.price, cur)) + ' ' + esc(per(r.kit)) + '</span></button>'; }
      html += '<div class="wr-eq-grid">' + r.pieces.map(function (p) {
        return '<button type="button" class="wr-eq-piece" aria-pressed="' + !!d.items[p.code] + '" data-eqp="' + esc(p.code) + '"><b>' + esc(eqLabel(p)) + '</b><span>' + esc(money(p.price, cur)) + ' ' + esc(per(p)) + '</span></button>'; }).join('') + '</div>';
      var sz = r.pieces.filter(function (p) { return d.items[p.code] && ((p.sizes || []).length || (p.thick || []).length > 1); });
      if (sz.length) html += '<div class="wr-eq-sizes">' + sz.map(function (p) {
        var x = d.items[p.code];
        return '<label><span>' + esc(eqLabel(p)) + '</span><span class="wr-eq-sel">' + ((p.sizes || []).length ? '<select data-eqsize="' + esc(p.code) + '"><option value="">' + esc(t(p.size_kind === 'shoe' ? 'eq_shoe' : 'eq_size')) + '</option>' + p.sizes.map(function (v) {
          var o = out(p.code, v) && x.size !== v; return '<option value="' + esc(v) + '"' + (x.size === v ? ' selected' : '') + (o ? ' disabled' : '') + '>' + esc(v) + (o ? ' · ' + esc(t('eq_out')) : '') + '</option>'; }).join('') + '</select>' : '') +
          ((p.thick || []).length > 1 ? '<select data-eqthick="' + esc(p.code) + '" aria-label="' + esc(t('eq_thick')) + '">' + p.thick.map(function (th) { return '<option value="' + esc(th) + '"' + ((x.thick || p.thick[0]) === th ? ' selected' : '') + '>' + esc(eqThick(th)) + '</option>'; }).join('') + '</select>' : '') + '</span></label>';
      }).join('') + '</div>';
      if (((q.equipment && q.equipment.kit_broken) || []).indexOf(e.tab) >= 0) html += '<p class="wr-msg info">' + esc(t('eq_kit_broken', { total: money(q.total, q.currency) })) + '</p>';
      html += '<label>' + esc(t('eq_note')) + '<input type="text" maxlength="300" data-eqnote value="' + esc(e.note || '') + '"></label>';
    }
    box.innerHTML = html + '<p class="wr-note wr-eq-inc">✓ ' + esc(t('eq_included')) + '</p>';
  }
  function eqBind(refresh) {
    var box = app.querySelector('[data-eq]'); if (!box) return;
    box.addEventListener('click', function (ev) {
      var b = ev.target.closest('button'); if (!b) return; var e = S.eq, d = e.divers[e.tab], r = S.svc.rental;
      if (b.hasAttribute('data-eqrent')) { e.rent = b.getAttribute('data-eqrent') === '1'; eqDraw(); refresh(); return; }
      if (b.hasAttribute('data-eqtab')) { e.tab = +b.getAttribute('data-eqtab'); eqDraw(); return; }
      if (b.hasAttribute('data-eqcopy')) { var prev = e.divers[e.tab - 1]; e.divers[e.tab] = { kit: prev.kit, items: JSON.parse(JSON.stringify(prev.items)) }; eqDraw(); refresh(); return; }
      if (b.hasAttribute('data-eqkit')) {
        var all = r.kit.codes.every(function (c) { return d.items[c]; });
        if (d.kit && all) { d.kit = false; r.kit.codes.forEach(function (c) { delete d.items[c]; }); }
        else { d.kit = true; r.kit.codes.forEach(function (c) { if (!d.items[c]) d.items[c] = eqStart(c); }); }
        eqDraw(); refresh(); return;
      }
      if (b.hasAttribute('data-eqp')) { var c = b.getAttribute('data-eqp'); if (d.items[c]) delete d.items[c]; else d.items[c] = eqStart(c); eqDraw(); refresh(); }
    });
    box.addEventListener('change', function (ev) {
      var el = ev.target, d = S.eq.divers[S.eq.tab];
      if (el.hasAttribute('data-eqsize')) { d.items[el.getAttribute('data-eqsize')].size = el.value; refresh(); }
      if (el.hasAttribute('data-eqthick')) { d.items[el.getAttribute('data-eqthick')].thick = el.value; refresh(); }
    });
    box.addEventListener('input', function (ev) { if (ev.target.hasAttribute('data-eqnote')) S.eq.note = ev.target.value; });
  }

  // ------------------------------------------------------------------ screen 2: «Tus datos»
  function toDetails() {
    if (!ready()) { say(t('rx_err_slot')); return; }
    var miss = eqMissing();
    if (miss) { S.eq.tab = miss.diver; S.eq.open = true; s1(); say(miss.text); return; }
    toHost({ event: 'reserva_iniciada', booking: { service: S.svc.title, service_id: S.svc.id, date: S.slot ? S.slot.date : S.sel.days[0] } });
    s2();
  }
  function whenText() {
    if (S.slot) return day(S.slot.date, { weekday: 'short' }) + ' · ' + S.slot.time;
    var ds = S.sel.days; return ds.length > 1 ? day(ds[0]) + ' – ' + day(ds[ds.length - 1]) : day(ds[0]) + (S.sel.part && S.sel.part !== 'full' ? ' · ' + t(S.sel.part === 'am' ? 'morning' : 'afternoon') : '');
  }
  function field(name, label, input, hint) {
    return '<div class="wr-field" data-f="' + name + '"><label for="f-' + name + '">' + esc(label) + '</label>' + input + (hint ? '<small class="wr-hint">' + esc(hint) + '</small>' : '') +
      '<small class="wr-ferr" id="e-' + name + '" hidden></small></div>';
  }
  function s2() {
    S.step = 2;
    var s = S.svc, mem = stored(REMEMBER), f = S.form, p = provider();
    var v = function (k) { return f[k] != null ? f[k] : (mem && mem[k]) || ''; };
    var prefix = v('prefix') || p.phone_prefix || '+34';
    var opts = PREFIXES.indexOf(prefix) < 0 ? [prefix].concat(PREFIXES) : PREFIXES;
    var level = s.level ? '<div class="wr-field" data-f="level"><span class="wr-lbl" id="l-level">' + esc(t('rx_level')) + '</span><div class="wr-levels" role="radiogroup" aria-labelledby="l-level">' +
      LEVELS.map(function (l) { return '<button type="button" class="wr-chip" role="radio" aria-checked="' + (S.level === l) + '" data-level="' + l + '">' + esc(t('rx_lv_' + l)) + '</button>'; }).join('') +
      '</div><small class="wr-hint">' + esc(t('rx_level_asks', { level: s.level })) + '</small><small class="wr-ferr" id="e-level" hidden></small></div>' : '';
    var html = '<button type="button" class="wr-sum1" data-back><span><b>' + esc(s.title) + '</b><small>' + esc(whenText() + ' · ' + (S.pax > 1 ? t('rx_people_n', { n: S.pax }) : t('rx_people_1'))) + '</small></span><em>' + esc(t('rx_change')) + '</em></button>' +
      '<form novalidate data-form autocomplete="on">' +
      field('name', t('name'), '<input id="f-name" type="text" name="fullname" autocomplete="name" required maxlength="180" aria-describedby="e-name" value="' + esc(v('name')) + '">') +
      field('email', t('email'), '<input id="f-email" type="email" name="email" inputmode="email" autocomplete="email" required maxlength="160" aria-describedby="e-email" value="' + esc(v('email')) + '">') +
      field('phone', t('phone'), '<div class="wr-tel"><select name="prefix" autocomplete="tel-country-code" aria-label="' + esc(t('rx_prefix')) + '">' + opts.map(function (x) { return '<option' + (x === prefix ? ' selected' : '') + '>' + esc(x) + '</option>'; }).join('') +
        '</select><input id="f-phone" type="tel" name="phone" inputmode="tel" autocomplete="tel-national" maxlength="30" aria-describedby="e-phone" value="' + esc(v('phone')) + '"></div>') +
      level + insBox(s) +
      '<details class="wr-fold wr-fold-s"><summary><span>' + esc(t('rx_comment')) + '</span></summary><div class="wr-fold-in"><textarea name="notes" maxlength="1000" aria-label="' + esc(t('notes')) + '">' + esc(f.notes || '') + '</textarea></div></details>' +
      '<label class="wr-hp" aria-hidden="true">Web<input type="text" name="website" tabindex="-1" autocomplete="off"></label>' +
      '<div class="wr-field" data-f="accept"><label class="wr-check"><input type="checkbox" name="accept_policy" aria-describedby="e-accept"' + (f.accept ? ' checked' : '') + '><span>' + esc(t('rx_accept')) +
        ' <button type="button" class="wr-link wr-inline" data-terms aria-expanded="false">' + esc(t('rx_see_terms')) + '</button></span></label><small class="wr-ferr" id="e-accept" hidden></small>' +
        '<div class="wr-terms" data-terms-box hidden><p><b>' + esc(t('policy')) + ':</b> ' + esc(s.policy || p.policy || '') + '</p>' +
        (s.mode === 'payment' ? '<p>' + esc(t('pay_note', { min: S.cat.hold_minutes || boot.hold_minutes || 10 })) + '</p>' : '<p>' + esc(t('request_note')) + '</p>') +
        '<p>' + esc(t('processor', { center: p.name })) + ' <a href="' + esc(boot.privacy) + '" target="_blank" rel="noopener">' + esc(t('privacy')) + '</a></p></div></div>' +
      '<label class="wr-check wr-remember"><input type="checkbox" name="remember"' + (mem || f.remember ? ' checked' : '') + '><span>' + esc(t('rx_remember')) + '</span></label>' +
      (mem ? '<button type="button" class="wr-link wr-small" data-forget>' + esc(t('rx_forget')) + '</button>' : '') +
      '</form>';
    frame(html, bar(s.mode === 'payment' ? payLabel() : t('send_request'), true), 2);
    bindBar(submit);
    var form = app.querySelector('[data-form]');
    app.querySelector('[data-back]').addEventListener('click', function () { keepForm(); s1(); });
    form.addEventListener('submit', function (ev) { ev.preventDefault(); submit(); });
    form.addEventListener('input', function (ev) { dirty(true); var w = ev.target.closest('.wr-field'); if (w) clearErr(w.getAttribute('data-f')); });
    form.addEventListener('change', function (ev) { var w = ev.target.closest('.wr-field'); if (w) clearErr(w.getAttribute('data-f')); });
    app.querySelectorAll('[data-level]').forEach(function (b) { b.addEventListener('click', function () { S.level = b.getAttribute('data-level'); dirty(true); clearErr('level'); app.querySelectorAll('[data-level]').forEach(function (x) { x.setAttribute('aria-checked', x === b); }); }); });
    var terms = app.querySelector('[data-terms]');
    terms.addEventListener('click', function (ev) { ev.preventDefault(); var box = app.querySelector('[data-terms-box]'); box.hidden = !box.hidden; terms.setAttribute('aria-expanded', !box.hidden); });
    var fg = app.querySelector('[data-forget]'); if (fg) fg.addEventListener('click', function () { store(REMEMBER, null); ['fullname', 'email', 'phone'].forEach(function (k) { form.elements[k].value = ''; }); form.elements.remember.checked = false; fg.remove(); });
    var offBtn = app.querySelector('[data-ins-offers]'); if (offBtn) offBtn.addEventListener('click', function () { insOffers(app.querySelector('[data-ins-list]')); });
    app.querySelectorAll('[name=ins_mode]').forEach(function (r) { r.addEventListener('change', function () { var h = app.querySelector('[data-ins-have]'); if (h) h.hidden = r.value !== 'have' || !r.checked; }); });
    insOthers(S.pax);
    if (!S.quote) requote();
  }
  function keepForm() {
    var f = app.querySelector('[data-form]'); if (!f) return;
    S.form = { name: f.elements.fullname.value, email: f.elements.email.value, prefix: f.elements.prefix.value, phone: f.elements.phone.value, notes: f.elements.notes.value,
      accept: f.elements.accept_policy.checked, remember: f.elements.remember.checked };
  }
  function setErr(name, text) {
    var w = app.querySelector('.wr-field[data-f="' + name + '"]'); if (!w) return;
    var e = w.querySelector('.wr-ferr'); e.textContent = text; e.hidden = false; w.classList.add('bad');
    var i = w.querySelector('input,select,textarea,button'); if (i) i.setAttribute('aria-invalid', 'true');
  }
  function clearErr(name) {
    var w = app.querySelector('.wr-field[data-f="' + name + '"]'); if (!w || !w.classList.contains('bad')) return;
    var e = w.querySelector('.wr-ferr'); e.hidden = true; w.classList.remove('bad');
    var i = w.querySelector('[aria-invalid]'); if (i) i.removeAttribute('aria-invalid');
  }
  function phoneValue(f) {
    var raw = (f.elements.phone.value || '').trim(); if (!raw) return '';
    if (/^\+|^00/.test(raw)) return raw.replace(/^00/, '+');
    return f.elements.prefix.value + ' ' + raw;
  }
  function validate(f) {
    var bad = [];
    var name = (f.elements.fullname.value || '').trim(), email = (f.elements.email.value || '').trim(), phone = (f.elements.phone.value || '').replace(/[\s().-]/g, '');
    if (name.length < 2) bad.push(['name', t('rx_err_name')]);
    if (!/^[^@\s]+@[^@\s]+\.[^@\s]{2,}$/.test(email)) bad.push(['email', t('rx_err_email')]);
    if (phone && !/^\+?\d{6,15}$/.test(phone.replace(/^00/, '+'))) bad.push(['phone', t('rx_err_phone')]);
    if (S.svc.level && LEVELS.indexOf(S.level) < 0) bad.push(['level', t('rx_err_level')]);
    if (!f.elements.accept_policy.checked) bad.push(['accept', t('rx_err_accept')]);
    bad.forEach(function (b) { setErr(b[0], b[1]); });
    if (bad.length) {
      var w = app.querySelector('.wr-field[data-f="' + bad[0][0] + '"]'); var i = w && w.querySelector('input,button');
      if (w && w.scrollIntoView) w.scrollIntoView({ block: 'center', behavior: 'smooth' }); if (i) i.focus({ preventScroll: true });
    }
    return !bad.length;
  }
  var idem = null;
  function submit() {
    if (S.busy) return;
    var f = app.querySelector('[data-form]'); if (!f) return;
    say('', 'info');
    if (!validate(f)) return;
    var s = S.svc, data = choice();
    data.fullname = f.elements.fullname.value.trim(); data.email = f.elements.email.value.trim(); data.phone = phoneValue(f);
    data.notes = (f.elements.notes.value || '').trim(); data.website = f.elements.website.value;
    data.accept_policy = true; data.lang = lang; data.canal = channel; data.host_url = hostUrl; data.host = boot.host || ''; data.reserva_expres = true;
    if (s.level) data.level = S.level;
    if (!insCollect(f, data)) return;
    keepForm();
    if (f.elements.remember.checked) store(REMEMBER, { name: data.fullname, email: data.email, prefix: f.elements.prefix.value, phone: (f.elements.phone.value || '').trim() });
    else store(REMEMBER, null);
    if (boot.test) return testDone(data);
    var embedded = s.mode === 'payment' && !!S.cat.stripe;
    if (embedded) data.pago_integrado = true;
    S.busy = true; var go = app.querySelector('[data-primary]'); if (go) { go.disabled = true; go.classList.add('wr-wait'); }
    var win = null;
    if (s.mode === 'payment' && !embedded && boot.mode === 'widget') { try { win = window.open('', 'wd-pago'); } catch (e) { win = null; } }   // opened now: popup blockers allow it
    idem = idem || key();
    book(data, idem).then(function (r) {
      S.busy = false; idem = null;
      if (r.status === 'insurance_pending') { if (win) try { win.close(); } catch (e) { /* closed */ } return insStep(r); }
      if (r.client_secret && r.stripe) return payStep(r);
      if (r.checkout_url) {
        if (boot.mode !== 'widget') { location.href = r.checkout_url; return; }
        if (win) { try { win.location.href = r.checkout_url; } catch (e) { win = null; } }
        return paying(r, win);
      }
      if (win) try { win.close(); } catch (e) { /* closed already */ }
      done(r);
    }).catch(function (e) {
      S.busy = false; if (go) { go.disabled = false; go.classList.remove('wr-wait'); } if (win) try { win.close(); } catch (x) { /* closed */ }
      if (e.data && e.data.code === 'no_spots') {
        idem = null; keepForm();
        S.alt = { list: e.data.alternatives || [] }; S.slot = null;
        return loadStrip(S.from).then(function () { s1(); say(t('no_spots')); });
      }
      if (/correo|email/i.test(e.message || '') && e.status === 400) setErr('email', errText(e));
      else if (/titulaci/i.test(e.message || '')) setErr('level', t('rx_err_level'));
      else say(errText(e));
    });
  }
  function testDone(data) {
    dirty(false); S.step = 'done';
    frame('<div class="wr-done"><div class="wr-ico" aria-hidden="true">✓</div><h2>' + esc(t(S.svc.mode === 'payment' ? 'rx_done_paid' : 'rx_done_req')) + '</h2>' +
      '<p class="wr-msg info">' + esc(t('rx_test_done')) + '</p><p class="wr-note">' + esc(S.svc.title + ' · ' + whenText()) + '</p>' +
      '<button type="button" class="wr-btn wr-sec" data-again>' + esc(t('rx_again')) + '</button></div>', null, 'done');
    app.querySelector('[data-again]').addEventListener('click', function () { S.form = {}; s1(); });
    toHost({ event: 'reserva_completada', booking: { ref: 'PRUEBA', status: 'test', service: S.svc.title, paid: false } });
    void data;
  }

  // ------------------------------------------------------------------ the payment inside the booking (Stripe's own form)
  var stripeLoad = null;
  function loadStripe() {
    if (window.Stripe) return Promise.resolve(window.Stripe);
    if (stripeLoad) return stripeLoad;
    stripeLoad = new Promise(function (ok, ko) {
      var sc = document.createElement('script'); sc.src = STRIPE_JS; sc.async = true;
      sc.onload = function () { window.Stripe ? ok(window.Stripe) : ko(new Error('stripe')); };
      sc.onerror = function () { stripeLoad = null; ko(new Error('stripe')); };
      document.head.appendChild(sc);
    });
    return stripeLoad;
  }
  function holdText(sec) { var m = Math.floor(sec / 60), s = sec % 60; return m + ':' + (s < 10 ? '0' : '') + s; }
  function payStep(r) {
    S.step = 'pay'; S.booking = r; dirty(true);
    var until = Date.now() + (r.hold_seconds != null ? r.hold_seconds : (S.cat.hold_minutes || 10) * 60) * 1000;
    frame('<div class="wr-hold" data-hold role="timer" aria-live="off">⏱ <span>' + esc(t('rx_hold', { time: holdText(Math.max(0, Math.round((until - Date.now()) / 1000))) })) + '</span></div>' +
      '<p class="wr-note">' + esc(S.svc.title + ' · ' + whenText() + ' · ' + (S.pax > 1 ? t('rx_people_n', { n: S.pax }) : t('rx_people_1'))) + '</p>' +
      '<div class="wr-stripe" id="wr-stripe" data-stripe><div class="wr-skel wr-skel-pay"></div><p class="wr-note">' + esc(t('opening_pay')) + '</p></div>', bar(null, false, { noTrust: true }), 'pay');
    bindBar();
    clearInterval(S.timer);
    S.timer = setInterval(function () {
      var left = Math.max(0, Math.round((until - Date.now()) / 1000)), h = app.querySelector('[data-hold] span');
      if (h) h.textContent = t('rx_hold', { time: holdText(left) });
      if (left <= 60 && h) h.parentNode.classList.add('low');
      if (left <= 0) { clearInterval(S.timer); holdOver(); }
    }, 1000);
    loadStripe().then(function (Stripe) {
      var stripe = Stripe(r.stripe.key, { stripeAccount: r.stripe.account, locale: lang === 'zh' ? 'zh' : lang });
      return stripe.initEmbeddedCheckout({ fetchClientSecret: function () { return Promise.resolve(r.client_secret); }, onComplete: function () { paidInside(r); } });
    }).then(function (checkout) {
      S.checkout = checkout; var box = app.querySelector('[data-stripe]'); if (!box) { checkout.destroy(); return; }
      box.innerHTML = ''; checkout.mount('#wr-stripe');
    }).catch(function () {
      var box = app.querySelector('[data-stripe]');
      if (box) box.innerHTML = '<p class="wr-msg err">' + esc(t('rx_stripe_fail')) + '</p><a class="wr-btn wr-sec" href="' + esc(boot.base + '/mi-reserva/' + r.token + '?pagar=1') + '" target="_blank" rel="noopener">' + esc(t('pay_link')) + '</a>';
    });
  }
  function holdOver() {
    if (S.checkout) { try { S.checkout.destroy(); } catch (e) { /* gone */ } S.checkout = null; }
    var box = app.querySelector('[data-stripe]'); if (!box) return;
    box.innerHTML = '<p class="wr-msg info">' + esc(t('rx_hold_over')) + '</p><button type="button" class="wr-btn" data-again>' + esc(t('rx_again')) + '</button>';
    box.querySelector('[data-again]').addEventListener('click', function () { S.slot = null; S.booking = null; loadStrip(S.from).then(function () { autoPick(); s1(); }); });
  }
  function paidInside(r) {
    clearInterval(S.timer);
    var box = app.querySelector('[data-stripe]'); if (box) box.insertAdjacentHTML('afterbegin', '<p class="wr-msg ok">' + esc(t('rx_paid_checking')) + '</p>');
    var tries = 0;
    (function check() {
      api('/api/mi-reserva/' + r.token + '/comprobar-pago', { lang: lang }).then(function (d) {
        var b = d.booking;
        if (b.status === 'confirmed' || ++tries >= 8) { if (S.checkout) { try { S.checkout.destroy(); } catch (e) { /* gone */ } S.checkout = null; } return done(Object.assign({}, r, { status: b.status === 'confirmed' ? 'confirmed' : 'payment_in_progress' }), true, b); }
        setTimeout(check, 1500);
      }).catch(function () { if (++tries < 8) setTimeout(check, 2000); else done(Object.assign({}, r, { status: 'payment_in_progress' }), true); });
    })();
  }

  // Stripe's page in a new window (the server has no publishable key, or a payment started there)
  function paying(r, win) {
    S.step = 'pay';
    frame('<div class="wr-done"><h2>' + esc(t('waiting_pay')) + '</h2><p class="wr-note">' + esc(t('opening_pay')) + '</p>' +
      '<a class="wr-btn" href="' + esc(r.checkout_url) + '" target="_blank" rel="noopener">' + esc(t('pay_link')) + '</a></div>', null, 'pay');
    var until = Date.now() + ((S.cat.hold_minutes || 10) + 2) * 60000;
    (function poll() {
      api('/api/mi-reserva/' + r.token).then(function (d) {
        var b = d.booking;
        if (b.status === 'confirmed') return done({ status: 'confirmed', ref: b.ref, token: r.token, booking_url: r.booking_url }, true, b);
        if (b.status === 'expired' || b.status === 'cancelled') {
          frame('<div class="wr-done"><p class="wr-msg info">' + esc(t('pay_cancelled')) + '</p><button class="wr-btn wr-sec" type="button" data-again>' + esc(t('rx_again')) + '</button></div>', null, 'pay');
          app.querySelector('[data-again]').addEventListener('click', function () { S.slot = null; loadStrip(S.from).then(function () { autoPick(); s1(); }); }); return;
        }
        if (Date.now() < until) setTimeout(poll, 2500);
      }).catch(function () { if (Date.now() < until) setTimeout(poll, 4000); });
    })();
    void win;
  }

  // ------------------------------------------------------------------ «¡Reservado!»
  function done(r, paid, view) {
    S.step = 'done'; dirty(false); clearInterval(S.timer);
    toHost({ event: 'reserva_completada', booking: { ref: r.ref, status: r.status, service: S.svc && S.svc.title, paid: !!paid } });
    var draw = function (b) {
      b = b || {};
      var ok = (b.status || r.status) === 'confirmed', p = (b.provider) || provider(), tok = r.token || b.token;
      if (!/^\d+\.[A-Za-z0-9_-]{20,}$/.test(tok || '')) tok = null;   // a booking of a WORLDIVES account: its page is in the account
      var email = (S.form && S.form.email) || '';
      var when = b.date ? (b.days && b.days.length > 1 ? day(b.days[0]) + ' – ' + day(b.days[b.days.length - 1]) : fmt(b.date, { weekday: 'long', day: 'numeric', month: 'long' }) + (b.time ? ' · ' + b.time : '')) : (S.svc ? whenText() : '');
      var wa = p.whatsapp ? p.whatsapp + (p.whatsapp.indexOf('?') < 0 ? '?' : '&') + 'text=' + encodeURIComponent(t('rx_wa_text', { ref: r.ref || b.ref || '' })) : '';
      var acts = [];
      if (tok) acts.push('<a class="wr-act" href="' + esc(boot.base + '/mi-reserva/' + tok + '.ics') + '" download data-ics><span aria-hidden="true">📅</span>' + esc(t('rx_calendar')) + '</a>');
      if (p.maps) acts.push('<a class="wr-act" href="' + esc(p.maps) + '" target="_blank" rel="noopener"><span aria-hidden="true">📍</span>' + esc(t('rx_directions')) + '</a>');
      if (wa) acts.push('<a class="wr-act" href="' + esc(wa) + '" target="_blank" rel="noopener"><span aria-hidden="true">💬</span>' + esc(t('rx_whatsapp')) + '</a>');
      var pax = b.participants || S.pax;
      frame('<div class="wr-done"><div class="wr-ico" aria-hidden="true">✓</div><h2>' + esc(t(ok ? 'rx_done_paid' : (r.status === 'payment_in_progress' ? 'paid' : 'rx_done_req'))) + '</h2>' +
        (r.ref || b.ref ? '<p class="wr-ref">' + esc(t('reference')) + ': <b>' + esc(r.ref || b.ref) + '</b></p>' : '') +
        '<p class="wr-when"><b>' + esc((b.service || (S.svc && S.svc.title) || '')) + '</b><br>' + esc(when) + ' · ' + esc(pax > 1 ? t('rx_people_n', { n: pax }) : t('rx_people_1')) + '</p>' +
        (!ok && r.response_deadline_text ? '<p class="wr-note">' + esc(t('reply_before', { when: r.response_deadline_text })) + '</p>' : '') +
        (b.has_qr && tok ? '<figure class="wr-qr"><img src="' + esc('/api/mi-reserva/' + tok + '/qr.svg') + '" alt="' + esc(t('rx_qr_alt')) + '" width="144" height="144"><figcaption>' + esc(t('rx_qr_note')) + '</figcaption></figure>' : '') +
        (b.meeting_point ? '<p class="wr-note">📍 ' + esc(t('rx_meeting')) + ': ' + esc(b.meeting_point) + '</p>' : '') +
        (acts.length ? '<div class="wr-acts">' + acts.join('') + '</div>' : '') +
        (pax > 1 && tok ? '<button type="button" class="wr-btn wr-sec wr-full" data-people>' + esc(t('rx_companions')) + '</button>' : '') +
        (email ? '<p class="wr-note">' + esc(t('mail_sent', { email: email })) + '</p>' : '') +
        (S.svc && S.svc.insurance && S.svc.insurance !== 'no' ? '<p class="wr-msg info">' + esc(t('ins_bring')) + '</p>' : '') +
        (r.booking_url ? '<a class="wr-link" href="' + esc(r.booking_url) + '" target="_blank" rel="noopener">' + esc(t('your_booking')) + '</a>' : '') +
        '<p class="wr-note wr-acc">' + esc(t('account_offer')) + ' <a class="wr-link" href="' + esc(boot.register + '?tipo=recreational' + (email ? '&email=' + encodeURIComponent(email) : '')) + '" target="_blank" rel="noopener">' + esc(t('create_account')) + '</a></p></div>', null, 'done');
      var pb = app.querySelector('[data-people]'); if (pb) pb.addEventListener('click', function () { companions(tok, pax, b.people || [], function () { draw(b); }); });
    };
    if (view) return draw(view);
    if (!/^\d+\.[A-Za-z0-9_-]{20,}$/.test(r.token || '')) return draw(null);
    api('/api/mi-reserva/' + r.token + '?lang=' + lang).then(function (d) { draw(d.booking); }).catch(function () { draw(null); });
  }

  // «Completar los datos de mis acompañantes»: names, level and sizes (they go to the boat list of the centre)
  function companions(tok, pax, people, back) {
    var prev = S.step; S.step = 'people';
    var by = {}; (people || []).forEach(function (p) { by[p.seat] = p; });
    var rows = '';
    for (var seat = 2; seat <= pax; seat++) {
      var p = by[seat] || {};
      rows += '<fieldset class="wr-person" data-seat="' + seat + '"><legend>' + esc(t('rx_companion_n', { n: seat - 1 })) + '</legend>' +
        '<label>' + esc(t('name')) + '<input type="text" name="name" maxlength="120" autocomplete="off" value="' + esc(p.name || '') + '"></label>' +
        '<div class="wr-three"><label>' + esc(t('rx_level')) + '<select name="level"><option value=""></option>' + LEVELS.map(function (l) { return '<option value="' + l + '"' + (p.level === l ? ' selected' : '') + '>' + esc(t('rx_lv_' + l)) + '</option>'; }).join('') + '</select></label>' +
        '<label>' + esc(t('eq_size')) + '<select name="size"><option value=""></option>' + SIZES.map(function (z) { return '<option' + (p.size === z ? ' selected' : '') + '>' + z + '</option>'; }).join('') + '</select></label>' +
        '<label>' + esc(t('eq_shoe')) + '<input type="text" name="shoe" inputmode="decimal" maxlength="4" value="' + esc(p.shoe || '') + '"></label></div></fieldset>';
    }
    frame('<button type="button" class="wr-link" data-back>‹ ' + esc(t('back')) + '</button><h2 class="wr-h">' + esc(t('rx_companions')) + '</h2><p class="wr-note">' + esc(t('rx_companions_note')) + '</p>' +
      '<form novalidate data-people-form>' + rows + '<button type="submit" class="wr-btn wr-full">' + esc(t('rx_save')) + '</button></form>', null, 'people');
    app.querySelector('[data-back]').addEventListener('click', function () { S.step = prev; back(); });
    app.querySelector('[data-people-form]').addEventListener('submit', function (ev) {
      ev.preventDefault(); var btn = ev.target.querySelector('button[type=submit]'); btn.disabled = true;
      var list = [];
      ev.target.querySelectorAll('[data-seat]').forEach(function (fs) {
        list.push({ name: fs.querySelector('[name=name]').value.trim(), level: fs.querySelector('[name=level]').value || null, size: fs.querySelector('[name=size]').value || null, shoe: fs.querySelector('[name=shoe]').value.trim() || null });
      });
      api('/api/mi-reserva/' + tok + '/acompanantes', { people: list }).then(function (out) {
        btn.disabled = false; people.length = 0; Array.prototype.push.apply(people, out.people || []); say(t('rx_saved'), 'ok');
      }).catch(function (e) { btn.disabled = false; say(errText(e)); });
    });
  }

  function info() {
    var p = S.cat.provider; S.step = 'info';
    frame('<p class="wr-msg info">' + esc(t('no_online')) + '</p><form novalidate data-info><label>' + esc(t('name')) + '<input type="text" name="name" required maxlength="120" autocomplete="name"></label>' +
      '<label>' + esc(t('email')) + '<input type="email" name="email" required maxlength="160" autocomplete="email"></label><label>' + esc(t('phone')) + '<input type="tel" name="phone" maxlength="40" autocomplete="tel"></label>' +
      '<label>' + esc(t('message')) + '<textarea name="message" required minlength="10" maxlength="2000"></textarea></label>' +
      '<label class="wr-check"><input type="checkbox" name="accept_privacy" required><span>' + esc(t('processor', { center: p.name })) + '</span></label>' +
      '<button class="wr-btn wr-full" type="submit">' + esc(t('send')) + '</button></form>', null, 'info');
    app.querySelector('[data-info]').addEventListener('submit', function (ev) {
      ev.preventDefault(); var f = ev.target;
      var body = { name: f.elements.name.value.trim(), email: f.elements.email.value.trim(), phone: f.elements.phone.value.trim(), message: f.elements.message.value.trim(),
        accept_privacy: f.elements.accept_privacy.checked, lang: lang };
      body[p.type === 'center' ? 'center_id' : 'provider_user_id'] = p.id;
      api('/api/info-requests', body).then(function () { frame('<div class="wr-done"><div class="wr-ico">✓</div><p>' + esc(t('info_sent')) + '</p></div>', null, 'info'); }).catch(function (e) { say(errText(e)); });
    });
  }

  // ------------------------------------------------------------------ the booking of a customer without an account
  function insLine(b) {
    var i = b.insurance; if (!i || i.required === 'no' || b.status === 'insurance_pending') return '';
    var ok = i.status === 'ok' || i.status === 'declared';
    return '<dt>' + esc(t('ins_title')) + '</dt><dd>' + (ok ? '🟢 ' + esc(t('ins_ok')) + (i.insurer ? ' · ' + esc(i.insurer) : '') : esc(t('ins_bring'))) + '</dd>';
  }
  function bookingPage() {
    var b = boot.booking; S.step = 'booking';
    if (boot.mode === 'return') {
      var paidNow = b.status === 'confirmed';
      frame('<div class="wr-done"><div class="wr-ico" aria-hidden="true">' + (paidNow ? '✓' : 'i') + '</div><h2>' + esc(paidNow ? t('paid') : t('st_' + b.status) || b.status_label) + '</h2>' +
        (boot.back === 'cancel' ? '<p class="wr-note">' + esc(t('pay_cancelled')) + '</p>' : '') +
        '<p class="wr-note">' + esc(t('reference')) + ': ' + esc(b.ref) + '</p><button class="wr-btn wr-sec" type="button" data-x>' + esc(t('close')) + '</button></div>', null, 'return');
      app.querySelector('[data-x]').addEventListener('click', function () { window.close(); });
      if (paidNow) setTimeout(function () { try { window.close(); } catch (e) { /* the browser keeps it */ } }, 4000);
      return;
    }
    var when = b.days && b.days.length > 1 ? day(b.days[0]) + ' – ' + day(b.days[b.days.length - 1]) : fmt(b.date, { weekday: 'long', day: 'numeric', month: 'long', year: 'numeric' }) + (b.time ? ' · ' + b.time : '');
    var st = t('st_' + b.status); if (st === 'st_' + b.status) st = b.status_label;
    var p = b.provider || {};
    var acts = [];
    if (['cancelled', 'rejected', 'expired'].indexOf(b.status) < 0) acts.push('<a class="wr-act" href="' + esc(boot.base + '/mi-reserva/' + b.token + '.ics') + '" download><span aria-hidden="true">📅</span>' + esc(t('rx_calendar')) + '</a>');
    if (p.maps) acts.push('<a class="wr-act" href="' + esc(p.maps) + '" target="_blank" rel="noopener"><span aria-hidden="true">📍</span>' + esc(t('rx_directions')) + '</a>');
    if (p.whatsapp) acts.push('<a class="wr-act" href="' + esc(p.whatsapp + '?text=' + encodeURIComponent(t('rx_wa_text', { ref: b.ref }))) + '" target="_blank" rel="noopener"><span aria-hidden="true">💬</span>' + esc(t('rx_whatsapp')) + '</a>');
    frame('<h2 class="wr-h">' + esc(t('your_booking')) + '</h2>' + (boot.back === 'ok' && b.status === 'confirmed' ? '<p class="wr-msg ok">' + esc(t('paid')) + '</p>' : '') +
      (boot.back === 'cancelado' ? '<p class="wr-msg info">' + esc(t('pay_cancelled')) + '</p>' : '') +
      '<dl class="wr-kv"><dt>' + esc(t('reference')) + '</dt><dd>' + esc(b.ref) + '</dd><dt>' + esc(t('activity')) + '</dt><dd>' + esc(b.service) + '</dd>' +
      '<dt>' + esc(t('date')) + '</dt><dd>' + esc(when) + ' <span class="wr-note">(' + esc(t('local_time', { tz: tzName(b.timezone) })) + ')</span></dd>' +
      '<dt>' + esc(t('people')) + '</dt><dd>' + b.participants + '</dd><dt>' + esc(t('total')) + '</dt><dd>' + esc(money(b.price, b.currency)) + '</dd>' +
      '<dt>' + esc(t('status')) + '</dt><dd>' + esc(st) + '</dd>' + insLine(b) + (b.meeting_point ? '<dt>' + esc(t('rx_meeting')) + '</dt><dd>' + esc(b.meeting_point) + '</dd>' : '') + '</dl>' +
      (b.has_qr ? '<figure class="wr-qr"><img src="' + esc('/api/mi-reserva/' + b.token + '/qr.svg') + '" alt="' + esc(t('rx_qr_alt')) + '" width="144" height="144"><figcaption>' + esc(t('rx_qr_note')) + '</figcaption></figure>' : '') +
      (acts.length ? '<div class="wr-acts">' + acts.join('') + '</div>' : '') +
      (b.can_people ? '<button type="button" class="wr-btn wr-sec wr-full" data-people>' + esc(t('rx_companions')) + '</button>' : '') +
      (b.payment_deadline ? '<p class="wr-note">' + esc(b.payment_deadline) + '</p>' : '') +
      '<div class="wr-policy"><b>' + esc(t('policy')) + '</b><br>' + esc(b.policy || '') + '</div>' +
      '<div class="wr-stripe" id="wr-stripe" data-stripe hidden></div>' +
      '<div class="wr-actions">' + (b.can_pay ? '<button class="wr-btn" type="button" data-pay>' + esc(t('pay_now')) + '</button>' : '') +
      (b.can_cancel ? '<button class="wr-btn wr-sec" type="button" data-cancel>' + esc(t('cancel_booking')) + '</button>' : '') +
      (b.slug ? '<a class="wr-link" href="' + esc(boot.base + '/c/' + b.slug) + '">' + esc(t('catalog')) + '</a>' : '') + '</div>' +
      (b.status === 'insurance_pending' ? insUploadForm(b.insurance && b.insurance.deadline || b.hold_expires_at) : ''), null, 'booking');
    if (b.status === 'insurance_pending') insBindUpload(b.token, function (out) {
      var nb = out.booking || {};
      if (nb.checkout_url) { location.href = nb.checkout_url; return; }
      api('/api/mi-reserva/' + b.token).then(function (d) { boot.booking = Object.assign(d.booking, { token: b.token }); bookingPage(); say(t('ins_saved'), 'ok'); });
    });
    var pb = app.querySelector('[data-people]'); if (pb) pb.addEventListener('click', function () { companions(b.token, b.participants, b.people || [], bookingPage); });
    var pay = app.querySelector('[data-pay]');
    if (pay) {
      var startPay = function () {
        pay.disabled = true;
        api('/api/mi-reserva/' + b.token + '/pagar', { pago_integrado: !!b.stripe }).then(function (r) {
          if (r.client_secret && r.stripe) {
            var box = app.querySelector('[data-stripe]'); box.hidden = false; box.innerHTML = '<div class="wr-skel wr-skel-pay"></div>'; pay.hidden = true;
            return loadStripe().then(function (Stripe) {
              return Stripe(r.stripe.key, { stripeAccount: r.stripe.account, locale: lang }).initEmbeddedCheckout({ fetchClientSecret: function () { return Promise.resolve(r.client_secret); },
                onComplete: function () { api('/api/mi-reserva/' + b.token + '/comprobar-pago', { lang: lang }).then(function (d) { boot.booking = Object.assign(d.booking, { token: b.token }); boot.back = 'ok'; bookingPage(); }); } });
            }).then(function (ch) { box.innerHTML = ''; ch.mount('#wr-stripe'); });
          }
          location.href = r.checkout_url;
        }).catch(function (e) { pay.disabled = false; say(errText(e)); });
      };
      pay.addEventListener('click', startPay);
      if (boot.pay) { if (b.stripe) startPay(); else pay.focus(); }
    }
    var cancel = app.querySelector('[data-cancel]');
    if (cancel) cancel.addEventListener('click', function () {
      if (!window.confirm(t('cancel_confirm'))) return;
      cancel.disabled = true;
      api('/api/mi-reserva/' + b.token + '/cancelar', {}).then(function () { return api('/api/mi-reserva/' + b.token); })
        .then(function (d) { boot.booking = Object.assign(d.booking, { token: b.token }); bookingPage(); say(t('cancelled'), 'ok'); })
        .catch(function (e) { cancel.disabled = false; say(errText(e)); });
    });
  }

  // The centre's colour on the buttons; the text on them dark when the colour is light (always readable)
  function brand(c) {
    if (!c || !/^#[0-9a-f]{6}$/i.test(c)) return;
    var ch = [1, 3, 5].map(function (i) { var v = parseInt(c.substr(i, 2), 16) / 255; return v <= 0.03928 ? v / 12.92 : Math.pow((v + 0.055) / 1.055, 2.4); });
    var lum = 0.2126 * ch[0] + 0.7152 * ch[1] + 0.0722 * ch[2];
    document.body.style.setProperty('--marca', c);
    document.body.style.setProperty('--sobre-marca', lum > 0.36 ? '#011C3C' : '#ffffff');
  }

  // ------------------------------------------------------------------ start
  brand(boot.color || (boot.booking && boot.booking.color));
  if (boot.mode === 'booking' || boot.mode === 'return') { bookingPage(); return; }
  skeleton();
  var q = '?lang=' + lang + '&canal=' + channel + (boot.service && boot.mode === 'widget' && boot.fmt === 'calendario' ? '&servicio=' + boot.service : '') + (boot.type ? '&tipo=' + encodeURIComponent(boot.type) : '');
  api('/api/w/' + boot.slug + q).then(function (c) {
    S.cat = c;
    brand(c.color);
    if (!c.bookable) return info();
    if (!c.services.length) { frame('<p class="wr-msg info">' + esc(t('no_dates')) + '</p>', null, 1); return; }
    if (boot.people) S.pax = boot.people;
    var pre = boot.service && c.services.filter(function (s) { return s.id === boot.service && s.bookable; })[0];
    var only = c.services.length === 1 && c.services[0].bookable ? c.services[0] : null;
    var first = pre || only;
    if (!first) return s1();
    // A link with everything chosen (servicio, fecha, hora, personas) opens straight on «Tus datos»
    pickService(first.id).then(function () {
      var direct = S.slot && ((boot.slot && S.slot.id === boot.slot) || (boot.date && boot.time && S.slot.date === boot.date && S.slot.time === boot.time));
      if (direct) { requote(); s2(); }
    });
  }).catch(function (e) { app.innerHTML = '<p class="wr-msg err">' + esc(errText(e)) + '</p>'; });
})();
