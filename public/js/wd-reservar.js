/* WORLDIVES · reservar desde la web del centro (v50.56).
 * Una sola aplicación para: el widget (/w/<centro>, dentro de un iframe en la web del centro, formatos botón,
 * calendario y lista), la página del centro (/c/<centro>), la página de una reserva sin cuenta (/mi-reserva/…) y la
 * vuelta del pago (/w/pago/…). El servidor decide todo lo importante (plazas, precio, reglas): aquí solo se pregunta
 * y se enseña. Sin cookies, sin analítica, sin librerías.
 */
(function () {
  'use strict';
  var boot = JSON.parse(document.getElementById('wd-boot').textContent || '{}');
  var T = boot.t || {}; var app = document.getElementById('wr-app'); var lang = boot.lang || 'es';
  var inFrame = window.top !== window;
  var hostUrl = (location.ancestorOrigins && location.ancestorOrigins.length ? location.ancestorOrigins[0] : '') || (inFrame ? document.referrer : '') || '';
  var hostOrigin = (function () { try { return hostUrl ? new URL(hostUrl).origin : ''; } catch (e) { return ''; } })();
  var channel = boot.mode === 'widget' ? 'widget' : 'link';

  function t(k, v) { return String(T[k] || k).replace(/\{(\w+)\}/g, function (m, n) { return v && v[n] != null ? v[n] : m; }); }
  function esc(s) { return String(s == null ? '' : s).replace(/[&<>"']/g, function (c) { return { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]; }); }
  function money(v, cur) { try { return new Intl.NumberFormat(lang, { style: 'currency', currency: cur || 'EUR', maximumFractionDigits: (+v % 1 ? 2 : 0) }).format(+v || 0); } catch (e) { return (+v || 0).toFixed(2) + ' ' + (cur || 'EUR'); } }
  function day(iso, opts) { try { return new Intl.DateTimeFormat(lang, Object.assign({ weekday: 'short', day: 'numeric', month: 'short', timeZone: 'UTC' }, opts || {})).format(new Date(iso + 'T12:00:00Z')); } catch (e) { return iso; } }
  function monthName(ym) { try { var s = new Intl.DateTimeFormat(lang, { month: 'long', year: 'numeric', timeZone: 'UTC' }).format(new Date(ym + '-15T12:00:00Z')); return s.charAt(0).toUpperCase() + s.slice(1); } catch (e) { return ym; } }
  function addMonth(ym, n) { var d = new Date(ym + '-15T12:00:00Z'); d.setUTCMonth(d.getUTCMonth() + n); return d.toISOString().slice(0, 7); }
  function tzName(tz) { return String(tz || '').split('/').pop().replace(/_/g, ' '); }
  function key() { try { return crypto.randomUUID(); } catch (e) { return 'k' + Date.now().toString(36) + Math.random().toString(36).slice(2, 12); } }

  // ------------------------------------------------------------------ talking to the page that embeds the widget
  function toHost(msg) {
    if (!inFrame || !hostOrigin) return;
    msg.source = 'worldives';
    try { window.parent.postMessage(msg, hostOrigin); } catch (e) { /* the page went away */ }
  }
  if (inFrame && 'ResizeObserver' in window) {
    var lastH = 0;
    new ResizeObserver(function () { var h = Math.ceil(document.documentElement.scrollHeight); if (Math.abs(h - lastH) > 2) { lastH = h; toHost({ type: 'height', h: h }); } }).observe(document.body);
  }
  if (boot.mode === 'widget' && boot.fmt === 'boton') document.addEventListener('keydown', function (e) { if (e.key === 'Escape') toHost({ type: 'close' }); });
  if (boot.mode === 'widget' && !inFrame && boot.slug) { location.replace(boot.base + '/c/' + boot.slug + location.search.replace(/[?&]f=[^&]*/, '')); return; }

  function api(path, body, extra) {
    var o = { method: body ? 'POST' : 'GET', headers: { Accept: 'application/json' }, credentials: boot.mode === 'widget' ? 'omit' : 'same-origin' };
    if (body) { o.headers['Content-Type'] = 'application/json'; o.body = JSON.stringify(body); }
    if (extra && extra.idem) o.headers['Idempotency-Key'] = extra.idem;
    return fetch(path, o).then(function (r) {
      return r.json().catch(function () { return {}; }).then(function (d) { if (!r.ok) { var e = new Error(d.error || t('error')); e.status = r.status; e.data = d; throw e; } return d; });
    });
  }
  function errText(e) {
    if (!e) return t('error');
    if (e.data && e.data.code === 'no_spots') return t('no_spots');
    if (e.status === 429) return t('too_many');
    if (lang !== 'es' && e.status >= 500) return t('error');
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

  // ------------------------------------------------------------------ drawing
  var S = { cat: null, svc: null, month: null, dates: null, sel: null, pax: 1, quote: null, busy: false };
  function say(text, kind) { var m = app.querySelector('[data-msg]'); if (m) { m.className = 'wr-msg ' + (kind || 'err'); m.textContent = text; m.hidden = !text; } }
  function head() {
    var p = (S.cat && S.cat.provider) || (boot.booking && boot.booking.provider) || {};
    var close = boot.mode === 'widget' && boot.fmt === 'boton' ? '<button class="wr-close" type="button" data-close aria-label="' + esc(t('close')) + '">×</button>' : '';
    return '<header class="wr-head">' + (p.logo ? '<img src="' + esc(p.logo) + '" alt="">' : '') + '<div><h1>' + esc(p.name || '') + '</h1>' + (p.place ? '<small>' + esc(p.place) + '</small>' : '') + '</div>' + close + '</header>';
  }
  function foot() {
    return '<footer class="wr-foot"><span>' + esc(t('powered')) + '</span><a href="' + esc(boot.privacy) + '" target="_blank" rel="noopener">' + esc(t('privacy')) + '</a></footer>';
  }
  function draw(body) {
    app.innerHTML = head() + body + '<p class="wr-msg" data-msg hidden role="alert"></p>' + foot();
    var c = app.querySelector('[data-close]'); if (c) c.addEventListener('click', function () { toHost({ type: 'close' }); });
  }
  function priceLine(s) {
    return '<span class="wr-price">' + esc(t('from')) + ' ' + esc(money(s.price, s.currency)) + '</span> <span class="wr-note">' + esc(t(s.per === 'day' ? 'per_day' : 'per_person')) + '</span>';
  }

  function home() {
    var list = S.cat.services;
    if (!S.cat.bookable) return info();
    if (boot.service && list.length === 1) return pick(list[0].id);
    var showNext = boot.mode !== 'widget' || boot.fmt === 'lista';
    draw('<h2>' + esc(t('choose_activity')) + '</h2><div class="wr-grid">' + list.map(function (s) {
      var next = showNext && s.next && s.next.length ? '<div class="wr-chips">' + s.next.map(function (x) {
        return '<button class="wr-chip" type="button" data-slot="' + x.id + '" data-svc="' + s.id + '"' + (x.free > 0 ? '' : ' disabled') + '>' + esc(day(x.date)) + ' ' + esc(x.time || '') + '</button>';
      }).join('') + '</div>' : '';
      return '<article class="wr-card">' + (s.photo && s.photo.src ? '<img src="' + esc(s.photo.src) + '"' + (s.photo.srcset ? ' srcset="' + esc(s.photo.srcset) + '" sizes="(min-width:560px) 150px, 100vw"' : '') + ' alt="" loading="lazy">' : '') +
        '<div class="wr-body"><h3>' + esc(s.title) + '</h3><div class="wr-meta">' + priceLine(s) + (s.duration ? '<span>' + esc(t('duration')) + ': ' + Math.round(s.duration / 60 * 10) / 10 + ' h</span>' : '') + '</div>' +
        (s.description ? '<p class="wr-note">' + esc(s.description.slice(0, 160)) + (s.description.length > 160 ? '…' : '') + '</p>' : '') + next +
        (s.bookable ? '<div><button class="wr-btn" type="button" data-svc="' + s.id + '">' + esc(t('see_dates')) + '</button></div>' : '<p class="wr-note">' + esc(s.reason || t('no_online')) + '</p>') + '</div></article>';
    }).join('') + '</div>');
    app.querySelectorAll('button[data-svc]').forEach(function (b) {
      b.addEventListener('click', function () { var slot = b.getAttribute('data-slot'); pick(+b.getAttribute('data-svc'), slot ? +slot : null); });
    });
  }

  function pick(id, slotId) {
    S.svc = S.cat.services.filter(function (s) { return s.id === id; })[0]; S.sel = null; S.quote = null; S.pax = 1;
    if (!S.svc) return home();
    S.month = (boot.date || (S.svc.next && S.svc.next[0] && S.svc.next[0].date) || new Date().toISOString()).slice(0, 7);
    loadMonth().then(function () {
      if (slotId) { S.sel = { slot: (S.dates.slots || []).filter(function (x) { return x.id === slotId; })[0] }; if (S.sel.slot) return details(); }
      if (boot.date && S.dates.slots) { var d0 = S.dates.slots.filter(function (x) { return x.date === boot.date; }); if (d0.length) S.day = boot.date; }
      dates();
    });
  }
  function loadMonth() {
    draw('<p class="wr-load">' + esc(t('loading')) + '</p>');
    return api('/api/w/' + boot.slug + '/fechas?servicio=' + S.svc.id + '&mes=' + S.month).then(function (d) { S.dates = d; S.month = d.month; }).catch(function (e) { S.dates = { slots: [], days: {} }; say(errText(e)); });
  }

  function calendar(isOn, isFull, isSel) {
    var first = new Date(S.month + '-01T12:00:00Z'); var off = (first.getUTCDay() + 6) % 7; var n = new Date(Date.UTC(first.getUTCFullYear(), first.getUTCMonth() + 1, 0)).getUTCDate();
    var wk = []; for (var i = 0; i < 7; i++) wk.push('<span>' + esc(new Intl.DateTimeFormat(lang, { weekday: 'narrow', timeZone: 'UTC' }).format(new Date(Date.UTC(2024, 0, 1 + i, 12)))) + '</span>');
    var cells = []; for (i = 0; i < off; i++) cells.push('<span></span>');
    for (var d = 1; d <= n; d++) {
      var iso = S.month + '-' + (d < 10 ? '0' : '') + d; var on = isOn(iso), full = isFull(iso);
      cells.push('<button type="button" class="wr-day' + (on ? ' on' : '') + (full ? ' full' : '') + (isSel(iso) ? ' sel' : '') + '" data-day="' + iso + '"' + (on ? '' : ' disabled') + ' aria-label="' + esc(day(iso, { weekday: 'long', month: 'long' })) + '">' + d + '</button>');
    }
    var today = (S.dates.today || '').slice(0, 7);
    return '<div class="wr-cal"><div class="wr-cal-top"><button type="button" data-mon="-1" aria-label="' + esc(t('prev_month')) + '"' + (S.month <= today ? ' disabled' : '') + '>‹</button><b>' + esc(monthName(S.month)) +
      '</b><button type="button" data-mon="1" aria-label="' + esc(t('next_month')) + '">›</button></div><div class="wr-week">' + wk.join('') + '</div><div class="wr-days">' + cells.join('') + '</div></div>';
  }
  function bindMonth() {
    app.querySelectorAll('[data-mon]').forEach(function (b) { b.addEventListener('click', function () { S.month = addMonth(S.month, +b.getAttribute('data-mon')); S.day = null; loadMonth().then(dates); }); });
  }

  function dates() {
    var s = S.svc, d = S.dates;
    var back = (S.cat.services.length > 1 || !boot.service) ? '<button class="wr-link" type="button" data-back>‹ ' + esc(t('back')) + '</button>' : '';
    if (s.unit === 'slot') {
      var by = {}; (d.slots || []).forEach(function (x) { (by[x.date] = by[x.date] || []).push(x); });
      var html = back + '<h2>' + esc(s.title) + '</h2><p class="wr-note">' + esc(t('choose_date')) + ' · ' + esc(t('local_time', { tz: tzName(d.timezone) })) + '</p>' +
        calendar(function (iso) { return !!by[iso]; }, function (iso) { return by[iso] && by[iso].every(function (x) { return x.free <= 0; }); }, function (iso) { return iso === S.day; });
      if (!(d.slots || []).length) html += '<p class="wr-msg info">' + esc(t('no_dates')) + '</p>';
      if (S.day && by[S.day]) html += '<div class="wr-slots">' + by[S.day].map(function (x) {
        var cls = x.free <= 0 ? 'none' : (x.free <= 2 ? 'low' : '');
        return '<button class="wr-slot" type="button" data-pick="' + x.id + '"' + (x.free > 0 ? '' : ' disabled') + '><b>' + esc(day(x.date, { weekday: 'long' })) + ' · ' + esc(x.time || '') +
          '</b><span class="wr-free ' + cls + '">' + esc(x.free <= 0 ? t('full') : (x.free === 1 ? t('one_spot') : t('free_spots', { n: x.free }))) + '</span></button>';
      }).join('') + '</div>';
      draw(html); bindMonth();
      app.querySelectorAll('[data-day]').forEach(function (b) { b.addEventListener('click', function () { S.day = b.getAttribute('data-day'); dates(); }); });
      app.querySelectorAll('[data-pick]').forEach(function (b) { b.addEventListener('click', function () { S.sel = { slot: (d.slots || []).filter(function (x) { return x.id === +b.getAttribute('data-pick'); })[0] }; details(); }); });
    } else {
      var sel = (S.sel && S.sel.days) || []; var part = (S.sel && S.sel.part) || 'full';
      var html2 = back + '<h2>' + esc(s.title) + '</h2><p class="wr-note">' + esc(t('choose_days')) + ' · ' + esc(t('local_time', { tz: tzName(d.timezone) })) + '</p>' +
        calendar(function (iso) { var st = (d.days || {})[iso]; return st === 'free' || st === 'am' || st === 'pm'; }, function (iso) { return (d.days || {})[iso] === 'busy'; }, function (iso) { return sel.indexOf(iso) >= 0; });
      if (s.unit === 'half_day' && sel.length === 1) {
        html2 += '<div class="wr-chips" role="group" style="margin-top:10px">' + ['full', 'am', 'pm'].map(function (p) {
          return '<button class="wr-chip" type="button" data-part="' + p + '" aria-pressed="' + (part === p) + '">' + esc(t({ full: 'full_day', am: 'morning', pm: 'afternoon' }[p])) + '</button>';
        }).join('') + '</div>';
      }
      html2 += '<p style="margin-top:12px"><button class="wr-btn wr-full" type="button" data-next' + (sel.length ? '' : ' disabled') + '>' + esc(t('next')) + '</button></p>';
      draw(html2); bindMonth();
      app.querySelectorAll('[data-day]').forEach(function (b) {
        b.addEventListener('click', function () {
          var iso = b.getAttribute('data-day'); var cur = (S.sel && S.sel.days) || [];
          if (cur.length === 1 && iso > cur[0]) {   // second click: a range of consecutive days
            var out = [], dd = new Date(cur[0] + 'T12:00:00Z');
            while (dd.toISOString().slice(0, 10) <= iso) { out.push(dd.toISOString().slice(0, 10)); dd.setUTCDate(dd.getUTCDate() + 1); }
            S.sel = { days: out, part: 'full' };
          } else S.sel = { days: [iso], part: part };
          dates();
        });
      });
      app.querySelectorAll('[data-part]').forEach(function (b) { b.addEventListener('click', function () { S.sel.part = b.getAttribute('data-part'); dates(); }); });
      var nx = app.querySelector('[data-next]'); if (nx) nx.addEventListener('click', details);
    }
    var bk = app.querySelector('[data-back]'); if (bk) bk.addEventListener('click', function () { S.svc = null; home(); });
  }

  function choice() {
    var s = S.svc; var b = { service_id: s.id, participants: S.pax };
    if (S.sel.slot) b.slot_id = S.sel.slot.id; else { b.days = S.sel.days; b.part = S.sel.part || 'full'; }
    return b;
  }
  function quote() {
    return api('/api/w/' + boot.slug + '/precio', choice()).then(function (q) { S.quote = q; return q; });
  }
  function details() {
    var s = S.svc, sel = S.sel;
    toHost({ event: 'reserva_iniciada', booking: { service: s.title, service_id: s.id, date: sel.slot ? sel.slot.date : sel.days[0] } });
    var when = sel.slot ? day(sel.slot.date, { weekday: 'long' }) + ' · ' + (sel.slot.time || '') : (sel.days.length > 1 ? day(sel.days[0]) + ' – ' + day(sel.days[sel.days.length - 1]) : day(sel.days[0], { weekday: 'long' }));
    var max = Math.min(s.max_participants || 20, sel.slot ? Math.max(1, sel.slot.free) : 20);
    var mode = s.mode === 'payment' ? t('pay_note', { min: S.cat.hold_minutes || boot.hold_minutes || 10 }) : t('request_note');
    draw('<button class="wr-link" type="button" data-back>‹ ' + esc(t('back')) + '</button><h2>' + esc(s.title) + '</h2><p class="wr-note">' + esc(when) + ' · ' + esc(t('local_time', { tz: tzName(S.dates.timezone) })) + '</p>' +
      '<form novalidate data-form><div class="wr-step"><span>' + esc(t('people')) + '</span><button type="button" data-pax="-1" aria-label="−">−</button><output data-paxv>' + S.pax + '</output><button type="button" data-pax="1" aria-label="+">+</button></div>' +
      '<div class="wr-sum" data-sum><span class="wr-note">' + esc(t('loading')) + '</span></div>' +
      '<h3>' + esc(t('your_details')) + '</h3><label>' + esc(t('name')) + '<input type="text" name="fullname" autocomplete="name" required maxlength="180"></label>' +
      '<div class="wr-two"><label>' + esc(t('email')) + '<input type="email" name="email" autocomplete="email" required maxlength="160"></label>' +
      '<label>' + esc(t('phone')) + '<input type="tel" name="phone" autocomplete="tel" maxlength="40"></label></div>' +
      '<label>' + esc(t('notes')) + '<textarea name="notes" maxlength="1000"></textarea></label>' +
      '<label class="wr-hp" aria-hidden="true">Web<input type="text" name="website" tabindex="-1" autocomplete="off"></label>' +
      '<div class="wr-policy"><b>' + esc(t('policy')) + '</b><br>' + esc(S.cat.provider.policy || '') + '</div>' +
      '<label class="wr-check"><input type="checkbox" name="accept_policy" required><span>' + esc(t('accept_policy')) + '</span></label>' +
      '<p class="wr-note">' + esc(mode) + '</p><p class="wr-note">' + esc(t('processor', { center: S.cat.provider.name })) + '</p>' +
      '<button class="wr-btn wr-full" type="submit" data-go>' + esc(s.mode === 'payment' ? t('pay_book') : t('send_request')) + '</button></form>');
    app.querySelector('[data-back]').addEventListener('click', dates);
    function refresh() {
      app.querySelector('[data-paxv]').textContent = S.pax;
      quote().then(function (q) {
        app.querySelector('[data-sum]').innerHTML = (q.lines || []).map(function (l) {
          return '<div><span>' + esc(l.label) + (l.qty > 1 ? ' × ' + l.qty : '') + '</span><span>' + esc(money(l.total, q.currency)) + '</span></div>';
        }).join('') + '<div class="wr-total"><span>' + esc(t('total')) + '</span><span>' + esc(money(q.total, q.currency)) + '</span></div>';
      }).catch(function (e) { app.querySelector('[data-sum]').innerHTML = '<span class="wr-msg err">' + esc(errText(e)) + '</span>'; });
    }
    app.querySelectorAll('[data-pax]').forEach(function (b) { b.addEventListener('click', function () { S.pax = Math.max(1, Math.min(max, S.pax + +b.getAttribute('data-pax'))); refresh(); }); });
    refresh();
    var idem = key();
    app.querySelector('[data-form]').addEventListener('submit', function (ev) {
      ev.preventDefault(); if (S.busy) return;
      var f = ev.target; var data = choice();
      ['fullname', 'email', 'phone', 'notes', 'website'].forEach(function (k) { data[k] = (f.elements[k].value || '').trim(); });
      data.accept_policy = f.elements.accept_policy.checked; data.lang = lang; data.canal = channel; data.host_url = hostUrl; data.host = boot.host || '';
      if (data.fullname.length < 2) return say(t('need_name'));
      if (!/^[^@\s]+@[^@\s]+\.[^@\s]+$/.test(data.email)) return say(t('check_email'));
      if (!data.accept_policy) return say(t('accept_policy'));
      S.busy = true; var go = app.querySelector('[data-go]'); go.disabled = true; say('', 'info');
      var win = null;
      if (s.mode === 'payment' && boot.mode === 'widget') { try { win = window.open('', 'wd-pago'); } catch (e) { win = null; } }   // opened now: popup blockers allow it
      book(data, idem).then(function (r) {
        S.busy = false;
        if (r.checkout_url) {
          if (boot.mode !== 'widget') { location.href = r.checkout_url; return; }
          if (win) { try { win.location.href = r.checkout_url; } catch (e) { win = null; } }
          return paying(r, win);
        }
        if (win) try { win.close(); } catch (e) { /* closed already */ }
        done(r);
      }).catch(function (e) {
        S.busy = false; go.disabled = false; if (win) try { win.close(); } catch (x) { /* closed */ }
        say(errText(e));
        if (e.data && e.data.code === 'no_spots') { S.sel = null; loadMonth().then(dates).then(function () { say(t('no_spots')); }); }
      });
    });
  }

  function paying(r, win) {
    draw('<div class="wr-done"><h2>' + esc(t('waiting_pay')) + '</h2><p class="wr-note">' + esc(t('opening_pay')) + '</p>' +
      '<a class="wr-btn" href="' + esc(r.checkout_url) + '" target="_blank" rel="noopener">' + esc(t('pay_link')) + '</a></div>');
    var until = Date.now() + ((S.cat.hold_minutes || 10) + 2) * 60000;
    (function poll() {
      api('/api/mi-reserva/' + r.token).then(function (d) {
        var b = d.booking;
        if (b.status === 'confirmed') return done({ status: 'confirmed', ref: b.ref, token: r.token, booking_url: r.booking_url }, true);
        if (b.status === 'expired' || b.status === 'cancelled') { draw('<div class="wr-done"><p class="wr-msg info">' + esc(t('pay_cancelled')) + '</p><button class="wr-btn wr-sec" type="button" data-again>' + esc(t('back')) + '</button></div>'); app.querySelector('[data-again]').addEventListener('click', home); return; }
        if (Date.now() < until) setTimeout(poll, 2500);
      }).catch(function () { if (Date.now() < until) setTimeout(poll, 4000); });
    })();
  }

  function done(r, paid) {
    var ok = r.status === 'confirmed';
    toHost({ event: 'reserva_completada', booking: { ref: r.ref, status: r.status, service: S.svc && S.svc.title, paid: !!paid } });
    var email = (app.querySelector('input[name=email]') || {}).value || '';
    draw('<div class="wr-done"><div class="wr-ico" aria-hidden="true">✓</div><h2>' + esc(t(ok ? 'confirmed' : 'requested')) + '</h2>' +
      (r.ref ? '<p><b>' + esc(t('reference')) + ':</b> ' + esc(r.ref) + '</p>' : '') +
      (!ok && r.response_deadline_text ? '<p>' + esc(t('reply_before', { when: r.response_deadline_text })) + '</p>' : '') +
      (email ? '<p class="wr-note">' + esc(t('mail_sent', { email: email })) + '</p>' : '') +
      (r.booking_url ? '<a class="wr-btn wr-sec" href="' + esc(r.booking_url) + '" target="_blank" rel="noopener">' + esc(t('your_booking')) + '</a>' : '') +
      '<p class="wr-note" style="margin-top:8px">' + esc(t('account_offer')) + '</p><a class="wr-link" href="' + esc(boot.register + '?tipo=recreational' + (email ? '&email=' + encodeURIComponent(email) : '')) + '" target="_blank" rel="noopener">' + esc(t('create_account')) + '</a></div>');
  }

  function info() {
    var p = S.cat.provider;
    draw('<p class="wr-msg info">' + esc(t('no_online')) + '</p><form novalidate data-info><label>' + esc(t('name')) + '<input type="text" name="name" required maxlength="120"></label>' +
      '<label>' + esc(t('email')) + '<input type="email" name="email" required maxlength="160"></label><label>' + esc(t('phone')) + '<input type="tel" name="phone" maxlength="40"></label>' +
      '<label>' + esc(t('message')) + '<textarea name="message" required minlength="10" maxlength="2000"></textarea></label>' +
      '<label class="wr-check"><input type="checkbox" name="accept_privacy" required><span>' + esc(t('processor', { center: p.name })) + '</span></label>' +
      '<button class="wr-btn wr-full" type="submit">' + esc(t('send')) + '</button></form>');
    app.querySelector('[data-info]').addEventListener('submit', function (ev) {
      ev.preventDefault(); var f = ev.target;
      var body = { name: f.elements.name.value.trim(), email: f.elements.email.value.trim(), phone: f.elements.phone.value.trim(), message: f.elements.message.value.trim(),
        accept_privacy: f.elements.accept_privacy.checked, lang: lang };
      body[p.type === 'center' ? 'center_id' : 'provider_user_id'] = p.id;
      api('/api/info-requests', body).then(function () { draw('<div class="wr-done"><div class="wr-ico">✓</div><p>' + esc(t('info_sent')) + '</p></div>'); }).catch(function (e) { say(errText(e)); });
    });
  }

  // ------------------------------------------------------------------ the booking of a customer without an account
  function bookingPage() {
    var b = boot.booking;
    if (boot.mode === 'return') {
      var paidNow = b.status === 'confirmed';
      draw('<div class="wr-done"><div class="wr-ico" aria-hidden="true">' + (paidNow ? '✓' : 'i') + '</div><h2>' + esc(paidNow ? t('paid') : t('st_' + b.status) || b.status_label) + '</h2>' +
        (boot.back === 'cancel' ? '<p class="wr-note">' + esc(t('pay_cancelled')) + '</p>' : '') +
        '<p class="wr-note">' + esc(t('reference')) + ': ' + esc(b.ref) + '</p><button class="wr-btn wr-sec" type="button" data-x>' + esc(t('close')) + '</button></div>');
      app.querySelector('[data-x]').addEventListener('click', function () { window.close(); });
      if (paidNow) setTimeout(function () { try { window.close(); } catch (e) { /* the browser keeps it */ } }, 4000);
      return;
    }
    var when = b.days && b.days.length > 1 ? day(b.days[0]) + ' – ' + day(b.days[b.days.length - 1]) : day(b.date, { weekday: 'long', year: 'numeric' }) + (b.time ? ' · ' + b.time : '');
    var st = t('st_' + b.status); if (st === 'st_' + b.status) st = b.status_label;
    draw('<h2>' + esc(t('your_booking')) + '</h2>' + (boot.back === 'ok' && b.status === 'confirmed' ? '<p class="wr-msg ok">' + esc(t('paid')) + '</p>' : '') +
      (boot.back === 'cancelado' ? '<p class="wr-msg info">' + esc(t('pay_cancelled')) + '</p>' : '') +
      '<dl class="wr-kv"><dt>' + esc(t('reference')) + '</dt><dd>' + esc(b.ref) + '</dd><dt>' + esc(t('activity')) + '</dt><dd>' + esc(b.service) + '</dd>' +
      '<dt>' + esc(t('date')) + '</dt><dd>' + esc(when) + ' <span class="wr-note">(' + esc(t('local_time', { tz: tzName(b.timezone) })) + ')</span></dd>' +
      '<dt>' + esc(t('people')) + '</dt><dd>' + b.participants + '</dd><dt>' + esc(t('total')) + '</dt><dd>' + esc(money(b.price, b.currency)) + '</dd>' +
      '<dt>' + esc(t('status')) + '</dt><dd>' + esc(st) + '</dd></dl>' +
      (b.payment_deadline ? '<p class="wr-note">' + esc(b.payment_deadline) + '</p>' : '') +
      '<div class="wr-policy" style="margin:12px 0"><b>' + esc(t('policy')) + '</b><br>' + esc(b.policy || '') + '</div>' +
      '<div class="wr-actions">' + (b.can_pay ? '<button class="wr-btn" type="button" data-pay>' + esc(t('pay_now')) + '</button>' : '') +
      (b.can_cancel ? '<button class="wr-btn wr-sec" type="button" data-cancel>' + esc(t('cancel_booking')) + '</button>' : '') +
      (b.slug ? '<a class="wr-link" href="' + esc(boot.base + '/c/' + b.slug) + '">' + esc(t('catalog')) + '</a>' : '') + '</div>');
    var pay = app.querySelector('[data-pay]');
    if (pay) {
      pay.addEventListener('click', function () {
        pay.disabled = true;
        api('/api/mi-reserva/' + b.token + '/pagar', {}).then(function (r) { location.href = r.checkout_url; }).catch(function (e) { pay.disabled = false; say(errText(e)); });
      });
      if (boot.pay) pay.focus();
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

  // ------------------------------------------------------------------ start
  if (boot.mode === 'booking' || boot.mode === 'return') { bookingPage(); return; }
  var q = '?lang=' + lang + '&canal=' + channel + (boot.service ? '&servicio=' + boot.service : '') + (boot.type ? '&tipo=' + encodeURIComponent(boot.type) : '');
  api('/api/w/' + boot.slug + q).then(function (c) {
    S.cat = c;
    if (c.color && /^#[0-9a-f]{6}$/i.test(c.color)) document.body.style.setProperty('--marca', c.color);
    if (!c.services.length && c.bookable) { draw('<p class="wr-msg info">' + esc(t('no_dates')) + '</p>'); return; }
    if (boot.mode === 'widget' && boot.fmt === 'calendario' && c.services.length === 1) return pick(c.services[0].id);
    if (boot.mode === 'page' && boot.service) return pick(boot.service);
    home();
  }).catch(function (e) { app.innerHTML = '<p class="wr-msg err">' + esc(errText(e)) + '</p>'; });
})();
